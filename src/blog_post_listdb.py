# Статья 27: list_db = False остановил queue_job (jobrunner не может получить список баз) – db_name, несколько баз,
# dbfilter, старая версия queue_job. Случай с прод-сервера (Odoo 14, обезличено), код проверен по OCA/queue и odoo/odoo
# 14.0–18.0 (2026-11-17). Все 6 языков.

LISTDB = {
    "slug": "odoo-list-db-false-db-name-queue-job-jobrunner",
    "date": "2026-11-17",
    "tags": ["Odoo", "queue_job", "Security", "Configuration"],
    "code": {
        "log": ("Odoo log · every 5 seconds after list_db = False (paths shortened)", """ERROR ? odoo.addons.queue_job.jobrunner.runner: exception: sleeping 5s and retrying
Traceback (most recent call last):
  File ".../queue_job/jobrunner/runner.py", line 501, in run
    self.initialize_databases()
  File ".../queue_job/jobrunner/runner.py", line 410, in initialize_databases
    for db_name in self.get_db_names():
  File ".../queue_job/jobrunner/runner.py", line 396, in get_db_names
    db_names = odoo.service.db.exp_list(True)
  File ".../odoo/service/db.py", line 423, in exp_list
    raise odoo.exceptions.AccessDenied()
odoo.exceptions.AccessDenied: Access Denied"""),
        "sql": ("SQL · is the queue standing still?", """SELECT state, count(*), min(date_created) AS oldest
  FROM queue_job WHERE state IN ('pending', 'enqueued', 'started') GROUP BY state;
-- pending jobs hours old + nothing 'done' since then = the job runner is not dispatching"""),
        "why": ("python · why: two functions in odoo/service/db.py (Odoo 14–18) and queue_job", """def exp_list(document=False):            # the RPC method behind /web/database/list
    if not odoo.tools.config['list_db']:
        raise odoo.exceptions.AccessDenied()   # <- list_db = False
    return list_dbs()

def list_dbs(force=False):
    if not odoo.tools.config['list_db'] and not force:
        raise odoo.exceptions.AccessDenied()
    if not odoo.tools.config['dbfilter'] and odoo.tools.config['db_name']:
        # without dbfilter, db_name is used "as comma separated list of exposed databases"
        return sorted(db.strip() for db in odoo.tools.config['db_name'].split(','))
    ...                                        # otherwise: ask PostgreSQL

# queue_job/jobrunner/runner.py
def get_db_names(self):
    if config["db_name"]:
        db_names = config["db_name"].split(",")      # note: no strip()
    else:
        db_names = odoo.service.db.exp_list(True)    # OLD versions  -> AccessDenied with list_db = False
        # db_names = odoo.service.db.list_dbs(True)  # current OCA 14.0–18.0 -> force=True, works"""),
        "conf": ("odoo.conf · the fix", """[options]
list_db = False          ; database manager and /web/database/list closed
db_name = prod           ; the job runner knows the database without asking for the list

; several databases: comma separated, NO spaces (queue_job splits on "," without strip)
; db_name = prod,stage_copy

; several databases + choose by host name (subdomain = database name):
; db_name = acme,globex
; dbfilter = ^%d$        ; acme.erp.example.com -> acme, globex.erp.example.com -> globex"""),
        "check": ("bash · after the restart", """sudo systemctl restart odoo
grep -c 'jobrunner.runner: exception' /var/log/odoo/odoo.log     # must stop growing
grep 'queue_job.jobrunner' /var/log/odoo/odoo.log | tail -3       # "database connections ready", "queue job runner ready for db prod"
# and the SQL above: pending -> 0, new rows in 'done'"""),
    },
    "links": [
        ("Blog: password protection for the database manager", "@blog:nginx-apache-password-protect-odoo-database-manager"),
        ("Blog: nginx security audit in front of Odoo", "@blog:nginx-security-audit-odoo-hsts-cookies-x-frame-options"),
        ("Blog: Odoo after a year in production – perimeter, housekeeping, monitoring", "@blog:odoo-production-hardening-housekeeping-monitoring"),
        ("Blog: Telegram bot for Odoo admins (/jobs found the stuck queue)", "@blog:telegram-bot-odoo-monitoring-deploy-stage-copy"),
        ("OCA queue – jobrunner/runner.py", "https://github.com/OCA/queue/blob/17.0/queue_job/jobrunner/runner.py"),
        ("odoo/service/db.py (list_dbs)", "https://github.com/odoo/odoo/blob/17.0/odoo/service/db.py"),
    ],
    "t": {},
}


