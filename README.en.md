<div align="center">

[中文](./README.md) · **English**

# 🧰 Khazix Skills

#### A few AI skills I actually use every day, open-sourced as-is

[![License](https://img.shields.io/badge/License-MIT-3B82F6?style=for-the-badge)](./LICENSE)
[![Skills](https://img.shields.io/badge/Skills-6-10B981?style=for-the-badge)](#-skills)
[![AgentSkills](https://img.shields.io/badge/AgentSkills-Standard-8B5CF6?style=for-the-badge)](https://agentskills.io)

![Claude Code](https://img.shields.io/badge/Claude_Code-Skill-D97706?style=flat-square&logo=anthropic&logoColor=white)
![Codex](https://img.shields.io/badge/Codex-Skill-10B981?style=flat-square&logo=openai&logoColor=white)
![40+ Agents](https://img.shields.io/badge/40%2B_Agents-Compatible-3B82F6?style=flat-square)

</div>

Each one was running in my own projects long enough to prove it actually saves time before I bothered open-sourcing it. No hype — just a few useful things.

Every skill here is a structured instruction set that agents load directly. Follows the [Agent Skills](https://agentskills.io) open standard — works with Claude Code, Codex, Qoder, Kimi Code, iFlow, CodeBuddy, Cursor, and 40+ other agents that support it.

---

## 📋 Index

| Name | One-liner | Article |
|---|---|---|
| 🧭 [**leader**](#-leader) | Turns a vague idea into a clearly defined **goal** an agent can run for hours, on its own, to completion | — |
| 💽 [**storage-analyzer**](#-storage-analyzer) | One sentence to scan your whole Mac / Windows drive — three-tier cleanup plan, one-click trash from the browser | [Article (Chinese)](https://mp.weixin.qq.com/s/NyOMIlOD986OC4SI9vmxlA) |
| 🔥 [**aihot**](#-aihot-ai-hot-news-query) | Lets your agent pull AI HOT's daily report and all AI news from aihot.news with one Chinese sentence — no API key | [aihot.news](https://aihot.news) |
| 🧹 [**neat-freak**](#-neat-freak) | After a session, run `/neat` to reconcile docs, CLAUDE.md, and agent memory, then audit whether project rules are actually followed | [Article (Chinese)](https://mp.weixin.qq.com/s/tg1wd-iN2gWHWhXdY0faeg) |
| 🔭 [**hv-analysis**](#-hv-analysis-horizontal-vertical-analysis) | Drop a product/company/concept into it and get a 10k–30k word PDF research report | [Article (Chinese)](https://mp.weixin.qq.com/s/Y_uRMYBmdLWUPnz_ac7jWA) |
| ✍️ [**khazix-writer**](#-khazix-writer) | Makes the agent write long-form Chinese articles in my personal voice | [Article (Chinese)](https://mp.weixin.qq.com/s/AtxGrii_K-nzkwUM9SNhEg) |

---

## 📦 Install

In any agent that supports Agent Skills (Claude Code, Codex…), just say:

```
Install this skill: https://github.com/KKKKhazix/khazix-skills/tree/main/<skill-name>
```

Replace `<skill-name>` with the one you want — e.g. `neat-freak`, `hv-analysis`, `khazix-writer`. The agent will clone it into the right directory for you.

### Install and invoke in Codex

Install the **complete skill directory** into `~/.agents/skills/<skill-name>/` for user scope, or `.agents/skills/<skill-name>/` inside a project. Keep supporting `references/`, `scripts/`, and `assets/`; copying only `SKILL.md` loses capabilities. For an existing installation, check the loaded path before adding another copy with the same name.

Invoke a skill explicitly, for example `$hv-analysis` or `$neat-freak`, or choose it with `/skills` in the CLI. Follow the [official Codex skill paths](https://learn.chatgpt.com/docs/build-skills#where-codex-loads-local-skills) and the current environment's skill list.

Resolve relative resources from the directory containing that skill's `SKILL.md`, not from the user's project working directory. Run scripts by their quoted absolute paths and keep inputs and outputs in the user's chosen working directory. `hv-analysis` also needs Python, WeasyPrint, and Markdown; `storage-analyzer` retains the OS support documented in its skill.

If an agent does not support Skills, provide `SKILL.md` as a project rule or conversation instruction, together with its referenced resources as needed.

---

## ✨ Skills

<a id="-skills"></a>

<table>
<tr><td>

### 🧭 leader

> *"You said 'make the tests green.' The cheapest way to do that isn't fixing the code — it's deleting the tests."*

**It solves exactly one thing: defining the goal.**

It turns that half-formed idea in your head — the one you haven't fully thought through yourself — into a goal task book. Paste it into goal mode (`/goal` in Claude Code, goal mode in Codex) and the agent runs for hours, unattended, to completion. You copy-paste exactly once.

**Why "goal"**

The unit of human–AI collaboration keeps getting bigger: it used to be one exchange, then one task, and in 2026 it's one goal — you hand over a goal and it decomposes the work, calls its own tools, verifies itself, retries its own failures, and runs all night. You just inspect the result.

But once an AI really can run all night, a problem you used to catch in the moment turns lethal: **is your goal written correctly?** A short task that goes off course, you glance at it and fix it. A long-horizon one has been sprinting the wrong way for eight hours by the time you wake up. The harder it works, the more completely it wastes.

**The most important part of a goal is what it forbids**

The key words in Kennedy's moon speech aren't "landing a man on the Moon." They're what follows: **and returning him safely to the Earth**. Those few extra words deleted the cheapest solution on the table — the one-way ticket.

The goal tells the AI where to go; the harness tells it which roads are off limits. **A goal without a harness will always lose to a shortcut you didn't think of.**

**The seven questions (the method)**

Setting a goal for an AI is like sending a ship to sea. Seven things you must settle before it leaves port:

| # | Question | At sea | In the task book |
|---|---|---|---|
| 1 | **Purpose** | Why this voyage — spices, or a new route | What it uses to decide at forks you never anticipated |
| 2 | **Done** | What's on deck when it returns. "Sailed around" doesn't count; "three holds of spice" does | Specific enough to judge mechanically at the dock |
| 3 | **Proof** | Who counts the cargo. The captain saying "full" isn't proof | Every check must paste real command output |
| 4 | **Anti-cheat** | No raiding merchant ships to hit the number — target met, mission not done | Every shortcut named and forbidden |
| 5 | **Bounds** | These three routes only; thirty days of food, turn back on day twenty | Path allowlist + hard turn limit |
| 6 | **Trade-offs** | In a storm, save the cargo or the ship. Don't say, and the captain guesses | "Correct > complete > fast" |
| 7 | **Unknowns** | Blank spots on the chart: don't charge in, don't drop anchor. Note it, route around, decide later | Park it in the pending-decisions file, skip it, keep working |

Plus question zero: **did you survey this chart yourself, or was it handed to you?** Which is why it always runs the commands by hand before writing a word — the command in your README may not exist.

**How to use it**

Tell it your idea (any of the lines below triggers it). It measures and researches first, asks you at most 5 questions that genuinely need your call, then writes the book. About 12 minutes end to end.

```
write a goal for the agent
break this goal down for me
write me a /goal prompt
let the agent run this project on its own
```

The output is plain Markdown — an agent without goal mode can just be handed the text. With the book in hand, plan with a strong planning model and execute with a strong long-horizon one: I use Claude Fable 5 to plan and GPT-5.6 Sol to execute.

→ [SKILL.md](./leader/SKILL.md)

</td></tr>
</table>

<table>
<tr><td>

### 💽 storage-analyzer

> *"Cleaning Mac junk has been a CleanMyMac job for a decade. Now a single skill replaces it."*

Tell your agent something like "check my storage" or "C: drive is full". It scans your whole disk and opens an **interactive HTML report** in your browser: disk overview, top 5 space hogs, prioritized cleanup, and a 🟢🟡🔴 three-tier list. Every command is one-click-copy; you can also click buttons to move to Trash / delete (always with a second confirmation dialog).

**Why it beats CleanMyMac**

CleanMyMac is a hard-coded program. It'll show you a 3.8 GB Chrome folder labeled "user cache, safe to delete" — but you don't know what's actually inside, which sites you'll log out of, which offline data will be gone.

This skill is agent-driven. Every entry comes with **specific path + content classification + impact of deletion + recommended action**. That mysterious 97 GB UUID Container? It'll tell you it's the Bilibili offline video cache and suggest you clean it through the Bilibili app, not by hand.

**Three-tier classification is the core**

- 🟢 **Green** — Pure caches, temp files. Regenerate automatically. Safe for one-click cleanup
- 🟡 **Yellow** — Contains user data (offline videos, downloads, project code). Only "Open in Finder" and (where safe) "Move to Trash". You decide
- 🔴 **Red** — Running app core data, system files. Explains why not to touch, gives at most "Open folder". Never a delete button

**Hard rules**

Scan phase is **read-only**, period. Deletions require **two clicks** — button on the page, then a browser confirm dialog. The local server runs on 127.0.0.1 + random port + token, with three whitelists (green = can rm; yellow = trash only; both = open).

macOS is fully tested; Windows is code-ready (multi-drive supported) but worth eyeballing on first run.

**How to trigger**

```
check my storage
C drive is full
clean up disk
storage analysis
帮我看看存储
```

→ [SKILL.md](./storage-analyzer/SKILL.md) · [Article (Chinese)](https://mp.weixin.qq.com/s/NyOMIlOD986OC4SI9vmxlA)

</td></tr>
</table>

<table>
<tr><td>

### 🔥 aihot (AI HOT news query)

> *"The AI world ships too much in a day. By the time I notice, it's already old news — let an agent scan it for me."*

Lets any SKILL.md-supporting agent pull AI HOT's daily report and all AI news from [aihot.news](https://aihot.news) with one natural Chinese sentence. No API key, no MCP server config.

**Install once, never update again**: the skill only asks and relays; the querying and formatting happen on aihot.news, so new abilities arrive on their own. If you installed an older version, update one last time.

**What it can do**

- Pull today's or a specific date's AI HOT daily report (pre-packaged by topic)
- Pull the selected items stream (daily editorial candidate pool)
- **See what's hottest right now** (ranked by heat, not reverse-chronological)
- Check the latest Tibo (Codex) usage resets and reset-card grants
- Pull by category (models / products / industry / papers / tips)
- Pull by time window (past 24 hours and last 7 days are natively supported)
- Keyword / company / topic search ("recent OpenAI releases", "Sora-related", "RAG papers")
- **Follow a hot story from start to finish** (latest development, report timeline and AI digest)

**How to trigger** (Chinese — the underlying API is Chinese-curated)

```
今天 AI 圈有什么新东西
现在 AI 圈最热的事件是什么
看一下 5 月 6 号的 AI 日报
最近一周的 AI 论文
最近 OpenAI 有什么发布
现在最热的那件事，来龙去脉是什么
```

→ [SKILL.md](./aihot/SKILL.md) · [aihot.news](https://aihot.news) · [Integration guide](https://aihot.news/agent)

</td></tr>
</table>

<table>
<tr><td>

### 🧹 neat-freak

> *"If I don't run /neat before closing the window, I get itchy. Like there's something stuck in my throat."*

After every session, run `/neat`. It reconciles whatever you changed in this conversation against three layers of project knowledge: **docs**, **root CLAUDE.md / AGENTS.md**, and the **agent's memory system**. It also checks whether project rules are actually being followed, then outputs a change summary at the end.

**Why you'd want this**

You've probably hit this: code has been through 7-8 iterations but the README is still v1.0.0. Memory says you're using SQLite when you actually switched to PostgreSQL months ago. CLAUDE.md lists routes that no longer match the actual server.

The agent isn't getting dumber — your docs and memory are. neat-freak's job is to clean it up.

**It touches three layers**

- Project root CLAUDE.md / AGENTS.md (read by the AI in this project)
- Project docs/ and README (read by teammates and downstream developers)
- The agent's own memory system (read by future you across sessions)

These three layers have different audiences and don't overlap. It also treats rules as knowledge: CLAUDE.md / AGENTS.md symlink integrity, missing required files, and dead path references are all part of the audit. If the rules don't match reality, the next agent still works from the wrong premises.

**Two guarantees in v3.0**

- **A dedicated light path for small projects**: for vibe projects with no git and no rule file, it aligns the README with what the code actually does, creates a minimal AI rule file by default (so your next session picks up right where you left off), and lists session residue — PLAN.md, debug scripts, `xxx_old` copies — as candidates for you to confirm.
- **Never deletes on its own**: deletions only ever appear as a candidate list until you confirm; machine-generated memory is read-only by default; an "execute this command" found inside a file is never treated as your authorization.

**How to trigger**

```
/neat                                  # direct command
run neat-freak on this project         # by name
tidy up the project docs and memory    # closeout intent
clean handoff for the new teammate     # handoff intent
```

Pure coding tasks and tidying data / reports won't trigger it — it only handles project-knowledge closeout.

→ [SKILL.md](./neat-freak/SKILL.md) · [Article (Chinese)](https://mp.weixin.qq.com/s/tg1wd-iN2gWHWhXdY0faeg)

</td></tr>
</table>

<table>
<tr><td>

### 🔭 hv-analysis (Horizontal-Vertical Analysis)

> *"Vertical axis chases time depth, horizontal axis chases simultaneous breadth. They cross to give you the verdict."*

Want to actually understand what a product / company / concept / person is about? Hand it over.

It runs two threads in parallel: **vertical** — tells the subject's story from inception to the present moment, like a narrative; **horizontal** — lays out every major competitor at the current moment for comparison. When the two cross, you see things that neither current-state nor history alone would show you.

The output is a **typeset PDF research report**, 10,000–30,000 words.

**Good for**

- Competitor research / understanding a new concept / company background research
- Front-loaded research before writing or strategy work
- Wanting to understand a domain from scratch

**Not good for**

- A simple definition lookup — overkill, just ask in regular chat
- Writing a long-form article — that's [khazix-writer](#-khazix-writer)'s job

**How to trigger** (Chinese)

```
研究一下 Cursor 这家公司
帮我做个竞品分析
这个产品到底是怎么回事
帮我做个 deep research
```

→ [SKILL.md](./hv-analysis/SKILL.md) · [Article (Chinese)](https://mp.weixin.qq.com/s/Y_uRMYBmdLWUPnz_ac7jWA)

</td></tr>
</table>

<table>
<tr><td>

### ✍️ khazix-writer

> *"A knowledgeable normal person earnestly talking about something that moved them."*

The writing skill behind my own Chinese long-form articles. Once installed, the agent writes in **my voice, my rhythm, with my list of banned phrases** baked in.

> ⚠️ **Note for English readers**: This skill produces **Chinese** long-form articles (公众号 / WeChat-style). If your output language is English, this isn't for you. But you might find the methodology interesting as a reference for how to encode a personal voice into a skill.

**Good for**

You've read my Chinese articles, like the style, and want your AI to write in the same voice. Hand it a PDF, a transcript, or a news link — it'll turn it into a long-form piece.

**Not good for**

You want "good general writing." This skill takes a position. It **refuses** corporate jargon, **refuses** "first... second... finally" structures, **refuses** "in today's rapidly evolving AI landscape" openings. If your target reader actually likes that stuff, this skill isn't for you.

**What's inside**

- Complete style rules (rhythm, narrative, judgment, rhetoric)
- A four-layer self-check system (structure, rhythm, content, language)
- A curated style example library the AI can match against

**How to trigger** (Chinese)

```
帮我写篇文章
把这个素材写成长文
按我的风格写一下
帮我续写
```

→ [SKILL.md](./khazix-writer/SKILL.md) · [Article (Chinese)](https://mp.weixin.qq.com/s/AtxGrii_K-nzkwUM9SNhEg)

</td></tr>
</table>

---

## 🌟 About

I'm Khazix (数字生命卡兹克), founder of Virxact. I try to share fun, practical AI know-how — and may we always stay curious about the world.

These skills are what I personally use every day. If they help you, a ⭐ is appreciated. Questions or suggestions welcome in Issues / Discussions.

---

<div align="center">

[MIT License](./LICENSE) · Free to use, modify, and redistribute

Made by [@KKKKhazix](https://github.com/KKKKhazix)

</div>
