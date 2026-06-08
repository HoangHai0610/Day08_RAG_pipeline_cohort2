"""
Task 4 — Chunking & Indexing vào Vector Store.

Hướng dẫn:
    1. Đọc toàn bộ markdown files từ data/standardized/
    2. Chọn 1 chunking strategy (giải thích lý do)
    3. Chọn 1 embedding model (giải thích lý do)
    4. Index vào vector store (Weaviate khuyến cáo)

Chunking options (langchain-text-splitters):
    - RecursiveCharacterTextSplitter: an toàn, phổ biến
    - MarkdownHeaderTextSplitter: tốt cho file có heading
    - SemanticChunker: dùng embedding để tách (nâng cao)

Embedding model options:
    - sentence-transformers/all-MiniLM-L6-v2 (384 dim, nhẹ)
    - BAAI/bge-m3 (1024 dim, multilingual, tốt cho tiếng Việt)
    - OpenAI text-embedding-3-small (1536 dim, API)

Vector store options:
    - Weaviate (khuyến cáo: hỗ trợ hybrid search built-in)
    - ChromaDB (đơn giản, local)
    - FAISS (chỉ dense search)

Cài đặt:
    pip install langchain-text-splitters sentence-transformers weaviate-client
"""

import hashlib
import json
import math
import re
from pathlib import Path

STANDARDIZED_DIR = Path(__file__).parent.parent / "data" / "standardized"
INDEX_DIR = Path(__file__).parent.parent / "data" / "index"
INDEX_FILE = INDEX_DIR / "chunks.json"
CONFIG_FILE = INDEX_DIR / "config.json"


# =============================================================================
# CONFIGURATION — Giải thích lựa chọn của bạn trong comment
# =============================================================================

# RecursiveCharacterTextSplitter an toàn cho cả văn bản pháp luật dài và bài báo:
# ưu tiên cắt theo đoạn/dòng/câu, chỉ cắt cứng khi đoạn quá dài.
CHUNK_SIZE = 500        # 500 ký tự đủ ngắn để retrieval chính xác và qua context dễ.
CHUNK_OVERLAP = 50      # 50 ký tự giữ ngữ cảnh giữa 2 chunk liền kề.
CHUNKING_METHOD = "recursive"  # "recursive" | "markdown_header" | "semantic"

# Dùng local hashing embedding để chạy offline, không cần tải model/API.
# Đây là baseline nhẹ cho bài học; nếu có GPU/API có thể đổi sang BAAI/bge-m3.
EMBEDDING_MODEL = "local-hashing-vietnamese-384"
EMBEDDING_DIM = 384

# Local JSON index đủ cho demo/test và làm nền cho Task 5 semantic search.
VECTOR_STORE = "local_json"  # "local_json" | "weaviate" | "chromadb" | "faiss"


# =============================================================================
# IMPLEMENTATION
# =============================================================================

def load_documents() -> list[dict]:
    """
    Đọc toàn bộ markdown files từ data/standardized/.

    Returns:
        List of {'content': str, 'metadata': {'source': str, 'type': str}}
    """
    documents = []
    if not STANDARDIZED_DIR.exists():
        return documents

    for md_file in sorted(STANDARDIZED_DIR.rglob("*.md")):
        content = md_file.read_text(encoding="utf-8").strip()
        if not content:
            continue

        doc_type = md_file.parent.name if md_file.parent.name in {"legal", "news"} else "unknown"
        documents.append({
            "content": content,
            "metadata": {
                "source": md_file.name,
                "type": doc_type,
                "path": str(md_file.relative_to(STANDARDIZED_DIR)).replace("\\", "/"),
            },
        })

    return documents


def chunk_documents(documents: list[dict]) -> list[dict]:
    """
    Chunk documents theo strategy đã chọn.

    Returns:
        List of {'content': str, 'metadata': dict} — mỗi item là 1 chunk
    """
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", "; ", ", ", " ", ""],
        length_function=len,
    )

    chunks = []
    for doc in documents:
        splits = splitter.split_text(doc["content"])
        chunk_index = 0

        for chunk_text in splits:
            for safe_chunk in hard_limit_chunk(chunk_text.strip()):
                if not safe_chunk:
                    continue

                chunks.append({
                    "content": safe_chunk,
                    "metadata": {
                        **doc["metadata"],
                        "chunk_index": chunk_index,
                        "chunk_id": f"{doc['metadata']['source']}::{chunk_index}",
                    },
                })
                chunk_index += 1

    return chunks


