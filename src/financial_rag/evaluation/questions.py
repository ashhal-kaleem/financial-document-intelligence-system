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
        question="How many employees did Interbank have at the close of 2024?",
        expected_source="interbank",
        question_type="factual",
    ),
    EvalQuestion(
        id="ib_02",
        question="What is Interbank's digital transformation strategy?",
        expected_source="interbank",
        question_type="strategic",
    ),
    EvalQuestion(
        id="ib_03",
        question="What sustainability or corporate social responsibility projects does Interbank have?",
        expected_source="interbank",
        question_type="strategic",
    ),
    EvalQuestion(
        id="ib_04",
        question="What is Interbank's dividend policy?",
        expected_source="interbank",
        question_type="factual",
    ),
    EvalQuestion(
        id="ib_05",
        question="What are the main risks facing Interbank?",
        expected_source="interbank",
        question_type="strategic",
    ),
    EvalQuestion(
        id="ib_06",
        question="Who is the CEO of Interbank?",
        expected_source="interbank",
        question_type="factual",
    ),
    # ── Scotiabank ─────────────────────────────────────────────────────────
    EvalQuestion(
        id="sb_01",
        question="What is Plin and how does Scotiabank Peru use it?",
        expected_source="scotiabank",
        question_type="factual",
    ),
    EvalQuestion(
        id="sb_02",
        question="What digital products did Scotiabank launch in 2024?",
        expected_source="scotiabank",
        question_type="factual",
    ),
    EvalQuestion(
        id="sb_03",
        question="How does Scotiabank manage credit risk?",
        expected_source="scotiabank",
        question_type="strategic",
    ),
    EvalQuestion(
        id="sb_04",
        question="What is Scotiabank Peru's financial inclusion strategy?",
        expected_source="scotiabank",
        question_type="strategic",
    ),
    # ── Out-of-scope (should return "no info") ─────────────────────────────
    EvalQuestion(
        id="oos_01",
        question="What was Peru's GDP in 2024?",
        expected_source=None,
        question_type="out_of_scope",
    ),
    EvalQuestion(
        id="oos_02",
        question="What is Bitcoin and how does it work?",
        expected_source=None,
        question_type="out_of_scope",
    ),
]
