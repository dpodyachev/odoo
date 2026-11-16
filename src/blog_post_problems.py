# Статья 23: главные проблемы Odoo (обновления, производительность, маркетплейс, кастомизация, бухучёт, интеграции,
# права/автоматизации, скрытые затраты) + лайфхаки администратора/DevOps (cron-инстанс, SIGHUP, queue_job, бэкапы,
# обезвреживание stage, PgBouncer, click-odoo-update, профилирование, сброс assets). По тексту владельца, проверено и дополнено.

PROBLEMS = {
    "slug": "odoo-main-problems-limitations-devops-tips",
    "date": "2026-11-16",
    "tags": ["Odoo", "Upgrade", "Performance", "DevOps", "Security", "Best practices"],
    "code": {
        "cron": ("docker-compose.yml · separate instance only for cron jobs", """services:
  odoo-web:                     # users: HTTP workers, no cron
    image: my-odoo:17
    command: ["odoo", "-c", "/etc/odoo/odoo.conf", "--workers=8", "--max-cron-threads=0"]
  odoo-cron:                    # same code, same database, no HTTP
    image: my-odoo:17
    command: ["odoo", "-c", "/etc/odoo/odoo.conf", "--workers=0", "--max-cron-threads=2", "--no-http"]
    mem_limit: 6g               # a runaway cron cannot eat the web server's RAM (container is restarted instead)
    restart: unless-stopped"""),
        "hup": ("bash · restart Odoo without killing running requests", """# prefork mode: SIGHUP = graceful stop of the workers (current requests finish) + re-exec of odoo with the same arguments
kill -HUP $(pgrep -f 'odoo-bin.*-c /etc/odoo/odoo.conf' | head -1)     # the master process
docker kill --signal=HUP odoo                                          # in Docker: works if odoo runs as PID 1 (exec in the entrypoint)
# code and odoo.conf are re-read; sessions survive (they are stored on disk), open websockets reconnect"""),
        "backup": ("bash · backup without the database manager", """DB=mydb; D=/backup/$(date +%F)
mkdir -p $D
pg_dump -Fc -Z6 -d $DB -f $D/$DB.dump                       # custom format: parallel restore, single tables
rsync -a --delete /var/lib/odoo/filestore/$DB/ /backup/filestore/$DB/    # incremental; or a ZFS/LVM/cloud snapshot
pg_restore -l $D/$DB.dump > /dev/null && echo "dump readable"            # minimal check – a real restore test belongs on stage"""),
        "neutralize": ("bash · a copy of production must not send anything", """# Odoo 16+: built-in neutralization (crons off, mail servers off, payment providers in test mode, banner "neutralized")
odoo-bin neutralize -c /etc/odoo/odoo.conf -d mydb_stage

# additionally / for Odoo ≤ 15 – in SQL:
UPDATE ir_cron SET active = false;
UPDATE ir_mail_server SET active = false;
UPDATE fetchmail_server SET active = false;
UPDATE ir_config_parameter SET value = 'https://stage.example.com' WHERE key = 'web.base.url';
# and in odoo.conf of stage: no real SMTP (smtp_server = localhost + a mail catcher like Mailpit)"""),
        "assets": ("SQL / odoo shell · white screen without styles: rebuild the asset bundles", """-- 1) cause first: does the file exist? (Odoo log: "Could not get content for /web/assets/..." or FileNotFoundError)
SELECT id, name, url, store_fname FROM ir_attachment WHERE url LIKE '/web/assets/%' ORDER BY id DESC LIMIT 5;
-- 2) delete the generated bundles – Odoo builds them again on the next page load
DELETE FROM ir_attachment WHERE url LIKE '/web/assets/%';

# the same via the ORM (also removes the files from the filestore):
odoo-bin shell -c /etc/odoo/odoo.conf -d mydb <<'EOF'
env['ir.attachment'].search([('url', '=like', '/web/assets/%')]).unlink()
env.cr.commit()
EOF
# then hard-reload the browser (Ctrl+Shift+R); with several Odoo servers – a shared filestore is mandatory"""),
        "prof": ("slow requests: where the time goes", """# PostgreSQL: log every query slower than 1 s (postgresql.conf, reload is enough)
log_min_duration_statement = 1000
# history per query: pg_stat_statements / PoWA (see the PoWA article)

# Odoo: the request line in the log ends with three numbers – SQL queries, SQL time, remaining (Python) time:
# ... "POST /web/dataset/call_kw/sale.order/web_search_read HTTP/1.1" 200 - 1250 0.812 3.104
#                                                        queries ^  SQL s ^  other s ^

# a hanging worker: Python stack without restart (py-spy on the host; in Docker run it as root on the host with the host PID)
py-spy dump --pid 12345
py-spy top  --pid 12345"""),
    },
    "links": [
        ("Blog: updating modules with click-odoo-update", "@blog:odoo-module-update-click-odoo-update"),
        ("Blog: copy production to stage – stop crons, mail and integrations first", "@blog:odoo-stage-restore-stop-cron-jobs"),
        ("Blog: how many users can one Odoo server handle?", "@blog:odoo-how-many-users-one-server-workers"),
        ("Blog: could not serialize access – concurrent updates in Odoo", "@blog:odoo-could-not-serialize-access-concurrent-update"),
        ("Blog: PgBouncer for Odoo", "@blog:pgbouncer-odoo-connection-pooling"),
        ("Blog: PoWA – query history and index advice", "@blog:powa-postgresql-workload-analyzer-odoo-docker"),
        ("Blog: PostgreSQL restore fails – foreign keys, duplicates", "@blog:postgresql-restore-fails-foreign-key-duplicate-index-odoo"),
        ("Blog: Odoo server security", "@blog:odoo-server-security-logs-secrets-ports-encryption"),
        ("Blog: Odoo logging options", "@blog:odoo-logging-options-cheatsheet"),
        ("OpenUpgrade (OCA) – migration of Community databases", "https://github.com/OCA/OpenUpgrade"),
        ("click-odoo-contrib (ACSONE)", "https://github.com/acsone/click-odoo-contrib"),
        ("queue_job (OCA)", "https://github.com/OCA/queue/tree/17.0/queue_job"),
        ("py-spy", "https://github.com/benfred/py-spy"),
        ("PostgreSQL/Odoo config calculator (this site)", "@page:pg-odoo-calculator.html"),
    ],
    "t": {},
}

_TBL = {
    "en": [["Problem", "What really helps"],
           ["Major upgrade breaks custom modules", "few customisations, upgrade every 1–2 versions, test migration on a copy, budget it"],
           ["Slow with large data", "indexes, fix N+1 code, archive old data, separate cron instance, enough workers and RAM"],
           ["Third-party modules", "OCA or known authors, code review, tests, install on stage first"],
           ["Over-customisation", "standard process first, change code only where it creates value"],
           ["Local accounting / reporting", "check the localisation (country, Community vs Enterprise) before the project"],
           ["Integrations and data migration", "clean master data first, external IDs, queue_job, retries"],
           ["Access rights, automations", "groups instead of individual rights, record rules tested with real users, no automation loops"],
           ["Stage sends real mail", "neutralize every copy of production"]],
    "de": [["Problem", "Was wirklich hilft"],
           ["Major-Upgrade bricht eigene Module", "wenig Anpassungen, alle 1–2 Versionen upgraden, Migration an einer Kopie testen, einplanen"],
           ["Langsam bei großen Datenmengen", "Indizes, N+1-Code beheben, Altdaten archivieren, eigene Cron-Instanz, genug Worker und RAM"],
           ["Module von Drittanbietern", "OCA oder bekannte Autoren, Code-Review, Tests, zuerst auf Stage installieren"],
           ["Überanpassung", "zuerst Standardprozess, Code nur dort ändern, wo er Wert schafft"],
           ["Lokale Buchhaltung / Meldewesen", "Lokalisierung (Land, Community vs. Enterprise) vor dem Projekt prüfen"],
           ["Schnittstellen und Datenübernahme", "Stammdaten zuerst bereinigen, externe IDs, queue_job, Wiederholungen"],
           ["Zugriffsrechte, Automatisierungen", "Gruppen statt Einzelrechte, Datensatzregeln mit echten Benutzern testen, keine Automatisierungsschleifen"],
           ["Stage verschickt echte E-Mails", "jede Kopie der Produktion neutralisieren"]],
    "fr": [["Problème", "Ce qui aide vraiment"],
           ["Une montée de version majeure casse les modules spécifiques", "peu de personnalisations, migrer toutes les 1–2 versions, tester sur une copie, la budgéter"],
           ["Lenteur avec de gros volumes", "index, corriger le code N+1, archiver les anciennes données, instance cron séparée, assez de workers et de RAM"],
           ["Modules tiers", "OCA ou auteurs connus, revue de code, tests, installation d'abord sur stage"],
           ["Sur-personnalisation", "d'abord le processus standard, ne changer le code que là où il crée de la valeur"],
           ["Comptabilité et déclarations locales", "vérifier la localisation (pays, Community vs Enterprise) avant le projet"],
           ["Intégrations et reprise de données", "nettoyer d'abord les données de base, ID externes, queue_job, nouvelles tentatives"],
           ["Droits d'accès, automatisations", "des groupes plutôt que des droits individuels, règles d'enregistrement testées avec de vrais utilisateurs, pas de boucles d'automatisation"],
           ["Le stage envoie de vrais e-mails", "neutraliser chaque copie de la production"]],
    "el": [["Πρόβλημα", "Τι βοηθά πραγματικά"],
           ["Η μεγάλη αναβάθμιση σπάει τα δικά σας modules", "λίγες προσαρμογές, αναβάθμιση κάθε 1–2 εκδόσεις, δοκιμή μετάβασης σε αντίγραφο, προϋπολογισμός"],
           ["Αργό με μεγάλο όγκο δεδομένων", "ευρετήρια, διόρθωση κώδικα N+1, αρχειοθέτηση παλιών δεδομένων, ξεχωριστό instance για cron, αρκετοί workers και RAM"],
           ["Modules τρίτων", "OCA ή γνωστοί δημιουργοί, έλεγχος κώδικα, tests, πρώτα εγκατάσταση σε stage"],
           ["Υπερβολική προσαρμογή", "πρώτα η τυπική διαδικασία, αλλαγή κώδικα μόνο όπου δημιουργεί αξία"],
           ["Τοπική λογιστική / αναφορές", "έλεγχος της τοπικοποίησης (χώρα, Community vs Enterprise) πριν από το έργο"],
           ["Διασυνδέσεις και μεταφορά δεδομένων", "πρώτα καθαρισμός βασικών δεδομένων, εξωτερικά IDs, queue_job, επαναλήψεις"],
           ["Δικαιώματα, αυτοματισμοί", "ομάδες αντί για ατομικά δικαιώματα, κανόνες εγγραφών ελεγμένοι με πραγματικούς χρήστες, χωρίς βρόχους αυτοματισμών"],
           ["Το stage στέλνει πραγματικά e-mail", "εξουδετέρωση κάθε αντιγράφου της παραγωγής"]],
    "uk": [["Проблема", "Що реально допомагає"],
           ["Мажорне оновлення ламає власні модулі", "мінімум доробок, оновлення кожні 1–2 версії, тест міграції на копії, окремий бюджет"],
           ["Повільно на великих обсягах", "індекси, виправлення N+1 у коді, архівування старих даних, окремий інстанс для cron, достатньо воркерів і RAM"],
           ["Сторонні модулі", "OCA або відомі автори, рев'ю коду, тести, установка спершу на stage"],
           ["Надмірна кастомізація", "спершу стандартний процес, код змінювати лише там, де це дає цінність"],
           ["Локальний облік і звітність", "перевірити локалізацію (країна, Community чи Enterprise) до старту проєкту"],
           ["Інтеграції та перенесення даних", "спершу очистити довідники, зовнішні ID, queue_job, повтори"],
           ["Права доступу, автоматизації", "групи замість індивідуальних прав, record rules перевіряти на реальних користувачах, без циклів автоматизацій"],
           ["Stage розсилає справжню пошту", "знешкоджувати кожну копію продакшену"]],
    "ru": [["Проблема", "Что реально помогает"],
           ["Мажорное обновление ломает свои модули", "минимум доработок, обновление каждые 1–2 версии, тест миграции на копии, отдельный бюджет"],
           ["Медленно на больших объёмах", "индексы, исправление N+1 в коде, архивирование старых данных, отдельный инстанс для cron, достаточно воркеров и RAM"],
           ["Сторонние модули", "OCA или известные авторы, ревью кода, тесты, установка сначала на stage"],
           ["Избыточная кастомизация", "сначала стандартный процесс, код менять только там, где это даёт ценность"],
           ["Локальный учёт и отчётность", "проверить локализацию (страна, Community или Enterprise) до старта проекта"],
           ["Интеграции и перенос данных", "сначала очистить справочники, внешние ID, queue_job, повторы"],
           ["Права доступа, автоматизации", "группы вместо индивидуальных прав, record rules проверять на реальных пользователях, без циклов автоматизаций"],
           ["Stage рассылает настоящую почту", "обезвреживать каждую копию продакшена"]],
}


