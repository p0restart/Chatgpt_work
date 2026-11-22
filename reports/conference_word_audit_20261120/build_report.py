from pathlib import Path
import json
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT

R=Path(__file__).resolve().parent
d=Document()
sec=d.sections[0]
sec.page_width=Inches(8.2677);sec.page_height=Inches(11.6929)
sec.top_margin=sec.bottom_margin=Inches(.75)
sec.left_margin=sec.right_margin=Inches(.78)
for name in ['Normal','Body Text','Title','Heading 1','Heading 2','Heading 3']:
 st=d.styles[name];st.font.name='Times New Roman';st.font.color.rgb=RGBColor(0,0,0)
 st.element.get_or_add_rPr().get_or_add_rFonts().set(qn('w:eastAsia'),'宋体')
 st.font.size=Pt(10.5)
 st.paragraph_format.space_after=Pt(4)
 st.paragraph_format.line_spacing=1.08
for name,size in [('Title',18),('Heading 1',14),('Heading 2',11.5),('Heading 3',10.5)]:
 st=d.styles[name];st.font.size=Pt(size);st.font.bold=True
 st.element.get_or_add_rPr().get_or_add_rFonts().set(qn('w:eastAsia'),'黑体')
 st.paragraph_format.space_before=Pt(10 if name!='Title' else 0)
 st.paragraph_format.space_after=Pt(6)
 st.paragraph_format.keep_with_next=True
normal=d.styles['Normal'];normal.paragraph_format.widow_control=True
for st in d.styles:
 if st.element.pPr is not None:
  for border in list(st.element.pPr.findall(qn('w:pBdr'))):st.element.pPr.remove(border)

def p(text='',bold=False):
 q=d.add_paragraph();q.paragraph_format.alignment=WD_ALIGN_PARAGRAPH.JUSTIFY
 run=q.add_run(text);run.bold=bold
 return q
def h(text,level=1):d.add_heading(text,level=level)
def issue(code,title,where,detail,fix,grade='必须处理'):
 h(f'{code} {title}',2)
 location=p(f'定位：{where}。判定：{grade}。',True)
 location.paragraph_format.keep_with_next=True
 p(detail);p('建议：'+fix)
def table(headers,rows,widths=None):
 t=d.add_table(rows=1, cols=len(headers));t.alignment=WD_TABLE_ALIGNMENT.CENTER
 t.autofit=False
 for c,s in zip(t.rows[0].cells,headers):c.text=s
 for row in rows:
  for c,s in zip(t.add_row().cells,row):c.text=str(s)
 for ri,row in enumerate(t.rows):
  no_split=OxmlElement('w:cantSplit');row._tr.get_or_add_trPr().append(no_split)
  for j,c in enumerate(row.cells):
   if widths:c.width=Inches(widths[j])
   c.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
   tcPr=c._tc.get_or_add_tcPr()
   mar=OxmlElement('w:tcMar')
   for name in ['top','bottom','left','right']:
    q=OxmlElement('w:'+name);q.set(qn('w:w'),'70');q.set(qn('w:type'),'dxa');mar.append(q)
   tcPr.append(mar)
   borders=OxmlElement('w:tcBorders')
   for name in ['top','left','bottom','right']:
    b=OxmlElement('w:'+name);b.set(qn('w:val'),'single');b.set(qn('w:sz'),'4');b.set(qn('w:color'),'D9D9D9');borders.append(b)
   tcPr.append(borders)
   if ri==0:
    shade=OxmlElement('w:shd');shade.set(qn('w:fill'),'E8EDF2');tcPr.append(shade)
   for q in c.paragraphs:
    q.paragraph_format.space_after=Pt(2);q.paragraph_format.space_before=Pt(2)
    for run in q.runs:run.font.size=Pt(9);run.bold=(ri==0)
 repeat=OxmlElement('w:tblHeader');t.rows[0]._tr.get_or_add_trPr().append(repeat)
 d.add_paragraph().paragraph_format.space_after=Pt(0)
 return t
def link(label,url):
 q=d.add_paragraph();q.paragraph_format.space_after=Pt(3)
 rel=q.part.relate_to(url,'http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink',is_external=True)
 el=OxmlElement('w:hyperlink');el.set(qn('r:id'),rel)
 rr=OxmlElement('w:r');pr=OxmlElement('w:rPr');color=OxmlElement('w:color');color.set(qn('w:val'),'174A73');pr.append(color);rr.append(pr)
 tt=OxmlElement('w:t');tt.text=label;rr.append(tt);el.append(rr);q._p.append(el)

