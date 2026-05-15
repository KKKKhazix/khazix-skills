#!/usr/bin/env python3
"""aihot daily HTML 渲染器：吃 remix 后的 JSON 出 self-contained HTML。

输入 JSON 结构（agent 在 share-daily 流程 Step 3 写出）：
{
  "date": "YYYY-MM-DD",
  "sections": [
    {
      "label": "模型",                 // 简化后的章节名
      "items": [
        {
          "title": "remix 后的标题",
          "source": "remix 后的信源",
          "summary": "API 原文 summary，原样照抄",
          "url": "https://..."
        }
      ]
    }
  ]
}

章节顺序、标签简化、title/source remix 都在 agent 那一侧完成。
本脚本只负责把结构化数据塞进 HTML 模板，**不做任何文本改写**。

用法：
  python3 render_daily_html.py <input.json> <output.html>
"""

import sys
import re
import json
import html
import base64
from pathlib import Path

DEFAULT_HERO = Path(__file__).resolve().parent.parent / "assets" / "hero.jpg"


def hero_data_uri(path: Path) -> str:
    """读取 hero 图，base64 编码为 data: URI；文件不存在返回空串。"""
    if not path.exists():
        return ""
    suffix = path.suffix.lower().lstrip(".")
    mime = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png", "webp": "image/webp", "svg": "image/svg+xml"}.get(suffix, "application/octet-stream")
    data = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{data}"


# URL：识别 http/https，遇到空白、引号、尖括号、中文标点、右括号停。
URL_RE = re.compile(r"https?://[^\s<>\"'　，。、；：！？）】」』]+")
# Hashtag：# 后跟 ASCII 字母/数字/_ 或中文。
HASHTAG_RE = re.compile(r"#[A-Za-z0-9_一-鿿]+")


def parse_source(name: str) -> tuple[str, str]:
    """从 API sourceName 解析出 (badge, body)。

    - "X：xxx (@yyy)"  → ("X", "xxx (@yyy)")
    - "xxx（RSS）"     → ("RSS", "xxx")
    - "xxx（网页）"     → ("网页", "xxx")
    - 其它             → ("", name)  原样
    """
    if name.startswith("X："):
        return "X", name[2:]
    for tail, badge in (("（RSS）", "RSS"), ("（网页）", "网页")):
        if name.endswith(tail):
            return badge, name[: -len(tail)]
    return "", name


def linkify_summary(text: str) -> str:
    """对 summary 做内联标记：URL → 可点击 link，hashtag → 弱化 span，其余文本 escape。"""
    placeholders: dict[str, str] = {}

    def stash(snippet: str) -> str:
        key = f"\x00P{len(placeholders)}\x00"
        placeholders[key] = snippet
        return key

    def sub_url(m: re.Match) -> str:
        url = m.group(0)
        # 修掉 URL 末尾可能粘连的标点（保守剥一层）
        trail = ""
        while url and url[-1] in ".,;:!?)）】」』":
            trail = url[-1] + trail
            url = url[:-1]
        if not url:
            return m.group(0)
        href = html.escape(url, quote=True)
        body = html.escape(url, quote=False)
        return stash(f'<a href="{href}" target="_blank" rel="noopener" class="inline-link">{body}</a>') + trail

    def sub_hashtag(m: re.Match) -> str:
        tag = m.group(0)
        return stash(f'<span class="hashtag">{html.escape(tag, quote=False)}</span>')

    text = URL_RE.sub(sub_url, text)
    text = HASHTAG_RE.sub(sub_hashtag, text)
    text = html.escape(text, quote=False)
    for key, snippet in placeholders.items():
        text = text.replace(key, snippet)
    return text


TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
<meta name="robots" content="noindex, nofollow">
<meta name="color-scheme" content="light">
<meta name="theme-color" content="#fdfcf9">
<title>{title}</title>
<style>
  :root {{
    --ink: #141413;
    --ink-soft: #3d3d3a;
    --ink-faint: #87867f;
    --bg: #f0eee6;
    --rule: #e0ddd2;
    --rule-soft: #e8e6dc;
    --num-ink: #b0aea5;
    --quote-bar: #c9a96b;
    --link: #c46849;
    --tag-bg: #e8e6dc;
    --tag-ink: #6b6862;
  }}
  * {{ box-sizing: border-box; }}
  html, body {{
    margin: 0; padding: 0;
    background: var(--bg);
    color: var(--ink);
    font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
    font-size: 17px;
    line-height: 1.75;
    -webkit-font-smoothing: antialiased;
    -webkit-text-size-adjust: 100%;
  }}
  .container {{ max-width: 720px; margin: 0 auto; padding: 48px 24px 80px; }}

  figure.hero {{
    margin: 12px 0 0;
    border-radius: 8px;
    overflow: hidden;
    line-height: 0;
  }}
  figure.hero img {{
    display: block;
    width: 100%;
    height: auto;
    aspect-ratio: 21 / 9;
    object-fit: cover;
  }}

  header.page {{
    margin-bottom: 0; padding-bottom: 0;
    text-align: center;
  }}
  header.page h1 {{
    font-size: 28px; font-weight: 700; margin: 0 0 8px;
    letter-spacing: -0.01em;
  }}
  header.page .meta {{
    color: var(--ink-faint); font-size: 14px;
  }}
  header.page .meta .sep {{ margin: 0 8px; color: var(--rule); }}

  .toolbar {{
    display: flex; justify-content: space-between; align-items: center;
    margin: 18px 0 56px; gap: 12px; padding: 0 8px;
  }}
  .toolbar .hint {{
    display: inline-flex; align-items: center; gap: 5px;
    margin: 0; color: var(--ink-faint); font-size: 13px; line-height: 1.4;
  }}
  .toolbar .hint svg {{ width: 13px; height: 13px; flex-shrink: 0; opacity: 0.85; }}
  .share-btn {{
    display: inline-flex; align-items: center; gap: 6px;
    padding: 0;
    background: transparent;
    border: none;
    color: var(--ink-faint); font: inherit; font-size: 13px; font-weight: 500;
    cursor: pointer;
    transition: color 0.15s;
    flex: 0 0 auto;
    -webkit-appearance: none;
    appearance: none;
  }}
  .share-btn:hover {{ color: var(--link); }}
  .share-btn svg {{ width: 14px; height: 14px; flex-shrink: 0; }}
  .share-btn.copied {{ color: var(--link); }}

  section.chapter {{ margin-top: 64px; }}
  section.chapter:first-of-type {{ margin-top: 0; }}
  section.chapter h2 {{
    font-size: 22px; font-weight: 700; margin: 0 0 32px;
    padding-left: 14px; border-left: 4px solid var(--link);
    letter-spacing: -0.01em;
    color: var(--ink);
  }}

  article.item {{
    position: relative;
    padding: 0 0 36px;
    margin-bottom: 36px;
    border-bottom: 1px solid var(--rule-soft);
  }}
  section.chapter article.item:last-of-type {{
    border-bottom: none;
    margin-bottom: 0;
    padding-bottom: 8px;
  }}
  article.item .num {{
    position: absolute;
    top: -4px;
    right: -2px;
    color: rgba(20, 20, 19, 0.045);
    font-size: 56px;
    font-weight: 800;
    line-height: 1;
    font-variant-numeric: tabular-nums;
    letter-spacing: -0.04em;
    pointer-events: none;
    user-select: none;
    z-index: 0;
  }}
  article.item .body {{ position: relative; z-index: 1; min-width: 0; padding-right: 64px; }}
  article.item .title {{
    margin: 0 0 10px;
    font-size: 19px; font-weight: 700;
    line-height: 1.45;
    letter-spacing: -0.005em;
    word-wrap: break-word;
  }}
  article.item .title a {{
    color: var(--ink);
    text-decoration: none;
    transition: color 0.15s;
  }}
  article.item .title a:hover {{ color: var(--link); }}
  article.item .source {{
    display: flex;
    align-items: center;
    gap: 7px;
    flex-wrap: wrap;
    margin: 0 0 12px;
    font-size: 13px;
    line-height: 1.4;
    color: var(--ink-faint);
  }}
  article.item .source .badge {{
    display: inline-block;
    padding: 1px 7px;
    background: var(--tag-bg);
    color: var(--tag-ink);
    font-size: 11px;
    font-weight: 600;
    line-height: 1.5;
    border-radius: 3px;
    letter-spacing: 0.02em;
    flex: 0 0 auto;
  }}
  article.item .source .src-body {{ color: var(--ink-faint); }}
  article.item .summary {{
    margin: 0 0 12px;
    color: var(--ink-soft);
    font-size: 16px;
    line-height: 1.7;
    word-wrap: break-word;
  }}
  article.item .summary .inline-link {{
    color: var(--ink-soft);
    text-decoration: underline dotted;
    text-decoration-color: var(--ink-faint);
    text-decoration-thickness: 1px;
    text-underline-offset: 3px;
    word-break: break-all;
    transition: color 0.15s, text-decoration-color 0.15s;
  }}
  article.item .summary .inline-link:hover {{
    color: var(--link);
    text-decoration: underline solid;
    text-decoration-color: var(--link);
  }}
  article.item .summary .hashtag {{
    color: var(--ink-faint);
    font-size: 0.88em;
    font-weight: 400;
    opacity: 0.6;
    margin-right: 2px;
  }}

  footer.page {{
    margin-top: 64px; padding-top: 24px;
    border-top: 1px solid var(--rule);
    color: var(--ink-faint); font-size: 13px; line-height: 1.6;
    text-align: center;
  }}
  footer.page a {{ color: var(--ink-faint); text-decoration: underline; }}

  @media (max-width: 600px) {{
    body {{ font-size: 16px; }}
    .container {{ padding: 28px 16px 64px; }}
    figure.hero {{ margin: 16px 0 0; border-radius: 6px; }}
    .toolbar {{ margin: 14px 0 40px; padding: 0 6px; }}
    .toolbar .hint {{ font-size: 12px; }}
    .share-btn {{ font-size: 13px; }}
    .share-btn svg {{ width: 14px; height: 14px; }}
    article.item .body {{ padding-right: 48px; }}
    header.page {{ margin-bottom: 32px; padding-bottom: 20px; }}
    header.page h1 {{ font-size: 24px; }}
    section.chapter {{ margin-top: 48px; }}
    section.chapter h2 {{ font-size: 19px; margin-bottom: 24px; }}
    article.item {{
      padding-bottom: 28px;
      margin-bottom: 28px;
    }}
    article.item .num {{
      font-size: 42px;
      top: -2px;
      right: 0;
    }}
    article.item .title {{ font-size: 18px; padding-right: 28px; }}
    article.item .summary {{ font-size: 15.5px; }}
  }}

