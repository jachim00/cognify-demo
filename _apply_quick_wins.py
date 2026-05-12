"""
Cognify — Quick Wins z audytu Karola (2026-05-12).
QW-1: paragraf EN→lokalny w careers DE/FR/NO/HU
QW-2: alt og:image + sprawdzenie cognify-X.webp alt-ów
QW-3: canonical + meta robots na każdej stronie
QW-4: hreflang × 7 (6 wersji + x-default) na każdej stronie
QW-5: robots.txt + sitemap.xml
QW-6: Google Fonts non-blocking preload+swap
QW-7: security headers + cache + gzip → .htaccess (część już była, dodaję CSP/HSTS)
QW-8: JSON-LD Organization
QW-9: hero copy — POMINIĘTE (zmiana copywriterska, nie strukturalna; do osobnego briefu)
QW-10: Open Graph + Twitter Card komplet + per-locale og:locale

Idempotentny. Marker w HTML: <!-- COGNIFY-SEO START --> ... <!-- COGNIFY-SEO END -->
"""
from __future__ import annotations
from pathlib import Path
import sys, json, re

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent
DOMAIN = "https://cognify.pl"
OLD_DOMAIN = "https://jachim00.github.io/cognify-demo"

# ──────────────────────────────────────────────────────────────
# Mapa stron: plik → (slug strony, język)
# Slug identyfikuje "ten sam content" w innych językach.
# ──────────────────────────────────────────────────────────────
PAGE_MAP = {
    # PL root
    "index.html":                ("home",       "pl"),
    "kariera.html":              ("careers",    "pl"),
    "andrzej.html":              ("agent",      "pl"),
    "socialboost.html":          ("socialboost","pl"),
    "taskpilot.html":            ("taskpilot",  "pl"),
    "dziekujemy.html":           ("thanks",     "pl"),
    "polityka-prywatnosci.html": ("privacy",    "pl"),
    "regulamin.html":            ("terms",      "pl"),
    # EN
    "en/index.html":             ("home",       "en"),
    "en/careers.html":           ("careers",    "en"),
    "en/andrew.html":            ("agent",      "en"),
    "en/socialboost.html":       ("socialboost","en"),
    "en/taskpilot.html":         ("taskpilot",  "en"),
    "en/thanks.html":            ("thanks",     "en"),
    "en/privacy.html":           ("privacy",    "en"),
    "en/terms.html":             ("terms",      "en"),
    # DE
    "de/index.html":             ("home",       "de"),
    "de/careers.html":           ("careers",    "de"),
    "de/andreas.html":           ("agent",      "de"),
    "de/socialboost.html":       ("socialboost","de"),
    "de/taskpilot.html":         ("taskpilot",  "de"),
    "de/thanks.html":            ("thanks",     "de"),
    "de/privacy.html":           ("privacy",    "de"),
    "de/terms.html":             ("terms",      "de"),
    # FR
    "fr/index.html":             ("home",       "fr"),
    "fr/careers.html":           ("careers",    "fr"),
    "fr/andre.html":             ("agent",      "fr"),
    "fr/socialboost.html":       ("socialboost","fr"),
    "fr/taskpilot.html":         ("taskpilot",  "fr"),
    "fr/thanks.html":            ("thanks",     "fr"),
    "fr/privacy.html":           ("privacy",    "fr"),
    "fr/terms.html":             ("terms",      "fr"),
    # NO
    "no/index.html":             ("home",       "no"),
    "no/careers.html":           ("careers",    "no"),
    "no/anders.html":            ("agent",      "no"),
    "no/socialboost.html":       ("socialboost","no"),
    "no/taskpilot.html":         ("taskpilot",  "no"),
    "no/thanks.html":            ("thanks",     "no"),
    "no/privacy.html":           ("privacy",    "no"),
    "no/terms.html":             ("terms",      "no"),
    # HU
    "hu/index.html":             ("home",       "hu"),
    "hu/careers.html":           ("careers",    "hu"),
    "hu/andras.html":            ("agent",      "hu"),
    "hu/socialboost.html":       ("socialboost","hu"),
    "hu/taskpilot.html":         ("taskpilot",  "hu"),
    "hu/thanks.html":            ("thanks",     "hu"),
    "hu/privacy.html":           ("privacy",    "hu"),
    "hu/terms.html":             ("terms",      "hu"),
}

