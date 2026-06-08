from src.task9_retrieval_pipeline import retrieve
from src.task10_generation import generate_with_citation

queries = [
    "Miu Lê bị bắt và phạm tội gì?",
    "Chi Dân và An Tây bị truy tố tội gì?",
    "Điều 249 quy định hình phạt tàng trữ ma túy như thế nào?",
    "Luật Phòng chống ma túy 2021 có những hình thức cai nghiện nào?",
    "Long Nhật và Sơn Ngọc Minh bị bắt vì hành vi gì?",
]

for q in queries:
    print("\n" + "="*90)
    print("QUERY:", q)
    print("-"*90)
    chunks = retrieve(q, top_k=5, score_threshold=0)
    print("TOP SOURCES:")
    for i, c in enumerate(chunks[:3], 1):
        md = c.get('metadata', {})
        snippet = c.get('content','')[:350].replace('\n', ' ')
        print(f" {i}. score={c.get('score',0):.3f} source={md.get('source')} chunk={md.get('chunk_index')} type={md.get('type')}")
        print("    ", snippet)
    print("\nANSWER:")
    print(generate_with_citation(q, context_chunks=chunks, top_k=5)["answer"])
