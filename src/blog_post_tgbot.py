# Статья 25: наш Telegram-бот для Odoo – команды, примеры отчётов (обезличены), отдельный хост БД и реплика,
# /2stage (свежая база stage с мастера), деплой, установка, безопасность, GitHub Actions. Все 6 языков.
# Примеры вывода – реальные (/health, /jobs, /users), переведены с русского интерфейса бота, хосты и имена заменены.

REPO = "https://github.com/dpodyachev/odoo-ops-bot"

TGBOT = {
    "slug": "telegram-bot-odoo-monitoring-deploy-stage-copy",
    "date": "2026-11-17",
    "tags": ["Odoo", "Telegram", "Monitoring", "PostgreSQL", "DevOps", "Security"],
    "code": {
        "health": ("/health · Odoo 14 on systemd (translated from the bot's Russian interface, host anonymized)", """== ✅ PROD: all good

✅ Disk /: 51% – 77.2 GB of 149.9 GB used, 66.6 GB free
✅ RAM: 32% – 10.4 GB of 15.3 GB available
✅ Load average 1/5/15 min: 0.48 / 0.23 / 0.13 on 4 CPU (12% / 6% / 3% of the cores)
   CPU now: busy 11%, iowait 0%
✅ odoo_main: active, since Mon 2026-11-09 15:12:02 EET, restarts: 0
✅ postgresql: active
✅ nginx: active, since 2026-07-06 00:50:20, config: ok, ports 80:up 443:up
✅ nginx, last 5000 requests (since 17/Nov/2026:00:05:41): 5xx – 0, of them 502/504 – 0
✅ nginx error.log, last hour: errors 0, of them upstream (Odoo) – 0
✅ port 8069: up
✅ port 8072: up
✅ HTTP erp.example.com/web/login: 200 in 0.30 s
ℹ️ Log: /opt/odoo/odoo-server.log (0 MB), last entry 1 s ago
ℹ️ Errors in the last 10000 lines: 0 (+ scanner noise: 4)"""),
        "jobs": ("/jobs · cron and queue_job (excerpt, two installations)", """== ⚙️ PROD: jobs (database erp)

▶️ Running now:
nothing

🧩 queue_job – failed: 173, done: 5838
failed in 24 h: 1

Last failed jobs:
16.11 22:35  Sync dates: MO/01796
      odoo.exceptions.UserError: Some work orders have already started, you cannot unplan this manufacturing order.
15.11 22:35  Sync dates: MO/01796
      odoo.exceptions.UserError: Some work orders have already started, you cannot unplan this manufacturing order.

== ⏰ Cron: active 31

last run     next run     interval     job
 17.11 08:43  17.11 08:48  5 minutes    Jobs Garbage Collector
 17.11 08:40  17.11 08:45  5 minutes    Mail: Fetchmail Service
 17.11 08:23  17.11 09:22  1 hours      Mail: Email Queue Manager
 17.11 06:00  18.11 06:00  1 days       Backup scheduler morning

== ⚙️ PROD (second installation): jobs (database erp)

🧩 queue_job – pending: 25, failed: 1609, done: 187569, cancelled: 3
failed in 24 h: 0

In the queue (first 10):
16.11 22:30  pending  sync.task.run
16.11 22:30  pending  Queue job method for sending Telegram notifications
Last done:
16.11 20:24    25.8s  Queue job method for sending Telegram notifications"""),
        "users": ("/users · who works in Odoo (names replaced)", """== 👥 PROD: users in the last 24 h (database erp)

Were in Odoo (web client open): 10
Online now: 6
Changed documents: 4
Logins with password: 1 (users: 1) – sessions are long, so there are few logins
Active internal users: 27, portal: 0

Last activity (Europe/Kyiv):
🟢 17.11 08:44  User A
🟢 17.11 08:33  User B
⚪ 17.11 08:06  User C
⚪ 16.11 17:41  User D

Changes in documents (records, where):
    53  User D  account.move,mrp.production,mrp.workorder,stock.move
    27  User B  account.move,mrp.workorder,purchase.order,sale.order"""),
        "replica": ("/health · Odoo 16 in Docker, PostgreSQL on a separate host with a streaming replica (excerpt, anonymized)", """✅ Disk /: 37% – 283.6 GB of 773.9 GB used, 490.3 GB free
✅ RAM: 72% – 17.7 GB of 62.8 GB available
✅ Load average 1/5/15 min: 0.28 / 0.30 / 0.30 on 32 CPU (1% / 1% / 1% of the cores)
✅ odoo-1: active, since 2026-11-13 17:13:56 UTC, restarts: 0
✅ postgresql (db-01): active, connections 107 of 450, disk 52% (556.9 GB free)
   replication: 10.0.0.12/32 streaming, lag 00:00:00
✅ HTTP crm.example.com/web/login: 200 in 0.19 s
ℹ️ Log: docker logs odoo-1 (10 MB), last entry 298 s ago

# targets.json: where the bot goes for what
"db_ssh":    "admin@db-01",     # PostgreSQL status, /jobs (needs the primary: FOR UPDATE SKIP LOCKED)
"db_ssh_ro": "admin@db-02",     # /users – heavy reads go to the replica"""),
        "clone": ("/2stage · steps on the database host and the neutralization SQL", """# runs on the stage DB host as a transient systemd unit (survives a dropped SSH session and a bot restart)
check       replication connection to the master (conninfo from the old replica config, password -> pgpass 600)
stop        stop Odoo stage and PostgreSQL stage
clean       delete the old data directory
basebackup  pg_basebackup -X stream -c fast -P   (no -R: the copy becomes a standalone database)
fix         remove standby.signal, empty postgresql.auto.conf
start       start PostgreSQL with the normal stage configs, wait until WAL is replayed
neutralize  the SQL below
done        start Odoo stage, check HTTP, run /health

-- neutralization: nothing on stage may send mail or run by itself
UPDATE ir_config_parameter SET value = :'stage_url' WHERE key = 'web.base.url';
UPDATE ir_cron SET active = false WHERE active;
UPDATE ir_mail_server SET active = false, smtp_pass = NULL;
UPDATE fetchmail_server SET active = false, password = NULL;
UPDATE queue_job SET state = 'cancelled'
 WHERE state IN ('wait_dependencies', 'pending', 'enqueued', 'started');

# the final message (template)
✅ Fresh copy in <N> min, database <db>: <size>. Neutralized: web.base.url=https://stage.example.com,
   cron_active=0, mail_servers_active=0. Odoo stage started, site answers 200."""),
        "install": ("bash · installation (one folder and one bot per client)", f"""git clone {REPO}.git odoo-bot-client1 && cd odoo-bot-client1
cp .env.example .env && chmod 600 .env       # bot token, allowed chats, language
cp targets.example.json targets.json          # servers: ssh, url, paths, service, database, ports
python3 bot.py --cli health prod              # check without Telegram
./run.sh start                                # background + auto-restart; ./run.sh status | stop | restart
# or Docker: deploy/docker-compose.yml"""),
        "config": (".env and targets.json · the minimum", """# .env
MONITOR_BOT_TOKEN=            # from @BotFather, a separate bot per client
ALLOWED_CHAT_IDS=111111111,-222222222   # who may talk to the bot (groups are negative)
ADMIN_CHAT_IDS=111111111      # /pull /update /restore /backup /2stage – private chats only
DEFAULT_LANG=ru               # ru | uk
SSH_KEY=/root/.ssh/client1_ed25519

# targets.json
{ "tz": "Europe/Berlin",
  "servers": {
    "prod":  { "ssh": "odoo@erp.example.com", "url": "https://erp.example.com/web/login",
               "conf": "/etc/odoo/odoo.conf", "service": "odoo", "odoo_ports": "8069 8072" },
    "stage": { "ssh": "odoo@stage.example.com", "url": "https://stage.example.com/web/login",
               "update_cmd": "click-odoo-update" } } }"""),
        "ci": (".github/workflows/ci.yml · excerpt", """permissions:
  contents: read                 # the workflow token can only read the repository

jobs:
  lint:                          # py_compile, ruff (real errors only), ShellCheck, example configs
    ...
  secrets:
    steps:
      - uses: actions/checkout@v5
        with:
          fetch-depth: 0         # the whole history: a secret may sit in an old commit
          persist-credentials: false
      - uses: gitleaks/gitleaks-action@v2

on:
  push:
  pull_request:
  schedule:
    - cron: "17 5 * * 1"         # weekly re-scan with the newest gitleaks rules"""),
    },
    "links": [
        ("The bot on GitHub", REPO),
        ("Blog: Odoo after a year in production – perimeter, housekeeping, monitoring", "@blog:odoo-production-hardening-housekeeping-monitoring"),
        ("Blog: restoring Odoo on stage – stop cron and jobs", "@blog:odoo-stage-restore-stop-cron-jobs"),
        ("Blog: module update with click-odoo-update", "@blog:odoo-module-update-click-odoo-update"),
        ("Blog: Odoo 19 and a PostgreSQL read replica", "@blog:odoo-19-postgresql-read-replica"),
        ("Blog: could not serialize access – concurrent updates in Odoo", "@blog:odoo-could-not-serialize-access-concurrent-update"),
        ("Blog: Odoo server security – logs, secrets, ports, encryption", "@blog:odoo-server-security-logs-secrets-ports-encryption"),
        ("gitleaks", "https://github.com/gitleaks/gitleaks"),
    ],
    "t": {},
}


def _b(title, summary, intro, note, h, why, cmd_tbl, ex_p, ex_note, an_p, rep_p, rep_ul, clone_ul, clone_p,
       dep_ul, inst_ul, sec_ul, ci_tbl, ci_p, closing, links):
    return {"title": title, "summary": summary, "body": [
        ("p", intro), ("note", note),
        ("h", h[0]), ("ul", why),
        ("h", h[1]), ("table", cmd_tbl),
        ("h", h[2]), ("p", ex_p), ("code", "health"), ("code", "jobs"), ("code", "users"), ("p", ex_note),
        ("h", h[3]), ("p", an_p),
        ("h", h[4]), ("p", rep_p), ("code", "replica"), ("ul", rep_ul),
        ("h", h[5]), ("ul", clone_ul), ("code", "clone"), ("p", clone_p),
        ("h", h[6]), ("ul", dep_ul),
        ("h", h[7]), ("code", "install"), ("ul", inst_ul), ("code", "config"),
        ("h", h[8]), ("ul", sec_ul),
        ("h", h[9]), ("table", ci_tbl), ("code", "ci"), ("p", ci_p),
        ("h", h[10]), ("p", closing),
        ("links", links)]}


