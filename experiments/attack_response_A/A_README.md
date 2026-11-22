# Work A：攻击强度时变下的防御策略响应

2026 年 11 月 18 日完成，待用户独立审计。仅使用合成模型。沿用冻结 D7 六资产拓扑、A=0.8、B=1.2、T=10，将控制时域划分为 12 槽。Web 的预设 0.40 不变，故 API 请求峰值 0.50 按登记规则裁剪到 0.40；实际为 **0.20 → 0.40 → 0.20**。

**主要发现。** 在相同实际输入下，重规划（C2）的综合损失由不更新（C1）的 8.361145 降至 8.350089，绝对下降 0.011056、相对下降 0.1322%。匹配状态实验确认：第 5 槽 API 隔离增强、恢复减弱，第 9 槽方向反转。效应不是逐时占优：部分时点 API、数据库及全网均值受损略升，Web 的受损未降低；业务中断和两项行动投入成本均增加。C0 仅为正常攻击参照，不用于归因重规划收益。

## 复现

可从压缩包解压目录直接运行，无需 Git 或项目其他实验文件。`A_source/` 来自仓库 `1409b7e71451564613c1ded61762a2724d0d0b98`；脚本校验 SHA-256。建议采用 `A_run_config.json` 的 Python 3.11 和确切依赖版本；运行环境需安装 NumPy、SciPy、PyYAML、pandas、Matplotlib（含 Pillow）。

```powershell
python A_reproduce.py --output ./fresh_run
python A_plot.py --root ./fresh_run
```

`A_reproduce.py` 重新求解五份计划并生成所有数值 CSV、配置、逐次优化轨迹、验收明细和运行日志。已有交付目录不被覆盖。从仓库执行时可加 `experiments/attack_response_A/` 前缀。若单独验证交付的 K6/K12 固定控制对照，运行 `python A_verify_grid.py`；它检查同一控制函数，不重新优化。报告和交接文本为人工解读，不由脚本自动生成。

## 阅读顺序

1. `A_model_parameter_audit.md`、`A_experiment_protocol.md`：来源、参数、信息边界。
2. `A_results.csv` / `A_state_trajectories.csv`：执行计划和全部 RK4 采样；`A_plans.csv`：五份完整优化计划，不等同于实际执行；`A_matched_response.csv`：两事件同状态差值。
3. `A_metrics.csv` 和 `A_figures/`：完整损失分解、图 A1/A2 与 A2 配套小表。图中虚线为重规划时点，状态用百分数显示；CSV 中为比例。
4. `A_validation.md`、`A_optimizer_trace.json`、`A_execution.log`、`A_replay.log`、`A_replay_checks.json`：数值与复现审计。`A_paper_summary.md`、`A_handoff.md`：供论文对话审阅，不是已通过的 G2 或已改稿件。
