# Статья 30: Odoo и DATEV пошагово – Community (OCA datev_export_dtvf) и Enterprise (Datev DATA/ATCH). Проверено
# 2026-11-18 на Odoo 18 Community + OCA l10n-germany 18.0 (83e8d6a), тестовая база (SKR03, счёт 690 € + 19 %,
# счёт поставщика 120 € + 19 %). Языки: en, de, ru, uk (fr/el – английская версия с пометкой).

DATEV = {
    "slug": "odoo-datev-export-step-by-step-community-enterprise",
    "date": "2026-11-18",
    "tags": ["Odoo", "DATEV", "Accounting", "Germany"],
    "code": {
        "addons": ("bash · get the OCA modules (Odoo 18; same for 17 with branch 17.0)", """cd /opt/odoo/addons-oca            # any directory in addons_path
git clone -b 18.0 --depth 1 https://github.com/OCA/l10n-germany
git clone -b 18.0 --depth 1 https://github.com/OCA/server-ux     # date_range (fiscal year, months)
# odoo.conf:  addons_path = ...,/opt/odoo/addons-oca/l10n-germany,/opt/odoo/addons-oca/server-ux
sudo systemctl restart odoo
# Apps -> Update Apps List -> search "Datev Export DTVF" -> Install
# (command line: odoo -d <db> -i datev_export_dtvf --stop-after-init)"""),
        "result": ("our test database · invoice INV/2026/00001 (690 € + 19 %) and bill BILL/2026/11/0001 (120 € + 19 %)", """ZIP DATEV_2026-11.zip: EXTF_Buchungsstapel_20261101.csv, EXTF_DebKred_Stamm.csv, EXTF_Kontenbeschriftungen.csv

EXTF_Buchungsstapel – first columns (Umsatz; S/H; WKZ; Kurs; Basis; WKZ; Konto; Gegenkonto; BU; Datum; Beleg 1; Beleg 2; Skonto; Text)
690,00;"S";"EUR";1,000000;690,00;"EUR";10000;8400;"40";1811;"INV/2026/00001";"Wallbox Mont";;"INV/2026/00001"
131,10;"S";"EUR";1,000000;131,10;"EUR";10000;1776;"";1811;"INV/2026/00001";"19%";;"INV/2026/00001"
120,00;"H";"EUR";1,000000;120,00;"EUR";70000;3400;"40";1811;"BILL/2026/11/0001";"Kabel NYM-J ";;"RE-4711"
22,80;"H";"EUR";1,000000;22,80;"EUR";70000;1576;"";1811;"BILL/2026/11/0001";"19% I";;"RE-4711"

EXTF_DebKred_Stamm
10000;"Beispiel Kunde GmbH";...;"DE";...;"Königstraße 10";"";"70173";"Stuttgart";"DE";...
70000;"Elektro Großhandel KG";...

# without partner numbering, Konto was 1410 / 1610 (collective accounts) and the partners got numbers 7 and 8 (database IDs)
# without the BU-40 flag, the lines to 8400 / 3400 had an empty BU-Schlüssel"""),
        "check": ("bash · look into the file before sending it", """unzip -o DATEV_2026-11.zip -d datev && cd datev
head -c 3 EXTF_Buchungsstapel_*.csv | xxd     # efbbbf = UTF-8 with BOM
cut -d';' -f1-11 EXTF_Buchungsstapel_*.csv | head
# sum of all S amounts = sum of all H amounts?  the tax advisor will check the same"""),
    },
    "links": [
        ("OCA l10n-germany (datev_export_dtvf, datev_export_xml, datev_import_csv_dtvf, l10n_de_tax_statement)", "https://github.com/OCA/l10n-germany/tree/18.0"),
        ("Odoo 18 documentation: Germany (DATEV, GoBD, SKR03/SKR04)", "https://www.odoo.com/documentation/18.0/applications/finance/fiscal_localizations/germany.html"),
        ("Blog: what companies in Germany search for in a CRM (DATEV is one of the top Odoo searches)", "@blog:crm-germany-what-people-search-google-autocomplete"),
        ("Blog: Odoo costs realistically", "@blog:odoo-costs-licence-hosting-implementation-germany"),
    ],
    "t": {},
}


def _d(title, summary, intro, note, h, which_p, which_table, pre_ul, steps, result_p, traps_ul, ee_p, ee_ul, other_ul,
       closing, links):
    return {"title": title, "summary": summary, "body": [
        ("p", intro), ("note", note),
        ("h", h[0]), ("p", which_p), ("table", which_table),
        ("h", h[1]), ("ul", pre_ul),
        ("h", h[2]), ("ol", steps[:3]), ("code", "addons"), ("ol", steps[3:]),
        ("h", h[3]), ("p", result_p), ("code", "result"), ("code", "check"),
        ("h", h[4]), ("ul", traps_ul),
        ("h", h[5]), ("p", ee_p), ("ul", ee_ul),
        ("h", h[6]), ("ul", other_ul),
        ("h", h[7]), ("p", closing),
        ("links", links)]}


