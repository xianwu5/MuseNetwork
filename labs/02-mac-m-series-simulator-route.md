# 实验环境路线：M 系列 Mac 上用 eNSP / EVE-NG / HCL

日期：2026-11-04
结论：三者都没有 macOS 原生版；M 系列 Mac 本地跑 x86 模拟器是弱项，推荐用一台 x86 机器做实验服务器，Mac 只做浏览器访问。

## 为什么 M 系列本地难跑

- eNSP、HCL 是 Windows 软件，HCL 官方建议 Win10 + 自带 VirtualBox 6.0.14。
- EVE-NG 官方不支持 Mac ARM 系列，原因涉及 VMware Fusion 和嵌套 CPU。
- UTM 可以模拟 x86，但模拟开销大，且 EVE-NG 里再跑虚拟路由器时常缺嵌套虚拟化支持，路由器可能起不来。

## 推荐路线：x86 实验服务器 + Mac 浏览器

1. 准备一台 x86 机器：旧 Intel 电脑、二手迷你主机，或者公司/家里闲置的 Windows 电脑。
2. 在上面装 EVE-NG：用 EVE-NG 官方 ISO 裸机安装，或在 Ubuntu 20.04 上安装；内存建议至少 16GB，跑多台路由器时越大越好。
3. 把实验服务器和 Mac 连到同一个局域网，记下服务器 IP。
4. Mac 上打开浏览器访问 `https://<服务器IP>`，登录 EVE-NG，在网页里画拓扑、加设备、连线、开机。
5. 华为镜像需要自己从合法渠道准备，EVE-NG 本身不自带厂商镜像。
6. 我们的 PBR 实验（PC1 走专线、其他走默认路由）就按这个方式在 EVE-NG 里搭。

## eNSP / HCL 的安排

- eNSP、HCL 放在那台 Windows x86 机器上装，不要硬塞进 M 系列 Mac 的 Windows ARM 虚拟机里。
- 如果只有一台 x86 机器，可以在上面同时装 Windows + HCL/eNSP，或者分开：一台跑 EVE-NG，一台跑 Windows。

## 不推荐的本地折腾路线

- M 系列 Mac + UTM 模拟 x86 Windows，再在里面装 VirtualBox / EVE-NG：能装上不代表能稳定跑，性能和嵌套虚拟化都可能卡住。
- M 系列 Mac + Parallels / VMware Fusion 装 Windows 11 ARM：日常 Windows 应用可以跑，但 eNSP/HCL 依赖的 VirtualBox x86 虚拟化层仍然是短板。

## 下一步待确认

- 是否已有闲置 x86 机器或服务器可用？
- 如果没有，是否接受二手迷你主机或云上带嵌套虚拟化的裸金属/专属主机方案？普通不支持嵌套虚拟化的云 VPS 不适合直接装 EVE-NG。
