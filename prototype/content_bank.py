"""
Offline demo content bank
=========================
Curated, sensible content so the prototype produces *real* output with no API
key. When HF_API_TOKEN is set, a real LLM replaces all of this for ANY topic.

Structure:
    TOPICS[topic_key] = {
        "explanations": {beginner/intermediate/advanced: text},
        "questions":    {easy/medium/hard: [ {question, options, answer, explanation} ]},
    }
"""

TOPICS = {
    "photosynthesis": {
        "explanations": {
            "beginner": (
                "Photosynthesis is how green plants make their own food. "
                "Using sunlight, water from the soil, and carbon dioxide from the air, "
                "the green parts of a leaf cook up sugar and release oxygen. "
                "Think of a leaf as a tiny solar-powered kitchen."
            ),
            "intermediate": (
                "Photosynthesis converts light energy into chemical energy. In the "
                "chloroplasts, chlorophyll absorbs sunlight and powers a reaction "
                "between carbon dioxide (CO2) and water (H2O) to produce glucose "
                "(C6H12O6) and oxygen (O2). Overall: 6CO2 + 6H2O -> C6H12O6 + 6O2."
            ),
            "advanced": (
                "Photosynthesis has two coupled stages. The light-dependent reactions "
                "in the thylakoid membranes split water (photolysis), driving electron "
                "transport to generate ATP and NADPH while releasing O2. The "
                "light-independent Calvin cycle in the stroma then fixes CO2 via RuBisCO, "
                "using ATP and NADPH to synthesise G3P and ultimately glucose."
            ),
        },
        "questions": {
            "easy": [
                {"question": "What gas do plants release during photosynthesis?",
                 "options": ["A) Carbon dioxide", "B) Oxygen", "C) Nitrogen", "D) Hydrogen"],
                 "answer": "B", "explanation": "Photosynthesis releases oxygen as a by-product."},
                {"question": "What do plants mainly use to make food?",
                 "options": ["A) Moonlight", "B) Sound", "C) Sunlight", "D) Soil only"],
                 "answer": "C", "explanation": "Sunlight provides the energy for photosynthesis."},
                {"question": "Where in the plant does most photosynthesis happen?",
                 "options": ["A) Roots", "B) Leaves", "C) Flowers", "D) Bark"],
                 "answer": "B", "explanation": "Leaves hold the most chlorophyll, so most photosynthesis happens there."},
            ],
            "medium": [
                {"question": "Which molecule absorbs light in a leaf?",
                 "options": ["A) Glucose", "B) Chlorophyll", "C) Water", "D) Oxygen"],
                 "answer": "B", "explanation": "Chlorophyll is the green pigment that absorbs light."},
                {"question": "What are the products of photosynthesis?",
                 "options": ["A) CO2 and water", "B) Glucose and oxygen",
                             "C) Nitrogen and ATP", "D) Salt and water"],
                 "answer": "B", "explanation": "Glucose and oxygen are produced from CO2 and water."},
                {"question": "Why do most leaves look green?",
                 "options": ["A) They absorb green light", "B) They reflect green light via chlorophyll",
                             "C) They store glucose", "D) They have no pigment"],
                 "answer": "B", "explanation": "Chlorophyll reflects green wavelengths, so leaves look green."},
            ],
            "hard": [
                {"question": "Where does the Calvin cycle take place?",
                 "options": ["A) Thylakoid membrane", "B) Mitochondria",
                             "C) Stroma of the chloroplast", "D) Cell wall"],
                 "answer": "C", "explanation": "The light-independent Calvin cycle occurs in the stroma."},
                {"question": "Which enzyme fixes CO2 in the Calvin cycle?",
                 "options": ["A) ATP synthase", "B) RuBisCO", "C) Amylase", "D) Catalase"],
                 "answer": "B", "explanation": "RuBisCO catalyses carbon fixation in the Calvin cycle."},
                {"question": "What does photolysis split during the light reactions?",
                 "options": ["A) Glucose", "B) Water", "C) Carbon dioxide", "D) ATP"],
                 "answer": "B", "explanation": "Photolysis splits water, releasing electrons, protons and O2."},
            ],
        },
    },
    "fractions": {
        "explanations": {
            "beginner": (
                "A fraction shows part of a whole. If you cut a pizza into 4 equal "
                "slices and eat 1, you ate 1/4. The bottom number (denominator) is how "
                "many equal parts there are; the top number (numerator) is how many you have."
            ),
            "intermediate": (
                "Fractions represent division. To add fractions you need a common "
                "denominator: 1/2 + 1/3 = 3/6 + 2/6 = 5/6. To multiply, multiply tops "
                "and bottoms: 2/3 x 3/4 = 6/12 = 1/2."
            ),
            "advanced": (
                "Fractions are rational numbers a/b with b != 0. Operations rely on the "
                "least common multiple for addition/subtraction and on reciprocal "
                "multiplication for division (a/b ÷ c/d = a/b x d/c). Every fraction has "
                "a unique simplest form found by dividing by the GCD of numerator and denominator."
            ),
        },
        "questions": {
            "easy": [
                {"question": "What is 1/2 of a pizza cut into 2 equal pieces?",
                 "options": ["A) 1 piece", "B) 2 pieces", "C) 0 pieces", "D) 4 pieces"],
                 "answer": "A", "explanation": "Half of 2 equal pieces is 1 piece."},
                {"question": "In the fraction 3/5, which is the denominator?",
                 "options": ["A) 3", "B) 5", "C) 8", "D) 15"],
                 "answer": "B", "explanation": "The denominator is the bottom number, 5."},
                {"question": "Which fraction is larger: 1/2 or 1/4?",
                 "options": ["A) 1/4", "B) 1/2", "C) They are equal", "D) Cannot tell"],
                 "answer": "B", "explanation": "Halves are bigger than quarters."},
            ],
            "medium": [
                {"question": "What is 1/4 + 1/4?",
                 "options": ["A) 1/8", "B) 2/8", "C) 1/2", "D) 1/16"],
                 "answer": "C", "explanation": "1/4 + 1/4 = 2/4 = 1/2."},
                {"question": "What is 2/3 x 3/4?",
                 "options": ["A) 1/2", "B) 5/7", "C) 6/7", "D) 1/4"],
                 "answer": "A", "explanation": "2/3 x 3/4 = 6/12 = 1/2."},
                {"question": "Simplify 4/8 to its simplest form.",
                 "options": ["A) 1/2", "B) 2/3", "C) 4/8 is simplest", "D) 1/4"],
                 "answer": "A", "explanation": "4/8 divides by 4 to give 1/2."},
            ],
            "hard": [
                {"question": "What is 5/6 - 1/3 in simplest form?",
                 "options": ["A) 4/3", "B) 1/2", "C) 4/6", "D) 1/6"],
                 "answer": "B", "explanation": "5/6 - 2/6 = 3/6 = 1/2."},
                {"question": "What is 3/4 ÷ 1/2?",
                 "options": ["A) 3/8", "B) 1 1/2", "C) 2/3", "D) 6/4 only"],
                 "answer": "B", "explanation": "3/4 x 2/1 = 6/4 = 1 1/2."},
                {"question": "What is 2/5 + 1/10 in simplest form?",
                 "options": ["A) 3/15", "B) 1/2", "C) 5/10", "D) 3/10"],
                 "answer": "B", "explanation": "4/10 + 1/10 = 5/10 = 1/2."},
            ],
        },
    },
}


