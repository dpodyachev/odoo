# Статья 41: полезные модули Odoo по областям (OCA + стандарт) – что каждый даёт и когда не нужен. Языки: en, de, ru, uk.
# Тема по мотивам git.gmbh («Odoo Apps»), текст свой. Дополняет blog_post_apps.py (источники, лицензии, чек-лист) – не повторять.
# Все технические имена OCA проверены в ветке 17.0 на github.com/OCA (25.11.2026).

USEFULMODS_POST = {
    "slug": "useful-odoo-modules-by-area-oca-standard-what-each-gives",
    "date": "2026-11-25",
    "tags": ["Odoo", "OCA", "Modules", "Community"],
    "code": {
        "install": ("shell · add an OCA repository to Odoo in docker and install one module (Odoo 17)", """# 1) next to docker-compose.yml: clone the repository, branch = your Odoo version
mkdir -p oca && cd oca
git clone -b 17.0 --depth 1 https://github.com/OCA/server-tools.git
git clone -b 17.0 --depth 1 https://github.com/OCA/queue.git
cd ..

# 2) mount it into the container (docker-compose.yml, service "odoo"):
#      volumes:
#        - ./oca:/mnt/oca:ro
#    and add every repository folder to addons_path (odoo.conf):
#      addons_path = /mnt/extra-addons,/mnt/oca/server-tools,/mnt/oca/queue
#    (one path per repository, not /mnt/oca itself)

# 3) python dependencies of the module, if it has any (see its README / manifest "external_dependencies")
docker compose exec odoo pip install --user -r /mnt/oca/server-tools/requirements.txt

# 4) restart, then install on the COPY of the database first
docker compose restart odoo
docker compose exec odoo odoo -d test_copy -i auditlog --stop-after-init --no-http

# later, after "git pull" in the repository: update the module
docker compose exec odoo odoo -d test_copy -u auditlog --stop-after-init --no-http"""),
    },
    "links": [
        ("Blog: Odoo apps and modules – what you need and what each one costs later", "@blog:odoo-apps-modules-community-enterprise-oca-app-store-what-you-need"),
        ("Blog: Odoo in docker compose with extra addons and nginx", "@blog:odoo-docker-compose-extra-addons-nginx"),
        ("Blog: updating modules with click-odoo-update", "@blog:odoo-module-update-click-odoo-update"),
        ("Odoo Community Association (OCA)", "https://odoo-community.org/"),
        ("OCA on GitHub – all repositories", "https://github.com/OCA"),
        ("Our hour packs", "@page:#packs"),
    ],
    "t": {},
}

# Таблицы: (модуль, репозиторий) одинаковы во всех языках, тексты – по языкам.
_OPS = [("auditlog", "OCA/server-tools"), ("database_cleanup", "OCA/server-tools"),
        ("auto_backup", "OCA/server-tools"), ("base_technical_user", "OCA/server-tools")]
_UX = [("web_environment_ribbon", "OCA/web"), ("web_responsive", "OCA/web"), ("web_m2x_options", "OCA/web"),
       ("partner_firstname", "OCA/partner-contact")]
_REP = [("mis_builder", "OCA/mis-builder"), ("account_financial_report", "OCA/account-financial-reporting"),
        ("report_xlsx", "OCA/reporting-engine"), ("date_range", "OCA/server-ux")]
_ACC = [("account_reconcile_oca", "OCA/account-reconcile"), ("account_statement_import_camt", "OCA/bank-statement-import"),
        ("account_asset_management", "OCA/account-financial-tools"), ("datev_export", "OCA/l10n-germany"),
        ("l10n_de_tax_statement", "OCA/l10n-germany")]
_STK = [("stock_no_negative", "OCA/stock-logistics-workflow"), ("stock_picking_invoice_link", "OCA/stock-logistics-workflow"),
        ("stock_cycle_count", "OCA/stock-logistics-warehouse"), ("stock_mts_mto_rule", "OCA/stock-logistics-warehouse")]
_SRV = [("helpdesk_mgmt", "OCA/helpdesk"), ("dms", "OCA/dms"), ("mail_tracking", "OCA/social")]


def _tbl(head, mods, texts):
    """texts: [(what it gives, not needed when)] в порядке mods."""
    return [head] + [[f"`{m}`", r, a, b] for (m, r), (a, b) in zip(mods, texts)]


def _body(x):
    """x – словарь текстов одного языка."""
    H = x["h"]
    return [
        ("p", x["intro"]), ("note", x["note"]),
        ("h", H[0]), ("p", x["before"]),
        ("h", H[1]), ("table", _tbl(x["head"], _OPS, x["ops"])), ("p", x["ops_p"]),
        ("h", H[2]), ("p", x["queue_p"]), ("ul", x["queue_ul"]),
        ("h", H[3]), ("table", _tbl(x["head"], _UX, x["ux"])),
        ("h", H[4]), ("table", _tbl(x["head"], _REP, x["rep"])), ("p", x["rep_p"]),
        ("h", H[5]), ("p", x["acc_p"]), ("table", _tbl(x["head"], _ACC, x["acc"])),
        ("h", H[6]), ("p", x["stk_p"]), ("table", _tbl(x["head"], _STK, x["stk"])),
        ("h", H[7]), ("table", _tbl(x["head"], _SRV, x["srv"])),
        ("h", H[8]), ("p", x["inst_p"]), ("code", "install"), ("ul", x["inst_ul"]),
        ("h", H[9]), ("ol", x["first"]),
        ("h", H[10]), ("p", x["closing"]),
        ("links", x["links"]),
    ]


