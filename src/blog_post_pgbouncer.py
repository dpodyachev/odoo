# Статья 17: PgBouncer для Odoo – transaction pooling для воркеров, session для шины (LISTEN imbus в БД postgres) и queue_job. Все 6 языков.

PGBOUNCER = {
    "slug": "pgbouncer-odoo-connection-pooling",
    "date": "2026-11-16",
    "tags": ["PgBouncer", "PostgreSQL", "Odoo", "Performance", "queue_job"],
    "code": {
        "ini": ("/etc/pgbouncer/pgbouncer.ini", """[databases]
; Odoo databases: one server connection per TRANSACTION
mydb     = host=127.0.0.1 port=5432 pool_mode=transaction
; Odoo bus: LISTEN imbus runs in the database "postgres" – needs a SESSION
postgres = host=127.0.0.1 port=5432 pool_mode=session pool_size=10
; everything else (database manager, new databases)
*        = host=127.0.0.1 port=5432

[pgbouncer]
listen_addr = 0.0.0.0              ; or the private IP only
listen_port = 6432
auth_type = scram-sha-256
auth_file = /etc/pgbouncer/userlist.txt
pool_mode = transaction            ; default for entries without pool_mode
max_client_conn = 2000             ; Odoo side: cheap, can be high
default_pool_size = 40             ; real PostgreSQL connections per database+user
min_pool_size = 5
reserve_pool_size = 10
reserve_pool_timeout = 3
max_db_connections = 150           ; hard cap per database towards PostgreSQL
server_idle_timeout = 600
query_wait_timeout = 120           ; client waits max. 2 min for a free server connection
admin_users = pgbouncer_admin
stats_users = pgbouncer_admin
logfile = /var/log/postgresql/pgbouncer.log"""),
        "auth": ("bash · users for PgBouncer (no plain passwords)", """sudo apt install pgbouncer           # Debian/Ubuntu; also available as a container image

# copy the SCRAM hash of the role from PostgreSQL into userlist.txt (format: "user" "hash")
sudo -u postgres psql -Atc "SELECT '\\"' || rolname || '\\" \\"' || rolpassword || '\\"' FROM pg_authid WHERE rolname IN ('odoo','pgbouncer_admin')" \\
  | sudo tee /etc/pgbouncer/userlist.txt >/dev/null
sudo chown postgres:postgres /etc/pgbouncer/userlist.txt && sudo chmod 600 /etc/pgbouncer/userlist.txt
sudo systemctl restart pgbouncer

# alternative without a file: auth_user + auth_query (PgBouncer asks PostgreSQL for the hash)"""),
        "odoo": ("etc/odoo.conf", """[options]
db_host = 10.0.0.10        ; host of PgBouncer (often the DB server itself)
db_port = 6432             ; PgBouncer instead of 5432
db_maxconn = 16            ; per Odoo process – client connections to PgBouncer are cheap

[queue_job]
; the job runner uses LISTEN queue_job and a session advisory lock -> NOT via transaction pooling
jobrunner_db_host = 10.0.0.10
jobrunner_db_port = 5432   ; directly to PostgreSQL (or a PgBouncer entry with pool_mode=session)"""),
        "show": ("psql · look into PgBouncer", """psql -h 10.0.0.10 -p 6432 -U pgbouncer_admin pgbouncer

SHOW POOLS;     -- per database/user: cl_active, cl_waiting, sv_active, sv_idle, maxwait
SHOW STATS;     -- queries/transactions per second, average query and wait time
SHOW CLIENTS;   -- who is connected (Odoo processes)
SHOW SERVERS;   -- real connections to PostgreSQL
SHOW CONFIG;    -- effective settings
RELOAD;         -- re-read pgbouncer.ini without dropping connections
PAUSE mydb; RESUME mydb;   -- e.g. around a restore or DROP DATABASE
KILL mydb;                  -- drop all connections of a database"""),
        "check": ("bash · is the bus still working?", """# the Odoo log after the start must show the bus listening:
grep "listen imbus" /var/log/odoo/odoo.log        # "Bus.loop listen imbus on db postgres"

# in PostgreSQL: the LISTEN connection is a long-lived session to the database postgres
psql -U postgres -c "SELECT pid, datname, application_name, state, backend_start
                     FROM pg_stat_activity WHERE datname = 'postgres' AND query ILIKE 'listen%';\""""),
    },
    "links": [
        ("PgBouncer: configuration", "https://www.pgbouncer.org/config.html"),
        ("PgBouncer: pooling modes and features", "https://www.pgbouncer.org/features.html"),
        ("Odoo 17 source: bus (LISTEN imbus on db postgres)", "https://github.com/odoo/odoo/blob/17.0/addons/bus/models/bus.py"),
        ("OCA queue_job: jobrunner_db_host / jobrunner_db_port", "https://github.com/OCA/queue/tree/17.0/queue_job"),
        ("PostgreSQL/Odoo config calculator (this site)", "@page:pg-odoo-calculator.html"),
        ("Blog: PostgreSQL cheat sheet for Odoo admins", "@blog:postgresql-odoo-admin-cheat-sheet"),
        ("Blog: Odoo 19 with a read replica", "@blog:odoo-19-postgresql-read-replica"),
    ],
    "t": {},
}

