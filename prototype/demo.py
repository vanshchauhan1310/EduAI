"""
CLI demo — Adaptive Tutor (CBSE Class 10 PCM, English + Telugu)
==============================================================
Generates the full tutor output for one concept and prints it.

Run from the prototype/ folder:
    python demo.py
    python demo.py Physics Electricity "Ohm's Law" 30 both
    (args: subject chapter concept mastery language)
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from learning_system import AdaptiveTutor, level_for, quiz_distribution
from llm_provider import using_real_llm


def hr(t):
    print("\n" + "=" * 70 + f"\n  {t}\n" + "=" * 70)


def main():
    a = sys.argv
    subject  = a[1] if len(a) > 1 else "Physics"
    chapter  = a[2] if len(a) > 2 else "Electricity"
    concept  = a[3] if len(a) > 3 else "Ohm's Law"
    mastery  = float(a[4]) if len(a) > 4 else 30
    language = a[5] if len(a) > 5 else "both"

    hr("Adaptive Tutor")
    print(f"{subject} · {chapter} · {concept}")
    print(f"Mastery {mastery}/100 ({level_for(mastery)}) · "
          f"LLM: {'HuggingFace' if using_real_llm() else 'offline'} · lang={language}")
    print(f"Adaptive quiz plan: "
          + ", ".join(f"{v} {k}" for k, v in quiz_distribution(mastery).items() if v))

    r = AdaptiveTutor().generate(subject, chapter, concept, mastery, language)

    hr("1. Student analysis")
    sa = r.student_analysis
    print("Level:", sa.level, "| weak:", sa.weak_concepts, "| strong:", sa.strong_concepts)

    hr("2. Learning path")
    for p in r.learning_path:
        print(f"  [{p.priority}] {p.concept} ({p.estimated_time}) — {p.activity}")

    hr("3. Lesson")
    print("[English]", (r.lesson.english_explanation or "")[:400])
    if r.lesson.telugu_explanation:
        print("\n[తెలుగు]", r.lesson.telugu_explanation[:400])
    if r.lesson.worked_examples:
        print("\nWorked examples:", *(f"\n  - {w}" for w in r.lesson.worked_examples))
    if r.lesson.common_mistakes:
        print("Common mistakes:", *(f"\n  - {m}" for m in r.lesson.common_mistakes))

    hr(f"4. Adaptive quiz ({len(r.quiz)} questions)")
    for i, q in enumerate(r.quiz, 1):
        print(f"  Q{i}. [{q.difficulty}/{q.type}] {q.question}")
        for o in q.options:
            print("      ", o)
        print("      answer:", q.answer)

    hr("5. Recommendations")
    print("Next concepts:", r.recommendations.next_concepts)
    print("Estimated new mastery:", r.recommendations.estimated_mastery_score)
    print("Next lesson:", r.recommendations.next_lesson)


if __name__ == "__main__":
    main()
