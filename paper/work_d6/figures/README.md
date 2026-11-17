# D6 图表与数据来源

本目录使用原图的PNG、PDF、SVG逐字节复制件，没有新绘图或重新运行优化。正文8图9表；额外保留补充图S1、E0状态图与总资源使用图。复制指纹及完整路径见[source_manifest.json](source_manifest.json)。下列路径相对项目根目录。

|正文图|文件名|数据及原始来源|显示与状态|
|---|---|---|---|
|图1|fig01_matched_network|data/matched_edges.csv；36匹配model.json；原D2同名图|六节点八边，equal/unequal；已批准证据|
|图2|fig02_losses_interactions|data/matched_four_cells.csv；36格fine_evaluation/summary.json:fine_J_D|全部九组四格，H48，已批准|
|图3|figure_interaction_comparison|data/d4_four_cell_comparison.csv；D4-P0-1各格FIXED/GAME/objectives.json|全部九组H48，**待批准**|
|图4|fig03_temporal_allocation|data/matched_controls_all_nodes.csv、matched_budgets.csv；fine/controls.json|seed11三容量C/D，节点2/3动作及全网容量；已批准|
|图5|paired_comparisons|data/replanning_comparisons.csv；run03/comparisons.csv、objectives.csv|三容量两攻击完整配对，H48，**待批准**|
|图6、7|resources_E0、resources_E1|data/replanning_executed_controls.csv；run03/executed_controls.csv|B1.2全部六节点六槽，实际动作，**待批准**|
|图8|states_E1|data/replanning_trajectories.csv；run03/trajectories.csv|B1.2全部六资产，H192重放，**待批准**|
|补充|figS01_seed33_state_allocation|原D2 matched_states_H12.csv及C/D控制|seed33/B1.2异质性，H12状态，已批准|
|补充|states_E0、resource_use|run03/trajectories.csv、executed_controls.csv，data中复制件|E0全节点状态和两协议全网用量，**待批准**|

|正文表|数据来源与计算|
|---|---|
|表1 参数|冻结02_MODEL_SPEC及36匹配模型；精确边权见matched_edges.csv|
|表2 八方法|既有D3表2；src/experiments.py、supplement_c2.py定义，非新实验|
|表3 六行强基线统计|baseline_all_objectives.csv、baseline_pairs.csv；九D格H192、同协议配对|
|表4 九组战略差异|p0_case_summary.csv，控制、攻击与收益列直接提取；完整分量在p0_defense_by_node_slot/p0_attack_by_node_slot|
|表5 六项收益矩阵|p0_payoff_matrix.csv筛选seed11/B1.2，不优化或挑选效果|
|表6 六组重规划结果|replanning_comparisons.csv，post目标与full百分比分别显示，原精度另存|
|表7 六节点首槽配置|replanning_resource_adjustments.csv，B1.2/E0/G/slot3；E1首次相同|
|表8 时间|replanning_timing_summary.csv；计时定义见原run03报告|
|表9 K精化/复现|robust_interactions、robust_cross_class、k_control_distances、environment_cross_environment_errors复制表及原JSON|

所有主图均采用原有显示范围，不添加置信区间、误差条或显著性星号。原D2和D5已有的源图QA见其正式图表清单与figure_qa_notes；D6另对复用图作目视检查，未重新执行所有PDF碰撞审计。未生成会议套版PDF，不能把原图QA等同最终版面验收。
