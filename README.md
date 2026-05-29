# EduAI Governance Platform

> Enterprise-grade, mobile-first AI-Powered Education Governance Platform built for real-world district-level educational administration in India.

---

## Overview

EduAI Governance Platform is a production-ready, role-based education management system that digitalizes governance workflows across all levels of the education hierarchy — from District Education Officers down to Students and Parents. It uses AI to predict dropout risk, score school health, recommend interventions, and surface actionable insights in real time.

### Key Capabilities

| Capability | Description |
|---|---|
| Role-Based Dashboards | Separate, purpose-built dashboards for DEO, MEO, HM, Teacher, Student, Parent |
| AI Dropout Prediction | ML model predicts at-risk students 4–6 weeks in advance |
| Attendance Intelligence | Real-time attendance tracking with anomaly detection |
| School Health Scoring | Composite 0–100 score per school using 12 parameters |
| Governance Reporting | Automated district-level reports with trend analysis |
| Parent Engagement | WhatsApp + Push notifications for parents |
| Offline Support | Attendance and core data work offline with sync |

---

## Architecture

```
edu-governance-platform/
├── mobile-app/          # React Native Expo (iOS + Android)
├── backend/             # FastAPI (Python 3.11+)
├── docs/
│   ├── api/             # Full REST API documentation
│   ├── workflows/       # Business process documentation
│   └── architecture/    # System design documentation
├── .env.example
└── README.md
```

### Technology Stack

**Mobile App**
- React Native 0.74 + Expo SDK 51
- TypeScript (strict mode)
- Zustand (state management)
- React Query v5 (server state & caching)
- NativeWind v4 (Tailwind CSS for React Native)
- React Navigation v6 (role-based navigation)
- Axios (HTTP client)
- AsyncStorage (offline persistence)
- Expo Notifications (push notifications)

**Backend**
- Python 3.11 + FastAPI 0.111
- SQLAlchemy 2.0 (async ORM)
- Alembic (database migrations)
- PostgreSQL 16 (primary database)
- Redis 7 (caching + rate limiting)
- Pydantic v2 (data validation)
- Python-Jose (JWT)
- Passlib + bcrypt (password hashing)
- OpenAI SDK (AI insights)
- Celery + Redis (background tasks)

**Infrastructure**
- Docker + Docker Compose
- Nginx (reverse proxy)
- AWS S3 (file storage)
- Firebase (push notifications)
- Twilio / WATI (WhatsApp)
- Sentry (error monitoring)

---

## User Roles

| Role | Description |
|---|---|
| `DEO` | District Education Officer — district-wide governance |
| `MEO` / `BEO` | Mandal/Block Education Officer — cluster monitoring |
| `HM` | Headmaster / Principal — school command center |
| `TEACHER` | Classroom management, attendance, grading |
| `STUDENT` | Learning dashboard, assignments, AI tutor |
| `PARENT` | Child monitoring, notifications, complaints |

---

## Quick Start

### Prerequisites

- Node.js 20+
- Python 3.11+
- PostgreSQL 16
- Redis 7
- Expo CLI (`npm install -g expo-cli`)
- Docker (optional, recommended)

---

## PostgreSQL Setup

```bash
# Create database
psql -U postgres
CREATE DATABASE eduai_db;
CREATE USER eduai_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE eduai_db TO eduai_user;
\q
```

---

## Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate
# Activate (macOS/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment variables
cp ../.env.example .env
# Edit .env with your actual values

# Run database migrations
alembic upgrade head

# Seed initial data (optional)
python -m app.utils.seed_data

# Start development server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Backend runs at: `http://localhost:8000`
Swagger UI: `http://localhost:8000/docs`
ReDoc: `http://localhost:8000/redoc`

---

## Mobile App Setup

```bash
cd mobile-app

# Install dependencies
npm install

# Copy environment variables
cp ../.env.example .env.local
# Edit EXPO_PUBLIC_API_BASE_URL to point to your backend

# Start Expo development server
npx expo start

# Run on Android
npx expo start --android

# Run on iOS
npx expo start --ios

# Run on web
npx expo start --web

# Build production APK
npx eas build --platform android --profile production

# Build production IPA
npx eas build --platform ios --profile production
```

---

## Docker Compose (Recommended)

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f backend

# Stop all services
docker-compose down

