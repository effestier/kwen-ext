"""Regex patterns for finding video sources, embeds, and media URLs."""

import re

# Direct video file URLs
M3U8_PATTERN = re.compile(r'https?://[^\s"\'<>]+\.m3u8[^\s"\'<>]*', re.IGNORECASE)
MP4_PATTERN = re.compile(r'https?://[^\s"\'<>]+\.mp4[^\s"\'<>]*', re.IGNORECASE)
VIDEO_URL_PATTERN = re.compile(r'https?://[^\s"\'<>]+\.(m3u8|mp4|mkv|webm|avi)[^\s"\'<>]*', re.IGNORECASE)

# Iframe sources
IFRAME_SRC_PATTERN = re.compile(r'<iframe[^>]+src=["\']([^"\']+)["\']', re.IGNORECASE)
IFRAME_SRC_PATTERN2 = re.compile(r'<iframe[^>]+src=([^\s>]+)', re.IGNORECASE)

# Embed IDs (base64 encoded — common in anime sites)
EMBED_ID_PATTERN = re.compile(r'data-embed-id=["\']([^"\']+)["\']', re.IGNORECASE)

# Video player patterns
JWPLAYER_SOURCE = re.compile(r'file\s*:\s*["\']([^"\']+)["\']', re.IGNORECASE)
VIDEOJS_SOURCE = re.compile(r'src\s*:\s*["\']([^"\']+)["\']', re.IGNORECASE)
SOURCE_TAG = re.compile(r'<source[^>]+src=["\']([^"\']+)["\']', re.IGNORECASE)

# HLS/Streaming patterns
HLS_CONFIG = re.compile(r'(?:hls|Hls)\.loadSource\(["\']([^"\']+)["\']\)', re.IGNORECASE)
VIDEO_CONFIG = re.compile(r'(?:file|source|url|src)\s*[:=]\s*["\']([^"\']*\.(?:m3u8|mp4)[^"\']*)["\']', re.IGNORECASE)

# Download link patterns
DOWNLOAD_LINK = re.compile(r'href=["\']([^"\']*(?:mediafire|mega|drive|gofile|streamtape|anonfiles|1fichier)[^"\']*)["\']', re.IGNORECASE)

# Base64 encoded data attributes
B64_ATTR_PATTERN = re.compile(r'data-[a-z-]+=["\']([A-Za-z0-9+/=]+)["\']', re.IGNORECASE)


def find_m3u8_urls(text):
    """Find all m3u8 URLs in text."""
    return list(set(M3U8_PATTERN.findall(text)))


def find_mp4_urls(text):
    """Find all mp4 URLs in text."""
    return list(set(MP4_PATTERN.findall(text)))


def find_video_urls(text):
    """Find all video file URLs in text."""
    return list(set(VIDEO_URL_PATTERN.findall(text)))


def find_iframe_sources(text):
    """Find all iframe src URLs."""
    sources = IFRAME_SRC_PATTERN.findall(text)
    sources += IFRAME_SRC_PATTERN2.findall(text)
    # Clean up
    cleaned = []
    for src in sources:
        src = src.strip().strip("'\"")
        if src and not src.startswith("javascript:"):
            cleaned.append(src)
    return list(set(cleaned))


def find_embed_ids(text):
    """Find all data-embed-id values."""
    return EMBED_ID_PATTERN.findall(text)


def find_player_sources(text):
    """Find video sources from common player configurations."""
    sources = []
    sources += JWPLAYER_SOURCE.findall(text)
    sources += SOURCE_TAG.findall(text)
    sources += HLS_CONFIG.findall(text)
    sources += VIDEO_CONFIG.findall(text)
    return list(set(sources))
