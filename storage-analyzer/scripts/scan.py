#!/usr/bin/env python3
"""Read-only storage scanner (macOS + Windows + Linux).

Collects disk usage, system info, and per-directory size breakdowns for the
hot spots that typically eat disk, and emits one JSON blob to stdout for Claude
to interpret and classify. Auto-detects the OS and scans the right locations.

STRICTLY READ-ONLY: only sizes/lists/reads metadata. Never creates, moves, or
deletes anything.

Output shape (same on both OSes):
{
  "generated_at", "scan_seconds",
  "system": {os, build, arch, user, home, filesystem,
             disk_total, disk_used, disk_free, purgeable,
             disks: [{name, total, used, free}]},   # all volumes/drives
  "groups": { "<group>": [{name, path, size_kb, size_h}], ... },
  "accounting": {...}   # Linux only — 缺口对账，见 reconcile_linux()
}
"""
import json
import os
import shutil
import sys
import time

HOME = os.path.expanduser("~")


def human(kb):
    """KB number -> human string like '12.3 GB'."""
    n = float(kb) * 1024
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024 or unit == "TB":
            return f"{n:.1f} {unit}" if unit not in ("B", "KB") else f"{int(n)} {unit}"
        n /= 1024


# ======================================================================
# macOS
# ======================================================================
import re
import subprocess


def run(cmd, timeout=180):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout).stdout
    except Exception:
        return ""


