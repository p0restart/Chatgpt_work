"""Descriptive G2 evidence tables; no significance claims."""
import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd
from .experiments import write_json


def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);args=p.parse_args()
    root=Path(args.root); df=pd.read_csv(root/'summary.csv')
    group=df.groupby(['scenario','B','method','evaluation'])
    group[['J_D','J_A','binding_slots','isolation_use_mean','recovery_use_mean']].agg(['mean','std','min','max']).to_csv(root/'seed_statistics.csv')
    pair=df.pivot(index=['seed','scenario','B','evaluation'],columns='method',values='J_D').reset_index()
    baselines=['Uniform','Value-only','Spread-only','Isolation-only','Recovery-only']
    for b in baselines:
        pair[f'reduction_vs_{b}_pct']=100*(pair[b]-pair['Joint-dynamic'])/pair[b]
    pair['best_baseline']=pair[baselines].min(axis=1)
    pair['reduction_vs_best_pct']=100*(pair.best_baseline-pair['Joint-dynamic'])/pair.best_baseline
    pair.to_csv(root/'paired_comparisons.csv',index=False)
    reductions=[]
    for evaluation,g in pair.groupby('evaluation'):
        for b in baselines+['best']:
            col=f'reduction_vs_{b}_pct'
            reductions.append(dict(evaluation=evaluation,baseline=b,count=len(g),mean_pct=g[col].mean(),
                                   sd_pct=g[col].std(),min_pct=g[col].min(),max_pct=g[col].max(),
                                   positive_count=int((g[col]>1e-6).sum()),negative_count=int((g[col]<-1e-6).sum())))
    pd.DataFrame(reductions).to_csv(root/'reduction_statistics.csv',index=False)
    mechanisms=[]; hashes={}; same_graph=True
    for case in sorted(p for p in root.glob('seed*') if p.is_dir()):
        m=json.loads((case/'model.json').read_text()); beta=np.array(m['beta'])
        seed=int(case.name.split('_')[0][4:])
        if seed in hashes: same_graph=same_graph and np.array_equal(hashes[seed],beta)
        else: hashes[seed]=beta
        highspread=int(beta.sum(axis=1).argmax());highvalue=int(np.argmax(m['q']))
        c=pd.read_csv(case/'Joint-dynamic_adaptive_attack'/'controls.csv')
        s=c[c.node==highspread].s.to_numpy();r=c[c.node==highvalue].r.to_numpy()
        delta=s-r
        signs=np.sign(delta[np.abs(delta)>1e-6])
        mechanisms.append(dict(case=case.name,seed=seed,B=m['B'],scenario=case.name.split('_B')[0].split('_',1)[1],
                               high_spread=highspread,high_value=highvalue,mean_source_isolation=float(s.mean()),
                               mean_value_recovery=float(r.mean()),
                               exploratory_priority_sign_changes=int(np.sum(signs[1:]!=signs[:-1]))))
    mechanism=pd.DataFrame(mechanisms); mechanism.to_csv(root/'mechanism_diagnostics.csv',index=False)
    business=mechanism[mechanism.scenario.isin(['separated','business_cost'])].pivot(index=['seed','B'],columns='scenario',values='mean_source_isolation').reset_index()
    business['change_C_minus_B']=business.business_cost-business.separated
    business.to_csv(root/'business_paired.csv',index=False)
    joint=df[(df.method=='Joint-dynamic') & (df.evaluation=='adaptive_attack')]
    result=dict(same_graph_within_seed=bool(same_graph),reductions=reductions,
                joint_binding_by_B=joint.groupby('B').binding_slots.agg(['min','max','mean']).reset_index().to_dict('records'),
                business_change_min=float(business.change_C_minus_B.min()),business_change_max=float(business.change_C_minus_B.max()),
                business_decreased_count=int((business.change_C_minus_B < -1e-6).sum()),
                exploratory_priority_switch_count=int((mechanism.exploratory_priority_sign_changes>0).sum()))
    write_json(root/'findings.json',result)
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
