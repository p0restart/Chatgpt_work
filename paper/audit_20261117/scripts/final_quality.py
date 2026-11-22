from pathlib import Path
import json,sys,subprocess,hashlib,zipfile,re
sys.path.append(r'C:\Users\Jin\AppData\Local\Temp\codex_audit_20261117_deps')
import pymupdf
from lxml import etree
BASE=Path(__file__).resolve().parents[1]
FIGSKILL=Path(r'C:\Users\Jin\.codex\plugins\cache\nature-skills\nature-skills\0.1.0\skills\nature-figure\scripts')
checks={}
for row in json.loads((BASE/'raw_static/source_manifest.json').read_text(encoding='utf-8'))['files']:
    checks[row['local']]=hashlib.sha256((BASE/row['local']).read_bytes()).hexdigest()==row['sha256']
for row in json.loads((BASE/'input/sensitivity_package/manifest.json').read_text(encoding='utf-8')):
    p=BASE/row['local']
    if p.name.startswith(tuple(f'item_{i:02d}' for i in range(1,7))):
        checks[row['local']]=hashlib.sha256(p.read_bytes()).hexdigest()==row['sha256']
checks['original_MD_unchanged']=hashlib.sha256(Path(r'C:\Users\Jin\Downloads\网络防御决策论文_单栏中文_模型定义与文献修订稿.md').read_bytes()).hexdigest()=='858db2de26af001a3ec13bf35e821ed62720c858e4d6efc86cf59ddf2890aa98'
checks['original_DOCX_unchanged']=hashlib.sha256(Path(r'C:\Users\Jin\Downloads\网络防御决策论文_单栏中文_模型定义与文献修订稿.docx').read_bytes()).hexdigest()=='741407b33682812f96abfa31a45c01a12d4ff5b84536027bdc9f367316905c43'
with zipfile.ZipFile(BASE/'多资产网络防御决策论文_审计修订稿.docx') as z:
    root=etree.fromstring(z.read('word/document.xml'))
ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main','m':'http://schemas.openxmlformats.org/officeDocument/2006/math'}
regular=''.join(root.xpath('//w:t/text()',namespaces=ns))
mathtxt=''.join(root.xpath('//m:t/text()',namespaces=ns))
checks['no_raw_latex']=not('$' in regular or '\\' in regular)
checks['calligraphic_sets_preserved']='𝒜' in mathtxt and '𝒢' in mathtxt
checks['three_images']=len(root.xpath('//w:drawing',namespaces=ns))==3
checks['six_tables']=len(root.xpath('//w:tbl',namespaces=ns))==6
checks['eighteen_equations']=len(re.findall(r'\{#eq-\d+\}',(BASE/'qa/paper_export.md').read_text(encoding='utf-8')))==18
for name in ['capacity_three_budgets','actions_three_budgets']:
    for ext in ['png','pdf','svg']:checks[f'{name}.{ext}']=(BASE/'figures'/f'{name}.{ext}').stat().st_size>1000
    pdf=BASE/'figures'/f'{name}.pdf'
    with pymupdf.open(pdf) as d:checks[f'{name}_170mm']=abs(d[0].rect.width/72*25.4-170)<.01
    for script,args in [('audit_figure_collisions.py',['--json-out',str(BASE/'qa'/f'{name}_collision.json')]),('audit_pdf_text.py',['--min-pt','8','--json'])]:
        r=subprocess.run([sys.executable,str(FIGSKILL/script),str(pdf),*args],capture_output=True,text=True,encoding='utf-8',errors='replace')
        checks[f'{name}_{script}']=r.returncode==0
        (BASE/'qa'/f'{name}_{script}.log').write_text(r.stdout+'\n'+r.stderr,encoding='utf-8')
r=subprocess.run([sys.executable,str(FIGSKILL/'validate_figure.py'),str(BASE/'scripts/make_figures.py')],capture_output=True,text=True,encoding='utf-8',errors='replace')
(BASE/'qa/figure_source_preflight.log').write_text(r.stdout+'\n'+r.stderr,encoding='utf-8')
checks['figure_source_no_failure']=r.returncode==0
checks['86_numeric_checks']=json.loads((BASE/'data/audit_summary.json').read_text())['passed']
(BASE/'qa/final_quality.json').write_text(json.dumps({'checks':checks,'passed':all(checks.values())},ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'count':len(checks),'failed':[k for k,v in checks.items() if not v]},ensure_ascii=False))
if not all(checks.values()):raise SystemExit(1)
