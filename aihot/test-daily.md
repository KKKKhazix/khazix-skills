# aihot · test-daily 子命令规范（HTML 新流程）

> **本文件由 fork 仓库 MrArcrM/khazix-skills 维护，不属于上游 KKKKhazix/khazix-skills。**
> 触发字面 `/aihot test-daily` / `/aihot test-daily YYYY-MM-DD` 时，agent 先读本文件再执行。
>
> **流程定位**：HTML + share-html 链接 + 飞书短消息（替代旧的 markdown → PDF 上传附件）。share-daily 暂时还在 PDF 旧流程（见 `./share-daily.md`），等 test-daily 在测试群迭代稳定后再 apply 到 share-daily。

## 触发条件

用户输入**字面包含** `test-daily` 字符串才触发本流程：

| 子命令 | 行为 |
|---|---|
| `/aihot test-daily` | 拉今日日报 → 生成 HTML → 上传 share-html → 发链接到**测试群** |
| `/aihot test-daily YYYY-MM-DD` | 拉指定日期日报，同上 |

**字面匹配**：模糊表述（"测试日报"、"发到测试群"、"调试日报"）**不触发**——避免误触。

## 飞书 bot + 群

- **bot profile**：`ai-digest`（即 AI-Daily-Digest 飞书机器人）。所有 lark-cli 调用必须显式 `--profile ai-digest`，**不要**用默认 profile。
- **测试群 chat_id**：`oc_1ff1b4cc554f9dee3809000d90c9f383`（飞书显示名 "Claude Code App"）

## 工作流（一气呵成，任一步失败即停 + 告知用户、绝不继续）

### Step 1 · 确认日期

- `date "+%Y-%m-%d"` 拿系统当日（**不**信对话注入的 currentDate）
- 用户没指定日期 → 默认今日
- 用户给了 `YYYY-MM-DD` → 用该日期，先校验格式正确

### Step 2 · 拉数据 + role 标签

用 `fetch_daily_with_roles.py` 一步完成：
1. 抓 `/api/public/daily/$DATE` JSON
2. 抓 `/daily` SSR HTML 提取 role 映射（aihot public API/RSS/OpenAPI 都不暴露 role，唯一来源是 SSR markup）
3. 按 sourceName 在 sections 内 join role
4. 重排章节顺序为：模型 → 产品 → 技巧 → 行业 → 论文
5. 简化章节标签（"模型发布/更新" → "模型" 等）
6. 输出合并 JSON 到指定路径

```bash
SKILL_DIR=/Users/guoqu/Documents/ClaudeCodeWorkSpace/agents/honey-bee/.claude/skills/aihot
mkdir -p /tmp/aihot-daily
python3 "$SKILL_DIR/scripts/fetch_daily_with_roles.py" "$DATE" "/tmp/aihot-daily/daily-$DATE.json"
```

输出 JSON 结构：
```json
{
  "date": "YYYY-MM-DD",
  "sections": [
    {
      "label": "模型",
      "items": [
        {
          "title": "...",          // API 原 title
          "source": "...",         // API 原 sourceName（不 remix）
          "source_role": "官方·X",  // 从 /daily SSR 抓的 role-tag
          "summary": "...",        // API 原 summary，一字未改
          "url": "..."             // API 原 sourceUrl
        }
      ]
    }
  ]
}
```

role 取值集：`官方·X` / `X·KOL` / `官方` / `综合资讯` / `学术机构` / `""`（解析失败兜底）

脚本会向 stderr 打印 `wrote {path} — N items, M role matched (K missing)`，正常情况 `K=0`（24/24 命中）。

**错误处理**：
- HTTP 404（日报未生成 / 不存在）→ **告诉用户，停**："$DATE 日报还没生成（北京 8:00 后才出），要不要拉昨天？" **不要静默 fallback** 到昨日
- 其他 HTTP / 网络错误 → **告诉用户，停**
- 大量 role missing（K 远大于 0）→ aihot SSR markup 可能改版，提示用户检查 `scripts/fetch_daily_with_roles.py` 的 `ROLE_PAT` 正则

### Step 3 · LLM remix 标题（先跳过 — MVP）

> **MVP 阶段不做这步**——API 原 title 已经足够可读，先保持流程最简。
>
> 未来加这步时：agent 读 `daily-$DATE.json`，对每条 item 按 share-daily.md 第 3.4 节"标题 remix 风格"改写 title 字段，覆写文件。规则：去营销腔/英译中/过长提炼核心/可加副标题/≤30 字。

