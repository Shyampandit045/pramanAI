# Praman AI (न्याय प्रमाण) — Mobile & Web Platform

**Intelligent Legal Quote Verification & Evidence Platform**  
*Cross-referencing legal quotations against authentic Indian Supreme Court judgments (1950–Present).*

---

## 🏛️ Overview

Generative AI platforms frequently hallucinate, subtly alter, or misattribute legal quotations when drafting appellate briefs, judicial orders, and research memos. **Praman AI** is a professional evidence-based legal verification platform. 

It preserves the **Judicial Evidence Standard**:
> **Praman AI proves what is present in official judgments, not merely what an AI model generates.** A quotation is never labeled "fabricated" or "fake" solely because it was not located in a single record.

The mobile application is a high-performance **React Native (Expo SDK 58 + TypeScript)** client that seamlessly connects to the existing Python FastAPI judicial verification engine.

---

## 📱 Mobile Architecture & Screens

The mobile client is located in [`mobile/`](./mobile) and implements all 8 core platform screens:

1. **Dashboard / Welcome (`HomeScreen.tsx`)**:
   - Hero banner with judicial branding (navy `#0F172A`, gold `#D97706`, royal purple `#7C3AED`).
   - Quick verification shortcut & Batch Audit launcher.
   - Live system metrics (Judgments Indexed, Total Verifications, Exact Matches, Modified Quotes).
   - **⚡ 1-Click Evaluation Presets**: Instant testing for *Romesh Thappar (1950)* (Exact Match), *Bharat Bank (1950)* (Modified Quote), *Kesavananda Bharati (1973)* (Not Found), and Archival Scanned PDFs (Inconclusive).
   - Recent verification summary.

2. **Verify Quote (`VerifyScreen.tsx`)**:
   - Full legal quotation input with word & character counters.
   - Dual-mode support: **Indexed Judgment Corpus** or **Direct PDF Upload**.
   - Searchable Supreme Court corpus selector.
   - Optional judgment citation, court, and URL fields.
   - Integrated **Cross-Case Tracing** tool to locate matching judicial doctrines across all cases.

3. **Verification Results (`VerificationResultScreen.tsx`)**:
   - Status badge (**Exact Match**, **Modified Quote**, **Context Mismatch**, **Source Not Found**, **Inconclusive**).
   - Clear plain-language explanation and judicial non-fabrication advisories.
   - **Proof-Carrying Evidence**: Judgment title, court jurisdiction, citation, page number, and source URL link.
   - **Word-Level Diff Analysis**:
     - *Visual Flow*: Interactive chips (green for verbatim, amber for modified/substituted words, red for added/hallucinated text, strikethrough for omitted text).
     - *Side-by-Side Comparison*: Submitted quote vs. authentic court record.
   - **🧬 Quote DNA**: Stable cryptographic SHA-256 canonical hash, token count, character length, and source DNA variance indicator.
   - **⚖️ Context & Attribution Integrity**: Automatically flags counsel arguments vs. bench holdings, dissenting opinions, and omitted qualifying clauses.
   - **Official ReportLab PDF & JSON Export**: 1-tap download and native mobile sharing via `expo-sharing`.

4. **Batch Legal Audit (`BatchAuditScreen.tsx`)**:
   - Audit legal briefs, appellate petitions, or multi-quote memos.
   - Automated quote extraction using quotation pattern recognition.
   - 1-Click "Load Sample Brief with 3 AI Quotes" for instant evaluation.
   - Status distribution filter chips and itemized results.

5. **Audit History (`HistoryScreen.tsx`)**:
   - Full history of previous checks stored in backend database.
   - Real-time search across case title, quotation, and citation.
   - Status filtering pills.
   - 1-tap view evidence details and record deletion.

6. **Landmark Judgment Corpus (`CorpusScreen.tsx`)**:
   - Searchable repository of authentic Indian Supreme Court judgments (AWS Open Data Registry, CC BY 4.0).
   - Filter by historic years (1950, 1962, 1973, 2024, etc.).
   - 1-tap "Verify Quote Here" shortcut.

7. **Benchmark & Evaluation (`BenchmarkScreen.tsx`)**:
   - Real, reproducible benchmarks derived from the verified test harness:
     - **Precision**: 100.0%
     - **Recall**: 100.0%
     - **False-Positive Rate**: 0.0%
     - **Test Pass Rate**: 100% across all 8 core specification test cases.
   - Transparent dataset limitations disclosure.

8. **Methodology & Settings (`MethodologyScreen.tsx`)**:
   - Detailed guide explaining how quote verification works and what each status means.
   - The Judicial Non-Fabrication Rule.
   - **Live Backend Connection Diagnostic & Server URL Config**: Test connection and change API base URL dynamically for Wi-Fi/emulator testing.
   - Privacy architecture notice.

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- **Python**: 3.10+ (tested with Python 3.14)
- **Node.js**: v18+ (tested with Node v24.11)
- **Expo CLI**: bundled with `npx expo`

### 2. Start the Backend Server
From the project root:
```bash
# Starts the FastAPI backend with database initialization and seeding
python run.py --host 0.0.0.0 --port 8000
```
- API Base URL: `http://localhost:8000`
- Interactive Swagger Docs: `http://localhost:8000/docs`
- Web Application: `http://localhost:8000/`

### 3. Configure Mobile App Environment
In [`mobile/.env`](./mobile/.env):
```ini
# For Android Emulator:
# EXPO_PUBLIC_API_BASE_URL=http://10.0.2.2:8000

# For Physical Phone on same Wi-Fi (replace with your computer's local IP):
EXPO_PUBLIC_API_BASE_URL=http://10.196.62.140:8000

# For Web / Local:
# EXPO_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
```
*(Note: You can also adjust or test the server URL directly inside the mobile app on the "Guide & Settings" tab!)*

### 4. Run the Mobile App
From the project root:
```bash
# Start the Expo development server
npm run start:mobile
```
Inside the `mobile/` directory:
- Press `a` to launch on Android Emulator or connected USB device.
- Press `w` to open in Web browser.
- Scan the QR code using the **Expo Go** app on your physical iOS or Android phone.

---

## 🧪 Testing

Run the comprehensive test suite verifying the Python backend, new mobile API endpoints, and React Native mobile workflows:

```bash
# Run all tests (Backend + Mobile API + Jest)
npm test

# Run individual test suites
npm run test:backend       # Python Section 9 specification tests (8/8 pass)
npm run test:mobile-api    # Python mobile API endpoint tests (Health, Batch, Trace, DNA, Benchmarks)
npm run test:mobile        # Jest React Native unit & workflow tests (10/10 pass)
```

---

## 📦 Building for Android

### Local Android Build (Requires Android SDK & JDK)
Inside the `mobile/` directory:
```bash
npx expo run:android
```

### Production APK / AAB via EAS Build
```bash
# Install EAS CLI
npm install -g eas-cli

# Login to Expo account
eas login

# Build standalone Android APK
eas build -p android --profile preview
```

---

## ⚖️ License & Attribution
- **Dataset**: Indian Supreme Court Judgments (1950–Present), AWS Open Data Registry, licensed under **Creative Commons Attribution 4.0 International (CC BY 4.0)**.
- **Platform**: Praman AI Legal Technology Platform.

