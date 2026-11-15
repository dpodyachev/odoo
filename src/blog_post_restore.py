# Статья 14: бэкап есть, а восстановить нельзя – foreign key, дубли в уникальных индексах, отсутствующие индексы; CTE+UNNEST, гомоглифы. Все 6 языков.

RESTORE = {
    "slug": "postgresql-restore-fails-foreign-key-duplicate-index-odoo",
    "date": "2026-11-15",
    "tags": ["PostgreSQL", "Backup", "Restore", "Odoo", "pg_restore"],
    "code": {
        "errors": ("pg_restore · typical errors", """pg_restore: error: could not execute query: ERROR:  could not create unique index "ir_model_data_module_name_uniq_index"
DETAIL:  Key (module, name)=(__export__, res_partner_4711_8d1c) is duplicated.

pg_restore: error: could not execute query: ERROR:  insert or update on table "sale_order_line"
  violates foreign key constraint "sale_order_line_order_id_fkey"
DETAIL:  Key (order_id)=(91234) is not present in table "sale_order".

pg_restore: error: could not execute query: ERROR:  role "odoo_prod" does not exist
pg_restore: error: could not execute query: ERROR:  index "res_partner_x_idx" does not exist      # --clean on an empty DB
pg_restore: error: unsupported version (1.16) in file header                                      # dump newer than pg_restore
pg_restore: warning: errors ignored on restore: 37"""),
        "steps": ("bash · restore so that you see every error", """createdb -U odoo mydb_check
# no --exit-on-error: load everything, collect ALL errors in one file
pg_restore -U odoo -d mydb_check --no-owner --no-privileges -j 4 mydb.dump 2> restore.log
echo "exit code: $?"
grep -c "ERROR" restore.log
grep -A2 "ERROR" restore.log | less

# the dump in sections: data first, indexes/constraints last
pg_restore -l mydb.dump | less              # table of contents
pg_restore -U odoo -d mydb_check --section=pre-data  mydb.dump
pg_restore -U odoo -d mydb_check --section=data      mydb.dump
pg_restore -U odoo -d mydb_check --section=post-data mydb.dump 2> post.log   # indexes, FKs: errors appear here"""),
        "dups": ("sql · duplicates behind a unique index", """-- which values block the unique index (example: ir_model_data)
SELECT module, name, count(*), array_agg(id ORDER BY id) AS ids
  FROM ir_model_data
 GROUP BY module, name
HAVING count(*) > 1;

-- check indexes of the SOURCE database for corruption (PostgreSQL 14+)
pg_amcheck -d mydb --heapallindexed --progress
-- or per index: CREATE EXTENSION amcheck; SELECT bt_index_check('ir_model_data_module_name_uniq_index'::regclass, true);"""),
        "orphans": ("sql · rows whose parent is gone (foreign key)", """-- order lines without an order
SELECT l.id, l.order_id
  FROM sale_order_line l
  LEFT JOIN sale_order o ON o.id = l.order_id
 WHERE l.order_id IS NOT NULL AND o.id IS NULL;

-- generic: all foreign keys of a table and their definition
SELECT conname, pg_get_constraintdef(oid) FROM pg_constraint
 WHERE conrelid = 'sale_order_line'::regclass AND contype = 'f';"""),
        "cte": ("sql · a fixed list of IDs as a table: CTE + UNNEST", """WITH partner_list AS (
    SELECT UNNEST(ARRAY[101, 102, 103, 104]) AS partner_id
),
first_invoice AS (
    SELECT m.partner_id, MIN(m.invoice_date) AS first_invoice_date
      FROM account_move m
      JOIN partner_list pl ON pl.partner_id = m.partner_id
     WHERE m.move_type = 'out_invoice' AND m.state = 'posted'
     GROUP BY m.partner_id
)
SELECT p.id AS partner_id, p.name, fi.first_invoice_date
  FROM res_partner p
  JOIN partner_list pl ON pl.partner_id = p.id
  LEFT JOIN first_invoice fi ON fi.partner_id = p.id      -- LEFT: partners without invoices stay visible
 ORDER BY p.id;"""),
        "homoglyph": ("sql · the invisible typo: Cyrillic letters in a Latin value", """-- 'Сomplete' with a Cyrillic С looks identical but never matches 'Complete'
SELECT DISTINCT cancel_cause, encode(convert_to(cancel_cause, 'UTF8'), 'hex')
  FROM my_table
 WHERE cancel_cause ~ '[А-Яа-яЁёІіЇїЄє]' AND cancel_cause ~ '[A-Za-z]';   -- mixed alphabets"""),
        "after": ("bash · after the cleanup: let Odoo restore its constraints", """# Odoo recreates missing indexes (index=True) and foreign keys of many2one fields
docker compose run --rm odoo odoo -c /etc/odoo/odoo.conf -d mydb_check \\
    -u all --workers=0 --no-http --stop-after-init
grep -iE "foreign key|index|ERROR" update.log"""),
    },
    "links": [
        ("PostgreSQL: pg_restore", "https://www.postgresql.org/docs/current/app-pgrestore.html"),
        ("PostgreSQL: pg_amcheck", "https://www.postgresql.org/docs/current/app-pgamcheck.html"),
        ("PostgreSQL wiki: locale data changes (glibc 2.28)", "https://wiki.postgresql.org/wiki/Locale_data_changes"),
        ("Odoo operations skill for AI agents (Markdown)", "https://2027.pp.ua/skill_odoo.md"),
        ("Blog: restoring a backup on stage without cron jobs", "@blog:odoo-stage-restore-stop-cron-jobs"),
        ("Blog: free hosting, database and filestore (backups to R2)", "@blog:odoo-17-free-hosting-database-filestore"),
    ],
    "t": {},
}