# Reset database
docker-compose down -v && docker-compose up -d
```

---

## Environment Variables

Copy `.env.example` to `.env` and configure:

| Variable | Description | Required |
|---|---|---|
| `DATABASE_URL` | PostgreSQL connection string | Yes |
| `JWT_SECRET_KEY` | Secret key for JWT signing | Yes |
| `OPENAI_API_KEY` | OpenAI API key for AI features | Yes |
| `FIREBASE_*` | Firebase credentials for push notifications | Yes |
| `TWILIO_*` | Twilio credentials for WhatsApp/SMS | Optional |
| `AWS_*` | AWS credentials for file storage | Optional |
| `REDIS_URL` | Redis connection string | Yes |
| `EXPO_PUBLIC_API_BASE_URL` | Backend API URL for mobile app | Yes |

---

## Folder Structure

### Mobile App

```
mobile-app/src/
├── screens/
│   ├── auth/             # Login, ForgotPassword
│   ├── common/           # Splash, Profile, Settings
│   ├── deo/              # District dashboard, school health, dropout, insights
│   ├── meo/              # Cluster monitor, attendance intelligence
│   ├── hm/               # School dashboard, attendance, student monitor
│   ├── teacher/          # Attendance, assignments, grading, AI assistant
│   ├── student/          # Assignments, performance, AI tutor
│   └── parent/           # Child tracking, notifications, complaints
├── components/
│   ├── common/           # Button, Card, Header, LoadingSpinner, etc.
│   └── charts/           # AttendanceChart, PerformanceChart, etc.
├── navigation/           # Role-based stack/tab navigators
├── services/             # Axios API service functions
├── store/                # Zustand global state stores
├── hooks/                # Custom React hooks
├── utils/                # Helper functions, formatters, validators
├── constants/            # API URLs, role constants, app config
├── types/                # TypeScript interfaces and types
└── theme/                # Colors, typography, spacing tokens
```

### Backend

```
backend/app/
├── api/v1/               # Route handlers (thin controllers)
│   ├── auth.py
│   ├── students.py
│   ├── teachers.py
│   ├── attendance.py
│   ├── assessments.py
│   ├── analytics.py
│   ├── notifications.py
│   └── ai.py
├── core/                 # Config, security, dependencies
├── models/               # SQLAlchemy ORM models
├── schemas/              # Pydantic request/response schemas
├── services/             # Business logic layer
├── repositories/         # Database access layer
├── ai/                   # AI/ML modules
├── analytics/            # Analytics engine
├── notifications/        # Push, WhatsApp, SMS notification handlers
├── database/             # DB session, base model
└── utils/                # Helpers, validators, seed data
```

---

## API Documentation

Full API documentation is available at:
- **Interactive**: `http://localhost:8000/docs` (Swagger UI)
- **Alternative**: `http://localhost:8000/redoc` (ReDoc)
- **Markdown**: [`docs/api/README.md`](docs/api/README.md)

---

## Development Workflow

```bash
# 1. Create a feature branch
git checkout -b feature/your-feature-name

# 2. Backend: run tests
cd backend && pytest tests/ -v --cov=app

# 3. Mobile: run type check
cd mobile-app && npx tsc --noEmit

# 4. Mobile: run linter
cd mobile-app && npx eslint src/ --ext .ts,.tsx

# 5. Commit with conventional commits
git commit -m "feat(attendance): add bulk attendance upload API"

# 6. Push and open PR
git push origin feature/your-feature-name
```

---

## Coding Standards

### Frontend (TypeScript)
- Strict TypeScript — no `any` types
- Functional components with hooks only
- Named exports for components
- co-locate component-specific styles
- React Query for all server state
- Zustand only for global client state (auth, theme)
- NativeWind utility classes (no inline StyleSheet for layout)
- File naming: `PascalCase` for components, `camelCase` for hooks/utils

### Backend (Python)
- Type hints on all functions
- Async-first — all DB calls use `await`
- Repository pattern — no raw SQL in services
- Service layer — no business logic in routes
- Pydantic v2 models for all I/O
- Dependency injection via FastAPI `Depends`
- HTTP exceptions via `HTTPException` only
- File naming: `snake_case` throughout

---

## Development Phases

### Phase 1 — Foundation (Weeks 1–4)
- [x] Authentication & JWT
- [x] Role-based navigation
- [x] Attendance marking & tracking
- [x] Basic dashboards (DEO, MEO, HM, Teacher)

### Phase 2 — Analytics & Assessments (Weeks 5–8)
- [x] Analytics dashboards
- [x] Assessment creation & grading
- [x] Push notifications
- [x] WhatsApp alerts

### Phase 3 — AI & Engagement (Weeks 9–12)
- [x] Dropout prediction model
- [x] AI risk detection
- [x] Parent engagement portal
- [x] Recommendation engine
- [x] School health scoring

---

## Contribution Guide

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Follow coding standards above
4. Write tests for new features
5. Ensure all tests pass (`pytest` for backend, `jest` for frontend)
6. Submit a Pull Request with a clear description

---

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

---

## Support

For issues and questions, open a GitHub Issue or contact the platform team.
