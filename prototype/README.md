# Personalized Learning & Quiz System — LangChain Prototype

A small, standalone prototype (separate from the EduSakhi backend) that shows the
core idea: **adapt teaching and testing to each learner, and persist progress.**

## What it does

For one learner + one topic, it runs an adaptive loop:

```
load mastery (SQL) ─▶ teach at the learner's LEVEL ─▶ quiz at their DIFFICULTY
        ▲                                                          │
        └────────── update mastery (SQL) ◀── grade ◀──────────────┘
```

- **LangChain LCEL chains** do the generation:
  - `explanation_chain = prompt | model | StrOutputParser`
  - `quiz_chain        = prompt | model | PydanticOutputParser(Quiz)`
- **Personalization** maps mastery → level/difficulty:
  | mastery | level | quiz |
  |---|---|---|
  | < 0.4 | beginner | easy |
  | 0.4–0.7 | intermediate | medium |
  | ≥ 0.7 | advanced | hard |
- **Mastery update (EMA):** `new = 0.6·old + 0.4·quiz_score`
- **SQL storage (SQLite):** learners, per-topic mastery, and every quiz attempt —
  so re-running *continues* from saved progress.

## LLM

Generation uses a **HuggingFace** model via `langchain-huggingface`. If a live
call fails (or no token is set), it falls back to a built-in offline model so the
demo always runs.

## Setup

```bash
cd prototype
pip install -r requirements.txt

copy .env.example .env        # Windows  (cp on macOS/Linux)
# Edit .env and paste your HuggingFace token (free):
#   https://huggingface.co/settings/tokens   (READ scope)
```

## Run

```bash
python demo.py                        # learner "Asha", topic "Photosynthesis"
python demo.py "Fractions"            # built-in offline topic
python demo.py "Newton's Laws" Ravi   # any topic + learner (needs a token)
```

Built-in offline topics (work with no token): **Photosynthesis**, **Fractions**.
With a token, any topic works because the LLM generates the content.

## Files

| File | Role |
|---|---|
| `schemas.py` | Pydantic `Quiz`/`MCQ` the parser targets |
| `content_bank.py` | Curated offline content (no-key demo + fallback) |
| `llm_provider.py` | `get_chat_model()` — HF LLM or offline `DemoChatModel` |
| `learning_system.py` | The LangChain chains + personalization + grading |
| `db.py` | SQLite persistence (learners, progress, quiz_attempts) |
| `demo.py` | Runnable walkthrough |
