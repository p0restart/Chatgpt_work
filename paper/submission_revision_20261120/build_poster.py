"""Create a source-grounded A0 conference poster with editable SVG and vector PDF."""
from pathlib import Path
import sys, json, re, zipfile, hashlib
from xml.etree import ElementTree as E
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor

R=Path(__file__).resolve().parent
OUT=R/'conference_poster'; OUT.mkdir(exist_ok=True)
sys.path.append(str(R/'qa/python_deps'))
import fitz

W,H=841/25.4*72,1189/25.4*72
M=85; G=78; CW=(W-2*M-G)/2; LX=M; RX=M+CW+G
NAVY='#112E46'; TEAL='#007E87'; TEXT='#233947'; GRAY='#536570'; LINE='#CAD7DF'; WHITE='#FFFFFF'
for name,file in [('Arial','arial.ttf'),('Arial-Bold','arialbd.ttf'),('Arial-Italic','ariali.ttf')]:
    pdfmetrics.registerFont(TTFont(name,'C:/Windows/Fonts/'+file))
NS='http://www.w3.org/2000/svg'; E.register_namespace('',NS)
E.register_namespace('xlink','http://www.w3.org/1999/xlink')
svg=E.Element('{%s}svg'%NS,{'width':'841mm','height':'1189mm','viewBox':f'0 0 {W} {H}'})
c=canvas.Canvas(str(OUT/'layout.pdf'),pagesize=(W,H))
c.setTitle('A Resource-Constrained Network Defense Decision Method Based on a Nonzero-Sum Differential Game')
c.setAuthor('Author information to be completed')
records=[]; figures=[]

def rect(x,y,w,h,fill):
    c.setFillColor(HexColor(fill)); c.rect(x,H-y-h,w,h,stroke=0,fill=1)
    E.SubElement(svg,'{%s}rect'%NS,{'x':str(x),'y':str(y),'width':str(w),'height':str(h),'fill':fill})

def line(x,y,x2,y2,color=LINE,width=2):
    c.setStrokeColor(HexColor(color)); c.setLineWidth(width); c.line(x,H-y,x2,H-y2)
    E.SubElement(svg,'{%s}line'%NS,{'x1':str(x),'y1':str(y),'x2':str(x2),'y2':str(y2),'stroke':color,'stroke-width':str(width)})

def text(x,y,s,size=30,bold=False,color=TEXT,italic=False):
    # y is the top of the text box, with a common baseline across both exports.
    font='Arial-Bold' if bold else ('Arial-Italic' if italic else 'Arial')
    baseline=y+size*.87
    c.setFont(font,size); c.setFillColor(HexColor(color)); c.drawString(x,H-baseline,s)
    a={'x':str(x),'y':str(baseline),'font-family':'Arial','font-size':str(size),'fill':color}
    if bold:a['font-weight']='700'
    if italic:a['font-style']='italic'
    E.SubElement(svg,'{%s}text'%NS,a).text=s
    width=pdfmetrics.stringWidth(s,font,size)
    records.append({'text':s,'x':x,'y':y,'width':width,'size':size})
    assert x>=0 and x+width<W-20,(s,x+width,W)
    return y+size*1.2

def para(x,y,s,width=CW,size=30,leading=43,bold=False,color=TEXT):
    font='Arial-Bold' if bold else 'Arial'; words=s.split(); rows=[]; row=''
    for word in words:
        new=(row+' '+word).strip()
        if row and pdfmetrics.stringWidth(new,font,size)>width:
            rows.append(row); row=word
        else:row=new
    if row:rows.append(row)
    for n,row in enumerate(rows):text(x,y+n*leading,row,size,bold,color)
    return y+len(rows)*leading

def section(x,y,num,title):
    text(x,y,num,31,True,TEAL)
    text(x+65,y-2,title,41,True,NAVY)
    line(x,y+59,x+CW,y+59)

def figure(name,x,y,w):
    src=R/'latex/figures'/name
    pdf=fitz.open(src.with_suffix('.pdf')); p=pdf[0]; h=w*p.rect.height/p.rect.width; pdf.close()
    figures.append((src.with_suffix('.pdf'),(x,y,x+w,y+h)))
    # Embed the original vector SVG, while avoiding duplicate IDs across plots.
    root=E.fromstring(src.with_suffix('.svg').read_text(encoding='utf-8'))
    prefix=name+'_'
    for el in root.iter():
        if 'id' in el.attrib:el.set('id',prefix+el.attrib['id'])
        for key,value in list(el.attrib.items()):
            value=re.sub(r'url\(#([^)]+)\)',lambda m:'url(#'+prefix+m[1]+')',value)
            if key.endswith('href') and value.startswith('#'):value='#'+prefix+value[1:]
            el.set(key,value)
    view=[float(v) for v in root.attrib['viewBox'].split()]
    group=E.SubElement(svg,'{%s}g'%NS,{'transform':f'translate({x},{y}) scale({w/view[2]},{h/view[3]})'})
    for child in list(root):group.append(child)
    return y+h

