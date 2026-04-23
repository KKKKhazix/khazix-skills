# Khazix Skills - Claude Code Plugin

數字生命卡兹克（Khazix）的 Claude Code 技能集合。

## 包含的 Skills

### 1. khazix-writer
公眾號長文寫作 skill，用於撰寫公眾號文章、長文創作。

**觸發詞：** 寫文章、寫稿子、幫我寫、續寫、擴寫、公眾號文章、長文、出稿

### 2. hv-analysis
橫縱分析法（Horizontal-Vertical Analysis）深度研究 skill，用於系統性研究產品、公司、概念或技術。

**觸發詞：** 橫縱分析、研究一下、幫我分析、深度研究、做個研究、調研一下、竞品分析

## 安装方法

### 推荐：Claude Code 插件市场（一键安装，自动更新）

```bash
# 添加到插件市场
claude plugin marketplace add KKKKhazix/khazix-skills

# 安装插件
claude plugin install khazix-skills@KKKKhazix
```

## 使用方法

安裝後，在 Claude Code 中使用：

```bash
# 使用寫作 skill
/khazix-writer 幫我寫一篇關於 AI 的文章

# 使用橫縱分析 skill
/hv-analysis 研究一下 ChatGPT
```

## 更新

Claude Code 會自動檢查更新，或手動更新：

```bash
claude plugin update khazix-skills
```

## 原理說明

### Plugin 系統工作原理

1. **Git Clone**: Claude 將 plugin 倉庫 clone 到本地 `~/.claude/plugins/` 目錄
2. **Skill 註冊**: 讀取 `plugin.json`，將所有 skills 註冊到 Claude 的技能系統
3. **自動更新**: 定期 `git pull` 檢查更新，或手動觸發更新
4. **版本管理**: 通過 Git tags/branches 管理不同版本

### Plugin vs MCP Server

- **Plugin**: 靜態內容（markdown skills），通過 Git 同步，無需運行進程
- **MCP Server**: 動態服務（API、工具），需要運行獨立進程提供實時功能

Plugin 適合分享可重用的提示詞模板和工作流程，MCP Server 適合提供動態數據和外部服務集成。

## License

MIT
