from pathlib import Path
import zipfile, json, hashlib, io, collections
from lxml import etree as E
from docx import Document

ROOT=Path(__file__).resolve().parent
NS={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main','m':'http://schemas.openxmlformats.org/officeDocument/2006/math','a':'http://schemas.openxmlformats.org/drawingml/2006/main','wp':'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing'}
W='{'+NS['w']+'}'
SOURCES={'en':Path(r'C:\Users\Jin\Desktop\投稿版\A Finite-Resource Network Defense Decision Method Based on a Nonzero-Sum Differential Game.docx'),'zh':Path(r'C:\Users\Jin\Desktop\投稿版\1119-final-基于非零和微分博弈的有限资源网络防御决策方法.docx')}
for label,path in list(SOURCES.items()):
    copy=ROOT/'input'/path.name
    copy.parent.mkdir(parents=True,exist_ok=True)
    if not copy.exists():copy.write_bytes(path.read_bytes())
    SOURCES[label]=copy
with zipfile.ZipFile(r'C:\Users\Jin\Downloads\85af8c1144191aabd9596aa7081d7a27.zip') as z:
    for n in z.namelist():
        if n.endswith(('.docx','.pdf','.tex')) and '~$' not in n:
            dest=ROOT/'template'/Path(n).name
            dest.parent.mkdir(parents=True,exist_ok=True)
            if not dest.exists():dest.write_bytes(z.read(n))
SOURCES['template']=ROOT/'template'/'Conference-template-letter.docx'

def rawtext(el):
    return ''.join(E.XPath('.//w:t/text() | .//m:t/text()',namespaces=NS)(el))

def props(el):
    if el is None:return {}
    return {E.QName(c).localname: {E.QName(k).localname:v for k,v in c.attrib.items()} for c in el}

def mergeprops(a,b):
    for k,v in b.items():a.setdefault(k,{}).update(v)
    return a

def stylechain(st):
    a=[]
    while st is not None:
        a.insert(0,st)
        st=st.base_style
    return a

for label,path in SOURCES.items():
    sourcebytes=path.read_bytes()
    if label=='template':
        buf=io.BytesIO()
        replacements={b'http://purl.oclc.org/ooxml/wordprocessingml/main':NS['w'].encode(),b'http://purl.oclc.org/ooxml/officeDocument/math':NS['m'].encode(),b'http://purl.oclc.org/ooxml/officeDocument/relationships':b'http://schemas.openxmlformats.org/officeDocument/2006/relationships',b'http://purl.oclc.org/ooxml/drawingml/main':NS['a'].encode(),b'http://purl.oclc.org/ooxml/drawingml/wordprocessingDrawing':NS['wp'].encode()}
        with zipfile.ZipFile(io.BytesIO(sourcebytes)) as zin, zipfile.ZipFile(buf,'w') as zout:
            for n in zin.namelist():
                b=zin.read(n)
                if n.endswith(('.xml','.rels')):
                    for a,c in replacements.items():b=b.replace(a,c)
                zout.writestr(n,b)
        sourcebytes=buf.getvalue()
    doc=Document(io.BytesIO(sourcebytes))
    with zipfile.ZipFile(io.BytesIO(sourcebytes)) as z:
        xml=E.fromstring(z.read('word/document.xml'))
        settings=E.fromstring(z.read('word/settings.xml'))
        styles=E.fromstring(z.read('word/styles.xml'))
        defaults=styles.find('w:docDefaults',NS)
        records=[]
        for i,p in enumerate(doc.paragraphs,1):
            pp={}
            rp={}
            for st in stylechain(p.style):
                mergeprops(pp,props(st.element.find('w:pPr',NS)))
                mergeprops(rp,props(st.element.find('w:rPr',NS)))
            mergeprops(pp,props(p._p.find('w:pPr',NS)))
            runs=[]
            for r in p.runs:
                rr=json.loads(json.dumps(rp))
                if r.style:
                    for st in stylechain(r.style):mergeprops(rr,props(st.element.find('w:rPr',NS)))
                mergeprops(rr,props(r._r.find('w:rPr',NS)))
                if r.text:runs.append({'text':r.text,'props':rr})
            records.append({'id':i,'text':rawtext(p._p),'style':p.style.name,'props':pp,'runs':runs,'math':p._p.xpath('.//m:oMath') and [rawtext(q) for q in p._p.xpath('.//m:oMath')], 'images':len(p._p.xpath('.//w:drawing'))})
        tables=[]
        for i,t in enumerate(doc.tables,1):
            tables.append({'id':i,'rows':[[rawtext(c._tc) for c in row.cells] for row in t.rows],'xml':E.tostring(t._tbl,encoding='unicode')})
        sections=[]
        for s in doc.sections:
            sections.append({'width_in':s.page_width/914400,'height_in':s.page_height/914400,'top_in':s.top_margin/914400,'bottom_in':s.bottom_margin/914400,'left_in':s.left_margin/914400,'right_in':s.right_margin/914400,'xml':E.tostring(s._sectPr,encoding='unicode')})
        media=[]
        from PIL import Image
        for n in z.namelist():
            if n.startswith('word/media/'):
                item={'name':n,'bytes':len(z.read(n))}
                out=ROOT/'media'/label/Path(n).name;out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(z.read(n))
                try:
                    im=Image.open(io.BytesIO(z.read(n)));item.update({'size':im.size,'format':im.format})
                except Exception:pass
                media.append(item)
        data={'source':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'sections':sections,'defaults':E.tostring(defaults,encoding='unicode') if defaults is not None else None,'paragraphs':records,'tables':tables,'media':media,'math_count':len(xml.xpath('//m:oMath',namespaces=NS)),'embedded_objects':len(xml.xpath('//*[local-name()="OLEObject"]')),'comments':[n for n in z.namelist() if 'comment' in n.lower()],'insertions':len(xml.xpath('//w:ins',namespaces=NS)),'deletions':len(xml.xpath('//w:del',namespaces=NS)),'settings':E.tostring(settings,encoding='unicode')}
        (ROOT/f'{label}_audit.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
        lines=[]
        for i,el in enumerate(doc.element.body):
            if E.QName(el).localname=='p':
                pidx=next((r['id'] for r,p in zip(records,doc.paragraphs) if p._p is el),0)
                lines.append(f'P{pidx:03d} {rawtext(el)}')
            elif E.QName(el).localname=='tbl':
                lines.append('TABLE\n'+'\n'.join(' | '.join(rawtext(c) for c in row.findall('w:tc',NS)) for row in el.findall('w:tr',NS)))
        (ROOT/f'{label}_text.txt').write_text('\n\n'.join(lines),encoding='utf-8')
        print(label,'paragraphs',len(records),'tables',len(tables),'math',data['math_count'],'media',len(media),'sections',len(sections))
