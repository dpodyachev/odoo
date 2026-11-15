# Статья 13: "could not serialize access due to concurrent update" в Odoo – что это, когда опасно, как найти и убрать. Все 6 языков.

SERIALIZE = {
    "slug": "odoo-could-not-serialize-access-concurrent-update",
    "date": "2026-11-15",
    "tags": ["Odoo 17", "PostgreSQL", "Concurrency", "Cron", "queue_job"],
    "code": {
        "log": ("log · PostgreSQL and Odoo", """# PostgreSQL log
ERROR:  could not serialize access due to concurrent update
STATEMENT:  UPDATE "product_template" SET "write_date"=..., "write_uid"=... WHERE id IN (4711)

# Odoo log (odoo/service/model.py, retrying) – the same moment
INFO mydb odoo.service.model: SERIALIZATION_FAILURE, 4 tries left, try again in 1.3127 sec...
INFO mydb odoo.service.model: SERIALIZATION_FAILURE, 3 tries left, try again in 2.8410 sec...

# only this one is a real problem:
INFO mydb odoo.service.model: SERIALIZATION_FAILURE, maximum number of tries reached!"""),
        "demo": ("psql · reproduce in two sessions", """-- session A                                   -- session B
BEGIN ISOLATION LEVEL REPEATABLE READ;           BEGIN ISOLATION LEVEL REPEATABLE READ;
SELECT 1;  -- snapshot taken                     SELECT 1;  -- snapshot taken
UPDATE res_partner SET comment='A' WHERE id=7;
                                                 UPDATE res_partner SET comment='B' WHERE id=7;
                                                 -- waits for A ...
COMMIT;
                                                 -- ERROR: could not serialize access
                                                 --        due to concurrent update"""),
        "find": ("bash · who collides with whom", """# how often, and when (per hour)
grep "SERIALIZATION_FAILURE" /var/log/odoo/odoo.log | cut -c1-13 | sort | uniq -c | tail -24

# what was running at the same time: cron starts/ends around a failure
grep -E "SERIALIZATION_FAILURE|Starting job|Job done|Job .* failed" /var/log/odoo/odoo.log | less

# PostgreSQL: log lock waits with the application and the PID
#   postgresql.conf:
#   log_lock_waits = on
#   deadlock_timeout = 1s
#   log_line_prefix = '%m [%p] %a %u@%d '

# long transactions right now (the usual partner of the failures)
psql -d mydb -c "SELECT pid, now()-xact_start AS tx_age, application_name, left(query,100)
                 FROM pg_stat_activity WHERE xact_start IS NOT NULL ORDER BY tx_age DESC LIMIT 10;" """),
        "fix": ("python · custom cron: short transactions, skip locked rows", """def _cron_process(self, batch=200):
    while True:
        # take only rows nobody else is working on right now
        self.env.cr.execute(\"\"\"
            SELECT id FROM my_model
             WHERE state = 'todo'
             ORDER BY id
             LIMIT %s
             FOR UPDATE SKIP LOCKED\"\"\", [batch])
        ids = [r[0] for r in self.env.cr.fetchall()]
        if not ids:
            break
        self.browse(ids)._process()
        self.env.cr.commit()      # short transaction – fewer collisions with users"""),
        "qj": ("odoo.conf · queue_job: one lane for jobs that touch the same records", """[queue_job]
channels = root:4,root.stock:1

# channel "stock" (parent root) also as a record: Job Queue → Channels
# in code: product/stock jobs go through the single lane
#   records.with_delay(channel="root.stock").sync_stock()"""),
    },
    "links": [
        ("PostgreSQL: Repeatable Read isolation level", "https://www.postgresql.org/docs/current/transaction-iso.html#XACT-REPEATABLE-READ"),
        ("Odoo 17 source: odoo/service/model.py (retrying)", "https://github.com/odoo/odoo/blob/17.0/odoo/service/model.py"),
        ("OCA queue_job – channels", "https://github.com/OCA/queue/tree/17.0/queue_job"),
        ("Odoo operations skill for AI agents (Markdown)", "https://2027.pp.ua/skill_odoo.md"),
        ("Blog: Odoo logging cheat sheet", "@blog:odoo-logging-options-cheatsheet"),
        ("Blog: restoring on stage without cron jobs", "@blog:odoo-stage-restore-stop-cron-jobs"),
    ],
    "t": {},
}

