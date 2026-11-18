# Статьи блога. Каждая статья: slug, date, tags, code (общие для всех языков блоки кода) и t[lang] = title/summary/body.
# body — список блоков: ("p", текст) ("h", подзаголовок) ("code", ключ) ("ul"/"ol", [пункты]) ("note", текст)
# ("table", [[заголовки], [строка], ...]). В тексте: `код` и **жирный**. Нет перевода для языка — показывается EN с пометкой.
# Имена баз/серверов в примерах нейтральные (mydb, stage.example.com) — без данных клиентов.

POSTS = []

# ---------------------------------------------------------------------------------------------------------------------
POSTS.append({
    "slug": "odoo-17-python-3-14-docker",
    "date": "2026-11-15",
    "tags": ["Docker", "Python 3.14", "Odoo 17"],
    "code": {
        "compose": ("docker-compose.yml", """services:
  odoo:
    image: odoo17-py314:latest          # new image: Python 3.14 + dependencies, no Odoo code inside
    restart: unless-stopped
    depends_on: [db]
    command: odoo -c /etc/odoo/odoo.conf
    volumes:
      # Odoo 17 source from Git, mounted where Python 3.14 looks for packages
      - ./extra_addons/odoo:/usr/local/lib/python3.14/site-packages/odoo
      - ./extra_addons/custom:/mnt/extra-addons
      - ./etc/odoo.conf:/etc/odoo/odoo.conf:ro
      - odoo-data:/var/lib/odoo
  db:
    image: postgres:16
    restart: unless-stopped
    environment:
      POSTGRES_USER: odoo
      POSTGRES_PASSWORD_FILE: /run/secrets/pg_password
    volumes:
      - db-data:/var/lib/postgresql/data

volumes:
  odoo-data:
  db-data:"""),
        "dockerfile": ("docker/odoo17-py314/Dockerfile", """FROM python:3.14-slim-trixie

# runtime libraries for Odoo
RUN apt-get update && apt-get install -y --no-install-recommends \\
        libpq5 libxml2 libxslt1.1 libjpeg62-turbo libldap2 libsasl2-2 \\
        fonts-dejavu-core node-less \\
    && rm -rf /var/lib/apt/lists/*

# Python dependencies: Odoo 17 requirements, pins raised to versions with 3.14 support
COPY requirements-py314.txt /tmp/
RUN apt-get update && apt-get install -y --no-install-recommends \\
        build-essential libpq-dev libldap2-dev libsasl2-dev \\
    && pip install --no-cache-dir -r /tmp/requirements-py314.txt \\
    && apt-get purge -y build-essential libpq-dev libldap2-dev libsasl2-dev \\
    && apt-get autoremove -y && rm -rf /var/lib/apt/lists/*

# 'odoo' command - the code itself comes from the mounted Git checkout
RUN printf '#!/usr/bin/env python3\\nimport odoo\\nodoo.cli.main()\\n' > /usr/local/bin/odoo \\
    && chmod +x /usr/local/bin/odoo \\
    && useradd -m -d /var/lib/odoo -u 101 odoo \\
    && mkdir -p /mnt/extra-addons && chown -R odoo /var/lib/odoo /mnt/extra-addons

USER odoo
EXPOSE 8069 8072"""),
        "steps": ("bash", """# 1) backup: database + filestore
docker compose exec -T db pg_dump -U odoo -Fc mydb > mydb-$(date +%F).dump
docker compose exec -T odoo tar czf - -C /var/lib/odoo filestore/mydb > filestore-$(date +%F).tgz

# 2) build the new image (keep the old one for rollback)
docker build -t odoo17-py314:latest ./docker/odoo17-py314

# 3) does Odoo import under 3.14?
docker compose run --rm --no-deps odoo \\
    python3 -c "import sys, odoo; print(sys.version.split()[0], odoo.release.version)"

# 4) start and watch the log
docker compose up -d odoo
docker compose logs -f --tail=200 odoo | grep -E "ERROR|Traceback|ImportError|Warning\""""),
        "rollback": ("bash", """# rollback: previous image in docker-compose.yml (and the old site-packages path), then
docker compose up -d odoo"""),
    },
    "t": {
        "de": {
            "title": "Odoo 17 auf Python 3.14 umstellen – mit docker-compose",
            "summary": "Eigenes Image odoo17-py314, Odoo-Quellcode aus Git in site-packages gemountet, Prüfung auf Stage und Rücksprung in einer Minute.",
            "body": [
                ("p", "Ein bestehendes Odoo 17 läuft in Docker – und soll auf eine neuere Python-Version, hier **3.14**. Gründe: Sicherheitsupdates des Basis-Images, neuere Bibliotheken für eigene Module, oft auch spürbar schnellere Python-Laufzeit. Odoo 17 wurde für Python 3.10–3.12 entwickelt, 3.14 ist offiziell nicht freigegeben – deshalb gilt: **erst Stage, dann Produktion**."),
                ("h", "Die Idee: Image und Odoo-Code trennen"),
                ("p", "Das neue Image `odoo17-py314:latest` enthält nur Python 3.14 und die Abhängigkeiten. Der Odoo-Code selbst kommt aus einem Git-Checkout und wird dorthin gemountet, wo Python Pakete sucht: `./extra_addons/odoo:/usr/local/lib/python3.14/site-packages/odoo`. So lassen sich Odoo-Patches per `git pull` einspielen, ohne das Image neu zu bauen."),
                ("code", "compose"),
                ("note", "Wichtig: Der Pfad enthält die Python-Version. Beim Wechsel von 3.12 auf 3.14 muss auch `python3.12` → `python3.14` im Volume angepasst werden – sonst findet Python das Paket `odoo` nicht."),
                ("h", "Das Image"),
                ("code", "dockerfile"),
                ("p", "Die `requirements.txt` von Odoo 17 pinnt Versionen für ältere Python-Versionen. Für 3.14 werden die Pins für Pakete mit C-Erweiterungen (z. B. `gevent`, `greenlet`, `lxml`, `psycopg2`, `Pillow`, `reportlab`) auf Versionen angehoben, für die es 3.14-Wheels gibt. `wkhtmltopdf` (PDF-Berichte) wird wie bisher separat installiert."),
                ("h", "Ablauf"),
                ("code", "steps"),
                ("ul", [
                    "Auf Stage alle wichtigen Abläufe durchklicken: Angebote, Rechnungen, Lager, PDF-Berichte, E-Mail (in den Mail-Catcher), geplante Aktionen.",
                    "Im Log auf `ImportError`, `DeprecationWarning` und `SyntaxWarning` achten – ältere Module mit ungültigen Escape-Sequenzen in Strings fallen hier zuerst auf. Seit Python 3.13 fehlen außerdem einige alte Standardmodule (PEP 594).",
                    "Ein Modul-Update (`-u`) ist für den reinen Python-Wechsel nicht nötig – das Datenbankschema ändert sich nicht.",
                ]),
                ("h", "Rücksprung"),
                ("code", "rollback"),
                ("p", "Weil Datenbank und Filestore unverändert bleiben, dauert der Rücksprung so lange wie ein Container-Neustart."),
            ],
        },
        "en": {
            "title": "Moving Odoo 17 to Python 3.14 – with docker-compose",
            "summary": "A custom odoo17-py314 image, Odoo source from Git mounted into site-packages, testing on stage and a one-minute rollback.",
            "body": [
                ("p", "An existing Odoo 17 runs in Docker and should move to a newer Python, here **3.14**. Reasons: security updates of the base image, newer libraries for custom modules, and often a noticeably faster Python runtime. Odoo 17 was built for Python 3.10–3.12; 3.14 is not officially supported – so the rule is **stage first, production second**."),
                ("h", "The idea: separate the image from the Odoo code"),
                ("p", "The new image `odoo17-py314:latest` only contains Python 3.14 and the dependencies. The Odoo code comes from a Git checkout and is mounted where Python looks for packages: `./extra_addons/odoo:/usr/local/lib/python3.14/site-packages/odoo`. Odoo patches are then a `git pull` away, without rebuilding the image."),
                ("code", "compose"),
                ("note", "Important: the path contains the Python version. When moving from 3.12 to 3.14, change `python3.12` → `python3.14` in the volume too – otherwise Python will not find the `odoo` package."),
                ("h", "The image"),
                ("code", "dockerfile"),
                ("p", "Odoo 17's `requirements.txt` pins versions for older Pythons. For 3.14, raise the pins of packages with C extensions (e.g. `gevent`, `greenlet`, `lxml`, `psycopg2`, `Pillow`, `reportlab`) to versions that ship 3.14 wheels. `wkhtmltopdf` (PDF reports) is installed separately as before."),
                ("h", "Procedure"),
                ("code", "steps"),
                ("ul", [
                    "On stage, click through all key flows: quotations, invoices, inventory, PDF reports, e-mail (into a mail catcher), scheduled actions.",
                    "Watch the log for `ImportError`, `DeprecationWarning` and `SyntaxWarning` – older modules with invalid escape sequences in strings show up here first. Since Python 3.13 some old standard modules are gone as well (PEP 594).",
                    "A module update (`-u`) is not needed for a pure Python switch – the database schema does not change.",
                ]),
                ("h", "Rollback"),
                ("code", "rollback"),
                ("p", "Database and filestore stay untouched, so a rollback takes as long as a container restart."),
            ],
        },
        "uk": {
            "title": "Перехід Odoo 17 на Python 3.14 у docker-compose",
            "summary": "Власний образ odoo17-py314, код Odoo з Git змонтовано в site-packages, перевірка на stage і відкат за хвилину.",
            "body": [
                ("p", "Наявний Odoo 17 працює в Docker, і його треба перевести на новіший Python, тут **3.14**. Навіщо: оновлення безпеки базового образу, свіжі бібліотеки для власних модулів, часто помітно швидший Python. Odoo 17 розроблявся під Python 3.10–3.12, 3.14 офіційно не підтримується. Тому правило: **спершу stage, потім прод**."),
                ("h", "Ідея: розділити образ і код Odoo"),
                ("p", "Новий образ `odoo17-py314:latest` містить лише Python 3.14 і залежності. Код Odoo береться з Git-репозиторію і монтується туди, де Python шукає пакети: `./extra_addons/odoo:/usr/local/lib/python3.14/site-packages/odoo`. Патчі Odoo тоді ставляться через `git pull`, без перезбирання образу."),
                ("code", "compose"),
                ("note", "Важливо: у шляху є версія Python. При переході з 3.12 на 3.14 змініть у volume `python3.12` → `python3.14`, інакше Python не знайде пакет `odoo`."),
                ("h", "Образ"),
                ("code", "dockerfile"),
                ("p", "`requirements.txt` в Odoo 17 фіксує версії для старіших Python. Для 3.14 піднімаємо версії пакетів із C-розширеннями (`gevent`, `greenlet`, `lxml`, `psycopg2`, `Pillow`, `reportlab` тощо) до тих, що мають wheels для 3.14. `wkhtmltopdf` (PDF-звіти) ставиться окремо, як і раніше."),
                ("h", "Порядок дій"),
                ("code", "steps"),
                ("ul", [
                    "На stage пройти всі ключові процеси: пропозиції, рахунки, склад, PDF-звіти, пошта (у mail catcher), заплановані дії.",
                    "У лозі стежити за `ImportError`, `DeprecationWarning` і `SyntaxWarning`. Старі модулі з некоректними escape-послідовностями в рядках вилізуть першими. З Python 3.13 також прибрано кілька старих стандартних модулів (PEP 594).",
                    "Оновлення модулів (`-u`) для самої зміни Python не потрібне: схема бази не змінюється.",
                ]),
                ("h", "Відкат"),
                ("code", "rollback"),
                ("p", "База і filestore не змінюються, тому відкат триває стільки ж, скільки перезапуск контейнера."),
            ],
        },
        "ru": {
            "title": "Перевод Odoo 17 на Python 3.14 в docker-compose",
            "summary": "Свой образ odoo17-py314, код Odoo из Git смонтирован в site-packages, проверка на stage и откат за минуту.",
            "body": [
                ("p", "Существующий Odoo 17 работает в Docker, и его нужно перевести на более новый Python, здесь **3.14**. Зачем: обновления безопасности базового образа, свежие библиотеки для собственных модулей, часто заметно более быстрый Python. Odoo 17 разрабатывался под Python 3.10–3.12, 3.14 официально не поддерживается. Поэтому правило: **сначала stage, потом прод**."),
                ("h", "Идея: разделить образ и код Odoo"),
                ("p", "Новый образ `odoo17-py314:latest` содержит только Python 3.14 и зависимости. Код Odoo берётся из Git-репозитория и монтируется туда, где Python ищет пакеты: `./extra_addons/odoo:/usr/local/lib/python3.14/site-packages/odoo`. Патчи Odoo тогда ставятся через `git pull`, без пересборки образа."),
                ("code", "compose"),
                ("note", "Важно: в пути есть версия Python. При переходе с 3.12 на 3.14 поменяйте в volume `python3.12` → `python3.14`, иначе Python не найдёт пакет `odoo`."),
                ("h", "Образ"),
                ("code", "dockerfile"),
                ("p", "`requirements.txt` в Odoo 17 фиксирует версии для старых Python. Для 3.14 поднимаем версии пакетов с C-расширениями (`gevent`, `greenlet`, `lxml`, `psycopg2`, `Pillow`, `reportlab` и др.) до тех, у которых есть wheels под 3.14. `wkhtmltopdf` (PDF-отчёты) ставится отдельно, как и раньше."),
                ("h", "Порядок действий"),
                ("code", "steps"),
                ("ul", [
                    "На stage пройти все ключевые процессы: предложения, счета, склад, PDF-отчёты, почта (в mail catcher), запланированные действия.",
                    "В логе следить за `ImportError`, `DeprecationWarning` и `SyntaxWarning`. Старые модули с некорректными escape-последовательностями в строках вылезут первыми. С Python 3.13 также убрано несколько старых стандартных модулей (PEP 594).",
                    "Обновление модулей (`-u`) для самой смены Python не нужно: схема базы не меняется.",
                ]),
                ("h", "Откат"),
                ("code", "rollback"),
                ("p", "База и filestore не меняются, поэтому откат занимает столько же, сколько перезапуск контейнера."),
            ],
        },
    },
})

