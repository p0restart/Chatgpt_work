"""Check the D8 manuscript against saved D7 evidence, without solving or integrating."""
from pathlib import Path
import hashlib
import json
import re
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'paper/work_d8_1'
D7=ROOT/'paper/work_d7'
paper=(OUT/'paper_v3_zh.md').read_text(encoding='utf-8')
old=(D7/'paper_v2_zh.md').read_text(encoding='utf-8')
checks=[]
def check(name,ok):
    checks.append(dict(check=name,passed=bool(ok)))
    assert ok,name
def source(name):return pd.read_csv(OUT/'data'/f'{name}.csv')
def rounded(name,val,shown,digits=6):check(name,f'{val:.{digits}f}'==shown)

required=['paper_v3_zh.md','revision_log.md','claim_evidence_audit.md','algorithm_audit.md','figure_table_plan.md','remaining_issues.md']
for f in required:
    s=(OUT/f).read_text(encoding='utf-8')
    check(f+' present and substantive',len(s)>1000)
    check(f+' no unfilled placeholders','{{' not in s and 'TODO' not in s)
    check(f+' no control bytes',not any(ord(c)<32 and c not in '\n\r\t' for c in s))
for n in range(1,6):check(f'chapter {n}',bool(re.search(r'^# '+str(n)+r' ',paper,re.M)))
for term in ['槽','四格','运行日志显示','实验跑出','控制时段']:
    check('terminology '+term,term not in paper)
for n in range(1,9):
    def eq(s):
        blocks=re.findall(r'\\\[([\s\S]*?)\\\]',s)
        return next(b for b in blocks if f'\\tag{{{n}}}' in b)
    check(f'frozen equation {n} unchanged',eq(paper)==eq(old))
check('event metric equation 9',paper.count(r'\tag{9}')==1)
check('bibliography exactly retained',paper.split('## 参考文献',1)[1]==old.split('## 参考文献',1)[1])
check('15 references',len(re.findall(r'^\[\d+\]',paper,re.M))==15)
for n in range(1,9):check(f'main table {n}',f'**表{n}　' in paper)
check('supplementary full table','表A1' in paper)
images=re.findall(r'!\[[^\]]*\]\(([^)]+)\)',paper)
check('four nonduplicate figures',len(images)==4 and len(set(images))==4)
for path in images:check('image '+path,(OUT/path).is_file())
algos=re.findall(r'```text\n(算法[12]：[\s\S]*?)\n```',paper)
alg_audit=(OUT/'algorithm_audit.md').read_text(encoding='utf-8')
check('two algorithms',len(algos)==2)
for a in algos:check(a.splitlines()[0]+' audit matches',a in alg_audit)

# Numeric table values must occur in the manuscript and preserve signs.
for name,cols in [
    ('cross_matrix',['a0','aG','aBR_F']),
    ('fixed_attack_costs',['security','business','isolation','recovery','J_D']),
    ('rolling_event_post',['P','G','R','percent_P_to_G','percent_P_to_R','R_minus_G','percent_R_to_G'])]:
    for v in source(name)[cols].to_numpy().ravel():
        check(name+' '+f'{v:.6f}',f'{v:.6f}' in paper)
full=source('rolling_all_periods')
for v in full[full.period=='full'][['P','G','R','percent_P_to_G','percent_P_to_R','percent_R_to_G']].to_numpy().ravel():
    check('full loss '+f'{v:.6f}',f'{v:.6f}' in paper)

actions=source('asset_actions_B1.2').set_index(['paper_node','slot'])
action_values=[('v1',0,'s','0.323232'),('v1',0,'r','0.294892'),('v1',1,'s','0.345588'),('v1',1,'r','0.348708'),('v1',1,'x_start','0.194672'),('v1',4,'s','0.098344'),('v4',1,'x_start','0.014047'),('v4',1,'s','0.000951'),('v4',4,'x_start','0.073640'),('v4',4,'s','0.042531'),('v4',4,'r','0.083404'),('v5',0,'r','0.004480'),('v5',4,'r','0.139747'),('v5',5,'r','0.073475'),('v3',5,'r','0.057968'),('v4',5,'r','0.030317'),('v3',4,'s','0.085630'),('v3',3,'r','0.156446')]
for node,k,col,shown in action_values:
    rounded(f'asset prose {node}/{k}/{col}',actions.loc[(node,k),col],shown)
    check('asset numeric cited '+shown,shown in paper)