SERIALIZE["t"]["en"] = {
    "title": "“could not serialize access due to concurrent update” in Odoo – harmless noise or a real problem?",
    "summary": "What the PostgreSQL error means in Odoo, why Odoo retries it silently, when it becomes a problem for users and crons, how to find who collides with whom – and how to get rid of it.",
    "body": [
        ("p", "The PostgreSQL log is full of `ERROR: could not serialize access due to concurrent update`, users sometimes wait several seconds after “Save”, and now and then a cron fails. What is going on – and do you have to do anything?"),
        ("note", "Short version: Odoo runs every transaction in `REPEATABLE READ` and **repeats** the request automatically up to 5 times. Single errors are normal. A problem only when the log says `maximum number of tries reached` or when they pile up – then two processes keep writing the same records, usually a long cron and the users."),
        ("h", "What the error means"),
        ("p", "Odoo opens every transaction with the isolation level `REPEATABLE READ`: it sees the data as it was at its start. If transaction B wants to change a row that transaction A has changed and committed in the meantime, PostgreSQL refuses – B would overwrite something it has never seen."),
        ("code", "demo"),
        ("h", "What Odoo does with it"),
        ("code", "log"),
        ("ul", [
            "Odoo rolls back, waits a random time (up to 2, 4, 8, 16 s) and runs the **whole request again** – up to 5 attempts (`MAX_TRIES_ON_CONCURRENCY_FAILURE`). The same applies to lock timeouts and deadlocks.",
            "For the user that means: no error, but a click that takes seconds.",
            "Every attempt is an `ERROR` line in the PostgreSQL log – so many such lines are usually just retries that succeeded.",
            "After the 5th failure the user gets an error message; a cron job fails and runs again only at its next scheduled time.",
        ]),
        ("h", "Typical causes"),
        ("ul", [
            "**Long crons** that write many records in one transaction (recomputations, stock/price syncs, report data) while users edit the same records.",
            "**Integrations** (shop, marketplace, warehouse) that update the same products or orders every minute.",
            "**Several queue jobs in parallel** on the same records.",
            "**“Hot” rows** that everybody writes: a counter field on the company or partner, a shared sequence, a parent record whose stored compute field depends on its children.",
            "**Imports** of thousands of rows during working hours.",
        ]),
        ("h", "Finding out who collides with whom"),
        ("code", "find"),
        ("p", "In practice the time pattern gives it away: the failures come in waves exactly when a particular cron or job runs. Then you know which code to look at."),
        ("h", "Getting rid of it"),
        ("ul", [
            "**Shorter transactions:** process crons in batches and commit after each batch; take only free rows with `FOR UPDATE SKIP LOCKED`.",
            "**Different times:** move heavy crons out of working hours, do not start several crons on the same minute.",
            "**One lane for jobs on the same records:** a queue_job channel with capacity 1.",
            "**No hot rows:** do not keep counters on shared records; compute them on demand or in a separate table.",
            "**Check stored compute fields:** a wide `@api.depends` turns a small write into an update of many records.",
            "**Imports** in the evening or via queue_job in small chunks.",
        ]),
        ("code", "fix"),
        ("code", "qj"),
        ("note", "Do not “fix” it by lowering the isolation level or catching the exception in custom code – that turns a visible retry into silently lost updates."),
        ("links", "Links"),
    ],
}

