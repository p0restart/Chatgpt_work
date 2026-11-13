"""Controlled D2 text revision and read-only equation audit; no solver imports."""
from pathlib import Path
import json,hashlib,re,csv
R=Path(__file__).resolve().parents[3]; O=R/'paper/work_d2'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,s):p.write_text(s,encoding='utf-8')
inputs=json.loads((O/'analysis/source_manifest.json').read_text())
d1=[R/'paper/work_d1'/n for n in ['04_system_model_zh.md','05_game_solution_zh.md','D1_model_rewrite_note.md']]
assert all(sha(p)==inputs[p.relative_to(R).as_posix()]['sha256'] for p in d1)
before={p.relative_to(R).as_posix():sha(p) for p in list((O/'tables').glob('*'))+list((O/'figures').glob('*')) if p.is_file()}
hist=O/'analysis/minimal_revision_before';hist.mkdir(exist_ok=True)
for n in ['02_experimental_design_zh.md','03_results_discussion_zh.md','D2_handoff.md','00_D2_evidence_inventory.md','analysis/delivery_manifest.json']:
    p=O/n;dst=hist/p.name
    if not dst.exists():dst.write_bytes(p.read_bytes())
p=O/'02_experimental_design_zh.md';s=p.read_text(encoding='utf-8')
s=s.replace(r'G_{m,e}=100\frac{J_D^{m,e}-J_D^{\mathrm{Joint},e}}{J_D^{m,e}}\%. \tag{18}',r'G_{m,e}=100\frac{J_D^{m,e}-J_D^{\mathrm{Joint},e}}{J_D^{m,e}}. \tag{18}')
s=s.replace('正值表示联合动态损失较低，负值表示较高。该分母',r'\(G_{m,e}\)表示以百分数报告时的数值，表3统一以“%”标注单位；例如\(G_{m,e}=0.1\)表示损失降低0.1%。正值表示联合动态损失较低，负值表示较高。该分母')
put(p,s)
rows=list(csv.DictReader((O/'tables/matched_four_cells.csv').open(encoding='utf-8-sig')))
for x in rows:x['relative_pct']=100*float(x['interaction'])/float(x['J_C'])
p=O/'03_results_discussion_zh.md';s=p.read_text(encoding='utf-8')
anchor='三个种子均在中容量取得较大的目标交互，而非随容量单调增大。'
new=r'为说明该交互相对总损失的量级，以同一种子、同一容量下C格的防御损失\(J_D^C\)为参照，将\(I_J/J_D^C\)换算为百分数，九组结果为0.170%—0.261%；低、中、高容量分别为0.170%—0.211%、0.206%—0.261%和0.181%—0.206%。该比例仅对四格交互作尺度归一化，不是式(18)的防御方法改善率，也不表示一项可以与强基线收益相加的独立收益。'
if new not in s:s=s.replace(anchor,anchor+'\n\n'+new)
put(p,s)
files=d1[:2]+[O/'02_experimental_design_zh.md',O/'03_results_discussion_zh.md']
defs={};refs={i:[] for i in range(1,21)}
for p in files:
    sec=''; lines=p.read_text(encoding='utf-8').splitlines()
    for i,line in enumerate(lines,1):
        if line.startswith('## '):sec=line[3:]
        for n in re.findall(r'\\tag\{(\d+)\}',line):
            assert int(n) not in defs
            defs[int(n)]=(p,sec,i)
        for group in re.findall(r'式\(\d+\)(?:、\(\d+\))*',line):
            for n in re.findall(r'\((\d+)\)',group):refs[int(n)].append((p,sec,i))
