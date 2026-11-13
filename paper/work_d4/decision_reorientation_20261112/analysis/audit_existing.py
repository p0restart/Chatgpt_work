"""Read saved evidence only. No solver, integrator, or research-module imports."""
from pathlib import Path
import csv
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[4]
OUT = ROOT / 'paper/work_d4/decision_reorientation_20261112'
REPORT = ROOT / 'reports/work_d4/decision_reorientation_20261112'

def read_json(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

def rows(path):
    with path.open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))

def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')

def csv_out(name, data):
    path = OUT / 'evidence' / name
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, list(data[0]))
        w.writeheader()
        w.writerows(data)

def snapshot():
    paths = set()
    for folder in ['src', 'configs', 'tests', 'paper/work_d1', 'paper/work_d2', 'paper/work_d3']:
        for p in (ROOT / folder).rglob('*'):
            if p.is_file() and not any(x in p.parts for x in ('_qa_packages', '__pycache__', 'mpl_config')):
                paths.add(p)
    for name in ['AGENTS.md', '02_MODEL_SPEC.md', 'DECISIONS.md', 'reviews/APPROVAL_LOG.md', 'logs/STATUS.md', 'reviews/G_D4_P0_1_submission.md']:
        paths.add(ROOT / name)
    for folder in ['results/matched_mechanism/run01', 'results/supplement_c2/run01', 'results/supplement_c2/run02',
                   'results/work_c2_robustness/k_refinement/run01', 'results/work_d4/p0_1_fixed_attack/run01',
                   'results/equilibrium_counterexample/run01', 'paper/work_d4/P0_01_fixed_attack']:
        if (ROOT / folder).exists():
            for p in (ROOT / folder).rglob('*'):
                if p.is_file() and not any(x in p.parts for x in ('__pycache__', 'mpl_config')):
                    paths.add(p)
    return {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)}

