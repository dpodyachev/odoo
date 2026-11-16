# Статья 24: Odoo через полгода–год в продакшене – периметр (proxy_mode, nginx, права на ФС), регламентное обслуживание
# (ir_logging, вложения, кроны, сессии, раздутые таблицы), мониторинг (зависшие cron, queue_job, health, метрики через
# postgres_exporter, odoo shell). По тексту владельца, проверено и исправлено. Все 6 языков.

LONGRUN = {
    "slug": "odoo-production-hardening-housekeeping-monitoring",
    "date": "2026-11-16",
    "tags": ["Odoo", "Security", "nginx", "PostgreSQL", "Monitoring", "Maintenance"],
    "code": {
        "nginx": ("nginx · perimeter in front of Odoo (fragment of the 443 server block)", """# odoo.conf: proxy_mode = True  – Odoo then trusts X-Forwarded-For/-Host/-Proto, so nginx MUST overwrite them
proxy_set_header X-Forwarded-For   $remote_addr;      # not $proxy_add_x_forwarded_for if nginx is the first hop
proxy_set_header X-Forwarded-Host  $host;
proxy_set_header X-Forwarded-Proto $scheme;
proxy_set_header X-Real-IP         $remote_addr;

location ~ ^/web/database/ { deny all; }                      # manager, selector, backup/restore/drop
location = /website/info  { deny all; }

# external API only for known integrations (the web client itself uses /web/dataset/…, not these)
location ~ ^/(xmlrpc|jsonrpc|json/2)(/|$) {
    allow 10.0.0.0/8;          # e.g. telephony, shop, ETL
    allow 203.0.113.10;
    deny  all;
    proxy_pass http://odoo;
}

# login brake (http {}: limit_req_zone $binary_remote_addr zone=odoo_login:10m rate=10r/m;)
location = /web/login { limit_req zone=odoo_login burst=5 nodelay; proxy_pass http://odoo; }"""),
        "perm": ("bash · Odoo may write only to data_dir", """# code: owned by root (or a deploy user), readable for odoo – a hole in a module cannot rewrite code
sudo chown -R root:odoo /opt/odoo/odoo /opt/odoo/custom-addons
sudo chmod -R u=rwX,g=rX,o= /opt/odoo/odoo /opt/odoo/custom-addons
# config: secrets inside, readable for odoo, not writable
sudo chown root:odoo /etc/odoo/odoo.conf && sudo chmod 640 /etc/odoo/odoo.conf
# data: filestore + sessions – the only place Odoo writes (plus the log directory)
sudo chown -R odoo:odoo /var/lib/odoo
# Docker: code baked into the image or mounted :ro, only the data volume writable
#   volumes: [ "./addons:/mnt/extra-addons:ro", "odoo-data:/var/lib/odoo" ]"""),
        "sizes": ("SQL · what grows? (run monthly)", """-- biggest tables incl. indexes and TOAST
SELECT relname, pg_size_pretty(pg_total_relation_size(oid)) AS total
  FROM pg_class WHERE relkind = 'r' ORDER BY pg_total_relation_size(oid) DESC LIMIT 15;

-- attachments by model (db_datas = in the database, file_size = in the filestore)
SELECT res_model, count(*), pg_size_pretty(sum(file_size)) AS size
  FROM ir_attachment GROUP BY res_model ORDER BY sum(file_size) DESC NULLS LAST LIMIT 15;

-- attachments not linked to a record (res_id 0/NULL) older than 30 days – REVIEW, do not delete blindly:
-- website images, report templates, field attachments (res_field) are legitimately unlinked
SELECT res_model, res_field IS NOT NULL AS is_field, count(*), pg_size_pretty(sum(file_size))
  FROM ir_attachment
 WHERE coalesce(res_id, 0) = 0 AND create_date < now() - interval '30 days'
 GROUP BY 1, 2 ORDER BY sum(file_size) DESC NULLS LAST;"""),
        "clean": ("SQL · housekeeping that is safe to automate", """-- ir_logging: server action logs, log_db, some audit modules – keep 30 days
DELETE FROM ir_logging WHERE create_date < now() - interval '30 days';

-- sent e-mails kept with auto_delete = false (mail_mail rows, not the chatter messages)
DELETE FROM mail_mail WHERE state = 'sent' AND write_date < now() - interval '30 days';

-- done queue jobs are removed by the cron "AutoVacuum Job Queue" (queue_job) – check it is active:
SELECT cron_name, active, nextcall, lastcall FROM ir_cron
 WHERE cron_name ILIKE ANY (ARRAY['%vacuum%', '%garbage%', '%mail queue%']);

-- after big deletions: return space inside the tables (no lock; VACUUM FULL only in a maintenance window)
VACUUM (ANALYZE) ir_logging; VACUUM (ANALYZE) mail_mail;"""),
        "crons": ("SQL · review of active crons", """SELECT c.id, c.cron_name, c.interval_number || ' ' || c.interval_type AS every,
       c.nextcall, c.lastcall, m.model
  FROM ir_cron c JOIN ir_model m ON m.id = c.model_id
 WHERE c.active ORDER BY c.interval_type, c.interval_number;
-- keep: Base: Auto-vacuum internal data, Mail: Email Queue Manager, Mail: Fetchmail (if incoming mail is used),
--       queue_job garbage collector / requeue, Notification cleanup, currency rates (if used)
-- candidates to switch off: Publisher: Update Notification, digest e-mails, unused integrations and demo-style crons"""),
        "mon": ("SQL · monitoring queries (every 5 min, alert if not empty)", """-- 1) crons that should have run more than 30 min ago
SELECT id, cron_name, nextcall FROM ir_cron
 WHERE active AND nextcall < now() AT TIME ZONE 'UTC' - interval '30 minutes';

-- 2) a cron/job that runs too long: transactions older than 20 min
SELECT pid, now() - xact_start AS age, application_name, left(query, 120)
  FROM pg_stat_activity WHERE datname = current_database() AND xact_start < now() - interval '20 minutes';

-- 3) queue_job: backlog and failures
SELECT state, count(*) FROM queue_job WHERE state NOT IN ('done', 'cancelled') GROUP BY state;
SELECT count(*) AS failed_last_hour FROM queue_job WHERE state = 'failed' AND date_done > now() - interval '1 hour';"""),
        "exporter": ("postgres_exporter · Odoo metrics for Prometheus without an Odoo module", """# queries.yaml for prometheus-community/postgres_exporter (--extend.query-path)
odoo_cron:
  query: |
    SELECT count(*) FILTER (WHERE active) AS active,
           count(*) FILTER (WHERE active AND nextcall < now() AT TIME ZONE 'UTC' - interval '30 minutes') AS late
      FROM ir_cron
  metrics:
    - active: { usage: GAUGE, description: "active crons" }
    - late:   { usage: GAUGE, description: "crons late by more than 30 min" }
odoo_queue_job:
  query: "SELECT state, count(*) AS jobs FROM queue_job WHERE state <> 'done' GROUP BY state"
  metrics:
    - state: { usage: LABEL }
    - jobs:  { usage: GAUGE, description: "queue jobs per state" }
# plus the usual: node_exporter (CPU/RAM/disk), nginx 5xx rate, ERROR/CRITICAL count in the Odoo log (Loki/promtail)"""),
        "shell": ("odoo shell · diagnose with the ORM instead of raw SQL", """odoo-bin shell -c /etc/odoo/odoo.conf -d mydb --no-http
>>> env.user.name                                   # the shell runs as superuser (OdooBot / __system__)
>>> u = env.ref('base.user_admin')
>>> env['sale.order'].with_user(u).check_access_rights('write', raise_exception=False)   # rights as a real user
>>> so = env['sale.order'].browse(42); so._compute_amounts(); so.amount_total            # recompute in memory
>>> env.cr.rollback()                               # nothing is saved unless you call env.cr.commit()"""),
    },
    "links": [
        ("Blog: the main problems of Odoo – and admin tips", "@blog:odoo-main-problems-limitations-devops-tips"),
        ("Blog: nginx security audit in front of Odoo", "@blog:nginx-security-audit-odoo-hsts-cookies-x-frame-options"),
        ("Blog: password protection for the database manager", "@blog:nginx-apache-password-protect-odoo-database-manager"),
        ("Blog: leaked passwords, brute force and 2FA in Odoo", "@blog:password-leaks-brute-force-2fa-odoo"),
        ("Blog: Odoo server security – logs, secrets, ports, encryption", "@blog:odoo-server-security-logs-secrets-ports-encryption"),
        ("Blog: PostgreSQL cheat sheet for Odoo admins", "@blog:postgresql-odoo-admin-cheat-sheet"),
        ("Blog: PoWA – query history for PostgreSQL", "@blog:powa-postgresql-workload-analyzer-odoo-docker"),
        ("Blog: Grafana behind nginx", "@blog:grafana-behind-nginx-subpath-odoo"),
        ("postgres_exporter (Prometheus)", "https://github.com/prometheus-community/postgres_exporter"),
        ("Odoo security skill for AI agents (Markdown)", "https://2027.pp.ua/skill_odoo_security.md"),
    ],
    "t": {},
}


