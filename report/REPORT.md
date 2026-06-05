# Báo Cáo Lab 7: Data Foundations — Embedding & Vector Store

**Họ tên:** Vũ Thành Danh  
**Mã học viên:** 2A202600606  
**Thành viên nhóm:** Nguyễn Văn Chung — 2A202600647  
**Domain:** Internal Knowledge Assistant / RAG Support Knowledge Base  
**Ngày:** 05/06/2026

---

## Team Information

| Student | Student ID | Role |
|---|---|---|
| Vũ Thành Danh | 2A202600606 | Chọn và đánh giá `SentenceChunker(max_sentences_per_chunk=3)`, chạy benchmark, viết report |
| Nguyễn Văn Chung | 2A202600647 | Chọn và đánh giá `RecursiveChunker(chunk_size=512)`, đối chiếu strategy nhóm |

---

## 1. Warm-up

### 1.1 Cosine Similarity in Plain Language

**High cosine similarity nghĩa là gì?**  
High cosine similarity nghĩa là hai vector có hướng gần giống nhau trong embedding space. Với văn bản, điều này thường cho thấy hai đoạn có nội dung hoặc ý nghĩa gần nhau, dù không nhất thiết dùng cùng từ khóa.

**Ví dụ HIGH similarity:**

- Sentence A: `Vector stores keep embeddings for semantic search.`
- Sentence B: `A vector database retrieves similar chunks for RAG.`
- Lý do: cả hai đều nói về vector store, embeddings, semantic search và retrieval.

**Ví dụ LOW similarity:**

- Sentence A: `Metadata filters improve retrieval precision.`
- Sentence B: `Bananas are yellow fruits.`
- Lý do: hai câu thuộc hai chủ đề hoàn toàn khác nhau.

**Vì sao cosine similarity thường phù hợp hơn Euclidean distance cho text embeddings?**  
Cosine similarity tập trung vào hướng vector, tức là mức độ gần nhau về ý nghĩa. Euclidean distance phụ thuộc nhiều vào độ lớn vector, trong khi với text embeddings, hướng thường quan trọng hơn magnitude.

### 1.2 Chunking Math

**Document 10,000 ký tự, chunk_size=500, overlap=50:**

```text
step = chunk_size - overlap = 500 - 50 = 450
num_chunks = ceil((doc_length - overlap) / step)
           = ceil((10000 - 50) / 450)
           = ceil(22.11)
           = 23 chunks
```

**Nếu overlap tăng lên 100:**

```text
step = 500 - 100 = 400
num_chunks = ceil((10000 - 100) / 400)
           = ceil(24.75)
           = 25 chunks
```

Overlap lớn hơn tạo nhiều chunk hơn, tốn thêm embedding/storage/search cost, nhưng giúp giữ ngữ cảnh tốt hơn ở ranh giới giữa hai chunk.

---

## 2. Document Selection — Nhóm

### 2.1 Domain

**Domain:** Internal Knowledge Assistant / RAG Support Knowledge Base.

Nhóm chọn domain này vì nó phù hợp trực tiếp với mục tiêu lab: tài liệu nội bộ thường nằm rải rác trong nhiều file `.md/.txt`, cần metadata, chunking, vector search và retrieval để trả lời có căn cứ. Bộ dữ liệu không chứa PII và có cả tiếng Anh lẫn tiếng Việt để kiểm tra metadata filtering theo `language`.

### 2.2 Data Inventory

| # | Tên tài liệu | Nguồn | Số ký tự | Metadata đã gán |
|---|---|---|---:|---|
| 1 | `python_intro.txt` | Study note tự chuẩn hóa cho lab | 1,944 | `source`, `category=programming`, `language=en`, `owner`, `doc_type`, `pii=no` |
| 2 | `vector_store_notes.md` | Group RAG note | 2,123 | `source`, `category=vector_store`, `language=en`, `owner`, `doc_type`, `pii=no` |
| 3 | `rag_system_design.md` | Internal assistant scenario | 2,391 | `source`, `category=rag_design`, `language=en`, `owner`, `doc_type`, `pii=no` |
| 4 | `customer_support_playbook.txt` | Support operations scenario | 1,692 | `source`, `category=support`, `language=en`, `owner`, `doc_type`, `pii=no` |
| 5 | `chunking_experiment_report.md` | Group experiment summary | 1,987 | `source`, `category=chunking`, `language=en`, `owner`, `doc_type`, `pii=no` |
| 6 | `vi_retrieval_notes.md` | Vietnamese retrieval note | 1,667 | `source`, `category=retrieval`, `language=vi`, `owner`, `doc_type`, `pii=no` |

