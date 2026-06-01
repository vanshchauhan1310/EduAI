"""
Streamlit frontend — Adaptive Tutor (CBSE Class 10 PCM, English + Telugu, RAG)
=============================================================================
- Pick Subject -> Chapter -> Concept from the built-in Class 10 modules.
- Student chooses how many questions to attempt.
- RAG grounds the lesson/quiz in the Class 10 knowledge base (sources shown).
- Score-gated: pass (>= threshold) -> advance to next concept;
               below -> re-attempt the quiz + review recommendations.

Run from the prototype/ folder:
    streamlit run app.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st

import db as store
import curriculum
import rag
from learning_system import (
    AdaptiveTutor, level_for, quiz_distribution, update_mastery,
    LANGUAGES, PASS_THRESHOLD,
)
from llm_provider import using_real_llm


@st.cache_resource
def get_tutor() -> AdaptiveTutor:
    store.init_db()
    return AdaptiveTutor()


@st.cache_resource
def get_examgen():
    from exam_generator import ExamGenerator
    return ExamGenerator()


tutor = get_tutor()

_LEVEL_TO_DIFF = {"Beginner": "Easy", "Intermediate": "Medium", "Advanced": "Hard"}

st.set_page_config(page_title="EduSakhi Tutor", page_icon="🎓", layout="wide")
st.title("🎓 EduSakhi — Adaptive AI Tutor (CBSE Class 10 · PCM · EN + తెలుగు · RAG)")
st.caption("Class 10 modules · RAG-grounded lessons · adaptive quiz · "
           f"score ≥ {PASS_THRESHOLD:.0f}% to advance")


# ── Sidebar: module selection ──────────────────────────────────────────────────
with st.sidebar:
    st.header("Student & module")
    learner_name = st.text_input("Student name", value="Asha")
    subject = st.selectbox("Subject", curriculum.subjects())
    chapter = st.selectbox("Chapter", curriculum.chapters(subject))

    options = curriculum.concepts(subject, chapter)
    want = st.session_state.get("concept_name")
    idx = options.index(want) if want in options else 0
    concept = st.selectbox("Concept", options, index=idx)
    st.session_state.concept_name = concept

    language = st.selectbox("Language", list(LANGUAGES.keys()),
                            format_func=lambda k: LANGUAGES[k], index=2)
    mode = st.radio("Question mode", ["Adaptive quiz", "Board exam paper"])
    num_q = st.number_input("Number of questions (up to 100)", 1, 100, 5)
    q_types = ["MCQ"]
    if mode == "Adaptive quiz":
        q_types = st.multiselect(
            "Question types (any combo)",
            ["MCQ", "MSQ", "Short Answer", "Long Answer"],
            default=["MCQ"],
        ) or ["MCQ"]
    if num_q > 20:
        st.caption("⏳ Many questions are generated in batches — give it a moment.")

    topic_key = f"{subject} / {concept}"
    db = store.SessionLocal()
    learner = store.get_or_create_learner(db, learner_name.strip() or "Asha")
    saved = store.get_mastery(db, learner.id, topic_key)
    mastery = st.slider("Mastery score (0-100)", 0, 100, int(round(saved)))

    manual_rag = st.text_area("Override NCERT content (optional)", height=90)

    import pdf_ingest
    with st.expander(f"📚 Knowledge base — {store.count_chunks(db)} PDF chunks"):
        st.caption(f"PDFs stored in (test only): `{pdf_ingest.PDF_DIR}`")

        use_ocr = st.checkbox("Use OCR (for scanned / symbol-font PDFs — slow, ~few s/page)")
        ocr_start = ocr_end = None
        if use_ocr:
            cc1, cc2 = st.columns(2)
            ocr_start = cc1.number_input("From page", 1, 2000, 1)
            ocr_end = cc2.number_input("To page", 1, 2000, 20)

        def _run_ingest(path, label):
            bar = st.progress(0.0, text="Working…") if use_ocr else None
            def _prog(done, total):
                if bar:
                    bar.progress(done / max(1, total), text=f"OCR page {done}/{total}")
            with st.spinner(f"Parsing {label}…"):
                res = pdf_ingest.ingest_pdf(
                    path, subject, chapter, db, use_ocr=use_ocr,
                    page_start=int(ocr_start) if use_ocr else 1,
                    page_end=int(ocr_end) if use_ocr else None,
                    progress=_prog if use_ocr else None,
                )
            if bar:
                bar.empty()
            if res["success"]:
                total = rag.rebuild_index()
                st.success(f"Ingested {res['chunks']} chunks from {res['source']} "
                           f"({res['pages']} pages). RAG index: {total} docs.")
            else:
                st.error(res.get("error", "Ingestion failed."))

        up = st.file_uploader("Upload an NCERT PDF", type="pdf", key="pdf_up")
        if up is not None and st.button("Save & ingest upload", key="ingest_up"):
            path = pdf_ingest.save_pdf_bytes(up.name, up.getbuffer())
            _run_ingest(path, up.name)

        existing = pdf_ingest.list_pdfs()
        if existing:
            pick = st.selectbox("…or ingest a PDF already in the folder", existing)
            if st.button("Ingest selected", key="ingest_existing"):
                _run_ingest(pdf_ingest.path_for(pick), pick)

        srcs = store.kb_sources(db)
        if srcs:
            st.caption("Indexed PDFs:")
            for s in srcs:
                st.caption(f"• {s[0]} — {s[1]}/{s[2]} — {s[3]} chunks")

    st.divider()
    st.markdown(f"**LLM:** {'🟢 HuggingFace' if using_real_llm() else '⚪ offline'}")
    st.markdown(f"**Storage:** `{store.DB_PATH}`")


# ── Status bar ─────────────────────────────────────────────────────────────────
dist = quiz_distribution(mastery, num_q)
c1, c2, c3, c4 = st.columns(4)
c1.metric("Mastery", f"{mastery}/100")
c2.metric("Level", level_for(mastery))
c3.metric("Quiz plan", ", ".join(f"{v}{k[0]}" for k, v in dist.items() if v))
c4.metric("Pass mark", f"{PASS_THRESHOLD:.0f}%")
st.progress(mastery / 100, text="Mastery")
st.markdown("**Learning path:** " + "  →  ".join(
    f"**🟢 {c}**" if c == concept else f"⚪ {c}"
    for c in curriculum.concepts(subject, chapter)))


# ── PDF coverage indicator (content-relevance based, not chapter tag) ──────────
rag_context, rag_sources = rag.context_for(subject, chapter, concept)
_pdf_total = store.count_chunks(db)
_pdf_hits = [h for h in rag_sources if h.get("kind") == "pdf"]
if _pdf_hits:
    top = _pdf_hits[0]
    st.success(f"📄 Grounded in your uploaded PDF — top match **{top['concept']}** "
               f"(score {top['score']}). Questions will use this content.")
elif _pdf_total:
    st.info(f"📄 {_pdf_total} PDF chunks indexed, but none strongly match "
            f"**{concept}** — using built-in notes + closest PDF text.")
else:
    st.warning("⚠️ No PDF ingested — questions use built-in notes. "
               "Upload one in the sidebar (📚) to ground them in it.")

# ── RAG retrieval preview ──────────────────────────────────────────────────────
with st.expander("🔎 RAG — retrieved Class 10 content (grounds the lesson & quiz)"):
    if rag_sources:
        for s in rag_sources:
            tag = "📄 PDF" if s.get("kind") == "pdf" else "📝 note"
            st.markdown(f"- {tag} **{s['concept']}** _(score {s['score']})_ — {s['text'][:240]}")
    else:
        st.write("No matching notes found; the tutor will use general CBSE knowledge.")


# Reset generated content when the selection changes.
sig = f"{learner.id}|{topic_key}|{language}|{mastery}|{num_q}|{mode}|{','.join(q_types)}"
if st.session_state.get("sig") != sig:
    st.session_state.sig = sig
    st.session_state.pop("resp", None)
    st.session_state.pop("result", None)
    st.session_state.pop("assessment", None)


exam_mode = mode == "Board exam paper"
btn_label = "✨ Generate lesson + exam paper" if exam_mode else "✨ Generate lesson + adaptive quiz"
if st.button(btn_label, type="primary", use_container_width=True):
    with st.spinner("Tutor is analysing and building the RAG-grounded content…"):
        st.session_state.resp = tutor.generate(
            subject=subject, chapter=chapter, concept=concept, mastery=mastery,
            language=language, rag_content=manual_rag or rag_context,
            num_questions=num_q, with_quiz=not exam_mode, q_types=q_types,
        )
        st.session_state.pop("result", None)
        st.session_state.pop("assessment", None)
        if exam_mode:
            st.session_state.assessment = get_examgen().generate_assessment(
                subject, chapter, concept,
                difficulty=_LEVEL_TO_DIFF.get(level_for(mastery), "Medium"),
                num_questions=num_q, rag_content=manual_rag or rag_context,
            ).model_dump()


resp = st.session_state.get("resp")
if resp:
    left, right = st.columns([3, 2])
    with left:
        st.subheader(f"📘 Lesson · {resp.lesson.concept}")
        if language in ("english", "both") and resp.lesson.english_explanation:
            st.markdown("**English**"); st.write(resp.lesson.english_explanation)
        if language in ("telugu", "both") and resp.lesson.telugu_explanation:
            st.markdown("**తెలుగు**"); st.write(resp.lesson.telugu_explanation)
        for title, items in [
            ("🌍 Real-life examples", resp.lesson.real_life_examples),
            ("✏️ Worked examples", resp.lesson.worked_examples),
            ("⚠️ Common mistakes", resp.lesson.common_mistakes),
            ("📝 Revision notes", resp.lesson.revision_notes),
        ]:
            if items:
                st.markdown(f"**{title}**")
                for e in items:
                    st.markdown(f"- {e}")

    with right:
        sa = resp.student_analysis
        st.subheader("🧠 Student analysis")
        st.write(f"**Level:** {sa.level}")
        if sa.weak_concepts:  st.write("**Weak:** " + ", ".join(sa.weak_concepts))
        if sa.strong_concepts: st.write("**Strong:** " + ", ".join(sa.strong_concepts))
        if resp.learning_path:
            st.subheader("🗺️ Learning path")
            st.table([{"#": p.priority, "concept": p.concept,
                       "time": p.estimated_time, "activity": p.activity}
                      for p in resp.learning_path])
        r = resp.recommendations
        st.subheader("🎯 Recommendations")
        if r.next_concepts: st.write("**Next concepts:** " + ", ".join(r.next_concepts))
        if r.next_lesson:   st.write(f"**Next lesson:** {r.next_lesson}")

    # ── Board exam paper (teammate-compatible schema) ──────────────────────────
    if "assessment" in st.session_state:
        a = st.session_state.assessment
        st.divider()
        st.subheader(f"🧾 Exam paper · {a['total_questions']} questions · "
                     f"{a['total_marks']} marks · {a['difficulty']}")
        for i, q in enumerate(a["questions"], 1):
            st.markdown(f"**Q{i}. ({q['marks']} marks · {q['difficulty']} · {q['type']}) "
                        f"{q['question_text']}**")
            with st.expander("Model answer & marking points"):
                if q.get("sample_answer"):
                    st.markdown(f"**Sample answer:** {q['sample_answer']}")
                if q.get("expected_points"):
                    st.markdown("**Expected points:**")
                    for p in q["expected_points"]:
                        st.markdown(f"- {p}")
        with st.expander("📦 Assessment JSON (matches exam_prep schema)"):
            st.json(a)
        st.download_button("⬇️ Download assessment.json",
                           data=__import__("json").dumps(a, indent=2, ensure_ascii=False),
                           file_name=f"assessment_{a['assessment_id'][:8]}.json",
                           mime="application/json")

    # ── Quiz ───────────────────────────────────────────────────────────────────
    if resp.quiz and "result" not in st.session_state:
        st.divider()
        st.subheader(f"📝 Adaptive quiz ({len(resp.quiz)} questions)")
        with st.form("quiz"):
            answers = {}
            for i, q in enumerate(resp.quiz):
                t = q.type.upper()
                st.markdown(f"**Q{i+1}. [{q.difficulty}/{q.type}] {q.question}**")
                if t == "MCQ" and q.options:
                    picked = st.radio("Choose one:", q.options, index=None, key=f"q_{i}",
                                      label_visibility="collapsed")
                    answers[i] = picked[0] if picked else ""
                elif t == "MSQ" and q.options:
                    picks = st.multiselect("Select all that apply:", q.options, key=f"q_{i}",
                                           label_visibility="collapsed")
                    answers[i] = ",".join(p[0] for p in picks)
                elif t == "LONG ANSWER":
                    answers[i] = st.text_area("Your answer:", key=f"q_{i}",
                                              label_visibility="collapsed")
                else:  # Short Answer / other
                    answers[i] = st.text_input("Your answer:", key=f"q_{i}",
                                               label_visibility="collapsed")
            if st.form_submit_button("✅ Submit quiz", use_container_width=True):
                graded = tutor.grade(resp.quiz, answers)
                decision = tutor.progress_decision(graded, subject, chapter, concept)
                new_m = update_mastery(mastery, graded["percentage"])
                store.record_attempt(db, learner.id, topic_key, level_for(mastery),
                                     graded["correct"], graded["scored"],
                                     graded["percentage"] / 100)
                store.set_mastery(db, learner.id, topic_key, new_m)
                st.session_state.result = {"graded": graded, "decision": decision,
                                           "old": mastery, "new": new_m}
                st.rerun()


# ── Result + score-gated progression ──────────────────────────────────────────
if "result" in st.session_state:
    res = st.session_state.result
    g, d = res["graded"], res["decision"]
    st.divider()
    st.subheader("📊 Result")
    st.metric("MCQ score", f"{g['correct']}/{g['scored']}", f"{g['percentage']:.0f}%")
    for i, r in enumerate(g["results"]):
        if r["is_correct"] is None:
            st.markdown(f"ℹ️ **Q{i+1}** ({r['type']}) — expected: **{r['correct_answer']}**. {r['explanation']}")
        else:
            icon = "✅" if r["is_correct"] else "❌"
            st.markdown(f"{icon} **Q{i+1}.** {r['question']}")
            if not r["is_correct"]:
                st.markdown(f"&nbsp;&nbsp;&nbsp;Correct: **{r['correct_answer']}** — {r['explanation']}")

    st.write(f"Mastery {res['old']} → **{res['new']}** "
             f"({level_for(res['old'])} → {level_for(res['new'])}).")

    if d["passed"]:
        st.success(f"✅ {d['message']}")
        if d["next_concept"]:
            if st.button(f"🚀 Advance to: {d['next_concept']}", use_container_width=True):
                st.session_state.concept_name = d["next_concept"]
                st.session_state.pop("resp", None)
                st.session_state.pop("result", None)
                st.rerun()
    else:
        st.error(f"🔁 {d['message']}")
        if d["review_topics"]:
            st.markdown("**Recommended review topics:** " + ", ".join(d["review_topics"]))
        if st.button("🔁 Re-attempt the quiz (new questions)", use_container_width=True):
            with st.spinner("Generating a fresh quiz…"):
                st.session_state.resp.quiz = tutor.make_quiz(
                    subject, chapter, concept, mastery, num_q, language)
            st.session_state.pop("result", None)
            st.rerun()


# ── History ────────────────────────────────────────────────────────────────────
hist = store.get_history(db, learner.id, topic_key)
if hist:
    st.divider()
    st.subheader("📈 Quiz history (from SQL)")
    st.table([{"time": a.created_at.strftime("%H:%M:%S"), "level": a.difficulty,
               "score": f"{a.correct}/{a.total}", "pct": f"{a.score*100:.0f}%"}
              for a in hist])

db.close()