def _l(title, summary, intro, note, h, sec, sec_p, house, house_note, mon, mon_p, closing, links):
    return {"title": title, "summary": summary, "body": [
        ("p", intro), ("note", note),
        ("h", h[0]), ("ul", sec), ("code", "nginx"), ("p", sec_p), ("code", "perm"),
        ("h", h[1]), ("ul", house), ("code", "sizes"), ("code", "clean"), ("p", house_note), ("code", "crons"),
        ("h", h[2]), ("ul", mon), ("code", "mon"), ("p", mon_p), ("code", "exporter"), ("code", "shell"),
        ("h", h[3]), ("p", closing),
        ("links", links)]}


LONGRUN["t"]["en"] = _l(
    "Odoo after a year in production: perimeter, housekeeping and monitoring",
    "What keeps an Odoo installation healthy after the go-live: proxy_mode with headers nginx overwrites, closed database manager, external API only for known IPs, a login rate limit, read-only code; regular cleanup of ir_logging, mail_mail and attachments, a review of crons; monitoring of late crons, long transactions and queue_job, metrics without an extra Odoo module, and odoo shell instead of manual SQL.",
    "Six to twelve months after the go-live many Odoo systems get slower and harder to maintain – not because of one bug, but because nobody looks after the perimeter, the growing system tables and the background jobs. These are the checks we run on the servers we maintain.",
    "Short version: `proxy_mode = True` only with nginx overwriting `X-Forwarded-*`; database manager closed, XML-RPC/JSON-RPC only for integration IPs, `limit_req` on the login; Odoo writes only to `data_dir`; monthly look at table sizes, logs and attachments; crons reviewed – but core housekeeping crons stay on; alerts on late crons, long transactions and the job queue.",
    ["Perimeter and network", "Housekeeping", "Monitoring and diagnostics", "Conclusion"],
    ["**`proxy_mode = True`** behind nginx or a load balancer – otherwise Odoo logs the proxy address for every request, and fail2ban, GeoIP and the login brake see only one IP. But it makes Odoo trust `X-Forwarded-For/-Host/-Proto`: nginx must set (overwrite) these headers, otherwise any client can pretend to be any IP.",
     "**Close the dangerous endpoints in nginx.** `/web/database/` (manager, selector, backup, restore, drop) and `/website/info` are never needed publicly; additionally `list_db = False`.",
     "**External API only for known clients.** The web client and the mobile app use `/web/dataset/…`, not `/xmlrpc/` or `/jsonrpc` – closing those does not break the UI. But integrations (telephony, shops, ETL, Excel add-ins) use exactly XML-RPC/JSON-RPC (Odoo 19 also `/json/2/`): allow their IPs instead of blocking blindly. API keys of integrations bypass 2FA – one technical user per integration with minimal rights.",
     "**A rate limit on `/web/login`** with `limit_req`, in addition to Odoo's own login cooldown (`base.login_cooldown_after` / `_duration`) and fail2ban on the Odoo log."],
    "**File system rights.** The Odoo process needs write access only to `data_dir` (filestore and sessions) and its log directory. Core and custom code belong to root or a deploy user and are only readable for `odoo` – then a vulnerability in a module cannot overwrite Python files, and nobody “hot-fixes” code on the server outside git. `odoo.conf` contains passwords: readable for Odoo, not for everyone, not writable.",
    ["**ir_logging.** It is filled by server actions (`log()`), by `log_db` and by some audit modules; Odoo does not clean it. With chatty automations it reaches gigabytes – delete entries older than 30 days by a cron or a scheduled SQL job.",
     "**mail_mail.** Outgoing mails with `auto_delete = false` stay in `mail_mail` after sending. These are not the chatter messages (`mail_message`) – they can be removed after a few weeks.",
     "**Attachments.** When a record is deleted, Odoo deletes its attachments, and the autovacuum (`_gc_file_store`) removes files without a database record from the filestore. Attachments without a record (`res_id = 0`) are not always garbage – website images, report templates and binary fields are stored that way. Look at sizes by model first and delete only what you understand.",
     "**Crons.** Every app brings scheduled actions. Review them: unused integrations, digests, “Publisher: Update Notification” can go. Never switch off “Base: Auto-vacuum internal data” (it cleans old bus messages, old wizard records, the filestore), the mail queue, and the queue_job garbage collector – without them the system silts up. HTTP sessions are cleaned by Odoo itself, not by a cron.",
     "**Large tables.** `mail_message`, `mail_tracking_value`, `bus_bus` and stock/accounting tables grow fastest; after mass deletions run `VACUUM (ANALYZE)`; `VACUUM FULL` only in a maintenance window."],
    "Odoo removes the done jobs of OCA queue_job with its own cron as well – check that these crons are active and run (`lastcall`), especially on copies where all crons were switched off.",
    ["**Late and hanging crons.** `ir_cron` has no persistent lock flag: a running cron holds a row lock only for its transaction; if the worker dies, the lock disappears and the cron runs again at the next `nextcall`. So watch two things: active crons whose `nextcall` is more than 30 minutes in the past (no cron worker, or a cron that blocks the others), and transactions older than 20 minutes in `pg_stat_activity` (a cron or job that never finishes). Recent Odoo versions deactivate crons that fail repeatedly – an unexpectedly inactive cron is also a signal.",
     "**Errors in the log.** Alert on ERROR/CRITICAL lines (Loki/promtail, ELK, Zabbix) – not on every line, but on the rate per 5 minutes, and filter scanner noise (bad HTTP requests to the Odoo port).",
     "**Health checks.** `/web/health` (current versions) or `/web/login` only shows that the HTTP server answers. A check that touches the database (the login page renders from the database) plus the SQL checks below gives the real state.",
     "**odoo shell for diagnostics.** Instead of manual `UPDATE` in PostgreSQL, which bypasses business logic, constraints and the ORM cache, use `odoo-bin shell`: check access rights as a real user, recompute a field, call a method – and roll back."],
    "No extra Odoo module is needed for metrics: `postgres_exporter` with a few custom SQL queries delivers crons, the job queue and table sizes to Prometheus; `node_exporter` the server; the Odoo log goes to Loki. Grafana on top – behind nginx with a password.",
    "None of this is complicated, but it has to be done regularly: once a month table sizes, attachments and crons; permanently alerts on late crons, long transactions, the job queue and errors. We set this up as part of Odoo operations for companies in Germany, Austria and Switzerland.",
    "Links")

