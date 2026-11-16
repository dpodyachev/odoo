# Статья 12: Odoo 18/19 + PostgreSQL read replica (db_replica_host) – как работает и почему бывает медленнее. Все 6 языков.

REPLICA = {
    "slug": "odoo-19-postgresql-read-replica",
    "date": "2026-11-15",
    "tags": ["Odoo 19", "Odoo 18", "PostgreSQL", "Replica", "Performance"],
    "code": {
        "conf": ("etc/odoo.conf · Odoo 18 / 19", """[options]
db_host = 10.0.0.10            ; primary – all writes
db_replica_host = 10.0.0.11    ; hot standby – read-only requests
db_replica_port = 5432
; user, password and database name are the same as on the primary

; Odoo 19: simulate a replica on the same server (no network) – for comparison
; dev_mode = replica"""),
        "flow": ("text · request flow (odoo/http.py, 18.0 / 19.0)", """request ──► read-only cursor (replica): check registry, match route
              │
              ├─ route readonly=True  /  auth='none'  /  call_kw on @api.readonly method
              │        └─► served on the REPLICA
              │              └─ tries to write? ReadOnlySqlTransaction
              │                   └─► "retrying with a read/write cursor" → whole request again on PRIMARY
              │
              └─ everything else (save, create, buttons, onchange, most controllers)
                       └─► close replica cursor, open cursor on PRIMARY, serve there

replica down → "Failed to open a readonly cursor, falling back to read-write cursor for 20min" """),
        "measure": ("bash · measure instead of guessing", """# 1) network: round trip from the Odoo host to primary and replica
psql -h 10.0.0.10 -U odoo -d mydb -c '\\timing on' -c 'select 1' -c 'select 1'
psql -h 10.0.0.11 -U odoo -d mydb -c '\\timing on' -c 'select 1' -c 'select 1'

# 2) read-only routes that write anyway (each one = request executed twice)
grep -c "retrying with a read/write cursor" /var/log/odoo/odoo.log

# 3) replication lag (on the replica) and status (on the primary)
psql -h 10.0.0.11 -c "SELECT now() - pg_last_xact_replay_timestamp() AS lag;"
psql -h 10.0.0.10 -c "SELECT client_addr, state, replay_lag FROM pg_stat_replication;"

# 4) same scenario three times: no replica / dev_mode=replica / real replica
#    (Locust or the browser's network tab) – compare the times"""),
        "pg": ("postgresql · streaming replication (minimal)", """# primary – postgresql.conf
wal_level = replica
max_wal_senders = 10
# primary – pg_hba.conf
host  replication  replicator  10.0.0.11/32  scram-sha-256
# primary – SQL
CREATE ROLE replicator WITH REPLICATION LOGIN PASSWORD '...';

# replica – empty data directory, then:
pg_basebackup -h 10.0.0.10 -U replicator -D /var/lib/postgresql/16/main -R -X stream -P
# replica – postgresql.conf
hot_standby = on
hot_standby_feedback = on          # fewer "conflict with recovery" cancellations
max_standby_streaming_delay = 30s"""),
    },
    "links": [
        ("This article on Medium (English)", "https://medium.com/@dpodiatschev/replicas-in-odoo-19-it-can-slow-system-dfb20db4b959"),
        ("Odoo 19 source: odoo/http.py (_serve_db)", "https://github.com/odoo/odoo/blob/19.0/odoo/http.py"),
        ("Odoo 19 source: odoo/tools/config.py (db_replica_*)", "https://github.com/odoo/odoo/blob/19.0/odoo/tools/config.py"),
        ("PostgreSQL: Hot Standby", "https://www.postgresql.org/docs/current/hot-standby.html"),
        ("PostgreSQL: pg_basebackup", "https://www.postgresql.org/docs/current/app-pgbasebackup.html"),
        ("Odoo replica skill for AI agents (Markdown)", "https://2027.pp.ua/skill_odoo_replica.md"),
        ("Blog: Odoo with docker compose, extra-addons and nginx", "@blog:odoo-docker-compose-extra-addons-nginx"),
        ("Blog: free hosting, database and filestore for Odoo 17", "@blog:odoo-17-free-hosting-database-filestore"),
    ],
    "t": {},
}

