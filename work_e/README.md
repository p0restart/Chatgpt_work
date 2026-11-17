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

交付校验（不优化）：

```powershell
python -B work_e/scripts/verify_delivery.py
```

它检查模型/配置完全一致、原1102来源哈希、全部矩阵特征对、90次优化退出码及固定控制状态/目标保存一致性，再检查SHA256SUMS。verification.json是数据与文件自检，不是全局数学证明或外部认证。
