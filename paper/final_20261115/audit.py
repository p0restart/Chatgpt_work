"""Deterministic manuscript/data audit, independent of the assembly calculations."""
from pathlib import Path
import re,json,hashlib
import numpy as np
import pandas as pd
from scipy.integrate import simpson
BASE=Path(__file__).resolve().parent
text=(BASE/'论文终稿_中文.md').read_text(encoding='utf-8')
checks=[]
def check(name,condition,detail=''):
    checks.append(dict(check=name,passed=bool(condition),detail=str(detail)))
def tbl(n):
    m=re.search(r'\*\*表4-'+str(n)+r'[^\n]*\n\n((?:\|[^\n]*\n?)+)',text)
    assert m,n
    rows=[]
    for line in m.group(1).splitlines()[2:]:rows.append([x.strip() for x in line.strip('|').split('|')])
    return rows
def close(a,b):return abs(float(a)-float(b))<=5.1e-7
raw=BASE/'raw_d7/results'
for n,row in enumerate(tbl(3)):
    g=json.loads((raw/'static/B1.2/G_controls.json').read_text());f=json.loads((raw/'static/B1.2/F_controls.json').read_text())
    expected=[sum(g[1][n]),sum(g[2][n]),sum(g[1][n])+sum(g[2][n]),sum(f[1][n])+sum(f[2][n])]
    check(f'table4_3_slot{n+1}',all(close(a,b) for a,b in zip(row[1:],expected)),expected)
for row in tbl(6):
    B=float(row[0]);a={'$a_0$':'a0','$a_G$':'aG','$a_{BR,F}$':'aBR_F'}[row[1]]
    d=pd.read_csv(raw/f'static/B{B}/cross_evaluation.csv');d=d[d.attack==a].set_index('method')
    g=d.loc['G','J_D'];f=d.loc['F','J_D']
    check(f'table4_6_{B}_{a}',all(close(x,y) for x,y in zip(row[2:],[g,f,g-f])),[g,f,g-f])
labels={'加权受损安全损失':'security','隔离业务中断':'business','隔离二次成本':'isolation','恢复二次成本':'recovery','综合防御损失':'J_D'}
cross=pd.read_csv(raw/'static/B1.2/cross_evaluation.csv')
for row in tbl(7):
    a={'$a_G$':'aG','$a_0$':'a0'}[row[0]];key=labels[row[1]];d=cross[cross.attack==a].set_index('method');g=d.loc['G',key];f=d.loc['F',key]
    check(f'table4_7_{a}_{key}',all(close(x,y) for x,y in zip(row[2:],[g,f,g-f])),[g,f,g-f])
for row in tbl(8):
    B=float(row[0]);E=row[1];d=pd.read_csv(raw/f'rolling_event_B{B}/objectives.csv')
    d=d[(d.evaluation==E)&(d.H==48)&(d.period=='post')].set_index('method')
    p,g,r=[d.loc[m,'J_D'] for m in ['P','G','R']]
    expected=[p,g,r,100*(p-g)/p,100*(p-r)/p]
    check(f'table4_8_{B}_{E}',all(close(x.rstrip('%'),y) for x,y in zip(row[2:],expected)),expected)

# Check every representative action/state cell and every mean-control cell.
dec=pd.read_csv(raw/'static/B1.2/G_decisions.csv')
for row,(node,slot) in zip(tbl(4),[(0,0),(0,1),(3,1),(3,4),(4,0),(4,4)]):
    d=dec[(dec.node==node)&(dec.slot==slot)].iloc[0]
    check(f'table4_4_{node}_{slot}',all(close(x,y) for x,y in zip(row[2:],[d.x_start,d.s,d.r])))
for i,row in enumerate(tbl(5)):
    expected=[]
    for component in [1,2]:
        for p in ['G','F']:
            u=json.loads((raw/f'static/B1.2/{p}_controls.json').read_text());expected.append(np.mean(np.array(u[component])[:,i]))
    check(f'table4_5_{i+1}',all(close(x,y) for x,y in zip(row[1:],expected)))

