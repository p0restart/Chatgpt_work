"""G1-C1 matched synthetic experiment; local diagnostics, no global certificate."""
import argparse
from dataclasses import asdict, replace
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

from .core import synthetic_model_from_config, validate_model, simulate, check_controls
from .game_solver import ResponseProblem, observed_gaps, response
from .experiments import write_json, initial_controls, save_evaluation
from .diagnose_equilibrium import residuals, strong_audit, mechanism


def matched_model(cfg, design, outgoing, value):
    m = synthetic_model_from_config(cfg)
    beta = np.zeros((m.n, m.n))
    rng = np.random.default_rng(cfg['seed'])
    for edge in design['network']['incoming']:
        beta[edge['source'], edge['targets']] = rng.uniform(*edge['seed_weight_range'])
    weights = design['network']['outgoing_conditions'][outgoing]
    for node in design['matched_source_nodes']:
        beta[node, design['downstream_nodes']] = weights[f'node{node}_to_each_downstream']
    m = replace(m, beta=beta, q=np.array(design['value_conditions'][value]['q'], dtype=float),
                h=np.array(design['h'], dtype=float), x0=np.array(design['x0'], dtype=float))
    validate_model(m)
    return m


def control_distance(a, b):
    return max(float(np.max(np.abs(x-y))) for x,y in zip(a,b))


def strict_solve(m, u, T, steps, seed, out):
    out.mkdir()
    for iteration in range(41):
        gap, d, a = observed_gaps(m, u, T, steps, seed+10*iteration, starts=1)
        res = residuals(m,u,T,steps)
        distance = max(float(np.max(np.abs(d[j]-u[j]))) for j in (1,2))
        distance = max(distance, float(np.max(np.abs(a[0]-u[0]))))
        passed = (max(gap['relative_D'],gap['relative_A']) <= 1e-7
                  and max(res.values()) <= 1e-4 and distance <= 1e-3
                  and all(gap[p]['all_starts_success'] for p in ('D','A')))
        row = dict(iteration=iteration, **gap, incumbent_residual=res,
                   response_distance=distance, passed=passed, controls=[x.tolist() for x in u])
        if not passed and iteration < 40:
            next_u, attack_info = response(m, (u[0],d[1],d[2]), T, steps, 'A',seed+10*iteration+2,1)
            row['sequential_attack'] = attack_info
        with (out/'trace.jsonl').open('a', encoding='utf-8') as f:
            f.write(json.dumps(row)+'\n')
        print(out.parent.name, out.name, iteration, f"gap={max(gap['relative_D'],gap['relative_A']):.3g}", flush=True)
        if passed or iteration == 40:
            break
        u = next_u
    write_json(out/'controls.json',[x.tolist() for x in u])
    write_json(out/'last.json',row)
    return u,row


def source_transfers(m,u,T,steps,out):
    """All feasible ordered transfers among s2,s3,r2,r3, at fixed attack."""
    pr = ResponseProblem(m,*u,T,steps,'D')
    base,g = pr.value_gradient(pr.initial)
    v = pr.initial.reshape(pr.K,pr.width)
    g = g.reshape(v.shape)
    rows=[]
    for k in range(pr.K):
        for src in (2,3,m.n+2,m.n+3):
            for dst in (2,3,m.n+2,m.n+3):
                if src == dst:
                    continue
                step = min(1e-5,.1*v[k,src]*pr.weights[src],.1*(1-v[k,dst])*pr.weights[dst])
                analytic = -g[k,src]/pr.weights[src]+g[k,dst]/pr.weights[dst]
                row=dict(slot=k,source=src,destination=dst,analytic=analytic,
                         feasible=bool(step>=1e-10),capacity_step=max(0.,step))
                if step>=1e-10:
                    w=v.copy();w[k,src]-=step/pr.weights[src];w[k,dst]+=step/pr.weights[dst]
                    val,_=pr.value_gradient(w.ravel())
                    row.update(finite_difference=(val-base)/step,
                               error=abs((val-base)/step-analytic),violation=pr.violation(w.ravel()))
                rows.append(row)
    pd.DataFrame(rows).to_csv(out/'source_transfers.csv',index=False)


