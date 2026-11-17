from common import *
import os,subprocess
def main():
    skill=Path('C:/Users/Jin/.codex/plugins/cache/nature-skills/nature-skills/0.1.0/skills/nature-figure/scripts')
    env=os.environ.copy();env['PYTHONPATH']=str(ROOT/'paper/work_d2/analysis/_qa_packages')+os.pathsep+env.get('PYTHONPATH','');env['PYTHONDONTWRITEBYTECODE']='1'
    qa=OUT/'figures/qa';qa.mkdir(exist_ok=True);rows=[]
    checks=[('source',skill/'validate_figure.py',[str(OUT/'scripts/plot_results.py'),'--json'])]
    for name,script,args in checks:
        r=subprocess.run([sys.executable,'-B',str(script),*args],capture_output=True,text=True,env=env)
        (qa/f'{name}.json').write_text(r.stdout or r.stderr,encoding='utf-8');rows.append(dict(check=name,returncode=r.returncode))
    for p in sorted((OUT/'figures').glob('*.pdf')):
        for name,script,args in [('text','audit_pdf_text.py',['--min-pt','5','--json']),('collisions','audit_figure_collisions.py',['--json'])]:
            r=subprocess.run([sys.executable,'-B',str(skill/script),str(p),*args],capture_output=True,text=True,env=env)
            (qa/f'{p.stem}_{name}.json').write_text(r.stdout or r.stderr,encoding='utf-8');rows.append(dict(figure=p.name,check=name,returncode=r.returncode))
    dump(qa/'summary.json',rows);print(json.dumps(rows),flush=True)
if __name__=='__main__':main()
