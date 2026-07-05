from datetime import datetime, timezone

from risklens.models import IntelligenceItem
from risklens.pipeline.deduplicate import deduplicate_items


def item(item_id: str, title: str) -> IntelligenceItem:
    return IntelligenceItem(
        id=item_id,
        title=title,
        url=f"https://example.com/{item_id}",
        source="Example",
        published_at=datetime.now(timezone.utc),
    )


def test_deduplicate_removes_same_title_and_url_fingerprint():
    first = item("a", "AI governance signal")
    duplicate = item("a", "AI governance signal")
    unique = deduplicate_items([first, duplicate])
    assert len(unique) == 1
