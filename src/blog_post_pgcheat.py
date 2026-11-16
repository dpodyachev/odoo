# Статья 16: шпаргалка PostgreSQL для администратора Odoo (бэкап/восстановление, web/curl, размеры, пользователи и права,
# пароли, запросы и kill, vacuum, EXPLAIN, индексы, настройки vs воркеры Odoo, pgtune/pgconfig, калькулятор). Все 6 языков.

PGCHEAT = {
    "slug": "postgresql-odoo-admin-cheat-sheet",
    "date": "2026-11-16",
    "tags": ["PostgreSQL", "Odoo", "psql", "Backup", "Performance", "Cheat sheet"],
    "code": {
        "connect": ("psql · connect and look around", """sudo -u postgres psql                          # as superuser on the DB server (peer auth)
psql -h 10.0.0.10 -U odoo -d mydb             # over the network (password from ~/.pgpass)
docker compose exec db psql -U odoo -d mydb   # PostgreSQL in docker compose

\\l+            -- databases with size, owner, encoding
\\c mydb        -- switch database
\\dt+           -- tables with size        \\dt+ res_*   -- with a pattern
\\d+ res_partner -- columns, indexes, constraints, triggers of one table
\\di+ res_partner* -- indexes with size
\\du            -- roles (users) and their rights
\\x auto        -- wide rows vertically     \\timing on  -- show query duration
\\q             -- quit"""),
        "sizes": ("sql · database and table sizes", """-- databases, biggest first
SELECT datname, pg_size_pretty(pg_database_size(datname)) AS size
  FROM pg_database ORDER BY pg_database_size(datname) DESC;

-- top 10 tables (data + indexes + TOAST)
SELECT relname AS table,
       pg_size_pretty(pg_total_relation_size(relid)) AS total,
       pg_size_pretty(pg_relation_size(relid))       AS data,
       pg_size_pretty(pg_indexes_size(relid))        AS indexes,
       n_live_tup AS rows
  FROM pg_stat_user_tables
 ORDER BY pg_total_relation_size(relid) DESC
 LIMIT 10;"""),
        "dump": ("bash · backup: pg_dump, pg_dumpall, pg_basebackup", """# one database, custom format (compressed, selective restore, parallel restore)
pg_dump -U odoo -Fc -f mydb_$(date +%F).dump mydb

# very large database: directory format, 4 parallel jobs
pg_dump -U odoo -Fd -j 4 -f mydb_$(date +%F).dir mydb

# without owner and grants (restore under any role)
pg_dump -U odoo -Fc --no-owner --no-acl -f mydb.dump mydb

# roles and their passwords – NOT included in pg_dump
sudo -u postgres pg_dumpall --globals-only > globals.sql

# physical copy of the whole cluster (all databases, for a replica or PITR)
sudo -u postgres pg_basebackup -D /backup/base_$(date +%F) -Ft -z -X stream -P

# Odoo also needs the filestore (attachments) – same moment as the dump
tar -C /var/lib/odoo/filestore -czf filestore_mydb_$(date +%F).tgz mydb"""),
        "restore": ("bash · restore: pg_restore and psql", """createdb -U odoo -O odoo mydb_restored
pg_restore -U odoo -d mydb_restored --no-owner --no-acl -j 4 mydb.dump 2> restore.log
grep -c ERROR restore.log                       # must be 0 – pg_restore continues after errors!

# plain SQL dump (e.g. dump.sql from an Odoo zip backup)
psql -U odoo -d mydb_restored -v ON_ERROR_STOP=1 -f dump.sql

# statistics are not in the dump – collect them right away
vacuumdb -U odoo -d mydb_restored --analyze-in-stages

# filestore folder must be named like the database
tar -C /var/lib/odoo/filestore -xzf filestore_mydb.tgz && mv /var/lib/odoo/filestore/mydb /var/lib/odoo/filestore/mydb_restored"""),
        "web": ("bash · backup and restore through Odoo (web / curl)", """# browser: https://erp.example.com/web/database/manager  (needs list_db = True and the master password)

# backup as zip (dump.sql + filestore + manifest.json) or as dump (database only)
curl -sS -X POST https://erp.example.com/web/database/backup \\
     -F "master_pwd=$ODOO_MASTER" -F "name=mydb" -F "backup_format=zip" \\
     -o mydb_$(date +%F).zip

# restore under a new name; copy=true = new database UUID (for a copy next to the original)
curl -sS -X POST https://erp.example.com/web/database/restore \\
     -F "master_pwd=$ODOO_MASTER" -F "name=mydb_copy" -F "copy=true" \\
     -F "backup_file=@mydb_2026-11-16.zip"

# list databases (JSON-RPC)
curl -sS -H 'Content-Type: application/json' \\
     -d '{"jsonrpc":"2.0","method":"call","params":{}}' https://erp.example.com/web/database/list

# ODOO_MASTER from a file, not typed into the shell history:  ODOO_MASTER=$(cat ~/.odoo_master)"""),
        "roles": ("sql / bash · users, databases, rights", """-- a role for Odoo: may create databases, is NOT a superuser
CREATE ROLE odoo LOGIN CREATEDB PASSWORD 'change-me';      -- or: sudo -u postgres createuser -P --createdb odoo

-- database owned by Odoo's role
CREATE DATABASE mydb OWNER odoo ENCODING 'UTF8' TEMPLATE template0;   -- or: createdb -O odoo mydb
DROP DATABASE mydb_old WITH (FORCE);                       -- PostgreSQL 13+, or: dropdb --force mydb_old

-- after a restore under another role: hand everything over to odoo (run inside the database)
ALTER DATABASE mydb OWNER TO odoo;
REASSIGN OWNED BY old_owner TO odoo;

-- read-only user for reports / BI
CREATE ROLE report LOGIN PASSWORD 'change-me';
GRANT CONNECT ON DATABASE mydb TO report;
GRANT USAGE ON SCHEMA public TO report;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO report;
ALTER DEFAULT PRIVILEGES FOR ROLE odoo IN SCHEMA public GRANT SELECT ON TABLES TO report;

DROP ROLE report;                                          -- before: REASSIGN/DROP OWNED BY report;"""),
        "passwd": ("passwords: PostgreSQL role and Odoo user", """-- PostgreSQL role (interactive, password not in the history)
sudo -u postgres psql -c '\\password odoo'
-- or in SQL (lands in the log/history – avoid on shared servers)
ALTER ROLE odoo PASSWORD 'new-long-password';
-- then the same value in odoo.conf: db_password = ...

# Odoo user (e.g. admin with id 2) – through Odoo, so the hash is correct
docker compose run --rm odoo odoo shell -c /etc/odoo/odoo.conf -d mydb --no-http <<'EOF'
user = env['res.users'].browse(2)
user.password = 'new-long-password'
env.cr.commit()
EOF
# master password (database manager): admin_passwd in odoo.conf, restart Odoo"""),
        "activity": ("sql · what is running – and stopping long queries", """-- running queries, longest first
SELECT pid, usename, application_name, client_addr, state,
       now() - xact_start  AS tx_age,
       now() - query_start AS query_age,
       wait_event_type, wait_event, left(query, 120) AS query
  FROM pg_stat_activity
 WHERE datname = current_database() AND state <> 'idle'
 ORDER BY query_start;

-- cancel one query (gentle) / end the session (hard)
SELECT pg_cancel_backend(12345);
SELECT pg_terminate_backend(12345);

-- end everything running longer than 20 minutes (look at the list first!)
SELECT pid, now() - query_start AS age, pg_terminate_backend(pid)
  FROM pg_stat_activity
 WHERE datname = current_database()
   AND state IN ('active', 'idle in transaction')
   AND now() - query_start > interval '20 minutes'
   AND pid <> pg_backend_pid();

-- safety net in postgresql.conf instead of manual killing
-- idle_in_transaction_session_timeout = '30min'"""),
        "vacuum": ("sql · vacuum and health", """-- tables with many dead rows and when autovacuum last ran
SELECT relname, n_live_tup, n_dead_tup,
       round(100.0 * n_dead_tup / greatest(n_live_tup, 1), 1) AS dead_pct,
       last_autovacuum, last_autoanalyze
  FROM pg_stat_user_tables ORDER BY n_dead_tup DESC LIMIT 15;

VACUUM (VERBOSE, ANALYZE) mail_message;   -- online, no lock for readers/writers
ANALYZE;                                  -- fresh statistics (after restore, big imports)
VACUUM FULL mail_message;                 -- rewrites the table: EXCLUSIVE LOCK – only in a maintenance window
-- online alternative to VACUUM FULL: the pg_repack extension

-- big Odoo tables: vacuum earlier than the default 20 %
ALTER TABLE mail_message SET (autovacuum_vacuum_scale_factor = 0.02, autovacuum_analyze_scale_factor = 0.01);

-- transaction ID wraparound: watch the age (alarm above ~1.5 billion)
SELECT datname, age(datfrozenxid) FROM pg_database ORDER BY 2 DESC;"""),
        "explain": ("sql · slow queries: pg_stat_statements and EXPLAIN ANALYZE", """-- top queries by total time (shared_preload_libraries = 'pg_stat_statements', then CREATE EXTENSION)
SELECT round(total_exec_time) AS total_ms, calls, round(mean_exec_time, 1) AS avg_ms, left(query, 150)
  FROM pg_stat_statements ORDER BY total_exec_time DESC LIMIT 10;

-- execute and measure one query (ANALYZE really runs it – wrap writes in BEGIN … ROLLBACK)
EXPLAIN (ANALYZE, BUFFERS)
SELECT id FROM sale_order WHERE partner_id = 4711 AND state = 'sale' ORDER BY date_order DESC LIMIT 80;

-- what to look for in the plan:
--   Seq Scan on a big table + "Rows Removed by Filter: 1000000"  -> index candidate
--   estimated rows=1 vs actual rows=50000                        -> stale statistics: ANALYZE
--   Sort Method: external merge  Disk: …                         -> work_mem too small for this query
--   Buffers: shared read=… (high)                                -> data not in cache (RAM / shared_buffers)
-- readable visualisation: explain.dalibo.com"""),
        "indexes": ("sql · which columns have which indexes", """\\d+ sale_order          -- in psql: everything incl. indexes
\\di+ sale_order*        -- indexes with size

-- indexes of a table with their columns
SELECT indexname, indexdef FROM pg_indexes WHERE tablename = 'sale_order' ORDER BY 1;

-- is a given column indexed?
SELECT i.relname AS index, a.attname AS column
  FROM pg_index x
  JOIN pg_class i ON i.oid = x.indexrelid
  JOIN pg_class t ON t.oid = x.indrelid
  JOIN pg_attribute a ON a.attrelid = t.oid AND a.attnum = ANY (x.indkey)
 WHERE t.relname = 'sale_order' AND a.attname = 'partner_id';

-- unused indexes (since the last statistics reset) – cost on every write
SELECT relname, indexrelname, idx_scan, pg_size_pretty(pg_relation_size(indexrelid)) AS size
  FROM pg_stat_user_indexes WHERE idx_scan = 0 ORDER BY pg_relation_size(indexrelid) DESC LIMIT 15;

-- create without blocking writes
CREATE INDEX CONCURRENTLY sale_order_partner_state_idx ON sale_order (partner_id, state);"""),
        "exA": ("postgresql.conf · example A: 8 GB / 4 CPU, Odoo and PostgreSQL on one server, ~25 users", """# odoo.conf: workers = 6, max_cron_threads = 2, limit_memory_soft = 2 GB, limit_memory_hard = 2.5 GB
# RAM: ~1.4 GB system, ~2.3 GB Odoo workers (average), 4 GB for PostgreSQL
max_connections = 100
shared_buffers = 1GB
effective_cache_size = 3GB
maintenance_work_mem = 256MB
work_mem = 4MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
min_wal_size = 1GB
max_wal_size = 4GB
random_page_cost = 1.1
effective_io_concurrency = 200
max_worker_processes = 4
max_parallel_workers_per_gather = 2
max_parallel_workers = 4
jit = off"""),
        "exB": ("postgresql.conf · example B: dedicated DB server 32 GB / 8 CPU, ~100 users", """# odoo.conf on the Odoo server (8 CPU, 16 GB): workers = 17, max_cron_threads = 2, db_host = 10.0.0.10
max_connections = 100
shared_buffers = 8GB
effective_cache_size = 24GB
maintenance_work_mem = 2GB
work_mem = 18MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
min_wal_size = 1GB
max_wal_size = 4GB
random_page_cost = 1.1
effective_io_concurrency = 200
huge_pages = try
max_worker_processes = 8
max_parallel_workers_per_gather = 4
max_parallel_workers = 8
max_parallel_maintenance_workers = 4
jit = off
shared_preload_libraries = 'pg_stat_statements'
log_min_duration_statement = 2000"""),
    },
    "links": [
        ("PostgreSQL/Odoo config calculator (this site)", "@page:pg-odoo-calculator.html"),
        ("PGTune", "https://pgtune.leopard.in.ua/"),
        ("PGConfig", "https://www.pgconfig.org/"),
        ("PostgreSQL: pg_dump / pg_restore", "https://www.postgresql.org/docs/current/app-pgdump.html"),
        ("PostgreSQL: monitoring statistics (pg_stat_*)", "https://www.postgresql.org/docs/current/monitoring-stats.html"),
        ("PostgreSQL: routine vacuuming", "https://www.postgresql.org/docs/current/routine-vacuuming.html"),
        ("Odoo 17: deploying, worker and memory sizing", "https://www.odoo.com/documentation/17.0/administration/on_premise/deploy.html"),
        ("explain.dalibo.com – EXPLAIN visualiser", "https://explain.dalibo.com/"),
        ("Blog: the backup will not restore", "@blog:postgresql-restore-fails-foreign-key-duplicate-index-odoo"),
        ("Blog: restoring on stage without cron jobs", "@blog:odoo-stage-restore-stop-cron-jobs"),
        ("Blog: could not serialize access", "@blog:odoo-could-not-serialize-access-concurrent-update"),
        ("Blog: pgload – load test for PostgreSQL", "@blog:postgresql-load-test-pgload-replica"),
        ("Blog: PgBouncer for Odoo", "@blog:pgbouncer-odoo-connection-pooling"),
    ],
    "t": {},
}