d.add_paragraph('会议论文模板与中英对照审查报告','Title')
p('审查日期：2026年11月20日　审查对象：英文会议稿及所附中文对照稿',True)
p('结论：英文稿的主要版式框架符合所给会议模板，核心模型、主要数字及中英文结论基本一致；但当前版本仍有明确的格式缺项和书目问题，不宜直接作为提交终稿。优先处理作者占位信息、图内字号、公式字体差异、算法及表格中的数学排版、五条文献的作者省略和文献[21]的来源链接。')
p('本次只审查并形成修改建议，没有改写两份论文，也没有调整模型、重新优化策略或新增正式实验。附件中的投稿和缴费说明仅作为资料，不构成执行授权。')

h('一 审查依据与证据范围')
p('原消息所列两份论文在检查期间已移至桌面“投稿版”文件夹。本次以该文件夹内同名文件为对象，保存核对副本及SHA-256。英文稿通过Microsoft Word只读打开并导出，实际为6页；中文稿为9页。页码均指本次导出的物理页码，英文稿本身没有显示页码。')
p('检查包含：Word页面和样式结构、实际字体与字号、段落与图表分页、18个编号公式、算法框、4幅图和3张数据表、中英文内容对应、表内算术与冻结控制数据、22条参考文献及其正文引用。英文稿6页均逐页视觉检查。文献核查主要限于出版社元数据和摘要；少量条目查看作者公开原文首页或书籍前置页，不表示22篇全文均已审读。本次未执行查重系统比对、全面新颖性检索或研究求解器重跑。')
p('格式判断同时使用会议提供的Word样稿和Checking list。二者存在差异时，以下报告分别说明：检查清单要求完整“Figure”、阿拉伯数字图表编号及上标文献引注，而通用Word样稿正文中仍写“Fig.”并示例其他格式。当前稿采用完整Figure、阿拉伯数字和上标引注，符合会议检查清单，不应因此判错。')
p('中文稿在此作为翻译依据，不以其A4单栏、中文图注或页码判定英文投稿稿不合格。会议具体名称、审稿匿名要求和独立页数收费规则未在已给材料中明确，不能据此推定。')

h('二 模板符合性核对')
table(['检查项','实测或文档证据','判断'],[
('页数','英文6页；清单要求4–20页','符合'),
('纸张与方向','Letter，8.5 × 11英寸，纵向','符合'),
('页边距','上1.905cm、下2.54cm、左右约1.575cm；与Word样稿一致','符合'),
('分栏','标题作者区域通栏，主体双栏；栏间距0.25英寸','符合'),
('标题','Times New Roman 24pt，居中，无副标题','符合'),
('正文','Times New Roman约10pt，两端对齐；首行缩进0.2英寸','符合主要设置'),
('摘要与关键词','9pt；摘要加粗，关键词加粗斜体；5个关键词','主要符合'),
('标题层级','一级罗马数字居中小型大写；二级A/B/C左对齐斜体','符合'),
('图表题注','8pt；图注在下、表题在上；Figure/Table全称，阿拉伯数字，末尾句号','符合清单'),
('公式编辑和编号','18个编号公式均为可编辑Office数学对象；编号在公式对象外侧，顺序完整','符合编辑和编号要求'),
('公式字体','实际导出出现Cambria Math；样稿指定Times New Roman或Symbol','存在明确差异，见F03'),
('参考文献引注','22条均在正文出现；正文引注均上标；顺序无缺号','符合'),
('图像分辨率','4图有效分辨率约495、660、704、487ppi，均为PNG','像素充足，字号另有问题'),
('图内语言','英文4图未发现中文字符','符合'),
('表格可编辑性','3张数据表均为Word表格；表1中的公式却是普通文本','表格符合，公式需改'),
('作者信息','仍有Author 1/2、Department、Email等占位文字','不符合终稿要求'),
('修订与批注','未发现修订插入/删除、批注、隐藏文字或失效交叉引用域','未发现此类遗留'),
('页眉页脚与页码','英文稿未添加页码，无明显多余页眉页脚文字','符合样稿不加页码的说明'),
('文献数量与时效','22条，含2024–2026年研究及必要经典方法书籍','满足数量；无需把经典来源全换新'),
('引用来源国家','[15]作者原稿首页单位覆盖中国、澳大利亚、丹麦','至少三国有证据；不等同国籍认定')
],[1.17,4.36,1.17])

