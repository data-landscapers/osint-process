"""Link a minted {place}--{topic} page from its place hub (housekeeping By place extractions).
Appends `(+ [[page]])` to the hub's existing `- [[topic]]` line; failing that, adds a bullet
after the hub's last topic bullet, or at the end of its `## Active topics` list.
Usage: link-minted-hub.py <topic-slug> <DATE> CODE:page [CODE:page ...]"""
import io,re,sys
topic,date=sys.argv[1],sys.argv[2]
for arg in sys.argv[3:]:
    code,page=arg.split(':')
    p=f'wiki/places/{code}.md'; t=io.open(p,encoding='utf-8',newline='').read()
    eol='\r\n' if '\r\n' in t else '\n'
    if f'[[{page}]]' in t: print('already',code); continue
    m=re.search(r'^(- \[\['+re.escape(topic)+r'\]\].*?)(\r?)$',t,re.M)
    if m:
        t=t[:m.start()]+m.group(1)+f' (+ [[{page}]])'+m.group(2)+t[m.end():]
    else:
        ms=list(re.finditer(r'^- \[\[[a-z]+\.[a-z]+\]\][^\r\n]*',t,re.M))
        a=re.search(r'^## Active topics\s*$',t,re.M)
        if not ms and not a:
            # a thin hub with no topic list at all: open an Active topics section for it,
            # before Entities / Notes / Related if it has one, else at the end
            anchor=re.search(r'^## (Entities|Notes|Related)\b',t,re.M)
            pt=io.open(f'wiki/intersections/{page}.md',encoding='utf-8').read()
            name=re.search(r'^title:\s*"?[^×]*× ([^"\r\n]*)',pt,re.M).group(1).strip()
            sec=f"## Active topics{eol}{eol}- **{name}** → **[[{page}]]** — extracted from [[{topic}]]'s place index {date}.{eol}"
            if anchor: t=t[:anchor.start()]+sec+eol+t[anchor.start():]
            else: t=t.rstrip('\r\n')+eol+eol+sec
            io.open(p,'w',encoding='utf-8',newline='').write(t); print('linked',code); continue
        if not ms and a:
            nxt=re.search(r'^## ',t[a.end():],re.M); sec_end=a.end()+(nxt.start() if nxt else len(t)-a.end())
            bl=list(re.finditer(r'^- [^\r\n]*',t[a.end():sec_end],re.M))
            j=a.end()+bl[-1].end() if bl else a.end()
            pt=io.open(f'wiki/intersections/{page}.md',encoding='utf-8').read()
            name=re.search(r'^title:\s*"?[^×]*× ([^"\r\n]*)',pt,re.M).group(1).strip()
            t=t[:j]+eol+f"- **{name}** → **[[{page}]]** — extracted from [[{topic}]]'s place index {date}."+t[j:]
            io.open(p,'w',encoding='utf-8',newline='').write(t); print('linked',code); continue
        if not ms: print('NO topic list',code); continue
        j=ms[-1].end()
        t=t[:j]+eol+f'- [[{topic}]] — the place material is at [[{page}]] (extracted from [[{topic}]] {date}).'+t[j:]
    io.open(p,'w',encoding='utf-8',newline='').write(t); print('linked',code)
