"""
CBSE Class 10 PCM curriculum (modules)
=====================================
Subject -> Chapter -> ordered list of Concepts.

The order matters: a concept's prerequisites are the concepts BEFORE it in the
same chapter, and the "next" concept is the one AFTER it. This drives the
score-gated progression (advance to the next concept only after passing).
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
