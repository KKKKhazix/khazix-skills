---
name: hub-architect
description: >
  把多个相关 Skill 组织成 Hub/Leaf 架构——一个入口路由 + 多个叶子模块。
  当用户的 Skill 越装越多、触发词开始打架、或者想按领域归类时触发。
  MUST trigger when user says: "整理 skills", "skill 太多了", "帮我归类",
  "建一个 hub", "把 X 和 Y 合到一起", "做一个统一入口", "路由 skill",
  "hub/leaf", "skill 架构", "skill 管理", or any phrase about organizing
  multiple skills into a unified structure.
---

# Hub Architect — Skill 组织架构师

> **跨平台 Agent Skill** — Claude Code · Codex · OpenCode · OpenClaw 通用。

你是一个 **Skill 架构师**。当用户的 Skill 数量增长到需要组织管理时，你帮他们把散装 Skill 组织成 Hub/Leaf 架构——一个路由入口管多个功能叶子。

## 为什么需要 Hub/Leaf 架构

装了 5 个以上 Skill 后，三个问题开始出现：

1. **触发词打架**：两个 Skill 都想响应"帮我处理文档"，Agent 不知道该加载哪个
2. **Token 浪费**：Agent 一次加载所有 Skill 的 SKILL.md，大部分跟当前任务无关
3. **维护噩梦**：改一个 Skill 的触发条件，要检查会不会误触发别的

Hub/Leaf 架构解决这三个问题：**一个 Hub 做路由器，按意图只加载一个 Leaf**。

## 核心概念

```
用户说"帮我提交 PR"
        ↓
   Hub SKILL.md（路由器）
   意图分类 → "这是 git 操作"
        ↓
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
| 触发词高度重叠 | ✅ 用 Hub 统一路由 | |
| 功能互补但领域不同 | ✅ 归到同一 Hub | |
| 用户经常连续使用 | ✅ 减少切换开销 | |
| 独立安装、独立更新 | | ✅ 互不干扰 |
| 使用频率极高、路径短 | | ✅ 减少路由开销 |

## 执行流程

### 第一步：盘点现有 Skill

列出现有的所有 Skill，逐个分析：

```bash
# Claude Code 全局 Skill 目录
ls ~/.claude/skills/

# 或者项目级
ls .claude/skills/
```

对每个 Skill 记录：
- **名称**
- **触发条件**（从 SKILL.md frontmatter 提取）
- **使用频率**（高/中/低）
- **领域标签**（git / web / doc / media / data / ...）

### 第二步：识别冲突和聚类

**冲突检测**：哪些 Skill 的触发词会打架？

```
冲突示例：
  Skill A: "帮我提交代码" → 加载 A
  Skill B: "帮我提交 PR"  → 加载 B
  用户说"帮我提交" → ？？？
```

**聚类分析**：哪些 Skill 属于同一领域？

```
聚类示例：
  [git] 领域：
    - github（gh CLI：issue, PR, Actions）
    - git-orchestrator（Git 生命周期：branch, commit, merge）

  [doc] 领域：
    - docx（Word 文档操作）
    - pdf（PDF 生成/转换）
    - pptx（PPT 制作）
```

### 第三步：设计 Hub 结构

为每个聚类创建一个 Hub：

```
{hub-name}/
├── SKILL.md              ← 路由器
├── modules/
│   ├── {leaf-1}/
│   │   └── LEAF.md       ← 叶子模块 1
│   ├── {leaf-2}/
│   │   └── LEAF.md       ← 叶子模块 2
│   └── ...
└── references/            ← 共享参考（可选）
    └── shared-guide.md
```

### 第四步：编写 Hub SKILL.md

Hub 的 SKILL.md 是**纯路由器**，不包含执行逻辑。标准结构：

```yaml
---
name: {hub-name}
description: >
  统一 {领域} 工作流路由器。当用户涉及 {领域列表} 操作时触发，
  按意图路由到对应的叶子模块。
---

# {hub-name}

## Trigger
- Route only. 分类意图，只加载一个叶子模块。
- 避免同时加载多个叶子，减少 token 开销。

## Purpose
- {领域描述}

## Leaf Mapping
- {leaf-1} -> modules/{leaf-1}/LEAF.md ({leaf-1 的一句话描述})
- {leaf-2} -> modules/{leaf-2}/LEAF.md ({leaf-2 的一句话描述})
- ...

## Routing Rules
1. 如果用户意图是 {条件 A}，加载 `{leaf-1}`。
2. 如果用户意图是 {条件 B}，加载 `{leaf-2}`。
3. 如果意图不明确，先问一个澄清问题再加载。
```

**路由规则的写法关键**：

- **一个规则对应一个叶子**，不要交叉
- **用用户会说的话描述**，不用内部术语
- **最后一条永远是"不明确就问"**，兜底防误触发

### 第五步：迁移 Leaf 模块

把已有的独立 Skill 迁移为 Hub 的叶子：

```bash
# 创建目录结构
mkdir -p {hub}/modules/{leaf-name}

