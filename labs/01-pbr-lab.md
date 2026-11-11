# 实验：PBR 按源地址分流

日期：2026-11-04
目标：验证同一目的地址下，指定源网段走专线、其他流量走默认路由。

## 拓扑

- PC1：10.1.0.10/16，接 R1 入接口
- PC2：192.168.1.10/24，接 R1 入接口
- R1 到专线下一跳：172.16.1.2
- R1 到默认出口下一跳：172.16.2.2
- 测试目标：203.0.113.10（用 TEST-NET-3 地址段做实验目标，不要用真实公网业务地址）
- R1 上需要有一条到 203.0.113.0/24 的路由，下一跳指向默认出口方向，否则 PBR 之外的流量无路可走。

实验环境：华为设备（VRP），eNSP / EVE-NG 等模拟器均可。接口号以实际设备为准，以下用 GigabitEthernet0/0/0 举例。

## 配置（华为 VRP，R1）

```
acl number 3001
 rule 5 permit ip source 10.1.0.0 0.0.255.255 destination 203.0.113.10 0
#
policy-based-route PBR permit node 10
 if-match acl 3001
 apply ip-address next-hop 172.16.1.2
#
policy-based-route PBR permit node 20
#
interface GigabitEthernet0/0/0
 description 接 PC 侧
 ip policy-based-route PBR
```

说明：

- ACL 3001 是高级 ACL，3000-3999 段；通配符掩码里 0 表示必须匹配、255 表示任意。
- node 10 只匹配 PC1 网段去往测试目标的流量，强制走专线。
- node 20 没有 if-match 条件，相当于放行其余流量走正常路由表。
- 策略应用在接 PC 的接口上；如果是设备自己产生的流量，改用本地策略路由。
- 华为的下一跳失效回退要结合具体版本看：先做断链路演练，再根据设备支持的检测方式补兜底，不要凭空套用其他厂商的 track 语法。

## 配置对照（Cisco，仅在 Cisco 设备上用，不要套用到华为 R1）

```
access-list 101 permit ip 10.1.0.0 0.0.255.255 host 203.0.113.10

route-map PBR permit 10
 match ip address 101
 set ip next-hop 172.16.1.2
route-map PBR permit 20

interface GigabitEthernet0/0
 description 接 PC 侧
 ip policy route-map PBR
```

说明：

- 序号 10 只匹配 PC1 网段去往测试目标的流量，强制走专线。
- 序号 20 没有 match 条件，相当于放行其余流量走正常路由表。
- 策略应用在接 PC 的入接口上。

## 验证步骤

1. PC1 ping / tracert 203.0.113.10，路径应经过 172.16.1.2。
2. PC2 ping / tracert 同一目标，路径应经过默认出口 172.16.2.2。
3. 华为验证：`display policy-based-route PBR` 看 node 10 是否匹配；`display acl 3001` 看规则命中计数；`display ip routing-table 203.0.113.10` 确认路由表本身没有被 PBR 改掉。
4. Cisco 对照验证：`show route-map PBR`、`show ip policy`、`show ip route 203.0.113.10`（仅在 Cisco 设备上用）。

## 故障演练：下一跳失效

1. 关掉专线下一跳方向的接口或链路。
2. PC1 再访问测试目标，观察是否中断。
3. 思考改进：给 set ip next-hop 配 track / verify-availability，或者改用兜底设计，让失效时能回退到默认路由。
4. 恢复链路后，再验证 PC1 回到专线路径。

## 实验结论（做完后填写）

- PBR 是否按源地址分流成功：
- 路由表是否被改动：
- 下一跳失效时的表现和改进办法：
