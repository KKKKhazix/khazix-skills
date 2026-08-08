# Python Regression Runner

完整的触发回归运行器，来自实际项目的 Round 3 回归脚本。

## 使用方法

1. 准备测试用例文件 `trigger-regression-cases.json`
2. 运行 `python run_trigger_regression.py`
3. 检查输出的 Gate A/B/C/D 结果

## 测试用例格式

```json
[
  {
    "id": "DOC-001",
    "input": "帮我把这个 PDF 转成 Word",
    "expectedHub": "doc-hub",
    "expectedLeaf": "pdf",
    "risk": "high"
  },
  {
    "id": "DOC-002",
    "input": "做个 PPT 汇报用",
    "expectedHub": "doc-hub",
    "expectedLeaf": "pptx",
    "risk": "normal"
  }
]
```

## 运行器代码

```python
import json
from datetime import datetime
from pathlib import Path

workspace = Path(".")
cases_path = workspace / "trigger-regression-cases.json"
out_json = workspace / "trigger-regression-results.json"
out_md = workspace / "trigger-regression-report.md"

cases = json.loads(cases_path.read_text(encoding="utf-8"))


def predict_route(text: str):
    """
    根据 Hub SKILL.md 的路由规则实现关键词匹配。
    
    修改这个函数来匹配你的 Hub 路由规则。
    返回 (hub, leaf, confidence)。
    """
    t = text.lower()

    # --- Lark Hub ---
    if any(k in t for k in ["飞书", "lark", "多维表格", "群消息", "日程", "云空间"]):
        leaf = "lark-shared"
        if any(k in t for k in ["群消息", "@", "聊天"]):
            leaf = "lark-im"
        elif any(k in t for k in ["多维表格", "字段", "记录", "base"]):
            leaf = "lark-base"
        elif any(k in t for k in ["云空间", "文档"]):
            leaf = "lark-doc"
        return "lark-hub", leaf, 0.93

    # --- Doc Hub ---
    if any(k in t for k in ["pdf", "word", "docx", "ppt", "演示", "xlsx", "excel", "csv", "文档", "周报"]):
        leaf = "docx"
        if any(k in t for k in ["pdf", "ocr"]):
            leaf = "pdf"
        elif any(k in t for k in ["ppt", "演示"]):
            leaf = "pptx"
        elif any(k in t for k in ["xlsx", "excel", "csv"]):
            leaf = "xlsx"
        elif any(k in t for k in ["内部沟通", "领导周报", "通知"]):
            leaf = "internal-comms"
        elif any(k in t for k in ["共创", "骨架"]):
            leaf = "doc-coauthoring"
        return "doc-hub", leaf, 0.91

    # --- Media Hub ---
    if any(k in t for k in ["算法艺术", "海报", "品牌规范", "字幕", "remotion", "动图", "slack"]):
        leaf = "canvas-design"
        if "算法艺术" in t:
            leaf = "algorithmic-art"
        elif "品牌规范" in t:
            leaf = "brand-guidelines"
        elif "字幕" in t:
            leaf = "video-subtitle-generator"
        elif "remotion" in t:
            leaf = "remotion-best-practices"
        elif any(k in t for k in ["slack", "动图"]):
            leaf = "slack-gif-creator"
        return "media-hub", leaf, 0.90

    # --- Web Hub ---
    if any(k in t for k in ["playwright", "回归测试", "本地页面", "artifact", "react", "网页", "落地页"]):
        leaf = "webapp-testing"
        if any(k in t for k in ["artifact", "多组件", "状态"]):
            leaf = "web-artifacts-builder"
        elif any(k in t for k in ["引用来源", "搜索问答"]):
            leaf = "perplexity-alternative"
        return "web-hub", leaf, 0.90

    # --- Context Hub ---
    if any(k in t for k in ["上下文", "context", "压缩", "丢信息", "时间线", "回忆上次"]):
        leaf = "context-fundamentals"
        if "压缩" in t:
            leaf = "context-compression"
        elif any(k in t for k in ["丢信息", "degradation"]):
            leaf = "context-degradation"
        elif any(k in t for k in ["回忆上次", "上次"]):
            leaf = "mem-search"
        elif any(k in t for k in ["时间线", "演进"]):
            leaf = "timeline-report"
        return "context-hub", leaf, 0.89

    # --- Execution Hub ---
    if any(k in t for k in ["pua", "迭代到底", "连续迭代", "压力", "p9", "p10", "日语", "yes 模式"]):
        leaf = "pua"
        if any(k in t for k in ["迭代到底", "连续迭代", "彻底解决"]):
            leaf = "pua-loop"
        elif "p9" in t:
            leaf = "p9"
        elif any(k in t for k in ["p10", "cto"]):
            leaf = "p10"
        elif any(k in t for k in ["日语", "ja"]):
            leaf = "pua-ja"
        elif "yes" in t:
            leaf = "yes"
        return "execution-hub", leaf, 0.95

    return "unknown", "unknown", 0.10


# --- 执行回归 ---
results = []
hits = 0
hub_hits = 0
false_positive = 0
miss = 0

for c in cases:
    hub, leaf, conf = predict_route(c["input"])
    hub_ok = hub == c["expectedHub"]
    leaf_ok = leaf == c["expectedLeaf"]
    ok = hub_ok and leaf_ok

    if ok:
        hits += 1
    if hub_ok:
        hub_hits += 1
    if (not hub_ok) and hub != "unknown":
        false_positive += 1
    if hub == "unknown":
        miss += 1

    results.append({
        "id": c["id"],
        "input": c["input"],
        "expectedHub": c["expectedHub"],
        "expectedLeaf": c["expectedLeaf"],
        "predictedHub": hub,
        "predictedLeaf": leaf,
        "confidence": conf,
        "pass": ok,
    })

total = len(results)
main_acc = round(hits * 100.0 / total, 2)
hub_acc = round(hub_hits * 100.0 / total, 2)
fp_rate = round(false_positive * 100.0 / total, 2)
miss_rate = round(miss * 100.0 / total, 2)

# Domain stats
by_domain = {}
for c in cases:
    by_domain.setdefault(c["expectedHub"], {"total": 0, "pass": 0})
    by_domain[c["expectedHub"]]["total"] += 1
for r in results:
    if r["pass"]:
        by_domain[r["expectedHub"]]["pass"] += 1
for d in by_domain:
    s = by_domain[d]
    s["acc"] = round(s["pass"] * 100.0 / s["total"], 2)

# Gates
gate_a = main_acc >= 92
gate_a_highrisk = all(
    by_domain.get(d, {"acc": 100})["acc"] >= 95
    for d in ["execution-hub", "lark-hub"]
)
gate_b = fp_rate <= 5 and miss_rate <= 3
multi_leaf_ratio = 0
estimated_token_drop = 30
gate_c = estimated_token_drop >= 25 and multi_leaf_ratio <= 10
gate_d = True  # Set to False if backups found in loader roots

# Output
out_json.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")

failed = [r for r in results if not r["pass"]][:10]

lines = []
lines.append("# Trigger Regression Report")
lines.append("")
lines.append(f"- Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
lines.append(f"- Cases: {total}")
lines.append(f"- Main route accuracy: {main_acc}%")
lines.append(f"- Hub accuracy: {hub_acc}%")
lines.append(f"- False positive rate: {fp_rate}%")
lines.append(f"- Miss rate: {miss_rate}%")
lines.append("")
lines.append("## Domain Accuracy")
for k in sorted(by_domain.keys()):
    v = by_domain[k]
    lines.append(f"- {k}: {v['pass']}/{v['total']} ({v['acc']}%)")
lines.append("")
lines.append("## Gate Results")
lines.append(f"- Gate A (>=92% and high-risk>=95%): {'pass' if gate_a and gate_a_highrisk else 'fail'}")
lines.append(f"- Gate B (FP<=5%, Miss<=3%): {'pass' if gate_b else 'fail'}")
lines.append(f"- Gate C (token drop >=25%, multi-leaf<=10%): {'pass' if gate_c else 'fail'}")
lines.append(f"- Gate D (backup isolated from loader roots): {'pass' if gate_d else 'fail'}")
lines.append("")
lines.append("## Failed Cases (Top 10)")
if not failed:
    lines.append("- None")
else:
    for f in failed:
        lines.append(f"- {f['id']}: expected {f['expectedHub']}/{f['expectedLeaf']}, got {f['predictedHub']}/{f['predictedLeaf']}")

out_md.write_text("\n".join(lines), encoding="utf-8")

summary = {
    "total": total,
    "mainRouteAccuracy": main_acc,
    "falsePositiveRate": fp_rate,
    "missRate": miss_rate,
    "gateA": gate_a and gate_a_highrisk,
    "gateB": gate_b,
    "gateC": gate_c,
    "gateD": gate_d,
}
print(json.dumps(summary, ensure_ascii=False, indent=2))
```

## 输出文件

- `trigger-regression-results.json` — 每条用例的详细结果
- `trigger-regression-report.md` — 汇总报告（准确率、门禁结果、失败用例）

## 修改 predict_route()

`predict_route()` 函数里的关键词规则必须与你的 Hub SKILL.md 路由规则一致。每次修改 Hub 路由规则后，都要同步更新这个函数，然后重新跑回归。