TGBOT["t"]["en"] = _b(
    "A Telegram bot for Odoo admins: monitoring, logs, cron, deployment and a fresh stage database",
    "The bot we use for the Odoo servers we maintain: /health, /log, /errors, /jobs, /users, an AI analysis, a prod → stage copy, git pull with module update and rollback, and /2stage – a fresh stage database from the PostgreSQL master. Real report examples, installation, security and what the GitHub Actions in the repository do.",
    "Most questions about an Odoo server are the same every week: is it up, what is in the log, did the crons run, is the job queue moving, who is working right now. We answer them with one Telegram command instead of an SSH session. The bot is one Python file without dependencies; it connects to the servers over SSH and runs fixed read-only scripts. It is open source.",
    f"Short version: one bot per client, the configuration in two files (`.env`, `targets.json`), nothing installed on the Odoo servers. Read commands for everyone in the allowed chats; `/pull`, `/update`, `/restore`, `/backup`, `/2stage` only for the admin in a private chat, always as a plan with a confirmation button. Code: `{REPO.split('//')[1]}`.",
    ["Why a bot", "Commands", "Report examples", "/analyze: a second opinion from Claude", "Database on a separate host and a streaming replica",
     "/2stage: a fresh stage database from the master", "Deployment: /pull, /update, /restore", "Installation", "Security", "GitHub: what the Actions do", "Conclusion"],
    ["**From the phone, in seconds.** `/health prod` answers in 2–5 seconds – useful when a user calls and you are not at the computer.",
     "**Always the same checks.** Disk, RAM, CPU, Odoo, PostgreSQL, nginx, ports, the login page, the log – nobody forgets a step, and the result is comparable from day to day.",
     "**Nothing on the servers.** No agent, no open port: the bot needs SSH and a user who can read logs.",
     "**One bot per client.** The code is shared, the bot token, chats and servers are separate. A mistake in a chat id must not send one client's logs to another client's chat."],
    [["Command", "What it does"],
     ["`/health`", "disk, RAM, load average and CPU/iowait (top processes under load), the Odoo service, PostgreSQL, nginx (`nginx -t`, ports 80/443, 5xx and 502/504 in the last 5000 requests, error.log for an hour), Odoo ports, HTTP check of `/web/login`, log size and errors"],
     ["`/log [N|all]`", "the last lines of the Odoo log: up to 100 as text without date and pid, more as a file, `all` – the whole current log as .gz"],
     ["`/errors`", "the last 10 ERROR/CRITICAL/FATAL; scanner noise and serialization retries are filtered out and only counted"],
     ["`/jobs`", "cron: last and next run, ▶ running now, ⚠ late; queue_job: running, queue, last done and failed with the error"],
     ["`/users [all]`", "who was in Odoo in the last 24 hours, who is online, who changed which documents"],
     ["`/analyze`", "all of the above plus tracebacks → Claude → verdict, causes, steps; compares with the previous analysis"],
     ["`/backup`", "copy prod → stage: a new database with the date in the name, filestore, neutralization, switch, module update, check – or start the server's own backup unit"],
     ["`/pull`", "`git pull` in every repository from `addons_path`: new commits and affected modules, then confirmation"],
     ["`/update`", "`click-odoo-update`: only modules whose code changed; Odoo keeps running, a restart button at the end"],
     ["`/restore`", "roll the code back to the state before one of the last `/pull`"],
     ["`/2stage`", "drop the stage database and copy a fresh one from the master with `pg_basebackup`, neutralize, start Odoo stage"]],
    "Real output of our bots, translated from the Russian interface; hosts, job references and user names are replaced.",
    "What we look at: errors without scanner noise (bots that send broken HTTP to port 8069 are counted separately, otherwise every report is red). In `/jobs` the same job failing every evening at 22:35 for a week is a business problem, not a server problem – the bot shows the error text, so it goes straight to the right person. In the second installation 25 jobs have been waiting since 22:30 while the last finished at 20:24 – the queue stands still, typically the job runner is not running or a channel is blocked. ▶ “running now” is not a guess: the bot tries `SELECT … FOR UPDATE SKIP LOCKED` on `ir_cron` – a row locked by a worker is a cron in progress. `/users` counts from `bus_presence`, `res_users_log` and `write_date` of the main documents; it shows who works and where, not what they typed.",
    "`/analyze` collects the health report, the errors with tracebacks and the cron/queue state, adds the previous analysis of the same server and sends it to Claude (`claude -p`) **without tools**: the model can only read the data it was given, not run commands. The answer is a verdict, causes, concrete steps and “what was fixed, what remains, what is new” since the last time. It takes about 30 seconds and is a good second opinion at 7 a.m. – not a replacement for an admin.",
    "On larger installations PostgreSQL runs on its own host, often with a streaming replica. The bot then has two SSH targets: the Odoo host (service or Docker container, nginx, log) and the database host (PostgreSQL status, connections, disk, replication).",
    ["**Replication in `/health`.** From `pg_stat_replication` on the master: replica address, state and `replay_lag`. A lag that grows or a missing `streaming` line is visible in the same report as the disk.",
     "**Heavy reads on the replica.** `/users` scans `mail_message` and the document tables – it goes to `db_ssh_ro` (the replica) and does not load the master.",
     "**`/jobs` on the master.** The “running now” check needs `FOR UPDATE SKIP LOCKED`, which is not possible on a hot standby.",
     "**Docker.** For Odoo in a container the bot reads `docker logs` and the container state instead of systemd and the log file."],
    ["**What it does.** Stop Odoo stage, delete the stage database cluster, copy a fresh one from the master with `pg_basebackup`, start it as an independent database, neutralize it, start Odoo stage. For a database of hundreds of gigabytes this takes hours – the bot posts progress in one message that it keeps editing.",
     "**Without `-R`.** The copy is not made a standby: no `standby.signal`, `postgresql.auto.conf` from the master is emptied, PostgreSQL starts with the normal stage configuration (`wal_level=minimal` is fine – WAL from the copy is replayed by crash recovery).",
     "**Neutralization before Odoo starts.** All crons off, all queue jobs cancelled, mail servers off and their passwords removed, `web.base.url` set to the stage address – the copy cannot send a single e-mail or call an integration.",
     "**On the database host, as a systemd unit.** The script runs via `systemd-run`: a dropped SSH session or a restart of the bot does not interrupt it; the bot only polls the status file."],
    "The password of the replication user never reaches the bot, the chat or the log: the script reads `primary_conninfo` from the configuration that already exists on the database host and writes a temporary `pgpass` (mode 600) that is deleted at exit. If something fails before the old data is deleted, the bot starts Odoo stage again – stage stays as it was.",
    ["**`/pull`** – `git pull` in every repository from `addons_path` of the Odoo configuration. First a plan: new commits per repository and the modules they touch; only after the button the pull runs. The commits “before” are saved for `/restore`.",
     "**`/update`** – `click-odoo-update` compares module checksums and updates only modules whose code changed. Odoo is not stopped; at the end a button restarts it. With several databases the bot asks which one.",
     "**`/restore`** – pick one of the last `/pull` and return the repositories to the commits before it (`git reset --keep` – local changes are not lost), then the `/update` plan.",
     "**Guard rails.** Only `ADMIN_CHAT_IDS` (private chats), a lock per server – two deployments cannot run at once, confirmation buttons expire after 30 minutes."],
    ["Create a bot with @BotFather – a separate one per client – and put the token into `.env`.",
     "Write to the bot: the refusal appears in `bot.log` as `denied chat_id=…` – that is the id for `ALLOWED_CHAT_IDS`.",
     "SSH: a dedicated key per client and a user without root who can read the Odoo and nginx logs; `sudo -n` only for what you enable (`systemctl status`, `nginx -t`; deployment and `/2stage` need more).",
     "For `/analyze` – Claude Code on the bot host (`claude` in `PATH`); without it everything else works."],
    ["**No user input in the shell.** Commands are fixed scripts; arguments (numbers, module names, commit hashes, database names) are checked with regular expressions before they are substituted.",
     "**Access by chat id.** Everybody else gets “no access” and is logged. Write and copy commands are accepted only from private chats – a group id in `ADMIN_CHAT_IDS` is ignored, because in a group any member could press the button.",
     "**Plan, then confirmation.** Every changing command first shows what it will do; the button belongs to the chat that asked and expires.",
     "**Claude without tools.** `/analyze` passes text to the model and gets text back. Even if a log line contains an instruction (“ignore the above…”), the model cannot do anything on the server.",
     "**No passwords in the bot.** `psql` runs with peer authentication on the server; the replication password stays on the database host.",
     "**Personal data.** Logs and `/users` contain names and e-mails: only private chats and a closed group, logs as files, never as public links.",
     "**The repository.** `.env` and `targets.json` are in `.gitignore`; the public repository was created with a fresh history, without the internal history that contains client hosts; every push is scanned for secrets."],
    [["What", "Why"],
     ["`ci.yml` → `lint`", "Python syntax, ruff (only real errors such as undefined names), ShellCheck for `run.sh` and the scripts, example configs are valid JSON without real hosts, the bot loads with the example configs"],
     ["`ci.yml` → `secrets`", "gitleaks over the whole history on every push and pull request, and weekly – new rules also find old leaks"],
     ["`.gitleaks.toml`", "the default rules plus one for Telegram bot tokens"],
     ["`dependabot.yml`", "a weekly pull request when the used actions get new versions"],
     ["`permissions: contents: read`", "the workflow token can only read; `persist-credentials: false` – it does not stay in the checkout"]],
    "There is no deployment and there are no secrets in the workflows: CI cannot reach any server, so a malicious pull request has nothing to steal. In the repository settings we also enable GitHub secret scanning with push protection (a push with a token is rejected before it lands) and branch protection on `main` with the CI checks required.",
    "A bot does not replace Prometheus and Grafana – it answers the questions an admin asks every day, from the phone and in the same way every time. We run it for every Odoo installation we maintain for companies in Germany, Austria and Switzerland; the code is open – take it, adapt it, and keep your tokens out of git.",
    "Links")

