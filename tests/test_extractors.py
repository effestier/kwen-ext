"""Tests for extractors."""

import pytest
from unittest.mock import patch, MagicMock
from bs4 import BeautifulSoup

from kwen_ext.extractors.base import ExtractionResult
from kwen_ext.extractors.iframe import IframeExtractor
from kwen_ext.extractors.wordpress import WordPressAnimeExtractor


SAMPLE_IFRAME_HTML = """
<html>
<head><title>Test Movie - Watch Online</title></head>
<body>
    <meta property="og:image" content="https://example.com/poster.jpg">
    <meta property="og:description" content="A great movie">
    <iframe src="https://player.example.com/embed/abc123" width="640" height="360"></iframe>
    <a href="https://mediafire.com/file/abc123/movie.mkv">Download 1080p</a>
</body>
</html>
"""

SAMPLE_WORDPRESS_HTML = """
<html>
<head>
    <title>Doraemon Movie - Dora Bash</title>
    <meta property="og:title" content="Doraemon Movie - Dora Bash">
    <meta property="og:image" content="https://dorabash.in/poster.jpg">
    <meta property="og:description" content="A Doraemon movie">
</head>
<body>
    <div class="episode-player-box">
        <iframe src='https://abyssplayer.com/zgNtdANCr'></iframe>
    </div>
    <div class="player-selection player-sub">
        <span data-embed-id="QWJ5c3NzdWI=:aHR0cHM6Ly9hYnlzc3BsYXllci5jb20vemFiYzEyMw==">Abyss</span>
        <span data-embed-id="TW9vbnN1Yg==:aHR0cHM6Ly9ieXNldmVwb2luLmNvbS9lL3Rlc3Q=">Moon</span>
    </div>
    <div class="player-selection player-dub">
        <span data-embed-id="SGluZGlkdWI=:aHR0cHM6Ly9hYnlzc3BsYXllci5jb20vaGluZGk=">Hindi</span>
    </div>
    <div class="anime-metadata">
        <span>PG</span><span>DUB</span><span>HD</span><span>SUB</span><span>MOVIE</span><span>90M</span>
    </div>
    <div class="anime-synopsis">
        <p>Nobita is trying to prove that the Monkey King exists...</p>
    </div>
    <section class="download-section">
        <div class="download-section-item">
            <div class="download-section-item-res">1080p</div>
            <a class="download-section-item-link" href="https://mediafire.com/file/abc/movie.mkv">Mediafire</a>
        </div>
    </section>
</body>
</html>
"""


class TestExtractionResult:
    def test_empty(self):
        r = ExtractionResult()
        assert r.has_content() is False
        assert r.to_dict()["title"] is None

    def test_with_content(self):
        r = ExtractionResult()
        r.title = "Test"
        r.sources.append({"url": "https://example.com/video.m3u8", "type": "hls", "quality": "1080p", "label": "HLS"})
        assert r.has_content() is True

    def test_add_resolved_streams(self):
        r = ExtractionResult()
        r.add_resolved_streams([
            {"url": "https://cdn.com/stream.m3u8", "type": "hls"},
            {"url": "https://cdn.com/video.mp4", "type": "mp4"},
        ], label="Test")
        assert len(r.sources) == 2
        assert r.sources[0]["label"] == "Test"

    def test_add_resolved_dedup(self):
        r = ExtractionResult()
        r.add_resolved_streams([{"url": "https://cdn.com/stream.m3u8", "type": "hls"}])
        r.add_resolved_streams([{"url": "https://cdn.com/stream.m3u8", "type": "hls"}])
        assert len(r.sources) == 1


class TestIframeExtractor:
    def _extract(self, html, url="https://example.com/watch/movie/"):
        ext = IframeExtractor(verbose=False)
        soup = BeautifulSoup(html, "lxml")
        ext.fetch_page = lambda u, **kw: (soup, html, [])
        return ext.extract(url)

    def test_title(self):
        result = self._extract(SAMPLE_IFRAME_HTML)
        assert "Test Movie" in result.title

    def test_poster(self):
        result = self._extract(SAMPLE_IFRAME_HTML)
        assert "poster.jpg" in result.poster

    def test_iframe(self):
        result = self._extract(SAMPLE_IFRAME_HTML)
        assert len(result.embeds) >= 1
        assert "player.example.com" in result.embeds[0]["url"]

    def test_download(self):
        result = self._extract(SAMPLE_IFRAME_HTML)
        assert len(result.downloads) >= 1
        assert "mediafire.com" in result.downloads[0]["url"]


class TestWordPressExtractor:
    def _extract(self, html, url="https://dorabash.in/watch/test/"):
        ext = WordPressAnimeExtractor(verbose=False)
        soup = BeautifulSoup(html, "lxml")
        ext.fetch_page = lambda u, **kw: (soup, html, [])
        return ext.extract(url)

    def test_title(self):
        result = self._extract(SAMPLE_WORDPRESS_HTML)
        assert "Doraemon" in result.title

    def test_embeds_sub_dub(self):
        result = self._extract(SAMPLE_WORDPRESS_HTML)
        subs = [e for e in result.embeds if e.get("audio") == "sub"]
        dubs = [e for e in result.embeds if e.get("audio") == "dub"]
        assert len(subs) >= 2  # Abyss + Moon
        assert len(dubs) >= 1  # Hindi

    def test_downloads(self):
        result = self._extract(SAMPLE_WORDPRESS_HTML)
        assert len(result.downloads) >= 1
        assert result.downloads[0]["quality"] == "1080p"

    def test_metadata(self):
        result = self._extract(SAMPLE_WORDPRESS_HTML)
        assert result.metadata.get("source") == "wordpress"

    def test_synopsis(self):
        result = self._extract(SAMPLE_WORDPRESS_HTML)
        assert "Monkey King" in result.description
