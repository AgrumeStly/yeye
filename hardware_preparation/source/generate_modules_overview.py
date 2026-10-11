from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer, PageBreak

BASE = Path(__file__).resolve().parents[1]
OUTPUT = BASE / 'hardware_modules_overview.pdf'
pdfmetrics.registerFont(TTFont('CN', r'C:\Windows\Fonts\simhei.ttf'))
NAVY = colors.HexColor('#17364A')
TEAL = colors.HexColor('#087F8C')
MUTED = colors.HexColor('#526875')
PALE = colors.HexColor('#EEF6F8')
RULE = colors.HexColor('#D6E3E8')
W, H = A4
CW = W-72
styles = {
    'title': ParagraphStyle('title',fontName='CN',fontSize=23,leading=30,textColor=NAVY,spaceAfter=9),
    'sub': ParagraphStyle('sub',fontName='CN',fontSize=10,leading=15,textColor=MUTED,spaceAfter=12),
    'head': ParagraphStyle('head',fontName='CN',fontSize=13,leading=18,textColor=TEAL,spaceBefore=11,spaceAfter=7),
    'body': ParagraphStyle('body',fontName='CN',fontSize=10,leading=16,textColor=NAVY,wordWrap='CJK',spaceAfter=7),
    'cell': ParagraphStyle('cell',fontName='CN',fontSize=9.3,leading=14,textColor=NAVY,wordWrap='CJK'),
    'th': ParagraphStyle('th',fontName='CN',fontSize=9.3,leading=14,textColor=colors.white,wordWrap='CJK'),
    'small': ParagraphStyle('small',fontName='CN',fontSize=8.6,leading=13,textColor=MUTED,wordWrap='CJK',spaceAfter=6),
}
story=[]
def add(s,style='body'):
    story.append(Paragraph(s,styles[style]))
def table(headers,rows,widths):
    data=[[Paragraph(s,styles['th']) for s in headers]]
    data.extend([[Paragraph(s,styles['cell']) for s in row] for row in rows])
    t=Table(data,colWidths=widths,repeatRows=1,hAlign='LEFT')
    t.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),NAVY),
        ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,PALE]),
        ('VALIGN',(0,0),(-1,-1),'TOP'),
        ('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8),
        ('TOPPADDING',(0,0),(-1,-1),8),('BOTTOMPADDING',(0,0),(-1,-1),8),
        ('LINEBELOW',(0,-1),(-1,-1),.6,RULE),
    ]))
    story.append(t)
    story.append(Spacer(1,6))

add('智能小车硬件模块清单','title')
add('第1页 / 完赛基础系统 · 模块规划与后续选型依据 · 2026-10-10','sub')
add('先确定需要哪些功能模块，再逐项确定规格、集成方式和预算。下表参考容易搭建的双轮差速结构；所有模块名称表示功能，不代表必须各买一块独立电路板。')
table(['部分','需要的模块 / 大致数量','负责什么'],[
    ('视觉','摄像头及镜头：1套<br/>视觉处理单元：1套<br/>必要的连接线、存储与散热','识别黑色边界、车道方向、急弯和起终点；输出路径偏差及识别可信度。存储和散热按后续平台需要配置。'),
    ('主控','运动控制单元：1套<br/>启动按键、状态指示<br/>程序下载与调试接口','接收视觉结果，计算左右轮目标速度；执行速度控制、转向、减速和停车。按键/指示可集成在板上。'),
    ('通信','视觉与主控的有线通信接口<br/>信号线与对应接头：1套','传递路径结果、运行状态和语音指令。接口可以由两块板直接提供，未必需要额外转接模块。'),
    ('动力与反馈','驱动电机：2只<br/>电机驱动：双路或单路×2<br/>轮速编码器：每个电机1套','电机提供动力，驱动电路控制正反转/刹车，编码器测轮速以形成闭环。编码器可随电机集成。'),
    ('机械结构','底板/车架：1套<br/>驱动轮：2只；后支撑轮：1套<br/>电机支架、轮毂/联轴器<br/>摄像头支架、电池固定件','承载各模块，保证轮组、轴径和安装孔匹配；摄像头固定可靠，电池低位布置。'),
    ('供电','可充电电池：1套<br/>电源转换与分配：1套<br/>总开关、电压监测与滤波<br/>匹配电池的充电设备：1套','为电机和电子模块提供合适电压及电流；监测低电量。充电设备包含所需电源和连接线。'),
    ('连接与安装','电源线、信号线、插头、排针<br/>螺丝、螺母、垫片、隔离柱<br/>绝缘材料、热缩管、线束固定件','完成实际装车。接线与紧固配件随具体接口、孔位及布局确定数量。'),
],[72,220,CW-292])
add('各部分如何配合','head')
add('摄像头 → 视觉处理 → 主控 → 电机驱动 → 电机与车轮<br/>编码器 → 主控（反馈实际轮速）<br/>电池 → 电源转换/分配 → 各电子模块及动力部分')
add('对高速稳定完赛而言，编码器、稳固的摄像头支架、可靠供电和急弯减速能力都值得优先保留。底层模块可以集成，功能仍需完整。','small')

