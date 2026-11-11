# 知识点：BGP 第 1 讲 — 邻居建立与 FSM（深度版）

日期：2026-11-08
所属月份/阶段：第 1 个月 / BGP 7 讲之 1
标准：5 关全过才算掌握（讲清、盲配、排障 3 案、设计、面试 10 题）

## 核心概念

### BGP 是什么协议

- BGP 是 EGP，AS 之间传路由的协议。TCP 179 端口，面向连接，可靠。
- 和 OSPF 的区别：OSPF 是 IGP，在 AS 内算最短路；BGP 是策略路由，在 AS 间按策略选路，不只看开销。
- eBGP：不同 AS 之间，TTL 默认 1，直连为主；iBGP：同一 AS 内，TTL 默认 255，一般用 Loopback 建邻居。

### 5 种报文

- Open：建邻居时交换参数 — 版本、AS 号、Hold Time、Router ID、认证、可选参数。
- Update：传路由 + 撤销路由。只传增量，不是周期全量。
- Notification：出错时发，告诉对方错在哪，然后断邻居。
- Keepalive：保活，默认 60 秒发一次，确认对方还活着。
- Route-refresh：请求对方重发路由，用于策略改了之后不重启邻居就刷新。

### FSM：6 个状态

Idle → Connect → Active → OpenSent → OpenConfirm → Established

- Idle：初始态。拒绝所有连接，等启动事件（手动 start、或有路由要发）。出错回 Idle 会清掉所有资源。
- Connect：正在建 TCP 连接。TCP 建好了发 Open，进 OpenSent；TCP 建失败，进 Active；超时或出错，回 Idle。
- Active：TCP 建失败后重试。一直在尝试主动连对方。如果对方主动连过来，也能进 OpenSent。
- OpenSent：TCP 已建，等对方的 Open。收到正确的 Open，进 OpenConfirm；收到错的 Open，发 Notification 回 Idle。
- OpenConfirm：等对方的 Keepalive。收到 Keepalive，进 Established；Hold Timer 超时，回 Idle。
- Established：正常工作态。收发 Update、Keepalive。收到 Notification 或 TCP 断了，回 Idle。

记住口诀：Idle 等启动，Connect 连 TCP，Active 重试连，OpenSent 等 Open，OpenConfirm 等 Keepalive，Established 传路由。

### 定时器

- Keepalive 默认 60 秒，Hold Time 默认 180 秒，Hold 是 Keepalive 的 3 倍。
- 协商时取两边 Hold Time 里小的那个；如果一方配 0，Hold Time 不生效，邻居永不断（危险，别这么配）。
- eBGP 直连检测：默认 TTL 1，跨设备要配 ebgp-max-hop。

## 关键结论 / 容易记混的点

- BGP 邻居不起来，先看 TCP 179 通不通，再看 Open 参数对不对，最后看路由可达。顺序不能乱。
- iBGP 一定要用 Loopback 建邻居 + update-source，不然一根链路断了邻居就断了；eBGP 一般用直连接口。
- Router ID 选举：手动配的最优先，其次 Loopback 最大的 IP，其次物理接口最大的 IP。邻居两边 Router ID 不能一样。
- AS 号错一个数字，Open 就被拒，状态卡在 OpenSent / Active。
- 认证对不上，Notification 会告诉你，状态直接回 Idle。
- Hold Time 不是越大越好：太小容易误断，太大故障发现慢。生产常用 90/30 或 180/60。
- BGP 邻居起来不代表有路由：Established 只是通道通了，路由还要看 import/export 策略、下一跳可达、同步规则（华为默认不检查 IGP 同步）。

## 华为 VRP 配置（盲配目标）

场景：R1 AS 65001，R2 AS 65002，eBGP 直连；R1-R3 是 iBGP，用 Loopback（R1 10.1.1.1，R3 10.3.3.3）。

```vrp
# R1
bgp 65001
 router-id 10.1.1.1
 peer 10.0.12.2 as-number 65002
 peer 10.0.12.2 description to-R2-ISP
 peer 10.0.12.2 password cipher <认证密码>
 peer 10.3.3.3 as-number 65001
 peer 10.3.3.3 connect-interface LoopBack0
 peer 10.3.3.3 description to-R3-iBGP
```

验证：

```vrp
display bgp peer
# State 必须是 Established，UpTime 在走，MsgRcvd / MsgSent 在涨

display bgp peer verbose
# 看 Hold Time、Keepalive、Router ID、认证、收到的路由数

display tcp status
# 看 179 端口的 TCP 连接是不是 Established
```

## 排障思路（面试常考）

- display bgp peer 看 State：卡在哪个状态，就查那一步。
  - Idle：BGP 没启动、peer 没配、对方地址不可达
  - Active：TCP 179 不通 — 查 ACL、防火墙、源接口、下一跳路由
  - OpenSent：Open 参数错 — AS 号、Router ID 冲突、Hold Time、认证
  - OpenConfirm：Keepalive 没收到 — Hold Timer、链路丢包
  - Established 但一会又断：Hold Time 太小、链路抖动、CPU 高导致 Keepalive 发不出去
- 先查 TCP，再查 Open，最后查路由。别一上来就改策略。
- 改了策略不用重启邻居：peer route-policy 改完，用 refresh bgp all import / export 或 peer x refresh 触发 Route-refresh。

## 自测题（BGP-1 面试题，10 道，目标全对）

1. BGP 用什么传输协议、哪个端口？为什么不用 UDP？
2. FSM 6 个状态各是什么意思？卡在 Active 和卡在 OpenSent，原因有什么不同？
3. Open 报文里协商哪几个参数？哪个对不上会直接拒？
4. Keepalive 和 Hold Time 默认各是多少？协商规则是什么？
5. eBGP 和 iBGP 建邻居，TTL 和源接口有什么不同？为什么 iBGP 要用 Loopback？
6. Router ID 怎么选？两边一样会怎样？
7. 邻居 Established 了，但 display bgp routing-table 里没有路由，可能的原因有哪些？
8. 改了 import 策略，怎么不重启邻居就让它生效？
9. BGP 邻居频繁 flapping，Hold Time 太小和链路丢包分别怎么判断？
10. 给你一个双出口场景，画出 eBGP + iBGP 拓扑，标出每个邻居的 AS 号、源接口、认证。

## 还没搞懂 / 下一步

下一步：BGP 第 2 讲 — 路由发布与选路全属性（先做完本讲实验 lab 03）。
