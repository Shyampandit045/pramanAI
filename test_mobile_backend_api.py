"""
Test script to verify the new endpoints created for the Praman AI Mobile App:
- /api/health
- /api/verify (with Quote DNA and Context Flags)
- /api/verify/batch
- /api/verify/trace
- /api/benchmarks
"""

import json
from backend.main import (
    health_check,
    verify_quote_endpoint,
    VerifyQuoteRequest,
    verify_batch_endpoint,
    BatchVerifyRequest,
    BatchVerifyItem,
    trace_quote_endpoint,
    TraceQuoteRequest,
    get_benchmarks,
    get_system_stats
)
from backend.auth import DEMO_USER_ID

def main():
    print("Testing /api/health...")
    h = health_check()
    assert h["status"] == "online"
    print(f"Health check OK: {h}")

    demo_user = {
        "id": DEMO_USER_ID,
        "email": "demo@nyayapramaan.gov.in",
        "full_name": "Adv. Priya Sharma",
        "role": "Legal Advocate"
    }

    print("\nTesting /api/verify with Quote DNA...")
    exact_quote = (
        "freedom of speech and of the press lay at the foundation of all democratic organisations, "
        "for without free political discussion no public education, so essential for the proper functioning "
        "of the processes of popular government, is possible."
    )
    req = VerifyQuoteRequest(judgment_id="sc-1950-594", submitted_quote=exact_quote)
    v_res = verify_quote_endpoint(req, current_user=demo_user)
    assert v_res["status"] == "Exact Match"
    assert "quote_dna" in v_res
    assert v_res["quote_dna"]["submitted"]["fingerprint"].startswith("Q-DNA-")
    print(f"Quote DNA generated: {v_res['quote_dna']['submitted']['fingerprint']}")
    print(f"Verified At: {v_res.get('verified_at')}")

    print("\nTesting /api/verify/batch...")
    batch_req = BatchVerifyRequest(
        items=[
            BatchVerifyItem(
                id="q1",
                quote=exact_quote,
                judgment_id="sc-1950-594"
            ),
            BatchVerifyItem(
                id="q2",
                quote="Generally speaking, this Supreme Court will never grant special leave, unless it is proven that exceptional and critical circumstances exist.",
                judgment_id="sc-1950-459"
            )
        ]
    )
    b_res = verify_batch_endpoint(batch_req, current_user=demo_user)
    assert b_res["total_quotes"] == 2
    assert b_res["status_distribution"]["Exact Match"] == 1
    assert b_res["status_distribution"]["Modified Quote"] == 1
    print(f"Batch audit OK: {b_res['total_quotes']} items, distribution: {b_res['status_distribution']}")

    print("\nTesting /api/verify/trace...")
    trace_req = TraceQuoteRequest(quote="freedom of speech and of the press", min_similarity=0.35)
    t_res = trace_quote_endpoint(trace_req)
    assert t_res["total_matches_found"] > 0
    print(f"Quote trace OK: found {t_res['total_matches_found']} matches across corpus")
    print(f"Top match: {t_res['matches'][0]['case_title']} (score: {t_res['matches'][0]['similarity_score']}%)")

    print("\nTesting /api/benchmarks...")
    bench = get_benchmarks()
    assert bench["evaluation_metrics"]["precision"] == 100.0
    assert len(bench["test_results"]) == 8
    print(f"Benchmarks OK: precision {bench['evaluation_metrics']['precision']}%, {len(bench['test_results'])} tests verified")

    print("\nALL MOBILE BACKEND ENDPOINTS TESTED SUCCESSFULLY!")

if __name__ == "__main__":
    main()