_SETTINGS_TABLE = {
    "en": [["Setting", "Rule of thumb", "Depends on Odoo"],
           ["`max_connections`", "Odoo processes × ~3 + reserve, often 100–200", "`workers` + `max_cron_threads` + gevent; `db_maxconn` is a per-process cap, not the real usage; ×2 with a read replica (Odoo 18+)"],
           ["`shared_buffers`", "25 % of the RAM PostgreSQL gets", "on a shared server only of PostgreSQL's share – Odoo workers need their RAM too"],
           ["`effective_cache_size`", "~75 % of that RAM", "only a planner hint, allocates nothing"],
           ["`work_mem`", "(RAM − shared_buffers) / (connections × 3)", "per sort/hash and connection – big Odoo reports use several at once; too high + many workers = OOM"],
           ["`maintenance_work_mem`", "RAM/16, max 2 GB", "faster VACUUM, CREATE INDEX, module updates that build indexes"],
           ["`max_wal_size`", "4 GB+ (more for big imports)", "mass imports, `-u all` and migrations write lots of WAL"],
           ["`random_page_cost`", "1.1 on SSD/NVMe", "makes the planner use Odoo's indexes"],
           ["`jit`", "off", "Odoo runs many short queries"],
           ["`idle_in_transaction_session_timeout`", "e.g. 30 min", "ends forgotten transactions (shell sessions, broken scripts)"]],
}