def _b(lang, title, summary, intro, note, h, tech, impl, cost, tips_proc, tips_db, tips_dev, assets_p, closing, links):
    return {"title": title, "summary": summary, "body": [
        ("p", intro), ("note", note),
        ("h", h[0]), ("ul", tech),
        ("h", h[1]), ("ul", impl),
        ("h", h[2]), ("ul", cost),
        ("h", h[3]), ("table", _TBL[lang]),
        ("h", h[4]), ("ul", tips_proc), ("code", "cron"), ("code", "hup"),
        ("h", h[5]), ("ul", tips_db), ("code", "backup"), ("code", "neutralize"),
        ("h", h[6]), ("ul", tips_dev), ("code", "prof"),
        ("h", h[7]), ("p", assets_p[0]), ("ul", assets_p[1]), ("code", "assets"),
        ("h", h[8]), ("p", closing),
        ("links", links)]}


# ================================================================ EN
PROBLEMS["t"]["en"] = _b("en",
    "The main problems of Odoo – and how administrators and DevOps avoid them",
    "Where Odoo really hurts: major upgrades, performance with large data, third-party modules, over-customisation, local accounting, integrations, access rights and automations, hidden costs. Plus proven admin and DevOps practices: a separate cron instance, graceful restart, queue_job, backups without the database manager, neutralised stage copies, PgBouncer, click-odoo-update, profiling and rebuilding broken assets.",
    "Odoo's weak points are rarely crashes of the core. They appear with growth: the yearly major version, millions of records, hundreds of users, modules from the app store and code written “quickly” for the go-live. This is a list from practice – what goes wrong and what we do about it on the servers we run.",
    "Short version: keep customisation small and in modules, plan upgrades as projects, check third-party code, measure before tuning, separate cron jobs from the web workers, back up with pg_dump + filestore sync, neutralise every copy of production – and know how to rebuild assets.",
    ["Technical and architectural limits", "Implementation and operation", "Hidden costs", "Overview", "Admin tips: processes and load", "Database, backups, stage", "Deploy, debugging, monitoring", "Broken assets – a classic", "Conclusion"],
    ["**Major upgrades.** A new version every year; between versions models, fields, JavaScript (OWL) and views change. Custom modules break on renamed fields and XPath expressions that no longer match. Odoo's upgrade service (Enterprise) migrates only standard modules; Community databases go through OpenUpgrade (OCA). Every custom module needs its own migration and a test on a copy – that is a project with a budget, not a button.",
     "**Performance with large data.** The monolith itself is rarely the limit; typical causes are custom code with N+1 queries (`read()`/`search()` in a loop), stored computed fields recomputed over millions of records, missing indexes on fields used in domains, a `mail_message`/`mail_tracking_value` growing to hundreds of GB, and long cron jobs whose workers keep gigabytes of RAM. Without measuring (PostgreSQL statistics, request times in the log) tuning is guessing.",
     "**Third-party modules.** The Odoo Apps store checks little more than that a module installs – there is no quality certification. Conflicting overrides of the same method, missing access rules, `sudo()` and raw SQL with string formatting are common. OCA modules go through review and CI, but also need testing in your combination.",
     "**Offline work.** The Point of Sale works offline and synchronises later; almost everything else (backend, mobile app – essentially the web client) needs a connection.",
     "**Community vs. Enterprise.** Some functions exist only in Enterprise (e.g. full accounting reports, studio, some localisations, the mobile app features); filling the gap with third-party modules increases the upgrade risk."],
    ["**The over-customisation trap.** Because everything can be changed, companies rebuild their old processes in code instead of adopting standard flows. Every change is paid again at each upgrade. Rule of thumb: configuration before Studio, Studio before code, code only where it creates real value – and always in modules under version control, never in the database only.",
     "**Local accounting depth.** The quality of localisations differs by country and edition. In Germany, for example, check DATEV export, GoBD-compliant processes and VAT returns before the project; in other countries the local statutory reporting can be weaker than in specialised local software.",
     "**Integrations and data migration.** Importing master data without cleaning creates duplicates and wrong stock. Use external IDs for repeatable imports, migrate in test runs, reconcile totals. Integrations with marketplaces, payment providers and telephony need retries, idempotency and monitoring – not a blocking HTTP request.",
     "**Access rights and automations.** Wrong groups and record rules are both a security and a support problem; test them with real user accounts, not as admin. Automated actions on “on save” can trigger each other or the same record again and loop; server actions with Python code run with elevated rights. Both belong in reviews.",
     "**Copies of production.** A stage or test database restored from production with active crons sends real invoices, reminders and integration calls. Neutralisation is part of every restore."],
    ["**Dependence on the integrator.** Licences are cheap compared with the implementation and maintenance; good Odoo knowledge is scarce. Clarify who maintains custom modules, who does upgrades and who watches the servers.",
     "**Operations are not free.** Self-hosting means backups and restore tests, monitoring, updates of OS, PostgreSQL and Odoo, security. Odoo Online (SaaS) removes this work but does not allow custom Python modules; Odoo.sh is in between.",
     "**Staff resistance.** Without role-based training employees do not understand the document chains, go back to Excel and create errors that later look like software problems."],
    ["**A separate instance for cron jobs.** Run a second Odoo process (container or service) on the same code and database with `--workers=0 --max-cron-threads=2 --no-http`, and set `max_cron_threads = 0` on the web server. Heavy nightly recomputations and imports no longer take web workers, and a memory limit on the cron container protects the users' workers – in a real case eight cron processes held 3.5–3.8 GB each on the web server.",
     "**Graceful restart instead of kill.** `SIGHUP` lets the running requests finish and restarts Odoo with the same arguments, re-reading code and `odoo.conf`. Sessions survive; websockets reconnect.",
     "**queue_job (OCA) for heavy work.** Integrations, mass e-mails, synchronisations go into an asynchronous queue with retries and channels that limit parallelism, instead of blocking an HTTP worker until the time limit kills it. The job runner needs its own database connection (and a session pool with PgBouncer)."],
    ["**Backups with pg_dump and rsync, not via the database manager.** The manager builds a ZIP of database and filestore in a Python worker – with databases of several GB it hits memory and time limits and blocks a worker. `pg_dump -Fc` plus an incremental filestore sync (or snapshots) is faster and restorable table by table. Disable the manager (`list_db = False`).",
     "**Neutralise every copy of production.** Odoo 16+ has `odoo-bin neutralize` (crons and mail servers off, payment providers in test mode). `dbfilter` alone does not stop anything from being sent – it only selects the database. In addition, give stage an SMTP that cannot deliver (a mail catcher) and set its own `web.base.url`.",
     "**PgBouncer in transaction mode** when there are many workers or several Odoo servers: hundreds of client connections share a few dozen PostgreSQL connections. Two exceptions need session mode: the Odoo bus (`LISTEN imbus`) and the queue_job runner."],
    ["**click-odoo-update for deployments.** It stores checksums of the module files in the database and runs `-u` only for modules whose code changed – deployments take seconds instead of minutes, and nobody forgets a module.",
     "**Measure, then tune.** For slow queries use PostgreSQL itself: `log_min_duration_statement`, `pg_stat_statements` or PoWA. `log_level = debug_sql` logs every query and floods the log – only for a few seconds on stage; `log_db_level` writes log lines into the table `ir_logging` and is not a profiling tool. Odoo also writes the number of queries, SQL time and the remaining time of every request at the end of its request log line.",
     "**py-spy for a hanging worker.** `py-spy dump --pid <PID>` shows the Python stack of a running process without restarting it. In Docker run py-spy on the host as root with the host PID (or give the container `SYS_PTRACE`)."],
    ["After a deployment the backend is white or without styles, the browser console shows 404/500 for `/web/assets/...`, the Odoo log says “Could not get content for /web/assets/…” or `FileNotFoundError`. The bundles are attachments: the record is in the database, the file in the filestore. We have seen this many times; the causes are almost always the same:",
     ["the filestore is missing or not persistent – a Docker volume not mounted, `data_dir` changed, a database restored without its filestore;",
      "several Odoo servers without a shared filestore – server A generated the bundle, server B cannot find the file;",
      "a module update interrupted while compiling assets, or a broken SCSS/JS file in a custom module (then the log shows the compile error – fix the code first);",
      "an old bundle cached by a CDN/proxy after the update."]],
    "Most Odoo problems are predictable – and therefore preventable: little and clean custom code, upgrades planned, third-party modules checked, the database measured, background work separated from users, backups that are actually restored on stage. We set this up and maintain it for companies in Germany, Austria and Switzerland.",
    "Links")

