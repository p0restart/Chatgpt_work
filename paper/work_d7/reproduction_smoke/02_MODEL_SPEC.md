# 02 · 数学模型与理论验证规范（v2.0 候选）

## 1. 资产、网络、状态和控制

研究 n 个云工作负载的**实例组**；状态 `x_i(t)∈[0,1]` 是实例组 `i` 的受损实例比例。有效攻击传播网络为非负有向权重 `β_{ji}`，表示由 j 向 i 的传播率，`β_{ii}=0`；业务调用边**不必然是攻击传播边**。

攻击入口集合 `E`；`α_i>0` 仅对 `i∈E`，其余 `α_i=0` 且 `a_i(t)=0`。攻击强度 `a_i∈[0,1]`；传播抑制 `s_j∈[0,1]` 作用于**来源 j 的出边**；恢复投入 `r_i∈[0,1]`。隔离有效性 `ε_j∈(0,1]`（基准可设 1），基础恢复率 `δ_i≥0`，投入恢复效率 `γ_i≥0`。

## 2. 动力学

$$
\dot x_i=(1-x_i)\left[\alpha_i a_i+\sum_{j\ne i}\beta_{ji}(1-\varepsilon_j s_j)x_j\right]-(\delta_i+\gamma_i r_i)x_i,\quad x(0)=x_0\in[0,1]^n.
$$

令 `z_i = α_i a_i + Σ_{j≠i} β_{ji}(1−ε_j s_j)x_j`，可得 `f_i=(1−x_i)z_i−(δ_i+γ_i r_i)x_i`。当 `x_i=0` 时 `f_i=z_i≥0`；当 `x_i=1` 时 `f_i=−(δ_i+γ_i r_i)≤0`，在有界可测控制和固定非负参数下正不变。Work 须补充局部 Lipschitz、解存在唯一性条件，不得只写一句显然。

## 3. 两方目标、可行控制集合

防御者**最小化**：

$$
J_D=\int_0^T\left[\sum_i(q_i x_i+h_i s_i)+\tfrac12\sum_i(c_i^s s_i^2+c_i^r r_i^2)\right]dt+\sum_i\omega_i x_i(T).
$$

攻击者**最大化**：

$$
J_A=\int_0^T\left[\sum_i g_i x_i-\tfrac12\sum_i c_i^a a_i^2\right]dt+\sum_i\nu_i x_i(T).
$$

`q_i,g_i,h_i,ω_i,ν_i ≥0` 且 `c_i^s,c_i^r,c_i^a>0`。其中 `q_i x_i` 为被攻击损失，`h_i s_i` 是**因隔离产生的业务中断损失**；经济成本与资源容量系数不是相同概念。

每一时刻（几乎处处）满足：

$$
\sum_i(b_i^s s_i+b_i^r r_i)\le B,\quad\sum_i d_i^a a_i\le A,
$$

并且 `0≤s_i,r_i,a_i≤1`、非入口 `a_i=0`。`B,A` 是每时刻容量，非累计预算。`b_i^s,b_i^r,d_i^a>0`。

## 4. 严格区分均衡概念

两位玩家在 `t=0` 确定随时间变化的开环控制 `u=(s,r)`、`a`，其策略不以实测状态的实时变化为输入。

开环 Nash 满足，对允许的开环控制 `u,a`：

$$J_D(u^*,a^*)\le J_D(u,a^*),\qquad J_A(u^*,a^*)\ge J_A(u^*,a).$$

数值采用 K 个控制槽，策略是受限分段常值开环策略。其 gap 为在**相同离散策略类内**重新优化单方所得的可改善量，不能视为连续函数空间中 Nash 的严格证明。即使 gap 很小，也可能是局部优化器的假象；必须进行优化器多起点与数值误差核查。

## 5. Hamiltonian 与 Pontryagin 必要条件

令 `L_D,L_A` 为相应瞬时目标，被控向量场记为 `f`；`H_D=L_D+(p^D)^⊤f`（防御者最小化），`H_A=L_A+(p^A)^⊤f`（攻击者最大化）。在适当的正则性和正常型极值假设下：

$$ -\dot p^D=\partial_x H_D,\quad p_i^D(T)=\omega_i;\qquad -\dot p^A=\partial_x H_A,\quad p_i^A(T)=\nu_i.$$

Work 应显式展开 Jacobian 的来源节点索引并测试符号：

- `∂f_i/∂x_i = −z_i−δ_i−γ_i r_i`（因为 `β_{ii}=0`）；
- `∂f_i/∂x_l = (1−x_i) β_{li}(1−ε_l s_l)` 对 `l≠i`；
- 所以 `−ṗ_l^D=q_l+Σ_i p_i^D (∂f_i/∂x_l)`，攻击者 `−ṗ_l^A=g_l+Σ_i p_i^A (∂f_i/∂x_l)`。

给定状态/伴随轨迹，定义防御边际收益：

$$ M_i^s=\varepsilon_i x_i\sum_{k\ne i}\beta_{ik}(1-x_k)p_k^D,\qquad M_i^r=\gamma_i x_i p_i^D.$$

给定资源乘子 `λ_D≥0`，关于各控制的瞬时 Hamiltonian 最小化必要条件（本模型对控制为凸二次、可行集线性且紧）给出：

$$ s_i=\operatorname{clip}_{[0,1]}((M_i^s-h_i-\lambda_D b_i^s)/c_i^s),\quad r_i=\operatorname{clip}_{[0,1]}((M_i^r-\lambda_D b_i^r)/c_i^r).$$

攻击者使用最大化 KKT，`λ_A≥0`：

$$ a_i=\operatorname{clip}_{[0,1]}((\alpha_i(1-x_i)p_i^A-\lambda_A d_i^a)/c_i^a),\;i\in E;\quad a_i=0,\;i\notin E.$$

`λ_D,λ_A` 必须满足预算和互补松弛条件。**这些条件不证明整个动态博弈的均衡存在、唯一或全局可得。**

## 6. 待检验的优先级解释（不是预先证明的主定理）

单位容量净边际收益：`S_i=(M_i^s−h_i)/b_i^s`，`R_i=M_i^r/b_i^r`。在给定 `(t,x,p^D)`、微小的新增容量、控制接近零并考虑上界的局部情形，优先向正的最大值分配资源可能有合理解释；但不能写成全局多期阈值定理。优先级是否随价值/传播影响/业务代价而切换需要经理论附条件说明与真实数值结果确认。

## 7. 关键验证任务

- 校验状态正不变性、连续右端的局部 Lipschitz；Python 测试对照积分容差。
- 校验 `β_{ji}` 与 `s_j` 的来源节点索引，不将出站隔离错误作用于目标节点。
- 明确控制的凸 Hamiltonian 结构仅对**固定伴随量的瞬时问题**成立，不能替代全局 Nash 证明。
- 在 G1 提交导数、伴随方程、KKT 符号与维度的逐项核查表。

## 冻结记录
2026-10-26：用户明确批准G1；上述v2模型生效冻结。此处仅更新审批状态，不修改数学定义。
