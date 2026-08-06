# Member Role Report — Day 10: Data Pipeline & Data Observability


## 1. Thông tin cá nhân

| Thông tin         | Nội dung                  |
| ------------------ | -------------------------- |
| Họ và tên       | Tạ Hồng Quí          |
| MSSV               | 2A202601538                    |
| Khóa/Lớp         | K4            |
| Tên nhóm         | Edge-Agent     |
| Vai trò chính    | Role 4 (Evaluation & Observability) |
| Repository         | K4_Day10_Data-Pipeline-Data-Observability |
| Ngày hoàn thành | 2026-08-06             |

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao  | Trạng thái                                 |
| ------------------ | --------------------- | ---------------- | ----------------- | -------------------------------------------- |
| Đóng băng Eval Set | `src/evaluation/testset.py` (`build_test_set`) | `papers_clean` (DataFrame) | `data/eval/test_set.json` (Bộ câu hỏi) | Hoàn thành |
| Kiểm tra Data Quality & Freshness | `src/observability/quality.py` | `papers_clean` (DataFrame) | Các file JSON lưu metrics chất lượng | Hoàn thành |
| Sinh báo cáo tự động | `src/observability/reporting.py` | Metrics, Quality, Freshness JSON | `phase1_report.md` và `corruption_report.md` | Hoàn thành |

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động                         | Thành viên/module được hỗ trợ | Kết quả                    |
| ------------------------------------ | ------------------------------------ | ---------------------------- |
| Phân tích lỗi Data Bẩn | Role 2 (Cleaning & Corruption) | Hỗ trợ dò tìm nguyên nhân tại sao file `papers_clean_corrupted.csv` làm rớt Hit Rate xuống 50% bằng cách trích xuất file báo cáo `quality_report_corrupted.json`. |

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao       | Cách xác minh         |
| --------------------------- | ----------------------------- | ------------------------- | ----------------------- |
| Viết logic sinh Test Set (Frozen) | `src/evaluation/testset.py` | 16 câu hỏi có `ground_truth` | Đọc file `data/eval/test_set.json` sinh ra |
| Viết Data Quality Checks | `src/observability/quality.py` | Báo cáo null ID, null Title, freshness | Kiểm tra file `data/quality/*.json` |
| Viết Reporting Logic Markdown | `src/observability/reporting.py` | Báo cáo Markdown tổng hợp so sánh | Đọc file `data/reports/corruption_report.md` |

Tạo ra bộ Test Set cố định (Frozen Evaluation Set) gồm 16 câu hỏi trích xuất từ dữ liệu sạch, có kèm `ground_truth` và `ground_truth_doc_ids` chuẩn xác, giúp nhóm có thước đo cố định để chấm điểm RAG agent ở cả 3 pha: Baseline, Corrupted, Repaired.

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết

Tạo thước đo đánh giá (A/B testing) cố định để so sánh chất lượng của RAG agent; xây dựng chốt chặn kiểm soát chất lượng dữ liệu để phát hiện dữ liệu bẩn; và tổng hợp số liệu để báo cáo trực quan.

### Cách triển khai

- **Testset:** Lấy ngẫu nhiên các bài báo (bằng pandas `head`), tự động sinh 4 loại câu hỏi (tóm tắt, tác giả, ngày, category) kèm đáp án để làm mốc. Tổng cộng 16 câu hỏi.
- **Quality:** Dùng pandas check `.isnull().sum()` và `.nunique()` để phát hiện ID trống/trùng, text ngắn `<100` ký tự. Đếm số dòng mà `age_days` vượt quá `freshness_threshold`.
- **Reporting:** Dùng chuỗi f-string định dạng Markdown theo dạng bảng, dễ dàng so sánh 3 trạng thái.

### Input, output và contract

| Thành phần                   | Mô tả                                     |
| ------------------------------ | ------------------------------------------- |
| Input                          | `papers_clean` DataFrame, Metrics dicts     |
| Output                         | `test_set.json`, quality JSONs, MD Reports |
| Module phụ thuộc             | `core.utils` (cho việc đọc/ghi file)        |
| Module sử dụng output        | `eval`, luồng pipeline so sánh kết quả      |
| Điều kiện lỗi cần xử lý | Xử lý an toàn khi df rỗng (trả về danh sách rỗng 0 câu hỏi) |

### Cách xác minh

```bash
uv run python script/run_phase1.py
uv run python script/run_corruption_flow.py
```

