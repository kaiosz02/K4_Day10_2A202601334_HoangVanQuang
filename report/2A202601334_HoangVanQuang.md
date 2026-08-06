# Member Role Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin | Nội dung |
| --- | --- |
| Họ và tên | Hoàng Văn Quang |
| MSSV | 2A202601334 |
| Khóa/Lớp | K4 |
| Tên nhóm | Adge-Agent |
| Vai trò chính | Lead / Pipeline Integrator |
| Repository | `https://github.com/kaiosz02/K4_Day10_2A202601334_HoangVanQuang.git` |
| Ngày hoàn thành | 2026-08-06 |

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao | Trạng thái |
| --- | --- | --- | --- | --- |
| Orchestration baseline | `src/pipelines/phase1.py` | Settings + raw records + clean dataframe | Baseline artifacts (`metrics`, `answers`, `report`) | Hoàn thành |
| Orchestration corruption/repair | `src/pipelines/corruption_flow.py` | Baseline clean + test set cố định | Corrupted/repaired artifacts + comparison report | Hoàn thành |
| Chuẩn hóa embedding Gemini | `src/retrieval/embeddings.py`, `src/retrieval/index.py`, `src/evaluation/metrics.py`, `src/core/config.py` | `GOOGLE_API_KEY`, `embedding_model` | Embedding `gemini-embedding-2` chạy ổn định trong cả baseline/corruption flow | Hoàn thành |
| Chốt bàn giao CP4/CP6 | `cp4_handoff_report.md`, `cp6_final_handoff.md` | Kết quả thực thi pipeline | Checklist vận hành/demo có bằng chứng | Hoàn thành |

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động | Thành viên/module được hỗ trợ | Kết quả |
| --- | --- | --- |
| Hỗ trợ module retrieval/evaluation tích hợp với Gemini API key dạng nhiều token | `src/retrieval/*`, `src/evaluation/metrics.py` | Bỏ lỗi `401 UNAUTHENTICATED`, chạy thành công embedding `gemini-embedding-2` |
| Hỗ trợ chuẩn hóa report tiếng Việt | `src/observability/reporting.py` | Report CP6 có bảng delta và kết luận rõ ràng |
| Hỗ trợ cấu hình Git cho artifact runtime | `.gitignore`, dữ liệu `data/chroma/` | Tránh theo dõi file Chroma runtime và xử lý merge dở dang |

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao | Cách xác minh |
| --- | --- | --- | --- |
| Hoàn thiện pipeline baseline CP3 | `script/run_phase1.py`, `src/pipelines/phase1.py` | Sinh đủ `baseline_metrics.json`, `baseline_answers.json`, quality/freshness, `phase1_report.md` | Chạy `.\.venv\Scripts\python.exe script/run_phase1.py` thành công |
| Hoàn thiện pipeline CP5 (corrupt -> evaluate -> repair -> compare) | `script/run_corruption_flow.py`, `src/pipelines/corruption_flow.py` | Sinh đủ `corruption_log.json`, `corrupted_metrics.json`, `repaired_metrics.json`, `corruption_report.md` | Chạy `.\.venv\Scripts\python.exe script/run_corruption_flow.py` thành công |
| Tối ưu độ ổn định runtime | `src/retrieval/embeddings.py` | Có retry tự động khi gặp quota tạm thời (`429`) | Pipeline CP5 chạy lại thành công sau khi bổ sung retry |

Output tiêu biểu của vai trò tích hợp:
- Tạo được bộ artifact so sánh 3 trạng thái baseline/corrupted/repaired và chứng minh quan hệ nhân quả giữa lỗi dữ liệu và chất lượng RAG.

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết

Ghép các module rời rạc (ingestion, cleaning, retrieval, evaluation, observability) thành luồng chạy end-to-end ổn định trên Windows, dùng đúng model embedding Gemini, và giữ so sánh công bằng giữa baseline/corrupted/repaired.

### Cách triển khai

- Chuẩn hóa `GeminiEmbeddings` để gọi API thật (`models/gemini-embedding-2`) thay vì fallback ngầm sang MiniLM.
- Bổ sung logic chọn đúng API key Gemini khi `.env` chứa nhiều key phân tách bằng dấu phẩy.
- Truyền `google_api_key` tường minh vào embedding client để tránh thư viện đọc nhầm toàn chuỗi key.
- Sửa logging trong pipeline sang ASCII để tránh lỗi `UnicodeEncodeError` trên terminal cp1252.
- Thêm retry cho lỗi quota embedding (`429 RESOURCE_EXHAUSTED`) để pipeline CP5 không gãy giữa chừng.
- Sinh report CP6 có cột delta giúp demo trực quan mức suy giảm và phục hồi.

### Input, output và contract

| Thành phần | Mô tả |
| --- | --- |
| Input | `raw_records`, `papers_clean`, `test_set.json`, `Settings.paths` |
| Output | Baseline/corrupted/repaired metrics, answers, quality, freshness, reports |
| Contract cần giữ | Cùng test set cho 3 trạng thái; tách collection (`papers-baseline`, `papers-corrupted`, `papers-repaired`); không ghi đè baseline |
| Điều kiện lỗi quan trọng | Key Gemini không hợp lệ, lỗi encoding Windows, quota embedding |

### Cách xác minh

```bash
.\.venv\Scripts\python.exe script/run_phase1.py
.\.venv\Scripts\python.exe script/run_corruption_flow.py
```

- Kết quả mong đợi: sinh đủ artifact trong `data/results/`, `data/quality/`, `data/reports/`.
- Kết quả thực tế: cả hai flow chạy thành công, report comparison cập nhật đầy đủ.

## 5. Một quyết định kỹ thuật quan trọng

