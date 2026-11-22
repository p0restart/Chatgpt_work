from pathlib import Path
import json,hashlib,zipfile,sys
import numpy as np
BASE=Path(__file__).resolve().parents[1]
checks={}
for B in (.6,1.2,1.8):
    folder=BASE/'raw_static'/f'B{B}'
    m=json.loads((folder/'model.json').read_text(encoding='utf-8-sig'))
    attacks=json.loads((folder/'cross_attacks.json').read_text(encoding='utf-8-sig'))
    for name,a in attacks.items():
        if name not in ('a0','aG','aBR_F'):continue
        a=np.asarray(a)
        checks[f'B{B}/{name}/attack_capacity']=bool(np.max(a@np.asarray(m['d_a']))<=m['A']+1e-10)
        checks[f'B{B}/{name}/attack_bounds']=bool(a.min()>=-1e-10 and a.max()<=1+1e-10)
assert all(checks.values())
(BASE/'qa/attack_capacity_check.json').write_text(json.dumps(checks,indent=2),encoding='utf-8')
visual={
    'date':'2026-11-17',
    'renderer':'Native Microsoft Word COM, read-only PDF export',
    'paper_pages':9,'report_pages':4,
    'every_final_page_inspected':True,
    'paper_checks':['native equations and script set glyphs','15-line indented algorithm on one page','3 figures readable','all 5 data tables intact','17 references in order','no text outside page'],
    'report_checks':['scientific notation not spanning body text','tables and links readable','no text outside page'],
    'figure_preflight_notes':['Static width warning misreads 17/2.54 as inches; PDF width verified as 170 mm.','No TIFF provided: PNG at 600 dpi plus PDF/SVG are supplied; no venue requested TIFF.'],
    'fixed_model_unchanged':True,
    'new_optimization':False,
    'documents':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in BASE.glob('*.docx')}
}
(BASE/'qa/visual_review.json').write_text(json.dumps(visual,ensure_ascii=False,indent=2),encoding='utf-8')
files=[]
for pattern in ['*.docx','*.md','references.bib']:
    files+=list(BASE.glob(pattern))
for folder in ['data','figures','raw_static','reviews','supplement']:
    files+=[p for p in (BASE/folder).rglob('*') if p.is_file()]
for name in ['data_audit.py','make_figures.py','audit_panel_alignment.py','prepare_export.py','polish_docx.py','build_audit_report.py','render_word.ps1','pdf_qa.py']:
    files.append(BASE/'scripts'/name)
for name in ['original.md','original.docx','rId31.png','review_packet.md','review_packet_supplement.md']:
    files.append(BASE/'input'/name)
for pattern in ['item_01.*','item_02.*','item_03.*','item_04.*','item_05.*','item_06.*','manifest.json']:
    files+=list((BASE/'input/sensitivity_package').glob(pattern))
for pattern in ['*.json','*.log','format.txt','paper_export.md','report_export.md','figure_contract.md']:
    files+=list((BASE/'qa').glob(pattern))
files=sorted(set(files))
manifest=[{'path':p.relative_to(BASE).as_posix(),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in files]
(BASE/'MANIFEST.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
dest=BASE/'论文审计修订交付包_20261117.zip'
with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for p in files+[BASE/'MANIFEST.json']:z.write(p,p.relative_to(BASE).as_posix())
with zipfile.ZipFile(dest) as z:
    assert z.testzip() is None
    for row in manifest:assert hashlib.sha256(z.read(row['path'])).hexdigest()==row['sha256']
print(json.dumps({'package':str(dest),'files':len(manifest)+1,'bytes':dest.stat().st_size,'hash_verification':'PASS','attack_checks':len(checks)},ensure_ascii=True))