story.append(PageBreak())
add('加分功能与准备事项','title')
add('第2页 / 语音、可选升级、装配工具与下一轮决策','sub')
add('语音与自动停车：建议规划的加分功能','head')
table(['功能','需要的模块','集成方式'],[
    ('语音采集与识别','麦克风、音频采集<br/>离线语音识别处理能力','可由视觉处理单元兼任，也可使用独立语音模块；识别须在车上完成。'),
    ('语音应答','音频播放、功放、扬声器','播放预录应答即可；功放和播放能力可能已在处理板上集成。'),
    ('冲线自动停车','终点识别能力<br/>一圈完成判断与停车控制','先考虑复用摄像头、编码器和主控程序；是否增加传感器，等实际识别效果再定。'),
],[102,194,CW-296])
add('按比赛要求规划语音启动、冲线后语音接管停车、语音应答及不少于两条自选指令。语音是额外功能；基础完赛可先通过按键启动。','small')
add('可选升级模块：后续按实际问题选择','head')
table(['模块','什么时候考虑'],[
    ('惯性测量单元','需要测转动、辅助判断急弯或短时视觉失效时考虑；先确认数据确实能改善控制。'),
    ('辅助灰度/循迹传感器','需要近处边界或终点的辅助识别时考虑。不能默认能够代替完整视觉方案。'),
    ('调试显示、日志存储或通信','需要观察数据、定位丢线原因时考虑；调试接口也可复用已有板上接口。'),
],[155,CW-155])
add('装配与验证需要准备','head')
add('开发电脑及数据线；下载调试工具（若开发板需要）；万用表、焊接与剥线工具、螺丝刀、必要的开孔工具；直尺、电子秤；白色路面与黑色边界材料组成的练习赛道。工具可以借用，后续预算要单独统计。')
add('下一轮逐项确定的五件事','head')
add('1. 主控：能否复用已有板，接口和定时器是否够用。<br/>2. 视觉：摄像头、处理单元，以及是否兼任语音。<br/>3. 动力：目标速度与整车重量，决定电机、轮径及驱动能力。<br/>4. 供电：电池、电源转换、充电设备和接口是否匹配。<br/>5. 结构：整车尺寸、布局、固定方式和加工难度。')
add('比赛约束与资料依据','head')
add('依据工作区《比赛文档.pdf》：整车长≤30cm、宽≤20cm、高≤25cm，含电池总重≤5kg；使用可充电电池；在净宽50cm、含锐角转弯的车道内自主完成一圈，计算及语音处理均在车上完成。','small')
add('后续预算应同时覆盖车上模块、充电/下载配件及安装耗材；可借用工具和练习赛道另外列账。','small')

def footer(c,doc):
    c.saveState()
    c.setStrokeColor(RULE)
    c.line(36,35,W-36,35)
    c.setFont('CN',8)
    c.setFillColor(MUTED)
    c.drawString(36,22,'SMART CAR / HARDWARE MODULES / 2026-10-10')
    c.drawRightString(W-36,22,f'{doc.page} / 2')
    c.restoreState()

SimpleDocTemplate(str(OUTPUT),pagesize=A4,leftMargin=36,rightMargin=36,topMargin=34,bottomMargin=48,
    title='智能小车硬件模块清单',author='Codex').build(story,onFirstPage=footer,onLaterPages=footer)
print(OUTPUT)