def audit():
    checks = []
    def check(name, passed, **details):
        checks.append(dict(name=name, passed=bool(passed), **details))
    baseline = REPORT / 'protected_before.json'
    if not baseline.exists():
        dump(baseline, snapshot())
    old = read_json(baseline)
    changed = [p for p, h in old.items() if not (ROOT/p).exists() or hashlib.sha256((ROOT/p).read_bytes()).hexdigest()!=h]
    check('protected_sources_unchanged', not changed, count=len(old), changed=changed)
    matched = ROOT / 'results/matched_mechanism/run01'
    case_paths = sorted(matched.glob('seed*'))
    check('matched_case_count', len(case_paths)==36, count=len(case_paths))
    raw_objectives = {}
    budget_rows = []
    selected_controls = []
    for case in case_paths:
        m = read_json(case/'model.json')
        a, s, r = read_json(case/'fine/controls.json')
        audit_row = read_json(case/'fine_audit.json')
        summary = read_json(case/'fine_evaluation/summary.json')
        raw_objectives[case.name] = float(audit_row['J_D'])
        check(case.name+'_H48_saved_objective', abs(audit_row['J_D']-summary['fine_J_D'])<=1e-12)
        max_violation = 0.0
        for k in range(6):
            su = sum(x*y for x,y in zip(s[k],m['b_s']))
            ru = sum(x*y for x,y in zip(r[k],m['b_r']))
            au = sum(x*y for x,y in zip(a[k],m['d_a']))
            max_violation = max(max_violation, su+ru-m['B'], au-m['A'])
            row = dict(case=case.name, B=m['B'], slot=k, t_start=k*10/6, t_end=(k+1)*10/6,
                       isolation_use=su, recovery_use=ru, defense_use=su+ru, attack_use=au,
                       slack=m['B']-su-ru, binding=abs(m['B']-su-ru)<1e-6)
            budget_rows.append(row)
            for i in range(6):
                if not m['entry'][i]:
                    max_violation=max(max_violation,abs(a[k][i]))
                max_violation=max(max_violation,-a[k][i],a[k][i]-1,-s[k][i],s[k][i]-1,-r[k][i],r[k][i]-1)
                if case.name=='seed11_B1.2_unequal_high_at_node3':
                    selected_controls.append(dict(case=case.name, slot=k, t_start=k*10/6, t_end=(k+1)*10/6,
                        node=i,a=a[k][i],s=s[k][i],r=r[k][i],source=(case/'fine/controls.json').relative_to(ROOT).as_posix()))
        check(case.name+'_saved_plan_feasible',max_violation<=1e-10,max_violation=max_violation)
    csv_out('saved_budget_use_all36.csv', budget_rows)
    csv_out('saved_allocation_seed11_B1.2_D.csv',selected_controls)
    binding = {str(b):sum(r['binding'] for r in budget_rows if r['B']==b) for b in (0.6,1.2,1.8)}
    check('binding_counts_60_40_1',list(binding.values())==[60,40,1],counts=binding)
    pairs = rows(ROOT/'paper/work_d2/tables/baseline_pairs.csv')
    for row in pairs:
        val=100*(float(row['baseline_cost'])-float(row['joint']))/float(row['baseline_cost'])
        check('paired_'+row['case']+'_'+row['evaluation']+'_'+row['baseline'],abs(val-float(row['reduction_percent']))<1e-10)
    csv_out('saved_fixed_trained_comparisons.csv',[r for r in pairs if r['namespace']=='matched_D' and r['baseline']=='Fixed-trained'])
    source_pairs=rows(ROOT/'results/supplement_c2/run02/paired.csv')
    pair_map={(r['case'],r['evaluation'],r['baseline']):r for r in source_pairs}
    raw_pair_errors=[]
    for row in pairs:
        if row['namespace']!='matched_D':
            continue
        source=pair_map[(row['case'],row['evaluation'],row['baseline'])]
        raw_pair_errors.append(abs(float(source['reduction_percent'])-float(row['reduction_percent'])))
    check('D2_pairs_match_raw_supplement_pairs',max(raw_pair_errors)<=1e-10,count=len(raw_pair_errors),max_error=max(raw_pair_errors))
    objs=rows(ROOT/'paper/work_d2/tables/baseline_all_objectives.csv')
    raw_summary_errors=[]
    same_defense=[]
    for row in objs:
        if row['namespace']!='matched_D':
            continue
        folder=ROOT/'results/supplement_c2/run02/comparison'/row['case']
        summary=read_json(folder/(row['method']+'_'+row['evaluation'])/'summary.json')
        raw_summary_errors.append(abs(float(row['fine_J_D'])-summary['fine_J_D']))
        if row['evaluation']=='adaptive_attack':
            aa=rows(folder/(row['method']+'_adaptive_attack')/'controls.csv')
            ff=rows(folder/(row['method']+'_common_fixed_attack')/'controls.csv')
            aa={(r['slot'],r['node']):r for r in aa}; ff={(r['slot'],r['node']):r for r in ff}
            same_defense.append(max(abs(float(aa[k][v])-float(ff[k][v])) for k in aa for v in ('s','r')))
    check('144_saved_objectives_match_raw_summary',max(raw_summary_errors)<=1e-12,count=len(raw_summary_errors),max_error=max(raw_summary_errors))
    check('72_defenses_identical_between_evaluations',max(same_defense)<=1e-12,count=len(same_defense),max_error=max(same_defense))
    csv_out('saved_budget_loss_D9_H192.csv',[{k:r[k] for k in ['case','seed','B','evaluation','fine_J_D','fine_J_A','H_objective','H_parts','defense_use_mean','binding_slots','isolation_use_mean','recovery_use_mean']} for r in objs if r['namespace']=='matched_D' and r['method']=='Joint-dynamic'])
    p0=rows(ROOT/'paper/work_d4/P0_01_fixed_attack/four_cell_comparison.csv')
    for row in p0:
        vals={}
        for cell in 'ABCD':
            for kind in ['GAME','FIXED']:
                path=ROOT/row[f'source_{cell}_{kind}'].replace('\\','/')
                check('P0_source_'+str(row['seed'])+'_'+row['B']+'_'+cell+'_'+kind,path.exists())
                if kind=='FIXED':
                    objective=read_json(path.parent/'objectives.json')['48']['J_D']
                    check('P0_fixed_raw_value_'+str(row['seed'])+'_'+row['B']+'_'+cell,
                          abs(objective-float(row['FIXED_J_'+cell]))<=1e-12)
            game_path=Path(row[f'source_{cell}_GAME'].replace('\\','/'))
            case_name=game_path.parts[-3]
            check('P0_game_value_'+str(row['seed'])+'_'+row['B']+'_'+cell,abs(raw_objectives[case_name]-float(row['GAME_J_'+cell]))<=1e-10)
        for kind in ['GAME','FIXED']:
            v=[float(row[kind+'_J_'+c]) for c in 'ABCD']
            inter=(v[3]-v[2])-(v[1]-v[0])
            check('P0_interaction_'+str(row['seed'])+'_'+row['B']+'_'+kind,abs(inter-float(row['I_game' if kind=='GAME' else 'I_fixed']))<=1e-12)
    csv_out('saved_P0_1_pending_review.csv',[{k:r[k] for k in ['seed','B','H','I_game','I_fixed','delta_I','fixed_over_game','quality_status']} for r in p0])
    cross=rows(ROOT/'results/equilibrium_audit/counterexample01/cross_evaluation.csv')
    cross_display=rows(ROOT/'paper/work_d2/tables/counterexample_cross_evaluation.csv')
    for a,b in zip(cross,cross_display):
        check('counterexample_cross_'+a['defense']+'_'+a['attack'],
              a['defense']==b['defense'] and a['attack']==b['attack'] and abs(float(a['J_D'])-float(b['J_D']))<=1e-12)
    comparison=read_json(ROOT/'results/equilibrium_audit/counterexample01/comparison.json')
    negative=100*(comparison['recovery_J_D']-comparison['joint_J_D'])/comparison['recovery_J_D']
    check('counterexample_negative_reduction',abs(negative-comparison['joint_reduction_pct'])<=1e-12 and negative<0)
    csv_out('saved_original_counterexample_cross.csv',cross)
    for row in rows(ROOT/'results/work_c2_robustness/k_refinement/run01/tables/interactions.csv'):
        check('K_two_groups_positive_'+row['seed']+'_'+row['B'],
              float(row['I6'])>0 and float(row['I12'])>0 and abs(float(row['delta'])-(float(row['I12'])-float(row['I6'])))<=1e-12)
    core_case=ROOT/'results/matched_mechanism/run01/seed11_B1.2_unequal_high_at_node3'
    csv_out('proposed_experiment_edges_from_saved_model.csv',[dict(source=j,target=i,beta=b) for j,row in enumerate(read_json(core_case/'model.json')['beta']) for i,b in enumerate(row) if b])
    missing=['G_D1_独立验收报告.md','G_D1_R1_验收报告.md','G_D3_independent_peer_review.md']
    found={name:[p.relative_to(ROOT).as_posix() for folder in ('paper','reviews','reports','handoffs') for p in (ROOT/folder).rglob(name)] for name in missing}
    info=dict(date='2026-11-12 Asia/Shanghai',mode='saved_files_and_arithmetic_only',
              optimization_executed=False,integration_executed=False,research_tests_executed=False,
              passed=all(c['passed'] for c in checks),check_count=len(checks),failed=[c for c in checks if not c['passed']],
              checks=checks,independent_report_search=found,
              fixed_trained_adaptive_range=[min(float(r['reduction_percent']) for r in pairs if r['namespace']=='matched_D' and r['baseline']=='Fixed-trained' and r['evaluation']=='adaptive_attack'), max(float(r['reduction_percent']) for r in pairs if r['namespace']=='matched_D' and r['baseline']=='Fixed-trained' and r['evaluation']=='adaptive_attack')],
              fixed_trained_common_range=[min(float(r['reduction_percent']) for r in pairs if r['namespace']=='matched_D' and r['baseline']=='Fixed-trained' and r['evaluation']=='common_fixed_attack'),max(float(r['reduction_percent']) for r in pairs if r['namespace']=='matched_D' and r['baseline']=='Fixed-trained' and r['evaluation']=='common_fixed_attack')])
    dump(REPORT/'saved_evidence_audit.json',info)
    print(json.dumps({k:v for k,v in info.items() if k not in ('checks',)},ensure_ascii=True,indent=2))
    if not info['passed']:
        sys.exit(1)

if __name__=='__main__':
    audit()
