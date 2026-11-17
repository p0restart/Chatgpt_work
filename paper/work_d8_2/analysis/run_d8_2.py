"""D8-2 adapters only. Frozen D7 model and solvers are imported unchanged."""
from pathlib import Path
import sys, json, hashlib, platform, time, argparse, shutil, os
from datetime import datetime, timezone, timedelta
from dataclasses import replace
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
import numpy as np
import pandas as pd
import scipy
from src import game_solver as gs
from src.core import simulate, check_controls, validate_model
from src.experiments import initial_controls, write_json
from src.matched_mechanism import strict_solve, control_distance
from src.supplement_c2 import load_model, load_controls, dump_model
from paper.work_d5.analysis.run_replanning import Run, random_pair, execute, objective, PARTS

BASE = Path(os.environ.get('D8_2_OUTPUT', str(ROOT/'paper/work_d8_2'))).resolve()
D7 = ROOT/'paper/work_d7'
STATIC = D7/'results/static/B1.2'
ROLL = D7/'results/rolling_event_B1.2'
SEED = 20261115
T, K, H = 10., 12, 24
NAMES = {'attempts':'optimizer_attempts','audit':'solver_audit','timing':'timing',
    'plans':'planned_controls','executed':'executed_controls','trajectories':'trajectories',
    'objectives':'objectives','comparisons':'comparisons','attacks':'attack_scenarios',
    'quality':'quality','tasks':'tasks'}

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def now(): return datetime.now(timezone(timedelta(hours=8))).isoformat()
def csv(p, rows): pd.DataFrame(rows).to_csv(p,index=False,encoding='utf-8-sig')
def manifest():
    rows=[dict(path=p.relative_to(BASE).as_posix(),bytes=p.stat().st_size,sha256=sha(p))
        for p in sorted(BASE.rglob('*')) if p.is_file() and p.name not in
        ('data_manifest.csv','SHA256SUMS') and '__pycache__' not in p.parts
        and p.suffix not in ('.part',)]
    csv(BASE/'data_manifest.csv',rows)
    rows.append(dict(path='data_manifest.csv',sha256=sha(BASE/'data_manifest.csv')))
    (BASE/'SHA256SUMS').write_text(''.join(f"{r['sha256']}  {r['path']}\n" for r in rows),encoding='utf-8')
def gate(n, passed, **kw):
    write_json(BASE/f'checkpoints/gate{n}.json',dict(gate=n,completed_at=now(),passed=bool(passed),**kw))
    manifest()
def restore_run(out, cls=Run):
    out.mkdir(parents=True,exist_ok=True)
    run=cls(out)
    for attr,name in NAMES.items():
        p=out/f'{name}.csv'
        if p.exists(): setattr(run,attr,pd.read_csv(p).to_dict('records'))
    return run

