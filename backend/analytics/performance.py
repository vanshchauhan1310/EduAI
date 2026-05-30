"""
Learning Analytics Engine
==========================
Tracks student performance, identifies learning trends, and
generates insights about weak/strong concepts per student.

Data sources
------------
- concept_mastery table  → per-concept mastery scores
- quiz_attempts table    → quiz history and scores
- analytics table        → aggregated running totals
"""

from datetime import datetime
from typing import Dict, List

from sqlalchemy.orm import Session

from database.models import (
    Student, ConceptMastery, QuizAttempt, Analytics
)
from adaptive_engine.mastery import MasteryEngine


class PerformanceAnalytics:
    """Computes and stores learning analytics for EduSakhi students."""

    def __init__(self):
        self.mastery_engine = MasteryEngine()

    # ── Student profile ───────────────────────────────────────────────────────
    def get_student_profile(self, student_id: int, db: Session) -> Dict:
        """
        Full student learning profile with mastery breakdown by subject.
        """
        student = db.query(Student).filter(Student.id == student_id).first()
        if not student:
            return {"error": "Student not found"}

        records = (
            db.query(ConceptMastery)
            .filter(ConceptMastery.student_id == student_id)
            .all()
        )

        # Group by subject
        by_subject: Dict[str, Dict] = {}
        for r in records:
            subj = r.subject
            if subj not in by_subject:
                by_subject[subj] = {}
            by_subject[subj][r.concept] = {
                "mastery":      round(r.mastery_score, 4),
                "level":        self.mastery_engine.get_level_label(r.mastery_score),
                "attempts":     r.attempts,
                "chapter":      r.chapter,
                "last_updated": r.last_updated.isoformat() if r.last_updated else None,
            }

        # Overall mastery
        all_scores = [r.mastery_score for r in records]
        avg_mastery = (
            round(sum(all_scores) / len(all_scores), 4) if all_scores else 0.0
        )

        categorized = self.mastery_engine.categorize_concepts(
            {r.concept: r.mastery_score for r in records}
        )

        return {
            "student_id":       student_id,
            "name":             student.name,
            "grade":            student.grade,
            "school":           student.school,
            "language":         student.language_preference,
            "overall_mastery":  avg_mastery,
            "subjects":         by_subject,
            "summary": {
                "strong_concepts": len(categorized["strong"]),
                "medium_concepts": len(categorized["medium"]),
                "weak_concepts":   len(categorized["weak"]),
                "total_tracked":   len(records),
            },
        }

    # ── Learning analytics ────────────────────────────────────────────────────
    def get_learning_analytics(self, student_id: int, db: Session) -> Dict:
        """
        Detailed analytics: weak/strong concepts, subject averages, quiz trend.
        """
        records = (
            db.query(ConceptMastery)
            .filter(ConceptMastery.student_id == student_id)
            .all()
        )

        attempts = (
            db.query(QuizAttempt)
            .filter(QuizAttempt.student_id == student_id)
            .order_by(QuizAttempt.attempted_at)
            .all()
        )

        # ── Weak concepts (need attention) ────────────────────────────────────
        weak = sorted(
            [
                {
                    "concept": r.concept,
                    "subject": r.subject,
                    "chapter": r.chapter,
                    "mastery": round(r.mastery_score, 4),
                    "level":   "weak",
                }
                for r in records
                if r.mastery_score < self.mastery_engine.WEAK_THRESHOLD
            ],
            key=lambda x: x["mastery"],
        )

        # ── Strong concepts ───────────────────────────────────────────────────
        strong = sorted(
            [
                {
                    "concept": r.concept,
                    "subject": r.subject,
                    "chapter": r.chapter,
                    "mastery": round(r.mastery_score, 4),
                    "level":   "strong",
                }
                for r in records
                if r.mastery_score >= self.mastery_engine.MEDIUM_THRESHOLD
            ],
            key=lambda x: x["mastery"],
            reverse=True,
        )

        # ── Subject-wise average mastery ──────────────────────────────────────
        subject_data: Dict[str, List[float]] = {}
        for r in records:
            subject_data.setdefault(r.subject, []).append(r.mastery_score)

        subject_mastery = {
            subj: round(sum(scores) / len(scores), 4)
            for subj, scores in subject_data.items()
        }

        # ── Quiz performance trend (last 10 attempts) ─────────────────────────
        quiz_trend = [
            {
                "date":       a.attempted_at.isoformat(),
                "concept":    a.concept,
                "subject":    a.subject,
                "score":      round(a.score, 4),
                "percentage": round(a.score * 100, 2),
                "difficulty": a.difficulty,
            }
            for a in attempts[-10:]
        ]

        return {
            "student_id":            student_id,
            "weak_concepts":         weak,
            "strong_concepts":       strong,
            "subject_mastery":       subject_mastery,
            "quiz_trend":            quiz_trend,
            "total_concepts_tracked": len(records),
            "total_quiz_attempts":   len(attempts),
        }

    # ── Mastery update with analytics sync ───────────────────────────────────
    def upsert_concept_mastery(
        self,
        student_id:    int,
        concept:       str,
        subject:       str,
        chapter:       str,
        new_mastery:   float,
        quiz_score:    float,
        time_spent:    int,
        db:            Session,
    ) -> Dict:
        """
        Update ConceptMastery and Analytics tables after a quiz attempt.

        Returns the improvement summary.
        """
        # ── ConceptMastery table ──────────────────────────────────────────────
        record = (
            db.query(ConceptMastery)
            .filter(
                ConceptMastery.student_id == student_id,
                ConceptMastery.concept    == concept,
                ConceptMastery.subject    == subject,
            )
            .first()
        )

        old_mastery = 0.0
        if record:
            old_mastery           = record.mastery_score
            record.mastery_score  = new_mastery
            record.attempts      += 1
            record.last_updated   = datetime.utcnow()
        else:
            record = ConceptMastery(
                student_id    = student_id,
                concept       = concept,
                subject       = subject,
                chapter       = chapter,
                mastery_score = new_mastery,
                attempts      = 1,
            )
            db.add(record)

        # ── Analytics table ───────────────────────────────────────────────────
        analytics = (
            db.query(Analytics)
            .filter(
                Analytics.student_id == student_id,
                Analytics.concept    == concept,
                Analytics.subject    == subject,
            )
            .first()
        )

        if analytics:
            analytics.mastery      = new_mastery
            analytics.score        = quiz_score
            analytics.attempts    += 1
            analytics.time_spent  += time_spent
            analytics.last_updated = datetime.utcnow()
        else:
            analytics = Analytics(
                student_id = student_id,
                concept    = concept,
                subject    = subject,
                mastery    = new_mastery,
                score      = quiz_score,
                attempts   = 1,
                time_spent = time_spent,
            )
            db.add(analytics)

        db.commit()

        return self.mastery_engine.get_improvement(old_mastery, new_mastery)
