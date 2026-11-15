# Статья 15: pgload – свой генератор нагрузки на PostgreSQL; локальная база vs внешняя с репликой. Код из tools/pgload/pgload.py. Все 6 языков.
import os

_SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools", "pgload", "pgload.py")
with open(_SRC, encoding="utf-8") as _fh:
    _CODE = _fh.read()

PGLOAD = {
    "slug": "postgresql-load-test-pgload-replica",
    "date": "2026-11-15",
    "tags": ["PostgreSQL", "Performance", "Replica", "Load test", "Python"],
    "code": {
        "run": ("bash · runs to compare", """pip install psycopg2-binary
export PGDATABASE=loadtest PGUSER=odoo            # password: ~/.pgpass, never on the command line

# A) local database over the Unix socket
PGHOST=/run/postgresql ./pgload.py -w 32 -c 20000 -s 64 -r | tee a_local.log

# B) remote database, asynchronous replica
PGHOST=10.0.0.10 ./pgload.py -w 32 -c 20000 -s 64 -r | tee b_remote.log

# C) same remote database, synchronous replica (on the primary: synchronous_standby_names = '*')
PGHOST=10.0.0.10 ./pgload.py -w 32 -c 20000 -s 64 -r | tee c_remote_sync.log

# D) Odoo-like: many small reads and short writes
PGHOST=10.0.0.10 ./pgload.py -m mixed --read-ratio 0.8 -s 2 -w 64 -c 50000 | tee d_mixed.log

grep RESULT *.log
./pgload.py --drop                                  # clean up"""),
        "out": ("output", """2026-11-15 22:10:01 server 10.0.0.10 PostgreSQL 16.4, synchronous_commit=on, replicas=1; workers=32 count=20000 size=64kB mode=insert
2026-11-15 22:10:02 insert: n=100 ...
2026-11-15 22:11:40 RESULT insert: n=20000 204/s avg=156.2ms p50=148.0 p95=231.4 p99=298.7 max=611.0ms | written 937 MB (9.6 MB/s) | errors 0 | 98s
(example of the format – your numbers depend entirely on hardware, network and settings)"""),
        "watch": ("sql · watch during the run", """-- on the primary: replication and how far the replica is behind
SELECT application_name, state, sync_state, write_lag, flush_lag, replay_lag FROM pg_stat_replication;
-- WAL generated (PostgreSQL 14+): run before and after, compare
SELECT wal_records, pg_size_pretty(wal_bytes), wal_buffers_full FROM pg_stat_wal;
-- what the test connections are waiting for
SELECT wait_event_type, wait_event, count(*) FROM pg_stat_activity
 WHERE application_name = 'pgload' GROUP BY 1, 2 ORDER BY 3 DESC;"""),
        "src": ("python · pgload.py (download: /tools/pgload.py)", _CODE),
    },
    "links": [
        ("pgload.py – download", "https://2027.pp.ua/tools/pgload.py"),
        ("PostgreSQL: synchronous_commit and synchronous replication", "https://www.postgresql.org/docs/current/warm-standby.html#SYNCHRONOUS-REPLICATION"),
        ("PostgreSQL: pg_stat_wal / pg_stat_replication", "https://www.postgresql.org/docs/current/monitoring-stats.html"),
        ("pgbench – the standard benchmark", "https://www.postgresql.org/docs/current/pgbench.html"),
        ("Blog: Odoo 19 with a read replica", "@blog:odoo-19-postgresql-read-replica"),
    ],
    "t": {},
}

