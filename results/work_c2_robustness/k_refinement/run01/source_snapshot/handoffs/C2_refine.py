"""Run the approved eight-case K refinement without modifying the historical solver."""
import hashlib
import json
import sys
from pathlib import Path
from dataclasses import asdict
import platform
import time
import numpy as np
import scipy
import yaml
from src.core import check_controls, simulate
from src.experiments import initial_controls, write_json
from src.diagnose_equilibrium import residuals, strong_audit
from src.matched_mechanism import matched_model, strict_solve, control_distance
from src.game_solver import ResponseProblem
from handoffs.C2_prepare import EXPECTED, ROOT, sha

CELLS = [('A','equal','high_at_node2'),('B','equal','high_at_node3'),
         ('C','unequal','high_at_node2'),('D','unequal','high_at_node3')]
GROUPS = [(11,.6),(33,1.2)]
OLD = Path('results/matched_mechanism/run01')

def controls(u):
    return [x.tolist() for x in u]

def compact(m,u,T,H,out):
    a = simulate(m,*u,T,H)
    b = simulate(m,*u,T,H*2)
    err = dict(objective=max(abs(a[p]-b[p]) for p in ('J_D','J_A')),
               parts=max(abs(a['parts'][p]-b['parts'][p]) for p in a['parts']),
               state=float(np.max(abs(a['states']-b['states'][::2]))))
    diag = {}
    for p in ('D','A'):
        pr = ResponseProblem(m,*u,T,H,p)
        diag[p] = pr.violation(pr.initial)
    write_json(out,dict(J_D=a['J_D'],J_A=a['J_A'],parts=a['parts'],errors=err,
                        violation=diag, residual=residuals(m,u,T,H),
                        times=a['times'].tolist(),states=a['states'].tolist(),
                        controls=controls(u),defense_use=(u[1]@m.b_s+u[2]@m.b_r).tolist(),
                        attack_use=(u[0]@m.d_a).tolist()))
    return a, err, diag

def audit_ok(audit):
    return (max(audit['strong_relative_D'],audit['strong_relative_A'])<=1e-7
            and all(r['success'] and r['violation']<=1e-10 for r in audit_records(audit)))

def audit_records(audit):
    return [r for p in ('D','A') for r in audit[p]['raw']]+[r for q in audit['sparse'] for r in q['raw']]

