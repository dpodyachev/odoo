# Статья 18: сколько пользователей тянет один сервер Odoo – воркеры, их разумный максимум, «одновременные» ≠ «все»,
# что упирается первым и как масштабировать дальше. Ссылки на PgBouncer и калькулятор. Все 6 языков.

SCALING = {
    "slug": "odoo-how-many-users-one-server-workers",
    "date": "2026-11-16",
    "tags": ["Odoo", "Performance", "Workers", "Scaling", "Sizing"],
    "code": {
        "formula": ("rules of thumb (Odoo documentation)", """workers (max)        = CPU cores × 2 + 1
concurrent users     ≈ workers × 6
RAM for Odoo         ≈ workers × (0.8 × 150 MB + 0.2 × 1 GB)  ≈ workers × 325 MB
                       + cron threads, gevent process, OS, (PostgreSQL if on the same server)

example: 16 cores  ->  33 workers  ->  ~200 concurrent users  ->  ~11 GB RAM for Odoo"""),
        "conf": ("etc/odoo.conf · 16 cores, 32 GB, PostgreSQL on its own server", """[options]
workers = 33
max_cron_threads = 2
limit_memory_soft = 2147483648      ; 2 GB – worker is recycled after the request
limit_memory_hard = 2684354560      ; 2.5 GB – worker is killed immediately
limit_time_cpu = 600
limit_time_real = 1200
db_maxconn = 16
proxy_mode = True
gevent_port = 8072"""),
        "measure": ("sql · how many users are really online", """-- Odoo 16–18: presence of the web client (updated by the bus, roughly every minute)
SELECT status, count(*) FROM bus_presence
 WHERE last_poll > now() - interval '5 minutes' GROUP BY status;

-- Odoo 19: the model moved to mail
SELECT status, count(*) FROM mail_presence
 WHERE last_poll > now() - interval '5 minutes' GROUP BY status;

-- all internal users with a login (the "total" number)
SELECT count(*) FROM res_users WHERE active AND share = false;

-- how busy are the workers right now (requests in PostgreSQL at this moment)
SELECT count(*) FILTER (WHERE state = 'active') AS active, count(*) AS connections
  FROM pg_stat_activity WHERE datname = current_database();"""),
        "case": ("bash · who uses the RAM: HTTP workers or cron workers?", """# RSS, age (seconds since start) and CPU of all Odoo processes, biggest first
ps -eo rss,etimes,pcpu,args --sort=-rss | grep '[o]doo' | awk '{printf "%6d MB  %8ds  %s%%\\n", $1/1024, $2, $3}' | head -40

# a real production server (32 cores, 62 GB, workers = 25, max_cron_threads = 8):
#   3841 MB  246872s  1.0%     <- 8 processes ~3.5–3.8 GB each, alive since the Odoo restart (2.9 days):
#   ...                            the CRON workers – together ~29 GB
#    358 MB   12687s  1.9%     <- 25 HTTP workers ~260 MB each (recycled every few hours) – together ~6.5 GB
#   ...
# odoo.conf there: limit_memory_soft = 8000000000, limit_memory_hard = 16000000000"""),
        "log": ("bash · request times from the Odoo log", """# werkzeug log line ends with: <query count> <SQL time> <other time>
#   ... "POST /web/dataset/call_kw/sale.order/web_search_read HTTP/1.1" 200 - 42 0.031 0.118
# slowest requests of the day
grep "HTTP/1.1\\" 200" /var/log/odoo/odoo.log | awk '{print $(NF-1)+$NF, $0}' | sort -rn | head -20"""),
    },
    "links": [
        ("Calculator: odoo.conf + postgresql.conf from CPU, RAM, users, servers", "@page:pg-odoo-calculator.html"),
        ("Calculator with sliders", "@page:pg-odoo-calculator-sliders.html"),
        ("Blog: PgBouncer for Odoo", "@blog:pgbouncer-odoo-connection-pooling"),
        ("Blog: PostgreSQL cheat sheet for Odoo admins", "@blog:postgresql-odoo-admin-cheat-sheet"),
        ("Blog: Odoo 19 with a read replica", "@blog:odoo-19-postgresql-read-replica"),
        ("Blog: pgload – load test for PostgreSQL", "@blog:postgresql-load-test-pgload-replica"),
        ("Odoo 17: deploying – worker number and memory", "https://www.odoo.com/documentation/17.0/administration/on_premise/deploy.html"),
    ],
    "t": {},
}

_TBL = {
    "en": [["Server (Odoo only)", "Workers (max)", "Concurrent users", "Users in total (typical)"],
           ["4 cores, 8 GB", "9", "~50", "~250–500"],
           ["8 cores, 16 GB", "17", "~100", "~500–1 000"],
           ["16 cores, 32 GB", "33", "~200", "~1 000–2 000"],
           ["32 cores, 64 GB", "65", "~390", "~2 000–4 000"],
           ["64 cores, 128 GB", "129", "~770", "~4 000–8 000"],
           ["192 cores (largest machines)", "385", "~2 300 in theory", "in practice PostgreSQL limits first"]],
}