PGLOAD["t"]["en"] = {
    "title": "pgload: a small load generator for PostgreSQL – local database vs. remote database with a replica",
    "summary": "Why we wrote our own load tool besides pgbench, what it measures (latency percentiles, throughput, errors), how to compare local socket, remote host and synchronous replica – with the full code, passwords only from the environment.",
    "body": [
        ("p", "Before moving an Odoo database to a separate PostgreSQL server with a replica, we wanted numbers, not opinions: how much slower is a commit over the network? What does a synchronous replica cost? Which settings matter? `pgbench` measures its own TPC-B-like workload; we wanted **our** pattern – many parallel connections, binary blocks like Odoo attachments, short reads – and the same command against every variant."),
        ("note", "Short version: pgload opens N parallel connections, inserts (and optionally reads) blocks of configurable size, and reports throughput and latency percentiles. Run it identically against local socket, remote host and remote host with synchronous replica – the differences are your network and replication costs. Only on a test database: it writes real data and WAL."),
        ("h", "What it does"),
        ("ul", [
            "Creates a schema `pgload` with one table (bytea column, two indexes – so every insert also updates indexes and WAL like a real table).",
            "Runs `--count` operations with `--workers` parallel connections, in blocks; each operation is its own transaction (autocommit) – so every insert pays a full commit, including waiting for a synchronous replica.",
            "Modes: `insert`, `select` (random range reads), `mixed` with `--read-ratio`.",
            "Prints after every block and at the end: operations per second, average, p50/p95/p99/max latency, MB written, errors.",
            "Connection data **only from the libpq environment** (`PGHOST`, `PGUSER`, `PGDATABASE`, password via `~/.pgpass`) – nothing secret in the script or the shell history.",
        ]),
        ("h", "Running a comparison"),
        ("code", "run"),
        ("code", "out"),
        ("h", "What to vary – one thing at a time"),
        ("table", [
            ["Setting", "What it shows"],
            ["Unix socket vs. TCP to localhost vs. remote host", "pure network cost per commit/query"],
            ["`synchronous_commit` on / off / `remote_write` / `remote_apply`", "cost of durability and of waiting for the replica"],
            ["Asynchronous vs. synchronous replica (`synchronous_standby_names`)", "every commit waits for the replica's round trip"],
            ["`wal_compression`, `max_wal_size`, `checkpoint_timeout`", "WAL volume and checkpoint spikes (watch p99/max)"],
            ["`-s` small (2 kB) vs. large (512 kB)", "latency-bound vs. bandwidth-bound"],
            ["`-w` 8 → 32 → 128", "where throughput stops growing and latency explodes"],
        ]),
        ("code", "watch"),
        ("h", "How to read the results"),
        ("ul", [
            "**Small blocks:** latency ≈ network round trip + commit (fsync). With a synchronous replica add the round trip to the replica. A few milliseconds per operation are normal remotely – and Odoo does hundreds of small operations per click, so they add up.",
            "**Large blocks:** throughput is limited by bandwidth and WAL; `wal_compression` can help, the disk of primary and replica decides.",
            "**p99/max far above average:** checkpoints, autovacuum or a replica that cannot keep up – compare with `pg_stat_wal` and `replay_lag`.",
            "**More workers, same throughput:** the bottleneck is reached; more connections only add waiting.",
            "In our project the remote setup was clearly slower per operation; the tool separated how much of it was network and how much PostgreSQL settings.",
        ]),
        ("h", "Safety"),
        ("ul", [
            "Never run it against production “just briefly”: 20 000 × 64 kB is about 1.3 GB of data plus the same in WAL, replicated and included in the next backups.",
            "Use a dedicated database (`createdb loadtest`) or a stage copy, and `--drop` afterwards.",
            "Do not put `PGPASSWORD` into scripts in the repository; use `~/.pgpass` (chmod 600) or peer authentication on the socket.",
        ]),
        ("h", "The code"),
        ("p", "One file, only dependency `psycopg2`. It is a cleaned-up version of an internal tool: correct percentiles instead of averaged averages, one thread pool, mixed mode, cleanup, no secrets."),
        ("code", "src"),
        ("links", "Links"),
    ],
}