# ---------------------------------------------------------------------------------------------------------------------
POSTS.append({
    "slug": "odoo-module-update-click-odoo-update",
    "date": "2026-11-15",
    "tags": ["Updates", "click-odoo-update", "odoo -u"],
    "code": {
        "click": ("bash · click-odoo-update", """# once per container (user site-packages): pip install --user click-odoo-contrib

# which modules changed since the last update?
docker compose exec odoo /var/lib/odoo/.local/bin/click-odoo-update \\
    -c /etc/odoo/odoo.conf -d mydb --list-only

# update exactly those modules
docker compose exec odoo /var/lib/odoo/.local/bin/click-odoo-update \\
    -c /etc/odoo/odoo.conf -d mydb --i18n-overwrite

# workers must load the new Python code
docker compose restart odoo"""),
        "odoo": ("bash · odoo -u", """docker compose stop odoo

docker compose run --rm odoo odoo -c /etc/odoo/odoo.conf -d mydb \\
    -u all \\
    --workers=0 --no-http \\
    --stop-after-init \\
    --i18n-overwrite \\
    --without-demo=all

docker compose start odoo"""),
        "some": ("bash", """# only selected modules instead of everything
... -u sale_custom,stock_custom --workers=0 --no-http --stop-after-init"""),
    },
    "t": {
        "de": {
            "title": "Odoo-Module aktualisieren: click-odoo-update oder odoo -u",
            "summary": "Zwei bewährte Wege für Modul-Updates in Docker – nur geänderte Module per Prüfsumme oder vollständig ohne offene Ports. Mit Erklärung aller Schalter.",
            "body": [
                ("p", "Neuer Code liegt auf dem Server – jetzt muss die Datenbank nachziehen: neue Felder, Ansichten, Daten, Übersetzungen. Ich nutze zwei Wege, je nach Situation."),
                ("h", "a) click-odoo-update – nur das, was sich geändert hat"),
                ("p", "`click-odoo-update` aus `click-odoo-contrib` berechnet für jedes Modul eine Prüfsumme der Dateien und speichert sie in der Datenbank. Beim nächsten Lauf werden **nur Module mit geänderter Prüfsumme** aktualisiert. Bei Systemen mit Hunderten Modulen ist das der Unterschied zwischen Minuten und Sekunden."),
                ("code", "click"),
                ("ul", [
                    "`--list-only` zeigt vorher, was aktualisiert würde – ideal für einen Blick vor dem eigentlichen Lauf.",
                    "`--i18n-overwrite` lädt Übersetzungen der Module neu und **überschreibt** dabei in der Datenbank geänderte Texte. Bewusst einsetzen, wenn Anwender Bezeichnungen selbst angepasst haben.",
                    "Danach Odoo neu starten – laufende Worker kennen den neuen Python-Code sonst nicht.",
                ]),
                ("h", "b) Über Odoo selbst – ohne offene Ports"),
                ("p", "Der klassische Weg mit `-u`, aber als einmaliger Lauf in einem separaten Container, der keinen Port öffnet und sich danach selbst beendet:"),
                ("code", "odoo"),
                ("table", [
                    ["Schalter", "Wozu"],
                    ["`-u all`", "alle installierten Module aktualisieren (oder eine Liste: `-u modul_a,modul_b`)"],
                    ["`--workers=0`", "ein einziger Prozess – keine parallelen Worker während der Migration"],
                    ["`--no-http`", "kein Webserver: kein Portkonflikt mit dem laufenden Odoo, keine Nutzer im halbfertigen Zustand"],
                    ["`--stop-after-init`", "nach dem Update beenden statt weiterlaufen"],
                    ["`--i18n-overwrite`", "Übersetzungen neu laden und überschreiben (siehe oben)"],
                    ["`--without-demo=all`", "niemals Demodaten laden"],
                ]),
                ("note", "Häufiger Stolperstein: In `odoo --help` steht `--without-demo=WITHOUT_DEMO`. `WITHOUT_DEMO` ist nur der Platzhalter – der richtige Wert ist `all` (oder eine Modulliste)."),
                ("code", "some"),
                ("h", "Was wann?"),
                ("table", [
                    ["", "click-odoo-update", "odoo -u … --stop-after-init"],
                    ["Was wird aktualisiert", "nur geänderte Module", "alles oder gezielte Liste"],
                    ["Dauer bei vielen Modulen", "Sekunden bis Minuten", "Minuten bis Stunden"],
                    ["Ausfallzeit", "Neustart der Worker", "für die Dauer des Updates"],
                    ["Wann", "tägliche Deployments, Hotfixes", "Versionssprünge, nach Upgrades, wenn Prüfsummen fehlen"],
                ]),
                ("p", "In beiden Fällen gilt: vorher Backup, zuerst auf Stage, und den Log des Laufs aufheben – er ist das Protokoll der Migration."),
            ],
        },
        "en": {
            "title": "Updating Odoo modules: click-odoo-update or odoo -u",
            "summary": "Two proven ways to update modules in Docker – only changed modules via checksum, or a full update with no open ports. Every flag explained.",
            "body": [
                ("p", "New code is on the server – now the database has to catch up: new fields, views, data, translations. I use two ways, depending on the situation."),
                ("h", "a) click-odoo-update – only what changed"),
                ("p", "`click-odoo-update` from `click-odoo-contrib` computes a checksum of each module's files and stores it in the database. On the next run it updates **only modules whose checksum changed**. On systems with hundreds of modules that is the difference between minutes and seconds."),
                ("code", "click"),
                ("ul", [
                    "`--list-only` shows what would be updated – perfect for a look before the real run.",
                    "`--i18n-overwrite` reloads module translations and **overwrites** texts that were changed in the database. Use it deliberately if users customised labels themselves.",
                    "Restart Odoo afterwards – running workers do not know the new Python code otherwise.",
                ]),
                ("h", "b) Through Odoo itself – with no open ports"),
                ("p", "The classic `-u` way, but as a one-off run in a separate container that opens no port and exits when done:"),
                ("code", "odoo"),
                ("table", [
                    ["Flag", "Purpose"],
                    ["`-u all`", "update all installed modules (or a list: `-u module_a,module_b`)"],
                    ["`--workers=0`", "a single process – no parallel workers during the migration"],
                    ["`--no-http`", "no web server: no port clash with the running Odoo, no users in a half-migrated state"],
                    ["`--stop-after-init`", "exit after the update instead of serving"],
                    ["`--i18n-overwrite`", "reload and overwrite translations (see above)"],
                    ["`--without-demo=all`", "never load demo data"],
                ]),
                ("note", "Common pitfall: `odoo --help` shows `--without-demo=WITHOUT_DEMO`. `WITHOUT_DEMO` is just the placeholder – the correct value is `all` (or a module list)."),
                ("code", "some"),
                ("h", "Which one when?"),
                ("table", [
                    ["", "click-odoo-update", "odoo -u … --stop-after-init"],
                    ["What is updated", "changed modules only", "everything or a chosen list"],
                    ["Duration with many modules", "seconds to minutes", "minutes to hours"],
                    ["Downtime", "worker restart", "for the whole update"],
                    ["When", "daily deployments, hotfixes", "version jumps, after upgrades, when checksums are missing"],
                ]),
                ("p", "Either way: backup first, stage first, and keep the log of the run – it is the record of the migration."),
            ],
        },
        "uk": {
            "title": "Оновлення модулів Odoo: click-odoo-update або odoo -u",
            "summary": "Два перевірені способи оновлювати модулі в Docker: лише змінені модулі за контрольною сумою або повне оновлення без відкритих портів. З поясненням усіх ключів.",
            "body": [
                ("p", "Новий код уже на сервері, тепер базу треба підтягнути: нові поля, в'юхи, дані, переклади. Я користуюся двома способами, залежно від ситуації."),
                ("h", "а) click-odoo-update – лише те, що змінилося"),
                ("p", "`click-odoo-update` з пакета `click-odoo-contrib` рахує контрольну суму файлів кожного модуля і зберігає її в базі. Під час наступного запуску оновлюються **лише модулі зі зміненою сумою**. На системах із сотнями модулів це різниця між хвилинами і секундами."),
                ("code", "click"),
                ("ul", [
                    "`--list-only` заздалегідь показує, що буде оновлено. Зручно подивитися перед справжнім запуском.",
                    "`--i18n-overwrite` перезавантажує переклади модулів і **перезаписує** змінені в базі тексти. Використовуйте свідомо, якщо користувачі самі правили назви.",
                    "Після цього перезапустіть Odoo, інакше робочі процеси не побачать новий Python-код.",
                ]),
                ("h", "б) Через сам Odoo – без відкритих портів"),
                ("p", "Класичний шлях з `-u`, але як разовий запуск в окремому контейнері, який не відкриває порт і сам завершується:"),
                ("code", "odoo"),
                ("table", [
                    ["Ключ", "Навіщо"],
                    ["`-u all`", "оновити всі встановлені модулі (або список: `-u module_a,module_b`)"],
                    ["`--workers=0`", "один процес, без паралельних воркерів під час міграції"],
                    ["`--no-http`", "без вебсервера: немає конфлікту портів із робочим Odoo, користувачі не потрапляють у напівоновлену систему"],
                    ["`--stop-after-init`", "завершитися після оновлення, а не працювати далі"],
                    ["`--i18n-overwrite`", "перезавантажити й перезаписати переклади (див. вище)"],
                    ["`--without-demo=all`", "ніколи не завантажувати демо-дані"],
                ]),
                ("note", "Типова пастка: у `odoo --help` написано `--without-demo=WITHOUT_DEMO`. `WITHOUT_DEMO` – це лише підказка, правильне значення `all` (або список модулів)."),
                ("code", "some"),
                ("h", "Що й коли?"),
                ("table", [
                    ["", "click-odoo-update", "odoo -u … --stop-after-init"],
                    ["Що оновлюється", "лише змінені модулі", "усе або вибраний список"],
                    ["Тривалість при багатьох модулях", "секунди–хвилини", "хвилини–години"],
                    ["Простій", "перезапуск воркерів", "увесь час оновлення"],
                    ["Коли", "щоденні деплої, хотфікси", "зміна версії, після апгрейдів, коли немає контрольних сум"],
                ]),
                ("p", "В обох випадках: спершу бекап, спершу stage, і збережіть лог запуску – це протокол міграції."),
            ],
        },
        "ru": {
            "title": "Обновление модулей Odoo: click-odoo-update или odoo -u",
            "summary": "Два проверенных способа обновлять модули в Docker: только изменённые модули по контрольной сумме или полное обновление без открытых портов. С разбором всех ключей.",
            "body": [
                ("p", "Новый код уже на сервере, теперь базу нужно подтянуть: новые поля, вьюхи, данные, переводы. Я пользуюсь двумя способами, в зависимости от ситуации."),
                ("h", "а) click-odoo-update – только то, что изменилось"),
                ("p", "`click-odoo-update` из пакета `click-odoo-contrib` считает контрольную сумму файлов каждого модуля и хранит её в базе. При следующем запуске обновляются **только модули с изменившейся суммой**. На системах с сотнями модулей это разница между минутами и секундами."),
                ("code", "click"),
                ("ul", [
                    "`--list-only` заранее показывает, что будет обновлено. Удобно посмотреть перед настоящим запуском.",
                    "`--i18n-overwrite` перезагружает переводы модулей и **перезаписывает** изменённые в базе тексты. Используйте осознанно, если пользователи сами правили названия.",
                    "После этого перезапустите Odoo, иначе рабочие процессы не увидят новый Python-код.",
                ]),
                ("h", "б) Через сам Odoo – без открытых портов"),
                ("p", "Классический путь с `-u`, но как разовый запуск в отдельном контейнере, который не открывает порт и сам завершается:"),
                ("code", "odoo"),
                ("table", [
                    ["Ключ", "Зачем"],
                    ["`-u all`", "обновить все установленные модули (или список: `-u module_a,module_b`)"],
                    ["`--workers=0`", "один процесс, без параллельных воркеров во время миграции"],
                    ["`--no-http`", "без веб-сервера: нет конфликта портов с работающим Odoo, пользователи не попадают в полуобновлённую систему"],
                    ["`--stop-after-init`", "завершиться после обновления, а не работать дальше"],
                    ["`--i18n-overwrite`", "перезагрузить и перезаписать переводы (см. выше)"],
                    ["`--without-demo=all`", "никогда не загружать демо-данные"],
                ]),
                ("note", "Частая ловушка: в `odoo --help` написано `--without-demo=WITHOUT_DEMO`. `WITHOUT_DEMO` – это только подсказка, правильное значение `all` (или список модулей)."),
                ("code", "some"),
                ("h", "Что и когда?"),
                ("table", [
                    ["", "click-odoo-update", "odoo -u … --stop-after-init"],
                    ["Что обновляется", "только изменённые модули", "всё или выбранный список"],
                    ["Длительность при многих модулях", "секунды–минуты", "минуты–часы"],
                    ["Простой", "перезапуск воркеров", "всё время обновления"],
                    ["Когда", "ежедневные деплои, хотфиксы", "смена версии, после апгрейдов, когда нет контрольных сумм"],
                ]),
                ("p", "В обоих случаях: сначала бэкап, сначала stage, и сохраните лог запуска – это протокол миграции."),
            ],
        },
    },
})

