# Work B：攻击重点转移下的防御资源空间响应

2026-11-18，供独立审核。冻结 D7 六资产合成模型，主容量 1.2。实际两入口强度按 P=(0.40,0.20) → Q=(0.20,0.40) → P 切换，每段四槽；攻击投入和努力成本均不变。不使用实验 A 的数据、控制或结果。

最主要的证据是图 B1(c)：第 5 槽匹配对照中，首槽 API 和 Web 资源均略增，随后第 6–8 槽出现 API 减、Web 增。共同实际输入下，重规划综合损失由 7.922288 降至 7.904890（0.2196%）；但累计加权受损损失增加 0.012550，数据库、全网终点受损比例均上升。净收益来自行动成本下降，并非整体安全状态改善。

## 独立复现

解压，在 `attack_response_B` 内执行（Python 3.11，NumPy、SciPy、PyYAML、pandas、Matplotlib 版本见 `B_run_config.json`）：

```powershell
python B_reproduce.py --output ./fresh_run
python B_plot.py --root ./fresh_run
```

不需要原仓库、实验 A 或插件。脚本校验 `B_source/` 的 SHA-256，对应仓库版本 1409b7e71451564613c1ded61762a2724d0d0b98。绘图复现无需布置额外的图形审计工具。使用新输出目录，避免覆盖。两份运行日志的时长允许不同。

- `B_results.csv`：C0/C1/C2 实际执行控制、资源量/占比、槽起止状态；`B_state_trajectories.csv`：所有 RK4 子步状态；`B_metrics.csv`：六资产/全网峰值、终值、目标及分解。
- `B_plans.csv`：五份完整预测计划，未执行尾部也保留；`B_spatial_response.csv`：事件状态固定时的 P、Q 与 Q−P，槽 9 实际更新方向是 P−Q。
- `B_figures/`：两幅图及配套损失表。英文图中受损以百分数显示，CSV 为比例。图 B1(c) 左右两块分别来自两个独立事件状态，不是拼接的执行结果。
- `B_validation.md`、`B_optimizer_trace.json`、两份运行日志记录审计和复跑；`B_paper_summary.md`、`B_handoff.md` 用于论文对话复核。
