# C2补充实验：结果与写作证据



2026-11-02。实验已完成；本报告为G2审阅依据，未预填最终论文审批。全部参数和范围在SUPPLEMENT_C2_PROTOCOL.md中预先登记。



## 1 有限策略核验

|B|step|defense_plans|attack_plans|pairs|pure_equilibria|minimum_max_regret|candidate_gap_D|candidate_gap_A|candidate_J_D|candidate_J_A|max_table_refinement|independent_error|continuous_certificate|
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
|0.6|0.6|49|9|441|1|0|0|0|5.7060765|3.1007596|2.8855258e-06|3.6855239e-09|False|
|0.6|0.3|784|9|7056|1|0|0|0|5.7060765|3.1007596|2.8855258e-06|1.5405783e-09|False|
|1.2|0.6|484|9|4356|1|0|0|0|5.6771429|3.031691|3.3164262e-06|3.6855239e-09|False|
|1.2|0.3|41616|9|374544|1|0|0|0|5.6771429|3.031691|3.9512751e-06|1.6514985e-09|False|



四个表分别覆盖两个容量与两个网格，不是四个现实样本。零遗憾是保存数值收益表及有限菜单内的结果；不认证连续控制域。积分误差来自精化和独立积分器对照，不是严格数学误差界。



### 网格均衡成本与连续候选

|B|grid|selected_J_D|selected_J_A|pure_count|equilibrium_mask_stable|candidate_J_D|cost_difference_grid_minus_candidate|
|---|---|---|---|---|---|---|---|
|0.6|step0.3|6.4112442|2.9994681|1|True|5.7060765|0.70516769|
|0.6|step0.6|6.8581504|3.1706223|1|True|5.7060765|1.1520739|
|1.2|step0.3|6.4112442|2.9994681|1|True|5.6771429|0.73410132|
|1.2|step0.6|6.8581504|3.1706223|1|True|5.6771429|1.1810075|



网格均衡与连续候选的成本不能作为同一游戏内算法优劣的直接排序，因为双方策略空间不同。该表用于揭示离散化改变了允许的选择。



## 2 九个匹配配置的主要比较

下表为各自局部攻击响应后的J_D降低百分比；正数表示动态联合损失较低。1%为预登记工程描述阈值，不是统计显著性。

各方法容量上限相同，实际资源用量不强制相等。启发式按固定份额投入，优化方法可以保留容量。因此，相对启发式优势不能单独归因于博弈考虑。

|baseline|count|min|median|max|positive_count|at_least_1pct|
|---|---|---|---|---|---|---|
|Fixed-trained|9|0.028961563|0.14634256|0.28608115|9|0|
|Isolation-only|9|5.6650095|10.362181|10.999605|9|9|
|Joint-static|9|0.66103486|1.5432419|2.1901327|9|6|
|Recovery-only|9|0.88742389|3.5121419|4.7962219|9|7|
|Spread-only|9|5.5782992|9.3306179|14.053104|9|9|
|Uniform|9|7.6932292|10.117373|11.480109|9|9|
|Value-only|9|8.2227806|12.740923|17.542138|9|9|



### 按容量列出完整范围

|B|baseline|min|median|max|
|---|---|---|---|---|
|0.6|Fixed-trained|0.048295932|0.20398987|0.28608115|
|0.6|Isolation-only|5.6650095|6.4989194|6.7981715|
|0.6|Joint-static|0.66103486|0.70955059|0.75169758|
|0.6|Recovery-only|0.88742389|0.89271785|1.1118522|
|0.6|Spread-only|5.5782992|6.3960516|6.5004494|
|0.6|Uniform|7.6932292|7.794848|8.0165054|
|0.6|Value-only|8.2227806|8.5023247|8.708|
|1.2|Fixed-trained|0.034315072|0.14634256|0.21080736|
|1.2|Isolation-only|10.087082|10.362181|10.519068|
|1.2|Joint-static|1.363188|1.5432419|1.5898944|
|1.2|Recovery-only|3.1988617|3.5121419|3.8343064|
|1.2|Spread-only|8.0561357|9.3306179|9.5692656|
|1.2|Uniform|9.840156|10.117373|10.269714|
|1.2|Value-only|12.74073|12.740923|12.973593|
|1.8|Fixed-trained|0.028961563|0.11831863|0.18375732|
|1.8|Isolation-only|10.733563|10.820543|10.999605|
|1.8|Joint-static|1.8749572|1.9975093|2.1901327|
|1.8|Recovery-only|3.524999|3.9121309|4.7962219|
|1.8|Spread-only|11.001359|13.684529|14.053104|
|1.8|Uniform|11.293924|11.343854|11.480109|
|1.8|Value-only|16.838565|17.422519|17.542138|



