#!/usr/bin/env python3
"""pgload – a small PostgreSQL load generator: many parallel connections insert (and optionally read) binary blocks.

Compare the same run against different databases or settings: local socket vs. remote host, with and without a
synchronous replica, synchronous_commit on/off, wal_compression, max_wal_size, disk types ...

Connection only via the standard libpq environment variables – no passwords in the code or on the command line:
    PGHOST, PGPORT, PGUSER, PGPASSWORD (or ~/.pgpass), PGDATABASE

    export PGHOST=/run/postgresql PGDATABASE=loadtest PGUSER=odoo      # password from ~/.pgpass
    ./pgload.py --workers 32 --count 20000 --block 200 --size 64 --randomize
    ./pgload.py --mode mixed --read-ratio 0.7 --workers 64 --count 50000
    ./pgload.py --drop                                                  # remove the test schema afterwards

Writes into its own schema "pgload" – run it on a test/stage database, never blindly on production:
count × size of data plus WAL, replication traffic and bigger backups.

Based on an internal tool of the author; source: https://2027.pp.ua/en/blog/postgresql-load-test-pgload-replica
"""
import argparse
import os
import random
import statistics
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

import psycopg2
import psycopg2.pool

DDL = """
CREATE SCHEMA IF NOT EXISTS pgload;
CREATE TABLE IF NOT EXISTS pgload.ldata (
    id    bigserial PRIMARY KEY,
    ctime timestamptz NOT NULL DEFAULT clock_timestamp(),
    rmark double precision NOT NULL DEFAULT random(),
    size  integer NOT NULL DEFAULT 0,
    data  bytea
);
CREATE INDEX IF NOT EXISTS i_pgload_ctime ON pgload.ldata (ctime);
CREATE INDEX IF NOT EXISTS i_pgload_rmark ON pgload.ldata (rmark);
"""
INSERT = "INSERT INTO pgload.ldata (size, data) VALUES (%s, %s)"
SELECT = "SELECT id, size, length(data) FROM pgload.ldata WHERE rmark >= %s ORDER BY rmark LIMIT %s"


def log(msg):
    print(f"{datetime.now():%Y-%m-%d %H:%M:%S} {msg}", flush=True)


def percentile(values, p):
    if not values:
        return 0.0
    values = sorted(values)
    k = (len(values) - 1) * p / 100
    f, c = int(k), min(int(k) + 1, len(values) - 1)
    return values[f] + (values[c] - values[f]) * (k - f)


class Runner:
    def __init__(self, args):
        self.args = args
        self.pool = psycopg2.pool.ThreadedConnectionPool(1, args.workers, application_name="pgload")
        self.payload = os.urandom(args.size * 1024)
        self.lock = threading.Lock()
        self.lat = {"insert": [], "select": []}
        self.bytes = 0
        self.errors = 0

    def one(self, kind):
        conn = self.pool.getconn()
        try:
            conn.autocommit = True                     # one statement = one transaction = one commit
            t0 = time.perf_counter()
            with conn.cursor() as cur:
                if kind == "insert":
                    sz = random.randint(len(self.payload) // 2, len(self.payload)) if self.args.randomize else len(self.payload)
                    cur.execute(INSERT, (sz, self.payload[:sz]))
                else:
                    sz = 0
                    cur.execute(SELECT, (random.random(), self.args.read_rows))
                    cur.fetchall()
            dt = time.perf_counter() - t0
            with self.lock:
                self.lat[kind].append(dt)
                self.bytes += sz
        except Exception as e:                         # noqa: BLE001 – count and continue, a load test must not stop
            with self.lock:
                self.errors += 1
            log(f"ERROR {kind}: {e}".strip())
        finally:
            self.pool.putconn(conn)

    def report(self, t_start, final=False):
        el = time.perf_counter() - t_start
        with self.lock:
            parts = []
            for kind, v in self.lat.items():
                if v:
                    parts.append(f"{kind}: n={len(v)} {len(v) / el:.0f}/s avg={statistics.fmean(v) * 1000:.1f}ms "
                                 f"p50={percentile(v, 50) * 1000:.1f} p95={percentile(v, 95) * 1000:.1f} "
                                 f"p99={percentile(v, 99) * 1000:.1f} max={max(v) * 1000:.1f}ms")
            mb = self.bytes / 1024 / 1024
            log(("RESULT " if final else "") + " | ".join(parts) + f" | written {mb:.0f} MB ({mb / el:.1f} MB/s) | errors {self.errors} | {el:.0f}s")

    def run(self):
        a = self.args
        conn = self.pool.getconn()
        try:
            conn.autocommit = True
            with conn.cursor() as cur:
                cur.execute(DDL)
                cur.execute("SELECT current_setting('synchronous_commit'), current_setting('server_version'), "
                            "inet_server_addr(), (SELECT count(*) FROM pg_stat_replication)")
                sc, ver, addr, repl = cur.fetchone()
        finally:
            self.pool.putconn(conn)
        log(f"server {addr or 'unix socket'} PostgreSQL {ver}, synchronous_commit={sc}, replicas={repl}; "
            f"workers={a.workers} count={a.count} size={a.size}kB mode={a.mode}")
        t0 = time.perf_counter()
        done = 0
        with ThreadPoolExecutor(max_workers=a.workers) as ex:
            while done < a.count:
                n = min(a.block, a.count - done)
                kinds = ["select" if a.mode == "select" or (a.mode == "mixed" and random.random() < a.read_ratio)
                         else "insert" for _ in range(n)]
                list(ex.map(self.one, kinds))          # wait for the whole block
                done += n
                self.report(t0)
        self.report(t0, final=True)


def drop():
    with psycopg2.connect(application_name="pgload") as conn, conn.cursor() as cur:
        cur.execute("DROP SCHEMA IF EXISTS pgload CASCADE")
    log("schema pgload dropped")


def main():
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("-w", "--workers", type=int, default=32, help="parallel connections (default 32)")
    p.add_argument("-c", "--count", type=int, default=10000, help="operations in total (default 10000)")
    p.add_argument("-b", "--block", type=int, default=100, help="operations per block / progress line (default 100)")
    p.add_argument("-s", "--size", type=int, default=64, help="max. data per insert in kB (default 64)")
    p.add_argument("-r", "--randomize", action="store_true", help="random size between size/2 and size")
    p.add_argument("-m", "--mode", choices=["insert", "select", "mixed"], default="insert")
    p.add_argument("--read-ratio", type=float, default=0.5, help="share of reads in mixed mode (default 0.5)")
    p.add_argument("--read-rows", type=int, default=50, help="rows per read (default 50)")
    p.add_argument("--drop", action="store_true", help="drop the pgload schema and exit")
    a = p.parse_args()
    if a.drop:
        return drop()
    if "PGPASSWORD" in os.environ and os.environ.get("PGHOST", "").startswith("/"):
        log("hint: PGPASSWORD is set although a Unix socket is used – prefer ~/.pgpass or peer auth")
    Runner(a).run()


if __name__ == "__main__":
    sys.exit(main())
