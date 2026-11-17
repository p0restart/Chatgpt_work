# D8-1 主张—证据审计

2026-11-14，Asia/Shanghai。范围为D7既有输出的读取、算术检查和写作重组。未调用优化器，未重新积分状态，未开展新增实验。全部来源相对项目根目录，D8派生数据位于`paper/work_d8_1/data/`。复核使用未舍入数值，正文一般保留六位小数；独立舍入的分项可能有末位加总差。

## 1. 必读文件与原始数据对应关系

|要求|实际定位|在本阶段的用途|
|---|---|---|
|D7第二版完整论文|`paper/work_d7/paper_v2_zh.md`|五章原稿及15项参考文献；冻结公式(1)–(8)逐式保留|
|实验总报告与预注册|`paper/work_d7/execution_report.md`、`D7_experiment_protocol.md`（与`03_experiment_protocol.md`同版）|确认单网络三预算、事件和无扰动范围、真实数值门槛|
|新网络、资产、参数|`paper/work_d7/config_new_topology.yaml`、`topology_assets.csv`、`topology_edges.csv`、`results/static/B*/model.json`|六资产、八边、q、入口、源/目标方向和瞬时容量|
|算法及主张映射|`paper/work_d7/algorithm_code_map.md`、`claim_evidence_map.md`|先建立来源关系，再对真实源码核对，未只依赖旧叙述|
|静态控制|`paper/work_d7/results/static/planned_controls.csv`、`B*/G_controls.json`、`F_controls.json`|主路径a/s/r和逐区间资源；核对静态主计划与资产导出|
|静态交叉、收益、成本|`paper/work_d7/results/static/B*/cross_evaluation.csv`、`cross_attacks.json`|完整18项评价，包含J_D/J_A与各项成本|
|滚动内部计划|`paper/work_d7/results/rolling_event_B*/planned_controls.csv`|按方法、评价条件、update和selected筛选；只取当次执行首区间|
|实际攻击|同目录`attack_scenarios.csv`、`B*/frozen_attacks.json`|E0/E1实际输入；与执行CSV逐分量核对|
|实际防御与状态|同目录`executed_controls.csv`、`trajectories.csv`及`B*/E*_method_executed.json`|严格区分规划与执行；前段一致性、实际动作与状态|
|滚动损失及事件后口径|同目录`objectives.csv`、`comparisons.csv`、`B*/E*_method_cumulative_costs_H*.csv`|H48为主，pre/post/full分段及分母；没有虚构新事件后指标|
|无扰动对照|`paper/work_d7/results/rolling_control_B1.2/`同名文件|仅主预算；E0实际攻击跨组相同，E1跨组另生成|
|逐资产全量数据|`paper/work_d7/results/derived/all_asset_decisions.csv`|1080行，30条六资产×六区间轨迹；主容量G为其中36行|
|数值检查|`paper/work_d7/results/derived/metrics.json`、`numerical_quality_summary.csv`、`results/verification.json`、`solver_audit.csv`、`quality.csv`|既有局部响应、退出码、积分精度和独立固定控制复算|
|图表与来源|`paper/work_d7/figures/figure_sources.json`、`figures/qa/summary.json`及PNG/PDF/SVG|沿用已生成图件，正文重编图号，未新增同信息图|
|参考文献核验|`paper/work_d7/reference_claim_map.md`、`literature_learning.md`、`references.bib`、`sources/papers/2.txt`|沿用已核实访问层级；定向重读Tian直接先例的本地原文；未声称本轮重查全部在线文献|

`B*`为0.6、1.2、1.8，四个rolling目录中的结果CSV位于目录根，模型与执行JSON位于其下同名`B*/`子目录。程序节点0–5对应论文v1–v6；alpha[0]就是论文alpha_1。源端beta为来源行、接收列，不能交换方向。

## 2. 主张、指标与边界

