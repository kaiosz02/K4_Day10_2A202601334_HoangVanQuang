# Group Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin bài nộp

| Thông tin | Nội dung |
| --- | --- |
| Khóa/Lớp | K4 |
| Tên nhóm | Adge-Agent |
| Repository | `D:\thuc_hanh_vinAI\K4_Day10_2A202601334_HoangVanQuang` |
| Ngày hoàn thành | 2026-08-06 |

### Thành viên và phân công

| STT | Họ và tên | MSSV | Vai trò chính | Module/deliverable sở hữu |
| --: | --- | --- | --- | --- |
| 1 | Hoàng Văn Quang | 2A202601334 | Lead / Pipeline Integrator | `src/pipelines/phase1.py`, `src/pipelines/corruption_flow.py`, tích hợp embedding Gemini |
| 2 | Nguyễn Thị Việt Vinh | 2A202601836 | Data foundation & recovery | `src/ingestion/crossref.py`, `src/ingestion/cleaning.py`, `src/ingestion/corruption.py` |
| 3 | Hoàng Thị Trà My | 2A202601290 | RAG & agent owner | `src/retrieval/` (index, search, agent) |
| 4 | Tạ Hồng Quí | 2A202601538 | Evaluation & observability | `src/evaluation/testset.py`, `src/observability/quality.py`, `src/observability/reporting.py` |

## 2. Tóm tắt kết quả

Nhóm đã hoàn thiện đầy đủ hai luồng chính: baseline pipeline (`script/run_phase1.py`) và corruption/repair flow (`script/run_corruption_flow.py`). Ở baseline, hệ thống tạo đủ artifact từ raw, clean, embedding index, test set, metrics, quality/freshness đến report markdown. Kết quả baseline đạt `retrieval_hit_rate=1.0`, `mean_token_f1=0.8363`, `judge_accuracy=0.8125`, `mean_judge_score=4.3125`.

Trong pha corruption, nhóm áp dụng 6 kịch bản lỗi dữ liệu có kiểm soát (drop latest records, blank summary, inject noise, truncate title, stale dates, duplicate rows) và ghi log đầy đủ trong `data/results/corruption_log.json`. Các lỗi này làm chất lượng RAG suy giảm mạnh: hit rate giảm từ 100% xuống 50%, token F1 giảm từ 0.8363 xuống 0.3844, judge accuracy giảm từ 81.25% xuống 37.50%.

Ở pha repair, nhóm khôi phục lại dữ liệu từ raw source thay vì sửa tay kết quả; sau đó rebuild index và evaluate lại trên cùng test set. Kết quả repaired phục hồi về baseline cho cả bốn chỉ số chính. Blocker quan trọng nhất là tích hợp Gemini Embedding 2 trong điều kiện key/encoding/quota runtime, đã được xử lý bằng chuẩn hóa parser key, truyền key tường minh, đổi log ASCII và thêm retry cho lỗi quota.

## 3. Kiến trúc và luồng dữ liệu

### Luồng end-to-end

```text
Crossref API
    -> raw response/raw records
    -> cleaning và data modeling
    -> embedding + ChromaDB index
    -> evaluation baseline
    -> quality/freshness reports
    -> corruption
    -> re-index và re-evaluate
    -> repair từ dữ liệu nguồn
    -> comparison report
```

### Trách nhiệm của từng khối

| Khối | Input | Xử lý chính | Output/artifact | Owner |
| --- | --- | --- | --- | --- |
| Ingestion | Crossref API payload | Fetch, retry/backoff, parse về `PaperRecord` | `data/raw/crossref_response.json`, `data/raw/crossref_records.json` | Nguyễn Thị Việt Vinh |
| Cleaning | Raw records | Normalize, dedupe, parse date, tạo `text_for_embedding`, `age_days` | `data/clean/papers_clean.csv`, `data/clean/papers_clean.json` | Nguyễn Thị Việt Vinh |
| Embedding/index | Clean dataframe | Embed bằng `gemini-embedding-2`, build Chroma collections | `data/embeddings/*.json`, `data/chroma/` | Hoàng Thị Trà My + Hoàng Văn Quang |
| Evaluation | Test set + index | Answer question, tính retrieval/judge metrics | `data/results/*_metrics.json`, `*_answers.json` | Tạ Hồng Quí |
| Observability | Clean/corrupted/repaired data | Quality checks + freshness report + markdown report | `data/quality/*`, `data/reports/*` | Tạ Hồng Quí |
| Corruption/repair | Baseline clean + raw records | Tạo corruption có log, rebuild, repair từ raw | `data/results/corruption_log.json`, corrupted/repaired artifacts | Nguyễn Thị Việt Vinh + Hoàng Văn Quang |
| Orchestration | Settings + toàn bộ module | Điều phối thứ tự chạy end-to-end | Flow baseline/corruption chạy ổn định | Hoàng Văn Quang |

