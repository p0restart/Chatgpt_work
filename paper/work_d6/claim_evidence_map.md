# D6 主张—证据映射

日期：2026-11-13（Asia/Shanghai）。本文为既有证据整合，没有新增优化或积分。下列原始路径均相对项目根目录；D6图表复制件的来源与SHA-256见[来源清单](figures/source_manifest.json)。数值观察与理论性质分开；“数值通过”不表示人工批准。

## 主要主张

|编号／正文位置|主张与类别|原始证据文件、字段及重算方式|对应显示项／协议|审批与边界|
|---|---|---|---|---|
|C01／§2、§3.1|固定可行控制下连续状态方程解唯一、立方体正不变；理论性质|02_MODEL_SPEC.md；handoffs/B_math_audit.md §2.1；src/core.py:dynamics。有限参数、控制有界可测、局部Lipschitz及边界向内|式(1)—(5)；不是数值实验结论|冻结模型；不推断离散RK4任意步长保域|
|C02／§3.1—3.3|理论Nash、有限槽全局偏离与局部已发现改善不同|handoffs/B_math_audit.md §2.3—2.5；src/game_solver.py:ResponseProblem、observed_gaps；src/matched_mechanism.py:strict_solve|式(6)—(16)、算法1|不增加纯开环Nash存在、唯一或收敛定理；未采用T1未审理论升级|
|C03／§3.4|状态和收益经直接射击生成逐槽隔离与恢复资源|results/matched_mechanism/run01/seed11_B1.2_unequal_high_at_node3/model.json、fine/controls.json（数组依次a/s/r）；容量按式(1)求和|原计划完整36行：figures/data/original_allocation.csv；首槽示例总量0.836845|既有证据；示例不是普遍配置规则，归一化动作无生产接口|
|C04／§4.1、4.4|九组价值位置×传播条件交互为正；A/B对称|results/matched_mechanism/run01/各36格/fine_evaluation/summary.json:fine_J_D；fine/controls.json。每seed/B计算(D−C)−(B−A)|图1、2；matched_four_cells.csv、matched_edges.csv；H48|已获既有范围批准；含双方共同调整，不是现实因果效应|
|C05／§4.4|固定攻击也产生近似量级正交互|results/work_d4/p0_1_fixed_attack/run01/各格/FIXED/objectives.json与GAME/objectives.json:H48；paper/work_d4/P0_01_fixed_attack/four_cell_comparison.csv内source_*指向原控制|图3；九组I_fixed/I_game=97.124%—99.426%；H48，各自训练条件|**D4-P0-1待批准**；比值不是性能改善率；ΔI不是纯战略因果量|
|C06／§4.5|低容量2/3隔离近零、中容量异质、高容量松弛|matched各格fine/controls.json、model.json；paper/work_d2/tables/matched_budgets.csv、control_interactions_all_nodes.csv；全部节点求总量，按1e−6绑定判据|图4、补充图S1；低/中/高B各72槽，绑定60/40/1|既有范围；槽不是独立样本，不推出统一动作切换|
|C07／摘要、§4.6、结论|九D格各自响应下G相对Fixed-trained仅0.029%—0.286%；公共固定全反向|results/supplement_c2/run02/comparison/各九D格/各方法/各评价/summary.json:fine_J_D；paired.csv与comparison_statistics.csv；完整定位见paper/work_d2/tables/result_provenance.csv|表2、3；baseline_all_objectives.csv、baseline_pairs.csv；H192，100×(基线−联合)/基线|既有批准；防御计划在两评价保持相同，各自响应的攻击可不同；三种强基线差值不可相加|
|C08／§4.7|防御与攻击存在有限战略相互依赖|reports/work_d5/p0/run02/defense_by_node_slot.csv、attack_by_node_slot.csv、payoff_matrix.csv、case_summary.csv；源头results/supplement_c2/run02/comparison，原始返回提取见optimizer_returns.json/source_manifest.json|表4、5；同一防御固定，比较aG/aF的J_A；H192|**D5新增审计待批准**；54冻结配对重放而非新增均衡。攻击入口未变，小收益不证明博弈不可替代|
|C09／§3.5、4.8|重新求剩余时域、只执行首槽已真实实现|results/work_d5/replanning/run03/planned_controls.csv、executed_controls.csv、tasks.csv、trajectories.csv及各B/任务初态与trace；independent_checks.csv逐项核对|算法2、图6—8、表7；t=5、20/3、25/3；K'=3/2/1|**D5-run03待批准**；执行历史依赖，不是t=0开环均衡或Markov反馈Nash|
|C10／摘要、§4.8、结论|G较P六组均改善，G较R在E0负、E1正|run03/objectives.csv、comparisons.csv；分别按period=post/full计算P−G、R−G以及相应基线分母；18完整轨迹、不删负值|表6、图5；H48；同B/E下三方法公共实际攻击完全相同|**待批准**；E1仅针对P尾段生成，不能称针对G/R最坏攻击；无无扰动对照|
|C11／§4.8|总损失与加权受损分项可能反向|run03/objectives.csv、loss_component_comparisons.csv；B0.6/E1与B1.8/E0比较security及J_D|表6解释、图8；H48成本，图状态H192，二者精度分别说明|**待批准**；不以总目标排名冒充安全分项排名|
|C12／§4.8|G计算开销高于R，不能证明实时性|run03/timing.csv:type=replanning_total；timing_summary.csv；metadata.json及D5_execution_report.md §7|表8；G/R各18次，实际秒数；B1.2原计时承接run02|**待批准**；额外审计不重复累加；原离线求解耗时缺失、模型时间未标定|
|C13／§4.9|原网络联合相对仅恢复不占优|results/equilibrium_audit/counterexample01/comparison.json、cross_evaluation.csv|正文原值12.437518228196426与12.436854043461201；交叉矩阵CSV保留|已批准边界；原business_cost网络，非第十个D格；不证明增添动作本质有害|
|C14／§4.9|两组K精化方向保持，但K6嵌入K12仍有偏离|results/work_c2_robustness/k_refinement/run01/tables/interactions.csv、cross_class.csv、各case.json；D2 k_control_distances.csv|表9；仅seed11/B0.6和seed33/B1.2；(K,H)=(6,48)/(12,24)|G2-Work-C2已批准；不能推广全部36配置或D5重规划控制类|
|C15／§4.9|同主机隔离环境四格复现与历史53测试|results/work_c2_robustness/cross_environment/comparison.json；tables/cross_environment_errors.csv；handoffs/c1_evidence/tests_final.txt、comparison.json|表9；seed11/B1.2的K6四格|已批准范围；不是跨平台或独立数学实现，D6未重跑测试|
|C16／§4.9|run03登记局部质量及3909项复核通过|run03/quality_summary.csv、solver_audit.csv、optimizer_attempts.csv、independent_validation.json、independent_checks.csv、independent_replay.csv；run01/02 metadata记录失败|局部残差、退出、H精化、DOP853固定动作复核各自报告|**待批准**；作者侧另算法重积分，不是同行评审或全局证书|