avg=source('asset_mean_all_budgets')
for B in [.6,1.2,1.8]:
    d=avg[avg.B==B]
    expected=['v1','v2','v3','v5','v4','v6'] if B==.6 else ['v1','v2','v3','v4','v5','v6']
    check(f'asset resource ordering B{B}',d.sort_values('asset_resource',ascending=False).paper_node.tolist()==expected)
    for val in d.asset_resource:check('asset budget table '+f'{val:.6f}',f'{val:.6f}' in paper)
for node,B,shown in [('v1',.6,'60.09'),('v1',1.8,'44.48'),('v4',.6,'2.16'),('v4',1.8,'9.43'),('v3',.6,'10.10'),('v3',1.8,'15.07')]:
    rounded('asset share '+node+str(B),100*avg[(avg.paper_node==node)&(avg.B==B)].iloc[0].share_of_used_defense,shown,2)

first=source('prediction_errors_first_B1.2')
for E,M,linf,l1 in [('E0','G','0.123123','0.246245'),('E0','R','0.022252','0.044504'),('E1','G','0.008902','0.017804'),('E1','R','0.109772','0.219545')]:
    v=first[(first.evaluation==E)&(first.method==M)].iloc[0]
    rounded(E+M+' Linf',v.Linf,linf);rounded(E+M+' L1',v.L1,l1)
mean=source('prediction_error_time_mean')
for B in [.6,1.2,1.8]:
    d=mean[(mean['case']=='event')&(mean.B==B)].set_index(['evaluation','method'])
    check(f'E0 R matches better B{B}',d.loc[('E0','R'),'L1']<d.loc[('E0','G'),'L1'])
    check(f'E1 G matches better B{B}',d.loc[('E1','G'),'L1']<d.loc[('E1','R'),'L1'])
for E,M,shown in [('E0','G','0.290254'),('E0','R','0.014835'),('E1','G','0.009603'),('E1','R','0.268425')]:
    v=mean[(mean['case']=='event')&(mean.B==1.2)&(mean.evaluation==E)&(mean.method==M)].iloc[0]
    rounded('time mean '+E+M,v.L1,shown)
exe=pd.read_csv(D7/'results/rolling_event_B1.2/executed_controls.csv')
for M,col,vals in [('G','s',['0.031608','0.053527','0.000000']),('G','r',['0.082296','0.092094','0.036463']),('P','r',['0.085494','0.083404','0.030317'])]:
    d=exe[(exe.evaluation=='E1')&(exe.method==M)&(exe.node==3)&(exe.slot>=3)].sort_values('slot')
    for i,val in enumerate(vals):rounded(f'execution {M}{col}/{i}',d.iloc[i][col],val)
cost=source('execution_costs')
d=cost[(cost['case']=='event')&(cost.B==1.2)&(cost.evaluation=='E0')&(cost.period=='post')].set_index('method')
rounded('event E0 security improvement',d.loc['P','security']-d.loc['G','security'],'0.052344')
rounded('event E0 extra action costs',(d.loc['G',['business','isolation','recovery']]-d.loc['P',['business','isolation','recovery']]).sum(),'0.048333')

audit=json.loads((OUT/'data/audit_checks.json').read_text())
check('all saved-data arithmetic checks passed',audit['passed'])
hashes=json.loads((OUT/'data/source_hashes.json').read_text())
for rel,value in hashes.items():
    check('source unchanged '+rel,hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()==value)
check('no solver imports in D8 analysis',all(not re.search(r'^(from src|import src|from paper.work_d[57])',p.read_text(encoding='utf-8'),re.M) for p in (OUT/'analysis').glob('*.py')))
result=dict(passed=True,checks=len(checks),scope='Document, frozen-equation, numeric-table, narrative-value and saved-source checks; no new experiment.',results=checks)
(OUT/'data/delivery_checks.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(dict(passed=True,delivery_checks=len(checks),data_checks=len(audit['checks']),unchanged_sources=len(hashes)),ensure_ascii=False))
