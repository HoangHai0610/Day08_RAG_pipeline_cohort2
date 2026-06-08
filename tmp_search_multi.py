import requests,re,sys
from html import unescape
queries=['Chi Dân An Tây ma túy','nghệ sĩ bị bắt ma túy','ca sĩ bị bắt ma túy','người mẫu An Tây ma túy','Trúc Phương ma túy','Châu Việt Cường ma túy','Hữu Tín ma túy']
out=[]
for q in queries:
    url='https://tuoitre.vn/tim-kiem.htm?keywords='+requests.utils.quote(q)
    html=requests.get(url,headers={'User-Agent':'Mozilla/5.0'},timeout=20).text
    out.append(f'\nQUERY {q} len {len(html)}')
    seen=set(); count=0
    for m in re.finditer(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', html, re.S):
        l=m.group(1); t=re.sub('<[^>]+>',' ',m.group(2)); t=' '.join(unescape(t).split())
        if len(t)>15 and any(k in t.lower() for k in ['ma túy','ma tuý','chi dân','an tây','trúc phương','hữu tín','châu việt']):
            if (t,l) in seen: continue
            seen.add((t,l)); out.append(f'- {t} => {l}'); count+=1
            if count>=10: break
sys.stdout.buffer.write('\n'.join(out).encode('utf-8','ignore'))
