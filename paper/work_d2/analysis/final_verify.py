"""Final artifact and protected-input integrity checks; no experiments."""
from pathlib import Path
import json,re,hashlib
import pandas as pd
O=Path(__file__).resolve().parents[1]; R=O.parents[1]
s=json.loads((O/'analysis/source_manifest.json').read_text())
changed=[p for p,d in s.items() if hashlib.sha256((R/p).read_bytes()).hexdigest()!=d['sha256']]
extra={}
for p in (R/'results/work_c2_robustness/k_refinement/run01').glob('seed*/warm/fine/controls.json'):
    extra[p.relative_to(R).as_posix()]={'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}
(O/'analysis/additional_control_sources.json').write_text(json.dumps(extra,indent=2))
missing_links=[]
for p in O.glob('*.md'):
    for link in re.findall(r'\]\(([^)]+)\)',p.read_text(encoding='utf-8')):
        if not re.match(r'https?://',link) and not (p.parent/link.split('#')[0]).exists():missing_links.append((p.name,link))
eq=[]
for name in ['02_experimental_design_zh.md','03_results_discussion_zh.md']:
    eq+=re.findall(r'\\tag\{(\d+)\}',(O/name).read_text(encoding='utf-8'))
nan=[]
for name in ['matched_four_cells.csv','matched_controls_all_nodes.csv','matched_budgets.csv','matched_states_H12.csv','baseline_all_objectives.csv','baseline_pairs.csv','robust_all_paths.csv','robust_cross_class.csv','robust_solver_quality.csv','k_control_distances.csv']:
    df=pd.read_csv(O/'tables'/name)
    if df.isna().any().any():nan.append(name)
figs=['fig01_matched_network','fig02_losses_interactions','fig03_temporal_allocation','figS01_seed33_state_allocation']
missing=[f'{n}.{e}' for n in figs for e in ['pdf','svg','png','alignment.json','collision.json'] if not (O/'figures'/f'{n}.{e}').exists()]
assert not changed and not missing_links and not nan and not missing
assert eq==['17','18','19','20'],eq
out=dict(status='READY_FOR_G_D2_REVIEW',protected_files_checked=len(s),protected_files_changed=changed,additional_control_sources=len(extra),missing_links=missing_links,nan_tables=nan,equations=eq,missing_figure_files=missing,experiments_run=False,approval_log_modified=False)
(O/'analysis/final_verification.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
deliver={}
for p in O.rglob('*'):
    if p.is_file() and '_qa_packages' not in p.parts and p.name!='delivery_manifest.json':deliver[p.relative_to(O).as_posix()]=hashlib.sha256(p.read_bytes()).hexdigest()
(O/'analysis/delivery_manifest.json').write_text(json.dumps(deliver,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(out,ensure_ascii=False,indent=2))
