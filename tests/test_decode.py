"""Tests for decode utilities."""

import pytest
from kwen_ext.utils.decode import (
    b64decode, b64encode, resolve_url, extract_domain,
    is_valid_url, decode_embed_id, sanitize_url,
)


class TestB64:
    def test_decode(self):
        assert b64decode("aGVsbG8=") == "hello"

    def test_encode(self):
        assert b64encode("hello") == "aGVsbG8="

    def test_decode_padding(self):
        # Missing padding
        assert b64decode("aGVsbG8") == "hello"

    def test_decode_invalid(self):
        assert b64decode("!!!invalid!!!") is None


class TestUrl:
    def test_resolve_relative(self):
        assert resolve_url("https://example.com/page/", "video.mp4") == "https://example.com/page/video.mp4"

    def test_resolve_absolute(self):
        assert resolve_url("https://example.com/page/", "https://cdn.com/video.mp4") == "https://cdn.com/video.mp4"

    def test_extract_domain(self):
        assert extract_domain("https://sub.example.com/path") == "sub.example.com"

    def test_valid_url(self):
        assert is_valid_url("https://example.com") is True
        assert is_valid_url("not a url") is False
        assert is_valid_url("") is False


class TestDecodeEmbedId:
    def test_label_url_format(self):
        encoded = "QWJ5c3NzdWI=:aHR0cHM6Ly9hYnlzc3BsYXllci5jb20vemFiYzEyMw=="
        result = decode_embed_id(encoded)
        assert result is not None
        label, url = result
        assert "Abyss" in label
        assert "abyssplayer.com" in url

    def test_plain_base64_url(self):
        encoded = b64encode("https://example.com/video.mp4")
        result = decode_embed_id(encoded)
        assert result is not None
        assert result[1] == "https://example.com/video.mp4"

    def test_invalid(self):
        assert decode_embed_id("not-base64!!!") is None


class TestSanitizeUrl:
    def test_strips_token(self):
        url = "https://example.com/video.mp4?token=secret123&quality=1080p"
        result = sanitize_url(url)
        assert "token" not in result
        assert "secret123" not in result
        assert "quality=1080p" in result

    def test_strips_api_key(self):
        url = "https://example.com/api?key=abc123&id=456"
        result = sanitize_url(url)
        assert "key" not in result
        assert "abc123" not in result
        assert "id=456" in result

    def test_clean_url_unchanged(self):
        url = "https://example.com/video.mp4"
        assert sanitize_url(url) == url