_SIZE = {
    "en": [["Value", "Rule of thumb", "Why"],
           ["`max_client_conn`", "Odoo processes × `db_maxconn` (+ reserve)", "client connections are cheap in PgBouncer"],
           ["`default_pool_size`", "≈ 2–4 × CPU cores of the DB server", "that many transactions run in PostgreSQL at the same time"],
           ["`max_db_connections`", "below PostgreSQL `max_connections` minus reserve", "PostgreSQL never sees more"],
           ["PostgreSQL `max_connections`", "sum of all pools + session pools + admin reserve", "now small (100–300) instead of thousands"],
           ["`query_wait_timeout`", "60–120 s", "otherwise clients wait forever when the pool is exhausted"]],
}

PGBOUNCER["t"]["en"] = {
    "title": "PgBouncer for Odoo: transaction pooling without breaking the bus and queue_job",
    "summary": "Why many Odoo workers need a connection pooler, why transaction pooling breaks Odoo's live notifications and OCA queue_job if you do it naively, and a working pgbouncer.ini with session pooling for the database postgres – plus sizing, monitoring and troubleshooting.",
    "body": [
        ("p", "With several Odoo servers or hundreds of workers the number of database connections explodes: every Odoo process keeps its own pool of up to `db_maxconn` connections. PostgreSQL pays for every connection with a process and RAM – and around a few hundred active connections it slows down noticeably. PgBouncer sits in between: Odoo opens as many cheap client connections as it likes, PostgreSQL only sees a small pool."),
        ("note", "Short version: Odoo's databases in `pool_mode = transaction`, the database `postgres` in `pool_mode = session` (the Odoo bus runs `LISTEN imbus` there), and the OCA queue_job runner directly to PostgreSQL via `jobrunner_db_host/port`. Do it differently and chat, notifications and job processing silently stop working."),
        ("h", "Pooling modes – and what Odoo needs"),
        ("ul", [
            "**session**: a server connection belongs to the client until it disconnects. Safe, but saves almost nothing with Odoo's long-lived connections.",
            "**transaction**: a server connection only for the duration of one transaction. This is where the gain is: hundreds of idle Odoo connections share a few dozen real ones.",
            "**statement**: no multi-statement transactions – unusable for Odoo.",
            "Odoo's normal requests work in transaction mode: every request is a transaction, psycopg2 sends the isolation level with `BEGIN`, Odoo uses no server-side prepared statements.",
        ]),
        ("h", "The two traps"),
        ("ul", [
            "**Odoo bus (live chat, notifications, Discuss):** the gevent process opens a connection to the database **postgres** and runs `LISTEN imbus` (source: `addons/bus/models/bus.py`). `LISTEN` only works in a session – in transaction mode the notifications get lost.",
            "**OCA queue_job:** the job runner runs `LISTEN queue_job` and holds a session advisory lock (`pg_try_advisory_lock`) so that only one runner works. Both need a session – the runner gets its own connection settings: `jobrunner_db_host` / `jobrunner_db_port`.",
        ]),
        ("h", "Configuration"),
        ("code", "ini"),
        ("code", "auth"),
        ("code", "odoo"),
        ("h", "Sizing"),
        ("table", _SIZE["en"]),
        ("p", "Example: 4 Odoo servers × 33 workers, DB server with 32 cores. `max_client_conn = 2000`, `default_pool_size = 64–100`, `max_db_connections = 150`, PostgreSQL `max_connections = 200`. Without PgBouncer, PostgreSQL would have needed several hundred to thousands of connections."),
        ("h", "Monitoring"),
        ("code", "show"),
        ("p", "The most important column is `cl_waiting` in `SHOW POOLS`: clients waiting for a free server connection. Permanently above zero = pool too small or long transactions (long crons, reports) occupy it. `maxwait` shows how long the oldest waits."),
        ("code", "check"),
        ("h", "Troubleshooting"),
        ("ul", [
            "**Chat messages and notifications only appear after reload** → the database `postgres` runs in transaction mode; set `pool_mode=session` for it.",
            "**queue_job jobs stay in “enqueued”** → the runner connects via transaction pooling; set `jobrunner_db_port` to PostgreSQL or a session entry.",
            "**`no more connections allowed (max_client_conn)`** → raise `max_client_conn`; check Odoo processes × `db_maxconn`.",
            "**`query_wait_timeout`** → pool exhausted: raise `default_pool_size` carefully or find the long transactions (`pg_stat_activity`).",
            "**`DROP DATABASE` / restore fails: database is being accessed** → `PAUSE mydb;` or `KILL mydb;` in the PgBouncer console, or work directly on port 5432.",
            "**Odoo database manager does not list a new database** → wildcard entry `*` present? With `list_db = False` irrelevant anyway.",
        ]),
        ("h", "When you do not need it"),
        ("p", "One Odoo server with 10–20 workers next to PostgreSQL: the number of connections is small, PgBouncer only adds a component. It pays off with several Odoo servers, many workers, `max_connections` in the high hundreds – our calculator shows a hint above 500."),
        ("links", "Links"),
    ],
}

_SIZE["de"] = [["Wert", "Faustregel", "Warum"],
    ["`max_client_conn`", "Odoo-Prozesse × `db_maxconn` (+ Reserve)", "Client-Verbindungen sind in PgBouncer billig"],
    ["`default_pool_size`", "≈ 2–4 × CPU-Kerne des DB-Servers", "so viele Transaktionen laufen gleichzeitig in PostgreSQL"],
    ["`max_db_connections`", "unter `max_connections` von PostgreSQL minus Reserve", "mehr sieht PostgreSQL nie"],
    ["`max_connections` (PostgreSQL)", "Summe aller Pools + Session-Pools + Admin-Reserve", "jetzt klein (100–300) statt Tausende"],
    ["`query_wait_timeout`", "60–120 s", "sonst warten Clients ewig, wenn der Pool erschöpft ist"]]

