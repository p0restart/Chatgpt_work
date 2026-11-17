# 防御完整二阶变分及带符号的DAG分解

对象B。以下对任意可行策略及可行线段方向成立；边界导数使用光滑延拓，凸性只沿域内线段判断。令b_ji=beta_ji(1-s_j)，z_i=alpha_i a_i+sum_j b_ji x_j，d_i=delta_i+gamma_i r_i，u=(s,r)，v=(v^s,v^r)。

## P1. 全部导数，不省略混合项

\[
(f_xy)_i=-(z_i+d_i)y_i+(1-x_i)\sum_jb_{ji}y_j,
\quad(f_uv)_i=-(1-x_i)\sum_j\beta_{ji}x_jv^s_j-\gamma_i x_i v^r_i.\tag{D1}
\]

\[
(f_{xx}[y,\tilde y])_i=-y_i\sum_jb_{ji}\tilde y_j-\tilde y_i\sum_jb_{ji}y_j,
\quad(f_{xu}[y,v])_i=y_i\sum_j\beta_{ji}x_jv^s_j-(1-x_i)\sum_j\beta_{ji}y_jv^s_j-\gamma_i y_i v^r_i.\tag{D2}
\]

f_uu=0，f_xxx=0，但f_xxu一般不为零；本二阶变分不需要省略它以外的任何二阶项。D1中的来源j索引与原beta.T实现一致；恢复混合项是本地i，不是来源j。

沿U+theta V微分，y=dx/dtheta、w=d²x/dtheta²：

\[
\dot y=f_xy+f_uv,\ y(0)=0;\qquad
\dot w=f_xw+f_{xx}[y,y]+2f_{xu}[y,v],\ w(0)=0.\tag{D3}
\]

原目标omega=0，因此

\[
D^2_{UU}J_D[V,V]=\underbrace{\int_0^T(\|v^s\|²+\|v^r\|²)dt}_{Q_{cost}=\Delta\|V\|²}
+\underbrace{\int_0^T q^Tw(t)dt}_{Q_{state}}.\tag{D4}
\]

q·w不预设符号。由-pdot=q+f_x^Tp、p(T)=0及分部积分亦得Qstate=integral p^T(fxx[y,y]+2fxu[y,v])。f_x是Metzler，q非负，所以p≥0；这不使括号自动非负。

## P2. 分离真正非负的曲率，避免重复粗绝对值界

对节点i，暂将上游感染输入z_i与本地d_i视作独立函数。记

\[
\xi_i=\sum_j\beta_{ji}[(1-s_j)y_j-x_jv^s_j],\quad
\rho_i=\gamma_i v^r_i,\quad
\zeta_i=\sum_j\beta_{ji}[(1-s_j)w_j-2v^s_jy_j].\tag{D5}
\]

令E_i(t,tau)=exp[-integral_tau^t(z_i+d_i)]、L_i(t,tau)=integral_tau^t(xi_i+rho_i)。由感染比例的另一积分因子表达

\[
x_i(t)=x_{0i}E_i(t,0)+\int_0^t z_i(\tau)E_i(t,\tau)d\tau
\]

两次微分并将含zeta的部分合并，得到**恒等式**

\[
w_i(t)=\int_0^t E_i(t,\tau)(1-x_i(\tau))\zeta_i(\tau)d\tau+P_i(t)-2\int_0^t E_i(t,\tau)\xi_i(\tau)L_i(t,\tau)d\tau,\tag{D6}
\]

\[
P_i(t)=x_{0i}E_i(t,0)L_i(t,0)^2+\int_0^t z_i(\tau)E_i(t,\tau)L_i(t,\tau)^2d\tau\ge0.\tag{D7}
\]

这是先保留符号、再估计剩余项的分解：所有节点P_i均可证明非负，源节点xi_i=zeta_i=0，故其全部恢复二阶曲率w_i=P_i≥0。没有把这一正项误当负项相加。隔离—上游状态项-2v^s_j y_j和暴露—本地恢复混合项仍可能有两种符号；不假定状态关于防御凸。

## P3. DAG比较核与输入输出界

拓扑顺序0,1,3,2,5,4。递推取

\[
\bar z_i=\alpha_i a_{cap}+\sum_j\beta_{ji}X_j,\qquad X_i=\max(x_{0i},\bar z_i/(\delta+\bar z_i)).\tag{D8}
\]

