from __future__ import annotations

from risklens.models import EvidenceLevel, IntelligenceItem, SourceType

HIGH_RISK_TAGS = {"model_risk", "operational_risk", "cybersecurity_risk", "regulatory_risk"}
SEVERITY_SCORES = {"low": 0.25, "medium": 0.60, "high": 1.0}


def assign_evidence_quality_score(item: IntelligenceItem) -> float:
    if item.evidence_level == EvidenceLevel.primary and item.source_type in {
        SourceType.official,
        SourceType.regulatory,
        SourceType.company,
    }:
        return 0.95
    if item.evidence_level == EvidenceLevel.secondary and item.source_type == SourceType.academic:
        return 0.80
    if item.source_type == SourceType.media:
        return 0.60
    if item.evidence_level == EvidenceLevel.unverified:
        return 0.25
    if item.evidence_level == EvidenceLevel.primary:
        return 0.85
    if item.evidence_level == EvidenceLevel.secondary:
        return 0.65
    return 0.40


def assign_severity_and_urgency(item: IntelligenceItem) -> tuple[str, str]:
    tags = set(item.risk_tags)
    primary_or_regulatory = item.evidence_level == EvidenceLevel.primary or item.source_type in {
        SourceType.regulatory,
        SourceType.official,
    }

    if (
        item.source_type == SourceType.regulatory
        and primary_or_regulatory
        and tags.intersection(
            {
                "model_risk",
                "operational_risk",
                "regulatory_risk",
                "third_party_risk",
                "ai_governance_risk",
            }
        )
    ):
        return "high", "act_now"
    if "cybersecurity_risk" in tags and primary_or_regulatory:
        return "high", "act_now"
    if item.source_type == SourceType.academic:
        return "medium", "watch"
    if item.source_type == SourceType.media:
        if tags.intersection(HIGH_RISK_TAGS):
            return "medium", "monitor"
        return "low", "watch"
    if tags == {"opportunity_signal"} or ("opportunity_signal" in tags and len(tags) == 1):
        return "low", "watch"
    if tags.intersection(HIGH_RISK_TAGS):
        return "medium", "monitor"
    return "medium", "watch"


def severity_score(item: IntelligenceItem) -> float:
    return SEVERITY_SCORES.get(item.severity, 0.60)


def enrich_items_with_severity(items: list[IntelligenceItem]) -> list[IntelligenceItem]:
    for item in items:
        item.evidence_quality_score = assign_evidence_quality_score(item)
        item.severity, item.urgency = assign_severity_and_urgency(item)
    return items
