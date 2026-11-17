# 攻防交叉曲率的全域结构界

对象B，原参数。令W_D、W_A为两方逐槽方向；以下小写v(t)、b(t)是对应函数。令y^D、y^A为状态一阶变分，t=∂²x/(∂U∂A)[W_D,W_A]。原动力学没有直接u乘a，故

\[
\dot t=f_xt+f_{xx}[y^D,y^A]+f_{xu}[y^A,v]+f_{xa}[y^D,b],\quad t(0)=0,
\]

其中(f_xa[y,b])_i=-alpha_i y_i b_i（只在入口）。对任意非负状态权重w，伴随p^w=integral_t^T Phi_x(tau,t)^T w dtau满足0≤p^w(t)≤S^Tw。已证||y^D_i||L2≤(Ge_D)_i；攻击输入比较给G_A=S diag(alpha)E_entry，||y^A_i||L2≤(G_A e_A)_i。

逐项对混合变分而非完整防御Hessian取绝对值，Cauchy–Schwarz给

\[
|D²_{UA}\int w^Tx|\le e_D^T C(w)e_A,
\]

\[
C(w)=G^T[\operatorname{diag}(p)\beta^T+\beta\operatorname{diag}(p)]G_A+R_DG_A+G^T\operatorname{diag}(\alpha p)E_{entry},\quad p=S^Tw,
\]

\[
R_D=\begin{bmatrix}\operatorname{diag}(\beta p)+\operatorname{diag}(X)\beta\operatorname{diag}(p)\\\operatorname{diag}(\gamma p)\end{bmatrix}.\tag{M1}
\]

首项是f_xx，R_D上半部两个项分别对应隔离对上游变分和对接收变分的耦合，下半部是恢复，末项是入口攻击—状态耦合。所有矩阵元素非负，保留DAG可达零结构。

因||e_D||=sqrt(Delta)||W_D||、||e_A||=sqrt(Delta)||W_A||，逐槽欧氏混合算子范数≤Delta||C(w)||₂。

本模型H_DA=.5D²_UA(J_D-J_A)，双方直接成本无交叉，q-g=(0,0,0,0,3,0)，omega=nu=0。所以只需w=3e_database，而不是把所有q和g相加。该权重使其他节点的直接状态收益交叉曲率严格相消，但数据库路径仍然贡献，不得置零。

证书对非负对称C(w)C(w)^T找到正有理向量v，精确验证C(w)C(w)^Tv≤253v。因此

\[
\|H_{DA}\|²\le(\Delta²/4)253=6325/36,\quad \|H_{DA}\|<13.255.\tag{M2}
\]

这是保守全域上界；不是Work E约.2–.36的样点范数。不能把大上界解释为真实交叉耦合大到破坏单调性。

以w=g同样认证||C(g)||²≤405，故-J_A的攻击梯度关于U的Lipschitz常数≤Delta sqrt(405)。结合m_A=Delta，得到**实际模型的攻击全局响应映射**

\[
\|BR_A(U)-BR_A(V)\|≤\sqrt{405}\|U-V\|.\tag{M3}
\]

证明由两个全局凸攻击子问题的最优性VI相减，再使用攻击强单调性和交叉梯度界，不需要假设活跃约束保持不变。常数大于1，且防御响应单值未知，故不提供复合最佳响应压缩。