h('三 需要修正的格式与低级错误')
issue('F01','作者栏仍为模板占位信息','英文第1页作者区','作者姓名、机构、城市、邮编、国家及邮箱或ORCID均仍是方括号占位信息。第一作者后的星号只占好了通讯作者标记的位置，并未形成真实通讯作者信息。','填入真实且已确认的作者顺序和单位信息，删除方括号占位说明；通讯作者按清单标星。若会议要求匿名审稿，应另依会议正式要求处理，现有材料不能证明有该要求。')
issue('F02','图内文字过小且字形不符合样稿','英文第4页Figure 1–3、第5页Figure 4','四图均缩至3.18英寸宽。图2三个子图、图3两个热图及图4四个曲线子图的数字和标签在当前栏宽下明显过小，图3尤其难以在100%阅读尺寸辨认。样稿要求图内标签使用8pt Times New Roman，当前图中文字呈无衬线字形。高像素分辨率不能弥补物理字号过小。PNG没有可供Word反查的原始字体属性，不能仅从文件精确声称其字体家族和每个标签的点数。','从原图源文件按最终版面重导出：采用Times New Roman并按最终印刷尺寸保证8pt左右标签；图2–4宜跨双栏或重新安排子图。若跨栏，不应只等比放大当前图而忽略总高和分页；需再次检查曲线、图例和热图单元数字。')
issue('F03','可编辑公式的实际字体与样稿不同','英文第2–5页公式及行内数学内容','Word导出PDF确认数学字形使用Cambria Math；Word样稿第Equations节明文指定Times New Roman或Symbol。因而不能只凭正文Times New Roman就判全文字体合格。同时会议检查清单要求公式使用MathType或Office公式编辑器，并不允许用图片解决所有公式问题。','将数学内容统一为符合要求的可编辑公式字体方案，或取得会议对Office默认Cambria Math的明确接受说明。保留编辑性和公式外编号；不能简单把公式截图或批量改为普通文本。此项是模板差异，不能在无依据时自行宣布Cambria Math已获准。')
issue('F04','算法框残留代码式数学记号','英文第3页Algorithm 1','算法框是7pt普通文字，含B_D、B_A、J_D、z_D^(0)、z_D^(m+1)、gap_D、D_i,k，以及parameters theta、stopping tolerances epsilon等写法；而正文相同对象使用数学下标、上标和希腊字母。原始XML确认算法框没有Office数学对象。这不是正确公式的显示提取损失，实际页面也显示这些字符。','把上下标和θ、ε排成规范数学记号，保持与正文一一对应；建议将算法字改为至少8pt并适当扩大框体。英文语法也可将第7行末尾冒号改为规范的“then break”。')
issue('F05','表格和题注中的容量变量没有排成下标','英文第4页Table 1、Table 2列头和Figure 3题注；第5页Figure 4与Table 3题注；图2子图标题','正文已用B的D/A下标区分攻防容量，但这些位置仍直接显示B_D或B_A。大小写与含义可理解，问题是符号外观不一致。','统一为B的D/A下标，保持符号体例；图内标题需在绘图源文件中修改，题注和表格需在Word中修改。此处无需改回中文稿的B和A，英文增加下标本身是合理的符号澄清。')
issue('F06','表1中的数学表达式并非公式对象','英文第4页Table 1','表格可编辑，但x(0)向量、α参数、成本系数连等式等均是普通文本或Unicode上下标。清单明确要求表格中的公式也由MathType或Office公式编辑器创建。','保留Word表格，将实际数学表达式逐格转为可编辑公式；不要把整张表转图。普通栏目名称和数值可以保留文字。')
issue('F07','参考文献作者省略不符合所给样稿','英文第6页文献[1]、[7]、[9]、[10]、[16]','样稿规定“Unless there are six authors or more give all authors’ names”。上述四条有5位作者、[16]有4位作者，当前均仅列前三位再加et al.，应补全。此规则针对参考文献条目，不要求把引言中的“et al.”全部展开。','按第五节已核实的完整作者表补全。[11]、[12]、[14]、[15]分别有6、7、6、6位作者，可按该样稿保留et al.。[13]人数尚未从原始记录坐实，不作确定性判错。')
issue('F08','文献21缺少DOI或来源链接','英文第6页文献[21]，中文第9页同条','该技术报告有作者、报告号和年份，但没有DOI或来源链接。清单要求每条文献均提供其一。报告真实存在，不应凭空编一个DOI。','补充可访问的报告来源链接及访问日期；可使用第五节列出的原报告扫描件，提交前实际打开确认可用。')
issue('F09','段间距与作者区字号未完整保留样稿','英文第1页作者区、摘要关键词及全文正文','与样稿逐项比较：正文直接格式段后为5.5pt，样稿6pt；摘要段后7pt，样稿10pt；关键词段后5pt，样稿6pt。作者姓名10.5pt、单位信息8.5pt，样稿对应示例为9pt，机构行使用斜体。主体字号及正文对齐并无全局性错误。','若按“严格沿用模板”提交，恢复对应样式的段间距及作者区实际示例字号和斜体。差异较小，属于排版一致性问题，不应夸大为整篇格式失效。',grade='建议按模板统一')
issue('F10','图表位置和孤行需进一步整理','英文第4页中部图1、表1、图2和表2；第4页右栏末至第5页左栏首','样稿建议图表置于栏顶或栏底，当前多处嵌于栏中；清单同时要求嵌入正文，二者可同时做到。第4页右栏最后仅留下“The API gateway serves as an attack entry point and”，后文接在第5页，形成孤行。正文段落设置关闭了widowControl。第6页右栏空白较大，但本次未发现空白页、正文截断或图表重叠。','优先调整图2–4的跨栏布局，启用合适的孤行控制，并让段落至少保留两行。最后一页双栏等高是版面改进建议，所给材料没有明确要求，不应当作硬性不合格。',grade='建议处理')

