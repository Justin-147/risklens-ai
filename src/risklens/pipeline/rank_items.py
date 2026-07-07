from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime

from risklens.models import IntelligenceItem
from risklens.pipeline.severity import severity_score


def _aware_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def apply_recency(items: list[IntelligenceItem], as_of: datetime | None = None) -> None:
    now = _aware_utc(as_of or datetime.now(UTC))
    for item in items:
        age_days = max(0, (now - _aware_utc(item.published_at)).days)
        item.recency_score = max(0.15, 1 - min(age_days, 90) / 90)


def rank_items(
    items: list[IntelligenceItem],
    limit: int = 8,
    as_of: datetime | None = None,
) -> list[IntelligenceItem]:
    apply_recency(items, as_of=as_of)
    for item in items:
        item.final_score = (
            0.24 * item.authority_score
            + 0.20 * item.relevance_score
            + 0.16 * item.recency_score
            + 0.12 * item.risk_or_opportunity_score
            + 0.10 * item.novelty_score
            + 0.10 * item.evidence_quality_score
            + 0.08 * severity_score(item)
            - item.duplication_penalty
        )
    ranked = sorted(items, key=lambda item: item.final_score, reverse=True)
    return enforce_media_cap(ranked, limit=limit)


def enforce_media_cap(items: list[IntelligenceItem], limit: int = 8) -> list[IntelligenceItem]:
    max_per_source = max(1, int(limit * 0.30))
    counts: Counter[str] = Counter()
    selected: list[IntelligenceItem] = []
    for item in items:
        if counts[item.source] >= max_per_source:
            continue
        selected.append(item)
        counts[item.source] += 1
        if len(selected) == limit:
            break
    return selected
