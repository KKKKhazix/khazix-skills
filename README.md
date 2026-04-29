# 公众号写作模板

这份模板给我自己平时写公众号时直接用。
主要配合两个 skill：

- `hv-analysis`：负责深度研究、竞品分析、历史脉络、行业判断
- `khazix-writer`：负责把素材写成公众号长文

## 1. 工具评测稿

帮我用 `khazix-writer` 写一篇公众号文章。

主题是：`[工具名]` 到底值不值得用。

我的素材：
1. 我为什么开始用它
2. 我实际用了哪些功能
3. 最惊艳我的地方
4. 最让我失望的地方
5. 它和 `[竞品1]` / `[竞品2]` 的区别
6. 我觉得它适合什么人，不适合什么人

要求：
- 写成长文，不要写成参数表
- 要像真人在讲自己的真实体验
- 要有明确判断，不要模棱两可
- 保留优点，也要直接写缺点
- 适合发公众号

## 2. 深度分析稿

帮我先用 `hv-analysis` 深度研究 `[研究对象]`，然后把结论整理成适合公众号写作的素材。

我重点想看：
1. 它是怎么发展起来的
2. 它现在的竞争对手是谁
3. 它最核心的优势和短板
4. 它今天的位置是怎么形成的
5. 未来最值得关注的变化是什么

输出要求：
- 先给我研究结论
- 再列出最值得写成文章的 5 个角度
- 再给我一个适合公众号长文的文章框架

## 3. 行业观察稿

帮我用 `khazix-writer` 写一篇公众号行业观察文章。

主题：`[行业现象/趋势]`

我想表达的核心判断：
`[你的核心观点]`

我已有素材：
1. 最近发生的事件
2. 我的个人观察
3. 几个行业案例
4. 我认同和不认同的观点
5. 我觉得读者真正该关心的点

要求：
- 不要写成新闻整理
- 要有个人判断和立场
- 要有故事感和节奏感
- 不要太像 AI 写的
- 最后要落到一个更大的判断上

## 4. 方法论稿

帮我用 `khazix-writer` 写一篇方法论文章。

主题：`[方法/经验/心得]`

我准备写的内容：
1. 我为什么会形成这套方法
2. 我踩过哪些坑
3. 这套方法具体怎么做
4. 它适合谁，不适合谁
5. 常见误区是什么
6. 我现在怎么看它的局限性

要求：
- 每一节都要让读者看完能立刻行动
- 不要只讲大道理
- 要坦诚写学习成本和失败点
- 开头要谦逊一点，不要像在教训人
- 结尾要有一点信念感，但别空

## 5. 体验故事稿

帮我用 `khazix-writer` 把这段经历写成公众号文章。

经历主题：`[你经历了什么]`

原始素材：
`[把你的经历、笔记、聊天记录、碎片感受贴在这里]`

要求：
- 重点保留真实细节
- 要像“我真的经历过这件事”
- 可以有情绪，但不要狗血
- 要让读者觉得这不是编出来的
- 从具体故事切入，再慢慢拉到更大的思考

## 6. 续写 / 改写稿

帮我用 `khazix-writer` 续写 / 改写这篇文章。

原文：
`[贴文章或草稿]`

我的要求：
1. 保留原文核心观点
2. 加强节奏感和活人感
3. 补足不够具体的地方
4. 删掉太像 AI 的表达
5. 如果有必要，重写开头和结尾

额外要求：
- 不要改得像另一个人写的
- 要保留我的判断
- 重点是让它更适合公众号发表

## 7. 推荐工作流

### 情况 A：我已经有很多素材
直接用 `khazix-writer` 出稿。

### 情况 B：我只有题目，还没研究透
先用 `hv-analysis` 做研究，再把结果喂给 `khazix-writer`。

### 情况 C：我要写深度长文
推荐顺序：
1. `hv-analysis` 研究对象
2. 提炼最值得写的判断
3. 加入我自己的体验和观点
4. `khazix-writer` 出稿
5. 我自己再人工改一轮

一句话理解：
- `hv-analysis` 负责“搞明白”
- `khazix-writer` 负责“写成稿”

# Khazix Skills
<div align="center">

**中文** · [English](./README.en.md)

# 🧰 Khazix Skills

#### 我自己每天在用的一些 AI 技能和 Prompt，都开源在这里

