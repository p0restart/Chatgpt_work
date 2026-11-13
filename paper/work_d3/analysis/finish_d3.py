"""Package local D3 review artifacts after document QA; no publication action."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / 'paper/work_d3'
PKG = OUT / 'review_package'
PKG.mkdir(exist_ok=True)
ZIP = PKG / 'Work_D3_review_light.zip'

(PKG / 'README.md').write_text('''# Work D3 轻量审阅包

日期：2026-11-11。解压后保持paper/work_d3与paper/work_d1、paper/work_d2的相对结构，从paper/work_d3/manuscript_zh.md或D3_handoff.md开始审阅。包内保留摘要、结论、主文、补充材料、引用库、作者侧审查、格式待办和验证结果，以及引用的D1/D2上下文、表格和源图。

该包供本地内容审阅，不是已套会议模板的投稿文件，也不是原始研究独立重跑环境。未包含results原始大目录、Python依赖环境或文献原PDF；源索引中指向这些目录的路径需回到完整项目使用。当前摘要/主文的本地链接有效，不代表外部审稿人已能访问所有数据。包内不嵌套自身ZIP。

最终会议、模板、篇幅和作者信息尚未确定，最终PDF视觉检查未执行。历史G-D1验收缺件不在本轮补签；G-D2通过依据是用户本次明确授权。
''', encoding='utf-8')

def files():
    picked = set()
    for p in OUT.rglob('*'):
        if p.is_file() and p != ZIP and '__pycache__' not in p.parts:
            picked.add(p)
    for base in ['paper/work_d1', 'paper/work_d2']:
        for p in (ROOT / base).glob('*'):
            if p.is_file() and p.suffix in {'.md', '.json'}:
                picked.add(p)
    for base in ['paper/work_d2/tables', 'paper/work_d2/figures']:
        for p in (ROOT / base).glob('*'):
            if p.is_file():
                picked.add(p)
    for name in ['reviews/G_D2_decision.md', 'reviews/APPROVAL_LOG.md',
                 'DECISIONS.md', 'logs/STATUS.md', '02_MODEL_SPEC.md',
                 'literature/fulltext_audit/source_manifest.json',
                 'paper/work_d2/analysis/minimal_revision_version_manifest.json']:
        p = ROOT / name
        if p.is_file():
            picked.add(p)
    return sorted(picked)

def pack():
    with zipfile.ZipFile(ZIP, 'w', zipfile.ZIP_DEFLATED) as archive:
        for p in files():
            archive.write(p, p.relative_to(ROOT).as_posix())

# Materialize the archive target so the local link check covers its actual path.
pack()
result = subprocess.run([sys.executable, str(OUT / 'analysis/verify_d3.py')], cwd=ROOT)
if result.returncode:
    raise SystemExit(result.returncode)

status = ROOT / 'logs/STATUS.md'
marker = '## 2026-11-11 / Work D3通用稿完成'
if marker not in status.read_text(encoding='utf-8-sig'):
    with status.open('a', encoding='utf-8') as f:
        f.write('''
## 2026-11-11 / Work D3通用稿完成
- 当前：G-D2 APPROVED；D3 READY_FOR_AUTHOR_REVIEW / TEMPLATE_PENDING。授权原文见reviews/G_D2_decision.md；不新增人工签字或最终投稿批准。
- 交付：paper/work_d3/manuscript_zh.md、中英文摘要、结论、补充材料、五项统一引用、压缩审查和投稿格式待办。现有第1–5节由12,260至5,694汉字，减少53.6%；新增摘要/结论另计，不等同会议页数。
- 85项文档与保存数据核验通过；20组公式原样保留，反向评价、反例、控制异质性和跨类偏离留主文。源码、模型、D1/D2源稿及实验记录未改；没有新优化、积分、研究测试或独立审稿。
- 5个D1历史哈希差异为换行和Markdown表格格式，规范化内容相同，详见D3审查及版本比较记录。
- 会议/模板/篇幅/作者信息待确定；可审阅通用稿，会议专用套版、最终PDF逐页检查及实际投稿尚未执行。入口paper/work_d3/D3_handoff.md。
''')

delivery = {}
for p in files():
    if p == OUT / 'analysis/delivery_manifest.json':
        continue
    delivery[p.relative_to(ROOT).as_posix()] = hashlib.sha256(p.read_bytes()).hexdigest()
(OUT / 'analysis/delivery_manifest.json').write_text(json.dumps({
    'date':'2026-11-11', 'status':'READY_FOR_AUTHOR_REVIEW_TEMPLATE_PENDING',
    'scope':'local review delivery, no original results or dependencies; archive/self manifest excluded from file hashes',
    'files':delivery}, ensure_ascii=False, indent=2), encoding='utf-8')
pack()
print(json.dumps({'package':ZIP.relative_to(ROOT).as_posix(),'bytes':ZIP.stat().st_size,
                  'sha256':hashlib.sha256(ZIP.read_bytes()).hexdigest(),
                  'archived_files':len(files())},ensure_ascii=False))
