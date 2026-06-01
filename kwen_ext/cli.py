"""CLI entry point for kwen-ext."""

import argparse
import json
import sys

from kwen_ext import __version__
from kwen_ext.core import extract, extract_html
from kwen_ext.utils.decode import sanitize_url, is_valid_url


BANNER = r"""
██╗  ██╗██╗    ██╗███████╗███╗   ██╗      ███████╗██╗  ██╗████████╗
██║ ██╔╝██║    ██║██╔════╝████╗  ██║      ██╔════╝╚██╗██╔╝╚══██╔══╝
█████╔╝ ██║ █╗ ██║█████╗  ██╔██╗ ██║█████╗█████╗   ╚███╔╝    ██║
██╔═██╗ ██║███╗██║██╔══╝  ██║╚██╗██║╚════╝██╔══╝   ██╔██╗    ██║
██║  ██╗╚███╔███╔╝███████╗██║ ╚████║      ███████╗██╔╝ ██╗   ██║
╚═╝  ╚═╝ ╚══╝╚══╝ ╚══════╝╚═╝  ╚═══╝      ╚══════╝╚═╝  ╚═╝   ╚═╝
                       Media Extractor v{version}
"""


def format_sources(result):
    """Format sources for human-readable output."""
    lines = []

    if result.title:
        lines.append(f"\n  Title: {result.title}")

    if result.duration:
        lines.append(f"  Duration: {result.duration}")

    if result.description:
        desc = result.description[:200] + "..." if len(result.description) > 200 else result.description
        lines.append(f"  Description: {desc}")

    if result.poster:
        lines.append(f"  Poster: {sanitize_url(result.poster)}")

    # Embeds / Players
    if result.embeds:
        lines.append(f"\n  --- Players ({len(result.embeds)}) ---")
        # Group by audio type
        subs = [e for e in result.embeds if e.get("audio") == "sub"]
        dubs = [e for e in result.embeds if e.get("audio") == "dub"]
        other = [e for e in result.embeds if e.get("audio") not in ("sub", "dub")]

        if subs:
            lines.append("  SUB:")
            for e in subs:
                lines.append(f"    {e['label']:20s} {sanitize_url(e['url'])}")

        if dubs:
            lines.append("  DUB:")
            for e in dubs:
                lines.append(f"    {e['label']:20s} {sanitize_url(e['url'])}")

        if other:
            lines.append("  Other:")
            for e in other:
                lines.append(f"    {e['label']:20s} {sanitize_url(e['url'])}")

    # Direct video sources
    if result.sources:
        lines.append(f"\n  --- Video Sources ({len(result.sources)}) ---")
        for s in result.sources:
            lines.append(f"    [{s['type']:5s}] {s.get('quality', '?'):6s} {sanitize_url(s['url'])}")

    # Downloads
    if result.downloads:
        lines.append(f"\n  --- Downloads ({len(result.downloads)}) ---")
        for d in result.downloads:
            lines.append(f"    {d['quality']:8s} {d['host']:15s} {sanitize_url(d['url'])}")

    # Extra metadata
    if result.metadata:
        extra = {k: v for k, v in result.metadata.items() if k not in ("source", "url")}
        if extra:
            lines.append("\n  --- Metadata ---")
            for k, v in extra.items():
                if isinstance(v, list):
                    lines.append(f"    {k}: {', '.join(str(i) for i in v)}")
                else:
                    lines.append(f"    {k}: {v}")

    if not result.has_content():
        lines.append("\n  No media found on this page.")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        prog="kwen-ext",
        description="Extract video streams, download links & metadata from streaming sites.",
        epilog="Examples:\n"
               "  kwen-ext https://example.com/watch/movie/\n"
               "  kwen-ext https://example.com/watch/movie/ --json\n"
               "  kwen-ext https://example.com/watch/movie/ -v\n",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("url", help="URL of the page to extract from")
    parser.add_argument("--json", action="store_true", dest="json_output", help="Output as JSON")
    parser.add_argument("--extractor", "-e", help="Force a specific extractor (wordpress, iframe)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--downloads-only", action="store_true", help="Show only download links")
    parser.add_argument("--html", help="Parse a saved HTML file instead of fetching URL")
    parser.add_argument("--version", action="version", version=f"kwen-ext v{__version__}")
    parser.add_argument("--no-banner", action="store_true", help="Suppress the ASCII banner")

    args = parser.parse_args()

    # Validate URL
    if not is_valid_url(args.url):
        print(f"  Error: Invalid URL: {args.url}", file=sys.stderr)
        sys.exit(1)

    try:
        from kwen_ext.utils.http import validate_url
        validate_url(args.url)
    except ValueError as e:
        print(f"  Error: {e}", file=sys.stderr)
        sys.exit(1)

    if not args.no_banner:
        print(BANNER.format(version=__version__))

    print(f"  Extracting from: {args.url}\n")

    try:
        if args.html:
            # Parse local HTML file
            with open(args.html, "r", encoding="utf-8") as f:
                html_content = f.read()
            result = extract_html(
                html_content,
                url=args.url,
                extractor_name=args.extractor,
                verbose=args.verbose,
            )
        else:
            result = extract(
                args.url,
                extractor_name=args.extractor,
                verbose=args.verbose,
            )
    except Exception as e:
        error_msg = str(e)
        print(f"  Error: {error_msg}", file=sys.stderr)

        if "403" in error_msg:
            print("\n  Cloudflare blocked this request.", file=sys.stderr)
            print("  Workarounds:", file=sys.stderr)
            print("    1. Save the page HTML from your browser (Ctrl+S), then:", file=sys.stderr)
            print(f"       kwen-ext {args.url} --html saved_page.html", file=sys.stderr)
            print("    2. Use yt-dlp: yt-dlp <url>", file=sys.stderr)
            print("    3. Use a browser extension like Video DownloadHelper", file=sys.stderr)

        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

    if args.json_output:
        print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))
    elif args.downloads_only:
        if result.downloads:
            for d in result.downloads:
                print(f"{d['quality']:8s} {d['host']:15s} {d['url']}")
        else:
            print("  No download links found.")
    else:
        print(format_sources(result))

    print()


if __name__ == "__main__":
    main()
