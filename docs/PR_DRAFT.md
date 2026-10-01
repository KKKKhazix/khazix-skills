# PR 草稿：hv-analysis 修复宽屏封面白页 + macOS 中文字体栈增强

> 状态：**草稿，未提交**。对外动作（fork push / 开 PR）需用户确认后再执行。
>
- 目标仓库：KKKKhazix/khazix-skills（upstream）
- 源分支：`feat/merge-whitepage-fix`（fork: openclaw-jarvis-lab/khazix-skills）
- 基线：upstream/main `741eb55`
- 涉及 commit：`9093a15`（白页修复）、`5fb3bdf`（字体栈增强）

---

## PR 标题（建议）

```
fix(hv-analysis): 宽屏浏览器封面白页 + macOS 中文字体栈增强
```

## PR 描述（建议正文）

### 改动一：修复宽屏浏览器打开 HTML 时封面白页（30vh）

**问题背景**

`md_to_pdf.py` 生成的中间 HTML（调试用，与 PDF 同目录同名 `.html`）在浏览器里直接打开时，宽屏视口（1920px+）下封面整页看似空白——封面标题被推出首屏，用户第一眼以为生成失败。

**根因**

CSS 中 `.cover { padding-top: 45% }` 的百分比 padding 是相对**包含块宽度**计算的。A4 打印宽度（210mm）下 45% 表现正常；但浏览器宽屏视口下 45% × 1920px = 864px+，把标题顶出首屏。

**修复**

改用 `padding-top: 30vh`（相对视口高度）：

- 浏览器侧：标题稳在首屏可见，任何视口宽度都不再白页
- WeasyPrint 侧：vh 单位同样受支持，相对 A4 页面高度（297mm）约等于原 45% 宽度对应的视觉位置，**PDF 排版不变**

**测试方式**

1. 用 hv-analysis skill 生成任一报告，得到中间 `.html` 和 `.pdf`
2. 浏览器 1920px+ 宽度打开 `.html`：修复前封面白页，修复后标题首屏可见
3. 打开 `.pdf` 对比：封面排版与修复前一致（标题位置、分页均不变）

### 改动二：md_to_pdf 中文字体栈增强（macOS CJK fallback）

**问题背景**

原 `font-family: "Droid Sans Fallback", Helvetica, Arial, sans-serif` 只含一个 CJK fallback（Droid Sans Fallback）。macOS 上该字体通常不存在，中文实际落到系统默认字体，不同 macOS 版本表现不一致，部分环境中文渲染异常。

**修复**

页眉 `@top-center`、页脚 `@bottom-center`、`body` 三处统一扩展为完整跨平台 CJK 字体栈：

```
"PingFang SC", "Hiragino Sans GB", "Heiti SC", "Noto Sans CJK SC",
"Source Han Sans SC", "Microsoft YaHei", "Droid Sans Fallback",
"Apple Color Emoji", "Segoe UI Emoji", "Noto Color Emoji",
Helvetica, Arial, sans-serif
```

- macOS：命中 PingFang SC（系统自带），渲染稳定可预期
- Windows：命中 Microsoft YaHei
- Linux：命中 Noto Sans CJK SC / Source Han Sans SC
- 未装任何 CJK 字体的环境：仍回落 Droid Sans Fallback（原行为，不劣化）
- Emoji 字体前置保证 emoji 不缺字

**测试方式**

1. macOS 上运行 `python md_to_pdf.py input.md out.pdf`，检查 PDF 页眉页脚中文（"第 N 页"）与正文字体渲染
2. 有条件可在 Windows / Linux 各跑一次，确认命中各自平台字体
3. 无 CJK 字体环境（如极简容器）确认仍能回落渲染不报错

### 兼容性说明

- 两个改动均为纯 CSS 层面，不触碰 Python 逻辑与 Markdown 转换流程
- `vh` 是 CSS Values and Units Level 3 标准单位，WeasyPrint 与主流浏览器均已支持
- 字体栈为渐进增强，最坏情况回落到原字体链，无行为劣化
