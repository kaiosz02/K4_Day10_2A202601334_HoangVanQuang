# Member Role Report — Day 10: Data Pipeline & Data Observability

> Mỗi thành viên trong nhóm tự hoàn thành mẫu này để báo cáo đúng vai trò, phần việc và mức hiểu của mình. Không sao chép nguyên báo cáo chung hoặc báo cáo của thành viên khác. Thay nội dung trong dấu `[ ]` và xóa các dòng hướng dẫn không cần thiết trước khi nộp.

## 1. Thông tin cá nhân

| Thông tin         | Nội dung                  |
| ------------------ | -------------------------- |
| Họ và tên       | Tạ Hồng Quí          |
| MSSV               | 2A202601538                    |
| Khóa/Lớp         | K4            |
| Tên nhóm         | Adge-Agent     |
| Vai trò chính    | Role 4                |
| Repository         | [Đường dẫn repository] |
| Ngày hoàn thành | 2026-8-6             |

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao  | Trạng thái                                 |
| ------------------ | --------------------- | ---------------- | ----------------- | -------------------------------------------- |
| Đóng băng Eval Set | `src/evaluation/testset.py` (`build_test_set`) | `papers_clean` (DataFrame) | `data/eval/test_set.json` (Bộ câu hỏi) | Hoàn thành |
| Kiểm tra Data Quality & Freshness | `src/observability/quality.py` | `papers_clean` (DataFrame) | Các file JSON lưu metrics chất lượng | Hoàn thành |
| Sinh báo cáo tự động | `src/observability/reporting.py` | Metrics, Quality, Freshness JSON | `phase1_report.md` và `corruption_report.md` | Hoàn thành |

Chỉ nhận ownership cho phần bạn trực tiếp thực hiện. Liên hệ rõ phần việc của bạn với đầu vào, đầu ra và các thành viên phụ thuộc vào phần đó.

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động                         | Thành viên/module được hỗ trợ | Kết quả                    |
| ------------------------------------ | ------------------------------------ | ---------------------------- |
| [Debug/tích hợp/tài liệu] | [Tên hoặc module] | [Kết quả và bằng chứng] |

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao       | Cách xác minh         |
| --------------------------- | ----------------------------- | ------------------------- | ----------------------- |
| Viết logic sinh Test Set (Frozen) | `src/evaluation/testset.py` | 12 câu hỏi có `ground_truth` | Đọc file `data/eval/test_set.json` sinh ra |
| Viết Data Quality Checks | `src/observability/quality.py` | Báo cáo null ID, null Title, freshness | Kiểm tra file `data/quality/*.json` |
| Viết Reporting Logic Markdown | `src/observability/reporting.py` | Báo cáo Markdown tổng hợp so sánh | Đọc file `data/reports/corruption_report.md` |

Nêu một output cụ thể mà phần việc của bạn tạo ra hoặc giúp xác minh:

Tạo ra bộ Test Set cố định (Frozen Evaluation Set) gồm 12 câu hỏi trích xuất từ dữ liệu sạch, có kèm `ground_truth` và `ground_truth_doc_ids` chuẩn xác, giúp nhóm có thước đo cố định để chấm điểm RAG agent ở cả 3 pha: Baseline, Corrupted, Repaired.

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết

### Vấn đề cần giải quyết

Tạo thước đo đánh giá (A/B testing) cố định để so sánh chất lượng của RAG agent; xây dựng chốt chặn kiểm soát chất lượng dữ liệu để phát hiện dữ liệu bẩn; và tổng hợp số liệu để báo cáo trực quan.

### Cách triển khai

- **Testset:** Lấy ngẫu nhiên 3 bài báo (bằng pandas `sample`), tự động sinh 4 loại câu hỏi (tóm tắt, tác giả, ngày, category) kèm đáp án để làm mốc.
- **Quality:** Dùng pandas check `.isnull().sum()` và `.nunique()` để phát hiện ID trống/trùng, text ngắn `<10` ký tự. Đếm số dòng mà `age_days` vượt quá `freshness_threshold`.
- **Reporting:** Dùng chuỗi f-string định dạng Markdown theo dạng bảng, dễ dàng so sánh 3 trạng thái.

### Input, output và contract

| Thành phần                   | Mô tả                                     |
| ------------------------------ | ------------------------------------------- |
| Input                          | `papers_clean` DataFrame, Metrics dicts     |
| Output                         | `test_set.json`, quality JSONs, MD Reports |
| Module phụ thuộc             | `core.utils` (cho việc đọc/ghi file)        |
| Module sử dụng output        | `eval`, luồng pipeline so sánh kết quả      |
| Điều kiện lỗi cần xử lý | Xử lý an toàn khi df rỗng (trả về 0)       |

### Cách xác minh

```bash
[Ghi lệnh thực tế đã chạy]
```

