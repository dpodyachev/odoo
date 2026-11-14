#!/usr/bin/env python3
"""Генератор статического сайта: src/lang_<xx>.py + config.py → site/<xx>/index.html, impressum.html, datenschutz.html.
Запуск: python3 src/build.py   (без зависимостей; результат коммитится, Cloudflare Pages отдаёт папку site/)."""
import datetime
import hashlib
import re
import html
import importlib
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import config as C  # noqa: E402

OUT = os.path.join(os.path.dirname(HERE), "site")
E = html.escape
YEAR = datetime.date.today().year
VERIFY = "".join(f'<meta name="{E(k)}" content="{E(v)}">\n' for k, v in C.SITE_VERIFY.items())

ICONS = {
    "install": '<path d="M4 7h16M4 12h16M4 17h10"/><circle cx="18" cy="17" r="2"/>',
    "support": '<path d="M12 3a7 7 0 0 0-7 7v4a2 2 0 0 0 2 2h1v-6H6"/><path d="M12 3a7 7 0 0 1 7 7v4a2 2 0 0 1-2 2h-1v-6h2"/><path d="M16 18a4 4 0 0 1-4 3"/>',
    "fix": '<path d="M14.7 6.3a4 4 0 0 0-5.4 5.4L3 18l3 3 6.3-6.3a4 4 0 0 0 5.4-5.4l-2.5 2.5-2.5-.5-.5-2.5z"/>',
    "update": '<path d="M20 11a8 8 0 1 0-2.3 5.7"/><path d="M20 4v7h-7"/>',
    "integration": '<rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/><path d="M10 6.5h4a3 3 0 0 1 3 3V14"/>',
    "server": '<rect x="3" y="4" width="18" height="7" rx="1.5"/><rect x="3" y="13" width="18" height="7" rx="1.5"/><path d="M7 7.5h.01M7 16.5h.01"/>',
}


def asset(path):
    """/assets/x?v=<hash>: браузер кэширует assets на сутки, хэш сбрасывает кэш при изменении файла."""
    with open(os.path.join(OUT, path.lstrip("/")), "rb") as fh:
        return f"{path}?v={hashlib.sha1(fh.read()).hexdigest()[:8]}"


def icon(name):
    return (f'<svg class="ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" '
            f'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{ICONS[name]}</svg>')


def url(lang, page=""):
    # Reader View (Firefox/Safari): секции с классом "extra" Readability отбрасывает — в режиме чтения остаются вводная и цены.
# Cloudflare Pages отдаёт /x.html по адресу /x (308 с .html) — ссылки сразу без расширения
    return f"/{lang}/{page[:-5] if page.endswith('.html') else page}"


def head(T, lang, page, title, desc):
    alts = "\n".join(f'<link rel="alternate" hreflang="{l}" href="{C.BASE_URL}{url(l, page)}">' for l in C.LANGS)
    alts += f'\n<link rel="alternate" hreflang="x-default" href="{C.BASE_URL}{url(C.LANGS[0], page)}">'
    return f"""<!doctype html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{E(title)}</title>
<meta name="description" content="{E(desc)}">
<link rel="canonical" href="{C.BASE_URL}{url(lang, page)}">
{alts}
<meta property="og:title" content="{E(title)}">
<meta property="og:description" content="{E(desc)}">
<meta property="og:type" content="website">
<meta property="og:url" content="{C.BASE_URL}{url(lang, page)}">
<meta name="theme-color" content="#3b2a4a">
{VERIFY}<link rel="icon" href="/assets/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="{asset('/assets/style.css')}">
<script src="{asset('/assets/theme.js')}" defer></script>
</head>
<body>
"""


def flag(l):
    f = C.FLAGS.get(l)
    return f'<img class="flag" src="{asset(f"/assets/flags/{f}.svg")}" alt="" width="20" height="14">' if f else ""


def langswitch(lang, page):
    cur = ' aria-current="true"'
    items = "".join(
        f'<a href="{url(l, page)}" hreflang="{l}" lang="{l}" title="{E(C.LANG_NAMES[l])}" aria-label="{E(C.LANG_NAMES[l])}"{cur if l == lang else ""}>'
        f'{flag(l)}<span class="lc">{l.upper()}</span></a>'
        for l in C.LANGS)
    return f'<nav class="langs" aria-label="Language">{items}</nav>'


