# 3 博弈分析与数值求解

## 3.1 开环Nash条件与计算对象

在第2节定义的策略集合上，开环Nash控制对\((u^*,a^*)\)要求任一方在对手计划固定时均不能通过单边改变整个时间计划改善目标，即

\[
J_D(u^*,a^*)\leq J_D(u,a^*)\quad\forall u\in\mathcal U,
\qquad
J_A(u^*,a^*)\geq J_A(u^*,a)\quad\forall a\in\mathcal A. \tag{6}
\]

式(6)是理论上的比较条件，不预设其解存在或唯一。实际计算限制在有限个控制槽的分段常值策略集合内，并使用局部优化搜索单方响应。因此，下文将程序输出称为经局部响应诊断的开环候选，不将交替更新停止等同于式(6)成立。

## 3.2 Hamiltonian与状态伴随关系

分别将式(4)、(5)的积分被积函数记为\(L_D,L_A\)，引入防御与攻击伴随向量\(p^D,p^A\)，定义

\[
H_D=L_D+(p^D)^\top f,
\qquad H_A=L_A+(p^A)^\top f. \tag{7}
\]

固定对手的可行计划，考虑本方的最优控制问题。向量场和瞬时目标对状态及本方控制连续可微，控制集合固定、紧且凸，初始状态固定，终端状态自由、终端成本可微。在正常型最优控制满足Pontryagin极值原理（Pontryagin maximum principle，PMP）的条件下，状态方程与伴随方程及几乎处处的Hamiltonian极值条件构成必要条件。状态立方体的边界由动力学保持，不在此额外施加独立的状态路径约束。

沿给定轨迹，记\(F_{i\ell}=\partial f_i/\partial x_\ell\)。由\(\beta_{ii}=0\)，状态Jacobian为

\[
F_{ii}=-z_i-d_i,
\qquad F_{i\ell}=(1-x_i)\beta_{\ell i}(1-\varepsilon_\ell s_\ell)
\quad(\ell\ne i). \tag{8}
\]

非对角项中的\(\ell\)为来源，\(i\)为接收节点。令\(\ell\)为伴随分量索引，将矩阵形式\(-\dot p=\partial_x L+F^\top p\)展开，得到

\[
\begin{aligned}
-\dot p_\ell^D&=q_\ell-(z_\ell+d_\ell)p_\ell^D
 +(1-\varepsilon_\ell s_\ell)\sum_{i\ne\ell}\beta_{\ell i}(1-x_i)p_i^D,
&p_\ell^D(T)&=\omega_\ell,\\
-\dot p_\ell^A&=g_\ell-(z_\ell+d_\ell)p_\ell^A
 +(1-\varepsilon_\ell s_\ell)\sum_{i\ne\ell}\beta_{\ell i}(1-x_i)p_i^A,
&p_\ell^A(T)&=\nu_\ell.
\end{aligned} \tag{9}
\]

防御侧最小化\(H_D\)，攻击侧最大化\(H_A\)；两者在上述各自目标约定下均具有式(9)的伴随符号。代码为统一调用最小化器，将攻击目标写为\(F_A=-J_A\)，其状态收益和终端项分别为\(-g^\top x\)和\(-\nu^\top x(T)\)，攻击二次成本则为正。这与理论最大化\(J_A\)等价；若使用该最小化约定定义连续伴随，它对应\(-p^A\)，不能与式(9)的\(p^A\)混用。

在非负权重下，\(F\)的非对角元非负，反向时间伴随系统的输入及初值也非负，故\(p^D,p^A\geq0\)。这些量描述沿给定控制轨迹增加受损状态所产生的后续边际目标变化，不是对所有状态的反馈价值函数。PMP关系没有建立博弈的存在性、唯一性或求解迭代的全局收敛性。

## 3.3 隔离和恢复的边际作用

对来源节点\(i\)的控制求偏导，有

\[
\frac{\partial f_k}{\partial s_i}
=-(1-x_k)\beta_{ik}\varepsilon_i x_i,
\qquad
\frac{\partial f_k}{\partial r_i}=-\gamma_i x_i\mathbf1_{\{k=i\}},
\qquad
\frac{\partial f_k}{\partial a_i}=\alpha_i(1-x_i)\mathbf1_{\{k=i\}}. \tag{10}
\]

其中\(\mathbf1\)为指示函数，且第一式在\(k=i\)时因零自环等于零。由此定义两类防御行动对未来损失的瞬时边际削减量

\[
M_i^s=\varepsilon_i x_i\sum_{k\ne i}\beta_{ik}(1-x_k)p_k^D,
\qquad M_i^r=\gamma_i x_ip_i^D. \tag{11}
\]

