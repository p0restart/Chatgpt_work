"""One defense perturbation -> attacker BR -> defender BR; no game iteration.

Run in any extracted package: python run_experiment.py --out rerun
Only the bundled, hash-checked D7 core and response solver are imported.
"""
from pathlib import Path
import argparse, hashlib, json, platform, sys, time, traceback
from datetime import datetime
from zoneinfo import ZoneInfo
import numpy as np
import pandas as pd
import scipy
from scipy.integrate import solve_ivp

HERE = Path(__file__).resolve().parent
sys.path.insert(0,str(HERE/'runtime'))
from src.core import Model, validate_model, check_controls, simulate
from src.game_solver import ResponseProblem, local_best_response

T, K, H, SEED = 10., 6, 48, 20261115
ASSETS = ['API网关','Web应用','订单处理','身份认证','核心数据库','后台管理']
PARTS = ['security','business','isolation','recovery','attacker_value','attacker_effort']
def now(): return datetime.now(ZoneInfo('Asia/Shanghai')).isoformat()
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,obj): p.write_text(json.dumps(obj,indent=2,ensure_ascii=False,allow_nan=False),encoding='utf-8')
def csv(p,rows): pd.DataFrame(rows).to_csv(p,index=False,encoding='utf-8-sig',float_format='%.17g')
def dist(x,y): return float(np.max(np.abs(np.asarray(x)-np.asarray(y))))
def main(out):
    out.mkdir(exist_ok=False,parents=True)
    log=(out/'run.log').open('w',encoding='utf-8',buffering=1)
    def say(s):
        line=f'{now()} {s}'
        print(line,flush=True); log.write(line+'\n')
    started=time.perf_counter()
    try:
        manifest=json.loads((HERE/'input_manifest.json').read_text(encoding='utf-8'))
        for name,info in manifest['sources'].items():
            p=HERE/('runtime/'+name if name.startswith('src/') else 'inputs/'+name)
            assert sha(p)==info['sha256'],name
        d7=HERE/'inputs/paper/work_d7'
        static=d7/'results/static/B1.2'
        d=json.loads((static/'model.json').read_text())
        m=Model(**{k:np.array(v,dtype=bool if k=='entry' else float) if isinstance(v,list) else v for k,v in d.items()})
        validate_model(m)
        original=tuple(np.array(v,dtype=float) for v in json.loads((static/'G_controls.json').read_text()))
        assert all(v.shape==(6,6) for v in original)
        assert m.n==6 and m.B==1.2 and m.A==.8
        assert np.array_equal(m.x0,[.1,0,0,0,0,0]) and np.array_equal(m.entry,[True,True,False,False,False,False])
        expected_beta=np.zeros((6,6))
        for j,i,w in [(0,2,.08),(0,3,.09),(1,2,.1),(3,2,.11),(3,4,.07),(3,5,.12),(2,4,.1),(5,4,.05)]: expected_beta[j,i]=w
        assert np.array_equal(m.beta,expected_beta)
        historical=json.loads((d7/'sources/source_manifest.json').read_text())
        source_match={name:manifest['sources'][name]['sha256']==historical[name.replace('/','\\')]['sha256'] for name in ['src/core.py','src/game_solver.py']}
        assert all(source_match.values())
        check_controls(m,*original)
        baseline=simulate(m,*original,T,H)
        old=json.loads((static/'G_evaluation.json').read_text())
        reproduction_error=max(abs(baseline[p]-old[p]) for p in ['J_D','J_A'])
        assert reproduction_error<=1e-12
        assert m.b_r[0]==m.b_r[1]
        perturb_checks=[]; plans=None; delta=None
        for candidate in [.05,.025]:
            proposed={'baseline':tuple(v.copy() for v in original)}
            valid=True
            for name,sign in [('positive',1),('negative',-1)]:
                u=tuple(v.copy() for v in original)
                u[2][1:4,0]-=sign*candidate
                u[2][1:4,1]+=sign*candidate
                violation=max(0.,float(max(v.max()-1 for v in u)),float(max(-v.min() for v in u)),float(np.max(u[1]@m.b_s+u[2]@m.b_r-m.B)))
                ok=violation<=1e-10
                perturb_checks.append(dict(delta=candidate,scenario=name,violation=violation,feasible=ok,
                    capacity_change=dist(u[1]@m.b_s+u[2]@m.b_r,original[1]@m.b_s+original[2]@m.b_r)))
                valid=valid and ok
                proposed[name]=u
            if valid: delta=candidate;plans=proposed;break
        dump(out/'perturbation_preflight.json',dict(equal_recovery_capacity=True,checks=perturb_checks,selected_delta=delta))
        if plans is None: raise RuntimeError('Both preregistered perturbations infeasible; no clipping permitted')
        env=dict(started=now(),python=sys.version,executable=sys.executable,platform=platform.platform(),
            numpy=np.__version__,scipy=scipy.__version__,pandas=pd.__version__,argv=sys.argv,
            solver='original D7 SLSQP; maxiter=300; ftol=1e-10; starts=3 (incumbent, zero, random)',
            T=T,K=K,H=H,seed=SEED,source_hashes_match_D7=source_match)
        dump(out/'environment.json',env)
        (out/'requirements.txt').write_text(f'numpy=={np.__version__}\nscipy=={scipy.__version__}\npandas=={pd.__version__}\n',encoding='utf-8')
        protocol=f'''# E-EXP实验方案与基准参数核查

登记时间：{now()}；本文件写入后才进行优化。用户本轮指令已明确授权这一实验范围；新结果等待用户和后续审阅者审查，不登记为G2结果批准。论文树只读。

原始输入来自D7 results/static/B1.2/model.json与G_controls.json，未使用论文均值、图形反推。输入副本与SHA256见input_manifest.json。core.py、game_solver.py与D7运行前SHA完全相同：{source_match}。

n=6,T=10,K=6,B=1.2,A=0.8,x0=(0.1,0,0,0,0,0)，入口v1/v2。8条传播边与模型副本逐项核对。完整参数在inputs内model.json。原ODE、目标、容量和控制上界1全部保留；状态含义为受损比例。复算J_D={baseline['J_D']:.15g}，J_A={baseline['J_A']:.15g}，与原始记录最大差{reproduction_error:.3g}。

正向：仅1基编号的第2/3/4区间r_v1减δ、r_v2加δ；反向相反。本次δ={delta}，两方向均可行；b_r(v1)=b_r(v2)=1，逐槽容量不变。不裁剪控制，不改其余参数。delta=0.025仅在0.05失败时检查。

依次固定baseline/positive/negative防御，以原a_G为暖初值做攻击响应；再固定positive/negative攻击响应，以原u_G为暖初值做防御响应。仅一次链条，不调用交替博弈。每次原local_best_response：三初值=当前计划、全零、随机；随机生成和可行化沿用原函数，主种子20261115，五任务依次偏移0/10/20/30/40。返回值仍用原函数的可行且目标不劣准则选择。

RK4每槽H48主求解；每任务另在相同对手下以H48选中响应作暖初值，H96三初值复核（seed+300）。保存所有起点/返回控制、退出码、目标、投影残差与耗时。H96返回控制只作精度复核，不替代主结果。每个固定控制对做H48/96/192复算及独立写出的DOP853分槽积分(rtol=1e-11,atol=1e-13)，比较全部H48时间点状态和成本分项，不跨控制不连续点积分。

继承D7门槛：违反≤1e-10、状态[-1e-10,1+1e-10]、投影残差≤1e-4、多初值/积分精化控制差≤1e-3、目标/状态/分项积分差≤1e-6。响应复核已发现改善/(1+|J|)≤1e-7。原a_G是否还可改善单独报告；不能以扰动后对a_G的改善直接解释扰动作用。扰动作用另以a_BR(u±)对a_BR(u_G)比较。

控制误差经验包络e取该任务H48/H96全部返回解与H48选中解的最大绝对差。攻击扰动差超过e_perturbed+e_baseline才称超过观测数值误差；此包络为经验诊断，不是数学误差上界。防御控制对原u_G的差还对比D7原三路径spread及1e-3门槛；正反防御响应的差以各自包络之和检查。小变化和负结果原样保留。收益改善报告绝对值和以同一对手下原目标绝对值为分母的百分比。

本实验是受限分段常值控制类的局部数值最佳响应，三初值一致不证明全局最优、Nash存在/唯一或全局收敛。没有新增拓扑、容量、成本参数敏感性，也没有生产云验证；不做统计显著性检验。仅生成一张主要汇总表，不另作图。
'''
        (out/'protocol_and_baseline.md').write_text(protocol,encoding='utf-8')
        defense_rows=[]
        for label,u in plans.items():
            for k in range(K):
                for i in range(m.n):
                    defense_rows.append(dict(scenario=label,slot=k+1,t_start=k*T/K,t_end=(k+1)*T/K,asset=i+1,name=ASSETS[i],
                        isolation=u[1][k,i],recovery=u[2][k,i],delta_isolation=u[1][k,i]-original[1][k,i],delta_recovery=u[2][k,i]-original[2][k,i]))
        csv(out/'defense_original_and_perturbed.csv',defense_rows)
        baseline_resource=[dict(slot=k+1,attack=float(original[0][k]@m.d_a),defense=float(original[1][k]@m.b_s+original[2][k]@m.b_r)) for k in range(K)]
        dump(out/'baseline_reproduction.json',dict(J_D=baseline['J_D'],J_A=baseline['J_A'],parts=baseline['parts'],reproduction_error=reproduction_error,resources=baseline_resource))
        say(f'Preflight passed; delta={delta}; baseline JD={baseline["J_D"]:.12g}, JA={baseline["J_A"]:.12g}')
        attempts=[]; convergence=[]; errors={}; solutions={}
        def solve(label,u,player,seed):
            say(f'Start {label}: player={player}, H48 three starts')
            pr=ResponseProblem(m,*u,T,H,player)
            v,raw=local_best_response(pr,seed=seed,starts=3,maxiter=300,ftol=1e-10)
            selected=pr.schedules(v)
            val,grad=pr.value_gradient(v)
            say(f'{label} H48 done; objective={val:.12g}; start H96 precision audit')
            fine=ResponseProblem(m,*selected,T,96,player)
            vf,rawf=local_best_response(fine,seed=seed+300,starts=3,maxiter=300,ftol=1e-10)
            allraw=[]
            for h,rr,problem in [(48,raw,pr),(96,rawf,fine)]:
                for row in rr:
                    allraw.append(dict(task=label,player=player,H=h,seed=seed if h==48 else seed+300,**row))
                    attempts.append({k:v for k,v in allraw[-1].items() if k not in ['initial_control','control']})
            dump(out/f'{label}_optimizer_raw.json',allraw)
            csv(out/'optimizer_attempts.csv',attempts)
            envelope=max(dist(np.array(row['control']),v) for row in allraw)
            coarse_spread=max(dist(np.array(row['control']),v) for row in raw)
            fine_delta=dist(v,vf)
            refined_base=fine.value_gradient(fine.initial)[0]
            refined_value=fine.value_gradient(vf)[0]
            improvement=refined_base-refined_value
            row=dict(task=label,player=player,objective=val,projected_residual=pr.projected_residual(v,grad),
                max_attempt_residual=max(r['projected_residual'] for r in allraw),
                violation=pr.violation(v),all_starts_success=all(r['success'] for r in allraw),
                objective_spread_H48=float(np.ptp([r['objective'] for r in raw])),
                control_spread_H48=coarse_spread,H96_control_difference=fine_delta,control_error_envelope=envelope,
                H96_discovered_improvement=max(0.,improvement),H96_relative_improvement=max(0.,improvement)/(1+abs(refined_base)))
            row['passed']=bool(row['all_starts_success'] and row['max_attempt_residual']<=1e-4 and row['violation']<=1e-10 and envelope<=1e-3 and row['H96_relative_improvement']<=1e-7)
            convergence.append(row);errors[label]=envelope
            csv(out/'convergence.csv',convergence)
            dump(out/f'{label}_selected_controls.json',[z.tolist() for z in selected])
            if not row['passed']: raise RuntimeError(f'Numerical quality failed: {label}; no dependent solves performed')
            say(f'{label} passed; residual={row["projected_residual"]:.3g}, error envelope={envelope:.3g}')
            return selected
        for j,(label,u) in enumerate(plans.items()):
            solutions['A_'+label]=solve('A_'+label,u,'A',SEED+10*j)
        for j,label in enumerate(['positive','negative']):
            fixed=(solutions['A_'+label][0],original[1],original[2])
            solutions['D_'+label]=solve('D_'+label,fixed,'D',SEED+30+10*j)
        attack_rows=[];defender_rows=[];difference_rows=[]
        for label in plans:
            a=solutions['A_'+label][0]
            for k in range(K):
                for i in range(m.n):
                    attack_rows.append(dict(scenario=label,slot=k+1,asset=i+1,name=ASSETS[i],attack=a[k,i],
                        delta_from_aG=a[k,i]-original[0][k,i],delta_from_baseline_BR=a[k,i]-solutions['A_baseline'][0][k,i]))
            for k in range(K):
                for i in range(2):
                    difference_rows.append(dict(player='A',scenario=label,slot=k+1,asset=i+1,channel='attack',
                        value=a[k,i],reference=original[0][k,i],difference=a[k,i]-original[0][k,i]))
        for label in ['positive','negative']:
            u=solutions['D_'+label]
            for k in range(K):
                for i in range(m.n):
                    defender_rows.append(dict(scenario=label,slot=k+1,t_start=k*T/K,t_end=(k+1)*T/K,asset=i+1,name=ASSETS[i],
                        isolation=u[1][k,i],recovery=u[2][k,i],delta_isolation=u[1][k,i]-original[1][k,i],delta_recovery=u[2][k,i]-original[2][k,i]))
                    for z,channel in [(1,'isolation'),(2,'recovery')]:
                        difference_rows.append(dict(player='D',scenario=label,slot=k+1,asset=i+1,channel=channel,
                            value=u[z][k,i],reference=original[z][k,i],difference=u[z][k,i]-original[z][k,i]))
        csv(out/'attacker_best_responses.csv',attack_rows)
        csv(out/'defender_best_responses.csv',defender_rows)
        csv(out/'control_differences.csv',difference_rows)
        allpairs={**{'input_'+k:v for k,v in plans.items()},**solutions}
        objective_rows=[];constraint_rows=[];integration_rows=[];state_rows=[]
        # Independent implementation: loop-based exposure and explicit cost equations.
        def independent(u):
            y=np.r_[m.x0,np.zeros(6)]; states=[m.x0.copy()]; minimum=float(m.x0.min());maximum=float(m.x0.max())
            for k in range(K):
                a,s,r=[v[k] for v in u]
                def fun(t,z):
                    x=z[:6];exposure=m.alpha*a
                    for j in range(6):
                        for i in range(6): exposure[i]+=m.beta[j,i]*(1-m.epsilon[j]*s[j])*x[j]
                    dx=(1-x)*exposure-(m.delta+m.gamma*r)*x
                    costs=[sum(m.q*x),sum(m.h*s),sum(m.c_s*s*s)/2,sum(m.c_r*r*r)/2,sum(m.g*x),sum(m.c_a*a*a)/2]
                    return np.r_[dx,costs]
                times=np.linspace(k*T/K,(k+1)*T/K,H+1)
                sol=solve_ivp(fun,(times[0],times[-1]),y,method='DOP853',rtol=1e-11,atol=1e-13,dense_output=True)
                assert sol.success
                minimum=min(minimum,float(sol.y[:6].min()));maximum=max(maximum,float(sol.y[:6].max()))
                evaluated=sol.sol(times)
                states.extend(evaluated[:6,1:].T);y=sol.y[:,-1]
            jd=float(sum(y[6:10])+m.omega@y[:6]);ja=float(y[10]-y[11]+m.nu@y[:6])
            return np.array(states),y[6:],jd,ja,minimum,maximum
        say('All five response tasks complete; auditing 8 fixed control pairs')
        for label,u in allpairs.items():
            check_controls(m,*u)
            sims={h:simulate(m,*u,T,h) for h in [48,96,192]};s=sims[48]
            for k in range(K):
                constraint_rows.append(dict(pair=label,slot=k+1,attack_resource=float(u[0][k]@m.d_a),
                    defense_resource=float(u[1][k]@m.b_s+u[2][k]@m.b_r),
                    attack_slack=float(m.A-u[0][k]@m.d_a),defense_slack=float(m.B-u[1][k]@m.b_s-u[2][k]@m.b_r),
                    control_min=float(min(v[k].min() for v in u)),control_max=float(max(v[k].max() for v in u))))
            for h,sim in sims.items():
                objective_rows.append(dict(pair=label,integrator='RK4',H=h,J_D=sim['J_D'],J_A=sim['J_A'],**sim['parts']))
                for t,x in zip(sim['times'],sim['states']):
                    state_rows.append(dict(pair=label,integrator='RK4',H=h,t=t,**{f'x{i+1}':x[i] for i in range(6)}))
                if h>48:
                    integration_rows.append(dict(pair=label,comparison=f'RK4_48_vs_{h}',state_error=dist(s['states'],sim['states'][::h//48]),
                        objective_error=max(abs(s[p]-sim[p]) for p in ['J_D','J_A']),parts_error=max(abs(s['parts'][p]-sim['parts'][p]) for p in s['parts']),
                        state_min=float(sim['states'].min()),state_max=float(sim['states'].max())))
            x,c,jd,ja,lo,hi=independent(u)
            for t,xx in zip(s['times'],x): state_rows.append(dict(pair=label,integrator='DOP853',H=0,t=t,**{f'x{i+1}':xx[i] for i in range(6)}))
            objective_rows.append(dict(pair=label,integrator='DOP853',H=0,J_D=jd,J_A=ja,**dict(zip(PARTS,c)),terminal_defense=float(m.omega@x[-1]),terminal_attacker=float(m.nu@x[-1])))
            integration_rows.append(dict(pair=label,comparison='RK4_48_vs_DOP853',state_error=dist(s['states'],x),
                objective_error=max(abs(s['J_D']-jd),abs(s['J_A']-ja)),parts_error=max(abs(s['parts'][p]-c[j]) for j,p in enumerate(PARTS)),
                state_min=min(lo,float(x.min()),float(s['states'].min())),state_max=max(hi,float(x.max()),float(s['states'].max()))))
        for row in integration_rows: row['passed']=bool(max(row[p] for p in ['state_error','objective_error','parts_error'])<=1e-6 and row['state_min']>=-1e-10 and row['state_max']<=1+1e-10)
        csv(out/'objectives_all_integrators.csv',objective_rows)
        csv(out/'constraints_by_slot.csv',constraint_rows)
        csv(out/'integration_audit.csv',integration_rows)
        csv(out/'state_trajectories.csv',state_rows)
        summaries=[]
        for label,u in plans.items():
            ab=solutions['A_'+label]
            before=simulate(m,*u,T,H);after=simulate(m,*ab,T,H)
            a_gain=after['J_A']-before['J_A']
            a_effect=dist(ab[0],solutions['A_baseline'][0])
            a_noise=errors['A_'+label]+errors['A_baseline']
            row=dict(scenario=label,delta_recovery=0 if label=='baseline' else delta,
                JA_original_attack=before['J_A'],JA_BR=after['J_A'],JA_improvement=a_gain,
                JA_improvement_percent=100*a_gain/abs(before['J_A']),max_attack_change_from_aG=dist(ab[0],original[0]),
                max_attack_change_from_baseline_BR=a_effect,attack_comparison_error_envelope=a_noise,
                attack_effect_exceeds_observed_error=bool(a_effect>a_noise))
            if label!='baseline':
                ub=solutions['D_'+label]; fixed=(ab[0],original[1],original[2])
                dbefore=simulate(m,*fixed,T,H);dafter=simulate(m,*ub,T,H)
                d_gain=dbefore['J_D']-dafter['J_D']
                dchange=max(dist(ub[z],original[z]) for z in [1,2])
                dnoise=errors['D_'+label]+max(1e-3,json.loads((static/'G/decision.json').read_text())['spread'])
                row.update(JD_original_defense=dbefore['J_D'],JD_BR=dafter['J_D'],JD_improvement=d_gain,
                    JD_improvement_percent=100*d_gain/abs(dbefore['J_D']),max_isolation_change=dist(ub[1],original[1]),
                    max_recovery_change=dist(ub[2],original[2]),max_defense_change=dchange,
                    defense_error_reference=dnoise,defense_change_exceeds_error_reference=bool(dchange>dnoise))
            summaries.append(row)
        csv(out/'payoff_and_control_summary.csv',summaries)
        a_pm=dist(solutions['A_positive'][0],solutions['A_negative'][0])
        d_pm=max(dist(solutions['D_positive'][z],solutions['D_negative'][z]) for z in [1,2])
        comparison=dict(positive_negative_attack_distance=a_pm,attack_error_sum=errors['A_positive']+errors['A_negative'],
            positive_negative_defense_distance=d_pm,defense_error_sum=errors['D_positive']+errors['D_negative'])
        comparison['attack_difference_resolved']=bool(a_pm>comparison['attack_error_sum'])
        comparison['defense_difference_resolved']=bool(d_pm>comparison['defense_error_sum'])
        dump(out/'positive_negative_comparison.json',comparison)
        passed=bool(all(r['passed'] for r in convergence+integration_rows))
        metrics=dict(status='SUCCESS' if passed else 'AUDIT_FAILED',completed=now(),seconds=time.perf_counter()-started,
            delta=delta,response_tasks=5,optimizer_calls=len(attempts),all_slsqp_success=all(r['success'] for r in attempts),
            max_projected_residual=max(r['projected_residual'] for r in attempts),
            max_control_error_envelope=max(errors.values()),max_integration_error=max(max(r[p] for p in ['state_error','objective_error','parts_error']) for r in integration_rows),
            state_min=min(r['state_min'] for r in integration_rows),state_max=max(r['state_max'] for r in integration_rows),
            max_constraint_violation=max(0.,max(-min(r['attack_slack'],r['defense_slack'],r['control_min'],1-r['control_max']) for r in constraint_rows)),
            baseline_reproduction_error=reproduction_error,comparison=comparison)
        dump(out/'verification.json',metrics)
        # One main table only. Full precision CSV is the source for this rounded presentation.
        table=['# 实验结论与主要结果','',f'执行状态：{metrics["status"]}；执行日期{now()}；δ={delta}。','',
            '|防御扰动|攻击收益J_A：原攻击→响应|攻击收益改善|攻击控制最大差/原a_G|攻击控制最大差/基准BR|防御损失J_D：原防御→响应|损失改善|隔离/恢复最大差|',
            '|---|---:|---:|---:|---:|---:|---:|---:|']
        for r in summaries:
            name={'baseline':'基准','positive':'正向','negative':'反向'}[r['scenario']]
            a=f'{r["JA_original_attack"]:.9f} → {r["JA_BR"]:.9f}'
            if r['scenario']=='baseline': dvalue=dg=du='—'
            else:
                dvalue=f'{r["JD_original_defense"]:.9f} → {r["JD_BR"]:.9f}'
                dg=f'{r["JD_improvement"]:.3g} ({r["JD_improvement_percent"]:.6g}%)'
                du=f'{r["max_isolation_change"]:.6g} / {r["max_recovery_change"]:.6g}'
            table.append(f'|{name}|{a}|{r["JA_improvement"]:.3g} ({r["JA_improvement_percent"]:.6g}%)|{r["max_attack_change_from_aG"]:.6g}|{r["max_attack_change_from_baseline_BR"]:.6g}|{dvalue}|{dg}|{du}|')
        table.extend(['',f'正反攻击响应最大差{a_pm:.9g}，两任务经验误差包络之和{comparison["attack_error_sum"]:.9g}；超过误差：{comparison["attack_difference_resolved"]}。正反防御响应最大差{d_pm:.9g}，经验误差之和{comparison["defense_error_sum"]:.9g}；超过误差：{comparison["defense_difference_resolved"]}。',
            '', '攻击收益比较始终固定同一防御；防御损失比较始终固定同一攻击。基准攻击重新求解用于区分原候选求解误差与扰动效应。防御响应不再约束为恢复转移，允许原模型内全部隔离和恢复控制调整。控制逐槽方向和资产分布见defender_best_responses.csv、control_differences.csv。',
            '', '收益改善是已发现的局部单方改善，不是未知全局gap的上界；控制变化与目标改善大小应分别解读。防御对原u_G差值可能含原候选误差，因此同时报告正反响应间差异和保守1e-3原候选参考。',
            '', '本结果只支持这个固定合成实例、δ和K=6策略类下的数值策略相互依赖性判断。多初值及精度检查为经验依据，不证明全局最优或Nash存在、唯一、全局收敛；未做连续控制全局搜索、跨机器独立优化复现或生产云实测。确定性优化初值不作为独立实验样本，不给统计显著性结论。',
            '', '结果供用户提交另一位论文审阅者；本轮停止于实验交付，不修改论文、不升级既有审批。'])
        (out/'results_and_limitations.md').write_text('\n'.join(table)+'\n',encoding='utf-8')
        (out/'numerical_audit.md').write_text(f'''# 数值约束与收敛精度审计

状态：{metrics['status']}。原始输入目标复算最大差{reproduction_error:.6g}。全部参数、状态、控制均未裁剪。

五任务×H48/H96×三初值，共{len(attempts)}次SLSQP。全部正常退出：{metrics['all_slsqp_success']}；最大投影残差{metrics['max_projected_residual']:.9g}。各次状态码、迭代数、目标、容量违反、投影残差及完整起点/终点分别保存optimizer_attempts.csv与五份*_optimizer_raw.json。convergence.csv保存已发现的进一步改善、多初值目标差与控制差、H96控制差和经验控制误差包络；全数通过原D7门槛：{all(r['passed'] for r in convergence)}。

8个固定控制对逐槽约束最大违反{metrics['max_constraint_violation']:.9g}。三组防御恢复转移保持逐槽用量不变，所有控制上下界合格。48条逐槽约束明细见constraints_by_slot.csv。状态最小{metrics['state_min']:.9g}、最大{metrics['state_max']:.9g}；RK4全部保存网格及DOP853内部接受步/共同网格均在允许区间。原模型在x_i=0时向量场非负，在x_i=1时非正（可行非负率和控制），亦支持连续状态域不变性。

8对×H48/96/192及DOP853共32组轨迹和目标。独立DOP853未调用core.dynamics、cost_rates或RK4函数，逐槽重启，比较全部H48共同网格、双方目标和六成本分项。24项比较均合格：{all(r['passed'] for r in integration_rows)}；最大状态/目标/分项绝对差{metrics['max_integration_error']:.9g}。见integration_audit.csv、objectives_all_integrators.csv、state_trajectories.csv。

最大经验控制误差包络{metrics['max_control_error_envelope']:.9g}。各扰动相对基准攻击BR的效果使用对应包络之和判别，见payoff_and_control_summary.csv。正反防御响应距离及对应误差见positive_negative_comparison.json。不将优化ftol直接当控制误差，也不将同初值停止直接当Nash。H96仅复核相同固定对手，没有新增交替博弈。

本次为同一执行环境中的独立方程实现与积分器复算；未声称第二研究者、第二机器或独立全流程优化复现。后续复现命令见README.md。历史不利结果未改写，论文保护核查由finalize.py另行完成。
''',encoding='utf-8')
        from interpret_controls import describe
        describe(out)
        say(f'Completed: {metrics["status"]}; elapsed={metrics["seconds"]:.1f}s')
        assert passed
    except Exception as exc:
        dump(out/'FAILED.json',dict(time=now(),error=repr(exc),traceback=traceback.format_exc()))
        say(f'FAILED: {exc!r}; preserved outputs, no automatic model changes')
        raise
    finally: log.close()
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--out',default='run01');args=ap.parse_args()
    destination=Path(args.out)
    main(destination if destination.is_absolute() else HERE/destination)
