# 知识点：BGP Local Preference 与 AS_PATH 选路

日期：2026-11-08
所属月份/阶段：第 1 个月 / 补短板（BGP）

## 核心概念

一句话：Local Preference 管我们 AS 的流量从哪个出口出去，AS_PATH 长短管别人怎么选进来，两者作用方向相反，优先级也不同。

### Local Preference

- BGP 的公认任意属性（Well-known Discretionary），只在本地 AS 内有效。
- 不会传给 eBGP 邻居，只会在 iBGP 之间传递。
- 默认值 100，值越大越优先。
- 作用：同一个目的前缀从多个 eBGP 邻居学到时，选 Local Preference 高的那条，决定本 AS 的出站出口。

### AS_PATH

- BGP 的公认强制属性（Well-known Mandatory），记录路由经过的 AS 号列表。
- 两个作用：防环（看到自己的 AS 号就丢弃）；选路（路径越短越优先）。
- 只能在 Local Preference 之后比。如果 Local Preference 不同，AS_PATH 再短也没用。

### 华为 BGP 选路顺序（从先到后）

1. PrefVal 越大越优先（华为私有，默认值 0，只在本地设备有效，优先级高于 Local Preference）
2. Local Preference 越大越优先
3. 本地始发的路由优先（network / aggregate / import 产生的，优先于从邻居学来的）
4. AS_PATH 越短越优先
5. Origin 类型：IGP > EGP > Incomplete
6. MED 越小越优先（默认只比较来自同一个相邻 AS 的路由）
7. eBGP 路由优先于 iBGP 路由
8. 到下一跳的 IGP 开销越小越优先
9. Router ID 越小越优先，其次 Cluster List 最短、Originator ID 最小、对端地址最小

记住前 4 个就够应付大部分选路题：PrefVal → Local Preference → 本地始发 → AS_PATH。

更正（2026-11-09）：上面是简版，完整顺序见 06 笔记——最前面要先丢弃下一跳不可达的路由；第 3 步“本地始发”内部还有顺序（聚合 > 汇总 > network > import > 学到的）；AS_PATH 前面还有 AIGP。

## 关键结论 / 容易记混的点

- Local Preference 只管出站，不管入站。想让别人少走某条链路进来，不能靠 Local Preference，要靠 AS_PATH Prepend 或 MED。
- Local Preference 要在从 eBGP 邻居收路由的 import 方向上设，设完才会通过 iBGP 传给 AS 内的其他路由器。在 export 给 eBGP 的方向上设是白设，对方收不到。
- AS_PATH Prepend 是在 export 方向上人为把自己的 AS 号多加几次，让路径变长，别人就不爱选这条路。加的是自己的 AS 号，不是别人的。
- PrefVal 是华为的本地概念，只对本设备生效，不会传给任何邻居。排障时如果 Local Preference 明明设高了却不生效，先看 PrefVal 是不是被别的策略改过。
- 默认 100：只给想优先的那条设 200 就够了，另一条保持默认 100，不用两边都设。

## 实验 / 例子

场景：企业 AS 65001，双出口。ISP-A（AS 100，1.1.1.1）是主出口，ISP-B（AS 200，2.2.2.2）是备用。出站想优先走 ISP-A。

```vrp
# 先定义 route-policy，只给从 ISP-A 学到的路由提 Local Preference
route-policy ISP-A-IN permit node 10
 apply local-preference 200
#
route-policy ISP-A-IN permit node 20
# node 20 空匹配 = 放行其余路由，保持默认 100
#
bgp 65001
 router-id 10.1.1.1
 peer 1.1.1.1 as-number 100
 peer 1.1.1.1 route-policy ISP-A-IN import
 peer 2.2.2.2 as-number 200
 #
 # 想让外面进来时少走 ISP-B，在发给 ISP-B 的方向上做 Prepend
 peer 2.2.2.2 route-policy ISP-B-OUT export
#
route-policy ISP-B-OUT permit node 10
 apply as-path 65001 65001 additive
#
route-policy ISP-B-OUT permit node 20
```

验证：

```vrp
display bgp routing-table
# 看同一前缀的两条路由，LocPrf 一列：走 ISP-A 的是 200，走 ISP-B 的是 100，带 * 的是最优

display bgp routing-table 8.8.8.8
# 看 AS-Path 和 LocPrf 细节

display ip routing-table 0.0.0.0
# 确认默认路由的下一跳是不是 ISP-A
```

结果预期：出站流量走 ISP-A；ISP-A 挂了，ISP-B 的 100 顶上，自动切换。

## 排障思路

- Local Preference 设了不生效：先看 route-policy 是不是挂在 import 方向，再看有没有漏写最后的 permit node（route-policy 默认隐含 deny，漏了会把其他路由都挡掉）。
- 选路结果和预期相反：按华为选路顺序一层层查，先看 PrefVal，再看 Local Preference，不要一上来就盯 AS_PATH。
- 想调入站却改了 Local Preference：方向错了。入站调优用 AS_PATH Prepend 或 MED，Local Preference 出不了 AS。
- Prepend 加完没效果：对端可能有自己的 Local Preference 策略，优先级高于 AS_PATH；或者 Prepend 挂错了方向（应该挂在 export，不是 import）。

## 自测题

1. 同一前缀从两个 ISP 学到，Local Preference 分别是 200 和 100，AS_PATH 分别是 3 跳和 1 跳，哪条最优？为什么？
2. 想让本 AS 的出站流量优先走 ISP-A，应该在哪个方向、哪个邻居上挂 route-policy？
3. 想让外部流量少从 ISP-B 进来，应该改 Local Preference 还是做 AS_PATH Prepend？挂在哪个方向？
4. 华为设备上，一条路由 PrefVal 是 10、Local Preference 是 200，另一条 PrefVal 是 0、Local Preference 是 300，哪条最优？

## 还没搞懂 / 下一步

下一步：TCP 快速重传和拥塞控制（测评错题之二）。
