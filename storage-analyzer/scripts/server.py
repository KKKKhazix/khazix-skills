#!/usr/bin/env python3
"""Serve the storage report with a guarded one-click delete API (macOS + Windows).

Starts on 127.0.0.1 + a random port + a random per-session token, serves the
interactive report, and exposes POST /action to move green-tier paths to Trash
or delete them outright. Stop with Ctrl+C.

Usage:
    server.py <analysis.json>

SAFETY MODEL — read before changing:
- Allowlist: only paths listed in this report's green items `trash_paths` are
  accepted. Every request path is realpath-resolved and must be in the allowlist
  AND under $HOME. Anything else is rejected. This is the core guard — the
  endpoint cannot be used to delete arbitrary files.
- Bound to 127.0.0.1 only; every POST requires the session token; Host header
  must be 127.0.0.1 (blocks DNS-rebinding from a malicious page).
- Two modes: "trash" (Finder -> Trash, reversible) and "rm" (immediate,
  irreversible). The browser confirms each action before sending.
"""
import json
import os
import secrets
import shutil
import stat
import subprocess
import sys
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(HERE, "..", "assets", "report_template.html")
HOME = os.path.realpath(os.path.expanduser("~"))
TOKEN = secrets.token_urlsafe(24)

DATA = {}
TPL = ""
RM_ALLOW = set()
TRASH_ALLOW = set()
OPEN_ALLOW = set()


def expand(p):
    return os.path.realpath(os.path.expanduser(p))


def load(src):
    with open(src, encoding="utf-8") as f:
        data = json.load(f)
    with open(TEMPLATE, encoding="utf-8") as f:
        tpl = f.read()
    # 三套白名单，权限从严到宽：
    #   rm    = 仅绿灯 trash_paths（可直接删的纯缓存）
    #   trash = 绿灯 + 橙灯 trash_paths（橙灯只准移废纸篓，不准直接删）
    #   open  = trash 全集 + 橙灯 path + 红灯 app_paths（仅"在文件管理器打开"，非破坏性）
    rm_allow, trash_allow, open_allow = set(), set(), set()

    def destructive_ok(item, rp):
        """破坏性白名单的准入判定——由代码强制，不靠 SKILL.md 的约定。

        needs_sudo 项（/var/log、apt 缓存等 root 大户）即使 agent 误给了
        trash_paths 也不得进入 rm/trash：它们要么删不动、要么需要提权，
        后台代删都不稳妥。

        只收 $HOME 的【严格子孙】：rp == HOME 必须拒绝——一个畸形的绿灯项
        写成 trash_paths: ["~"] 就会让 shutil.rmtree 抹掉整个家目录。
        同样拒绝与废纸篓不同文件系统的路径：那种项 trash 必失败，
        留在白名单里只会让 rm 变成唯一可用按钮，把可逆操作诱导成不可逆的。
        """
        if item.get("needs_sudo"):
            return False
        if not rp.startswith(HOME + os.sep):
            return False
        if _crosses_mount(rp):
            return False        # bind mount 等：路径在 home 内，存储在外面
        return _same_fs_as_trash(rp)

    # 同步净化 data：被拒的路径要从 trash_paths 里剔除，否则页面照样渲染
    # 出删除按钮，点下去必然 403——死按钮比没按钮更糟，用户会以为是故障。
    for it in data.get("green", []):
        kept = []
        for p in (it.get("trash_paths") or []):
            rp = expand(p)
            open_allow.add(rp)
            if destructive_ok(it, rp):
                rm_allow.add(rp); trash_allow.add(rp); kept.append(p)
        if it.get("trash_paths") is not None:
            it["trash_paths"] = kept
    for it in data.get("yellow", []):
        kept = []
        for p in (it.get("trash_paths") or []):
            rp = expand(p)
            open_allow.add(rp)
            if destructive_ok(it, rp):
                trash_allow.add(rp); kept.append(p)
        if it.get("trash_paths") is not None:
            it["trash_paths"] = kept
        if it.get("path"):
            rp = expand(it["path"])
            if os.path.exists(rp):
                open_allow.add(rp)
    # 红灯只允许"打开"（应用本体在 /Applications，删除让用户在访达里自己卸）
    for it in data.get("red", []):
        for p in (it.get("app_paths") or []):
            rp = expand(p)
            if os.path.exists(rp):
                open_allow.add(rp)
    return data, tpl, rm_allow, trash_allow, open_allow


