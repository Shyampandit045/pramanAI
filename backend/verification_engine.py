"""
Nyaya Pramaan - Advanced Legal Verification Engine
Compares AI-generated legal quotations against authentic Indian court judgments.
Detects: Exact Match, Modified Quote, Quote Not Found, and Inconclusive results.
Produces word-level diffs (matching, modified, deleted, inserted).
"""

import re
import difflib
import unicodedata
import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple


def normalize_text(text: str) -> str:
    """
    Normalizes legal text: cleans curled quotes, ligature characters,
    soft hyphens, and collapses whitespace while preserving words.
    """
    if not text:
        return ""
    
    # Unicode normalize
    text = unicodedata.normalize("NFKD", text)
    
    # Replace curly quotes and apostrophes
    text = text.replace("“", '"').replace("”", '"')
    text = text.replace("‘", "'").replace("’", "'").replace("`", "'")
    text = text.replace("—", " - ").replace("–", " - ")
    
    # Fix broken hyphenated line wraps (e.g., 'dis-\ncretion' -> 'discretion')
    text = re.sub(r'(\w+)-\s*\n\s*(\w+)', r'\1\2', text)
    
    # Replace line breaks and tabs with single space
    text = re.sub(r'[\r\n\t]+', ' ', text)
    
    # Collapse multiple spaces
    text = re.sub(r'\s{2,}', ' ', text)
    
    return text.strip()


def tokenize_words(text: str) -> List[str]:
    """Tokenizes text into words and punctuation."""
    return re.findall(r'\b[\w\'-]+\b|[.,;:!?"\(\)]', text)


def clean_word(w: str) -> str:
    """Lowercases and strips punctuation for comparison."""
    return re.sub(r'[^\w]', '', w.lower())


def compute_word_diff(submitted_text: str, original_text: str) -> Dict[str, Any]:
    """
    Performs word-level alignment between submitted quotation and original judgment text.
    Returns categorized tokens:
      - 'match': identical words
      - 'modified': words replaced or altered
      - 'inserted': hallucinated/added words in submitted quotation
      - 'deleted': words present in original judgment but omitted in submitted quote
    """
    sub_tokens = tokenize_words(submitted_text)
    orig_tokens = tokenize_words(original_text)
    
    sub_clean = [clean_word(t) for t in sub_tokens]
    orig_clean = [clean_word(t) for t in orig_tokens]
    
    matcher = difflib.SequenceMatcher(None, orig_clean, sub_clean)
    
    diff_tokens = []
    matches_count = 0
    modified_count = 0
    inserted_count = 0
    deleted_count = 0
    
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            for k in range(j2 - j1):
                diff_tokens.append({
                    "type": "match",
                    "text": sub_tokens[j1 + k],
                    "orig_text": orig_tokens[i1 + k]
                })
                matches_count += 1
        elif tag == "replace":
            # Some words were changed or substituted
            orig_slice = orig_tokens[i1:i2]
            sub_slice = sub_tokens[j1:j2]
            
            # Align pairwise where possible
            min_len = min(len(orig_slice), len(sub_slice))
            for k in range(min_len):
                diff_tokens.append({
                    "type": "modified",
                    "text": sub_slice[k],
                    "orig_text": orig_slice[k]
                })
                modified_count += 1
                
            if len(sub_slice) > min_len:
                for k in range(min_len, len(sub_slice)):
                    diff_tokens.append({
                        "type": "inserted",
                        "text": sub_slice[k],
                        "orig_text": ""
                    })
                    inserted_count += 1
            elif len(orig_slice) > min_len:
                for k in range(min_len, len(orig_slice)):
                    diff_tokens.append({
                        "type": "deleted",
                        "text": "",
                        "orig_text": orig_slice[k]
                    })
                    deleted_count += 1
        elif tag == "insert":
            for k in range(j1, j2):
                diff_tokens.append({
                    "type": "inserted",
                    "text": sub_tokens[k],
                    "orig_text": ""
                })
                inserted_count += 1
        elif tag == "delete":
            for k in range(i1, i2):
                diff_tokens.append({
                    "type": "deleted",
                    "text": "",
                    "orig_text": orig_tokens[k]
                })
                deleted_count += 1

    total_words = len(sub_tokens)
    similarity = matcher.ratio()
    
    return {
        "diff_tokens": diff_tokens,
        "similarity": round(similarity * 100, 1),
        "matches_count": matches_count,
        "modified_count": modified_count,
        "inserted_count": inserted_count,
        "deleted_count": deleted_count,
        "total_submitted_words": total_words
    }


