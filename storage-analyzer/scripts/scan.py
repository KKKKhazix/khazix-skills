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
  "groups": { "<group>": [{name, path, size_kb, size_h}], ... }
}
"""
import json
import os
import shutil
import stat
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


def du_children(path, min_kb=51200, limit=40, same_volume=True):
    """Size every immediate child of `path` via du, sorted desc (macOS, Linux).

    same_volume=True skips mount points and nested mounts (macOS: another
    volume is another disk). Linux passes False: ZFS datasets and btrfs
    subvolumes are separate mounts that still use the same pool or disk.
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
    for name in entries:
        if name in (".", ".."):
            continue
        child = os.path.join(path, name)
        if os.path.islink(child):
            continue
        try:
            if same_volume and os.lstat(child).st_dev != parent_dev:
                # A mount point (e.g. Xcode's FSKit CoreDevice/DeviceFS): its
                # contents live on another volume, not on this disk.
                SCAN_ERRORS.add("已跳过挂载点（属于另一个卷，不占本盘空间）：" + child)
                continue
        except OSError:
            continue
        # -x: stay on this volume, so mounts nested deeper are not counted.
        out = run(["du", "-skx" if same_volume else "-sk", child], timeout=120)
        m = re.match(r"\s*(\d+)", out)
        if not m:
            continue
        kb = int(m.group(1))
        if kb < min_kb:
            continue
        results.append({"name": name, "path": child, "size_kb": kb, "size_h": human(kb)})
    results.sort(key=lambda r: r["size_kb"], reverse=True)
    return results[:limit]


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
        try:
            if os.stat(path).st_dev != os.stat(os.path.dirname(path.rstrip("/"))).st_dev:
                SCAN_ERRORS.add("已跳过挂载点（属于另一个卷，不占本盘空间）：" + path)
                continue
        except OSError:
            continue
        out = run(["du", "-skx", path], timeout=180)
        m = re.match(r"\s*(\d+)", out)
        if not m:
            continue
        kb = int(m.group(1))
        if kb < 51200:
            continue
        results.append({"name": os.path.basename(path.rstrip("/")) or path,
                        "path": path, "size_kb": kb, "size_h": human(kb)})
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
# Windows  (stdlib only: os, shutil, ctypes)
# ======================================================================
def is_link(st):
    return stat.S_ISLNK(st.st_mode) or getattr(st, "st_reparse_tag", 0) in (0xA0000003, 0xA000000C)


def dir_size_bytes(path, sizes=None):
    """Postorder traversal: no recursion, no junctions, reuse totals within one scan."""
    if sizes is None:
        sizes = {}
    path = os.path.abspath(path)
    stack = [(path, False)]
    children = {}
    while stack:
        current, visited = stack.pop()
        if current in sizes:
            continue
        if visited:
            size, subdirs = children.pop(current)
            sizes[current] = size + sum(sizes[p] for p in subdirs)
            continue
        size, subdirs = 0, []
        try:
            with os.scandir(current) as entries:
                for entry in entries:
                    try:
                        st = entry.stat(follow_symlinks=False)
                        if is_link(st):
                            continue
                        if stat.S_ISDIR(st.st_mode):
                            subdirs.append(entry.path)
                        elif stat.S_ISREG(st.st_mode):
                            size += st.st_size
                    except OSError as e:
                        SCAN_ERRORS.add(str(e))
        except OSError as e:
            SCAN_ERRORS.add(str(e))
        children[current] = (size, subdirs)
        stack.append((current, True))
        stack.extend((child, False) for child in subdirs if child not in sizes)
    return sizes[path]


SCAN_ERRORS = set()