### Step 3.5 · 每日重生成 hero banner

按 `$DATE` md5 hash 从 `scripts/hero_prompts.json` 的 20 张清晨感基调池里抽一条，跑 gpt-image 生成 **1792x768（21:9 直出）** → sips 缩到 1280 宽 + jpg quality 88 → 覆盖 `assets/hero.jpg`。同一天复跑命中同一基调（hash 确定），跨天换图。

```bash
python3 "$SKILL_DIR/scripts/gen_hero.py" "$DATE"
```

耗时 ~60-90s（gpt-image API 一张约 30-60s + sips 几秒），成本 ¥0.30/张。

**这一步是 Step 1-6 全流程里唯一一个失败不阻断的例外**——hero 只是装饰，gpt-image 偶发失败 / 网络抖动 / quota 用完时，脚本退出非 0 且**不修改** `assets/hero.jpg`，沿用前一天那张继续 Step 4。具体处理：

```bash
if ! python3 "$SKILL_DIR/scripts/gen_hero.py" "$DATE"; then
  echo "⚠️ hero 重生成失败，沿用昨日 hero.jpg 继续" >&2
fi
```

**基调池**：20 张清晨感 hand-drawn 插画（2026-05-15 curated）—— 薄荷绿 4 张 / 蓝色系 5 张 / 紫色 2 张 / 粉桃 4 张 / 海泡沫 2 张 / 桉绿 1 张 / 杏色 1 张 / 春绿 1 张。新增/删除基调改 `hero_prompts.json` 即可。

### Step 4 · 渲染 HTML

```bash
python3 "$SKILL_DIR/scripts/render_daily_html.py" \
  "/tmp/aihot-daily/daily-$DATE.json" \
  "/tmp/aihot-daily/AI HOT日报-$DATE.html"
```

输出 self-contained HTML，预期 ~180KB（含 base64 内嵌 hero banner）。

**渲染特性**（CSS 已固化在脚本里，视觉迭代 v2 定稿 2026-05-15）：

布局结构：
- 暖米底 `#f0eee6`（Anthropic 招牌色）+ 显式 `<meta name="color-scheme" content="light">` 强制亮色
- container max-width 720px
- 垂直顺序：居中标题(h1) + 居中 meta → 12px → hero → 18px → toolbar → 56px → 章节内容
- 整体「报头区 + 正文区」分明

Hero banner：
- base64 内嵌 `assets/hero.jpg`，**21:9 直出**（gpt-image `--size 1792x768`，CSS `aspect-ratio: 21/9; object-fit: cover` 几乎无裁切），圆角 8px（移动端 6px）
- 主题：每日按 $DATE hash 从 20 张清晨感基调池抽一条（Step 3.5 已经覆盖好 hero.jpg）
- 全部走"清晨明快 + 与暖米底反差"的色调（薄荷/蓝/紫/粉桃/海泡沫…）— 排除深夜墨色 / cream oat / 烟橙姜黄

Toolbar（hero 正下方）：
- 左：`ⓘ 标题可跳转` — info icon + 浅灰提示文字
- 右：`🔗 分享` 按钮 — 链接 icon + 纯文字、无 border、淡灰色，向内收 8px padding
- 点击「分享」复制 `window.location.href` → 文字切「已复制」+ 砖橙色 1.8s → 自动恢复
- 用 `navigator.clipboard.writeText` 主路径 + `document.execCommand('copy')` 兜底（非 secure context）

正文 article 排版：
- long-form 段落式（**无卡片**、无阴影、无圆角边框、无外框）
- 每条 item 用细横线 `--rule-soft` `#e8e6dc` 分隔
- **编号大数字改成右上角水印**：`position: absolute`、56px（移动端 42px）、`rgba(20,20,19,0.045)` 极淡、`font-weight: 800`、`letter-spacing: -0.04em`、`z-index: 0`、`pointer-events: none`
- body `padding-right: 64px`（移动端 48px）让正文文字跟水印数字**在垂直方向上不重叠**

标题与信源：
- 标题点击跳 sourceUrl（默认黑色无下划线，hover 变砖橙）— 不显示「原文 →」
- 信源 = 徽章（`官方·X` 等）+ API 原 sourceName 主体（@handle 完整保留）

Summary 处理：
- API 原文照抄（一字不改）
- summary 内 URL 自动 linkify：虚线下划线、跟正文同色、hover 才变橙
- hashtag 弱化为浅灰小字（0.88em, opacity 0.6）

