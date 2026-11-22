from pathlib import Path
from zipfile import ZipFile
from lxml import etree as E
from docx import Document
from pypdf import PdfReader
import json, re, collections, hashlib
ROOT=Path(__file__).resolve().parent
NS={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main','m':'http://schemas.openxmlformats.org/officeDocument/2006/math','a':'http://schemas.openxmlformats.org/drawingml/2006/main','wp':'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing','r':'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}
def parse_props(el):
    return {E.QName(c).localname:{E.QName(k).localname:v for k,v in c.attrib.items()} for c in el} if el is not None else {}
def merge(a,b):
    for k,v in b.items():a.setdefault(k,{}).update(v)
    return a
def chain(st):
    out=[]
    while st is not None:out.insert(0,st);st=st.base_style
    return out
doc=Document(next((ROOT/'input').glob('A Finite*.docx')))
with ZipFile(next((ROOT/'input').glob('A Finite*.docx'))) as z:
    st=E.fromstring(z.read('word/styles.xml'))
    defaults=parse_props(st.find('w:docDefaults/w:rPrDefault/w:rPr',NS))
    runs=[]
    for p in doc.element.xpath('.//w:p'):
        from docx.text.paragraph import Paragraph
        para=Paragraph(p,doc)
        for r in para.runs:
            if not r.text:continue
            rp=json.loads(json.dumps(defaults))
            for style in chain(para.style):merge(rp,parse_props(style.element.find('w:rPr',NS)))
            if r.style:
                for style in chain(r.style):merge(rp,parse_props(style.element.find('w:rPr',NS)))
            merge(rp,parse_props(r._r.find('w:rPr',NS)))
            runs.append({'text':r.text,'style':para.style.name,'effective':rp})
    summary={}
    for s in sorted(set(r['style'] for r in runs)):
        rs=[r for r in runs if r['style']==s]
        summary[s]=dict(collections.Counter(str((r['effective'].get('rFonts'),r['effective'].get('sz'),r['effective'].get('i'),r['effective'].get('smallCaps'))) for r in rs))
    rels=E.fromstring(z.read('word/_rels/document.xml.rels'))
    rid={q.get('Id'):q.get('Target') for q in rels}
    images=[]
    for drawing in doc.element.xpath('.//w:drawing'):
        ex=drawing.find('.//wp:extent',NS);b=drawing.find('.//a:blip',NS)
        images.append({'rid':b.get('{'+NS['r']+'}embed'),'target':rid.get(b.get('{'+NS['r']+'}embed')),'width_in':int(ex.get('cx'))/914400,'height_in':int(ex.get('cy'))/914400})
    (ROOT/'effective_fonts.json').write_text(json.dumps({'summary':summary,'runs':runs,'images':images},ensure_ascii=False,indent=2),encoding='utf-8')
    lines=[f'{k}: {v}' for k,v in summary.items()]+[str(images)]
    (ROOT/'effective_fonts_summary.txt').write_text('\n'.join(lines),encoding='utf-8')
    cjk=[r['text'] for r in runs if re.search('[\u4e00-\u9fff]',r['text'])]
    formulas=doc.element.xpath('.//m:oMath')
    (ROOT/'en_math.xml').write_text('\n'.join(E.tostring(q,encoding='unicode') for q in formulas),encoding='utf-8')
    print('font summary',summary)
    print('images',images,'CJK',cjk)
d=json.loads((ROOT/'en_audit.json').read_text(encoding='utf-8'))
refs=[q for q in d['paragraphs'] if re.match(r'^\[\d+\]',q['text'])]
cites=[]
for p in d['paragraphs']:
    if p['id']>=76:continue
    for r in p['runs']:
        for match in re.finditer(r'\[([0-9,–-]+)\]',r['text']):
            cites.append({'p':p['id'],'citation':match.group(),'superscript':r['props'].get('vertAlign',{}).get('val')=='superscript'})
numbers=[]
for c in cites:
    for x in c['citation'][1:-1].split(','):
        if re.search('[–-]',x):
            a,b=map(int,re.split('[–-]',x));numbers.extend(range(a,b+1))
        else:numbers.append(int(x))
numeric={
'table2_sums':[sum(float(d['tables'][15]['rows'][j][col]) for j in range(1,7)) for col in range(1,4)],
'mean_main_intervals':sum([.843705,1.2,1.2,1.2,1.065570,.337751])/6,
'JD_improvement_vs_N':(10.945701-9.326647)/10.945701*100,
'JD_improvement_vs_M':(9.556834-9.326647)/9.556834*100,
'Lsec_difference':8.580319-8.176990,
'cost_difference':1.149657-.976515,
'terminal_difference':.157163-.156868,
'sum_L_cost':[10.945701+0,8.580319+.976515,8.176990+1.149657],
'api_resource_shares':[.339102/.564365,.463738/.974504,.480837/1.081025],
'identity_resource_shares':[.012188/.564365,.076786/.974504,.101903/1.081025]}
data={'citations':cites,'cited_numbers':sorted(set(numbers)),'references':len(refs),'missing_cites':sorted(set(range(1,23))-set(numbers)),'non_superscript':[x for x in cites if not x['superscript']],'numerical_checks':numeric}
(ROOT/'checks.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
print('numeric',numeric)
print('citation check',len(cites),sorted(set(numbers)),data['non_superscript'])
for label in ['en','zh']:
    reader=PdfReader(ROOT/f'{label}.pdf')
    print(label,'pages',len(reader.pages))
    # PDF text and external metadata are evidence only; visual inspection remains necessary.
