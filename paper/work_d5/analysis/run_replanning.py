"""D5 orchestration only: reuse frozen dynamics and local solvers."""
from __future__ import annotations

import argparse
from dataclasses import replace
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
import numpy as np
import pandas as pd
import scipy
from src import game_solver as gs
from src.core import simulate, check_controls, validate_model
from src.diagnose_equilibrium import residuals
from src.experiments import write_json
from src.matched_mechanism import strict_solve, control_distance
from src.supplement_c2 import load_model, load_controls, dump_model

DT = 5 / 3
PARTS = ['security', 'business', 'isolation', 'recovery', 'terminal_defense',
         'attacker_value', 'attacker_effort', 'terminal_attacker']


def now():
    return datetime.now(timezone.utc).isoformat()


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def csv(path, rows):
    pd.DataFrame(rows).to_csv(path, index=False)


def random_pair(m, K, seed):
    rng = np.random.default_rng(seed)
    u = [rng.random((K, m.n)) for _ in range(3)]
    u[0][:, ~m.entry] = 0
    u[0] *= np.minimum(1, m.A / (u[0] @ m.d_a + 1e-30))[:, None]
    use = u[1] @ m.b_s + u[2] @ m.b_r
    for j in (1, 2):
        u[j] *= np.minimum(1, m.B / (use + 1e-30))[:, None]
    return tuple(u)