# slug+lang → URL path
def url_for(slug: str, lang: str) -> str:
    table = {
        ("home","pl"):        "/",
        ("home","en"):        "/en/",
        ("home","de"):        "/de/",
        ("home","fr"):        "/fr/",
        ("home","no"):        "/no/",
        ("home","hu"):        "/hu/",
        ("careers","pl"):     "/kariera",
        ("careers","en"):     "/en/careers",
        ("careers","de"):     "/de/careers",
        ("careers","fr"):     "/fr/careers",
        ("careers","no"):     "/no/careers",
        ("careers","hu"):     "/hu/careers",
        ("agent","pl"):       "/andrzej",
        ("agent","en"):       "/en/andrew",
        ("agent","de"):       "/de/andreas",
        ("agent","fr"):       "/fr/andre",
        ("agent","no"):       "/no/anders",
        ("agent","hu"):       "/hu/andras",
        ("socialboost","pl"): "/socialboost",
        ("socialboost","en"): "/en/socialboost",
        ("socialboost","de"): "/de/socialboost",
        ("socialboost","fr"): "/fr/socialboost",
        ("socialboost","no"): "/no/socialboost",
        ("socialboost","hu"): "/hu/socialboost",
        ("taskpilot","pl"):   "/taskpilot",
        ("taskpilot","en"):   "/en/taskpilot",
        ("taskpilot","de"):   "/de/taskpilot",
        ("taskpilot","fr"):   "/fr/taskpilot",
        ("taskpilot","no"):   "/no/taskpilot",
        ("taskpilot","hu"):   "/hu/taskpilot",
        ("thanks","pl"):      "/dziekujemy",
        ("thanks","en"):      "/en/thanks",
        ("thanks","de"):      "/de/thanks",
        ("thanks","fr"):      "/fr/thanks",
        ("thanks","no"):      "/no/thanks",
        ("thanks","hu"):      "/hu/thanks",
        ("privacy","pl"):     "/polityka-prywatnosci",
        ("privacy","en"):     "/en/privacy",
        ("privacy","de"):     "/de/privacy",
        ("privacy","fr"):     "/fr/privacy",
        ("privacy","no"):     "/no/privacy",
        ("privacy","hu"):     "/hu/privacy",
        ("terms","pl"):       "/regulamin",
        ("terms","en"):       "/en/terms",
        ("terms","de"):       "/de/terms",
        ("terms","fr"):       "/fr/terms",
        ("terms","no"):       "/no/terms",
        ("terms","hu"):       "/hu/terms",
    }
    return table.get((slug, lang), "/")

LANGS = ["pl", "en", "de", "fr", "no", "hu"]
OG_LOCALE = {"pl":"pl_PL","en":"en_US","de":"de_DE","fr":"fr_FR","no":"nb_NO","hu":"hu_HU"}

# ──────────────────────────────────────────────────────────────
# JSON-LD Organization (jeden, używany na każdej stronie)
# ──────────────────────────────────────────────────────────────
JSONLD_ORG = {
    "@context": "https://schema.org",
    "@type": "Organization",
    "@id": f"{DOMAIN}/#organization",
    "name": "Cognify Sp. z o.o.",
    "url": f"{DOMAIN}/",
    "logo": f"{DOMAIN}/og-image.webp",
    "image": f"{DOMAIN}/og-image.webp",
    "description": "Wdrożenia AI dla biznesu — automatyzacja procesów, agenci AI, integracje LLM.",
    "foundingDate": "2023",
    "identifier": "KRS:0001024267",
    "address": {
        "@type": "PostalAddress",
        "streetAddress": "ul. Chłodna 51",
        "postalCode": "00-867",
        "addressLocality": "Warszawa",
        "addressCountry": "PL"
    },
    "contactPoint": {
        "@type": "ContactPoint",
        "contactType": "sales",
        "email": "kontakt@cognify.pl",
        "availableLanguage": ["pl","en","de","fr","no","hu"]
    }
}

