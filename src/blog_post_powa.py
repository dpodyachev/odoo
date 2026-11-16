# Статья 22: PoWA (PostgreSQL Workload Analyzer) для Odoo – remote mode в Docker: repository + collector + web,
# расширения на наблюдаемых серверах (primary и реплика), роль без superuser, пароль не в powa_servers,
# что смотреть для Odoo. Основа – реальный docker-compose мониторинга (обезличено, без паролей и адресов). Все 6 языков.

POWA = {
    "slug": "powa-postgresql-workload-analyzer-odoo-docker",
    "date": "2026-11-16",
    "tags": ["PostgreSQL", "PoWA", "Monitoring", "Docker", "Odoo", "Performance"],
    "code": {
        "arch": ("architecture (remote mode)", """ monitored PostgreSQL servers            monitoring host (Docker)
 ┌──────────────────────────────┐        ┌────────────────────────────────────────┐
 │ primary   10.0.0.10:5432     │◄──┐    │ powa-collector  ── every N s snapshot ─┐│
 │  db "powa": powa, pg_stat_*  │   ├────┤                                        ││
 │ replica   10.0.0.11:5432     │◄──┘    │ powa-repository (PostgreSQL + powa) ◄──┘│
 │ stage     10.0.0.20:5432     │◄───────┤                                         │
 └──────────────────────────────┘        │ powa-web :8888 ──► nginx/SSH tunnel     │
                                         └────────────────────────────────────────┘"""),
        "pkgs": ("bash · on every monitored PostgreSQL server (Ubuntu, PGDG repository)", """sudo apt install postgresql-16-powa postgresql-16-pg-qualstats postgresql-16-pg-stat-kcache \\
                 postgresql-16-pg-wait-sampling postgresql-16-pg-track-settings postgresql-16-hypopg

# postgresql.conf (or ALTER SYSTEM) – needs a RESTART of PostgreSQL
shared_preload_libraries = 'pg_stat_statements,pg_stat_kcache,pg_qualstats,pg_wait_sampling'
track_io_timing = on
pg_stat_statements.max = 10000
pg_qualstats.sample_rate = 0.01          # sample 1 % of queries – enough for index advice, low overhead
# "powa" itself is NOT needed in shared_preload_libraries on remote servers (only for local mode)

sudo systemctl restart postgresql        # plan a window: Odoo loses its connections for a moment"""),
        "sql": ("psql · database, extensions and role on the monitored server", """CREATE DATABASE powa;
\\c powa
CREATE EXTENSION pg_stat_statements;
CREATE EXTENSION btree_gist;
CREATE EXTENSION powa;
CREATE EXTENSION pg_qualstats;
CREATE EXTENSION pg_stat_kcache;
CREATE EXTENSION pg_wait_sampling;
CREATE EXTENSION pg_track_settings;

-- index suggestions: hypopg in every Odoo database you want to optimise
\\c mydb
CREATE EXTENSION hypopg;

-- collector role: no superuser needed (PostgreSQL 10+)
CREATE ROLE powa LOGIN PASSWORD '<long random>';
GRANT pg_read_all_stats TO powa;
\\c powa
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO powa;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO powa;"""),
        "hba": ("pg_hba.conf · only the monitoring host", """# TYPE   DATABASE  USER  ADDRESS          METHOD
hostssl  powa      powa  10.0.0.50/32     scram-sha-256
hostssl  mydb      powa  10.0.0.50/32     scram-sha-256    # for "optimize" / EXPLAIN in powa-web
# then: SELECT pg_reload_conf();"""),
        "compose": ("docker-compose.yml · monitoring host", """services:
  powa-repository:
    image: powateam/powa-archivist-16:5.3.0
    restart: unless-stopped
    environment:
      POSTGRES_PASSWORD_FILE: /run/secrets/repo_password    # not 'trust'
    secrets: [repo_password]
    volumes:
      - powa-data:/var/lib/postgresql/data
      - ./register.sql:/register.sql:ro           # run once after the first start (see "check")
    healthcheck:
      test: ["CMD-SHELL", "psql -U postgres -AXtc 'SELECT 1 FROM powa_servers LIMIT 1' powa"]
      interval: 10s

  powa-collector:
    image: powateam/powa-collector:1.3.2
    restart: unless-stopped
    environment:
      PGPASSFILE: /run/secrets/pgpass          # passwords for the remote servers – not in powa_servers
    secrets: [pgpass]
    volumes:
      - ./powa-collector.conf:/etc/powa-collector.conf:ro
    depends_on:
      powa-repository: { condition: service_healthy }

  powa-web:
    image: powateam/powa-web:5.3.1
    restart: unless-stopped
    volumes:
      - ./powa-web.conf:/etc/powa-web.conf:ro
    ports:
      - "127.0.0.1:8888:8888"                  # only localhost – nginx or an SSH tunnel in front

volumes:
  powa-data:
secrets:
  repo_password: { file: ./secrets/repo_password }
  pgpass:        { file: ./secrets/pgpass }     # chmod 600"""),
        "register": ("register.sql · which servers to collect", """-- frequency in seconds, retention: how long snapshots are kept
SELECT powa_register_server(hostname => '10.0.0.10', alias => 'prod',
       username => 'powa', port => 5432, frequency => 300, retention => '14 days'::interval,
       extensions => '{pg_stat_kcache,pg_qualstats,pg_wait_sampling,pg_track_settings}');
SELECT powa_register_server(hostname => '10.0.0.11', alias => 'replica',
       username => 'powa', port => 5432, frequency => 300, retention => '14 days'::interval,
       extensions => '{pg_stat_kcache,pg_qualstats,pg_wait_sampling,pg_track_settings}');
-- no "password =>" here: powa_servers would keep it in plain text.
-- later changes: powa_configure_server(), powa_deactivate_server(), powa_delete_and_purge_server()"""),
        "conf": ("powa-collector.conf · powa-web.conf · secrets/pgpass", """// /etc/powa-collector.conf
{ "repository": { "dsn": "postgresql://postgres@powa-repository:5432/powa" },
  "use_server_alias": true, "debug": false }

# /etc/powa-web.conf  (Python syntax)
servers = {
  'repository': { 'host': 'powa-repository', 'port': '5432', 'database': 'powa' }
}   # no username/password here: log in in the web UI with a PostgreSQL role
cookie_secret = "<long random>"
address = "0.0.0.0"          # inside the container; published only on 127.0.0.1
port = 8888
url_prefix = "/powa"

# secrets/pgpass   host:port:database:user:password
10.0.0.10:5432:*:powa:<password>
10.0.0.11:5432:*:powa:<password>
powa-repository:5432:powa:postgres:<repository password>"""),
        "nginx": ("nginx · powa-web under /powa/ with a password", """location ^~ /powa/ {
    auth_basic "powa";
    auth_basic_user_file /etc/nginx/.htpasswd_powa;
    proxy_set_header Authorization "";
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_pass http://127.0.0.1:8888;
}
# or simply: ssh -L 8888:127.0.0.1:8888 monitoring-host  ->  http://localhost:8888/powa/"""),
        "check": ("bash · is it collecting?", """docker compose up -d
docker compose exec powa-repository psql -U postgres powa -f /register.sql   # once
docker compose restart powa-collector && docker compose logs -f powa-collector
docker compose exec powa-repository psql -U postgres powa -c \\
  "SELECT id, alias, hostname, frequency, retention, enabled FROM powa_servers;"
# last snapshot per server (errors must be empty)
docker compose exec powa-repository psql -U postgres powa -c \\
  "SELECT srvid, snapts, errors FROM powa_snapshot_metas ORDER BY srvid;"
# typical error in the collector log: "extension pg_qualstats is not installed" -> CREATE EXTENSION on that server"""),
    },
    "links": [
        ("PoWA documentation", "https://powa.readthedocs.io/"),
        ("PoWA: remote setup", "https://powa.readthedocs.io/en/latest/remote_setup.html"),
        ("PoWA: security (pg_read_all_stats, passwords)", "https://powa.readthedocs.io/en/latest/security.html"),
        ("PoWA Docker images (powateam)", "https://hub.docker.com/u/powateam"),
        ("pg_qualstats", "https://github.com/powa-team/pg_qualstats"),
        ("HypoPG – hypothetical indexes", "https://github.com/HypoPG/hypopg"),
        ("Blog: PostgreSQL cheat sheet for Odoo admins", "@blog:postgresql-odoo-admin-cheat-sheet"),
        ("Blog: pgload – load test for PostgreSQL and the replica", "@blog:postgresql-load-test-pgload-replica"),
        ("Blog: could not serialize access – concurrent updates in Odoo", "@blog:odoo-could-not-serialize-access-concurrent-update"),
        ("Blog: Grafana behind nginx under a sub-path", "@blog:grafana-behind-nginx-subpath-odoo"),
    ],
    "t": {},
}

