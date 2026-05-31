# Admin Copilot — Workflow Documentation

---

## Overview

```
Admin Copilot
      │
      ├── Circular Summarization   PDF → AI → Structured Summary
      ├── Letter Generator         Form → AI → Official Letter
      ├── Report Generator         DB Data → AI → Analytics Report
      └── Translation              Text → AI → Bilingual Output
```

All features share the same AI pipeline: **Input → Gemini 1.5 Flash → Output → PostgreSQL → Export**

---

## 1. Circular Summarization Workflow

**Actors:** HM, MEO, DEO

### Sequence Diagram:

```
User (Mobile App)      FastAPI Backend           Gemini AI            PostgreSQL
        │                      │                       │                    │
        │── Upload PDF ────────►│                       │                    │
        │                      │─── Extract text ───►  │                    │
        │                      │    (PyMuPDF)           │                    │
        │                      │                       │                    │
        │                      │── Send prompt ────────►│                    │
        │                      │   (+ circular text)    │                    │
        │                      │                       │                    │
        │                      │◄── structured JSON ───│                    │
        │                      │   (summary, actions,  │                    │
        │                      │    deadlines, etc.)   │                    │
        │                      │                       │                    │
        │                      │── Save to DB ─────────────────────────────►│
        │                      │                       │                    │
        │◄── Summary Response ─│                       │                    │
        │                      │                       │                    │
        │── Request PDF ───────►│                       │                    │
        │                      │── Generate PDF ──────►│                    │
        │                      │   (ReportLab)         │                    │
        │◄── PDF Download ─────│                       │                    │
```

### Activity Flow:

```
[User taps Circular Summarizer]
         │
[Opens CircularSummarizerScreen]
         │
[Taps Upload Zone]
         │
[DocumentPicker opens — select PDF]
         │
[Taps "Summarize Circular"]
         │
[POST /copilot/summarize-circular (multipart)]
         │
[Backend: PyMuPDF extracts text from PDF]
         │
         ├── No text found? → 422 Error: "Scanned image PDF"
         │
[Trim text to 12,000 chars to fit token window]
         │
[Build CIRCULAR_SUMMARY_PROMPT with text]
         │
[Call Gemini 1.5 Flash → generate_json()]
         │
[Parse JSON response: validate CircularSummaryJSON schema]
         │
[Save record to circular_summaries table]
         │
[Return CircularSummaryResponse to mobile]
         │
[Display 6 structured section cards]
         │
[User taps "Download PDF"]
         │
[GET /copilot/circulars/{id}/export/pdf]
         │
[ReportLab generates formatted A4 PDF]
         │
[StreamingResponse → mobile downloads file]
```

### Error Handling:
```
PDF too large (>20MB)          → 413: "PDF exceeds 20 MB limit"
Non-PDF file                   → 400: "Only PDF files are supported"
Scanned/image PDF              → 422: "No readable text detected"
Gemini returns malformed JSON  → Graceful fallback with partial data
Gemini quota exceeded          → 429: "AI service temporarily unavailable"
```

---

## 2. Official Letter Generator Workflow

**Actors:** HM, MEO, DEO

### Sequence Diagram:

```
User (Mobile)          FastAPI            Gemini AI         PostgreSQL
      │                   │                   │                  │
      │── GET /templates ─►│                  │                  │
      │◄── Template List ──│                  │                  │
      │                   │                   │                  │
      │── Select Template ─►│                 │                  │
      │   + Fill Form     │                   │                  │
      │                   │                   │                  │
      │── POST /generate-letter ──────────────►│                 │
      │                   │── Build prompt ──►│                  │
      │                   │   (template +     │                  │
      │                   │    form fields)   │                  │
      │                   │◄── Letter text ───│                  │
      │                   │   (plain text,    │                  │
      │                   │    govt format)   │                  │
      │                   │── Generate ref# ──►                  │
      │                   │   (EDU/LA/2025/XYZ) ←               │
      │                   │── Save to DB ───────────────────────►│
      │◄── LetterResponse ─│                  │                  │
      │                   │                   │                  │
      │── POST /export/pdf ►│                 │                  │
      │                   │── ReportLab ──────►                  │
      │◄── PDF bytes ──────│                  │                  │
      │                   │                   │                  │
      │── POST /export/docx ►│                │                  │
      │                   │── python-docx ────►                  │
      │◄── DOCX bytes ─────│                  │                  │
```

