from pathlib import Path
from decimal import Decimal
from xml.sax.saxutils import escape
import json
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer, PageBreak, Flowable

BASE = Path(__file__).resolve().parents[1]
OUT = BASE / 'hardware_purchase_list.pdf'
pdfmetrics.registerFont(TTFont('CN', r'C:\Windows\Fonts\simhei.ttf'))
NAVY = colors.HexColor('#153149')
BLUE = colors.HexColor('#136F94')
GRAY = colors.HexColor('#526473')
LIGHT = colors.HexColor('#EDF5F8')
LINE = colors.HexColor('#D4E1E8')
W, H = A4
CW = W - 72
styles = {
    'title': ParagraphStyle('title', fontName='CN', fontSize=24, leading=31, textColor=NAVY, spaceAfter=10),
    'sub': ParagraphStyle('sub', fontName='CN', fontSize=10, leading=15, textColor=GRAY, spaceAfter=14),
    'h': ParagraphStyle('h', fontName='CN', fontSize=13, leading=18, textColor=BLUE, spaceBefore=12, spaceAfter=7),
    'p': ParagraphStyle('p', fontName='CN', fontSize=10, leading=16, textColor=NAVY, spaceAfter=7, wordWrap='CJK'),
    'small': ParagraphStyle('small', fontName='CN', fontSize=8.4, leading=12.5, textColor=GRAY, spaceAfter=6, wordWrap='CJK'),
    'cell': ParagraphStyle('cell', fontName='CN', fontSize=8.6, leading=12.7, textColor=NAVY, wordWrap='CJK'),
    'th': ParagraphStyle('th', fontName='CN', fontSize=8.6, leading=12.7, textColor=colors.white, wordWrap='CJK'),
}

def p(text, style='p'):
    return Paragraph(text, styles[style])

def link(label, url):
    return '<link href="' + escape(url, {'"': '&quot;'}) + '" color="#136F94"><u>' + escape(label) + '</u></link>'

story = []
def add(text, style='p'):
    story.append(p(text, style))

def title(n, text, sub):
    if n > 1: story.append(PageBreak())
    add(f'{n:02d} / {text}', 'title')
    add(sub, 'sub')

def table(headers, rows, widths):
    data = [[p(x, 'th') for x in headers]]
    data += [[p(str(x), 'cell') for x in row] for row in rows]
    t = Table(data, colWidths=widths, repeatRows=1, hAlign='LEFT')
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), NAVY), ('VALIGN',(0,0),(-1,-1),'TOP'),
        ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,LIGHT]),
        ('LEFTPADDING',(0,0),(-1,-1),7), ('RIGHTPADDING',(0,0),(-1,-1),7),
        ('TOPPADDING',(0,0),(-1,-1),7), ('BOTTOMPADDING',(0,0),(-1,-1),7),
        ('LINEBELOW',(0,-1),(-1,-1),.5,LINE),
    ]))
    story.append(t)
    story.append(Spacer(1,7))

