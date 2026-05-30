"""
Concept Dependency Graph
========================
A Directed Acyclic Graph (DAG) of CBSE Class 10 PCM concepts.
An edge  A -> B  means "you should learn A before B".

Used to:
    * order a learning path so prerequisites come first
    * find what a student should learn next
    * show prerequisite chains
"""

from typing import Dict, List, Optional

import networkx as nx


# ── Concept prerequisite relationships (prerequisite, concept) ────────────────
DEFAULT_DEPENDENCIES = [
    # ───────── Physics: Electricity ─────────
    ("Current", "Voltage"),
    ("Voltage", "Resistance"),
    ("Resistance", "Ohms Law"),
    ("Ohms Law", "Series Circuit"),
    ("Ohms Law", "Parallel Circuit"),
    ("Series Circuit", "Electric Power"),
    ("Parallel Circuit", "Electric Power"),
    ("Electric Power", "Heating Effect"),

    # ───────── Physics: Magnetic Effects ─────────
    ("Current", "Magnetic Field"),
    ("Magnetic Field", "Solenoid"),
    ("Solenoid", "Electromagnet"),
    ("Electromagnet", "Electric Motor"),
    ("Magnetic Field", "Electromagnetic Induction"),
    ("Electromagnetic Induction", "Electric Generator"),

    # ───────── Physics: Light ─────────
    ("Reflection", "Laws of Reflection"),
    ("Laws of Reflection", "Spherical Mirrors"),
    ("Spherical Mirrors", "Mirror Formula"),
    ("Refraction", "Snells Law"),
    ("Snells Law", "Lenses"),
    ("Lenses", "Lens Formula"),
    ("Lens Formula", "Power of Lens"),

    # ───────── Chemistry: Chemical Reactions ─────────
    ("Chemical Equation", "Balancing Equations"),
    ("Balancing Equations", "Combination Reaction"),
    ("Balancing Equations", "Decomposition Reaction"),
    ("Balancing Equations", "Displacement Reaction"),
    ("Displacement Reaction", "Oxidation Reduction"),

    # ───────── Chemistry: Acids, Bases and Salts ─────────
    ("Properties of Acids", "pH Scale"),
    ("Properties of Bases", "pH Scale"),
    ("pH Scale", "Neutralization"),
    ("Neutralization", "Salts"),
    ("Salts", "Common Salt"),
    ("Salts", "Baking Soda"),
    ("Salts", "Washing Soda"),

    # ───────── Mathematics: Polynomials ─────────
    ("Polynomials", "Zeroes of Polynomial"),
    ("Zeroes of Polynomial", "Relationship Zeroes Coefficients"),
    ("Relationship Zeroes Coefficients", "Division Algorithm"),

    # ───────── Mathematics: Quadratic Equations ─────────
    ("Quadratic Equations", "Factorization Method"),
    ("Factorization Method", "Completing Square"),
    ("Completing Square", "Quadratic Formula"),
    ("Quadratic Formula", "Discriminant"),
    ("Discriminant", "Nature of Roots"),

    # ───────── Mathematics: Trigonometry ─────────
    ("Trigonometric Ratios", "Trigonometric Identities"),
    ("Trigonometric Identities", "Heights and Distances"),
]


class ConceptDependencyGraph:
    """Wraps a NetworkX DiGraph of concept prerequisites."""

    def __init__(self, dependencies: Optional[List] = None):
        self.graph = nx.DiGraph()
        for prereq, concept in (dependencies or DEFAULT_DEPENDENCIES):
            self.graph.add_edge(prereq, concept)

    # ── Queries ───────────────────────────────────────────────────────────────
    def get_prerequisites(self, concept: str) -> List[str]:
        """All concepts that must be learned before `concept` (in order)."""
        if concept not in self.graph:
            return []
        ancestors = nx.ancestors(self.graph, concept)
        sub = self.graph.subgraph(ancestors)
        return list(nx.topological_sort(sub))

    def get_next_concepts(self, concept: str) -> List[str]:
        """Concepts that directly depend on `concept`."""
        if concept not in self.graph:
            return []
        return list(self.graph.successors(concept))

    def get_learning_order(self, concepts: List[str]) -> List[str]:
        """
        Topologically sort the given concepts so prerequisites come first.
        Concepts not present in the graph are appended at the end.
        """
        in_graph = [c for c in concepts if c in self.graph]
        if not in_graph:
            return list(concepts)

        sub = self.graph.subgraph(nx.ancestors(self.graph, in_graph[0]).union(set(in_graph)))
        try:
            full_order = list(nx.topological_sort(self.graph))
        except nx.NetworkXUnfeasible:
            return list(concepts)

        wanted = set(concepts)
        ordered = [c for c in full_order if c in wanted]
        # Append any concepts not in the graph, preserving input order.
        extras = [c for c in concepts if c not in self.graph]
        return ordered + extras

    # ── Visualisation data ────────────────────────────────────────────────────
    def get_graph_data(self, filter_concepts: Optional[List[str]] = None) -> Dict:
        """Return nodes + edges (optionally filtered to a concept set)."""
        if filter_concepts:
            keep = set(filter_concepts)
            nodes = [n for n in self.graph.nodes if n in keep]
            edges = [
                {"from": u, "to": v}
                for u, v in self.graph.edges
                if u in keep and v in keep
            ]
        else:
            nodes = list(self.graph.nodes)
            edges = [{"from": u, "to": v} for u, v in self.graph.edges]

        return {"nodes": nodes, "edges": edges}
