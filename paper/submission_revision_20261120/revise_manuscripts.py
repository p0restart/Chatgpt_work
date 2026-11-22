"""Apply the verified editorial changes to LaTeX and the retained Word layout."""
from pathlib import Path
from copy import deepcopy
import json,re,sys
from lxml import etree as E
from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches,Pt
from docx.text.paragraph import Paragraph
from docx.enum.text import WD_ALIGN_PARAGRAPH
R=Path(__file__).resolve().parent
sys.path.append(str(R/'qa/math_deps'))
from latex2mathml.converter import convert
XSL=E.XSLT(E.parse(r'C:/Program Files/Microsoft Office/root/Office16/MML2OMML.XSL'))
oldtex=(R/'original_latex/main.tex').read_text(encoding='utf-8')
tex=oldtex
changes=[]
def swap(a,b,required=True):
 global tex
 if a not in tex:
  if required:raise ValueError('Missing source: '+a[:90])
  return
 tex=tex.replace(a,b);changes.append((a,b))

swap('A Finite-Resource Network Defense Decision Method','A Resource-Constrained Network Defense Decision Method')
swap('The network state is described by the compromised fraction of each asset to characterize how a defender dynamically deploys defensive resources.',
     'Asset-level compromised fractions describe network-state evolution, while isolation and recovery controls specify the defender\'s resource allocation over time.')
swap('a dynamic defense action decision algorithm (ABR-DAD) is developed',
     'Alternating Best Response for Dynamic Defense Action Decision (ABR-DAD) is developed')
swap('per-time capacity constraint','instantaneous capacity constraint')
swap('Dynamic defense achieves lower cumulative weighted compromise loss and cumulative comprehensive defense loss than both reference schemes, demonstrating the effectiveness of the method for calculating dynamic defensive actions under finite resources.',
     'In the main-capacity comparison under the shared attack plan generated with dynamic defense, the dynamic plan reduces cumulative weighted compromise loss and total cumulative defender loss relative to both reference schemes. These results support the method for computing defense schedules under finite resources.')
swap('recovery-input efficiency','recovery effectiveness coefficient')
swap('cumulative comprehensive defense loss','total cumulative defender loss')
swap('Cumulative comprehensive defense loss','Total cumulative defender loss')
swap('cumulative comprehensive loss','total cumulative loss')
swap('instantaneous comprehensive loss','instantaneous total loss')
swap('overall comprehensive loss','total cumulative loss')
swap('comprehensive defense losses','total defender losses')
swap('comprehensive defense loss','total defender loss',False)
swap('compromise and comprehensive defense losses','compromise and total defender losses',False)
swap('assess spatiotemporal computability and capacity feasibility','assess whether the method produces capacity-feasible defense schedules across assets and time intervals')
swap('both capacity saturation and investment contraction','both binding capacity constraints and reduced late-horizon control effort')
swap('Total (network mean)','Total (time mean)')
swap('The simulation employs preset directed propagation parameters, with normalized model intensities and costs.',
     r'This is a synthetic six-asset network with preset propagation parameters and normalized time, control intensities, and costs. Table~\ref{tab:params} summarizes the simulation parameters.')
swap('The nodes are $v_1$: API gateway,','The nodes are $v_1$: application programming interface (API) gateway,')
swap('are compared under the same attack-control trajectory. G is',
     'are compared under the attack-control trajectory computed jointly with G and then held fixed for all three schemes. G is')
swap('Under all three schemes, newly induced compromise pressure on the gateway falls below the corresponding recovery effect, changing its compromised fraction from increasing to decreasing.',
     r'Under all three schemes, the compromise inflow $(1-x_1)\lambda_1$ falls below the recovery outflow $(\delta_1+\gamma_1r_1)x_1$, so the gateway compromised fraction changes from increasing to decreasing.')
swap('Under the same attack sequence, dynamic defense reduces',
     'At the main defense capacity, under the shared attack plan generated with G, dynamic defense reduces')
