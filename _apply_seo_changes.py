"""
Cognify — jednorazowy skrypt SEO/UX:
  1) ID sekcji: rozwiazania→solutions, jak-pracujemy→process,
     kontakt→contact, oferty→jobs, staz→internship
  2) href="#X"  →  href="/[lang]/Y" (per slug per język)
  3) href="(../)?index.html#X" → href="/[lang]/Y" (cross-page z portfolio)
  4) Inject JS scroll handler przed </body>
  5) Update H1 per plik (PL/EN/DE/FR/NO/HU; index + kariera)

Bezpieczny: idempotentny (powtórne uruchomienie nic nie psuje), wypisuje diff-summary.
"""
from __future__ import annotations
from pathlib import Path
import sys

# Force UTF-8 stdout on Windows (cp1250 default crashes on unicode)
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent
LANGS = ("en", "de", "fr", "no", "hu")

# ──────────────────────────────────────────────────────────────
# Mapy
# ──────────────────────────────────────────────────────────────
ID_MAP = {
    "rozwiazania": "solutions",
    "jak-pracujemy": "process",
    "kontakt": "contact",
    "oferty": "jobs",
    "staz": "internship",
}
# stack, case — bez zmian, ale obecne w żabnich linkach
ANCHOR_SLUGS = list(ID_MAP.keys()) + ["stack", "case"]
SLUG_RENAME = {**ID_MAP, "stack": "stack", "case": "case"}

# ──────────────────────────────────────────────────────────────
# JS scroll handler
# ──────────────────────────────────────────────────────────────
SCROLL_JS = """  <!-- Cognify: pretty-URL scroll handler (.htaccess przekazuje ?s=section) -->
  <script>
  (function () {
    var SECTION_SLUGS = /^(solutions|process|stack|case|contact|jobs|internship)$/i;
    var SECTION_PATH = /^\\/(?:[a-z]{2}\\/)?(solutions|process|stack|case|contact|jobs|internship)\\/?$/i;

    function scrollToId(id) {
      var el = document.getElementById(id);
      if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    // 1) Pretty URL load (?s=stack lub #stack)
    var q = new URLSearchParams(location.search);
    var s = q.get('s');
    var hash = location.hash.replace(/^#/, '');
    var target = (s && SECTION_SLUGS.test(s)) ? s : (hash && SECTION_SLUGS.test(hash) ? hash : null);

    if (s) {
      q.delete('s');
      var qs = q.toString();
      history.replaceState(null, '', location.pathname + (qs ? '?' + qs : ''));
    }

    function init() { if (target) scrollToId(target); }
    if (document.readyState === 'complete') init();
    else window.addEventListener('load', function () { setTimeout(init, 30); });

    // 2) Klik w /solutions itp. NA TEJ samej stronie: bez reloadu
    document.addEventListener('click', function (e) {
      var a = e.target.closest && e.target.closest('a[href]');
      if (!a) return;
      if (a.target === '_blank' || e.metaKey || e.ctrlKey || e.shiftKey) return;
      var href = a.getAttribute('href');
      if (!href) return;
      var url;
      try { url = new URL(href, location.href); } catch (err) { return; }
      if (url.origin !== location.origin) return;
      var m = url.pathname.match(SECTION_PATH);
      if (!m) return;
      var slug = m[1].toLowerCase();
      if (!document.getElementById(slug)) return;  // sekcja nie istnieje tutaj → reload (zgodnie z htaccess)
      e.preventDefault();
      scrollToId(slug);
      history.pushState(null, '', url.pathname + url.search);
    });
  })();
  </script>
"""

