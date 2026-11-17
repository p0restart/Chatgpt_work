"""Reintegrate saved G1-C1 controls and tabulate all paired effects."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd
from .core import Model,simulate,check_controls
from .experiments import write_json


def load_model(path):
    data=json.loads(path.read_text(encoding='utf-8'))
    return Model(**{k:np.array(v,dtype=bool if k=='entry' else float) if isinstance(v,list) else v for k,v in data.items()})


def raw_records(obj):
    if isinstance(obj,dict):
        if all(k in obj for k in ('initial_control','control','status','success','projected_residual')):
            yield obj
        else:
            for v in obj.values():
                yield from raw_records(v)
    elif isinstance(obj,list):
        for v in obj:
            yield from raw_records(v)


def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);args=p.parse_args()
    root=Path(args.root);summary=pd.read_csv(root/'summary.csv')
    allocation=[];integrations=[];optimizers=[];transfers=[];symmetry=[];capacity=[]
    for case in summary['case']:
        folder=root/case;m=load_model(folder/'model.json')
        for label in ('uniform','zero','random','fine'):
            u=tuple(np.array(x) for x in json.loads((folder/label/'controls.json').read_text()))
            check_controls(m,*u)
            sim=simulate(m,*u,10,48)
            if label=='fine':
                for window,sl in [('all',slice(0,6)),('first4',slice(0,4)),('last2',slice(4,6))]:
                    use=u[1]@m.b_s+u[2]@m.b_r
                    capacity.append(dict(case=case,window=window,
                        binding_slots=int(np.sum(np.abs(use[sl]-m.B)<1e-6)),
                        minimum_slack=float((m.B-use[sl]).min()),
                        mean_total_isolation=float((u[1][sl]@m.b_s).mean()),
                        mean_total_recovery=float((u[2][sl]@m.b_r).mean())))
            saved=json.loads((folder/f'{label}_evaluation'/'summary.json').read_text())
            integrations.append(dict(case=case,initialization=label,
                error=max(abs(sim['J_D']-saved['fine_J_D']),abs(sim['J_A']-saved['fine_J_A'])),
                state_min=float(sim['states'].min()),state_max=float(sim['states'].max()),
                max_budget_violation=float(max(0,np.max(u[0]@m.d_a-m.A),np.max(u[1]@m.b_s+u[2]@m.b_r-m.B))),
                stored_integration_error=saved['integration_error']))
            for kind,j in [('s',1),('r',2)]:
                for node in (2,3):
                    for window,sl in [('all',slice(0,6)),('first4',slice(0,4)),('last2',slice(4,6))]:
                        allocation.append(dict(case=case,initialization=label,kind=kind,node=node,window=window,
                            average=float(u[j][sl,node].mean()),integral=float(u[j][sl,node].sum()*10/6)))
        for file in list(folder.glob('*/trace.jsonl'))+[folder/'strong_audit.json',folder/'fine_audit.json']:
            objects=([json.loads(line) for line in file.read_text().splitlines()] if file.suffix=='.jsonl'
                     else [json.loads(file.read_text())])
            for obj in objects:
                for raw in raw_records(obj):
                    optimizers.append(dict(case=case,file=str(file.relative_to(root)),**{
                        k:raw[k] for k in ('status','success','projected_residual','violation','nit')}))
        df=pd.read_csv(folder/'source_transfers.csv');df['case']=case;transfers.append(df)
    alloc=pd.DataFrame(allocation);alloc.to_csv(root/'source_allocations.csv',index=False)
    pd.DataFrame(capacity).to_csv(root/'capacity_summary.csv',index=False)
    integ=pd.DataFrame(integrations);integ.to_csv(root/'reintegration_audit.csv',index=False)
    opt=pd.DataFrame(optimizers);opt.to_csv(root/'optimizer_audit.csv',index=False)
    transfer=pd.concat(transfers,ignore_index=True);transfer.to_csv(root/'all_source_transfers.csv',index=False)
    paired=pd.read_csv(root/'paired_effects.csv');robust=[];slot_effects=[]
    for keys,group in paired.groupby(['seed','B','window','kind','node']):
        fine=group[group.initialization=='fine'].iloc[0]
        values=group.interaction.to_numpy()
        robust.append(dict(zip(['seed','B','window','kind','node'],keys)),)
        robust[-1].update(interaction=float(fine.interaction),
            initialization_and_refinement_range=float(np.ptp(values)),
            all_above_resolution=bool(np.all(np.abs(values)>1e-3)),
            same_sign=bool(np.all(values>0) or np.all(values<0)),
            numerical_pass=bool(group.numerical_pass.all()),
            robust_resolved=bool(group.numerical_pass.all() and np.all(np.abs(values)>1e-3)
                                 and (np.all(values>0) or np.all(values<0)) and np.ptp(values)<=1e-3))
    robust=pd.DataFrame(robust);robust.to_csv(root/'robust_effects.csv',index=False)
    for (seed,budget),group in summary.groupby(['seed','B']):
        if len(group)==4:
            lookup={(r.outgoing,r.value):root/r.case for r in group.itertuples()}
            for label in ('uniform','zero','random','fine'):
                controls={key:[np.array(x) for x in json.loads((folder/label/'controls.json').read_text())]
                          for key,folder in lookup.items()}
                for kind,j in [('s',1),('r',2)]:
                    for node in (2,3):
                        eq=controls['equal','high_at_node3'][j]-controls['equal','high_at_node2'][j]
                        neq=controls['unequal','high_at_node3'][j]-controls['unequal','high_at_node2'][j]
                        for slot in range(6):
                            slot_effects.append(dict(seed=int(seed),B=float(budget),initialization=label,
                                kind=kind,node=node,slot=slot,equal_value_effect=eq[slot,node],
                                unequal_value_effect=neq[slot,node],interaction=(neq-eq)[slot,node]))
        equal=group[group.outgoing=='equal']
        if len(equal)!=2:continue
        paths={r.value:root/r.case/'fine'/'controls.json' for r in equal.itertuples()}
        u={k:[np.array(x) for x in json.loads(p.read_text())] for k,p in paths.items()}
        difference=max(float(np.max(np.abs(a[:,[0,1,3,2,4,5]]-b)))
                       for a,b in zip(u['high_at_node2'],u['high_at_node3']))
        symmetry.append(dict(seed=int(seed),B=float(budget),max_swapped_control_difference=difference))
    pd.DataFrame(symmetry).to_csv(root/'equal_graph_symmetry.csv',index=False)
    slot_df=pd.DataFrame(slot_effects);slot_df.to_csv(root/'slotwise_effects.csv',index=False)
    contrast_errors=[]
    for row in paired.itertuples():
        slots=slot_df[(slot_df.seed==row.seed)&(slot_df.B==row.B)&
            (slot_df.initialization==row.initialization)&(slot_df.kind==row.kind)&(slot_df.node==row.node)]
        if row.window=='first4':slots=slots[slots.slot<4]
        if row.window=='last2':slots=slots[slots.slot>=4]
        contrast_errors.append(abs(float(slots.interaction.mean())-row.interaction))
    meta=json.loads((root/'metadata.json').read_text());hash_ok=all(
        hashlib.sha256(Path(path).read_bytes()).hexdigest()==digest for path,digest in meta['source_hashes'].items())
    audit=dict(cases=len(summary),numerical_pass_count=int(summary.numerical_pass.sum()),
        all_numerical_pass=bool(summary.numerical_pass.all()),source_hashes_match=hash_ok,
        reintegrations=len(integ),reintegration_max_error=float(integ.error.max()),
        integration_max_error=float(integ.stored_integration_error.max()),
        budget_max_violation=float(integ.max_budget_violation.max()),
        states_in_domain=bool(integ.state_min.min()>=0 and integ.state_max.max()<=1),
        optimizer_runs=len(opt),all_optimizer_success=bool(opt.success.all()),
        all_optimizer_residual_max=float(opt.projected_residual.max()),
        feasible_transfers=int(transfer.feasible.sum()),transfer_max_error=float(transfer.error.max()),
        minimum_feasible_transfer_derivative=float(transfer[transfer.feasible].analytic.min()),
        relative_improvement_max=float(summary.relative_max.max()),
        incumbent_residual_max=float(summary.incumbent_residual_max.max()),
        initialization_control_difference_max=float(summary.initialization_control_difference.max()),
        integration_control_difference_max=float(summary.integration_control_difference.max()),
        interaction_uncertainty_max=float(robust.initialization_and_refinement_range.max()),
        saved_contrast_recalculation_max_error=max(contrast_errors),
        global_certificate=False)
    analysis_sources=[Path(__file__),Path('src/report_matched.py'),Path('src/compare_matched.py'),Path('src/resume_matched.py')]
    audit['analysis_source_hashes']={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in analysis_sources}
    snapshots=root/'analysis_source_snapshot';snapshots.mkdir(exist_ok=True)
    for source in analysis_sources:
        (snapshots/source.name).write_bytes(source.read_bytes())
    write_json(root/'audit.json',audit);print(json.dumps(audit,indent=2))


if __name__=='__main__':main()
