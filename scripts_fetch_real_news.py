from pathlib import Path
import requests, re, json
from html import unescape
from datetime import datetime
from urllib.parse import urljoin

BASE='https://tuoitre.vn'
URLS=[
 'https://tuoitre.vn/bat-ca-si-long-nhat-va-ca-si-son-ngoc-minh-vi-lien-quan-ma-tuy-20260520082138943.htm',
 'https://tuoitre.vn/long-nhat-bi-bat-vi-ma-tuy-la-ba-tam-showbiz-tung-co-tinh-tao-loat-scandal-de-noi-tieng-2026052012470757.htm',
 'https://tuoitre.vn/ca-si-son-ngoc-minh-truoc-khi-bi-bat-vi-ma-tuy-nguoi-nha-mat-lien-lac-bo-be-ca-hat-nhieu-nam-20260520133233973.htm',
 'https://tuoitre.vn/ca-si-miu-le-bi-bat-qua-tang-su-dung-ma-tuy-o-hai-phong-20260511172700149.htm',
 'https://tuoitre.vn/chuyen-an-vn10-truy-to-227-bi-can-trong-do-co-ca-si-chi-dan-an-tay-2026040308051239.htm',
 'https://tuoitre.vn/vu-4-tiep-vien-hang-khong-xach-tay-ma-tuy-tiec-sinh-nhat-bay-lac-cua-co-tien-truc-phuong-20260413135309212.htm',
 'https://tuoitre.vn/bat-nguoi-mau-an-tay-ca-si-chi-dan-co-tien-truc-phuong-do-lien-quan-ma-tuy-20241114114826655.htm',
]
OUT=Path('data/landing/news'); STD=Path('data/standardized/news')
OUT.mkdir(parents=True,exist_ok=True); STD.mkdir(parents=True,exist_ok=True)

def clean_html(s):
    s=re.sub(r'<script[\s\S]*?</script>|<style[\s\S]*?</style>', ' ', s, flags=re.I)
    s=re.sub(r'<[^>]+>', ' ', s)
    return ' '.join(unescape(s).split())

def meta(html, prop):
    pats=[fr'<meta[^>]+property=["\']{re.escape(prop)}["\'][^>]+content=["\']([^"\']+)["\']', fr'<meta[^>]+name=["\']{re.escape(prop)}["\'][^>]+content=["\']([^"\']+)["\']']
    for p in pats:
        m=re.search(p, html, re.I)
        if m: return unescape(m.group(1)).strip()
    return ''

def extract(html):
    title=meta(html,'og:title') or meta(html,'title')
    desc=meta(html,'og:description') or meta(html,'description')
    pub=meta(html,'article:published_time') or meta(html,'pubdate')
    # TuoiTre body normally has detail-cmain / detail-content afcbc-body; retain paragraphs
    paragraphs=[]
    for m in re.finditer(r'<p[^>]*>(.*?)</p>', html, re.S|re.I):
        txt=clean_html(m.group(1))
        if len(txt)>40 and not txt.startswith(('TTO -','Copyright')):
            if txt not in paragraphs:
                paragraphs.append(txt)
    # Add desc at top if body sparse
    if desc and desc not in paragraphs:
        paragraphs.insert(0, desc)
    content='\n\n'.join(paragraphs[:30])
    if len(content)<800:
        text=clean_html(html)
        # fallback around keywords
        content=(desc+'\n\n'+text[:4000]).strip()
    return title, desc, pub, content

session=requests.Session(); session.headers.update({'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
for i,url in enumerate(URLS,1):
    r=session.get(url,timeout=25)
    title,desc,pub,content=extract(r.text)
    year=''
    m=re.search(r'(20\d{2})', pub or url)
    if m: year=m.group(1)
    data={
      'url':url,
      'title':title or f'Tuoi Tre article {i}',
      'source':'Tuổi Trẻ Online',
      'date_published':pub,
      'date_crawled':datetime.now().isoformat(timespec='seconds'),
      'year':year,
      'status_code':r.status_code,
      'content_markdown':f"# {title}\n\n**Source:** Tuổi Trẻ Online\n**URL:** {url}\n**Published:** {pub}\n**Crawled:** {datetime.now().isoformat(timespec='seconds')}\n\n{content}\n"
    }
    fn=f'tuoitre_real_{i:02d}.json'
    OUT.joinpath(fn).write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
    STD.joinpath(Path(fn).stem+'.md').write_text(data['content_markdown'],encoding='utf-8')
    print(i, r.status_code, len(content), (title or '').encode('ascii','ignore').decode())