BOM = [
 ('01','主控','立创·天空星 STM32F407VET6 开发板-青春版',1,'39.9','官网展示价'),
 ('02','视觉套件','立创·庐山派 Lite-K230D-CanMV / 128MB / GC2093',1,'188','官网展示价'),
 ('03','调试器','立创 DAPLink 调试工具',1,'22.9','官网展示价'),
 ('04','存储卡','MK米客方德 SDSDQAB-008G-MK / 8GB / Class 10',1,'15','估算'),
 ('05','编码电机套装','Yahboom MD310Z20_7.4V + Bracket + 3mm Coupling',2,'40','估算'),
 ('06','驱动轮','Yahboom 65mm classic rubber wheel / 6000300098',2,'6','估算'),
 ('07','驱动板','Yahboom AT8236 Standard / YB-MNT03-V1.0',1,'55','估算'),
 ('08','底板','FR4 无覆铜板 180×110×2mm / 四角R3',1,'12','估算'),
 ('09','后支撑轮','Yahboom 1-inch universal wheel / 6000301765 裸轮',1,'6','估算'),
 ('10','视觉安装台','FR4 80×60×2mm + M3×60mm 铝合金双通柱×4',1,'12','估算'),
 ('11','电池','Tattu TA-45C-800-2S1P-XT30',1,'45','估算'),
 ('12','充电器','ISDT UC2 / 0.8A / 2S LiPo',1,'35','估算'),
 ('13','充电电源','小米 MDY-11-EM / USB-A / 5V档3A',1,'25','估算'),
 ('14','扬声器','DFRobot FIT0502 / 8Ω / 3W标称',1,'15','官网展示价'),
 ('15','USB数据线','USB-A公→USB-C公 / 0.3m / USB2.0 480Mbps / 3A',2,'5','估算'),
 ('16','接线包','按第4页逐项购买，含电源转接、信号线和固定耗材',1,'30','估算'),
 ('17','紧固件包','按第4页逐项购买，含排针和绝缘支撑柱',1,'15','估算'),
 ('18','无源器件包','按第4页电容、电阻精确规格购买',1,'5','估算'),
 ('19','散热片','铝散热片 20×20×6mm / 绝缘导热胶贴',1,'3','估算'),
]
TOTAL = sum(Decimal(x[4])*x[3] for x in BOM)
SHIPPING = Decimal('20')
assert TOTAL == Decimal('625.8'), TOTAL

title(1, '智能小车定型采购清单', 'F407 + K230D Lite · 双轮差速 · 2026-10-10 · 版本 1.0')
add('先按这一套选型；全新购齐预计约 646 元。', 'h')
add('器件合计 <b>625.8 元</b>，另预留运费/价差 20 元，合计 <b>645.8 元</b>。这比已确定的 600 元预算高 45.8 元，尚不能称为“600 元内已核价”。本文件用于采购比价，没有下单。')
add('若严格控制在 600 元：先借用第 03 项 DAPLink 和第 13 项 USB 电源，可降至约 <b>597.9 元</b>（含 20 元预留）；车上硬件不变。此方案以确实能借到为前提。')
table(['项目','本次确定的方案'],[
 ('主控 / 视觉','天空星 F407VET6 青春版 + 庐山派 Lite-K230D-CanMV 标准套件；GC2093 小镜头定焦版随套件购买。'),
 ('动力 / 供电','两只 MD310Z20_7.4V、1:20、450 rpm；亚博经典橡胶轮；AT8236 标准驱动板；Tattu 2S 800mAh。'),
 ('尺寸 / 质量目标','设计包络 200×190×180mm（长×宽×高）；整车质量预算 650g，验收目标不超过 700g。均为设计值，尚未装车测量。'),
 ('速度目标','标称转速换算轮缘速度约 1.59m/s；调好后的直线目标 1.0–1.3m/s。弯道主动减速，整圈平均速度暂不承诺。'),
 ('结构 / 加工','180×110×2mm FR4 底板，前部双轮、后部万向轮，视觉模块高置。需钻孔、焊排针和接线；不是免加工整车套件。'),
], [94,CW-94])
add('比赛要求如何覆盖', 'h')
add('按工作区《比赛文档.pdf》：整车上限 300×200×250mm、含电池不超过 5kg；赛道净宽 500mm、含急弯；车上自主计算，顺时针一圈须在 5 分钟内完成。安装后必须量轮胎、线缆和摄像头的最外侧尺寸。')
add('保留板载麦克风 + 外接扬声器，以实现语音启动、应答和终点停车相关功能。硬件齐全不代表语音功能已完成，仍需关键词识别、预录语音及终点状态机。')
add('价格与型号的可信度', 'h')
add('四项价格来自厂家/官方商城展示；其他为采购预算估算，国内店铺结算价和库存未能逐项验证。型号、规格与选项已列明；螺丝、板材、线材属于标准件，以尺寸/接口定义，不能伪造统一商品型号。', 'small')

