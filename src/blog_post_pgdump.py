# Статья: pg_dump и pg_restore для Odoo – все варианты: Docker, systemd (без докера), внешний сервер, форматы, отдельные таблицы,
# filestore, ZIP менеджера баз, бэкап по расписанию, типичные ошибки. en, de, ru, uk (fr/el – английская версия).

PGDUMP = {
    "slug": "pg-dump-pg-restore-odoo-docker-systemd-remote",
    "date": "2026-11-19",
    "tags": ["PostgreSQL", "Backup", "pg_dump", "pg_restore", "Docker", "Odoo"],
    "code": {
        "where": ("bash · first: how does PostgreSQL run here?", """grep -E '^(db_host|db_port|db_user|data_dir)' /etc/odoo/odoo.conf   # where Odoo connects (Docker: inside the container)

docker ps --format '{{.Names}}  {{.Image}}'      # a container with image postgres:NN → PostgreSQL in Docker
systemctl list-units 'postgresql*'               # postgresql@16-main.service → PostgreSQL as a system service
pg_lsclusters                                    # Debian/Ubuntu: version, cluster, port, status, data directory
psql --version; pg_dump --version                # client version on THIS machine
sudo -u postgres psql -c 'select version();'     # server version (native install)"""),
        "native": ("bash · PostgreSQL as a system service (systemd, no Docker)", """# as the postgres superuser via the local socket (peer authentication)
sudo -u postgres pg_dump -Fc -d mydb > /var/backups/odoo/mydb-$(date +%F).dump    # '>' is opened by YOUR shell: no permission problems
sudo -u postgres pg_dump -Fc -d mydb -f /var/lib/postgresql/mydb.dump              # -f writes as postgres: the folder must be writable for postgres

# as the Odoo user with a password over TCP (no sudo needed)
pg_dump -h 127.0.0.1 -U odoo -Fc -d mydb -f mydb.dump          # password from ~/.pgpass (see below) or PGPASSWORD

# several PostgreSQL versions on one server (Debian/Ubuntu pg_wrapper)
pg_lsclusters
sudo -u postgres pg_dump --cluster 16/main -Fc -d mydb > mydb.dump
# RHEL/Rocky: binaries in /usr/pgsql-16/bin, service postgresql-16
sudo -u postgres /usr/pgsql-16/bin/pg_dump -Fc -d mydb > mydb.dump

systemctl status postgresql@16-main      # Debian/Ubuntu: 'postgresql.service' is only an umbrella unit
journalctl -u postgresql@16-main -n 50"""),
        "docker": ("bash · PostgreSQL in Docker (docker compose)", """# dump: -T is mandatory – without it Docker allocates a TTY and corrupts the binary dump (\\n → \\r\\n)
docker compose exec -T db pg_dump -U odoo -Fc mydb > mydb-$(date +%F).dump
docker exec -i my-postgres pg_dump -U odoo -Fc mydb > mydb.dump            # the same without compose

# restore from stdin (custom format, but without -j)
docker compose exec -T db createdb -U odoo mydb_copy
docker compose exec -T db pg_restore -U odoo -d mydb_copy --no-owner < mydb.dump

# parallel restore needs a FILE inside the container
docker cp mydb.dump my-postgres:/tmp/mydb.dump
docker exec my-postgres pg_restore -U odoo -d mydb_copy --no-owner -j 4 /tmp/mydb.dump
docker exec my-postgres rm /tmp/mydb.dump

# no client on the host / wrong version: a throw-away container with the right client
docker run --rm --network host -e PGPASSWORD -v "$PWD":/backup postgres:16 \\
    pg_dump -h 127.0.0.1 -U odoo -Fc -d mydb -f /backup/mydb.dump"""),
        "remote": ("bash · database on another server or a managed database", """# directly (port 5432 reachable, TLS required by most cloud databases)
pg_dump "host=db.example.com port=5432 dbname=mydb user=odoo sslmode=require" -Fc -f mydb.dump

# password without typing it: ~/.pgpass, mode 600 – host:port:db:user:password
echo 'db.example.com:5432:mydb:odoo:SECRET' >> ~/.pgpass && chmod 600 ~/.pgpass

# port closed from outside: SSH tunnel
ssh -fN -L 15432:127.0.0.1:5432 admin@db.example.com
pg_dump -h 127.0.0.1 -p 15432 -U odoo -Fc -d mydb -f mydb.dump

# or run pg_dump THERE and stream the result here (nothing stored on the server)
ssh admin@db.example.com "sudo -u postgres pg_dump -Fc -d mydb" > mydb.dump

# copy prod → stage in one pipe, without an intermediate file (no -j possible)
pg_dump -h prod-db -U odoo -Fc -d mydb | pg_restore -h stage-db -U odoo -d mydb_stage --no-owner"""),
        "formats": ("bash · the four formats", """pg_dump -Fp mydb | gzip > mydb.sql.gz      # plain SQL: readable, restore with psql, no selective/parallel restore
pg_dump -Fc mydb -f mydb.dump               # custom: compressed, pg_restore, single tables, -j on restore  ← default choice
pg_dump -Fd -j 8 mydb -f mydb.dir           # directory: the only format that also DUMPS in parallel – big databases
pg_dump -Ft mydb -f mydb.tar                # tar: rarely needed

pg_dump -Fc -Z 9 mydb -f mydb.dump          # stronger compression (slower)
pg_dump -Fc --compress=zstd:5 mydb -f mydb.dump    # PostgreSQL 16+: zstd – faster and smaller than gzip
pg_dumpall --globals-only > globals.sql     # roles and passwords – NOT in pg_dump; needed for a full server move"""),
        "restore": ("bash · restore: new database, owner, overwrite", """# 1) empty database in UTF8, owner = the Odoo user
sudo -u postgres createdb -O odoo -E UTF8 -T template0 mydb_restored

# 2a) custom/directory format; as postgres, objects belong to odoo thanks to --role
sudo -u postgres pg_restore -d mydb_restored --no-owner --role=odoo -j 4 mydb.dump 2> restore.log
grep -c ERROR restore.log                     # 0 – otherwise read the log (see the article on restore errors)

# 2b) plain SQL
gunzip -c mydb.sql.gz | sudo -u postgres psql -d mydb_restored -v ON_ERROR_STOP=1

# overwrite an existing database: better restore under a NEW name and swap
sudo -u postgres psql -c "select pg_terminate_backend(pid) from pg_stat_activity where datname='mydb'"
sudo -u postgres psql -c 'ALTER DATABASE mydb RENAME TO mydb_old'
sudo -u postgres psql -c 'ALTER DATABASE mydb_restored RENAME TO mydb'
# (pg_restore --clean --if-exists -d mydb also works, but you have no way back if it breaks halfway)"""),
        "tables": ("bash · single tables, list, exclusions", """pg_restore -l mydb.dump | less                          # table of contents of a custom dump
pg_restore -l mydb.dump | grep -c 'TABLE DATA'

pg_dump -Fc -d mydb -t res_partner -t res_partner_bank -f partners.dump     # only these tables
pg_dump -Fc -d mydb --exclude-table-data='bus_bus' -f mydb.dump            # structure yes, data no (test copies)

# one table back from a full dump: into a SCRATCH database, then copy what you need with SQL
sudo -u postgres createdb -O odoo scratch
sudo -u postgres pg_restore -d scratch --no-owner --role=odoo -t res_partner mydb.dump
# selective restore by list: comment lines out with ';' and pass the list back
pg_restore -l mydb.dump > toc.txt ; vi toc.txt ; pg_restore -L toc.txt -d scratch mydb.dump"""),
        "filestore": ("bash · Odoo: the filestore belongs to the backup", """# attachments, images, PDFs are NOT in the database – they are files: <data_dir>/filestore/<database>
#   native install: ~odoo/.local/share/Odoo/filestore/mydb   (data_dir in odoo.conf)
#   official Docker image: /var/lib/odoo/filestore/mydb  (usually a volume)
tar -C /var/lib/odoo/filestore -czf mydb-filestore-$(date +%F).tgz mydb
docker compose exec -T odoo tar -C /var/lib/odoo/filestore -czf - mydb > mydb-filestore.tgz     # from the container
rsync -a --delete /var/lib/odoo/filestore/mydb/ backup@nas:/odoo/filestore/mydb/                # incremental

# restored under a NEW database name? The folder must carry the new name
tar -C /var/lib/odoo/filestore -xzf mydb-filestore.tgz && mv /var/lib/odoo/filestore/mydb /var/lib/odoo/filestore/mydb_restored
chown -R odoo:odoo /var/lib/odoo/filestore/mydb_restored"""),
        "zip": ("bash · the ZIP from the Odoo database manager, restored by hand", """# /web/database/manager → Backup (zip) = dump.sql + filestore/ + manifest.json
unzip -q mydb.zip -d mydb_zip && cat mydb_zip/manifest.json      # Odoo version, PostgreSQL version, modules
sudo -u postgres createdb -O odoo -E UTF8 -T template0 mydb
sudo -u postgres psql -d mydb -v ON_ERROR_STOP=1 -q -f mydb_zip/dump.sql
mkdir -p /var/lib/odoo/filestore && cp -a mydb_zip/filestore /var/lib/odoo/filestore/mydb && chown -R odoo:odoo /var/lib/odoo/filestore/mydb"""),
        "cron": ("bash · /usr/local/bin/odoo-backup.sh – nightly backup with check and rotation", """#!/bin/bash
set -euo pipefail
DB=mydb; DIR=/var/backups/odoo; KEEP=14; D=$(date +%F_%H%M)
FS=/var/lib/odoo/filestore/$DB                      # adapt (see above)
mkdir -p "$DIR"
# choose ONE line: native (systemd) / Docker
sudo -u postgres pg_dump -Fc -d "$DB" > "$DIR/$DB-$D.dump"
# docker compose -f /opt/odoo/docker-compose.yml exec -T db pg_dump -U odoo -Fc "$DB" > "$DIR/$DB-$D.dump"
pg_restore -l "$DIR/$DB-$D.dump" > /dev/null        # quick sanity check: header and table of contents readable
tar -C "$(dirname "$FS")" -czf "$DIR/$DB-$D-filestore.tgz" "$(basename "$FS")"
find "$DIR" -name "$DB-*" -mtime +$KEEP -delete     # rotation
echo "$(date -Is) OK $(du -sh "$DIR/$DB-$D.dump" | cut -f1)" >> "$DIR/backup.log"

# crontab -e (root):  30 2 * * *  /usr/local/bin/odoo-backup.sh || echo "backup FAILED" | mail -s backup admin@example.com"""),
        "errors": ("text · typical errors and what they mean", """pg_dump: error: connection to server on socket "/var/run/postgresql/.s.PGSQL.5432" failed:
  FATAL:  Peer authentication failed for user "odoo"          → local socket checks the Linux user: sudo -u postgres … or -h 127.0.0.1
  FATAL:  role "root" does not exist                          → started as root without -U: add -U odoo or use sudo -u postgres
pg_dump: error: aborting because of server version mismatch    → pg_dump older than the server: use the server's version (container/--cluster)
pg_restore: error: unsupported version (1.16) in file header   → dump made by a newer pg_dump: restore with the same or newer pg_restore
pg_restore: error: input file appears to be a text format dump. Please use psql.   → plain SQL dump (-Fp / ZIP): restore with psql
pg_dump: error: could not open output file "…": Permission denied → -f writes as postgres: use '>' or a folder postgres may write to
pg_restore: error: parallel restore from standard input is not supported → give a file, not '<'
ERROR:  role "odoo_prod" does not exist                         → restore with --no-owner --no-privileges (or --role=odoo)"""),
    },
    "links": [
        ("PostgreSQL: pg_dump", "https://www.postgresql.org/docs/current/app-pgdump.html"),
        ("PostgreSQL: pg_restore", "https://www.postgresql.org/docs/current/app-pgrestore.html"),
        ("PostgreSQL: the password file (.pgpass)", "https://www.postgresql.org/docs/current/libpq-pgpass.html"),
        ("Docker Hub: official postgres image", "https://hub.docker.com/_/postgres"),
        ("Blog: the backup exists – but will not restore", "@blog:postgresql-restore-fails-foreign-key-duplicate-index-odoo"),
        ("Blog: restoring a backup on stage without cron jobs", "@blog:odoo-stage-restore-stop-cron-jobs"),
        ("Blog: PostgreSQL cheat sheet for Odoo admins", "@blog:postgresql-odoo-admin-cheat-sheet"),
        ("Blog: free hosting, database and filestore (backups to R2)", "@blog:odoo-17-free-hosting-database-filestore"),
    ],
    "t": {},
}

