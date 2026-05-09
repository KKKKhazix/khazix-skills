# aihot · share-daily / test-daily 子命令规范

> **本文件不属于上游 KKKKhazix/khazix-skills，是 fork 仓库 MrArcrM/khazix-skills 的本地扩展。**
> SKILL.md 在末尾通过引用指向本文件——遇到 `share-daily` / `test-daily` 子命令时 agent 应先读本文件再执行。

## 触发条件

用户输入**字面包含**以下子命令字符串才触发本流程，其余 `/aihot` 用法走 SKILL.md 主流程：

| 子命令 | 行为 |
|---|---|
| `/aihot share-daily` | 拉今日日报，生成 PDF，发**分享群** |
| `/aihot share-daily YYYY-MM-DD` | 拉指定日期日报，生成 PDF，发**分享群** |
| `/aihot test-daily` | 拉今日日报，生成 PDF，发**测试群**（用于格式调试） |
| `/aihot test-daily YYYY-MM-DD` | 拉指定日期日报，生成 PDF，发**测试群** |

**字面匹配**：用户消息里必须出现 `share-daily` 或 `test-daily` 字符串，模糊表述（"分享日报"、"发到分享群"、"分享 daily"）**不触发**——避免误推送到生产群。

## 飞书 bot 与群配置

**bot**：lark-cli profile = `ai-digest`（即 AI-Daily-Digest 飞书机器人）。所有 lark-cli 调用必须显式 `--profile ai-digest`，**不要**用默认 profile（默认是 Claude Code App bot，不是本流程的发送方）。

**群 ID**（hardcode 在本文件，agent 直接读取）：

```
TEST_CHAT_ID  = oc_1ff1b4cc554f9dee3809000d90c9f383   # 测试群（飞书内显示名："Claude Code App"）
SHARE_CHAT_ID = oc_937244556a810e4996bfc221adb21794   # 分享群（飞书内显示名："AI俱乐部核心成员群"）
```

## 工作流（一气呵成，任一步失败即停 + 告知用户、绝不发群）

### Step 1 · 确认日期

- `date "+%Y-%m-%d"` 拿系统当日（**不**信对话注入的 currentDate）
- 用户没指定日期 → 默认今日
- 用户给了 `YYYY-MM-DD` 参数 → 用该日期，先校验格式正确

### Step 2 · 拉 API

```bash
UA="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
curl -sH "User-Agent: $UA" "https://aihot.virxact.com/api/public/daily/$DATE" -o /tmp/aihot-daily/aihot-$DATE.json
```

**错误处理**：
- HTTP 404（日报未生成 / 不存在）→ **告诉用户，停**：「2026-05-09 日报还没生成（北京时间 8:00 后才出），要不要拉昨天？」**不要静默 fallback** 到昨日。
- 其他 HTTP 错误 / curl 失败 → **告诉用户，停**。

### Step 3 · 渲染 markdown

#### 3.1 章节顺序（**必须**按此顺序，跟 API 返回顺序不一致）

**模型 → 产品 → 技巧 → 行业 → 论文**

API daily 返回 `sections[]` 顺序为：模型发布/更新 / 产品发布/更新 / 行业动态 / 论文研究 / 技巧与观点。**重排**为上面的 5 段顺序。

#### 3.2 章节标签简化

API `sections[].label` 直出长版（"模型发布/更新"、"产品发布/更新"、"行业动态"、"论文研究"、"技巧与观点"），**改成简版** H2：

| API label | 输出 H2 |
|---|---|
| 模型发布/更新 | 模型 |
| 产品发布/更新 | 产品 |
| 技巧与观点 | 技巧 |
| 行业动态 | 行业 |
| 论文研究 | 论文 |

#### 3.3 markdown 模板

```markdown
---
title: "AI HOT 日报 · YYYY-MM-DD"
---

# AI HOT 日报 · YYYY-MM-DD

## 模型

1. **<remix 标题>** — <remix 信源>

   <API 原文 summary，原样照抄不改写>

   <sourceUrl>

2. ...

## 产品

3. ...

...

## 论文

N. ...
```

**重要规则**：
- **标题** = remix（中文化 + 口语化 + 提取关键词，参考下方"标题 remix 风格"）
- **信源** = remix（短化，参考下方"信源 remix 映射"）
- **摘要正文** = API `summary` 字段**原样照抄**，**不改写、不压缩、不润色**
- **编号** = 跨章节贯穿 1..N，按章节新顺序编（不是按 API 原顺序）
- **没有**开头引用块（"时间窗 / 共 N 条 / 数据来自 ..."）
- **没有**结尾"数据来源 ..." 段
- **没有**章节内"⚠️ 跟前一天重合"等主动检测的提示
- **没有**前导 lead 段（即使 API 返回了 `lead` 字段也不渲染——本流程定位是"日报内容"，不要 metadata）

#### 3.4 标题 remix 风格

参考 5/8 ~ 5/9 PDF 验证过的风格——

- **保留事实和关键数字**：去营销腔 / 去废话，但事实和数字不删
- **英文 title 翻译成中文**：例 *Scaling Trusted Access for Cyber with GPT-5.5 and GPT-5.5-Cyber* → "GPT-5.5 与 GPT-5.5-Cyber 扩展可信网络安全访问"
- **过长中文 title 提取核心**：例 "在 Excel、PowerPoint、Word 和 Outlook 中与 Claude 协同工作" → "Claude 接入 Excel / PowerPoint / Word / Outlook"
- **加一个冒号副标题点出亮点**（可选）：例 "Ring-2.6-1T" → "Ring-2.6-1T：万亿参数'思维模型'"
- **保持 30 字以内**做硬约束（少数例外可放宽）

