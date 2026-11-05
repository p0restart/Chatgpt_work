# 第5节写作依据与自检

2026-11-03。执行CONFERENCE_WRITING_PLAN.md步骤1；本轮交付一章完整中文准备稿。写作轴：manuscript / research / experiments+discussion / 中文内容稿 / generic（会议未定）。中文稿是项目明确约定，不使用技能的默认英文交付。G2=PENDING；本次“按照规划开始写作论文”不记作G2批准。

## 核心论点与结构

在已计算的合成网络中，价值位置对隔离、恢复配置的影响依赖传播条件与容量状态；九个指定配置中的联合动作、时间安排和攻击考虑具有不同收益幅度，原反例限制了逐例优势主张。

- 5.1说明两组数据、评价对手及改善率分母，先排除比较口径混淆。
- 5.2以四格交互回答配置问题，同时保留低容量恢复效应、中容量异质性和高容量松弛。
- 5.3以强基线分别界定三项增量，将未达到1%的攻击考虑收益写入正文。
- 5.4给出有限菜单和局部诊断的不同认证范围。
- 5.5保留原反例，并把容量、成本、终端和求解限制对应到具体主张。

## 段落—证据映射

下表的P按各小节自然段顺序编号，不计表题、表格与独立公式。全部数值源于项目已保存结果；本轮只重新计算算术与显示表，没有重新优化或新增实验。

| 位置与段落起句 | 依据与定位 | 证据性质及边界 |
|---|---|---|
| 5.1 P1“本节通过两组计算” | matched_mechanism/run01/summary.csv；supplement_c2/run02/comparison/summary.csv；SUPPLEMENT_C2_PROTOCOL.md | 36机制配置、9比较配置及单列反例，不能混算 |
| 表5-1 | matched_mechanism/run01各配置model.json；02_MODEL_SPEC.md；METHODS_AND_EXPERIMENTS_DRAFT_ZH.md | 冻结模型与实际参数；未标定现实单位 |
| 5.1 P2“比较对象包括” | SUPPLEMENT_C2_PROTOCOL.md；src/supplement_c2.py；METHODS_AND_EXPERIMENTS_DRAFT_ZH.md | 八方法的防御限制；相同上限不等于相同投入 |
| 5.1 P3“每套最终防御” | comparison/summary.csv中的evaluation、method、fine_J_D；paired.csv | 每套防御冻结后分别评价；非零和局部攻击响应 |
| 5.1 P4“正值表示” | SUPPLEMENT_C2_PROTOCOL.md；MATCHED_MECHANISM_PROTOCOL.md；src/audit_matched.py | 1%与0.001均为预设工程口径，无总体推断 |
| 5.2 P1“四格设计使” | MATCHED_MECHANISM_PROTOCOL.md；各格model.json；MATCHED_MECHANISM_FINDINGS.md第3—4节 | 总价值、传播权重、入口暴露匹配；双方均重求 |
| 5.2 P2—P3“为度量交互”“该差值检验” | paired_effects.csv字段equal_value_effect、unequal_value_effect、interaction；robust_effects.csv | 参数配置交互，不是损失改善率或时间切换次数 |
| 5.2 P4“低容量” | robust_effects.csv筛B=0.6/window=first4/kind=r；capacity_summary.csv；source_allocations.csv | 六个负恢复交互范围；比较节点隔离零效应不代表全网无隔离 |
| 5.2 P5“中容量” | robust_effects.csv筛B=1.2/seed/window；capacity_summary.csv | 两种子末期隔离交互、另一种子前期恢复交互；无统一方向 |
| 5.2 P6“高容量” | robust_effects.csv筛B=1.8/window=all；capacity_summary.csv | 正交互与多数槽容量松弛同时成立 |
| 5.3 P1及表5-2 | paired.csv筛unequal_high_at_node3/adaptive_attack；comparison_by_budget.csv | 各容量三个种子的范围；7/9、6/9、0/9按原精度计数 |
| 5.3 P2“联合动作的收益” | comparison_statistics.csv；ch05_benefits_by_budget.csv | 仅恢复低容量两例不足1%；仅隔离降幅及启发式边界 |
| 5.3 P3“时间安排的收益” | components_by_budget.csv筛B=1.2/Joint-dynamic或Joint-static；comparison/summary.csv | 三种子均值；安全分项升高而总损失下降，不能宣称分项全面改善 |
| 5.3 P4“考虑攻击调整” | comparison_statistics.csv两evaluation的Fixed-trained行；paired.csv | 响应评价正差与固定评价负差；不同训练方法的排序反转 |
| 5.4 P1及表5-3 | finite/B0.6、B1.2/step0.6、step0.3/audit.json | 四个有限数值游戏、386397策略对；容差1e-8 |
| 5.4 P2“四张表” | finite_selected_costs.csv；各表payoffs_12.npz、payoffs_48.npz的既有审计 | 标记稳定不等于网格成本一致，也不认证连续控制 |
| 5.4 P3“六节点机制实验” | matched_mechanism/run01/audit.json；supplement_c2/run02/independent_audit.json | 两批审计分开；局部观测改善为未知最大改善的下界 |
| 5.5 P1“原模块化网络” | paired.csv筛case=seed33_business_cost_B0.6/evaluation=adaptive_attack/baseline=Recovery-only | 反例成本12.437518228182524对12.436854412938402；不得从匹配样本中删除该边界 |
| 5.5 P2“容量上限” | comparison/summary.csv中九配置Joint-dynamic/adaptive_attack；components_by_budget.csv | 指定三种子算术均值，无总体含义；成本解释来自冻结目标 |
| 5.5 P3“本节的决策含义” | 02_MODEL_SPEC.md；WRITING_DECISION.md；上述两批审计 | 对实际证据的综合解释；K精化、反馈及生产云效果未获验证 |