PGBOUNCER["t"]["de"] = {
    "title": "PgBouncer für Odoo: Transaction Pooling, ohne Bus und queue_job zu zerstören",
    "summary": "Warum viele Odoo-Worker einen Connection Pooler brauchen, warum Transaction Pooling die Live-Benachrichtigungen von Odoo und OCA queue_job bei naiver Einrichtung lahmlegt, und eine funktionierende pgbouncer.ini mit Session Pooling für die Datenbank postgres – dazu Dimensionierung, Überwachung und Fehlersuche.",
    "body": [
        ("p", "Mit mehreren Odoo-Servern oder Hunderten Workern explodiert die Zahl der Datenbankverbindungen: Jeder Odoo-Prozess hält einen eigenen Pool mit bis zu `db_maxconn` Verbindungen. PostgreSQL bezahlt jede Verbindung mit einem Prozess und RAM – und ab einigen Hundert aktiven Verbindungen wird es spürbar langsamer. PgBouncer sitzt dazwischen: Odoo öffnet so viele billige Client-Verbindungen, wie es will, PostgreSQL sieht nur einen kleinen Pool."),
        ("note", "Kurzfassung: Die Odoo-Datenbanken mit `pool_mode = transaction`, die Datenbank `postgres` mit `pool_mode = session` (dort läuft `LISTEN imbus` des Odoo-Bus) und der OCA-queue_job-Runner direkt zu PostgreSQL über `jobrunner_db_host/port`. Anders eingerichtet hören Chat, Benachrichtigungen und Job-Verarbeitung still auf zu funktionieren."),
        ("h", "Pooling-Modi – und was Odoo braucht"),
        ("ul", [
            "**session**: Eine Server-Verbindung gehört dem Client, bis er sich trennt. Sicher, spart bei Odoos langlebigen Verbindungen aber fast nichts.",
            "**transaction**: Eine Server-Verbindung nur für die Dauer einer Transaktion. Hier liegt der Gewinn: Hunderte untätige Odoo-Verbindungen teilen sich wenige Dutzend echte.",
            "**statement**: keine Transaktionen aus mehreren Anweisungen – für Odoo unbrauchbar.",
            "Normale Odoo-Anfragen funktionieren im Transaktionsmodus: Jede Anfrage ist eine Transaktion, psycopg2 sendet die Isolationsstufe mit `BEGIN`, Odoo nutzt keine serverseitigen Prepared Statements.",
        ]),
        ("h", "Die zwei Fallen"),
        ("ul", [
            "**Odoo-Bus (Live-Chat, Benachrichtigungen, Dialog):** Der Gevent-Prozess öffnet eine Verbindung zur Datenbank **postgres** und führt `LISTEN imbus` aus (Quelle: `addons/bus/models/bus.py`). `LISTEN` funktioniert nur in einer Session – im Transaktionsmodus gehen die Benachrichtigungen verloren.",
            "**OCA queue_job:** Der Job-Runner führt `LISTEN queue_job` aus und hält einen Session-Advisory-Lock (`pg_try_advisory_lock`), damit nur ein Runner arbeitet. Beides braucht eine Session – der Runner bekommt eigene Verbindungsdaten: `jobrunner_db_host` / `jobrunner_db_port`.",
        ]),
        ("h", "Konfiguration"),
        ("code", "ini"),
        ("code", "auth"),
        ("code", "odoo"),
        ("h", "Dimensionierung"),
        ("table", _SIZE["de"]),
        ("p", "Beispiel: 4 Odoo-Server × 33 Worker, DB-Server mit 32 Kernen. `max_client_conn = 2000`, `default_pool_size = 64–100`, `max_db_connections = 150`, PostgreSQL `max_connections = 200`. Ohne PgBouncer hätte PostgreSQL mehrere Hundert bis Tausende Verbindungen gebraucht."),
        ("h", "Überwachung"),
        ("code", "show"),
        ("p", "Die wichtigste Spalte ist `cl_waiting` in `SHOW POOLS`: Clients, die auf eine freie Server-Verbindung warten. Dauerhaft über null = Pool zu klein oder lange Transaktionen (lange Cron-Jobs, Berichte) belegen ihn. `maxwait` zeigt, wie lange der älteste wartet."),
        ("code", "check"),
        ("h", "Fehlersuche"),
        ("ul", [
            "**Chat-Nachrichten und Benachrichtigungen erscheinen erst nach Neuladen** → Die Datenbank `postgres` läuft im Transaktionsmodus; für sie `pool_mode=session` setzen.",
            "**queue_job-Jobs bleiben auf „enqueued“** → Der Runner verbindet sich über Transaction Pooling; `jobrunner_db_port` auf PostgreSQL oder einen Session-Eintrag setzen.",
            "**`no more connections allowed (max_client_conn)`** → `max_client_conn` erhöhen; Odoo-Prozesse × `db_maxconn` prüfen.",
            "**`query_wait_timeout`** → Pool erschöpft: `default_pool_size` vorsichtig erhöhen oder die langen Transaktionen finden (`pg_stat_activity`).",
            "**`DROP DATABASE` / Restore scheitert: database is being accessed** → `PAUSE mydb;` oder `KILL mydb;` in der PgBouncer-Konsole oder direkt auf Port 5432 arbeiten.",
            "**Der Odoo-Datenbankmanager zeigt eine neue Datenbank nicht** → Wildcard-Eintrag `*` vorhanden? Mit `list_db = False` ohnehin egal.",
        ]),
        ("h", "Wann man es nicht braucht"),
        ("p", "Ein Odoo-Server mit 10–20 Workern neben PostgreSQL: Die Zahl der Verbindungen ist klein, PgBouncer bringt nur eine zusätzliche Komponente. Es lohnt sich mit mehreren Odoo-Servern, vielen Workern, `max_connections` im hohen dreistelligen Bereich – unser Rechner zeigt ab 500 einen Hinweis."),
        ("links", "Links"),
    ],
}

