# Поиск по сайту (статический): индекс строится при сборке из АНГЛИЙСКИХ страниц site/en/ (только <main>, без шапки/подвала).
# Документ = страница или её раздел с якорем (h2/section/article с id) – результат ведёт сразу на #якорь.
# Слова: технические токены целиком (pg_dump, odoo.conf, docker-compose) + их части; без служебных слов (STOP),
# без названия сайта/интерфейса (NOISE) и без слов, которые встречаются больше чем на MAX_DF доле страниц (шаблонный текст).
# Результат: site/assets/search-index.json + site/assets/search-words.txt (весь словарь – для ручной проверки).
import collections
import glob
import html
import json
import math
import os
import re

MAX_DF = 0.95          # шаблонный текст убирается по блокам (BOILER), поэтому тематические слова вроде docker/backup остаются
EXCLUDE = ("impressum.html", "datenschutz.html", "blog/index.html", "search.html")

STOP = set("""a about above across after afterwards again against all almost alone along already also although always am among an and another any
anybody anyhow anyone anything anyway anywhere are aren around as at back be became because become becomes becoming been before beforehand behind
being below beside besides between beyond both but by can cannot could couldn did didn do does doesn doing don done down during each eg either else
elsewhere enough etc even ever every everybody everyone everything everywhere except few for former formerly from further get gets getting give
given gives go goes going gone got had hadn has hasn have haven having he hence her here hereby herein hers herself him himself his how however i
ie if in inc indeed into is isn it its itself just keep keeps kept know known knows last later least less let lets like likely ll made make makes
making many may maybe me meanwhile might mine more moreover most mostly much must my myself namely need needed needs neither never nevertheless
new next no nobody none nor not nothing now nowhere of off often on once one ones only onto or other others otherwise our ours ourselves out over
own per perhaps please put quite rather re really s same say says see seem seemed seems seen several shall she should shouldn show shown shows
since so some somebody somehow someone something sometimes somewhere still such t take taken takes than that the their theirs them themselves
then there thereafter thereby therefore therein these they thing things this those though through throughout thus to together too toward towards
two three four five six seven eight nine ten under until up upon us use used uses using usually ve very via want wants was wasn way ways we well
were weren what whatever when whenever where whereas wherever whether which while who whoever whole whom whose why will with within without won
would wouldn yes yet you your yours yourself yourselves first second third once also simply just else able usually around one two often
always never already instead whole kind lot lots good better best bad worse worst big small large long short high low right wrong real really
true false sure fine easy hard simple simply quick quickly fast slow often day days week weeks month months year years time times today tomorrow
yesterday hour hours minute minutes min sec ago now soon still again each every case cases part parts point example examples e g vs per cent
percent thing things way something anything nothing everything people person someone anyone everyone place""".split())

NOISE = set("""goldberg odoo services service dmytro podyachev book call article articles blog read previous next links link copy written
written min reading sections section contents more less here also see home top menu back page pages note short version""".split())

GLOSSARY = set("""odoo community enterprise saas online odoo.sh studio module modules addon addons manifest model models field fields view views
qweb owl orm xml python postgresql postgres psql docker compose nginx traefik apache certbot letsencrypt ssl tls https cron worker workers
longpolling websocket gevent filestore backup backups restore dump replica replication wal vacuum index indexes upgrade migration staging stage
neutralize crm sales sale quotation invoice invoices invoicing accounting journal ledger tax taxes vat datev elster gobd fiscal payment payments
bank reconciliation inventory warehouse stock picking delivery receipt purchase vendor manufacturing mrp bom workcenter routing pos point-of-sale
ecommerce website shop helpdesk project timesheet timesheets planning hr payroll employee recruitment expenses subscription rental documents sign
knowledge spreadsheet dashboard discuss chatter activity email smtp imap pop3 gmail outlook microsoft google oauth oauth2 telegram whatsapp bot
printer printing pdf wkhtmltopdf report reports label barcode iot partner contact lead opportunity pipeline pricelist product variant lot serial
multi-company user users group groups access rights security password 2fa firewall fail2ban ssh vps hetzner cloudflare r2 s3 rclone rsync
monitoring logs log logging alert alerts uptime performance memory cpu ram disk swap limit limits timeout proxy proxy_mode dbfilter list_db
admin_passwd master translation translations language languages localization l10n gdpr dsgvo impressum hosting license licence licensing price
pricing cost costs calculator sap oca github gitlab bitbucket repository git ci deployment deploy contractor checklist""".split())

