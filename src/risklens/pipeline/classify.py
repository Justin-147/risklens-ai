from __future__ import annotations

from risklens.models import IntelligenceItem


def classify_items(items: list[IntelligenceItem], profile: dict) -> list[IntelligenceItem]:
    keywords = [kw.lower() for kw in profile.get("keywords", [])]
    domains = profile.get("domains", [])
    for item in items:
        text = f"{item.title} {item.summary} {item.raw_text}".lower()
        matches = sum(1 for keyword in keywords if keyword in text)
        item.relevance_score = min(1.0, 0.35 + matches * 0.16)
        item.topic = profile.get("name", "General")
        item.affected_domains = domains[:3]
    return items
