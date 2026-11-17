"""Rasterize the actual Word-exported PDF and check page bounds and text."""
from pathlib import Path
import sys,json,argparse
ap=argparse.ArgumentParser();ap.add_argument('--pymupdf-path',type=Path);args=ap.parse_args()
if args.pymupdf_path:sys.path.insert(0,str(args.pymupdf_path.resolve()))
import pymupdf
from PIL import Image,ImageDraw
base=Path(__file__).resolve().parent;out=base/'document_qa';out.mkdir(exist_ok=True)
doc=pymupdf.open(base/'论文终稿_中文.pdf');texts=[];issues=[]
for i,page in enumerate(doc):
    page.get_pixmap(matrix=pymupdf.Matrix(1.5,1.5)).save(out/f'page-{i+1}.png');texts.append(page.get_text())
    for b in page.get_text('blocks'):
        if b[0]<25 or b[2]>page.rect.width-25:issues.append(dict(page=i+1,type='margin',bbox=b[:4],text=b[4][:70]))
    if '\ufffd' in page.get_text():issues.append(dict(page=i+1,type='replacement_character'))
(out/'extracted_text.txt').write_text('\n\n'.join(texts),encoding='utf-8')
for k in range(0,len(doc),4):
    canvas=Image.new('RGB',(1250,1700),'#d0d0d0')
    for j in range(4):
        if k+j>=len(doc):break
        im=Image.open(out/f'page-{k+j+1}.png');im.thumbnail((610,805))
        x=(j%2)*625+(625-im.width)//2;y=(j//2)*850+30
        canvas.paste(im,(x,y));ImageDraw.Draw(canvas).text((x,y-22),f'PAGE {k+j+1}',fill='black')
    canvas.save(out/f'overview-{k//4+1}.png')
(out/'qa_summary.json').write_text(json.dumps(dict(pages=len(doc),issues=issues,renderer='Microsoft Word native PDF export; PyMuPDF rasterization. LibreOffice absent.'),ensure_ascii=False,indent=2),encoding='utf-8')
print('Pages',len(doc),'flags',issues)