PGDUMP["t"]["en"] = {
    "title": "pg_dump and pg_restore for Odoo: every variant – Docker, systemd, remote server, filestore",
    "summary": "How to back up and restore an Odoo database whether PostgreSQL runs in Docker, as a system service or on another server: formats, parallel jobs, single tables, the filestore, the ZIP from the database manager, a nightly script with rotation and the typical error messages.",
    "body": [
        ("p", "“Make a backup” sounds like one command. In practice the command depends on **where PostgreSQL runs**: in a Docker container, as a normal system service (systemd) or on a separate or cloud database server. Each variant has its own pitfalls – a missing `-T`, the wrong client version, peer authentication, a folder the postgres user may not write to. Here are all variants side by side, with commands you can copy."),
        ("note", "Short version: `pg_dump -Fc` (custom format) is the right default. Back up the **filestore** as well – without it Odoo has no attachments. Restore into a **new** database and swap names, check the restore log for `ERROR`, and test a restore regularly."),
        ("h", "Step 0: find out how PostgreSQL runs", "where"),
        ("code", "where"),
        ("p", "Important: `db_host` in odoo.conf tells you where **Odoo** connects. `localhost` inside a container means the container itself, `db` is usually the compose service name, an IP address means another server."),
        ("h", "PostgreSQL as a system service (systemd, no Docker)", "systemd"),
        ("code", "native"),
        ("ul", [
            "**Local socket = peer authentication:** PostgreSQL checks the Linux user name. That is why `sudo -u postgres` works without a password and `pg_dump -U odoo` as root does not.",
            "**`>` instead of `-f`** with `sudo -u postgres`: the redirection is opened by your shell (root), so any target folder works.",
            "**Several clusters** on one machine (an old 14 and a new 16): `pg_lsclusters` shows them, `--cluster 16/main` chooses the right one including the right binaries.",
        ]),
        ("h", "PostgreSQL in Docker", "docker"),
        ("code", "docker"),
        ("ul", [
            "**`-T` with `docker compose exec`** (or `-i` without `-t` with `docker exec`) – otherwise the dump is silently corrupted and only fails on restore.",
            "The official **Odoo image contains a PostgreSQL client** too – but often an older one than the server. If `pg_dump` complains about a version mismatch, run it in the database container or in a throw-away `postgres:NN` container of the server's version.",
            "Do not dump the **volume files** (`/var/lib/postgresql/data`) of a running database – that is not a consistent backup.",
        ]),
        ("h", "Database on another server or managed (RDS, DigitalOcean, Hetzner …)", "remote"),
        ("code", "remote"),
        ("p", "The version rule applies here too: the `pg_dump` client must be **at least** the server version. On an old workstation the client is often older – a `postgres:NN` container solves that without installing anything."),
        ("h", "Formats: which one when", "formats"),
        ("code", "formats"),
        ("table", [
            ["Format", "Restore with", "Single tables", "Parallel", "For"],
            ["plain `-Fp` (.sql)", "`psql`", "no", "no", "small databases, reading/editing, migration to other tools"],
            ["custom `-Fc`", "`pg_restore`", "yes", "restore only", "**default** – nightly backups, copies to stage"],
            ["directory `-Fd`", "`pg_restore`", "yes", "dump and restore", "large databases (tens/hundreds of GB)"],
            ["tar `-Ft`", "`pg_restore`", "yes", "no", "rarely"],
        ]),
        ("p", "pg_dump does not stop Odoo: it reads a consistent snapshot while users keep working. It does block **schema changes** – a module update (`-u`) waits until the dump is done. On large databases a long dump also delays vacuum, so run it at night."),
        ("h", "Restore", "restore"),
        ("code", "restore"),
        ("ul", [
            "`-T template0 -E UTF8`: a clean database with the right encoding; the default template may contain extras.",
            "`--no-owner --role=odoo`: the objects belong to the Odoo user even if the source server used a different role name.",
            "`-j 4` (number of CPU cores): speeds up restoring indexes considerably – only with a file, not with stdin.",
            "A restored copy of production sends e-mails and runs cron jobs – before starting Odoo on it, neutralise it (see the article on stage restores).",
        ]),
        ("h", "Single tables, table of contents, exclusions", "tables"),
        ("code", "tables"),
        ("p", "Restoring one table **directly into production** almost never works cleanly in Odoo: foreign keys, sequences and dependent tables do not match. Safer: restore into a scratch database, compare, then copy exactly the rows you need with SQL."),
        ("h", "Odoo: the filestore belongs to the backup", "filestore"),
        ("code", "filestore"),
        ("p", "A database without its filestore opens, but every attachment, product image and stored PDF is missing (“file not found” in the log). Database and filestore should come from the same point in time – dump first, then the filestore, both in the same script."),
        ("h", "The ZIP from the database manager, restored by hand", "zip"),
        ("p", "The ZIP from `/web/database/manager` contains a plain SQL dump and the filestore. With large databases the upload through the browser fails (time and size limits) – unpacked by hand it always works:"),
        ("code", "zip"),
        ("h", "Nightly backup with check and rotation", "cron"),
        ("code", "cron"),
        ("ul", [
            "`set -euo pipefail`: if pg_dump fails, the script stops and the `|| mail` in crontab reports it.",
            "`pg_restore -l` is a quick check that the file is a readable dump – not that the data restores cleanly. For that: a regular **test restore** on stage.",
            "Keep copies **off the server** as well (rsync, R2/S3) – a backup on the same disk does not survive a disk failure or a deleted VPS.",
        ]),
        ("h", "Typical errors", "errors"),
        ("code", "errors"),
        ("links", "Links"),
    ],
}

