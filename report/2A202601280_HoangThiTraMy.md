# Member Role Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin         | Nội dung                  |
| ------------------ | -------------------------- |
| Họ và tên       | Hoàng Thị Trà My           |
| MSSV               | 2A202601280                |
| Khóa/Lớp         | K4                         |
| Tên nhóm         | Edge-Agent                   |
| Vai trò chính    | Ingestion & Data Cleaning Specialist |
| Repository         | https://github.com/kaiosz02/K4_Day10_2A202601334_HoangVanQuang.git |
| Ngày hoàn thành | 2026-08-06                 |

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao  | Trạng thái                                 |
| ------------------ | --------------------- | ---------------- | ----------------- | -------------------------------------------- |
| Crossref Ingestion | `src/ingestion/crossref.py` (`fetch_source_records`, `parse_crossref_payload`, `load_raw_records`) | `Settings` (source_query, source_filter, max_results) | `data/raw/crossref_response.json`, `data/raw/crossref_records.json` | Hoàn thành |
| Data Cleaning & Normalization | `src/ingestion/cleaning.py` (`clean_text`, `build_clean_dataframe`, `save_clean_dataframe`) | `list[PaperRecord]`, `run_date` | `data/clean/papers_clean.csv`, `data/clean/papers_clean.json` | Hoàn thành |

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động                         | Thành viên/module được hỗ trợ | Kết quả                    |
| ------------------------------------ | ------------------------------------ | ---------------------------- |
| Tích hợp Script Chạy Ingestion | Quang - phụ trách Pipeline (`phase1.py`) | Tạo `script/run_ingestion.py` giúp chạy độc lập & kiểm thử nhanh luồng lấy/làm sạch dữ liệu |
| Cấu hình Query & Filter | Team Core Config (`src/core/config.py`) | Kiểm thử và tinh chỉnh `source_query` ("LLM Agentic robotics") và `source_filter` |

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao       | Cách xác minh         |
| --------------------------- | ----------------------------- | ------------------------- | ----------------------- |
| Gọi Crossref API với Retry & Backoff | [src/ingestion/crossref.py] | [crossref_response.json],[crossref_records.json] | `.\.venv\Scripts\python.exe script/run_ingestion.py` |
| Xóa thẻ HTML/XML, chuẩn hóa Text, tính Freshness & Embed Column | [src/ingestion/cleaning.py] | [papers_clean.csv],[papers_clean.json] | Kiểm tra kích thước file & Schema Dataframe (24 dòng x 16 cột) |

Nêu một output cụ thể mà phần việc của bạn tạo ra hoặc giúp xác minh:

- Đã thu thập và làm sạch thành công **24 bài báo khoa học chuẩn** từ Crossref API.
- Đã tạo cột `text_for_embedding` chuẩn hóa dưới dạng: `Title: [title] | Authors: [authors_joined] | Summary: [summary]` hoàn toàn sạch bóng các thẻ XML (`<jats:p>`, `<b>`, `<i>`) và loại bỏ các bản ghi rác.

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết

Thu thập metadata bài báo từ nguồn mở Crossref REST API công khai. Xử lý các thách thức:
1. API có thể trả về lỗi tạm thời HTTP `429` (Rate Limit) hoặc `503` (Service Unavailable).
2. Dữ liệu thô từ Crossref chứa nhiều thẻ XML/HTML (`<jats:p>`, `<b>`, `<i>`, `<title>`) và HTML entities (`&amp;`, `&lt;`).
3. Cấu trúc tác giả và danh mục bị lồng ghép (nested dict/list).
4. Cần chuẩn hóa ngày xuất bản ISO `YYYY-MM-DD`, tính `age_days` phục vụ data observability và xây dựng cột biểu diễn ngữ nghĩa `text_for_embedding` cho mô hình RAG.

### Cách triển khai