SCALING["t"]["en"] = {
    "title": "How many users can one Odoo server handle? Workers, their sensible maximum – and why “concurrent” ≠ “all users”",
    "summary": "How Odoo scales with workers, why the maximum is CPU cores × 2 + 1, what “6 users per worker” really means, how many people that is in total, what breaks first – and how to go beyond one server.",
    "body": [
        ("p", "“We have 500 employees – how big must the server be?” The honest answer starts with a question back: how many of them work in Odoo **at the same moment**? Odoo does not scale with the number of accounts, it scales with the number of requests running in parallel – and those are handled by **workers**."),
        ("note", "Short version: at most CPU cores × 2 + 1 workers per server, about 6 concurrent users per worker. 16 cores ≈ 33 workers ≈ 200 concurrent users ≈ 1 000–2 000 users in total. Beyond that: several Odoo servers, a strong PostgreSQL, PgBouncer."),
        ("h", "How Odoo works with workers"),
        ("ul", [
            "With `workers > 0` Odoo runs in **prefork** mode: a main process starts N worker processes; **each worker handles exactly one HTTP request at a time**.",
            "Separately: a **gevent** process for the websocket (chat, notifications) and the **cron threads** (`max_cron_threads`).",
            "A user is not “in a worker”: between clicks they occupy nothing. A worker is busy only while a request runs – usually 50–500 ms, a big report or import much longer.",
            "If all workers are busy, new requests wait – Odoo feels slow although CPU and RAM may still be free.",
        ]),
        ("h", "The rules of thumb"),
        ("code", "formula"),
        ("ul", [
            "**Why CPU × 2 + 1:** a worker partly waits for PostgreSQL and the network – so a core can serve about two; more workers than that only fight over the CPU.",
            "**Why ~6 users per worker:** a working user sends a request every few seconds and each takes a fraction of a second – six such users rarely hit the same worker at the same moment. With heavy use (POS, warehouse scanners, big reports, eCommerce) fewer.",
            "**RAM:** about 325 MB per worker on average; the limits `limit_memory_soft/hard` are ceilings for peaks, not the average.",
        ]),
        ("h", "“Concurrent” ≠ “all users”"),
        ("p", "Three different numbers are often mixed up:"),
        ("ul", [
            "**Users in total** – accounts with a login (what the licence counts).",
            "**Online users** – logged in, Odoo tab open. At peak typically 30–60 % of the total.",
            "**Concurrent (active) users** – actually clicking, saving, printing in the same minutes. Typically 10–20 % of the total; the “6 per worker” rule refers to these.",
        ]),
        ("p", "So 1 000 employees with an Odoo account are usually 100–200 concurrent users – one good server with 16 cores. Shift work, month-end closing or a sales campaign in the shop can double the peak – plan for the peak, not the average."),
        ("code", "measure"),
        ("h", "What one server can carry"),
        ("table", _TBL["en"]),
        ("p", "If PostgreSQL runs on the same machine, take about a quarter of the cores and up to half of the RAM away from Odoo. Our calculator does that automatically."),
        ("code", "conf"),
        ('h', 'Real case: the memory is eaten by crons, not by users'),
        ('p', 'On a production server with 32 cores and 62 GB, Odoo used 33 GB of RAM – it looked like “too many users”. The process list showed the opposite: 25 HTTP workers needed only ~260 MB each, but 8 cron workers had grown to 3.5–3.8 GB each and had been alive since the last restart – about 29 GB together.'),
        ('code', 'case'),
        ('ul', ['**Cause:** `limit_memory_soft = 8 GB`. A worker is only recycled after exceeding the soft limit; HTTP workers are also recycled by `limit_request`, cron workers practically never – they keep the memory of the largest job they ever ran.', '**Effect:** RAM that could carry 40–60 more HTTP workers is blocked; under memory pressure the OS starts swapping or the OOM killer hits.', '**Fix:** `limit_memory_soft` ~2–3 GB and `limit_memory_hard` ~3–4 GB (big imports/reports into queue_job with their own limits), `max_cron_threads` 2–4 instead of 8. Freed RAM → more HTTP workers.', '**Lesson:** before buying hardware or counting users, look at which processes actually hold the RAM.']),
        ("h", "What breaks first"),
        ("ul", [
            "**Long requests** – reports, exports, imports block a worker for minutes. Move them into queue_job or crons; otherwise 33 workers are effectively 20.",
            "**PostgreSQL** – CPU, disk I/O, locks (`could not serialize access`), too many connections. A strong DB server is the foundation of every large installation.",
            "**RAM** – too many workers for the RAM means swapping or OOM kills; then fewer workers are faster.",
            "**Custom modules** – one slow computed field or an `onchange` with hundreds of queries costs more than any hardware.",
        ]),
        ("code", "log"),
        ("h", "Beyond one server"),
        ("ul", [
            "**First tune:** indexes, slow queries, crons out of working hours, reports into queue_job – often doubles the capacity for free.",
            "**Separate PostgreSQL** on its own server with fast NVMe and enough RAM for the cache.",
            "**Several Odoo servers** behind a load balancer: same odoo.conf, shared filestore (NFS or object storage via fs_attachment), shared sessions (or sticky sessions), crons only on one server.",
            "**PgBouncer** as soon as the connections run into hundreds – but with session pooling for the bus and the queue_job runner.",
            "**Read replica** (Odoo 18+) for read-heavy load – measure, it can also make things slower.",
            "**Load test** before go-live: Locust scenarios with realistic clicks, compare p95 response times.",
        ]),
        ("note", "Try it with your numbers: the calculator turns CPU, RAM, users and number of Odoo servers into odoo.conf and postgresql.conf – and warns when the CPU is not enough, when PostgreSQL becomes the bottleneck and when PgBouncer is due."),
        ("links", "Links"),
    ],
}

_TBL["de"] = [["Server (nur Odoo)", "Worker (max.)", "Gleichzeitige Anwender", "Anwender insgesamt (typisch)"],
    ["4 Kerne, 8 GB", "9", "~50", "~250–500"],
    ["8 Kerne, 16 GB", "17", "~100", "~500–1 000"],
    ["16 Kerne, 32 GB", "33", "~200", "~1 000–2 000"],
    ["32 Kerne, 64 GB", "65", "~390", "~2 000–4 000"],
    ["64 Kerne, 128 GB", "129", "~770", "~4 000–8 000"],
    ["192 Kerne (größte Maschinen)", "385", "~2 300 theoretisch", "in der Praxis begrenzt vorher PostgreSQL"]]

