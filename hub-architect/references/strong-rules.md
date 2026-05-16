# 五条强规则详解

每条规则都来自实际迁移事故。没有"以防万一"的规则——每条都踩过坑。

## 规则 1：备份先行

**规则**：任何技能结构改动必须先备份，再替换验证，最后删除原入口。

**正确顺序**：
1. `cp -r ~/.claude/skills/{skill} workspace/backups/{skill}.bak.$(date +%Y%m%d)`
2. 复制到 Hub 并验证
3. 验证通过后删除原入口

**反模式（血的教训）**：
```
# 错误：先删再建
rm -rf ~/.claude/skills/old-skill
cp -r workspace/backups/old-skill ~/.claude/skills/hub/modules/new-leaf/
# 如果第 2 步失败，old-skill 已经没了，无法回滚
```

**为什么必须这个顺序**：删除是不可逆操作。先备份 = 保留回滚能力。中间任何步骤失败，都能从备份恢复到原始状态。

## 规则 2：加载隔离

**规则**：备份与审计产物不得进入全局技能加载根目录。

**全局技能加载根目录**：
- `~/.claude/skills/`
- `~/.agents/skills/`（如果有）

**安全的备份位置**：
- `workspace/backups/`
- `~/backups/`
- 任何不在 skills 根目录下的路径

**反模式（血的教训）**：
```
# 错误：备份放在 skills 根内
mkdir -p ~/.claude/skills/backups/
cp -r ~/.claude/skills/old-skill ~/.claude/skills/backups/old-skill.bak
# Agent 加载器扫描 ~/.claude/skills/ 时会发现 backups/old-skill.bak/SKILL.md
# 结果：old-skill 被加载两次（原入口 + 备份入口），触发行为不可预测
```

**Gate D 就是检查这个**：`backup_in_loader = any((p / "backups").exists() for p in loader_roots)`

## 规则 3：回归放行

**规则**：结构变更后必须通过 Gate A/B/D 才允许放行。

**Gate A**：主路由准确率 >= 92%，高风险域 >= 95%
**Gate B**：误触发率 <= 5%，漏触发率 <= 3%
**Gate D**：备份目录不在 loader 根内

**反模式（血的教训）**：
```
# 错误："我试了两个用例没问题"
# 实际：48 条用例中有 3 条失败，其中 2 条是高频场景
# 上线后用户说"帮我写 PPT"，路由到了 web-hub 而不是 doc-hub
```

**为什么 92% 不是 100%**：现实中有模糊意图的边界用例，100% 意味着过度拟合。92% 是经过 3 轮回归验证的平衡点。

## 规则 4：证据三角

**规则**：声称某 Skill 可调用时必须同时提供映射证据、结构证据、行为证据。

| 证据 | 检查命令 | 通过条件 |
|---|---|---|
| 映射证据 | `grep "{leaf}" hub/SKILL.md` | 有匹配行 |
| 结构证据 | `test -s hub/modules/{leaf}/LEAF.md` | 文件存在且非空 |
| 行为证据 | 回归用例 expectedLeaf == predictedLeaf | 匹配 |

**反模式（血的教训）**：
```
# 错误："Hub 里写了映射行，应该没问题"
# 实际：leaf 文件是空的（复制时出错）
# 结果：Agent 路由到了正确的 Hub，但加载叶子时报错
```

**为什么需要三个**：映射证据证明"Hub 知道有这个叶子"，结构证据证明"叶子文件真的存在"，行为证据证明"路由逻辑能正确命中"。三者缺一不可。

## 规则 5：双根复审

**规则**：迁移完成必须同时审计 .agents 与 .claude，不得以单根结果放行。

**两个根目录**：
- `~/.claude/skills/`（Claude Code 的 Skill 根）
- `~/.agents/skills/`（某些 Agent 框架的 Skill 根）

**反模式（血的教训）**：
```
# 错误：只检查了 ~/.claude/skills/
ls ~/.claude/skills/ | wc -l  # 18 个，看起来对了
# 实际：~/.agents/skills/ 里还有 19 个未迁移的 Skill
# 结果：Agent 从两个根加载，出现重复触发
```

**为什么叫"复审"**：不是"迁移两次"，是"迁移完后，两个根都要扫一遍，确认没有遗漏或重复"。
