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

if __name__ == '__main__': unittest.main()