PGLOAD["t"]["de"] = {
    "title": "pgload: ein kleiner Lastgenerator für PostgreSQL – lokale Datenbank gegen entfernte Datenbank mit Replica",
    "summary": "Warum wir neben pgbench ein eigenes Lastwerkzeug geschrieben haben, was es misst (Latenz-Perzentile, Durchsatz, Fehler), wie man lokalen Socket, entfernten Host und synchrone Replica vergleicht – mit vollständigem Code, Passwörter nur aus der Umgebung.",
    "body": [
        ("p", "Bevor eine Odoo-Datenbank auf einen eigenen PostgreSQL-Server mit Replica umzieht, wollten wir Zahlen statt Meinungen: Wie viel langsamer ist ein Commit über das Netzwerk? Was kostet eine synchrone Replica? Welche Einstellungen zählen? `pgbench` misst seine eigene TPC-B-ähnliche Last; wir wollten **unser** Muster – viele parallele Verbindungen, Binärblöcke wie Odoo-Anhänge, kurze Lesezugriffe – und denselben Befehl gegen jede Variante."),
        ("note", "Kurzfassung: pgload öffnet N parallele Verbindungen, fügt Blöcke einstellbarer Größe ein (und liest optional) und meldet Durchsatz und Latenz-Perzentile. Identisch gegen lokalen Socket, entfernten Host und entfernten Host mit synchroner Replica ausführen – die Unterschiede sind Ihre Netzwerk- und Replikationskosten. Nur auf einer Testdatenbank: Es schreibt echte Daten und WAL."),
        ("h", "Was es tut"),
        ("ul", [
            "Legt ein Schema `pgload` mit einer Tabelle an (bytea-Spalte, zwei Indizes – jeder Insert aktualisiert also Indizes und WAL wie eine echte Tabelle).",
            "Führt `--count` Operationen mit `--workers` parallelen Verbindungen in Blöcken aus; jede Operation ist eine eigene Transaktion (Autocommit) – jeder Insert zahlt also einen vollen Commit, inklusive Warten auf eine synchrone Replica.",
            "Modi: `insert`, `select` (zufällige Bereichs-Lesezugriffe), `mixed` mit `--read-ratio`.",
            "Gibt nach jedem Block und am Ende aus: Operationen pro Sekunde, Durchschnitt, p50/p95/p99/max-Latenz, geschriebene MB, Fehler.",
            "Verbindungsdaten **nur aus der libpq-Umgebung** (`PGHOST`, `PGUSER`, `PGDATABASE`, Passwort über `~/.pgpass`) – nichts Geheimes im Skript oder in der Shell-History.",
        ]),
        ("h", "Einen Vergleich fahren"),
        ("code", "run"),
        ("code", "out"),
        ("h", "Was man variiert – immer nur eine Sache"),
        ("table", [
            ["Einstellung", "Was sie zeigt"],
            ["Unix-Socket vs. TCP auf localhost vs. entfernter Host", "reine Netzwerkkosten pro Commit/Abfrage"],
            ["`synchronous_commit` on / off / `remote_write` / `remote_apply`", "Kosten der Dauerhaftigkeit und des Wartens auf die Replica"],
            ["Asynchrone vs. synchrone Replica (`synchronous_standby_names`)", "jeder Commit wartet auf den Round Trip zur Replica"],
            ["`wal_compression`, `max_wal_size`, `checkpoint_timeout`", "WAL-Menge und Checkpoint-Spitzen (p99/max beobachten)"],
            ["`-s` klein (2 kB) vs. groß (512 kB)", "latenzgebunden vs. bandbreitengebunden"],
            ["`-w` 8 → 32 → 128", "wo der Durchsatz aufhört zu wachsen und die Latenz explodiert"],
        ]),
        ("code", "watch"),
        ("h", "Ergebnisse lesen"),
        ("ul", [
            "**Kleine Blöcke:** Latenz ≈ Netzwerk-Round-Trip + Commit (fsync). Mit synchroner Replica kommt der Round Trip zur Replica hinzu. Ein paar Millisekunden pro Operation sind entfernt normal – und Odoo macht Hunderte kleine Operationen pro Klick, das summiert sich.",
            "**Große Blöcke:** Der Durchsatz wird von Bandbreite und WAL begrenzt; `wal_compression` kann helfen, die Platten von Primary und Replica entscheiden.",
            "**p99/max weit über dem Durchschnitt:** Checkpoints, Autovacuum oder eine Replica, die nicht nachkommt – mit `pg_stat_wal` und `replay_lag` vergleichen.",
            "**Mehr Worker, gleicher Durchsatz:** Der Engpass ist erreicht; mehr Verbindungen erzeugen nur Wartezeit.",
            "In unserem Projekt war die entfernte Variante pro Operation deutlich langsamer; das Werkzeug hat getrennt, wie viel davon Netzwerk und wie viel PostgreSQL-Einstellungen war.",
        ]),
        ("h", "Sicherheit"),
        ("ul", [
            "Nie „nur kurz“ gegen die Produktion laufen lassen: 20 000 × 64 kB sind etwa 1,3 GB Daten plus noch einmal so viel WAL, repliziert und in den nächsten Backups enthalten.",
            "Eine eigene Datenbank (`createdb loadtest`) oder eine Stage-Kopie verwenden und danach `--drop`.",
            "`PGPASSWORD` nicht in Skripte im Repository schreiben; `~/.pgpass` (chmod 600) oder Peer-Authentifizierung über den Socket nutzen.",
        ]),
        ("h", "Der Code"),
        ("p", "Eine Datei, einzige Abhängigkeit `psycopg2`. Es ist eine aufgeräumte Fassung eines internen Werkzeugs: korrekte Perzentile statt gemittelter Mittelwerte, ein Thread-Pool, gemischter Modus, Aufräumen, keine Geheimnisse."),
        ("code", "src"),
        ("links", "Links"),
    ],
}

