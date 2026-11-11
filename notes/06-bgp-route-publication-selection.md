# 知识点：BGP 第 2 讲 — 路由发布与选路全属性（深度版）

日期：2026-11-09
所属月份/阶段：第 1 个月 / BGP 7 讲之 2
标准：5 关全过才算掌握（讲清、盲配、排障 3 案、设计、面试 10 题）

## 核心概念

### 路由怎么进 BGP：三种发布方式

- network：前缀必须已在本地路由表里（精确匹配），打 Origin i。第 1 讲故障 2 就是这个规矩：R3 配了 network 8.8.8.8，但本地没有这条路由，什么都发不出去，直到 LoopBack1 建出来才有得发。
- import-route：从别的协议、静态或直连路由引入，打 Origin ?（Incomplete）。默认把该来源的所有路由都引进来，生产上要加 route-policy 只引想引的。
- aggregate：聚合路由，打 Origin i。
- Origin 只在前面属性都相同才比较，平时不影响转发。

### 华为完整选路顺序（纠正 02 笔记的简版）

按顺序一条一条比，比出结果就停，后面的不再比：

0. 下一跳不可达的路由直接丢弃
1. PrefVal 最大（华为私有，默认值 0，只在本地设备有效）
2. Local Preference 最大
3. 路由类型：聚合 > 汇总 > network > import > 学到的
4. AIGP 最小
5. AS_PATH 最短
6. Origin：i < e < ?（IGP 最优，Incomplete 最差）
7. MED 最小（默认只比较来自同一个相邻 AS 的路由）
8. eBGP 优于 iBGP
9. 到下一跳的 IGP 开销最小
10. Router ID 最小，其次 Cluster List 最短、Originator ID 最小、对端地址最小

### 两个坑

- PrefVal 是第一个比的，而且只在本地一台设备上生效。本地设的 PrefVal 能悄悄压过精心设的 Local Preference。排障时 Local Preference 明明设高了却不生效，先看 PrefVal。
- MED 默认只在同一个邻居 AS 来的路由之间比。不同 ISP 的 MED 不直接比，除非开 always-compare-med。

## 开场实验：Origin 从 i 变成 ?

- 基线：R1 上 `display bgp routing-table 8.8.8.8`，Origin 是 i。
- R3 上换发布方式。注意：LoopBack1 的 8.8.8.8 是直连路由，优先于静态，不先撤掉它，静态路由不会生效，import-route 也引不到。所以先撤 LoopBack1 的地址，再配静态到 NULL0，再 undo network、import-route static。
  ```
  system-view
  interface LoopBack1
   undo ip address
  quit
  ip route-static 8.8.8.8 255.255.255.255 NULL0
  bgp 65002
   undo network 8.8.8.8 255.255.255.255
   import-route static
  quit
  ```
- R1 再看：Origin 应该从 i 变成 ?，AS-path 还是 65002，下一跳还是 10.2.2.2。
- 注意两点：import-route static 会把 R3 上所有静态路由都引进来，包括回程路由 10.0.12.0/24，R1 上会多看到一条 BGP 路由；实验期间 R1 ping 8.8.8.8 会不通，是 NULL0 丢包，不是 Origin 的问题。
- 恢复：
  ```
  bgp 65002
   undo import-route static
   network 8.8.8.8 255.255.255.255
  quit
  undo ip route-static 8.8.8.8 255.255.255.255 NULL0
  interface LoopBack1
   ip address 8.8.8.8 255.255.255.255
  quit
  ```

实验结果（2026-11-09 晚，已验证）：R1 上 8.8.8.8 的 Origin 从 i 变成 Incomplete（?），AS-path 还是 65002，下一跳还是 10.2.2.2。说明发布方式只改 Origin 标记，不影响路由本身被选中和转发；Origin 只有在两条路竞争、前面属性都相同的时候才起作用。

## 今晚的插曲：实验恢复

