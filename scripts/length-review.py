"""Replace a concept page's `## Length — reviewed …` section with a new dated review.
Usage: length-review.py <topic-slug> <YYYY-MM-DD> <file holding the review body, one paragraph per line>
The heading records the page's size, `(at N words)` by lint #8's own measure, so the ruling holds
until the page outgrows it rather than until its next edit (LINT.md #8)."""
import io,os,re,subprocess,sys
topic,date,src=sys.argv[1:4]
p=f'wiki/concepts/{topic}.md'; t=io.open(p,encoding='utf-8',newline='').read(); eol='\r\n' if '\r\n' in t else '\n'
s=re.search(r'^## Length — reviewed .*$',t,re.M); e=re.search(r'^## ',t[s.end():],re.M)
paras=[l.strip() for l in io.open(src,encoding='utf-8').read().splitlines() if l.strip()]
new=f'## Length — reviewed {date}'+eol+eol+(eol+eol).join(paras)+eol+eol
end=s.end()+e.start() if e else len(t)   # the review may be the page's last section
t=t[:s.start()]+new+t[end:]
io.open(p,'w',encoding='utf-8',newline='').write(t)
# measure the page as ruled and stamp the size on the heading
out=subprocess.run([sys.executable,os.path.join(os.path.dirname(os.path.abspath(__file__)),'page-length.py'),p],capture_output=True,text=True,encoding='utf-8').stdout
m=re.search(r'([\d,]+) words',out)
if m:
    t=io.open(p,encoding='utf-8',newline='').read()
    t=t.replace(f'## Length — reviewed {date}'+eol,f'## Length — reviewed {date} (at {m.group(1)} words)'+eol,1)
    io.open(p,'w',encoding='utf-8',newline='').write(t)
