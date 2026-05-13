"""
Convert .html URLs to directory-style clean URLs for GitHub Pages.

Each foo.html (except index.html) becomes foo/index.html. Every internal href/src
is rewritten to point at the new clean URL relative to the new file location.
Root-absolute section anchors (/jobs, /solutions, /en/contact, etc.) become
in-page or cross-page #anchor links.

Run from repo root:  python _rewrite_to_clean_urls.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

LANGS = {"en", "de", "fr", "no", "hu"}
SECTION_TO_HOME = {"solutions", "process", "stack", "case", "contact"}
SECTION_TO_CAREERS = {"jobs", "internship"}
CAREERS_SLUG_BY_LANG = {"": "kariera", "en": "careers", "de": "careers", "fr": "careers", "no": "careers", "hu": "careers"}

HREF_RE = re.compile(r'\b(href|src)="([^"]+)"')
FORMSUBMIT_NEXT_RE = re.compile(
    r'value="(https?://cognify\.pl)(?:/(en|de|fr|no|hu))?/([\w-]+)\.html"'
)


def old_site_path(html_file: Path) -> str:
    """Absolute site path BEFORE rewrite. /index.html, /kariera.html, /en/careers.html."""
    return "/" + html_file.relative_to(ROOT).as_posix()


def new_site_path(html_file: Path) -> str:
    """Absolute site path AFTER rewrite. /, /kariera/, /en/, /en/careers/."""
    rel = html_file.relative_to(ROOT).as_posix()
    if rel == "index.html":
        return "/"
    if rel.endswith("/index.html"):
        return "/" + rel[: -len("index.html")]
    if rel.endswith(".html"):
        return "/" + rel[: -len(".html")] + "/"
    return "/" + rel


def new_file_relpath(html_file: Path) -> str:
    """New filesystem path (relative to ROOT) for this file."""
    rel = html_file.relative_to(ROOT).as_posix()
    if rel == "index.html" or rel.endswith("/index.html"):
        return rel
    if rel.endswith(".html"):
        return rel[: -len(".html")] + "/index.html"
    return rel


def expand_section_anchor(path: str) -> str | None:
    """
    /jobs, /en/contact, /de/internship, etc. → new absolute URL with #fragment.
    Returns None if not a section anchor.
    """
    parts = path.strip("/").split("/")
    if len(parts) == 1:
        slug = parts[0]
        if slug in SECTION_TO_HOME:
            return f"/#{slug}"
        if slug in SECTION_TO_CAREERS:
            return f"/{CAREERS_SLUG_BY_LANG['']}/#{slug}"
    elif len(parts) == 2 and parts[0] in LANGS:
        lang, slug = parts
        if slug in SECTION_TO_HOME:
            return f"/{lang}/#{slug}"
        if slug in SECTION_TO_CAREERS:
            return f"/{lang}/{CAREERS_SLUG_BY_LANG[lang]}/#{slug}"
    return None


def normalize(p: str) -> str:
    """Normalize ./ and ../ in a path, keep trailing slash."""
    trailing = p.endswith("/") and len(p) > 1
    parts: list[str] = []
    for seg in p.split("/"):
        if seg in ("", "."):
            continue
        if seg == "..":
            if parts:
                parts.pop()
            continue
        parts.append(seg)
    out = "/" + "/".join(parts)
    if trailing and not out.endswith("/"):
        out += "/"
    return out or "/"


def resolve_to_old_abs(href: str, current_old_path: str) -> str | None:
    """Resolve href value to absolute OLD site path with frag/query preserved."""
    if not href or href.startswith(
        ("http://", "https://", "mailto:", "tel:", "javascript:", "//", "data:")
    ):
        return None
    if href.startswith("#"):
        return None  # in-page anchor — keep as-is
    path_q_frag = href
    path_part, frag_sep, frag = path_q_frag.partition("#")
    path_part, q_sep, q = path_part.partition("?")
    if path_part.startswith("/"):
        abs_p = path_part
    else:
        cur_dir = current_old_path.rsplit("/", 1)[0] + "/"
        abs_p = cur_dir + path_part
    abs_p = normalize(abs_p)
    if path_part.endswith("/") and not abs_p.endswith("/"):
        abs_p += "/"
    out = abs_p
    if q_sep:
        out += "?" + q
    if frag_sep:
        out += "#" + frag
    return out


def map_old_abs_to_new_abs(abs_old: str, file_map: dict[str, str]) -> str:
    """Map an absolute OLD site path to absolute NEW. Handles section anchors."""
    path_part, frag_sep, frag = abs_old.partition("#")
    path_part, q_sep, q = path_part.partition("?")
    if not frag_sep and not q_sep:
        sect = expand_section_anchor(path_part)
        if sect is not None:
            return sect
    new_path = file_map.get(path_part, path_part)
    out = new_path
    if q_sep:
        out += "?" + q
    if frag_sep:
        out += "#" + frag
    return out


def relativize(target_abs: str, from_file_new_abs: str) -> str:
    """
    Compute relative href from a file (at from_file_new_abs, e.g. /kariera/index.html)
    to a target absolute site path (e.g. /en/careers/ or /#jobs or /cookies.js).
    """
    path_part, frag_sep, frag = target_abs.partition("#")
    path_part, q_sep, q = path_part.partition("?")

    from_dir = from_file_new_abs.rsplit("/", 1)[0] + "/"
    target_parts = [p for p in path_part.split("/") if p]
    from_parts = [p for p in from_dir.split("/") if p]
    i = 0
    while i < len(target_parts) and i < len(from_parts) and target_parts[i] == from_parts[i]:
        i += 1
    up = len(from_parts) - i
    rel_parts = [".."] * up + target_parts[i:]
    rel = "/".join(rel_parts)
    if path_part.endswith("/") and rel_parts and not rel.endswith("/"):
        rel += "/"
    if not rel:
        # same dir as current — if there's a fragment/query, drop the path entirely
        if frag_sep or q_sep:
            rel = ""
        else:
            rel = "./"
    out = rel
    if q_sep:
        out += "?" + q
    if frag_sep:
        out += "#" + frag
    return out


def build_file_map(all_html: list[Path]) -> dict[str, str]:
    """Map OLD absolute site path → NEW absolute site path for every HTML."""
    m: dict[str, str] = {}
    for f in all_html:
        old_p = old_site_path(f)
        new_p = new_site_path(f)
        m[old_p] = new_p
        if old_p == "/index.html":
            m["/"] = "/"
        elif old_p.endswith("/index.html"):
            dir_with_slash = old_p[: -len("index.html")]
            m[dir_with_slash] = new_p
            m[dir_with_slash.rstrip("/")] = new_p
        elif old_p.endswith(".html"):
            stem = old_p[: -len(".html")]
            m[stem] = new_p
            m[stem + "/"] = new_p
    return m


def rewrite_content(content: str, old_abs: str, new_file_abs: str, file_map: dict[str, str]) -> str:
    def repl_href(match: re.Match[str]) -> str:
        attr, val = match.group(1), match.group(2)
        target_old = resolve_to_old_abs(val, old_abs)
        if target_old is None:
            return match.group(0)
        target_new = map_old_abs_to_new_abs(target_old, file_map)
        new_val = relativize(target_new, new_file_abs)
        return f'{attr}="{new_val}"'

    out = HREF_RE.sub(repl_href, content)

    def repl_next(match: re.Match[str]) -> str:
        base, lang, slug = match.group(1), match.group(2), match.group(3)
        if lang:
            return f'value="{base}/{lang}/{slug}/"'
        return f'value="{base}/{slug}/"'

    out = FORMSUBMIT_NEXT_RE.sub(repl_next, out)
    return out


def main() -> int:
    all_html = sorted(
        p
        for p in ROOT.rglob("*.html")
        if ".git" not in p.parts and ".playwright-mcp" not in p.parts
    )
    file_map = build_file_map(all_html)
    print(f"Found {len(all_html)} HTML files.")
    print(f"file_map entries: {len(file_map)}")

    moved = 0
    rewritten = 0
    for src in all_html:
        old_abs = old_site_path(src)
        new_fs_rel = new_file_relpath(src)
        new_fs_path = ROOT / new_fs_rel
        new_file_abs = "/" + new_fs_rel

        content = src.read_text(encoding="utf-8")
        new_content = rewrite_content(content, old_abs, new_file_abs, file_map)

        if src.resolve() == new_fs_path.resolve():
            if new_content != content:
                src.write_text(new_content, encoding="utf-8")
                rewritten += 1
        else:
            new_fs_path.parent.mkdir(parents=True, exist_ok=True)
            new_fs_path.write_text(new_content, encoding="utf-8")
            src.unlink()
            moved += 1

    print(f"Moved: {moved}, rewritten in place: {rewritten}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
