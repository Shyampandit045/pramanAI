"""
Nyaya Pramaan - Dataset & Case Lookup Service
Manages local indexing of Indian court judgments, metadata searches,
and dynamic fetching from the AWS Open Data repository.
Designed for Supreme Court of India and extensible to Indian High Courts.
"""

import os
import re
import json
import sqlite3
from typing import List, Dict, Any, Optional
import requests
from bs4 import BeautifulSoup

from backend.db import get_db, row_to_dict, rows_to_dicts
from backend.pdf_service import extract_pages_from_bytes, extract_pages_from_file

S3_BASE_URL = "https://indian-supreme-court-judgments.s3.amazonaws.com"


def search_local_judgments(
    query: str = "",
    year: Optional[int] = None,
    court: Optional[str] = None,
    limit: int = 25
) -> List[Dict[str, Any]]:
    """
    Searches the local database for judgments matching query terms.
    Supports title, petitioner, respondent, citation, case_id, and year.
    """
    with get_db() as conn:
        cursor = conn.cursor()
        sql = "SELECT * FROM judgments WHERE 1=1"
        params = []

        if query:
            q_clean = f"%{query.strip()}%"
            sql += """ AND (
                title LIKE ? OR 
                petitioner LIKE ? OR 
                respondent LIKE ? OR 
                citation LIKE ? OR 
                case_id LIKE ? OR
                nc_display LIKE ?
            )"""
            params.extend([q_clean, q_clean, q_clean, q_clean, q_clean, q_clean])

        if year:
            sql += " AND year = ?"
            params.append(year)

        if court and court != "All Courts":
            sql += " AND court LIKE ?"
            params.append(f"%{court}%")

        sql += " ORDER BY year DESC, title ASC LIMIT ?"
        params.append(limit)

        cursor.execute(sql, params)
        return rows_to_dicts(cursor.fetchall())


def get_judgment_by_id(judgment_id: str) -> Optional[Dict[str, Any]]:
    """Retrieves a single judgment record by ID."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM judgments WHERE id = ?", (judgment_id,))
        return row_to_dict(cursor.fetchone())


def get_judgment_pages(judgment: Dict[str, Any]) -> Dict[int, str]:
    """
    Returns a dictionary of {page_num: page_text} for a judgment.
    Uses cached extracted_text if available, or extracts from local PDF.
    """
    # 1. Check if extracted_text is stored as JSON in DB
    raw_text = judgment.get("extracted_text")
    if raw_text:
        try:
            pages = json.loads(raw_text)
            if isinstance(pages, dict):
                return {int(k): str(v) for k, v in pages.items()}
        except Exception:
            # Fallback if raw text is stored as a single block
            return {1: str(raw_text)}

    # 2. Check local PDF path
    local_pdf = judgment.get("local_pdf_path")
    if local_pdf and os.path.exists(local_pdf):
        pages_dict, _, _ = extract_pages_from_file(local_pdf)
        # Update cache in DB
        _cache_judgment_pages(judgment["id"], pages_dict)
        return pages_dict

    # 3. If s3_pdf_url exists, attempt targeted fetch
    s3_pdf_url = judgment.get("s3_pdf_url")
    if s3_pdf_url:
        try:
            resp = requests.get(s3_pdf_url, timeout=15)
            if resp.status_code == 200:
                pages_dict, _, _ = extract_pages_from_bytes(resp.content)
                _cache_judgment_pages(judgment["id"], pages_dict)
                return pages_dict
        except Exception as e:
            print(f"Failed to fetch remote S3 PDF: {e}")

    return {1: judgment.get("title", "")}


def _cache_judgment_pages(judgment_id: str, pages_dict: Dict[int, str]):
    """Caches extracted page texts into the database."""
    with get_db() as conn:
        cursor = conn.cursor()
        pages_json = json.dumps({str(k): v for k, v in pages_dict.items()})
        cursor.execute(
            "UPDATE judgments SET extracted_text = ?, page_count = ? WHERE id = ?",
            (pages_json, len(pages_dict), judgment_id)
        )
        conn.commit()


def fetch_from_aws_s3_on_demand(year: int, search_keyword: str) -> List[Dict[str, Any]]:
    """
    On-demand targeted search in AWS Open Data repository for years
    not fully cached locally. Extracts metadata and makes cases available.
    """
    index_url = f"{S3_BASE_URL}/metadata/tar/year={year}/metadata.index.json"
    results = []

    try:
        resp = requests.get(index_url, timeout=10)
        if resp.status_code != 200:
            return []

        data = resp.json()
        parts = data.get("parts", [])
        if not parts:
            return []

        candidate_files = parts[0].get("files", [])
        # Check first 50 files for match
        for fn in candidate_files[:40]:
            meta_url = f"{S3_BASE_URL}/metadata/json/year={year}/{fn}"
            m_resp = requests.get(meta_url, timeout=5)
            if m_resp.status_code == 200:
                meta_json = m_resp.json()
                html = meta_json.get("raw_html", "")
                if search_keyword.lower() in html.lower():
                    soup = BeautifulSoup(html, "html.parser")
                    title_elem = soup.find("strong")
                    title = title_elem.get_text().strip() if title_elem else fn
                    
                    case_path = meta_json.get("path", fn.replace(".json", ""))
                    pdf_url = f"{S3_BASE_URL}/data/pdf/year={year}/english/{case_path}_EN.pdf"
                    
                    case_record = {
                        "id": f"sc-{year}-{case_path}",
                        "case_id": case_path,
                        "citation": f"{year} INSC {case_path.split('_')[-1]}",
                        "title": title,
                        "court": "Supreme Court of India",
                        "year": year,
                        "s3_pdf_url": pdf_url,
                        "s3_json_url": meta_url
                    }
                    results.append(case_record)
                    if len(results) >= 5:
                        break
    except Exception as e:
        print(f"Error querying AWS S3 on-demand: {e}")

    return results
