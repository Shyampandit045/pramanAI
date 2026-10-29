"""
Nyaya Pramaan - Comprehensive Verification & Specification Test Suite
Exercises all 8 testing criteria defined in Section 9:
  1. Genuine quotation that matches the original judgment (Exact Match).
  2. Real case with a modified quotation (Modified Quote & detailed diff).
  3. Real case with quote not present (Quote Not Found & rule compliance: never labeled fabricated).
  4. Incorrect citation / missing judgment (404 with guidance notice).
  5. Uploaded PDF verification (direct PDF upload and text verification).
  6. Unreadable or scanned document (Inconclusive status with OCR notes).
  7. Login, logout, password reset, and access control.
  8. Help request submission and report downloads (ReportLab PDF & JSON audit).
"""

import sys
import os
import io
import json

from backend.db import init_db, get_db, row_to_dict
from backend.seed_data import seed_database
from backend.auth import (
    register_user,
    authenticate_user,
    request_password_reset,
    reset_password,
    validate_session,
    destroy_session,
    get_demo_session,
    DEMO_USER_ID
)
from backend.verification_engine import (
    verify_quotation,
    compute_word_diff,
    find_best_matching_passage,
    normalize_text
)
from backend.pdf_service import (
    validate_pdf_bytes,
    extract_pages_from_bytes,
    extract_pages_from_file
)
from backend.dataset_service import (
    search_local_judgments,
    get_judgment_by_id,
    get_judgment_pages
)
from backend.report_generator import generate_pdf_report, generate_json_report
from backend.main import (
    verify_quote_endpoint,
    VerifyQuoteRequest,
    RegisterRequest,
    register_endpoint,
    LoginRequest,
    login_endpoint,
    ForgotPasswordRequest,
    forgot_password_endpoint,
    ResetPasswordRequest,
    reset_password_endpoint,
    SupportTicketRequest,
    create_support_ticket,
    download_pdf_report,
    download_json_report,
    get_system_stats,
    list_cases
)


