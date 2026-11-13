# D2 主张—证据映射

以下表内源路径均相对项目根目录；D2派生表在tables。状态“允许”表示证据支持限定文字，不是人工批准。

|论文主张/位置|数值及证据|原始来源与派生表|范围|反例/边界|裁决|
|---|---|---|---|---|---|
|4.2匹配上游，保持下游总量|8边、下游总权重0.32，q交换不改变g|matched各model.json；matched_edges.csv|36配置|结构暴露匹配不强制状态匹配|允许|
|5.1价值位置效应受传播条件影响|9组I_J为0.018274—0.029192|fine_evaluation/summary.json:fine_J_D；matched_four_cells.csv|3种子×3容量|含攻击共同响应；无现实因果含义|允许|
|5.1 A/B对称|目标差≤7.32e-12，交换控制差≤7.75e-11|fine控制和目标；symmetry_recomputed.csv|9组|C/D不是镜像|允许|
|5.2低容量核心隔离近零|s2/s3≤7.65e-16|fine/controls.json；matched_controls_all_nodes.csv|B0.6的12格|不能写持续两动作切换|允许|
|5.2低容量前段恢复交互负向|r2为−.007356至−.006017，r3为−.006030至−.004761|控制重算；control_interactions_all_nodes.csv|同物理前四槽，3种子|末段seed22 r2转正|允许|
|5.2中容量异质性|seed11/22全域恢复交互近零正；seed33负|同上，robust_effects历史对照|B1.2|不推普适方向|允许|
|5.2高容量多数松弛|B1.8仅1/72槽绑定|fine控制及budgets；matched_budgets.csv|12格、K6|槽非独立样本，容量上限非消耗|允许|
|5.3强基线改善|响应评价Recovery .887—4.796%，Static .661—2.190%，Fixed .029—.286%|旧C2各summary:fine_J_D；baseline_pairs/statistics.csv|9D格，H192|小收益；不同攻击响应；不可相加|允许|
|5.3固定评价反向|Fixed比较−.094142至−.016590%，0/9正向|同上common_fixed_attack|相同9D格|不能隐藏或外推全36|允许|
|5.4原图反例|12.437518228196426 > 12.436854043461201|counterexample01/comparison.json与cross_evaluation.csv|原图seed33/business_cost/B0.6|同一固定攻击交叉比较中联合较低；不证明动作有害|允许|
|5.5两组K交互保持|.0182736907→.0182733189；.0291919616→.0291096181|K_refinement原始baseline/case，interactions.csv|仅两组8格|末段控制变化、跨类偏离存在|允许|
|5.5跨类偏离|D归一化.1223—.2141%，A .1731—.1767%|case.json:cross；robust_cross_class.csv|复制K6后固定对手，K12搜索|不同于K12重新求解残差；非全局上界|允许|
|5.5同主机隔离依赖复现|目标差≤1.96e-12，控制≤1.13e-11，状态≤4.08e-12|cross_environment/comparison.json及errors表|seed11/B1.2四格|相同Python/算法，非跨平台|允许|
|一般收益来源定理、严格Nash或首创新算法|无此证据|D1贡献裁决；B/C审计|不适用|局部条件不提供全局证书|禁止|

冻结研究主张未扩展；无新增外部文献引用或优先权声明。先例威胁沿用D1/Work C已有审查，本轮不宣称重新查新。完整八方法双方目标、安全/业务/行动成本分解、资源使用及全控制数据均保留，未以弱基线差距替代强基线结果。