def has_topic(topic: str) -> bool:
    return _key(topic) in TOPICS


def _key(topic: str) -> str:
    return topic.strip().lower()


def get_explanation(topic: str, level: str) -> str:
    entry = TOPICS.get(_key(topic))
    if not entry:
        return (
            f"[Demo content] '{topic}' is not in the offline content bank. "
            f"Set HF_API_TOKEN to generate a real {level}-level explanation for any topic. "
            f"For now, here is a {level} placeholder describing the key idea of {topic}."
        )
    return entry["explanations"].get(level, entry["explanations"]["beginner"])


def get_questions(topic: str, difficulty: str, n: int) -> list:
    entry = TOPICS.get(_key(topic))
    if not entry:
        # Generic placeholder questions for unknown topics (offline only).
        return [
            {
                "question": f"[Demo] Which statement best describes a key idea of {topic}?",
                "options": ["A) Option A", "B) Option B", "C) Option C", "D) Option D"],
                "answer": "A",
                "explanation": "Placeholder — set HF_API_TOKEN for real questions on any topic.",
            }
            for _ in range(n)
        ]
    pool = entry["questions"].get(difficulty, entry["questions"]["easy"])
    # Repeat the pool if more questions are requested than available.
    out = []
    i = 0
    while len(out) < n:
        out.append(pool[i % len(pool)])
        i += 1
    return out[:n]