if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def run_tests():
    print("\n" + "="*70)
    print("  NYAYA PRAMAAN - OFFICIAL VERIFICATION TEST SUITE")
    print("="*70 + "\n")

    # Seed Database
    print("[INIT] Initializing database and authentic Supreme Court judgments...")
    init_db()
    seed_database()
    demo_user = {
        "id": DEMO_USER_ID,
        "email": "demo@nyayapramaan.gov.in",
        "full_name": "Adv. Priya Sharma (Senior Advocate, SCBA)",
        "role": "Senior Advocate"
    }
    print("  -> Initialized successfully.\n")

    # -------------------------------------------------------------
    # 1. Genuine quotation that matches original judgment
    # -------------------------------------------------------------
    print("[TEST 1] Testing Genuine Quotation (Romesh Thappar v. State of Madras 1950)...")
    exact_quote = (
        "freedom of speech and of the press lay at the foundation of all democratic organisations, "
        "for without free political discussion no public education, so essential for the proper functioning "
        "of the processes of popular government, is possible."
    )
    req = VerifyQuoteRequest(judgment_id="sc-1950-594", submitted_quote=exact_quote)
    res = verify_quote_endpoint(req, current_user=demo_user)
    
    assert res["status"] == "Exact Match", f"Expected 'Exact Match', got '{res['status']}'"
    assert res["similarity_score"] == 100.0, f"Expected 100.0%, got {res['similarity_score']}"
    assert res["page_number"] == 9, f"Expected Page 9, got {res['page_number']}"
    assert res["diff"]["matches_count"] >= 30, f"Expected matches_count >= 30, got {res['diff']['matches_count']}"
    assert res["diff"]["modified_count"] == 0, "Exact match should have 0 modified words"
    assert res["diff"]["inserted_count"] == 0, "Exact match should have 0 inserted words"
    print(f"  -> PASS: Verified as '{res['status']}' (100.0% match, verified on Page {res['page_number']}).")

    # -------------------------------------------------------------
    # 2. Real case with modified quotation
    # -------------------------------------------------------------
    print("\n[TEST 2] Testing Modified Quotation (The Bharat Bank Ltd. 1950)...")
    mod_quote = (
        "Generally speaking, this Supreme Court will never grant special leave, unless it is proven that "
        "exceptional and critical circumstances exist, that substantial and irreparable injustice has occurred."
    )
    req_mod = VerifyQuoteRequest(judgment_id="sc-1950-459", submitted_quote=mod_quote)
    res_mod = verify_quote_endpoint(req_mod, current_user=demo_user)
    
    assert res_mod["status"] == "Modified Quote", f"Expected 'Modified Quote', got '{res_mod['status']}'"
    assert 50.0 <= res_mod["similarity_score"] < 99.0, f"Expected score 50-99%, got {res_mod['similarity_score']}"
    assert res_mod["diff"]["modified_count"] > 0, "Expected modified words detected"
    print(f"  -> PASS: Verified as '{res_mod['status']}' (Score: {res_mod['similarity_score']}%, Alterations caught: {res_mod['diff']['modified_count']}).")

    # -------------------------------------------------------------
    # 3. Real case with quotation not found (RULE: Never label as fabricated)
    # -------------------------------------------------------------
    print("\n[TEST 3] Testing Quote Not Found (Kesavananda Bharati 1973)...")
    not_found_quote = (
        "Parliament possesses absolute sovereign power to abrogate any provision of the Constitution "
        "including human rights without judicial intervention or constitutional scrutiny."
    )
    req_nf = VerifyQuoteRequest(judgment_id="sc-1973-kesavananda", submitted_quote=not_found_quote)
    res_nf = verify_quote_endpoint(req_nf, current_user=demo_user)
    
    assert res_nf["status"] == "Quote Not Found", f"Expected 'Quote Not Found', got '{res_nf['status']}'"
    # Strict specification compliance check:
    assert "fabricated" not in res_nf["status"].lower(), "CRITICAL VIOLATION: Labeled quote as fabricated!"
    assert "does not necessarily mean the quotation is fabricated" in res_nf["explanation"], "Missing mandatory judicial non-fabrication disclaimer!"
    print(f"  -> PASS: Verified as '{res_nf['status']}'. Rule strictly respected (non-fabrication notice present).")

    # -------------------------------------------------------------
    # 4. Incorrect citation / missing judgment
    # -------------------------------------------------------------
    print("\n[TEST 4] Testing Missing Judgment / Incorrect Citation...")
    req_missing = VerifyQuoteRequest(judgment_id="non-existent-case-12345", submitted_quote="Some quote")
    try:
        verify_quote_endpoint(req_missing, current_user=demo_user)
        assert False, "Expected HTTPException for missing case"
    except Exception as e:
        detail_msg = getattr(e, "detail", str(e))
        assert "We couldn't find the requested judgment" in detail_msg
        assert "This does not necessarily mean the quotation is fake" in detail_msg
        print(f"  -> PASS: Missing case safely raises judicial advisory: '{detail_msg}'")

    # -------------------------------------------------------------
    # 5. Uploaded PDF verification
    # -------------------------------------------------------------
    print("\n[TEST 5] Testing Uploaded PDF Document Verification...")
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    pdf_buffer = io.BytesIO()
    c = canvas.Canvas(pdf_buffer, pagesize=letter)
    c.drawString(100, 720, "SUPREME COURT OF INDIA RECORD OF PROCEEDINGS")
    c.drawString(100, 690, "The principle of natural justice requires that no person shall be condemned unheard.")
    c.drawString(100, 670, "Audi alteram partem is an indispensable prerequisite of fair administrative action.")
    c.showPage()
    c.save()
    custom_pdf_bytes = pdf_buffer.getvalue()

    # Validate PDF bytes
    validate_pdf_bytes(custom_pdf_bytes, "counsel_uploaded_record.pdf")
    pages, num_p, scanned = extract_pages_from_bytes(custom_pdf_bytes)
    assert num_p == 1, f"Expected 1 page, got {num_p}"
    assert not scanned, "Digital PDF should not be classified as scanned"

    test_upload_quote = "The principle of natural justice requires that no person shall be condemned unheard."
    res_upload = verify_quotation(
        submitted_quote=test_upload_quote,
        document_pages=pages,
        is_scanned=scanned
    )
    assert res_upload["status"] == "Exact Match", f"Expected Exact Match, got {res_upload['status']}"
    assert res_upload["similarity_score"] == 100.0
    print(f"  -> PASS: Uploaded PDF extracted and verified as '{res_upload['status']}' (100.0% match).")

    # -------------------------------------------------------------
    # 6. Unreadable or scanned document
    # -------------------------------------------------------------
    print("\n[TEST 6] Testing Scanned / Unreadable Document (Inconclusive)...")
    scanned_case = get_judgment_by_id("sc-scanned-archive-01")
    scanned_pages = get_judgment_pages(scanned_case)
    res_scanned = verify_quotation(
        submitted_quote="The state rehabilitation commissioner is bound to execute all pending allotment certificates.",
        document_pages=scanned_pages,
        is_scanned=bool(scanned_case.get("is_scanned", 1))
    )
    assert res_scanned["status"] == "Inconclusive", f"Expected 'Inconclusive', got '{res_scanned['status']}'"
    assert "Document text layer is unreadable or incomplete" in res_scanned["explanation"]
    assert len(res_scanned.get("reasons", [])) > 0
    print(f"  -> PASS: Verified as '{res_scanned['status']}' with OCR limitation notice: '{res_scanned['explanation']}'")

    # -------------------------------------------------------------
    # 7. Login, Logout, Password Reset, and Access Control
    # -------------------------------------------------------------
    print("\n[TEST 7] Testing Authentication Engine, Password Hashing, & Access Control...")
    import time
    test_email = f"advocate.mehta.{int(time.time())}@bombaybar.org"
    test_pwd = "Pleadings2026!#"
    
    # Register
    reg_req = RegisterRequest(
        email=test_email,
        full_name="Adv. Rohinton Mehta",
        password=test_pwd,
        role="Bombay High Court Advocate"
    )
    reg_res = register_endpoint(reg_req)
    assert reg_res["user"]["email"] == test_email
    token = reg_res["token"]
    assert token is not None

    # Validate active session
    user_rec = validate_session(token)
    assert user_rec is not None
    assert user_rec["email"] == test_email

    # Check password not stored in plaintext
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT password_hash FROM users WHERE email = ?", (test_email,))
        stored_hash = cursor.fetchone()[0]
        assert stored_hash != test_pwd, "CRITICAL ERROR: Plaintext password stored!"
        assert len(stored_hash) == 64, "PBKDF2 SHA-256 hash length should be 64 hex characters"

    # Request Password Reset
    forgot_req = ForgotPasswordRequest(email=test_email)
    forgot_res = forgot_password_endpoint(forgot_req)
    reset_token = forgot_res["reset_token"]
    assert reset_token is not None

    # Reset Password
    new_pwd = "UpdatedPleadings2026!"
    reset_req = ResetPasswordRequest(reset_token=reset_token, new_password=new_pwd)
    reset_res = reset_password_endpoint(reset_req)
    assert "successfully updated" in reset_res["message"]

    # Login with new password
    login_req = LoginRequest(email=test_email, password=new_pwd)
    login_res = login_endpoint(login_req)
    assert login_res["user"]["email"] == test_email
    new_token = login_res["token"]

    # Logout
    destroy_session(new_token)
    assert validate_session(new_token) is None, "Session should be invalidated after logout"

    # Demo session test
    demo_sess = get_demo_session()
    assert demo_sess["user"]["is_demo"] is True
    print("  -> PASS: Registration, PBKDF2 hashing, Password Reset, Login, Session Invalidation, & Demo validated.")

    # -------------------------------------------------------------
    # 8. Help request submission and report downloads (PDF & JSON)
    # -------------------------------------------------------------
    print("\n[TEST 8] Testing Help Request Submission and Report Downloads...")
    # Help request
    ticket_req = SupportTicketRequest(
        case_name="K.G. Khosla & Co. v. Deputy Commissioner of Commercial Taxes",
        citation="1966 AIR 1216",
        court="Supreme Court of India",
        issue_category="Missing Judgment in Repository",
        description="Quotation regarding sales tax exemption on imported goods needs verification.",
        contact_email="advocate.mehta@bombaybar.org"
    )
    ticket_res = create_support_ticket(ticket_req, current_user=demo_user)
    assert ticket_res["ticket_id"].startswith("TKT-")
    print(f"  -> PASS: Support ticket registered with ID: {ticket_res['ticket_id']}")

    # Report downloads
    ver_id = "NP-VER-1950-EXACT"
    # PDF report
    pdf_resp = download_pdf_report(ver_id, current_user=demo_user)
    assert pdf_resp.media_type == "application/pdf"
    assert pdf_resp.body.startswith(b"%PDF"), "Generated PDF does not start with %PDF magic header"
    print(f"  -> PASS: Official ReportLab PDF Report generated ({len(pdf_resp.body)} bytes).")

    # JSON audit report
    json_resp = download_json_report(ver_id, current_user=demo_user)
    assert json_resp.media_type == "application/json"
    audit_data = json.loads(json_resp.body.decode("utf-8"))
    assert audit_data["certificate_id"] == ver_id
    assert audit_data["verification_result"]["status"] == "Exact Match"
    assert "legal_attribution" in audit_data
    print(f"  -> PASS: Structured JSON Audit Report generated and verified.")

    # -------------------------------------------------------------
    # System Stats & Case Listing
    # -------------------------------------------------------------
    stats = get_system_stats()
    assert stats["total_judgments_indexed"] >= 8
    cases = list_cases(q="Romesh", limit=5)
    assert cases["count"] >= 1
    assert "ROMESH THAPPAR" in cases["cases"][0]["title"]
    print(f"  -> PASS: Search and Statistics APIs verified ({stats['total_judgments_indexed']} judgments indexed).")

    print("\n" + "="*70)
    print("  ALL 8 CORE SYSTEM SPECIFICATIONS PASSED WITH 100% SUCCESS!")
    print("="*70 + "\n")


if __name__ == "__main__":
    run_tests()
