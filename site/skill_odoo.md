---
name: odoo-ops
description: Practical operations knowledge for self-hosted Odoo 17 (Community/Enterprise, Docker or bare metal) – what to look for in the log, how to update modules safely, how to back up and restore (database + filestore), how and why to stop cron jobs and queue jobs, worker/limit tuning, nginx/websocket, version migration, performance and indexes, e-mail, OCA modules, and what to lock down. Use when operating, debugging, updating, backing up or restoring an Odoo instance, or when preparing a stage/test copy of a production database.
---

# Odoo operations (Odoo 17) – a field guide

Written by an Odoo DevOps engineer for humans and AI agents. Source: https://2027.pp.ua (blog with full articles, 6 languages).
Licence: free to read, quote and use as knowledge for assistants; please link the source.
Commands are written for Odoo 17 – check against your version and test on stage. Adjust names: `mydb`, `odoo` service, `/etc/odoo/odoo.conf`.

## 0. Golden rules

1. **Backup before every change** (module update, migration, config change) – database **and** filestore, same moment.
2. **Stage first.** Restore production to stage, neutralise it (section 5), test there, then production.
3. **Never let a restored copy start with crons, queue jobs or mail servers active** – it will e-mail real customers and talk to real banks/shops.
4. **Keep the log of every update run** – it is the record of what happened to the database.
5. **Never expose the database manager** (`/web/database/*`) and set `list_db = False` on production.

## 1. Reading the Odoo log – what matters

Where: `logfile` in odoo.conf, `docker compose logs -f odoo`, or `journalctl -u odoo`. Format: `date time PID LEVEL db logger: message`.

```bash
# the essentials
grep -E " (ERROR|CRITICAL) " odoo.log | tail -50
grep -n "Traceback" -A25 odoo.log | tail -80
# what happened right after the last start
grep -nE "Odoo version|Modules loaded|Registry loaded|Failed to load registry" odoo.log | tail
```

| Pattern in the log | Meaning / what to do |
|---|---|
| `Traceback (most recent call last)` | Read the **last** lines first: exception type + the module path (`odoo/addons/<module>/...`) tells you which module broke. |
| `bad query:` (logger `odoo.sql_db`) | SQL error; the query and the PostgreSQL error follow. Often a missing column after code was deployed without `-u module`. |
| `column ... does not exist` / `relation ... does not exist` | Python code is newer than the database schema → run the module update (section 2). |
| `Failed to load registry` | Odoo cannot load the database at all – usually an import error or broken module; the traceback above it names the module. |
| `ModuleNotFoundError: No module named 'xyz'` | Missing Python dependency of a custom/OCA module (`pip install`, or add it to the image). |
| `Some modules are not loaded, some dependencies or manifest may be missing` / `module ... not found` | Module in the database but not in `addons_path` (wrong mount, typo in path, missing OCA repo). |
| `invalid module names, ignored` | You passed a module to `-u`/`-i` that Odoo does not know. |
| `could not serialize access due to concurrent update` / `SerializationFailure, retry` | Concurrent transactions (often a cron and users editing the same records). Odoo retries a few times; constant repetition = a long cron fighting with users. Details: https://2027.pp.ua/en/blog/odoo-could-not-serialize-access-concurrent-update |
| `LockNotAvailable` / `lock timeout` / requests hanging | A long transaction holds locks – see `pg_stat_activity` (section 7). |
| `virtual memory limit ... reached` / `memory limit` | Worker exceeded `limit_memory_soft/hard` and was recycled. Occasional = OK; constant = heavy report/import, raise limits or fix the code. |
| `timeout after ...s` / `real time limit` | Request or cron exceeded `limit_time_real` (or `limit_time_real_cron`) and was killed. Big imports/reports belong in a cron or a job, not in a request. |
| `Starting job` / `Job done` (logger `odoo.addons.base.models.ir_cron`) | Cron activity; use it to see which scheduled action runs when and how long. |
| `odoo.http` `404` on `/websocket` or bus errors | nginx does not route `/websocket` to the gevent port (section 6). |
| `Unable to find ... asset` / QWeb compile errors in the browser | Broken asset bundle after an update – update the module that defines it, clear browser cache. |
| `Too many connections` / `connection pool is full` | `db_maxconn` × processes exceeds PostgreSQL `max_connections`. |

