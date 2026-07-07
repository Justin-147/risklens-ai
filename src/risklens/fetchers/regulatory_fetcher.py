from risklens.fetchers.rss_fetcher import fetch_rss
from risklens.models import IntelligenceItem


def fetch_regulatory(feed_url: str, source: str, limit: int = 10) -> list[IntelligenceItem]:
    return fetch_rss(feed_url, source, limit=limit)
