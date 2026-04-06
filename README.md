# Virxact Open Skills

卡兹克（[虚实传媒 Virxact](https://virxact.com)）开源的 AI Skills 合集。

这里是我们自己在用的、经过长期打磨的 Skills，现在决定把它们完整地、一字不改地开源出来。

## 什么是 Skill

Skill 是一种可以被 AI 编程工具（如 [Claude Code](https://docs.anthropic.com/en/docs/claude-code)）加载的结构化指令集。它把一个人的方法论、经验、风格偏好蒸馏成一套 AI 可以理解和执行的规则体系，让 AI 在特定场景下按照这套方法论来工作。

简单来说，Skill = 把一个人的能力打包成 AI 可以复用的模块。

## 当前已开源的 Skills

| Skill | 说明 | 路径 |
|-------|------|------|
| **kaizike-writer** | 卡兹克公众号长文写作 Skill，包含完整的写作风格规则、四层自检体系、内容方法论和风格示例库 | [`kaizike-writer/`](./kaizike-writer/) |

## 安装方法

### Claude Code（推荐）

1. 下载你想用的 Skill 文件夹（比如 `kaizike-writer/`）
2. 放到你的 Claude Code 项目的 `.skills/skills/` 目录下
3. 启动 Claude Code 即可自动加载

```bash
# 示例：安装 kaizike-writer
git clone https://github.com/KKKKhazix/open-skills.git
cp -r open-skills/kaizike-writer /你的项目路径/.skills/skills/
```

### 手动使用

你也可以直接把 `SKILL.md` 的内容复制到任何支持自定义 Prompt 的 AI 工具中使用。

## 关于开源这件事

这是一个互联网开源精神回归的时代。我们见到无数人、无数大佬，好像回到了 30 年前互联网精神最本质的时代，每个人都在无私分享，把自己的方法、把自己的经验总结成 Skill，分享出来。

我们也想给这个时代贡献一份自己的力量。

## License

[MIT](./LICENSE)
