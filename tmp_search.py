import requests,re,sys
from html import unescape
url='https://tuoitre.vn/tim-kiem.htm?keywords=Chi%20D%C3%A2n%20An%20T%C3%A2y%20ma%20t%C3%BAy'
html=requests.get(url,headers={'User-Agent':'Mozilla/5.0'},timeout=20).text
out=['len '+str(len(html))]
for m in re.finditer(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', html, re.S):
    l=m.group(1); t=re.sub('<[^>]+>',' ',m.group(2)); t=' '.join(unescape(t).split())
    if any(k in t.lower() for k in ['chi dân','an tây','ma túy','ma tuý','trúc phương']):
        out.append(f'{t} => {l}')
sys.stdout.buffer.write('\n'.join(out[:50]).encode('utf-8','ignore'))
