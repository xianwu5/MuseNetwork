#!/usr/bin/env python3
"""Draw diagrams for the Obsidian tutorial (PIL, Noto Sans CJK SC)."""
from PIL import Image, ImageDraw, ImageFont

REG = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
BOLD = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"

NAVY = (27, 58, 95)
NAVY_D = (16, 38, 66)
CREAM = (255, 248, 236)
AMBER = (242, 194, 48)
BLUE = (70, 130, 200)
BLUE_L = (220, 232, 245)
GREEN = (46, 139, 87)
GREEN_L = (214, 240, 222)
GREY = (90, 90, 90)
INK = (34, 34, 34)
WHITE = (255, 255, 255)
RED = (200, 60, 60)

OUT = "assets"


def font(size, bold=False):
    return ImageFont.truetype(BOLD if bold else REG, size, index=2)


def tc(d, cx, y, s, f, fill):
    w = d.textlength(s, font=f)
    d.text((cx - w / 2, y), s, font=f, fill=fill)


def tl(d, x, y, s, f, fill):
    d.text((x, y), s, font=f, fill=fill)


def rbox(d, box, fill, outline=None, width=2, radius=18):
    d.rounded_rectangle(box, radius=radius, fill=fill,
                        outline=outline, width=width)


def arrow(d, x1, y1, x2, y2, fill=NAVY, width=5):
    d.line([(x1, y1), (x2, y2)], fill=fill, width=width)
    # arrowhead
    import math
    ang = math.atan2(y2 - y1, x2 - x1)
    for da in (2.6, -2.6):
        d.line([(x2, y2),
                (x2 - 26 * math.cos(ang + da), y2 - 26 * math.sin(ang + da))],
               fill=fill, width=width)


