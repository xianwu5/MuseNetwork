# 实验：BGP 第 3 讲 — 路由汇总（接林逸 2026-11-12 给的第 0、1 步）

日期：2026-11-13（第 2 步备好，待第 1 步结果）
状态：第 1 步待用户在林逸那边交结果；第 2 步已备好，第 1 步结果一到就能做
环境：沿用第 3 讲拓扑（R1–R2 iBGP，R2–R3 eBGP，R1–R3 直连 eBGP 10.0.13.0/24）

## 前情

- 第 3 讲实验 1、2 已验证：AS_PATH Prepend、Community 65002:100。
- 林逸 2026-11-12 已给清理步骤和汇总第 0、1 步，并让用户先发 R1 的结果再做聚合。
- 本文件只补第 2 步及以后，不重复第 1 步的配置。

## 第 0 步：验基线（林逸已给，复核用）

R1 上 `display bgp routing-table 8.8.8.8`，最优应该是直连 eBGP（下一跳 10.0.13.3），AS-path 只有一个 65002，LocalPref 100，没有 Community。

如果还没清干净，按林逸给的清理步骤清（策略名以 display 为准）：

R3：
```vrp
system-view
bgp 65002
 undo peer 10.0.13.1 route-policy COMM export
 undo peer 10.0.13.1 advertise-community
quit
undo route-policy COMM
return
reset bgp 10.0.13.1
```

R1：
```vrp
system-view
bgp 65001
 undo peer 10.0.13.3 route-policy SETLP import
quit
undo route-policy SETLP
undo ip community-filter 1
return
reset bgp 10.0.13.3
```

PREPEND 如还在配置里（`display current-configuration bgp` 能看到），按同样格式 undo 掉再 save。三台 `save`，再 Ctrl+S 保存拓扑。

## 第 1 步：R3 加 3 条明细路由（林逸已给，待做）

R3 加 LoopBack2–4（8.8.8.9、8.8.8.10、8.8.8.11 /32），再 network 进 BGP。
预期：R1 上能看到 4 条 /32（8.8.8.8/9/10/11）。先把这个结果发给林逸，再做第 2 步。

## 第 2 步：R3 上做聚合（新备好的，可直接粘贴）

8.8.8.8–8.8.8.11 正好是一段 /30：8.8.8.8 255.255.255.252。粘贴前先 system-view，每段配完有 quit，不带 # 号行。

```vrp
system-view
bgp 65002
 aggregate 8.8.8.8 255.255.255.252 detail-suppressed
quit
return
```

要点：aggregate 只在 BGP 表里至少有一条明细（组分路由）时才生成汇总；Origin 是 i；detail-suppressed 的意思是只发汇总，不发明细。

## 第 3 步：验证

R1 上：
```vrp
display bgp routing-table 8.8.8.8 255.255.255.252
display bgp routing-table
```

预期：R1 只剩一条 8.8.8.8/30，Origin i，4 条 /32 不见了（被 detail-suppressed 压住，不是被删了）。

R3 上：
```vrp
display bgp routing-table 8.8.8.8
```

预期：R3 本地 BGP 表里汇总和 4 条 /32 都在——明细只在通告时被压住，本地还在。

再测连通性：R1 上 `ping 8.8.8.9`、`ping 8.8.8.11` 应该通（走汇总到 R3，R3 本地有 LoopBack2–4）。

## 第 4 步（可选）：去掉 detail-suppressed 对比一次

```vrp
system-view
bgp 65002
 undo aggregate 8.8.8.8 255.255.255.252
 aggregate 8.8.8.8 255.255.255.252
quit
return
```

R1 上再查：汇总和 4 条 /32 同时出现。然后恢复成带 detail-suppressed 的版本（undo 再加回），保持干净的结束状态。

## 第 5 步：保存

三台 `save`，再 Ctrl+S 保存拓扑。

## 结果记录（做完再填）

- 第 1 步 R1 看到 4 条 /32：是 / 否，截图/输出：
- 聚合后 R1 只剩 8.8.8.8/30：是 / 否，Origin：
- R3 本地明细还在：是 / 否
- ping 8.8.8.9、8.8.8.11：通 / 不通

## 第 3 讲还剩什么

汇总实验做完，第 3 讲还剩排障 3 案、面试 10 题（按 5 关标准：讲清、盲配、排障 3 案、设计、面试 10 题）。
