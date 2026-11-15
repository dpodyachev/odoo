---
name: odoo-replica
description: Odoo 18/19 with a PostgreSQL read replica (db_replica_host / db_replica_port) – how Odoo decides between replica and primary (readonly routes, @api.readonly, auth='none'), why it can make Odoo slower (double cursor, network latency, retries, connection pools, replication lag), how to set up streaming replication, how to measure and when it is worth it. Use when configuring, debugging or evaluating an Odoo read replica, or when Odoo got slower after enabling one.
---

# Odoo 18/19 + PostgreSQL read replica

By an Odoo DevOps engineer, for humans and AI agents. Source: https://2027.pp.ua · article: https://2027.pp.ua/en/blog/odoo-19-postgresql-read-replica
Facts below are taken from the Odoo source (`odoo/tools/config.py`, `odoo/sql_db.py`, `odoo/http.py`, `odoo/orm/registry.py`, branches 18.0/19.0). Odoo 17 and older have no replica support.

## 1. Enable

```ini
[options]
db_host = 10.0.0.10            ; primary (read/write)
db_replica_host = 10.0.0.11    ; hot-standby replica (read-only)
db_replica_port = 5432
; same db_user / db_password / db_name as the primary
```
Odoo 19 also reads the environment variables `PGHOST_REPLICA`, `PGPORT_REPLICA`. Command line: `--db_replica_host`, `--db_replica_port`.
- Odoo 18: an **empty** `db_replica_host =` meant "read-only connection to the same server" (for testing).
- Odoo 19: that is gone (warning in the log); use `dev_mode = replica` / `--dev=replica` to simulate a replica on the same server.

## 2. What goes where (request flow)

1. **Every** HTTP request with a database first opens a **read-only cursor** (on the replica, if configured) to check the registry and match the route.
2. Route marked read-only → the request is served entirely on the replica.
   - `@http.route(..., readonly=True)` or a callable deciding per request.
   - Default: routes with `auth='none'` are read-only, everything else read/write.
   - `/web/dataset/call_kw` and `call_button` are read-only **only** if the called model method is decorated `@api.readonly` (`search`, `search_read`, `search_count`, `search_fetch`, `read`, `name_search`, … and the web client's read methods).
3. Route is read/write (save, create, buttons, onchange, most controllers) → the replica cursor is **closed** and a new cursor on the **primary** is opened.
4. A read-only route that tries to write → PostgreSQL `ReadOnlySqlTransaction` → log warning `... retrying with a read/write cursor` → the **whole request runs again** on the primary.
5. Replica unreachable → warning `Failed to open a readonly cursor, falling back to read-write cursor for 20min 0sec` → everything goes to the primary for 20 minutes, then Odoo tries again.
6. Two connection pools per process (read-only and read/write), each up to `db_maxconn`.
7. Crons, `-u` updates and shell use the primary.

## 3. Why it can be slower (checked list)

| Cause | Effect | Check |
|---|---|---|
| Replica not in the same LAN (other DC, VPN, cloud region) | Odoo sends many small queries per request; +1–20 ms each → seconds per click | `psql -h <replica> -c '\timing on' -c 'select 1'` from the Odoo host; compare with the primary |
| Every write request starts on the replica, then switches | extra connection + queries on the replica before the real work on the primary | compare with `--dev=replica` on one server (no network) |
| Custom/OCA routes or methods marked read-only that write | request executed twice (replica, then primary) | `grep -c "retrying with a read/write cursor" odoo.log` |
| Replica on weaker hardware / cold cache | slower reads than the primary | `EXPLAIN (ANALYZE, BUFFERS)` of a slow query on both |
| More connections (two pools × workers) | `max_connections` reached, waits | `SELECT count(*), application_name FROM pg_stat_activity GROUP BY 2;` on both |
| Replication lag | not slower, but stale data right after saving (list shows old values) | on replica: `SELECT now() - pg_last_xact_replay_timestamp();` |
| Queries cancelled on the replica | `canceling statement due to conflict with recovery` → errors/retries | set `hot_standby_feedback = on` on the replica |

How to isolate network vs. logic: run the same scenario (e.g. Locust or the browser network tab) three times – (a) no replica, (b) `--dev=replica` on the same server, (c) real replica. (b) slower than (a) → Odoo's own overhead; (c) much slower than (b) → network/replica hardware.

## 4. PostgreSQL streaming replication (minimal)

```bash
# primary: postgresql.conf
wal_level = replica
max_wal_senders = 10
# primary: pg_hba.conf
host replication replicator 10.0.0.11/32 scram-sha-256
# primary: CREATE ROLE replicator WITH REPLICATION LOGIN PASSWORD '...';

# replica: empty data dir, then
pg_basebackup -h 10.0.0.10 -U replicator -D /var/lib/postgresql/16/main -R -X stream -P
# replica: postgresql.conf
hot_standby = on
hot_standby_feedback = on          # fewer query cancellations
max_standby_streaming_delay = 30s

# primary: replication status and lag
SELECT client_addr, state, sync_state, replay_lag FROM pg_stat_replication;
```
- Use **physical streaming replication** (hot standby). Logical replication is not what Odoo's replica mode expects.
- `synchronous_commit = remote_apply` + `synchronous_standby_names` gives read-your-writes but makes every write wait for the replica – usually not worth it for Odoo.
- The replica is also your **failover**: even without `db_replica_host` it is valuable (promote with `pg_ctl promote` / `SELECT pg_promote();`).

## 5. When it pays off – and when not

Worth trying when **all** of these hold:
- the primary is the bottleneck (CPU/IO) and the load is **read-heavy**: public website/eCommerce pages (`auth='public'` read-only routes), portals, dashboards, list views, reports, API reads;
- replica in the same LAN/AZ, round-trip < 1 ms, same hardware class;
- custom modules reviewed: no writes in read-only routes, `@api.readonly` only on methods that really only read.

Not worth it / first do something else:
- small and medium instances (tens of users): tune the primary first – indexes, `pg_stat_statements`, workers, PostgreSQL memory (see https://2027.pp.ua/skill_odoo.md section 10);
- write-heavy workloads (POS, stock moves, imports, MRP): writes go to the primary anyway, and they pay the extra replica step;
- replica far away (other region, over VPN/Internet).

## 6. Custom code checklist

- Controller only reads → `@http.route(..., readonly=True)`; it reads **and** writes → leave the default (read/write).
- Model method callable via RPC that only reads → `@api.readonly`; never on methods that write, send mail, create activities or update "last seen" fields.
- Watch the log after deployment for `retrying with a read/write cursor` – each one names a route that should not be read-only.
- Do not rely on reading data you just wrote in a previous request from a read-only route (replication lag).
