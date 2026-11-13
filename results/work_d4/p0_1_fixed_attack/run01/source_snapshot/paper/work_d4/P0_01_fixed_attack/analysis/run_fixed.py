"""D4-P0-1: new fixed-attack defense optimizations, immutable GAME baseline."""
from pathlib import Path
from dataclasses import asdict
from datetime import datetime, timezone
import argparse
import hashlib
import json
import platform
import shutil
import subprocess
import sys
import time
import traceback

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
import numpy as np
import pandas as pd
import scipy
from scipy.integrate import solve_ivp
import yaml
from src.core import simulate, check_controls
from src.game_solver import ResponseProblem, local_best_response
from src.experiments import initial_controls
from src.supplement_c2 import load_model, load_controls

PAPER = ROOT/'paper/work_d4/P0_01_fixed_attack'
REPORT = ROOT/'reports/work_d4'
CELLS = {'A':('equal','high_at_node2'),'B':('equal','high_at_node3'),
         'C':('unequal','high_at_node2'),'D':('unequal','high_at_node3')}
GROUPS = [(11,1.2)] + [(s,b) for s in (11,22,33) for b in (.6,1.2,1.8) if (s,b)!=(11,1.2)]
PARTS = ['security','business','isolation','recovery','terminal_defense',
         'attacker_value','attacker_effort','terminal_attacker']

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def dump(p,obj):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')

def now():
    return datetime.now(timezone.utc).isoformat()

def distance(u,v):
    return max(float(np.max(np.abs(u[j]-v[j]))) for j in (1,2))

def fixed_attack():
    a=np.zeros((6,6));a[:,:2]=.4
    return a

def fixed_starts(m,seed):
    uniform=initial_controls(m,6,'Uniform')
    rng=np.random.default_rng(seed+20261027)
    raw=[rng.uniform(0,1,(6,m.n)) for _ in range(3)]
    use=raw[1]@m.b_s+raw[2]@m.b_r
    for j in (1,2):
        raw[j]*=np.minimum(1,m.B/use)[:,None]
    starts=[(fixed_attack(),uniform[1],uniform[2]),
            (fixed_attack(),np.zeros((6,m.n)),np.zeros((6,m.n))),
            (fixed_attack(),raw[1],raw[2])]
    for u in starts:
        check_controls(m,*u)
        assert np.array_equal(u[0],fixed_attack())
    return starts

def response_audit(m,u,H,seed,starts):
    pr=ResponseProblem(m,*u,10.,H,'D','joint')
    base,grad=pr.value_gradient(pr.initial)
    v,raw=local_best_response(pr,seed,starts=starts,maxiter=300,ftol=1e-10)
    val,g=pr.value_gradient(v)
    signed=float(base-val)
    found=max(0.,signed)
    returned=pr.schedules(v)
    return returned,dict(H=H,seed=seed,starts=starts,incumbent_objective=base,
        returned_objective=val,signed_improvement=signed,improvement=found,
        relative_improvement=found/(1+abs(base)),
        incumbent_residual=pr.projected_residual(pr.initial,grad),
        response_residual=pr.projected_residual(v,g),violation=pr.violation(v),
        response_distance=distance(u,returned),all_starts_success=all(r['success'] for r in raw),raw=raw)

def optimize_path(m,u,H,seed,folder):
    folder.mkdir()
    dump(folder/'initial_controls.json',[x.tolist() for x in u])
    trace=[]
    for iteration in range(41):
        next_u,row=response_audit(m,u,H,seed+10*iteration,1)
        passed=bool(row['all_starts_success'] and row['relative_improvement']<=1e-7
                    and row['incumbent_residual']<=1e-4 and row['response_distance']<=1e-3
                    and row['violation']<=1e-10)
        row.update(iteration=iteration,passed=passed,controls=[v.tolist() for v in u])
        trace.append(row)
        with (folder/'trace.jsonl').open('a',encoding='utf-8') as f:
            f.write(json.dumps(row,ensure_ascii=False,allow_nan=False)+'\n')
        if passed or iteration==40 or not row['all_starts_success']:
            break
        u=next_u
    dump(folder/'controls.json',[x.tolist() for x in u])
    info=dict(passed=bool(trace[-1]['passed'] and all(t['all_starts_success'] for t in trace)),
              last=trace[-1],optimizer_calls=sum(len(t['raw']) for t in trace))
    dump(folder/'quality.json',info)
    return u,info