assert sorted(defs)==list(range(1,21))
names=['双方逐时容量约束；成本系数与占用系数区分','有界可测的完整开环策略集合','源端隔离与本地恢复的受损比例ODE','防御累计损失、业务中断、二次成本与终端项（最小化）','攻击状态收益减二次投入成本及终端项（最大化）','完整开环Nash的双边偏离不等式，仅作理论定义','双方Hamiltonian，L_D/L_A来自现式(4)/(5)','状态Jacobian；行是接收节点，非对角列是来源','两套伴随方程与终端条件；攻击最大化符号不混用−J_A','控制对状态向量场的偏导；隔离作用于来源出边','瞬时边际削减量M_i^s/M_i^r，不是通用排序定理','固定状态/伴随的瞬时KKT截断解','容量可行性与互补松弛，绑定不强迫乘子正','K槽类中精确ODE目标的全局单边改善（未由局部求解认证）','RK4目标的非负已发现改善及1+绝对目标归一化','离散目标梯度的欧氏投影无穷范数残差','同seed/B的价值位置效应与四格交互；上标是实验格','同配置/评价的基线分母改善率；乘100后的数值以%报告','时间窗控制均值/积分与逐槽容量；积分不是二次成本','六槽复制到十二槽后目标差、完整防御/攻击控制无穷范数差']
def link(p,i):return f'[{p.parent.name}/{p.name}:{i}]({"../work_d1/" if p.parent.name=="work_d1" else ""}{p.name}#L{i})'
report='# D1–D2 公式与术语一致性核对\n\n日期：2026-11-11。结论：**PASS**。当前D1两份正文与11月11日重组说明均与D2源清单逐字节哈希一致；式(1)至(20)各有且仅有一处定义，编号连续。未发现旧式号误用，故无需修改D1或交叉引用。仅式(18)百分数显示方式与5.1相对量级按本轮授权修订。\n\n## 1. 当前版本与哈希\n\n|文件|当前SHA256|D2 source_manifest登记一致|\n|---|---|---|\n'
for p in d1:report+=f'|{p.name}|`{sha(p)}`|是|\n'
report+='\n核对清单：analysis/source_manifest.json。D1_R1_verification.json是更早R1历史清单，其求解节哈希不是11月11日现稿哈希；不得用旧清单否定当前D2接管版本。重组说明将旧动力学(1)→现(3)、旧防御目标(2)→现(4)、旧攻击目标(3)→现(5)、旧容量(4)→现(1)、旧策略集合(5)→现(2)，式(6)–(16)不变。D2确实沿用此新顺序。\n\n## 2. 逐式定位与引用\n\n行号为本次受控修订后的UTF-8文本行号；链接中的L行锚供审查定位，Markdown查看器不支持时按所列行号查找。“无显式式号引用”不等于没有使用相应定义。\n\n|式|定义章节/位置|数学定义与一致性判读|两份D1及D2第4/5节中的显式引用位置|\n|---:|---|---|---|\n'
for n,(p,sec,i) in sorted(defs.items()):
    rr='；'.join(link(a,k)+'（'+b+'）' for a,b,k in refs[n]) or '无显式式号引用；定义就地解释'
    report+=f'|{n}|{sec}；{link(p,i)}|{names[n-1]}|{rr}|\n'
report+='''
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
'''
for x in rows:report+=f"|{x['seed']}|{x['B']}|{x['relative_pct']:.9f}|\n"
report+='\n## 5. 受控修订与审批边界\n\n没有旧式号误用；D1两个正文、重组说明、冻结模型、源数据和历史审批只读。式(18)仅统一百分数排版，5.1只增补相对量级与分母。数值文件保持不变。达到本轮版本对齐条件，不等于G-D2人工批准；等待用户明确批准后才可进入D3，无需重做D2数据分析。\n'
put(O/'D1_D2_equation_alignment.md',report)
post={p:sha(R/p) for p in before};assert post==before
rec=dict(status='PASS_ALIGNMENT_WAITING_USER_G_D2',D1_hashes={p.relative_to(R).as_posix():sha(p) for p in d1},numeric_and_figure_files_unchanged=len(before),old_reference_misuse=False,equations=list(defs),experiments_run=False)
put(O/'analysis/minimal_revision_verification.json',json.dumps(rec,ensure_ascii=False,indent=2))
put(O/'analysis/minimal_revision_protected_hashes.json',json.dumps(before,ensure_ascii=False,indent=2))
print(json.dumps(rec,ensure_ascii=False,indent=2))
