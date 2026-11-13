# 现有实验全面盘点与完成状态审计

## Material Passport

- 审计日期：2026-11-05（Asia/Shanghai）。
- 类型：本地只读实验盘点；Verification Status: **ANALYZED**。本轮没有重新优化、重新积分、运行实验或测试；只读取文件、核对哈希、重算保存收益表和配置覆盖关系。
- 唯一新增文件：`handoffs/A_inventory.md`。没有修改模型、代码、配置、审批、报告、图表或原始数据。
- 项目根目录：`C:/Users/Jin/Documents/00Graduate_student/ChatGPT_Work__v2`。下文相对路径均从此目录解析；Markdown链接相对本报告目录解析。
- 判断依据：有效审批与冻结决定优先；协议界定分母；实际参数、控制、日志、表格和审计产物界定完成情况。历史报告中的“已完成”不单独构成证据。
- 范围：P0/P2、原G1/P3/P4、四配置强化诊断及反例、G1-C1匹配36配置、C2有限表与强基线、对应图表。论文撰写与文献新颖性不属于本任务。

## 1. 核心结论与完成率口径

**36个匹配六资产配置全部实际完成，并非仍停留在“候选配置”阶段。原三场景27配置和324条公平评价也完整存在。C2正式run02完成；run01失败，不能计入成功实验。**

“完成”指协议要求的运行单元及其可追溯产物存在；“数值通过”只指登记的局部诊断；“复现”须另外区分重新优化与保存策略核验。不能把100%执行完成率写成100%均衡认证率或100%独立复现率。

|统计对象及分母来源|实际完成/应完成|完成率|可支持的准确含义|
|---|---:|---:|---|
|原G1/P3：3场景×3种子×3预算|27/27|100%|原modular图的配置覆盖|
|原P3公平评价：27×6方法×2模式|324/324|100%|保存评价完整；main与fair不是648个独立实验|
|原P3优化方法局部工程检查：27×3优化方法|81/81|100%|通过原1%目标与质量检查，不是严格Nash|
|原图追加严格诊断：预选4配置×3初值|12/12（4/4配置）|100%|此次追加范围完成；对原27配置的严格重算覆盖为4/27=14.81%|
|G1-C1：四格×3种子×3预算|36/36|100%|完整局部数值门槛通过；不同初值不是新增网络样本|
|C2方法比较：预选D格9配置＋原图反例1配置|10/10|100%|9个匹配配置单列，1个原图反例单列|
|C2最终评价：10×8方法×2模式|160/160|100%|与原324条存在复用关系，不能当484个独立样本|
|C2有限表：2预算×2网格|4/4|100%|共386,397个数值策略对，非连续域证书|
|G1-C1同环境独立重求|4/36|11.11%|首组四格；16组初值/精化控制完全相同|
|原P3同环境独立重求pilot覆盖|1/27|3.70%|仅seed11/separated/B1.2的Joint-dynamic及其两模式，不是该配置全部六方法复跑|
|C2完整独立重跑|0/1完整批次|0%已证实|有重积分和独立积分器抽查，未见第二次成功完整重跑|

这些分母属于不同协议、不同统计层级，不给出一个把它们相加的“全项目百分比”。匹配36配置中八方法完整比较覆盖9/36=25%，这是**证据适用范围**，不是C2剩余27配置漏跑：C2只预登记D格9配置。

## 2. 当前有效模型、协议及命名版本

### 2.1 有效冻结与历史状态

