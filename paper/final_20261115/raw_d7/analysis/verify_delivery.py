"""Final evidence, parameter, manuscript, link and artifact consistency checks."""
from pathlib import Path
import json,hashlib,re,ast
import numpy as np,pandas as pd,yaml
ROOT=Path(__file__).resolve().parents[3];BASE=ROOT/'paper/work_d7';checks=[]
def check(name,condition):checks.append(dict(check=name,passed=bool(condition)))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
cfg=yaml.safe_load((BASE/'config_new_topology.yaml').read_text(encoding='utf-8'))
for p in [*sorted((BASE/'results/static').glob('B*/model.json')),*sorted((BASE/'results').glob('rolling_*/B*/model_pre.json')),*sorted((BASE/'results').glob('rolling_*/B*/model_post.json'))]:
    m=json.loads(p.read_text());B=float(p.parent.name[1:]);expected={k:cfg[k] for k in m};expected['B']=B
    if p.name=='model_post.json' and 'rolling_event' in str(p):expected['alpha']=[.5,.25,0,0,0,0]
    check(f'frozen_parameters:{p.relative_to(BASE)}',all(np.array_equal(m[k],v) for k,v in expected.items()))
original=json.loads((BASE/'sources/source_manifest.json').read_text());integrity=0
for rel,item in original.items():
    normalized=rel.replace('\\','/')
    if normalized.startswith('src/') or normalized in ['02_MODEL_SPEC.md','paper/work_d5/analysis/run_replanning.py']:
        check(f'historical_source_unchanged:{normalized}',sha(ROOT/rel)==item['sha256']);integrity+=1
for name in ['verification.json','derived/asset_export_check.json']:
    check(name,json.loads((BASE/'results'/name).read_text())['passed'])
for p in (BASE/'results').rglob('*gate.json'):check(str(p.relative_to(BASE)),json.loads(p.read_text())['passed'])
actions=pd.read_csv(BASE/'results/derived/all_asset_decisions.csv')
check('1080_asset_interval_rows',len(actions)==1080)
check('30_distinct_control_trajectories',len(actions.groupby(['case','B','evaluation','method']))==30)
check('asset_period_uniqueness',not actions.duplicated(['case','B','evaluation','method','slot','code_index']).any())
for x in json.loads((BASE/'figures/qa/summary.json').read_text()):check('figure:'+x['figure']+':'+x['check'],x['returncode']==0)
for p in (BASE/'figures/qa').glob('*_alignment.json'):check('alignment:'+p.name,json.loads(p.read_text())['verdict']=='PASS')
for fig,items in json.loads((BASE/'figures/figure_sources.json').read_text()).items():
    for item in items:check(f'figure_source_sha:{fig}:{item["path"]}',sha(BASE/item['path'])==item['sha256'])
paper=(BASE/'paper_v2_zh.md').read_text(encoding='utf-8')
check('five_chapters',re.findall(r'^# ([1-5]) ',paper,re.M)==list('12345'))
check('four_main_tables',len(re.findall(r'^\*\*表[1-4]',paper,re.M))==4)
check('five_main_figures',len(re.findall(r'^!\[图[1-5]',paper,re.M))==5)
check('fifteen_reference_entries',len(re.findall(r'^\[\d+\] ',paper,re.M))==15)
check('fifteen_bib_entries',len(re.findall(r'^@', (BASE/'references.bib').read_text(encoding='utf-8'),re.M))==15)
check('no_unfilled_template','{{' not in paper and 'TODO' not in paper)
check('pending_review_visible','尚待人工审核' in paper and '待人工审阅' in paper)
for filename in ['paper_v2_zh.md','supplement_zh.md']:
    text=(BASE/filename).read_text(encoding='utf-8')
    for url in re.findall(r'\]\(([^)]+)\)',text):
        if '://' not in url:check(f'local_link:{filename}:{url}',(BASE/url).exists())
required=['01_decisions_and_provenance.md','02_topology_spec.md','03_experiment_protocol.md','topology_assets.csv','topology_edges.csv','topology_assets_edges.csv','config_new_topology.yaml','references.bib','reference_claim_map.md','algorithm_code_map.md','claim_evidence_map.md','D6_D7_change_log.md','review_checklist.md','remaining_risks.md','REPRODUCE.md']
for name in required:check('required:'+name,(BASE/name).is_file())
change=(BASE/'D6_D7_change_log.md').read_text(encoding='utf-8')
check('20_unique_review_items',len(set(re.findall(r'\|(P[012]-\d\d)\|',change)))==20)
for p in (BASE/'analysis').rglob('*.py'):
    ast.parse(p.read_text(encoding='utf-8'));check('syntax:'+p.name,True)
smoke=BASE/'reproduction_smoke/paper/work_d7/results/gate1/gate1.json'
check('isolated_workspace_preflight',smoke.exists() and json.loads(smoke.read_text())['passed'])
if smoke.exists():
    (BASE/'sources/reproduction_smoke.json').write_text(json.dumps(dict(passed=json.loads(smoke.read_text())['passed'],checks=28,scope='Fresh directory imports and Gate1 only; no second full optimization'),indent=2),encoding='utf-8')
result=dict(passed=all(x['passed'] for x in checks),checks=len(checks),unchanged_historical_source_files=integrity,failed=[x for x in checks if not x['passed']],items=checks)
(BASE/'results/delivery_verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k!='items'},ensure_ascii=False))
assert result['passed']