SERIALIZE["t"]["de"] = {
    "title": "„could not serialize access due to concurrent update“ in Odoo – harmloses Rauschen oder echtes Problem?",
    "summary": "Was der PostgreSQL-Fehler in Odoo bedeutet, warum Odoo ihn still wiederholt, wann er für Anwender und Cron-Jobs zum Problem wird, wie man findet, wer mit wem kollidiert – und wie man ihn loswird.",
    "body": [
        ("p", "Das PostgreSQL-Log ist voll mit `ERROR: could not serialize access due to concurrent update`, Anwender warten nach „Speichern“ manchmal mehrere Sekunden, und hin und wieder scheitert ein Cron-Job. Was passiert da – und muss man etwas tun?"),
        ("note", "Kurzfassung: Odoo führt jede Transaktion in `REPEATABLE READ` aus und **wiederholt** die Anfrage automatisch bis zu 5-mal. Einzelne Fehler sind normal. Ein Problem erst, wenn im Log `maximum number of tries reached` steht oder sie sich häufen – dann schreiben zwei Prozesse ständig dieselben Datensätze, meist ein langer Cron-Job und die Anwender."),
        ("h", "Was der Fehler bedeutet"),
        ("p", "Odoo öffnet jede Transaktion mit der Isolationsstufe `REPEATABLE READ`: Sie sieht die Daten so, wie sie bei ihrem Start waren. Will Transaktion B eine Zeile ändern, die Transaktion A inzwischen geändert und festgeschrieben hat, lehnt PostgreSQL ab – B würde etwas überschreiben, das sie nie gesehen hat."),
        ("code", "demo"),
        ("h", "Was Odoo damit macht"),
        ("code", "log"),
        ("ul", [
            "Odoo rollt zurück, wartet eine zufällige Zeit (bis 2, 4, 8, 16 s) und führt die **ganze Anfrage erneut** aus – bis zu 5 Versuche (`MAX_TRIES_ON_CONCURRENCY_FAILURE`). Dasselbe gilt für Lock-Timeouts und Deadlocks.",
            "Für Anwender heißt das: kein Fehler, aber ein Klick, der Sekunden dauert.",
            "Jeder Versuch ist eine `ERROR`-Zeile im PostgreSQL-Log – viele solcher Zeilen sind meist nur erfolgreiche Wiederholungen.",
            "Nach dem 5. Fehlschlag bekommt der Anwender eine Fehlermeldung; ein Cron-Job scheitert und läuft erst zum nächsten geplanten Zeitpunkt wieder.",
        ]),
        ("h", "Typische Ursachen"),
        ("ul", [
            "**Lange Cron-Jobs**, die viele Datensätze in einer Transaktion schreiben (Neuberechnungen, Lager-/Preis-Abgleiche, Berichtsdaten), während Anwender dieselben Datensätze bearbeiten.",
            "**Schnittstellen** (Shop, Marktplatz, Lager), die jede Minute dieselben Produkte oder Aufträge aktualisieren.",
            "**Mehrere Queue-Jobs parallel** auf denselben Datensätzen.",
            "**„Heiße“ Zeilen**, die alle schreiben: ein Zählerfeld am Unternehmen oder Partner, eine gemeinsame Sequenz, ein Elterndatensatz, dessen gespeichertes Compute-Feld von den Kindern abhängt.",
            "**Importe** von Tausenden Zeilen während der Arbeitszeit.",
        ]),
        ("h", "Herausfinden, wer mit wem kollidiert"),
        ("code", "find"),
        ("p", "In der Praxis verrät es das Zeitmuster: Die Fehler kommen in Wellen genau dann, wenn ein bestimmter Cron-Job oder Job läuft. Dann weiß man, welchen Code man ansehen muss."),
        ("h", "Loswerden"),
        ("ul", [
            "**Kürzere Transaktionen:** Cron-Jobs in Paketen verarbeiten und nach jedem Paket committen; mit `FOR UPDATE SKIP LOCKED` nur freie Zeilen nehmen.",
            "**Andere Zeiten:** schwere Cron-Jobs aus der Arbeitszeit verlegen, nicht mehrere auf dieselbe Minute legen.",
            "**Eine Spur für Jobs auf denselben Datensätzen:** ein queue_job-Kanal mit Kapazität 1.",
            "**Keine heißen Zeilen:** keine Zähler an gemeinsamen Datensätzen; bei Bedarf berechnen oder in einer eigenen Tabelle führen.",
            "**Gespeicherte Compute-Felder prüfen:** ein breites `@api.depends` macht aus einem kleinen Schreibzugriff ein Update vieler Datensätze.",
            "**Importe** abends oder per queue_job in kleinen Stücken.",
        ]),
        ("code", "fix"),
        ("code", "qj"),
        ("note", "Nicht „reparieren“, indem man die Isolationsstufe senkt oder die Exception im eigenen Code abfängt – das macht aus einer sichtbaren Wiederholung still verlorene Änderungen."),
        ("links", "Links"),
    ],
}

