---
name: hub-architect
description: >
  把多个相关 Skill 组织成 Hub/Leaf 架构——一个入口路由 + 多个叶子模块。
  包含完整的安全迁移流程（7 步）、触发回归测试（4 道门禁）、证据三角验证、
  备案隔离规则。不是"搭个路由就完事"，是经过 8 个 Hub、48 条回归用例、
  3 轮回归验证实战打磨出来的工程方法论。
  MUST trigger when user says: "整理 skills", "skill 太多了", "帮我归类",
  "建一个 hub", "把 X 和 Y 合到一起", "做一个统一入口", "路由 skill",
  "hub/leaf", "skill 架构", "skill 管理", "迁移 skill 到 hub",
  "触发测试", "回归测试", or any phrase about organizing multiple skills
  into a unified structure with safety guarantees.
---

# Hub Architect — Skill 组织架构师

> **跨平台 Agent Skill** — Claude Code · Codex · OpenCode · OpenClaw 通用。
> 方法论来源：8 个 Hub（60+ 叶子）、48 条回归用例、3 轮回归验证、L0-L4 沉淀体系。

你是一个 **Skill 架构师**。当用户的 Skill 数量增长到需要组织管理时，你帮他们把散装 Skill 组织成 Hub/Leaf 架构——一个路由入口管多个功能叶子。

**但搭路由只是开始。** 真正的难点是：迁移过程中不丢 Skill、迁移后触发准确率有保证、出问题能回滚。这个 Skill 覆盖从搭建到验证到回滚的完整工程链路。

---

## 第一部分：核心概念

### 为什么需要 Hub/Leaf 架构

装了 5 个以上 Skill 后，三个问题开始出现：

1. **触发词打架**：两个 Skill 都想响应"帮我处理文档"，Agent 不知道该加载哪个
2. **Token 浪费**：Agent 一次加载所有 Skill 的 SKILL.md，大部分跟当前任务无关
3. **维护噩梦**：改一个 Skill 的触发条件，要检查会不会误触发别的

Hub/Leaf 架构解决这三个问题：**一个 Hub 做路由器，按意图只加载一个 Leaf**。

```
用户说"帮我提交 PR"
        |
   Hub SKILL.md（路由器）
   意图分类 -> "这是 git 操作"
        |
   modules/git-orchestrator/LEAF.md（只加载这一个）
```

### 三层结构

| 层 | 文件 | 职责 |
|---|---|---|
| **Hub** | `SKILL.md` | 意图分类 + 路由分发，不含具体执行逻辑 |
| **Leaf** | `modules/{name}/LEAF.md` | 一个叶子 = 一个完整能力，可独立存在 |
| **Refs** | `references/*.md` | 共享参考文档（可选，叶子之间复用的资料放这里） |

### 什么适合做 Hub，什么保持独立

| 判断条件 | 做 Hub 子模块 | 保持独立 Skill |
|---|---|---|
| 触发词高度重叠 | YES - 用 Hub 统一路由 | |
| 功能互补但领域不同 | YES - 归到同一 Hub | |
| 用户经常连续使用 | YES - 减少切换开销 | |
| 独立安装、独立更新 | | YES - 互不干扰 |
| 使用频率极高、路径短 | | YES - 减少路由开销 |

---

## 第二部分：安全迁移流程（7 步）

**迁移不是"复制粘贴"。** 每一步都有明确的输入、输出和验证条件。跳步 = 埋雷。

### 第 1 步：基线快照

迁移前必须知道"现在有什么"。

```bash
# 盘点所有顶层 Skill
ls ~/.claude/skills/

# 计数
ls ~/.claude/skills/ | wc -l

# 检查重复冲突（同一领域有多个 Skill）
grep -r "description:" ~/.claude/skills/*/SKILL.md | sort
```

输出：
- 完整 Skill 清单（名称 + 触发条件 + 领域标签）
- 顶层 Skill 总数
- 重复冲突列表（哪些 Skill 的触发词打架）

### 第 2 步：隔离备份

**规则：备份放 workspace/backups，不进入 skills 根目录。**

```bash
# 创建备份目录（不在 skills 根内）
mkdir -p workspace/backups/

# 备份要迁移的 Skill
cp -r ~/.claude/skills/{skill-name} workspace/backups/{skill-name}.bak.$(date +%Y%m%d)
```

