---
name: odoo-ops
description: Practical operations knowledge for self-hosted Odoo 17 (Community/Enterprise, Docker or bare metal) – what to look for in the log, how to update modules safely, how to back up and restore (database + filestore), how and why to stop cron jobs and queue jobs, worker/limit tuning, nginx/websocket, and what to lock down. Use when operating, debugging, updating, backing up or restoring an Odoo instance, or when preparing a stage/test copy of a production database.
---

# Odoo operations (Odoo 17) – a field guide

Written by an Odoo DevOps engineer for humans and AI agents. Source: https://2027.pp.ua (blog with full articles, 6 languages).
Licence: free to read, quote and use as knowledge for assistants; please link the source.
Every command below was used on real systems. Adjust names: `mydb`, `odoo` service, `/etc/odoo/odoo.conf`.

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
| `could not serialize access due to concurrent update` / `SerializationFailure, retry` | Concurrent transactions (often a cron and users editing the same records). Odoo retries a few times; constant repetition = a long cron fighting with users. |
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
- **A backup is only proven by a restore** – restore to stage regularly (section 5).
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

## 8. Security minimum

- Close `/web/database/manager`, `/web/database/selector` and `/web/database/*` at nginx (deny or Basic Auth / IP allow-list); `list_db = False`; long random `admin_passwd`.
- 2FA for admins, no shared "admin" login, API keys instead of passwords for integrations.
- Do not publish port 8069/8072 – only nginx (or Cloudflare Tunnel) in front.
- Keep `odoo.conf` (contains `db_password`, `admin_passwd`) out of git.
Details: https://2027.pp.ua/en/blog/nginx-apache-password-protect-odoo-database-manager · https://2027.pp.ua/en/blog/password-leaks-brute-force-2fa-odoo

## More

- Free hosting options, database and filestore (R2) for Odoo 17: https://2027.pp.ua/en/blog/odoo-17-free-hosting-database-filestore
- Odoo 17 on Python 3.14 with Docker: https://2027.pp.ua/en/blog/odoo-17-python-3-14-docker
- All articles: https://2027.pp.ua/en/blog/ · site overview for AI agents: https://2027.pp.ua/llms.txt