# ---------------------------------------------------------------------------------------------------------------------
POSTS.append({
    "slug": "odoo-stage-restore-stop-cron-jobs",
    "date": "2026-11-15",
    "tags": ["Stage", "Backup", "Cron", "queue_job"],
    "code": {
        "restore": ("bash", """docker compose stop odoo                       # Odoo must NOT be running yet

docker compose exec -T db dropdb   -U odoo --if-exists mydb_stage
docker compose exec -T db createdb -U odoo mydb_stage
docker compose exec -T db pg_restore -U odoo -d mydb_stage --no-owner < mydb.dump

# neutralise BEFORE the first start (SQL below)
docker compose exec -T db psql -U odoo -d mydb_stage -v ON_ERROR_STOP=1 < stage-safety.sql

# filestore: the folder name must match the database name
#   .../filestore/mydb  ->  .../filestore/mydb_stage

docker compose start odoo"""),
        "sql": ("stage-safety.sql", """BEGIN;
-- 1. remember what was active (to re-enable selectively later)
CREATE TABLE IF NOT EXISTS zz_stage_cron_before AS
    SELECT id, cron_name, active FROM ir_cron;

-- 2. all scheduled actions off
UPDATE ir_cron SET active = false WHERE active;

-- 3. queue_job (if installed): nothing waiting may run
UPDATE queue_job SET state = 'cancelled'
 WHERE state IN ('pending', 'enqueued', 'started', 'wait_dependencies');

-- 4. no outgoing / incoming mail
UPDATE ir_mail_server   SET active = false;
UPDATE fetchmail_server SET active = false;

-- 5. stage URL and its own database UUID
UPDATE ir_config_parameter SET value = 'https://stage.example.com' WHERE key = 'web.base.url';
UPDATE ir_config_parameter SET value = gen_random_uuid()::text   WHERE key = 'database.uuid';
COMMIT;"""),
        "neutralize": ("bash · Odoo 16+", """docker compose run --rm odoo odoo neutralize -c /etc/odoo/odoo.conf -d mydb_stage"""),
        "conf": ("etc/odoo.conf (stage)", """[options]
; no cron thread at all on stage
max_cron_threads = 0
; without queue_job here the job runner does not start
server_wide_modules = base,web
; every e-mail ends up in Mailpit - nothing leaves the server
smtp_server = mailpit
smtp_port = 1025"""),
        "check": ("sql", """SELECT count(*) FROM ir_cron WHERE active;                 -- expected: 0
SELECT state, count(*) FROM queue_job GROUP BY state;      -- no pending / enqueued
SELECT key, value FROM ir_config_parameter WHERE key = 'web.base.url';"""),
    },
    "t": {
        "de": {
            "title": "Backup auf Stage einspielen – ohne dass Cron-Jobs und Queue-Jobs losrennen",
            "summary": "Warum Stage-Systeme Mahnungen an echte Kunden schicken können, und die Reihenfolge, mit der das nicht passiert: SQL vor dem ersten Start, neutralize, Stage-Konfiguration.",
            "body": [
                ("p", "Die Produktionsdatenbank wird auf Stage eingespielt, um ein Update zu testen. Odoo startet – und arbeitet sofort alles ab, was während der Ausfallzeit „fällig“ geworden ist: Mahnungen und Rechnungen per E-Mail, Abgleich mit Shop, Bank oder Versanddienstleister, Queue-Jobs aus der Warteschlange. Mit echten Kundendaten und echten Zugangsdaten. Der klassische Stage-Unfall."),
                ("p", "Der Kern: **Odoo startet Cron-Threads und den Job-Runner gleich beim Start.** Abschalten in der Oberfläche ist zu spät. Alles muss passieren, **bevor** Odoo die Datenbank zum ersten Mal sieht."),
                ("h", "1. Einspielen – Odoo bleibt gestoppt"),
                ("code", "restore"),
                ("h", "2. Neutralisieren per SQL"),
                ("code", "sql"),
                ("note", "Die Tabellen `queue_job` und `fetchmail_server` gibt es nur, wenn die Module installiert sind – fehlende Zeilen vorher entfernen. Die Liste `zz_stage_cron_before` hilft, auf Stage später gezielt einzelne Crons wieder einzuschalten."),
                ("p", "Seit Odoo 16 gibt es zusätzlich den eingebauten Befehl `neutralize`: er deaktiviert u. a. geplante Aktionen, Mailserver und Zahlungsanbieter und blendet ein Banner „neutralisiert“ ein. Ich nutze ihn als Basis und ergänze das SQL für Drittmodule wie `queue_job`."),
                ("code", "neutralize"),
                ("h", "3. Stage-Konfiguration als zweite Sicherung"),
                ("code", "conf"),
                ("p", "Selbst wenn eine neue Datenbank ohne Neutralisierung eingespielt wird, kann mit dieser Konfiguration nichts nach außen gehen: kein Cron-Thread, kein Job-Runner, Mails nur im Mail-Catcher."),
                ("h", "4. Prüfen"),
                ("code", "check"),
                ("ul", [
                    "Erst wenn alle drei Abfragen stimmen, Stage für Tests freigeben.",
                    "Zugangsdaten zu externen Diensten (Shop, Bank, Versand, Zahlungen) auf Stage durch Sandbox-Schlüssel ersetzen oder entfernen.",
                    "Den ganzen Ablauf als Skript ablegen – dann ist ein frisches Stage eine Sache von Minuten, und kein Schritt wird vergessen.",
                ]),
            ],
        },
        "en": {
            "title": "Restoring a backup on stage – without cron jobs and queue jobs firing",
            "summary": "Why stage systems can send dunning letters to real customers, and the order of steps that prevents it: SQL before the first start, neutralize, a stage config.",
            "body": [
                ("p", "The production database is restored on stage to test an update. Odoo starts – and immediately processes everything that became \"due\" during the downtime: dunning and invoice e-mails, syncs with the shop, bank or carriers, queued jobs. With real customer data and real credentials. The classic stage accident."),
                ("p", "The core point: **Odoo starts its cron threads and the job runner right at startup.** Switching things off in the UI is too late. Everything has to happen **before** Odoo sees the database for the first time."),
                ("h", "1. Restore – Odoo stays stopped"),
                ("code", "restore"),
                ("h", "2. Neutralise with SQL"),
                ("code", "sql"),
                ("note", "The tables `queue_job` and `fetchmail_server` only exist when the modules are installed – drop those lines otherwise. The `zz_stage_cron_before` list helps to re-enable individual crons on stage later on purpose."),
                ("p", "Since Odoo 16 there is also the built-in `neutralize` command: among other things it deactivates scheduled actions, mail servers and payment providers and shows a \"neutralized\" banner. I use it as the base and add the SQL for third-party modules such as `queue_job`."),
                ("code", "neutralize"),
                ("h", "3. A stage config as a second safety net"),
                ("code", "conf"),
                ("p", "Even if a database is restored without neutralising, nothing can leave the server with this config: no cron thread, no job runner, e-mail only in the mail catcher."),
                ("h", "4. Verify"),
                ("code", "check"),
                ("ul", [
                    "Release stage for testing only when all three queries look right.",
                    "Replace credentials for external services (shop, bank, shipping, payments) on stage with sandbox keys, or remove them.",
                    "Keep the whole procedure as a script – a fresh stage is then a matter of minutes, and no step is forgotten.",
                ]),
            ],
        },
        "uk": {
            "title": "Розгортання бекапу на stage – так, щоб cron і queue_job не запустилися",
            "summary": "Чому stage може надіслати нагадування про оплату справжнім клієнтам, і порядок дій, за якого цього не станеться: SQL до першого старту, neutralize, конфіг stage.",
            "body": [
                ("p", "Продакшн-базу розгортають на stage, щоб протестувати оновлення. Odoo стартує і одразу виконує все, що «настало» за час простою: листи з нагадуваннями й рахунками, синхронізацію з магазином, банком чи службою доставки, завдання з черги. Зі справжніми даними клієнтів і справжніми доступами. Класична аварія на stage."),
                ("p", "Головне: **Odoo запускає cron-потоки і job runner одразу під час старту.** Вимикати в інтерфейсі вже пізно. Усе треба зробити **до того**, як Odoo вперше побачить базу."),
                ("h", "1. Розгортання – Odoo зупинено"),
                ("code", "restore"),
                ("h", "2. Нейтралізація через SQL"),
                ("code", "sql"),
                ("note", "Таблиці `queue_job` і `fetchmail_server` існують лише тоді, коли встановлено відповідні модулі. Інакше приберіть ці рядки. Список `zz_stage_cron_before` допоможе потім свідомо ввімкнути окремі cron на stage."),
                ("p", "Починаючи з Odoo 16 є ще вбудована команда `neutralize`: вона, серед іншого, вимикає заплановані дії, поштові сервери та платіжних провайдерів і показує банер «neutralized». Я беру її за основу і доповнюю SQL для сторонніх модулів, як-от `queue_job`."),
                ("code", "neutralize"),
                ("h", "3. Конфіг stage як друга страховка"),
                ("code", "conf"),
                ("p", "Навіть якщо базу розгорнуть без нейтралізації, з таким конфігом нічого не піде назовні: немає cron-потоку, немає job runner, пошта лише в mail catcher."),
                ("h", "4. Перевірка"),
                ("code", "check"),
                ("ul", [
                    "Віддавати stage на тестування лише тоді, коли всі три запити показують правильний результат.",
                    "Доступи до зовнішніх сервісів (магазин, банк, доставка, платежі) на stage замінити на sandbox-ключі або прибрати.",
                    "Увесь порядок дій зберегти як скрипт: тоді свіжий stage – справа кількох хвилин, і жоден крок не забудеться.",
                ]),
            ],
        },
        "ru": {
            "title": "Развёртывание бэкапа на stage – так, чтобы cron и queue_job не запустились",
            "summary": "Почему stage может разослать напоминания об оплате реальным клиентам, и порядок действий, при котором этого не случится: SQL до первого старта, neutralize, конфиг stage.",
            "body": [
                ("p", "Продакшн-базу разворачивают на stage, чтобы протестировать обновление. Odoo стартует и сразу выполняет всё, что «наступило» за время простоя: письма с напоминаниями и счетами, синхронизацию с магазином, банком или службой доставки, задания из очереди. С реальными данными клиентов и реальными доступами. Классическая авария на stage."),
                ("p", "Главное: **Odoo запускает cron-потоки и job runner сразу при старте.** Выключать в интерфейсе уже поздно. Всё нужно сделать **до того**, как Odoo впервые увидит базу."),
                ("h", "1. Развёртывание – Odoo остановлен"),
                ("code", "restore"),
                ("h", "2. Нейтрализация через SQL"),
                ("code", "sql"),
                ("note", "Таблицы `queue_job` и `fetchmail_server` есть только тогда, когда установлены соответствующие модули. Иначе уберите эти строки. Список `zz_stage_cron_before` поможет потом осознанно включить отдельные cron на stage."),
                ("p", "Начиная с Odoo 16 есть ещё встроенная команда `neutralize`: она, среди прочего, выключает запланированные действия, почтовые серверы и платёжных провайдеров и показывает баннер «neutralized». Я беру её за основу и дополняю SQL для сторонних модулей, например `queue_job`."),
                ("code", "neutralize"),
                ("h", "3. Конфиг stage как вторая страховка"),
                ("code", "conf"),
                ("p", "Даже если базу развернут без нейтрализации, с таким конфигом ничего не уйдёт наружу: нет cron-потока, нет job runner, почта только в mail catcher."),
                ("h", "4. Проверка"),
                ("code", "check"),
                ("ul", [
                    "Отдавать stage на тестирование только тогда, когда все три запроса показывают правильный результат.",
                    "Доступы к внешним сервисам (магазин, банк, доставка, платежи) на stage заменить на sandbox-ключи или убрать.",
                    "Весь порядок действий сохранить как скрипт: тогда свежий stage – дело нескольких минут, и ни один шаг не забудется.",
                ]),
            ],
        },
    },
})