SERIALIZE["t"]["fr"] = {
    "title": "« could not serialize access due to concurrent update » dans Odoo – bruit inoffensif ou vrai problème ?",
    "summary": "Ce que signifie cette erreur PostgreSQL dans Odoo, pourquoi Odoo la relance en silence, quand elle devient un problème pour les utilisateurs et les crons, comment trouver qui entre en collision avec qui – et comment s'en débarrasser.",
    "body": [
        ("p", "Le journal PostgreSQL est plein de `ERROR: could not serialize access due to concurrent update`, les utilisateurs attendent parfois plusieurs secondes après « Enregistrer », et de temps en temps un cron échoue. Que se passe-t-il – et faut-il agir ?"),
        ("note", "En bref : Odoo exécute chaque transaction en `REPEATABLE READ` et **relance** automatiquement la requête jusqu'à 5 fois. Des erreurs isolées sont normales. Problème seulement si le journal indique `maximum number of tries reached` ou si elles s'accumulent – deux processus écrivent alors sans cesse les mêmes enregistrements, en général un long cron et les utilisateurs."),
        ("h", "Ce que signifie l'erreur"),
        ("p", "Odoo ouvre chaque transaction avec le niveau d'isolation `REPEATABLE READ` : elle voit les données telles qu'elles étaient à son début. Si la transaction B veut modifier une ligne que la transaction A a modifiée et validée entre-temps, PostgreSQL refuse – B écraserait quelque chose qu'elle n'a jamais vu."),
        ("code", "demo"),
        ("h", "Ce qu'Odoo en fait"),
        ("code", "log"),
        ("ul", [
            "Odoo annule, attend un temps aléatoire (jusqu'à 2, 4, 8, 16 s) et réexécute **toute la requête** – jusqu'à 5 tentatives (`MAX_TRIES_ON_CONCURRENCY_FAILURE`). Idem pour les délais de verrou et les deadlocks.",
            "Pour l'utilisateur : pas d'erreur, mais un clic qui dure des secondes.",
            "Chaque tentative est une ligne `ERROR` dans le journal PostgreSQL – beaucoup de ces lignes ne sont souvent que des relances réussies.",
            "Après le 5e échec, l'utilisateur reçoit un message d'erreur ; un cron échoue et ne repart qu'à sa prochaine échéance.",
        ]),
        ("h", "Causes typiques"),
        ("ul", [
            "**Crons longs** qui écrivent beaucoup d'enregistrements dans une seule transaction (recalculs, synchronisations stock/prix, données de rapports) pendant que les utilisateurs modifient les mêmes enregistrements.",
            "**Intégrations** (boutique, marketplace, entrepôt) qui mettent à jour les mêmes produits ou commandes chaque minute.",
            "**Plusieurs queue jobs en parallèle** sur les mêmes enregistrements.",
            "**Lignes « chaudes »** écrites par tous : un compteur sur la société ou le partenaire, une séquence partagée, un parent dont un champ calculé stocké dépend des enfants.",
            "**Imports** de milliers de lignes pendant les heures de travail.",
        ]),
        ("h", "Trouver qui entre en collision avec qui"),
        ("code", "find"),
        ("p", "En pratique, le motif temporel trahit la cause : les erreurs arrivent par vagues exactement quand un cron ou un job précis tourne. On sait alors quel code examiner."),
        ("h", "S'en débarrasser"),
        ("ul", [
            "**Transactions plus courtes :** traiter les crons par lots et valider après chaque lot ; ne prendre que les lignes libres avec `FOR UPDATE SKIP LOCKED`.",
            "**Autres horaires :** déplacer les crons lourds hors des heures de travail, ne pas en lancer plusieurs à la même minute.",
            "**Une seule file pour les jobs sur les mêmes enregistrements :** un canal queue_job de capacité 1.",
            "**Pas de lignes chaudes :** pas de compteurs sur des enregistrements partagés ; les calculer à la demande ou dans une table à part.",
            "**Vérifier les champs calculés stockés :** un `@api.depends` large transforme une petite écriture en mise à jour de nombreux enregistrements.",
            "**Imports** le soir ou via queue_job en petits morceaux.",
        ]),
        ("code", "fix"),
        ("code", "qj"),
        ("note", "Ne pas « corriger » en baissant le niveau d'isolation ou en interceptant l'exception dans son code – cela transforme une relance visible en mises à jour perdues en silence."),
        ("links", "Liens"),
    ],
}

