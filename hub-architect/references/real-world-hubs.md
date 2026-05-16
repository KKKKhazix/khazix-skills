# 真实 Hub 架构案例

以下案例来自实际使用中的 Hub/Leaf 架构（8 个 Hub，60+ 叶子），供参考。

## 案例一：git-hub（2 叶子）

**背景**：GitHub CLI 操作和 Git 生命周期管理，两个都能响应"帮我提交"。

```
git-hub/
  SKILL.md
  modules/
    github/           # gh CLI: issue, PR, Actions, API
    git-orchestrator/ # Git lifecycle: branch, commit, merge, rebase, push
```

路由：issue/PR/CI/API -> `github`，branch/commit/merge -> `git-orchestrator`

## 案例二：doc-hub（6 叶子）

**背景**：文档操作按产出物类型路由。

```
doc-hub/
  SKILL.md
  modules/
    docx/            # Word
    pdf/             # PDF
    pptx/            # PPT
    xlsx/            # Excel
    doc-coauthoring/ # 多人协作
    internal-comms/  # 内部沟通
```

路由：按文件扩展名和用户明确意图。用户说"帮我做个报告"时需确认文件类型。

## 案例三：web-hub（6 叶子）

**背景**：Web 开发涉及测试、设计、构建、搜索、数据采集等多个阶段。

```
web-hub/
  SKILL.md
  modules/
    webapp-testing/        # 功能测试
    frontend-design/       # 前端设计
    web-artifacts-builder/ # 构建打包
    perplexity-alternative/# 搜索问答
    quanzi-post-data-collector/ # 鹅圈子数据采集
    web-access/            # 网页抓取
```

路由：测试/验证 -> `webapp-testing`，设计/UI -> `frontend-design`，构建/打包 -> `web-artifacts-builder`

## 案例四：media-hub（7 叶子）

**背景**：视觉/视频/动图等媒体创作任务，每种媒体类型有完全不同的工具链。

```
media-hub/
  SKILL.md
  modules/
    algorithmic-art/           # 算法生成艺术
    brand-guidelines/          # 品牌视觉规范
    canvas-design/             # 画布设计
    theme-factory/             # 主题/配色生成
    video-subtitle-generator/  # 视频字幕
    remotion-best-practices/   # Remotion 最佳实践
    slack-gif-creator/         # Slack 动图
```

## 案例五：context-hub（6 叶子）

**背景**：上下文工程相关——压缩、降级、基础概念、记忆搜索。

```
context-hub/
  SKILL.md
  modules/
    context-compression/       # 上下文压缩
    context-degradation/       # 信息降级
    context-fundamentals/      # 基础概念
    agent-skills-context-engineering/ # Agent 上下文工程
    mem-search/                # 记忆搜索
    timeline-report/           # 时间线报告
```

## 案例六：execution-hub（12 叶子）

**背景**：执行模式和压力模式路由——PUA、MAMA、YES 等不同执行风格。

```
execution-hub/
  SKILL.md
  modules/
    pua/          # 标准 PUA 模式
    pua-global/   # 全局 PUA
    pua-en/       # 英文 PUA
    pua-ja/       # 日文 PUA
    pua-loop/     # 循环迭代 PUA
    mama/         # 妈妈模式
    yes/          # YES 模式
    p7/           # P7 模式
    p9/           # P9 模式
    p10/          # P10 模式
    pro/          # Pro 模式
    shot/         # Shot 模式
```

路由策略：关键词匹配 + 用户明确指定。高风险域，Gate A 要求 >= 95%。

## 案例七：lark-hub（22 叶子 + 3 快速路径）

**背景**：飞书/Lark 生态全量操作，是最大的 Hub。

```
lark-hub/
  SKILL.md           # 3 个快速路径 + 19 个按需路由
  modules/
    lark-base/       # 快速路径 1: 多维表格
    lark-doc/        # 快速路径 2: 云文档
    lark-im/         # 快速路径 3: 群消息
    lark-calendar/   # 日历
    lark-contact/    # 通讯录
    lark-drive/      # 云空间
    lark-event/      # 事件流
    lark-mail/       # 邮件
    lark-minutes/    # 会议纪要
    lark-openapi-explorer/ # API 探索
    lark-shared/     # 共享工具
    lark-sheets/     # 电子表格
    lark-skill-maker/# Skill 制作器
    lark-task/       # 任务
    lark-vc/         # 视频会议
    lark-whiteboard/ # 白板
    lark-wiki/       # 知识库
    lark-workflow-meeting-summary/ # 会议纪要工作流
    lark-workflow-standup-report/  # 站会报告工作流
    feishu-bitable-global-admin/   # 多维表格管理
    feishu-integration/            # 飞书集成
    feishu-preworkflow-builder-global/ # 工作流构建器
```

路由策略：高频场景走快速路径（直接匹配），中频走规则链，低频问用户。

## 案例八：obsidian-hub（2 叶子）

**背景**：Obsidian 笔记操作。

```
obsidian-hub/
  SKILL.md
  modules/
    obsidian-cil-global/ # CIL 全局操作
    obsidian-skills/     # Obsidian 技能
```

## 设计启示

1. **冲突是 Hub 诞生的信号**：每个 Hub 都因原有独立 Skill 开始打架而创建
2. **路由规则越简单越好**：一句话判断比复杂条件树更可靠
3. **兜底规则不能省**：用户意图模糊时，问一句比猜错好
4. **叶子数量 3-7 个为宜**：太少不值得建 Hub，太多路由规则难维护
5. **大型 Hub 需要分层**：10+ 叶子时用快速路径 + 规则链 + 兜底三层
6. **Hub 可以随时间增长**：先做核心 2-3 个叶子，新能力以叶子形式加入
7. **高风险域 Gate A 要求更高**：execution-hub 和 lark-hub 要求 >= 95%
