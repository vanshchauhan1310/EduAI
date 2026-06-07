from typing import Dict, List


QUESTION_TEMPLATES: Dict[str, List[str]] = {

    "definition": [
        "What is {concept}?",
        "Define {concept}.",
        "Write the definition of {concept}."
    ],

    "reasoning": [
        "Why does {concept} occur?",
        "Explain why {concept} takes place.",
        "What causes {concept}?"
    ],

    "explanation": [
        "Explain {concept} with an example.",
        "Describe {concept} in detail.",
        "Explain the process of {concept}."
    ],

    "comparison": [
        "Differentiate between {concept1} and {concept2}.",
        "Compare {concept1} and {concept2}.",
    ],

    "application": [
        "How is {concept} used in everyday life?",
        "Give one real-life application of {concept}.",
        "Explain the practical importance of {concept}."
    ],

    "equation": [
        "Write the balanced equation for {concept}.",
        "Represent {concept} using a balanced chemical equation."
    ],

    "case_based": [
        (
            "A student observes a phenomenon related to "
            "{concept}. Explain the observation."
        ),

        (
            "A real-life situation involves {concept}. "
            "Analyse and explain."
        )
    ]
}