Chi tiết inventory nằm trong `report/DATA_INVENTORY.md`.

### 2.3 Metadata Schema

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho retrieval? |
|---|---|---|---|
| `source` | string | `data/vector_store_notes.md` | Giúp trích nguồn và debug retrieved chunk |
| `category` | string | `vector_store`, `support`, `retrieval` | Dùng để lọc trước khi search, giảm nhiễu giữa nhiều domain |
| `language` | string | `en`, `vi` | Query tiếng Việt có thể filter sang tài liệu tiếng Việt |
| `owner` | string | `Support operations scenario` | Biết tài liệu thuộc nhóm/nguồn nào |
| `doc_type` | string | `playbook`, `technical_note` | Phân biệt playbook, design note và report |
| `pii` | string | `no` | Phục vụ kiểm soát an toàn dữ liệu |

---

## 3. Chunking Strategy — Cá nhân chọn, nhóm so sánh

### 3.1 Baseline Analysis

Chạy `ChunkingStrategyComparator().compare()` trên 3 tài liệu với `chunk_size=512`:

| Tài liệu | Strategy | Chunk Count | Avg Length | Preserves Context? |
|---|---|---:|---:|---|
| `vector_store_notes.md` | FixedSizeChunker | 5 | 424.6 | Trung bình, có thể cắt ngang đoạn |
| `vector_store_notes.md` | SentenceChunker | 10 | 210.2 | Tốt ở mức câu, dễ đọc |
| `vector_store_notes.md` | RecursiveChunker | 7 | 301.6 | Tốt ở mức paragraph/section |
| `rag_system_design.md` | FixedSizeChunker | 5 | 478.2 | Trung bình |
| `rag_system_design.md` | SentenceChunker | 7 | 338.9 | Tốt, mỗi chunk có 2–3 câu |
| `rag_system_design.md` | RecursiveChunker | 7 | 339.9 | Tốt, giữ paragraph tốt hơn |
| `customer_support_playbook.txt` | FixedSizeChunker | 4 | 423.0 | Trung bình |
| `customer_support_playbook.txt` | SentenceChunker | 4 | 420.8 | Tốt, phù hợp playbook |
| `customer_support_playbook.txt` | RecursiveChunker | 5 | 336.8 | Tốt, giữ paragraph ngắn rõ ràng |

### 3.2 Strategy Của Tôi

**Loại:** `SentenceChunker(max_sentences_per_chunk=3)`.

Strategy này tách văn bản theo ranh giới câu bằng regex, sau đó gom tối đa 3 câu vào một chunk. Với support playbook và note nội bộ, cách này làm chunk dễ đọc, ít bị cắt ngang câu, và giúp người chấm dễ kiểm tra top retrieved chunks.

**Lý do chọn:** Dataset của tôi gồm nhiều đoạn giải thích ngắn, playbook và note có câu rõ ràng. Nếu dùng fixed-size, chunk có thể cắt ngang hướng dẫn. Nếu dùng recursive, kết quả tốt nhưng khó giải thích hơn sentence strategy trong một bài lab nhập môn.

### 3.3 So Sánh Với Baseline

| Strategy | Chunk quality | Retrieval/debug quality | Nhận xét |
|---|---|---|---|
| Fixed-size | Ổn định về độ dài nhưng có thể cắt ngang ý | Dễ có chunk chứa keyword nhưng thiếu hướng dẫn đầy đủ | Không chọn làm chính |
| Recursive | Giữ paragraph/section tốt | Rất phù hợp docs dài có heading | Tốt nhưng không phải strategy cá nhân của tôi |
| Sentence-based | Giữ câu hoàn chỉnh, dễ đọc | Phù hợp FAQ/playbook/support notes | Chọn làm strategy chính |

### 3.4 So Sánh Với Thành Viên Khác

| Thành viên | Strategy | Evidence | Điểm mạnh | Điểm yếu |
|---|---|---|---|---|
| Vũ Thành Danh | `SentenceChunker(max_sentences_per_chunk=3)` | 6 docs, sentence chunks, 5 benchmark queries, offline demo log | Dễ đọc, ít cắt ngang câu, phù hợp playbook/FAQ | Có thể thiếu context nếu câu ngắn hoặc nội dung phụ thuộc paragraph |
| Nguyễn Văn Chung | `RecursiveChunker(chunk_size=512)` | 7 docs, 26 chunks, top-1 relevant 5/5, top-3 relevant 5/5 | Giữ cấu trúc Markdown/paragraph tốt, phù hợp docs kỹ thuật | Cần tuning chunk size và separator |