1. **`src/ingestion/crossref.py`**:
   - Hàm `fetch_source_records`: Sử dụng `requests.get()` truyền header `User-Agent` hợp lệ. Tích hợp vòng lặp Retry đến 5 lần với thuật toán **Exponential Backoff** (`wait_time = backoff_factor * 2^attempt`).
   - Lưu trữ nguyên văn HTTP JSON response thô vào `settings.paths.raw_api_response` để phục vụ công tác kiểm toán nguồn (data audit).
   - Hàm `parse_crossref_payload`: Trích xuất DOI (làm `paper_id` ổn định), title, abstract/description, author, subject, dates, URLs. Lọc bỏ ngay lập tức nếu thiếu `title` hoặc `summary`.
   - Lưu danh sách bản ghi đã parse phẳng vào `settings.paths.raw_records_json`.

2. **`src/ingestion/cleaning.py`**:
   - Hàm `clean_text`: Dùng `html.unescape()` để giải mã ký tự đặc biệt và `re.sub(r'<[^>]+>', ' ', text)` để xóa bỏ hoàn toàn các thẻ HTML/XML, sau đó chuẩn hóa khoảng trắng dư thừa.
   - Hàm `build_clean_dataframe`:
     - Lọc bỏ rác: Drop bản ghi rỗng tiêu đề hoặc có `summary` ngắn dưới 100 ký tự (`len(summary) < 100`).
     - Gộp danh sách tác giả thành chuỗi `authors_joined` phân cách bởi dấu phẩy (mặc định `"Unknown"` nếu rỗng).
     - Gộp mảng danh mục thành `categories_joined` (mặc định `"General"` nếu rỗng).
     - Đưa ngày `published` về dạng ISO `YYYY-MM-DD`, tính `age_days = (run_date.date() - published_date.date()).days` (nếu ngày tương lai thì gán về `0`).
     - Tạo cột ngữ nghĩa `text_for_embedding = f"Title: {title} | Authors: {authors_joined} | Summary: {summary}"`.
     - Loại bỏ trùng lặp theo `paper_id` (`drop_duplicates`) và sắp xếp bài báo theo ngày `published` mới nhất giảm dần.
   - Hàm `save_clean_dataframe`: Xuất kết quả ra cả 2 file `papers_clean.csv` và `papers_clean.json`.

### Input, output và contract

| Thành phần                   | Mô tả                                     |
| ------------------------------ | ------------------------------------------- |
| Input                          | `Settings` (chứa `source_query`, `source_filter`, `max_results`, `paths`) |
| Output                         | `data/raw/crossref_response.json`, `data/raw/crossref_records.json`, `data/clean/papers_clean.csv`, `data/clean/papers_clean.json` |
| Module phụ thuộc             | `src/core/config.py` (`Settings`, `Paths`) |
| Module sử dụng output        | `src/retrieval/index.py` (nạp dữ liệu vào ChromaDB Vector Store) |
| Điều kiện lỗi cần xử lý | Lỗi HTTP 429/503 từ API Crossref, dữ liệu XML lồng sâu, bài báo rỗng abstract hoặc bị trùng DOI |

### Cách xác minh

```bash
.\.venv\Scripts\python.exe script/run_ingestion.py
```

- **Kết quả mong đợi:** Lấy về 24 bản ghi thô từ Crossref API, làm sạch không còn thẻ HTML/XML, xuất ra CSV và JSON đầy đủ 16 cột.
- **Kết quả thực tế:** Chạy thành công 100%, thu thập 24 bản ghi sạch với query `"LLM Agentic robotics"`.
- **Artifact/log:** `data/raw/crossref_response.json`, `data/raw/crossref_records.json`, `data/clean/papers_clean.csv`, `data/clean/papers_clean.json`.

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Cần chọn phương án tạo `paper_id` duy nhất và ổn định cho từng bài báo thu thập từ Crossref API.
- **Các phương án đã cân nhắc:**
  1. *Phương án 1:* Sinh chuỗi UUID hoặc MD5 hash ngẫu nhiên cho mỗi lần chạy pipeline.
  2. *Phương án 2:* Sử dụng trực tiếp mã DOI (`item.get("DOI")`) làm `paper_id`.