# ================================================================ DE
PROBLEMS["t"]["de"] = _b("de",
    "Die größten Probleme von Odoo – und wie Administratoren und DevOps sie vermeiden",
    "Wo Odoo wirklich wehtut: Major-Upgrades, Performance bei großen Datenmengen, Drittanbieter-Module, Überanpassung, lokale Buchhaltung, Schnittstellen, Rechte und Automatisierungen, versteckte Kosten. Dazu bewährte Praxis für Admins und DevOps: eigene Cron-Instanz, sanfter Neustart, queue_job, Backups ohne Datenbankmanager, neutralisierte Stage-Kopien, PgBouncer, click-odoo-update, Profiling und das Neuerzeugen kaputter Assets.",
    "Die Schwächen von Odoo sind selten Abstürze des Kerns. Sie zeigen sich mit dem Wachstum: die jährliche Hauptversion, Millionen Datensätze, Hunderte Benutzer, Module aus dem App Store und Code, der „schnell“ für den Go-live geschrieben wurde. Eine Liste aus der Praxis – was schiefgeht und was wir auf den Servern, die wir betreuen, dagegen tun.",
    "Kurzfassung: Anpassungen klein halten und in Modulen, Upgrades als Projekte planen, Fremdcode prüfen, erst messen, dann tunen, Cron-Jobs von den Web-Workern trennen, mit pg_dump + Filestore-Sync sichern, jede Kopie der Produktion neutralisieren – und wissen, wie man Assets neu erzeugt.",
    ["Technische und architektonische Grenzen", "Einführung und Betrieb", "Versteckte Kosten", "Überblick", "Admin-Tipps: Prozesse und Last", "Datenbank, Backups, Stage", "Deployment, Debugging, Monitoring", "Kaputte Assets – ein Klassiker", "Fazit"],
    ["**Major-Upgrades.** Jedes Jahr eine neue Version; zwischen den Versionen ändern sich Modelle, Felder, JavaScript (OWL) und Ansichten. Eigene Module brechen an umbenannten Feldern und XPath-Ausdrücken, die nicht mehr passen. Der Upgrade-Service von Odoo (Enterprise) migriert nur Standardmodule; Community-Datenbanken laufen über OpenUpgrade (OCA). Jedes eigene Modul braucht seine eigene Migration und einen Test an einer Kopie – ein Projekt mit Budget, kein Knopfdruck.",
     "**Performance bei großen Datenmengen.** Der Monolith selbst ist selten die Grenze; typische Ursachen sind eigener Code mit N+1-Abfragen (`read()`/`search()` in Schleifen), gespeicherte berechnete Felder, die über Millionen Datensätze neu berechnet werden, fehlende Indizes auf Feldern in Domains, `mail_message`/`mail_tracking_value` mit Hunderten GB und lange Cron-Jobs, deren Worker Gigabytes RAM halten. Ohne Messung (PostgreSQL-Statistiken, Anfragezeiten im Log) ist Tuning Raten.",
     "**Module von Drittanbietern.** Der Odoo App Store prüft kaum mehr, als dass ein Modul installierbar ist – eine Qualitätszertifizierung gibt es nicht. Konkurrierende Überschreibungen derselben Methode, fehlende Zugriffsregeln, `sudo()` und rohes SQL mit String-Formatierung sind häufig. OCA-Module gehen durch Review und CI, müssen aber in Ihrer Kombination ebenfalls getestet werden.",
     "**Offline-Arbeit.** Die Kasse (Point of Sale) arbeitet offline und synchronisiert später; fast alles andere (Backend, mobile App – im Kern der Web-Client) braucht eine Verbindung.",
     "**Community vs. Enterprise.** Manche Funktionen gibt es nur in Enterprise (z. B. vollständige Buchhaltungsberichte, Studio, einige Lokalisierungen, Funktionen der mobilen App); die Lücke mit Drittmodulen zu füllen erhöht das Upgrade-Risiko."],
    ["**Die Falle der Überanpassung.** Weil sich alles ändern lässt, bauen Unternehmen ihre alten Prozesse im Code nach, statt Standardabläufe zu übernehmen. Jede Änderung wird bei jedem Upgrade erneut bezahlt. Faustregel: Konfiguration vor Studio, Studio vor Code, Code nur dort, wo er echten Wert schafft – und immer in Modulen unter Versionskontrolle, nie nur in der Datenbank.",
     "**Tiefe der lokalen Buchhaltung.** Die Qualität der Lokalisierungen hängt von Land und Edition ab. In Deutschland z. B. DATEV-Export, GoBD-konforme Abläufe und Umsatzsteuer-Voranmeldung vor dem Projekt prüfen; in anderen Ländern kann das gesetzliche Meldewesen schwächer sein als in spezialisierter lokaler Software.",
     "**Schnittstellen und Datenübernahme.** Stammdaten ohne Bereinigung zu importieren erzeugt Dubletten und falsche Bestände. Externe IDs für wiederholbare Importe nutzen, in Testläufen migrieren, Summen abgleichen. Schnittstellen zu Marktplätzen, Zahlungsanbietern und Telefonie brauchen Wiederholungen, Idempotenz und Überwachung – keinen blockierenden HTTP-Request.",
     "**Zugriffsrechte und Automatisierungen.** Falsche Gruppen und Datensatzregeln sind ein Sicherheits- und ein Supportproblem; mit echten Benutzerkonten testen, nicht als Admin. Automatisierte Aktionen „beim Speichern“ können sich gegenseitig oder denselben Datensatz erneut auslösen und in eine Schleife geraten; Serveraktionen mit Python-Code laufen mit erhöhten Rechten. Beides gehört ins Review.",
     "**Kopien der Produktion.** Eine Stage- oder Testdatenbank aus der Produktion mit aktiven Crons verschickt echte Rechnungen, Mahnungen und Schnittstellenaufrufe. Neutralisieren gehört zu jeder Wiederherstellung."],
    ["**Abhängigkeit vom Integrator.** Lizenzen sind günstig im Vergleich zu Einführung und Wartung; gutes Odoo-Wissen ist knapp. Klären, wer eigene Module pflegt, wer Upgrades macht und wer die Server überwacht.",
     "**Betrieb ist nicht umsonst.** Selbst hosten heißt Backups und Wiederherstellungstests, Monitoring, Updates von Betriebssystem, PostgreSQL und Odoo, Sicherheit. Odoo Online (SaaS) nimmt diese Arbeit ab, erlaubt aber keine eigenen Python-Module; Odoo.sh liegt dazwischen.",
     "**Widerstand der Mitarbeitenden.** Ohne rollenbezogene Schulung verstehen Mitarbeitende die Belegketten nicht, gehen zurück zu Excel und erzeugen Fehler, die später wie Softwareprobleme aussehen."],
    ["**Eine eigene Instanz für Cron-Jobs.** Einen zweiten Odoo-Prozess (Container oder Dienst) auf demselben Code und derselben Datenbank mit `--workers=0 --max-cron-threads=2 --no-http` betreiben und auf dem Webserver `max_cron_threads = 0` setzen. Schwere nächtliche Neuberechnungen und Importe belegen keine Web-Worker mehr, und ein Speicherlimit für den Cron-Container schützt die Worker der Benutzer – in einem echten Fall hielten acht Cron-Prozesse je 3,5–3,8 GB auf dem Webserver.",
     "**Sanfter Neustart statt kill.** `SIGHUP` lässt laufende Anfragen zu Ende laufen und startet Odoo mit denselben Argumenten neu, Code und `odoo.conf` werden neu gelesen. Sitzungen bleiben erhalten; Websockets verbinden sich neu.",
     "**queue_job (OCA) für schwere Arbeit.** Schnittstellen, Massen-E-Mails, Synchronisationen gehören in eine asynchrone Warteschlange mit Wiederholungen und Kanälen, die die Parallelität begrenzen, statt einen HTTP-Worker zu blockieren, bis das Zeitlimit ihn beendet. Der Job-Runner braucht eine eigene Datenbankverbindung (und mit PgBouncer einen Session-Pool)."],
    ["**Backups mit pg_dump und rsync, nicht über den Datenbankmanager.** Der Manager baut ein ZIP aus Datenbank und Filestore in einem Python-Worker – bei Datenbanken mit mehreren GB stößt er an Speicher- und Zeitlimits und blockiert einen Worker. `pg_dump -Fc` plus inkrementeller Filestore-Sync (oder Snapshots) ist schneller und tabellenweise wiederherstellbar. Den Manager abschalten (`list_db = False`).",
     "**Jede Kopie der Produktion neutralisieren.** Odoo 16+ hat `odoo-bin neutralize` (Crons und Mailserver aus, Zahlungsanbieter im Testmodus). `dbfilter` allein verhindert keinen Versand – er wählt nur die Datenbank. Zusätzlich Stage einen SMTP geben, der nicht zustellen kann (Mail-Catcher), und eine eigene `web.base.url` setzen.",
     "**PgBouncer im Transaktionsmodus** bei vielen Workern oder mehreren Odoo-Servern: Hunderte Client-Verbindungen teilen sich wenige Dutzend PostgreSQL-Verbindungen. Zwei Ausnahmen brauchen den Session-Modus: der Odoo-Bus (`LISTEN imbus`) und der queue_job-Runner."],
    ["**click-odoo-update für Deployments.** Es speichert Prüfsummen der Moduldateien in der Datenbank und führt `-u` nur für Module aus, deren Code sich geändert hat – Deployments dauern Sekunden statt Minuten, und niemand vergisst ein Modul.",
     "**Erst messen, dann tunen.** Für langsame Abfragen PostgreSQL selbst nutzen: `log_min_duration_statement`, `pg_stat_statements` oder PoWA. `log_level = debug_sql` protokolliert jede Abfrage und flutet das Log – nur für wenige Sekunden auf Stage; `log_db_level` schreibt Logzeilen in die Tabelle `ir_logging` und ist kein Profiling-Werkzeug. Odoo schreibt außerdem Anzahl der Abfragen, SQL-Zeit und übrige Zeit jeder Anfrage ans Ende seiner Log-Zeile.",
     "**py-spy für einen hängenden Worker.** `py-spy dump --pid <PID>` zeigt den Python-Stack eines laufenden Prozesses ohne Neustart. In Docker py-spy auf dem Host als root mit der Host-PID starten (oder dem Container `SYS_PTRACE` geben)."],
    ["Nach einem Deployment ist das Backend weiß oder ohne Styles, die Browserkonsole zeigt 404/500 für `/web/assets/...`, im Odoo-Log steht „Could not get content for /web/assets/…“ oder `FileNotFoundError`. Die Bundles sind Anhänge: der Datensatz liegt in der Datenbank, die Datei im Filestore. Wir haben das oft gesehen; die Ursachen sind fast immer dieselben:",
     ["der Filestore fehlt oder ist nicht persistent – Docker-Volume nicht eingebunden, `data_dir` geändert, Datenbank ohne Filestore wiederhergestellt;",
      "mehrere Odoo-Server ohne gemeinsamen Filestore – Server A hat das Bundle erzeugt, Server B findet die Datei nicht;",
      "ein Modul-Update wurde beim Kompilieren der Assets unterbrochen, oder eine kaputte SCSS/JS-Datei in einem eigenen Modul (dann zeigt das Log den Kompilierfehler – zuerst den Code reparieren);",
      "ein altes Bundle wird nach dem Update von CDN/Proxy aus dem Cache geliefert."]],
    "Die meisten Odoo-Probleme sind vorhersehbar – und damit vermeidbar: wenig und sauberer eigener Code, geplante Upgrades, geprüfte Drittmodule, gemessene Datenbank, Hintergrundarbeit von den Benutzern getrennt, Backups, die auf Stage tatsächlich wiederhergestellt werden. Wir richten das für Unternehmen in Deutschland, Österreich und der Schweiz ein und betreuen es.",
    "Links")

