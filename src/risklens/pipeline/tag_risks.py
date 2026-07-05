from __future__ import annotations

from risklens.models import IntelligenceItem


def tag_risks(items: list[IntelligenceItem], taxonomy: dict) -> list[IntelligenceItem]:
    definitions = taxonomy.get("risk_tags", {})
    for item in items:
        text = f"{item.title} {item.summary} {item.raw_text}".lower()
        tags = []
        for tag, meta in definitions.items():
            if any(term.lower() in text for term in meta.get("terms", [])):
                tags.append(tag)
        item.risk_tags = tags or ["opportunity_signal"]
        item.risk_or_opportunity_score = min(1.0, 0.25 + 0.18 * len(item.risk_tags))
    return items
