import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = Path(os.environ.get('HV_SCRIPT', ROOT / 'hv-analysis/scripts/md_to_pdf.py'))

REPORT = """# Cursor 横纵分析报告
> 研究时间：2026-11-18 | 所属领域：AI 编程 | 研究对象类型：产品

## 一、一句话定义

正文里提到所属领域这四个字的句子要留着。
"""


class HvReportTests(unittest.TestCase):
    def convert(self, markdown_text):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / 'report.md'
            output = Path(tmp) / 'report.html'
            source.write_text(markdown_text, encoding='utf-8')
            subprocess.run([sys.executable, str(SCRIPT), str(source), str(output)], check=True, capture_output=True)
            return output.read_text(encoding='utf-8')

    def test_cover_meta_is_not_repeated_in_body(self):
        page = self.convert(REPORT)
        self.assertEqual(page.count('研究时间：2026-11-18'), 1)
        self.assertIn("<div class='meta'>研究时间：2026-11-18", page)
        self.assertNotIn('<blockquote>', page)
        self.assertEqual(page.count('Cursor 横纵分析报告</h1>'), 1)
        self.assertIn('正文里提到所属领域这四个字的句子要留着。', page)

    def test_body_sentence_is_kept_when_it_serves_as_meta(self):
        page = self.convert('# 标题\n\n所属领域是 AI 编程，这句是正文。\n')
        self.assertEqual(page.count('所属领域是 AI 编程，这句是正文。'), 2)

    def test_split_meta_without_meta_line(self):
        spec = importlib.util.spec_from_file_location('md_to_pdf', SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.assertEqual(module.split_meta('# 标题\n\n正文'), ('# 标题\n\n正文', ''))


if __name__ == '__main__':
    unittest.main()
