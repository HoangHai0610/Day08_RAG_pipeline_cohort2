"""
Task 10 — Generation Có Citation.

Hướng dẫn:
    1. Chọn top_k, top_p phù hợp (giải thích lý do)
    2. Sắp xếp lại chunks sau reranking để tránh "lost in the middle"
    3. Inject context vào prompt
    4. Yêu cầu LLM trả lời có citation
    5. Nếu không đủ evidence → "I cannot verify this information"
"""

import os
import re
import requests
from dotenv import load_dotenv

load_dotenv()

try:
    from .task4_chunking_indexing import tokenize
    from .task9_retrieval_pipeline import retrieve
except ImportError:  # Cho phép chạy trực tiếp: python src/task10_generation.py
    from task4_chunking_indexing import tokenize
    from task9_retrieval_pipeline import retrieve


# =============================================================================
# CONFIGURATION — Giải thích lựa chọn
# =============================================================================

# top_k: Số chunks đưa vào context
# Chọn 5 vì: đủ evidence mà không quá dài gây lost in the middle
TOP_K = 5

# top_p (nucleus sampling): Xác suất tích luỹ cho token generation
# Chọn 0.9 vì: đủ diverse nhưng không quá random
TOP_P = 0.9

# temperature: Độ ngẫu nhiên của output
# Chọn 0.3 vì: RAG cần factual, ít sáng tạo
TEMPERATURE = 0.3
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")


# =============================================================================
# SYSTEM PROMPT
# =============================================================================

SYSTEM_PROMPT = """Answer the following question comprehensively in Vietnamese.
For every statement of fact or claim, immediately insert a citation in brackets
linking to the specific source (e.g., [Luật Phòng chống ma tuý 2021, Điều 3]
or [VnExpress, 2024]).

If the information is not explicitly stated in the provided context or knowledge
base, state 'Tôi không thể xác minh thông tin này từ nguồn hiện có' rather than
guessing.

Rules:
- Only use information from the provided context
- Every factual claim MUST have a citation
- If context is insufficient, say so clearly
- Structure your answer with clear paragraphs"""


# =============================================================================
# DOCUMENT REORDERING (tránh lost in the middle)
# =============================================================================

def reorder_for_llm(chunks: list[dict]) -> list[dict]:
    """
    Sắp xếp chunks để tránh "lost in the middle" effect.

    LLM nhớ tốt thông tin ở ĐẦU và CUỐI prompt, quên thông tin ở GIỮA.
    Strategy: đặt chunks quan trọng nhất ở đầu và cuối, kém quan trọng ở giữa.

    Input order (by score):  [1, 2, 3, 4, 5]
    Output order:            [1, 3, 5, 4, 2]
    (best first, worst in middle, second-best last)

    Args:
        chunks: List sorted by score descending (from retrieval)

    Returns:
        List reordered để maximize LLM attention.
    """
    if len(chunks) <= 2:
        return chunks

    front = [chunks[i] for i in range(0, len(chunks), 2)]
    back_start = len(chunks) - 1 if len(chunks) % 2 == 0 else len(chunks) - 2
    back = [chunks[i] for i in range(back_start, 0, -2)]
    return front + back


# =============================================================================
# CONTEXT FORMATTING
# =============================================================================

def format_context(chunks: list[dict]) -> str:
    """
    Format chunks thành context string cho prompt.
    Mỗi chunk có label source để LLM có thể cite.

    Args:
        chunks: List of {'content': str, 'metadata': dict, 'score': float}

    Returns:
        Formatted context string.
    """
    context_parts = []
    for i, chunk in enumerate(chunks, 1):
        metadata = chunk.get("metadata", {})
        source = metadata.get("source", f"source-{i}")
        doc_type = metadata.get("type", "unknown")
        score = float(chunk.get("score", 0.0))
        context_parts.append(
            f"[Document {i} | Source: {source} | Type: {doc_type} | Score: {score:.3f}]\n"
            f"{chunk.get('content', '').strip()}\n"
        )
    return "\n---\n".join(context_parts)


