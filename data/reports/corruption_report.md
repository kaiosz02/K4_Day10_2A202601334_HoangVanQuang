# Báo cáo so sánh Corrupted và Repaired

## Bảng so sánh chỉ số đánh giá

| Chỉ số | Baseline | Corrupted | Repaired | Delta (Corrupted - Baseline) | Delta (Repaired - Corrupted) |
|---|---:|---:|---:|---:|---:|
| Retrieval Hit Rate | 100.00% | 50.00% | 100.00% | -50.00% | +50.00% |
| Mean Token F1 | 0.8363 | 0.3844 | 0.8363 | -0.4519 | +0.4519 |
| Judge Accuracy | 81.25% | 37.50% | 81.25% | -43.75% | +43.75% |
| Mean Judge Score | 4.31/5 | 2.56/5 | 4.31/5 | -1.75 | +1.75 |

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
