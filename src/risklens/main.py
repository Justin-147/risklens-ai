from __future__ import annotations

import argparse
import json
import os
from datetime import date, datetime, timezone
from pathlib import Path

from risklens.config import DATA_DIR, REPORTS_DIR, load_profiles, load_taxonomy
from risklens.llm.mock_provider import MockLLMProvider
from risklens.pipeline.collect import collect_items_from_fetchers
from risklens.models import EvidenceLevel, IntelligenceItem, SourceType
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


def mock_items(profile: str) -> list[IntelligenceItem]:
    today = datetime.now(timezone.utc)
    base = {
        "financial_services": [
            ("Federal Reserve highlights bank operational resilience expectations for AI vendors", "Federal Reserve", SourceType.regulatory, "Regulatory guidance emphasizes third-party controls, model governance, and operational resilience for banks adopting artificial intelligence.", "https://www.federalreserve.gov/"),
            ("BIS paper examines AI adoption in banking supervision and model risk", "BIS", SourceType.official, "Supervisors are testing AI-enabled monitoring while warning about explainability, concentration, and governance gaps.", "https://www.bis.org/"),
            ("Major bank expands enterprise AI controls for wealth management workflows", "Company Filing", SourceType.company, "A large financial institution describes AI governance, customer trust, and advisor productivity controls in public materials.", "https://example.com/company-ai-controls"),
        ],
        "fintech_web3_risk": [
            ("Stablecoin policy proposal raises liquidity and reserve transparency requirements", "SEC", SourceType.regulatory, "Policy signals point to tighter disclosure, operational resilience, and liquidity controls for stablecoin issuers.", "https://www.sec.gov/"),
            ("Crypto market structure report flags cybersecurity and reputational risk", "Industry Media", SourceType.media, "Market participants cite custody controls, fraud monitoring, and customer trust as core Web3 adoption constraints.", "https://example.com/web3-risk"),
            ("Government data note digital asset enforcement trends", "Treasury", SourceType.official, "Public enforcement signals focus on fraud, sanctions controls, and operational accountability across crypto intermediaries.", "https://home.treasury.gov/"),
        ],
        "ai_technology_strategy": [
            ("Model provider releases enterprise AI agent governance features", "Company Blog", SourceType.company, "New controls focus on agent permissions, audit logs, and policy enforcement for enterprise AI adoption.", "https://example.com/ai-agent-governance"),
            ("Academic benchmark study compares model reliability in multi-step workflows", "arXiv", SourceType.academic, "Research highlights hallucination, tool-use failures, and validation needs for AI agents in production.", "https://arxiv.org/"),
            ("Cloud infrastructure report shows demand for AI compute and resilience planning", "Industry Media", SourceType.media, "Infrastructure teams are balancing GPU capacity, cost controls, cyber resilience, and vendor concentration.", "https://example.com/ai-infra"),
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
            published_at=today,
            summary=summary,
            raw_text=summary,
            evidence_level=EvidenceLevel.primary if source_type in {SourceType.official, SourceType.regulatory, SourceType.company} else EvidenceLevel.secondary,
        )
        for idx, (title, source, source_type, summary, url) in enumerate(rows, start=1)
    ]


def run_report(profile: str, mock: bool = False) -> dict[str, Path]:
    profiles = load_profiles()
    if profile not in profiles:
        raise ValueError(f"Unknown profile '{profile}'. Choose one of: {', '.join(profiles)}")
    items = mock_items(profile) if mock else collect_items_from_fetchers(profile)
    raw_path = DATA_DIR / "raw" / f"{date.today().isoformat()}_{profile}.json"
    raw_path.write_text(json.dumps([item.to_json_dict() for item in items], indent=2), encoding="utf-8")

    taxonomy = load_taxonomy()
    processed = normalize_items(items)
    processed = deduplicate_items(processed)
    processed = score_sources(processed)
    processed = classify_items(processed, profiles[profile])
    processed = tag_risks(processed, taxonomy)
    processed = enrich_items_with_severity(processed)
    processed = rank_items(processed)

    processed_path = DATA_DIR / "processed" / f"{date.today().isoformat()}_{profile}.json"
    processed_path.write_text(json.dumps([item.to_json_dict() for item in processed], indent=2), encoding="utf-8")

    context = build_report_context(profiles[profile]["name"], processed)
    provider = MockLLMProvider()
    if os.getenv("RISKLENS_USE_LLM", "false").lower() == "true" and not mock:
        from risklens.llm.openai_provider import OpenAIProvider

        provider = OpenAIProvider()

    report_en = provider.generate_report(context, language="en")
    report_zh = provider.generate_report(context, language="zh")
    stem = f"{date.today().isoformat()}_{profile}"
    markdown_en_path = REPORTS_DIR / "markdown" / f"{stem}_en.md"
    markdown_zh_path = REPORTS_DIR / "markdown" / f"{stem}_zh.md"
    html_en_path = REPORTS_DIR / "html" / f"{stem}_en.html"
    html_zh_path = REPORTS_DIR / "html" / f"{stem}_zh.html"
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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="RiskLens AI intelligence pipeline")
    subparsers = parser.add_subparsers(dest="command", required=True)
    run = subparsers.add_parser("run", help="Generate a risk-aware intelligence report")
    run.add_argument("--profile", required=True, choices=sorted(load_profiles().keys()))
    run.add_argument("--mock", action="store_true", help="Run without external API keys")

    agent_run = subparsers.add_parser("agent-run", help="Run controlled agentic orchestration")
    agent_run.add_argument("--profile", required=True, choices=sorted(load_profiles().keys()))
    agent_run.add_argument("--mock", action="store_true", help="Run agent tools with deterministic mock data")
    agent_run.add_argument("--max-iterations", type=int, default=3)
    agent_run.add_argument("--max-items", type=int, default=8)
    agent_run.add_argument("--simulate-gap", action="store_true", help="Omit one evidence type in the first mock iteration to demonstrate retry behavior")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.command == "run":
        outputs = run_report(args.profile, mock=args.mock)
        for label, path in outputs.items():
            print(f"{label}: {path}")
    elif args.command == "agent-run":
        from risklens.agent.orchestrator import run_agent

        state = run_agent(args.profile, mock=args.mock, max_iterations=args.max_iterations, max_items=args.max_items, simulate_gap=args.simulate_gap)
        for label, path in state.final_report_paths.items():
            print(f"{label}: {path}")
        print(f"status: {state.status.value}")
        if state.evaluations:
            print(f"coverage_score: {state.evaluations[-1].coverage_score:.2f}")


if __name__ == "__main__":
    main()