REPLICA["t"]["en"] = {
    "title": "Odoo 19 with a PostgreSQL read replica: write to the primary, read from the replica – and why it can get slower",
    "summary": "Since Odoo 18, two lines in odoo.conf send read-only requests to a replica. How Odoo decides per request (from the source), why my tests were slower, how to measure it and when it pays off.",
    "body": [
        ("p", "Since **Odoo 18** (and refined in **19**) Odoo can split the load: writes go to the PostgreSQL **primary**, read-only requests to a **read replica**. It is two lines in `odoo.conf`. In my experiments Odoo became **slower**, not faster – so I read the source to understand why."),
        ("note", "Short version: every request starts on the replica; everything that writes (save, buttons, onchange) then switches to the primary. With network latency to the replica each click pays twice. A replica helps only for read-heavy load with the replica in the same LAN (< 1 ms)."),
        ("h", "Enabling it"),
        ("code", "conf"),
        ("ul", [
            "Odoo 17 and older: no replica support.",
            "Odoo 18: an **empty** `db_replica_host =` means a read-only connection to the same server via the Unix socket (for testing).",
            "Odoo 19: that was replaced by `dev_mode = replica` (`--dev=replica`); Odoo 19 also reads `PGHOST_REPLICA` / `PGPORT_REPLICA` from the environment.",
        ]),
        ("h", "What goes where – straight from the source"),
        ("code", "flow"),
        ("ul", [
            "A route is read-only if it says `readonly=True` (or a function decides per request). Routes with `auth='none'` are read-only by default, all others read/write.",
            "`/web/dataset/call_kw` and `call_button` use the replica **only** when the called method is decorated `@api.readonly` – `search`, `search_read`, `search_count`, `read`, `name_search` and the web client's read methods.",
            "Crons, module updates (`-u`) and the shell always use the primary.",
            "Each worker gets **two** connection pools (read-only and read/write), each up to `db_maxconn`.",
        ]),
        ("h", "Why it can be slower"),
        ("ul", [
            "**Network latency.** Odoo sends dozens to hundreds of small queries per request. 2–5 ms extra per query to a replica in another data centre or over VPN add up to seconds.",
            "**Double start for writes.** Every write request first opens a cursor on the replica, checks the registry, then closes it and starts again on the primary.",
            "**Retries.** A custom or OCA route marked read-only that writes anyway fails with `ReadOnlySqlTransaction` and runs **completely again** on the primary.",
            "**Weaker replica / cold cache.** If the replica has less RAM or its cache is cold, the same query is slower than on the primary.",
            "**Connections.** Two pools per worker can hit PostgreSQL `max_connections`.",
            "**Replication lag** does not slow things down, but right after saving a list may still show old values – confusing for users.",
        ]),
        ("h", "Measure instead of guessing"),
        ("code", "measure"),
        ("p", "The trick is step 4: if `dev_mode = replica` on one server is as fast as no replica, Odoo's own overhead is small and the slowdown comes from the **network or the replica's hardware**. That was exactly the open question in my tests."),
        ("h", "The PostgreSQL side"),
        ("code", "pg"),
        ("p", "Use physical streaming replication (hot standby). `synchronous_commit = remote_apply` would guarantee that a read sees the previous write, but makes every write wait for the replica – rarely worth it for Odoo. And the replica is valuable anyway as a **failover** (`SELECT pg_promote();`), even without `db_replica_host`."),
        ("h", "When it pays off"),
        ("table", [
            ["Situation", "Replica for reads?"],
            ["Website / eCommerce with many visitors, portals, dashboards, reports, API reads; primary at its limit", "**yes** – if the replica is in the same LAN"],
            ["Small or medium instance (tens of users)", "no – tune the primary first: indexes, workers, PostgreSQL memory"],
            ["Write-heavy: POS, stock, imports, manufacturing", "rarely – writes go to the primary anyway"],
            ["Replica in another region / over VPN", "no – latency eats the gain"],
            ["High availability", "**yes as standby** – with or without `db_replica_host`"],
        ]),
        ("h", "For your own modules"),
        ("ul", [
            "Mark controllers that only read with `readonly=True`; methods called via RPC that only read with `@api.readonly` – never methods that write, send mail or update “last seen” fields.",
            "After a deployment watch the log for `retrying with a read/write cursor` – each line names a route that should not be read-only.",
        ]),
        ("links", "Links"),
    ],
}

