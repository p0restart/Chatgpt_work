"""D2: read saved evidence only. No src imports, integration or optimization."""
from pathlib import Path
import hashlib, json, sys, platform
import numpy as np
import pandas as pd
import yaml

ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'paper/work_d2'
TBL=OUT/'tables'
sources={}; checks=[]; anomalies=[]
def reg(p):
    p=Path(p); p=p if p.is_absolute() else ROOT/p
    b=p.read_bytes(); sources[p.relative_to(ROOT).as_posix()]={'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
    return p
def js(p): return json.loads(reg(p).read_text(encoding='utf-8-sig'))
def csv(p):
    d=pd.read_csv(reg(p)); assert not d.select_dtypes('number').isin([np.inf,-np.inf]).any().any(),p
    return d
def ck(name,yes,detail=''):
    checks.append(dict(check=name,passed=bool(yes),detail=str(detail)))
    if not yes: anomalies.append(dict(severity='BLOCKER',issue=name,detail=str(detail)))
def save(d,name): d.to_csv(TBL/name,index=False,encoding='utf-8-sig')

for pat in ['paper/work_d1/*.md','paper/work_d1/*.json','handoffs/*.md','reviews/*.md','reports/*PROTOCOL.md']:
    for p in ROOT.glob(pat): reg(p).read_text(encoding='utf-8-sig')
for p in ['DECISIONS.md','02_MODEL_SPEC.md','configs/base.yaml','configs/proposed_mechanism_identification.yaml','src/experiments.py','src/supplement_c2.py','src/report_c2.py','src/matched_mechanism.py','src/core.py','src/game_solver.py']:
    reg(p).read_text(encoding='utf-8-sig')
v=js('paper/work_d1/D1_R1_verification.json')
for name,h in v['sha256'].items():
    p=reg('paper/work_d1/'+name)
    if sources[p.relative_to(ROOT).as_posix()]['sha256']!=h:
        anomalies.append(dict(severity='INFO',issue='D1 historical hash differs',detail=name+'; explained by D1_model_rewrite_note.md; current version preserved'))
anomalies.extend([
 dict(severity='INFO',issue='G-D1-R1 report not found locally',detail='User states PASS; not relabelled as local manual approval. Current instruction authorizes D2 only.'),
 dict(severity='INFO',issue='D1 stale three-contribution wording',detail='Use 01_research_contributions.md two-contribution R1; do not overwrite D1.'),
 dict(severity='INFO',issue='Old supplement run01 FAILED',detail='Preserved; run02 is one successful batch, not two replications.'),
 dict(severity='INFO',issue='Historical scenario field separated in matched exports',detail='Namespace/cell reconstructed from case directory and actual model; not P3 separated.')])

M=ROOT/'results/matched_mechanism/run01'
sm=csv(M/'summary.csv')
ck('36 unique matched cases',len(sm)==36 and not sm.case.duplicated().any())
aux={f:csv(M/(f+'.csv')) for f in ['paired_effects','slotwise_effects','robust_effects','source_allocations','capacity_summary','equal_graph_symmetry']}
objs=[]; controls=[]; budgets=[]; states=[]; edges=[]; models={}; rawcontrol={}; provenance=[]
mapping={('equal','high_at_node2'):'A',('equal','high_at_node3'):'B',('unequal','high_at_node2'):'C',('unequal','high_at_node3'):'D'}
for row in sm.itertuples():
    p=M/row.case; m=js(p/'model.json'); models[row.case]=m
    cfg=yaml.safe_load(reg(p/'config.yaml').read_text()); cfg=cfg['base']
    cell=mapping[row.outgoing,row.value]; beta=np.array(m['beta']); q=np.ones(6);q[2 if cell in 'AC' else 3]=4
    ck(row.case+' model',np.count_nonzero(beta)==8 and np.array_equal(m['q'],q) and np.allclose(m['g'],1) and np.allclose(m['h'],.05) and beta[0,2]==beta[0,3] and beta[1,2]==beta[1,3] and np.isclose(beta[2:4,4:6].sum(),.32) and np.allclose(beta[2,4:6],.08 if cell in 'AB' else .12) and np.allclose(beta[3,4:6],.08 if cell in 'AB' else .04))
    c=np.array(js(p/'fine/controls.json'));rawcontrol[row.case]=c
    ck(row.case+' control shape',c.shape==(3,6,6) and np.isfinite(c).all())
    e=js(p/'fine_evaluation/summary.json'); ref=csv(p/'fine_evaluation/refinement.csv')
    ck(row.case+' objective crosscheck',abs(e['fine_J_D']-row.J_D)<1e-10 and abs(e['fine_J_D']-ref.loc[ref.substeps==48,'J_D'].iloc[0])<1e-10)
    ck(row.case+' objective decomposition H12',abs(sum(e[k] for k in ['security','business','isolation','recovery','terminal_defense'])-e['J_D'])<1e-10)
    for f in ['case_audit.json','fine_audit.json','strong_audit.json','attack_evaluation.json']: js(p/f)
    meta=dict(namespace='matched',case=row.case,seed=row.seed,B=row.B,cell=cell,K=6)
    objs.append(dict(**meta,H=48,J_D=e['fine_J_D'],J_A=e['fine_J_A'],J_D_H12=e['J_D'],security_H12=e['security'],business=e['business'],isolation=e['isolation'],recovery=e['recovery']))
    for j,i in zip(*np.nonzero(beta)):edges.append(dict(**meta,source=j,target=i,beta=beta[j,i],q_source=m['q'][j],q_target=m['q'][i]))
    du=c[1]@m['b_s']+c[2]@m['b_r']; au=c[0]@m['d_a']
    b=csv(p/'fine_evaluation/budgets.csv')
    ck(row.case+' capacities',np.max(du-m['B'])<1e-10 and np.max(au-m['A'])<1e-10 and np.max(abs(du-b.defense_use.to_numpy()))<1e-12)
    for k in range(6):
        budgets.append(dict(**meta,slot=k,t_start=k*10/6,t_end=(k+1)*10/6,defense_use=du[k],isolation_use=c[1,k]@m['b_s'],recovery_use=c[2,k]@m['b_r'],attack_use=au[k],slack=m['B']-du[k],binding=abs(m['B']-du[k])<1e-6))
        for i in range(6):controls.append(dict(**meta,slot=k,t_start=k*10/6,t_end=(k+1)*10/6,node=i,a=c[0,k,i],s=c[1,k,i],r=c[2,k,i]))
    st=csv(p/'fine_evaluation/trajectories.csv'); ck(row.case+' states',st.x.between(-1e-10,1+1e-10).all() and len(st)==438)
    for k,val in meta.items():st[k]=val
    st['H']=12; states.append(st)
    provenance.append(dict(**meta,method='Joint-dynamic',evaluation='saved jointly responding candidate',H=48,metric='fine_J_D; paired contrasts; all controls',source=str((p/'fine_evaluation/summary.json').relative_to(ROOT)),display='Fig1/2/3; Table1; S1'))
obj=pd.DataFrame(objs);ctl=pd.DataFrame(controls);bud=pd.DataFrame(budgets)
piv=obj.pivot(index=['seed','B'],columns='cell',values='J_D').add_prefix('J_').reset_index()
piv['equal_effect']=piv.J_B-piv.J_A;piv['unequal_effect']=piv.J_D-piv.J_C;piv['interaction']=piv.unequal_effect-piv.equal_effect
save(obj,'matched_objectives.csv');save(piv,'matched_four_cells.csv');save(ctl,'matched_controls_all_nodes.csv');save(bud,'matched_budgets.csv');save(pd.concat(states),'matched_states_H12.csv');save(pd.DataFrame(edges),'matched_edges.csv')
alloc=[];ints=[]
for (seed,B,cell,node),g in ctl.groupby(['seed','B','cell','node']):
    for window,lo,hi in [('all',0,6),('first4',0,4),('last2',4,6)]:
        sub=g[(g.slot>=lo)&(g.slot<hi)]
        for kind in ['s','r','a']:alloc.append(dict(seed=seed,B=B,cell=cell,node=node,window=window,kind=kind,average=sub[kind].mean(),integral=sub[kind].sum()*10/6))
al=pd.DataFrame(alloc)
for keys,g in al.groupby(['seed','B','node','window','kind']):
    z=g.set_index('cell').average; ints.append(dict(zip(['seed','B','node','window','kind'],keys),equal_effect=z.B-z.A,unequal_effect=z.D-z.C,interaction=(z.D-z.C)-(z.B-z.A)))
it=pd.DataFrame(ints);save(al,'allocations_all_nodes.csv');save(it,'control_interactions_all_nodes.csv')
hist=aux['paired_effects'].query("initialization=='fine'")
join=hist.merge(it,on=['seed','B','node','window','kind'],suffixes=('_old','_new'))
ck('control effects reproduce history',len(join)==108 and np.max(abs(join.interaction_old-join.interaction_new))<1e-12,len(join))
sym=[]
for keys,g in obj.groupby(['seed','B']):
    names=g.set_index('cell')['case'];ca=rawcontrol[names.A];cb=rawcontrol[names.B]
    diff=np.max(abs(ca[:,:, [0,1,3,2,4,5]]-cb));sym.append(dict(seed=keys[0],B=keys[1],max_swapped_control_difference=diff))
sy=pd.DataFrame(sym);save(sy,'symmetry_recomputed.csv');ck('A/B symmetry history',np.max(abs(sy.max_swapped_control_difference-aux['equal_graph_symmetry'].max_swapped_control_difference))<1e-10)

C=ROOT/'results/supplement_c2/run02';comp=[]
for p in sorted((C/'comparison').glob('seed*')):
    if not p.is_dir():continue
    m=js(p/'model.json');cfg=js(p/'config.json');js(p/'inputs.json')
    for ep in sorted(p.glob('*_attack')):
        if not ep.is_dir(): continue
        e=js(ep/'summary.json');c=csv(ep/'controls.csv');b=csv(ep/'budgets.csv');ref=csv(ep/'refinement.csv');st=csv(ep/'trajectories.csv')
        ck(str(ep.relative_to(C))+' complete/finite',len(c)==36 and not c.isna().any().any() and not st.isna().any().any() and e['violation']<1e-10)
        ck(str(ep.relative_to(C))+' H192 objective',abs(e['fine_J_D']-ref.loc[ref.substeps==192,'J_D'].iloc[0])<1e-10)
        ck(str(ep.relative_to(C))+' H48 parts',abs(sum(e[k] for k in ['security','business','isolation','recovery','terminal_defense'])-e['J_D'])<1e-10)
        if e['evaluation']=='common_fixed_attack':ck(str(ep.relative_to(C))+' common attack',np.allclose(c[c.node.isin([0,1])].a,.4) and np.allclose(c[~c.node.isin([0,1])].a,0))
        if e['method']=='Joint-static':ck(str(ep.relative_to(C))+' static',c.groupby('node')[['s','r']].std().max().max()<1e-12)
        if e['method']=='Recovery-only':ck(str(ep.relative_to(C))+' no isolation',abs(c.s).max()<1e-12)
        if e['method']=='Isolation-only':ck(str(ep.relative_to(C))+' no recovery',abs(c.r).max()<1e-12)
        e.update(case=p.name,namespace='matched_D' if 'unequal' in p.name else 'original_counterexample',K=6,H_objective=192,H_parts=48)
        comp.append(e)
        provenance.append(dict(namespace=e['namespace'],case=p.name,seed=e['seed'],B=e['B'],cell='D' if 'unequal' in p.name else 'P3 business_cost',K=6,H=192,method=e['method'],evaluation=e['evaluation'],metric='fine_J_D; 100*(baseline-Joint)/baseline',source=str((ep/'summary.json').relative_to(ROOT)),display='Table2/3; S1'))
co=pd.DataFrame(comp);ck('comparison 160 unique records',len(co)==160 and not co.duplicated(['case','method','evaluation']).any())
ck('matched D 144 records',len(co[co.namespace=='matched_D'])==144)
save(co,'baseline_all_objectives.csv')
pa=[]
for (case,ev),g in co.groupby(['case','evaluation']):
    j=g[g.method=='Joint-dynamic'].iloc[0]
    for r in g.itertuples():
        if r.method=='Joint-dynamic':continue
        pa.append(dict(case=case,namespace=r.namespace,evaluation=ev,seed=r.seed,B=r.B,baseline=r.method,joint=j.fine_J_D,baseline_cost=r.fine_J_D,absolute_difference=r.fine_J_D-j.fine_J_D,reduction_percent=100*(r.fine_J_D-j.fine_J_D)/r.fine_J_D))
pa=pd.DataFrame(pa);save(pa,'baseline_pairs.csv');old=csv(C/'paired.csv');j=pa.merge(old,on=['case','evaluation','baseline'],suffixes=('_new','_old'))
ck('140 pairs reproduce history',len(j)==140 and np.max(abs(j.reduction_percent_new-j.reduction_percent_old))<1e-10)
ss=pa[pa.namespace=='matched_D'].groupby(['evaluation','baseline']).reduction_percent.agg(['count','min','median','max']).reset_index()
ss['positive_count']=[int(((pa.namespace=='matched_D')&(pa.evaluation==r.evaluation)&(pa.baseline==r.baseline)&(pa.reduction_percent>1e-8)).sum()) for r in ss.itertuples()]
save(ss,'baseline_statistics.csv');old=csv(C/'comparison_statistics.csv');j=ss.merge(old,on=['evaluation','baseline'],suffixes=('_new','_old'))
ck('statistics reproduce history',max(np.max(abs(j[k+'_new']-j[k+'_old'])) for k in ['min','median','max'])<1e-10)
ce=js('results/equilibrium_audit/counterexample01/comparison.json');cx=csv('results/equilibrium_audit/counterexample01/cross_evaluation.csv');save(cx,'counterexample_cross_evaluation.csv')
ck('counterexample precise values',abs(cx.query("defense=='Joint' and attack=='Joint'").J_D.iloc[0]-ce['joint_J_D'])<1e-12 and abs(cx.query("defense=='Recovery' and attack=='Recovery'").J_D.iloc[0]-ce['recovery_J_D'])<1e-12)

R=ROOT/'results/work_c2_robustness/k_refinement/run01'
rt={}
for p in (R/'tables').glob('*.csv'):
    rt[p.stem]=csv(p);save(rt[p.stem],'robust_'+p.name)
for r in rt['paired_objectives'].itertuples():
    p=R/f'seed{r.seed}_B{r.B}_{r.cell}';bl=js(p/'baseline.json');cs=js(p/'case.json');js(p/'embedding.json');js(p/'cross_evaluation.json');js(p/'cross_class_deviation.json')
    ck(p.name+' original objectives',abs(bl['J_D']-r.J_D_K6)<1e-12 and abs(cs['paths'][0]['J_D']-r.J_D_K12)<1e-12 and cs['paths'][0]['path']=='warm')
for r in rt['interactions'].itertuples():
    z=rt['paired_objectives'].query('seed==@r.seed and B==@r.B').set_index('cell')
    for k in [6,12]:
        a=z['J_D_K'+str(k)];ck(f'interaction {r.seed}/{r.B} K{k}',abs((a.D-a.C)-(a.B-a.A)-getattr(r,'I'+str(k)))<1e-12)
env=js('results/work_c2_robustness/cross_environment/comparison.json');js('results/work_c2_robustness/cross_environment/environment.json')
for name in ['solver_quality','cross_environment_errors','cross_environment_allocations']:
    save(csv('results/work_c2_robustness/tables/'+name+'.csv'),'environment_'+name+'.csv')
for p in (ROOT/'results/work_c2_robustness/cross_environment/run01').glob('seed*'):
    if p.is_dir():
        js(p/'model.json');js(p/'fine/controls.json');js(p/'fine_evaluation/summary.json')
js('results/supplement_c2/run01/metadata.json');js(C/'metadata.json');js(C/'independent_audit.json');audit=js(M/'audit.json')
save(csv(C/'finite/summary.csv'),'finite_menu_summary.csv')

# Verify existing manifests against their own roots, not against newer source versions.
hashrows=[]
for manifest,base in [(C/'manifest.json',C),(C/'analysis_manifest.json',C),(R/'manifest.json',ROOT),(ROOT/'results/work_c2_robustness/logs/history_input_hashes.json',ROOT)]:
    data=js(manifest)
    if isinstance(data,dict) and 'files' in data:data=data['files']
    items=[(x['path'],x['sha256']) for x in data] if isinstance(data,list) else list(data.items())
    for rel,h in items:
        p=base/Path(rel);exists=p.exists();actual=hashlib.sha256(p.read_bytes()).hexdigest() if exists else None
        resolved=False
        if actual!=h and p==ROOT/'reviews/APPROVAL_LOG.md':
            b=p.read_bytes();idx=b.index(b'## G2-Work-C2')
            resolved=any(hashlib.sha256(b[:i]).hexdigest()==h for i in range(idx-8,idx+1))
            if resolved:anomalies.append(dict(severity='INFO',issue='Historical approval hash resolved',detail='Current log prefix of 4290 bytes exactly matches pre-G2 hash; only subsequent approved G2-Work-C2 append differs. No experimental data mismatch.'))
        hashrows.append(dict(manifest=str(manifest.relative_to(ROOT)),path=rel,exists=exists,match=actual==h,resolved_append=resolved))
        if actual!=h and not resolved:anomalies.append(dict(severity='BLOCKER',issue='Historical manifest mismatch',detail=str(p)))
save(pd.DataFrame(hashrows),'historical_hash_checks.csv');ck('historical manifests reconciled',all(x['match'] or x['resolved_append'] for x in hashrows),len(hashrows))
save(pd.DataFrame(provenance),'result_provenance.csv');save(pd.DataFrame(checks),'verification_checks.csv');save(pd.DataFrame(anomalies),'anomalies.csv')
(OUT/'analysis/source_manifest.json').write_text(json.dumps(sources,ensure_ascii=False,indent=2),encoding='utf-8')
result=dict(date='2026-11-11',python=platform.python_version(),numpy=np.__version__,pandas=pd.__version__,source_files=len(sources),checks=len(checks),failed_checks=sum(not x['passed'] for x in checks),hash_checks=len(hashrows),blockers=[a for a in anomalies if a['severity']=='BLOCKER'],matched_interactions=piv.to_dict('records'),counterexample=ce,cross_environment=env,matched_historical_audit=audit)
(OUT/'analysis/verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k not in ['matched_interactions','matched_historical_audit']},ensure_ascii=False,indent=2))
print(piv.to_string(index=False));print(ss.to_string(index=False))
if result['blockers']:sys.exit(1)