h('四 中英文准确性与术语审查')
p('总判断：英文稿不是逐句生硬翻译，主要命题和证据强度与中文基本一致。未发现把“受损比例”误译为单台服务器被攻陷概率、把开环博弈误写成Markov反馈博弈、把局部必要条件或有限偏离搜索写成全局Nash证明的情况。英文相较中文修顺了若干原稿断句，不能据此判作漏译。')
table(['概念','英文稿用法','审查意见'],[
('非零和开环微分博弈','nonzero-sum, open-loop differential game','专业且准确；作名词短语可不在differential与game间加连字符'),
('受损比例','compromised fraction','准确，优于attack probability；建议全稿保持'),
('有效传播率','effective propagation rate','准确；未误写攻击成功概率'),
('源端隔离与本地恢复','source-side isolation; local recovery','准确；图内Source isolation可统一为Source-side isolation'),
('分段常值控制','piecewise-constant controls','专业且准确'),
('交替最佳响应','alternating best responses','专业；作形容词时可用alternating-best-response或best-response，按语法处理'),
('单方偏离','unilateral deviation','准确；discovered unilateral improvement也保留了有限搜索含义'),
('SLSQP','sequential least-squares programming','通用且正确，不应误改成“sequential quadratic programming”后仍声称全称一致'),
('固定均值防御','fixed-mean defense','按文中定义可理解，但不是通用标准算法名；首次明确它是逐资产、逐动作均值常值基线'),
('累计综合防御损失','cumulative comprehensive defense loss','语义对应但较直译；可统一为total cumulative defender loss，并保持J_D定义'),
('时空可计算性','spatiotemporal computability','措辞不自然，易被理解为新的计算复杂性概念；建议描述可行时段行动计划'),
('身份认证与后台管理','identity authentication; back-end management','可接受的专业表达，无须为换词而改成另一资产名称')
],[1.35,2.38,2.97])