class Run:
    def __init__(self, out):
        self.out = out
        self.context = {}
        self.attempts, self.audit, self.timing, self.plans = [], [], [], []
        self.executed, self.trajectories, self.objectives, self.comparisons = [], [], [], []
        self.attacks, self.quality, self.tasks = [], [], []
        self.original_br = gs.local_best_response
        gs.local_best_response = self.logged_br

    def logged_br(self, problem, seed=11, starts=3, maxiter=300, ftol=1e-10):
        start = time.perf_counter()
        v, raw = self.original_br(problem, seed, starts, maxiter, ftol)
        elapsed = time.perf_counter() - start
        call = len(self.attempts)
        with (self.out / 'optimizer_calls.jsonl').open('a', encoding='utf-8') as f:
            f.write(json.dumps(dict(**self.context, call=call, player=problem.player,
                K=problem.K, T=problem.T, H=problem.substeps, seed=seed,
                maxiter=maxiter, ftol=ftol, wall_seconds=elapsed, raw=raw)) + '\n')
        for row in raw:
            self.attempts.append(dict(**self.context, call=call, player=problem.player,
                K=problem.K, H=problem.substeps, seed=seed,
                **{k: val for k, val in row.items() if k not in ('initial_control', 'control')}))
        self.timing.append(dict(**self.context, item='response_optimization',
            player=problem.player, H=problem.substeps, seconds=elapsed,
            note='nested within task time; do not add twice'))
        return v, raw

    def save(self):
        for name, rows in [('optimizer_attempts', self.attempts), ('solver_audit', self.audit),
                ('timing', self.timing), ('planned_controls', self.plans),
                ('executed_controls', self.executed), ('trajectories', self.trajectories),
                ('objectives', self.objectives), ('comparisons', self.comparisons),
                ('attack_scenarios', self.attacks), ('quality', self.quality), ('tasks', self.tasks)]:
            if rows:
                csv(self.out / f'{name}.csv', rows)

    def plan_rows(self, u, label, j, selected=False):
        for k in range(len(u[0])):
            for node in range(6):
                self.plans.append(dict(self.context, path=label, selected=selected,
                    absolute_slot=3+j+k, t_start=(3+j+k)*DT, node=node,
                    a_plan=u[0][k,node], s_plan=u[1][k,node], r_plan=u[2][k,node]))

    def one_audit(self, m, u, T, H, player, info, base, opt, label):
        pr = gs.ResponseProblem(m, *u, T, H, player)
        _, grad = pr.value_gradient(pr.initial)
        incres = pr.projected_residual(pr.initial, grad)
        signed = base - info['objective']
        distance = float(np.max(abs(opt - pr.initial)))
        row = dict(**self.context, audit=label, player=player, H=H,
            signed_improvement=signed, discovered_improvement=max(0, signed),
            relative_improvement=max(0, signed)/(1+abs(base)),
            incumbent_residual=incres, response_residual=info['residual'],
            violation=info['violation'], response_distance=distance,
            all_starts_success=info['all_starts_success'])
        row['passed'] = bool(row['relative_improvement'] <= 1e-7 and incres <= 1e-4
            and distance <= 1e-3 and info['violation'] <= 1e-10
            and info['all_starts_success'])
        self.audit.append(row)
        return row['passed']

    def pair_audit(self, m, u, T, H, seed, label):
        gap, du, au = gs.observed_gaps(m, u, T, H, seed, starts=3)
        good = []
        for p, candidate, base in [('D', du, gap['J_D']), ('A', au, -gap['J_A'])]:
            pr = gs.ResponseProblem(m, *candidate, T, H, p)
            good.append(self.one_audit(m, u, T, H, p, gap[p], base, pr.initial, label))
        return all(good)

    def game(self, m, warm, seed, folder, j):
        start = time.perf_counter()
        index = len(self.attempts)
        solutions, lasts = [], []
        initials = [warm, tuple(np.zeros_like(x) for x in warm), random_pair(m, len(warm[0]), seed+2)]
        for p, (label, initial) in enumerate(zip(('warm','zero','random'), initials)):
            self.context.update(phase='online_planning', path=label)
            sol, last = strict_solve(m, initial, len(warm[0])*DT, 48, seed+p, folder/label)
            solutions.append(sol); lasts.append(last)
            self.plan_rows(sol, label, j, label=='warm')
            for player in ('D', 'A'):
                self.audit.append(dict(**self.context, audit='strict_path_final', player=player,
                    H=48, signed_improvement=last[f'signed_gap_{player}'],
                    discovered_improvement=last[f'gap_{player}'],
                    relative_improvement=last[f'relative_{player}'],
                    incumbent_residual=last['incumbent_residual'][player],
                    response_distance=last['response_distance'], passed=last['passed']))
        spread = max(control_distance(solutions[0], v) for v in solutions[1:])
        self.context.update(phase='online_planning', path='warm_validation')
        passed = self.pair_audit(m, solutions[0], len(warm[0])*DT, 48, seed, 'H48_multistart')
        seconds = time.perf_counter()-start
        all_success = all(r['success'] for r in self.attempts[index:])
        passed = passed and all(x['passed'] for x in lasts) and spread <= 1e-3 and all_success
        self.timing.append(dict(**self.context, item='replanning_total', seconds=seconds,
            note='includes 3 full paths and H48 final validation; nested responses included'))
        self.quality.append(dict(**self.context, check='three_path_control_spread', value=spread,
            threshold=1e-3, passed=spread<=1e-3))
        self.context.update(phase='extra_audit', path='warm')
        ts = time.perf_counter()
        fine = self.pair_audit(m, solutions[0], len(warm[0])*DT, 96, seed, 'H96_fixed_candidate')
        self.timing.append(dict(**self.context, item='precision_audit_total', seconds=time.perf_counter()-ts))
        write_json(folder/'decision.json', dict(passed=bool(passed and fine), online_seconds=seconds,
            spread=spread, all_optimizer_calls_success=all_success,
            selected_path='warm', x0=m.x0.tolist(), K=len(warm[0]), T=len(warm[0])*DT, seed=seed))
        return solutions[0], bool(passed and fine)

    def unilateral(self, m, u, player, seed, folder, j=0, strong=False):
        """Fixed-opponent solve; original best-response routine owns all optimization."""
        T = len(u[0])*DT
        start = time.perf_counter(); first = len(self.attempts)
        self.context.update(phase='attack_generation' if strong else 'online_planning', path='multistart')
        pr = gs.ResponseProblem(m, *u, T, 48, player)
        v, raw = gs.local_best_response(pr, seed=seed+2, starts=3)
        candidate = pr.schedules(v)
        original = candidate
        for p, row in enumerate(raw):
            self.plan_rows(pr.schedules(np.array(row['control'])), ['warm','zero','random'][p], j)
        if strong:
            for iteration in range(41):
                pp = gs.ResponseProblem(m, *candidate, T, 48, player)
                best, raw12 = gs.local_best_response(pp, seed+100+iteration, starts=12)
                best_value = pp.value_gradient(best)[0]
                for channel in range(pp.width):
                    z = np.zeros((pp.K, pp.width))
                    z[:,channel] = min(1, pp.capacity/pp.weights[channel])
                    sp = gs.ResponseProblem(m, *pp.schedules(z.ravel()), T, 48, player)
                    sv, _ = gs.local_best_response(sp, seed+200+10*iteration+channel, starts=1)
                    value = sp.value_gradient(sv)[0]
                    if value < best_value:
                        best_value, best = value, sv
                base, grad = pp.value_gradient(pp.initial)
                res = pp.projected_residual(pp.initial, grad)
                signed = base-best_value; distance=float(np.max(abs(best-pp.initial)))
                ok = bool(max(0,signed)/(1+abs(base))<=1e-7 and res<=1e-4 and distance<=1e-3)
                self.audit.append(dict(**self.context, audit='E1_12start_sparse', player=player,
                    H=48, iteration=iteration, signed_improvement=signed,
                    discovered_improvement=max(0,signed), relative_improvement=max(0,signed)/(1+abs(base)),
                    incumbent_residual=res, response_distance=distance, passed=ok))
                write_json(folder/f'strong_{iteration:02d}.json',dict(current=[x.tolist() for x in candidate],
                    returned=[x.tolist() for x in pp.schedules(best)], raw12=raw12, passed=ok))
                if ok or iteration==40:
                    break
                candidate = pp.schedules(best)
        pp = gs.ResponseProblem(m, *candidate, T, 48, player)
        vv, rr = gs.local_best_response(pp, seed+300, starts=3)
        val, grad = pp.value_gradient(vv)
        base = pp.value_gradient(pp.initial)[0]
        info = dict(objective=val, residual=pp.projected_residual(vv,grad),
            violation=pp.violation(vv), all_starts_success=all(t['success'] for t in rr))
        good = self.one_audit(m,candidate,T,48,player,info,base,vv,'H48_fixed_opponent')
        # Compare solutions from the three independent original starting points.
        spread = max(float(np.max(abs(np.array(t['control'])-v))) for t in raw)
        success = all(t['success'] for t in self.attempts[first:])
        good = bool(good and spread<=1e-3 and success and (not strong or ok))
        elapsed = time.perf_counter()-start
        self.timing.append(dict(**self.context,item='attack_generation_total' if strong else 'replanning_total',
            seconds=elapsed, note='nested responses included'))
        self.quality.append(dict(**self.context,check='three_start_control_spread',value=spread,
            threshold=1e-3,passed=spread<=1e-3))
        self.plan_rows(candidate,'selected',j,True)
        self.context.update(phase='extra_audit')
        ts=time.perf_counter()
        pp96=gs.ResponseProblem(m,*candidate,T,96,player)
        v96,r96=gs.local_best_response(pp96,seed+300,starts=3)
        val,g=pp96.value_gradient(v96)
        fine=self.one_audit(m,candidate,T,96,player,dict(objective=val,
            residual=pp96.projected_residual(v96,g),violation=pp96.violation(v96),
            all_starts_success=all(t['success'] for t in r96)),
            pp96.value_gradient(pp96.initial)[0],v96,'H96_fixed_candidate')
        self.timing.append(dict(**self.context,item='precision_audit_total',seconds=time.perf_counter()-ts))
        write_json(folder/'decision.json',dict(passed=bool(good and fine),online_seconds=elapsed,
            spread=spread,all_optimizer_calls_success=success,seed=seed,x0=m.x0.tolist(),
            K=len(u[0]),T=T,controls=[x.tolist() for x in candidate],
            initial_selected_controls=[x.tolist() for x in original]))
        return candidate, bool(good and fine)