_EXT = {
    "en": [["Extension", "What it gives you", "Odoo example"],
           ["`pg_stat_statements`", "time, calls, rows per normalised query", "which ORM `search_read` eats the most time"],
           ["`pg_stat_kcache`", "real CPU time and disk reads per query", "CPU-bound (many small queries) vs. I/O-bound (`mail_message` scans)"],
           ["`pg_qualstats` + `hypopg`", "WHERE/JOIN predicates, index suggestions tested with hypothetical indexes", "missing index on a `res_partner` or custom-model field"],
           ["`pg_wait_sampling`", "what sessions wait for", "`Lock: transactionid` = concurrent updates, `IO: DataFileRead` = cache too small"],
           ["`pg_track_settings`", "history of `postgresql.conf` changes", "“since when is work_mem 64 MB?”"]],
    "de": [["Erweiterung", "Was sie liefert", "Beispiel Odoo"],
           ["`pg_stat_statements`", "Zeit, Aufrufe, Zeilen je normalisierter Abfrage", "welches ORM-`search_read` die meiste Zeit frisst"],
           ["`pg_stat_kcache`", "echte CPU-Zeit und Plattenlesen je Abfrage", "CPU-lastig (viele kleine Abfragen) oder I/O-lastig (Scans auf `mail_message`)"],
           ["`pg_qualstats` + `hypopg`", "WHERE/JOIN-Prädikate, Indexvorschläge mit hypothetischen Indizes geprüft", "fehlender Index auf einem Feld von `res_partner` oder einem eigenen Modell"],
           ["`pg_wait_sampling`", "worauf Sitzungen warten", "`Lock: transactionid` = gleichzeitige Updates, `IO: DataFileRead` = Cache zu klein"],
           ["`pg_track_settings`", "Verlauf der Änderungen an `postgresql.conf`", "„seit wann ist work_mem 64 MB?“"]],
    "fr": [["Extension", "Ce qu'elle apporte", "Exemple Odoo"],
           ["`pg_stat_statements`", "temps, appels, lignes par requête normalisée", "quel `search_read` de l'ORM consomme le plus de temps"],
           ["`pg_stat_kcache`", "temps CPU réel et lectures disque par requête", "limité par le CPU (beaucoup de petites requêtes) ou par les E/S (parcours de `mail_message`)"],
           ["`pg_qualstats` + `hypopg`", "prédicats WHERE/JOIN, suggestions d'index testées avec des index hypothétiques", "index manquant sur un champ de `res_partner` ou d'un modèle personnalisé"],
           ["`pg_wait_sampling`", "ce que les sessions attendent", "`Lock: transactionid` = mises à jour concurrentes, `IO: DataFileRead` = cache trop petit"],
           ["`pg_track_settings`", "historique des changements de `postgresql.conf`", "« depuis quand work_mem vaut 64 Mo ? »"]],
    "el": [["Επέκταση", "Τι δίνει", "Παράδειγμα Odoo"],
           ["`pg_stat_statements`", "χρόνος, κλήσεις, γραμμές ανά κανονικοποιημένο ερώτημα", "ποιο `search_read` του ORM τρώει τον περισσότερο χρόνο"],
           ["`pg_stat_kcache`", "πραγματικός χρόνος CPU και αναγνώσεις δίσκου ανά ερώτημα", "περιορισμός από CPU (πολλά μικρά ερωτήματα) ή από I/O (σαρώσεις του `mail_message`)"],
           ["`pg_qualstats` + `hypopg`", "κατηγορήματα WHERE/JOIN, προτάσεις ευρετηρίων ελεγμένες με υποθετικά ευρετήρια", "ευρετήριο που λείπει σε πεδίο του `res_partner` ή δικού σας μοντέλου"],
           ["`pg_wait_sampling`", "τι περιμένουν οι συνεδρίες", "`Lock: transactionid` = ταυτόχρονες ενημερώσεις, `IO: DataFileRead` = μικρή cache"],
           ["`pg_track_settings`", "ιστορικό αλλαγών του `postgresql.conf`", "«από πότε το work_mem είναι 64 MB;»"]],
    "uk": [["Розширення", "Що дає", "Приклад для Odoo"],
           ["`pg_stat_statements`", "час, кількість викликів і рядків для кожного нормалізованого запиту", "який `search_read` ORM забирає найбільше часу"],
           ["`pg_stat_kcache`", "реальний час CPU і читання з диска для кожного запиту", "упор у CPU (багато дрібних запитів) чи в диск (скани `mail_message`)"],
           ["`pg_qualstats` + `hypopg`", "умови WHERE/JOIN і поради щодо індексів, перевірені гіпотетичними індексами", "бракує індексу на полі `res_partner` або власної моделі"],
           ["`pg_wait_sampling`", "на що чекають сесії", "`Lock: transactionid` означає конкурентні оновлення, `IO: DataFileRead` — замалий кеш"],
           ["`pg_track_settings`", "історія змін `postgresql.conf`", "«відколи work_mem = 64 МБ?»"]],
    "ru": [["Расширение", "Что даёт", "Пример для Odoo"],
           ["`pg_stat_statements`", "время, число вызовов и строк для каждого нормализованного запроса", "какой `search_read` ORM съедает больше всего времени"],
           ["`pg_stat_kcache`", "реальное время CPU и чтение с диска для каждого запроса", "упор в CPU (много мелких запросов) или в диск (сканы `mail_message`)"],
           ["`pg_qualstats` + `hypopg`", "условия WHERE/JOIN и советы по индексам, проверенные гипотетическими индексами", "не хватает индекса на поле `res_partner` или своей модели"],
           ["`pg_wait_sampling`", "чего ждут сессии", "`Lock: transactionid` означает конкурентные обновления, `IO: DataFileRead` — маленький кэш"],
           ["`pg_track_settings`", "история изменений `postgresql.conf`", "«с какого момента work_mem = 64 МБ?»"]],
}


