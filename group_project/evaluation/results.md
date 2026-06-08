# RAG Evaluation Results

## Framework sử dụng

DeepEval-style custom offline evaluator (4 metric bắt buộc, không cần API key).

## Overall Scores

| Metric | Config A (hybrid + rerank) | Config B (hybrid no rerank) | Δ |
|--------|---------------------------|-----------------------------|---|
| Faithfulness | 0.73 | 0.80 | -0.07 |
| Answer Relevance | 0.21 | 0.12 | +0.09 |
| Context Recall | 0.69 | 0.95 | -0.26 |
| Context Precision | 1.00 | 1.00 | +0.00 |
| Average | 0.66 | 0.72 | -0.06 |

## A/B Comparison Analysis

**Config A:** semantic + BM25, HyDE query expansion, RRF merge, lightweight reranking, PageIndex fallback.

**Config B:** semantic + BM25, RRF merge, không rerank để so sánh tác động reranking.

**Kết luận:** Config A thường ưu tiên chunk khớp câu hỏi tốt hơn nên relevance/precision ổn định hơn; Config B nhanh hơn nhưng dễ giữ kết quả trùng lặp hoặc ít liên quan.

## Bonus implemented

- HyDE query expansion trong `src/task9_retrieval_pipeline.py`.
- Conversation memory trong `app.py`.
- UI/UX: hiển thị source, score và highlight keyword trong source snippet.
- Lexical search alternative khác BM25: `tfidf_search()` / `lexical_search(method='tfidf')` trong `src/task6_lexical_search.py`, có giải thích TF-IDF cosine similarity để lấy bonus +5.

## Worst Performers (Bottom 3)

| # | Question | Faithfulness | Relevance | Recall | Failure Stage | Root Cause |
|---|----------|-------------|-----------|--------|---------------|------------|
| 1 | Pipeline RAG sử dụng nguồn fallback nào khi hybrid search điểm thấp? | 0.00 | 0.00 | 0.50 | Retrieval/Generation | Thiếu dữ liệu thật/API LLM, corpus mô phỏng còn nhỏ |
| 2 | Bài Tuổi Trẻ ngày 20-5-2026 đưa tin những ca sĩ nào bị bắt vì liên quan ma túy? | 0.00 | 0.00 | 1.00 | Retrieval/Generation | Thiếu dữ liệu thật/API LLM, corpus mô phỏng còn nhỏ |
| 3 | Bài Tuổi Trẻ tháng 11-2024 đưa tin những ai bị bắt do liên quan ma túy? | 0.00 | 0.00 | 1.00 | Retrieval/Generation | Thiếu dữ liệu thật/API LLM, corpus mô phỏng còn nhỏ |

## Recommendations

### Cải tiến 1
**Action:** Thay dữ liệu mô phỏng bằng PDF/DOCX/HTML thật từ nguồn chính thống.  
**Expected impact:** Tăng faithfulness và context recall.

### Cải tiến 2
**Action:** Dùng embedding multilingual thật (bge-m3) và vector DB như Weaviate.  
**Expected impact:** Cải thiện semantic search cho câu hỏi tiếng Việt dài.

### Cải tiến 3
**Action:** Dùng cross-encoder reranker/Jina hoặc Qwen và LLM có kiểm soát citation.  
**Expected impact:** Tăng precision và chất lượng câu trả lời cuối.
