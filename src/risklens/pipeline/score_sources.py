from __future__ import annotations

from risklens.models import IntelligenceItem, SourceType


AUTHORITY_BY_TYPE = {
    SourceType.official: 0.95,
    SourceType.regulatory: 0.95,
    SourceType.company: 0.85,
    SourceType.academic: 0.82,
    SourceType.market: 0.75,
    SourceType.media: 0.68,
    SourceType.other: 0.45,
}


def score_sources(items: list[IntelligenceItem]) -> list[IntelligenceItem]:
    for item in items:
        item.authority_score = max(item.authority_score, AUTHORITY_BY_TYPE.get(item.source_type, 0.45))
    return items
