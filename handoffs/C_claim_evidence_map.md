# Work C｜结论—证据映射

2026-11-07。允许表述可用于后续写作；本文件不改正式稿。Pxx及BibTeX键见[C_prior_art_matrix.csv](C_prior_art_matrix.csv)。下列重现命令是项目已有入口，**本会话未执行优化复跑**。

|拟写点/结果|具体项目证据|外部近邻|精确允许表述|禁止表述|
|---|---|---|---|---|
|状态和两控制机制|[模型§§1–3](../02_MODEL_SPEC.md)、[现稿§3](../manuscript/03_model_zh.md)|P04 Preciado2014Protection Eq.(3)；P03 Zhang2023Potential Eq.(1)|采用源端出向传播抑制和本地恢复两类动作，描述实例组受损比例|单台服务器受攻击概率；首次连续传播模型|
|非零和开环计划|[规格§4](../02_MODEL_SPEC.md)、[方法§§4.1–4.3](../manuscript/04_method_zh.md)|P01 Tian2025Cloud §4.3；P11 Paarporn2024Tradeoffs §II|在有限时域非零和博弈中求分段常值开环局部响应候选|首个云非零和开环博弈；实时反馈Nash|
|容量定义|[模型§3](../02_MODEL_SPEC.md)、[匹配配置](../configs/proposed_mechanism_identification.yaml)|P04/P11（其总预算不同）|隔离与恢复共享逐槽容量上限，优化允许留有余量|跨期总预算；各方法实际消耗相同|
|匹配四格设计|[协议](../reports/MATCHED_MECHANISM_PROTOCOL.md)、[配置](../configs/proposed_mechanism_identification.yaml)、[对称检查](../results/matched_mechanism/run01/equal_graph_symmetry.csv)|P06 Botteghi2026Contagion §4.1/4.2|在边连接关系和上游暴露匹配条件下，交叉改变出强度条件与高价值位置，检验模型内配置交互|传播矩阵四格完全相同；随机现实因果试验；四格设计首创|
|交互条件性|[全部稳健效应](../results/matched_mechanism/run01/robust_effects.csv)、[逐槽效应](../results/matched_mechanism/run01/slotwise_effects.csv)、[容量](../results/matched_mechanism/run01/capacity_summary.csv)、[机制报告](../reports/MATCHED_MECHANISM_RESULTS.md)|P07 Chen2025ProtectRecover；P19 Ren2020Honeynet|所检交互依赖容量、入口边权和报告时间窗；低容量前四槽恢复交互较一致，中容量不一致、高容量多松弛|任意网络普适规律；一般时间优先级切换；已经验证T变化|
|局部隔离不活跃|[源投入](../results/matched_mechanism/run01/source_allocations.csv)、同根各case/fine_evaluation/controls.csv|P04/P11（动作作用不同）|低容量时节点2/3隔离近零，恢复交互需结合全网控制解释|两比较节点始终出现显著隔离恢复竞争|
|联合相对仅恢复|[C2统计](../results/supplement_c2/run02/comparison_statistics.csv)、[逐项配对](../results/supplement_c2/run02/paired.csv)|P11/P07；非其算法复现|匹配D格九配置、各自局部攻击响应下损失降低0.887%–4.796%|全部36格均胜；对现有文献算法普遍领先|
|分时相对静态|同上，baseline=Joint-static|P01/P10动态策略先例|同九配置降低0.661%–2.190%，仅六项达到1%描述门槛|动态方法显著更优；静态攻击/防御概念混同|
|针对战略攻击训练增量|同上，baseline=Fixed-trained；[预登记](../reports/SUPPLEMENT_C2_PROTOCOL.md)|P01/P06战略模型|各自响应评价下额外降低0.029%–0.286%，九项均低于预设1%描述门槛|博弈较优化具有显著收益；小gap证明方法优势|
|公共固定攻击比较|同表evaluation=common_fixed_attack；[方法和范围](../reports/SUPPLEMENT_C2_PROTOCOL.md)|P01/P06（时序不同）|冻结最终防御后，在公共固定攻击下联合相对Fixed-trained为−0.094%至−0.017%；训练假设与评价攻击必须分开|把重新训练后的比较当作同一防御策略受攻击变化|
|原负反例|[同精度反例](../results/equilibrium_audit/counterexample01/comparison.json)、[C2报告§3](../reports/C2_FINDINGS.md)、C2 comparison中原图case|P13 Zargham2014WorstCase（不同反例命题）|原图seed33/business_cost/B0.6，联合12.437518高于仅恢复12.436854，负值保留且另列|联合控制对任意配置不劣；反例证明联合可行域更大仍固定对手全局更差|
|有限表稳定性|[四表汇总](../results/supplement_c2/run02/finite/summary.csv)、[方法§4.4](../manuscript/04_method_zh.md)、[B审计](B_math_audit.md)|P11理论均衡不可迁移|386397个策略对构成的四个数值表各识别一个容差内纯均衡，仅限明确菜单|连续动作唯一Nash；六节点全局证明；积分容差是严格误差界|
|数值验证与当前修复|[B审计](B_math_audit.md)、[C1修复](C1_fix_report.md)、[修复对比](c1_evidence/comparison.json)|P12也区分启发式和全局认证|有多初值/积分精化/局部偏离证据；C1报告接口修复及单例前后相同|本轮独立跑53测试；53测试证明全局收敛；B缺陷必使历史结果无效|
|适用范围|[实验协议](../04_EXPERIMENT_PROTOCOL.md)、[库存](A_inventory.md)、[现稿讨论](../manuscript/05_results_zh.md)|P06/P12有更广拓扑；不能借为自身验证|合成六资产网络族，三种子重现入口权，T=10、K=6、零终端权重|生产云实测；三独立现实样本；统计显著；一般规模可扩展|

## 复核与复现入口

只读核对：`python handoffs/C_verify_deliverables.py`，检查文献计数、交付文件、引用键、项目路径、文件指纹和相关工作正文长度。它不运行新实验。

原匹配实验的全量重现（须新目录；此处仅记录，不执行）：

```powershell
python -m src.matched_mechanism --output results/matched_mechanism/reproduce_C_review
python -m src.resume_matched --root results/matched_mechanism/reproduce_C_review
python -m src.audit_matched --root results/matched_mechanism/reproduce_C_review
```

`resume_matched`仅在程序按四格边界时间停止且允许续接时使用，不作失败重试。报告重建入口见原reports/MATCHED_MECHANISM_RESULTS.md。

C2既有协议的重现：

```powershell
python -m src.supplement_c2 --output results/supplement_c2/reproduce_C_review
python -m src.report_c2 --root results/supplement_c2/reproduce_C_review --report reports/C2_REPRODUCED_C_REVIEW.md
```

这些命令说明原研究的可重现来源，不是本次执行声明，也不是新实验范围授权。修复后环境及输入来源需重新记录；不能覆盖run01/run02。文献检索则按C_search_log查询表及CSV原文URL/位置重放；网页可得性与排序可能变化。