def cover():
    W, H = 1240, 1656
    im = Image.new("RGB", (W, H), NAVY)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W, 10], fill=AMBER)
    tc(d, W // 2, 210, "数据中心网工 · 笔记整合", font(46), fill=(159, 180, 216))
    tc(d, W // 2, 420, "Obsidian", font(170, bold=True), fill=WHITE)
    tc(d, W // 2, 600, "使用教程", font(170, bold=True), fill=WHITE)
    d.rectangle([W // 2 - 110, 830, W // 2 + 110, 838], fill=AMBER)
    tc(d, W // 2, 890, "从 Flomo / 语雀", font(56), fill=WHITE)
    tc(d, W // 2, 980, "收进一个本地知识库", font(56), fill=WHITE)
    tc(d, W // 2, 1150, "以 MuseNetwork 文件夹为起点", font(44), fill=(159, 180, 216))
    tc(d, W // 2, 1230, "Mac + Win11 双设备 · 7 天练会双链", font(44), fill=(159, 180, 216))
    tc(d, W // 2, 1480, "本地 Markdown · 免费 · 全程离线", font(40), fill=(159, 180, 216))
    im.save(f"{OUT}/cover.png")


def vault():
    W, H = 1240, 940
    im = Image.new("RGB", (W, H), CREAM)
    d = ImageDraw.Draw(im)
    tc(d, W // 2, 36, "MuseNetwork 文件夹 = 一个现成的保险库", font(46, bold=True), fill=NAVY)
    # folder box
    rbox(d, [70, 130, 640, 820], fill=WHITE, outline=NAVY, width=3)
    tc(d, 355, 150, "MuseNetwork /", font(40, bold=True), fill=NAVY)
    lines = [
        ("notes /", NAVY, True),
        ("  00 测评 3/8", INK, False),
        ("  01 路由策略和策略路由", INK, False),
        ("  02 BGP Local Preference", INK, False),
        ("  03 TCP 快速重传", INK, False),
        ("  04 BGP 邻居建立与 FSM", INK, False),
        ("labs /", NAVY, True),
        ("  01 PBR 按源分流", INK, False),
        ("  02 实验环境", INK, False),
        ("  03 BGP 邻居实验", INK, False),
        ("plan.md  半年计划", INK, False),
        ("guides /  本教程", INK, False),
    ]
    y = 220
    for s, col, b in lines:
        tl(d, 100, y, s, font(34, bold=b), fill=col)
        y += 48
    # arrow
    arrow(d, 670, 470, 800, 470, fill=AMBER, width=8)
    # vault box
    rbox(d, [830, 300, 1170, 640], fill=NAVY, outline=NAVY, width=3)
    tc(d, 1000, 330, "Obsidian", font(52, bold=True), fill=WHITE)
    tc(d, 1000, 420, "保险库", font(52, bold=True), fill=WHITE)
    tc(d, 1000, 520, "直接打开", font(36), fill=AMBER)
    tc(d, 1000, 570, "不用导入", font(36), fill=AMBER)
    tc(d, W // 2, 860, "文件还是原来的 .md，Obsidian 只是给它们加了链接和视图",
       font(34), fill=GREY)
    im.save(f"{OUT}/vault.png")


def interface():
    W, H = 1240, 860
    im = Image.new("RGB", (W, H), CREAM)
    d = ImageDraw.Draw(im)
    tc(d, W // 2, 30, "Obsidian 界面：一眼看懂的 4 个部分", font(46, bold=True), fill=NAVY)
    # window
    rbox(d, [60, 120, 1180, 760], fill=WHITE, outline=NAVY, width=3)
    d.rectangle([60, 120, 1180, 168], fill=NAVY)
    tc(d, 620, 128, "Obsidian — MuseNetwork", font(32, bold=True), fill=WHITE)
    # left sidebar
    d.rectangle([60, 168, 320, 715], fill=BLUE_L)
    tc(d, 190, 190, "左侧栏", font(36, bold=True), fill=NAVY)
    for i, s in enumerate(["notes /", "labs /", "plan.md", "网络学习地图"]):
        tl(d, 90, 250 + i * 52, s, font(30), fill=INK)
    # center
    d.line([(320, 168), (320, 715)], fill=NAVY, width=2)
    tc(d, 620, 190, "中间：编辑器", font(36, bold=True), fill=NAVY)
    tl(d, 350, 260, "# BGP Local Preference", font(32, bold=True), fill=INK)
    tl(d, 350, 310, "默认值 100，值越大越优先……", font(30), fill=INK)
    tl(d, 350, 360, "见 [[BGP 邻居建立与 FSM]]", font(30), fill=BLUE)
    # right sidebar
    d.line([(920, 168), (920, 715)], fill=NAVY, width=2)
    d.rectangle([920, 168, 1180, 715], fill=GREEN_L)
    tc(d, 1050, 190, "右侧栏", font(36, bold=True), fill=NAVY)
    tl(d, 940, 250, "反向链接", font(30, bold=True), fill=INK)
    tl(d, 940, 300, "· BGP 邻居 FSM", font(28), fill=INK)
    tl(d, 940, 340, "· 路由策略", font(28), fill=INK)
    tl(d, 940, 380, "· 网络学习地图", font(28), fill=INK)
    tl(d, 940, 440, "大纲", font(30, bold=True), fill=INK)
    tl(d, 940, 490, "· 核心概念", font(28), fill=INK)
    tl(d, 940, 530, "· 选路顺序", font(28), fill=INK)
    # status bar
    d.rectangle([60, 715, 1180, 760], fill=NAVY)
    tl(d, 90, 726, "字数 1,240  ·  已同步  ·  反向链接 3 条", font(26), fill=WHITE)
    tc(d, W // 2, 790, "左侧找文件，中间写笔记，右侧看谁链了我，底部看状态",
       font(34), fill=GREY)
    im.save(f"{OUT}/interface.png")


def linking():
    W, H = 1240, 900
    im = Image.new("RGB", (W, H), CREAM)
    d = ImageDraw.Draw(im)
    tc(d, W // 2, 30, "双链：写一次，两边都连上", font(46, bold=True), fill=NAVY)
    # note A
    rbox(d, [60, 120, 560, 480], fill=WHITE, outline=NAVY, width=3)
    tc(d, 310, 140, "02-bgp-local-pref.md", font(34, bold=True), fill=NAVY)
    tl(d, 90, 210, "Local Preference 默认 100，", font(30), fill=INK)
    tl(d, 90, 255, "值越大越优先。", font(30), fill=INK)
    tl(d, 90, 320, "邻居怎么建，见", font(30), fill=INK)
    tl(d, 90, 365, "[[BGP 邻居建立与 FSM]]", font(32, bold=True), fill=BLUE)
    # note B
    rbox(d, [680, 120, 1180, 480], fill=WHITE, outline=NAVY, width=3)
    tc(d, 930, 140, "04-bgp-neighbor-fsm.md", font(34, bold=True), fill=NAVY)
    tl(d, 710, 210, "邻居到 Established 才能", font(30), fill=INK)
    tl(d, 710, 255, "传路由。", font(30), fill=INK)
    tl(d, 710, 320, "选路看", font(30), fill=INK)
    tl(d, 710, 365, "[[BGP Local Preference]]", font(32, bold=True), fill=BLUE)
    # arrows between
    arrow(d, 570, 250, 670, 250, fill=BLUE, width=6)
    tc(d, 620, 200, "正向", font(28, bold=True), fill=BLUE)
    arrow(d, 670, 330, 570, 330, fill=GREEN, width=6)
    tc(d, 620, 350, "反向", font(28, bold=True), fill=GREEN)
    tc(d, 620, 290, "自动", font(28, bold=True), fill=GREEN)
    # bottom: red link
    rbox(d, [60, 560, 1180, 800], fill=WHITE, outline=RED, width=3)
    tc(d, 620, 580, "[[还没写的笔记]] 显示红色，点一下就新建", font(36, bold=True), fill=RED)
    tc(d, 620, 650, "先写链接，再补内容 —— 笔记是这样长出来的", font(34), fill=INK)
    tc(d, 620, 710, "反向链接面板：不用自己维护，谁链了我一目了然", font(34), fill=GREY)
    im.save(f"{OUT}/linking.png")


def graph():
    W, H = 1240, 920
    im = Image.new("RGB", (W, H), CREAM)
    d = ImageDraw.Draw(im)
    tc(d, W // 2, 30, "关系图谱：5 篇笔记 + 2 个实验，一张图看清", font(46, bold=True), fill=NAVY)
    cx, cy = 620, 480
    nodes = [
        ("网络学习地图", cx, cy, AMBER, NAVY, True),
        ("00 测评 3/8", 260, 200, BLUE_L, NAVY, False),
        ("01 路由策略", 620, 170, BLUE_L, NAVY, False),
        ("02 BGP 选路", 980, 200, BLUE_L, NAVY, False),
        ("03 TCP 快重传", 260, 760, BLUE_L, NAVY, False),
        ("04 BGP 邻居 FSM", 980, 760, BLUE_L, NAVY, False),
        ("实验 PBR", 620, 860, GREEN_L, NAVY, False),
        ("实验 BGP 邻居", 1050, 480, GREEN_L, NAVY, False),
    ]
    # edges first
    for name, x, y, *_ in nodes[1:]:
        d.line([(cx, cy), (x, y)], fill=(180, 190, 205), width=3)
    d.line([(260, 200), (620, 170)], fill=(180, 190, 205), width=3)
    d.line([(620, 170), (980, 200)], fill=(180, 190, 205), width=3)
    d.line([(980, 200), (980, 760)], fill=(180, 190, 205), width=3)
    d.line([(260, 760), (980, 760)], fill=(180, 190, 205), width=3)
    d.line([(980, 760), (1050, 480)], fill=(180, 190, 205), width=3)
    # nodes
    for name, x, y, fill, fg, big in nodes:
        w, h = (300, 84) if big else (250, 66)
        rbox(d, [x - w // 2, y - h // 2, x + w // 2, y + h // 2],
             fill=fill, outline=NAVY, width=3)
        tc(d, x, y - 22 if big else y - 18, name, font(34 if big else 30, bold=True), fill=fg)
    im.save(f"{OUT}/graph.png")


def migration():
    W, H = 1240, 860
    im = Image.new("RGB", (W, H), CREAM)
    d = ImageDraw.Draw(im)
    tc(d, W // 2, 30, "搬家：3 天收进一个库", font(46, bold=True), fill=NAVY)
    # sources
    rbox(d, [60, 130, 400, 420], fill=WHITE, outline=NAVY, width=3)
    tc(d, 230, 150, "Flomo", font(44, bold=True), fill=NAVY)
    tc(d, 230, 220, "平时的小想法", font(32), fill=INK)
    tc(d, 230, 270, "MEMO 导出", font(32), fill=GREY)
    tc(d, 230, 330, "→ 每日笔记", font(32, bold=True), fill=BLUE)
    rbox(d, [60, 470, 400, 760], fill=WHITE, outline=NAVY, width=3)
    tc(d, 230, 490, "语雀", font(44, bold=True), fill=NAVY)
    tc(d, 230, 560, "网络学习笔记", font(32), fill=INK)
    tc(d, 230, 610, "导出 Markdown", font(32), fill=GREY)
    tc(d, 230, 670, "→ notes/ 文件夹", font(32, bold=True), fill=BLUE)
    # arrows
    arrow(d, 420, 280, 700, 330, fill=AMBER, width=8)
    arrow(d, 420, 610, 700, 560, fill=AMBER, width=8)
    # vault
    rbox(d, [720, 130, 1180, 760], fill=NAVY, outline=NAVY, width=3)
    tc(d, 950, 160, "Obsidian 保险库", font(44, bold=True), fill=WHITE)
    tc(d, 950, 240, "MuseNetwork /", font(36), fill=AMBER)
    for i, s in enumerate(["notes/  正式笔记", "daily/  每日想法",
                           "网络学习地图（MOC）", "Canvas / Bases"]):
        tl(d, 770, 320 + i * 62, "·  " + s, font(32), fill=WHITE)
    tc(d, 950, 600, "第 1 天建库  →  第 2 天导语雀", font(32, bold=True), fill=AMBER)
    tc(d, 950, 650, "→  第 3 天导 Flomo", font(32, bold=True), fill=AMBER)
    tc(d, W // 2, 800, "旧应用先留着只读一个月，确认不丢东西再卸载",
       font(34), fill=GREY)
    im.save(f"{OUT}/migration.png")


def daily():
    W, H = 1240, 780
    im = Image.new("RGB", (W, H), CREAM)
    d = ImageDraw.Draw(im)
    tc(d, W // 2, 30, "每日笔记：Flomo 的活，Obsidian 这样接", font(46, bold=True), fill=NAVY)
    steps = [
        ("1", "突然想到\n一个小想法", "比如：BGP 选路\n和 OSPF 哪里不同"),
        ("2", "打开今日日记\nCtrl / Cmd + N", "写 2 行，不用排版\n不用想放哪里"),
        ("3", "有用的想法\n加 [[链接]]", "[[BGP 选路]]\n链到正式笔记"),
        ("4", "正式笔记的\n反向链接里", "出现这条日记\n想法有了归处"),
    ]
    x = 60
    for num, title, desc in steps:
        rbox(d, [x, 140, x + 250, 560], fill=WHITE, outline=NAVY, width=3)
        d.ellipse([x + 90, 165, x + 160, 235], fill=AMBER)
        tc(d, x + 125, 178, num, font(40, bold=True), fill=NAVY)
        for i, line in enumerate(title.split("\n")):
            tc(d, x + 125, 260 + i * 46, line, font(32, bold=True), fill=NAVY)
        for i, line in enumerate(desc.split("\n")):
            tc(d, x + 125, 370 + i * 42, line, font(26), fill=GREY)
        if x + 250 < 1180:
            arrow(d, x + 262, 350, x + 300, 350, fill=AMBER, width=6)
        x += 300
    tc(d, W // 2, 620, "先捕捉，再整理 —— 想法不丢，笔记不乱", font(36, bold=True), fill=NAVY)
    tc(d, W // 2, 690, "Flomo 的习惯不用改，只是换了个地方写", font(32), fill=GREY)
    im.save(f"{OUT}/daily.png")


if __name__ == "__main__":
    cover()
    vault()
    interface()
    linking()
    graph()
    migration()
    daily()
    print("done")
