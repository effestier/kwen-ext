"""Generic iframe/embed extractor — works on any page with iframes."""

from kwen_ext.extractors.base import BaseExtractor, ExtractionResult
from kwen_ext.extractors import patterns
from kwen_ext.utils.decode import decode_embed_id, resolve_url, b64decode, is_valid_url


class IframeExtractor(BaseExtractor):
    """
    Generic extractor that finds iframes and embedded video players.
    Works as a fallback for sites without a specific extractor.
    """

    name = "iframe"
    domains = []  # Matches everything as fallback

    def matches(self, url):
        return True  # Always matches — used as fallback

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

        # Extract title
        title_tag = soup.find("title")
        if title_tag:
            result.title = title_tag.get_text(strip=True)

        # Extract og:image poster
        og_image = soup.find("meta", property="og:image")
        if og_image and og_image.get("content"):
            result.poster = og_image["content"]

        # Extract description
        og_desc = soup.find("meta", property="og:description")
        if og_desc and og_desc.get("content"):
            result.description = og_desc["content"]

        # Find iframe sources
        iframe_srcs = patterns.find_iframe_sources(raw_html)
        for src in iframe_srcs:
            full_url = resolve_url(url, src)
            result.embeds.append({
                "url": full_url,
                "label": self._guess_label(full_url),
                "type": "iframe",
            })
            self.log(f"Found iframe: {full_url}")

        # Find base64-encoded embed IDs
        embed_ids = patterns.find_embed_ids(raw_html)
        for encoded in embed_ids:
            decoded = decode_embed_id(encoded)
            if decoded:
                label, embed_url = decoded
                result.embeds.append({
                    "url": embed_url,
                    "label": label,
                    "type": "embed",
                })
                self.log(f"Decoded embed: {label} -> {embed_url}")

        # Find direct video URLs in page source
        m3u8_urls = patterns.find_m3u8_urls(raw_html)
        for u in m3u8_urls:
            result.sources.append({
                "url": u,
                "type": "hls",
                "quality": "unknown",
                "label": "HLS Stream",
            })
            self.log(f"Found m3u8: {u}")

        mp4_urls = patterns.find_mp4_urls(raw_html)
        for u in mp4_urls:
            result.sources.append({
                "url": u,
                "type": "mp4",
                "quality": "unknown",
                "label": "MP4",
            })
            self.log(f"Found mp4: {u}")

        # Find player-configured sources
        player_srcs = patterns.find_player_sources(raw_html)
        for src in player_srcs:
            if src not in [s["url"] for s in result.sources]:
                result.sources.append({
                    "url": src,
                    "type": "hls" if ".m3u8" in src else "mp4",
                    "quality": "unknown",
                    "label": "Player Source",
                })

        # Find download links
        download_links = patterns.DOWNLOAD_LINK.findall(raw_html)
        for dl in download_links:
            full_url = resolve_url(url, dl)
            result.downloads.append({
                "url": full_url,
                "quality": "unknown",
                "host": self._guess_host(full_url),
            })

        return result

    def _guess_label(self, url):
        """Guess a human-readable label from a URL."""
        from kwen_ext.utils.decode import extract_domain
        domain = extract_domain(url)
        known = {
            "abyssplayer": "Abyss",
            "bysevpoint": "Moon",
            "streamtape": "Streamtape",
            "mp4upload": "Mp4Upload",
            "doodstream": "Dood",
            "mixdrop": "MixDrop",
        }
        for key, label in known.items():
            if key in domain:
                return label
        return domain.split(".")[0].title()

    def _guess_host(self, url):
        """Guess the hosting service from a download URL."""
        from kwen_ext.utils.decode import extract_domain
        domain = extract_domain(url)
        known = {
            "mediafire": "Mediafire",
            "mega": "Mega",
            "drive.google": "Google Drive",
            "gofile": "GoFile",
            "streamtape": "Streamtape",
            "1fichier": "1Fichier",
        }
        for key, label in known.items():
            if key in domain:
                return label
        return domain
