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

    def fetch_page(self, url):
        """Fetch and parse a page."""
        self.log(f"Fetching {url}")
        resp = fetch(url, client=self.client)
        return BeautifulSoup(resp.text, "lxml"), resp.text

    def extract(self, url):
        """
        Extract media info from a URL.

        Returns an ExtractionResult.
        Must be implemented by subclasses.
        """
        raise NotImplementedError("Subclasses must implement extract()")