REPLICA["t"]["de"] = {
    "title": "Odoo 19 mit PostgreSQL-Read-Replica: schreiben auf dem Primary, lesen von der Replica – und warum es langsamer werden kann",
    "summary": "Seit Odoo 18 schicken zwei Zeilen in der odoo.conf lesende Anfragen an eine Replica. Wie Odoo pro Anfrage entscheidet (aus dem Quellcode), warum meine Tests langsamer waren, wie man misst und wann es sich lohnt.",
    "body": [
        ("p", "Seit **Odoo 18** (verfeinert in **19**) kann Odoo die Last aufteilen: Schreibzugriffe gehen an den PostgreSQL-**Primary**, rein lesende Anfragen an eine **Read-Replica**. Das sind zwei Zeilen in der `odoo.conf`. In meinen Versuchen wurde Odoo damit **langsamer** statt schneller – also habe ich im Quellcode nachgesehen, warum."),
        ("note", "Kurzfassung: Jede Anfrage beginnt auf der Replica; alles, was schreibt (Speichern, Buttons, Onchange), wechselt danach zum Primary. Mit Netzwerklatenz zur Replica zahlt jeder Klick doppelt. Eine Replica hilft nur bei leselastiger Last und wenn sie im selben LAN steht (< 1 ms)."),
        ("h", "Einschalten"),
        ("code", "conf"),
        ("ul", [
            "Odoo 17 und älter: keine Replica-Unterstützung.",
            "Odoo 18: ein **leeres** `db_replica_host =` bedeutet eine Nur-Lese-Verbindung zum selben Server über den Unix-Socket (zum Testen).",
            "Odoo 19: dafür gibt es jetzt `dev_mode = replica` (`--dev=replica`); außerdem liest Odoo 19 `PGHOST_REPLICA` / `PGPORT_REPLICA` aus der Umgebung.",
        ]),
        ("h", "Was wohin geht – direkt aus dem Quellcode"),
        ("code", "flow"),
        ("ul", [
            "Eine Route ist lesend, wenn sie `readonly=True` angibt (oder eine Funktion pro Anfrage entscheidet). Routen mit `auth='none'` sind standardmäßig lesend, alle anderen schreibend.",
            "`/web/dataset/call_kw` und `call_button` nutzen die Replica **nur**, wenn die aufgerufene Methode mit `@api.readonly` markiert ist – `search`, `search_read`, `search_count`, `read`, `name_search` und die Lesemethoden des Web-Clients.",
            "Cron-Jobs, Modul-Updates (`-u`) und die Shell nutzen immer den Primary.",
            "Jeder Worker bekommt **zwei** Verbindungspools (lesend und schreibend), jeweils bis `db_maxconn`.",
        ]),
        ("h", "Warum es langsamer werden kann"),
        ("ul", [
            "**Netzwerklatenz.** Odoo schickt pro Anfrage Dutzende bis Hunderte kleiner Abfragen. 2–5 ms extra pro Abfrage zu einer Replica in einem anderen Rechenzentrum oder über VPN summieren sich zu Sekunden.",
            "**Doppelter Start beim Schreiben.** Jede schreibende Anfrage öffnet zuerst einen Cursor auf der Replica, prüft die Registry, schließt ihn und beginnt auf dem Primary von vorn.",
            "**Wiederholungen.** Eine eigene oder OCA-Route, die als lesend markiert ist, aber doch schreibt, scheitert mit `ReadOnlySqlTransaction` und läuft **komplett noch einmal** auf dem Primary.",
            "**Schwächere Replica / kalter Cache.** Hat die Replica weniger RAM oder ist ihr Cache kalt, ist dieselbe Abfrage langsamer als auf dem Primary.",
            "**Verbindungen.** Zwei Pools pro Worker können `max_connections` von PostgreSQL erreichen.",
            "**Replikationsverzögerung** bremst nicht, aber direkt nach dem Speichern kann eine Liste noch alte Werte zeigen – verwirrend für Anwender.",
        ]),
        ("h", "Messen statt raten"),
        ("code", "measure"),
        ("p", "Der Trick ist Schritt 4: Ist `dev_mode = replica` auf einem Server genauso schnell wie ohne Replica, ist der Eigenaufwand von Odoo gering, und die Bremse liegt im **Netzwerk oder in der Hardware der Replica**. Genau das war in meinen Tests die offene Frage."),
        ("h", "Die PostgreSQL-Seite"),
        ("code", "pg"),
        ("p", "Physische Streaming-Replikation (Hot Standby) verwenden. `synchronous_commit = remote_apply` würde garantieren, dass ein Lesezugriff den vorherigen Schreibzugriff sieht, lässt aber jeden Schreibzugriff auf die Replica warten – für Odoo selten sinnvoll. Und als **Failover** ist die Replica ohnehin wertvoll (`SELECT pg_promote();`), auch ohne `db_replica_host`."),
        ("h", "Wann es sich lohnt"),
        ("table", [
            ["Situation", "Replica zum Lesen?"],
            ["Website / Shop mit vielen Besuchern, Portale, Dashboards, Berichte, API-Lesezugriffe; Primary am Limit", "**ja** – wenn die Replica im selben LAN steht"],
            ["Kleine oder mittlere Instanz (Dutzende Anwender)", "nein – zuerst den Primary optimieren: Indizes, Worker, PostgreSQL-Speicher"],
            ["Schreiblastig: Kasse, Lager, Importe, Fertigung", "selten – Schreibzugriffe gehen ohnehin an den Primary"],
            ["Replica in anderer Region / über VPN", "nein – die Latenz frisst den Gewinn"],
            ["Hochverfügbarkeit", "**ja, als Standby** – mit oder ohne `db_replica_host`"],
        ]),
        ("h", "Für eigene Module"),
        ("ul", [
            "Controller, die nur lesen, mit `readonly=True` markieren; per RPC aufgerufene Methoden, die nur lesen, mit `@api.readonly` – nie Methoden, die schreiben, Mails senden oder „zuletzt gesehen“-Felder aktualisieren.",
            "Nach einem Deployment im Log auf `retrying with a read/write cursor` achten – jede Zeile nennt eine Route, die nicht lesend sein sollte.",
        ]),
        ("links", "Links"),
    ],
}

