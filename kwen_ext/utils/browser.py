"""Headless browser client — bypasses Cloudflare, intercepts video streams."""

import re
from urllib.parse import urlparse

try:
    from playwright.sync_api import sync_playwright
    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False


class BrowserSession:
    """
    Headless browser session that:
    - Bypasses Cloudflare challenges
    - Intercepts network requests to find video streams
    - Returns page HTML after JS rendering
    """

    def __init__(self, headless=True, timeout=60000):
        self.headless = headless
        self.timeout = timeout
        self._playwright = None
        self._browser = None
        self._intercepted_urls = []
        self._video_urls = []

    def __enter__(self):
        if not HAS_PLAYWRIGHT:
            raise RuntimeError("playwright not installed. Run: pip install playwright && python -m playwright install chromium")

        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(
            headless=self.headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
            ],
        )
        return self

    def __exit__(self, *args):
        if self._browser:
            self._browser.close()
        if self._playwright:
            self._playwright.stop()

    def _on_response(self, response):
        """Intercept network responses to find video streams."""
        url = response.url
        content_type = response.headers.get("content-type", "")

        # Track video stream URLs
        if any(ext in url.lower() for ext in [".m3u8", ".mp4", ".ts", ".webm", ".mkv"]):
            self._video_urls.append({
                "url": url,
                "type": self._guess_type(url, content_type),
            })

        # Track any HLS manifest
        if "mpegurl" in content_type.lower() or url.endswith(".m3u8"):
            if url not in [v["url"] for v in self._video_urls]:
                self._video_urls.append({"url": url, "type": "hls"})

    def _guess_type(self, url, content_type):
        """Guess video type from URL and content type."""
        url_lower = url.lower()
        if ".m3u8" in url_lower or "mpegurl" in content_type:
            return "hls"
        if ".mp4" in url_lower:
            return "mp4"
        if ".webm" in url_lower:
            return "webm"
        if ".ts" in url_lower:
            return "ts"
        return "unknown"

    def fetch_page(self, url, wait_for=None, wait_seconds=5):
        """
        Fetch a page with a real browser, bypassing Cloudflare.

        Args:
            url: Page URL
            wait_for: CSS selector to wait for (optional)
            wait_seconds: Seconds to wait for network activity (default 5)

        Returns:
            (page_html, intercepted_video_urls)
        """
        self._video_urls = []
        self._intercepted_urls = []

        context = self._browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
        )
        page = context.new_page()

        # Listen for network responses
        page.on("response", self._on_response)

        try:
            # Navigate and wait for Cloudflare challenge to resolve
            page.goto(url, wait_until="domcontentloaded", timeout=self.timeout)

            # Wait for CF challenge to pass (check for "Just a moment..." title)
            try:
                page.wait_for_function(
                    "() => !document.title.includes('Just a moment')",
                    timeout=15000,
                )
            except Exception:
                pass  # CF might not be present

            # Wait for specific element if requested
            if wait_for:
                try:
                    page.wait_for_selector(wait_for, timeout=10000)
                except Exception:
                    pass

            # Wait for network to settle
            page.wait_for_timeout(wait_seconds * 1000)

            # Get the rendered HTML
            html = page.content()

            return html, list(self._video_urls)

        finally:
            context.close()

    def resolve_embed(self, embed_url, wait_seconds=10):
        """
        Visit an embed player page and intercept the actual video stream URLs.

        Args:
            embed_url: The embed/player URL (e.g., https://abyssplayer.com/abc123)
            wait_seconds: How long to wait for stream requests

        Returns:
            list of {"url": ..., "type": ...} for found streams
        """
        self._video_urls = []

        context = self._browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
        )
        page = context.new_page()
        page.on("response", self._on_response)

        try:
            page.goto(embed_url, wait_until="domcontentloaded", timeout=self.timeout)

            # Try clicking play button if it exists
            for selector in ["button.play", ".play-btn", "#play", "video", ".vjs-big-play-button", "[class*=play]"]:
                try:
                    page.click(selector, timeout=2000)
                    break
                except Exception:
                    continue

            # Wait for video stream requests
            page.wait_for_timeout(wait_seconds * 1000)

            # Also try to find video sources in the page's JS
            try:
                js_sources = page.evaluate("""() => {
                    const sources = [];
                    // Check video elements
                    document.querySelectorAll('video, source').forEach(el => {
                        if (el.src) sources.push({url: el.src, type: 'video'});
                    });
                    // Check common player variables
                    if (window.player && window.player.src) sources.push({url: window.player.src(), type: 'player'});
                    if (window.videojs) {
                        try { sources.push({url: window.videojs('video').src(), type: 'videojs'}); } catch(e) {}
                    }
                    return sources;
                }""")
                for src in js_sources:
                    if src["url"] and src["url"] not in [v["url"] for v in self._video_urls]:
                        self._video_urls.append(src)
            except Exception:
                pass

            return list(self._video_urls)

        finally:
            context.close()


def is_playwright_available():
    """Check if playwright is installed and browsers are available."""
    if not HAS_PLAYWRIGHT:
        return False
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            browser.close()
        return True
    except Exception:
        return False