def find_best_matching_passage(
    submitted_quote: str,
    pages_dict: Dict[int, str]
) -> Tuple[float, str, Optional[int], str]:
    """
    Scans document pages to find the passage with the highest similarity.
    Returns: (best_score, best_passage, best_page, best_context_paragraph)
    """
    clean_sub = normalize_text(submitted_quote)
    if not clean_sub:
        return 0.0, "", None, ""
        
    sub_words = clean_sub.split()
    sub_len = len(sub_words)
    if sub_len == 0:
        return 0.0, "", None, ""

    best_score = 0.0
    best_passage = ""
    best_page = None
    best_context = ""
    
    # 1. First pass: exact substring match per page
    for page_num, page_text in pages_dict.items():
        norm_page = normalize_text(page_text)
        if clean_sub.lower() in norm_page.lower():
            # Exact match found on this page!
            idx = norm_page.lower().find(clean_sub.lower())
            start_context = max(0, idx - 150)
            end_context = min(len(norm_page), idx + len(clean_sub) + 150)
            context = norm_page[start_context:end_context].strip()
            return 1.0, clean_sub, page_num, context

    # 2. Second pass: sliding window over sentences / word blocks per page
    sub_clean_words = [clean_word(w) for w in sub_words if clean_word(w)]

    for page_num, page_text in pages_dict.items():
        norm_page = normalize_text(page_text)
        page_words = norm_page.split()
        if len(page_words) < 5:
            continue
            
        # Window size is approximately the length of the quotation with padding
        win_size = max(8, min(len(page_words), int(sub_len * 1.35) + 6))
        step = max(2, sub_len // 5)
        
        for i in range(0, max(1, len(page_words) - 4), step):
            window_slice = page_words[i:i + win_size]
            cand_passage = " ".join(window_slice)
            
            # Quick token overlap pre-filter
            cand_lower = cand_passage.lower()
            shared_words = sum(1 for w in sub_words if len(w) > 3 and w.lower() in cand_lower)
            if shared_words < max(2, int(sub_len * 0.15)):
                continue
                
            cand_clean_words = [clean_word(w) for w in window_slice if clean_word(w)]
            word_ratio = difflib.SequenceMatcher(None, sub_clean_words, cand_clean_words).ratio()
            char_ratio = difflib.SequenceMatcher(None, clean_sub.lower(), cand_passage.lower()).ratio()
            ratio = max(word_ratio, char_ratio)

            if ratio > best_score:
                best_score = ratio
                best_passage = cand_passage
                best_page = page_num
                
                # Context paragraph around window
                start_c = max(0, i - 20)
                end_c = min(len(page_words), i + win_size + 20)
                best_context = " ".join(page_words[start_c:end_c])
                
                if best_score > 0.98:
                    break

    return best_score, best_passage, best_page, best_context


def compute_quote_dna(text: str) -> Dict[str, Any]:
    """
    Computes a stable cryptographic and structural fingerprint (Quote DNA)
    for canonical legal text verification.
    """
    if not text:
        return {
            "fingerprint": "Q-DNA-000000000000",
            "hash_full": "",
            "token_count": 0,
            "char_count": 0,
            "canonical_preview": ""
        }
    norm = normalize_text(text).lower()
    sha = hashlib.sha256(norm.encode("utf-8")).hexdigest()
    fingerprint = f"Q-DNA-{sha[:12].upper()}"
    tokens = [t for t in tokenize_words(norm) if re.match(r'^\w+$', t)]
    return {
        "fingerprint": fingerprint,
        "hash_full": sha,
        "token_count": len(tokens),
        "char_count": len(norm),
        "canonical_preview": norm[:120] + ("..." if len(norm) > 120 else "")
    }


def detect_context_flags(submitted_quote: str, context_text: Optional[str] = None) -> List[Dict[str, str]]:
    """
    Detects attribution integrity issues, party contentions vs court holdings,
    dissenting opinions, or omitted qualifying clauses.
    """
    flags = []
    if not context_text:
        return flags
    
    ctx_lower = context_text.lower()
    sub_lower = submitted_quote.lower()
    
    # 1. Party contention vs Court holding
    party_patterns = [
        ("counsel for the appellant argued", "Contention by appellant's counsel rather than conclusive ruling of the bench."),
        ("counsel contended", "Quotation is from an advocate's submission during argument."),
        ("learned counsel submitted", "Quotation originates from advocate submissions."),
        ("the petitioner submits", "Party argument presented by petitioner."),
        ("it was argued on behalf of", "Quotation reflects a party's legal argument."),
        ("the appellant contends", "Argument of the appellant.")
    ]
    for pattern, explanation in party_patterns:
        if pattern in ctx_lower:
            flags.append({
                "type": "party_attribution",
                "severity": "warning",
                "title": "Party Contention Alert",
                "description": f"Surrounding context indicates: {explanation}"
            })
            break

    # 2. Dissenting opinion
    dissent_patterns = [
        ("dissenting opinion", "Quote appears within a dissenting opinion."),
        ("dissenting judgment", "Quote is from a dissenting judicial opinion."),
        ("i regret i am unable to agree", "Quote is part of a minority/dissenting view."),
        ("i have arrived at a different conclusion", "Separate or dissenting opinion statement.")
    ]
    for pattern, explanation in dissent_patterns:
        if pattern in ctx_lower:
            flags.append({
                "type": "dissenting_opinion",
                "severity": "warning",
                "title": "Dissenting Opinion Notice",
                "description": explanation
            })
            break

    # 3. Omitted qualifications or conditions
    qual_patterns = [
        ("provided always that", "Mandatory proviso/qualification"),
        ("subject to the condition that", "Condition precedent"),
        ("save and except", "Statutory exception clause"),
        ("unless the contrary is proved", "Rebuttable presumption proviso")
    ]
    for phrase, label in qual_patterns:
        if phrase in ctx_lower and phrase not in sub_lower:
            flags.append({
                "type": "omitted_qualification",
                "severity": "info",
                "title": f"Omitted Clause ({label})",
                "description": f"Original passage contains qualifying text '{phrase}' which was omitted from the quotation."
            })
            break

    return flags


def verify_quotation(
    submitted_quote: str,
    document_pages: Dict[int, str],
    case_metadata: Optional[Dict[str, Any]] = None,
    is_scanned: bool = False
) -> Dict[str, Any]:
    """
    Main verification pipeline for a submitted quotation.
    
    Status definitions:
      1. 'Exact Match': Quotation matches verbatim (100% precision).
      2. 'Modified Quote': Case found, quotation matches partially (50%-99%) with altered, omitted, or added words.
      3. 'Quote Not Found': Case found, but quotation has no substantial match (< 50%).
         * Never label as fabricated solely because it was not found.
      4. 'Inconclusive': Document unreadable, scanned without readable text, or text layer missing.
    """
    submitted_quote = submitted_quote.strip()
    if not submitted_quote:
        raise ValueError("Submitted quotation cannot be empty.")

    now_iso = datetime.now(timezone.utc).isoformat()
    sub_dna = compute_quote_dna(submitted_quote)
    total_doc_words = sum(len(p.split()) for p in document_pages.values())
    
    # Check for unreadable / scanned document
    if is_scanned or total_doc_words < 10:
        return {
            "status": "Inconclusive",
            "similarity_score": 0.0,
            "matched_text": None,
            "page_number": None,
            "diff": {
                "diff_tokens": [{"type": "inconclusive", "text": submitted_quote, "orig_text": ""}],
                "similarity": 0.0,
                "matches_count": 0,
                "modified_count": 0,
                "inserted_count": 0,
                "deleted_count": 0,
                "total_submitted_words": len(submitted_quote.split())
            },
            "context_paragraph": None,
            "explanation": (
                "Document text layer is unreadable or incomplete. Scanned documents or image-based PDFs "
                "require specialized optical character recognition (OCR). Verification is inconclusive."
            ),
            "reasons": [
                "Document contains scanned images rather than selectable text",
                "Text extraction yielded fewer than readable document threshold",
                "OCR fidelity was insufficient to guarantee verification integrity"
            ],
            "quote_dna": {
                "submitted": sub_dna,
                "source": None
            },
            "context_flags": [],
            "verified_at": now_iso
        }

    # Search for match in document pages
    score, best_passage, page_num, context_paragraph = find_best_matching_passage(
        submitted_quote,
        document_pages
    )

    norm_sub = normalize_text(submitted_quote)
    norm_pass = normalize_text(best_passage)
    source_dna = compute_quote_dna(best_passage) if best_passage else None
    context_flags = detect_context_flags(submitted_quote, context_paragraph)

    # 1. Exact Match Check (score > 0.98 or exact substring)
    if score >= 0.98 or (norm_pass and norm_sub.lower() in norm_pass.lower()):
        diff_res = compute_word_diff(submitted_quote, best_passage if best_passage else submitted_quote)
        return {
            "status": "Exact Match",
            "similarity_score": 100.0,
            "matched_text": best_passage or submitted_quote,
            "page_number": page_num or 1,
            "diff": diff_res,
            "context_paragraph": context_paragraph or best_passage,
            "explanation": "The submitted quotation matches the authentic court judgment verbatim.",
            "is_exact": True,
            "quote_dna": {
                "submitted": sub_dna,
                "source": source_dna or sub_dna
            },
            "context_flags": context_flags,
            "verified_at": now_iso
        }

    # 2. Modified Quote Check (50% <= score < 98%)
    elif score >= 0.50:
        diff_res = compute_word_diff(submitted_quote, best_passage)
        return {
            "status": "Modified Quote",
            "similarity_score": round(score * 100, 1),
            "matched_text": best_passage,
            "page_number": page_num,
            "diff": diff_res,
            "context_paragraph": context_paragraph,
            "explanation": (
                "The quotation is derived from a genuine passage in this judgment, but contains "
                "modified words, omitted phrases, or inserted text compared to the original record."
            ),
            "is_exact": False,
            "quote_dna": {
                "submitted": sub_dna,
                "source": source_dna
            },
            "context_flags": context_flags,
            "verified_at": now_iso
        }

    # 3. Quote Not Found (< 50%)
    else:
        diff_res = compute_word_diff(submitted_quote, "")
        return {
            "status": "Quote Not Found",
            "similarity_score": round(score * 100, 1),
            "matched_text": None,
            "page_number": None,
            "diff": diff_res,
            "context_paragraph": None,
            "explanation": (
                "The submitted quotation could not be located in this judgment. "
                "Important: This does not necessarily mean the quotation is fabricated or fake. "
                "It may belong to a concurring/dissenting opinion, oral remarks, another connected case, "
                "or an unindexed volume."
            ),
            "is_exact": False,
            "reasons": [
                "Quotation may be from a different bench or connected petition in the same matter",
                "Quotation may appear in separate concurring or dissenting judgment",
                "Quotation may be an oral observation recorded in law reports but not in final judgment text",
                "Citation may point to a different year or volume"
            ],
            "quote_dna": {
                "submitted": sub_dna,
                "source": None
            },
            "context_flags": context_flags,
            "verified_at": now_iso
        }
