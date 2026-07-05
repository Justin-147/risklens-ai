from risklens.fetchers.rss_fetcher import fetch_rss


def fetch_arxiv(query: str, limit: int = 10):
    url = f"https://export.arxiv.org/api/query?search_query=all:{query}&start=0&max_results={limit}"
    return fetch_rss(url, "arXiv", limit=limit)