_SIZE["fr"] = [["Valeur", "Règle empirique", "Pourquoi"],
    ["`max_client_conn`", "processus Odoo × `db_maxconn` (+ réserve)", "les connexions client sont peu coûteuses dans PgBouncer"],
    ["`default_pool_size`", "≈ 2–4 × cœurs CPU du serveur BD", "autant de transactions tournent en même temps dans PostgreSQL"],
    ["`max_db_connections`", "sous `max_connections` de PostgreSQL moins une réserve", "PostgreSQL n'en voit jamais plus"],
    ["`max_connections` (PostgreSQL)", "somme des pools + pools de session + réserve admin", "maintenant petit (100–300) au lieu de milliers"],
    ["`query_wait_timeout`", "60–120 s", "sinon les clients attendent indéfiniment quand le pool est épuisé"]]

PGBOUNCER["t"]["fr"] = {
    "title": "PgBouncer pour Odoo : le pooling par transaction sans casser le bus et queue_job",
    "summary": "Pourquoi beaucoup de workers Odoo ont besoin d'un pooler de connexions, pourquoi le pooling par transaction casse les notifications en direct d'Odoo et OCA queue_job s'il est mis en place naïvement, et un pgbouncer.ini fonctionnel avec pooling de session pour la base postgres – plus dimensionnement, surveillance et dépannage.",
    "body": [
        ("p", "Avec plusieurs serveurs Odoo ou des centaines de workers, le nombre de connexions à la base explose : chaque processus Odoo garde son propre pool de jusqu'à `db_maxconn` connexions. PostgreSQL paie chaque connexion avec un processus et de la RAM – et à partir de quelques centaines de connexions actives il ralentit nettement. PgBouncer se place entre les deux : Odoo ouvre autant de connexions client bon marché qu'il veut, PostgreSQL ne voit qu'un petit pool."),
        ("note", "En bref : les bases Odoo en `pool_mode = transaction`, la base `postgres` en `pool_mode = session` (le bus Odoo y exécute `LISTEN imbus`), et le runner OCA queue_job directement vers PostgreSQL via `jobrunner_db_host/port`. Autrement, le chat, les notifications et le traitement des jobs cessent de fonctionner en silence."),
        ("h", "Modes de pooling – et ce dont Odoo a besoin"),
        ("ul", [
            "**session** : une connexion serveur appartient au client jusqu'à sa déconnexion. Sûr, mais n'économise presque rien avec les connexions longues d'Odoo.",
            "**transaction** : une connexion serveur seulement pendant une transaction. C'est là qu'est le gain : des centaines de connexions Odoo inactives se partagent quelques dizaines de vraies.",
            "**statement** : pas de transactions à plusieurs instructions – inutilisable pour Odoo.",
            "Les requêtes normales d'Odoo fonctionnent en mode transaction : chaque requête est une transaction, psycopg2 envoie le niveau d'isolation avec `BEGIN`, Odoo n'utilise pas de requêtes préparées côté serveur.",
        ]),
        ("h", "Les deux pièges"),
        ("ul", [
            "**Bus Odoo (chat en direct, notifications, Discussion) :** le processus gevent ouvre une connexion à la base **postgres** et exécute `LISTEN imbus` (source : `addons/bus/models/bus.py`). `LISTEN` ne fonctionne qu'en session – en mode transaction, les notifications se perdent.",
            "**OCA queue_job :** le runner exécute `LISTEN queue_job` et garde un verrou consultatif de session (`pg_try_advisory_lock`) pour qu'un seul runner travaille. Les deux exigent une session – le runner reçoit ses propres paramètres de connexion : `jobrunner_db_host` / `jobrunner_db_port`.",
        ]),
        ("h", "Configuration"),
        ("code", "ini"),
        ("code", "auth"),
        ("code", "odoo"),
        ("h", "Dimensionnement"),
        ("table", _SIZE["fr"]),
        ("p", "Exemple : 4 serveurs Odoo × 33 workers, serveur BD à 32 cœurs. `max_client_conn = 2000`, `default_pool_size = 64–100`, `max_db_connections = 150`, PostgreSQL `max_connections = 200`. Sans PgBouncer, PostgreSQL aurait eu besoin de plusieurs centaines à milliers de connexions."),
        ("h", "Surveillance"),
        ("code", "show"),
        ("p", "La colonne la plus importante est `cl_waiting` dans `SHOW POOLS` : les clients qui attendent une connexion serveur libre. Durablement au-dessus de zéro = pool trop petit ou longues transactions (crons longs, rapports) qui l'occupent. `maxwait` indique depuis combien de temps le plus ancien attend."),
        ("code", "check"),
        ("h", "Dépannage"),
        ("ul", [
            "**Les messages du chat et les notifications n'apparaissent qu'après rechargement** → la base `postgres` est en mode transaction ; lui mettre `pool_mode=session`.",
            "**Les jobs queue_job restent en « enqueued »** → le runner passe par le pooling par transaction ; mettre `jobrunner_db_port` vers PostgreSQL ou une entrée en session.",
            "**`no more connections allowed (max_client_conn)`** → augmenter `max_client_conn` ; vérifier processus Odoo × `db_maxconn`.",
            "**`query_wait_timeout`** → pool épuisé : augmenter prudemment `default_pool_size` ou trouver les longues transactions (`pg_stat_activity`).",
            "**`DROP DATABASE` / restauration échoue : database is being accessed** → `PAUSE mydb;` ou `KILL mydb;` dans la console PgBouncer, ou travailler directement sur le port 5432.",
            "**Le gestionnaire de bases Odoo n'affiche pas une nouvelle base** → entrée joker `*` présente ? Avec `list_db = False`, sans importance de toute façon.",
        ]),
        ("h", "Quand on n'en a pas besoin"),
        ("p", "Un serveur Odoo avec 10–20 workers à côté de PostgreSQL : le nombre de connexions est faible, PgBouncer n'ajoute qu'un composant. Il devient rentable avec plusieurs serveurs Odoo, beaucoup de workers, un `max_connections` dans les centaines élevées – notre calculateur affiche un avertissement au-delà de 500."),
        ("links", "Liens"),
    ],
}

