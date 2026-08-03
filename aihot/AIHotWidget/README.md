# AI HOT 小组件

一个 SwiftUI + WidgetKit App，将 AI HOT 当前热点以小组件形式展示在 iPhone 桌面。

## 功能

- `AI 当前热点`：抓取 AI HOT 首页“当前热点”聚合榜，最多显示前 6 条。
- 支持大号尺寸小组件。
- 自动、浅色、深色、透明四种外观。
- 每 15 分钟请求一次新的 WidgetKit 时间线。
- 每条热点都可独立点击并打开对应原始网页。
- 网络失败时回退到扩展内最近一次缓存。

## 运行

直接打开已经生成好的工程：

```bash
open AIHotWidget.xcodeproj
```

选择 `AIHot` scheme 后即可在模拟器运行。安装到真机前，在 Xcode 的
Signing & Capabilities 中选择自己的开发团队；如果 Bundle ID 冲突，再改成自己的唯一标识。

运行后，在模拟器或真机主屏幕添加“AI 当前热点”大号小组件。

修改 `project.yml` 后可重新生成工程：

```bash
xcodegen generate
```

## iOS 刷新与透明背景限制

WidgetKit 的 15 分钟时间线是刷新请求，不保证系统精确每 15 分钟执行。iOS 会结合电量、使用频率和系统预算决定实际刷新时间。

透明模式使用 `Color.clear` 和可移除容器背景。主屏幕最终是否显示完全透明由当前 iOS 版本、主屏幕样式及系统渲染模式决定；第三方小组件不能绕过系统策略直接读取壁纸来伪造像素级透明背景。
