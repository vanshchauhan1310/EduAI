# Admin Copilot — Complete API Documentation

**Base URL:** `http://localhost:8000/api/v1/copilot`
**Auth:** Bearer JWT token required on all endpoints
**Access Roles:** HM, MEO, DEO (Translation also available to TEACHER, STUDENT, PARENT)
**AI Provider:** NVIDIA NIM (`NVIDIA_NIM_MODEL`)

---

## Feature Overview

| Feature | Endpoint Prefix | Purpose |
|---|---|---|
| Circular Summarization | `/copilot/summarize-circular` | PDF → structured JSON summary |
| Letter Generator | `/copilot/generate-letter` | Form fields → official letter |
| Report Generator | `/copilot/generate-report` | Live DB data → AI report |
| Translation | `/copilot/translate` | Telugu ↔ English |

---

## 1. Circular Summarization

### POST `/copilot/summarize-circular`
Upload a PDF government circular and get an AI-generated structured summary.

**Access:** HM, MEO, DEO  
**Content-Type:** `multipart/form-data`

**Form Fields:**
| Field | Type | Required | Description |
|---|---|---|---|
| `file` | File (PDF) | Yes | Government circular PDF (max 20 MB) |

**Response 201:**
```json
{
  "id": 1,
  "file_name": "circular_2025_education.pdf",
  "summary_json": {
    "summary": "This circular mandates all government schools to submit attendance data digitally by June 30, 2025...",
    "key_instructions": [
      "All HMs must upload monthly attendance by the 5th of every month",
      "Use only the official EduAI portal for data submission"
    ],
    "action_items": [
      "HM to register on EduAI portal by June 15",
      "Designate a data entry operator per school"
    ],
    "deadlines": [
      "Portal registration: June 15, 2025",
      "First data upload: June 30, 2025"
    ],
    "responsible_officers": [
      "Headmaster (school level)",
      "MEO (mandal verification)",
      "DEO (district approval)"
    ],
    "compliance_requirements": [
      "Monthly attendance report must achieve 95% completeness",
      "Non-compliance will attract withholding of school grants"
    ]
  },
  "created_at": "2025-05-30T09:15:00+05:30"
}
```

**Error Responses:**
| Code | Message |
|---|---|
| 400 | Only PDF files are supported |
| 413 | PDF exceeds 20 MB limit |
| 422 | PDF appears to have no readable text (scanned image) |
| 401 | Authentication required |
| 403 | Insufficient role |

---

### GET `/copilot/circulars/history`
Get the list of previously summarized circulars.

**Query Params:** `limit` (default: 20, max: 100)

**Response 200:**
```json
[
  {
    "id": 1,
    "file_name": "circular_2025_education.pdf",
    "summary_preview": "This circular mandates all government schools to submit attendance data...",
    "created_at": "2025-05-30T09:15:00+05:30"
  }
]
```

---

### GET `/copilot/circulars/{summary_id}`
Fetch a previously generated summary by ID.

**Response 200:** Full `CircularSummaryResponse` object (same as POST response)

---

### GET `/copilot/circulars/{summary_id}/export/pdf`
Download the circular summary as a formatted government-style PDF.

**Response:** `application/pdf` file stream  
**Content-Disposition:** `attachment; filename=circular_summary_{id}.pdf`

---

## 2. Official Letter Generator

### GET `/copilot/letters/templates`
List all available letter templates.

**Access:** HM, MEO, DEO

**Response 200:**
```json
[
  {
    "key": "leave_approval",
    "name": "Leave Approval Letter",
    "description": "Approve or acknowledge a teacher's leave request",
    "fields": [
      { "key": "teacher_name",  "label": "Teacher Name",     "type": "text",   "required": true },
      { "key": "leave_type",    "label": "Leave Type",       "type": "select", "options": ["Casual Leave","Medical Leave","Earned Leave","Maternity Leave"], "required": true },
      { "key": "leave_days",    "label": "Number of Days",   "type": "number", "required": true },
      { "key": "from_date",     "label": "From Date",        "type": "date",   "required": true },
      { "key": "to_date",       "label": "To Date",          "type": "date",   "required": true },
      { "key": "reason",        "label": "Reason",           "type": "textarea","required": true },
      { "key": "school_name",   "label": "School Name",      "type": "text",   "required": true },
      { "key": "hm_name",       "label": "Headmaster Name",  "type": "text",   "required": true }
    ]
  },
  {
    "key": "teacher_transfer",
    "name": "Teacher Transfer Request",
    "description": "Request transfer of a teacher to another school",
    "fields": ["..."]
  }
]
```

**Available Templates:**
| Key | Name |
|---|---|
| `leave_approval` | Leave Approval Letter |
| `teacher_transfer` | Teacher Transfer Request |
| `infrastructure_request` | Infrastructure Request |
| `parent_notice` | Parent Notice |
| `scholarship_recommendation` | Scholarship Recommendation |
| `compliance_submission` | Compliance Submission |
| `budget_request` | Budget Request |

