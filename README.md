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

数字生命卡兹克的 AI 工具箱。

这里是我自己在用的、经过长期打磨的 Prompts 和 Skills，现在决定把它们完整地、一字不改地开源出来。

两种东西，一个目的：把我积累的方法论变成可复用的工具。

- **Prompts** — 轻量级，复制粘贴到任何 AI 对话或 Deep Research 里就能用
- **Skills** — 重量级，遵循 [Agent Skills](https://agentskills.io) 开放标准的结构化指令集，安装后 Agent 会自动加载

## Prompts

| Prompt | 说明 | 用法 | 讲解 |
|--------|------|------|------|
| [**横纵分析法**](./prompts/横纵分析法.md) | 通用深度研究框架，融合历时-共时分析与竞争战略视角，半小时出一份万字级研究报告 | 复制 Prompt，修改「研究对象」，丢进任何支持 Deep Research 的模型 | [公众号文章](https://mp.weixin.qq.com/s/Y_uRMYBmdLWUPnz_ac7jWA) |

## Skills

| Skill | 说明 | 讲解 |
|-------|------|------|
| [**hv-analysis**](./hv-analysis/) | 横纵分析法深度研究 Skill，自动联网收集信息，纵向追时间深度 + 横向追竞争广度，最终输出排版精美的 PDF 研究报告 | [公众号文章](https://mp.weixin.qq.com/s/Y_uRMYBmdLWUPnz_ac7jWA) |
| [**khazix-writer**](./khazix-writer/) | 卡兹克公众号长文写作 Skill，包含完整的写作风格规则、四层自检体系、内容方法论和风格示例库 | [公众号文章](https://mp.weixin.qq.com/s/AtxGrii_K-nzkwUM9SNhEg) |

### Skill 安装方式

**通过 Agent 安装**

在 Claude Code、Codex、OpenClaw 等支持 Skill 的 Agent 中，直接对话：

```
安装这个 skill：https://github.com/KKKKhazix/khazix-skills
```

**手动安装**

1. 点仓库右上角 **Code → Download ZIP**，或者 `git clone https://github.com/KKKKhazix/khazix-skills.git`
2. 把你想装的 Skill 文件夹（比如 `hv-analysis/`）整个复制到对应工具的 Skills 目录下

各工具的 Skills 安装路径：

| 工具 | 路径 |
|------|------|
| Claude Code | `~/.claude/skills/` |
| OpenClaw | `~/.openclaw/skills/` |
| Codex | `~/.agents/skills/` |

例如装 hv-analysis 到 Claude Code：

```bash
git clone https://github.com/KKKKhazix/khazix-skills.git
cp -r khazix-skills/hv-analysis ~/.claude/skills/
```

## License

[MIT](./LICENSE)
