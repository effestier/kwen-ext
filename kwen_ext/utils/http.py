"""HTTP client with Cloudflare bypass support."""

import requests
from urllib.parse import urlparse

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

# Block internal/private IPs to prevent SSRF
BLOCKED_HOSTS = {
    "localhost", "127.0.0.1", "0.0.0.0", "::1",
    "10.0.0.0", "192.168.0.0", "172.16.0.0",
    "metadata.google.internal", "169.254.169.254",
}

ALLOWED_SCHEMES = {"http", "https"}


def validate_url(url):
    """Validate a URL is safe to fetch. Raises ValueError if not."""
    parsed = urlparse(url)

    if parsed.scheme not in ALLOWED_SCHEMES:
        raise ValueError(f"Blocked scheme: {parsed.scheme}")

    hostname = (parsed.hostname or "").lower()

    if hostname in BLOCKED_HOSTS:
        raise ValueError(f"Blocked host: {hostname}")

    # Block private IP ranges
    if hostname.startswith(("10.", "192.168.", "172.16.", "172.17.", "172.18.",
                            "172.19.", "172.2", "172.30.", "172.31.")):
        raise ValueError(f"Blocked private IP: {hostname}")

    # Block file:// and other dangerous schemes in redirects
    if parsed.scheme not in ALLOWED_SCHEMES:
        raise ValueError(f"Blocked scheme: {parsed.scheme}")

    return True


def get_client(force_cloudscraper=False):
    """Return an HTTP session, using cloudscraper if available."""
    if force_cloudscraper and HAS_CLOUDSCRAPER:
        try:
            return cloudscraper.create_scraper(browser={"browser": "chrome", "platform": "windows", "mobile": False})
        except Exception:
            pass
    session = requests.Session()
    session.headers.update(DEFAULT_HEADERS)
    return session


def fetch(url, client=None, timeout=30):
    """Fetch a URL and return the response. Auto-retries with cloudscraper on 403."""
    validate_url(url)

    # Always try cloudscraper first if available (handles Cloudflare)
    if client is None:
        client = get_client(force_cloudscraper=True)

    resp = client.get(url, timeout=timeout, allow_redirects=True)

    # Validate redirect didn't go somewhere dangerous
    if resp.url:
        validate_url(resp.url)

    # If blocked, retry with cloudscraper
    if resp.status_code == 403 and HAS_CLOUDSCRAPER:
        client = get_client(force_cloudscraper=True)
        resp = client.get(url, timeout=timeout, allow_redirects=True)

    resp.raise_for_status()
    return resp