def _mountpoints():
    """当前所有挂载点的绝对路径集合（Linux）。

    st_dev 挡不住【同设备】的 bind mount：把 /srv/data bind 到 ~/cache 之后，
    realpath 仍在 $HOME 内、st_dev 也相同，破坏性操作就能穿透 home 边界删到
    外面去。/proc/self/mountinfo 的第 5 个字段就是挂载点路径，纯标准库、
    一次 split 即可，比 st_dev 更能表达"这里是另一棵树的入口"。
    """
    pts = set()
    try:
        with open("/proc/self/mountinfo", encoding="utf-8") as f:
            for line in f:
                parts = line.split(" ")
                if len(parts) >= 5:
                    pts.add(parts[4].replace("\\040", " ").replace("\\011", "\t"))
    except OSError:
        pass
    return pts


def _crosses_mount(rp):
    """rp 自身或其任一祖先（到 HOME 为止）是否是挂载点。

    命中即拒绝破坏性操作：那意味着这条路径下面挂着另一棵目录树，
    rmtree 会删到 $HOME 之外的真实存储上。
    """
    if not sys.platform.startswith("linux"):
        return False
    pts = _mountpoints()
    if not pts:
        return False            # 读不到 mountinfo 时不误伤，交给其他护栏
    cur = rp
    while cur.startswith(HOME + os.sep):
        if cur in pts:
            return True
        cur = os.path.dirname(cur)
    return False


def has_gui():
    """有没有图形界面。无头（SSH 上的服务器）时不弹浏览器、不开文件管理器。"""
    if sys.platform in ("darwin",) or sys.platform.startswith("win"):
        return True
    return bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))


def move_to_trash(path):
    if sys.platform == "darwin":
        _trash_macos(path)
    elif sys.platform.startswith("win"):
        _trash_windows(path)
    elif sys.platform.startswith("linux"):
        _trash_linux(path)
    else:
        raise OSError("移到废纸篓仅支持 macOS / Windows / Linux")


def _trash_macos(path):
    # osascript Finder delete -> macOS Trash, recoverable. First run may prompt
    # for Finder automation permission. Fall back to ~/.Trash move if it fails.
    script = 'tell application "Finder" to delete (POSIX file %s as alias)' % json.dumps(path)
    r = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    if r.returncode != 0:
        dest = os.path.join(HOME, ".Trash",
                            os.path.basename(path.rstrip("/")) + "." + time.strftime("%H%M%S"))
        shutil.move(path, dest)


def _xdg_trash_dir():
    """home 废纸篓的绝对路径。

    XDG 规范要求 XDG_DATA_HOME 是绝对路径；相对值必须忽略并退回默认位置，
    否则废纸篓会落到进程 cwd 下的某个目录，桌面工具根本找不到。
    """
    base = os.environ.get("XDG_DATA_HOME") or ""
    if not os.path.isabs(base):
        base = os.path.join(HOME, ".local", "share")
    return os.path.join(base, "Trash")


def _same_fs_as_trash(path):
    """path 与 home 废纸篓是否在同一文件系统。

    比对【实际落点】而不是 HOME：XDG_DATA_HOME 可能被指到另一块盘上，
    那时源与 HOME 同盘也照样 rename 失败。取最近的已存在祖先来 stat，
    因为 Trash 目录本身可能还没创建。
    非 Linux 平台无此限制（macOS/Windows 的回收站由系统自己处理跨盘）。
    """
    if not sys.platform.startswith("linux"):
        return True
    dest = _xdg_trash_dir()
    while not os.path.exists(dest):
        parent = os.path.dirname(dest)
        if parent == dest:
            break
        dest = parent
    try:
        return os.stat(path).st_dev == os.stat(dest).st_dev
    except OSError:
        return False


