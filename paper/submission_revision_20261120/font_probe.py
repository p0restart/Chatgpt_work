from pathlib import Path
from copy import deepcopy
from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt
R=Path(__file__).resolve().parent
source=Document(R.parents[1]/'reports/conference_word_audit_20261120/input/A Finite-Resource Network Defense Decision Method Based on a Nonzero-Sum Differential Game.docx')
d=Document()
d.styles['Normal'].font.name='Times New Roman';d.styles['Normal'].font.size=Pt(10)
for table in [source.tables[1],source.tables[2],source.tables[3],source.tables[5],source.tables[8]]:
 d.element.body.insert(-1,deepcopy(table._tbl))
mp=d.settings.element.find(qn('m:mathPr'))
if mp is None:mp=OxmlElement('m:mathPr');d.settings.element.append(mp)
mf=mp.find(qn('m:mathFont'))
if mf is None:mf=OxmlElement('m:mathFont');mp.insert(0,mf)
mf.set(qn('m:val'),'Times New Roman')
for el in d.element.xpath('.//m:r'):
 rp=el.find(qn('w:rPr'))
 if rp is None:rp=OxmlElement('w:rPr');el.insert(0,rp)
 fonts=rp.find(qn('w:rFonts'))
 if fonts is None:fonts=OxmlElement('w:rFonts');rp.insert(0,fonts)
 for key in ['ascii','hAnsi','cs']:fonts.set(qn('w:'+key),'Times New Roman')
for fonts in d.element.xpath('.//w:rFonts'):
 for key in ['ascii','hAnsi','cs']:fonts.set(qn('w:'+key),'Times New Roman')
d.save(R/'qa/font_probe.docx')
print('saved font probe')
