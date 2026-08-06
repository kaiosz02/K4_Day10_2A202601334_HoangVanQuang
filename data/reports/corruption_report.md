# Data Corruption & Recovery Comparison Report

## Evaluation Metrics Comparison

| Metric | Baseline | Corrupted | Repaired |
|---|---|---|---|
| Retrieval Hit Rate | 100.00% | 50.00% | 100.00% |
| Mean Token F1 | 0.8363 | 0.3892 | 0.8363 |
| Judge Accuracy | 75.00% | 37.50% | 75.00% |
| Mean Judge Score | 4.00/5 | 2.50/5 | 4.00/5 |

## Quality & Freshness Assessment

| Assessment | Corrupted Data | Repaired Data |
|---|---|---|
| Quality Passed | No | Yes |
| Null Titles | 0 | 0 |
| Short Summaries | 4 | 0 |
| Stale Rows | 5 | 0 |

## Conclusion
Data errors significantly decrease the accuracy of the Retrieval-Augmented Generation (RAG) agent. Correctly repairing data from raw sources recovers the original RAG metrics.