swap('sequential least-squares programming (SLSQP) solves the single-player optimization with control bounds and linear capacity constraints',
     'sequential least-squares programming (SLSQP) computes local numerical responses under control bounds and linear capacity constraints')
swap('The plans are then updated alternately.',
     r'These local responses approximate the theoretical best-response problems in \eqref{eq:BRD}--\eqref{eq:BRA}. The plans are then updated alternately.')

# Verified bibliography corrections. Retain the unresolved r13 author list.
for a,b in [
 (r'V. M. Preciado, M. Zargham, C. Enyioha, \emph{et al.},',r'V. M. Preciado, M. Zargham, C. Enyioha, A. Jadbabaie, and G. J. Pappas,'),
 (r'K. Lou, G. Zhao, J. Wang, \emph{et al.},',r'K. Lou, G. Zhao, J. Wang, X. Huang, and Z. Wan,'),
 (r'Y. Mi, H. Zhang, H. Hu, \emph{et al.},',r'Y. Mi, H. Zhang, H. Hu, J. Tan, and J. Wang,'),
 (r'L. Tian, C. Gan, J. Lin, \emph{et al.},',r'L. Tian, C. Gan, J. Lin, F. Shang, and Q. Zhu,'),
 (r'Y. Qin, X. Yang, L. X. Yang, \emph{et al.},',r'Y. Qin, X. Yang, L. X. Yang, and K. Huang,'),
 ('Moving-target defense decision optimization based on Markov differential games','Research on defense decision optimization of mobile targets based on Markov differential game'),
 ('Information Network Security','Netinfo Security'),
 (r'Versuchsanstalt f\"ur Luft- und Raumfahrt, 1988.',r'Versuchsanstalt f\"ur Luft- und Raumfahrt, 1988. [Online]. Available: \url{https://degenerateconic.com/slsqp.html}.')
]:swap(a,b)

diagnostic_definition=r'''For the stopping diagnostics, write $F_D=J_D$ and $F_A=-J_A$, with the opponent's plan fixed. Let $\widetilde z_p$ be the numerical unilateral response and let $\mathcal C_D=U_K$ and $\mathcal C_A=A_K$. The discovered improvement is $gap_p=\max\{0,F_p(z_p)-F_p(\widetilde z_p)\}$. We use the unit-step projected-gradient residual $stat_p=\|z_p-\Pi_{\mathcal C_p}(z_p-\nabla F_p(z_p))\|_\infty$ and the response distance $dist_p=\|\widetilde z_p-z_p\|_\infty$, where $\Pi$ is Euclidean projection onto the bounded, capacity-constrained feasible set. Response candidates are accepted only if their bound and capacity violations are at most $10^{-10}$. The single-start checks used for stopping are distinct from the three-start searches performed after termination.'''
anchor='The defender then obtains an isolation and recovery plan by asset and interval.'
swap(anchor,'\n\n'+diagnostic_definition+'\n\n'+anchor)
env=r'''The archived optimization used Python 3.11.7, NumPy 1.26.4, and SciPy 1.11.4 on Windows. The base random seeds were 20262114, 20261114, and 20263114 for capacities 0.6, 1.2, and 1.8, respectively; the random full-run initialization used the corresponding base seed plus two. The uniform-start plan was selected for reporting. Saved controls, trajectories, diagnostic records, and figure-generation inputs accompany the manuscript source.'''
validation=r'''All three uniform-start paths first met the stopping criteria after five alternating updates. Across the three capacities and both players, the normalized discovered improvement, current-plan projected residual, and response distance did not exceed $2.90\times10^{-10}$, $6.48\times10^{-5}$, and $3.35\times10^{-5}$, respectively; all final single-start SLSQP exit codes were zero. The largest control difference between full-run initializations was below $4.02\times10^{-5}$. Separate three-start checks of the final reported plans also passed the stated local criteria. For the three main-capacity comparison plans, increasing RK4 substeps per control interval from 48 to 192 changed shared-time states by at most $8.71\times10^{-12}$. These are numerical diagnostics within the specified strategy class.'''
setup_end=r'Capacities $B_D=0.6$ and $1.8$ are used to illustrate resource allocation under varying capacity.'
swap(setup_end,setup_end+'\n\n'+env+'\n\n'+validation)