_EN = {
    "title": "Odoo modules that make your ERP more powerful: a practical list by area",
    "summary": "Concrete modules for Odoo 17 Community and Enterprise, sorted by area – audit log, background jobs, test-database ribbon, management reports, bank reconciliation, assets, DATEV, stock rules, helpdesk, documents, mail tracking: what each one gives, when you do not need it, and how to install an OCA module in docker.",
    "intro": "Odoo out of the box covers a lot, but many companies run into the same gaps: who changed this price, why is the import blocking everybody, where is the bank reconciliation in Community, how do I get a real P&L by month. For most of these gaps there is already a well-maintained module – usually from the Odoo Community Association (OCA). Below is our short list by area, with one honest column: when you do not need the module.",
    "note": "All OCA module names below were checked in the 17.0 branches on github.com/OCA on 25 November 2026. Availability for 18.0 and 19.0 differs per module – check the branch of your version. We are an independent Odoo service provider, not an Odoo partner.",
    "h": ["Before you install anything", "Administration and operations", "Background jobs: queue_job", "Usability",
          "Reports and figures", "Accounting in Community – and for Germany", "Warehouse", "Service, documents, e-mail",
          "How to install an OCA module", "What we would install first", "Conclusion"],
    "before": "Every module you add has to be ported and tested again at every Odoo upgrade. Where modules come from, what their licences mean and a checklist for third-party code are in our separate article [Odoo apps and modules](@blog:odoo-apps-modules-community-enterprise-oca-app-store-what-you-need). Here it is only about *which* modules are worth that price. Rule number one stays: install on a copy of the database first.",
    "head": ["Module", "Repository", "What it gives", "Not needed when"],
    "ops": [("A log of who changed which field when, with old and new value – per model you choose.", "nobody ever asks “who changed this?” – or you only need it on one or two fields, where standard chatter tracking is enough."),
            ("Finds leftovers of uninstalled modules: orphan tables, columns, models – and lets you remove them.", "the database was created fresh and no module was ever uninstalled. Use only on a copy and with a backup."),
            ("Scheduled database dumps from inside Odoo, optionally to a remote server.", "you already back up with pg_dump outside Odoo – which we recommend: a backup should not depend on the application it protects."),
            ("A technical user for crons and integrations instead of running them as the admin.", "you have no integrations and no own scheduled jobs.")],
    "ops_p": "`auditlog` is the one we install most often. Keep the list of logged models short – logging every write on `stock.move` or `account.move.line` makes the log table grow fast and slows down busy days.",
    "queue_p": "`queue_job` (repository OCA/queue) moves long tasks into the background: imports, mass e-mails, synchronisation with a shop, exports to accounting. Users do not wait, failed jobs can be retried, and you see every job with its error. Many other OCA modules depend on it.",
    "queue_ul": ["It must be loaded server-wide: `server_wide_modules = web,queue_job` in odoo.conf, and Odoo must run with workers (`workers > 0`).",
                 "Set the channels, e.g. `[queue_job] channels = root:2` – otherwise one heavy import can still occupy all workers.",
                 "With several databases on one server, the job runner needs `db_name` or a proper `dbfilter` – the classic trap we describe in the article on `list_db = False`.",
                 "Not needed when nothing in your system runs longer than a few seconds."],
    "ux": [("A coloured ribbon “TEST” on every non-production database – configurable via system parameters.", "you never have a test copy. You should have one."),
           ("A mobile-friendly app menu and layout for the backend.", "you are on Odoo 17 or newer: the standard backend is responsive already. Useful mainly on 16 and older."),
           ("Controls “Create and edit…” and the number of entries in many2one dropdowns.", "users never create half-filled records by mistake from a dropdown."),
           ("Separate first and last name fields for contacts.", "you only work with companies, or the single name field is fine for your letters and exports.")],
    "rep": [("Management reports defined by rules: P&L by month, budget vs actual, KPIs by department – exportable to Excel.", "you are on Enterprise and the standard financial reports and budgets are enough."),
            ("Trial balance, general ledger, open items, aged partner balance – for Community.", "you are on Enterprise: the full accounting reports are included."),
            ("A base for Excel exports of any report – developers build on it.", "nobody needs Excel files that are generated by Odoo itself."),
            ("Named periods (months, quarters, fiscal years) to pick in reports.", "you only report by calendar month."),],
    "rep_p": "`mis_builder` needs `date_range` and `report_xlsx`, which is why they appear together here. It is the one module that most often replaces a weekly Excel export.",
    "acc_p": "In Community, Odoo ships invoicing and basic accounting; the bank reconciliation widget, asset management and most reports are Enterprise. OCA fills exactly these gaps. For Germany, the standard localisation `l10n_de` with the SKR03/SKR04 charts of accounts comes with Odoo; OCA/l10n-germany adds the rest:",
    "acc": [("A bank reconciliation screen for Community: match statement lines with invoices and payments.", "you are on Enterprise – its own reconciliation is included."),
            ("Import of CAMT.053 bank statements (the format German banks provide).", "your bank is synchronised online, or you are on Enterprise with its own import."),
            ("Fixed assets with depreciation boards and automatic depreciation entries.", "you are on Enterprise (Assets app), or your tax advisor keeps the assets outside Odoo."),
            ("Export of journal entries in DATEV format for the tax advisor.", "the tax advisor works directly in Odoo, or you are on Enterprise with the DATEV export – see our DATEV article."),
            ("The German VAT return (Umsatzsteuer-Voranmeldung) figures from Odoo.", "the tax advisor prepares the VAT return from the DATEV data anyway.")],
    "stk_p": "The standard Inventory app already covers routes, multi-step receipts and lots. These OCA modules close small but annoying gaps:",
    "stk": [("Forbids negative stock per product or category.", "negative stock is never an issue – or you deliberately allow it for drop-ship-like flows."),
            ("Links deliveries and invoices both ways: which picking was invoiced where.", "you invoice exactly by order and nobody asks which delivery an invoice belongs to."),
            ("Cycle counting: count parts of the warehouse regularly instead of one big inventory per year.", "the warehouse is small enough to count completely in a day."),
            ("Mixed rule “take from stock, order the rest”.", "you either always buy to order or always deliver from stock.")],
    "srv": [("Tickets with teams, stages, SLA-like deadlines and a customer portal – for Community.", "you are on Enterprise and use the Helpdesk app."),
            ("A document management system: folders, access rights, files linked to records.", "you are on Enterprise (Documents app), or files live in a separate system such as SharePoint or Nextcloud."),
            ("Shows whether an e-mail was delivered, opened or bounced – right in the chatter.", "your mail server or e-mail provider already reports this and nobody looks inside Odoo.")],
    "inst_p": "OCA repositories are plain git repositories, one per topic, one branch per Odoo version. You clone the branch of your version and add the folder to `addons_path`. In docker it looks like this:",
    "inst_ul": ["Always clone the branch of **your** Odoo version (17.0, 18.0, …). A module from another branch will not install or, worse, will half work.",
                "Many modules depend on modules from other OCA repositories – the manifest `depends` tells you which repositories you also need.",
                "Pin the exact commit you tested (or keep the repositories in your own git) – `git pull` on production without a test is how updates break.",
                "Remove a module the same way: uninstall on the copy first, check, then on production."],
    "first": ["**`web_environment_ribbon`** on every test copy – it costs nothing and prevents “oops, that was production”.",
              "**`auditlog`** on a few critical models: prices, partners' bank accounts, users and access rights.",
              "**`queue_job`** as soon as anything runs longer than a minute: imports, shop sync, mass mailing.",
              "**`account_reconcile_oca`** and **`account_statement_import_camt`** for Community with German banks.",
              "**`mis_builder`** when someone builds the same Excel report every month."],
    "closing": "Modules are cheap to install and expensive to keep. The ones above solve problems that almost every Odoo company meets, they are widely used and maintained for current versions. Install them on a copy, keep the list short, and write down why each module is there – then the next upgrade is a plan, not a surprise. If you want a second opinion on your module list, our smallest hour pack is enough for a review.",
    "links": "Links",
}