PGLOAD["t"]["fr"] = {
    "title": "pgload : un petit générateur de charge pour PostgreSQL – base locale contre base distante avec réplique",
    "summary": "Pourquoi nous avons écrit notre propre outil de charge à côté de pgbench, ce qu'il mesure (percentiles de latence, débit, erreurs), comment comparer socket local, hôte distant et réplique synchrone – avec le code complet, mots de passe uniquement depuis l'environnement.",
    "body": [
        ("p", "Avant de déplacer une base Odoo vers un serveur PostgreSQL séparé avec réplique, nous voulions des chiffres plutôt que des opinions : de combien un commit est-il plus lent à travers le réseau ? Que coûte une réplique synchrone ? Quels réglages comptent ? `pgbench` mesure sa propre charge de type TPC-B ; nous voulions **notre** profil – beaucoup de connexions parallèles, des blocs binaires comme les pièces jointes Odoo, des lectures courtes – et la même commande contre chaque variante."),
        ("note", "En bref : pgload ouvre N connexions parallèles, insère (et lit en option) des blocs de taille réglable et affiche débit et percentiles de latence. Lancé à l'identique contre le socket local, l'hôte distant et l'hôte distant avec réplique synchrone, il montre vos coûts de réseau et de réplication. Uniquement sur une base de test : il écrit de vraies données et du WAL."),
        ("h", "Ce qu'il fait"),
        ("ul", [
            "Crée un schéma `pgload` avec une table (colonne bytea, deux index – chaque insertion met donc à jour index et WAL comme une vraie table).",
            "Exécute `--count` opérations avec `--workers` connexions parallèles, par blocs ; chaque opération est sa propre transaction (autocommit) – chaque insertion paie un commit complet, y compris l'attente d'une réplique synchrone.",
            "Modes : `insert`, `select` (lectures aléatoires par plage), `mixed` avec `--read-ratio`.",
            "Affiche après chaque bloc et à la fin : opérations par seconde, moyenne, latence p50/p95/p99/max, Mo écrits, erreurs.",
            "Paramètres de connexion **uniquement via l'environnement libpq** (`PGHOST`, `PGUSER`, `PGDATABASE`, mot de passe via `~/.pgpass`) – rien de secret dans le script ni dans l'historique du shell.",
        ]),
        ("h", "Lancer une comparaison"),
        ("code", "run"),
        ("code", "out"),
        ("h", "Ce qu'on fait varier – une chose à la fois"),
        ("table", [
            ["Réglage", "Ce qu'il montre"],
            ["Socket Unix vs. TCP vers localhost vs. hôte distant", "coût réseau pur par commit/requête"],
            ["`synchronous_commit` on / off / `remote_write` / `remote_apply`", "coût de la durabilité et de l'attente de la réplique"],
            ["Réplique asynchrone vs. synchrone (`synchronous_standby_names`)", "chaque commit attend l'aller-retour vers la réplique"],
            ["`wal_compression`, `max_wal_size`, `checkpoint_timeout`", "volume de WAL et pics de checkpoint (surveiller p99/max)"],
            ["`-s` petit (2 ko) vs. grand (512 ko)", "limité par la latence vs. par la bande passante"],
            ["`-w` 8 → 32 → 128", "où le débit cesse de croître et où la latence explose"],
        ]),
        ("code", "watch"),
        ("h", "Lire les résultats"),
        ("ul", [
            "**Petits blocs :** latence ≈ aller-retour réseau + commit (fsync). Avec une réplique synchrone, ajouter l'aller-retour vers la réplique. Quelques millisecondes par opération sont normales à distance – et Odoo fait des centaines de petites opérations par clic, cela s'additionne.",
            "**Grands blocs :** le débit est limité par la bande passante et le WAL ; `wal_compression` peut aider, les disques du primaire et de la réplique décident.",
            "**p99/max très au-dessus de la moyenne :** checkpoints, autovacuum ou une réplique qui ne suit pas – comparer avec `pg_stat_wal` et `replay_lag`.",
            "**Plus de workers, même débit :** le goulot est atteint ; plus de connexions ne font qu'ajouter de l'attente.",
            "Dans notre projet, la variante distante était nettement plus lente par opération ; l'outil a séparé la part du réseau de celle des réglages PostgreSQL.",
        ]),
        ("h", "Sécurité"),
        ("ul", [
            "Ne jamais le lancer « juste un instant » contre la production : 20 000 × 64 ko font environ 1,3 Go de données plus autant de WAL, répliqués et inclus dans les prochaines sauvegardes.",
            "Utiliser une base dédiée (`createdb loadtest`) ou une copie de stage, puis `--drop`.",
            "Ne pas écrire `PGPASSWORD` dans des scripts du dépôt ; utiliser `~/.pgpass` (chmod 600) ou l'authentification peer via le socket.",
        ]),
        ("h", "Le code"),
        ("p", "Un seul fichier, seule dépendance `psycopg2`. C'est une version nettoyée d'un outil interne : vrais percentiles au lieu de moyennes de moyennes, un seul pool de threads, mode mixte, nettoyage, aucun secret."),
        ("code", "src"),
        ("links", "Liens"),
    ],
}

