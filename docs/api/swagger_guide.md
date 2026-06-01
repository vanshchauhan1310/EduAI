# Swagger UI Guide — EduAI Governance Platform

FastAPI **auto-generates** interactive API documentation from your Python code. No extra configuration needed.

---

## Accessing the Docs

Once the backend is running (`uvicorn main:app --reload`):

| URL | Tool | Use |
|---|---|---|
| `http://localhost:8000/docs` | **Swagger UI** | Interactive — try APIs live in browser |
| `http://localhost:8000/redoc` | **ReDoc** | Read-only — cleaner reference view |
| `http://localhost:8000/openapi.json` | **Raw JSON** | Import into Postman, Insomnia, etc. |

---

## How Swagger Works in FastAPI

FastAPI reads your route decorators + Pydantic schemas and builds the OpenAPI spec automatically.

### Example — how `copilot.py` becomes a Swagger endpoint:

```python
# backend/app/api/v1/copilot.py

@router.post(
    "/summarize-circular",          # ← becomes the path
    response_model=CircularSummaryResponse,  # ← documents the response shape
    status_code=201,                # ← shows in docs
)
async def summarize_circular(
    file: UploadFile = File(..., description="Government circular PDF"),  # ← shown in docs
    current_user: User = Depends(require_hm),   # ← security shown as 🔒
    db: AsyncSession = Depends(get_db),         # ← hidden from docs (injected)
):
    """Upload a PDF circular and receive an AI-generated structured summary."""
    # ↑ This docstring becomes the endpoint description in Swagger
```

This automatically produces in Swagger:
- **Path**: `POST /api/v1/copilot/summarize-circular`
- **Description**: "Upload a PDF circular and receive an AI-generated structured summary."
- **Request body**: file upload field with description
- **Response**: documented JSON shape from `CircularSummaryResponse`
- **Auth**: padlock icon (🔒) — requires Bearer token

---

## Step-by-Step: Testing APIs via Swagger UI

### Step 1 — Open Swagger
Navigate to: `http://localhost:8000/docs`

You'll see all API groups (tags) collapsed:
```
▶ Authentication
▶ Attendance
▶ Students
▶ Assessments
▶ Analytics
▶ AI Insights
▶ Notifications
▶ Admin Copilot    ← new
```

---

### Step 2 — Authenticate (required for all endpoints)

1. Click **`POST /api/v1/auth/login`** → **Try it out**
2. Enter credentials:
```json
{
  "email": "hm@school.gov.in",
  "password": "Admin@123"
}
```
3. Click **Execute**
4. Copy the `access_token` from the response
5. Click the **Authorize 🔒** button (top right of Swagger page)
6. Paste: `Bearer eyJ...your-token...`
7. Click **Authorize** → **Close**

All subsequent requests will include the JWT automatically.

---

### Step 3 — Test the Admin Copilot APIs

#### A. Circular Summarizer

1. Expand **Admin Copilot** tag
2. Click `POST /api/v1/copilot/summarize-circular` → **Try it out**
3. Click **Choose File** → select any government PDF
4. Click **Execute**
5. Response appears below with the 6-section JSON summary

#### B. Letter Generator

1. Click `GET /api/v1/copilot/letters/templates` → **Try it out** → **Execute**
   - See all 7 available templates + their required fields

2. Click `POST /api/v1/copilot/generate-letter` → **Try it out**
3. Paste request body:
```json
{
  "letter_type": "leave_approval",
  "template_fields": {
    "teacher_name": "Rajesh Kumar",
    "designation": "SGT",
    "leave_type": "Medical Leave",
    "leave_days": 3,
    "from_date": "2025-06-10",
    "to_date": "2025-06-12",
    "reason": "Fever and medical treatment",
    "school_name": "ZPHS Venkatapuram",
    "hm_name": "Lakshmi Rao"
  },
  "language": "English"
}
```
4. Click **Execute** — see the generated letter + reference number

5. Copy the `id` from the response
6. Click `POST /api/v1/copilot/export-letter/pdf?letter_id={id}` → **Try it out**
7. Enter the `letter_id` → **Execute** → Click **Download file**

#### C. Report Generator

```json
{
  "report_type": "attendance",
  "report_scope": "school",
  "scope_id": 1,
  "academic_year": "2024-25"
}
```

#### D. Translation

```json
{
  "source_language": "Telugu",
  "target_language": "English",
  "text": "అన్ని పాఠశాలల ప్రధానోపాధ్యాయులు హాజరు నివేదికను సమర్పించాలి."
}
```

---

## How Pydantic Models Appear in Swagger

Your schemas become documented request/response bodies automatically.

```python
# backend/app/schemas/copilot.py

class LetterGenerateRequest(BaseModel):
    letter_type: str = Field(..., description="Template key, e.g. 'leave_approval'")
    template_fields: dict[str, Any] = Field(..., description="Dynamic form values")
    language: str = Field(default="English", description="Output language: English or Telugu")
```

In Swagger this shows:
```
Request body (application/json):
  {
    "letter_type": "string"          ← with description "Template key, e.g. 'leave_approval'"
    "template_fields": {}            ← with description "Dynamic form values"
    "language": "English"            ← with default value shown
  }
```

---

## API Tags (Grouping)

Each router is tagged in Swagger by the `tags=` parameter:

```python
router = APIRouter(prefix="/copilot", tags=["Admin Copilot"])
#                                     ↑ This creates the group in Swagger
```

All EduAI tags:
| Tag | Prefix |
|---|---|
| Authentication | `/api/v1/auth` |
| Students | `/api/v1/students` |
| Attendance | `/api/v1/attendance` |
| Assessments | `/api/v1/assessments` |
| Analytics | `/api/v1/analytics` |
| AI Insights | `/api/v1/ai` |
| Notifications | `/api/v1/notifications` |
| Admin Copilot | `/api/v1/copilot` |
| Health | `/health` |

---

## Importing into Postman

1. Open Postman → **Import**
2. Select **Link**
3. Paste: `http://localhost:8000/openapi.json`
4. Click **Import**
5. All 40+ endpoints appear as a collection

---

## Swagger in Production

In production, disable Swagger to avoid exposing API internals:

```python
# backend/main.py
app = FastAPI(
    title=settings.APP_NAME,
    docs_url="/docs" if settings.APP_ENV != "production" else None,   # ← disable in prod
    redoc_url="/redoc" if settings.APP_ENV != "production" else None,
)
```

Or protect it with HTTP Basic Auth for internal team use.