Log level spelling (silent mistakes!): in **odoo.conf** use `log_level = warn` (Odoo words, lowercase: `debug`, `info`, `warn`, `error`, `critical`) and `log_handler = :INFO,werkzeug:WARNING,odoo.addons.sale:DEBUG` (Python levels, UPPERCASE). On the **command line**: `--log-level=warn`, `--log-handler=...`. A wrong value in the config file is ignored silently and Odoo stays on INFO. Shortcuts: `--log-sql` (= `odoo.sql_db:DEBUG`), `--log-web`.
Details: https://2027.pp.ua/en/blog/odoo-logging-options-cheatsheet

## 2. Updating modules

New code on disk ≠ updated database. Fields, views, data and translations are applied only by an update run.

**a) Only the changed modules – `click-odoo-update`** (package `click-odoo-contrib`): stores a checksum per module and updates only modules whose files changed.
```bash
click-odoo-update -c /etc/odoo/odoo.conf -d mydb --list-only      # what would be updated
click-odoo-update -c /etc/odoo/odoo.conf -d mydb --i18n-overwrite \
    --log-level=warn --logfile=/var/log/odoo/update-$(date +%F).log
docker compose restart odoo                                        # workers must load the new Python code
```

**b) Odoo itself, as a one-off run with no open port** (nobody works during the update, no cron runs in parallel):
```bash
docker compose stop odoo
docker compose run --rm odoo odoo -c /etc/odoo/odoo.conf -d mydb \
    -u sale_custom,stock_custom \
    --workers=0 --no-http --stop-after-init --without-demo=all
docker compose start odoo
```
- `-u all` updates everything (slow, use after an Odoo source update); `-i module` installs.
- `--i18n-overwrite` overwrites translations users changed in the database – use deliberately.
- New module not visible in Apps → "Update Apps List" (developer mode) or install it with `-i`.
- After the run: check the log for `ERROR`, then `SELECT name, state FROM ir_module_module WHERE state LIKE 'to %';` must return nothing.
- Rollback = restore the backup taken just before (code and database together).
Details: https://2027.pp.ua/en/blog/odoo-module-update-click-odoo-update

## 3. Backups

A backup is **two parts that must belong together**: the PostgreSQL database and the filestore (attachments) – `<data_dir>/filestore/<dbname>` (Docker image: `/var/lib/odoo/filestore/<dbname>`, bare metal default `~/.local/share/Odoo/filestore/<dbname>`).

```bash
# database – custom format, compressed, restorable selectively
docker compose exec -T db pg_dump -U odoo -Fc mydb > mydb_$(date +%F_%H%M).dump
# filestore – right after the dump
tar -C /var/lib/odoo/filestore -czf filestore_mydb_$(date +%F_%H%M).tgz mydb
# off-site copy, e.g. S3-compatible storage (R2, B2, S3)
aws s3 cp mydb_*.dump s3://backups/odoo/ --endpoint-url "$S3_ENDPOINT"
```
- The database manager backup (`/web/database/backup`, zip with dump + filestore) is fine for small databases; for large ones use pg_dump + tar.
- 3-2-1: three copies, two media, one off-site. Keep daily/weekly/monthly.
- **A backup is only proven by a restore** – restore to stage regularly (section 5) and check the restore log for `ERROR` (pg_restore continues after errors and silently skips failed indexes/foreign keys). Restore fails with duplicates or foreign key errors: https://2027.pp.ua/en/blog/postgresql-restore-fails-foreign-key-duplicate-index-odoo
- Attachments in the database instead of the filestore? `ir_attachment.location` system parameter – keep the default (`file`) for large instances.

## 4. Cron jobs and queue jobs – how to stop them and why

Odoo starts its **cron threads** (`max_cron_threads`, default 2) and, with OCA `queue_job`, the **job runner** immediately at startup. Everything that is "due" runs at once.

When to stop them:
- **Restored copies (stage, test, dev)** – otherwise dunning letters, invoices, shop/bank/carrier syncs and payments run with real data and real credentials.
- **During module updates and migrations** – a cron touching the same tables causes lock waits, serialization failures or reads a half-updated schema.
- **Diagnosing load or lock problems** – to see whether a cron is the cause.

