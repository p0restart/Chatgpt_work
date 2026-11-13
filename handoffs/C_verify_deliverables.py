"""Read-only artifact consistency checks; does not run research experiments."""
from pathlib import Path
import csv
import hashlib
import json
import re

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'handoffs'
manifest=json.loads((OUT/'C_evidence_manifest.json').read_text(encoding='utf-8'))
rows=list(csv.DictReader((OUT/'C_prior_art_matrix.csv').open(encoding='utf-8-sig',newline='')))
assert len(rows)==21
assert len({x['id'] for x in rows})==21
assert len({x['bibkey'] for x in rows})==21
assert sum(x['access']=='全文方法级核验' for x in rows)==9
assert sum(x['access']=='仅摘要可核验' for x in rows)==12
assert len({x['doi'].lower() for x in rows if x['doi']})==sum(bool(x['doi']) for x in rows)
for item in manifest['inputs']+manifest['outputs']:
    path=ROOT/item['path']
    assert path.exists(),item['path']
    assert hashlib.sha256(path.read_bytes()).hexdigest()==item['sha256'],item['path']
bib=(OUT/'C_bibliography.bib').read_text(encoding='utf-8')
keys=set(re.findall(r'@(?:article|misc)\{([^,]+),',bib))
assert keys=={x['bibkey'] for x in rows}
links=[]
for name in ['C_search_log.md','C_literature_novelty_audit.md','C_claim_evidence_map.md','C_related_work_draft.md']:
    text=(OUT/name).read_text(encoding='utf-8')
    for link in re.findall(r'\]\(([^)]+)\)',text):
        if not link.startswith(('https:','http:','#')):
            assert (OUT/link.split('#')[0]).exists(),(name,link)
            links.append(link)
    for key in re.findall(r'@([A-Za-z]+\d{4}[A-Za-z]+)',text):assert key in keys,(name,key)
draft=(OUT/'C_related_work_draft.md').read_text(encoding='utf-8')
body=draft.split('## 相关工作正文\n',1)[1].split('## 三条贡献声明',1)[0]
hanzi=len(re.findall(r'[\u4e00-\u9fff]',body))
assert 800<=hanzi<=1200,hanzi
print(json.dumps({'result':'PASS','research_records':len(rows),'fulltext_method_checked':9,
 'abstract_preview_only':12,'bib_entries':len(keys),'local_links_checked':len(links),
 'related_work_hanzi':hanzi,'inputs_hash_checked':len(manifest['inputs']),
 'outputs_hash_checked':len(manifest['outputs']),'experiments_run':False},ensure_ascii=False,indent=2))
