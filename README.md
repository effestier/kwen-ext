<p align="center">
  <br>
  <img src="https://img.shields.io/badge/python-3.8+-blue?logo=python&logoColor=white" alt="Python 3.8+">
  <img src="https://img.shields.io/badge/license-MIT-green" alt="MIT License">
  <img src="https://img.shields.io/badge/version-1.0.0-orange" alt="v1.0.0">
  <br><br>
</p>

<h1 align="center">kwen-ext</h1>

<p align="center">
  <b>Stop copying embed URLs by hand.</b><br>
  Give it a page URL. Get every video source, stream link, and download back.<br>
  <br>
  <i>Built by <a href="https://github.com/kwen">Kwen</a> — because inspecting network tabs for m3u8 links is not a hobby.</i>
</p>

---

## What does it do?

You know when you're on a streaming site and there's an embedded player, 6 different servers, SUB and DUB options, and download links scattered everywhere?

**kwen-ext** takes that page URL and gives you back everything structured:

```
$ kwen-ext https://dorabash.in/watch/some-anime-movie/

██╗  ██╗██╗    ██╗███████╗███╗   ██╗      ███████╗██╗  ██╗████████╗
██║ ██╔╝██║    ██║██╔════╝████╗  ██║      ██╔════╝╚██╗██╔╝╚══██╔══╝
█████╔╝ ██║ █╗ ██║█████╗  ██╔██╗ ██║█████╗█████╗   ╚███╔╝    ██║
 ...

  Title: Some Anime Movie
  Duration: 90M
  Poster: https://example.com/poster.jpg

  --- Players (6) ---
  SUB:
    Abyss                https://abyssplayer.com/abc123
    Moon                 https://bysevpoint.com/e/xyz789
  DUB:
    Hindi                https://abyssplayer.com/hindi123
    Tamil                https://abyssplayer.com/tamil456

  --- Downloads (1) ---
    1080p    Mediafire        https://mediafire.com/file/...
```

---

## Install

```bash
# From source (recommended)
git clone https://github.com/kwen/kwen-ext.git
cd kwen-ext
pip install -e .

# Or just install dependencies and run directly
pip install -r requirements.txt
python -m kwen_ext <url>
```

---

## Usage

### Basic extraction

```bash
kwen-ext https://example.com/watch/some-movie/
```

### JSON output (for scripting / piping)

```bash
kwen-ext https://example.com/watch/some-movie/ --json
```

```json
{
  "title": "Some Movie",
  "poster": "https://...",
  "embeds": [
    {"url": "https://player.com/abc", "label": "Abyss", "type": "embed", "audio": "sub"}
  ],
  "downloads": [
    {"url": "https://mediafire.com/...", "quality": "1080p", "host": "Mediafire"}
  ]
}
```

### Only download links

```bash
kwen-ext https://example.com/watch/some-movie/ --downloads-only
```

### Force a specific extractor

```bash
kwen-ext https://example.com/watch/some-movie/ --extractor wordpress
```

### Verbose mode (debug what's happening)

```bash
kwen-ext https://example.com/watch/some-movie/ -v
```

### Pipe to other tools

```bash
# Get all player URLs as a list
kwen-ext https://example.com/watch/ --json | jq '.embeds[].url'

# Get download links only
kwen-ext https://example.com/watch/ --json | jq '.downloads[]'

# Open the first stream in mpv
kwen-ext https://example.com/watch/ --json | jq -r '.sources[0].url' | xargs mpv
```

---

## How it works

kwen-ext uses a **layered extraction approach**:

```
Page URL
  |
  v
[HTML Parser] ---> Finds iframes, data-embed-id, source tags
  |
  v
[Base64 Decoder] ---> Decodes embed IDs (common in anime sites)
  |
  v
[Pattern Matcher] ---> Regex for m3u8, mp4, download links
  |
  v
[Site Extractor] ---> Site-specific logic (WordPress/kiranime, etc.)
  |
  v
ExtractionResult (title, sources, downloads, embeds, metadata)
```

### The embed ID trick

Most anime streaming sites encode their player URLs in base64 inside `data-embed-id` attributes:

