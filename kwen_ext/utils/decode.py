"""Decode utilities — base64, URL parsing, embed ID extraction."""

import re
import base64
from urllib.parse import urljoin, urlparse, unquote, urlencode, parse_qs, urlunparse


def b64decode(s):
    """Decode a base64 string, handling padding issues."""
    s = s.strip()
    # Add padding if needed
    missing = len(s) % 4
    if missing:
        s += "=" * (4 - missing)
    try:
        return base64.b64decode(s).decode("utf-8")
    except Exception:
        return None


def b64encode(s):
    """Encode a string to base64."""
    return base64.b64encode(s.encode("utf-8")).decode("utf-8")


def resolve_url(base, relative):
    """Resolve a relative URL against a base URL."""
    return urljoin(base, relative)


def extract_domain(url):
    """Extract the domain from a URL."""
    parsed = urlparse(url)
    return parsed.netloc


def is_valid_url(s):
    """Check if a string is a valid URL."""
    try:
        result = urlparse(s)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


# Query params that might contain sensitive tokens/keys
SENSITIVE_PARAMS = {
    "token", "key", "api_key", "apikey", "auth", "signature",
    "secret", "password", "session", "sid", "access_token",
    "refresh_token", "jwt", "bearer", "cookie",
}


def sanitize_url(url):
    """Strip sensitive query parameters from a URL to prevent token leakage."""
    parsed = urlparse(url)
    params = parse_qs(parsed.query, keep_blank_values=True)

    cleaned = {k: v for k, v in params.items()
               if k.lower() not in SENSITIVE_PARAMS}

    new_query = urlencode(cleaned, doseq=True) if cleaned else ""
    return urlunparse(parsed._replace(query=new_query))


def decode_embed_id(encoded):
    """
    Decode embed IDs commonly used by anime streaming sites.
    Format: "base64_label:base64_url"
    Returns (label, url) or None.
    """
    if ":" not in encoded:
        # Try plain base64 decode
        decoded = b64decode(encoded)
        if decoded and is_valid_url(decoded):
            return ("unknown", decoded)
        return None

    parts = encoded.split(":", 1)
    label = b64decode(parts[0])
    url = b64decode(parts[1])

    if label and url:
        return (label.strip(), url.strip())
    return None