_DE = {
    "title": "Odoo-Module, die Ihr ERP leistungsfähiger machen: eine praktische Liste nach Bereichen",
    "summary": "Konkrete Module für Odoo 17 Community und Enterprise, sortiert nach Bereichen – Änderungsprotokoll, Hintergrundjobs, Testdatenbank-Banner, Management-Berichte, Bankabgleich, Anlagen, DATEV, Lagerregeln, Helpdesk, Dokumente, Mail-Tracking: was jedes Modul bringt, wann Sie es nicht brauchen und wie man ein OCA-Modul in Docker installiert.",
    "intro": "Odoo bringt ab Werk viel mit, aber viele Unternehmen stoßen auf dieselben Lücken: Wer hat diesen Preis geändert? Warum blockiert der Import alle anderen? Wo ist der Bankabgleich in Community? Wie bekomme ich eine echte GuV pro Monat? Für die meisten dieser Lücken gibt es bereits ein gut gepflegtes Modul – meist von der Odoo Community Association (OCA). Hier ist unsere kurze Liste nach Bereichen, mit einer ehrlichen Spalte: wann Sie das Modul nicht brauchen.",
    "note": "Alle OCA-Modulnamen unten haben wir am 25. November 2026 in den 17.0-Branches auf github.com/OCA geprüft. Für 18.0 und 19.0 ist die Verfügbarkeit je Modul unterschiedlich – prüfen Sie den Branch Ihrer Version. Wir sind ein unabhängiger Odoo-Dienstleister, kein Odoo-Partner.",
    "h": ["Bevor Sie etwas installieren", "Administration und Betrieb", "Hintergrundjobs: queue_job", "Bedienung",
          "Berichte und Kennzahlen", "Buchhaltung in Community – und für Deutschland", "Lager", "Service, Dokumente, E-Mail",
          "So installieren Sie ein OCA-Modul", "Was wir zuerst installieren würden", "Fazit"],
    "before": "Jedes zusätzliche Modul muss bei jedem Odoo-Update erneut portiert und getestet werden. Woher Module kommen, was ihre Lizenzen bedeuten und eine Checkliste für Fremdcode finden Sie in unserem eigenen Artikel [Odoo-Apps und Module](@blog:odoo-apps-modules-community-enterprise-oca-app-store-what-you-need). Hier geht es nur darum, *welche* Module diesen Preis wert sind. Regel Nummer eins bleibt: zuerst auf einer Kopie der Datenbank installieren.",
    "head": ["Modul", "Repository", "Was es bringt", "Nicht nötig, wenn"],
    "ops": [("Ein Protokoll, wer welches Feld wann geändert hat, mit altem und neuem Wert – für die Modelle, die Sie wählen.", "nie jemand fragt „wer hat das geändert?“ – oder Sie es nur für ein, zwei Felder brauchen; dann reicht das Standard-Tracking im Chatter."),
            ("Findet Reste deinstallierter Module: verwaiste Tabellen, Spalten, Modelle – und entfernt sie.", "die Datenbank neu angelegt wurde und nie ein Modul deinstalliert wurde. Nur auf einer Kopie und mit Backup verwenden."),
            ("Geplante Datenbank-Dumps aus Odoo heraus, optional auf einen entfernten Server.", "Sie bereits mit pg_dump außerhalb von Odoo sichern – was wir empfehlen: Ein Backup sollte nicht von der Anwendung abhängen, die es schützt."),
            ("Ein technischer Benutzer für Cronjobs und Schnittstellen statt des Administrators.", "Sie keine Schnittstellen und keine eigenen geplanten Jobs haben.")],
    "ops_p": "`auditlog` installieren wir am häufigsten. Halten Sie die Liste der protokollierten Modelle kurz – wer jede Änderung an `stock.move` oder `account.move.line` protokolliert, lässt die Protokolltabelle schnell wachsen und bremst arbeitsreiche Tage.",
    "queue_p": "`queue_job` (Repository OCA/queue) verlagert lange Aufgaben in den Hintergrund: Importe, Massen-E-Mails, Abgleich mit einem Shop, Exporte in die Buchhaltung. Die Benutzer warten nicht, fehlgeschlagene Jobs lassen sich wiederholen, und Sie sehen jeden Job mit seinem Fehler. Viele andere OCA-Module bauen darauf auf.",
    "queue_ul": ["Es muss serverweit geladen werden: `server_wide_modules = web,queue_job` in der odoo.conf, und Odoo muss mit Workern laufen (`workers > 0`).",
                 "Kanäle setzen, z. B. `[queue_job] channels = root:2` – sonst kann ein schwerer Import trotzdem alle Worker belegen.",
                 "Bei mehreren Datenbanken auf einem Server braucht der Job-Runner `db_name` oder einen passenden `dbfilter` – die klassische Falle, die wir im Artikel zu `list_db = False` beschreiben.",
                 "Nicht nötig, wenn in Ihrem System nichts länger als ein paar Sekunden läuft."],
    "ux": [("Ein farbiges Banner „TEST“ auf jeder Nicht-Produktiv-Datenbank – einstellbar über Systemparameter.", "Sie nie eine Testkopie haben. Sie sollten eine haben."),
           ("Ein mobilfreundliches App-Menü und Layout für das Backend.", "Sie Odoo 17 oder neuer nutzen: Das Standard-Backend ist bereits responsiv. Sinnvoll vor allem bis Version 16."),
           ("Steuert „Anlegen und bearbeiten…“ und die Anzahl der Einträge in Many2one-Auswahllisten.", "Benutzer nie versehentlich halbleere Datensätze aus einer Auswahlliste anlegen."),
           ("Getrennte Felder für Vor- und Nachname bei Kontakten.", "Sie nur mit Firmen arbeiten oder ein einziges Namensfeld für Briefe und Exporte reicht.")],
    "rep": [("Management-Berichte nach Regeln: GuV pro Monat, Plan/Ist, Kennzahlen je Abteilung – mit Export nach Excel.", "Sie Enterprise nutzen und die Standard-Finanzberichte und Budgets ausreichen."),
            ("Summen- und Saldenliste, Hauptbuch, offene Posten, Altersstruktur – für Community.", "Sie Enterprise nutzen: Die vollständigen Buchhaltungsberichte sind enthalten."),
            ("Eine Basis für Excel-Exporte beliebiger Berichte – Entwickler bauen darauf auf.", "niemand Excel-Dateien braucht, die Odoo selbst erzeugt."),
            ("Benannte Zeiträume (Monate, Quartale, Geschäftsjahre) zur Auswahl in Berichten.", "Sie nur nach Kalendermonaten auswerten.")],
    "rep_p": "`mis_builder` benötigt `date_range` und `report_xlsx` – deshalb stehen sie hier zusammen. Es ist das Modul, das am häufigsten einen wöchentlichen Excel-Export ersetzt.",
    "acc_p": "In Community liefert Odoo Rechnungsstellung und eine Grundbuchhaltung; der Bankabgleich, die Anlagenbuchhaltung und die meisten Berichte sind Enterprise. Genau diese Lücken füllt die OCA. Für Deutschland bringt Odoo die Standard-Lokalisierung `l10n_de` mit den Kontenrahmen SKR03/SKR04 mit; OCA/l10n-germany ergänzt den Rest:",
    "acc": [("Ein Bankabgleich-Bildschirm für Community: Kontoauszugszeilen mit Rechnungen und Zahlungen abgleichen.", "Sie Enterprise nutzen – dort ist der Abgleich enthalten."),
            ("Import von CAMT.053-Kontoauszügen (das Format, das deutsche Banken liefern).", "Ihre Bank online synchronisiert ist oder Sie Enterprise mit eigenem Import nutzen."),
            ("Anlagenbuchhaltung mit Abschreibungsplänen und automatischen Abschreibungsbuchungen.", "Sie Enterprise (App Anlagen) nutzen oder Ihr Steuerberater die Anlagen außerhalb von Odoo führt."),
            ("Export der Buchungen im DATEV-Format für den Steuerberater.", "der Steuerberater direkt in Odoo arbeitet oder Sie Enterprise mit DATEV-Export nutzen – siehe unseren DATEV-Artikel."),
            ("Die Zahlen für die Umsatzsteuer-Voranmeldung aus Odoo.", "der Steuerberater die Voranmeldung ohnehin aus den DATEV-Daten erstellt.")],
    "stk_p": "Die Standard-App Lager deckt Routen, mehrstufige Wareneingänge und Chargen bereits ab. Diese OCA-Module schließen kleine, aber lästige Lücken:",
    "stk": [("Verbietet negativen Bestand je Produkt oder Kategorie.", "negativer Bestand nie ein Thema ist – oder Sie ihn bewusst für streckengeschäftsähnliche Abläufe zulassen."),
            ("Verknüpft Lieferungen und Rechnungen in beide Richtungen: welche Lieferung wo berechnet wurde.", "Sie genau pro Auftrag fakturieren und niemand fragt, zu welcher Lieferung eine Rechnung gehört."),
            ("Permanente Inventur: Teile des Lagers regelmäßig zählen statt einer großen Inventur pro Jahr.", "das Lager klein genug ist, um es an einem Tag komplett zu zählen."),
            ("Gemischte Regel „aus dem Bestand nehmen, den Rest bestellen“.", "Sie entweder immer auftragsbezogen einkaufen oder immer ab Lager liefern.")],
    "srv": [("Tickets mit Teams, Phasen, Fristen und Kundenportal – für Community.", "Sie Enterprise nutzen und die Helpdesk-App verwenden."),
            ("Ein Dokumentenmanagement: Ordner, Zugriffsrechte, Dateien an Datensätzen.", "Sie Enterprise (App Dokumente) nutzen oder Dateien in einem eigenen System wie SharePoint oder Nextcloud liegen."),
            ("Zeigt direkt im Chatter, ob eine E-Mail zugestellt, geöffnet oder abgewiesen wurde.", "Ihr Mailserver oder E-Mail-Anbieter das bereits meldet und niemand in Odoo nachsieht.")],
    "inst_p": "OCA-Repositories sind normale Git-Repositories, eines pro Thema, ein Branch pro Odoo-Version. Sie klonen den Branch Ihrer Version und tragen den Ordner in `addons_path` ein. In Docker sieht das so aus:",
    "inst_ul": ["Immer den Branch **Ihrer** Odoo-Version klonen (17.0, 18.0, …). Ein Modul aus einem anderen Branch installiert sich nicht – oder funktioniert schlimmer noch nur halb.",
                "Viele Module hängen von Modulen aus anderen OCA-Repositories ab – `depends` im Manifest zeigt, welche Repositories Sie zusätzlich brauchen.",
                "Den getesteten Commit festhalten (oder die Repositories im eigenen Git führen) – `git pull` auf dem Produktivsystem ohne Test ist der klassische Weg, wie Updates kaputtgehen.",
                "Ein Modul entfernen Sie genauso: zuerst auf der Kopie deinstallieren, prüfen, dann produktiv."],
    "first": ["**`web_environment_ribbon`** auf jeder Testkopie – kostet nichts und verhindert „Ups, das war produktiv“.",
              "**`auditlog`** auf wenigen kritischen Modellen: Preise, Bankkonten von Partnern, Benutzer und Zugriffsrechte.",
              "**`queue_job`**, sobald etwas länger als eine Minute läuft: Importe, Shop-Abgleich, Massenmails.",
              "**`account_reconcile_oca`** und **`account_statement_import_camt`** für Community mit deutschen Banken.",
              "**`mis_builder`**, wenn jemand jeden Monat denselben Excel-Bericht baut."],
    "closing": "Module sind schnell installiert und teuer im Unterhalt. Die oben genannten lösen Probleme, die fast jedes Odoo-Unternehmen hat; sie sind weit verbreitet und für aktuelle Versionen gepflegt. Installieren Sie sie auf einer Kopie, halten Sie die Liste kurz und notieren Sie, warum jedes Modul da ist – dann ist das nächste Update ein Plan und keine Überraschung. Wenn Sie eine zweite Meinung zu Ihrer Modulliste möchten, reicht unser kleinstes Stundenpaket für eine Durchsicht.",
    "links": "Links",
}

