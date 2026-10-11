from pathlib import Path
from decimal import Decimal
from collections import Counter
from xml.sax.saxutils import escape
import json
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer, PageBreak

BASE = Path(__file__).resolve().parents[1]
BOM = json.loads((BASE/'source'/'purchase_bom.json').read_text(encoding='utf-8'))
ITEMS = {r['id']:r for r in BOM['rows']}
ALLOCATIONS = {
    'control':[('01',1),('03',1),('07',1),('11',1),('12',1),('15',1),('18',1)],
    'vision':[('02',1),('04',1),('15',1),('19',1)],
    'hardware':[('05',2),('06',2),('08',1),('09',1),('10',1),('13',1),('14',1),('16',1),('17',1)],
}
TITLES = {'control':'主控队员购买清单','vision':'视觉队员购买清单','hardware':'硬件队员购买清单'}
NAMES = {'control':'主控','vision':'视觉','hardware':'硬件'}
TOTALS = {role:sum(Decimal(str(ITEMS[i]['unit_budget']))*q for i,q in rows) for role,rows in ALLOCATIONS.items()}
counts = Counter()
for rows in ALLOCATIONS.values():
    for i,q in rows: counts[i]+=q
assert counts==Counter({r['id']:r['quantity'] for r in BOM['rows']}), 'Missing or duplicated purchase quantities'
assert sum(TOTALS.values())==Decimal(str(BOM['parts_total']))==Decimal('625.8')
assert max(TOTALS.values())-min(TOTALS.values())==Decimal('4.0')

pdfmetrics.registerFont(TTFont('CN',r'C:\Windows\Fonts\simhei.ttf'))
NAVY=colors.HexColor('#153149')
BLUE=colors.HexColor('#136F94')
GRAY=colors.HexColor('#526473')
PALE=colors.HexColor('#EDF5F8')
LINE=colors.HexColor('#D4E1E8')
W,H=A4
CW=W-72
styles={
    'title':ParagraphStyle('title',fontName='CN',fontSize=23,leading=30,textColor=NAVY,spaceAfter=8),
    'sub':ParagraphStyle('sub',fontName='CN',fontSize=9.5,leading=14,textColor=GRAY,spaceAfter=10),
    'h':ParagraphStyle('h',fontName='CN',fontSize=12,leading=17,textColor=BLUE,spaceBefore=10,spaceAfter=6),
    'p':ParagraphStyle('p',fontName='CN',fontSize=9.7,leading=15,textColor=NAVY,wordWrap='CJK',spaceAfter=7),
    'small':ParagraphStyle('small',fontName='CN',fontSize=8.5,leading=12.5,textColor=GRAY,wordWrap='CJK',spaceAfter=6),
    'cell':ParagraphStyle('cell',fontName='CN',fontSize=9,leading=13,textColor=NAVY,wordWrap='CJK'),
    'th':ParagraphStyle('th',fontName='CN',fontSize=9,leading=13,textColor=colors.white,wordWrap='CJK'),
}
def par(s,style='p'):
    return Paragraph(s,styles[style])
def link(label,url):
    return f'<link href="{escape(url,{chr(34): "&quot;"})}" color="#136F94"><u>{escape(label)}</u></link>'
def money(value):
    return f'{Decimal(str(value)):.1f}'