TGBOT["t"]["de"] = _b(
    "Ein Telegram-Bot für Odoo-Admins: Monitoring, Logs, Cron, Deployment und eine frische Stage-Datenbank",
    "Der Bot, mit dem wir die von uns betreuten Odoo-Server führen: /health, /log, /errors, /jobs, /users, eine KI-Analyse, Kopie Prod → Stage, git pull mit Modul-Update und Rücksprung, und /2stage – eine frische Stage-Datenbank vom PostgreSQL-Master. Echte Berichte, Installation, Sicherheit und was die GitHub Actions im Repository tun.",
    "Die meisten Fragen zu einem Odoo-Server sind jede Woche dieselben: läuft er, was steht im Log, sind die Crons gelaufen, bewegt sich die Job-Warteschlange, wer arbeitet gerade. Wir beantworten sie mit einem Telegram-Befehl statt einer SSH-Sitzung. Der Bot ist eine Python-Datei ohne Abhängigkeiten; er verbindet sich per SSH und führt feste, lesende Skripte aus. Er ist Open Source.",
    f"Kurzfassung: ein Bot pro Kunde, die Konfiguration in zwei Dateien (`.env`, `targets.json`), nichts wird auf den Odoo-Servern installiert. Lesende Befehle für alle in den erlaubten Chats; `/pull`, `/update`, `/restore`, `/backup`, `/2stage` nur für den Admin im privaten Chat, immer als Plan mit Bestätigungsknopf. Code: `{REPO.split('//')[1]}`.",
    ["Warum ein Bot", "Befehle", "Beispielberichte", "/analyze: eine zweite Meinung von Claude", "Datenbank auf eigenem Host und Streaming-Replikat",
     "/2stage: frische Stage-Datenbank vom Master", "Deployment: /pull, /update, /restore", "Installation", "Sicherheit", "GitHub: was die Actions tun", "Fazit"],
    ["**Vom Handy, in Sekunden.** `/health prod` antwortet in 2–5 Sekunden – praktisch, wenn ein Anwender anruft und man nicht am Rechner sitzt.",
     "**Immer dieselben Prüfungen.** Platte, RAM, CPU, Odoo, PostgreSQL, nginx, Ports, Login-Seite, Log – kein Schritt wird vergessen, und die Ergebnisse sind von Tag zu Tag vergleichbar.",
     "**Nichts auf den Servern.** Kein Agent, kein offener Port: der Bot braucht SSH und einen Benutzer, der Logs lesen darf.",
     "**Ein Bot pro Kunde.** Der Code ist gemeinsam, Bot-Token, Chats und Server sind getrennt. Ein Fehler in einer Chat-ID darf nicht die Logs eines Kunden in den Chat eines anderen schicken."],
    [["Befehl", "Was er tut"],
     ["`/health`", "Platte, RAM, Load Average und CPU/iowait (Top-Prozesse unter Last), Odoo-Dienst, PostgreSQL, nginx (`nginx -t`, Ports 80/443, 5xx und 502/504 in den letzten 5000 Anfragen, error.log der letzten Stunde), Odoo-Ports, HTTP-Prüfung von `/web/login`, Loggröße und Fehler"],
     ["`/log [N|all]`", "die letzten Zeilen des Odoo-Logs: bis 100 als Text ohne Datum und PID, mehr als Datei, `all` – das ganze aktuelle Log als .gz"],
     ["`/errors`", "die letzten 10 ERROR/CRITICAL/FATAL; Scanner-Rauschen und Serialization-Wiederholungen werden herausgefiltert und nur gezählt"],
     ["`/jobs`", "Cron: letzter und nächster Lauf, ▶ läuft gerade, ⚠ verspätet; queue_job: laufend, Warteschlange, zuletzt erledigt und fehlgeschlagen mit Fehlertext"],
     ["`/users [all]`", "wer in den letzten 24 Stunden in Odoo war, wer online ist, wer welche Belege geändert hat"],
     ["`/analyze`", "alles oben plus Tracebacks → Claude → Urteil, Ursachen, Schritte; Vergleich mit der vorigen Analyse"],
     ["`/backup`", "Kopie Prod → Stage: neue Datenbank mit Datum im Namen, Filestore, Entschärfung, Umschalten, Modul-Update, Prüfung – oder Start der eigenen Backup-Unit des Servers"],
     ["`/pull`", "`git pull` in jedem Repository aus `addons_path`: neue Commits und betroffene Module, dann Bestätigung"],
     ["`/update`", "`click-odoo-update`: nur Module mit geändertem Code; Odoo läuft weiter, am Ende ein Neustart-Knopf"],
     ["`/restore`", "den Code auf den Stand vor einem der letzten `/pull` zurücksetzen"],
     ["`/2stage`", "die Stage-Datenbank löschen und mit `pg_basebackup` frisch vom Master kopieren, entschärfen, Odoo Stage starten"]],
    "Echte Ausgaben unserer Bots, aus der russischen Oberfläche übersetzt; Hosts, Belegnummern und Benutzernamen sind ersetzt.",
    "Worauf wir schauen: Fehler ohne Scanner-Rauschen (Bots, die kaputtes HTTP an Port 8069 schicken, werden getrennt gezählt – sonst wäre jeder Bericht rot). In `/jobs` ist derselbe Job, der eine Woche lang jeden Abend um 22:35 scheitert, ein fachliches Problem, kein Serverproblem – der Bot zeigt den Fehlertext, so geht es direkt an die richtige Person. In der zweiten Installation warten 25 Jobs seit 22:30, der letzte wurde um 20:24 fertig – die Warteschlange steht, typischerweise läuft der Job-Runner nicht oder ein Kanal ist blockiert. ▶ „läuft gerade“ ist keine Vermutung: der Bot versucht `SELECT … FOR UPDATE SKIP LOCKED` auf `ir_cron` – eine von einem Worker gesperrte Zeile ist ein laufender Cron. `/users` rechnet aus `bus_presence`, `res_users_log` und `write_date` der Hauptbelege; es zeigt, wer wo arbeitet, nicht was er eingibt.",
    "`/analyze` sammelt den Health-Bericht, die Fehler mit Tracebacks und den Zustand von Cron und Warteschlange, fügt die vorige Analyse desselben Servers hinzu und schickt alles an Claude (`claude -p`) **ohne Werkzeuge**: das Modell kann nur die übergebenen Daten lesen, keine Befehle ausführen. Die Antwort: Urteil, Ursachen, konkrete Schritte und „was behoben ist, was bleibt, was neu ist“ seit dem letzten Mal. Das dauert etwa 30 Sekunden und ist eine gute zweite Meinung um 7 Uhr morgens – kein Ersatz für einen Admin.",
    "Bei größeren Installationen läuft PostgreSQL auf einem eigenen Host, oft mit einem Streaming-Replikat. Der Bot hat dann zwei SSH-Ziele: den Odoo-Host (Dienst oder Docker-Container, nginx, Log) und den Datenbank-Host (PostgreSQL-Status, Verbindungen, Platte, Replikation).",
    ["**Replikation in `/health`.** Aus `pg_stat_replication` auf dem Master: Adresse des Replikats, Zustand und `replay_lag`. Wachsender Rückstand oder eine fehlende `streaming`-Zeile steht im selben Bericht wie die Platte.",
     "**Schwere Lesezugriffe aufs Replikat.** `/users` durchsucht `mail_message` und die Belegtabellen – es geht an `db_ssh_ro` (das Replikat) und belastet den Master nicht.",
     "**`/jobs` auf dem Master.** Die Prüfung „läuft gerade“ braucht `FOR UPDATE SKIP LOCKED`, und das geht auf einem Hot Standby nicht.",
     "**Docker.** Für Odoo im Container liest der Bot `docker logs` und den Containerzustand statt systemd und Logdatei."],
    ["**Was er tut.** Odoo Stage stoppen, den Datenbank-Cluster von Stage löschen, mit `pg_basebackup` frisch vom Master kopieren, als eigenständige Datenbank starten, entschärfen, Odoo Stage starten. Bei Hunderten Gigabyte dauert das Stunden – der Bot zeigt den Fortschritt in einer Nachricht, die er laufend bearbeitet.",
     "**Ohne `-R`.** Die Kopie wird kein Standby: kein `standby.signal`, `postgresql.auto.conf` vom Master wird geleert, PostgreSQL startet mit der normalen Stage-Konfiguration (`wal_level=minimal` ist in Ordnung – das WAL der Kopie spielt die Crash-Recovery ein).",
     "**Entschärfen, bevor Odoo startet.** Alle Crons aus, alle Queue-Jobs abgebrochen, Mailserver aus und ihre Passwörter entfernt, `web.base.url` auf die Stage-Adresse – die Kopie kann keine einzige E-Mail senden und keine Schnittstelle aufrufen.",
     "**Auf dem Datenbank-Host, als systemd-Unit.** Das Skript läuft über `systemd-run`: eine abgerissene SSH-Sitzung oder ein Neustart des Bots unterbrechen es nicht; der Bot liest nur die Statusdatei."],
    "Das Passwort des Replikationsbenutzers erreicht weder den Bot noch den Chat noch das Log: das Skript liest `primary_conninfo` aus der Konfiguration, die schon auf dem Datenbank-Host liegt, und schreibt eine temporäre `pgpass` (Modus 600), die am Ende gelöscht wird. Schlägt etwas fehl, bevor die alten Daten gelöscht sind, startet der Bot Odoo Stage wieder – Stage bleibt, wie es war.",
    ["**`/pull`** – `git pull` in jedem Repository aus `addons_path` der Odoo-Konfiguration. Zuerst ein Plan: neue Commits je Repository und die betroffenen Module; erst nach dem Knopf wird gezogen. Die Commits „davor“ werden für `/restore` gespeichert.",
     "**`/update`** – `click-odoo-update` vergleicht Modul-Prüfsummen und aktualisiert nur Module mit geändertem Code. Odoo wird nicht gestoppt; am Ende startet ein Knopf es neu. Bei mehreren Datenbanken fragt der Bot, welche.",
     "**`/restore`** – einen der letzten `/pull` wählen und die Repositories auf die Commits davor zurücksetzen (`git reset --keep` – lokale Änderungen gehen nicht verloren), danach der `/update`-Plan.",
     "**Leitplanken.** Nur `ADMIN_CHAT_IDS` (private Chats), eine Sperre pro Server – zwei Deployments laufen nie gleichzeitig, Bestätigungsknöpfe verfallen nach 30 Minuten."],
    ["Mit @BotFather einen Bot anlegen – einen eigenen pro Kunde – und das Token in `.env` eintragen.",
     "Dem Bot schreiben: die Ablehnung steht in `bot.log` als `denied chat_id=…` – das ist die ID für `ALLOWED_CHAT_IDS`.",
     "SSH: ein eigener Schlüssel pro Kunde und ein Benutzer ohne root, der die Logs von Odoo und nginx lesen darf; `sudo -n` nur für das, was man freischaltet (`systemctl status`, `nginx -t`; Deployment und `/2stage` brauchen mehr).",
     "Für `/analyze` – Claude Code auf dem Bot-Host (`claude` im `PATH`); ohne funktioniert alles andere."],
    ["**Keine Benutzereingabe in der Shell.** Befehle sind feste Skripte; Argumente (Zahlen, Modulnamen, Commit-Hashes, Datenbanknamen) werden vor dem Einsetzen mit regulären Ausdrücken geprüft.",
     "**Zugriff per Chat-ID.** Alle anderen bekommen „kein Zugriff“ und werden protokolliert. Schreibende und kopierende Befehle werden nur aus privaten Chats angenommen – eine Gruppen-ID in `ADMIN_CHAT_IDS` wird ignoriert, weil in einer Gruppe jedes Mitglied den Knopf drücken könnte.",
     "**Erst Plan, dann Bestätigung.** Jeder ändernde Befehl zeigt zuerst, was er tun wird; der Knopf gehört dem Chat, der gefragt hat, und verfällt.",
     "**Claude ohne Werkzeuge.** `/analyze` gibt Text an das Modell und bekommt Text zurück. Selbst wenn eine Logzeile eine Anweisung enthält („ignoriere das Obige…“), kann das Modell auf dem Server nichts tun.",
     "**Keine Passwörter im Bot.** `psql` läuft mit Peer-Authentifizierung auf dem Server; das Replikationspasswort bleibt auf dem Datenbank-Host.",
     "**Personenbezogene Daten.** Logs und `/users` enthalten Namen und E-Mails: nur private Chats und eine geschlossene Gruppe, Logs als Datei, nie als öffentlicher Link.",
     "**Das Repository.** `.env` und `targets.json` stehen in `.gitignore`; das öffentliche Repository wurde mit frischer Historie angelegt, ohne die interne Historie mit Kunden-Hosts; jeder Push wird auf Geheimnisse geprüft."],
    [["Was", "Wozu"],
     ["`ci.yml` → `lint`", "Python-Syntax, ruff (nur echte Fehler wie undefinierte Namen), ShellCheck für `run.sh` und die Skripte, Beispielkonfigurationen sind gültiges JSON ohne echte Hosts, der Bot lädt mit den Beispielkonfigurationen"],
     ["`ci.yml` → `secrets`", "gitleaks über die ganze Historie bei jedem Push und Pull Request sowie wöchentlich – neue Regeln finden auch alte Lecks"],
     ["`.gitleaks.toml`", "die Standardregeln plus eine für Telegram-Bot-Tokens"],
     ["`dependabot.yml`", "ein wöchentlicher Pull Request, wenn die verwendeten Actions neue Versionen bekommen"],
     ["`permissions: contents: read`", "das Workflow-Token kann nur lesen; `persist-credentials: false` – es bleibt nicht im Checkout"]],
    "In den Workflows gibt es kein Deployment und keine Secrets: die CI erreicht keinen Server, ein bösartiger Pull Request hat also nichts zu stehlen. In den Repository-Einstellungen schalten wir zusätzlich GitHub Secret Scanning mit Push Protection ein (ein Push mit Token wird abgewiesen, bevor er ankommt) und Branch Protection auf `main` mit Pflicht-Checks der CI.",
    "Ein Bot ersetzt nicht Prometheus und Grafana – er beantwortet die Fragen, die ein Admin jeden Tag stellt, vom Handy und jedes Mal gleich. Wir betreiben ihn für jede Odoo-Installation, die wir für Unternehmen in Deutschland, Österreich und der Schweiz betreuen; der Code ist offen – nehmen, anpassen, und Tokens aus git heraushalten.",
    "Links")