def _d(title, summary, intro, note, h, case_p, why_p, why_ul, fix_ul, multi_ul, closing, links):
    return {"title": title, "summary": summary, "body": [
        ("p", intro), ("note", note),
        ("h", h[0]), ("p", case_p), ("code", "log"), ("code", "sql"),
        ("h", h[1]), ("p", why_p), ("code", "why"), ("ul", why_ul),
        ("h", h[2]), ("code", "conf"), ("ul", fix_ul), ("code", "check"),
        ("h", h[3]), ("ul", multi_ul),
        ("h", h[4]), ("p", closing),
        ("links", links)]}


LISTDB["t"]["en"] = _d(
    "list_db = False stopped queue_job: why Odoo then needs db_name (and how to list several databases)",
    "We closed the Odoo database manager with list_db = False – and the OCA queue_job runner stopped: jobs stayed pending for hours, the log showed AccessDenied every 5 seconds. Why it happens, the fix with db_name, several databases (comma separated, without spaces), dbfilter, and why updating queue_job also helps.",
    "`list_db = False` is a standard hardening step: it hides the database manager and the database list. On one production server it had a side effect that nobody noticed for a night: background jobs of OCA `queue_job` were no longer executed. Our Telegram bot showed it in `/jobs` the next morning: 25 jobs pending since 22:30, the last finished job at 20:24.",
    "Short version: older `queue_job` versions ask Odoo for the list of databases with `exp_list()`, which raises `AccessDenied` when `list_db = False`. Fix: set `db_name` in `odoo.conf` (several databases comma separated, without spaces) and restart Odoo – or update `queue_job`: current OCA versions use `list_dbs(force=True)`, which works with `list_db = False`.",
    ["The case", "Why it happens", "The fix", "Several databases", "Conclusion"],
    "Odoo 14, OCA queue_job, one database. Yesterday evening `list_db = False` was added and Odoo restarted. The web client and the users kept working – only the job queue stood still. In the log, every 5 seconds:",
    "The job runner starts inside the Odoo server and first needs to know which databases to serve. If `db_name` is empty, it asks Odoo for the list – and in older versions it does that through the same function that serves the database manager:",
    ["`exp_list()` is the public RPC method for the database list. With `list_db = False` it refuses everybody – including the job runner inside the server.",
     "`list_dbs(force=True)` is the internal function: `force=True` ignores `list_db`. The current OCA branches 14.0–18.0 of `queue_job` call exactly this, so with an up-to-date `queue_job` the problem does not occur. The installation in our case had an older copy of the module.",
     "If `db_name` is set, the job runner does not ask at all – it takes the names from the configuration."],
    ["`db_name` is the database (or databases) Odoo works with; on the command line `-d` / `--database`.",
     "Restart is required – the job runner reads the configuration at start.",
     "With one database `db_name` also helps the web client: no database selection, `/web/login` opens the right database directly.",
     "Better still: update `queue_job` to the current version of your Odoo series – then it no longer depends on `list_db`, and you get the other fixes too."],
    ["**Comma separated, without spaces**: `db_name = prod,stage_copy`. Odoo itself strips spaces, `queue_job` does not – `prod, stage_copy` makes the job runner look for a database named ` stage_copy` with a leading space.",
     "**Which database does the browser get?** With `list_db = False` there is no selector. Use `dbfilter`: `^%d$` takes the first part of the host name (`acme.erp.example.com` → `acme`), `^%h$` the full host name. One host name per database, one certificate per name (or a wildcard).",
     "**Careful with dbfilter + db_name**: if `dbfilter` is set, Odoo's own `list_dbs()` ignores the `db_name` list and asks PostgreSQL, filtered by `dbfilter`. The job runner still takes the list from `db_name`. Keep both consistent.",
     "**Copies on the same PostgreSQL** (a stage copy, an old test database) that are not in `db_name` are not served by the job runner – usually exactly what you want on production."],
    "Closing the database manager is right, but after any change to `list_db`, `db_name` or `dbfilter` check the job queue, not only the login page: pending jobs that do not move are the symptom. And keep `queue_job` up to date – the current version does not have this problem at all. We check this as part of Odoo operations for companies in Germany, Austria and Switzerland.",
    "Links")

