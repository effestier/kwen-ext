"""Tests for pattern matching."""

import pytest
from kwen_ext.extractors.patterns import (
    find_m3u8_urls, find_mp4_urls, find_iframe_sources,
    find_embed_ids, find_player_sources,
)


class TestM3u8:
    def test_basic(self):
        text = 'source: "https://cdn.example.com/stream.m3u8"'
        urls = find_m3u8_urls(text)
        assert len(urls) == 1
        assert "stream.m3u8" in urls[0]

    def test_with_params(self):
        text = "https://cdn.com/video.m3u8?token=abc&quality=1080"
        urls = find_m3u8_urls(text)
        assert len(urls) == 1

    def test_none(self):
        assert find_m3u8_urls("no video here") == []


class TestMp4:
    def test_basic(self):
        text = '<source src="https://cdn.com/movie.mp4">'
        urls = find_mp4_urls(text)
        assert len(urls) == 1
        assert "movie.mp4" in urls[0]


class TestIframe:
    def test_double_quotes(self):
        html = '<iframe src="https://player.example.com/embed/123" width="640"></iframe>'
        sources = find_iframe_sources(html)
        assert len(sources) == 1
        assert "player.example.com" in sources[0]

    def test_single_quotes(self):
        html = "<iframe src='https://player.example.com/embed/456'></iframe>"
        sources = find_iframe_sources(html)
        assert len(sources) == 1

    def test_no_iframe(self):
        assert find_iframe_sources("<div>no iframe</div>") == []


class TestEmbedIds:
    def test_basic(self):
        html = '<span data-embed-id="QWJ5c3NzdWI=:aHR0cHM6Ly9hYnlzc3BsYXllci5jb20vemFiYzEyMw==">Abyss</span>'
        ids = find_embed_ids(html)
        assert len(ids) == 1
        assert ids[0] == "QWJ5c3NzdWI=:aHR0cHM6Ly9hYnlzc3BsYXllci5jb20vemFiYzEyMw=="

    def test_none(self):
        assert find_embed_ids("<div>no embeds</div>") == []


class TestPlayerSources:
    def test_jwplayer(self):
        text = 'file: "https://cdn.com/stream.m3u8"'
        sources = find_player_sources(text)
        assert len(sources) >= 1

    def test_source_tag(self):
        text = '<source src="https://cdn.com/video.mp4" type="video/mp4">'
        sources = find_player_sources(text)
        assert len(sources) >= 1
