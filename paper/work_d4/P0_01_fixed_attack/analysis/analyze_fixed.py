"""Aggregate every preregistered cell, including failures; no research optimization."""
from pathlib import Path
import json
import hashlib
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[4]
PAPER=ROOT/'paper/work_d4/P0_01_fixed_attack'
RUN=ROOT/'results/work_d4/p0_1_fixed_attack/run01'
REPORT=ROOT/'reports/work_d4'
PARTS=['security','business','isolation','recovery','terminal_defense','attacker_value','attacker_effort','terminal_attacker']

def load(p):
    return json.loads(p.read_text(encoding='utf-8'))

def write(p,obj):
    p.write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')

def interaction(values):
    return (values['D']-values['C'])-(values['B']-values['A'])

def sign(value):
    return 1 if value>4e-6 else -1 if value < -4e-6 else 0

def main():
    design=pd.read_csv(PAPER/'design_matrix.csv')
    quality=[];costs=[];controls=[];state=[];attempts=[]
    for row in design.to_dict('records'):
        folder=RUN/row['case']
        if not (folder/'complete.json').exists():
            quality.append({**{k:row[k] for k in ('case','cell','seed','B')},'status':'NOT_RUN','numerical_pass':False})
            continue
        q=load(folder/'complete.json');quality.append(q)
        for phase in ['uniform_H12','zero_H12','random_H12','uniform_H48','zero_H48','random_H48']:
            for line in (folder/phase/'trace.jsonl').read_text(encoding='utf-8').splitlines():
                info=json.loads(line)
                for raw in info['raw']:
                    attempts.append(dict(case=row['case'],phase=phase,iteration=info['iteration'],
                        start=raw['start'],status=raw['status'],success=raw['success'],
                        objective=raw['objective'],projected_residual=raw['projected_residual'],
                        violation=raw['violation'],seconds=raw['seconds'],nit=raw['nit']))
        audit_items=[('coarse12',load(folder/'coarse_12_start_audit.json')),
                     ('fine3',load(folder/'fine_3_start_audit.json'))]
        audit_items += [(f"sparse{info['channel']}",info) for info in load(folder/'coarse_sparse_audits.json')]
        for phase,info in audit_items:
            for raw in info['raw']:
                attempts.append(dict(case=row['case'],phase=phase,iteration=-1,start=raw['start'],
                    status=raw['status'],success=raw['success'],objective=raw['objective'],
                    projected_residual=raw['projected_residual'],violation=raw['violation'],
                    seconds=raw['seconds'],nit=raw['nit']))
        cost=pd.read_csv(folder/'costs_H48.csv');costs.append(cost)
        ctrl=pd.read_csv(folder/'controls.csv');controls.append(ctrl)
        state.append(pd.read_csv(folder/'state_summary_H48.csv'))
    qdf=pd.DataFrame(quality)
    included_cases=set(qdf.loc[qdf.status!='NOT_RUN','case'])
    qdf.drop(columns=['conditions'],errors='ignore').to_csv(PAPER/'solver_quality.csv',index=False)
    attempts=pd.DataFrame(attempts);attempts.to_csv(PAPER/'optimizer_attempts.csv',index=False)
    cost=pd.concat(costs,ignore_index=True) if costs else pd.DataFrame()
    ctrl=pd.concat(controls,ignore_index=True) if controls else pd.DataFrame()
    states=pd.concat(state,ignore_index=True) if state else pd.DataFrame()
    cost.to_csv(PAPER/'objective_components_H48.csv',index=False)
    ctrl.to_csv(PAPER/'all_controls.csv',index=False)
    states.to_csv(PAPER/'node_state_summary.csv',index=False)
    comparisons=[];refinement_rows=[];component_rows=[];control_interactions=[];symmetry=[]
    historical=pd.read_csv(ROOT/'paper/work_d2/tables/matched_four_cells.csv')
    for (seed,budget),group in design.groupby(['seed','B'],sort=True):
        qr=qdf[(qdf.seed==seed)&(qdf.B==budget)]
        out=dict(seed=int(seed),B=budget,H=48,quality_status='PASS' if qr.numerical_pass.all() else ('IN_PROGRESS' if (qr.status=='NOT_RUN').any() else 'INCONCLUSIVE'),
                 completed_cells=int((qr.status!='NOT_RUN').sum()),
                 I_game=np.nan,I_fixed=np.nan,delta_I=np.nan)
        if not all(c in included_cases for c in group.case):
            comparisons.append(out);continue
        objs={r['cell']:{e:load(RUN/r['case']/e/'objectives.json') for e in ('GAME','FIXED','CROSS')}
              for r in group.to_dict('records')}
        for e in ('GAME','FIXED','CROSS'):
            vals={cell:obj[e]['48']['J_D'] for cell,obj in objs.items()}
            out.update({f'{e}_J_{c}':v for c,v in vals.items()})
            out[f'{e}_V_equal']=vals['B']-vals['A'];out[f'{e}_V_unequal']=vals['D']-vals['C']
            I=interaction(vals);out['I_'+e.lower()]=I
            out[f'{e}_C_denominator']=vals['C'];out[f'{e}_I_over_C_percent']=100*I/vals['C'] if vals['C']!=0 else np.nan
            out[f'{e}_sign_resolution_4e_6']=sign(I)
            for part in PARTS:
                iv=interaction({c:o[e]['48']['parts'][part] for c,o in objs.items()})
                component_rows.append(dict(seed=seed,B=budget,evaluation=e,H=48,component=part,interaction=iv))
            for H in (12,24,48,96,192):
                j={c:o[e][str(H)]['J_D'] for c,o in objs.items()}
                refinement_rows.append(dict(seed=seed,B=budget,evaluation=e,H=H,J_A=j['A'],J_B=j['B'],J_C=j['C'],J_D=j['D'],I=interaction(j)))
            # Directly recheck node exchange in both state and complete controls.
            pair=group.set_index('cell');aa=RUN/pair.loc['A','case']/e;bb=RUN/pair.loc['B','case']/e
            a=[np.asarray(x) for x in load(aa/'controls.json')];b=[np.asarray(x) for x in load(bb/'controls.json')]
            swap=[0,1,3,2,4,5]
            sx=np.load(aa/'trajectory_H48.npz')['states'];sy=np.load(bb/'trajectory_H48.npz')['states']
            result=dict(seed=seed,B=budget,evaluation=e,H=48,objective_error=abs(vals['B']-vals['A']),
                 control_exchange_error=max(float(np.max(np.abs(x[:,swap]-y))) for x,y in zip(a,b)),
                 state_exchange_error=float(np.max(np.abs(sx[:,swap]-sy))))
            symmetry.append(result);out[f'{e}_AB_objective_error']=result['objective_error']
            for window,slots in [('all',list(range(6))),('first4',list(range(4))),('last2',list(range(4,6)))]:
                for node in range(6):
                    for kind in ('s','r'):
                        values={}
                        for cell in ('A','B','C','D'):
                            rr=ctrl[(ctrl.seed==seed)&(ctrl.B==budget)&(ctrl.cell==cell)&(ctrl.evaluation==e)&(ctrl.node==node)&ctrl.slot.isin(slots)]
                            values[cell]=float(rr[kind].mean())
                        val=interaction(values)
                        control_interactions.append(dict(seed=seed,B=budget,evaluation=e,node=node,kind=kind,window=window,
                            interaction_mean=val,interaction_integral=val*len(slots)*10/6,exceeds_0_001=abs(val)>.001))
        out['delta_I']=out['I_game']-out['I_fixed']
        out['delta_I_attack_input']=out['I_game']-out['I_cross']
        out['delta_I_defense_reoptimization']=out['I_cross']-out['I_fixed']
        out['fixed_over_game']=out['I_fixed']/out['I_game'] if abs(out['I_game'])>1e-6 else np.nan
        out['delta_over_abs_game_percent']=100*out['delta_I']/abs(out['I_game']) if abs(out['I_game'])>1e-6 else np.nan
        h=historical[(historical.seed==seed)&(historical.B==budget)].iloc[0]
        out['historical_GAME_replay_max_error']=max(abs(out[f'GAME_J_{c}']-h[f'J_{c}']) for c in 'ABCD')
        out['same_resolved_sign']=sign(out['I_game'])==sign(out['I_fixed']) and sign(out['I_game'])!=0
        for r in group.to_dict('records'):
            out[f"source_{r['cell']}_GAME"]=r['game_source']
            out[f"source_{r['cell']}_FIXED"]=str((RUN/r['case']/'FIXED/controls.json').relative_to(ROOT))
            out[f"quality_{r['cell']}"]=qr[qr.cell==r['cell']].iloc[0]['status']
        comparisons.append(out)
    comparison=pd.DataFrame(comparisons);comparison.to_csv(PAPER/'four_cell_comparison.csv',index=False)
    pd.DataFrame(refinement_rows).to_csv(PAPER/'integration_interactions.csv',index=False)
    pd.DataFrame(component_rows).to_csv(PAPER/'cost_interactions.csv',index=False)
    pd.DataFrame(control_interactions).to_csv(PAPER/'control_interactions.csv',index=False)
    pd.DataFrame(symmetry).to_csv(PAPER/'symmetry_checks.csv',index=False)
    # Full per-node/window plans and objective decomposition, with repeated costs explicitly identified.
    combo=[];differences=[];state_diffs=[]
    for row in design.to_dict('records'):
        folder=RUN/row['case']
        if row['case'] not in included_cases:
            continue
        cc=ctrl[ctrl.case==row['case']]
        base=load(folder/'model.json')
        gg=cc[cc.evaluation=='GAME'].set_index(['slot','node'])
        ff=cc[cc.evaluation=='FIXED'].set_index(['slot','node'])
        for k,node in gg.index:
            differences.append(dict(case=row['case'],seed=row['seed'],B=row['B'],cell=row['cell'],slot=k,node=node,
                  s_GAME=gg.loc[(k,node),'s'],s_FIXED=ff.loc[(k,node),'s'],delta_s=ff.loc[(k,node),'s']-gg.loc[(k,node),'s'],
                  r_GAME=gg.loc[(k,node),'r'],r_FIXED=ff.loc[(k,node),'r'],delta_r=ff.loc[(k,node),'r']-gg.loc[(k,node),'r']))
        for e in ('GAME','FIXED','CROSS'):
            objective=cost[(cost.case==row['case'])&(cost.evaluation==e)].iloc[0].to_dict()
            for window,slots in [('all',list(range(6))),('first4',list(range(4))),('last2',list(range(4,6)))]:
                for node in range(6):
                    ss=cc[(cc.evaluation==e)&cc.slot.isin(slots)&(cc.node==node)]
                    xx=states[(states.case==row['case'])&(states.evaluation==e)&(states.node==node)].iloc[0]
                    combo.append(dict(**objective,node=node,window=window,window_duration=len(slots)*10/6,
                         s_mean=float(ss.s.mean()),r_mean=float(ss.r.mean()),a_mean=float(ss.a.mean()),
                         s_integral=float(ss.s.sum()*10/6),r_integral=float(ss.r.sum()*10/6),
                         q=base['q'][node],out_strength=sum(base['beta'][node]),
                         terminal_state=xx['terminal'],state_area_trapezoid_H48=xx['area_trapezoid_H48']))
        traj={e:np.load(folder/e/'trajectory_H48.npz') for e in ('GAME','FIXED','CROSS')}
        for ti,t in enumerate(traj['GAME']['times']):
            for node in range(6):
                x={e:float(traj[e]['states'][ti,node]) for e in traj}
                state_diffs.append(dict(case=row['case'],seed=row['seed'],B=row['B'],cell=row['cell'],t=t,node=node,
                      x_GAME=x['GAME'],x_FIXED=x['FIXED'],x_CROSS=x['CROSS'],
                      fixed_minus_game=x['FIXED']-x['GAME'],cross_minus_game=x['CROSS']-x['GAME'],
                      fixed_minus_cross=x['FIXED']-x['CROSS']))
    pd.DataFrame(combo).to_csv(PAPER/'controls_costs.csv',index=False)
    pd.DataFrame(differences).to_csv(PAPER/'control_differences.csv',index=False)
    pd.DataFrame(state_diffs).to_csv(PAPER/'state_differences_H48.csv',index=False)
    frozen=load(PAPER/'frozen_inputs.json')
    changed=[p for p,d in frozen['protected_files'].items() if hashlib.sha256((ROOT/p).read_bytes()).hexdigest()!=d]
    summary=dict(completed_cells=int((qdf.status!='NOT_RUN').sum()),passed_cells=int(qdf.numerical_pass.sum()),
                 not_run_cells=int((qdf.status=='NOT_RUN').sum()),optimizer_calls=len(attempts),
                 failed_optimizer_calls=int((~attempts.success).sum()) if len(attempts) else 0,
                 complete_groups=int((comparison.completed_cells==4).sum()),
                 all_quality_pass=bool(qdf.numerical_pass.all()),protected_changes=changed,
                 stage_status='WAITING_USER_G_D4_P0_1_REVIEW' if load(RUN/'metadata.json')['status'] in ('COMPLETED','NUMERICAL_GATE_FAILED','EXECUTION_FAILED') else 'RUNNING_P0_1',
                 table_rows=len(comparison),independence='separate integrator expression; same execution session')
    numeric=qdf[qdf.status!='NOT_RUN']
    for key in ['relative_improvement_max','current_residual_max','response_distance_max','initialization_difference_H12',
                'initialization_difference_H48','integration_control_difference','violation','GAME_baseline_replay_error',
                'max_integration_error','independent_max_error','D_GAME_FIXED_control_difference']:
        summary[key]=float(numeric[key].max()) if len(numeric) else None
    if len(symmetry):
        sym=pd.DataFrame(symmetry)
        summary['symmetry_max']={e:{k:float(sym[sym.evaluation==e][k].max()) for k in ['objective_error','control_exchange_error','state_exchange_error']} for e in ('GAME','FIXED')}
    if comparison.I_fixed.notna().any():
        for key in ['I_game','I_fixed','delta_I','fixed_over_game','delta_over_abs_game_percent','GAME_I_over_C_percent','FIXED_I_over_C_percent']:
            summary[key+'_range']=[float(comparison[key].min()),float(comparison[key].max())]
        summary['same_resolved_sign_count']=int(comparison.same_resolved_sign.fillna(False).sum())
    write(REPORT/'P0_01_summary.json',summary)
    print(json.dumps(summary,ensure_ascii=False,indent=2))

if __name__=='__main__':
    main()
