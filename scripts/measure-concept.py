"""Word counts per `## ` section of a concept page, and By place lines over §8's bar (120 words)."""
import io,re,sys
t=io.open(f'wiki/concepts/{sys.argv[1]}.md',encoding='utf-8').read()
body=t.split('\n---',1)[1]; W=lambda s: len(s.split())
secs=re.split(r'(?m)^(## .*)$',body)
print('total',W(body))
for i in range(1,len(secs),2): print(' ',secs[i][:60],W(secs[i+1]))
m=re.search(r'(?ms)^## By place\s*\n(.*?)(?=^## |\Z)',t)
if m:
    cells=[l for l in m.group(1).splitlines() if l.startswith('- **[[')]
    print('by-place lines',len(cells),'over 120:',[(l[:30],W(l)) for l in cells if W(l)>120])