# ---------------------------------------------------------------------------------------------------------------------
POSTS.append({
    "slug": "odoo-logging-options-cheatsheet",
    "date": "2026-11-15",
    "tags": ["Logging", "odoo.conf", "CLI", "click-odoo"],
    "code": {
        "conf": ("etc/odoo.conf", """[options]
log_level = warn
log_handler = :INFO,werkzeug:WARNING,odoo.addons.sale:DEBUG
logfile = /var/log/odoo/odoo.log
; write warnings and errors into the database (Settings -> Technical -> Logging)
log_db = %d
log_db_level = warning"""),
        "cli": ("bash · odoo", """odoo -c /etc/odoo/odoo.conf \\
    --log-level=warn \\
    --log-handler=odoo.addons.sale:DEBUG \\
    --log-handler=werkzeug:WARNING \\
    --logfile=/var/log/odoo/odoo.log

# shortcuts (Odoo 17)
odoo -c /etc/odoo/odoo.conf --log-sql     # = --log-handler=odoo.sql_db:DEBUG
odoo -c /etc/odoo/odoo.conf --log-web     # = --log-handler=odoo.http:DEBUG"""),
        "click": ("bash · click-odoo-update", """click-odoo-update -c /etc/odoo/odoo.conf -d mydb \\
    --log-level=warn \\
    --logfile=/var/log/odoo/update-$(date +%F).log
# log_handler: put it into the -c config file"""),
        "wrong": ("etc/odoo.conf – wrong", """log-level = ERROR                         ; dash + capital letters: silently ignored -> stays INFO
log_level = warning                       ; unknown value: silently INFO
log_handler = odoo.addons.sale:debug      ; lowercase: silently INFO"""),
        "check": ("bash", """# what does your Odoo version accept?
odoo --help | grep -A3 -- "--log-level"
grep -n "PSEUDOCONFIG_MAPPER" -A12 odoo/netsvc.py

# what is actually set in the file?
grep -nE "^ *log" /etc/odoo/odoo.conf"""),
    },
    "t": {
        "de": {
            "title": "Odoo-Logging: warn oder warning, log_level oder --log-level? Spickzettel",
            "summary": "Konfigurationsdatei, Kommandozeile, click-odoo-update – drei Schreibweisen, drei Arten von Stufen. Eine Tabelle zum Nachschlagen und die Fehler, bei denen Odoo still auf INFO bleibt.",
            "body": [
                ("p", "Ich vergesse es selbst immer wieder: Heißt es `warn` oder `warning`? `log_level` oder `log-level`? Die Antwort hängt davon ab, **wo** man es schreibt. Hier alles auf einer Seite (geprüft am Quellcode von Odoo 17)."),
                ("h", "Die Faustregel"),
                ("ul", [
                    "**In `odoo.conf`: Unterstrich** – `log_level`, `log_handler`, `log_db_level`.",
                    "**In der Kommandozeile: Bindestrich** – `--log-level`, `--log-handler`, `--log-db-level`.",
                    "`log_level` kennt **Odoo-eigene Wörter, klein**: `warn` (nicht `warning`!), `error`, `info`, `debug` …",
                    "`log_handler` erwartet **Python-Stufen in GROSSBUCHSTABEN**: `WARNING`, `ERROR`, `DEBUG`.",
                    "`log_db_level` erwartet **Python-Stufen klein**: `warning`, `error` (Standard: `warning`).",
                ]),
                ("h", "Spickzettel"),
                ("table", [
                    ["Was", "odoo.conf", "Kommandozeile", "click-odoo-update"],
                    ["Gesamt-Stufe", "`log_level = warn`", "`--log-level=warn`", "`--log-level=warn`"],
                    ["Stufe je Logger", "`log_handler = werkzeug:WARNING,odoo.addons.sale:DEBUG`", "`--log-handler=odoo.addons.sale:DEBUG` (mehrfach möglich)", "über `-c` Konfigurationsdatei"],
                    ["Logdatei", "`logfile = /var/log/odoo/odoo.log`", "`--logfile=…`", "`--logfile=…`"],
                    ["Syslog", "`syslog = True`", "`--syslog`", "–"],
                    ["In die Datenbank", "`log_db = %d`, `log_db_level = warning`", "`--log-db=%d --log-db-level=warning`", "über `-c`"],
                    ["Abkürzungen", "–", "`--log-sql`, `--log-web`", "–"],
                ]),
                ("h", "Erlaubte Werte"),
                ("table", [
                    ["Option", "Werte"],
                    ["`log_level`", "`info` (Standard), `warn`, `error`, `critical`, `debug`, `debug_sql`, `debug_rpc`, `debug_rpc_answer`, `notset`, `test`, `runbot`"],
                    ["`log_handler`", "`PREFIX:STUFE`, Stufe = `DEBUG` · `INFO` · `WARNING` (oder `WARN`) · `ERROR` · `CRITICAL`; leerer Prefix = Root-Logger, z. B. `:INFO`"],
                    ["`log_db_level`", "`debug` · `info` · `warning` · `error` · `critical`"],
                    ["`log_db`", "`%d` = aktuelle Datenbank oder Name einer eigenen Log-Datenbank"],
                ]),
                ("h", "Beispiele"),
                ("code", "conf"),
                ("code", "cli"),
                ("p", "`click-odoo-update` (und die anderen `click-odoo`-Skripte) haben eigene Schalter `--log-level` und `--logfile` mit denselben Werten wie Odoo. Logger-genaue Einstellungen kommen aus der mit `-c` übergebenen Konfigurationsdatei."),
                ("code", "click"),
                ("h", "Die stillen Fehler"),
                ("p", "Die Kommandozeile meldet einen falschen Wert sofort (`invalid choice: 'warning'`). Die Konfigurationsdatei **nicht** – Odoo läuft einfach mit INFO weiter, und man wundert sich über volle Logs:"),
                ("code", "wrong"),
                ("note", "`log_level = warn` setzt nur die Logger `odoo` und `werkzeug` auf WARNING. Fremde Bibliotheken loggen über den Root-Logger weiter mit INFO – wer es ganz ruhig will, ergänzt `log_handler = :WARNING`."),
                ("h", "Nachprüfen statt raten"),
                ("code", "check"),
            ],
        },
        "en": {
            "title": "Odoo logging: warn or warning, log_level or --log-level? A cheat sheet",
            "summary": "Config file, command line, click-odoo-update – three spellings and three kinds of levels. One table to look things up, plus the mistakes where Odoo silently stays on INFO.",
            "body": [
                ("p", "I keep forgetting it myself: is it `warn` or `warning`? `log_level` or `log-level`? The answer depends on **where** you write it. Everything on one page (checked against the Odoo 17 source)."),
                ("h", "Rule of thumb"),
                ("ul", [
                    "**In `odoo.conf`: underscore** – `log_level`, `log_handler`, `log_db_level`.",
                    "**On the command line: dash** – `--log-level`, `--log-handler`, `--log-db-level`.",
                    "`log_level` takes **Odoo's own words, lowercase**: `warn` (not `warning`!), `error`, `info`, `debug` …",
                    "`log_handler` expects **Python levels in UPPERCASE**: `WARNING`, `ERROR`, `DEBUG`.",
                    "`log_db_level` expects **Python levels in lowercase**: `warning`, `error` (default: `warning`).",
                ]),
                ("h", "Cheat sheet"),
                ("table", [
                    ["What", "odoo.conf", "Command line", "click-odoo-update"],
                    ["Overall level", "`log_level = warn`", "`--log-level=warn`", "`--log-level=warn`"],
                    ["Per-logger level", "`log_handler = werkzeug:WARNING,odoo.addons.sale:DEBUG`", "`--log-handler=odoo.addons.sale:DEBUG` (repeatable)", "via the `-c` config file"],
                    ["Log file", "`logfile = /var/log/odoo/odoo.log`", "`--logfile=…`", "`--logfile=…`"],
                    ["Syslog", "`syslog = True`", "`--syslog`", "–"],
                    ["Into the database", "`log_db = %d`, `log_db_level = warning`", "`--log-db=%d --log-db-level=warning`", "via `-c`"],
                    ["Shortcuts", "–", "`--log-sql`, `--log-web`", "–"],
                ]),
                ("h", "Allowed values"),
                ("table", [
                    ["Option", "Values"],
                    ["`log_level`", "`info` (default), `warn`, `error`, `critical`, `debug`, `debug_sql`, `debug_rpc`, `debug_rpc_answer`, `notset`, `test`, `runbot`"],
                    ["`log_handler`", "`PREFIX:LEVEL`, level = `DEBUG` · `INFO` · `WARNING` (or `WARN`) · `ERROR` · `CRITICAL`; empty prefix = root logger, e.g. `:INFO`"],
                    ["`log_db_level`", "`debug` · `info` · `warning` · `error` · `critical`"],
                    ["`log_db`", "`%d` = current database, or the name of a separate log database"],
                ]),
                ("h", "Examples"),
                ("code", "conf"),
                ("code", "cli"),
                ("p", "`click-odoo-update` (and the other `click-odoo` scripts) have their own `--log-level` and `--logfile` switches with the same values as Odoo. Per-logger settings come from the config file passed with `-c`."),
                ("code", "click"),
                ("h", "The silent mistakes"),
                ("p", "The command line rejects a wrong value immediately (`invalid choice: 'warning'`). The config file does **not** – Odoo simply keeps running on INFO, and you wonder why the logs are so full:"),
                ("code", "wrong"),
                ("note", "`log_level = warn` only sets the `odoo` and `werkzeug` loggers to WARNING. Third-party libraries keep logging at INFO via the root logger – for a really quiet log add `log_handler = :WARNING`."),
                ("h", "Check instead of guessing"),
                ("code", "check"),
            ],
        },
        "uk": {
            "title": "Логи Odoo: warn чи warning, log_level чи --log-level? Шпаргалка",
            "summary": "Конфіг, командний рядок, click-odoo-update – три написання і три види рівнів. Одна таблиця, щоб підглядати, і помилки, за яких Odoo мовчки лишається на INFO.",
            "body": [
                ("p", "Сам постійно забуваю: `warn` чи `warning`? `log_level` чи `log-level`? Відповідь залежить від того, **де** це пишеш. Усе на одній сторінці (перевірено за кодом Odoo 17)."),
                ("h", "Просте правило"),
                ("ul", [
                    "**В `odoo.conf` – підкреслення**: `log_level`, `log_handler`, `log_db_level`.",
                    "**У командному рядку – дефіс**: `--log-level`, `--log-handler`, `--log-db-level`.",
                    "`log_level` приймає **власні слова Odoo, малими**: `warn` (не `warning`!), `error`, `info`, `debug` …",
                    "`log_handler` чекає **рівні Python ВЕЛИКИМИ**: `WARNING`, `ERROR`, `DEBUG`.",
                    "`log_db_level` чекає **рівні Python малими**: `warning`, `error` (за замовчуванням `warning`).",
                ]),
                ("h", "Шпаргалка"),
                ("table", [
                    ["Що", "odoo.conf", "Командний рядок", "click-odoo-update"],
                    ["Загальний рівень", "`log_level = warn`", "`--log-level=warn`", "`--log-level=warn`"],
                    ["Рівень для логера", "`log_handler = werkzeug:WARNING,odoo.addons.sale:DEBUG`", "`--log-handler=odoo.addons.sale:DEBUG` (можна кілька разів)", "через конфіг `-c`"],
                    ["Файл логу", "`logfile = /var/log/odoo/odoo.log`", "`--logfile=…`", "`--logfile=…`"],
                    ["Syslog", "`syslog = True`", "`--syslog`", "–"],
                    ["У базу даних", "`log_db = %d`, `log_db_level = warning`", "`--log-db=%d --log-db-level=warning`", "через `-c`"],
                    ["Скорочення", "–", "`--log-sql`, `--log-web`", "–"],
                ]),
                ("h", "Допустимі значення"),
                ("table", [
                    ["Параметр", "Значення"],
                    ["`log_level`", "`info` (за замовчуванням), `warn`, `error`, `critical`, `debug`, `debug_sql`, `debug_rpc`, `debug_rpc_answer`, `notset`, `test`, `runbot`"],
                    ["`log_handler`", "`PREFIX:РІВЕНЬ`, рівень = `DEBUG` · `INFO` · `WARNING` (або `WARN`) · `ERROR` · `CRITICAL`; порожній префікс = кореневий логер, напр. `:INFO`"],
                    ["`log_db_level`", "`debug` · `info` · `warning` · `error` · `critical`"],
                    ["`log_db`", "`%d` = поточна база або назва окремої бази для логів"],
                ]),
                ("h", "Приклади"),
                ("code", "conf"),
                ("code", "cli"),
                ("p", "`click-odoo-update` (та інші скрипти `click-odoo`) мають власні ключі `--log-level` і `--logfile` з тими самими значеннями, що й Odoo. Налаштування окремих логерів беруться з конфігу, переданого через `-c`."),
                ("code", "click"),
                ("h", "Тихі помилки"),
                ("p", "Командний рядок одразу лається на неправильне значення (`invalid choice: 'warning'`). Конфіг – **ні**: Odoo просто працює далі на INFO, а ти дивуєшся, чому лог такий великий:"),
                ("code", "wrong"),
                ("note", "`log_level = warn` ставить WARNING лише логерам `odoo` і `werkzeug`. Сторонні бібліотеки й далі пишуть INFO через кореневий логер. Для зовсім тихого логу додайте `log_handler = :WARNING`."),
                ("h", "Перевіряти, а не вгадувати"),
                ("code", "check"),
            ],
        },
        "ru": {
            "title": "Логи Odoo: warn или warning, log_level или --log-level? Шпаргалка",
            "summary": "Конфиг, командная строка, click-odoo-update – три написания и три вида уровней. Одна таблица, чтобы подглядывать, и ошибки, при которых Odoo молча остаётся на INFO.",
            "body": [
                ("p", "Сам постоянно забываю: `warn` или `warning`? `log_level` или `log-level`? Ответ зависит от того, **где** это пишешь. Всё на одной странице (проверено по коду Odoo 17)."),
                ("h", "Простое правило"),
                ("ul", [
                    "**В `odoo.conf` – подчёркивание**: `log_level`, `log_handler`, `log_db_level`.",
                    "**В командной строке – дефис**: `--log-level`, `--log-handler`, `--log-db-level`.",
                    "`log_level` принимает **собственные слова Odoo, строчными**: `warn` (не `warning`!), `error`, `info`, `debug` …",
                    "`log_handler` ждёт **уровни Python ЗАГЛАВНЫМИ**: `WARNING`, `ERROR`, `DEBUG`.",
                    "`log_db_level` ждёт **уровни Python строчными**: `warning`, `error` (по умолчанию `warning`).",
                ]),
                ("h", "Шпаргалка"),
                ("table", [
                    ["Что", "odoo.conf", "Командная строка", "click-odoo-update"],
                    ["Общий уровень", "`log_level = warn`", "`--log-level=warn`", "`--log-level=warn`"],
                    ["Уровень для логгера", "`log_handler = werkzeug:WARNING,odoo.addons.sale:DEBUG`", "`--log-handler=odoo.addons.sale:DEBUG` (можно несколько раз)", "через конфиг `-c`"],
                    ["Файл лога", "`logfile = /var/log/odoo/odoo.log`", "`--logfile=…`", "`--logfile=…`"],
                    ["Syslog", "`syslog = True`", "`--syslog`", "–"],
                    ["В базу данных", "`log_db = %d`, `log_db_level = warning`", "`--log-db=%d --log-db-level=warning`", "через `-c`"],
                    ["Сокращения", "–", "`--log-sql`, `--log-web`", "–"],
                ]),
                ("h", "Допустимые значения"),
                ("table", [
                    ["Параметр", "Значения"],
                    ["`log_level`", "`info` (по умолчанию), `warn`, `error`, `critical`, `debug`, `debug_sql`, `debug_rpc`, `debug_rpc_answer`, `notset`, `test`, `runbot`"],
                    ["`log_handler`", "`PREFIX:УРОВЕНЬ`, уровень = `DEBUG` · `INFO` · `WARNING` (или `WARN`) · `ERROR` · `CRITICAL`; пустой префикс = корневой логгер, напр. `:INFO`"],
                    ["`log_db_level`", "`debug` · `info` · `warning` · `error` · `critical`"],
                    ["`log_db`", "`%d` = текущая база или имя отдельной базы для логов"],
                ]),
                ("h", "Примеры"),
                ("code", "conf"),
                ("code", "cli"),
                ("p", "`click-odoo-update` (и другие скрипты `click-odoo`) имеют собственные ключи `--log-level` и `--logfile` с теми же значениями, что и Odoo. Настройки отдельных логгеров берутся из конфига, переданного через `-c`."),
                ("code", "click"),
                ("h", "Тихие ошибки"),
                ("p", "Командная строка сразу ругается на неправильное значение (`invalid choice: 'warning'`). Конфиг – **нет**: Odoo просто работает дальше на INFO, а ты удивляешься, почему лог такой большой:"),
                ("code", "wrong"),
                ("note", "`log_level = warn` ставит WARNING только логгерам `odoo` и `werkzeug`. Сторонние библиотеки продолжают писать INFO через корневой логгер. Для совсем тихого лога добавьте `log_handler = :WARNING`."),
                ("h", "Проверять, а не угадывать"),
                ("code", "check"),
            ],
        },
    },
})

