from __future__ import annotations

import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from risklens.agent.evaluator import evaluate_coverage
from risklens.agent.memory import JsonMemoryStore
from risklens.agent.planner import create_plan
from risklens.agent.state import AgentRunState, TaskStatus, ToolCall
from risklens.agent.tools import build_tool_registry
from risklens.agent.verifier import verify_items, verify_report_text
from risklens.config import PROJECT_ROOT, load_profiles, load_taxonomy
from risklens.llm.mock_provider import MockLLMProvider
from risklens.pipeline.build_context import build_report_context
from risklens.pipeline.classify import classify_items
from risklens.pipeline.deduplicate import deduplicate_items
from risklens.pipeline.normalize import normalize_items
from risklens.pipeline.rank_items import rank_items
from risklens.pipeline.score_sources import score_sources
from risklens.pipeline.severity import enrich_items_with_severity
from risklens.pipeline.tag_risks import tag_risks
from risklens.writers.html_writer import write_html
from risklens.writers.markdown_writer import write_markdown


def _generated_at(value: datetime | None) -> datetime:
    if value is None:
        return datetime.now(UTC).replace(tzinfo=None)
    if value.tzinfo is not None:
        return value.astimezone(UTC).replace(tzinfo=None)
    return value


def _isoformat_utc(value: datetime) -> str:
    return value.replace(tzinfo=UTC).isoformat()


def _run_date(value: datetime) -> str:
    return value.date().isoformat()


def _resolve_output_root(output_root: Path | None) -> Path:
    if output_root is None:
        return PROJECT_ROOT
    path = Path(output_root)
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    return path


def _process_items(items, profile: str, generated_at: datetime):
    profiles = load_profiles()
    taxonomy = load_taxonomy()
    processed = normalize_items(items)
    processed = deduplicate_items(processed)
    processed = score_sources(processed)
    processed = classify_items(processed, profiles[profile])
    processed = tag_risks(processed, taxonomy)
    processed = enrich_items_with_severity(processed)
    return rank_items(processed, as_of=generated_at)


def _evaluation_gaps(evaluation) -> list[str]:
    gaps: list[str] = []
    gaps.extend(evaluation.missing_topics)
    gaps.extend(evaluation.source_diversity_issues)
    gaps.extend(evaluation.evidence_quality_issues)
    return gaps


def _coverage_limitations(state: AgentRunState) -> list[str]:
    if not state.evaluations:
        return []
    limitations = _evaluation_gaps(state.evaluations[-1])
    limitations.extend(state.errors)
    return list(dict.fromkeys(limitations))


def _append_limitations(report: str, limitations: list[str], language: str) -> str:
    if not limitations:
        return report
    if language == "zh":
        lines = ["", "## 覆盖范围限制"]
        lines.extend(f"- {item}" for item in limitations)
        lines.append("- 本简报应视为阶段性情报视图，而非完整市场或监管评估。")
    else:
        lines = ["", "## Coverage Limitations"]
        lines.extend(f"- {item}" for item in limitations)
        lines.append(
            "- Treat this briefing as a partial intelligence view, not a comprehensive assessment."
        )
    return report + "\n" + "\n".join(lines)


