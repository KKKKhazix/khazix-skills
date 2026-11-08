# Linux 数据布局与分级参考

分析 Linux 扫描结果时读这份。讲"东西存在哪、怎么辨认、归哪一级"。

> **适用范围**：路径与分级依据 XDG/FHS，各发行版通用；但清理命令示例以 **Debian/Ubuntu 系** 为主（本 skill 仅在 Ubuntu 26.04 实测），文中已标注 Fedora/Arch 的对应写法。`~/snap`、`/var/lib/snapd` 仅 snap 用户存在；无 snap 的发行版自动跳过。

## 关键目录

| 目录 | 装什么 | 典型分级 |
|---|---|---|
| `~/.cache/*` | 应用/工具缓存（pip、uv、huggingface、浏览器） | 🟢 可自动清 |
| `~/.npm`、`~/.cargo`、`~/.rustup`、`~/.gradle`、`~/.m2`、`~/go/pkg` | 开发缓存/工具链 | 🟢 |
| `~/.local/share/Trash` | 回收站内容（已删待清） | 🟢 清空回收站（需确认） |
| `~/.local/share/*` | 应用数据（flatpak、podman、pnpm、聊天记录） | 🟡 多为用户数据 |
| `~/snap/*` | snap 应用用户数据（含缓存子目录 `~/snap/*/current/.cache`） | 🟡 用户数据，缓存子路径可 🟢 |
| `~/Downloads` 里的 .deb/.iso/.tar.gz | 安装包/镜像残留 | 🟢（确认不用后） |
| `/var/cache/apt` | apt 包缓存（**Debian/Ubuntu**；Fedora 为 `/var/cache/dnf`，Arch 为 `/var/cache/pacman`） | 🟢（Debian/Ubuntu：`sudo apt clean`；Fedora：`sudo dnf clean all`；Arch：`sudo pacman -Sc`，均需 root） |
| `/var/log` | 系统日志 | 🟢 部分可清（`journalctl --vacuum-size`，需 root），一般归蓝色 |
| `/var/lib/snapd/snaps` | snap 旧版本 .snap 文件（**仅装了 snap 的发行版，常见于 Ubuntu**） | 🟢 但需 root（只给命令，不代跑） |
| `/var/lib/docker`、`/var/lib/containers` | 容器镜像/卷 | 🟡 镜像 `docker system df` 看；卷含数据 |
| `/opt`、`/usr/local` | 手装软件 | 🔴 想卸时上灯，给间接释放步骤 |
| `/tmp` | 临时文件（重启可清） | 🟢（注意有程序运行时依赖） |
| 系统文件、apt 源缓存 | 系统 | 不上灯，归蓝色"系统及其他" |

## 辨认"神秘大目录"

- `du` 出来的隐藏目录（`.local`、`.cache` 下 UUID/哈希命名）：`ls` 进一层看内容，按文件类型判断（`.whl`/`.tar` 是缓存，`*.db`/`*.json` 是应用数据）
- `~/go/pkg/mod`、`~/.cargo/registry` 是模块缓存，删了下次重新下载，🟢
- `node_modules` 遍布各项目：属于项目代码的一部分，归 🟡（项目不再用才删），不进 🟢
- 仍只读，别动文件

## 扫描与磁盘口径

- 扫描不跳过挂载点：ZFS 数据集、btrfs 子卷挂在 `/var/lib`、`/home` 等处，但用的是同一个池或同一块盘。家目录或 `/var` 下若挂了网络盘、移动硬盘，体积也会算进去，判断前用 `findmnt -T <路径>` 看它属于哪个文件系统。
- 磁盘总览按 ZFS 池或设备合并：主盘是装着 `/` 的那个，其他池和盘列在「其他磁盘」。ZFS 的已用是各数据集自身数据之和，不含快照；快照占用看 `zfs list -t snapshot`（只给命令，不代删）。
- 🔴 项在 Linux 上不给 `app_paths`（打开按钮只允许家目录内），卸载写成包管理器命令：`sudo apt remove <包>`、`sudo snap remove <名>`、`flatpak uninstall <id>`。

## 权限注意

- 普通用户读不了 `/var/lib/docker`、`/root` 等：du 输出空 → 扫描静默跳过。报告 `denied` 里列出来，提示"这部分体量未计入"
- 需要 root 的清理命令（apt clean、journal vacuum）只写进报告命令区让用户自己跑，**绝不代跑 sudo**

## 间接释放（写进 long_term，不上红灯）

- Debian/Ubuntu：`sudo apt autoremove && sudo apt clean`；Fedora：`sudo dnf autoremove && sudo dnf clean all`；Arch：`sudo pacman -Sc && pacman -Qtdq | sudo pacman -Rns -`
- `journalctl --vacuum-size=200M`（通用，需 root）
- snap 旧版本（仅 Ubuntu 等装了 snap 的系统）：`sudo snap list --all | grep disabled` 后 `sudo snap remove <rev>`
- 重启清 `/tmp`、释放部分缓存页
- 大文件归档到外置盘 / NAS / 云盘

## 删除机制

`server.py` 在 Linux 用 `gio trash`（GIO/GLib，GNOME 自带、KDE 通常也装了，入 `~/.local/share/Trash`，可恢复；目标与 Trash 不同文件系统时落在 `$topdir/.Trash-$uid`）；无 gio 时回退 `trash`（trash-cli，最小环境可 `apt install trash-cli` 后使用）；两者都没有则该按钮报错（「直接删除」不受影响）。打开文件夹用 `xdg-open`（freedesktop 标准，各桌面发行版通用）。

**符号链接布局**：不少发行版/用户把 `~/.cache`、`~/.cargo`、`~/.npm`、`~/.rustup` 等做成指向集中缓存目录（如 `~/.dev-cache/*`）的符号链接。清理这类目标时给卡片加 `clear_contents: true`（只清内容、保留目录），否则整目录删除会让链接悬空。
