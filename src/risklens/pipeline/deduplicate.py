from __future__ import annotations

import re

from risklens.models import IntelligenceItem


def fingerprint(text: str) -> str:
    words = re.findall(r"[a-z0-9]+", text.lower())
    return " ".join(words[:18])


def deduplicate_items(items: list[IntelligenceItem]) -> list[IntelligenceItem]:
    seen: set[str] = set()
    unique: list[IntelligenceItem] = []
    for item in items:
        key = fingerprint(f"{item.title} {item.url}")
        if key in seen:
            item.duplication_penalty = 0.35
            continue
        seen.add(key)
        unique.append(item)
    return unique
