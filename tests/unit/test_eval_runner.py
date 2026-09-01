"""Unit tests for the evaluation module.

Covers BenchmarkConfig, EvalResult, EvalSummary metrics calculations,
BenchmarkRunner (with mocked pipeline and judge), judge_faithfulness (mocked),
and CSV/JSON report serialization.
"""

import json
import csv
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from financial_rag.evaluation.metrics import EvalResult, EvalSummary
from financial_rag.evaluation.questions import EvalQuestion
from financial_rag.evaluation.runner import BenchmarkConfig, BenchmarkRunner


# ── Helpers ────────────────────────────────────────────────────────────────────

def _make_result(
    *,
    question_id: str = "q_01",
    question_type: str = "factual",
    expected_source: str | None = "interbank",
    source_hit: bool = True,
    is_grounded: bool = True,
    faithfulness: int = 3,
    think: bool = False,
    retrieval_ms: float = 100.0,
    generation_ms: float = 500.0,
    chunks_used: int = 3,
    top_score: float = 0.85,
) -> EvalResult:
    return EvalResult(
        question_id=question_id,
        question="¿Cuál fue la utilidad neta?",
        question_type=question_type,
        expected_source=expected_source,
        model="llama-3.1-8b-instant",
        top_k=5,
        score_threshold=0.0,
        think=think,
        chunks_used=chunks_used,
        top_score=top_score,
        retrieval_ms=retrieval_ms,
        source_hit=source_hit,
        answer="La utilidad fue S/ 1,200 millones [1].",
        generation_ms=generation_ms,
        is_grounded=is_grounded,
        faithfulness=faithfulness,
        judge_reasoning="Fully grounded.",
    )


def _make_summary(results: list[EvalResult], think: bool = False) -> EvalSummary:
    s = EvalSummary(model="llama-3.1-8b-instant", top_k=5, score_threshold=0.0, think=think)
    s.results = results
    return s


# ── BenchmarkConfig ────────────────────────────────────────────────────────────

class TestBenchmarkConfig:
    def test_think_defaults_to_false(self):
        cfg = BenchmarkConfig(model="llama-3.1-8b-instant", top_k=5)
        assert cfg.think is False

    def test_think_can_be_set_true(self):
        cfg = BenchmarkConfig(model="llama-3.3-70b-versatile", top_k=5, think=True)
        assert cfg.think is True

    def test_judge_model_default(self):
        cfg = BenchmarkConfig(model="llama-3.1-8b-instant", top_k=5)
        assert cfg.judge_model == "llama-3.1-8b-instant"

    def test_score_threshold_default(self):
        cfg = BenchmarkConfig(model="llama-3.1-8b-instant", top_k=5)
        assert cfg.score_threshold == 0.0

    def test_use_reranker_defaults_false(self):
        cfg = BenchmarkConfig(model="llama-3.1-8b-instant", top_k=5)
        assert cfg.use_reranker is False

    def test_use_hybrid_defaults_false(self):
        cfg = BenchmarkConfig(model="llama-3.1-8b-instant", top_k=5)
        assert cfg.use_hybrid is False


# ── EvalResult ─────────────────────────────────────────────────────────────────

class TestEvalResult:
    def test_faithfulness_pct_full_score(self):
        r = _make_result(faithfulness=3)
        assert r.faithfulness_pct == pytest.approx(1.0)

    def test_faithfulness_pct_zero(self):
        r = _make_result(faithfulness=0)
        assert r.faithfulness_pct == pytest.approx(0.0)

    def test_faithfulness_pct_partial(self):
        r = _make_result(faithfulness=2)
        assert r.faithfulness_pct == pytest.approx(2 / 3)

    def test_total_ms_is_sum(self):
        r = _make_result(retrieval_ms=100.0, generation_ms=400.0)
        assert r.total_ms == pytest.approx(500.0)

    def test_think_field_stored(self):
        r = _make_result(think=True)
        assert r.think is True

    def test_think_defaults_false(self):
        r = _make_result()
        assert r.think is False


