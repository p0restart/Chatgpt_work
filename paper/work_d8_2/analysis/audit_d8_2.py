"""Author-side audit by independent fixed-control DOP853 integration; no optimization."""
from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
import numpy as np
import pandas as pd
from scipy.integrate import solve_ivp
from paper.work_d8_2.analysis.run_d8_2 import BASE,D7,STATIC,ROLL,PARTS,sha,csv,manifest,load_model,load_controls

def quality_table(folder,output):
    rows=[]
    aud=pd.read_csv(folder/'solver_audit.csv')
    limits={'relative_improvement':1e-7,'incumbent_residual':1e-4,'response_residual':1e-4,'response_distance':1e-3,'violation':1e-10}
    for idx,row in aud.iterrows():
        context={k:row[k] for k in ('B','evaluation','method','update','path','audit','player','H') if k in row and pd.notna(row[k])}
        for key,threshold in limits.items():
            if key in row and pd.notna(row[key]): rows.append(dict(**context,check=key,value=row[key],threshold=threshold,passed=row[key]<=threshold,source_row=idx))
        if 'all_starts_success' in row and pd.notna(row['all_starts_success']):
            val=0 if row['all_starts_success'] else 1
            rows.append(dict(**context,check='audit_exit_failures',value=val,threshold=0,passed=val==0,source_row=idx))
    q=pd.read_csv(folder/'quality.csv')
    rows+=q.to_dict('records')
    attempts=pd.read_csv(folder/'optimizer_attempts.csv')
    for idx,row in attempts.iterrows():
        context={k:row[k] for k in ('B','evaluation','method','update','path','player','H','call','start','seed') if k in row and pd.notna(row[k])}
        rows.append(dict(**context,check='optimizer_exit_failure',value=0 if row.success else 1,threshold=0,passed=bool(row.success),source_row=idx))
        rows.append(dict(**context,check='optimizer_control_violation',value=row.violation,threshold=1e-10,passed=row.violation<=1e-10,source_row=idx))
    for row in rows:row['experiment']=folder.name
    csv(output,rows)
    return rows

def independent(mpre,mpost,u,H,change_slot):
    """Reimplement augmented RHS and integrate each discontinuity separately."""
    kmax=len(u[0]);dt=10/kmax;y=np.r_[mpre.x0,np.zeros(6)];states=[y[:6].copy()];times=[0.];costs=[]
    for k in range(kmax):
        m=mpre if k<change_slot else mpost
        a,s,r=(v[k] for v in u)
        def rhs(t,z):
            x=z[:6]
            force=m.alpha*a+np.sum(m.beta*((1-m.epsilon*s)*x)[:,None],axis=0)
            dx=(1-x)*force-(m.delta+m.gamma*r)*x
            rates=np.array([sum(m.q*x),sum(m.h*s),sum(.5*m.c_s*s*s),sum(.5*m.c_r*r*r),sum(m.g*x),sum(.5*m.c_a*a*a)])
            return np.r_[dx,rates]
        grid=np.linspace(k*dt,(k+1)*dt,H+1)
        sol=solve_ivp(rhs,(k*dt,(k+1)*dt),y,method='DOP853',rtol=1e-12,atol=1e-14,t_eval=grid)
        assert sol.success
        times.extend(grid[1:]);states.extend(sol.y[:6,1:].T);y=sol.y[:,-1];costs.append(y[6:].copy())
    parts=dict(zip(['security','business','isolation','recovery','attacker_value','attacker_effort'],y[6:]))
    parts.update(terminal_defense=mpost.omega@y[:6],terminal_attacker=mpost.nu@y[:6])
    return dict(times=np.array(times),states=np.array(states),parts=parts,post=y[6:]-costs[change_slot-1] if 0<change_slot<kmax else None)