def header(T, lang, page):
    nav = "".join(f'<a href="{url(lang)}#{k}">{E(v)}</a>' for k, v in T["nav"].items())
    return f"""<header class="top">
<div class="wrap top-in">
<a class="brand" href="{url(lang)}"><span class="logo">G</span><span>{E(C.BRAND)}<small>{E(C.BRAND_SUB)}</small></span></a>
<nav class="menu">{nav}</nav>
{langswitch(lang, page)}
<button type="button" class="theme" hidden aria-label="{E(T["theme_toggle"])}" title="{E(T["theme_toggle"])}">🌙</button>
</div>
</header>
"""


def book_url():
    return C.CAL_URL or C.TELEGRAM


def cta(T, cls=""):
    return f"""<div class="cta {cls}">
<a class="btn primary" href="{E(book_url())}" target="_blank" rel="noopener">{E(T["cta_book"])}</a>
<a class="btn" href="{E(C.TELEGRAM)}" target="_blank" rel="noopener">Telegram {E(C.TELEGRAM_HANDLE)}</a>
<a class="btn ghost" href="mailto:{E(C.EMAIL)}">{E(C.EMAIL)}</a>
</div>"""


def footer(T, lang, page):
    return f"""<footer class="foot">
<div class="wrap foot-in">
<div><strong>{E(C.BRAND)} · {E(C.BRAND_SUB)}</strong><br>{E(T["footer_tag"])}</div>
<div class="foot-links">
<a href="{url(lang, 'impressum.html')}">{E(T["impressum"])}</a>
<a href="{url(lang, 'datenschutz.html')}">{E(T["privacy"])}</a>
<a href="mailto:{E(C.EMAIL)}">{E(C.EMAIL)}</a>
<a href="{E(C.TELEGRAM)}" target="_blank" rel="noopener">Telegram</a>
</div>
{langswitch(lang, page)}
<div class="small">© {YEAR} {E(C.BRAND)}. {E(T["footer_note"])}</div>
</div>
</footer>
</body>
</html>
"""


def chat(T):
    out = []
    for m in T["chat"]:
        who = m.get("who", "bot")
        btns = "".join(f"<span>{E(b)}</span>" for b in m.get("buttons", []))
        kb = f'<div class="kb">{btns}</div>' if btns else ""
        out.append(f'<div class="msg {who}"><div class="bubble">{m["html"]}{kb}</div></div>')
    return "\n".join(out)


def slides():
    """site/slides/slide1.jpg, slide2.jpg … (натуральная сортировка); ?v= — сброс кэша при замене файла."""
    d = os.path.join(OUT, "slides")
    if not os.path.isdir(d):
        return []
    files = [f for f in os.listdir(d) if re.fullmatch(r"slide\d+\.(jpe?g|png|webp)", f, re.I)]
    files.sort(key=lambda f: int(re.search(r"\d+", f).group()))
    out = []
    for f in files:
        with open(os.path.join(d, f), "rb") as fh:
            out.append(f"/slides/{f}?v={hashlib.sha1(fh.read()).hexdigest()[:8]}")
    return out


def slider(T):
    imgs = slides()
    if not imgs:
        return ""
    pics = "".join(f'<img src="{src}" alt="{E(T["slide_alt"].format(n=i))}"{" class=on" if i == 1 else ""}'
                   f' loading="{"eager" if i == 1 else "lazy"}" decoding="async">'
                   for i, src in enumerate(imgs, 1))
    dots = "".join(f'<button type="button" aria-label="{E(T["slides_goto"].format(n=i))}"'
                   f'{" aria-current=true" if i == 1 else ""}></button>' for i in range(1, len(imgs) + 1))
    return f"""<section id="examples" class="sec extra">
<div class="wrap">
<h2>{E(T["slides_title"])}</h2>
<p class="intro">{E(T["slides_intro"])}</p>
<div class="slider" data-interval="{C.SLIDE_INTERVAL_MS}" aria-roledescription="carousel">
<div class="slides">{pics}</div>
<button type="button" class="sl-prev" aria-label="{E(T["slides_prev"])}">‹</button>
<button type="button" class="sl-next" aria-label="{E(T["slides_next"])}">›</button>
<div class="sl-dots">{dots}</div>
</div>
</div>
</section>
<script src="{asset('/assets/slider.js')}" defer></script>
"""