SERIALIZE["t"]["el"] = {
    "title": "«could not serialize access due to concurrent update» στο Odoo – αθώος θόρυβος ή πραγματικό πρόβλημα;",
    "summary": "Τι σημαίνει αυτό το σφάλμα της PostgreSQL στο Odoo, γιατί το Odoo το επαναλαμβάνει σιωπηλά, πότε γίνεται πρόβλημα για χρήστες και cron, πώς βρίσκετε ποιος συγκρούεται με ποιον – και πώς το ξεφορτώνεστε.",
    "body": [
        ("p", "Το log της PostgreSQL είναι γεμάτο με `ERROR: could not serialize access due to concurrent update`, οι χρήστες περιμένουν μερικές φορές αρκετά δευτερόλεπτα μετά την «Αποθήκευση» και πού και πού ένα cron αποτυγχάνει. Τι συμβαίνει – και πρέπει να κάνετε κάτι;"),
        ("note", "Συνοπτικά: το Odoo εκτελεί κάθε συναλλαγή σε `REPEATABLE READ` και **επαναλαμβάνει** αυτόματα το αίτημα έως 5 φορές. Μεμονωμένα σφάλματα είναι φυσιολογικά. Πρόβλημα υπάρχει μόνο όταν το log γράφει `maximum number of tries reached` ή όταν πληθαίνουν – τότε δύο διεργασίες γράφουν συνεχώς τις ίδιες εγγραφές, συνήθως ένα μακρύ cron και οι χρήστες."),
        ("h", "Τι σημαίνει το σφάλμα"),
        ("p", "Το Odoo ανοίγει κάθε συναλλαγή με επίπεδο απομόνωσης `REPEATABLE READ`: βλέπει τα δεδομένα όπως ήταν στην αρχή της. Αν η συναλλαγή B θέλει να αλλάξει μια γραμμή που η A άλλαξε και επικύρωσε στο μεταξύ, η PostgreSQL αρνείται – η B θα έγραφε πάνω σε κάτι που δεν είδε ποτέ."),
        ("code", "demo"),
        ("h", "Τι κάνει το Odoo"),
        ("code", "log"),
        ("ul", [
            "Το Odoo κάνει rollback, περιμένει τυχαίο χρόνο (έως 2, 4, 8, 16 s) και εκτελεί **ολόκληρο το αίτημα ξανά** – έως 5 προσπάθειες (`MAX_TRIES_ON_CONCURRENCY_FAILURE`). Το ίδιο ισχύει για lock timeouts και deadlocks.",
            "Για τον χρήστη: κανένα σφάλμα, αλλά ένα κλικ που διαρκεί δευτερόλεπτα.",
            "Κάθε προσπάθεια είναι μια γραμμή `ERROR` στο log της PostgreSQL – πολλές τέτοιες γραμμές είναι συνήθως απλώς επιτυχημένες επαναλήψεις.",
            "Μετά την 5η αποτυχία ο χρήστης βλέπει μήνυμα σφάλματος· ένα cron αποτυγχάνει και ξανατρέχει μόνο στην επόμενη προγραμματισμένη ώρα.",
        ]),
        ("h", "Συνήθεις αιτίες"),
        ("ul", [
            "**Μακριά cron** που γράφουν πολλές εγγραφές σε μία συναλλαγή (επανυπολογισμοί, συγχρονισμοί αποθήκης/τιμών, δεδομένα αναφορών) ενώ οι χρήστες επεξεργάζονται τις ίδιες εγγραφές.",
            "**Διασυνδέσεις** (eShop, marketplace, αποθήκη) που ενημερώνουν κάθε λεπτό τα ίδια προϊόντα ή παραγγελίες.",
            "**Πολλά queue jobs παράλληλα** στις ίδιες εγγραφές.",
            "**«Καυτές» γραμμές** που γράφουν όλοι: ένας μετρητής στην εταιρεία ή στον συνεργάτη, μια κοινή ακολουθία, μια γονική εγγραφή της οποίας ένα αποθηκευμένο υπολογιζόμενο πεδίο εξαρτάται από τα παιδιά.",
            "**Εισαγωγές** χιλιάδων γραμμών σε ώρες εργασίας.",
        ]),
        ("h", "Ποιος συγκρούεται με ποιον"),
        ("code", "find"),
        ("p", "Στην πράξη το χρονικό μοτίβο το προδίδει: τα σφάλματα έρχονται κατά κύματα ακριβώς όταν τρέχει ένα συγκεκριμένο cron ή job. Τότε ξέρετε ποιον κώδικα να κοιτάξετε."),
        ("h", "Πώς το ξεφορτώνεστε"),
        ("ul", [
            "**Μικρότερες συναλλαγές:** επεξεργασία των cron σε παρτίδες με commit μετά από κάθε παρτίδα· μόνο ελεύθερες γραμμές με `FOR UPDATE SKIP LOCKED`.",
            "**Άλλες ώρες:** τα βαριά cron εκτός ωραρίου, όχι πολλά στο ίδιο λεπτό.",
            "**Μία λωρίδα για jobs στις ίδιες εγγραφές:** κανάλι queue_job με χωρητικότητα 1.",
            "**Όχι καυτές γραμμές:** όχι μετρητές σε κοινές εγγραφές· υπολογισμός κατά απαίτηση ή σε ξεχωριστό πίνακα.",
            "**Έλεγχος αποθηκευμένων υπολογιζόμενων πεδίων:** ένα πλατύ `@api.depends` κάνει μια μικρή εγγραφή ενημέρωση πολλών εγγραφών.",
            "**Εισαγωγές** το βράδυ ή μέσω queue_job σε μικρά κομμάτια.",
        ]),
        ("code", "fix"),
        ("code", "qj"),
        ("note", "Μην το «διορθώνετε» χαμηλώνοντας το επίπεδο απομόνωσης ή πιάνοντας την εξαίρεση στον κώδικά σας – έτσι μια ορατή επανάληψη γίνεται σιωπηλά χαμένες αλλαγές."),
        ("links", "Σύνδεσμοι"),
    ],
}

