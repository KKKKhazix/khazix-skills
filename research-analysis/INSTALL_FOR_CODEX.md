# Codex 安装说明

## 从 GitHub 安装

在 Codex 里说：

```text
帮我安装这个 skill：https://github.com/KKKKhazix/khazix-skills/tree/main/research-analysis
```

或手动复制目录：

```bash
mkdir -p ~/.codex/skills/research-analysis
rsync -a --exclude='.git' research-analysis/ ~/.codex/skills/research-analysis/
```

## 触发方式

安装后，直接说：

```text
研究一下这个新闻：……
深度研究一下这篇文章：……
调研一下这个开源项目：……
看看这个微信文章背后的研究源头：……
```

## 验收标准

一次合格输出至少包含：

- 事实核验
- 原始来源追踪
- 多视角矛盾图或其结果
- 横纵分析
- 反常识洞察
- Markdown 报告
- 信息来源清单
