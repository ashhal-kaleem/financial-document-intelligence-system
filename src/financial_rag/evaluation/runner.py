"""Benchmark runner — tests multiple pipeline configs against the question set."""

from dataclasses import dataclass

from financial_rag.evaluation.judge import judge_faithfulness
from financial_rag.evaluation.metrics import EvalResult, EvalSummary
from financial_rag.evaluation.questions import BENCHMARK_QUESTIONS, EvalQuestion
from financial_rag.generation.groq import GroqGenerator
from financial_rag.pipeline.pipeline import RAGPipeline
from financial_rag.retrieval.factory import create_retriever


@dataclass
class BenchmarkConfig:
    model: str
    top_k: int
    score_threshold: float = 0.0
    judge_model: str = "llama-3.1-8b-instant"
    think: bool = False
    use_reranker: bool = False
    use_hybrid: bool = False


class BenchmarkRunner:
    """Runs the benchmark question set against multiple pipeline configurations.

    Args:
        store_path: Path to the FAISS index.
        configs: List of configurations to test.
        questions: Question set to evaluate (defaults to full BENCHMARK_QUESTIONS).
        verbose: Print progress to stdout.
    """

    def __init__(
        self,
        store_path: str = "data/processed/vector_store",
        configs: list[BenchmarkConfig] | None = None,
        questions: list[EvalQuestion] | None = None,
        verbose: bool = True,
    ) -> None:
        self._store_path = store_path
        self._configs = configs or self._default_configs()
        self._questions = questions or BENCHMARK_QUESTIONS
        self._verbose = verbose

    def run(self) -> list[EvalSummary]:
        """Run all configs against all questions. Returns one EvalSummary per config."""
        summaries: list[EvalSummary] = []

        for config in self._configs:
            if self._verbose:
                print(f"\n{'─'*60}")
                print(f"Config: model={config.model}  top_k={config.top_k}  threshold={config.score_threshold}  think={config.think}  reranker={config.use_reranker}  hybrid={config.use_hybrid}")
                print(f"{'─'*60}")

            summary = self._run_config(config)
            summaries.append(summary)

        return summaries

    def _run_config(self, config: BenchmarkConfig) -> EvalSummary:
        retriever = create_retriever(
            self._store_path, 
            score_threshold=config.score_threshold, 
            use_hybrid=config.use_hybrid,
            use_reranker=config.use_reranker,
        )
        generator = GroqGenerator(model=config.model)
        pipeline = RAGPipeline(retriever=retriever, generator=generator, top_k=config.top_k)

        summary = EvalSummary(
            model=config.model,
            top_k=config.top_k,
            score_threshold=config.score_threshold,
            think=config.think,
        )

        for q in self._questions:
            if self._verbose:
                print(f"  [{q.id}] {q.question[:60]}...")

            response = pipeline.ask(q.question, top_k=config.top_k)

            source_hit = False
            if q.expected_source:
                source_hit = any(
                    q.expected_source in c.lower() for c in response.citations
                )

            faithfulness, reasoning = judge_faithfulness(
                question=q.question,
                answer=response.answer,
                citations=response.citations,
                contexts=response.chunk_texts,
                judge_model=config.judge_model,
            )

            result = EvalResult(
                question_id=q.id,
                question=q.question,
                question_type=q.question_type,
                expected_source=q.expected_source,
                model=config.model,
                top_k=config.top_k,
                score_threshold=config.score_threshold,
                think=config.think,
                chunks_used=response.chunks_used,
                top_score=response.top_score or 0.0,
                retrieval_ms=response.retrieval_ms,
                source_hit=source_hit,
                answer=response.answer,
                generation_ms=response.generation_ms,
                is_grounded=response.is_grounded,
                faithfulness=faithfulness,
                judge_reasoning=reasoning,
            )
            summary.results.append(result)

            if self._verbose:
                tag = "✓" if faithfulness >= 2 else "✗"
                print(
                    f"    {tag} faith={faithfulness}/3  "
                    f"hit={'✓' if source_hit else '✗'}  "
                    f"total={response.total_ms:.0f}ms"
                )

        return summary

    @staticmethod
    def _default_configs() -> list[BenchmarkConfig]:
        return [
            BenchmarkConfig(model="llama-3.1-8b-instant",    top_k=5),
            BenchmarkConfig(model="llama-3.3-70b-versatile", top_k=5),
        ]

    @staticmethod
    def think_experiment_configs(
        models: list[str] | None = None,
        top_k: int = 5,
    ) -> list[BenchmarkConfig]:
        """Paired think=False / think=True configs for the same models.

        The think flag is kept for compatibility with existing BenchmarkConfig
        dataclass and eval reports.

        Args:
            models: Model tags to compare.
            top_k: Chunk count to use for all configs.
        """
        models = models or ["llama-3.1-8b-instant", "llama-3.3-70b-versatile"]
        return [
            BenchmarkConfig(model=m, top_k=top_k, think=think)
            for m in models
            for think in (False, True)
        ]
