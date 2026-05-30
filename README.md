# EduSakhi — AI Education Platform with Governance

> **EduSakhi** is the core: an AI-powered personalised adaptive learning system for CBSE Class 10
> students (Physics, Chemistry, Mathematics) with bilingual (English + Telugu) tutoring.
> The **Governance layer** (roles, schools, attendance, analytics) is built *on top of* and
> *integrated into* the same EduSakhi backend — one FastAPI app, one database, one set of conventions.

---

## How the two parts fit together

EduSakhi is the foundation. Everything else plugs into it using the **same stack** so it stays
fully integratable:

| Layer | Stack (shared everywhere) |
|---|---|
| Web framework | FastAPI (single app at `backend/app/main.py`) |
| Database | SQLAlchemy ORM, **sync**, SQLite by default (`DATABASE_URL` to switch to Postgres) |
| Session | `database/db.py` → `get_db()` dependency, used by **all** modules |
| Validation | Pydantic v2 |
| AI / LLM | HuggingFace `InferenceClient` (Qwen3 / Llama 3.1 / Gemma) + RAG over ChromaDB |
| Auth | JWT (python-jose) + passlib/bcrypt, role-based access |

```
backend/
├── app/main.py            # ONE FastAPI app: EduSakhi endpoints + governance endpoints
├── database/
│   ├── db.py              # shared sync engine + get_db()           [EduSakhi]
│   └── models.py          # learning tables + governance tables (User, School, Attendance)
├── core/                  # shared auth/security, config, deps      [NEW – governance]
├── governance/            # roles, schools, attendance services     [NEW – governance]
├── adaptive_engine/       # mastery, dependency graph, diagnostic   [EduSakhi]
├── rag/                   # PDF ingestion + retriever               [EduSakhi]
├── llm/                   # AI tutor + quiz generator               [EduSakhi]
├── analytics/             # learning analytics                      [EduSakhi]
└── requirements.txt
```

Because governance modules import the **same** `database.db.get_db` session and add their tables to
the **same** `models.py`, a governance endpoint and an EduSakhi endpoint can share data in one
request (e.g. a Teacher marks attendance *and* views a student's concept mastery).

---

## User Roles

| Role | Description |
|---|---|
| `DEO` | District Education Officer — district-wide governance |
| `MEO` / `BEO` | Mandal/Block Education Officer — cluster monitoring |
| `HM` | Headmaster / Principal — school command center |
| `TEACHER` | Attendance, grading, assigns EduSakhi learning paths |
| `STUDENT` | EduSakhi learning dashboard, diagnostics, AI tutor, quizzes |
| `PARENT` | Child monitoring, notifications |

---

## Quick Start

```bash
cd backend

python -m venv venv
venv\Scripts\activate            # Windows   (source venv/bin/activate on macOS/Linux)

pip install -r requirements.txt

copy ..\.env.example .env         # Windows   (cp on macOS/Linux). SQLite default — no Postgres needed.

python -m app.utils.seed_data     # optional: create demo admin + school + student

uvicorn app.main:app --reload --port 8000
```

- Swagger UI: <http://localhost:8000/docs>
- ReDoc: <http://localhost:8000/redoc>

---

## Modules

**EduSakhi (learning core)**
1. Automated knowledge base — NCERT PDFs → ChromaDB (no manual JSON)
2. Diagnostic assessment engine
3. Student knowledge profile (mastery 0.0–1.0)
4. Concept dependency graph (NetworkX)
5. Adaptive learning path engine
6. Bilingual AI tutor (English + Telugu)
7. RAG system (PDF → ChromaDB → LLM)
8. Adaptive quiz generation
9. Mastery update engine (`0.7·old + 0.3·quiz`)
10. Learning analytics

**Governance (integrated layer)**
- JWT auth + role-based access control
- Schools & student/teacher records
- Attendance tracking
- (planned) dropout prediction, school health scoring, parent notifications

---

## Environment Variables

Copy `.env.example` → `backend/.env`:

| Variable | Description | Default |
|---|---|---|
| `DATABASE_URL` | DB connection string | `sqlite:///./edusakhi.db` |
| `JWT_SECRET_KEY` | Secret for signing JWTs | _(change me)_ |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token lifetime | `60` |
| `HF_API_TOKEN` | HuggingFace token for the AI tutor | _(optional)_ |
| `HF_MODEL` | LLM model id | `Qwen/Qwen3-8B` |
| `EMBEDDING_MODEL` | Embedding model | `BAAI/bge-small-en-v1.5` |
| `CHROMA_DB_PATH` | ChromaDB persist path | `./chroma_db` |

---

## License

MIT — see [LICENSE](LICENSE).