class K12Run(Run):
    """D5 orchestration with explicit T/K and matched H; no core modifications."""
    def plan_rows(self,u,label,j,selected=False):
        dt=T/len(u[0])
        for k in range(len(u[0])):
            for node in range(len(u[0][k])):
                self.plans.append(dict(self.context,path=label,selected=selected,
                    absolute_slot=k,t_start=k*dt,t_end=(k+1)*dt,node=node,
                    a_plan=u[0][k,node],s_plan=u[1][k,node],r_plan=u[2][k,node]))

    def game(self,m,warm,seed,folder,j=-3):
        start=time.perf_counter(); index=len(self.attempts)
        solutions=[]; lasts=[]
        initials=[warm,tuple(np.zeros_like(x) for x in warm),random_pair(m,len(warm[0]),seed+2)]
        for p,(label,initial) in enumerate(zip(('uniform','zero','random'),initials)):
            self.context.update(phase='offline_planning',path=label)
            write_json(folder/f'initial_{label}.json',dict(seed=seed+p,controls=[x.tolist() for x in initial]))
            sol,last=strict_solve(m,initial,T,H,seed+p,folder/label)
            solutions.append(sol); lasts.append(last)
            self.plan_rows(sol,label,j,label=='uniform')
            for player in ('D','A'):
                self.audit.append(dict(**self.context,audit='strict_path_final',player=player,H=H,
                    signed_improvement=last[f'signed_gap_{player}'],discovered_improvement=last[f'gap_{player}'],
                    relative_improvement=last[f'relative_{player}'],incumbent_residual=last['incumbent_residual'][player],
                    response_distance=last['response_distance'],passed=last['passed']))
            self.save()
        spread=max(control_distance(solutions[0],v) for v in solutions[1:])
        self.context.update(phase='offline_planning',path='uniform_validation')
        passed=self.pair_audit(m,solutions[0],T,H,seed,'H24_multistart')
        seconds=time.perf_counter()-start
        success=all(r['success'] for r in self.attempts[index:])
        passed=bool(passed and all(x['passed'] for x in lasts) and spread<=1e-3 and success)
        self.timing.append(dict(**self.context,item='replanning_total',seconds=seconds,note='nested responses included; H48 audit excluded'))
        self.quality.append(dict(**self.context,check='three_path_control_spread',value=spread,threshold=1e-3,passed=spread<=1e-3))
        self.context.update(phase='extra_audit',path='uniform')
        ts=time.perf_counter()
        fine=self.pair_audit(m,solutions[0],T,2*H,seed,'H48_fixed_candidate')
        self.timing.append(dict(**self.context,item='precision_audit_total',seconds=time.perf_counter()-ts))
        write_json(folder/'decision.json',dict(passed=bool(passed and fine),online_seconds=seconds,
            spread=spread,all_optimizer_calls_success=success and all(r['success'] for r in self.attempts[index:]),
            selected_path='uniform',x0=m.x0.tolist(),K=len(warm[0]),T=T,H=H,seed=seed))
        return solutions[0],bool(passed and fine)

    def unilateral(self,m,u,player,seed,folder,j=-3,strong=False):
        start=time.perf_counter(); first=len(self.attempts)
        self.context.update(phase='attack_generation' if strong else 'offline_planning',path='multistart')
        pr=gs.ResponseProblem(m,*u,T,H,player)
        v,raw=gs.local_best_response(pr,seed=seed+2,starts=3)
        candidate=pr.schedules(v); original=candidate
        for p,row in enumerate(raw):
            self.plan_rows(pr.schedules(np.array(row['control'])),['warm','zero','random'][p],j)
        if strong:
            for iteration in range(41):
                pp=gs.ResponseProblem(m,*candidate,T,H,player)
                best,raw12=gs.local_best_response(pp,seed+100+iteration,starts=12)
                best_value=pp.value_gradient(best)[0]
                for channel in range(pp.width):
                    z=np.zeros((pp.K,pp.width)); z[:,channel]=min(1,pp.capacity/pp.weights[channel])
                    sp=gs.ResponseProblem(m,*pp.schedules(z.ravel()),T,H,player)
                    sv,_=gs.local_best_response(sp,seed+200+10*iteration+channel,starts=1)
                    value=sp.value_gradient(sv)[0]
                    if value<best_value: best_value,best=value,sv
                base,grad=pp.value_gradient(pp.initial)
                res=pp.projected_residual(pp.initial,grad)
                signed=base-best_value; distance=float(np.max(abs(best-pp.initial)))
                ok=bool(max(0,signed)/(1+abs(base))<=1e-7 and res<=1e-4 and distance<=1e-3)
                self.audit.append(dict(**self.context,audit='12start_sparse',player=player,H=H,iteration=iteration,
                    signed_improvement=signed,discovered_improvement=max(0,signed),relative_improvement=max(0,signed)/(1+abs(base)),
                    incumbent_residual=res,response_distance=distance,passed=ok))
                write_json(folder/f'strong_{iteration:02d}.json',dict(current=[x.tolist() for x in candidate],returned=[x.tolist() for x in pp.schedules(best)],raw12=raw12,passed=ok))
                self.save()
                if ok or iteration==40: break
                candidate=pp.schedules(best)
        pp=gs.ResponseProblem(m,*candidate,T,H,player)
        vv,rr=gs.local_best_response(pp,seed+300,starts=3)
        val,grad=pp.value_gradient(vv)
        good=self.one_audit(m,candidate,T,H,player,dict(objective=val,residual=pp.projected_residual(vv,grad),
            violation=pp.violation(vv),all_starts_success=all(t['success'] for t in rr)),pp.value_gradient(pp.initial)[0],vv,'H24_fixed_opponent')
        spread=max(float(np.max(abs(np.array(t['control'])-v))) for t in raw)
        success=all(t['success'] for t in self.attempts[first:])
        good=bool(good and spread<=1e-3 and success and (not strong or ok))
        elapsed=time.perf_counter()-start
        self.timing.append(dict(**self.context,item='attack_generation_total' if strong else 'replanning_total',seconds=elapsed,note='nested responses included'))
        self.quality.append(dict(**self.context,check='three_start_control_spread',value=spread,threshold=1e-3,passed=spread<=1e-3))
        self.plan_rows(candidate,'selected',j,True)
        self.context.update(phase='extra_audit'); ts=time.perf_counter()
        finepr=gs.ResponseProblem(m,*candidate,T,2*H,player)
        fv,fr=gs.local_best_response(finepr,seed+300,starts=3)
        val,g=finepr.value_gradient(fv)
        fine=self.one_audit(m,candidate,T,2*H,player,dict(objective=val,residual=finepr.projected_residual(fv,g),
            violation=finepr.violation(fv),all_starts_success=all(t['success'] for t in fr)),finepr.value_gradient(finepr.initial)[0],fv,'H48_fixed_candidate')
        self.timing.append(dict(**self.context,item='precision_audit_total',seconds=time.perf_counter()-ts))
        write_json(folder/'decision.json',dict(passed=bool(good and fine),online_seconds=elapsed,spread=spread,
            all_optimizer_calls_success=all(t['success'] for t in self.attempts[first:]),seed=seed,x0=m.x0.tolist(),
            K=len(u[0]),T=T,H=H,controls=[x.tolist() for x in candidate],initial_selected_controls=[x.tolist() for x in original]))
        return candidate,bool(good and fine)