# ──────────────────────────────────────────────────────────────
# H1 — pary (old, new) per plik względem ROOT
# ──────────────────────────────────────────────────────────────
H1 = {
    "index.html": (
        '        Twoja firma.<br>\n'
        '        <span class="text-gradient">Lepsza dzięki AI.</span><br>\n'
        '        <span class="text-slate-300 font-light">Bez zwiększania zespołu.</span>',
        '        Wdrożenia AI dla biznesu.<br>\n'
        '        <span class="text-gradient">Twoja firma — lepsza dzięki AI.</span><br>\n'
        '        <span class="text-slate-300 font-light">Bez zwiększania zespołu.</span>',
    ),
    "kariera.html": (
        '        Buduj AI <span class="text-gradient">z nami.</span>',
        '        Kariera w Cognify — <span class="text-gradient">buduj AI z nami.</span>',
    ),
    "en/index.html": (
        '        Your company.<br>\n'
        '        <span class="text-gradient">Better with AI.</span><br>\n'
        '        <span class="text-slate-300 font-light">Without growing your team.</span>',
        '        AI implementations for business.<br>\n'
        '        <span class="text-gradient">Your company — better with AI.</span><br>\n'
        '        <span class="text-slate-300 font-light">Without growing your team.</span>',
    ),
    "en/careers.html": (
        '        Build AI <span class="text-gradient">with us.</span>',
        '        Careers at Cognify — <span class="text-gradient">build AI with us.</span>',
    ),
    "de/index.html": (
        '        Ihr Unternehmen.<br>\n'
        '        <span class="text-gradient">Besser mit KI.</span><br>\n'
        '        <span class="text-slate-300 font-light">Ohne Team-Erweiterung.</span>',
        '        KI-Implementierungen für Unternehmen.<br>\n'
        '        <span class="text-gradient">Ihr Unternehmen — besser mit KI.</span><br>\n'
        '        <span class="text-slate-300 font-light">Ohne Team-Erweiterung.</span>',
    ),
    "de/careers.html": (
        '        Bauen Sie KI <span class="text-gradient">mit uns.</span>',
        '        Karriere bei Cognify — <span class="text-gradient">gestalte KI mit uns.</span>',
    ),
    "fr/index.html": (
        '        Votre entreprise.<br>\n'
        '        <span class="text-gradient">Plus performante grâce à l\'IA.</span><br>\n'
        '        <span class="text-slate-300 font-light">Sans agrandir l\'équipe.</span>',
        '        Implémentations IA pour entreprises.<br>\n'
        '        <span class="text-gradient">Votre entreprise — plus performante grâce à l\'IA.</span><br>\n'
        '        <span class="text-slate-300 font-light">Sans agrandir l\'équipe.</span>',
    ),
    "fr/careers.html": (
        '        Construisez l\'IA <span class="text-gradient">avec nous.</span>',
        '        Carrières chez Cognify — <span class="text-gradient">construisez l\'IA avec nous.</span>',
    ),
    "no/index.html": (
        '        Bedriften din.<br>\n'
        '        <span class="text-gradient">Bedre med KI.</span><br>\n'
        '        <span class="text-slate-300 font-light">Uten å utvide teamet.</span>',
        '        KI-implementeringer for bedrifter.<br>\n'
        '        <span class="text-gradient">Bedriften din — bedre med KI.</span><br>\n'
        '        <span class="text-slate-300 font-light">Uten å utvide teamet.</span>',
    ),
    "no/careers.html": (
        '        Bygg KI <span class="text-gradient">med oss.</span>',
        '        Karriere hos Cognify — <span class="text-gradient">bygg KI med oss.</span>',
    ),
    "hu/index.html": (
        '        A vállalata.<br>\n'
        '        <span class="text-gradient">Jobban AI-val.</span><br>\n'
        '        <span class="text-slate-300 font-light">Csapatnövelés nélkül.</span>',
        '        MI-bevezetések cégeknek.<br>\n'
        '        <span class="text-gradient">A vállalata — jobban MI-vel.</span><br>\n'
        '        <span class="text-slate-300 font-light">Csapatnövelés nélkül.</span>',
    ),
    "hu/careers.html": (
        '        Építsd az AI-t <span class="text-gradient">velünk.</span>',
        '        Karrier a Cognifyben — <span class="text-gradient">építsd velünk az MI-t.</span>',
    ),
}

# ──────────────────────────────────────────────────────────────
# Klasyfikacja plików
# ──────────────────────────────────────────────────────────────
MAIN_FILES = list(H1.keys())  # dostają wszystko: id + href + JS + H1

# Cross-page (podstrony portfolio + thanks) — TYLKO href rewrite (mają linki do index.html#X)
SUBPAGES = [
    "andrzej.html", "bolek.html", "socialboost.html", "taskpilot.html",
    "dziekujemy.html", "polityka-prywatnosci.html", "regulamin.html",
    "en/andrew.html", "en/socialboost.html", "en/taskpilot.html", "en/thanks.html",
    "en/privacy.html", "en/terms.html",
    "de/andreas.html", "de/socialboost.html", "de/taskpilot.html", "de/thanks.html",
    "de/privacy.html", "de/terms.html",
    "fr/andre.html", "fr/socialboost.html", "fr/taskpilot.html", "fr/thanks.html",
    "fr/privacy.html", "fr/terms.html",
    "no/anders.html", "no/socialboost.html", "no/taskpilot.html", "no/thanks.html",
    "no/privacy.html", "no/terms.html",
    "hu/andras.html", "hu/socialboost.html", "hu/taskpilot.html", "hu/thanks.html",
    "hu/privacy.html", "hu/terms.html",
]

