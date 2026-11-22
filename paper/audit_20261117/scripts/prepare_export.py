from pathlib import Path
import re,json
import sys
BASE=Path(__file__).resolve().parents[1];ROOT=BASE.parents[1]
DEPS=Path(r'C:\Users\Jin\AppData\Local\Temp\codex_audit_20261117_deps')
sys.path.append(str(DEPS))
import md_to_word
keys=['Preciado2014','AlEiadeh2025','Paarporn2024','Chen2025','Li2023Cloud','Tian2025','Zhang2023ScaleFree','Zhang2023Potential','Sun2022','Hu2023','Lou2026','Basar1999','Betts2010','Hairer1993','Nocedal2006','Kraft1988','Caruso2020']
original_bib=ROOT/'paper/work_d7/references.bib'
bib=(original_bib if original_bib.exists() else BASE/'references.bib').read_text(encoding='utf-8')
additional_bib=r'''
@article{AlEiadeh2025,
 author={Mohammad Ryiad Al-Eiadeh and Mustafa Abdallah},
 title={{PR-DRA}: {PageRank}-based defense resource allocation methods for securing interdependent systems modeled by attack graphs},
 journal={International Journal of Information Security},year={2025},volume={24},pages={50},doi={10.1007/s10207-024-00964-3}}
@article{Chen2025,
 author={Wei Chen and Jingrui Wang and Yongxiang Xia and Zhen Wang},
 title={To protect, or to recover? The effect of defense resource allocation on network robustness},
 journal={Chaos},year={2025},volume={35},number={12},pages={123136},doi={10.1063/5.0267934}}
@book{Betts2010,
 author={John T. Betts},title={Practical Methods for Optimal Control and Estimation Using Nonlinear Programming},
 edition={2},address={Philadelphia},publisher={SIAM},year={2010},doi={10.1137/1.9780898718577}}
@article{Caruso2020,
 author={Francesco Caruso and Maria Carmela Ceparano and Jacqueline Morgan},
 title={An Inverse-Adjusted Best Response Algorithm for Nash Equilibria},
 journal={SIAM Journal on Optimization},year={2020},volume={30},number={2},pages={1638--1663},doi={10.1137/18M1213701}}
'''
if original_bib.exists():bib+=additional_bib
(BASE/'references.bib').write_text(bib,encoding='utf-8')
text=(BASE/'多资产网络防御决策论文_审计修订稿.md').read_text(encoding='utf-8')
text=text.split('# 参考文献')[0]
text=re.sub(r'!\[[^\]]*\]', '![]', text)
text=text.replace(r'\mathop{\arg\min}',r'\operatorname{argmin}').replace(r'\mathop{\arg\max}',r'\operatorname{argmax}')
# Avoid a reader edge case when an inline formula ends in an escaped brace.
text=text.replace(r'\{',r'\lbrace ').replace(r'\}',r'\rbrace')
script_letters=dict(zip('ACGJNPTU','𝒜𝒞𝒢𝒥𝒩𝒫𝒯𝒰'))
text=re.sub(r'\\mathcal\s*\{?([ACGJNPTU])\}?',lambda m:script_letters[m[1]],text)
# Keep a readable Markdown deliverable; the following source is the engine contract.
text=re.sub(r'^\# (.+)',r'%% 文档标题 \1',text,count=1)
text=text.replace('**摘要：**','%% 摘要 **摘要：**',1).replace('**关键词：**','%% 关键词 **关键词：**',1)
def eq(m):
    s=m.group(1).strip()
    num=re.search(r'\\qquad\\text\{\((\d+)\)\}',s)
    if num:s=s[:num.start()].rstrip(' .');return '$$'+s+'$$ {#eq-'+num.group(1)+'}'
    return '$$'+s+'$$'
text=re.sub(r'\$\$(.*?)\$\$',eq,text,flags=re.S)
def cite(m):
    parts=re.split(r'[,，]',m.group(1));ns=[]
    for part in parts:
        if re.search(r'[-–—]',part):
            a,b=map(int,re.split(r'[-–—]',part));ns.extend(range(a,b+1))
        else:ns.append(int(part))
    if any(n<1 or n>17 for n in ns):return m.group(0)
    return '['+'; '.join('@'+keys[n-1] for n in ns)+']'
text=re.sub(r'\[(\d+(?:[–—,-]\d+)*)\]',cite,text)
lines=[]
for line in text.splitlines():
    if re.match(r'\*\*表\d',line):line='%% 表格题注 '+line
    elif line.startswith('**图'):line='%% 图片题注 '+line
    elif line.startswith('*注：'):line='%% 表注 '+line.strip('*')
    line=line.replace('(figures/','(../figures/')
    lines.append(line)
header='---\nbibliography: ../references.bib\ncsl: chinese-gb7714-2015-numeric.csl\n---\n\n'
(BASE/'qa/paper_export.md').write_text(header+'\n'.join(lines)+'\n\n%% 参考文献标题 参考文献\n',encoding='utf-8')
fmt=(Path(md_to_word.__file__).parent/'presets/zh-academic.txt').read_text(encoding='utf-8')
fmt=fmt.replace('上2.54cm 下2.54cm 左3.18cm 右3.18cm','上2cm 下2cm 左2cm 右2cm')
fmt=fmt.replace('行距1.5倍','行距1.15倍').replace('行距1.25倍','行距1.1倍')
fmt=fmt.replace('小四','10.5pt').replace('五号','9pt').replace('小9pt','8.5pt')
fmt=fmt.replace('二号','16pt').replace('三号','13pt').replace('四号','11.5pt')
fmt=fmt.replace('段前18磅 段后12磅','段前10磅 段后5磅')
fmt=fmt.replace('段前12磅 段后6磅','段前8磅 段后4磅')
fmt=fmt.replace('段前6磅 段后6磅','段前5磅 段后4磅')
fmt=fmt.replace('悬挂缩进0.5英寸','悬挂缩进0.25英寸')
fmt=re.sub(r'^(一级标题：[^\n]*?)居中',r'\1左对齐',fmt,flags=re.M)
fmt=re.sub(r'^(表注：[^\n]*?)居中',r'\1左对齐',fmt,flags=re.M)
(BASE/'qa/format.txt').write_text(fmt,encoding='utf-8')
print('Normalized manuscript, bibliography, and A4 single-column format prepared.')