def _trash_linux(path):
    """XDG Trash 规范入废纸篓。三级回退：gio → trash-put → stdlib 手写。

    跨文件系统必须拒绝（Q2 决策）：规范要求写到目标盘自己的 .Trash-$UID，
    而 shutil.move 跨设备会退化成"复制 + 删源"——对一个 97GB 的目录意味着
    先复制 97GB（盘可能都不够），语义上是慢速删除而不是"移到废纸篓"。
    宁可不给按钮，也不做用户以为可逆、实际不可逆的事。
    """
    if not _same_fs_as_trash(path):
        raise OSError("该路径与废纸篓不在同一文件系统上，无法移入；"
                      "请在文件管理器里自行处理")
    for tool in (["gio", "trash", "--"], ["trash-put", "--"]):
        if shutil.which(tool[0]):
            r = subprocess.run(tool + [path], capture_output=True, text=True)
            if r.returncode == 0:
                return
    _trash_xdg_stdlib(path)


def _trash_xdg_stdlib(path):
    """纯标准库实现 XDG Trash：files/ 放本体，info/ 放 .trashinfo。

    两份都要写，文件管理器才认得、才能"还原"——只 move 到 files/ 是残废的
    废纸篓，GUI 里点还原会失败。

    名字冲突用 O_EXCL 原子占位而不是"先查存在再写"：服务跑在
    ThreadingHTTPServer 下，两个同名请求会在检查与写入之间的窗口里选中同一个
    dest_name，后到的 os.rename 直接覆盖先到的本体——用户以为进了废纸篓的
    文件被静默吞掉。O_EXCL 让冲突方拿到 FileExistsError 并顺延到下一个名字。
    """
    trash = _xdg_trash_dir()
    files_dir, info_dir = os.path.join(trash, "files"), os.path.join(trash, "info")
    # 显式 0700：.trashinfo 里存着原始绝对路径，umask 022 下会变成 0644，
    # 多用户机器上等于把用户的目录结构公开给所有人。
    # 但只在【权限位真的有意义】的文件系统上强制：vfat/exfat 挂载的 home
    # 恒为 0777 且 chmod 无效，拿"权限太宽"拒绝它是拿错尺子——那种盘上
    # 根本没有 Unix 权限语义可言，拒绝只会让废纸篓彻底不可用。
    for d in (trash, files_dir, info_dir):
        os.makedirs(d, mode=0o700, exist_ok=True)
        before = stat.S_IMODE(os.stat(d).st_mode)
        chmod_err = None
        try:
            os.chmod(d, 0o700)      # 目录已存在时 makedirs 的 mode 不生效
        except OSError as e:
            chmod_err = e
        after = stat.S_IMODE(os.stat(d).st_mode)
        if after & 0o077:
            if chmod_err is not None:
                # chmod 真的失败了（如目录属于别的用户）——这不是"文件系统
                # 没有权限语义"，而是我们无权收紧它。别人能改名/删除废纸篓
                # 里的东西，不该往里放。
                raise OSError("废纸篓目录 %s 权限为 %o 且无法收紧（%s）；"
                              "已中止操作" % (d, after, chmod_err))
            if after != before:
                # chmod 生效了却仍然过宽 —— 有别的东西在放宽权限，属异常
                raise OSError("废纸篓目录 %s 权限为 %o，对其他用户可见；"
                              "已中止操作（.trashinfo 含原始路径）。"
                              "请手动 chmod 700 后重试" % (d, after))
            # chmod 成功但模式没变：vfat/exfat 这类由挂载选项决定权限的文件
            # 系统。让用户去 chmod 是不可能完成的指令，给出可行方向即可。
            print("提示：废纸篓目录 %s 权限为 %o 且 chmod 无效，"
                  "该文件系统权限由挂载选项决定（如 vfat/exfat 的 umask=/fmask=）。"
                  ".trashinfo 内含原始路径，同机其他用户可读。" % (d, after),
                  file=sys.stderr, flush=True)

    name = os.path.basename(path.rstrip("/")) or "item"
    # 为后缀留出余量：.trashinfo(10) + ".99"(3) 或 ".YYYYmmddHHMMSS.xxxxxx"(22)。
    # 一个合法的 255 字节名字加上 .trashinfo 就会 ENAMETOOLONG，
    # 首个候选直接抛错、连随机兜底都到不了。按字节截断（中文名不能按字符）。
    try:
        name_max = os.pathconf(info_dir, "PC_NAME_MAX")
    except (OSError, ValueError, AttributeError):
        name_max = 255
    budget = max(16, name_max - len(".trashinfo") - 24)
    nb = name.encode("utf-8", "surrogateescape")
    if len(nb) > budget:
        name = nb[:budget].decode("utf-8", "ignore") or "item"

    info = ("[Trash Info]\nPath=%s\nDeletionDate=%s\n"
            % (_url_quote(os.path.abspath(path)), time.strftime("%Y-%m-%dT%H:%M:%S")))

    # 先按 name、name.1 … 顺延（贴合桌面工具的命名习惯），仍冲突就退到
    # 时间戳+随机后缀。纯计数上限会让 "cache" 这类高频名字最终无法入废纸篓，
    # 且逼近上限时每次请求都要做上千次文件系统调用。
    dest_name, info_path, fd = name, None, None
    candidates = [name] + ["%s.%d" % (name, n) for n in range(1, 100)]
    candidates += ["%s.%s.%s" % (name, time.strftime("%Y%m%d%H%M%S"),
                                 secrets.token_hex(3)) for _ in range(10)]
    for cand_name in candidates:
        if os.path.lexists(os.path.join(files_dir, cand_name)):
            continue                 # 本体位已占，换名字
        candidate = os.path.join(info_dir, cand_name + ".trashinfo")
        try:
            # O_EXCL：创建成功即原子地占住这个名字，并发的第二个请求必然失败
            fd = os.open(candidate, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            dest_name, info_path = cand_name, candidate
            break
        except FileExistsError:
            continue
    if info_path is None:
        raise OSError("无法在废纸篓中为 %s 分配名称" % name)

    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(info)
    try:
        os.rename(path, os.path.join(files_dir, dest_name))
    except OSError:
        os.remove(info_path)        # 本体没进去就别留孤儿 info
        raise


def _url_quote(p):
    from urllib.parse import quote
    # 按字节 quote：Linux 文件名是字节串，非 UTF-8 的名字经 surrogateescape
    # 进到 str 后直接 quote 会抛 UnicodeEncodeError，整条废纸篓路径失效。
    return quote(os.fsencode(p))


def _trash_windows(path):
    # Send to Recycle Bin via SHFileOperationW with FOF_ALLOWUNDO (stdlib ctypes).
    # UNTESTED on this build — verify on a real Windows machine.
    import ctypes
    from ctypes import wintypes

    class SHFILEOPSTRUCTW(ctypes.Structure):
        _fields_ = [
            ("hwnd", wintypes.HWND),
            ("wFunc", wintypes.UINT),
            ("pFrom", wintypes.LPCWSTR),
            ("pTo", wintypes.LPCWSTR),
            ("fFlags", ctypes.c_uint16),
            ("fAnyOperationsAborted", wintypes.BOOL),
            ("hNameMappings", ctypes.c_void_p),
            ("lpszProgressTitle", wintypes.LPCWSTR),
        ]

    FO_DELETE = 3
    FOF_ALLOWUNDO = 0x0040
    FOF_NOCONFIRMATION = 0x0010
    FOF_SILENT = 0x0004
    op = SHFILEOPSTRUCTW()
    op.wFunc = FO_DELETE
    op.pFrom = os.path.abspath(path) + "\x00\x00"  # double-null terminated list
    op.fFlags = FOF_ALLOWUNDO | FOF_NOCONFIRMATION | FOF_SILENT
    rc = ctypes.windll.shell32.SHFileOperationW(ctypes.byref(op))
    if rc != 0:
        raise OSError("SHFileOperation failed (code %d)" % rc)


def hard_delete(path, parent_fd=None, leaf=None):
    """直接删除。给了 parent_fd 就相对该 fd 操作，不重新解析路径字符串。"""
    if parent_fd is not None and leaf is not None:
        st = os.lstat(leaf, dir_fd=parent_fd)
        if stat.S_ISDIR(st.st_mode):
            # rmtree 只认路径；用 fd 打开真实目录后再删其内容，
            # 最后相对父 fd 移除目录本身，全程不经过可被替换的路径串。
            sub = os.open(leaf, os.O_RDONLY | os.O_DIRECTORY
                          | getattr(os, "O_NOFOLLOW", 0), dir_fd=parent_fd)
            try:
                _rmtree_at(sub)
            finally:
                os.close(sub)
            os.rmdir(leaf, dir_fd=parent_fd)
        else:
            os.unlink(leaf, dir_fd=parent_fd)
        return
    if os.path.isdir(path) and not os.path.islink(path):
        shutil.rmtree(path)
    else:
        os.remove(path)


def _rmtree_at(dir_fd):
    """清空 dir_fd 指向的目录（不删该目录本身），全程 fd 相对操作。

    用显式栈而非递归：Python 默认递归上限 1000，而深目录树（构建缓存、
    嵌套 node_modules）能轻易超过——递归版会在中途抛 RecursionError 并
    留下半删状态，比不删更糟。显式栈只受内存限制。
    每层同时只持有 O(深度) 个 fd，出栈即关闭，不会耗尽描述符。
    """
    # 栈元素：(fd, 是否已展开)。第一次访问先列目录、删文件、压入子目录；
    # 第二次访问（子目录都处理完了）才关 fd 并由父层 rmdir。
    stack = [(dir_fd, False, None, None)]   # (fd, expanded, parent_fd, name)
    while stack:
        fd, expanded, parent_fd, name = stack.pop()
        if expanded:
            if fd != dir_fd:
                os.close(fd)
            if parent_fd is not None and name is not None:
                try:
                    os.rmdir(name, dir_fd=parent_fd)
                except FileNotFoundError:
                    pass            # 已被并发删除，视作完成
            continue
        subdirs = []
        try:
            entries = os.listdir(fd)
        except OSError:
            entries = []            # 读不到就跳过，让上层 rmdir 自然失败
        for entry in entries:
            try:
                st = os.lstat(entry, dir_fd=fd)
            except FileNotFoundError:
                continue            # 并发消失，跳过
            if stat.S_ISDIR(st.st_mode):
                try:
                    sub = os.open(entry, os.O_RDONLY | os.O_DIRECTORY
                                  | getattr(os, "O_NOFOLLOW", 0), dir_fd=fd)
                except OSError:
                    continue        # 打不开（权限/竞态），留给上层 rmdir 报错
                subdirs.append((sub, entry))
            else:
                # 普通文件、符号链接（含悬空）、socket、fifo、设备节点
                # 一律 unlink——O_NOFOLLOW + lstat 保证不会跟随到目标去。
                try:
                    os.unlink(entry, dir_fd=fd)
                except FileNotFoundError:
                    pass
        # 先压回自己（标记已展开），再压子目录：子目录先出栈处理完，
        # 轮到自己时目录已空，可以安全 rmdir。
        stack.append((fd, True, parent_fd, name))
        for sub, entry in subdirs:
            stack.append((sub, False, fd, entry))


def open_in_file_manager(path):
    # 非破坏性：在访达 / 资源管理器里打开该位置，方便用户自己审查删除
    target = path if os.path.isdir(path) else os.path.dirname(path)
    if sys.platform == "darwin":
        # .app 是 bundle，对它用 open 会"启动应用"而非显示；必须用 open -R 在访达里选中。
        if target.rstrip("/").endswith(".app"):
            r = subprocess.run(["open", "-R", target], capture_output=True, text=True)
            if r.returncode != 0:
                raise OSError((r.stderr or "open -R 失败").strip())
            return
        # 普通文件夹：先试直接打开看内容；沙盒容器（如微信）open 会报 -10814，
        # 退回 open -R 在父目录里选中它。两者都失败才算错。
        r = subprocess.run(["open", target], capture_output=True, text=True)
        if r.returncode != 0:
            r2 = subprocess.run(["open", "-R", target], capture_output=True, text=True)
            if r2.returncode != 0:
                raise OSError((r.stderr or r2.stderr or "open 失败").strip())
    elif sys.platform.startswith("win"):
        subprocess.run(["explorer", target])  # explorer 退出码不可靠，不据此判成败
    elif sys.platform.startswith("linux"):
        if not has_gui():
            raise OSError("当前是无图形界面环境，无法打开文件管理器；"
                          "请在终端用 ls -la 查看该路径")
        opener = next((t for t in ("xdg-open", "gio", "nautilus", "dolphin", "thunar")
                       if shutil.which(t)), None)
        if not opener:
            raise OSError("未找到文件管理器（xdg-open / nautilus / dolphin / thunar）")
        cmd = ["gio", "open", target] if opener == "gio" else [opener, target]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            raise OSError((r.stderr or "打开失败").strip())
    else:
        raise OSError("打开文件夹仅支持 macOS / Windows / Linux")


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, code, body, ctype="application/json"):
        b = body.encode("utf-8") if isinstance(body, str) else body
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            blob = json.dumps(DATA, ensure_ascii=False)
            cfg = json.dumps({"token": TOKEN, "endpoint": "/action"})
            html = TPL.replace("__REPORT_DATA__", blob).replace("__DELETE_CONFIG__", cfg)
            self._send(200, html, "text/html; charset=utf-8")
        else:
            self._send(404, "not found", "text/plain")

    def do_POST(self):
        if self.path != "/action":
            self._send(404, json.dumps({"ok": False, "error": "not found"}))
            return
        # DNS-rebinding guard: only accept local Host
        host = (self.headers.get("Host") or "").split(":")[0]
        if host not in ("127.0.0.1", "localhost"):
            self._send(403, json.dumps({"ok": False, "error": "host 不被允许"}))
            return
        n = int(self.headers.get("Content-Length", 0))
        try:
            req = json.loads(self.rfile.read(n) or b"{}")
        except Exception:
            self._send(400, json.dumps({"ok": False, "error": "请求格式错误"}))
            return
        if req.get("token") != TOKEN:
            self._send(403, json.dumps({"ok": False, "error": "token 校验失败"}))
            return
        mode = req.get("mode")
        allow = {"rm": RM_ALLOW, "trash": TRASH_ALLOW, "open": OPEN_ALLOW}.get(mode)
        if allow is None:
            self._send(400, json.dumps({"ok": False, "error": "未知操作"}))
            return
        # 先全量校验再执行：混着一个非法路径的批量请求应当【整批拒绝】，
        # 而不是删掉前几个再报错——后者会让页面显示"失败"却已实际删除，
        # 用户据此重试或误判状态都很危险。
        # 去重：[p, p] 会让第二次复核发现目标已被第一次删掉而误报 409。
        paths, _seen = [], set()
        for _p in (req.get("paths") or []):
            _rp = expand(_p)
            if _rp not in _seen:
                _seen.add(_rp)
                paths.append(_p)
        checked = []

        def _abort(code, payload):
            for _, _, fd_, _, _ in checked:
                if fd_ is not None:
                    try:
                        os.close(fd_)
                    except OSError:
                        pass
            self._send(code, json.dumps(payload))

        for p in paths:
            rp = expand(p)
            if rp not in allow:
                _abort(403, {"ok": False, "error": "路径不在白名单：%s" % p})
                return
            # 二级护栏，按操作类型分档：破坏性操作（rm / trash）只允许 $HOME 内，
            # 应用安装位置仅对非破坏性的 open 放行。
            # 这两档必须分开：白名单虽已限制路径来源，但 analysis JSON 由 agent
            # 生成，一旦某个绿灯项误带了 /usr/local/... 的 trash_paths，
            # 合并成一档就会让它通过校验并被递归删除。
            # 破坏性档只认【严格子孙】：rp == HOME 会让 rmtree 抹掉整个家目录。
            if mode == "open":
                roots = (HOME, "/Applications", "/opt", "/usr/local", "/usr/share",
                         "/var/lib/flatpak", "/snap")
                inside = any(rp == b or rp.startswith(b + os.sep) for b in roots)
            else:
                inside = rp.startswith(HOME + os.sep) and not _crosses_mount(rp)
            if not inside:
                _abort(403, {"ok": False, "error": "路径越界：%s" % p})
                return
            # 破坏性操作用 dir_fd 锚定父目录：校验拿到的只是【字符串】，
            # 两阶段之间父目录可能被换成指向别处的软链，同一字符串就解析到
            # 白名单外的目标。打开父目录持有 fd 后，后续 lstat / unlink 全部
            # 相对该 fd 进行——fd 绑定的是打开那一刻的真实 inode，
            # 之后无论路径怎么被替换都影响不到它。
            parent_fd, ident = None, None
            if mode != "open":
                parent = os.path.dirname(rp)
                leaf = os.path.basename(rp)
                try:
                    parent_fd = os.open(parent, os.O_RDONLY | os.O_DIRECTORY
                                        | getattr(os, "O_NOFOLLOW", 0))
                except OSError as e:
                    _abort(403, {"ok": False,
                                 "error": "无法锁定父目录：%s（%s）" % (p, e)})
                    return
                # 复核父目录身份：确保打开的确实是校验时那个 $HOME 内的目录
                try:
                    pst = os.fstat(parent_fd)
                    rst = os.stat(parent)
                    if (pst.st_dev, pst.st_ino) != (rst.st_dev, rst.st_ino):
                        raise OSError("父目录在校验期间发生变化")
                    lst = os.lstat(leaf, dir_fd=parent_fd)
                    ident = (lst.st_dev, lst.st_ino)
                except OSError:
                    ident = None        # 已不存在，执行阶段当作"已清理"
                checked.append((p, rp, parent_fd, leaf, ident))
                continue
            checked.append((p, rp, None, None, None))

        done = []
        try:
            for p, rp, parent_fd, leaf, ident in checked:
                try:
                    if mode != "open":
                        # 通过 fd 复核：fd 锚定的是校验时那个真实目录 inode，
                        # 路径字符串在两阶段之间被怎么替换都影响不到这次查询。
                        try:
                            st = os.lstat(leaf, dir_fd=parent_fd)
                            now = (st.st_dev, st.st_ino)
                        except OSError:
                            now = None
                        if now != ident:
                            self._send(409, json.dumps({
                                "ok": False, "done": done,
                                "error": "路径在校验后发生变化，已中止：%s" % p}))
                            return
                    if mode == "open":
                        open_in_file_manager(rp)
                    elif ident is None:
                        pass  # already gone, treat as success
                    elif mode == "trash":
                        # 废纸篓走系统工具/规范流程，只能用路径；此处已由上面的
                        # fd 复核确认路径当前仍指向校验时的同一 inode。
                        move_to_trash(rp)
                    else:
                        hard_delete(rp, parent_fd=parent_fd, leaf=leaf)
                    done.append(p)
                except Exception as e:
                    # 带上 done：前面几项可能已经真的删掉了，只回 error 会让页面
                    # 显示"整批失败"，用户重试或误判状态都危险。
                    self._send(500, json.dumps({"ok": False, "error": str(e),
                                                "done": done}))
                    return
            self._send(200, json.dumps({"ok": True, "done": done}))
        finally:
            for _, _, fd_, _, _ in checked:
                if fd_ is not None:
                    try:
                        os.close(fd_)
                    except OSError:
                        pass


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    global DATA, TPL, RM_ALLOW, TRASH_ALLOW, OPEN_ALLOW
    DATA, TPL, RM_ALLOW, TRASH_ALLOW, OPEN_ALLOW = load(sys.argv[1])
    srv = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    port = srv.server_address[1]
    url = "http://127.0.0.1:%d/" % port
    # flush=True：stdout 重定向到文件/管道时（nohup、agent 捕获输出）默认全缓冲，
    # 不刷就看不到端口和 ssh -L 提示——无头场景下那正是唯一的入口信息。
    print("报告服务已启动：" + url, flush=True)
    print("绿灯可删 %d 项 | 橙灯可移废纸篓/打开文件夹 %d 项 | 页面上点"
          % (len(RM_ALLOW), len(TRASH_ALLOW) - len(RM_ALLOW)), flush=True)
    print("用完按 Ctrl+C 停止服务（服务关掉后按钮即失效）", flush=True)
    if has_gui():
        webbrowser.open(url)
    else:
        print("\n未检测到图形界面。在本地机器上跑：", flush=True)
        print("    ssh -L %d:127.0.0.1:%d <此主机>" % (port, port), flush=True)
        print("然后在本地浏览器打开上面的地址。", flush=True)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\n已停止服务。")


if __name__ == "__main__":
    main()
