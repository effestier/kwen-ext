"""Base extractor class — all site extractors inherit from this."""

from bs4 import BeautifulSoup

from kwen_ext.utils.http import fetch, get_client


class ExtractionResult:
    """Container for extracted media data."""

    def __init__(self):
        self.title = None
        self.poster = None
        self.description = None
        self.duration = None
        self.sources = []       # {"url": ..., "type": ..., "quality": ..., "label": ...}
        self.downloads = []     # {"url": ..., "quality": ..., "host": ...}
        self.embeds = []        # {"url": ..., "label": ..., "type": ...}
        self.metadata = {}      # Extra metadata (genre, year, etc.)

    def to_dict(self):
        return {
            "title": self.title,
            "poster": self.poster,
            "description": self.description,
            "duration": self.duration,
            "sources": self.sources,
            "downloads": self.downloads,
            "embeds": self.embeds,
            "metadata": self.metadata,
        }

    def has_content(self):
        return bool(self.sources or self.downloads or self.embeds)

    def add_resolved_streams(self, streams, label=None):
        """Add resolved stream URLs (from embed resolver) to sources."""
        for stream in streams:
            url = stream.get("url", "")
            stype = stream.get("type", "unknown")
            if url and url not in [s["url"] for s in self.sources]:
                self.sources.append({
                    "url": url,
                    "type": stype,
                    "quality": "unknown",
                    "label": label or f"Resolved {stype}",
                })


class BaseExtractor:
    """
    Base class for site-specific extractors.

    Subclass this and implement extract() to add support for a new site.
    """

    name = "base"
    domains = []  # List of domains this extractor handles

    def __init__(self, verbose=False):
        self.verbose = verbose
        self.client = get_client()

    def log(self, msg):
        if self.verbose:
            print(f"  [{self.name}] {msg}")

    def matches(self, url):
        """Check if this extractor can handle the given URL."""
        from kwen_ext.utils.decode import extract_domain
        domain = extract_domain(url)
        return any(d in domain for d in self.domains)

    def fetch_page(self, url, use_browser=False):
        """Fetch and parse a page. If use_browser=True, use headless browser (bypasses CF)."""
        self.log(f"Fetching {url}")
        if use_browser:
            from kwen_ext.utils.http import fetch_with_browser
            html, video_urls = fetch_with_browser(url)
            return BeautifulSoup(html, "lxml"), html, video_urls
        resp = fetch(url, client=self.client)
        return BeautifulSoup(resp.text, "lxml"), resp.text, []

    def resolve_embed_streams(self, embed_url, wait_seconds=10):
        """Resolve an embed URL to actual video stream URLs using headless browser."""
        self.log(f"Resolving embed: {embed_url}")
        from kwen_ext.utils.http import resolve_embed_url
        try:
            streams = resolve_embed_url(embed_url, wait_seconds=wait_seconds)
            self.log(f"Found {len(streams)} streams from {embed_url}")
            return streams
        except Exception as e:
            self.log(f"Failed to resolve {embed_url}: {e}")
            return []

    def extract(self, url):
        """
        Extract media info from a URL.

        Returns an ExtractionResult.
        Must be implemented by subclasses.
        """
        raise NotImplementedError("Subclasses must implement extract()")