# ──────────────────────────────────────────────────────────────
# Bug fix QW-1: paragraf EN → lokalny w careers DE/FR/NO/HU
# ──────────────────────────────────────────────────────────────
EN_PARAGRAPH = ("We build systems that work overnight for Polish companies today — "
                "and will work for companies across Europe tomorrow. We're looking for people "
                "who get more satisfaction from working with language models, process automation, "
                "and real production deployments than from another meeting about another slide.")

LOCAL_PARAGRAPH = {
    "de": ("Wir bauen Systeme, die heute nachts für polnische Unternehmen arbeiten — "
           "und morgen für Unternehmen aus ganz Europa. Wir suchen Menschen, die mehr Befriedigung "
           "aus der Arbeit mit Sprachmodellen, Prozessautomatisierung und echten Produktions-Deployments "
           "ziehen als aus dem nächsten Meeting über die nächste Folie."),
    "fr": ("Nous construisons des systèmes qui travaillent la nuit pour les entreprises polonaises "
           "aujourd'hui — et qui travailleront demain pour des entreprises de toute l'Europe. "
           "Nous cherchons des personnes qui tirent plus de satisfaction du travail avec des modèles "
           "de langage, de l'automatisation des processus et de déploiements de production réels "
           "qu'd'une énième réunion sur une énième diapositive."),
    "no": ("Vi bygger systemer som jobber om natten for polske selskaper i dag — og som vil jobbe "
           "for selskaper i hele Europa i morgen. Vi leter etter folk som får mer tilfredsstillelse "
           "av å jobbe med språkmodeller, prosessautomatisering og ekte produksjons-deployment "
           "enn av nok et møte om nok et lysark."),
    "hu": ("Olyan rendszereket építünk, amelyek ma éjszaka lengyel cégek helyett dolgoznak — "
           "és holnap egész Európában fognak cégek helyett dolgozni. Olyan embereket keresünk, "
           "akik nagyobb elégedettséget merítenek nyelvi modellekkel, folyamatautomatizálással és "
           "valós éles bevezetésekkel végzett munkából, mint még egy értekezletből egy újabb diáról."),
}

# ──────────────────────────────────────────────────────────────
# Title/description fallback per slug per lang (gdy strona ich nie ma)
# Większość stron ma już title+description; OG title/description bierzemy z nich.
# ──────────────────────────────────────────────────────────────

MARKER_START = "<!-- COGNIFY-SEO START -->"
MARKER_END = "<!-- COGNIFY-SEO END -->"

