# D1–D2 公式与术语一致性核对

日期：2026-11-11。结论：**PASS**。当前D1两份正文与11月11日重组说明均与D2源清单逐字节哈希一致；式(1)至(20)各有且仅有一处定义，编号连续。未发现旧式号误用，故无需修改D1或交叉引用。仅式(18)百分数显示方式与5.1相对量级按本轮授权修订。

## 1. 当前版本与哈希

|文件|当前SHA256|D2 source_manifest登记一致|
|---|---|---|
|04_system_model_zh.md|`e41b7cb65072b1201e2397feadfc3be1a8c80e1df51441f1ad75d502894f49f3`|是|
|05_game_solution_zh.md|`da2d3d235e6297fa490e8d983911a0d5809bdc6b0fd77f0477a3dc70c2f1bed6`|是|
|D1_model_rewrite_note.md|`94b8c02994d760d5a05bee2b2920d610a73644be9babcb1720ce3bc05426dba7`|是|

核对清单：analysis/source_manifest.json。D1_R1_verification.json是更早R1历史清单，其求解节哈希不是11月11日现稿哈希；不得用旧清单否定当前D2接管版本。重组说明将旧动力学(1)→现(3)、旧防御目标(2)→现(4)、旧攻击目标(3)→现(5)、旧容量(4)→现(1)、旧策略集合(5)→现(2)，式(6)–(16)不变。D2确实沿用此新顺序。

## 2. 逐式定位与引用

行号为本次受控修订后的UTF-8文本行号；链接中的L行锚供审查定位，Markdown查看器不支持时按所列行号查找。“无显式式号引用”不等于没有使用相应定义。