def source_citation(chunk: dict) -> str:
    """Tạo citation dạng [Nguồn, Năm] từ metadata/content."""
    metadata = chunk.get("metadata", {})
    source = metadata.get("source", "Nguồn không rõ")
    source_name = re.sub(r"\.(md|pdf|docx?|json)$", "", source, flags=re.IGNORECASE)
    source_name = source_name.replace("-", " ")

    haystack = f"{source} {chunk.get('content', '')}"
    year_match = re.search(r"(20\d{2}|19\d{2})", haystack)
    year = year_match.group(1) if year_match else "N/A"
    return f"[{source_name}, {year}]"


def best_evidence_sentence(query: str, content: str) -> str:
    """Chọn câu/đoạn ngắn có overlap tốt nhất với query."""
    query_tokens = set(tokenize(query))
    pieces = re.split(r"(?<=[.!?。])\s+|\n+", content)
    candidates = [piece.strip() for piece in pieces if len(piece.strip()) >= 30]
    if not candidates:
        return content.strip()[:300]

    def score(piece: str) -> tuple[int, int]:
        tokens = set(tokenize(piece))
        return (len(query_tokens.intersection(tokens)), -len(piece))

    best = max(candidates, key=score)
    return best[:450].strip()


def _ollama_available() -> bool:
    """Return True when the local Ollama server is reachable."""
    try:
        response = requests.get(f"{OLLAMA_URL}/api/tags", timeout=2)
        return response.status_code == 200
    except Exception:
        return False


# =============================================================================
# GENERATION
# =============================================================================

def generate_with_citation(query: str, top_k: int = TOP_K) -> dict:
    """
    End-to-end RAG generation có citation.

    Pipeline:
        1. Retrieve relevant chunks
        2. Reorder để tránh lost in the middle
        3. Format context với source labels
        4. Build prompt (system + context + query)
        5. Call LLM
        6. Return answer + sources

    Args:
        query: Câu hỏi của user

    Returns:
        {
            'answer': str,           # Câu trả lời có citation
            'sources': list[dict],   # Các chunks đã dùng
            'retrieval_source': str  # 'hybrid' hoặc 'pageindex'
        }
    """
    chunks = retrieve(query, top_k=top_k)
    if not chunks:
        return {
            "answer": "Tôi không thể xác minh thông tin này từ nguồn hiện có.",
            "sources": [],
            "retrieval_source": "none",
        }

    reordered = reorder_for_llm(chunks)
    _ = format_context(reordered)

    evidence_lines = []
    for chunk in reordered[:top_k]:
        sentence = best_evidence_sentence(query, chunk.get("content", ""))
        if not sentence:
            continue
        evidence_lines.append(f"- {sentence} {source_citation(chunk)}")

    if not evidence_lines:
        answer = "Tôi không thể xác minh thông tin này từ nguồn hiện có."
    else:
        answer = "Dựa trên các nguồn đã truy xuất:\n" + "\n".join(evidence_lines)

    return {
        "answer": answer,
        "sources": chunks,
        "retrieval_source": chunks[0].get("source", "hybrid") if chunks else "none",
    }


if __name__ == "__main__":
    test_queries = [
        "Hình phạt cho tội tàng trữ trái phép chất ma tuý theo pháp luật Việt Nam?",
        "Những nghệ sĩ nào đã bị bắt vì liên quan tới ma tuý?",
        "Quy trình cai nghiện bắt buộc theo Luật Phòng chống ma tuý 2021?",
    ]

    for q in test_queries:
        print(f"\n{'='*70}")
        print(f"Q: {ascii(q)[1:-1]}")
        print("=" * 70)
        result = generate_with_citation(q)
        print(f"\nA: {ascii(result['answer'])[1:-1]}")
        print(f"\n[Sources: {len(result['sources'])} chunks | via {result['retrieval_source']}]")
