# Member Role Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin         | Nội dung                  |
| ------------------ | -------------------------- |
| Họ và tên       | Nguyễn Thị Việt Vinh  |
| MSSV               | 2A202601836                    |
| Khóa/Lớp         | K4            |
| Tên nhóm         | Edge-Agent (Nhóm 4)     |
| Vai trò chính    | Role 3 — RAG-agent |
| Repository         | https://github.com/kaiosz02/K4_Day10_2A202601334_HoangVanQuang |
| Ngày hoàn thành | 2026-08-06             |

---

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu (Ownership)

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao | Trạng thái |
| ------------------ | --------------------- | ---------------- | ----------------- | ---------------- |
| **Ingestion (Crossref API)** | `src/ingestion/crossref.py`<br>(`fetch_source_records`, `parse_crossref_payload`, `load_raw_records`) | Crossref REST API (`query`, `filter`, `rows`) | `data/raw/crossref_response.json`<br>`data/raw/crossref_records.json`<br>`list[PaperRecord]` | Hoàn thành |
| **Data Cleaning & Structuring** | `src/ingestion/cleaning.py`<br>(`build_clean_dataframe`) | `list[PaperRecord]`, `run_date` | `data/clean/papers_clean.csv`<br>`data/clean/papers_clean.json`<br>`clean DataFrame` | Hoàn thành |
| **Data Corruption Simulation** | `src/ingestion/corruption.py`<br>(`corrupt_clean_dataframe`) | Baseline clean DataFrame | `data/clean/papers_clean_corrupted.csv`<br>`data/results/corruption_log.json`<br>`corrupted DataFrame` | Hoàn thành |
| **Data Repair Execution** | `src/ingestion/crossref.py` & `cleaning.py` | Authoritative Raw Source (`crossref_records.json`) | `data/clean/papers_clean_repaired.csv`<br>`repaired DataFrame` | Hoàn thành |

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động | Thành viên/module được hỗ trợ | Kết quả |
| --------- | ------------------------------------ | ------- |
| Tích hợp luồng Data Ingestion vào Baseline Pipeline | Member 1 (Hoàng Văn Quang) / `src/pipelines/phase1.py` | Cung cấp dữ liệu sạch `papers_clean.csv` đồng bộ cho bước Indexing và Testing |
| Tích hợp luồng Repair từ Raw Snapshot | Member 1 / `src/pipelines/corruption_flow.py` | Khôi phục tự động dữ liệu từ `crossref_records.json` không sửa tay |

---

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao | Cách xác minh |
| --------------------------- | ----------------------------- | ------------------------- | ----------------------- |
| Gọi API & Parse payload Crossref | `src/ingestion/crossref.py` | Lấy 24 bài báo thật, parse thành `PaperRecord` schema | Đọc file `data/raw/crossref_records.json` |
| Làm sạch & định dạng dữ liệu | `src/ingestion/cleaning.py` | Loại bỏ thẻ XML/HTML `<jats:p>`, tạo `text_for_embedding`, tính `age_days` | Kiểm tra file `data/clean/papers_clean.csv` |
| Giả lập Data Corruption | `src/ingestion/corruption.py` | Tạo 6 dạng lỗi (xóa bài mới, blank summary, text noise, truncate title, stale date, duplicate) | Kiểm tra `papers_clean_corrupted.csv` và `corruption_log.json` |
| Tự động Phục hồi Dữ liệu | `src/ingestion/cleaning.py` & `crossref.py` | Tái tạo DataFrame sạch từ raw snapshot ban đầu | Kiểm tra `papers_clean_repaired.csv` |

---

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết
1. Thu thập dữ liệu bài báo học thuật từ Crossref REST API với tiêu chuẩn schema thống nhất (`PaperRecord`).
2. Làm sạch các ký tự nhiễu và thẻ HTML/XML (`<jats:p>`), định dạng ngày tháng xuất bản chuẩn ISO `YYYY-MM-DD`, tính toán độ tươi dữ liệu (`age_days`), và tạo cấu trúc `text_for_embedding` không bị lặp rác.
3. Tạo ra dữ liệu lỗi (Data Corruption) có kiểm soát để phục vụ đo lường suy giảm RAG agent và đánh giá tính năng kiểm định Data Quality & Freshness Monitoring.
4. Cung cấp cơ chế tự động khôi phục dữ liệu (Data Repair) từ nguồn raw đáng tin cậy.

### Cách triển khai Kỹ thuật

