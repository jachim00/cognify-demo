"""
Post-pass after _rewrite_to_clean_urls.py: fixes residual .html references.

1. Lang `careers/index.html` files reference `../../kariera.html` instead of `../../kariera/`
   (root cause: kariera.html was moved manually before the main script ran, so
   the main script's file_map had no entry for /kariera.html).
2. Pre-existing source bug: lang person-pages (en/andrew, de/andreas, fr/andre,
   no/anders, hu/andras) cross-reference each other using a SINGLE filename per
   page (e.g. en/andrew.html lang switcher uses `../andrew.html` for PL → should
   point to /andrzej/, and `../de/andrew.html` for DE → should point to /de/andreas/).
   This is wrong in source; we fix it now since after refactor those .html paths
   are 100% broken.
3. bolek/index.html has a meta refresh + canonical to old .html URL.
"""
from __future__ import annotations
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent

# Per-language slug for the "founder profile" page
PERSON_SLUG = {"pl": "andrzej", "en": "andrew", "de": "andreas", "fr": "andre", "no": "anders", "hu": "andras"}
LANGS = ["en", "de", "fr", "no", "hu"]


def fix_lang_careers_kariera_ref() -> int:
    """Replace `../../kariera.html` with `../../kariera/` in lang careers pages."""
    fixed = 0
    for lang in LANGS:
        f = ROOT / lang / "careers" / "index.html"
        if not f.exists():
            continue
        c = f.read_text(encoding="utf-8")
        new = c.replace('href="../../kariera.html"', 'href="../../kariera/"')
        if new != c:
            f.write_text(new, encoding="utf-8")
            fixed += 1
    return fixed


def fix_person_page_lang_switcher() -> int:
    """
    In each lang's person page (e.g. en/andrew/index.html), the lang switcher
    has wrong filenames for cross-lang links. Fix per language.
    """
    fixed = 0
    for current_lang in LANGS:
        current_slug = PERSON_SLUG[current_lang]
        f = ROOT / current_lang / current_slug / "index.html"
        if not f.exists():
            continue
        c = f.read_text(encoding="utf-8")
        # PL link: ../../{current_slug}.html → ../../andrzej/
        c = c.replace(f'href="../../{current_slug}.html"', 'href="../../andrzej/"')
        # Other langs: ../../<lang>/{current_slug}.html → ../../<lang>/{PERSON_SLUG[lang]}/
        for other_lang in LANGS:
            if other_lang == current_lang:
                continue
            other_slug = PERSON_SLUG[other_lang]
            c = c.replace(
                f'href="../../{other_lang}/{current_slug}.html"',
                f'href="../../{other_lang}/{other_slug}/"',
            )
        f.write_text(c, encoding="utf-8")
        fixed += 1
    return fixed


def fix_bolek_redirect() -> int:
    """bolek/index.html — meta refresh + canonical to old .html URL."""
    f = ROOT / "bolek" / "index.html"
    if not f.exists():
        return 0
    c = f.read_text(encoding="utf-8")
    # Meta refresh: url=andrzej.html → url=../andrzej/
    c = re.sub(
        r'<meta\s+http-equiv="refresh"\s+content="(\d+);\s*url=andrzej\.html"',
        r'<meta http-equiv="refresh" content="\1; url=../andrzej/"',
        c,
    )
    # Canonical to old URL — pointing to github.io URL with .html
    c = c.replace(
        'href="https://jachim00.github.io/cognify-demo/andrzej.html"',
        'href="https://jachim00.github.io/cognify-demo/andrzej/"',
    )
    # Body text mentions "andrzej.html" but it's just display text — keep readable
    # (the actual link href is already correct: ../andrzej/)
    f.write_text(c, encoding="utf-8")
    return 1


def fix_andrzej_lang_switcher() -> int:
    """
    PL andrzej/index.html lang switcher had correct names. After main script
    they should already be ../en/andrew/ etc. Verify nothing slipped.
    """
    f = ROOT / "andrzej" / "index.html"
    if not f.exists():
        return 0
    c = f.read_text(encoding="utf-8")
    bad = re.findall(r'href="[^"]*\.html"', c)
    if bad:
        print(f"  andrzej/index.html has {len(bad)} residual .html: {bad[:3]}")
    return 0


def main() -> int:
    n1 = fix_lang_careers_kariera_ref()
    print(f"Fixed kariera.html refs in {n1} careers pages")
    n2 = fix_person_page_lang_switcher()
    print(f"Fixed person-page lang switcher in {n2} pages")
    n3 = fix_bolek_redirect()
    print(f"Fixed bolek redirect: {n3}")
    fix_andrzej_lang_switcher()
    # Final check
    remaining = 0
    for f in ROOT.rglob("*.html"):
        if ".git" in f.parts or ".playwright-mcp" in f.parts:
            continue
        c = f.read_text(encoding="utf-8")
        bad = re.findall(r'href="(?!https?:|mailto:|tel:|//|#)([^"]*\.html(?:[?#][^"]*)?)"', c)
        if bad:
            print(f"  REMAINING in {f.relative_to(ROOT)}: {bad}")
            remaining += len(bad)
    print(f"Total remaining .html href references: {remaining}")
    return 0


if __name__ == "__main__":
    main()
