"""Extractor for WordPress-based anime streaming sites (kiranime theme and similar)."""

from kwen_ext.extractors.base import BaseExtractor, ExtractionResult
from kwen_ext.extractors import patterns
from kwen_ext.utils.decode import decode_embed_id, resolve_url, b64decode


class WordPressAnimeExtractor(BaseExtractor):
    """
    Extractor for WordPress anime sites using themes like kiranime, flavor, etc.
    These sites typically:
    - Use data-embed-id attributes with base64-encoded server URLs
    - Have SUB/DUB server selection
    - Include download sections with quality options
    - Use the WordPress REST API for episode data
    """

    name = "wordpress"
    domains = []  # Detected by structure, not domain

    def matches(self, url):
        """Detect by checking for kiranime/wordpress patterns in the page."""
        try:
            from kwen_ext.utils.http import fetch
            resp = fetch(url, client=self.client, timeout=10)
            html = resp.text
            # Check for WordPress anime theme indicators
            indicators = [
                "kiranime" in html.lower(),
                "episode-player" in html,
                "data-embed-id" in html,
                "player-selection" in html,
                "anime-metadata" in html,
            ]
            return any(indicators)
        except Exception:
            return False

    def extract(self, url, use_browser=False):
        result = ExtractionResult()
        soup, raw_html, browser_videos = self.fetch_page(url, use_browser=use_browser)

        # Add video URLs intercepted by browser
        for bv in browser_videos:
            result.sources.append({
                "url": bv["url"],
                "type": bv.get("type", "unknown"),
                "quality": "unknown",
                "label": "Browser Intercepted",
            })

        # Title from og:title or <title>
        og_title = soup.find("meta", property="og:title")
        if og_title and og_title.get("content"):
            result.title = og_title["content"].split(" - ")[0].strip()
        elif soup.find("title"):
            result.title = soup.find("title").get_text(strip=True).split(" - ")[0].strip()

        # Poster image
        og_image = soup.find("meta", property="og:image")
        if og_image and og_image.get("content"):
            result.poster = og_image["content"]

        # Also try the featured image in the page
        featured_img = soup.find("img", class_="wp-post-image")
        if featured_img and featured_img.get("src"):
            result.poster = featured_img["src"]

        # Description / Synopsis
        synopsis_div = soup.find("div", class_="anime-synopsis")
        if synopsis_div:
            result.description = synopsis_div.get_text(strip=True)
        elif soup.find("meta", property="og:description"):
            result.description = soup.find("meta", property="og:description").get("content", "")

        # Duration
        metadata = soup.find("div", class_="anime-metadata")
        if metadata:
            spans = metadata.find_all("span")
            for span in spans:
                text = span.get_text(strip=True)
                if "M" in text and text.replace("M", "").isdigit():
                    result.duration = text

        # Extract embed sources (SUB/DUB servers)
        embed_elements = soup.find_all(attrs={"data-embed-id": True})
        for el in embed_elements:
            encoded = el["data-embed-id"]
            decoded = decode_embed_id(encoded)
            if decoded:
                label, embed_url = decoded

                # Determine if it's SUB or DUB
                parent = el.find_parent(class_=lambda c: c and ("player-sub" in c or "player-dub" in c))
                audio_type = "unknown"
                if parent:
                    if "player-sub" in (parent.get("class") or []):
                        audio_type = "sub"
                    elif "player-dub" in (parent.get("class") or []):
                        audio_type = "dub"

                display_label = el.get_text(strip=True) or label

                result.embeds.append({
                    "url": embed_url,
                    "label": display_label,
                    "type": "embed",
                    "audio": audio_type,
                })
                self.log(f"Found {audio_type} server: {display_label} -> {embed_url}")

        # Active player iframe (the currently loaded one)
        iframe = soup.find("iframe")
        if iframe and iframe.get("src"):
            src = iframe["src"]
            if src.startswith("//"):
                src = "https:" + src
            result.embeds.insert(0, {
                "url": src,
                "label": "Default Player",
                "type": "iframe",
                "audio": "default",
            })

        # Extract download links
        download_section = soup.find("section", class_="download-section")
        if download_section:
            items = download_section.find_all("div", class_="download-section-item")
            for item in items:
                quality_div = item.find("div", class_="download-section-item-res")
                quality = quality_div.get_text(strip=True) if quality_div else "unknown"

                links = item.find_all("a", class_="download-section-item-link")
                for link in links:
                    href = link.get("href", "")
                    host = link.get_text(strip=True)
                    if href:
                        result.downloads.append({
                            "url": href,
                            "quality": quality,
                            "host": host,
                        })
                        self.log(f"Found download: {quality} on {host}")

        # Additional metadata
        result.metadata["source"] = "wordpress"
        result.metadata["url"] = url

        # Try to extract genres
        genre_links = soup.select("a[href*='/genre/']")
        if genre_links:
            result.metadata["genres"] = [g.get_text(strip=True) for g in genre_links]

        # Try to extract score
        score_span = soup.find("span", class_="star-icon")
        if score_span and score_span.parent:
            score_text = score_span.parent.get_text(strip=True)
            result.metadata["score"] = score_text

        return result