h('可直接采用的英文表达改进',2)
p('以下是局部建议，不代表原句均属错译；若采用，应同步检查术语和分页。')
for title,where,orig,new,why in [
('E01 标题中的资源受限表达','第1页标题','A Finite-Resource Network Defense Decision Method Based on a Nonzero-Sum Differential Game','A Resource-Constrained Network Defense Decision Method Based on a Nonzero-Sum Differential Game','finite-resource可理解；resource-constrained更常见、更直接表达约束。这是风格改进，不是现标题语法错误。'),
('E02 受损状态与决策任务的逻辑','第1页摘要','The network state is described by the compromised fraction of each asset to characterize how a defender dynamically deploys defensive resources.','Asset-level compromised fractions describe network-state evolution, while isolation and recovery controls specify the defender’s resource allocation over time.','把描述状态和选择行动的职责说清楚；中文原句本身也较绕，不应仅归咎英文。'),
('E03 逐时容量','第1页摘要、第4页实验设置','per-time capacity constraints','instantaneous capacity constraints','per-time可理解，instantaneous与连续时间模型中的瞬时约束更一致。'),
('E04 行动求解','第1页摘要、第3页算法介绍','a dynamic defense action decision algorithm','an algorithm for computing dynamic defense actions','避免名词堆叠；正式ABR-DAD名称保留，不另造新缩写。'),
('E05 理论最优响应与数值局部响应','第3页式(13)–(14)之后','SLSQP solves the single-player optimization ...','SLSQP computes local numerical responses for the constrained single-player problems; it does not guarantee the global optima in (13)–(14).','正文已区分theoretical best responses与算法框local response，补一句可让数学定义和实际求解器关系更明确。'),
('E06 模型的输入效率','第2页式(2)之后','recovery-input efficiency','recovery effectiveness coefficient','原译可理解；后一表达更直接对应恢复控制在状态方程中的作用系数。不要改成可测量的现实恢复速度。'),
('E07 不标准的可计算性措辞','第4页IV-B开头','assess spatiotemporal computability and capacity feasibility','assess whether the method produces capacity-feasible defense schedules across assets and time intervals','准确说明检验任务，不引入未定义的computability指标。'),
('E08 资源投入的收缩','第4页IV-B末尾','capacity saturation and investment contraction','binding capacity constraints and reduced late-horizon control effort','investment contraction偏经济语境；控制投入用control effort更自然。'),
('E09 表2总计标题','第4页Table 2末行','Total (network mean)','Total time-averaged resource use','这里是全网总资源占用的时间平均，不是六个资产的算术平均，避免相差六倍的理解。'),
('E10 比较结论的场景','第1页摘要和第5–6页结论','Dynamic defense achieves lower ... than both reference schemes.','In the B_D = 1.2 case, under the shared attack plan generated with G, dynamic defense yields lower cumulative weighted compromise loss and total cumulative defender loss than the two reference schemes.','比较结果来自主容量和这一共同攻击，三种容量均展示配置不能自动推为三个容量都做了同样效果比较。实际排版时B_D须用下标。'),
('E11 API缩写','第4页IV-A第一次使用API gateway','API gateway','application programming interface (API) gateway','API很常见，但样稿要求缩写首次定义；正文首次补全即可，图内保留API。'),
('E12 受损由升转降的判据','第5页IV-C','newly induced compromise pressure ... falls below the corresponding recovery effect','At the start of interval 6, the compromise inflow (1 − x_i)λ_i falls below the recovery outflow (δ_i + γ_i r_i)x_i at the gateway under all three schemes.','λ_i已被定义为pressure，真正决定导数正负的是两项状态流量；此建议让解释精确对应式(2)。正文变量应用公式编辑器。')
]:
 h(title,3);p('定位：'+where+'。')
 p('当前：'+orig);p('建议：'+new);p('理由：'+why)

h('中文原稿中已经存在的低级问题',2)
p('Z01　中文第5页4.2节有“……保护收益与行动成本的权衡这一结果体现了……”，在“权衡”后漏句号。英文分成两句，已经修正此处断句。')
p('Z02　中文第2页定义1第3项出现“U，A。分别为……”，应改为“其中U和A分别为……”。第4项“x(t)∈[0,1]ⁿ。为……”以及第5项“……。由式……”也有不当断句。英文相应句法顺畅，未造成模型含义改变。')
p('Z03　中文小标题“2.2博弈模型”“3动态防御行动求解”的编号后间隔不一致。中文图3的部分右侧资产标签贴近左侧子图边界；英文重绘后有所改善，但英文的物理字号过小仍需解决。')
p('英文容量B_D、B_A与中文B、A建立了明确对应；英文将中文表3转置为“指标×方案”，数值对应正确。这些是可接受的编辑调整，不属于翻译错误。')

