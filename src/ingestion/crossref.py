from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
import time
import requests

from core.config import Settings


@dataclass(frozen=True)
class PaperRecord:
    paper_id: str
    title: str
    summary: str
    authors: list[str]
    categories: list[str]
    primary_category: str
    published: str
    updated: str
    abs_url: str
    pdf_url: str
    comment: str


def _format_date(date_parts: list) -> str:
    """Format Crossref date-parts list into YYYY-MM-DD string."""
    if not date_parts or not isinstance(date_parts, list):
        return "1970-01-01"
    parts = date_parts[0] if isinstance(date_parts[0], list) else date_parts
    try:
        year = int(parts[0]) if len(parts) > 0 else 1970
        month = int(parts[1]) if len(parts) > 1 and parts[1] is not None else 1
        day = int(parts[2]) if len(parts) > 2 and parts[2] is not None else 1
        return f"{year:04d}-{month:02d}-{day:02d}"
    except Exception:
        return "1970-01-01"


def parse_crossref_payload(payload: dict) -> list[PaperRecord]:
    """Parse Crossref payload into list of PaperRecord.

    Rules:
    1. Duyet payload["message"]["items"].
    2. Lay DOI (paper_id), title, abstract/description (summary), authors, subject (categories), dates, URLs.
    3. Loc chi lay cac ban ghi co cay du title va summary (abstract hoac description).
    4. Tra ve list PaperRecord.
    """
    records: list[PaperRecord] = []
    items = payload.get("message", {}).get("items", [])
    if not isinstance(items, list):
        return records

    for item in items:
        if not isinstance(item, dict):
            continue

        paper_id = str(item.get("DOI", "") or item.get("id", "") or "").strip()

        # Extract title
        raw_title = item.get("title", [])
        if isinstance(raw_title, list):
            title = " ".join([str(t) for t in raw_title if t]).strip()
        else:
            title = str(raw_title or "").strip()

        # Extract summary (abstract or description)
        raw_summary = item.get("abstract", "") or item.get("description", "")
        if isinstance(raw_summary, list):
            summary = " ".join([str(s) for s in raw_summary if s]).strip()
        else:
            summary = str(raw_summary or "").strip()

        # Filter: must have non-empty title AND non-empty summary
        if not title or not summary:
            continue

        # Extract authors
        authors: list[str] = []
        raw_authors = item.get("author", [])
        if isinstance(raw_authors, list):
            for auth in raw_authors:
                if isinstance(auth, dict):
                    given = str(auth.get("given", "")).strip()
                    family = str(auth.get("family", "")).strip()
                    name = str(auth.get("name", "")).strip()
                    if given or family:
                        full_name = f"{given} {family}".strip()
                    else:
                        full_name = name
                    if full_name:
                        authors.append(full_name)

        # Extract categories (subjects)
        raw_cats = item.get("subject", [])
        categories: list[str] = []
        if isinstance(raw_cats, list):
            categories = [str(c).strip() for c in raw_cats if c and str(c).strip()]
        primary_category = categories[0] if categories else "General"

        # Dates
        pub_obj = (
            item.get("published-online")
            or item.get("published-print")
            or item.get("issued")
            or item.get("created")
            or {}
        )
        published = _format_date(pub_obj.get("date-parts", []))

        upd_obj = item.get("deposited") or item.get("indexed") or pub_obj
        updated = _format_date(upd_obj.get("date-parts", []))

        # URLs
        abs_url = str(item.get("URL", f"https://doi.org/{paper_id}" if paper_id else "")).strip()
        pdf_url = ""
        links = item.get("link", [])
        if isinstance(links, list):
            for l in links:
                if isinstance(l, dict) and l.get("content-type") == "application/pdf":
                    pdf_url = str(l.get("URL", "")).strip()
                    break

        # Comment
        raw_container = item.get("container-title", [])
        if isinstance(raw_container, list):
            comment = " ".join([str(c) for c in raw_container if c]).strip()
        else:
            comment = str(raw_container or "").strip()

        record = PaperRecord(
            paper_id=paper_id,
            title=title,
            summary=summary,
            authors=authors,
            categories=categories,
            primary_category=primary_category,
            published=published,
            updated=updated,
            abs_url=abs_url,
            pdf_url=pdf_url,
            comment=comment,
        )
        records.append(record)

    return records


def fetch_source_records(settings: Settings) -> list[PaperRecord]:
    """Goi source API Crossref, retry voi backoff, luu raw response & raw records, tra ve list PaperRecord."""
    url = "https://api.crossref.org/works"
    params = {
        "query": settings.source_query,
        "rows": settings.max_results,
    }
    if settings.source_filter:
        params["filter"] = settings.source_filter

    headers = {
        "User-Agent": "DataPipelineObservabilityLab/1.0 (mailto:lab@example.com)"
    }

    max_retries = 5
    backoff_factor = 1.5
    payload = None

    for attempt in range(max_retries):
        try:
            response = requests.get(url, params=params, headers=headers, timeout=30)
            if response.status_code == 200:
                payload = response.json()
                break
            elif response.status_code in {429, 500, 502, 503, 504}:
                wait_time = backoff_factor * (2 ** attempt)
                print(f"HTTP {response.status_code} from Crossref. Retrying in {wait_time:.1f}s... (Attempt {attempt+1}/{max_retries})")
                time.sleep(wait_time)
            else:
                response.raise_for_status()
        except requests.RequestException as e:
            if attempt == max_retries - 1:
                print(f"Error calling Crossref API after {max_retries} attempts: {e}")
                # Fallback to existing raw response if available
                if settings.paths.raw_records_json.exists():
                    print("Falling back to local raw_records_json snapshot...")
                    return load_raw_records(settings.paths.raw_records_json)
                raise e
            wait_time = backoff_factor * (2 ** attempt)
            time.sleep(wait_time)

    if payload is None:
        if settings.paths.raw_records_json.exists():
            return load_raw_records(settings.paths.raw_records_json)
        raise RuntimeError("Failed to fetch payload from Crossref API.")

    # 1. Save raw HTTP response (auditing)
    settings.paths.raw_api_response.parent.mkdir(parents=True, exist_ok=True)
    with open(settings.paths.raw_api_response, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    # 2. Parse records
    records = parse_crossref_payload(payload)

    # 3. Save raw records (parsed flat list)
    settings.paths.raw_records_json.parent.mkdir(parents=True, exist_ok=True)
    with open(settings.paths.raw_records_json, "w", encoding="utf-8") as f:
        json.dump([asdict(r) for r in records], f, indent=2, ensure_ascii=False)

    return records


def load_raw_records(path: Path) -> list[PaperRecord]:
    """Doc JSON snapshot va map thanh list PaperRecord."""
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return [PaperRecord(**item) for item in data]