PGCHEAT["t"]["en"] = {
    "title": "PostgreSQL for Odoo admins: the cheat sheet – backup, restore, users, queries, vacuum, indexes, tuning",
    "summary": "Everything you need day to day: pg_dump/pg_restore/pg_basebackup and backups through Odoo with curl, sizes and the top 10 tables, users and rights, resetting passwords, finding and killing long queries, vacuum, EXPLAIN ANALYZE, indexes, and how PostgreSQL settings depend on Odoo's workers – plus pgtune, pgconfig.org and our calculator.",
    "body": [
        ("p", "A page to bookmark: the PostgreSQL commands I use for Odoo, sorted by task. Odoo 16–19, PostgreSQL 13–17; replace `mydb`, `odoo` and hosts with yours."),
        ("note", "Before anything that changes data – restore, DROP, VACUUM FULL, terminating sessions – make a fresh backup and try it on stage first."),
        ("h", "1. Connecting and looking around in psql"),
        ("code", "connect"),
        ("h", "2. How big are databases and tables?"),
        ("code", "sizes"),
        ("p", "In Odoo the top 10 is almost always `mail_message`, `mail_tracking_value`, `ir_attachment` (only metadata – the files are in the filestore), `account_move_line`, `stock_move` and the `bus_bus`/`queue_job` tables."),
        ("h", "3. Backup: pg_dump, pg_dumpall, pg_basebackup"),
        ("code", "dump"),
        ("ul", [
            "`pg_dump` – one database, logical, portable between versions. The standard for Odoo.",
            "`pg_dumpall --globals-only` – roles and passwords, which pg_dump does not include.",
            "`pg_basebackup` – the whole server, physical: basis for replicas and point-in-time recovery, only for the same major version.",
            "`--no-owner --no-acl` (`-O -x`): no `ALTER OWNER` and `GRANT` in the dump – restorable under any role. Works for pg_dump as well as pg_restore.",
            "There is no `pg_backup` tool – what is meant is usually one of these three.",
        ]),
        ("h", "4. Restore"),
        ("code", "restore"),
        ("h", "5. Through Odoo: web and curl"),
        ("code", "web"),
        ("p", "Practical for small databases and for people without server access. For large ones (tens of GB) the zip export takes long and can hit `limit_time_real` – then use pg_dump. Never leave the database manager publicly reachable: `list_db = False` on production, enable it only temporarily or protect `/web/database/*` in nginx."),
        ("h", "6. Users, databases and rights"),
        ("code", "roles"),
        ("p", "Odoo's role should own its databases and have `CREATEDB` only if the database manager is used – never superuser."),
        ("h", "7. Resetting passwords"),
        ("code", "passwd"),
        ("p", "Do not write an Odoo password directly into `res_users.password` with SQL: Odoo stores a hash and would not accept a plain value. Via `odoo shell` Odoo hashes it itself."),
        ("h", "8. What is running right now – and stopping long queries"),
        ("code", "activity"),
        ("ul", [
            "First `pg_cancel_backend` (cancels the query, the session stays), only then `pg_terminate_backend`.",
            "`idle in transaction` for minutes is a bug in a script or an open shell – it holds locks and blocks vacuum.",
            "Killing an Odoo worker's query rolls back its transaction – the user sees an error, data stays consistent.",
        ]),
        ("h", "9. Monitoring and vacuum"),
        ("code", "vacuum"),
        ("ul", [
            "**Autovacuum** does the daily work – do not switch it off; tune it per table for the big Odoo tables.",
            "**VACUUM (ANALYZE)** – online, frees space for reuse and refreshes statistics. After a restore or big import: `ANALYZE`.",
            "**VACUUM FULL** – returns disk space to the OS but locks the table completely; maintenance window or `pg_repack`.",
            "Watch: dead rows, `last_autovacuum`, transaction ID age, disk space, long transactions.",
        ]),
        ("h", "10. Slow queries: EXPLAIN ANALYZE"),
        ("code", "explain"),
        ("p", "Where do the slow queries come from? `log_min_duration_statement = 2000` writes every query over 2 s into the PostgreSQL log with its text; `pg_stat_statements` sums them up. Copy the query, run `EXPLAIN (ANALYZE, BUFFERS)` on a stage copy, read the plan from the most expensive node."),
        ("h", "11. Indexes: which column has which index"),
        ("code", "indexes"),
        ("p", "In Odoo, add indexes preferably in the module (`index=True` on the field) – an index created by hand in SQL is unknown to Odoo. Before creating one, check that it is really used (`EXPLAIN`), and remove indexes that are never used."),
        ("h", "12. PostgreSQL settings and Odoo workers"),
        ("p", "PostgreSQL and Odoo share the same budget: connections and – on one server – the same RAM. Odoo's settings therefore determine PostgreSQL's:"),
        ("table", _SETTINGS_TABLE["en"]),
        ("p", "Odoo side: about 6 concurrent users per worker, at most 2 × CPU cores + 1 workers; per worker on average ~150 MB for light and ~1 GB for heavy requests (Odoo documentation). `limit_memory_soft/hard` are ceilings for peaks, not averages."),
        ("h", "13. pgtune and pgconfig.org"),
        ("ul", [
            "**PGTune** (pgtune.leopard.in.ua): enter PostgreSQL version, OS, DB type, RAM, CPU, number of connections and storage – you get a postgresql.conf block. For Odoo choose “Web application” or “OLTP”.",
            "**PGConfig** (pgconfig.org): similar, with profiles (web, OLTP, data warehouse, mixed, desktop), also outputs `ALTER SYSTEM` commands and explains each parameter.",
            "Both know nothing about Odoo: they take “connections” as a given and assume the whole RAM belongs to PostgreSQL. With Odoo on the same server you must enter only PostgreSQL's share – and derive the connections from the workers.",
        ]),
        ("p", "Two examples in the style of these tools, adjusted for Odoo:"),
        ("code", "exA"),
        ("code", "exB"),
        ("note", "That is exactly what our calculator does: enter CPU, RAM, users and whether PostgreSQL runs on the same server – it outputs odoo.conf and postgresql.conf together, also as ALTER SYSTEM, and with sliders you can see which lines change."),
        ("links", "Links"),
    ],
}

_SETTINGS_TABLE["de"] = [["Einstellung", "Faustregel", "Hängt ab von Odoo"],
    ["`max_connections`", "Odoo-Prozesse × ~3 + Reserve, oft 100–200", "`workers` + `max_cron_threads` + Gevent; `db_maxconn` ist eine Obergrenze pro Prozess, nicht der echte Verbrauch; ×2 mit Read-Replica (Odoo 18+)"],
    ["`shared_buffers`", "25 % des RAM, den PostgreSQL bekommt", "auf einem gemeinsamen Server nur vom PostgreSQL-Anteil – Odoo-Worker brauchen ihren RAM auch"],
    ["`effective_cache_size`", "~75 % dieses RAM", "nur ein Hinweis für den Planer, belegt nichts"],
    ["`work_mem`", "(RAM − shared_buffers) / (Verbindungen × 3)", "pro Sortierung/Hash und Verbindung – große Odoo-Berichte nutzen mehrere gleichzeitig; zu hoch + viele Worker = OOM"],
    ["`maintenance_work_mem`", "RAM/16, max. 2 GB", "schnelleres VACUUM, CREATE INDEX, Modul-Updates, die Indizes bauen"],
    ["`max_wal_size`", "4 GB+ (mehr bei großen Importen)", "Massenimporte, `-u all` und Migrationen schreiben viel WAL"],
    ["`random_page_cost`", "1,1 auf SSD/NVMe", "damit der Planer die Indizes von Odoo nutzt"],
    ["`jit`", "off", "Odoo führt viele kurze Abfragen aus"],
    ["`idle_in_transaction_session_timeout`", "z. B. 30 min", "beendet vergessene Transaktionen (Shell-Sitzungen, kaputte Skripte)"]]

