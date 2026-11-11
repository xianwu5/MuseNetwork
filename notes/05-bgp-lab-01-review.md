# 复盘：BGP 第 1 讲实验之夜（2026-11-08）

实验：labs/03-bgp-neighbor-lab.md。拓扑：R1–R2 iBGP（AS 65001），R2–R3 eBGP（R3 是 ISP，AS 65002），R3 发布 8.8.8.8/32。

## 今晚的成果

- 基础连通打通：三台 `display bgp peer` 全是 Established，R1 学到 8.8.8.8，R1 ping 8.8.8.8 通。
- 实战排障 4 个故障，逐个定位修复。
- 定了实验编址规范（见下）。

## 编址规范（以后所有实验都按这个来）

- 直链：10.0.XY.0/24，X、Y 是两端设备编号，主机位取设备编号。如 R1–R2 用 10.0.12.0/24（R1 .1，R2 .2），R2–R3 用 10.0.23.0/24（R2 .2，R3 .3）。
- Loopback：10.n.n.n/32，n 是设备编号。R1 10.1.1.1，R2 10.2.2.2，R3 10.3.3.3。
- Router ID 与 Loopback 相同。

## 故障 1：邻居卡在 Idle

- 现象：R1 的 peer 10.2.2.2 状态 Idle，MsgRcvd/MsgSent 都是 0；`display tcp status` 里 179 只有 Listening，没有发出的连接。
- 定位：R1 的 ping、路由、接口都没问题，问题在 R2。R2 的 `display bgp peer` 头两行暴露了答案。
- 根因：R2 的配置是从 R1 复制过来改了一半——Router ID 还是 10.1.1.1，跟 R1 撞车；AS 号抄成 6501，少了个 0。
- 修复：R2 上 `undo bgp 6501`，重建 `bgp 65001`，router-id 改成 10.2.2.2，peer 重新配。
- 教训：复制配置改一半是最容易错的。邻居起不来，先看 `display bgp peer` 头两行的 Router ID 和 AS 号。

## 故障 2：R2 ping 不通 8.8.8.8，R3 没把路由发出来

- 现象：R2–R3 已 Established，但 R2 没有 8.8.8.8 的路由。
- 定位：R3 的 `display ip routing-table 8.8.8.8` 是空的，R3 自己就没有这条路由。
- 根因：BGP 的 `network` 命令不会凭空造路由，它只发布本地路由表里已经有的路由。R3 从来没配过 8.8.8.8，所以 `network 8.8.8.8` 是空的。
- 修复：R3 上加一个 LoopBack1 模拟这个地址。
  ```
  interface LoopBack1
   ip address 8.8.8.8 255.255.255.255
  ```
- 教训：`network` 是把已有路由“搬进”BGP，不是造路由。

## 故障 3：R1 ping 不通，下一跳不可达

- 现象：R2 有了 8.8.8.8 的路由，也发给了 R1，但 R1 ping 还是不通。
- 定位：R1 的 `display bgp routing-table 8.8.8.8` 里，下一跳是 10.0.23.3，R1 没有去 10.0.23.0/24 的路由。
- 根因：iBGP 默认不改下一跳，R1 收到的 8.8.8.8 下一跳还是 R3 的 10.0.23.3。
- 修复：R2 上让它发给 R1 时把下一跳改成自己。
  ```
  bgp 65001
   peer 10.1.1.1 next-hop-local
  ```
  注意：这句是邻居已经 Established 之后才加上去的，已发布的路由不会自动重发，必须 `reset bgp 10.1.1.1` 让邻居重建、按新规则重发，R1 的下一跳才会变成 10.2.2.2。
- 教训：改了 BGP 策略要让它生效，得 reset 或 refresh。另：这台 eNSP 不认 `refresh bgp 10.0.23.2 export` 这种写法，报错 Unrecognized command。

## 故障 4：还是不通，缺回程路由

- 现象：reset 之后 R1 的路由全对了——Original nexthop 10.2.2.2，Relay 10.0.12.2，去程通了，ping 还是 timeout。
- 定位：去程没问题，问题在回程。R1 ping 的源地址是 10.0.12.1，R3 没有去 10.0.12.0/24 的路由，回包直接丢了。
- 根因：ping 要通，去程和回程都得有路由，只通一半还是不通。
- 修复：R3 上加回程静态路由。
  ```
  ip route-static 10.0.12.0 255.255.255.0 10.0.23.2
  ```
- 教训：路由有了但 ping 不通，先查回程——目的设备有没有去 ping 源地址的路由。

## 两个问答

### 改 AS 号，BGP 会断吗？

会。华为上改 AS 号必须先 `undo bgp` 把整个进程删掉再重建，邻居先掉到 Idle；重建后 Open 报文带的 AS 对不上，对端发 Notification（Bad Peer AS）拒掉，状态在 OpenSent 和 Idle 之间翻。

### iBGP 为什么一定要用 Loopback？

Loopback 绑的是设备不是某根线，永远不会 down；配合 IGP 或静态路由多路径可达，任意一条路通邻居就不掉；TCP 的源地址必须和对端配的 peer 地址一致，`connect-interface LoopBack0` 就是固定源地址。eBGP 一般是直连单链路，TTL 默认 1，用直连接口就行。

## 通用排障顺序（今晚验证过的）

邻居状态 → 有没有收到路由 → 下一跳可达吗 → 去程通吗 → 回程通吗

## 排障题进展

- 排障题 1（ACL 挡 179）：已做。状态一度还显示 Established（Hold 180 秒没到）；TCP 不通；删 ACL 后约 60 秒恢复，UpTime 重新计时。
- 排障题 2（改 AS 号，卡 OpenSent）：已做。R2 的 state 是 Active（故障时状态会在 Idle/Connect/Active/OpenSent 之间翻，看的是哪个瞬间；undo 重建期间 R3 的 BGP 没起来，TCP 连不上就显示 Active）。邻居恢复后 R1 学不到 8.8.8.8，确认是重建时漏了 network 8.8.8.8，补上后 R1 ping 通。教训：undo bgp 会清空全部 BGP 配置，重建时按清单补：router-id、peer、network。
- 排障题 3（iBGP 错源接口）：已做。R1 上删掉 connect-interface 后邻居起不来（TCP 源地址变成 10.0.12.1，对端只认 10.1.1.1）；直连链路断掉 iBGP 就断；用 Loopback 建邻居且有备用路径时，链路断了邻居不断。