_SIZE["el"] = [["Τιμή", "Εμπειρικός κανόνας", "Γιατί"],
    ["`max_client_conn`", "διεργασίες Odoo × `db_maxconn` (+ απόθεμα)", "οι συνδέσεις πελάτη είναι φθηνές στο PgBouncer"],
    ["`default_pool_size`", "≈ 2–4 × πυρήνες CPU του server βάσης", "τόσες συναλλαγές τρέχουν ταυτόχρονα στην PostgreSQL"],
    ["`max_db_connections`", "κάτω από το `max_connections` της PostgreSQL μείον απόθεμα", "η PostgreSQL δεν βλέπει ποτέ περισσότερες"],
    ["`max_connections` (PostgreSQL)", "άθροισμα όλων των pools + session pools + απόθεμα διαχείρισης", "τώρα μικρό (100–300) αντί για χιλιάδες"],
    ["`query_wait_timeout`", "60–120 s", "αλλιώς οι πελάτες περιμένουν για πάντα όταν εξαντληθεί το pool"]]

PGBOUNCER["t"]["el"] = {
    "title": "PgBouncer για Odoo: transaction pooling χωρίς να σπάσει το bus και το queue_job",
    "summary": "Γιατί πολλοί workers του Odoo χρειάζονται connection pooler, γιατί το transaction pooling σπάει τις ζωντανές ειδοποιήσεις του Odoo και το OCA queue_job αν στηθεί αφελώς, και ένα λειτουργικό pgbouncer.ini με session pooling για τη βάση postgres – μαζί με διαστασιολόγηση, παρακολούθηση και αντιμετώπιση προβλημάτων.",
    "body": [
        ("p", "Με πολλούς servers Odoo ή εκατοντάδες workers ο αριθμός των συνδέσεων στη βάση εκρήγνυται: κάθε διεργασία Odoo κρατά δικό της pool έως `db_maxconn` συνδέσεις. Η PostgreSQL πληρώνει κάθε σύνδεση με μια διεργασία και RAM – και από μερικές εκατοντάδες ενεργές συνδέσεις και πάνω επιβραδύνεται αισθητά. Το PgBouncer μπαίνει ενδιάμεσα: το Odoo ανοίγει όσες φθηνές συνδέσεις πελάτη θέλει, η PostgreSQL βλέπει μόνο ένα μικρό pool."),
        ("note", "Συνοπτικά: οι βάσεις του Odoo με `pool_mode = transaction`, η βάση `postgres` με `pool_mode = session` (εκεί το bus του Odoo εκτελεί `LISTEN imbus`), και ο runner του OCA queue_job απευθείας στην PostgreSQL μέσω `jobrunner_db_host/port`. Αλλιώς το chat, οι ειδοποιήσεις και η επεξεργασία των jobs σταματούν σιωπηλά."),
        ("h", "Λειτουργίες pooling – και τι χρειάζεται το Odoo"),
        ("ul", [
            "**session**: μια σύνδεση server ανήκει στον πελάτη μέχρι να αποσυνδεθεί. Ασφαλές, αλλά δεν εξοικονομεί σχεδόν τίποτα με τις μακρόβιες συνδέσεις του Odoo.",
            "**transaction**: μια σύνδεση server μόνο για τη διάρκεια μιας συναλλαγής. Εδώ είναι το κέρδος: εκατοντάδες αδρανείς συνδέσεις Odoo μοιράζονται λίγες δεκάδες πραγματικές.",
            "**statement**: χωρίς συναλλαγές πολλών εντολών – άχρηστο για το Odoo.",
            "Τα κανονικά αιτήματα του Odoo λειτουργούν σε transaction mode: κάθε αίτημα είναι μία συναλλαγή, το psycopg2 στέλνει το επίπεδο απομόνωσης με το `BEGIN`, το Odoo δεν χρησιμοποιεί prepared statements στον server.",
        ]),
        ("h", "Οι δύο παγίδες"),
        ("ul", [
            "**Bus του Odoo (ζωντανό chat, ειδοποιήσεις, Discuss):** η διεργασία gevent ανοίγει σύνδεση στη βάση **postgres** και εκτελεί `LISTEN imbus` (πηγή: `addons/bus/models/bus.py`). Το `LISTEN` λειτουργεί μόνο σε session – σε transaction mode οι ειδοποιήσεις χάνονται.",
            "**OCA queue_job:** ο runner εκτελεί `LISTEN queue_job` και κρατά ένα session advisory lock (`pg_try_advisory_lock`) ώστε να δουλεύει μόνο ένας runner. Και τα δύο χρειάζονται session – ο runner παίρνει δικές του ρυθμίσεις σύνδεσης: `jobrunner_db_host` / `jobrunner_db_port`.",
        ]),
        ("h", "Ρύθμιση"),
        ("code", "ini"),
        ("code", "auth"),
        ("code", "odoo"),
        ("h", "Διαστασιολόγηση"),
        ("table", _SIZE["el"]),
        ("p", "Παράδειγμα: 4 servers Odoo × 33 workers, server βάσης με 32 πυρήνες. `max_client_conn = 2000`, `default_pool_size = 64–100`, `max_db_connections = 150`, PostgreSQL `max_connections = 200`. Χωρίς PgBouncer η PostgreSQL θα χρειαζόταν μερικές εκατοντάδες έως χιλιάδες συνδέσεις."),
        ("h", "Παρακολούθηση"),
        ("code", "show"),
        ("p", "Η σημαντικότερη στήλη είναι η `cl_waiting` στο `SHOW POOLS`: πελάτες που περιμένουν ελεύθερη σύνδεση server. Μόνιμα πάνω από μηδέν = πολύ μικρό pool ή μακριές συναλλαγές (μακριά cron, αναφορές) που το καταλαμβάνουν. Το `maxwait` δείχνει πόση ώρα περιμένει ο παλαιότερος."),
        ("code", "check"),
        ("h", "Αντιμετώπιση προβλημάτων"),
        ("ul", [
            "**Τα μηνύματα chat και οι ειδοποιήσεις εμφανίζονται μόνο μετά από ανανέωση** → η βάση `postgres` τρέχει σε transaction mode· ορίστε της `pool_mode=session`.",
            "**Τα jobs του queue_job μένουν σε «enqueued»** → ο runner συνδέεται μέσω transaction pooling· βάλτε το `jobrunner_db_port` στην PostgreSQL ή σε καταχώριση session.",
            "**`no more connections allowed (max_client_conn)`** → αυξήστε το `max_client_conn`· ελέγξτε διεργασίες Odoo × `db_maxconn`.",
            "**`query_wait_timeout`** → εξαντλημένο pool: αυξήστε προσεκτικά το `default_pool_size` ή βρείτε τις μακριές συναλλαγές (`pg_stat_activity`).",
            "**Αποτυγχάνει το `DROP DATABASE` / η επαναφορά: database is being accessed** → `PAUSE mydb;` ή `KILL mydb;` στην κονσόλα του PgBouncer, ή δουλέψτε απευθείας στη θύρα 5432.",
            "**Ο database manager του Odoo δεν δείχνει νέα βάση** → υπάρχει η καταχώριση μπαλαντέρ `*`; Με `list_db = False` δεν έχει σημασία ούτως ή άλλως.",
        ]),
        ("h", "Πότε δεν το χρειάζεστε"),
        ("p", "Ένας server Odoo με 10–20 workers δίπλα στην PostgreSQL: οι συνδέσεις είναι λίγες, το PgBouncer απλώς προσθέτει ένα ακόμα στοιχείο. Αξίζει με πολλούς servers Odoo, πολλούς workers, `max_connections` στις υψηλές εκατοντάδες – ο υπολογιστής μας δείχνει ειδοποίηση πάνω από 500."),
        ("links", "Σύνδεσμοι"),
    ],
}