# Typography and float sizes. The provided author block remains for manual completion.
swap(r'\documentclass[conference,letterpaper]{IEEEtran}',r'\RequirePackage[T1]{fontenc}'+'\n'+r'\documentclass[conference,letterpaper]{IEEEtran}')
swap(r'\usepackage[T1]{fontenc}'+'\n'+r'\usepackage{newtxtext,newtxmath}',r'''\usepackage{iftex}
\ifPDFTeX
  \usepackage[T1]{fontenc}
  \usepackage{newtxtext,newtxmath}
\else
  \usepackage{newtxtext,newtxmath}
  \AtBeginDocument{\defaultfontfeatures{}\setmainfont{Times New Roman}}
\fi''')
swap(r'\usepackage[super]{cite}',r'\usepackage[super,nomove]{cite}')
swap(r'\def\fnum@figure{Figure~\thefigure.}',r'''\def\fnum@figure{Figure~\thefigure}
\def\@citess#1{\mbox{\textsuperscript{\OverciteFont{[#1]}}}}
\renewcommand{\IEEEkeywordsname}{Keywords}''')
swap(r'\begin{thebibliography}{22}',r'\IEEEtriggeratref{19}'+'\n'+r'\begin{thebibliography}{22}'+'\n'+r'\interlinepenalty=10000')
swap(r'{\scriptsize'+'\n'+r'\textbf{Input:}',r'{\footnotesize'+'\n'+r'\textbf{Input:}')
swap(r'\centering\scriptsize\renewcommand',r'\centering\footnotesize\renewcommand')
for number,name in [(1,'network'),(2,'capacity'),(3,'actions'),(4,'states')]:
 if number==1:
  swap(r'\includegraphics[width=.98\columnwidth]{fig1_network_en.png}',r'\includegraphics[width=3.18in]{fig1_network_en.pdf}')
 else:
  pattern=r'\\begin\{figure\}\[[^\]]*\]\s*\\centering\\includegraphics\[width=\.98\\columnwidth\]\{fig'+str(number)+r'_[^}]+\.png\}.*?\\end\{figure\}'
  match=re.search(pattern,tex,re.S)
  if not match:raise ValueError('figure not found '+str(number))
  block=match.group().replace(r'\begin{figure}',r'\begin{figure*}').replace(r'\end{figure}',r'\end{figure*}')
  block=re.sub(r'\[[!a-z]+\]',r'[!t]',block,count=1)
  block=block.replace(r'width=.98\columnwidth',r'width=6.76in').replace('.png}', '.pdf}')
  tex=tex[:match.start()]+block+tex[match.end():]
swap(r'\begin{tabular}{@{}p{1.55in}rrr@{}}',r'\setlength{\tabcolsep}{3pt}'+'\n'+r'\begin{tabularx}{\columnwidth}{@{}Xrrr@{}}')
# Only the effectiveness table uses the preceding tabularx change.
effects_start=tex.index(r'\caption{Three effectiveness metrics')
effects_end=tex.index(r'\end{table}',effects_start)
segment=tex[effects_start:effects_end].replace(r'\end{tabular}',r'\end{tabularx}')
tex=tex[:effects_start]+segment+tex[effects_end:]
note=r'\par\vspace{2pt}{\footnotesize Totals are computed before rounding.}'
asset_start=tex.index(r'\caption{Mean defensive resource use')
asset_end=tex.index(r'\end{table}',asset_start)
tex=tex[:asset_end]+note+'\n'+tex[asset_end:]
(R/'latex/main.tex').write_text(tex,encoding='utf-8')

