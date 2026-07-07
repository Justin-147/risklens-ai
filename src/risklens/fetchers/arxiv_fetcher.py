from risklens.fetchers.rss_fetcher import fetch_rss
from risklens.models import IntelligenceItem


def fetch_arxiv(query: str, limit: int = 10) -> list[IntelligenceItem]:
    url = f"https://export.arxiv.org/api/query?search_query=all:{query}&start=0&max_results={limit}"
    return fetch_rss(url, "arXiv", limit=limit)
