import json
chunks=json.load(open('data/local_chunks.json',encoding='utf-8'))
print('total',len(chunks))
for c in chunks:
    if c['metadata'].get('source')=='article_04.md':
        print('\nIDX',c['metadata'].get('chunk_index'))
        print(c['content'][:1500].replace('\n',' '))