LONGRUN["t"]["de"] = _l(
    "Odoo nach einem Jahr im Betrieb: Perimeter, Wartung und Monitoring",
    "Was eine Odoo-Installation nach dem Go-live gesund hält: proxy_mode mit Headern, die nginx überschreibt, geschlossener Datenbankmanager, externe API nur für bekannte IPs, Login-Ratenlimit, schreibgeschützter Code; regelmäßige Bereinigung von ir_logging, mail_mail und Anhängen, Durchsicht der Crons; Überwachung verspäteter Crons, langer Transaktionen und queue_job, Metriken ohne zusätzliches Odoo-Modul und odoo shell statt manuellem SQL.",
    "Sechs bis zwölf Monate nach dem Go-live werden viele Odoo-Systeme langsamer und schwerer zu warten – nicht wegen eines Fehlers, sondern weil sich niemand um Perimeter, wachsende Systemtabellen und Hintergrundjobs kümmert. Das sind die Prüfungen, die wir auf den von uns betreuten Servern machen.",
    "Kurzfassung: `proxy_mode = True` nur, wenn nginx `X-Forwarded-*` überschreibt; Datenbankmanager geschlossen, XML-RPC/JSON-RPC nur für IPs von Schnittstellen, `limit_req` auf dem Login; Odoo schreibt nur in `data_dir`; monatlich Tabellengrößen, Logs und Anhänge ansehen; Crons durchsehen – die Wartungs-Crons des Kerns bleiben an; Alarme bei verspäteten Crons, langen Transaktionen und der Job-Warteschlange.",
    ["Perimeter und Netzwerk", "Regelmäßige Wartung", "Monitoring und Diagnose", "Fazit"],
    ["**`proxy_mode = True`** hinter nginx oder einem Load Balancer – sonst protokolliert Odoo bei jeder Anfrage die Proxy-Adresse, und fail2ban, GeoIP und die Login-Bremse sehen nur eine IP. Aber damit vertraut Odoo `X-Forwarded-For/-Host/-Proto`: nginx muss diese Header setzen (überschreiben), sonst kann jeder Client sich als beliebige IP ausgeben.",
     "**Gefährliche Endpunkte in nginx schließen.** `/web/database/` (Manager, Auswahl, Sicherung, Wiederherstellung, Löschen) und `/website/info` braucht öffentlich niemand; zusätzlich `list_db = False`.",
     "**Externe API nur für bekannte Clients.** Web-Client und mobile App nutzen `/web/dataset/…`, nicht `/xmlrpc/` oder `/jsonrpc` – deren Sperre bricht die Oberfläche nicht. Schnittstellen (Telefonie, Shops, ETL, Excel-Add-ins) nutzen aber genau XML-RPC/JSON-RPC (Odoo 19 auch `/json/2/`): ihre IPs freigeben statt blind sperren. API-Schlüssel von Schnittstellen umgehen 2FA – ein technischer Benutzer je Schnittstelle mit minimalen Rechten.",
     "**Ratenlimit auf `/web/login`** mit `limit_req`, zusätzlich zur Login-Sperre von Odoo selbst (`base.login_cooldown_after` / `_duration`) und fail2ban auf dem Odoo-Log."],
    "**Dateisystemrechte.** Der Odoo-Prozess braucht Schreibrechte nur auf `data_dir` (Filestore und Sitzungen) und sein Log-Verzeichnis. Kern- und eigener Code gehören root oder einem Deploy-Benutzer und sind für `odoo` nur lesbar – dann kann eine Lücke in einem Modul keine Python-Dateien überschreiben, und niemand „repariert“ Code am Server an git vorbei. `odoo.conf` enthält Passwörter: für Odoo lesbar, nicht für alle, nicht beschreibbar.",
    ["**ir_logging.** Gefüllt von Serveraktionen (`log()`), von `log_db` und einigen Audit-Modulen; Odoo räumt sie nicht auf. Mit gesprächigen Automatisierungen erreicht sie Gigabytes – Einträge älter als 30 Tage per Cron oder geplantem SQL-Job löschen.",
     "**mail_mail.** Ausgehende Mails mit `auto_delete = false` bleiben nach dem Versand in `mail_mail`. Das sind nicht die Chatter-Nachrichten (`mail_message`) – sie können nach einigen Wochen weg.",
     "**Anhänge.** Wird ein Datensatz gelöscht, löscht Odoo seine Anhänge, und der Autovacuum (`_gc_file_store`) entfernt Dateien ohne Datenbankeintrag aus dem Filestore. Anhänge ohne Datensatz (`res_id = 0`) sind nicht immer Müll – Website-Bilder, Berichtsvorlagen und Binärfelder werden so gespeichert. Erst die Größen je Modell ansehen und nur löschen, was man versteht.",
     "**Crons.** Jede App bringt geplante Aktionen mit. Durchsehen: ungenutzte Schnittstellen, Digests, „Publisher: Update Notification“ können weg. Nie abschalten: „Base: Auto-vacuum internal data“ (räumt Bus-Daten, alte Wizard-Datensätze, Filestore auf), die Mail-Warteschlange und den Garbage Collector von queue_job – ohne sie verschlammt das System. HTTP-Sitzungen räumt Odoo selbst auf, nicht per Cron.",
     "**Große Tabellen.** `mail_message`, `mail_tracking_value`, `bus_bus` und Lager-/Buchhaltungstabellen wachsen am schnellsten; nach Massenlöschungen `VACUUM (ANALYZE)`; `VACUUM FULL` nur im Wartungsfenster."],
    "Erledigte Jobs von OCA queue_job entfernt Odoo ebenfalls per eigenem Cron – prüfen, ob diese Crons aktiv sind und laufen (`lastcall`), besonders auf Kopien, auf denen alle Crons abgeschaltet wurden.",
    ["**Verspätete und hängende Crons.** `ir_cron` hat kein dauerhaftes Sperr-Flag: ein laufender Cron hält eine Zeilensperre nur für seine Transaktion; stirbt der Worker, verschwindet die Sperre, und der Cron läuft beim nächsten `nextcall` erneut. Also zwei Dinge beobachten: aktive Crons, deren `nextcall` mehr als 30 Minuten zurückliegt (kein Cron-Worker oder ein Cron blockiert die anderen), und Transaktionen älter als 20 Minuten in `pg_stat_activity` (ein Cron oder Job, der nie endet). Neuere Odoo-Versionen deaktivieren wiederholt fehlschlagende Crons – ein unerwartet inaktiver Cron ist ebenfalls ein Signal.",
     "**Fehler im Log.** Alarm auf ERROR/CRITICAL-Zeilen (Loki/promtail, ELK, Zabbix) – nicht auf jede Zeile, sondern auf die Rate je 5 Minuten, und Scanner-Rauschen (fehlerhafte HTTP-Anfragen auf den Odoo-Port) herausfiltern.",
     "**Health-Checks.** `/web/health` (aktuelle Versionen) oder `/web/login` zeigt nur, dass der HTTP-Server antwortet. Eine Prüfung, die die Datenbank berührt (die Login-Seite wird aus der Datenbank gerendert), plus die SQL-Prüfungen unten zeigen den echten Zustand.",
     "**odoo shell für die Diagnose.** Statt manueller `UPDATE` in PostgreSQL, die Geschäftslogik, Constraints und den ORM-Cache umgehen, `odoo-bin shell` nutzen: Zugriffsrechte als echter Benutzer prüfen, ein Feld neu berechnen, eine Methode aufrufen – und zurückrollen."],
    "Für Metriken braucht es kein zusätzliches Odoo-Modul: `postgres_exporter` mit einigen eigenen SQL-Abfragen liefert Crons, Job-Warteschlange und Tabellengrößen an Prometheus, `node_exporter` den Server, das Odoo-Log geht nach Loki. Darüber Grafana – hinter nginx mit Passwort.",
    "Nichts davon ist kompliziert, aber es muss regelmäßig passieren: monatlich Tabellengrößen, Anhänge und Crons; dauerhaft Alarme bei verspäteten Crons, langen Transaktionen, Job-Warteschlange und Fehlern. Wir richten das als Teil des Odoo-Betriebs für Unternehmen in Deutschland, Österreich und der Schweiz ein.",
    "Links")