**为什么隔离？** 如果备份放在 `~/.claude/skills/backups/`，Agent 的 Skill 加载器会把备份里的 SKILL.md 也当成有效 Skill，导致重复触发。这是 Gate D 检查的内容。

### 第 3 步：替换并删除

**先复制到 Hub，验证通过后再删原入口。不要反过来。**

```bash
# 复制到 Hub 的 modules 目录
mkdir -p ~/.claude/skills/{hub}/modules/{leaf-name}/
cp ~/.claude/skills/{old-skill}/SKILL.md ~/.claude/skills/{hub}/modules/{leaf-name}/LEAF.md

# 验证 leaf 文件存在且非空
test -s ~/.claude/skills/{hub}/modules/{leaf-name}/LEAF.md && echo "OK" || echo "EMPTY!"

# 验证通过后才删除原入口
rm ~/.claude/skills/{old-skill}/SKILL.md
```

**LEAF.md vs SKILL.md 的区别**：
- SKILL.md 是独立入口，需要完整的触发条件描述
- LEAF.md 被 Hub 加载，触发条件由 Hub 统一管理，但保留完整触发条件以便独立使用

### 第 4 步：映射更新

Hub 的 SKILL.md 必须新增对应映射行。

```yaml
## Leaf Mapping
- {leaf-name} -> modules/{leaf-name}/LEAF.md ({一句话描述})

## Routing Rules
N. 如果用户意图是 {条件}，加载 `{leaf-name}`。
```

**检查清单**：
- Leaf Mapping 有对应条目
- Routing Rules 有对应规则
- 路由规则与其他叶子互斥

### 第 5 步：可调用性检查（证据三角）

**声称某 Skill 可调用，必须同时满足三个条件：**

| 证据类型 | 检查方法 | 不通过的后果 |
|---|---|---|
| **映射证据** | Hub SKILL.md 中存在该 leaf 映射行 | Agent 不知道有这个叶子 |
| **结构证据** | leaf 文件存在且非空 | 路由到了但找不到文件 |
| **行为证据** | 回归用例中 expectedLeaf == predictedLeaf | 路由到了但路由逻辑错误 |

```bash
# 映射证据
grep "{leaf-name}" ~/.claude/skills/{hub}/SKILL.md

# 结构证据
test -s ~/.claude/skills/{hub}/modules/{leaf-name}/LEAF.md && echo "OK"

# 行为证据（需要回归测试，见第三部分）
python scripts/run_trigger_regression.py
```

**三者缺一，不得宣称"已稳定可调用"。**

### 第 6 步：回归门禁

通过 4 道门禁才能放行。详见第三部分。

### 第 7 步：清理

```bash
# 清理空目录
find ~/.claude/skills/{old-skill}/ -type d -empty -delete

# 最终计数（应比基线少）
ls ~/.claude/skills/ | wc -l
```

---

## 第三部分：触发回归测试

迁移完不是"感觉对了"就行。需要结构化验证。

### 测试用例格式

每条用例是一个 JSON 对象：

```json
{
  "id": "DOC-001",
  "input": "帮我把这个 PDF 转成 Word",
  "expectedHub": "doc-hub",
  "expectedLeaf": "pdf",
  "risk": "high"
}
```

字段说明：
- `id`：用例编号，格式 `{HUB_PREFIX}-{NNN}`
- `input`：模拟用户输入
- `expectedHub`：期望命中的 Hub
- `expectedLeaf`：期望命中的叶子
- `risk`：`high`（高频/关键路径）或 `normal`

### 用例设计原则

1. **正例**：应触发指定 Hub/Leaf 的典型输入
2. **反例**：不应触发该 Hub 的边界输入
3. **混合例**：多意图输入，需选主路由
4. **每个 Hub 至少 6 条**，高风险域（execution-hub, lark-hub）至少 8 条

### 回归运行器

用 Python 脚本实现关键词路由预测，与期望值对比：

