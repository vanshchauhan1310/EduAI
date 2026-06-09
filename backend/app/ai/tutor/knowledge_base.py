# app/ai/tutor/knowledge_base.py
"""
Curated CBSE Class 10 concept notes (ported from prototype/knowledge_base.py).

Concise NCERT-style notes per concept — the seed corpus the RAG retriever indexes
so lessons/quizzes/chat stay grounded even before any PDF has been ingested.
Keys match the concept names in curriculum.CURRICULUM.
"""

NOTES = {
    # ── Physics: Electricity ──────────────────────────────────────────────────
    "Electric Current":
        "Electric current is the rate of flow of electric charge through a conductor. "
        "It is measured in amperes (A). I = Q/t, where Q is charge in coulombs and t is time in seconds. "
        "Conventional current flows from the positive to the negative terminal.",
    "Potential Difference":
        "Potential difference (voltage) between two points is the work done to move a unit charge "
        "from one point to the other. It is measured in volts (V): V = W/Q. A voltmeter connected in "
        "parallel measures potential difference.",
    "Resistance":
        "Resistance opposes the flow of current in a conductor and is measured in ohms (Ω). "
        "It depends on length, area of cross-section, material and temperature. R = ρL/A, where ρ is resistivity.",
    "Ohm's Law":
        "Ohm's Law states that the current through a conductor is directly proportional to the potential "
        "difference across it, provided temperature stays constant: V = IR. A graph of V versus I is a straight line.",
    "Resistors in Series":
        "In a series combination the same current flows through each resistor and the total resistance is the "
        "sum: R = R1 + R2 + R3. The total voltage is shared among the resistors.",
    "Resistors in Parallel":
        "In a parallel combination the voltage across each resistor is the same and 1/R = 1/R1 + 1/R2 + 1/R3. "
        "The combined resistance is less than the smallest individual resistance.",
    "Electric Power":
        "Electric power is the rate at which electrical energy is consumed: P = VI = I²R = V²/R, measured in watts (W). "
        "Commercial energy is measured in kilowatt-hours (kWh).",
    "Heating Effect of Current":
        "When current flows through a resistor, electrical energy converts to heat. Joule's law of heating: "
        "H = I²Rt. This effect is used in electric heaters, irons and bulbs.",

    # ── Physics: Light ────────────────────────────────────────────────────────
    "Reflection of Light":
        "Reflection is the bouncing back of light from a surface. The laws of reflection: the angle of incidence "
        "equals the angle of reflection, and the incident ray, reflected ray and normal lie in the same plane.",
    "Spherical Mirrors":
        "Spherical mirrors are concave or convex. Key terms: pole, centre of curvature, focus, focal length "
        "(f = R/2). Concave mirrors can form real or virtual images; convex mirrors always form virtual, diminished images.",
    "Mirror Formula":
        "The mirror formula relates object distance u, image distance v and focal length f: 1/v + 1/u = 1/f. "
        "Magnification m = -v/u = h'/h. Sign conventions follow the Cartesian system.",
    "Refraction of Light":
        "Refraction is the bending of light when it passes from one medium to another due to a change in speed. "
        "Light bends towards the normal entering a denser medium and away when entering a rarer medium.",
    "Snell's Law":
        "Snell's law of refraction: n1 sin(i) = n2 sin(r). The refractive index n = c/v = sin(i)/sin(r). "
        "It measures how much a medium slows down and bends light.",
    "Lenses":
        "A convex (converging) lens bends light to a focus; a concave (diverging) lens spreads light out. "
        "Images depend on object position relative to the focus and optical centre.",
    "Lens Formula":
        "The lens formula is 1/v - 1/u = 1/f, with magnification m = v/u. Convex lenses have positive focal length, "
        "concave lenses negative, by the sign convention.",
    "Power of a Lens":
        "Power of a lens is the reciprocal of its focal length in metres: P = 1/f, measured in dioptres (D). "
        "Convex lenses have positive power, concave lenses negative.",

    # ── Chemistry: Chemical Reactions and Equations ───────────────────────────
    "Chemical Equation":
        "A chemical equation represents a reaction using symbols and formulae of reactants and products. "
        "Reactants are written on the left, products on the right, separated by an arrow.",
    "Balancing Equations":
        "A balanced equation has equal numbers of each atom on both sides, satisfying the law of conservation of mass. "
        "Coefficients are adjusted; subscripts in formulae are never changed.",
    "Combination Reaction":
        "In a combination reaction two or more substances combine to form a single product, e.g. "
        "CaO + H2O → Ca(OH)2. Such reactions are often exothermic.",
    "Decomposition Reaction":
        "In a decomposition reaction a single compound breaks into two or more simpler substances, using heat "
        "(thermal), light (photolytic) or electricity (electrolytic), e.g. 2FeSO4 → Fe2O3 + SO2 + SO3.",
    "Displacement Reaction":
        "In a displacement reaction a more reactive element displaces a less reactive one from its compound, "
        "e.g. Fe + CuSO4 → FeSO4 + Cu. Reactivity is governed by the activity series.",
    "Oxidation and Reduction":
        "Oxidation is gain of oxygen or loss of hydrogen/electrons; reduction is the opposite. Together they form "
        "redox reactions. Corrosion and rancidity are everyday redox processes.",

    # ── Chemistry: Acids, Bases and Salts ─────────────────────────────────────
    "Properties of Acids":
        "Acids taste sour, turn blue litmus red, and release H+ ions in water. They react with metals to release "
        "hydrogen gas and with carbonates to release carbon dioxide.",
    "Properties of Bases":
        "Bases taste bitter, feel soapy, turn red litmus blue, and release OH- ions in water. Water-soluble bases "
        "are called alkalis.",
    "pH Scale":
        "The pH scale (0–14) measures acidity or alkalinity. pH < 7 is acidic, pH = 7 is neutral, pH > 7 is basic. "
        "It depends on H+ ion concentration and is important in daily life and agriculture.",
    "Neutralization":
        "A neutralization reaction between an acid and a base produces salt and water: "
        "acid + base → salt + water (e.g. HCl + NaOH → NaCl + H2O). It is generally exothermic.",
    "Salts":
        "Salts are ionic compounds formed from the neutralization of an acid and a base. Their pH depends on the "
        "strength of the parent acid and base; families share a common acid or base radical.",
    "Baking Soda":
        "Baking soda is sodium hydrogen carbonate (NaHCO3), a mild non-corrosive base. It is used in cooking, "
        "as an antacid, and in fire extinguishers; on heating it releases CO2.",
    "Washing Soda":
        "Washing soda is sodium carbonate decahydrate (Na2CO3·10H2O). It is used for cleaning, softening hard "
        "water, and in the manufacture of glass, soap and paper.",

    # ── Mathematics: Quadratic Equations ──────────────────────────────────────
    "Standard Form":
        "A quadratic equation in one variable has the standard form ax² + bx + c = 0, where a ≠ 0. "
        "Its solutions are the values of x that satisfy the equation, called roots.",
    "Factorization Method":
        "To solve by factorization, split the middle term so ax² + bx + c factors into two linear factors, then set "
        "each factor to zero. Example: x² + 5x + 6 = (x+2)(x+3) = 0.",
    "Completing the Square":
        "Completing the square rewrites ax² + bx + c = 0 as a(x + p)² = q, allowing direct solving by taking square "
        "roots. It is also used to derive the quadratic formula.",
    "Quadratic Formula":
        "The quadratic formula gives the roots of ax² + bx + c = 0 as x = (-b ± √(b² - 4ac)) / 2a. "
        "It works for every quadratic equation.",
    "Discriminant":
        "The discriminant is D = b² - 4ac. It determines the nature of the roots without solving the equation in full.",
    "Nature of Roots":
        "If D > 0 the roots are real and distinct; if D = 0 they are real and equal; if D < 0 there are no real roots "
        "(the roots are imaginary).",

    # ── Mathematics: Trigonometry ─────────────────────────────────────────────
    "Trigonometric Ratios":
        "For a right triangle, sin θ = opposite/hypotenuse, cos θ = adjacent/hypotenuse, tan θ = opposite/adjacent. "
        "cosec, sec and cot are their reciprocals.",
    "Trigonometric Ratios of Specific Angles":
        "Standard values are known for 0°, 30°, 45°, 60° and 90°. For example sin30° = 1/2, cos45° = 1/√2, "
        "tan60° = √3. These are used to evaluate expressions quickly.",
    "Trigonometric Identities":
        "The fundamental identities are sin²θ + cos²θ = 1, 1 + tan²θ = sec²θ, and 1 + cot²θ = cosec²θ. "
        "They are used to simplify and prove trigonometric expressions.",
    "Heights and Distances":
        "Trigonometry is applied to find heights and distances using angles of elevation and depression. "
        "A right triangle is formed and a suitable ratio (usually tan) relates the known and unknown sides.",
}
