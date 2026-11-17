# Work E-R2 全局最佳响应认证

先读R2_final_report.md。R2_00固定对象，R2_01为已通过的攻击证书，R2_02为未达1%的防御试运行，R2_03/04给对象分层和验收。所有新文件只在本目录；原Work E、E-R1、D7/D8与候选均不修改。

结果分类：B，部分认证成功。B攻击归一化偏离上界约0.000496915%；B防御上界约31.3706%，不足以认证1%。没有发现经收益区间确认的显著战略偏离，也没有证明其不存在。不能称为联合近似均衡认证成功。

## 实际执行顺序

项目根目录执行，Python 3.11.7，原NumPy/SciPy/Matplotlib及标准库fractions；没有新增依赖安装：

```powershell
python -B work_e_r2/scripts/register.py
python -B work_e_r2/scripts/attacker.py
python -B work_e_r2/scripts/verify_attacker.py --full
python -B work_e_r2/scripts/defender.py
python -B work_e_r2/scripts/verify_defender.py --full
python -B work_e_r2/scripts/build_summary.py
python -B work_e_r2/scripts/plot_results.py
python -B work_e_r2/scripts/check_figures.py
python -B work_e_r2/scripts/verify_delivery.py --seal
python -B work_e_r2/scripts/verify_delivery.py
```

完整验证与报告/图表整理有部分时间重叠，但攻击完整认证先于防御搜索。defender拒绝覆盖已有分支日志；重做主试验须另存原目录并使用独立输出副本，不删除或覆盖历史证据。重新执行命令不表示已发生第二次实验。

候选收益与H24上角计算曾作一次计时/区间核对，R1 C0收益另作交叉复核；都是固定点认证辅助，不是新候选。主攻击37.20秒、主防御326.73秒；不包含后续全量复核及图表整理，不能当端到端耗时。

## 独立验证

```powershell
python -B work_e_r2/scripts/verify_attacker.py --full
python -B work_e_r2/scripts/verify_defender.py --full
python -B work_e_r2/scripts/verify_delivery.py
```

--full会从精确输入重做所有区间积分；攻击25次、可行响应校验及防御1999个上角，加上整棵分支树和源凸松弛核对。只读解析主证书可省略--full进行代数/覆盖快速复核，但不应将它称完整积分复现。每次验证重写自己的通过记录，主实验原始数据不改。

检查器是可独立运行的确定性程序，配合proofs/中的解析证明；完整复核共享公开区间积分核心，并非第二套独立积分算法，不宣称外部专家或形式化证明助手认证。机器C的全域舍入与保护行为未获证明。

## 文件说明

- frozen_candidate.json：继承R1逐分量精确分数和容量，整个R2不变。
- attacker_secants.json：全部认证梯度探针收益区间。
- attacker_certificate.json：强凹二次对偶界、线性核查界、全局收益区间。
- heuristic_D/A.json及controls/states：原SLSQP全部起点、退出码、控制、每槽资源和普通浮点状态；validated字段是修复后精确响应的ODE包络。
- defender_nodes.jsonl：1999个父子区域、精确边界、裁剪/下界和状态。
- defender_corner_evaluations.jsonl：所有比较上角ODE评价；这些上角可以超容量，仅作下界放松，不能当可行响应。
- source_relaxation_certificate.json：入口强凸子问题的精确指数传播与梯度包络。
- defender_bounds.csv：全部主阶段上下界日志，包括预算停止时的最终记录。
- objective_bounds.csv/combined_assessment.json：B/C0收益、偏离、归一化指标与最终分类。
- figures/：三张实际数据图，PDF/SVG和600dpi PNG；区间是确定性认证包络，不是统计置信区间。

最终状态WAITING_USER_E_R2_REVIEW；不修改论文，不更新正式算法，不把单侧通过改写为联合Nash认证。
