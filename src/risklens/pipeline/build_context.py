from __future__ import annotations

from datetime import UTC, datetime

from risklens.models import IntelligenceItem


def _report_date(generated_at: datetime | None) -> str:
    if generated_at is None:
        return datetime.now(UTC).date().isoformat()
    if generated_at.tzinfo is not None:
        generated_at = generated_at.astimezone(UTC).replace(tzinfo=None)
    return generated_at.date().isoformat()


def build_report_context(
    profile_name: str,
    items: list[IntelligenceItem],
    generated_at: datetime | None = None,
) -> dict:
    return {
        "profile_name": profile_name,
        "report_date": _report_date(generated_at),
        "items": [item.to_json_dict() for item in items],
        "top_risks": sorted({tag for item in items for tag in item.risk_tags}),
    }
