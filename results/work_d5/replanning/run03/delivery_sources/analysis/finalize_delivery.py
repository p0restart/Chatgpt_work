"""Record review-ready status and package the completed D5 outputs."""
from pathlib import Path
import argparse
import hashlib
import json
import zipfile

ROOT=Path(__file__).resolve().parents[3]


def append_once(path,text):
    if text not in path.read_text(encoding='utf-8'):
        with path.open('a',encoding='utf-8') as f:f.write(text)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('run');a=ap.parse_args();out=Path(a.run).resolve()
    report=out/'D5_execution_report.md';assert report.exists()
    verification=json.loads((out/'independent_validation.json').read_text())
    assert verification['passed']
    qa=json.loads((out/'figures/automated_qa.json').read_text())
    assert all(x['exit_code']==0 for x in qa)
    required=['experiment_protocol.md','executed_controls.csv','planned_controls.csv','trajectories.csv',
        'objectives.csv','comparisons.csv','solver_audit.csv','timing.csv','D5_execution_report.md']
    assert all((out/f).exists() for f in required)
    meta=json.loads((out/'metadata.json').read_text())
    meta['review_status']='WAITING_USER_D5_REVIEW'
    meta['independent_validation_passed']=True
    meta['figure_automated_qa_passed']=True
    (out/'metadata.json').write_text(json.dumps(meta,indent=2),encoding='utf-8')
    note=f'''\n## 2026-11-13 / Work D5：COMPLETED / WAITING_USER_D5_REVIEW
- 三预算、两条公共攻击、P/G/R，共18条完整轨迹已完成，G/R各18次重规划；登记数值门槛和{verification['checks']}项作者侧复核通过。
- 三预算E0下G略劣于R，E1下略优；不宣称普遍优势、全局Nash或真实云实时性。全部分项、控制、候选、失败及wall-clock已保存。
- run01为预检JSON记录失败，run02为CSV保存中断；原件保留，run03承接通过的B1.2并同参数完成两预算，重复候选核对一致。未修改D3/原冻结模型/历史数据。
- 最终入口{out.as_posix()}/D5_execution_report.md；人工审阅reviews/G_D5_experiment_submission.md。D5结果未获人工批准；其他待审事项不代批。\n'''
    # Keep the logged entry project-relative, including after an interrupted package build.
    note=note.replace(out.as_posix(),out.relative_to(ROOT).as_posix())
    append_once(ROOT/'logs/STATUS.md',note)
    append_once(ROOT/'DECISIONS.md',
        '\n- **2026-11-13 / Work D5 实验完成，非结果批准**：18完整公平评价轨迹和登记数值门槛/作者侧复核通过；三预算E0下G略劣R、E1略优，保留负结果和计算成本。run01/run02中断记录保留，最终run03。提交reviews/G_D5_experiment_submission.md，状态WAITING_USER_D5_REVIEW；不改D3、不升级均衡或实时性主张，未批准旧D4/P0待审事项。\n')
    append_once(ROOT/'reviews/APPROVAL_LOG.md',
        '\n### D5结果提交（非批准）\n- 2026-11-13：18轨迹完成，提交G_D5_experiment_submission.md；WAITING_USER_D5_REVIEW。尚未收到本轮结果人工批复，不将执行授权改为结果批准。\n')
    manifest=[]
    for p in sorted(out.rglob('*')):
        if p.is_file() and p.name!='delivery_manifest.json' and '__pycache__' not in str(p):
            manifest.append(dict(path=p.relative_to(out).as_posix(),bytes=p.stat().st_size,
                sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
    (out/'delivery_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    package=ROOT/'reports/work_d5/Work_D5_review_package.zip';package.parent.mkdir(parents=True,exist_ok=True)
    assert not package.exists()
    with zipfile.ZipFile(package,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in out.rglob('*'):
            if p.is_file() and '__pycache__' not in str(p):z.write(p,p.relative_to(ROOT))
        z.write(ROOT/'reviews/G_D5_experiment_submission.md','reviews/G_D5_experiment_submission.md')
        z.write(ROOT/'paper/work_d5/revision_log.md','paper/work_d5/revision_log.md')
        for name in ('run01','run02'):
            for f in ('metadata.json','protected_after.json'):
                p=out.parent/name/f
                if p.exists():z.write(p,p.relative_to(ROOT))
    with zipfile.ZipFile(package) as z:assert z.testzip() is None
    receipt=dict(status='WAITING_USER_D5_REVIEW',files=len(manifest),zip_bytes=package.stat().st_size,
        zip_sha256=hashlib.sha256(package.read_bytes()).hexdigest(),zip_crc_passed=True,
        package=str(package),scope='complete final run and source snapshots; prior interrupted-run metadata included; full old runs remain in project')
    (package.parent/'delivery_receipt.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
    print(json.dumps(receipt))


if __name__=='__main__':main()
