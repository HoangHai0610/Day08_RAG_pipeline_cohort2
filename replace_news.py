import json
from pathlib import Path
news=Path('data/landing/news')
std=Path('data/standardized/news')
for i in range(1,8):
    src=news/f'tuoitre_real_{i:02d}.json'
    if not src.exists():
        continue
    data=json.loads(src.read_text(encoding='utf-8'))
    (news/f'article_{i:02d}.json').write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    (std/f'article_{i:02d}.md').write_text(data.get('content_markdown',''), encoding='utf-8')
print('updated', len(list(news.glob('article_*.json'))), 'article files from TuoiTre real URLs')
