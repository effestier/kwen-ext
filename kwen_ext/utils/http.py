"""HTTP client with Cloudflare bypass support."""

import requests

try:
    import cloudscraper
    HAS_CLOUDSCRAPER = True
except ImportError:
    HAS_CLOUDSCRAPER = False

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}


def get_client(force_cloudscraper=False):
    """Return an HTTP session, using cloudscraper if available."""
    if force_cloudscraper or HAS_CLOUDSCRAPER:
        try:
            return cloudscraper.create_scraper(browser={"browser": "chrome", "platform": "windows", "mobile": False})
        except Exception:
            pass
    session = requests.Session()
    session.headers.update(DEFAULT_HEADERS)
    return session


def fetch(url, client=None, timeout=30):
    """Fetch a URL and return the response. Auto-retries with cloudscraper on 403."""
    if client is None:
        client = get_client()

    resp = client.get(url, timeout=timeout, allow_redirects=True)

    # If blocked and we're not already using cloudscraper, retry with it
    if resp.status_code == 403 and not HAS_CLOUDSCRAPER:
        client = get_client(force_cloudscraper=True)
        resp = client.get(url, timeout=timeout, allow_redirects=True)

    resp.raise_for_status()
    return resp
