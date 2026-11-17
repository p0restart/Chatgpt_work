# 数值约束与收敛精度审计

状态：SUCCESS。原始输入目标复算最大差0。全部参数、状态、控制均未裁剪。

五任务×H48/H96×三初值，共30次SLSQP。全部正常退出：True；最大投影残差8.31052878e-06。各次状态码、迭代数、目标、容量违反、投影残差及完整起点/终点分别保存optimizer_attempts.csv与五份*_optimizer_raw.json。convergence.csv保存已发现的进一步改善、多初值目标差与控制差、H96控制差和经验控制误差包络；全数通过原D7门槛：True。

8个固定控制对逐槽约束最大违反3.21964677e-15。三组防御恢复转移保持逐槽用量不变，所有控制上下界合格。48条逐槽约束明细见constraints_by_slot.csv。状态最小0、最大0.340352127；RK4全部保存网格及DOP853内部接受步/共同网格均在允许区间。原模型在x_i=0时向量场非负，在x_i=1时非正（可行非负率和控制），亦支持连续状态域不变性。

8对×H48/96/192及DOP853共32组轨迹和目标。独立DOP853未调用core.dynamics、cost_rates或RK4函数，逐槽重启，比较全部H48共同网格、双方目标和六成本分项。24项比较均合格：True；最大状态/目标/分项绝对差1.36468614e-11。见integration_audit.csv、objectives_all_integrators.csv、state_trajectories.csv。

最大经验控制误差包络5.51432439e-06。各扰动相对基准攻击BR的效果使用对应包络之和判别，见payoff_and_control_summary.csv。正反防御响应距离及对应误差见positive_negative_comparison.json。不将优化ftol直接当控制误差，也不将同初值停止直接当Nash。H96仅复核相同固定对手，没有新增交替博弈。

本次为同一执行环境中的独立方程实现与积分器复算；未声称第二研究者、第二机器或独立全流程优化复现。后续复现命令见README.md。历史不利结果未改写，论文保护核查由finalize.py另行完成。
