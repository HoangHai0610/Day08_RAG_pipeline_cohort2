"""
Task 7 — Reranking Module.

Chọn 1 trong các phương pháp:
    - Cross-encoder reranker: Jina Reranker v2 (multilingual) hoặc Qwen3-Reranker
    - MMR (Maximal Marginal Relevance): tự implement
    - RRF (Reciprocal Rank Fusion): tự implement

Nếu dùng MMR hoặc RRF, đảm bảo hiểu và giải thích được cơ chế.
"""

import math

try:
    from .task4_chunking_indexing import embed_text, tokenize
    from .task5_semantic_search import cosine_similarity
except ImportError:  # Cho phép chạy trực tiếp: python src/task7_reranking.py
    from task4_chunking_indexing import embed_text, tokenize
    from task5_semantic_search import cosine_similarity


def lexical_overlap_score(query: str, content: str) -> float:
    """Tính điểm liên quan local bằng overlap token giữa query và document."""
    query_tokens = tokenize(query)
    content_tokens = tokenize(content)
    if not query_tokens or not content_tokens:
        return 0.0

    query_set = set(query_tokens)
    content_set = set(content_tokens)
    overlap = query_set.intersection(content_set)
    coverage = len(overlap) / len(query_set)

    # Boost nhẹ nếu token query xuất hiện nhiều lần trong content.
    frequency = sum(content_tokens.count(token) for token in overlap)
    frequency_boost = math.log1p(frequency) / 10
    return min(1.0, coverage + frequency_boost)


def rerank_cross_encoder(
    query: str, candidates: list[dict], top_k: int = 5
) -> list[dict]:
    """
    Rerank candidates sử dụng cross-encoder model.

    Args:
        query: Câu truy vấn
        candidates: List of {'content': str, 'score': float, 'metadata': dict}
        top_k: Số lượng kết quả sau rerank

    Returns:
        List of top_k candidates, re-scored và sorted by rerank_score descending.
    """
    if top_k <= 0 or not candidates:
        return []

    query_embedding = embed_text(query)
    scored = []
    for rank, candidate in enumerate(candidates, 1):
        content = candidate.get("content", "")
        semantic = cosine_similarity(query_embedding, candidate.get("embedding") or embed_text(content))
        lexical = lexical_overlap_score(query, content)
        original = float(candidate.get("score", 0.0))
        original_norm = original / (1.0 + abs(original))

        # Local cross-encoder surrogate: ưu tiên match trực tiếp, giữ lại tín hiệu semantic/original.
        rerank_score = 0.55 * lexical + 0.30 * max(0.0, semantic) + 0.15 * original_norm
        item = candidate.copy()
        item["score"] = round(float(rerank_score), 6)
        item["metadata"] = candidate.get("metadata", {})
        item["metadata"] = {**item["metadata"], "original_rank": rank}
        scored.append(item)

    scored.sort(key=lambda item: item["score"], reverse=True)
    return scored[:top_k]


def rerank_mmr(
    query_embedding: list[float],
    candidates: list[dict],
    top_k: int = 5,
    lambda_param: float = 0.7,
) -> list[dict]:
    """
    Maximal Marginal Relevance — chọn candidates vừa relevant vừa diverse.

    MMR = λ * sim(query, doc) - (1-λ) * max(sim(doc, selected_docs))

    Args:
        query_embedding: Vector embedding của query
        candidates: List of {'content': str, 'score': float, 'embedding': list, 'metadata': dict}
        top_k: Số lượng kết quả
        lambda_param: Trade-off giữa relevance (1.0) và diversity (0.0)

    Returns:
        List of top_k candidates selected by MMR.
    """
    if top_k <= 0 or not candidates:
        return []

    prepared = []
    for candidate in candidates:
        item = candidate.copy()
        item["embedding"] = candidate.get("embedding") or embed_text(candidate.get("content", ""))
        prepared.append(item)

    selected_indices = []
    remaining = list(range(len(prepared)))

    while remaining and len(selected_indices) < top_k:
        best_idx = None
        best_score = float("-inf")

        for idx in remaining:
            relevance = cosine_similarity(query_embedding, prepared[idx]["embedding"])
            diversity_penalty = 0.0
            if selected_indices:
                diversity_penalty = max(
                    cosine_similarity(prepared[idx]["embedding"], prepared[selected]["embedding"])
                    for selected in selected_indices
                )

            mmr_score = lambda_param * relevance - (1 - lambda_param) * diversity_penalty
            if mmr_score > best_score:
                best_score = mmr_score
                best_idx = idx

        selected_indices.append(best_idx)
        remaining.remove(best_idx)

    results = []
    for idx in selected_indices:
        item = prepared[idx].copy()
        item["score"] = round(float(max(0.0, cosine_similarity(query_embedding, item["embedding"]))), 6)
        item.pop("embedding", None)
        results.append(item)
    return results