# Надписи раздела по языкам
UI = {
    "de": {"prev": 'Vorheriger Artikel', "next": 'Nächster Artikel', "title": "Blog & How-tos", "intro": "Fälle aus der Praxis und Anleitungen rund um Odoo, Docker und PostgreSQL – so, wie ich sie selbst umsetze.",
           "read": "Weiterlesen", "back": "← Alle Artikel", "fallback": "", "min": "Min. Lesezeit",
           "cta_title": "Soll ich das für Sie übernehmen?", "cta_text": "Ich setze das in Ihrem System um – zuerst auf einer Testkopie, mit Rücksprung und Protokoll."},
    "en": {"prev": 'Previous article', "next": 'Next article', "title": "Blog & how-tos", "intro": "Real cases and step-by-step guides on Odoo, Docker and PostgreSQL – the way I do it myself.",
           "read": "Read more", "back": "← All articles", "fallback": "", "min": "min read",
           "cta_title": "Want me to do this for you?", "cta_text": "I'll implement it in your system – on a test copy first, with rollback and a written record."},
    "fr": {"prev": 'Article précédent', "next": 'Article suivant', "title": "Blog & guides", "intro": "Cas réels et guides pas à pas sur Odoo, Docker et PostgreSQL – tels que je les applique moi-même.",
           "read": "Lire la suite", "back": "← Tous les articles", "fallback": "Cet article n’est pas encore disponible en français – voici la version anglaise.", "min": "min de lecture",
           "cta_title": "Je m’en occupe pour vous ?", "cta_text": "Je le mets en place dans votre système – d’abord sur une copie de test, avec retour arrière et compte rendu."},
    "el": {"prev": 'Προηγούμενο άρθρο', "next": 'Επόμενο άρθρο', "title": "Blog & οδηγοί", "intro": "Πραγματικές περιπτώσεις και οδηγοί βήμα-βήμα για Odoo, Docker και PostgreSQL – όπως τα εφαρμόζω ο ίδιος.",
           "read": "Περισσότερα", "back": "← Όλα τα άρθρα", "fallback": "Το άρθρο δεν είναι ακόμη διαθέσιμο στα ελληνικά – ακολουθεί η αγγλική έκδοση.", "min": "λεπτά ανάγνωσης",
           "cta_title": "Να το αναλάβω εγώ;", "cta_text": "Το υλοποιώ στο σύστημά σας – πρώτα σε αντίγραφο δοκιμών, με δυνατότητα επαναφοράς και αναφορά."},
    "uk": {"prev": 'Попередня стаття', "next": 'Наступна стаття', "title": "Блог і how-to", "intro": "Реальні випадки й покрокові інструкції з Odoo, Docker і PostgreSQL – так, як я роблю це сам.",
           "read": "Читати далі", "back": "← Усі статті", "fallback": "", "min": "хв читання",
           "cta_title": "Зробити це для вас?", "cta_text": "Я впроваджу це у вашій системі – спершу на тестовій копії, з можливістю відкату й протоколом."},
    "ru": {"prev": 'Предыдущая статья', "next": 'Следующая статья', "title": "Блог и how-to", "intro": "Реальные случаи и пошаговые инструкции по Odoo, Docker и PostgreSQL – так, как я делаю это сам.",
           "read": "Читать дальше", "back": "← Все статьи", "fallback": "", "min": "мин чтения",
           "cta_title": "Сделать это для вас?", "cta_text": "Я внедрю это в вашей системе – сначала на тестовой копии, с возможностью отката и протоколом."},
}

