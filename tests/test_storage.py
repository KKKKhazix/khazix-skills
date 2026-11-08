import importlib.util
import http.client
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'storage-analyzer/scripts'))
import server
import scan

class StorageTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.home = Path(self.tmp.name).resolve()
        self.addCleanup(patch.stopall)
        patch.object(server, 'HOME', str(self.home)).start()
        self.cache = self.home / 'cache'
        self.cache.mkdir()
        (self.cache / 'file').write_text('cache')
        data = {'system': {'os': 'test'}, 'green': [{'trash_paths': [str(self.cache), str(self.home)]}]}
        source = self.home / 'analysis.json'
        source.write_text(json.dumps(data))
        server.DATA, server.TPL, server.RM_ALLOW, server.TRASH_ALLOW, server.OPEN_ALLOW = server.load(source)
        self.http = server.ThreadingHTTPServer(('127.0.0.1', 0), server.Handler)
        self.thread = threading.Thread(target=self.http.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.stop)
    def stop(self):
        self.http.shutdown(); self.http.server_close(); self.thread.join()
    def request(self, method, path='/', payload=None, host=None):
        c = http.client.HTTPConnection('127.0.0.1', self.http.server_address[1])
        headers = {'Content-Type': 'application/json'}
        if host: headers['Host'] = host
        c.request(method, path, json.dumps(payload) if payload is not None else None, headers)
        r = c.getresponse(); result = r.status, r.read().decode(); c.close(); return result
    def delete(self, paths):
        return self.request('POST', '/action', {'token': server.TOKEN, 'mode': 'rm', 'paths': list(map(str, paths))})
    def test_home_root_rejected(self):
        with patch.object(server, 'hard_delete') as delete:
            self.assertEqual(self.delete([self.home])[0], 403)
            delete.assert_not_called()
    def test_validate_entire_batch_before_deleting(self):
        self.assertEqual(self.delete([self.cache, self.home])[0], 403)
        self.assertTrue(self.cache.exists())
    def test_git_worktree_rejected(self):
        (self.cache / '.git').write_text('gitdir: ../repo/.git/worktrees/example')
        self.assertEqual(self.delete([self.cache])[0], 403)
        self.assertTrue(self.cache.exists())
    def test_parent_of_worktree_rejected(self):
        p=self.cache/'project'; p.mkdir(); (p/'.git').mkdir()
        self.assertEqual(self.delete([self.cache])[0], 403)
    def test_nonlocal_host_cannot_read_report(self):
        code,body=self.request('GET',host='untrusted.invalid')
        self.assertEqual(code,403); self.assertNotIn(server.TOKEN, body)
    def test_report_data_cannot_break_script(self):
        server.DATA['summary']={'overview':'</script><div id=audit-marker></div><script>'}
        code,body=self.request('GET')
        self.assertEqual(code,200); self.assertEqual(body.count('</script>'),1)
    def test_cache_deletion(self):
        self.assertEqual(self.delete([self.cache])[0],200)
        self.assertFalse(self.cache.exists())
    def test_clear_contents_keeps_directory(self):
        (self.cache / 'sub').mkdir(); (self.cache / 'sub' / 'f').write_text('x')
        (self.cache / '.hidden').write_text('h')
        data = {'system': {'os': 'test'},
                'green': [{'trash_paths': [str(self.cache)], 'clear_contents': True}]}
        source = self.home / 'clear.json'
        source.write_text(json.dumps(data))
        server.DATA, server.TPL, server.RM_ALLOW, server.TRASH_ALLOW, server.OPEN_ALLOW = server.load(source)
        self.assertEqual(self.delete([self.cache])[0], 200)
        self.assertTrue(self.cache.exists())
        self.assertEqual(list(self.cache.iterdir()), [])
    def test_single_file_deletion(self):
        target=self.cache/'file'
        server.RM_ALLOW.add(str(target))
        self.assertEqual(self.delete([target])[0],200)
        self.assertFalse(target.exists())
    def test_already_gone_target_succeeds(self):
        target=self.cache/'already-gone'
        server.RM_ALLOW.add(str(target))
        self.assertEqual(self.delete([target])[0],200)
    def test_readonly_cache_deletion(self):
        sub=self.cache/'module'; sub.mkdir(); f=sub/'file'; f.write_text('cache')
        f.chmod(stat.S_IREAD); sub.chmod(stat.S_IREAD|stat.S_IEXEC)
        try:
            self.assertEqual(self.delete([self.cache])[0],200)
            self.assertFalse(self.cache.exists())
        finally:
            if sub.exists(): sub.chmod(stat.S_IRWXU)
            if f.exists(): f.chmod(stat.S_IRWXU)
    def test_link_to_outside_not_followed(self):
        outside=self.home/'outside'; outside.mkdir(); (outside/'keep').write_text('keep')
        try: (self.cache/'link').symlink_to(outside,target_is_directory=True)
        except OSError: self.skipTest('symlink creation unavailable')
        self.assertEqual(self.delete([self.cache])[0],200)
        self.assertEqual((outside/'keep').read_text(),'keep')
    @unittest.skipUnless(sys.platform=='win32', 'Windows junction')
    def test_windows_junction_is_not_counted(self):
        target=self.home/'target'; target.mkdir(); (target/'file').write_bytes(b'x'*2048)
        junction=self.cache/'junction'
        subprocess.run(['cmd','/c','mklink','/J',str(junction),str(target)],check=True,capture_output=True)
        try: self.assertEqual(scan.dir_size_bytes(str(self.cache)),5)
        finally: junction.rmdir()