LONGRUN["t"]["fr"] = _l(
    "Odoo après un an en production : périmètre, maintenance et supervision",
    "Ce qui garde une installation Odoo en bonne santé après la mise en production : proxy_mode avec des en-têtes réécrits par nginx, gestionnaire de bases fermé, API externe seulement pour des IP connues, limite de débit sur la connexion, code en lecture seule ; nettoyage régulier d'ir_logging, mail_mail et des pièces jointes, revue des crons ; supervision des crons en retard, des longues transactions et de queue_job, métriques sans module Odoo supplémentaire, et odoo shell au lieu de SQL manuel.",
    "Six à douze mois après la mise en production, beaucoup de systèmes Odoo deviennent plus lents et plus difficiles à maintenir – non pas à cause d'un bug, mais parce que personne ne s'occupe du périmètre, des tables système qui grossissent et des tâches de fond. Voici les contrôles que nous faisons sur les serveurs que nous exploitons.",
    "En bref : `proxy_mode = True` seulement si nginx réécrit `X-Forwarded-*` ; gestionnaire de bases fermé, XML-RPC/JSON-RPC seulement pour les IP des intégrations, `limit_req` sur la connexion ; Odoo n'écrit que dans `data_dir` ; chaque mois, un œil sur la taille des tables, les journaux et les pièces jointes ; revue des crons – mais les crons de maintenance du noyau restent actifs ; alertes sur les crons en retard, les longues transactions et la file de jobs.",
    ["Périmètre et réseau", "Maintenance régulière", "Supervision et diagnostic", "Conclusion"],
    ["**`proxy_mode = True`** derrière nginx ou un répartiteur de charge – sinon Odoo journalise l'adresse du proxy pour chaque requête, et fail2ban, GeoIP et le frein de connexion ne voient qu'une seule IP. Mais Odoo fait alors confiance à `X-Forwarded-For/-Host/-Proto` : nginx doit définir (réécrire) ces en-têtes, sinon n'importe quel client peut se faire passer pour n'importe quelle IP.",
     "**Fermer les points d'accès dangereux dans nginx.** `/web/database/` (gestionnaire, sélecteur, sauvegarde, restauration, suppression) et `/website/info` ne sont jamais utiles en public ; en plus `list_db = False`.",
     "**API externe seulement pour des clients connus.** Le client web et l'application mobile utilisent `/web/dataset/…`, pas `/xmlrpc/` ni `/jsonrpc` – les fermer ne casse pas l'interface. Mais les intégrations (téléphonie, boutiques, ETL, compléments Excel) utilisent justement XML-RPC/JSON-RPC (Odoo 19 aussi `/json/2/`) : autoriser leurs IP plutôt que bloquer à l'aveugle. Les clés API des intégrations contournent la 2FA – un utilisateur technique par intégration avec des droits minimaux.",
     "**Une limite de débit sur `/web/login`** avec `limit_req`, en plus du frein de connexion d'Odoo (`base.login_cooldown_after` / `_duration`) et de fail2ban sur le journal d'Odoo."],
    "**Droits sur le système de fichiers.** Le processus Odoo n'a besoin d'écrire que dans `data_dir` (filestore et sessions) et son répertoire de journaux. Le code du noyau et le code spécifique appartiennent à root ou à un utilisateur de déploiement et ne sont que lisibles pour `odoo` – ainsi une faille dans un module ne peut pas réécrire des fichiers Python, et personne ne « corrige » le code sur le serveur en dehors de git. `odoo.conf` contient des mots de passe : lisible par Odoo, pas par tous, non modifiable.",
    ["**ir_logging.** Remplie par les actions serveur (`log()`), par `log_db` et certains modules d'audit ; Odoo ne la nettoie pas. Avec des automatisations bavardes, elle atteint des gigaoctets – supprimer les entrées de plus de 30 jours par un cron ou une tâche SQL planifiée.",
     "**mail_mail.** Les e-mails sortants avec `auto_delete = false` restent dans `mail_mail` après l'envoi. Ce ne sont pas les messages du chatter (`mail_message`) – on peut les supprimer après quelques semaines.",
     "**Pièces jointes.** Quand un enregistrement est supprimé, Odoo supprime ses pièces jointes, et l'autovacuum (`_gc_file_store`) retire du filestore les fichiers sans enregistrement en base. Les pièces jointes sans enregistrement (`res_id = 0`) ne sont pas toujours des déchets – images du site, modèles de rapport et champs binaires sont stockés ainsi. Regarder d'abord les tailles par modèle et ne supprimer que ce que l'on comprend.",
     "**Crons.** Chaque application apporte ses actions planifiées. Les passer en revue : intégrations inutilisées, digests, « Publisher: Update Notification » peuvent partir. Ne jamais désactiver « Base: Auto-vacuum internal data » (nettoie les données du bus, les anciens enregistrements d'assistants, le filestore), la file d'e-mails et le ramasse-miettes de queue_job – sans eux le système s'envase. Les sessions HTTP sont nettoyées par Odoo lui-même, pas par un cron.",
     "**Grandes tables.** `mail_message`, `mail_tracking_value`, `bus_bus` et les tables de stock et de comptabilité grossissent le plus vite ; après des suppressions massives, `VACUUM (ANALYZE)` ; `VACUUM FULL` seulement dans une fenêtre de maintenance."],
    "Les jobs terminés d'OCA queue_job sont aussi supprimés par un cron dédié – vérifier que ces crons sont actifs et tournent (`lastcall`), surtout sur des copies où tous les crons ont été désactivés.",
    ["**Crons en retard et bloqués.** `ir_cron` n'a pas de drapeau de verrou persistant : un cron en cours tient un verrou de ligne seulement pendant sa transaction ; si le worker meurt, le verrou disparaît et le cron repart au prochain `nextcall`. Surveiller donc deux choses : les crons actifs dont le `nextcall` est dépassé de plus de 30 minutes (pas de worker cron, ou un cron qui bloque les autres), et les transactions de plus de 20 minutes dans `pg_stat_activity` (un cron ou un job qui ne se termine jamais). Les versions récentes d'Odoo désactivent les crons qui échouent à répétition – un cron inactif de façon inattendue est aussi un signal.",
     "**Erreurs dans le journal.** Alerter sur les lignes ERROR/CRITICAL (Loki/promtail, ELK, Zabbix) – pas sur chaque ligne, mais sur le taux par 5 minutes, en filtrant le bruit des scanners (requêtes HTTP invalides sur le port d'Odoo).",
     "**Contrôles de santé.** `/web/health` (versions actuelles) ou `/web/login` montre seulement que le serveur HTTP répond. Un contrôle qui touche la base (la page de connexion est rendue depuis la base) plus les contrôles SQL ci-dessous donnent l'état réel.",
     "**odoo shell pour le diagnostic.** Au lieu d'`UPDATE` manuels dans PostgreSQL, qui contournent la logique métier, les contraintes et le cache de l'ORM, utiliser `odoo-bin shell` : vérifier les droits d'accès en tant que vrai utilisateur, recalculer un champ, appeler une méthode – puis annuler."],
    "Aucun module Odoo supplémentaire n'est nécessaire pour les métriques : `postgres_exporter` avec quelques requêtes SQL personnalisées fournit à Prometheus les crons, la file de jobs et la taille des tables, `node_exporter` le serveur, et le journal d'Odoo part dans Loki. Grafana par-dessus – derrière nginx avec un mot de passe.",
    "Rien de tout cela n'est compliqué, mais il faut le faire régulièrement : chaque mois la taille des tables, les pièces jointes et les crons ; en permanence des alertes sur les crons en retard, les longues transactions, la file de jobs et les erreurs. Nous mettons cela en place dans le cadre de l'exploitation d'Odoo pour des entreprises en Allemagne, en Autriche et en Suisse.",
    "Liens")