# Retained Word layout: edit content from the same revised LaTeX paragraphs.
doc=Document(R/'word_original.docx')
original_paragraphs=list(doc.paragraphs)
labels={label:i+1 for i,label in enumerate(re.findall(r'\\begin\{equation\}\\label\{([^}]+)\}',oldtex))}
figrefs={'network':1,'capacity':2,'actions':3,'states':4};tabrefs={'params':1,'asset':2,'effects':3}
def textclean(s):
 s=s.replace('---','—').replace('--','–').replace("``",'“').replace("''",'”').replace("'",'’').replace('~',' ')
 s=s.replace(r'\%', '%').replace(r'\&','&').replace(r'\quad',' ')
 s=s.replace(r'Ba\c{s}ar','Başar').replace(r'N\o rsett','Nørsett').replace(r'f\"ur','für')
 return s
def math(texcode,size=None):
 mm=convert(texcode)
 result=XSL(E.fromstring(mm.encode('utf-8')))
 el=deepcopy(result.getroot())
 if E.QName(el).localname=='oMathPara':el=deepcopy(el.find(qn('m:oMath')))
 if size:
  for r in el.iter(qn('m:r')):
   rp=r.find(qn('w:rPr'))
   if rp is None:rp=OxmlElement('w:rPr');r.insert(0,rp)
   sz=rp.find(qn('w:sz'))
   if sz is None:sz=OxmlElement('w:sz');rp.append(sz)
   sz.set(qn('w:val'),str(round(size*2)))
 return el
def fill(p,s,size=None):
 for ch in list(p._p):
  if ch.tag!=qn('w:pPr'):p._p.remove(ch)
 s=re.sub(r'\\eqref\{([^}]+)\}',lambda m:'('+str(labels[m[1]])+')',s)
 s=re.sub(r'\\ref\{fig:([^}]+)\}',lambda m:str(figrefs[m[1]]),s)
 s=re.sub(r'\\ref\{tab:([^}]+)\}',lambda m:str(tabrefs[m[1]]),s)
 # Formatting wrappers in these paper paragraphs are single-level.
 s=re.sub(r'\\url\{([^}]+)\}',r'\1',s)
 tokens=re.split(r'(\$[^$]+\$|\\cite\{[^}]+\}|\\(?:emph|textbf)\{[^{}]*\})',s)
 for token in tokens:
  if not token:continue
  if token.startswith('$'):
   p._p.append(math(token[1:-1],size))
  elif token.startswith(r'\cite'):
   nums=','.join(x[1:] for x in re.search(r'\{([^}]+)\}',token)[1].split(','))
   run=p.add_run('['+nums+']');run.font.superscript=True
  elif token.startswith((r'\emph',r'\textbf')):
   run=p.add_run(textclean(re.search(r'\{(.*)\}',token)[1]));run.font.name='Times New Roman'
   run.italic=token.startswith(r'\emph');run.bold=token.startswith(r'\textbf')
   if size:run.font.size=Pt(size)
  else:
   run=p.add_run(textclean(token));run.font.name='Times New Roman'
   if size:run.font.size=Pt(size)
 return p
def matching(needle):
 for p in original_paragraphs:
  if needle.startswith('['):
   if p.text.startswith(needle):return p
   continue
  alltext=''.join(p._p.itertext())
  if needle in p.text or needle in alltext:return p
 raise ValueError('Word paragraph not found '+needle)
def texpara(starts):
 for para in tex.splitlines():
  if para.startswith(starts):return para.strip()
 raise ValueError('TeX paragraph not found '+starts)