def _p(lang, title, summary, intro, note, h, p_arch, p_server, p_role, p_compose, ul_compose, p_web, ul_odoo, ul_found, p_cost, links):
    return {"title": title, "summary": summary, "body": [
        ("p", intro), ("note", note),
        ("h", h[0]), ("table", _EXT[lang]),
        ("h", h[1]), ("p", p_arch), ("code", "arch"),
        ("h", h[2]), ("p", p_server), ("code", "pkgs"), ("p", p_role), ("code", "sql"), ("code", "hba"),
        ("h", h[3]), ("p", p_compose), ("code", "compose"), ("code", "register"), ("code", "conf"), ("ul", ul_compose),
        ("h", h[4]), ("p", p_web), ("code", "nginx"), ("code", "check"),
        ("h", h[5]), ("ul", ul_odoo),
        ("h", h[6]), ("ul", ul_found),
        ("h", h[7]), ("p", p_cost),
        ("links", links)]}


POWA["t"]["en"] = _p("en",
    "PoWA for PostgreSQL behind Odoo: setup in Docker (remote mode), extensions, security and what to look at",
    "PoWA (PostgreSQL Workload Analyzer) shows which queries cost the most, what sessions wait for and which indexes are missing – with history. A working Docker setup in remote mode for a primary and a replica, the extensions on the database servers, a collector role without superuser, passwords outside the powa_servers table, and what to look for with Odoo.",
    "`pg_stat_activity` shows what runs **now**; `pg_stat_statements` shows totals since the last reset. When users report “Odoo was slow yesterday between 10 and 11”, you need history – per query, with CPU, disk, waits and index advice. That is PoWA. This article is based on a real monitoring setup for a large Odoo database (hundreds of GB, primary + streaming replica + stage): what was set up, what we would change, and a clean configuration to copy.",
    "Short version: on each PostgreSQL server install the extensions, set `shared_preload_libraries` (restart!), create the database `powa` and a role with `pg_read_all_stats`; on a monitoring host run `powa-archivist` (repository), `powa-collector` and `powa-web` in Docker; register servers with `powa_register_server()` without a password (use `.pgpass`); publish powa-web only on localhost behind nginx or an SSH tunnel.",
    ["What PoWA collects", "Architecture: remote mode", "1. The monitored PostgreSQL servers", "2. Monitoring host in Docker", "3. Web UI and checks", "What to look at with Odoo", "Found in a real setup", "Overhead"],
    "Since PoWA 4 the snapshots are not stored on the production server itself (local mode) but by a separate **collector** in a **repository** database on another host. Advantages: no extra writes on the production database, one UI for primary, replica and stage, and the replica can be monitored too (it is read-only and could not store anything locally).",
    "The statistics are produced by extensions loaded into PostgreSQL at start. Packages come from the PGDG repository (apt.postgresql.org); replace 16 with your major version. The same `shared_preload_libraries` must be set on the replica – its config file is separate, extensions created on the primary replicate automatically.",
    "The collector does not need a superuser: `pg_read_all_stats` lets it read the statistics of all sessions, plus execute rights on the PoWA functions. Create the database `powa` and the extensions on the primary only – the replica receives them via replication.",
    "On the monitoring host three containers are enough. The PoWA project's example compose contains two additional demo instances (`remote-primary`, `remote-standby`) – they only exist to show the UI with test data and can be removed.",
    ["`frequency`: 300 s is the default; with very large databases and many queries 600 s keeps the repository smaller.",
     "`retention`: 7–14 days are enough to answer “what happened yesterday / last week”; the repository grows with servers × queries × snapshots.",
     "`use_server_alias`: the UI shows `prod`/`replica` instead of IP addresses.",
     "Repository and collector need no published ports – they talk inside the compose network."],
    "powa-web logs in with a PostgreSQL role (of the repository database). It sees query texts – including literal values in WHERE clauses, i.e. potentially personal data – so it must not be public.",
    ["**Queries per database** sorted by total time: typical Odoo candidates are `search_read`/`read_group` on `mail_message`, `mail_followers`, `res_partner`, and the reports of custom modules.",
     "**Calls vs. time**: thousands of fast queries per request = an N+1 problem in Python code (missing `prefetch`, `read()` in a loop), not a database problem.",
     "**Index suggestions** (pg_qualstats + hypopg): check the suggestion against Odoo – an index on a field is better declared in the model (`index=True` / `index='trigram'` in Odoo 16+) than created by hand.",
     "**Waits**: `Lock: transactionid`/`tuple` = concurrent updates of the same records (crons, queue jobs) – see the serialization article; `IO: DataFileRead` = `shared_buffers` / RAM too small; `LWLock: WALWrite` = slow disk.",
     "**Replica**: if Odoo 18/19 sends read-only requests to the replica, compare its top queries with the primary.",
     "**Settings history**: the effect of a `work_mem` or `random_page_cost` change is visible on the timeline."],
    ["**powa-web published on `0.0.0.0:8888`** on a host with a public IP – the UI with all query texts was potentially reachable from the internet. Fix: `127.0.0.1:8888:8888` + nginx with password or SSH tunnel; and the cloud firewall.",
     "**Remote passwords in `powa_register_server(... password => '...')`** inside the compose file: stored in plain text in the file and in the `powa_servers` table, and the password was a simple word. Fix: no password in SQL, `.pgpass` in the collector, a long random password, rotate it.",
     "**`POSTGRES_HOST_AUTH_METHOD: trust`** for the repository: anyone in the Docker network gets superuser without a password. Fix: `POSTGRES_PASSWORD_FILE`.",
     "**`*-git` images** (built from the development branch) and three copies of the compose file: use released, pinned versions (`powa-archivist-16:5.3.0`, `powa-collector:1.3.2`, `powa-web:5.3.1`) and keep the file in git without secrets.",
     "**Demo instances** `remote-primary`/`remote-standby` running next to the real servers – not needed, remove them."],
    "`pg_stat_statements` and `pg_wait_sampling` cost little. `pg_stat_kcache` adds a system call per query – negligible for Odoo's query sizes. `pg_qualstats` is the most expensive – keep `sample_rate` low (0.01–0.1). The snapshots themselves are a few queries every `frequency` seconds. In practice the overhead on an Odoo production server is in the low single-digit percent range; test on stage first and compare with a load test.",
    "Links")