def rerank_rrf(
    ranked_lists: list[list[dict]], top_k: int = 5, k: int = 60
) -> list[dict]:
    """
    Reciprocal Rank Fusion — gộp kết quả từ nhiều ranker.

    RRF(d) = Σ 1 / (k + rank_r(d))

    Args:
        ranked_lists: List of ranked result lists (mỗi list từ 1 ranker)
        top_k: Số lượng kết quả cuối cùng
        k: Smoothing constant (default=60, từ paper Cormack et al. 2009)

    Returns:
        List of top_k candidates sorted by RRF score descending.
    """
    if top_k <= 0:
        return []

    rrf_scores = {}
    content_map = {}

    for ranked_list in ranked_lists:
        for rank, item in enumerate(ranked_list, 1):
            metadata = item.get("metadata", {})
            key = metadata.get("chunk_id") or metadata.get("index_id") or item.get("content", "")
            if not key:
                continue
            rrf_scores[key] = rrf_scores.get(key, 0.0) + 1.0 / (k + rank)
            if key not in content_map or item.get("score", 0) > content_map[key].get("score", 0):
                content_map[key] = item

    sorted_keys = sorted(rrf_scores, key=lambda key: rrf_scores[key], reverse=True)

    results = []
    for key in sorted_keys[:top_k]:
        item = content_map[key].copy()
        item["score"] = round(float(rrf_scores[key]), 6)
        item["metadata"] = item.get("metadata", {})
        results.append(item)

    return results


# =============================================================================
# Main rerank interface
# =============================================================================

def rerank(
    query: str,
    candidates: list[dict],
    top_k: int = 5,
    method: str = "cross_encoder",  # "cross_encoder" | "mmr" | "rrf"
) -> list[dict]:
    """
    Unified reranking interface.

    Args:
        query: Câu truy vấn
        candidates: Danh sách candidates từ retrieval
        top_k: Số lượng kết quả sau rerank
        method: Phương pháp reranking

    Returns:
        List of top_k reranked candidates.
    """
    if top_k <= 0 or not candidates:
        return []

    if method == "cross_encoder":
        return rerank_cross_encoder(query, candidates, top_k)
    elif method == "mmr":
        return rerank_mmr(embed_text(query), candidates, top_k)
    elif method == "rrf":
        return rerank_rrf([candidates], top_k=top_k)
    else:
        raise ValueError(f"Unknown rerank method: {method}")


if __name__ == "__main__":
    # Test with dummy data
    dummy_candidates = [
        {"content": "Điều 248: Tội tàng trữ trái phép chất ma tuý", "score": 0.8, "metadata": {}},
        {"content": "Nghệ sĩ X bị bắt vì sử dụng ma tuý", "score": 0.7, "metadata": {}},
        {"content": "Hình phạt tù từ 2-7 năm cho tội tàng trữ", "score": 0.6, "metadata": {}},
    ]
    results = rerank("hình phạt tàng trữ ma tuý", dummy_candidates, top_k=2)
    for r in results:
        preview = ascii(r["content"])[1:-1]
        print(f"[{r['score']:.3f}] {preview}")
