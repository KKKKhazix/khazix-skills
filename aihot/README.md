# AIHOT — Agent Skill

让支持 Agent Skills（`SKILL.md`）的工具直接用中文查询 [AIHOT](https://aihot.news)：最新精选、关键词动态、当前热点和事件来龙去脉、AI 日报、周报和月报、Codex 额度重置。

**装一次就好，以后不用再更新。** 这个 Skill 只负责把问题交给 AIHOT、把结果讲给你；查什么、怎么整理都在 AIHOT 服务器上完成，并持续改进。AIHOT 以后新增的能力，已经装好的 Skill 会自动用上。

基础能力长期保持匿名、只读、无需 API Key。本 Skill 遵循公开使用规则：个人非商业、公益非商业和组织内部使用免费；任何面向外部的商业产品、收费服务、客户交付、代理接口、数据转售、公开镜像或批量公开再分发，须事先取得书面授权。

## 安装前可审阅

- [SKILL.md](https://aihot.news/aihot-skill/SKILL.md)
- [安装包清单](https://aihot.news/aihot-skill/manifest.sha256)
- [install.sh](https://aihot.news/aihot-skill/install.sh)
- [GitHub 镜像](https://github.com/KKKKhazix/khazix-skills/tree/main/aihot)

安装包只有 3 个文件：

```text
SKILL.md
LICENSE
agents/openai.yaml
```

## 让 Agent 安装

把这句话发给你的 Agent：`请安装 AIHOT Skill：https://aihot.news/aihot-skill/README.md`

给 Agent 的做法：

- 能运行 Bash（macOS、Linux、WSL）：用下面的安装命令，Claude Code 用 `--target claude`，其它支持 Agent Skills 的工具用 `--target agents`。
- 不能运行 Bash（例如 Windows 原生环境）：不要把 Bash 命令粘贴到 PowerShell。按 [安装包清单](https://aihot.news/aihot-skill/manifest.sha256) 从 `https://aihot.news/aihot-skill/<文件名>` 下载其中 3 个文件，逐个核对 SHA-256，放进当前 Agent 实际读取的 skills 目录下名为 `aihot` 的文件夹，整体替换里面的旧内容。

## 命令行安装

以下 Bash 命令适用于 macOS、Linux 与 WSL。脚本不会猜测平台，必须显式指定 `--target` 或 `--dir`，无参数只显示帮助并退出。

Skill 正文安装到 Agent Skills 通用目录 `~/.agents/skills/aihot`（Codex、Gemini CLI、GitHub Copilot、OpenCode 共用）：

```bash
bash <(curl -fsSL https://aihot.news/aihot-skill/install.sh) --target agents
```

Claude Code 按官方约定从 `~/.claude/skills` 发现个人 Skill；下面的命令把正文装到通用目录，再建一个指向同一实体的兼容软链，不复制第二份：

```bash
bash <(curl -fsSL https://aihot.news/aihot-skill/install.sh) --target claude
```

装到自定义目录：

```bash
bash <(curl -fsSL https://aihot.news/aihot-skill/install.sh) \
  --dir "$HOME/path/to/skills/aihot"
```

安装器先把完整包下载到同一磁盘的临时目录，逐文件验证 SHA-256 与 Skill 身份，全部通过后才一次替换目标目录。人类说明 `README.md` 不会放进 Skill 安装目录。

安装器会在本地生成 `.aihot-actor-id`（权限 `0600`），更新时保留。它是可轮换的随机 UUID，仅用于把同一直接消费实例跨网页、Skill、MCP、RSS 与 API 去重，不是账号、API Key 或授权。从 AIHOT 接入页复制命令时可用 `--actor <uuid-v4>` 与其它渠道复用同一随机假名标识；不传也能正常使用。不希望参与跨渠道分析，就在安装命令后追加 `--no-actor`：安装器会保存本地退出标记，后续更新与旧目录迁移都不会重新生成 Actor，以后显式传入 `--actor <uuid-v4>` 才会重新加入。安装器还会在本地生成只忽略这两个文件的 `.gitignore`，避免项目级安装时误提交。

## 从旧版更新（最后一次）

旧版包括 1.x，以及 2026 年 9 月 30 日前装的 2.0.0。它们的目录里有 `references` 文件夹，`SKILL.md` 里写着 `/api/v1/items`。旧版还能用，但需要再更新一次，之后就再也不用更新了。

- 重新运行当初的安装命令（`--target` 或 `--dir` 与当初相同），或者把这句话发给 Agent：`请把我已安装的 AIHOT Skill 更新到最新版：https://aihot.news/aihot-skill/README.md`
- 更新必须落在当前 Agent 实际读取的那一份上；装到别处只会多出一份副本。
- 已是最终版的样子：安装目录里只有 `SKILL.md`、`LICENSE`、`agents/openai.yaml`（外加本地生成的 `.aihot-actor-id`、`.gitignore`），`SKILL.md` 里写着 `/api/v1/agent`。

安装器会检查以下旧位置，防止同名 Skill 被一个 Agent 重复发现：

```text
~/.claude/skills/aihot
~/.codex/skills/aihot
~/.gemini/skills/aihot
~/.copilot/skills/aihot
~/.config/opencode/skills/aihot
```

发现旧副本时默认停止，不会静默覆盖或再造一份。确认这些目录都是旧的 AIHOT Skill 后，显式迁移：

```bash
bash <(curl -fsSL https://aihot.news/aihot-skill/install.sh) \
  --target agents \
  --migrate-legacy
```

也可以用 `--dir <旧目录>` 原地更新单一旧副本；这种方式不会处理其它重复副本。迁移完成后，厂商目录不再保留独立副本；Claude Code 的兼容入口是指向 `~/.agents/skills/aihot` 的软链。

## 安装后验证

1. 重启 Agent 或开启新会话。
2. 让 Agent 列出它发现的 skills，确认只有一份 `aihot`。
3. 提问：`过去 24 小时 AI 圈最重要的 5 件事是什么？`

成功的回答会写明时间范围，给出中文摘要，并把标题链接到 AIHOT 站内阅读页。

## 能查询什么

AIHOT 目前能查的全部内容，以 [给 Agent 的使用说明](https://aihot.news/api/v1/agent) 为准；新能力会先加在那里。现在包括：

- 过去 24 小时或最近 7 天的精选与全部公开动态，可按模型、产品、行业、论文、教程与观点分类。
- 公司、产品、模型、人物和话题关键词（最近 7 天）。
- 现在最热的多源事件，以及每个事件的最新进展、报道时间线和 AI 综述。
- 最新或指定日期的 AI 日报，最新或指定一期的周报、月报。
- Codex 额度重置与 Tibo 发重置卡的预告和确认。

超过 7 天的历史搜索暂不保证；模型榜目前只有网页。

## 不装 Skill 也能用

- 让 Agent 读 [https://aihot.news/api/v1/agent](https://aihot.news/api/v1/agent)，按里面的说明查询。
- 支持远程 MCP 的客户端可以接 `https://aihot.news/api/mcp`，工具返回的内容与上面相同。

## 内容、许可与署名

- `LICENSE` 中的 MIT License 只覆盖 Skill 指令与随附文件。
- AIHOT 服务与数据输出适用 [AIHOT 公开使用规则](https://aihot.news/terms)。匿名、无需 API Key 只说明技术访问方式，不代表所有用途均获许可。
- 第三方原文及全文版权仍归原作者，不因经过 AIHOT 而改变。
- 个人非商业、公益非商业和组织内部使用免费。面向外部的商业产品、收费服务、客户交付、代理接口、数据转售、公开镜像、批量公开再分发或对外模型产品须先取得书面授权；仅标注「数据来源：AIHOT」不代表已取得授权。
- 授权联系 `agent@virxact.com`。attribution 与 canonical 继续用于机器识别和追溯；重要引用回第三方原文核对。

详细接入文档：[aihot.news/agent](https://aihot.news/agent)

反馈：[aihot.news/feedback](https://aihot.news/feedback)
