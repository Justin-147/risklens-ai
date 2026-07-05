from risklens.fetchers.rss_fetcher import fetch_rss


def fetch_regulatory(feed_url: str, source: str, limit: int = 10):
    return fetch_rss(feed_url, source, limit=limit)
