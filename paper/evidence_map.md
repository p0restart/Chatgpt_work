# 论文论断—证据映射（Work 持续维护）

| 具体断言 | 类型（证明/文献/数值） | 证据位置/DOI | 已核实？ | 可进摘要结论？（G2） |
|---|---|---|---|---|
|在规定非负参数和可行可测控制下，状态保持[0,1]^n|证明|reports/mathematical_audit.md 第2节|同一代理推导/审计，待人工审阅|未获G2批准|
|网络微分博弈及保护恢复权衡已有研究|文献|literature/references_verified.md R1–R5|2026-10-25模型相关正文核查，非全部证明认证|未获G2批准|
|n=4,K=4固定对手局部响应可重复计算|数值|results/p2/run03/；reports/p2_reproduction_final.json|是，仅P2算例|不作为正式效果结论|
|P2防御响应容量不绑定|数值|results/p2/run03/slot_budgets.csv|是|负结果须保留|
|价值传播错位引起可推广的控制切换|候选假说|literature/novelty_decision.md|尚无证据|否|
|联合方法相对强消融的有限成本差，含一项劣于仅恢复的反例|数值|results/p3/fair01/paired_comparisons.csv；reviews/G2_submission.md|27配置已核查，不能宣称始终更优|等待G2|
|已找到Nash或已证明全局最优|无支持|无|否|禁止|


|81个受限优化策略对满足1%相对观测改善工程目标|数值|results/p3/fair01/audit.json|是，局部响应下界，非Nash证书|等待G2|
|全量保存控制重积分、pilot完整复跑|复现|results/p3/fair01/reintegration_audit.csv、pilot_reproduction.json|是，非全批次独立重新优化|等待G2|

## 2026-11-03 第5节准备稿新增映射

章节：manuscript/sections/05_RESULTS_AND_DISCUSSION_ZH.md。段落级定位、数据筛选条件与边界见manuscript/preparation/CH05_WRITING_NOTES.md。以下均未获G2结果批准，本次写作指令不代填批准。

| 具体断言 | 类型 | 证据位置 | 本轮核对 | 可进最终摘要结论？ |
|---|---|---|---|---|
| 36配置中的价值位置配置效应依赖传播条件、容量与时窗 | 数值 | results/matched_mechanism/run01/robust_effects.csv、capacity_summary.csv、audit.json | 核对既有数据及低容量前四槽恢复交互范围；无统一切换证书 | 等待G2 |
| 九个指定匹配配置中联合相对仅恢复降低0.887%–4.796%，7/9达到1% | 数值 | results/supplement_c2/run02/paired.csv、comparison/summary.csv；manuscript/sections/data/ch05_checks.json | 从保存的fine_J_D复算；不代表36配置均有此比较 | 等待G2 |
| 相对静态联合降低0.661%–2.190%，低容量三例均不足1% | 数值 | 同上及comparison_by_budget.csv | 逐容量与种子核对；含不同攻击响应，不能作纯时间效应 | 等待G2 |
| 相对固定攻击训练仅降低0.029%–0.286%，固定评价下九例排序反转 | 数值 | comparison_statistics.csv、paired.csv两评价 | 完整保留0/9达到1%及固定评价负差 | 等待G2 |
| 原模块化网络反例中联合比仅恢复高约0.00534% | 数值 | paired.csv中seed33_business_cost_B0.6/adaptive_attack/Recovery-only | 精确值12.437518228182524对12.436854412938402，单列反例 | 等待G2，必须保留 |
| 四张有限菜单覆盖386397策略对、每表一个容差内纯策略均衡 | 数值 | results/supplement_c2/run02/finite各audit.json、finite_selected_costs.csv | 策略数乘积与总数复算；不认证连续控制域或六节点全局均衡 | 等待G2 |
