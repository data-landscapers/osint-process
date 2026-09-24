"""Housekeeping 147-style extraction: concept `## By place` cells -> {place}--{topic} pages.
Usage: extract.py <topic-slug> [--write] [--date YYYY-MM-DD]"""
import io,os,re,sys,glob,json,collections
TOPIC=sys.argv[1]; WRITE='--write' in sys.argv
DATE=next((a.split('=')[1] for a in sys.argv if a.startswith('--date=')),'2026-09-24')
CONCEPT=f'wiki/concepts/{TOPIC}.md'
def rd(p): return io.open(p,encoding='utf-8',newline='').read()
def wr(p,t): io.open(p,'w',encoding='utf-8',newline='').write(t)
names={}
for l in io.open('lookups/countries.csv',encoding='utf-8-sig'):
    c=l.strip().split(',')
    if len(c)>=2 and re.fullmatch(r'[A-Z]{3}',c[0]): names[c[0]]=c[1]
RAW=set(os.path.splitext(f)[0] for d in glob.glob('raw/*') for f in os.listdir(d) if f.endswith('.md'))
# target pages by place
pages={}
for p in glob.glob(f'wiki/intersections/*--{TOPIC.replace(".","-")}.md'):
    m=re.search(r'^place:\s*(\S+)',rd(p),re.M)
    if m: pages[m.group(1)]=p
t=rd(CONCEPT); eol='\r\n' if '\r\n' in t else '\n'
L=t.split(eol)
s=next(i for i,l in enumerate(L) if l.strip()=='## By place')
e=next(i for i in range(s+1,len(L)) if L[i].startswith('## '))
# A cell is a `- **[[` bullet plus the indented lines directly under it. Anything else in the
# section - headings, italic batch markers, notes - is a separator and is never touched: the
# first version absorbed separators into the cell above and moved them with it (job 154).
cells=[];spans=[];i=s+1
while i<e:
    if L[i].startswith('- **[['):
        j=i+1
        while j<e and L[j][:1] in (' ','\t') and L[j].strip(): j+=1
        cells.append(L[i:j]); spans.append((i,j)); i=j
    else: i+=1
def code(c): 
    m=re.match(r'- \*\*\[\[([A-Z]{3})\]\]',c[0]); return m.group(1) if m else None
def cites(txt): return [x for x in dict.fromkeys(re.findall(r'\[\[([^\]|#]+?)(?:\|[^\]]*)?\]\]',txt)) if x in RAW]
def words(txt): return len(re.findall(r'\w+',txt))
POINTER=re.compile(r'extracted in full|Index entry only')
by=collections.OrderedDict()
for c in cells: by.setdefault(code(c),[]).append(c)
report=[];moves={};mint=[];keep=[]
for pl,cs in by.items():
    txt=eol.join(eol.join(c) for c in cs)
    # a pointer is short: an "extracted … Index entry only" line that still carries a paragraph
    # of its own is content, and is checked and moved like any other cell (job 173, TCD)
    content=[c for c in cs if not (POINTER.search(c[0]) and not cites(eol.join(c)) and words(eol.join(c))<=60)]
    ctxt=eol.join(eol.join(c) for c in content)
    w=words(ctxt); n=len(cites(ctxt))
    material = w>=120 or n>=2
    if not content: report.append((pl,'already-pointer',w,n)); continue
    if not material: keep.append(pl); report.append((pl,'under-bar',w,n)); continue
    if pl not in pages: mint.append(pl); report.append((pl,'MINT',w,n)); continue
    page=rd(pages[pl])
    mv=[c for c in content if (not cites(eol.join(c))) or any(('[['+x) not in page for x in cites(eol.join(c)))]
    moves[pl]=(mv,content)
    report.append((pl,'merge',w,n,len(content),len(mv)))
for r in report: print(*r)
print('cells',len(cells),'places',len(by),'merge',len(moves),'mint',mint,'under',keep)
json.dump({'mint':mint,'keep':keep},open(os.path.join(os.environ.get('TEMP','.'),f'{TOPIC}.plan.json'),'w'))
if not WRITE: sys.exit()
# --- write merges
lost=[]
for pl,(mv,content) in moves.items():
    p=pages[pl]; pt=rd(p); pe='\r\n' if '\r\n' in pt else '\n'
    if mv:
        block=pe.join(pe.join(c) for c in mv)
        pt=pt.rstrip('\r\n')+pe+pe+f'## Extracted from [[{TOPIC}]] → By place ({DATE})'+pe+pe+f'*Moved whole from the concept page\'s index, unedited, because this page did not yet carry it.*'+pe+pe+block+pe
        new=[x for c in mv for x in cites(eol.join(c))]
        m=re.search(r'^sources:[ \t]*\[(.*)\][ \t]*$',pt,re.M)
        if m:
            have=set(re.findall(r'\[([^\[\]]+)\]',m.group(1)))
            add=[x for x in dict.fromkeys(new) if x not in have]
            if add:
                inner=m.group(1).strip()
                inner=(inner+', ' if inner else '')+', '.join('['+x+']' for x in add)
                pt=pt[:m.start()]+'sources: ['+inner+']'+pt[m.end():]
        wr(p,pt)
    pt=rd(p)
    for c in content:
        for x in cites(eol.join(c)):
            if '[['+x not in pt: lost.append((pl,x))
print('lost citations:',lost)
# --- rewrite in place: a merged place's first cell becomes the pointer, its other cells go
slug=lambda pl: os.path.splitext(os.path.basename(pages[pl]))[0]
seen=set();out=[];k=0
span_of={sp[0]:(sp,c) for sp,c in zip(spans,cells)}
i=0
while i<len(L):
    if i in span_of:
        (a,b),c=span_of[i]; pl=code(c)
        if pl in moves:
            if pl not in seen:
                out.append(f'- **[[{pl}]] {names.get(pl,pl)} — extracted in full: [[{slug(pl)}]].** *Index entry only; the page carries the material this index used to hold.*')
                seen.add(pl)
            i=b; continue
        out.extend(L[a:b]); i=b; continue
    out.append(L[i]); i+=1
wr(CONCEPT,eol.join(out))
