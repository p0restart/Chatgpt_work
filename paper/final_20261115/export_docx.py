"""Export audited Markdown to Word using native OMML mathematics."""
from pathlib import Path
import sys,re,copy,json
BASE=Path(__file__).resolve().parent
sys.path.insert(0,str(BASE/'vendor'))
from latex2mathml.converter import convert
from lxml import etree
from docx import Document
from docx.shared import Inches,Pt,RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.enum.table import WD_TABLE_ALIGNMENT,WD_CELL_VERTICAL_ALIGNMENT

source=(BASE/'论文终稿_中文.md').read_text(encoding='utf-8')
transform=etree.XSLT(etree.parse('C:/Program Files/Microsoft Office/root/Office16/MML2OMML.XSL'))
doc=Document();sec=doc.sections[0]
sec.page_width=Inches(8.5);sec.page_height=Inches(11)
sec.top_margin=Inches(.75);sec.bottom_margin=Inches(.75);sec.left_margin=Inches(.80);sec.right_margin=Inches(.80)
sec.header_distance=Inches(.30);sec.footer_distance=Inches(.30)
for name in ['Normal','Title','Heading 1','Heading 2','Heading 3','Caption']:
    st=doc.styles[name];st.font.name='Times New Roman';st.font.color.rgb=RGBColor(0,0,0)
    st._element.get_or_add_rPr().get_or_add_rFonts().set(qn('w:eastAsia'),'宋体')
    for border in st._element.findall('.//'+qn('w:pBdr')):border.getparent().remove(border)
normal=doc.styles['Normal'];normal.font.size=Pt(11)
normal.paragraph_format.line_spacing=1.12;normal.paragraph_format.space_after=Pt(4)
for name,size in [('Title',18),('Heading 1',15),('Heading 2',12),('Heading 3',11)]:
    st=doc.styles[name];st.font.size=Pt(size);st.font.bold=True
    st.paragraph_format.space_before=Pt(10);st.paragraph_format.space_after=Pt(5)
    st.paragraph_format.keep_with_next=True
    st._element.get_or_add_rPr().get_or_add_rFonts().set(qn('w:eastAsia'),'黑体')
doc.styles['Caption'].font.size=Pt(9)
doc.styles['Caption'].paragraph_format.space_after=Pt(5)
math_count=0;failures=[]
def math(par,tex,display=False):
    global math_count
    tex=tex.strip()
    tex=re.sub(r'\\tag\{\d+\}','',tex)
    tex=tex.replace(r'\begin{aligned}',r'\begin{array}{l}').replace(r'\end{aligned}',r'\end{array}').replace('&','')
    tex=tex.replace(r'\arg',r'\operatorname{arg}')
    try:
        xml=convert(tex,display='block' if display else 'inline')
        result=transform(etree.fromstring(xml.encode('utf-8')))
        el=result.getroot()
        if el is None:raise ValueError('Empty OMML')
        # Use a run-level equation in a Word paragraph, including display equations.
        if el.tag==qn('m:oMathPara'):
            node=el.find(qn('m:oMath'));el=node if node is not None else el
        for node in el.iter(qn('m:r')):
            prop=node.find(qn('w:rPr'))
            if prop is None:prop=etree.SubElement(node,qn('w:rPr'))
            fonts=etree.SubElement(prop,qn('w:rFonts'));fonts.set(qn('w:ascii'),'Cambria Math');fonts.set(qn('w:hAnsi'),'Cambria Math')
            size=etree.SubElement(prop,qn('w:sz'));size.set(qn('w:val'),'20' if display else '22')
        par._p.append(copy.deepcopy(el));math_count+=1
    except Exception as e:
        failures.append(dict(tex=tex,error=str(e)));raise

def rich(par,text):
    for token in re.split(r'(\$[^$]+\$|\*\*.*?\*\*|\[[^\]]+\]\([^)]*\))',text):
        if not token:continue
        if token.startswith('$') and token.endswith('$'):math(par,token[1:-1])
        elif token.startswith('**'):
            richbold=token[2:-2]
            # Render math in bold leads faithfully without leaving source markers.
            if '$' in richbold:rich(par,richbold)
            else:par.add_run(richbold).bold=True
        elif re.match(r'\[[^\]]+\]\(',token):par.add_run(re.match(r'\[([^\]]+)\]',token).group(1))
        else:par.add_run(token)

