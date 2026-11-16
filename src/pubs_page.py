# Страница «Публикации»: статьи автора на внешних площадках (Medium и т. п.). Значок газеты в меню. 6 языков.
# Новая публикация: добавить запись в PUBS (самая новая – первой), затем python3 src/build.py.

SLUG = "publications.html"

ICON = ('<path d="M4 5.5h13v13a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2z"/><path d="M17 9h3v9.5a2 2 0 0 1-4 0"/>'
        '<path d="M7 9h7M7 12.5h7M7 16h4"/>')

PUBS = [
    {
        "date": "2026-11-16",
        "outlet": "Medium",
        "url": "https://medium.com/@dpodiatschev/replicas-in-odoo-19-it-can-slow-system-dfb20db4b959",
        "tag_url": "https://medium.com/tag/odoo-19",
        "lang": "EN",
        "blog": "odoo-19-postgresql-read-replica",
        "t": {
            "de": ("Read-Replicas in Odoo 19: warum sie das System verlangsamen können",
                   "Wie Odoo 18/19 Anfragen zwischen Primary und Replica verteilt, warum jeder schreibende Klick doppelt zahlt und wie man misst."),
            "en": ("Read replicas in Odoo 19: why they can slow the system down",
                   "How Odoo 18/19 splits requests between primary and replica, why every writing click pays twice, and how to measure it."),
            "fr": ("Répliques en lecture dans Odoo 19 : pourquoi elles peuvent ralentir le système",
                   "Comment Odoo 18/19 répartit les requêtes entre primaire et réplique, pourquoi chaque clic d'écriture paie deux fois et comment mesurer."),
            "el": ("Read replicas στο Odoo 19: γιατί μπορεί να επιβραδύνουν το σύστημα",
                   "Πώς το Odoo 18/19 μοιράζει τα αιτήματα μεταξύ primary και replica, γιατί κάθε κλικ εγγραφής πληρώνει διπλά και πώς να μετρήσετε."),
            "uk": ("Read-репліки в Odoo 19: чому вони можуть сповільнити систему",
                   "Як Odoo 18/19 розподіляє запити між майстром і реплікою, чому кожен клік із записом платить двічі і як це виміряти."),
            "ru": ("Read-реплики в Odoo 19: почему они могут замедлить систему",
                   "Как Odoo 18/19 распределяет запросы между мастером и репликой, почему каждый клик с записью платит дважды и как это измерить."),
        },
    },
]

TX = {
    "de": {"nav": "Publikationen", "title": "Publikationen", "intro": "Meine Artikel auf anderen Plattformen – oft eine kürzere oder englische Fassung eines Blogartikels.",
           "read": "Lesen auf", "also": "Ausführlich im Blog", "tag": "Weitere Artikel zum Thema"},
    "en": {"nav": "Publications", "title": "Publications", "intro": "My articles on other platforms – often a shorter or English version of a blog post.",
           "read": "Read on", "also": "In detail on the blog", "tag": "More articles on the topic"},
    "fr": {"nav": "Publications", "title": "Publications", "intro": "Mes articles sur d'autres plateformes – souvent une version plus courte ou anglaise d'un article du blog.",
           "read": "Lire sur", "also": "En détail sur le blog", "tag": "Autres articles sur le sujet"},
    "el": {"nav": "Δημοσιεύσεις", "title": "Δημοσιεύσεις", "intro": "Τα άρθρα μου σε άλλες πλατφόρμες – συχνά μια συντομότερη ή αγγλική εκδοχή ενός άρθρου του blog.",
           "read": "Διαβάστε στο", "also": "Αναλυτικά στο blog", "tag": "Περισσότερα άρθρα για το θέμα"},
    "uk": {"nav": "Публікації", "title": "Публікації", "intro": "Мої статті на інших майданчиках – часто коротша або англійська версія статті з блогу.",
           "read": "Читати на", "also": "Детально в блозі", "tag": "Інші статті на тему"},
    "ru": {"nav": "Публикации", "title": "Публикации", "intro": "Мои статьи на других площадках – часто более короткая или английская версия статьи из блога.",
           "read": "Читать на", "also": "Подробно в блоге", "tag": "Другие статьи по теме"},
}


def page_html(lang, E, url, fmt_date):
    X = TX[lang]
    items = []
    for p in PUBS:
        title, summary = p["t"].get(lang) or p["t"]["en"]
        extra = []
        if p.get("blog"):
            extra.append(f'<a href="{url(lang, "blog/" + p["blog"] + ".html")}">{E(X["also"])} →</a>')
        if p.get("tag_url"):
            extra.append(f'<a href="{E(p["tag_url"])}" target="_blank" rel="noopener">{E(X["tag"])} ({E(p["outlet"])})</a>')
        items.append(
            f'<article class="post-card"><p class="post-meta">{fmt_date(p["date"], lang)} · <b>{E(p["outlet"])}</b> · {E(p["lang"])}</p>'
            f'<h2><a href="{E(p["url"])}" target="_blank" rel="noopener">{E(title)}</a></h2><p>{E(summary)}</p>'
            f'<p class="post-tags">{" · ".join(extra)}</p>'
            f'<a class="more" href="{E(p["url"])}" target="_blank" rel="noopener">{E(X["read"])} {E(p["outlet"])} ↗</a></article>')
    return (f'<main class="sec blog"><div class="wrap narrow"><h1>{E(X["title"])}</h1><p class="intro">{E(X["intro"])}</p>'
            f'<div class="post-list">{"".join(items)}</div></div></main>')