1. 模型是[02_MODEL_SPEC.md](../02_MODEL_SPEC.md)的v2.0，2026-10-26 G1批准后冻结；标题保留“候选”是旧文字，不代表当前尚未批准。数学解释见[mathematical_audit.md](../reports/mathematical_audit.md)。有限时域、非零和、K槽分段开环；SLSQP局部响应及交替响应；不是Markov反馈Nash。
2. 基础协议是[04_EXPERIMENT_PROTOCOL.md](../04_EXPERIMENT_PROTOCOL.md)，运行实现由[base.yaml](../configs/base.yaml)、[P3_preregistration.md](../reports/P3_preregistration.md)与P3运行源码快照具体化。正式n=6、K=6、T=10，seed=11/22/33，B=0.6/1.2/1.8，A=0.8；求解RK4每槽12子步，原P3以24/48子步检查。
3. G1-C1于2026-10-27批准；有效补充为[proposed_mechanism_identification.yaml](../configs/proposed_mechanism_identification.yaml)及[MATCHED_MECHANISM_PROTOCOL.md](../reports/MATCHED_MECHANISM_PROTOCOL.md)。文件名proposed是历史命名，内部状态已APPROVED。改变匹配网络设计，不改变冻结方程与目标。
4. 2026-10-27原图严格诊断由[MECHANISM_EQUILIBRIUM_PROTOCOL.md](../reports/MECHANISM_EQUILIBRIUM_PROTOCOL.md)限定四配置，不能把原27个全部升级为同等精度。
5. C2由2026-11-02授权及[SUPPLEMENT_C2_PROTOCOL.md](../reports/SUPPLEMENT_C2_PROTOCOL.md)限定；没有独立语义版本号，以日期、协议快照和哈希识别。n=3/K=2有限表只核验算法；六节点方法比较复用既有模型。
6. 当前G2为2026-11-03 **APPROVED**，依据[APPROVAL_LOG.md](../reviews/APPROVAL_LOG.md)与[DECISIONS.md](../DECISIONS.md)最新有效条目。README_RUN、blocker和若干报告仍含历史PENDING或“尚无强基线”文字，不能据此误判实验未完成，也不能据此伪造新审批。本轮不修改这些文件。

共同参数为合成/归一化；x是实例组受损比例，B/A是逐时容量。c_a=c_s=c_r=1是行动成本系数，不是预算；omega=nu=0。三网络种子改变合成边权，求解随机初值是数值稳健性检查，两者不能合并成更多独立样本。

### 2.2 两版A/B/C/D必须隔离

| 命名空间      | A                   | B                     | C                                    | D                     | 唯一数据根目录                           |
| --------- | ------------------- | --------------------- | ------------------------------------ | --------------------- | --------------------------------- |
| 原G1/P3三场景 | aligned：高价值在最大出强度节点 | separated：高价值在最小出强度节点 | business_cost：沿用separated并提高最大出强度节点h | **未定义，无待补D场景**        | `results/p3/main01`、`fair01`      |
| G1-C1四格   | equal/high_at_node2 | equal/high_at_node3   | unequal/high_at_node2                | unequal/high_at_node3 | `results/matched_mechanism/run01` |

四格A/B中节点2、3向每个下游的边权均0.08；C/D中分别0.12、0.04。高价值q=4，其他q=1，h全为0.05。节点0、1是攻击入口；0和1分别向2、3提供成对相等的入边；**2和3各自都向4和5连边，共8条边**。本轮读取36份model.json与设计逐一核对，边权、q、h和B无不一致。不得用“节点2只连4、节点3只连5”的简图替代实际数据。

原P3的A不等于匹配A，原P3的B不等于匹配B，原P3的C不等于匹配C。C2采用匹配D格；原business_cost反例另列，不是“第十个D格”。C2协议内部的A/B/C小节又分别指有限表/方法比较/旧证据复用，也不是场景名称。

## 3. 现有实验—证据文件—审计状态—待补内容矩阵

