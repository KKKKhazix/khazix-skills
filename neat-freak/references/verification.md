# 证据层级与发布终态

## 风险决定证据深度

| 结论 | 最低证据 |
|---|---|
| “文档链接有效” | 项目自己的 doc-link/index check 或逐链接存在性 |
| “规则已同源” | realpath/readlink/import + 平台实际加载顺序 |
| “代码实现是 X” | 当前目标分支代码、schema、配置与相关测试 |
| “PR 已完成” | PR state=merged + merge commit；不能推导已部署 |
| “已部署” | deploy marker/release 指向目标 commit + 服务 active |
| “用户已看到新版本” | canonical 用户 URL/API 的真实响应，必要时同时比 origin/cache |
| “可安全清场” | merged + production contains change + knowledge receipt + lane clean + 无唯一未集成文件 |
| “已获准清场” | 当前任务已有明确清理授权 + 对象仍在授权范围内 |
| “整个项目干净” | 项目内所有适用事实面 verified；warning、pending 和 out-of-scope 单列 |

代码直觉、旧 memory、commit message 和 cache-buster URL 都只能当线索，不能单独证明生产终态。

## 真相矩阵

对每个发现至少记录：

```text
topic: <事实主题>
authority: <当前权威来源>
code: verified-current | stale | n/a
runtime: verified-current | stale | unverified | n/a
docs: verified-current | stale | changed
rules: verified-current | stale | changed | n/a
memory: verified-current | stale | generated-read-only | changed | n/a
action: <做了什么或为什么没做>
verification: <命令、页面或门禁>
```

用户不需要看到完整矩阵，但最终摘要必须保留未闭合状态。

## 发布状态机

```text
implemented
  -> locally verified
  -> pushed / PR opened
  -> CI + required backtest/visual review passed
  -> merged
  -> deployed
  -> live verified
  -> knowledge closed + receipt recorded
  -> existing cleanup authorization checked (ask only if missing)
  -> workspace cleaned
  -> post-cleanup audit passed
  -> cleanup result appended
```

跳过的状态必须有项目规则允许的原因。失败停在哪一格，就按那一格汇报，不能用“基本完成”覆盖。

## 缓存和多表面产品

当用户可见内容经过 CDN、边缘缓存、搜索索引、异步 worker 或多客户端时，至少识别：

- origin 是否为新内容；
- canonical URL 是否仍为旧缓存；
- API/页面/通知/RSS 是否共享同一数据出口；
- deploy marker 是否在所有异步进程真正切换之后才写；
- cache-buster 是否只是诊断，而非真实用户验收。

只验证其中一个表面时，在结论里明确限制范围。

## 清场前 gate

清场前核实以下事实：

1. 验证目标工作已集成并上线；
2. 同步 docs/rules/获准记忆；
3. 记录项目要求的 knowledge closeout receipt；
4. 预览待删除 worktree/branch/db/artifact；
5. 检查 dirty 文件和 patch equivalence；
6. 核对当前任务的清理授权，已明确批准的不重复询问；
7. 执行范围内的清理，保留尚有唯一内容或尚未授权的对象；
8. 重新运行 workspace audit，汇报实际清理结果和待决项。


目录名、分支年龄和 agent 会话是否关闭都不能证明可删除。

## 验证失败时

- 同一失败第二次出现，停止盲重试，重新检查假设、环境和命令名。
- 门禁要求机器可读 metadata 时，补正确留痕并触发新事件；不要用人工确认绕过可修复的格式问题。
- 失败发生在生产写入前，明确说“尚未影响生产”；发生在切流后，先确认当前 active release 和回滚边界。
- 任何未验证项保持 `pending`，不要为了摘要好看把它降格成 warning。