POWA["t"]["de"] = _p("de",
    "PoWA für PostgreSQL hinter Odoo: Einrichtung in Docker (Remote-Modus), Erweiterungen, Sicherheit und was man ansieht",
    "PoWA (PostgreSQL Workload Analyzer) zeigt, welche Abfragen am meisten kosten, worauf Sitzungen warten und welche Indizes fehlen – mit Verlauf. Eine funktionierende Docker-Einrichtung im Remote-Modus für Primary und Replica, die Erweiterungen auf den Datenbankservern, eine Collector-Rolle ohne Superuser, Passwörter außerhalb der Tabelle powa_servers und worauf man bei Odoo achtet.",
    "`pg_stat_activity` zeigt, was **jetzt** läuft; `pg_stat_statements` zeigt Summen seit dem letzten Reset. Wenn Nutzer melden „Odoo war gestern zwischen 10 und 11 langsam“, braucht man Verlauf – je Abfrage, mit CPU, Platte, Wartezuständen und Indexvorschlägen. Das ist PoWA. Der Artikel beruht auf einem echten Monitoring für eine große Odoo-Datenbank (Hunderte GB, Primary + Streaming-Replica + Stage): was eingerichtet war, was wir ändern würden und eine saubere Konfiguration zum Übernehmen.",
    "Kurzfassung: auf jedem PostgreSQL-Server die Erweiterungen installieren, `shared_preload_libraries` setzen (Neustart!), Datenbank `powa` und eine Rolle mit `pg_read_all_stats` anlegen; auf einem Monitoring-Host `powa-archivist` (Repository), `powa-collector` und `powa-web` in Docker; Server mit `powa_register_server()` ohne Passwort registrieren (`.pgpass`); powa-web nur auf localhost hinter nginx oder einem SSH-Tunnel.",
    ["Was PoWA sammelt", "Architektur: Remote-Modus", "1. Die überwachten PostgreSQL-Server", "2. Monitoring-Host in Docker", "3. Weboberfläche und Prüfung", "Worauf man bei Odoo schaut", "Gefunden in einer echten Einrichtung", "Last"],
    "Seit PoWA 4 werden die Snapshots nicht mehr auf dem Produktionsserver selbst gespeichert (lokaler Modus), sondern von einem eigenen **Collector** in einer **Repository**-Datenbank auf einem anderen Host. Vorteile: keine zusätzlichen Schreibvorgänge auf der Produktionsdatenbank, eine Oberfläche für Primary, Replica und Stage, und auch die Replica lässt sich überwachen (sie ist schreibgeschützt und könnte lokal nichts speichern).",
    "Die Statistiken liefern Erweiterungen, die beim Start in PostgreSQL geladen werden. Pakete aus dem PGDG-Repository (apt.postgresql.org); 16 durch die eigene Hauptversion ersetzen. Dieselben `shared_preload_libraries` gehören auch auf die Replica – ihre Konfigurationsdatei ist getrennt, die auf dem Primary angelegten Erweiterungen replizieren automatisch.",
    "Der Collector braucht keinen Superuser: `pg_read_all_stats` erlaubt das Lesen der Statistiken aller Sitzungen, dazu Ausführungsrechte auf die PoWA-Funktionen. Datenbank `powa` und Erweiterungen nur auf dem Primary anlegen – die Replica bekommt sie per Replikation.",
    "Auf dem Monitoring-Host genügen drei Container. Das Beispiel-Compose des PoWA-Projekts enthält zwei zusätzliche Demo-Instanzen (`remote-primary`, `remote-standby`) – die zeigen nur die Oberfläche mit Testdaten und können weg.",
    ["`frequency`: 300 s ist Standard; bei sehr großen Datenbanken mit vielen Abfragen hält 600 s das Repository kleiner.",
     "`retention`: 7–14 Tage genügen für „was war gestern / letzte Woche“; das Repository wächst mit Servern × Abfragen × Snapshots.",
     "`use_server_alias`: die Oberfläche zeigt `prod`/`replica` statt IP-Adressen.",
     "Repository und Collector brauchen keine veröffentlichten Ports – sie sprechen im Compose-Netz."],
    "powa-web meldet sich mit einer PostgreSQL-Rolle (der Repository-Datenbank) an. Es sieht Abfragetexte – samt Literalwerten in WHERE-Bedingungen, also potenziell personenbezogene Daten – und darf daher nicht öffentlich sein.",
    ["**Abfragen je Datenbank** nach Gesamtzeit: typische Odoo-Kandidaten sind `search_read`/`read_group` auf `mail_message`, `mail_followers`, `res_partner` und die Berichte eigener Module.",
     "**Aufrufe vs. Zeit**: Tausende schnelle Abfragen je Anfrage = ein N+1-Problem im Python-Code (fehlendes `prefetch`, `read()` in einer Schleife), kein Datenbankproblem.",
     "**Indexvorschläge** (pg_qualstats + hypopg): mit Odoo abgleichen – einen Index auf ein Feld besser im Modell deklarieren (`index=True` / `index='trigram'` ab Odoo 16) als von Hand anlegen.",
     "**Wartezustände**: `Lock: transactionid`/`tuple` = gleichzeitige Updates derselben Datensätze (Cron-Jobs, Queue-Jobs) – siehe Artikel zu Serialisierungsfehlern; `IO: DataFileRead` = `shared_buffers` / RAM zu klein; `LWLock: WALWrite` = langsame Platte.",
     "**Replica**: schickt Odoo 18/19 Leseanfragen an die Replica, deren Top-Abfragen mit dem Primary vergleichen.",
     "**Verlauf der Einstellungen**: die Wirkung einer Änderung an `work_mem` oder `random_page_cost` ist auf der Zeitachse sichtbar."],
    ["**powa-web auf `0.0.0.0:8888` veröffentlicht** auf einem Host mit öffentlicher IP – die Oberfläche mit allen Abfragetexten war potenziell aus dem Internet erreichbar. Lösung: `127.0.0.1:8888:8888` + nginx mit Passwort oder SSH-Tunnel; dazu die Cloud-Firewall.",
     "**Passwörter der Server in `powa_register_server(... password => '...')`** in der Compose-Datei: im Klartext in der Datei und in der Tabelle `powa_servers`, und das Passwort war ein einfaches Wort. Lösung: kein Passwort im SQL, `.pgpass` im Collector, ein langes Zufallspasswort, rotieren.",
     "**`POSTGRES_HOST_AUTH_METHOD: trust`** für das Repository: jeder im Docker-Netz ist ohne Passwort Superuser. Lösung: `POSTGRES_PASSWORD_FILE`.",
     "**`*-git`-Images** (aus dem Entwicklungszweig gebaut) und drei Kopien der Compose-Datei: veröffentlichte, festgelegte Versionen nutzen (`powa-archivist-16:5.3.0`, `powa-collector:1.3.2`, `powa-web:5.3.1`) und die Datei ohne Geheimnisse in git halten.",
     "**Demo-Instanzen** `remote-primary`/`remote-standby` liefen neben den echten Servern – unnötig, entfernen."],
    "`pg_stat_statements` und `pg_wait_sampling` kosten wenig. `pg_stat_kcache` fügt je Abfrage einen Systemaufruf hinzu – bei Odoos Abfragegrößen vernachlässigbar. `pg_qualstats` ist am teuersten – `sample_rate` niedrig halten (0,01–0,1). Die Snapshots selbst sind ein paar Abfragen alle `frequency` Sekunden. In der Praxis liegt die Last auf einem Odoo-Produktionsserver im niedrigen einstelligen Prozentbereich; zuerst auf Stage testen und mit einem Lasttest vergleichen.",
    "Links")

