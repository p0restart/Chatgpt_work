# D1 前置证据登记

核查日期：2026-11-10（Asia/Shanghai）。本轮只读核对、推导和写作；不运行研究实验、单方响应搜索或历史漏洞探针，不重跑测试。登记中的测试与优化结果属于保存记录。`verification.json` 为本轮读取原始汇总后产生的计数与来源指纹，不是重新求解结果。下列项目路径均相对于项目根目录。

## 1. 有效版本与审批

|事项|当前判定|直接依据|写作边界|
|---|---|---|---|
|冻结数学模型|v2，2026-10-26 G1 已批准|`02_MODEL_SPEC.md`末尾冻结记录；`DECISIONS.md`；`reviews/APPROVAL_LOG.md`|标题中的“候选”是历史残留；不改方程、动作、信息结构|
|匹配四格|2026-10-27 G1-C1 已批准|同上；`configs/proposed_mechanism_identification.yaml`；`reports/MATCHED_MECHANISM_PROTOCOL.md`|n=6、K=6、T=10；36配置|
|原结果写作|2026-11-03 G2 已批准|审批日志G2条目；`reviews/G2_C2_submission.md`|批准已有结果与边界，不是全局均衡认证|
|Work C2 K精化|2026-11-10 G1-Work-C2 APPROVED_SCOPE|审批日志原文“批准 G1-Work-C2，按登记协议执行”|seed11/B0.6、seed33/B1.2，两组八格|
|Work C2 新结果|**2026-11-10 G2-Work-C2 APPROVED**|`reviews/G2_WORK_C2_submission.md`、审批日志原文“批准G2”、`DECISIONS.md`同日条目|指定实例的交互、控制变化、跨类偏离和K=6隔离环境复现可用；非全部36配置精化|
|D1|本次用户授权前三节写作与审查|本次启动指令|交付后等待人工审核；不进入D2、不补填审批|

冲突处理：`handoffs/C2_robustness.md`首段仍写“新增结论待G2”，其11月8日部分还写K=12为0/8。当前审批日志、G2提交文件和实际结果共同更新这两种历史状态；不改原交接。B报告中的B1–B4“待修复”由11月7日C1修复取代；A报告的“未证实新环境复现”和文献报告的“K加密缺口”需结合11月10日新增证据更新，但连续控制收敛缺口仍在。

## 2. 前置材料与核查范围

|工作|读取材料/原始证据|核查结论|仍有边界|
|---|---|---|---|
|A盘点|`handoffs/A_inventory.md`；基础与匹配协议；配置；`results/matched_mechanism/run01/summary.csv`|本轮重新计数匹配36行、36个通过标记。原P3为27配置、324评价；补充C2为匹配D格9配置另加原图反例|P3计数沿用A的文件级盘点，D1未复核其全部324条轨迹；不同实验层不能相加为独立样本|
|B审计|`handoffs/B_math_audit.md`、`B_math_diagnostic.py/json`；`src/core.py`、`src/game_solver.py`|来源隔离、目标正负号、Jacobian与离散灵敏度对应；本轮重新推导PMP/KKT|旧探针包含现已应拒绝的输入，不执行；历史19项测试不等于当前全部测试|
|C1修复|`handoffs/C1_fix_report.md`、`handoffs/c1_evidence/comparison.json`、`tests_final.txt`；`tests/test_b_fixes.py`；修复后源码|53=19既有+34新增参数化用例；B1有限性、B2入口一致性、B3积分失败、B4严格零自环/入口正性均已落实；当前两核心哈希与C1一致|只对一个正常六资产配置、两积分精度、双方各三起点做过修复前后比较；不是36配置全重跑|
|旧C2强基线|`handoffs/C_claim_evidence_map.md`；`results/supplement_c2/run02/comparison_statistics.csv`；`src/supplement_c2.py`|9个D格各自响应评价下Fixed-trained增量0.029%–0.286%；公共固定攻击评价反向；动作与分时收益分别登记|这是旧补充C2，不是Work C2；四张有限收益表只对菜单有效；run01失败保留|
|Work C2精化|`handoffs/C2_robustness.md`；精化协议；`results/work_c2_robustness/k_refinement/run01/metadata.json`、`tables/solver_quality.csv`、`interactions.csv`|本轮解析metadata复核8/8配置、32/32路径；最大已发现相对改善3.3647005e-9、最大残差9.9409716e-5；两组目标交互正向|是保存记录核对，未重求；残差接近1e-4门槛；部分控制效应跨0.001分辨率|
|Work C2跨环境|`results/work_c2_robustness/cross_environment/comparison.json`；交接与协议|seed11/B1.2的K=6四格，comparison_pass及numerical_pass均true；460优化调用零失败；目标差最大1.96110e-12|同主机同基础Python、同版本NumPy/SciPy的新隔离依赖环境；不是跨操作系统或独立模型实现|
|创新性审查|`handoffs/C_literature_novelty_audit.md`、`C_prior_art_matrix.csv`、`C_claim_evidence_map.md`、`C_search_log.md`、`C_related_work_draft.md`、`C_bibliography.bib`|采用保守裁决：具体建模为整合；匹配交互为主要增量；分层收益为支撑；创新性风险中高|21篇/9项全文级是Work C历史审查范围，不冒称D1重新逐篇全文核验|