def price_unit(T, unit, price):
    u = T["units"]
    if unit == "h":
        return f'<b>{price}</b> <span>{E(u["h"])}</span>'
    if unit == "fix":
        return f'<b>{price}</b> <span>{E(u["fix"])}</span>'
    if unit == "from_fix":
        return f'<span>{E(u["from"])}</span> <b>{price}</b> <span>{E(u["fix"])}</span>'
    return f'<span>{E(u["from"])}</span> <b>{price}</b>'


def index(T, lang):
    s = []
    s.append(head(T, lang, "", T["meta_title"], T["meta_desc"]))
    s.append(header(T, lang, ""))
    badges = "".join(f"<li>{E(b)}</li>" for b in T["badges"])
    s.append(f"""<main>
<section class="hero extra">
<div class="wrap hero-in">
<div>
<p class="kicker">{E(T["kicker"])}</p>
<h1>{T["h1"]}</h1>
<p class="lead">{E(T["sub"])}</p>
{cta(T)}
<ul class="badges extra">{badges}</ul>
</div>
<div class="hero-card" aria-hidden="true">
<div class="hc-row"><span class="dot ok"></span>{E(T["hero_card"][0])}<em>200 · 0.18 s</em></div>
<div class="hc-row"><span class="dot ok"></span>{E(T["hero_card"][1])}<em>03:00</em></div>
<div class="hc-row"><span class="dot warn"></span>{E(T["hero_card"][2])}<em>91 %</em></div>
<div class="hc-row"><span class="dot ok"></span>{E(T["hero_card"][3])}<em>0</em></div>
<div class="hc-foot">{E(T["hero_card"][4])}</div>
</div>
</div>
</section>
""")
    cards = "".join(f'<article class="card">{icon(ic)}<h3>{E(t)}</h3><p>{E(x)}</p></article>'
                    for ic, t, x in T["services"])
    s.append(f"""<section id="services" class="sec extra">
<div class="wrap">
<h2>{E(T["services_title"])}</h2>
<p class="intro">{E(T["services_intro"])}</p>
<div class="grid3">{cards}</div>
</div>
</section>
""")
    dach = "".join(
        f'<article class="feat"><p class="tag">{E(tag)}</p><h3>{E(t)}</h3><p>{E(x)}</p>'
        f'<ul>{"".join(f"<li>{E(b)}</li>" for b in bl)}</ul></article>'
        for tag, t, x, bl in T["dach"])
    s.append(f"""<section id="dach" class="sec alt extra">
<div class="wrap">
<h2>{E(T["dach_title"])}</h2>
<p class="intro">{E(T["dach_intro"])}</p>
<div class="grid2">{dach}</div>
</div>
</section>
""")
    pts = "".join(f"<li><b>{E(a)}</b> {E(b)}</li>" for a, b in T["bot_points"])
    s.append(f"""<section id="bot" class="sec extra">
<div class="wrap bot-in">
<div>
<h2>{E(T["bot_title"])}</h2>
<p class="intro">{E(T["bot_intro"])}</p>
<ul class="checks">{pts}</ul>
<p class="note">{E(T["bot_note"])}</p>
</div>
<figure class="phone">
<div class="phone-top"><span class="logo sm">G</span><div><b>Odoo Monitor</b><small>{E(T["bot_online"])}</small></div></div>
<div class="chat">
{chat(T)}
</div>
<figcaption>{E(T["chat_caption"])}</figcaption>
</figure>
</div>
</section>
""")
    mon = "".join(f'<article class="card"><p class="tag mono">{E(tag)}</p><h3>{E(t)}</h3><p>{E(x)}</p></article>'
                  for tag, t, x in T["mon"])
    s.append(f"""<section id="monitoring" class="sec alt extra">
<div class="wrap">
<h2>{E(T["mon_title"])}</h2>
<p class="intro">{E(T["mon_intro"])}</p>
<div class="grid3">{mon}</div>
<p class="note">{E(T["mon_note"])}</p>
</div>
</section>
""")
    steps = "".join(f'<li><span class="num">{i}</span><h3>{E(t)}</h3><p>{E(x)}</p></li>'
                    for i, (t, x) in enumerate(T["process"], 1))
    s.append(f"""<section class="sec extra">
<div class="wrap">
<h2>{E(T["process_title"])}</h2>
<ol class="steps">{steps}</ol>
</div>
</section>
""")
    plans = []
    for key, price, hours, react in C.PLANS:
        p = T["plans"][key]
        feats = "".join(f"<li>{E(f)}</li>" for f in p["features"])
        plans.append(f"""<article class="plan{' hot' if key == 'business' else ''}">
<h3>{E(p["name"])}</h3>
<p class="pdesc">{E(p["desc"])}</p>
<p class="price"><b>{price}</b> <span>{E(T["per_month"])}</span></p>
<ul>
<li>{E(T["incl_hours"].format(h=hours))}</li>
<li>{E(T["reaction"][react])}</li>
{feats}
</ul>
</article>""")
    rows = "".join(f'<tr><td>{E(T["price_names"][k][0])}<br><small>{E(T["price_names"][k][1])}</small></td>'
                   f'<td class="pr">{price_unit(T, u, p)}</td></tr>' for k, p, u in C.PRICES)
    cases = "".join(f'<article class="case"><h3>{E(t)}</h3><p>{E(x)}</p><p class="cprice">{E(pr)}</p></article>'
                    for t, x, pr in T["cases"])
    s.append(f"""<section id="prices" class="sec alt">
<div class="wrap">
<p class="reader-intro"><b>{E(C.BRAND)} · {E(C.BRAND_SUB)}</b> — {E(T["kicker"])}</p>
<p class="reader-intro">{E(T["sub"])}</p>
<p class="reader-intro">Telegram: <a href="{E(C.TELEGRAM)}">{E(C.TELEGRAM_HANDLE)}</a> · E-Mail: <a href="mailto:{E(C.EMAIL)}">{E(C.EMAIL)}</a> · <a href="{E(book_url())}">{E(T["cta_book"])}</a></p>
<h2>{E(T["prices_title"])}</h2>
<p class="intro">{E(T["prices_intro"])}</p>
<div class="plans">{"".join(plans)}</div>
<p class="note center">{E(T["plans_note"])}</p>
<h3 class="sub">{E(T["table_title"])}</h3>
<div class="tablewrap"><table class="prices">
<thead><tr><th>{E(T["table_head"][0])}</th><th>{E(T["table_head"][1])}</th></tr></thead>
<tbody>{rows}</tbody>
</table></div>
<p class="note">{E(T["vat_note"])}</p>
<h3 class="sub">{E(T["cases_title"])}</h3>
<div class="grid3">{cases}</div>
</div>
</section>
""")
    facts = "".join(f"<li>{E(f)}</li>" for f in T["about_facts"])
    paras = "".join(f"<p>{E(p)}</p>" for p in T["about"])
    s.append(f"""<section id="about" class="sec extra">
<div class="wrap about-in">
<div>
<h2>{E(T["about_title"])}</h2>
{paras}
</div>
<ul class="facts">{facts}</ul>
</div>
</section>
""")
    faq = "".join(f"<details><summary>{E(q)}</summary><p>{E(a)}</p></details>" for q, a in T["faq"])
    s.append(f"""<section class="sec alt extra">
<div class="wrap narrow">
<h2>{E(T["faq_title"])}</h2>
<div class="faq">{faq}</div>
</div>
</section>
""")
    s.append(slider(T))
    s.append(f"""<section id="contact" class="sec contact extra">
<div class="wrap narrow center">
<h2>{E(T["contact_title"])}</h2>
<p class="intro">{E(T["contact_text"])}</p>
{cta(T, "center")}
<p class="note">{E(T["contact_note"])}</p>
</div>
</section>
</main>
""")
    s.append(footer(T, lang, ""))
    return "".join(s)