DATEV["t"]["en"] = _d(
    "Odoo and DATEV step by step: export for the tax advisor in Community (OCA) and Enterprise",
    "Most small companies in Germany do their bookkeeping with a tax advisor who works in DATEV. How to get invoices and bills from Odoo to DATEV: the Community way with the OCA module datev_export_dtvf (tested on Odoo 18 with real output), the Enterprise way (Datev DATA / ATCH), the settings that decide whether the import works – partner numbers, automatic accounts, Berater- and Mandantennummer – and what to agree with the tax advisor first.",
    "\"Odoo DATEV\" and \"Odoo DATEV Schnittstelle\" are among the most frequent German Odoo searches. The reason is simple: most small companies in Germany write invoices themselves, but the bookkeeping, VAT return and annual accounts are done by a tax advisor – in DATEV. So Odoo has to deliver data that DATEV can import without retyping.",
    "We tested the Community way on Odoo 18 Community with the OCA modules from l10n-germany (branch 18.0, as of September 2026) in a separate test database: SKR03, one customer invoice (690 € + 19 %), one vendor bill (120 € + 19 %). The outputs below are from that test. The Enterprise way is described from the official Odoo documentation – we did not test it here.",
    ["Which way: Community or Enterprise", "Before you start", "Step by step: Community with OCA", "What comes out", "The traps we hit", "Enterprise: Datev DATA and ATCH", "Other DATEV modules", "Conclusion"],
    "There are two DATEV formats that matter for a small company: the **Buchungsstapel** (journal entries as a CSV file – the tax advisor imports them into DATEV Rechnungswesen) and **document transfer** (invoice PDFs and XML into DATEV Unternehmen online). Which one your tax advisor wants is the first question.",
    [["", "Odoo Community + OCA", "Odoo Enterprise"],
     ["Journal entries (Buchungsstapel)", "`datev_export_dtvf`: ZIP with EXTF_Buchungsstapel, DebKred_Stamm, Kontenbeschriftungen", "Accounting ‣ Reporting ‣ General Ledger ‣ Datev DATA (zip)"],
     ["Invoice documents", "`datev_export_xml`: XML + PDF for DATEV Unternehmen online", "General Ledger ‣ Datev ATCH (zip) for DATEV Belegtransfer"],
     ["Import from DATEV (payroll, year-end)", "`datev_import_csv_dtvf`", "–"],
     ["VAT return (UStVA)", "`l10n_de_tax_statement` (OCA; needs tax tag configuration – not tested here)", "German tax report"],
     ["Licence", "free (AGPL), you maintain the modules", "Enterprise subscription"]],
    ["**Chart of accounts SKR03 or SKR04** – ask the tax advisor which one. It can only be changed **before the first posted entry**; afterwards you need a new company or database.",
     "**Beraternummer and Mandantennummer** – from the tax advisor (the consultant number has 4–8 digits, the client number up to 5).",
     "**Account length** – usually 4 digits for G/L accounts, so customers and suppliers get 5-digit personal accounts (10000–69999 customers, 70000–99999 suppliers). Again: ask.",
     "**Which format and how often** – Buchungsstapel monthly is the usual case; some advisors prefer documents via DATEV Unternehmen online.",
     "**A test month** – agree that the first export is a test: the advisor imports it into a test client and tells you what does not fit."],
    ["**Install the German localisation**: Apps ‣ \"Germany - Accounting\" (`l10n_de`). In Settings ‣ Invoicing ‣ Fiscal Localization choose **SKR03** or **SKR04** – before posting anything.",
     "**Company data**: Settings ‣ Companies: address, tax number, VAT ID. They end up on invoices and in the export header.",
     "**Get the OCA modules** `datev_export_dtvf` (from OCA/l10n-germany) and `date_range` (from OCA/server-ux) and install them:",
     "**DATEV settings**: Settings ‣ Invoicing ‣ block **DATEV Export**: Consultant Number, Client Number, **DATEV account code length** (4), **DATEV Partner numbering** = Sequence, with one sequence for customers (starting at 10000) and one for suppliers (starting at 70000). Create the sequences under Settings ‣ Technical ‣ Sequences (debug mode).",
     "**Automatic accounts**: in SKR03, accounts such as 8400 (revenue 19 %) and 3400 (goods 19 %) are automatic accounts in DATEV – DATEV calculates the VAT from the amount itself. Odoo already exports the VAT as a separate line. Open these accounts (Invoicing ‣ Configuration ‣ Chart of Accounts) and tick **Suppress automatic calculations in DATEV** – the lines then get BU-Schlüssel 40. Agree this with the tax advisor.",
     "**Date ranges**: Settings ‣ Technical ‣ Date ranges: one range for the fiscal year (e.g. 2026) and one per month (2026-11 …).",
     "**Export**: Invoicing ‣ Reporting ‣ **DATEV export** ‣ New: name, fiscal year, periods (months), optionally journals ‣ **Generate** ‣ download the ZIP.",
     "**Check and send**: look into the file (below), send it to the tax advisor, get feedback on the test month, then repeat monthly. Posted entries are exported – drafts are not."],
    "For our test month the module created a ZIP with three files. In the journal entries every invoice is split into lines from the personal account to the G/L account – revenue and VAT separately:",
    ["**Without partner numbering**, Konto was the collective account 1410 / 1610 and the partner master data got the database IDs 7 and 8 as numbers. The tax advisor cannot work with that – set \"Sequence\".",
     "**Automatic accounts**: without the flag, the lines to 8400 / 3400 had an empty BU-Schlüssel, while the VAT came as its own line – DATEV would calculate VAT a second time. With the flag: BU 40.",
     "**Encoding**: the CSV files are UTF-8 with BOM. Current DATEV versions read that; if umlauts arrive broken, this is the place to look.",
     "**Partners appear twice** in EXTF_DebKred_Stamm in our test (once per invoice line). DATEV overwrites with the same data, but it is worth knowing when you compare.",
     "**Text fields are cut** to DATEV lengths (\"Wallbox Mont\") – keep invoice line descriptions short at the start.",
     "**Only posted entries** of the chosen periods are exported – an invoice posted later with an older date needs a new export of that month (agree how corrections are handled)."],
    "Odoo Enterprise brings the DATEV export in its German accounting reports. According to the Odoo 18 documentation:",
    ["**Datev DATA (zip)**: Accounting ‣ Reporting ‣ General Ledger ‣ actions ‣ Datev DATA (zip) – customers, vendors and journal items as EXTF CSV files for DATEV Rechnungswesen.",
     "**Datev ATCH (zip)**: same place – the invoice and bill files plus document.xml for DATEV Belegtransfer; the journal items reference the documents by GUID.",
     "Customer invoice files must have been created with **Send**, vendor bills received by e-mail alias or uploaded.",
     "Odoo states it is **certified GoBD-compliant**; on-premise you are responsible for backups yourself."],
    ["**`datev_export_xml`** – invoices and bills as XML + PDF for DATEV Unternehmen online (upload via the free DATEV transfer app). Not for pure G/L postings such as payments.",
     "**`datev_import_csv_dtvf`** – the other direction: import DATEV CSV from the tax advisor (payroll, depreciation, year-end entries) as journal entries.",
     "**`l10n_de_tax_statement`** – the UStVA (VAT return) to transfer to ELSTER; needs the tax tags configured per line.",
     "**E-invoicing**: XRechnung and ZUGFeRD come with Odoo's standard module `account_edi_ubl_cii` – a separate topic."],
    "DATEV and Odoo work together in Community too – with an OCA module, five settings and one test month with the tax advisor. The work is not the export button but the agreement: chart of accounts, account length, partner numbers, automatic accounts. We set this up for companies in Germany, Austria and Switzerland and can show the whole path on a test database before your data is involved.",
    "Links")