TGBOT["t"]["fr"] = _b(
    "Un bot Telegram pour les admins Odoo : supervision, journaux, cron, déploiement et une base de stage fraîche",
    "Le bot avec lequel nous exploitons les serveurs Odoo dont nous avons la charge : /health, /log, /errors, /jobs, /users, une analyse par IA, une copie prod → stage, git pull avec mise à jour des modules et retour arrière, et /2stage – une base de stage fraîche depuis le maître PostgreSQL. Exemples réels, installation, sécurité et rôle des GitHub Actions du dépôt.",
    "La plupart des questions sur un serveur Odoo reviennent chaque semaine : est-il en ligne, que dit le journal, les crons ont-ils tourné, la file de jobs avance-t-elle, qui travaille en ce moment. Nous y répondons par une commande Telegram au lieu d'une session SSH. Le bot est un seul fichier Python sans dépendances ; il se connecte en SSH et exécute des scripts fixes en lecture. Il est open source.",
    f"En bref : un bot par client, la configuration dans deux fichiers (`.env`, `targets.json`), rien à installer sur les serveurs Odoo. Les commandes de lecture pour tous les chats autorisés ; `/pull`, `/update`, `/restore`, `/backup`, `/2stage` seulement pour l'admin en chat privé, toujours sous forme de plan avec un bouton de confirmation. Code : `{REPO.split('//')[1]}`.",
    ["Pourquoi un bot", "Commandes", "Exemples de rapports", "/analyze : un second avis de Claude", "Base sur un hôte séparé et réplique en streaming",
     "/2stage : une base de stage fraîche depuis le maître", "Déploiement : /pull, /update, /restore", "Installation", "Sécurité", "GitHub : ce que font les Actions", "Conclusion"],
    ["**Depuis le téléphone, en quelques secondes.** `/health prod` répond en 2 à 5 secondes – utile quand un utilisateur appelle et que l'on n'est pas devant l'ordinateur.",
     "**Toujours les mêmes contrôles.** Disque, RAM, CPU, Odoo, PostgreSQL, nginx, ports, page de connexion, journal – aucune étape n'est oubliée et les résultats se comparent d'un jour à l'autre.",
     "**Rien sur les serveurs.** Pas d'agent, pas de port ouvert : le bot a besoin de SSH et d'un utilisateur qui peut lire les journaux.",
     "**Un bot par client.** Le code est commun, le jeton du bot, les chats et les serveurs sont séparés. Une erreur d'identifiant de chat ne doit pas envoyer les journaux d'un client dans le chat d'un autre."],
    [["Commande", "Ce qu'elle fait"],
     ["`/health`", "disque, RAM, load average et CPU/iowait (processus les plus gourmands sous charge), service Odoo, PostgreSQL, nginx (`nginx -t`, ports 80/443, 5xx et 502/504 sur les 5000 dernières requêtes, error.log de la dernière heure), ports Odoo, contrôle HTTP de `/web/login`, taille du journal et erreurs"],
     ["`/log [N|all]`", "les dernières lignes du journal Odoo : jusqu'à 100 en texte sans date ni pid, plus sous forme de fichier, `all` – tout le journal courant en .gz"],
     ["`/errors`", "les 10 dernières ERROR/CRITICAL/FATAL ; le bruit des scanners et les reprises de sérialisation sont filtrés et seulement comptés"],
     ["`/jobs`", "cron : dernier et prochain passage, ▶ en cours, ⚠ en retard ; queue_job : en cours, file, derniers terminés et échoués avec l'erreur"],
     ["`/users [all]`", "qui était dans Odoo ces dernières 24 heures, qui est en ligne, qui a modifié quels documents"],
     ["`/analyze`", "tout ce qui précède plus les tracebacks → Claude → verdict, causes, étapes ; comparaison avec l'analyse précédente"],
     ["`/backup`", "copie prod → stage : nouvelle base avec la date dans le nom, filestore, neutralisation, bascule, mise à jour des modules, contrôle – ou lancement de l'unité de sauvegarde du serveur"],
     ["`/pull`", "`git pull` dans chaque dépôt de `addons_path` : nouveaux commits et modules touchés, puis confirmation"],
     ["`/update`", "`click-odoo-update` : seulement les modules dont le code a changé ; Odoo continue de tourner, un bouton de redémarrage à la fin"],
     ["`/restore`", "ramener le code à l'état d'avant l'un des derniers `/pull`"],
     ["`/2stage`", "supprimer la base de stage et en copier une fraîche depuis le maître avec `pg_basebackup`, neutraliser, démarrer Odoo stage"]],
    "Sorties réelles de nos bots, traduites de l'interface russe ; hôtes, références et noms d'utilisateurs remplacés.",
    "Ce que nous regardons : les erreurs sans le bruit des scanners (les robots qui envoient du HTTP invalide sur le port 8069 sont comptés à part, sinon chaque rapport serait rouge). Dans `/jobs`, le même job qui échoue chaque soir à 22 h 35 pendant une semaine est un problème métier, pas un problème de serveur – le bot montre le texte de l'erreur, cela part directement à la bonne personne. Dans la deuxième installation, 25 jobs attendent depuis 22 h 30 alors que le dernier s'est terminé à 20 h 24 – la file est à l'arrêt, typiquement le job runner ne tourne pas ou un canal est bloqué. ▶ « en cours » n'est pas une supposition : le bot tente `SELECT … FOR UPDATE SKIP LOCKED` sur `ir_cron` – une ligne verrouillée par un worker est un cron en cours. `/users` compte à partir de `bus_presence`, `res_users_log` et du `write_date` des documents principaux ; il montre qui travaille et où, pas ce qui est saisi.",
    "`/analyze` rassemble le rapport de santé, les erreurs avec tracebacks et l'état des crons et de la file, ajoute l'analyse précédente du même serveur et envoie le tout à Claude (`claude -p`) **sans outils** : le modèle ne peut que lire les données fournies, pas exécuter de commandes. La réponse : un verdict, des causes, des étapes concrètes et « ce qui est corrigé, ce qui reste, ce qui est nouveau » depuis la dernière fois. Cela prend environ 30 secondes et donne un bon second avis à 7 h du matin – sans remplacer un admin.",
    "Sur les grandes installations, PostgreSQL tourne sur son propre hôte, souvent avec une réplique en streaming. Le bot a alors deux cibles SSH : l'hôte Odoo (service ou conteneur Docker, nginx, journal) et l'hôte de la base (état de PostgreSQL, connexions, disque, réplication).",
    ["**La réplication dans `/health`.** Depuis `pg_stat_replication` sur le maître : adresse de la réplique, état et `replay_lag`. Un retard qui grandit ou une ligne `streaming` absente apparaît dans le même rapport que le disque.",
     "**Les lectures lourdes sur la réplique.** `/users` parcourt `mail_message` et les tables de documents – il va sur `db_ssh_ro` (la réplique) et ne charge pas le maître.",
     "**`/jobs` sur le maître.** Le contrôle « en cours » a besoin de `FOR UPDATE SKIP LOCKED`, impossible sur un hot standby.",
     "**Docker.** Pour Odoo en conteneur, le bot lit `docker logs` et l'état du conteneur au lieu de systemd et du fichier journal."],
    ["**Ce qu'il fait.** Arrêter Odoo stage, supprimer le cluster de base de stage, en copier un frais depuis le maître avec `pg_basebackup`, le démarrer comme base indépendante, le neutraliser, démarrer Odoo stage. Pour des centaines de gigaoctets, cela prend des heures – le bot affiche la progression dans un message qu'il met à jour.",
     "**Sans `-R`.** La copie ne devient pas un standby : pas de `standby.signal`, le `postgresql.auto.conf` du maître est vidé, PostgreSQL démarre avec la configuration normale du stage (`wal_level=minimal` convient – le WAL de la copie est rejoué par la récupération après crash).",
     "**Neutraliser avant le démarrage d'Odoo.** Tous les crons désactivés, tous les jobs de la file annulés, serveurs de messagerie désactivés et leurs mots de passe effacés, `web.base.url` sur l'adresse du stage – la copie ne peut envoyer aucun e-mail ni appeler aucune intégration.",
     "**Sur l'hôte de la base, comme unité systemd.** Le script tourne via `systemd-run` : une session SSH coupée ou un redémarrage du bot ne l'interrompent pas ; le bot lit seulement le fichier d'état."],
    "Le mot de passe de l'utilisateur de réplication n'atteint ni le bot, ni le chat, ni le journal : le script lit `primary_conninfo` dans la configuration déjà présente sur l'hôte de la base et écrit un `pgpass` temporaire (mode 600), supprimé à la fin. Si quelque chose échoue avant la suppression des anciennes données, le bot redémarre Odoo stage – le stage reste tel qu'il était.",
    ["**`/pull`** – `git pull` dans chaque dépôt de l'`addons_path` de la configuration Odoo. D'abord un plan : nouveaux commits par dépôt et modules concernés ; le pull ne se fait qu'après le bouton. Les commits « d'avant » sont gardés pour `/restore`.",
     "**`/update`** – `click-odoo-update` compare les sommes de contrôle des modules et ne met à jour que ceux dont le code a changé. Odoo n'est pas arrêté ; à la fin un bouton le redémarre. S'il y a plusieurs bases, le bot demande laquelle.",
     "**`/restore`** – choisir l'un des derniers `/pull` et ramener les dépôts aux commits d'avant (`git reset --keep` – les modifications locales ne sont pas perdues), puis le plan de `/update`.",
     "**Garde-fous.** Seulement `ADMIN_CHAT_IDS` (chats privés), un verrou par serveur – deux déploiements ne tournent jamais en même temps, les boutons de confirmation expirent après 30 minutes."],
    ["Créer un bot avec @BotFather – un par client – et mettre le jeton dans `.env`.",
     "Écrire au bot : le refus apparaît dans `bot.log` comme `denied chat_id=…` – c'est l'identifiant pour `ALLOWED_CHAT_IDS`.",
     "SSH : une clé dédiée par client et un utilisateur sans root qui peut lire les journaux d'Odoo et de nginx ; `sudo -n` seulement pour ce que l'on active (`systemctl status`, `nginx -t` ; le déploiement et `/2stage` demandent plus).",
     "Pour `/analyze` – Claude Code sur l'hôte du bot (`claude` dans le `PATH`) ; sans lui, tout le reste fonctionne."],
    ["**Aucune saisie utilisateur dans le shell.** Les commandes sont des scripts fixes ; les arguments (nombres, noms de modules, hachages de commits, noms de bases) sont vérifiés par expressions régulières avant d'être insérés.",
     "**Accès par identifiant de chat.** Tous les autres reçoivent « pas d'accès » et sont journalisés. Les commandes qui écrivent ou copient ne sont acceptées que depuis des chats privés – un identifiant de groupe dans `ADMIN_CHAT_IDS` est ignoré, car dans un groupe n'importe quel membre pourrait appuyer sur le bouton.",
     "**D'abord le plan, ensuite la confirmation.** Chaque commande qui modifie montre d'abord ce qu'elle va faire ; le bouton appartient au chat qui l'a demandé et expire.",
     "**Claude sans outils.** `/analyze` passe du texte au modèle et reçoit du texte. Même si une ligne de journal contient une instruction (« ignore ce qui précède… »), le modèle ne peut rien faire sur le serveur.",
     "**Aucun mot de passe dans le bot.** `psql` tourne avec l'authentification peer sur le serveur ; le mot de passe de réplication reste sur l'hôte de la base.",
     "**Données personnelles.** Les journaux et `/users` contiennent des noms et des e-mails : seulement des chats privés et un groupe fermé, les journaux en fichier, jamais en lien public.",
     "**Le dépôt.** `.env` et `targets.json` sont dans `.gitignore` ; le dépôt public a été créé avec un historique neuf, sans l'historique interne qui contient des hôtes clients ; chaque push est analysé à la recherche de secrets."],
    [["Quoi", "Pourquoi"],
     ["`ci.yml` → `lint`", "syntaxe Python, ruff (seulement les vraies erreurs comme les noms non définis), ShellCheck pour `run.sh` et les scripts, exemples de configuration en JSON valide sans vrais hôtes, le bot se charge avec ces exemples"],
     ["`ci.yml` → `secrets`", "gitleaks sur tout l'historique à chaque push et pull request, et chaque semaine – de nouvelles règles trouvent aussi d'anciennes fuites"],
     ["`.gitleaks.toml`", "les règles par défaut plus une pour les jetons de bot Telegram"],
     ["`dependabot.yml`", "une pull request hebdomadaire quand les actions utilisées ont de nouvelles versions"],
     ["`permissions: contents: read`", "le jeton du workflow ne peut que lire ; `persist-credentials: false` – il ne reste pas dans le checkout"]],
    "Les workflows ne contiennent ni déploiement ni secrets : la CI n'atteint aucun serveur, une pull request malveillante n'a donc rien à voler. Dans les réglages du dépôt, nous activons aussi le secret scanning de GitHub avec push protection (un push contenant un jeton est refusé avant d'arriver) et la protection de la branche `main` avec les contrôles de CI obligatoires.",
    "Un bot ne remplace pas Prometheus et Grafana – il répond aux questions qu'un admin se pose chaque jour, depuis le téléphone et toujours de la même façon. Nous le faisons tourner pour chaque installation Odoo que nous exploitons pour des entreprises en Allemagne, en Autriche et en Suisse ; le code est ouvert – prenez-le, adaptez-le, et gardez vos jetons hors de git.",
    "Liens")

