from pathlib import Path
import sys, json
sys.path.append(r'C:\Users\Jin\AppData\Local\Temp\codex_audit_20261117_deps')
import fitz

source=Path(sys.argv[1]).resolve()
out=source.parent/(source.stem+'_pages')
out.mkdir(exist_ok=True)
doc=fitz.open(source)
pages=[]
for i,p in enumerate(doc):
    p.get_pixmap(matrix=fitz.Matrix(1.5,1.5),alpha=False).save(out/f'page_{i+1:02d}.png')
    spans=[s for b in p.get_text('dict')['blocks'] if 'lines' in b for l in b['lines'] for s in l['spans']]
    outside=[s['text'] for s in spans if s['bbox'][0]<-1 or s['bbox'][1]<-1 or s['bbox'][2]>p.rect.width+1 or s['bbox'][3]>p.rect.height+1]
    pages.append({'page':i+1,'text_length':len(p.get_text()),'outside_page':outside})
(out/'text.txt').write_text('\n\n'.join(f'--- PAGE {i+1} ---\n'+p.get_text() for i,p in enumerate(doc)),encoding='utf-8')
(out/'geometry.json').write_text(json.dumps(pages,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'pages':len(doc),'outside_page':sum(len(p['outside_page']) for p in pages),'folder':str(out)},ensure_ascii=False))