def run_case(cfg, design, outgoing, value, out):
    out.mkdir()
    m=matched_model(cfg,design,outgoing,value)
    T,K,steps=cfg['T'],cfg['K'],cfg['rk4_substeps_per_slot']
    (out/'config.yaml').write_text(yaml.safe_dump(dict(base=cfg,design=design,outgoing=outgoing,value=value),sort_keys=False),encoding='utf-8')
    write_json(out/'model.json',{k:v.tolist() if isinstance(v,np.ndarray) else v for k,v in asdict(m).items()})
    pd.DataFrame([dict(source=j,target=i,beta=m.beta[j,i]) for j,i in zip(*np.nonzero(m.beta))]).to_csv(out/'edges.csv',index=False)
    uniform=initial_controls(m,K,'Uniform')
    rng=np.random.default_rng(cfg['seed']+20261027)
    random=[rng.uniform(0,1,(K,m.n)) for _ in range(3)]
    random[0][:,~m.entry]=0
    random[0]*=np.minimum(1,m.A/(random[0]@m.d_a))[:,None]
    use=random[1]@m.b_s+random[2]@m.b_r
    for j in (1,2):
        random[j]*=np.minimum(1,m.B/use)[:,None]
    solutions=[]; last_rows=[]
    for label,initial in [('uniform',uniform),('zero',tuple(np.zeros_like(x) for x in uniform)),('random',tuple(random))]:
        check_controls(m,*initial)
        u,last=strict_solve(m,initial,T,steps,cfg['seed']+10000,out/label)
        solutions.append(u);last_rows.append(last)
        save_evaluation(out/f'{label}_evaluation',m,cfg,u,'Joint-dynamic',label)
    stable=max(control_distance(solutions[i],solutions[j]) for i in range(3) for j in range(i))
    u=solutions[0]
    audit=strong_audit(m,u,T,steps,cfg['seed']+80000,out,'strong_audit')
    fine_u,fine_last=strict_solve(m,u,T,48,cfg['seed']+90000,out/'fine')
    fine_gap,_,fine_attack=observed_gaps(m,fine_u,T,48,cfg['seed']+91000,starts=3)
    write_json(out/'fine_audit.json',fine_gap)
    save_evaluation(out/'fine_evaluation',m,{**cfg,'rk4_substeps_per_slot':12},fine_u,'Joint-dynamic','fine_optimized')
    mechanism(m,fine_u,T,48,out)
    source_transfers(m,fine_u,T,48,out)
    fixed=simulate(m,uniform[0],fine_u[1],fine_u[2],T,48)
    adaptive=simulate(m,*fine_attack,T,48)
    write_json(out/'attack_evaluation.json',dict(
        fixed_attack_controls=uniform[0].tolist(),
        fixed_attack_J_D=fixed['J_D'],
        strict_response_attack_controls=fine_attack[0].tolist(),
        strict_response_attack_J_D=adaptive['J_D'],
        defense_held_fixed=True, label='Same final defense, common fixed attack versus local attack response'))
    strong_success=all(audit[p]['all_starts_success'] for p in ('D','A')) and all(
        raw['success'] for item in audit['sparse'] for raw in item['raw'])
    all_res=[raw['projected_residual'] for p in ('D','A') for raw in audit[p]['raw']]
    all_res += [raw['projected_residual'] for item in audit['sparse'] for raw in item['raw']]
    relative=max(audit['strong_relative_D'],audit['strong_relative_A'],
                 fine_gap['relative_D'],fine_gap['relative_A'],
                 *[row[p] for row in last_rows for p in ('relative_D','relative_A')])
    max_res=max(*[max(row['incumbent_residual'].values()) for row in last_rows],
                max(fine_last['incumbent_residual'].values()))
    refinement=control_distance(u,fine_u)
    numerical_pass=(all(row['passed'] for row in last_rows) and fine_last['passed']
                    and strong_success and all(fine_gap[p]['all_starts_success'] for p in ('D','A'))
                    and relative<=1e-7 and max_res<=1e-4 and stable<=1e-3 and refinement<=1e-3)
    result=dict(case=out.name,seed=cfg['seed'],B=m.B,outgoing=outgoing,value=value,
                numerical_pass=bool(numerical_pass),relative_max=relative,incumbent_residual_max=max_res,
                initialization_control_difference=stable,integration_control_difference=refinement,
                strong_starts_success=strong_success,strong_start_residual_max=max(all_res),
                fixed_attack_J_D=fixed['J_D'],strict_response_attack_J_D=adaptive['J_D'],
                J_D=fine_gap['J_D'],J_A=fine_gap['J_A'],global_certificate=False)
    write_json(out/'case_audit.json',result)
    return result