# ================================================================ FR
PROBLEMS["t"]["fr"] = _b("fr",
    "Les principaux problèmes d'Odoo – et comment les administrateurs et le DevOps les évitent",
    "Où Odoo fait vraiment mal : montées de version majeures, performances avec de gros volumes, modules tiers, sur-personnalisation, comptabilité locale, intégrations, droits et automatisations, coûts cachés. Plus des pratiques éprouvées pour admins et DevOps : instance cron séparée, redémarrage en douceur, queue_job, sauvegardes sans gestionnaire de bases, copies de stage neutralisées, PgBouncer, click-odoo-update, profilage et reconstruction des assets cassés.",
    "Les points faibles d'Odoo sont rarement des plantages du noyau. Ils apparaissent avec la croissance : la version majeure annuelle, des millions d'enregistrements, des centaines d'utilisateurs, des modules de l'app store et du code écrit « vite » pour la mise en production. Voici une liste issue de la pratique – ce qui se passe mal et ce que nous faisons sur les serveurs que nous exploitons.",
    "En bref : peu de personnalisations et dans des modules, planifier les montées de version comme des projets, vérifier le code tiers, mesurer avant d'optimiser, séparer les crons des workers web, sauvegarder avec pg_dump + synchronisation du filestore, neutraliser chaque copie de la production – et savoir reconstruire les assets.",
    ["Limites techniques et d'architecture", "Mise en œuvre et exploitation", "Coûts cachés", "Vue d'ensemble", "Conseils d'admin : processus et charge", "Base de données, sauvegardes, stage", "Déploiement, débogage, supervision", "Assets cassés – un classique", "Conclusion"],
    ["**Montées de version majeures.** Une nouvelle version chaque année ; entre les versions, modèles, champs, JavaScript (OWL) et vues changent. Les modules spécifiques cassent sur des champs renommés et des expressions XPath qui ne correspondent plus. Le service de migration d'Odoo (Enterprise) ne migre que les modules standard ; les bases Community passent par OpenUpgrade (OCA). Chaque module spécifique a besoin de sa propre migration et d'un test sur une copie – c'est un projet avec un budget, pas un bouton.",
     "**Performances avec de gros volumes.** Le monolithe lui-même est rarement la limite ; causes typiques : code spécifique avec requêtes N+1 (`read()`/`search()` dans une boucle), champs calculés stockés recalculés sur des millions d'enregistrements, index manquants sur les champs utilisés dans les domaines, `mail_message`/`mail_tracking_value` qui atteignent des centaines de Go, et longs crons dont les workers gardent des gigaoctets de RAM. Sans mesure (statistiques PostgreSQL, temps des requêtes dans le journal), l'optimisation est de la devinette.",
     "**Modules tiers.** La boutique Odoo Apps ne vérifie guère plus que l'installation d'un module – il n'y a pas de certification de qualité. Surcharges concurrentes de la même méthode, règles d'accès manquantes, `sudo()` et SQL brut avec formatage de chaînes sont fréquents. Les modules OCA passent par une revue et une CI, mais doivent aussi être testés dans votre combinaison.",
     "**Travail hors ligne.** Le point de vente fonctionne hors ligne et synchronise plus tard ; presque tout le reste (backend, application mobile – au fond le client web) exige une connexion.",
     "**Community vs Enterprise.** Certaines fonctions n'existent qu'en Enterprise (par ex. rapports comptables complets, Studio, certaines localisations, fonctions de l'application mobile) ; combler l'écart avec des modules tiers augmente le risque à chaque montée de version."],
    ["**Le piège de la sur-personnalisation.** Comme tout peut être modifié, les entreprises recodent leurs anciens processus au lieu d'adopter les flux standard. Chaque changement se paie à nouveau à chaque montée de version. Règle empirique : la configuration avant Studio, Studio avant le code, du code seulement là où il crée une vraie valeur – et toujours dans des modules versionnés, jamais seulement dans la base.",
     "**Profondeur de la comptabilité locale.** La qualité des localisations dépend du pays et de l'édition. En Allemagne, par exemple, vérifier l'export DATEV, les processus conformes GoBD et les déclarations de TVA avant le projet ; ailleurs, les déclarations réglementaires peuvent être plus faibles que dans un logiciel local spécialisé.",
     "**Intégrations et reprise de données.** Importer des données de base sans nettoyage crée des doublons et des stocks faux. Utiliser des ID externes pour des imports répétables, migrer par essais, rapprocher les totaux. Les intégrations avec places de marché, prestataires de paiement et téléphonie demandent nouvelles tentatives, idempotence et supervision – pas une requête HTTP bloquante.",
     "**Droits d'accès et automatisations.** Des groupes et règles d'enregistrement erronés posent un problème de sécurité et de support ; les tester avec de vrais comptes utilisateurs, pas en admin. Les actions automatisées « à l'enregistrement » peuvent se déclencher mutuellement ou relancer le même enregistrement et boucler ; les actions serveur en Python s'exécutent avec des droits élevés. Les deux relèvent de la revue de code.",
     "**Copies de la production.** Une base de stage ou de test restaurée depuis la production avec des crons actifs envoie de vraies factures, relances et appels d'intégration. La neutralisation fait partie de chaque restauration."],
    ["**Dépendance envers l'intégrateur.** Les licences sont bon marché comparées à la mise en œuvre et à la maintenance ; les bonnes compétences Odoo sont rares. Clarifier qui maintient les modules spécifiques, qui fait les montées de version et qui surveille les serveurs.",
     "**L'exploitation n'est pas gratuite.** Héberger soi-même signifie sauvegardes et tests de restauration, supervision, mises à jour de l'OS, de PostgreSQL et d'Odoo, sécurité. Odoo Online (SaaS) supprime ce travail mais n'autorise pas de modules Python spécifiques ; Odoo.sh se situe entre les deux.",
     "**Résistance du personnel.** Sans formation par rôle, les employés ne comprennent pas les chaînes de documents, reviennent à Excel et créent des erreurs qui ressemblent ensuite à des problèmes du logiciel."],
    ["**Une instance séparée pour les crons.** Faire tourner un second processus Odoo (conteneur ou service) sur le même code et la même base avec `--workers=0 --max-cron-threads=2 --no-http`, et mettre `max_cron_threads = 0` sur le serveur web. Les lourds recalculs nocturnes et imports n'occupent plus de workers web, et une limite mémoire sur le conteneur cron protège les workers des utilisateurs – dans un cas réel, huit processus cron gardaient chacun 3,5–3,8 Go sur le serveur web.",
     "**Redémarrage en douceur plutôt que kill.** `SIGHUP` laisse finir les requêtes en cours et redémarre Odoo avec les mêmes arguments, en relisant le code et `odoo.conf`. Les sessions survivent ; les websockets se reconnectent.",
     "**queue_job (OCA) pour les gros traitements.** Intégrations, e-mails en masse, synchronisations vont dans une file asynchrone avec nouvelles tentatives et canaux qui limitent le parallélisme, au lieu de bloquer un worker HTTP jusqu'à ce que la limite de temps le tue. Le runner a besoin de sa propre connexion à la base (et d'un pool en mode session avec PgBouncer)."],
    ["**Sauvegardes avec pg_dump et rsync, pas via le gestionnaire de bases.** Le gestionnaire construit un ZIP de la base et du filestore dans un worker Python – avec des bases de plusieurs Go, il atteint les limites de mémoire et de temps et bloque un worker. `pg_dump -Fc` plus une synchronisation incrémentale du filestore (ou des snapshots) est plus rapide et restaurable table par table. Désactiver le gestionnaire (`list_db = False`).",
     "**Neutraliser chaque copie de la production.** Odoo 16+ a `odoo-bin neutralize` (crons et serveurs de mail désactivés, prestataires de paiement en mode test). `dbfilter` seul n'empêche aucun envoi – il choisit seulement la base. En plus, donner au stage un SMTP qui ne peut pas livrer (un mail catcher) et sa propre `web.base.url`.",
     "**PgBouncer en mode transaction** avec beaucoup de workers ou plusieurs serveurs Odoo : des centaines de connexions client partagent quelques dizaines de connexions PostgreSQL. Deux exceptions exigent le mode session : le bus Odoo (`LISTEN imbus`) et le runner queue_job."],
    ["**click-odoo-update pour les déploiements.** Il enregistre des sommes de contrôle des fichiers de modules dans la base et lance `-u` seulement pour les modules dont le code a changé – les déploiements prennent des secondes au lieu de minutes, et personne n'oublie un module.",
     "**Mesurer, puis optimiser.** Pour les requêtes lentes, utiliser PostgreSQL lui-même : `log_min_duration_statement`, `pg_stat_statements` ou PoWA. `log_level = debug_sql` journalise chaque requête et inonde le journal – seulement quelques secondes sur stage ; `log_db_level` écrit les lignes de journal dans la table `ir_logging` et n'est pas un outil de profilage. Odoo écrit aussi le nombre de requêtes, le temps SQL et le temps restant de chaque requête HTTP à la fin de sa ligne de journal.",
     "**py-spy pour un worker bloqué.** `py-spy dump --pid <PID>` montre la pile Python d'un processus en cours sans le redémarrer. Dans Docker, lancer py-spy sur l'hôte en root avec le PID de l'hôte (ou donner `SYS_PTRACE` au conteneur)."],
    ["Après un déploiement, le backend est blanc ou sans styles, la console du navigateur montre 404/500 pour `/web/assets/...`, le journal Odoo indique « Could not get content for /web/assets/… » ou `FileNotFoundError`. Les bundles sont des pièces jointes : l'enregistrement est dans la base, le fichier dans le filestore. Nous l'avons vu de nombreuses fois ; les causes sont presque toujours les mêmes :",
     ["le filestore manque ou n'est pas persistant – volume Docker non monté, `data_dir` modifié, base restaurée sans son filestore ;",
      "plusieurs serveurs Odoo sans filestore partagé – le serveur A a généré le bundle, le serveur B ne trouve pas le fichier ;",
      "une mise à jour de module interrompue pendant la compilation des assets, ou un fichier SCSS/JS cassé dans un module spécifique (le journal montre alors l'erreur de compilation – réparer d'abord le code) ;",
      "un ancien bundle servi depuis le cache d'un CDN/proxy après la mise à jour."]],
    "La plupart des problèmes d'Odoo sont prévisibles – donc évitables : peu de code spécifique et propre, des montées de version planifiées, des modules tiers vérifiés, une base mesurée, le travail de fond séparé des utilisateurs, des sauvegardes réellement restaurées sur stage. Nous mettons cela en place et l'exploitons pour des entreprises en Allemagne, en Autriche et en Suisse.",
    "Liens")