昨晚实验没保存，eNSP 关机后三台配置全丢。恢复时踩到的坑：文件里的配置带 # 分隔行，直接粘贴会报错，且命令行停在接口视图里，导致后面的 `ip route-static` 和 `bgp` 被拒绝。已把 lab 03 改成可直接粘贴的格式（去 #、每段接口后加 quit、粘贴前先 system-view）。教训：每次配完每台设备上 `save`（输 y 确认），再在 eNSP 里 Ctrl+S 保存拓扑。

## 选路调优实验（2026-11-10 晚，已验证）

拓扑：加了 R1–R3 直连（10.0.13.0/24，eBGP），R1 有两条路到 8.8.8.8：直连 eBGP（下一跳 10.0.13.3）和经 R2 的 iBGP（下一跳 10.2.2.2）。基线：最优是直连 eBGP（eBGP 优先于 iBGP）。

- 实验 1 PrefVal：R1 上 `peer 10.2.2.2 preferred-value 100`，最优翻成 iBGP；eBGP 路径显示 `not preferred for PreVal`。结论：PrefVal 第 1 步比，能压过 eBGP 优先规则。
- 实验 2 Local Preference：清掉 PrefVal 后，R1 上 route-policy LP200（apply local-preference 200）应用到 iBGP 邻居入方向，最优翻成 iBGP。结论：Local Preference 越大越优，第 2 步比。
- 实验 3 对决：iBGP 侧 Local Preference 200，eBGP 侧 PrefVal 100，结果 eBGP 赢。结论：PrefVal 先比，Local Preference 200 没机会被比到——这就是信里说的坑。
- 实验 4 MED（未完成）：R3 对 R1 出方向设 MED 200，验证了默认 MED 不比（直连 MED 200、经 R2 的 MED 0，最优还是直连）。`bestroute med-always` 在这台 eNSP 的老 VRP 上两个视图下都不支持，跨 AS 比 MED 的翻转没做成。标准做法是加一台同 AS 的邻居（R4 方案），或在新版 VRP/真机上开 `bestroute med-always`。

版本注意（eNSP 老 VRP）：
- 没有 `apply med`，设 MED 用 `apply cost 200`（策略用到 BGP 上时 cost 就是 MED）。
- 没有 `bestroute med-always`（BGP 视图和 ipv4-family unicast 视图都没有）。
- `refresh bgp` 不支持，用 `reset bgp` 代替。

## 排障 3 案（2026-11-10 晚，全过）

- 第 1 案 PrefVal 陷阱：R1 上 iBGP 邻居被设 preferred-value 100，最优走了 R2。诊断：按选路顺序比，PrefVal 100 对 0，第 1 步定胜负；Local Preference 都是 100 打平，AS_PATH 都是 65002 打平。修复：undo preferred-value + reset。
- 第 2 案发布丢失：R3 上 undo network 8.8.8.8，R1、R2 都没路由。诊断：R3 本地路由表里 8.8.8.8/32 Direct 还在，BGP 表里没有（The network does not exist），配置里 network 语句没了。修复：加回 network。
- 第 3 案 Origin 被改：R3 对 R1 出方向策略 apply origin incomplete，直连路径 Origin 变成 ?，最优翻到 iBGP（Origin i）。诊断：前面属性全平，Origin 这一步 i 优于 ?。修复：R3 删出方向策略 + reset。

## 面试 10 题（2026-11-11 晚补答后全对——已过）

首答（2026-11-10 晚）：2 全对（第 4、7 题），5 部分对，3 错。
补答（2026-11-11 晚）：第 1 题 aggregate→i；第 2 题根本区别是精确匹配；第 3 题前 5 步全对；第 5 题另一条路 PrefVal 被设高、第一优先级；第 6 题默认只在同一邻居 AS 之间比、跨 AS 开 bestroute med-always；第 8 题 R1 只收到 1 条、Origin i；第 9 题第 8 步比、能推翻；第 10 题完整顺序全对。10 道全对，面试关已过。

## 还没搞懂 / 下一步

- 第 2 讲完成：开场实验、调优实验、排障 3 案、面试 10 题全部通过。MED 跨 AS 比较因 eNSP 老 VRP 不支持未实操（概念已掌握）。
- 下一步：第 3 讲选路调优（AS_PATH Prepend、Community、路由汇总）。