PGDUMP["t"]["de"] = {
    "title": "pg_dump und pg_restore für Odoo: alle Varianten – Docker, systemd, entfernter Server, Filestore",
    "summary": "Wie man eine Odoo-Datenbank sichert und wiederherstellt – egal ob PostgreSQL in Docker, als Systemdienst oder auf einem anderen Server läuft: Formate, parallele Jobs, einzelne Tabellen, Filestore, das ZIP aus dem Datenbankmanager, ein nächtliches Skript mit Rotation und die typischen Fehlermeldungen.",
    "body": [
        ("p", "„Mach mal ein Backup“ klingt nach einem Befehl. In der Praxis hängt der Befehl davon ab, **wo PostgreSQL läuft**: in einem Docker-Container, als normaler Systemdienst (systemd) oder auf einem separaten bzw. Cloud-Datenbankserver. Jede Variante hat ihre Fallen – ein fehlendes `-T`, die falsche Client-Version, Peer-Authentifizierung, ein Ordner, in den der Benutzer postgres nicht schreiben darf. Hier alle Varianten nebeneinander, mit Befehlen zum Kopieren."),
        ("note", "Kurzfassung: `pg_dump -Fc` (Custom-Format) ist der richtige Standard. Den **Filestore** mitsichern – ohne ihn fehlen in Odoo alle Anhänge. In eine **neue** Datenbank einspielen und die Namen tauschen, das Restore-Log auf `ERROR` prüfen und das Einspielen regelmäßig testen."),
        ("h", "Schritt 0: herausfinden, wie PostgreSQL läuft", "where"),
        ("code", "where"),
        ("p", "Wichtig: `db_host` in der odoo.conf sagt, wohin sich **Odoo** verbindet. `localhost` in einem Container ist der Container selbst, `db` meist der Name des Compose-Dienstes, eine IP-Adresse ein anderer Server."),
        ("h", "PostgreSQL als Systemdienst (systemd, ohne Docker)", "systemd"),
        ("code", "native"),
        ("ul", [
            "**Lokaler Socket = Peer-Authentifizierung:** PostgreSQL prüft den Linux-Benutzernamen. Deshalb funktioniert `sudo -u postgres` ohne Passwort, `pg_dump -U odoo` als root aber nicht.",
            "**`>` statt `-f`** bei `sudo -u postgres`: die Umleitung öffnet Ihre Shell (root), also geht jeder Zielordner.",
            "**Mehrere Cluster** auf einer Maschine (altes 14 und neues 16): `pg_lsclusters` zeigt sie, `--cluster 16/main` wählt den richtigen samt passenden Programmen.",
        ]),
        ("h", "PostgreSQL in Docker", "docker"),
        ("code", "docker"),
        ("ul", [
            "**`-T` bei `docker compose exec`** (bzw. `-i` ohne `-t` bei `docker exec`) – sonst wird der Dump unbemerkt beschädigt und scheitert erst beim Einspielen.",
            "Das offizielle **Odoo-Image enthält ebenfalls einen PostgreSQL-Client** – oft aber einen älteren als der Server. Meldet `pg_dump` einen Versionskonflikt, im Datenbank-Container oder in einem Wegwerf-Container `postgres:NN` mit der Server-Version ausführen.",
            "Die **Volume-Dateien** (`/var/lib/postgresql/data`) einer laufenden Datenbank nicht einfach kopieren – das ist kein konsistentes Backup.",
        ]),
        ("h", "Datenbank auf einem anderen Server oder als Managed Service (RDS, DigitalOcean, Hetzner …)", "remote"),
        ("code", "remote"),
        ("p", "Auch hier gilt die Versionsregel: der `pg_dump`-Client muss **mindestens** die Server-Version haben. Auf einem alten Arbeitsrechner ist der Client oft älter – ein `postgres:NN`-Container löst das ohne Installation."),
        ("h", "Formate: welches wann", "formats"),
        ("code", "formats"),
        ("table", [
            ["Format", "Einspielen mit", "Einzelne Tabellen", "Parallel", "Wofür"],
            ["plain `-Fp` (.sql)", "`psql`", "nein", "nein", "kleine Datenbanken, lesen/bearbeiten, Migration in andere Tools"],
            ["custom `-Fc`", "`pg_restore`", "ja", "nur Einspielen", "**Standard** – nächtliche Backups, Kopien für Stage"],
            ["directory `-Fd`", "`pg_restore`", "ja", "Dump und Einspielen", "große Datenbanken (Dutzende/Hunderte GB)"],
            ["tar `-Ft`", "`pg_restore`", "ja", "nein", "selten"],
        ]),
        ("p", "pg_dump hält Odoo nicht an: es liest einen konsistenten Schnappschuss, während die Benutzer weiterarbeiten. Es blockiert aber **Schemaänderungen** – ein Modul-Update (`-u`) wartet, bis der Dump fertig ist. Bei großen Datenbanken verzögert ein langer Dump auch das Vacuum – also nachts laufen lassen."),
        ("h", "Einspielen", "restore"),
        ("code", "restore"),
        ("ul", [
            "`-T template0 -E UTF8`: eine saubere Datenbank mit der richtigen Kodierung; das Standard-Template kann Extras enthalten.",
            "`--no-owner --role=odoo`: die Objekte gehören dem Odoo-Benutzer, auch wenn der Quellserver einen anderen Rollennamen hatte.",
            "`-j 4` (Anzahl CPU-Kerne): beschleunigt vor allem den Aufbau der Indizes – nur mit Datei, nicht über stdin.",
            "Eine eingespielte Produktionskopie verschickt E-Mails und führt Cron-Jobs aus – vor dem Start von Odoo neutralisieren (siehe Artikel zum Einspielen auf Stage).",
        ]),
        ("h", "Einzelne Tabellen, Inhaltsverzeichnis, Ausschlüsse", "tables"),
        ("code", "tables"),
        ("p", "Eine einzelne Tabelle **direkt in die Produktion** einzuspielen klappt in Odoo fast nie sauber: Fremdschlüssel, Sequenzen und abhängige Tabellen passen nicht. Sicherer: in eine Hilfsdatenbank einspielen, vergleichen und dann genau die benötigten Zeilen per SQL übernehmen."),
        ("h", "Odoo: der Filestore gehört zum Backup", "filestore"),
        ("code", "filestore"),
        ("p", "Eine Datenbank ohne ihren Filestore öffnet sich, aber alle Anhänge, Produktbilder und gespeicherten PDFs fehlen („file not found“ im Log). Datenbank und Filestore sollten vom selben Zeitpunkt stammen – erst der Dump, dann der Filestore, beides im selben Skript."),
        ("h", "Das ZIP aus dem Datenbankmanager von Hand einspielen", "zip"),
        ("p", "Das ZIP aus `/web/database/manager` enthält einen Plain-SQL-Dump und den Filestore. Bei großen Datenbanken scheitert das Hochladen im Browser (Zeit- und Größenlimits) – von Hand entpackt klappt es immer:"),
        ("code", "zip"),
        ("h", "Nächtliches Backup mit Prüfung und Rotation", "cron"),
        ("code", "cron"),
        ("ul", [
            "`set -euo pipefail`: scheitert pg_dump, bricht das Skript ab, und das `|| mail` in der crontab meldet es.",
            "`pg_restore -l` prüft schnell, dass die Datei ein lesbarer Dump ist – nicht, dass sich die Daten sauber einspielen lassen. Dafür: regelmäßiges **Test-Einspielen** auf Stage.",
            "Kopien auch **außerhalb des Servers** aufbewahren (rsync, R2/S3) – ein Backup auf derselben Platte überlebt keinen Plattenausfall und keinen gelöschten VPS.",
        ]),
        ("h", "Typische Fehler", "errors"),
        ("code", "errors"),
        ("links", "Links"),
    ],
}