title(2, '电子与供电采购', '金额为人民币；“展示”表示官网展示价，“估”表示预算估算。蓝字可点击。')
electronics = [
 ('01','天空星 STM32F407VET6 开发板-青春版<br/>只买核心开发板；168MHz。',1,'39.9','39.9 展示',link('立创商品 23849165','https://item.szlcsc.com/23849165.html')),
 ('02','庐山派 Lite-K230D-CanMV，128MB<br/>含定制 GC2093 小镜头定焦摄像头。',1,'188','188 展示',link('立创商品 59063152','https://item.szlcsc.com/59063152.html')),
 ('03','立创 DAPLink 调试工具<br/>使用随配下载线或第4页杜邦线连接SWD。',1,'22.9','22.9 展示',link('立创商品 56199685','https://item.szlcsc.com/56199685.html')),
 ('04','MK米客方德 SDSDQAB-008G-MK<br/>microSD / 8GB / Class 10。',1,'15','15 估',link('立创商品 58293428','https://item.szlcsc.com/mro/58293428.html')),
 ('07','Yahboom AT8236 Standard<br/>板上丝印 YB-MNT03-V1.0；标准版。',1,'55','55 估',link('亚博天猫商品','https://detail.tmall.com/item.htm?id=700583380137')),
 ('11','Tattu TA-45C-800-2S1P-XT30<br/>7.4V / 800mAh / 45C / 2S。',1,'45','45 估',link('厂家型号页；国内按全名搜','https://genstattu.com/tattu-800mah-7-4v-45c-2s1p-lipo-battery-pack-with-xt30-plug/')),
 ('12','ISDT UC2<br/>0.8A，2S LiPo 4.2V/节。',1,'35','35 估',link('厂家型号页；国内按全名搜','https://www.isdt.co/uc2-2.html')),
 ('13','小米 MDY-11-EM USB电源<br/>USB-A口，5V档3A；购买全新正品。',1,'25','25 估','国内搜索：小米 MDY-11-EM'),
 ('14','DFRobot FIT0502 扬声器<br/>8Ω；商品标3W，额定/RMS约2W。',1,'15','15 展示',link('DFRobot 官方商城','https://mall.dfrobot.com.cn/goods-1311.html')),
 ('15','USB-A公→USB-C公 数据线<br/>0.3m / USB2.0 480Mbps / 3A。',2,'5','10 估','标准件，须支持数据传输'),
 ('19','铝散热片 20×20×6mm<br/>带绝缘导热胶贴，贴主芯片处。',1,'3','3 估','标准件；避开周围元件'),
]
table(['编号','确定型号 / 购买选项','数量','单价','小计','入口'], electronics, [34,200,34,35,65,CW-368])
add('套件重复购买检查', 'h')
add('K230D 商品包装图列出：主板、GC2093、摄像头钣金支架、小螺丝、GH1.25 转杜邦线等。赠品可能调整，收到订单确认页后按第4页补缺。TF 卡必须单买。当前官方流程支持 USB 烧录 TF 卡，因此本清单未另配读卡器。', 'small')