隔离直接减少下游状态的增长，其价值取决于来源受损程度、可传播的下游比例及下游伴随损失；恢复直接减少本地受损，同时通过之后的状态演化影响外传损害。两类伴随量都含未来传播与直接损失的信息，因而不能将其概括为“隔离只看传播、恢复只看价值”。源端隔离与接收端防护的区别在于控制直接改变哪些状态方程；这是干预位置的区别，而非新的普遍资源配置定理。

## 3.4 瞬时容量约束下的KKT条件

固定\((t,x,p^D,p^A)\)以及对手控制后，防御Hamiltonian关于\((s,r)\)具有正定对角二次项，攻击Hamiltonian关于入口\(a\)具有负定对角二次项。因此，本方瞬时子问题分别严格凸和严格凹，在非空紧多面体上各有唯一控制解。此结论不包含状态对整段控制的非线性依赖，不能推广为完整动态目标的全局凸性或凹性。

使用Karush–Kuhn–Tucker（KKT）条件，防御拉格朗日函数取\(H_D+\lambda_D[\sum_i(b_i^ss_i+b_i^rr_i)-B]\)，攻击取\(H_A-\lambda_A[\sum_i d_i^aa_i-A]\)。容量乘子\(\lambda_D,\lambda_A\geq0\)。以\(\operatorname{clip}_{[0,1]}(v)=\min(1,\max(0,v))\)合并箱约束，可得

\[
\begin{aligned}
s_i&=\operatorname{clip}_{[0,1]}
 \left(\frac{M_i^s-h_i-\lambda_Db_i^s}{c_i^s}\right),\\
r_i&=\operatorname{clip}_{[0,1]}
 \left(\frac{M_i^r-\lambda_Db_i^r}{c_i^r}\right),\\
a_i&=\operatorname{clip}_{[0,1]}
 \left(\frac{\alpha_i(1-x_i)p_i^A-\lambda_Ad_i^a}{c_i^a}\right)
 \quad(i\in\mathcal E),\qquad a_i=0\quad(i\notin\mathcal E).
\end{aligned} \tag{12}
\]

容量可行性与互补松弛为

\[
\begin{aligned}
&\sum_i(b_i^ss_i+b_i^rr_i)\leq B,\quad
\lambda_D\left[\sum_i(b_i^ss_i+b_i^rr_i)-B\right]=0,\\
&\sum_i d_i^aa_i\leq A,\quad
\lambda_A\left[\sum_i d_i^aa_i-A\right]=0.
\end{aligned} \tag{13}
\]

容量松弛时相应乘子为零；容量绑定不必意味着乘子严格为正。正二次成本使边际回报随投入下降。在控制接近零且允许增加的方向上，\((M_i^s-h_i)/b_i^s\)与\(M_i^r/b_i^r\)提供单位容量边际比较；非零投入处须分别扣除\(c_i^ss_i\)与\(c_i^rr_i\)，并处理箱约束饱和。这一解释以当前状态和伴随为条件，不给出跨整个时域固定不变的资源优先级。

## 3.5 分段开环直接射击

将\([0,T]\)等分为\(K\)个槽，槽长\(\Delta=T/K\)，在第\(k\)槽采用常值\((a_k,s_k,r_k)\)，\(k=0,\ldots,K-1\)。由此得到\(\mathcal U_K\subset\mathcal U\)及\(\mathcal A_K\subset\mathcal A\)。每槽满足式(1)即可保证逐时容量几乎处处成立，不在约束左侧额外乘槽长。防御变量按每槽\([s_k,r_k]\)排列，攻击变量仅保留入口分量。

采用直接射击：给定槽变量，以经典四阶Runge–Kutta（RK4）法同时积分状态和累计目标，每槽使用\(H\)个子步，步长为\(T/(KH)\)。梯度通过同步传播RK4离散映射的状态灵敏度获得。固定对手后，以序列最小二乘规划（Sequential Least Squares Programming，SLSQP）在箱约束和线性容量约束下最小化\(J_D\)或\(-J_A\)。这一路径不求解连续PMP状态—伴随边值问题；式(12)用于结构分析，也不能逐时套用后代替常值槽优化，因为槽变量的梯度汇总整个槽及其后续状态影响。

单方局部搜索将当前可行计划保留为候选，并根据登记起点集合求解。返回点只有在目标有限、容量及边界违反不超过\(10^{-10}\)，且目标不劣于保留候选时才替换候选。该接受规则本身不要求优化器退出成功，因此退出码、响应残差及通过字段另行保存，不能把可行改善点直接称为成功最优响应。当前实现拒绝非有限输入与非整数子步，并检查完成的RK4子步及灵敏度；可行计划积分越界时显式失败，不裁剪状态或自动隐藏失败。容量集合外的有限线搜索试探保留平滑目标扩展，但不作为可行结果接受。