|编号/正文位置|主张及指标|原始证据与D8导出|判断/边界|
|---|---|---|---|
|C1，§2.1表1–2|认证出强度0.30最高；数据库q=4且无出边；八条安全条件|拓扑CSV、各预算model.json；模型配置原文|固定场景事实；加权出强度不是动态中心性，安全边不是业务调用或已证实漏洞|
|C2，§2–3|状态是受损实例组比例，隔离作用来源，恢复作用本地|冻结式(1)–(3)、core.py、game_solver.py快照|未增删任何控制或收益；聚合动作不等于平台命令|
|C3，§4.2图3|主容量36行a/s/r及容量序列|B1.2/G_controls.json、static/planned_controls.csv、all_asset_decisions.csv；`asset_actions_B1.2.csv`、`resource_by_interval.csv`|读取的实际数值配置；不是多样本平均，也非生产云行动|
|C4，§4.2|网关早期高投入；认证隔离滞后；数据库恢复相对优先级上升|同上，各节点x_start、s、r，式(7)–(8)|配置事实直接支持；边际解释由必要条件与输出共同支撑，未作因素消融归因|
|C5，§4.2表4|网关份额60.09%→44.48%，认证2.16%→9.43%；认证/数据库顺位改变|三个预算离线G控制；`asset_mean_all_budgets.csv`|前三位及末位稳定，低预算数据库高于认证，其他预算相反；份额分母为实际使用资源，非全部份额单调上升|
|C6，§4.3表5|公共a0下F总损失更低，其他两列G略低|三个原始cross_evaluation.csv；`cross_matrix.csv`、`same_attack_differences.csv`|列内同攻击公平比较；不能推广为统一优势|
|C7，§4.3表6|G在a0下安全损失更低但综合损失更高，三预算成立|同一原表security/business/isolation/recovery/J_D；`fixed_attack_costs.csv`|低预算恢复成本下降，不能说各分项全部增加|
|C8，§4.3|各自响应下G损失低0.00577%–0.01579%，攻击响应存在但小|G/aG与F/aBR_F；cross_attacks.json最大分量变化|不同攻击协议；不是纯防御因果效果；攻击最大化J_A而非J_D|
|C9，§4.4表7|六条件G/P事件后改善0.04039%–0.17253%，R/P改善0.04550%–0.16312%|objectives.csv H=48/period=post；comparisons.csv；`rolling_event_post.csv`|主指标[5,10]；两个重规划方法都改善，不能全部归于博弈|
|C10，§4.4表7|E0 G略劣R，E1略优；无稳定优势|同上R−G，范围−0.000548至−0.000381及0.000541至0.000640|只限规定实际攻击，未声称真实攻击下有效|
|C11，§4.4.2表8|首次预测与执行输入及四组误差|选定内部计划、attack_scenarios、executed_controls；`prediction_errors_first_B1.2.csv`|生成过程warm初值的E1攻击约0.5320276，不是最终冻结约0.5320248；本稿使用后者|
|C12，§4.4.2|三更新首区间时间平均偏差匹配方向与G/R损失排序一致|三个事件预算各G/R×E0/E1×3更新；`prediction_errors_all_updates.csv`、`prediction_error_time_mean.csv`|是描述性一致解释；非攻击预测能力验证、非检测准确率、非独立机制因果识别|
|C13，§4.4图4|认证恢复首段略降、后两段升；数据库状态差可短暂为正|B1.2 executed_controls/trajectories，原D7图5|没有断言所有资产所有时刻都改善|
|C14，附录A|全时域损失与事件后绝对差相同；主预算无扰动对照|objectives.csv period=pre/post/full；`rolling_all_periods.csv`、`rolling_control.csv`|百分比分母不同；E1组间攻击不同，不是纯alpha因果对照|
|C15，§4.2/4.4.3|既有1544尝试、345响应诊断、165质量检查、114独立复算；耗时|D7 metrics/verification/quality与timing；`inherited_numerical_quality.csv`|继承诊断，不是D8新实验；非全局Nash认证、外部独立审查或实时性证明|
|C16，§1/4.5|已有云开环微分博弈、数值算法和滚动控制先例|D7文献核验、原文及保留15项引用|无首次建模、原创SLSQP/RK4或通用算法优越性声明；只读摘要的文献访问级别保持原记录|

## 3. 派生指标定义

- 静态列内差：F−G，百分比100(F−G)/F，攻击必须同列；各自响应差另外使用G/aG、F/aBR_F。
- 总防御损失：security+business+isolation+recovery+terminal_defense；攻击净收益：attacker_value−attacker_effort+terminal_attacker。
- 平均资产资源：六个等长控制区间的(s+r)算术平均。份额：该平均除以六资产平均资源之和；不是除以B。
- 事件后损失：H=48、period=post，等于同一方法full−pre。事件前为[0,5]，后段为[5,10]，状态连续，终端只归后段；单点边界无重复积分面积。
- G/P、R/P相对改善分别为100(P−G)/P、100(P−R)/P；G/R相对改善100(R−G)/R。post与full分开计算。
- 预测误差：每次只取selected=True、absolute_slot=3+update的首执行区间，e=a_plan−a_actual；L1=sum(abs(e))，L2=欧氏范数，Linf=max(abs(e))。非入口全部为0，所以六维与两入口范数相同。时间平均偏差为三个等长区间范数的均值，绝非将所有剩余预测区间混合计数。

## 4. 复核和结果状态

在项目根执行`python paper/work_d8_1/analysis/audit_existing_data.py`。首次完成171项既有数据检查，53个来源文件SHA-256写入`data/source_hashes.json`；再次运行额外验证来源数量和哈希未变。检查覆盖18项成本加总、双方交叉响应收益、24条执行轨迹分段加总、同攻击/共同历史、内部首区间筛选及离线G原控制一致性。未重新运行D7优化或积分验证；114项DOP853是D7既有记录。

正文表格由`analysis/build_manuscript.py`读取这些核验后的表生成；式(1)–(8)从第二版保留，式(9)只定义既有事件后指标，不改变目标函数。最终交付检查及结果见`data/delivery_checks.json`。

状态为**第一阶段修订完成，WAITING_USER_D8_1_REVIEW**。本次修订授权不是D7结果验收，也不改变D4/D5历史待审状态，不代填人工批准。