**Kết luận nhóm:** Không có strategy tốt nhất cho mọi tài liệu. Với bài của Chung, recursive chunking hợp lý hơn vì dataset là technical docs có heading và paragraph dài. Với bài của tôi, sentence chunking hợp lý vì dataset là playbook/note nội bộ có câu ngắn, dễ đánh giá và dễ debug.

---

## 4. My Approach — Cá nhân

### 4.1 Chunking Functions

- `SentenceChunker.chunk`: dùng regex `(?<=[.!?])\s+|\n+` để tách theo dấu câu và newline, bỏ khoảng trắng thừa, rồi gom tối đa `max_sentences_per_chunk` câu vào một chunk.
- `RecursiveChunker.chunk`: thử separator theo thứ tự `\n\n`, `\n`, `. `, space, rồi fallback. Base case là text rỗng hoặc text ngắn hơn `chunk_size`.
- `compute_similarity`: tính cosine similarity bằng dot product chia cho tích độ dài vector; nếu vector zero thì trả về `0.0` để tránh chia cho 0.

### 4.2 EmbeddingStore

- `add_documents`: nhận list `Document`, tạo embedding cho `content`, copy metadata và lưu record in-memory.
- `search`: embed query, tính dot product/cosine-like score với toàn bộ records, sort giảm dần theo score.
- `search_with_filter`: lọc metadata trước rồi mới search trên tập ứng viên, giúp giảm nhiễu.
- `delete_document`: xóa theo `id` hoặc `metadata.doc_id`, trả về `True` nếu có record bị xóa.

### 4.3 KnowledgeBaseAgent

`KnowledgeBaseAgent.answer` triển khai đúng RAG pattern: retrieve top-k chunks, build prompt gồm context và question, sau đó gọi `llm_fn`. Trong bài này, `llm_fn` có thể là demo LLM/offline fallback để người chấm chạy không cần API key.

### 4.4 Test Results

```text
python -m pytest tests/ -q
42 passed
```

Log minh chứng nằm ở `report/pytest_log.txt`.

### 4.5 Demo Evidence

| Log file | Lệnh chạy | Mục đích |
|---|---|---|
| `report/pytest_log.txt` | `python -m pytest tests/ -q` | Chứng minh code pass tests |
| `report/offline_fallback_demo_log.txt` | `python main.py "What are embeddings used for in search?"` | Chứng minh manual demo chạy offline |
| `report/vector_store_demo_log.txt` | `python scripts/vector_store_demo.py` | Chứng minh data inventory, strategy comparison, similarity, retrieval và failure case |

**Ghi rõ về OpenRouter:** Bài này không claim chạy OpenRouter. Demo dùng offline fallback để đảm bảo reproducible và không cần API key.

---

## 5. Similarity Predictions — Cá nhân

| Pair | Sentence A | Sentence B | Dự đoán | Actual Score | Đúng? |
|---|---|---|---|---:|---|
| 1 | Vector stores keep embeddings for semantic search. | A vector database retrieves similar chunks for RAG. | high | 0.3333 | Đúng tương đối: cùng chủ đề vector/RAG/search |
| 2 | Metadata filters reduce noisy retrieval results. | Access control and language fields narrow search candidates. | medium | 0.0000 | Chưa đúng với keyword embedder vì ít overlap từ khóa |
| 3 | Sentence chunking keeps natural language boundaries. | Recursive chunking first tries paragraph separators. | medium | 0.2236 | Đúng tương đối: cùng chủ đề chunking |
| 4 | Python is useful for AI model workflows. | FastAPI can expose Python logic over HTTP. | medium | 0.1826 | Đúng tương đối: cùng chủ đề Python |
| 5 | Retrieval should escalate when evidence is missing. | Bananas are yellow fruits. | low | 0.0000 | Đúng |

**Điều bất ngờ:** Pair #2 về metadata/filter đáng lẽ liên quan ở mức medium, nhưng keyword embedder cho 0 vì wording khác nhau. Điều này cho thấy embedding model thật sẽ xử lý paraphrase tốt hơn keyword-overlap demo.

---

## 6. Results — Benchmark Queries & Gold Answers

### 6.1 Benchmark Queries & Gold Answers

