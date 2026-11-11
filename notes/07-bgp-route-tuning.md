# 知识点：BGP 第 3 讲 — 选路调优（AS_PATH Prepend、Community、路由汇总）

日期：2026-11-11
所属月份/阶段：第 1 个月 / BGP 7 讲之 3
标准：5 关全过才算掌握（讲清、盲配、排障 3 案、设计、面试 10 题）

## 核心概念

### AS_PATH Prepend
- 在出方向策略里用 `apply as-path <AS号> <AS号> additive` 把 AS_PATH 人为垫长。AS_PATH 越短越优先（第 5 步），垫长就是让这条路变差，流量走另一条。
- 典型用途：双出口/多归属时，让某个 ISP 的入方向流量少走这条链路。只影响别人怎么选你，不影响你自己出方向。
- 注意：Prepend 的是自己的 AS 号，重复出现是合法的；防环检查看的是 AS 号出现与否，不是次数。

### Community（团体属性）
- BGP 的可选过渡属性，用 `AA:NN` 标记路由，本身不直接参与选路，但可以被策略匹配后改 LocalPref、Prepend 等。
- 常见标准值：no-export（不发给 eBGP 邻居）、no-advertise（不发给任何邻居）。
- 关键点：团体属性默认不发给邻居，必须在邻居上配 `peer <地址> advertise-community` 才会带出去；接收方用 `ip community-filter` + route-policy 的 `if-match community-filter` 来匹配。
- 典型用途：ISP 给客户路由打标记，客户按标记调 LocalPref，实现“走某条链路优先”的精细控制。

### 路由汇总（待做）
- `aggregate` 把多条明细聚合成一条，Origin i；默认明细和汇总一起发，加 `detail-suppressed` 只发汇总。

## 实验（2026-11-11 晚，已验证）

拓扑沿用第 2 讲：R1–R2 iBGP，R2–R3 eBGP，R1–R3 直连 eBGP；R1 两条路到 8.8.8.8，基线最优是直连 eBGP。

- 实验 1 AS_PATH Prepend：R3 对 R1 出方向 `apply as-path 65002 65002 additive`，直连路径 AS-path 变成 65002 65002 65002（长度 3），显示 `not preferred for AS-Path`，最优翻到 iBGP（AS-path 65002，长度 1）。结论：AS_PATH 越短越优先，第 5 步比。注意：策略改了要 reset 邻居，通告要几秒才到，查早了会看到旧结果。
- 实验 2 Community：R3 对 R1 出方向 `apply community 65002:100 additive` + `peer 10.0.13.1 advertise-community`；R1 上 `ip community-filter 1 permit 65002:100`，route-policy 匹配后 `apply local-preference 200` 应用到直连邻居入方向。结果：直连路径带 Community 65002:100，localpref 200，重新变回最优。结论：Community 本身不选路，靠策略匹配后改属性来起作用；不配 advertise-community，标记发不出去。

## 还没搞懂 / 下一步

- 路由汇总实验待做。
- 排障 3 案、面试 10 题待做。