# ================================================================ EL
PROBLEMS["t"]["el"] = _b("el",
    "Τα κύρια προβλήματα του Odoo – και πώς τα αποφεύγουν οι διαχειριστές και το DevOps",
    "Πού πονά πραγματικά το Odoo: μεγάλες αναβαθμίσεις, απόδοση με μεγάλο όγκο δεδομένων, modules τρίτων, υπερβολική προσαρμογή, τοπική λογιστική, διασυνδέσεις, δικαιώματα και αυτοματισμοί, κρυφό κόστος. Και δοκιμασμένες πρακτικές για διαχειριστές και DevOps: ξεχωριστό instance για cron, ήπια επανεκκίνηση, queue_job, αντίγραφα χωρίς τον διαχειριστή βάσεων, εξουδετερωμένα αντίγραφα stage, PgBouncer, click-odoo-update, profiling και αναδημιουργία χαλασμένων assets.",
    "Τα αδύναμα σημεία του Odoo σπάνια είναι καταρρεύσεις του πυρήνα. Εμφανίζονται με την ανάπτυξη: η ετήσια κύρια έκδοση, εκατομμύρια εγγραφές, εκατοντάδες χρήστες, modules από το app store και κώδικας γραμμένος «γρήγορα» για την έναρξη λειτουργίας. Μια λίστα από την πράξη – τι πάει στραβά και τι κάνουμε στους servers που διαχειριζόμαστε.",
    "Συνοπτικά: λίγες προσαρμογές και μέσα σε modules, οι αναβαθμίσεις ως έργα, έλεγχος κώδικα τρίτων, πρώτα μέτρηση και μετά ρύθμιση, cron χωριστά από τους web workers, αντίγραφα με pg_dump + συγχρονισμό filestore, εξουδετέρωση κάθε αντιγράφου της παραγωγής – και γνώση του πώς ξαναφτιάχνονται τα assets.",
    ["Τεχνικά και αρχιτεκτονικά όρια", "Υλοποίηση και λειτουργία", "Κρυφό κόστος", "Σύνοψη", "Συμβουλές διαχείρισης: διεργασίες και φορτίο", "Βάση, αντίγραφα, stage", "Deploy, debugging, παρακολούθηση", "Χαλασμένα assets – ένα κλασικό", "Συμπέρασμα"],
    ["**Μεγάλες αναβαθμίσεις.** Κάθε χρόνο νέα έκδοση· ανάμεσα στις εκδόσεις αλλάζουν μοντέλα, πεδία, JavaScript (OWL) και views. Τα δικά σας modules σπάνε σε πεδία που μετονομάστηκαν και εκφράσεις XPath που δεν ταιριάζουν πια. Η υπηρεσία αναβάθμισης του Odoo (Enterprise) μεταφέρει μόνο τα τυπικά modules· οι βάσεις Community περνούν από το OpenUpgrade (OCA). Κάθε δικό σας module χρειάζεται δική του μετάβαση και δοκιμή σε αντίγραφο – είναι έργο με προϋπολογισμό, όχι ένα κουμπί.",
     "**Απόδοση με μεγάλο όγκο δεδομένων.** Ο μονόλιθος σπάνια είναι το όριο· τυπικές αιτίες είναι κώδικας με ερωτήματα N+1 (`read()`/`search()` σε βρόχο), αποθηκευμένα υπολογιζόμενα πεδία που ξαναϋπολογίζονται σε εκατομμύρια εγγραφές, ευρετήρια που λείπουν σε πεδία των domains, `mail_message`/`mail_tracking_value` που φτάνουν εκατοντάδες GB και μακροχρόνια cron των οποίων οι workers κρατούν gigabytes RAM. Χωρίς μέτρηση (στατιστικά PostgreSQL, χρόνοι αιτημάτων στο log) η ρύθμιση είναι μαντεψιά.",
     "**Modules τρίτων.** Το κατάστημα Odoo Apps ελέγχει ελάχιστα περισσότερα από το αν ένα module εγκαθίσταται – δεν υπάρχει πιστοποίηση ποιότητας. Συχνά βλέπουμε ανταγωνιστικές επικαλύψεις της ίδιας μεθόδου, κανόνες πρόσβασης που λείπουν, `sudo()` και ωμό SQL με μορφοποίηση συμβολοσειρών. Τα modules του OCA περνούν από review και CI, αλλά πρέπει κι αυτά να δοκιμαστούν στον δικό σας συνδυασμό.",
     "**Εργασία εκτός σύνδεσης.** Το ταμείο (Point of Sale) δουλεύει offline και συγχρονίζει αργότερα· σχεδόν όλα τα άλλα (backend, mobile app – ουσιαστικά ο web client) χρειάζονται σύνδεση.",
     "**Community vs Enterprise.** Ορισμένες λειτουργίες υπάρχουν μόνο στο Enterprise (π.χ. πλήρεις λογιστικές αναφορές, Studio, κάποιες τοπικοποιήσεις, λειτουργίες της mobile app)· η κάλυψη του κενού με modules τρίτων αυξάνει τον κίνδυνο στις αναβαθμίσεις."],
    ["**Η παγίδα της υπερβολικής προσαρμογής.** Επειδή όλα αλλάζουν, οι εταιρείες ξαναχτίζουν τις παλιές τους διαδικασίες σε κώδικα αντί να υιοθετήσουν τις τυπικές ροές. Κάθε αλλαγή πληρώνεται ξανά σε κάθε αναβάθμιση. Εμπειρικός κανόνας: ρύθμιση πριν από το Studio, Studio πριν από τον κώδικα, κώδικας μόνο όπου δημιουργεί πραγματική αξία – και πάντα σε modules με έλεγχο εκδόσεων, ποτέ μόνο μέσα στη βάση.",
     "**Βάθος τοπικής λογιστικής.** Η ποιότητα των τοπικοποιήσεων διαφέρει ανά χώρα και έκδοση. Στη Γερμανία, για παράδειγμα, ελέγξτε την εξαγωγή DATEV, διαδικασίες συμβατές με GoBD και δηλώσεις ΦΠΑ πριν από το έργο· σε άλλες χώρες οι υποχρεωτικές αναφορές μπορεί να είναι πιο αδύναμες από εξειδικευμένο τοπικό λογισμικό.",
     "**Διασυνδέσεις και μεταφορά δεδομένων.** Η εισαγωγή βασικών δεδομένων χωρίς καθαρισμό δημιουργεί διπλότυπα και λάθος αποθέματα. Χρησιμοποιήστε εξωτερικά IDs για επαναλήψιμες εισαγωγές, μεταφέρετε με δοκιμαστικές εκτελέσεις, συμφωνήστε τα σύνολα. Οι διασυνδέσεις με marketplaces, παρόχους πληρωμών και τηλεφωνία χρειάζονται επαναλήψεις, idempotency και παρακολούθηση – όχι ένα μπλοκαρισμένο αίτημα HTTP.",
     "**Δικαιώματα και αυτοματισμοί.** Λάθος ομάδες και κανόνες εγγραφών είναι πρόβλημα ασφάλειας και υποστήριξης· δοκιμάστε τα με πραγματικούς λογαριασμούς χρηστών, όχι ως admin. Οι αυτοματοποιημένες ενέργειες «κατά την αποθήκευση» μπορούν να ενεργοποιούν η μία την άλλη ή ξανά την ίδια εγγραφή και να μπουν σε βρόχο· οι server actions με κώδικα Python τρέχουν με αυξημένα δικαιώματα. Και τα δύο ανήκουν στον έλεγχο κώδικα.",
     "**Αντίγραφα της παραγωγής.** Μια βάση stage ή δοκιμών από την παραγωγή με ενεργά cron στέλνει πραγματικά τιμολόγια, υπενθυμίσεις και κλήσεις διασυνδέσεων. Η εξουδετέρωση είναι μέρος κάθε επαναφοράς."],
    ["**Εξάρτηση από τον συνεργάτη υλοποίησης.** Οι άδειες είναι φθηνές σε σύγκριση με την υλοποίηση και τη συντήρηση· η καλή γνώση του Odoo σπανίζει. Ξεκαθαρίστε ποιος συντηρεί τα δικά σας modules, ποιος κάνει τις αναβαθμίσεις και ποιος παρακολουθεί τους servers.",
     "**Η λειτουργία δεν είναι δωρεάν.** Η αυτοφιλοξενία σημαίνει αντίγραφα και δοκιμές επαναφοράς, παρακολούθηση, ενημερώσεις λειτουργικού, PostgreSQL και Odoo, ασφάλεια. Το Odoo Online (SaaS) αφαιρεί αυτή τη δουλειά αλλά δεν επιτρέπει δικά σας modules Python· το Odoo.sh βρίσκεται ενδιάμεσα.",
     "**Αντίσταση του προσωπικού.** Χωρίς εκπαίδευση ανά ρόλο, οι εργαζόμενοι δεν καταλαβαίνουν τις αλυσίδες παραστατικών, γυρίζουν στο Excel και δημιουργούν λάθη που αργότερα μοιάζουν με προβλήματα του λογισμικού."],
    ["**Ξεχωριστό instance για cron.** Τρέξτε δεύτερη διεργασία Odoo (container ή υπηρεσία) στον ίδιο κώδικα και την ίδια βάση με `--workers=0 --max-cron-threads=2 --no-http` και ορίστε `max_cron_threads = 0` στον web server. Οι βαριοί νυχτερινοί επανυπολογισμοί και οι εισαγωγές δεν πιάνουν πια web workers, και ένα όριο μνήμης στο container των cron προστατεύει τους workers των χρηστών – σε πραγματική περίπτωση οκτώ διεργασίες cron κρατούσαν η καθεμία 3,5–3,8 GB στον web server.",
     "**Ήπια επανεκκίνηση αντί για kill.** Το `SIGHUP` αφήνει τα τρέχοντα αιτήματα να ολοκληρωθούν και επανεκκινεί το Odoo με τα ίδια ορίσματα, ξαναδιαβάζοντας κώδικα και `odoo.conf`. Οι συνεδρίες επιβιώνουν· τα websockets επανασυνδέονται.",
     "**queue_job (OCA) για βαριά δουλειά.** Διασυνδέσεις, μαζικά e-mail και συγχρονισμοί μπαίνουν σε ασύγχρονη ουρά με επαναλήψεις και κανάλια που περιορίζουν τον παραλληλισμό, αντί να μπλοκάρουν έναν HTTP worker μέχρι να τον τερματίσει το χρονικό όριο. Ο job runner χρειάζεται δική του σύνδεση στη βάση (και pool σε session mode με PgBouncer)."],
    ["**Αντίγραφα με pg_dump και rsync, όχι μέσω του διαχειριστή βάσεων.** Ο διαχειριστής φτιάχνει ZIP από βάση και filestore μέσα σε έναν Python worker – με βάσεις αρκετών GB χτυπά όρια μνήμης και χρόνου και μπλοκάρει έναν worker. Το `pg_dump -Fc` μαζί με σταδιακό συγχρονισμό του filestore (ή snapshots) είναι ταχύτερο και επαναφέρεται και ανά πίνακα. Απενεργοποιήστε τον διαχειριστή (`list_db = False`).",
     "**Εξουδετέρωση κάθε αντιγράφου της παραγωγής.** Το Odoo 16+ έχει `odoo-bin neutralize` (cron και mail servers απενεργοποιημένα, πάροχοι πληρωμών σε test mode). Το `dbfilter` μόνο του δεν σταματά καμία αποστολή – απλώς επιλέγει τη βάση. Επιπλέον, δώστε στο stage ένα SMTP που δεν μπορεί να παραδώσει (mail catcher) και δικό του `web.base.url`.",
     "**PgBouncer σε transaction mode** με πολλούς workers ή πολλούς servers Odoo: εκατοντάδες συνδέσεις clients μοιράζονται λίγες δεκάδες συνδέσεις PostgreSQL. Δύο εξαιρέσεις χρειάζονται session mode: ο δίαυλος του Odoo (`LISTEN imbus`) και ο runner του queue_job."],
    ["**click-odoo-update για τα deploys.** Αποθηκεύει checksums των αρχείων των modules στη βάση και τρέχει `-u` μόνο για τα modules των οποίων ο κώδικας άλλαξε – τα deploys διαρκούν δευτερόλεπτα αντί για λεπτά, και κανείς δεν ξεχνά module.",
     "**Πρώτα μέτρηση, μετά ρύθμιση.** Για αργά ερωτήματα χρησιμοποιήστε το ίδιο το PostgreSQL: `log_min_duration_statement`, `pg_stat_statements` ή PoWA. Το `log_level = debug_sql` καταγράφει κάθε ερώτημα και πλημμυρίζει το log – μόνο για λίγα δευτερόλεπτα σε stage· το `log_db_level` γράφει γραμμές log στον πίνακα `ir_logging` και δεν είναι εργαλείο profiling. Το Odoo γράφει επίσης στο τέλος της γραμμής log κάθε αιτήματος τον αριθμό ερωτημάτων, τον χρόνο SQL και τον υπόλοιπο χρόνο.",
     "**py-spy για έναν worker που κόλλησε.** Το `py-spy dump --pid <PID>` δείχνει τη στοίβα Python μιας διεργασίας που τρέχει χωρίς επανεκκίνηση. Σε Docker τρέξτε το py-spy στον host ως root με το PID του host (ή δώστε στο container `SYS_PTRACE`)."],
    ["Μετά από ένα deploy το backend είναι λευκό ή χωρίς στυλ, η κονσόλα του browser δείχνει 404/500 για `/web/assets/...`, το log του Odoo γράφει «Could not get content for /web/assets/…» ή `FileNotFoundError`. Τα bundles είναι συνημμένα: η εγγραφή βρίσκεται στη βάση, το αρχείο στο filestore. Το έχουμε δει πολλές φορές· οι αιτίες είναι σχεδόν πάντα ίδιες:",
     ["το filestore λείπει ή δεν είναι μόνιμο – volume Docker που δεν προσαρτήθηκε, αλλαγμένο `data_dir`, βάση που επαναφέρθηκε χωρίς το filestore της·",
      "πολλοί servers Odoo χωρίς κοινό filestore – ο server A δημιούργησε το bundle, ο server B δεν βρίσκει το αρχείο·",
      "ενημέρωση module που διακόπηκε κατά τη μεταγλώττιση των assets ή χαλασμένο αρχείο SCSS/JS σε δικό σας module (τότε το log δείχνει το σφάλμα μεταγλώττισης – πρώτα διορθώστε τον κώδικα)·",
      "παλιό bundle που σερβίρεται από cache CDN/proxy μετά την ενημέρωση."]],
    "Τα περισσότερα προβλήματα του Odoo είναι προβλέψιμα – άρα αποφεύξιμα: λίγος και καθαρός δικός σας κώδικας, σχεδιασμένες αναβαθμίσεις, ελεγμένα modules τρίτων, μετρημένη βάση, εργασίες παρασκηνίου χωριστά από τους χρήστες, αντίγραφα που πράγματι επαναφέρονται σε stage. Τα στήνουμε και τα συντηρούμε για επιχειρήσεις στη Γερμανία, την Αυστρία και την Ελβετία.",
    "Σύνδεσμοι")