# 移动 SKILL.md → LEAF.md（内容不变，改个名）
cp {old-skill}/SKILL.md {hub}/modules/{leaf-name}/LEAF.md

# 如果有 references/，一起迁移
cp -r {old-skill}/references/ {hub}/modules/{leaf-name}/references/ 2>/dev/null
```

**LEAF.md 和 SKILL.md 的区别**：
- SKILL.md 是独立入口，需要完整的触发条件描述
- LEAF.md 被 Hub 加载，触发条件由 Hub 统一管理，叶子本身只管执行

### 第六步：验证

```bash
# 检查目录结构
find {hub}/ -type f -name "*.md" | sort

# 检查 Hub 的路由规则覆盖所有叶子
grep -c "modules/" {hub}/SKILL.md  # 应等于叶子数量

# 模拟测试：用不同触发词测试路由是否正确
```

## 设计模式

### 模式一：按工具归类

最常见。同一工具链的不同操作归到一个 Hub。

```
git-hub/
├── SKILL.md           # "GitHub 操作" 或 "Git 版本控制" → 路由
├── modules/
│   ├── github/        # gh CLI：issue, PR, Actions, API
│   └── git-orchestrator/  # Git 生命周期：branch, commit, merge
```

路由规则：
1. issue/PR/CI/API → `github`
2. branch/commit/merge/rebase/push → `git-orchestrator`

### 模式二：按产出物归类

产出相同类型结果的不同方式归到一个 Hub。

```
doc-hub/
├── SKILL.md           # "文档操作" → 路由
├── modules/
│   ├── docx/          # Word 文档
│   ├── pdf/           # PDF 生成
│   └── pptx/          # PPT 制作
```

路由规则：
1. 文件是 .docx 或要求 Word → `docx`
2. 文件是 .pdf 或要求 PDF → `pdf`
3. 演示文稿/PPT → `pptx`

### 模式三：按意图深度归类

同一领域不同深度的操作归到一个 Hub。

```
web-hub/
├── SKILL.md           # "Web 相关" → 路由
├── modules/
│   ├── webapp-testing/       # 功能测试
│   ├── frontend-design/      # 前端设计
│   └── web-artifacts-builder/ # 构建产出物
```

路由规则：
1. 测试/验证/web app → `webapp-testing`
2. 设计/UI/CSS/布局 → `frontend-design`
3. 构建/打包/部署产出物 → `web-artifacts-builder`

## 注意事项

### Hub 本身不干活

Hub SKILL.md 只做路由，不包含任何执行逻辑。如果你发现自己在 Hub 里写了"具体怎么做某事"，说明那部分应该放到叶子模块里。

### 一次只加载一个叶子

这是 Hub/Leaf 架构的核心承诺。如果一个任务确实需要两个叶子的能力（比如"把 git log 输出写成 PDF 文档"），有两种处理方式：

1. **让用户明确**：问一句"这是 git 操作还是文档操作？"
2. **建一个编排叶子**：专门处理跨叶子的组合任务

### 触发词不重叠

每个叶子的触发词必须互斥。如果两个叶子都能响应同一个用户意图，要么合并它们，要么细化路由规则。

### 叶子可独立存在

从 Hub 里拿出来的叶子，放在独立目录里应该仍然能作为独立 Skill 使用。这意味着 LEAF.md 里应该保留完整的触发条件描述，Hub 的路由只是"快捷方式"而非"唯一入口"。

## 常见问题

**Q: Skill 多少个以上才需要 Hub？**
A: 没有硬性数字。当触发词开始打架、或者你发现自己经常手动切换 Skill 时，就该考虑了。一般 3-5 个同领域 Skill 是个好起点。

**Q: Hub 可以嵌套吗？**
A: 技术上可以，但不推荐。两层路由已经足够复杂，三层会让意图分类变得不可维护。如果真的需要，说明你的领域划分粒度有问题，先重新审视聚类。

**Q: 已经装了独立 Skill，怎么迁移到 Hub？**
A: 复制 SKILL.md 到 Hub 的 modules/{name}/LEAF.md，更新 Hub 的路由规则，然后删掉独立 Skill。注意保留 LEAF.md 里的完整触发条件，方便未来需要时拆出来。

**Q: 路由规则写错了怎么办？**
A: Agent 会加载错误的叶子模块，执行不符合预期。最安全的做法是路由规则最后加一条"不确定就问用户"的兜底规则。

## 参考资料

- **[references/hub-leaf-checklist.md](references/hub-leaf-checklist.md)** — Hub/Leaf 架构搭建清单，逐步检查用
- **[references/real-world-hubs.md](references/real-world-hubs.md)** — 真实 Hub 架构案例参考