class DuChildrenTests(unittest.TestCase):
    def test_mount_points_skipped_only_on_same_volume_scans(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); (root / 'local').mkdir(); (root / 'mounted').mkdir()
            real_lstat = os.lstat
            def fake_lstat(path, *args, **kwargs):
                st = real_lstat(path, *args, **kwargs)
                if str(path).endswith('mounted'):  # pretend another filesystem is mounted here
                    return os.stat_result((st.st_mode, st.st_ino, st.st_dev + 1) + tuple(st)[3:])
                return st
            fake_du = lambda cmd, timeout=180: '2048\t' + cmd[-1]
            with patch.object(scan.os, 'lstat', fake_lstat), patch.object(scan, 'run', fake_du):
                mac = [r['name'] for r in scan.du_children(str(root), min_kb=1)]
                linux = [r['name'] for r in scan.du_children(str(root), min_kb=1, same_volume=False)]
        scan.SCAN_ERRORS.clear()
        self.assertEqual(mac, ['local'])
        self.assertEqual(sorted(linux), ['local', 'mounted'])

class LinuxDiskTests(unittest.TestCase):
    """GNU df output -> disk overview; df Used on ZFS is per dataset (children excluded)."""
    HEADER = 'Filesystem Type 1B-blocks Used Avail Mounted on\n'
    def system(self, rows):
        out = self.HEADER + '\n'.join(rows) + '\n'
        with patch.object(scan, 'run', lambda cmd, timeout=180: out if cmd[0] == 'df' else ''):
            return scan.system_info_linux()
    def test_zfs_pool_sums_datasets_and_counts_free_once(self):
        s = self.system([
            'rpool/ROOT/ubuntu_abc zfs 400000000000 10000000000 390000000000 /',
            'rpool/ROOT/ubuntu_abc/var/lib zfs 420000000000 30000000000 390000000000 /var/lib',
            'rpool/USERDATA/home_abc zfs 450000000000 60000000000 390000000000 /home/u',
            'bpool/BOOT/ubuntu_abc zfs 1800000000 200000000 1600000000 /boot',
            '/dev/nvme0n1p1 vfat 536000000 6000000 530000000 /boot/efi'])
        self.assertEqual(s['disk_name'], 'rpool')
        self.assertEqual(s['disk_used'], scan.human(100000000000 // 1024))
        self.assertEqual(s['disk_total'], scan.human(490000000000 // 1024))
        self.assertEqual([d['name'] for d in s['disks']], ['rpool', 'bpool'])
    def test_btrfs_subvolumes_are_one_disk(self):
        s = self.system([
            '/dev/nvme0n1p3 btrfs 500000000000 120000000000 378000000000 /',
            '/dev/nvme0n1p3 btrfs 500000000000 120000000000 378000000000 /home',
            '/dev/nvme0n1p2 ext4 1000000000 300000000 600000000 /boot'])
        self.assertEqual(s['disk_used'], scan.human(120000000000 // 1024))
        self.assertEqual(s['disk_total'], scan.human(500000000000 // 1024))
        self.assertEqual(len(s['disks']), 2)
    def test_external_drive_is_listed_but_not_main_disk(self):
        s = self.system([
            '/dev/sda2 ext4 250000000000 80000000000 157000000000 /',
            '/dev/sdb1 exfat 1000000000000 400000000000 600000000000 /media/u/USB DRIVE'])
        self.assertEqual(s['disk_name'], '/dev/sda2')
        self.assertEqual(s['disk_total'], scan.human(250000000000 // 1024))
        self.assertEqual({d['name'] for d in s['disks']}, {'/dev/sda2', '/dev/sdb1'})
    def test_unparseable_df_falls_back_to_root(self):
        s = self.system(['df: unrecognized option'])
        self.assertEqual((s['disk_name'], s['disks']), ('/', []))
        self.assertNotEqual(s['disk_total'], '?')

if __name__ == '__main__': unittest.main()