# ── EvalSummary ────────────────────────────────────────────────────────────────

class TestEvalSummary:
    def test_n_returns_result_count(self):
        s = _make_summary([_make_result(), _make_result(question_id="q_02")])
        assert s.n == 2

    def test_n_zero_when_empty(self):
        s = _make_summary([])
        assert s.n == 0

    def test_avg_faithfulness_full(self):
        results = [_make_result(faithfulness=3), _make_result(faithfulness=3, question_id="q_02")]
        s = _make_summary(results)
        assert s.avg_faithfulness == pytest.approx(1.0)

    def test_avg_faithfulness_mixed(self):
        results = [
            _make_result(faithfulness=3, question_id="q_01"),
            _make_result(faithfulness=0, question_id="q_02"),
        ]
        s = _make_summary(results)
        assert s.avg_faithfulness == pytest.approx(0.5)

    def test_avg_faithfulness_zero_when_empty(self):
        assert _make_summary([]).avg_faithfulness == 0.0

    def test_source_hit_rate_all_hit(self):
        results = [
            _make_result(source_hit=True, expected_source="interbank", question_id="q_01"),
            _make_result(source_hit=True, expected_source="interbank", question_id="q_02"),
        ]
        assert _make_summary(results).source_hit_rate == pytest.approx(1.0)

    def test_source_hit_rate_none_hit(self):
        results = [
            _make_result(source_hit=False, expected_source="interbank", question_id="q_01"),
            _make_result(source_hit=False, expected_source="interbank", question_id="q_02"),
        ]
        assert _make_summary(results).source_hit_rate == pytest.approx(0.0)

    def test_source_hit_rate_excludes_none_expected_source(self):
        results = [
            _make_result(source_hit=True, expected_source="interbank", question_id="q_01"),
            _make_result(source_hit=False, expected_source=None, question_id="q_02"),  # out-of-scope
        ]
        # Only q_01 counts; q_02 has no expected_source
        assert _make_summary(results).source_hit_rate == pytest.approx(1.0)

    def test_grounded_rate_excludes_out_of_scope(self):
        results = [
            _make_result(question_type="factual",      is_grounded=True,  question_id="q_01"),
            _make_result(question_type="out_of_scope", is_grounded=False, question_id="q_02"),
        ]
        # Only factual question counts for grounded_rate
        assert _make_summary(results).grounded_rate == pytest.approx(1.0)

    def test_grounded_rate_zero_when_all_ungrounded(self):
        results = [
            _make_result(question_type="factual", is_grounded=False, question_id="q_01"),
        ]
        assert _make_summary(results).grounded_rate == pytest.approx(0.0)

    def test_out_of_scope_rejection_rate_full(self):
        results = [
            _make_result(question_type="out_of_scope", is_grounded=False, question_id="q_01"),
            _make_result(question_type="out_of_scope", is_grounded=False, question_id="q_02"),
        ]
        assert _make_summary(results).out_of_scope_rejection_rate == pytest.approx(1.0)

    def test_out_of_scope_rejection_rate_zero_when_grounded(self):
        results = [
            _make_result(question_type="out_of_scope", is_grounded=True, question_id="q_01"),
        ]
        assert _make_summary(results).out_of_scope_rejection_rate == pytest.approx(0.0)

    def test_out_of_scope_zero_when_no_oos_questions(self):
        results = [_make_result(question_type="factual")]
        assert _make_summary(results).out_of_scope_rejection_rate == 0.0

    def test_avg_retrieval_ms(self):
        results = [
            _make_result(retrieval_ms=100.0, question_id="q_01"),
            _make_result(retrieval_ms=200.0, question_id="q_02"),
        ]
        assert _make_summary(results).avg_retrieval_ms == pytest.approx(150.0)

    def test_avg_generation_ms(self):
        results = [
            _make_result(generation_ms=400.0, question_id="q_01"),
            _make_result(generation_ms=600.0, question_id="q_02"),
        ]
        assert _make_summary(results).avg_generation_ms == pytest.approx(500.0)

    def test_avg_total_ms_equals_sum_of_avgs(self):
        results = [
            _make_result(retrieval_ms=100.0, generation_ms=400.0, question_id="q_01"),
            _make_result(retrieval_ms=200.0, generation_ms=600.0, question_id="q_02"),
        ]
        s = _make_summary(results)
        assert s.avg_total_ms == pytest.approx(s.avg_retrieval_ms + s.avg_generation_ms)

    def test_think_field_stored_on_summary(self):
        s = _make_summary([], think=True)
        assert s.think is True


