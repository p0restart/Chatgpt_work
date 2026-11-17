# D8-2 主张—证据映射

2026-11-15。全部为指定六资产网络、B1.2的确定性仿真观察。不存在自动改稿或结果人工批准。

|主张|直接证据|可复核操作|支持范围/不能推出|
|---|---|---|---|
|平均总资源排序保持|results/K12/asset_rankings.csv；两组G/F原控制|对s+r按等长段取平均、按1e-8容差排序|两种K、指定模型；不是策略逐点稳定或全局收敛|
|K12映射回K6后控制差有限，但子段变化明显|K12_vs_K6_control_comparison.csv；subinterval_changes.csv|相邻两段均值减K6，逐段Linf/RMSE及内部差|必须同时报告平均与子段变化，不能只看目标|
|G/F同攻击列内方向保持|两K交叉矩阵；G_F_same_attack_differences.csv|同一K同一攻击的F−G|跨K的aG/aBR,F是不同数值轨迹，不是共同攻击|
|G自身JD降约0.099655%，F固定攻击JD降约0.152871%|K12_vs_K6_objective_comparison.csv；objective_changes.csv|匹配物理步长、(K12−K6)/abs(K6)|G双方控制均改变；局部策略候选，不证明全局最优|
|当前攻击更新增量在E0/E1方向相反且很小|R_LAG_E0/E1_objectives.csv；D7原objectives.csv；paired_comparisons.csv|H48、post、同一冻结实际攻击下R-LAG−G|包含后续自身状态差，非纯攻击预测因果效果；无普遍优势|
|R-LAG严格使用历史G攻击计划和自身状态|input_provenance.json；provenance_checks.csv；executed_first_interval.json|同分支源计划切片、暖启动与状态完全相等核对|预测机制消融，仍依赖G历史计算，不是独立普通基线|
|预测误差排序与损失方向一致|all_method_prediction_errors.csv；prediction_error_time_means.csv|每更新首段两入口L1/Linf的时间均值|描述性一致；非现实预测准确率或独立因果机制|
|数值诊断通过|K12/R_LAG_numerical_quality.csv；results/verification.json；各原始优化日志|按登记门槛检查、最大值及位置保留|受限策略空间的已发现偏离，不是全局Nash gap上界|
|固定轨迹积分一致|independent_fixed_control_audit.csv；积分精化检查|独立ODE右端+DOP853复算8条新轨迹|同作者数值审计，不是另一机器重优化或外部认证|
|原数据和核心保持|source_immutability_check.csv；source_and_config_manifest.json|182项来源SHA256及授权日志追加前缀|D7/D8-1原件不改；授权日志追加不等于结果批准|

复现命令见README_REPRODUCE.md；所有分析程序位于analysis/，未修改src/。