# статьи 5–6 вынесены в blog_posts_more.py
from blog_posts_more import COMPOSE as _C1, CERTBOT as _C2  # noqa: E402
POSTS += [_C1, _C2]
from blog_post_ssl import SSL as _C3  # noqa: E402  (все 6 языков внутри)
POSTS.append(_C3)
from blog_post_sec import AUTH as _C4, PWD as _C5  # noqa: E402
POSTS += [_C4, _C5]
from blog_post_access import ACCESS as _C6  # noqa: E402
POSTS.append(_C6)
from blog_post_free import FREE as _C7  # noqa: E402  (все 6 языков внутри)
POSTS.append(_C7)

# переводы, вынесенные в отдельные файлы (blog_posts_<lang>.py)
from blog_posts_fr import FR as _FR  # noqa: E402
for _p in POSTS:
    if _p["slug"] in _FR:
        _p["t"]["fr"] = _FR[_p["slug"]]
from blog_posts_el import EL as _EL  # noqa: E402
for _p in POSTS:
    if _p["slug"] in _EL:
        _p["t"]["el"] = _EL[_p["slug"]]


def ACCESS_TITLE(lang):
    """Заголовок статьи о Cloudflare Access на нужном языке (для ссылки со страницы /test2/)."""
    p = next(x for x in POSTS if x["slug"] == "cloudflare-access-zero-trust-step-by-step")
    return p["t"].get(lang, p["t"]["en"])["title"]
