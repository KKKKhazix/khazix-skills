#!/usr/bin/env python3
"""Inject an analysis JSON into the HTML template -> a standalone report.

Usage:
    build_report.py <analysis.json> [output.html]

The analysis JSON is produced by Claude after interpreting scan.py output.
Schema (all sections optional except system):

{
  "generated_at": "2026-05-28 12:00:00",
  "scan_seconds": 42.1,
  "system": {os, build, arch, user, home, filesystem,
             disk_total, disk_used, disk_free, purgeable},
  "top5": [{rank, tier(green|yellow|red), size, type, name, path, note}],
  "green":  [{name, path, size_estimate, kill_processes:[], trash_paths:[...], commands:[{label,cmd}]}],
  "yellow": [{name, path, size, content_profile, why_manual, disposal, risk, trash_paths:[...]?, open_note?}],
  "red":    [{name, path, size, why_keep, indirect_release, auto_reclaim, app_paths:[...]?}],
  "denied": ["/path/one", ...],
  "summary": {overview, tier_stats:{green,yellow,red}, priority:[...], long_term:[...]}
}
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(HERE, "..", "assets", "report_template.html")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    src = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else os.path.expanduser(
        "~/Desktop/storage-report.html")

    with open(src, "r", encoding="utf-8") as f:
        data = json.load(f)
    with open(TEMPLATE, "r", encoding="utf-8") as f:
        tpl = f.read()

    blob = json.dumps(data, ensure_ascii=False)
    # 静态报告不带删除能力（DELETE=null），删除按钮只在 server.py 服务时出现
    html = tpl.replace("__REPORT_DATA__", blob).replace("__DELETE_CONFIG__", "null")

    with open(out, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"报告已生成: {out}")
    opener = ("start" if sys.platform.startswith("win")
              else "open" if sys.platform == "darwin" else "xdg-open")
    print(f"打开: {opener} '{out}'")


if __name__ == "__main__":
    main()
