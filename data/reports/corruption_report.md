# Báo cáo so sánh Corrupted và Repaired

## Bảng so sánh chỉ số đánh giá

| Metric | Baseline | Corrupted | Repaired |
|---|---|---|---|
| Retrieval Hit Rate | 100.00% | 50.00% | 100.00% |
| Mean Token F1 | 0.8363 | 0.3892 | 0.8363 |
| Judge Accuracy | 75.00% | 37.50% | 75.00% |
| Mean Judge Score | 4.00/5 | 2.50/5 | 4.00/5 |

## Đánh giá chất lượng dữ liệu và độ tươi

| Hạng mục | Corrupted | Repaired |
|---|---:|---:|
| Chất lượng đạt | Không | Có |
| Số tiêu đề null | 0 | 0 |
| Số summary quá ngắn | 4 | 0 |
| Số dòng stale | 5 | 0 |

## Kết luận
Corruption làm giảm rõ rệt chất lượng RAG (hit rate, token F1, judge accuracy, judge score đều giảm). 
Khi repair lại từ dữ liệu raw đáng tin cậy, các chỉ số phục hồi gần/đúng về baseline.