def legal_page(T, lang, page, key):
    L = T[key]
    data = {
        "name": E(C.OWNER_NAME), "street": E(C.OWNER_STREET), "city": E(C.OWNER_CITY),
        "country": E(C.OWNER_COUNTRY), "email": E(C.EMAIL),
        "vat": E(T["kleinunternehmer"] if C.VAT_ID == "KLEINUNTERNEHMER" else C.VAT_ID),
        "telegram": E(C.TELEGRAM_HANDLE), "brand": E(C.BRAND),
    }
    body = L["html"].format(**data)
    note = f'<p class="note legalnote">{E(T["legal_note"])} <a href="{url("de", page)}">Deutsch</a></p>' if lang != "de" else ""
    return (head(T, lang, page, f'{L["title"]} · {C.BRAND}', L["title"]) + header(T, lang, page)
            + f'<main class="sec"><div class="wrap narrow legal"><h1>{E(L["title"])}</h1>{note}{body}</div></main>'
            + footer(T, lang, page))


LANG_JS = """// Выбор языка по настройкам браузера; по умолчанию — __DEF__. Ничего не сохраняет (без cookies/localStorage).
// Файл генерируется src/build.py из config.LANGS.
(function () {
  var supported = [__LANGS__], pick = "__DEF__";
  var list = navigator.languages || [navigator.language || ""];
  for (var i = 0; i < list.length; i++) {
    var l = String(list[i]).toLowerCase().slice(0, 2);
    if (l === "ua") l = "uk";
    if (supported.indexOf(l) >= 0) { pick = l; break; }
  }
  location.replace("/" + pick + "/" + location.hash);
})();
"""