RESTORE["t"]["en"] = {
    "title": "The backup exists – but will not restore: foreign keys, duplicates in unique indexes, missing indexes",
    "summary": "Why a pg_dump that ran without errors can fail on pg_restore, how to see every error at once, how to find duplicates and orphaned rows, why a corrupted index is often the real cause – and a few SQL patterns from real repairs.",
    "body": [
        ("p", "The nightly `pg_dump` ran without a single error for months. Then the day comes when you need it – and `pg_restore` stops with `could not create unique index` or `violates foreign key constraint`. The data in the dump is exactly what was in the database. So the database itself was already broken."),
        ("note", "Short version: pg_dump copies data, it does not check it. Indexes and foreign keys are only rebuilt on restore – and that is where hidden inconsistencies surface. Restore regularly as a test, check the source with `pg_amcheck`, and read every line of the restore log."),
        ("h", "Typical errors"),
        ("code", "errors"),
        ("ul", [
            "**Duplicate key in a unique index** – the source database contains duplicates that its (corrupted) index no longer noticed.",
            "**Foreign key violated** – child rows point to parents that no longer exist (deleted by hand, a failed migration, a constraint dropped at some point).",
            "**Role does not exist** – the dump carries owners and grants: restore with `--no-owner --no-privileges`.",
            "**Index does not exist** with `--clean` on an empty database – harmless; use `--clean --if-exists`.",
            "**Unsupported version in file header** – the dump was made by a newer pg_dump; restore with a pg_restore of at least that version.",
        ]),
        ("h", "Why pg_restore still says “done”"),
        ("p", "By default pg_restore **continues** after errors and ends with `errors ignored on restore: N`. Tables and data are there – only the failed index or foreign key is missing. Odoo starts, looks normal, and the database has no uniqueness or referential checks where they failed. That is worse than a clear abort."),
        ("code", "steps"),
        ("h", "Duplicates: often the index was corrupted, not the application"),
        ("p", "A unique index cannot let duplicates in – unless it is corrupted. The classic cause: an **operating-system upgrade with a new glibc** (2.28 changed the sort order of text). Indexes on text columns built under the old sort order are then silently wrong; inserts slip past them. pg_dump does not notice, the restore builds the index fresh – and fails."),
        ("code", "dups"),
        ("ul", [
            "Clean up the duplicates **in the source** (merge or delete the wrong row – for Odoo records carefully, other tables may reference them), then `REINDEX` the affected indexes and dump again.",
            "After every OS upgrade under PostgreSQL: `REINDEX` the text indexes (PostgreSQL 15+ also warns about a collation version mismatch).",
        ]),
        ("h", "Orphaned rows: the foreign key has nothing to point to"),
        ("code", "orphans"),
        ("p", "Decide per case: restore the missing parent from an older backup, re-link the children, or delete them. Then Odoo can recreate its own constraints:"),
        ("code", "after"),
        ("h", "SQL patterns from real repairs"),
        ("p", "When you repair, you often work with a fixed list of IDs from a ticket or a log. A CTE with `UNNEST(ARRAY[...])` turns the list into a table you can join – much clearer than a long `IN (...)` repeated in several places:"),
        ("code", "cte"),
        ("p", "Two lessons from a real query of this kind: with `JOIN` instead of `LEFT JOIN`, every ID without a match silently disappears from the result – you think you checked 50 partners and saw 43. And a filter on a text value found nothing because two letters of the value in the query were **Cyrillic** – visually identical to Latin:"),
        ("code", "homoglyph"),
        ("h", "Prevention"),
        ("ul", [
            "**Test restores** regularly (stage, weekly or monthly) and check the restore log for `ERROR` – automatically, not by eye.",
            "`pg_amcheck` on the production database now and then, and after every OS/glibc upgrade a `REINDEX`.",
            "pg_dump and pg_restore of the same major version as the server, or pg_restore newer than pg_dump.",
            "Never drop constraints “temporarily” and forget them; never delete rows by hand without checking who references them.",
            "Keep more than one generation of backups – the damage is often older than the last dump.",
        ]),
        ("links", "Links"),
    ],
}