```python
import json
from pathlib import Path

cases = json.loads(Path("trigger-regression-cases.json").read_text())

def predict_route(text: str):
    """根据 Hub SKILL.md 的路由规则实现关键词匹配"""
    t = text.lower()

    # 按优先级检查每个 Hub 的触发关键词
    if any(k in t for k in ["pdf", "word", "docx", "ppt"]):
        leaf = "docx"
        if "pdf" in t:
            leaf = "pdf"
        elif "ppt" in t:
            leaf = "pptx"
        return "doc-hub", leaf, 0.91

    # ... 其他 Hub 的路由逻辑

    return "unknown", "unknown", 0.10

# 执行回归
results = []
hits = 0
for c in cases:
    hub, leaf, conf = predict_route(c["input"])
    ok = hub == c["expectedHub"] and leaf == c["expectedLeaf"]
    if ok:
        hits += 1
    results.append({
        "id": c["id"],
        "input": c["input"],
        "expected": f"{c['expectedHub']}/{c['expectedLeaf']}",
        "predicted": f"{hub}/{leaf}",
        "pass": ok
    })

accuracy = round(hits * 100 / len(results), 2)
print(f"Accuracy: {accuracy}%")
```

完整运行器代码见 [references/regression-runner.md](references/regression-runner.md)。

### 四道验收门禁

| 门禁 | 条件 | 必过？ | 含义 |
|---|---|---|---|
| **Gate A** | 主路由准确率 >= 92%，高风险域 >= 95% | MUST | 路由逻辑基本正确 |
| **Gate B** | 误触发率 <= 5%，漏触发率 <= 3% | MUST | 不会把用户导到错误的 Hub |
| **Gate C** | Token 开销下降 >= 25%，多叶子加载 <= 10% | SHOULD | 架构确实省了 token |
| **Gate D** | 备份目录不在 loader 根内 | MUST | 备份不会被误触发 |

**放行规则**：Gate A + B + D 全通过才允许继续清理旧入口。

**冻结规则**：连续两轮低于阈值，冻结新增迁移，先修复触发规则。

### 失败分类与修复

| 错误类型 | 表现 | 修复方向 |
|---|---|---|
| **Type A**：触发到错误 Hub | 用户说"帮我写 PPT"，路由到了 web-hub | 修正 Hub 的 Trigger 边界描述和排他条件 |
| **Type B**：Hub 正确但 Leaf 错误 | 路由到 doc-hub 但选了 docx 而不是 pdf | 补充 Leaf 映射关键词与负例 |
| **Type C**：触发了多个 Hub | 同时加载了 doc-hub 和 web-hub | 收紧"单次只加载一个 Leaf"的路由规则 |

### 报告模板

```markdown
# Trigger Regression Report

- Date: {date}
- Cases: {total}
- Main route accuracy: {accuracy}%
- False positive rate: {fp_rate}%
- Miss rate: {miss_rate}%

## Domain Accuracy
- {hub}: {pass}/{total} ({acc}%)

## Gate Results
- Gate A: {pass/fail}
- Gate B: {pass/fail}
- Gate C: {pass/fail}
- Gate D: {pass/fail}

## Failed Cases (Top 10)
- {id}: expected {expected}, got {predicted}
```

---

## 第四部分：五条强规则

这五条规则是 8 个 Hub 迁移中血的教训，每条都对应过一次线上事故。

### 规则 1：备份先行

**任何技能结构改动必须先备份，再替换验证，最后删除原入口。**

反模式：先删再建 -> 中途出错 -> Skill 丢失，无法回滚。

### 规则 2：加载隔离

**备份与审计产物不得进入全局技能加载根目录。**

反模式：备份放在 `~/.claude/skills/backups/` -> Agent 把备份当有效 Skill -> 重复触发。

### 规则 3：回归放行

**结构变更后必须通过 Gate A/B/D 才允许放行。**

反模式："我试了两个用例没问题" -> 上线后高频场景路由错误。

### 规则 4：证据三角

**声称某 Skill 可调用时必须同时提供映射证据、结构证据、行为证据。**

反模式："Hub 里写了映射行" -> 但 leaf 文件是空的 -> 路由到了找不到。

### 规则 5：双根复审

**迁移完成必须同时审计 .agents 与 .claude，不得以单根结果放行。**

反模式：只查了 `.claude/skills/` -> 遗漏了 `.agents/skills/` 里的同名 Skill。

---

## 第五部分：备案与回滚

### 备案清单

每次迁移必须记录：

```json
{
  "phase": "phase-N",
  "date": "2026-04-20",
  "skills_migrated": ["skill-a", "skill-b"],
  "backup_paths": [
    "workspace/backups/skill-a.bak.20260420",
    "workspace/backups/skill-b.bak.20260420"
  ],
  "regression_report": "docs/trigger-regression-report-roundN.json"
}
```

### 回滚流程

迁移失败时：