# Short replacements safe across existing plain text runs.
for para in doc.paragraphs:
 for run in para.runs:
  t=run.text
  for a,b in [
   ('A Finite-Resource Network Defense Decision Method','A Resource-Constrained Network Defense Decision Method'),
   ('recovery-input efficiency','recovery effectiveness coefficient'),
   ('cumulative comprehensive defense loss','total cumulative defender loss'),
   ('Cumulative comprehensive defense loss','Total cumulative defender loss'),
   ('cumulative comprehensive loss','total cumulative loss'),
   ('instantaneous comprehensive loss','instantaneous total loss'),
   ('overall comprehensive loss','total cumulative loss'),
   ('comprehensive defense losses','total defender losses'),
   ('comprehensive defense loss','total defender loss'),
   ('per-time capacity constraint','instantaneous capacity constraint'),
   ('Information Network Security','Netinfo Security')]:t=t.replace(a,b)
  if t!=run.text:run.text=t

# Changed multi-run paragraphs are reconstructed with native editable equations.
abstract=re.search(r'\\begin\{abstract\}\s*(.*?)\s*\\end\{abstract\}',tex,re.S)[1]
pa=matching('Abstract—');fill(pa,'Abstract—'+abstract)
for run in pa.runs:run.bold=True;run.italic=False;run.font.size=Pt(9)
pa.runs[0].text=pa.runs[0].text[len('Abstract—'):]
labelrun=pa.add_run('Abstract—');labelrun.bold=True;labelrun.italic=True;labelrun.font.size=Pt(9)
pa._p.insert(1 if pa._p.pPr is not None else 0,labelrun._r)
for needle,starts in [
 ('are candidate defender and attacker plans','Here $v$ and $b$ are candidate'),
 ('A directed multi-asset attack-propagation network is constructed','A directed multi-asset attack-propagation network is constructed'),
 ('For main capacity','For main capacity'),
 ('The experiment first reports','The experiment first reports'),
 ('Figure\u00a04 shows','Figure~\\ref{fig:states} shows'),
 ('This paper establishes a nonzero-sum','This paper establishes a nonzero-sum')
]:fill(matching(needle),texpara(starts))
stop=matching('The maximum number of alternating iterations')
stop_tex=texpara('The maximum number of alternating iterations')
# The inserted definition splits the old paragraph; retain its final lead-in.
fill(stop,stop_tex)
newp=Paragraph(OxmlElement('w:p'),doc._body);stop._p.addnext(newp._p);newp.style='Body Text';fill(newp,diagnostic_definition)
lead=Paragraph(OxmlElement('w:p'),doc._body);newp._p.addnext(lead._p);lead.style='Body Text'
fill(lead,'The defender then obtains an isolation and recovery plan by asset and interval. For asset $i$ and interval $k$,')
setup=matching('For main capacity')
last=setup
for body in [env,validation]:
 npg=Paragraph(OxmlElement('w:p'),doc._body);last._p.addnext(npg._p);npg.style='Body Text';fill(npg,body);last=npg

# Replace verified bibliography entries as whole paragraphs.
for i in [1,6,7,9,10,13,16,21]:
 entry=re.search(r'\\bibitem\{r'+str(i)+r'\}\s*(.*?)(?=\n\\bibitem|\n\\end\{thebibliography\})',tex,re.S)[1].strip()
 fill(matching('['+str(i)+'] '),'['+str(i)+'] '+entry,size=8)

# The paper's captions already use the correct styles; replace literal B_D.
for p in doc.paragraphs:
 if p.style.name in ['figure caption','table head'] and 'B_D' in p.text:
  fill(p,p.text.replace('B_D',r'$B_D$'))

tables=list(doc.tables)
for table in tables:
 for row in table.rows:
  for cell in row.cells:
   for p in cell.paragraphs:
    for run in p.runs:
     run.text=run.text.replace('Cum. comprehensive defense loss','Total cumulative defender loss')
# Parameter expressions become native mathematical objects.
params=[
 r'$n=6$; $T=10$; $K=6$; $\Delta t=5/3$',
 r'$x(0)=(0.1,0,0,0,0,0)$; $B_A=0.8$',
 r'$B_D\in\{0.6,1.2,1.8\}$; main case $B_D=1.2$',
 r'$\alpha_1=\alpha_2=0.25$, other $\alpha_i=0$; $\varepsilon_i=1$',
 r'$\delta_i=0.1$; $\gamma_i=0.3$; $q=(1,1,1,1,4,1)$; $g_i=1$',
 r'$h_i=0.05$; $c_i^s=c_i^r=c_i^a=1$; $b_i^s=b_i^r=d_i^a=1$; $\omega=\nu=0$']