LISTDB["t"]["de"] = _d(
    "list_db = False hat queue_job gestoppt: warum Odoo dann db_name braucht (und wie man mehrere Datenbanken angibt)",
    "Wir haben den Odoo-Datenbankmanager mit list_db = False geschlossen – und der Job-Runner von OCA queue_job blieb stehen: Jobs stundenlang pending, im Log alle 5 Sekunden AccessDenied. Warum das passiert, die Lösung mit db_name, mehrere Datenbanken (kommagetrennt, ohne Leerzeichen), dbfilter und warum ein Update von queue_job ebenfalls hilft.",
    "`list_db = False` ist ein Standardschritt der Härtung: es versteckt den Datenbankmanager und die Datenbankliste. Auf einem Produktivserver hatte es eine Nebenwirkung, die eine Nacht lang niemand bemerkte: Hintergrundjobs von OCA `queue_job` wurden nicht mehr ausgeführt. Unser Telegram-Bot zeigte es am nächsten Morgen in `/jobs`: 25 Jobs pending seit 22:30, der letzte erledigte Job um 20:24.",
    "Kurzfassung: ältere Versionen von `queue_job` holen die Datenbankliste über `exp_list()`, das bei `list_db = False` `AccessDenied` wirft. Lösung: `db_name` in `odoo.conf` setzen (mehrere Datenbanken kommagetrennt, ohne Leerzeichen) und Odoo neu starten – oder `queue_job` aktualisieren: aktuelle OCA-Versionen nutzen `list_dbs(force=True)`, das mit `list_db = False` funktioniert.",
    ["Der Fall", "Warum das passiert", "Die Lösung", "Mehrere Datenbanken", "Fazit"],
    "Odoo 14, OCA queue_job, eine Datenbank. Am Vorabend wurde `list_db = False` gesetzt und Odoo neu gestartet. Web-Client und Anwender arbeiteten weiter – nur die Job-Warteschlange stand. Im Log alle 5 Sekunden:",
    "Der Job-Runner startet im Odoo-Server und muss zuerst wissen, welche Datenbanken er bedient. Ist `db_name` leer, fragt er Odoo nach der Liste – in älteren Versionen über dieselbe Funktion, die auch den Datenbankmanager bedient:",
    ["`exp_list()` ist die öffentliche RPC-Methode für die Datenbankliste. Mit `list_db = False` verweigert sie jedem die Antwort – auch dem Job-Runner im Server.",
     "`list_dbs(force=True)` ist die interne Funktion: `force=True` ignoriert `list_db`. Die aktuellen OCA-Zweige 14.0–18.0 von `queue_job` rufen genau diese auf; mit aktuellem `queue_job` tritt das Problem also nicht auf. Die Installation in unserem Fall hatte eine ältere Kopie des Moduls.",
     "Ist `db_name` gesetzt, fragt der Job-Runner gar nicht – er nimmt die Namen aus der Konfiguration."],
    ["`db_name` ist die Datenbank (oder sind die Datenbanken), mit der Odoo arbeitet; auf der Kommandozeile `-d` / `--database`.",
     "Ein Neustart ist nötig – der Job-Runner liest die Konfiguration beim Start.",
     "Bei einer Datenbank hilft `db_name` auch dem Web-Client: keine Datenbankauswahl, `/web/login` öffnet direkt die richtige Datenbank.",
     "Noch besser: `queue_job` auf die aktuelle Version Ihrer Odoo-Serie aktualisieren – dann hängt es nicht mehr von `list_db` ab, und man bekommt die übrigen Korrekturen dazu."],
    ["**Kommagetrennt, ohne Leerzeichen**: `db_name = prod,stage_copy`. Odoo selbst entfernt Leerzeichen, `queue_job` nicht – `prod, stage_copy` lässt den Job-Runner eine Datenbank namens ` stage_copy` mit führendem Leerzeichen suchen.",
     "**Welche Datenbank bekommt der Browser?** Mit `list_db = False` gibt es keine Auswahl. Dafür `dbfilter`: `^%d$` nimmt den ersten Teil des Hostnamens (`acme.erp.example.com` → `acme`), `^%h$` den ganzen Hostnamen. Ein Hostname pro Datenbank, ein Zertifikat pro Name (oder ein Wildcard-Zertifikat).",
     "**Vorsicht bei dbfilter + db_name**: ist `dbfilter` gesetzt, ignoriert Odoos eigenes `list_dbs()` die `db_name`-Liste und fragt PostgreSQL, gefiltert mit `dbfilter`. Der Job-Runner nimmt die Liste trotzdem aus `db_name`. Beides konsistent halten.",
     "**Kopien auf demselben PostgreSQL** (eine Stage-Kopie, eine alte Testdatenbank), die nicht in `db_name` stehen, bedient der Job-Runner nicht – auf Produktion meist genau das Gewünschte."],
    "Den Datenbankmanager zu schließen ist richtig, aber nach jeder Änderung an `list_db`, `db_name` oder `dbfilter` die Job-Warteschlange prüfen, nicht nur die Login-Seite: Jobs, die pending bleiben, sind das Symptom. Und `queue_job` aktuell halten – die aktuelle Version hat das Problem gar nicht. Das prüfen wir als Teil des Odoo-Betriebs für Unternehmen in Deutschland, Österreich und der Schweiz.",
    "Links")