LONGRUN["t"]["el"] = _l(
    "Το Odoo μετά από έναν χρόνο σε παραγωγή: περίμετρος, συντήρηση και παρακολούθηση",
    "Τι κρατά υγιή μια εγκατάσταση Odoo μετά την έναρξη λειτουργίας: proxy_mode με κεφαλίδες που αντικαθιστά ο nginx, κλειστός διαχειριστής βάσεων, εξωτερικό API μόνο για γνωστές IP, όριο ρυθμού στη σύνδεση, κώδικας μόνο για ανάγνωση· τακτικός καθαρισμός των ir_logging, mail_mail και συνημμένων, έλεγχος των cron· παρακολούθηση καθυστερημένων cron, μακρών συναλλαγών και queue_job, μετρικές χωρίς επιπλέον module Odoo, και odoo shell αντί για χειροκίνητο SQL.",
    "Έξι έως δώδεκα μήνες μετά την έναρξη λειτουργίας, πολλά συστήματα Odoo γίνονται πιο αργά και δυσκολότερα στη συντήρηση – όχι λόγω ενός σφάλματος, αλλά επειδή κανείς δεν φροντίζει την περίμετρο, τους πίνακες συστήματος που μεγαλώνουν και τις εργασίες παρασκηνίου. Αυτοί είναι οι έλεγχοι που κάνουμε στους servers που συντηρούμε.",
    "Συνοπτικά: `proxy_mode = True` μόνο αν ο nginx αντικαθιστά τα `X-Forwarded-*`· κλειστός διαχειριστής βάσεων, XML-RPC/JSON-RPC μόνο για IP διασυνδέσεων, `limit_req` στη σύνδεση· το Odoo γράφει μόνο στο `data_dir`· κάθε μήνα ματιά σε μεγέθη πινάκων, logs και συνημμένα· έλεγχος των cron – αλλά τα cron συντήρησης του πυρήνα μένουν ενεργά· ειδοποιήσεις για καθυστερημένα cron, μακριές συναλλαγές και την ουρά εργασιών.",
    ["Περίμετρος και δίκτυο", "Τακτική συντήρηση", "Παρακολούθηση και διάγνωση", "Συμπέρασμα"],
    ["**`proxy_mode = True`** πίσω από nginx ή load balancer – αλλιώς το Odoo καταγράφει τη διεύθυνση του proxy για κάθε αίτημα, και το fail2ban, το GeoIP και το φρένο σύνδεσης βλέπουν μόνο μία IP. Όμως έτσι το Odoo εμπιστεύεται τα `X-Forwarded-For/-Host/-Proto`: ο nginx πρέπει να ορίζει (να αντικαθιστά) αυτές τις κεφαλίδες, αλλιώς κάθε client μπορεί να παριστάνει οποιαδήποτε IP.",
     "**Κλείστε τα επικίνδυνα endpoints στον nginx.** Τα `/web/database/` (διαχειριστής, επιλογή, αντίγραφο, επαναφορά, διαγραφή) και `/website/info` δεν χρειάζονται ποτέ δημόσια· επιπλέον `list_db = False`.",
     "**Εξωτερικό API μόνο για γνωστούς clients.** Ο web client και η mobile app χρησιμοποιούν `/web/dataset/…`, όχι `/xmlrpc/` ή `/jsonrpc` – το κλείσιμό τους δεν χαλά το UI. Όμως οι διασυνδέσεις (τηλεφωνία, καταστήματα, ETL, πρόσθετα Excel) χρησιμοποιούν ακριβώς XML-RPC/JSON-RPC (το Odoo 19 και `/json/2/`): επιτρέψτε τις IP τους αντί να μπλοκάρετε στα τυφλά. Τα κλειδιά API των διασυνδέσεων παρακάμπτουν το 2FA – ένας τεχνικός χρήστης ανά διασύνδεση με ελάχιστα δικαιώματα.",
     "**Όριο ρυθμού στο `/web/login`** με `limit_req`, επιπλέον του φρένου σύνδεσης του ίδιου του Odoo (`base.login_cooldown_after` / `_duration`) και του fail2ban στο log του Odoo."],
    "**Δικαιώματα στο σύστημα αρχείων.** Η διεργασία του Odoo χρειάζεται δικαίωμα εγγραφής μόνο στο `data_dir` (filestore και συνεδρίες) και στον κατάλογο των logs. Ο κώδικας του πυρήνα και ο δικός σας ανήκουν στον root ή σε χρήστη deploy και είναι μόνο αναγνώσιμοι για τον `odoo` – έτσι ένα κενό ασφαλείας σε module δεν μπορεί να ξαναγράψει αρχεία Python, και κανείς δεν «διορθώνει» κώδικα στον server εκτός git. Το `odoo.conf` περιέχει κωδικούς: αναγνώσιμο από το Odoo, όχι από όλους, όχι εγγράψιμο.",
    ["**ir_logging.** Γεμίζει από server actions (`log()`), από το `log_db` και από ορισμένα modules ελέγχου· το Odoo δεν τον καθαρίζει. Με «φλύαρους» αυτοματισμούς φτάνει gigabytes – διαγράφετε εγγραφές παλαιότερες των 30 ημερών με cron ή προγραμματισμένη εργασία SQL.",
     "**mail_mail.** Τα εξερχόμενα e-mail με `auto_delete = false` μένουν στο `mail_mail` μετά την αποστολή. Δεν είναι τα μηνύματα του chatter (`mail_message`) – μπορούν να διαγραφούν μετά από μερικές εβδομάδες.",
     "**Συνημμένα.** Όταν διαγράφεται μια εγγραφή, το Odoo διαγράφει και τα συνημμένα της, και το autovacuum (`_gc_file_store`) αφαιρεί από το filestore αρχεία χωρίς εγγραφή στη βάση. Τα συνημμένα χωρίς εγγραφή (`res_id = 0`) δεν είναι πάντα σκουπίδια – εικόνες του website, πρότυπα αναφορών και δυαδικά πεδία αποθηκεύονται έτσι. Δείτε πρώτα τα μεγέθη ανά μοντέλο και διαγράψτε μόνο ό,τι καταλαβαίνετε.",
     "**Cron.** Κάθε εφαρμογή φέρνει προγραμματισμένες ενέργειες. Ελέγξτε τες: αχρησιμοποίητες διασυνδέσεις, digests, «Publisher: Update Notification» μπορούν να φύγουν. Ποτέ μην απενεργοποιείτε το «Base: Auto-vacuum internal data» (καθαρίζει δεδομένα του bus, παλιές εγγραφές wizards, το filestore), την ουρά αλληλογραφίας και τον garbage collector του queue_job – χωρίς αυτά το σύστημα «λασπώνει». Τις συνεδρίες HTTP τις καθαρίζει το ίδιο το Odoo, όχι κάποιο cron.",
     "**Μεγάλοι πίνακες.** Οι `mail_message`, `mail_tracking_value`, `bus_bus` και οι πίνακες αποθήκης/λογιστικής μεγαλώνουν ταχύτερα· μετά από μαζικές διαγραφές `VACUUM (ANALYZE)`· `VACUUM FULL` μόνο σε παράθυρο συντήρησης."],
    "Τις ολοκληρωμένες εργασίες του OCA queue_job τις αφαιρεί επίσης δικό του cron – ελέγξτε ότι αυτά τα cron είναι ενεργά και τρέχουν (`lastcall`), ιδίως σε αντίγραφα όπου απενεργοποιήθηκαν όλα τα cron.",
    ["**Καθυστερημένα και κολλημένα cron.** Το `ir_cron` δεν έχει μόνιμη σημαία κλειδώματος: ένα cron που τρέχει κρατά κλείδωμα γραμμής μόνο για τη συναλλαγή του· αν πεθάνει ο worker, το κλείδωμα χάνεται και το cron ξανατρέχει στο επόμενο `nextcall`. Παρακολουθήστε λοιπόν δύο πράγματα: ενεργά cron με `nextcall` περισσότερο από 30 λεπτά στο παρελθόν (κανένας cron worker ή ένα cron που μπλοκάρει τα άλλα) και συναλλαγές παλαιότερες των 20 λεπτών στο `pg_stat_activity` (cron ή εργασία που δεν τελειώνει ποτέ). Οι νεότερες εκδόσεις του Odoo απενεργοποιούν cron που αποτυγχάνουν επανειλημμένα – ένα απρόσμενα ανενεργό cron είναι κι αυτό σήμα.",
     "**Σφάλματα στο log.** Ειδοποιήσεις για γραμμές ERROR/CRITICAL (Loki/promtail, ELK, Zabbix) – όχι για κάθε γραμμή, αλλά για τον ρυθμό ανά 5 λεπτά, φιλτράροντας τον θόρυβο των σαρωτών (λανθασμένα αιτήματα HTTP στη θύρα του Odoo).",
     "**Health checks.** Το `/web/health` (τρέχουσες εκδόσεις) ή το `/web/login` δείχνει μόνο ότι ο HTTP server απαντά. Ένας έλεγχος που αγγίζει τη βάση (η σελίδα σύνδεσης αποδίδεται από τη βάση) μαζί με τους ελέγχους SQL παρακάτω δίνει την πραγματική κατάσταση.",
     "**odoo shell για διάγνωση.** Αντί για χειροκίνητα `UPDATE` στο PostgreSQL, που παρακάμπτουν επιχειρησιακή λογική, constraints και την cache του ORM, χρησιμοποιήστε `odoo-bin shell`: ελέγξτε δικαιώματα ως πραγματικός χρήστης, ξαναϋπολογίστε ένα πεδίο, καλέστε μια μέθοδο – και κάντε rollback."],
    "Για μετρικές δεν χρειάζεται επιπλέον module Odoo: το `postgres_exporter` με μερικά δικά σας ερωτήματα SQL δίνει στον Prometheus τα cron, την ουρά εργασιών και τα μεγέθη πινάκων, το `node_exporter` τον server, και το log του Odoo πηγαίνει στο Loki. Από πάνω Grafana – πίσω από nginx με κωδικό.",
    "Τίποτα από αυτά δεν είναι περίπλοκο, αλλά πρέπει να γίνεται τακτικά: κάθε μήνα μεγέθη πινάκων, συνημμένα και cron· μόνιμα ειδοποιήσεις για καθυστερημένα cron, μακριές συναλλαγές, την ουρά εργασιών και σφάλματα. Τα στήνουμε ως μέρος της λειτουργίας του Odoo για επιχειρήσεις στη Γερμανία, την Αυστρία και την Ελβετία.",
    "Σύνδεσμοι")