BRAND = re.compile(r"goldberg|podyachev")    # название сайта и автора – не искать, даже внутри доменов

TOK = re.compile(r"[A-Za-z][A-Za-z0-9]*(?:[_.\-/][A-Za-z0-9]+)*")


def _text(s):
    s = re.sub(r"<(script|style|svg)[^>]*>.*?</\1>", " ", s, flags=re.S)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s))).strip()


def words(text):
    out = []
    for m in TOK.finditer(text):
        w = m.group(0).lower().strip("._-/")
        if "/" in w and w.count("/") > 1:           # пути: /var/lib/odoo → части
            parts = [p for p in w.split("/") if p]
        else:
            parts = [w]
        for w in parts:
            subs = [w] + ([p for p in re.split(r"[_.\-/]", w) if len(p) >= 3] if re.search(r"[_.\-/]", w) else [])
            for x in subs:
                if len(x) < 2 or x.isdigit() or x in STOP or x in NOISE or BRAND.search(x):
                    continue
                if not re.search(r"[a-z]", x) or HEXLIKE.match(x) or len(x) > 40 or re.match(r"^[a-z]\.", x):
                    continue
                out.append(x)
    return out


BLOCK = re.compile(r"<(p|li|a|h[1-6]|figcaption|td|th|button|span|small|div)\b[^>]*>(.*?)</\1>", re.S)
STRONG = re.compile(r"<(code|pre|h1|h2|h3|b|strong|th|td|figcaption|i)\b[^>]*>(.*?)</\1>", re.S)
HEXLIKE = re.compile(r"^(?=.*\d)[0-9a-f]{3,}$|^[a-z]\d{1,3}$|^\d+[a-z]{1,2}\d*$")


def blocks(s):
    return {_text(m.group(2)) for m in BLOCK.finditer(s)} - {""}


def docs_of(path, url, s):
    """Страница → документы: части до первого якоря и разделы с якорем (h2/section/article с id)."""
    m = re.search(r"<main.*?</main>", s, re.S)
    s = m.group(0) if m else s
    title = _text(re.search(r"<h1[^>]*>(.*?)</h1>", s, re.S).group(1)) if "<h1" in s else ""
    cuts = [(m.start(), m.group(2)) for m in re.finditer(r'<(h2|section|article)\b[^>]*\bid="([^"]+)"', s)]
    res, pos, cur = [], 0, None
    for st, aid in cuts + [(len(s), None)]:
        chunk = s[pos:st]
        h = re.search(r"<h2[^>]*>(.*?)</h2>", chunk, re.S)
        res.append({"u": url + (f"#{cur}" if cur else ""), "h": _text(h.group(1)).lstrip("# ").strip() if (cur and h) else "",
                    "text": _text(chunk)})
        pos, cur = st, aid
    return title, [d for d in res if d["text"]]


