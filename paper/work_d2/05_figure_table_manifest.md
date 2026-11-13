# 图表与源数据清单

绘图脚本analysis/plot_figures.py；统计脚本analysis/build_analysis.py；表格导出analysis/finish_package.py。所有图均为Matplotlib从原始保存数据的D2派生表绘制，无生成图像或手填数值。正式输出为PDF/SVG/PNG；图内英文标签，中文标题及解释在正文。人工科学审阅：待G-D2，未代填。

|显示项|面板/筛选|原始输入|处理与单位|输出|
|---|---|---|---|---|
|Fig.1|equal/unequal两个图，取seed11 B0.6 A/C；价值交换为A/C高2、B/D高3|matched对应model.json|按beta非零项画8边；入口u/v与参数表对应；q取实际模型|figures/fig01_matched_network.{pdf,svg,png}；tables/matched_edges.csv|
|Fig.2|a–c三个B的36原值；d–f全部9组交互|36份fine_evaluation/summary.json:fine_J_D|H48，I=(D−C)−(B−A)，归一化目标单位；零基线|figures/fig02_losses_interactions.*；tables/matched_four_cells.csv|
|Fig.3|a–c隔离、d–f恢复、g–i总容量；seed11三B，C/D|fine/controls.json及各model|s/r原始强度、总用量/B，时间0–10、槽宽5/3；仅例图筛选，其他记录不删|figures/fig03_temporal_allocation.*；matched_controls_all_nodes.csv、matched_budgets.csv|
|Fig.S1|seed33/B1.2 C/D，隔离、恢复、容量、状态|上述控制及fine_evaluation/trajectories.csv|四格中C/D示例；状态H12，x为受损比例|figures/figS01_seed33_state_allocation.*；matched_states_H12.csv|
|Table1|模型和实验参数|冻结base/design及36份model|真实数值、来源、合成标记|第4节；tables/design_table_1.csv|
|Table2|八方法|src/experiments.py、supplement_c2.py及历史源码快照|训练方式、时间/动作自由度、实际容量规则|第4节；tables/design_table_2.csv|
|Fig2原值表|全部9组|同Fig2|原值6位，差值另保留完整精度|第5节；tables/results_table_1.csv|
|Table3|3强基线×2模式，9D格|旧C2逐评价summary.json:fine_J_D|H192，100×(基线−联合)/基线；范围/中位数，零负结果保留|第5节；tables/results_table_2.csv；baseline_pairs.csv、baseline_all_objectives.csv|
|Table4|反例、两组K、跨类、复现|counterexample比较JSON；Work C2 case/baseline/comparison|各证据层独立标注；不合并样本量|第5节；tables/results_table_3.csv；robust_*.csv、environment_*.csv|

## 数据与视觉检查

统计核验见analysis/verification.json。图形每次修改后重跑对齐、PDF字号和遮挡检查；结果见每图alignment.json、collision.json及analysis/figure_qa_log.txt。人工审阅尚未完成，执行者目视检查另记06_D2_review.md。

图形无误差条：这些点是同一合成构造族的确定性配置，不是现实网络抽样。主文以范围和逐配置配对表达变化，不添加置信区间或显著性星号。Fig2保留零轴；相近原值难以目视区分时用原值表和交互面板补足，不裁剪原值轴夸大优势。Fig3隔离与恢复用不同纵轴，图注明示；近零线保留。

统计表中的成本分解遵循自身保存精度，未冒充H192分解；全部六节点控制和容量保留。K控制距离使用逐槽复制和真实时间对齐，另见tables/k_control_distances.csv；paired_objectives中的stable_distance为多初值差，不作K差使用。
