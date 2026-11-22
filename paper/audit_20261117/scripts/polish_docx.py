from pathlib import Path
import sys,json
from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt

path=Path(sys.argv[1]).resolve()
doc=Document(path)
# Keep the 15-line algorithm on one page, with its caption and input/output.
for t in doc.tables:
    if len(t.rows)==16 and t.cell(0,0).text.strip()=='行':
        for i,row in enumerate(t.rows):
            trpr=row._tr.get_or_add_trPr()
            node=OxmlElement('w:cantSplit');trpr.append(node)
            for ci,c in enumerate(row.cells):
                for p in c.paragraphs:
                    p.paragraph_format.keep_with_next=(i<len(t.rows)-1)
                    p.paragraph_format.space_after=Pt(2)
                    p.paragraph_format.space_before=Pt(2)
                    level=1 if i in (3,4,10) else (2 if i in (5,6,7,8,9) else 0)
                    if ci==1:
                        p.paragraph_format.left_indent=Pt(level*9)
        prev=t._tbl.getprevious()
        for _ in range(3):
            if prev is not None and prev.tag==qn('w:p'):
                pr=prev.get_or_add_pPr()
                node=OxmlElement('w:keepNext');pr.append(node)
                prev=prev.getprevious()
    elif len(t.rows)<=12:
        for i,row in enumerate(t.rows):
            for c in row.cells:
                for p in c.paragraphs:
                    p.paragraph_format.keep_with_next=(i<len(t.rows)-1)
        prev=t._tbl.getprevious()
        if prev is not None and prev.tag==qn('w:p'):
            node=OxmlElement('w:keepNext');prev.get_or_add_pPr().append(node)
regular=''.join(doc.element.xpath('//w:t/text()'))
bad=[p.text for p in doc.paragraphs if '$' in p.text or '\\' in p.text]
if bad:raise ValueError('Unconverted math in regular text: '+repr(bad[:3]))
doc.save(path)
print(json.dumps({'docx':path.name,'unconverted_math':len(bad),'math_objects':len(doc.element.xpath('//m:oMath')),'tables':len(doc.tables),'images':len(doc.inline_shapes)},ensure_ascii=False))
