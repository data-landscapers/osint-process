"""Fill an empty `entities:` on a minted intersection from its own cited records.
Takes the entities tagged on the page's `sources:` records, keeps those tagged by two or more of
them (or all, when the page cites only one or two), most-tagged first, capped at 12. Writes only
when `entities:` is empty. Usage: derive-entities.py <page.md> [...] [--write]"""
import io,os,re,sys,glob,collections
sys.path.insert(0,'scripts'); import vault_lib as V
W='--write' in sys.argv
RAW={os.path.splitext(f)[0]:os.path.join(d,f) for d in glob.glob('raw/*') for f in os.listdir(d) if f.endswith('.md')}
for p in [a for a in sys.argv[1:] if a.endswith('.md')]:
    t=io.open(p,encoding='utf-8',newline='').read()
    fm,_,_=V.parse_frontmatter(t)
    if fm.get('entities'): print('has entities',p); continue
    srcs=[s for s in fm.get('sources') or [] if s in RAW]
    c=collections.Counter()
    for s in srcs:
        f,_,_=V.parse_frontmatter(io.open(RAW[s],encoding='utf-8').read())
        c.update(set(f.get('entities') or []))
    floor=2 if len(srcs)>2 else 1
    ents=[e for e,n in c.most_common() if n>=floor][:12]
    print(p,len(srcs),'sources ->',ents)
    if W and ents:
        t=re.sub(r'^entities:[ \t]*\[\][ \t]*(?=\r?$)','entities: ['+', '.join('['+e+']' for e in ents)+']',t,count=1,flags=re.M)
        io.open(p,'w',encoding='utf-8',newline='').write(t)