title(3, '动力与机械采购', '动力选项已固定；板材和安装台按下列尺寸购买，加工孔位以实物配套件为准。')
mechanical = [
 ('05','Yahboom MD310Z20_7.4V<br/>1:20 / 450rpm / 3mm D轴<br/>选 Motor+Bracket+Coupling<br/>厂家套装SKU：6000301565',2,'40','80',link('亚博天猫电机','https://detail.tmall.com/item.htm?id=703875566318')),
 ('06','Yahboom 65mm classic rubber wheel<br/>经典橡胶轮；SKU 6000300098<br/>厂家尺寸图实际外径67.5mm、轮胎宽26.5mm。',2,'6','12',link('亚博天猫轮组','https://detail.tmall.com/item.htm?id=609075310031')),
 ('08','FR4 无覆铜玻纤板<br/>180×110×2mm；四角R3；去毛刺。<br/>按尺寸切割，不用覆铜PCB。',1,'12','12','搜索：FR4无铜板 定尺切割'),
 ('09','Yahboom 1-inch universal wheel<br/>裸轮SKU 6000301765<br/>安装高度33.5mm，轮径25mm。',1,'6','6',link('亚博天猫万向轮','https://detail.tmall.com/item.htm?id=609300451155')),
 ('10','视觉安装台组件<br/>FR4板80×60×2mm ×1<br/>M3×60mm铝合金双通隔离柱 ×4<br/>用原装摄像头支架固定摄像头。',1,'12','12','标准件；柱长为本体长度'),
]
table(['编号','确定型号 / 购买选项','数量','单价','小计','入口'],mechanical,[34,230,34,35,35,CW-368])
add('电机套装必须这样选', 'h')
add('买 2 套“电机 + 支架 + 3mm 联轴器”，另买 2 只经典橡胶轮。联轴器为 3mm 轴孔、12mm 六角；不要选 6mm 轴孔，也不要选 TT 电机扁孔轮。厂家 Motor+Bracket+Tire 套装默认轮径为 48mm，不是本方案使用的轮组。')
add('电机套装应包含每只电机的 PH2.0-6P 编码器线、配套支架紧固件和联轴器顶丝；本清单不重复计算。亚博国际站 SKU 用于识别选项，国内店铺的内部编号可能不同。')
add('底盘安装尺寸', 'h')
add('两电机镜像安装在底板下方，左右输出轴同轴，轮子位于板外；底板前端距驱动轴中心约 45mm。后万向轮中心置于底板前端约 150mm 处。先摆件再钻孔，防止电机、后轮旋转范围和紧固件相互干涉。')
add('倒装电机支架时，按厂家轴心距安装面19.75mm计算，底板下表面高度约为33.75+19.75=53.5mm。后轮高度33.5mm，配第4页M3×20mm隔离柱，名义上同高；轮胎受压后用平垫微调。')
add('工艺边界：这是一套可按规格购买的散件方案；底板未提供经实物验证的数控孔位图。板材开孔、视觉角度和线束走向需要装配时调整。', 'small')

title(4, '小配件逐项下单', '第16–18项按整包预留预算；以下是包内准确规格与最低数量，避免漏买。')
table(['归属','购买规格 / 数量','用途与装配说明'],[
 ('16 / 30元','XT30U-M 公头成品线，18AWG红黑，10cm ×1','接电池XT30母头至驱动板电源端子；按金属端子形态核对公母和极性。'),
 ('16','USB-A母座转螺丝端子板，4P，标明5V/GND/D+/D- ×2','驱动板5V/GND分两路供电；USB-A→C数据线分别接主控、视觉。端子板须绝缘固定。'),
 ('16','MX1.25-2P插头带线，15cm ×1','扬声器接K230D。FIT0502自带PH2.0头需剪下转接；焊点用热缩管绝缘。'),
 ('16','杜邦线母对母40P，2.54mm，20cm ×1排<br/>22AWG硅胶线，红/黑各0.5m','信号互连、SWD和5V供电布线；电池主回路用上面的18AWG成品线。'),
 ('16','2.54mm双面洞洞板50×70mm ×1<br/>尼龙扎带2.5×100mm ×20<br/>魔术贴绑带20×200mm ×2','搭分压/滤波小板，整理线束，固定电池；不用松散面包板上车。'),
 ('16','2:1热缩管，直径2/3/5mm各0.3m<br/>双面泡棉胶10×1mm，长0.5m','转接线绝缘；固定扬声器/电池垫。摄像头主要靠硬支架固定。'),
 ('17 / 15元','M3×20mm双通尼龙柱 ×4<br/>M3×6mm双通尼龙柱 ×8<br/>M2.5×6mm双通尼龙柱 ×4','20mm支撑后万向轮；6mm柱用于电路板隔离，M2.5柱用于视觉板。'),
 ('17','M3×6mm螺丝 ×24；M3×10mm螺丝 ×12<br/>M3螺母 ×20；M3平垫 ×30<br/>M2.5×6mm螺丝 ×8；M2.5螺母 ×4<br/>M4×8mm螺丝 ×2；M4平垫 ×2','普通十字盘头；M4×8mm用于轮子与六角联轴器固定。电机支架、联轴器顶丝、摄像头专用小螺丝使用原装随配件。'),
 ('17','2.54mm直排针：2×20P ×2，2×5P ×1','F407接口焊接；订单已含时无需重复购买。M3×60mm柱已计入第10项。'),
 ('18 / 5元','470μF/16V 105℃径向电解电容 ×2<br/>100nF/50V X7R陶瓷电容 ×3<br/>20kΩ、10kΩ / 1% / 0.25W电阻各×2','电源滤波、电机端抑制干扰、电池电压采样；电解注意正负极。'),
], [53,244,CW-297])
add('已包含的线材与接头', 'h')
add('GH1.25-4P→2.54mm杜邦母头线：视觉套件赠送3条，串口实际需1条。PH2.0-6P电机线：电机套装每只1条。若订单取消赠品，按这些规格补齐并计入实际结算；不要拿MX1.25与GH1.25互换。', 'small')
add('装配工具', 'h')
add('还需借用实验室：万用表、电烙铁/焊锡、剥线钳、热缩加热工具、带夹具的小电钻及3.2/4.2mm钻头、直尺、电子秤、十字螺丝刀和配套内六角。工具与练习赛道未计入上述购车预算；若全部工具也从零购买，总费用会继续增加。', 'small')

