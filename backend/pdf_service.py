"""
Nyaya Pramaan - PDF Processing & Document Text Service
Extracts text page-by-page, detects scanned/unreadable documents, and safely validates uploads.
"""

import io
import os
from typing import Dict, Any, Tuple
import pypdf

MAX_UPLOAD_SIZE_BYTES = 25 * 1024 * 1024  # 25MB
MIN_WORDS_PER_PAGE_THRESHOLD = 5


def validate_pdf_bytes(file_bytes: bytes, filename: str) -> None:
    """Validates PDF file headers and size restrictions."""
    if len(file_bytes) > MAX_UPLOAD_SIZE_BYTES:
        raise ValueError(f"Uploaded file exceeds the 25MB limit (Size: {len(file_bytes) / (1024*1024):.1f}MB).")
    
    if len(file_bytes) < 4 or not file_bytes.startswith(b"%PDF"):
        raise ValueError("Invalid file format. Only authentic PDF documents (.pdf) are supported.")


def extract_pages_from_bytes(file_bytes: bytes) -> Tuple[Dict[int, str], int, bool]:
    """
    Extracts text per page from binary PDF content.
    Returns:
      (pages_dict, total_pages, is_scanned)
    """
    try:
        reader = pypdf.PdfReader(io.BytesIO(file_bytes))
        total_pages = len(reader.pages)
        if total_pages == 0:
            return {}, 0, True

        pages_dict: Dict[int, str] = {}
        total_extracted_words = 0

        for page_idx, page in enumerate(reader.pages, start=1):
            try:
                page_text = page.extract_text() or ""
                # Strip excessive control characters
                cleaned = " ".join(page_text.split())
                pages_dict[page_idx] = cleaned
                total_extracted_words += len(cleaned.split())
            except Exception:
                pages_dict[page_idx] = ""

        # If average words per page is less than threshold, it's likely a scanned/image PDF
        avg_words = total_extracted_words / total_pages if total_pages > 0 else 0
        is_scanned = (avg_words < MIN_WORDS_PER_PAGE_THRESHOLD) or (total_extracted_words < 10)

        return pages_dict, total_pages, is_scanned

    except pypdf.errors.PdfReadError as e:
        raise ValueError(f"Corrupted or password-protected PDF document: {str(e)}")
    except Exception as e:
        raise ValueError(f"Unable to parse PDF document: {str(e)}")


def extract_pages_from_file(file_path: str) -> Tuple[Dict[int, str], int, bool]:
    """Extracts text per page from a local PDF file path."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"PDF file not found at path: {file_path}")
        
    with open(file_path, "rb") as f:
        content = f.read()
    return extract_pages_from_bytes(content)