```bash
# 1. 从备份恢复原 Skill
cp -r workspace/backups/{skill-name}.bak.* ~/.claude/skills/{skill-name}/

# 2. 从 Hub 中移除对应 leaf
rm ~/.claude/skills/{hub}/modules/{leaf-name}/LEAF.md

# 3. 从 Hub SKILL.md 中删除映射行和路由规则

# 4. 重新跑回归测试，确认恢复到基线水平
python scripts/run_trigger_regression.py
```

**回滚触发条件**：
- Gate A/B/D 任一必过门禁失败
- 连续两轮回归低于阈值
- 用户手动要求回滚

---

## 第六部分：设计模式

### 模式一：按工具归类

同一工具链的不同操作归到一个 Hub。

```
git-hub/
  SKILL.md
  modules/
    github/           # gh CLI: issue, PR, Actions, API
    git-orchestrator/ # Git lifecycle: branch, commit, merge
```

路由规则：
1. issue/PR/CI/API -> `github`
2. branch/commit/merge/rebase/push -> `git-orchestrator`

### 模式二：按产出物归类

产出相同类型结果的不同方式归到一个 Hub。

```
doc-hub/
  SKILL.md
  modules/
    docx/           # Word
    pdf/            # PDF
    pptx/           # PPT
    xlsx/           # Excel
```

路由规则：
1. .docx or Word -> `docx`
2. .pdf or PDF -> `pdf`
3. PPT/slide -> `pptx`
4. Excel/table -> `xlsx`

### 模式三：按意图深度归类

同一领域不同深度的操作归到一个 Hub。

```
web-hub/
  SKILL.md
  modules/
    webapp-testing/        # functional testing
    frontend-design/       # UI/CSS design
    web-artifacts-builder/ # build & package
```

### 模式四：大型 Hub（10+ 叶子）

当叶子超过 10 个，路由策略需要分层：

```
lark-hub/
  SKILL.md           # 22 leaves, 3 fast-path
  modules/
    lark-base/     # fast-path 1
    lark-doc/      # fast-path 2
    lark-im/       # fast-path 3
    lark-calendar/
    lark-drive/
    ... (17 more)
```

路由策略：
1. 高频场景走快速路径（直接匹配，不走规则链）
2. 中频场景走 Routing Rules
3. 低频场景走兜底（问用户）

---

## 第七部分：Hub SKILL.md 模板

```yaml
---
name: {hub-name}
description: >
  Unified {domain} workflow router. Trigger for {domain list} operations
  and route to leaf skills on demand.
---

# {hub-name}

## Trigger
- Route only. Classify intent and load only one leaf.
- Avoid broad multi-leaf loading to reduce token overhead.

## Purpose
- {domain description}

## Leaf Mapping
- {leaf-1} -> modules/{leaf-1}/LEAF.md ({one-line description})
- {leaf-2} -> modules/{leaf-2}/LEAF.md ({one-line description})
- ...

## Routing Rules
1. If user intent is {condition A}, load `{leaf-1}`.
2. If user intent is {condition B}, load `{leaf-2}`.
3. If intent is unclear, ask one disambiguation question before loading.

## Migration Notes
- Original SKILL.md files were backed up to workspace/backups before replacement.
- Leaf modules keep original guidance; hub performs first-pass routing only.
- If rollback is needed, restore from workspace/backups manifest.
```

---

## Common Questions

**Q: How many skills before I need a Hub?**
A: When trigger words start clashing or you find yourself manually switching skills. 3-5 same-domain skills is a good starting point.

**Q: Can Hubs nest?**
A: Not recommended. Two layers of routing is complex enough; three makes intent classification unmanageable.

**Q: What if routing is wrong after migration?**
A: Run regression to identify Type A/B/C errors, fix per the triage table. If two consecutive rounds fail, trigger rollback.

**Q: Is regression testing mandatory?**
A: Yes. Gate A/B/D are must-pass. "I tried two cases and it worked" != "48 cases all pass".

**Q: No Python environment for regression?**
A: Manually walk through core cases (at least 3 positive + 1 negative per Hub), record pass rate. But Python is recommended for full regression.

---

## References

- **[references/hub-leaf-checklist.md](references/hub-leaf-checklist.md)** - Setup checklist (before/during/after)
- **[references/real-world-hubs.md](references/real-world-hubs.md)** - 8 real Hub architecture examples
- **[references/strong-rules.md](references/strong-rules.md)** - 5 strong rules with anti-patterns
- **[references/regression-runner.md](references/regression-runner.md)** - Python regression runner full code
