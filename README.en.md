<div align="center">

[中文](./README.md) · **English**

# 🧰 Khazix Skills

#### A few AI skills I actually use every day, open-sourced as-is

[![License](https://img.shields.io/badge/License-MIT-3B82F6?style=for-the-badge)](./LICENSE)
[![Skills](https://img.shields.io/badge/Skills-7-10B981?style=for-the-badge)](#-skills)
[![AgentSkills](https://img.shields.io/badge/AgentSkills-Standard-8B5CF6?style=for-the-badge)](https://agentskills.io)

![Claude Code](https://img.shields.io/badge/Claude_Code-Skill-D97706?style=flat-square&logo=anthropic&logoColor=white)
![Codex](https://img.shields.io/badge/Codex-Skill-10B981?style=flat-square&logo=openai&logoColor=white)
![OpenCode](https://img.shields.io/badge/OpenCode-Skill-3B82F6?style=flat-square)
![OpenClaw](https://img.shields.io/badge/OpenClaw-Skill-8B5CF6?style=flat-square)

</div>

Each one was running in my own projects long enough to prove it actually saves time before I bothered open-sourcing it. No hype — just a few useful things.

Every skill here is a structured instruction set that agents load directly. Follows the [Agent Skills](https://agentskills.io) open standard. Works with Claude Code, Codex, OpenCode, and OpenClaw.

---

## 📋 Index

| Name | One-liner | Article |
|---|---|---|
| 💽 [**storage-analyzer**](#-storage-analyzer) | One sentence to scan your whole Mac / Windows drive — three-tier cleanup plan, one-click trash from the browser | [Article (Chinese)](https://mp.weixin.qq.com/s/NyOMIlOD986OC4SI9vmxlA) |
| 🔥 [**aihot**](#-aihot-ai-hot-news-query) | Lets your agent pull AI HOT's daily report and all AI news from aihot.virxact.com with one Chinese sentence — no API key | [aihot.virxact.com](https://aihot.virxact.com) |
| 🧹 [**neat-freak**](#-neat-freak) | After a session, run `/neat` to reconcile your project docs, CLAUDE.md, and agent memory with the code | [Article (Chinese)](https://mp.weixin.qq.com/s/tg1wd-iN2gWHWhXdY0faeg) |
| 🔭 [**hv-analysis**](#-hv-analysis-horizontal-vertical-analysis) | Drop a product/company/concept into it and get a 10k–30k word PDF research report | [Article (Chinese)](https://mp.weixin.qq.com/s/Y_uRMYBmdLWUPnz_ac7jWA) |
| 🧠 [**research-analysis**](#-research-analysis) | Turns news, WeChat articles, papers, open-source projects, or controversial claims into a sourced Markdown research report | [SKILL.md](./research-analysis/SKILL.md) |
| ✍️ [**khazix-writer**](#-khazix-writer) | Makes the agent write long-form Chinese articles in my personal voice | [Article (Chinese)](https://mp.weixin.qq.com/s/AtxGrii_K-nzkwUM9SNhEg) |

---

## 📦 Install

In any agent that supports Skills (Claude Code, Codex, OpenClaw…), just say:

```
Install this skill: https://github.com/KKKKhazix/khazix-skills/tree/main/<skill-name>
```

Replace `<skill-name>` with the one you want — e.g. `neat-freak`, `hv-analysis`, `khazix-writer`. The agent will clone it into the right directory for you.

---

## ✨ Skills

<a id="-skills"></a>

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

**🌐 Cross-platform**: macOS fully tested; Windows code-ready (multi-drive supported), worth eyeballing on first run

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

Lets any SKILL.md-supporting agent pull AI HOT's daily report and all AI news from [aihot.virxact.com](https://aihot.virxact.com) with one natural Chinese sentence. No API key, no MCP server config.

**What it can do**

- Pull today's or a specific date's AI HOT daily report (pre-packaged by topic)
- Pull the selected items stream (daily editorial candidate pool)
- Pull by category (models / products / industry / papers / tips)
- Pull by time window (last N days)
- Keyword / company / topic search ("recent OpenAI releases", "Sora-related", "RAG papers")

**How to trigger** (Chinese — the underlying API is Chinese-curated)

```
今天 AI 圈有什么新东西
看一下 5 月 6 号的 AI 日报
最近一周的 AI 论文
看下精选条目
最近 OpenAI 有什么发布
```

**🌐 Cross-platform**: Claude Code · Codex CLI · Cursor · Gemini CLI · OpenCode · Cline · Windsurf

**🇨🇳 China-friendly direct install** (no GitHub access needed):

```
curl -fsSL https://aihot.virxact.com/aihot-skill/install.sh | bash
```

→ [SKILL.md](./aihot/SKILL.md) · [aihot.virxact.com](https://aihot.virxact.com) · [Integration guide](https://aihot.virxact.com/agent)

</td></tr>
</table>

<table>
<tr><td>

### 🧹 neat-freak

> *"If I don't run /neat before closing the window, I get itchy. Like there's something stuck in my throat."*

After every session, run `/neat`. It reconciles whatever you changed in this conversation against three layers of project knowledge: **docs**, **root CLAUDE.md / AGENTS.md**, and the **agent's memory system**. Outputs a change summary at the end.

**Why you'd want this**

You've probably hit this: code has been through 7-8 iterations but the README is still v1.0.0. Memory says you're using SQLite when you actually switched to PostgreSQL months ago. CLAUDE.md lists routes that no longer match the actual server.

The agent isn't getting dumber — your docs and memory are. neat-freak's job is to clean it up.

**It touches three layers**

- Project root CLAUDE.md / AGENTS.md (read by the AI in this project)
- Project docs/ and README (read by teammates and downstream developers)
- The agent's own memory system (read by future you across sessions)

These three layers have different audiences and don't overlap. That's exactly why I wasn't satisfied with Claude Code's AutoDream — it only touched memory, leaving the docs to rot.

**How to trigger**

```
/neat            # direct command
sync up          # natural language
tidy up docs     # natural language
整理一下          # 中文
```

**🌐 Cross-platform**: Claude Code · Codex · OpenCode · OpenClaw

[![ClawHub](https://img.shields.io/badge/ClawHub-v1.0.1-EC4899?style=flat-square)](https://clawhub.ai)
[![Tessl](https://img.shields.io/badge/Tessl-0.1.1-3B82F6?style=flat-square)](https://tessl.io/registry/khazix-skills/neat-freak)

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

[![ClawHub](https://img.shields.io/badge/ClawHub-v1.0.0-EC4899?style=flat-square)](https://clawhub.ai)
[![Tessl](https://img.shields.io/badge/Tessl-published-3B82F6?style=flat-square)](https://tessl.io/registry/khazix-skills/hv-analysis)

→ [SKILL.md](./hv-analysis/SKILL.md) · [Article (Chinese)](https://mp.weixin.qq.com/s/Y_uRMYBmdLWUPnz_ac7jWA)

</td></tr>
</table>

<table>
<tr><td>

### 🧠 research-analysis

> *"Don't just summarize the article. Trace the facts, sources, contradictions, and blind spots behind it."*

This is the everyday "research this" skill. Give it a news item, a WeChat article, a paper, an open-source project, a company name, or a controversial claim. It first turns the input into claims to verify, then traces primary sources and produces a Markdown research report.

How it differs from `hv-analysis`: `hv-analysis` is for big horizontal/vertical PDF reports on products, companies, concepts, or people. `research-analysis` is the daily research desk for content work: faster, source-first, Markdown-native, and designed for articles, events, methods, repositories, and claims.

**What it does**

- Reads WeChat links through 得到大脑 / Get 笔记 when available, instead of stopping at WeChat verification pages
- Fact-checks viral claims: what is true, what needs cooling down, what can be strengthened
- Traces papers, official projects, GitHub repos, company announcements, regulatory files, and primary sources
- Uses STORM-style prewriting: perspective discovery, perspective-specific questions, contradiction maps
- Applies horizontal/vertical analysis: timeline, comparable cases, stakeholders, future scenarios
- Outputs a Markdown report with key conclusions, fact-checking, contrarian insight, writing material, and sources

**How to trigger**

```
研究一下这个新闻：……
深度研究一下这篇文章：……
调研一下这个开源项目：……
看看这个微信文章背后的研究源头：……
```

**Not for**

- Simple definition lookups
- One-line factual answers
- Writing final Chinese long-form articles; use `khazix-writer` for that

→ [SKILL.md](./research-analysis/SKILL.md) · [Codex install guide](./research-analysis/INSTALL_FOR_CODEX.md)

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

[![ClawHub](https://img.shields.io/badge/ClawHub-v1.0.0-EC4899?style=flat-square)](https://clawhub.ai)
[![Tessl](https://img.shields.io/badge/Tessl-0.1.1-3B82F6?style=flat-square)](https://tessl.io/registry/khazix-skills/khazix-writer)

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
