"""Rebuild the audit tables without rerunning optimizers."""
import argparse
import hashlib
import json
from pathlib import Path
import pandas as pd
from .experiments import write_json

p=argparse.ArgumentParser();p.add_argument('--root',required=True);args=p.parse_args()
root=Path(args.root)
metadata=json.loads((root/'metadata.json').read_text())
assert metadata['status']=='COMPLETED'
rows=[];raw=[];cases=[]
for folder in sorted(p for p in root.iterdir() if p.is_dir() and (p/'case_audit.json').exists()):
    cases.append(dict(case=folder.name,**json.loads((folder/'case_audit.json').read_text())))
    for label in ['old_strong_audit','new_strong_audit']:
        g=json.loads((folder/(label+'.json')).read_text())
        for player in ['D','A']:raw.extend(g[player]['raw'])
        for s in g['sparse']:raw.extend(s['raw'])
    marg=pd.read_csv(folder/'marginals.csv')
    for slot,group in marg.groupby('slot'):
        inside=group[(group.control>1e-4)&(group.control<1-1e-4)]
        rows.append(dict(case=folder.name,slot=int(slot),budget_slack=float(group.budget_slack.iloc[0]),
             active_marginal_spread=float(inside.net_benefit_per_capacity.max()-inside.net_benefit_per_capacity.min()) if len(inside)>1 else 0,
             total_s=float(group[group.kind=='s'].control.sum()),total_r=float(group[group.kind=='r'].control.sum())))
pd.DataFrame(rows).to_csv(root/'slot_mechanism_audit.csv',index=False)
pd.DataFrame(cases).to_csv(root/'case_summary.csv',index=False)
trials=pd.read_csv(root/'summary.csv')
result=dict(cases=len(cases),trials=len(trials),trials_passed=int(trials.passed.sum()),
            strong_local_starts=len(raw),all_strong_starts_success=all(r['success'] for r in raw),
            max_violation=max(r['violation'] for r in raw),
            max_initialization_control_difference=max(c['control_difference_across_initializations'] for c in cases),
            max_new_observed_relative_improvement=max(c['new_relative_max'] for c in cases),
            max_transfer_derivative_error=max(c['max_direction_error'] for c in cases),
            max_active_marginal_spread=max(r['active_marginal_spread'] for r in rows),global_certificate=False)
write_json(root/'verification.json',result)
print(json.dumps(result,indent=2))