## 复核与重现命令

D6本轮实际执行的确定性检查只读取文件、比较公式、核对哈希及保存表算术：

```powershell
python paper/work_d6/analysis/verify_d6.py
```

以下为历史实验的重现入口，本轮**没有执行**。应使用新的空目录并按相应协议准备环境，不覆盖旧结果；本映射不构成新增实验授权。

```powershell
python -m src.matched_mechanism --output results/reproduce_matched_new
python -m src.supplement_c2 --output results/reproduce_c2_new
results/work_c2_robustness/cross_environment/venv/Scripts/python.exe -m handoffs.C2_refine reproduce_new
results/work_c2_robustness/cross_environment/venv/Scripts/python.exe -m handoffs.C2_refine_analysis reproduce_new
python reports/work_d5/analysis/audit_decision_difference.py --output reports/work_d5/p0/reproduction_new
python paper/work_d5/analysis/run_replanning.py --output results/work_d5/replanning/reproduce_new
python paper/work_d5/analysis/verify_results.py results/work_d5/replanning/reproduce_new
```

D4-P0-1重现入口以[原执行记录](../../reports/work_d4/P0_01_execution_notes.md)和[原协议](../work_d4/P0_01_fixed_attack/protocol.md)为准；原图反例入口以其保存metadata和[数学审计](../../handoffs/B_math_audit.md)为准，不猜造命令参数。D5完整参数、版本、种子、控制、初态、原始退出码与时间记录位于run03及source_snapshot；delivery_sources保存后续分析与绘图源码。D6图表数据目录是审阅复制件，不是完整独立重跑环境。

## 解释与推测的界线

“来源受损降低可以减少外传”由方程支持；“C格价值与强出边对齐使恢复兼顾外传”只是与保存结果相容的解释，没有路径因果分解。“E1中G预测较贴近实际攻击”有保存计划支持，但预测误差导致收益优势的因果关系未被单独识别。论文未采用首次、普遍领先、全局均衡、现实云有效或实时部署等主张。
