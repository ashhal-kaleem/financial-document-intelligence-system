"""Data models for RAG evaluation results."""

from dataclasses import dataclass, field


@dataclass
class EvalResult:
    """Result of running one benchmark question through one pipeline config."""

    question_id: str
    question: str
    question_type: str
    expected_source: str | None

    # Pipeline config
    model: str
    top_k: int
    score_threshold: float

    # Retrieval
    chunks_used: int
    top_score: float
    retrieval_ms: float
    source_hit: bool          # expected_source found in retrieved chunks

    # Generation
    answer: str
    generation_ms: float
    is_grounded: bool

    # LLM-as-judge
    faithfulness: int         # 0-3 scale (3 = fully faithful)

    # Optional fields (defaults must come after all required fields)
    think: bool = False
    judge_reasoning: str = ""

    @property
    def total_ms(self) -> float:
        return self.retrieval_ms + self.generation_ms

    @property
    def faithfulness_pct(self) -> float:
        return self.faithfulness / 3.0


@dataclass
class EvalSummary:
    """Aggregated metrics for one pipeline configuration."""

    model: str
    top_k: int
    score_threshold: float
    think: bool = False
    results: list[EvalResult] = field(default_factory=list)

    @property
    def n(self) -> int:
        return len(self.results)

    @property
    def avg_retrieval_ms(self) -> float:
        return sum(r.retrieval_ms for r in self.results) / self.n if self.n else 0

    @property
    def avg_generation_ms(self) -> float:
        return sum(r.generation_ms for r in self.results) / self.n if self.n else 0

    @property
    def avg_total_ms(self) -> float:
        return self.avg_retrieval_ms + self.avg_generation_ms

    @property
    def avg_top_score(self) -> float:
        return sum(r.top_score for r in self.results) / self.n if self.n else 0

    @property
    def grounded_rate(self) -> float:
        grounded = [r for r in self.results if r.question_type != "out_of_scope"]
        return sum(r.is_grounded for r in grounded) / len(grounded) if grounded else 0

    @property
    def source_hit_rate(self) -> float:
        with_source = [r for r in self.results if r.expected_source is not None]
        return sum(r.source_hit for r in with_source) / len(with_source) if with_source else 0

    @property
    def avg_faithfulness(self) -> float:
        return sum(r.faithfulness_pct for r in self.results) / self.n if self.n else 0

    @property
    def out_of_scope_rejection_rate(self) -> float:
        """Fraction of out-of-scope questions correctly answered with 'no info'."""
        oos = [r for r in self.results if r.question_type == "out_of_scope"]
        return sum(not r.is_grounded for r in oos) / len(oos) if oos else 0
