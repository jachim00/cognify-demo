"""
Wstrzykuje <script defer src="/cookies.js"></script> do <head> każdego HTML
oraz link "Ustawienia cookies" w footerze (per język).
Idempotentny — markery COGNIFY-COOKIES.
"""
from __future__ import annotations
from pathlib import Path
import sys, re

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent
MARKER_SCRIPT = "<!-- COGNIFY-COOKIES SCRIPT -->"
MARKER_LINK_START = "<!-- COGNIFY-COOKIES LINK START -->"
MARKER_LINK_END = "<!-- COGNIFY-COOKIES LINK END -->"

SCRIPT_TAG = f'{MARKER_SCRIPT}\n  <script defer src="/cookies.js"></script>'

LINK_LABEL = {
    "pl": "Ustawienia cookies",
    "en": "Cookie settings",
    "de": "Cookie-Einstellungen",
    "fr": "Paramètres cookies",
    "no": "Innstillinger for cookies",
    "hu": "Süti beállítások",
}

def lang_of(rel: str) -> str:
    p = rel.split("/")
    return p[0] if p[0] in ("en","de","fr","no","hu") else "pl"

def inject_script(content: str) -> tuple[str, int]:
    if MARKER_SCRIPT in content:
        return content, 0
    if "</head>" not in content:
        return content, 0
    return content.replace("</head>", f"  {SCRIPT_TAG}\n</head>", 1), 1

def inject_cookie_link(content: str, lang: str) -> tuple[str, int]:
    """Dodaje link 'Ustawienia cookies' w footerze (przy linkach do polityki prywatności / regulaminu)."""
    if MARKER_LINK_START in content:
        return content, 0
    label = LINK_LABEL[lang]
    new_link = (
        f'{MARKER_LINK_START}'
        f'<a href="#" onclick="event.preventDefault(); '
        f'(window.cognifyOpenCookieSettings||function(){{alert(\'Cookies skrypt jeszcze się ładuje…\');}})();" '
        f'class="hover:text-slate-300 transition">{label}</a>'
        f'{MARKER_LINK_END}'
    )

    # Wstaw obok linku do polityki prywatności w footerze (każdy język)
    # PL: polityka-prywatnosci.html / EN+others: privacy.html
    # Linki przed naszym refactorem mogły być z .html, po refactorze są pretty.
    # Spróbujmy oba warianty.
    patterns_pl = [
        r'(<a\s+href="(?:/)?polityka-prywatnosci(?:\.html)?"[^>]*>[^<]+</a>)',
    ]
    patterns_other = [
        r'(<a\s+href="(?:/)?(?:' + lang + r'/)?privacy(?:\.html)?"[^>]*>[^<]+</a>)',
    ]
    patterns = patterns_pl if lang == "pl" else patterns_other

    for pat in patterns:
        m = re.search(pat, content)
        if m:
            # Wstaw nasz link tuż PO linku do polityki
            new_content = content[:m.end()] + "\n            " + new_link + content[m.end():]
            return new_content, 1
    return content, 0


HTML_FILES = []
for p in ROOT.rglob("*.html"):
    rel = p.relative_to(ROOT).as_posix()
    if "bolek.html" in rel:  # redirect stub
        continue
    HTML_FILES.append(rel)


def main():
    print("=" * 60)
    print("Cognify — cookie banner injection")
    print("=" * 60)
    print()

    s_count = 0
    l_count = 0
    for rel in sorted(HTML_FILES):
        p = ROOT / rel
        text = p.read_text(encoding="utf-8")
        orig = text
        lang = lang_of(rel)
        text, n_s = inject_script(text)
        text, n_l = inject_cookie_link(text, lang)
        if text != orig:
            p.write_text(text, encoding="utf-8")
        s_count += n_s
        l_count += n_l
        flag = "+" if (n_s or n_l) else "."
        print(f"  {flag} {rel:<32} script={n_s} footer_link={n_l}")

    print()
    print(f"Done — script: {s_count} files, footer link: {l_count} files")
    print("Test lokalnie: otwórz index.html — banner powinien wyskoczyć od dołu.")
    print("Reset: w konsoli przeglądarki → cognifyResetConsent()")

if __name__ == "__main__":
    main()
