from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas


ROOT = Path(r"D:\Projects\yeye")
OUTPUT = ROOT / "hardware_preparation" / "archive" / "hardware_list_697CNY_superseded.pdf"
OUTPUT.parent.mkdir(parents=True, exist_ok=True)

pdfmetrics.registerFont(TTFont("SimHei", r"C:\Windows\Fonts\simhei.ttf"))
FONT = "SimHei"
W, H = A4


def wrapped(text, width, size):
    lines, current = [], ""
    for ch in text:
        if pdfmetrics.stringWidth(current + ch, FONT, size) <= width:
            current += ch
        else:
            lines.append(current)
            current = ch
    if current:
        lines.append(current)
    return lines


rows = [
    ("1", "STM32 NUCLEO-G474RE 主控板", "1", "原装开发板，板载 ST-LINK；负责双电机闭环与传感器采集", "167"),
    ("2", "立创庐山派 Lite-K230D-CanMV 标准套件", "1", "型号 LCKFB-LSPI-K230D-128M-CanMV；下单确认含 GC2093 摄像头和排线", "210"),
    ("3", "microSD 卡", "1", "8 GB 及以上，Class 10", "15"),
    ("4", "ICM-42688-P 六轴 IMU 模块", "1", "购买焊好的模块，不买裸芯片；支持 3.3 V、SPI", "25"),
    ("5", "N20 金属减速编码电机套装", "2 套", "两侧同型号；6 V、空载约 600-800 rpm；AB 相编码器可接 3.3 V；含轮胎和固定支架", "100"),
    ("6", "DRV8833 双路电机驱动模块", "1", "两路独立驱动；核对模块封装及每路电流，须匹配电机堵转电流", "20"),
    ("7", "底板、万向支撑球、摄像头可调支架", "各 1", "组成紧凑双轮差速车，安装后满足比赛外形限制", "35"),
    ("8", "2S 7.4 V 锂电池", "1", "约 850-1500 mAh；放电能力、插头和尺寸匹配整车", "45"),
    ("9", "2S 平衡充电器", "1", "与电池平衡接口匹配", "20"),
    ("10", "5 V 降压模块", "1", "给视觉板和主控分别并联取电；输出能力满足两板需要", "15"),
    ("11", "6 V 降压模块", "1", "给电机驱动供电；目标持续输出至少 3 A，按所选电机复核", "20"),
    ("12", "开关、插头、导线、铜柱、螺丝、热缩管、扎带", "1 批", "包括主控与视觉板的 UART 三线连接；固定电池和摄像头排线", "25"),
]

c = canvas.Canvas(str(OUTPUT), pagesize=A4)
c.setTitle("智能小车必买硬件清单")
c.setAuthor("Codex")

navy = colors.HexColor("#14283D")
muted = colors.HexColor("#526273")
blue = colors.HexColor("#1664A5")
line = colors.HexColor("#DCE3E9")

c.setFillColor(navy)
c.setFont(FONT, 20)
c.drawString(35, H - 49, "智能小车必买硬件清单")
c.setFillColor(muted)
c.setFont(FONT, 9)
c.drawString(35, H - 68, "三人队伍  |  双轮差速 + 前置视觉  |  整车预算约 700 元")
c.drawRightString(W - 35, H - 68, "2026-10-10")

c.setFillColor(colors.HexColor("#EAF3FA"))
c.roundRect(35, H - 111, W - 70, 29, 5, fill=1, stroke=0)
c.setFillColor(blue)
c.setFont(FONT, 9.3)
c.drawString(45, H - 100, "价格是单项采购目标上限，不是已锁定报价。下单前须重新核算实付总价。")

x0 = 35
widths = [28, 160, 45, 230, 62]
xs = [x0]
for width in widths:
    xs.append(xs[-1] + width)

y = H - 130
c.setFillColor(navy)
c.roundRect(x0, y - 26, sum(widths), 26, 3, fill=1, stroke=0)
c.setFillColor(colors.white)
c.setFont(FONT, 9)
for i, label in enumerate(["#", "必买硬件", "数量", "下单时核对", "目标价"]):
    c.drawString(xs[i] + 7, y - 17, label)
y -= 26

for idx, row in enumerate(rows):
    number, item, qty, spec, price = row
    item_lines = wrapped(item, widths[1] - 12, 8.2)
    spec_lines = wrapped(spec, widths[3] - 12, 8.2)
    rh = max(len(item_lines), len(spec_lines), 1) * 12 + 12
    if idx % 2 == 0:
        c.setFillColor(colors.HexColor("#F5F8FA"))
        c.rect(x0, y - rh, sum(widths), rh, fill=1, stroke=0)
    c.setFillColor(line)
    c.line(x0, y - rh, x0 + sum(widths), y - rh)
    c.setFillColor(navy)
    c.setFont(FONT, 8.2)
    c.drawString(xs[0] + 7, y - 15, number)
    for n, value in enumerate(item_lines):
        c.drawString(xs[1] + 6, y - 15 - 12 * n, value)
    c.drawString(xs[2] + 6, y - 15, qty)
    c.setFillColor(muted)
    for n, value in enumerate(spec_lines):
        c.drawString(xs[3] + 6, y - 15 - 12 * n, value)
    c.setFillColor(navy)
    c.drawRightString(xs[5] - 7, y - 15, price + " 元")
    y -= rh

c.setFillColor(colors.HexColor("#EAF3FA"))
c.rect(x0, y - 30, sum(widths), 30, fill=1, stroke=0)
c.setFillColor(navy)
c.setFont(FONT, 10)
c.drawRightString(xs[4] - 7, y - 20, "目标合计（不含运费和工具）")
c.setFillColor(blue)
c.setFont(FONT, 12)
c.drawRightString(xs[5] - 7, y - 20, "697 元")
y -= 47

c.setFillColor(navy)
c.setFont(FONT, 9)
c.drawString(35, y, "接线与采购核对")
c.setFillColor(muted)
c.setFont(FONT, 8)
notes = [
    "电池分两路：6 V 降压给电机驱动；5 V 降压给视觉板和主控；所有模块共地。",
    "视觉板与 STM32 的 UART 只接 TX、RX、GND，信号为 3.3 V；电机不能从主控板 5 V 引脚取电。",
    "购买前确认：视觉套件含摄像头；电机堵转电流与驱动匹配；电池、充电器和插头配套。",
]
for i, note in enumerate(notes):
    c.drawString(35, y - 15 - i * 13, note)

c.setFillColor(muted)
c.setFont(FONT, 7.4)
c.drawString(35, 53, "工具另备或借用：电脑、万用表、电烙铁、USB-C 数据线、Micro-USB 数据线。")
c.drawString(35, 39, "参考：DigiKey 主控报价、立创庐山派快速入门、TI DRV8833 产品资料；比赛尺寸以比赛文档为准。")
c.setStrokeColor(line)
c.line(35, 29, W - 35, 29)
c.setFont(FONT, 7)
c.drawRightString(W - 35, 17, "1 / 1")
c.save()
print(OUTPUT)
print("bottom_y", y - 15 - 2 * 13)
