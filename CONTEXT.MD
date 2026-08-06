# Context: Day 10 — Data Pipeline & Data Observability for RAG

## 1. Mục tiêu dự án

Đây là bài lab mô phỏng vòng đời dữ liệu đầy đủ cho một hệ thống RAG (Retrieval-Augmented
Generation) sử dụng metadata bài báo học thuật lấy từ **Crossref API**
(`https://api.crossref.org/works`).

Luồng end-to-end:

```
Crossref API
  -> raw data (data/raw/)
  -> cleaned data (data/clean/)
  -> embedding + ChromaDB (data/embeddings/, data/chroma/)
  -> RAG agent (semantic search + exact lookup)
  -> evaluation (data/eval/, data/results/)
  -> data quality + freshness report (data/quality/)
  -> corrupt data intentionally (simulate bad data)
  -> re-evaluate impact of corruption
  -> repair from raw source
  -> compare baseline / corrupted / repaired (data/reports/)
```

Trọng tâm: không chỉ code chạy được, mà phải **chứng minh bằng metrics và report** rằng dữ liệu
xấu làm giảm chất lượng agent, và repair đúng cách phục hồi được chất lượng.

Tài liệu gốc trong repo: `README.md` (setup + checklist), `Guide.md` (hướng dẫn 15 bước chi tiết),
`Rubric.md` (thang điểm 0-90 + bonus 90-100).

## 2. Thông tin nhóm

Nhóm 4 người, dự án nằm tại:
`D:\thuc_hanh_vinAI\K4_Day10_2A202601334_HoangVanQuang`

| Vai trò | Thành viên | MSSV | Phạm vi phụ trách | File chính |
|---|---|---|---|---|
| **1 — Lead / Pipeline integrator** | Hoàng Văn Quang | 2A202601334 | Settings, orchestration, release, demo | `src/core/`, `src/pipelines/phase1.py`, `src/pipelines/corruption_flow.py` |
| **2 — Data foundation & recovery** | Nguyễn Thị Việt Vinh | 2A202601836 | Crossref ingestion, cleaning, corruption, repair | `src/ingestion/crossref.py`, `cleaning.py`, `corruption.py` |
| **3 — RAG & agent owner** | Hoàng Thị Trà My | 2A202601290 | MiniLM embedding, Chroma, semantic search, agent | `src/retrieval/` (đã implement sẵn — chỉ cần đọc/verify) |
| **4 — Evaluation & observability** | Tạ Hồng Quí | 2A202601538 | Test set, metrics, quality, freshness, reports | `src/evaluation/testset.py`, `src/observability/quality.py`, `reporting.py` |

Quy tắc xuyên suốt cả nhóm:
- Chỉ chạy corruption flow **sau khi** baseline đã có đủ artifact.
- Giữ nguyên test set, ground truth, evaluator, top-k khi so sánh baseline / corrupted / repaired.
- Dùng path và collection **riêng** cho 3 trạng thái — không ghi đè baseline.
- Repair = chạy lại pipeline từ raw/source đáng tin, **không sửa tay** answers hoặc metrics.
- Report phải trỏ tới artifact có thật; không commit API key hoặc `.env`.

## 3. Yêu cầu môi trường

- Python 3.11, 3.12 hoặc 3.13 (theo `pyproject.toml` / `uv.lock`)
- **Môi trường dùng trong nhóm: `.venv` + `pip`** (không dùng `uv`). Setup:

  Windows PowerShell:
  ```powershell
  python -m venv .venv
  .\.venv\Scripts\Activate.ps1
  python -m pip install --upgrade pip
  python -m pip install -e .
  ```

  macOS/Linux:
  ```bash
  python3 -m venv .venv
  source .venv/bin/activate
  python -m pip install --upgrade pip
  python -m pip install -e .
  ```

  > Lưu ý: `pip install -r requirements.txt` KHÔNG cài package trong `src/`. Luôn dùng
  > `python -m pip install -e .` (cài cả project lẫn dependency) sau khi kích hoạt `.venv`.
  > Mọi lệnh chạy code bên dưới đều giả định `.venv` đã được activate trong shell hiện tại.

- Copy `.env.example` -> `.env`, điền credential của 1 LLM provider
  (mặc định `LLM_PROVIDER=gemini`, `LLM_MODEL=gemini-2.5-flash`, cần `GOOGLE_API_KEY`)
- Providers hỗ trợ: openai, gemini, anthropic, openrouter, ollama, custom OpenAI-compatible

Tìm tất cả phần chưa code (PowerShell nếu chưa có `rg`):
```powershell
Get-ChildItem src -Recurse -Filter *.py | Select-String -Pattern 'TODO\(student\)|NotImplementedError'
```
hoặc (nếu có `ripgrep`):
```bash
rg -n "TODO\(student\)|NotImplementedError" src
```

Chạy pipeline (đã activate `.venv`):
```bash
python script/run_phase1.py           # Pha 1: baseline
python script/run_corruption_flow.py  # Pha 2: corruption/repair/compare (chỉ sau khi Pha 1 xong)
```

