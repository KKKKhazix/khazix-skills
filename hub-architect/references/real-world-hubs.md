# 真实 Hub 架构案例

以下案例来自实际使用中的 Hub/Leaf 架构，供参考。

## 案例一：git-hub（Git/GitHub 操作路由）

**背景**：用户装了 GitHub CLI 操作 Skill 和 Git 生命周期管理 Skill，两个都能响应"帮我提交"。

**结构**：
```
git-hub/
├── SKILL.md
└── modules/
    ├── github/
    │   └── LEAF.md        # gh CLI：issue, PR, Actions, API 查询
    └── git-orchestrator/
        └── LEAF.md        # Git 版本控制：branch, commit, merge, rebase, push
```

**路由规则**：
1. issue/PR/CI/API/Release → `github`（平台操作）
2. branch/commit/merge/rebase/push/PR 生命周期 → `git-orchestrator`（版本控制）
3. 不明确 → 问用户"是 GitHub 平台操作还是 Git 版本控制？"

**关键设计**：把"GitHub 平台操作"（gh CLI）和"Git 版本控制"（git 命令）分开，虽然都跟"提交"有关，但工具和操作对象完全不同。

## 案例二：doc-hub（文档操作路由）

**背景**：用户经常需要处理 Word、PDF、PPT 三种文档，每种有不同的库和操作方式。

**结构**：
```
doc-hub/
├── SKILL.md
└── modules/
    ├── docx/
    │   └── LEAF.md        # python-docx：读写 Word
    ├── pdf/
    │   └── LEAF.md        # PDF 生成/转换/合并
    ├── pptx/
    │   └── LEAF.md        # python-pptx：PPT 制作
    ├── xlsx/
    │   └── LEAF.md        # openpyxl：Excel 操作
    └── doc-coauthoring/
        └── LEAF.md        # 多人文档协作
```

**路由规则**：
1. 文件扩展名 .docx 或明确要求 Word → `docx`
2. 文件扩展名 .pdf 或明确要求 PDF → `pdf`
3. 演示文稿/PPT/slide → `pptx`
4. 表格/Excel/数据表 → `xlsx`
5. 协作/多人编辑/版本管理 → `doc-coauthoring`
6. 不明确 → 问用户文件类型

**关键设计**：按产出物类型路由，用户说"帮我做个报告"时需要进一步确认是要 Word 还是 PDF。

## 案例三：web-hub（Web 工作流路由）

**背景**：Web 开发涉及测试、设计、构建等多个阶段，每个阶段有专门的 Skill。

**结构**：
```
web-hub/
├── SKILL.md
└── modules/
    ├── webapp-testing/
    │   └── LEAF.md        # Web 应用功能测试
    ├── frontend-design/
    │   └── LEAF.md        # 前端 UI/CSS 设计
    └── web-artifacts-builder/
        └── LEAF.md        # Web 项目构建打包
```

**路由规则**：
1. 测试/验证/检查 → `webapp-testing`
2. 设计/UI/CSS/布局/样式 → `frontend-design`
3. 构建/打包/部署/产出物 → `web-artifacts-builder`
4. 不明确 → 问用户处于哪个阶段

**关键设计**：按开发生命周期阶段路由，同一功能在不同阶段需要不同的 Skill。

## 案例四：media-hub（媒体创作路由）

**背景**：视觉/视频/动图等媒体创作任务，每种媒体类型有完全不同的工具链。

**结构**：
```
media-hub/
├── SKILL.md
└── modules/
    ├── algorithmic-art/
    │   └── LEAF.md        # 算法生成艺术
    ├── brand-guidelines/
    │   └── LEAF.md        # 品牌视觉规范
    ├── canvas-design/
    │   └── LEAF.md        # Canvas/画布设计
    ├── theme-factory/
    │   └── LEAF.md        # 主题/配色生成
    ├── video-subtitle-generator/
    │   └── LEAF.md        # 视频字幕生成
    └── slack-gif-creator/
        └── LEAF.md        # Slack 动图制作
```

**路由规则**：
1. 算法艺术/生成艺术 → `algorithmic-art`
2. 品牌/视觉规范/logo → `brand-guidelines`
3. 画布/布局/排版 → `canvas-design`
4. 主题/配色/风格 → `theme-factory`
5. 视频/字幕 → `video-subtitle-generator`
6. 动图/GIF → `slack-gif-creator`
7. 不明确 → 问用户具体需求

**关键设计**：媒体领域差异大，叶子数量多但各自独立，路由规则主要靠关键词匹配。

## 设计启示

从这些案例中总结的规律：

1. **冲突是 Hub 诞生的信号**：每个 Hub 的创建都是因为原有独立 Skill 开始打架
2. **路由规则越简单越好**：一句话判断比复杂条件树更可靠
3. **兜底规则不能省**：用户意图模糊时，问一句比猜错好
4. **叶子数量 3-7 个为宜**：太少不值得建 Hub，太多路由规则难维护
5. **Hub 可以随时间增长**：先做核心 2-3 个叶子，新能力以叶子形式加入
