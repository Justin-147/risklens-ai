from __future__ import annotations

import re
from collections import Counter

from risklens.agent.state import IntelligencePlan
from risklens.models import EvidenceLevel, IntelligenceItem, SourceType

BANNED_REPORT_PHRASES = [
    "buy recommendation",
    "sell recommendation",
    "hold recommendation",
    "you should buy",
    "you should sell",
    "autonomous trading",
    "personal holdings",
]

SOURCE_SECTION_PATTERNS = [
    r"^\s*#{1,6}\s*source list\s*$",
    r"^\s*#{1,6}\s*sources\s*$",
    r"^\s*#{1,6}\s*来源列表\s*$",
    r"^\s*#{1,6}\s*来源\s*$",
]


def verify_items(items: list[IntelligenceItem], plan: IntelligencePlan) -> list[str]:
    issues: list[str] = []
    if not items:
        return ["No selected items available for verification."]

    for item in items:
        if not item.title or not item.source or not item.published_at or not item.url:
            issues.append(f"Missing required evidence fields for item {item.id}.")
        if not item.risk_tags:
            issues.append(f"Missing risk tags for item {item.id}.")
        if not str(item.url).startswith(("http://", "https://")):
            issues.append(f"Invalid URL for item {item.id}.")

    source_counts = Counter(item.source for item in items)
    max_allowed = plan.source_diversity_constraints.get("max_single_source_share", 0.30)
    dominant, count = source_counts.most_common(1)[0]
    share = count / len(items)
    if share > max_allowed:
        issues.append(
            f"Single-source dominance: {dominant} accounts for {share:.0%} of selected items."
        )

    high_confidence = [item for item in items if item.authority_score >= 0.85]
    weak_high_confidence = [
        item
        for item in high_confidence
        if item.evidence_level == EvidenceLevel.unverified
        and item.source_type not in {SourceType.official, SourceType.regulatory, SourceType.company}
    ]
    if weak_high_confidence:
        issues.append("High-confidence claims include weak or unverified evidence.")

    return issues


def verify_report_text(report: str) -> list[str]:
    lowered = report.lower()
    issues = [
        f"Report contains prohibited phrase: {phrase}"
        for phrase in BANNED_REPORT_PHRASES
        if phrase in lowered
    ]
    has_source_section = any(
        re.search(pattern, report, flags=re.IGNORECASE | re.MULTILINE)
        for pattern in SOURCE_SECTION_PATTERNS
    )
    if not has_source_section:
        issues.append("Report is missing a source section.")
    return issues