- Bối cảnh: cần dùng Gemini Embedding 2 theo yêu cầu nhưng `.env` chứa nhiều token khác loại.
- Các phương án đã cân nhắc:
  - Chỉ lấy key đầu tiên như ban đầu.
  - Tự động chọn key hợp lệ dạng `AIza...` và truyền tường minh vào client.
- Phương án đã chọn: chọn key `AIza...` + truyền vào `GoogleGenerativeAIEmbeddings`.
- Lý do: đảm bảo đúng định dạng Gemini API key, loại bỏ lỗi xác thực 401, không yêu cầu người dùng sửa toàn bộ file `.env`.
- Bằng chứng: call embedding test trả về vector dimension `3072`; pipeline baseline/CP5 chạy qua bước index/search thành công.

## 6. Một lỗi hoặc blocker đã xử lý

- Triệu chứng/lỗi:
  - `401 UNAUTHENTICATED` khi gọi Gemini embedding.
  - `UnicodeEncodeError` ở Windows do emoji trong `print`.
  - `429 RESOURCE_EXHAUSTED` ở bước evaluate repaired.
- Lệnh tái hiện:
  - `.\.venv\Scripts\python.exe script/run_phase1.py`
  - `.\.venv\Scripts\python.exe script/run_corruption_flow.py`
- Nguyên nhân gốc:
  - Key đầu tiên trong chuỗi `GOOGLE_API_KEY` không phải key Gemini.
  - Terminal cp1252 không encode được một số emoji Unicode.
  - Vượt quota free-tier embed request theo phút.
- Cách xử lý:
  - Sửa parser key trong `src/core/config.py`.
  - Truyền key explicit trong `GeminiEmbeddings`.
  - Đổi log emoji sang ASCII trong `phase1.py` và `corruption_flow.py`.
  - Thêm retry + sleep cho lỗi quota trong `src/retrieval/embeddings.py`.
- Cách xác minh sau khi sửa:
  - Chạy lại cả Phase 1 và Phase 2 thành công.
  - Kiểm tra artifact đầu ra và metric khớp report.
- Điều học được: với pipeline tích hợp API ngoài, cần xử lý tốt cả cấu hình key, encoding runtime và rate limit để đảm bảo reproducibility.

## 7. Hiểu biết về luồng end-to-end

1. Dữ liệu đi từ Crossref API -> lưu raw response/raw records -> cleaning thành schema chuẩn -> build embedding/index -> phục vụ retrieval/agent và evaluator.
2. `ground_truth_doc_ids` trong test set là chuẩn để đo retrieval hit; `ground_truth` dùng để đo chất lượng câu trả lời (Token F1/Judge).
3. Quality checks đo tính đúng/đủ/nhất quán schema; freshness đo độ mới của dữ liệu theo ngưỡng thời gian.
4. Phải dùng cùng test set cho baseline/corrupted/repaired để loại nhiễu, đảm bảo so sánh công bằng.
5. Repair thành công khi quality/freshness phục hồi và metric RAG quay lại gần hoặc bằng baseline.

## 8. Phân tích kết quả

### Metrics chính

| Metric/signal | Baseline | Corrupted | Repaired | Nhận xét cá nhân |
| --- | ---: | ---: | ---: | --- |
| `retrieval_hit_rate` | 100.00% | 50.00% | 100.00% | Corruption làm mất khả năng truy hồi đúng tài liệu, repair khôi phục hoàn toàn |
| `mean_token_f1` | 0.8363 | 0.3844 | 0.8363 | Chất lượng nội dung trả lời giảm sâu khi context bẩn/thiếu |
| `judge_accuracy` | 81.25% | 37.50% | 81.25% | Độ đúng của câu trả lời giảm mạnh theo chất lượng dữ liệu |
| `mean_judge_score` | 4.31 | 2.56 | 4.31 | Judge phản ánh rõ tác động corruption |
| Quality checks | Pass | Fail | Pass | Corrupted vi phạm uniqueness/summary/freshness |
| Freshness status | Fresh | Stale | Fresh | Dữ liệu repaired quay lại ngưỡng freshness kỳ vọng |

### Kết luận từ số liệu

1. Corruption (blank summary, stale date, duplicate, noise...) -> quality/freshness xấu đi -> retrieval và answer quality giảm rõ rệt.
2. Repair bằng cách rebuild lại từ raw source đáng tin cậy -> quality/freshness phục hồi -> metric RAG về baseline.

Corruption ảnh hưởng rõ nhất:
- Nhóm lỗi làm rỗng/giảm chất lượng summary và drop bản ghi mới làm mất context hữu ích, dẫn đến hit rate giảm còn 50%.

Kết quả khác kỳ vọng ban đầu:
- Trong lần chạy đầu CP5, repaired evaluation bị kẹt vì quota embedding; sau khi bổ sung retry, pipeline hoàn tất ổn định.

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất

1. Data pipeline chỉ đáng tin khi có artifact kiểm chứng được ở từng giai đoạn, không chỉ dựa vào log "done".
2. Data quality và freshness là tín hiệu sớm cho suy giảm chất lượng RAG trước khi nhìn vào metric cuối.
3. Tích hợp API ngoài (Gemini) cần chiến lược cấu hình key và retry/rate-limit ngay từ đầu.

### Nếu có thêm thời gian

- Thêm cache embedding theo query/document hash để giảm số lần gọi API, tiết kiệm quota và tăng tốc độ evaluation.
- Bổ sung dashboard nhỏ cho deltas baseline/corrupted/repaired để demo trực quan hơn.

## 10. Cam kết của thành viên

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [x] Tôi không ghi "đã chạy thành công" cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Hoàng Văn Quang  
**Ngày xác nhận:** 2026-08-06