POWA["t"]["fr"] = _p("fr",
    "PoWA pour PostgreSQL derrière Odoo : installation dans Docker (mode distant), extensions, sécurité et quoi regarder",
    "PoWA (PostgreSQL Workload Analyzer) montre quelles requêtes coûtent le plus, ce que les sessions attendent et quels index manquent – avec historique. Une installation Docker fonctionnelle en mode distant pour un primaire et une réplique, les extensions sur les serveurs de base, un rôle collecteur sans superutilisateur, les mots de passe hors de la table powa_servers, et quoi surveiller avec Odoo.",
    "`pg_stat_activity` montre ce qui tourne **maintenant** ; `pg_stat_statements` montre des totaux depuis la dernière remise à zéro. Quand les utilisateurs signalent « Odoo était lent hier entre 10 h et 11 h », il faut un historique – par requête, avec CPU, disque, attentes et conseils d'index. C'est PoWA. L'article s'appuie sur une vraie supervision d'une grande base Odoo (des centaines de Go, primaire + réplique en streaming + stage) : ce qui était en place, ce que nous changerions et une configuration propre à reprendre.",
    "En bref : sur chaque serveur PostgreSQL, installer les extensions, régler `shared_preload_libraries` (redémarrage !), créer la base `powa` et un rôle avec `pg_read_all_stats` ; sur un hôte de supervision, `powa-archivist` (dépôt), `powa-collector` et `powa-web` dans Docker ; enregistrer les serveurs avec `powa_register_server()` sans mot de passe (`.pgpass`) ; powa-web seulement sur localhost derrière nginx ou un tunnel SSH.",
    ["Ce que PoWA collecte", "Architecture : mode distant", "1. Les serveurs PostgreSQL surveillés", "2. L'hôte de supervision dans Docker", "3. Interface web et vérifications", "Quoi regarder avec Odoo", "Trouvé dans une vraie installation", "Surcoût"],
    "Depuis PoWA 4, les instantanés ne sont plus stockés sur le serveur de production lui-même (mode local), mais par un **collecteur** séparé dans une base **dépôt** sur un autre hôte. Avantages : aucune écriture supplémentaire sur la base de production, une seule interface pour primaire, réplique et stage, et la réplique peut aussi être surveillée (elle est en lecture seule et ne pourrait rien stocker localement).",
    "Les statistiques viennent d'extensions chargées dans PostgreSQL au démarrage. Paquets du dépôt PGDG (apt.postgresql.org) ; remplacer 16 par votre version majeure. Le même `shared_preload_libraries` doit être réglé sur la réplique – son fichier de configuration est séparé, les extensions créées sur le primaire se répliquent automatiquement.",
    "Le collecteur n'a pas besoin de superutilisateur : `pg_read_all_stats` permet de lire les statistiques de toutes les sessions, plus le droit d'exécuter les fonctions PoWA. Créer la base `powa` et les extensions seulement sur le primaire – la réplique les reçoit par réplication.",
    "Sur l'hôte de supervision, trois conteneurs suffisent. Le compose d'exemple du projet PoWA contient deux instances de démonstration en plus (`remote-primary`, `remote-standby`) – elles ne servent qu'à montrer l'interface avec des données de test et peuvent être supprimées.",
    ["`frequency` : 300 s par défaut ; avec de très grosses bases et beaucoup de requêtes, 600 s garde le dépôt plus petit.",
     "`retention` : 7 à 14 jours suffisent pour répondre à « que s'est-il passé hier / la semaine dernière » ; le dépôt grossit avec serveurs × requêtes × instantanés.",
     "`use_server_alias` : l'interface affiche `prod`/`replica` au lieu des adresses IP.",
     "Le dépôt et le collecteur n'ont besoin d'aucun port publié – ils communiquent dans le réseau du compose."],
    "powa-web se connecte avec un rôle PostgreSQL (de la base dépôt). Il voit les textes des requêtes – y compris les valeurs littérales des clauses WHERE, donc potentiellement des données personnelles – et ne doit donc pas être public.",
    ["**Requêtes par base** triées par temps total : les candidats typiques d'Odoo sont `search_read`/`read_group` sur `mail_message`, `mail_followers`, `res_partner` et les rapports des modules personnalisés.",
     "**Appels vs temps** : des milliers de requêtes rapides par requête HTTP = un problème N+1 dans le code Python (`prefetch` manquant, `read()` dans une boucle), pas un problème de base.",
     "**Suggestions d'index** (pg_qualstats + hypopg) : les confronter à Odoo – mieux vaut déclarer un index sur un champ dans le modèle (`index=True` / `index='trigram'` depuis Odoo 16) que le créer à la main.",
     "**Attentes** : `Lock: transactionid`/`tuple` = mises à jour concurrentes des mêmes enregistrements (crons, queue jobs) – voir l'article sur les erreurs de sérialisation ; `IO: DataFileRead` = `shared_buffers` / RAM trop petits ; `LWLock: WALWrite` = disque lent.",
     "**Réplique** : si Odoo 18/19 envoie les requêtes en lecture seule à la réplique, comparer ses requêtes principales avec celles du primaire.",
     "**Historique des réglages** : l'effet d'un changement de `work_mem` ou `random_page_cost` se voit sur la chronologie."],
    ["**powa-web publié sur `0.0.0.0:8888`** sur un hôte avec IP publique – l'interface avec tous les textes de requêtes était potentiellement accessible depuis Internet. Correction : `127.0.0.1:8888:8888` + nginx avec mot de passe ou tunnel SSH ; et le pare-feu du cloud.",
     "**Mots de passe des serveurs dans `powa_register_server(... password => '...')`** dans le fichier compose : en clair dans le fichier et dans la table `powa_servers`, et le mot de passe était un simple mot. Correction : pas de mot de passe dans le SQL, `.pgpass` dans le collecteur, un long mot de passe aléatoire, à renouveler.",
     "**`POSTGRES_HOST_AUTH_METHOD: trust`** pour le dépôt : n'importe qui dans le réseau Docker devient superutilisateur sans mot de passe. Correction : `POSTGRES_PASSWORD_FILE`.",
     "**Images `*-git`** (construites depuis la branche de développement) et trois copies du fichier compose : utiliser des versions publiées et figées (`powa-archivist-16:5.3.0`, `powa-collector:1.3.2`, `powa-web:5.3.1`) et garder le fichier dans git sans secrets.",
     "**Instances de démo** `remote-primary`/`remote-standby` tournant à côté des vrais serveurs – inutiles, à supprimer."],
    "`pg_stat_statements` et `pg_wait_sampling` coûtent peu. `pg_stat_kcache` ajoute un appel système par requête – négligeable pour la taille des requêtes d'Odoo. `pg_qualstats` est le plus coûteux – garder `sample_rate` bas (0,01–0,1). Les instantanés eux-mêmes sont quelques requêtes toutes les `frequency` secondes. En pratique, le surcoût sur un serveur Odoo de production reste de quelques pour cent au plus ; tester d'abord sur stage et comparer avec un test de charge.",
    "Liens")