_SIZE["uk"] = [["Параметр", "Емпіричне правило", "Чому"],
    ["`max_client_conn`", "процеси Odoo × `db_maxconn` (+ запас)", "клієнтські з'єднання в PgBouncer дешеві"],
    ["`default_pool_size`", "≈ 2–4 × ядра CPU сервера БД", "стільки транзакцій одночасно працює в PostgreSQL"],
    ["`max_db_connections`", "нижче за `max_connections` PostgreSQL мінус запас", "більше PostgreSQL не побачить ніколи"],
    ["`max_connections` (PostgreSQL)", "сума всіх пулів + сесійні пули + запас для адміна", "тепер невелике значення (100–300), а не тисячі"],
    ["`query_wait_timeout`", "60–120 с", "інакше, коли пул вичерпано, клієнти чекатимуть вічно"]]

PGBOUNCER["t"]["uk"] = {
    "title": "PgBouncer для Odoo: transaction pooling, який не ламає шину і queue_job",
    "summary": "Навіщо багатьом воркерам Odoo пулер з'єднань, чому наївно налаштований transaction pooling ламає живі сповіщення Odoo та OCA queue_job, і робочий pgbouncer.ini з session pooling для бази postgres. А також розрахунок розмірів, моніторинг і пошук проблем.",
    "body": [
        ("p", "Коли серверів Odoo кілька або воркерів сотні, кількість з'єднань з базою різко зростає: кожен процес Odoo тримає власний пул до `db_maxconn` з'єднань. PostgreSQL платить за кожне з'єднання окремим процесом і пам'яттю, і вже після кількох сотень активних з'єднань помітно сповільнюється. PgBouncer стоїть посередині: Odoo відкриває скільки завгодно дешевих клієнтських з'єднань, а PostgreSQL бачить лише невеликий пул."),
        ("note", "Коротко: бази Odoo — у `pool_mode = transaction`, база `postgres` — у `pool_mode = session` (там шина Odoo виконує `LISTEN imbus`), а раннер OCA queue_job ходить напряму до PostgreSQL через `jobrunner_db_host/port`. Інакше чат, сповіщення й обробка завдань непомітно перестануть працювати."),
        ("h", "Режими пулінгу і що потрібно Odoo"),
        ("ul", [
            "**session**: серверне з'єднання належить клієнту, доки той не від'єднається. Безпечно, але з довгими з'єднаннями Odoo майже нічого не заощаджує.",
            "**transaction**: серверне з'єднання видається лише на час однієї транзакції. Саме тут виграш: сотні простоюючих з'єднань Odoo ділять кілька десятків справжніх.",
            "**statement**: транзакцій з кількох запитів немає, тож для Odoo не підходить.",
            "Звичайні запити Odoo працюють у режимі transaction: кожен запит — це одна транзакція, psycopg2 передає рівень ізоляції разом із `BEGIN`, а серверних prepared statements Odoo не використовує.",
        ]),
        ("h", "Дві пастки"),
        ("ul", [
            "**Шина Odoo (живий чат, сповіщення, Discuss):** процес gevent відкриває з'єднання з базою **postgres** і виконує `LISTEN imbus` (код: `addons/bus/models/bus.py`). `LISTEN` працює лише в сесії, тож у режимі transaction сповіщення губляться.",
            "**OCA queue_job:** раннер виконує `LISTEN queue_job` і тримає advisory lock на рівні сесії (`pg_try_advisory_lock`), щоб працював лише один раннер. І те, і те потребує сесії, тому для раннера є окремі параметри з'єднання: `jobrunner_db_host` / `jobrunner_db_port`.",
        ]),
        ("h", "Налаштування"),
        ("code", "ini"),
        ("code", "auth"),
        ("code", "odoo"),
        ("h", "Розрахунок розмірів"),
        ("table", _SIZE["uk"]),
        ("p", "Приклад: 4 сервери Odoo по 33 воркери, сервер БД на 32 ядра. `max_client_conn = 2000`, `default_pool_size = 64–100`, `max_db_connections = 150`, у PostgreSQL `max_connections = 200`. Без PgBouncer PostgreSQL знадобилося б від кількох сотень до тисяч з'єднань."),
        ("h", "Моніторинг"),
        ("code", "show"),
        ("p", "Найважливіша колонка в `SHOW POOLS` — `cl_waiting`: клієнти, які чекають на вільне серверне з'єднання. Якщо вона постійно більша за нуль, пул замалий або його займають довгі транзакції (довгі крони, звіти). `maxwait` показує, скільки чекає найстаріший клієнт."),
        ("code", "check"),
        ("h", "Пошук проблем"),
        ("ul", [
            "**Повідомлення чату й сповіщення з'являються лише після перезавантаження сторінки** → база `postgres` працює в режимі transaction; задайте для неї `pool_mode=session`.",
            "**Завдання queue_job застрягають у стані «enqueued»** → раннер підключається через transaction pooling; спрямуйте `jobrunner_db_port` на PostgreSQL або на запис із режимом session.",
            "**`no more connections allowed (max_client_conn)`** → збільште `max_client_conn` і перевірте добуток процесів Odoo на `db_maxconn`.",
            "**`query_wait_timeout`** → пул вичерпано: обережно збільште `default_pool_size` або знайдіть довгі транзакції (`pg_stat_activity`).",
            "**`DROP DATABASE` чи відновлення не вдається: database is being accessed** → виконайте `PAUSE mydb;` або `KILL mydb;` у консолі PgBouncer чи працюйте напряму через порт 5432.",
            "**Менеджер баз Odoo не показує нову базу** → перевірте, чи є запис із шаблоном `*`. Утім, з `list_db = False` це не має значення.",
        ]),
        ("h", "Коли він не потрібен"),
        ("p", "Один сервер Odoo з 10–20 воркерами поряд із PostgreSQL: з'єднань мало, і PgBouncer лише додає ще один компонент. Він виправданий, коли серверів Odoo кілька, воркерів багато, а `max_connections` сягає сотень. Наш калькулятор показує підказку, якщо значення перевищує 500."),
        ("links", "Посилання"),
    ],
}