title(5, '供电与装配关系', '先完成供电和编码器验证，再接视觉闭环；以下是功能接线关系，不替代各板原理图。')
table(['电源 / 信号','确定的连接方式'],[
 ('动力主路','Tattu 2S电池（满电8.4V）→ XT30线 → AT8236标准板输入；驱动板电机输出分别接左右电机。使用板载总开关。'),
 ('5V逻辑电源','AT8236标准板的5V输出 → 两块USB-A端子板 → 两根A-to-C线 → F407、K230D的Type-C口。标准板带5V/3A降压；不再单独购买两块降压模块。'),
 ('编码器','电机编码器按厂家线序接3.3V、GND、A、B；A/B接F407定时器编码器输入。电机动力两根线与编码器电源分开。'),
 ('视觉串口','K230D UART2的GH1.25-4P接口 → F407串口；TX接RX、RX接TX、GND共地，接口的5V线不用时单独绝缘。双方使用3.3V逻辑。'),
 ('驱动控制','F407四路GPIO/PWM → AT8236两桥控制输入；按厂家真值表实现正反转、刹车和停止。上电先保持输出关闭。'),
 ('电池采样','电池正极→20kΩ→ADC节点→10kΩ→GND；节点并100nF到GND。满电时ADC约2.8V。接F407空闲ADC引脚，并用万用表校准。'),
 ('语音','板载麦克风采集关键词；FIT0502接K230D扬声器的SPK+/SPK-。输出是差分功放，两根喇叭线均不接GND。'),
 ('充电','电池从车上断开；2S的JST-XH 3P平衡头接UC2的2S口；小米USB电源以A-to-C线给UC2供5V。UC2 0.8A约为这块电池的1C。'),
], [91,CW-91])
add('接电前的三个关键检查', 'h')
add('1. 万用表检查极性与5V输出。2S电池最低工作电压会低于K230D宽压口标称8V，不能直接用该宽压口给视觉供电。')
add('2. 确认AT8236是标准版，带5V降压与总开关；按本方案两台电机的堵转电流估算有余量，但仍须做同时启动、刹车和视觉运行的掉压/温升测试。')
add('3. 电脑USB调试时先断开对应板的车载5V；SWD只接信号和GND时，不再接DAP的电源输出，避免两路电源互相回灌。')
add('机械摆放', 'h')
add('电池靠近驱动轴、低位固定；F407和驱动板平铺于底板，板底绝缘。视觉安装台由60mm柱抬高，K230D与短排线摄像头一起安装；镜头高度约140mm、向下约25°作为初始调试值。验收量整车宽≤190mm、高≤180mm，并检查后轮360°旋转无碰擦。', 'small')