def audit_fixed():
    from src.core import simulate
    from paper.work_d5.analysis.run_replanning import execute
    rows=[];m=load_model(STATIC/'model.json');att=json.loads((BASE/'results/K12/cross_attacks.json').read_text())
    for method in ('G','F'):
        u=load_controls(BASE/f'K12_{method}_controls.json')
        for name,a in att.items():
            controls=(np.array(a),u[1],u[2]);rk=simulate(m,*controls,10,24);iv=independent(m,m,controls,24,12)
            rows.append(dict(experiment='A',method=method,evaluation=name,state_error=float(np.max(abs(rk['states']-iv['states']))),
                parts_error=max(abs(rk['parts'][p]-iv['parts'][p]) for p in PARTS)))
    pre=load_model(ROLL/'B1.2/model_pre.json');post=load_model(ROLL/'B1.2/model_post.json')
    for event in ('E0','E1'):
        u=load_controls(BASE/f'results/R_LAG/{event}_executed.json');rk=execute(pre,post,u,48);iv=independent(pre,post,u,48,3)
        rows.append(dict(experiment='B',method='R-LAG',evaluation=event,state_error=float(np.max(abs(rk['states']-iv['states']))),
            parts_error=max(abs(rk['parts'][p]-iv['parts'][p]) for p in PARTS)))
    for row in rows:row['threshold']=1e-6;row['passed']=max(row['state_error'],row['parts_error'])<=1e-6
    csv(BASE/'results/independent_fixed_control_audit.csv',rows)
    assert all(r['passed'] for r in rows)
    return rows