# ================================================================ UK
PROBLEMS["t"]["uk"] = _b("uk",
    "Головні проблеми Odoo і як адміністратори та DevOps їх уникають",
    "Де Odoo справді болить: мажорні оновлення, продуктивність на великих обсягах, сторонні модулі, надмірна кастомізація, локальний облік, інтеграції, права й автоматизації, приховані витрати. А також перевірені практики для адміністраторів і DevOps: окремий інстанс для cron, м'який перезапуск, queue_job, бекапи без менеджера баз, знешкоджені копії для stage, PgBouncer, click-odoo-update, профілювання і перезбирання зламаних assets.",
    "Слабкі місця Odoo рідко пов'язані з падінням ядра. Вони проявляються з ростом: щорічна мажорна версія, мільйони записів, сотні користувачів, модулі з магазину застосунків і код, написаний «швидко» до запуску. Нижче список із практики: що йде не так і що ми з цим робимо на серверах, які супроводжуємо.",
    "Коротко: доробок мало, і всі вони в модулях. Оновлення плануємо як окремі проєкти, сторонній код перевіряємо, спершу вимірюємо, потім налаштовуємо. Cron відокремлюємо від веб-воркерів, бекап робимо через pg_dump і синхронізацію filestore, кожну копію продакшену знешкоджуємо. І знаємо, як перезібрати assets.",
    ["Технічні та архітектурні обмеження", "Впровадження та експлуатація", "Приховані витрати", "Огляд", "Поради адміну: процеси й навантаження", "База даних, бекапи, stage", "Деплой, дебаг, моніторинг", "Зламані assets — класика", "Висновок"],
    ["**Мажорні оновлення.** Нова версія виходить щороку, і між версіями змінюються моделі, поля, JavaScript (OWL) та представлення. Власні модулі ламаються на перейменованих полях і XPath, які більше не знаходять потрібного елемента. Сервіс оновлення Odoo (Enterprise) мігрує лише стандартні модулі, а бази Community проходять через OpenUpgrade (OCA). Кожному власному модулю потрібна своя міграція й тест на копії. Це проєкт із бюджетом, а не кнопка.",
     "**Продуктивність на великих обсягах.** Сам моноліт рідко буває межею. Типові причини інші: власний код із запитами N+1 (`read()`/`search()` у циклі), збережені обчислювані поля, які перераховуються на мільйонах записів, відсутні індекси на полях із доменів, `mail_message`/`mail_tracking_value` на сотні ГБ і довгі крони, воркери яких тримають гігабайти RAM. Без вимірювань (статистика PostgreSQL, час запитів у лозі) налаштування перетворюється на вгадування.",
     "**Сторонні модулі.** Магазин Odoo Apps перевіряє хіба що те, що модуль установлюється; сертифікації якості немає. Часто трапляються конфліктні перевизначення того самого методу, відсутні правила доступу, `sudo()` і сирий SQL із форматуванням рядків. Модулі OCA проходять рев'ю і CI, але їх теж треба тестувати у вашій комбінації.",
     "**Робота офлайн.** Каса (Point of Sale) працює офлайн і синхронізується пізніше. Майже все інше (бекенд, мобільний застосунок, який по суті є веб-клієнтом) потребує з'єднання.",
     "**Community чи Enterprise.** Частина функцій є лише в Enterprise (наприклад, повні бухгалтерські звіти, Studio, деякі локалізації, функції мобільного застосунку). Закривати цю різницю сторонніми модулями означає підвищувати ризик при кожному оновленні."],
    ["**Пастка надмірної кастомізації.** Оскільки змінити можна все, компанії переносять у код свої старі процеси замість того, щоб прийняти стандартні сценарії. За кожну зміну доводиться платити знову при кожному оновленні. Практичне правило: налаштування раніше за Studio, Studio раніше за код, код лише там, де він дає реальну цінність. І завжди в модулях під контролем версій, а не лише в базі.",
     "**Глибина локального обліку.** Якість локалізацій залежить від країни та редакції. У Німеччині, наприклад, до старту проєкту варто перевірити експорт у DATEV, процеси за GoBD і декларації ПДВ. В інших країнах регламентована звітність може бути слабшою, ніж у спеціалізованому локальному ПЗ.",
     "**Інтеграції та перенесення даних.** Імпорт довідників без очищення створює дублікати й неправильні залишки. Використовуйте зовнішні ID для повторюваних імпортів, мігруйте пробними прогонами, звіряйте підсумки. Інтеграціям із маркетплейсами, платіжними сервісами й телефонією потрібні повтори, ідемпотентність і моніторинг, а не блокувальний HTTP-запит.",
     "**Права доступу й автоматизації.** Неправильні групи та record rules — це проблема і безпеки, і підтримки. Перевіряйте їх на реальних облікових записах користувачів, а не під адміном. Автоматичні дії «при збереженні» можуть запускати одна одну або той самий запис і зациклитися. Серверні дії з кодом Python виконуються з підвищеними правами. І те, і інше має проходити рев'ю.",
     "**Копії продакшену.** База stage чи тестова база, відновлена з продакшену з активними кронами, розсилає справжні рахунки, нагадування й виклики інтеграцій. Знешкодження — обов'язкова частина кожного відновлення."],
    ["**Залежність від інтегратора.** Ліцензії дешеві порівняно з упровадженням і супроводом, а хороших знавців Odoo мало. Домовтеся, хто супроводжує власні модулі, хто робить оновлення і хто стежить за серверами.",
     "**Експлуатація не безкоштовна.** Власний хостинг означає бекапи й тести відновлення, моніторинг, оновлення ОС, PostgreSQL та Odoo, безпеку. Odoo Online (SaaS) знімає цю роботу, але не дозволяє власних Python-модулів. Odoo.sh посередині.",
     "**Опір персоналу.** Без навчання за ролями співробітники не розуміють ланцюжків документів, повертаються до Excel і роблять помилки, які потім виглядають як проблеми програми."],
    ["**Окремий інстанс для cron.** Запустіть другий процес Odoo (контейнер або сервіс) на тому самому коді й базі з `--workers=0 --max-cron-threads=2 --no-http`, а на веб-сервері поставте `max_cron_threads = 0`. Тоді важкі нічні перерахунки й імпорти більше не займають веб-воркери, а ліміт пам'яті на контейнері з кронами захищає воркери користувачів. У реальному випадку вісім процесів cron тримали по 3,5–3,8 ГБ кожен на веб-сервері.",
     "**М'який перезапуск замість kill.** `SIGHUP` дає завершитися поточним запитам і перезапускає Odoo з тими самими аргументами, перечитуючи код і `odoo.conf`. Сесії зберігаються, websockets перепідключаються.",
     "**queue_job (OCA) для важкої роботи.** Інтеграції, масові розсилки й синхронізації йдуть в асинхронну чергу з повторами й каналами, які обмежують паралельність. Так вони не блокують HTTP-воркер, доки його не вб'є ліміт часу. Runner потребує власного з'єднання з базою (а з PgBouncer — пулу в режимі session)."],
    ["**Бекапи через pg_dump і rsync, а не через менеджер баз.** Менеджер пакує базу й filestore у ZIP усередині Python-воркера. На базах у кілька ГБ він упирається в ліміти пам'яті й часу і блокує воркер. `pg_dump -Fc` плюс інкрементна синхронізація filestore (або знімки) працює швидше й дає змогу відновлювати окремі таблиці. Менеджер вимкніть (`list_db = False`).",
     "**Знешкоджуйте кожну копію продакшену.** В Odoo 16+ є `odoo-bin neutralize`: він вимикає крони й поштові сервери та переводить платіжні сервіси в тестовий режим. Сам `dbfilter` нічого не блокує, він лише вибирає базу. Додатково дайте stage SMTP, який не може доставити пошту (mail catcher), і власний `web.base.url`.",
     "**PgBouncer у режимі transaction**, коли воркерів багато або серверів Odoo кілька. Сотні клієнтських з'єднань ділять кілька десятків з'єднань PostgreSQL. Два винятки потребують режиму session: шина Odoo (`LISTEN imbus`) і runner queue_job."],
    ["**click-odoo-update для деплою.** Він зберігає контрольні суми файлів модулів у базі й запускає `-u` лише для модулів зі зміненим кодом. Деплой триває секунди замість хвилин, і ніхто не забуде модуль.",
     "**Спершу вимірювати, потім налаштовувати.** Для повільних запитів використовуйте сам PostgreSQL: `log_min_duration_statement`, `pg_stat_statements` або PoWA. `log_level = debug_sql` пише в лог кожен запит і заливає його повністю, тому вмикайте його лише на кілька секунд і на stage. `log_db_level` записує рядки логу в таблицю `ir_logging` і для профілювання не підходить. Odoo також пише в кінці рядка логу кожного HTTP-запиту кількість SQL-запитів, час SQL і решту часу.",
     "**py-spy для завислого воркера.** `py-spy dump --pid <PID>` показує стек Python процесу, що працює, без перезапуску. У Docker запускайте py-spy на хості під root з PID хоста (або дайте контейнеру `SYS_PTRACE`)."],
    ["Після деплою бекенд білий або без стилів, консоль браузера показує 404/500 для `/web/assets/...`, а в лозі Odoo «Could not get content for /web/assets/…» або `FileNotFoundError`. Бандли — це вкладення: запис лежить у базі, файл — у filestore. Ми бачили це багато разів, і причини майже завжди ті самі:",
     ["filestore відсутній або не зберігається між перезапусками: том Docker не змонтований, змінено `data_dir`, базу відновили без її filestore;",
      "кілька серверів Odoo без спільного filestore: сервер A згенерував бандл, а сервер B не знаходить файл;",
      "оновлення модуля перервалося під час компіляції assets, або у власному модулі зламаний файл SCSS/JS (тоді в лозі видно помилку компіляції, і спершу треба виправити код);",
      "після оновлення CDN або проксі віддає старий бандл із кешу."]],
    "Більшість проблем Odoo передбачувані, а отже, їм можна запобігти. Потрібні мінімум чистого власного коду, сплановані оновлення, перевірені сторонні модулі, виміряна база, фонові задачі окремо від користувачів і бекапи, які справді відновлюють на stage. Ми налаштовуємо й супроводжуємо це для компаній у Німеччині, Австрії та Швейцарії.",
    "Посилання")