title(6, '重量、速度与性能判断', '以下为工程计算和调试目标，不能当作已经测得的竞赛成绩。')
table(['质量分项','预算质量','依据'],[
 ('电机×2','140g','厂家约70g/只'),
 ('轮子×2 + 联轴器 + 电机支架','90g','轮子/联轴器参考值，支架与螺丝估算'),
 ('FR4底板 + 后万向轮','103g','底板按约1.85g/cm^3估算73g；后轮约29g'),
 ('主控 + 视觉/摄像头 + 驱动','80g','驱动厂家约22g，其余留质量预算'),
 ('电池','60g','厂家页面质量字段不一致；按50–70g估算并留余量'),
 ('视觉平台/立柱 + 扬声器','64g','安装结构约40g，扬声器厂家24g'),
 ('线束、散热、紧固与机动余量','113g','装车前的预留值'),
 ('整车设计预算','650g','实际以电子秤称重为准；控制在700g以内'),
], [245,65,CW-310])
add('450 rpm 不等于慢：必须同时看轮径与负载', 'h')
add('轮缘速度 v = π × D × n / 60 = π × 0.0675 × 450 / 60 ≈ <b>1.59m/s</b>。这是厂家标称转速对应的几何速度；未获得该转速的统一负载测试条件，所以不当作装车实测极速。')
add('电机额定转矩0.4kgf·cm/只。按33.75mm轮半径计算，两轮理想牵引力约2.32N；650g整车对应理想加速度约3.6m/s^2，实际受轮胎抓地、传动、电池和驱动限制。选择310电机是为获得明确的负载参数及配套安装件。')
add('速度调试顺序：0.3m/s稳定完赛 → 0.6m/s → 0.9m/s → 直线1.0–1.3m/s；急弯先以0.3–0.5m/s开始。每次提高速度都检查出界、摆动和制动距离。这个配置不能保证达到某个名次。')
add('算力与画面延迟', 'h')
add('F407负责两路编码器、PWM、速度环、转向和停车，168MHz足够作为这套结构的控制器，建议控制周期5ms（200Hz）。K230D独立处理画面，再把偏差/曲率/置信度发给F407，不让F407处理整幅图。')
add('视觉先用320×240或局部图像、边界提取和短曝光，目标是实测有效更新50–60Hz；帧率与延迟要记录，不能用芯片宣传值代替。建议UART 115200，16字节×60Hz仅960字节/秒。超过80ms没收到新结果时主动减速/停车。')
add('弯道与空气阻力', 'h')
add('差速转弯需要给外侧轮留速度余量。以轮距0.16m、中心转弯半径0.20m为例，外轮速度为中心速度的1.4倍；不能一直按直线速度过弯。约1.5m/s下优先减重、压低重心和抑制视觉抖动，暂不加尾翼或外壳。', 'small')