章节：
- 章节竖条统一砖橙 `#c46849`，不分章节配色（试过 5 章专色太花，已撤回）
- 章节版块标签简化（模型/产品/技巧/行业/论文）
- header meta：`共 N 条 · 模型 X · 产品 Y · 技巧 Z · 行业 W · 论文 V`，不写"数据来源"

其它：
- 没有 lead 段（即使 API 返回 `lead` 也不渲染）
- 没有 hr 横线分隔（试过 hero 下紧贴一条淡横线，效果太碎，撤回）

**错误**：脚本失败 → **告诉用户，停**

### Step 5 · 上传 share-html

走 `/share-html` skill 的核心逻辑（cp 到数据目录加 6 位 hash 防猜 → wrangler 部署 → 拿 URL → 写 share log）：

```bash
SHARE_DIR=~/Documents/ClaudeCodeWorkSpace/data/share-html
HASH=$(openssl rand -hex 3)
SLUG="ai-hot-daily-$DATE-$HASH"
TARGET="$SHARE_DIR/${SLUG}.html"
cp "/tmp/aihot-daily/AI HOT日报-$DATE.html" "$TARGET"

# wrangler 需要 node v22+，nvm 装在 ~/.nvm/versions/node/v22.20.0/
export PATH=~/.nvm/versions/node/v22.20.0/bin:$PATH
cd "$SHARE_DIR" && wrangler pages deploy . \
  --project-name gqshare \
  --commit-dirty=true \
  --branch main

URL="https://gqshare.pages.dev/${SLUG}.html"
TS=$(date "+%Y-%m-%dT%H:%M:%S")
echo "{\"ts\":\"$TS\",\"source\":\"/tmp/aihot-daily/AI HOT日报-$DATE.html\",\"slug\":\"$SLUG\",\"url\":\"$URL\"}" >> ~/Documents/ClaudeCodeWorkSpace/data/cf-meta/share_log.jsonl
```

⚠️ share log **绝不**写进 `$SHARE_DIR` —— wrangler 全量上传该目录，log 会变成公网可读，泄露所有历史分享链接。永远 append 到 `~/Documents/ClaudeCodeWorkSpace/data/cf-meta/share_log.jsonl`（外部）。

**错误**：wrangler 失败 → **告诉用户，停**，留 HTML 在本地

### Step 6 · 发飞书测试群（短文本消息）

只发两行：`📝 AI HOT 日报 MM/DD` + `🔗 URL`。**不要**塞内容摘要——长内容点链接看，群消息保持清爽（≤10 字描述规则，遵循 share-html skill 约定）。

```bash
SHORT_DATE=$(date -j -f "%Y-%m-%d" "$DATE" "+%m/%d" 2>/dev/null || date -d "$DATE" "+%m/%d")
MSG="📝 AI HOT 日报 ${SHORT_DATE}
🔗 ${URL}"
lark-cli --profile ai-digest im +messages-send \
  --chat-id oc_1ff1b4cc554f9dee3809000d90c9f383 \
  --text "$MSG" \
  --as bot
```

**`--profile ai-digest` 必加**——少了会用默认 Claude Code App bot 发，目标群里 AI-Daily-Digest 才是预期发送方。

**错误**：lark-cli 失败 → **告诉用户，留 HTML 在本地** `/tmp/aihot-daily/AI HOT日报-$DATE.html` + URL，让他手动转发

### Step 7 · 回报

成功后给用户：
- "test-daily ✅ 已发测试群"
- `URL`：$URL
- `message_id`：lark-cli 返回值
- `HTML 体积`：KB
- `role 命中`：N/N（fetch 脚本输出）

**不要**把端点路径 / curl 命令 / wrangler 输出 / lark-cli 完整 JSON 泄漏到回复里。

## 常见错误对应

| 现象 | 根因 | 处置 |
|---|---|---|
| fetch 报 HTTP 404 | 日报未生成（北京 8:00 前）/ 日期不存在 | 告知用户，问要不要拉昨日 |
| fetch 报 HTTP 403 | UA 未带 / curl 默认 UA 被 nginx 黑名单挡 | 检查 `fetch_daily_with_roles.py` 里的 `UA` 常量 |
| role matched 远小于 total | aihot 网站 SSR markup 改版 | 检查 `ROLE_PAT` 正则；临时可继续，role 为空时脚本自动 fallback 到 `parse_source()` 三段式徽章（X / RSS / 网页）|
| render 报 hero 文件不存在 | `assets/hero.jpg` 被误删 | 不影响渲染（脚本会跳过 hero block），但页面顶部少一块。重生成见下方"资产清单" |
| wrangler 报 "Project not found" | gqshare 项目被误删 | 重建：`wrangler pages project create gqshare --production-branch main` |
| lark-cli 报 token 错误 | ai-digest profile token 失效 | 告知用户运行 `lark-cli --profile ai-digest auth login` |
| 飞书消息发出但群里没看到 | bot 不在测试群里 | 告知用户把 AI-Daily-Digest 加进测试群 |

