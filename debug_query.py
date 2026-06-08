from src.task9_retrieval_pipeline import retrieve
q='Miu Lê bị bắt và phạm tội gì?'
r=retrieve(q, top_k=5, score_threshold=0)
print('N',len(r))
for i,x in enumerate(r,1):
    print('\n---',i,x.get('score'),x.get('metadata'))
    print(x.get('content','')[:1000].replace('\n',' '))