RESTORE["t"]["de"] = {
    "title": "Das Backup ist da – lässt sich aber nicht einspielen: Fremdschlüssel, Duplikate in Unique-Indizes, fehlende Indizes",
    "summary": "Warum ein fehlerfrei gelaufener pg_dump beim pg_restore scheitern kann, wie man alle Fehler auf einmal sieht, Duplikate und verwaiste Zeilen findet, warum oft ein beschädigter Index die eigentliche Ursache ist – und einige SQL-Muster aus echten Reparaturen.",
    "body": [
        ("p", "Der nächtliche `pg_dump` lief monatelang ohne einen einzigen Fehler. Dann kommt der Tag, an dem man ihn braucht – und `pg_restore` bricht mit `could not create unique index` oder `violates foreign key constraint` ab. Die Daten im Dump sind genau die aus der Datenbank. Die Datenbank selbst war also schon kaputt."),
        ("note", "Kurzfassung: pg_dump kopiert Daten, prüft sie aber nicht. Indizes und Fremdschlüssel werden erst beim Einspielen neu aufgebaut – und genau dort tauchen versteckte Inkonsistenzen auf. Regelmäßig testweise wiederherstellen, die Quelle mit `pg_amcheck` prüfen und jede Zeile des Restore-Logs lesen."),
        ("h", "Typische Fehler"),
        ("code", "errors"),
        ("ul", [
            "**Doppelter Schlüssel in einem Unique-Index** – die Quelldatenbank enthält Duplikate, die ihr (beschädigter) Index nicht mehr bemerkt hat.",
            "**Fremdschlüssel verletzt** – Kindzeilen verweisen auf Eltern, die es nicht mehr gibt (von Hand gelöscht, gescheiterte Migration, irgendwann entfernte Constraint).",
            "**Rolle existiert nicht** – der Dump enthält Eigentümer und Rechte: mit `--no-owner --no-privileges` einspielen.",
            "**Index existiert nicht** bei `--clean` auf einer leeren Datenbank – harmlos; `--clean --if-exists` verwenden.",
            "**Unsupported version in file header** – der Dump stammt von einem neueren pg_dump; mit einem pg_restore mindestens dieser Version einspielen.",
        ]),
        ("h", "Warum pg_restore trotzdem „fertig“ meldet"),
        ("p", "Standardmäßig macht pg_restore nach Fehlern **weiter** und endet mit `errors ignored on restore: N`. Tabellen und Daten sind da – es fehlt nur der gescheiterte Index oder Fremdschlüssel. Odoo startet, sieht normal aus, und die Datenbank hat dort, wo es scheiterte, keine Eindeutigkeits- oder Referenzprüfung mehr. Das ist schlimmer als ein klarer Abbruch."),
        ("code", "steps"),
        ("h", "Duplikate: oft war der Index beschädigt, nicht die Anwendung"),
        ("p", "Ein Unique-Index kann keine Duplikate durchlassen – außer er ist beschädigt. Der Klassiker: ein **Betriebssystem-Update mit neuer glibc** (2.28 hat die Sortierreihenfolge von Text geändert). Indizes auf Textspalten, die mit der alten Sortierung gebaut wurden, sind danach still falsch; Einfügungen rutschen durch. pg_dump merkt nichts, das Einspielen baut den Index neu – und scheitert."),
        ("code", "dups"),
        ("ul", [
            "Duplikate **in der Quelle** bereinigen (zusammenführen oder die falsche Zeile löschen – bei Odoo-Datensätzen vorsichtig, andere Tabellen können darauf verweisen), dann die betroffenen Indizes mit `REINDEX` neu bauen und erneut sichern.",
            "Nach jedem Betriebssystem-Update unter PostgreSQL: Textindizes mit `REINDEX` neu bauen (PostgreSQL 15+ warnt zusätzlich vor einer abweichenden Collation-Version).",
        ]),
        ("h", "Verwaiste Zeilen: der Fremdschlüssel zeigt ins Leere"),
        ("code", "orphans"),
        ("p", "Pro Fall entscheiden: fehlenden Elterndatensatz aus einem älteren Backup holen, Kinder neu zuordnen oder löschen. Danach kann Odoo seine eigenen Constraints wieder anlegen:"),
        ("code", "after"),
        ("h", "SQL-Muster aus echten Reparaturen"),
        ("p", "Bei Reparaturen arbeitet man oft mit einer festen Liste von IDs aus einem Ticket oder Log. Eine CTE mit `UNNEST(ARRAY[...])` macht aus der Liste eine Tabelle, die man joinen kann – viel übersichtlicher als ein langes, mehrfach wiederholtes `IN (...)`:"),
        ("code", "cte"),
        ("p", "Zwei Lehren aus einer echten Abfrage dieser Art: Mit `JOIN` statt `LEFT JOIN` verschwindet jede ID ohne Treffer still aus dem Ergebnis – man glaubt, 50 Partner geprüft zu haben, und sieht 43. Und ein Filter auf einen Textwert fand nichts, weil zwei Buchstaben des Werts in der Abfrage **kyrillisch** waren – optisch identisch mit lateinischen:"),
        ("code", "homoglyph"),
        ("h", "Vorbeugen"),
        ("ul", [
            "Regelmäßig **testweise wiederherstellen** (Stage, wöchentlich oder monatlich) und das Restore-Log auf `ERROR` prüfen – automatisch, nicht mit dem Auge.",
            "Ab und zu `pg_amcheck` auf der Produktivdatenbank und nach jedem Betriebssystem-/glibc-Update ein `REINDEX`.",
            "pg_dump und pg_restore in derselben Hauptversion wie der Server oder pg_restore neuer als pg_dump.",
            "Constraints nie „vorübergehend“ entfernen und vergessen; Zeilen nie von Hand löschen, ohne zu prüfen, wer darauf verweist.",
            "Mehr als eine Backup-Generation aufbewahren – der Schaden ist oft älter als der letzte Dump.",
        ]),
        ("links", "Links"),
    ],
}