h('五 参考文献逐条核查')
p('本次未发现已核实条目有DOI指向另一篇论文的明确错配。[13]官方论文记录获取不完整，应保留待核状态。未发现所访问出版社页面提示撤稿，但未进行独立完整的撤稿数据库审计，不能据此保证所有来源不存在后续更正。')
table(['编号','结果与处理','核验范围'],[
('[1]','书目信息匹配；5作者，应全列','IEEE/作者公开原文'),
('[2]','匹配；2025卷年与DOI含2024不冲突','Springer元数据和摘要'),
('[3]','匹配，2作者','作者发表目录与NSF原文记录'),
('[4]','匹配，4作者；未打开AIP全文','书目和摘要，非全文'),
('[5]','匹配；2022为正式卷期年','Wiley元数据和摘要'),
('[6]','作者年卷页DOI匹配；改用官网英文题名','期刊官网元数据和摘要'),
('[7]','2026、9、143匹配；5作者，应全列','出版社全文页面，重点核元数据和摘要'),
('[8]','匹配；2019 DOI与2020卷年无冲突','作者目录、IEEE目录及作者摘要'),
('[9]','匹配；5作者，应全列','Wiley页面，非全文深读'),
('[10]','匹配；5作者，应全列','出版社摘要、节选和作者声明'),
('[11]','匹配；6作者，可按模板用et al.','出版社元数据和摘要'),
('[12]','匹配；7作者，可用et al.','出版社元数据和摘要'),
('[13]','部分待核；期刊英文名应核为Netinfo Security','仅摘要和期刊信息，未取得官方论文原始记录'),
('[14]','匹配；6作者，可用et al.','作者团队公开记录，非全文'),
('[15]','匹配；6作者；机构来自中、澳、丹','作者机构仓储原文首页和摘要'),
('[16]','匹配；4作者，应补K. Huang','出版社元数据和摘要'),
('[17]','1999有原书版权页依据，不因网页1998机械改错','SIAM书籍前置页及出版社记录'),
('[18]','匹配，第2版2010','SIAM元数据和章节摘要'),
('[19]','1993第2版及现有作者顺序有原书依据','Springer原书标题页与版权页'),
('[20]','匹配，第2版2006','Springer元数据和目录'),
('[21]','报告真实；缺来源链接，需补','报告检索与实现者来源页；扫描件直接获取本次超时'),
('[22]','书目信息匹配；仅支持“相关迭代研究”','SIAM元数据和摘要，不是本文算法收敛证明')
],[.48,4.0,2.22])
h('需要补全的作者及书目文字',2)
for text in [
'[1] V. M. Preciado, M. Zargham, C. Enyioha, A. Jadbabaie, and G. J. Pappas.',
'[7] K. Lou, G. Zhao, J. Wang, X. Huang, and Z. Wan.',
'[9] Y. Mi, H. Zhang, H. Hu, J. Tan, and J. Wang.',
'[10] L. Tian, C. Gan, J. Lin, F. Shang, and Q. Zhu.',
'[16] Y. Qin, X. Yang, L. X. Yang, and K. Huang.',
'[6] 官网正式英文题名为“Research on defense decision optimization of mobile targets based on Markov differential game”。稿中译名含义可理解，但参考文献宜使用可检索的正式题名。',
'[13] 稿中Information Network Security为刊名直译。期刊英文名可核为Netinfo Security；该论文官方英文题名及完整作者序列仍需取原始首页确认。不要把另一篇《基于时机博弈的网络安全防御决策方法》的作者、卷页和DOI换入当前《基于时间微分博弈……》条目。',
'[17] 1999与网页1998、[19] 1993与电子重印2008均为不同出版日期口径，现稿写法有原始证据，不判为低级错误。[19]原书作者顺序Hairer、Nørsett、Wanner正确，不按网页排序误改。'
]:p(text)

h('核查来源',2)
sources=[
('[1] IEEE DOI及作者公开原文','https://www.georgejpappas.org/wp-content/uploads/2024/04/06763066.pdf'),
('[2] Springer正式页面','https://doi.org/10.1007/s10207-024-00964-3'),
('[3] NSF作者原文','https://par.nsf.gov/servlets/purl/10574678'),
('[4] 书目与摘要','https://pubmed.ncbi.nlm.nih.gov/41416673/'),
('[5] Wiley正式页面','https://onlinelibrary.wiley.com/doi/abs/10.1111/risa.13837'),
('[6] 期刊官网','https://www.arocmag.cn/abs/2023.01.0011'),
('[7] Springer正式页面','https://link.springer.com/article/10.1186/s42400-026-00577-4'),
('[8] 作者发表目录','https://yun-han.github.io/publications/'),
('[9] Wiley正式页面','https://onlinelibrary.wiley.com/doi/10.1155/2021/5594697'),
('[10] Elsevier DOI页面','https://doi.org/10.1016/j.comcom.2025.108148'),
('[11] Elsevier正式页面','https://www.sciencedirect.com/science/article/pii/S1389128623000804'),
('[12] Elsevier正式页面','https://www.sciencedirect.com/science/article/pii/S0167404823000974'),
('[13] 题名与摘要','https://www.infosecworld.cn/index.php?a=show&c=index&catid=10&id=4730&m=content'),
('[13] 万方期刊信息','https://sns.wanfangdata.com.cn/perio/xxwlaq?issueNum=1&publishYear=2022&tabId=article'),
('[14] 作者团队公开记录','https://www.vcrab.com.au/icds2020/'),
('[15] DTU机构仓储原文','https://backend.orbit.dtu.dk/ws/files/337115978/Optimal_Repair_Strategy_Against_Advanced_Persistent_Threats_Under_Time-Varying_Networks.pdf'),
('[16] Elsevier正式页面','https://www.sciencedirect.com/science/article/abs/pii/S0167404824003080'),
('[17] SIAM原书前置页','https://epubs.siam.org/doi/pdf/10.1137/1.9781611971132.fm'),
('[18] SIAM出版社记录','https://epubs.siam.org/doi/10.1137/1.9780898718577'),
('[19] Springer原书前置页','https://link.springer.com/content/pdf/bfm:978-3-540-78862-1/1'),
('[20] Springer出版社记录','https://link.springer.com/book/10.1007/978-0-387-40065-5'),
('[21] 原报告扫描件候选链接 提交前复核可访问性','https://degenerateconic.com/uploads/2018/03/DFVLR_FB_88_28.pdf'),
('[21] SLSQP实现者来源页','https://degenerateconic.com/slsqp.html'),
('[22] SIAM出版社记录','https://epubs.siam.org/doi/10.1137/18M1213701')]
for label,url in sources:link(label,url)

