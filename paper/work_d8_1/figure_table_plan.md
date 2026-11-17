# D8-1 图表修改与来源

2026-11-14。本阶段已落实为完整Markdown稿：4张沿用图、8张主表及1张附录表。用新表补充原稿缺少的协议、成本和事件后指标，不重复绘制相同曲线。图件位于邻接D7目录，正文采用本版图号；原文件名不改。

|本版图表/位置|修改和阅读目的|实际文件/数据来源|状态|
|---|---|---|---|
|表1，§2.1资产属性|增加六资产角色、入口、q和加权出强度；将资产语义前移至建模|D7 topology_assets.csv、config_new_topology.yaml、B*/model.json|已写入；加权出强度不称作经验传播能力|
|表2，§2.1传播边|逐边列出8条关联的访问/凭证/利用条件，避免业务调用等同安全边|D7 topology_edges.csv的security_assumption、empirically_verified=False|已写入；无虚构漏洞|
|图1，§2.1拓扑|保留网络与源端隔离/本地恢复示意，与表1–2互补|`../work_d7/figures/fig1_topology.png`；原figure_sources.json及固定beta|沿用D7已校验图，不改变拓扑|
|表3，§4.1参数|保持全部模型、成本、初态、容量和量纲，说明时间未标定|D7原表1、config_new_topology.yaml、D7_experiment_protocol.md|逐字保留参数含义，统一控制区间术语|
|图2，§4.1执行流程|保留状态/参数→剩余规划→首区间防御→实际状态的分支|`../work_d7/figures/fig2_execution_flow.png`；run_rolling.py|沿用；预测攻击和公共实际攻击分开|
|图3，§4.2逐资产行动|完整展示6资产×6区间隔离与恢复，不只摘录认证/数据库|`../work_d7/figures/fig3_defense_actions.png`；B1.2/G_controls.json；D8 asset_actions_B1.2.csv|沿用；已目视检查，0–1色标和两位标注保留|
|表4，§4.2预算配置|增加三预算平均资源与实际使用份额，回答相对配置是否改变|D8 asset_mean_all_budgets.csv，由原G_controls和all_asset_decisions核对|已生成；未将份额分母写成预算上限|
|表5，§4.3完整交叉|用每预算2防御×3攻击的完整矩阵替换只列两协议的简表|三个D7 cross_evaluation.csv；D8 cross_matrix.csv|已生成；原18项完整可查；列内同攻击、对角不同攻击|
|表6，§4.3成本分解|新增三预算在a0下的安全、业务中断、隔离、恢复和总损失|同上；D8 fixed_attack_costs.csv|已生成；保留低预算恢复成本下降的反向分项|
|表7，§4.4.1事件后损失|把[5,10]作为主要比较，加入R/P改善，明确各分母及R−G正负|三个事件组objectives.csv H48/post、comparisons.csv；D8 rolling_event_post.csv|已生成；主要指标移至正文|
|表8，§4.4.2预测/实际攻击|首次G、R、E0、E1两入口攻击对照，正文紧随四组偏差和跨更新均值|三个执行CSV，尤其planned_controls的selected首区间；D8 prediction_errors_first_B1.2.csv及all_updates|已核对；生成初值E1与最终冻结E1未混用|
|图4，§4.4.3执行状态/动作|保留数据库状态正负差与认证实际恢复行动，展示非单调变化|`../work_d7/figures/fig5_rolling_execution.png`；event_B1.2 trajectories/executed_controls|原D7图5改为本版图4；已目视检查，保留×1000标注|
|表A1，附录A|全时域作为补充，保留三预算事件及主预算无扰动的8行结果|D8 rolling_all_periods.csv full；原4个rolling目录|已生成；P/G/R及三种相对差齐全|

不再在正文沿用D7图4的两协议差图：完整表5已经覆盖且更能防止混淆攻击条件。原图仍保留在D7，未删除负结果。D7图S1和全1080行决策仍可追溯，但本版不再重复同一主容量行动数值。未新增预测误差曲线，以表8、定量段落和完整CSV支持即可。

## 显示与审阅范围

图1–4已在本阶段逐一重新打开查看，未发现遮挡或图例歧义；四张图均沿用D7原PNG，原PDF/SVG及文字/碰撞检查记录保留在D7。新增表格用原数值自动排入Markdown，不冒称Word/PDF排版已完成。所有表格分项采用独立舍入，极小误差以未舍入源表为准；负数和零值不裁剪。最终会议篇幅、字号及版心需目标会议确定后再处理。