def sparse_audits(m,u,seed):
    rows=[]
    pr=ResponseProblem(m,*u,10.,12,'D')
    base=pr.value_gradient(pr.initial)[0]
    for channel in range(pr.width):
        v=np.zeros((6,pr.width));v[:,channel]=min(1.,pr.capacity/pr.weights[channel])
        start=pr.schedules(v.ravel())
        result,info=response_audit(m,start,12,seed+channel,1)
        info.update(channel=channel,improvement_against_primary=max(0.,base-info['returned_objective']),
                    relative_against_primary=max(0.,base-info['returned_objective'])/(1+abs(base)),
                    distance_against_primary=distance(u,result))
        rows.append(info)
    return rows

def independent_reference(m,u,H=192):
    """Independent scalar-index ODE/cost expressions, no core.dynamics/cost_rates."""
    y=np.r_[m.x0,np.zeros(6)]
    all_states=[m.x0.copy()];times=[0.]
    for k in range(6):
        a,s,r=(v[k] for v in u)
        def rhs(t,z):
            x=z[:m.n]
            dx=np.zeros(m.n)
            for i in range(m.n):
                incoming=sum(m.beta[j,i]*(1-m.epsilon[j]*s[j])*x[j] for j in range(m.n) if j!=i)
                dx[i]=(1-x[i])*(m.alpha[i]*a[i]+incoming)-(m.delta[i]+m.gamma[i]*r[i])*x[i]
            costs=np.array([sum(m.q[i]*x[i] for i in range(m.n)),
                            sum(m.h[i]*s[i] for i in range(m.n)),
                            .5*sum(m.c_s[i]*s[i]**2 for i in range(m.n)),
                            .5*sum(m.c_r[i]*r[i]**2 for i in range(m.n)),
                            sum(m.g[i]*x[i] for i in range(m.n)),
                            .5*sum(m.c_a[i]*a[i]**2 for i in range(m.n))])
            return np.r_[dx,costs]
        start,stop=k*10/6,(k+1)*10/6
        grid=np.linspace(start,stop,H+1)
        ans=solve_ivp(rhs,(start,stop),y,method='DOP853',rtol=1e-11,atol=1e-13,t_eval=grid)
        if not ans.success or not np.all(np.isfinite(ans.y)):
            raise RuntimeError('Independent integrator failed: '+ans.message)
        all_states.extend(ans.y[:m.n,1:].T);times.extend(grid[1:]);y=ans.y[:,-1]
    state=np.asarray(all_states)
    if state.min() < -1e-10 or state.max()>1+1e-10:
        raise FloatingPointError('Independent state outside domain')
    parts=dict(zip(['security','business','isolation','recovery','attacker_value','attacker_effort'],map(float,y[m.n:])))
    parts['terminal_defense']=float(m.omega@y[:m.n]);parts['terminal_attacker']=float(m.nu@y[:m.n])
    jd=sum(parts[k] for k in PARTS[:5]);ja=parts['attacker_value']-parts['attacker_effort']+parts['terminal_attacker']
    return dict(times=np.asarray(times),states=state,parts=parts,J_D=jd,J_A=ja)