PGCHEAT["t"]["de"] = {
    "title": "PostgreSQL für Odoo-Admins: der Spickzettel – Backup, Restore, Benutzer, Abfragen, Vacuum, Indizes, Tuning",
    "summary": "Alles für den Alltag: pg_dump/pg_restore/pg_basebackup und Backups über Odoo mit curl, Größen und die Top-10-Tabellen, Benutzer und Rechte, Passwörter zurücksetzen, lange Abfragen finden und beenden, Vacuum, EXPLAIN ANALYZE, Indizes und wie die PostgreSQL-Einstellungen von den Odoo-Workern abhängen – dazu pgtune, pgconfig.org und unser Rechner.",
    "body": [
        ("p", "Eine Seite für die Lesezeichen: die PostgreSQL-Befehle, die ich für Odoo verwende, nach Aufgabe sortiert. Odoo 16–19, PostgreSQL 13–17; `mydb`, `odoo` und Hosts durch Ihre ersetzen."),
        ("note", "Vor allem, was Daten verändert – Restore, DROP, VACUUM FULL, Sitzungen beenden – ein frisches Backup machen und zuerst auf Stage ausprobieren."),
        ("h", "1. Verbinden und umsehen in psql"),
        ("code", "connect"),
        ("h", "2. Wie groß sind Datenbanken und Tabellen?"),
        ("code", "sizes"),
        ("p", "In Odoo besteht die Top 10 fast immer aus `mail_message`, `mail_tracking_value`, `ir_attachment` (nur Metadaten – die Dateien liegen im Filestore), `account_move_line`, `stock_move` und den Tabellen `bus_bus`/`queue_job`."),
        ("h", "3. Backup: pg_dump, pg_dumpall, pg_basebackup"),
        ("code", "dump"),
        ("ul", [
            "`pg_dump` – eine Datenbank, logisch, zwischen Versionen übertragbar. Der Standard für Odoo.",
            "`pg_dumpall --globals-only` – Rollen und Passwörter, die pg_dump nicht enthält.",
            "`pg_basebackup` – der ganze Server, physisch: Grundlage für Replicas und Point-in-Time-Recovery, nur für dieselbe Hauptversion.",
            "`--no-owner --no-acl` (`-O -x`): kein `ALTER OWNER` und `GRANT` im Dump – unter jeder Rolle einspielbar. Gilt für pg_dump wie für pg_restore.",
            "Ein Werkzeug `pg_backup` gibt es nicht – gemeint ist meist eines dieser drei.",
        ]),
        ("h", "4. Wiederherstellen"),
        ("code", "restore"),
        ("h", "5. Über Odoo: Web und curl"),
        ("code", "web"),
        ("p", "Praktisch für kleine Datenbanken und für Personen ohne Serverzugang. Bei großen (Dutzende GB) dauert der Zip-Export lange und kann an `limit_time_real` scheitern – dann pg_dump. Den Datenbankmanager nie öffentlich erreichbar lassen: `list_db = False` in Produktion, nur vorübergehend einschalten oder `/web/database/*` in nginx schützen."),
        ("h", "6. Benutzer, Datenbanken und Rechte"),
        ("code", "roles"),
        ("p", "Die Rolle von Odoo sollte Eigentümerin ihrer Datenbanken sein und `CREATEDB` nur haben, wenn der Datenbankmanager genutzt wird – nie Superuser."),
        ("h", "7. Passwörter zurücksetzen"),
        ("code", "passwd"),
        ("p", "Ein Odoo-Passwort nicht per SQL direkt in `res_users.password` schreiben: Odoo speichert einen Hash und würde einen Klartext nicht akzeptieren. Über `odoo shell` hasht Odoo selbst."),
        ("h", "8. Was läuft gerade – und lange Abfragen beenden"),
        ("code", "activity"),
        ("ul", [
            "Zuerst `pg_cancel_backend` (bricht die Abfrage ab, die Sitzung bleibt), erst dann `pg_terminate_backend`.",
            "`idle in transaction` über Minuten ist ein Fehler in einem Skript oder eine offene Shell – hält Sperren und blockiert Vacuum.",
            "Wird die Abfrage eines Odoo-Workers beendet, rollt seine Transaktion zurück – der Anwender sieht einen Fehler, die Daten bleiben konsistent.",
        ]),
        ("h", "9. Überwachen und Vacuum"),
        ("code", "vacuum"),
        ("ul", [
            "**Autovacuum** erledigt die tägliche Arbeit – nicht abschalten; für die großen Odoo-Tabellen pro Tabelle einstellen.",
            "**VACUUM (ANALYZE)** – online, gibt Platz zur Wiederverwendung frei und aktualisiert Statistiken. Nach Restore oder großem Import: `ANALYZE`.",
            "**VACUUM FULL** – gibt Plattenplatz an das Betriebssystem zurück, sperrt die Tabelle aber komplett; Wartungsfenster oder `pg_repack`.",
            "Beobachten: tote Zeilen, `last_autovacuum`, Alter der Transaktions-IDs, Plattenplatz, lange Transaktionen.",
        ]),
        ("h", "10. Langsame Abfragen: EXPLAIN ANALYZE"),
        ("code", "explain"),
        ("p", "Woher kommen die langsamen Abfragen? `log_min_duration_statement = 2000` schreibt jede Abfrage über 2 s mit Text ins PostgreSQL-Log; `pg_stat_statements` summiert sie. Abfrage kopieren, auf einer Stage-Kopie `EXPLAIN (ANALYZE, BUFFERS)` ausführen, den Plan vom teuersten Knoten her lesen."),
        ("h", "11. Indizes: welche Spalte hat welchen Index"),
        ("code", "indexes"),
        ("p", "In Odoo Indizes bevorzugt im Modul anlegen (`index=True` am Feld) – ein von Hand per SQL angelegter Index ist Odoo unbekannt. Vor dem Anlegen prüfen, ob er wirklich genutzt wird (`EXPLAIN`), und nie genutzte Indizes entfernen."),
        ("h", "12. PostgreSQL-Einstellungen und Odoo-Worker"),
        ("p", "PostgreSQL und Odoo teilen dasselbe Budget: Verbindungen und – auf einem Server – denselben RAM. Die Einstellungen von Odoo bestimmen daher die von PostgreSQL:"),
        ("table", _SETTINGS_TABLE["de"]),
        ("p", "Odoo-Seite: etwa 6 gleichzeitige Anwender pro Worker, höchstens 2 × CPU-Kerne + 1 Worker; pro Worker im Schnitt ~150 MB für leichte und ~1 GB für schwere Anfragen (Odoo-Dokumentation). `limit_memory_soft/hard` sind Obergrenzen für Spitzen, keine Durchschnittswerte."),
        ("h", "13. pgtune und pgconfig.org"),
        ("ul", [
            "**PGTune** (pgtune.leopard.in.ua): PostgreSQL-Version, Betriebssystem, DB-Typ, RAM, CPU, Verbindungen und Datenträger eingeben – man erhält einen postgresql.conf-Block. Für Odoo „Web application“ oder „OLTP“ wählen.",
            "**PGConfig** (pgconfig.org): ähnlich, mit Profilen (Web, OLTP, Data Warehouse, Mixed, Desktop), gibt auch `ALTER SYSTEM`-Befehle aus und erklärt jeden Parameter.",
            "Beide wissen nichts von Odoo: Sie nehmen „Verbindungen“ als gegeben und gehen davon aus, dass der ganze RAM PostgreSQL gehört. Mit Odoo auf demselben Server darf man nur den Anteil von PostgreSQL eingeben – und die Verbindungen aus den Workern ableiten.",
        ]),
        ("p", "Zwei Beispiele im Stil dieser Werkzeuge, angepasst an Odoo:"),
        ("code", "exA"),
        ("code", "exB"),
        ("note", "Genau das macht unser Rechner: CPU, RAM, Anwender und ob PostgreSQL auf demselben Server läuft eingeben – er gibt odoo.conf und postgresql.conf zusammen aus, auch als ALTER SYSTEM, und mit Schiebereglern sieht man, welche Zeilen sich ändern."),
        ("links", "Links"),
    ],
}

_SETTINGS_TABLE["fr"] = [["Paramètre", "Règle empirique", "Dépend d'Odoo"],
    ["`max_connections`", "processus Odoo × ~3 + réserve, souvent 100–200", "`workers` + `max_cron_threads` + gevent ; `db_maxconn` est un plafond par processus, pas l'usage réel ; ×2 avec réplique (Odoo 18+)"],
    ["`shared_buffers`", "25 % de la RAM attribuée à PostgreSQL", "sur un serveur partagé, seulement de la part de PostgreSQL – les workers Odoo ont aussi besoin de RAM"],
    ["`effective_cache_size`", "~75 % de cette RAM", "simple indication pour le planificateur, n'alloue rien"],
    ["`work_mem`", "(RAM − shared_buffers) / (connexions × 3)", "par tri/hash et par connexion – les gros rapports Odoo en utilisent plusieurs ; trop haut + beaucoup de workers = OOM"],
    ["`maintenance_work_mem`", "RAM/16, max. 2 Go", "VACUUM, CREATE INDEX et mises à jour de modules plus rapides"],
    ["`max_wal_size`", "4 Go+ (plus pour de gros imports)", "imports massifs, `-u all` et migrations écrivent beaucoup de WAL"],
    ["`random_page_cost`", "1,1 sur SSD/NVMe", "pour que le planificateur utilise les index d'Odoo"],
    ["`jit`", "off", "Odoo exécute beaucoup de requêtes courtes"],
    ["`idle_in_transaction_session_timeout`", "p. ex. 30 min", "termine les transactions oubliées (sessions shell, scripts cassés)"]]

