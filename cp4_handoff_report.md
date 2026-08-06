# Bàn Giao Checkpoint 4 - Hoàng Văn Quang

## Ảnh Chụp Baseline (khóa trước CP5)

- File metrics baseline: `data/results/baseline_metrics.json`
- File answers baseline: `data/results/baseline_answers.json`
- Báo cáo baseline: `data/reports/phase1_report.md`
- Báo cáo chất lượng và độ tươi: `data/quality/quality_report_baseline`, `data/quality/freshness_report.json`

Chỉ số baseline hiện tại:
- `samples`: 16
- `retrieval_hit_rate`: 1.0000
- `mean_token_f1`: 0.8363
- `judge_accuracy`: 0.8125
- `mean_judge_score`: 4.3125

Ảnh chụp độ tươi dữ liệu:
- `total_rows`: 24
- `stale_rows`: 0
- `is_fresh`: true

## Kế Hoạch Corruption Cho CP5

Mục tiêu: tạo lỗi dữ liệu có kiểm soát và đo mức ảnh hưởng bằng evaluator/test set cố định.

Các loại corruption dự kiến:
1. Bỏ các bản ghi mới nhất (mô phỏng thiếu dữ liệu mới).
2. Làm trống trường tóm tắt (mô phỏng tài liệu thiếu nội dung).
3. Chèn nhiễu vào phần tóm tắt (mô phỏng nội dung chất lượng thấp).
4. Cắt ngắn tiêu đề (mô phỏng suy giảm metadata).
5. Đẩy ngày xuất bản cũ hơn (mô phỏng dữ liệu lỗi thời).
6. Thêm bản ghi trùng lặp (mô phỏng lỗi dedupe).

## Nguyên Tắc Bắt Buộc Giữ

- Giữ nguyên test set: `data/eval/test_set.json`.
- Giữ nguyên toàn bộ artifact baseline để làm mốc so sánh (chỉ đọc, không ghi đè).
- Dùng collection tách biệt cho từng trạng thái:
  - `papers-baseline`
  - `papers-corrupted`
  - `papers-repaired`
- Giữ `refresh_source=False` và `refresh_test_set=False` để đảm bảo so sánh công bằng.

## Checklist Chạy CP5

1. Chạy lệnh: `python script/run_corruption_flow.py`
2. Xác minh các artifact mới:
   - `data/results/corruption_log.json`
   - `data/results/corrupted_metrics.json`
   - `data/results/repaired_metrics.json`
   - `data/reports/corruption_report.md`
3. Xác nhận file baseline metrics không bị thay đổi ngoài ý muốn.
4. Trình bày ít nhất một trường hợp chất lượng giảm và một trường hợp phục hồi có dẫn chứng từ artifact.

