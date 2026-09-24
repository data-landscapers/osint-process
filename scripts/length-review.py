"""Replace a concept page's `## Length — reviewed …` section with a new dated review.
Usage: length-review.py <topic-slug> <YYYY-MM-DD> <file holding the review body, one paragraph per line>"""
import io,re,sys
topic,date,src=sys.argv[1:4]
p=f'wiki/concepts/{topic}.md'; t=io.open(p,encoding='utf-8',newline='').read(); eol='\r\n' if '\r\n' in t else '\n'
s=re.search(r'^## Length — reviewed .*$',t,re.M); e=re.search(r'^## ',t[s.end():],re.M)
paras=[l.strip() for l in io.open(src,encoding='utf-8').read().splitlines() if l.strip()]
new=f'## Length — reviewed {date}'+eol+eol+(eol+eol).join(paras)+eol+eol
end=s.end()+e.start() if e else len(t)   # the review may be the page's last section
t=t[:s.start()]+new+t[end:]
io.open(p,'w',encoding='utf-8',newline='').write(t)