## 4. Cách tái hiện kết quả

### Cấu hình không chứa secret

| Biến/cấu hình | Giá trị sử dụng |
| --- | --- |
| `LLM_PROVIDER` | `gemini` |
| `LLM_MODEL` | `gemini-3.1-flash-lite` |
| Embedding model | `gemini-embedding-2` |
| Số lượng Crossref records | 24 |
| Retrieval `top_k` | 4 |
| Freshness threshold | 180 ngày |
| Random seed | Không cố định seed toàn cục |

### Lệnh cài đặt

```bash
python -m pip install -e .
```

### Lệnh chạy

```bash
python script/run_phase1.py
python script/run_corruption_flow.py
```

### Kết quả tái hiện

| Lệnh | Trạng thái | Thời điểm chạy gần nhất | Bằng chứng |
| --- | --- | --- | --- |
| Baseline pipeline | Thành công | 2026-08-06 16:09 | `data/results/baseline_metrics.json`, `data/reports/phase1_report.md` |
| Corruption flow | Thành công | 2026-08-06 16:44 | `data/results/corrupted_metrics.json`, `data/results/repaired_metrics.json`, `data/reports/corruption_report.md` |

## 5. Ingestion, cleaning và data contract

### Nguồn dữ liệu

| Thuộc tính | Giá trị |
| --- | --- |
| Source | Crossref REST API (`https://api.crossref.org/works`) |
| Query/filter | Query: `LLM Agentic robotics`; Filter: `from-pub-date:<động theo now-180d>,has-abstract:true` |
| Thời điểm lấy dữ liệu | Trong lần chạy pipeline gần nhất ngày 2026-08-06 |
| Số record nhận được | 24 |
| Cơ chế retry/backoff | Có retry cho lỗi rate-limit/server tạm thời (429/503) |

### Raw và clean schema

| Trường | Kiểu dữ liệu | Bắt buộc? | Ý nghĩa | Xử lý khi thiếu/sai |
| --- | --- | --- | --- | --- |
| `paper_id` | string | Có | Định danh tài liệu ổn định | Loại bỏ hoặc không cho qua nếu null/trùng |
| `title` | string | Có | Tiêu đề bài báo | Làm sạch whitespace; báo lỗi quality nếu thiếu |
| `summary` | string | Có | Tóm tắt để tạo ngữ cảnh | Làm sạch; kiểm tra `short_summaries` |
| `authors_joined` | string | Có | Chuỗi tác giả phục vụ QA | Chuẩn hóa join từ list authors |
| `categories_joined` | string | Có | Chuỗi category phục vụ QA | Chuẩn hóa join từ list categories |
| `published` | string/date | Có | Ngày xuất bản | Parse date; dùng tính `age_days` |
| `age_days` | int | Có | Số ngày tính từ ngày chạy | Dùng cho freshness checks |
| `text_for_embedding` | string | Có | Nội dung đầu vào embedding | Ghép title/summary/authors/categories theo contract |

### Quy tắc cleaning

| Quy tắc | Quality dimension liên quan | Số record bị tác động | Cách xác minh |
| --- | --- | ---: | --- |
| Chuẩn hóa text và bỏ giá trị rỗng/không hợp lệ | Completeness/Validity | Theo từng lần chạy | Kiểm tra `quality_report_baseline` |
| Dedupe theo `paper_id` | Uniqueness | Theo từng lần chạy | `is_id_unique` trong quality report |
| Tính `age_days` từ `published` | Freshness readiness | Toàn bộ records | `freshness_report*.json` |
| Tạo `text_for_embedding` theo schema cố định | Consistency | Toàn bộ records | Kiểm tra manifest embeddings + sample clean rows |

Nhóm tạo `text_for_embedding` từ các trường nội dung chính, giữ `paper_id` ổn định để liên kết xuyên suốt raw -> clean -> index -> evaluation, và dùng `age_days` làm tín hiệu freshness.

## 6. Evaluation setup

