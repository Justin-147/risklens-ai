from __future__ import annotations

import argparse
import json
import os
from datetime import UTC, datetime, time
from pathlib import Path

from risklens.config import PROJECT_ROOT, load_profiles, load_taxonomy
from risklens.llm.mock_provider import MockLLMProvider
from risklens.llm.provider import LLMProvider
from risklens.models import EvidenceLevel, IntelligenceItem, SourceType
from risklens.pipeline.build_context import build_report_context
from risklens.pipeline.classify import classify_items
from risklens.pipeline.collect import collect_items_from_fetchers
from risklens.pipeline.deduplicate import deduplicate_items
from risklens.pipeline.normalize import normalize_items
from risklens.pipeline.rank_items import rank_items
from risklens.pipeline.score_sources import score_sources
from risklens.pipeline.severity import enrich_items_with_severity
from risklens.pipeline.tag_risks import tag_risks
from risklens.writers.html_writer import write_html
from risklens.writers.markdown_writer import write_markdown


def parse_as_of(value: str | None) -> datetime | None:
    if value is None:
        return None
    text = value.strip()
    normalized = text[:-1] + "+00:00" if text.endswith("Z") else text
    try:
        if len(normalized) == 10:
            parsed = datetime.combine(datetime.fromisoformat(normalized).date(), time.min)
        else:
            parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            "--as-of must use YYYY-MM-DD, YYYY-MM-DDTHH:MM:SS, or ISO datetime with timezone."
        ) from exc
    if parsed.tzinfo is not None:
        return parsed.astimezone(UTC).replace(tzinfo=None)
    return parsed


def resolve_output_root(output_root: str | Path | None) -> Path:
    if output_root is None:
        return PROJECT_ROOT
    path = Path(output_root)
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    return path


def _generated_at(value: datetime | None) -> datetime:
    if value is None:
        return datetime.now(UTC).replace(tzinfo=None)
    if value.tzinfo is not None:
        return value.astimezone(UTC).replace(tzinfo=None)
    return value


def _aware_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def mock_items(
    profile: str,
    generated_at: datetime | None = None,
) -> list[IntelligenceItem]:
    published_at = _aware_utc(_generated_at(generated_at))
    base = {
        "financial_services": [
            (
                "Federal Reserve highlights bank operational resilience expectations "
                "for AI vendors",
                "Federal Reserve",
                SourceType.regulatory,
                "Regulatory guidance emphasizes third-party controls, model governance, and "
                "operational resilience for banks adopting artificial intelligence.",
                "https://www.federalreserve.gov/",
            ),
            (
                "BIS paper examines AI adoption in banking supervision and model risk",
                "BIS",
                SourceType.official,
                "Supervisors are testing AI-enabled monitoring while warning about explainability, "
                "concentration, and governance gaps.",
                "https://www.bis.org/",
            ),
            (
                "Major bank expands enterprise AI controls for wealth management workflows",
                "Company Filing",
                SourceType.company,
                "A large financial institution describes AI governance, customer trust, and "
                "advisor productivity controls in public materials.",
                "https://example.com/company-ai-controls",
            ),
        ],
        "fintech_web3_risk": [
            (
                "Stablecoin policy proposal raises liquidity and reserve transparency requirements",
                "SEC",
                SourceType.regulatory,
                "Policy signals point to tighter disclosure, operational resilience, and liquidity "
                "controls for stablecoin issuers.",
                "https://www.sec.gov/",
            ),
            (
                "Crypto market structure report flags cybersecurity and reputational risk",
                "Industry Media",
                SourceType.media,
                "Market participants cite custody controls, fraud monitoring, and customer trust "
                "as core Web3 adoption constraints.",
                "https://example.com/web3-risk",
            ),
            (
                "Government data note digital asset enforcement trends",
                "Treasury",
                SourceType.official,
                "Public enforcement signals focus on fraud, sanctions controls, and operational "
                "accountability across crypto intermediaries.",
                "https://home.treasury.gov/",
            ),
        ],
        "ai_technology_strategy": [
            (
                "Model provider releases enterprise AI agent governance features",
                "Company Blog",
                SourceType.company,
                "New controls focus on agent permissions, audit logs, and policy enforcement for "
                "enterprise AI adoption.",
                "https://example.com/ai-agent-governance",
            ),
            (
                "Academic benchmark study compares model reliability in multi-step workflows",
                "arXiv",
                SourceType.academic,
                "Research highlights hallucination, tool-use failures, and validation needs for "
                "AI agents in production.",
                "https://arxiv.org/",
            ),
            (
                "Cloud infrastructure report shows demand for AI compute and resilience planning",
                "Industry Media",
                SourceType.media,
                "Infrastructure teams are balancing GPU capacity, cost controls, cyber resilience, "
                "and vendor concentration.",
                "https://example.com/ai-infra",
            ),
        ],
    }
    rows = base.get(profile, base["financial_services"])
    return [
        IntelligenceItem(
            id=f"mock-{profile}-{idx}",
            title=title,
            url=url,
            source=source,
            source_type=source_type,
            published_at=published_at,
            summary=summary,
            raw_text=summary,
            evidence_level=(
                EvidenceLevel.primary
                if source_type in {SourceType.official, SourceType.regulatory, SourceType.company}
                else EvidenceLevel.secondary
            ),
        )
        for idx, (title, source, source_type, summary, url) in enumerate(rows, start=1)
    ]