上表省略的路径前缀：机制CSV均在results/matched_mechanism/run01；C2 CSV、comparison及finite均在results/supplement_c2/run02；协议与说明均在reports。生成的ch05_*.csv位于manuscript/sections/data。

## 图表与数据清单

| 图表 | 当前状态 | 可用数据与后续编排 |
|---|---|---|
| 表5-1 主要实验设置 | 已写入章节 | model.json及冻结模型；最终与模型章参数表去重 |
| 表5-2 三项增量按容量比较 | 已写入章节 | ch05_benefits_by_budget.csv、ch05_benefits_by_case.csv；保留全部种子与两种评价 |
| 表5-3 小规模有限策略核验 | 已写入章节 | ch05_finite_verification.csv；最终可与方法章核验表合并 |
| 规划中的配置交互图 | 本轮仅确定数据，未声称已绘制 | robust_effects.csv、paired_effects.csv、slotwise_effects.csv；容量标识来自capacity_summary.csv或ch05_capacity_binding.csv；不能仅选统一方向通道 |
| 规划中的按容量收益图 | 本轮仅确定数据，未声称已绘制 | ch05_benefits_by_case.csv；区分两评价，三类强基线与原反例分开。若以图替代表5-2，删除重复数值展示 |

章节当前不引用未生成的图。无会议页限时先保证论证可读；上述临时表号、表数不等于最终会议版图表预算。

## 正文取舍与重复检查

| 证据功能           | 放置                                |
| -------------- | --------------------------------- |
| 核心配置交互及容量异质性   | 5.2主文，完整逐槽/逐种子数值保留在原CSV           |
| 三项收益与排序反转      | 5.3主文及表5-2；次要启发式逐配置数值在数据文件        |
| 小规模核验与主要局部诊断   | 5.4短表与一段；完整收益矩阵、退出码、哈希保留在数据目录     |
| 原负结果、松弛、终端与K边界 | 5.2/5.5主文，不移入补充材料隐藏               |
| 原27配置较弱精度比较    | 本章未并入新九配置统计；原文件保留，后续补充材料可按原证据层级引用 |

改写以RESULTS_DRAFT_ZH.md为素材，补入机制段落、比较口径、损失分解和边界，未覆盖原素材。范围数字主要集中在表5-2；正文解释低容量门槛、分项差异与攻击评价反转。局部诊断只在5.4集中陈述；5.5说明这些限制如何影响解释，不重复全部诊断数字。各节字符计数见data/ch05_text_checks.json；这是新章扩写，不把原素材的段落强行对应为一一改写。

## 已完成的核对与未完成项

- 重新从160条评价的fine_J_D核对140行配对改善率，最大算术差见ch05_checks.json；核对全部14组收益统计，差为0。
- 从九配置的126行配对记录重算各容量、各评价和各基线统计，保留所有种子；原反例单列。
- 核对四张有限收益表的策略数乘积与总数、36机制配置通过数、负恢复交互范围及容量绑定范围。
- 对照术语表检查受损比例、瞬时容量、来源隔离、分段开环计划及局部响应表述。本章未新增外部文献引用；相关工作按计划第4步核对既有原文后另写。
- 核对是保存数据的算术及文本检查，不是本轮重新运行原实验、独立重求全批次或人工G2批准。

尚缺的实际决定为G2对具体结果的批准，以及最终格式适配所需的目标会议与页限。它们不阻止本章准备稿及后续已规划的独立章节准备；摘要、结论与最终合稿继续按项目关卡执行。不提出扩大研究范围的任务。

复算本章表格：`python manuscript/preparation/build_ch05_evidence.py`。原实验重现命令仍见reports/SUPPLEMENT_C2_PROTOCOL.md和reports/MATCHED_MECHANISM_RESULTS.md；本轮没有声称执行这些重求命令。

后续修订可按小节或段落起句定位，保留不受影响的内容。下一章按计划步骤2撰写第3节“系统模型与问题定义”。