```html
<span data-embed-id="QWJ5c3NzdWI=:aHR0cHM6Ly9hYnlzc3BsYXllci5jb20vemFiYzEyMw==">Abyss</span>
```

That's `base64("Abyss"):base64("https://abyssplayer.com/zabc123")`. kwen-ext decodes this automatically.

### Extractors

| Extractor | What it handles |
|-----------|----------------|
| `wordpress` | Anime sites using kiranime/flavor WordPress themes |
| `iframe` | Generic fallback — finds any iframes, video sources, download links |

Extractors are matched in order. `wordpress` is checked first, then `iframe` catches everything else.

---

## Adding a new site

Found a site that doesn't extract well? Add a custom extractor:

```python
# kwen_ext/extractors/mysite.py

from kwen_ext.extractors.base import BaseExtractor, ExtractionResult

class MySiteExtractor(BaseExtractor):
    name = "mysite"
    domains = ["mysite.com", "mysite.net"]

    def extract(self, url):
        result = ExtractionResult()
        soup, raw_html = self.fetch_page(url)

        # Your extraction logic here
        # result.title = ...
        # result.embeds.append({"url": ..., "label": ..., "type": "embed"})
        # result.downloads.append({"url": ..., "quality": ..., "host": ...})

        return result
```

Then register it in `kwen_ext/core.py`:

```python
from kwen_ext.extractors.mysite import MySiteExtractor

EXTRACTORS = [
    MySiteExtractor,    # Add it here
    WordPressAnimeExtractor,
]
```

---

## Output format

```typescript
{
  title: string | null,
  poster: string | null,        // URL to poster/thumbnail
  description: string | null,
  duration: string | null,      // e.g. "90M"

  sources: [{                   // Direct video file URLs
    url: string,                // m3u8 or mp4 URL
    type: "hls" | "mp4",
    quality: string,            // "1080p", "720p", "unknown"
    label: string               // Human-readable label
  }],

  downloads: [{                 // Download page links
    url: string,
    quality: string,
    host: string                // "Mediafire", "Mega", etc.
  }],

  embeds: [{                    // Embedded player URLs
    url: string,
    label: string,              // "Abyss", "Hindi", etc.
    type: "iframe" | "embed",
    audio?: "sub" | "dub" | "default"
  }],

  metadata: {                   // Extra info (varies by site)
    source: string,
    genres?: string[],
    score?: string
  }
}
```

---

## Why?

Because every streaming site has:
- 5+ embed servers encoded in base64
- Download links buried in separate sections
- SUB and DUB mixed together
- No API

And every time you want to grab a stream URL, you:
1. Open DevTools
2. Go to Network tab
3. Filter by "m3u8"
4. Refresh the page
5. Click through 3 ad overlays
6. Find the right URL
7. Copy it

**kwen-ext does all of that in one command.**

---

## Troubleshooting

### "Cloudflare blocked the request"

Some sites use Cloudflare bot protection. kwen-ext uses `cloudscraper` to handle this, but it doesn't always work. If you get blocked:

```bash
# Try verbose mode to see what's happening
kwen-ext <url> -v
```

If it's consistently blocked, the site likely has aggressive protection. Open an issue with the URL.

### "No media found"

- Check if the page loads content dynamically (JavaScript). kwen-ext parses static HTML only.
- Try `--extractor iframe` to force the generic extractor.
- Use `-v` to see what the extractor is finding.

### Base64 decode errors

Some sites use non-standard encoding. If you see garbled labels, it's usually harmless — the URL itself should still be correct.

---

## Contributing

1. Fork it
2. Create your branch (`git checkout -b add-cool-site`)
3. Add an extractor in `kwen_ext/extractors/`
4. Test it (`kwen-ext <url> -v`)
5. Commit and push
6. Open a PR

---

## License

MIT — do whatever you want with it.

---

<p align="center">
  <b>kwen-ext</b> — part of the <a href="https://github.com/kwen">Kwen</a> ecosystem.<br>
  <sub>Built with frustration and too many open DevTools tabs.</sub>
</p>
