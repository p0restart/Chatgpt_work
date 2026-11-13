"""Compare actual isolated re-solves with untouched history at equal H=48."""
import json
from pathlib import Path
import hashlib
import numpy as np
import pandas as pd
from src.core import Model, simulate
from src.game_solver import ResponseProblem

ROOT=Path('results/work_c2_robustness')

def read(p):
    return json.loads(p.read_text())

def main():
    new=ROOT/'cross_environment/run01'
    if read(new/'metadata.json')['status']!='COMPLETED':
        raise RuntimeError('Re-solve incomplete; comparison not allowed')
    old=Path('results/matched_mechanism/run01')
    rows=[]; quality=[]; allocations=[]; hashes={}; opts=[]
    for name,cell in [('equal_high_at_node2','A'),('equal_high_at_node3','B'),
                      ('unequal_high_at_node2','C'),('unequal_high_at_node3','D')]:
        case=f'seed11_B1.2_{name}'
        oc,nc=old/case,new/case
        raw=read(nc/'model.json')
        assert raw==read(oc/'model.json'), 'Model drift'
        m=Model(**{k:np.array(v) if isinstance(v,list) else v for k,v in raw.items()})
        ou=tuple(np.array(v) for v in read(oc/'fine/controls.json'))
        nu=tuple(np.array(v) for v in read(nc/'fine/controls.json'))
        os=simulate(m,*ou,10,48); ns=simulate(m,*nu,10,48); finer=simulate(m,*nu,10,96)
        pd.DataFrame([dict(t=float(t),node=i,old_x=float(ox[i]),new_x=float(nx[i]))
                      for t,ox,nx in zip(ns['times'],os['states'],ns['states'])
                      for i in range(m.n)]).to_csv(ROOT/f'tables/states_H48_{cell}.csv',index=False)
        og=read(oc/'fine_audit.json'); ng=read(nc/'fine_audit.json'); audit=read(nc/'case_audit.json')
        control=max(float(np.max(abs(a-b))) for a,b in zip(ou,nu))
        state=float(np.max(abs(os['states']-ns['states'])))
        initdiff=max(float(np.max(abs(np.array(read(oc/f'{label}/controls.json'))-
                                            np.array(read(nc/f'{label}/controls.json')))))
                     for label in ('uniform','zero','random','fine'))
        row=dict(cell=cell,case=case,model_exact=True,old_J_D=os['J_D'],new_J_D=ns['J_D'],
                 old_J_A=os['J_A'],new_J_A=ns['J_A'],error_J_D=abs(os['J_D']-ns['J_D']),
                 error_J_A=abs(os['J_A']-ns['J_A']),control_linf=control,state_linf=state,
                 all_initializations_control_difference=initdiff,
                 gap_D_difference=abs(og['gap_D']-ng['gap_D']),gap_A_difference=abs(og['gap_A']-ng['gap_A']),
                 relative_D_difference=abs(og['relative_D']-ng['relative_D']),
                 relative_A_difference=abs(og['relative_A']-ng['relative_A']))
        row['comparison_pass']=bool(max(row['error_J_D'],row['error_J_A'])<=1e-6 and control<=1e-3 and
                                    state<=1e-5 and max(row['relative_D_difference'],row['relative_A_difference'])<=1e-7)
        rows.append(row)
        residual={}; violations={}
        for player in ('D','A'):
            pr=ResponseProblem(m,*nu,10,48,player)
            _,g=pr.value_gradient(pr.initial)
            residual[player]=pr.projected_residual(pr.initial,g)
            violations[player]=pr.violation(pr.initial)
        quality.append(dict(cell=cell,J_D=ns['J_D'],J_A=ns['J_A'],gap_D=ng['gap_D'],gap_A=ng['gap_A'],
                            signed_gap_D=ng['signed_gap_D'],signed_gap_A=ng['signed_gap_A'],
                            relative_D=ng['relative_D'],relative_A=ng['relative_A'],
                            residual_D=residual['D'],residual_A=residual['A'],
                            violation=max(violations.values()),
                            integration_error=max(abs(ns[p]-finer[p]) for p in ('J_D','J_A')),
                            state_min=float(ns['states'].min()),state_max=float(ns['states'].max()),
                            numerical_pass=audit['numerical_pass'],
                            all_fine_optimizer_success=all(ng[p]['all_starts_success'] for p in ('D','A')),
                            init_stability=audit['initialization_control_difference'],
                            fine_control_difference=audit['integration_control_difference']))
        for k in range(6):
            for node in (2,3):
                allocations.append(dict(cell=cell,slot=k,t_start=k*10/6,t_end=(k+1)*10/6,node=node,
                                        s=nu[1][k,node],r=nu[2][k,node],
                                        defense_use=float(nu[1][k]@m.b_s+nu[2][k]@m.b_r)))
        for p in nc.rglob('*.json*'):
            hashes[p.as_posix()]=hashlib.sha256(p.read_bytes()).hexdigest()
        # Capture optimizer statuses from every alternating path, sparse and final audits.
        for label in ('uniform','zero','random','fine'):
            for line in (nc/label/'trace.jsonl').read_text().splitlines():
                record=json.loads(line)
                for phase in ('D','A','sequential_attack'):
                    if phase in record:
                        for item in record[phase]['raw']:
                            opts.append(dict(cell=cell,path=label,iteration=record['iteration'],phase=phase,
                                             **{k:item[k] for k in ('start','success','status','nit','nfev','njev',
                                                                    'seconds','violation','projected_residual')}))
        for label in ('fine_audit','strong_audit'):
            record=read(nc/f'{label}.json')
            for phase in ('D','A'):
                for item in record[phase]['raw']:
                    opts.append(dict(cell=cell,path=label,iteration=-1,phase=phase,
                                     **{k:item[k] for k in ('start','success','status','nit','nfev','njev',
                                                            'seconds','violation','projected_residual')}))
            for sparse in record.get('sparse',[]):
                for item in sparse['raw']:
                    opts.append(dict(cell=cell,path=label+'_sparse',iteration=-1,phase=sparse['player'],
                                     **{k:item[k] for k in ('start','success','status','nit','nfev','njev',
                                                            'seconds','violation','projected_residual')}))
    df=pd.DataFrame(rows); q=pd.DataFrame(quality); op=pd.DataFrame(opts)
    df.to_csv(ROOT/'tables/cross_environment_errors.csv',index=False)
    q.to_csv(ROOT/'tables/solver_quality.csv',index=False)
    op.to_csv(ROOT/'tables/optimizer_calls.csv',index=False)
    pd.DataFrame(allocations).to_csv(ROOT/'tables/cross_environment_allocations.csv',index=False)
    jd=df.set_index('cell')
    interaction={}
    for prefix in ('old','new'):
        j=jd[f'{prefix}_J_D']; interaction[prefix]=float((j.D-j.C)-(j.B-j.A))
    interaction['absolute_error']=abs(interaction['new']-interaction['old'])
    summary=dict(interaction=interaction,comparison_pass=bool(df.comparison_pass.all() and
                 interaction['absolute_error']<=4e-6),numerical_pass=bool(q.numerical_pass.all()),
                 optimizer_calls=len(op),optimizer_failures=int((~op.success).sum()),
                 max_control_difference=float(df.control_linf.max()),max_state_difference=float(df.state_linf.max()),
                 max_objective_difference=float(df[['error_J_D','error_J_A']].to_numpy().max()),
                 max_relative_gap=float(q[['relative_D','relative_A']].to_numpy().max()),
                 max_residual=float(q[['residual_D','residual_A']].to_numpy().max()),
                 max_violation=float(q.violation.max()),max_integration_error=float(q.integration_error.max()))
    (ROOT/'cross_environment/comparison.json').write_text(json.dumps(summary,indent=2))
    (ROOT/'logs/new_result_hashes.json').write_text(json.dumps(hashes,indent=2))
    print(json.dumps(summary))

if __name__=='__main__':
    main()