### 动态联合配置的容量与成本分解

下表为每个容量下三个指定种子的算术均值，用于描述这三张合成图，不估计现实总体。binding_slots是六槽中的平均绑定槽数。

|B|security|business|isolation|recovery|defense_use_mean|binding_slots|
|---|---|---|---|---|---|---|
|0.6|10.569171|0.064026299|0.068661414|0.3898058|0.57752237|5|
|1.2|9.2946289|0.16261154|0.33021196|0.78742025|1.0135191|3.3333333|
|1.8|8.8459033|0.19495072|0.47993267|0.99042433|1.1905788|0.33333333|



### 公共固定攻击下，同一最终防御的交叉评价

|baseline|count|min|median|max|positive_count|at_least_1pct|
|---|---|---|---|---|---|---|
|Fixed-trained|9|-0.094141684|-0.055678423|-0.016590261|0|0|
|Isolation-only|9|5.7749538|10.417957|11.062296|9|9|
|Joint-static|9|0.7340597|1.695124|2.3899509|9|6|
|Recovery-only|9|0.77017547|3.1246155|4.6331667|9|6|
|Spread-only|9|5.6693582|9.360079|14.079888|9|9|
|Uniform|9|7.4684451|9.9026165|11.384967|9|9|
|Value-only|9|8.1815191|12.700209|17.407914|9|9|



固定训练方法面对固定攻击求防御响应，联合方法的防御来自双方交替响应。公共固定攻击评价冻结两者防御，不重新训练，不把不同防御策略冒充同一策略在不同攻击下的效果。



## 3 原负结果的补充复核

|baseline|joint|baseline_cost|reduction_percent|
|---|---|---|---|
|Uniform|12.437518|13.716608|9.3251199|
|Value-only|12.437518|13.766586|9.654299|
|Spread-only|12.437518|13.498308|7.8586848|
|Recovery-only|12.437518|12.436854|-0.005337485|
|Isolation-only|12.437518|13.914497|10.614673|
|Joint-static|12.437518|12.54478|0.85503009|
|Fixed-trained|12.437518|12.441141|0.029119944|



这是原模块化网络反例，与九个匹配配置分开统计，不把十个配置当成同一抽样总体。



## 4 复用的原27配置结果

|baseline|min|median|max|
|---|---|---|---|
|Isolation-only|3.9472313|10.014075|19.862958|
|Recovery-only|-0.010877661|1.5964379|8.459955|
|Spread-only|5.8944034|9.1199542|17.258714|
|Uniform|6.5622635|11.454824|17.396053|
|Value-only|5.3111725|12.495853|21.930929|



旧324条评价已全部重新积分，误差见existing_audit.json。旧表保留原局部求解精度；不能与本次强化结果混写成同等强度的均衡认证。



## 5 独立检查与失败记录

```json

{
  "finite_tables": 4,
  "finite_random_checks": 20,
  "max_vector_scalar_error": 8.881784197001252e-15,
  "max_independent_integrator_error": 2.2947306277387725e-09,
  "solver_runs": 128,
  "failed_solver_runs": 0,
  "multistart_groups": 32,
  "max_multistart_control_spread": 8.947342323523122e-05,
  "multistart_failed_groups": 0,
  "optimizer_calls": 2404,
  "failed_optimizer_calls": 0,
  "evaluated_local_candidates": 40,
  "failed_final_local_candidates": 0,
  "max_optimizer_violation": 7.049916206369744e-14,
  "new_reintegrated": 160,
  "max_reintegration_error": 7.105427357601002e-15,
  "continuous_global_certificate": false,
  "integration_error_bound": "empirical_only_not_rigorous"
}

```



首次编码/目录错误保留在run01与C2_EXECUTION_LOG.md；未覆盖负实验结果。数值门槛失败如非零，必须在写作包中显式处理，不能只引用完成状态。



## 6 数据与重现

- 主输出：results/supplement_c2/run02；完整收益表在finite；新增逐槽控制、预算、状态及积分精化在comparison。

- 结果统计：paired.csv、comparison_statistics.csv、comparison_by_budget.csv、adaptive_costs.csv。

- 原36配置的机制结果仍见reports/MATCHED_MECHANISM_FINDINGS.md，不由本次九配置比较替代。

```powershell

python -m pytest -q

python -m src.supplement_c2 --output results/supplement_c2/reproduction_new

python -m src.report_c2 --root results/supplement_c2/reproduction_new --report reports/C2_REPRODUCED.md

```

主实验拒绝覆盖已有目录。报告生成器重新计算统计并检查保存策略；重建报告不等于完整重新优化。