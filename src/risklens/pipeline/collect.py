from __future__ import annotations

import warnings
from collections.abc import Callable
from datetime import UTC, datetime
from typing import TypeVar

from risklens.agent.config import get_agent_profile
from risklens.fetchers.arxiv_fetcher import fetch_arxiv
from risklens.fetchers.market_fetcher import fetch_market_signals
from risklens.fetchers.regulatory_fetcher import fetch_regulatory
from risklens.fetchers.rss_fetcher import fetch_rss
from risklens.models import EvidenceLevel, IntelligenceItem, SourceType

T = TypeVar("T")


def _safe_call(label: str, call: Callable[[], list[T]]) -> list[T]:
    try:
        return call()
    except Exception as exc:  # pragma: no cover - network and parser failures vary by environment
        warnings.warn(f"{label} failed: {exc}", RuntimeWarning, stacklevel=2)
        return []


def _market_dict_to_item(row: dict, idx: int, profile: str) -> IntelligenceItem:
    title = str(row.get("title") or row.get("name") or f"Market signal {idx}")
    summary = str(
        row.get("summary")
        or row.get("description")
        or "Public market signal collected by market adapter."
    )
    url = str(row.get("url") or "https://example.org/risklens-demo/market-signal")
    source = str(row.get("source") or "Market Adapter")
    return IntelligenceItem(
        id=f"market-{profile}-{idx}",
        title=title,
        url=url,
        source=source,
        source_type=SourceType.market,
        published_at=datetime.now(UTC),
        summary=summary,
        raw_text=summary,
        evidence_level=EvidenceLevel.secondary,
    )


def collect_items_from_fetchers(profile: str) -> list[IntelligenceItem]:
    """Collect candidate items from real fetcher adapters for non-mock pipeline mode."""
    profile_config = get_agent_profile(profile)
    feeds = profile_config.get("feeds", {})
    queries = profile_config.get("queries", {})
    items: list[IntelligenceItem] = []

    for feed in feeds.get("regulatory", []):
        feed_url = str(feed["url"])
        feed_source = str(feed["source"])

        def call_regulatory(
            feed_url: str = feed_url,
            feed_source: str = feed_source,
        ) -> list[IntelligenceItem]:
            return fetch_regulatory(feed_url, feed_source, limit=5)

        fetched = _safe_call(f"regulatory:{feed_source}", call_regulatory)
        for item in fetched:
            item.source_type = SourceType.regulatory
            item.evidence_level = EvidenceLevel.primary
        items.extend(fetched)

    for feed in feeds.get("rss", []):
        feed_url = str(feed["url"])
        feed_source = str(feed["source"])

        def call_rss(
            feed_url: str = feed_url,
            feed_source: str = feed_source,
        ) -> list[IntelligenceItem]:
            return fetch_rss(feed_url, feed_source, limit=5)

        items.extend(_safe_call(f"rss:{feed_source}", call_rss))

    for query in queries.get("arxiv", [profile.replace("_", " ")]):
        query_text = str(query)

        def call_arxiv(query_text: str = query_text) -> list[IntelligenceItem]:
            return fetch_arxiv(query_text, limit=3)

        fetched = _safe_call(f"arxiv:{query_text}", call_arxiv)
        for item in fetched:
            item.source_type = SourceType.academic
            item.evidence_level = EvidenceLevel.secondary
        items.extend(fetched)

    market_rows = _safe_call("market", fetch_market_signals)
    items.extend(
        _market_dict_to_item(row, idx, profile) for idx, row in enumerate(market_rows, start=1)
    )
    return items