PGCHEAT["t"]["fr"] = {
    "title": "PostgreSQL pour administrateurs Odoo : l'aide-mémoire – sauvegarde, restauration, utilisateurs, requêtes, vacuum, index, réglages",
    "summary": "Tout le nécessaire au quotidien : pg_dump/pg_restore/pg_basebackup et sauvegardes via Odoo avec curl, tailles et top 10 des tables, utilisateurs et droits, réinitialisation des mots de passe, trouver et arrêter les longues requêtes, vacuum, EXPLAIN ANALYZE, index, et comment les réglages PostgreSQL dépendent des workers Odoo – plus pgtune, pgconfig.org et notre calculateur.",
    "body": [
        ("p", "Une page à garder en favori : les commandes PostgreSQL que j'utilise pour Odoo, classées par tâche. Odoo 16–19, PostgreSQL 13–17 ; remplacez `mydb`, `odoo` et les hôtes par les vôtres."),
        ("note", "Avant toute opération qui modifie des données – restauration, DROP, VACUUM FULL, arrêt de sessions – faire une sauvegarde récente et essayer d'abord sur stage."),
        ("h", "1. Se connecter et explorer dans psql"),
        ("code", "connect"),
        ("h", "2. Quelle taille pour les bases et les tables ?"),
        ("code", "sizes"),
        ("p", "Dans Odoo, le top 10 est presque toujours `mail_message`, `mail_tracking_value`, `ir_attachment` (métadonnées seulement – les fichiers sont dans le filestore), `account_move_line`, `stock_move` et les tables `bus_bus`/`queue_job`."),
        ("h", "3. Sauvegarde : pg_dump, pg_dumpall, pg_basebackup"),
        ("code", "dump"),
        ("ul", [
            "`pg_dump` – une base, logique, transportable entre versions. Le standard pour Odoo.",
            "`pg_dumpall --globals-only` – rôles et mots de passe, absents de pg_dump.",
            "`pg_basebackup` – tout le serveur, physique : base des répliques et de la restauration à un instant donné, uniquement pour la même version majeure.",
            "`--no-owner --no-acl` (`-O -x`) : pas d'`ALTER OWNER` ni de `GRANT` dans le dump – restaurable sous n'importe quel rôle. Valable pour pg_dump comme pour pg_restore.",
            "Il n'existe pas d'outil `pg_backup` – on pense en général à l'un de ces trois.",
        ]),
        ("h", "4. Restauration"),
        ("code", "restore"),
        ("h", "5. Via Odoo : web et curl"),
        ("code", "web"),
        ("p", "Pratique pour les petites bases et pour les personnes sans accès au serveur. Pour les grandes (des dizaines de Go), l'export zip est long et peut atteindre `limit_time_real` – utiliser alors pg_dump. Ne jamais laisser le gestionnaire de bases accessible publiquement : `list_db = False` en production, l'activer seulement temporairement ou protéger `/web/database/*` dans nginx."),
        ("h", "6. Utilisateurs, bases et droits"),
        ("code", "roles"),
        ("p", "Le rôle d'Odoo doit être propriétaire de ses bases et n'avoir `CREATEDB` que si le gestionnaire de bases est utilisé – jamais superutilisateur."),
        ("h", "7. Réinitialiser les mots de passe"),
        ("code", "passwd"),
        ("p", "Ne pas écrire un mot de passe Odoo directement dans `res_users.password` en SQL : Odoo stocke un hash et refuserait une valeur en clair. Via `odoo shell`, Odoo le hache lui-même."),
        ("h", "8. Ce qui tourne en ce moment – et arrêter les longues requêtes"),
        ("code", "activity"),
        ("ul", [
            "D'abord `pg_cancel_backend` (annule la requête, la session reste), ensuite seulement `pg_terminate_backend`.",
            "`idle in transaction` pendant des minutes est un bug de script ou un shell ouvert – il garde des verrous et bloque le vacuum.",
            "Arrêter la requête d'un worker Odoo annule sa transaction – l'utilisateur voit une erreur, les données restent cohérentes.",
        ]),
        ("h", "9. Surveillance et vacuum"),
        ("code", "vacuum"),
        ("ul", [
            "**Autovacuum** fait le travail quotidien – ne pas le désactiver ; le régler table par table pour les grosses tables Odoo.",
            "**VACUUM (ANALYZE)** – en ligne, libère de l'espace pour réutilisation et met à jour les statistiques. Après une restauration ou un gros import : `ANALYZE`.",
            "**VACUUM FULL** – rend l'espace disque au système mais verrouille complètement la table ; fenêtre de maintenance ou `pg_repack`.",
            "À surveiller : lignes mortes, `last_autovacuum`, âge des identifiants de transaction, espace disque, longues transactions.",
        ]),
        ("h", "10. Requêtes lentes : EXPLAIN ANALYZE"),
        ("code", "explain"),
        ("p", "D'où viennent les requêtes lentes ? `log_min_duration_statement = 2000` écrit chaque requête de plus de 2 s avec son texte dans le journal PostgreSQL ; `pg_stat_statements` les cumule. Copier la requête, lancer `EXPLAIN (ANALYZE, BUFFERS)` sur une copie de stage, lire le plan à partir du nœud le plus coûteux."),
        ("h", "11. Index : quelle colonne a quel index"),
        ("code", "indexes"),
        ("p", "Dans Odoo, créer de préférence les index dans le module (`index=True` sur le champ) – un index créé à la main en SQL est inconnu d'Odoo. Avant d'en créer un, vérifier qu'il est vraiment utilisé (`EXPLAIN`), et supprimer les index jamais utilisés."),
        ("h", "12. Réglages PostgreSQL et workers Odoo"),
        ("p", "PostgreSQL et Odoo partagent le même budget : les connexions et – sur un seul serveur – la même RAM. Les réglages d'Odoo déterminent donc ceux de PostgreSQL :"),
        ("table", _SETTINGS_TABLE["fr"]),
        ("p", "Côté Odoo : environ 6 utilisateurs simultanés par worker, au plus 2 × cœurs CPU + 1 workers ; par worker en moyenne ~150 Mo pour les requêtes légères et ~1 Go pour les lourdes (documentation Odoo). `limit_memory_soft/hard` sont des plafonds pour les pics, pas des moyennes."),
        ("h", "13. pgtune et pgconfig.org"),
        ("ul", [
            "**PGTune** (pgtune.leopard.in.ua) : saisir version de PostgreSQL, système, type de base, RAM, CPU, nombre de connexions et stockage – on obtient un bloc postgresql.conf. Pour Odoo, choisir « Web application » ou « OLTP ».",
            "**PGConfig** (pgconfig.org) : similaire, avec des profils (web, OLTP, data warehouse, mixte, desktop), produit aussi des commandes `ALTER SYSTEM` et explique chaque paramètre.",
            "Aucun des deux ne connaît Odoo : ils prennent les « connexions » comme une donnée et supposent que toute la RAM appartient à PostgreSQL. Avec Odoo sur le même serveur, il faut saisir seulement la part de PostgreSQL – et déduire les connexions des workers.",
        ]),
        ("p", "Deux exemples dans le style de ces outils, adaptés à Odoo :"),
        ("code", "exA"),
        ("code", "exB"),
        ("note", "C'est exactement ce que fait notre calculateur : saisir CPU, RAM, utilisateurs et si PostgreSQL tourne sur le même serveur – il produit odoo.conf et postgresql.conf ensemble, aussi en ALTER SYSTEM, et avec les curseurs on voit quelles lignes changent."),
        ("links", "Liens"),
    ],
}

_SETTINGS_TABLE["el"] = [["Ρύθμιση", "Εμπειρικός κανόνας", "Εξαρτάται από το Odoo"],
    ["`max_connections`", "διεργασίες Odoo × ~3 + απόθεμα, συχνά 100–200", "`workers` + `max_cron_threads` + gevent· το `db_maxconn` είναι ανώτατο όριο ανά διεργασία, όχι η πραγματική χρήση· ×2 με read replica (Odoo 18+)"],
    ["`shared_buffers`", "25 % της RAM που παίρνει η PostgreSQL", "σε κοινό server μόνο από το μερίδιο της PostgreSQL – και οι workers του Odoo χρειάζονται RAM"],
    ["`effective_cache_size`", "~75 % αυτής της RAM", "απλώς υπόδειξη για τον planner, δεν δεσμεύει τίποτα"],
    ["`work_mem`", "(RAM − shared_buffers) / (συνδέσεις × 3)", "ανά ταξινόμηση/hash και σύνδεση – οι μεγάλες αναφορές του Odoo χρησιμοποιούν πολλά μαζί· πολύ υψηλό + πολλοί workers = OOM"],
    ["`maintenance_work_mem`", "RAM/16, έως 2 GB", "ταχύτερα VACUUM, CREATE INDEX και ενημερώσεις modules"],
    ["`max_wal_size`", "4 GB+ (περισσότερο για μεγάλες εισαγωγές)", "μαζικές εισαγωγές, `-u all` και μεταπτώσεις γράφουν πολύ WAL"],
    ["`random_page_cost`", "1,1 σε SSD/NVMe", "ώστε ο planner να χρησιμοποιεί τους indexes του Odoo"],
    ["`jit`", "off", "το Odoo εκτελεί πολλά σύντομα ερωτήματα"],
    ["`idle_in_transaction_session_timeout`", "π.χ. 30 min", "τερματίζει ξεχασμένες συναλλαγές (συνεδρίες shell, χαλασμένα scripts)"]]