h('六 数值 公式与图文一致性')
p('以下为对现稿数字和既有冻结输出的核对，不是重新运行最佳响应求解器，也不是新增实验结果。')
table(['检查内容','核对结果'],[
('编号公式','(1)–(18)连续；英文主要数学关系与中文一致；行内归一化改善量分母保留了1+|J_p|，不能因纯文本提取丢失括号而误判。'),
('容量与参数','n=6、T=10、K=6、Δt=5/3、B_A=0.8及三种B_D均对应；初态、8条传播边、权重和成本未发现英译变值。'),
('主容量逐槽资源','0.843705、1.2、1.2、1.2、1.065570、0.337751与冻结控制相符；第2–4槽上限激活。'),
('另外两容量','0.6下前5槽用满，1.8下全部有余量，与冻结控制及正文相符；浮点约10^−15超出属于数值舍入。'),
('表2逐资产均值','18个均值与冻结控制逐项核对，四舍五入至6位一致。'),
('表2总计','B_D=1.2列已显示行相加为0.974503，显示总计为0.974504；未舍入值求和得到后者，是正常舍入差。建议表下注明总计按未舍入值计算，不应强改其中某行。'),
('防御分量','6资产×6时段×2动作=72；入口攻击6时段×2入口=12，计算正确。'),
('表3成本恒等式','10.945701+0=10.945701；8.580319+0.976515=9.556834；8.176990+1.149657=9.326647。'),
('损失降低百分比','相对N降低14.7916885%；相对M降低2.4086115%；写14.79%和2.41%正确。'),
('受损损失差','8.580319−8.176990=0.403329，正确；行动业务成本增加0.173142，抵消后综合损失仍降低0.230187。'),
('终端受损排序','M=0.156868，G=0.157163，G高0.000295；原稿中英文都保留M期末略优的结果。'),
('攻击下降和恢复强度','0.384142→0.139831、0.365943→0.137174；G网关末槽恢复0.080739、M常值约0.262580，均与冻结控制一致。'),
('图4交叉解释','既有数据记录网关G/M交叉约8.49189、认证约8.90035，正文t≈8.49正确；核心数据库终端G优于M，与文字相符。'),
('跨容量资源份额','API入口份额约60.09%→47.59%→44.48%；认证份额约2.16%→7.88%→9.43%，支持表2后的判断。')
],[1.46,5.24])

