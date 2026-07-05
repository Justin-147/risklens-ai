from __future__ import annotations

from datetime import datetime, timezone
import warnings

import feedparser
import requests

from risklens.models import EvidenceLevel, IntelligenceItem, SourceType


def fetch_rss(feed_url: str, source: str, limit: int = 10, timeout: int = 10) -> list[IntelligenceItem]:
    try:
        response = requests.get(feed_url, timeout=timeout)
        response.raise_for_status()
    except requests.RequestException as exc:
        warnings.warn(f"RSS fetch failed for {source}: {exc}", RuntimeWarning)
        return []

    parsed = feedparser.parse(response.content)
    if getattr(parsed, "bozo", False):
        warnings.warn(f"RSS parser warning for {source}: {getattr(parsed, 'bozo_exception', 'unknown parser issue')}", RuntimeWarning)
    if not parsed.entries:
        warnings.warn(f"RSS feed returned no entries for {source}: {feed_url}", RuntimeWarning)
        return []

    items: list[IntelligenceItem] = []
    for entry in parsed.entries[:limit]:
        published = getattr(entry, "published_parsed", None)
        published_at = datetime(*published[:6], tzinfo=timezone.utc) if published else datetime.now(timezone.utc)
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