def du_kb(path, timeout=180):
    """跑 du -skx，返回 (kb, partial, failed)。

    GNU du 遇到读不到的子目录时会打印【偏小的】小计、往 stderr 刷
    "Permission denied" 并以退出码 1 结束——只取 stdout 就会把一个残缺的
    数字当成完整测量。这里把退出码和 stderr 判读出来，让上层能标 partial。
    超时（慢盘/巨型目录）返回 failed=True，避免该目录静默消失。
    """
    try:
        r = subprocess.run(["du", "-skx", path], capture_output=True,
                           text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return 0, False, True
    except Exception:
        return 0, False, True
    m = re.match(r"\s*(\d+)", r.stdout or "")
    if not m:
        return 0, False, True
    partial = r.returncode != 0 or "denied" in (r.stderr or "").lower()
    return int(m.group(1)), partial, False


def du_children(path, min_kb=51200, limit=40):
    """Size every immediate child of `path` via du, sorted desc.

    `-x` 只阻止 du 在【操作数以下】跨文件系统，操作数本身是挂载点时照样整块算。
    所以还要显式比对子项与父目录的 st_dev：~/data 若是外置盘挂载点，
    du -skx ~/data 仍会返回整块外置盘的体量，把它算进主盘就是错的。
    命中的挂载点单独标记 mountpoint=True 交给上层，不静默丢弃。
    """
    if not os.path.isdir(path):
        return []
    results = []
    try:
        entries = sorted(os.listdir(path))
        parent_dev = os.stat(path).st_dev
    except PermissionError:
        return [{"name": "(permission denied)", "path": path,
                 "size_kb": 0, "size_h": "?", "denied": True}]
    except OSError:
        return []
    for name in entries:
        if name in (".", ".."):
            continue
        child = os.path.join(path, name)
        if os.path.islink(child):
            continue
        try:
            if os.stat(child).st_dev != parent_dev:
                # 子项自身是挂载点：体量属于另一块盘，不计入本盘，
                # 但要留痕——它在 system.disks 里作为独立盘出现。
                results.append({"name": name, "path": child, "size_kb": 0,
                                "size_h": "—", "mountpoint": True})
                continue
        except OSError:
            continue
        kb, partial, failed = du_kb(child, timeout=120)
        if failed or kb < min_kb:
            continue
        item = {"name": name, "path": child, "size_kb": kb, "size_h": human(kb)}
        if partial:
            item["partial"] = True      # 有子目录读不到，实际更大
        results.append(item)
    # 挂载点哨兵 size_kb=0，排序后垫底，会被 [:limit] 截掉——而它恰恰是
    # "这块盘另有乾坤"的唯一线索，且下游要靠它把该路径计入 known。
    # 所以按体量截断只作用于普通条目，哨兵全量保留。
    sentinels = [r for r in results if r.get("mountpoint")]
    normal = [r for r in results if not r.get("mountpoint")]
    normal.sort(key=lambda r: r["size_kb"], reverse=True)
    return normal[:limit] + sentinels

MAC_TARGETS = [
    ("home", HOME, 102400),
    ("library", os.path.join(HOME, "Library"), 51200),
    ("caches", os.path.join(HOME, "Library/Caches"), 51200),
    ("containers", os.path.join(HOME, "Library/Containers"), 51200),
    ("group_containers", os.path.join(HOME, "Library/Group Containers"), 51200),
    ("app_support", os.path.join(HOME, "Library/Application Support"), 51200),
    ("applications", "/Applications", 102400),
    ("downloads", os.path.join(HOME, "Downloads"), 51200),
    ("dev_caches", None, 51200),
]

MAC_DEV_CACHE_PATHS = [
    "~/Library/Caches/pip", "~/Library/Caches/uv", "~/.cache", "~/.cargo",
    "~/.npm", "~/.pnpm-store", "~/.gradle", "~/.m2",
    "~/Library/Developer/Xcode/DerivedData", "~/Library/Developer/CoreSimulator",
    "~/Library/Developer/Xcode/iOS DeviceSupport", "~/Library/pnpm",
    "~/go/pkg", "~/.docker",
]


def dev_caches_macos():
    results = []
    for p in MAC_DEV_CACHE_PATHS:
        path = os.path.expanduser(p)
        if not os.path.isdir(path):
            continue
        kb, partial, failed = du_kb(path, timeout=180)
        if failed or kb < 51200:
            continue
        item = {"name": os.path.basename(path.rstrip("/")) or path,
                "path": path, "size_kb": kb, "size_h": human(kb)}
        if partial:
            item["partial"] = True
        results.append(item)
    results.sort(key=lambda r: r["size_kb"], reverse=True)
    return results


def system_info_macos():
    info = {}
    info["os"] = "macOS " + run(["sw_vers", "-productVersion"]).strip()
    info["build"] = run(["sw_vers", "-buildVersion"]).strip()
    arch = run(["uname", "-m"]).strip()
    brand = run(["sysctl", "-n", "machdep.cpu.brand_string"]).strip()
    info["arch"] = (f"Apple Silicon (arm64){' / ' + brand if brand else ''}"
                    if arch == "arm64" else f"{arch}{' / ' + brand if brand else ''}")
    info["user"] = os.environ.get("USER", "") or run(["whoami"]).strip()
    info["home"] = HOME
    total, used, free = "?", "?", "?"
    try:
        t, u, f = shutil.disk_usage("/")
        total, used, free = human(t // 1024), human(u // 1024), human(f // 1024)
    except Exception:
        pass
    info["disk_total"], info["disk_used"], info["disk_free"] = total, used, free
    dinfo = run(["diskutil", "info", "/"])
    fs = re.search(r"File System Personality:\s*(.+)", dinfo)
    info["filesystem"] = fs.group(1).strip() if fs else "APFS"
    pm = re.search(r"Purgeable Space:\s*([\d.,]+ \w+)", dinfo)
    info["purgeable"] = pm.group(1).strip() if pm else ""
    info["disk_name"] = "Macintosh HD"
    info["disks"] = [{"name": "Macintosh HD", "total": total, "used": used, "free": free}]
    return info


def scan_macos():
    system = system_info_macos()
    groups = {}
    for key, path, floor in MAC_TARGETS:
        groups[key] = dev_caches_macos() if key == "dev_caches" else du_children(path, min_kb=floor)
    return system, groups


# ======================================================================
# Windows  (UNTESTED on this build — stdlib only: os, shutil, ctypes)
# ======================================================================
def dir_size_bytes(path):
    """Recursive size in bytes via os.scandir. Skips symlinks and unreadable."""
    total = 0
    try:
        with os.scandir(path) as it:
            for e in it:
                try:
                    if e.is_symlink():
                        continue
                    if e.is_file(follow_symlinks=False):
                        total += e.stat(follow_symlinks=False).st_size
                    elif e.is_dir(follow_symlinks=False):
                        total += dir_size_bytes(e.path)
                except (PermissionError, OSError):
                    continue
    except (PermissionError, OSError):
        pass
    return total


def scandir_children(path, min_kb=51200, limit=40):
    """Size every immediate child of `path` via os.scandir. Windows."""
    if not path or not os.path.isdir(path):
        return []
    results = []
    try:
        entries = sorted(os.listdir(path))
    except PermissionError:
        return [{"name": "(permission denied)", "path": path,
                 "size_kb": 0, "size_h": "?", "denied": True}]
    for name in entries:
        child = os.path.join(path, name)
        if os.path.islink(child):
            continue
        try:
            kb = (os.path.getsize(child) if os.path.isfile(child)
                  else dir_size_bytes(child)) // 1024
        except (PermissionError, OSError):
            continue
        if kb < min_kb:
            continue
        results.append({"name": name, "path": child, "size_kb": kb, "size_h": human(kb)})
    results.sort(key=lambda r: r["size_kb"], reverse=True)
    return results[:limit]


def list_drives_windows():
    drives = []
    import string
    for letter in string.ascii_uppercase:
        root = f"{letter}:\\"
        if os.path.exists(root):
            try:
                t, u, f = shutil.disk_usage(root)
                drives.append({"name": root, "total": human(t // 1024),
                               "used": human(u // 1024), "free": human(f // 1024)})
            except Exception:
                continue
    return drives


def system_info_windows():
    import platform
    info = {}
    info["os"] = platform.system() + " " + platform.release()
    info["build"] = platform.version()
    info["arch"] = os.environ.get("PROCESSOR_ARCHITECTURE", platform.machine())
    info["user"] = os.environ.get("USERNAME", "")
    info["home"] = os.environ.get("USERPROFILE", HOME)
    sysdrive = os.environ.get("SystemDrive", "C:") + "\\"
    total, used, free = "?", "?", "?"
    try:
        t, u, f = shutil.disk_usage(sysdrive)
        total, used, free = human(t // 1024), human(u // 1024), human(f // 1024)
    except Exception:
        pass
    info["disk_total"], info["disk_used"], info["disk_free"] = total, used, free
    info["filesystem"] = "NTFS"
    info["purgeable"] = ""
    info["disk_name"] = sysdrive
    info["disks"] = list_drives_windows()
    return info


def scan_windows():
    profile = os.environ.get("USERPROFILE", HOME)
    local = os.environ.get("LOCALAPPDATA", os.path.join(profile, "AppData", "Local"))
    roaming = os.environ.get("APPDATA", os.path.join(profile, "AppData", "Roaming"))
    targets = [
        ("user_profile", profile, 102400),
        ("appdata_local", local, 51200),
        ("appdata_roaming", roaming, 51200),
        ("temp", os.environ.get("TEMP", os.path.join(local, "Temp")), 51200),
        ("downloads", os.path.join(profile, "Downloads"), 51200),
        ("program_files", os.environ.get("ProgramFiles", r"C:\Program Files"), 102400),
        ("program_files_x86", os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"), 102400),
    ]
    groups = {}
    for key, path, floor in targets:
        groups[key] = scandir_children(path, min_kb=floor)

    dev_paths = [
        os.path.join(profile, ".cache"), os.path.join(profile, ".npm"),
        os.path.join(profile, ".gradle"), os.path.join(profile, ".m2"),
        os.path.join(profile, ".nuget", "packages"), os.path.join(profile, ".cargo"),
        os.path.join(local, "pip", "Cache"), os.path.join(local, "Yarn"),
        os.path.join(local, "uv"), os.path.join(local, "ms-playwright"),
        os.path.join(local, "go-build"),
    ]
    dev = []
    for path in dev_paths:
        if not os.path.isdir(path):
            continue
        try:
            kb = dir_size_bytes(path) // 1024
        except (PermissionError, OSError):
            continue
        if kb < 51200:
            continue
        dev.append({"name": os.path.basename(path.rstrip("\\/")) or path,
                    "path": path, "size_kb": kb, "size_h": human(kb)})
    dev.sort(key=lambda r: r["size_kb"], reverse=True)
    groups["dev_caches"] = dev
    return system_info_windows(), groups


# ======================================================================
# Linux  (stdlib + coreutils: du / df / lsblk-free)
#
# 三个 Linux 独有的设计约束，改代码前先读：
#
# 1. 缺口对账 (reconcile)。macOS 上 du 读不到会报错，能标 denied；Linux 上
#    du 对 root 目录是【静默低估】——把读不到的算作 0 还返回成功。/var/lib/docker
#    动辄几十 G 却完全不出现在结果里，报告会理直气壮地指错大户。所以扫完必须拿
#    df 的已用减去已归类之和，把差额显式报出来。
# 2. 兜底下钻 (uncategorized)。固定目标表列不全各发行版的目录（nix / srv /
#    pacman cache …），所以对 $HOME 和 /var 各做一层通用下钻，捞出表外的大目录。
#    与对账是同一件事的两面：对账说"差了 200G"，下钻说"在哪"。
# 3. sudo 项 = 只读展示范本。/var 下的大户多为 root 所有，清理要 sudo。这些项
#    照常上报、给命令，但 needs_sudo=True，报告端一律不给 trash_paths ——
#    一键删除通道对它们物理关闭。
# ======================================================================
LINUX_TARGETS = [
    ("home", HOME, 102400),
    ("cache", os.path.join(HOME, ".cache"), 51200),
    ("local_share", os.path.join(HOME, ".local/share"), 51200),
    ("config", os.path.join(HOME, ".config"), 51200),
    ("downloads", os.path.join(HOME, "Downloads"), 51200),
    ("flatpak_apps", os.path.join(HOME, ".var/app"), 51200),
    ("snap_home", os.path.join(HOME, "snap"), 51200),
    ("opt", "/opt", 102400),
    ("usr_local", "/usr/local", 102400),
    ("dev_caches", None, 51200),
]

LINUX_DEV_CACHE_PATHS = [
    "~/.cache/pip", "~/.cache/uv", "~/.cache/huggingface", "~/.cache/torch",
    "~/.cache/ms-playwright", "~/.cache/yarn", "~/.cache/go-build",
    "~/.npm", "~/.pnpm-store", "~/.cargo", "~/.gradle", "~/.m2", "~/.nuget",
    "~/go/pkg", "~/.conda/pkgs", "~/anaconda3/pkgs", "~/miniconda3/pkgs",
    "~/.local/share/virtualenvs", "~/.local/share/containers",
    "~/.local/share/Trash", "~/.docker", "~/.rustup", "~/.deno", "~/.bun",
]

# 需要 sudo 才能看/清的系统路径。只探测、只给命令，永不进删除白名单。
LINUX_SUDO_TARGETS = [
    ("/var/lib/docker", "docker system df / docker system prune -a"),
    ("/var/lib/containers", "podman system prune -a"),
    ("/var/log", "sudo journalctl --vacuum-size=200M"),
    ("/var/cache/apt/archives", "sudo apt clean"),
    ("/var/cache/pacman/pkg", "sudo pacman -Sc"),
    ("/var/cache/dnf", "sudo dnf clean all"),
    ("/var/lib/snapd/snaps", "sudo snap set system refresh.retain=2"),
    ("/var/tmp", "sudo systemd-tmpfiles --clean"),
    ("/nix/store", "nix-collect-garbage -d"),
]

# df 里要滤掉的伪文件系统：内存盘、snap 的 squashfs 环回、内核接口、网络盘。
# 注意 overlay / zfs 不在此列：容器根和 ZFS 根是合法的真实根文件系统，
# 滤掉会导致 root_used_kb 取不到值（见 list_mounts_linux 的 source 放行规则）。
NOISE_FSTYPES = {
    "tmpfs", "devtmpfs", "squashfs", "efivarfs", "devpts", "proc",
    "sysfs", "cgroup", "cgroup2", "securityfs", "pstore", "bpf", "configfs",
    "debugfs", "tracefs", "fusectl", "ramfs", "autofs", "binfmt_misc",
    "hugetlbfs", "mqueue", "nsfs", "fuse.gvfsd-fuse", "fuse.portal",
    "nfs", "nfs4", "cifs", "smbfs", "sshfs", "fuse.sshfs", "iso9660",
}

# 无设备节点但合法的真实文件系统。ZFS 的 source 是 pool 名（如 rpool/ROOT），
# overlay 容器根的 source 就是字面量 "overlay"，两者都不以 /dev/ 开头，
# 只按 /dev/ 前缀放行会把它们整个漏掉、进而让对账拿不到根盘已用量。
DEVLESS_FSTYPES = {"zfs", "btrfs", "overlay", "ext4", "xfs"}


def list_mounts_linux():
    """本地真实文件系统列表（滤掉 tmpfs / squashfs / 网络盘等噪声）。

    Q7：主盘照旧做分组扫描，其他挂载点只报容量——模板已支持多盘列表。
    每项带 st_dev，供 reconcile_linux 按文件系统归属做对账。
    """
    out = run(["df", "-PT", "-k"])
    mounts, seen_src = [], set()
    for line in out.splitlines()[1:]:
        parts = line.split(None, 6)
        if len(parts) < 7:
            continue
        source, fstype, total_kb, used_kb, avail_kb, _pct, target = parts
        if fstype in NOISE_FSTYPES:
            continue
        if not source.startswith("/dev/") and fstype not in DEVLESS_FSTYPES:
            continue
        if source in seen_src:      # bind mount / 同一块盘挂多处，只算一次
            continue
        seen_src.add(source)
        try:
            t, u, a = int(total_kb), int(used_kb), int(avail_kb)
        except ValueError:
            continue
        if t <= 0:
            continue
        try:
            st_dev = os.stat(target).st_dev
        except OSError:
            st_dev = None
        mounts.append({"name": target, "source": source, "fstype": fstype,
                       "total": human(t), "used": human(u), "free": human(a),
                       "total_kb": t, "used_kb": u, "st_dev": st_dev})
    mounts.sort(key=lambda m: m["total_kb"], reverse=True)
    return mounts


def dev_caches_linux():
    results = []
    for p in LINUX_DEV_CACHE_PATHS:
        path = os.path.expanduser(p)
        if not os.path.isdir(path):
            continue
        kb, partial, failed = du_kb(path, timeout=180)
        if failed or kb < 51200:
            continue
        item = {"name": os.path.basename(path.rstrip("/")) or path,
                "path": path, "size_kb": kb, "size_h": human(kb)}
        if partial:
            item["partial"] = True
        results.append(item)
    results.sort(key=lambda r: r["size_kb"], reverse=True)
    return results


def sudo_targets_linux():
    """探测 root 拥有的系统大户。读不到就标 denied + 给 sudo 查看命令。"""
    results = []
    for path, hint in LINUX_SUDO_TARGETS:
        if not os.path.isdir(path):
            continue
        readable = os.access(path, os.R_OK | os.X_OK)
        # cleanup_hint 只作为给 agent 的提示，清理命令的权威版本在
        # references/linux.md 的表里，不在这里重复维护第二份。
        item = {"name": path, "path": path, "needs_sudo": True,
                "cleanup_hint": hint}
        if readable:
            kb, partial, failed = du_kb(path, timeout=180)
            item.update(size_kb=kb, size_h=human(kb) if not failed else "?")
            # 可读不代表读全了：子目录仍可能是 0700 root。du 的退出码/stderr
            # 能确认这一点，确认不了时也保守标 partial（宁可多提示不可漏报）。
            item["partial"] = True
            if failed:
                item["denied"] = True
        else:
            item.update(size_kb=0, size_h="?", denied=True)
        results.append(item)
    results.sort(key=lambda r: r["size_kb"], reverse=True)
    return results


def uncategorized_linux(known_paths):
    """兜底下钻：$HOME 和 /var 各一层，捞出固定目标表没覆盖到的大目录。"""
    results = []
    for parent, floor in ((HOME, 512000), ("/var", 512000)):
        if not os.path.isdir(parent):
            continue
        try:
            entries = sorted(os.listdir(parent))
        except (PermissionError, OSError):
            continue
        for name in entries:
            child = os.path.join(parent, name)
            if os.path.islink(child) or not os.path.isdir(child):
                continue
            if child in known_paths:
                continue
            if not os.access(child, os.R_OK | os.X_OK):
                continue
            kb, partial, failed = du_kb(child, timeout=180)
            if failed:
                continue
            # 已知子孙的体量要扣掉，但【不能整个跳过 child】：
            # /var/lib/docker 已知时若把 /var/lib 整条略去，/var/lib/postgresql
            # 这样的兄弟目录就被一起埋了。扣减后仍够大才上报，既不重复计数
            # 也不制造扫描盲区。
            known_kids = [k for k in known_paths if k.startswith(child + os.sep)]
            subtracted = False
            if known_kids:
                # 只扣顶层的已知子孙，避免嵌套的祖孙被扣两次
                tops = [k for k in known_kids
                        if not any(k.startswith(o + os.sep) for o in known_kids)]
                child_dev = None
                try:
                    child_dev = os.stat(child).st_dev
                except OSError:
                    pass
                for k in tops:
                    # du -x 已经不会跨挂载点，若子孙在别的文件系统上，
                    # child 的体量里本来就不含它，再扣一次会让本盘少算。
                    try:
                        if child_dev is not None and os.stat(k).st_dev != child_dev:
                            continue
                    except OSError:
                        continue
                    kid_kb, _, kid_failed = du_kb(k, timeout=180)
                    if kid_failed:
                        continue        # 量不到就不扣，也就不能声称已扣
                    kb = max(0, kb - kid_kb)
                    subtracted = True
            if kb < floor:
                continue
            item = {"name": name, "path": child,
                    "size_kb": kb, "size_h": human(kb)}
            if subtracted:
                item["excludes_known"] = True   # 体量已扣除单列的已知子目录
            if partial:
                item["partial"] = True
            results.append(item)
    results.sort(key=lambda r: r["size_kb"], reverse=True)
    return results


def reconcile_linux(groups, mounts):
    """缺口对账：按【每个文件系统】各自算 df 已用 − 已归类之和。

    必须逐盘算，不能把所有条目加总后只跟 / 比：Linux 上 /home 独立分区极常见，
    若 / 用 20 GB 而 /home 用 100 GB，合并对账会凭空捏造 80 GB 的"重叠"。
    归属靠 st_dev（不是路径前缀）——挂载点可以嵌套在任意深度。

    差额里混着系统本体（/usr、/lib 等本来就该算蓝色），也混着 du 读不到的
    root 目录。两者不可分，所以如实报数 + 报告端注明"可能藏有大户"。
    """
    # 各组之间路径互相嵌套（home 组含 .cache，uncategorized 的 /var/lib 含
    # sudo_targets 的 /var/lib/snapd/snaps）。先收集再只保留【最顶层】路径，
    # 单向前缀过滤挡得住子项、挡不住后来居上的父项。
    #
    # excludes_known 的条目例外：它的体量已经扣掉了单列的已知子孙，
    # 与子孙条目【不重叠】。若按普通规则让它吞掉子孙，两边都会少算。
    cand, exclusive = {}, set()
    for items in groups.values():
        for it in items:
            rp, kb = it.get("path"), it.get("size_kb") or 0
            if rp and kb:
                cand[rp] = max(cand.get(rp, 0), kb)
                if it.get("excludes_known"):
                    exclusive.add(rp)
    tops = {rp: kb for rp, kb in cand.items()
            if not any(rp.startswith(o + os.sep) and o not in exclusive
                       for o in cand)}

    # 按 st_dev 把每个顶层条目归到它所在的文件系统。du -x 保证条目体量不跨盘。
    by_dev, unresolved_kb = {}, 0
    for rp, kb in tops.items():
        try:
            dev = os.stat(rp).st_dev
        except OSError:
            unresolved_kb += kb          # 扫描后被删/权限变化，无法归属
            continue
        by_dev[dev] = by_dev.get(dev, 0) + kb

    per_fs, total_gap, total_overlap = [], 0, 0
    seen_dev = set()
    for m in mounts:
        dev = m.get("st_dev")
        if dev is None:
            continue
        if dev in seen_dev:
            # 同一 st_dev 的第二行（source 别名 / bind mount 漏网）：
            # 体量已归给第一行，这里再算一次会把它整盘报成 gap。
            continue
        seen_dev.add(dev)
        counted = by_dev.pop(dev, 0)
        diff = m["used_kb"] - counted
        entry = {
            "mount": m["name"], "fstype": m["fstype"],
            "used_kb": m["used_kb"], "used_h": m["used"],
            "categorized_kb": counted, "categorized_h": human(counted),
            "gap_kb": max(0, diff), "gap_h": human(max(0, diff)),
        }
        if diff < 0:
            entry["overlap_kb"] = -diff
            entry["overlap_h"] = human(-diff)
            total_overlap += -diff
        else:
            total_gap += diff
        per_fs.append(entry)

    # 归到了某个 st_dev 但该盘没出现在 mounts 里（被 NOISE_FSTYPES 滤掉的
    # 挂载点，如落在 tmpfs 上的路径）——如实单列，不要静默并进别处。
    unmatched_kb = sum(by_dev.values()) + unresolved_kb

    root = next((e for e in per_fs if e["mount"] == "/"), None)
    result = {
        "per_filesystem": per_fs,
        "unmatched_kb": unmatched_kb, "unmatched_h": human(unmatched_kb),
        "gap_kb": total_gap, "gap_h": human(total_gap),
        "note": "差额 = 系统本体（/usr、/lib 等）+ 权限不足未能读取的目录。"
                "Linux 上 du 对 root 目录是静默低估，此处可能藏有大户，"
                "报告里应归入蓝色「系统及其他」并提示用户用 sudo 核实。"
                "对账按文件系统分别计算，per_filesystem 里每项独立成立。",
    }
    if root:        # 兼容旧字段名，报告端主要看根盘
        result["root_used_kb"] = root["used_kb"]
        result["root_used_h"] = root["used_h"]
        result["categorized_kb"] = root["categorized_kb"]
        result["categorized_h"] = root["categorized_h"]
    if total_overlap:
        result["overlap_kb"] = total_overlap
        result["overlap_h"] = human(total_overlap)
        result["note"] += (
            " 注意：有文件系统的合计超出其实际已用，共 %s。"
            "常见成因是硬链接缓存（uv / pnpm / conda 等）在多次 du 中被重复计数；"
            "文件系统压缩、reflink/CoW 共享、稀疏文件也会造成同向偏差。"
            "报告里对相关项的「可释放空间」应说明实际释放量可能更小。"
            % result["overlap_h"])
    return result


def system_info_linux(mounts):
    """系统与磁盘信息。mounts 由调用方传入，不在这里重复探测——
    避免把对账所需的输入藏进展示用的 dict 再 pop 出来（隐藏状态 + false-zero）。
    """
    info = {}
    pretty = ""
    try:
        with open("/etc/os-release", encoding="utf-8") as f:
            for line in f:
                if line.startswith("PRETTY_NAME="):
                    pretty = line.split("=", 1)[1].strip().strip('"')
                    break
    except OSError:
        pass
    info["os"] = pretty or ("Linux " + run(["uname", "-r"]).strip())
    info["build"] = run(["uname", "-r"]).strip()
    arch = run(["uname", "-m"]).strip()
    model = ""
    try:
        with open("/proc/cpuinfo", encoding="utf-8") as f:
            for line in f:
                if line.startswith("model name"):
                    model = line.split(":", 1)[1].strip()
                    break
    except OSError:
        pass
    info["arch"] = f"{arch}{' / ' + model if model else ''}"
    info["user"] = os.environ.get("USER", "") or run(["whoami"]).strip()
    info["home"] = HOME
    total, used, free = "?", "?", "?"
    try:
        t, u, f = shutil.disk_usage("/")
        total, used, free = human(t // 1024), human(u // 1024), human(f // 1024)
    except Exception:
        pass
    info["disk_total"], info["disk_used"], info["disk_free"] = total, used, free
    root = next((m for m in mounts if m["name"] == "/"), None)
    info["filesystem"] = root["fstype"] if root else "unknown"
    info["purgeable"] = ""          # Linux 无"可清除空间"概念
    info["disk_name"] = (root["source"] + " (/)") if root else "/"
    info["disks"] = [{k: m[k] for k in ("name", "total", "used", "free")}
                     for m in mounts]
    return info


def scan_linux():
    mounts = list_mounts_linux()
    system = system_info_linux(mounts)
    groups = {}
    known = set()
    for key, path, floor in LINUX_TARGETS:
        if key == "dev_caches":
            groups[key] = dev_caches_linux()
        else:
            groups[key] = du_children(path, min_kb=floor)
            if path:
                known.add(path)
    for items in groups.values():
        for it in items:
            if it.get("path"):
                known.add(it["path"])
    # sudo_targets 先于 uncategorized，且把它的路径也计入 known：
    # 否则 /var/log 会同时以"特权/可能不全"和"未分类"两种身份出现，
    # 报告端可能列两遍，或挑中没有 needs_sudo 标记的那份。
    groups["sudo_targets"] = sudo_targets_linux()
    for it in groups["sudo_targets"]:
        if it.get("path"):
            known.add(it["path"])
    groups["uncategorized"] = uncategorized_linux(known)
    accounting = reconcile_linux(groups, mounts)
    return system, groups, accounting


# ======================================================================
def main():
    started = time.time()
    accounting = None
    if sys.platform == "darwin":
        system, groups = scan_macos()
    elif sys.platform.startswith("win"):
        system, groups = scan_windows()
    elif sys.platform.startswith("linux"):
        system, groups, accounting = scan_linux()
    else:
        print(json.dumps({"error": "unsupported_platform", "platform": sys.platform,
                          "message": "scan.py supports macOS, Windows and Linux."},
                         ensure_ascii=False))
        return
    data = {
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "system": system,
        "groups": groups,
        "scan_seconds": round(time.time() - started, 1),
    }
    if accounting:
        data["accounting"] = accounting
    print(json.dumps(data, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