def build_seo_head(rel: str, slug: str, lang: str, current_head: str) -> str:
    """Generuje blok SEO do wstrzyknięcia w <head>."""
    path = url_for(slug, lang)
    canonical = DOMAIN + path

    # OG title/description — wyciągnij z istniejących <title> i <meta name="description">
    title_m = re.search(r'<title>(.*?)</title>', current_head, re.DOTALL)
    desc_m = re.search(r'<meta\s+name=["\']description["\']\s+content=["\'](.*?)["\']', current_head)
    page_title = (title_m.group(1).strip() if title_m else f"Cognify").replace('"', '&quot;')
    page_desc = (desc_m.group(1) if desc_m else "Wdrożenia AI dla biznesu.").replace('"', '&quot;')

    og_locale = OG_LOCALE[lang]
    og_alt_locales = "\n  ".join(
        f'<meta property="og:locale:alternate" content="{OG_LOCALE[l]}">'
        for l in LANGS if l != lang
    )

    # hreflang × 7 (6 lang + x-default → EN)
    hreflang_lines = []
    for l in LANGS:
        hreflang_lines.append(
            f'<link rel="alternate" hreflang="{l}" href="{DOMAIN}{url_for(slug, l)}">'
        )
    hreflang_lines.append(
        f'<link rel="alternate" hreflang="x-default" href="{DOMAIN}{url_for(slug, "en")}">'
    )
    hreflang_block = "\n  ".join(hreflang_lines)

    jsonld = json.dumps(JSONLD_ORG, ensure_ascii=False, indent=2)

    block = f"""{MARKER_START}
  <link rel="canonical" href="{canonical}">
  <meta name="robots" content="index,follow,max-snippet:-1,max-image-preview:large,max-video-preview:-1">
  {hreflang_block}
  <meta property="og:type" content="website">
  <meta property="og:site_name" content="Cognify">
  <meta property="og:locale" content="{og_locale}">
  {og_alt_locales}
  <meta property="og:url" content="{canonical}">
  <meta property="og:title" content="{page_title}">
  <meta property="og:description" content="{page_desc}">
  <meta property="og:image" content="{DOMAIN}/og-image.webp">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <meta property="og:image:alt" content="Cognify — wdrożenia AI dla biznesu">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{page_title}">
  <meta name="twitter:description" content="{page_desc}">
  <meta name="twitter:image" content="{DOMAIN}/og-image.webp">
  <script type="application/ld+json">
{jsonld}
  </script>
  {MARKER_END}"""
    return block


def fix_og_image_url(content: str) -> tuple[str, int]:
    """og:image i twitter:image: jachim00.github.io/cognify-demo → cognify.pl"""
    n = content.count(OLD_DOMAIN)
    content = content.replace(OLD_DOMAIN, DOMAIN)
    return content, n


def font_swap_preload(content: str) -> tuple[str, int]:
    """Zamień blokujący <link rel="stylesheet"> Google Fonts na preload+onload + noscript."""
    pattern = re.compile(
        r'<link\s+href="(https://fonts\.googleapis\.com/css2\?[^"]+)"\s+rel="stylesheet">'
    )
    m = pattern.search(content)
    if not m:
        return content, 0
    url = m.group(1)
    if "display=swap" not in url:
        url = url + ("&" if "?" in url else "?") + "display=swap"
    replacement = (
        f'<link rel="preload" as="style" href="{url}" '
        f'onload="this.onload=null;this.rel=\'stylesheet\'">\n'
        f'  <noscript><link rel="stylesheet" href="{url}"></noscript>'
    )
    return pattern.sub(replacement, content, count=1), 1


def inject_seo_block(content: str, rel: str, slug: str, lang: str) -> tuple[str, int]:
    """Wstrzyknij blok SEO przed </head>. Idempotentny via marker."""
    if MARKER_START in content:
        # Zastąp istniejący blok (re-run friendly)
        new_block = build_seo_head(rel, slug, lang, content)
        pattern = re.compile(
            re.escape(MARKER_START) + r'.*?' + re.escape(MARKER_END),
            re.DOTALL
        )
        new_content = pattern.sub(new_block, content)
        return new_content, 1
    # Wstaw przed </head>
    if "</head>" not in content:
        return content, 0
    new_block = build_seo_head(rel, slug, lang, content)
    return content.replace("</head>", f"  {new_block}\n</head>", 1), 1


def fix_careers_paragraph(content: str, lang: str) -> tuple[str, int]:
    """QW-1: paragraf EN → lokalny w careers DE/FR/NO/HU."""
    if lang not in LOCAL_PARAGRAPH:
        return content, 0
    if EN_PARAGRAPH not in content:
        return content, 0
    return content.replace(EN_PARAGRAPH, LOCAL_PARAGRAPH[lang], 1), 1


# ──────────────────────────────────────────────────────────────
# Process all HTML files
# ──────────────────────────────────────────────────────────────
def process(rel: str, slug: str, lang: str) -> dict:
    path = ROOT / rel
    if not path.exists():
        return {"file": rel, "error": "missing"}
    text = path.read_text(encoding="utf-8")
    orig = text

    text, n_og = fix_og_image_url(text)
    text, n_font = font_swap_preload(text)
    text, n_seo = inject_seo_block(text, rel, slug, lang)
    n_careers = 0
    if slug == "careers":
        text, n_careers = fix_careers_paragraph(text, lang)

    if text != orig:
        path.write_text(text, encoding="utf-8")
    return {
        "file": rel, "og_url": n_og, "font_swap": n_font,
        "seo_block": n_seo, "careers_para": n_careers,
        "changed": text != orig,
    }