def execute(mpre, mpost, u, H):
    """Per-slot execution using the existing augmented RK4, no state reset."""
    x = mpre.x0.copy(); parts = {p:0. for p in PARTS}
    states=[x.copy()]; times=[0.]; boundaries=[]; continuity=[]
    costs=[]
    for k in range(6):
        m = replace(mpre if k<3 else mpost, x0=x.copy())
        continuity.append(float(np.max(abs(m.x0-x))))
        sim = simulate(m, *(v[k:k+1] for v in u), DT, H)
        times.extend((k*DT+sim['times'][1:]).tolist())
        states.extend(sim['states'][1:]); x=sim['states'][-1].copy()
        for p in PARTS:
            if not p.startswith('terminal_'):
                parts[p]+=sim['parts'][p]
        costs.append(parts.copy()); boundaries.append(x.copy())
    parts['terminal_defense']=float(mpost.omega@x)
    parts['terminal_attacker']=float(mpost.nu@x)
    return dict(times=np.array(times),states=np.array(states),parts=parts,
        slot_costs=costs,boundaries=boundaries,continuity=max(continuity))


def objective(parts):
    return (sum(parts[p] for p in ('security','business','isolation','recovery','terminal_defense')),
        parts['attacker_value']-parts['attacker_effort']+parts['terminal_attacker'])