| Thành phần | Cấu hình thực tế |
| --- | --- |
| Số câu hỏi | 16 |
| Các `question_type` | `summary`, `authors`, `date`, `categories` |
| Ground-truth document ID | Lấy từ `paper_id` thật trong clean data |
| Embedding model | `gemini-embedding-2` |
| Vector store/collection | ChromaDB với `papers-baseline`, `papers-corrupted`, `papers-repaired` |
| Retrieval `top_k` | 4 |
| LLM provider/model | `gemini` / `gemini-3.1-flash-lite` |
| Test set dùng chung cho ba trạng thái | `data/eval/test_set.json` |

Test set được giữ nguyên để đảm bảo mọi thay đổi metric là do chất lượng dữ liệu/index thay đổi, không phải do thay đổi đề bài đánh giá.

## 7. Kết quả baseline

### Artifact checklist

| Artifact | Đường dẫn thực tế | Trạng thái | Ghi chú |
| --- | --- | --- | --- |
| Raw response/records | `data/raw/` | Có | Có `crossref_response.json`, `crossref_records.json` |
| Cleaned dataset | `data/clean/` | Có | Có CSV và JSON sạch |
| Embedding manifest/index | `data/embeddings/`, `data/chroma/` | Có | Collection baseline được tạo |
| Evaluation set | `data/eval/test_set.json` | Có | Dùng chung cho 3 trạng thái |
| Baseline metrics | `data/results/baseline_metrics.json` | Có | Đồng bộ với report |
| Quality/freshness | `data/quality/` | Có | Có baseline/corrupted/repaired |
| Baseline report | `data/reports/phase1_report.md` | Có | Sinh tự động |

### Baseline metrics

| Metric | Giá trị | Diễn giải |
| --- | ---: | --- |
| `retrieval_hit_rate` | 1.0000 | Retriever tìm đúng tài liệu ground-truth cho toàn bộ mẫu |
| `mean_token_f1` | 0.8363 | Chất lượng nội dung trả lời tốt trên dữ liệu sạch |
| `judge_accuracy` | 0.8125 | Judge đánh giá đa số câu trả lời đạt yêu cầu |
| `mean_judge_score` | 4.3125 | Điểm chất lượng trả lời cao trên thang 5 |
| Ragas | N/A (skipped) | Chưa bật `RUN_RAGAS=1` trong lần chạy chính |

## 8. Data quality và freshness

### Quality checks

| Check | Quality dimension | Ngưỡng/kỳ vọng | Kết quả baseline | Bằng chứng |
| --- | --- | --- | --- | --- |
| `null_ids == 0` | Completeness | 0 | Pass (`0`) | `data/quality/quality_report_baseline` |
| `is_id_unique == true` | Uniqueness | true | Pass (`true`) | `data/quality/quality_report_baseline` |
| `short_summaries == 0` | Validity | 0 | Pass (`0`) | `data/quality/quality_report_baseline` |
| `pass == true` | Overall quality gate | true | Pass (`true`) | `data/quality/quality_report_baseline` |

### Freshness

| Thuộc tính | Giá trị |
| --- | --- |
| Freshness được đo tại | `data/quality/freshness_report.json` |
| Timestamp mới nhất | `2026-07-31` |
| Ngưỡng freshness | 180 ngày |
| Trạng thái baseline | Fresh |
| Lý do | `stale_rows=0/24`, `is_fresh=true` |

## 9. Corruption scenarios và repair

| Corruption | Cách tạo | Record bị tác động | Quality signal kỳ vọng | Tác động thực tế | Cách repair |
| --- | --- | ---: | --- | --- | --- |
| `drop_latest_records` | Loại bớt bản ghi mới nhất | 2 | Freshness xấu đi, ngữ cảnh mới bị thiếu | Hit rate giảm | Rebuild lại từ raw records |
| `blank_summary` | Làm trống summary | 2 | `short_summaries` tăng | Token F1 giảm | Chạy cleaning lại từ raw |
| `inject_noise` | Chèn nhiễu vào summary | 2 | Chất lượng ngữ cảnh giảm | Judge score giảm | Reload raw + clean |
| `truncate_title` | Cắt ngắn title | 2 | Metadata suy giảm | Ảnh hưởng retrieval/qa | Re-clean từ nguồn chuẩn |
| `stale_published_date` | Dời ngày về 2020 | 3 | `stale_rows` tăng | Freshness fail | Tái tạo published đúng từ raw |
| `add_duplicates` | Nhân bản dòng dữ liệu | 2 | `is_id_unique=false` | Quality fail | Dedupe lại khi cleaning |

