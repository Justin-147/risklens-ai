from __future__ import annotations

from risklens.models import IntelligenceItem


def build_report_context(profile_name: str, items: list[IntelligenceItem]) -> dict:
    return {
        "profile_name": profile_name,
        "items": [item.to_json_dict() for item in items],
        "top_risks": sorted({tag for item in items for tag in item.risk_tags}),
    }