INFO={
    '01':('天空星 STM32F407VET6 开发板-青春版<br/>只买核心开发板。',link('立创商品 23849165','https://item.szlcsc.com/23849165.html')),
    '02':('庐山派 Lite-K230D-CanMV / 128MB<br/>标准套件，含GC2093小镜头定焦摄像头。',link('立创商品 59063152','https://item.szlcsc.com/59063152.html')),
    '03':('立创 DAPLink 调试工具<br/>核对配套SWD下载线。',link('立创商品 56199685','https://item.szlcsc.com/56199685.html')),
    '04':('MK米客方德 SDSDQAB-008G-MK<br/>microSD / 8GB / Class 10。',link('立创商品 58293428','https://item.szlcsc.com/mro/58293428.html')),
    '05':('Yahboom MD310Z20_7.4V<br/>1:20 / 450rpm / 3mm D轴<br/>选 Motor+Bracket+Coupling<br/>套装SKU：6000301565。',link('亚博天猫电机','https://detail.tmall.com/item.htm?id=703875566318')),
    '06':('Yahboom 65mm classic rubber wheel<br/>经典橡胶轮，SKU 6000300098<br/>厂家图实际外径67.5mm。',link('亚博天猫轮组','https://detail.tmall.com/item.htm?id=609075310031')),
    '07':('Yahboom AT8236 Standard 标准版<br/>丝印 YB-MNT03-V1.0<br/>带5V降压输出和总开关。',link('亚博天猫驱动板','https://detail.tmall.com/item.htm?id=700583380137')),
    '08':('FR4 无覆铜板，180×110×2mm<br/>四角R3，切边去毛刺；孔位装配时确定。','搜索：FR4 无铜板 定尺切割'),
    '09':('Yahboom 1-inch universal wheel 裸轮<br/>SKU 6000301765 / 安装高度33.5mm。',link('亚博天猫万向轮','https://detail.tmall.com/item.htm?id=609300451155')),
    '10':('视觉安装台：FR4板80×60×2mm ×1<br/>M3×60mm铝合金双通隔离柱 ×4。','按这两项标准件购买；12元为合计估算'),
    '11':('Tattu TA-45C-800-2S1P-XT30<br/>7.4V / 800mAh / 45C / 2S<br/>动力头XT30；平衡头JST-XH 3P。',link('厂家型号页','https://genstattu.com/tattu-800mah-7-4v-45c-2s1p-lipo-battery-pack-with-xt30-plug/')+'<br/>国内搜索完整型号'),
    '12':('ISDT UC2 / 0.8A<br/>支持2S LiPo，4.2V/节<br/>USB-C输入，XH平衡充电接口。',link('厂家型号页','https://www.isdt.co/uc2-2.html')+'<br/>国内搜索：ISDT UC2'),
    '13':('小米 MDY-11-EM USB电源<br/>USB-A口，5V档3A；全新正品。','国内搜索：小米 MDY-11-EM'),
    '14':('DFRobot FIT0502 扬声器<br/>8Ω / 标称3W / 自带PH2.0线。',link('DFRobot官方商城','https://mall.dfrobot.com.cn/goods-1311.html')),
    '15':('USB-A公→USB-C公数据线<br/>0.3m / USB2.0 480Mbps / 3A。','搜索完整规格；须支持数据传输<br/>本单1根，另一位队员另买1根'),
    '16':('接线与耗材包：按第2页逐项买齐。','30元为整组预算，不是固定套装商品'),
    '17':('紧固件与排针：按第2页逐项买齐。','15元为整组预算，不是固定套装商品'),
    '18':('470μF/16V 105℃径向电解电容 ×2<br/>100nF/50V X7R陶瓷电容 ×3<br/>20kΩ及10kΩ / 1% / 0.25W电阻各×2。','标准件逐项购买；5元为整组预算'),
    '19':('铝散热片20×20×6mm ×1<br/>带绝缘导热胶贴。','搜索：20×20×6mm 铝散热片 导热胶贴'),
}
WIRE_ROWS=[
    ('XT30电源线','XT30U-M公头成品线 / 18AWG红黑 / 10cm','1条'),
    ('USB电源端子板','USB-A母座转螺丝端子板 / 4P<br/>标明5V、GND、D+、D-','2块'),
    ('扬声器转接线','MX1.25-2P插头带线 / 15cm','1条'),
    ('信号与电源线','杜邦线母对母 / 2.54mm / 40P / 20cm<br/>22AWG硅胶线：红、黑各0.5m','1排 + 1m'),
    ('安装与连接','2.54mm双面洞洞板50×70mm ×1<br/>尼龙扎带2.5×100mm ×20<br/>魔术贴绑带20×200mm ×2','按左列数量'),
    ('绝缘与固定','2:1热缩管：直径2/3/5mm各0.3m<br/>双面泡棉胶10×1mm，长0.5m','按左列数量'),
]
FIX_ROWS=[
    ('隔离柱','M3×20mm双通尼龙柱 ×4<br/>M3×6mm双通尼龙柱 ×8<br/>M2.5×6mm双通尼龙柱 ×4','共16只'),
    ('螺丝 / 螺母 / 垫片','M3×6mm螺丝 ×24；M3×10mm螺丝 ×12<br/>M3螺母 ×20；M3平垫 ×30<br/>M2.5×6mm螺丝 ×8；M2.5螺母 ×4<br/>M4×8mm螺丝 ×2；M4平垫 ×2','按左列数量<br/>普通十字盘头'),
    ('排针','2.54mm直排针：2×20P ×2、2×5P ×1','各按左列数量'),
]

