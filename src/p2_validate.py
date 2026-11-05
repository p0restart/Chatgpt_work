"""Reproducible pre-G1 feasibility run. Refuses to overwrite an existing run."""
import argparse
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
import hashlib
import json
import platform
import sys
import time
import numpy as np
import pandas as pd
import scipy
import yaml
from .core import synthetic_model_from_config, simulate, check_controls
from .game_solver import ResponseProblem, local_best_response


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', default='configs/p2.yaml')
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    outdir = Path(args.output)
    outdir.mkdir(parents=True, exist_ok=False)
    t0 = time.perf_counter()
    cfg = yaml.safe_load(Path(args.config).read_text(encoding='utf-8'))
    p = cfg['p2']
    m = synthetic_model_from_config(cfg)
    K, T, steps = cfg['K'], cfg['T'], cfg['rk4_substeps_per_slot']
    a = np.zeros((K, m.n)); a[:, m.entry] = p['fixed_attack_each_entry']
    s = np.full_like(a, p['fixed_isolation_each_node'])
    r = np.full_like(a, p['fixed_recovery_each_node'])
    check_controls(m, a, s, r)
    (outdir/'config.yaml').write_text(yaml.safe_dump(cfg, sort_keys=False), encoding='utf-8')
    md = {k: v.tolist() if isinstance(v, np.ndarray) else v for k, v in asdict(m).items()}
    (outdir/'model.json').write_text(json.dumps(md, indent=2), encoding='utf-8')
    edges = [{'source':j,'target':i,'beta':m.beta[j,i]} for j,i in zip(*np.nonzero(m.beta))]
    pd.DataFrame(edges).to_csv(outdir/'edges.csv', index=False)
    summaries, traces, controls, trajectories, refinements, gradients, slots = [], [], [], [], [], [], []
    base = simulate(m,a,s,r,T,steps)
    for player in ('D','A'):
        pr = ResponseProblem(m,a,s,r,T,steps,player)
        v, trace = local_best_response(pr, cfg['seed'],p['starts'],p['maxiter'],p['ftol'])
        # Save raw starts immediately, including unsuccessful optimization exits.
        (outdir/f'{player}_raw_solver.json').write_text(json.dumps(trace,indent=2),encoding='utf-8')
        aa, ss, rr = pr.schedules(v)
        check_controls(m,aa,ss,rr)
        sim = simulate(m,aa,ss,rr,T,steps)
        val, grad = pr.value_gradient(v)
        expected = sim['J_D'] if player=='D' else -sim['J_A']
        interior = .5*(pr.initial+v)
        _, analytic = pr.value_gradient(interior)
        for eps in p['gradient_steps']:
            fd = np.zeros_like(v)
            for j in range(v.size):
                delta = np.zeros_like(v); delta[j]=eps
                fd[j]=(pr.value_gradient(interior+delta)[0]-pr.value_gradient(interior-delta)[0])/(2*eps)
            gradients.append(dict(player=player,epsilon=eps,max_abs_error=float(np.max(np.abs(fd-analytic)))))
        sims = {st:simulate(m,aa,ss,rr,T,st) for st in p['refinement_substeps']}
        finest = sims[max(sims)]
        for st, fine in sims.items():
            refinements.append(dict(player=player,substeps=st,dt=T/K/st,J_D=fine['J_D'],J_A=fine['J_A'],
                                    error_J_D=abs(fine['J_D']-finest['J_D']),error_J_A=abs(fine['J_A']-finest['J_A']),
                                    terminal_state_error=float(np.max(np.abs(fine['states'][-1]-finest['states'][-1]))),
                                    max_cost_component_error=max(abs(fine['parts'][key]-finest['parts'][key]) for key in fine['parts'])))
        # Refine optimization as well as integrate the same controls more accurately.
        finepr = ResponseProblem(m,aa,ss,rr,T,24,player)
        fv, ftrace = local_best_response(finepr,cfg['seed'],1,p['maxiter'],p['ftol'])
        (outdir/f'{player}_refined_solver.json').write_text(json.dumps(ftrace,indent=2),encoding='utf-8')
        for row in trace:
            traces.append({'player':player,**{k:v for k,v in row.items() if k not in ('control','initial_control')}})
        for k in range(K):
            slots.append(dict(player=player,slot=k,defense_use=float(ss[k]@m.b_s+rr[k]@m.b_r),attack_use=float(aa[k]@m.d_a),
                              defense_slack=float(m.B-ss[k]@m.b_s-rr[k]@m.b_r),attack_slack=float(m.A-aa[k]@m.d_a)))
            for i in range(m.n):
                controls.append(dict(player=player,slot=k,node=i,a=aa[k,i],s=ss[k,i],r=rr[k,i]))
        for t,x in zip(sim['times'],sim['states']):
            for i in range(m.n):
                trajectories.append(dict(player=player,t=t,node=i,x=x[i]))
        improvement = base['J_D']-sim['J_D'] if player=='D' else sim['J_A']-base['J_A']
        summaries.append(dict(player=player,label='FIXED_OPPONENT_LOCAL_RESPONSE_NOT_EQUILIBRIUM',
                              initial_J_D=base['J_D'],initial_J_A=base['J_A'],J_D=sim['J_D'],J_A=sim['J_A'],
                              observed_improvement=improvement,violation=pr.violation(v),
                              projected_residual=pr.projected_residual(v,grad),
                              multistart_objective_spread=float(np.ptp([z['objective'] for z in trace])),
                              all_starts_success=all(z['success'] for z in trace),
                              objective_implementation_error=abs(val-expected),
                              refined_reoptimization_improvement=finepr.value_gradient(v)[0]-finepr.value_gradient(fv)[0],
                              refined_control_max_change=float(np.max(np.abs(v-fv))),
                              state_min=float(sim['states'].min()),state_max=float(sim['states'].max()),**sim['parts']))
        print(json.dumps(summaries[-1]),flush=True)
    for name,rows in [('summary',summaries),('solver_trace',traces),('controls',controls),('trajectories',trajectories),
                      ('rk4_refinement',refinements),('gradient_check',gradients),('slot_budgets',slots)]:
        pd.DataFrame(rows).to_csv(outdir/f'{name}.csv',index=False)
    checks = dict(all_starts_success=all(row['all_starts_success'] for row in summaries),
                  feasible=all(row['violation']<=p['feasibility_tolerance'] for row in summaries),
                  nonworsening=all(row['observed_improvement']>=-1e-9 for row in summaries),
                  residual=all(row['projected_residual']<=p['projected_residual_tolerance'] for row in summaries),
                  multistart=all(row['multistart_objective_spread']<=p['multistart_objective_spread_tolerance'] for row in summaries),
                  derivatives=all(row['max_abs_error']<=p['derivative_tolerance'] for row in gradients),
                  refinement=all(max(row['error_J_D'],row['error_J_A'])<=p['refinement_objective_tolerance'] for row in refinements if row['substeps']>=12))
    metadata=dict(command=' '.join(sys.argv),timestamp=datetime.now().astimezone().isoformat(),seconds=time.perf_counter()-t0,
                  python=sys.version,platform=platform.platform(),numpy=np.__version__,scipy=scipy.__version__,
                  seed=cfg['seed'],checks=checks,full_gap_computed=False,global_optimum_certified=False,
                  source_hashes={str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(Path('src').glob('*.py'))})
    (outdir/'metadata.json').write_text(json.dumps(metadata,indent=2),encoding='utf-8')
    print(json.dumps(metadata),flush=True)
    if not all(checks.values()):
        raise SystemExit('P2 diagnostic failed; preserve results and report at G1')


if __name__=='__main__':
    main()