PGLOAD["t"]["el"] = {
    "title": "pgload: ένας μικρός γεννήτορας φορτίου για PostgreSQL – τοπική βάση έναντι απομακρυσμένης βάσης με replica",
    "summary": "Γιατί γράψαμε δικό μας εργαλείο φορτίου δίπλα στο pgbench, τι μετρά (εκατοστημόρια καθυστέρησης, ρυθμό, σφάλματα), πώς συγκρίνετε τοπικό socket, απομακρυσμένο host και σύγχρονο replica – με πλήρη κώδικα, κωδικοί μόνο από το περιβάλλον.",
    "body": [
        ("p", "Πριν μεταφέρουμε μια βάση Odoo σε ξεχωριστό server PostgreSQL με replica, θέλαμε αριθμούς, όχι απόψεις: πόσο πιο αργό είναι ένα commit μέσω δικτύου; Πόσο κοστίζει ένα σύγχρονο replica; Ποιες ρυθμίσεις μετράνε; Το `pgbench` μετρά το δικό του φορτίο τύπου TPC-B· εμείς θέλαμε το **δικό μας** μοτίβο – πολλές παράλληλες συνδέσεις, δυαδικά μπλοκ όπως τα συνημμένα του Odoo, σύντομες αναγνώσεις – και την ίδια εντολή απέναντι σε κάθε παραλλαγή."),
        ("note", "Συνοπτικά: το pgload ανοίγει N παράλληλες συνδέσεις, εισάγει (και προαιρετικά διαβάζει) μπλοκ ρυθμιζόμενου μεγέθους και αναφέρει ρυθμό και εκατοστημόρια καθυστέρησης. Τρέξτε το πανομοιότυπα σε τοπικό socket, απομακρυσμένο host και απομακρυσμένο host με σύγχρονο replica – οι διαφορές είναι το κόστος δικτύου και αναπαραγωγής σας. Μόνο σε βάση δοκιμών: γράφει πραγματικά δεδομένα και WAL."),
        ("h", "Τι κάνει"),
        ("ul", [
            "Δημιουργεί schema `pgload` με έναν πίνακα (στήλη bytea, δύο indexes – κάθε εισαγωγή ενημερώνει indexes και WAL όπως ένας πραγματικός πίνακας).",
            "Εκτελεί `--count` λειτουργίες με `--workers` παράλληλες συνδέσεις, σε μπλοκ· κάθε λειτουργία είναι ξεχωριστή συναλλαγή (autocommit) – κάθε εισαγωγή πληρώνει ένα πλήρες commit, μαζί με την αναμονή για σύγχρονο replica.",
            "Λειτουργίες: `insert`, `select` (τυχαίες αναγνώσεις εύρους), `mixed` με `--read-ratio`.",
            "Τυπώνει μετά από κάθε μπλοκ και στο τέλος: λειτουργίες ανά δευτερόλεπτο, μέσο όρο, καθυστέρηση p50/p95/p99/max, MB που γράφτηκαν, σφάλματα.",
            "Στοιχεία σύνδεσης **μόνο από το περιβάλλον libpq** (`PGHOST`, `PGUSER`, `PGDATABASE`, κωδικός μέσω `~/.pgpass`) – τίποτα μυστικό στο script ή στο ιστορικό του shell.",
        ]),
        ("h", "Εκτέλεση σύγκρισης"),
        ("code", "run"),
        ("code", "out"),
        ("h", "Τι αλλάζετε – ένα πράγμα κάθε φορά"),
        ("table", [
            ["Ρύθμιση", "Τι δείχνει"],
            ["Unix socket vs. TCP σε localhost vs. απομακρυσμένος host", "καθαρό κόστος δικτύου ανά commit/ερώτημα"],
            ["`synchronous_commit` on / off / `remote_write` / `remote_apply`", "κόστος ανθεκτικότητας και αναμονής για το replica"],
            ["Ασύγχρονο vs. σύγχρονο replica (`synchronous_standby_names`)", "κάθε commit περιμένει το round trip προς το replica"],
            ["`wal_compression`, `max_wal_size`, `checkpoint_timeout`", "όγκος WAL και αιχμές checkpoint (δείτε p99/max)"],
            ["`-s` μικρό (2 kB) vs. μεγάλο (512 kB)", "περιορισμός από καθυστέρηση vs. από εύρος ζώνης"],
            ["`-w` 8 → 32 → 128", "πού σταματά να αυξάνεται ο ρυθμός και εκτοξεύεται η καθυστέρηση"],
        ]),
        ("code", "watch"),
        ("h", "Πώς διαβάζετε τα αποτελέσματα"),
        ("ul", [
            "**Μικρά μπλοκ:** καθυστέρηση ≈ round trip δικτύου + commit (fsync). Με σύγχρονο replica προστίθεται το round trip προς το replica. Λίγα χιλιοστά του δευτερολέπτου ανά λειτουργία είναι φυσιολογικά απομακρυσμένα – και το Odoo κάνει εκατοντάδες μικρές λειτουργίες ανά κλικ, οπότε αθροίζονται.",
            "**Μεγάλα μπλοκ:** ο ρυθμός περιορίζεται από το εύρος ζώνης και το WAL· το `wal_compression` μπορεί να βοηθήσει, αποφασίζουν οι δίσκοι του primary και του replica.",
            "**p99/max πολύ πάνω από τον μέσο όρο:** checkpoints, autovacuum ή replica που δεν προλαβαίνει – συγκρίνετε με `pg_stat_wal` και `replay_lag`.",
            "**Περισσότεροι workers, ίδιος ρυθμός:** φτάσατε τη στενωπό· περισσότερες συνδέσεις απλώς προσθέτουν αναμονή.",
            "Στο έργο μας η απομακρυσμένη παραλλαγή ήταν σαφώς πιο αργή ανά λειτουργία· το εργαλείο ξεχώρισε πόσο οφειλόταν στο δίκτυο και πόσο στις ρυθμίσεις της PostgreSQL.",
        ]),
        ("h", "Ασφάλεια"),
        ("ul", [
            "Ποτέ «για λίγο» απέναντι στην παραγωγή: 20 000 × 64 kB είναι περίπου 1,3 GB δεδομένα συν άλλα τόσα WAL, που αναπαράγονται και μπαίνουν στα επόμενα αντίγραφα ασφαλείας.",
            "Χρησιμοποιήστε ξεχωριστή βάση (`createdb loadtest`) ή αντίγραφο stage, και μετά `--drop`.",
            "Μη γράφετε `PGPASSWORD` σε scripts του αποθετηρίου· χρησιμοποιήστε `~/.pgpass` (chmod 600) ή peer authentication μέσω socket.",
        ]),
        ("h", "Ο κώδικας"),
        ("p", "Ένα αρχείο, μόνη εξάρτηση το `psycopg2`. Είναι καθαρισμένη έκδοση ενός εσωτερικού εργαλείου: σωστά εκατοστημόρια αντί για μέσους όρους μέσων όρων, ένα thread pool, μικτή λειτουργία, καθάρισμα, κανένα μυστικό."),
        ("code", "src"),
        ("links", "Σύνδεσμοι"),
    ],
}