TGBOT["t"]["el"] = _b(
    "Ένα bot Telegram για διαχειριστές Odoo: παρακολούθηση, logs, cron, deployment και φρέσκια βάση stage",
    "Το bot με το οποίο διαχειριζόμαστε τους servers Odoo που συντηρούμε: /health, /log, /errors, /jobs, /users, ανάλυση με AI, αντίγραφο prod → stage, git pull με ενημέρωση modules και επαναφορά, και /2stage – φρέσκια βάση stage από τον master της PostgreSQL. Πραγματικά παραδείγματα, εγκατάσταση, ασφάλεια και τι κάνουν τα GitHub Actions του αποθετηρίου.",
    "Οι περισσότερες ερωτήσεις για έναν server Odoo είναι ίδιες κάθε εβδομάδα: λειτουργεί, τι γράφει το log, έτρεξαν τα cron, προχωρά η ουρά εργασιών, ποιος δουλεύει τώρα. Τις απαντάμε με μία εντολή Telegram αντί για σύνδεση SSH. Το bot είναι ένα αρχείο Python χωρίς εξαρτήσεις· συνδέεται με SSH και εκτελεί σταθερά scripts μόνο ανάγνωσης. Είναι ανοιχτού κώδικα.",
    f"Συνοπτικά: ένα bot ανά πελάτη, η ρύθμιση σε δύο αρχεία (`.env`, `targets.json`), τίποτα δεν εγκαθίσταται στους servers Odoo. Εντολές ανάγνωσης για όλους στα επιτρεπόμενα chats· `/pull`, `/update`, `/restore`, `/backup`, `/2stage` μόνο για τον διαχειριστή σε ιδιωτικό chat, πάντα ως σχέδιο με κουμπί επιβεβαίωσης. Κώδικας: `{REPO.split('//')[1]}`.",
    ["Γιατί bot", "Εντολές", "Παραδείγματα αναφορών", "/analyze: δεύτερη γνώμη από τον Claude", "Βάση σε ξεχωριστό host και streaming replica",
     "/2stage: φρέσκια βάση stage από τον master", "Deployment: /pull, /update, /restore", "Εγκατάσταση", "Ασφάλεια", "GitHub: τι κάνουν τα Actions", "Συμπέρασμα"],
    ["**Από το κινητό, σε δευτερόλεπτα.** Το `/health prod` απαντά σε 2–5 δευτερόλεπτα – χρήσιμο όταν τηλεφωνεί ένας χρήστης και δεν είστε στον υπολογιστή.",
     "**Πάντα οι ίδιοι έλεγχοι.** Δίσκος, RAM, CPU, Odoo, PostgreSQL, nginx, θύρες, σελίδα σύνδεσης, log – κανένα βήμα δεν ξεχνιέται και τα αποτελέσματα συγκρίνονται από μέρα σε μέρα.",
     "**Τίποτα στους servers.** Κανένας agent, καμία ανοιχτή θύρα: το bot χρειάζεται SSH και έναν χρήστη που διαβάζει logs.",
     "**Ένα bot ανά πελάτη.** Ο κώδικας είναι κοινός, το token του bot, τα chats και οι servers χωριστά. Ένα λάθος σε chat id δεν πρέπει να στείλει τα logs ενός πελάτη στο chat άλλου."],
    [["Εντολή", "Τι κάνει"],
     ["`/health`", "δίσκος, RAM, load average και CPU/iowait (κορυφαίες διεργασίες υπό φορτίο), υπηρεσία Odoo, PostgreSQL, nginx (`nginx -t`, θύρες 80/443, 5xx και 502/504 στα τελευταία 5000 αιτήματα, error.log της τελευταίας ώρας), θύρες Odoo, έλεγχος HTTP του `/web/login`, μέγεθος log και σφάλματα"],
     ["`/log [N|all]`", "οι τελευταίες γραμμές του log Odoo: έως 100 ως κείμενο χωρίς ημερομηνία και pid, περισσότερες ως αρχείο, `all` – όλο το τρέχον log σε .gz"],
     ["`/errors`", "τα 10 τελευταία ERROR/CRITICAL/FATAL· ο θόρυβος των scanners και οι επαναλήψεις serialization φιλτράρονται και μόνο μετριούνται"],
     ["`/jobs`", "cron: τελευταία και επόμενη εκτέλεση, ▶ τρέχει τώρα, ⚠ καθυστερεί· queue_job: σε εκτέλεση, ουρά, τελευταίες ολοκληρωμένες και αποτυχημένες με το σφάλμα"],
     ["`/users [all]`", "ποιος ήταν στο Odoo το τελευταίο 24ωρο, ποιος είναι online, ποιος άλλαξε ποια έγγραφα"],
     ["`/analyze`", "όλα τα παραπάνω συν tracebacks → Claude → ετυμηγορία, αιτίες, βήματα· σύγκριση με την προηγούμενη ανάλυση"],
     ["`/backup`", "αντίγραφο prod → stage: νέα βάση με ημερομηνία στο όνομα, filestore, εξουδετέρωση, εναλλαγή, ενημέρωση modules, έλεγχος – ή εκκίνηση της μονάδας backup του server"],
     ["`/pull`", "`git pull` σε κάθε αποθετήριο του `addons_path`: νέα commits και επηρεαζόμενα modules, μετά επιβεβαίωση"],
     ["`/update`", "`click-odoo-update`: μόνο modules με αλλαγμένο κώδικα· το Odoo συνεχίζει να τρέχει, στο τέλος κουμπί επανεκκίνησης"],
     ["`/restore`", "επαναφορά του κώδικα στην κατάσταση πριν από ένα από τα τελευταία `/pull`"],
     ["`/2stage`", "διαγραφή της βάσης stage και φρέσκιο αντίγραφο από τον master με `pg_basebackup`, εξουδετέρωση, εκκίνηση του Odoo stage"]],
    "Πραγματική έξοδος των bots μας, μεταφρασμένη από το ρωσικό περιβάλλον· hosts, αριθμοί εγγράφων και ονόματα χρηστών έχουν αντικατασταθεί.",
    "Τι κοιτάμε: σφάλματα χωρίς τον θόρυβο των scanners (bots που στέλνουν χαλασμένο HTTP στη θύρα 8069 μετριούνται χωριστά, αλλιώς κάθε αναφορά θα ήταν κόκκινη). Στο `/jobs` η ίδια εργασία που αποτυγχάνει κάθε βράδυ στις 22:35 για μια εβδομάδα είναι επιχειρησιακό πρόβλημα, όχι πρόβλημα server – το bot δείχνει το κείμενο του σφάλματος, άρα πηγαίνει κατευθείαν στο σωστό άτομο. Στη δεύτερη εγκατάσταση 25 εργασίες περιμένουν από τις 22:30 ενώ η τελευταία ολοκληρώθηκε στις 20:24 – η ουρά έχει σταματήσει, συνήθως δεν τρέχει ο job runner ή ένα κανάλι είναι μπλοκαρισμένο. Το ▶ «τρέχει τώρα» δεν είναι εικασία: το bot δοκιμάζει `SELECT … FOR UPDATE SKIP LOCKED` στο `ir_cron` – μια γραμμή κλειδωμένη από worker είναι cron σε εξέλιξη. Το `/users` μετρά από `bus_presence`, `res_users_log` και `write_date` των κύριων εγγράφων· δείχνει ποιος δουλεύει και πού, όχι τι πληκτρολογεί.",
    "Το `/analyze` συγκεντρώνει την αναφορά υγείας, τα σφάλματα με tracebacks και την κατάσταση cron και ουράς, προσθέτει την προηγούμενη ανάλυση του ίδιου server και τα στέλνει στον Claude (`claude -p`) **χωρίς εργαλεία**: το μοντέλο μπορεί μόνο να διαβάσει τα δεδομένα που του δόθηκαν, όχι να εκτελέσει εντολές. Η απάντηση: ετυμηγορία, αιτίες, συγκεκριμένα βήματα και «τι διορθώθηκε, τι μένει, τι νέο» από την προηγούμενη φορά. Διαρκεί περίπου 30 δευτερόλεπτα και είναι καλή δεύτερη γνώμη στις 7 το πρωί – όχι αντικατάσταση του διαχειριστή.",
    "Σε μεγαλύτερες εγκαταστάσεις η PostgreSQL τρέχει σε δικό της host, συχνά με streaming replica. Το bot έχει τότε δύο στόχους SSH: τον host του Odoo (υπηρεσία ή container Docker, nginx, log) και τον host της βάσης (κατάσταση PostgreSQL, συνδέσεις, δίσκος, αναπαραγωγή).",
    ["**Αναπαραγωγή στο `/health`.** Από το `pg_stat_replication` στον master: διεύθυνση της replica, κατάσταση και `replay_lag`. Καθυστέρηση που μεγαλώνει ή γραμμή `streaming` που λείπει φαίνεται στην ίδια αναφορά με τον δίσκο.",
     "**Βαριές αναγνώσεις στη replica.** Το `/users` σαρώνει το `mail_message` και τους πίνακες εγγράφων – πηγαίνει στο `db_ssh_ro` (τη replica) και δεν φορτώνει τον master.",
     "**`/jobs` στον master.** Ο έλεγχος «τρέχει τώρα» χρειάζεται `FOR UPDATE SKIP LOCKED`, που δεν είναι δυνατό σε hot standby.",
     "**Docker.** Για Odoo σε container το bot διαβάζει `docker logs` και την κατάσταση του container αντί για systemd και αρχείο log."],
    ["**Τι κάνει.** Σταματά το Odoo stage, διαγράφει το cluster της βάσης stage, αντιγράφει ένα φρέσκο από τον master με `pg_basebackup`, το ξεκινά ως ανεξάρτητη βάση, το εξουδετερώνει, ξεκινά το Odoo stage. Για εκατοντάδες gigabyte αυτό διαρκεί ώρες – το bot δείχνει την πρόοδο σε ένα μήνυμα που ενημερώνει συνεχώς.",
     "**Χωρίς `-R`.** Το αντίγραφο δεν γίνεται standby: κανένα `standby.signal`, το `postgresql.auto.conf` του master αδειάζει, η PostgreSQL ξεκινά με την κανονική ρύθμιση του stage (το `wal_level=minimal` είναι εντάξει – το WAL του αντιγράφου εφαρμόζεται από το crash recovery).",
     "**Εξουδετέρωση πριν ξεκινήσει το Odoo.** Όλα τα cron ανενεργά, όλες οι εργασίες της ουράς ακυρωμένες, mail servers ανενεργοί και οι κωδικοί τους σβησμένοι, `web.base.url` στη διεύθυνση του stage – το αντίγραφο δεν μπορεί να στείλει ούτε ένα e-mail ούτε να καλέσει διασύνδεση.",
     "**Στον host της βάσης, ως μονάδα systemd.** Το script τρέχει μέσω `systemd-run`: μια διακοπή του SSH ή επανεκκίνηση του bot δεν το διακόπτουν· το bot απλώς διαβάζει το αρχείο κατάστασης."],
    "Ο κωδικός του χρήστη αναπαραγωγής δεν φτάνει ποτέ στο bot, στο chat ή στο log: το script διαβάζει το `primary_conninfo` από τη ρύθμιση που ήδη υπάρχει στον host της βάσης και γράφει προσωρινό `pgpass` (δικαιώματα 600) που διαγράφεται στο τέλος. Αν κάτι αποτύχει πριν διαγραφούν τα παλιά δεδομένα, το bot ξεκινά ξανά το Odoo stage – το stage μένει όπως ήταν.",
    ["**`/pull`** – `git pull` σε κάθε αποθετήριο του `addons_path` της ρύθμισης Odoo. Πρώτα σχέδιο: νέα commits ανά αποθετήριο και τα modules που αγγίζουν· το pull γίνεται μόνο μετά το κουμπί. Τα commits «πριν» αποθηκεύονται για το `/restore`.",
     "**`/update`** – το `click-odoo-update` συγκρίνει checksums των modules και ενημερώνει μόνο όσα άλλαξαν. Το Odoo δεν σταματά· στο τέλος ένα κουμπί το επανεκκινεί. Με πολλές βάσεις το bot ρωτά ποια.",
     "**`/restore`** – επιλογή ενός από τα τελευταία `/pull` και επαναφορά των αποθετηρίων στα commits πριν από αυτό (`git reset --keep` – οι τοπικές αλλαγές δεν χάνονται), μετά το σχέδιο του `/update`.",
     "**Δικλίδες.** Μόνο `ADMIN_CHAT_IDS` (ιδιωτικά chats), κλείδωμα ανά server – δύο deployments δεν τρέχουν ποτέ ταυτόχρονα, τα κουμπιά επιβεβαίωσης λήγουν μετά από 30 λεπτά."],
    ["Δημιουργήστε bot με το @BotFather – ξεχωριστό για κάθε πελάτη – και βάλτε το token στο `.env`.",
     "Γράψτε στο bot: η άρνηση εμφανίζεται στο `bot.log` ως `denied chat_id=…` – αυτό είναι το id για το `ALLOWED_CHAT_IDS`.",
     "SSH: ξεχωριστό κλειδί ανά πελάτη και χρήστης χωρίς root που διαβάζει τα logs του Odoo και του nginx· `sudo -n` μόνο για ό,τι ενεργοποιείτε (`systemctl status`, `nginx -t`· το deployment και το `/2stage` χρειάζονται περισσότερα).",
     "Για το `/analyze` – Claude Code στον host του bot (`claude` στο `PATH`)· χωρίς αυτό όλα τα άλλα λειτουργούν."],
    ["**Καμία είσοδος χρήστη στο shell.** Οι εντολές είναι σταθερά scripts· τα ορίσματα (αριθμοί, ονόματα modules, hashes commits, ονόματα βάσεων) ελέγχονται με κανονικές εκφράσεις πριν μπουν.",
     "**Πρόσβαση με chat id.** Όλοι οι άλλοι παίρνουν «χωρίς πρόσβαση» και καταγράφονται. Εντολές που γράφουν ή αντιγράφουν γίνονται δεκτές μόνο από ιδιωτικά chats – ένα id ομάδας στο `ADMIN_CHAT_IDS` αγνοείται, γιατί σε ομάδα οποιοδήποτε μέλος θα μπορούσε να πατήσει το κουμπί.",
     "**Πρώτα σχέδιο, μετά επιβεβαίωση.** Κάθε εντολή που αλλάζει κάτι δείχνει πρώτα τι θα κάνει· το κουμπί ανήκει στο chat που ρώτησε και λήγει.",
     "**Claude χωρίς εργαλεία.** Το `/analyze` δίνει κείμενο στο μοντέλο και παίρνει κείμενο πίσω. Ακόμη κι αν μια γραμμή log περιέχει οδηγία («αγνόησε τα παραπάνω…»), το μοντέλο δεν μπορεί να κάνει τίποτα στον server.",
     "**Κανένας κωδικός στο bot.** Το `psql` τρέχει με peer authentication στον server· ο κωδικός αναπαραγωγής μένει στον host της βάσης.",
     "**Προσωπικά δεδομένα.** Τα logs και το `/users` περιέχουν ονόματα και e-mails: μόνο ιδιωτικά chats και κλειστή ομάδα, logs ως αρχεία, ποτέ ως δημόσιοι σύνδεσμοι.",
     "**Το αποθετήριο.** Τα `.env` και `targets.json` είναι στο `.gitignore`· το δημόσιο αποθετήριο δημιουργήθηκε με νέο ιστορικό, χωρίς το εσωτερικό ιστορικό που περιέχει hosts πελατών· κάθε push ελέγχεται για μυστικά."],
    [["Τι", "Γιατί"],
     ["`ci.yml` → `lint`", "σύνταξη Python, ruff (μόνο πραγματικά σφάλματα όπως ακαθόριστα ονόματα), ShellCheck για το `run.sh` και τα scripts, τα παραδείγματα ρυθμίσεων είναι έγκυρο JSON χωρίς πραγματικούς hosts, το bot φορτώνει με αυτά"],
     ["`ci.yml` → `secrets`", "gitleaks σε όλο το ιστορικό σε κάθε push και pull request, και κάθε εβδομάδα – νέοι κανόνες βρίσκουν και παλιές διαρροές"],
     ["`.gitleaks.toml`", "οι προεπιλεγμένοι κανόνες συν ένας για tokens bot Telegram"],
     ["`dependabot.yml`", "εβδομαδιαίο pull request όταν τα χρησιμοποιούμενα actions αποκτούν νέες εκδόσεις"],
     ["`permissions: contents: read`", "το token του workflow μόνο διαβάζει· `persist-credentials: false` – δεν μένει στο checkout"]],
    "Στα workflows δεν υπάρχει deployment ούτε μυστικά: το CI δεν φτάνει σε κανέναν server, άρα ένα κακόβουλο pull request δεν έχει τι να κλέψει. Στις ρυθμίσεις του αποθετηρίου ενεργοποιούμε επίσης το secret scanning του GitHub με push protection (ένα push με token απορρίπτεται πριν φτάσει) και branch protection στο `main` με υποχρεωτικούς ελέγχους CI.",
    "Ένα bot δεν αντικαθιστά το Prometheus και το Grafana – απαντά στις ερωτήσεις που κάνει ένας διαχειριστής κάθε μέρα, από το κινητό και πάντα με τον ίδιο τρόπο. Το τρέχουμε για κάθε εγκατάσταση Odoo που συντηρούμε για εταιρείες στη Γερμανία, την Αυστρία και την Ελβετία· ο κώδικας είναι ανοιχτός – πάρτε τον, προσαρμόστε τον και κρατήστε τα tokens σας έξω από το git.",
    "Σύνδεσμοι")

