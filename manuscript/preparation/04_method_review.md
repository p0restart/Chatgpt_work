# 第4节起草与证据核对记录

日期：2026-11-05。交付：manuscript/04_method_zh.md。依据用户“写第4章内容”及已批准逐章顺序完成中文内容稿；研究型论文、方法章节、中文输入、通用会议格式。沿用TERMINOLOGY.md，不新增模型假设或实验，不产生新的G1/G2审批记录。

## 本章核心论点与结构

在冻结模型下，以分段常值控制和实际SLSQP/RK4实现计算交替局部响应候选；用同一策略对偏离、当前驻定残差、多初值和积分检查支撑局部数值稳定性，再用小规模有限菜单提供可穷举参照。

章节顺序：4.1控制与积分离散；4.2单方受约束优化；4.3同一策略对核验及交替更新；4.4有限表完整枚举；4.5精度与证据范围。算法框对应强化实现，避免把旧阻尼交替程序或未执行的伴随求解写入正文。

## 证据映射

| 正文位置 | 核对依据 | 状态 |
|---|---|---|
| 4.1状态与目标同时积分、终端项、非入口控制 | 02_MODEL_SPEC.md；src/core.py::simulate；src/game_solver.py::ResponseProblem | 已核对 |
| 4.2离散RK4灵敏度、SLSQP、容量线性约束、可行且不劣才接受 | src/game_solver.py::value_gradient、local_best_response | 已核对 |
| 4.2补充ftol=1e-11与匹配ftol=1e-10 | src/supplement_c2.py::best_response；src/game_solver.py::response | 已核对，分别陈述 |
| 4.2静态控制绑定与梯度求和、仅恢复/隔离约束 | src/supplement_c2.py::StaticDefense、problem；src/game_solver.py::ResponseProblem | 已核对 |
| 4.3同一策略对核验，之后D更新、再求A；最多40轮更新 | src/supplement_c2.py::local_solve；src/matched_mechanism.py::strict_solve | 已核对 |
| 4.3残差在当前控制处计算，改善分母为1+绝对目标值 | 同上；src/diagnose_equilibrium.py::residuals；src/game_solver.py::observed_gaps | 已核对 |
| 4.3三条路径与单次调用初值的区别；12→48子步重新优化 | src/supplement_c2.py::starting_controls、optimized_plan；src/matched_mechanism.py::run_case | 已核对 |
| 4.3最终三起点攻击评价，冻结防御；匹配12起点和稀疏起点 | src/supplement_c2.py::comparison_run；src/diagnose_equilibrium.py::strong_audit | 已核对 |
| 4.4网格等级、全部策略对数及遗憾 | src/supplement_c2.py::plans、finite_run；results/supplement_c2/run02/finite/summary.csv | 已核对 |
| 4.4扩充菜单解释 | manuscript/preparation/FINITE_VERIFICATION_NOTE.md；candidate_deviations.npz及代码 | 已核对 |
| 4.5独立积分容差及表内精化差 | src/supplement_c2.py::independent_values；finite/summary.csv；finite_selected_costs.csv | 已核对 |
| 表2优化调用、初值差异、40候选、20抽查及160复算 | results/supplement_c2/run02/independent_audit.json | 已核对 |
| 4.5环境版本 | results/supplement_c2/run02/metadata.json | 已核对 |

## 必须保留的解释

- 观测改善是同一数值目标的连续控制域最大改善的下界，不是上界。极小值不保证未知全局偏离小。
- 投影残差在当前控制处计算；响应优化器自身残差另存，二者不得混用。
- 三初值完整求解不等于每一轮均执行三起点；C2单次更新starts=1，评价starts=3，匹配强化starts=12并加稀疏起点。
- 动态联合九匹配配置复用原fine控制；原反例复用equilibrium_audit/warm控制，C2未重新训练这些防御。来源见source_provenance_audit.json。
- 128次C2求解、32组初值及40最终候选不是原36机制配置计数；表2明确标注补充实验。
- 7.11e-15为相同192子步设置下保存值与复算值的一致性，不是48→192的积分误差，更不是严格误差界。
- 表内1e-8均衡容差与实测积分差属不同层次。四表精化差最大3.951275120428477e-6；20组独立抽查最大2.2947306277387725e-9。
- 积分子步H精化未增加控制时段K，不推出连续控制或反馈策略收敛。

## 重现入口（记录既有命令，本轮未执行）

```powershell
python -m src.supplement_c2 --output results/supplement_c2/reproduction_new
python -m src.report_c2 --root results/supplement_c2/reproduction_new --report reports/C2_REPRODUCED.md
```

完整重算须使用未存在的输出目录；报告重建不等于重新优化。原36匹配配置入口为src.matched_mechanism，设计配置为configs/proposed_mechanism_identification.yaml，各案例另存config.yaml；重现入口为 `python -m src.matched_mechanism --output results/matched_mechanism/reproduction_new`，本轮未执行。

## 本轮自检与待整合事项

已完成静态代码—文字核对、符号衔接和数值记录核对；本轮未运行实验或测试。式号接第3节的(7)，从(8)至(13)；表2沿用写作计划的小规模与局部数值核验表，合稿时统一编号。研究主张及负结果不变，第3、5节未修改。

目标会议及页限未指定，暂不套用具体版式。标准数值方法的引文在相关工作与全文参考文献整合时统一补入经核查条目，本章未虚构参考文献。现有第5.5节也概述核验结果，合稿时可压缩重复计数，保留其解释边界。其余正文无待填结果。
