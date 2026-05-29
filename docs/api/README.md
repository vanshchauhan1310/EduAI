# EduAI Platform — Complete API Documentation

**Base URL:** `http://localhost:8000/api/v1`
**Auth:** Bearer JWT token in `Authorization` header
**Interactive Docs:** `/docs` (Swagger UI) | `/redoc` (ReDoc)

---

## Authentication

### POST `/auth/login`
Authenticate a user and receive JWT tokens.

**Access:** Public

**Request Body:**
```json
{ "email": "deo@district.gov.in", "password": "SecurePass@123" }
```

**Response 200:**
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "id": 1, "email": "deo@district.gov.in",
    "full_name": "Ravi Kumar", "role": "DEO",
    "school_id": null, "district_id": 1, "mandal_id": null
  }
}
```

**Errors:**
| Code | Message |
|------|---------|
| 401 | Invalid email or password |
| 403 | Account is deactivated |
| 422 | Validation error |

---

### POST `/auth/refresh`
Exchange a refresh token for a new token pair.

**Access:** Public

**Request Body:**
```json
{ "refresh_token": "eyJ..." }
```

**Response 200:** Same as `/auth/login`

---

### POST `/auth/logout`
Invalidate the current session (client discards tokens).

**Access:** Any authenticated user

**Response:** `204 No Content`

---

### POST `/auth/forgot-password`
Trigger a password reset email.

**Request Body:**
```json
{ "email": "teacher@school.gov.in" }
```

**Response 200:**
```json
{ "message": "If an account exists, a reset link has been sent." }
```

---

### POST `/auth/reset-password`
Reset password using the token from the email.

**Request Body:**
```json
{ "token": "abc123xyz", "new_password": "NewSecurePass@1" }
```

**Validation Rules:**
- `new_password`: min 8 chars, 1 uppercase letter, 1 digit

---

### GET `/auth/me`
Returns the currently authenticated user profile.

**Access:** Any authenticated user

**Response 200:**
```json
{ "id": 1, "email": "hm@school.gov.in", "full_name": "Lakshmi Rao", "role": "HM", "school_id": 5, "district_id": 1, "mandal_id": 2, "is_active": true }
```

---

## Attendance APIs

### POST `/attendance/mark`
Mark attendance for a single student or teacher.

**Access:** TEACHER, HM, MEO, DEO

**Request Body:**
```json
{
  "reference_type": "STUDENT",
  "reference_id": 101,
  "school_id": 5,
  "date": "2025-05-29",
  "status": "PRESENT",
  "session": "FULL",
  "class_id": 7,
  "section": "A",
  "latitude": 16.5062,
  "longitude": 80.6480,
  "remarks": null
}
```

**Status Values:** `PRESENT | ABSENT | LATE | HALF_DAY | HOLIDAY | LEAVE`

**Response 200:**
```json
{ "id": 1234, "reference_type": "STUDENT", "reference_id": 101, "date": "2025-05-29", "status": "PRESENT", "is_geo_verified": true }
```

**Errors:**
| Code | Message |
|------|---------|
| 409 | Attendance already marked for student on this date |
| 403 | Insufficient role |

---

### POST `/attendance/mark/bulk`
Mark attendance for an entire class at once.

**Access:** TEACHER, HM

**Request Body:**
```json
{
  "reference_type": "STUDENT",
  "school_id": 5,
  "class_id": 7,
  "section": "A",
  "date": "2025-05-29",
  "records": [
    { "reference_id": 101, "status": "PRESENT" },
    { "reference_id": 102, "status": "ABSENT", "remarks": "Fever" },
    { "reference_id": 103, "status": "LATE" }
  ]
}
```

**Response 200:**
```json
{ "marked": 3, "skipped": 0, "skipped_ids": [] }
```

---

### GET `/attendance/student/{student_id}/summary`
Get attendance summary for a student over a date range.

**Access:** Any authenticated user

**Query Params:** `from_date` (YYYY-MM-DD), `to_date` (YYYY-MM-DD)

**Response 200:**
```json
{
  "total_days": 22, "present_days": 19, "absent_days": 2, "late_days": 1,
  "half_days": 0, "attendance_percentage": 86.36,
  "consecutive_absences": 0, "last_absent_date": "2025-05-22"
}
```

---

### GET `/attendance/school/{school_id}/daily`
Get school-wide attendance summary for a given date.

**Query Params:** `report_date` (default: today)

**Response 200:**
```json
{ "total": 450, "present": 392, "absent": 52, "late": 6, "rate": 87.11 }
```

---

### GET `/attendance/student/{student_id}/records`
Get raw attendance records for a student.

**Query Params:** `from_date`, `to_date`

**Response 200:**
```json
[
  { "id": 1, "date": "2025-05-29", "status": "PRESENT", "session": "FULL", "remarks": null },
  { "id": 2, "date": "2025-05-28", "status": "ABSENT", "session": "FULL", "remarks": "Sick" }
]
```

---

## Student APIs

### POST `/students/`
Create a new student record.

**Access:** HM, MEO, DEO

**Request Body:**
```json
{
  "admission_no": "A2025001", "aadhaar_no": "123456789012",
  "first_name": "Arjun", "last_name": "Kumar",
  "date_of_birth": "2012-05-15", "gender": "MALE", "category": "OBC",
  "parent_name": "Ramesh Kumar", "parent_phone": "+919876543210",
  "current_class": 7, "section": "A", "academic_year": "2024-25",
  "school_id": 5, "enrollment_date": "2025-06-01",
  "receives_midday_meal": true, "receives_scholarship": false, "has_disability": false
}
```

**Errors:**
| Code | Message |
|------|---------|
| 409 | Student with admission number already exists |
| 422 | Validation error |

---

### GET `/students/{student_id}`
Get student details.

**Access:** Any authenticated user

---

### PUT `/students/{student_id}`
Update student information.

**Access:** HM, MEO, DEO

---

### GET `/students/`
List students with filtering and pagination.

**Query Params:** `school_id`, `class_grade`, `section`, `risk_level`, `page`, `page_size`

**Response 200:**
```json
{
  "items": [...],
  "total": 450, "page": 1, "page_size": 20, "pages": 23
}
```

---

### GET `/students/school/{school_id}/high-risk`
Get all HIGH and CRITICAL risk students in a school.

**Access:** HM, MEO, DEO

---

### POST `/students/{student_id}/dropout`
Mark a student as dropped out.

**Access:** HM, MEO, DEO

**Query Params:** `reason`, `dropout_date` (YYYY-MM-DD)

---

## Assessment APIs

### POST `/assessments/`
Create a new assessment.

**Access:** TEACHER, HM

**Request Body:**
```json
{
  "title": "FA1 Mathematics", "assessment_type": "FA1",
  "subject": "Mathematics", "class_grade": 7, "section": "A",
  "school_id": 5, "academic_year": "2024-25",
  "max_marks": 50, "passing_marks": 20, "duration_minutes": 60
}
```

**Assessment Types:** `FA1 | FA2 | FA3 | FA4 | SA1 | SA2 | UNIT_TEST | HALF_YEARLY | ANNUAL`

---

### GET `/assessments/school/{school_id}`
List all assessments for a school.

**Query Params:** `class_grade`, `subject`

---

### POST `/assessments/{assessment_id}/grade`
Submit grades for an assessment.

**Request Body:**
```json
{
  "results": [
    { "student_id": 101, "marks_obtained": 42, "is_absent": false, "teacher_feedback": "Good work" },
    { "student_id": 102, "is_absent": true }
  ]
}
```

---

### GET `/assessments/{assessment_id}/analytics`
Get analytics for an assessment.

**Response 200:**
```json
{
  "assessment_id": 1, "total_students": 35,
  "average_percentage": 68.5, "min_percentage": 24.0,
  "max_percentage": 96.0, "pass_rate": 85.7
}
```

---

## Analytics APIs

### GET `/analytics/district/{district_id}/overview`
District-level governance overview for DEO.

**Access:** DEO

**Response 200:**
```json
{
  "district_id": 1, "total_schools": 245, "total_students": 85420,
  "high_risk_students": 1284, "attendance_rate_this_month": 87.3,
  "dropout_risk_rate": 1.50
}
```

---

### GET `/analytics/mandal/{mandal_id}/overview`
Mandal-level cluster overview for MEO.

**Access:** MEO, DEO

---

### GET `/analytics/school/{school_id}/performance`
School-level performance for HM.

**Query Params:** `academic_year`

**Response 200:**
```json
{
  "school_id": 5, "academic_year": "2024-25",
  "total_students": 450, "attendance_rate_30d": 86.4,
  "risk_breakdown": { "LOW": 390, "MEDIUM": 40, "HIGH": 15, "CRITICAL": 5 }
}
```

---

## AI APIs

### GET `/ai/student/{student_id}/risk`
Get AI-generated dropout risk assessment for a student.

**Access:** Any authenticated user

**Response 200:**
```json
{
  "student_id": 101, "student_name": "Arjun Kumar",
  "risk_score": 0.72, "risk_level": "HIGH",
  "risk_factors": ["Low attendance rate: 68%", "Consecutive absences: 5 days"],
  "recommendations": ["Schedule immediate counselor visit", "Notify parent via WhatsApp"],
  "features": { "attendance_rate": 0.68, "consecutive_absences": 5, "avg_assessment_percentage": 45.2 }
}
```

---

### POST `/ai/school/{school_id}/run-risk-scan`
Run dropout risk assessment for all students in a school.

**Access:** HM, MEO, DEO

**Response 200:**
```json
{ "school_id": 5, "students_scanned": 450, "high_risk_count": 23, "results_summary": [...] }
```

---

### GET `/ai/school/{school_id}/health-score`
Get AI-computed school health score.

**Response 200:**
```json
{
  "school_id": 5, "school_name": "ZPHS Venkatapuram",
  "health_score": 74.5, "grade": "B",
  "breakdown": {
    "student_attendance_rate": { "value": "87%", "weight": 20, "weighted_score": 17.4 },
    "infrastructure_score": { "value": "4/6 amenities", "weight": 10, "weighted_score": 6.67 }
  },
  "total_students": 450, "total_teachers": 14
}
```

---

### GET `/ai/student/{student_id}/recommendations`
Get AI-generated learning recommendations for a student.

**Response 200:**
```json
{
  "student_id": 101, "student_name": "Arjun Kumar",
  "subject_performance": { "Mathematics": 68.0, "Science": 84.5 },
  "weak_subjects": ["Mathematics", "English"],
  "strong_subjects": ["Science", "Telugu"],
  "recommendations": [
    { "subject": "Mathematics", "current_average": 68.0, "priority": "MEDIUM",
      "interventions": ["Khan Academy exercises", "Peer tutoring"], "target_percentage": 50 }
  ],
  "ai_enhanced_plan": "Specific GPT-4o generated plan..."
}
```

---

### GET `/ai/insights/{scope}/{reference_id}`
Get all AI insights for a student, school, mandal, or district.

**Scope Values:** `STUDENT | SCHOOL | MANDAL | DISTRICT`

---

### POST `/ai/insights/{insight_id}/action`
Mark an AI insight as actioned.

**Request Body:**
```json
{ "action_notes": "Counselor visited student on 2025-05-29. Parent notified via WhatsApp." }
```

---

## Notification APIs

### GET `/notifications/`
Get all notifications for the current user.

**Query Params:** `limit` (default: 20, max: 100)

---

### POST `/notifications/{notification_id}/read`
Mark a notification as read.

**Response:** `204 No Content`

---

### POST `/notifications/send-alert`
Send a push notification to a user.

**Access:** HM, MEO, DEO

**Request Body:**
```json
{
  "recipient_id": 42, "title": "Attendance Alert",
  "body": "Arjun Kumar has been absent for 5 consecutive days.",
  "notification_type": "ATTENDANCE_ALERT"
}
```

---

### PUT `/notifications/fcm-token`
Register or update FCM token for push notifications.

**Query Params:** `token` (FCM device token)

---

## Health Check

### GET `/health`
Server health check.

**Response 200:**
```json
{ "status": "healthy", "version": "1.0.0" }
```

---

## Authentication Flow

```
Client                        Server
  |                             |
  |-- POST /auth/login -------->|
  |<-- { access_token,          |
  |      refresh_token,         |
  |      user }                 |
  |                             |
  |-- GET /students/ ---------->|
  |   (Authorization: Bearer   |
  |    <access_token>)          |
  |<-- 200 OK                   |
  |                             |
  |   (access_token expires)    |
  |-- POST /auth/refresh ------>|
  |   { refresh_token: "..." }  |
  |<-- { new_access_token,      |
  |      new_refresh_token }    |
```

---

## Role Access Matrix

| Endpoint Category | DEO | MEO | HM | TEACHER | STUDENT | PARENT |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| Auth | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| District Analytics | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Mandal Analytics | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| School Analytics | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| Mark Attendance | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |
| Create Student | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| View Students | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |
| Create Assessment | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |
| View Own Data | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ |
| AI Risk Scan | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| Notifications | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