def generate(role):
    story=[]
    def add(s,style='p'): story.append(par(s,style))
    def table(headers,rows,widths):
        data=[[par(s,'th') for s in headers]]
        data.extend([[par(str(s),'cell') for s in row] for row in rows])
        t=Table(data,colWidths=widths,repeatRows=1,hAlign='LEFT')
        t.setStyle(TableStyle([
            ('BACKGROUND',(0,0),(-1,0),NAVY),('VALIGN',(0,0),(-1,-1),'TOP'),
            ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,PALE]),
            ('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),
            ('TOPPADDING',(0,0),(-1,-1),5.5 if role=='hardware' else 7),
            ('BOTTOMPADDING',(0,0),(-1,-1),5.5 if role=='hardware' else 7),
            ('LINEBELOW',(0,-1),(-1,-1),.5,LINE),
        ]))
        story.append(t)
        story.append(Spacer(1,6))
    add(TITLES[role],'title')
    add('按原完整采购方案分配 / 原编号用于对账 / 2026-10-10','sub')
    add(f'本单器件预计 <b>{money(TOTALS[role])} 元</b>（未含运费）。主控207.8元、视觉211.0元、硬件207.0元，三人器件合计625.8元。全队另留20元运费/价差，计划合计645.8元。')
    add('金额沿用原清单的展示价或预算估算，本次未重新核价；最终以实际订单为准。型号按原F407方案。蓝色文字可点击；标准件按规格搜索购买。','small')
    rows=[]
    for i,q in ALLOCATIONS[role]:
        item=ITEMS[i]
        desc,entry=INFO[i]
        status='原展示价' if item['price_status']=='官网展示价' else '估算'
        rows.append((i,desc,str(q),money(item['unit_budget']),money(Decimal(str(item['unit_budget']))*q)+'<br/>'+status,entry))
    table(['编号','型号 / 必须选择的规格','数量','单价','小计','购买入口 / 搜索词'],rows,[34,216,34,42,57,CW-383])
    if role=='control':
        add('下单核对与交接','h')
        add('1. 驱动板选 AT8236 Standard 标准版；电池选2S、800mAh、XT30，充电器选UC2。确认电池平衡头与UC2的2S口匹配。<br/>2. 第18项是上表全部电容、电阻，各按数量买齐；不另买整套“电子元件大礼包”。<br/>3. DAPLink订单检查下载线；未含时可用硬件队员购买的杜邦线连接。<br/>4. 本人买1根USB数据线。充电用USB电源由硬件队员购买；车上电源接头及紧固件也由硬件队员负责。')
        add('收到后：记录实付款，核对板子和电池接口；把电池/充电器交给硬件队员统一检查，再开展供电和电机调试。','small')
    elif role=='vision':
        add('视觉套件需要包含什么','h')
        add('核对订单为 Lite-K230D-CanMV 128MB 标准套件，含GC2093小镜头定焦摄像头。原厂家包装图还列出摄像头钣金支架、安装小螺丝和GH1.25转杜邦线；赠品以订单为准。')
        add('如果赠品缺少，请按下列规格补缺：GH1.25-4P→2.54mm杜邦母头线，至少1条，用于与主控串口通信。追加费用记录到全队对账中。','small')
        add('下单核对与交接','h')
        add('1. TF卡需要单买1张，规格8GB、Class 10。<br/>2. 本人只买1根USB数据线，主控另外买1根；选可传数据的A-to-C线。<br/>3. 散热片需带绝缘导热胶贴；若套件已含相同散热件，记录后从本单扣掉，避免重复买。<br/>4. 摄像头不另买第二套。扬声器、扬声器转接线、视觉安装台和固定件由硬件队员购买。')
        add('收到后：先拍包装与配件照片，完成摄像头画面测试；将安装孔位、随配线材和支架交给硬件队员核对装车。','small')
    else:
        add('电机与轮组的关键选项','h')
        add('两只电机在同一店购买相同规格，选“Motor+Bracket+Coupling”：每套含支架和3mm轴孔、12mm六角联轴器；另买经典橡胶轮2只。默认带轮电机套装使用48mm轮，勿用它替代本单轮组。','small')
        add('第10项含4只60mm铝合金柱；第17项不再重复买这4只。电机套装应含PH2.0-6P编码器线、支架螺丝和联轴器顶丝，按订单检查随配数量。第16、17项详细内容见下一页。','small')
        story.append(PageBreak())
        add('硬件队员 / 配件展开表','title')
        add('以下全部归硬件队员采购 / 两组预算已计入第1页，不能再重复加总','sub')
        add('第16项 / 接线与耗材 / 整组预计30元','h')
        table(['类别','精确规格','数量'],WIRE_ROWS,[87,340,CW-427])
        add('第17项 / 紧固件与排针 / 整组预计15元','h')
        table(['类别','精确规格','数量'],FIX_ROWS,[87,340,CW-427])
        add('配件数量与接口核对','h')
        add('1. 喇叭自带PH2.0线，视觉板扬声器座需要MX1.25-2P转接；MX1.25和GH1.25不能互换。<br/>2. M4×8mm螺丝用于轮子与六角联轴器固定。M3×20mm柱用于后支撑轮；60mm铝合金柱只在第10项购买。<br/>3. 若主控板订单已附相同排针，扣掉重复排针并记录；电容/电阻由主控队员购买。<br/>4. USB电源交给主控队员配UC2充电器使用；喇叭和转接线交给视觉队员测试。')
        add('标准件有最小包装数量时，买能覆盖需求的最小包装，记录余量和实际费用。组预算是估算；按表逐项核对，不能用商品标题相似的“大礼包”代替。','small')
    add('采购与对账约定','h')
    add('每人只按本单数量下单；提交订单截图和实付款，包含运费。配件取消重复购买或增加补缺时，三人同步记账。若希望最终平均出资，可把实际总支出除以3，再结算差额。','small')
    add('原方案工具、练习赛道未计入器件预算，装配工具优先借用。来源：hardware_preparation/hardware_purchase_list.pdf。本单是该方案的分工版本。','small')
    pages=2 if role=='hardware' else 1
    def footer(c,doc):
        c.saveState()
        c.setStrokeColor(LINE)
        c.line(36,35,W-36,35)
        c.setFont('CN',8)
        c.setFillColor(GRAY)
        c.drawString(36,22,'SMART CAR / PERSONAL PURCHASE LIST / 2026-10-10')
        c.drawRightString(W-36,22,f'{doc.page} / {pages}')
        c.restoreState()
    path=BASE/f'purchase_list_{role}.pdf'
    SimpleDocTemplate(str(path),pagesize=A4,leftMargin=36,rightMargin=36,topMargin=34,bottomMargin=48,
        title=TITLES[role],author='Codex').build(story,onFirstPage=footer,onLaterPages=footer)
    return path

for role in ALLOCATIONS:
    print(generate(role),money(TOTALS[role]))
(BASE/'source'/'team_purchase_allocation.json').write_text(json.dumps({
    'date':'2026-10-10','source':'hardware_purchase_list.pdf',
    'allocations':{role:{'buyer':NAMES[role],'rows':[{'source_id':i,'quantity':q} for i,q in rows],
        'parts_total':float(TOTALS[role])} for role,rows in ALLOCATIONS.items()},
    'parts_total':625.8,'shared_shipping_price_allowance':20,'planned_total':645.8,
    'budget_note':'All prices carried forward from the source PDF; no new merchant quotes. Tools and practice track excluded.'
},ensure_ascii=False,indent=2),encoding='utf-8')