SCALING["t"]["de"] = {
    "title": "Wie viele Anwender schafft ein Odoo-Server? Worker, ihr sinnvolles Maximum – und warum „gleichzeitig“ ≠ „alle Anwender“",
    "summary": "Wie Odoo mit Workern skaliert, warum das Maximum CPU-Kerne × 2 + 1 ist, was „6 Anwender pro Worker“ wirklich bedeutet, wie viele Personen das insgesamt sind, was zuerst bricht – und wie man über einen Server hinauskommt.",
    "body": [
        ("p", "„Wir haben 500 Mitarbeiter – wie groß muss der Server sein?“ Die ehrliche Antwort beginnt mit einer Gegenfrage: Wie viele davon arbeiten **im selben Moment** in Odoo? Odoo skaliert nicht mit der Zahl der Konten, sondern mit der Zahl parallel laufender Anfragen – und die bearbeiten die **Worker**."),
        ("note", "Kurzfassung: höchstens CPU-Kerne × 2 + 1 Worker pro Server, etwa 6 gleichzeitige Anwender pro Worker. 16 Kerne ≈ 33 Worker ≈ 200 gleichzeitige Anwender ≈ 1 000–2 000 Anwender insgesamt. Darüber hinaus: mehrere Odoo-Server, ein starkes PostgreSQL, PgBouncer."),
        ("h", "Wie Odoo mit Workern arbeitet"),
        ("ul", [
            "Mit `workers > 0` läuft Odoo im **Prefork**-Modus: Ein Hauptprozess startet N Worker-Prozesse; **jeder Worker bearbeitet genau eine HTTP-Anfrage gleichzeitig**.",
            "Dazu: ein **Gevent**-Prozess für den Websocket (Chat, Benachrichtigungen) und die **Cron-Threads** (`max_cron_threads`).",
            "Ein Anwender „sitzt“ nicht in einem Worker: Zwischen den Klicks belegt er nichts. Ein Worker ist nur belegt, solange eine Anfrage läuft – meist 50–500 ms, ein großer Bericht oder Import viel länger.",
            "Sind alle Worker belegt, warten neue Anfragen – Odoo wirkt langsam, obwohl CPU und RAM vielleicht noch frei sind.",
        ]),
        ("h", "Die Faustregeln"),
        ("code", "formula"),
        ("ul", [
            "**Warum CPU × 2 + 1:** Ein Worker wartet zum Teil auf PostgreSQL und das Netzwerk – ein Kern kann also etwa zwei bedienen; mehr Worker streiten nur um die CPU.",
            "**Warum ~6 Anwender pro Worker:** Ein arbeitender Anwender schickt alle paar Sekunden eine Anfrage, und jede dauert Sekundenbruchteile – sechs solche Anwender treffen selten im selben Moment auf denselben Worker. Bei schwerer Nutzung (Kasse, Lagerscanner, große Berichte, Onlineshop) weniger.",
            "**RAM:** im Schnitt etwa 325 MB pro Worker; die Grenzen `limit_memory_soft/hard` sind Obergrenzen für Spitzen, nicht der Durchschnitt.",
        ]),
        ("h", "„Gleichzeitig“ ≠ „alle Anwender“"),
        ("p", "Drei verschiedene Zahlen werden oft verwechselt:"),
        ("ul", [
            "**Anwender insgesamt** – Konten mit Login (das, was die Lizenz zählt).",
            "**Online-Anwender** – angemeldet, Odoo-Tab offen. In der Spitze typischerweise 30–60 % der Gesamtzahl.",
            "**Gleichzeitige (aktive) Anwender** – klicken, speichern, drucken tatsächlich in denselben Minuten. Typischerweise 10–20 % der Gesamtzahl; die Regel „6 pro Worker“ bezieht sich auf diese.",
        ]),
        ("p", "1 000 Mitarbeiter mit Odoo-Konto sind also meist 100–200 gleichzeitige Anwender – ein guter Server mit 16 Kernen. Schichtarbeit, Monatsabschluss oder eine Verkaufsaktion im Shop können die Spitze verdoppeln – für die Spitze planen, nicht für den Durchschnitt."),
        ("code", "measure"),
        ("h", "Was ein Server tragen kann"),
        ("table", _TBL["de"]),
        ("p", "Läuft PostgreSQL auf derselben Maschine, gehen etwa ein Viertel der Kerne und bis zur Hälfte des RAM für Odoo ab. Unser Rechner berücksichtigt das automatisch."),
        ("code", "conf"),
        ('h', 'Praxisfall: Den Speicher fressen die Cron-Jobs, nicht die Anwender'),
        ('p', 'Auf einem Produktivserver mit 32 Kernen und 62 GB belegte Odoo 33 GB RAM – es sah nach „zu vielen Anwendern“ aus. Die Prozessliste zeigte das Gegenteil: 25 HTTP-Worker brauchten nur ~260 MB je, aber 8 Cron-Worker waren auf 3,5–3,8 GB je gewachsen und liefen seit dem letzten Neustart – zusammen etwa 29 GB.'),
        ('code', 'case'),
        ('ul', ['**Ursache:** `limit_memory_soft = 8 GB`. Ein Worker wird erst nach Überschreiten des Soft-Limits recycelt; HTTP-Worker zusätzlich über `limit_request`, Cron-Worker praktisch nie – sie behalten den Speicher des größten Jobs, den sie je ausgeführt haben.', '**Folge:** RAM, der 40–60 weitere HTTP-Worker tragen könnte, ist blockiert; bei Speicherdruck swappt das System oder der OOM-Killer schlägt zu.', '**Lösung:** `limit_memory_soft` ~2–3 GB und `limit_memory_hard` ~3–4 GB (große Importe/Berichte in queue_job mit eigenen Grenzen), `max_cron_threads` 2–4 statt 8. Freier RAM → mehr HTTP-Worker.', '**Lehre:** Bevor man Hardware kauft oder Anwender zählt, nachsehen, welche Prozesse den RAM wirklich belegen.']),
        ("h", "Was zuerst bricht"),
        ("ul", [
            "**Lange Anfragen** – Berichte, Exporte, Importe blockieren einen Worker minutenlang. In queue_job oder Cron-Jobs verlagern; sonst sind 33 Worker effektiv 20.",
            "**PostgreSQL** – CPU, Platten-I/O, Sperren (`could not serialize access`), zu viele Verbindungen. Ein starker DB-Server ist die Grundlage jeder großen Installation.",
            "**RAM** – zu viele Worker für den RAM bedeuten Swapping oder OOM-Kills; dann sind weniger Worker schneller.",
            "**Eigene Module** – ein langsames berechnetes Feld oder ein `onchange` mit Hunderten Abfragen kostet mehr als jede Hardware.",
        ]),
        ("code", "log"),
        ("h", "Über einen Server hinaus"),
        ("ul", [
            "**Zuerst optimieren:** Indizes, langsame Abfragen, Cron-Jobs außerhalb der Arbeitszeit, Berichte in queue_job – verdoppelt die Kapazität oft kostenlos.",
            "**Eigener PostgreSQL-Server** mit schnellen NVMe-Platten und genug RAM für den Cache.",
            "**Mehrere Odoo-Server** hinter einem Load Balancer: gleiche odoo.conf, gemeinsamer Filestore (NFS oder Objektspeicher über fs_attachment), gemeinsame Sessions (oder Sticky Sessions), Cron-Jobs nur auf einem Server.",
            "**PgBouncer**, sobald die Verbindungen in die Hunderte gehen – aber mit Session Pooling für den Bus und den queue_job-Runner.",
            "**Read-Replica** (Odoo 18+) für leselastige Last – messen, sie kann auch bremsen.",
            "**Lasttest** vor dem Go-live: Locust-Szenarien mit realistischen Klicks, p95-Antwortzeiten vergleichen.",
        ]),
        ("note", "Mit Ihren Zahlen ausprobieren: Der Rechner macht aus CPU, RAM, Anwendern und Anzahl der Odoo-Server eine odoo.conf und postgresql.conf – und warnt, wenn die CPU nicht reicht, wenn PostgreSQL zum Engpass wird und wann PgBouncer fällig ist."),
        ("links", "Links"),
    ],
}

_TBL["fr"] = [["Serveur (Odoo seul)", "Workers (max.)", "Utilisateurs simultanés", "Utilisateurs au total (typique)"],
    ["4 cœurs, 8 Go", "9", "~50", "~250–500"],
    ["8 cœurs, 16 Go", "17", "~100", "~500–1 000"],
    ["16 cœurs, 32 Go", "33", "~200", "~1 000–2 000"],
    ["32 cœurs, 64 Go", "65", "~390", "~2 000–4 000"],
    ["64 cœurs, 128 Go", "129", "~770", "~4 000–8 000"],
    ["192 cœurs (les plus grosses machines)", "385", "~2 300 en théorie", "en pratique PostgreSQL limite avant"]]