def scandir_children(path, min_kb=51200, limit=40, sizes=None):
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
        try:
            if is_link(os.lstat(child)):
                continue
            kb = (os.path.getsize(child) if os.path.isfile(child)
                  else dir_size_bytes(child, sizes)) // 1024
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
    sizes = {}
    for key, path, floor in targets:
        groups[key] = scandir_children(path, min_kb=floor, sizes=sizes)

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
            kb = dir_size_bytes(path, sizes) // 1024
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
# Linux (GNOME/Debian-family first; tested on Ubuntu 26.04 + ZFS)
# ======================================================================
def system_info_linux():
    import platform as _platform
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
    info["os"] = pretty or ("Linux " + _platform.release())
    info["build"] = _platform.release()
    arch = _platform.machine()
    brand = ""
    try:
        with open("/proc/cpuinfo", encoding="utf-8") as f:
            for line in f:
                if line.startswith("model name"):
                    brand = line.split(":", 1)[1].strip()
                    break
    except OSError:
        pass
    info["arch"] = f"{arch}{' / ' + brand if brand else ''}"
    info["user"] = os.environ.get("USER", "") or run(["whoami"]).strip()
    info["home"] = HOME
    disks, root = list_disks_linux()
    main_disk = next((d for d in disks if d["name"] == root), None)
    if main_disk:
        sizes = (main_disk["total"], main_disk["used"], main_disk["free"])
    else:
        # df unavailable/unparseable (e.g. BusyBox): fall back to the root filesystem.
        try:
            sizes = shutil.disk_usage("/")
        except OSError:
            sizes = None
    info["disk_total"], info["disk_used"], info["disk_free"] = (
        (human(v // 1024) for v in sizes) if sizes else ("?", "?", "?"))
    info["disks"] = [{"name": d["name"], "total": human(d["total"] // 1024),
                      "used": human(d["used"] // 1024),
                      "free": human(d["free"] // 1024)} for d in disks]
    fs = run(["findmnt", "-no", "FSTYPE", "/"]).strip()
    info["filesystem"] = fs or "unknown"
    info["purgeable"] = ""
    info["disk_name"] = root or "/"
    return info


def list_disks_linux():
    """One entry per real filesystem from GNU df (bytes), and the one holding /.

    - ZFS: datasets of a pool share its free space, and df Used is only what
      each dataset references itself (child datasets are separate mounts), so a
      pool's used is the sum over its mounted datasets and free counts once.
      Snapshots are not included.
    - A source listed more than once (btrfs subvolumes, bind mounts) is one
      filesystem and is counted once.
    Mounts under 10 MB used are noise. GNU df only; BusyBox yields nothing.
    """
    out = run(["df", "-B1", "--output=source,fstype,size,used,avail,target",
               "-x", "tmpfs", "-x", "devtmpfs", "-x", "squashfs", "-x", "overlay"])
    disks, root = {}, ""
    for line in out.splitlines()[1:]:
        parts = line.split(None, 5)
        if len(parts) < 6:
            continue
        src, fstype, target = parts[0], parts[1], parts[5]
        try:
            size, used, avail = (int(p) for p in parts[2:5])
        except ValueError:
            continue
        name = src.split("/")[0] if fstype == "zfs" else src
        if target == "/":
            root = name
        disk = disks.get(name)
        if disk is None:
            disks[name] = {"name": name, "used": used, "free": avail,
                           "total": used + avail if fstype == "zfs" else size}
        elif fstype == "zfs":
            disk["used"] += used
            disk["total"] = disk["used"] + disk["free"]
    kept = [d for d in disks.values() if d["used"] >= 10 * 1024 * 1024 or d["name"] == root]
    kept.sort(key=lambda d: d["used"], reverse=True)
    return kept, root


LINUX_TARGETS = [
    ("home", HOME, 102400),
    ("cache", os.path.join(HOME, ".cache"), 51200),
    ("local_share", os.path.join(HOME, ".local/share"), 51200),
    ("downloads", os.path.join(HOME, "Downloads"), 51200),
    ("system", "/var", 102400),
    ("tmp", "/tmp", 51200),
    ("dev_caches", None, 51200),
]

LINUX_DEV_CACHE_PATHS = [
    "~/.cache/pip", "~/.cache/uv", "~/.cache/huggingface",
    "~/.cache/ms-playwright", "~/.cache/Yarn", "~/.cache/google-cloud",
    "~/.cargo", "~/.rustup", "~/.npm", "~/.pnpm-store",
    "~/.gradle", "~/.m2", "~/.nuget/packages",
    "~/go/pkg", "~/.docker", "~/.conda", "~/.ollama",
    "~/.local/share/uv", "~/.local/share/pnpm", "~/.local/share/containers",
    "~/.local/share/Trash", "~/.vscode/extensions",
    "~/snap", "~/.cache",
]


def dev_caches_linux():
    results = []
    for p in LINUX_DEV_CACHE_PATHS:
        path = os.path.expanduser(p)
        if not os.path.isdir(path) or os.path.islink(path):
            continue
        out = run(["du", "-sk", path], timeout=180)
        m = re.match(r"\s*(\d+)", out)
        if not m:
            continue
        kb = int(m.group(1))
        if kb < 51200:
            continue
        results.append({"name": os.path.basename(path.rstrip("/")) or path,
                        "path": path, "size_kb": kb, "size_h": human(kb)})
    seen, dedup = set(), []
    for r in results:
        if r["path"] in seen:
            continue
        seen.add(r["path"])
        dedup.append(r)
    dedup.sort(key=lambda r: r["size_kb"], reverse=True)
    return dedup


def scan_linux():
    system = system_info_linux()
    groups = {}
    for key, path, floor in LINUX_TARGETS:
        groups[key] = (dev_caches_linux() if key == "dev_caches"
                       else du_children(path, min_kb=floor, same_volume=False))
    return system, groups


# ======================================================================
def main():
    sys.stdout.reconfigure(encoding="utf-8")
    SCAN_ERRORS.clear()
    started = time.time()
    if sys.platform == "darwin":
        system, groups = scan_macos()
    elif sys.platform.startswith("win"):
        system, groups = scan_windows()
    elif sys.platform.startswith("linux"):
        system, groups = scan_linux()
    else:
        print(json.dumps({"error": "unsupported_platform", "platform": sys.platform,
                          "message": "scan.py supports macOS, Windows and Linux only."},
                         ensure_ascii=False))
        return
    data = {
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "system": system,
        "groups": groups,
        "scan_seconds": round(time.time() - started, 1),
        "warnings": sorted(SCAN_ERRORS),
    }
    print(json.dumps(data, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