</style>
</head>
<body>
<div class="container">
<header class="page">
  <h1>AI HOT 日报 · {date}</h1>
  <div class="meta">共 {total} 条<span class="sep">·</span>{section_stats}</div>
</header>
{hero}
<div class="toolbar">
  <p class="hint">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
      <circle cx="12" cy="12" r="10"/>
      <line x1="12" y1="16" x2="12" y2="12"/>
      <line x1="12" y1="8" x2="12.01" y2="8"/>
    </svg>
    <span>标题可跳转</span>
  </p>
  <button type="button" class="share-btn" onclick="shareCopy(this)" aria-label="复制本页链接">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
      <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/>
      <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>
    </svg>
    <span class="share-label">分享</span>
  </button>
</div>

{body}

<footer class="page">
  AI HOT 日报 · {date} · 共 {total} 条
</footer>
</div>
<script>
function shareCopy(btn) {{
  var url = window.location.href;
  var label = btn.querySelector('.share-label');
  if (!label.dataset.orig) label.dataset.orig = label.textContent;
  function done() {{
    label.textContent = '已复制';
    btn.classList.add('copied');
    setTimeout(function () {{
      label.textContent = label.dataset.orig;
      btn.classList.remove('copied');
    }}, 1800);
  }}
  if (navigator.clipboard && navigator.clipboard.writeText) {{
    navigator.clipboard.writeText(url).then(done, function () {{
      legacyCopy(url); done();
    }});
  }} else {{
    legacyCopy(url); done();
  }}
}}
function legacyCopy(text) {{
  var ta = document.createElement('textarea');
  ta.value = text;
  ta.style.position = 'fixed'; ta.style.opacity = '0';
  document.body.appendChild(ta);
  ta.select();
  try {{ document.execCommand('copy'); }} catch (e) {{}}
  document.body.removeChild(ta);
}}
</script>
</body>
</html>
"""


def render_item(idx: int, item: dict) -> str:
    title = html.escape(item.get("title", ""))
    # badge：优先用 source_role（aihot SSR 给的精细分类），fallback 走 parse_source 兜底
    role = item.get("source_role", "")
    src_text = item.get("source", "")
    if role:
        badge, body = role, src_text
    else:
        badge, body = parse_source(src_text)
    summary = linkify_summary(item.get("summary", ""))
    url = html.escape(item.get("url", ""), quote=True)
    source_html = ""
    if badge:
        source_html = f'<span class="badge">{html.escape(badge)}</span>'
    source_html += f'<span class="src-body">{html.escape(body)}</span>'
    return (
        '<article class="item">\n'
        '  <div class="body">\n'
        f'    <h3 class="title"><a href="{url}" target="_blank" rel="noopener">{title}</a></h3>\n'
        f'    <p class="source">{source_html}</p>\n'
        f'    <p class="summary">{summary}</p>\n'
        '  </div>\n'
        f'  <div class="num" aria-hidden="true">{idx}</div>\n'
        '</article>'
    )


def render_section(section: dict, idx_start: int) -> tuple[int, str]:
    label_raw = section.get("label", "")
    label = html.escape(label_raw)
    items_html = []
    idx = idx_start
    for item in section.get("items", []):
        items_html.append(render_item(idx, item))
        idx += 1
    items_str = "\n".join(items_html)
    section_html = (
        f'<section class="chapter" data-label="{label}">\n'
        f'<h2>{label}</h2>\n'
        f'{items_str}\n'
        '</section>'
    )
    return idx, section_html


def render(data: dict, hero_path=None) -> str:
    date = data.get("date", "")
    title = f"AI HOT 日报 · {date}"
    sections_html = []
    section_counts = []
    idx = 1
    for section in data.get("sections", []):
        label = section.get("label", "")
        n = len(section.get("items", []))
        section_counts.append((label, n))
        idx, section_html = render_section(section, idx)
        sections_html.append(section_html)
    total = idx - 1
    body_html = "\n\n".join(sections_html)
    section_stats = " · ".join(
        f"{html.escape(label)} {n}" for label, n in section_counts if n > 0
    )

    hero_uri = hero_data_uri(hero_path or DEFAULT_HERO)
    hero_html = (
        f'<figure class="hero"><img src="{hero_uri}" alt=""></figure>' if hero_uri else ""
    )

    return TEMPLATE.format(
        title=html.escape(title, quote=True),
        date=html.escape(date),
        total=total,
        section_stats=section_stats,
        hero=hero_html,
        body=body_html,
    )


def main() -> None:
    if len(sys.argv) < 3:
        print("Usage: render_daily_html.py <input.json> <output.html>", file=sys.stderr)
        sys.exit(1)

    inp = Path(sys.argv[1])
    out = Path(sys.argv[2])

    data = json.loads(inp.read_text(encoding="utf-8"))
    html_text = render(data)
    out.write_text(html_text, encoding="utf-8")
    print(f"wrote {out}", file=sys.stderr)


if __name__ == "__main__":
    main()