def preflight(out):
    checks=[]
    corehash={str(p):sha(p) for p in Path('src').glob('*.py')}
    snapshot=Path('results/work_d4/p0_1_fixed_attack/run01/source_snapshot/src')
    for name in ('core.py','game_solver.py','matched_mechanism.py','supplement_c2.py'):
        checks.append(dict(check=f'D4_snapshot:{name}',passed=sha(Path('src')/name)==sha(snapshot/name)))
    for B in (1.2,.6,1.8):
        source=Path(f'results/matched_mechanism/run01/seed11_B{B}_unequal_high_at_node3')
        m=load_model(source/'model.json');u=load_controls(source/'fine/controls.json')
        validate_model(m);check_controls(m,*u)
        assert m.n==6 and m.B==B and m.A==.8 and np.count_nonzero(m.beta)==8
        checks.append(dict(check=f'original_inputs:B{B}',passed=True))
    # Sensitivity validation at all three actual remaining-horizon dimensions.
    m=load_model(Path('results/matched_mechanism/run01/seed11_B1.2_unequal_high_at_node3/model.json'))
    m=replace(m,alpha=np.array([.5,.25,0,0,0,0]),x0=np.array([.15,.12,.07,.05,.02,.01]))
    for K in (3,2,1):
        u=random_pair(m,K,20261112+K)
        for player in ('D','A'):
            pr=gs.ResponseProblem(m,*u,K*DT,48,player)
            v=pr.initial.copy();value,g=pr.value_gradient(v)
            errors=[]
            for index in (0,len(v)-1):
                delta=np.zeros_like(v);delta[index]=1e-6
                fd=(pr.value_gradient(v+delta)[0]-pr.value_gradient(v-delta)[0])/2e-6
                errors.append(abs(fd-g[index]))
            sim=simulate(m,*u,K*DT,48)
            error=abs(value-(sim['J_D'] if player=='D' else -sim['J_A']))
            checks.append(dict(check=f'K{K}:{player}:gradient_objective',value=max(errors+[error]),
                threshold=1e-6,passed=bool(max(errors+[error])<=1e-6)))
    csv(out/'interface_checks.csv',checks)
    write_json(out/'preflight.json',dict(passed=all(x['passed'] for x in checks),checks=checks,
        core_source_hashes=corehash))
    assert all(x['passed'] for x in checks)


