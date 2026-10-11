from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer, PageBreak

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'team_work_outline.pdf'
pdfmetrics.registerFont(TTFont('CN', r'C:\Windows\Fonts\simhei.ttf'))
NAVY = colors.HexColor('#17364A')
TEAL = colors.HexColor('#087F8C')
MUTED = colors.HexColor('#526875')
PALE = colors.HexColor('#EEF6F8')
RULE = colors.HexColor('#D6E3E8')
W, H = A4
CW = W - 72
styles = {
    'title': ParagraphStyle('title',fontName='CN',fontSize=23,leading=30,textColor=NAVY,spaceAfter=8),
    'sub': ParagraphStyle('sub',fontName='CN',fontSize=10,leading=15,textColor=MUTED,spaceAfter=10),
    'head': ParagraphStyle('head',fontName='CN',fontSize=13,leading=18,textColor=TEAL,spaceBefore=10,spaceAfter=6),
    'body': ParagraphStyle('body',fontName='CN',fontSize=10.2,leading=16,textColor=NAVY,spaceAfter=7,wordWrap='CJK'),
    'small': ParagraphStyle('small',fontName='CN',fontSize=8.8,leading=13,textColor=MUTED,spaceAfter=5,wordWrap='CJK'),
    'cell': ParagraphStyle('cell',fontName='CN',fontSize=9.2,leading=14,textColor=NAVY,wordWrap='CJK'),
    'th': ParagraphStyle('th',fontName='CN',fontSize=9.2,leading=14,textColor=colors.white,wordWrap='CJK'),
}
story = []
def add(s,style='body'):
    story.append(Paragraph(s,styles[style]))
def table(headers,rows,widths):
    data = [[Paragraph(s,styles['th']) for s in headers]]
    data += [[Paragraph(s,styles['cell']) for s in row] for row in rows]
    t = Table(data,colWidths=widths,repeatRows=1,hAlign='LEFT')
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

add('三人参赛分工大纲','title')
add('第1页 / 每个人负责什么 · 主控、视觉、硬件 · 2026-10-10','sub')
add('共同目标：先稳定跑完一圈，再逐步提速，同时完成加分功能和报告。','head')
add('主控让车按要求行动，视觉让车看清赛道，硬件让车可靠地跑起来。三个人各有主责，整车调试和赛前演练一起完成。')
add('按比赛评分：行驶功能60分，语音及自动停车等额外功能40分，报告20分。跑得快、少碰边、功能可靠、能讲清楚设计，都影响成绩。','small')

add('你 / 主控：负责小车的行动和整车协调','head')
add('1. 学会给控制板下载程序，让电机前进、后退、转向和停车。<br/>2. 接收视觉队友给的方向信息，让车沿赛道行驶，尽量走稳。<br/>3. 调整速度：直道加速，急弯减速；看不清路时能减速或停车。<br/>4. 接入启动、语音命令和终点停车，协调各部分一起工作。<br/>5. 汇总试跑问题、程序版本和报告内容，安排联调。')
add('交付给队友：能控制车运动的程序、大家都理解的信息约定，以及一套可重复使用的启动和停车流程。','small')

add('视觉队员 / 熟悉 Python：负责看路和识别','head')
add('1. 学会使用摄像头，能拍照、看画面、保存测试图片。<br/>2. 找到赛道两边，判断车偏向哪侧、前方往哪边转。<br/>3. 告诉主控：方向怎么调、前方是否急弯、这次是否看清楚。<br/>4. 测试直道、急弯、阴影和起终点，减少误认和漏认。<br/>5. 牵头实现语音识别和应答；由主控执行动作，硬件配合安装。')
add('交付给队友：稳定的赛道判断结果、标出识别效果的图片，以及能在车上运行的视觉程序。','small')

add('硬件队员 / 从基础开始：负责车体和供电','head')
add('1. 整理需要的模块和配件，核对尺寸、接口与安装是否匹配。<br/>2. 装底盘、电机、轮子和摄像头，把各模块固定牢靠。<br/>3. 学会接线、焊接和检查供电，避免松线、掉电、轮子卡住。<br/>4. 试跑后检查车身抖动、轮胎打滑和发热，配合调整布局。<br/>5. 准备练习赛道、充电设备和备件，记录接线与安装照片。')
add('交付给队友：接线清楚、供电稳定、结构牢固的小车；对应的实物照片和配件记录。','small')