def write(path, text):
    full = os.path.join(OUT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(text)


def main():
    pages = []
    for lang in C.LANGS:
        T = importlib.import_module(f"lang_{lang}").T
        write(f"{lang}/index.html", index(T, lang))
        write(f"{lang}/impressum.html", legal_page(T, lang, "impressum.html", "impressum_page"))
        write(f"{lang}/datenschutz.html", legal_page(T, lang, "datenschutz.html", "privacy_page"))
        pages += [url(lang), url(lang, "impressum.html"), url(lang, "datenschutz.html")]
    write("assets/lang.js", LANG_JS.replace("__LANGS__", ", ".join(f'"{l}"' for l in C.LANGS)).replace("__DEF__", C.LANGS[0]))
    alts = "\n".join(f'<link rel="alternate" hreflang="{l}" href="{C.BASE_URL}{url(l)}">' for l in C.LANGS)
    links = " · ".join(f'<a href="{url(l)}" lang="{l}">{flag(l)} {E(C.LANG_NAMES[l])}</a>' for l in C.LANGS)
    write("index.html", f"""<!doctype html>
<html lang="{C.LANGS[0]}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{E(C.BRAND)} · {E(C.BRAND_SUB)}</title>
<meta name="description" content="Odoo Support, Installation & Integration für Deutschland, Österreich und die Schweiz.">
<link rel="canonical" href="{C.BASE_URL}{url(C.LANGS[0])}">
{alts}
<link rel="alternate" hreflang="x-default" href="{C.BASE_URL}{url(C.LANGS[0])}">
{VERIFY}<link rel="icon" href="/assets/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="{asset('/assets/style.css')}">
<script src="{asset('/assets/lang.js')}"></script>
</head>
<body>
<main class="sec"><div class="wrap narrow center">
<h1>{E(C.BRAND)} · {E(C.BRAND_SUB)}</h1>
<p class="rootlangs">{links}</p>
</div></main>
</body>
</html>
""")
    write("404.html", f"""<!doctype html>
<html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>404 · {E(C.BRAND)}</title><link rel="stylesheet" href="{asset('/assets/style.css')}"></head>
<body><main class="sec"><div class="wrap narrow center"><h1>404</h1>
<p>Seite nicht gefunden · Page not found</p><p><a class="btn primary" href="/">{E(C.BRAND)} · {E(C.BRAND_SUB)}</a></p></div></main></body></html>
""")
    today = datetime.date.today().isoformat()
    write("sitemap.xml", '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
          + "".join(f"<url><loc>{C.BASE_URL}{p}</loc><lastmod>{today}</lastmod></url>\n" for p in pages) + "</urlset>\n")
    write("robots.txt", f"User-agent: *\nAllow: /\nSitemap: {C.BASE_URL}/sitemap.xml\n")
    print("ok:", len(pages), "pages →", OUT)


if __name__ == "__main__":
    main()
