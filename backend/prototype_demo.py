"""
EduSakhi — Prototype Demo
=========================
A no-frills walkthrough of the whole product journey for ONE demo student,
using the real engines (with built-in fallbacks, so it runs without an LLM
token or any uploaded PDFs).

Run from the backend/ folder:
    python prototype_demo.py

It demonstrates, in order:
  1. Create a student
  2. Generate a diagnostic test (placeholder questions w/o LLM)
  3. Evaluate the test  -> per-concept mastery
  4. Show the concept dependency ordering (NetworkX)
  5. Generate an adaptive learning path
  6. Simulate a quiz result -> update mastery (0.7*old + 0.3*new)
  7. Learning analytics (weak/strong concepts)
  8. Governance: mark attendance for the same student
"""

import os
import sys

# Make `backend/` importable when run directly.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.db import SessionLocal, create_tables
from database.models import Student
from adaptive_engine.diagnostic import DiagnosticEngine
from adaptive_engine.dependency_graph import ConceptDependencyGraph
from adaptive_engine.recommendation import RecommendationEngine
from adaptive_engine.mastery import MasteryEngine
from analytics.performance import PerformanceAnalytics
from governance.schemas import AttendanceMark
from governance import attendance_service


def hr(title):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def main():
    create_tables()
    db = SessionLocal()

    SUBJECT = "Physics"
    CHAPTER = "Electricity"
    CONCEPTS = ["Current", "Voltage", "Resistance", "Ohms Law", "Electric Power"]

    # ── 1. Create a student ───────────────────────────────────────────────────
    hr("1. New student joins EduSakhi")
    student = Student(name="Lakshmi", age=15, grade="10",
                      school="Govt High School, Demo", language_preference="both")
    db.add(student)
    db.commit()
    db.refresh(student)
    print(f"Created student: id={student.id}, name={student.name}, grade={student.grade}")

    # ── 2. Diagnostic test ────────────────────────────────────────────────────
    hr("2. Generate a diagnostic test")
    diag = DiagnosticEngine()
    test = diag.generate_diagnostic_test(
        subject=SUBJECT, chapter=CHAPTER, concepts=CONCEPTS,
        questions_per_concept=2, llm_client=None,   # no LLM -> placeholder
    )
    print(f"Generated {test['total_questions']} questions "
          f"across {len(CONCEPTS)} concepts (LLM off -> placeholders).")
    print("Example question:", test["questions"][0]["question"])

    # ── 3. Evaluate the test (simulate the student's answers) ─────────────────
    hr("3. Student submits answers -> per-concept mastery")
    # Simulate: strong on Current/Voltage, weak on Resistance/Ohms Law/Power.
    answers = {}
    for q in test["questions"]:
        qno = str(q["question_no"])
        if q["concept"] in ("Current", "Voltage"):
            answers[qno] = q["answer"]            # correct
        else:
            answers[qno] = "Z"                     # wrong
    result = diag.evaluate_test(answers, test["questions"])
    print(f"Score: {result['correct_answers']}/{result['total_questions']} "
          f"({result['overall_percentage']}%)")
    print("Mastery per concept:")
    for c, m in result["mastery_scores"].items():
        print(f"   - {c:<16} {m}")

    mastery_scores = result["mastery_scores"]

    # ── 4. Concept dependency ordering ────────────────────────────────────────
    hr("4. Concept dependency graph (learn prerequisites first)")
    graph = ConceptDependencyGraph()
    order = graph.get_learning_order(CONCEPTS)
    print("Correct learning order:", " -> ".join(order))
    print("Prerequisites of 'Ohms Law':", graph.get_prerequisites("Ohms Law"))

    # ── 5. Adaptive learning path ─────────────────────────────────────────────
    hr("5. Personalised adaptive learning path")
    rec = RecommendationEngine()
    path = rec.generate_learning_path(mastery_scores, SUBJECT, CHAPTER)
    s = path["summary"]
    print(f"Weak: {s['weak_concepts']}")
    print(f"Medium: {s['medium_concepts']}")
    print(f"Strong (skip): {s['strong_concepts']}")
    print(f"Total activities: {s['total_activities']}, "
          f"est. {s['estimated_minutes']} min")
    print("First 5 steps:")
    for act in path["learning_path"][:5]:
        print(f"   {act['step']}. [{act['type']}] {act['title']} "
              f"({act.get('estimated_minutes', 0)}m)")

    # ── 6. Student does a quiz on 'Resistance' -> update mastery ──────────────
    hr("6. Quiz on 'Resistance' -> mastery update (0.7*old + 0.3*new)")
    engine = MasteryEngine()
    analytics = PerformanceAnalytics()
    old = mastery_scores["Resistance"]
    quiz_score = 0.8     # she studied and scored 80%
    new = engine.update_mastery(old, quiz_score)
    improvement = analytics.upsert_concept_mastery(
        student_id=student.id, concept="Resistance", subject=SUBJECT,
        chapter=CHAPTER, new_mastery=new, quiz_score=quiz_score,
        time_spent=300, db=db,
    )
    # Also persist the other diagnostic masteries so analytics has data.
    for c, m in mastery_scores.items():
        if c != "Resistance":
            analytics.upsert_concept_mastery(
                student_id=student.id, concept=c, subject=SUBJECT,
                chapter=CHAPTER, new_mastery=m, quiz_score=m,
                time_spent=0, db=db,
            )
    print(f"Resistance mastery: {improvement['old_mastery']} "
          f"({improvement['old_level']}) -> {improvement['new_mastery']} "
          f"({improvement['new_level']})  change={improvement['change']:+}")

    # ── 7. Learning analytics ─────────────────────────────────────────────────
    hr("7. Learning analytics dashboard")
    la = analytics.get_learning_analytics(student.id, db)
    print("Weak concepts:", [w["concept"] for w in la["weak_concepts"]])
    print("Strong concepts:", [w["concept"] for w in la["strong_concepts"]])
    print("Subject mastery:", la["subject_mastery"])

    # ── 8. Governance: mark attendance ────────────────────────────────────────
    hr("8. Governance layer — teacher marks attendance")
    attendance_service.mark_attendance(
        AttendanceMark(student_id=student.id, school_id=1,
                       date="2026-05-30", status="present"),
        marked_by=1, db=db,
    )
    summary = attendance_service.get_student_summary(student.id, db)
    print(f"Attendance: {summary['present']}/{summary['total_days']} days "
          f"present ({summary['attendance_percentage']}%)")

    db.close()
    hr("Prototype complete — this is the journey we are building")
    print("Next: add HF_API_TOKEN + upload NCERT PDFs to turn the placeholder")
    print("tutor/quizzes into real bilingual AI content.")


if __name__ == "__main__":
    main()
