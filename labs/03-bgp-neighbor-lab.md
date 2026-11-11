# 实验：BGP 第 1 讲 — 邻居建立（eNSP / HCL）

日期：2026-11-08
修订：2026-11-08，按用户定的编址规范统一，并补齐 R2、R3 缺的接口地址
环境：Win11 笔记本，eNSP / HCL（用户 2026-11-08 确认）
设备：华为 AR / NE 模拟器均可，接口号以实际为准

## 编址规范（以后所有实验都按这个来）

- 直链：10.0.XY.0/24，X、Y 是两端设备编号，主机位取设备编号。如 R1–R2 用 10.0.12.0/24（R1 .1，R2 .2），R2–R3 用 10.0.23.0/24（R2 .2，R3 .3）。
- Loopback：10.n.n.n/32，n 是设备编号。R1 10.1.1.1，R2 10.2.2.2，R3 10.3.3.3。
- Router ID 与 Loopback 相同。

## 拓扑

```
        AS 65001                    AS 65002
   R1 —————— R2 —————— R3(ISP)
  10.0.12.1  10.0.12.2 / 10.0.23.2   10.0.23.3
  Lo0 10.1.1.1   Lo0 10.2.2.2      Lo0 10.3.3.3
```

- R1-R2：iBGP，用 Loopback0 建邻居，AS 65001
- R2-R3：eBGP，直连建邻居，R2 AS 65001，R3 AS 65002
- R1-R2、R2-R3 之间先配通直连 IP；iBGP 要 Loopback 可达，R1、R2 之间配静态路由（或跑 OSPF）
- R3 模拟 ISP，发布 8.8.8.8/32

## 基础配置（先做通，再做排障）

以下配置可直接粘贴：粘贴前先输入 system-view；每段接口配完有 quit；不要带 # 号行（# 行粘贴时会报错，还会让后面的命令卡在错误的视图里）。

R1：
```vrp
interface LoopBack0
 ip address 10.1.1.1 255.255.255.255
quit
interface GigabitEthernet0/0/0
 ip address 10.0.12.1 255.255.255.0
quit
ip route-static 10.2.2.2 255.255.255.255 10.0.12.2
bgp 65001
 router-id 10.1.1.1
 peer 10.2.2.2 as-number 65001
 peer 10.2.2.2 connect-interface LoopBack0
quit
return
```

R2：
```vrp
interface LoopBack0
 ip address 10.2.2.2 255.255.255.255
quit
interface GigabitEthernet0/0/0
 ip address 10.0.12.2 255.255.255.0
quit
interface GigabitEthernet0/0/1
 ip address 10.0.23.2 255.255.255.0
quit
ip route-static 10.1.1.1 255.255.255.255 10.0.12.1
bgp 65001
 router-id 10.2.2.2
 peer 10.1.1.1 as-number 65001
 peer 10.1.1.1 connect-interface LoopBack0
 peer 10.1.1.1 next-hop-local
 peer 10.0.23.3 as-number 65002
 peer 10.0.23.3 description to-ISP
quit
return
```

R3：LoopBack1 的 8.8.8.8 是为了让 network 有路由可发；回程静态路由是让 R3 能把 ping 的回包发回给 R1。
```vrp
interface LoopBack0
 ip address 10.3.3.3 255.255.255.255
quit
interface LoopBack1
 ip address 8.8.8.8 255.255.255.255
quit
interface GigabitEthernet0/0/0
 ip address 10.0.23.3 255.255.255.0
quit
ip route-static 10.0.12.0 255.255.255.0 10.0.23.2
bgp 65002
 router-id 10.3.3.3
 peer 10.0.23.2 as-number 65001
 network 8.8.8.8 255.255.255.255
quit
return
```

验证目标：
1. `display bgp peer` 三台全是 Established
2. R1 上 `display bgp routing-table 8.8.8.8` 能看到经 R2 学到的路由
3. R1 ping 8.8.8.8 通

提示：路由有了但 ping 不通，先查回程——目的设备有没有去 ping 源地址的路由。

## 保存配置（每次配完都要做）

eNSP 里设备断电或关拓扑会丢掉没保存的配置。配完先在每台设备上保存：
```
save
```
提示保存时输入 y 确认。然后在 eNSP 里保存拓扑（Ctrl+S），下次打开拓扑、启动设备，配置还在。

## 排障题 1：邻居卡在 Active

操作：在 R2 上加一条 ACL，挡掉 TCP 179。
```
acl number 3000
 rule 5 deny tcp destination-port eq 179
quit
interface GigabitEthernet0/0/1
 traffic-filter inbound acl 3000
quit
```
任务：
- 看 R2-R3 的 display bgp peer，State 是什么？
- 用 display tcp status 和 ping 验证 TCP 通不通
- 修复：删掉 ACL，邻居多久恢复？UpTime 重新计时吗？

## 排障题 2：Open 参数错，卡在 OpenSent

操作：把 R3 的 AS 号故意配错。注意：华为上改 AS 号不能只改一行，必须先 undo 掉
整个 BGP 进程再重建，所以邻居会先断开；重建后因为 AS 对不上，Open 报文被拒。
```
undo bgp 65002
bgp 65003
 router-id 10.3.3.3
 peer 10.0.23.2 as-number 65001
 network 8.8.8.8 255.255.255.255
```
任务：
- 看 R2 的 display bgp peer，State 是什么？Notification 里报什么错？
- 用 display bgp peer verbose 看对端 AS 号
- 修复：改回 65002（同样先 undo bgp 65003 再重建，peer 和 network 都要重新配），邻居恢复后检查 R1 是否重新学到 8.8.8.8

## 排障题 3：iBGP 用错源接口

操作：R1 上删掉 connect-interface LoopBack0，改成直连接口建 iBGP。
```
undo peer 10.2.2.2 connect-interface LoopBack0
```
任务：
- 邻居还能起来吗？为什么？（提示：TCP 源地址变了，对端认不认？）
- 关掉 R1-R2 的直连链路，iBGP 会怎样？再用 Loopback 建，有备用路径时还会断吗？
- 修复：改回 LoopBack0，写下你的结论：iBGP 为什么一定要用 Loopback？

## 实验结论（做完后填写）

- eBGP / iBGP 是否都 Established：是（2026-11-08 晚），R1 ping 8.8.8.8 通
- 排障题 1（ACL 挡 179）：已做。现象：ACL 加上后状态一度还显示 Established（Hold 定时器 180 秒没到，BGP 还没发现对端死了）；TCP 不通（R3 的 Keepalive/Update 到不了 R2）；删掉 ACL 后约 60 秒恢复，UpTime 重新计时。
- 排障题 2：已做。现象：R2 的 state 是 Active（不是 OpenSent——故障时状态会在 Idle/Connect/Active/OpenSent 之间翻，取决于查看时机；undo 重建期间 R3 的 BGP 没起来，TCP 连不上就显示 Active）。邻居恢复后 R1 学不到 8.8.8.8，确认是重建 R3 的 BGP 时漏了 network 8.8.8.8，补上后 R1 ping 通。
- 排障题 3：已做。现象：R1 上删掉 connect-interface 后邻居起不来（TCP 源地址变成 10.0.12.1，对端只认 10.1.1.1）；直连链路断掉 iBGP 就断；用 Loopback 建邻居且有备用路径时，链路断了邻居不断。
- 3 道排障题各花了多久定位：
- 哪道题最容易错，下次先查什么：