SCALING["t"]["fr"] = {
    "title": "Combien d'utilisateurs un serveur Odoo supporte-t-il ? Les workers, leur maximum raisonnable – et pourquoi « simultanés » ≠ « tous les utilisateurs »",
    "summary": "Comment Odoo monte en charge avec les workers, pourquoi le maximum est cœurs CPU × 2 + 1, ce que « 6 utilisateurs par worker » signifie vraiment, combien de personnes cela fait au total, ce qui casse en premier – et comment dépasser un seul serveur.",
    "body": [
        ("p", "« Nous avons 500 employés – quelle taille de serveur ? » La réponse honnête commence par une question : combien d'entre eux travaillent dans Odoo **au même moment** ? Odoo ne monte pas en charge avec le nombre de comptes, mais avec le nombre de requêtes exécutées en parallèle – et ce sont les **workers** qui les traitent."),
        ("note", "En bref : au plus cœurs CPU × 2 + 1 workers par serveur, environ 6 utilisateurs simultanés par worker. 16 cœurs ≈ 33 workers ≈ 200 utilisateurs simultanés ≈ 1 000–2 000 utilisateurs au total. Au-delà : plusieurs serveurs Odoo, un PostgreSQL puissant, PgBouncer."),
        ("h", "Comment Odoo travaille avec les workers"),
        ("ul", [
            "Avec `workers > 0`, Odoo tourne en mode **prefork** : un processus principal lance N processus workers ; **chaque worker traite exactement une requête HTTP à la fois**.",
            "En plus : un processus **gevent** pour le websocket (chat, notifications) et les **threads cron** (`max_cron_threads`).",
            "Un utilisateur n'est pas « dans un worker » : entre deux clics il n'occupe rien. Un worker n'est occupé que pendant une requête – en général 50–500 ms, beaucoup plus pour un gros rapport ou un import.",
            "Si tous les workers sont occupés, les nouvelles requêtes attendent – Odoo semble lent alors que CPU et RAM sont peut-être encore libres.",
        ]),
        ("h", "Les règles empiriques"),
        ("code", "formula"),
        ("ul", [
            "**Pourquoi CPU × 2 + 1 :** un worker attend en partie PostgreSQL et le réseau – un cœur peut donc en servir environ deux ; davantage de workers se disputent seulement le CPU.",
            "**Pourquoi ~6 utilisateurs par worker :** un utilisateur qui travaille envoie une requête toutes les quelques secondes et chacune dure une fraction de seconde – six utilisateurs de ce type tombent rarement au même instant sur le même worker. Avec un usage lourd (caisse, scanners d'entrepôt, gros rapports, e-commerce), moins.",
            "**RAM :** environ 325 Mo par worker en moyenne ; les limites `limit_memory_soft/hard` sont des plafonds pour les pics, pas la moyenne.",
        ]),
        ("h", "« Simultanés » ≠ « tous les utilisateurs »"),
        ("p", "Trois nombres différents sont souvent confondus :"),
        ("ul", [
            "**Utilisateurs au total** – comptes avec identifiant (ce que compte la licence).",
            "**Utilisateurs en ligne** – connectés, onglet Odoo ouvert. Au pic, en général 30–60 % du total.",
            "**Utilisateurs simultanés (actifs)** – cliquent, enregistrent, impriment réellement dans les mêmes minutes. En général 10–20 % du total ; la règle « 6 par worker » se rapporte à eux.",
        ]),
        ("p", "1 000 employés avec un compte Odoo font donc généralement 100–200 utilisateurs simultanés – un bon serveur à 16 cœurs. Le travail posté, la clôture mensuelle ou une action commerciale dans la boutique peuvent doubler le pic – dimensionner pour le pic, pas pour la moyenne."),
        ("code", "measure"),
        ("h", "Ce qu'un serveur peut porter"),
        ("table", _TBL["fr"]),
        ("p", "Si PostgreSQL tourne sur la même machine, retirer à Odoo environ un quart des cœurs et jusqu'à la moitié de la RAM. Notre calculateur le fait automatiquement."),
        ("code", "conf"),
        ('h', 'Cas réel : la mémoire est mangée par les crons, pas par les utilisateurs'),
        ('p', "Sur un serveur de production à 32 cœurs et 62 Go, Odoo occupait 33 Go de RAM – cela ressemblait à « trop d'utilisateurs ». La liste des processus montrait l'inverse : 25 workers HTTP n'utilisaient que ~260 Mo chacun, mais 8 workers cron avaient grossi jusqu'à 3,5–3,8 Go chacun et tournaient depuis le dernier redémarrage – environ 29 Go au total."),
        ('code', 'case'),
        ('ul', ["**Cause :** `limit_memory_soft = 8 Go`. Un worker n'est recyclé qu'après avoir dépassé la limite souple ; les workers HTTP le sont aussi via `limit_request`, les workers cron pratiquement jamais – ils gardent la mémoire du plus gros job qu'ils aient exécuté.", "**Effet :** une RAM qui pourrait porter 40–60 workers HTTP de plus est bloquée ; sous pression mémoire, le système swappe ou l'OOM killer frappe.", '**Correction :** `limit_memory_soft` ~2–3 Go et `limit_memory_hard` ~3–4 Go (gros imports/rapports dans queue_job avec leurs propres limites), `max_cron_threads` 2–4 au lieu de 8. RAM libérée → plus de workers HTTP.', "**Leçon :** avant d'acheter du matériel ou de compter les utilisateurs, regarder quels processus occupent vraiment la RAM."]),
        ("h", "Ce qui casse en premier"),
        ("ul", [
            "**Les requêtes longues** – rapports, exports, imports bloquent un worker pendant des minutes. Les déplacer dans queue_job ou des crons ; sinon 33 workers en valent effectivement 20.",
            "**PostgreSQL** – CPU, E/S disque, verrous (`could not serialize access`), trop de connexions. Un serveur de base solide est le fondement de toute grande installation.",
            "**La RAM** – trop de workers pour la RAM signifie swap ou processus tués (OOM) ; alors moins de workers vont plus vite.",
            "**Les modules maison** – un champ calculé lent ou un `onchange` avec des centaines de requêtes coûte plus que n'importe quel matériel.",
        ]),
        ("code", "log"),
        ("h", "Au-delà d'un serveur"),
        ("ul", [
            "**D'abord optimiser :** index, requêtes lentes, crons hors des heures de travail, rapports dans queue_job – double souvent la capacité gratuitement.",
            "**PostgreSQL séparé** sur son propre serveur avec des disques NVMe rapides et assez de RAM pour le cache.",
            "**Plusieurs serveurs Odoo** derrière un répartiteur de charge : même odoo.conf, filestore partagé (NFS ou stockage objet via fs_attachment), sessions partagées (ou sessions persistantes), crons sur un seul serveur.",
            "**PgBouncer** dès que les connexions se comptent par centaines – mais avec pooling de session pour le bus et le runner queue_job.",
            "**Réplique en lecture** (Odoo 18+) pour une charge majoritairement en lecture – mesurer, elle peut aussi ralentir.",
            "**Test de charge** avant la mise en production : scénarios Locust avec des clics réalistes, comparer les temps de réponse p95.",
        ]),
        ("note", "Essayez avec vos chiffres : le calculateur transforme CPU, RAM, utilisateurs et nombre de serveurs Odoo en odoo.conf et postgresql.conf – et avertit quand le CPU ne suffit pas, quand PostgreSQL devient le goulot et quand PgBouncer s'impose."),
        ("links", "Liens"),
    ],
}