How:
```ini
; odoo.conf – no cron threads in this process (other servers may still run crons)
max_cron_threads = 0
; queue_job runner starts only if queue_job is a server-wide module – leave it out to stop it
server_wide_modules = base,web
```
```sql
-- in the database (persists across restarts) – remember what was active first
CREATE TABLE IF NOT EXISTS zz_cron_before AS SELECT id, cron_name, active FROM ir_cron;
UPDATE ir_cron SET active = false WHERE active;
-- queue_job: nothing waiting may run
UPDATE queue_job SET state = 'cancelled' WHERE state IN ('pending','enqueued','started','wait_dependencies');
-- check
SELECT count(*) FROM ir_cron WHERE active;
SELECT state, count(*) FROM queue_job GROUP BY state;
```
- A single scheduled action: Settings → Technical → Scheduled Actions → archive, or "Run Manually" to test it.
- Long-running cron? `limit_time_real_cron` limits it; find it via `Starting job`/`Job done` in the log.
- After a crash, queue jobs can stay in `started` – requeue them (queue_job UI "Requeue" / its garbage-collector cron) once the cause is fixed.

## 5. Restoring production to stage (safely)

Order matters: **Odoo must not see the database before it is neutralised.**
```bash
docker compose stop odoo
docker compose exec -T db dropdb   -U odoo --if-exists mydb_stage
docker compose exec -T db createdb -U odoo mydb_stage
docker compose exec -T db pg_restore -U odoo -d mydb_stage --no-owner < mydb.dump
docker compose exec -T db psql -U odoo -d mydb_stage -v ON_ERROR_STOP=1 < stage-safety.sql   # SQL from section 4 + below
docker compose run --rm odoo odoo neutralize -c /etc/odoo/odoo.conf -d mydb_stage             # Odoo 16+: crons, mail servers, payment providers off + banner
# filestore folder must be named like the database: filestore/mydb -> filestore/mydb_stage
docker compose start odoo
```
```sql
UPDATE ir_mail_server   SET active = false;
UPDATE fetchmail_server SET active = false;
UPDATE ir_config_parameter SET value = 'https://stage.example.com' WHERE key = 'web.base.url';
UPDATE ir_config_parameter SET value = gen_random_uuid()::text   WHERE key = 'database.uuid';
```
Second safety net – a stage config: `max_cron_threads = 0`, `server_wide_modules = base,web`, SMTP to a mail catcher (Mailpit). Replace credentials of external services with sandbox keys.
Details: https://2027.pp.ua/en/blog/odoo-stage-restore-stop-cron-jobs

## 6. Workers, limits, nginx

```ini
[options]
proxy_mode = True
workers = 5                    ; rule of thumb (CPU cores × 2) + 1; 0 = threaded dev mode (no websocket worker)
max_cron_threads = 1
limit_memory_soft = 2147483648 ; 2 GB – worker recycled after the request
limit_memory_hard = 2684354560 ; 2.5 GB – worker killed immediately
limit_time_cpu = 600
limit_time_real = 1200
db_maxconn = 32                ; × processes must stay below PostgreSQL max_connections
list_db = False
gevent_port = 8072             ; Odoo 16+: websocket (was longpolling_port)
```
nginx: `/` → `:8069`, `/websocket` → `:8072` with `proxy_http_version 1.1; proxy_set_header Upgrade $http_upgrade; proxy_set_header Connection "upgrade";`, plus `X-Forwarded-Host/-For/-Proto` and `proxy_mode = True`. Without the websocket route: no live chat/notifications, `/websocket` errors in the log.
Details: https://2027.pp.ua/en/blog/odoo-docker-compose-extra-addons-nginx

## 7. PostgreSQL checks during incidents