LISTDB["t"]["fr"] = _d(
    "list_db = False a arrêté queue_job : pourquoi Odoo a alors besoin de db_name (et comment indiquer plusieurs bases)",
    "Nous avons fermé le gestionnaire de bases d'Odoo avec list_db = False – et le job runner d'OCA queue_job s'est arrêté : jobs en pending pendant des heures, AccessDenied dans le journal toutes les 5 secondes. Pourquoi, la correction avec db_name, plusieurs bases (séparées par des virgules, sans espaces), dbfilter, et pourquoi mettre à jour queue_job aide aussi.",
    "`list_db = False` est une étape classique de durcissement : il masque le gestionnaire de bases et la liste des bases. Sur un serveur de production, il a eu un effet secondaire que personne n'a vu pendant une nuit : les jobs de fond d'OCA `queue_job` n'étaient plus exécutés. Notre bot Telegram l'a montré le lendemain matin dans `/jobs` : 25 jobs en pending depuis 22 h 30, le dernier job terminé à 20 h 24.",
    "En bref : les anciennes versions de `queue_job` demandent la liste des bases via `exp_list()`, qui lève `AccessDenied` avec `list_db = False`. Correction : définir `db_name` dans `odoo.conf` (plusieurs bases séparées par des virgules, sans espaces) et redémarrer Odoo – ou mettre à jour `queue_job` : les versions OCA actuelles utilisent `list_dbs(force=True)`, qui fonctionne avec `list_db = False`.",
    ["Le cas", "Pourquoi", "La correction", "Plusieurs bases", "Conclusion"],
    "Odoo 14, OCA queue_job, une seule base. La veille au soir, `list_db = False` a été ajouté et Odoo redémarré. Le client web et les utilisateurs ont continué – seule la file de jobs était à l'arrêt. Dans le journal, toutes les 5 secondes :",
    "Le job runner démarre dans le serveur Odoo et doit d'abord savoir quelles bases servir. Si `db_name` est vide, il demande la liste à Odoo – et dans les anciennes versions, il le fait par la même fonction que celle du gestionnaire de bases :",
    ["`exp_list()` est la méthode RPC publique de la liste des bases. Avec `list_db = False`, elle refuse tout le monde – y compris le job runner dans le serveur.",
     "`list_dbs(force=True)` est la fonction interne : `force=True` ignore `list_db`. Les branches OCA actuelles 14.0–18.0 de `queue_job` appellent justement celle-ci ; avec un `queue_job` à jour, le problème n'apparaît donc pas. L'installation de notre cas avait une copie plus ancienne du module.",
     "Si `db_name` est défini, le job runner ne demande rien – il prend les noms dans la configuration."],
    ["`db_name` est la base (ou les bases) avec laquelle Odoo travaille ; en ligne de commande `-d` / `--database`.",
     "Un redémarrage est nécessaire – le job runner lit la configuration au démarrage.",
     "Avec une seule base, `db_name` aide aussi le client web : pas de choix de base, `/web/login` ouvre directement la bonne base.",
     "Encore mieux : mettre `queue_job` à jour pour votre série d'Odoo – il ne dépend alors plus de `list_db`, et vous avez les autres corrections en plus."],
    ["**Séparées par des virgules, sans espaces** : `db_name = prod,stage_copy`. Odoo retire lui-même les espaces, `queue_job` non – avec `prod, stage_copy`, le job runner cherche une base nommée ` stage_copy` avec un espace au début.",
     "**Quelle base pour le navigateur ?** Avec `list_db = False`, il n'y a pas de sélecteur. Utiliser `dbfilter` : `^%d$` prend la première partie du nom d'hôte (`acme.erp.example.com` → `acme`), `^%h$` le nom d'hôte complet. Un nom d'hôte par base, un certificat par nom (ou un wildcard).",
     "**Attention à dbfilter + db_name** : si `dbfilter` est défini, `list_dbs()` d'Odoo ignore la liste `db_name` et interroge PostgreSQL avec le filtre `dbfilter`. Le job runner, lui, prend toujours la liste de `db_name`. Garder les deux cohérents.",
     "**Les copies sur le même PostgreSQL** (une copie de stage, une ancienne base de test) qui ne sont pas dans `db_name` ne sont pas servies par le job runner – en production, c'est généralement ce que l'on veut."],
    "Fermer le gestionnaire de bases est juste, mais après tout changement de `list_db`, `db_name` ou `dbfilter`, vérifiez la file de jobs, pas seulement la page de connexion : des jobs qui restent en pending sont le symptôme. Et gardez `queue_job` à jour – la version actuelle n'a pas ce problème. Nous le vérifions dans le cadre de l'exploitation d'Odoo pour des entreprises en Allemagne, en Autriche et en Suisse.",
    "Liens")