## 4. Cấu trúc thư mục

```
src/core/          Settings, Paths, utils dùng chung  (ĐÃ CODE XONG)
src/ingestion/      Crossref fetch, cleaning, corruption (TODO)
src/retrieval/      embeddings, ChromaDB index, LLM provider, agent, qa (ĐÃ CODE XONG — tham khảo)
src/evaluation/     test set builder (TODO), metrics (ĐÃ CODE XONG)
src/observability/  quality checks, freshness, markdown reports (TODO)
src/pipelines/      phase1.py và corruption_flow.py — orchestration (TODO)
script/             2 entrypoint: run_phase1.py, run_corruption_flow.py
data/               artifact sinh ra khi chạy (raw/clean/embeddings/eval/results/quality/reports)
```

## 5. Data contracts quan trọng (không được đổi tự do)

### `PaperRecord` (src/ingestion/crossref.py)
```python
paper_id, title, summary, authors: list[str], categories: list[str],
primary_category, published, updated, abs_url, pdf_url, comment
```

### Cleaned DataFrame cần các cột
`paper_id` (unique, not null), `title`, `summary`, `authors_joined`, `categories_joined`,
`summary_chars`, `published`, `age_days`, `text_for_embedding`.

### Test set item (src/evaluation/testset.py output)
```json
{ "id": ..., "question_type": "summary|authors|date|categories",
  "question": ..., "ground_truth": ..., "ground_truth_doc_ids": [...] }
```
`ground_truth_doc_ids` phải lấy từ `paper_id` thật trong dữ liệu clean, không tự bịa.

### Settings & Paths (src/core/config.py — đã implement, KHÔNG cần sửa)
`load_settings()` trả về `Settings` chứa toàn bộ path chuẩn hoá cho 3 trạng thái
(baseline/corrupted/repaired): `clean_csv/json`, `embeddings_json`, `metrics`, `answers`,
`quality_dir`, `freshness_report`, `reports`, collection names
(`papers-baseline`, `papers-corrupted`, `papers-repaired`), `top_k=4`,
`freshness_threshold_days=180`, `source_query`, `source_filter`, `max_results=24`.
Dùng đúng các path này thay vì hard-code string.

### Metrics quan tâm (src/evaluation/metrics.py — đã implement)
`retrieval_hit_rate`, `mean_token_f1`, `judge_accuracy`, `mean_judge_score`, `ragas` (optional,
bật bằng `RUN_RAGAS=1`).

## 6. Việc cần làm theo từng file (TODO hiện tại)

- `src/ingestion/crossref.py`: `parse_crossref_payload`, `fetch_source_records` (gọi API + retry
  cho 429/503 + lưu raw response/records), `load_raw_records`.
- `src/ingestion/cleaning.py`: `build_clean_dataframe` — normalize, parse date, tính `age_days`,
  tạo `text_for_embedding`, dedupe, filter record xấu.
- `src/ingestion/corruption.py`: `corrupt_clean_dataframe` — drop latest records, blank summary,
  inject noise, truncate title, làm date cũ đi, thêm duplicate, ghi corruption log.
- `src/evaluation/testset.py`: `build_test_set` — sinh câu hỏi summary/authors/date/categories từ
  dữ liệu đã clean.
- `src/observability/quality.py`: `run_data_quality_checks`, `build_freshness_report`.
- `src/observability/reporting.py`: `generate_phase1_report`, `generate_corruption_report`.
- `src/pipelines/phase1.py`: ghép toàn bộ luồng baseline end-to-end.
- `src/pipelines/corruption_flow.py`: ghép corrupt -> rebuild -> evaluate -> repair -> compare.

`src/retrieval/*` (embeddings, index, llm, agent, qa) đã có code hoàn chỉnh, dùng làm tham khảo,
không bắt buộc sửa trừ khi phát hiện lỗi.

## 7. Checklist trước khi nộp (theo README.md)

- [ ] Cài được trên môi trường sạch bằng `.venv` + `pip` (`python -m pip install -e .`)
- [ ] Baseline pipeline chạy end-to-end (`script/run_phase1.py`)
- [ ] Corruption flow chạy sau baseline (`script/run_corruption_flow.py`)
- [ ] Đầy đủ artifact: raw, clean, embedding, evaluation, quality, report
- [ ] Metrics/report khớp với artifact thực tế
- [ ] Chứng minh được before/corrupted/repaired bằng số liệu cụ thể
- [ ] Không có API key hoặc `.env` trong Git
- [ ] Đối chiếu `Rubric.md` (8 mục, 90 điểm cơ bản + bonus)

## 8. Cách dùng file này

Coding agent nên đọc file này trước khi động vào code để hiểu: mục tiêu bài lab, contract dữ
liệu không được phá vỡ, path/collection chuẩn trong `Settings`, và đúng phạm vi TODO cần làm theo
vai trò được giao (mặc định ưu tiên vai trò 1 — Lead/Pipeline integrator, nếu người yêu cầu không
nói khác).