add('三个人必须一起做的事','head')
add('一起确认规则和采购方案；一起试跑、看录像、找问题；各自写清自己的工作。队长负责报名及通知确认，主控队员可牵头汇总进度和最终报告。')

story.append(PageBreak())
add('从准备到比赛怎么推进','title')
add('第2页 / 六个阶段 · 以做出的成果判断是否进入下一步','sub')
table(['阶段','三个人分别做什么','这一阶段完成的标志'],[
    ('1 / 准备与学习','主控：认识控制板，跑通最简单程序。<br/>视觉：认识摄像头，能获取和保存画面。<br/>硬件：列配件，了解接线和装车方法。','共同确认方案、采购清单和分工；每个人知道自己的第一步。'),
    ('2 / 各自跑通基础','主控：让车轮按要求转动和停止。<br/>视觉：在样例图和实拍图上找到赛道。<br/>硬件：完成装车，检查供电和固定。','车能受程序控制；视觉有可用结果；车体可以安全试跑。'),
    ('3 / 联动低速完赛','主控：用视觉结果控制转向和速度。<br/>视觉：跟着实车处理识别不准的位置。<br/>硬件：修正松动、歪斜、抖动等问题。','队内建议目标：连续3次低速试跑均完成一圈，尽量不碰边，能按要求停车。'),
    ('4 / 逐步提高速度','主控：分段调整直道和弯道速度。<br/>视觉：提前识别弯道，减少画面延迟。<br/>硬件：检查打滑、发热和摄像头晃动。','记录用时和失误；提速后仍能连续稳定完赛。每次只改少量设置。'),
    ('5 / 加分与报告','主控：执行语音动作和终点停车。<br/>视觉：识别命令、播放应答、判断终点。<br/>硬件：安装麦克风/喇叭，整理实物资料。','演示语音启动、接管、应答和自选指令；整合报告与试跑证据。'),
    ('6 / 赛前与现场','主控：保存稳定程序，演练启动和停车。<br/>视觉：检查现场画面，确认识别稳定。<br/>硬件：充电、检查接线、准备工具备件。','完整模拟一次验收；明确现场操作分工和出问题时的恢复步骤。'),
],[68,285,CW-353])

add('想取得好成绩，重点盯住这四件事','head')
add('稳定：连续多次完赛，少碰边，出问题能定位。<br/>速度：在稳定的基础上缩短用时，急弯提前减速。<br/>功能：语音要清楚可靠；自动停车要能重复演示。<br/>表达：三个人都能说明自己的工作、遇到的问题和改进办法。')
add('约定一个简单的合作节奏','head')
add('每次开工前说清当天目标；结束时留下程序、照片和问题记录。联调时三个人尽量在场，把“车不对劲”说成具体表现，例如某个弯冲出去、突然停电或识别错了方向。')
add('赛前核对','head')
add('尺寸、重量和电池符合要求；完整跑一圈；冲线后语音接管可在3秒内停稳；能演示不少于两条自选语音指令；报告、稳定程序和充电/工具/备件准备齐全。自动停车作为额外加分项安排。','small')
add('依据：competition/比赛文档.pdf 第2-4页。阶段顺序及“连续3次试跑”为团队建议目标，正式赛程和评分解释以主办方通知为准。','small')

def footer(c,doc):
    c.saveState()
    c.setStrokeColor(RULE)
    c.line(36,35,W-36,35)
    c.setFont('CN',8)
    c.setFillColor(MUTED)
    c.drawString(36,22,'SMART CAR / TEAM WORK OUTLINE / 2026-10-10')
    c.drawRightString(W-36,22,f'{doc.page} / 2')
    c.restoreState()

SimpleDocTemplate(str(OUTPUT),pagesize=A4,leftMargin=36,rightMargin=36,topMargin=34,bottomMargin=48,
    title='三人参赛分工大纲',author='Codex').build(story,onFirstPage=footer,onLaterPages=footer)
print(OUTPUT)