LISTDB["t"]["el"] = _d(
    "Το list_db = False σταμάτησε το queue_job: γιατί το Odoo χρειάζεται τότε db_name (και πώς δηλώνονται πολλές βάσεις)",
    "Κλείσαμε τον διαχειριστή βάσεων του Odoo με list_db = False – και ο job runner του OCA queue_job σταμάτησε: εργασίες σε pending για ώρες, AccessDenied στο log κάθε 5 δευτερόλεπτα. Γιατί συμβαίνει, η λύση με db_name, πολλές βάσεις (με κόμμα, χωρίς κενά), dbfilter, και γιατί βοηθά και η ενημέρωση του queue_job.",
    "Το `list_db = False` είναι συνηθισμένο βήμα θωράκισης: κρύβει τον διαχειριστή βάσεων και τη λίστα βάσεων. Σε έναν server παραγωγής είχε μια παρενέργεια που κανείς δεν πρόσεξε για μία νύχτα: οι εργασίες παρασκηνίου του OCA `queue_job` δεν εκτελούνταν πια. Το Telegram bot μας το έδειξε το επόμενο πρωί στο `/jobs`: 25 εργασίες σε pending από τις 22:30, η τελευταία ολοκληρωμένη στις 20:24.",
    "Συνοπτικά: παλαιότερες εκδόσεις του `queue_job` ζητούν τη λίστα βάσεων με `exp_list()`, που πετά `AccessDenied` όταν `list_db = False`. Λύση: ορίστε `db_name` στο `odoo.conf` (πολλές βάσεις με κόμμα, χωρίς κενά) και επανεκκινήστε το Odoo – ή ενημερώστε το `queue_job`: οι τρέχουσες εκδόσεις του OCA χρησιμοποιούν `list_dbs(force=True)`, που λειτουργεί με `list_db = False`.",
    ["Η περίπτωση", "Γιατί συμβαίνει", "Η λύση", "Πολλές βάσεις", "Συμπέρασμα"],
    "Odoo 14, OCA queue_job, μία βάση. Το προηγούμενο βράδυ προστέθηκε `list_db = False` και έγινε επανεκκίνηση. Ο web client και οι χρήστες συνέχισαν να δουλεύουν – μόνο η ουρά εργασιών σταμάτησε. Στο log, κάθε 5 δευτερόλεπτα:",
    "Ο job runner ξεκινά μέσα στον server του Odoo και πρώτα πρέπει να ξέρει ποιες βάσεις εξυπηρετεί. Αν το `db_name` είναι κενό, ζητά τη λίστα από το Odoo – και στις παλαιότερες εκδόσεις μέσω της ίδιας συνάρτησης που εξυπηρετεί τον διαχειριστή βάσεων:",
    ["Το `exp_list()` είναι η δημόσια μέθοδος RPC για τη λίστα βάσεων. Με `list_db = False` αρνείται σε όλους – και στον job runner μέσα στον server.",
     "Το `list_dbs(force=True)` είναι η εσωτερική συνάρτηση: το `force=True` αγνοεί το `list_db`. Οι τρέχοντες κλάδοι OCA 14.0–18.0 του `queue_job` καλούν ακριβώς αυτήν, οπότε με ενημερωμένο `queue_job` το πρόβλημα δεν εμφανίζεται. Η εγκατάσταση της περίπτωσής μας είχε παλαιότερο αντίγραφο του module.",
     "Αν έχει οριστεί `db_name`, ο job runner δεν ρωτά καθόλου – παίρνει τα ονόματα από τη ρύθμιση."],
    ["Το `db_name` είναι η βάση (ή οι βάσεις) με την οποία δουλεύει το Odoo· στη γραμμή εντολών `-d` / `--database`.",
     "Χρειάζεται επανεκκίνηση – ο job runner διαβάζει τη ρύθμιση κατά την εκκίνηση.",
     "Με μία βάση το `db_name` βοηθά και τον web client: καμία επιλογή βάσης, το `/web/login` ανοίγει απευθείας τη σωστή βάση.",
     "Ακόμη καλύτερα: ενημερώστε το `queue_job` στην τρέχουσα έκδοση της σειράς του Odoo σας – τότε δεν εξαρτάται πια από το `list_db`, και παίρνετε και τις άλλες διορθώσεις."],
    ["**Με κόμμα, χωρίς κενά**: `db_name = prod,stage_copy`. Το ίδιο το Odoo αφαιρεί τα κενά, το `queue_job` όχι – με `prod, stage_copy` ο job runner ψάχνει βάση με όνομα ` stage_copy` με κενό στην αρχή.",
     "**Ποια βάση παίρνει ο browser;** Με `list_db = False` δεν υπάρχει επιλογέας. Χρησιμοποιήστε `dbfilter`: το `^%d$` παίρνει το πρώτο μέρος του ονόματος host (`acme.erp.example.com` → `acme`), το `^%h$` ολόκληρο το όνομα host. Ένα όνομα host ανά βάση, ένα πιστοποιητικό ανά όνομα (ή wildcard).",
     "**Προσοχή στο dbfilter + db_name**: αν έχει οριστεί `dbfilter`, το `list_dbs()` του Odoo αγνοεί τη λίστα `db_name` και ρωτά την PostgreSQL με φίλτρο το `dbfilter`. Ο job runner όμως παίρνει πάντα τη λίστα από το `db_name`. Κρατήστε τα συνεπή.",
     "**Αντίγραφα στην ίδια PostgreSQL** (αντίγραφο stage, παλιά βάση δοκιμών) που δεν είναι στο `db_name` δεν εξυπηρετούνται από τον job runner – στην παραγωγή συνήθως ακριβώς αυτό θέλουμε."],
    "Το κλείσιμο του διαχειριστή βάσεων είναι σωστό, αλλά μετά από κάθε αλλαγή στα `list_db`, `db_name` ή `dbfilter` ελέγξτε την ουρά εργασιών, όχι μόνο τη σελίδα σύνδεσης: εργασίες που μένουν σε pending είναι το σύμπτωμα. Και κρατήστε το `queue_job` ενημερωμένο – η τρέχουσα έκδοση δεν έχει καθόλου αυτό το πρόβλημα. Το ελέγχουμε στο πλαίσιο της λειτουργίας Odoo για εταιρείες στη Γερμανία, την Αυστρία και την Ελβετία.",
    "Σύνδεσμοι")