# ── BenchmarkRunner construction ──────────────────────────────────────────────

class TestBenchmarkRunnerInit:
    def test_accepts_custom_questions(self):
        q = EvalQuestion(
            id="t_01", question="¿Cuál fue la utilidad neta?",
            question_type="factual", expected_source="interbank",
        )
        runner = BenchmarkRunner(questions=[q], configs=[BenchmarkConfig(model="x", top_k=3)])
        assert runner._questions == [q]

    def test_accepts_custom_configs(self):
        cfgs = [BenchmarkConfig(model="llama-3.1-8b-instant", top_k=5, think=True)]
        runner = BenchmarkRunner(configs=cfgs, questions=[])
        assert runner._configs[0].think is True

    def test_default_configs_think_is_false(self):
        runner = BenchmarkRunner()
        assert all(not c.think for c in runner._configs)


# ── think_experiment_configs ───────────────────────────────────────────────────

class TestThinkExperimentConfigs:
    def test_returns_paired_configs(self):
        cfgs = BenchmarkRunner.think_experiment_configs(models=["llama-3.1-8b-instant"])
        assert len(cfgs) == 2
        assert cfgs[0].think is False
        assert cfgs[1].think is True
        assert cfgs[0].model == cfgs[1].model == "llama-3.1-8b-instant"

    def test_default_models_are_two(self):
        cfgs = BenchmarkRunner.think_experiment_configs()
        models = [c.model for c in cfgs]
        assert len(set(models)) == 2  # two distinct models
        assert len(cfgs) == 4         # 2 models × 2 think settings

    def test_all_think_values_present(self):
        cfgs = BenchmarkRunner.think_experiment_configs(models=["llama-3.3-70b-versatile"])
        think_values = {c.think for c in cfgs}
        assert think_values == {True, False}

    def test_top_k_propagated(self):
        cfgs = BenchmarkRunner.think_experiment_configs(models=["llama-3.1-8b-instant"], top_k=3)
        assert all(c.top_k == 3 for c in cfgs)


# ── BenchmarkRunner._run_config (mocked pipeline) ────────────────────────────