for row,content in zip(tables[13].rows[1:],params):fill(row.cells[1].paragraphs[0],content,size=8)
for i,b in enumerate([.6,1.2,1.8],1):fill(tables[15].rows[0].cells[i].paragraphs[0],f'$B_D={b:.1f}$',size=8)
tables[15].rows[-1].cells[0].text='Total (time mean)'
effect_widths=[1.44,.68,.68,.68]
tables[18].autofit=False
for col,width in zip(tables[18].columns,effect_widths):col.width=Inches(width)
for row in tables[18].rows:
 for cell,width in zip(row.cells,effect_widths):
  cell.width=Inches(width)
  margins=OxmlElement('w:tcMar')
  for side in ['left','right']:
   margin=OxmlElement('w:'+side);margin.set(qn('w:w'),'45');margin.set(qn('w:type'),'dxa');margins.append(margin)
  cell._tc.get_or_add_tcPr().append(margins)
  for p in cell.paragraphs:p.paragraph_format.keep_together=True
effect_total=tables[18]._tbl.tblPr.find(qn('w:tblW'));effect_total.set(qn('w:w'),str(round(sum(effect_widths)*1440)));effect_total.set(qn('w:type'),'dxa')
for table in tables:
 for row in table.rows:
  pr=row._tr.get_or_add_trPr()
  if pr.find(qn('w:cantSplit')) is None:pr.append(OxmlElement('w:cantSplit'))
  for cell in row.cells:
   for p in cell.paragraphs:
    for run in p.runs:
     if table in [tables[13],tables[15],tables[18]]:run.font.size=Pt(8)
notepar=Paragraph(OxmlElement('w:p'),doc._body);tables[15]._tbl.addnext(notepar._p)
notepar.style='Normal';fill(notepar,'Totals are computed before rounding.',size=8)

# Rebuild the pseudocode using native Office math, all at 8pt.
cell=tables[9].cell(0,0)
for ch in list(cell._tc):
 if ch.tag!=qn('w:tcPr'):cell._tc.remove(ch)
algo=[
 'Algorithm 1. Alternating Best Response for Dynamic Defense Action Decision (ABR-DAD)',
 r'Input: $\mathcal G,x_0,T,K,B_D,B_A$, parameters $\theta$, tolerances $\epsilon$, iteration limit $M$.',
 r'Output: actions $D$, resource use $R$, final plans, $J_D$, diagnostics.',
 r'1  Initialize feasible $z_D^{(0)},z_A^{(0)}$.',
 r'2  for $m=0,1,\ldots,M-1$ do',
 r'3  Fix $z_A^{(m)}$; use RK4 and SLSQP to compute local defender response $z_D^{(m+1)}$.',
 r'4  Fix $z_D^{(m+1)}$; compute local attacker response $z_A^{(m+1)}$.',
 r'5  Test single-start deviations; compute $gap_D,gap_A$.',
 r'6  Compute $stat_p$, $dist_p$, and capacity violation.',
 r'7  if both diagnostic SLSQP runs exit normally and all three stopping metrics pass then break.',
 r'8  end for',
 r'9  Run three-start checks and integration refinement; form $D_{i,k},R_{i,k}$.',
 r'10 Return $D,R$, final plans, $J_D$, and diagnostics.'
]
for i,line in enumerate(algo):
 p=cell.add_paragraph();p.style='Normal';p.paragraph_format.space_after=Pt(1);fill(p,line,size=8)
 p.paragraph_format.alignment=WD_ALIGN_PARAGRAPH.LEFT;p.paragraph_format.first_line_indent=Pt(0);p.paragraph_format.line_spacing=1.0
 if i==0:
  for run in p.runs:run.bold=True