_TBL["el"] = [["Server (μόνο Odoo)", "Workers (μέγ.)", "Ταυτόχρονοι χρήστες", "Χρήστες συνολικά (τυπικά)"],
    ["4 πυρήνες, 8 GB", "9", "~50", "~250–500"],
    ["8 πυρήνες, 16 GB", "17", "~100", "~500–1 000"],
    ["16 πυρήνες, 32 GB", "33", "~200", "~1 000–2 000"],
    ["32 πυρήνες, 64 GB", "65", "~390", "~2 000–4 000"],
    ["64 πυρήνες, 128 GB", "129", "~770", "~4 000–8 000"],
    ["192 πυρήνες (τα μεγαλύτερα μηχανήματα)", "385", "~2 300 θεωρητικά", "στην πράξη περιορίζει πρώτα η PostgreSQL"]]

SCALING["t"]["el"] = {
    "title": "Πόσους χρήστες αντέχει ένας server Odoo; Workers, το λογικό τους μέγιστο – και γιατί «ταυτόχρονοι» ≠ «όλοι οι χρήστες»",
    "summary": "Πώς κλιμακώνεται το Odoo με workers, γιατί το μέγιστο είναι πυρήνες CPU × 2 + 1, τι σημαίνει πραγματικά «6 χρήστες ανά worker», πόσα άτομα είναι αυτό συνολικά, τι σπάει πρώτο – και πώς πάτε πέρα από έναν server.",
    "body": [
        ("p", "«Έχουμε 500 υπαλλήλους – πόσο μεγάλος πρέπει να είναι ο server;» Η ειλικρινής απάντηση ξεκινά με μια ερώτηση: πόσοι από αυτούς δουλεύουν στο Odoo **την ίδια στιγμή**; Το Odoo δεν κλιμακώνεται με τον αριθμό των λογαριασμών αλλά με τον αριθμό των αιτημάτων που τρέχουν παράλληλα – και αυτά τα χειρίζονται οι **workers**."),
        ("note", "Συνοπτικά: το πολύ πυρήνες CPU × 2 + 1 workers ανά server, περίπου 6 ταυτόχρονοι χρήστες ανά worker. 16 πυρήνες ≈ 33 workers ≈ 200 ταυτόχρονοι χρήστες ≈ 1 000–2 000 χρήστες συνολικά. Πέρα από αυτό: πολλοί servers Odoo, ισχυρή PostgreSQL, PgBouncer."),
        ("h", "Πώς δουλεύει το Odoo με workers"),
        ("ul", [
            "Με `workers > 0` το Odoo τρέχει σε λειτουργία **prefork**: μια κύρια διεργασία ξεκινά N διεργασίες worker· **κάθε worker χειρίζεται ακριβώς ένα αίτημα HTTP τη φορά**.",
            "Επιπλέον: μια διεργασία **gevent** για το websocket (chat, ειδοποιήσεις) και τα **νήματα cron** (`max_cron_threads`).",
            "Ένας χρήστης δεν «κάθεται» σε έναν worker: ανάμεσα στα κλικ δεν καταλαμβάνει τίποτα. Ένας worker είναι απασχολημένος μόνο όσο τρέχει ένα αίτημα – συνήθως 50–500 ms, μια μεγάλη αναφορά ή εισαγωγή πολύ περισσότερο.",
            "Αν όλοι οι workers είναι απασχολημένοι, τα νέα αιτήματα περιμένουν – το Odoo φαίνεται αργό ενώ CPU και RAM μπορεί να είναι ακόμα ελεύθερα.",
        ]),
        ("h", "Οι εμπειρικοί κανόνες"),
        ("code", "formula"),
        ("ul", [
            "**Γιατί CPU × 2 + 1:** ένας worker εν μέρει περιμένει την PostgreSQL και το δίκτυο – ένας πυρήνας εξυπηρετεί λοιπόν περίπου δύο· περισσότεροι workers απλώς τσακώνονται για τη CPU.",
            "**Γιατί ~6 χρήστες ανά worker:** ένας χρήστης που δουλεύει στέλνει ένα αίτημα κάθε λίγα δευτερόλεπτα και καθένα διαρκεί κλάσμα του δευτερολέπτου – έξι τέτοιοι χρήστες σπάνια πέφτουν την ίδια στιγμή στον ίδιο worker. Με βαριά χρήση (POS, σαρωτές αποθήκης, μεγάλες αναφορές, eShop) λιγότεροι.",
            "**RAM:** κατά μέσο όρο περίπου 325 MB ανά worker· τα όρια `limit_memory_soft/hard` είναι ανώτατα όρια για αιχμές, όχι ο μέσος όρος.",
        ]),
        ("h", "«Ταυτόχρονοι» ≠ «όλοι οι χρήστες»"),
        ("p", "Τρεις διαφορετικοί αριθμοί συχνά μπερδεύονται:"),
        ("ul", [
            "**Χρήστες συνολικά** – λογαριασμοί με σύνδεση (αυτό που μετρά η άδεια).",
            "**Συνδεδεμένοι χρήστες** – συνδεδεμένοι, με ανοιχτή καρτέλα Odoo. Στην αιχμή συνήθως 30–60 % του συνόλου.",
            "**Ταυτόχρονοι (ενεργοί) χρήστες** – πράγματι κάνουν κλικ, αποθηκεύουν, τυπώνουν στα ίδια λεπτά. Συνήθως 10–20 % του συνόλου· σε αυτούς αναφέρεται ο κανόνας «6 ανά worker».",
        ]),
        ("p", "Άρα 1 000 υπάλληλοι με λογαριασμό Odoo είναι συνήθως 100–200 ταυτόχρονοι χρήστες – ένας καλός server με 16 πυρήνες. Βάρδιες, κλείσιμο μήνα ή μια προώθηση στο eShop μπορούν να διπλασιάσουν την αιχμή – σχεδιάστε για την αιχμή, όχι για τον μέσο όρο."),
        ("code", "measure"),
        ("h", "Τι αντέχει ένας server"),
        ("table", _TBL["el"]),
        ("p", "Αν η PostgreSQL τρέχει στο ίδιο μηχάνημα, αφαιρέστε από το Odoo περίπου το ένα τέταρτο των πυρήνων και έως τη μισή RAM. Ο υπολογιστής μας το κάνει αυτόματα."),
        ("code", "conf"),
        ('h', 'Πραγματικό παράδειγμα: τη μνήμη την τρώνε τα cron, όχι οι χρήστες'),
        ('p', 'Σε server παραγωγής με 32 πυρήνες και 62 GB το Odoo καταλάμβανε 33 GB RAM – έμοιαζε με «πάρα πολλούς χρήστες». Η λίστα διεργασιών έδειξε το αντίθετο: 25 HTTP workers χρειάζονταν μόνο ~260 MB ο καθένας, ενώ 8 cron workers είχαν φουσκώσει στα 3,5–3,8 GB ο καθένας και έτρεχαν από την τελευταία επανεκκίνηση – περίπου 29 GB συνολικά.'),
        ('code', 'case'),
        ('ul', ['**Αιτία:** `limit_memory_soft = 8 GB`. Ένας worker ανακυκλώνεται μόνο αφού ξεπεράσει το soft όριο· οι HTTP workers ανακυκλώνονται και μέσω `limit_request`, οι cron workers πρακτικά ποτέ – κρατούν τη μνήμη της μεγαλύτερης εργασίας που έτρεξαν ποτέ.', '**Συνέπεια:** RAM που θα μπορούσε να σηκώσει 40–60 επιπλέον HTTP workers είναι δεσμευμένη· υπό πίεση μνήμης το σύστημα κάνει swap ή χτυπά ο OOM killer.', '**Λύση:** `limit_memory_soft` ~2–3 GB και `limit_memory_hard` ~3–4 GB (μεγάλες εισαγωγές/αναφορές σε queue_job με δικά τους όρια), `max_cron_threads` 2–4 αντί για 8. Ελεύθερη RAM → περισσότεροι HTTP workers.', '**Δίδαγμα:** πριν αγοράσετε hardware ή μετρήσετε χρήστες, δείτε ποιες διεργασίες πραγματικά κρατούν τη RAM.']),
        ("h", "Τι σπάει πρώτο"),
        ("ul", [
            "**Μακριά αιτήματα** – αναφορές, εξαγωγές, εισαγωγές μπλοκάρουν έναν worker για λεπτά. Μεταφέρετέ τα σε queue_job ή cron· αλλιώς 33 workers είναι στην πράξη 20.",
            "**PostgreSQL** – CPU, I/O δίσκου, κλειδώματα (`could not serialize access`), πάρα πολλές συνδέσεις. Ένας ισχυρός server βάσης είναι το θεμέλιο κάθε μεγάλης εγκατάστασης.",
            "**RAM** – πάρα πολλοί workers για τη RAM σημαίνουν swap ή OOM kills· τότε λιγότεροι workers είναι ταχύτεροι.",
            "**Δικά σας modules** – ένα αργό υπολογιζόμενο πεδίο ή ένα `onchange` με εκατοντάδες ερωτήματα κοστίζει περισσότερο από οποιοδήποτε hardware.",
        ]),
        ("code", "log"),
        ("h", "Πέρα από έναν server"),
        ("ul", [
            "**Πρώτα βελτιστοποίηση:** indexes, αργά ερωτήματα, cron εκτός ωραρίου, αναφορές σε queue_job – συχνά διπλασιάζει τη χωρητικότητα δωρεάν.",
            "**Ξεχωριστή PostgreSQL** σε δικό της server με γρήγορους δίσκους NVMe και αρκετή RAM για cache.",
            "**Πολλοί servers Odoo** πίσω από load balancer: ίδιο odoo.conf, κοινό filestore (NFS ή object storage μέσω fs_attachment), κοινές συνεδρίες (ή sticky sessions), cron μόνο σε έναν server.",
            "**PgBouncer** μόλις οι συνδέσεις φτάσουν τις εκατοντάδες – αλλά με session pooling για το bus και τον runner του queue_job.",
            "**Read replica** (Odoo 18+) για φορτίο κυρίως ανάγνωσης – μετρήστε, μπορεί και να επιβραδύνει.",
            "**Δοκιμή φόρτου** πριν το go-live: σενάρια Locust με ρεαλιστικά κλικ, σύγκριση χρόνων απόκρισης p95.",
        ]),
        ("note", "Δοκιμάστε με τους δικούς σας αριθμούς: ο υπολογιστής μετατρέπει CPU, RAM, χρήστες και αριθμό servers Odoo σε odoo.conf και postgresql.conf – και προειδοποιεί όταν η CPU δεν φτάνει, όταν η PostgreSQL γίνεται στενωπός και πότε χρειάζεται PgBouncer."),
        ("links", "Σύνδεσμοι"),
    ],
}

