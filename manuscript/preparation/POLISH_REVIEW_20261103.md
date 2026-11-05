# 第3节与第5节修订核对记录

日期：2026-11-03（Asia/Shanghai）。依据用户本会话提供的通用学术写作规范、攻防博弈专项约束及“修改润色已完成的两节论文草稿”要求执行。G2批准依据为reviews/APPROVAL_LOG.md的2026-11-03有效条目。本次未变更冻结模型、实验参数或人工审批记录。

## 正文与版本

当前稿为manuscript/03_model_zh.md和manuscript/05_results_zh.md。本次修订前原稿保存在manuscript/history/before_polishing_20261103/。manuscript/sections/05_RESULTS_AND_DISCUSSION_ZH.md是此前独立准备稿，本次不覆盖。

## 修订依据与处理

|位置|处理|核查依据|
|---|---|---|
|3.1—3.2|统一行内LaTeX，解释传播来源索引、聚合比例状态和固定参数假设；补全可测时间与状态局部Lipschitz条件|02_MODEL_SPEC.md第1—2节；reports/mathematical_audit.md；修订前式（2）|
|3.3—3.4|说明瞬时容量、效用量纲及目标函数形式的建模属性；明确攻击者最大化自身收益|02_MODEL_SPEC.md第3节；两方原目标函数，未改公式|
|3.5|统一策略集合符号，明确时间依赖开环控制与状态反馈的区别|02_MODEL_SPEC.md第4节；既有逐章计划|
|5.1|拆开配置设计、方法限制与评价攻击口径，补齐已使用的种子编号|reports/SUPPLEMENT_C2_PROTOCOL.md；manuscript/preparation/METHODS_AND_EXPERIMENTS_DRAFT_ZH.md|
|5.2|用带传播条件和价值位置下标的控制量重述既有四格差值，避免四格标签B与容量B混淆；说明负值含义|results/matched_mechanism/run01/robust_effects.csv、capacity_summary.csv；reports/MATCHED_MECHANISM_FINDINGS.md|
|5.3|保留三类启发式比较，补报原已计算的仅隔离消融；表1报告三项主要比较，正文解释容量差异和超过门槛的计数|results/supplement_c2/run02/paired.csv、comparison_by_budget.csv|
|5.4|保留小幅攻击调整收益、排序反转及原反例；说明固定对手下可行集包含关系与不同响应策略对比较的区别|同批paired.csv；results/equilibrium_audit/counterexample01/cross_evaluation.csv|
|5.5|明确有限表均衡识别、局部连续候选偏离核验、积分精化与控制槽精化的不同对象|results/supplement_c2/run02/finite/*/*/audit.json、independent_audit.json；results/matched_mechanism/run01/audit.json|

反例正文中12.437518与12.436854取自C2保存成本，旧交叉评价另有独立记录。正文用“此前”标明交叉评价的时间来源，不将旧仅恢复成本12.4368540435与C2成本12.4368544129冒充同一次计算。两者均支持保留该负增益案例。

## 术语约定

沿用manuscript/preparation/TERMINOLOGY.md。当前正文统一使用“受损实例比例”“瞬时防御容量”“来源隔离”“主动恢复”“总防御损失”“局部攻击响应评价”“配置交互”。正文“固定攻击优化”对应数据方法Fixed-trained，即针对公共恒定攻击求解防御，与准备材料“固定攻击训练”指同一比较方案；本次没有新增方法。

## 结果放置与重复检查

|内容|功能与位置|取舍|
|---|---|---|
|四格交互及容量、时间窗差异|核心结果，5.2|保留全部三种容量的解释；公式替换原标签式解释|
|联合动作与时间分配收益|核心结果，5.3及表1|表格保留完整分容量范围；正文重点报告方向、计数与比较条件|
|攻击调整小收益、固定评价反转|改变收益解释，5.4|全部保留在正文|
|原模块化网络反例|改变逐例优势主张，5.4|保留在正文，另述旧交叉评价的来源|
|有限表与局部、积分诊断|可信度支撑，5.5|集中陈述；完整矩阵、优化退出码仍保存在原数据目录|
|连续控制、反馈及终端边界|限定结论，3.5及5.5|模型章定义策略，结果章说明证据范围，避免逐段重复|

论证顺序为配置交互→联合动作与时间分配→攻击响应与反例→数值可信度和适用范围。章节结构保持原有五个小节；只在局部重组段落。未新增外部文献、统计检验或未保存结果。正文无审查记录、写作过程说明或额外生成标记。

## 实际核对

本次使用Python标准库读取保存CSV/JSON，核对140行配对降低率，最大算术差为0；重取九配置七基线的范围与超过1%的计数；复核四组主要交互范围及低、高容量前四槽的绑定情况。四张有限表共386397策略对，每表一个纯策略均衡，候选有限菜单偏离改善记录均为0。检查了公式定界符、式（1）—（7）编号及文本编码。结果保存在POLISH_CHECKS_20261103.json，包含正文SHA256。

本次没有重新求解攻防计划，也没有重新运行原积分器或优化器；5.5的积分误差和优化检查是既有审计结果。原实验重现命令见reports/SUPPLEMENT_C2_PROTOCOL.md和reports/MATCHED_MECHANISM_RESULTS.md，C2入口为python -m src.supplement_c2 --output results/supplement_c2/reproduction_new，应选择不存在的新目录。保存数据报告入口为python -m src.report_c2；本次没有执行完整重现命令。

中文篇幅采用含公式与Markdown标记的非空白字符计数，不以英文分词统计代替中文字数。第3节3061→3766，第5节2915→3891。增加内容用于显式定义、比较口径与证据边界，未增加背景铺陈；各小节前后计数见JSON。后续合稿可将5.1与方法章重复的设置集中编排，当前独立章节保留读者理解比较所需的信息。
