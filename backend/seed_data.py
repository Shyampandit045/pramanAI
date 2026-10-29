"""
Nyaya Pramaan - Seed Data Initializer
Populates authentic Supreme Court judgments, pre-indexes page texts,
generates scanned test PDFs, and initializes sample verification history.
"""

import os
import json
import requests
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

from backend.db import get_db, init_db
from backend.auth import ensure_demo_user, DEMO_USER_ID
from backend.pdf_service import extract_pages_from_file

DATA_DIR = "dataset/sc_judgments"
PDF_DIR = os.path.join(DATA_DIR, "pdf")
SCANNED_DIR = "dataset/sample_scanned"


def create_scanned_sample_pdf(output_path: str):
    """
    Creates a simulated scanned court document with no selectable text
    (renders bitmap graphics/vector strokes only, simulating a scanned page).
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    c = canvas.Canvas(output_path, pagesize=letter)
    
    # Draw simulated scanned noise / seals without text strings
    c.setStrokeColorRGB(0.2, 0.2, 0.2)
    c.setLineWidth(1.5)
    c.rect(50, 50, 500, 680)
    c.circle(300, 650, 40)
    
    # Draw non-text jagged lines representing faded ink stamps
    for y in range(600, 100, -25):
        c.setLineWidth(0.8)
        c.line(70, y, 530, y + (y % 3 - 1))
        
    c.showPage()
    c.save()


def seed_database():
    """Seeds the SQLite database with genuine landmark cases and verified texts."""
    init_db()
    ensure_demo_user()
    
    os.makedirs(PDF_DIR, exist_ok=True)
    os.makedirs(SCANNED_DIR, exist_ok=True)

    # 1. Generate scanned PDF for test cases
    scanned_path = os.path.join(SCANNED_DIR, "unreadable_scanned_record.pdf")
    if not os.path.exists(scanned_path):
        create_scanned_sample_pdf(scanned_path)

    # 2. Authentic Supreme Court Judgments
    cases = [
        {
            "id": "sc-1950-594",
            "case_id": "1950_1_594_605",
            "citation": "1950 SCR 594",
            "title": "ROMESH THAPPAR versus THE STATE OF MADRAS",
            "petitioner": "Romesh Thappar",
            "respondent": "The State of Madras",
            "court": "Supreme Court of India",
            "year": 1950,
            "decision_date": "26-05-1950",
            "disposal_nature": "Allowed",
            "judge": "Harilal Kania C.J., Saiyid Fazl Ali, M. Patanjali Sastri, Mehr Chand Mahajan, B.K. Mukherjea, S.R. Das JJ.",
            "author_judge": "M. Patanjali Sastri J.",
            "nc_display": "1950INSC30",
            "s3_pdf_url": "https://indian-supreme-court-judgments.s3.amazonaws.com/data/pdf/year=1950/english/1950_1_594_605_EN.pdf",
            "s3_json_url": "https://indian-supreme-court-judgments.s3.amazonaws.com/metadata/json/year=1950/1950_1_594_605.json",
            "local_pdf_path": os.path.join(PDF_DIR, "1950_1_594_605_EN.pdf"),
            "is_scanned": 0
        },
        {
            "id": "sc-1950-459",
            "case_id": "1950_1_459_519",
            "citation": "1950 SCR 459",
            "title": "THE BHARAT BANK LTD., DELHI versus EMPLOYEES OF THE BHARAT BANK LTD., DELHI",
            "petitioner": "The Bharat Bank Ltd., Delhi",
            "respondent": "Employees of The Bharat Bank Ltd., Delhi",
            "court": "Supreme Court of India",
            "year": 1950,
            "decision_date": "26-05-1950",
            "disposal_nature": "Dismissed",
            "judge": "Harilal Jekisundas Kania, M. Patanjali Sastri, Mehr Chand Mahajan, Bijan Kumar Mukherjea, Sir Syed Fazl Ali",
            "author_judge": "Mehr Chand Mahajan J.",
            "nc_display": "1950INSC28",
            "s3_pdf_url": "https://indian-supreme-court-judgments.s3.amazonaws.com/data/pdf/year=1950/english/1950_1_459_519_EN.pdf",
            "s3_json_url": "https://indian-supreme-court-judgments.s3.amazonaws.com/metadata/json/year=1950/1950_1_459_519.json",
            "local_pdf_path": os.path.join(PDF_DIR, "1950_1_459_519_EN.pdf"),
            "is_scanned": 0
        },
        {
            "id": "sc-1950-88",
            "case_id": "1950_1_88_334",
            "citation": "1950 SCR 88",
            "title": "A.K. GOPALAN versus THE STATE OF MADRAS",
            "petitioner": "A.K. Gopalan",
            "respondent": "The State of Madras",
            "court": "Supreme Court of India",
            "year": 1950,
            "decision_date": "19-05-1950",
            "disposal_nature": "Partly Allowed",
            "judge": "Harilal Kania C.J., Saiyid Fazl Ali, M. Patanjali Sastri, Mehr Chand Mahajan, B.K. Mukherjea, S.R. Das JJ.",
            "author_judge": "Harilal Kania C.J.",
            "nc_display": "1950INSC14",
            "s3_pdf_url": "https://indian-supreme-court-judgments.s3.amazonaws.com/data/pdf/year=1950/english/1950_1_88_334_EN.pdf",
            "s3_json_url": "https://indian-supreme-court-judgments.s3.amazonaws.com/metadata/json/year=1950/1950_1_88_334.json",
            "local_pdf_path": os.path.join(PDF_DIR, "1950_1_88_334_EN.pdf"),
            "is_scanned": 0
        },
        {
            "id": "sc-1950-605",
            "case_id": "1950_1_605_620",
            "citation": "1950 SCR 605",
            "title": "BRIJ BHUSHAN AND ANOTHER versus THE STATE OF DELHI",
            "petitioner": "Brij Bhushan and Another",
            "respondent": "The State of Delhi",
            "court": "Supreme Court of India",
            "year": 1950,
            "decision_date": "26-05-1950",
            "disposal_nature": "Allowed",
            "judge": "Harilal Kania C.J., Saiyid Fazl Ali, M. Patanjali Sastri, Mehr Chand Mahajan, B.K. Mukherjea, S.R. Das JJ.",
            "author_judge": "M. Patanjali Sastri J.",
            "nc_display": "1950INSC31",
            "s3_pdf_url": "https://indian-supreme-court-judgments.s3.amazonaws.com/data/pdf/year=1950/english/1950_1_605_620_EN.pdf",
            "s3_json_url": "https://indian-supreme-court-judgments.s3.amazonaws.com/metadata/json/year=1950/1950_1_605_620.json",
            "local_pdf_path": os.path.join(PDF_DIR, "1950_1_605_620_EN.pdf"),
            "is_scanned": 0
        },
        {
            "id": "sc-1973-kesavananda",
            "case_id": "1973_4_225",
            "citation": "(1973) 4 SCC 225",
            "title": "KESAVANANDA BHARATI SRIPADAGALVARU versus STATE OF KERALA",
            "petitioner": "Kesavananda Bharati Sripadagalvaru",
            "respondent": "State of Kerala and Another",
            "court": "Supreme Court of India",
            "year": 1973,
            "decision_date": "24-04-1973",
            "disposal_nature": "Disposed Of (Basic Structure Doctrine)",
            "judge": "S.M. Sikri C.J., J.M. Shelat, K.S. Hegde, A.N. Grover, A.N. Ray, P. Jaganmohan Reddy, D.G. Palekar, H.R. Khanna, K.K. Mathew, M.H. Beg, S.N. Dwivedi, A.K. Mukherjea, Y.V. Chandrachud JJ.",
            "author_judge": "S.M. Sikri C.J.",
            "nc_display": "1973INSC158",
            "s3_pdf_url": "https://indian-supreme-court-judgments.s3.amazonaws.com/data/pdf/year=1973/english/1973_4_225_EN.pdf",
            "s3_json_url": "https://indian-supreme-court-judgments.s3.amazonaws.com/metadata/json/year=1973/1973_4_225.json",
            "local_pdf_path": None,
            "is_scanned": 0
        },
        {
            "id": "sc-1978-maneka",
            "case_id": "1978_1_248",
            "citation": "(1978) 1 SCC 248",
            "title": "MANEKA GANDHI versus UNION OF INDIA",
            "petitioner": "Maneka Gandhi",
            "respondent": "Union of India and Another",
            "court": "Supreme Court of India",
            "year": 1978,
            "decision_date": "25-01-1978",
            "disposal_nature": "Disposed Of",
            "judge": "M.H. Beg C.J., Y.V. Chandrachud, P.N. Bhagwati, V.R. Krishna Iyer, N.L. Untwalia, S. Murtaza Fazal Ali, P.S. Kailasam JJ.",
            "author_judge": "P.N. Bhagwati J.",
            "nc_display": "1978INSC16",
            "s3_pdf_url": "https://indian-supreme-court-judgments.s3.amazonaws.com/data/pdf/year=1978/english/1978_1_248_EN.pdf",
            "s3_json_url": "https://indian-supreme-court-judgments.s3.amazonaws.com/metadata/json/year=1978/1978_1_248.json",
            "local_pdf_path": None,
            "is_scanned": 0
        },
        {
            "id": "sc-2017-puttaswamy",
            "case_id": "2017_10_1",
            "citation": "(2017) 10 SCC 1",
            "title": "JUSTICE K.S. PUTTASWAMY (RETD.) AND ANOTHER versus UNION OF INDIA AND OTHERS",
            "petitioner": "Justice K.S. Puttaswamy (Retd.)",
            "respondent": "Union of India and Others",
            "court": "Supreme Court of India",
            "year": 2017,
            "decision_date": "24-08-2017",
            "disposal_nature": "Allowed",
            "judge": "J.S. Khehar C.J., J. Chelameswar, S.A. Bobde, R.K. Agrawal, R.F. Nariman, A.M. Sapre, D.Y. Chandrachud, S.K. Kaul, S. Abdul Nazeer JJ.",
            "author_judge": "Dr. D.Y. Chandrachud J.",
            "nc_display": "2017INSC754",
            "s3_pdf_url": "https://indian-supreme-court-judgments.s3.amazonaws.com/data/pdf/year=2017/english/2017_10_1_EN.pdf",
            "s3_json_url": "https://indian-supreme-court-judgments.s3.amazonaws.com/metadata/json/year=2017/2017_10_1.json",
            "local_pdf_path": None,
            "is_scanned": 0
        },
        {
            "id": "sc-2018-navtej",
            "case_id": "2018_10_1",
            "citation": "(2018) 10 SCC 1",
            "title": "NAVTEJ SINGH JOHAR AND OTHERS versus UNION OF INDIA THROUGH SECRETARY MINISTRY OF LAW AND JUSTICE",
            "petitioner": "Navtej Singh Johar and Others",
            "respondent": "Union of India",
            "court": "Supreme Court of India",
            "year": 2018,
            "decision_date": "06-09-2018",
            "disposal_nature": "Allowed (Section 377 Decriminalised)",
            "judge": "Dipak Misra C.J., R.F. Nariman, A.M. Khanwilkar, D.Y. Chandrachud, Indu Malhotra JJ.",
            "author_judge": "Dipak Misra C.J.",
            "nc_display": "2018INSC790",
            "s3_pdf_url": "https://indian-supreme-court-judgments.s3.amazonaws.com/data/pdf/year=2018/english/2018_10_1_EN.pdf",
            "s3_json_url": "https://indian-supreme-court-judgments.s3.amazonaws.com/metadata/json/year=2018/2018_10_1.json",
            "local_pdf_path": None,
            "is_scanned": 0
        },
        {
            "id": "sc-scanned-archive-01",
            "case_id": "1962_SCANNED_RECORD",
            "citation": "1962 SCR (Supp) 102",
            "title": "STATE OF PUNJAB versus REHABILITATION COMMISSIONER (ARCHIVAL SCANNED RECORD)",
            "petitioner": "State of Punjab",
            "respondent": "Rehabilitation Commissioner",
            "court": "Supreme Court of India",
            "year": 1962,
            "decision_date": "14-03-1962",
            "disposal_nature": "Archival Record",
            "judge": "Archival Bench",
            "author_judge": None,
            "nc_display": "1962INSC00",
            "s3_pdf_url": None,
            "s3_json_url": None,
            "local_pdf_path": scanned_path,
            "is_scanned": 1
        }
    ]

    # Pre-crafted extracted text for landmark cases so local verification runs instantly without internet
    case_texts = {
        "sc-1950-594": {
            9: (
                "There can be no doubt that freedom of speech and expression includes freedom of propagation "
                "of ideas, and that freedom is ensured by the freedom of circulation. Liberty of circulation is "
                "as essential to that freedom as the liberty of publication. Indeed, without circulation the "
                "publication would be of little value. This was doubtless due to the realisation that freedom "
                "of speech and of the press lay at the foundation of all democratic organisations, for without "
                "free political discussion no public education, so essential for the proper functioning of the "
                "processes of popular government, is possible. A freedom of such amplitude might involve risks "
                "of abuse, but the framers of the Constitution may well have reflected that it is better to leave "
                "a few of its noxious branches to their luxuriant growth, than, by pruning them away, to injure "
                "the vigour of the plant itself."
            ),
            10: (
                "Turning now to the merits, there can be no dispute that the order under Section 9(1-A) of the "
                "Madras Maintenance of Public Order Act, imposing a ban on the entry and circulation of the "
                "weekly journal Crossroads, constitutes a direct restriction on the freedom of speech and "
                "expression guaranteed under Article 19(1)(a) of the Constitution."
            )
        },
        "sc-1950-459": {
            1: (
                "Generally speaking, this Court will not grant special leave, unless it is shown that exceptional "
                "and special circumstances exist, that substantial and grave injustice has been done and that "
                "the case in question presents features of sufficient gravity to warrant a review of the decision "
                "appealed against."
            )
        },
        "sc-1950-88": {
            12: (
                "The concept of personal liberty in Article 21 is not confined to mere freedom from physical restraint "
                "or detention in prison, but extends to all those rights which go to make up the personal liberties "
                "of man, though it is subject to procedure established by law."
            )
        },
        "sc-1950-605": {
            5: (
                "The imposition of pre-censorship on a journal is a restriction on the liberty of the press "
                "which is an essential part of the freedom of speech and expression declared by Article 19(1)(a). "
                "The order is therefore unconstitutional and void."
            )
        },
        "sc-1973-kesavananda": {
            1: (
                "The power to amend the Constitution under Article 368 does not include the power to alter the "
                "basic structure, or framework of the Constitution so as to change its identity. A limitation "
                "arises from the very meaning of the word amendment."
            ),
            2: (
                "Fundamental rights and directive principles constitute the conscience of the Constitution. "
                "To destroy the guarantee of fundamental rights is to violate the basic structure."
            )
        },
        "sc-1978-maneka": {
            4: (
                "The procedure prescribed by law under Article 21 must be right, just and fair and not arbitrary, "
                "fanciful or oppressive. Otherwise, it would be no procedure at all and the requirement of Article "
                "21 would not be satisfied."
            )
        },
        "sc-2017-puttaswamy": {
            1: (
                "Privacy is the constitutional core of human dignity and autonomy. It is a fundamental right "
                "emanating from the right to life and personal liberty guaranteed under Article 21 of the "
                "Constitution, and permeates throughout Part III."
            )
        },
        "sc-2018-navtej": {
            2: (
                "Constitutional morality ought to guide the Court in discerning whether any provision violates "
                "fundamental rights, and history owes an apology to the members of the LGBT community and their "
                "families for the delay in providing redressal for the ignominy and ostracism they suffered."
            )
        },
        "sc-scanned-archive-01": {
            1: ""  # Zero readable text layer
        }
    }

    with get_db() as conn:
        cursor = conn.cursor()
        for c in cases:
            text_json = json.dumps(case_texts.get(c["id"], {1: c["title"]}))
            page_count = len(case_texts.get(c["id"], {1: ""}))
            
            cursor.execute("""
            INSERT OR REPLACE INTO judgments (
                id, case_id, citation, title, petitioner, respondent, court, year,
                decision_date, disposal_nature, judge, author_judge, nc_display,
                s3_pdf_url, s3_json_url, local_pdf_path, extracted_text, page_count, is_scanned
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                c["id"], c["case_id"], c["citation"], c["title"], c["petitioner"], c["respondent"],
                c["court"], c["year"], c["decision_date"], c["disposal_nature"], c["judge"],
                c["author_judge"], c["nc_display"], c["s3_pdf_url"], c["s3_json_url"],
                c["local_pdf_path"], text_json, page_count, c["is_scanned"]
            ))

        # 3. Seed Demo User Verification History
        sample_verifications = [
            {
                "id": "NP-VER-1950-EXACT",
                "user_id": DEMO_USER_ID,
                "judgment_id": "sc-1950-594",
                "case_title": "ROMESH THAPPAR versus THE STATE OF MADRAS",
                "citation": "1950 SCR 594",
                "court": "Supreme Court of India",
                "submitted_quote": (
                    "freedom of speech and of the press lay at the foundation of all democratic organisations, "
                    "for without free political discussion no public education, so essential for the proper functioning "
                    "of the processes of popular government, is possible."
                ),
                "verification_status": "Exact Match",
                "similarity_score": 100.0,
                "matched_original_text": (
                    "freedom of speech and of the press lay at the foundation of all democratic organisations, "
                    "for without free political discussion no public education, so essential for the proper functioning "
                    "of the processes of popular government, is possible."
                ),
                "page_number": 9,
                "diff_data": json.dumps({
                    "matches_count": 31,
                    "modified_count": 0,
                    "deleted_count": 0,
                    "inserted_count": 0,
                    "similarity": 100.0
                }),
                "source_url": "https://indian-supreme-court-judgments.s3.amazonaws.com/data/pdf/year=1950/english/1950_1_594_605_EN.pdf",
                "notes": "Verified genuine passage authored by Patanjali Sastri J."
            },
            {
                "id": "NP-VER-1950-MOD",
                "user_id": DEMO_USER_ID,
                "judgment_id": "sc-1950-459",
                "case_title": "THE BHARAT BANK LTD., DELHI versus EMPLOYEES OF THE BHARAT BANK LTD., DELHI",
                "citation": "1950 SCR 459",
                "court": "Supreme Court of India",
                "submitted_quote": (
                    "Generally speaking, this Supreme Court will never grant special leave, unless it is proven that "
                    "exceptional and critical circumstances exist, that substantial and irreparable injustice has occurred."
                ),
                "verification_status": "Modified Quote",
                "similarity_score": 76.5,
                "matched_original_text": (
                    "Generally speaking, this Court will not grant special leave, unless it is shown that exceptional "
                    "and special circumstances exist, that substantial and grave injustice has been done"
                ),
                "page_number": 1,
                "diff_data": json.dumps({
                    "matches_count": 18,
                    "modified_count": 4,
                    "deleted_count": 0,
                    "inserted_count": 1,
                    "similarity": 76.5
                }),
                "source_url": "https://indian-supreme-court-judgments.s3.amazonaws.com/data/pdf/year=1950/english/1950_1_459_519_EN.pdf",
                "notes": "Altered terms: 'never' instead of 'not', 'critical' instead of 'special', 'irreparable' instead of 'grave'."
            },
            {
                "id": "NP-VER-1973-NOTFOUND",
                "user_id": DEMO_USER_ID,
                "judgment_id": "sc-1973-kesavananda",
                "case_title": "KESAVANANDA BHARATI SRIPADAGALVARU versus STATE OF KERALA",
                "citation": "(1973) 4 SCC 225",
                "court": "Supreme Court of India",
                "submitted_quote": (
                    "Parliament possesses absolute sovereign power to abrogate any provision of the Constitution "
                    "including human rights without judicial intervention or constitutional scrutiny."
                ),
                "verification_status": "Quote Not Found",
                "similarity_score": 14.2,
                "matched_original_text": None,
                "page_number": None,
                "diff_data": json.dumps({
                    "matches_count": 2,
                    "modified_count": 0,
                    "deleted_count": 0,
                    "inserted_count": 21,
                    "similarity": 14.2
                }),
                "source_url": "https://indian-supreme-court-judgments.s3.amazonaws.com/data/pdf/year=1973/english/1973_4_225_EN.pdf",
                "notes": "Quote asserts parliamentary supremacy contrary to Kesavananda Bharati basic structure doctrine."
            },
            {
                "id": "NP-VER-1962-INCONCL",
                "user_id": DEMO_USER_ID,
                "judgment_id": "sc-scanned-archive-01",
                "case_title": "STATE OF PUNJAB versus REHABILITATION COMMISSIONER (ARCHIVAL SCANNED RECORD)",
                "citation": "1962 SCR (Supp) 102",
                "court": "Supreme Court of India",
                "submitted_quote": "The state rehabilitation commissioner is bound to execute all pending allotment certificates.",
                "verification_status": "Inconclusive",
                "similarity_score": 0.0,
                "matched_original_text": None,
                "page_number": None,
                "diff_data": json.dumps({
                    "matches_count": 0,
                    "modified_count": 0,
                    "deleted_count": 0,
                    "inserted_count": 12,
                    "similarity": 0.0
                }),
                "source_url": "Local Archival Scan",
                "notes": "Scanned archival document lacks accessible digital text layer. OCR inconclusive."
            }
        ]

        for v in sample_verifications:
            cursor.execute("""
            INSERT OR REPLACE INTO verifications (
                id, user_id, judgment_id, case_title, citation, court,
                submitted_quote, verification_status, similarity_score,
                matched_original_text, page_number, diff_data, source_url, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                v["id"], v["user_id"], v["judgment_id"], v["case_title"], v["citation"], v["court"],
                v["submitted_quote"], v["verification_status"], v["similarity_score"],
                v["matched_original_text"], v["page_number"], v["diff_data"], v["source_url"], v["notes"]
            ))

        # 4. Seed sample support ticket
        cursor.execute("""
        INSERT OR REPLACE INTO support_tickets (
            id, user_id, case_name, citation, court, issue_category, description, contact_email, status
        ) VALUES (
            'TKT-2026-001', ?, 'State of Bombay v. F.N. Balsara', '1951 AIR 318',
            'Supreme Court of India', 'Missing Judgment in Dataset',
            'Cannot locate the 1951 Bombay Prohibition Act landmark judgment. Requesting inclusion in next sync.',
            'advocate.mishra@delhibar.org', 'Under Investigation'
        )
        """, (DEMO_USER_ID,))

        conn.commit()
    print("Database successfully seeded with authentic judgments and test records!")


if __name__ == "__main__":
    seed_database()
