# 知识点：BGP 第 3 讲 — 选路调优（AS_PATH Prepend、Community、路由汇总）

日期：2026-11-11～2026-11-13，已完成
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

### 路由汇总
- `aggregate` 把多条明细聚合成一条，Origin i；默认明细和汇总一起发，加 `detail-suppressed` 只发汇总。
- 已验证（2026-11-13）：汇总路由出现不需要 reset，配完立刻可见；`detail-suppressed` 后明细消失，但 ping 明细地址仍通（走聚合路由）。

## 实验（2026-11-11 晚，已验证）

拓扑沿用第 2 讲：R1–R2 iBGP，R2–R3 eBGP，R1–R3 直连 eBGP；R1 两条路到 8.8.8.8，基线最优是直连 eBGP。

- 实验 1 AS_PATH Prepend：R3 对 R1 出方向 `apply as-path 65002 65002 additive`，直连路径 AS-path 变成 65002 65002 65002（长度 3），显示 `not preferred for AS-Path`，最优翻到 iBGP（AS-path 65002，长度 1）。结论：AS_PATH 越短越优先，第 5 步比。注意：策略改了要 reset 邻居，通告要几秒才到，查早了会看到旧结果。
- 实验 2 Community：R3 对 R1 出方向 `apply community 65002:100 additive` + `peer 10.0.13.1 advertise-community`；R1 上 `ip community-filter 1 permit 65002:100`，route-policy 匹配后 `apply local-preference 200` 应用到直连邻居入方向。结果：直连路径带 Community 65002:100，localpref 200，重新变回最优。结论：Community 本身不选路，靠策略匹配后改属性来起作用；不配 advertise-community，标记发不出去。

## 实验 3 路由汇总（2026-11-13，已验证）

- 第 0 步基线确认：实验 1、2 的策略已清理（PREPEND、COMM、SETLP 都 undo）。R1 上最优是直连 eBGP（下一跳 10.0.13.3），AS-path 只有一个 65002，LocalPref 100，没有 Community。
- 第 1 步加明细：R3 加 LoopBack2/3/4（8.8.8.9/10/11 /32）并 network 发布，R1 上看到 4 条 /32。坑：`display bgp routing-table 8.8.8.8` 只显示 8.8.8.8 这一条，看不到另外 3 条；要看全表用不带地址的 `display bgp routing-table`。
- 第 2 步汇总（不抑制明细）：R3 配 `aggregate 8.8.8.8 255.255.255.248`，R1 立刻看到 8.8.8.8/29，不用 reset 刷新，和 4 条 /32 并存。/29 的 Origin i、AS-path 65002 是按本笔记的预期，用户只确认了 /29 出现，没单独发详情输出，以现场为准。
- 第 3 步抑制明细：改成 `aggregate 8.8.8.8 255.255.255.248 detail-suppressed`，R1 上只剩 /29，4 条 /32 明细消失；R1 上 ping 8.8.8.9 仍通，走聚合路由。
- 恢复：已恢复基线，只留 8.8.8.8/32，ping 通；三台都 save，再 Ctrl+S 保存拓扑。
- 结论：汇总路由出现不需要 reset；`detail-suppressed` 只影响通告，不影响转发——明细地址仍可达，靠聚合路由转发。

## 排障 3 案（2026-11-13，全部通过）

- 第 1 案 AS_PATH 被垫长：R3 出方向策略把直连路径 AS-path 垫到 65002 65002 65002，最优翻到经 R2 的 iBGP（下一跳 10.0.12.2）。用户直接找对根因：第 5 步 AS_PATH 越短越优先。修复：R3 上 `undo peer 10.0.13.1 route-policy PREPEND export`，`undo route-policy PREPEND`，`reset bgp 10.0.13.1`；最优变回直连。
- 第 2 案 Community 没发出去：R3 策略里打了 Community 65002:100，但邻居上没配 `advertise-community`，R1 直连那条没带标记，SETLP 策略匹配不上，localpref 仍是 100，最优仍是 iBGP。用户先猜错到 R2 的策略上，纠正后查到直连那条确实没有 Community，再确认 R3 邻居配置里少了 `advertise-community` 这一行。修复：R3 上 `peer 10.0.13.1 advertise-community` 后 reset；直连带上 Community，localpref 变 200，最优翻回直连（Local Preference 第 2 步先于 AS_PATH 第 5 步）。清理：第 2 案的 PC / SETLP 策略和 community-filter 1 都已 undo。
- 第 3 案聚合掩码配错：R3 配了 `aggregate 8.8.8.0 255.255.255.0`，R1 上聚合路由是 8.8.8.0/24，覆盖 .0～.255 共 256 个地址，大部分不存在。明细是 .8、.9、.10、.11，最小覆盖网段是 8.8.8.8/29（范围 .8～.15）。修复：`undo aggregate 8.8.8.0 255.255.255.0`，改成 `aggregate 8.8.8.8 255.255.255.248 detail-suppressed`；R1 上只剩 /29，ping 8.8.8.9 仍通。
- 恢复基线：第 3 案后 R3 上 undo 聚合与 3 条 network、删 LoopBack2/3/4 地址、三台 save + Ctrl+S；基线已恢复（2026-11-13 16:09 林逸确认）。

## 面试 10 题首答（2026-11-13 16:03，手写照片，未通过）

- 全对 4 道：Q2、Q4、Q8、Q9。
- 半对 2 道：Q3（缺 LocalPref 200 机制）、Q6（只答了抑制明细）。
- 错 4 道：
  - Q1：把 Prepend 机制错说成“不接收路由”，步数错写第 4 步（应为第 5 步）。
  - Q5：聚合生成条件写反了。
  - Q7：没答出 Origin i 和 AS-path 65002。
  - Q10：选路顺序错——Origin 应在 AS_PATH 后，MED 应在 eBGP/iBGP 前；还漏了路由类型和 AIGP。
- 重答 6 道待做：Q1、Q3、Q5、Q6、Q7、Q10。全部答对才算过面试关，第 3 讲才算完成。

## 面试重答进度（2026-11-13，已完成）

- 已过 3 道：Q5、Q6、Q7。
- 补答 3 项（2026-11-13 16:23，打字）全部对了：
  - Q1：“越长越不优先”——AS-Path 越长越不优先，方向确认无误（之前“越长越优”确为笔误）。
  - Q3：完整机制——R3 打标记 → R1 匹配后 LocalPref 200 → 第 2 步先比，AS_PATH 第 5 步还没比到，直连赢回。
  - Q10：实验映射——Prepend → AS_PATH 第 5 步；Community → Local Preference 第 2 步；聚合 → 路由类型第 3 步。
- 第 3 讲已完成：实验 3 个、排障 3 案、面试 10 题全过。

## 第 3 讲已完成 / 下一步

- 第 3 讲已完成（2026-11-13）：实验 3 个（Prepend、Community、路由汇总）、排障 3 案、面试 10 题全过。
- 下一讲：第 4 讲 RR 与联盟（路由反射器与联盟）。
- 面试 10 题主题（备查）：Prepend 作用与选路步数、垫长后翻路的原因、Community 经 LocalPref 起作用的步数、缺 advertise-community 的原因、aggregate 生成条件、detail-suppressed 的作用、聚合路由的 Origin 与 AS-path、/29 而非 /24 的原因、localpref 200 + 长 AS-path 对 localpref 100 + 短 AS-path 的比较、选路全顺序及三个实验对应的步数。
