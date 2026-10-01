# Linux 数据布局与分级参考

分析 Linux 扫描结果时读这份。讲"东西存在哪、怎么辨认、归哪一级"。

## 三个 Linux 独有的约束

分级之前先理解这三条，它们决定了报告能不能说真话。

**缺口对账**：`scan.py` 输出的 `accounting` 字段。macOS 上 `du` 读不到会报错、能标 `denied`；Linux 上 `du` 对 root 目录是**静默低估**——把读不到的算作 0 还返回成功。所以扫完要拿 `df` 已用减去已归类之和。

对账**按文件系统分别计算**（`per_filesystem` 数组，每项一个挂载点），不能把所有条目加总后只跟 `/` 比：`/home` 独立分区在 Linux 上极常见，合并对账会凭空捏造巨额「重叠」。条目归属靠 `st_dev` 而非路径前缀，因为挂载点可以嵌套在任意深度。

- `gap_kb > 0` → 差额归入蓝色「系统及其他」，并说明"其中可能有权限不足未读到的大户，可用 `sudo du -shx /var/lib/docker` 之类核实"。
- `overlap_kb` → 该盘合计**超过**实际已用。最常见成因是硬链接缓存（uv / pnpm / conda / nix）在多次 `du` 中被重复计数；文件系统压缩、reflink/CoW 共享、稀疏文件也会造成同向偏差。此时相关项的"预估释放空间"必须说明**实际释放量可能明显更小**。
- 条目带 `partial: true` → `du` 遇到读不到的子目录，返回的是偏小的小计（退出码非 0 或 stderr 有 denied）。报告里要说明该项实际更大。
- 条目带 `mountpoint: true` → 该子目录自身是挂载点，体量属于另一块盘，不计入本盘（它会在 `system.disks` 里作为独立盘出现）。

**跨文件系统降级**：`server.py` 的废纸篓只在**废纸篓自身所在**的文件系统内可用（不是"home 所在"——`XDG_DATA_HOME` 可能被指到别的盘）。挂在 `/mnt`、`/media`、外置盘上的项，即使是绿灯也不要给 `trash_paths`；给了也会被白名单构造阶段挡掉，按钮不会出现。这类项只给可复制命令。

**sudo 项 = 只读展示范本**：`groups.sudo_targets` 里的东西全是 root 所有。它们**照常上灯**（多为 🟢，`/var/log`、apt 缓存是标准可清项），标题带 `[需 sudo]`，给可复制命令，但 `trash_paths` **一律留空**——一键删除通道对它们物理关闭。即使误给了 `trash_paths`，`server.py` 也会按 `needs_sudo` 标记拒绝其进入 rm/trash 白名单（由代码强制，不靠约定）。这不是铁律的例外，而是"删除命令只展示、用户自己在终端确认后运行"的标准形态。

## 关键目录

| 目录 | 装什么 | 典型分级 |
|---|---|---|
| `~/.cache/{pip,uv,huggingface,torch,ms-playwright,go-build}` | 开发/模型缓存 | 🟢 可自动清 |
| `~/.npm`、`~/.pnpm-store`、`~/.cargo`、`~/.gradle`、`~/.m2`、`~/go/pkg` | 包管理缓存 | 🟢 |
| `~/.conda/pkgs`、`~/{ana,mini}conda3/pkgs` | conda 包缓存（`conda clean -a`） | 🟢 |
| `~/.local/share/Trash` | 废纸篓没清空——删了才真正释放 | 🟢 |
| `~/Downloads` 里的 .deb/.rpm/.AppImage/.run | 安装包残留 | 🟢 |
| `~/.cache/huggingface/hub`、模型权重 | 重下要几十 G，删前想清楚 | 🟡 |
| `~/.config/*`、`~/.local/share/*` | 应用数据（Chrome Profile、微信、QQ、飞书聊天记录） | 🟡 多为用户数据 |
| `~/.var/app/*`（flatpak）、`~/snap/*` | 沙盒应用数据 | 🟡 |
| `~/.local/share/Steam`、`~/.wine` | 游戏 / Wine 前缀 | 🟡 |
| 项目里的 `node_modules`、`.venv`、`target/`、`__pycache__` | 可重建但重建要时间 | 🟡 |
| `/opt/*`、`/usr/local/*` | 手装应用本体 | 🔴 走包管理器卸载，不手删 |
| 发行版包管理装的应用 | apt/dnf/pacman 装的 | 🔴 `indirect_release` 写卸载命令 |
| `/usr`、`/lib`、内核镜像 | 系统本身 | 不上灯，归蓝色「系统及其他」 |