---

### POST `/copilot/generate-letter`
Generate an official government letter from a template.

**Access:** HM, MEO, DEO

**Request Body:**
```json
{
  "letter_type": "leave_approval",
  "template_fields": {
    "teacher_name": "Rajesh Kumar",
    "designation": "Secondary Grade Teacher",
    "leave_type": "Medical Leave",
    "leave_days": 3,
    "from_date": "2025-06-02",
    "to_date": "2025-06-04",
    "reason": "Undergoing medical treatment for fever and related complications",
    "school_name": "ZPHS Venkatapuram",
    "hm_name": "Lakshmi Rao"
  },
  "language": "English"
}
```

**Field Validation:**
- `letter_type`: Must be a valid template key
- `template_fields`: Must include all `required: true` fields from the template
- `language`: `"English"` (default) or `"Telugu"`

**Response 201:**
```json
{
  "id": 5,
  "letter_type": "leave_approval",
  "reference_number": "EDU/LA/2025/XYZ12",
  "content": "GOVERNMENT OF ANDHRA PRADESH\nDepartment of School Education\n\nRef. No.: EDU/LA/2025/XYZ12\nDate: 30-05-2025\n\nTo,\nThe Headmaster/Principal\nZPHS Venkatapuram\n\nSub: Approval of Medical Leave — Rajesh Kumar, SGT\n\nSir/Madam,\n\nWith reference to the leave application submitted by Sri Rajesh Kumar, Secondary Grade Teacher...\n\nYours faithfully,\n\nLakshmi Rao\nHeadmaster, ZPHS Venkatapuram",
  "created_at": "2025-05-30T10:00:00+05:30"
}
```

**Error Responses:**
| Code | Message |
|---|---|
| 400 | Unknown letter type: {type} |
| 422 | Validation error |

---

### GET `/copilot/letters/history`
Get generated letters history.

**Query Params:** `limit` (default: 20)

**Response 200:**
```json
[
  {
    "id": 5,
    "letter_type": "leave_approval",
    "reference_number": "EDU/LA/2025/XYZ12",
    "created_at": "2025-05-30T10:00:00+05:30"
  }
]
```

---

### GET `/copilot/letters/{letter_id}`
Fetch a specific generated letter.

---

### POST `/copilot/export-letter/pdf?letter_id={id}`
Download a generated letter as PDF.

**Response:** `application/pdf` stream

---

### POST `/copilot/export-letter/docx?letter_id={id}`
Download a generated letter as editable DOCX.

**Response:** `application/vnd.openxmlformats-officedocument.wordprocessingml.document` stream

---

## 3. Automated Report Generator

### POST `/copilot/generate-report`
Generate an AI-narrated analytics report from live database data.

**Access:** HM, MEO, DEO

**Request Body:**
```json
{
  "report_type": "school_performance",
  "report_scope": "school",
  "scope_id": 5,
  "academic_year": "2024-25"
}
```

**Report Types:**
| `report_type` | Description | Data Sources |
|---|---|---|
| `school_performance` | Academic performance, risk distribution | students, assessments |
| `attendance` | Attendance rates, absenteeism patterns | attendance |
| `teacher_performance` | Teacher metrics, workload, attendance | teachers, attendance |
| `school_health` | Infrastructure, composite health scores | schools |

**Scope:**
| `report_scope` | Description |
|---|---|
| `school` | Single school (school_id) |
| `mandal` | All schools in a mandal |
| `district` | All schools in a district |

**Response 201:**
```json
{
  "id": 3,
  "report_type": "school_performance",
  "report_scope": "school",
  "content": "EXECUTIVE SUMMARY\nThe school shows 86% attendance rate...",
  "content_json": {
    "executive_summary": "ZPHS Venkatapuram maintains an 86.4% attendance rate for the current month...",
    "kpi_analysis": "Total enrollment: 450 students. High-risk students: 23 (5.1%). Average assessment score: 68.5%...",
    "trends": "Attendance has improved by 2.3% over the last quarter. Dropout risk is declining for Classes 6-8...",
    "risks": "15 students in Classes 9 and 10 remain at HIGH or CRITICAL dropout risk. Teacher-student ratio at 1:32...",
    "recommendations": [
      "Deploy counselor for 15 high-risk students in Classes 9-10 before June 15",
      "Initiate remedial classes in Mathematics for Class 8 students below 40%",
      "Schedule parent meetings for 23 chronic absentees this week",
      "Request additional teacher for Science from MEO office",
      "Upgrade drinking water facility to address infrastructure gap"
    ],
    "action_plan": [
      "Week 1: HM to conduct risk student review session",
      "Week 2: Parent meetings for chronic absentees",
      "Week 3-4: Remedial class implementation",
      "Month 2: Infrastructure request submission to MEO"
    ]
  },
  "created_at": "2025-05-30T11:00:00+05:30"
}
```