#### 3.5 信源 remix 映射

| API `sourceName` 范式 | 输出 |
|---|---|
| `X：宝玉 (@dotey)` | `宝玉（X）` |
| `X：OpenAI (@OpenAI)` | `OpenAI（X）` |
| `OpenAI：官网动态（RSS · 排除企业/客户案例）` | `OpenAI 官网` |
| `Anthropic：Research（发表成果 · 网页）` | `Anthropic Research` |
| `Hugging Face：Blog（RSS）` | `Hugging Face Blog` |
| `IT之家（RSS）` | `IT之家` |
| `Apple Machine Learning Research（RSS）` | `Apple Machine Learning Research` |
| `Google Blog：AI（RSS）` | `Google AI Blog` |
| `Claude Code：GitHub Releases（RSS）` | `Claude Code GitHub Releases` |
| `BAIR：Berkeley AI Research Blog` | `Berkeley AI Research Blog` |
| `Hacker News 热门（buzzing.cc 中文翻译）` | `Hacker News` |
| `Tomer Tunguz 博客（VC 分析）` | `Tomer Tunguz 博客` |
| `Runway：News（网页）` | `Runway News` |
| `Cursor Blog` | `Cursor Blog`（已经够短，不变） |
| `Simon Willison 博客` | `Simon Willison 博客`（不变） |
| 其他 X 账号 `X：xxx (@yyy)` | `xxx（X）` |
| 其他 RSS 类 | 去掉"（RSS）"等技术尾缀 |

### Step 4 · 生成 PDF

文件名规范：`AI HOT日报-YYYY-MM-DD.pdf`（中间一个半角空格、连字符、ISO 日期）

```bash
~/.claude/skills/md-to-pdf/scripts/md_to_pdf.sh \
  "/tmp/aihot-daily/AI HOT日报-$DATE.md" \
  "/tmp/aihot-daily/AI HOT日报-$DATE.pdf" \
  claude-white-larger
```

**主题必须 `claude-white-larger`**（手机阅读字号），不是默认 `claude-white`。

错误：md_to_pdf.sh 失败 → **告诉用户，停**。

### Step 5 · 发飞书

`cd` 到 PDF 所在目录后用相对路径（lark-cli `--file` 拒绝绝对路径）：

```bash
# share-daily 走分享群
cd /tmp/aihot-daily && lark-cli --profile ai-digest im +messages-send \
  --chat-id oc_937244556a810e4996bfc221adb21794 \
  --file "./AI HOT日报-$DATE.pdf" \
  --as bot

# test-daily 走测试群
cd /tmp/aihot-daily && lark-cli --profile ai-digest im +messages-send \
  --chat-id oc_1ff1b4cc554f9dee3809000d90c9f383 \
  --file "./AI HOT日报-$DATE.pdf" \
  --as bot
```

**`--profile ai-digest` 必加**——少了会用默认 Claude Code App bot 发，目标群里 AI-Daily-Digest 才是预期发送方。

错误：lark-cli 失败 → **告诉用户，停**，留 PDF 在本地（`/tmp/aihot-daily/AI HOT日报-$DATE.pdf`），告诉用户路径让他手动拖。

### Step 6 · 回报

成功后给用户：
- 子命令（share-daily / test-daily）+ 目标群名
- message_id
- create_time
- PDF 大小（KB）

不要把端点路径、curl 命令、内部状态泄漏到回复里。

## 常见错误对应

| 现象 | 根因 | 处置 |
|---|---|---|
| `curl` 返 HTTP 404 | 日报未生成（北京 8:00 前）/ 日期不存在 | 告知用户，问要不要拉昨日 |
| `lark-cli` 报 `--file must be a relative path` | 用了绝对路径 | cd 到 PDF 目录再用 ./ 相对路径 |
| `lark-cli` 报 token 错误 | ai-digest profile token 失效 | 告知用户运行 `lark-cli --profile ai-digest auth login` |
| 飞书消息发出但群里看不到文件 | bot 不在群里 | 告知用户把 AI-Daily-Digest 加进目标群 |
| md_to_pdf 失败说"主题不存在" | larger 主题没装 | 检查 `~/.claude/skills/md-to-pdf/themes/claude-white-larger/` |

## 不要做

- **不要**在用户没明说"share-daily" / "test-daily" 字符串时触发本流程
- **不要**把 share-daily 默认发到测试群（名字是 share-daily，发分享群是核心语义）
- **不要**用默认 lark-cli profile（必须 `--profile ai-digest`）
- **不要**改写 API summary 文本——本流程的"remix 风格"只对**标题 + 信源**适用
- **不要**主动加章节内"⚠️ 跟前一天重合" / "今日 N 条" / "数据来源" 等装饰性提示
- **不要**默认带 lead 段，即使 API 返回了 `lead` 字段
- **不要**自动调度（cron / launchd）跑本流程——用户每次手动 `/aihot share-daily` 才跑

## 决策记录

- 2026-05-09 · 创建本文件，定型 share-daily / test-daily 子命令规范，由郭大大与 honey-bee 在测试群迭代 4 版后落定
- 章节顺序"模型→产品→技巧→行业→论文" — 郭大大要求，把"技巧"提前到第三位（API 默认是最后一位）
- 章节标签简版 — 跟随 aihot.virxact.com 网站 UI 的视觉简化（API 返回的是长版）