基础配置为\(n=6,K=6,T=10\)。积分、优化器和随机种子的复现设置单列于本目录复现备注。

算法1给出主要匹配实验实际使用的强化流程。令\(\widehat\Delta_D,\widehat\Delta_A\)为第3.6节的已发现改善，\(R_D,R_A\)为当前候选残差，\(d_{\rm resp}\)为双方响应计划相对当前计划的最大分量变化。

```text
算法1：匹配实验的分段开环局部候选求解与审计
输入：冻结模型、T、K、积分子步H、登记种子、可行初始计划c=(a,s,r)
单路径 StrictSolve(c,H)：
  对轮次 m=0,...,40：
    固定同一个c，分别从当前本方计划启动SLSQP，求防御响应d与攻击响应b
    计算当前c的双方目标、已发现相对改善、R_D、R_A及d_resp
    检查：相对改善均≤1e-7；R_D,R_A≤1e-4；d_resp≤1e-3；双方优化退出成功
    若检查通过：保存当前c及通过记录，返回
    若m=40：保存当前c及未通过记录，返回
    固定防御响应d，再求攻击方对(a,d_s,d_r)的局部响应b_seq
    记录顺序攻击响应及退出码，更新c=(b_seq_a,d_s,d_r)
  不把达到轮数上限视为数值通过
主流程：
  从均分、零、随机三类可行初值分别执行StrictSolve，保留全部路径
  以均分路径为登记主路径，比较三路径终点，不择优删除路径
  对主路径执行12起点与各单通道稀疏起点的单方偏离审计
  以主路径为初值、H=48执行StrictSolve，再作三起点偏离审计
  汇总路径通过标记、优化退出码、约束、积分与跨初值控制差
输出：全部计划、轨迹、目标、诊断及通过/失败标记；不输出全局均衡证书
```





## 3.6 候选质量与偏离边界

给定控制对\((u,a)\)，在精确ODE目标下，\(K\)槽策略类中的全局单边改善定义为

\[
\Delta_D^K=J_D(u,a)-\min_{v\in\mathcal U_K}J_D(v,a),
\qquad
\Delta_A^K=\max_{b\in\mathcal A_K}J_A(u,b)-J_A(u,a). \tag{14}
\]

有限槽可行集合紧且目标连续，单方极值可取到，但局部优化器不保证找到该极值。令带帽目标\(\widehat J\)表示实际RK4数值目标，\(\widetilde u,\widetilde a\)表示搜索返回的可行响应。当前核心偏离接口保存有符号差，并将展示的非负已发现改善定义为

\[
\begin{aligned}
\widehat\Delta_D&=\max\{0,\widehat J_D(u,a)-\widehat J_D(\widetilde u,a)\},\\
\widehat\Delta_A&=\max\{0,\widehat J_A(u,\widetilde a)-\widehat J_A(u,a)\},\\
\widehat\rho_D&=\frac{\widehat\Delta_D}{1+|\widehat J_D(u,a)|},\qquad
\widehat\rho_A=\frac{\widehat\Delta_A}{1+|\widehat J_A(u,a)|}.
\end{aligned} \tag{15}
\]

相对于同一数值目标的全局搜索，已发现改善至多提供改善的下界，小的已发现改善不是未知全局最佳响应改善的上界。因此，低于工程门槛不能作为全局Nash证书；考虑积分误差后，它也不是式(14)真实ODE改善的严格界。若要形成严格界，还需覆盖相关可行控制的统一积分误差控制，而保存候选上的精化差不提供该保证。

对本方槽向量\(v\)、相应可行多面体\(\mathcal C\)及最小化目标\(F\)（防御为\(\widehat J_D\)，攻击为\(-\widehat J_A\)），使用欧氏投影\(\Pi_{\mathcal C}\)定义

\[
R(v)=\left\|v-\Pi_{\mathcal C}\bigl(v-\nabla F(v)\bigr)\right\|_\infty. \tag{16}
\]

该量检查离散目标的一阶驻点条件，依赖目标与变量尺度，零残差也不证明全局最优。多起点终点相近、成功退出和积分精化进一步约束数值不确定性，但不消除远处未发现偏离。流程状态“完成”与数值门槛“通过”分别记录，使用结果时同时检查。

最后，控制槽数\(K\)改变策略空间，每槽积分子步\(H\)只改变固定策略类的积分精度，两者不能互相替代。\(K=12\)补充研究仅覆盖两组预指定实例的四格，隔离依赖环境复现另限于一组\(K=6\)四格，具体结果与变化范围在实验部分报告。小规模有限策略表的纯均衡也只属于其特定离散菜单，不认证六节点连续动作问题。本文据此将理论必要条件、受限策略类的全局偏离量、局部搜索发现的改善和数值积分诊断分别表述。