_RU = {
    "title": "Модули Odoo, которые делают ERP мощнее: практический список по областям",
    "summary": "Конкретные модули для Odoo 17 Community и Enterprise по областям – журнал изменений, фоновые задачи, плашка тестовой базы, управленческие отчёты, сверка банка, основные средства, DATEV, правила склада, хелпдеск, документы, отслеживание писем: что даёт каждый, когда он не нужен и как поставить модуль OCA в docker.",
    "intro": "Odoo «из коробки» умеет много, но многие компании упираются в одни и те же пробелы: кто поменял эту цену, почему импорт блокирует всех, где сверка банка в Community, как получить нормальный P&L по месяцам. Почти для каждого такого пробела уже есть хорошо поддерживаемый модуль – чаще всего от Odoo Community Association (OCA). Ниже – наш короткий список по областям, с одной честной колонкой: когда модуль не нужен.",
    "note": "Все технические имена модулей OCA ниже проверены в ветках 17.0 на github.com/OCA 25 ноября 2026. Для 18.0 и 19.0 наличие отличается от модуля к модулю – проверяйте ветку своей версии. Мы независимый поставщик услуг по Odoo, не партнёр Odoo.",
    "h": ["Прежде чем что-то ставить", "Администрирование и эксплуатация", "Фоновые задачи: queue_job", "Удобство работы",
          "Отчёты и показатели", "Бухгалтерия в Community – и для Германии", "Склад", "Сервис, документы, почта",
          "Как установить модуль OCA", "Что мы поставили бы первым", "Итог"],
    "before": "Каждый добавленный модуль нужно заново переносить и тестировать при каждом обновлении Odoo. Откуда берутся модули, что значат их лицензии, и чек-лист для чужого кода – в отдельной статье [Модули Odoo](@blog:odoo-apps-modules-community-enterprise-oca-app-store-what-you-need). Здесь – только о том, *какие* модули стоят этой цены. Правило номер один не меняется: сначала ставим на копию базы.",
    "head": ["Модуль", "Репозиторий", "Что даёт", "Не нужен, если"],
    "ops": [("Журнал: кто, когда и какое поле поменял, со старым и новым значением – для выбранных моделей.", "никто никогда не спрашивает «кто это поменял?» – или нужно одно-два поля: тогда хватает стандартного отслеживания в чаттере."),
            ("Находит остатки удалённых модулей: «осиротевшие» таблицы, колонки, модели – и удаляет их.", "база создана с нуля и модули никогда не удалялись. Только на копии и с бэкапом."),
            ("Плановые дампы базы из самого Odoo, при желании на удалённый сервер.", "вы уже делаете бэкап через pg_dump вне Odoo – как мы и советуем: бэкап не должен зависеть от приложения, которое он защищает."),
            ("Технический пользователь для cron-задач и интеграций вместо администратора.", "у вас нет интеграций и своих плановых задач.")],
    "ops_p": "`auditlog` мы ставим чаще всего. Держите список логируемых моделей коротким: если писать каждое изменение `stock.move` или `account.move.line`, таблица журнала быстро растёт и тормозит загруженные дни.",
    "queue_p": "`queue_job` (репозиторий OCA/queue) уводит долгие задачи в фон: импорты, массовые рассылки, синхронизацию с магазином, выгрузки в бухгалтерию. Пользователи не ждут, упавшие задачи можно перезапустить, и каждая задача видна вместе с ошибкой. На нём построено много других модулей OCA.",
    "queue_ul": ["Модуль грузится на уровне сервера: `server_wide_modules = web,queue_job` в odoo.conf, и Odoo должен работать с воркерами (`workers > 0`).",
                 "Задайте каналы, например `[queue_job] channels = root:2` – иначе один тяжёлый импорт всё равно займёт все воркеры.",
                 "Если на сервере несколько баз, раннеру нужен `db_name` или правильный `dbfilter` – классическая ловушка, которую мы описали в статье про `list_db = False`.",
                 "Не нужен, если у вас ничего не выполняется дольше нескольких секунд."],
    "ux": [("Цветная плашка «TEST» на каждой не-рабочей базе – настраивается системными параметрами.", "у вас никогда нет тестовой копии. А она должна быть."),
           ("Удобное для телефона меню приложений и вёрстка интерфейса.", "у вас Odoo 17 или новее: стандартный интерфейс уже адаптивный. Полезен в основном на 16 и старше."),
           ("Управляет «Создать и изменить…» и числом строк в выпадающих списках many2one.", "пользователи не создают по ошибке полупустые записи из выпадающего списка."),
           ("Отдельные поля имени и фамилии у контактов.", "вы работаете только с компаниями или одного поля имени хватает для писем и выгрузок.")],
    "rep": [("Управленческие отчёты по правилам: P&L по месяцам, план/факт, показатели по отделам – с выгрузкой в Excel.", "у вас Enterprise и стандартных финансовых отчётов и бюджетов достаточно."),
            ("Оборотно-сальдовая ведомость, главная книга, открытые позиции, старение долгов – для Community.", "у вас Enterprise: полные бухгалтерские отчёты там есть."),
            ("Основа для выгрузки любых отчётов в Excel – на ней строят разработчики.", "никому не нужны Excel-файлы, которые формирует сам Odoo."),
            ("Именованные периоды (месяцы, кварталы, финансовые годы) для выбора в отчётах.", "вы смотрите только по календарным месяцам.")],
    "rep_p": "`mis_builder` требует `date_range` и `report_xlsx`, поэтому они здесь вместе. Это тот модуль, который чаще всего заменяет еженедельную ручную выгрузку в Excel.",
    "acc_p": "В Community есть выставление счетов и базовая бухгалтерия; сверка банка, основные средства и большинство отчётов – в Enterprise. Именно эти пробелы и закрывает OCA. Для Германии стандартная локализация `l10n_de` с планами счетов SKR03/SKR04 идёт с Odoo; OCA/l10n-germany добавляет остальное:",
    "acc": [("Экран сверки банка для Community: сопоставление строк выписки со счетами и платежами.", "у вас Enterprise – там своя сверка."),
            ("Импорт выписок CAMT.053 (формат, который дают немецкие банки).", "банк синхронизируется онлайн, или у вас Enterprise со своим импортом."),
            ("Основные средства с графиками амортизации и автоматическими проводками.", "у вас Enterprise (приложение Assets) или налоговый консультант ведёт ОС вне Odoo."),
            ("Выгрузка проводок в формате DATEV для налогового консультанта.", "консультант работает прямо в Odoo, или у вас Enterprise с выгрузкой DATEV – см. нашу статью про DATEV."),
            ("Цифры для ежемесячной декларации по НДС (Umsatzsteuer-Voranmeldung) из Odoo.", "консультант всё равно готовит декларацию по данным DATEV.")],
    "stk_p": "Стандартное приложение «Склад» уже умеет маршруты, многошаговую приёмку и партии. Эти модули OCA закрывают мелкие, но раздражающие пробелы:",
    "stk": [("Запрещает отрицательные остатки по товару или категории.", "отрицательные остатки никогда не проблема – или вы сознательно их допускаете для транзитных схем."),
            ("Связывает отгрузки и счета в обе стороны: какая отгрузка в каком счёте.", "вы выставляете счёт строго по заказу и никто не спрашивает, к какой отгрузке он относится."),
            ("Циклическая инвентаризация: регулярно считать части склада вместо одной большой инвентаризации в год.", "склад настолько мал, что его можно пересчитать целиком за день."),
            ("Смешанное правило «взять со склада, остальное заказать».", "вы либо всегда закупаете под заказ, либо всегда отгружаете со склада.")],
    "srv": [("Тикеты с командами, стадиями, сроками и порталом клиента – для Community.", "у вас Enterprise и вы пользуетесь приложением Helpdesk."),
            ("Система документов: папки, права доступа, файлы, привязанные к записям.", "у вас Enterprise (приложение Documents) или файлы живут в отдельной системе – SharePoint, Nextcloud."),
            ("Показывает прямо в чаттере, доставлено ли письмо, открыто или отклонено.", "почтовый сервер или провайдер уже это показывает и в Odoo никто не смотрит.")],
    "inst_p": "Репозитории OCA – обычные git-репозитории, по одному на тему, по одной ветке на версию Odoo. Клонируете ветку своей версии и добавляете папку в `addons_path`. В docker это выглядит так:",
    "inst_ul": ["Всегда клонируйте ветку **своей** версии Odoo (17.0, 18.0, …). Модуль из другой ветки не установится – или, хуже, будет работать наполовину.",
                "Многие модули зависят от модулей из других репозиториев OCA – `depends` в манифесте покажет, какие репозитории нужны ещё.",
                "Фиксируйте проверенный коммит (или держите репозитории в своём git) – `git pull` на рабочем сервере без теста – классический способ сломать обновление.",
                "Удаляется модуль так же: сначала на копии, проверка, потом на рабочей базе."],
    "first": ["**`web_environment_ribbon`** на каждой тестовой копии – ничего не стоит и спасает от «ой, это была рабочая база».",
              "**`auditlog`** на нескольких критичных моделях: цены, банковские счета партнёров, пользователи и права.",
              "**`queue_job`**, как только что-то идёт дольше минуты: импорты, синхронизация магазина, рассылки.",
              "**`account_reconcile_oca`** и **`account_statement_import_camt`** – для Community с немецкими банками.",
              "**`mis_builder`**, если кто-то каждый месяц собирает один и тот же отчёт в Excel."],
    "closing": "Модули ставятся быстро, а содержать их дорого. Те, что выше, решают задачи, которые встречаются почти в каждой компании на Odoo; они широко используются и поддерживаются для актуальных версий. Ставьте их на копию, держите список коротким и записывайте, зачем нужен каждый модуль, – тогда следующее обновление будет планом, а не сюрпризом. Если нужен второй взгляд на ваш список модулей, для разбора хватит нашего самого маленького пакета часов.",
    "links": "Ссылки",
}