_SIZE["ru"] = [["Параметр", "Эмпирическое правило", "Почему"],
    ["`max_client_conn`", "процессы Odoo × `db_maxconn` (+ запас)", "клиентские соединения в PgBouncer дешёвые"],
    ["`default_pool_size`", "≈ 2–4 × ядра CPU сервера БД", "столько транзакций одновременно работает в PostgreSQL"],
    ["`max_db_connections`", "ниже `max_connections` PostgreSQL минус запас", "больше PostgreSQL не увидит никогда"],
    ["`max_connections` (PostgreSQL)", "сумма всех пулов + сессионные пулы + запас для админа", "теперь небольшое значение (100–300), а не тысячи"],
    ["`query_wait_timeout`", "60–120 с", "иначе, когда пул исчерпан, клиенты будут ждать вечно"]]

PGBOUNCER["t"]["ru"] = {
    "title": "PgBouncer для Odoo: transaction pooling, который не ломает шину и queue_job",
    "summary": "Зачем многим воркерам Odoo пулер соединений, почему наивно настроенный transaction pooling ломает живые уведомления Odoo и OCA queue_job, и рабочий pgbouncer.ini с session pooling для базы postgres. А также расчёт размеров, мониторинг и поиск проблем.",
    "body": [
        ("p", "Когда серверов Odoo несколько или воркеров сотни, число соединений с базой резко растёт: каждый процесс Odoo держит собственный пул до `db_maxconn` соединений. PostgreSQL платит за каждое соединение отдельным процессом и памятью, и уже после нескольких сотен активных соединений заметно замедляется. PgBouncer стоит посередине: Odoo открывает сколько угодно дешёвых клиентских соединений, а PostgreSQL видит только небольшой пул."),
        ("note", "Коротко: базы Odoo — в `pool_mode = transaction`, база `postgres` — в `pool_mode = session` (там шина Odoo выполняет `LISTEN imbus`), а раннер OCA queue_job ходит напрямую в PostgreSQL через `jobrunner_db_host/port`. Иначе чат, уведомления и обработка заданий незаметно перестанут работать."),
        ("h", "Режимы пулинга и что нужно Odoo"),
        ("ul", [
            "**session**: серверное соединение принадлежит клиенту, пока тот не отключится. Безопасно, но с долгими соединениями Odoo почти ничего не экономит.",
            "**transaction**: серверное соединение выдаётся только на время одной транзакции. Именно здесь выигрыш: сотни простаивающих соединений Odoo делят несколько десятков настоящих.",
            "**statement**: транзакций из нескольких запросов нет, поэтому для Odoo не подходит.",
            "Обычные запросы Odoo работают в режиме transaction: каждый запрос — это одна транзакция, psycopg2 передаёт уровень изоляции вместе с `BEGIN`, а серверных prepared statements Odoo не использует.",
        ]),
        ("h", "Две ловушки"),
        ("ul", [
            "**Шина Odoo (живой чат, уведомления, Discuss):** процесс gevent открывает соединение с базой **postgres** и выполняет `LISTEN imbus` (код: `addons/bus/models/bus.py`). `LISTEN` работает только в сессии, поэтому в режиме transaction уведомления теряются.",
            "**OCA queue_job:** раннер выполняет `LISTEN queue_job` и держит advisory lock на уровне сессии (`pg_try_advisory_lock`), чтобы работал только один раннер. И то и другое требует сессии, поэтому для раннера есть отдельные параметры соединения: `jobrunner_db_host` / `jobrunner_db_port`.",
        ]),
        ("h", "Настройка"),
        ("code", "ini"),
        ("code", "auth"),
        ("code", "odoo"),
        ("h", "Расчёт размеров"),
        ("table", _SIZE["ru"]),
        ("p", "Пример: 4 сервера Odoo по 33 воркера, сервер БД на 32 ядра. `max_client_conn = 2000`, `default_pool_size = 64–100`, `max_db_connections = 150`, в PostgreSQL `max_connections = 200`. Без PgBouncer PostgreSQL понадобилось бы от нескольких сотен до тысяч соединений."),
        ("h", "Мониторинг"),
        ("code", "show"),
        ("p", "Самая важная колонка в `SHOW POOLS` — `cl_waiting`: клиенты, которые ждут свободное серверное соединение. Если она постоянно больше нуля, пул мал или его занимают долгие транзакции (долгие кроны, отчёты). `maxwait` показывает, сколько ждёт самый старый клиент."),
        ("code", "check"),
        ("h", "Поиск проблем"),
        ("ul", [
            "**Сообщения чата и уведомления появляются только после перезагрузки страницы** → база `postgres` работает в режиме transaction; задайте для неё `pool_mode=session`.",
            "**Задания queue_job застревают в состоянии «enqueued»** → раннер подключается через transaction pooling; направьте `jobrunner_db_port` в PostgreSQL или на запись с режимом session.",
            "**`no more connections allowed (max_client_conn)`** → увеличьте `max_client_conn` и проверьте произведение процессов Odoo на `db_maxconn`.",
            "**`query_wait_timeout`** → пул исчерпан: осторожно увеличьте `default_pool_size` или найдите долгие транзакции (`pg_stat_activity`).",
            "**`DROP DATABASE` или восстановление не проходит: database is being accessed** → выполните `PAUSE mydb;` или `KILL mydb;` в консоли PgBouncer либо работайте напрямую через порт 5432.",
            "**Менеджер баз Odoo не показывает новую базу** → проверьте, есть ли запись с шаблоном `*`. Впрочем, с `list_db = False` это неважно.",
        ]),
        ("h", "Когда он не нужен"),
        ("p", "Один сервер Odoo с 10–20 воркерами рядом с PostgreSQL: соединений мало, и PgBouncer только добавляет ещё один компонент. Он оправдан, когда серверов Odoo несколько, воркеров много, а `max_connections` доходит до сотен. Наш калькулятор показывает подсказку, если значение больше 500."),
        ("links", "Ссылки"),
    ],
}
