"""Core extraction logic — routes URLs to the right extractor."""

from kwen_ext.extractors.base import ExtractionResult
from kwen_ext.extractors.wordpress import WordPressAnimeExtractor
from kwen_ext.extractors.iframe import IframeExtractor

# Registry of specialized extractors (order matters — first match wins)
EXTRACTORS = [
    WordPressAnimeExtractor,
]

# Fallback extractor (always matches)
FALLBACK = IframeExtractor


def get_extractor(url, verbose=False):
    """Find the best extractor for a URL."""
    for cls in EXTRACTORS:
        ext = cls(verbose=verbose)
        if ext.matches(url):
            return ext

    # Fallback to generic iframe extractor
    return FALLBACK(verbose=verbose)


def extract(url, extractor_name=None, verbose=False):
    """
    Extract media info from a URL.

    Args:
        url: The page URL to extract from
        extractor_name: Force a specific extractor (optional)
        verbose: Print debug info

    Returns:
        ExtractionResult with all found media
    """
    if extractor_name:
        # Find by name
        for cls in EXTRACTORS:
            if cls.name == extractor_name:
                ext = cls(verbose=verbose)
                return ext.extract(url)
        if FALLBACK.name == extractor_name:
            ext = FALLBACK(verbose=verbose)
            return ext.extract(url)
        raise ValueError(f"Unknown extractor: {extractor_name}")

    ext = get_extractor(url, verbose=verbose)
    if verbose:
        print(f"Using extractor: {ext.name}")
    return ext.extract(url)