DATEV["t"]["de"] = _d(
    "Odoo und DATEV Schritt für Schritt: Export für den Steuerberater in Community (OCA) und Enterprise",
    "Die meisten kleinen Unternehmen in Deutschland buchen mit einem Steuerberater, der in DATEV arbeitet. Wie Rechnungen und Eingangsrechnungen aus Odoo zu DATEV kommen: der Community-Weg mit dem OCA-Modul datev_export_dtvf (auf Odoo 18 getestet, mit echter Ausgabe), der Enterprise-Weg (Datev DATA / ATCH), die Einstellungen, an denen der Import hängt – Personenkonten, Automatikkonten, Berater- und Mandantennummer – und was man vorher mit dem Steuerberater klärt.",
    "„Odoo DATEV“ und „Odoo DATEV Schnittstelle“ gehören zu den häufigsten deutschen Odoo-Suchen. Der Grund ist einfach: Die meisten kleinen Firmen in Deutschland schreiben Rechnungen selbst, aber Buchhaltung, Umsatzsteuervoranmeldung und Jahresabschluss macht der Steuerberater – in DATEV. Odoo muss also Daten liefern, die DATEV ohne Abtippen einlesen kann.",
    "Den Community-Weg haben wir auf Odoo 18 Community mit den OCA-Modulen aus l10n-germany (Zweig 18.0, Stand September 2026) in einer separaten Testdatenbank geprüft: SKR03, eine Ausgangsrechnung (690 € + 19 %), eine Eingangsrechnung (120 € + 19 %). Die Ausgaben unten stammen aus diesem Test. Den Enterprise-Weg beschreiben wir nach der offiziellen Odoo-Dokumentation – hier nicht getestet.",
    ["Welcher Weg: Community oder Enterprise", "Bevor es losgeht", "Schritt für Schritt: Community mit OCA", "Was herauskommt", "Die Fallen, in die wir getreten sind", "Enterprise: Datev DATA und ATCH", "Weitere DATEV-Module", "Fazit"],
    "Für ein kleines Unternehmen zählen zwei DATEV-Formate: der **Buchungsstapel** (Buchungen als CSV – der Steuerberater liest sie in DATEV Rechnungswesen ein) und der **Belegtransfer** (Rechnungs-PDF und XML in DATEV Unternehmen online). Was Ihr Steuerberater möchte, ist die erste Frage.",
    [["", "Odoo Community + OCA", "Odoo Enterprise"],
     ["Buchungen (Buchungsstapel)", "`datev_export_dtvf`: ZIP mit EXTF_Buchungsstapel, DebKred_Stamm, Kontenbeschriftungen", "Buchhaltung ‣ Berichtswesen ‣ Hauptbuch ‣ Datev DATA (zip)"],
     ["Belege", "`datev_export_xml`: XML + PDF für DATEV Unternehmen online", "Hauptbuch ‣ Datev ATCH (zip) für DATEV Belegtransfer"],
     ["Import aus DATEV (Lohn, Abschluss)", "`datev_import_csv_dtvf`", "–"],
     ["Umsatzsteuervoranmeldung", "`l10n_de_tax_statement` (OCA; braucht Konfiguration der Steuer-Tags – hier nicht getestet)", "Deutscher Steuerbericht"],
     ["Lizenz", "kostenlos (AGPL), Module pflegen Sie selbst", "Enterprise-Abo"]],
    ["**Kontenrahmen SKR03 oder SKR04** – den Steuerberater fragen. Er lässt sich nur **vor der ersten gebuchten Buchung** ändern; danach braucht man eine neue Firma oder Datenbank.",
     "**Beraternummer und Mandantennummer** – vom Steuerberater (Beraternummer 4–8 Stellen, Mandantennummer bis 5).",
     "**Sachkontenlänge** – meist 4 Stellen, damit bekommen Kunden und Lieferanten 5-stellige Personenkonten (10000–69999 Debitoren, 70000–99999 Kreditoren). Auch das: fragen.",
     "**Welches Format, wie oft** – monatlicher Buchungsstapel ist der Normalfall; manche Kanzleien wollen lieber Belege über DATEV Unternehmen online.",
     "**Ein Testmonat** – vereinbaren, dass der erste Export ein Test ist: Die Kanzlei liest ihn in einen Testmandanten ein und sagt, was nicht passt."],
    ["**Deutsche Lokalisierung installieren**: Apps ‣ „Deutschland – Buchhaltung“ (`l10n_de`). Unter Einstellungen ‣ Rechnungsstellung ‣ Steuerliche Lokalisierung **SKR03** oder **SKR04** wählen – bevor irgendetwas gebucht ist.",
     "**Firmendaten**: Einstellungen ‣ Unternehmen: Anschrift, Steuernummer, USt-IdNr. Sie landen auf Rechnungen und im Kopf des Exports.",
     "**OCA-Module holen** – `datev_export_dtvf` (aus OCA/l10n-germany) und `date_range` (aus OCA/server-ux) – und installieren:",
     "**DATEV-Einstellungen**: Einstellungen ‣ Rechnungsstellung ‣ Block **DATEV Export**: Beraternummer (Consultant Number), Mandantennummer (Client Number), **DATEV account code length** (4), **DATEV Partner numbering** = Sequence, mit je einer Nummernfolge für Kunden (ab 10000) und Lieferanten (ab 70000). Die Folgen unter Einstellungen ‣ Technisch ‣ Nummernfolgen anlegen (Entwicklermodus).",
     "**Automatikkonten**: Im SKR03 sind z. B. 8400 (Erlöse 19 %) und 3400 (Wareneingang 19 %) in DATEV Automatikkonten – DATEV rechnet die Umsatzsteuer selbst aus dem Betrag heraus. Odoo exportiert die Steuer aber schon als eigene Zeile. Diese Konten öffnen (Rechnungsstellung ‣ Konfiguration ‣ Kontenplan) und **Suppress automatic calculations in DATEV** anhaken – die Zeilen bekommen dann BU-Schlüssel 40. Mit dem Steuerberater abstimmen.",
     "**Datumsbereiche**: Einstellungen ‣ Technisch ‣ Date ranges: ein Bereich für das Geschäftsjahr (z. B. 2026) und einer je Monat (2026-11 …).",
     "**Export**: Rechnungsstellung ‣ Berichtswesen ‣ **DATEV export** ‣ Neu: Name, Geschäftsjahr, Perioden (Monate), optional Journale ‣ **Generate** ‣ ZIP herunterladen.",
     "**Prüfen und senden**: in die Datei schauen (unten), an die Kanzlei schicken, Rückmeldung zum Testmonat abwarten, dann monatlich wiederholen. Exportiert werden gebuchte Buchungen – Entwürfe nicht."],
    "Für unseren Testmonat hat das Modul ein ZIP mit drei Dateien erzeugt. Im Buchungsstapel wird jede Rechnung in Zeilen vom Personenkonto auf das Sachkonto aufgeteilt – Erlös und Umsatzsteuer getrennt:",
    ["**Ohne Personenkonten-Nummerierung** stand im Feld Konto das Sammelkonto 1410 / 1610, und die Stammdaten bekamen die Datenbank-IDs 7 und 8 als Nummern. Damit kann die Kanzlei nichts anfangen – „Sequence“ einstellen.",
     "**Automatikkonten**: Ohne den Haken hatten die Zeilen auf 8400 / 3400 einen leeren BU-Schlüssel, während die Steuer als eigene Zeile kam – DATEV würde die Umsatzsteuer ein zweites Mal rechnen. Mit Haken: BU 40.",
     "**Zeichensatz**: Die CSV-Dateien sind UTF-8 mit BOM. Aktuelle DATEV-Versionen lesen das; kommen Umlaute kaputt an, ist hier die Stelle.",
     "**Partner doppelt** in EXTF_DebKred_Stamm in unserem Test (einmal je Rechnungszeile). DATEV überschreibt mit denselben Daten, aber beim Vergleichen sollte man es wissen.",
     "**Textfelder werden gekürzt** auf DATEV-Längen („Wallbox Mont“) – Positionstexte am Anfang kurz halten.",
     "**Nur gebuchte Buchungen** der gewählten Perioden werden exportiert – eine später gebuchte Rechnung mit älterem Datum braucht einen neuen Export dieses Monats (abstimmen, wie Korrekturen laufen)."],
    "Odoo Enterprise bringt den DATEV-Export in den deutschen Buchhaltungsberichten mit. Laut Odoo-18-Dokumentation:",
    ["**Datev DATA (zip)**: Buchhaltung ‣ Berichtswesen ‣ Hauptbuch ‣ Aktionen ‣ Datev DATA (zip) – Kunden, Lieferanten und Buchungszeilen als EXTF-CSV für DATEV Rechnungswesen.",
     "**Datev ATCH (zip)**: an derselben Stelle – die Rechnungsdateien plus document.xml für DATEV Belegtransfer; die Buchungen verweisen per GUID auf die Belege.",
     "Ausgangsrechnungen müssen mit **Senden** erzeugt, Eingangsrechnungen per E-Mail-Alias empfangen oder hochgeladen sein.",
     "Odoo gibt an, **GoBD-zertifiziert** zu sein; on-premise ist man für Backups selbst verantwortlich."],
    ["**`datev_export_xml`** – Rechnungen als XML + PDF für DATEV Unternehmen online (Upload mit der kostenlosen DATEV-Übertragungs-App). Nicht für reine Sachkontenbuchungen wie Zahlungen.",
     "**`datev_import_csv_dtvf`** – die andere Richtung: DATEV-CSV vom Steuerberater (Lohn, AfA, Abschlussbuchungen) als Buchungen importieren.",
     "**`l10n_de_tax_statement`** – die Umsatzsteuervoranmeldung zur Übertragung an ELSTER; braucht die Steuer-Tags je Zeile.",
     "**E-Rechnung**: XRechnung und ZUGFeRD kommen mit dem Odoo-Standardmodul `account_edi_ubl_cii` – ein eigenes Thema."],
    "DATEV und Odoo funktionieren auch in der Community – mit einem OCA-Modul, fünf Einstellungen und einem Testmonat mit der Kanzlei. Die Arbeit ist nicht der Export-Knopf, sondern die Abstimmung: Kontenrahmen, Kontenlänge, Personenkonten, Automatikkonten. Wir richten das für Unternehmen in Deutschland, Österreich und der Schweiz ein und zeigen den ganzen Weg gern auf einer Testdatenbank, bevor Ihre Daten im Spiel sind.",
    "Links")