RESTORE["t"]["fr"] = {
    "title": "La sauvegarde existe – mais ne se restaure pas : clés étrangères, doublons dans les index uniques, index manquants",
    "summary": "Pourquoi un pg_dump sans erreur peut échouer au pg_restore, comment voir toutes les erreurs d'un coup, trouver doublons et lignes orphelines, pourquoi un index corrompu est souvent la vraie cause – et quelques modèles SQL issus de vraies réparations.",
    "body": [
        ("p", "Le `pg_dump` nocturne tourne depuis des mois sans la moindre erreur. Puis vient le jour où l'on en a besoin – et `pg_restore` s'arrête avec `could not create unique index` ou `violates foreign key constraint`. Les données du dump sont exactement celles de la base. La base elle-même était donc déjà abîmée."),
        ("note", "En bref : pg_dump copie les données, il ne les vérifie pas. Index et clés étrangères ne sont reconstruits qu'à la restauration – c'est là que les incohérences cachées apparaissent. Restaurer régulièrement pour tester, vérifier la source avec `pg_amcheck` et lire chaque ligne du journal de restauration."),
        ("h", "Erreurs typiques"),
        ("code", "errors"),
        ("ul", [
            "**Clé dupliquée dans un index unique** – la base source contient des doublons que son index (corrompu) ne voyait plus.",
            "**Clé étrangère violée** – des lignes enfants pointent vers des parents qui n'existent plus (supprimés à la main, migration ratée, contrainte supprimée un jour).",
            "**Le rôle n'existe pas** – le dump contient propriétaires et droits : restaurer avec `--no-owner --no-privileges`.",
            "**L'index n'existe pas** avec `--clean` sur une base vide – sans gravité ; utiliser `--clean --if-exists`.",
            "**Unsupported version in file header** – le dump vient d'un pg_dump plus récent ; restaurer avec un pg_restore au moins de cette version.",
        ]),
        ("h", "Pourquoi pg_restore dit quand même « terminé »"),
        ("p", "Par défaut, pg_restore **continue** après une erreur et finit par `errors ignored on restore: N`. Tables et données sont là – il ne manque que l'index ou la clé étrangère en échec. Odoo démarre, semble normal, et la base n'a plus de contrôle d'unicité ou de référence là où cela a échoué. C'est pire qu'un arrêt net."),
        ("code", "steps"),
        ("h", "Doublons : souvent l'index était corrompu, pas l'application"),
        ("p", "Un index unique ne peut pas laisser passer de doublons – sauf s'il est corrompu. Le cas classique : une **mise à jour du système avec une nouvelle glibc** (la 2.28 a changé l'ordre de tri du texte). Les index sur des colonnes texte construits avec l'ancien ordre deviennent faux en silence ; des insertions passent au travers. pg_dump ne voit rien, la restauration reconstruit l'index – et échoue."),
        ("code", "dups"),
        ("ul", [
            "Nettoyer les doublons **dans la source** (fusionner ou supprimer la mauvaise ligne – prudence avec les enregistrements Odoo, d'autres tables peuvent y faire référence), puis `REINDEX` des index concernés et nouvelle sauvegarde.",
            "Après chaque mise à jour du système sous PostgreSQL : `REINDEX` des index texte (PostgreSQL 15+ signale aussi une version de collation différente).",
        ]),
        ("h", "Lignes orphelines : la clé étrangère pointe dans le vide"),
        ("code", "orphans"),
        ("p", "Décider au cas par cas : récupérer le parent manquant d'une sauvegarde plus ancienne, rattacher les enfants ou les supprimer. Ensuite Odoo peut recréer ses propres contraintes :"),
        ("code", "after"),
        ("h", "Modèles SQL issus de vraies réparations"),
        ("p", "Pour une réparation, on travaille souvent avec une liste fixe d'identifiants venant d'un ticket ou d'un journal. Une CTE avec `UNNEST(ARRAY[...])` transforme la liste en table que l'on peut joindre – bien plus lisible qu'un long `IN (...)` répété à plusieurs endroits :"),
        ("code", "cte"),
        ("p", "Deux leçons d'une vraie requête de ce genre : avec `JOIN` au lieu de `LEFT JOIN`, chaque identifiant sans correspondance disparaît en silence du résultat – on croit avoir vérifié 50 partenaires et on en voit 43. Et un filtre sur une valeur texte ne trouvait rien parce que deux lettres de la valeur dans la requête étaient **cyrilliques** – visuellement identiques aux latines :"),
        ("code", "homoglyph"),
        ("h", "Prévention"),
        ("ul", [
            "**Restaurations de test** régulières (stage, chaque semaine ou chaque mois) et contrôle automatique du journal de restauration sur `ERROR`.",
            "`pg_amcheck` de temps en temps sur la base de production, et un `REINDEX` après chaque mise à jour du système ou de la glibc.",
            "pg_dump et pg_restore de la même version majeure que le serveur, ou pg_restore plus récent que pg_dump.",
            "Ne jamais supprimer des contraintes « temporairement » et les oublier ; ne jamais supprimer de lignes à la main sans vérifier qui y fait référence.",
            "Conserver plusieurs générations de sauvegardes – le dommage est souvent plus ancien que le dernier dump.",
        ]),
        ("links", "Liens"),
    ],
}

