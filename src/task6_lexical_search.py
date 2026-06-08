"""
Task 6 — Lexical Search Module (BM25).

Mặc định sử dụng BM25. Nếu dùng phương pháp khác (TF-IDF, Elasticsearch,
Weaviate BM25 built-in), hãy giải thích cơ chế trong buổi demo → +5 bonus.

Cài đặt:
    pip install rank-bm25

BM25 hoạt động thế nào:
    - Term Frequency (TF): từ xuất hiện nhiều trong document → điểm cao
    - Inverse Document Frequency (IDF): từ hiếm → quan trọng hơn
    - Document length normalization: document dài không bị ưu tiên quá mức
    - Formula: score(q,d) = Σ IDF(qi) * (tf(qi,d) * (k1+1)) / (tf(qi,d) + k1*(1-b+b*|d|/avgdl))
    - k1=1.5 (term saturation), b=0.75 (length normalization)
"""

import json
import math
from functools import lru_cache

try:
    from .task4_chunking_indexing import INDEX_FILE, run_pipeline, tokenize
except ImportError:  # Cho phép chạy trực tiếp: python src/task6_lexical_search.py
    from task4_chunking_indexing import INDEX_FILE, run_pipeline, tokenize


CORPUS: list[dict] = []  # List of {'content': str, 'metadata': dict}


@lru_cache(maxsize=1)
def load_corpus() -> list[dict]:
    """Load chunks đã index ở Task 4 để BM25 và semantic search dùng cùng corpus."""
    global CORPUS

    if not INDEX_FILE.exists():
        run_pipeline()

    if not INDEX_FILE.exists():
        CORPUS = []
        return CORPUS

    chunks = json.loads(INDEX_FILE.read_text(encoding="utf-8"))
    CORPUS = [
        {
            "content": chunk.get("content", ""),
            "metadata": chunk.get("metadata", {}),
        }
        for chunk in chunks
        if chunk.get("content")
    ]
    return CORPUS


class SimpleBM25:
    """
    Fallback BM25 nhỏ gọn nếu package rank_bm25 chưa được cài.

    Công thức giữ đúng ý chính: TF, IDF và normalization theo độ dài tài liệu.
    """

    def __init__(self, tokenized_corpus: list[list[str]], k1: float = 1.5, b: float = 0.75):
        self.tokenized_corpus = tokenized_corpus
        self.k1 = k1
        self.b = b
        self.doc_lengths = [len(doc) for doc in tokenized_corpus]
        self.avgdl = sum(self.doc_lengths) / len(self.doc_lengths) if self.doc_lengths else 0
        self.doc_freqs = []
        document_frequency = {}

        for doc in tokenized_corpus:
            frequencies = {}
            for token in doc:
                frequencies[token] = frequencies.get(token, 0) + 1
            self.doc_freqs.append(frequencies)
            for token in frequencies:
                document_frequency[token] = document_frequency.get(token, 0) + 1

        doc_count = len(tokenized_corpus)
        self.idf = {
            token: math.log(1 + (doc_count - freq + 0.5) / (freq + 0.5))
            for token, freq in document_frequency.items()
        }

    def get_scores(self, query_tokens: list[str]) -> list[float]:
        scores = []
        for frequencies, doc_len in zip(self.doc_freqs, self.doc_lengths):
            score = 0.0
            for token in query_tokens:
                tf = frequencies.get(token, 0)
                if tf == 0:
                    continue

                idf = self.idf.get(token, 0.0)
                denominator = tf + self.k1 * (1 - self.b + self.b * doc_len / self.avgdl)
                score += idf * (tf * (self.k1 + 1)) / denominator
            scores.append(score)
        return scores


def build_bm25_index(corpus: list[dict]):
    """
    Xây dựng BM25 index từ corpus.

    Args:
        corpus: List of {'content': str, 'metadata': dict}
    """
    tokenized_corpus = [tokenize(doc["content"]) for doc in corpus]

    try:
        from rank_bm25 import BM25Okapi
        return BM25Okapi(tokenized_corpus)
    except ImportError:
        return SimpleBM25(tokenized_corpus)


@lru_cache(maxsize=1)
def get_bm25_index():
    """Cache BM25 index vì corpus không đổi trong một phiên chạy."""
    return build_bm25_index(load_corpus())


def lexical_search(query: str, top_k: int = 10) -> list[dict]:
    """
    Tìm kiếm từ khóa sử dụng BM25.

    Args:
        query: Câu truy vấn
        top_k: Số lượng kết quả tối đa

    Returns:
        List of {
            'content': str,
            'score': float,      # BM25 score
            'metadata': dict
        }
        Sorted by score descending.
    """
    if top_k <= 0 or not query.strip():
        return []

    corpus = load_corpus()
    if not corpus:
        return []

    tokenized_query = tokenize(query)
    if not tokenized_query:
        return []

    bm25 = get_bm25_index()
    raw_scores = bm25.get_scores(tokenized_query)
    scores = [float(score) for score in raw_scores]
    ranked_indices = sorted(range(len(scores)), key=lambda idx: scores[idx], reverse=True)

    results = []
    for idx in ranked_indices[:top_k]:
        if scores[idx] <= 0:
            continue

        results.append({
            "content": corpus[idx]["content"],
            "score": round(scores[idx], 6),
            "metadata": corpus[idx]["metadata"],
        })

    return results


if __name__ == "__main__":
    # Test
    results = lexical_search("Điều 248 tàng trữ trái phép chất ma tuý", top_k=5)
    for r in results:
        preview = ascii(r["content"][:100])[1:-1]
        print(f"[{r['score']:.3f}] {preview}...")
