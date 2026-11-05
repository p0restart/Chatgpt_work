"""Bounded C2 evidence supplement. Finite payoff-table audit is not an ODE certificate."""
import argparse
from dataclasses import asdict, replace
from datetime import datetime, timezone
import hashlib
import itertools
import json
from pathlib import Path
import platform
import shutil
import time

import numpy as np
import pandas as pd
import scipy
from scipy.integrate import solve_ivp
import yaml

from .core import Model, synthetic_model_from_config, simulate, dynamics, cost_rates, check_controls
from .game_solver import ResponseProblem, local_best_response
from .experiments import initial_controls, write_json, save_evaluation


def load_controls(path):
    if path.suffix == '.json':
        return tuple(np.array(v, dtype=float) for v in json.loads(path.read_text()))
    df = pd.read_csv(path)
    return tuple(df.pivot(index='slot', columns='node', values=p).to_numpy() for p in ('a','s','r'))


def load_model(path):
    d = json.loads(path.read_text())
    return Model(**{k: np.array(v, dtype=bool if k=='entry' else float) if isinstance(v,list) else v for k,v in d.items()})


def dump_model(path,m):
    write_json(path,{k:v.tolist() if isinstance(v,np.ndarray) else v for k,v in asdict(m).items()})


class StaticDefense:
    """Chain rule through tied controls, with the same per-slot polytope."""
    def __init__(self, base):
        self.base=base
        self.K=1; self.width=base.width
        self.weights=base.weights; self.capacity=base.capacity
        self.initial=base.initial.reshape(base.K,base.width).mean(axis=0)
        self.upper=base.upper[:base.width].copy()
        self.C=self.weights[None,:]

    def value_gradient(self,v):
        val,g=self.base.value_gradient(np.tile(v,self.base.K))
        return val,g.reshape(self.base.K,self.width).sum(axis=0)

    def schedules(self,v):
        return self.base.schedules(np.tile(v,self.base.K))

    violation=ResponseProblem.violation
    projected_residual=ResponseProblem.projected_residual


def problem(m,u,T,steps,player,mode):
    base=ResponseProblem(m,*u,T,steps,player,mode if mode in ('recovery','isolation') else 'joint')
    return StaticDefense(base) if player=='D' and mode=='static' else base


def best_response(m,u,T,steps,player,mode,seed,starts):
    pr=problem(m,u,T,steps,player,mode)
    v,raw=local_best_response(pr,seed,starts=starts,maxiter=300,ftol=1e-11)
    val,g=pr.value_gradient(v)
    _,g0=pr.value_gradient(pr.initial)
    return pr.schedules(v),dict(player=player,objective=val,raw=raw,
        success=all(r['success'] for r in raw),residual=pr.projected_residual(v,g),
        incumbent_residual=pr.projected_residual(pr.initial,g0),violation=pr.violation(v))