Corruption log:
- Đường dẫn: `data/results/corruption_log.json`
- Trạng thái: Có
- Nhận xét: Có đủ loại corruption, số lượng bản ghi ảnh hưởng, `paper_id` cụ thể và mô tả tác động.

Repair được thực hiện bằng cách tái tạo dataset repaired từ raw source (`crossref_records.json`) và chạy lại cleaning/index/evaluation, không sửa tay answers hoặc metrics.

## 10. So sánh baseline, corrupted và repaired

| Metric/signal | Baseline | Corrupted | Repaired | Thay đổi do corruption | Mức phục hồi | Nhận xét |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| `retrieval_hit_rate` | 1.0000 | 0.5000 | 1.0000 | -0.5000 | +0.5000 | Suy giảm mạnh khi dữ liệu lỗi; phục hồi hoàn toàn sau repair |
| `mean_token_f1` | 0.8363 | 0.3844 | 0.8363 | -0.4519 | +0.4519 | Nội dung trả lời giảm chất lượng khi context bẩn/thiếu |
| `judge_accuracy` | 0.8125 | 0.3750 | 0.8125 | -0.4375 | +0.4375 | Judge phản ánh rõ tác động dữ liệu |
| `mean_judge_score` | 4.3125 | 2.5625 | 4.3125 | -1.7500 | +1.7500 | Chất lượng tổng thể phục hồi về mức baseline |
| Quality checks pass/fail | Pass | Fail | Pass | Xấu đi | Phục hồi | Corrupted vi phạm uniqueness + short summaries + stale rows |
| Freshness status | Fresh | Stale | Fresh | Xấu đi | Phục hồi | Repair trả dữ liệu về trạng thái fresh |

Hai kết luận nhân quả chính:
1. Corruption làm rỗng/nhiễu nội dung và làm cũ dữ liệu -> quality/freshness fail -> retrieval và answer quality giảm mạnh.
2. Repair bằng cách rebuild từ raw source -> quality/freshness phục hồi -> toàn bộ metric RAG phục hồi về baseline.

## 11. Vấn đề tích hợp quan trọng

- **Triệu chứng:** `401 UNAUTHENTICATED` khi gọi Gemini embedding, `UnicodeEncodeError` khi in emoji trên Windows, và `429 RESOURCE_EXHAUSTED` khi chạy CP5 liên tục.
- **Nguyên nhân:** `.env` chứa nhiều key trong một biến; terminal cp1252 không hỗ trợ một số ký tự Unicode; quota embed theo phút của free-tier.
- **Cách xử lý:** chọn key hợp lệ dạng `AIza...`, truyền key tường minh vào embedding client, đổi log sang ASCII, thêm retry khi gặp 429.
- **Cách xác minh:** chạy lại `script/run_phase1.py` và `script/run_corruption_flow.py` thành công; artifact và metrics khớp report.

## 12. Giới hạn và hướng cải thiện

| Giới hạn hiện tại | Ảnh hưởng | Hướng cải thiện có thể kiểm chứng |
| --- | --- | --- |
| Quota embedding miễn phí dễ chạm ngưỡng | Có thể làm flow gián đoạn khi chạy nhiều lần liên tiếp | Thêm cache embedding theo query/document hash và batch tốt hơn; giảm số lần gọi API |
| Report hiện ở mức tĩnh (Markdown) | Khó drill-down từng câu hỏi lỗi khi demo | Bổ sung dashboard hoặc script phân tích case-level từ `*_answers.json` |

## 13. Checklist trước khi nộp

- [x] Thông tin nhóm và repository chính xác.
- [x] Phân công khớp với module, artifact và kết quả thực tế.
- [x] Lệnh tái hiện đã được chạy lại trên phiên bản dùng để nộp.
- [x] Baseline, corrupted và repaired dùng cùng evaluation set.
- [x] Bảng metrics khớp với các file trong `data/results/`.
- [x] Quality/freshness conclusions khớp với `data/quality/`.
- [x] Các đường dẫn báo cáo và artifact truy cập được.
- [x] Mỗi thành viên đã hoàn thành báo cáo vai trò riêng.
- [x] Không có `.env`, API key, token hoặc secret trong source, report, log hay ảnh.