def _save_trace(
    state: AgentRunState,
    started_at: str,
    completed_at: str,
    coverage_history: list[dict],
    generated_at: datetime,
    output_root: Path,
    run_suffix: str = "",
) -> Path:
    latest = state.evaluations[-1] if state.evaluations else None
    gaps = _evaluation_gaps(latest) if latest else []
    trace = {
        "run_id": state.run_id,
        "profile": state.profile,
        "status": state.status.value,
        "started_at": started_at,
        "completed_at": completed_at,
        "iteration_count": state.iteration_count,
        "plan": state.plan.model_dump(mode="json") if state.plan else None,
        "tools_called": [
            {
                "tool_name": result.tool_name,
                "status": result.status.value,
                "item_count": len(result.items),
                "errors": result.errors,
                "metadata": result.metadata,
            }
            for result in state.tool_results
        ],
        "coverage_score": latest.coverage_score if latest else 0.0,
        "coverage_history": coverage_history,
        "gaps": gaps,
        "retry_decisions": state.retry_decisions,
        "errors": state.errors,
        "final_report_paths": state.final_report_paths,
        "source_mix": dict(Counter(item.source for item in state.processed_items)),
        "topic_coverage": {
            "missing_topics": latest.missing_topics if latest else [],
            "required_topics": state.plan.required_topics if state.plan else [],
        },
    }
    trace_name = f"{_run_date(generated_at)}_{state.profile}{run_suffix}_trace.json"
    path = output_root / "reports" / "traces" / trace_name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(trace, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def run_agent(
    profile: str,
    mock: bool = False,
    max_iterations: int = 3,
    max_items: int = 8,
    simulate_gap: bool = False,
    generated_at: datetime | None = None,
    output_root: Path | None = None,
) -> AgentRunState:
    generated_at = _generated_at(generated_at)
    root = _resolve_output_root(output_root)
    started_at = _isoformat_utc(generated_at)
    completed_at = _isoformat_utc(generated_at)
    run_id = f"agent-{_run_date(generated_at)}-{uuid4().hex[:8]}"
    state = AgentRunState(run_id=run_id, profile=profile, status=TaskStatus.RUNNING)
    state.plan = create_plan(profile, max_iterations=max_iterations, max_items=max_items)
    run_suffix = "_gap" if simulate_gap else ""
    registry = build_tool_registry(mock=mock, simulate_gap=simulate_gap)
    tools_to_call = list(state.plan.required_tools)
    coverage_history: list[dict] = []

    for iteration in range(1, state.plan.max_iterations + 1):
        state.iteration_count = iteration
        tools_called_this_iteration: list[str] = []
        for tool_name in tools_to_call:
            tool = registry.get(tool_name)
            if not tool:
                state.errors.append(f"Unknown tool requested: {tool_name}")
                continue
            tools_called_this_iteration.append(tool_name)
            parameters = {"limit": max_items, "generated_at": generated_at}
            if simulate_gap and iteration == 1:
                parameters["omit_source_types"] = ["academic"]
            state.tool_calls.append(
                ToolCall(
                    tool_name=tool_name,
                    reason="Plan or coverage gap requested this tool.",
                    iteration=iteration,
                    parameters={
                        key: value for key, value in parameters.items() if key != "generated_at"
                    },
                )
            )
            result = tool.run(profile, parameters=parameters)
            state.tool_results.append(result)
            state.collected_items.extend(result.items)
            if result.errors:
                state.errors.extend(f"{tool_name}: {error}" for error in result.errors)

        if not state.collected_items:
            state.status = TaskStatus.FAILED
            coverage_history.append(
                {
                    "iteration": iteration,
                    "coverage_score": 0.0,
                    "gaps": ["No usable items collected."],
                    "tools_called_this_iteration": tools_called_this_iteration,
                    "retry_reason": "No usable items collected.",
                    "improved": False,
                }
            )
            break

        state.processed_items = _process_items(state.collected_items, profile, generated_at)
        evaluation = evaluate_coverage(state.processed_items, state.plan)
        state.evaluations.append(evaluation)
        gaps = _evaluation_gaps(evaluation)
        previous_score = coverage_history[-1]["coverage_score"] if coverage_history else None
        improved = previous_score is None or evaluation.coverage_score > previous_score
        retry_reason = ""
        if evaluation.should_continue:
            retry_reason = "; ".join(gaps) if gaps else "Coverage below target."
        coverage_history.append(
            {
                "iteration": iteration,
                "coverage_score": evaluation.coverage_score,
                "gaps": gaps,
                "tools_called_this_iteration": tools_called_this_iteration,
                "retry_reason": retry_reason,
                "improved": improved,
            }
        )

        if not evaluation.should_continue or iteration >= state.plan.max_iterations:
            if evaluation.should_continue and iteration >= state.plan.max_iterations:
                coverage_history[-1]["retry_reason"] = (
                    retry_reason or "Reached max iterations before all gaps were resolved."
                )
            break
        state.status = TaskStatus.RETRYING
        already_called = {call.tool_name for call in state.tool_calls}
        tools_to_call = [
            tool for tool in evaluation.recommended_next_tools if tool not in already_called
        ]
        if not tools_to_call:
            tools_to_call = evaluation.recommended_next_tools[:1]
        decision = (
            f"Iteration {iteration}: coverage score {evaluation.coverage_score:.2f}; "
            f"calling {', '.join(tools_to_call)} to address gaps: {retry_reason}"
        )
        state.retry_decisions.append(decision)
        coverage_history[-1]["retry_reason"] = decision

    if state.status != TaskStatus.FAILED:
        if not state.processed_items:
            state.status = TaskStatus.FAILED
        else:
            verification_issues = verify_items(state.processed_items, state.plan)
            state.errors.extend(verification_issues)
            latest = state.evaluations[-1] if state.evaluations else None
            if (
                latest
                and latest.coverage_score >= 0.80
                and not verification_issues
                and not state.errors
            ):
                state.status = TaskStatus.SUCCESS
            elif latest and latest.coverage_score >= 0.80 and state.errors:
                state.status = TaskStatus.PARTIAL_SUCCESS
            else:
                state.status = TaskStatus.PARTIAL_SUCCESS

            context = build_report_context(
                load_profiles()[profile]["name"],
                state.processed_items,
                generated_at=generated_at,
            )
            context["agent_status"] = state.status.value
            context["coverage_score"] = (
                state.evaluations[-1].coverage_score if state.evaluations else 0.0
            )
            limitations = (
                _coverage_limitations(state) if state.status == TaskStatus.PARTIAL_SUCCESS else []
            )
            provider = MockLLMProvider()
            report_en = _append_limitations(
                provider.generate_report(context, language="en"),
                limitations,
                "en",
            )
            report_zh = _append_limitations(
                provider.generate_report(context, language="zh"),
                limitations,
                "zh",
            )
            report_issues = verify_report_text(report_en) + verify_report_text(report_zh)
            if report_issues:
                state.errors.extend(report_issues)
                state.status = TaskStatus.PARTIAL_SUCCESS

            stem = f"{_run_date(generated_at)}_{profile}_agent{run_suffix}"
            raw_path = root / "data" / "raw" / f"{stem}.json"
            processed_path = root / "data" / "processed" / f"{stem}.json"
            markdown_en = root / "reports" / "markdown" / f"{stem}_en.md"
            markdown_zh = root / "reports" / "markdown" / f"{stem}_zh.md"
            html_en = root / "reports" / "html" / f"{stem}_en.html"
            html_zh = root / "reports" / "html" / f"{stem}_zh.html"
            raw_path.parent.mkdir(parents=True, exist_ok=True)
            processed_path.parent.mkdir(parents=True, exist_ok=True)
            raw_path.write_text(
                json.dumps(
                    [item.to_json_dict() for item in state.collected_items],
                    indent=2,
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            processed_path.write_text(
                json.dumps(
                    [item.to_json_dict() for item in state.processed_items],
                    indent=2,
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            write_markdown(markdown_en, report_en)
            write_markdown(markdown_zh, report_zh)
            write_html(html_en, report_en)
            write_html(html_zh, report_zh)
            state.final_report_paths = {
                "raw": str(raw_path),
                "processed": str(processed_path),
                "markdown_en": str(markdown_en),
                "markdown_zh": str(markdown_zh),
                "html_en": str(html_en),
                "html_zh": str(html_zh),
            }

    trace_path = _save_trace(
        state,
        started_at,
        completed_at,
        coverage_history,
        generated_at,
        root,
        run_suffix=run_suffix,
    )
    state.final_report_paths["trace"] = str(trace_path)
    JsonMemoryStore(root / "data" / "memory" / "memory.json").record_run(
        state,
        started_at,
        completed_at,
    )
    return state