DATEV["t"]["ru"] = _d(
    "Odoo и DATEV пошагово: выгрузка для налогового консультанта в Community (OCA) и Enterprise",
    "Большинство маленьких компаний в Германии ведут учёт через налогового консультанта (Steuerberater), который работает в DATEV. Как передать счета из Odoo в DATEV: путь Community с модулем OCA datev_export_dtvf (проверено на Odoo 18, с реальным выводом), путь Enterprise (Datev DATA / ATCH), настройки, от которых зависит импорт – номера контрагентов, автоматические счета, номер консультанта и клиента – и что заранее обсудить с консультантом.",
    "«Odoo DATEV» и «Odoo DATEV Schnittstelle» – одни из самых частых немецких запросов про Odoo. Причина простая: большинство маленьких фирм в Германии выставляют счета сами, а бухгалтерию, декларацию НДС и годовую отчётность делает Steuerberater – в DATEV. Значит, Odoo должен отдавать данные, которые DATEV прочитает без перепечатывания.",
    "Путь Community мы проверили на Odoo 18 Community с модулями OCA из l10n-germany (ветка 18.0, состояние на сентябрь 2026) в отдельной тестовой базе: SKR03, один счёт клиенту (690 € + 19 %), один счёт поставщика (120 € + 19 %). Вывод ниже – из этого теста. Путь Enterprise описан по официальной документации Odoo – здесь мы его не проверяли.",
    ["Какой путь: Community или Enterprise", "До начала", "Пошагово: Community с OCA", "Что получается", "Ловушки, в которые мы попали", "Enterprise: Datev DATA и ATCH", "Другие модули DATEV", "Вывод"],
    "Для маленькой компании важны два формата DATEV: **Buchungsstapel** (проводки в CSV – консультант загружает их в DATEV Rechnungswesen) и **передача документов** (PDF и XML счетов в DATEV Unternehmen online). Что нужно вашему консультанту – первый вопрос.",
    [["", "Odoo Community + OCA", "Odoo Enterprise"],
     ["Проводки (Buchungsstapel)", "`datev_export_dtvf`: ZIP с EXTF_Buchungsstapel, DebKred_Stamm, Kontenbeschriftungen", "Бухгалтерия ‣ Отчёты ‣ Главная книга ‣ Datev DATA (zip)"],
     ["Документы", "`datev_export_xml`: XML + PDF для DATEV Unternehmen online", "Главная книга ‣ Datev ATCH (zip) для DATEV Belegtransfer"],
     ["Импорт из DATEV (зарплата, закрытие года)", "`datev_import_csv_dtvf`", "–"],
     ["Декларация НДС (UStVA)", "`l10n_de_tax_statement` (OCA; нужна настройка налоговых тегов – здесь не проверяли)", "Немецкий налоговый отчёт"],
     ["Лицензия", "бесплатно (AGPL), модули поддерживаете сами", "подписка Enterprise"]],
    ["**План счетов SKR03 или SKR04** – спросите консультанта. Поменять его можно только **до первой проведённой записи**; потом нужна новая компания или база.",
     "**Beraternummer и Mandantennummer** – от консультанта (номер консультанта 4–8 цифр, номер клиента до 5).",
     "**Длина счетов** – обычно 4 цифры для счетов главной книги, тогда клиенты и поставщики получают 5-значные личные счета (10000–69999 дебиторы, 70000–99999 кредиторы). Тоже уточнить.",
     "**Какой формат и как часто** – обычно Buchungsstapel раз в месяц; некоторые консультанты хотят документы через DATEV Unternehmen online.",
     "**Тестовый месяц** – договоритесь, что первая выгрузка тестовая: консультант загружает её в тестового клиента и говорит, что не подходит."],
    ["**Установить немецкую локализацию**: Приложения ‣ «Germany - Accounting» (`l10n_de`). В Настройки ‣ Счета ‣ Фискальная локализация выбрать **SKR03** или **SKR04** – до любых проводок.",
     "**Данные компании**: Настройки ‣ Компании: адрес, налоговый номер, USt-IdNr. Они попадают в счета и в заголовок выгрузки.",
     "**Взять модули OCA** – `datev_export_dtvf` (из OCA/l10n-germany) и `date_range` (из OCA/server-ux) – и установить:",
     "**Настройки DATEV**: Настройки ‣ Счета ‣ блок **DATEV Export**: Consultant Number, Client Number, **DATEV account code length** (4), **DATEV Partner numbering** = Sequence, с последовательностью для клиентов (с 10000) и для поставщиков (с 70000). Последовательности создать в Настройки ‣ Технические ‣ Последовательности (режим разработчика).",
     "**Автоматические счета**: в SKR03 счета вроде 8400 (выручка 19 %) и 3400 (закупка 19 %) в DATEV – Automatikkonten: DATEV сам выделяет НДС из суммы. А Odoo уже выгружает НДС отдельной строкой. Откройте эти счета (Счета ‣ Настройка ‣ План счетов) и включите **Suppress automatic calculations in DATEV** – строки получат BU-Schlüssel 40. Согласуйте с консультантом.",
     "**Периоды**: Настройки ‣ Технические ‣ Date ranges: один период на финансовый год (например, 2026) и по одному на месяц (2026-11 …).",
     "**Выгрузка**: Счета ‣ Отчёты ‣ **DATEV export** ‣ Создать: название, финансовый год, периоды (месяцы), при необходимости журналы ‣ **Generate** ‣ скачать ZIP.",
     "**Проверить и отправить**: заглянуть в файл (ниже), отправить консультанту, дождаться ответа по тестовому месяцу, дальше – ежемесячно. Выгружаются только проведённые записи, черновики – нет."],
    "Для тестового месяца модуль создал ZIP из трёх файлов. В проводках каждый счёт разбит на строки с личного счёта на счёт главной книги – выручка и НДС отдельно:",
    ["**Без нумерации контрагентов** в поле Konto был собирательный счёт 1410 / 1610, а в справочнике партнёры получили номера 7 и 8 (ID в базе). Консультанту это не подходит – ставьте «Sequence».",
     "**Автоматические счета**: без флага строки на 8400 / 3400 шли с пустым BU-Schlüssel, а НДС приходил отдельной строкой – DATEV посчитал бы НДС второй раз. С флагом: BU 40.",
     "**Кодировка**: CSV в UTF-8 с BOM. Текущие версии DATEV это читают; если умлауты приходят битыми – смотреть сюда.",
     "**Партнёры дважды** в EXTF_DebKred_Stamm в нашем тесте (по разу на строку счёта). DATEV перезапишет теми же данными, но при сверке это стоит знать.",
     "**Текстовые поля обрезаются** до длины DATEV («Wallbox Mont») – описания позиций лучше делать короткими.",
     "**Только проведённые записи** выбранных периодов – счёт, проведённый позже задним числом, требует новой выгрузки того месяца (договоритесь, как идут исправления)."],
    "В Odoo Enterprise выгрузка DATEV встроена в немецкие бухгалтерские отчёты. По документации Odoo 18:",
    ["**Datev DATA (zip)**: Бухгалтерия ‣ Отчёты ‣ Главная книга ‣ действия ‣ Datev DATA (zip) – клиенты, поставщики и проводки в EXTF CSV для DATEV Rechnungswesen.",
     "**Datev ATCH (zip)**: там же – файлы счетов и document.xml для DATEV Belegtransfer; проводки ссылаются на документы по GUID.",
     "Файлы счетов клиентам должны быть созданы кнопкой **Отправить**, счета поставщиков – получены через e-mail-алиас или загружены.",
     "Odoo заявляет **сертификацию GoBD**; on-premise за бэкапы отвечаете вы."],
    ["**`datev_export_xml`** – счета как XML + PDF для DATEV Unternehmen online (загрузка бесплатным приложением DATEV). Не для чистых проводок по счетам, например платежей.",
     "**`datev_import_csv_dtvf`** – обратное направление: импорт CSV из DATEV от консультанта (зарплата, амортизация, закрытие года) как проводок.",
     "**`l10n_de_tax_statement`** – декларация НДС (UStVA) для ELSTER; нужна настройка налоговых тегов по строкам.",
     "**Электронные счета**: XRechnung и ZUGFeRD – в стандартном модуле Odoo `account_edi_ubl_cii`, это отдельная тема."],
    "DATEV и Odoo работают и в Community – с модулем OCA, пятью настройками и тестовым месяцем у консультанта. Работа не в кнопке выгрузки, а в договорённостях: план счетов, длина счетов, номера контрагентов, автоматические счета. Мы настраиваем это для компаний в Германии, Австрии и Швейцарии и можем показать весь путь на тестовой базе, прежде чем в дело пойдут ваши данные.",
    "Ссылки")

