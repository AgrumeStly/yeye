"""Generate the Chinese beginner guide from its editable Markdown source."""
from html import escape
from pathlib import Path
import re

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer, PageBreak,
    Flowable, Preformatted, KeepTogether,
)

BASE = Path(__file__).resolve().parents[1]
SOURCE = BASE / 'github_collaboration_guide.md'
OUTPUT = BASE / 'github_collaboration_guide.pdf'
pdfmetrics.registerFont(TTFont('CN', 'C:/Windows/Fonts/simhei.ttf'))
pdfmetrics.registerFontFamily('CN', normal='CN', bold='CN', italic='CN', boldItalic='CN')
NAVY = colors.HexColor('#18394B')
TEAL = colors.HexColor('#087F8C')
MUTED = colors.HexColor('#58707F')
PALE = colors.HexColor('#EDF5F7')
RULE = colors.HexColor('#D5E3E9')
W, H = A4
CW = W - 76
styles = {
    'title': ParagraphStyle('title', fontName='CN', fontSize=20, leading=26,
                            textColor=NAVY, spaceAfter=12, wordWrap='CJK'),
    'head': ParagraphStyle('head', fontName='CN', fontSize=12, leading=18,
                           textColor=TEAL, spaceBefore=9, spaceAfter=6, keepWithNext=True),
    'body': ParagraphStyle('body', fontName='CN', fontSize=10, leading=16,
                           textColor=NAVY, spaceAfter=7, wordWrap='CJK'),
    'note': ParagraphStyle('note', fontName='CN', fontSize=8.8, leading=13.5,
                           textColor=MUTED, spaceAfter=6, wordWrap='CJK'),
    'cell': ParagraphStyle('cell', fontName='CN', fontSize=9, leading=14,
                           textColor=NAVY, wordWrap='CJK'),
    'th': ParagraphStyle('th', fontName='CN', fontSize=9, leading=14,
                         textColor=colors.white, wordWrap='CJK'),
    'code': ParagraphStyle('code', fontName='CN', fontSize=9, leading=14,
                           textColor=NAVY, leftIndent=9, rightIndent=9,
                           spaceBefore=5, spaceAfter=8, backColor=PALE, borderPadding=9),
}


def inline(s):
    """Support only the inline Markdown used in this document."""
    s = escape(s)
    s = re.sub(r'\[([^\]]+)\]\((https?://[^\s)]+)\)',
               lambda m: f'<a href="{m.group(2)}" color="#087F8C">{m.group(1)}</a>', s)
    s = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', s)
    s = re.sub(r'`([^`]+)`', r'\1', s)
    return s


class Workflow(Flowable):
    def __init__(self):
        Flowable.__init__(self)
        self.width, self.height = CW, 76

    def draw(self):
        c = self.canv
        labels = [('工作文件', 'Save / 保存'), ('本地历史', 'Commit / 提交'),
                  ('网页分支', 'Push / 上传'), ('共享main', 'PR / 合并')]
        bw = 116
        for i, (title, sub) in enumerate(labels):
            x = i * (CW-bw) / 3
            c.setFillColor(PALE if i != 3 else NAVY)
            c.roundRect(x, 16, bw, 53, 6, fill=1, stroke=0)
            c.setFillColor(NAVY if i != 3 else colors.white)
            c.setFont('CN', 11); c.drawCentredString(x+bw/2, 48, title)
            c.setFont('CN', 8.7); c.drawCentredString(x+bw/2, 29, sub)
            if i < 3:
                c.setFillColor(TEAL); c.setFont('CN', 10)
                c.drawCentredString(x+bw+9, 38, '>')


class DesktopUI(Flowable):
    def __init__(self):
        Flowable.__init__(self)
        self.width, self.height = CW, 158

    def draw(self):
        c = self.canv
        c.setStrokeColor(RULE); c.setFillColor(colors.white)
        c.roundRect(0, 6, CW, 148, 5, fill=1, stroke=1)
        c.setFillColor(NAVY); c.rect(0, 116, CW, 38, fill=1, stroke=0)
        c.setFillColor(colors.white); c.setFont('CN', 8.8)
        for x, title, val in [(10,'Current Repository','yeye'),(180,'Current Branch','vision/lane-basic'),
                              (363,'同步按钮','Fetch / Pull / Push')]:
            c.drawString(x, 141, title); c.setFont('CN', 10); c.drawString(x, 125, val); c.setFont('CN', 8.8)
        c.setStrokeColor(RULE); c.line(165, 6, 165, 116)
        c.setFillColor(TEAL); c.setFont('CN', 10)
        c.drawString(12, 98, 'Changes | History')
        c.setFillColor(NAVY); c.setFont('CN', 9)
        c.drawString(12, 79, '修改文件 / 提交历史')
        c.drawString(12, 52, 'Summary + Description')
        c.setFillColor(TEAL); c.roundRect(12, 15, 141, 23, 3, fill=1, stroke=0)
        c.setFillColor(colors.white); c.setFont('CN', 8.3)
        c.drawCentredString(82, 23, 'Commit to 当前分支')
        c.setFillColor(NAVY); c.setFont('CN', 11)
        c.drawString(183, 86, '右侧：文件修改前后的差异')
        c.setFont('CN', 9); c.drawString(183, 61, '先看懂变化，再决定哪些文件提交')
        c.setFillColor(MUTED); c.drawString(183, 31, '界面示意 / 非真实软件截图')


