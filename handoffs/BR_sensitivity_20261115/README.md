# 攻防最佳响应敏感性实验交付

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