## 3. 命名与必须保留的后续证据

原P3 A/B/C分别为aligned/separated/business_cost，无D；匹配A/B/C/D分别为equal/high2、equal/high3、unequal/high2、unequal/high3。旧C2比较仅取匹配D格九配置，原图seed33/business_cost/B0.6另列。

匹配网络0、1均向2、3输入成对相同边权，2、3各向4、5连边，共8条边。equal每条出边0.08；unequal节点2每条0.12、节点3每条0.04；交换q=4位置，其余q=1，g=1。边存在关系不变，传播矩阵随equal/unequal改变；A/B镜像不延伸到C/D。初始状态实际为(0.1,0,0,0,0,0)，不能将协议简写“入口受损0.10”误解为两个入口均受损。

|D2必须继承的事实|证据接口|禁止外推|
|---|---|---|
|交互包含攻击共同调整；中预算/时间窗异质；高预算可能容量松弛|匹配run01下`robust_effects.csv`、`slotwise_effects.csv`、`capacity_summary.csv`；Work C映射|不是固定攻击的纯防御因果效应；不是一般切换定理|
|低容量核心节点隔离近零|同根`source_allocations.csv`|不能只凭恢复变化称两节点始终两动作竞争|
|Joint相对Recovery降低0.887%–4.796%，相对Static降低0.661%–2.190%，相对Fixed-trained仅0.029%–0.286%|旧C2 `comparison_statistics.csv`，均为9个D格adaptive_attack|不能推广至36格或外部论文算法|
|共同固定攻击下Joint相对Fixed-trained为−0.094%至−0.017%；原图Joint约12.437518、Recovery约12.436854|旧C2统计、Work C映射指向`results/equilibrium_audit/counterexample01/comparison.json`|反例不得删除；不同攻击下不能套用固定对手可行域包含关系|
|K精化目标交互0.0182736907→0.0182733189、0.0291919616→0.0291096181|精化`tables/interactions.csv`|只限两组；不能称控制轨迹不变|
|复制K=6计划后K=12仍可发现单边改善|精化metadata各case.cross；`tables/cross_class.csv`|不是K=12重新求解后残余偏离，不是全局改善上界|
|同T=10早/末时间窗|匹配协议、精化协议|不是T敏感性|

## 4. 文献实际访问与引用资格

D1正式引言只使用五项关键先例。Tian、Paarporn–Xu、Chen分别读取`literature/fulltext_audit/R1_extracted.txt`、`R3_extracted.txt`、`R4_extracted.txt`的方法相关段；原PDF历史地址和指纹在同目录`source_manifest.json`。本轮检查发现这三个Desktop路径均不存在，仓库搜索未找到对应英文原PDF，仅找到原文提取及Tian中文图片翻译。故采用已有原文提取，不使用中文图片翻译作引文证据，不声称本轮打开了原PDF或完成逐页图像审校。原PDF恢复与公式排版复审作为来源保全待办，不影响本轮只引用已读方法文字的范围。

Preciado读[作者公开全文](https://arxiv.org/html/1309.6270)§II-B/II-C；Botteghi读[v2全文](https://arxiv.org/html/2601.16805v2)§2和§3，并结合Work C的§4核查记录。本轮访问日期均为2026-11-10；Chen DOI入口本轮访问失败，采用本地原文提取。Botteghi正式引用明确选arXiv v2，不虚构期刊上线日期。引用细节及七维对照见`01_research_contributions.md`。

P05 Bai、P19 Ren、P10 Guo、P20 Wu仍为仅摘要/预览，精确动作和容量结构待全文核实；P08已有OA入口但本轮不补全文；P14/P18若改用期刊版仍需核版本。它们不承担任何“已有研究不存在本机制”的判断，也不进入本轮五项正式参考文献。未发现完全相同设计不等于证明首创。

## 5. 复现与来源保护

以下是已有研究的重现入口，仅记录，D1不执行；必须使用新输出目录：

```powershell
python -m src.matched_mechanism --output <新的空目录>
python -m src.matched_mechanism --pilot-only --output <新的空目录>
python -m src.supplement_c2 --output <新的空目录>
results/work_c2_robustness/cross_environment/venv/Scripts/python.exe -m handoffs.C2_refine <新运行名>
results/work_c2_robustness/cross_environment/venv/Scripts/python.exe -m handoffs.C2_refine_analysis <同一运行名>
python -m pytest -q -p no:cacheprovider
```

完整环境、输入、种子和命令以各运行目录metadata/source_snapshot和Work C2 `logs/commands.md`为准。当前core SHA256为`ef2c675252d5fc8e00bc7103dd542a40bbf9c7714412207dd4e0b20966859419`，game_solver为`8a5469467d5028077f6b83f7c9bb2dde5be6e0ff46790c07d252f0d70dbd1d87`。D1起始来源清单保存于`verification.json`，交付时再次比对。前置核对完成，允许进入定位及正文写作；不形成任何新的人工批准。