title(7, '总账与核对入口', '主要型号可按链接/完整名称购买；付款前仍须核对店铺选项、配件和最终金额。')
table(['编号 / 内容','数量','金额'],[
 ('01–04 主控、视觉、DAPLink、TF卡','各1','265.8'),
 ('05–07 电机套装、驱动轮、AT8236','2 / 2 / 1','147.0'),
 ('08–10 底板、后轮、视觉安装台','各1','30.0'),
 ('11–15 电池、充电器、电源、扬声器、USB线','1 / 1 / 1 / 1 / 2','130.0'),
 ('16–19 接线包、紧固件、无源件、散热片','各1','53.0'),
 ('器件合计 / 运费及价差预留 / 计划总额','—','625.8 / 20 / 645.8'),
], [344,55,CW-399])
add('厂家资料索引（核验日期：2026-10-10）', 'h')
sources = [
 ('S1 比赛要求','工作区《比赛文档.pdf》共6页；尺寸、赛道、评分及自主运行要求。'),
 ('S2 主控与价格',link('天空星硬件说明','https://wiki.lckfb.com/zh-hans/fdb/skystar.html')+'；'+link('立创开发板官网价格入口','https://lckfb.com/')+'。'),
 ('S3 视觉与包装',link('官方快速上手：GC2093、TF卡与USB烧录','https://openkits-wiki.easyeda.com/zh-hans/lushan-pi-k230/quick-start.html')+'；'+link('官方发货清单图片','https://image.lceda.cn/openkits/files/0de20a44bf65400184139797fdede5bf.jpg')+'。'),
 ('S4 电机参数',link('亚博310电机资料：电压、转速、转矩和编码器','https://www.yahboom.net/public/upload/upload-html/1744700910/Motor%20introduction%20and%20usage.html')+'；'+link('型号与套装','https://category.yahboom.net/products/310motor')+'。'),
 ('S5 驱动与结构',link('AT8236标准版','https://category.yahboom.net/products/dual-md-module')+'；'+link('轮胎与3mm联轴器','https://category.yahboom.net/products/wheel-set')+'；'+link('1英寸万向轮','https://category.yahboom.net/products/yahboom-1-inch-universal-wheel')+'。'),
 ('S6 电池与充电',link('Tattu 800mAh 2S XT30','https://genstattu.com/tattu-800mah-7-4v-45c-2s1p-lipo-battery-pack-with-xt30-plug/')+'；'+link('ISDT UC2参数','https://www.isdt.co/uc2-2.html')+'；'+link('MDY-11-EM CQC证书','https://www.cqc.com.cn/www/upload/file/2026-05/1778469881856.pdf')+'。'),
 ('S7 语音与调试',link('FIT0502扬声器','https://www.dfrobot.com/product-1506.html')+'；'+link('K230D支持的模型功能','https://wiki.lckfb.com/public/storage/html/canmv-web-ide/lushan-skill/models.html')+'；'+link('DAPLink接线','https://wiki.lckfb.com/zh-hans/fdb/lckfb-daplink-emulator.html')+'。'),
]
table(['索引','依据'], sources, [95,CW-95])
add('收到器件后按这四步验收', 'h')
add('① 点数并核对型号：2S/XT30电池、3mm联轴器、经典橡胶轮、AT8236标准版、Lite-K230D套件。② 空载验证两轮方向、编码器计数、5V电源和摄像头。③ 称重、量整车包络并拍照留档。④ 从低速开始，以连续稳定完赛作为升速条件。', 'small')
add('本版替代原《hardware_list_600CNY.pdf》中的泛化N20/DRV8833组合。参考资料确认了选型依据，但本车未完成装配和整车试验；国内实际报价、底板孔位和动态性能还不是已验证结果。', 'small')

def footer(c, doc):
    c.saveState()
    c.setStrokeColor(LINE)
    c.line(36,36,W-36,36)
    c.setFont('CN',8)
    c.setFillColor(GRAY)
    c.drawString(36,23,'SMART CAR / PURCHASE SPECIFICATION / 2026-10-10')
    c.drawRightString(W-36,23,f'{doc.page} / 7')
    c.restoreState()

doc = SimpleDocTemplate(str(OUT), pagesize=A4, rightMargin=36, leftMargin=36,
    topMargin=35, bottomMargin=48, title='智能小车定型采购清单：F407 + K230D Lite', author='Codex')
doc.build(story,onFirstPage=footer,onLaterPages=footer)
(BASE/'source'/'purchase_bom.json').write_text(json.dumps({
    'date':'2026-10-10','currency':'CNY','rows':[{'id':r[0],'category':r[1],'model':r[2],'quantity':r[3],'unit_budget':float(r[4]),'price_status':r[5]} for r in BOM],
    'parts_total':float(TOTAL),'shipping_allowance':float(SHIPPING),'planned_total':float(TOTAL+SHIPPING),
    'note':'Only rows marked 官网展示价 have a checked display price; remaining numbers are budget estimates, not merchant quotes.'
}, ensure_ascii=False,indent=2),encoding='utf-8')
print(OUT)
print('Parts:', TOTAL, 'With allowance:', TOTAL+SHIPPING)
