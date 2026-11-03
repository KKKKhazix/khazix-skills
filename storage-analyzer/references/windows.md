# Windows 数据布局与分级参考

分析 Windows 扫描结果时读这份。讲"东西存在哪、怎么辨认、归哪一级"。
注意：Windows 代码路径在 macOS 上无法验证，分析时对路径存在性保持谨慎。

## 多盘符

Windows 通常多个盘（C:、D:…）。磁盘总览会列出所有盘，但**分析和清理聚焦系统盘 C:**——缓存、AppData、临时文件几乎都在 C:。其他盘（D: 等）一般是用户自存的资料/游戏，归 🟡 让用户自己判断，不要自动给删除按钮。

## 关键目录

| 目录（环境变量） | 装什么 | 典型分级 |
|---|---|---|
| `%LOCALAPPDATA%`（`C:\Users\<u>\AppData\Local`） | 浏览器缓存、应用数据、Temp，最大头 | 缓存 🟢 / 应用数据 🟡 |
| `%LOCALAPPDATA%\Temp`、`%TEMP%` | 临时文件 | 🟢 |
| `%APPDATA%`（Roaming） | 应用配置/数据 | 🟡 |
| 浏览器缓存 `%LOCALAPPDATA%\Google\Chrome\User Data\*\Cache`、Edge 同构 | 浏览器缓存 | 🟢 |
| 浏览器 `User Data\<Profile>`（非 Cache 部分） | 书签/登录态 | 🟡 |
| `%USERPROFILE%\.cache`、`.npm`、`.gradle`、`.m2`、`.nuget\packages`、`%LOCALAPPDATA%\pip\Cache`、`Yarn` | 开发缓存 | 🟢 |
| `C:\Program Files`、`Program Files (x86)` | 应用本体 | 🔴 仅重复/想卸时上灯，否则归蓝色 |
| `%USERPROFILE%\Downloads` 的安装包 | exe/msi 残留 | 🟢 |
| `C:\$Recycle.Bin` | 回收站 | 🟡 提示用户清空 |

## 系统占用（不上灯，归蓝色"系统及其他"，间接释放写 long_term）

- `C:\Windows\WinSxS`：组件存储，**绝不能手删**，用 `DISM /Online /Cleanup-Image /StartComponentCleanup`
- `C:\Windows\SoftwareDistribution\Download`：Windows Update 缓存，用磁盘清理处理
- `hiberfil.sys`（休眠）、`pagefile.sys`（虚拟内存）：系统管理，别手动删
- 间接释放：设置 > 系统 > 存储 > 存储感知；`cleanmgr`（磁盘清理）；扩展磁盘清理选 Windows 更新清理

## 删除机制

`server.py` 在 Windows 用 ctypes 调 `SHFileOperationW`(FOF_ALLOWUNDO) 送进回收站；纯标准库。🟢 项的 `trash_paths` 应在用户配置文件（`%USERPROFILE%`）目录内，便于白名单与 HOME 越界校验通过。

## 联接目录与项目

先用 `Get-Item -Force` 检查 LinkType、Target，junction 不计入实体大小；`.git` 文件也是 worktree 标识。项目和工具安装目录不能仅凭体积大、时间久就列入可清理项。UTF-8 输出在 PowerShell 用 `Out-File -Encoding utf8` 保存。
