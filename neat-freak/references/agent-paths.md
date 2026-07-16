# Agent 记忆与配置路径速查

不同 agent 平台的记忆系统和项目配置文件位置不一样。执行第一步盘点时按你正在使用的平台查这张表。

## Claude Code

| 用途 | 路径 |
|---|---|
| 跨会话记忆(全局) | `~/.claude/projects/<encoded-project-path>/memory/` |
| 记忆索引文件 | `~/.claude/projects/<...>/memory/MEMORY.md` |
| 全局指令 | `~/.claude/CLAUDE.md` |
| 项目级指令 | 项目根 `CLAUDE.md`(可层级嵌套) |
| Skills 目录 | `~/.claude/skills/<name>/SKILL.md` |

记忆文件用 YAML frontmatter:`name`、`description`、`type`(user / feedback / project / reference)。

## OpenAI Codex

| 用途 | 路径 |
|---|---|
| 跨会话指令(全局，手改、权威) | `~/.codex/AGENTS.md` 或 `$CODEX_HOME/AGENTS.md` |
| 项目级指令 | 项目根 `AGENTS.md`(可层级嵌套；常软链到 `CLAUDE.md`) |
| 项目级 override | `AGENTS.override.md`(若存在,覆盖同目录 AGENTS.md) |
| 自动记忆库(机器生成) | `~/.codex/memories/`(git 仓)：`MEMORY.md` 索引 + `memory_summary.md` + `raw_memories.md` + `rollout_summaries/` |
| 全局 Skills | `~/.codex/skills/<name>/SKILL.md` |
| 钉住的记忆型 Skill | `~/.codex/memories/skills/<name>/SKILL.md` |
| 项目内 Skills | 项目内 `.codex/skills/<name>/` |

**纠正旧说法**：Codex **有**独立记忆库 `~/.codex/memories/`，但它是**机器自动生成**的——由会话 rollout 经 Chronicle 管线蒸馏（`rollout_summaries/` → `raw_memories.md` → `MEMORY.md`）。所以同步时分两层处理：

- **手改、权威的跨会话事实** → 写进 `~/.codex/AGENTS.md`（全局）或项目根 `AGENTS.md`（项目级，aihot 即软链 CLAUDE.md）。这是 neat-freak 真正要对齐的目标。
- **`~/.codex/memories/` 里的 rollout 派生文件（MEMORY.md / raw_memories.md / memory_summary.md）不要手改**——它们是「某次会话里做过 X」的历史记录，会按 rollout 重新生成，手删等于白删。把功夫花在 AGENTS.md。
- **唯一该手动清的**：`~/.codex/memories/skills/<feature>/` 与 `~/.codex/skills/<feature>/` 下的**死 skill**（指向已退役功能的、不会自动重生）。退役一个功能时一并删掉对应 skill 目录（在 memories git 仓里 commit，可审计）。

发现项目里有 `TEAM_GUIDE.md` 或 `.agents.md` 也要看——这是 Codex 的 fallback 文件名。

## GitHub Copilot

| 用途 | 路径 |
|---|---|
| 项目级主指令 | 项目根 `AGENTS.md`（开放标准,可层级嵌套）**或** `.github/copilot-instructions.md`（二选一,不要双主文件） |
| 文件级指令 | `.github/instructions/*.instructions.md` |
| 自定义 agents | `.github/agents/*.agent.md` |
| Prompts | `.github/prompts/*.prompt.md` |
| 项目级 skills | `.github/skills/<name>/SKILL.md`、`.agents/skills/<name>/SKILL.md`、`.claude/skills/<name>/SKILL.md` |
| 用户级 skills | `~/.copilot/skills/<name>/SKILL.md`、`~/.agents/skills/<name>/SKILL.md`、`~/.claude/skills/<name>/SKILL.md` |
| Hooks（条件检查） | `.github/hooks/*.json` |

Copilot 没有独立的"记忆索引 + 记忆文件"机制。对 neat-freak 来说,优先盘点 `AGENTS.md` 或 `.github/copilot-instructions.md`,再看 Copilot 相关配置目录即可。

执行 neat-freak 第一步时,如果当前平台是 GitHub Copilot,至少按下面顺序盘点:

1. 先确认项目级主指令到底是哪一个: `AGENTS.md` 还是 `.github/copilot-instructions.md`。如果两者都存在且都写实质内容,标记为待整理。
2. 再枚举 `.github/instructions/` 看有没有按文件或任务范围生效的规则。
3. 再枚举 `.github/agents/`、`.github/skills/`、`.agents/skills/`,判断有没有项目级工作流知识需要同步。
4. `.github/prompts/` 作为中优先级检查:只要仓库把 prompt 当成团队交付物,就要一起盘点。
5. `.github/hooks/` 只在仓库明确依赖 hook 做策略校验、自动注入上下文或阻止危险操作时检查;不要把所有 hook 都默认抬到最高优先级。

如果你在 Copilot 仓库里看到 `.claude/skills/`,不要直接跳过。Copilot 会扫描这类目录,所以这些 skill 也属于有效知识面。

## OpenClaw

| 用途 | 路径 |
|---|---|
| 用户级 skills | `~/.openclaw/skills/<name>/SKILL.md`（首次运行自动创建） |
| 项目级 skills | `.openclaw/skills/<name>/SKILL.md`（仓库根目录下） |
| Workspace skills | 当前 workspace 的 `skills/` 目录 |

**加载优先级**：workspace > project-agent > personal-agent > managed/local > bundled > extra dirs。同名 skill 高优先级覆盖低优先级。

OpenClaw 没有独立的"记忆文件 + 索引"机制，跨会话信息可放在项目根的 markdown（CLAUDE.md / AGENTS.md / 等价文件）里，参照 Codex 的做法。frontmatter 支持 `metadata.openclaw` 字段做加载时的 gating（按 OS、环境变量、二进制依赖筛选），但不是 neat-freak 必需的。

## OpenCode

| 用途 | 路径 |
|---|---|
| 全局配置 | `~/.config/opencode/` |
| 项目配置 | `.opencode/` |
| Skills 目录(项目) | `.opencode/skills/`、`.claude/skills/`、`.codex/skills/` 都会被扫描 |
| Skills 目录(全局) | `~/.config/opencode/skills/`、`~/.claude/skills/`、`~/.codex/skills/` |

OpenCode 同时读取 Claude Code 和 Codex 的目录,所以同一个 skill 装在 `~/.claude/skills/` 下的话三家都能识别。OpenClaw 走自己的 `~/.openclaw/skills/`，需要单独装一份（或用符号链接）。

## 如果当前 agent 没有独立记忆系统

跳过"记忆"那一层,把功夫全花在:
- 项目根 markdown(CLAUDE.md / AGENTS.md / 本平台等价文件)
- README.md
- docs/

仍然是有效的同步——记忆是锦上添花,docs 才是项目知识的最低保障。

## 跨平台共存策略

如果一个项目同时被 Claude Code 用户和 Codex 用户使用:

- **`CLAUDE.md` 是真身,`AGENTS.md` 是指向它的软链**(`ln -s CLAUDE.md AGENTS.md`),永远只编辑 CLAUDE.md
- **绝不允许两份独立维护**——两处真相必然分叉,分叉必然有一边烂。发现两份内容不一致的独立文件,按 SKILL.md 第二步的处置分级走:合并需要人工确认哪边是权威,列「待你拍板」
- 若工作空间层级规则对同源机制另有声明,以工作空间规则为准
- docs/ 和 README 是平台中立的,不需要分两份