# Replace all four image assets and use continuous full-width sections for 2--4.
figtables=[tables[12],tables[14],tables[16],tables[17]]
fignames=['fig1_network_en','fig2_capacity_en','fig3_actions_en','fig4_states_en']
for i,(table,name) in enumerate(zip(figtables,fignames),1):
 p=table.cell(0,0).paragraphs[0]
 for ch in list(p._p):
  if ch.tag!=qn('w:pPr'):p._p.remove(ch)
 p.add_run().add_picture(str(R/f'latex/figures/{name}.png'),width=Inches(3.18 if i==1 else 6.76))
 table.autofit=False
 w=Inches(3.18 if i==1 else 6.76)
 table.columns[0].width=w;table.cell(0,0).width=w
 pr=table._tbl.tblPr
 width=pr.find(qn('w:tblW'));width.set(qn('w:w'),str(int(w/635)));width.set(qn('w:type'),'dxa')
 if i>1:
  before=OxmlElement('w:p');table._tbl.addprevious(before)
  sep=Paragraph(before,doc._body);sep.paragraph_format.space_before=Pt(0);sep.paragraph_format.space_after=Pt(0);sep.paragraph_format.line_spacing=Pt(1)
  sep.add_run().font.size=Pt(1)
  caption=table._tbl.getnext()
  if caption.tag!=qn('w:p'):raise ValueError('Missing figure caption')
  for para,cols in [(before,2),(caption,1)]:
   pp=para.find(qn('w:pPr'))
   if pp is None:pp=OxmlElement('w:pPr');para.insert(0,pp)
   old=pp.find(qn('w:sectPr'))
   if old is not None:pp.remove(old)
   section=deepcopy(doc.sections[-1]._sectPr)
   for tag in ['w:headerReference','w:footerReference']:
    for x in list(section.findall(qn(tag))):section.remove(x)
   typ=section.find(qn('w:type'))
   if typ is None:typ=OxmlElement('w:type');section.insert(0,typ)
   typ.set(qn('w:val'),'continuous')
   columns=section.find(qn('w:cols'));columns.set(qn('w:num'),str(cols));columns.set(qn('w:space'),'360')
   pp.append(section)
  # Leave subsequent body text separate from the span.
  Paragraph(caption,doc._body).paragraph_format.keep_with_next=False

# Restore template spacing and prevent isolated lines.
for p in doc.paragraphs:
 if p.style.name=='Body Text':
  p.paragraph_format.space_after=Pt(6);p.paragraph_format.widow_control=True
 if p.style.name=='Abstract':p.paragraph_format.space_after=Pt(10)
 if p.style.name=='Keywords':p.paragraph_format.space_after=Pt(6)
 if p.style.name in ['figure caption','table head']:
  for run in p.runs:run.font.size=Pt(8)
 if p.style.name=='references':p.paragraph_format.space_after=Pt(0)
for cell in tables[0].rows[0].cells:
 for pi,p in enumerate(cell.paragraphs):
  for run in p.runs:run.font.size=Pt(9);run.italic=(pi in [1,2])
for p in doc.element.xpath('.//w:p'):
 # Body spelling language is English; no invented author information.
 for lang in p.xpath('.//w:lang'):
  lang.set(qn('w:val'),'en-US')

out=R/'Network_Defense_Revised.docx';doc.save(out)
(R/'editorial_changes.json').write_text(json.dumps(changes,ensure_ascii=False,indent=2),encoding='utf-8')
final_tex=(R/'latex/main.tex').read_text(encoding='utf-8')
final_tex=re.sub(r'(\$[0-9.]+\\times10\^\{-[0-9]+\}\$)',lambda m:r'\mbox{'+m[1]+'}',final_tex)
(R/'latex/main.tex').write_text(final_tex,encoding='utf-8')
print('Revised LaTeX and Word manuscripts')