LISTDB["t"]["uk"] = _d(
    "list_db = False зупинив queue_job: чому тоді Odoo потрібен db_name (і як вказати кілька баз)",
    "Ми закрили менеджер баз Odoo через list_db = False – і job runner з OCA queue_job зупинився: завдання годинами в pending, у лозі кожні 5 секунд AccessDenied. Чому так, виправлення через db_name, кілька баз (через кому, без пробілів), dbfilter і чому допомагає також оновлення queue_job.",
    "`list_db = False` – стандартний крок захисту: він ховає менеджер баз і список баз. На одному продакшн-сервері він мав побічний ефект, якого ніхто не помітив за ніч: фонові завдання OCA `queue_job` перестали виконуватися. Наш Telegram-бот показав це вранці в `/jobs`: 25 завдань у pending з 22:30, останнє виконане – о 20:24.",
    "Коротко: старі версії `queue_job` отримують список баз через `exp_list()`, який при `list_db = False` кидає `AccessDenied`. Виправлення: вказати `db_name` в `odoo.conf` (кілька баз – через кому, без пробілів) і перезапустити Odoo – або оновити `queue_job`: актуальні версії OCA викликають `list_dbs(force=True)`, що працює з `list_db = False`.",
    ["Випадок", "Чому так", "Виправлення", "Кілька баз", "Висновок"],
    "Odoo 14, OCA queue_job, одна база. Напередодні ввечері додали `list_db = False` і перезапустили Odoo. Веб-клієнт і користувачі працювали далі – стояла лише черга завдань. У лозі кожні 5 секунд:",
    "Job runner стартує всередині сервера Odoo і спершу має знати, які бази обслуговувати. Якщо `db_name` порожній, він питає список у Odoo – а в старих версіях робить це через ту саму функцію, що обслуговує менеджер баз:",
    ["`exp_list()` – публічний RPC-метод списку баз. З `list_db = False` він відмовляє всім – і job runner'у всередині сервера теж.",
     "`list_dbs(force=True)` – внутрішня функція: `force=True` ігнорує `list_db`. Актуальні гілки OCA 14.0–18.0 `queue_job` викликають саме її, тож з оновленим `queue_job` проблеми немає. В інсталяції з нашого випадку була старіша копія модуля.",
     "Якщо `db_name` заданий, job runner нічого не питає – бере імена з конфігурації."],
    ["`db_name` – база (або бази), з якою працює Odoo; у командному рядку `-d` / `--database`.",
     "Потрібен перезапуск – job runner читає конфігурацію при старті.",
     "З однією базою `db_name` допомагає й веб-клієнту: без вибору бази, `/web/login` одразу відкриває потрібну.",
     "Ще краще: оновити `queue_job` до актуальної версії вашої серії Odoo – тоді він не залежить від `list_db`, і ви отримаєте інші виправлення."],
    ["**Через кому, без пробілів**: `db_name = prod,stage_copy`. Сам Odoo пробіли прибирає, а `queue_job` – ні: з `prod, stage_copy` job runner шукатиме базу ` stage_copy` з пробілом на початку.",
     "**Яку базу отримає браузер?** З `list_db = False` вибору немає. Потрібен `dbfilter`: `^%d$` бере першу частину імені хоста (`acme.erp.example.com` → `acme`), `^%h$` – повне ім'я хоста. Одне ім'я хоста на базу, сертифікат на кожне ім'я (або wildcard).",
     "**Обережно з dbfilter + db_name**: якщо заданий `dbfilter`, власний `list_dbs()` Odoo ігнорує список `db_name` і питає PostgreSQL з фільтром `dbfilter`. А job runner усе одно бере список з `db_name`. Тримайте їх узгодженими.",
     "**Копії на тому самому PostgreSQL** (копія stage, стара тестова база), яких немає в `db_name`, job runner не обслуговує – на продакшні зазвичай саме це й потрібно."],
    "Закрити менеджер баз – правильно, але після кожної зміни `list_db`, `db_name` чи `dbfilter` перевіряйте чергу завдань, а не лише сторінку входу: завдання, що не виходять з pending, – це симптом. І тримайте `queue_job` оновленим – актуальна версія такої проблеми не має. Ми перевіряємо це в межах супроводу Odoo для компаній у Німеччині, Австрії та Швейцарії.",
    "Посилання")

