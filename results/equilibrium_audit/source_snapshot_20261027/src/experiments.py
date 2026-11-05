"""Approved G1 experiments. Local-response diagnostics, never a Nash certificate."""
import argparse
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import sys
import time
import numpy as np
import pandas as pd
import scipy
import yaml
from .core import synthetic_model_from_config, simulate, check_controls
from .game_solver import response, alternating_responses


METHODS = ['Uniform', 'Value-only', 'Spread-only', 'Isolation-only', 'Recovery-only', 'Joint-dynamic']


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False), encoding='utf-8')


def initial_controls(m, K, method):
    a = np.zeros((K, m.n))
    a[:, m.entry] = min(1., m.A / m.d_a[m.entry].sum())
    weights = m.q if method == 'Value-only' else m.beta.sum(axis=1) if method == 'Spread-only' else np.ones(m.n)
    weights = weights / weights.sum()
    # Fixed heuristics: half the capacity for each control, no outcome tuning.
    s = np.tile(np.minimum(1., .5*m.B*weights/m.b_s), (K, 1))
    r = np.tile(np.minimum(1., .5*m.B*weights/m.b_r), (K, 1))
    if method == 'Isolation-only':
        r[:] = 0
    if method == 'Recovery-only':
        s[:] = 0
    check_controls(m, a, s, r)
    return a, s, r


def save_evaluation(folder, m, cfg, controls, method, evaluation, gap=None):
    folder.mkdir()
    K, T, steps = cfg['K'], cfg['T'], cfg['rk4_substeps_per_slot']
    a, s, r = controls
    check_controls(m, a, s, r)
    sims = {st: simulate(m, *controls, T, st) for st in (steps, steps*2, steps*4)}
    sim, fine = sims[steps], sims[steps*4]
    pd.DataFrame([dict(slot=k, node=i, a=a[k,i], s=s[k,i], r=r[k,i])
                  for k in range(K) for i in range(m.n)]).to_csv(folder/'controls.csv', index=False)
    pd.DataFrame([dict(t=t, node=i, x=x[i]) for t,x in zip(sim['times'],sim['states'])
                  for i in range(m.n)]).to_csv(folder/'trajectories.csv', index=False)
    du = s @ m.b_s + r @ m.b_r
    au = a @ m.d_a
    pd.DataFrame(dict(slot=np.arange(K), defense_use=du, attack_use=au,
                      defense_slack=m.B-du, attack_slack=m.A-au)).to_csv(folder/'budgets.csv', index=False)
    refinements = [dict(substeps=st, J_D=v['J_D'], J_A=v['J_A'],
                        error_J_D=abs(v['J_D']-fine['J_D']), error_J_A=abs(v['J_A']-fine['J_A']),
                        max_component_error=max(abs(v['parts'][p]-fine['parts'][p]) for p in v['parts']),
                        state_error=float(np.max(np.abs(v['states'][-1]-fine['states'][-1]))))
                   for st,v in sims.items()]
    pd.DataFrame(refinements).to_csv(folder/'refinement.csv', index=False)
    row = dict(seed=cfg['seed'], scenario=cfg['scenario'], B=m.B, method=method, evaluation=evaluation,
               J_D=sim['J_D'], J_A=sim['J_A'], **sim['parts'],
               high_value_area=float(np.trapz(sim['states'][:,np.argmax(m.q)],sim['times'])),
               defense_use_mean=float(du.mean()), binding_slots=int(np.sum(abs(du-m.B)<1e-6)),
               isolation_use_mean=float((s@m.b_s).mean()), recovery_use_mean=float((r@m.b_r).mean()),
               violation=float(max(0, np.max(du-m.B), np.max(au-m.A),
                                   *[max(float(np.max(-u)),float(np.max(u-1))) for u in controls])),
               integration_error=max(refinements[0]['error_J_D'],refinements[0]['error_J_A']),
               fine_J_D=fine['J_D'], fine_J_A=fine['J_A'],
               state_min=float(sim['states'].min()), state_max=float(sim['states'].max()))
    if gap:
        row.update({k:gap[k] for k in ('gap_D','gap_A','relative_D','relative_A','target_met','quality_met')})
    write_json(folder/'summary.json', row)
    return row