# ================================================================ RU
PROBLEMS["t"]["ru"] = _b("ru",
    "Главные проблемы Odoo и как администраторы и DevOps их обходят",
    "Где Odoo действительно болит: мажорные обновления, производительность на больших объёмах, сторонние модули, избыточная кастомизация, локальный учёт, интеграции, права и автоматизации, скрытые затраты. И проверенные практики для администраторов и DevOps: отдельный инстанс для cron, мягкий перезапуск, queue_job, бэкапы без менеджера баз, обезвреженные копии для stage, PgBouncer, click-odoo-update, профилирование и пересборка сломанных assets.",
    "Слабые места Odoo редко связаны с падением ядра. Они проявляются с ростом: ежегодная мажорная версия, миллионы записей, сотни пользователей, модули из магазина приложений и код, написанный «быстро» к запуску. Ниже список из практики: что идёт не так и что мы с этим делаем на серверах, которые сопровождаем.",
    "Коротко: доработок мало, и все они в модулях. Обновления планируем как отдельные проекты, сторонний код проверяем, сначала измеряем, потом настраиваем. Cron отделяем от веб-воркеров, бэкап делаем через pg_dump и синхронизацию filestore, каждую копию продакшена обезвреживаем. И знаем, как пересобрать assets.",
    ["Технические и архитектурные ограничения", "Внедрение и эксплуатация", "Скрытые затраты", "Обзор", "Советы админу: процессы и нагрузка", "База данных, бэкапы, stage", "Деплой, отладка, мониторинг", "Сломанные assets — классика", "Вывод"],
    ["**Мажорные обновления.** Новая версия выходит каждый год, и между версиями меняются модели, поля, JavaScript (OWL) и представления. Свои модули ломаются на переименованных полях и XPath, которые больше не находят нужный элемент. Сервис обновления Odoo (Enterprise) мигрирует только стандартные модули, а базы Community проходят через OpenUpgrade (OCA). Каждому своему модулю нужна своя миграция и тест на копии. Это проект с бюджетом, а не кнопка.",
     "**Производительность на больших объёмах.** Сам монолит редко бывает пределом. Типичные причины другие: свой код с запросами N+1 (`read()`/`search()` в цикле), хранимые вычисляемые поля, которые пересчитываются на миллионах записей, отсутствующие индексы на полях из доменов, `mail_message`/`mail_tracking_value` на сотни ГБ и долгие кроны, воркеры которых держат гигабайты RAM. Без измерений (статистика PostgreSQL, время запросов в логе) настройка превращается в угадывание.",
     "**Сторонние модули.** Магазин Odoo Apps проверяет разве что то, что модуль устанавливается; сертификации качества нет. Часто встречаются конфликтующие переопределения одного метода, отсутствующие правила доступа, `sudo()` и сырой SQL с форматированием строк. Модули OCA проходят ревью и CI, но их тоже нужно тестировать в вашей комбинации.",
     "**Работа офлайн.** Касса (Point of Sale) работает офлайн и синхронизируется позже. Почти всё остальное (бэкенд, мобильное приложение, которое по сути является веб-клиентом) требует соединения.",
     "**Community или Enterprise.** Часть функций есть только в Enterprise (например, полные бухгалтерские отчёты, Studio, некоторые локализации, функции мобильного приложения). Закрывать эту разницу сторонними модулями значит повышать риск при каждом обновлении."],
    ["**Ловушка избыточной кастомизации.** Раз изменить можно всё, компании переносят в код свои старые процессы вместо того, чтобы принять стандартные сценарии. За каждое изменение приходится платить снова при каждом обновлении. Практическое правило: настройка раньше Studio, Studio раньше кода, код только там, где он даёт реальную ценность. И всегда в модулях под контролем версий, а не только в базе.",
     "**Глубина локального учёта.** Качество локализаций зависит от страны и редакции. В Германии, например, до старта проекта стоит проверить экспорт в DATEV, процессы по GoBD и декларации НДС. В других странах регламентированная отчётность может быть слабее, чем в специализированном локальном ПО (в СНГ — например, 1С).",
     "**Интеграции и перенос данных.** Импорт справочников без очистки создаёт дубликаты и неправильные остатки. Используйте внешние ID для повторяемых импортов, мигрируйте пробными прогонами, сверяйте итоги. Интеграциям с маркетплейсами, платёжными сервисами и телефонией нужны повторы, идемпотентность и мониторинг, а не блокирующий HTTP-запрос.",
     "**Права доступа и автоматизации.** Неправильные группы и record rules — это проблема и безопасности, и поддержки. Проверяйте их на реальных учётных записях пользователей, а не под админом. Автоматические действия «при сохранении» могут запускать друг друга или ту же запись и зациклиться. Серверные действия с кодом Python выполняются с повышенными правами. И то, и другое должно проходить ревью.",
     "**Копии продакшена.** База stage или тестовая база, восстановленная из продакшена с активными кронами, рассылает настоящие счета, напоминания и вызовы интеграций. Обезвреживание — обязательная часть каждого восстановления."],
    ["**Зависимость от интегратора.** Лицензии дёшевы по сравнению с внедрением и сопровождением, а хороших знатоков Odoo мало. Договоритесь, кто сопровождает свои модули, кто делает обновления и кто следит за серверами.",
     "**Эксплуатация не бесплатна.** Свой хостинг означает бэкапы и тесты восстановления, мониторинг, обновления ОС, PostgreSQL и Odoo, безопасность. Odoo Online (SaaS) снимает эту работу, но не разрешает свои Python-модули. Odoo.sh посередине.",
     "**Сопротивление персонала.** Без обучения по ролям сотрудники не понимают цепочек документов, возвращаются к Excel и делают ошибки, которые потом выглядят как проблемы программы."],
    ["**Отдельный инстанс для cron.** Запустите второй процесс Odoo (контейнер или сервис) на том же коде и базе с `--workers=0 --max-cron-threads=2 --no-http`, а на веб-сервере поставьте `max_cron_threads = 0`. Тогда тяжёлые ночные пересчёты и импорты больше не занимают веб-воркеры, а лимит памяти на контейнере с кронами защищает воркеры пользователей. В реальном случае восемь процессов cron держали по 3,5–3,8 ГБ каждый на веб-сервере.",
     "**Мягкий перезапуск вместо kill.** `SIGHUP` даёт завершиться текущим запросам и перезапускает Odoo с теми же аргументами, перечитывая код и `odoo.conf`. Сессии сохраняются, websockets переподключаются.",
     "**queue_job (OCA) для тяжёлой работы.** Интеграции, массовые рассылки и синхронизации уходят в асинхронную очередь с повторами и каналами, которые ограничивают параллельность. Так они не блокируют HTTP-воркер, пока его не убьёт лимит времени. Runner нужно своё соединение с базой (а с PgBouncer — пул в режиме session)."],
    ["**Бэкапы через pg_dump и rsync, а не через менеджер баз.** Менеджер упаковывает базу и filestore в ZIP внутри Python-воркера. На базах в несколько ГБ он упирается в лимиты памяти и времени и блокирует воркер. `pg_dump -Fc` плюс инкрементная синхронизация filestore (или снимки) работает быстрее и позволяет восстанавливать отдельные таблицы. Менеджер выключите (`list_db = False`).",
     "**Обезвреживайте каждую копию продакшена.** В Odoo 16+ есть `odoo-bin neutralize`: он выключает кроны и почтовые серверы и переводит платёжные сервисы в тестовый режим. Сам `dbfilter` ничего не блокирует, он только выбирает базу. Дополнительно дайте stage SMTP, который не может доставить почту (mail catcher), и свой `web.base.url`.",
     "**PgBouncer в режиме transaction**, когда воркеров много или серверов Odoo несколько. Сотни клиентских соединений делят несколько десятков соединений PostgreSQL. Два исключения требуют режима session: шина Odoo (`LISTEN imbus`) и runner queue_job."],
    ["**click-odoo-update для деплоя.** Он хранит контрольные суммы файлов модулей в базе и запускает `-u` только для модулей с изменённым кодом. Деплой занимает секунды вместо минут, и никто не забудет модуль.",
     "**Сначала измерять, потом настраивать.** Для медленных запросов используйте сам PostgreSQL: `log_min_duration_statement`, `pg_stat_statements` или PoWA. `log_level = debug_sql` пишет в лог каждый запрос и заливает его полностью, поэтому включайте его только на несколько секунд и на stage. `log_db_level` записывает строки лога в таблицу `ir_logging` и для профилирования не подходит. Odoo также пишет в конце строки лога каждого HTTP-запроса число SQL-запросов, время SQL и остальное время.",
     "**py-spy для зависшего воркера.** `py-spy dump --pid <PID>` показывает стек Python работающего процесса без перезапуска. В Docker запускайте py-spy на хосте под root с PID хоста (или дайте контейнеру `SYS_PTRACE`)."],
    ["После деплоя бэкенд белый или без стилей, консоль браузера показывает 404/500 для `/web/assets/...`, а в логе Odoo «Could not get content for /web/assets/…» или `FileNotFoundError`. Бандлы — это вложения: запись лежит в базе, файл — в filestore. Мы видели это много раз, и причины почти всегда одни и те же:",
     ["filestore отсутствует или не сохраняется между перезапусками: том Docker не смонтирован, изменён `data_dir`, базу восстановили без её filestore;",
      "несколько серверов Odoo без общего filestore: сервер A сгенерировал бандл, а сервер B не находит файл;",
      "обновление модуля прервалось во время компиляции assets, или в своём модуле сломан файл SCSS/JS (тогда в логе видна ошибка компиляции, и сначала нужно исправить код);",
      "после обновления CDN или прокси отдаёт старый бандл из кэша."]],
    "Большинство проблем Odoo предсказуемы, а значит, их можно предотвратить. Нужны минимум чистого своего кода, спланированные обновления, проверенные сторонние модули, измеренная база, фоновые задачи отдельно от пользователей и бэкапы, которые действительно восстанавливают на stage. Мы настраиваем и сопровождаем это для компаний в Германии, Австрии и Швейцарии.",
    "Ссылки")
