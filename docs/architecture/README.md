# EduAI Platform — Complete Architecture Documentation

---

## 1. High-Level System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      MOBILE CLIENTS                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐   │
│  │  DEO App │  │  MEO App │  │   HM App │  │ Teacher/     │   │
│  │(District)│  │(Cluster) │  │ (School) │  │ Student/     │   │
│  │          │  │          │  │          │  │ Parent App   │   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └──────┬───────┘   │
└───────┼──────────────┼──────────────┼────────────────┼──────────┘
        │              │              │                │
        └──────────────┴──────────────┴────────────────┘
                               │ HTTPS/REST
                               ▼
┌──────────────────────────────────────────────────────────────────┐
│                        NGINX (Reverse Proxy)                      │
│              Rate Limiting | SSL Termination | Load Balancing     │
└──────────────────────────────┬───────────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────────┐
│                    FASTAPI APPLICATION LAYER                       │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────────────┐  │
│  │  Auth &     │  │  Business    │  │    AI / ML Engine       │  │
│  │  JWT Guard  │  │  Services    │  │  (Risk | Recommend |    │  │
│  │             │  │              │  │   School Health)        │  │
│  └─────────────┘  └──────────────┘  └────────────────────────┘  │
└──────────┬──────────────────────────────────────┬────────────────┘
           │                                      │
           ▼                                      ▼