# ──────────────────────────────────────────────────────────────
# Transformacje
# ──────────────────────────────────────────────────────────────
def lang_of(rel: str) -> str:
    parts = rel.split("/")
    if parts[0] in LANGS:
        return parts[0]
    return ""  # PL root

def url_prefix(lang: str) -> str:
    return f"/{lang}" if lang else ""

def rename_ids(content: str) -> tuple[str, int]:
    n = 0
    for old, new in ID_MAP.items():
        before = content
        content = content.replace(f'id="{old}"', f'id="{new}"')
        n += (before != content)
    return content, n

def rewrite_hrefs(content: str, lang: str) -> tuple[str, int]:
    prefix = url_prefix(lang)
    n = 0
    # 1) same-page anchors:  href="#X"  →  href="{prefix}/{new}"
    for slug in ANCHOR_SLUGS:
        new = SLUG_RENAME[slug]
        before = content
        content = content.replace(f'href="#{slug}"', f'href="{prefix}/{new}"')
        if before != content: n += 1
    # 2) cross-page from same-folder subpages: href="index.html#X" → href="{prefix}/{new}"
    for slug in ANCHOR_SLUGS:
        new = SLUG_RENAME[slug]
        before = content
        content = content.replace(f'href="index.html#{slug}"', f'href="{prefix}/{new}"')
        if before != content: n += 1
    # 3) cross-page from /{lang}/subpage: href="../index.html#X" → href="/{lang}/{new}"
    # tu prefix musi być folderem języka subpage, nie pustym (PL root nie używa ../)
    for slug in ANCHOR_SLUGS:
        new = SLUG_RENAME[slug]
        before = content
        content = content.replace(f'href="../index.html#{slug}"', f'href="{prefix}/{new}"')
        if before != content: n += 1
    return content, n

def inject_js(content: str) -> tuple[str, int]:
    if "Cognify: pretty-URL scroll handler" in content:
        return content, 0
    if "</body>" not in content:
        return content, 0
    return content.replace("</body>", SCROLL_JS + "</body>", 1), 1

def update_h1(content: str, rel: str) -> tuple[str, int]:
    pair = H1.get(rel)
    if not pair:
        return content, 0
    old, new = pair
    if new in content:
        return content, 0  # już zaktualizowane
    if old not in content:
        print(f"  ⚠ H1 nie znaleziony w {rel} (może już zmodyfikowany lub inne formatowanie)")
        return content, 0
    return content.replace(old, new, 1), 1

# ──────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────
def process_main(rel: str) -> dict:
    path = ROOT / rel
    if not path.exists():
        return {"file": rel, "error": "missing"}
    text = path.read_text(encoding="utf-8")
    orig = text
    lang = lang_of(rel)
    text, n_ids = rename_ids(text)
    text, n_href = rewrite_hrefs(text, lang)
    text, n_js = inject_js(text)
    text, n_h1 = update_h1(text, rel)
    if text != orig:
        path.write_text(text, encoding="utf-8")
    return {"file": rel, "ids": n_ids, "href_groups": n_href, "js": n_js, "h1": n_h1, "changed": text != orig}

def process_subpage(rel: str) -> dict:
    path = ROOT / rel
    if not path.exists():
        return {"file": rel, "error": "missing"}
    text = path.read_text(encoding="utf-8")
    orig = text
    lang = lang_of(rel)
    text, n_href = rewrite_hrefs(text, lang)
    if text != orig:
        path.write_text(text, encoding="utf-8")
    return {"file": rel, "href_groups": n_href, "changed": text != orig}

def main():
    print("=" * 60)
    print("Cognify — apply SEO/UX changes")
    print("=" * 60)
    print()
    print("[MAIN: id + href + JS + H1]")
    main_stats = [process_main(r) for r in MAIN_FILES]
    for s in main_stats:
        if "error" in s:
            print(f"  ✗ {s['file']}: {s['error']}")
            continue
        flag = "✓" if s["changed"] else "·"
        print(f"  {flag} {s['file']:<28} ids={s['ids']} href_groups={s['href_groups']} js={s['js']} h1={s['h1']}")

    print()
    print("[SUBPAGES: href only]")
    sub_stats = [process_subpage(r) for r in SUBPAGES]
    for s in sub_stats:
        if "error" in s:
            print(f"  ✗ {s['file']}: {s['error']}")
            continue
        flag = "✓" if s["changed"] else "·"
        print(f"  {flag} {s['file']:<32} href_groups={s['href_groups']}")

    print()
    print("Done.")

if __name__ == "__main__":
    main()