SERIALIZE["t"]["uk"] = {
    "title": "«could not serialize access due to concurrent update» в Odoo – нешкідливий шум чи справжня проблема?",
    "summary": "Що означає ця помилка PostgreSQL в Odoo, чому Odoo мовчки повторює запит, коли вона стає проблемою для користувачів і кронів, як знайти, хто з ким конфліктує, і як її позбутися.",
    "body": [
        ("p", "Лог PostgreSQL повний рядків `ERROR: could not serialize access due to concurrent update`, користувачі після «Зберегти» іноді чекають кілька секунд, а час від часу падає крон. Що відбувається і чи треба щось робити?"),
        ("note", "Коротко: Odoo виконує кожну транзакцію в `REPEATABLE READ` і автоматично **повторює** запит до 5 разів. Поодинокі помилки — це нормально. Проблема лише тоді, коли в лозі є `maximum number of tries reached` або помилки накопичуються. Це означає, що два процеси постійно пишуть ті самі записи, зазвичай довгий крон і користувачі."),
        ("h", "Що означає помилка"),
        ("p", "Odoo відкриває кожну транзакцію з рівнем ізоляції `REPEATABLE READ`: вона бачить дані такими, якими вони були на її початку. Якщо транзакція B хоче змінити рядок, який транзакція A тим часом змінила й закомітила, PostgreSQL відмовляє, бо B перезаписала б те, чого не бачила."),
        ("code", "demo"),
        ("h", "Що з цим робить Odoo"),
        ("code", "log"),
        ("ul", [
            "Odoo робить rollback, чекає випадковий час (до 2, 4, 8, 16 с) і виконує **весь запит заново**, до 5 спроб (`MAX_TRIES_ON_CONCURRENCY_FAILURE`). Так само Odoo поводиться з тайм-аутами блокувань і дедлоками.",
            "Для користувача це означає: помилки немає, але клік триває секунди.",
            "Кожна спроба — це рядок `ERROR` у лозі PostgreSQL, тож багато таких рядків зазвичай означають просто успішні повтори.",
            "Після 5-ї невдачі користувач бачить помилку, а крон падає і запуститься знову лише в наступний запланований час.",
        ]),
        ("h", "Типові причини"),
        ("ul", [
            "**Довгі крони**, які пишуть багато записів в одній транзакції (перерахунки, синхронізація залишків чи цін, дані звітів), поки користувачі редагують ті самі записи.",
            "**Інтеграції** (магазин, маркетплейс, склад), які щохвилини оновлюють ті самі товари чи замовлення.",
            "**Кілька queue job паралельно** на тих самих записах.",
            "**«Гарячі» рядки**, які пишуть усі: лічильник на компанії чи партнері, спільна послідовність, батьківський запис, чиє збережене обчислюване поле залежить від дочірніх.",
            "**Імпорти** тисяч рядків у робочий час.",
        ]),
        ("h", "Як знайти, хто з ким конфліктує"),
        ("code", "find"),
        ("p", "На практиці все видно за часом: помилки йдуть хвилями саме тоді, коли працює певний крон або job. Тоді зрозуміло, який код дивитися."),
        ("h", "Як позбутися"),
        ("ul", [
            "**Коротші транзакції:** обробляйте крони пакетами й комітьте після кожного пакета; беріть лише вільні рядки через `FOR UPDATE SKIP LOCKED`.",
            "**Інший час:** перенесіть важкі крони з робочих годин і не ставте кілька на ту саму хвилину.",
            "**Одна смуга для jobs на тих самих записах:** канал queue_job з місткістю 1.",
            "**Без гарячих рядків:** не тримайте лічильники на спільних записах; рахуйте їх на вимогу або в окремій таблиці.",
            "**Перевірте збережені обчислювані поля:** широкий `@api.depends` перетворює маленький запис на оновлення багатьох записів.",
            "**Імпорти** робіть увечері або через queue_job невеликими частинами.",
        ]),
        ("code", "fix"),
        ("code", "qj"),
        ("note", "Не «лагодьте» це зниженням рівня ізоляції чи перехопленням винятку у своєму коді: так видимий повтор перетворюється на непомітно втрачені зміни."),
        ("links", "Посилання"),
    ],
}