TGBOT["t"]["uk"] = _b(
    "Telegram-бот для адміністратора Odoo: моніторинг, логи, cron, деплой і свіжа база stage",
    "Бот, яким ми обслуговуємо сервери Odoo: /health, /log, /errors, /jobs, /users, аналіз через ШІ, копія prod → stage, git pull з оновленням модулів і відкатом, і /2stage – свіжа база stage з майстра PostgreSQL. Реальні приклади звітів, встановлення, безпека і що роблять GitHub Actions у репозиторії.",
    "Більшість питань до сервера Odoo щотижня однакові: чи працює, що в лозі, чи відпрацювали cron, чи рухається черга завдань, хто зараз працює. Ми відповідаємо на них однією командою в Telegram замість SSH-сесії. Бот – один файл Python без залежностей; він ходить на сервери по SSH і виконує фіксовані скрипти на читання. Код відкритий.",
    f"Коротко: окремий бот на клієнта, налаштування у двох файлах (`.env`, `targets.json`), на сервери Odoo нічого не встановлюється. Команди на читання – для всіх у дозволених чатах; `/pull`, `/update`, `/restore`, `/backup`, `/2stage` – лише адміністратору в особистому чаті, завжди як план з кнопкою підтвердження. Код: `{REPO.split('//')[1]}`.",
    ["Навіщо бот", "Команди", "Приклади звітів", "/analyze: друга думка від Claude", "База на окремому хості і потокова репліка",
     "/2stage: свіжа база stage з майстра", "Деплой: /pull, /update, /restore", "Встановлення", "Безпека", "GitHub: що роблять Actions", "Висновок"],
    ["**З телефону, за секунди.** `/health prod` відповідає за 2–5 секунд – зручно, коли телефонує користувач, а ви не за комп'ютером.",
     "**Завжди ті самі перевірки.** Диск, RAM, CPU, Odoo, PostgreSQL, nginx, порти, сторінка входу, лог – жоден крок не забудеться, а результати можна порівнювати день у день.",
     "**Нічого на серверах.** Ні агента, ні відкритого порту: боту потрібні SSH і користувач, який може читати логи.",
     "**Окремий бот на клієнта.** Код спільний, токен бота, чати і сервери – окремі. Помилка в chat id не повинна відправити логи одного клієнта в чат іншого."],
    [["Команда", "Що робить"],
     ["`/health`", "диск, RAM, load average і CPU/iowait (топ процесів під навантаженням), сервіс Odoo, PostgreSQL, nginx (`nginx -t`, порти 80/443, 5xx і 502/504 в останніх 5000 запитах, error.log за годину), порти Odoo, HTTP-перевірка `/web/login`, розмір лога і помилки"],
     ["`/log [N|all]`", "останні рядки лога Odoo: до 100 – текстом без дати і pid, більше – файлом, `all` – весь поточний лог у .gz"],
     ["`/errors`", "10 останніх ERROR/CRITICAL/FATAL; шум сканерів і повтори serialization відсіюються і лише рахуються"],
     ["`/jobs`", "cron: останній і наступний запуск, ▶ виконується зараз, ⚠ прострочено; queue_job: що виконується, черга, останні виконані і з помилкою разом з текстом помилки"],
     ["`/users [all]`", "хто був в Odoo за 24 години, хто онлайн, хто змінював які документи"],
     ["`/analyze`", "усе вище плюс трейсбеки → Claude → вердикт, причини, кроки; порівняння з минулим аналізом"],
     ["`/backup`", "копія prod → stage: нова база з датою в імені, filestore, знешкодження, перемикання, оновлення модулів, перевірка – або запуск власного юніта бекапу сервера"],
     ["`/pull`", "`git pull` у кожному репозиторії з `addons_path`: нові коміти і зачеплені модулі, потім підтвердження"],
     ["`/update`", "`click-odoo-update`: лише модулі, у яких змінився код; Odoo не зупиняється, наприкінці кнопка перезапуску"],
     ["`/restore`", "повернути код до стану перед одним з останніх `/pull`"],
     ["`/2stage`", "видалити базу stage і скопіювати свіжу з майстра через `pg_basebackup`, знешкодити, запустити Odoo stage"]],
    "Реальний вивід наших ботів (тут – переклад з інтерфейсу); хости, номери документів та імена користувачів замінені.",
    "На що дивимось: помилки без шуму сканерів (боти, що шлють бите HTTP на порт 8069, рахуються окремо – інакше кожен звіт був би червоним). У `/jobs` одне й те саме завдання, що тиждень поспіль падає щовечора о 22:35, – це бізнесова проблема, а не серверна: бот показує текст помилки, і вона одразу йде потрібній людині. У другій інсталяції 25 завдань чекають з 22:30, а останнє виконане о 20:24 – черга стоїть, зазвичай не працює job runner або заблокований канал. ▶ «виконується зараз» – не здогадка: бот пробує `SELECT … FOR UPDATE SKIP LOCKED` по `ir_cron` – рядок, заблокований воркером, і є cron, що виконується. `/users` рахує з `bus_presence`, `res_users_log` і `write_date` основних документів; показує, хто і де працює, а не що саме вводить.",
    "`/analyze` збирає звіт health, помилки з трейсбеками і стан cron та черги, додає минулий аналіз цього ж сервера і передає все Claude (`claude -p`) **без інструментів**: модель може лише читати передані дані, а не виконувати команди. Відповідь – вердикт, причини, конкретні кроки і «що виправлено, що залишилось, що нового» з минулого разу. Триває близько 30 секунд і є доброю другою думкою о 7 ранку – але не заміною адміністратора.",
    "На великих інсталяціях PostgreSQL працює на окремому хості, часто з потоковою реплікою. Тоді в бота дві SSH-цілі: хост Odoo (сервіс або Docker-контейнер, nginx, лог) і хост бази (стан PostgreSQL, з'єднання, диск, реплікація).",
    ["**Реплікація в `/health`.** З `pg_stat_replication` на майстрі: адреса репліки, стан і `replay_lag`. Відставання, що росте, або відсутній рядок `streaming` видно в тому ж звіті, що й диск.",
     "**Важкі читання – на репліку.** `/users` проходить `mail_message` і таблиці документів – він іде на `db_ssh_ro` (репліку) і не навантажує майстер.",
     "**`/jobs` – на майстрі.** Перевірці «виконується зараз» потрібен `FOR UPDATE SKIP LOCKED`, а на hot standby це неможливо.",
     "**Docker.** Для Odoo в контейнері бот читає `docker logs` і стан контейнера замість systemd і файлу лога."],
    ["**Що робить.** Зупиняє Odoo stage, видаляє кластер бази stage, копіює свіжий з майстра через `pg_basebackup`, запускає його як самостійну базу, знешкоджує, запускає Odoo stage. Для сотень гігабайт це години – бот показує хід в одному повідомленні, яке постійно оновлює.",
     "**Без `-R`.** Копія не стає standby: жодного `standby.signal`, `postgresql.auto.conf` з майстра очищається, PostgreSQL стартує зі звичайними конфігами stage (`wal_level=minimal` підходить – WAL з копії програється crash recovery).",
     "**Знешкодження до запуску Odoo.** Усі cron вимкнені, усі завдання черги скасовані, поштові сервери вимкнені, їхні паролі стерті, `web.base.url` – адреса stage: копія не зможе надіслати жодного листа чи викликати інтеграцію.",
     "**На хості бази, як systemd-юніт.** Скрипт запускається через `systemd-run`: обрив SSH чи перезапуск бота його не переривають; бот лише читає файл статусу."],
    "Пароль користувача реплікації не потрапляє ні в бот, ні в чат, ні в лог: скрипт бере `primary_conninfo` з конфігу, який уже лежить на хості бази, і пише тимчасовий `pgpass` (права 600), що видаляється наприкінці. Якщо щось впаде до видалення старих даних, бот запустить Odoo stage назад – stage залишиться як був.",
    ["**`/pull`** – `git pull` у кожному репозиторії з `addons_path` конфігу Odoo. Спершу план: нові коміти по репозиторіях і зачеплені модулі; pull – лише після кнопки. Коміти «до» зберігаються для `/restore`.",
     "**`/update`** – `click-odoo-update` порівнює контрольні суми модулів і оновлює лише ті, у яких змінився код. Odoo не зупиняється; наприкінці кнопка перезапуску. Якщо баз кілька – бот спитає яку.",
     "**`/restore`** – вибрати один з останніх `/pull` і повернути репозиторії до комітів перед ним (`git reset --keep` – локальні зміни не втрачаються), потім план `/update`.",
     "**Запобіжники.** Лише `ADMIN_CHAT_IDS` (особисті чати), блокування на сервер – два деплої одночасно не підуть, кнопки підтвердження застарівають за 30 хвилин."],
    ["Створіть бота в @BotFather – окремого на кожного клієнта – і впишіть токен у `.env`.",
     "Напишіть боту: відмова з'явиться в `bot.log` як `denied chat_id=…` – це id для `ALLOWED_CHAT_IDS`.",
     "SSH: окремий ключ на клієнта і користувач без root, який може читати логи Odoo і nginx; `sudo -n` лише для того, що вмикаєте (`systemctl status`, `nginx -t`; деплою і `/2stage` потрібно більше).",
     "Для `/analyze` – Claude Code на хості бота (`claude` у `PATH`); без нього решта працює."],
    ["**Жодного вводу користувача в shell.** Команди – фіксовані скрипти; аргументи (числа, імена модулів, хеші комітів, імена баз) перевіряються регулярними виразами до підстановки.",
     "**Доступ за chat id.** Усі інші отримують «Немає доступу» і пишуться в лог. Команди, що змінюють чи копіюють, приймаються лише з особистих чатів – id групи в `ADMIN_CHAT_IDS` ігнорується, бо в групі кнопку міг би натиснути будь-який учасник.",
     "**Спершу план, потім підтвердження.** Кожна команда, що змінює, спочатку показує, що зробить; кнопка належить чату, який питав, і застаріває.",
     "**Claude без інструментів.** `/analyze` передає моделі текст і отримує текст. Навіть якщо в рядку лога є інструкція («ігноруй усе вище…»), модель нічого не зможе зробити на сервері.",
     "**Жодних паролів у боті.** `psql` працює з peer-автентифікацією на сервері; пароль реплікації залишається на хості бази.",
     "**Персональні дані.** Логи і `/users` містять імена та e-mail: лише особисті чати і закрита група, логи – файлом, ніколи публічним посиланням.",
     "**Репозиторій.** `.env` і `targets.json` – у `.gitignore`; публічний репозиторій створено з чистою історією, без внутрішньої, де є хости клієнтів; кожен push перевіряється на секрети."],
    [["Що", "Навіщо"],
     ["`ci.yml` → `lint`", "синтаксис Python, ruff (лише справжні помилки, як-от невизначені імена), ShellCheck для `run.sh` і скриптів, приклади конфігів – валідний JSON без реальних хостів, бот завантажується з прикладами конфігів"],
     ["`ci.yml` → `secrets`", "gitleaks по всій історії на кожен push і pull request, а також щотижня – нові правила знаходять і старі витоки"],
     ["`.gitleaks.toml`", "стандартні правила плюс одне для токенів Telegram-ботів"],
     ["`dependabot.yml`", "щотижневий pull request, коли в використаних actions з'являються нові версії"],
     ["`permissions: contents: read`", "токен workflow може лише читати; `persist-credentials: false` – він не залишається в checkout"]],
    "У workflow немає ні деплою, ні секретів: CI не дістає до жодного сервера, тож шкідливому pull request нічого красти. У налаштуваннях репозиторію ми також вмикаємо GitHub secret scanning з push protection (push з токеном відхиляється ще до того, як потрапить у репозиторій) і захист гілки `main` з обов'язковими перевірками CI.",
    "Бот не замінює Prometheus і Grafana – він відповідає на питання, які адміністратор ставить щодня, з телефону і щоразу однаково. Ми використовуємо його на кожній інсталяції Odoo, яку обслуговуємо для компаній у Німеччині, Австрії та Швейцарії; код відкритий – беріть, адаптуйте і тримайте токени поза git.",
    "Посилання")