|式|定义章节/位置|数学定义与一致性判读|两份D1及D2第4/5节中的显式引用位置|
|---:|---|---|---|
|1|2.3 策略集合与资源约束；[work_d1/04_system_model_zh.md:41](../work_d1/04_system_model_zh.md#L41)|双方逐时容量约束；成本系数与占用系数区分|[work_d1/04_system_model_zh.md:46](../work_d1/04_system_model_zh.md#L46)（2.3 策略集合与资源约束）；[work_d1/04_system_model_zh.md:46](../work_d1/04_system_model_zh.md#L46)（2.3 策略集合与资源约束）；[work_d1/05_game_solution_zh.md:106](../work_d1/05_game_solution_zh.md#L106)（3.5 分段开环直接射击）|
|2|2.3 策略集合与资源约束；[work_d1/04_system_model_zh.md:51](../work_d1/04_system_model_zh.md#L51)|有界可测的完整开环策略集合|无显式式号引用；定义就地解释|
|3|2.4 策略作用下的状态演化；[work_d1/04_system_model_zh.md:65](../work_d1/04_system_model_zh.md#L65)|源端隔离与本地恢复的受损比例ODE|[work_d1/04_system_model_zh.md:97](../work_d1/04_system_model_zh.md#L97)（2.6 博弈定义与研究问题）|
|4|2.5 双方目标与非零和结构；[work_d1/04_system_model_zh.md:82](../work_d1/04_system_model_zh.md#L82)|防御累计损失、业务中断、二次成本与终端项（最小化）|[work_d1/04_system_model_zh.md:97](../work_d1/04_system_model_zh.md#L97)（2.6 博弈定义与研究问题）；[work_d1/05_game_solution_zh.md:17](../work_d1/05_game_solution_zh.md#L17)（3.2 Hamiltonian与状态伴随关系）；[work_d2/02_experimental_design_zh.md:81](02_experimental_design_zh.md#L81)（4.5 评价指标与数值诊断）|
|5|2.5 双方目标与非零和结构；[work_d1/04_system_model_zh.md:90](../work_d1/04_system_model_zh.md#L90)|攻击状态收益减二次投入成本及终端项（最大化）|[work_d1/04_system_model_zh.md:97](../work_d1/04_system_model_zh.md#L97)（2.6 博弈定义与研究问题）；[work_d1/05_game_solution_zh.md:17](../work_d1/05_game_solution_zh.md#L17)（3.2 Hamiltonian与状态伴随关系）；[work_d2/02_experimental_design_zh.md:81](02_experimental_design_zh.md#L81)（4.5 评价指标与数值诊断）|
|6|3.1 开环Nash条件与计算对象；[work_d1/05_game_solution_zh.md:10](../work_d1/05_game_solution_zh.md#L10)|完整开环Nash的双边偏离不等式，仅作理论定义|[work_d1/04_system_model_zh.md:99](../work_d1/04_system_model_zh.md#L99)（2.6 博弈定义与研究问题）；[work_d1/05_game_solution_zh.md:13](../work_d1/05_game_solution_zh.md#L13)（3.1 开环Nash条件与计算对象）；[work_d1/05_game_solution_zh.md:13](../work_d1/05_game_solution_zh.md#L13)（3.1 开环Nash条件与计算对象）|
|7|3.2 Hamiltonian与状态伴随关系；[work_d1/05_game_solution_zh.md:21](../work_d1/05_game_solution_zh.md#L21)|双方Hamiltonian，L_D/L_A来自现式(4)/(5)|无显式式号引用；定义就地解释|
|8|3.2 Hamiltonian与状态伴随关系；[work_d1/05_game_solution_zh.md:31](../work_d1/05_game_solution_zh.md#L31)|状态Jacobian；行是接收节点，非对角列是来源|无显式式号引用；定义就地解释|
|9|3.2 Hamiltonian与状态伴随关系；[work_d1/05_game_solution_zh.md:44](../work_d1/05_game_solution_zh.md#L44)|两套伴随方程与终端条件；攻击最大化符号不混用−J_A|[work_d1/05_game_solution_zh.md:47](../work_d1/05_game_solution_zh.md#L47)（3.2 Hamiltonian与状态伴随关系）；[work_d1/05_game_solution_zh.md:47](../work_d1/05_game_solution_zh.md#L47)（3.2 Hamiltonian与状态伴随关系）|
|10|3.3 隔离和恢复的边际作用；[work_d1/05_game_solution_zh.md:61](../work_d1/05_game_solution_zh.md#L61)|控制对状态向量场的偏导；隔离作用于来源出边|无显式式号引用；定义就地解释|
|11|3.3 隔离和恢复的边际作用；[work_d1/05_game_solution_zh.md:68](../work_d1/05_game_solution_zh.md#L68)|瞬时边际削减量M_i^s/M_i^r，不是通用排序定理|无显式式号引用；定义就地解释|
|12|3.4 瞬时容量约束下的KKT条件；[work_d1/05_game_solution_zh.md:88](../work_d1/05_game_solution_zh.md#L88)|固定状态/伴随的瞬时KKT截断解|[work_d1/05_game_solution_zh.md:108](../work_d1/05_game_solution_zh.md#L108)（3.5 分段开环直接射击）|
|13|3.4 瞬时容量约束下的KKT条件；[work_d1/05_game_solution_zh.md:99](../work_d1/05_game_solution_zh.md#L99)|容量可行性与互补松弛，绑定不强迫乘子正|无显式式号引用；定义就地解释|
|14|3.6 候选质量与偏离边界；[work_d1/05_game_solution_zh.md:149](../work_d1/05_game_solution_zh.md#L149)|K槽类中精确ODE目标的全局单边改善（未由局部求解认证）|[work_d1/05_game_solution_zh.md:163](../work_d1/05_game_solution_zh.md#L163)（3.6 候选质量与偏离边界）|
|15|3.6 候选质量与偏离边界；[work_d1/05_game_solution_zh.md:160](../work_d1/05_game_solution_zh.md#L160)|RK4目标的非负已发现改善及1+绝对目标归一化|[work_d2/02_experimental_design_zh.md:87](02_experimental_design_zh.md#L87)（4.5 评价指标与数值诊断）；[work_d2/02_experimental_design_zh.md:99](02_experimental_design_zh.md#L99)（4.5 评价指标与数值诊断）|
|16|3.6 候选质量与偏离边界；[work_d1/05_game_solution_zh.md:168](../work_d1/05_game_solution_zh.md#L168)|离散目标梯度的欧氏投影无穷范数残差|[work_d2/02_experimental_design_zh.md:99](02_experimental_design_zh.md#L99)（4.5 评价指标与数值诊断）|
|17|4.2 匹配四格设计；[work_d2/02_experimental_design_zh.md:47](02_experimental_design_zh.md#L47)|同seed/B的价值位置效应与四格交互；上标是实验格|[work_d2/02_experimental_design_zh.md:97](02_experimental_design_zh.md#L97)（4.5 评价指标与数值诊断）|
|18|4.5 评价指标与数值诊断；[work_d2/02_experimental_design_zh.md:84](02_experimental_design_zh.md#L84)|同配置/评价的基线分母改善率；乘100后的数值以%报告|[work_d2/03_results_discussion_zh.md:27](03_results_discussion_zh.md#L27)（5.1 价值位置与传播条件的交互）；[work_d2/03_results_discussion_zh.md:55](03_results_discussion_zh.md#L55)（5.3 与强基线的比较）|
|19|4.5 评价指标与数值诊断；[work_d2/02_experimental_design_zh.md:94](02_experimental_design_zh.md#L94)|时间窗控制均值/积分与逐槽容量；积分不是二次成本|无显式式号引用；定义就地解释|
|20|4.5 评价指标与数值诊断；[work_d2/02_experimental_design_zh.md:104](02_experimental_design_zh.md#L104)|六槽复制到十二槽后目标差、完整防御/攻击控制无穷范数差|[work_d2/03_results_discussion_zh.md:95](03_results_discussion_zh.md#L95)（5.5 数值可靠性与稳健性）|

## 3. 术语及边界复核

|术语|D1定义|D2采用及判读|
|---|---|---|
|x_i|实例组受损比例|状态图与正文一致，不写单机概率|
|beta_ji与s_j|来源j到接收i；隔离抑制来源出边|8条边、出向和及节点解释一致|
|u=(s,r)|完整防御计划|式(20)只含防御两控制，a另列。图1的u/v为局部边标签，图注已明确限定，不改变全局u定义；后续模板排版宜使用完整beta下标以降低阅读负担，本轮不改图形|
|q/g|双方损失/收益权重分开|价值交换只变q；g=1不变|
|A/B与上标A—D|容量与实验格属于不同语境|式(17)明确上标为实验格，J_D下标为防御者|
|b与c|容量系数与目标成本不同|式(19)及参数表保持区分|
|K/H|控制槽与槽内积分子步|策略类扩大与积分精化分别解释|
|M_i^s/M_i^r|依赖轨迹的瞬时边际量|5.2定性解释，不称普适优先级定理|
|Delta/rho/R|全局偏离、已发现改善、驻点残差不同|D2沿用式(15)/(16)，未把局部发现量写成全局上界|
|G百分数与交互相对量级|G是新增方法评价量，非rho|G乘100后以%显示；I_J/J_D^C仅为交互尺度，不混作G|
|adaptive_attack|模型仍同时开环|冻结防御后求局部攻击响应，不是实时反馈或Stackelberg|

## 4. 相对量级的只读复算

源文件为tables/matched_four_cells.csv，指标为100×interaction/J_C；J_C对应同seed/B、H48的C格防御损失。仅在报告与5.1添加解释，不修改或新增数值CSV、不积分、不优化。

|seed|B|I_J/J_D^C换算值(%)|
|---:|---:|---:|
|11|0.6|0.170153577|
|11|1.2|0.210765791|
|11|1.8|0.181643959|
|22|0.6|0.178114099|
|22|1.2|0.206443581|
|22|1.8|0.180967819|
|33|0.6|0.211389275|
|33|1.2|0.260639149|
|33|1.8|0.205521610|

## 5. 受控修订与审批边界

没有旧式号误用；D1两个正文、重组说明、冻结模型、源数据和历史审批只读。式(18)仅统一百分数排版，5.1只增补相对量级与分母。数值文件保持不变。达到本轮版本对齐条件，不等于G-D2人工批准；等待用户明确批准后才可进入D3，无需重做D2数据分析。