def local_solve(m,u,T,steps,mode,seed,folder):
    folder.mkdir(parents=True)
    for iteration in range(41):
        du,di=best_response(m,u,T,steps,'D',mode,seed+10*iteration,1)
        au,ai=best_response(m,u,T,steps,'A',mode,seed+10*iteration+1,1)
        sim=simulate(m,*u,T,steps)
        gd=max(0.,sim['J_D']-di['objective']); ga=max(0.,-ai['objective']-sim['J_A'])
        distance=max(np.max(abs(du[1]-u[1])),np.max(abs(du[2]-u[2])),np.max(abs(au[0]-u[0])))
        passed=bool(max(gd/(1+abs(sim['J_D'])),ga/(1+abs(sim['J_A'])))<=1e-7 and
                    max(di['incumbent_residual'],ai['incumbent_residual'])<=1e-4 and distance<=1e-3 and di['success'] and ai['success'])
        row=dict(iteration=iteration,J_D=sim['J_D'],J_A=sim['J_A'],gap_D=gd,gap_A=ga,
                 distance=float(distance),passed=passed,D=di,A=ai,controls=[v.tolist() for v in u])
        if not passed and iteration<40:
            next_u,seq=best_response(m,(u[0],du[1],du[2]),T,steps,'A',mode,seed+10*iteration+2,1)
            row['sequential_A']=seq
        with (folder/'trace.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(row)+'\n')
        if passed or iteration==40:break
        u=next_u
    write_json(folder/'last.json',row)
    write_json(folder/'controls.json',[v.tolist() for v in u])
    return u,row


def starting_controls(m,K,mode,seed):
    u=initial_controls(m,K,'Uniform')
    rng=np.random.default_rng(seed)
    rand=[rng.random((K,m.n)) for _ in range(3)]
    rand[0][:,~m.entry]=0
    rand[0]*=np.minimum(1,m.A/(rand[0]@m.d_a+1e-30))[:,None]
    use=rand[1]@m.b_s+rand[2]@m.b_r
    for j in (1,2):rand[j]*=np.minimum(1,m.B/(use+1e-30))[:,None]
    result=[u,tuple(np.zeros_like(x) for x in u),tuple(rand)]
    for a,s,r in result:
        if mode=='recovery':s[:]=0
        if mode=='isolation':r[:]=0
        if mode=='static':s[:]=s.mean(axis=0);r[:]=r.mean(axis=0)
    return result


def optimized_plan(m,K,T,mode,seed,folder):
    sols=[]; lasts=[]
    for label,u in zip(('uniform','zero','random'),starting_controls(m,K,mode,seed)):
        sol,last=local_solve(m,u,T,12,mode,seed,folder/label)
        sols.append(sol);lasts.append(last)
    stability=max(float(np.max(abs(sols[i][j]-sols[0][j]))) for i in (1,2) for j in range(3))
    fine,last=local_solve(m,sols[0],T,48,mode,seed+1000,folder/'fine')
    write_json(folder/'multistart.json',dict(control_spread=stability,all_pass=all(v['passed'] for v in lasts),fine_pass=last['passed']))
    return fine


def batch_values(m,a,s,r,T,steps):
    """Vectorized independent RK4 trajectories; each batch item is one strategy pair."""
    size,K,n=a.shape
    y=np.zeros((size,n+2));y[:,:n]=m.x0
    dt=T/(K*steps)
    for k in range(K):
        ak,sk,rk=a[:,k],s[:,k],r[:,k]
        direct=sk@m.h+.5*((sk*sk)@m.c_s+(rk*rk)@m.c_r)
        effort=.5*((ak*ak)@m.c_a)
        def rhs(z):
            x=z[:,:n]
            f=(1-x)*(m.alpha*ak+(x*(1-m.epsilon*sk))@m.beta)-(m.delta+m.gamma*rk)*x
            return np.column_stack((f,x@m.q+direct,x@m.g-effort))
        for _ in range(steps):
            f1=rhs(y);f2=rhs(y+dt*f1/2);f3=rhs(y+dt*f2/2);f4=rhs(y+dt*f3)
            y+=dt*(f1+2*f2+2*f3+f4)/6
    return np.column_stack((y[:,n]+y[:,:n]@m.omega,y[:,n+1]+y[:,:n]@m.nu))


def plans(m,step,K=2):
    levels=np.arange(int(np.floor((1+1e-12)/step))+1)*step
    slots=np.array([v for v in itertools.product(levels,repeat=2*m.n) if np.dot(v,np.r_[m.b_s,m.b_r])<=m.B+1e-12])
    idx=np.array(list(itertools.product(range(len(slots)),repeat=K)))
    return slots[idx]


def independent_values(m,u,T):
    K=len(u[0]);y=np.r_[m.x0,np.zeros(6)]
    for k in range(K):
        a,s,r=(v[k] for v in u)
        def rhs(t,z):return np.r_[dynamics(m,z[:m.n],a,s,r),cost_rates(m,z[:m.n],a,s,r)]
        result=solve_ivp(rhs,(k*T/K,(k+1)*T/K),y,method='DOP853',rtol=1e-11,atol=1e-13)
        if not result.success:raise RuntimeError(result.message)
        y=result.y[:,-1]
    return np.array([sum(y[m.n:m.n+4])+m.omega@y[:m.n],y[-2]-y[-1]+m.nu@y[:m.n]])


def finite_run(out):
    out.mkdir()
    cfg=yaml.safe_load(Path('configs/base.yaml').read_text())
    cfg.update(n=3,K=2,attack_entry_indices=[0],x0=[.1,0,0],network='chain')
    base=synthetic_model_from_config(cfg)
    beta=np.array([[0,.12,0],[0,0,.08],[0,0,0]])
    attacks=np.zeros((9,2,3));attacks[:,:,0]=np.array(list(itertools.product([0,.4,.8],repeat=2)))
    rows=[]
    for budget in (.6,1.2):
        m=replace(base,beta=beta,q=np.array([1.,1.,4.]),B=budget)
        case=out/f'B{budget}';case.mkdir();dump_model(case/'model.json',m)
        u=optimized_plan(m,2,10.,'joint',11,case/'continuous_candidate')
        check_controls(m,*u)
        for step in (.6,.3):
            folder=case/f'step{step}';folder.mkdir()
            defense=plans(m,step)
            np.savez_compressed(folder/'strategies.npz',defense=defense,attack=attacks)
            values={}
            for substeps in (12,48):
                table=np.empty((len(defense),len(attacks),2))
                for ia,at in enumerate(attacks):
                    for lo in range(0,len(defense),2048):
                        d=defense[lo:lo+2048]
                        a=np.broadcast_to(at,(len(d),2,3))
                        table[lo:lo+len(d),ia]=batch_values(m,a,d[:,:,:3],d[:,:,3:],10.,substeps)
                values[substeps]=table
                np.savez_compressed(folder/f'payoffs_{substeps}.npz',J_D=table[:,:,0],J_A=table[:,:,1])
            table=values[48];jd=table[:,:,0];ja=table[:,:,1]
            gd=np.maximum(0,jd-jd.min(axis=0)[None,:]);ga=np.maximum(0,ja.max(axis=1)[:,None]-ja)
            regret=np.maximum(gd,ga)
            eq=np.argwhere(regret<=1e-8)
            selected=np.unravel_index(np.argmin(regret),regret.shape)
            pd.DataFrame([dict(defense=int(i),attack=int(j),gap_D=gd[i,j],gap_A=ga[i,j]) for i,j in eq]).to_csv(folder/'pure_equilibria.csv',index=False)
            # Exhaust ALL finite menu deviations against the continuous candidate, not just nearby moves.
            devd=[]
            for lo in range(0,len(defense),2048):
                d=defense[lo:lo+2048]
                devd.extend(batch_values(m,np.broadcast_to(u[0],(len(d),2,3)),d[:,:,:3],d[:,:,3:],10.,48)[:,0])
            deva=batch_values(m,attacks,np.broadcast_to(u[1],attacks.shape),np.broadcast_to(u[2],attacks.shape),10.,48)[:,1]
            np.savez_compressed(folder/'candidate_deviations.npz',J_D=devd,J_A=deva)
            current=simulate(m,*u,10.,48);idbest=int(np.argmin(devd));iabest=int(np.argmax(deva))
            dd=defense[idbest]
            selected_u=(attacks[selected[1]],defense[selected[0],:,:3],defense[selected[0],:,3:])
            probes=[('candidate',u),('best_D',(u[0],dd[:,:3],dd[:,3:])),('best_A',(attacks[iabest],u[1],u[2])),('minimum_regret',selected_u)]
            checks=[]
            for label,pu in probes:
                iv=independent_values(m,pu,10.);rv=simulate(m,*pu,10.,48)
                checks.append(dict(label=label,J_D_DOP853=float(iv[0]),J_A_DOP853=float(iv[1]),error=float(np.max(abs(iv-[rv['J_D'],rv['J_A']])))))
                write_json(folder/f'{label}_controls.json',[v.tolist() for v in pu])
            pd.DataFrame(checks).to_csv(folder/'independent_integrator.csv',index=False)
            save_evaluation(folder/'selected_evaluation',m,{**cfg,'B':budget,'seed':11,'scenario':'small_chain','rk4_substeps_per_slot':12},selected_u,'finite_minimum_regret','finite_menu')
            row=dict(B=budget,step=step,defense_plans=len(defense),attack_plans=len(attacks),pairs=len(defense)*len(attacks),
                     pure_equilibria=len(eq),minimum_max_regret=float(regret.min()),
                     candidate_gap_D=max(0.,current['J_D']-min(devd)),candidate_gap_A=max(0.,max(deva)-current['J_A']),
                     candidate_J_D=current['J_D'],candidate_J_A=current['J_A'],
                     max_table_refinement=float(np.max(abs(values[12]-values[48]))),
                     independent_error=max(v['error'] for v in checks),continuous_certificate=False)
            write_json(folder/'audit.json',row);rows.append(row)
            pd.DataFrame(rows).to_csv(out/'summary.csv',index=False)
            print('FINITE',row,flush=True)
    return rows


def comparison_run(out):
    out.mkdir()
    source=Path('results/matched_mechanism/run01')
    cases=[source/f'seed{s}_B{b}_unequal_high_at_node3' for s in (11,22,33) for b in (.6,1.2,1.8)]
    cases.append(Path('results/p3/fair01/seed33_business_cost_B0.6'))
    rows=[]
    for case in cases:
        folder=out/case.name;folder.mkdir();m=load_model(case/'model.json');dump_model(folder/'model.json',m)
        raw=yaml.safe_load((case/'config.yaml').read_text());cfg=raw.get('base',raw)
        write_json(folder/'config.json',cfg)
        if 'matched_mechanism' in str(case):
            joint=load_controls(case/'fine/controls.json')
        else:joint=load_controls(Path('results/equilibrium_audit/run01')/case.name/'warm/controls.json')
        inputs=dict(joint_source=str(case),model_sha256=hashlib.sha256((case/'model.json').read_bytes()).hexdigest())
        write_json(folder/'inputs.json',inputs)
        methods={method:initial_controls(m,6,method) for method in ('Uniform','Value-only','Spread-only')}
        methods['Joint-dynamic']=joint
        for label,mode in [('Recovery-only','recovery'),('Isolation-only','isolation'),('Joint-static','static')]:
            methods[label]=optimized_plan(m,6,10.,mode,cfg['seed'],folder/label)
            print('PLAN',case.name,label,flush=True)
        init=initial_controls(m,6,'Uniform')
        fixed,di=best_response(m,init,10.,48,'D','joint',cfg['seed'],3)
        write_json(folder/'Fixed-trained_response.json',di)
        methods['Fixed-trained']=fixed
        for label,u in methods.items():
            mode={'Recovery-only':'recovery','Isolation-only':'isolation','Joint-static':'static'}.get(label,'joint')
            evaluated,ai=best_response(m,u,10.,48,'A',mode,cfg['seed']+90000,3)
            _,di=best_response(m,evaluated,10.,48,'D',mode,cfg['seed']+90001,3)
            write_json(folder/f'{label}_evaluation_audit.json',dict(A=ai,D=di))
            for evaluation,control in [('adaptive_attack',evaluated),('common_fixed_attack',(init[0],u[1],u[2]))]:
                row=save_evaluation(folder/f'{label}_{evaluation}',m,{**cfg,'rk4_substeps_per_slot':48},control,label,evaluation)
                row['case']=case.name
                row['attack_success']=ai['success'];row['attack_residual']=ai['residual']
                row['observed_D_improvement_at_adaptive']=max(0.,simulate(m,*evaluated,10.,48)['J_D']-di['objective'])
                rows.append(row)
            pd.DataFrame(rows).to_csv(out/'summary.csv',index=False)
        print('COMPLETE',case.name,flush=True)
    return rows


def audit_existing(out):
    source=Path('results/p3/fair01')
    df=pd.read_csv(source/'summary.csv')
    checks=[]
    for case in sorted(source.glob('seed*')):
        m=load_model(case/'model.json')
        for folder in sorted(case.glob('*_attack')):
            old=json.loads((folder/'summary.json').read_text())
            u=load_controls(folder/'controls.csv');check_controls(m,*u)
            sim=simulate(m,*u,10.,48)
            checks.append(dict(case=case.name,method=old['method'],evaluation=old['evaluation'],
                               error=abs(sim['J_D']-old['fine_J_D'])))
    pd.DataFrame(checks).to_csv(out/'existing_reintegration.csv',index=False)
    paired=[]
    for key,group in df.groupby(['seed','scenario','B','evaluation']):
        jd=float(group.loc[group.method=='Joint-dynamic','fine_J_D'].iloc[0])
        for _,r in group.iterrows():
            if r['method']=='Joint-dynamic':continue
            paired.append(dict(seed=key[0],scenario=key[1],B=key[2],evaluation=key[3],baseline=r['method'],
                               joint=jd,baseline_cost=r['fine_J_D'],reduction_percent=100*(r['fine_J_D']-jd)/r['fine_J_D']))
    pd.DataFrame(paired).to_csv(out/'existing_paired.csv',index=False)
    write_json(out/'existing_audit.json',dict(rows=len(df),reintegrated=len(checks),max_error=max(r['error'] for r in checks)))


def manifest(out):
    rows=[]
    for p in sorted(out.rglob('*')):
        if p.is_file() and p.name!='manifest.json':
            rows.append(dict(path=str(p.relative_to(out)),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),bytes=p.stat().st_size))
    write_json(out/'manifest.json',rows)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);ap.add_argument('--part',choices=['all','finite','comparison','existing'],default='all');args=ap.parse_args()
    out=Path(args.output);out.mkdir(parents=True,exist_ok=False)
    snap=out/'source_snapshot';snap.mkdir()
    for p in [*Path('src').glob('*.py'),Path('configs/base.yaml'),Path('reports/SUPPLEMENT_C2_PROTOCOL.md')]:shutil.copy2(p,snap/p.name)
    meta=dict(status='RUNNING',part=args.part,started_utc=datetime.now(timezone.utc).isoformat(),python=platform.python_version(),numpy=np.__version__,scipy=scipy.__version__,pandas=pd.__version__,platform=platform.platform(),seed=11,continuous_certificate=False)
    write_json(out/'metadata.json',meta);start=time.perf_counter()
    try:
        if args.part in ('all','existing'):audit_existing(out)
        if args.part in ('all','finite'):finite_run(out/'finite')
        if args.part in ('all','comparison'):comparison_run(out/'comparison')
        meta['status']='COMPLETED'
    except Exception as e:
        meta.update(status='FAILED',error=repr(e));raise
    finally:
        meta['seconds']=time.perf_counter()-start;write_json(out/'metadata.json',meta);manifest(out)


if __name__=='__main__':main()