LONGRUN["t"]["uk"] = _l(
    "Odoo після року в продакшені: периметр, обслуговування і моніторинг",
    "Що тримає інсталяцію Odoo здоровою після запуску. Периметр: proxy_mode із заголовками, які перезаписує nginx, закритий менеджер баз, зовнішнє API лише для відомих IP, ліміт на вхід, код лише для читання. Регулярне очищення ir_logging, mail_mail і вкладень та перегляд кронів. Моніторинг кронів, що запізнюються, довгих транзакцій і queue_job, метрики без додаткового модуля Odoo, odoo shell замість ручного SQL.",
    "Через пів року чи рік після запуску багато систем Odoo стають повільнішими й складнішими в супроводі. Причина не в одному баґу, а в тому, що ніхто не стежить за периметром, системними таблицями, які ростуть, і фоновими задачами. Нижче перевірки, які ми робимо на серверах, що супроводжуємо.",
    "Коротко: `proxy_mode = True` лише тоді, коли nginx перезаписує `X-Forwarded-*`. Менеджер баз закритий, XML-RPC/JSON-RPC лише для IP інтеграцій, `limit_req` на вхід. Odoo пише лише в `data_dir`. Раз на місяць дивимося розміри таблиць, логи й вкладення. Крони переглядаємо, але службові крони ядра лишаються ввімкненими. Налаштовуємо алерти на крони, що запізнюються, довгі транзакції й чергу задач.",
    ["Периметр і мережа", "Регулярне обслуговування", "Моніторинг і діагностика", "Висновок"],
    ["**`proxy_mode = True`** за nginx або балансувальником. Інакше Odoo пише в лог адресу проксі для кожного запиту, а fail2ban, GeoIP і гальмо входу бачать лише одну IP. Але тоді Odoo довіряє `X-Forwarded-For/-Host/-Proto`, тож nginx має виставляти (перезаписувати) ці заголовки. Інакше будь-який клієнт зможе видати себе за будь-яку IP.",
     "**Закрийте небезпечні ендпоінти в nginx.** `/web/database/` (менеджер, вибір бази, бекап, відновлення, видалення) і `/website/info` публічно не потрібні ніколи. Додатково `list_db = False`.",
     "**Зовнішнє API лише для відомих клієнтів.** Веб-клієнт і мобільний застосунок працюють через `/web/dataset/…`, а не `/xmlrpc/` чи `/jsonrpc`, тож закриття цих шляхів інтерфейс не ламає. Але інтеграції (телефонія, магазини, ETL, надбудови Excel) працюють саме через XML-RPC/JSON-RPC (в Odoo 19 ще й `/json/2/`). Тому дозвольте їхні IP, а не блокуйте наосліп. API-ключі інтеграцій обходять 2FA, тож для кожної інтеграції потрібен окремий технічний користувач із мінімальними правами.",
     "**Ліміт на `/web/login`** через `limit_req` — на додачу до гальма входу самого Odoo (`base.login_cooldown_after` / `_duration`) і fail2ban на лозі Odoo."],
    "**Права на файлову систему.** Процесу Odoo потрібен запис лише в `data_dir` (filestore і сесії) та в каталог логів. Код ядра й власний код належать root або користувачу для деплою, а для `odoo` доступні лише на читання. Тоді вразливість у модулі не зможе перезаписати Python-файли, і ніхто не «підправить» код на сервері в обхід git. `odoo.conf` містить паролі: він має читатися процесом Odoo, але не всіма, і бути недоступним для запису.",
    ["**ir_logging.** Таблицю наповнюють серверні дії (`log()`), `log_db` і деякі модулі аудиту, а Odoo її не очищає. З «балакучими» автоматизаціями вона доростає до гігабайтів. Видаляйте записи старші за 30 днів кроном або запланованим SQL-завданням.",
     "**mail_mail.** Вихідні листи з `auto_delete = false` лишаються в `mail_mail` після відправлення. Це не повідомлення чатера (`mail_message`), їх можна видаляти через кілька тижнів.",
     "**Вкладення.** Коли запис видаляють, Odoo видаляє і його вкладення, а autovacuum (`_gc_file_store`) прибирає з filestore файли без запису в базі. Вкладення без запису (`res_id = 0`) не завжди сміття: так зберігаються зображення сайту, шаблони звітів і бінарні поля. Спершу подивіться розміри по моделях і видаляйте лише те, що розумієте.",
     "**Крони.** Кожен застосунок додає свої заплановані дії. Перегляньте їх: невикористані інтеграції, дайджести, «Publisher: Update Notification» можна вимкнути. Ніколи не вимикайте «Base: Auto-vacuum internal data» (він чистить дані шини, старі записи майстрів, filestore), чергу пошти та збирач сміття queue_job. Без них система замулюється. HTTP-сесії Odoo чистить сам, а не кроном.",
     "**Великі таблиці.** Найшвидше ростуть `mail_message`, `mail_tracking_value`, `bus_bus`, а також складські й бухгалтерські таблиці. Після масових видалень запускайте `VACUUM (ANALYZE)`, а `VACUUM FULL` — лише у вікні обслуговування."],
    "Виконані задачі OCA queue_job теж прибирає окремий крон. Перевірте, що ці крони активні й запускаються (`lastcall`), особливо на копіях, де вимкнули всі крони.",
    ["**Крони, що запізнюються чи зависли.** В `ir_cron` немає постійного прапорця блокування: крон, що виконується, тримає блокування рядка лише на час своєї транзакції. Якщо воркер помре, блокування зникне, і крон запуститься знову на наступному `nextcall`. Тож стежте за двома речами. Перша: активні крони, у яких `nextcall` у минулому більше ніж на 30 хвилин (немає cron-воркера або один крон блокує інші). Друга: транзакції старші за 20 хвилин у `pg_stat_activity` (крон чи задача, яка ніколи не завершується). Нові версії Odoo вимикають крони, що постійно падають, тож несподівано неактивний крон — теж сигнал.",
     "**Помилки в лозі.** Алерти на рядки ERROR/CRITICAL (Loki/promtail, ELK, Zabbix) варто ставити не на кожен рядок, а на частоту за 5 хвилин. Шум сканерів (биті HTTP-запити на порт Odoo) треба відфільтрувати.",
     "**Health-checks.** `/web/health` (у поточних версіях) чи `/web/login` показує лише, що HTTP-сервер відповідає. Реальний стан дає перевірка, що звертається до бази (сторінка входу рендериться з бази), разом із SQL-перевірками нижче.",
     "**odoo shell для діагностики.** Ручні `UPDATE` у PostgreSQL обходять бізнес-логіку, обмеження й кеш ORM. Замість них використовуйте `odoo-bin shell`: перевірте права під реальним користувачем, перерахуйте поле, викличте метод, а потім зробіть rollback."],
    "Для метрик не потрібен додатковий модуль Odoo. `postgres_exporter` з кількома власними SQL-запитами віддає в Prometheus крони, чергу задач і розміри таблиць, `node_exporter` — стан сервера, а лог Odoo йде в Loki. Зверху Grafana за nginx із паролем.",
    "Нічого складного тут немає, але робити це треба регулярно. Раз на місяць — розміри таблиць, вкладення й крони. Постійно — алерти на крони, що запізнюються, довгі транзакції, чергу задач і помилки. Ми налаштовуємо це в межах супроводу Odoo для компаній у Німеччині, Австрії та Швейцарії.",
    "Посилання")

