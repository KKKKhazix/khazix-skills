---
name: storage-analyzer
description: >
  macOS / Windows 只读存储分析助手（自动识别系统）。扫描整机磁盘占用，找出
  占空间大户，把每一项分成 🟢可自动清理 / 🟡需人工判断 / 🔴谨慎清理 三级并给出
  可执行处置方案，生成排版精美、可折叠、命令可一键复制的交互式 HTML 报告，并可
  起本地服务在网页上一键删除（移废纸篓/直接删）。扫描全程只读。务必在以下场景
  使用：用户说"存储分析""磁盘满了""C盘/硬盘满了""空间不够""清理空间"
  "清理磁盘""占空间""哪些东西占地方""帮我看看存储""看一下电脑存储/空间"
  "存储空间""电脑空间不够""内存满了/不够/不足""看下内存/存储"（中文口语里
  "内存"常指存储空间）"storage analysis""disk cleanup""清缓存""磁盘清理"；
  或用户抱怨电脑没空间、想知道什么东西吃硬盘、想要清理建议时。注意：若用户明确
  指运行内存/RAM（如"哪个进程吃内存""内存占用高"想看活动监视器），那是 RAM
  不是存储，不属于本 skill。
---

# Storage Analyzer

对 macOS 做一次只读存储分析，产出交互式 HTML 报告。流程：扫描 → 分析分级 → 生成网页 → 打开。

## 铁律

- **全程只读。** 只能跑扫描/统计/列目录/读元信息（df、du、diskutil、stat、ls）。绝对禁止 rm、mv、rmdir、清空回收站、改权限等任何写操作。
- **删除命令只展示，不执行。** 报告里给出的清理命令是供用户自己在终端确认后运行的。即使用户在对话里说"帮我删"，也要先停下确认（命中全局红线：删除文件必须先问），不要直接代跑。
- **估算标注清楚。** 涉及"可释放空间"一律说明是估算值。
- **路径、命令保留原文不翻译。**

## 执行流程

### Step 1 扫描（只读）

```bash
python3 scripts/scan.py > /tmp/storage_scan.json
```

`scan.py` 自动识别系统（`sys.platform`）：
- **macOS**：扫 home、library、caches、containers、group_containers、app_support、applications、downloads、dev_caches，用 `du` 算大小。
- **Windows**：扫 user_profile、appdata_local、appdata_roaming、temp、downloads、program_files(_x86)、dev_caches，用 `os.scandir` 算大小；`system.disks` 含所有盘符。

输出 JSON：`system`（系统/磁盘信息，含 `disk_name` 主盘名 + `disks` 全部盘）+ `groups`（各组子目录大小，已降序、过滤 50MB 以下）。扫描较慢，耐心等。读不到的目录标 `denied`，需在报告里列出并提示遗漏体量。

### Step 2 分析与分级

先看 `system.os` 判断系统，读对应的数据布局参考：macOS 读 [references/macos.md](references/macos.md)，Windows 读 [references/windows.md](references/windows.md)（讲该系统东西存哪、怎么辨认、归哪一级）。然后读 `/tmp/storage_scan.json` 做这几件事：

