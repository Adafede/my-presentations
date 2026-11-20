"""Inject the JavaScript-free Simple Analytics pixel and CSS into rendered HTML."""

from __future__ import annotations

import os
import re
from pathlib import Path
from urllib.parse import quote

SITE_DIR = Path("_site")
ANALYTICS_HOSTNAME = "adafede.github.io"
BASE_PATH = "/my-presentations"
PIXEL_STYLE_ID = "analytics-pixel-style"
PIXEL_CSS = (
    f'<style id="{PIXEL_STYLE_ID}">'
    ".analytics-pixel{position:absolute;inset-block-start:0;inset-inline-start:0;"
    "inline-size:1px;block-size:1px;opacity:0;pointer-events:none;}</style>"
)
SCRIPT_RE = re.compile(
    r'<script\b[^>]*\bsrc=["\'][^"\']*simpleanalyticscdn\.com[^"\']*["\'][^>]*>\s*</script>',
    re.IGNORECASE,
)
NOSCRIPT_PIXEL_RE = re.compile(
    r"<noscript\b[^>]*>[\s\S]*?noscript\.gif[\s\S]*?</noscript>",
    re.IGNORECASE,
)
EXISTING_PIXEL_RE = re.compile(
    r'<img\b[^>]*\bclass=["\'][^"\']*\banalytics-pixel\b[^"\']*["\'][^>]*>',
    re.IGNORECASE,
)
EXISTING_STYLE_RE = re.compile(
    rf'<style\b[^>]*\bid=["\']{PIXEL_STYLE_ID}["\'][^>]*>[\s\S]*?</style>',
    re.IGNORECASE,
)


def page_path_for(html_file: Path, site_dir: Path = SITE_DIR) -> str:
    """Return the canonical site path for a rendered HTML file."""
    rel = html_file.relative_to(site_dir).as_posix()
    if rel == "index.html":
        return f"{BASE_PATH}/"
    if rel.endswith("/index.html"):
        return f"{BASE_PATH}/{rel[:-10].rstrip('/')}/"
    return f"{BASE_PATH}/{rel}"


def build_pixel_tag(page_path: str, hostname: str = ANALYTICS_HOSTNAME) -> str:
    """Build the JavaScript-free Simple Analytics ``<img>`` pixel element."""
    encoded_host = quote(hostname, safe=".-")
    encoded_path = quote(page_path, safe="")
    return (
        "<img\n"
        f'  src="https://queue.simpleanalyticscdn.com/noscript.gif?hostname={encoded_host}&amp;path={encoded_path}"\n'
        '  alt=""\n'
        '  width="1"\n'
        '  height="1"\n'
        '  referrerpolicy="no-referrer-when-downgrade"\n'
        '  decoding="async"\n'
        '  fetchpriority="low"\n'
        '  aria-hidden="true"\n'
        '  class="analytics-pixel"\n'
        "/>"
    )


def inject_analytics_pixel(site_dir: Path = SITE_DIR) -> int:
    """Inject ``.analytics-pixel`` CSS and ``noscript.gif`` into every page under ``_site``."""
    if not site_dir.is_dir():
        return 0

    updated = 0
    for html_file in sorted(site_dir.rglob("*.html")):
        if html_file.name == "talk_map.html":
            continue

        original = html_file.read_text(encoding="utf-8")
        content = SCRIPT_RE.sub("", original)
        content = NOSCRIPT_PIXEL_RE.sub("", content)
        content = EXISTING_STYLE_RE.sub("", content)
        content = EXISTING_PIXEL_RE.sub("", content)

        if "</head>" in content and ".analytics-pixel" not in content:
            content = content.replace("</head>", f"{PIXEL_CSS}\n</head>", 1)

        if "</body>" in content:
            pixel = build_pixel_tag(page_path_for(html_file, site_dir))
            content = content.replace("</body>", f"{pixel}\n</body>", 1)

        if content != original:
            html_file.write_text(content, encoding="utf-8")
            updated += 1

    return updated


def main() -> None:
    """Quarto post-render entry point."""
    output_dir = Path(os.environ.get("QUARTO_PROJECT_OUTPUT_DIR", str(SITE_DIR)))
    inject_analytics_pixel(output_dir)


if __name__ == "__main__":
    main()
