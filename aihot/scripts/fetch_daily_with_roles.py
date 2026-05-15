#!/usr/bin/env python3
"""拉 aihot daily 数据 + 从 /daily HTML 提取 role 映射，输出合并 JSON。

输出 JSON 结构（供 render_daily_html.py 消费）：
{
  "date": "YYYY-MM-DD",
  "sections": [
    {
      "label": "模型",                  // 简化
      "items": [
        {
          "title": "...",               // API 原 title
          "source": "X：腾讯混元 (@TencentHunyuan)",  // API 原 sourceName
          "source_role": "官方·X",        // 从 /daily HTML 提取，可能为空
          "summary": "...",             // API 原 summary，一字未改
          "url": "..."                  // API 原 sourceUrl
        }
      ]
    }
  ]
}

章节顺序固定：模型 → 产品 → 技巧 → 行业 → 论文

用法：
  python3 fetch_daily_with_roles.py <YYYY-MM-DD> <output.json>
"""

import sys
import re
import json
import urllib.request
import urllib.error
from pathlib import Path


UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)
BASE = "https://aihot.virxact.com"

LABEL_ORDER = ["模型发布/更新", "产品发布/更新", "技巧与观点", "行业动态", "论文研究"]
LABEL_SHORT = {
    "模型发布/更新": "模型",
    "产品发布/更新": "产品",
    "技巧与观点": "技巧",
    "行业动态": "行业",
    "论文研究": "论文",
}

ROLE_PAT = re.compile(r'class="role-tag">([^<]+)</span><span>([^<]+)</span>')


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=20) as resp:
        return resp.read().decode("utf-8")


def extract_roles(html_text: str) -> dict[str, str]:
    """从 /daily HTML 正则提取 sourceName → role 映射。"""
    roles: dict[str, str] = {}
    for role, src in ROLE_PAT.findall(html_text):
        # 同名 sourceName 出现多次时取第一次（实测同名 role 一致）
        roles.setdefault(src, role)
    return roles


def main() -> None:
    if len(sys.argv) < 3:
        print("Usage: fetch_daily_with_roles.py <YYYY-MM-DD> <output.json>", file=sys.stderr)
        sys.exit(1)

    date = sys.argv[1]
    out = Path(sys.argv[2])

    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date):
        print(f"invalid date format: {date} (want YYYY-MM-DD)", file=sys.stderr)
        sys.exit(2)

    # 1. API daily JSON
    api = json.loads(fetch(f"{BASE}/api/public/daily/{date}"))

    # 2. /daily HTML —— 先试指定日期，失败回退到最新（aihot 当前的 /daily 总是最新）
    html_text = ""
    for path in (f"{BASE}/daily/{date}", f"{BASE}/daily"):
        try:
            html_text = fetch(path)
            break
        except urllib.error.HTTPError as e:
            if e.code == 404:
                continue
            raise
    roles = extract_roles(html_text)

    # 3. join + 章节重排
    sections_by_label = {s["label"]: s for s in api.get("sections", [])}
    sections_out = []
    matched = 0
    total = 0
    for label in LABEL_ORDER:
        if label not in sections_by_label:
            continue
        s = sections_by_label[label]
        items = []
        for it in s.get("items", []):
            src = it.get("sourceName", "")
            role = roles.get(src, "")
            if role:
                matched += 1
            total += 1
            items.append(
                {
                    "title": it.get("title", ""),
                    "source": src,
                    "source_role": role,
                    "summary": it.get("summary", ""),
                    "url": it.get("sourceUrl", ""),
                }
            )
        sections_out.append({"label": LABEL_SHORT[label], "items": items})

    out_data = {"date": api.get("date", date), "sections": sections_out}
    out.write_text(json.dumps(out_data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        f"wrote {out} — {total} items, {matched} role matched ({total - matched} missing)",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