def register():
    BASE.mkdir(exist_ok=True); (BASE/'checkpoints').mkdir(exist_ok=True)
    assert not (BASE/'source_and_config_manifest.json').exists(), 'Do not overwrite preregistration'
    sources={}
    def add(p,role):
        assert p.is_file(),p
        sources[p.relative_to(ROOT).as_posix()]=dict(role=role,sha256=sha(p),bytes=p.stat().st_size)
    for p in [D7/'D7_experiment_protocol.md',D7/'03_experiment_protocol.md',D7/'config_new_topology.yaml',
        D7/'topology_assets.csv',D7/'topology_edges.csv',ROOT/'02_MODEL_SPEC.md',ROOT/'DECISIONS.md',ROOT/'reviews/APPROVAL_LOG.md']:
        add(p,'protocol_model_or_authority')
    for p in (ROOT/'paper/work_d8_1').glob('*.md'): add(p,'D8_1_required_read_only')
    for folder in [STATIC,ROLL/'B1.2']:
        for p in folder.rglob('*'):
            if p.is_file(): add(p,'D7_original_controls_execution_and_plans')
    for folder in [D7/'results/static',ROLL]:
        for p in folder.glob('*.csv'): add(p,'D7_original_tables')
    checks=[]
    for rel in ['src/core.py','src/game_solver.py','src/matched_mechanism.py','src/diagnose_equilibrium.py',
        'src/experiments.py','src/supplement_c2.py','paper/work_d5/analysis/run_replanning.py',
        'paper/work_d7/analysis/run_d7.py','paper/work_d7/analysis/run_rolling.py']:
        live=ROOT/rel; snap=D7/'source_snapshot'/rel
        add(live,'imported_source'); add(snap,'D7_actual_source_snapshot')
        checks.append(dict(path=rel,live_sha256=sha(live),snapshot_sha256=sha(snap),equal=sha(live)==sha(snap)))
    m=load_model(STATIC/'model.json'); validate_model(m)
    assert all(x['equal'] for x in checks)
    assert m.B==1.2 and m.A==.8 and m.q[4]==4 and np.count_nonzero(m.beta)==8
    assert json.loads((STATIC/'static_gate.json').read_text())['passed']
    assert json.loads((ROLL/'B1.2/budget_gate.json').read_text())['passed']
    old=load_controls(STATIC/'G_controls.json')
    common=json.loads((ROLL/'B1.2/common_prefix.json').read_text())
    assert all(np.array_equal(v[:3],np.array(c)) for v,c in zip(old,common['controls']))
    mapping=dict(K6_controls='paper/work_d7/results/static/B1.2/{G,F}_controls.json',
        K6_cross='paper/work_d7/results/static/B1.2/cross_evaluation.csv',
        actual_attacks='paper/work_d7/results/rolling_event_B1.2/B1.2/frozen_attacks.json',
        first_lag='offline G_controls.json [0][3:6]',later_lag='{event}_G/update{j-1}/warm/controls.json [0][1:]',
        common_history='paper/work_d7/results/rolling_event_B1.2/B1.2/common_prefix.json',
        comparisons='paper/work_d7/results/rolling_event_B1.2/objectives.csv (H48, period=post)',
        derived_D8_tables_used_as_experimental_inputs=False)
    write_json(BASE/'source_and_config_manifest.json',dict(created=now(),sources=sources,source_equality=checks,mapping=mapping,
        parameters=json.loads((STATIC/'model.json').read_text()),K12=dict(K=K,T=T,H=H,seed=SEED,path_offsets=[0,1,2]),
        environment=dict(python=sys.version,platform=platform.platform(),numpy=np.__version__,scipy=scipy.__version__,pandas=pd.__version__)))
    gate(0,True,source_count=len(sources),source_snapshot_equal=True)