DATEV["t"]["uk"] = _d(
    "Odoo і DATEV покроково: вивантаження для податкового консультанта в Community (OCA) та Enterprise",
    "Більшість малих компаній у Німеччині ведуть облік через податкового консультанта (Steuerberater), який працює в DATEV. Як передати рахунки з Odoo в DATEV: шлях Community з модулем OCA datev_export_dtvf (перевірено на Odoo 18, з реальним виводом), шлях Enterprise (Datev DATA / ATCH), налаштування, від яких залежить імпорт – номери контрагентів, автоматичні рахунки, номер консультанта й клієнта – і що заздалегідь обговорити з консультантом.",
    "«Odoo DATEV» і «Odoo DATEV Schnittstelle» – одні з найчастіших німецьких запитів про Odoo. Причина проста: більшість малих фірм у Німеччині виставляють рахунки самі, а бухгалтерію, декларацію ПДВ і річну звітність робить Steuerberater – у DATEV. Отже, Odoo має віддавати дані, які DATEV прочитає без передруковування.",
    "Шлях Community ми перевірили на Odoo 18 Community з модулями OCA з l10n-germany (гілка 18.0, стан на вересень 2026) в окремій тестовій базі: SKR03, один рахунок клієнту (690 € + 19 %), один рахунок постачальника (120 € + 19 %). Вивід нижче – з цього тесту. Шлях Enterprise описано за офіційною документацією Odoo – тут ми його не перевіряли.",
    ["Який шлях: Community чи Enterprise", "Перед початком", "Покроково: Community з OCA", "Що виходить", "Пастки, в які ми потрапили", "Enterprise: Datev DATA і ATCH", "Інші модулі DATEV", "Висновок"],
    "Для малої компанії важливі два формати DATEV: **Buchungsstapel** (проведення в CSV – консультант завантажує їх у DATEV Rechnungswesen) і **передача документів** (PDF і XML рахунків у DATEV Unternehmen online). Що потрібно вашому консультанту – перше питання.",
    [["", "Odoo Community + OCA", "Odoo Enterprise"],
     ["Проведення (Buchungsstapel)", "`datev_export_dtvf`: ZIP з EXTF_Buchungsstapel, DebKred_Stamm, Kontenbeschriftungen", "Бухгалтерія ‣ Звіти ‣ Головна книга ‣ Datev DATA (zip)"],
     ["Документи", "`datev_export_xml`: XML + PDF для DATEV Unternehmen online", "Головна книга ‣ Datev ATCH (zip) для DATEV Belegtransfer"],
     ["Імпорт з DATEV (зарплата, закриття року)", "`datev_import_csv_dtvf`", "–"],
     ["Декларація ПДВ (UStVA)", "`l10n_de_tax_statement` (OCA; потрібне налаштування податкових тегів – тут не перевіряли)", "Німецький податковий звіт"],
     ["Ліцензія", "безкоштовно (AGPL), модулі підтримуєте самі", "підписка Enterprise"]],
    ["**План рахунків SKR03 чи SKR04** – запитайте консультанта. Змінити його можна лише **до першого проведеного запису**; потім потрібна нова компанія або база.",
     "**Beraternummer і Mandantennummer** – від консультанта (номер консультанта 4–8 цифр, номер клієнта до 5).",
     "**Довжина рахунків** – зазвичай 4 цифри для рахунків головної книги, тоді клієнти й постачальники отримують 5-значні особові рахунки (10000–69999 дебітори, 70000–99999 кредитори). Теж уточнити.",
     "**Який формат і як часто** – зазвичай Buchungsstapel щомісяця; деякі консультанти хочуть документи через DATEV Unternehmen online.",
     "**Тестовий місяць** – домовтеся, що перше вивантаження тестове: консультант завантажує його в тестового клієнта й каже, що не підходить."],
    ["**Встановити німецьку локалізацію**: Додатки ‣ «Germany - Accounting» (`l10n_de`). У Налаштування ‣ Рахунки ‣ Фіскальна локалізація обрати **SKR03** або **SKR04** – до будь-яких проведень.",
     "**Дані компанії**: Налаштування ‣ Компанії: адреса, податковий номер, USt-IdNr. Вони потрапляють у рахунки й у заголовок вивантаження.",
     "**Взяти модулі OCA** – `datev_export_dtvf` (з OCA/l10n-germany) і `date_range` (з OCA/server-ux) – і встановити:",
     "**Налаштування DATEV**: Налаштування ‣ Рахунки ‣ блок **DATEV Export**: Consultant Number, Client Number, **DATEV account code length** (4), **DATEV Partner numbering** = Sequence, з послідовністю для клієнтів (з 10000) і для постачальників (з 70000). Послідовності створити в Налаштування ‣ Технічні ‣ Послідовності (режим розробника).",
     "**Автоматичні рахунки**: у SKR03 рахунки на кшталт 8400 (виручка 19 %) і 3400 (закупівля 19 %) у DATEV – Automatikkonten: DATEV сам виділяє ПДВ із суми. А Odoo вже вивантажує ПДВ окремим рядком. Відкрийте ці рахунки (Рахунки ‣ Налаштування ‣ План рахунків) і ввімкніть **Suppress automatic calculations in DATEV** – рядки отримають BU-Schlüssel 40. Узгодьте з консультантом.",
     "**Періоди**: Налаштування ‣ Технічні ‣ Date ranges: один період на фінансовий рік (наприклад, 2026) і по одному на місяць (2026-11 …).",
     "**Вивантаження**: Рахунки ‣ Звіти ‣ **DATEV export** ‣ Створити: назва, фінансовий рік, періоди (місяці), за потреби журнали ‣ **Generate** ‣ завантажити ZIP.",
     "**Перевірити й надіслати**: зазирнути у файл (нижче), надіслати консультанту, дочекатися відповіді щодо тестового місяця, далі – щомісяця. Вивантажуються лише проведені записи, чернетки – ні."],
    "Для тестового місяця модуль створив ZIP із трьох файлів. У проведеннях кожен рахунок розбито на рядки з особового рахунку на рахунок головної книги – виручка й ПДВ окремо:",
    ["**Без нумерації контрагентів** у полі Konto був збірний рахунок 1410 / 1610, а в довіднику партнери отримали номери 7 і 8 (ID у базі). Консультанту це не підходить – ставте «Sequence».",
     "**Автоматичні рахунки**: без прапорця рядки на 8400 / 3400 йшли з порожнім BU-Schlüssel, а ПДВ приходив окремим рядком – DATEV порахував би ПДВ удруге. З прапорцем: BU 40.",
     "**Кодування**: CSV в UTF-8 з BOM. Поточні версії DATEV це читають; якщо умлаути приходять зламаними – дивитися сюди.",
     "**Партнери двічі** в EXTF_DebKred_Stamm у нашому тесті (по разу на рядок рахунку). DATEV перезапише тими самими даними, але під час звірки це варто знати.",
     "**Текстові поля обрізаються** до довжини DATEV («Wallbox Mont») – описи позицій краще робити короткими.",
     "**Лише проведені записи** вибраних періодів – рахунок, проведений пізніше заднім числом, потребує нового вивантаження того місяця (домовтеся, як ідуть виправлення)."],
    "В Odoo Enterprise вивантаження DATEV вбудоване в німецькі бухгалтерські звіти. За документацією Odoo 18:",
    ["**Datev DATA (zip)**: Бухгалтерія ‣ Звіти ‣ Головна книга ‣ дії ‣ Datev DATA (zip) – клієнти, постачальники й проведення в EXTF CSV для DATEV Rechnungswesen.",
     "**Datev ATCH (zip)**: там само – файли рахунків і document.xml для DATEV Belegtransfer; проведення посилаються на документи за GUID.",
     "Файли рахунків клієнтам мають бути створені кнопкою **Надіслати**, рахунки постачальників – отримані через e-mail-аліас або завантажені.",
     "Odoo заявляє **сертифікацію GoBD**; on-premise за бекапи відповідаєте ви."],
    ["**`datev_export_xml`** – рахунки як XML + PDF для DATEV Unternehmen online (завантаження безкоштовним застосунком DATEV). Не для чистих проведень за рахунками, наприклад платежів.",
     "**`datev_import_csv_dtvf`** – зворотний напрямок: імпорт CSV з DATEV від консультанта (зарплата, амортизація, закриття року) як проведень.",
     "**`l10n_de_tax_statement`** – декларація ПДВ (UStVA) для ELSTER; потрібне налаштування податкових тегів по рядках.",
     "**Електронні рахунки**: XRechnung і ZUGFeRD – у стандартному модулі Odoo `account_edi_ubl_cii`, це окрема тема."],
    "DATEV і Odoo працюють і в Community – з модулем OCA, п'ятьма налаштуваннями й тестовим місяцем у консультанта. Робота не в кнопці вивантаження, а в домовленостях: план рахунків, довжина рахунків, номери контрагентів, автоматичні рахунки. Ми налаштовуємо це для компаній у Німеччині, Австрії та Швейцарії й можемо показати весь шлях на тестовій базі, перш ніж у справу підуть ваші дані.",
    "Посилання")
