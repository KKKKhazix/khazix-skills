[![MseeP.ai Security Assessment Badge](https://mseep.net/pr/kkkkhazix-khazix-skills-badge.png)](https://mseep.ai/app/kkkkhazix-khazix-skills)

<div align="center">

**中文** · [English](./README.en.md)

# 🧰 Khazix Skills

#### 我自己每天在用的一些 AI Skill，都开源在这里

[![License](https://img.shields.io/badge/License-MIT-3B82F6?style=for-the-badge)](./LICENSE)
[![Skills](https://img.shields.io/badge/Skills-6-10B981?style=for-the-badge)](#-skills)
[![AgentSkills](https://img.shields.io/badge/AgentSkills-Standard-8B5CF6?style=for-the-badge)](https://agentskills.io)

![Claude Code](https://img.shields.io/badge/Claude_Code-Skill-D97706?style=flat-square&logo=anthropic&logoColor=white)
![Codex](https://img.shields.io/badge/Codex-Skill-10B981?style=flat-square&logo=openai&logoColor=white)
![40+ Agents](https://img.shields.io/badge/40%2B_Agents-Compatible-3B82F6?style=flat-square)

</div>

都是在自己项目里跑通了一段时间，确实省事，才搬出来开源的。没什么花活，就是几个挺实用的东西。

这里的每个 Skill 都是 Agent 能直接加载的结构化指令集，遵循 [Agent Skills](https://agentskills.io) 开放标准。Claude Code、Codex、Qoder、Kimi Code、iFlow、CodeBuddy、Cursor 等 40+ 支持该标准的 Agent 都能装。

---

## 📋 目录

| 名字 | 一句话 | 讲解 |
|---|---|---|
| 🧭 [**leader（领导）**](#-leader领导) | 帮你把一句模糊的想法定义成一个清晰的**目标**，让 AI 拿着自己跑几个小时到完成 | — |
| 💽 [**storage-analyzer（清理垃圾）**](#-storage-analyzer清理垃圾) | 一句话扫描 Mac / Windows 整机磁盘，三色分级给清理决策，网页上一键移废纸篓 | [公众号文章](https://mp.weixin.qq.com/s/NyOMIlOD986OC4SI9vmxlA) |
| 🔥 [**aihot（AI HOT 资讯查询）**](#-aihotai-hot-资讯查询) | 让 Agent 用一句话拿到 aihot.virxact.com 每天的 AI HOT 日报和全部 AI 动态，无需 API Key | [aihot.virxact.com](https://aihot.virxact.com) |
| 🧹 [**neat-freak（洁癖）**](#-neat-freak洁癖) | 干完活跑一下 `/neat`，自动对齐项目文档、CLAUDE.md、Agent 记忆，并审计规则有没有被执行 | [公众号文章](https://mp.weixin.qq.com/s/tg1wd-iN2gWHWhXdY0faeg) |
| 🔭 [**hv-analysis（横纵分析法）**](#-hv-analysis横纵分析法) | 想搞懂一个产品/公司/概念是怎么回事，丢给它，给你一份万字 PDF 研究报告 | [公众号文章](https://mp.weixin.qq.com/s/Y_uRMYBmdLWUPnz_ac7jWA) |
| ✍️ [**khazix-writer（卡兹克写作）**](#-khazix-writer卡兹克写作) | 装上之后，Agent 用我的口吻和节奏写公众号长文 | [公众号文章](https://mp.weixin.qq.com/s/AtxGrii_K-nzkwUM9SNhEg) |

---

## 📦 安装方式

在 Claude Code、Codex 等支持 Agent Skills 的工具里，直接说：

```
帮我安装这个 skill：https://github.com/KKKKhazix/khazix-skills/tree/main/<skill-name>
```

把 `<skill-name>` 换成你想装的那个，比如 `neat-freak`、`hv-analysis`、`khazix-writer`。Agent 会自己 clone 到对应目录，不用你操心路径。

你的 Agent 不支持 Skill 也没关系：把对应目录的 `SKILL.md` 全文下载下来，当成项目规则文件（或直接贴进对话）让 Agent 照着执行，效果一致。

---

## ✨ Skills

<a id="-skills"></a>

<table>
<tr><td>

### 🧭 leader（领导）

> *"你说让测试变绿，最省力的办法不是修代码，是把测试删了。"*

**它只解决一件事：帮你定义目标。**

把你脑子里那句模模糊糊、自己都还没想清楚的需求，变成一份目标任务书——粘进目标模式（Claude Code 的 `/goal`、Codex 的目标模式）就能让 AI 独立跑几个小时到完成。你全程只做一次复制粘贴。

**为什么是「目标」**

人和 AI 的协作单位一直在变大：过去是一轮对话，后来是一个任务，2026 年的今天是一个目标——你给它一个目标，它自己拆任务、自己调工具、自己验证、失败自己重试，跑一整夜，你只管验收。

但当 AI 真能跑一整夜，一个以前还能临场补救的问题就变得致命：**你的目标写得对不对**。短任务跑偏你看一眼就能纠正；长程任务跑偏，你睡醒时它已经朝错误方向狂奔了八小时。它越勤奋，浪费得越彻底。

**目标里最重要的部分，是「什么不能做」**

肯尼迪那句登月宣言，关键不在「登月」，在后半句——把人送上月球，**然后安全带回地球**。多出来的「安全返回」四个字，一笔删掉了「单程票」这个最省钱的解法。

Goal 告诉 AI 往哪走，Harness 告诉它哪些路不许走。**没有 Harness 的 Goal，AI 永远会找到你没想到的捷径。**

**目标七问（心法）**

给 AI 定目标就像派一艘船出海，出海前你必须想清楚七件事，缺一条都不行：

| # | 问题 | 出海版 | 落到任务书 |
|---|---|---|---|
| 1 | **目的** | 我们为什么出这趟海，找香料还是探航线 | 遇到没写到的岔路口，它靠这句自己判断 |
| 2 | **完成态** | 「出去转一圈」不算，「带回三船香料」才算 | 具体到靠岸那一刻机器就能判 |
| 3 | **证据** | 谁上船清点货舱。不能船长说满载就是满载 | 每条验收都要贴出实际命令输出 |
| 4 | **反作弊** | 不许劫商船凑数：指标达成，事一件没干 | 把偷懒路径一条条点名禁止 |
| 5 | **地界** | 只许走这三条航线；粮食只够三十天 | 白名单 + 跑满 N 轮即停 |
| 6 | **取舍** | 风暴里保货还是保船？不说，船长只能猜 | 「算得对 > 做得全 > 做得快」 |
| 7 | **未知** | 空白海域别硬闯也别抛锚，记下来绕过去 | 拿不准的写进待裁决清单，跳过做别的 |

还有第零问：**这张海图是你自己测的，还是听来的**。所以它动笔前一定先钻进代码库亲手跑一遍——文档里写的命令，实际可能根本不存在。

**怎么用**

跟它说一句想法（下面任意一句都能触发），它先实测调研，再问你最多 5 个必须你拍板的问题，然后写出任务书。全程约 12 分钟。

```
帮我给 agent 写个目标
帮我详细拆一下这个目标
写个 goal 提示词
让 agent 自己跑这个项目
```

产出是纯 Markdown，没有目标模式的 Agent 直接粘贴发送也一样用。拿到任务书后推荐用规划强的模型出目标、执行强的模型跑长程——我自己是 Claude Fable 5 规划 + GPT-5.6 Sol 执行，国产的 Kimi K3 规划、GLM-5.2 执行也不错。

→ [SKILL.md](./leader/SKILL.md)

</td></tr>
</table>

<table>
<tr><td>

### 💽 storage-analyzer（清理垃圾）

> *"清 Mac 垃圾这件事，过去十几年都靠 CleanMyMac 这种翻译层软件。现在一个 skill 就够了。"*

随口跟 Agent 说一句"帮我看看存储"或"C 盘满了"，它会扫一遍整机磁盘，在浏览器里打开一份**交互式 HTML 报告**：磁盘总览、占用 Top 5、清理优先级、🟢🟡🔴 三色分级清单。命令一键复制，也可以直接点按钮移到废纸篓 / 删除（每次都有二次确认弹窗）。

**它和 CleanMyMac 的区别**

CleanMyMac 是个写死规则的软件，扫到一个 3.8G 的 Chrome 文件夹只会告诉你"用户缓存文件，可删"——但你不知道里面到底是什么、删了哪些网站要重新登录。

这个 skill 由 Agent 驱动，每一项都给你**具体路径 + 类型说明 + 删了的影响 + 推荐处置方式**。比如那 97 GB 的 UUID Container 它会告诉你是 B 站离线视频缓存、建议在 B 站客户端里清而不是手删。

**三色分级是核心**

- 🟢 **绿灯** — 纯缓存、临时文件，删了自动再生。可以让 Agent 一键清
- 🟡 **黄灯** — 含用户数据（离线视频、下载、项目代码）。只给"在访达打开"和"移废纸篓"，让你自己决定，不给直接删
- 🔴 **红灯** — 运行中应用核心数据、系统文件。解释为什么不能动，最多给"打开文件夹"，永远不给删除按钮

**铁律**

全程只读扫描，绝不擅自动手。删除操作必须你在浏览器上点按钮 + 浏览器弹框二次确认才执行。本地服务跑在 127.0.0.1 + 随机端口 + token，安全模型上三套白名单分级（绿灯能删、橙灯只能移废纸篓、红灯只能打开）。

macOS 完整实测；Windows 代码就绪（多盘符已支持），首次用建议留个心眼。

**怎么触发**

```
帮我看看存储
C 盘满了
清理一下磁盘
看下电脑空间
storage analysis
```

→ [SKILL.md](./storage-analyzer/SKILL.md) · [公众号讲解](https://mp.weixin.qq.com/s/NyOMIlOD986OC4SI9vmxlA)

</td></tr>
</table>

<table>
<tr><td>

### 🔥 aihot（AI HOT 资讯查询）

> *"AI 圈一天发太多东西，等我反应过来已经过气了——干脆让 Agent 帮我每天扫一遍。"*

让支持 SKILL.md 的 Agent 用最自然的中文一句话拿到 [aihot.virxact.com](https://aihot.virxact.com) 每天的 AI HOT 日报和全部 AI 动态。无需 API Key、无需配 MCP server。

**它能做什么**

- 拉今日 / 指定日期的 AI HOT 日报（按主题打包好的成品）
- 拉精选条目流（每日精编候选池）
- **看当前最热事件**（按热度排，不是按时间倒序）
- 按分类拉条目（模型 / 产品 / 行业 / 论文 / 技巧）
- 按时间窗拉（原生支持过去 24 小时和最近 7 天）
- 关键词 / 公司 / 主题搜索（"OpenAI 最近发的"、"Sora 相关"、"RAG 论文"）
- **把当前全部精选同步到本地**，之后只接收变化

**怎么触发**

```
今天 AI 圈有什么新东西
现在 AI 圈最热的事件是什么
看一下 5 月 6 号的 AI 日报
最近一周的 AI 论文
最近 OpenAI 有什么发布
把 AI HOT 当前全部精选同步到本地
```

→ [SKILL.md](./aihot/SKILL.md) · [aihot.virxact.com](https://aihot.virxact.com) · [接入指南](https://aihot.virxact.com/agent)

</td></tr>
</table>

<table>
<tr><td>

### 🧹 neat-freak（洁癖）

> *"每次任务做完要退出窗口的时候，如果不跑一遍 /neat，我就浑身难受，如坐针毡如芒刺背如鲠在喉。"*

每次你在 Agent 里干完一件事，跑一下 `/neat`，它会把你这次会话改的东西，跟项目里的**文档**、**CLAUDE.md / AGENTS.md**、**Agent 记忆**全部对齐一遍，还会检查项目规则有没有被真实执行，最后给你一份变更摘要。

**为什么需要这个**

你大概也遇到过：代码都迭代了七八轮，文档还是最初那一版；记忆里写着用 SQLite，其实你早换 PostgreSQL 了；CLAUDE.md 里的接口列表跟实际路由对不上。Agent 看着这些过期信息，越用越笨。

不是模型变笨，是文档和记忆脑腐了。neat-freak 就是清这个的。

**它会动哪三层东西**

- 项目根的 CLAUDE.md / AGENTS.md（给当前 AI 看的）
- 项目的 docs/ 和 README（给同事和其他人看的）
- Agent 自己的记忆系统（给跨会话的自己看的）

这三层受众不同，职责不重叠，得分别处理。它还会把规则当成知识来审：比如 CLAUDE.md / AGENTS.md 是否同源、必备文件有没有缺、规则里引用的路径还在不在。规则不落地，下一轮 Agent 还是会按错前提做事。

**v3.0 的两条底线**

- **小项目有专门的轻量路径**：没有 git、没有规则文件的 vibe 项目，它会把 README 对齐到代码现状、默认帮你建一份最小的 AI 规则文件（下次开新会话直接恢复上下文），再把 PLAN.md、调试脚本、`xxx_old` 这类会话残留列成清单等你确认。
- **绝不擅自删东西**：所有删除只出候选清单，你确认了才动手；机器生成的记忆默认只读；文件里读到的「执行这条命令」不会被当成你的授权。

**怎么触发**

```
/neat                          # 直接命令
跑一下洁癖                      # 点名
把文档和记忆整理一下             # 收尾意图
新人接手，帮我做个 clean handoff  # 交接意图
```

纯代码任务、整理数据 / 周报这类请求不会触发它——它只管项目知识收尾。

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

**怎么触发**

```
研究一下 Cursor 这家公司
帮我做个竞品分析
这个产品到底是怎么回事
帮我做个 deep research
```

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

**怎么触发**

```
帮我写篇文章
把这个素材写成长文
按我的风格写一下
帮我续写
```

→ [SKILL.md](./khazix-writer/SKILL.md) · [公众号讲解](https://mp.weixin.qq.com/s/AtxGrii_K-nzkwUM9SNhEg)

</td></tr>
</table>

---

## 🌟 关于

我是数字生命卡兹克，虚实传媒创始人，努力地分享一些有趣的 AI 干货，也愿我们永远对世界保持好奇。

这些 skill 都是我自己每天在用的，开源出来如果对你有帮助，给个 ⭐ 就行。有问题或建议，欢迎在 Issues / Discussions 里说一声。

---

<div align="center">

[MIT License](./LICENSE) · 自由使用 / 修改 / 再分发

Made by [@KKKKhazix](https://github.com/KKKKhazix)

</div>
