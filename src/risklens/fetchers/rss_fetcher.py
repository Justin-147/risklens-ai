from __future__ import annotations

import warnings
from datetime import UTC, datetime

import feedparser
import requests

from risklens.models import EvidenceLevel, IntelligenceItem, SourceType


def fetch_rss(
    feed_url: str, source: str, limit: int = 10, timeout: int = 10
) -> list[IntelligenceItem]:
    try:
        response = requests.get(feed_url, timeout=timeout)
        response.raise_for_status()
    except requests.RequestException as exc:
        warnings.warn(f"RSS fetch failed for {source}: {exc}", RuntimeWarning, stacklevel=2)
        return []

    parsed = feedparser.parse(response.content)
    if getattr(parsed, "bozo", False):
        parser_issue = getattr(parsed, "bozo_exception", "unknown parser issue")
        warnings.warn(
            f"RSS parser warning for {source}: {parser_issue}",
            RuntimeWarning,
            stacklevel=2,
        )
    if not parsed.entries:
        warnings.warn(
            f"RSS feed returned no entries for {source}: {feed_url}",
            RuntimeWarning,
            stacklevel=2,
        )
        return []

    items: list[IntelligenceItem] = []
    for entry in parsed.entries[:limit]:
        published = getattr(entry, "published_parsed", None)
        published_at = (
            datetime(*published[:6]).replace(tzinfo=UTC) if published else datetime.now(UTC)
        )
        summary = getattr(entry, "summary", "")
        items.append(
            IntelligenceItem(
                id=f"{source}:{getattr(entry, 'id', getattr(entry, 'link', entry.title))}",
                title=entry.title,
                url=getattr(entry, "link", feed_url),
                source=source,
                source_type=SourceType.media,
                published_at=published_at,
                summary=summary,
                raw_text=summary,
                evidence_level=EvidenceLevel.secondary,
            )
        )
    return items