_UK = {
    "title": "Модулі Odoo, які роблять ERP потужнішою: практичний список за напрямками",
    "summary": "Конкретні модулі для Odoo 17 Community та Enterprise за напрямками – журнал змін, фонові задачі, плашка тестової бази, управлінські звіти, звірка банку, основні засоби, DATEV, правила складу, хелпдеск, документи, відстеження листів: що дає кожен, коли він не потрібен і як поставити модуль OCA в docker.",
    "intro": "Odoo «з коробки» вміє багато, але багато компаній натрапляють на ті самі прогалини: хто змінив цю ціну, чому імпорт блокує всіх, де звірка банку в Community, як отримати нормальний P&L по місяцях. Майже для кожної такої прогалини вже є добре підтримуваний модуль – найчастіше від Odoo Community Association (OCA). Нижче – наш короткий список за напрямками, з однією чесною колонкою: коли модуль не потрібен.",
    "note": "Усі технічні назви модулів OCA нижче перевірено в гілках 17.0 на github.com/OCA 25 листопада 2026. Для 18.0 та 19.0 наявність відрізняється від модуля до модуля – перевіряйте гілку своєї версії. Ми незалежний постачальник послуг з Odoo, не партнер Odoo.",
    "h": ["Перш ніж щось ставити", "Адміністрування та експлуатація", "Фонові задачі: queue_job", "Зручність роботи",
          "Звіти та показники", "Бухгалтерія в Community – і для Німеччини", "Склад", "Сервіс, документи, пошта",
          "Як встановити модуль OCA", "Що ми поставили б першим", "Підсумок"],
    "before": "Кожен доданий модуль треба заново переносити й тестувати при кожному оновленні Odoo. Звідки беруться модулі, що означають їхні ліцензії, і чек-лист для чужого коду – в окремій статті [Модулі Odoo](@blog:odoo-apps-modules-community-enterprise-oca-app-store-what-you-need). Тут – лише про те, *які* модулі варті цієї ціни. Правило номер один не змінюється: спершу ставимо на копію бази.",
    "head": ["Модуль", "Репозиторій", "Що дає", "Не потрібен, якщо"],
    "ops": [("Журнал: хто, коли і яке поле змінив, зі старим і новим значенням – для вибраних моделей.", "ніхто ніколи не питає «хто це змінив?» – або потрібно одне-два поля: тоді вистачає стандартного відстеження в чатері."),
            ("Знаходить залишки видалених модулів: «осиротілі» таблиці, колонки, моделі – і видаляє їх.", "базу створено з нуля і модулі ніколи не видалялися. Лише на копії й з бекапом."),
            ("Планові дампи бази з самого Odoo, за бажання на віддалений сервер.", "ви вже робите бекап через pg_dump поза Odoo – як ми й радимо: бекап не має залежати від застосунку, який він захищає."),
            ("Технічний користувач для cron-задач та інтеграцій замість адміністратора.", "у вас немає інтеграцій і власних планових задач.")],
    "ops_p": "`auditlog` ми ставимо найчастіше. Тримайте список моделей у журналі коротким: якщо писати кожну зміну `stock.move` чи `account.move.line`, таблиця журналу швидко росте й гальмує завантажені дні.",
    "queue_p": "`queue_job` (репозиторій OCA/queue) переносить довгі задачі у фон: імпорти, масові розсилки, синхронізацію з магазином, вивантаження в бухгалтерію. Користувачі не чекають, невдалі задачі можна перезапустити, і кожну задачу видно разом із помилкою. На ньому побудовано багато інших модулів OCA.",
    "queue_ul": ["Модуль завантажується на рівні сервера: `server_wide_modules = web,queue_job` в odoo.conf, і Odoo має працювати з воркерами (`workers > 0`).",
                 "Задайте канали, наприклад `[queue_job] channels = root:2` – інакше один важкий імпорт усе одно займе всі воркери.",
                 "Якщо на сервері кілька баз, раннеру потрібен `db_name` або правильний `dbfilter` – класична пастка, яку ми описали в статті про `list_db = False`.",
                 "Не потрібен, якщо у вас нічого не виконується довше кількох секунд."],
    "ux": [("Кольорова плашка «TEST» на кожній не-робочій базі – налаштовується системними параметрами.", "у вас ніколи немає тестової копії. А вона має бути."),
           ("Зручне для телефона меню застосунків і верстка інтерфейсу.", "у вас Odoo 17 або новіший: стандартний інтерфейс уже адаптивний. Корисний переважно на 16 і старших."),
           ("Керує «Створити й змінити…» і кількістю рядків у випадних списках many2one.", "користувачі не створюють помилково напівпорожні записи з випадного списку."),
           ("Окремі поля імені та прізвища в контактах.", "ви працюєте лише з компаніями або одного поля імені вистачає для листів і вивантажень.")],
    "rep": [("Управлінські звіти за правилами: P&L по місяцях, план/факт, показники по відділах – з вивантаженням в Excel.", "у вас Enterprise і стандартних фінансових звітів та бюджетів достатньо."),
            ("Оборотно-сальдова відомість, головна книга, відкриті позиції, старіння боргів – для Community.", "у вас Enterprise: повні бухгалтерські звіти там є."),
            ("Основа для вивантаження будь-яких звітів в Excel – на ній будують розробники.", "нікому не потрібні Excel-файли, які формує сам Odoo."),
            ("Іменовані періоди (місяці, квартали, фінансові роки) для вибору у звітах.", "ви дивитеся лише по календарних місяцях.")],
    "rep_p": "`mis_builder` потребує `date_range` і `report_xlsx`, тому вони тут разом. Це той модуль, що найчастіше замінює щотижневе ручне вивантаження в Excel.",
    "acc_p": "У Community є виставлення рахунків і базова бухгалтерія; звірка банку, основні засоби й більшість звітів – в Enterprise. Саме ці прогалини й закриває OCA. Для Німеччини стандартна локалізація `l10n_de` з планами рахунків SKR03/SKR04 іде з Odoo; OCA/l10n-germany додає решту:",
    "acc": [("Екран звірки банку для Community: зіставлення рядків виписки з рахунками й платежами.", "у вас Enterprise – там своя звірка."),
            ("Імпорт виписок CAMT.053 (формат, який дають німецькі банки).", "банк синхронізується онлайн, або у вас Enterprise зі своїм імпортом."),
            ("Основні засоби з графіками амортизації та автоматичними проводками.", "у вас Enterprise (застосунок Assets) або податковий консультант веде ОЗ поза Odoo."),
            ("Вивантаження проводок у форматі DATEV для податкового консультанта.", "консультант працює просто в Odoo, або у вас Enterprise з вивантаженням DATEV – див. нашу статтю про DATEV."),
            ("Цифри для щомісячної декларації з ПДВ (Umsatzsteuer-Voranmeldung) з Odoo.", "консультант однаково готує декларацію за даними DATEV.")],
    "stk_p": "Стандартний застосунок «Склад» уже вміє маршрути, багатокрокове приймання й партії. Ці модулі OCA закривають дрібні, але дратівливі прогалини:",
    "stk": [("Забороняє від'ємні залишки за товаром або категорією.", "від'ємні залишки ніколи не проблема – або ви свідомо їх допускаєте для транзитних схем."),
            ("Пов'язує відвантаження й рахунки в обидва боки: яке відвантаження в якому рахунку.", "ви виставляєте рахунок суворо за замовленням і ніхто не питає, до якого відвантаження він належить."),
            ("Циклічна інвентаризація: регулярно рахувати частини складу замість однієї великої інвентаризації на рік.", "склад такий малий, що його можна перерахувати повністю за день."),
            ("Змішане правило «взяти зі складу, решту замовити».", "ви або завжди закуповуєте під замовлення, або завжди відвантажуєте зі складу.")],
    "srv": [("Тікети з командами, стадіями, строками й порталом клієнта – для Community.", "у вас Enterprise і ви користуєтеся застосунком Helpdesk."),
            ("Система документів: папки, права доступу, файли, прив'язані до записів.", "у вас Enterprise (застосунок Documents) або файли живуть в окремій системі – SharePoint, Nextcloud."),
            ("Показує просто в чатері, чи лист доставлено, відкрито або відхилено.", "поштовий сервер чи провайдер уже це показує і в Odoo ніхто не дивиться.")],
    "inst_p": "Репозиторії OCA – звичайні git-репозиторії, по одному на тему, по одній гілці на версію Odoo. Клонуєте гілку своєї версії й додаєте папку в `addons_path`. У docker це виглядає так:",
    "inst_ul": ["Завжди клонуйте гілку **своєї** версії Odoo (17.0, 18.0, …). Модуль з іншої гілки не встановиться – або, гірше, працюватиме наполовину.",
                "Багато модулів залежать від модулів з інших репозиторіїв OCA – `depends` у маніфесті покаже, які репозиторії потрібні ще.",
                "Фіксуйте перевірений коміт (або тримайте репозиторії у своєму git) – `git pull` на робочому сервері без тесту – класичний спосіб зламати оновлення.",
                "Видаляється модуль так само: спершу на копії, перевірка, потім на робочій базі."],
    "first": ["**`web_environment_ribbon`** на кожній тестовій копії – нічого не коштує й рятує від «ой, це була робоча база».",
              "**`auditlog`** на кількох критичних моделях: ціни, банківські рахунки партнерів, користувачі та права.",
              "**`queue_job`**, щойно щось триває довше хвилини: імпорти, синхронізація магазину, розсилки.",
              "**`account_reconcile_oca`** і **`account_statement_import_camt`** – для Community з німецькими банками.",
              "**`mis_builder`**, якщо хтось щомісяця збирає той самий звіт в Excel."],
    "closing": "Модулі ставляться швидко, а утримувати їх дорого. Ті, що вище, розв'язують задачі, які трапляються майже в кожній компанії на Odoo; вони широко використовуються й підтримуються для актуальних версій. Ставте їх на копію, тримайте список коротким і записуйте, навіщо потрібен кожен модуль, – тоді наступне оновлення буде планом, а не сюрпризом. Якщо потрібен другий погляд на ваш список модулів, для розбору вистачить нашого найменшого пакета годин.",
    "links": "Посилання",
}

for _l, _x in (("en", _EN), ("de", _DE), ("ru", _RU), ("uk", _UK)):
    USEFULMODS_POST["t"][_l] = {"title": _x["title"], "summary": _x["summary"], "body": _body(_x)}
