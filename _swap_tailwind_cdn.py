"""
Replace Tailwind CDN with compiled static CSS file in every HTML.

Removes:
  <script src="https://cdn.tailwindcss.com"></script>
  <script>tailwind.config = { ... };</script>   (multiline)

Adds:
  <link rel="stylesheet" href="<PREFIX>tailwind.css">

Where <PREFIX> is the relative path from the file to repo root.
"""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent

CDN_SCRIPT_RE = re.compile(
    r'\s*<script\s+src="https://cdn\.tailwindcss\.com"></script>\s*\n', re.MULTILINE
)
INLINE_CONFIG_RE = re.compile(
    r'\s*<script>\s*\n\s*tailwind\.config\s*=\s*\{.*?\};\s*\n\s*</script>\s*\n',
    re.DOTALL,
)


def depth_to_prefix(html_path: Path) -> str:
    parts = html_path.relative_to(ROOT).parts
    up = len(parts) - 1
    return "../" * up if up > 0 else ""


def process(html_path: Path) -> bool:
    content = html_path.read_text(encoding="utf-8")
    if "cdn.tailwindcss.com" not in content:
        return False
    # Remove both blocks
    new = CDN_SCRIPT_RE.sub("\n", content)
    new = INLINE_CONFIG_RE.sub("\n", new)
    if new == content:
        print(f"  WARN: pattern didn't match in {html_path}")
        return False
    # Inject <link> right after <noscript>...fonts.googleapis...</noscript> line
    # (after the font preload block, before any <style>)
    prefix = depth_to_prefix(html_path)
    link_tag = f'  <link rel="stylesheet" href="{prefix}tailwind.css">\n'
    # Try to inject after the noscript font fallback
    m = re.search(r'<noscript><link[^>]*googleapis[^>]*></noscript>\s*\n', new)
    if m:
        new = new[: m.end()] + link_tag + new[m.end() :]
    else:
        # Fallback: inject before </head>
        new = new.replace("</head>", link_tag + "</head>", 1)
    html_path.write_text(new, encoding="utf-8")
    return True


def main() -> int:
    count = 0
    for f in sorted(ROOT.rglob("*.html")):
        if ".git" in f.parts or ".playwright-mcp" in f.parts or "node_modules" in f.parts:
            continue
        if process(f):
            count += 1
    print(f"Swapped Tailwind CDN to static CSS in {count} HTML files")
    return 0


if __name__ == "__main__":
    main()
