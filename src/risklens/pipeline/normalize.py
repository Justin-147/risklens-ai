from __future__ import annotations

from collections.abc import Sequence

from risklens.models import IntelligenceItem


def normalize_items(items: Sequence[IntelligenceItem | dict]) -> list[IntelligenceItem]:
    return [
        item if isinstance(item, IntelligenceItem) else IntelligenceItem(**item) for item in items
    ]