rect(0,0,W,H,WHITE)
rect(0,0,W,22,TEAL)
text(M,68,'NETWORK SECURITY / NONZERO-SUM DIFFERENTIAL GAMES',27,True,TEAL)
for y,s in [(135,'A Resource-Constrained Network Defense'),
            (232,'Decision Method Based on a Nonzero-Sum'),
            (329,'Differential Game')]:
    text(M,y,s,87,True,NAVY)
text(M,446,'[Author names in manuscript order]',34,True,NAVY)
text(M,497,'[Department, University / Organization, City, Country]     [Corresponding email]',28,color=GRAY)
line(M,557,W-M,557,LINE,3)
rect(M,594,W-2*M,183,'#EEF7F6')
para(M+31,620,'Scheduling isolation and recovery reduces cumulative loss',W-2*M-62,43,56,True,NAVY)
para(M+31,680,'Main capacity B = 1.2. The attack plan is computed jointly with dynamic defense and then fixed for all comparisons.',W-2*M-62,31,43,color=TEXT)

section(LX,842,'01','Model and decision problem')
para(LX,929,'Choose source isolation and local recovery for each asset and time interval while attacks propagate across a directed network.',size=31,leading=44)
end=figure('fig1_network_en',LX+225,1080,620)
para(LX,1570,'Six logical assets. Direct attacks enter at the API gateway and Web application. Recovery lowers local compromise; isolation suppresses outgoing propagation.',size=29,leading=41)

section(LX,1778,'02','Compute a defense schedule')
para(LX,1864,'ABR-DAD: Alternating Best Response for Dynamic Defense Action Decision.',size=30,leading=42,bold=True)
steps=[
 '1  Parameterize controls over six time intervals.',
 '2  Fix the attack plan and optimize defense locally.',
 '3  Fix defense and optimize the attack locally.',
 '4  Repeat, then check unilateral deviations and feasibility.'
]
for i,s in enumerate(steps):para(LX,1972+i*54,s,size=29,leading=40)
para(LX,2215,'RK4 evaluates state trajectories; SLSQP computes local numerical responses under control bounds and instantaneous capacity constraints.',size=29,leading=41)

section(LX,2393,'03','Allocate resources across assets and time')
figure('fig3_actions_en',LX,2482,CW)
para(LX,2935,'At B = 1.2, capacity binds in intervals 2–4. All three capacities show reduced effort in the final interval.',size=29,leading=41)

section(RX,842,'04','Compare cumulative defense losses')
text(RX,933,'2.41%',100,True,TEAL)
text(RX+CW*.51,933,'14.79%',100,True,TEAL)
para(RX,1049,'Lower total loss than fixed-mean defense',CW*.46,29,39)
para(RX+CW*.51,1049,'Lower total loss than no defense',CW*.47,29,39)
para(RX,1175,'The dynamic and fixed-mean plans have equal cumulative isolation and recovery inputs for each asset. Their timing differs.',size=30,leading=43)
figure('fig4_states_en',RX,1340,CW)
para(RX,2010,'Compromised fractions under the shared attack plan. Dynamic defense protects the core database more strongly; some late-horizon state curves cross.',size=28,leading=39)

# Fully editable table. Values are copied from the manuscript, not recomputed.
ty=2167
col=[RX,RX+355,RX+603,RX+851]
line(RX,ty,RX+CW,ty,NAVY,2.5)
for x,s in zip(col,['Defense plan','Security loss','Total loss','Final state']):text(x+8,ty+20,s,27,True,NAVY)
line(RX,ty+72,RX+CW,ty+72)
rows=[('No defense','10.945701','10.945701','0.221271'),
      ('Fixed mean (M)','8.580319','9.556834','0.156868'),
      ('Dynamic (G)','8.176990','9.326647','0.157163')]
for i,row in enumerate(rows):
    yy=ty+95+i*67
    if i==2:rect(RX,yy-12,CW,62,'#EEF7F6')
    for x,s in zip(col,row):text(x+8,yy,s,27,i==2,TEAL if i==2 else TEXT)