def preflight():
    m=load_model(STATIC/'model.json'); rows=[]
    def add(check,value,threshold,**kw): rows.append(dict(check=check,value=float(value),threshold=threshold,passed=bool(value<=threshold),**kw))
    for k,tt,hh in [(12,10.,24),(3,5.,48),(2,10/3,48),(1,5/3,48)]:
        u=tuple(v*.5 for v in random_pair(m,k,SEED+k))
        check_controls(m,*u)
        for p in ('D','A'):
            pr=gs.ResponseProblem(m,*u,tt,hh,p); val,g=pr.value_gradient(pr.initial)
            assert len(pr.initial)==k*(12 if p=='D' else 2) and pr.C.shape==(k,len(pr.initial))
            errors=[]
            for j in range(len(g)):
                d=np.zeros_like(g); d[j]=1e-6
                fd=(pr.value_gradient(pr.initial+d)[0]-pr.value_gradient(pr.initial-d)[0])/2e-6
                errors.append(abs(fd-g[j]))
            add('all_component_gradient',max(errors),1e-6,K=k,player=p,component=int(np.argmax(errors)))
            sim=simulate(m,*u,tt,hh)
            add('objective_match',abs(val-(sim['J_D'] if p=='D' else -sim['J_A'])),1e-10,K=k,player=p)
            assert np.allclose(pr.C@pr.initial,(u[1]+u[2]).sum(axis=1) if p=='D' else u[0].sum(axis=1))
        if k==12:
            embedded=tuple(np.repeat(v,2,axis=0) for v in load_controls(STATIC/'G_controls.json'))
            check_controls(m,*embedded)
            fine=simulate(m,*embedded,10.,24); coarse=simulate(m,*load_controls(STATIC/'G_controls.json'),10.,48)
            add('K6_embedding_same_physical_step',np.max(abs(fine['states']-coarse['states'])),1e-12,K=k)
            add('K6_embedding_objective',abs(fine['J_D']-coarse['J_D']),1e-12,K=k)
    # Small response smoke test: same six assets, one control interval only.
    smoke=[]
    small=initial_controls(m,1,'Uniform')
    for p in ('D','A'):
        pr=gs.ResponseProblem(m,*small,5/3,48,p)
        v,raw=gs.local_best_response(pr,SEED+500+(p=='A'),starts=3)
        val,g=pr.value_gradient(v)
        smoke.append(dict(player=p,seed=SEED+500+(p=='A'),raw=raw,selected=v.tolist()))
        add('small_response_residual',pr.projected_residual(v,g),1e-4,K=1,player=p)
        add('small_response_violation',pr.violation(v),1e-10,K=1,player=p)
        add('small_response_exit_failures',sum(not a['success'] for a in raw),0,K=1,player=p)
    write_json(BASE/'checkpoints/gate1_small_response_raw.json',smoke)
    csv(BASE/'checkpoints/gate1_checks.csv',rows)
    passed=all(r['passed'] for r in rows); gate(1,passed,checks=rows)
    assert passed,'Gate1 failed'