```python
# 1. Strip XML/HTML tags cho tóm tắt bài báo
def _clean_abstract(raw_abstract: str) -> str:
    if not raw_abstract:
        return ""
    cleaned = re.sub(r"<[^>]+>", " ", raw_abstract)
    return normalize_whitespace(cleaned)

# 2. Xây dựng text_for_embedding chuẩn xác không lặp vô ích
text_for_embedding = f"Title: {title}. Summary: {summary}"

# 3. Mô phỏng data corruption ghi log đầy đủ
log_payload = {
    "timestamp": datetime.now().isoformat(),
    "total_rows_before": total_orig,
    "total_rows_after": len(corrupted_df),
    "corruptions": corruption_log,
}
```

### Input, Output và Contract

| Thành phần | Mô tả |
| ---------- | ------ |
| **Input** | Query API Crossref (`query`, `filter`, `max_results=24`), raw response JSON |
| **Output** | `PaperRecord` dataclass, `papers_clean.csv`, `papers_clean_corrupted.csv`, `corruption_log.json` |
| **Contract** | `paper_id` unique & not null; `text_for_embedding` chứa đầy đủ Title + Summary; `age_days` tính từ `run_date` |
| **Xử lý lỗi** | Tự động retry khi gặp HTTP status `429` (Rate limit) hoặc `503` (Service Unavailable); hỗ trợ fallback dataset offline nếu API gián đoạn |

### Cách xác minh bằng lệnh thực tế

```bash
# 1. Kiểm tra nghiệm thu Ingestion & Clean Data
python script/verify_ingestion_and_config.py

# 2. Thực thi Baseline Pipeline (Pha 1)
python script/run_phase1.py

# 3. Thực thi Corruption & Repair Pipeline (Pha 2)
python script/run_corruption_flow.py
```

* **Kết quả thực tế:**
  * Raw dataset: 24 bài báo được fetch và parse chính xác.
  * Clean dataset: 24 dòng không trùng lặp, 0 null paper_id, 0 null title.
  * Corruption: 6 loại lỗi được ghi nhận đầy đủ vào `data/results/corruption_log.json`.
  * Repair: Tự động tải lại từ raw snapshot, làm sạch và phục hồi 100% số lượng dòng.

---

## 5. Một quyết định kỹ thuật quan trọng

* **Bối cảnh:** Dữ liệu tóm tắt (abstract) nhận về từ Crossref API thường chứa các thẻ XML/HTML dạng `<jats:p>`, `<jats:title>`, hoặc khoảng trắng dư thừa.
* **Các phương án đã cân nhắc:**
  1. *Phương án A*: Giữ nguyên văn bản chứa thẻ XML/HTML để lưu vào DataFrame và Vector Store.
  2. *Phương án B*: Sử dụng Regular Expression `re.sub(r"<[^>]+>", " ", raw_abstract)` và `normalize_whitespace` để làm sạch toàn bộ thẻ markup trước khi tạo `text_for_embedding`.
* **Phương án đã chọn:** **Phương án B**.
* **Lý do:** Thẻ XML/HTML tạo ra các token nhiễu không mang giá trị ngữ nghĩa, làm giảm độ tương đồng Cosine Similarity của model MiniLM embedding và lãng phí context window của LLM.
* **Bằng chứng:** Sau khi áp dụng Phương án B, chỉ số `retrieval_hit_rate` trên Baseline Phase đạt tuyệt đối **100.00%** và `mean_token_f1` đạt **0.8363**.

---

## 6. Một lỗi hoặc blocker đã xử lý

* **Triệu chứng/lỗi nguyên văn:**
  `ERROR: Failed to build 'pandas' when installing build dependencies for pandas / Cannot compile Python.h`
* **Bước tái hiện:** Chạy `python -m pip install -e .` trên Windows với môi trường virtualenv được khởi tạo từ Python bản MSYS2/MinGW.
* **Nguyên nhân gốc:** Trình quản lý pip cố gắng biên dịch `pandas` và `numpy` từ mã nguồn tarball do không khớp định dạng bánh xe prebuilt wheel (`win_amd64`) trên Windows.
* **Cách xử lý:** 
  1. Ghim phiên bản tương thích `pandas==2.2.2` và `numpy<2.0.0` trong `pyproject.toml` và `requirements.txt`.
  2. Tạo môi trường `.venv` chính thức bằng Windows Native Python 3.11 (`C:\Users\dungt\AppData\Local\Programs\Python\Python311\python.exe`).
* **Cách xác minh sau khi sửa:** Lệnh `.\.venv\Scripts\pip.exe install -e .` hoàn tất cài đặt toàn bộ gói phụ thuộc trong 5 giây mà không xảy ra lỗi biên dịch C.

---

## 7. Hiểu biết về luồng end-to-end

1. **Dữ liệu đi từ Crossref đến vector index như thế nào?**
   Dữ liệu raw từ Crossref API (`raw_records_json`) -> Parse & Clean (`build_clean_dataframe`) -> Tạo `text_for_embedding` -> Vectorize bằng `MiniLMEmbeddings` -> Nạp vào ChromaDB Persistent Index collection `papers-baseline`.