class TestBenchmarkRunnerRun:
    """Test _run_config with all external dependencies mocked."""

    def _run_mocked(self, think: bool = False) -> EvalSummary:
        from financial_rag.chunking.models import Chunk
        from financial_rag.embeddings.mock import MockEmbedder
        from financial_rag.generation.mock import MockGenerator
        from financial_rag.retrieval.retriever import VectorRetriever
        from financial_rag.retrieval.vector_store import FAISSVectorStore
        from financial_rag.pipeline.pipeline import RAGPipeline

        embedder = MockEmbedder(dim=16)
        store = FAISSVectorStore(dimension=16)
        chunk = Chunk(
            content="La utilidad neta fue S/ 1,200 millones.",
            source="interbank_2023.pdf",
            page=0, chunk_index=0, total_chunks=1, metadata={},
        )
        store.add_chunks([chunk], embedder)
        retriever = VectorRetriever(store=store, embedder=embedder, score_threshold=-1.0)
        pipeline = RAGPipeline(retriever=retriever, generator=MockGenerator(), top_k=3)

        question = EvalQuestion(
            id="q_01",
            question="¿Cuál fue la utilidad neta?",
            question_type="factual",
            expected_source="interbank",
        )
        config = BenchmarkConfig(model="llama-3.1-8b-instant", top_k=3, think=think)
        runner = BenchmarkRunner(
            configs=[config], questions=[question], verbose=False,
        )

        with (
            patch("financial_rag.evaluation.runner.create_retriever", return_value=retriever),
            patch("financial_rag.evaluation.runner.GroqGenerator", return_value=MockGenerator()),
            patch("financial_rag.evaluation.runner.judge_faithfulness", return_value=(3, "ok")),
        ):
            return runner._run_config(config)

    def test_returns_eval_summary(self):
        summary = self._run_mocked()
        assert isinstance(summary, EvalSummary)

    def test_summary_has_one_result_per_question(self):
        summary = self._run_mocked()
        assert summary.n == 1

    def test_result_captures_think_flag(self):
        summary_false = self._run_mocked(think=False)
        summary_true  = self._run_mocked(think=True)
        assert summary_false.results[0].think is False
        assert summary_true.results[0].think is True

    def test_faithfulness_from_judge_stored(self):
        summary = self._run_mocked()
        assert summary.results[0].faithfulness == 3

    def test_source_hit_detected(self):
        summary = self._run_mocked()
        # MockGenerator returns a grounded answer so citations should reference interbank
        assert isinstance(summary.results[0].source_hit, bool)


# ── judge_faithfulness (mocked Groq) ──────────────────────────────────────────

class TestJudgeFaithfulness:
    def _call_judge(self, groq_response: str) -> tuple[int, str]:
        from financial_rag.evaluation.judge import judge_faithfulness
        mock_client = MagicMock()
        mock_message = MagicMock()
        mock_message.content = groq_response
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response
        with patch("financial_rag.evaluation.judge.groq_sdk.Groq", return_value=mock_client):
            return judge_faithfulness(
                question="¿Cuál fue la utilidad neta?",
                answer="La utilidad fue S/ 1,200 millones.",
                citations=["interbank_2023.pdf, p.1"],
                contexts=["La utilidad neta fue S/ 1,200 millones."],
            )

    def test_returns_tuple(self):
        score, reasoning = self._call_judge("3")
        assert isinstance(score, int)
        assert isinstance(reasoning, str)

    def test_parses_plain_digit_3(self):
        score, _ = self._call_judge("3")
        assert score == 3

    def test_parses_plain_digit_0(self):
        score, _ = self._call_judge("0")
        assert score == 0

    def test_parses_verdict_suffix(self):
        score, _ = self._call_judge("After careful analysis, score: 2")
        assert score == 2

    def test_score_in_valid_range(self):
        for raw in ("0", "1", "2", "3"):
            score, _ = self._call_judge(raw)
            assert 0 <= score <= 3

    def test_judge_error_returns_fallback(self):
        from financial_rag.evaluation.judge import judge_faithfulness
        with patch(
            "financial_rag.evaluation.judge.groq_sdk.Groq",
            side_effect=RuntimeError("boom"),
        ):
            score, reasoning = judge_faithfulness(
                question="q", answer="a", citations=[], contexts=None,
            )
        assert score == 1
        assert "judge error" in reasoning


# ── save_csv ──────────────────────────────────────────────────────────────────