- **Kết quả mong đợi:** Script hoàn thành không lỗi, xuất ra đủ 3 file báo cáo (baseline, corrupted, repaired) và cảnh báo đỏ ở pha Corrupted.
- **Kết quả thực tế:** Hit rate rớt từ 1.0 xuống 0.5 ở pha Corrupted, Quality check báo `FAILED` và `STALE`. Khôi phục về 1.0 ở pha Repaired.
- **Artifact/log:** `data/reports/corruption_report.md`

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Cần một phương pháp để đo lường công bằng sự suy giảm chất lượng của AI khi dữ liệu bị hỏng.
- **Các phương án đã cân nhắc:** (1) Sinh bộ test ngẫu nhiên ở mỗi pha. (2) Đóng băng một bộ test set (Golden Set) duy nhất từ pha Baseline và dùng lại cho các pha sau.
- **Phương án đã chọn:** Phương án (2) - Đóng băng Test Set.
- **Lý do:** Dùng chung 1 bộ đề thi duy nhất (Idempotency) là cách duy nhất để chứng minh điểm AI (F1/Hit Rate) rớt là do **Dữ liệu bẩn**, chứ không phải do câu hỏi đợt 2 khó hơn đợt 1.
- **Bằng chứng quyết định phù hợp:** Đã cố định được file `data/eval/test_set.json` không bị ghi đè, giúp báo cáo `corruption_report.md` phản ánh đúng delta chênh lệch do data bẩn.

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:** Evaluator thỉnh thoảng báo Success giả nhưng LLM sinh ra câu trả lời rác khi data bị xóa trống.
- **Lệnh hoặc bước tái hiện:** `uv run python script/run_corruption_flow.py` lúc chạy Corrupted pha (làm rỗng summary).
- **Nguyên nhân gốc:** Khi LLM bị thiếu dữ liệu do bài báo rỗng, nó bị ảo giác (hallucination) tự bịa ra câu trả lời (ví dụ tác giả là 'Chang Lei'). Hệ thống đánh giá không bắt được nếu chỉ đo form.
- **Cách xử lý:** Viết thêm bộ lọc ở Quality Checks để đếm chính xác số lượng bài báo có `len(summary) < 100` làm bằng chứng. Ở khâu Evaluator, dùng LLM làm Judge để chấm điểm xem câu trả lời có khớp với ground_truth không thay vì chỉ so sánh chuỗi.
- **Cách xác minh sau khi sửa:** Check log hiển thị `The model answer is empty and failed to provide any summary` với `score: 1` và `token_f1: 0.0`.
- **Điều học được:** Đừng tin tưởng con số nếu không có cơ chế chốt chặn (Observability). Sự ảo giác của LLM có thể che lấp đi việc data bên dưới đã bị rỗng từ lâu.

## 7. Hiểu biết về luồng end-to-end

Giải thích ngắn gọn bằng lời của bạn:

1. Dữ liệu đi từ Crossref đến vector index như thế nào?
2. Evaluation set và ground-truth document IDs dùng để đo retrieval/answer quality ra sao?
3. Quality checks khác freshness monitoring ở điểm nào trong bài lab?
4. Vì sao phải dùng cùng test set cho baseline, corrupted và repaired?
5. Repair được xem là thành công dựa trên artifact và metric nào?

**Câu trả lời:**

1. Dữ liệu thô từ Crossref (raw json) -> Cleaning (Lọc rỗng, lọc trùng, ghép Title + Author + Summary thành `text_for_embedding`) -> Embedding bằng `GeminiEmbeddings` -> Nạp vào `ChromaDB` làm Vector Index.
2. `ground_truth_doc_ids` được đối chiếu với danh sách doc IDs do hệ thống RAG tìm về. Nếu ID có mặt -> tính là Hit (đo Retrieval Hit Rate). Câu trả lời của RAG sinh ra được so sánh token/ngữ nghĩa với `ground_truth` -> đo Answer Quality (F1/Judge).
3. Quality checks kiểm tra tính **toàn vẹn cấu trúc** của dữ liệu (trống, trùng lặp, nội dung quá ngắn). Freshness check đánh giá độ **chính xác về mặt thời gian** (dữ liệu có bị lỗi thời, quá hạn so với ngưỡng cho phép hay không).
4. Phải dùng cùng một test set cố định (A/B testing) để đảm bảo mọi sự thay đổi trong điểm số (F1, Hit Rate) đều bắt nguồn từ một biến số duy nhất là: Chất lượng của Data.
5. Repair thành công khi file `quality_report_repaired.json` báo `success: true` (Xanh) và các metrics của AI (`retrieval_hit_rate`, `mean_token_f1`) phục hồi về mức 1.0 và 0.83 như ban đầu ở pha Baseline.