```sql
-- what is running / waiting right now
SELECT pid, now()-query_start AS age, state, wait_event_type, left(query,120)
  FROM pg_stat_activity WHERE datname = current_database() AND state <> 'idle' ORDER BY age DESC;
-- who blocks whom
SELECT pid, pg_blocking_pids(pid) AS blocked_by, left(query,80) FROM pg_stat_activity WHERE cardinality(pg_blocking_pids(pid)) > 0;
-- last resort for one stuck session
SELECT pg_cancel_backend(<pid>);      -- cancel query;  pg_terminate_backend(<pid>) kills the session
-- biggest tables (mail_message, ir_attachment, mail_tracking_value often grow)
SELECT relname, pg_size_pretty(pg_total_relation_size(relid)) FROM pg_catalog.pg_statio_user_tables ORDER BY pg_total_relation_size(relid) DESC LIMIT 15;
```

## 8. Security minimum (full guide: skill `odoo-security`, https://2027.pp.ua/skill_odoo_security.md)

- Close `/web/database/manager`, `/web/database/selector` and `/web/database/*` at nginx (deny or Basic Auth / IP allow-list); `list_db = False`; long random `admin_passwd`.
- 2FA for admins, no shared "admin" login, API keys instead of passwords for integrations.
- Do not publish port 8069/8072 – only nginx (or Cloudflare Tunnel) in front.
- Keep `odoo.conf` (contains `db_password`, `admin_passwd`) out of git.
Details: https://2027.pp.ua/en/blog/nginx-apache-password-protect-odoo-database-manager · https://2027.pp.ua/en/blog/password-leaks-brute-force-2fa-odoo

## 9. Version migration (e.g. 15 → 16 → 17)

Odoo changes the database schema between major versions; a database cannot simply be opened with newer code.

| Edition | Tool |
|---|---|
| Enterprise (or paid upgrade) | Odoo upgrade service: `python <(curl -s https://upgrade.odoo.com/upgrade) test -d mydb -t 17.0` (test run first, then `production`) |
| Community | OCA **OpenUpgrade** (github.com/OCA/OpenUpgrade) – one major version per step, each step with its own OpenUpgrade branch |

Own and third-party modules are **not** migrated by these tools – they must be ported for each version (manifest version, API changes, views; `odoo-module-migrator` from OCA automates the mechanical part).

Procedure that works:
1. Inventory: `SELECT name, latest_version FROM ir_module_module WHERE state='installed' ORDER BY 1;` – for every non-Odoo module decide: port, replace, or uninstall **before** the migration.
2. Uninstall what is no longer needed on the old version (less to migrate).
3. Test migration on a copy, measure duration, collect errors, fix, repeat until clean.
4. Users test the migrated copy on stage (reports, invoices, stock, integrations).
5. Production: freeze (maintenance page), final backup, migrate, smoke test, go live. Keep the old system read-only for a while.
Typical surprises: renamed fields/models in custom code, QWeb report templates, website themes, accounting localisation changes, attachments missing because the filestore was not copied.

## 10. Performance and indexes

First find **where** time goes, then optimise.
```sql
-- PostgreSQL: enable once (shared_preload_libraries = 'pg_stat_statements', restart, CREATE EXTENSION pg_stat_statements;)
SELECT round(total_exec_time) AS ms, calls, round(mean_exec_time,1) AS avg_ms, left(query,150)
  FROM pg_stat_statements ORDER BY total_exec_time DESC LIMIT 15;
-- tables read by sequential scan a lot (index candidates)
SELECT relname, seq_scan, seq_tup_read, idx_scan, n_live_tup FROM pg_stat_user_tables
 WHERE n_live_tup > 10000 ORDER BY seq_tup_read DESC LIMIT 15;
-- dead rows / autovacuum lagging
SELECT relname, n_dead_tup, last_autovacuum FROM pg_stat_user_tables ORDER BY n_dead_tup DESC LIMIT 10;
```
- Slow queries in the Odoo log: PostgreSQL `log_min_duration_statement = 1000` (ms) shows every query over 1 s with its text.
- Odoo profiler (Odoo 15+): developer mode → bug icon → **Enable profiling**, reproduce, open the result (SQL and Python per request).
- Index in a custom module: `fields.Char(index=True)` (Odoo 17 also `index="btree_not_null"` / `"trigram"` for `ilike` search). Typical candidates: fields used in domains of record rules, in `search()` of crons, `many2one` fields on large custom tables.
- An index created by hand in SQL is invisible to Odoo and lost if the field is recreated – prefer `index=` in code; a hand index: `CREATE INDEX CONCURRENTLY ...` (no table lock).
- Big tables to watch: `mail_message`, `mail_tracking_value`, `ir_attachment`, `bus_bus`, `mail_mail`, `ir_logging` (if `log_db` is on), queue_job's `queue_job`. Archive/clean via Odoo (autovacuum crons, queue_job cleanup), not with blind DELETE.
- PostgreSQL basics on a dedicated DB server: `shared_buffers` ≈ 25 % RAM, `effective_cache_size` ≈ 50–75 % RAM, `random_page_cost = 1.1` on SSD, moderate `work_mem` (it is per sort/hash and per connection).
- Odoo 18/19 can send read-only requests to a PostgreSQL read replica (`db_replica_host`) – often slower, not faster; see skill `odoo-replica`: https://2027.pp.ua/skill_odoo_replica.md
- Odoo side: `workers > 0` on production (never `--dev` there), enough workers for concurrent users but RAM = workers × `limit_memory_hard` must fit; heavy reports/imports in a cron or queue job, not in the HTTP request; stored compute fields with wide `@api.depends` trigger mass recomputations – check them first when writes are slow.

