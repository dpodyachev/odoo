#!/usr/bin/env python3
"""Генератор статического сайта: src/lang_<xx>.py + config.py → site/<xx>/index.html, impressum.html, datenschutz.html.
Запуск: python3 src/build.py   (без зависимостей; результат коммитится, Cloudflare Pages отдаёт папку site/)."""
import datetime
import hashlib
import re
import html
import importlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import config as C  # noqa: E402
import europe_map as M  # noqa: E402
import blog_posts as BP  # noqa: E402
import test_pages as TP  # noqa: E402
import calc_page as CP  # noqa: E402
import pubs_page as PP  # noqa: E402

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


CONTACTS_KEY = b"goldberg-odoo"


def write_contacts_js():
    """Личные контакты → site/assets/contacts.js в виде XOR+base64 (перевёрнутая строка): в HTML их нет,
    браузер подставляет их в элементы с data-ch (href), data-ct (title/aria-label), data-cx (текст)."""
    import base64
    P = dict(C.PRIVATE)
    P["whatsapp_text"] = P.get("whatsapp", "").split("//")[-1]
    raw = json.dumps(P, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    enc = base64.b64encode(bytes(b ^ CONTACTS_KEY[i % len(CONTACTS_KEY)] for i, b in enumerate(raw))).decode()[::-1]
    js = ('''(function () {
  var s = atob("%s".split("").reverse().join("")), k = "%s", b = new Uint8Array(s.length);
  for (var i = 0; i < s.length; i++) b[i] = s.charCodeAt(i) ^ k.charCodeAt(i %% k.length);
  var C = JSON.parse(new TextDecoder().decode(b)); window.GC = C;
  function f(t) { return t.replace(/\\{(\\w+)\\}/g, function (_, n) { return C[n] || ""; }); }
  function run() {
    document.querySelectorAll("[data-ch],[data-ct],[data-cx]").forEach(function (e) {
      var v = e.getAttribute("data-ch"); if (v) e.setAttribute("href", f(v));
      v = e.getAttribute("data-ct"); if (v) { e.title = f(v); e.setAttribute("aria-label", f(v)); }
      v = e.getAttribute("data-cx"); if (v) e.textContent = f(v);
    });
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", run); else run();
})();
''' % (enc, CONTACTS_KEY.decode()))
    with open(os.path.join(OUT, "assets", "contacts.js"), "w", encoding="utf-8") as fh:
        fh.write(js)


def check_no_private():
    """Сборка падает, если личные данные попали в site/ открытым текстом."""
    needles = {v for k, v in C.PRIVATE.items() if v and len(v) >= 6}
    needles |= {v.split("//")[-1] for v in needles if "//" in v}
    needles |= {v.lstrip("+") for v in needles if v.startswith("+")}
    bad = []
    for root, _d, files in os.walk(OUT):
        for fn in files:
            if fn.endswith((".html", ".js", ".json", ".xml", ".txt", ".css")) and fn != "contacts.js":
                path = os.path.join(root, fn)
                with open(path, encoding="utf-8", errors="ignore") as fh:
                    t = fh.read()
                bad += [os.path.relpath(path, OUT) for n in needles if n in t]
    if bad:
        sys.exit("ОШИБКА: личные данные открытым текстом в: " + ", ".join(sorted(set(bad))[:10]))


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
<link rel="alternate" type="text/plain" href="/llms.txt" title="Site overview for AI assistants (llms.txt)">
<link rel="alternate" type="text/markdown" href="/skill_odoo.md" title="Odoo operations skill for AI agents (Markdown)">
<link rel="alternate" type="text/markdown" href="/skill_odoo_security.md" title="Odoo security skill for AI agents (Markdown)">
<link rel="stylesheet" href="{asset('/assets/style.css')}">
<script src="{asset('/assets/theme.js')}" defer></script>
<script src="{asset('/assets/contacts.js')}" defer></script>
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
    def svg(*paths):
        return ('<svg class="ico-nav" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" '
                'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' + "".join(paths) + '</svg>')
    gear = svg('<circle cx="12" cy="12" r="7.8" stroke-width="3" stroke-dasharray="3 3.125" stroke-linecap="butt"/>',
               '<circle cx="12" cy="12" r="6"/>', '<circle cx="12" cy="12" r="2"/>')
    icons = {  # пункты меню-значки: подпись во всплывающей подсказке и aria-label
        "services": svg(ICONS["fix"]) + gear + svg('<path d="M13 2 4 14h7l-1 8 10-13h-7z"/>'),
        "bot": svg('<circle cx="12" cy="12" r="9.2"/>', '<circle cx="12" cy="12" r="5.2" opacity=".55"/>',
                   '<g class="sweep"><path d="M12 12 18.5 5.5A9.2 9.2 0 0 1 21.2 12z" fill="currentColor" stroke="none" opacity=".28"/>'
                   '<path d="M12 12l6.5-6.5"/></g>', '<circle cx="15.6" cy="15" r="1.3" fill="currentColor" stroke="none"/>'),
        "prices": f'<span aria-hidden="true">{C.PRICE_ICON.get(lang, "€")}</span>',
        "dach": svg('<path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h5M14 3l5 5v4M14 3v5h5"/>',
                    '<path d="M8.5 11h5M8.5 14.5h3"/>', '<path d="m14.5 18.5 2 2 4-4.5"/>'),
        "about": svg('<rect x="3" y="7" width="18" height="13" rx="2"/>', '<path d="M9 7V5a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2M3 13h18"/>'),
        "contact": svg('<rect x="3" y="5" width="18" height="14" rx="2"/>', '<path d="m3.5 6.5 8.5 6.5 8.5-6.5"/>'),
        "blog": svg('<circle cx="12" cy="12" r="9.2"/>', '<path d="M9.3 9.2a2.8 2.8 0 0 1 5.4 1c0 1.9-2.7 2.4-2.7 4"/>',
                    '<circle cx="12" cy="17.4" r=".9" fill="currentColor" stroke="none"/>'),
        "calc": svg(CP.CALC_ICON),
        "pubs": svg(PP.ICON),
    }
    items = []
    for k, v in T["nav"].items():   # калькулятор PostgreSQL/Odoo – сразу после блога
        items.append((k, v))
        if k == "blog":
            items.append(("pubs", PP.TX[lang]["nav"]))
            items.append(("calc", CP.TX[lang]["nav"]))
    hrefs = {"blog": url(lang, "blog/"), "calc": url(lang, CP.SLUG), "pubs": url(lang, PP.SLUG)}
    current = {"blog": page.startswith("blog/"), "calc": page in (CP.SLUG, CP.SLUG_S), "pubs": page == PP.SLUG}
    cls = {"services": "nav-icon multi", "prices": "nav-icon cur", "bot": "nav-icon radar"}
    nav = "".join(
        f'<a class="{cls.get(k, "nav-icon")}" href="{hrefs.get(k, url(lang) + "#" + k)}" '
        f'title="{E(v)}" aria-label="{E(v)}"{" aria-current=page" if current.get(k) else ""}>{icons[k]}</a>' if k in icons
        else f'<a href="{url(lang)}#{k}">{E(v)}</a>' for k, v in items)
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


SOCIAL_SVG = {  # значки контактов: адрес/ник — в подсказке и aria-label
    "mail": '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="m3.5 6.5 8.5 6.5 8.5-6.5"/>',
    "tg": '<path d="M21.5 3.5 2.8 10.7c-.9.4-.9 1.6.1 1.9l4.6 1.5 1.8 5.6c.3.8 1.3 1 1.9.4l2.6-2.5 4.8 3.5c.7.5 1.7.1 1.9-.7L22.9 4.9c.2-1-.6-1.8-1.4-1.4z"/><path d="m7.5 14.1 10-6.6-7.6 8.1"/>',
    "tel": '<path d="M22 16.9v3a2 2 0 0 1-2.2 2 19.8 19.8 0 0 1-8.6-3.1 19.5 19.5 0 0 1-6-6A19.8 19.8 0 0 1 2.1 4.2 2 2 0 0 1 4.1 2h3a2 2 0 0 1 2 1.7c.1.9.4 1.8.7 2.7a2 2 0 0 1-.5 2.1L8 9.8a16 16 0 0 0 6 6l1.3-1.3a2 2 0 0 1 2.1-.4c.9.3 1.8.6 2.7.7a2 2 0 0 1 1.7 2z"/>',
    "wa": '<path d="M3.5 20.5l1.3-4.2A8.6 8.6 0 1 1 8 19.4z"/><path d="M9 8.6c.1 2.9 3.4 6.2 6.3 6.4l1.2-1.4-1.9-1-.9.8c-1-.5-2.3-1.8-2.8-2.8l.8-.9-1-1.9z"/>',
    "li": '<rect x="3" y="3" width="18" height="18" rx="3"/><path d="M8 10.5V17M8 7.3v.1M12 17v-6.5M12 13.3c0-1.6 1.1-2.8 2.5-2.8S17 11.5 17 13v4"/>',
}


def social(kind, cls=""):
    """Значок контакта. Личные (mail/tg/wa/tel) — без адреса в HTML: href/подсказку подставляет contacts.js."""
    href, label, ext, on = {
        "mail": ("mailto:{email}", "E-Mail: {email}", "", C.EMAIL),
        "tg": ("{telegram}", "Telegram: {telegram_handle}", ' target="_blank" rel="noopener"', C.TELEGRAM),
        "wa": ("{whatsapp}", "WhatsApp", ' target="_blank" rel="noopener"', C.WHATSAPP),
        "tel": ("tel:{phone}", "Tel.: {phone_display}", "", C.PHONE),
        "li": (getattr(C, "LINKEDIN", ""), "LinkedIn", ' target="_blank" rel="noopener me"', getattr(C, "LINKEDIN", "")),
    }[kind]
    if not on:
        return ""
    generic = {"mail": "E-Mail", "tg": "Telegram", "wa": "WhatsApp", "tel": "Tel.", "li": "LinkedIn"}[kind]
    attrs = (f'href="{E(href)}" title="{generic}" aria-label="{generic}"' if kind == "li"
             else f'data-ch="{E(href)}" data-ct="{E(label)}" title="{generic}" aria-label="{generic}"')
    return (f'<a class="soc-ico{(" " + cls) if cls else ""}" {attrs}{ext}>'
            f'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" '
            f'stroke-linejoin="round" aria-hidden="true">{SOCIAL_SVG[kind]}</svg></a>')

def cta(T, cls="", li=False):
    return f"""<div class="cta {cls}">
<a class="btn primary" href="{E(book_url())}" target="_blank" rel="noopener">{E(T["cta_book"])}</a>
{social("tg", "btn")}
{social("wa", "btn ghost")}
{social("tel", "btn ghost")}
{social("mail", "btn ghost")}
{social("li", "btn ghost") if li else ""}
</div>"""


def footer(T, lang, page):
    return f"""<footer class="foot">
<div class="wrap foot-in">
<div><strong>{E(C.BRAND)} · {E(C.BRAND_SUB)}</strong><br>{E(T["footer_tag"])}</div>
<div class="foot-links">
<a href="{url(lang, 'blog/')}">{E(T["nav"]["blog"])}</a>
<a href="{url(lang, PP.SLUG)}">{E(PP.TX[lang]["nav"])}</a>
<a href="{url(lang, CP.SLUG)}">{E(CP.TX[lang]["nav"])}</a>
<a href="{url(lang, 'impressum.html')}">{E(T["impressum"])}</a>
<a href="{url(lang, 'datenschutz.html')}">{E(T["privacy"])}</a>
<span class="foot-soc">{social("mail")}{social("tg")}{social("wa")}{social("tel")}{social("li")}</span>
</div>
{langswitch(lang, page)}
<div class="small">© {YEAR} {E(C.BRAND)}. {E(T["footer_note"])}</div>
</div>
</footer>
</body>
</html>
"""


def phone(T, msgs, caption):
    return f"""<figure class="phone">
<div class="phone-top"><span class="logo sm">G</span><div><b>Odoo Monitor</b><small>{E(T["bot_online"])}</small></div></div>
<div class="chat">
{chat(T, msgs)}
</div>
<figcaption>{E(caption)}</figcaption>
</figure>"""


def chat(T, msgs=None):
    out = []
    for m in (msgs if msgs is not None else T["chat"]):
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
    return f"""<section id="examples" class="sec alt extra">
<div class="wrap">
<h2>{E(T["slides_title"])}</h2>
<p class="intro">{E(T["slides_intro"])}</p>
<div class="slider" data-interval="{C.SLIDE_INTERVAL_MS}" aria-roledescription="carousel"
 data-l-close="{E(T["lb"]["close"])}" data-l-in="{E(T["lb"]["zoom_in"])}" data-l-out="{E(T["lb"]["zoom_out"])}"
 data-l-full="{E(T["lb"]["full"])}" data-l-prev="{E(T["slides_prev"])}" data-l-next="{E(T["slides_next"])}">
<div class="slides">{pics}</div>
<button type="button" class="sl-prev" aria-label="{E(T["slides_prev"])}">‹</button>
<button type="button" class="sl-next" aria-label="{E(T["slides_next"])}">›</button>
<div class="sl-dots">{dots}</div>
</div>
</div>
</section>
<script src="{asset('/assets/slider.js')}" defer></script>
"""


def echeck(T):
    """Лид-магнит «E-Rechnung-Check»: 5 вопросов, результат считается в браузере (assets/echeck.js), ничего не отправляется."""
    X = T["echeck"]
    qs = []
    for i, (tag, q, hint, _tip) in enumerate(X["q"], 1):
        opts = "".join(f'<label><input type="radio" name="q{i}" value="{v}" required> {E(a)}</label>'
                       for v, a in zip((2, 1, 0), X["answers"]))
        qs.append(f'<fieldset class="eq"><legend><span class="num">{i}</span><span><b>{E(tag)}:</b> {E(q)}</span></legend>'
                  f'<p class="hint">{E(hint)}</p><div class="opts">{opts}</div></fieldset>')
    data = {k: X[k] for k in ("answers", "score", "levels", "mail_subject", "mail_intro", "mail_outro")}
    data["q"] = [(tag, tip) for tag, _q, _h, tip in X["q"]]
    data["title"] = X["title"]
    data["cal"] = book_url()   # e-mail берёт echeck.js из window.GC (contacts.js)
    js = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    return f"""<section id="echeck" class="sec echeck-sec extra">
<div class="wrap narrow">
<p class="kicker">{E(X["kicker"])}</p>
<h2>{E(X["title"])}</h2>
<p class="intro">{E(X["intro"])}</p>
<form class="echeck" novalidate>
{"".join(qs)}
<p class="small">🔒 {E(X["privacy"])}</p>
<button class="btn primary" type="submit">{E(X["submit"])}</button>
<p class="ec-err" role="alert" hidden>{E(X["need_all"])}</p>
</form>
<div class="ec-result" hidden tabindex="-1">
<p class="ec-score"></p>
<h3 class="ec-level"></h3>
<p class="ec-text"></p>
<div class="ec-todo"><p><b>{E(X["todo"])}</b></p><ul></ul></div>
<div class="ec-cta">
<h3>🎯 {E(X["cta_title"])}</h3>
<p>{E(X["cta_text"])}</p>
<div class="cta">
<a class="btn primary ec-book" href="{E(book_url())}" target="_blank" rel="noopener">{E(X["cta_book"])}</a>
<a class="btn ec-mail" data-ch="mailto:{{email}}">{E(X["cta_mail"])}</a>
<a class="btn ec-tg" data-ch="{{telegram}}" target="_blank" rel="noopener">{E(X["cta_tg"])}</a>
</div>
<p class="small ec-copied" hidden>✅ {E(X["copied"])}</p>
</div>
</div>
<script type="application/json" class="ec-data">{js}</script>
</div>
</section>
<script src="{asset('/assets/echeck.js')}" defer></script>
"""


def map_xy(lon, lat):
    import math
    l, p, l0, p0 = map(math.radians, (lon, lat, M.LON0, M.LAT0))
    k = math.sqrt(2 / (1 + math.sin(p0) * math.sin(p) + math.cos(p0) * math.cos(p) * math.cos(l - l0)))
    x = k * math.cos(p) * math.sin(l - l0)
    y = -k * (math.cos(p0) * math.sin(p) - math.sin(p0) * math.cos(p) * math.cos(l - l0))
    return round((x - M.CX0) * M.S, 1), round((y - M.CY0) * M.S, 1)


def europe_map(T):
    """Карта (Natural Earth, src/europe_map.py) с флажками городов из config.MAP_CITIES."""
    X = T["map"]
    hl = "".join(f'<path class="hl" d="{d}"/>' for cid, d in M.PATHS.items() if cid in M.HIGHLIGHT)
    other = "".join(f'<path d="{d}"/>' for cid, d in M.PATHS.items() if cid not in M.HIGHLIGHT)
    pins = []
    proj = getattr(C, "MAP_PROJECTS", {})
    for key, lon, lat, pos in C.MAP_CITIES:
        x, y = map_xy(lon, lat)
        tx, ty, anchor = {"e": (14, 5, "start"), "w": (-7, 5, "end"), "s": (0, 20, "middle")}[pos]
        home = " home" if key == C.MAP_HOME else ""
        pins.append(f'<g class="pin{home}" transform="translate({x} {y})"><circle r="3"/><path class="pole" d="M0 0V-20"/>'
                    f'<path class="flag" d="M0-20l13 4.5-13 4.5z"/>'
                    f'<text x="{tx}" y="{ty}" text-anchor="{anchor}">{E(X["c"][key])}</text>'
                    + (f'<text class="proj" x="{tx}" y="{ty + 18}" text-anchor="{anchor}">{E(proj[key])}</text>' if key in proj else "")
                    + '</g>')
    return f"""<figure class="map">
<svg viewBox="0 0 {M.W} {M.H}" role="img" aria-label="{E(X["title"])}: {E(", ".join(X["c"][k] for k, *_ in C.MAP_CITIES))}">
<rect class="sea" width="{M.W}" height="{M.H}"/>
<g class="land">{hl}{other}</g>
{"".join(pins)}
</svg>
<figcaption><b>{E(X["title"])}</b> · {E(X["caption"])} <span class="map-home">⚑ {E(X["home"])}</span></figcaption>
</figure>"""


def lt_shots(T):
    """Скриншоты веб-интерфейса Locust (site/img/locust-*.webp); клик — полноэкранный просмотр (slider.js)."""
    X = T["lt_shots"]
    items = "".join(
        f'<figure class="shot"><button type="button" class="shot-btn" aria-label="{E(X["full"])}: {E(cap)}">'
        f'<img src="{asset("/img/" + f)}" alt="{E(cap)}" width="{w}" height="{h}" loading="lazy" decoding="async"></button>'
        f'<figcaption>{E(cap)}</figcaption></figure>'
        for (f, w, h), cap in zip([("locust-stats.webp", 1600, 861), ("locust-charts.webp", 1600, 1135)], X["caps"]))
    return (f'<div class="lb-group shots" data-l-close="{E(T["lb"]["close"])}" data-l-in="{E(T["lb"]["zoom_in"])}" '
            f'data-l-out="{E(T["lb"]["zoom_out"])}" data-l-full="{E(T["lb"]["full"])}" '
            f'data-l-prev="{E(T["slides_prev"])}" data-l-next="{E(T["slides_next"])}">{items}</div>'
            f'<p class="note shots-note">{E(X["note"])}</p>')


LOCUST_SAMPLE = """from locust import HttpUser, task, between

class SalesUser(HttpUser):
    wait_time = between(2, 8)            # think time like a real user

    def on_start(self):
        self.login()                     # /web/session/authenticate

    @task(5)
    def search_quotations(self):
        self.call("sale.order", "web_search_read",
                  [("state", "=", "draft")], limit=80,
                  specification={"name": {}, "amount_total": {}})

    @task(1)
    def create_and_confirm(self):
        so = self.call("sale.order", "create",
                       {"partner_id": self.random_customer(),
                        "order_line": self.random_lines(3)})
        self.call("sale.order", "action_confirm", [so])
        self.client.get(f"/report/pdf/sale.report_saleorder/{so}",
                        name="PDF quotation")"""


def offer(T):
    """Плашка Einstiegsangebot; пусто, если OFFER=None или срок прошёл."""
    o = getattr(C, "OFFER", None)
    if not o:
        return ""
    until = datetime.date.fromisoformat(o["until"])
    if datetime.date.today() > until:
        return ""
    X = T["offer"]
    d = until.strftime(X["date"])
    return (f'<aside class="offer"><b class="offer-t">{E(X["title"])}</b> '
            f'<span>{E(X["text"].format(p=o["price"], h=o["hours"], d=d))}</span> '
            f'<a class="btn primary small" href="{E(book_url())}" target="_blank" rel="noopener">{E(X["cta"])}</a></aside>')


def yearly(price):
    """Годовая оплата = 10 месяцев (2 месяца бесплатно): "1 490 €" → "14 900 €"."""
    n = int("".join(ch for ch in price if ch.isdigit())) * 10
    return f"{n:,}".replace(",", " ") + " €"


def price_unit(T, unit, price):
    u = T["units"]
    if unit == "h":
        return f'<b>{price}</b> <span>{E(u["h"])}</span>'
    if unit == "fix":
        return f'<b>{price}</b> <span>{E(u["fix"])}</span>'
    if unit == "from_fix":
        return f'<span>{E(u["from"])}</span> <b>{price}</b> <span>{E(u["fix"])}</span>'
    if unit == "pct":
        return f'<b>{price}</b> <span>{E(u["pct"])}</span>'
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
<p class="hero-check"><a href="#echeck">✅ {E(T["echeck"]["hero_link"])} →</a></p>
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
<p class="note">{E(T["dach_note"])}</p>
</div>
</section>
""")
    s.append(echeck(T))
    impl = "".join(f'<li><span class="num">{i}</span><h3>{E(t)}</h3><p>{E(x)}</p></li>'
                   for i, (t, x) in enumerate(T["impl"], 1))
    s.append(f"""<section id="implementation" class="sec extra">
<div class="wrap">
<h2>{E(T["impl_title"])}</h2>
<p class="intro">{E(T["impl_intro"])}</p>
<ol class="steps impl">{impl}</ol>
</div>
</section>
""")
    pts = "".join(f"<li><b>{E(a)}</b> {E(b)}</li>" for a, b in T["bot_points"])
    s.append(f"""<section id="bot" class="sec alt extra">
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
<div class="wrap">
<h3 class="sub">{E(T["bot_more_title"])}</h3>
<p class="intro">{E(T["bot_more_intro"])}</p>
<div class="phones2">{"".join(phone(T, c["msgs"], c["caption"]) for c in T["chat2"])}</div>
</div>
</section>
""")
    mon = "".join(f'<article class="card"><p class="tag mono">{E(tag)}</p><h3>{E(t)}</h3><p>{E(x)}</p></article>'
                  for tag, t, x in T["mon"])
    s.append(f"""<section id="monitoring" class="sec extra">
<div class="wrap">
<h2>{E(T["mon_title"])}</h2>
<p class="intro">{E(T["mon_intro"])}</p>
<div class="grid3">{mon}</div>
<p class="note">{E(T["mon_note"])}</p>
</div>
</section>
""")
    lt = "".join(f'<article class="card"><p class="tag mono">{E(tag)}</p><h3>{E(t)}</h3><p>{E(x)}</p></article>'
                 for tag, t, x in T["lt"])
    s.append(f"""<section id="loadtest" class="sec extra lt-sec">
<div class="wrap">
<h2>{E(T["lt_title"])}</h2>
<p class="intro">{E(T["lt_intro"])}</p>
<h3 class="sub">{E(T["lt_types_title"])}</h3>
<dl class="lt-types">{"".join(f'<div><dt>{E(n)}</dt><dd>{E(d)}</dd></div>' for n, d in T["lt_types"])}</dl>
<div class="grid3">{lt}</div>
{lt_shots(T)}
<figure class="code"><figcaption>{E(T["lt_code"])}</figcaption><pre><code>{E(LOCUST_SAMPLE)}</code></pre></figure>
<p class="note">{E(T["lt_note"])}</p>
</div>
</section>
""")
    steps = "".join(f'<li><span class="num">{i}</span><h3>{E(t)}</h3><p>{E(x)}</p></li>'
                    for i, (t, x) in enumerate(T["process"], 1))
    s.append(f"""<section class="sec alt extra">
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
<p class="yearly">{E(T["yearly"].format(p=yearly(price)))}</p>
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
    s.append(f"""<section id="prices" class="sec">
<div class="wrap">
<p class="reader-intro"><b>{E(C.BRAND)} · {E(C.BRAND_SUB)}</b> — {E(T["kicker"])}</p>
<p class="reader-intro">{E(T["sub"])}</p>
<p class="reader-intro"><span class="foot-soc">{social("tg")}{social("wa")}{social("tel")}{social("li")}{social("mail")}</span> · <a href="{E(book_url())}">{E(T["cta_book"])}</a></p>
<h2>{E(T["prices_title"])}</h2>
<p class="intro">{E(T["prices_intro"])}</p>
{offer(T)}
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
    s.append(f"""<section id="about" class="sec alt extra">
<div class="wrap about-in">
<div>
<h2>{E(T["about_title"])}</h2>
{paras}
</div>
<ul class="facts">{facts}</ul>
</div>
<div class="wrap">{europe_map(T)}</div>
</section>
""")
    faq = "".join(f"<details><summary>{E(q)}</summary><p>{E(a)}</p></details>" for q, a in T["faq"])
    s.append(f"""<section class="sec extra">
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
{cta(T, "center", li=True)}
<p class="note">{E(T["contact_note"])}</p>
</div>
</section>
</main>
""")
    s.append(footer(T, lang, ""))
    return "".join(s)


NOSCRIPT_CONTACTS = {
    "de": "JavaScript ist deaktiviert – Anschrift und Kontaktdaten werden zum Schutz vor Spam-Bots daher als Bild angezeigt:",
    "en": "JavaScript is disabled – to protect against spam bots, the address and contact details are shown as an image:",
    "fr": "JavaScript est désactivé – pour se protéger des robots de spam, l'adresse et les coordonnées sont affichées sous forme d'image :",
    "el": "Η JavaScript είναι απενεργοποιημένη – για προστασία από spam bots, η διεύθυνση και τα στοιχεία επικοινωνίας εμφανίζονται ως εικόνα:",
    "uk": "JavaScript вимкнено – для захисту від спам-ботів адреса й контакти показані зображенням:",
    "ru": "JavaScript выключен – для защиты от спам-ботов адрес и контакты показаны картинкой:",
}
NOSCRIPT_NOIMG = {
    "de": "JavaScript ist deaktiviert – Anschrift und Kontaktdaten können nicht geladen werden. Bitte JavaScript aktivieren.",
    "en": "JavaScript is disabled – the address and contact details cannot be loaded. Please enable JavaScript.",
    "fr": "JavaScript est désactivé – l'adresse et les coordonnées ne peuvent pas être chargées. Veuillez activer JavaScript.",
    "el": "Η JavaScript είναι απενεργοποιημένη – η διεύθυνση και τα στοιχεία επικοινωνίας δεν μπορούν να φορτωθούν.",
    "uk": "JavaScript вимкнено – адресу й контакти не вдається завантажити. Увімкніть JavaScript.",
    "ru": "JavaScript выключен – адрес и контакты не могут подгрузиться. Включите JavaScript.",
}
CONTACT_IMG = None   # имя PNG с контактами для <noscript> (создаётся при сборке, если есть Pillow)


def write_contact_image():
    """PNG с адресом и контактами для страниц без JS (Impressum). Нужен Pillow; без него — только текст-подсказка.
    Файл в .gitignore: генерируется в GitHub Action перед деплоем, в репозиторий не попадает."""
    global CONTACT_IMG
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("Pillow не установлен — картинка контактов для <noscript> не создана")
        return
    P = C.PRIVATE
    lines = [C.OWNER_NAME, P.get("street", ""), P.get("city", ""), C.OWNER_COUNTRY, "",
             "E-Mail: " + P.get("email", ""), "Telegram: " + P.get("telegram_handle", ""),
             "Tel.: " + P.get("phone_display", ""), "WhatsApp: " + P.get("whatsapp", "").split("//")[-1]]
    fdir = "/usr/share/fonts/truetype/dejavu/"
    sc = 2
    font = ImageFont.truetype(fdir + "DejaVuSans.ttf", 16 * sc)
    bold = ImageFont.truetype(fdir + "DejaVuSans-Bold.ttf", 16 * sc)
    lh, pad = 26 * sc, 18 * sc
    w = max(int(ImageDraw.Draw(Image.new("RGB", (1, 1))).textlength(l, font=bold)) for l in lines) + 2 * pad
    img = Image.new("RGB", (w, lh * len(lines) + 2 * pad - 6 * sc), "#ffffff")
    d = ImageDraw.Draw(img)
    for i, l in enumerate(lines):
        d.text((pad, pad + i * lh), l, fill="#1d1a22", font=bold if i == 0 else font)
    data = img.tobytes()
    name = f"assets/ci-{hashlib.sha1(data).hexdigest()[:10]}.png"
    for old in os.listdir(os.path.join(OUT, "assets")):
        if old.startswith("ci-") and old.endswith(".png"):
            os.remove(os.path.join(OUT, "assets", old))
    img.save(os.path.join(OUT, name), optimize=True)
    CONTACT_IMG = (name, img.width // sc, img.height // sc)


def noscript_contacts(lang):
    if CONTACT_IMG:
        n, w, h = CONTACT_IMG
        return (f'<noscript><div class="note nojs-ci"><p>{E(NOSCRIPT_CONTACTS.get(lang, NOSCRIPT_CONTACTS["en"]))}</p>'
                f'<img src="/{n}" width="{w}" height="{h}" alt="Kontakt / Contact"></div></noscript>')
    return f'<noscript><p class="note nojs-ci">{E(NOSCRIPT_NOIMG.get(lang, NOSCRIPT_NOIMG["en"]))}</p></noscript>'


def legal_page(T, lang, page, key):
    L = T[key]
    data = {
        "name": E(C.OWNER_NAME), "street": '<span data-cx="{street}"></span>', "city": '<span data-cx="{city}"></span>',
        "country": E(C.OWNER_COUNTRY), "email": '<a data-ch="mailto:{email}" data-cx="{email}"></a>',
        "vat": E(T["kleinunternehmer"] if C.VAT_ID == "KLEINUNTERNEHMER" else C.VAT_ID),
        "telegram": '<a data-ch="{telegram}" data-cx="{telegram_handle}" target="_blank" rel="noopener"></a>', "brand": E(C.BRAND),
        "phone": ('<a data-ch="tel:{phone}" data-cx="{phone_display}"></a>' if C.PHONE else "—"),
        "whatsapp": ('<a data-ch="{whatsapp}" data-cx="{whatsapp_text}" target="_blank" rel="noopener"></a>' if C.WHATSAPP else "—"),
    }
    body = L["html"].format(**data)
    note = f'<p class="note legalnote">{E(T["legal_note"])} <a href="{url("de", page)}">Deutsch</a></p>' if lang != "de" else ""
    return (head(T, lang, page, f'{L["title"]} · {C.BRAND}', L["title"]) + header(T, lang, page)
            + f'<main class="sec"><div class="wrap narrow legal"><h1>{E(L["title"])}</h1>{note}{noscript_contacts(lang)}{body}</div></main>'
            + footer(T, lang, page))


def inline(text):
    """Экранирование + `код` и **жирный** в текстах статей."""
    t = E(text)
    t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)


def post_lang(post, lang):
    return lang if lang in post["t"] else "en"


def read_min(post, lang):
    tx = post["t"][post_lang(post, lang)]
    words = sum(len(str(b[1]).split()) for b in tx["body"]) + sum(len(c[1].split()) // 3 for c in post["code"].values())
    return max(2, round(words / 180))


def fmt_date(d, lang):
    y, m, dd = d.split("-")
    return f"{dd}.{m}.{y}" if lang != "en" else f"{y}-{m}-{dd}"


def ordered_posts():
    """Новые сверху; при одинаковой дате — позже добавленная статья выше."""
    return [p for _, p in sorted(enumerate(BP.POSTS), key=lambda x: (x[1]["date"], x[0]), reverse=True)]


def blog_index(T, lang):
    U = BP.UI[lang]
    page = "blog/"
    cards = "".join(
        f'<article class="post-card"><p class="post-meta">{fmt_date(p["date"], lang)} · {read_min(p, lang)} {E(U["min"])}</p>'
        f'<h2><a href="{url(lang, "blog/" + p["slug"] + ".html")}">{E(p["t"][post_lang(p, lang)]["title"])}</a></h2>'
        f'<p>{E(p["t"][post_lang(p, lang)]["summary"])}</p>'
        f'<p class="post-tags">{"".join(f"<span>{E(t)}</span>" for t in p["tags"])}</p>'
        f'<a class="more" href="{url(lang, "blog/" + p["slug"] + ".html")}">{E(U["read"])} →</a></article>'
        for p in ordered_posts())
    return (head(T, lang, page, f'{U["title"]} · {C.BRAND} {C.BRAND_SUB}', U["intro"]) + header(T, lang, page)
            + f'<main class="sec blog"><div class="wrap narrow"><h1>{E(U["title"])}</h1><p class="intro">{E(U["intro"])}</p>'
            + f'<div class="post-list">{cards}</div></div></main>' + footer(T, lang, page))


def post_nav(lang, post, U):
    """Предыдущая / следующая статья по кругу (в порядке списка блога)."""
    lst = ordered_posts()
    if len(lst) < 2:
        return ""
    i = next(k for k, p in enumerate(lst) if p["slug"] == post["slug"])
    prv, nxt = lst[(i - 1) % len(lst)], lst[(i + 1) % len(lst)]
    a = lambda p, cls, lab, arrow: (f'<a class="{cls}" href="{url(lang, "blog/" + p["slug"] + ".html")}" rel="{cls}">'
                                   f'<small>{(arrow + " " + E(lab)) if cls == "prev" else (E(lab) + " " + arrow)}</small><span>{E(p["t"][post_lang(p, lang)]["title"])}</span></a>')
    allp = f'<a class="all" href="{url(lang, "blog/")}"><small>{E(U["back"])}</small></a>'
    return (f'<nav class="post-nav" aria-label="{E(U["title"])}">{a(prv, "prev", U["prev"], "←")}{allp}'
            f'{a(nxt, "next", U["next"], "→")}</nav>')


def blog_post(T, lang, post):
    U = BP.UI[lang]
    pl = post_lang(post, lang)
    tx = post["t"][pl]
    page = "blog/" + post["slug"] + ".html"
    out = []
    for b in tx["body"]:
        kind = b[0]
        if kind == "p":
            out.append(f"<p>{inline(b[1])}</p>")
        elif kind == "h":
            out.append(f"<h2>{inline(b[1])}</h2>")
        elif kind == "note":
            out.append(f'<p class="post-note">{inline(b[1])}</p>')
        elif kind in ("ul", "ol"):
            out.append(f"<{kind}>" + "".join(f"<li>{inline(x)}</li>" for x in b[1]) + f"</{kind}>")
        elif kind == "code":
            cap, code = post["code"][b[1]]
            out.append(f'<figure class="code"><figcaption>{E(cap)}</figcaption><pre><code>{E(code)}</code></pre></figure>')
        elif kind == "links":
            out.append(f"<h2>{inline(b[1])}</h2><ul class=\"post-links\">" + "".join(
                (f'<li><a href="{url(lang, "blog/" + u[6:] + ".html")}">{E(t)}</a></li>' if u.startswith("@blog:")
                 else f'<li><a href="{url(lang, u[6:])}">{E(t)}</a></li>' if u.startswith("@page:")
                 else f'<li><a href="{E(u)}" target="_blank" rel="noopener">{E(t)}</a></li>') for t, u in post.get("links", [])) + "</ul>")
        elif kind == "table":
            hd, *rows = b[1]
            out.append('<div class="tablewrap"><table class="post-table"><thead><tr>' + "".join(f"<th>{inline(c)}</th>" for c in hd)
                       + "</tr></thead><tbody>" + "".join("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>" for r in rows)
                       + "</tbody></table></div>")
    note = f'<p class="post-note">{E(U["fallback"])}</p>' if pl != lang and U["fallback"] else ""
    ld = json.dumps({"@context": "https://schema.org", "@type": "BlogPosting", "headline": tx["title"],
                     "description": tx["summary"], "datePublished": post["date"], "inLanguage": pl,
                     "author": {"@type": "Person", "name": C.OWNER_NAME.split(" –")[0], "url": C.BASE_URL,
                                "sameAs": [x for x in (getattr(C, "LINKEDIN", ""),) if x]},
                     "mainEntityOfPage": C.BASE_URL + url(lang, page)}, ensure_ascii=False).replace("</", "<\\/")
    return (head(T, lang, page, f'{tx["title"]} · {C.BRAND}', tx["summary"]).replace(
                '</head>', f'<script type="application/ld+json">{ld}</script>\n</head>', 1)
            + header(T, lang, page)
            + f'<main class="sec blog"><article class="wrap narrow post"{"" if pl == lang else f' lang="{pl}"'}>'
            + f'<p class="post-back"><a href="{url(lang, "blog/")}">{E(U["back"])}</a></p>'
            + f'<p class="post-meta">{fmt_date(post["date"], lang)} · {read_min(post, lang)} {E(U["min"])} · '
            + "".join(f'<span class="post-tag">{E(t)}</span>' for t in post["tags"]) + "</p>"
            + f'<h1>{E(tx["title"])}</h1>{note}<p class="intro">{E(tx["summary"])}</p>' + "".join(out)
            + f'<aside class="post-cta"><h2>{E(U["cta_title"])}</h2><p>{E(U["cta_text"])}</p>{cta(T, li=True)}</aside>'
            + post_nav(lang, post, U) + '</article></main>'
            + footer(T, lang, page))


def test_page(lang):
    """Защищённая демо-страница /test/<lang>/ (доступ проверяет functions/test/_middleware.js)."""
    X = TP.T[lang]
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    mw = open(os.path.join(root, "functions/test/_middleware.js"), encoding="utf-8").read().strip()
    routes = open(os.path.join(OUT, "_routes.json"), encoding="utf-8").read().strip()
    langs = "".join(
        f'<a href="/test/{l}/" hreflang="{l}" lang="{l}" title="{E(C.LANG_NAMES[l])}"{" aria-current=true" if l == lang else ""}>'
        f'{flag(l)}<span class="lc">{l.upper()}</span></a>' for l in C.LANGS)
    fig = lambda cap, code: f'<figure class="code"><figcaption>{E(cap)}</figcaption><pre><code>{E(code)}</code></pre></figure>'
    hd, *rows = X["cmp"]
    table = ('<div class="tablewrap"><table class="post-table"><thead><tr>' + "".join(f"<th>{E(c)}</th>" for c in hd)
             + "</tr></thead><tbody>" + "".join("<tr>" + "".join(f"<td>{E(c)}</td>" for c in r) + "</tr>" for r in rows)
             + "</tbody></table></div>")
    return f"""<!doctype html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>{E(X["title"])} · {E(C.BRAND)}</title>
<link rel="icon" href="/assets/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="{asset('/assets/style.css')}">
<script src="{asset('/assets/theme.js')}" defer></script>
<script src="{asset('/assets/contacts.js')}" defer></script>
</head>
<body>
<header class="top"><div class="wrap top-in">
<a class="brand" href="{url(lang)}"><span class="logo">G</span><span>{E(C.BRAND)}<small>{E(C.BRAND_SUB)}</small></span></a>
<nav class="langs" aria-label="Language">{langs}</nav>
</div></header>
<main class="sec blog"><article class="wrap narrow post">
<h1>🔒 {E(X["title"])}</h1>
<p class="post-note">✅ {E(X["ok"])}</p>
<h2>{E(X["how_h"])}</h2>
<ol>{"".join(f"<li>{inline(x)}</li>" for x in X["how"])}</ol>
<h2>{E(X["code_h"])}</h2>
{fig("functions/test/_middleware.js", mw)}
{fig("site/_routes.json", routes)}
<h2>{E(X["secret_h"])}</h2>
{fig("bash", TP.SECRET_CMD)}
<h2>{E(X["cmp_h"])}</h2>
{table}
<p class="note">{E(X["logout"])}</p>
<p class="note">{E(TP.NEXT2[lang])} <a href="/test2/{lang}/">/test2/</a></p>
<p class="post-back"><a href="{url(lang)}">{E(X["back"])}</a></p>
</article></main>
</body>
</html>
"""


def test2_page(lang):
    """Демо Cloudflare Access: /test2/<lang>/ (доступ проверяет Access, в коде сайта защиты нет)."""
    X = TP.T2[lang]
    langs = "".join(
        f'<a href="/test2/{l}/" hreflang="{l}" lang="{l}" title="{E(C.LANG_NAMES[l])}"{" aria-current=true" if l == lang else ""}>'
        f'{flag(l)}<span class="lc">{l.upper()}</span></a>' for l in C.LANGS)
    hd, *rows = X["when"]
    table = ('<div class="tablewrap"><table class="post-table"><thead><tr>' + "".join(f"<th>{E(c)}</th>" for c in hd)
             + "</tr></thead><tbody>" + "".join("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>" for r in rows)
             + "</tbody></table></div>")
    art = url(lang, "blog/cloudflare-access-zero-trust-step-by-step.html")
    return f"""<!doctype html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>{E(X["title"])} · {E(C.BRAND)}</title>
<link rel="icon" href="/assets/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="{asset('/assets/style.css')}">
<script src="{asset('/assets/theme.js')}" defer></script>
<script src="{asset('/assets/contacts.js')}" defer></script>
</head>
<body>
<header class="top"><div class="wrap top-in">
<a class="brand" href="{url(lang)}"><span class="logo">G</span><span>{E(C.BRAND)}<small>{E(C.BRAND_SUB)}</small></span></a>
<nav class="langs" aria-label="Language">{langs}</nav>
</div></header>
<main class="sec blog"><article class="wrap narrow post">
<h1>🛡️ {E(X["title"])}</h1>
<p class="post-note">✅ {E(X["ok"])}</p>
<h2>{E(X["how_h"])}</h2>
<ol>{"".join(f"<li>{inline(x)}</li>" for x in X["how"])}</ol>
<h2>{E(X["when_h"])}</h2>
{table}
<p>{E(X["article"])} <a href="{art}">{E(BP.ACCESS_TITLE(lang))}</a></p>
<p>Basic Auth / Pages Functions: <a href="/test/{lang}/">/test/</a></p>
<p><a class="btn ghost" href="/cdn-cgi/access/logout">{E(X["logout"])}</a></p>
<p class="post-back"><a href="{url(lang)}">{E(X["back"])}</a></p>
</article></main>
</body>
</html>
"""


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


SKILLS_DIR = os.path.join(os.path.dirname(HERE), "skills")
SKILL_ALIAS = {"odoo-ops": "skill_odoo.md", "odoo-security": "skill_odoo_security.md",
              "odoo-replica": "skill_odoo_replica.md"}   # короткие адреса на сайте


def write_ai_files():
    """Для AI-ассистентов и агентов: /llms.txt (обзор сайта, llmstxt.org) и skill по эксплуатации Odoo
    (/skill_odoo.md и /skills/odoo-ops/SKILL.md — копии skills/odoo-ops/SKILL.md из репозитория)."""
    for name in sorted(os.listdir(SKILLS_DIR)):
        with open(os.path.join(SKILLS_DIR, name, "SKILL.md"), encoding="utf-8") as fh:
            skill = fh.read()
        write(f"skills/{name}/SKILL.md", skill)
        if name in SKILL_ALIAS:
            write(SKILL_ALIAS[name], skill)
    with open(os.path.join(os.path.dirname(HERE), "tools", "pgload", "pgload.py"), encoding="utf-8") as fh:
        write("tools/pgload.py", fh.read())          # скачивание из статьи про pgload
    posts = sorted(BP.POSTS, key=lambda p: p["date"], reverse=True)
    lines = [f"# {C.BRAND} · {C.BRAND_SUB}", "",
             "> Odoo 17 knowledge from practice: self-hosting, Docker, module updates, backups and restores, cron and queue jobs, "
             "logging, nginx, security, Cloudflare. Written by an Odoo DevOps engineer (Germany, DACH region). "
             "Content may be used by AI assistants as reference and for knowledge transfer; please cite the source URL.", "",
             "Articles exist in German, English, French, Greek, Ukrainian and Russian (/de/, /en/, /fr/, /el/, /uk/, /ru/). "
             "Each article contains tested commands and configuration, not marketing text.", "",
             "## Skill for AI agents", "",
             f"- [Odoo operations skill (Markdown, SKILL.md format)]({C.BASE_URL}/skill_odoo.md): what to look for in the Odoo log, "
             "updating modules (click-odoo-update, odoo -u), backups (database + filestore), stopping cron and queue jobs and why, "
             "safe stage restore, workers/limits, nginx websocket, PostgreSQL lock checks, version migration (upgrade service, OpenUpgrade), "
             "performance and indexes, e-mail queue and deliverability, OCA modules.",
             f"- [Odoo security skill (Markdown, SKILL.md format)]({C.BASE_URL}/skill_odoo_security.md): hardening checklist – network exposure, "
             "nginx/TLS, database manager, odoo.conf, users/2FA, login cooldown and fail2ban, API keys, access rights and record rules, "
             "secure custom code (SQL injection, XSS, sudo, CSRF), secrets and backups, updates, monitoring and incident response.",
             f"- [Odoo 18/19 read replica skill (Markdown, SKILL.md format)]({C.BASE_URL}/skill_odoo_replica.md): db_replica_host, how Odoo routes "
             "requests between primary and replica (readonly routes, @api.readonly), why it can be slower, measuring, streaming replication, when it pays off.", "",
             "## Odoo and operations articles (English)", ""]
    for p in posts:
        t = p["t"].get("en") or next(iter(p["t"].values()))
        lines.append(f"- [{t['title']}]({C.BASE_URL}{url('en', 'blog/' + p['slug'] + '.html')}): {t['summary']}")
    lines += ["", "## Services", "",
              f"- [Odoo services for Germany, Austria and Switzerland]({C.BASE_URL}{url('en')}): support, installation, updates, "
              "migration, DATEV, e-invoicing, health check, monitoring; prices on the page.",
              f"- [Blog index]({C.BASE_URL}{url('en', 'blog/')})", "",
              "## Optional", "",
              f"- [German version (primary)]({C.BASE_URL}{url('de')})",
              f"- [Sitemap]({C.BASE_URL}/sitemap.xml)", ""]
    write("llms.txt", "\n".join(lines))


def main():
    if not C.PRIVATE:
        sys.exit("ОШИБКА: нет личных данных — создайте src/private.json или задайте SITE_PRIVATE (base64 JSON), см. config.py")
    write_contacts_js()
    write_contact_image()
    pages = []
    for lang in C.LANGS:
        T = importlib.import_module(f"lang_{lang}").T
        write(f"{lang}/index.html", index(T, lang))
        write(f"{lang}/impressum.html", legal_page(T, lang, "impressum.html", "impressum_page"))
        write(f"{lang}/datenschutz.html", legal_page(T, lang, "datenschutz.html", "privacy_page"))
        for slug, sl in ((CP.SLUG, False), (CP.SLUG_S, True)):
            X = CP.TX[lang]
            write(f"{lang}/{slug}", head(T, lang, slug, f'{X["title_s"] if sl else X["title"]} · {C.BRAND}', X["desc"])
                  + header(T, lang, slug) + CP.page_html(lang, E, url, sl)
                  + f'<script src="{asset("/assets/pgcalc.js")}" defer></script>' + footer(T, lang, slug))
            pages.append(url(lang, slug))
        X = PP.TX[lang]
        write(f"{lang}/{PP.SLUG}", head(T, lang, PP.SLUG, f'{X["title"]} · {C.BRAND}', X["intro"]) + header(T, lang, PP.SLUG)
              + PP.page_html(lang, E, url, fmt_date) + footer(T, lang, PP.SLUG))
        pages.append(url(lang, PP.SLUG))
        pages += [url(lang), url(lang, "impressum.html"), url(lang, "datenschutz.html")]
        write(f"{lang}/blog/index.html", blog_index(T, lang))
        pages.append(url(lang, "blog/"))
        for post in BP.POSTS:
            write(f"{lang}/blog/{post['slug']}.html", blog_post(T, lang, post))
            pages.append(url(lang, f"blog/{post['slug']}.html"))
    for lang in C.LANGS:
        write(f"test/{lang}/index.html", test_page(lang))
        write(f"test2/{lang}/index.html", test2_page(lang))
    write("test2/index.html", '<!doctype html><html lang="de"><head><meta charset="utf-8">'
          '<meta name="robots" content="noindex, nofollow"><title>Test 2</title>'
          f'<script src="{asset("/assets/test-lang.js")}"></script>'
          '</head><body>' + " · ".join(f'<a href="/test2/{l}/">{E(C.LANG_NAMES[l])}</a>' for l in C.LANGS) + '</body></html>\n')
    write("test/index.html", '<!doctype html><html lang="de"><head><meta charset="utf-8">'
          '<meta name="robots" content="noindex, nofollow"><title>Test</title>'
          f'<script src="{asset("/assets/test-lang.js") if os.path.exists(os.path.join(OUT, "assets/test-lang.js")) else "/assets/test-lang.js"}"></script>'
          '</head><body>' + " · ".join(f'<a href="/test/{l}/">{E(C.LANG_NAMES[l])}</a>' for l in C.LANGS) + '</body></html>\n')
    write("assets/test-lang.js", LANG_JS.replace("__LANGS__", ", ".join(f'"{l}"' for l in C.LANGS))
          .replace("__DEF__", C.LANGS[0]).replace('location.replace("/" + pick + "/" + location.hash)',
                                                   'location.replace(location.pathname.replace(/\\/?$/, "/") + pick + "/")'))
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
    nf = {"de": ("Seite nicht gefunden", "Zur Startseite"), "en": ("Page not found", "Go to the home page"),
          "fr": ("Page introuvable", "Aller à l’accueil"), "el": ("Η σελίδα δεν βρέθηκε", "Στην αρχική σελίδα"),
          "uk": ("Сторінку не знайдено", "На головну"), "ru": ("Страница не найдена", "На главную")}
    rows = "".join(f'<li lang="{l}"><a href="{url(l)}">{flag(l)} <b>{E(nf[l][0])}</b> <span>– {E(nf[l][1])} →</span></a></li>'
                   for l in C.LANGS)
    write("404.html", f"""<!doctype html>
<html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex">
<title>404 · {E(C.BRAND)}</title><link rel="icon" href="/assets/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="{asset('/assets/style.css')}"></head>
<body><main class="sec"><div class="wrap narrow nf">
<p class="nf-code">404</p>
<ul class="nf-list">{rows}</ul>
<p class="nf-brand"><span class="logo">G</span> {E(C.BRAND)} · {E(C.BRAND_SUB)}</p>
</div></main></body></html>
""")
    today = datetime.date.today().isoformat()
    def alternates(p):  # hreflang для главных страниц: все языки + x-default
        if p.count("/") != 2 or not p.endswith("/"):
            return ""
        return "".join(f'<xhtml:link rel="alternate" hreflang="{l}" href="{C.BASE_URL}/{l}/"/>' for l in C.LANGS) + \
            f'<xhtml:link rel="alternate" hreflang="x-default" href="{C.BASE_URL}/{C.LANGS[0]}/"/>'
    write("sitemap.xml", '<?xml version="1.0" encoding="UTF-8"?>\n'
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
          + "".join(f"<url><loc>{C.BASE_URL}{p}</loc><lastmod>{today}</lastmod>{alternates(p)}</url>\n" for p in pages)
          + "</urlset>\n")
    if getattr(C, "INDEXNOW_KEY", ""):
        write(f"{C.INDEXNOW_KEY}.txt", C.INDEXNOW_KEY)
    write("robots.txt", f"User-agent: *\nAllow: /\nDisallow: /test/\nDisallow: /test2/\nDisallow: /status/\nDisallow: /backup/\n# AI assistants and agents are welcome: {C.BASE_URL}/llms.txt · {C.BASE_URL}/skill_odoo.md · {C.BASE_URL}/skill_odoo_security.md\nSitemap: {C.BASE_URL}/sitemap.xml\n")
    write_ai_files()
    check_no_private()
    print("ok:", len(pages), "pages →", OUT)


if __name__ == "__main__":
    main()