PGCHEAT["t"]["el"] = {
    "title": "PostgreSQL για διαχειριστές Odoo: το σκονάκι – backup, επαναφορά, χρήστες, ερωτήματα, vacuum, indexes, ρυθμίσεις",
    "summary": "Ό,τι χρειάζεστε καθημερινά: pg_dump/pg_restore/pg_basebackup και backup μέσω Odoo με curl, μεγέθη και οι 10 μεγαλύτεροι πίνακες, χρήστες και δικαιώματα, επαναφορά κωδικών, εύρεση και τερματισμός μακριών ερωτημάτων, vacuum, EXPLAIN ANALYZE, indexes και πώς οι ρυθμίσεις της PostgreSQL εξαρτώνται από τους workers του Odoo – μαζί με pgtune, pgconfig.org και τον υπολογιστή μας.",
    "body": [
        ("p", "Μια σελίδα για τους σελιδοδείκτες: οι εντολές PostgreSQL που χρησιμοποιώ για το Odoo, ταξινομημένες ανά εργασία. Odoo 16–19, PostgreSQL 13–17· αντικαταστήστε `mydb`, `odoo` και hosts με τα δικά σας."),
        ("note", "Πριν από οτιδήποτε αλλάζει δεδομένα – επαναφορά, DROP, VACUUM FULL, τερματισμό συνεδριών – πάρτε φρέσκο backup και δοκιμάστε πρώτα σε stage."),
        ("h", "1. Σύνδεση και περιήγηση στο psql"),
        ("code", "connect"),
        ("h", "2. Πόσο μεγάλες είναι οι βάσεις και οι πίνακες;"),
        ("code", "sizes"),
        ("p", "Στο Odoo το top 10 είναι σχεδόν πάντα `mail_message`, `mail_tracking_value`, `ir_attachment` (μόνο μεταδεδομένα – τα αρχεία είναι στο filestore), `account_move_line`, `stock_move` και οι πίνακες `bus_bus`/`queue_job`."),
        ("h", "3. Backup: pg_dump, pg_dumpall, pg_basebackup"),
        ("code", "dump"),
        ("ul", [
            "`pg_dump` – μία βάση, λογικό, μεταφέρσιμο μεταξύ εκδόσεων. Το πρότυπο για το Odoo.",
            "`pg_dumpall --globals-only` – ρόλοι και κωδικοί, που δεν περιέχει το pg_dump.",
            "`pg_basebackup` – όλος ο server, φυσικό: βάση για replicas και point-in-time recovery, μόνο για την ίδια κύρια έκδοση.",
            "`--no-owner --no-acl` (`-O -x`): χωρίς `ALTER OWNER` και `GRANT` στο dump – επαναφέρεται με οποιονδήποτε ρόλο. Ισχύει τόσο για pg_dump όσο και για pg_restore.",
            "Εργαλείο `pg_backup` δεν υπάρχει – συνήθως εννοείται ένα από αυτά τα τρία.",
        ]),
        ("h", "4. Επαναφορά"),
        ("code", "restore"),
        ("h", "5. Μέσω Odoo: web και curl"),
        ("code", "web"),
        ("p", "Πρακτικό για μικρές βάσεις και για άτομα χωρίς πρόσβαση στον server. Για μεγάλες (δεκάδες GB) η εξαγωγή zip αργεί και μπορεί να φτάσει το `limit_time_real` – τότε pg_dump. Ποτέ μην αφήνετε τον database manager δημόσια προσβάσιμο: `list_db = False` στην παραγωγή, ενεργοποίηση μόνο προσωρινά ή προστασία του `/web/database/*` στο nginx."),
        ("h", "6. Χρήστες, βάσεις και δικαιώματα"),
        ("code", "roles"),
        ("p", "Ο ρόλος του Odoo πρέπει να είναι ιδιοκτήτης των βάσεών του και να έχει `CREATEDB` μόνο αν χρησιμοποιείται ο database manager – ποτέ superuser."),
        ("h", "7. Επαναφορά κωδικών"),
        ("code", "passwd"),
        ("p", "Μη γράφετε κωδικό Odoo απευθείας στο `res_users.password` με SQL: το Odoo αποθηκεύει hash και δεν θα δεχόταν απλό κείμενο. Μέσω `odoo shell` το Odoo κάνει μόνο του το hash."),
        ("h", "8. Τι τρέχει τώρα – και τερματισμός μακριών ερωτημάτων"),
        ("code", "activity"),
        ("ul", [
            "Πρώτα `pg_cancel_backend` (ακυρώνει το ερώτημα, η συνεδρία μένει), μόνο μετά `pg_terminate_backend`.",
            "`idle in transaction` για λεπτά είναι σφάλμα script ή ανοιχτό shell – κρατά κλειδώματα και μπλοκάρει το vacuum.",
            "Ο τερματισμός του ερωτήματος ενός worker του Odoo κάνει rollback τη συναλλαγή του – ο χρήστης βλέπει σφάλμα, τα δεδομένα μένουν συνεπή.",
        ]),
        ("h", "9. Παρακολούθηση και vacuum"),
        ("code", "vacuum"),
        ("ul", [
            "Το **autovacuum** κάνει την καθημερινή δουλειά – μην το απενεργοποιείτε· ρυθμίστε το ανά πίνακα για τους μεγάλους πίνακες του Odoo.",
            "**VACUUM (ANALYZE)** – online, ελευθερώνει χώρο για επαναχρησιμοποίηση και ανανεώνει τα στατιστικά. Μετά από επαναφορά ή μεγάλη εισαγωγή: `ANALYZE`.",
            "**VACUUM FULL** – επιστρέφει χώρο δίσκου στο λειτουργικό αλλά κλειδώνει πλήρως τον πίνακα· παράθυρο συντήρησης ή `pg_repack`.",
            "Παρακολουθείτε: νεκρές γραμμές, `last_autovacuum`, ηλικία των transaction ID, χώρο δίσκου, μακριές συναλλαγές.",
        ]),
        ("h", "10. Αργά ερωτήματα: EXPLAIN ANALYZE"),
        ("code", "explain"),
        ("p", "Από πού έρχονται τα αργά ερωτήματα; Το `log_min_duration_statement = 2000` γράφει κάθε ερώτημα πάνω από 2 s με το κείμενό του στο log της PostgreSQL· το `pg_stat_statements` τα αθροίζει. Αντιγράψτε το ερώτημα, τρέξτε `EXPLAIN (ANALYZE, BUFFERS)` σε αντίγραφο stage, διαβάστε το πλάνο από τον ακριβότερο κόμβο."),
        ("h", "11. Indexes: ποια στήλη έχει ποιον index"),
        ("code", "indexes"),
        ("p", "Στο Odoo δημιουργήστε indexes κατά προτίμηση στο module (`index=True` στο πεδίο) – ένας index που φτιάχτηκε με το χέρι σε SQL είναι άγνωστος στο Odoo. Πριν τον δημιουργήσετε ελέγξτε ότι πράγματι χρησιμοποιείται (`EXPLAIN`) και αφαιρέστε indexes που δεν χρησιμοποιούνται ποτέ."),
        ("h", "12. Ρυθμίσεις PostgreSQL και workers του Odoo"),
        ("p", "Η PostgreSQL και το Odoo μοιράζονται τον ίδιο προϋπολογισμό: συνδέσεις και – σε έναν server – την ίδια RAM. Οι ρυθμίσεις του Odoo καθορίζουν λοιπόν αυτές της PostgreSQL:"),
        ("table", _SETTINGS_TABLE["el"]),
        ("p", "Πλευρά Odoo: περίπου 6 ταυτόχρονοι χρήστες ανά worker, το πολύ 2 × πυρήνες CPU + 1 workers· ανά worker κατά μέσο όρο ~150 MB για ελαφριά και ~1 GB για βαριά αιτήματα (τεκμηρίωση Odoo). Τα `limit_memory_soft/hard` είναι ανώτατα όρια για αιχμές, όχι μέσοι όροι."),
        ("h", "13. pgtune και pgconfig.org"),
        ("ul", [
            "**PGTune** (pgtune.leopard.in.ua): δίνετε έκδοση PostgreSQL, λειτουργικό, τύπο βάσης, RAM, CPU, αριθμό συνδέσεων και αποθήκευση – παίρνετε ένα μπλοκ postgresql.conf. Για το Odoo επιλέξτε «Web application» ή «OLTP».",
            "**PGConfig** (pgconfig.org): παρόμοιο, με προφίλ (web, OLTP, data warehouse, mixed, desktop), βγάζει και εντολές `ALTER SYSTEM` και εξηγεί κάθε παράμετρο.",
            "Κανένα δεν ξέρει το Odoo: θεωρούν τις «συνδέσεις» δεδομένες και ότι όλη η RAM ανήκει στην PostgreSQL. Με το Odoo στον ίδιο server πρέπει να δώσετε μόνο το μερίδιο της PostgreSQL – και να βγάλετε τις συνδέσεις από τους workers.",
        ]),
        ("p", "Δύο παραδείγματα στο ύφος αυτών των εργαλείων, προσαρμοσμένα στο Odoo:"),
        ("code", "exA"),
        ("code", "exB"),
        ("note", "Ακριβώς αυτό κάνει ο υπολογιστής μας: δίνετε CPU, RAM, χρήστες και αν η PostgreSQL τρέχει στον ίδιο server – βγάζει odoo.conf και postgresql.conf μαζί, και ως ALTER SYSTEM, και με τα ρυθμιστικά βλέπετε ποιες γραμμές αλλάζουν."),
        ("links", "Σύνδεσμοι"),
    ],
}