## 资产清单

- `scripts/fetch_daily_with_roles.py` — 拉数据 + SSR HTML role 注入 + 章节重排 + 标签简化
- `scripts/render_daily_html.py` — JSON → self-contained HTML（含 inline CSS、base64 hero、徽章/linkify/hashtag）
- `scripts/gen_hero.py` — 按 $DATE hash 从基调池抽一条 → gpt-image 21:9 直出 → sips 压缩 → 覆盖 hero.jpg；失败不阻断（exit ≠ 0 时 hero.jpg 不动）
- `scripts/hero_prompts.json` — 20 张清晨感基调池（curated 2026-05-15）；新增/删除基调改这里
- `assets/hero.jpg` — 顶部 banner，1280 宽 ~100-150KB；由 gen_hero.py 每日覆盖（21:9 jpg quality 88）

**手动测试某一天的 hero**：

```bash
SKILL_DIR=/Users/guoqu/Documents/ClaudeCodeWorkSpace/agents/honey-bee/.claude/skills/aihot
python3 "$SKILL_DIR/scripts/gen_hero.py" 2026-05-15  # 任意日期；同日 hash 命中同一基调
# 看新 hero
open "$SKILL_DIR/assets/hero.jpg"
```

**扩充基调池**：编辑 `scripts/hero_prompts.json` 的 `candidates` 数组，加新 entry（id / palette / subject / body）。`common_head` 和 `common_tail` 通用约束保持不变（极简手绘 + 黑描边 + 21:9 + 无文字）。改完不需要 redeploy，下次跑 gen_hero.py 自动用新池子。

## 不要做

- **不要**在用户没明说 `test-daily` 字符串时触发本流程
- **不要**改写 API summary 文本（"原样照抄"是硬约束）
- **不要**渲染 `lead` 段（即使 API 返回了 `lead` 字段也跳过）
- **不要**主动加章节内"⚠️ 跟前一天重合" / "今日 N 条" / "数据来源" 等装饰性提示
- **不要**自动调度 cron / launchd 跑本流程——用户每次手动 `/aihot test-daily` 才跑
- **不要**用默认 lark-cli profile（必须 `--profile ai-digest`）

## 决策记录（2026-05-15 一次性沉淀）

迭代过程中达成的关键决策，按主题分组：

### 流程架构
- **废弃 PDF**：日报作为一次性消费品，HTML（可点跳转、移动端响应式、share-html 链接看完即焚）比 PDF 附件体验好太多
- **跳过 markdown 中间步**：原 share-daily 流程是 agent 写 markdown → pandoc → typst → PDF。新流程直接 JSON → HTML，agent 关注语义层（fetch + 可选 remix），脚本关注视觉层（CSS / 排版 / linkify / 徽章）
- **role 字段双抓**：aihot public API（OpenAPI / 3 个 RSS feed）全部未暴露 role，唯一来源是 `/daily` SSR HTML 正则提取。多 200ms 一次 GET 换"官方·X / X·KOL / 综合资讯 / 学术机构"精细分类，值得

### 视觉设计
- **风格基调**：参考 Anthropic Claude blog（暖米底 + long-form + 极简插画 hero），不要"信息流卡片"质感
- **暖米底 `#f0eee6`**：Anthropic 招牌色，比纯白柔和，比 follow-builders 的 `#fdfcf9` 更暖
- **去掉 dark mode 适配**：用户系统主题千差万别，统一亮色最可控，加 `color-scheme: light` 显式声明
- **去掉卡片**：每条 item 用细横线 + 大留白分隔，不要圆角/阴影/边框，更接近 blog long-form
- **章节统一砖橙竖条**：试过 5 章专色（模型焦糖 / 产品砖橙 / 技巧橄榄绿 / 行业灰蓝 / 论文灰紫）但太花，撤回到统一砖橙 `#c46849`
- **编号淡灰大数字**：28px tabular-nums，淡灰 `#b0aea5`，不抢戏