RESTORE["t"]["el"] = {
    "title": "Το αντίγραφο ασφαλείας υπάρχει – αλλά δεν επαναφέρεται: foreign keys, διπλότυπα σε unique indexes, indexes που λείπουν",
    "summary": "Γιατί ένα pg_dump χωρίς σφάλματα μπορεί να αποτύχει στο pg_restore, πώς βλέπετε όλα τα σφάλματα μαζί, πώς βρίσκετε διπλότυπα και ορφανές γραμμές, γιατί συχνά η πραγματική αιτία είναι ένας κατεστραμμένος index – και μερικά μοτίβα SQL από πραγματικές επισκευές.",
    "body": [
        ("p", "Το νυχτερινό `pg_dump` έτρεχε για μήνες χωρίς ούτε ένα σφάλμα. Μετά έρχεται η μέρα που το χρειάζεστε – και το `pg_restore` σταματά με `could not create unique index` ή `violates foreign key constraint`. Τα δεδομένα του dump είναι ακριβώς αυτά της βάσης. Άρα η ίδια η βάση ήταν ήδη χαλασμένη."),
        ("note", "Συνοπτικά: το pg_dump αντιγράφει δεδομένα, δεν τα ελέγχει. Οι indexes και τα foreign keys χτίζονται ξανά μόνο στην επαναφορά – και εκεί εμφανίζονται οι κρυφές ασυνέπειες. Κάνετε δοκιμαστικές επαναφορές τακτικά, ελέγχετε την πηγή με `pg_amcheck` και διαβάζετε κάθε γραμμή του log επαναφοράς."),
        ("h", "Συνήθη σφάλματα"),
        ("code", "errors"),
        ("ul", [
            "**Διπλό κλειδί σε unique index** – η βάση πηγής περιέχει διπλότυπα που ο (κατεστραμμένος) index της δεν έβλεπε πια.",
            "**Παραβίαση foreign key** – γραμμές-παιδιά δείχνουν σε γονείς που δεν υπάρχουν πια (σβησμένοι με το χέρι, αποτυχημένη μετάπτωση, constraint που αφαιρέθηκε κάποτε).",
            "**Ο ρόλος δεν υπάρχει** – το dump περιέχει ιδιοκτήτες και δικαιώματα: επαναφορά με `--no-owner --no-privileges`.",
            "**Ο index δεν υπάρχει** με `--clean` σε κενή βάση – ακίνδυνο· χρησιμοποιήστε `--clean --if-exists`.",
            "**Unsupported version in file header** – το dump φτιάχτηκε από νεότερο pg_dump· επαναφορά με pg_restore τουλάχιστον αυτής της έκδοσης.",
        ]),
        ("h", "Γιατί το pg_restore λέει παρ' όλα αυτά «τέλος»"),
        ("p", "Εξ ορισμού το pg_restore **συνεχίζει** μετά από σφάλματα και τελειώνει με `errors ignored on restore: N`. Πίνακες και δεδομένα υπάρχουν – λείπει μόνο ο index ή το foreign key που απέτυχε. Το Odoo ξεκινά, φαίνεται κανονικό, και η βάση δεν έχει πια έλεγχο μοναδικότητας ή αναφορών εκεί όπου απέτυχε. Αυτό είναι χειρότερο από μια καθαρή διακοπή."),
        ("code", "steps"),
        ("h", "Διπλότυπα: συχνά χάλασε ο index, όχι η εφαρμογή"),
        ("p", "Ένας unique index δεν αφήνει διπλότυπα – εκτός αν είναι κατεστραμμένος. Το κλασικό: μια **αναβάθμιση λειτουργικού με νέα glibc** (η 2.28 άλλαξε τη σειρά ταξινόμησης κειμένου). Οι indexes σε στήλες κειμένου που χτίστηκαν με την παλιά σειρά γίνονται σιωπηλά λάθος· εισαγωγές περνούν από κάτω τους. Το pg_dump δεν καταλαβαίνει τίποτα, η επαναφορά ξαναχτίζει τον index – και αποτυγχάνει."),
        ("code", "dups"),
        ("ul", [
            "Καθαρίστε τα διπλότυπα **στην πηγή** (συγχώνευση ή διαγραφή της λάθος γραμμής – προσοχή στις εγγραφές του Odoo, άλλοι πίνακες μπορεί να αναφέρονται σε αυτές), μετά `REINDEX` στους επηρεασμένους indexes και νέο αντίγραφο.",
            "Μετά από κάθε αναβάθμιση λειτουργικού κάτω από την PostgreSQL: `REINDEX` στους indexes κειμένου (η PostgreSQL 15+ προειδοποιεί επίσης για διαφορετική έκδοση collation).",
        ]),
        ("h", "Ορφανές γραμμές: το foreign key δείχνει στο κενό"),
        ("code", "orphans"),
        ("p", "Αποφασίστε ανά περίπτωση: επαναφορά του γονέα που λείπει από παλαιότερο αντίγραφο, νέα σύνδεση των παιδιών ή διαγραφή τους. Μετά το Odoo μπορεί να ξαναδημιουργήσει τα δικά του constraints:"),
        ("code", "after"),
        ("h", "Μοτίβα SQL από πραγματικές επισκευές"),
        ("p", "Στις επισκευές δουλεύετε συχνά με μια σταθερή λίστα IDs από ένα ticket ή ένα log. Ένα CTE με `UNNEST(ARRAY[...])` κάνει τη λίστα πίνακα που μπορείτε να κάνετε join – πολύ πιο καθαρό από ένα μακρύ `IN (...)` επαναλαμβανόμενο σε πολλά σημεία:"),
        ("code", "cte"),
        ("p", "Δύο μαθήματα από ένα πραγματικό τέτοιο ερώτημα: με `JOIN` αντί για `LEFT JOIN`, κάθε ID χωρίς αντιστοιχία εξαφανίζεται σιωπηλά από το αποτέλεσμα – νομίζετε ότι ελέγξατε 50 συνεργάτες και βλέπετε 43. Και ένα φίλτρο σε τιμή κειμένου δεν έβρισκε τίποτα επειδή δύο γράμματα της τιμής στο ερώτημα ήταν **κυριλλικά** – οπτικά ίδια με τα λατινικά:"),
        ("code", "homoglyph"),
        ("h", "Πρόληψη"),
        ("ul", [
            "**Δοκιμαστικές επαναφορές** τακτικά (stage, εβδομαδιαία ή μηνιαία) και αυτόματος έλεγχος του log επαναφοράς για `ERROR`.",
            "`pg_amcheck` πού και πού στη βάση παραγωγής, και `REINDEX` μετά από κάθε αναβάθμιση λειτουργικού / glibc.",
            "pg_dump και pg_restore της ίδιας κύριας έκδοσης με τον server, ή pg_restore νεότερο από το pg_dump.",
            "Ποτέ μην αφαιρείτε constraints «προσωρινά» και τα ξεχνάτε· ποτέ μη σβήνετε γραμμές με το χέρι χωρίς να ελέγξετε ποιος αναφέρεται σε αυτές.",
            "Κρατάτε περισσότερες από μία γενιές αντιγράφων – η ζημιά είναι συχνά παλαιότερη από το τελευταίο dump.",
        ]),
        ("links", "Σύνδεσμοι"),
    ],
}