|现有实验|证据文件及日志|审计状态|待补内容与复现边界|
|---|---|---|---|
|P0六节点预设控制烟雾仿真与基础测试|`logs/p0_smoke.json`、`p0_pytest.txt`、`p0_input_manifest.csv`、`src/smoke.py`|已执行；5项历史测试通过|不是六资产攻防优化，不计正式配置完成率|
|P2 n4/K4固定对手双方各自响应，seed11/B1.2|`results/p2/run01/02/03`各含config/model/edges、summary、controls、trajectories、slot_budgets、solver_trace、A/D_raw_solver及refined_solver、gradient_check、rk4_refinement；`logs/p2_run02.txt`、`p2_run03.txt`；`reports/verification.md`|完成；最终主审计run03；双方响应均通过登记检查|`reports/p2_reproduction.json`及`p2_reproduction_final.json`记录数值一致。两种固定对手任务不能拼成均衡；预算松弛保留|
|P3 pilot01/pilot02，seed11/separated/B1.2，Joint-dynamic|`results/p3/pilot01`、`pilot02`；`logs/p3_pilot01.txt`、`p3_pilot02.txt`；`fair01/pilot_reproduction.json`|完成；两模式控制/数值汇总差0|同环境重求；不是完整27配置复现|
|P3 main01，原27配置、六方法、两模式|`results/p3/main01/summary.csv`、`metadata.json`、各case/solver_trace.csv与原始响应JSON、`source_snapshot`；`logs/p3_main01.txt`、`p3_main_audit.txt`|完成，324条，81优化任务原1%目标通过|阻尼攻击候选仅作过程诊断；不应作为最终公平比较替代fair01|
|P3 fair01，冻结各方法最终防御后补完整攻击局部响应|`results/p3/fair01/summary.csv`、`audit.json`、`optimizer_audit.csv`、`reintegration_audit.csv`、`ranking_audit.csv`、各case/*_adaptive_response.json与defense_audit_response.json；`logs/p3_fair01.txt`、`p3_fair_audit_fixed.txt`|完成，324条；81/81目标与质量通过|全量保存策略核验，不是全量优化复跑；局部gap非全局上界。C2又复核原324条|
|原图4配置强化诊断|`results/equilibrium_audit/run01`的case_summary、summary、verification及各case/warm、zero、random、强响应/细积分审计；`logs/equilibrium_audit_run01.txt`|完成4/4配置、12/12初值求解，304强搜索起点成功|其余23个原P3配置没有此次严格重算；原四旧候选不通过后来1e-7目标，旧1%通过仍保留|
|seed33/business_cost/B0.6同精度反例与交叉攻击评价|`results/equilibrium_audit/counterexample01/comparison.json`、`cross_evaluation.csv`、`strong_fine_audit.json`、`recovery_start_joint_response.json`；`logs/equilibrium_counterexample01.txt`、`equilibrium_counterexample_cross.txt`|完成；负增益仍存在|Joint约12.437518，Recovery约12.436854；不是实验失败，不可删除。无第二次完整独立重求证据|
|G1-C1首组四格门槛及独立pilot|`results/matched_mechanism/run01/pilot_gate.json`、`pilot_reproduction.json`；`pilot_reproduction01`对应四目录；`logs/STATUS.md`|四格通过，扩展获程序门槛许可；16组控制精确一致|仅seed11/B1.2四格独立复跑|
|G1-C1全36配置|`results/matched_mechanism/run01/summary.csv`、`audit.json`、`optimizer_audit.csv`、`reintegration_audit.csv`、各case模型/日志/四组控制；`logs/g1_c1_delivery_check.json`、`logs/STATUS.md`|完成36/36，局部门槛36/36|28配置后因30分钟边界暂停，后续8完成；不是数值失败或未完成。累计2371.96秒；未全量独立重求|
|G1-C1机制差值/资源转移|同根目录paired_effects、slotwise_effects、robust_effects、source_allocations、capacity_summary、all_source_transfers、equal_graph_symmetry；`reports/MATCHED_MECHANISM_RESULTS.md`|分析产物完成；1098可行转移核验记录|交互非普适时间切换；中预算跨种子/时段不一致，高预算多松弛；无新增强基线在全部四格上的结果|
|C2 run01初次执行|`results/supplement_c2/run01/metadata.json`、`manifest.json`、`source_snapshot`；`reports/C2_EXECUTION_LOG.md`|**FAILED**，22.95秒，FileNotFoundError；无正式新增结果|保留失败。目录扫描误把seed_statistics.csv当案例，修复后另建run02；不计为成功复现|
|C2 run02有限策略核验|`finite/B0.6`、`B1.2`下两个step目录：strategies.npz、payoffs_12/48.npz、audit、candidate_deviations、pure_equilibria、独立积分检查及selected_evaluation；`independent_audit.json`|4/4表完成，386397对；每表1个数值纯均衡|本轮从保存48子步矩阵重新核算，数量与零最小最大遗憾一致；非连续域证书，非第二次完整计算|
|C2 run02八方法比较|`comparison`的9个匹配D格目录＋1个原图反例，模型/config/inputs、multistart、trace、evaluation_audit、各评价目录；paired.csv、adaptive_costs.csv、solver_final_audit.csv、final_local_candidate_audit.csv|10/10配置，160/160评价完成；140条对联合基线配对|八方法为Uniform、Value-only、Spread-only、Isolation-only、Recovery-only、Joint-dynamic、Joint-static、Fixed-trained。匹配A/B/C没有同范围八方法比较|
|C2旧证据复核与数据完整性|`existing_audit.json`、`existing_reintegration.csv`、`source_provenance_audit.json`、`manifest.json`、`analysis_manifest.json`；`reports/C2_EXECUTION_LOG.md`|原324条复核；本轮1431＋1447条哈希全部一致|分析清单与原清单有重叠，不是2878份独立数据。C2完整批次仅run02成功一次|
|测试/环境历史记录|`logs/environment.txt`、`requirements-p2-observed.txt`、p2/p3/g1_c1/c2测试日志；`logs/c2_final_tests.txt`|阶段测试为5→12→15→16→19通过；末次19通过|本轮未重跑测试。原环境Python3.11.7/NumPy1.26.4/SciPy1.11.4；pytest7.4.0与原>=8声明不一致，未证实全新环境复现|
|P3与现稿图表|`figures/p3`四组CSV/PNG/PDF/SVG及QA JSON；`reports/P3_figure_QA.md`；`manuscript/figures/fig01`至`fig05`，绘图源`manuscript/preparation/plot_sections_03_05.py`|图表产物存在、数据来源可追踪；本轮目视抽查网络、全交互、原基线图|绘图不是新实验。P3历史QA为0 FAIL/0 WARN碰撞，源预检另有2 WARN；本轮未重新渲染所有PDF或重绘|

## 4. 逐配置覆盖：原27配置与匹配36配置

### 4.1 原P3三场景，按场景与预算列出种子

所有格子的共同方法为Uniform、Value-only、Spread-only、Isolation-only、Recovery-only、Joint-dynamic，评价为fixed_attack与adaptive_attack；每个场景/预算有3×6×2=36条。case目录格式`seed{seed}_{scenario}_B{B}`。

|场景|B|已完成种子|fair01评价条数|状态|
|---|---:|---|---:|---|
|aligned|0.6|11、22、33|36|完整|
|aligned|1.2|11、22、33|36|完整|
|aligned|1.8|11、22、33|36|完整|
|separated|0.6|11、22、33|36|完整|
|separated|1.2|11、22、33|36|完整|
|separated|1.8|11、22、33|36|完整|
|business_cost|0.6|11、22、33|36|完整|
|business_cost|1.2|11、22、33|36|完整|
|business_cost|1.8|11、22、33|36|完整|

本轮对main01与fair01各324个键逐一核对：预期键缺失0、重复0；每评价的controls、trajectories、budgets、refinement、summary五文件缺失0。配置/模型/边表位于各case根目录；正式全流程日志在main01，公平响应日志在fair01，二者需共同保留。

### 4.2 匹配36配置逐项清单

下表每行的证据目录均为`results/matched_mechanism/run01/{case}`。每行已检查model、config、edges、case_audit、strong_audit、fine_audit、attack_evaluation；uniform/zero/random/fine四组各有controls.json、last.json、trace.jsonl及五项评价文件，未发现缺失。每个case具有四个保存求解/精化组，不计成四个独立实验。

|case（证据目录名）|四格名|局部数值状态|额外同环境独立重求|C2八方法覆盖|
|---|---|---|---|---|
|seed11_B0.6_equal_high_at_node2|A|通过|未见|未做（非C2登记范围）|
|seed11_B0.6_equal_high_at_node3|B|通过|未见|未做（非C2登记范围）|
|seed11_B0.6_unequal_high_at_node2|C|通过|未见|未做（非C2登记范围）|
|seed11_B0.6_unequal_high_at_node3|D|通过|未见|有|
|seed11_B1.2_equal_high_at_node2|A|通过|有：pilot|未做（非C2登记范围）|
|seed11_B1.2_equal_high_at_node3|B|通过|有：pilot|未做（非C2登记范围）|
|seed11_B1.2_unequal_high_at_node2|C|通过|有：pilot|未做（非C2登记范围）|
|seed11_B1.2_unequal_high_at_node3|D|通过|有：pilot|有|
|seed11_B1.8_equal_high_at_node2|A|通过|未见|未做（非C2登记范围）|
|seed11_B1.8_equal_high_at_node3|B|通过|未见|未做（非C2登记范围）|
|seed11_B1.8_unequal_high_at_node2|C|通过|未见|未做（非C2登记范围）|
|seed11_B1.8_unequal_high_at_node3|D|通过|未见|有|
|seed22_B0.6_equal_high_at_node2|A|通过|未见|未做（非C2登记范围）|
|seed22_B0.6_equal_high_at_node3|B|通过|未见|未做（非C2登记范围）|
|seed22_B0.6_unequal_high_at_node2|C|通过|未见|未做（非C2登记范围）|
|seed22_B0.6_unequal_high_at_node3|D|通过|未见|有|
|seed22_B1.2_equal_high_at_node2|A|通过|未见|未做（非C2登记范围）|
|seed22_B1.2_equal_high_at_node3|B|通过|未见|未做（非C2登记范围）|
|seed22_B1.2_unequal_high_at_node2|C|通过|未见|未做（非C2登记范围）|
|seed22_B1.2_unequal_high_at_node3|D|通过|未见|有|
|seed22_B1.8_equal_high_at_node2|A|通过|未见|未做（非C2登记范围）|
|seed22_B1.8_equal_high_at_node3|B|通过|未见|未做（非C2登记范围）|
|seed22_B1.8_unequal_high_at_node2|C|通过|未见|未做（非C2登记范围）|
|seed22_B1.8_unequal_high_at_node3|D|通过|未见|有|
|seed33_B0.6_equal_high_at_node2|A|通过|未见|未做（非C2登记范围）|
|seed33_B0.6_equal_high_at_node3|B|通过|未见|未做（非C2登记范围）|
|seed33_B0.6_unequal_high_at_node2|C|通过|未见|未做（非C2登记范围）|
|seed33_B0.6_unequal_high_at_node3|D|通过|未见|有|
|seed33_B1.2_equal_high_at_node2|A|通过|未见|未做（非C2登记范围）|
|seed33_B1.2_equal_high_at_node3|B|通过|未见|未做（非C2登记范围）|
|seed33_B1.2_unequal_high_at_node2|C|通过|未见|未做（非C2登记范围）|
|seed33_B1.2_unequal_high_at_node3|D|通过|未见|有|
|seed33_B1.8_equal_high_at_node2|A|通过|未见|未做（非C2登记范围）|
|seed33_B1.8_equal_high_at_node3|B|通过|未见|未做（非C2登记范围）|
|seed33_B1.8_unequal_high_at_node2|C|通过|未见|未做（非C2登记范围）|
|seed33_B1.8_unequal_high_at_node3|D|通过|未见|有|

### 4.3 C2有限表明细

|B|网格步长|防御计划|攻击计划|策略对|保存表纯均衡数|本轮保存矩阵复核|
|---:|---:|---:|---:|---:|---:|---|
|0.6|0.6|49|9|441|1|通过|
|0.6|0.3|784|9|7056|1|通过|
|1.2|0.6|484|9|4356|1|通过|
|1.2|0.3|41616|9|374544|1|通过|

四张48子步收益表维度与上表一致，J_D和J_A均有限；本轮按防御列最小值、攻击行最大值，以1e-8容差重算，每表均1个纯策略均衡，最小最大遗憾均0。该核验没有重新计算ODE收益。小图固定链0→1→2、q=(1,1,4)、n=3/K=2；不能把它加到六节点场景样本量中。

## 5. 数值检查、可复现性与来源完整性

### 5.1 已有检查的实际强度

|实验层|保存审计中的关键量|判定|
|---|---|---|
|原P3 fair01|最大相对观测改善0.00222001724；预算违规1.454e-14；12对48子步目标差2.43e-8；重积分差9.77e-15；排序变化0|达到原1%工程目标，但不能升级为1e-7严格结果|
|原图4配置严格诊断|12次求解通过；最大新相对观测改善2.24e-10；三初值控制差≤6.23e-5|仅这4配置的强化局部证据|
|匹配36配置|最大相对观测改善1.54022e-9；当前策略残差最大9.970996e-5；三初值最大差8.87604e-5；预算违规8.105e-15|36/36通过登记门槛；残差接近1e-4阈值，不能隐去|
|匹配全量核验|4209次记录优化成功；144组保存策略重积分差0；积分精化差9.4533e-9；可行转移导数误差≤1.87519e-5|已有全量保存策略验证，不是144个独立实验|
|C2|128次求解、32多初值组、40最终候选全部通过；2404优化调用成功；160重积分差≤7.11e-15；20随机独立积分抽查误差≤2.30e-9|run02数值质量证据完整；无连续控制全局证书|

这些数字来源于保存的audit/verification/independent_audit及对应CSV。本轮重新核对文件覆盖、清单哈希、模型设计和有限收益矩阵；**没有重新执行这些审计程序的积分或优化部分**。

### 5.2 可以怎样复现，哪些尚未验证

- **P2**：三次同环境运行；两份复现JSON显示控制、目标、轨迹、预算、梯度、步长表一致。具备最明确的小规模重求证据。
- **P3**：pilot两次重新优化一致；324条策略均已重积分，C2再次检查。完整主批次没有第二套独立重求数据。
- **原图强化诊断与反例**：有参数源、求解轨迹、多起点、细积分与交叉评价；未见第二个完整诊断批次。不同初值不能直接称独立环境复现。
- **G1-C1**：保存主批次与独立四格pilot；36模型全部可重建；本轮核对metadata所列当前源文件哈希全部一致。其余32配置没有独立重求证据。
- **C2**：两份清单均当前一致；历史输入由source_provenance_audit追踪；160评价产物完整。独立积分器是算法实现的交叉检查，不是C2整批复跑。有限枚举本轮重算的是已存收益矩阵上的最佳响应关系。
- **跨环境**：尚未证实。依赖实测文件存在，但没有全新隔离环境成功复现日志。不能将“命令可用/文件齐全”写成“本轮已在新环境复现”。

原P3当前P3_preregistration.md与main01启动哈希不同。已检查冻结快照：`results/p3/main01/source_snapshot/P3_preregistration.md`与metadata登记哈希匹配；当前文档仅追加公平评价补充段。是可解释的协议追加，不是原数值结果失效。复现main应明确使用冻结快照，fair按补充登记解释，不能无说明地宣称所有当前协议文件与最早启动版本完全相同。

### 5.3 重现命令索引（仅记录，本轮未执行）

运行须选择不存在的新目录，保留失败；建议先使用原实测依赖版本。C2需要保留matched/run01、p3/fair01和equilibrium_audit/run01历史输入。数值源快照位置：P2各run/source_snapshot；P3 main01/source_snapshot；匹配run01/source_snapshot及analysis_source_snapshot；C2 run02/source_snapshot及analysis_source_snapshot。

```powershell
python -m src.p2_validate --config configs/p2.yaml --output results/p2/reproduction_new
python -m src.experiments --config configs/base.yaml --output results/p3/reproduction_pilot --pilot
python -m src.experiments --config configs/base.yaml --output results/p3/reproduction_main
python -m src.fair_evaluation --source results/p3/reproduction_main --output results/p3/reproduction_fair
python -m src.diagnose_equilibrium --output results/equilibrium_audit/reproduction_new
python -m src.diagnose_counterexample --equilibrium-root results/equilibrium_audit/reproduction_new --output results/equilibrium_audit/reproduction_counterexample
python -m src.matched_mechanism --output results/matched_mechanism/reproduction_pilot --pilot-only
python -m src.matched_mechanism --output results/matched_mechanism/reproduction_full
python -m src.supplement_c2 --output results/supplement_c2/reproduction_new
```

这是原项目入口索引；完整复现应锁定对应源码快照。`audit_p3`、`audit_matched`、`report_c2`会生成/更新审计文件，故本轮没有调用；重建图表也会写文件，本轮没有调用。

## 6. 未完成、失败、无法验证与负结果分列

### 6.1 确认失败或中断的记录

|记录|实际原因|最终处置及影响|
|---|---|---|
|C2 run01 FAILED|目录扫描错误；metadata记录FileNotFoundError，执行日志说明将seed_statistics.csv当目录|保留失败；修复实现后run02成功，不覆盖run01；不是两次成功复现|
|C2新增测试最初3失败|Windows默认GBK读取UTF-8配置|修复显式UTF-8后19通过，见C2_EXECUTION_LOG；不表示科学假设不成立|
|C2首次报告生成失败|对Python列表误用abs|报告程序修复后审计完成，未覆盖实验数据|
|P3早期汇总/审计异常|将seed_statistics.csv匹配为配置目录，曾误计28|`logs/p3_findings.txt`、`p3_fair_audit.txt`保留；带fixed日志纠正为27，本轮独立键核对也为27|
|P3早期pytest收集错误|历史source_snapshot重复导入造成import mismatch|pytest.ini限制tests后15通过；历史执行说明保留|
|匹配批次28后时间暂停|30分钟按四格组边界停止|metadata.segments记录核验输入哈希后续8完成，当前COMPLETED；不是数值门槛失败|

现有完整批次未发现未解决的数值失败配置或缺失配置；这个判断不等于“项目从未出错”。图表依赖下载/环境问题见P3_execution_notes，属于辅助工程记录，不应计入科学实验成功率。

### 6.2 真正尚缺的验证

1. **K槽精化尚未完成**：12/24/48/192等RK4子步改变的是积分步长，不是K。未见K=6与更细控制槽的配对重求证据。
2. **连续策略域全局gap/Nash、反馈Nash、全局唯一性尚未验证**：所有六节点优化为局部搜索；小规模有限表穷尽不补齐这个缺口。这些不是当前受限机制论文必须承诺完成的任务。
3. **完整跨环境复现未验证**，P3与匹配全批次独立重求也未验证；C2只一次成功完整运行。
4. **匹配A/B/C的八方法强基线对照未开展**，原C2只登记D格。原P3三场景的旧基线不能填充这些空格。
5. **普适隔离/恢复动态优先级切换条件没有直接验证**。四格差值是跨配置干预的交互，控制曲线交叉不是通用切换定理；不能标记“已经检验并全面否定”。
6. **扩展拓扑、参数标定、真实云测试未完成**。基础协议提及链/星作为后续敏感性，没有找到相应正式结果；固定匹配DAG不是链/星敏感性系列。n≥20、非零终端权重等也无已完成证据，不计入当前批准分母。
7. **更广泛参数/随机网络总体推广未验证**。3种子是3组合成边权，未估计现实总体分布或统计功效。

### 6.3 已完成但不支持强结论的结果

- 原P3 81个任务中79仅一轮更新、2个两轮；原1%门槛过宽。已完成的成本表不能转述为81个高精度均衡。
- 四个原图旧候选在后来1e-7门槛下均存在更大观测改善，强化后通过；阈值版本不同，不构成伪造旧1%通过，也不能混用两版精度。
- 原反例联合相对仅恢复的负收益从约-0.010878%缩小到约-0.00534%，没有消失；C2约-0.005337%。精度和评价层不同，必须与具体文件绑定。
- C2匹配D格联合对Fixed-trained仅0.028962%–0.286081%，9/9低于预登记1%门槛；这是方法价值的已完成负证据，不是“等补更多实验才能宣布正优势”。
- 对Recovery-only改善0.887424%–4.796222%，7/9达到1%；对Joint-static改善0.661035%–2.190133%，6/9达到1%。不能说全部配置都有≥1%优势。
- 公共固定攻击下对Fixed-trained的9个改善均为负（约-0.094142%至-0.016590%），应与各自攻击响应后的结果分开。
- 匹配低预算源节点隔离近零；中预算交互方向/时段不一致；高预算多数容量松弛。因此可报告条件性交互，不能统一解释为持续的容量争夺。

## 7. 图表审计与实验事实的对应

原P3四图与CSV成套存在：paired_ablation（27配对配置）、capacity（各场景/预算三种子）、business（9个C-B配对）、gaps（81优化任务）。历史字体/碰撞检查见P3_figure_QA，不能把制图检查当数值复现。

现稿五图由plot_sections_03_05.py读取保存数据：fig01取匹配边表；fig02取seed11/B0.6四格fine_evaluation节点2恢复；fig03取paired_effects的fine记录；fig04/05取C2 paired.csv的九匹配配置。本轮已目视检查fig01的八边拓扑、fig03全种子交互热图和P3 paired_ablation；其余图检查生成源和文件存在，未逐页重新渲染。现稿图不能扩大样本、增加完成率或替代日志。`manuscript/preparation/POLISH_CHECKS_20261103.json`记录140条配对算术误差0，是既有分析检查记录，不是新实验。

## 8. 面向EI会议小论文的证据缺口与最小补充建议

未给出具体会议，本节按“小规模合成机制研究”的可审核性判断，不宣称EI存在统一实验数量或接收标准。现有执行量已足以形成受限的机制与收益边界证据；主要缺口不是把36个配置再全部跑一遍。

|拟支持的结论|已有证据|缺口级别|最小补充或处理|
|---|---|---|---|
|K=6下价值位置×出传播强度的条件性交互|36配置、匹配设计、三种子三预算、初值/积分检查|可用；尚缺控制槽稳健性|优先补少量配对K精化；不扩大为普适切换|
|结果可由他人在另一环境重建|快照、版本、哈希、pilot|直接复现缺口|新环境完整重求一个既有四格pilot；记录实测版本与误差|
|D格中动态/联合/博弈考虑的收益范围|9匹配配置八方法两评价＋反例|当前有限范围可用|不必补全部36基线；若主张所有A/B/C/D收益则必须另做匹配对照|
|博弈考虑具有≥1%实用优势|9/9低于门槛|已有反面证据|保留小收益与边界，不追加择优配置寻正结果|
|联合总优于仅恢复|原图反例仍负|被现有反例限制|必须保留反例及交叉攻击解释；无需重复证明预设优势|
|连续控制全局均衡或反馈解|仅有限表/局部响应|不具备|从适用主张中排除；不作为本小论文最小补实验|
|真实云有效性/跨拓扑普适性|合成网络|不具备|明确合成范围；真实标定属独立扩展，不列最小包|

建议的最小新增计算包（**仅建议，未执行**）：

1. **控制槽配对精化：8个新配置**。固定既有四格设计，选seed11/B0.6及seed33/B1.2两组，各四格；只将K由6细化至12，T、图、经济参数和容量不变，保持原局部质量标准。先将原六槽控制复制到十二槽作为可行热启动，再用原多初值方案检查。比较同组四格交互的符号/工程阈值、成本与预算绑定，并将细槽控制按原时间窗比较。该选择覆盖低预算主效应与中预算种子33异质性，不按期待收益挑配置；只支持这两组稳健性，不能冒称全36收敛。
2. **跨环境独立复现：4个既有配置重求**。在干净数值环境重现seed11/B1.2完整四格pilot，用冻结源码/配置快照；先记录实际依赖，再比较模型哈希、目标、逐槽控制和四格差值。浮点环境改变时预先给出容差，不能事后只挑目标一致而忽略控制差。可附一个既有有限收益表的只读重算作为轻量检查，不需要重做最大枚举表。
3. **现范围无需默认新增全36基线**。若确实要把D格收益推广为四格共同结论，才另提最小配对方案，例如seed11/B1.2全四格的Recovery-only、Joint-static、Fixed-trained，使用与C2同精度同评价；D格已有，新增A/B/C共9个方法训练单元。单种子单预算仍不能覆盖全部36，不建议为当前受限结论启动此扩展。

最小优先包为8个K精化新配置＋4个既有pilot跨环境复现，共12个配置级任务，而非12个独立统计样本；每配置实际仍含规定的多初值、双方响应及积分检查。本建议未估算或承诺运行时间。K精化改变批准的n/K/T实验设置，新增范围应先登记协议并由用户决定是否重开受影响关卡；本报告不替代批准，也未修改任何冻结设置。

不需要计算即可补齐的材料：明确两套A/B/C/D字典；将旧PENDING、候选标题、run01路径等历史状态做索引说明；按快照版本提供依赖和命令；把失败/负结果与有效分母同时交付。本报告已提供这些索引，但没有改写原文件。

## 9. 审计覆盖与解释风险检查

本轮覆盖协议、审批、3个P2运行、4个P3运行、原图严格诊断/反例、匹配主批次及pilot、C2失败与成功批次、结果矩阵/控制/轨迹/预算/日志、源快照/哈希、图表及历史QA。对数值矩阵只做读取和最佳响应关系重算，没有产生新实验结果。

解释风险11项检查：小样本功效（不作总体显著性判断）；p值滥用（无此推断）；多重比较/择优（全36列出、保留负值）；因果外推（原图混杂与匹配范围分离）；相关与机制混同（交互不等于切换）；伪重复（种子、初值、模式、有限策略对分开）；均值掩盖异质性（逐种子/预算与反例保留）；效应量与工程意义混淆（1%与0.001非统计显著性）；不确定性表述（无总体CI依据）；对照不公平（fixed/adaptive及main/fair分层）；幸存者/失败遗漏（run01与中断、历史错误保留）。这些是本地证据风险检查，不是额外统计检验或投稿验收。

**最终审计判断：批准范围内的主要计算批次已经完成，没有发现36候选配置中的漏跑；研究证据仍有控制槽稳健性、跨环境复现及强主张适用范围的缺口。下一步应优先补可复现性与K精化，而非把不同协议的既有结果混合成更大的完成率。**