PGDUMP["t"]["ru"] = {
    "title": "pg_dump и pg_restore для Odoo: все варианты – Docker, systemd, удалённый сервер, filestore",
    "summary": "Как сделать бэкап и восстановить базу Odoo, если PostgreSQL работает в Docker, как системная служба или на другом сервере: форматы, параллельная работа, отдельные таблицы, filestore, ZIP из менеджера баз, ночной скрипт с ротацией и типичные ошибки.",
    "body": [
        ("p", "«Сделай бэкап» звучит как одна команда. На практике команда зависит от того, **где работает PostgreSQL**: в Docker-контейнере, как обычная системная служба (systemd) или на отдельном либо облачном сервере баз данных. У каждого варианта свои ловушки: забытый `-T`, не та версия клиента, peer-аутентификация, папка, в которую пользователь postgres не может писать. Здесь все варианты рядом, с командами, которые можно копировать."),
        ("note", "Коротко: `pg_dump -Fc` (custom-формат) – правильный вариант по умолчанию. Обязательно сохраняйте и **filestore**: без него в Odoo пропадут все вложения. Восстанавливайте в **новую** базу и меняйте имена местами, проверяйте лог восстановления на `ERROR` и регулярно делайте тестовое восстановление."),
        ("h", "Шаг 0: выяснить, как запущен PostgreSQL", "where"),
        ("code", "where"),
        ("p", "Важно: `db_host` в odoo.conf говорит, куда подключается **Odoo**. `localhost` внутри контейнера – это сам контейнер, `db` – обычно имя сервиса в compose, IP-адрес – другой сервер."),
        ("h", "PostgreSQL как системная служба (systemd, без Docker)", "systemd"),
        ("code", "native"),
        ("ul", [
            "**Локальный сокет = peer-аутентификация:** PostgreSQL проверяет имя пользователя Linux. Поэтому `sudo -u postgres` работает без пароля, а `pg_dump -U odoo` от root – нет.",
            "**`>` вместо `-f`** при `sudo -u postgres`: перенаправление открывает ваша оболочка (root), поэтому подходит любая папка.",
            "**Несколько кластеров** на одной машине (старый 14 и новый 16): `pg_lsclusters` покажет их, а `--cluster 16/main` выберет нужный вместе с подходящими программами.",
        ]),
        ("h", "PostgreSQL в Docker", "docker"),
        ("code", "docker"),
        ("ul", [
            "**`-T` в `docker compose exec`** (или `-i` без `-t` в `docker exec`) обязателен – иначе дамп незаметно портится, и это выясняется только при восстановлении.",
            "В официальном **образе Odoo тоже есть клиент PostgreSQL** – но часто старее сервера. Если `pg_dump` жалуется на несовпадение версий, запускайте его в контейнере базы или во временном контейнере `postgres:NN` с версией сервера.",
            "Не копируйте **файлы тома** (`/var/lib/postgresql/data`) работающей базы – это не согласованный бэкап.",
        ]),
        ("h", "База на другом сервере или управляемая (RDS, DigitalOcean, Hetzner …)", "remote"),
        ("code", "remote"),
        ("p", "Правило версий действует и здесь: клиент `pg_dump` должен быть **не старее** версии сервера. На старом рабочем компьютере клиент часто старее – контейнер `postgres:NN` решает это без установки."),
        ("h", "Форматы: какой когда", "formats"),
        ("code", "formats"),
        ("table", [
            ["Формат", "Восстанавливать", "Отдельные таблицы", "Параллельно", "Для чего"],
            ["plain `-Fp` (.sql)", "`psql`", "нет", "нет", "маленькие базы, прочитать/поправить, перенос в другие системы"],
            ["custom `-Fc`", "`pg_restore`", "да", "только восстановление", "**по умолчанию** – ночные бэкапы, копии на stage"],
            ["directory `-Fd`", "`pg_restore`", "да", "и дамп, и восстановление", "большие базы (десятки/сотни ГБ)"],
            ["tar `-Ft`", "`pg_restore`", "да", "нет", "редко"],
        ]),
        ("p", "pg_dump не останавливает Odoo: он читает согласованный снимок, пока пользователи продолжают работать. Но он блокирует **изменения схемы** – обновление модуля (`-u`) будет ждать конца дампа. На больших базах долгий дамп ещё и задерживает vacuum, поэтому запускайте его ночью."),
        ("h", "Восстановление", "restore"),
        ("code", "restore"),
        ("ul", [
            "`-T template0 -E UTF8`: чистая база с правильной кодировкой; шаблон по умолчанию может содержать лишнее.",
            "`--no-owner --role=odoo`: объекты принадлежат пользователю Odoo, даже если на исходном сервере роль называлась иначе.",
            "`-j 4` (число ядер): заметно ускоряет построение индексов – только из файла, не через stdin.",
            "Восстановленная копия продакшена рассылает письма и запускает кроны – перед стартом Odoo её нужно обезвредить (см. статью про восстановление на stage).",
        ]),
        ("h", "Отдельные таблицы, оглавление, исключения", "tables"),
        ("code", "tables"),
        ("p", "Восстановить одну таблицу **прямо в рабочую базу** в Odoo почти никогда не получается чисто: не сходятся внешние ключи, последовательности и зависимые таблицы. Надёжнее: восстановить во вспомогательную базу, сравнить и перенести SQL-запросом ровно те строки, которые нужны."),
        ("h", "Odoo: filestore – часть бэкапа", "filestore"),
        ("code", "filestore"),
        ("p", "База без своего filestore открывается, но все вложения, картинки товаров и сохранённые PDF пропадают («file not found» в логе). База и filestore должны быть сняты в одно время – сначала дамп, потом filestore, в одном скрипте."),
        ("h", "ZIP из менеджера баз Odoo – восстановление вручную", "zip"),
        ("p", "ZIP из `/web/database/manager` содержит дамп в виде SQL и filestore. С большими базами загрузка через браузер падает (лимиты времени и размера) – распакованный вручную он восстанавливается всегда:"),
        ("code", "zip"),
        ("h", "Ночной бэкап с проверкой и ротацией", "cron"),
        ("code", "cron"),
        ("ul", [
            "`set -euo pipefail`: если pg_dump упал, скрипт останавливается, и `|| mail` в crontab об этом сообщит.",
            "`pg_restore -l` быстро проверяет, что файл – читаемый дамп, но не то, что данные чисто восстановятся. Для этого – регулярное **тестовое восстановление** на stage.",
            "Храните копии и **вне сервера** (rsync, R2/S3): бэкап на том же диске не переживёт отказ диска или удалённый VPS.",
        ]),
        ("h", "Типичные ошибки", "errors"),
        ("code", "errors"),
        ("links", "Ссылки"),
    ],
}