RESTORE["t"]["uk"] = {
    "title": "Бекап є, але не відновлюється: зовнішні ключі, дублікати в унікальних індексах, відсутні індекси",
    "summary": "Чому pg_dump без жодної помилки може не відновитися через pg_restore, як побачити всі помилки одразу, знайти дублікати й «осиротілі» рядки, чому справжня причина часто в пошкодженому індексі, і кілька SQL-прийомів із реальних ремонтів.",
    "body": [
        ("p", "Нічний `pg_dump` місяцями працював без жодної помилки. Потім настає день, коли він потрібен, а `pg_restore` зупиняється з `could not create unique index` або `violates foreign key constraint`. Дані в дампі точно ті, що були в базі. Отже, сама база вже була зламана."),
        ("note", "Коротко: pg_dump копіює дані, але не перевіряє їх. Індекси й зовнішні ключі перебудовуються лише під час відновлення, і саме там спливають приховані невідповідності. Регулярно робіть тестове відновлення, перевіряйте джерело через `pg_amcheck` і читайте кожен рядок логу відновлення."),
        ("h", "Типові помилки"),
        ("code", "errors"),
        ("ul", [
            "**Дубльований ключ в унікальному індексі:** у базі-джерелі є дублікати, яких її (пошкоджений) індекс уже не помічав.",
            "**Порушено зовнішній ключ:** дочірні рядки посилаються на батьків, яких більше немає (видалили вручну, міграція не вдалася, колись прибрали обмеження).",
            "**Роль не існує:** у дампі є власники й права, тож відновлюйте з `--no-owner --no-privileges`.",
            "**Індекс не існує** при `--clean` на порожній базі: це нешкідливо, використовуйте `--clean --if-exists`.",
            "**Unsupported version in file header:** дамп зроблено новішим pg_dump, тож відновлюйте pg_restore щонайменше тієї ж версії.",
        ]),
        ("h", "Чому pg_restore все одно пише «готово»"),
        ("p", "За замовчуванням pg_restore після помилок **продовжує** роботу і завершується повідомленням `errors ignored on restore: N`. Таблиці й дані на місці, бракує лише індексу чи зовнішнього ключа, який не створився. Odoo запускається й виглядає нормально, але там, де сталася помилка, база вже не перевіряє унікальність і посилання. Це гірше, ніж чітка зупинка."),
        ("code", "steps"),
        ("h", "Дублікати: часто зламався індекс, а не застосунок"),
        ("p", "Унікальний індекс не пропускає дублікатів, якщо він не пошкоджений. Класична причина — **оновлення ОС з новою glibc** (у версії 2.28 змінився порядок сортування тексту). Індекси на текстових колонках, побудовані за старим порядком, після цього непомітно стають неправильними, і вставки проходять повз них. pg_dump нічого не помічає, відновлення будує індекс заново і падає."),
        ("code", "dups"),
        ("ul", [
            "Приберіть дублікати **в джерелі** (об'єднайте або видаліть хибний рядок; із записами Odoo обережно, на них можуть посилатися інші таблиці). Потім перебудуйте зачеплені індекси через `REINDEX` і зробіть бекап заново.",
            "Після кожного оновлення ОС під PostgreSQL перебудовуйте текстові індекси через `REINDEX` (PostgreSQL 15+ ще й попереджає про розбіжність версії collation).",
        ]),
        ("h", "«Осиротілі» рядки: зовнішній ключ вказує в нікуди"),
        ("code", "orphans"),
        ("p", "Вирішуйте для кожного випадку окремо: відновіть відсутнього батька зі старішого бекапу, прив'яжіть дочірні рядки заново або видаліть їх. Після цього Odoo зможе відтворити власні обмеження:"),
        ("code", "after"),
        ("h", "SQL-прийоми з реальних ремонтів"),
        ("p", "Під час ремонту часто працюєш з фіксованим списком id з тікета чи логу. CTE з `UNNEST(ARRAY[...])` перетворює список на таблицю, з якою можна робити join. Це набагато зрозуміліше, ніж довгий `IN (...)`, повторений у кількох місцях:"),
        ("code", "cte"),
        ("p", "Два уроки з реального запиту такого типу. З `JOIN` замість `LEFT JOIN` кожен id без збігу непомітно зникає з результату: думаєш, що перевірив 50 партнерів, а бачиш 43. А фільтр за текстовим значенням нічого не знаходив, бо дві літери значення в запиті були **кириличними**, на вигляд такими самими, як латинські:"),
        ("code", "homoglyph"),
        ("h", "Профілактика"),
        ("ul", [
            "Регулярно робіть **тестове відновлення** (stage, щотижня чи щомісяця) і перевіряйте лог відновлення на `ERROR` автоматично, а не на око.",
            "Час від часу запускайте `pg_amcheck` на продуктивній базі, а після кожного оновлення ОС чи glibc робіть `REINDEX`.",
            "pg_dump і pg_restore тієї ж мажорної версії, що й сервер, або pg_restore новіший за pg_dump.",
            "Ніколи не прибирайте обмеження «тимчасово», щоб потім про них забути; ніколи не видаляйте рядки вручну, не перевіривши, хто на них посилається.",
            "Зберігайте більше одного покоління бекапів: пошкодження часто старше за останній дамп.",
        ]),
        ("links", "Посилання"),
    ],
}