def summarize(out, rows):
    pd.DataFrame(rows).to_csv(out/'summary.csv',index=False)
    effects=[]
    for seed,budget in sorted(set((r['seed'],r['B']) for r in rows)):
        group=[r for r in rows if r['seed']==seed and r['B']==budget]
        if len(group)!=4:
            continue
        lookup={(r['outgoing'],r['value']):r for r in group}
        for initialization in ('uniform','zero','random','fine'):
            u={key:tuple(np.array(x) for x in json.loads((out/r['case']/initialization/'controls.json').read_text())) for key,r in lookup.items()}
            for window,sl in [('all',slice(0,6)),('first4',slice(0,4)),('last2',slice(4,6))]:
                for kind,index in [('s',1),('r',2)]:
                    for node in (2,3):
                        eq=(u['equal','high_at_node3'][index]-u['equal','high_at_node2'][index])[sl,node]
                        neq=(u['unequal','high_at_node3'][index]-u['unequal','high_at_node2'][index])[sl,node]
                        did=neq-eq
                        effects.append(dict(seed=seed,B=budget,initialization=initialization,window=window,
                                            kind=kind,node=node,equal_value_effect=float(eq.mean()),
                                            unequal_value_effect=float(neq.mean()),interaction=float(did.mean()),
                                            integrated_interaction=float(did.sum()*10/6),
                                            exceeds_resolution=bool(abs(did.mean())>1e-3),
                                            numerical_pass=all(r['numerical_pass'] for r in group)))
    pd.DataFrame(effects).to_csv(out/'paired_effects.csv',index=False)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',required=True)
    parser.add_argument('--pilot-only',action='store_true')
    args=parser.parse_args()
    design_path=Path('configs/proposed_mechanism_identification.yaml')
    design=yaml.safe_load(design_path.read_text(encoding='utf-8'))
    if design['status']!='APPROVED_2026_10_27':
        raise ValueError('G1-C1 approval missing')
    base=yaml.safe_load(Path(design['base_config']).read_text(encoding='utf-8'))
    out=Path(args.output);out.mkdir(parents=True,exist_ok=False)
    paths=[Path(__file__),Path('src/core.py'),Path('src/game_solver.py'),Path('src/experiments.py'),
           Path('src/diagnose_equilibrium.py'),design_path,Path(design['base_config']),
           Path('reports/MATCHED_MECHANISM_PROTOCOL.md')]
    snapshot=out/'source_snapshot';snapshot.mkdir()
    for p in paths:
        target=snapshot/p.name;target.write_bytes(p.read_bytes())
    meta=dict(status='RUNNING_PILOT',command=sys.argv,started_at=datetime.now(timezone.utc).isoformat(),
              python=sys.version,platform=platform.platform(),numpy=np.__version__,scipy=scipy.__version__,
              pandas=pd.__version__,yaml=yaml.__version__,global_certificate=False,
              source_hashes={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths})
    write_json(out/'metadata.json',meta)
    start=time.perf_counter();rows=[]
    groups=[(11,1.2)]+[(s,b) for s in design['seeds'] for b in design['B_values'] if (s,b)!=(11,1.2)]
    if args.pilot_only:
        groups=groups[:1]
    for group_index,(seed,budget) in enumerate(groups):
        group=[]
        for outgoing in ('equal','unequal'):
            for value in ('high_at_node2','high_at_node3'):
                cfg={**base,'seed':seed,'B':budget}
                row=run_case(cfg,design,outgoing,value,out/f'seed{seed}_B{budget}_{outgoing}_{value}')
                group.append(row);rows.append(row);summarize(out,rows)
        passed=all(row['numerical_pass'] for row in group)
        if group_index==0:
            write_json(out/'pilot_gate.json',dict(passed=passed,cases=group,
                       decision='EXPANSION_ALLOWED' if passed else 'STOP_NO_EXPANSION'))
        meta.update(completed_cases=len(rows),seconds=time.perf_counter()-start)
        if not passed:
            meta['status']='NUMERICAL_GATE_FAILED';break
        if time.perf_counter()-start>1800 and group_index<len(groups)-1:
            meta['status']='STOPPED_AT_GROUP_BOUNDARY_30MIN';break
        meta['status']='RUNNING_EXPANSION'
        write_json(out/'metadata.json',meta)
    else:
        meta['status']='COMPLETED'
    write_json(out/'metadata.json',meta)
    print(json.dumps(meta),flush=True)


if __name__=='__main__':
    main()