def build(site_dir, out_dir, langs=("en",)):
    pages = []
    for f in sorted(glob.glob(f"{site_dir}/en/*.html") + glob.glob(f"{site_dir}/en/blog/*.html")):
        rel = os.path.relpath(f, f"{site_dir}/en")
        if rel in EXCLUDE:
            continue
        url = rel[:-5] if rel.endswith(".html") else rel
        url = "" if url == "index" else url
        pages.append((url, open(f, encoding="utf-8").read()))
    bdf = collections.Counter()
    mains = []
    for url, s in pages:
        m = re.search(r"<main.*?</main>", s, re.S)
        mains.append((url, m.group(0) if m else s))
        bdf.update(blocks(mains[-1][1]))
    boiler = {b for b, c in bdf.items() if c > 0.3 * len(pages) and len(b) > 2}
    strong = set()
    for url, s in mains:
        for m in STRONG.finditer(s):
            strong.update(words(_text(m.group(2))))
        strong.update(words(" ".join(re.findall(r'class="post-tag"[^>]*>([^<]+)<', s))))
    pages = []
    for url, s in mains:
        for b in sorted(boiler, key=len, reverse=True):
            s = s.replace(b, " ")
        pages.append((url, s))
    docs, df_page = [], collections.Counter()
    for url, s in pages:
        title, ds = docs_of(url, url, s)
        page_words = set()
        for d in ds:
            ws = words(d["text"] + " " + d["h"] + " " + d["h"])
            d["tf"] = collections.Counter(ws)
            d["t"] = title
            page_words |= set(ws)
            docs.append(d)
        tw = words(title)
        for d in ds:                                  # слова заголовка страницы – в каждом разделе, с весом
            d["tf"].update(tw * 3)
        df_page.update(page_words)
    n_pages = len(pages)
    # тема: слово было в «сильном» месте (код, заголовок, жирный, таблица, тег), техническое по форме или из словаря Odoo
    topical = lambda w: w in strong or w in GLOSSARY or re.search(r"[_.\-/0-9]", w)
    common = {w for w, c in df_page.items() if c > MAX_DF * n_pages or not topical(w)}
    vocab = sorted(w for w in df_page if w not in common)
    widx = {}
    df_doc = collections.Counter()
    for d in docs:
        df_doc.update(w for w in d["tf"] if w not in common)
    N = len(docs)
    for i, d in enumerate(docs):
        L = sum(d["tf"].values()) or 1
        for w, c in d["tf"].items():
            if w in common:
                continue
            sc = (c / L) ** .5 * math.log(1 + N / df_doc[w])
            widx.setdefault(w, []).append([i, round(sc * 100)])
    # названия страниц на всех языках (если страница переведена) – результаты показываются на языке посетителя
    titles, heads = {}, {}
    for url, _ in pages:
        tl = {}
        for lang in langs:
            f = f"{site_dir}/{lang}/" + ("index" if url == "" else url) + ".html"
            if os.path.exists(f):
                m = re.search(r"<h1[^>]*>(.*?)</h1>", open(f, encoding="utf-8").read(), re.S)
                if m:
                    tl[lang] = _text(m.group(1))
                    for d in docs_of(url, url, open(f, encoding="utf-8").read())[1]:     # заголовки разделов на этом языке
                        if d["h"]:
                            heads.setdefault(d["u"], {})[lang] = d["h"]
        titles[url] = tl
    out = {"d": [[d["u"], heads.get(d["u"], {"en": d["h"]} if d["h"] else {})] for d in docs], "p": titles, "w": widx}
    os.makedirs(out_dir, exist_ok=True)
    js = json.dumps(out, ensure_ascii=False, separators=(",", ":"))
    open(f"{out_dir}/search-index.json", "w", encoding="utf-8").write(js)
    open(f"{out_dir}/search-words.txt", "w", encoding="utf-8").write(
        f"# {len(vocab)} words from {n_pages} English pages ({N} sections); dropped as too common (> {int(MAX_DF*100)}% of pages): "
        + " ".join(sorted(common)) + "\n" + "\n".join(vocab) + "\n")
    return {"pages": n_pages, "docs": N, "words": len(vocab), "common": len(common), "bytes": len(js.encode())}


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    print(build(os.path.join(here, "..", "site"), os.path.join(here, "..", "site", "assets")))