def integration_error(a,b,ratio):
    return max(float(np.max(abs(a['states']-b['states'][::ratio]))),abs(a['J_D']-b['J_D']),abs(a['J_A']-b['J_A']),max(abs(a['parts'][p]-b['parts'][p]) for p in PARTS))

def controls_export(m,u,label):
    dt=T/len(u[0]); x=m.x0.copy(); rows=[]
    write_json(BASE/f'K12_{label}_controls.json',[v.tolist() for v in u])
    for k in range(len(u[0])):
        seg=simulate(replace(m,x0=x),*(v[k:k+1] for v in u),dt,H)
        for i in range(m.n):
            rows.append(dict(slot=k,t_start=k*dt,t_end=(k+1)*dt,node=i,paper_node=f'v{i+1}',a=u[0][k,i],s=u[1][k,i],r=u[2][k,i],
                resource=m.b_s[i]*u[1][k,i]+m.b_r[i]*u[2][k,i],total_resource=float(u[1][k]@m.b_s+u[2][k]@m.b_r),
                attack_resource=float(u[0][k]@m.d_a),x_start=x[i],x_end=seg['states'][-1,i],
                business=dt*m.h[i]*u[1][k,i],isolation=dt*.5*m.c_s[i]*u[1][k,i]**2,recovery=dt*.5*m.c_r[i]*u[2][k,i]**2))
        x=seg['states'][-1].copy()
    csv(BASE/f'K12_{label}_decisions.csv',rows)

