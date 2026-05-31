# EduSakhi — Adaptive AI Tutor Prototype (LangChain)

A standalone Streamlit prototype of the **Student AI Tutor** for CBSE Class 10
Government-school students (Physics, Chemistry, Mathematics) — English + Telugu.
It demonstrates the full adaptive loop, grounded in the NCERT knowledge base and
in your **uploaded PDFs (with OCR)**.

> Standalone from the `backend/` app. Stack: **LangChain + HuggingFace LLM + SQLite +
> RapidOCR**. Pure-Python TF-IDF RAG (no heavy embedding deps).

---

## What it does

From `Subject → Chapter → Concept` + a mastery score (0–100), the tutor produces:

1. **Student analysis** — level, weak/strong concepts, misconceptions
2. **Learning path** — prioritized concepts (reason, est. time, activity)
3. **Bilingual lesson** — English **and** Telugu explanation, real-life + worked
   examples, common mistakes, revision notes
4. **Adaptive quiz** — difficulty mix scales to mastery; **you choose the count
   (up to 100) and the types** (MCQ, MSQ, Short, Long — any combo)
5. **Score-gated progression** — pass (≥ 70%) → advance to the next concept;
   below → re-attempt with fresh questions + targeted review topics
6. **Recommendations** — next concepts, estimated new mastery, next lesson

Plus two extra modes:
- **🧾 Board exam paper** — subjective questions with `marks`, `sample_answer`,
  `expected_points` (matches the teammate's `exam_prep` JSON schema; downloadable).
- **💬 Chat** (separate page) — ask doubts in your own words; the topic is
  **auto-detected** from the question and answered from notes + your PDFs.

### Personalization (0–100 mastery)
| mastery | level | quiz difficulty mix |
|---|---|---|
| ≤ 40 | Beginner | easy-heavy |
| 41–70 | Intermediate | balanced |
| > 70 | Advanced | hard-heavy |

Mastery update (EMA): `new = 0.6·old + 0.4·quiz%`. Stored in SQLite, so re-running
continues from saved progress.

---

## RAG + PDFs

- Retrieval (TF-IDF) over a built-in **Class 10 knowledge base** *and* any
  **ingested PDF chunks** — PDF content is preferred (PDF-first grounding), so
  lessons **and quiz questions** are based on your uploaded material.
- **PDF parsing:** PyMuPDF (`fitz`). A **quality gate** rejects unreadable PDFs.
- **OCR fallback:** for scanned / symbol-font NCERT PDFs, enable **Use OCR**
  (RapidOCR) with a page range — it renders + reads pages (~a few sec/page).
- PDFs for testing live in `prototype/pdfs/` (git-ignored; see its README).

---

## LLM

Generation uses a **HuggingFace** chat model via `langchain-huggingface`. Without a
token (or on a failed call) it falls back to a built-in offline model so the demo
still runs. Telugu is produced by translating generated English (reliable), with
per-segment repair.

---

## Setup

```bash
cd prototype
pip install -r requirements.txt          # langchain, huggingface, sqlalchemy, pymupdf, rapidocr…

copy .env.example .env                    # Windows  (cp on macOS/Linux)
# In .env set a HuggingFace token (free) with the "Make calls to Inference
# Providers" permission:  https://huggingface.co/settings/tokens
#   HF_API_TOKEN=hf_...
#   HF_MODEL=Qwen/Qwen2.5-7B-Instruct
```

## Run

```bash
streamlit run app.py        # main tutor UI  ->  http://localhost:8501
                            # the "Chat" page appears in the left nav

python demo.py              # optional CLI walkthrough of one concept
```

### Using your own PDF
Sidebar → **📚 Knowledge base** → upload an NCERT PDF (text-based ingests directly;
scanned/symbol-font → tick **Use OCR** + page range) → pick the matching
Subject/Concept → **Generate**. The "🔎 RAG" panel shows the `📄 PDF` chunks used.

---

## Files

| File | Role |
|---|---|
| `app.py` | Streamlit UI (tutor + exam mode + PDF upload/OCR) |
| `pages/1_Chat.py` | 💬 Chat page (auto-topic, RAG-grounded) |
| `schemas.py` | Pydantic models: `TutorResponse`, `QuizItem`, `ExamQuestion`, `Assessment` |
| `learning_system.py` | `AdaptiveTutor` — LCEL chains, quiz (types/count), grading, progression, Telugu |
| `exam_generator.py` | `ExamGenerator` — board-exam paper in the exam_prep schema |
| `chat_engine.py` | `TutorChat` — auto-topic, RAG-grounded answers |
| `curriculum.py` | CBSE Class 10 PCM modules (subject → chapter → ordered concepts) |
| `knowledge_base.py` | Curated Class 10 concept notes (RAG corpus) |
| `rag.py` | TF-IDF retriever over notes + PDF chunks (PDF-first grounding) |
| `pdf_ingest.py` | PyMuPDF text extraction + quality gate + RapidOCR fallback |
| `llm_provider.py` | `get_chat_model()` — HF LLM or offline `DemoChatModel` |
| `db.py` | SQLite: learners, per-topic mastery, quiz_attempts, KB chunks |
| `content_bank.py` | Offline demo content (no-token fallback) |
| `demo.py` | CLI walkthrough |

---

## Notes / limits
- Retrieval is **TF-IDF (keyword)**; PDF-first grounding forces your PDF in for the
  selected topic. For meaning-based matching across large PDFs, swap to embeddings
  (e.g. `bge`/`e5` + pgvector/Qdrant).
- Telugu quality depends on the model (`Qwen2.5-7B` is rough on science terms); a
  more multilingual/Indic-tuned model improves it.
- OCR is ~a few seconds per page — OCR a **chapter's page range**, not the whole book.
- `prototype/` is a prototype; production should move storage to the backend DB
  (Postgres + pgvector) and PDFs to object storage.
```
