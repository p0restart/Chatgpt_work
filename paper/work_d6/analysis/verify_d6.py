"""Read-only source checks and arithmetic checks; no optimization or integration."""
from pathlib import Path
import csv, hashlib, json, re
from collections import defaultdict

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / 'paper/work_d6'
checks, failures = [], []
def check(name, ok):
    checks.append(name)
    if not ok: failures.append(name)
def close(name, a, b, tol=1e-9): check(name, abs(float(a)-float(b)) <= tol)
def rows(name):
    with (OUT/'figures/data'/name).open(encoding='utf-8-sig', newline='') as f: return list(csv.DictReader(f))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
paper = (OUT/'paper_v1_zh.md').read_text(encoding='utf-8')
d3 = (ROOT/'paper/work_d3/manuscript_zh.md').read_text(encoding='utf-8')
for f in ['paper_v1_zh.md','claim_evidence_map.md','references_check.md','revision_notes.md','review_checklist.md','math_check.md','figures/README.md']:
    check('deliverable:'+f, (OUT/f).is_file())
check('five_chapters', re.findall(r'^# ([1-5]) ',paper,re.M)==list('12345'))
def equations(s): return [x for x in re.findall(r'\\\[(.*?)\\\]',s,re.S) if r'\tag{' in x]
eq_same = equations(paper)==equations(d3) and len(equations(paper))==20
check('20_equations_identical_to_D3',eq_same)
check('eight_main_images',len(re.findall(r'^!\[',paper,re.M))==8)
check('nine_tables',re.findall(r'^\*\*表(\d+)',paper,re.M)==[str(i) for i in range(1,10)])
for target in re.findall(r'\]\(([^)]+)\)',paper):
    if not target.startswith(('https:','http:','#')): check('link:'+target,(OUT/target).exists())
manifest=json.loads((OUT/'analysis/input_manifest.json').read_text(encoding='utf-8'))
for p,h in manifest.items(): check('source_unchanged:'+p,sha(ROOT/p)==h)
copies=json.loads((OUT/'figures/source_manifest.json').read_text(encoding='utf-8'))
for r in copies:
    check('copy:'+r['destination'],sha(ROOT/r['source'])==sha(OUT/r['destination'])==r['sha256'])
for r in rows('matched_four_cells.csv'):
    close('matched interaction '+r['seed']+r['B'],float(r['J_D'])-float(r['J_C'])-float(r['J_B'])+float(r['J_A']),r['interaction'])
for r in rows('d4_four_cell_comparison.csv'):
    for prefix,field in [('GAME','I_game'),('FIXED','I_fixed')]:
        close(prefix+' interaction '+r['seed']+r['B'],float(r[prefix+'_J_D'])-float(r[prefix+'_J_C'])-float(r[prefix+'_J_B'])+float(r[prefix+'_J_A']),r[field])
    close('D4 ratio '+r['seed']+r['B'],float(r['I_fixed'])/float(r['I_game']),r['fixed_over_game'])
for r in rows('baseline_pairs.csv'):
    diff=float(r['baseline_cost'])-float(r['joint'])
    close('baseline difference '+str(r),diff,r['absolute_difference'])
    close('baseline percent '+str(r),100*diff/float(r['baseline_cost']),r['reduction_percent'])
pay=rows('p0_payoff_matrix.csv')
lookup={(r['case'],r['defense'],r['attack']):r for r in pay}
check('54_p0_payoffs',len(pay)==54)
for r in rows('p0_case_summary.csv'):
    c=r['case']
    for label,ag,af in [('own_response','aG','aF'),('common','a0','a0')]:
        g=float(lookup[c,'G',ag]['J_D']); f=float(lookup[c,'F',af]['J_D'])
        close(c+label+' gain',f-g,r[label+'_D_advantage'])
        close(c+label+' percent',100*(f-g)/f,r[label+'_D_advantage_percent'])
    check(c+' own/fixed signs',float(r['own_response_D_advantage'])>0 and float(r['common_D_advantage'])<0)
    for defense,own,other in [('G','aG','aF'),('F','aF','aG')]:
        close(c+defense+' attacker',float(lookup[c,defense,own]['J_A'])-float(lookup[c,defense,other]['J_A']),r['attacker_gain_'+defense+'_own_vs_cross'])
obj=rows('replanning_objectives.csv')
ol={(r['B'],r['evaluation'],r['method'],r['H'],r['period']):r for r in obj}
for r in obj:
    close('defense components '+str(tuple(r.values())[:5]),sum(float(r[k]) for k in ['security','business','isolation','recovery','terminal_defense']),r['J_D'])
    close('attack components '+str(tuple(r.values())[:5]),float(r['attacker_value'])-float(r['attacker_effort'])+float(r['terminal_attacker']),r['J_A'])
comp=rows('replanning_comparisons.csv')
check('12_comparisons',len(comp)==12)
for r in comp:
    key=r['B']+r['evaluation']+r['period']
    for m in 'PGR': close(key+m, r['J_D_'+m],ol[r['B'],r['evaluation'],m,'48',r['period']]['J_D'])
    for m in 'PR':
        delta=float(r['J_D_'+m])-float(r['J_D_G'])
        close(key+m+' delta',delta,r['delta_'+m+'_to_G'])
        close(key+m+' percent',100*delta/float(r['J_D_'+m]),r['percent_'+m+'_to_G'])
    check(key+' P improvement',float(r['delta_P_to_G'])>0)
    check(key+' R mixed ranking',(float(r['delta_R_to_G'])>0)==(r['evaluation']=='E1'))
controls=rows('replanning_executed_controls.csv')
groups=defaultdict(list); attack=defaultdict(list); prefix=defaultdict(list)
for r in controls:
    groups[r['B'],r['evaluation'],r['method'],r['slot']].append(r)
    attack[r['B'],r['evaluation'],r['slot'],r['node']].append(float(r['a_actual']))
    if int(r['slot'])<3:
        for k in ['a_actual','s','r']: prefix[r['B'],r['slot'],r['node'],k].append(float(r[k]))
    for k in ['s','r']: check('nonnegative '+str((r['B'],r['evaluation'],r['method'],r['slot'],r['node'],k)),float(r[k])>=-1e-10)
for key,rs in groups.items():
    use=sum(float(r['s'])+float(r['r']) for r in rs)
    check('budget '+str(key),use<=float(key[0])+1e-10 and len(rs)==6)
    close('resource column '+str(key),use,rs[0]['resource_use'])
for key,vals in attack.items(): check('common attack '+str(key),len(vals)==3 and max(vals)-min(vals)<1e-12)
for key,vals in prefix.items(): check('common prefix '+str(key),max(vals)-min(vals)<1e-12)
body=paper.split('## 参考文献')[0]
citation_lines={str(i):[n for n,line in enumerate(body.splitlines(),1) if f'[{i}]' in line] for i in range(1,6)}
for i,lines in citation_lines.items(): check('citation '+i,bool(lines))
check('pending evidence retained',paper.count('待批准')>=10)
report={'scope':'Document integrity and saved-table arithmetic only; no new optimization/integration or proof certification.', 'checks':len(checks),'passed':not failures,'failures':failures,'equations_unchanged':eq_same,'citation_lines':citation_lines,'copied_artifacts':len(copies),'protected_input_files':len(manifest),'paper_sha256':sha(OUT/'paper_v1_zh.md')}
(OUT/'analysis/verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
raise SystemExit(bool(failures))
