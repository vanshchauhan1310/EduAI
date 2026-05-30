"""
Adaptive Learning Recommendation Engine
========================================
Generates personalised learning paths based on concept mastery scores.

Rules
-----
mastery < 0.4  (Weak)   → Lesson + Examples + Practice + Quiz
mastery 0.4-0.7 (Medium) → Quick Review + Advanced Practice + Quiz
mastery ≥ 0.7  (Strong)  → Mark mastered, advance to next concept

The engine uses the dependency graph to order concepts correctly
(prerequisites are always learned before dependent concepts).
"""

from typing import Dict, List, Optional

from adaptive_engine.mastery import MasteryEngine, MasteryLevel
from adaptive_engine.dependency_graph import ConceptDependencyGraph


# ── Activity type constants ───────────────────────────────────────────────────
class ActivityType:
    LESSON     = "lesson"
    EXAMPLES   = "examples"
    PRACTICE   = "practice"
    QUIZ       = "quiz"
    REVIEW     = "review"
    ASSESSMENT = "chapter_assessment"


class RecommendationEngine:
    """
    Generates an adaptive, sequenced learning path for a student.
    """

    def __init__(self):
        self.mastery_engine   = MasteryEngine()
        self.dependency_graph = ConceptDependencyGraph()

    # ── Main entry point ──────────────────────────────────────────────────────
    def generate_learning_path(
        self,
        mastery_scores: Dict[str, float],
        subject:        str,
        chapter:        str,
    ) -> Dict:
        """
        Generate a full personalised learning path.

        Parameters
        ----------
        mastery_scores : {"Current": 0.9, "Voltage": 0.3, ...}
        subject        : "Physics"
        chapter        : "Electricity"

        Returns
        -------
        Complete learning path dict with summary + ordered activities.
        """
        # ── 1. Categorise concepts ────────────────────────────────────────────
        categorized      = self.mastery_engine.categorize_concepts(mastery_scores)
        priority_ordered = self.mastery_engine.get_priority_concepts(mastery_scores)

        # ── 2. Order weak + medium concepts using dependency graph ─────────────
        concepts_to_study = categorized["weak"] + categorized["medium"]
        ordered_concepts  = self.dependency_graph.get_learning_order(concepts_to_study)

        # ── 3. Build activity list ─────────────────────────────────────────────
        activities: List[Dict] = []
        total_time  = 0

        for concept in ordered_concepts:
            score   = mastery_scores.get(concept, 0.0)
            level   = self.mastery_engine.get_mastery_level(score)
            acts    = self._build_activities(concept, level, subject, chapter)
            activities.extend(acts)
            total_time += sum(a.get("estimated_minutes", 0) for a in acts)

        # ── 4. Add chapter assessment at the end ───────────────────────────────
        if concepts_to_study:
            activities.append({
                "step":              len(activities) + 1,
                "type":              ActivityType.ASSESSMENT,
                "concept":           "all",
                "title":             f"{chapter} – Final Chapter Test",
                "description":       "Test all concepts covered in this chapter.",
                "estimated_minutes": 30,
                "subject":           subject,
                "chapter":           chapter,
            })
            total_time += 30

        # Number the steps
        for i, act in enumerate(activities, 1):
            act["step"] = i

        return {
            "subject": subject,
            "chapter": chapter,
            "summary": {
                "weak_concepts":      categorized["weak"],
                "medium_concepts":    categorized["medium"],
                "strong_concepts":    categorized["strong"],
                "total_activities":   len(activities),
                "estimated_minutes":  total_time,
            },
            "priority_order": [c["concept"] for c in priority_ordered],
            "learning_path":  activities,
        }

    # ── Activity builder ──────────────────────────────────────────────────────
    def _build_activities(
        self,
        concept: str,
        level:   MasteryLevel,
        subject: str,
        chapter: str,
    ) -> List[Dict]:

        base = {"concept": concept, "subject": subject, "chapter": chapter}

        if level == MasteryLevel.WEAK:
            return [
                {**base, "type": ActivityType.LESSON,
                 "title": f"{concept} – Lesson",
                 "description": f"Learn {concept} from scratch with simple explanations and real-life analogies.",
                 "estimated_minutes": 15},

                {**base, "type": ActivityType.EXAMPLES,
                 "title": f"{concept} – Solved Examples",
                 "description": f"Study step-by-step solved problems on {concept}.",
                 "estimated_minutes": 10},

                {**base, "type": ActivityType.PRACTICE,
                 "title": f"{concept} – Practice (Easy)",
                 "description": f"Solve easy and medium practice questions on {concept}.",
                 "estimated_minutes": 20},

                {**base, "type": ActivityType.QUIZ,
                 "title": f"{concept} – Quiz",
                 "description": f"Take a short quiz to check your understanding of {concept}.",
                 "estimated_minutes": 10,
                 "difficulty": "easy"},
            ]

        elif level == MasteryLevel.MEDIUM:
            return [
                {**base, "type": ActivityType.REVIEW,
                 "title": f"{concept} – Quick Review",
                 "description": f"Quickly revise the key points of {concept}.",
                 "estimated_minutes": 5},

                {**base, "type": ActivityType.PRACTICE,
                 "title": f"{concept} – Advanced Practice",
                 "description": f"Solve medium and hard problems on {concept}.",
                 "estimated_minutes": 15},

                {**base, "type": ActivityType.QUIZ,
                 "title": f"{concept} – Quiz (Medium)",
                 "description": f"Test yourself with harder questions on {concept}.",
                 "estimated_minutes": 10,
                 "difficulty": "medium"},
            ]

        # Strong → no activities needed
        return []

    # ── Next activity helper ───────────────────────────────────────────────────
    def get_next_activity(
        self,
        current_concept:     str,
        mastery_score:       float,
        completed_titles:    List[str],
    ) -> Optional[Dict]:
        """
        Return the next pending activity for a concept, or suggest the next concept.
        """
        level       = self.mastery_engine.get_mastery_level(mastery_score)
        all_acts    = self._build_activities(current_concept, level, "", "")
        pending     = [a for a in all_acts if a["title"] not in completed_titles]

        if pending:
            return pending[0]

        # All activities done → suggest next concept in graph
        next_concepts = self.dependency_graph.get_next_concepts(current_concept)
        if next_concepts:
            return {
                "type":        "advance",
                "concept":     next_concepts[0],
                "title":       f"Move to {next_concepts[0]}",
                "description": f"You have completed {current_concept}! Start learning {next_concepts[0]}.",
            }

        return None
