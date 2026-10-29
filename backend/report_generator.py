"""
Nyaya Pramaan - Verification Report Generator
Generates official legal verification certificates in PDF format (via ReportLab)
and structured JSON format for audit, archiving, and judicial reference.
"""

import io
import json
import hashlib
from datetime import datetime
from typing import Dict, Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
    KeepTogether
)


def generate_json_report(verification_record: Dict[str, Any]) -> str:
    """Formats verification data into a structured, exportable JSON string."""
    report = {
        "report_type": "Nyaya Pramaan Legal Quote Verification Audit",
        "certificate_id": verification_record.get("id"),
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "case_details": {
            "title": verification_record.get("case_title"),
            "citation": verification_record.get("citation"),
            "court": verification_record.get("court"),
            "source_url": verification_record.get("source_url")
        },
        "verification_result": {
            "status": verification_record.get("verification_status"),
            "similarity_score_pct": verification_record.get("similarity_score"),
            "matched_page_number": verification_record.get("page_number"),
            "submitted_quotation": verification_record.get("submitted_quote"),
            "original_matched_text": verification_record.get("matched_original_text"),
            "diff_summary": verification_record.get("diff_data")
        },
        "legal_attribution": {
            "dataset": "Indian Supreme Court Judgments (AWS Open Data Registry)",
            "license": "Creative Commons Attribution 4.0 (CC BY 4.0)",
            "source_repository": "https://github.com/vanga/indian-supreme-court-judgments",
            "disclaimer": (
                "Nyaya Pramaan provides automated algorithmic text verification against official court records. "
                "A 'Quote Not Found' status indicates the quotation is not present in the verified document "
                "and does not conclude intentional fabrication."
            )
        }
    }
    return json.dumps(report, indent=2, ensure_ascii=False)