REPLICA["t"]["fr"] = {
    "title": "Odoo 19 avec une réplique PostgreSQL en lecture : écrire sur le primaire, lire sur la réplique – et pourquoi cela peut ralentir",
    "summary": "Depuis Odoo 18, deux lignes dans odoo.conf envoient les requêtes en lecture seule vers une réplique. Comment Odoo décide pour chaque requête (d'après le code source), pourquoi mes tests étaient plus lents, comment mesurer et quand cela vaut la peine.",
    "body": [
        ("p", "Depuis **Odoo 18** (affiné en **19**), Odoo peut répartir la charge : les écritures vont au **primaire** PostgreSQL, les requêtes en lecture seule à une **réplique**. Deux lignes dans `odoo.conf`. Dans mes essais, Odoo est devenu **plus lent** et non plus rapide – j'ai donc lu le code source pour comprendre pourquoi."),
        ("note", "En bref : chaque requête commence sur la réplique ; tout ce qui écrit (enregistrer, boutons, onchange) bascule ensuite vers le primaire. Avec de la latence réseau vers la réplique, chaque clic paie deux fois. Une réplique n'aide que pour une charge majoritairement en lecture, avec la réplique dans le même LAN (< 1 ms)."),
        ("h", "Activation"),
        ("code", "conf"),
        ("ul", [
            "Odoo 17 et antérieur : pas de prise en charge des répliques.",
            "Odoo 18 : un `db_replica_host =` **vide** signifie une connexion en lecture seule au même serveur via le socket Unix (pour tester).",
            "Odoo 19 : remplacé par `dev_mode = replica` (`--dev=replica`) ; Odoo 19 lit aussi `PGHOST_REPLICA` / `PGPORT_REPLICA` depuis l'environnement.",
        ]),
        ("h", "Qui va où – directement depuis le code source"),
        ("code", "flow"),
        ("ul", [
            "Une route est en lecture seule si elle indique `readonly=True` (ou si une fonction décide par requête). Les routes `auth='none'` sont en lecture seule par défaut, toutes les autres en lecture/écriture.",
            "`/web/dataset/call_kw` et `call_button` utilisent la réplique **uniquement** si la méthode appelée est décorée `@api.readonly` – `search`, `search_read`, `search_count`, `read`, `name_search` et les méthodes de lecture du client web.",
            "Les crons, les mises à jour de modules (`-u`) et le shell utilisent toujours le primaire.",
            "Chaque worker dispose de **deux** pools de connexions (lecture seule et lecture/écriture), chacun jusqu'à `db_maxconn`.",
        ]),
        ("h", "Pourquoi cela peut ralentir"),
        ("ul", [
            "**Latence réseau.** Odoo envoie des dizaines à des centaines de petites requêtes SQL par requête HTTP. 2–5 ms de plus par requête vers une réplique dans un autre centre de données ou via VPN font des secondes.",
            "**Double démarrage pour les écritures.** Chaque requête d'écriture ouvre d'abord un curseur sur la réplique, vérifie le registre, le ferme et recommence sur le primaire.",
            "**Relances.** Une route maison ou OCA marquée en lecture seule qui écrit quand même échoue avec `ReadOnlySqlTransaction` et s'exécute **entièrement une seconde fois** sur le primaire.",
            "**Réplique plus faible / cache froid.** Avec moins de RAM ou un cache froid, la même requête est plus lente que sur le primaire.",
            "**Connexions.** Deux pools par worker peuvent atteindre `max_connections` de PostgreSQL.",
            "**Le retard de réplication** ne ralentit pas, mais juste après l'enregistrement une liste peut encore afficher les anciennes valeurs – déroutant pour les utilisateurs.",
        ]),
        ("h", "Mesurer au lieu de deviner"),
        ("code", "measure"),
        ("p", "L'astuce est l'étape 4 : si `dev_mode = replica` sur un seul serveur est aussi rapide que sans réplique, le surcoût propre à Odoo est faible et le frein vient du **réseau ou du matériel de la réplique**. C'était justement la question ouverte de mes tests."),
        ("h", "Côté PostgreSQL"),
        ("code", "pg"),
        ("p", "Utiliser la réplication physique en streaming (hot standby). `synchronous_commit = remote_apply` garantirait qu'une lecture voit l'écriture précédente, mais chaque écriture attendrait la réplique – rarement utile pour Odoo. Et la réplique reste précieuse comme **bascule** (`SELECT pg_promote();`), même sans `db_replica_host`."),
        ("h", "Quand cela vaut la peine"),
        ("table", [
            ["Situation", "Réplique pour la lecture ?"],
            ["Site web / boutique très visités, portails, tableaux de bord, rapports, lectures API ; primaire saturé", "**oui** – si la réplique est dans le même LAN"],
            ["Instance petite ou moyenne (quelques dizaines d'utilisateurs)", "non – optimiser d'abord le primaire : index, workers, mémoire PostgreSQL"],
            ["Beaucoup d'écritures : caisse, stock, imports, fabrication", "rarement – les écritures vont de toute façon au primaire"],
            ["Réplique dans une autre région / via VPN", "non – la latence mange le gain"],
            ["Haute disponibilité", "**oui, en standby** – avec ou sans `db_replica_host`"],
        ]),
        ("h", "Pour vos propres modules"),
        ("ul", [
            "Marquer les contrôleurs qui ne font que lire avec `readonly=True` ; les méthodes appelées en RPC qui ne font que lire avec `@api.readonly` – jamais des méthodes qui écrivent, envoient des e-mails ou mettent à jour des champs « vu pour la dernière fois ».",
            "Après un déploiement, surveiller `retrying with a read/write cursor` dans le journal – chaque ligne désigne une route qui ne devrait pas être en lecture seule.",
        ]),
        ("links", "Liens"),
    ],
}