def evaluate(m,u,folder):
    folder.mkdir()
    check_controls(m,*u)
    sims={H:simulate(m,*u,10.,H) for H in (12,24,48,96,192)}
    fine=sims[192];rows=[]
    for H,sim in sims.items():
        row=dict(H=H,J_D=sim['J_D'],J_A=sim['J_A'],**sim['parts'],
                 objective_error=max(abs(sim['J_D']-fine['J_D']),abs(sim['J_A']-fine['J_A'])),
                 component_error=max(abs(sim['parts'][p]-fine['parts'][p]) for p in PARTS),
                 state_error=float(np.max(np.abs(sim['states']-fine['states'][::192//H]))),
                 state_min=float(sim['states'].min()),state_max=float(sim['states'].max()))
        rows.append(row)
    pd.DataFrame(rows).to_csv(folder/'integration_refinement.csv',index=False)
    ref=independent_reference(m,u)
    independent=dict(J_D=ref['J_D'],J_A=ref['J_A'],parts=ref['parts'],
        objective_error=max(abs(ref['J_D']-fine['J_D']),abs(ref['J_A']-fine['J_A'])),
        component_error=max(abs(ref['parts'][p]-fine['parts'][p]) for p in PARTS),
        state_error=float(np.max(np.abs(ref['states']-fine['states']))),
        method='DOP853 with separate scalar-index RHS and costs',rtol=1e-11,atol=1e-13)
    dump(folder/'independent_integrator.json',independent)
    for H in (48,192):
        np.savez_compressed(folder/f'trajectory_H{H}.npz',times=sims[H]['times'],states=sims[H]['states'])
    np.savez_compressed(folder/'independent_trajectory.npz',times=ref['times'],states=ref['states'])
    pd.DataFrame([dict(t=t,node=i,x=float(x[i])) for t,x in zip(sims[48]['times'],sims[48]['states'])
                  for i in range(m.n)]).to_csv(folder/'states_H48.csv',index=False)
    dump(folder/'controls.json',[v.tolist() for v in u])
    budgets=[dict(slot=k,defense_use=float(u[1][k]@m.b_s+u[2][k]@m.b_r),
                  attack_use=float(u[0][k]@m.d_a),B=m.B,A=m.A) for k in range(6)]
    pd.DataFrame(budgets).to_csv(folder/'budgets.csv',index=False)
    quality=dict(integration_pass=all(max(r['objective_error'],r['component_error'],r['state_error'])<=1e-6 for r in rows),
                 independent_pass=max(independent['objective_error'],independent['component_error'],independent['state_error'])<=1e-6,
                 max_integration_error=max(max(r['objective_error'],r['component_error'],r['state_error']) for r in rows),
                 independent_max_error=max(independent['objective_error'],independent['component_error'],independent['state_error']))
    dump(folder/'quality.json',quality)
    dump(folder/'objectives.json',{str(H):dict(J_D=s['J_D'],J_A=s['J_A'],parts=s['parts']) for H,s in sims.items()})
    return sims,quality

def case_run(row,output):
    folder=output/row['case'];folder.mkdir()
    source=ROOT/row['model_source'];model=load_model(source)
    for leaf in ('model.json','config.yaml'):
        shutil.copyfile(source.parent/leaf,folder/leaf)
    game=load_controls(ROOT/row['game_source'])
    dump(folder/'sources.json',row)
    fixed_solutions=[];coarse=[];path_infos=[]
    for label,u in zip(('uniform','zero','random'),fixed_starts(model,row['seed'])):
        cu,ci=optimize_path(model,u,12,row['seed']+10000,folder/f'{label}_H12')
        fu,fi=optimize_path(model,cu,48,row['seed']+90000,folder/f'{label}_H48')
        fixed_solutions.append(fu);coarse.append(cu);path_infos.extend([ci,fi])
        print('PATH',row['case'],label,'pass',ci['passed'],fi['passed'],flush=True)
    fixed=fixed_solutions[0]
    _,coarse_audit=response_audit(model,coarse[0],12,row['seed']+80000,12)
    dump(folder/'coarse_12_start_audit.json',coarse_audit)
    sparse=sparse_audits(model,coarse[0],row['seed']+80000)
    dump(folder/'coarse_sparse_audits.json',sparse)
    _,fine_audit=response_audit(model,fixed,48,row['seed']+91000,3)
    dump(folder/'fine_3_start_audit.json',fine_audit)
    controls={'GAME':game,'FIXED':fixed,'CROSS':(fixed_attack(),game[1],game[2])}
    evaluations={};quality={}
    for label,u in controls.items():
        evaluations[label],quality[label]=evaluate(model,u,folder/label)
    coarse_stability=max(distance(coarse[i],coarse[j]) for i in range(3) for j in range(i))
    fine_stability=max(distance(fixed_solutions[i],fixed_solutions[j]) for i in range(3) for j in range(i))
    refinement=distance(coarse[0],fixed)
    raw=[r for p in path_infos for r in p['last']['raw']]
    # Every path records all iterations; include early exit failures as well.
    path_success=all(p['passed'] for p in path_infos)
    audits=[coarse_audit,fine_audit]+sparse
    audits_success=all(p['all_starts_success'] for p in audits)
    relative=max(coarse_audit['relative_improvement'],fine_audit['relative_improvement'],
                 *[p['relative_against_primary'] for p in sparse],*[p['last']['relative_improvement'] for p in path_infos])
    current_residual=max(p['last']['incumbent_residual'] for p in path_infos)
    response_dist=max(p['last']['response_distance'] for p in path_infos)
    check_controls(model,*fixed)
    violation=max(ResponseProblem(model,*fixed,10.,48,'D').violation(np.c_[fixed[1],fixed[2]].ravel()),
                  float(np.max(np.abs(fixed[0]-fixed_attack()))))
    old=json.loads((source.parent/'case_audit.json').read_text(encoding='utf-8'))
    baseline_error=abs(evaluations['GAME'][48]['J_D']-old['J_D'])
    conditions=dict(paths=path_success,audits=audits_success,relative=relative<=1e-7,
        residual=current_residual<=1e-4,response_distance=response_dist<=1e-3,
        coarse_initializations=coarse_stability<=1e-3,fine_initializations=fine_stability<=1e-3,
        control_refinement=refinement<=1e-3,feasibility=violation<=1e-10,
        baseline_replay=baseline_error<=1e-10,
        integration=all(q['integration_pass'] for q in quality.values()),
        independent=all(q['independent_pass'] for q in quality.values()))
    result={**{k:row[k] for k in ('case','cell','seed','B')},'status':'PASS' if all(conditions.values()) else 'INCONCLUSIVE',
        'numerical_pass':all(conditions.values()),'conditions':conditions,'relative_improvement_max':relative,
        'current_residual_max':current_residual,'response_distance_max':response_dist,
        'initialization_difference_H12':coarse_stability,'initialization_difference_H48':fine_stability,
        'integration_control_difference':refinement,'violation':violation,'GAME_baseline_replay_error':baseline_error,
        'max_integration_error':max(q['max_integration_error'] for q in quality.values()),
        'independent_max_error':max(q['independent_max_error'] for q in quality.values()),
        'D_GAME_FIXED_control_difference':distance(game,fixed),
        'global_certificate':False,'fixed_attack_optimization_new':True,
        'failed_conditions':[k for k,v in conditions.items() if not v]}
    dump(folder/'case_quality.json',result)
    cost_rows=[];ctrl_rows=[];state_rows=[]
    for label,u in controls.items():
        sim=evaluations[label][48]
        cost_rows.append(dict(case=row['case'],cell=row['cell'],seed=row['seed'],B=row['B'],evaluation=label,H=48,
                              J_D=sim['J_D'],J_A=sim['J_A'],**sim['parts']))
        for k in range(6):
            for i in range(6):
                ctrl_rows.append(dict(case=row['case'],cell=row['cell'],seed=row['seed'],B=row['B'],
                    evaluation=label,slot=k,node=i,a=u[0][k,i],s=u[1][k,i],r=u[2][k,i]))
        for i in range(6):
            state_rows.append(dict(case=row['case'],cell=row['cell'],seed=row['seed'],B=row['B'],evaluation=label,
                 node=i,terminal=sim['states'][-1,i],area_trapezoid_H48=np.trapz(sim['states'][:,i],sim['times'])))
    pd.DataFrame(cost_rows).to_csv(folder/'costs_H48.csv',index=False)
    pd.DataFrame(ctrl_rows).to_csv(folder/'controls.csv',index=False)
    pd.DataFrame(state_rows).to_csv(folder/'state_summary_H48.csv',index=False)
    dump(folder/'complete.json',result)
    print('CASE',row['case'],result['status'],'rel',relative,'res',current_residual,flush=True)
    return result

def protect_check(manifest):
    return [p for p,d in manifest.items() if not (ROOT/p).is_file() or sha(ROOT/p)!=d]

def selfcheck(row,out):
    m=load_model(ROOT/row['model_source']);u=fixed_starts(m,row['seed'])[0]
    pr=ResponseProblem(m,*u,10.,48,'D');v=pr.initial.copy();value,g=pr.value_gradient(v)
    tests=[]
    for index in (0,6,13):
        # Centered derivative along a capacity-neutral within-slot transfer.
        direction=np.zeros_like(v);slot=index//12;src=index%12;dst=(src+1)%12
        direction[slot*12+src]=-1;direction[slot*12+dst]=1
        eps=1e-6
        plus=pr.value_gradient(v+eps*direction)[0];minus=pr.value_gradient(v-eps*direction)[0]
        fd=(plus-minus)/(2*eps);analytic=float(g@direction)
        tests.append(dict(index=index,analytic=analytic,finite_difference=fd,error=abs(fd-analytic)))
    sim=simulate(m,*u,10.,192);ref=independent_reference(m,u)
    error=max(abs(sim['J_D']-ref['J_D']),abs(sim['J_A']-ref['J_A']),
              float(np.max(np.abs(sim['states']-ref['states']))))
    passed=bool(max(t['error'] for t in tests)<=1e-5 and error<=1e-6)
    dump(out/'interface_selfcheck.json',dict(passed=passed,gradient=tests,independent_error=error,
         fixed_attack_in_all_starts=all(np.array_equal(c[0],fixed_attack()) for c in fixed_starts(m,row['seed']))))
    if not passed:
        raise RuntimeError('Interface self-check failed')

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',default='results/work_d4/p0_1_fixed_attack/run01')
    parser.add_argument('--resume',action='store_true')
    args=parser.parse_args()
    out=ROOT/args.output
    config=json.loads((PAPER/'run_config.json').read_text(encoding='utf-8'))
    frozen=json.loads((PAPER/'frozen_inputs.json').read_text(encoding='utf-8'))
    changed=protect_check(frozen['protected_files'])
    if changed:
        raise RuntimeError('Protected inputs changed: '+repr(changed))
    binding={p.relative_to(ROOT).as_posix():sha(p) for p in [Path(__file__),PAPER/'protocol.md',PAPER/'run_config.json',PAPER/'design_matrix.csv',PAPER/'instruction_source.md']}
    if args.resume:
        meta=json.loads((out/'metadata.json').read_text(encoding='utf-8'))
        if meta['bindings']!=binding:
            raise RuntimeError('Resume bindings changed')
        if meta['status'] not in ('STOPPED_AT_GROUP_BOUNDARY_30MIN','RUNNING'):
            raise RuntimeError('Resume only permitted for time boundary or interrupted complete-case boundary')
    else:
        out.mkdir(parents=True,exist_ok=False)
        snapshot=out/'source_snapshot';snapshot.mkdir()
        paths=[ROOT/p for p in binding]+list((ROOT/'src').glob('*.py'))
        for p in paths:
            target=snapshot/p.relative_to(ROOT);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,target)
        for leaf in ('frozen_inputs.json','interface_audit.md'):
            shutil.copyfile(PAPER/leaf,snapshot/leaf)
        meta=dict(status='RUNNING',started_utc=now(),python=sys.version,platform=platform.platform(),
                  numpy=np.__version__,scipy=scipy.__version__,pandas=pd.__version__,yaml=yaml.__version__,
                  bindings=binding,segments=[],execution_scope='P0-1 only',global_certificate=False)
    segment=dict(started_utc=now(),command=sys.argv,completed_at_start=len(list(out.glob('*/complete.json'))))
    meta['segments'].append(segment);meta['status']='RUNNING';dump(out/'metadata.json',meta)
    rows=pd.read_csv(PAPER/'design_matrix.csv').to_dict('records')
    start=time.perf_counter()
    try:
        if not args.resume:
            selfcheck(next(r for r in rows if r['seed']==11 and r['B']==1.2 and r['cell']=='A'),out)
        all_results=[]
        for group_index,(seed,budget) in enumerate(GROUPS):
            group=[]
            for row in [r for r in rows if r['seed']==seed and r['B']==budget]:
                done=out/row['case']/'complete.json'
                if done.exists():
                    result=json.loads(done.read_text(encoding='utf-8'))
                else:
                    result=case_run(row,out)
                group.append(result);all_results.append(result)
                pd.DataFrame(all_results).drop(columns=['conditions']).to_csv(out/'case_quality_summary.csv',index=False)
                meta['completed_cases']=len(all_results);dump(out/'metadata.json',meta)
            passed=all(r['numerical_pass'] for r in group)
            dump(out/f'group_seed{seed}_B{budget}.json',dict(seed=seed,B=budget,passed=passed,cases=group))
            if group_index==0:
                dump(out/'pilot_gate.json',dict(passed=passed,decision='EXPANSION_ALLOWED' if passed else 'STOP_NO_EXPANSION',cases=group))
            if not passed:
                meta['status']='NUMERICAL_GATE_FAILED';break
            if time.perf_counter()-start>1800 and group_index<len(GROUPS)-1:
                meta['status']='STOPPED_AT_GROUP_BOUNDARY_30MIN';break
        else:
            meta['status']='COMPLETED'
    except Exception:
        meta['status']='EXECUTION_FAILED'
        (out/'exception.txt').write_text(traceback.format_exc(),encoding='utf-8')
        print(traceback.format_exc(),flush=True)
    segment.update(ended_utc=now(),seconds=time.perf_counter()-start,status=meta['status'])
    changed=protect_check(frozen['protected_files']);meta['protected_changes']=changed
    dump(out/'metadata.json',meta)
    print('RUN_STATUS',meta['status'],'cases',meta.get('completed_cases',0),'protected_changes',changed,flush=True)
    if meta['status'] in ('EXECUTION_FAILED','NUMERICAL_GATE_FAILED') or changed:
        raise SystemExit(1)

if __name__=='__main__':
    main()