_SETTINGS_TABLE["uk"] = [["Налаштування", "Емпіричне правило", "Від чого залежить в Odoo"],
    ["`max_connections`", "процеси Odoo × ~3 + запас, часто 100–200", "`workers` + `max_cron_threads` + gevent; `db_maxconn` — стеля на процес, а не реальне споживання; ×2 з read-реплікою (Odoo 18+)"],
    ["`shared_buffers`", "25 % RAM, яку отримує PostgreSQL", "на спільному сервері лише від частки PostgreSQL, бо воркерам Odoo теж потрібна RAM"],
    ["`effective_cache_size`", "~75 % цієї RAM", "лише підказка для планувальника, нічого не виділяє"],
    ["`work_mem`", "(RAM − shared_buffers) / (з'єднання × 3)", "на кожне сортування чи hash і на з'єднання; великі звіти Odoo використовують кілька одразу, а завелике значення плюс багато воркерів дають OOM"],
    ["`maintenance_work_mem`", "RAM/16, до 2 ГБ", "швидші VACUUM, CREATE INDEX та оновлення модулів"],
    ["`max_wal_size`", "4 ГБ+ (більше для великих імпортів)", "масові імпорти, `-u all` і міграції пишуть багато WAL"],
    ["`random_page_cost`", "1,1 на SSD/NVMe", "щоб планувальник використовував індекси Odoo"],
    ["`jit`", "off", "Odoo виконує багато коротких запитів"],
    ["`idle_in_transaction_session_timeout`", "напр. 30 хв", "завершує забуті транзакції (сесії shell, зламані скрипти)"]]

PGCHEAT["t"]["uk"] = {
    "title": "PostgreSQL для адміністратора Odoo: шпаргалка — бекап, відновлення, користувачі, запити, vacuum, індекси, налаштування",
    "summary": "Усе потрібне щодня: pg_dump/pg_restore/pg_basebackup і бекап через Odoo за допомогою curl, розміри баз і топ-10 таблиць, користувачі й права, скидання паролів, пошук і зупинка довгих запитів, vacuum, EXPLAIN ANALYZE, індекси і те, як налаштування PostgreSQL залежать від воркерів Odoo. А також pgtune, pgconfig.org і наш калькулятор.",
    "body": [
        ("p", "Сторінка для закладок: команди PostgreSQL, якими я користуюся для Odoo, згруповані за задачами. Odoo 16–19, PostgreSQL 13–17; замініть `mydb`, `odoo` і хости на свої."),
        ("note", "Перед будь-якою дією, що змінює дані (відновлення, DROP, VACUUM FULL, завершення сесій), зробіть свіжий бекап і спершу спробуйте на stage."),
        ("h", "1. Підключення й огляд у psql"),
        ("code", "connect"),
        ("h", "2. Який розмір баз і таблиць?"),
        ("code", "sizes"),
        ("p", "В Odoo до топ-10 майже завжди входять `mail_message`, `mail_tracking_value`, `ir_attachment` (лише метадані, самі файли лежать у filestore), `account_move_line`, `stock_move` і таблиці `bus_bus`/`queue_job`."),
        ("h", "3. Бекап: pg_dump, pg_dumpall, pg_basebackup"),
        ("code", "dump"),
        ("ul", [
            "`pg_dump` — одна база, логічний дамп, переноситься між версіями. Стандарт для Odoo.",
            "`pg_dumpall --globals-only` — ролі та їхні паролі, яких немає в pg_dump.",
            "`pg_basebackup` — увесь сервер, фізична копія: основа для реплік і відновлення на момент часу, лише для тієї ж мажорної версії.",
            "`--no-owner --no-acl` (`-O -x`): у дампі немає `ALTER OWNER` і `GRANT`, тож його можна відновити під будь-якою роллю. Працює і для pg_dump, і для pg_restore.",
            "Інструмента `pg_backup` не існує, зазвичай мають на увазі один із цих трьох.",
        ]),
        ("h", "4. Відновлення"),
        ("code", "restore"),
        ("h", "5. Через Odoo: веб і curl"),
        ("code", "web"),
        ("p", "Зручно для невеликих баз і для людей без доступу до сервера. Для великих баз (десятки ГБ) zip-експорт триває довго й може впертися в `limit_time_real`, тоді краще pg_dump. Ніколи не залишайте менеджер баз відкритим: `list_db = False` на продуктиві, вмикайте лише тимчасово або захистіть `/web/database/*` у nginx."),
        ("h", "6. Користувачі, бази та права"),
        ("code", "roles"),
        ("p", "Роль Odoo має бути власником своїх баз і мати `CREATEDB` лише тоді, коли використовується менеджер баз. Суперкористувачем вона не має бути ніколи."),
        ("h", "7. Скидання паролів"),
        ("code", "passwd"),
        ("p", "Не записуйте пароль Odoo напряму в `res_users.password` через SQL: Odoo зберігає хеш і не прийме відкрите значення. Через `odoo shell` Odoo сам його захешує."),
        ("h", "8. Що виконується зараз і як зупинити довгі запити"),
        ("code", "activity"),
        ("ul", [
            "Спочатку `pg_cancel_backend` (скасовує запит, сесія лишається), і лише потім `pg_terminate_backend`.",
            "`idle in transaction` протягом хвилин — це помилка в скрипті або відкритий shell: такий стан тримає блокування й заважає vacuum.",
            "Якщо зупинити запит воркера Odoo, його транзакція відкотиться: користувач побачить помилку, але дані залишаться узгодженими.",
        ]),
        ("h", "9. Моніторинг і vacuum"),
        ("code", "vacuum"),
        ("ul", [
            "**Autovacuum** виконує щоденну роботу: не вимикайте його, а для великих таблиць Odoo налаштуйте окремо.",
            "**VACUUM (ANALYZE)** працює онлайн: звільняє місце для повторного використання й оновлює статистику. Після відновлення чи великого імпорту запустіть `ANALYZE`.",
            "**VACUUM FULL** повертає місце на диску операційній системі, але повністю блокує таблицю. Потрібне вікно обслуговування або `pg_repack`.",
            "Що відстежувати: мертві рядки, `last_autovacuum`, вік ідентифікаторів транзакцій, місце на диску, довгі транзакції.",
        ]),
        ("h", "10. Повільні запити: EXPLAIN ANALYZE"),
        ("code", "explain"),
        ("p", "Звідки беруться повільні запити? `log_min_duration_statement = 2000` записує в лог PostgreSQL кожен запит довший за 2 с разом із текстом, а `pg_stat_statements` підсумовує їх. Скопіюйте запит, виконайте `EXPLAIN (ANALYZE, BUFFERS)` на копії stage і читайте план від найдорожчого вузла."),
        ("h", "11. Індекси: яка колонка має який індекс"),
        ("code", "indexes"),
        ("p", "В Odoo індекси краще створювати в модулі (`index=True` на полі): індекс, створений вручну через SQL, Odoo не знає. Перш ніж створювати індекс, перевірте через `EXPLAIN`, що він справді використовується, і видаляйте індекси, які не використовуються ніколи."),
        ("h", "12. Налаштування PostgreSQL і воркери Odoo"),
        ("p", "PostgreSQL та Odoo ділять один бюджет: з'єднання, а на одному сервері ще й ту саму RAM. Тож налаштування Odoo визначають налаштування PostgreSQL:"),
        ("table", _SETTINGS_TABLE["uk"]),
        ("p", "З боку Odoo: приблизно 6 одночасних користувачів на воркер, не більше ніж 2 × ядра CPU + 1 воркерів; у середньому ~150 МБ на воркер для легких запитів і ~1 ГБ для важких (документація Odoo). `limit_memory_soft/hard` — це стеля для пікових навантажень, а не середнє."),
        ("h", "13. pgtune і pgconfig.org"),
        ("ul", [
            "**PGTune** (pgtune.leopard.in.ua): вказуєте версію PostgreSQL, ОС, тип бази, RAM, CPU, кількість з'єднань і тип диска та отримуєте блок для postgresql.conf. Для Odoo обирайте «Web application» або «OLTP».",
            "**PGConfig** (pgconfig.org): схожий інструмент із профілями (web, OLTP, data warehouse, mixed, desktop). Він також видає команди `ALTER SYSTEM` і пояснює кожен параметр.",
            "Жоден із них нічого не знає про Odoo: «з'єднання» вони беруть як задане і вважають, що вся RAM належить PostgreSQL. Якщо Odoo на тому ж сервері, вводьте лише частку PostgreSQL, а кількість з'єднань виводьте з воркерів.",
        ]),
        ("p", "Два приклади в стилі цих інструментів, підлаштовані під Odoo:"),
        ("code", "exA"),
        ("code", "exB"),
        ("note", "Саме це робить наш калькулятор: вводите CPU, RAM, кількість користувачів і чи працює PostgreSQL на тому ж сервері, а він видає odoo.conf і postgresql.conf разом, зокрема у вигляді ALTER SYSTEM. З повзунками видно, які рядки змінюються."),
        ("links", "Посилання"),
    ],
}

