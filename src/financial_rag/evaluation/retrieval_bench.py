"""Pure retrieval evaluation — Recall@k and MRR without any LLM.

Run with scripts/chunk_experiment.py to compare chunk configurations.
"""

import time
from dataclasses import dataclass, field

from financial_rag.evaluation.questions import BENCHMARK_QUESTIONS, EvalQuestion
from financial_rag.retrieval.retriever import VectorRetriever


@dataclass
class ChunkConfig:
    """Defines one chunking experiment."""
    label: str
    chunk_size: int
    chunk_overlap: int


@dataclass
class RetrievalHit:
    """Single-question result from a retrieval call."""
    question_id: str
    question_type: str
    expected_source: str | None
    hit: bool
    hit_rank: int | None   # 1-indexed position where source was found; None if missed
    top_score: float
    retrieval_ms: float


@dataclass
class RetrievalBenchResult:
    """Aggregated retrieval metrics for one chunk config × top_k combination."""
    config: ChunkConfig
    n_chunks: int
    top_k: int
    hits: list[RetrievalHit] = field(default_factory=list)

    @property
    def _in_scope(self) -> list[RetrievalHit]:
        return [h for h in self.hits if h.expected_source is not None]

    def recall_at_k(self) -> float:
        """Fraction of in-scope questions where the correct source appears in top_k."""
        iss = self._in_scope
        return sum(h.hit for h in iss) / len(iss) if iss else 0.0

    def mrr(self) -> float:
        """Mean Reciprocal Rank over in-scope questions.

        1.0 = source always ranked first.
        0.5 = source always ranked second.
        Higher is better.
        """
        iss = self._in_scope
        if not iss:
            return 0.0
        return sum(1.0 / h.hit_rank for h in iss if h.hit_rank) / len(iss)

    def avg_top_score(self) -> float:
        return sum(h.top_score for h in self.hits) / len(self.hits) if self.hits else 0.0

    def avg_retrieval_ms(self) -> float:
        return sum(h.retrieval_ms for h in self.hits) / len(self.hits) if self.hits else 0.0


def run_retrieval_bench(
    retriever: VectorRetriever,
    config: ChunkConfig,
    top_k: int = 5,
    questions: list[EvalQuestion] | None = None,
) -> RetrievalBenchResult:
    """Evaluate retrieval quality for a given retriever and chunk config.

    Args:
        retriever: Pre-built VectorRetriever wrapping a FAISS store.
        config: The chunk config used to build this retriever (for labeling).
        top_k: Number of chunks to retrieve per question.
        questions: Question set (defaults to full BENCHMARK_QUESTIONS).

    Returns:
        RetrievalBenchResult with Recall@k, MRR, and latency metrics.
    """
    questions = questions or BENCHMARK_QUESTIONS
    result = RetrievalBenchResult(config=config, n_chunks=retriever.store_size, top_k=top_k)

    for q in questions:
        t0 = time.perf_counter()
        retrieval = retriever.retrieve(q.question, top_k=top_k)
        elapsed_ms = (time.perf_counter() - t0) * 1000

        top_score = retrieval.top.score if retrieval.top else 0.0

        hit = False
        hit_rank: int | None = None

        if q.expected_source:
            for r in retrieval.results:
                if q.expected_source.lower() in r.chunk.source.lower():
                    hit = True
                    hit_rank = r.rank + 1  # convert 0-indexed to 1-indexed
                    break

        result.hits.append(RetrievalHit(
            question_id=q.id,
            question_type=q.question_type,
            expected_source=q.expected_source,
            hit=hit,
            hit_rank=hit_rank,
            top_score=top_score,
            retrieval_ms=elapsed_ms,
        ))

    return result


def print_bench_table(results: list[RetrievalBenchResult]) -> None:
    """Print a side-by-side comparison table of all bench results."""
    header = f"{'Config':<20} {'chunks':>6} {'top_k':>5} {'Recall@k':>8} {'MRR':>6} {'top_score':>9} {'ms/q':>7}"
    print("\n" + "─" * len(header))
    print(header)
    print("─" * len(header))

    best_mrr = max(r.mrr() for r in results)

    for r in results:
        mrr = r.mrr()
        marker = " ←" if mrr == best_mrr else ""
        print(
            f"{r.config.label:<20} {r.n_chunks:>6} {r.top_k:>5} "
            f"{r.recall_at_k():>8.1%} {mrr:>6.3f} "
            f"{r.avg_top_score():>9.4f} {r.avg_retrieval_ms():>7.1f}ms"
            f"{marker}"
        )

    print("─" * len(header))