- **Phương án đã chọn:** Phương án 2 (Dùng DOI làm `paper_id`).
- **Lý do:** DOI (Digital Object Identifier) là tiêu chuẩn định danh vĩnh viễn toàn cầu của các công bố học thuật. Sử dụng DOI giúp dữ liệu có tính chất **idempotent** (chạy lại pipeline nhiều lần vẫn ra đúng ID đó), hỗ trợ deduplicate chính xác 100% và giúp các bước quan sát dữ liệu (Data Observability / Lineage) dễ dàng truy vết về bài báo gốc trên Crossref.

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:** API Crossref trả về lỗi `HTTP 429 Too Many Requests` khi gửi nhiều yêu cầu liên tục, hoặc dữ liệu abstract chứa các thẻ XML lồng nhau như `<jats:p>`, `<b>`, `<title>Abstract</title>` làm bẩn nội dung text đưa vào embedding model.
- **Lệnh hoặc bước tái hiện:** Chạy thử hàm gọi API không có header `User-Agent` và không dừng nghỉ khi gặp rate limit.
- **Nguyên nhân gốc:** Crossref API giới hạn băng thông với các request không khai báo `User-Agent` rõ ràng. Ngoài ra dữ liệu abstract từ thư viện JATS XML chứa thẻ định dạng chưa được xử lý.
- **Cách xử lý:**
  1. Thêm `User-Agent: DataPipelineObservabilityLab/1.0 (mailto:lab@example.com)` vào header request.
  2. Xây dựng cơ chế retry với Exponential Backoff (`wait_time = backoff_factor * 2^attempt`).
  3. Viết hàm `clean_text` kết hợp `html.unescape()` và regex `re.sub(r'<[^>]+>', ' ', text)` để quét sạch tất cả các thẻ XML/HTML.
- **Cách xác minh sau khi sửa:** Chạy lại `script/run_ingestion.py`, API phản hồi thành công và văn bản trong `text_for_embedding` hoàn toàn sạch sẽ.
- **Điều học được:** Khi làm việc với API công khai, bắt buộc phải có cơ chế retry/backoff và header định danh. Dữ liệu thô từ bên thứ ba luôn phải trải qua bước làm sạch (cleaning) cẩn thận trước khi đưa vào các mô hình AI/LLM.

## 7. Hiểu biết về luồng end-to-end

1. **Dữ liệu đi từ Crossref đến vector index như thế nào?**
   - API Crossref $\rightarrow$ Raw HTTP JSON (`crossref_response.json`) $\rightarrow$ Raw Records (`crossref_records.json`) $\rightarrow$ Clean DataFrame (`papers_clean.csv`/`json`) $\rightarrow$ Sinh Vector Embeddings qua `sentence-transformers/all-MiniLM-L6-v2` $\rightarrow$ Nạp và lưu trữ trong ChromaDB Vector Store.
2. **Evaluation set và ground-truth document IDs dùng để đo retrieval/answer quality ra sao?**
   - Evaluation set chứa danh sách câu hỏi test, đáp án chuẩn (`ground_truth`) và danh sách ID bài báo liên quan (`ground_truth_doc_ids`). Khi RAG agent truy vấn, hệ thống so sánh các `paper_id` được tìm ra với `ground_truth_doc_ids` để tính **Retrieval Hit Rate**. Đáp án agent sinh ra được so sánh với `ground_truth` qua **Token F1** và **LLM-as-a-judge** score.
3. **Quality checks khác freshness monitoring ở điểm nào trong bài lab?**
   - **Quality checks**: Kiểm tra tính toàn vẹn của dữ liệu (số lượng bản ghi, null check ở các trường bắt buộc, độ dài tối thiểu của tóm tắt, trùng lặp ID).
   - **Freshness monitoring**: Kiểm tra độ tươi mới của dữ liệu dựa trên ngày xuất bản (`published`) và tuổi bài báo (`age_days`), cảnh báo nếu bài báo quá cũ so với ngưỡng cho phép (180 ngày).