SERIALIZE["t"]["ru"] = {
    "title": "«could not serialize access due to concurrent update» в Odoo – безобидный шум или настоящая проблема?",
    "summary": "Что означает эта ошибка PostgreSQL в Odoo, почему Odoo молча повторяет запрос, когда она становится проблемой для пользователей и кронов, как найти, кто с кем конфликтует, и как от неё избавиться.",
    "body": [
        ("p", "Лог PostgreSQL полон строк `ERROR: could not serialize access due to concurrent update`, пользователи после «Сохранить» иногда ждут несколько секунд, а время от времени падает крон. Что происходит и нужно ли что-то делать?"),
        ("note", "Коротко: Odoo выполняет каждую транзакцию в `REPEATABLE READ` и автоматически **повторяет** запрос до 5 раз. Единичные ошибки — это нормально. Проблема только тогда, когда в логе есть `maximum number of tries reached` или ошибки копятся. Значит, два процесса постоянно пишут одни и те же записи, обычно долгий крон и пользователи."),
        ("h", "Что означает ошибка"),
        ("p", "Odoo открывает каждую транзакцию с уровнем изоляции `REPEATABLE READ`: она видит данные такими, какими они были в её начале. Если транзакция B хочет изменить строку, которую транзакция A тем временем изменила и закоммитила, PostgreSQL отказывает, потому что B перезаписала бы то, чего не видела."),
        ("code", "demo"),
        ("h", "Что с этим делает Odoo"),
        ("code", "log"),
        ("ul", [
            "Odoo делает rollback, ждёт случайное время (до 2, 4, 8, 16 с) и выполняет **весь запрос заново**, до 5 попыток (`MAX_TRIES_ON_CONCURRENCY_FAILURE`). Так же Odoo ведёт себя при тайм-аутах блокировок и дедлоках.",
            "Для пользователя это значит: ошибки нет, но клик длится секунды.",
            "Каждая попытка — это строка `ERROR` в логе PostgreSQL, поэтому много таких строк обычно означают просто удачные повторы.",
            "После 5-й неудачи пользователь видит ошибку, а крон падает и запустится снова только в следующее запланированное время.",
        ]),
        ("h", "Типичные причины"),
        ("ul", [
            "**Долгие кроны**, которые пишут много записей в одной транзакции (пересчёты, синхронизация остатков или цен, данные отчётов), пока пользователи редактируют те же записи.",
            "**Интеграции** (магазин, маркетплейс, склад), которые ежеминутно обновляют одни и те же товары или заказы.",
            "**Несколько queue job параллельно** на одних и тех же записях.",
            "**«Горячие» строки**, которые пишут все: счётчик на компании или партнёре, общая последовательность, родительская запись, чьё сохраняемое вычисляемое поле зависит от дочерних.",
            "**Импорты** тысяч строк в рабочее время.",
        ]),
        ("h", "Как найти, кто с кем конфликтует"),
        ("code", "find"),
        ("p", "На практике всё видно по времени: ошибки идут волнами ровно тогда, когда работает определённый крон или job. Тогда понятно, какой код смотреть."),
        ("h", "Как избавиться"),
        ("ul", [
            "**Короче транзакции:** обрабатывайте кроны пачками и коммитьте после каждой пачки; берите только свободные строки через `FOR UPDATE SKIP LOCKED`.",
            "**Другое время:** вынесите тяжёлые кроны из рабочих часов и не ставьте несколько на одну и ту же минуту.",
            "**Одна полоса для jobs на одних и тех же записях:** канал queue_job с ёмкостью 1.",
            "**Без горячих строк:** не держите счётчики на общих записях; считайте их по запросу или в отдельной таблице.",
            "**Проверьте сохраняемые вычисляемые поля:** широкий `@api.depends` превращает маленькую запись в обновление множества записей.",
            "**Импорты** делайте вечером или через queue_job небольшими частями.",
        ]),
        ("code", "fix"),
        ("code", "qj"),
        ("note", "Не «чините» это понижением уровня изоляции или перехватом исключения в своём коде: так видимый повтор превращается в незаметно потерянные изменения."),
        ("links", "Ссылки"),
    ],
}
