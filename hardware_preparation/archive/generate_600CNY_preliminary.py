from pathlib import Path
from decimal import Decimal
import json
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

BASE = Path(__file__).resolve().parents[1]
OUTPUT = BASE / 'hardware_list_600CNY.pdf'
pdfmetrics.registerFont(TTFont('CN', r'C:\Windows\Fonts\simhei.ttf'))
W, H = A4
LEFT, RIGHT = 35, W - 35
NAVY = colors.HexColor('#16324B')
BLUE = colors.HexColor('#1766A1')
MUTED = colors.HexColor('#536474')
RULE = colors.HexColor('#D6E1E9')
PALE = colors.HexColor('#EDF5FA')

# All prices are row totals, not unit prices. Only the first three are
# listed manufacturer prices checked on 2026-10-10; others are estimates.
ROWS = [
    ('主控板', '天空星 STM32F407VET6 青春版', '1 块', '39.9', '168 MHz；需焊排针。只买核心板，不买学习底板。'),
    ('下载调试器', '立创 DAPLink + 匹配下载线', '1 套', '22.9', 'SWD 调试；可借用，节省的费用留作备件。'),
    ('视觉套件', '庐山派 Lite-K230D-CanMV', '1 套', '188', '128 MB 版本；订单须含 GC2093、排线与散热片。'),
    ('存储卡', 'microSD 8-16 GB，Class 10', '1 张', '15', '用于视觉板程序、固件和预录语音。'),
    ('编码电机', 'N20 金属减速电机，带 AB 相编码器', '2 只', '100', '6 V，考察空载 800-1000 rpm；须提供转矩、电流和编码器参数。'),
    ('驱动轮配件', '橡胶轮 + 匹配轮毂 + 电机支架', '2 套', '20', '轮径 32-35 mm；匹配轴径、D 形轴和固定孔。'),
    ('电机驱动', 'DRV8833 双路驱动成品模块', '1 块', '20', '优先 PWP/RTY 封装；按实际散热与两电机电流核对。'),
    ('车架组件', '轻质底板 + 支撑球 + 可调摄像头支架', '1 套', '30', '底板约 18 × 12 cm；含固定件，装好后再量整车尺寸。'),
    ('动力电池', '2S 7.4 V 锂电池，650-1000 mAh', '1 块', '45', '含动力插头、平衡头；放电能力覆盖双电机启动和控制板。'),
    ('充电器', '适配 2S 电池的平衡充电器', '1 套', '30', '配套电源及线材计入本项；接口、充电电流匹配电池。'),
    ('逻辑降压', '5 V 降压模块', '1 块', '20', '输入覆盖 2S 电池使用范围；目标可持续输出 3 A。'),
    ('动力降压', '可调降压模块，输出设为 6 V', '1 块', '20', '目标持续 3 A，按启动电流复核；低电量时须留意压差。'),
    ('语音应答', '4 Ω / 3 W 小喇叭 + 插线', '1 只', '5', '接 Lite 板载功放；播放预录音，麦克风用板载。'),
    ('接线与固定', '开关、插头、线材、排针、铜柱等', '1 批', '20', '含电池固定带、热缩管、电容及电压分压电阻。'),
    ('电脑连接', 'USB-C 数据线 + TF 读卡器', '1 批', '10', '优先复用已有配件；三块板可轮流使用数据线。'),
]
TOTAL = sum(Decimal(row[3]) for row in ROWS)
RESERVE = Decimal('600') - TOTAL
assert TOTAL == Decimal('585.8')

c = canvas.Canvas(str(OUTPUT), pagesize=A4)
c.setTitle('智能小车完整硬件清单 - 600 元预算')
c.setAuthor('Codex')

def text(x, y, value, size=9, color=NAVY):
    c.setFillColor(color)
    c.setFont('CN', size)
    c.drawString(x, y, value)