_TBL["uk"] = [["Сервер (лише Odoo)", "Воркерів (макс.)", "Одночасних користувачів", "Користувачів загалом (типово)"],
    ["4 ядра, 8 ГБ", "9", "~50", "~250–500"],
    ["8 ядер, 16 ГБ", "17", "~100", "~500–1 000"],
    ["16 ядер, 32 ГБ", "33", "~200", "~1 000–2 000"],
    ["32 ядра, 64 ГБ", "65", "~390", "~2 000–4 000"],
    ["64 ядра, 128 ГБ", "129", "~770", "~4 000–8 000"],
    ["192 ядра (найбільші машини)", "385", "~2 300 теоретично", "на практиці раніше впреться PostgreSQL"]]

SCALING["t"]["uk"] = {
    "title": "Скільки користувачів витримає один сервер Odoo? Воркери, їхній розумний максимум і чому «одночасні» ≠ «усі користувачі»",
    "summary": "Як Odoo масштабується воркерами, чому максимум — ядра CPU × 2 + 1, що насправді означає «6 користувачів на воркер», скільки це людей загалом, що ламається першим і як вийти за межі одного сервера.",
    "body": [
        ("p", "«У нас 500 співробітників, яким має бути сервер?» Чесна відповідь починається із зустрічного питання: скільки з них працюють в Odoo **в один і той самий момент**? Odoo масштабується не за кількістю облікових записів, а за кількістю запитів, що виконуються паралельно, а обробляють їх **воркери**."),
        ("note", "Коротко: не більше ніж ядра CPU × 2 + 1 воркерів на сервер, приблизно 6 одночасних користувачів на воркер. 16 ядер ≈ 33 воркери ≈ 200 одночасних користувачів ≈ 1 000–2 000 користувачів загалом. Далі — кілька серверів Odoo, потужний PostgreSQL і PgBouncer."),
        ("h", "Як Odoo працює з воркерами"),
        ("ul", [
            "Із `workers > 0` Odoo працює в режимі **prefork**: головний процес запускає N процесів-воркерів, і **кожен воркер обробляє рівно один HTTP-запит за раз**.",
            "Окремо є процес **gevent** для websocket (чат, сповіщення) і **потоки cron** (`max_cron_threads`).",
            "Користувач не «сидить» у воркері: між кліками він нічого не займає. Воркер зайнятий лише, поки виконується запит: зазвичай 50–500 мс, а великий звіт чи імпорт — значно довше.",
            "Якщо всі воркери зайняті, нові запити чекають. Odoo здається повільним, хоча CPU і RAM, можливо, ще вільні.",
        ]),
        ("h", "Емпіричні правила"),
        ("code", "formula"),
        ("ul", [
            "**Чому CPU × 2 + 1:** частину часу воркер чекає на PostgreSQL і мережу, тож одне ядро може обслуговувати приблизно два воркери. Більша кількість воркерів лише конкурує за CPU.",
            "**Чому ~6 користувачів на воркер:** користувач, який працює, надсилає запит раз на кілька секунд, і кожен триває частку секунди, тож шість таких користувачів рідко потрапляють на той самий воркер одночасно. При важкому використанні (POS, складські сканери, великі звіти, інтернет-магазин) їх менше.",
            "**RAM:** у середньому близько 325 МБ на воркер. Ліміти `limit_memory_soft/hard` — це стеля для пікових навантажень, а не середнє.",
        ]),
        ("h", "«Одночасні» ≠ «усі користувачі»"),
        ("p", "Часто плутають три різні числа:"),
        ("ul", [
            "**Користувачі загалом** — облікові записи з логіном (саме їх рахує ліцензія).",
            "**Користувачі онлайн** — увійшли в систему, вкладка Odoo відкрита. У пік зазвичай 30–60 % від загальної кількості.",
            "**Одночасні (активні) користувачі** — справді клікають, зберігають, друкують у ті самі хвилини. Зазвичай 10–20 % від загальної кількості, і правило «6 на воркер» стосується саме їх.",
        ]),
        ("p", "Тож 1 000 співробітників з обліковим записом в Odoo — це зазвичай 100–200 одночасних користувачів, тобто один добрий сервер на 16 ядер. Змінна робота, закриття місяця чи акція в магазині можуть подвоїти пік, тому плануйте під пік, а не під середнє."),
        ("code", "measure"),
        ("h", "Що витримає один сервер"),
        ("table", _TBL["uk"]),
        ("p", "Якщо PostgreSQL працює на тій самій машині, заберіть в Odoo приблизно чверть ядер і до половини RAM. Наш калькулятор робить це автоматично."),
        ("code", "conf"),
        ('h', "Реальний випадок: пам'ять з'їдають крони, а не користувачі"),
        ('p', 'На продуктивному сервері з 32 ядрами й 62 ГБ Odoo займав 33 ГБ RAM, і це скидалося на «забагато користувачів». Список процесів показав протилежне: 25 HTTP-воркерів займали лише по ~260 МБ, а 8 cron-воркерів розрослися до 3,5–3,8 ГБ кожен і працювали з моменту останнього перезапуску. Разом це близько 29 ГБ.'),
        ('code', 'case'),
        ('ul', ["**Причина:** `limit_memory_soft = 8 GB`. Воркер перезапускається лише після перевищення м'якого ліміту. HTTP-воркери перезапускаються ще й за `limit_request`, а cron-воркери практично ніколи: вони тримають пам'ять найбільшого завдання, яке колись виконували.", "**Наслідок:** заблоковано RAM, якої вистачило б ще на 40–60 HTTP-воркерів. Коли пам'яті бракує, система йде у своп або спрацьовує OOM killer.", '**Що зробити:** `limit_memory_soft` ~2–3 ГБ і `limit_memory_hard` ~3–4 ГБ (великі імпорти й звіти — у queue_job із власними лімітами), `max_cron_threads` 2–4 замість 8. Звільнена RAM піде на додаткових HTTP-воркерів.', '**Висновок:** перш ніж купувати залізо чи рахувати користувачів, подивіться, які процеси насправді тримають RAM.']),
        ("h", "Що ламається першим"),
        ("ul", [
            "**Довгі запити:** звіти, експорти, імпорти займають воркер на хвилини. Винесіть їх у queue_job або крони, інакше 33 воркери фактично працюють як 20.",
            "**PostgreSQL:** CPU, дисковий I/O, блокування (`could not serialize access`), забагато з'єднань. Потужний сервер БД — основа будь-якої великої інсталяції.",
            "**RAM:** якщо воркерів забагато для наявної RAM, починається своп або процеси вбиває OOM, і тоді менша кількість воркерів працює швидше.",
            "**Власні модулі:** одне повільне обчислюване поле чи `onchange` із сотнями запитів коштує більше, ніж будь-яке залізо.",
        ]),
        ("code", "log"),
        ("h", "Більше ніж один сервер"),
        ("ul", [
            "**Спершу оптимізація:** індекси, повільні запити, крони поза робочим часом, звіти в queue_job. Часто це безкоштовно подвоює ємність.",
            "**Окремий сервер PostgreSQL** зі швидкими NVMe-дисками й достатнім обсягом RAM для кешу.",
            "**Кілька серверів Odoo** за балансувальником: однаковий odoo.conf, спільний filestore (NFS або об'єктне сховище через fs_attachment), спільні сесії (або sticky sessions), крони лише на одному сервері.",
            "**PgBouncer**, щойно з'єднань стає кілька сотень, але з session pooling для шини й раннера queue_job.",
            "**Read-репліка** (Odoo 18+) для навантаження переважно на читання. Вимірюйте, бо вона може й сповільнити роботу.",
            "**Навантажувальний тест** перед запуском: сценарії Locust з реалістичними кліками й порівняння часу відповіді p95.",
        ]),
        ("note", "Спробуйте зі своїми цифрами: калькулятор за CPU, RAM, кількістю користувачів і серверів Odoo видає odoo.conf і postgresql.conf, а також попереджає, коли не вистачає CPU, коли вузьким місцем стає PostgreSQL і коли час ставити PgBouncer."),
        ("links", "Посилання"),
    ],
}

