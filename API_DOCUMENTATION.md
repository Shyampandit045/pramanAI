# Praman AI — API Integration Documentation

The Praman AI Mobile App integrates directly with the existing Python FastAPI backend server. The backend serves both the web client and mobile clients without duplication or conflicting logic.

---

## Central Configuration

- **Environment Variable**: `EXPO_PUBLIC_API_BASE_URL`
- **Default Fallback**: `http://10.196.62.140:8000` (or local machine Wi-Fi address)
- **Runtime Override**: The mobile app allows users to change and test the backend URL directly in the **Methodology & Settings** screen, persisting it in `AsyncStorage`.

---

## Core Endpoints

### 1. Health & Readiness
`GET /api/health`
- **Response**:
```json
{
  "status": "online",
  "service": "Praman AI / Nyaya Pramaan API",
  "version": "1.0.0",
  "timestamp": "2026-10-29T06:13:29Z",
  "corpus_ready": true
}
```

### 2. Single Quote Verification
`POST /api/verify`
- **Request Body**:
```json
{
  "judgment_id": "sc-1950-594",
  "submitted_quote": "freedom of speech and of the press lay at the foundation..."
}
```
- **Response**:
```json
{
  "verification_id": "NP-VER-48A9BD5FD4",
  "status": "Exact Match",
  "similarity_score": 100.0,
  "matched_text": "freedom of speech and of the press lay at the foundation...",
  "page_number": 9,
  "diff": {
    "diff_tokens": [
      { "type": "match", "text": "freedom", "orig_text": "freedom" }
    ],
    "similarity": 100.0,
    "matches_count": 41,
    "modified_count": 0,
    "inserted_count": 0,
    "deleted_count": 0,
    "total_submitted_words": 41
  },
  "quote_dna": {
    "submitted": {
      "fingerprint": "Q-DNA-B84CD624BEB1",
      "hash_full": "b84cd624beb16215858cfd7be8f533a0889218d6a782a472c2fc08f95c52c6f6",
      "token_count": 41,
      "char_count": 220
    },
    "source": {
      "fingerprint": "Q-DNA-B84CD624BEB1",
      "hash_full": "b84cd624beb16215858cfd7be8f533a0889218d6a782a472c2fc08f95c52c6f6",
      "token_count": 41,
      "char_count": 220
    }
  },
  "context_flags": [],
  "explanation": "The submitted quotation matches the authentic court judgment verbatim.",
  "case_details": {
    "id": "sc-1950-594",
    "title": "ROMESH THAPPAR versus THE STATE OF MADRAS",
    "citation": "1950 SCR 594",
    "court": "Supreme Court of India",
    "source_url": "https://indian-supreme-court-judgments.s3.amazonaws.com/..."
  }
}
```

### 3. Direct PDF Upload Verification
`POST /api/verify/upload-pdf`
- **Content-Type**: `multipart/form-data`
- **Form Fields**:
  - `file`: PDF binary
  - `submitted_quote`: string
  - `case_title`: string (optional)
  - `citation`: string (optional)

### 4. Batch Legal Audit
`POST /api/verify/batch`
- **Request Body**:
```json
{
  "document_text": "Full legal brief containing multiple quotations in quotes...",
  "default_judgment_id": "sc-1950-594"
}
```
*Or passing structured items:*
```json
{
  "items": [
    { "quote": "quote 1", "judgment_id": "sc-1950-594" },
    { "quote": "quote 2", "judgment_id": "sc-1950-459" }
  ]
}
```
- **Response**:
```json
{
  "batch_id": "NP-BATCH-A1B2C3D4",
  "total_quotes": 2,
  "status_distribution": {
    "Exact Match": 1,
    "Modified Quote": 1,
    "Quote Not Found": 0,
    "Inconclusive": 0
  },
  "average_similarity": 80.5,
  "results": [ ... ]
}
```

### 5. Cross-Case Quote Tracing
`POST /api/verify/trace`
- **Request Body**:
```json
{
  "quote": "freedom of speech and of the press",
  "min_similarity": 0.40,
  "limit": 10
}
```

### 6. Reproducible Benchmarks
`GET /api/benchmarks`
- **Response**:
Returns empirical metrics (`precision`, `recall`, `false_positive_rate`, `test_suite_pass_rate`), dataset boundaries, and itemized test case measurements.

### 7. Official PDF & JSON Report Export
- `GET /api/verifications/{verification_id}/report.pdf` — Generates and downloads official ReportLab PDF verification certificate.
- `GET /api/verifications/{verification_id}/report.json` — Downloads structured JSON evidence certificate.

### 8. Cases & Corpus Search
- `GET /api/cases?q={query}&year={year}&court={court}&limit={limit}`
- `GET /api/cases/{judgment_id}`
- `GET /api/cases/presets/samples` — Returns 1-click test scenarios for instant evaluation.