1. **挑 Top 5** 占用大户，判定类型（系统资产/应用本体/应用数据/应用缓存/开发缓存/用户文件/媒体内容/下载内容/虚拟机镜像/回收站/其他）。
2. **识别"神秘大目录"**：UUID 命名的 Container、不明的隐藏目录，要追查它属于哪个 App、装的是什么（例如某 97GB 的 UUID Container 实为 Bilibili 离线视频缓存）。必要时 `ls`/`du` 深入一层看清楚，但仍只读。
3. **三级分类 = 清理决策清单，不是全盘点。** 只把"存在'要不要动它'这个决策"的项放进三灯；日常在用的正常应用、操作系统本身、海量零碎小文件没有清理决策，不进三灯，它们落在磁盘条的蓝色"系统及其他"里。判定标准：
   - 🟢 **可自动清理**：纯缓存、临时文件、安装包残留、明确可再生且不影响功能、不丢用户数据（pip/uv/**npm cache（`_cacache`，不是 pnpm store）**/Xcode DerivedData 等开发缓存、浏览器缓存）。**特别注意：pnpm store（`~/Library/pnpm/store`）不是普通缓存，它是所有项目 `node_modules` 的硬链接源，直接 `rm -rf` 会导致所有 pnpm 项目依赖断裂。pnpm store 只能走 `pnpm store prune` 清理未引用包，不可给一键删除按钮。**
   - 🟡 **需人工判断**：含用户数据或有判断成本（离线视频、文档、项目代码 node_modules、聊天记录、设计稿）。给内容画像 + 至少 3 句处置路径（应用内清理 / 系统工具 / 文件管理器手动审查，三选最合适）+ 风险提示。**所有橙灯项在服务模式下自动有「在访达/资源管理器打开」按钮**（跳过去自己审查删）；如果该项有一个核实过、删了不破坏 App 的安全子路径（如 B站离线视频的 `.Downloads` 目录、旧备份目录），给它 `trash_paths` → 网页出现「移到废纸篓」按钮（橙灯只准移废纸篓、可逆，绝不给"直接删除"）。App 托管又无安全子路径的（Chrome/微信）只给打开按钮、不给 trash_paths。按钮下方会自动写明注意事项（打开只查看不删、移废纸篓可逆需清空才释放等）；如果某项在文件管理器里是 App 内部格式、不方便手动挑选，给它一个 `open_note` 字段做客观说明（会显示在注意事项里）。**口吻要中性、像产品说明**：直接描述"这里是什么结构、为什么不好手动删、想精细操作该去哪"，不要写成"我发现/提醒注意/看着像没视频"这种暴露开发者踩坑视角的话。
   - 🔴 **谨慎清理（有决策但不建议手删）**：你可能想动、但建议别手删的具体项——重复安装的应用、想卸载的大应用、运行中应用的核心数据等。给"为什么不建议手删" + `indirect_release` 写**具体卸载步骤**（自带卸载器 / 启动台长按 / 右键移废纸篓 / AppCleaner 清残留 / App Store 可重装等，要可照做不是空话）。应用项给 `app_paths`（真实 `.app` 绝对路径数组）→ 网页出现「在文件管理器打开（去卸载）」按钮，定位到 App 让用户自己正规卸载。**红灯不给删除/卸载按钮**（应用在系统目录、可能要管理员密码、可能有自带卸载器和残留，后台代删不稳妥）。**纯系统文件、APFS 快照不要单独列红卡**（没有清理决策），归蓝色即可；系统层面的释放技巧（重启释 swap、Time Machine 快照策略、可清除空间自动回收）写进 `summary.long_term` 长期建议。

每个 🟢 项要给：预估释放空间、清理前需关闭的进程、可一键复制的清理命令（用移到废纸篓或 App 自身清理入口的安全方式，谨慎用 `rm`；如用 `rm` 必须是明确的缓存子目录）。

**大小字段写干净**：`size` / `size_estimate` 用"约 14 GB""合计约 8.6 GB"即可——"约"已表示估算，不要再加"（估算）"，重复且不专业（模板也会自动去掉这种冗余括号）。可再生属性已由分级标题和按钮说明覆盖，别塞进大小字段。

### Step 3 生成交互报告

把分析结果写成 analysis JSON（schema 见 `scripts/build_report.py` 顶部注释）。

**🟢 项必须带 `trash_paths`**（具体可删的绝对路径数组，区别于人类可读的 `path` 展示字段）——这是网页删除按钮的前提，漏了按钮就不出现。

**默认用一键删除模式（`server.py`）打开报告**，因为这个 skill 的核心价值就是网页上能直接清理：
```bash
python3 scripts/server.py /tmp/storage_analysis.json   # 自动开浏览器，Ctrl+C 停
```
`server.py` 起在 127.0.0.1 + 随机端口 + 随机 token。🟢 项给「移到废纸篓」(可逆) +「直接删除」(立即释放、不可逆)；🟡 项给「在访达打开」+（有安全子路径时）「移到废纸篓」。**安全模型——三套白名单，权限从严到宽**：`rm` 只允许绿灯 `trash_paths`；`trash` 允许绿灯+橙灯 `trash_paths`（橙灯永远不能 rm）；`open`（在文件管理器打开，非破坏性）允许上述全部 + 橙灯真实 `path`。所有请求 realpath 校验 + 必须在 $HOME 内 + token + Host 校验，每次点击浏览器先 confirm。osascript/SHFileOperationW 入废纸篓，macOS 首次弹访达自动化授权点允许即可。