def embed_chunks(chunks: list[dict]) -> list[dict]:
    """
    Embed toàn bộ chunks bằng model đã chọn.

    Returns:
        Mỗi chunk dict được thêm key 'embedding': list[float]
    """
    for chunk in chunks:
        chunk["embedding"] = embed_text(chunk["content"])
    return chunks


def index_to_vectorstore(chunks: list[dict]):
    """
    Lưu chunks vào vector store đã chọn.
    """
    INDEX_DIR.mkdir(parents=True, exist_ok=True)

    indexed_chunks = []
    for i, chunk in enumerate(chunks):
        item = chunk.copy()
        item.setdefault("metadata", {})
        item["metadata"] = {**item["metadata"], "index_id": i}
        if "embedding" not in item:
            item["embedding"] = embed_text(item["content"])
        indexed_chunks.append(item)

    INDEX_FILE.write_text(
        json.dumps(indexed_chunks, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    CONFIG_FILE.write_text(
        json.dumps(
            {
                "chunking_method": CHUNKING_METHOD,
                "chunk_size": CHUNK_SIZE,
                "chunk_overlap": CHUNK_OVERLAP,
                "embedding_model": EMBEDDING_MODEL,
                "embedding_dim": EMBEDDING_DIM,
                "vector_store": VECTOR_STORE,
                "num_chunks": len(indexed_chunks),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    return INDEX_FILE


def hard_limit_chunk(text: str) -> list[str]:
    """Bảo đảm không chunk nào vượt CHUNK_SIZE, kể cả khi splitter gặp đoạn rất dài."""
    if len(text) <= CHUNK_SIZE:
        return [text]

    chunks = []
    step = CHUNK_SIZE - CHUNK_OVERLAP
    start = 0
    while start < len(text):
        chunks.append(text[start:start + CHUNK_SIZE].strip())
        start += step
    return chunks


def tokenize(text: str) -> list[str]:
    """Tokenize đơn giản, đủ tốt cho hashing baseline tiếng Việt."""
    return re.findall(r"[\wÀ-ỹ]+", text.lower(), flags=re.UNICODE)


def embed_text(text: str) -> list[float]:
    """
    Tạo vector hashing 384 chiều.

    Mỗi token được hash vào một chiều, cộng/trừ theo dấu hash rồi L2-normalize.
    Cách này không mạnh bằng embedding model thật nhưng chạy offline và ổn cho baseline.
    """
    vector = [0.0] * EMBEDDING_DIM
    for token in tokenize(text):
        digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
        value = int.from_bytes(digest, byteorder="big", signed=False)
        index = value % EMBEDDING_DIM
        sign = 1.0 if (value >> 1) & 1 else -1.0
        vector[index] += sign

    norm = math.sqrt(sum(v * v for v in vector))
    if norm == 0:
        return vector

    return [round(v / norm, 6) for v in vector]


def run_pipeline():
    """Chạy toàn bộ pipeline: load → chunk → embed → index."""
    print("=" * 50)
    print("Task 4: Chunking & Indexing")
    print(f"  Chunking: {CHUNKING_METHOD} (size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP})")
    print(f"  Embedding: {EMBEDDING_MODEL} (dim={EMBEDDING_DIM})")
    print(f"  Vector Store: {VECTOR_STORE}")
    print("=" * 50)

    docs = load_documents()
    print(f"\nLoaded {len(docs)} documents")

    chunks = chunk_documents(docs)
    print(f"Created {len(chunks)} chunks")

    chunks = embed_chunks(chunks)
    print(f"Embedded {len(chunks)} chunks")

    index_path = index_to_vectorstore(chunks)
    print(f"Indexed to vector store: {index_path}")


if __name__ == "__main__":
    run_pipeline()