TGBOT["t"]["ru"] = _b(
    "Telegram-бот для администратора Odoo: мониторинг, логи, cron, деплой и свежая база stage",
    "Бот, которым мы обслуживаем серверы Odoo: /health, /log, /errors, /jobs, /users, анализ через ИИ, копия prod → stage, git pull с обновлением модулей и откатом, и /2stage – свежая база stage с мастера PostgreSQL. Реальные примеры отчётов, установка, безопасность и что делают GitHub Actions в репозитории.",
    "Большинство вопросов к серверу Odoo каждую неделю одни и те же: работает ли, что в логе, отработали ли cron, движется ли очередь задач, кто сейчас работает. Мы отвечаем на них одной командой в Telegram вместо SSH-сессии. Бот – один файл Python без зависимостей; он ходит на серверы по SSH и выполняет фиксированные скрипты на чтение. Код открыт.",
    f"Коротко: отдельный бот на клиента, настройки в двух файлах (`.env`, `targets.json`), на серверы Odoo ничего не ставится. Команды на чтение – для всех в разрешённых чатах; `/pull`, `/update`, `/restore`, `/backup`, `/2stage` – только администратору в личном чате, всегда как план с кнопкой подтверждения. Код: `{REPO.split('//')[1]}`.",
    ["Зачем бот", "Команды", "Примеры отчётов", "/analyze: второе мнение от Claude", "База на отдельном хосте и потоковая реплика",
     "/2stage: свежая база stage с мастера", "Деплой: /pull, /update, /restore", "Установка", "Безопасность", "GitHub: что делают Actions", "Итог"],
    ["**С телефона, за секунды.** `/health prod` отвечает за 2–5 секунд – удобно, когда звонит пользователь, а вы не за компьютером.",
     "**Всегда одни и те же проверки.** Диск, RAM, CPU, Odoo, PostgreSQL, nginx, порты, страница входа, лог – ни один шаг не забудется, а результаты можно сравнивать день ко дню.",
     "**Ничего на серверах.** Ни агента, ни открытого порта: боту нужны SSH и пользователь, который может читать логи.",
     "**Отдельный бот на клиента.** Код общий, токен бота, чаты и серверы – отдельные. Ошибка в chat id не должна отправить логи одного клиента в чат другого."],
    [["Команда", "Что делает"],
     ["`/health`", "диск, RAM, load average и CPU/iowait (топ процессов под нагрузкой), сервис Odoo, PostgreSQL, nginx (`nginx -t`, порты 80/443, 5xx и 502/504 в последних 5000 запросах, error.log за час), порты Odoo, HTTP-проверка `/web/login`, размер лога и ошибки"],
     ["`/log [N|all]`", "последние строки лога Odoo: до 100 – текстом без даты и pid, больше – файлом, `all` – весь текущий лог в .gz"],
     ["`/errors`", "10 последних ERROR/CRITICAL/FATAL; шум сканеров и повторы serialization отсеиваются и только считаются"],
     ["`/jobs`", "cron: последний и следующий запуск, ▶ выполняется сейчас, ⚠ просрочен; queue_job: что выполняется, очередь, последние выполненные и упавшие с текстом ошибки"],
     ["`/users [all]`", "кто был в Odoo за 24 часа, кто онлайн, кто менял какие документы"],
     ["`/analyze`", "всё выше плюс трейсбеки → Claude → вердикт, причины, шаги; сравнение с прошлым анализом"],
     ["`/backup`", "копия prod → stage: новая база с датой в имени, filestore, обезвреживание, переключение, обновление модулей, проверка – или запуск собственного юнита бэкапа сервера"],
     ["`/pull`", "`git pull` во всех репозиториях из `addons_path`: новые коммиты и затронутые модули, потом подтверждение"],
     ["`/update`", "`click-odoo-update`: только модули, у которых изменился код; Odoo не останавливается, в конце кнопка перезапуска"],
     ["`/restore`", "вернуть код к состоянию до одного из последних `/pull`"],
     ["`/2stage`", "удалить базу stage и скопировать свежую с мастера через `pg_basebackup`, обезвредить, запустить Odoo stage"]],
    "Реальный вывод наших ботов (здесь – перевод с интерфейса); хосты, номера документов и имена пользователей заменены.",
    "На что смотрим: ошибки без шума сканеров (боты, которые шлют битый HTTP на порт 8069, считаются отдельно – иначе каждый отчёт был бы красным). В `/jobs` одна и та же задача, которая неделю подряд падает каждый вечер в 22:35, – это бизнес-проблема, а не серверная: бот показывает текст ошибки, и она сразу уходит нужному человеку. Во второй инсталляции 25 задач ждут с 22:30, а последняя выполнена в 20:24 – очередь стоит, обычно не работает job runner или заблокирован канал. ▶ «выполняется сейчас» – не догадка: бот пробует `SELECT … FOR UPDATE SKIP LOCKED` по `ir_cron` – строка, заблокированная воркером, и есть выполняющийся cron. `/users` считает по `bus_presence`, `res_users_log` и `write_date` основных документов; показывает, кто и где работает, а не что именно вводит.",
    "`/analyze` собирает отчёт health, ошибки с трейсбеками и состояние cron и очереди, добавляет прошлый анализ этого же сервера и передаёт всё Claude (`claude -p`) **без инструментов**: модель может только читать переданные данные, а не выполнять команды. Ответ – вердикт, причины, конкретные шаги и «что исправлено, что осталось, что нового» с прошлого раза. Занимает около 30 секунд и даёт хорошее второе мнение в 7 утра – но не заменяет администратора.",
    "На больших инсталляциях PostgreSQL работает на отдельном хосте, часто с потоковой репликой. Тогда у бота две SSH-цели: хост Odoo (сервис или Docker-контейнер, nginx, лог) и хост базы (состояние PostgreSQL, соединения, диск, репликация).",
    ["**Репликация в `/health`.** Из `pg_stat_replication` на мастере: адрес реплики, состояние и `replay_lag`. Растущее отставание или пропавшая строка `streaming` видны в том же отчёте, что и диск.",
     "**Тяжёлые чтения – на реплику.** `/users` проходит `mail_message` и таблицы документов – он идёт на `db_ssh_ro` (реплику) и не нагружает мастер.",
     "**`/jobs` – на мастере.** Проверке «выполняется сейчас» нужен `FOR UPDATE SKIP LOCKED`, а на hot standby это невозможно.",
     "**Docker.** Для Odoo в контейнере бот читает `docker logs` и состояние контейнера вместо systemd и файла лога."],
    ["**Что делает.** Останавливает Odoo stage, удаляет кластер базы stage, копирует свежий с мастера через `pg_basebackup`, запускает его как самостоятельную базу, обезвреживает, запускает Odoo stage. Для сотен гигабайт это часы – бот показывает ход в одном сообщении, которое постоянно обновляет.",
     "**Без `-R`.** Копия не становится standby: никакого `standby.signal`, `postgresql.auto.conf` с мастера очищается, PostgreSQL стартует с обычными конфигами stage (`wal_level=minimal` подходит – WAL из копии проигрывается crash recovery).",
     "**Обезвреживание до запуска Odoo.** Все cron выключены, все задачи очереди отменены, почтовые серверы выключены, их пароли стёрты, `web.base.url` – адрес stage: копия не сможет отправить ни одного письма и вызвать интеграцию.",
     "**На хосте базы, как systemd-юнит.** Скрипт запускается через `systemd-run`: обрыв SSH или перезапуск бота его не прерывают; бот только читает файл статуса."],
    "Пароль пользователя репликации не попадает ни в бот, ни в чат, ни в лог: скрипт берёт `primary_conninfo` из конфига, который уже лежит на хосте базы, и пишет временный `pgpass` (права 600), который удаляется в конце. Если что-то упадёт до удаления старых данных, бот запустит Odoo stage обратно – stage останется как был.",
    ["**`/pull`** – `git pull` во всех репозиториях из `addons_path` конфига Odoo. Сначала план: новые коммиты по репозиториям и затронутые модули; pull – только после кнопки. Коммиты «до» сохраняются для `/restore`.",
     "**`/update`** – `click-odoo-update` сравнивает контрольные суммы модулей и обновляет только те, у которых изменился код. Odoo не останавливается; в конце кнопка перезапуска. Если баз несколько – бот спросит, какую.",
     "**`/restore`** – выбрать один из последних `/pull` и вернуть репозитории к коммитам до него (`git reset --keep` – локальные правки не теряются), затем план `/update`.",
     "**Предохранители.** Только `ADMIN_CHAT_IDS` (личные чаты), блокировка на сервер – два деплоя одновременно не пойдут, кнопки подтверждения устаревают через 30 минут."],
    ["Создайте бота в @BotFather – отдельного на каждого клиента – и впишите токен в `.env`.",
     "Напишите боту: отказ появится в `bot.log` как `denied chat_id=…` – это id для `ALLOWED_CHAT_IDS`.",
     "SSH: отдельный ключ на клиента и пользователь без root, который может читать логи Odoo и nginx; `sudo -n` только для того, что включаете (`systemctl status`, `nginx -t`; деплою и `/2stage` нужно больше).",
     "Для `/analyze` – Claude Code на хосте бота (`claude` в `PATH`); без него остальное работает."],
    ["**Никакого ввода пользователя в shell.** Команды – фиксированные скрипты; аргументы (числа, имена модулей, хэши коммитов, имена баз) проверяются регулярными выражениями до подстановки.",
     "**Доступ по chat id.** Все остальные получают «Нет доступа» и пишутся в лог. Изменяющие и копирующие команды принимаются только из личных чатов – id группы в `ADMIN_CHAT_IDS` игнорируется, потому что в группе кнопку мог бы нажать любой участник.",
     "**Сначала план, потом подтверждение.** Каждая изменяющая команда сначала показывает, что сделает; кнопка принадлежит чату, который спрашивал, и устаревает.",
     "**Claude без инструментов.** `/analyze` передаёт модели текст и получает текст. Даже если в строке лога есть инструкция («игнорируй всё выше…»), модель ничего не сможет сделать на сервере.",
     "**Никаких паролей в боте.** `psql` работает с peer-аутентификацией на сервере; пароль репликации остаётся на хосте базы.",
     "**Персональные данные.** Логи и `/users` содержат имена и e-mail: только личные чаты и закрытая группа, логи – файлом, никогда публичной ссылкой.",
     "**Репозиторий.** `.env` и `targets.json` – в `.gitignore`; публичный репозиторий создан с чистой историей, без внутренней, где есть хосты клиентов; каждый push проверяется на секреты."],
    [["Что", "Зачем"],
     ["`ci.yml` → `lint`", "синтаксис Python, ruff (только настоящие ошибки, например неопределённые имена), ShellCheck для `run.sh` и скриптов, примеры конфигов – валидный JSON без реальных хостов, бот загружается с примерами конфигов"],
     ["`ci.yml` → `secrets`", "gitleaks по всей истории на каждый push и pull request, а также еженедельно – новые правила находят и старые утечки"],
     ["`.gitleaks.toml`", "стандартные правила плюс одно для токенов Telegram-ботов"],
     ["`dependabot.yml`", "еженедельный pull request, когда у используемых actions выходят новые версии"],
     ["`permissions: contents: read`", "токен workflow может только читать; `persist-credentials: false` – он не остаётся в checkout"]],
    "В workflow нет ни деплоя, ни секретов: CI не достаёт ни до одного сервера, так что вредоносному pull request нечего украсть. В настройках репозитория мы также включаем GitHub secret scanning с push protection (push с токеном отклоняется ещё до того, как попадёт в репозиторий) и защиту ветки `main` с обязательными проверками CI.",
    "Бот не заменяет Prometheus и Grafana – он отвечает на вопросы, которые администратор задаёт каждый день, с телефона и каждый раз одинаково. Мы используем его на каждой инсталляции Odoo, которую обслуживаем для компаний в Германии, Австрии и Швейцарии; код открыт – берите, адаптируйте и держите токены вне git.",
    "Ссылки")