def wrap(value, width, size):
    result = []
    for paragraph in value.split('\n'):
        line = ''
        for ch in paragraph:
            if pdfmetrics.stringWidth(line + ch, 'CN', size) > width:
                result.append(line)
                line = ch
            else:
                line += ch
        result.append(line)
    return result

def paragraph(value, y, size=9, leading=14, width=None, x=LEFT, color=MUTED):
    for line in wrap(value, width or RIGHT-LEFT, size):
        text(x, y, line, size, color)
        y -= leading
    return y

def header(title, subtitle, page):
    text(LEFT, H-48, title, 20)
    text(LEFT, H-69, subtitle, 9, MUTED)
    c.setStrokeColor(RULE)
    c.line(LEFT, 33, RIGHT, 33)
    text(LEFT, 20, '600 元方案 | 2026-10-10 | 旧预算清单已归档', 7, MUTED)
    text(RIGHT-30, 20, f'{page} / 2', 7, MUTED)

def section(title, body, y):
    text(LEFT, y, title, 11, BLUE)
    return paragraph(body, y-18, 9, 14)-12

header('智能小车完整硬件清单', 'STM32F407 + K230D Lite | 双轮差速 | 预算包含电池、充电器和下载器', 1)
c.setFillColor(PALE)
c.roundRect(LEFT, H-120, RIGHT-LEFT, 36, 5, fill=1, stroke=0)
text(LEFT+10, H-99, '硬件预计 585.8 元 + 预留 14.2 元 = 总预算 600 元', 11, BLUE)
text(LEFT+10, H-112, '前三项为官网查询价；其余为采购估算。预留用于运费或价差，实付超额须重新核算。', 8, MUTED)

widths = [61, 165, 40, 204, RIGHT-LEFT-470]
xs = [LEFT]
for width in widths:
    xs.append(xs[-1]+width)
y = H-134
c.setFillColor(NAVY)
c.rect(LEFT, y-25, RIGHT-LEFT, 25, fill=1, stroke=0)
for i, label in enumerate(['类别', '建议型号 / 规格', '数量', '配套与选购要求', '小计/元']):
    text(xs[i]+5, y-16, label, 8.2, colors.white)
y -= 25
for idx, (kind, model, qty, price, desc) in enumerate(ROWS):
    values = [kind, model, qty, desc, price]
    lines = [wrap(value, widths[i]-10, 8.1) for i, value in enumerate(values)]
    rh = max(map(len, lines))*11.5+12
    if idx % 2 == 0:
        c.setFillColor(colors.HexColor('#F4F7FA'))
        c.rect(LEFT, y-rh, RIGHT-LEFT, rh, fill=1, stroke=0)
    c.setStrokeColor(RULE)
    c.line(LEFT, y-rh, RIGHT, y-rh)
    for col, cell in enumerate(lines):
        for j, line in enumerate(cell):
            text(xs[col]+5, y-14-j*11.5, line, 8.1, MUTED if col==3 else NAVY)
    y -= rh
assert y > 90, y
text(LEFT, y-20, '金额为该行全部数量的合计。电机/驱动/电源型号须按第 2 页条件成套确认后下单。', 8.5, BLUE)
paragraph('工具另备或借用：电脑、万用表、烙铁与焊锡、螺丝刀。工具、备用电池、IMU 和自建赛道材料未计入；板载按键、麦克风无需重复采购。', y-37, 8.2, 12)
c.showPage()