### Form Validation Flow:
```
User selects template
         │
[Load dynamic fields from LETTER_TEMPLATES dict]
         │
User fills required fields
         │
[Client-side: all required fields non-empty?]
         │
         ├── No → Show field-level error highlights
         │
         └── Yes → Enable "Generate Letter" button
                        │
               [POST /generate-letter]
                        │
               [Gemini drafts letter]
                        │
               [Auto-generate Ref No: EDU/LA/YYYY/NNNNN]
                        │
               [Preview screen: letter text + export options]
```

### Reference Number Format:
```
EDU / {TYPE_CODE} / {YEAR} / {5-char-unique-id}

Examples:
  EDU/LA/2025/ABC12   ← Leave Approval
  EDU/TT/2025/XYZ99   ← Teacher Transfer
  EDU/IR/2025/PQR77   ← Infrastructure Request
```

---

## 3. Automated Report Generator Workflow

**Actors:** HM, MEO, DEO

### Sequence Diagram:

```
User (Mobile)       FastAPI         PostgreSQL        Gemini AI
      │                │                │                  │
      │── Select report type + scope ──►│                  │
      │                │                │                  │
      │                │── Fetch data ─►│                  │
      │                │   (schools,    │                  │
      │                │    students,   │                  │
      │                │    attendance, │                  │
      │                │    teachers)   │                  │
      │                │◄── Aggregated ─│                  │
      │                │    statistics  │                  │
      │                │                │                  │
      │                │── Build REPORT_GENERATION_PROMPT ─►│
      │                │   (type + data + sections)        │
      │                │◄── JSON report ────────────────────│
      │                │   (summary, KPIs, risks,          │
      │                │    recommendations, actions)      │
      │                │                │                  │
      │                │── Save report to generated_reports─►│
      │                │                │                  │
      │◄── ReportResponse ──────────────│                  │
      │   (content_json + plain_text)   │                  │
```

### Data Fetching by Report Type:
```
school_performance:
  → SELECT students WHERE school_id = ? AND is_active = true
  → SELECT avg(percentage) FROM assessment_results
  → COUNT students by risk_level
  → Compute: high_risk_ratio, average_dropout_risk, average_assessment_pct

attendance:
  → SELECT count, SUM(present) FROM attendance WHERE date >= 30 days ago
  → Compute: attendance_rate, absent_count, present_count

teacher_performance:
  → SELECT teachers WHERE school_id = ?
  → Aggregate: avg_attendance_pct, avg_performance_score, count by type
  → Flag: teachers below 80% attendance

school_health:
  → SELECT schools WHERE scope criteria
  → health_score, infrastructure flags
  → Compute: grade distribution (A/B/C/D), schools_needing_attention
```

### Report Sections Structure:
```json
{
  "executive_summary": "3-4 sentence overview of school/district status",
  "kpi_analysis":      "Specific numbers: attendance %, dropout count, scores",
  "trends":            "Month-over-month / quarter-over-quarter observations",
  "risks":             "Identified problem areas requiring attention",
  "recommendations":   ["Action 1", "Action 2", ...],
  "action_plan":       ["Week 1: Do X", "Week 2: Do Y", ...]
}
```

---

## 4. Translation Workflow

**Actors:** All authenticated users

### Sequence Diagram:

```
User (Mobile)       FastAPI         Gemini AI        PostgreSQL
      │                │                 │                 │
      │── Select source/target lang ─────►               │
      │── Type/paste text ───────────────►               │
      │── Tap Translate ─────────────────►               │
      │                │                 │                 │
      │                │── POST /translate                 │
      │                │── Validate: ──────►               │
      │                │   - Langs supported?             │
      │                │   - Langs different?             │
      │                │   - Text ≤ 10,000 chars?         │
      │                │                 │                 │
      │                │── Build TRANSLATION_PROMPT ──────►│
      │                │   (source, target, text)          │
      │                │◄── Translated text ───────────────│
      │                │                 │                 │
      │                │── Save to translations table ─────►│
      │                │                 │                 │
      │◄── TranslateResponse ─────────────                │
      │   (id, translated_text, word_count)               │
      │                │                 │                 │
      │── Tap Copy ─────────────────────►                 │
      │   (copy to clipboard)            │                 │
```