def solve_a():
    assert json.loads((BASE/'checkpoints/gate1.json').read_text())['passed']
    out=BASE/'results/K12';run=restore_run(out,K12Run); m=load_model(STATIC/'model.json');dump_model(out/'model.json',m)
    warm=initial_controls(m,K,'Uniform'); start=time.perf_counter()
    try:
        run.context=dict(B=1.2,evaluation='offline',method='G',update=-1)
        folder=out/'G';folder.mkdir()
        g,good=run.game(m,warm,SEED,folder);run.save();controls_export(m,g,'G')
        if not good: raise RuntimeError('K12 G numerical gate failed; selected Uniform retained')
        run.context=dict(B=1.2,evaluation='offline',method='F',update=-1)
        folder=out/'F';folder.mkdir()
        f,good=run.unilateral(m,warm,'D',SEED+100,folder);run.save();controls_export(m,f,'F')
        if not good: raise RuntimeError('K12 F numerical gate failed')
        run.context=dict(B=1.2,evaluation='cross',method='F_attack_response',update=-1)
        folder=out/'F_attack_response';folder.mkdir()
        af,good=run.unilateral(m,f,'A',SEED+200,folder,strong=True);run.save()
        write_json(out/'cross_attacks.json',dict(a0=f[0].tolist(),aG=g[0].tolist(),aBR_F=af[0].tolist()))
        if not good: raise RuntimeError('K12 F attack response gate failed')
        rows=[];states=[];usage=[]
        for label,u in [('G',g),('F',f)]:
            for name,a in [('a0',f[0]),('aG',g[0]),('aBR_F',af[0])]:
                sims={hh:simulate(m,a,u[1],u[2],T,hh) for hh in (H,2*H,4*H)}
                for hh,sim in sims.items():
                    rows.append(dict(K=K,H=hh,method=label,attack=name,J_D=sim['J_D'],J_A=sim['J_A'],**sim['parts']))
                    for t,x in zip(sim['times'],sim['states']): states.append(dict(method=label,attack=name,H=hh,t=t,**{f'x{i}':v for i,v in enumerate(x)}))
                err=max(integration_error(sims[H],sims[hh],hh//H) for hh in (2*H,4*H))
                run.quality.append(dict(B=1.2,method=label,evaluation=name,check='fixed_control_integration',value=err,threshold=1e-6,passed=err<=1e-6))
                domain=max(0.,float(-sims[H]['states'].min()),float(sims[H]['states'].max()-1))
                run.quality.append(dict(B=1.2,method=label,evaluation=name,check='state_domain',value=domain,threshold=1e-10,passed=domain<=1e-10))
                prd=gs.ResponseProblem(m,a,u[1],u[2],T,H,'D');pra=gs.ResponseProblem(m,a,u[1],u[2],T,H,'A')
                violation=max(prd.violation(prd.initial),pra.violation(pra.initial))
                run.quality.append(dict(B=1.2,method=label,evaluation=name,check='control_violation',value=violation,threshold=1e-10,passed=violation<=1e-10))
                for k in range(K):usage.append(dict(method=label,attack=name,slot=k,t_start=k*T/K,defense=float(u[1][k]@m.b_s+u[2][k]@m.b_r),attack_use=float(a[k]@m.d_a),B=m.B,A=m.A))
        csv(BASE/'K12_cross_evaluation.csv',rows);csv(out/'cross_states.csv',states);csv(out/'cross_resource.csv',usage)
        run.save(); passed=all(x['passed'] for x in run.quality) and all(x['passed'] for x in run.audit) and all(x['success'] for x in run.attempts)
        gate(2,passed,seconds=time.perf_counter()-start,optimizer_attempts=len(run.attempts));assert passed
    except Exception as exc:
        run.save();write_json(out/'FAILED.json',dict(at=now(),error=repr(exc),no_automatic_retry=True));manifest();raise
    finally: gs.local_best_response=run.original_br

def compare_a():
    m=load_model(STATIC/'model.json'); rows=[];assets=[];sub=[];objectives=[]
    for method in ('G','F'):
        u6=load_controls(STATIC/f'{method}_controls.json');u12=load_controls(BASE/f'K12_{method}_controls.json')
        for kind,a,b in zip(('a','s','r'),u6,u12):
            avg=b.reshape(6,2,m.n).mean(axis=1); diff=avg-a;delta=b[1::2]-b[::2]
            for node in [-1,*range(m.n)]:
                d=diff if node==-1 else diff[:,node];dd=delta if node==-1 else delta[:,node]
                rows.append(dict(method=method,control=kind,node=node,Linf=float(abs(d).max()),RMSE=float(np.sqrt(np.mean(d*d))),
                    within_parent_Linf=float(abs(dd).max()),within_parent_RMSE=float(np.sqrt(np.mean(dd*dd)))))
            for node in range(m.n): assets.append(dict(method=method,control=kind,node=node,K6_mean=float(a[:,node].mean()),K12_mean=float(b[:,node].mean()),difference=float(b[:,node].mean()-a[:,node].mean())))
            for k in range(6):
                for node in range(m.n):sub.append(dict(method=method,control=kind,parent_slot=k,node=node,K6=a[k,node],K12_first=b[2*k,node],K12_second=b[2*k+1,node],K12_average=avg[k,node],difference=diff[k,node],within_parent_change=delta[k,node]))
        for k,hs,u in [(6,(48,96,192),u6),(12,(24,48,96),u12)]:
            for hh in hs:
                sim=simulate(m,*u,10,hh)
                objectives.append(dict(method=method,K=k,H=hh,physical_step=10/(k*hh),J_D=sim['J_D'],J_A=sim['J_A'],**sim['parts']))
    csv(BASE/'K12_vs_K6_control_comparison.csv',rows);csv(BASE/'results/K12/asset_means.csv',assets);csv(BASE/'results/K12/subinterval_changes.csv',sub)
    csv(BASE/'K12_vs_K6_objective_comparison.csv',objectives)
    gate(3,True,note='Comparison completed; quality inherited from Gate2; no K6 reoptimization')

def solve_b():
    assert json.loads((BASE/'checkpoints/gate3.json').read_text())['passed']
    out=BASE/'results/R_LAG';run=restore_run(out); start=time.perf_counter()
    mpre=load_model(ROLL/'B1.2/model_pre.json');mpost=load_model(ROLL/'B1.2/model_post.json')
    old=load_controls(STATIC/'G_controls.json');common=json.loads((ROLL/'B1.2/common_prefix.json').read_text())
    frozen=json.loads((ROLL/'B1.2/frozen_attacks.json').read_text()); prediction_errors=[];predictions=[]
    try:
        for e,event in enumerate(('E0','E1')):
            attack=np.array(frozen[event]);x=np.array(common['x_event']);warm=tuple(v[3:].copy() for v in old)
            u=[v.copy() for v in old];u[0][3:]=attack
            for j in range(3):
                run.context=dict(B=1.2,evaluation=event,method='R-LAG',update=j)
                folder=out/event/f'update{j}';folder.mkdir(parents=True)
                source=STATIC/'G_controls.json' if j==0 else ROLL/f'B1.2/{event}_G/update{j-1}/warm/controls.json'
                prior=load_controls(source);pred=prior[0][3:6].copy() if j==0 else prior[0][1:].copy()
                assert pred.shape==(3-j,6)
                model=replace(mpost,x0=x.copy());dump_model(folder/'model_restart.json',model)
                write_json(folder/'input_provenance.json',dict(source=source.relative_to(ROOT).as_posix(),source_sha256=sha(source),
                    slice='[3:6]' if j==0 else '[1:]',fixed_attack_prediction=pred.tolist(),initial_defense=[warm[1].tolist(),warm[2].tolist()],
                    own_actual_state=x.tolist(),G_state_not_used=True,actual_future_not_used_for_optimization=True))
                seed=SEED+1000+100*e+10*j
                plan,good=run.unilateral(model,(pred,warm[1],warm[2]),'D',seed,folder,j)
                run.save();write_json(folder/'selected_controls.json',[v.tolist() for v in plan])
                if not good: raise RuntimeError(f'R-LAG {event} update{j} numerical failure')
                for k in range(3-j):
                    err=pred[k,:2]-attack[j+k,:2]
                    prediction_errors.append(dict(evaluation=event,method='R-LAG',update=j,forecast_step=k,absolute_slot=3+j+k,
                        t_start=(3+j+k)*10/6,L1=float(abs(err).sum()),Linf=float(abs(err).max()),
                        pred_v1=pred[k,0],pred_v2=pred[k,1],actual_v1=attack[j+k,0],actual_v2=attack[j+k,1],
                        executed_first_interval=k==0))
                for k in range(len(pred)):
                    for node in range(6):predictions.append(dict(evaluation=event,update=j,forecast_step=k,node=node,a=pred[k,node],s=plan[1][k,node],r=plan[2][k,node]))
                u[1][3+j]=plan[1][0];u[2][3+j]=plan[2][0]
                sim=simulate(model,attack[j:j+1],plan[1][:1],plan[2][:1],10/6,48)
                x=sim['states'][-1].copy();warm=tuple(v[1:].copy() for v in plan)
                run.tasks.append(dict(B=1.2,evaluation=event,method='R-LAG',update=j,passed=True,seed=seed))
                write_json(folder/'executed_first_interval.json',dict(x_end=x.tolist(),a=attack[j].tolist(),s=plan[1][0].tolist(),r=plan[2][0].tolist()))
                run.save()
            write_json(out/f'{event}_executed.json',[v.tolist() for v in u])
            rows=[]
            for k in range(6):
                for node in range(6):rows.append(dict(evaluation=event,method='R-LAG',slot=k,node=node,t_start=k*10/6,t_end=(k+1)*10/6,
                    a_actual=u[0][k,node],s=u[1][k,node],r=u[2][k,node],resource_use=float(u[1][k]@mpre.b_s+u[2][k]@mpre.b_r),budget=1.2))
            csv(BASE/f'R_LAG_{event}_controls.csv',rows)
            sims={hh:execute(mpre,mpost,u,hh) for hh in (48,96,192)};obj=[];states=[]
            for hh,sim in sims.items():
                pre=sim['slot_costs'][2]
                for period,parts in [('pre',pre),('post',{p:sim['parts'][p]-pre[p] for p in PARTS}),('full',sim['parts'])]:
                    jd,ja=objective(parts);obj.append(dict(B=1.2,evaluation=event,method='R-LAG',H=hh,period=period,J_D=jd,J_A=ja,**parts))
                for t,state in zip(sim['times'],sim['states']):states.append(dict(evaluation=event,H=hh,t=t,**{f'x{i}':v for i,v in enumerate(state)}))
            csv(BASE/f'R_LAG_{event}_objectives.csv',obj);csv(out/f'{event}_states.csv',states)
            p=sims[48];err=0.
            for hh in (96,192):
                f=sims[hh];err=max(err,float(np.max(abs(p['states']-f['states'][::hh//48]))),max(abs(p['parts'][key]-f['parts'][key]) for key in PARTS),max(abs(a-b) for a,b in zip(objective(p['parts']),objective(f['parts']))))
            prd=gs.ResponseProblem(mpre,*u,10,48,'D');pra=gs.ResponseProblem(mpre,*u,10,48,'A')
            for name,value,threshold in [('fixed_execution_integration',err,1e-6),('state_domain',max(0.,float(-p['states'].min()),float(p['states'].max()-1)),1e-10),
                ('continuity',p['continuity'],1e-12),('control_violation',max(prd.violation(prd.initial),pra.violation(pra.initial)),1e-10)]:
                run.quality.append(dict(B=1.2,evaluation=event,method='R-LAG',check=name,value=value,threshold=threshold,passed=value<=threshold))
            fair=True
            for method in ('P','G','R'):
                existing=load_controls(ROLL/f'B1.2/{event}_{method}_executed.json')
                fair=fair and np.array_equal(existing[0],u[0]) and all(np.array_equal(existing[i][:3],u[i][:3]) for i in (1,2))
            run.quality.append(dict(B=1.2,evaluation=event,method='R-LAG',check='common_attack_and_prefix',value=0 if fair else 1,threshold=0,passed=fair))
            run.save();print('EXECUTED R-LAG',event,obj[1]['J_D'],flush=True)
        csv(BASE/'R_LAG_prediction_errors.csv',prediction_errors);csv(out/'predicted_plans.csv',predictions)
        passed=all(r['passed'] for r in run.audit+run.quality) and all(r['success'] for r in run.attempts)
        gate(4,passed,seconds=time.perf_counter()-start,optimizer_attempts=len(run.attempts));assert passed
    except Exception as exc:
        run.save();csv(BASE/'R_LAG_prediction_errors.csv',prediction_errors)
        write_json(out/'FAILED.json',dict(at=now(),error=repr(exc),no_automatic_retry=True));manifest();raise
    finally:gs.local_best_response=run.original_br

def main():
    ap=argparse.ArgumentParser();ap.add_argument('stage',choices=['register','preflight','A','compare','B']);args=ap.parse_args()
    {'register':register,'preflight':preflight,'A':solve_a,'compare':compare_a,'B':solve_b}[args.stage]()
if __name__=='__main__':main()
