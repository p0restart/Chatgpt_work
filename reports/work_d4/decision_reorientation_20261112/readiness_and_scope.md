# Work D4 本轮来源阅读、核对与暂停边界

日期：2026-11-12（Asia/Shanghai）。当前任务负责主体：ChatGPT Work，在本会话可用环境读取和生成本项目文件；无平行代理、无外部执行者代跑。状态：**四材料送审 / WAITING_USER**。

## 阅读对象与用途

|来源|本轮读取/核对范围与用途|
|---|---|
|AGENTS.md、DECISIONS.md、APPROVAL_LOG、模型/实验/关卡规范|核对有效冻结、开环概念、逐时容量、G1/G2与不覆盖规则；未新增批准|
|paper/work_d3/manuscript_zh.md、supplement_zh.md|通读完整合稿和补充；逐节记录模型、方法、设计、结果、结论与原值范围|
|paper/work_d1/06_consistency_and_review.md、D1_R1_changelog.md、D1_R1_reproduction_notes.md、00_evidence_register.md|读取作者侧数学/实现审查、R1收缩贡献与源索引；承接历史缺失外部验收原件的限制|
|paper/work_d2/06_D2_review.md、analysis/independent_review_frozen.md、S1_source_data_index.md|读取作者修订处置、一份冻结独立审阅记录及原始结果定位；G-D2批复由正式文件确认|
|paper/work_d3/D3_review.md、D3_handoff.md、claim_evidence_map.md、citation_audit.md|读取通用合稿状态、主张来源、引用访问限制；不当作G-D3人工批准|
|src/core.py、game_solver.py、matched_mechanism.py|逐项对照动力学、收益分解、策略维数、逐槽容量、RK4离散灵敏度、当前点残差、严格停止与完整/顺序更新|
|src/supplement_c2.py、fair_evaluation.py、diagnose_equilibrium.py相关函数|核对固定训练、固定/响应评价、同防御跨评价、static绑定、原P3/旧C2差异和稀疏审计；识别六槽固定汇总不可直接用于剩余槽|
|results/matched_mechanism/run01|读取36个model、fine控制、fine_audit和fine_evaluation汇总；从原控制核容量和全节点配置；H12分解与H48目标区分|
|results/supplement_c2/run02/comparison、paired.csv|读取九D格144评价原summary和控制、配对原值；核对同防御跨评价一致及小增益/反向；历史run01失败不删除|
|results/equilibrium_audit/counterexample01|直接读取comparison.json和cross_evaluation.csv；核对原图负改善及共同攻击矩阵|
|results/work_c2_robustness/k_refinement/run01|读取metadata与两组交互原表；结合原协议核对K6/K12边界、跨类偏离与同主机环境复现范围；未重新运行|
|paper/work_d4/P0_01_fixed_attack、reports/work_d4/P0_01_*、reviews/G_D4_P0_1_submission.md|读取旧P0指令、正式协议、结果与待审状态；原FIXED objectives.H48与四格表核对；不重复运行，不把待审改为批准|
|handoffs/C_literature_novelty_audit.md及本地R1/R3原文提取相关段|使用已保存查新边界；另在线核对Preciado、Tian、Paarporn、Botteghi直接来源，与材料2访问范围一致|

## 核对的性质

`saved_evidence_audit.json`是本轮确定性文件/算术检查输出，不是新科学实验、研究测试或独立审稿。脚本不导入研究求解模块，不调用优化或积分。

检查包括36保存计划的箱/入口/容量、H48保存目标一致、绑定槽60/40/1、配对改善算术、九D格144目标与原summary、72份防御跨评价不变、P0-1的GAME/FIXED原值与差分、原图反例、两组K精化原表。CSV均提取或重算既有值，没有新拟合或生成新控制。

`protected_before.json`记录本次新材料写作前6014个既有文件指纹；覆盖D1/D2/D3、src/config/tests、冻结规范、审批/状态日志、匹配/补充/精化/P0-1等保存证据。收尾逐项核对。原始路径无输出覆盖；新的审阅单不改APPROVAL_LOG与DECISIONS。实际未找到的目录不声称已纳入保护。

复核本轮保存数据检查的命令（仅文件和算术）：

```powershell
python paper/work_d4/decision_reorientation_20261112/analysis/audit_existing.py
```

文档与包的检查另见delivery_verification.json；它也不是研究实验。轻量包不包含完整6014个文件或原始results，不宣称可脱离项目独立重跑研究。

## 缺失资料与当前可完成范围

项目paper/reviews/reports/handoffs中未找到 `G_D1_独立验收报告.md`、`G_D1_R1_验收报告.md`、`G_D3_independent_peer_review.md`。已读现存审阅文件，不补造外部审稿人意见、原文编号或人工签字。旧P0-1指令中的R3-M1/M2/M3是用户提供的转述来源，不能声称独立报告原件已闭环。

没有目标会议，故本次不声称满足特定EI会议新颖性门槛或投稿格式。四材料属于中文可编辑审阅稿，不是提交PDF。

## WAITING_USER边界

允许：维护当前提案、解释原数据和答复审阅意见、修订不依赖新实验的文字。未执行：入口α情景扩展、重规划数值编排、正式运行、新图绘制、最终全文替换。P0-2/P0-3亦未执行。

新用户指令确定当前四材料交付范围；旧P0-1待审状态保留。本轮人工需决定新方向和材料3实验范围，之后按G1实施、G2验收，再进行最终新版合稿。既有结果的小收益、公共固定反向、原图反例、容量松弛和跨K偏离不随定位改变而删除。
