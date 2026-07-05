import json
from datetime import datetime, timezone

from risklens.agent.config import get_agent_profile, load_agent_config
from risklens.agent.orchestrator import run_agent
from risklens.agent.tools import synthetic_items_for_tool
from risklens.agent.verifier import verify_report_text
from risklens.dashboard.file_matching import processed_files_for_profile, report_path_for_processed
from risklens.models import EvidenceLevel, IntelligenceItem, SourceType
from risklens.pipeline.severity import assign_severity_and_urgency


def make_item(source_type=SourceType.regulatory, evidence_level=EvidenceLevel.primary, tags=None):
    return IntelligenceItem(
        id="severity-test",
        title="Cybersecurity model risk regulatory signal",
        url="https://example.org/risklens-demo/severity-test",
        source="Synthetic Regulator",
        source_type=source_type,
        published_at=datetime.now(timezone.utc),
        summary="Cybersecurity and model risk control signal.",
        raw_text="Cybersecurity and model risk control signal.",
        risk_tags=tags or ["model_risk"],
        evidence_level=evidence_level,
    )


def test_verifier_accepts_english_source_list():
    assert verify_report_text("# Report\n\n## Source List\n- A") == []


def test_verifier_accepts_chinese_source_list():
    assert verify_report_text("# 简报\n\n## 来源列表\n- A") == []


def test_verifier_rejects_missing_source_section():
    issues = verify_report_text("# Report\n\n## Analysis\nNo sources here.")
    assert issues


def test_dashboard_matches_pipeline_agent_and_all(tmp_path):
    processed = tmp_path / "processed"
    reports = tmp_path / "reports"
    processed.mkdir()
    reports.mkdir()
    pipeline = processed / "2026-07-04_financial_services.json"
    agent = processed / "2026-07-04_financial_services_agent.json"
    pipeline.write_text("[]", encoding="utf-8")
    agent.write_text("[]", encoding="utf-8")
    assert processed_files_for_profile(processed, "financial_services", "Pipeline") == [pipeline]
    assert processed_files_for_profile(processed, "financial_services", "Agent") == [agent]
    assert set(processed_files_for_profile(processed, "financial_services", "All")) == {pipeline, agent}
    assert report_path_for_processed(reports, agent, "zh").name == "2026-07-04_financial_services_agent_zh.md"


def test_severity_high_for_primary_regulatory_model_risk():
    severity, urgency = assign_severity_and_urgency(make_item())
    assert severity == "high"
    assert urgency == "act_now"


def test_severity_medium_watch_for_academic_signal():
    severity, urgency = assign_severity_and_urgency(make_item(SourceType.academic, EvidenceLevel.secondary, ["model_risk"]))
    assert severity == "medium"
    assert urgency == "watch"


def test_config_loading_agent_plans():
    config = load_agent_config()
    profile = get_agent_profile("financial_services")
    assert "profiles" in config
    assert "required_topics" in profile
    assert "synthetic_items" in profile


def test_synthetic_mock_data_has_diverse_sources():
    items = []
    for tool_name in get_agent_profile("financial_services")["required_tools"]:
        items.extend(synthetic_items_for_tool("financial_services", tool_name))
    assert len(items) >= 8
    assert len({item.source for item in items}) >= 5
    assert all(str(item.url).startswith("https://example.org/risklens-demo/") for item in items)


def test_simulate_gap_creates_retry_decision_and_trace():
    state = run_agent("financial_services", mock=True, max_iterations=3, max_items=8, simulate_gap=True)
    assert state.retry_decisions
    trace = json.loads(open(state.final_report_paths["trace"], encoding="utf-8").read())
    assert trace["retry_decisions"]
    assert len(trace.get("coverage_history", [])) >= 2 or "could not improve" in " ".join(trace.get("retry_decisions", [])).lower()