`applications` 在 Linux 上不是单一目录：`/opt`、`/usr/local`、snap、flatpak、AppImage 五处并存。`.desktop` 文件在 `~/.local/share/applications` 和 `/usr/share/applications`。

## 需要 sudo 的系统大户

`scan.py` 已探测这些路径（读不到就标 `denied`），分级时配上对应命令：

| 路径 | 清理手法 | 说明 |
|---|---|---|
| `/var/lib/docker` | `docker system df` 看构成，`docker system prune -a` | DL 机器上常年几十 G，是最容易被忽略的头号大户 |
| `/var/lib/containers` | `podman system prune -a` | podman 等价物 |
| `/var/log`（含 journal） | `sudo journalctl --vacuum-size=200M` | 长期运行的机器上能吃掉几十 G |
| `/var/cache/apt/archives` | `sudo apt clean` | Debian/Ubuntu 标准可清项 |
| `/var/cache/pacman/pkg` | `sudo pacman -Sc` | Arch |
| `/var/cache/dnf` | `sudo dnf clean all` | Fedora/RHEL |
| `/var/lib/snapd/snaps` | `sudo snap set system refresh.retain=2` + 删旧 revision | snap 默认留 3 个版本，每个都是完整镜像 |
| `/nix/store` | `nix-collect-garbage -d` | NixOS |
| 旧内核 | `sudo apt autoremove --purge` | `/boot` 是独立小分区时最容易先满 |

## 间接释放（写进 long_term，不上红灯）

- `docker system prune -a` / `docker builder prune` —— 悬空镜像和构建缓存
- `conda clean -a`、`pip cache purge`、`uv cache clean`、`npm cache clean --force`
- `journalctl --vacuum-time=7d` 常态化，或改 `/etc/systemd/journald.conf` 的 `SystemMaxUse`
- snap 旧 revision 清理 + `refresh.retain=2`
- `sudo apt autoremove --purge` 清旧内核和孤儿包
- 可视化工具：`ncdu`（终端首选）、`baobab`（GNOME 磁盘用量分析器）、`filelight`（KDE）
- 大文件归档到外置盘 / NAS；`/home` 独立分区时考虑扩容而非反复清理

## 删除机制（XDG Trash）

`server.py` 在 Linux 上按 XDG Trash 规范入废纸篓，三级回退：`gio trash` → `trash-put`（trash-cli）→ 纯标准库手写。

标准库那级会同时写两份，缺一不可：
- `~/.local/share/Trash/files/<name>` —— 文件本体
- `~/.local/share/Trash/info/<name>.trashinfo` —— 原路径（URL 编码）+ ISO 删除时间

只 move 到 `files/` 是残废的废纸篓：文件管理器里点"还原"会失败。两份都写，`gio trash --list` 才认得、GUI 才能还原。

跨文件系统的路径直接拒绝（不做"复制+删源"的伪废纸篓）——见开头「跨文件系统降级」。

## 无头环境

没有 `DISPLAY`/`WAYLAND_DISPLAY` 时（SSH 上的服务器），跳过 Step 3：不渲染 HTML、不起服务，直接在对话里给完整诊断。调用方本来就是 agent，产物应该是对话里的结论，不是一个需要 `scp` 才能看的文件。