h('七 影响可复核性与结论解释的补充项')
issue('C01','共同攻击计划的来源应直接说明','英文第4页IV-A、第1页摘要和结论','现稿说明三个方案采用同一攻击，但未在比较定义中直接命名该攻击为G求解所得并冻结执行的攻击计划。M又由G的控制均值构造，比较具有明确条件。','加一句说明G、M、N均承受G所对应的冻结攻击计划，并在摘要或结果句附主容量条件。该比较支持时序配置效果，不能单独证明博弈求解优于所有防御方法或面对任意攻击均有优势。无需因此删掉已经正确呈现的条件性改进。',grade='建议补充，涉及结论边界')
issue('C02','停止指标给了阈值却未完整给出定义','英文第3页III-B及Algorithm 1','stat_p、dist_p、gap_p仅有名称。尚缺投影所用可行域、步长或归一化、距离范数，以及算法每轮gap与式(17)–(18)终止后多起点检查的关系。容量违反量viol被计算，但第7行没有写清它是否为单独通过条件。','按真实实现补齐定义；明确单起点停止诊断和三起点终止后复核的区别，以及容量容差/检查位置。不要把算法未实际使用的检查条件追写成已执行的停止条件。',grade='建议补充，影响重现')
issue('C03','数值诊断结果没有进入论文','英文III-B和IV-A','正文说明做多初值、约束与积分细化检查，却没有报告实际残差、退出码、多初值差异或细化误差。当前读者只能看到阈值，不能判断是否达到。项目已有2026年11月18日均匀初始化数值检验报告可作来源，但该报告的单路径停止结果不能冒充终止后的三起点复核。','添加紧凑诊断表或补充材料链接，至少给三容量的最终更新轮数、最大改善量、投影残差、响应距离、容量违反及求解器状态；三起点和积分细化结果应引用其真实文件。此建议是补报告已有证据，不是要求重跑或新增实验。',grade='建议补充，影响证据完整性')
issue('C04','随机种子和实现信息未交代','英文IV-A及III-B','随机初始化被提及，但正文没有随机种子、软件版本、运行环境或公开代码/数据获取位置。对提出算法的方法论文，重现实验输入与具体实现尤其重要。','在实验设置或补充材料加入实际版本、种子、脚本入口和完整控制/状态数据位置；运行时间若没有可靠记录则不编造。可将模型时间注明为归一化时间，不应擅加秒或分钟。',grade='建议补充，影响重现')
issue('C05','仿真定位和方法价值应保持准确','英文实验设置和结论','六资产拓扑、传播率和成本为预设归一化模型。当前没有把它写成生产云实测，这是正确的；建议直接用synthetic six-asset network减少歧义。现有M为均值常值对照、N为无防御，足以展示给定输入下的时序作用，但不能隔离ABR-DAD相对于其他强优化方法的独立收益。','保持当前问题、模型和有限比较范围，不额外声称真实部署有效性、全局最优或普遍均衡收敛。[22]的inverse-adjusted算法不能自动提供本文普通交替局部求解的收敛保证。是否增加更强基线属于后续研究设计决定，不在本次检查中代为修改。',grade='解释性提醒，不是已发现数学造假')

h('八 建议处理顺序')
p('第一步处理确定缺项：真实作者、五条完整作者列表、[21]来源链接、[6]正式题名，以及[13]刊名和待核字段。第二步处理版面：重导图2–4、统一公式和表格数学记号、算法框、变量下标，恢复模板间距并消除孤行。第三步处理措辞和证据：补共同攻击来源、诊断指标定义与已有验证结果，采用必要的英文专业表达改进。最后再次用Word导出逐页检查，确认字号、图表分页、18个公式及22条引文未因修改损坏。')
p('当前英文稿的核心模型和主要翻译无须推倒重来；需要的是有针对性的提交前修订。未核实项应保留为待核，不应为了形式整齐而编填。')

h('附录 审查记录与可复核文件')
p('输入副本、文件哈希及结构提取：本目录input、en_audit.json、zh_audit.json、template_audit.json。实际渲染及页码依据：en.pdf、zh.pdf、template.pdf及各render目录。字体与图尺寸：effective_fonts.json、en_pdf_fonts.json。算术与引文检查：checks.json。既有冻结控制的只读汇总：frozen_control_checks.json。')
p('本次检查脚本：audit_extract.py、check_details.py；运行使用当前工具环境提供的Python。Word真实分页通过render_word.ps1只读导出，关闭时未保存输入副本。未调用研究优化器。')
p('研究数据依据：paper/work_d7/results/static/B0.6、B1.2、B1.8中的G_controls.json和model.json；paper/figure_2_4_20261118中的verification.json、fig4_controls.csv及README.md；reports/均匀初始化路径_最终数值检验_20261118.md。以上材料用于核对当前稿已有数字，不替换其研究范围或批准记录。')
for label in ['en','zh','template']:
 data=json.loads((R/f'{label}_audit.json').read_text(encoding='utf-8'))
 p(label+' SHA-256：'+data['sha256'])

footer=sec.footer.paragraphs[0];footer.alignment=WD_ALIGN_PARAGRAPH.CENTER
rr=footer.add_run();rr.font.size=Pt(8)
f=OxmlElement('w:fldSimple');f.set(qn('w:instr'),'PAGE');footer._p.append(f)
dest=R/'论文模板与中英对照审查报告_20261120.docx'
d.save(dest)
print(dest)
