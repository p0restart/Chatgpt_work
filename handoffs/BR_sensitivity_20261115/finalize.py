"""Check no paper changes, verify stored full-precision controls, package handoff."""
from pathlib import Path
import hashlib, json, zipfile
from datetime import datetime
from zoneinfo import ZoneInfo
import numpy as np
import pandas as pd

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,obj):p.write_text(json.dumps(obj,indent=2,ensure_ascii=False),encoding='utf-8')
def main():
    run=HERE/'run01'
    status=json.loads((run/'verification.json').read_text())
    assert status['status']=='SUCCESS'
    previous=json.loads((HERE/'paper_before.json').read_text())
    current={p.relative_to(ROOT).as_posix():sha(p) for p in (ROOT/'paper').rglob('*')
             if p.is_file() and '__pycache__' not in p.parts}
    changed=[name for name in previous if previous[name]!=current.get(name)]
    added=sorted(set(current)-set(previous))
    assert not changed and not added,(changed,added)
    inputs=json.loads((HERE/'input_manifest.json').read_text())['sources']
    for name,info in inputs.items():assert sha(ROOT/name)==info['sha256'],name
    # Read floats with round-trip parser, then compare exported CSV against selected JSON.
    a=pd.read_csv(run/'attacker_best_responses.csv',float_precision='round_trip')
    d=pd.read_csv(run/'defender_best_responses.csv',float_precision='round_trip')
    expected_rows={'defense_original_and_perturbed.csv':108,'attacker_best_responses.csv':108,
        'defender_best_responses.csv':72,'payoff_and_control_summary.csv':3,
        'constraints_by_slot.csv':48,'optimizer_attempts.csv':30,'integration_audit.csv':24,
        'convergence.csv':5,'objectives_all_integrators.csv':32}
    counts={}
    for name,expected in expected_rows.items():
        counts[name]=len(pd.read_csv(run/name));assert counts[name]==expected,(name,counts[name])
    error=0.
    for label in ['baseline','positive','negative']:
        selected=np.array(json.loads((run/f'A_{label}_selected_controls.json').read_text()))
        values=a[a.scenario==label].pivot(index='slot',columns='asset',values='attack').to_numpy()
        error=max(error,float(np.max(abs(values-selected[0]))))
    for label in ['positive','negative']:
        selected=np.array(json.loads((run/f'D_{label}_selected_controls.json').read_text()))
        for z,name in [(1,'isolation'),(2,'recovery')]:
            values=d[d.scenario==label].pivot(index='slot',columns='asset',values=name).to_numpy()
            error=max(error,float(np.max(abs(values-selected[z]))))
    assert error<=1e-15
    check=dict(time=datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),
        paper_files_checked=len(previous),paper_files_changed=changed,paper_files_added=added,
        original_sources_unchanged=True,csv_rows=counts,max_csv_roundtrip_control_error=error,
        scope='Package consistency and paper preservation; no extra optimization')
    dump(HERE/'delivery_checks.json',check)
    (HERE/'README.md').write_text('''# 攻防最佳响应敏感性实验交付

实际执行日期为2026-11-16（Asia/Shanghai）；目录和ZIP按用户指定保留20261115标识。

主要结果：run01/results_and_limitations.md（唯一主要汇总表），精确数据见run01/payoff_and_control_summary.csv。数值检查见run01/numerical_audit.md与verification.json。方案和基准参数核查见run01/protocol_and_baseline.md。原始及扰动完整防御控制见run01/defense_original_and_perturbed.csv；双方响应见attacker_best_responses.csv、defender_best_responses.csv。所有槽号、资产号均从1开始；原始程序控制数组从0开始。

本轮没有绘图，完整逐资产、逐时段差异在control_differences.csv。没有修改论文、参考文献、章节或图表编号；delivery_checks.json记录论文树与原数据源的前后SHA核查。新实验不构成历史待审事项或G2结果批准。

## 复现

解压到一个新目录（不要覆盖原项目），进入BR_sensitivity_20261115目录。Python 3.11.7；NumPy/SciPy/Pandas精确版本见run01/requirements.txt与environment.json。

```powershell
python -m pip install -r run01/requirements.txt
python run_experiment.py --out rerun01
```

输出目录必须不存在。原始inputs只读，源码使用runtime/src下D7原版core.py和game_solver.py；运行前自动校验SHA。每次只执行三次攻击响应、两次防御响应，并各作一次H96固定对手精度审计；不执行完整交替博弈。不同环境下数值可能略变，必须重新检查所有质量门槛；不要求耗时相同。

run01/run.log为时间日志，*_optimizer_raw.json记录30次SLSQP完整起点/返回控制及状态，optimizer_attempts.csv便于筛查。state_trajectories.csv、objectives_all_integrators.csv保存32组积分结果，integration_audit.csv保存24组精度比较。constraints_by_slot.csv逐槽保存容量及界限；positive_negative_comparison.json辅助区分可分辨变化与数值误差。

prepare.py仅用于本次在原项目定位并冻结输入；重现时无需运行。finalize.py仅用于原项目交付保护和打包；重现优化仅需run_experiment.py、runtime和inputs。没有网络或外部服务依赖。包内未包括第三方论文全文。

package_manifest.json记录除ZIP自身、校验旁文件及缓存外每个交付文件的SHA256；ZIP内置CRC已核验。审计系同一执行者在本地运行环境所作，不声称外部独立研究者已复现或审阅。
''',encoding='utf-8')
    (HERE/'STATUS.md').write_text(f'''# E-EXP状态

{check['time']}：EXPERIMENT_COMPLETE_WAITING_USER_REVIEW。

本轮完整用户指令授权限定实验；方案先于优化写入。5个响应任务与30次SLSQP完成，数值审计通过。交付后停止，不进入论文修订。历史G1/G2及D7待审结果状态不作变更。

论文保护：{len(previous)}个文件SHA未变，未新增论文文件。结果属于固定合成实例的局部数值响应证据，不是全局Nash证明。
''',encoding='utf-8')
    excluded={'BR_sensitivity_results_20261115.zip','BR_sensitivity_results_20261115.zip.sha256','package_manifest.json'}
    files=[p for p in HERE.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name not in excluded]
    manifest={p.relative_to(HERE).as_posix():dict(bytes=p.stat().st_size,sha256=sha(p)) for p in files}
    dump(HERE/'package_manifest.json',manifest)
    files.append(HERE/'package_manifest.json')
    archive=HERE/'BR_sensitivity_results_20261115.zip'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in files:z.write(p,Path(HERE.name)/p.relative_to(HERE))
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        for name,info in manifest.items():
            assert hashlib.sha256(z.read(HERE.name+'/'+name)).hexdigest()==info['sha256'],name
    (HERE/'BR_sensitivity_results_20261115.zip.sha256').write_text(sha(archive)+'  '+archive.name+'\n',encoding='utf-8')
    print(json.dumps(dict(archive=str(archive),bytes=archive.stat().st_size,files=len(files),delivery_checks=check),ensure_ascii=False),flush=True)
if __name__=='__main__':main()