POWA["t"]["el"] = _p("el",
    "PoWA για PostgreSQL πίσω από Odoo: εγκατάσταση σε Docker (remote mode), επεκτάσεις, ασφάλεια και τι κοιτάμε",
    "Το PoWA (PostgreSQL Workload Analyzer) δείχνει ποια ερωτήματα κοστίζουν περισσότερο, τι περιμένουν οι συνεδρίες και ποια ευρετήρια λείπουν – με ιστορικό. Μια λειτουργική εγκατάσταση Docker σε remote mode για primary και replica, οι επεκτάσεις στους servers της βάσης, ρόλος collector χωρίς superuser, κωδικοί εκτός του πίνακα powa_servers και τι να προσέχετε με το Odoo.",
    "Το `pg_stat_activity` δείχνει τι τρέχει **τώρα**· το `pg_stat_statements` δείχνει σύνολα από τον τελευταίο μηδενισμό. Όταν οι χρήστες λένε «το Odoo ήταν αργό χθες μεταξύ 10 και 11», χρειάζεστε ιστορικό – ανά ερώτημα, με CPU, δίσκο, αναμονές και προτάσεις ευρετηρίων. Αυτό είναι το PoWA. Το άρθρο βασίζεται σε πραγματική παρακολούθηση μιας μεγάλης βάσης Odoo (εκατοντάδες GB, primary + streaming replica + stage): τι είχε στηθεί, τι θα αλλάζαμε και μια καθαρή ρύθμιση για αντιγραφή.",
    "Συνοπτικά: σε κάθε server PostgreSQL εγκαταστήστε τις επεκτάσεις, ορίστε `shared_preload_libraries` (επανεκκίνηση!), δημιουργήστε τη βάση `powa` και έναν ρόλο με `pg_read_all_stats`· σε έναν host παρακολούθησης τρέξτε `powa-archivist` (repository), `powa-collector` και `powa-web` σε Docker· καταχωρίστε τους servers με `powa_register_server()` χωρίς κωδικό (`.pgpass`)· το powa-web μόνο σε localhost πίσω από nginx ή SSH tunnel.",
    ["Τι συλλέγει το PoWA", "Αρχιτεκτονική: remote mode", "1. Οι παρακολουθούμενοι servers PostgreSQL", "2. Host παρακολούθησης σε Docker", "3. Web UI και έλεγχοι", "Τι κοιτάμε με το Odoo", "Ευρήματα σε πραγματική εγκατάσταση", "Επιβάρυνση"],
    "Από το PoWA 4 τα snapshots δεν αποθηκεύονται πια στον ίδιο τον server παραγωγής (local mode), αλλά από έναν ξεχωριστό **collector** σε μια βάση **repository** σε άλλο host. Πλεονεκτήματα: καμία επιπλέον εγγραφή στη βάση παραγωγής, ένα UI για primary, replica και stage, και μπορεί να παρακολουθηθεί και η replica (είναι μόνο για ανάγνωση και δεν θα μπορούσε να αποθηκεύσει τίποτα τοπικά).",
    "Τα στατιστικά τα παράγουν επεκτάσεις που φορτώνονται στο PostgreSQL κατά την εκκίνηση. Πακέτα από το αποθετήριο PGDG (apt.postgresql.org)· αντικαταστήστε το 16 με τη δική σας κύρια έκδοση. Το ίδιο `shared_preload_libraries` χρειάζεται και στη replica – το αρχείο ρυθμίσεών της είναι ξεχωριστό, οι επεκτάσεις που δημιουργούνται στο primary αναπαράγονται αυτόματα.",
    "Ο collector δεν χρειάζεται superuser: το `pg_read_all_stats` επιτρέπει την ανάγνωση των στατιστικών όλων των συνεδριών, μαζί με δικαίωμα εκτέλεσης των συναρτήσεων του PoWA. Δημιουργήστε τη βάση `powa` και τις επεκτάσεις μόνο στο primary – η replica τις λαμβάνει μέσω αναπαραγωγής.",
    "Στον host παρακολούθησης αρκούν τρία containers. Το παράδειγμα compose του έργου PoWA περιέχει δύο επιπλέον instances επίδειξης (`remote-primary`, `remote-standby`) – υπάρχουν μόνο για να δείξουν το UI με δοκιμαστικά δεδομένα και μπορούν να αφαιρεθούν.",
    ["`frequency`: 300 s είναι η προεπιλογή· σε πολύ μεγάλες βάσεις με πολλά ερωτήματα, τα 600 s κρατούν το repository μικρότερο.",
     "`retention`: 7–14 ημέρες αρκούν για το «τι έγινε χθες / την περασμένη εβδομάδα»· το repository μεγαλώνει με servers × ερωτήματα × snapshots.",
     "`use_server_alias`: το UI δείχνει `prod`/`replica` αντί για διευθύνσεις IP.",
     "Repository και collector δεν χρειάζονται δημοσιευμένες θύρες – επικοινωνούν μέσα στο δίκτυο του compose."],
    "Το powa-web συνδέεται με έναν ρόλο PostgreSQL (της βάσης repository). Βλέπει κείμενα ερωτημάτων – μαζί με τιμές στις συνθήκες WHERE, άρα πιθανώς προσωπικά δεδομένα – γι' αυτό δεν πρέπει να είναι δημόσιο.",
    ["**Ερωτήματα ανά βάση** ταξινομημένα κατά συνολικό χρόνο: τυπικοί υποψήφιοι στο Odoo είναι `search_read`/`read_group` σε `mail_message`, `mail_followers`, `res_partner` και οι αναφορές δικών σας modules.",
     "**Κλήσεις vs χρόνος**: χιλιάδες γρήγορα ερωτήματα ανά αίτημα = πρόβλημα N+1 στον κώδικα Python (λείπει `prefetch`, `read()` μέσα σε βρόχο), όχι πρόβλημα βάσης.",
     "**Προτάσεις ευρετηρίων** (pg_qualstats + hypopg): ελέγξτε τες απέναντι στο Odoo – ένα ευρετήριο σε πεδίο καλύτερα δηλώνεται στο μοντέλο (`index=True` / `index='trigram'` από Odoo 16) παρά δημιουργείται με το χέρι.",
     "**Αναμονές**: `Lock: transactionid`/`tuple` = ταυτόχρονες ενημερώσεις των ίδιων εγγραφών (crons, queue jobs) – βλ. άρθρο για σφάλματα serialization· `IO: DataFileRead` = μικρά `shared_buffers` / RAM· `LWLock: WALWrite` = αργός δίσκος.",
     "**Replica**: αν το Odoo 18/19 στέλνει αιτήματα ανάγνωσης στη replica, συγκρίνετε τα κορυφαία ερωτήματά της με του primary.",
     "**Ιστορικό ρυθμίσεων**: η επίδραση μιας αλλαγής στο `work_mem` ή στο `random_page_cost` φαίνεται στη χρονογραμμή."],
    ["**powa-web δημοσιευμένο στο `0.0.0.0:8888`** σε host με δημόσια IP – το UI με όλα τα κείμενα ερωτημάτων ήταν πιθανώς προσβάσιμο από το διαδίκτυο. Λύση: `127.0.0.1:8888:8888` + nginx με κωδικό ή SSH tunnel· και το firewall του cloud.",
     "**Κωδικοί των servers στο `powa_register_server(... password => '...')`** μέσα στο αρχείο compose: σε απλό κείμενο στο αρχείο και στον πίνακα `powa_servers`, και ο κωδικός ήταν μια απλή λέξη. Λύση: κανένας κωδικός στο SQL, `.pgpass` στον collector, μακρύς τυχαίος κωδικός, εναλλαγή.",
     "**`POSTGRES_HOST_AUTH_METHOD: trust`** για το repository: οποιοσδήποτε στο δίκτυο Docker γίνεται superuser χωρίς κωδικό. Λύση: `POSTGRES_PASSWORD_FILE`.",
     "**Images `*-git`** (από τον κλάδο ανάπτυξης) και τρία αντίγραφα του αρχείου compose: χρησιμοποιήστε δημοσιευμένες, καρφωμένες εκδόσεις (`powa-archivist-16:5.3.0`, `powa-collector:1.3.2`, `powa-web:5.3.1`) και κρατήστε το αρχείο σε git χωρίς μυστικά.",
     "**Instances επίδειξης** `remote-primary`/`remote-standby` έτρεχαν δίπλα στους πραγματικούς servers – δεν χρειάζονται, αφαιρέστε τα."],
    "Τα `pg_stat_statements` και `pg_wait_sampling` κοστίζουν λίγο. Το `pg_stat_kcache` προσθέτει μία κλήση συστήματος ανά ερώτημα – αμελητέο για τα μεγέθη ερωτημάτων του Odoo. Το `pg_qualstats` είναι το ακριβότερο – κρατήστε χαμηλό το `sample_rate` (0,01–0,1). Τα ίδια τα snapshots είναι λίγα ερωτήματα κάθε `frequency` δευτερόλεπτα. Στην πράξη η επιβάρυνση σε server παραγωγής Odoo είναι μερικά τοις εκατό το πολύ· δοκιμάστε πρώτα σε stage και συγκρίνετε με δοκιμή φορτίου.",
    "Σύνδεσμοι")