def run_case(cfg, folder, methods=METHODS):
    folder.mkdir()
    m = synthetic_model_from_config(cfg)
    T, K, steps, seed = cfg['T'], cfg['K'], cfg['rk4_substeps_per_slot'], cfg['seed']
    (folder/'config.yaml').write_text(yaml.safe_dump(cfg,sort_keys=False),encoding='utf-8')
    write_json(folder/'model.json', {k:v.tolist() if isinstance(v,np.ndarray) else v for k,v in asdict(m).items()})
    pd.DataFrame([dict(source=j,target=i,beta=m.beta[j,i]) for j,i in zip(*np.nonzero(m.beta))]).to_csv(folder/'edges.csv',index=False)
    rows, solver_rows = [], []
    for method in methods:
        start = time.perf_counter()
        mode = {'Isolation-only':'isolation','Recovery-only':'recovery'}.get(method,'joint')
        initial = initial_controls(m,K,method)
        fixed = initial
        if method in METHODS[3:]:
            fixed, info = response(m, initial, T, steps, 'D', seed, cfg['solver']['br_restarts'], mode)
            write_json(folder/f'{method}_fixed_response.json',info)
        rows.append(save_evaluation(folder/f'{method}_fixed_attack',m,cfg,fixed,method,'fixed_attack'))
        if method in METHODS[3:]:
            progress = folder/f'{method}_progress.jsonl'
            def callback(audit):
                with progress.open('a',encoding='utf-8') as f:
                    f.write(json.dumps(audit)+'\n')
                print(f"{folder.name} {method} round={audit['iteration']} gap={max(audit['relative_D'],audit['relative_A']):.6g}",flush=True)
            adaptive, trace = alternating_responses(m,fixed,T,steps,seed,cfg['solver'],mode,callback)
            write_json(folder/f'{method}_alternating.json',trace)
            gap = trace[-1]
            for audit in trace:
                for player in ('D','A','sequential_attack'):
                    if player not in audit:
                        continue
                    for raw in audit[player]['raw']:
                        solver_rows.append(dict(method=method,iteration=audit['iteration'],player=player,
                                                **{k:v for k,v in raw.items() if k not in ('initial_control','control')}))
        else:
            adaptive, info = response(m,fixed,T,steps,'A',seed,cfg['solver']['br_restarts'])
            write_json(folder/f'{method}_adaptive_response.json',info)
            gap = None
        rows.append(save_evaluation(folder/f'{method}_adaptive_attack',m,cfg,adaptive,method,'adaptive_attack',gap))
        rows[-1]['method_seconds'] = time.perf_counter()-start
        pd.DataFrame(rows).to_csv(folder/'summary.csv',index=False)
        pd.DataFrame(solver_rows).to_csv(folder/'solver_trace.csv',index=False)
    return rows


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--config',default='configs/base.yaml')
    parser.add_argument('--output',required=True)
    parser.add_argument('--pilot',action='store_true')
    args=parser.parse_args()
    cfg=yaml.safe_load(Path(args.config).read_text(encoding='utf-8'))
    out=Path(args.output); out.mkdir(parents=True,exist_ok=False)
    start=time.perf_counter()
    metadata=dict(started_at=datetime.now(timezone.utc).isoformat(),command=sys.argv,
                  python=sys.version,platform=platform.platform(),numpy=np.__version__,scipy=scipy.__version__,
                  pandas=pd.__version__,yaml=yaml.__version__, status='RUNNING',
                  scope='Synthetic K-slot local alternating responses; unknown global gaps',
                  source_hashes={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in
                                 [Path('src/core.py'),Path('src/game_solver.py'),Path(__file__),Path(args.config),Path('reports/P3_preregistration.md')]})
    write_json(out/'metadata.json',metadata)
    cases=[(11,'separated',1.2)] if args.pilot else [(s,c,b) for s in (11,22,33)
          for c in ('aligned','separated','business_cost') for b in (.6,1.2,1.8)]
    rows=[]
    for seed,scenario,budget in cases:
        case={**cfg,'seed':seed,'scenario':scenario,'B':budget}
        rows.extend(run_case(case,out/f'seed{seed}_{scenario}_B{budget}',
                             ['Joint-dynamic'] if args.pilot else METHODS))
        pd.DataFrame(rows).to_csv(out/'summary.csv',index=False)
    metadata.update(status='COMPLETED',seconds=time.perf_counter()-start)
    write_json(out/'metadata.json',metadata)


if __name__=='__main__':
    main()