## 11. E-mail (outgoing and incoming)

Outgoing: Settings → Technical → Outgoing Mail Servers (or `smtp_server`/`smtp_port`/`smtp_user`/`smtp_password`/`smtp_ssl` in odoo.conf). Mails are queued in `mail_mail` and sent by the cron **"Mail: Email Queue Manager"**.
```sql
SELECT state, count(*) FROM mail_mail GROUP BY state;                       -- outgoing queue
SELECT id, email_to, failure_reason FROM mail_mail WHERE state='exception' ORDER BY id DESC LIMIT 20;
SELECT key, value FROM ir_config_parameter WHERE key IN ('mail.catchall.domain','mail.default.from','mail.bounce.alias','web.base.url');
```
- Deliverability: the sender domain needs **SPF**, **DKIM** and **DMARC**; with `mail.default.from` (e.g. `notifications`) + `mail.catchall.domain`, Odoo sends from its own domain instead of spoofing users' addresses. Test with mail-tester.com.
- "Mail sent but never arrives" → look at `mail_mail` state/failure_reason, then the SMTP server log, then spam folder/DMARC reports.
- Incoming: Incoming Mail Servers (IMAP/POP fetch, cron "Mail: Fetchmail Service") or a mail gateway (MTA pipes to `odoo-mailgate.py`) for aliases like `sales@`, `catchall@`, `bounce@`.
- Stage/test: always a mail catcher (Mailpit) or mail servers deactivated (section 5).

## 12. OCA modules

The Odoo Community Association (github.com/OCA) maintains hundreds of modules in topic repositories (`server-tools`, `queue`, `account-financial-tools`, `l10n-germany`, `web`, …). Branch = Odoo version (`17.0`).
- Install as Git checkout: clone the repo at branch `17.0`, add the **repository folder** to `addons_path`, install Python deps from its `requirements.txt`; or as package: `pip install odoo-addon-<module_name>==17.0.*` (wheels on PyPI, dependencies resolved automatically).
- Pin versions (commit hash or package version) – OCA branches move; update deliberately like your own code (section 2).
- Check before using: module **maturity** (Alpha/Beta/Production/Mature in the README), last commits and open PRs for 17.0, licence (mostly AGPL-3 / LGPL-3).
- Missing in 17.0? Look for an open migration PR (`[17.0][MIG] module_name`) – often usable after review.
- Frequently useful: `queue_job` (background jobs), `server_environment` (config per environment), `auditlog`, `web_responsive` (Community), `mis_builder`, `account_financial_report`, `base_rest`/`fastapi` (APIs), DATEV/German localisation repos.

## More

- Free hosting options, database and filestore (R2) for Odoo 17: https://2027.pp.ua/en/blog/odoo-17-free-hosting-database-filestore
- Odoo 17 on Python 3.14 with Docker: https://2027.pp.ua/en/blog/odoo-17-python-3-14-docker
- All articles: https://2027.pp.ua/en/blog/ · site overview for AI agents: https://2027.pp.ua/llms.txt