POWA["t"]["uk"] = _p("uk",
    "PoWA для PostgreSQL за Odoo: налаштування в Docker (remote mode), розширення, безпека і що дивитися",
    "PoWA (PostgreSQL Workload Analyzer) показує, які запити коштують найдорожче, на що чекають сесії і яких індексів бракує, причому з історією. Робоче налаштування Docker у remote mode для primary і репліки, розширення на серверах БД, роль collector без superuser, паролі поза таблицею powa_servers і на що дивитися з Odoo.",
    "`pg_stat_activity` показує, що виконується **зараз**, а `pg_stat_statements` — підсумки з останнього скидання. Коли користувачі кажуть «Odoo вчора гальмував між 10 і 11», потрібна історія: по кожному запиту, з CPU, диском, очікуваннями й порадами щодо індексів. Саме це дає PoWA. Стаття спирається на реальний моніторинг великої бази Odoo (сотні ГБ, primary + streaming-репліка + stage): що було налаштовано, що ми змінили б і чиста конфігурація, яку можна взяти за основу.",
    "Коротко: на кожному сервері PostgreSQL встановіть розширення, задайте `shared_preload_libraries` (потрібен перезапуск!), створіть базу `powa` і роль з `pg_read_all_stats`. На хості моніторингу запустіть у Docker `powa-archivist` (репозиторій), `powa-collector` і `powa-web`. Сервери реєструйте через `powa_register_server()` без пароля, а паролі тримайте в `.pgpass`. powa-web публікуйте лише на localhost за nginx або SSH-тунелем.",
    ["Що збирає PoWA", "Архітектура: remote mode", "1. Сервери PostgreSQL, за якими стежимо", "2. Хост моніторингу в Docker", "3. Веб-інтерфейс і перевірка", "На що дивитися з Odoo", "Що знайшли в реальному налаштуванні", "Навантаження"],
    "Починаючи з PoWA 4, знімки зберігаються не на самому робочому сервері (local mode), а окремим **collector** у базі **repository** на іншому хості. Переваги: жодних додаткових записів у робочу базу, один інтерфейс для primary, репліки і stage, і можна стежити навіть за реплікою (вона лише для читання й не могла б нічого зберігати локально).",
    "Статистику збирають розширення, які PostgreSQL завантажує під час старту. Пакети беремо з репозиторію PGDG (apt.postgresql.org), а 16 замінюємо на свою основну версію. Той самий `shared_preload_libraries` потрібен і на репліці: її конфіг окремий, а розширення, створені на primary, реплікуються самі.",
    "Collector не потребує superuser: `pg_read_all_stats` дає читати статистику всіх сесій, плюс потрібне право виконувати функції PoWA. Базу `powa` і розширення створюйте лише на primary, репліка отримає їх через реплікацію.",
    "На хості моніторингу достатньо трьох контейнерів. Приклад compose від проєкту PoWA містить ще два демо-інстанси (`remote-primary`, `remote-standby`). Вони лише показують інтерфейс на тестових даних, тож їх можна прибрати.",
    ["`frequency`: стандартно 300 с; для дуже великих баз з великою кількістю запитів 600 с тримає репозиторій меншим.",
     "`retention`: 7–14 днів достатньо, щоб відповісти на «що було вчора / минулого тижня». Репозиторій росте пропорційно серверам × запитам × знімкам.",
     "`use_server_alias`: інтерфейс показує `prod`/`replica` замість IP-адрес.",
     "Repository і collector не потребують опублікованих портів, вони спілкуються всередині мережі compose."],
    "powa-web входить під роллю PostgreSQL (бази repository). Він бачить тексти запитів разом зі значеннями в умовах WHERE, тобто потенційно персональні дані, тому не має бути публічним.",
    ["**Запити по базі**, відсортовані за загальним часом: типові кандидати в Odoo — `search_read`/`read_group` по `mail_message`, `mail_followers`, `res_partner` і звіти власних модулів.",
     "**Виклики проти часу**: тисячі швидких запитів на один HTTP-запит означають проблему N+1 у Python-коді (бракує `prefetch`, `read()` у циклі), а не проблему бази.",
     "**Поради щодо індексів** (pg_qualstats + hypopg): звіряйте їх з Odoo. Індекс на поле краще оголосити в моделі (`index=True` / `index='trigram'` з Odoo 16), ніж створювати вручну.",
     "**Очікування**: `Lock: transactionid`/`tuple` означає конкурентні оновлення тих самих записів (крони, queue jobs), див. статтю про помилки serialization. `IO: DataFileRead` означає замалі `shared_buffers` / RAM, а `LWLock: WALWrite` — повільний диск.",
     "**Репліка**: якщо Odoo 18/19 відправляє запити на читання на репліку, порівняйте її топ запитів з primary.",
     "**Історія налаштувань**: ефект зміни `work_mem` або `random_page_cost` видно на часовій шкалі."],
    ["**powa-web опублікований на `0.0.0.0:8888`** на хості з публічною IP. Інтерфейс з усіма текстами запитів потенційно був доступний з інтернету. Виправлення: `127.0.0.1:8888:8888` + nginx з паролем або SSH-тунель, а також хмарний firewall.",
     "**Паролі серверів у `powa_register_server(... password => '...')`** прямо в compose-файлі. Вони лежали відкритим текстом і у файлі, і в таблиці `powa_servers`, а сам пароль був простим словом. Виправлення: жодних паролів у SQL, `.pgpass` у collector, довгий випадковий пароль і ротація.",
     "**`POSTGRES_HOST_AUTH_METHOD: trust`** для repository: будь-хто в мережі Docker стає superuser без пароля. Виправлення: `POSTGRES_PASSWORD_FILE`.",
     "**Образи `*-git`** (зібрані з гілки розробки) і три копії compose-файлу. Краще брати випущені й зафіксовані версії (`powa-archivist-16:5.3.0`, `powa-collector:1.3.2`, `powa-web:5.3.1`) і тримати файл у git без секретів.",
     "**Демо-інстанси** `remote-primary`/`remote-standby` працювали поруч зі справжніми серверами; вони не потрібні, їх варто прибрати."],
    "`pg_stat_statements` і `pg_wait_sampling` коштують мало. `pg_stat_kcache` додає один системний виклик на запит, що для розміру запитів Odoo непомітно. Найдорожчий — `pg_qualstats`, тому тримайте `sample_rate` низьким (0,01–0,1). Самі знімки — це кілька запитів кожні `frequency` секунд. На практиці навантаження на робочий сервер Odoo в межах кількох відсотків. Спершу перевірте на stage і порівняйте з навантажувальним тестом.",
    "Посилання")

