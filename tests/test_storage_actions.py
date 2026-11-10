"""Partial cleanup must retain only unfinished paths; retrying must not delete a recreated cache again."""
from pathlib import Path
import shutil
import subprocess
import unittest


@unittest.skipUnless(shutil.which("node"), "JavaScript runtime")
class CleanupState(unittest.TestCase):
    def test_partial_result_does_not_resubmit_completed_paths(self):
        template = Path(__file__).resolve().parents[1] / "storage-analyzer/assets/report_template.html"
        script = r'''
const fs = require('node:fs');
const assert = require('node:assert/strict');
const html = fs.readFileSync(process.argv[1], 'utf8');
const source = html.slice(html.indexOf('function doDelete('), html.indexOf('function doOpen('));
const status = {}, item = {classList: {add() {}}, querySelector() {return null;}};
const wrap = {dataset: {paths: btoa(JSON.stringify(['/first', '/second']))},
  querySelector: () => status, querySelectorAll: () => [], closest: () => item};
const button = {closest: () => wrap};
global.confirm = () => true;
const calls = [];
global.postAction = async (_, paths) => {
  calls.push(paths);
  return calls.length === 1 ? {ok: false, done: ['/first'], error: 'second failed'} : {ok: true, done: paths};
};
eval(source);
(async () => {
  doDelete(button, 'trash');
  await new Promise(resolve => setImmediate(resolve));
  doDelete(button, 'trash');
  await new Promise(resolve => setImmediate(resolve));
  assert.deepEqual(calls, [['/first', '/second'], ['/second']]);
})();
'''
        result = subprocess.run(["node", "-e", script, str(template)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
