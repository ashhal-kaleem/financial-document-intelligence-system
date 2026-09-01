"""Benchmark question set for RAG evaluation."""

from dataclasses import dataclass


@dataclass
class EvalQuestion:
    id: str
    question: str
    expected_source: str | None   # "interbank", "scotiabank", or None (out-of-scope)
    question_type: str            # "factual", "strategic", "out_of_scope"


BENCHMARK_QUESTIONS: list[EvalQuestion] = [
    # ── Interbank ──────────────────────────────────────────────────────────
    EvalQuestion(
        id="ib_01",
        question="¿Cuántos empleados tiene Interbank al cierre de 2024?",
        expected_source="interbank",
        question_type="factual",
    ),
    EvalQuestion(
        id="ib_02",
        question="¿Cuál es la estrategia de transformación digital de Interbank?",
        expected_source="interbank",
        question_type="strategic",
    ),
    EvalQuestion(
        id="ib_03",
        question="¿Qué proyectos de sostenibilidad o responsabilidad social tiene Interbank?",
        expected_source="interbank",
        question_type="strategic",
    ),
    EvalQuestion(
        id="ib_04",
        question="¿Cuál es la política de dividendos de Interbank?",
        expected_source="interbank",
        question_type="factual",
    ),
    EvalQuestion(
        id="ib_05",
        question="¿Cuáles son los principales riesgos que enfrenta Interbank?",
        expected_source="interbank",
        question_type="strategic",
    ),
    EvalQuestion(
        id="ib_06",
        question="¿Quién es el gerente general de Interbank?",
        expected_source="interbank",
        question_type="factual",
    ),
    # ── Scotiabank ─────────────────────────────────────────────────────────
    EvalQuestion(
        id="sb_01",
        question="¿Qué es Plin y cómo lo usa Scotiabank Perú?",
        expected_source="scotiabank",
        question_type="factual",
    ),
    EvalQuestion(
        id="sb_02",
        question="¿Qué productos digitales lanzó Scotiabank en 2024?",
        expected_source="scotiabank",
        question_type="factual",
    ),
    EvalQuestion(
        id="sb_03",
        question="¿Cómo gestiona Scotiabank el riesgo de crédito?",
        expected_source="scotiabank",
        question_type="strategic",
    ),
    EvalQuestion(
        id="sb_04",
        question="¿Cuál es la estrategia de inclusión financiera de Scotiabank Perú?",
        expected_source="scotiabank",
        question_type="strategic",
    ),
    # ── Out-of-scope (should return "no info") ─────────────────────────────
    EvalQuestion(
        id="oos_01",
        question="¿Cuál fue el PBI del Perú en 2024?",
        expected_source=None,
        question_type="out_of_scope",
    ),
    EvalQuestion(
        id="oos_02",
        question="¿Qué es el Bitcoin y cómo funciona?",
        expected_source=None,
        question_type="out_of_scope",
    ),
]