LONGRUN["t"]["ru"] = _l(
    "Odoo после года в продакшене: периметр, обслуживание и мониторинг",
    "Что держит инсталляцию Odoo здоровой после запуска. Периметр: proxy_mode с заголовками, которые перезаписывает nginx, закрытый менеджер баз, внешнее API только для известных IP, лимит на вход, код только для чтения. Регулярная очистка ir_logging, mail_mail и вложений и ревизия кронов. Мониторинг опаздывающих кронов, долгих транзакций и queue_job, метрики без дополнительного модуля Odoo, odoo shell вместо ручного SQL.",
    "Через полгода-год после запуска многие системы Odoo становятся медленнее и сложнее в сопровождении. Причина не в одном баге, а в том, что никто не следит за периметром, растущими системными таблицами и фоновыми задачами. Ниже проверки, которые мы делаем на серверах, которые сопровождаем.",
    "Коротко: `proxy_mode = True` только тогда, когда nginx перезаписывает `X-Forwarded-*`. Менеджер баз закрыт, XML-RPC/JSON-RPC только для IP интеграций, `limit_req` на вход. Odoo пишет только в `data_dir`. Раз в месяц смотрим размеры таблиц, логи и вложения. Кроны пересматриваем, но служебные кроны ядра остаются включёнными. Настраиваем алерты на опаздывающие кроны, долгие транзакции и очередь задач.",
    ["Периметр и сеть", "Регламентное обслуживание", "Мониторинг и диагностика", "Вывод"],
    ["**`proxy_mode = True`** за nginx или балансировщиком. Иначе Odoo пишет в лог адрес прокси для каждого запроса, а fail2ban, GeoIP и тормоз входа видят только один IP. Но тогда Odoo доверяет `X-Forwarded-For/-Host/-Proto`, поэтому nginx должен выставлять (перезаписывать) эти заголовки. Иначе любой клиент сможет выдать себя за любой IP.",
     "**Закройте опасные эндпоинты в nginx.** `/web/database/` (менеджер, выбор базы, бэкап, восстановление, удаление) и `/website/info` публично не нужны никогда. Дополнительно `list_db = False`.",
     "**Внешнее API только для известных клиентов.** Веб-клиент и мобильное приложение работают через `/web/dataset/…`, а не `/xmlrpc/` или `/jsonrpc`, так что закрытие этих путей интерфейс не ломает. Но интеграции (телефония, магазины, ETL, надстройки Excel) работают именно через XML-RPC/JSON-RPC (в Odoo 19 ещё и `/json/2/`). Поэтому разрешите их IP, а не блокируйте вслепую. API-ключи интеграций обходят 2FA, так что для каждой интеграции нужен отдельный технический пользователь с минимальными правами.",
     "**Лимит на `/web/login`** через `limit_req` — в дополнение к тормозу входа самого Odoo (`base.login_cooldown_after` / `_duration`) и fail2ban на логе Odoo."],
    "**Права на файловую систему.** Процессу Odoo нужна запись только в `data_dir` (filestore и сессии) и в каталог логов. Код ядра и свой код принадлежат root или пользователю для деплоя, а для `odoo` доступны только на чтение. Тогда уязвимость в модуле не сможет перезаписать Python-файлы, и никто не «подправит» код на сервере в обход git. `odoo.conf` содержит пароли: он должен читаться процессом Odoo, но не всеми, и быть недоступным для записи.",
    ["**ir_logging.** Таблицу заполняют серверные действия (`log()`), `log_db` и некоторые модули аудита, а Odoo её не чистит. С «болтливыми» автоматизациями она дорастает до гигабайтов. Удаляйте записи старше 30 дней кроном или запланированным SQL-заданием.",
     "**mail_mail.** Исходящие письма с `auto_delete = false` остаются в `mail_mail` после отправки. Это не сообщения чаттера (`mail_message`), их можно удалять через несколько недель.",
     "**Вложения.** Когда запись удаляют, Odoo удаляет и её вложения, а autovacuum (`_gc_file_store`) убирает из filestore файлы без записи в базе. Вложения без записи (`res_id = 0`) не всегда мусор: так хранятся картинки сайта, шаблоны отчётов и бинарные поля. Сначала посмотрите размеры по моделям и удаляйте только то, что понимаете.",
     "**Кроны.** Каждое приложение добавляет свои запланированные действия. Пересмотрите их: неиспользуемые интеграции, дайджесты, «Publisher: Update Notification» можно выключить. Никогда не выключайте «Base: Auto-vacuum internal data» (он чистит данные шины, старые записи мастеров, filestore), очередь почты и сборщик мусора queue_job. Без них система заиливается. HTTP-сессии Odoo чистит сам, а не кроном.",
     "**Большие таблицы.** Быстрее всего растут `mail_message`, `mail_tracking_value`, `bus_bus`, а также складские и бухгалтерские таблицы. После массовых удалений запускайте `VACUUM (ANALYZE)`, а `VACUUM FULL` — только в окне обслуживания."],
    "Выполненные задачи OCA queue_job тоже удаляет отдельный крон. Проверьте, что эти кроны активны и запускаются (`lastcall`), особенно на копиях, где выключили все кроны.",
    ["**Опаздывающие и зависшие кроны.** В `ir_cron` нет постоянного флага блокировки: выполняющийся крон держит блокировку строки только на время своей транзакции. Если воркер умрёт, блокировка исчезнет, и крон запустится снова на следующем `nextcall`. Поэтому следите за двумя вещами. Первое: активные кроны, у которых `nextcall` в прошлом больше чем на 30 минут (нет cron-воркера или один крон блокирует другие). Второе: транзакции старше 20 минут в `pg_stat_activity` (крон или задача, которая никогда не заканчивается). Новые версии Odoo выключают кроны, которые постоянно падают, так что неожиданно неактивный крон — тоже сигнал.",
     "**Ошибки в логе.** Алерты на строки ERROR/CRITICAL (Loki/promtail, ELK, Zabbix) стоит ставить не на каждую строку, а на частоту за 5 минут. Шум сканеров (битые HTTP-запросы на порт Odoo) нужно отфильтровать.",
     "**Health-checks.** `/web/health` (в текущих версиях) или `/web/login` показывает только, что HTTP-сервер отвечает. Реальное состояние даёт проверка, которая обращается к базе (страница входа рендерится из базы), вместе с SQL-проверками ниже.",
     "**odoo shell для диагностики.** Ручные `UPDATE` в PostgreSQL обходят бизнес-логику, ограничения и кэш ORM. Вместо них используйте `odoo-bin shell`: проверьте права под реальным пользователем, пересчитайте поле, вызовите метод, а потом сделайте rollback."],
    "Для метрик не нужен дополнительный модуль Odoo. `postgres_exporter` с несколькими своими SQL-запросами отдаёт в Prometheus кроны, очередь задач и размеры таблиц, `node_exporter` — состояние сервера, а лог Odoo уходит в Loki. Сверху Grafana за nginx с паролем.",
    "Ничего сложного здесь нет, но делать это нужно регулярно. Раз в месяц — размеры таблиц, вложения и кроны. Постоянно — алерты на опаздывающие кроны, долгие транзакции, очередь задач и ошибки. Мы настраиваем это в рамках сопровождения Odoo для компаний в Германии, Австрии и Швейцарии.",
    "Ссылки")