[![License](https://img.shields.io/badge/License-MIT-3B82F6?style=for-the-badge)](./LICENSE)
[![Skills](https://img.shields.io/badge/Skills-3-10B981?style=for-the-badge)](#-skills)
[![Prompts](https://img.shields.io/badge/Prompts-1-F59E0B?style=for-the-badge)](#-prompts)
[![AgentSkills](https://img.shields.io/badge/AgentSkills-Standard-8B5CF6?style=for-the-badge)](https://agentskills.io)

![Claude Code](https://img.shields.io/badge/Claude_Code-Skill-D97706?style=flat-square&logo=anthropic&logoColor=white)
![Codex](https://img.shields.io/badge/Codex-Skill-10B981?style=flat-square&logo=openai&logoColor=white)
![OpenCode](https://img.shields.io/badge/OpenCode-Skill-3B82F6?style=flat-square)
![OpenClaw](https://img.shields.io/badge/OpenClaw-Skill-8B5CF6?style=flat-square)

</div>

都是在自己项目里跑通了一段时间，确实省事，才搬出来开源的。没什么花活，就是几个挺实用的东西。

- **Skills** — Agent 能直接加载的结构化指令集，遵循 [Agent Skills](https://agentskills.io) 开放标准。Claude Code、Codex、OpenCode、OpenClaw 都能装
- **Prompts** — 一段提示词，复制粘贴到 ChatGPT / Claude / Gemini 任何对话里就能用，不需要安装

---

## 📋 目录

### Skills

| 名字 | 一句话 | 讲解 |
|---|---|---|
| 🧹 [**neat-freak（洁癖）**](#-neat-freak洁癖) | 干完活跑一下 `/neat`，自动把你这次改的东西跟项目文档、CLAUDE.md、Agent 记忆全部对齐 | [公众号文章](https://mp.weixin.qq.com/s/tg1wd-iN2gWHWhXdY0faeg) |
| 🔭 [**hv-analysis（横纵分析法）**](#-hv-analysis横纵分析法) | 想搞懂一个产品/公司/概念是怎么回事，丢给它，给你一份万字 PDF 研究报告 | [公众号文章](https://mp.weixin.qq.com/s/Y_uRMYBmdLWUPnz_ac7jWA) |
| ✍️ [**khazix-writer（卡兹克写作）**](#-khazix-writer卡兹克写作) | 装上之后，Agent 用我的口吻和节奏写公众号长文 | [公众号文章](https://mp.weixin.qq.com/s/AtxGrii_K-nzkwUM9SNhEg) |

### Prompts

| 名字 | 一句话 | 讲解 |
|---|---|---|
| 🔭 [**横纵分析法（Prompt 版）**](#-横纵分析法prompt-版) | 上面那个 Skill 的轻量版，复制粘贴到任何 Deep Research 模型里就能跑 | [公众号文章](https://mp.weixin.qq.com/s/Y_uRMYBmdLWUPnz_ac7jWA) |

---

## 📦 安装方式

在 Claude Code、Codex、OpenClaw 等支持 Skill 的 Agent 里，直接说：

```
帮我安装这个 skill：https://github.com/KKKKhazix/khazix-skills/tree/main/<skill-name>
```

把 `<skill-name>` 换成你想装的那个，比如 `neat-freak`、`hv-analysis`、`khazix-writer`。Agent 会自己 clone 到对应目录，不用你操心路径。

---

## ✨ Skills

<a id="-skills"></a>

<table>
<tr><td>

### 🧹 neat-freak（洁癖）

> *"每次任务做完要退出窗口的时候，如果不跑一遍 /neat，我就浑身难受，如坐针毡如芒刺背如鲠在喉。"*

每次你在 Agent 里干完一件事，跑一下 `/neat`，它会把你这次会话改的东西，跟项目里的**文档**、**CLAUDE.md / AGENTS.md**、**Agent 记忆**全部对齐一遍，最后给你一份变更摘要。

**为什么需要这个**

你大概也遇到过：代码都迭代了七八轮，文档还是最初那一版；记忆里写着用 SQLite，其实你早换 PostgreSQL 了；CLAUDE.md 里的接口列表跟实际路由对不上。Agent 看着这些过期信息，越用越笨。

不是模型变笨，是文档和记忆脑腐了。neat-freak 就是清这个的。

**它会动哪三层东西**

- 项目根的 CLAUDE.md / AGENTS.md（给当前 AI 看的）
- 项目的 docs/ 和 README（给同事和其他人看的）
- Agent 自己的记忆系统（给跨会话的自己看的）

这三层受众不同，职责不重叠，得分别处理。这也是我当时不满意 Claude Code 那个 AutoDream 的原因——它只动记忆，不动文档。

**怎么触发**

```
/neat            # 直接命令
整理一下          # 自然语言
同步一下          # 自然语言
sync up          # English
```

**🌐 跨平台**：Claude Code · Codex · OpenCode · OpenClaw

[![ClawHub](https://img.shields.io/badge/ClawHub-v1.0.1-EC4899?style=flat-square)](https://clawhub.ai)
[![Tessl](https://img.shields.io/badge/Tessl-0.1.1-3B82F6?style=flat-square)](https://tessl.io/registry/khazix-skills/neat-freak)

→ [SKILL.md](./neat-freak/SKILL.md) · [公众号讲解](https://mp.weixin.qq.com/s/tg1wd-iN2gWHWhXdY0faeg)

</td></tr>
</table>

<table>
<tr><td>

### 🔭 hv-analysis（横纵分析法）

> *"纵向追时间深度，横向追同期广度，最终交汇出判断。"*

想搞懂一个产品 / 公司 / 概念 / 人物到底是怎么回事，丢给它就行。

它会同时跑两条线：**纵向**把研究对象从诞生讲到当下，像讲故事一样把演变讲完整；**横向**把同期所有主要竞品摆出来逐一对比。最后两条线一交叉，能看出一些只看现状或只看历史看不出来的东西。

最后给你一份**排版精美的 PDF 研究报告**，10,000–30,000 字。

**适合**

- 调研竞品 / 调研一个新概念 / 调研一个公司
- 写作前期需要系统性的素材准备
- 对一个领域想从零搞懂

**不适合**

- 单纯查个名词解释 — 那种问题用普通对话就行，杀鸡用牛刀
- 写公众号文章 — 那个用下面的 khazix-writer

[![ClawHub](https://img.shields.io/badge/ClawHub-v1.0.0-EC4899?style=flat-square)](https://clawhub.ai)
[![Tessl](https://img.shields.io/badge/Tessl-published-3B82F6?style=flat-square)](https://tessl.io/registry/khazix-skills/hv-analysis)

→ [SKILL.md](./hv-analysis/SKILL.md) · [公众号讲解](https://mp.weixin.qq.com/s/Y_uRMYBmdLWUPnz_ac7jWA)

</td></tr>
</table>

<table>
<tr><td>

### ✍️ khazix-writer（卡兹克写作）

> *"有见识的普通人在认真聊一件打动他的事。"*

我自己写公众号的那套写作 skill。装上之后，Agent 写出来的东西就是我的口吻、我的节奏、我的禁忌词全在里面。

**适合**

你看过我公众号「数字生命卡兹克」的文章，觉得风格还行，想让你的 AI 也照着这个调子写东西。比如丢一篇 PDF / 一段语音转文字 / 一个新闻链接，让它写成长文。

**不适合**

你想要的是"通用好文笔"。这个 skill 是有立场的——它会**拒绝**写「赋能、抓手、闭环」、**拒绝**「首先...其次」、**拒绝**「在当今 AI 快速发展的时代」、**拒绝**「说白了 / 本质上 / 换句话说」。如果你的目标读者就好这一口，那这个 skill 不适合你。

**它会做什么**

- 完整的写作风格规则（节奏、叙事、判断、修辞）
- 四层自检体系（结构、节奏、内容、文字）
- 一套风格示例库（可以让 AI 直接对照）

[![ClawHub](https://img.shields.io/badge/ClawHub-v1.0.0-EC4899?style=flat-square)](https://clawhub.ai)
[![Tessl](https://img.shields.io/badge/Tessl-0.1.1-3B82F6?style=flat-square)](https://tessl.io/registry/khazix-skills/khazix-writer)

→ [SKILL.md](./khazix-writer/SKILL.md) · [公众号讲解](https://mp.weixin.qq.com/s/AtxGrii_K-nzkwUM9SNhEg)

</td></tr>
</table>

---

## 📝 Prompts

<a id="-prompts"></a>

<table>
<tr><td>

### 🔭 横纵分析法（Prompt 版）

上面那个 hv-analysis Skill 的**轻量版**——一段 prompt，复制粘贴到任何支持 Deep Research 的模型里就能跑（ChatGPT Deep Research、Gemini Deep Research、Grok Deep Search、Claude Research 都行），不需要安装任何东西。

半小时左右出一份万字级研究报告。

适合还没开始用 Claude Code / Codex 这类带 Skill 系统的 Agent，但又想体验一下这个方法论的人。

→ [横纵分析法.md](./prompts/横纵分析法.md) · [公众号讲解](https://mp.weixin.qq.com/s/Y_uRMYBmdLWUPnz_ac7jWA)

</td></tr>
</table>

---

## 🌟 关于

我是数字生命卡兹克，公众号「数字生命卡兹克」、虚实传媒（Virxact）创始人。视觉传达设计出身，做过用户研究和交互设计，**不是程序员**。

这些 skill 都是我自己每天在用的，开源出来如果对你有帮助，给个 ⭐ 就行。有问题或建议，欢迎在 Issues / Discussions 里说一声。

---

<div align="center">

[MIT License](./LICENSE) · 自由使用 / 修改 / 再分发

Made by [@KKKKhazix](https://github.com/KKKKhazix)

</div>
