"""
Mastery Update Engine
=====================
Tracks how well a student knows each concept on a 0.0–1.0 scale.

Mastery formula (Exponential Moving Average):
    new_mastery = 0.7 * old_mastery + 0.3 * quiz_score

Levels:
    Weak    : mastery < 0.4
    Medium  : 0.4 <= mastery < 0.7
    Strong  : mastery >= 0.7
"""

from enum import Enum
from typing import Dict, List


class MasteryLevel(str, Enum):
    WEAK   = "weak"
    MEDIUM = "medium"
    STRONG = "strong"


class MasteryEngine:
    """Updates and categorises concept mastery scores."""

    WEAK_THRESHOLD   = 0.4
    MEDIUM_THRESHOLD = 0.7

    OLD_WEIGHT = 0.7
    NEW_WEIGHT = 0.3

    # ── Core update formula ───────────────────────────────────────────────────
    def update_mastery(self, old_mastery: float, quiz_score: float) -> float:
        """
        Blend the old mastery with the latest quiz score.

        old_mastery : previous score (0.0–1.0)
        quiz_score  : latest quiz score (0.0–1.0)
        """
        new = self.OLD_WEIGHT * old_mastery + self.NEW_WEIGHT * quiz_score
        # Clamp to [0.0, 1.0]
        return round(min(1.0, max(0.0, new)), 4)

    # ── Level helpers ─────────────────────────────────────────────────────────
    def get_mastery_level(self, score: float) -> MasteryLevel:
        if score < self.WEAK_THRESHOLD:
            return MasteryLevel.WEAK
        if score < self.MEDIUM_THRESHOLD:
            return MasteryLevel.MEDIUM
        return MasteryLevel.STRONG

    def get_level_label(self, score: float) -> str:
        return self.get_mastery_level(score).value

    # ── Categorisation ────────────────────────────────────────────────────────
    def categorize_concepts(
        self, mastery_scores: Dict[str, float]
    ) -> Dict[str, List[str]]:
        """Split concepts into weak / medium / strong buckets."""
        result: Dict[str, List[str]] = {"weak": [], "medium": [], "strong": []}
        for concept, score in mastery_scores.items():
            result[self.get_mastery_level(score).value].append(concept)
        return result

    def get_priority_concepts(
        self, mastery_scores: Dict[str, float]
    ) -> List[Dict]:
        """
        Return concepts ordered by urgency (lowest mastery first).
        """
        ordered = sorted(
            mastery_scores.items(),
            key=lambda kv: kv[1],     # ascending by score
        )
        return [
            {
                "concept": concept,
                "mastery": round(score, 4),
                "level":   self.get_level_label(score),
                "gap":     round(1.0 - score, 4),
            }
            for concept, score in ordered
        ]

    # ── Improvement summary ───────────────────────────────────────────────────
    def get_improvement(self, old_mastery: float, new_mastery: float) -> Dict:
        delta = round(new_mastery - old_mastery, 4)
        return {
            "old_mastery":  round(old_mastery, 4),
            "new_mastery":  round(new_mastery, 4),
            "change":       delta,
            "improved":     delta > 0,
            "old_level":    self.get_level_label(old_mastery),
            "new_level":    self.get_level_label(new_mastery),
        }
