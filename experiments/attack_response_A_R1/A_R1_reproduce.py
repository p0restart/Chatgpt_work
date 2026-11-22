import argparse
import importlib.util
import json
import logging
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
INPUTS = (
    'A_reproduce.py', 'A_run_config.json', 'A_experiment_protocol.md', 'A_replay_checks.json',
    'A_results.csv', 'A_metrics.csv', 'A_plans.csv', 'A_matched_response.csv', 'A_state_trajectories.csv',
    'A_validation_checks.csv', 'A_source/src/__init__.py', 'A_source/src/core.py',
    'A_source/src/game_solver.py', 'A_source/paper/work_d7/config_new_topology.yaml',
)


def run(source, out, progress):
    spec = importlib.util.spec_from_file_location('original_A_driver', source/'A_reproduce.py')
    original = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(original)
    import numpy as np
    import pandas as pd

    cfg = json.loads((source/'A_run_config.json').read_text(encoding='utf-8'))
    source_hashes = {name: original.digest(source/name) for name in INPUTS}
    for row in json.loads((source/'A_replay_checks.json').read_text(encoding='utf-8-sig')):
        assert row['byte_identical'] and row['sha256'] == source_hashes[row['name']], row['name']
    assert source_hashes['A_reproduce.py'] == cfg['driver_sha256']
    assert source_hashes['A_experiment_protocol.md'] == cfg['protocol_sha256']
    np.testing.assert_array_equal(cfg['executed_api'], np.repeat([.20,.40,.20],4))
    for name in INPUTS:
        target = out/'original_A'/name
        if target.resolve() != (source/name).resolve():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source/name, target)

    diagnostics = out/'S1_audit'
    diagnostics.mkdir()
    exp = original.Experiment(diagnostics)
    progress.append(exp)
    fresh_cfg = json.loads((diagnostics/'A_run_config.json').read_text(encoding='utf-8'))
    for key in ('model','frozen_config','K','T','H','refine_H','slot_width','seeds','solver','numeric_threads','revision','source_sha256'):
        assert fresh_cfg[key] == cfg[key], key
    (diagnostics/'A_run_config.json').unlink()
    schedules = {scene: np.repeat([.20, peak, .20],4) for scene, peak in (('S1',.30),('S2',.40))}
    original.dump(out/'A_R1_run_config.json', dict(original_A=cfg, actual_api=schedules,
                  event_slots=[5,9], original_A_inputs_sha256=source_hashes,
                  driver_sha256=original.digest(Path(__file__)),
                  protocol_sha256=original.digest(HERE/'A_R1_protocol.md'),
                  packages=fresh_cfg['packages'], python=fresh_cfg['python'], platform=fresh_cfg['platform'],
                  S2='original Work A C1/C2 reused; only matched slot-5 endpoint problems recalculated'))

    def load(stem):
        return pd.read_csv(source/f'A_{stem}.csv', float_precision='round_trip')

    def controls(frame):
        return tuple(frame[channel].to_numpy().reshape(-1,6) for channel in ('a','s','r'))

    def same(label, left, right, limit=0):
        exp.check(label, original.maximum(np.asarray(left)-np.asarray(right)), limit)

    original_plans = load('plans')
    archived_results = load('results')
    archived_metrics = load('metrics')
    archived_traces = load('state_trajectories')
    archived_matched = load('matched_response')
    baseline = controls(original_plans[original_plans.label == 'D0'])
    first = tuple(channel[:4] for channel in baseline)
    warm5 = tuple(channel[4:] for channel in baseline[1:])
    actual = {scene: exp.attack(api) for scene, api in schedules.items()}
    model = exp.model
    logging.info('Frozen Work A verified; S1 uses .20/.30/.20; S2 execution uses archived .20/.40/.20')
    for scene, peak_use in (('S1',.70),('S2',.80)):
        exp.core.check_controls(model, actual[scene], *baseline[1:])
        same(f'{scene} per-slot attack use', actual[scene] @ model.d_a, np.repeat([.60,peak_use,.60],4),1e-12)
        same(f'{scene} event indices', np.flatnonzero(np.diff(actual[scene][:,0]))+2,[5,9])
        same(f'{scene} normal prefix', actual[scene][:4], first[0])
    for label in ('C1','C2'):
        archived = archived_results[archived_results.label == label]
        same(f'archived {label} uses exact S2 attack', controls(archived)[0], actual['S2'])
        same(f'archived {label} x0', archived.x_start.iloc[:6].to_numpy(), model.x0)
    same('archived S2 C1 holds D0', controls(archived_results[archived_results.label == 'C1'])[1:],baseline[1:])
    x4 = exp.evaluate(model.x0, first)['states'][-1]
    same('shared x4 matches archived event state', x4, archived_matched.query('event_slot == 5 and slot == 5').state_at_event,1e-12)
    levels = ((.20,'slot5_a020','M5_old'),(.30,'slot5_a030',None),(.40,'slot5_a040','D1'))
    for intensity, name, origin in levels:
        plan = exp.plan(name,4,x4,intensity,warm5,cfg['seeds']['slot5'])
        if origin:
            old = controls(original_plans[original_plans.label == origin])
            same(f'{name} reproduces A actions', plan, old,1e-8)
    reference = exp.traces['slot5_a020']
    for name in ('slot5_a030','slot5_a040'):
        same(f'{name} matching x4', exp.traces[name]['x0'], reference['x0'])
        for updated, prior in zip(exp.traces[name]['attempts'], reference['attempts']):
            same(f'{name} matched start {updated["start"]}',updated['initial_control'],prior['initial_control'])

    raised = exp.plans['slot5_a030'][1]
    second = tuple(channel[:4] for channel in raised)
    same('S1 observed middle actually executed', second[0],actual['S1'][4:8])
    x8 = exp.evaluate(x4,second)['states'][-1]
    lowered = exp.plan('S1_slot9',8,x8,.20,tuple(channel[4:] for channel in raised[1:]),cfg['seeds']['slot9'])
    systems = dict(C1=(actual['S1'],*baseline[1:]),
                   C2=(actual['S1'],*(np.concatenate([first[axis],second[axis],lowered[axis]]) for axis in (1,2))))
    same('S1 plans only see present levels', np.r_[raised[0][:,0],lowered[0][:,0]],np.repeat([.30,.20],[8,4]))
    same('S1 C1/C2 actual attacks equal',systems['C1'][0],systems['C2'][0])
    for label, schedule in systems.items():
        replay = exp.integrate_and_audit('S1_'+label,model.x0,schedule)
        exp.plans['S1_'+label] = (0,schedule,replay)
        same(f'S1 {label} initial state', replay['states'][0],model.x0)
        same(f'S1 {label} first four slots terminal state',replay['states'][4*original.H],x4,1e-12)
    runs = {label:exp.plans['S1_'+label][2] for label in systems}
    same('S1 C2 carries actual x8',runs['C2']['states'][8*original.H],x8,1e-12)
    same('S1 C1/C2 have identical pre-event state history',runs['C1']['states'][:4*original.H+1],
         runs['C2']['states'][:4*original.H+1],1e-12)
    results, metrics, traces = [], [], []
    for label, replay in runs.items():
        rows = list(exp.slot_rows(label,0,systems[label],replay))
        results.extend(dict(scenario='S1',**row) for row in rows)
        state = replay['states']
        weighted = state @ model.q / model.q.sum()
        traces.extend(dict(scenario='S1', label=label, time=time, weighted_damage=weight,
                           **{f'x{index+1}':value for index,value in enumerate(vector)})
                      for time,weight,vector in zip(replay['times'],weighted,state))
        usage = np.array([row['total_defense'] for row in rows if row['asset'] == 1])
        gain = runs['C1']['J_D']-replay['J_D']
        metrics.append(dict(scenario='S1',label=label,J_D=replay['J_D'],
                            **{key:replay['parts'][key] for key in original.PARTS},
                            api_terminal=state[-1,0],api_peak=state[:,0].max(),db_terminal=state[-1,4],
                            db_peak=state[:,4].max(),weighted_terminal=weighted[-1],weighted_peak=weighted.max(),
                            max_defense=usage.max(),capacity_ok=bool(usage.max() <= model.B+1e-10),
                            binding_slots=int(np.count_nonzero(abs(usage-model.B)<=1e-8)),
                            loss_improvement_vs_C1=gain,relative_improvement_vs_C1=gain/runs['C1']['J_D']))
    for stem, rows, archived in (('results',results,archived_results),('metrics',metrics,archived_metrics),
                                 ('state_trajectories',traces,archived_traces)):
        archived = archived[archived.label.isin(['C1','C2'])].copy()
        archived.insert(0,'scenario','S2')
        joined = pd.concat([pd.DataFrame(rows),archived],ignore_index=True)
        original.table(out/f'A_R1_{stem}.csv',joined)
    by_level = [list(exp.slot_rows(name,*exp.plans[name])) for _,name,_ in levels]
    matched = []
    for index,(intensity,_,_) in enumerate(levels):
        for row, base, middle in zip(by_level[index],by_level[0],by_level[1]):
            matched.append(dict(api_forecast=intensity,shared_x4=x4[row['asset']-1],**row,
                                **{f'delta_{key}_vs_020':row[key]-base[key] for key in ('s','r','resource')},
                                **{f'delta_{key}_vs_030':row[key]-middle[key] for key in ('s','r','resource')}))
    original.table(out/'A_R1_matched_response.csv',matched)
    original.table(out/'A_R1_S1_plans.csv',
                   [row for label in ('slot5_a030','S1_slot9') for row in exp.slot_rows(label,*exp.plans[label])])
    logging.info('S1 J_D: %s; S2 execution data reused from archived Work A', {name:r['J_D'] for name,r in runs.items()})


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--original-a',type=Path,default=HERE/'original_A')
    args = parser.parse_args()
    out = args.output.resolve()
    out.mkdir(parents=True,exist_ok=True)
    if (out/'A_R1_execution.log').exists():
        parser.error('use a fresh output directory')
    logging.basicConfig(level=logging.INFO,format='%(asctime)s %(message)s',
                        handlers=[logging.FileHandler(out/'A_R1_execution.log',encoding='utf-8'),logging.StreamHandler()])
    progress = []
    try:
        run(args.original_a.resolve(),out,progress)
        logging.info('PASS %d numerical checks',len(progress[0].checks))
    except Exception:
        logging.exception('Stopped; partial output preserved')
        raise
    finally:
        if progress:
            import pandas as pd

            pd.DataFrame(progress[0].checks).to_csv(out/'A_R1_validation_checks.csv',index=False,encoding='utf-8-sig')


if __name__ == '__main__':
    main()