def run_budget(run, B, b):
    start=time.perf_counter(); out=run.out/f'B{B}';out.mkdir()
    source=Path(f'results/matched_mechanism/run01/seed11_B{B}_unequal_high_at_node3')
    mpre=load_model(source/'model.json'); old=load_controls(source/'fine/controls.json')
    mpost=replace(mpre,alpha=np.array([.5,.25,0,0,0,0]))
    dump_model(out/'model_pre.json',mpre);dump_model(out/'model_post.json',mpost)
    prefix=simulate(mpre,*(v[:3] for v in old),5,48)
    xevent=prefix['states'][-1].copy();sub=replace(mpost,x0=xevent)
    write_json(out/'common_prefix.json',dict(x_event=xevent.tolist(),parts=prefix['parts'],
        J_D=prefix['J_D'],J_A=prefix['J_A'],controls=[v[:3].tolist() for v in old]))
    run.context=dict(B=B,evaluation='E1',method='E1_generator',update=0)
    tail=tuple(v[3:].copy() for v in old)
    e1folder=out/'E1_generation';e1folder.mkdir()
    e1,attackpass=run.unilateral(sub,tail,'A',20261112+1000*b+100,e1folder,strong=True)
    evaluations={'E0':np.tile([.4,.4,0,0,0,0],(3,1)), 'E1':e1[0].copy()}
    write_json(out/'frozen_attacks.json',{k:v.tolist() for k,v in evaluations.items()})
    passed=attackpass
    for e,(ename,attack) in enumerate(evaluations.items()):
        for k in range(3):
            for node in range(6):
                run.attacks.append(dict(B=B,evaluation=ename,slot=k+3,node=node,a_actual=attack[k,node],
                    source='uniform' if ename=='E0' else 'local_response_to_P'))
        values={}
        for method in ('P','G','R'):
            run.context=dict(B=B,evaluation=ename,method=method,update=-1)
            u=[v.copy() for v in old];u[0][3:]=attack
            x=xevent.copy();warm=tail;ok=True
            for j in range(3):
                if method=='P':
                    break
                run.context=dict(B=B,evaluation=ename,method=method,update=j)
                folder=out/f'{ename}_{method}'/f'update{j}';folder.mkdir(parents=True)
                model=replace(mpost,x0=x.copy());dump_model(folder/'model_restart.json',model)
                seed=20261112+1000*b+100*e+10*j
                if method=='G':
                    plan,taskpass=run.game(model,warm,seed,folder,j)
                else:
                    observed=old[0][2] if j==0 else attack[j-1]
                    prediction=np.tile(observed,(3-j,1))
                    warm=(prediction,warm[1],warm[2])
                    plan,taskpass=run.unilateral(model,warm,'D',seed,folder,j)
                run.tasks.append(dict(**run.context,passed=taskpass,absolute_time=(3+j)*DT,K=3-j))
                run.save()
                if not taskpass:
                    ok=False;passed=False;break
                u[1][3+j],u[2][3+j]=plan[1][0],plan[2][0]
                sim=simulate(model,attack[j:j+1],plan[1][:1],plan[2][:1],DT,48)
                x=sim['states'][-1].copy();warm=tuple(v[1:].copy() for v in plan)
                if time.perf_counter()-start>1800:
                    write_json(out/'timeout.json',dict(status='GROUP_TIME_LIMIT',seconds=time.perf_counter()-start))
                    run.save();return False
            if not ok:
                write_json(out/f'{ename}_{method}_failed.json',dict(status='NUMERICAL_FAIL',
                    reason='No qualified decision; trajectory stopped; no fallback counted'))
                continue
            run.context=dict(B=B,evaluation=ename,method=method,update=-1,phase='execution_evaluation')
            ts=time.perf_counter();sims={H:execute(mpre,mpost,u,H) for H in (48,96,192)}
            run.timing.append(dict(**run.context,item='fixed_execution_reintegration_total',seconds=time.perf_counter()-ts))
            primary=sims[48];err=0.
            for H in (96,192):
                fine=sims[H]
                err=max(err,float(np.max(abs(primary['states']-fine['states'][::H//48]))),
                    max(abs(primary['parts'][p]-fine['parts'][p]) for p in PARTS),
                    max(abs(a-bb) for a,bb in zip(objective(primary['parts']),objective(fine['parts']))))
            state_error=max(0.,float(-primary['states'].min()),float(primary['states'].max()-1))
            check_controls(mpre,*u)
            violation=max(0.,float((u[1]@mpre.b_s+u[2]@mpre.b_r-B).max()),
                float((u[0]@mpre.d_a-mpre.A).max()),max(float((-v).max()) for v in u),
                max(float((v-1).max()) for v in u),float(abs(u[0][:,~mpre.entry]).max()))
            for check,value,threshold in [('reintegration',err,1e-6),('state_domain',state_error,1e-10),
                    ('continuity',primary['continuity'],1e-12),('control_violation',violation,1e-10)]:
                run.quality.append(dict(**run.context,check=check,value=value,threshold=threshold,passed=value<=threshold))
                passed=passed and value<=threshold
            for k in range(6):
                use=float(u[1][k]@mpre.b_s+u[2][k]@mpre.b_r)
                for node in range(6):
                    run.executed.append(dict(B=B,evaluation=ename,method=method,slot=k,node=node,
                        t_start=k*DT,t_end=(k+1)*DT,a_actual=u[0][k,node],s=u[1][k,node],r=u[2][k,node],
                        resource_use=use,budget_slack=B-use,alpha0=.25 if k<3 else .5))
            for H,sim in sims.items():
                for t,state in zip(sim['times'],sim['states']):
                    run.trajectories.append(dict(B=B,evaluation=ename,method=method,H=H,t=t,
                        **{f'x{i}':float(state[i]) for i in range(6)}))
                pre=sim['slot_costs'][2]
                for period,parts in [('pre',pre),('post',{p:sim['parts'][p]-pre[p] for p in PARTS}),('full',sim['parts'])]:
                    jd,ja=objective(parts)
                    run.objectives.append(dict(B=B,evaluation=ename,method=method,H=H,period=period,
                        J_D=jd,J_A=ja,**parts))
                    if H==48:
                        values[(method,period)]=jd
                csv(out/f'{ename}_{method}_cumulative_costs_H{H}.csv',
                    [dict(slot=k,t_end=(k+1)*DT,**p) for k,p in enumerate(sim['slot_costs'])])
            write_json(out/f'{ename}_{method}_executed.json',[v.tolist() for v in u])
            print('EXECUTED',B,ename,method,objective(primary['parts'])[0],flush=True)
            run.save()
        if all((m,'full') in values for m in ('P','G','R')):
            for period in ('post','full'):
                jp,jg,jr=(values[(m,period)] for m in ('P','G','R'))
                run.comparisons.append(dict(B=B,evaluation=ename,period=period,J_D_P=jp,J_D_G=jg,J_D_R=jr,
                    delta_P_to_G=jp-jg,delta_R_to_G=jr-jg,
                    percent_P_to_G=100*(jp-jg)/jp,percent_R_to_G=100*(jr-jg)/jr))
    # Fairness from saved actual schedules, including the identical prefix.
    for ename in evaluations:
        arrays=[load_controls(out/f'{ename}_{method}_executed.json') for method in ('P','G','R')
            if (out/f'{ename}_{method}_executed.json').exists()]
        fair=len(arrays)==3 and all(np.array_equal(arrays[0][0],a[0]) for a in arrays[1:])
        fair=fair and all(all(np.array_equal(arrays[0][v][:3],a[v][:3]) for v in (1,2)) for a in arrays[1:])
        run.quality.append(dict(B=B,evaluation=ename,check='common_attack_and_prefix',passed=fair))
        passed=passed and fair
    write_json(out/'budget_gate.json',dict(passed=bool(passed),seconds=time.perf_counter()-start,
        decision='EXPANSION_ALLOWED' if passed else 'STOP_NO_EXPANSION'))
    run.save();return bool(passed)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);args=ap.parse_args()
    os.chdir(ROOT);out=Path(args.output);out.mkdir(parents=True,exist_ok=False)
    started=time.perf_counter()
    sources=[*Path('src').glob('*.py'),*Path('paper/work_d5').rglob('*'),
        Path('02_MODEL_SPEC.md'),Path('DECISIONS.md'),Path('reviews/APPROVAL_LOG.md'),
        Path('paper/work_d4/decision_reorientation_20261112/03_minimal_experiment_protocol.md')]
    for B in (1.2,.6,1.8):
        folder=Path(f'results/matched_mechanism/run01/seed11_B{B}_unequal_high_at_node3')
        sources.extend([folder/'model.json',folder/'fine/controls.json',folder/'fine_audit.json',folder/'case_audit.json'])
    sources=[p for p in sources if p.is_file() and '__pycache__' not in str(p)]
    protected=[p for base in ('src','configs','tests','paper/work_d3','results/matched_mechanism',
        'results/work_d4') for p in Path(base).rglob('*') if p.is_file() and '__pycache__' not in str(p)]
    protected.append(Path('02_MODEL_SPEC.md'))
    hashes={str(p):sha(p) for p in protected}
    write_json(out/'protected_before.json',hashes)
    for p in sources:
        target=out/'source_snapshot'/p;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target)
    shutil.copy2('paper/work_d5/experiment_protocol.md',out/'experiment_protocol.md')
    meta=dict(status='RUNNING',started_utc=now(),command=sys.argv,python=sys.version,
        platform=platform.platform(),processor=platform.processor(),cpu_count=os.cpu_count(),
        numpy=np.__version__,scipy=scipy.__version__,pandas=pd.__version__,pid=os.getpid(),
        thread_env={k:os.environ.get(k) for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS')},
        source_hashes={str(p):sha(p) for p in sources},historical_offline_seconds=None,
        historical_offline_note='Saved original plan reused; elapsed offline wall time not reconstructed',
        strict_global_nash_certificate=False,physical_time_calibration=False)
    write_json(out/'metadata.json',meta)
    try:
        preflight(out);run=Run(out)
        for b,B in enumerate((1.2,.6,1.8)):
            if not run_budget(run,B,b):
                meta['status']='NUMERICAL_GATE_FAILED';break
        else:
            meta['status']='COMPLETED_NUMERICAL_PASS'
        run.save()
    except Exception as e:
        meta.update(status='FAILED',error=repr(e));raise
    finally:
        changed=[p for p,h in hashes.items() if not Path(p).exists() or sha(p)!=h]
        write_json(out/'protected_after.json',dict(checked=len(hashes),changed=changed,passed=not changed))
        meta.update(ended_utc=now(),seconds=time.perf_counter()-started)
        write_json(out/'metadata.json',meta)
        print(json.dumps({k:v for k,v in meta.items() if k not in ('source_hashes',)}),flush=True)


if __name__=='__main__':
    main()