REPLICA["t"]["el"] = {
    "title": "Odoo 19 με PostgreSQL read replica: εγγραφή στον primary, ανάγνωση από το replica – και γιατί μπορεί να γίνει πιο αργό",
    "summary": "Από το Odoo 18, δύο γραμμές στο odoo.conf στέλνουν τα αιτήματα μόνο-ανάγνωσης σε replica. Πώς αποφασίζει το Odoo ανά αίτημα (από τον κώδικα), γιατί οι δοκιμές μου ήταν πιο αργές, πώς να μετρήσετε και πότε αξίζει.",
    "body": [
        ("p", "Από το **Odoo 18** (βελτιωμένο στο **19**) το Odoo μπορεί να μοιράσει το φορτίο: οι εγγραφές πηγαίνουν στον **primary** της PostgreSQL, τα αιτήματα μόνο-ανάγνωσης σε ένα **read replica**. Δύο γραμμές στο `odoo.conf`. Στα πειράματά μου το Odoo έγινε **πιο αργό** αντί για πιο γρήγορο – γι' αυτό διάβασα τον κώδικα για να καταλάβω γιατί."),
        ("note", "Συνοπτικά: κάθε αίτημα ξεκινά στο replica· ό,τι γράφει (αποθήκευση, κουμπιά, onchange) μετά μεταφέρεται στον primary. Με καθυστέρηση δικτύου προς το replica κάθε κλικ πληρώνει διπλά. Το replica βοηθά μόνο σε φορτίο κυρίως ανάγνωσης και όταν βρίσκεται στο ίδιο LAN (< 1 ms)."),
        ("h", "Ενεργοποίηση"),
        ("code", "conf"),
        ("ul", [
            "Odoo 17 και παλαιότερα: καμία υποστήριξη replica.",
            "Odoo 18: ένα **κενό** `db_replica_host =` σημαίνει σύνδεση μόνο-ανάγνωσης στον ίδιο server μέσω Unix socket (για δοκιμές).",
            "Odoo 19: αντικαταστάθηκε από το `dev_mode = replica` (`--dev=replica`)· το Odoo 19 διαβάζει επίσης `PGHOST_REPLICA` / `PGPORT_REPLICA` από το περιβάλλον.",
        ]),
        ("h", "Τι πάει πού – κατευθείαν από τον κώδικα"),
        ("code", "flow"),
        ("ul", [
            "Μια διαδρομή είναι μόνο-ανάγνωσης αν δηλώνει `readonly=True` (ή αν μια συνάρτηση αποφασίζει ανά αίτημα). Οι διαδρομές με `auth='none'` είναι εξ ορισμού μόνο-ανάγνωσης, όλες οι άλλες ανάγνωσης/εγγραφής.",
            "Τα `/web/dataset/call_kw` και `call_button` χρησιμοποιούν το replica **μόνο** όταν η καλούμενη μέθοδος έχει `@api.readonly` – `search`, `search_read`, `search_count`, `read`, `name_search` και οι μέθοδοι ανάγνωσης του web client.",
            "Τα cron, οι ενημερώσεις modules (`-u`) και το shell χρησιμοποιούν πάντα τον primary.",
            "Κάθε worker έχει **δύο** pools συνδέσεων (μόνο-ανάγνωσης και ανάγνωσης/εγγραφής), το καθένα έως `db_maxconn`.",
        ]),
        ("h", "Γιατί μπορεί να γίνει πιο αργό"),
        ("ul", [
            "**Καθυστέρηση δικτύου.** Το Odoo στέλνει δεκάδες έως εκατοντάδες μικρά ερωτήματα ανά αίτημα. 2–5 ms επιπλέον ανά ερώτημα προς replica σε άλλο data center ή μέσω VPN γίνονται δευτερόλεπτα.",
            "**Διπλή εκκίνηση στις εγγραφές.** Κάθε αίτημα εγγραφής ανοίγει πρώτα cursor στο replica, ελέγχει το registry, τον κλείνει και ξεκινά ξανά στον primary.",
            "**Επαναλήψεις.** Μια δική σας ή OCA διαδρομή δηλωμένη ως μόνο-ανάγνωσης που τελικά γράφει, αποτυγχάνει με `ReadOnlySqlTransaction` και εκτελείται **ολόκληρη ξανά** στον primary.",
            "**Πιο αδύναμο replica / κρύα cache.** Με λιγότερη RAM ή κρύα cache, το ίδιο ερώτημα είναι πιο αργό απ' ό,τι στον primary.",
            "**Συνδέσεις.** Δύο pools ανά worker μπορούν να φτάσουν το `max_connections` της PostgreSQL.",
            "**Η καθυστέρηση αναπαραγωγής** δεν επιβραδύνει, αλλά αμέσως μετά την αποθήκευση μια λίστα μπορεί να δείχνει ακόμα παλιές τιμές – μπερδεύει τους χρήστες.",
        ]),
        ("h", "Μετρήστε αντί να μαντεύετε"),
        ("code", "measure"),
        ("p", "Το κόλπο είναι το βήμα 4: αν το `dev_mode = replica` σε έναν server είναι το ίδιο γρήγορο με την περίπτωση χωρίς replica, το επιπλέον κόστος του Odoo είναι μικρό και το φρένο βρίσκεται στο **δίκτυο ή στο hardware του replica**. Αυτό ακριβώς ήταν το ανοιχτό ερώτημα στις δοκιμές μου."),
        ("h", "Η πλευρά της PostgreSQL"),
        ("code", "pg"),
        ("p", "Χρησιμοποιήστε φυσική streaming replication (hot standby). Το `synchronous_commit = remote_apply` θα εγγυόταν ότι μια ανάγνωση βλέπει την προηγούμενη εγγραφή, αλλά κάθε εγγραφή θα περίμενε το replica – σπάνια αξίζει για το Odoo. Και το replica έχει αξία ούτως ή άλλως ως **failover** (`SELECT pg_promote();`), ακόμα και χωρίς `db_replica_host`."),
        ("h", "Πότε αξίζει"),
        ("table", [
            ["Περίπτωση", "Replica για ανάγνωση;"],
            ["Ιστότοπος / eShop με πολλούς επισκέπτες, portals, dashboards, αναφορές, αναγνώσεις API· primary στο όριο", "**ναι** – αν το replica είναι στο ίδιο LAN"],
            ["Μικρή ή μεσαία εγκατάσταση (δεκάδες χρήστες)", "όχι – πρώτα βελτιστοποίηση του primary: indexes, workers, μνήμη PostgreSQL"],
            ["Πολλές εγγραφές: POS, αποθήκη, εισαγωγές, παραγωγή", "σπάνια – οι εγγραφές πάνε ούτως ή άλλως στον primary"],
            ["Replica σε άλλη περιοχή / μέσω VPN", "όχι – η καθυστέρηση τρώει το κέρδος"],
            ["Υψηλή διαθεσιμότητα", "**ναι, ως standby** – με ή χωρίς `db_replica_host`"],
        ]),
        ("h", "Για τα δικά σας modules"),
        ("ul", [
            "Σημειώστε τους controllers που μόνο διαβάζουν με `readonly=True` και τις μεθόδους RPC που μόνο διαβάζουν με `@api.readonly` – ποτέ μεθόδους που γράφουν, στέλνουν email ή ενημερώνουν πεδία «τελευταία προβολή».",
            "Μετά από κάθε deployment ελέγξτε το log για `retrying with a read/write cursor` – κάθε γραμμή δείχνει μια διαδρομή που δεν θα έπρεπε να είναι μόνο-ανάγνωσης.",
        ]),
        ("links", "Σύνδεσμοι"),
    ],
}