POWA["t"]["ru"] = _p("ru",
    "PoWA для PostgreSQL за Odoo: настройка в Docker (remote mode), расширения, безопасность и что смотреть",
    "PoWA (PostgreSQL Workload Analyzer) показывает, какие запросы обходятся дороже всего, чего ждут сессии и каких индексов не хватает, причём с историей. Рабочая настройка Docker в remote mode для primary и реплики, расширения на серверах БД, роль collector без superuser, пароли вне таблицы powa_servers и на что смотреть с Odoo.",
    "`pg_stat_activity` показывает, что выполняется **сейчас**, а `pg_stat_statements` — итоги с последнего сброса. Когда пользователи говорят «Odoo вчера тормозил с 10 до 11», нужна история: по каждому запросу, с CPU, диском, ожиданиями и советами по индексам. Именно это даёт PoWA. Статья основана на реальном мониторинге большой базы Odoo (сотни ГБ, primary + streaming-реплика + stage): что было настроено, что мы бы поменяли и чистая конфигурация, которую можно взять за основу.",
    "Коротко: на каждом сервере PostgreSQL поставьте расширения, задайте `shared_preload_libraries` (нужен перезапуск!), создайте базу `powa` и роль с `pg_read_all_stats`. На хосте мониторинга запустите в Docker `powa-archivist` (репозиторий), `powa-collector` и `powa-web`. Серверы регистрируйте через `powa_register_server()` без пароля, а пароли держите в `.pgpass`. powa-web публикуйте только на localhost за nginx или SSH-туннелем.",
    ["Что собирает PoWA", "Архитектура: remote mode", "1. Серверы PostgreSQL, за которыми следим", "2. Хост мониторинга в Docker", "3. Веб-интерфейс и проверка", "На что смотреть с Odoo", "Что нашли в реальной настройке", "Нагрузка"],
    "Начиная с PoWA 4, снимки хранятся не на самом рабочем сервере (local mode), а отдельным **collector** в базе **repository** на другом хосте. Плюсы: никаких дополнительных записей в рабочую базу, один интерфейс для primary, реплики и stage, и можно следить даже за репликой (она только для чтения и не смогла бы ничего хранить локально).",
    "Статистику собирают расширения, которые PostgreSQL загружает при старте. Пакеты берём из репозитория PGDG (apt.postgresql.org), а 16 заменяем на свою основную версию. Тот же `shared_preload_libraries` нужен и на реплике: её конфиг отдельный, а расширения, созданные на primary, реплицируются сами.",
    "Collector не нужен superuser: `pg_read_all_stats` даёт читать статистику всех сессий, плюс нужно право выполнять функции PoWA. Базу `powa` и расширения создавайте только на primary, реплика получит их через репликацию.",
    "На хосте мониторинга достаточно трёх контейнеров. Пример compose от проекта PoWA содержит ещё два демо-инстанса (`remote-primary`, `remote-standby`). Они только показывают интерфейс на тестовых данных, так что их можно убрать.",
    ["`frequency`: по умолчанию 300 с; для очень больших баз с большим числом запросов 600 с держит репозиторий меньше.",
     "`retention`: 7–14 дней хватает, чтобы ответить на «что было вчера / на прошлой неделе». Репозиторий растёт пропорционально серверам × запросам × снимкам.",
     "`use_server_alias`: интерфейс показывает `prod`/`replica` вместо IP-адресов.",
     "Repository и collector не нужны опубликованные порты, они общаются внутри сети compose."],
    "powa-web входит под ролью PostgreSQL (базы repository). Он видит тексты запросов вместе со значениями в условиях WHERE, то есть потенциально персональные данные, поэтому не должен быть публичным.",
    ["**Запросы по базе**, отсортированные по общему времени: типичные кандидаты в Odoo — `search_read`/`read_group` по `mail_message`, `mail_followers`, `res_partner` и отчёты своих модулей.",
     "**Вызовы против времени**: тысячи быстрых запросов на один HTTP-запрос означают проблему N+1 в Python-коде (нет `prefetch`, `read()` в цикле), а не проблему базы.",
     "**Советы по индексам** (pg_qualstats + hypopg): сверяйте их с Odoo. Индекс на поле лучше объявить в модели (`index=True` / `index='trigram'` с Odoo 16), чем создавать руками.",
     "**Ожидания**: `Lock: transactionid`/`tuple` означает конкурентные обновления одних и тех же записей (кроны, queue jobs), см. статью про ошибки serialization. `IO: DataFileRead` означает маленькие `shared_buffers` / RAM, а `LWLock: WALWrite` — медленный диск.",
     "**Реплика**: если Odoo 18/19 отправляет запросы на чтение на реплику, сравните её топ запросов с primary.",
     "**История настроек**: эффект изменения `work_mem` или `random_page_cost` виден на временной шкале."],
    ["**powa-web опубликован на `0.0.0.0:8888`** на хосте с публичным IP. Интерфейс со всеми текстами запросов потенциально был доступен из интернета. Исправление: `127.0.0.1:8888:8888` + nginx с паролем или SSH-туннель, а также облачный firewall.",
     "**Пароли серверов в `powa_register_server(... password => '...')`** прямо в compose-файле. Они лежали открытым текстом и в файле, и в таблице `powa_servers`, а сам пароль был простым словом. Исправление: никаких паролей в SQL, `.pgpass` в collector, длинный случайный пароль и ротация.",
     "**`POSTGRES_HOST_AUTH_METHOD: trust`** для repository: любой в сети Docker становится superuser без пароля. Исправление: `POSTGRES_PASSWORD_FILE`.",
     "**Образы `*-git`** (собраны из ветки разработки) и три копии compose-файла. Лучше брать выпущенные и зафиксированные версии (`powa-archivist-16:5.3.0`, `powa-collector:1.3.2`, `powa-web:5.3.1`) и держать файл в git без секретов.",
     "**Демо-инстансы** `remote-primary`/`remote-standby` работали рядом с настоящими серверами; они не нужны, их стоит убрать."],
    "`pg_stat_statements` и `pg_wait_sampling` стоят мало. `pg_stat_kcache` добавляет один системный вызов на запрос, что для размера запросов Odoo незаметно. Самый дорогой — `pg_qualstats`, поэтому держите `sample_rate` низким (0,01–0,1). Сами снимки — это несколько запросов каждые `frequency` секунд. На практике нагрузка на рабочий сервер Odoo в пределах нескольких процентов. Сначала проверьте на stage и сравните с нагрузочным тестом.",
    "Ссылки")