_SETTINGS_TABLE["ru"] = [["Настройка", "Эмпирическое правило", "От чего зависит в Odoo"],
    ["`max_connections`", "процессы Odoo × ~3 + запас, часто 100–200", "`workers` + `max_cron_threads` + gevent; `db_maxconn` — потолок на процесс, а не реальное потребление; ×2 с read-репликой (Odoo 18+)"],
    ["`shared_buffers`", "25 % RAM, которую получает PostgreSQL", "на общем сервере только от доли PostgreSQL, ведь воркерам Odoo тоже нужна RAM"],
    ["`effective_cache_size`", "~75 % этой RAM", "только подсказка для планировщика, ничего не выделяет"],
    ["`work_mem`", "(RAM − shared_buffers) / (соединения × 3)", "на каждую сортировку или hash и на соединение; большие отчёты Odoo используют несколько сразу, а слишком большое значение плюс много воркеров дают OOM"],
    ["`maintenance_work_mem`", "RAM/16, до 2 ГБ", "быстрее VACUUM, CREATE INDEX и обновление модулей"],
    ["`max_wal_size`", "4 ГБ+ (больше для крупных импортов)", "массовые импорты, `-u all` и миграции пишут много WAL"],
    ["`random_page_cost`", "1,1 на SSD/NVMe", "чтобы планировщик использовал индексы Odoo"],
    ["`jit`", "off", "Odoo выполняет много коротких запросов"],
    ["`idle_in_transaction_session_timeout`", "напр. 30 мин", "завершает забытые транзакции (сессии shell, сломанные скрипты)"]]

PGCHEAT["t"]["ru"] = {
    "title": "PostgreSQL для администратора Odoo: шпаргалка — бэкап, восстановление, пользователи, запросы, vacuum, индексы, настройки",
    "summary": "Всё нужное каждый день: pg_dump/pg_restore/pg_basebackup и бэкап через Odoo с помощью curl, размеры баз и топ-10 таблиц, пользователи и права, сброс паролей, поиск и остановка долгих запросов, vacuum, EXPLAIN ANALYZE, индексы и то, как настройки PostgreSQL зависят от воркеров Odoo. А также pgtune, pgconfig.org и наш калькулятор.",
    "body": [
        ("p", "Страница для закладок: команды PostgreSQL, которыми я пользуюсь для Odoo, сгруппированные по задачам. Odoo 16–19, PostgreSQL 13–17; замените `mydb`, `odoo` и хосты на свои."),
        ("note", "Перед любым действием, которое меняет данные (восстановление, DROP, VACUUM FULL, завершение сессий), сделайте свежий бэкап и сначала попробуйте на stage."),
        ("h", "1. Подключение и обзор в psql"),
        ("code", "connect"),
        ("h", "2. Какого размера базы и таблицы?"),
        ("code", "sizes"),
        ("p", "В Odoo в топ-10 почти всегда входят `mail_message`, `mail_tracking_value`, `ir_attachment` (только метаданные, сами файлы лежат в filestore), `account_move_line`, `stock_move` и таблицы `bus_bus`/`queue_job`."),
        ("h", "3. Бэкап: pg_dump, pg_dumpall, pg_basebackup"),
        ("code", "dump"),
        ("ul", [
            "`pg_dump` — одна база, логический дамп, переносится между версиями. Стандарт для Odoo.",
            "`pg_dumpall --globals-only` — роли и их пароли, которых нет в pg_dump.",
            "`pg_basebackup` — весь сервер, физическая копия: основа для реплик и восстановления на момент времени, только для той же мажорной версии.",
            "`--no-owner --no-acl` (`-O -x`): в дампе нет `ALTER OWNER` и `GRANT`, поэтому его можно восстановить под любой ролью. Работает и для pg_dump, и для pg_restore.",
            "Инструмента `pg_backup` не существует, обычно имеют в виду один из этих трёх.",
        ]),
        ("h", "4. Восстановление"),
        ("code", "restore"),
        ("h", "5. Через Odoo: веб и curl"),
        ("code", "web"),
        ("p", "Удобно для небольших баз и для людей без доступа к серверу. Для больших баз (десятки ГБ) zip-экспорт идёт долго и может упереться в `limit_time_real`, тогда лучше pg_dump. Никогда не оставляйте менеджер баз открытым: `list_db = False` на продакшене, включайте только временно или защитите `/web/database/*` в nginx."),
        ("h", "6. Пользователи, базы и права"),
        ("code", "roles"),
        ("p", "Роль Odoo должна быть владельцем своих баз и иметь `CREATEDB` только тогда, когда используется менеджер баз. Суперпользователем она не должна быть никогда."),
        ("h", "7. Сброс паролей"),
        ("code", "passwd"),
        ("p", "Не записывайте пароль Odoo напрямую в `res_users.password` через SQL: Odoo хранит хеш и не примет открытое значение. Через `odoo shell` Odoo сам его захеширует."),
        ("h", "8. Что выполняется сейчас и как остановить долгие запросы"),
        ("code", "activity"),
        ("ul", [
            "Сначала `pg_cancel_backend` (отменяет запрос, сессия остаётся), и только потом `pg_terminate_backend`.",
            "`idle in transaction` в течение минут — это ошибка в скрипте или открытый shell: такое состояние держит блокировки и мешает vacuum.",
            "Если остановить запрос воркера Odoo, его транзакция откатится: пользователь увидит ошибку, но данные останутся согласованными.",
        ]),
        ("h", "9. Мониторинг и vacuum"),
        ("code", "vacuum"),
        ("ul", [
            "**Autovacuum** выполняет ежедневную работу: не выключайте его, а для больших таблиц Odoo настройте отдельно.",
            "**VACUUM (ANALYZE)** работает онлайн: освобождает место для повторного использования и обновляет статистику. После восстановления или крупного импорта запустите `ANALYZE`.",
            "**VACUUM FULL** возвращает место на диске операционной системе, но полностью блокирует таблицу. Нужно окно обслуживания или `pg_repack`.",
            "Что отслеживать: мёртвые строки, `last_autovacuum`, возраст идентификаторов транзакций, место на диске, долгие транзакции.",
        ]),
        ("h", "10. Медленные запросы: EXPLAIN ANALYZE"),
        ("code", "explain"),
        ("p", "Откуда берутся медленные запросы? `log_min_duration_statement = 2000` пишет в лог PostgreSQL каждый запрос дольше 2 с вместе с текстом, а `pg_stat_statements` суммирует их. Скопируйте запрос, выполните `EXPLAIN (ANALYZE, BUFFERS)` на копии stage и читайте план от самого дорогого узла."),
        ("h", "11. Индексы: какая колонка имеет какой индекс"),
        ("code", "indexes"),
        ("p", "В Odoo индексы лучше создавать в модуле (`index=True` на поле): индекс, созданный вручную через SQL, Odoo не знает. Прежде чем создавать индекс, проверьте через `EXPLAIN`, что он действительно используется, и удаляйте индексы, которые не используются никогда."),
        ("h", "12. Настройки PostgreSQL и воркеры Odoo"),
        ("p", "PostgreSQL и Odoo делят один бюджет: соединения, а на одном сервере ещё и ту же RAM. Поэтому настройки Odoo определяют настройки PostgreSQL:"),
        ("table", _SETTINGS_TABLE["ru"]),
        ("p", "Со стороны Odoo: примерно 6 одновременных пользователей на воркер, не больше чем 2 × ядра CPU + 1 воркеров; в среднем ~150 МБ на воркер для лёгких запросов и ~1 ГБ для тяжёлых (документация Odoo). `limit_memory_soft/hard` — это потолок для пиковых нагрузок, а не среднее."),
        ("h", "13. pgtune и pgconfig.org"),
        ("ul", [
            "**PGTune** (pgtune.leopard.in.ua): указываете версию PostgreSQL, ОС, тип базы, RAM, CPU, число соединений и тип диска и получаете блок для postgresql.conf. Для Odoo выбирайте «Web application» или «OLTP».",
            "**PGConfig** (pgconfig.org): похожий инструмент с профилями (web, OLTP, data warehouse, mixed, desktop). Он также выдаёт команды `ALTER SYSTEM` и объясняет каждый параметр.",
            "Ни один из них ничего не знает об Odoo: «соединения» они берут как заданное и считают, что вся RAM принадлежит PostgreSQL. Если Odoo на том же сервере, вводите только долю PostgreSQL, а число соединений выводите из воркеров.",
        ]),
        ("p", "Два примера в стиле этих инструментов, подогнанные под Odoo:"),
        ("code", "exA"),
        ("code", "exB"),
        ("note", "Именно это делает наш калькулятор: вводите CPU, RAM, число пользователей и работает ли PostgreSQL на том же сервере, а он выдаёт odoo.conf и postgresql.conf вместе, в том числе в виде ALTER SYSTEM. С ползунками видно, какие строки меняются."),
        ("links", "Ссылки"),
    ],
}
