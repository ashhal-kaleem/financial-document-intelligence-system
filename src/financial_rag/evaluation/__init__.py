"""Evaluation — RAG quality metrics and benchmark runner."""

from financial_rag.evaluation.metrics import EvalResult, EvalSummary
from financial_rag.evaluation.runner import BenchmarkConfig, BenchmarkRunner
from financial_rag.evaluation.questions import BENCHMARK_QUESTIONS, EvalQuestion

__all__ = [
    "EvalResult",
    "EvalSummary",
    "BenchmarkConfig",
    "BenchmarkRunner",
    "BENCHMARK_QUESTIONS",
    "EvalQuestion",
]