┌─────────────────────┐              ┌────────────────────────────┐
│   PostgreSQL 16      │              │      External Services      │
│  (Primary Database)  │              │  ┌──────────┐ ┌─────────┐ │
│                      │              │  │ Firebase │ │ Twilio  │ │
│  Tables:             │              │  │  (Push)  │ │(WhatsApp│ │
│  users, schools,     │              │  └──────────┘ └─────────┘ │
│  students, teachers, │              │  ┌──────────┐ ┌─────────┐ │
│  attendance,         │              │  │  AWS S3  │ │ OpenAI  │ │
│  assessments,        │              │  │ (Files)  │ │  (GPT)  │ │
│  notifications,      │              │  └──────────┘ └─────────┘ │
│  ai_insights         │              └────────────────────────────┘
└─────────────────────┘
           │
           ▼
┌─────────────────────┐
│    Redis 7           │
│  (Cache + Sessions + │
│   Rate Limiting)     │
└─────────────────────┘
```

---

## 2. Mobile App Architecture

### Navigation Architecture:
```
RootNavigator
    │
    ├── AuthNavigator (unauthenticated)
    │       ├── LoginScreen
    │       └── ForgotPasswordScreen
    │
    └── RoleNavigator (authenticated — switches by user.role)
            ├── DEONavigator      (Tab: District | Health | Dropout | Insights)
            ├── MEONavigator      (Tab: Cluster | Attendance | Performance | Teachers)
            ├── HMNavigator       (Tab: Dashboard | Attendance | Students | Assessments | Parents)
            ├── TeacherNavigator  (Tab: Attendance | Assignments | Grading | AI Assist)
            ├── StudentNavigator  (Tab: Assignments | Attendance | Performance | AI Tutor)
            └── ParentNavigator   (Tab: Attendance | Performance | Alerts | Complaints)
```

### State Management:
```
Zustand Stores
    ├── useAuthStore     → user, tokens, isAuthenticated, isLoading
    └── useAppStore      → offline status, selectedSchoolId, academicYear, notificationCount

React Query (Server State)
    ├── /auth/me                    → staleTime: 5min
    ├── /analytics/district/*       → staleTime: 5min, refetch: manual
    ├── /attendance/school/*/daily  → refetchInterval: 5min
    ├── /students                   → staleTime: 2min
    └── /notifications              → staleTime: 1min
```

### API Layer (Axios):
```
api.ts (Axios instance)
    ├── Interceptor: Attach JWT token to every request
    ├── Interceptor: Auto-refresh on 401 (failed queue pattern)
    └── BaseURL: EXPO_PUBLIC_API_BASE_URL
```

### Offline Strategy:
- AsyncStorage: Cache last-fetched attendance data
- React Query: `staleWhileRevalidate` pattern
- Bulk attendance: Queue offline marks, sync on reconnect
- Critical data (student list, school info): Persisted locally

---

## 3. Backend Architecture (Modular Monolith)

```
backend/
├── main.py                    # FastAPI app, lifespan, CORS, Sentry
├── app/
│   ├── api/v1/                # Thin controllers (route handlers only)
│   │   ├── auth.py            # POST /auth/*
│   │   ├── attendance.py      # POST/GET /attendance/*
│   │   ├── students.py        # CRUD /students/*
│   │   ├── assessments.py     # CRUD /assessments/*
│   │   ├── analytics.py       # GET /analytics/*
│   │   ├── notifications.py   # GET/POST /notifications/*
│   │   ├── ai.py              # GET/POST /ai/*
│   │   └── router.py          # Assembles all routers
│   ├── core/
│   │   ├── config.py          # Pydantic Settings from .env
│   │   ├── security.py        # JWT, bcrypt functions
│   │   └── dependencies.py    # get_current_user, require_roles
│   ├── models/                # SQLAlchemy ORM mapped classes
│   ├── schemas/               # Pydantic v2 request/response models
│   ├── services/              # Business logic (no DB calls)
│   ├── repositories/          # Data access (only DB calls)
│   ├── ai/                    # ML inference modules
│   ├── analytics/             # Aggregation engines
│   ├── notifications/         # Firebase, Twilio integrations
│   ├── database/              # Async engine, session factory
│   └── utils/                 # Helpers, seed data
```

### Request Lifecycle:
```
HTTP Request
     │
[NGINX] → Rate limit check
     │
[FastAPI Middleware] → CORS, GZip
     │
[Route Handler] → Input validation (Pydantic)
     │
[Dependencies] → JWT decode, role check
     │
[Service Layer] → Business logic
     │
[Repository] → Async DB queries (SQLAlchemy)
     │
[Response] → Pydantic serialization → JSON
```

---

## 4. Database Architecture

### Entity Relationship Diagram:
```
districts
    │ 1
    │ ∞
mandals
    │ 1
    │ ∞
schools ────────────────────────────────────┐
    │ 1                                      │
    ├── ∞ students ──── ∞ attendance         │
    │         │                              │
    │         └── ∞ assessment_results       │
    │                   │                    │
    └── ∞ teachers      └── ∞ assessments ──┘
             │
             └── ∞ attendance (teacher)

users ──── teacher_profile (1:1)
      ──── student_profile (1:1)
      ──── notifications (1:∞)

ai_insights (polymorphic: STUDENT | SCHOOL | MANDAL | DISTRICT)
```

### Mandatory Tables:

| Table | Primary Key | Indexes | Key Fields |
|-------|-------------|---------|------------|
| `users` | `id` | `email`, `phone` | role, school_id, fcm_token |
| `districts` | `id` | `name` | state |
| `mandals` | `id` | `district_id` | name |
| `schools` | `id` | `dise_code`, `mandal_id` | health_score |
| `students` | `id` | `admission_no`, `school_id` | risk_level, dropout_risk_score |
| `teachers` | `id` | `employee_id`, `school_id` | subject_area, teacher_type |
| `attendance` | `id` | `reference_id`, `date`, `school_id` | reference_type, status |
| `assessments` | `id` | `school_id`, `class_grade` | assessment_type, subject |
| `assessment_results` | `id` | `assessment_id`, `student_id` | percentage, grade |
| `notifications` | `id` | `recipient_id`, `created_at` | channel, status, is_read |
| `ai_insights` | `id` | `reference_id`, `insight_type` | risk_score, scope |

### Indexing Strategy:
```sql
-- High-frequency queries
CREATE INDEX idx_attendance_ref_date ON attendance(reference_id, date);
CREATE INDEX idx_attendance_school_date ON attendance(school_id, date);
CREATE INDEX idx_students_school_risk ON students(school_id, risk_level);
CREATE INDEX idx_students_active ON students(school_id, is_active);
CREATE INDEX idx_notifications_recipient ON notifications(recipient_id, is_read, created_at);
CREATE INDEX idx_insights_scope_ref ON ai_insights(scope, reference_id);
```

---

## 5. Authentication Architecture

```
Login Request
     │
[Verify email + bcrypt password]
     │
[Generate Access Token (60 min)]
     │   payload: { sub: user_id, role, school_id, district_id, exp }
     │
[Generate Refresh Token (30 days)]
     │   payload: { sub: user_id, type: "refresh", exp }
     │
[Return both tokens to client]

Protected Request
     │
[Extract Bearer token from Authorization header]
     │
[Decode & verify JWT signature (HS256)]
     │
[Check token not expired]
     │
[Load user from DB by user_id]
     │
[Check user.is_active == true]
     │
[Check user.role ∈ required_roles]
     │
[Inject user into route handler]
```

---

## 6. AI Architecture

### Pipeline Overview:
```
Raw Data (attendance, assessments, student profile)
         │
Feature Engineering
    ├── attendance_rate = present / total_days
    ├── consecutive_absences = streak of absent days
    ├── avg_assessment_pct = mean(assessment_results.percentage)
    ├── socio_economic_risk = scholarship flag
    └── gender_distance = female + class >= 6
         │
Weighted Scoring Model (Phase 1 — Rule-based)
    risk_score = Σ(feature_i × weight_i)
         │
Risk Level Classification:
    ≥ 0.80 → CRITICAL
    ≥ 0.65 → HIGH
    ≥ 0.40 → MEDIUM
    < 0.40 → LOW
         │
AI Insight Record Created
         │
Optional: GPT-4o Enhancement (if API key configured)
    → Personalized recommendations
    → Natural language summary
```

### School Health Scoring:
```
8 Parameters:
1. student_attendance_rate  (weight: 20)
2. teacher_attendance_rate  (weight: 15)
3. dropout_rate             (weight: 15)
4. academic_performance     (weight: 15)
5. teacher_student_ratio    (weight: 10)
6. infrastructure_score     (weight: 10)
7. high_risk_student_ratio  (weight: 8)
8. assessment_coverage      (weight: 7)

Total possible: 100
Health Score = Σ(score_i × weight_i) / 100 × 100
```

---

## 7. Analytics Architecture

### Aggregation Layers:
```
Raw Events (attendance marks, assessment grades)
         │
         ▼
Daily Aggregates (school-level)
    - total_present, total_absent, attendance_rate
         │
         ▼
Monthly Rollups (mandal-level)
    - avg_attendance, dropout_count, risk_distribution
         │
         ▼
Quarterly Reports (district-level)
    - school rankings, intervention summary, trend analysis
```

---

## 8. Notification Architecture

```
Trigger Event
     │
[Notification Service]
     │
     ├── Channel: PUSH ──► Firebase Admin SDK
     │                        → User's FCM token
     │                        → Title + Body + Data payload
     │
     ├── Channel: WHATSAPP ──► Twilio API
     │                          → whatsapp:+91XXXXXXXXXX
     │                          → Template-based message
     │
     ├── Channel: SMS ──► Twilio SMS API
     │
     └── Channel: IN_APP ──► Saved to notifications table
                              → Fetched by client on next poll

Delivery tracking:
  PENDING → SENT → DELIVERED → READ
  PENDING → FAILED (retry 3x, then log)
```

---

## 9. Role-Based Access Architecture

### Permission Hierarchy:
```
DEO (highest)
 └── can access: district analytics, all schools, all mandals
      └── MEO
           └── can access: mandal schools, cluster data
                └── HM
                     └── can access: own school data
                          └── TEACHER
                               └── can access: own class data

STUDENT  → own data only
PARENT   → child's data only
```

### Middleware Implementation:
```python
# Role dependency injection
require_deo    = require_roles(UserRole.DEO)
require_meo    = require_roles(UserRole.DEO, UserRole.MEO)
require_hm     = require_roles(UserRole.DEO, UserRole.MEO, UserRole.HM)
require_teacher = require_roles(DEO, MEO, HM, TEACHER)
require_any    = require_roles(*all_roles)
```

---

## 10. Scalability Architecture

### Horizontal Scaling Plan:
```
Phase 1 (< 10k users):
  Single FastAPI server + PostgreSQL + Redis
  Deployed on single VM (4 CPU, 8 GB RAM)

Phase 2 (10k–100k users):
  Docker Swarm / Kubernetes
  3× FastAPI replicas behind Nginx
  PostgreSQL with read replicas
  Redis Cluster (3 nodes)

Phase 3 (100k+ users):
  Kubernetes auto-scaling (HPA)
  PostgreSQL → AWS RDS with connection pooling (PgBouncer)
  Celery workers for async AI processing
  CDN for static assets
  Background jobs via Celery Beat
```

### Caching Strategy:
```
L1 (React Query — client):     5 minutes for analytics
L2 (Redis — server):           School health scores (24h TTL)
                                District overview (15min TTL)
                                User session data (access_token lifetime)
L3 (PostgreSQL):               Full data, source of truth
```

### Background Job Architecture:
```
Celery Beat Scheduler
    ├── Every night 2:00 AM  → Run dropout risk scan (all districts)
    ├── Every Sunday 1:00 AM → Compute school health scores
    ├── 1st of month 3:00 AM → Generate governance reports
    └── Every 5 minutes      → Process notification queue
```
