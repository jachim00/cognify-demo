"""
Inject favicon links into <head> of every HTML page.
Computes correct relative path based on file depth.
Idempotent — skips files that already have favicon links.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MARKER_BEGIN = "<!-- COGNIFY-FAVICON -->"
MARKER_END = "<!-- /COGNIFY-FAVICON -->"


def depth_to_prefix(html_path: Path) -> str:
    """File at /a/b/c/index.html → '../../../' for root assets."""
    parts = html_path.relative_to(ROOT).parts
    up = len(parts) - 1
    return "../" * up if up > 0 else ""


def build_favicon_block(prefix: str) -> str:
    return (
        f"{MARKER_BEGIN}\n"
        f'  <link rel="icon" type="image/svg+xml" href="{prefix}favicon.svg">\n'
        f'  <link rel="icon" type="image/x-icon" sizes="any" href="{prefix}favicon.ico">\n'
        f'  <link rel="apple-touch-icon" href="{prefix}apple-touch-icon.png">\n'
        f"  {MARKER_END}"
    )


def inject(html_path: Path) -> bool:
    content = html_path.read_text(encoding="utf-8")
    if MARKER_BEGIN in content:
        return False
    if "favicon.svg" in content or "favicon.ico" in content or "apple-touch-icon" in content:
        return False
    prefix = depth_to_prefix(html_path)
    block = build_favicon_block(prefix)
    # Insert after <meta name="viewport"...> line
    marker = '<meta name="viewport"'
    idx = content.find(marker)
    if idx == -1:
        print(f"  SKIP (no viewport meta): {html_path}")
        return False
    end_of_line = content.find(">", idx) + 1
    new = content[:end_of_line] + "\n  " + block + content[end_of_line:]
    html_path.write_text(new, encoding="utf-8")
    return True


def main() -> int:
    count = 0
    for f in sorted(ROOT.rglob("*.html")):
        if ".git" in f.parts or ".playwright-mcp" in f.parts:
            continue
        if inject(f):
            count += 1
    print(f"Injected favicon links into {count} HTML files")
    return 0


if __name__ == "__main__":
    main()