标量比较给0≤x_i≤X_i。a_cap=.8在每入口给合法上界；允许两个入口各取.8只是**比较上界的外包络**，不是重跑或改变原攻击域。其松弛会损失攻击共享容量相关性。

令L=beta^T，M=L-delta I。L^4=0；e^(Mt)=e^(-delta t) sum_(ell=0)^3 t^ell L^ell/ell!。设S=integral_0^T e^(Mt)dt。由D1及正系统比较，

\[
\|y_i\|_{L²}\le (G e)_i,\quad G=S[\,L\operatorname{diag}X,\operatorname{diag}(\gamma X)\,],\quad
e=(\|v^s_0\|_{L²},…,\|v^s_5\|_{L²},\|v^r_0\|_{L²},…,\|v^r_5\|_{L²}).\tag{D9}
\]

证明：逐分量|y|≤e^(M·)*Dinput|v|，零延拓至实线，对非负核使用Young卷积L1×L2→L2。不用全网统一Gronwall指数，也不忽略不可达零元素。

设E=L G+[LdiagX,0]、R=[0,diag gamma]，则||xi_i||L2≤(Ee)_i，||rho_i||L2≤(Re)_i。

## P4. 有限路径消去w，构造12维全域下界

D6中w的上游系数核非负并被Kbar_ij(t,tau)=beta_ji exp[-delta(t-tau)]支配。该Volterra核的四次复合为零，故(I-K)^-1=I+K+K²+K³，保持序。D7的非负项在沿路径传播后仍非负，可以整体丢去作下界。对其余两项取绝对值，定义非负N_i(t)使w≥Kw-N。则w≥-(I-K)^-1N≥-(I-Kbar)^-1N。对q积分，有限卷积的对偶权重被

\[
\ell=q+\beta S^Tq\tag{D10}
\]

逐分量控制。注意ell是状态层扰动N的有效权重，不应误用ODE强迫层的伴随p替代。

记I0=integral_0^T e^(-delta t)dt、I1=integral_0^T t e^(-delta t)dt。Fubini、Cauchy–Schwarz及Young给

\[
\int N_i\le2I_0\sum_j\beta_{ji}e^s_j(Ge)_j+2I_1(Ee)_i((E+R)e)_i.\tag{D11}
\]

第二项的未来核为k(v)=(e^(-delta v)-e^(-delta T))/delta、0≤v≤T，其L1范数恰为I1；这说明这里不是任意猜测时间常数。

令Z=[diag(beta ell),0]，构造非负对称矩阵

\[
W=I_0(Z^TG+G^TZ)+I_1[2E^T\operatorname{diag}(\ell)E+E^T\operatorname{diag}(\ell)R+R^T\operatorname{diag}(\ell)E].\tag{D12}
\]

于是Qstate≥-e^TWe≥-lambda_max(W)||e||²，而||e||²=Delta||V||²。因此若存在严格证书Wv≤kappa v、v>0，则由相似加权行和/Perron上界得lambda_max(W)≤kappa，并有

\[
\nabla²_{UU}J_D\succeq\Delta(1-\kappa)I.\tag{D13}
\]

此矩阵判据若kappa<1即可证明强凸。**当前严格有理数证书只能给kappa=40，故下界为-65I，而非正定。** 这证明有限弱凸性，不能证明或反证原目标凸性。相较Work E约-4667.75明显缩紧，但仍未关闭第一优先级目标。

## P5. 容量与仍丢失的相关性

B=1.2保留在真实策略域及所有可行方向；比较界对更大的盒域亦成立，因此覆盖真实域。D8/D9并未充分保留“高隔离、高恢复、低受损、低暴露不能同时各取独立最坏值”的相关性。这是证书仍松的具体原因，不是已经发现负方向。B的约束不能简单变成||v(t)||≤1.2：Hessian方向可任意归一化，不能把可行控制幅值当方向界。该常见错误在本证明中未使用。

数据库隔离可从最佳响应集合分析中定位为零，但不擅自删除正式72维策略定义。一般凸性、拟凸性和响应凸值仍没有由本界推出。弱凸性只保证J_D+(65/2)||U||²凸；这个加项仅是性质陈述，**没有添加到原模型或求解目标**。