### 信息密度细节
- **标题改为链接**：去掉 `<p class="link">原文 →</p>`，h3 标题本身点击跳 sourceUrl
- **summary 内 URL 自动 linkify**：API summary 偶尔嵌 raw URL，渲染时识别并包 `<a>` —— 但弱化为虚线下划线 + 跟正文同色 + hover 才变橙（避免抢戏）
- **hashtag 弱化**：`#xxx` 标签浅灰小字（0.88em，opacity 0.6）—— 存在但不重要
- **不 remix sourceName**：API 原 sourceName 完整保留（含 @handle 等信息），徽章信息从 SSR HTML 抓的 role 来，跟 sourceName 互补不重叠
- **summary 一字不改**：API 原文照抄，包括 emoji / 引用 / 跨语言等都保留

### Hero banner
- **每日 hash 抽签换图**（2026-05-15 改造）：废弃固定 banner，每天按 $DATE md5 mod 20 从基调池抽一张，gpt-image 实时生成。同一天复跑命中同一张，跨天换图。¥0.30/天 × 30 天 ≈ ¥9/月可接受
- **直出 21:9**：gpt-image-2 支持任意 size，`--size 1792x768` 直出，CSS aspect-ratio 21/9 几乎无裁切。比原"16:9 → CSS 裁 21:9"少丢 1/4 像素 + 构图原生适配
- **基调池 20 张**（curated 2026-05-15）：30 张清晨感候选中郭大大选 20，全部"清晨明快 + 跟暖米底反差"——薄荷绿 4 / 蓝色系 5 / 紫 2 / 粉桃 4 / 海泡沫 2 / 桉绿 1 / 杏色 1 / 春绿 1。排除：深夜墨色 / cream oat（跟正文撞色）/ 烟橙姜黄（跟章节竖条撞色）
- **失败不阻断**：这是 Step 1-6 里唯一一个失败不停的步骤——hero 装饰性，gpt-image 偶发挂掉 / quota 用完时沿用前一天的 hero.jpg
- **生成参数（gen_hero.py 写死）**：gpt-image --size 1792x768 --quality high → sips 缩 1280 + jpg quality 88 → ~100-150KB；base64 后 ~140-200KB，HTML 总体积 ~180-260KB

### 视觉迭代 v2（2026-05-15 后续 — toolbar、水印编号、紧凑报头）
- **header 居中 + 紧凑**：h1 + meta 改 `text-align: center`，header → hero 间距从 32-40px 压到 12px（试过空旷感太强，撤回紧凑）；整体更像"报头"而不是"页眉 + 大留白"
- **hero 改 21:9**：3:2 高度太占，21:9 让 banner 退到背景位、把视觉焦点交给标题；圆角从 16 → 8
- **hero 换 sage green**：原 #c46849 砖橙底跟章节竖条同色撞了，且整体橙调过重；换 sage green 后跟暖米底互补、跟橙竖条对比不撞色
- **toolbar 区**（hero 正下方）：左 `ⓘ 标题可跳转` info icon + 提示文字（替代「点击标题跳转原文」更简洁）、右 `🔗 分享` 按钮
- **分享按钮纯文字**：试过 pill + border 太重撤回；最终 = svg icon + 「分享」文字、无 border、`var(--ink-faint)` 淡灰、hover 变砖橙
- **分享行为**：点击复制 `window.location.href`（部署后 = gqshare.pages.dev 公开 URL），文字切「已复制」+ 砖橙色 1.8s 后自动恢复；`navigator.clipboard.writeText` 主路径 + `document.execCommand('copy')` 兜底（覆盖非 secure context）
- **toolbar 内缩 8px**：share-btn 不贴 container 最右边，左右各 8px padding
- **去掉 hr 横线**：试过 hero 下紧贴一条淡横线分隔 toolbar、试过 toolbar 下分隔 chapter，效果都太碎，全删
- **编号变水印**：原左列 28px 灰数字 grid 布局改成右上角 absolute 水印：56px / `rgba(20,20,19,0.045)` 极淡 / `font-weight: 800` / `letter-spacing: -0.04em`（移动端 42px）。"一开头就是值得读的文字内容"
- **body padding-right: 64px**（移动端 48px）：避免正文 wrap 后伸到右边跟水印数字在垂直方向上叠加
- **toolbar → 章节间距 56px**：明显划开"报头区"和"正文区"，从 toolbar 进入第一章节有呼吸感
- **HTML 结构**：article 内 body 在前、num（数字水印）在后（语义上正文优先），num 加 `aria-hidden="true"`