REPLICA["t"]["uk"] = {
    "title": "Odoo 19 з read-реплікою PostgreSQL: писати на майстер, читати з репліки – і чому може стати повільніше",
    "summary": "Починаючи з Odoo 18 два рядки в odoo.conf відправляють запити лише на читання на репліку. Як Odoo вирішує для кожного запиту (з вихідного коду), чому мої тести були повільнішими, як виміряти і коли це має сенс.",
    "body": [
        ("p", "Починаючи з **Odoo 18** (і доопрацьовано в **19**) Odoo вміє ділити навантаження: записи йдуть на **майстер** PostgreSQL, запити лише на читання — на **репліку**. Це два рядки в `odoo.conf`. У моїх експериментах Odoo став **повільнішим**, а не швидшим, тож я подивився у вихідний код, чому."),
        ("note", "Коротко: кожен запит починається на репліці, а все, що пише (зберегти, кнопки, onchange), потім перемикається на майстер. Якщо до репліки є мережева затримка, кожен клік платить двічі. Репліка допомагає лише при навантаженні переважно на читання і коли вона в тій самій локальній мережі (< 1 мс)."),
        ("h", "Як увімкнути"),
        ("code", "conf"),
        ("ul", [
            "Odoo 17 і старші: репліки не підтримуються.",
            "Odoo 18: **порожній** `db_replica_host =` означає з'єднання лише на читання з тим самим сервером через Unix-сокет (для тестів).",
            "Odoo 19: замість цього тепер `dev_mode = replica` (`--dev=replica`); також Odoo 19 читає `PGHOST_REPLICA` / `PGPORT_REPLICA` зі змінних оточення.",
        ]),
        ("h", "Що куди йде — прямо з вихідного коду"),
        ("code", "flow"),
        ("ul", [
            "Маршрут вважається «лише читання», якщо в ньому вказано `readonly=True` (або функція вирішує для кожного запиту). Маршрути з `auth='none'` за замовчуванням лише на читання, усі інші — на читання й запис.",
            "`/web/dataset/call_kw` і `call_button` йдуть на репліку **лише** тоді, коли викликаний метод позначено `@api.readonly`: `search`, `search_read`, `search_count`, `read`, `name_search` і методи читання веб-клієнта.",
            "Крони, оновлення модулів (`-u`) і shell завжди працюють з майстром.",
            "Кожен воркер має **два** пули з'єднань (на читання і на запис), кожен до `db_maxconn`.",
        ]),
        ("h", "Чому може стати повільніше"),
        ("ul", [
            "**Мережева затримка.** На один запит Odoo надсилає десятки й сотні дрібних SQL-запитів. Зайві 2–5 мс на кожен до репліки в іншому дата-центрі чи через VPN складаються в секунди.",
            "**Подвійний старт для записів.** Кожен запит на запис спочатку відкриває курсор на репліці, перевіряє реєстр, закриває його і починає заново на майстрі.",
            "**Повтори.** Свій або OCA-маршрут, позначений «лише читання», який усе ж пише, падає з `ReadOnlySqlTransaction` і виконується **повністю ще раз** на майстрі.",
            "**Слабша репліка / холодний кеш.** Якщо в репліки менше RAM або холодний кеш, той самий запит повільніший, ніж на майстрі.",
            "**З'єднання.** Два пули на кожен воркер можуть упертися в `max_connections` PostgreSQL.",
            "**Затримка реплікації** не гальмує, але одразу після збереження список може ще показувати старі значення, і це плутає користувачів.",
        ]),
        ("h", "Вимірювати, а не вгадувати"),
        ("code", "measure"),
        ("p", "Ключовий крок — четвертий. Якщо `dev_mode = replica` на одному сервері працює так само швидко, як без репліки, то власні витрати Odoo невеликі, а гальмує **мережа або залізо репліки**. Саме це питання в моїх тестах залишилося відкритим."),
        ("h", "З боку PostgreSQL"),
        ("code", "pg"),
        ("p", "Використовуйте фізичну потокову реплікацію (hot standby). `synchronous_commit = remote_apply` гарантував би, що читання бачить попередній запис, але кожен запис чекав би репліку — для Odoo рідко виправдано. А як **резерв для перемикання** (`SELECT pg_promote();`) репліка корисна в будь-якому разі, навіть без `db_replica_host`."),
        ("h", "Коли це має сенс"),
        ("table", [
            ["Ситуація", "Репліка для читання?"],
            ["Сайт / магазин з великою кількістю відвідувачів, портали, дашборди, звіти, читання через API; майстер на межі", "**так**, якщо репліка в тій самій локальній мережі"],
            ["Мала або середня інсталяція (десятки користувачів)", "ні, спершу оптимізувати майстер: індекси, воркери, пам'ять PostgreSQL"],
            ["Багато записів: POS, склад, імпорти, виробництво", "рідко, записи все одно йдуть на майстер"],
            ["Репліка в іншому регіоні / через VPN", "ні, затримка з'їдає виграш"],
            ["Висока доступність", "**так, як standby**, з `db_replica_host` чи без"],
        ]),
        ("h", "Для власних модулів"),
        ("ul", [
            "Контролери, які лише читають, позначайте `readonly=True`, а методи, що викликаються через RPC і лише читають, позначайте `@api.readonly`. Ніколи не позначайте так методи, які пишуть, надсилають пошту чи оновлюють поля на кшталт «востаннє переглянуто».",
            "Після кожного розгортання стежте в лозі за `retrying with a read/write cursor`: кожен такий рядок вказує маршрут, який не має бути «лише читання».",
        ]),
        ("links", "Посилання"),
    ],
}

