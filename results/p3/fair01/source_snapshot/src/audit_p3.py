"""Reintegrate all saved schedules and audit exact pilot reproduction."""
import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd
import yaml
from .core import simulate, check_controls, synthetic_model_from_config
from .experiments import write_json


def audit(root):
    rows=[]; solver=[]; ranking=[]
    for case in sorted(root.glob('seed*')):
        cfg=yaml.safe_load((case/'config.yaml').read_text(encoding='utf-8'))
        m=synthetic_model_from_config(cfg)
        for folder in sorted(case.glob('*_attack')):
            saved=json.loads((folder/'summary.json').read_text(encoding='utf-8'))
            data=pd.read_csv(folder/'controls.csv')
            controls=[data.pivot(index='slot',columns='node',values=c).to_numpy() for c in ('a','s','r')]
            check_controls(m,*controls)
            sim=simulate(m,*controls,cfg['T'],cfg['rk4_substeps_per_slot']*4)
            err=max(abs(saved['fine_J_D']-sim['J_D']),abs(saved['fine_J_A']-sim['J_A']))
            parts=sum(saved[p] for p in ('security','business','isolation','recovery','terminal_defense'))
            rows.append(dict(case=case.name,method=saved['method'],evaluation=saved['evaluation'],
                             reintegration_error=err,decomposition_error=abs(parts-saved['J_D']),
                             integration_error=saved['integration_error'],violation=saved['violation'],
                             domain_pass=sim['states'].min()>=-1e-9 and sim['states'].max()<=1+1e-9))
        for file in case.glob('*_response.json'):
            info=json.loads(file.read_text(encoding='utf-8'))
            solver.append(dict(case=case.name,source=file.name,player=info['player'],
                               residual=info['residual'],all_starts_success=info['all_starts_success'],
                               max_start_residual=max(r['projected_residual'] for r in info['raw']),
                               objective_spread=info['objective_spread']))
        for file in case.glob('*_alternating.json'):
            trace=json.loads(file.read_text(encoding='utf-8'))
            for step in trace:
                for p in ('D','A','sequential_attack'):
                    if p not in step: continue
                    info=step[p]
                    solver.append(dict(case=case.name,source=file.name,player=p,iteration=step['iteration'],
                                       residual=info['residual'],all_starts_success=info['all_starts_success'],
                                       max_start_residual=max(r['projected_residual'] for r in info['raw']),
                                       objective_spread=info['objective_spread']))
        table=pd.read_csv(case/'summary.csv')
        for evaluation,g in table.groupby('evaluation'):
            ranking.append(dict(case=case.name,evaluation=evaluation,
                                stable=g.sort_values('J_D').method.tolist()==g.sort_values('fine_J_D').method.tolist()))
    a=pd.DataFrame(rows); a.to_csv(root/'reintegration_audit.csv',index=False)
    s=pd.DataFrame(solver); s.to_csv(root/'optimizer_audit.csv',index=False)
    pd.DataFrame(ranking).to_csv(root/'ranking_audit.csv',index=False)
    table=pd.read_csv(root/'summary.csv')
    g=table.dropna(subset=['relative_D'])
    result=dict(evaluations=len(a),configurations=len(list(root.glob('seed*'))),
                reintegration_max_error=float(a.reintegration_error.max()),
                integration_max_error=float(a.integration_error.max()),
                decomposition_max_error=float(a.decomposition_error.max()),
                violation_max=float(a.violation.max()),domain_pass=bool(a.domain_pass.all()),
                all_optimizers_success=bool(s.all_starts_success.all()),
                selected_response_max_residual=float(s.residual.max()),
                all_start_max_residual=float(s.max_start_residual.max()),
                multistart_max_objective_spread=float(s.objective_spread.max()),
                ranking_changes=sum(not r['stable'] for r in ranking),
                game_count=len(g),game_targets_pass=int(g.target_met.sum()),game_quality_pass=int(g.quality_met.sum()),
                relative_gap_min=float(g[['relative_D','relative_A']].max(axis=1).min()),
                relative_gap_max=float(g[['relative_D','relative_A']].max(axis=1).max()))
    write_json(root/'audit.json',result)
    return result


def compare_pilots(first,second):
    errors=[]
    for file in first.rglob('controls.csv'):
        a=pd.read_csv(file).to_numpy(); b=pd.read_csv(second/file.relative_to(first)).to_numpy()
        errors.append(float(np.max(np.abs(a-b))))
    a=pd.read_csv(first/'summary.csv'); b=pd.read_csv(second/'summary.csv')
    cols=[c for c in a.select_dtypes(include='number').columns if c!='method_seconds']
    errors.append(float(np.nanmax(np.abs(a[cols].to_numpy()-b[cols].to_numpy()))))
    return dict(max_abs_difference=max(errors),pass_tolerance=1e-10,passed=max(errors)<=1e-10,
                scope='Both pilot modes, complete controls and numeric summaries excluding timing')


if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--root',required=True)
    args=p.parse_args(); root=Path(args.root)
    print(json.dumps(audit(root),indent=2))
    result=compare_pilots(root.parent/'pilot01',root.parent/'pilot02')
    write_json(root/'pilot_reproduction.json',result)
    print(result)
