import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
class InstallerTests(unittest.TestCase):
    @unittest.skipIf(os.name=='nt','Bash installer is Unix-only')
    def test_shared_migration_keeps_claude_entry(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); home=root/'home'; home.mkdir()
            legacy=home/'.claude/skills/aihot'; legacy.mkdir(parents=True)
            (legacy/'SKILL.md').write_bytes((ROOT/'aihot/SKILL.md').read_bytes())
            # Inject fixture roots into a copy, never change the caller's HOME/CODEX_HOME.
            script=(ROOT/'aihot/install.sh').read_text().replace('$HOME','$TEST_INSTALL_HOME').replace('${HOME:', '${TEST_INSTALL_HOME:').replace('${CODEX_HOME:-','${TEST_CODEX_HOME:-')
            installer=root/'install.sh'; installer.write_text(script)
            binpath=root/'bin'; binpath.mkdir()
            curl=binpath/'curl'; curl.write_text('''#!/usr/bin/env python3
import os,sys,shutil
args=sys.argv[1:]
url=next(a for a in args if a.startswith('https://'))
source=os.path.join(os.environ['TEST_PACKAGE'],url.split('/aihot-skill/')[1])
if '-o' in args: shutil.copyfile(source,args[args.index('-o')+1])
else: sys.stdout.buffer.write(open(source,'rb').read())
'''); curl.chmod(0o755)
            env=dict(os.environ,TEST_INSTALL_HOME=str(home),TEST_PACKAGE=str(ROOT/'aihot'),PATH=str(binpath)+os.pathsep+os.environ['PATH'])
            result=subprocess.run(['bash',str(installer),'--target','agents','--migrate-legacy','--no-actor'],env=env,capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertTrue(legacy.is_symlink())
            self.assertEqual((legacy/'SKILL.md').read_bytes(),(ROOT/'aihot/SKILL.md').read_bytes())