4. **Vì sao phải dùng cùng test set cho baseline, corrupted và repaired?**
   - Để đảm bảo tính công bằng và nhất quán tuyệt đối (apples-to-apples comparison). Việc giữ nguyên bộ câu hỏi và đáp án chuẩn giúp đo lường chính xác mức độ sụt giảm chất lượng agent khi dữ liệu bị hư hỏng (corrupted) và mức độ phục hồi khi được sửa chữa (repaired).
5. **Repair được xem là thành công dựa trên artifact và metric nào?**
   - Repair thành công khi:
     - Data Quality & Freshness reports đều báo `Pass`.
     - Các chỉ số đánh giá RAG agent (Retrieval Hit Rate, Token F1, Judge Score) trong `repaired_metrics.json` phục hồi về mức tương đương hoặc cao hơn so với `baseline_metrics.json`.

## 8. Phân tích kết quả

### Metrics chính

| Metric/signal          | Baseline | Corrupted | Repaired | Nhận xét của cá nhân |
| ---------------------- | -------: | --------: | -------: | ------------------------- |
| `retrieval_hit_rate` |    1.00 |      0.42 |     1.00 | Dữ liệu rác làm giảm khả năng tìm đúng bài báo |
| `mean_token_f1`      |    0.78 |      0.35 |     0.78 | Chất lượng câu trả lời giảm mạnh khi summary bị lỗi/nhiễu |
| `judge_accuracy`     |    0.85 |      0.40 |     0.85 | LLM judge đánh giá kém khi ngữ cảnh bị khuyết |
| `mean_judge_score`   |    4.20 |      2.10 |     4.20 | Điểm tổng thể sụt giảm nặng do dữ liệu corrupted |
| Quality checks         |    PASS |      FAIL |     PASS | Quality check phát hiện được các dòng rỗng/trùng |
| Freshness status       |   FRESH |     STALE |    FRESH | Cảnh báo đúng khi cố tình làm cũ ngày xuất bản |

### Kết luận từ số liệu

1. **[Data corruption]** (Xóa summary, làm cũ ngày, nạp rác) $\rightarrow$ **[quality/freshness signal báo FAIL/STALE]** $\rightarrow$ **[retrieval_hit_rate giảm từ 1.00 xuống 0.42, token_f1 giảm từ 0.78 xuống 0.35]**.
2. **[Repair action]** (Tải lại dữ liệu chuẩn từ Crossref raw source) $\rightarrow$ **[quality/freshness signal phục hồi PASS/FRESH]** $\rightarrow$ **[agent metrics phục hồi hoàn toàn về mức 1.00 hit rate và 0.78 F1]**.

- **Corruption nào ảnh hưởng rõ nhất và vì sao?**
  - Corruption làm trống tóm tắt (`blank summary`) và truncated title ảnh hưởng nặng nhất đến RAG agent vì mô hình embedding không thể tạo vector biểu diễn chính xác, dẫn đến retrieval thất bại hoàn toàn.

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất

1. **Về Data Pipeline**: Cần xây dựng pipeline có tính idempotency, lưu trữ đầy đủ raw artifacts để có thể khôi phục (repair) dữ liệu bất kỳ lúc nào.
2. **Về Data Quality/Observability**: Data Observability (Quality checks & Freshness monitoring) là lá chắn quan trọng giúp phát hiện lỗi dữ liệu trước khi dữ liệu xấu đi vào mô hình AI.
3. **Về ảnh hưởng của Data đến RAG Agent**: Chất lượng của RAG Agent phụ thuộc trực tiếp 100% vào chất lượng dữ liệu ("Garbage in, Garbage out"). Sửa dữ liệu đúng cách giúp khôi phục hoàn toàn hiệu năng hệ thống.

### Nếu có thêm thời gian

- Phát triển thêm bộ quy tắc tự động phát hiện và loại bỏ ngôn ngữ không phải tiếng Anh trong tóm tắt bài báo, đồng thời tối ưu tốc độ gọi API bằng cách xử lý bất đồng bộ (async request).

## 10. Cam kết của thành viên

Đánh dấu sau khi tự kiểm tra:

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [x] Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Hoàng Thị Trà My
**Ngày xác nhận:** 2026-08-06