仅当用户明确只想要一份可分享/留存的只读文件时，才用静态模式（无删除按钮，因为 `file://` 打开的页面碰不到文件系统）：
```bash
python3 scripts/build_report.py /tmp/storage_analysis.json ~/Desktop/storage-report.html && open ~/Desktop/storage-report.html
```

**排障：网页上没有删除/移废纸篓按钮** = 要么开的是静态报告（改用 `server.py`），要么 🟢 项漏了 `trash_paths`（补上重启服务）。

报告阅读流（固定顺序）：磁盘总览卡片（容量 + 进度条 + 三色容量 pills + 系统信息，纯数据）→ 占用排行 Top5 → 执行建议 → 🟢🟡🔴 三级可折叠卡片（命令一键复制）→ 长期优化建议。即"现状 → 诊断 → 处方 → 操作 → 预防"。

注意 `summary.overview` 要写成一句话洞察（直接说最大占用是什么、能释放多少），不要重复总/已用/可用数字——那些已在卡片大数字里显示。overview 渲染在"执行建议"小节开头作引子（普通文字），紧接着是 `summary.priority` 优先级清单。

磁盘进度条把"已用"拆成分段：绿(可自动清)+橙(需手动)+红(已识别的不建议动项)+蓝(系统及其他，自动取 已用−绿−橙−红 的余量)，余下为可用(灰底)。`summary.tier_stats` 的 green / yellow / red 三个值都要以可解析的 GB 数字开头（如 "约 27.8 GB"），脚本从中取数算分段；蓝色段和"系统及其他"pill 由模板自动算余量。

pills 只渲染解析出的纯数字（如"约 5.5 GB"），不显示数据里的附注，所以 tier_stats 三个值写干净的数字即可，别加"仅已识别项/系统未计"这类道歉式说明——系统文件本来就归在蓝色段，红色只放你能量化的 🔴 项（重复应用、可卸载大应用等），量不准的系统文件/快照自然落到蓝色。

### Step 4 对话里给摘要

报告生成后，在对话里用一段话给结论先行的摘要：总可释放估算、最该先清的 2-3 项、风险最高的一项。细节让用户看网页。

## 依赖与运行前提

- 全部脚本是 **Python 3 标准库**，零第三方依赖（不用 pip install）。
- **macOS** 自带 python3、`du`、`diskutil`、`osascript`，开箱即用。
- **Windows** 默认没装 Python——需先装 Python 3，且命令多为 `python` 或 `py -3`（不是 `python3`）。本 skill 命令示例写的是 `python3`，在 Windows 上自动改用 `python` / `py -3`。
- 本 skill 是 **agent 驱动**：扫描出数据后由 agent（Claude）做分级分析，不是双击即用的独立 App。

## 平台状态

- **macOS**：完整实现并实测（扫描 / 报告 / 一键删除全验证过）。
- **Windows**：代码已写（`scan.py` 的 `scan_windows`、`server.py` 的 `_trash_windows` 走 `SHFileOperationW`），但**未在真实 Windows 上实测**。首次在 Windows 跑要核对：目标目录路径、`os.scandir` 大小、回收站删除是否正常。多盘符已支持（主盘分段条 + 其他盘列表）。

## 长期优化建议素材（写进报告 summary.long_term）

- 定期清理：`brew cleanup`、Xcode DerivedData、浏览器缓存
- 可视化工具：DaisyDisk、GrandPerspective、OmniDiskSweeper
- 大文件归档到外置盘 / iCloud / NAS；macOS「系统设置 > 通用 > 储存空间」的优化选项
