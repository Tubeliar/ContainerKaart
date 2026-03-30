#!/usr/bin/env python3
"""
inline_svg.py  —  inlines SVG files as symbols into site/index.html.
Output: site/index.inlined.html
"""

import re
from pathlib import Path

SITE_DIR = Path(__file__).parent.parent / "site"

# In dependency order: each file may reference the ones above it.
SVG_FILES = [
    "container-icon.svg",
    "container-with-litter.svg",
    "container-with-bag.svg",
    "container-with-furniture.svg",
]


def resolve_hrefs(text):
    """Rewrite cross-document SVG hrefs to local fragment IDs."""
    def replace(m):
        q, ref = m.group(1), m.group(2)
        frag = ref.split("#", 1)[1] if "#" in ref else Path(ref).stem
        return f"href={q}#{frag}{q}"
    return re.sub(r'href=(["\'])([^"\']*\.svg(?:#[^"\']*)?)\1', replace, text)


def build_sprite():
    hoisted_defs = []
    symbols = []

    for filename in SVG_FILES:
        text = resolve_hrefs((SITE_DIR / filename).read_text(encoding="utf-8"))
        stem = Path(filename).stem

        # Strip outer <svg ...>...</svg> wrapper.
        inner = re.sub(r'^\s*<svg\b[^>]*>\s*', '', text)
        inner = re.sub(r'\s*</svg>\s*$', '', inner.rstrip())

        # Hoist <defs> blocks to top-level sprite defs so url(#id) gradient
        # references resolve across all browsers regardless of nesting.
        def extract_defs(m):
            hoisted_defs.append(m.group(1).strip())
            return ""
        inner = re.sub(r'\s*<defs>(.*?)</defs>\s*', extract_defs, inner, flags=re.DOTALL)

        if re.match(r'\s*<symbol\b', inner):
            # Already a symbol — drop any trailing <use> (only needed for standalone viewing).
            inner = re.sub(r'\s*<use\b[^/]*/>\s*$', '', inner.rstrip())
            symbols.append(inner.strip())
        else:
            # Wrap the content as a new symbol, grabbing viewBox from the original <svg> tag.
            m = re.search(r'<svg\b[^>]*\bviewBox="([^"]*)"', text)
            if not m:
                w = re.search(r'<svg\b[^>]*\bwidth="([^"]*)"', text)
                h = re.search(r'<svg\b[^>]*\bheight="([^"]*)"', text)
                vb = f"0 0 {w.group(1) if w else '200'} {h.group(1) if h else '200'}"
            else:
                vb = m.group(1)
            symbols.append(f'<symbol id="{stem}" viewBox="{vb}">\n{inner.strip()}\n</symbol>')

    lines = ['<svg style="position:absolute;width:0;height:0;overflow:hidden" aria-hidden="true">']
    if hoisted_defs:
        lines += ["<defs>"] + hoisted_defs + ["</defs>"]
    lines += symbols + ["</svg>"]
    return "\n".join(lines)


html = (SITE_DIR / "index.template.html").read_text(encoding="utf-8")
sprite = build_sprite()
html = resolve_hrefs(html)
html = re.sub(r"(<body\b[^>]*>)", r"\1\n" + sprite, html, count=1)
output_path = SITE_DIR / "index.html"
output_path.write_text(html, encoding="utf-8", newline="\n")
print(f"Written to {output_path}")
