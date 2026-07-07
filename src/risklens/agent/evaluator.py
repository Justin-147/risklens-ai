from __future__ import annotations

from collections import Counter

from risklens.agent.state import CoverageEvaluation, IntelligencePlan
from risklens.models import EvidenceLevel, IntelligenceItem, SourceType

TOPIC_KEYWORDS = {
    "banking_ai": ["bank", "banking", "artificial intelligence", "ai"],
    "wealth_management": ["wealth", "advisor", "client assets"],
    "regulatory_policy": ["regulation", "policy", "supervision", "compliance"],
    "operational_resilience": ["operational", "resilience", "third-party", "vendor"],
    "model_risk": ["model", "validation", "governance", "hallucination"],
    "digital_transformation": ["digital", "transformation", "automation"],
    "stablecoins": ["stablecoin", "reserve"],
    "crypto_market_structure": ["crypto", "market structure", "digital asset"],
    "regulation": ["regulation", "policy", "enforcement"],
    "cybersecurity": ["cyber", "security", "breach", "fraud"],
    "operational_risk": ["operational", "controls", "resilience"],
    "liquidity_risk": ["liquidity", "reserve", "funding"],
    "reputational_risk": ["trust", "customer", "reputation"],
    "model_providers": ["model provider", "provider", "model"],
    "ai_agents": ["agent", "agents", "tool"],
    "enterprise_ai": ["enterprise", "adoption", "workflow"],
    "ai_infrastructure": ["infrastructure", "compute", "gpu", "cloud"],
    "model_governance": ["governance", "audit", "policy"],
    "ai_safety": ["safety", "alignment", "guardrail"],
    "technology_risk": ["technology", "platform", "dependency", "outage"],
    "earthquake_monitoring": ["earthquake", "seismic"],
    "natural_hazard_risk": ["hazard", "risk"],
    "scientific_risk": ["scientific", "research"],
    "early_warning": ["warning", "alert"],
    "research_signals": ["research", "study"],
}


def _covered_topics(items: list[IntelligenceItem], topics: list[str]) -> set[str]:
    covered: set[str] = set()
    corpus = "\n".join(
        f"{item.title} {item.summary} {item.raw_text} {' '.join(item.risk_tags)}".lower()
        for item in items
    )
    for topic in topics:
        terms = TOPIC_KEYWORDS.get(topic, [topic.replace("_", " ")])
        if any(term.lower() in corpus for term in terms):
            covered.add(topic)
    return covered


def _recommend_tools(missing_topics: list[str], evidence_issues: list[str]) -> list[str]:
    recommendations: list[str] = []
    text = " ".join(missing_topics + evidence_issues).lower()
    if any(term in text for term in ["regulatory", "regulation", "policy", "compliance"]):
        recommendations.append("regulatory_fetcher_tool")
    if any(term in text for term in ["academic", "model", "research", "safety"]):
        recommendations.append("arxiv_fetcher_tool")
    if any(term in text for term in ["market", "liquidity", "stablecoin", "crypto"]):
        recommendations.append("market_fetcher_tool")
    if any(term in text for term in ["company", "provider", "enterprise", "wealth"]):
        recommendations.append("rss_fetcher_tool")
    if any(term in text for term in ["earthquake", "hazard", "scientific"]):
        recommendations.append("usgs_fetcher_tool")
    return list(dict.fromkeys(recommendations or ["rss_fetcher_tool"]))


def evaluate_coverage(items: list[IntelligenceItem], plan: IntelligencePlan) -> CoverageEvaluation:
    if not items:
        return CoverageEvaluation(
            coverage_score=0.0,
            missing_topics=list(plan.required_topics),
            evidence_quality_issues=["No usable items collected."],
            recommended_next_tools=list(plan.required_tools),
            should_continue=True,
        )

    covered = _covered_topics(items, plan.required_topics)
    missing_topics = [topic for topic in plan.required_topics if topic not in covered]
    topic_coverage = len(covered) / max(1, len(plan.required_topics))

    primary_items = [
        item
        for item in items
        if item.evidence_level == EvidenceLevel.primary
        or item.source_type in {SourceType.official, SourceType.regulatory, SourceType.company}
    ]
    source_quality = min(1.0, len(primary_items) / max(1, len(items)) + 0.25)

    source_counts = Counter(item.source for item in items)
    max_share = max(source_counts.values()) / len(items)
    max_allowed = plan.source_diversity_constraints.get("max_single_source_share", 0.30)
    source_diversity_issues = []
    source_diversity = 1.0
    if max_share > max_allowed:
        dominant = source_counts.most_common(1)[0][0]
        source_diversity = max(0.0, 1 - (max_share - max_allowed))
        source_diversity_issues.append(
            f"Source concentration: {dominant} accounts for {max_share:.0%} of selected items."
        )

    item_count_score = min(1.0, len(items) / max(1, plan.min_items))
    valid_url_count = sum(1 for item in items if str(item.url).startswith(("http://", "https://")))
    tagged_count = sum(1 for item in items if item.risk_tags)
    evidence_completeness = ((valid_url_count / len(items)) + (tagged_count / len(items))) / 2

    evidence_quality_issues = []
    source_types = {item.source_type.value for item in items}
    if (
        "regulatory" in plan.preferred_source_types
        and SourceType.regulatory.value not in source_types
    ):
        evidence_quality_issues.append("Missing regulatory source evidence.")
    if "academic" in plan.preferred_source_types and SourceType.academic.value not in source_types:
        evidence_quality_issues.append("Missing academic source evidence.")
    if tagged_count < max(1, len(items) // 2):
        evidence_quality_issues.append("Too few selected items contain risk tags.")

    coverage_score = (
        0.35 * topic_coverage
        + 0.25 * source_quality
        + 0.20 * source_diversity
        + 0.10 * item_count_score
        + 0.10 * evidence_completeness
    )
    gap_penalty = (
        0.08 * len(missing_topics)
        + 0.12 * len(evidence_quality_issues)
        + 0.08 * len(source_diversity_issues)
    )
    coverage_score = max(0.0, min(1.0, coverage_score - gap_penalty))
    recommended_next_tools = _recommend_tools(
        missing_topics, evidence_quality_issues + source_diversity_issues
    )
    should_continue = bool(missing_topics or evidence_quality_issues or source_diversity_issues)
    return CoverageEvaluation(
        coverage_score=round(coverage_score, 3),
        missing_topics=missing_topics,
        source_diversity_issues=source_diversity_issues,
        evidence_quality_issues=evidence_quality_issues,
        recommended_next_tools=recommended_next_tools,
        should_continue=should_continue,
    )