class GuideDocument(SimpleDocTemplate):
    def afterFlowable(self, flowable):
        if isinstance(flowable, Paragraph) and flowable.style.name == 'title':
            title = flowable.getPlainText()
            key = f'chapter-{self.page}'
            self.canv.bookmarkPage(key)
            self.canv.addOutlineEntry(title, key, level=0)


content = SOURCE.read_text(encoding='utf-8')
sections = re.split(r'^# ', content, flags=re.M)[1:]
story = []
for section_id, section in enumerate(sections, start=1):
    if story:
        story.append(PageBreak())
    lines = section.splitlines()
    title = lines[0].strip()
    story.append(Paragraph(inline(title), styles['title']))
    story.append(Paragraph(f'{section_id:02d} / SMART CAR TEAM / GITHUB DESKTOP', styles['note']))
    i = 1
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1; continue
        if line.startswith('## '):
            story.append(Paragraph(inline(line[3:]), styles['head']))
        elif line == '[[workflow]]':
            story.append(Workflow())
        elif line == '[[desktop_ui]]':
            story.append(DesktopUI())
        elif line.startswith('```'):
            code = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith('```'):
                code.append(lines[i]); i += 1
            story.append(Preformatted('\n'.join(code), styles['code']))
        elif line.startswith('|'):
            rows = []
            while i < len(lines) and lines[i].strip().startswith('|'):
                cells = [s.strip() for s in lines[i].strip().strip('|').split('|')]
                if not all(re.fullmatch(r':?-+:?', cell) for cell in cells):
                    rows.append(cells)
                i += 1
            i -= 1
            count = len(rows[0])
            if section_id == 1:
                widths = [62, 325, CW-387]
            elif section_id == 2:
                widths = [108, 157, CW-265]
            elif count == 2:
                widths = [111, CW-111]
            else:
                widths = [109, 169, CW-278]
            table = Table([[Paragraph(inline(cell), styles['th'] if j == 0 else styles['cell'])
                            for cell in row] for j, row in enumerate(rows)],
                          colWidths=widths, repeatRows=1, hAlign='LEFT')
            table.setStyle(TableStyle([
                ('BACKGROUND',(0,0),(-1,0),NAVY),
                ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white, PALE]),
                ('VALIGN',(0,0),(-1,-1),'TOP'),
                ('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),
                ('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6),
                ('LINEBELOW',(0,-1),(-1,-1),.5,RULE),
            ]))
            story.extend([table, Spacer(1,8)])
        else:
            style = 'note' if line.startswith('依据：') or section_id == 21 and line.startswith('- ') else 'body'
            story.append(Paragraph(inline(line), styles[style]))
        i += 1


def footer(c, doc):
    c.saveState()
    c.setStrokeColor(RULE); c.line(38, 37, W-38, 37)
    c.setFillColor(MUTED); c.setFont('CN', 8)
    c.drawString(38, 23, 'YEYE / GITHUB COLLABORATION GUIDE / 2026-10-11')
    c.drawRightString(W-38, 23, f'{doc.page} / {len(sections)}')
    c.restoreState()


GuideDocument(str(OUTPUT), pagesize=A4, leftMargin=38, rightMargin=38,
              topMargin=34, bottomMargin=51, title='GitHub三人协作操作手册',
              author='智能赛车项目团队').build(story, onFirstPage=footer, onLaterPages=footer)
from pypdf import PdfReader
actual = len(PdfReader(OUTPUT).pages)
if actual != len(sections):
    raise RuntimeError(f'Layout overflow: {actual} pages for {len(sections)} chapters; repair before delivery')
print(f'{OUTPUT} / {actual} pages')