def run_report(
    profile: str,
    mock: bool = False,
    generated_at: datetime | None = None,
    output_root: str | Path | None = None,
) -> dict[str, Path]:
    generated_at = _generated_at(generated_at)
    root = resolve_output_root(output_root)
    profiles = load_profiles()
    if profile not in profiles:
        raise ValueError(f"Unknown profile '{profile}'. Choose one of: {', '.join(profiles)}")
    items = (
        mock_items(profile, generated_at=generated_at)
        if mock
        else collect_items_from_fetchers(profile)
    )
    stem = f"{generated_at.date().isoformat()}_{profile}"
    raw_path = root / "data" / "raw" / f"{stem}.json"
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    raw_path.write_text(
        json.dumps([item.to_json_dict() for item in items], indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    taxonomy = load_taxonomy()
    processed = normalize_items(items)
    processed = deduplicate_items(processed)
    processed = score_sources(processed)
    processed = classify_items(processed, profiles[profile])
    processed = tag_risks(processed, taxonomy)
    processed = enrich_items_with_severity(processed)
    processed = rank_items(processed, as_of=generated_at)

    processed_path = root / "data" / "processed" / f"{stem}.json"
    processed_path.parent.mkdir(parents=True, exist_ok=True)
    processed_path.write_text(
        json.dumps([item.to_json_dict() for item in processed], indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    context = build_report_context(profiles[profile]["name"], processed, generated_at=generated_at)
    provider: LLMProvider = MockLLMProvider()
    if os.getenv("RISKLENS_USE_LLM", "false").lower() == "true" and not mock:
        from risklens.llm.openai_provider import OpenAIProvider

        provider = OpenAIProvider()

    report_en = provider.generate_report(context, language="en")
    report_zh = provider.generate_report(context, language="zh")
    markdown_en_path = root / "reports" / "markdown" / f"{stem}_en.md"
    markdown_zh_path = root / "reports" / "markdown" / f"{stem}_zh.md"
    html_en_path = root / "reports" / "html" / f"{stem}_en.html"
    html_zh_path = root / "reports" / "html" / f"{stem}_zh.html"
    write_markdown(markdown_en_path, report_en)
    write_markdown(markdown_zh_path, report_zh)
    write_html(html_en_path, report_en)
    write_html(html_zh_path, report_zh)
    return {
        "raw": raw_path,
        "processed": processed_path,
        "markdown_en": markdown_en_path,
        "markdown_zh": markdown_zh_path,
        "html_en": html_en_path,
        "html_zh": html_zh_path,
    }


def copy_agent_samples(state, profile: str, simulate_gap: bool) -> dict[str, Path]:
    sample_reports = PROJECT_ROOT / "examples" / "sample_reports"
    sample_traces = PROJECT_ROOT / "examples" / "sample_traces"
    sample_outputs = PROJECT_ROOT / "examples" / "sample_outputs"
    for directory in [sample_reports, sample_traces, sample_outputs]:
        directory.mkdir(parents=True, exist_ok=True)

    copied = {
        "markdown_en": sample_reports / f"{profile}_agent_en.md",
        "markdown_zh": sample_reports / f"{profile}_agent_zh.md",
        "processed": sample_outputs / f"{profile}_agent.json",
        "trace": sample_traces
        / (f"{profile}_gap_trace.json" if simulate_gap else f"{profile}_trace.json"),
    }
    Path(state.final_report_paths["markdown_en"]).read_text(encoding="utf-8")
    copied["markdown_en"].write_text(
        Path(state.final_report_paths["markdown_en"]).read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    copied["markdown_zh"].write_text(
        Path(state.final_report_paths["markdown_zh"]).read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    copied["processed"].write_text(
        Path(state.final_report_paths["processed"]).read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    trace = json.loads(Path(state.final_report_paths["trace"]).read_text(encoding="utf-8"))
    trace["final_report_paths"] = {
        "processed": str(copied["processed"].relative_to(PROJECT_ROOT)).replace("\\", "/"),
        "markdown_en": str(copied["markdown_en"].relative_to(PROJECT_ROOT)).replace("\\", "/"),
        "markdown_zh": str(copied["markdown_zh"].relative_to(PROJECT_ROOT)).replace("\\", "/"),
        "trace": str(copied["trace"].relative_to(PROJECT_ROOT)).replace("\\", "/"),
    }
    copied["trace"].write_text(
        json.dumps(trace, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return copied


def _add_runtime_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--as-of", type=parse_as_of, default=None)
    parser.add_argument("--output-root", default=None)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="RiskLens AI intelligence pipeline")
    subparsers = parser.add_subparsers(dest="command", required=True)
    run = subparsers.add_parser("run", help="Generate a risk-aware intelligence report")
    run.add_argument("--profile", required=True, choices=sorted(load_profiles().keys()))
    run.add_argument("--mock", action="store_true", help="Run without external API keys")
    _add_runtime_options(run)

    agent_run = subparsers.add_parser("agent-run", help="Run controlled agentic orchestration")
    agent_run.add_argument("--profile", required=True, choices=sorted(load_profiles().keys()))
    agent_run.add_argument(
        "--mock", action="store_true", help="Run agent tools with deterministic mock data"
    )
    agent_run.add_argument("--max-iterations", type=int, default=3)
    agent_run.add_argument("--max-items", type=int, default=8)
    agent_run.add_argument(
        "--simulate-gap",
        action="store_true",
        help="Omit one evidence type in the first mock iteration to demonstrate retry behavior",
    )
    agent_run.add_argument(
        "--copy-samples",
        action="store_true",
        help="Copy stable generated reports, trace, and processed output into examples/",
    )
    _add_runtime_options(agent_run)

    subparsers.add_parser("validate", help="Validate local RiskLens AI configuration")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.command == "run":
        outputs = run_report(
            args.profile,
            mock=args.mock,
            generated_at=args.as_of,
            output_root=args.output_root,
        )
        for label, path in outputs.items():
            print(f"{label}: {path}")
        return 0
    if args.command == "agent-run":
        from risklens.agent.orchestrator import run_agent

        state = run_agent(
            args.profile,
            mock=args.mock,
            max_iterations=args.max_iterations,
            max_items=args.max_items,
            simulate_gap=args.simulate_gap,
            generated_at=args.as_of,
            output_root=resolve_output_root(args.output_root),
        )
        for label, output_path in state.final_report_paths.items():
            print(f"{label}: {output_path}")
        print(f"status: {state.status.value}")
        if state.evaluations:
            print(f"coverage_score: {state.evaluations[-1].coverage_score:.2f}")
        if args.copy_samples:
            for label, sample_path in copy_agent_samples(
                state, args.profile, args.simulate_gap
            ).items():
                print(f"sample_{label}: {sample_path}")
        return 0
    if args.command == "validate":
        from risklens.validation.config_validator import validate_project

        result = validate_project()
        print(f"validation_errors: {len(result.errors)}")
        print(f"validation_warnings: {len(result.warnings)}")
        print(f"status: {result.status}")
        for error in result.errors:
            print(f"error: {error}")
        for warning in result.warnings:
            print(f"warning: {warning}")
        return 0 if not result.errors else 1
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