for scenario in ['aG','a0']:
    data=pd.read_csv(BASE/f'results/gf_state_common_{scenario}.csv')
    g=data[data.plan=='G'];f=data[data.plan=='F']
    check(scenario+'_paired_times',np.array_equal(g.time.to_numpy(),f.time.to_numpy()) and len(g)==1153)
    check(scenario+'_same_initial',np.array_equal(g.iloc[0][[f'x{i}' for i in range(1,7)]].to_numpy(),f.iloc[0][[f'x{i}' for i in range(1,7)]].to_numpy()))
    check(scenario+'_weighted_identity',np.max(abs(data.xq-data[[f'x{i}' for i in range(1,7)]].to_numpy()@np.array([1,1,1,1,4,1])/9))<1e-14)
    for p,d in [('G',g),('F',f)]:
        t=d.time.to_numpy();rate=9*d.xq.to_numpy()
        # Independent quadrature of the actual exported state samples.
        area=sum(simpson(rate[k*192:(k+1)*192+1],x=t[k*192:(k+1)*192+1]) for k in range(6))
        check(scenario+'_'+p+'_security_integral_identity',abs(area-d.cumulative_security.iloc[-1])<1e-8,area-d.cumulative_security.iloc[-1])
    a=json.loads((raw/'static/B1.2/cross_attacks.json').read_text())[scenario]
    check(scenario+'_attack_shape',np.asarray(a).shape==(6,6))
tags=list(map(int,re.findall(r'\\tag\{(\d+)\}',text)))
check('equation_numbers',tags==list(range(1,11)),tags)
images=re.findall(r'!\[[^\]]*\]\(([^)]+)\)',text)
check('all_8_figure_links_exist',len(images)==8 and all((BASE/p).exists() for p in images),images)
check('five_chapters',len(re.findall(r'^# 第[一二三四五]章',text,re.M))==5)
check('no_draft_residue',not any(s in text for s in ['待补图','待核验','建议图注','若G低于F','当前写作包','0.599999999999']))
refs=re.findall(r'^\[(\d+)\]',text,re.M);check('15_references',refs==list(map(str,range(1,16))),refs)
body=text.split('# 参考文献')[0]
body=re.sub(r'\$\$.*?\$\$|\$[^$]*\$','',body,flags=re.S)
cited=set()
for group in re.findall(r'\[([\d,\-]+)\]',body):
    for bit in group.split(','):
        if '-' in bit:
            lo,hi=map(int,bit.split('-'));cited.update(range(lo,hi+1))
        else:cited.add(int(bit))
check('all_references_cited',cited==set(range(1,16)),sorted(cited))
base=(BASE/'source_handoff/第3章_已批准基准版_请保留.md').read_text(encoding='utf-8')
changes=json.loads((BASE/'chapter3_mechanical_changes.json').read_text(encoding='utf-8'))
for old,new in changes.items():base=base.replace(old,new)
final=(BASE/'chapters/chapter3.md').read_text(encoding='utf-8')
check('chapter3_only_registered_mechanical_changes',base.strip()==final.strip())
attempts=[]
for p in [raw/'static/optimizer_attempts.csv',*raw.glob('rolling_*/optimizer_attempts.csv')]:attempts.append(pd.read_csv(p))
ad=pd.concat(attempts);check('1544_optimizer_successes',len(ad)==1544 and ad.success.all(),len(ad))
manifest=json.loads((BASE/'raw_manifest.json').read_text())
check('copied_raw_hashes_intact',all(hashlib.sha256((BASE/p).read_bytes()).hexdigest()==v['sha256'] for p,v in manifest.items()))
summary=dict(passed=all(d['passed'] for d in checks),checks=len(checks),manuscript_sha256=hashlib.sha256((BASE/'论文终稿_中文.md').read_bytes()).hexdigest())
(BASE/'results/manuscript_audit_checks.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2),encoding='utf-8')
(BASE/'results/manuscript_audit_summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
print(json.dumps(summary,indent=2))
for d in checks:
    if not d['passed']:print(d)
assert summary['passed']