lines=source.splitlines();i=0;images=0;tables=0
while i<len(lines):
    line=lines[i].strip()
    if not line:i+=1;continue
    if line.startswith('$$'):
        buf=line[2:];i+=1
        while '$$' not in buf:
            buf+='\n'+lines[i];i+=1
        tex=buf.split('$$')[0];n=re.search(r'\\tag\{(\d+)\}',tex)
        p=doc.add_paragraph();p.alignment=WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before=Pt(5);p.paragraph_format.space_after=Pt(7)
        math(p,tex,True)
        if n:p.add_run('  （'+n.group(1)+'）')
        continue
    if line.startswith('!['):
        match=re.match(r'!\[([^\]]*)\]\(([^)]+)\)',line);p=doc.add_paragraph();p.alignment=WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.keep_with_next=True
        p.add_run().add_picture(str(BASE/match.group(2)),width=Inches(6.85))
        images+=1;i+=1;continue
    if line.startswith('|'):
        rows=[]
        while i<len(lines) and lines[i].strip().startswith('|'):
            cells=[x.strip() for x in lines[i].strip().strip('|').split('|')]
            if not all(re.fullmatch(r':?-+:?',c) for c in cells):rows.append(cells)
            i+=1
        t=doc.add_table(rows=0,cols=len(rows[0]));t.alignment=WD_TABLE_ALIGNMENT.CENTER;t.autofit=False
        width=6.85/len(rows[0])
        if len(rows[0])==2:widths=[1.65,5.20]
        elif len(rows[0])==7:widths=[.5,.5,1.1,1.1,1.1,1.25,1.30]
        elif len(rows[0])==6:widths=[.7,1.6,1.1,1.1,1.1,1.25]
        elif len(rows[0])==5:widths=[1.35,1.0,1.5,1.5,1.5]
        else:widths=[width]*len(rows[0])
        for c,w in zip(t.columns,widths):c.width=Inches(w)
        for k,row in enumerate(rows):
            cells=t.add_row().cells
            for j,(cell,txt) in enumerate(zip(cells,row)):
                cell.width=Inches(widths[j]);cell.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
                p=cell.paragraphs[0];p.paragraph_format.space_after=Pt(2);p.paragraph_format.space_before=Pt(2);p.paragraph_format.line_spacing=1.05
                p.alignment=WD_ALIGN_PARAGRAPH.LEFT if len(rows[0])==2 else WD_ALIGN_PARAGRAPH.CENTER
                rich(p,txt)
                for run in p.runs:run.font.size=Pt(9);run.bold=k==0
                tcPr=cell._tc.get_or_add_tcPr()
                borders=OxmlElement('w:tcBorders')
                for side in ['top','left','bottom','right']:
                    e=OxmlElement('w:'+side);e.set(qn('w:val'),'single');e.set(qn('w:sz'),'4');e.set(qn('w:color'),'D9D9D9');borders.append(e)
                tcPr.append(borders)
                if k==0:
                    shade=OxmlElement('w:shd');shade.set(qn('w:fill'),'EAEAEA');tcPr.append(shade)
            trPr=t.rows[-1]._tr.get_or_add_trPr();nosplit=OxmlElement('w:cantSplit');trPr.append(nosplit)
            if len(rows)<=5:
                for cell in cells:
                    for para in cell.paragraphs:para.paragraph_format.keep_with_next=k<len(rows)-1
            if k==0:
                repeat=OxmlElement('w:tblHeader');trPr.append(repeat)
        tables+=1;doc.add_paragraph().paragraph_format.space_after=Pt(1);continue
    heading=re.match(r'^(#{1,4})\s+(.*)',line)
    if heading:
        level=len(heading.group(1));text=heading.group(2)
        if i==0:p=doc.add_paragraph(text,style='Title');p.alignment=WD_ALIGN_PARAGRAPH.CENTER
        else:
            style='Heading '+str(max(1,level-1)) if level>1 else 'Heading 1'
            p=doc.add_paragraph(text,style=style)
        i+=1;continue
    if line.startswith('**图') or line.startswith('**附图'):
        p=doc.add_paragraph(style='Caption');rich(p,line);i+=1;continue
    if line.startswith('**表'):
        p=doc.add_paragraph();p.paragraph_format.keep_with_next=True;p.alignment=WD_ALIGN_PARAGRAPH.CENTER;rich(p,line);i+=1;continue
    if line.startswith('- '):
        p=doc.add_paragraph(style='List Bullet');rich(p,line[2:]);i+=1;continue
    text=line;i+=1
    while i<len(lines) and lines[i].strip() and not re.match(r'^(#|\$\$|!\[|\||- )',lines[i].strip()):
        text+=' '+lines[i].strip();i+=1
    p=doc.add_paragraph();rich(p,text)
    if re.match(r'^\[\d+\]',text):
        p.paragraph_format.line_spacing=1.0
        for run in p.runs:run.font.size=Pt(9.5)

footer=sec.footer.paragraphs[0];footer.alignment=WD_ALIGN_PARAGRAPH.CENTER
field=OxmlElement('w:fldSimple');field.set(qn('w:instr'),'PAGE');footer._p.append(field)
doc.core_properties.title='基于非零和微分博弈的有限资源网络防御决策方法'
doc.core_properties.subject='中文五章合稿'
doc.core_properties.author=''
# The bundled default document can carry a decorative title rule directly.
for border in doc._element.findall('.//'+qn('w:pBdr')):border.getparent().remove(border)
for border in doc.styles.element.findall('.//'+qn('w:pBdr')):border.getparent().remove(border)
path=BASE/'论文终稿_中文.docx';doc.save(path)
(BASE/'document_export.json').write_text(json.dumps(dict(math_equations=math_count,images=images,tables=tables,failures=failures,math_format='native OMML',page='Letter portrait, single column; conference template not specified'),indent=2),encoding='utf-8')
print(path,math_count,images,tables)
