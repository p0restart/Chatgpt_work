from pathlib import Path
from zipfile import ZipFile
import json, hashlib, shutil
from lxml import etree

BASE = Path(__file__).resolve().parents[1]
SOURCE = Path(r'C:\Users\Jin\Downloads\网络防御决策论文_最佳响应敏感性实验最终整合包_20261116.zip')
dest = BASE / 'input' / 'sensitivity_package'
dest.mkdir(exist_ok=True)
shutil.copyfile(SOURCE, BASE / 'input' / 'sensitivity_original.zip')
manifest=[]
with ZipFile(SOURCE) as z:
    for idx, info in enumerate(z.infolist(), 1):
        if info.is_dir(): continue
        suffix = Path(info.filename).suffix
        out = dest / f'item_{idx:02d}{suffix}'
        data = z.read(info)
        out.write_bytes(data)
        manifest.append(dict(original_name=info.filename, local=out.relative_to(BASE).as_posix(),
                             size=len(data), sha256=hashlib.sha256(data).hexdigest()))
(dest / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
with ZipFile(BASE/'input'/'original.docx') as z:
    ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
        'm':'http://schemas.openxmlformats.org/officeDocument/2006/math'}
    x=etree.fromstring(z.read('word/document.xml'))
    paras=[''.join(p.xpath('.//w:t/text()|.//m:t/text()', namespaces=ns)) for p in x.xpath('//w:body/w:p', namespaces=ns)]
    (BASE/'input'/'original_docx_text.txt').write_text('\n'.join(paras),encoding='utf-8')
    for name in z.namelist():
        if name.startswith('word/media/'):
            (BASE/'input'/Path(name).name).write_bytes(z.read(name))
print(json.dumps(manifest,ensure_ascii=True,indent=2))
