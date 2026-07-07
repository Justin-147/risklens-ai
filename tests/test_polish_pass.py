import json
from datetime import UTC, datetime
from pathlib import Path

from risklens.agent.orchestrator import run_agent
from risklens.agent.state import TaskStatus
from risklens.agent.tools import BaseTool, build_tool_registry
from risklens.llm.mock_provider import MockLLMProvider
from risklens.models import EvidenceLevel, IntelligenceItem, SourceType
from risklens.pipeline.build_context import build_report_context
from risklens.pipeline.rank_items import enforce_media_cap, rank_items
from risklens.pipeline.severity import enrich_items_with_severity


def item(
    item_id: str,
    source: str = "Synthetic Regulator",
    source_type: SourceType = SourceType.regulatory,
    tags=None,
) -> IntelligenceItem:
    return IntelligenceItem(
        id=item_id,
        title=f"Signal {item_id}",
        url=f"https://example.org/risklens-demo/{item_id}",
        source=source,
        source_type=source_type,
        published_at=datetime.now(UTC),
        summary="Model risk operational risk cybersecurity risk regulatory signal.",
        raw_text="Model risk operational risk cybersecurity risk regulatory signal.",
        authority_score=0.9 if source_type == SourceType.regulatory else 0.5,
        relevance_score=0.8,
        risk_or_opportunity_score=0.7,
        risk_tags=tags or ["model_risk"],
        evidence_level=EvidenceLevel.primary
        if source_type == SourceType.regulatory
        else EvidenceLevel.secondary,
    )


def test_simulate_gap_coverage_history_improves_and_records_gaps():
    state = run_agent(
        "financial_services", mock=True, max_iterations=3, max_items=8, simulate_gap=True
    )
    trace = json.loads(Path(state.final_report_paths["trace"]).read_text(encoding="utf-8"))
    history = trace["coverage_history"]
    assert history[0]["coverage_score"] < history[-1]["coverage_score"]
    assert trace["retry_decisions"]
    assert history[0]["gaps"]
    assert not history[-1]["gaps"] or history[-1]["retry_reason"]


def test_evidence_quality_score_is_assigned_and_serialized():
    enriched = enrich_items_with_severity([item("primary")])[0]
    assert enriched.evidence_quality_score > 0
    assert "evidence_quality_score" in enriched.to_json_dict()


def test_severity_influences_ranking():
    high = item("high", source_type=SourceType.regulatory, tags=["model_risk"])
    low = item(
        "low",
        source="Synthetic Industry Media",
        source_type=SourceType.media,
        tags=["opportunity_signal"],
    )
    high.relevance_score = low.relevance_score = 0.7
    high.authority_score = low.authority_score = 0.7
    enriched = enrich_items_with_severity([low, high])
    ranked = rank_items(enriched, limit=2)
    assert ranked[0].id == "high"


def test_report_monitoring_actions_vary_by_risk_tag():
    items = [
        enrich_items_with_severity([item("model", tags=["model_risk"])])[0],
        enrich_items_with_severity([item("cyber", tags=["cybersecurity_risk"])])[0],
        enrich_items_with_severity(
            [item("market", source_type=SourceType.market, tags=["market_risk"])]
        )[0],
    ]
    context = build_report_context("Financial Services", items)
    report = MockLLMProvider().generate_report(context)
    actions = [
        line for line in report.splitlines() if line.startswith("- Suggested monitoring action:")
    ]
    assert len(actions) >= 3
    assert len(set(actions)) > 1


def test_fetcher_failure_records_partial_success_without_crash(monkeypatch):
    class FailingTool(BaseTool):
        name = "rss_fetcher_tool"

        def _run(self, profile: str, parameters: dict):
            raise RuntimeError("synthetic fetch failure")

    registry = build_tool_registry(mock=True)
    registry["rss_fetcher_tool"] = FailingTool(mock=True)
    monkeypatch.setattr(
        "risklens.agent.orchestrator.build_tool_registry",
        lambda mock=False, simulate_gap=False: registry,
    )
    state = run_agent("ai_technology_strategy", mock=False, max_iterations=1, max_items=8)
    assert state.status == TaskStatus.PARTIAL_SUCCESS
    assert any("synthetic fetch failure" in error for error in state.errors)
    assert state.final_report_paths["trace"]


def test_source_diversity_cap_enforced():
    items = [item(str(idx), source="Dominant Source") for idx in range(5)]
    items += [item("alt1", source="Alt One"), item("alt2", source="Alt Two")]
    selected = enforce_media_cap(items, limit=5)
    assert sum(1 for selected_item in selected if selected_item.source == "Dominant Source") <= 1


def test_simulate_gap_uses_distinct_output_files():
    normal = run_agent("financial_services", mock=True, max_iterations=3, max_items=8)
    gap = run_agent(
        "financial_services", mock=True, max_iterations=3, max_items=8, simulate_gap=True
    )

    assert normal.final_report_paths["processed"] != gap.final_report_paths["processed"]
    assert normal.final_report_paths["trace"] != gap.final_report_paths["trace"]
    assert "_gap" in gap.final_report_paths["processed"]
    assert "_gap" in gap.final_report_paths["trace"]