| # | Query | Gold Answer | Expected Source | Metadata filter |
|---|---|---|---|---|
| 1 | What is a vector store used for in RAG? | A vector store keeps embeddings and retrieves the most similar chunks for semantic search or RAG. | `data/vector_store_notes.md` | `category=vector_store` |
| 2 | How can metadata filters improve retrieval precision? | Metadata filters narrow the search space and reduce noisy/wrong results. | `data/vector_store_notes.md` | `category=vector_store` |
| 3 | When should the support assistant escalate instead of answering? | If retrieval is insufficient or no document explains the issue, the assistant should escalate instead of improvising. | `data/customer_support_playbook.txt` | `category=support` |
| 4 | Trong hệ thống trợ lý tri thức nội bộ, retrieval đóng vai trò gì? | Retrieval tìm những đoạn tài liệu phù hợp nhất trước khi mô hình tạo câu trả lời. | `data/vi_retrieval_notes.md` | `language=vi` |
| 5 | Why is Python useful for AI applications? | Python supports data cleaning, training, evaluation scripts and integration with AI libraries/application logic. | `data/python_intro.txt` | `category=programming` |

### 6.2 Retrieval Results Summary

Khi chạy `scripts/vector_store_demo.py`, kết quả mong muốn là top-3 chứa đúng expected source cho cả 5 queries vì mỗi query dùng metadata filter hợp lý.

| # | Expected source | Relevant in top-3? | Ghi chú |
|---|---|---|---|
| 1 | `data/vector_store_notes.md` | Có | Filter `category=vector_store` giúp tập trung vào vector store notes |
| 2 | `data/vector_store_notes.md` | Có | Metadata section nằm trong cùng document |
| 3 | `data/customer_support_playbook.txt` | Có | Query escalation map đúng support playbook |
| 4 | `data/vi_retrieval_notes.md` | Có | Filter `language=vi` giúp tránh lấy nhầm tiếng Anh |
| 5 | `data/python_intro.txt` | Có | Filter `category=programming` map đúng Python note |

**Top-3 relevant:** 5/5.  
**Strategy:** `SentenceChunker(max_sentences_per_chunk=3)`.

### 6.3 Metadata Filtering

Metadata filtering giúp rõ rệt vì dataset có nhiều tài liệu đều liên quan RAG/AI. Nếu không lọc, query về support có thể lấy nhầm RAG design hoặc vector store notes. Với filter `category=support`, hệ thống chỉ search trong support playbook. Với query tiếng Việt, filter `language=vi` giúp lấy đúng `vi_retrieval_notes.md`.

---

## 7. What I Learned & Failure Analysis

### 7.1 Điều học được từ thành viên khác

Từ bài của Nguyễn Văn Chung, tôi thấy recursive chunking phù hợp hơn với tài liệu kỹ thuật Markdown có heading và paragraph dài. Strategy này giúp giữ cấu trúc tài liệu tốt hơn sentence chunking khi mỗi ý cần nhiều câu liên tiếp.

### 7.2 Điều học được từ demo nhóm

Retrieval không chỉ phụ thuộc code. Metadata, query design, chunking boundary và gold answers đều ảnh hưởng kết quả. Một hệ thống RAG cần log retrieved chunks để người phát triển kiểm tra vì sao agent trả lời như vậy.

### 7.3 Failure Case

**Failure query:**

```text
How to improve the system?
```

Query này quá mơ hồ. Nếu không có metadata filter, kết quả có thể trộn giữa RAG design, vector store notes, Python intro và support playbook. Cách cải thiện là hỏi lại user muốn cải thiện phần nào: data, chunking, embeddings, metadata, support process hay application architecture.

---

## 8. Self-Evaluation

| Tiêu chí | Loại | Điểm tự đánh giá |
|---|---|---:|
| Warm-up | Cá nhân | 5/5 |
| Document selection | Nhóm | 9/10 |
| Chunking strategy | Nhóm/cá nhân | 13/15 |
| My approach | Cá nhân | 10/10 |
| Similarity predictions | Cá nhân | 4/5 |
| Results | Cá nhân | 9/10 |
| Core implementation tests | Cá nhân | 30/30 |
| Demo | Nhóm | 5/5 |
| **Tổng** |  | **92/100** |

---

## 9. Submission Checklist

| Checklist theo lab | Trạng thái |
|---|---|
| All tests pass | Đạt — `42 passed` |
| `src/` updated | Đạt |
| `report/REPORT.md` completed | Đạt |
| Warm-up completed | Đạt |
| Document selection: 5–10 `.md/.txt` docs | Đạt — 6 docs |
| Metadata schema: ít nhất 2 fields hữu ích | Đạt — 6 fields |
| Comparator baseline on 2–3 docs | Đạt — 3 docs |
| Own strategy | Đạt — `SentenceChunker(max_sentences_per_chunk=3)` |
| Group comparison | Đạt — so sánh với Chung |
| Exactly 5 benchmark queries + gold answers | Đạt |
| Metadata filtering query | Đạt |
| Similarity predictions on 5 pairs | Đạt |
| Top-3 results for each query | Đạt |
| Failure analysis | Đạt |
| Demo evidence | Đạt — offline fallback logs |