from blog_post_replica import REPLICA as _C8  # noqa: E402
POSTS.append(_C8)
from blog_post_serialize import SERIALIZE as _C9  # noqa: E402
POSTS.append(_C9)
from blog_post_restore import RESTORE as _C10  # noqa: E402
POSTS.append(_C10)
from blog_post_pgload import PGLOAD as _C11  # noqa: E402
POSTS.append(_C11)
from blog_post_pgcheat import PGCHEAT as _C12  # noqa: E402
POSTS.append(_C12)
from blog_post_pgbouncer import PGBOUNCER as _C13  # noqa: E402
POSTS.append(_C13)
from blog_post_scaling import SCALING as _C14  # noqa: E402
POSTS.append(_C14)
from blog_post_security import SECURITY as _C15  # noqa: E402
POSTS.append(_C15)
from blog_post_grafana import GRAFANA as _C16, AUDIT as _C17  # noqa: E402  (все 6 языков внутри)
POSTS += [_C16, _C17]
from blog_post_powa import POWA as _C18  # noqa: E402  (все 6 языков внутри)
POSTS.append(_C18)
from blog_post_problems import PROBLEMS as _C19  # noqa: E402  (все 6 языков внутри)
POSTS.append(_C19)
from blog_post_longrun import LONGRUN as _C20  # noqa: E402  (все 6 языков внутри)
POSTS.append(_C20)
from blog_post_tgbot import TGBOT as _C21  # noqa: E402  (все 6 языков внутри)
POSTS.append(_C21)
from blog_post_freessl import FREESSL as _C22  # noqa: E402  (все 6 языков внутри)
POSTS.append(_C22)
from blog_post_listdb import LISTDB as _C23  # noqa: E402  (все 6 языков внутри)
POSTS.append(_C23)
from blog_post_vpsbench import VPSBENCH as _C24  # noqa: E402  (все 6 языков внутри)
POSTS.append(_C24)
from blog_post_crmsearch import CRMSEARCH as _C25  # noqa: E402  (все 6 языков внутри)
POSTS.append(_C25)
from blog_post_datev import DATEV as _C26  # noqa: E402  (en, de, ru, uk; fr/el – английская версия)
POSTS.append(_C26)
from blog_post_costs import COSTS as _C27  # noqa: E402  (en, de, ru, uk; fr/el – английская версия)
POSTS.append(_C27)
from blog_post_mailint import MAILINT as _C28  # noqa: E402  (en, de, ru, uk; fr/el – английская версия)
POSTS.append(_C28)
from blog_post_mailpw import MAILPW as _C29  # noqa: E402  (en, de, ru, uk; fr/el – английская версия)
POSTS.append(_C29)
from blog_post_odoosap import ODOOSAP as _C30  # noqa: E402  (en, de, ru, uk; fr/el – английская версия)
POSTS.append(_C30)
