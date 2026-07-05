from datetime import datetime, timezone
from pathlib import Path

from risklens.agent.evaluator import evaluate_coverage
from risklens.agent.memory import JsonMemoryStore
from risklens.agent.orchestrator import _append_limitations, run_agent
from risklens.agent.planner import create_plan
from risklens.agent.state import AgentRunState, IntelligencePlan, TaskStatus
from risklens.agent.verifier import verify_items
from risklens.models import EvidenceLevel, IntelligenceItem, SourceType


def make_item(
    item_id: str,
    title: str = "Banking AI regulation model risk signal",
    source: str = "Federal Reserve",
    source_type: SourceType = SourceType.regulatory,
    evidence_level: EvidenceLevel = EvidenceLevel.primary,
) -> IntelligenceItem:
    return IntelligenceItem(
        id=item_id,
        title=title,
        url=f"https://example.com/{item_id}",
        source=source,
        source_type=source_type,
        published_at=datetime.now(timezone.utc),
        summary=title,
        raw_text=title,
        risk_tags=["regulatory_risk"],
        evidence_level=evidence_level,
    )


def test_planner_generates_profile_specific_plan():
    financial = create_plan("financial_services")
    ai_strategy = create_plan("ai_technology_strategy")
    assert financial.required_topics != ai_strategy.required_topics
    assert "regulatory_fetcher_tool" in financial.required_tools
    assert "arxiv_fetcher_tool" in ai_strategy.required_tools
    assert financial.max_iterations == 3


def test_evaluator_detects_missing_topics():
    plan = create_plan("financial_services")
    evaluation = evaluate_coverage([make_item("1", title="Banking AI regulation")], plan)
    assert evaluation.missing_topics
    assert evaluation.should_continue


def test_evaluator_detects_source_concentration():
    plan = IntelligencePlan(
        profile="financial_services",
        required_topics=["regulatory_policy"],
        preferred_source_types=["regulatory"],
        required_tools=["regulatory_fetcher_tool"],
        min_items=3,
    )
    items = [make_item(str(i), source="Same Source") for i in range(4)]
    evaluation = evaluate_coverage(items, plan)
    assert evaluation.source_diversity_issues


def test_orchestrator_stops_at_max_iterations():
    state = run_agent("financial_services", mock=True, max_iterations=1, max_items=8)
    assert state.iteration_count <= 1
    assert state.status in {TaskStatus.SUCCESS, TaskStatus.PARTIAL_SUCCESS}


def test_memory_records_run(tmp_path):
    memory = JsonMemoryStore(tmp_path / "memory.json")
    state = AgentRunState(run_id="test-run", profile="financial_services", status=TaskStatus.SUCCESS)
    state.processed_items = [make_item("1")]
    memory.record_run(state, "2026-01-01T00:00:00Z", "2026-01-01T00:00:01Z")
    data = memory.load()
    assert data["runs"][0]["run_id"] == "test-run"
    assert data["items"]


def test_trace_file_created():
    state = run_agent("ai_technology_strategy", mock=True, max_iterations=1, max_items=8)
    trace_path = Path(state.final_report_paths["trace"])
    assert trace_path.exists()
    assert "coverage_score" in trace_path.read_text(encoding="utf-8")


def test_agent_run_mock_mode_generates_report():
    state = run_agent("fintech_web3_risk", mock=True, max_iterations=1, max_items=8)
    assert Path(state.final_report_paths["markdown_en"]).exists()
    assert Path(state.final_report_paths["markdown_zh"]).exists()
    assert state.status in {TaskStatus.SUCCESS, TaskStatus.PARTIAL_SUCCESS}


def test_verifier_rejects_missing_sources():
    plan = create_plan("financial_services")
    bad = make_item("bad")
    bad.source = ""
    issues = verify_items([bad], plan)
    assert issues


def test_report_contains_coverage_limitations_for_partial_success():
    report = _append_limitations("# Brief\n\n## Source List", ["Missing academic source evidence."], "en")
    assert "## Coverage Limitations" in report
    assert "Missing academic source evidence." in report