def comparisons():
    obj=pd.read_csv(BASE/'K12_vs_K6_objective_comparison.csv');diff=[]
    for method in ('G','F'):
        for level in range(3):
            a=obj[(obj.method==method)&(obj.K==6)&(obj.H==48*2**level)].iloc[0]
            b=obj[(obj.method==method)&(obj.K==12)&(obj.H==24*2**level)].iloc[0]
            for part in ['J_D','J_A',*PARTS]:diff.append(dict(method=method,integration_level=level,metric=part,K6=a[part],K12=b[part],difference=b[part]-a[part],relative_change=(b[part]-a[part])/abs(a[part]) if abs(a[part])>1e-12 else np.nan))
    csv(BASE/'results/K12/objective_changes.csv',diff)
    means=[]
    for method in ('G','F'):
        for k in (6,12):
            u=load_controls((STATIC/f'{method}_controls.json') if k==6 else (BASE/f'K12_{method}_controls.json'))
            for kind,data in [('isolation',u[1]),('recovery',u[2]),('resource',u[1]+u[2])]:
                avg=data.mean(axis=0)
                for node in range(6):means.append(dict(method=method,K=k,kind=kind,node=node,mean=avg[node],
                    rank=int(np.sum(avg>avg[node]+1e-8))+1,numerical_zero=bool(avg[node]<=1e-8),ranking_tolerance=1e-8))
    csv(BASE/'results/K12/asset_rankings.csv',means)
    cross6=pd.read_csv(STATIC/'cross_evaluation.csv');cross12=pd.read_csv(BASE/'K12_cross_evaluation.csv');cr=[]
    for k,frame in [(6,cross6),(12,cross12[cross12.H==24])]:
        for attack in ('a0','aG','aBR_F'):
            a=frame[(frame.method=='G')&(frame.attack==attack)].iloc[0];b=frame[(frame.method=='F')&(frame.attack==attack)].iloc[0]
            cr.append(dict(K=k,attack=attack,G=a.J_D,F=b.J_D,F_minus_G=b.J_D-a.J_D,percent_F_to_G=100*(b.J_D-a.J_D)/b.J_D))
    csv(BASE/'results/K12/G_F_same_attack_differences.csv',cr)
    historical=pd.read_csv(ROLL/'objectives.csv');combined=historical[(historical.B==1.2)&(historical.H==48)].copy()
    for event in ('E0','E1'):
        d=pd.read_csv(BASE/f'R_LAG_{event}_objectives.csv');combined=pd.concat([combined,d[d.H==48]],ignore_index=True)
    csv(BASE/'results/R_LAG/four_method_objectives.csv',combined.to_dict('records'))
    pairs=[]
    for event in ('E0','E1'):
        for period in ('post','full'):
            frame=combined[(combined.evaluation==event)&(combined.period==period)].set_index('method')
            for comparator in ('P','G','R'):
                other=frame.loc[comparator];lag=frame.loc['R-LAG']
                pairs.append(dict(evaluation=event,period=period,comparator=comparator,comparator_J_D=other.J_D,R_LAG_J_D=lag.J_D,
                    comparator_minus_R_LAG=other.J_D-lag.J_D,percent_comparator_to_R_LAG=100*(other.J_D-lag.J_D)/other.J_D))
    csv(BASE/'results/R_LAG/paired_comparisons.csv',pairs)
    pred=pd.read_csv(ROLL/'planned_controls.csv');fr=json.loads((ROLL/'B1.2/frozen_attacks.json').read_text());errors=[]
    for event in ('E0','E1'):
        actual=np.array(fr[event])
        for method in ('G','R'):
            for j in range(3):
                frame=pred[(pred.method==method)&(pred.evaluation==event)&(pred['update']==j)&pred.selected]
                for step,slot in enumerate(sorted(frame.absolute_slot.unique())):
                    at=frame[frame.absolute_slot==slot].sort_values('node').a_plan.to_numpy()
                    assert at.shape==(6,)
                    err=at[:2]-actual[j+step,:2]
                    errors.append(dict(evaluation=event,method=method,update=j,forecast_step=step,L1=float(abs(err).sum()),Linf=float(abs(err).max()),executed_first_interval=step==0))
    lag=pd.read_csv(BASE/'R_LAG_prediction_errors.csv');all_errors=pd.concat([pd.DataFrame(errors),lag],ignore_index=True)
    csv(BASE/'results/R_LAG/all_method_prediction_errors.csv',all_errors.to_dict('records'))
    first=all_errors[all_errors.executed_first_interval]
    csv(BASE/'results/R_LAG/prediction_error_time_means.csv',first.groupby(['evaluation','method'])[['L1','Linf']].mean().reset_index().to_dict('records'))
    changes=[];history=pd.read_csv(ROLL/'executed_controls.csv')
    for event in ('E0','E1'):
        lagc=pd.read_csv(BASE/f'R_LAG_{event}_controls.csv')
        for j in range(3):
            folder=BASE/f'results/R_LAG/{event}/update{j}'
            inputs=json.loads((folder/'input_provenance.json').read_text());sol=load_controls(folder/'selected_controls.json')
            for node in range(6):
                for kind,idx,col in [('s',1,'s'),('r',2,'r')]:
                    current=sol[idx][0,node];warm=np.array(inputs['initial_defense'][idx-1])[0,node]
                    prior=lagc[(lagc.slot==2+j)&(lagc.node==node)][col].iloc[0]
                    old=history[(history.evaluation==event)&(history.method=='P')&(history.slot==3+j)&(history.node==node)][col].iloc[0]
                    g=history[(history.evaluation==event)&(history.method=='G')&(history.slot==3+j)&(history.node==node)][col].iloc[0]
                    changes.append(dict(evaluation=event,update=j,node=node,control=kind,executed=current,previous_planned_same_slot=warm,
                        replanning_change=current-warm,previous_executed=prior,temporal_change=current-prior,P_same_slot=old,minus_P=current-old,G_same_slot=g,minus_G=current-g))
    csv(BASE/'results/R_LAG/action_changes.csv',changes)

def source_check():
    src=json.loads((BASE/'source_and_config_manifest.json').read_text());checks=[]
    authority={'DECISIONS.md','reviews/APPROVAL_LOG.md'}
    for rel,row in src['sources'].items():
        same=sha(ROOT/rel)==row['sha256']
        checks.append(dict(path=rel,initial_sha256=row['sha256'],final_sha256=sha(ROOT/rel),same=same,
            authorized_append_only_scope_log=rel in authority))
    csv(BASE/'results/source_immutability_check.csv',checks)
    assert all(r['same'] for r in checks if not r['authorized_append_only_scope_log'])
    for rel in authority:
        # Verify only an appended authorization entry differs from the registered bytes.
        data=(ROOT/rel).read_bytes();original_length=src['sources'][rel]['bytes']
        import hashlib
        assert hashlib.sha256(data[:original_length]).hexdigest()==src['sources'][rel]['sha256']
    return checks

