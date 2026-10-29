"""
Nyaya Pramaan - Authentication & Authorization Module
Secure password hashing (PBKDF2-SHA256), session tokens, password reset, and Demo Mode.
"""

import hashlib
import os
import secrets
import time
import uuid
from typing import Optional, Dict, Any, Tuple
from backend.db import get_db, row_to_dict

# In-memory session token store (token -> {user_id, expires_at})
# For production scale, can be backed by Redis or DB.
ACTIVE_SESSIONS: Dict[str, Dict[str, Any]] = {}
SESSION_EXPIRATION_SECONDS = 7 * 24 * 3600  # 7 days

DEMO_USER_ID = "demo-advocate-001"
DEMO_EMAIL = "demo@nyayapramaan.gov.in"
DEMO_NAME = "Adv. Priya Sharma (Senior Advocate, SCBA)"


def hash_password(password: str, salt: Optional[str] = None) -> Tuple[str, str]:
    """Hashes a password using PBKDF2-HMAC-SHA256 with a unique salt."""
    if not salt:
        salt = secrets.token_hex(16)
    hashed = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        100000
    ).hex()
    return hashed, salt


def verify_password(password: str, password_hash: str, salt: str) -> bool:
    """Verifies a plain password against the stored hash and salt."""
    test_hash, _ = hash_password(password, salt)
    return secrets.compare_digest(test_hash, password_hash)


def create_session(user_id: str) -> str:
    """Creates a new secure session token."""
    token = secrets.token_urlsafe(32)
    ACTIVE_SESSIONS[token] = {
        "user_id": user_id,
        "expires_at": time.time() + SESSION_EXPIRATION_SECONDS
    }
    return token


def validate_session(token: Optional[str]) -> Optional[Dict[str, Any]]:
    """Validates an active session token and returns the user record."""
    if not token or token not in ACTIVE_SESSIONS:
        return None
    
    session = ACTIVE_SESSIONS[token]
    if time.time() > session["expires_at"]:
        del ACTIVE_SESSIONS[token]
        return None
    
    user_id = session["user_id"]
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, email, full_name, role, created_at FROM users WHERE id = ?", (user_id,))
        user = row_to_dict(cursor.fetchone())
        return user


def destroy_session(token: Optional[str]) -> bool:
    """Logs out by invalidating session token."""
    if token and token in ACTIVE_SESSIONS:
        del ACTIVE_SESSIONS[token]
        return True
    return False


def register_user(email: str, full_name: str, password: str, role: str = "Legal Advocate") -> Dict[str, Any]:
    """Registers a new user with validation and password hashing."""
    email = email.strip().lower()
    full_name = full_name.strip()
    
    if not email or "@" not in email or "." not in email:
        raise ValueError("Please provide a valid email address.")
    if len(password) < 6:
        raise ValueError("Password must be at least 6 characters long.")
    if not full_name:
        raise ValueError("Full name is required.")
        
    pwd_hash, salt = hash_password(password)
    user_id = str(uuid.uuid4())
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
        if cursor.fetchone():
            raise ValueError(f"An account with email '{email}' already exists. Please log in.")
            
        cursor.execute("""
        INSERT INTO users (id, email, full_name, role, password_hash, salt)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, email, full_name, role, pwd_hash, salt))
        conn.commit()
        
    token = create_session(user_id)
    return {
        "user": {
            "id": user_id,
            "email": email,
            "full_name": full_name,
            "role": role
        },
        "token": token
    }


def authenticate_user(email: str, password: str) -> Dict[str, Any]:
    """Authenticates a user via email and password."""
    email = email.strip().lower()
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        row = cursor.fetchone()
        if not row:
            raise ValueError("No account found with this email address.")
            
        user = dict(row)
        if not verify_password(password, user["password_hash"], user["salt"]):
            raise ValueError("Incorrect password. Please try again.")
            
        token = create_session(user["id"])
        return {
            "user": {
                "id": user["id"],
                "email": user["email"],
                "full_name": user["full_name"],
                "role": user["role"]
            },
            "token": token
        }


def request_password_reset(email: str) -> str:
    """Generates a secure password reset token."""
    email = email.strip().lower()
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
        row = cursor.fetchone()
        if not row:
            raise ValueError("No account found with this email address.")
        
        user_id = row["id"]
        reset_token = secrets.token_urlsafe(24)
        cursor.execute("""
        UPDATE users 
        SET reset_token = ?, reset_token_expiry = datetime('now', '+1 hour')
        WHERE id = ?
        """, (reset_token, user_id))
        conn.commit()
        return reset_token


def reset_password(reset_token: str, new_password: str) -> bool:
    """Resets user password given a valid reset token."""
    if len(new_password) < 6:
        raise ValueError("Password must be at least 6 characters long.")
        
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT id FROM users 
        WHERE reset_token = ? AND reset_token_expiry > datetime('now')
        """, (reset_token,))
        row = cursor.fetchone()
        if not row:
            raise ValueError("Invalid or expired password reset token.")
            
        user_id = row["id"]
        pwd_hash, salt = hash_password(new_password)
        cursor.execute("""
        UPDATE users 
        SET password_hash = ?, salt = ?, reset_token = NULL, reset_token_expiry = NULL
        WHERE id = ?
        """, (pwd_hash, salt, user_id))
        conn.commit()
        return True


def ensure_demo_user():
    """Initializes the built-in Demo Account if it doesn't exist."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE id = ?", (DEMO_USER_ID,))
        if not cursor.fetchone():
            pwd_hash, salt = hash_password("NyayaDemo2026!")
            cursor.execute("""
            INSERT INTO users (id, email, full_name, role, password_hash, salt)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (DEMO_USER_ID, DEMO_EMAIL, DEMO_NAME, "Senior Advocate (Supreme Court of India)", pwd_hash, salt))
            conn.commit()


def get_demo_session() -> Dict[str, Any]:
    """Generates an instant 1-click Demo session."""
    ensure_demo_user()
    token = create_session(DEMO_USER_ID)
    return {
        "user": {
            "id": DEMO_USER_ID,
            "email": DEMO_EMAIL,
            "full_name": DEMO_NAME,
            "role": "Senior Advocate (Supreme Court of India)",
            "is_demo": True
        },
        "token": token
    }
