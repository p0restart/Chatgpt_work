"""Verify and package the D4 proposal. Does not execute research computations."""
from pathlib import Path
import hashlib
import json
import re
import zipfile

ROOT = Path(__file__).resolve().parents[4]
PAPER = ROOT/'paper/work_d4/decision_reorientation_20261112'
REPORT = ROOT/'reports/work_d4/decision_reorientation_20261112'
REVIEW = ROOT/'reviews/G_D4_direction_20261112_submission.md'

def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')

def main():
    checks=[]
    def check(name, passed, **detail):
        checks.append(dict(name=name, passed=bool(passed), **detail))
    baseline=json.loads((REPORT/'protected_before.json').read_text(encoding='utf-8'))
    changed=[p for p,h in baseline.items() if not (ROOT/p).exists() or hashlib.sha256((ROOT/p).read_bytes()).hexdigest()!=h]
    check('6014_existing_files_unchanged',len(baseline)==6014 and not changed, changed=changed)
    audit=json.loads((REPORT/'saved_evidence_audit.json').read_text(encoding='utf-8'))
    check('saved_evidence_checks_pass',audit['passed'],count=audit['check_count'])
    check('no_new_optimization_integration_or_research_tests',not any(audit[k] for k in ['optimization_executed','integration_executed','research_tests_executed']))
    for name in ['01_section_revision_map.md','02_contributions_evidence_risk.md','03_minimal_experiment_protocol.md','04_abstract_and_structure.md']:
        p=PAPER/name
        check(name+'_exists_and_has_content',p.exists() and p.stat().st_size>3000)
    md_files=[*PAPER.glob('*.md'),*REPORT.glob('*.md'),REVIEW]
    for p in md_files:
        text=p.read_text(encoding='utf-8')
        check(p.name+'_balanced_fences',text.count('```')%2==0)
        check(p.name+'_no_replacement_character','\ufffd' not in text)
        for label,target in re.findall(r'\[([^\]]+)\]\(([^)]+)\)',text):
            if target.startswith(('http://','https://')):
                continue
            target=target.split('#',1)[0]
            check(p.name+'_link_'+label,(p.parent/target).exists(),target=target)
    protocol=(PAPER/'03_minimal_experiment_protocol.md').read_text(encoding='utf-8')
    for phrase in ['PLAN_ONLY','0.50','WAITING_USER_G1_D4','E0','E1','18条','逐分量相同','不能称作原始t=0开环均衡','a(t−)']:
        check('protocol_contains_'+phrase,phrase in protocol)
    abstract=(PAPER/'04_abstract_and_structure.md').read_text(encoding='utf-8').split('## 中文摘要草稿\n',1)[1].split('**关键词',1)[0]
    check('abstract_reports_negative_and_local_boundaries',all(s in abstract for s in ['全部不占优','反例','局部数值候选','0.029%']))
    check('abstract_does_not_claim_replanning_result','重规划' not in abstract and '秒' not in abstract)
    result=dict(date='2026-11-12 Asia/Shanghai',status='WAITING_USER_G_D4_DIRECTION / WAITING_USER_G1_D4',
                passed=all(c['passed'] for c in checks),check_count=len(checks),checks=checks,
                note='Document/file checks only. No user approval, new research experiment, or independent review.',
                protected_files=len(baseline))
    write(REPORT/'delivery_verification.json',result)
    if not result['passed']:
        print(json.dumps([c for c in checks if not c['passed']],ensure_ascii=True,indent=2))
        raise SystemExit(1)
    artifact_files=sorted([p for p in PAPER.rglob('*') if p.is_file() and '__pycache__' not in p.parts]+[
        REPORT/'readiness_and_scope.md',REPORT/'saved_evidence_audit.json',REPORT/'delivery_verification.json',REVIEW])
    manifest=[dict(path=p.relative_to(ROOT).as_posix(),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in artifact_files]
    write(REPORT/'delivery_manifest.json',manifest)
    package=REPORT/'Work_D4_direction_review_20261112.zip'
    with zipfile.ZipFile(package,'w',zipfile.ZIP_DEFLATED) as archive:
        for p in artifact_files+[REPORT/'delivery_manifest.json']:
            archive.write(p,p.relative_to(ROOT).as_posix())
    with zipfile.ZipFile(package) as archive:
        check_zip=archive.testzip()
        count=len(archive.namelist())
    receipt=dict(package=package.relative_to(ROOT).as_posix(),bytes=package.stat().st_size,
                 entries=count,zip_integrity=check_zip is None,sha256=hashlib.sha256(package.read_bytes()).hexdigest())
    write(REPORT/'package_receipt.json',receipt)
    print(json.dumps(dict(passed=result['passed'],document_checks=len(checks),saved_evidence_checks=audit['check_count'],
                         protected_files=len(baseline),**receipt),ensure_ascii=True,indent=2))

if __name__=='__main__':
    main()