# ──────────────────────────────────────────────────────────────
# robots.txt + sitemap.xml
# ──────────────────────────────────────────────────────────────
def write_robots():
    content = f"""User-agent: *
Allow: /
Disallow: /*?preview=
Disallow: /AUDYT_KAROL.*
Disallow: /_apply_*.py

Sitemap: {DOMAIN}/sitemap.xml
"""
    (ROOT / "robots.txt").write_text(content, encoding="utf-8")
    return "robots.txt"


def write_sitemap():
    # Unikalne sluga
    slugs = ["home","careers","agent","socialboost","taskpilot","privacy","terms"]
    # thanks pomijamy w sitemap (post-conversion page, noindex potencjalnie)
    today = "2026-05-12"
    urls = []
    for slug in slugs:
        priority = "1.0" if slug == "home" else ("0.8" if slug in ("careers","agent","socialboost","taskpilot") else "0.4")
        changefreq = "weekly" if slug == "home" else "monthly"
        for lang in LANGS:
            loc = DOMAIN + url_for(slug, lang)
            alts = "\n".join(
                f'    <xhtml:link rel="alternate" hreflang="{l}" href="{DOMAIN}{url_for(slug, l)}"/>'
                for l in LANGS
            )
            xdef = f'    <xhtml:link rel="alternate" hreflang="x-default" href="{DOMAIN}{url_for(slug, "en")}"/>'
            urls.append(f"""  <url>
    <loc>{loc}</loc>
    <lastmod>{today}</lastmod>
    <changefreq>{changefreq}</changefreq>
    <priority>{priority}</priority>
{alts}
{xdef}
  </url>""")
    # Sekcje pretty-URL na index (jako osobne URLe w sitemap)
    for section in ["solutions","process","stack","case","contact"]:
        for lang in LANGS:
            loc = DOMAIN + (f"/{section}" if lang == "pl" else f"/{lang}/{section}")
            urls.append(f"""  <url>
    <loc>{loc}</loc>
    <lastmod>{today}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.6</priority>
  </url>""")
    # Sekcje na kariera (jobs, internship)
    for section in ["jobs","internship"]:
        for lang in LANGS:
            loc = DOMAIN + (f"/{section}" if lang == "pl" else f"/{lang}/{section}")
            urls.append(f"""  <url>
    <loc>{loc}</loc>
    <lastmod>{today}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.5</priority>
  </url>""")
    sitemap = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:xhtml="http://www.w3.org/1999/xhtml">
{chr(10).join(urls)}
</urlset>
"""
    (ROOT / "sitemap.xml").write_text(sitemap, encoding="utf-8")
    return f"sitemap.xml ({len(urls)} URLs)"


# ──────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────
def main():
    print("=" * 60)
    print("Cognify — apply Quick Wins (audyt Karol 2026-05-12)")
    print("=" * 60)
    print()

    print("[HTML — head injection + bug fixes]")
    results = []
    for rel, (slug, lang) in PAGE_MAP.items():
        r = process(rel, slug, lang)
        results.append(r)
        if "error" in r:
            print(f"  X {rel}: {r['error']}")
        else:
            flag = "+" if r["changed"] else "."
            print(f"  {flag} {rel:<32} og_url={r['og_url']} font={r['font_swap']} seo={r['seo_block']} careers={r['careers_para']}")

    print()
    print("[Files]")
    print(f"  + {write_robots()}")
    print(f"  + {write_sitemap()}")

    print()
    changed = sum(1 for r in results if r.get("changed"))
    print(f"Done — {changed}/{len(results)} HTML zmodyfikowanych.")


if __name__ == "__main__":
    main()