- **Kết quả mong đợi:** [Mô tả.]
- **Kết quả thực tế:** [Mô tả.]
- **Artifact/log:** [Đường dẫn; không chứa secret.]

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** [Vấn đề hoặc lựa chọn cần quyết định.]
- **Các phương án đã cân nhắc:** [Ít nhất hai phương án.]
- **Phương án đã chọn:** [Lựa chọn.]
- **Lý do:** [Trade-off về correctness, data quality, reproducibility, cost hoặc độ phức tạp.]
- **Bằng chứng quyết định phù hợp:** [Metric, artifact hoặc kết quả thử nghiệm.]

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:** [Che toàn bộ secret trước khi ghi.]
- **Lệnh hoặc bước tái hiện:** [Lệnh/bước.]
- **Nguyên nhân gốc:** [Root cause, không chỉ mô tả triệu chứng.]
- **Cách xử lý:** [Thay đổi cụ thể.]
- **Cách xác minh sau khi sửa:** [Lệnh và kết quả.]
- **Điều học được:** [Bài học kỹ thuật.]

Nếu chưa xử lý xong:

- **Phạm vi bị ảnh hưởng:** [Module/artifact.]
- **Những gì đã loại trừ:** [Các giả thuyết đã kiểm tra.]
- **Bước tiếp theo:** [Hành động có thể kiểm chứng.]

## 7. Hiểu biết về luồng end-to-end

Giải thích ngắn gọn bằng lời của bạn:

1. Dữ liệu đi từ Crossref đến vector index như thế nào?
2. Evaluation set và ground-truth document IDs dùng để đo retrieval/answer quality ra sao?
3. Quality checks khác freshness monitoring ở điểm nào trong bài lab?
4. Vì sao phải dùng cùng test set cho baseline, corrupted và repaired?
5. Repair được xem là thành công dựa trên artifact và metric nào?

**Câu trả lời:**

1. Dữ liệu đi từ Crossref (raw json) -> làm sạch -> chunking -> nhúng bằng `sentence-transformers` -> nạp vào `ChromaDB` (vector index).
2. Khi câu hỏi đi vào, agent sẽ tìm kiếm (retrieve) document. ID của doc tìm được sẽ đem so sánh với `ground_truth_doc_ids` (đo Hit Rate). Câu trả lời của agent sinh ra sẽ so với `ground_truth` (đo F1/Judge).
3. Quality checks kiểm tra độ toàn vẹn của dữ liệu (trống, trùng lặp, ngắn). Freshness check đánh giá độ trễ của dữ liệu (quá hạn so với ngưỡng ngày).
4. Để đảm bảo thước đo cố định (cùng một đề thi). Nếu thay đổi câu hỏi, kết quả thay đổi sẽ không thể chứng minh là do dữ liệu bẩn gây ra.
5. Repair thành công khi các file ở data/quality báo Pass xanh lại và các metrics agent (`retrieval_hit_rate`, `mean_token_f1`) phục hồi về mức gần/bằng Baseline.

## 8. Phân tích kết quả

### Metrics chính

| Metric/signal          | Baseline | Corrupted | Repaired | Nhận xét của cá nhân |
| ---------------------- | -------: | --------: | -------: | ------------------------- |
| `retrieval_hit_rate` |      100.00% |       50.00% |      100.00% | Sụt giảm mạnh khi data bẩn, phục hồi hoàn toàn sau repair. |
| `mean_token_f1`      |      0.8363 |       0.3892 |      0.8363 | Token F1 phản ánh đúng việc model sinh câu trả lời rác khi thiếu context. |
| `judge_accuracy`     |      75.00% |       37.50% |      75.00% | LLM làm giám khảo bắt được lỗi khi RAG trả lời sai do thiếu data. |
| `mean_judge_score`   |      4.00 |       2.50 |      4.00 | Giảm mạnh do model ảo giác (hallucination) khi không có thông tin nền. |
| Quality checks         |      Pass |       Fail |      Pass | Cảnh báo null/short text phát huy tác dụng cực tốt. |
| Freshness status       |      Pass |       Fail |      Pass | Cảnh báo stale_rows báo động đỏ khi có bài báo bị dời năm. |

### Kết luận từ số liệu

Hoàn thành hai chuỗi nguyên nhân–bằng chứng sau:

1. **Dữ liệu bị xóa/sửa sai (Data corruption)** → **Báo cáo Quality Fail (lỗi short summaries, stale rows)** → **Hit Rate rớt xuống 50.00% và Token F1 giảm còn 0.3892**.
2. **Khôi phục từ Raw (Repair action)** → **Báo cáo Quality xanh lại (Pass)** → **Hit Rate và F1 phục hồi 100% như Baseline**.

Corruption nào ảnh hưởng rõ nhất và vì sao?

Hành vi xóa nội dung (blank summary) và xóa ID ảnh hưởng rõ nhất. Khi bài báo bị trống nội dung trong ChromaDB, Retriever không lấy được context hữu ích (Hit Rate giảm 50%). Model không có thông tin để trả lời đành tự bịa (hallucination), kéo theo điểm đánh giá của Judge bị rớt thẳng đứng (từ 4.0 xuống 2.5).

Kết quả nào khác với kỳ vọng ban đầu?

[Nêu kết quả, giả thuyết và cách đã kiểm tra.]

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất

1. [Điều học được về data pipeline.]
2. [Điều học được về data quality/observability.]
3. [Điều học được về ảnh hưởng của data đến RAG agent.]

### Nếu có thêm thời gian

[Nêu một cải thiện cụ thể, lý do và cách đo cải thiện đó.]

## 10. Cam kết của thành viên

Đánh dấu sau khi tự kiểm tra:

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [ ] Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Tạ Hồng Quí
**Ngày xác nhận:** 2026-08-06