### Language Direction Rules:
```
Telugu → English: ✅ Allowed
English → Telugu: ✅ Allowed
Telugu → Telugu:  ❌ Error: "Source and target must differ"
English → English:❌ Error: "Source and target must differ"
```

### Character Limit Behavior:
```
0–8,999 chars:   Normal (counter shows neutral color)
9,000–9,999 chars: Warning (counter turns orange)
10,000 chars:    Limit reached (counter turns red, input stops)
>10,000 chars:   Backend returns 400 error
```

---

## AI Prompt Engineering

### Circular Summary Prompt:
```
System: Expert government education administrator in Andhra Pradesh
Task: Analyse circular text, extract structured information
Output: JSON with keys: summary, key_instructions, action_items,
        deadlines, responsible_officers, compliance_requirements
Constraint: Return ONLY valid JSON, no markdown
```

### Letter Generation Prompt:
```
System: Expert in official government letter drafting
Task: Generate formal letter from template + form data
Output: Plain text letter (ref number, date, to/from, subject, body, signature)
Constraints:
  - Use official GoAP letter format
  - Formal, respectful government language
  - Support English or Telugu output
```

### Report Generation Prompt:
```
System: Senior education data analyst for Government of Andhra Pradesh
Task: Analyse school data, generate professional report
Output: JSON with keys: executive_summary, kpi_analysis, trends,
        risks, recommendations, action_plan
Constraint: Be specific with numbers, use professional language
```

### Translation Prompt:
```
System: Expert translator, government education documents
Task: Translate text from {source} to {target}
Output: ONLY the translated text (no explanations)
Constraint: Maintain formal government tone, preserve proper nouns
```

---

## State Diagram: Copilot Document Lifecycle

```
                ┌─────────────┐
                │   PENDING   │ ← User uploads/submits
                └──────┬──────┘
                       │
                       ▼
                ┌─────────────┐
                │ PROCESSING  │ ← Gemini AI generating
                └──────┬──────┘
                       │
           ┌───────────┴───────────┐
           │                       │
           ▼                       ▼
    ┌─────────────┐         ┌─────────────┐
    │  COMPLETED  │         │   FAILED    │
    │  (stored)   │         │  (retried)  │
    └──────┬──────┘         └─────────────┘
           │
     ┌─────┴──────┐
     │            │
     ▼            ▼
┌─────────┐  ┌─────────┐
│EXPORTED │  │ VIEWED  │
│(PDF/DOCX│  │(in-app) │
└─────────┘  └─────────┘
```

---

## Security & Rate Limiting

| Concern | Mitigation |
|---|---|
| JWT Authentication | All copilot endpoints require valid Bearer token |
| Role Enforcement | `require_hm` dependency — blocks STUDENT/PARENT |
| File Size Limit | PDF uploads capped at 20 MB |
| Text Length Limit | Translation capped at 10,000 characters |
| PDF Sanitization | PyMuPDF only reads text — no code execution |
| Gemini API Key | Stored in `.env`, never exposed in responses |
| Output Sanitization | Gemini output stored as text, not executed |
| Rate Limiting | Nginx rate limiting — 30 req/min per IP |

---

## Performance Benchmarks (Estimates)

| Operation | Typical Latency | Notes |
|---|---|---|
| PDF Text Extraction | 0.5–2s | Depends on PDF size (pages) |
| Circular Summarization | 4–8s | Gemini 1.5 Flash |
| Letter Generation | 3–6s | Single Gemini call |
| Report Generation | 5–15s | DB fetch + Gemini |
| Translation (100 words) | 2–4s | Gemini |
| Translation (1000 words) | 4–8s | Larger context |
| PDF Export (Letter) | 0.2–0.5s | ReportLab in-memory |
| DOCX Export (Report) | 0.3–0.8s | python-docx in-memory |
