"""Run source, PDF text and geometry checks on the four actual exported figures."""
from pathlib import Path
import json
import os
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[4]
OUT=ROOT/'paper/work_d4/P0_01_fixed_attack'
SKILL=Path('C:/Users/Jin/.codex/plugins/cache/nature-skills/nature-skills/0.1.0/skills/nature-figure/scripts')

def main():
    records=[]
    source=subprocess.run([sys.executable,str(SKILL/'validate_figure.py'),str(OUT/'analysis/plot_fixed.py'),'--json'],
                          capture_output=True,text=True,encoding='utf-8')
    (OUT/'analysis/figure_source_qa.json').write_text(source.stdout,encoding='utf-8')
    records.append(dict(check='source',returncode=source.returncode))
    names=['figure_interaction_comparison']+[f'figure_temporal_seed11_B{b}' for b in (.6,1.2,1.8)]
    env=os.environ.copy();env['PYTHONDONTWRITEBYTECODE']='1'
    # Reuse only the already available PDF-audit dependencies in isolated children.
    env['PYTHONPATH']=str(ROOT/'paper/work_d2/analysis/_qa_packages')
    for name in names:
        path=OUT/f'{name}.pdf'
        text=subprocess.run([sys.executable,str(SKILL/'audit_pdf_text.py'),str(path),'--min-pt','5','--json'],
                             capture_output=True,text=True,encoding='utf-8')
        (OUT/f'{name}.font_qa.json').write_text(text.stdout,encoding='utf-8')
        collision=subprocess.run([sys.executable,str(SKILL/'audit_figure_collisions.py'),str(path),
                 '--json-out',str(OUT/f'{name}.collision.json'),
                 '--overlay-pdf',str(OUT/f'{name}.collision_overlay.pdf')],
                 capture_output=True,text=True,encoding='utf-8',env=env)
        (OUT/f'{name}.collision_log.txt').write_text(collision.stdout+'\n'+collision.stderr,encoding='utf-8')
        records.append(dict(figure=name,font_returncode=text.returncode,collision_returncode=collision.returncode))
    (OUT/'analysis/figure_qa_summary.json').write_text(json.dumps(records,indent=2),encoding='utf-8')
    print(json.dumps(records))
    if source.returncode or any(r.get('font_returncode',0) or r.get('collision_returncode',0) for r in records):
        raise SystemExit(1)

if __name__=='__main__':main()
