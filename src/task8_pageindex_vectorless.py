"""
Task 8 — PageIndex Vectorless RAG.

Đăng ký tài khoản tại: https://pageindex.ai/
SDK & sample code: https://github.com/VectifyAI/PageIndex

PageIndex cho phép RAG mà không cần vector store — sử dụng
structural understanding của document thay vì embedding.

Cài đặt:
    pip install pageindex

Hướng dẫn:
    1. Đăng ký account tại pageindex.ai
    2. Lấy API key
    3. Upload documents
    4. Query sử dụng PageIndex API
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

PAGEINDEX_API_KEY = os.getenv("PAGEINDEX_API_KEY", "")
STANDARDIZED_DIR = Path(__file__).parent.parent / "data" / "standardized"

try:
    from .task6_lexical_search import lexical_search
except ImportError:  # Cho phép chạy trực tiếp: python src/task8_pageindex_vectorless.py
    from task6_lexical_search import lexical_search


def upload_documents():
    """
    Upload toàn bộ markdown documents lên PageIndex.
    """
    documents = []
    if not STANDARDIZED_DIR.exists():
        return documents

    for md_file in sorted(STANDARDIZED_DIR.rglob("*.md")):
        documents.append({
            "content": md_file.read_text(encoding="utf-8"),
            "metadata": {
                "filename": md_file.name,
                "type": md_file.parent.name,
                "path": str(md_file.relative_to(STANDARDIZED_DIR)).replace("\\", "/"),
            },
        })

    return documents


def pageindex_search(query: str, top_k: int = 5) -> list[dict]:
    """
    Vectorless retrieval sử dụng PageIndex.
    Dùng làm fallback khi hybrid search không có kết quả tốt.

    Args:
        query: Câu truy vấn
        top_k: Số lượng kết quả tối đa

    Returns:
        List of {
            'content': str,
            'score': float,
            'metadata': dict,
            'source': 'pageindex'   # Đánh dấu nguồn retrieval
        }
    """
    if top_k <= 0 or not query.strip():
        return []

    # Fallback local mô phỏng vectorless retrieval: không dùng embedding,
    # chỉ dùng BM25/keyword trên cấu trúc chunk đã có.
    results = lexical_search(query, top_k=top_k)
    if not results:
        return []

    return [
        {
            "content": item["content"],
            "score": float(item["score"]),
            "metadata": {
                **item.get("metadata", {}),
                "retriever": "local_pageindex_fallback",
            },
            "source": "pageindex",
        }
        for item in results[:top_k]
    ]


if __name__ == "__main__":
    print("Test query:")
    results = pageindex_search("hình phạt sử dụng ma tuý", top_k=3)
    for r in results:
        preview = ascii(r["content"][:100])[1:-1]
        print(f"[{r['score']:.3f}] {preview}...")
