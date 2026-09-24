# Mint half of scripts/extract-by-place.py: regional {xxx}--{topic} pages from By place cells, and XAF cells to Key material.
# Usage: extract-by-place-mint.py <topic-slug> <Topic display name> XEA XSA ... [XAF]  (housekeeping 147)
import io,os,re,sys,glob
TOPIC=sys.argv[1]; TNAME=sys.argv[2]; DATE='2026-09-24'
REG={'XEA':('East Africa','xea'),'XSA':('Southern Africa','xsa'),'XWA':('West Africa','xwa'),'XCA':('Central Africa','xca'),'XNA':('North Africa','xna'),'XSS':('Sub-Saharan Africa','xss')}
NAMES={}
for l in io.open('lookups/countries.csv',encoding='utf-8-sig'):
    c=l.strip().split(',')
    if len(c)>=2: NAMES[c[0]]=c[1]
def prefix(code):
    # a country's slug prefix, read off its existing intersections (never guessed)
    for f in glob.glob('wiki/intersections/*--*.md'):
        tt=io.open(f,encoding='utf-8').read(600)
        if re.search(r'^place:\s*'+code+r'\s*$',tt,re.M): return os.path.basename(f).split('--')[0]
    return None
for a in sys.argv[3:]:
    if a not in REG and a not in ('XAF','XGL'):
        pre=prefix(a)
        if not pre: sys.exit('no slug prefix on file for '+a)
        REG[a]=(NAMES[a],pre)
mint=[a for a in sys.argv[3:] if a in REG]; CONT=[a for a in sys.argv[3:] if a in ('XAF','XGL')]
C=f'wiki/concepts/{TOPIC}.md'
rd=lambda p: io.open(p,encoding='utf-8',newline='').read()
def wr(p,t): io.open(p,'w',encoding='utf-8',newline='').write(t)
RAW=set(os.path.splitext(f)[0] for d in glob.glob('raw/*') for f in os.listdir(d) if f.endswith('.md'))
PLACES=set(l.split(',')[0] for l in io.open('lookups/countries.csv',encoding='utf-8-sig'))
t=rd(C); eol='\r\n' if '\r\n' in t else '\n'; L=t.split(eol)
s=next(i for i,l in enumerate(L) if l.strip()=='## By place'); e=next(i for i in range(s+1,len(L)) if L[i].startswith('## '))
def take(code):
    idx=[i for i in range(s+1,e) if L[i].startswith(f'- **[[{code}]]')]
    out=[]
    for i in idx:
        cell=[L[i]]; j=i+1
        while j<e and L[j][:1] in (' ','\t') and L[j].strip(): cell.append(L[j]); j+=1   # indented continuation only
        out.append((i,j,cell))
    return out
repl={}
tslug=TOPIC.replace('.','-')
for code in mint:
    cs=take(code); cells=[l for _,_,c in cs for l in c]; txt=eol.join(cells)
    links=list(dict.fromkeys(re.findall(r'\[\[([^\]|#]+?)(?:\|[^\]]*)?\]\]',txt)))
    src=[x for x in links if x in RAW]; places=[x for x in links if x in PLACES and x!=code]
    ents=[x for x in links if x not in RAW and x not in PLACES and '--' not in x and '.' not in x]
    name,pre=REG[code]; slug=f'{pre}--{tslug}'
    fm=['---','type: intersection',f'title: {name} × {TNAME}',f'place: {code}',f'topic: {TOPIC}',
        f"places: [{', '.join([code]+places)}]",f'topics: [{TOPIC}]',
        f"entities: [{', '.join('['+x+']' for x in ents)}]",'status: active',f'last_reviewed: {DATE}',
        f"sources: [{', '.join('['+x+']' for x in src)}]",'---','',f'# {name} × {TNAME}','',
        f'*Minted {DATE} (housekeeping) from the [[{TOPIC}]] concept page\'s *By place* index, where these cells had outgrown an index line. The cells are carried over unedited.*','',
        '## What we know','']
    wr(f'wiki/intersections/{slug}.md',eol.join(fm+cells)+eol)
    for n,(i,j,c) in enumerate(cs): repl[i]=(j,[f'- **[[{code}]] {name} — extracted in full: [[{slug}]].** *Index entry only; the page carries the material this index used to hold.*'] if n==0 else [])
    print('minted',slug,len(cells),'cells',len(src),'sources',len(ents),'entities')
moved=[]
KEY=next((l for l in L if l.startswith('## Key material')), None)
if KEY is None:
    # no *Key material* heading: the thematic section is the last one before `## By place`
    # that is not the Length review (data.statistics calls it *What matters now*)
    KEY=[l for l in L[:s] if l.startswith('## ') and not l.startswith('## Length')][-1]
KEY=KEY[3:]
LABEL={'XAF':'Africa-wide','XGL':'Global south'}
for code in CONT:
    cs=take(code); moved+=[l for _,_,c in cs for l in c]
    for n,(i,j,c) in enumerate(cs): repl[i]=(j,[f'- **[[{code}]] {LABEL[code]} — moved to *{KEY}* above**, where material that is not about one place belongs on this page; a place index is the wrong home for it.'] if n==0 else [])
out=[];i=0
while i<len(L):
    if i in repl: j,new=repl[i]; out.extend(new); i=j
    else: out.append(L[i]); i+=1
L=out
if moved:
    k=next(i for i,l in enumerate(L) if l.startswith('## '+KEY))
    k2=next(i for i in range(k+1,len(L)) if L[i].startswith('## '))
    while not L[k2-1].strip(): k2-=1
    L[k2:k2]=['',f'### {" and ".join(LABEL[c] for c in CONT)} cells moved from the *By place* index ({DATE})','']+moved
    print('moved',CONT,'cells',len(moved))
wr(C,eol.join(L))