def check_lag_provenance():
    previous={};checks=[]
    old=load_controls(STATIC/'G_controls.json');common=json.loads((ROLL/'B1.2/common_prefix.json').read_text())
    for event in ('E0','E1'):
        for j in range(3):
            folder=BASE/f'results/R_LAG/{event}/update{j}'
            inputs=json.loads((folder/'input_provenance.json').read_text())
            expected=old[0][3:6] if j==0 else load_controls(ROLL/f'B1.2/{event}_G/update{j-1}/warm/controls.json')[0][1:]
            sol=load_controls(folder/'selected_controls.json')
            warm=(old[1][3:],old[2][3:]) if j==0 else (previous[event][1][1:],previous[event][2][1:])
            state=np.array(common['x_event']) if j==0 else np.array(json.loads((BASE/f'results/R_LAG/{event}/update{j-1}/executed_first_interval.json').read_text())['x_end'])
            checks.append(dict(evaluation=event,update=j,attack_exact=np.array_equal(sol[0],expected),
                own_warm_start_exact=all(np.array_equal(a,np.array(b)) for a,b in zip(warm,inputs['initial_defense'])),
                own_state_exact=np.array_equal(state,np.array(inputs['own_actual_state'])),
                no_cross_branch=event in inputs['source'] if j else True))
            previous[event]=sol
    csv(BASE/'results/R_LAG/provenance_checks.csv',checks)
    assert all(all(r[k] for k in ('attack_exact','own_warm_start_exact','own_state_exact','no_cross_branch')) for r in checks)
    return checks

def main():
    comparisons()
    provenance=check_lag_provenance()
    rows=quality_table(BASE/'results/K12',BASE/'K12_numerical_quality.csv')
    # Explicit K6 fixed-plan refinement at all requested matched physical steps.
    from src.core import simulate
    from paper.work_d8_2.analysis.run_d8_2 import integration_error
    m=load_model(STATIC/'model.json')
    for method in ('G','F'):
        u=load_controls(STATIC/f'{method}_controls.json')
        sims={h:simulate(m,*u,10,h) for h in (48,96,192)}
        value=max(integration_error(sims[48],sims[h],h//48) for h in (96,192))
        rows.append(dict(B=1.2,evaluation='K6_reference',method=method,check='K6_fixed_control_integration',
            value=value,threshold=1e-6,passed=value<=1e-6))
    csv(BASE/'K12_numerical_quality.csv',rows)
    rows+=quality_table(BASE/'results/R_LAG',BASE/'R_LAG_numerical_quality.csv')
    summary=[]
    frame=pd.DataFrame(rows)
    for check,group in frame.groupby('check'):
        maximum=group.loc[group.value.idxmax()].to_dict()
        maximum.update(check=check,count=len(group),all_passed=bool(group.passed.all()))
        summary.append(maximum)
    csv(BASE/'results/numerical_quality_maxima.csv',summary)
    indep=audit_fixed();sources=source_check()
    good=all(r['passed'] for r in rows)
    result=dict(status='PASS' if good else 'NUMERICAL_ISSUES',quality_rows=len(rows),all_quality_passed=good,
        independent_trajectories=len(indep),independent_max_error=max(max(r['state_error'],r['parts_error']) for r in indep),
        source_files_checked=len(sources),all_D7_D8_1_sources_unchanged=all(r['same'] for r in sources if not r['authorized_append_only_scope_log']),
        lag_provenance_checks=len(provenance),no_K6_or_PGR_reoptimization=True,external_independent_review=False)
    from src.experiments import write_json
    write_json(BASE/'results/verification.json',result);manifest();print(json.dumps(result),flush=True)
    assert good
if __name__=='__main__':main()