2. **Evaluation set và ground-truth document IDs dùng để đo retrieval/answer quality ra sao?**
   Mỗi mẫu câu hỏi trong Test set chứa `ground_truth_doc_ids`. Khi Agent truy vấn, hệ thống so sánh danh sách `retrieved_doc_ids` với `ground_truth_doc_ids` để tính **Retrieval Hit Rate**. Câu trả lời sinh ra được so sánh với `ground_truth` để tính **Token F1** và **Judge Accuracy**.
3. **Quality checks khác freshness monitoring ở điểm nào?**
   Quality checks kiểm soát tính toàn vẹn của dữ liệu tại thời điểm nạp (null IDs, trùng lặp, rỗng summary). Freshness monitoring kiểm soát độ tươi dữ liệu theo thời gian (`age_days` so với SLA threshold `180` ngày).
4. **Vì sao phải dùng cùng test set cho baseline, corrupted và repaired?**
   Giữ nguyên Test set cố định (Frozen Baseline Testset) để đảm bảo điều kiện thí nghiệm đồng nhất (cùng một đề thi), giúp số liệu so sánh phản ánh chính xác tác động của dữ liệu bẩn và hiệu quả của quá trình repair.
5. **Repair được xem là thành công dựa trên artifact và metric nào?**
   Repair thành công khi: (1) Artifact `papers_clean_repaired.csv` và collection `papers-repaired` được tạo lại từ raw source; (2) Data Quality Checks báo `PASSED ✅`; (3) Chỉ số `retrieval_hit_rate` phục hồi về **100.00%** và `mean_token_f1` phục hồi về **0.8363** (ngang mức Baseline).

---

## 8. Phân tích kết quả

### Metrics chính từ thực nghiệm dự án

| Metric / Signal | Baseline | Corrupted (Dữ liệu lỗi) | Repaired (Phục hồi) | Nhận xét cá nhân |
| --------------- | -------: | ----------------------: | ------------------: | ---------------- |
| `retrieval_hit_rate` | **100.00%** | **50.00%** | **100.00%** | Dữ liệu bẩn làm sụt giảm 50% khả năng truy xuất đúng bài báo. |
| `mean_token_f1` | **0.8363** | **0.3892** | **0.8363** | Token F1 giảm hơn một nửa do thông tin tóm tắt bị mất/bị nhiễu. |
| `judge_accuracy` | **75.00%** | **37.50%** | **75.00%** | LLM Judge phát hiện chính xác câu trả lời sai lệch khi RAG thiếu thông tin. |
| `mean_judge_score` | **4.00 / 5** | **2.50 / 5** | **4.00 / 5** | Điểm số đánh giá trung bình phục hồi hoàn toàn sau khi repair. |
| Data Quality Status | **PASSED ✅** | **FAILED ❌** | **PASSED ✅** | Phát hiện chính xác 4 dòng blank summary và dòng trùng lặp. |
| Freshness Status | **FRESH ✅** | **STALE ⚠️** | **FRESH ✅** | Phát hiện chính xác 5 dòng bị dời ngày xuất bản về năm 2020. |

### Kết luận từ số liệu

1. **Dữ liệu bị làm hỏng (Data Corruption)** -> Báo cáo Quality Fail (`null_summaries`, `stale_rows`) -> Hit Rate rớt từ 100% xuống 50% và Token F1 giảm từ 0.8363 xuống 0.3892.
2. **Khôi phục từ Nguồn Raw (Repair Action)** -> Báo cáo Quality báo xanh `PASSED ✅` -> Hit Rate và F1 phục hồi 100% về mức Baseline.

---

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất
1. Quản lý luồng dữ liệu thô (Raw Data Ingestion) bằng các bản snapshot cố định là chìa khóa để có thể tự động khôi phục dữ liệu (Automated Data Repair) mà không phải sửa tay thủ công.
2. Làm sạch văn bản (Data Cleaning) tỉ mỉ (strip HTML/XML, chuẩn hóa khoảng trắng) có ảnh hưởng trực tiếp đến chất lượng vector embedding và độ chính xác của RAG Agent.
3. Data Observability (Quality Checks + Freshness Monitoring) đóng vai trò là "hệ thống cảnh báo sớm" giúp phát hiện sự cố dữ liệu trước khi dữ liệu bẩn làm hỏng kết quả của mô hình AI.

---

## 10. Cam kết của thành viên

Đánh dấu sau khi tự kiểm tra:

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [x] Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Nguyễn Thị Việt Vinh  
**Ngày xác nhận:** 2026-08-06