REPLICA["t"]["ru"] = {
    "title": "Odoo 19 с read-репликой PostgreSQL: писать на мастер, читать с реплики — и почему может стать медленнее",
    "summary": "Начиная с Odoo 18 две строки в odoo.conf отправляют запросы только на чтение на реплику. Как Odoo решает для каждого запроса (по исходному коду), почему мои тесты были медленнее, как измерить и когда это имеет смысл.",
    "body": [
        ("p", "Начиная с **Odoo 18** (и доработано в **19**) Odoo умеет делить нагрузку: записи идут на **мастер** PostgreSQL, запросы только на чтение — на **реплику**. Это две строки в `odoo.conf`. В моих экспериментах Odoo стал **медленнее**, а не быстрее, так что я посмотрел в исходный код, почему."),
        ("note", "Коротко: каждый запрос начинается на реплике, а всё, что пишет (сохранить, кнопки, onchange), потом переключается на мастер. Если до реплики есть сетевая задержка, каждый клик платит дважды. Реплика помогает только при нагрузке преимущественно на чтение и когда она в той же локальной сети (< 1 мс)."),
        ("h", "Как включить"),
        ("code", "conf"),
        ("ul", [
            "Odoo 17 и старше: реплики не поддерживаются.",
            "Odoo 18: **пустой** `db_replica_host =` означает соединение только на чтение с тем же сервером через Unix-сокет (для тестов).",
            "Odoo 19: вместо этого теперь `dev_mode = replica` (`--dev=replica`); также Odoo 19 читает `PGHOST_REPLICA` / `PGPORT_REPLICA` из переменных окружения.",
        ]),
        ("h", "Что куда идёт — прямо из исходного кода"),
        ("code", "flow"),
        ("ul", [
            "Маршрут считается «только чтение», если в нём указано `readonly=True` (или функция решает для каждого запроса). Маршруты с `auth='none'` по умолчанию только на чтение, все остальные — на чтение и запись.",
            "`/web/dataset/call_kw` и `call_button` идут на реплику **только** тогда, когда вызванный метод помечен `@api.readonly`: `search`, `search_read`, `search_count`, `read`, `name_search` и методы чтения веб-клиента.",
            "Кроны, обновление модулей (`-u`) и shell всегда работают с мастером.",
            "У каждого воркера **два** пула соединений (на чтение и на запись), каждый до `db_maxconn`.",
        ]),
        ("h", "Почему может стать медленнее"),
        ("ul", [
            "**Сетевая задержка.** На один запрос Odoo отправляет десятки и сотни мелких SQL-запросов. Лишние 2–5 мс на каждый до реплики в другом дата-центре или через VPN складываются в секунды.",
            "**Двойной старт для записей.** Каждый запрос на запись сначала открывает курсор на реплике, проверяет реестр, закрывает его и начинает заново на мастере.",
            "**Повторы.** Свой или OCA-маршрут, помеченный «только чтение», который всё же пишет, падает с `ReadOnlySqlTransaction` и выполняется **целиком ещё раз** на мастере.",
            "**Более слабая реплика / холодный кеш.** Если у реплики меньше RAM или холодный кеш, тот же запрос медленнее, чем на мастере.",
            "**Соединения.** Два пула на каждый воркер могут упереться в `max_connections` PostgreSQL.",
            "**Задержка репликации** не тормозит, но сразу после сохранения список может ещё показывать старые значения, и это путает пользователей.",
        ]),
        ("h", "Измерять, а не гадать"),
        ("code", "measure"),
        ("p", "Ключевой шаг — четвёртый. Если `dev_mode = replica` на одном сервере работает так же быстро, как без реплики, то собственные затраты Odoo невелики, а тормозит **сеть или железо реплики**. Именно этот вопрос в моих тестах остался открытым."),
        ("h", "Со стороны PostgreSQL"),
        ("code", "pg"),
        ("p", "Используйте физическую потоковую репликацию (hot standby). `synchronous_commit = remote_apply` гарантировал бы, что чтение видит предыдущую запись, но каждая запись ждала бы реплику — для Odoo редко оправдано. А как **резерв для переключения** (`SELECT pg_promote();`) реплика полезна в любом случае, даже без `db_replica_host`."),
        ("h", "Когда это имеет смысл"),
        ("table", [
            ["Ситуация", "Реплика для чтения?"],
            ["Сайт / магазин с большим числом посетителей, порталы, дашборды, отчёты, чтение через API; мастер на пределе", "**да**, если реплика в той же локальной сети"],
            ["Малая или средняя инсталляция (десятки пользователей)", "нет, сначала оптимизировать мастер: индексы, воркеры, память PostgreSQL"],
            ["Много записей: POS, склад, импорты, производство", "редко, записи всё равно идут на мастер"],
            ["Реплика в другом регионе / через VPN", "нет, задержка съедает выигрыш"],
            ["Высокая доступность", "**да, как standby**, с `db_replica_host` или без"],
        ]),
        ("h", "Для своих модулей"),
        ("ul", [
            "Контроллеры, которые только читают, помечайте `readonly=True`, а методы, вызываемые через RPC и только читающие, помечайте `@api.readonly`. Никогда не помечайте так методы, которые пишут, отправляют почту или обновляют поля вроде «последний просмотр».",
            "После каждого развёртывания следите в логе за `retrying with a read/write cursor`: каждая такая строка указывает маршрут, который не должен быть «только чтение».",
        ]),
        ("links", "Ссылки"),
    ],
}