PGDUMP["t"]["uk"] = {
    "title": "pg_dump і pg_restore для Odoo: усі варіанти – Docker, systemd, віддалений сервер, filestore",
    "summary": "Як зробити бекап і відновити базу Odoo, якщо PostgreSQL працює в Docker, як системна служба або на іншому сервері: формати, паралельна робота, окремі таблиці, filestore, ZIP із менеджера баз, нічний скрипт з ротацією й типові помилки.",
    "body": [
        ("p", "«Зроби бекап» звучить як одна команда. На практиці команда залежить від того, **де працює PostgreSQL**: у Docker-контейнері, як звичайна системна служба (systemd) чи на окремому або хмарному сервері баз даних. У кожного варіанта свої пастки: забутий `-T`, не та версія клієнта, peer-автентифікація, тека, у яку користувач postgres не може писати. Тут усі варіанти поруч, з командами, які можна копіювати."),
        ("note", "Коротко: `pg_dump -Fc` (custom-формат) – правильний варіант за замовчуванням. Обов'язково зберігайте й **filestore**: без нього в Odoo зникнуть усі вкладення. Відновлюйте в **нову** базу й міняйте імена місцями, перевіряйте лог відновлення на `ERROR` і регулярно робіть тестове відновлення."),
        ("h", "Крок 0: з'ясувати, як запущено PostgreSQL", "where"),
        ("code", "where"),
        ("p", "Важливо: `db_host` в odoo.conf показує, куди підключається **Odoo**. `localhost` усередині контейнера – це сам контейнер, `db` – зазвичай ім'я сервісу в compose, IP-адреса – інший сервер."),
        ("h", "PostgreSQL як системна служба (systemd, без Docker)", "systemd"),
        ("code", "native"),
        ("ul", [
            "**Локальний сокет = peer-автентифікація:** PostgreSQL перевіряє ім'я користувача Linux. Тому `sudo -u postgres` працює без пароля, а `pg_dump -U odoo` від root – ні.",
            "**`>` замість `-f`** при `sudo -u postgres`: перенаправлення відкриває ваша оболонка (root), тож підходить будь-яка тека.",
            "**Кілька кластерів** на одній машині (старий 14 і новий 16): `pg_lsclusters` покаже їх, а `--cluster 16/main` вибере потрібний разом із відповідними програмами.",
        ]),
        ("h", "PostgreSQL у Docker", "docker"),
        ("code", "docker"),
        ("ul", [
            "**`-T` у `docker compose exec`** (або `-i` без `-t` у `docker exec`) обов'язковий – інакше дамп непомітно псується, і це з'ясовується лише під час відновлення.",
            "В офіційному **образі Odoo теж є клієнт PostgreSQL** – але часто старіший за сервер. Якщо `pg_dump` скаржиться на розбіжність версій, запускайте його в контейнері бази або в тимчасовому контейнері `postgres:NN` з версією сервера.",
            "Не копіюйте **файли тому** (`/var/lib/postgresql/data`) працюючої бази – це не узгоджений бекап.",
        ]),
        ("h", "База на іншому сервері або керована (RDS, DigitalOcean, Hetzner …)", "remote"),
        ("code", "remote"),
        ("p", "Правило версій діє й тут: клієнт `pg_dump` має бути **не старішим** за версію сервера. На старому робочому комп'ютері клієнт часто старіший – контейнер `postgres:NN` розв'язує це без встановлення."),
        ("h", "Формати: який коли", "formats"),
        ("code", "formats"),
        ("table", [
            ["Формат", "Відновлювати", "Окремі таблиці", "Паралельно", "Для чого"],
            ["plain `-Fp` (.sql)", "`psql`", "ні", "ні", "малі бази, прочитати/виправити, перенесення в інші системи"],
            ["custom `-Fc`", "`pg_restore`", "так", "лише відновлення", "**за замовчуванням** – нічні бекапи, копії на stage"],
            ["directory `-Fd`", "`pg_restore`", "так", "і дамп, і відновлення", "великі бази (десятки/сотні ГБ)"],
            ["tar `-Ft`", "`pg_restore`", "так", "ні", "рідко"],
        ]),
        ("p", "pg_dump не зупиняє Odoo: він читає узгоджений знімок, поки користувачі працюють далі. Але він блокує **зміни схеми** – оновлення модуля (`-u`) чекатиме кінця дампу. На великих базах довгий дамп ще й затримує vacuum, тому запускайте його вночі."),
        ("h", "Відновлення", "restore"),
        ("code", "restore"),
        ("ul", [
            "`-T template0 -E UTF8`: чиста база з правильним кодуванням; шаблон за замовчуванням може містити зайве.",
            "`--no-owner --role=odoo`: об'єкти належать користувачу Odoo, навіть якщо на вихідному сервері роль називалася інакше.",
            "`-j 4` (кількість ядер): помітно пришвидшує побудову індексів – лише з файлу, не через stdin.",
            "Відновлена копія продакшену розсилає листи й запускає крони – перед стартом Odoo її треба знешкодити (див. статтю про відновлення на stage).",
        ]),
        ("h", "Окремі таблиці, зміст, винятки", "tables"),
        ("code", "tables"),
        ("p", "Відновити одну таблицю **просто в робочу базу** в Odoo майже ніколи не вдається чисто: не сходяться зовнішні ключі, послідовності й залежні таблиці. Надійніше: відновити в допоміжну базу, порівняти й перенести SQL-запитом саме ті рядки, які потрібні."),
        ("h", "Odoo: filestore – частина бекапу", "filestore"),
        ("code", "filestore"),
        ("p", "База без свого filestore відкривається, але всі вкладення, зображення товарів і збережені PDF зникають («file not found» у лозі). Базу й filestore треба знімати в один час – спершу дамп, потім filestore, в одному скрипті."),
        ("h", "ZIP із менеджера баз Odoo – відновлення вручну", "zip"),
        ("p", "ZIP із `/web/database/manager` містить дамп у вигляді SQL і filestore. З великими базами завантаження через браузер падає (ліміти часу й розміру) – розпакований вручну він відновлюється завжди:"),
        ("code", "zip"),
        ("h", "Нічний бекап з перевіркою й ротацією", "cron"),
        ("code", "cron"),
        ("ul", [
            "`set -euo pipefail`: якщо pg_dump упав, скрипт зупиняється, і `|| mail` у crontab про це повідомить.",
            "`pg_restore -l` швидко перевіряє, що файл – читабельний дамп, але не те, що дані чисто відновляться. Для цього – регулярне **тестове відновлення** на stage.",
            "Зберігайте копії й **поза сервером** (rsync, R2/S3): бекап на тому самому диску не переживе відмову диска чи видалений VPS.",
        ]),
        ("h", "Типові помилки", "errors"),
        ("code", "errors"),
        ("links", "Посилання"),
    ],
}