line(RX,ty+303,RX+CW,ty+303,NAVY,2)
para(RX,ty+324,'Total loss includes security loss plus business and action costs. Final state is the value-weighted compromised fraction at T = 10.',size=26,leading=36,color=GRAY)

section(RX,2649,'05','Timing shapes the loss–state tradeoff')
para(RX,2737,'The dynamic plan reduces accumulated compromise and total defender loss. The fixed-mean plan has a slightly lower final weighted compromised fraction (0.156868 versus 0.157163).',size=30,leading=43)
para(RX,2935,'The computed controls are capacity-feasible at B = 0.6, 1.2 and 1.8. Uniform-start paths meet the numerical stopping criteria after five alternating updates.',size=29,leading=41)

line(M,3110,W-M,3110,LINE,3)
text(M,3137,'MODEL & EVIDENCE',24,True,TEAL)
para(M,3180,'Synthetic six-asset network. Complete-information, nonzero-sum open-loop game. Local numerical responses in a piecewise-constant strategy class.',W-2*M,27,37)
text(M,3228,'Selected background',21,True,GRAY)
text(M,3260,'[1] Başar & Olsder. Dynamic Noncooperative Game Theory. SIAM, 1999. doi:10.1137/1.9781611971132.',21,color=GRAY)
text(M,3292,'[2] Preciado et al. Optimal Resource Allocation for Network Protection Against Spreading Processes. IEEE TCNS, 2014. doi:10.1109/TCNS.2014.2310911.',21,color=GRAY)
c.showPage(); c.save()
doc=fitz.open(OUT/'layout.pdf'); page=doc[0]
for src,box in figures:
    source=fitz.open(src)
    page.show_pdf_page(fitz.Rect(box),source,0)
    source.close()
doc.subset_fonts(); doc.save(OUT/'Network_Defense_Poster_A0_EN.pdf',garbage=4,deflate=True)
pix=page.get_pixmap(matrix=fitz.Matrix(.68,.68),alpha=False)
pix.save(OUT/'Network_Defense_Poster_Preview.png')
doc.close()
E.ElementTree(svg).write(OUT/'Network_Defense_Poster_A0_EN.svg',encoding='utf-8',xml_declaration=True)
svg_text=(OUT/'Network_Defense_Poster_A0_EN.svg').read_text(encoding='utf-8')
svg_text=svg_text[svg_text.index('<svg'):]
(OUT/'poster_view.html').write_text('<!doctype html><html><head><meta charset="utf-8"><style>html,body{margin:0;background:white}svg{display:block;width:1100px;height:auto}</style></head><body>'+svg_text+'</body></html>',encoding='utf-8')
(OUT/'使用说明.txt').write_text('''会议海报初稿

规格：A0 竖版，841 × 1189 mm，英文。
内容依据：Network_Defense_Revised.docx；沿用论文的网络图、行动热图和状态曲线。

文件
Network_Defense_Poster_A0_EN.pdf：打印用矢量 PDF，正文和图表字体已嵌入。
Network_Defense_Poster_A0_EN.svg：可编辑源文件，使用 Inkscape 或 Adobe Illustrator 打开。
Network_Defense_Poster_Preview.png：预览图，不建议作为大幅打印源文件。

使用前请完成
1. 用真实作者顺序、单位、城市、国家和通讯邮箱替换顶部方括号内容。
2. 收到会议的海报通知后，核对指定尺寸、语言、会议标识及上传要求。
3. 打印选择实际大小（100%），不添加页眉页脚；版式尺寸以会议最终通知为准。

编辑说明
正文、标题、结果数字和表格在 SVG 内均为文本对象；图表由原论文的矢量图组成。
主字体为 Arial，图表沿用 Times New Roman。编辑电脑需安装相应字体。
PDF 中 2.41% 和 14.79% 对应主容量 B=1.2、与动态方案联合求得并固定用于三方案的共同攻击计划。
海报保留固定均值方案期末加权受损比例略低这一结果，不将局部数值响应表述为严格 Nash 均衡。
作者信息待补充，因此当前版本为可供审阅和完善的海报初稿。
''',encoding='utf-8-sig')
with zipfile.ZipFile(OUT/'Network_Defense_Poster_Editable.zip','w',zipfile.ZIP_DEFLATED) as z:
    for name in ['Network_Defense_Poster_A0_EN.svg','使用说明.txt']:
        z.write(OUT/name,name)
(OUT/'poster_content.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')
print('A0 poster exported; vector figures:',len(figures))
print('Layout:',W,H,'points')
