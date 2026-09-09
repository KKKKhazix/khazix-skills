# local-patches

本目录存放「安装副本（`~/.claude/skills/`）有、但仓库版本没有」的本地增强，
以 patch 形式留档，方便日后向 upstream 提 PR 或重装修复。

## 生成时间

2026-09-09（对比 `~/.claude/skills/hv-analysis/` 与本仓库 `hv-analysis/`）

## 对比结论

两目录仅 `hv-analysis/scripts/md_to_pdf.py` 一个文件有差异，双向分歧：

| 改动 | 安装副本 | 仓库（feat/merge-whitepage-fix） |
|------|----------|----------------------------------|
| 中文字体栈增强（3 处：`@top-center` / `@bottom-center` / `body`） | ✅ 有 | ❌ 没有 → 见 0001 patch |
| 宽屏封面白页修复（`.cover` 的 `padding-top: 45%` → `30vh`） | ❌ 没有（还是 45%） | ✅ 有（9093a15，已 merge） |

## Patch 列表

### 0001-hv-analysis-md_to_pdf-macos-cjk-font-stack.patch

- **内容**：将 CSS 中 3 处 `font-family` 从单一 `"Droid Sans Fallback", Helvetica, Arial, sans-serif`
  扩展为完整的 macOS 中文字体栈（PingFang SC / Hiragino Sans GB / Noto Sans CJK SC 等 + emoji 字体）。
- **来源**：安装副本 `~/.claude/skills/hv-analysis/scripts/md_to_pdf.py`（2026-08-11 版）。
- **动机**：macOS 上 Droid Sans Fallback 通常不存在，中文字体回退不可控；显式字体栈保证
  页眉/页脚/正文在 macOS 渲染一致。
- **应用方式**（在本仓库根目录）：

  ```bash
  git apply local-patches/0001-hv-analysis-md_to_pdf-macos-cjk-font-stack.patch
  ```

  已通过 `git apply --check` 验证可干净应用。

## 待办提醒

安装副本 `~/.claude/skills/hv-analysis/scripts/md_to_pdf.py` **尚未包含宽屏白页修复**
（9093a15，`padding-top: 45%` → `30vh`）。合并本 patch 后重新同步安装副本即可同时获得
两项修复。