---

### GET `/copilot/reports/history`
Get report generation history.

---

### GET `/copilot/reports/{report_id}`
Fetch a specific report.

---

### GET `/copilot/reports/{report_id}/export/pdf`
Download a report as structured PDF with sections, headings, and bullets.

---

### GET `/copilot/reports/{report_id}/export/docx`
Download a report as editable DOCX document.

---

## 4. Translation (Telugu ↔ English)

### POST `/copilot/translate`
Translate text between Telugu and English.

**Access:** All authenticated users

**Request Body:**
```json
{
  "source_language": "Telugu",
  "target_language": "English",
  "text": "అన్ని ప్రభుత్వ పాఠశాలల ప్రధానోపాధ్యాయులు జూన్ 30, 2025 నాటికి హాజరు డేటాను అప్లోడ్ చేయాలి."
}
```

**Validation Rules:**
- `source_language`: `"Telugu"` or `"English"` only
- `target_language`: `"Telugu"` or `"English"` only; must differ from source
- `text`: min 1, max 10,000 characters

**Response 201:**
```json
{
  "id": 12,
  "source_language": "Telugu",
  "target_language": "English",
  "source_text": "అన్ని ప్రభుత్వ పాఠశాలల ప్రధానోపాధ్యాయులు జూన్ 30, 2025 నాటికి హాజరు డేటాను అప్లోడ్ చేయాలి.",
  "translated_text": "All Headmasters of government schools must upload attendance data by June 30, 2025.",
  "word_count": 15,
  "created_at": "2025-05-30T12:00:00+05:30"
}
```

**Error Responses:**
| Code | Message |
|---|---|
| 400 | Unsupported source language: {lang} |
| 400 | Source and target language must be different |
| 400 | Text exceeds 10,000 character limit |

---

### GET `/copilot/translations/history`
Get translation history for the current user.

**Query Params:** `limit` (default: 20)

**Response 200:**
```json
[
  {
    "id": 12,
    "source_language": "Telugu",
    "target_language": "English",
    "preview": "అన్ని ప్రభుత్వ పాఠశాలల ప్రధానోపాధ్యాయులు జూన్ 30, 2025...",
    "word_count": 15,
    "created_at": "2025-05-30T12:00:00+05:30"
  }
]
```

---

## Database Schema

```sql
-- Circular Summaries
CREATE TABLE circular_summaries (
  id               SERIAL PRIMARY KEY,
  user_id          INTEGER NOT NULL REFERENCES users(id),
  file_name        VARCHAR(500) NOT NULL,
  file_size_kb     INTEGER,
  raw_text_preview TEXT,
  summary_json     JSONB NOT NULL,
  created_at       TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_circular_summaries_user_id ON circular_summaries(user_id);

-- Generated Letters
CREATE TABLE generated_letters (
  id               SERIAL PRIMARY KEY,
  user_id          INTEGER NOT NULL REFERENCES users(id),
  letter_type      VARCHAR(100) NOT NULL,
  template_fields  JSONB NOT NULL,
  content          TEXT NOT NULL,
  reference_number VARCHAR(100),
  created_at       TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_generated_letters_user_id  ON generated_letters(user_id);
CREATE INDEX idx_generated_letters_type     ON generated_letters(letter_type);

-- Generated Reports
CREATE TABLE generated_reports (
  id               SERIAL PRIMARY KEY,
  user_id          INTEGER NOT NULL REFERENCES users(id),
  report_type      VARCHAR(100) NOT NULL,
  report_scope     VARCHAR(50),
  scope_id         INTEGER,
  content          TEXT NOT NULL,
  content_json     JSONB,
  created_at       TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_generated_reports_user_id  ON generated_reports(user_id);
CREATE INDEX idx_generated_reports_type     ON generated_reports(report_type);

-- Translations
CREATE TABLE translations (
  id               SERIAL PRIMARY KEY,
  user_id          INTEGER NOT NULL REFERENCES users(id),
  source_language  VARCHAR(50) NOT NULL,
  target_language  VARCHAR(50) NOT NULL,
  source_text      TEXT NOT NULL,
  translated_text  TEXT NOT NULL,
  word_count       INTEGER,
  created_at       TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_translations_user_id ON translations(user_id);
```

---

## Role Access Matrix — Copilot

| Endpoint | DEO | MEO | HM | TEACHER | STUDENT | PARENT |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| Summarize Circular | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| Circular History | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| Generate Letter | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| Letter Templates | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| Export Letter PDF/DOCX | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| Generate Report | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| Export Report PDF/DOCX | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| Translate Text | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Translation History | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
