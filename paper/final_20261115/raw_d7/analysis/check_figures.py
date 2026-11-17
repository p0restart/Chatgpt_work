from pathlib import Path
import subprocess,sys,json,os
BASE=Path(__file__).resolve().parents[1];qa=BASE/'analysis/figure_qa';reports=[]
env=os.environ.copy()
bundled=BASE.parents[1]/'paper/work_d2/analysis/_qa_packages'
if bundled.exists():env['PYTHONPATH']=str(bundled)+os.pathsep+env.get('PYTHONPATH','')
for p in sorted((BASE/'figures').glob('*.pdf')):
    for name,script,args in [('text','audit_pdf_text.py',['--min-pt','7','--json']),('collisions','audit_figure_collisions.py',['--json'])]:
        r=subprocess.run([sys.executable,str(qa/script),str(p),*args],capture_output=True,text=True,env=env)
        out=BASE/'figures/qa'/f'{p.stem}_{name}.json';out.write_text(r.stdout or r.stderr,encoding='utf-8')
        reports.append(dict(figure=p.name,check=name,returncode=r.returncode,report=str(out.relative_to(BASE))))
(BASE/'figures/qa/summary.json').write_text(json.dumps(reports,indent=2),encoding='utf-8');print(json.dumps(reports))
