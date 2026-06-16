import pytest

from shared_core.evaljudge import (
    CitationJudge,
    DriftDetector,
    JudgeResult,
    RefusalJudge,
    SemanticMatchJudge,
    SimulatedEvaluator,
    get_judge,
    list_judges,
)


def test_registry_lists_builtin_judges():
    names = list_judges()
    assert {"semantic_match", "citation", "refusal"}.issubset(set(names))
    assert isinstance(get_judge("citation"), CitationJudge)


@pytest.mark.asyncio
async def test_semantic_match_judge_lexical_path():
    judge = SemanticMatchJudge(threshold=0.5)
    hit = await judge.evaluate(
        expected="the quick brown fox", actual="the quick brown fox"
    )
    miss = await judge.evaluate(
        expected="apples and oranges", actual="quantum mechanics"
    )
    assert hit.passed and hit.score > 0.9
    assert not miss.passed


@pytest.mark.asyncio
async def test_citation_judge():
    judge = CitationJudge(min_citations=1)
    with_cite = await judge.evaluate(expected=None, actual="The sky is blue [1].")
    without = await judge.evaluate(expected=None, actual="The sky is blue.")
    assert with_cite.passed
    assert not without.passed


@pytest.mark.asyncio
async def test_refusal_judge():
    judge = RefusalJudge()
    refused = await judge.evaluate(
        expected=None, actual="I cannot answer that based on the provided documents."
    )
    answered = await judge.evaluate(expected=None, actual="The capital is Paris.")
    assert refused.passed
    assert not answered.passed


def test_simulated_evaluator_deterministic():
    sim = SimulatedEvaluator()
    s1 = sim.score("hello world", "hello world")
    s2 = sim.score("hello world", "hello world")
    assert s1 == s2
    assert s1 > 0.9


def test_drift_detector_flags_regression():
    baseline = [JudgeResult(passed=True, score=1.0, judge="semantic_match")]
    current = [JudgeResult(passed=False, score=0.2, judge="semantic_match")]
    report = DriftDetector(regression_threshold=0.05).compare(baseline, current)
    assert report.is_regression
    assert report.pass_rate_delta < 0
    assert "semantic_match" in report.changed_tests