RESTORE["t"]["ru"] = {
    "title": "Бэкап есть, но не восстанавливается: внешние ключи, дубли в уникальных индексах, отсутствующие индексы",
    "summary": "Почему pg_dump без единой ошибки может не восстановиться через pg_restore, как увидеть все ошибки сразу, найти дубли и «осиротевшие» строки, почему настоящая причина часто в повреждённом индексе, и несколько SQL-приёмов из реальных ремонтов.",
    "body": [
        ("p", "Ночной `pg_dump` месяцами работал без единой ошибки. Потом наступает день, когда он нужен, а `pg_restore` останавливается с `could not create unique index` или `violates foreign key constraint`. Данные в дампе ровно те, что были в базе. Значит, сама база уже была сломана."),
        ("note", "Коротко: pg_dump копирует данные, но не проверяет их. Индексы и внешние ключи перестраиваются только при восстановлении, и именно там всплывают скрытые несоответствия. Регулярно делайте тестовое восстановление, проверяйте источник через `pg_amcheck` и читайте каждую строку лога восстановления."),
        ("h", "Типичные ошибки"),
        ("code", "errors"),
        ("ul", [
            "**Дублированный ключ в уникальном индексе:** в базе-источнике есть дубли, которых её (повреждённый) индекс уже не замечал.",
            "**Нарушен внешний ключ:** дочерние строки ссылаются на родителей, которых больше нет (удалили вручную, миграция не удалась, когда-то убрали ограничение).",
            "**Роль не существует:** в дампе есть владельцы и права, поэтому восстанавливайте с `--no-owner --no-privileges`.",
            "**Индекс не существует** при `--clean` на пустой базе: это безобидно, используйте `--clean --if-exists`.",
            "**Unsupported version in file header:** дамп сделан более новым pg_dump, поэтому восстанавливайте pg_restore как минимум той же версии.",
        ]),
        ("h", "Почему pg_restore всё равно пишет «готово»"),
        ("p", "По умолчанию pg_restore после ошибок **продолжает** работу и заканчивает сообщением `errors ignored on restore: N`. Таблицы и данные на месте, не хватает только индекса или внешнего ключа, который не создался. Odoo запускается и выглядит нормально, но там, где произошла ошибка, база уже не проверяет уникальность и ссылки. Это хуже, чем чёткая остановка."),
        ("code", "steps"),
        ("h", "Дубли: часто сломался индекс, а не приложение"),
        ("p", "Уникальный индекс не пропускает дублей, если он не повреждён. Классическая причина — **обновление ОС с новой glibc** (в версии 2.28 изменился порядок сортировки текста). Индексы на текстовых колонках, построенные по старому порядку, после этого незаметно становятся неправильными, и вставки проходят мимо них. pg_dump ничего не замечает, восстановление строит индекс заново и падает."),
        ("code", "dups"),
        ("ul", [
            "Уберите дубли **в источнике** (объедините или удалите ошибочную строку; с записями Odoo осторожно, на них могут ссылаться другие таблицы). Затем перестройте затронутые индексы через `REINDEX` и сделайте бэкап заново.",
            "После каждого обновления ОС под PostgreSQL перестраивайте текстовые индексы через `REINDEX` (PostgreSQL 15+ ещё и предупреждает о расхождении версии collation).",
        ]),
        ("h", "«Осиротевшие» строки: внешний ключ указывает в никуда"),
        ("code", "orphans"),
        ("p", "Решайте для каждого случая отдельно: восстановите недостающего родителя из более старого бэкапа, привяжите дочерние строки заново или удалите их. После этого Odoo сможет пересоздать собственные ограничения:"),
        ("code", "after"),
        ("h", "SQL-приёмы из реальных ремонтов"),
        ("p", "При ремонте часто работаешь с фиксированным списком id из тикета или лога. CTE с `UNNEST(ARRAY[...])` превращает список в таблицу, с которой можно делать join. Это гораздо понятнее, чем длинный `IN (...)`, повторённый в нескольких местах:"),
        ("code", "cte"),
        ("p", "Два урока из реального запроса такого типа. С `JOIN` вместо `LEFT JOIN` каждый id без совпадения незаметно пропадает из результата: думаешь, что проверил 50 партнёров, а видишь 43. А фильтр по текстовому значению ничего не находил, потому что две буквы значения в запросе были **кириллическими**, на вид такими же, как латинские:"),
        ("code", "homoglyph"),
        ("h", "Профилактика"),
        ("ul", [
            "Регулярно делайте **тестовое восстановление** (stage, еженедельно или ежемесячно) и проверяйте лог восстановления на `ERROR` автоматически, а не на глаз.",
            "Время от времени запускайте `pg_amcheck` на рабочей базе, а после каждого обновления ОС или glibc делайте `REINDEX`.",
            "pg_dump и pg_restore той же мажорной версии, что и сервер, или pg_restore новее, чем pg_dump.",
            "Никогда не убирайте ограничения «временно», чтобы потом о них забыть; никогда не удаляйте строки вручную, не проверив, кто на них ссылается.",
            "Храните больше одного поколения бэкапов: повреждение часто старше последнего дампа.",
        ]),
        ("links", "Ссылки"),
    ],
}