def generate_pdf_report(verification_record: Dict[str, Any]) -> bytes:
    """
    Generates a formal legal verification certificate PDF using ReportLab.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()
    
    # Custom Palette
    c_navy = colors.HexColor("#0B1B3D")
    c_gold = colors.HexColor("#C5A059")
    c_dark = colors.HexColor("#1E293B")
    c_light_gray = colors.HexColor("#F8FAFC")
    c_border = colors.HexColor("#CBD5E1")
    
    # Status colors
    status_str = str(verification_record.get("verification_status", "Inconclusive"))
    if "Exact" in status_str:
        status_bg = colors.HexColor("#DCFCE7")
        status_text = colors.HexColor("#15803D")
    elif "Modified" in status_str:
        status_bg = colors.HexColor("#FEF3C7")
        status_text = colors.HexColor("#B45309")
    elif "Not Found" in status_str:
        status_bg = colors.HexColor("#FFE4E6")
        status_text = colors.HexColor("#BE123C")
    else:
        status_bg = colors.HexColor("#F1F5F9")
        status_text = colors.HexColor("#475569")

    # Typography Styles
    title_style = ParagraphStyle(
        "CertTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        textColor=c_navy,
        alignment=1
    )
    subtitle_style = ParagraphStyle(
        "CertSubTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=13,
        textColor=c_gold,
        alignment=1
    )
    h2_style = ParagraphStyle(
        "H2",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=15,
        textColor=c_navy
    )
    body_style = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=c_dark
    )
    body_italic = ParagraphStyle(
        "BodyItalic",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#334155")
    )
    quote_style = ParagraphStyle(
        "QuoteBlock",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=c_dark,
        backColor=colors.HexColor("#F8FAFC"),
        borderColor=c_border,
        borderWidth=1,
        borderPadding=8,
        spaceAfter=6
    )
    footer_style = ParagraphStyle(
        "Footer",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7,
        leading=10,
        textColor=colors.HexColor("#64748B"),
        alignment=1
    )

    story = []

    # Header
    story.append(Paragraph("NYAYA PRAMAAN (न्याय प्रमाण)", title_style))
    story.append(Spacer(1, 3))
    story.append(Paragraph("OFFICIAL COURT JUDGMENT QUOTE VERIFICATION CERTIFICATE", subtitle_style))
    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", thickness=1.5, color=c_gold, spaceAfter=12))

    # Certificate ID & Timestamp banner
    cert_id = verification_record.get("id", "NP-2026-REF")
    timestamp = verification_record.get("created_at", datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"))
    
    meta_banner = [
        [
            Paragraph(f"<b>Certificate ID:</b> {cert_id}", body_style),
            Paragraph(f"<b>Verification Date:</b> {timestamp}", body_style)
        ]
    ]
    t_banner = Table(meta_banner, colWidths=[260, 260])
    t_banner.setStyle(TableStyle([
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('TOPPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(t_banner)
    story.append(Spacer(1, 10))

    # Case Details Box
    case_title = verification_record.get("case_title", "Unknown Title")
    citation = verification_record.get("citation", "Not Available")
    court = verification_record.get("court", "Supreme Court of India")
    source_url = verification_record.get("source_url", "Official Court Archive")
    page_num = verification_record.get("page_number")
    page_display = f"Page {page_num}" if page_num else "Whole Document"

    case_data = [
        [Paragraph("<b>Case Name:</b>", body_style), Paragraph(case_title, body_style)],
        [Paragraph("<b>Official Citation:</b>", body_style), Paragraph(citation, body_style)],
        [Paragraph("<b>Court Jurisdiction:</b>", body_style), Paragraph(court, body_style)],
        [Paragraph("<b>Verified Page:</b>", body_style), Paragraph(page_display, body_style)],
        [Paragraph("<b>Source Record:</b>", body_style), Paragraph(source_url, body_style)]
    ]
    t_case = Table(case_data, colWidths=[120, 400])
    t_case.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
        ('GRID', (0, 0), (-1, -1), 0.5, c_border),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(Paragraph("<b>I. Case Identification</b>", h2_style))
    story.append(Spacer(1, 4))
    story.append(t_case)
    story.append(Spacer(1, 12))

    # Verification Result Banner
    sim_score = verification_record.get("similarity_score", 0.0)
    res_data = [
        [
            Paragraph(f"<b>Verification Status:</b> <font color='{status_text.hexval()}'>{status_str}</font>", h2_style),
            Paragraph(f"<b>Match Score:</b> {sim_score}%", h2_style)
        ]
    ]
    t_res = Table(res_data, colWidths=[350, 170])
    t_res.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), status_bg),
        ('BOX', (0, 0), (-1, -1), 1, status_text),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(Paragraph("<b>II. Verification Finding</b>", h2_style))
    story.append(Spacer(1, 4))
    story.append(t_res)
    story.append(Spacer(1, 10))

    # Submitted Quotation
    sub_quote = verification_record.get("submitted_quote", "")
    story.append(Paragraph("<b>III. Submitted Quotation (AI/Counsel Excerpt)</b>", h2_style))
    story.append(Spacer(1, 4))
    story.append(Paragraph(f'"{sub_quote}"', quote_style))
    story.append(Spacer(1, 8))

    # Original Text Found
    orig_text = verification_record.get("matched_original_text")
    story.append(Paragraph("<b>IV. Original Judgment Excerpt (Verified Record)</b>", h2_style))
    story.append(Spacer(1, 4))
    if orig_text:
        story.append(Paragraph(f'"{orig_text}"', quote_style))
    else:
        story.append(Paragraph("<i>No matching passage found in the judgment document.</i>", body_italic))
    story.append(Spacer(1, 8))

    # Diff / Token Breakdown Table
    diff_data = verification_record.get("diff_data") or {}
    if isinstance(diff_data, str):
        try:
            diff_data = json.loads(diff_data)
        except Exception:
            diff_data = {}

    matches_c = diff_data.get("matches_count", 0)
    mod_c = diff_data.get("modified_count", 0)
    del_c = diff_data.get("deleted_count", 0)
    ins_c = diff_data.get("inserted_count", 0)

    token_data = [
        [
            Paragraph("<b>Identical Words</b>", body_style),
            Paragraph("<b>Substituted Words</b>", body_style),
            Paragraph("<b>Omitted Words</b>", body_style),
            Paragraph("<b>Added Words</b>", body_style)
        ],
        [
            Paragraph(f"<font color='#15803D'><b>{matches_c}</b></font>", body_style),
            Paragraph(f"<font color='#B45309'><b>{mod_c}</b></font>", body_style),
            Paragraph(f"<font color='#DC2626'><b>{del_c}</b></font>", body_style),
            Paragraph(f"<font color='#7C3AED'><b>{ins_c}</b></font>", body_style)
        ]
    ]
    t_token = Table(token_data, colWidths=[130, 130, 130, 130])
    t_token.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#F1F5F9")),
        ('GRID', (0, 0), (-1, -1), 0.5, c_border),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(Paragraph("<b>V. Textual Difference Analysis</b>", h2_style))
    story.append(Spacer(1, 4))
    story.append(t_token)
    story.append(Spacer(1, 14))

    # Legal Disclaimer & Attribution
    disclaimer_text = (
        "<b>LEGAL & COMPLIANCE NOTICE:</b> This verification certificate is generated by the Nyaya Pramaan judicial "
        "verification system. In accordance with judicial protocol, a 'Quote Not Found' status strictly indicates that "
        "the text does not appear in the verified record, and does not establish intentional fabrication. "
        "Source data powered by the AWS Open Data Registry Indian Supreme Court Judgments (CC BY 4.0)."
    )
    story.append(HRFlowable(width="100%", thickness=0.5, color=c_border, spaceAfter=6))
    story.append(Paragraph(disclaimer_text, footer_style))

    # Build document
    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
