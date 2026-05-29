# EduAI Platform — Complete Business Workflow Documentation

---

## 1. User Authentication Workflow

**Actors:** All roles (DEO, MEO, HM, Teacher, Student, Parent)

### Flow:
```
[User Opens App]
       │
       ▼
[Splash Screen loads stored token]
       │
       ├──Token Found──► [Validate token against /auth/me]
       │                        │
       │                  Token Valid ──► [Load Role Dashboard]
       │                  Token Expired ► [Auto-refresh via /auth/refresh]
       │                                        │
       │                                  Refresh OK ──► [Load Role Dashboard]
       │                                  Refresh Fail ► [Redirect to Login]
       │
       └──No Token──► [Show Login Screen]
                              │
                       [User enters email + password]
                              │
                       [POST /auth/login]
                              │
                       ┌──────┴──────┐
                    Success       Failure
                       │              │
             [Store JWT tokens]  [Show error message]
             [Load Role Dashboard]
```

### Database Operations:
- Read: `users` table (by email)
- Read: Verify `hashed_password`
- Update: `users.reset_token` (on forgot password)

### Notifications:
- Failed login: no notification (security)
- Password reset: Email with reset link

---

## 2. Attendance Workflow

**Actors:** Teacher (marks), HM (monitors), MEO/DEO (oversees), Parent (receives alerts)

### Teacher Marks Attendance:
```
[Teacher opens Attendance screen]
       │
[Select Class & Section]
       │
[System loads student list for class]
       │
[Teacher marks each student: PRESENT/ABSENT/LATE]
       │
[Optional: Capture GPS location for geo-verification]
       │
[POST /attendance/mark/bulk]
       │
[Backend validates: no duplicate, school_id match]
       │
       ├── Success ──► [Attendance saved to DB]
       │                      │
       │              [Check for anomalies]
       │                      │
       │              [Absent > 3 days?]──Yes──► [Send Parent WhatsApp alert]
       │                                         [Flag student for HM review]
       │
       └── Conflict ──► [Show "Already marked" warning]
```

### Attendance Alert Escalation:
```
Day 1-2 Absent:     No action
Day 3 Absent:       Auto-send WhatsApp to Parent
Day 5 Absent:       HM receives push notification
Day 10 Absent:      MEO receives alert, HM follow-up required
Day 15 Absent:      DEO flagged, risk score updated to HIGH
Day 20+ Absent:     CRITICAL dropout risk — counselor deployment
```

### State Diagram:
```
[PRESENT] ◄──────────────────────── [Returns to school]
    │                                           ▲
    ▼                                           │
[ABSENT Day 1] ──► [ABSENT Day 3: Alert] ──► [ABSENT Day 10: Escalate]
                                                │
                                          [DROPOUT RISK]
```

---

## 3. Student Monitoring Workflow

**Actors:** Teacher, HM, MEO, DEO

```
[Daily Attendance Marked]
         │
[AI Risk Score Recalculated Nightly]
         │
   ┌─────┴─────┐
LOW Risk    HIGH/CRITICAL Risk
   │              │
[No action]  [Generate AI Insight]
             [Notify HM via Push]
                  │
         [HM reviews student profile]
                  │
         [Takes action: counselor / parent meeting]
                  │
         [Mark insight as actioned]
                  │
         [System tracks resolution]
```

---

## 4. Teacher Monitoring Workflow

**Actors:** HM, MEO, DEO

```
[Daily: Teacher logs attendance]
         │
[Weekly: HM reviews teacher attendance % ]
         │
Below 80%──► [HM flags teacher]
             [MEO notified if persistent]
                   │
             [DEO can initiate show-cause]
```

### Teacher Performance Metrics:
- Attendance rate (weekly/monthly)
- Assessment submission timeliness
- Student performance in their classes
- Workload: classes × students

---

## 5. Assessment Workflow

**Actors:** Teacher (creates, grades), Student (takes), HM/MEO/DEO (monitors)

```
[Teacher creates assessment on app]
         │
[POST /assessments/ → saved as Draft]
         │
[Teacher sets: type, subject, class, max_marks, date]
         │
[Publishes assessment → students can view]
         │
[Exam conducted]
         │
[Teacher enters marks on app]
         │
[POST /assessments/{id}/grade]
         │
[System auto-calculates % and grade (A+/A/B...)]
         │
[Analytics updated: class average, pass rate, rank]
         │
[Parent notified via push: "FA1 results published"]
```

---

## 6. Parent Notification Workflow

**Trigger Events:**
| Event | Channel | Message |
|-------|---------|---------|
| Attendance: 3+ consecutive absent | WhatsApp + Push | "Arjun absent 3 days — please contact school" |
| Exam results published | Push | "FA1 Mathematics results: B+" |
| Dropout risk HIGH | WhatsApp | "Urgent: Please meet HM regarding Arjun's performance" |
| School event | Push | "Annual Sports Day on June 15 at 9 AM" |
| Fee reminder | WhatsApp | "Term fees due by June 30" |

