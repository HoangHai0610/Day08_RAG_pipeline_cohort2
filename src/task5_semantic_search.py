"""
Task 5 — Semantic Search Module.

Viết module tìm kiếm ngữ nghĩa (dense retrieval) trên vector store.

Yêu cầu:
    - Input: query string + top_k
    - Output: danh sách chunks có score, sorted descending
    - Phải tương thích với embedding model và vector store ở Task 4
"""


import json
import math
from functools import lru_cache

try:
    from .task4_chunking_indexing import INDEX_FILE, embed_text, run_pipeline
except ImportError:  # Cho phép chạy trực tiếp: python src/task5_semantic_search.py
    from task4_chunking_indexing import INDEX_FILE, embed_text, run_pipeline


@lru_cache(maxsize=1)
def load_index() -> list[dict]:
    """Load local vector index đã tạo ở Task 4."""
    if not INDEX_FILE.exists():
        run_pipeline()

    if not INDEX_FILE.exists():
        return []

    chunks = json.loads(INDEX_FILE.read_text(encoding="utf-8"))
    return [chunk for chunk in chunks if chunk.get("content")]


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Tính cosine similarity giữa 2 vector."""
    if not a or not b:
        return 0.0

    dot = math.fsum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(math.fsum(x * x for x in a))
    norm_b = math.sqrt(math.fsum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0

    return dot / (norm_a * norm_b)


def semantic_search(query: str, top_k: int = 10) -> list[dict]:
    """
    Tìm kiếm ngữ nghĩa sử dụng vector similarity.

    Args:
        query: Câu truy vấn
        top_k: Số lượng kết quả tối đa

    Returns:
        List of {
            'content': str,      # Nội dung chunk
            'score': float,      # Cosine similarity score
            'metadata': dict     # source, doc_type, chunk_index
        }
        Sorted by score descending.
    """
    if top_k <= 0 or not query.strip():
        return []

    query_embedding = embed_text(query)
    scored_results = []

    for chunk in load_index():
        chunk_embedding = chunk.get("embedding") or embed_text(chunk["content"])
        score = max(0.0, cosine_similarity(query_embedding, chunk_embedding))
        scored_results.append({
            "content": chunk["content"],
            "score": round(float(score), 6),
            "metadata": chunk.get("metadata", {}),
        })

    scored_results.sort(key=lambda item: item["score"], reverse=True)
    return scored_results[:top_k]


if __name__ == "__main__":
    # Test
    results = semantic_search("hình phạt cho tội tàng trữ ma tuý", top_k=5)
    for r in results:
        preview = ascii(r["content"][:100])[1:-1]
        print(f"[{r['score']:.3f}] {preview}...")
