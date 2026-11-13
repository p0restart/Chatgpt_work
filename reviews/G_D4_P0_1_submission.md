# G-D4-P0-1 审核提交

日期为2026-11-11（Asia/Shanghai）。**状态 WAITING_USER_G_D4_P0_1_REVIEW**。用户尚未批准本阶段结果。本报告的数值通过不自动转为人工批准。

## 结果与建议定位

全部九组的外生固定攻击局部防御候选仍有可分辨的正向价值—传播交互。因此，在本构造族和登记求解流程中，攻击者战略响应并不是出现交互的必要条件；动态传播与防御优化本身已经能够产生该现象。

统一H=48主评价下，I_game为0.018274 至 0.029192，I_fixed为0.018120 至 0.028590，ΔI为+0.00010496 至 +0.00066031。I_fixed/I_game为0.971242 至 0.994256；100ΔI/abs(I_game)为+0.574 至 +2.876%（分母为原GAME交互绝对值，不是损失改善率）。

建议收缩任何“战略攻防独有交互”或“微分博弈不可替代”的解释，将主要贡献定位为该构造族中价值位置效应对传播条件的依赖。微分博弈保留为战略环境对照和适用边界，而非交互存在的必要条件。新增证据增强了现象的对照完整性，同时收紧了其战略归因。

## 证据清单

- [正式协议](../paper/work_d4/P0_01_fixed_attack/protocol.md)、[36格设计表](../paper/work_d4/P0_01_fixed_attack/design_matrix.csv)、[用户启动指令快照](../paper/work_d4/P0_01_fixed_attack/instruction_source.md)。
- [原始运行目录](../results/work_d4/p0_1_fixed_attack/run01)、[元数据](../results/work_d4/p0_1_fixed_attack/run01/metadata.json)、[先导质量关卡](../results/work_d4/p0_1_fixed_attack/run01/pilot_gate.json)。
- [九组四格完整对比](../paper/work_d4/P0_01_fixed_attack/four_cell_comparison.csv)、[全部配置与损失](../paper/work_d4/P0_01_fixed_attack/controls_costs.csv)、[控制差](../paper/work_d4/P0_01_fixed_attack/control_differences.csv)、[完整状态差](../paper/work_d4/P0_01_fixed_attack/state_differences_H48.csv)、[分项交互](../paper/work_d4/P0_01_fixed_attack/cost_interactions.csv)。
- [交互对比图](../paper/work_d4/P0_01_fixed_attack/figure_interaction_comparison.png)、[低容量时序](../paper/work_d4/P0_01_fixed_attack/figure_temporal_seed11_B0.6.png)、[中容量时序](../paper/work_d4/P0_01_fixed_attack/figure_temporal_seed11_B1.2.png)、[高容量时序](../paper/work_d4/P0_01_fixed_attack/figure_temporal_seed11_B1.8.png)。同名PDF/SVG可检查。
- [求解质量](../reports/work_d4/P0_01_solver_quality.md)、[逐格质量](../paper/work_d4/P0_01_fixed_attack/solver_quality.csv)、[全部优化调用](../paper/work_d4/P0_01_fixed_attack/optimizer_attempts.csv)、[复算核验](../reports/work_d4/P0_01_independent_validation.json)、[研究判断及回应草稿](../reports/work_d4/P0_01_m1_response.md)。

## 登记协议符合性

36格完成36，数值通过36，未运行0；SLSQP 1296次，失败0。复算核验PASS，1673项；历史输入保护改变列表[]。全量九组已纳入，不根据符号筛选；GAME未替换、FIXED全部新优化、三组时序可查、交叉评价独立命名。独立审稿报告缺失已按指令登记，不影响按所给R3-M1问题执行。

## 未解决问题及人工决定

请审核是否接受该阶段证据及上述贡献定位。当前只完成P0-1，不证明拓扑/参数范围或全部九组K12稳定；P0-2/P0-3只有方案占位，须分别获得后续启动指示。D3原稿、模型与历史结果保持不变，APPROVAL_LOG既有批准条目未修改；不记录G-D4 APPROVED，不实际投稿。

本阶段提交后停止。