header('装配与配套核对', '先核对接口和电流，再下单动力件；价格增加应优先保障电机、轮胎与供电。', 2)
y = H-101
y = section('01  尺寸、布局与速度目标', '比赛上限：长 30 cm、宽 20 cm、高 25 cm、总质量 5 kg；车道净宽 50 cm，示意图含约 77° 锐角弯，碰黑边扣分。建议整车约长 18-20 cm、宽 13-15 cm、高 15-18 cm，尽量控制在 300-450 g；均为设计目标，最终以实物测量为准。电池低置并靠近驱动轮轴，减少前后悬伸；摄像头俯仰可调。首车不增加尾翼或整流外壳。', y)
y = section('02  主控、视觉与语音分工', 'K230D 用 Python/CanMV 处理灰度图和多行边界，向 F407 发送偏差、弯道信息、置信度和时间戳。F407 用 C/C++ 做左右轮闭环、加减速及失联停车。先以视觉有效更新 50-60 次/秒、轮速控制 200 次/秒为调试目标，必须实测延迟后提速，不能把摄像头标称帧率当作算法帧率。语音先用关键词识别加预录音播放；与视觉并行运行的内存和延迟须实测。', y)
y = section('03  电机与驱动：下单前的必要条件', 'N20 只是外形类别，不能仅按转速购买。两电机须同型号，供应商应提供 6 V 下堵转电流、额定转矩/负载转速、减速比、编码器脉冲定义和供电范围。编码器应能以 3.3 V 工作，或使用兼容的电平转换。DRV8833 的 PWP/RTY 封装标称每路 1.5 A RMS、2 A 峰值；普通 PW 封装仅 0.5 A RMS，成品板仍受散热限制。若电机电流超出模块能力，须更换驱动并重算预算，不能直接拼接。', y)
y = section('04  电源连接与机械固定', '2S 电池（满电 8.4 V）经总开关分两路：一路降至 5 V，分别给 F407 与 K230D 供电；另一路降至 6 V，接电机驱动 VM，再接两电机。所有模块共地，动力回流不要经过控制板。6 V 降压器在低电量时可能失去稳压，应留足压差并用分压采样监测电池。先用万用表确认两路电压再接板；按实际板卡手册连接，不能把电池直接接 5 V 脚。UART 为 3.3 V TX/RX/GND；比赛装车采用可靠插接或焊接，摄像头排线、电池与电源线均须固定。', y)
y = section('05  预算边界与后补项', '保留 F407 与 K230D，暂不购买 IMU、额外语音模块、显示屏、无线遥控和高价摄像头。喇叭用于比赛要求的语音应答；板载蜂鸣器不能替代语音。借到 DAPLink 可节省 22.9 元，用于运费、备件或提高动力件预算。硬件仅提供实现条件，不保证取得语音附加分或某一圈速。', y)
text(LEFT, y, '资料依据与购买入口（点击文字可打开）', 10, BLUE)
y -= 17
refs = [
    ('[1] 立创官网：F407 青春版 39.9 / K230D Lite 188 / DAPLink 22.9 元', 'https://lckfb.com/'),
    ('[2] 天空星核心板：型号、焊接与接口规格', 'https://wiki.lckfb.com/zh-hans/fdb/skystar.html'),
    ('[3] 庐山派快速入门：标准套件与 TF 卡要求', 'https://openkits-wiki.easyeda.com/zh-hans/lushan-pi-k230/quick-start.html'),
    ('[4] TI DRV8833：封装差异、电流与供电范围', 'https://www.ti.com/product/DRV8833'),
    ('[5] K230D 模型兼容表：关键词识别与语音合成限制', 'https://wiki.lckfb.com/public/storage/html/canmv-web-ide/lushan-skill/models.html'),
]
for label, url in refs:
    text(LEFT, y, label, 7.5, BLUE)
    c.linkURL(url, (LEFT, y-2, RIGHT, y+9), relative=0, thickness=0)
    y -= 13
text(LEFT, y-2, '比赛规则来源：项目根目录“比赛文档.pdf”第 2-4 页。官网查询日期：2026-10-10。', 7.5, MUTED)
assert y > 50, y
c.save()
print(json.dumps({'path': str(OUTPUT), 'total': str(TOTAL), 'reserve': str(RESERVE), 'pages': 2, 'last_y': y}, ensure_ascii=True))