class TestSaveCSV:
    def _write_and_read(self, summaries, path):
        from financial_rag.evaluation.report import save_csv
        save_csv(summaries, path)
        with open(path, newline="") as f:
            return list(csv.DictReader(f))

    def test_creates_file(self, tmp_path):
        from financial_rag.evaluation.report import save_csv
        s = _make_summary([_make_result()])
        csv_path = tmp_path / "results.csv"
        save_csv([s], csv_path)
        assert csv_path.exists()

    def test_row_count_matches_results(self, tmp_path):
        s = _make_summary([_make_result(question_id="q_01"), _make_result(question_id="q_02")])
        rows = self._write_and_read([s], tmp_path / "r.csv")
        assert len(rows) == 2

    def test_think_column_present(self, tmp_path):
        s = _make_summary([_make_result(think=True)], think=True)
        rows = self._write_and_read([s], tmp_path / "r.csv")
        assert "think" in rows[0]

    def test_think_false_recorded(self, tmp_path):
        s = _make_summary([_make_result(think=False)])
        rows = self._write_and_read([s], tmp_path / "r.csv")
        assert rows[0]["think"] == "False"

    def test_think_true_recorded(self, tmp_path):
        s = _make_summary([_make_result(think=True)], think=True)
        rows = self._write_and_read([s], tmp_path / "r.csv")
        assert rows[0]["think"] == "True"

    def test_no_duplicate_rows_on_rerun(self, tmp_path):
        """Writing the same config twice must not produce duplicate rows."""
        from financial_rag.evaluation.report import save_csv
        s = _make_summary([_make_result()])
        csv_path = tmp_path / "r.csv"
        save_csv([s], csv_path)
        save_csv([s], csv_path)
        rows = self._write_and_read([s], csv_path)
        assert len(rows) == 1

    def test_think_true_and_false_both_kept(self, tmp_path):
        """think=True and think=False for the same model+question are distinct rows."""
        from financial_rag.evaluation.report import save_csv
        s_false = _make_summary([_make_result(think=False)], think=False)
        s_true  = _make_summary([_make_result(think=True)],  think=True)
        csv_path = tmp_path / "r.csv"
        save_csv([s_false], csv_path)
        save_csv([s_true], csv_path)
        with open(csv_path, newline="") as f:
            rows = list(csv.DictReader(f))
        assert len(rows) == 2
        think_values = {r["think"] for r in rows}
        assert think_values == {"True", "False"}


# ── save_json ─────────────────────────────────────────────────────────────────

class TestSaveJSON:
    def test_creates_file(self, tmp_path):
        from financial_rag.evaluation.report import save_json
        s = _make_summary([_make_result()])
        json_path = tmp_path / "results.json"
        save_json([s], json_path)
        assert json_path.exists()

    def test_json_contains_summaries_key(self, tmp_path):
        from financial_rag.evaluation.report import save_json
        s = _make_summary([_make_result()])
        json_path = tmp_path / "r.json"
        save_json([s], json_path)
        data = json.loads(json_path.read_text())
        assert "summaries" in data

    def test_think_field_in_json(self, tmp_path):
        from financial_rag.evaluation.report import save_json
        s = _make_summary([_make_result(think=True)], think=True)
        json_path = tmp_path / "r.json"
        save_json([s], json_path)
        data = json.loads(json_path.read_text())
        assert data["summaries"][0]["think"] is True

    def test_merges_with_existing_file(self, tmp_path):
        """Re-running a new config appends without removing the previous entry."""
        from financial_rag.evaluation.report import save_json
        s1 = _make_summary([_make_result()], think=False)
        s1.model = "llama-3.1-8b-instant"
        s2 = _make_summary([_make_result()], think=True)
        s2.model = "llama-3.1-8b-instant"
        json_path = tmp_path / "r.json"
        save_json([s1], json_path)
        save_json([s2], json_path)
        data = json.loads(json_path.read_text())
        assert len(data["summaries"]) == 2

    def test_avg_faithfulness_pct_present(self, tmp_path):
        from financial_rag.evaluation.report import save_json
        s = _make_summary([_make_result(faithfulness=3)])
        json_path = tmp_path / "r.json"
        save_json([s], json_path)
        data = json.loads(json_path.read_text())
        assert "avg_faithfulness_pct" in data["summaries"][0]
