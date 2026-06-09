# app/ai/tutor/curriculum.py
"""
CBSE Class 10 PCM curriculum (ported from prototype/curriculum.py).

Subject -> Chapter -> ordered list of Concepts. Order matters: a concept's
prerequisites are the concepts BEFORE it in the same chapter, and "next" is the
concept AFTER it — this drives the score-gated progression in grading.py.
"""

from typing import List, Optional

CURRICULUM = {
    "Physics": {
        "Electricity": [
            "Electric Current", "Potential Difference", "Resistance", "Ohm's Law",
            "Resistors in Series", "Resistors in Parallel", "Electric Power",
            "Heating Effect of Current",
        ],
        "Light – Reflection and Refraction": [
            "Reflection of Light", "Spherical Mirrors", "Mirror Formula",
            "Refraction of Light", "Snell's Law", "Lenses", "Lens Formula",
            "Power of a Lens",
        ],
    },
    "Chemistry": {
        "Chemical Reactions and Equations": [
            "Chemical Equation", "Balancing Equations", "Combination Reaction",
            "Decomposition Reaction", "Displacement Reaction", "Oxidation and Reduction",
        ],
        "Acids, Bases and Salts": [
            "Properties of Acids", "Properties of Bases", "pH Scale",
            "Neutralization", "Salts", "Baking Soda", "Washing Soda",
        ],
    },
    "Mathematics": {
        "Quadratic Equations": [
            "Standard Form", "Factorization Method", "Completing the Square",
            "Quadratic Formula", "Discriminant", "Nature of Roots",
        ],
        "Introduction to Trigonometry": [
            "Trigonometric Ratios", "Trigonometric Ratios of Specific Angles",
            "Trigonometric Identities", "Heights and Distances",
        ],
    },
}

# Starting mastery for a concept the learner has never attempted (0-100 scale).
DEFAULT_MASTERY = 20.0


def subjects() -> List[str]:
    return list(CURRICULUM.keys())


def chapters(subject: str) -> List[str]:
    return list(CURRICULUM.get(subject, {}).keys())


def concepts(subject: str, chapter: str) -> List[str]:
    return list(CURRICULUM.get(subject, {}).get(chapter, []))


def next_concept(subject: str, chapter: str, concept: str) -> Optional[str]:
    seq = concepts(subject, chapter)
    if concept in seq:
        i = seq.index(concept)
        if i + 1 < len(seq):
            return seq[i + 1]
    return None


def prerequisites(subject: str, chapter: str, concept: str) -> List[str]:
    seq = concepts(subject, chapter)
    if concept in seq:
        return seq[: seq.index(concept)]
    return []


def find_chapter(subject: str, concept: str) -> Optional[str]:
    """Locate the chapter a concept belongs to within a subject — used to fill
    in `chapter` for a mastery row that doesn't exist yet."""
    for chapter, items in CURRICULUM.get(subject, {}).items():
        if concept in items:
            return chapter
    return None


def level_for(mastery: float) -> str:
    """Mastery bands (0-100)."""
    if mastery <= 40:
        return "Beginner"
    if mastery <= 70:
        return "Intermediate"
    return "Advanced"