def case_run(out, seed,budget,letter,outgoing,value,base,design):
    start=time.perf_counter()
    out.mkdir()
    cfg={**base,'seed':seed,'B':budget}
    m=matched_model(cfg,design,outgoing,value)
    T=cfg['T']
    old=OLD/f'seed{seed}_B{budget}_{outgoing}_{value}'
    raw={k:v.tolist() if isinstance(v,np.ndarray) else v for k,v in asdict(m).items()}
    if raw!=json.loads((old/'model.json').read_text()):
        raise ValueError('Frozen model mismatch')
    u6=tuple(np.array(u) for u in json.loads((old/'fine/controls.json').read_text()))
    warm=tuple(np.repeat(u,2,axis=0) for u in u6)
    write_json(out/'inputs.json',dict(config={**cfg,'K':12,'rk4_substeps_per_slot':6},
         model=raw,cell=letter,outgoing=outgoing,value=value,history=str(old),
         hashes={str(p):sha(p) for p in (old/'model.json',old/'fine/controls.json',old/'fine_audit.json')},
         H_main=6,H_fine=24,H_check=48,solver_seed=seed+10000,random_seed=seed+20261027))
    check_controls(m,*warm)
    s6,_,_=compact(m,u6,T,48,out/'baseline.json')
    sw=simulate(m,*warm,T,24)
    embed=dict(objective=max(abs(sw[p]-s6[p]) for p in ('J_D','J_A')),
               state=float(np.max(abs(sw['states']-s6['states']))))
    write_json(out/'embedding.json',embed)
    if max(embed.values())>1e-12:
        raise ValueError('Copied control trajectory differs')
    uni=initial_controls(m,12,'Uniform')
    rng=np.random.default_rng(seed+20261027)
    rnd=[rng.uniform(0,1,(12,m.n)) for _ in range(3)]
    rnd[0][:,~m.entry]=0
    rnd[0]*=np.minimum(1,m.A/(rnd[0]@m.d_a))[:,None]
    use=rnd[1]@m.b_s+rnd[2]@m.b_r
    for j in (1,2):
        rnd[j]*=np.minimum(1,m.B/use)[:,None]
    final=[]; rows=[]
    for label,ini in [('warm',warm),('uniform',uni),('zero',tuple(np.zeros_like(u) for u in uni)),('random',tuple(rnd))]:
        p=out/label
        p.mkdir()
        check_controls(m,*ini)
        u,first=strict_solve(m,ini,T,6,seed+10000,p/'coarse')
        v,last=strict_solve(m,u,T,24,seed+90000,p/'fine')
        sim,err,violation=compact(m,v,T,24,p/'evaluation.json')
        audit=strong_audit(m,v,T,24,seed+80000,p,'deviation')
        path_raw=[r for stage in ('coarse','fine') for line in (p/stage/'trace.jsonl').read_text().splitlines()
                  for row in [json.loads(line)] for player in ('D','A','sequential_attack')
                  for r in row.get(player,{}).get('raw',[])]
        refine=control_distance(u,v)
        ok=bool(first['passed'] and last['passed'] and audit_ok(audit) and refine<=1e-3
                and max(err.values())<=1e-6 and max(violation.values())<=1e-10
                and all(r['success'] for r in path_raw))
        rows.append(dict(path=label,passed=ok,J_D=sim['J_D'],J_A=sim['J_A'],
                         gap_D=max(0.,audit['strong_raw_improvement_D']),gap_A=max(0.,audit['strong_raw_improvement_A']),
                         relative_D=max(0.,audit['strong_relative_D']),relative_A=max(0.,audit['strong_relative_A']),
                         residual_D=last['incumbent_residual']['D'],residual_A=last['incumbent_residual']['A'],
                         errors=err,violation=max(violation.values()),refine_distance=refine,
                         optimizer_calls=len(path_raw)+len(audit_records(audit)),
                         optimizer_failures=sum(not r['success'] for r in path_raw+audit_records(audit))))
        write_json(p/'quality.json',rows[-1])
        final.append(v)
    cross=strong_audit(m,warm,T,24,seed+80000,out,'cross_class_deviation')
    cross_success=all(r['success'] and r['violation']<=1e-10 for r in audit_records(cross))
    stable=max(control_distance(x,y) for j,x in enumerate(final) for y in final[:j])
    cross_eval=dict(D12_A6=simulate(m,warm[0],*final[0][1:],T,24)['J_D'],
                    D6_A12=simulate(m,final[0][0],*warm[1:],T,24)['J_D'],
                    attack_distance=float(np.max(abs(warm[0]-final[0][0]))))
    write_json(out/'cross_evaluation.json',cross_eval)
    result=dict(seed=seed,B=budget,cell=letter,case=out.name,paths=rows,stable_distance=stable,
                cross_success=cross_success,passed=bool(all(r['passed'] for r in rows) and stable<=1e-3 and cross_success),
                cross={p:dict(signed=cross[f'strong_raw_improvement_{p}'],
                              improvement=max(0.,cross[f'strong_raw_improvement_{p}']),
                              relative=max(0.,cross[f'strong_relative_{p}'])) for p in ('D','A')},
                seconds=time.perf_counter()-start)
    write_json(out/'case.json',result)
    print('CASE',out.name,result['passed'],flush=True)
    return result

def main():
    if any(sha(p)!=h for p,h in EXPECTED.items()):
        raise RuntimeError('C1 version mismatch')
    if '批准 G1-Work-C2，按登记协议执行' not in Path('reviews/APPROVAL_LOG.md').read_text(encoding='utf-8'):
        raise RuntimeError('Approval missing')
    out=ROOT/'k_refinement'/sys.argv[1]
    out.mkdir(exist_ok=False)
    base=yaml.safe_load(Path('configs/base.yaml').read_text(encoding='utf-8'))
    design=yaml.safe_load(Path('configs/proposed_mechanism_identification.yaml').read_text(encoding='utf-8'))
    paths=[*Path('src').glob('*.py'),Path(__file__),Path('handoffs/C2_prepare.py'),*map(Path,[
           'configs/base.yaml','configs/proposed_mechanism_identification.yaml','reports/WORK_C2_ROBUSTNESS_PROTOCOL.md'])]
    for p in paths:
        dest=out/'source_snapshot'/p.relative_to(Path.cwd()) if p.is_absolute() else out/'source_snapshot'/p
        dest.parent.mkdir(parents=True,exist_ok=True)
        dest.write_bytes(p.read_bytes())
    meta=dict(status='RUNNING',command=[sys.executable,'-m','handoffs.C2_refine',sys.argv[1]],
              python=sys.version,numpy=np.__version__,scipy=scipy.__version__,platform=platform.platform(),
              source_hashes={str(p):sha(p) for p in paths},cases=[])
    write_json(out/'metadata.json',meta)
    try:
        for seed,budget in GROUPS:
            group=[]
            for letter,outgoing,value in CELLS:
                result=case_run(out/f'seed{seed}_B{budget}_{letter}',seed,budget,letter,outgoing,value,base,design)
                group.append(result)
                meta['cases'].append(result)
                write_json(out/'metadata.json',meta)
            if not all(row['passed'] for row in group):
                meta['status']='STOPPED_QUALITY_GATE'
                break
        else:
            meta['status']='COMPLETED'
    except Exception as e:
        meta.update(status='FAILED',error=repr(e))
        raise
    finally:
        write_json(out/'metadata.json',meta)

if __name__=='__main__':
    main()
