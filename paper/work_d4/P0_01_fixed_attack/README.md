# P0-1 实验包阅读入口

本阶段只检验固定外生攻击下的价值—传播交互，不修改D3稿件。正式协议与设计先于新优化冻结；结果必须由实际运行及质量报告读取，不能把本说明当作通过记录。

建议先看reviews/G_D4_P0_1_submission.md和reports/work_d4/P0_01_m1_response.md，再查本目录four_cell_comparison.csv及交互图。数值与来源问题见P0_01_solver_quality.md、P0_01_independent_validation.json及原始运行目录。

## 字段口径

- 主比较全部使用H=48，H是每槽RK4子步，K始终6。H96/H192复核另表，不拼接不同精度。H12用于粗优化及积分诊断，H48用于细优化。
- four_cell_comparison.csv的GAME_J_A/GAME_J_B/GAME_J_C/GAME_J_D均是A/B/C/D四格的**防御损失J_D**，其中字母是实验格；FIXED/CROSS列同理。objective_components_H48.csv中的J_A则是攻击者净收益，J_D是防御损失。
- I=(J_D格−J_C格)−(J_B格−J_A格)，ΔI=I_game−I_fixed；相对量各自用同组C格损失作分母，列中显式给出分母。fixed_over_game和delta_over_abs_game_percent用交互而非损失作分母，均不是方法损失改善率。
- GAME=(原a、原u)，FIXED=(恒定0.4入口a、新优化u)，CROSS=(恒定0.4入口a、原u)。CROSS只用于附加交叉评价，不与主要I混报。
- controls_costs.csv每行是配置×评价×节点×时窗。成本/双方目标为整段计划的背景字段，会在不同节点/时窗行重复，**不得相加**；terminal_state及state_area_trapezoid_H48也为全时域量。s/r均值和积分才随所列时窗变化。all/first4/last2时窗重叠，不能相加为独立样本。
- control_differences.csv逐槽给出FIXED−GAME；state_differences_H48.csv包含同一时点的三种状态及差。node_state_summary.csv的状态面积是H48网格梯形近似，不能取代RK4增广积分得到的目标分项。
- cost_interactions.csv保留各成本分项的四格交互；防御五项交互之和等于防御目标交互。分项可以同时改变，不据此声称唯一机制归因。
- solver_quality.csv区分PASS、INCONCLUSIVE及NOT_RUN，优化调用失败另见optimizer_attempts.csv。小残差和多起点通过都不是全局最优或Nash证书。

## 原始目录

results/work_d4/p0_1_fixed_attack/run01中，每格使用原case名，模型与原配置逐字节复制。uniform/zero/random_H12和_H48保留新初值、逐轮trace、终点控制及质量；粗12起点、稀疏通道和细3起点审计各有JSON。GAME/FIXED/CROSS内分别保存完整控制、H48状态CSV、H48/H192状态NPZ、每槽容量、各H目标/分项、积分误差以及独立DOP853比较与状态。

NPZ中的times和states分别是时间向量和时点×六节点状态矩阵。元数据、先导关卡、九组状态、协议/源码快照、输入指纹和运行段均在run01中。独立G-D3审稿原文缺失依指令登记，用户提供的启动指令已归档，不伪称已读缺失原文。

## 检查与边界

analysis/analyze_fixed.py只汇总保存数据；analysis/verify_fixed.py从序列化计划重积分主目标、重算残差及九组差分；analysis/run_fixed.py会运行新优化，首次输出目录必须不存在。原稿、源码、模型及历史输入的377个指纹在frozen_inputs.json登记，最终复核不得出现改变。

至少三组时序固定为seed11的低/中/高容量，C/D两格的全部六节点行动及总容量可查。P0-2/P0-3只有PLAN_ONLY.md，没有新增实验。本阶段最终状态必须为WAITING_USER_G_D4_P0_1_REVIEW，不自动变为批准。