LISTDB["t"]["ru"] = _d(
    "list_db = False остановил queue_job: почему тогда Odoo нужен db_name (и как указать несколько баз)",
    "Мы закрыли менеджер баз Odoo через list_db = False – и job runner из OCA queue_job остановился: задачи часами в pending, в логе каждые 5 секунд AccessDenied. Почему так, исправление через db_name, несколько баз (через запятую, без пробелов), dbfilter и почему помогает и обновление queue_job.",
    "`list_db = False` – стандартный шаг защиты: он прячет менеджер баз и список баз. На одном продакшн-сервере у него оказался побочный эффект, которого никто не заметил за ночь: фоновые задачи OCA `queue_job` перестали выполняться. Наш Telegram-бот показал это утром в `/jobs`: 25 задач в pending с 22:30, последняя выполненная – в 20:24.",
    "Коротко: старые версии `queue_job` получают список баз через `exp_list()`, который при `list_db = False` выбрасывает `AccessDenied`. Исправление: указать `db_name` в `odoo.conf` (несколько баз – через запятую, без пробелов) и перезапустить Odoo – или обновить `queue_job`: актуальные версии OCA вызывают `list_dbs(force=True)`, который работает с `list_db = False`.",
    ["Случай", "Почему так", "Исправление", "Несколько баз", "Итог"],
    "Odoo 14, OCA queue_job, одна база. Накануне вечером добавили `list_db = False` и перезапустили Odoo. Веб-клиент и пользователи работали дальше – стояла только очередь задач. В логе каждые 5 секунд:",
    "Job runner стартует внутри сервера Odoo и сначала должен знать, какие базы обслуживать. Если `db_name` пустой, он спрашивает список у Odoo – а в старых версиях делает это через ту же функцию, что обслуживает менеджер баз:",
    ["`exp_list()` – публичный RPC-метод списка баз. С `list_db = False` он отказывает всем – и job runner'у внутри сервера тоже.",
     "`list_dbs(force=True)` – внутренняя функция: `force=True` игнорирует `list_db`. Актуальные ветки OCA 14.0–18.0 `queue_job` вызывают именно её, так что с обновлённым `queue_job` проблемы нет. В инсталляции из нашего случая была более старая копия модуля.",
     "Если `db_name` задан, job runner ничего не спрашивает – берёт имена из конфигурации."],
    ["`db_name` – база (или базы), с которой работает Odoo; в командной строке `-d` / `--database`.",
     "Нужен перезапуск – job runner читает конфигурацию при старте.",
     "С одной базой `db_name` помогает и веб-клиенту: без выбора базы, `/web/login` сразу открывает нужную.",
     "Ещё лучше: обновить `queue_job` до актуальной версии вашей серии Odoo – тогда он не зависит от `list_db`, и вы получите остальные исправления."],
    ["**Через запятую, без пробелов**: `db_name = prod,stage_copy`. Сам Odoo пробелы убирает, а `queue_job` – нет: с `prod, stage_copy` job runner будет искать базу ` stage_copy` с пробелом в начале.",
     "**Какую базу получит браузер?** С `list_db = False` выбора нет. Нужен `dbfilter`: `^%d$` берёт первую часть имени хоста (`acme.erp.example.com` → `acme`), `^%h$` – полное имя хоста. Одно имя хоста на базу, сертификат на каждое имя (или wildcard).",
     "**Осторожно с dbfilter + db_name**: если задан `dbfilter`, собственный `list_dbs()` Odoo игнорирует список `db_name` и спрашивает PostgreSQL с фильтром `dbfilter`. А job runner всё равно берёт список из `db_name`. Держите их согласованными.",
     "**Копии на том же PostgreSQL** (копия stage, старая тестовая база), которых нет в `db_name`, job runner не обслуживает – на продакшне обычно именно это и нужно."],
    "Закрыть менеджер баз – правильно, но после каждого изменения `list_db`, `db_name` или `dbfilter` проверяйте очередь задач, а не только страницу входа: задачи, которые не выходят из pending, – это симптом. И держите `queue_job` обновлённым – в актуальной версии этой проблемы нет. Мы проверяем это в рамках сопровождения Odoo для компаний в Германии, Австрии и Швейцарии.",
    "Ссылки")