### Notification Flow:
```
[Trigger Event Detected]
         │
[Identify Parent's contact (phone / FCM token)]
         │
         ├──Has FCM Token──► [Firebase Push Notification]
         │
         └──Has Phone──► [WhatsApp via Twilio/WATI API]
                               │
                    ┌──────────┴──────────┐
                 Delivered             Failed
                    │                     │
              [Mark DELIVERED]      [Retry (3x)]
                                         │
                                   [Mark FAILED]
                                   [Log error]
```

---

## 7. AI Risk Detection Workflow

**Runs:** Nightly batch (2:00 AM) + On-demand (per request)

```
[Nightly Cron Job / On-demand API call]
         │
[Fetch all active students for school/district]
         │
[For each student: extract features]
    │
    ├── Attendance rate (last 90 days)
    ├── Consecutive absences
    ├── Average assessment percentage
    ├── Socio-economic flags (scholarship, disability)
    └── Gender + class level risk factors
         │
[Compute weighted risk score (0.0 – 1.0)]
         │
         ├── ≥ 0.80 → CRITICAL (immediate action)
         ├── ≥ 0.65 → HIGH (alert HM today)
         ├── ≥ 0.40 → MEDIUM (monitor weekly)
         └── < 0.40 → LOW (no action)
         │
[Save risk score to student record]
[Create AI Insight record]
         │
[HIGH/CRITICAL → Notify HM via push]
[CRITICAL → Also notify MEO]
```

### Feature Engineering:
```python
risk_score = (
    (1 - attendance_rate)         × 0.35  +  # Most important
    min(consecutive_abs / 10, 1)  × 0.25  +  # Consecutive absences
    (1 - avg_assessment / 100)    × 0.20  +  # Academic performance
    socio_economic_flag           × 0.10  +  # Scholarship/poverty
    gender_distance_risk          × 0.05  +  # Girls grade 6+
    disability_flag               × 0.05     # Disability
)
```

---

## 8. Dropout Prediction Workflow

```
[Student Data Collected Daily]
         │
[Risk Score Updated Nightly]
         │
[Score Trend Monitored (4-week rolling)]
         │
[Trend Worsening? (score up 20% over 4 weeks)]
         │
         YES ──► [Escalate to CRITICAL]
                 [Notify: Teacher → HM → MEO → DEO chain]
                 [Generate intervention plan (AI)]
                 [Track intervention actions]
                        │
                 [Outcome: Student retained or dropout confirmed]
                        │
                 [Update model with outcome for retraining]
```

---

## 9. School Health Workflow

**Runs:** Weekly (Sundays, 1:00 AM) + On-demand

```
[POST /ai/school/{id}/health-score]
         │
[Collect 8 metric inputs:]
    │
    ├── Student attendance rate (last 30d)
    ├── Teacher attendance rate
    ├── Dropout rate (inactive/total)
    ├── Academic performance (avg %)
    ├── Teacher-student ratio
    ├── Infrastructure score (6 checks)
    ├── High-risk student ratio
    └── Assessment coverage rate
         │
[Compute weighted score → 0–100]
[Assign grade: A (80+) / B (65+) / C (50+) / D (<50)]
         │
[Save to school.health_score]
         │
[Grade D (<50) → Alert MEO, schedule inspection]
[Grade C (<65) → Alert HM, action plan required]
```

---

## 10. Governance Reporting Workflow

**Frequency:** Monthly (auto) + On-demand

**Actors:** DEO (receives), System (generates)

```
[First of Month: Cron triggers report generation]
         │
[Aggregate district data:]
    ├── All school health scores
    ├── Attendance trends (month-over-month)
    ├── Dropout count and risk status
    ├── Teacher rationalization data
    ├── Assessment performance averages
    └── AI insight summary
         │
[AI generates executive summary (GPT-4o)]
         │
[Report saved as JSON + PDF]
         │
[Sent to DEO via email + push notification]
         │
[Available at /analytics/district/{id}/report]
```

### Escalation Logic:
```
School Health Score < 40     → MEO inspection required within 7 days
District Dropout Rate > 5%   → State-level alert triggered
Attendance Rate < 75% (3 weeks) → Emergency intervention plan
Teacher Shortage > 30%       → Rationalization request auto-generated
```

---

## Sequence Diagram: Student At-Risk Alert

```
Teacher        Backend        AI Engine      HM App        Parent Phone
   │               │               │              │               │
   │──Mark Absent─►│               │              │               │
   │               │──Save record─►│              │               │
   │               │──Run risk────►│              │               │
   │               │◄──Score=0.75──│              │               │
   │               │──Update student record       │               │
   │               │──Create AI Insight           │               │
   │               │──Send Push──────────────────►│               │
   │               │──Send WhatsApp──────────────────────────────►│
   │               │               │              │               │
   │               │               │     [HM views insight]       │
   │               │               │     [Marks actioned]        │
   │               │               │              │               │
   │               │◄──POST /insights/{id}/action─│               │
   │               │──Update AI Insight           │               │
```
