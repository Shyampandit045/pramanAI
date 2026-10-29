"""
Nyaya Pramaan - Database Layer
SQLite storage for users, judgments, verifications, and support requests.
"""

import sqlite3
import os
import json
from datetime import datetime
from typing import Optional, List, Dict, Any

DB_PATH = os.environ.get("NYAYA_DB_PATH", "nyaya_pramaan.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_db() as conn:
        cursor = conn.cursor()
        
        # 1. Users table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            full_name TEXT NOT NULL,
            role TEXT DEFAULT 'Legal Advocate',
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            reset_token TEXT,
            reset_token_expiry TIMESTAMP
        )
        """)

        # 2. Judgments table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS judgments (
            id TEXT PRIMARY KEY,
            case_id TEXT,
            citation TEXT,
            title TEXT NOT NULL,
            petitioner TEXT,
            respondent TEXT,
            court TEXT DEFAULT 'Supreme Court of India',
            year INTEGER,
            decision_date TEXT,
            disposal_nature TEXT,
            judge TEXT,
            author_judge TEXT,
            nc_display TEXT,
            s3_pdf_url TEXT,
            s3_json_url TEXT,
            local_pdf_path TEXT,
            extracted_text TEXT,
            page_count INTEGER DEFAULT 0,
            is_scanned BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Indexes for fast lookup
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_judgments_title ON judgments(title)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_judgments_citation ON judgments(citation)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_judgments_year ON judgments(year)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_judgments_nc_display ON judgments(nc_display)")

        # 3. Verifications table (each user has their own history)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS verifications (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            judgment_id TEXT,
            case_title TEXT NOT NULL,
            citation TEXT,
            court TEXT,
            submitted_quote TEXT NOT NULL,
            verification_status TEXT NOT NULL,
            similarity_score REAL DEFAULT 0.0,
            matched_original_text TEXT,
            page_number INTEGER,
            diff_data TEXT,
            source_url TEXT,
            is_uploaded_doc BOOLEAN DEFAULT 0,
            uploaded_filename TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_verifications_user ON verifications(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_verifications_created ON verifications(created_at)")

        # 4. Support Tickets / Missing Cases Requests table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS support_tickets (
            id TEXT PRIMARY KEY,
            user_id TEXT,
            case_name TEXT NOT NULL,
            citation TEXT,
            court TEXT,
            issue_category TEXT NOT NULL,
            description TEXT NOT NULL,
            contact_email TEXT,
            status TEXT DEFAULT 'Pending Investigation',
            admin_notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tickets_user ON support_tickets(user_id)")

        conn.commit()


# Helper to convert sqlite3.Row to dict
def row_to_dict(row: Optional[sqlite3.Row]) -> Optional[Dict[str, Any]]:
    if row is None:
        return None
    d = dict(row)
    if "diff_data" in d and d["diff_data"]:
        try:
            d["diff_data"] = json.loads(d["diff_data"])
        except Exception:
            pass
    return d


def rows_to_dicts(rows: List[sqlite3.Row]) -> List[Dict[str, Any]]:
    return [row_to_dict(r) for r in rows if r is not None]
