"""Verify immutable evidence and build a dependency-free review archive."""
from pathlib import Path
import hashlib,json,zipfile
R=Path(__file__).resolve().parents[3];O=R/'paper/work_d2'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf-8')
source=json.loads((O/'analysis/source_manifest.json').read_text())
protected=json.loads((O/'analysis/minimal_revision_protected_hashes.json').read_text())
changes=[p for p,v in source.items() if sha(R/p)!=v['sha256']]
changes += [p for p,h in protected.items() if sha(R/p)!=h]
assert not changes,changes
pack=O/'review_package';pack.mkdir(exist_ok=True)
(pack/'README.md').write_text('''# Work D2 轻量审查包

入口：paper/work_d2/D2_handoff.md；本次验收：D1_D2_equation_alignment.md。

包括当前D1正文与版本说明、D2完整稿件、图形PDF/SVG/PNG、派生数值表、来源哈希与分析脚本。本次新版本标记PASS_ALIGNMENT / WAITING_USER_G_D2；不是人工审批通过。

排除_qa_packages、缓存、包自身及原始results大目录。保留paper/work_d1与paper/work_d2相对目录关系；原始results需在完整项目中访问，轻量包不宣称独立实验复现环境。analysis/minimal_revision_before为本次修订前历史快照；当前稿件在work_d2根目录。

目标会议模板尚未指定，conference_layout_checklist.md为待套版检查表。未运行新实验，D1/src/results/数值表/历史审批未改。等待用户G-D2人工批准后才可进入D3。
''',encoding='utf-8')
files=[p for p in O.rglob('*') if p.is_file() and not any(x in p.parts for x in ['_qa_packages','__pycache__','review_package']) and p.name not in ['minimal_revision_version_manifest.json','package_verification.json']]
files += [p for p in (R/'paper/work_d1').glob('*') if p.is_file() and p.suffix in ['.md','.json']]
manifest={'status':'PASS_ALIGNMENT_WAITING_USER_G_D2','date':'2026-11-11','protected_source_checks':len(source),'unchanged_table_figure_checks':len(protected),'protected_changes':changes,'files':{p.relative_to(R).as_posix():sha(p) for p in sorted(files)}}
mp=O/'analysis/minimal_revision_version_manifest.json';write(mp,manifest);files += [mp,pack/'README.md']
dest=pack/'Work_D2_GD2_review_light.zip'
with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
    for p in sorted(files):z.write(p,'README.md' if p==pack/'README.md' else p.relative_to(R).as_posix())
with zipfile.ZipFile(dest) as z:
    assert z.testzip() is None
    assert not any('_qa_packages' in x for x in z.namelist())
    for p in files:
        name='README.md' if p==pack/'README.md' else p.relative_to(R).as_posix()
        assert hashlib.sha256(z.read(name)).hexdigest()==sha(p)
    count=len(z.namelist())
result=dict(archive=dest.relative_to(R).as_posix(),bytes=dest.stat().st_size,sha256=sha(dest),files=count,archive_integrity='PASS',excluded_qa_packages=True,protected_source_changes=changes,experiments_run=False)
write(O/'analysis/package_verification.json',result)
print(json.dumps(result,ensure_ascii=False,indent=2))
