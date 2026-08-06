# Bàn giao Checkpoint 6 - Hoàng Văn Quang

## 1) Trạng thái hoàn thành

- Đã chạy xong `script/run_corruption_flow.py` thành công.
- Đã có đủ 3 trạng thái để so sánh: baseline, corrupted, repaired.
- Đã cập nhật report so sánh theo tiếng Việt và có cột delta rõ ràng.

## 2) Artifact cần nộp/demo

- Baseline:
  - `data/results/baseline_metrics.json`
  - `data/results/baseline_answers.json`
- Corrupted:
  - `data/results/corrupted_metrics.json`
  - `data/results/corrupted_answers.json`
  - `data/results/corruption_log.json`
- Repaired:
  - `data/results/repaired_metrics.json`
  - `data/results/repaired_answers.json`
- Report:
  - `data/reports/corruption_report.md`
  - `data/reports/phase1_report.md`

## 3) Kết quả chính để trình bày

- Retrieval Hit Rate: `100% -> 50% -> 100%` (baseline -> corrupted -> repaired)
- Mean Token F1: `0.8363 -> 0.3844 -> 0.8363`
- Judge Accuracy: `81.25% -> 37.50% -> 81.25%`
- Mean Judge Score: `4.31 -> 2.56 -> 4.31`

Kết luận: corruption làm giảm mạnh chất lượng RAG; repair từ raw source giúp phục hồi chỉ số về baseline.

## 4) Bằng chứng dữ liệu bị lỗi có chủ đích

Trong `data/results/corruption_log.json` đã có đủ các loại lỗi:
- drop_latest_records
- blank_summary
- inject_noise
- truncate_title
- stale_published_date
- add_duplicates

## 5) Kiểm tra an toàn trước khi nộp

- `.env` không được track trong Git.
- `data/chroma/*` đã được ignore để tránh commit file runtime.
- Không hard-code API key trong mã nguồn.

## 6) Kịch bản demo ngắn (3-5 phút)

1. Mở `data/reports/corruption_report.md` và trình bày bảng delta.
2. Chỉ rõ 1 chỉ số giảm mạnh sau corruption (ví dụ retrieval hit rate -50%).
3. Chỉ rõ 1 chỉ số phục hồi sau repair (ví dụ token F1 +0.4519).
4. Mở `data/results/corruption_log.json` để liên kết metric change với lỗi dữ liệu.
5. Kết thúc bằng thông điệp: "Data quality trực tiếp ảnh hưởng chất lượng RAG".

