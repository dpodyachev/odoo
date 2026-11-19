# Страница поиска /<lang>/search: статический поиск в браузере по индексу assets/search-index.json (строит search_index.py
# из английских страниц). Результаты открываются на языке посетителя (те же адреса страниц), разделы – сразу на #якорь.

SLUG = "search.html"

ICON = '<circle cx="10.5" cy="10.5" r="6.5"/><path d="m15.5 15.5 5 5"/>'

TX = {
    "de": {"nav": "Suche", "title": "Suche", "ph": "z. B. pg_dump, docker, odoo.conf, nginx …", "btn": "Suchen",
           "hint": "Durchsucht Blog, Anleitungen, Fragen & Antworten und Rechner. Der Index wird aus den englischen Seiten erstellt – suchen Sie mit englischen bzw. technischen Begriffen; die Treffer öffnen sich auf Deutsch.",
           "none": "Nichts gefunden. Weniger oder andere Wörter versuchen – oder den Anfang eines Wortes (pg_d).", "n": "Treffer", "words": "Gefunden"},
    "en": {"nav": "Search", "title": "Search", "ph": "e.g. pg_dump, docker, odoo.conf, nginx …", "btn": "Search",
           "hint": "Searches the blog, guides, Q&A and calculators. Technical terms work best; the beginning of a word is enough (pg_d, postgr).",
           "none": "Nothing found. Try fewer or other words – or the beginning of a word (pg_d).", "n": "results", "words": "Matched"},
    "fr": {"nav": "Recherche", "title": "Recherche", "ph": "p. ex. pg_dump, docker, odoo.conf, nginx …", "btn": "Rechercher",
           "hint": "Recherche dans le blog, les guides, les questions-réponses et les calculateurs. L'index est construit à partir des pages anglaises – cherchez avec des termes anglais ou techniques ; les résultats s'ouvrent en français.",
           "none": "Aucun résultat. Essayez moins de mots, d'autres mots – ou le début d'un mot (pg_d).", "n": "résultats", "words": "Trouvé"},
    "el": {"nav": "Αναζήτηση", "title": "Αναζήτηση", "ph": "π.χ. pg_dump, docker, odoo.conf, nginx …", "btn": "Αναζήτηση",
           "hint": "Αναζήτηση σε blog, οδηγούς, ερωτήσεις & απαντήσεις και υπολογιστές. Το ευρετήριο φτιάχνεται από τις αγγλικές σελίδες – αναζητήστε με αγγλικούς ή τεχνικούς όρους· τα αποτελέσματα ανοίγουν στα ελληνικά, όπου υπάρχει μετάφραση.",
           "none": "Δεν βρέθηκε τίποτα. Δοκιμάστε λιγότερες ή άλλες λέξεις – ή την αρχή μιας λέξης (pg_d).", "n": "αποτελέσματα", "words": "Βρέθηκαν"},
    "uk": {"nav": "Пошук", "title": "Пошук", "ph": "напр. pg_dump, docker, odoo.conf, nginx …", "btn": "Шукати",
           "hint": "Пошук у блозі, інструкціях, питаннях і відповідях та калькуляторах. Індекс будується з англійських сторінок – шукайте англійськими чи технічними термінами; результати відкриваються українською.",
           "none": "Нічого не знайдено. Спробуйте менше слів, інші слова – або початок слова (pg_d).", "n": "результатів", "words": "Знайдено"},
    "ru": {"nav": "Поиск", "title": "Поиск", "ph": "напр. pg_dump, docker, odoo.conf, nginx …", "btn": "Искать",
           "hint": "Поиск по блогу, инструкциям, вопросам и ответам и калькуляторам. Индекс строится по английским страницам – ищите английскими или техническими терминами; результаты открываются на русском.",
           "none": "Ничего не найдено. Попробуйте меньше слов, другие слова – или начало слова (pg_d).", "n": "результатов", "words": "Найдено"},
}


def page_html(lang, E, index_url, js_url):
    X = TX[lang]
    return (f'<main class="sec blog"><div class="wrap narrow"><h1>{E(X["title"])}</h1>'
            f'<form class="search-form" role="search" action="" onsubmit="return false">'
            f'<input id="q" name="q" type="search" autocomplete="off" spellcheck="false" placeholder="{E(X["ph"])}" aria-label="{E(X["title"])}" autofocus>'
            f'<button type="submit" class="btn primary">{E(X["btn"])}</button></form>'
            f'<p class="post-meta search-hint">{E(X["hint"])}</p>'
            f'<div id="results" class="post-list" aria-live="polite" data-lang="{lang}" data-index="{index_url}" '
            f'data-none="{E(X["none"])}" data-n="{E(X["n"])}" data-words="{E(X["words"])}"></div>'
            f'<noscript><p class="post-note">JavaScript is required for the search.</p></noscript>'
            f'</div></main><script src="{js_url}" defer></script>')
