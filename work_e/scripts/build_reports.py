"""Build Work E review reports from saved measurements; no optimization."""
import sys,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
import numpy as np
import pandas as pd
from diagnostics import OUT,load,unpack

def read(p):return json.loads((OUT/p).read_text(encoding='utf-8'))
def write(name,text):(OUT/name).write_text(text.strip()+'\n',encoding='utf-8')
def table(df,cols=None):
    if cols is not None:df=df[cols]
    return df.to_markdown(index=False,floatfmt='.10g')

def main():
    assert read('results/refinement_completed.json')['completed']
    d=pd.read_csv(OUT/'E3_experiment_results.csv');rr=pd.read_csv(OUT/'results/hessian_refinement.csv')
    s=pd.read_csv(OUT/'results/new_multistart_summary.csv');ic=pd.read_csv(OUT/'results/integration_checks.csv')
    fc=pd.read_csv(OUT/'results/feasible_direction_checks.csv');vi=pd.read_csv(OUT/'results/VI_residuals.csv')
    coarse=read('results/coarse_global_bound.json');comp=read('results/new_multistart/comparison.json')
    assert comp['completed'] and len(d)==5 and len(s)==3
    audit_rows=[];attempt_seconds=[];attempts=0
    for name in s.path:
        ad=read(f'results/new_multistart/{name}/final_same_pair_audits.json')
        for H,g in ad.items():
            for player in ('D','A'):
                for raw in g[player]['raw']:
                    attempts+=1;attempt_seconds.append(raw['seconds'])
                    audit_rows.append(dict(path=name,H=int(H),player=player,start=raw['start'],success=raw['success'],status=raw['status'],nit=raw['nit'],seconds=raw['seconds'],violation=raw['violation'],projected_residual=raw['projected_residual'],accepted=raw['accepted']))
        ar=pd.read_csv(OUT/f'results/new_multistart/{name}/optimizer_attempts.csv')
        attempts+=len(ar);attempt_seconds.extend(ar.seconds)
    audits=pd.DataFrame(audit_rows);audits.to_csv(OUT/'results/final_audit_optimizer_attempts.csv',index=False)
    assert audits.success.all() and (audits.status==0).all()
    assert s.passed.all() and s.all_iteration_optimizer_success.all()
    comparison=max(r['distance'] for r in comp['distances'])
    candidate=vi[vi.point=='saved_candidate'].iloc[0]
    dr=d.rename(columns={'point':'策略点','lambda_D':'D Hessian最小特征值','lambda_A':'-A Hessian最小特征值','lambda_H':'H最小特征值','cross_norm':'交叉块范数'})
    write('E3_numerical_diagnostics.md',f'''
# E3 数值诊断与计算成本

日期：2026-11-15。范围：D7新图，离线B1.2/K6/T10/H48；预登记见protocol.md。本轮实际完成五个84维矩阵、最弱样点两次完整矩阵复核、三条新交替路径及H48/H96同对手三起点响应复核。原结果未覆盖。

## E3.1 导数、边界与积分

复用原解析离散灵敏度，中心差分F构造84×84 Jacobian。未安装torch/jax；未新增依赖。Hessian包含完整状态及目标累计影响。完整矩阵差分步长1e-4；最弱点另用1e-5及H96复算。FD不是自动微分，亦非区间算术。

五点解析梯度与可行方向目标中心差分最大误差{d.gradient_max_error.max():.10g}；步长1e-3/1e-4/1e-5。自身块未经对称化的最大不对称误差D={d.D_asymmetry.max():.10g}、A={d.A_asymmetry.max():.10g}。先检查再取对称部分，没有通过强行对称掩盖误差。

内部点用两玩家独立随机方向；保存候选用正分量间同槽资源转移，近零变量固定，方向与步长的双侧容量/箱可行性逐项检查。完整边界Hessian本身通过光滑多项式延拓作无约束差分，未将超出约束的中心扰动称作可行偏离。原始目标不裁剪策略/状态。候选活跃面检查和内部最小特征向量检查见results/feasible_direction_checks.csv，最大Rayleigh复核差{fc.error.max():.10g}。

独立DOP853逐边组装ODE、逐控制间断点积分，rtol=1e-12/atol=1e-14。五点H48/H96/H192与其目标最大差{ic.error_DOP853.max():.10g}；灵敏度和simulate目标最大差{ic.error_simulate.max():.10g}；H48与细化梯度最大分量差{ic.gradient_difference_H48.max():.10g}。DOP853仅验证固定控制目标和指定方向二阶差分，不提供全域误差界或完整独立Hessian。二阶目标差分的小步长有消减误差，原值均保留，主诊断用梯度差分。

## E3.2/E3.3 曲率与伪梯度

{table(dr,['策略点','D Hessian最小特征值','-A Hessian最小特征值','H最小特征值','交叉块范数'])}

没有发现经复核的负曲率方向。所有点m_D、m_A为正且交叉块范数小于sqrt(m_D*m_A)，支持这些点的分块正定条件。点内特征值的单位为本报告未重标度的逐槽欧氏坐标；不能把它直接当连续时间L2模数。

最弱样点完整矩阵复核：

{table(rr,['point','fd_step','H_steps','lambda_D','lambda_A','lambda_H','J_max_difference'])}

这只说明样点和差分稳定性；没有覆盖全部策略域、所有预算、事件后子博弈或K12。正样本不是全局凸性/强单调性证明，也没有反证纯均衡存在或唯一。

## E3.4 新多初值搜索与旧记录复核

直接调用原strict_solve，完整三路径初始为均匀、全零及固定种子随机；未修改停止门槛、阻尼或正式源码。实际初始/最终策略、每轮双方响应退出码、改进量、控制轨迹全部保存于results/new_multistart。种子20261115/20261215/20261315只作为整数标识；starts=1的确定性路径不会因种子不同自动变成独立随机实验。

{table(s,['path','iterations','J_D','J_A','gap_D','gap_A','incumbent_residual_D','incumbent_residual_A','max_violation','seconds'])}

三路径最终策略最大两两距离{comparison:.10g}。均因原登记局部门槛停止，未触及40轮上限，未观察到阻止终止的持续循环。无法由此否定所有其他初始点的振荡。两次精度审计均固定同一最终候选，H48/H96分别做双方当前/零/随机三起点；本轮共{attempts}次优化尝试（迭代{int(s.optimizer_attempts.sum())}次，末端审计{len(audits)}次）均正常退出。逐项见final_audit_optimizer_attempts.csv及各路径optimizer_attempts.csv。末端最大容量违反{max(s.max_violation.max(),audits.violation.max()):.10g}；固定控制H48/H96最大积分差{s.integration_error.max():.10g}。

已发现改善是全局gap下界，不是上界。控制接近、收益接近、退出成功和小残差都不证明存在唯一Nash。历史D7三路径另存results/historical_multistart.csv，明确为旧记录重析，不充作本轮新实验。

两次后处理错误完整保留：①uniform优化与末端审计完成后，导出重复start字段触发TypeError；修为attempt_index后从已保存uniform结果继续zero/random，没有重跑uniform优化。②所有精度计算完成后，来源清单默认GBK读取UTF-8中文文件名触发解码错误；改为显式UTF-8，只继续来源校验，没有重算矩阵。证据分别为export_failure01.json、verification_failure02.json。没有丢弃不利结果；最终状态/目标/每槽预算是固定控制后处理保存，非另一次优化。

## E3.5 计算成本及全域认证可行性

实际D/A/联合维度72/12/84；一次联合梯度约{d.gradient_seconds.min():.3f}–{d.gradient_seconds.max():.3f}秒；完整Jacobian/Hessian约{d.hessian_seconds.min():.2f}–{d.hessian_seconds.max():.2f}秒（最弱点H96另见表）；最小特征值分解约{d.eigen_seconds.min():.5f}–{d.eigen_seconds.max():.5f}秒。单次SLSQP响应实测{min(attempt_seconds):.4f}–{max(attempt_seconds):.4f}秒，中位数{np.median(attempt_seconds):.4f}秒。环境与完整参数见run_config.json；计时是本机负载下实测，计算阶段有并行独立进程，不作硬件通用基准。

矩阵诊断成本可承受；84维均匀区间细分不可直接穷举。更合理的是利用DAG稀疏二阶灵敏度、容量约束和分块界，而非增加大量随机采样。尝试的粗Gronwall全域界给防御曲率下界{coarse['defense_lower_bound']:.10g}，不具有认证能力；负的是保守下界，不是实际负特征值。推导见E2。

当前候选的自然VI残差（∞）{candidate.natural_residual_inf:.10g}、线性VI gap {candidate.linear_VI_gap:.10g}。其余见results/VI_residuals.csv；只有补足自身凸性/强单调等前提后才能用作Nash误差或解距离上界。
''')
    write('E4_feasibility_conclusion.md',f'''
# E4 证明可行性判断

2026-11-15。当前属于**路线C：纯策略Nash存在性尚未证明**；这是证明状态，不是无均衡判定。五点曲率均正且三路径稳定，因此保留原模型继续研究全域曲率有明确依据，尚不能采用路线A/B作为已完成结论。

|目标|对象B：精确K槽|对象C：RK4|依据|
|---|---|---|---|
|策略域非空、紧致、凸|已证明|已证明|闭箱与逐槽独立线性容量|
|状态解唯一|已证明|固定有限步映射单值|ODE适定不等于RK4全域不越界|
|目标连续/光滑|已证明|多项式延拓已证明；全域保护有效性待证|E0/E1|
|防御自身凸性|待证明|待证明|样点最小值{d.lambda_D.min():.9g}，无全域界|
|攻击自身凹性|已证明强凹|待证明|B模数至少10/6；C采样最小值{d.lambda_A.min():.9g}|
|伪梯度强单调性|待证明|待证明|C五点最小值{d.lambda_H.min():.9g}|
|纯Nash存在|未证明；有明确充分条件|未证明；有明确充分条件|防御拟凸/响应凸值或全域强单调未闭合|
|纯Nash唯一|未证明|未证明|全域正定/加权条件/响应压缩均未认证|
|数值均衡收敛保证|未证明|未证明|三路径局部通过不能证明全局收敛|

没有找到对应充分条件的数值反例；也没有完成严格全域证书。粗界为负只表明该估计太松，不是条件不满足。自身凸性本来只是存在性的充分路线之一，即便以后证实非凸，也须进一步检查拟凸或响应集合结构，不能据此断言没有纯Nash。

推荐先保留原模型，尝试认证K6/B1.2防御全域曲率或最优响应凸值；若闭合即可先证明存在性。唯一性另按全域分块界或固定Rosen权重认证。优先级是证明自身凸性→存在性→交叉界/唯一性→算法条件与误差，不先改方程或提高成本。

最小下一包工作：①精确二阶离散灵敏度及误差包络；②利用八边DAG和逐槽容量建立防御曲率下界；③核定RK4全域有效性和B/C导数桥接。若这些界过松，再选响应凸值/受限策略邻域的理论；任何受限结论须写清域，不能回写为原全域定理。无须再跑三预算全实验或大规模随机搜索。

待用户批准E结论后再决定是否投入上述证明；本次不修改第三章、模型、参数或正式算法。
''')
    write('E_final_report.md',f'''
# Work E 均衡证明可行性报告

2026-11-15（Asia/Shanghai）。状态：**WAITING_USER_E_REVIEW**。

## 审查信息

本轮为同一执行者的数学推导、数值实验和自检；输入为D7固定新图与D8.1/D8.2有效材料，原文/代码/结果保持不变。没有外部数学认证或人工批准记录。完整来源指纹、参数、随机种子和复现命令分别见source_manifest.json、run_config.json、README.md。

## 问题1：当前能否证明Nash存在？

**尚不能证明原纯策略Nash存在，也没有证明它不存在。** 双方域非空紧凸且独立，精确ODE状态唯一、收益连续；固定防御时攻击目标可证明强凹。Debreu/Fan/Glicksberg型纯均衡路线仍缺防御全域拟凸性或最优响应凸值；RK4还需单独证明离散曲率和全域保护有效性。标准混合扩展存在只能作为另一个策略概念的补充，不代替本问题。详见E1。

## 问题2：当前能否证明Nash唯一？

**尚不能。** 五个代表点的完整伪梯度对称部分均正定，但未证明整个84维策略域H(z)≥mu I。Rosen加权条件与全局最佳响应压缩亦未认证，不能用多初值相近代替唯一性。当前没有负曲率反例，数值证据支持继续尝试严格证明，不能把本轮称作唯一均衡已获证。详见E2/E4。

## 问题3：数学与数值证据如何？

实际主对象为六资产、六槽、B1.2/T10/H48；防御72维、攻击12维。五个点覆盖严格内部、已存候选、99.9%容量、随机资源分配、低防御高攻击。

{table(dr,['策略点','D Hessian最小特征值','-A Hessian最小特征值','H最小特征值'])}

最弱点缩小差分步长后的lambda_min(H)={rr.iloc[0].lambda_H:.12g}，H96复核为{rr.iloc[1].lambda_H:.12g}。可行方向梯度误差最大{d.gradient_max_error.max():.6g}；五点独立DOP853目标核对误差最大{ic.error_DOP853.max():.6g}。策略逐分量在run_config.json，完整矩阵、特征向量与可行方向在results下，未只保留特征值摘要。

精确B中攻击强凸成本模数至少Delta=10/6（逐槽欧氏坐标）；D曲率的保守全域下界尝试没有闭合，负粗界不是反例。样点结果既不覆盖全域，也不覆盖所有预算/K12/动态事件子问题；H细化和DOP853核对都不是严格区间误差证书。

## 问题4：原SLSQP+交替能否可靠求解均衡？

**在本次三条小规模路径上，它稳定给出通过登记局部响应检查的候选；尚无求得全局Nash的保证。** 三条新路径分别经{s.iterations.tolist()}次更新终止，最终策略两两最大差{comparison:.8g}；共{attempts}次SLSQP尝试均正常退出，最大已发现防御改善{s.gap_D.max():.8g}，当前点投影残差最大{s[['incumbent_residual_D','incumbent_residual_A']].max().max():.8g}。各最终候选H48/H96均做固定同对手三起点复核，完整退出码/控制/预算/状态已保存。

这些改善量是未知全局偏离的下界。当前已存候选线性VI gap={candidate.linear_VI_gap:.8g}，可计算但尚不能无条件充作Nash误差上界。即使以后证明唯一，交替收敛仍须额外证明。详见E3/E5。两次后处理错误已公开记录并修复，不涉及优化失败后重选结果。

## 问题5：下一步最合理的路线？

**保留现有模型，先认证K6/B1.2的防御全域曲率/响应凸值，争取先证明存在性；唯一性作为独立的条件性目标。** 现有样点正曲率余量较大，值得做结构化二阶灵敏度和全域分块界。最小工作量是一个固定场景的数学认证包，不是重跑全部正式实验。若只能认证自身凸性，可证明存在性并保留唯一性未证；若能进一步认证强单调，再分析投影/外梯度收敛及可计算误差。若界始终过松，则转向其他响应拓扑或明确受限域理论，不能擅改成本、传播或策略来追求定理。

## 提交边界

本轮交付E0–E5及原始证据。E结论尚待用户审阅；第三章、冻结方程、正式求解器、原参数和D7/D8结果均未修改。审批日志未伪填本轮结果批准。
''')
    write('README.md','''
# Work E 读取与复现

先读E_final_report.md，再读E1/E2/E3/E4/E5；公式和来源见E0两文件、sources.md。仅本轮work_e是新交付。

实际已运行（项目根目录，Python 3.11.7）：

```powershell
python -B work_e/scripts/diagnostics.py benchmark
python -B work_e/scripts/diagnostics.py run
python -B work_e/scripts/search_and_audit.py
python -B work_e/scripts/refine_and_verify.py
python -B work_e/scripts/build_reports.py
```

search_and_audit首次在uniform完成后的CSV导出遇字段重名错误，修复后继续一次；已有uniform结果被读取，没有重复优化。固定控制状态/目标/预算后来单独调用save_fixed_outputs补齐，不属于重新求解。数据保留，见results/new_multistart/export_failure01.json。

refine_and_verify在全部精度数据保存后，默认GBK读取含中文文件名的UTF-8来源清单失败；改为显式UTF-8后只继续来源校验，没有重算矩阵或积分，见results/verification_failure02.json。

如需重新计算，保持原交付，先设新目录；脚本仍读D7原文件，不改变原研究源码。需要NumPy/SciPy/Pandas/PyYAML及现有项目依赖，无自动微分库或新增安装。约数分钟至十余分钟，取决于机器负载。三条交替路径按原41次检查上限停止。

```powershell
$env:WORK_E_OUTPUT = Join-Path (Get-Location) 'work_e_reproduction01'
python -B work_e/scripts/diagnostics.py run
python -B work_e/scripts/search_and_audit.py
python -B work_e/scripts/refine_and_verify.py
Remove-Item Env:WORK_E_OUTPUT
```

该命令只说明复现方法，不表示已再次运行。诊断拒绝覆盖已有完成结果；search脚本只复用已有完整路径以支持后处理中断恢复。报告生成脚本在新目录中只需三阶段数值输出即可重建动态报告，E0/E1/E2/E5静态理论文件保留原件供对照。

目录说明：E3_experiment_results.csv为五点主矩阵结果；results/*.npz含策略/原Jacobian/对称块/特征向量；*refinement.csv为完整矩阵精度复核；integration_checks.csv与feasible_direction_checks.csv为独立积分和边界证据；new_multistart含全部实际初末控制、迭代trace、退出码、逐槽预算、状态与同对手审计；VI_residuals.csv只是一阶VI证据。
''')
    # Regeneration replaces only the data-derived tail, preserving theory.
    for filename,marker in [('E1_existence_audit.md','\n## E3完成后的判定'),('E2_uniqueness_theory.md','\n## 全域界的具体尝试与E3判定')]:
        p=OUT/filename
        if p.exists():p.write_text(p.read_text(encoding='utf-8').split(marker)[0].rstrip()+'\n',encoding='utf-8')
    with (OUT/'E1_existence_audit.md').open('a',encoding='utf-8') as f:
        f.write(f'\n## E3完成后的判定\n\n五个RK4样点防御Hessian最小特征值下限{d.lambda_D.min():.10g}、攻击成本Hessian下限{d.lambda_A.min():.10g}；没有反例，但不构成全域证明。防御凸性、C攻击凹性分类仍为B（待证），不是A或C。精确B攻击凹性仍为A。纯Nash存在性仍未证明。\n')
    with (OUT/'E2_uniqueness_theory.md').open('a',encoding='utf-8') as f:
        f.write(f'''
## 全域界的具体尝试与E3判定

不改原参数，令b=max_i sum_j beta_ji=.29，b2=max_i sqrt(sum_j beta_ji²)，ell=b-min(delta)=.19，M=sqrt(b2²+.3²)，N=2b2+.3。对单位逐槽策略方向V，有||v(t)||₂≤||V||₂；状态Jacobian的无穷范数矩阵测度≤ell，||f_u v||∞≤M||V||₂。故一阶变分上界Y(t)=M*(exp(ell*t)-1)/ell。

二阶变分强迫项由||f_xx[y,y]||∞≤2b||y||∞²、||f_xu[y,v]||∞≤N||y||∞||v||₂给出。令W(t)=integral_0^t exp(ell*(t-tau))*(2bY(tau)²+2NY(tau))dtau，则状态收益曲率绝对值≤sum(q)*integral_0^T W(t)dt * ||V||₂²。原omega=0，直接行动成本曲率为Delta||V||₂²。

实际代入该保守界，状态曲率范数上界约{coarse['state_hessian_norm_bound']:.10g}，防御曲率下界约{coarse['defense_lower_bound']:.10g}。公式是全域的保守估计，数值代入使用普通双精度积分、非区间认证；由于余量极松，即使改为外向舍入也不能给出有用正下界。负下界不能当实际负曲率。需要利用DAG方向、符号、容量和局部状态包络改进，不能仅把最坏绝对值相加。

E3五点实际lambda_min(H)最小{d.lambda_H.min():.10g}，差分步长/积分细化保持；未发现负方向，但全域mu仍待证。当前全局唯一性未证明，分块/Rosen/压缩路线都未获全域认证。详见E3原始矩阵。
''')
    write('status_log.md','''
# Work E 状态与边界

- 2026-11-15：接收E启动授权，只允许独立审计和低成本预实验。
- E0：实际模型/新拓扑/参数/正文/实现核对完成。
- E1/E2：完成适定性、策略域、攻击凹性与条件性存在唯一性分析后启动E3。
- E3：五点矩阵与精度复核、独立积分、三条新交替路径、最终同对手审计完成。导出错误和恢复完整保留。
- E4：当前路线C（尚未证明纯均衡存在，非否定存在）；局部数值支持进一步认证。
- E5：算法条件、VI误差与最小后续证明工作评估完成；未替换正式算法。
- WAITING_USER_E_REVIEW：结果供人工审阅。批准之前不修改第三章、不重写模型、不改参数、不宣称唯一Nash；不伪填审批日志。
''')
    original=read('source_manifest.json');changed=[p for p,h in original.items() if hashlib.sha256((ROOT/p).read_bytes()).hexdigest()!=h]
    required=['E0_model_inventory.md','E0_mathematical_formulation.md','E1_existence_audit.md','E2_uniqueness_theory.md','E3_numerical_diagnostics.md','E3_experiment_results.csv','E4_feasibility_conclusion.md','E5_solver_assessment.md','E_final_report.md']
    report=dict(original_files_checked=len(original),original_changes=changed,required_files_present=all((OUT/p).exists() for p in required),points=len(d),fresh_paths=len(s),optimizer_attempts=attempts,all_optimizer_status_zero=bool(audits.success.all() and (audits.status==0).all() and s.all_iteration_optimizer_success.all()),sample_negative_eigenvalue_count=int((d[['lambda_D','lambda_A','lambda_H']]<0).to_numpy().sum()),max_path_distance=comparison,strict_global_certificate=False,state='WAITING_USER_E_REVIEW')
    assert not changed and report['required_files_present']
    (OUT/'delivery_checks.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False),flush=True)

if __name__=='__main__':main()