PGLOAD["t"]["uk"] = {
    "title": "pgload: невеликий генератор навантаження для PostgreSQL – локальна база проти віддаленої з реплікою",
    "summary": "Навіщо ми написали власний інструмент навантаження поряд із pgbench, що він вимірює (перцентилі затримки, пропускну здатність, помилки), як порівняти локальний сокет, віддалений хост і синхронну репліку. Повний код, паролі лише з оточення.",
    "body": [
        ("p", "Перш ніж переносити базу Odoo на окремий сервер PostgreSQL з реплікою, ми хотіли цифр, а не думок. Наскільки повільніший commit через мережу? Скільки коштує синхронна репліка? Які налаштування важливі? `pgbench` вимірює власне навантаження на кшталт TPC-B, а нам був потрібен **наш** профіль: багато паралельних з'єднань, бінарні блоки, як вкладення Odoo, короткі читання, і та сама команда для кожного варіанта."),
        ("note", "Коротко: pgload відкриває N паралельних з'єднань, вставляє (і за бажанням читає) блоки заданого розміру й показує пропускну здатність і перцентилі затримки. Запустіть його однаково на локальному сокеті, віддаленому хості та віддаленому хості з синхронною реплікою, і різниця покаже вартість мережі та реплікації. Лише на тестовій базі: він пише справжні дані й WAL."),
        ("h", "Що він робить"),
        ("ul", [
            "Створює схему `pgload` з однією таблицею (колонка bytea і два індекси), тож кожна вставка оновлює індекси й WAL, як справжня таблиця.",
            "Виконує `--count` операцій через `--workers` паралельних з'єднань, блоками. Кожна операція — окрема транзакція (autocommit), тож кожна вставка платить повний commit разом з очікуванням синхронної репліки.",
            "Режими: `insert`, `select` (випадкові читання діапазонів), `mixed` з `--read-ratio`.",
            "Після кожного блоку й наприкінці виводить: операції за секунду, середнє, затримку p50/p95/p99/max, записані МБ, помилки.",
            "Параметри з'єднання **лише зі змінних оточення libpq** (`PGHOST`, `PGUSER`, `PGDATABASE`, пароль через `~/.pgpass`), тож нічого секретного немає ні в скрипті, ні в історії shell.",
        ]),
        ("h", "Як запустити порівняння"),
        ("code", "run"),
        ("code", "out"),
        ("h", "Що змінювати — по одному параметру за раз"),
        ("table", [
            ["Налаштування", "Що показує"],
            ["Unix-сокет vs. TCP на localhost vs. віддалений хост", "чисту мережеву вартість одного commit чи запиту"],
            ["`synchronous_commit` on / off / `remote_write` / `remote_apply`", "вартість надійності та очікування репліки"],
            ["Асинхронна vs. синхронна репліка (`synchronous_standby_names`)", "кожен commit чекає повного обміну з реплікою"],
            ["`wal_compression`, `max_wal_size`, `checkpoint_timeout`", "обсяг WAL і піки checkpoint (дивіться на p99/max)"],
            ["`-s` малий (2 кБ) vs. великий (512 кБ)", "обмеження затримкою vs. обмеження смугою"],
            ["`-w` 8 → 32 → 128", "де пропускна здатність перестає рости, а затримка різко зростає"],
        ]),
        ("code", "watch"),
        ("h", "Як читати результати"),
        ("ul", [
            "**Малі блоки:** затримка ≈ мережевий обмін + commit (fsync). Із синхронною реплікою додається обмін з реплікою. Кілька мілісекунд на операцію для віддаленої бази — нормально, але Odoo робить сотні дрібних операцій на один клік, і вони складаються.",
            "**Великі блоки:** пропускну здатність обмежують смуга й WAL. `wal_compression` може допомогти, а вирішують диски майстра й репліки.",
            "**p99/max набагато вищі за середнє:** checkpoint, autovacuum або репліка, яка не встигає. Порівняйте з `pg_stat_wal` і `replay_lag`.",
            "**Більше воркерів, та сама пропускна здатність:** досягнуто вузьке місце, і нові з'єднання лише додають очікування.",
            "У нашому проєкті віддалений варіант був помітно повільнішим на кожну операцію, і інструмент показав, яку частину дає мережа, а яку — налаштування PostgreSQL.",
        ]),
        ("h", "Безпека"),
        ("ul", [
            "Ніколи не запускайте його «на хвилинку» на продуктиві: 20 000 × 64 кБ — це близько 1,3 ГБ даних і стільки ж WAL, які реплікуються й потрапляють у наступні бекапи.",
            "Використовуйте окрему базу (`createdb loadtest`) або копію на stage, а після тесту — `--drop`.",
            "Не пишіть `PGPASSWORD` у скрипти в репозиторії; використовуйте `~/.pgpass` (chmod 600) або peer-автентифікацію через сокет.",
        ]),
        ("h", "Код"),
        ("p", "Один файл, єдина залежність — `psycopg2`. Це почищена версія внутрішнього інструмента: правильні перцентилі замість середнього від середніх, один пул потоків, змішаний режим, прибирання, жодних секретів."),
        ("code", "src"),
        ("links", "Посилання"),
    ],
}