_TBL["ru"] = [["Сервер (только Odoo)", "Воркеров (макс.)", "Одновременных пользователей", "Пользователей всего (типично)"],
    ["4 ядра, 8 ГБ", "9", "~50", "~250–500"],
    ["8 ядер, 16 ГБ", "17", "~100", "~500–1 000"],
    ["16 ядер, 32 ГБ", "33", "~200", "~1 000–2 000"],
    ["32 ядра, 64 ГБ", "65", "~390", "~2 000–4 000"],
    ["64 ядра, 128 ГБ", "129", "~770", "~4 000–8 000"],
    ["192 ядра (самые большие машины)", "385", "~2 300 теоретически", "на практике раньше упрётся PostgreSQL"]]

SCALING["t"]["ru"] = {
    "title": "Сколько пользователей выдержит один сервер Odoo? Воркеры, их разумный максимум и почему «одновременные» ≠ «все пользователи»",
    "summary": "Как Odoo масштабируется воркерами, почему максимум — ядра CPU × 2 + 1, что на самом деле значит «6 пользователей на воркер», сколько это людей всего, что ломается первым и как выйти за пределы одного сервера.",
    "body": [
        ("p", "«У нас 500 сотрудников, каким должен быть сервер?» Честный ответ начинается со встречного вопроса: сколько из них работают в Odoo **в один и тот же момент**? Odoo масштабируется не по числу учётных записей, а по числу запросов, выполняемых параллельно, а обрабатывают их **воркеры**."),
        ("note", "Коротко: не больше чем ядра CPU × 2 + 1 воркеров на сервер, примерно 6 одновременных пользователей на воркер. 16 ядер ≈ 33 воркера ≈ 200 одновременных пользователей ≈ 1 000–2 000 пользователей всего. Дальше — несколько серверов Odoo, мощный PostgreSQL и PgBouncer."),
        ("h", "Как Odoo работает с воркерами"),
        ("ul", [
            "При `workers > 0` Odoo работает в режиме **prefork**: главный процесс запускает N процессов-воркеров, и **каждый воркер обрабатывает ровно один HTTP-запрос за раз**.",
            "Отдельно есть процесс **gevent** для websocket (чат, уведомления) и **потоки cron** (`max_cron_threads`).",
            "Пользователь не «сидит» в воркере: между кликами он ничего не занимает. Воркер занят, только пока выполняется запрос: обычно 50–500 мс, а большой отчёт или импорт — гораздо дольше.",
            "Если все воркеры заняты, новые запросы ждут. Odoo кажется медленным, хотя CPU и RAM, возможно, ещё свободны.",
        ]),
        ("h", "Эмпирические правила"),
        ("code", "formula"),
        ("ul", [
            "**Почему CPU × 2 + 1:** часть времени воркер ждёт PostgreSQL и сеть, поэтому одно ядро может обслуживать примерно два воркера. Большее число воркеров только конкурирует за CPU.",
            "**Почему ~6 пользователей на воркер:** работающий пользователь отправляет запрос раз в несколько секунд, и каждый длится долю секунды, поэтому шесть таких пользователей редко попадают на один воркер одновременно. При тяжёлом использовании (POS, складские сканеры, большие отчёты, интернет-магазин) их меньше.",
            "**RAM:** в среднем около 325 МБ на воркер. Лимиты `limit_memory_soft/hard` — это потолок для пиковых нагрузок, а не среднее.",
        ]),
        ("h", "«Одновременные» ≠ «все пользователи»"),
        ("p", "Часто путают три разных числа:"),
        ("ul", [
            "**Пользователи всего** — учётные записи с логином (именно их считает лицензия).",
            "**Пользователи онлайн** — вошли в систему, вкладка Odoo открыта. В пик обычно 30–60 % от общего числа.",
            "**Одновременные (активные) пользователи** — действительно кликают, сохраняют, печатают в одни и те же минуты. Обычно 10–20 % от общего числа, и правило «6 на воркер» относится именно к ним.",
        ]),
        ("p", "Поэтому 1 000 сотрудников с учётной записью в Odoo — это обычно 100–200 одновременных пользователей, то есть один хороший сервер на 16 ядер. Сменная работа, закрытие месяца или акция в магазине могут удвоить пик, поэтому планируйте под пик, а не под среднее."),
        ("code", "measure"),
        ("h", "Что выдержит один сервер"),
        ("table", _TBL["ru"]),
        ("p", "Если PostgreSQL работает на той же машине, заберите у Odoo примерно четверть ядер и до половины RAM. Наш калькулятор делает это автоматически."),
        ("code", "conf"),
        ('h', 'Реальный случай: память съедают кроны, а не пользователи'),
        ('p', 'На продакшен-сервере с 32 ядрами и 62 ГБ Odoo занимал 33 ГБ RAM, и это было похоже на «слишком много пользователей». Список процессов показал обратное: 25 HTTP-воркеров занимали всего по ~260 МБ, а 8 cron-воркеров разрослись до 3,5–3,8 ГБ каждый и работали с момента последнего перезапуска. Вместе это около 29 ГБ.'),
        ('code', 'case'),
        ('ul', ['**Причина:** `limit_memory_soft = 8 GB`. Воркер перезапускается только после превышения мягкого лимита. HTTP-воркеры перезапускаются ещё и по `limit_request`, а cron-воркеры практически никогда: они держат память самого большого задания, которое когда-либо выполняли.', '**Последствие:** заблокирована RAM, которой хватило бы ещё на 40–60 HTTP-воркеров. Когда памяти не хватает, система уходит в своп или срабатывает OOM killer.', '**Что сделать:** `limit_memory_soft` ~2–3 ГБ и `limit_memory_hard` ~3–4 ГБ (большие импорты и отчёты — в queue_job со своими лимитами), `max_cron_threads` 2–4 вместо 8. Освободившаяся RAM пойдёт на дополнительных HTTP-воркеров.', '**Вывод:** прежде чем покупать железо или считать пользователей, посмотрите, какие процессы на самом деле держат RAM.']),
        ("h", "Что ломается первым"),
        ("ul", [
            "**Долгие запросы:** отчёты, экспорты, импорты занимают воркер на минуты. Вынесите их в queue_job или кроны, иначе 33 воркера фактически работают как 20.",
            "**PostgreSQL:** CPU, дисковый I/O, блокировки (`could not serialize access`), слишком много соединений. Мощный сервер БД — основа любой большой инсталляции.",
            "**RAM:** если воркеров слишком много для имеющейся RAM, начинается своп или процессы убивает OOM, и тогда меньшее число воркеров работает быстрее.",
            "**Свои модули:** одно медленное вычисляемое поле или `onchange` с сотнями запросов стоит дороже любого железа.",
        ]),
        ("code", "log"),
        ("h", "Больше одного сервера"),
        ("ul", [
            "**Сначала оптимизация:** индексы, медленные запросы, кроны вне рабочего времени, отчёты в queue_job. Часто это бесплатно удваивает ёмкость.",
            "**Отдельный сервер PostgreSQL** с быстрыми NVMe-дисками и достаточным объёмом RAM для кеша.",
            "**Несколько серверов Odoo** за балансировщиком: одинаковый odoo.conf, общий filestore (NFS или объектное хранилище через fs_attachment), общие сессии (или sticky sessions), кроны только на одном сервере.",
            "**PgBouncer**, как только соединений становится несколько сотен, но с session pooling для шины и раннера queue_job.",
            "**Read-реплика** (Odoo 18+) для нагрузки преимущественно на чтение. Измеряйте, потому что она может и замедлить работу.",
            "**Нагрузочный тест** перед запуском: сценарии Locust с реалистичными кликами и сравнение времени ответа p95.",
        ]),
        ("note", "Попробуйте со своими цифрами: калькулятор по CPU, RAM, числу пользователей и серверов Odoo выдаёт odoo.conf и postgresql.conf, а также предупреждает, когда не хватает CPU, когда узким местом становится PostgreSQL и когда пора ставить PgBouncer."),
        ("links", "Ссылки"),
    ],
}