## 8. Phân tích kết quả

### Metrics chính

| Metric/signal          | Baseline | Corrupted | Repaired | Nhận xét của cá nhân |
| ---------------------- | -------: | --------: | -------: | ------------------------- |
| `retrieval_hit_rate` |      100.00% |       50.00% |      100.00% | Sụt giảm 50% khi data bẩn, phục hồi hoàn toàn sau repair. |
| `mean_token_f1`      |      0.8363 |       0.3844 |      0.8363 | Token F1 rớt thê thảm phản ánh model sinh câu trả lời rác (Hallucination) khi thiếu context. |
| `judge_accuracy`     |      81.25% |       37.50% |      81.25% | LLM làm giám khảo bắt được lỗi khi RAG trả lời sai do thiếu data. |
| `mean_judge_score`   |      4.31 |       2.56 |      4.31 | Giảm mạnh do model ảo giác khi không có thông tin nền (Summary bị rỗng). |
| Quality checks         |      Pass |       Fail |      Pass | Cảnh báo null/short text hoạt động cực tốt. Bắt được 4 short summaries. |
| Freshness status       |      Pass |       Fail |      Pass | Cảnh báo stale_rows báo động đỏ khi có 5 bài báo bị dời năm về quá khứ. |

### Kết luận từ số liệu

Hoàn thành hai chuỗi nguyên nhân–bằng chứng sau:

1. **Dữ liệu bị xóa/sửa sai (Data corruption)** → **Báo cáo Quality Fail (bắt được 4 lỗi short summaries, 5 stale rows)** → **Hit Rate rớt xuống 50.00% và Token F1 giảm còn 0.3844**.
2. **Khôi phục từ Raw Snapshot (Repair action)** → **Báo cáo Quality xanh lại (Pass)** → **Hit Rate và F1 phục hồi 100% như Baseline**.

Corruption nào ảnh hưởng rõ nhất và vì sao?

Hành vi xóa rỗng tóm tắt bài báo (Blank Summary) ảnh hưởng chí mạng nhất. Khi bài báo bị trống nội dung, hệ thống Retrieval Vector không thể tìm ra bài báo (Hit Rate giảm 50%). Do thiếu Context, LLM đành tự bịa ra câu trả lời (ví dụ: tự bịa tác giả là 'Chang Lei'). Điều này kéo theo điểm đánh giá của LLM Judge bị rớt thẳng đứng từ 4.31 xuống 2.56.

Kết quả nào khác với kỳ vọng ban đầu?

Bất ngờ nhất là việc chỉ cần 4 bài báo bị làm rỗng nội dung và 2 bài bị xóa (trong tổng số 24 bài), mà điểm `judge_accuracy` của toàn hệ thống đã rớt thê thảm từ 81.25% xuống 37.50%. Nó chứng minh rằng RAG cực kỳ nhạy cảm với dữ liệu bẩn, một chút rác (Garbage in) có thể phá hủy hoàn toàn độ tin cậy của hệ thống (Garbage out).

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất

1. **Shift-Left Observability:** Phải chặn lỗi data từ sớm (ngay khi Ingestion), đừng đợi đến lúc User chửi AI trả lời ngu mới đi dò lại từ đầu.
2. **Frozen Test Set:** Thước đo (Test Set) không được phép chạy random mỗi lần đánh giá, phải dùng chung 1 thước đo chuẩn mới có A/B Testing công bằng.
3. **Data Repair Lifecycle:** Khi data bẩn, tuyệt đối không sửa tay (Manual Fix) trên bảng data đã làm sạch, mà phải Rollback về Raw Source rồi làm sạch lại từ đầu để đảm bảo tính tái lập (Reproducibility).

### Nếu có thêm thời gian

Tích hợp tự động đẩy cảnh báo (Alert) bắn thẳng về Slack/Discord hoặc Email ngay khi script Quality Checks phát hiện ra tín hiệu `success: false`. Điều này sẽ giúp đội ngũ Data Engineering biết ngay lập tức hệ thống đang bị lỗi thay vì phải mở file JSON ra xem thủ công.

## 10. Cam kết của thành viên

Đánh dấu sau khi tự kiểm tra:

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [x] Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Tạ Hồng Quí  
**Ngày xác nhận:** 2026-08-06
