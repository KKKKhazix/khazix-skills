# Khazix Skills

数字生命卡兹克开源的 AI Skills 合集。

这里是我自己在用的、经过长期打磨的 Skills，现在决定把它们完整地、一字不改地开源出来。

## 什么是 Skill

Skill 是遵循 [Agent Skills](https://agentskills.io) 开放标准的结构化指令集，由包含指令、脚本和参考资源的文件夹组成，用于扩展 AI Agent 的能力边界。Agent 会在相关场景下自动加载对应的 Skill，你也可以通过 `/skill-name` 手动调用。

Skill 的设计理念是**可组合、可移植、按需加载**。多个 Skill 可以协同工作，同一个 Skill 可以跨工具使用。它让你能够把领域专业知识打包成 AI 可以复用的模块，在特定场景下按照这套方法论来执行任务。

## 已开源的 Skills

| Skill | 说明 |
|-------|------|
| [**khazix-writer**](./khazix-writer/) | 卡兹克公众号长文写作 Skill，包含完整的写作风格规则、四层自检体系、内容方法论和风格示例库 |

## 安装

### 通过 Agent 安装

在 Claude Code、Codex、OpenClaw 等支持 Skill 的 Agent 中，直接对话：

```
安装这个 skill：https://github.com/KKKKhazix/khazix-skills
```

### 手动安装

1. 如果仓库已经发布了对应 Skill 的 `.skill` 安装包，优先在 [Releases](https://github.com/KKKKhazix/khazix-skills/releases) 页面下载
2. 如果仓库暂未提供 `.skill` 安装包，直接将对应 Skill 文件夹（例如 `khazix-writer/`）复制到对应工具的 Skills 目录下
3. 保持 Skill 文件夹名称和目录结构不变

各工具的 Skills 安装路径：

| 工具 | 路径 |
|------|------|
| Claude Code | `~/.claude/skills/` |
| OpenClaw | `~/.openclaw/skills/` |
| Codex | `~/.agents/skills/` |

## License

[MIT](./LICENSE)