PGLOAD["t"]["ru"] = {
    "title": "pgload: небольшой генератор нагрузки для PostgreSQL – локальная база против удалённой с репликой",
    "summary": "Зачем мы написали свой инструмент нагрузки рядом с pgbench, что он измеряет (перцентили задержки, пропускную способность, ошибки), как сравнить локальный сокет, удалённый хост и синхронную реплику. Полный код, пароли только из окружения.",
    "body": [
        ("p", "Прежде чем переносить базу Odoo на отдельный сервер PostgreSQL с репликой, мы хотели цифр, а не мнений. Насколько медленнее commit через сеть? Сколько стоит синхронная реплика? Какие настройки важны? `pgbench` измеряет собственную нагрузку вроде TPC-B, а нам был нужен **наш** профиль: много параллельных соединений, бинарные блоки, как вложения Odoo, короткие чтения, и одна и та же команда для каждого варианта."),
        ("note", "Коротко: pgload открывает N параллельных соединений, вставляет (и при желании читает) блоки заданного размера и показывает пропускную способность и перцентили задержки. Запустите его одинаково на локальном сокете, удалённом хосте и удалённом хосте с синхронной репликой, и разница покажет стоимость сети и репликации. Только на тестовой базе: он пишет настоящие данные и WAL."),
        ("h", "Что он делает"),
        ("ul", [
            "Создаёт схему `pgload` с одной таблицей (колонка bytea и два индекса), так что каждая вставка обновляет индексы и WAL, как настоящая таблица.",
            "Выполняет `--count` операций через `--workers` параллельных соединений, блоками. Каждая операция — отдельная транзакция (autocommit), поэтому каждая вставка платит полный commit вместе с ожиданием синхронной реплики.",
            "Режимы: `insert`, `select` (случайные чтения диапазонов), `mixed` с `--read-ratio`.",
            "После каждого блока и в конце выводит: операции в секунду, среднее, задержку p50/p95/p99/max, записанные МБ, ошибки.",
            "Параметры соединения **только из переменных окружения libpq** (`PGHOST`, `PGUSER`, `PGDATABASE`, пароль через `~/.pgpass`), так что ничего секретного нет ни в скрипте, ни в истории shell.",
        ]),
        ("h", "Как запустить сравнение"),
        ("code", "run"),
        ("code", "out"),
        ("h", "Что менять — по одному параметру за раз"),
        ("table", [
            ["Настройка", "Что показывает"],
            ["Unix-сокет vs. TCP на localhost vs. удалённый хост", "чистую сетевую стоимость одного commit или запроса"],
            ["`synchronous_commit` on / off / `remote_write` / `remote_apply`", "стоимость надёжности и ожидания реплики"],
            ["Асинхронная vs. синхронная реплика (`synchronous_standby_names`)", "каждый commit ждёт полного обмена с репликой"],
            ["`wal_compression`, `max_wal_size`, `checkpoint_timeout`", "объём WAL и пики checkpoint (смотрите на p99/max)"],
            ["`-s` маленький (2 кБ) vs. большой (512 кБ)", "ограничение задержкой vs. ограничение полосой"],
            ["`-w` 8 → 32 → 128", "где пропускная способность перестаёт расти, а задержка резко растёт"],
        ]),
        ("code", "watch"),
        ("h", "Как читать результаты"),
        ("ul", [
            "**Маленькие блоки:** задержка ≈ сетевой обмен + commit (fsync). С синхронной репликой добавляется обмен с репликой. Несколько миллисекунд на операцию для удалённой базы — нормально, но Odoo делает сотни мелких операций на один клик, и они складываются.",
            "**Большие блоки:** пропускную способность ограничивают полоса и WAL. `wal_compression` может помочь, а решают диски мастера и реплики.",
            "**p99/max сильно выше среднего:** checkpoint, autovacuum или реплика, которая не успевает. Сравните с `pg_stat_wal` и `replay_lag`.",
            "**Больше воркеров, та же пропускная способность:** достигнуто узкое место, и новые соединения только добавляют ожидание.",
            "В нашем проекте удалённый вариант был заметно медленнее на каждую операцию, и инструмент показал, какую часть даёт сеть, а какую — настройки PostgreSQL.",
        ]),
        ("h", "Безопасность"),
        ("ul", [
            "Никогда не запускайте его «на минутку» на продакшене: 20 000 × 64 кБ — это около 1,3 ГБ данных и столько же WAL, которые реплицируются и попадают в следующие бэкапы.",
            "Используйте отдельную базу (`createdb loadtest`) или копию на stage, а после теста — `--drop`.",
            "Не пишите `PGPASSWORD` в скрипты в репозитории; используйте `~/.pgpass` (chmod 600) или peer-аутентификацию через сокет.",
        ]),
        ("h", "Код"),
        ("p", "Один файл, единственная зависимость — `psycopg2`. Это почищенная версия внутреннего инструмента: правильные перцентили вместо среднего от средних, один пул потоков, смешанный режим, очистка, никаких секретов."),
        ("code", "src"),
        ("links", "Ссылки"),
    ],
}
