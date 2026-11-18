# Статья 34: Odoo и SAP – практическая стоимость за 3 года для парикмахерской, пекарни, склада и автосервиса.
# SAP для малого бизнеса = SAP Business One (цены партнёров, SAP не публикует: business-one-beratung.de "Stand Oktober 2026",
# yagemi.de 30.09.2026: Kauf Professional 2700 / Limited 1400 / Starter 1140; Cloud 91 / 47 / 38 €/User/Monat, Hosting 50–65 €).
# Odoo – цены odoo.com/de_DE/pricing 18.11.2026 (как в статье costs). Расчёт – tco-скрипт ниже, вывод проверен.
# Языки: en, de, ru, uk; fr/el – английская версия.

ODOOSAP = {
    "slug": "odoo-vs-sap-business-one-real-cost-salon-bakery-warehouse-car-repair",
    "date": "2026-11-18",
    "tags": ["Odoo", "SAP", "ERP", "Kosten", "KMU"],
    "code": {
        "tco": ("python3 · the calculation – replace the assumptions with your offers", """DAY = 1000                                   # day rate of the partner – same for both (assumption)
ODOO = {"standard": (19.90, 24.90), "custom": (35.90, 44.90)}   # yearly billing: 1st year, then regular
SAP = {"professional": 91, "limited": 47, "starter": 38}       # SAP Business One Cloud, partner price lists
SAP_HOSTING = 55                             # per user per month, partners name 50-65 €

cases = {    # odoo: (plan, users, days, 0)   sap: ({user type: count}, days, add-ons €/month)
  "Hair salon (4 staff, 1 shop)":                   dict(odoo=("standard", 2, 2, 0),  sap=({"starter": 1}, 8, 1 * 40)),
  "Bakery (3 shops, own production)":               dict(odoo=("standard", 3, 6, 0),  sap=({"professional": 2, "limited": 1}, 15, 3 * 40)),
  "Warehouse / wholesale (10 users, scanners, shop)": dict(odoo=("custom", 10, 10, 0), sap=({"professional": 3, "limited": 7}, 20, 5 * 30)),
  "Car repair shop (6 staff, vehicle history)":     dict(odoo=("custom", 3, 8, 0),    sap=({"starter": 3}, 15, 0)),
}
for name, c in cases.items():
    plan, users, odays, oadd = c["odoo"]
    y1, reg = ODOO[plan]
    odoo_lic = users * 12 * (y1 + 2 * reg)
    odoo = odoo_lic + odays * DAY + 36 * oadd
    seats, sdays, sadd = c["sap"]
    sap_lic = 36 * (sum(n * (SAP[t] + SAP_HOSTING) for t, n in seats.items()) + sadd)
    sap = sap_lic + sdays * DAY
    print(name, round(odoo), round(sap), f"{sap / odoo:.1f}x")

# Hair salon (4 staff, 1 shop)                  3673  12788  3.5x
# Bakery (3 shops, own production)              8509  33504  3.9x
# Warehouse / wholesale (10 users, scanners, shop) 25084 66872 2.7x
# Car repair shop (6 staff, vehicle history)   12525  25044  2.0x"""),
    },
    "links": [
        ("Odoo pricing (Germany)", "https://www.odoo.com/de_DE/pricing"),
        ("SAP Business One prices – partner overview (DE)", "https://www.business-one-beratung.de/sap-business-one/preise-und-kosten.html"),
        ("SAP Business One costs 2026 – partner prices and implementation (DE)", "https://www.yagemi.de/blog/erp-warenwirtschaft/sap-business-one-kosten/"),
        ("SAP Business One – product page", "https://www.sap.com/products/erp/business-one.html"),
        ("Blog: what Odoo really costs", "@blog:odoo-costs-licence-hosting-implementation-germany"),
        ("Blog: Odoo and DATEV step by step", "@blog:odoo-datev-export-step-by-step-community-enterprise"),
    ],
    "t": {},
}


def _d(title, summary, intro, note, h, which_ul, price_table, assume_p, assume_ul, res_table,
       salon, bakery, wh, car, sap_ok_ul, hidden_ul, closing, links):
    body = [("p", intro), ("note", note),
            ("h", h[0]), ("ul", which_ul),
            ("h", h[1]), ("table", price_table),
            ("h", h[2]), ("p", assume_p), ("ul", assume_ul), ("code", "tco"),
            ("h", h[3]), ("table", res_table)]
    for i, (p, ul) in enumerate([salon, bakery, wh, car]):
        body += [("h", h[4 + i]), ("p", p), ("ul", ul)]
    body += [("h", h[8]), ("ul", sap_ok_ul), ("h", h[9]), ("ul", hidden_ul), ("h", h[10]), ("p", closing), ("links", links)]
    return {"title": title, "summary": summary, "body": body}


ODOOSAP["t"]["en"] = _d(
    "Odoo or SAP: what it really costs a hair salon, a bakery, a warehouse and a car repair shop",
    "SAP sounds safe, Odoo sounds cheap – but how big is the difference in euros? Four real small businesses, 3 years, licences, hosting and implementation: Odoo Enterprise against SAP Business One, the SAP product for small companies. With prices from 11/2026, the calculation to copy and an honest answer to when SAP is the better choice.",
    "\"Odoo oder SAP?\" is one of the questions small companies in Germany type into Google. The short answer is that for a business with 2 to 10 people working in the system, SAP costs **two to four times as much** over three years – and the difference comes less from the licence than from hosting and implementation. The long answer depends on the business, so we calculate four of them: a hair salon, a bakery with shops, a wholesale warehouse and a car repair shop.",
    "Where the numbers come from: Odoo prices from odoo.com (Germany, 18.11.2026). SAP does not publish prices for Business One; we use the price lists of German SAP partners (as of autumn 2026). Implementation days and add-on prices are our assumptions – they are marked, and the script below lets you replace them with real offers. All prices are net.",
    ["Which SAP?", "Licence prices side by side", "Assumptions", "Result: 3 years in euros", "Hair salon", "Bakery with three shops", "Warehouse / wholesale", "Car repair shop", "When SAP is the better choice", "Costs that are easy to miss", "Conclusion"],
    ["**SAP Business One** – the SAP product for small and medium companies, sold and implemented by partners. This is the one we compare.",
     "**SAP S/4HANA Cloud** (\"GROW with SAP\") – for medium and large companies; contracts and projects of a different size. Not a realistic option for a salon or a bakery.",
     "**SAP Business ByDesign** – according to several ERP portals no longer actively offered to new customers; ask SAP before planning with it."],
    [["", "Odoo Enterprise (Odoo Online)", "SAP Business One Cloud"],
     ["Full user per month", "Standard 19.90 € (1st year), then 24.90 €; Custom 35.90 € / 44.90 €", "Professional 91 €"],
     ["Limited user", "Light user 7.90 €", "Limited 47 €"],
     ["Small-company package", "—", "Starter 38 € (max. 5 users, reduced functions)"],
     ["Hosting", "included (Odoo Online)", "extra at the partner, about 50–65 € per user per month"],
     ["Purchase instead of rent", "no (Community: free licence, own server)", "Professional 2,700 €, Limited 1,400 €, Starter 1,140 € per user, plus 17–22 % maintenance per year"],
     ["Apps", "all apps in one price (POS, appointments, manufacturing, inventory, accounting …)", "core ERP; POS, appointments, scanner warehouse, workshop: add-ons from partners"]],
    "We compare rent with rent: Odoo Online against SAP Business One Cloud at a partner, three years, yearly billing. Hardware (tills, scanners, printers) and the TSE for German tills cost about the same in both cases and are left out.",
    ["**Same day rate** for both partners: 1,000 €. In practice SAP partners are often more expensive; with your offers the gap only grows.",
     "**Implementation days** – Odoo: salon 2, bakery 6, warehouse 10, car repair shop 8. SAP: 8, 15, 20, 15. The SAP numbers follow the partners' own examples (\"simple solution, 4 users, about 1 week, about 15,000 € incl. licence\").",
     "**Add-ons for SAP** (assumption): POS add-on 40 € per till per month, scanner app 30 € per device per month.",
     "**Users who only sell at the till** need no Odoo licence (POS login with employees); with SAP the till runs through the add-on."],
    [["Business", "Odoo, 3 years", "SAP Business One, 3 years", "Factor"],
     ["Hair salon (4 staff)", "3,673 €", "12,788 €", "3.5×"],
     ["Bakery (3 shops, production)", "8,509 €", "33,504 €", "3.9×"],
     ["Warehouse / wholesale (10 users)", "25,084 €", "66,872 €", "2.7×"],
     ["Car repair shop (6 staff)", "12,525 €", "25,044 €", "2.0×"]],
    ("Four hairdressers, one reception, the owner. Needed: online booking, customer card with history, till with TSE, a little stock (products for sale), invoices for the accountant.",
     ["**Odoo**: Appointments (customers book online, staff and chairs as resources), Point of Sale, Contacts, Inventory, Invoicing – all in Standard. 2 users (owner, reception); hairdressers use the till as employees without a licence.",
      "**SAP Business One** has neither online booking nor a till; both come from add-ons. One Starter user is enough for the office, but the project effort stays.",
      "**Honestly**: for a single salon, specialised salon software is often simpler than both. Odoo pays off when there are several salons, a shop or courses on top. SAP is oversized here."]),
    ("Three shops, a bakery with recipes, wholesale customers (cafés, canteens) with delivery notes and monthly invoices.",
     ["**Odoo**: Manufacturing with bills of materials (recipes) and daily production orders, Point of Sale in the shops, Sales with delivery notes, Inventory with lots and best-before dates, Invoicing. 3 users (owner, office, production); shop staff on the till without a licence.",
      "**SAP Business One**: production and bills of materials are part of Professional; the shops need a POS add-on. 2 Professional and 1 Limited user plus 3 tills.",
      "Where the money goes: with SAP 18,504 € of the 33,504 € are subscription and hosting – that runs every month, also after the project."]),
    ("Wholesale with 10 users: purchasing, sales, accounting, five warehouse workers with scanners, a web shop connected via interface.",
     ["**Odoo**: Inventory with the Barcode app, Purchase, Sales, Invoicing, DATEV, shipping connectors. Custom plan because of the external API for the shop; 10 users.",
      "**SAP Business One**: this is its home ground – strong in purchasing, inventory and finance. Scanner warehouse via add-on; 3 Professional, 7 Limited.",
      "The gap is smallest in relative terms here, but still about 40,000 € in three years. If the company is part of a group that already uses SAP, that changes the picture – see below."]),
    ("Six people, three of them working in the system: service advisor, office, owner. Needed: vehicles per customer with history, orders with labour and parts, appointments, invoices.",
     ["**Odoo**: Repairs, Inventory, Appointments, Invoicing; the vehicle per customer with mileage and history is added with Studio (Custom plan) or a small module.",
      "**SAP Business One**: has no workshop functions out of the box; the partner builds them – that is where the 15 days go. 3 Starter users.",
      "**Honestly**: for a typical workshop, German workshop software with DAT/TecDoc catalogue, HU dates and parts ordering is often the shortest way. Odoo makes sense when sales of vehicles or parts, several locations or own processes come on top."]),
    ["The company belongs to a **group that uses SAP** – consolidation, intercompany and the IT department speak SAP.",
     "**Complex manufacturing** with many variants, serial numbers along the whole chain, and a partner with an industry solution that fits exactly.",
     "A **bank, investor or auditor** asks for SAP – that happens, and then it is a business decision, not a technical one.",
     "Growth to **50+ users** with the prospect of S/4HANA – then Business One is the entry into the SAP world."],
    ["**SAP: indirect access** – programs that work with SAP data automatically (web shop, n8n, scripts) need their own licences; ask for it in the offer.",
     "**SAP: maintenance** on purchased licences – 17–22 % per year, every year.",
     "**Odoo: the second year** – the discounted first-year price ends; the calculation above already includes it.",
     "**Odoo: Custom plan** as soon as Studio, several companies or the external API are needed – almost double the Standard price.",
     "**Both: the till in Germany** needs a TSE (KassenSichV) – clarify before the project which certified solution is used.",
     "**Both: the people** – training and the first months after go-live cost more time than any licence."],
    "For a hair salon, a bakery or a car repair shop SAP is not the safe choice but the expensive one: two to four times the cost of Odoo, and the functions these businesses need (booking, till, workshop) come in SAP only through add-ons. In a wholesale warehouse SAP Business One is at home – and still more expensive; it pays off when the group or the bank asks for SAP. Take the script above, put your real offers in, and compare three years, not the first invoice. We implement Odoo for small companies in Germany, Austria and Switzerland and calculate your case on request.",
    "Links")

ODOOSAP["t"]["de"] = _d(
    "Odoo oder SAP: was es Friseursalon, Bäckerei, Lager und Kfz-Werkstatt wirklich kostet",
    "SAP klingt sicher, Odoo klingt günstig – aber wie groß ist der Unterschied in Euro? Vier echte Kleinbetriebe, 3 Jahre, Lizenzen, Hosting und Einführung: Odoo Enterprise gegen SAP Business One, das SAP-Produkt für kleine Unternehmen. Mit Preisen von 11/2026, der Rechnung zum Nachrechnen und einer ehrlichen Antwort, wann SAP die bessere Wahl ist.",
    "„Odoo oder SAP?“ gehört zu den Fragen, die kleine Unternehmen in Deutschland bei Google eingeben. Die kurze Antwort: Für einen Betrieb mit 2 bis 10 Personen im System kostet SAP über drei Jahre **das Zwei- bis Vierfache** – und der Unterschied kommt weniger aus der Lizenz als aus Hosting und Einführung. Die lange Antwort hängt vom Betrieb ab, deshalb rechnen wir vier durch: einen Friseursalon, eine Bäckerei mit Filialen, ein Großhandelslager und eine Kfz-Werkstatt.",
    "Woher die Zahlen kommen: Odoo-Preise von odoo.com (Deutschland, 18.11.2026). SAP veröffentlicht für Business One keine Preise; wir nutzen die Preislisten deutscher SAP-Partner (Stand Herbst 2026). Einführungstage und Add-on-Preise sind unsere Annahmen – sie sind gekennzeichnet, und mit dem Skript unten ersetzen Sie sie durch echte Angebote. Alle Preise netto.",
    ["Welches SAP?", "Lizenzpreise nebeneinander", "Annahmen", "Ergebnis: 3 Jahre in Euro", "Friseursalon", "Bäckerei mit drei Filialen", "Lager / Großhandel", "Kfz-Werkstatt", "Wann SAP die bessere Wahl ist", "Kosten, die man leicht übersieht", "Fazit"],
    ["**SAP Business One** – das SAP-Produkt für kleine und mittlere Unternehmen, verkauft und eingeführt von Partnern. Das vergleichen wir.",
     "**SAP S/4HANA Cloud** („GROW with SAP“) – für Mittelstand und Konzerne; Verträge und Projekte einer anderen Größe. Für Friseur oder Bäckerei keine realistische Option.",
     "**SAP Business ByDesign** – laut mehreren ERP-Portalen für Neukunden nicht mehr aktiv angeboten; vor der Planung bei SAP nachfragen."],
    [["", "Odoo Enterprise (Odoo Online)", "SAP Business One Cloud"],
     ["Vollanwender pro Monat", "Standard 19,90 € (1. Jahr), danach 24,90 €; Custom 35,90 € / 44,90 €", "Professional 91 €"],
     ["Eingeschränkter Anwender", "Light-Benutzer 7,90 €", "Limited 47 €"],
     ["Paket für Kleinbetriebe", "—", "Starter 38 € (max. 5 Anwender, eingeschränkte Funktionen)"],
     ["Hosting", "inklusive (Odoo Online)", "extra beim Partner, etwa 50–65 € pro Anwender und Monat"],
     ["Kauf statt Miete", "nein (Community: freie Lizenz, eigener Server)", "Professional 2.700 €, Limited 1.400 €, Starter 1.140 € pro Anwender, plus 17–22 % Wartung pro Jahr"],
     ["Apps", "alle Apps zu einem Preis (Kasse, Termine, Fertigung, Lager, Buchhaltung …)", "ERP-Kern; Kasse, Termine, Scanner-Lager, Werkstatt: Add-ons von Partnern"]],
    "Wir vergleichen Miete mit Miete: Odoo Online gegen SAP Business One Cloud beim Partner, drei Jahre, jährliche Zahlung. Hardware (Kassen, Scanner, Drucker) und die TSE für deutsche Kassen kosten in beiden Fällen etwa gleich viel und bleiben außen vor.",
    ["**Gleicher Tagessatz** für beide Partner: 1.000 €. In der Praxis sind SAP-Partner oft teurer; mit Ihren Angeboten wird der Abstand nur größer.",
     "**Einführungstage** – Odoo: Salon 2, Bäckerei 6, Lager 10, Werkstatt 8. SAP: 8, 15, 20, 15. Die SAP-Zahlen folgen den Beispielen der Partner selbst („einfache Lösung, 4 Anwender, ca. 1 Woche, ca. 15.000 € inkl. Lizenz“).",
     "**Add-ons für SAP** (Annahme): Kassen-Add-on 40 € pro Kasse und Monat, Scanner-App 30 € pro Gerät und Monat.",
     "**Wer nur an der Kasse verkauft**, braucht keine Odoo-Lizenz (Kassen-Login mit Mitarbeitern); bei SAP läuft die Kasse über das Add-on."],
    [["Betrieb", "Odoo, 3 Jahre", "SAP Business One, 3 Jahre", "Faktor"],
     ["Friseursalon (4 Mitarbeiter)", "3.673 €", "12.788 €", "3,5×"],
     ["Bäckerei (3 Filialen, Produktion)", "8.509 €", "33.504 €", "3,9×"],
     ["Lager / Großhandel (10 Anwender)", "25.084 €", "66.872 €", "2,7×"],
     ["Kfz-Werkstatt (6 Mitarbeiter)", "12.525 €", "25.044 €", "2,0×"]],
    ("Vier Friseurinnen und Friseure, ein Empfang, die Inhaberin. Gebraucht: Online-Terminbuchung, Kundenkarte mit Verlauf, Kasse mit TSE, etwas Lager (Verkaufsprodukte), Rechnungen für den Steuerberater.",
     ["**Odoo**: Termine (Kunden buchen online, Mitarbeiter und Stühle als Ressourcen), Kasse, Kontakte, Lager, Rechnungen – alles in Standard. 2 Anwender (Inhaberin, Empfang); die Friseure nutzen die Kasse als Mitarbeiter ohne Lizenz.",
      "**SAP Business One** hat weder Online-Buchung noch Kasse; beides kommt über Add-ons. Ein Starter-Anwender reicht fürs Büro, der Projektaufwand bleibt.",
      "**Ehrlich**: Für einen einzelnen Salon ist spezialisierte Salon-Software oft einfacher als beides. Odoo lohnt sich, wenn mehrere Salons, ein Shop oder Kurse dazukommen. SAP ist hier überdimensioniert."]),
    ("Drei Filialen, eine Backstube mit Rezepturen, Großkunden (Cafés, Kantinen) mit Lieferscheinen und Monatsrechnungen.",
     ["**Odoo**: Fertigung mit Stücklisten (Rezepturen) und täglichen Fertigungsaufträgen, Kasse in den Filialen, Verkauf mit Lieferscheinen, Lager mit Chargen und Mindesthaltbarkeit, Rechnungen. 3 Anwender (Inhaber, Büro, Produktion); Verkäuferinnen an der Kasse ohne Lizenz.",
      "**SAP Business One**: Fertigung und Stücklisten gehören zu Professional; die Filialen brauchen ein Kassen-Add-on. 2 Professional und 1 Limited plus 3 Kassen.",
      "Wohin das Geld geht: Bei SAP sind 18.504 € der 33.504 € Abo und Hosting – das läuft jeden Monat weiter, auch nach dem Projekt."]),
    ("Großhandel mit 10 Anwendern: Einkauf, Verkauf, Buchhaltung, fünf Lagermitarbeiter mit Scannern, ein Webshop über Schnittstelle.",
     ["**Odoo**: Lager mit der Barcode-App, Einkauf, Verkauf, Rechnungen, DATEV, Versand-Konnektoren. Custom-Plan wegen der externen API für den Shop; 10 Anwender.",
      "**SAP Business One**: Hier ist es zu Hause – stark in Einkauf, Lager und Finanzen. Scanner-Lager per Add-on; 3 Professional, 7 Limited.",
      "Relativ ist der Abstand hier am kleinsten, aber immer noch rund 40.000 € in drei Jahren. Gehört die Firma zu einer Gruppe, die SAP schon nutzt, ändert sich das Bild – siehe unten."]),
    ("Sechs Personen, drei davon im System: Serviceberater, Büro, Inhaber. Gebraucht: Fahrzeuge je Kunde mit Historie, Aufträge mit Arbeit und Teilen, Termine, Rechnungen.",
     ["**Odoo**: Reparaturen, Lager, Termine, Rechnungen; das Fahrzeug je Kunde mit Kilometerstand und Historie kommt mit Studio (Custom-Plan) oder einem kleinen Modul dazu.",
      "**SAP Business One**: hat keine Werkstattfunktionen ab Werk; der Partner baut sie – dort stecken die 15 Tage. 3 Starter-Anwender.",
      "**Ehrlich**: Für eine typische Werkstatt ist deutsche Werkstattsoftware mit DAT/TecDoc-Katalog, HU-Terminen und Teilebestellung oft der kürzeste Weg. Odoo lohnt sich, wenn Fahrzeug- oder Teileverkauf, mehrere Standorte oder eigene Abläufe dazukommen."]),
    ["Die Firma gehört zu einer **Gruppe mit SAP** – Konsolidierung, Intercompany und die IT sprechen SAP.",
     "**Komplexe Fertigung** mit vielen Varianten, Seriennummern über die ganze Kette und ein Partner mit genau passender Branchenlösung.",
     "Eine **Bank, ein Investor oder Prüfer** verlangt SAP – das kommt vor, und dann ist es eine geschäftliche Entscheidung, keine technische.",
     "Wachstum auf **50+ Anwender** mit Aussicht auf S/4HANA – dann ist Business One der Einstieg in die SAP-Welt."],
    ["**SAP: indirekter Zugriff** – Programme, die automatisch mit SAP-Daten arbeiten (Webshop, n8n, Skripte), brauchen eigene Lizenzen; im Angebot danach fragen.",
     "**SAP: Wartung** auf gekaufte Lizenzen – 17–22 % pro Jahr, jedes Jahr.",
     "**Odoo: das zweite Jahr** – der rabattierte Preis des ersten Jahres endet; die Rechnung oben enthält das bereits.",
     "**Odoo: Custom-Plan**, sobald Studio, mehrere Unternehmen oder die externe API gebraucht werden – fast der doppelte Standard-Preis.",
     "**Beide: die Kasse in Deutschland** braucht eine TSE (KassenSichV) – vor dem Projekt klären, welche zertifizierte Lösung genutzt wird.",
     "**Beide: die Menschen** – Schulung und die ersten Monate nach dem Start kosten mehr Zeit als jede Lizenz."],
    "Für Friseursalon, Bäckerei oder Kfz-Werkstatt ist SAP nicht die sichere, sondern die teure Wahl: das Zwei- bis Vierfache von Odoo, und die Funktionen, die diese Betriebe brauchen (Buchung, Kasse, Werkstatt), kommen bei SAP nur über Add-ons. Im Großhandelslager ist SAP Business One zu Hause – und trotzdem teurer; es lohnt sich, wenn Gruppe oder Bank SAP verlangen. Nehmen Sie das Skript oben, tragen Sie Ihre echten Angebote ein und vergleichen Sie drei Jahre, nicht die erste Rechnung. Wir führen Odoo für kleine Unternehmen in Deutschland, Österreich und der Schweiz ein und rechnen Ihren Fall auf Wunsch durch.",
    "Links")

ODOOSAP["t"]["ru"] = _d(
    "Odoo или SAP: сколько это реально стоит парикмахерской, пекарне, складу и автосервису",
    "SAP звучит надёжно, Odoo – дёшево, но какова разница в евро? Четыре реальных малых бизнеса, 3 года, лицензии, хостинг и внедрение: Odoo Enterprise против SAP Business One – продукта SAP для малых компаний. С ценами на 11/2026, расчётом, который можно повторить, и честным ответом, когда SAP – лучший выбор.",
    "«Odoo oder SAP?» – один из вопросов, которые малые компании в Германии вводят в Google. Короткий ответ: для бизнеса, где в системе работают от 2 до 10 человек, SAP за три года обходится **в два–четыре раза дороже** – и разница возникает не столько из-за лицензии, сколько из-за хостинга и внедрения. Длинный ответ зависит от бизнеса, поэтому считаем четыре: парикмахерскую, пекарню с магазинами, оптовый склад и автосервис.",
    "Откуда цифры: цены Odoo – с odoo.com (Германия, 18.11.2026). SAP не публикует цены на Business One; мы берём прайс-листы немецких партнёров SAP (осень 2026). Дни внедрения и цены дополнений – наши допущения: они помечены, и в скрипте ниже их можно заменить настоящими предложениями. Все цены без НДС.",
    ["Какой SAP?", "Цены лицензий рядом", "Допущения", "Итог: 3 года в евро", "Парикмахерская", "Пекарня с тремя магазинами", "Склад / оптовая торговля", "Автосервис", "Когда SAP – лучший выбор", "Затраты, которые легко пропустить", "Вывод"],
    ["**SAP Business One** – продукт SAP для малых и средних компаний, продают и внедряют партнёры. Его и сравниваем.",
     "**SAP S/4HANA Cloud** («GROW with SAP») – для средних и крупных компаний; договоры и проекты другого масштаба. Для парикмахерской или пекарни нереально.",
     "**SAP Business ByDesign** – по данным нескольких ERP-порталов, новым клиентам активно больше не предлагается; перед планированием уточнить у SAP."],
    [["", "Odoo Enterprise (Odoo Online)", "SAP Business One Cloud"],
     ["Полный пользователь в месяц", "Standard 19,90 € (1-й год), затем 24,90 €; Custom 35,90 € / 44,90 €", "Professional 91 €"],
     ["Ограниченный пользователь", "Light 7,90 €", "Limited 47 €"],
     ["Пакет для малого бизнеса", "—", "Starter 38 € (до 5 пользователей, урезанные функции)"],
     ["Хостинг", "включён (Odoo Online)", "отдельно у партнёра, примерно 50–65 € на пользователя в месяц"],
     ["Покупка вместо аренды", "нет (Community: бесплатная лицензия, свой сервер)", "Professional 2700 €, Limited 1400 €, Starter 1140 € за пользователя, плюс 17–22 % поддержки в год"],
     ["Приложения", "все приложения за одну цену (касса, запись, производство, склад, бухгалтерия …)", "ядро ERP; касса, запись, склад со сканерами, автосервис – дополнения партнёров"]],
    "Сравниваем аренду с арендой: Odoo Online против SAP Business One Cloud у партнёра, три года, оплата за год. Оборудование (кассы, сканеры, принтеры) и TSE для немецких касс стоят в обоих случаях примерно одинаково и в расчёт не входят.",
    ["**Одинаковая ставка дня** для обоих партнёров: 1000 €. На практике партнёры SAP часто дороже; с вашими предложениями разрыв только вырастет.",
     "**Дни внедрения** – Odoo: парикмахерская 2, пекарня 6, склад 10, автосервис 8. SAP: 8, 15, 20, 15. Цифры SAP следуют примерам самих партнёров («простое решение, 4 пользователя, около 1 недели, около 15 000 € с лицензией»).",
     "**Дополнения для SAP** (допущение): касса 40 € за кассу в месяц, приложение для сканеров 30 € за устройство в месяц.",
     "**Кто только продаёт на кассе**, не нужна лицензия Odoo (вход в кассу сотрудником); у SAP касса работает через дополнение."],
    [["Бизнес", "Odoo, 3 года", "SAP Business One, 3 года", "Разница"],
     ["Парикмахерская (4 сотрудника)", "3673 €", "12 788 €", "3,5×"],
     ["Пекарня (3 магазина, производство)", "8509 €", "33 504 €", "3,9×"],
     ["Склад / опт (10 пользователей)", "25 084 €", "66 872 €", "2,7×"],
     ["Автосервис (6 сотрудников)", "12 525 €", "25 044 €", "2,0×"]],
    ("Четыре мастера, администратор, владелица. Нужно: онлайн-запись, карточка клиента с историей, касса с TSE, немного склада (товары на продажу), счета для налогового консультанта.",
     ["**Odoo**: Запись (Appointments – клиенты записываются онлайн, мастера и кресла как ресурсы), Касса, Контакты, Склад, Счета – всё в Standard. 2 пользователя (владелица, администратор); мастера работают на кассе как сотрудники без лицензии.",
      "**SAP Business One**: нет ни онлайн-записи, ни кассы; и то и другое – дополнениями. Для офиса хватит одного пользователя Starter, но трудозатраты на проект остаются.",
      "**Честно**: для одного салона специализированная программа для салонов часто проще обоих вариантов. Odoo окупается, когда салонов несколько или добавляются магазин, курсы. SAP здесь избыточен."]),
    ("Три магазина, цех с рецептурами, оптовые клиенты (кафе, столовые) с накладными и ежемесячными счетами.",
     ["**Odoo**: Производство со спецификациями (рецептурами) и ежедневными заказами на производство, Касса в магазинах, Продажи с накладными, Склад с партиями и сроками годности, Счета. 3 пользователя (владелец, офис, производство); продавцы на кассе без лицензии.",
      "**SAP Business One**: производство и спецификации входят в Professional; магазинам нужно дополнение для кассы. 2 Professional и 1 Limited плюс 3 кассы.",
      "Куда уходят деньги: у SAP 18 504 € из 33 504 € – подписка и хостинг; это платится каждый месяц и после проекта."]),
    ("Оптовая торговля, 10 пользователей: закупки, продажи, бухгалтерия, пять кладовщиков со сканерами, интернет-магазин через интерфейс.",
     ["**Odoo**: Склад с приложением Barcode, Закупки, Продажи, Счета, DATEV, коннекторы доставки. План Custom из-за внешнего API для магазина; 10 пользователей.",
      "**SAP Business One**: здесь он дома – силён в закупках, складе и финансах. Склад со сканерами – дополнением; 3 Professional, 7 Limited.",
      "Относительно разрыв здесь самый маленький, но всё равно около 40 000 € за три года. Если компания входит в группу, которая уже работает на SAP, картина меняется – см. ниже."]),
    ("Шесть человек, трое в системе: мастер-приёмщик, офис, владелец. Нужно: автомобили клиента с историей, заказ-наряды с работами и запчастями, запись, счета.",
     ["**Odoo**: Ремонты (Repairs), Склад, Запись, Счета; автомобиль клиента с пробегом и историей добавляется через Studio (план Custom) или небольшой модуль.",
      "**SAP Business One**: функций автосервиса из коробки нет; их строит партнёр – туда и уходят 15 дней. 3 пользователя Starter.",
      "**Честно**: для типичного автосервиса немецкие программы для мастерских с каталогом DAT/TecDoc, сроками техосмотра (HU) и заказом запчастей часто самый короткий путь. Odoo имеет смысл, когда добавляется продажа автомобилей или запчастей, несколько точек или свои процессы."]),
    ["Компания входит в **группу, где работает SAP** – консолидация, внутригрупповые операции и ИТ-отдел говорят на SAP.",
     "**Сложное производство** со множеством вариантов, серийными номерами по всей цепочке и партнёр с точно подходящим отраслевым решением.",
     "**Банк, инвестор или аудитор** требует SAP – такое бывает, и тогда это бизнес-решение, а не техническое.",
     "Рост до **50+ пользователей** с перспективой S/4HANA – тогда Business One – вход в мир SAP."],
    ["**SAP: косвенный доступ** – программы, которые автоматически работают с данными SAP (интернет-магазин, n8n, скрипты), требуют своих лицензий; спрашивать в предложении.",
     "**SAP: поддержка** купленных лицензий – 17–22 % в год, каждый год.",
     "**Odoo: второй год** – скидка первого года заканчивается; расчёт выше это уже учитывает.",
     "**Odoo: план Custom**, как только нужны Studio, несколько компаний или внешний API, – почти вдвое дороже Standard.",
     "**Оба: касса в Германии** требует TSE (KassenSichV) – до проекта выяснить, какое сертифицированное решение используется.",
     "**Оба: люди** – обучение и первые месяцы после запуска стоят больше времени, чем любая лицензия."],
    "Для парикмахерской, пекарни или автосервиса SAP – не надёжный, а дорогой выбор: в два–четыре раза дороже Odoo, а нужные этим бизнесам функции (запись, касса, автосервис) у SAP есть только в дополнениях. На оптовом складе SAP Business One дома – и всё равно дороже; он окупается, когда SAP требует группа или банк. Возьмите скрипт выше, подставьте настоящие предложения и сравнивайте три года, а не первый счёт. Мы внедряем Odoo для малых компаний в Германии, Австрии и Швейцарии и по запросу посчитаем ваш случай.",
    "Ссылки")

ODOOSAP["t"]["uk"] = _d(
    "Odoo чи SAP: скільки це насправді коштує перукарні, пекарні, складу й автосервісу",
    "SAP звучить надійно, Odoo – дешево, але яка різниця в євро? Чотири реальні малі бізнеси, 3 роки, ліцензії, хостинг і впровадження: Odoo Enterprise проти SAP Business One – продукту SAP для малих компаній. З цінами на 11/2026, розрахунком, який можна повторити, і чесною відповіддю, коли SAP – кращий вибір.",
    "«Odoo oder SAP?» – одне з питань, які малі компанії в Німеччині вводять у Google. Коротка відповідь: для бізнесу, де в системі працюють від 2 до 10 людей, SAP за три роки коштує **у два–чотири рази дорожче** – і різниця виникає не стільки через ліцензію, скільки через хостинг і впровадження. Довга відповідь залежить від бізнесу, тому рахуємо чотири: перукарню, пекарню з магазинами, оптовий склад і автосервіс.",
    "Звідки цифри: ціни Odoo – з odoo.com (Німеччина, 18.11.2026). SAP не публікує ціни на Business One; ми беремо прайс-листи німецьких партнерів SAP (осінь 2026). Дні впровадження й ціни доповнень – наші припущення: вони позначені, і в скрипті нижче їх можна замінити справжніми пропозиціями. Усі ціни без ПДВ.",
    ["Який SAP?", "Ціни ліцензій поруч", "Припущення", "Підсумок: 3 роки в євро", "Перукарня", "Пекарня з трьома магазинами", "Склад / оптова торгівля", "Автосервіс", "Коли SAP – кращий вибір", "Витрати, які легко пропустити", "Висновок"],
    ["**SAP Business One** – продукт SAP для малих і середніх компаній, продають і впроваджують партнери. Його й порівнюємо.",
     "**SAP S/4HANA Cloud** («GROW with SAP») – для середніх і великих компаній; договори й проєкти іншого масштабу. Для перукарні чи пекарні нереально.",
     "**SAP Business ByDesign** – за даними кількох ERP-порталів, новим клієнтам активно більше не пропонується; перед плануванням уточнити в SAP."],
    [["", "Odoo Enterprise (Odoo Online)", "SAP Business One Cloud"],
     ["Повний користувач на місяць", "Standard 19,90 € (1-й рік), далі 24,90 €; Custom 35,90 € / 44,90 €", "Professional 91 €"],
     ["Обмежений користувач", "Light 7,90 €", "Limited 47 €"],
     ["Пакет для малого бізнесу", "—", "Starter 38 € (до 5 користувачів, урізані функції)"],
     ["Хостинг", "включено (Odoo Online)", "окремо в партнера, приблизно 50–65 € на користувача на місяць"],
     ["Купівля замість оренди", "ні (Community: безкоштовна ліцензія, свій сервер)", "Professional 2700 €, Limited 1400 €, Starter 1140 € за користувача, плюс 17–22 % підтримки на рік"],
     ["Застосунки", "усі застосунки за одну ціну (каса, запис, виробництво, склад, бухгалтерія …)", "ядро ERP; каса, запис, склад зі сканерами, автосервіс – доповнення партнерів"]],
    "Порівнюємо оренду з орендою: Odoo Online проти SAP Business One Cloud у партнера, три роки, оплата за рік. Обладнання (каси, сканери, принтери) і TSE для німецьких кас коштують в обох випадках приблизно однаково й у розрахунок не входять.",
    ["**Однакова ставка дня** для обох партнерів: 1000 €. На практиці партнери SAP часто дорожчі; з вашими пропозиціями розрив лише зросте.",
     "**Дні впровадження** – Odoo: перукарня 2, пекарня 6, склад 10, автосервіс 8. SAP: 8, 15, 20, 15. Цифри SAP відповідають прикладам самих партнерів («просте рішення, 4 користувачі, близько 1 тижня, близько 15 000 € з ліцензією»).",
     "**Доповнення для SAP** (припущення): каса 40 € за касу на місяць, застосунок для сканерів 30 € за пристрій на місяць.",
     "**Хто лише продає на касі**, тому не потрібна ліцензія Odoo (вхід у касу працівником); у SAP каса працює через доповнення."],
    [["Бізнес", "Odoo, 3 роки", "SAP Business One, 3 роки", "Різниця"],
     ["Перукарня (4 працівники)", "3673 €", "12 788 €", "3,5×"],
     ["Пекарня (3 магазини, виробництво)", "8509 €", "33 504 €", "3,9×"],
     ["Склад / опт (10 користувачів)", "25 084 €", "66 872 €", "2,7×"],
     ["Автосервіс (6 працівників)", "12 525 €", "25 044 €", "2,0×"]],
    ("Чотири майстри, адміністратор, власниця. Потрібно: онлайн-запис, картка клієнта з історією, каса з TSE, трохи складу (товари на продаж), рахунки для податкового консультанта.",
     ["**Odoo**: Запис (Appointments – клієнти записуються онлайн, майстри й крісла як ресурси), Каса, Контакти, Склад, Рахунки – усе в Standard. 2 користувачі (власниця, адміністратор); майстри працюють на касі як працівники без ліцензії.",
      "**SAP Business One**: немає ні онлайн-запису, ні каси; і те, й інше – доповненнями. Для офісу вистачить одного користувача Starter, але витрати на проєкт залишаються.",
      "**Чесно**: для одного салону спеціалізована програма для салонів часто простіша за обидва варіанти. Odoo окупається, коли салонів кілька або додаються магазин, курси. SAP тут надмірний."]),
    ("Три магазини, цех із рецептурами, оптові клієнти (кафе, їдальні) з накладними й щомісячними рахунками.",
     ["**Odoo**: Виробництво зі специфікаціями (рецептурами) і щоденними замовленнями на виробництво, Каса в магазинах, Продажі з накладними, Склад з партіями й термінами придатності, Рахунки. 3 користувачі (власник, офіс, виробництво); продавці на касі без ліцензії.",
      "**SAP Business One**: виробництво й специфікації входять у Professional; магазинам потрібне доповнення для каси. 2 Professional і 1 Limited плюс 3 каси.",
      "Куди йдуть гроші: у SAP 18 504 € із 33 504 € – підписка й хостинг; це платиться щомісяця й після проєкту."]),
    ("Оптова торгівля, 10 користувачів: закупівлі, продажі, бухгалтерія, п'ять комірників зі сканерами, інтернет-магазин через інтерфейс.",
     ["**Odoo**: Склад із застосунком Barcode, Закупівлі, Продажі, Рахунки, DATEV, конектори доставки. План Custom через зовнішній API для магазину; 10 користувачів.",
      "**SAP Business One**: тут він удома – сильний у закупівлях, складі й фінансах. Склад зі сканерами – доповненням; 3 Professional, 7 Limited.",
      "Відносно розрив тут найменший, але все одно близько 40 000 € за три роки. Якщо компанія входить у групу, яка вже працює на SAP, картина змінюється – див. нижче."]),
    ("Шість людей, троє в системі: майстер-приймальник, офіс, власник. Потрібно: автомобілі клієнта з історією, заказ-наряди з роботами й запчастинами, запис, рахунки.",
     ["**Odoo**: Ремонти (Repairs), Склад, Запис, Рахунки; автомобіль клієнта з пробігом та історією додається через Studio (план Custom) або невеликий модуль.",
      "**SAP Business One**: функцій автосервісу з коробки немає; їх будує партнер – туди й ідуть 15 днів. 3 користувачі Starter.",
      "**Чесно**: для типового автосервісу німецькі програми для майстерень з каталогом DAT/TecDoc, строками техогляду (HU) і замовленням запчастин часто найкоротший шлях. Odoo має сенс, коли додається продаж автомобілів чи запчастин, кілька точок або власні процеси."]),
    ["Компанія входить у **групу, де працює SAP** – консолідація, внутрішньогрупові операції й ІТ-відділ говорять мовою SAP.",
     "**Складне виробництво** з безліччю варіантів, серійними номерами по всьому ланцюгу й партнер з точно відповідним галузевим рішенням.",
     "**Банк, інвестор або аудитор** вимагає SAP – таке буває, і тоді це бізнес-рішення, а не технічне.",
     "Зростання до **50+ користувачів** з перспективою S/4HANA – тоді Business One – вхід у світ SAP."],
    ["**SAP: непрямий доступ** – програми, що автоматично працюють з даними SAP (інтернет-магазин, n8n, скрипти), потребують своїх ліцензій; питати в пропозиції.",
     "**SAP: підтримка** куплених ліцензій – 17–22 % на рік, щороку.",
     "**Odoo: другий рік** – знижка першого року закінчується; розрахунок вище це вже враховує.",
     "**Odoo: план Custom**, щойно потрібні Studio, кілька компаній або зовнішній API, – майже вдвічі дорожче за Standard.",
     "**Обидва: каса в Німеччині** потребує TSE (KassenSichV) – до проєкту з'ясувати, яке сертифіковане рішення використовується.",
     "**Обидва: люди** – навчання й перші місяці після запуску коштують більше часу, ніж будь-яка ліцензія."],
    "Для перукарні, пекарні чи автосервісу SAP – не надійний, а дорогий вибір: у два–чотири рази дорожче за Odoo, а потрібні цим бізнесам функції (запис, каса, автосервіс) у SAP є лише в доповненнях. На оптовому складі SAP Business One удома – і все одно дорожчий; він окупається, коли SAP вимагає група чи банк. Візьміть скрипт вище, підставте справжні пропозиції й порівнюйте три роки, а не перший рахунок. Ми впроваджуємо Odoo для малих компаній у Німеччині, Австрії та Швейцарії й на запит порахуємо ваш випадок.",
    "Посилання")


# --- Добавлено по вопросу: а self-hosted Odoo (Community) + работа внешних специалистов? ---
ODOOSAP["code"]["selfhost"] = ("python3 · Odoo Community on your own server, 3 years – same day rate, assumptions to replace", """DAY, VPS, ADMIN_H, RATE, SETUP = 1000, 25, 2, 90, 0.5  # day rate, server €/month, admin h/month, €/h, server setup days (prepared Docker setup)
cases = {   # Odoo implementation days (as above) + extra days for what Community lacks
  "Hair salon":       (2, 3),    # online booking and certified till (TSE) – third-party/OCA modules
  "Bakery":           (6, 3),    # TSE for the tills
  "Warehouse":        (10, 4),   # scanner app (OCA stock_barcodes), DATEV export (OCA) – the external API is free
  "Car repair shop":  (8, 1),    # vehicle fields as a small module instead of Studio
}
for name, (days, gap) in cases.items():
    run = 36 * (VPS + ADMIN_H * RATE)            # server + updates, backups, monitoring by a specialist
    setup = (SETUP + days + gap) * DAY
    print(f"{name:16} run {run}  setup+implementation {setup:.0f}  = {run + setup:.0f}")

# Hair salon       run 7380  setup+implementation 5500   = 12880
# Bakery           run 7380  setup+implementation 9500   = 16880
# Warehouse        run 7380  setup+implementation 14500  = 21880
# Car repair shop  run 7380  setup+implementation 9500   = 16880""")

_SH = {
    "en": ("Odoo on your own server (Community): cheaper?",
           "The Community edition costs no licence – but someone has to install the server, take care of backups, updates and monitoring, and fill the gaps where Community lacks Enterprise apps. In a small company that is usually an external specialist. With the same day rate, a server for 25 € a month and 2 hours of administration per month at 90 €:",
           [["Business", "Odoo Online (Enterprise)", "Odoo Community, own server", "SAP Business One"],
            ["Hair salon", "3,673 €", "12,880 €", "12,788 €"],
            ["Bakery", "8,509 €", "16,880 €", "33,504 €"],
            ["Warehouse / wholesale (10 users)", "25,084 €", "21,880 €", "66,872 €"],
            ["Car repair shop", "12,525 €", "16,880 €", "25,044 €"]],
           ["**Small teams pay more with their own server**: administration costs about 205 € a month regardless of the number of users. Odoo Online Standard costs 24.90 € per user – own hosting only pays off from about **8 users** (Standard) or **5 users** (Custom).",
            "**The warehouse is the exception**: 10 users on the Custom plan – here Community is already cheaper, and the external API is free.",
            "**If you administer yourself** (an IT person in the company), 6,480 € of the 7,380 € running costs disappear – then Community is the cheapest option everywhere. But the responsibility for backups stays with you.",
            "**What Community lacks** costs days: online booking, the certified till with TSE for Germany, the scanner app, Studio. There are OCA or third-party modules for most of it – check each one before deciding.",
            "**Version upgrades**: Odoo Online upgrades for you; on your own server a new major version means a migration project (OpenUpgrade) of several days. Not in the numbers above – plan it every 2–3 years.",
            "**Odoo Enterprise on your own server** is possible with the Custom plan – licence as above plus the costs of your own server; that rarely pays off for small companies."],
           "python3 · selfhost",
           "What external specialists do – and what you should get in writing",
           ["**Server setup** (½ day with a prepared Docker setup, otherwise 1–2 days): VPS in Germany, Docker or packages, nginx with HTTPS, PostgreSQL, mail, firewall.",
            "**Backups** to a second location with a tested restore – ask for the restore test, not only for the backup.",
            "**Monitoring and updates**: who notices if Odoo is down, who installs security updates, and how fast.",
            "**Implementation**: data import, settings, DATEV, documents, training – the days from the tables above.",
            "**Fixed scope and handover**: list of services, access data in your hands, documentation – so that you can change the service provider."]),
    "de": ("Odoo auf eigenem Server (Community): günstiger?",
           "Die Community-Edition kostet keine Lizenz – aber jemand muss den Server aufsetzen, sich um Backups, Updates und Monitoring kümmern und die Lücken füllen, wo Community die Enterprise-Apps fehlen. In einer kleinen Firma ist das meist ein externer Dienstleister. Mit gleichem Tagessatz, einem Server für 25 € im Monat und 2 Stunden Administration pro Monat zu 90 €:",
           [["Betrieb", "Odoo Online (Enterprise)", "Odoo Community, eigener Server", "SAP Business One"],
            ["Friseursalon", "3.673 €", "12.880 €", "12.788 €"],
            ["Bäckerei", "8.509 €", "16.880 €", "33.504 €"],
            ["Lager / Großhandel (10 Anwender)", "25.084 €", "21.880 €", "66.872 €"],
            ["Kfz-Werkstatt", "12.525 €", "16.880 €", "25.044 €"]],
           ["**Kleine Teams zahlen mit eigenem Server mehr**: Die Administration kostet etwa 205 € im Monat, egal wie viele Anwender. Odoo Online Standard kostet 24,90 € pro Anwender – eigenes Hosting lohnt sich erst ab etwa **8 Anwendern** (Standard) bzw. **5 Anwendern** (Custom).",
            "**Das Lager ist die Ausnahme**: 10 Anwender im Custom-Plan – hier ist Community schon günstiger, und die externe API ist frei.",
            "**Wer selbst administriert** (eine IT-Person im Haus), spart 6.480 € der 7.380 € Betriebskosten – dann ist Community überall die günstigste Option. Die Verantwortung für Backups bleibt aber bei Ihnen.",
            "**Was Community fehlt**, kostet Tage: Online-Buchung, die zertifizierte Kasse mit TSE für Deutschland, die Scanner-App, Studio. Für das meiste gibt es OCA- oder Drittanbieter-Module – jedes vor der Entscheidung prüfen.",
            "**Versions-Upgrades**: Odoo Online aktualisiert für Sie; auf eigenem Server ist eine neue Hauptversion ein Migrationsprojekt (OpenUpgrade) von mehreren Tagen. Nicht in den Zahlen oben – alle 2–3 Jahre einplanen.",
            "**Odoo Enterprise auf eigenem Server** geht mit dem Custom-Plan – Lizenz wie oben plus die Kosten des eigenen Servers; für kleine Firmen lohnt sich das selten."],
           "python3 · selfhost",
           "Was externe Dienstleister machen – und was Sie schriftlich haben sollten",
           ["**Server-Einrichtung** (½ Tag mit vorbereitetem Docker-Setup, sonst 1–2 Tage): VPS in Deutschland, Docker oder Pakete, nginx mit HTTPS, PostgreSQL, Mail, Firewall.",
            "**Backups** an einen zweiten Ort mit getesteter Wiederherstellung – nach dem Wiederherstellungstest fragen, nicht nur nach dem Backup.",
            "**Monitoring und Updates**: Wer merkt, wenn Odoo ausfällt, wer spielt Sicherheitsupdates ein, und wie schnell.",
            "**Einführung**: Datenimport, Einstellungen, DATEV, Belege, Schulung – die Tage aus den Tabellen oben.",
            "**Festumfang und Übergabe**: Leistungsliste, Zugangsdaten in Ihrer Hand, Dokumentation – damit Sie den Dienstleister wechseln können."]),
    "ru": ("Odoo на своём сервере (Community): дешевле?",
           "Редакция Community не стоит лицензии – но кто-то должен поставить сервер, следить за бэкапами, обновлениями и мониторингом и закрыть пробелы там, где Community не хватает приложений Enterprise. В маленькой компании это обычно внешний специалист. При той же ставке дня, сервере за 25 € в месяц и 2 часах администрирования в месяц по 90 €:",
           [["Бизнес", "Odoo Online (Enterprise)", "Odoo Community, свой сервер", "SAP Business One"],
            ["Парикмахерская", "3673 €", "12 880 €", "12 788 €"],
            ["Пекарня", "8509 €", "16 880 €", "33 504 €"],
            ["Склад / опт (10 пользователей)", "25 084 €", "21 880 €", "66 872 €"],
            ["Автосервис", "12 525 €", "16 880 €", "25 044 €"]],
           ["**Маленьким командам свой сервер обходится дороже**: администрирование стоит около 205 € в месяц независимо от числа пользователей. Odoo Online Standard – 24,90 € за пользователя; свой хостинг окупается примерно с **8 пользователей** (Standard) или **5 пользователей** (Custom).",
            "**Склад – исключение**: 10 пользователей на плане Custom – здесь Community уже дешевле, а внешний API бесплатный.",
            "**Если администрировать самим** (есть свой ИТ-специалист), из 7380 € текущих затрат уходят 6480 € – тогда Community везде самый дешёвый вариант. Но ответственность за бэкапы остаётся на вас.",
            "**Чего нет в Community**, стоит дней: онлайн-запись, сертифицированная касса с TSE для Германии, приложение для сканеров, Studio. Для большей части есть модули OCA или сторонние – проверять каждый до решения.",
            "**Переход на новую версию**: Odoo Online обновляет сам; на своём сервере новая основная версия – это проект миграции (OpenUpgrade) на несколько дней. В цифрах выше не учтено – закладывать раз в 2–3 года.",
            "**Odoo Enterprise на своём сервере** возможен с планом Custom – лицензия как выше плюс затраты на свой сервер; малым компаниям это редко выгодно."],
           "python3 · selfhost",
           "Что делают внешние специалисты – и что стоит получить письменно",
           ["**Настройка сервера** (½ дня с готовой Docker-сборкой, иначе 1–2 дня): VPS в Германии, Docker или пакеты, nginx с HTTPS, PostgreSQL, почта, файрвол.",
            "**Бэкапы** во второе место с проверенным восстановлением – спрашивать тест восстановления, а не только бэкап.",
            "**Мониторинг и обновления**: кто заметит, если Odoo упал, кто ставит обновления безопасности и как быстро.",
            "**Внедрение**: импорт данных, настройки, DATEV, документы, обучение – дни из таблиц выше.",
            "**Фиксированный объём и передача**: список работ, доступы у вас, документация – чтобы можно было сменить подрядчика."]),
    "uk": ("Odoo на власному сервері (Community): дешевше?",
           "Редакція Community не коштує ліцензії – але хтось має поставити сервер, стежити за бекапами, оновленнями й моніторингом і закрити прогалини там, де Community бракує застосунків Enterprise. У маленькій компанії це зазвичай зовнішній фахівець. За тієї ж ставки дня, сервера за 25 € на місяць і 2 годин адміністрування на місяць по 90 €:",
           [["Бізнес", "Odoo Online (Enterprise)", "Odoo Community, власний сервер", "SAP Business One"],
            ["Перукарня", "3673 €", "12 880 €", "12 788 €"],
            ["Пекарня", "8509 €", "16 880 €", "33 504 €"],
            ["Склад / опт (10 користувачів)", "25 084 €", "21 880 €", "66 872 €"],
            ["Автосервіс", "12 525 €", "16 880 €", "25 044 €"]],
           ["**Малим командам власний сервер обходиться дорожче**: адміністрування коштує близько 205 € на місяць незалежно від кількості користувачів. Odoo Online Standard – 24,90 € за користувача; власний хостинг окупається приблизно з **8 користувачів** (Standard) або **5 користувачів** (Custom).",
            "**Склад – виняток**: 10 користувачів на плані Custom – тут Community вже дешевший, а зовнішній API безкоштовний.",
            "**Якщо адмініструвати самим** (є свій ІТ-фахівець), із 7380 € поточних витрат зникають 6480 € – тоді Community скрізь найдешевший варіант. Але відповідальність за бекапи залишається на вас.",
            "**Чого немає в Community**, коштує днів: онлайн-запис, сертифікована каса з TSE для Німеччини, застосунок для сканерів, Studio. Для більшості є модулі OCA або сторонні – перевіряти кожен до рішення.",
            "**Перехід на нову версію**: Odoo Online оновлює сам; на власному сервері нова основна версія – це проєкт міграції (OpenUpgrade) на кілька днів. У цифрах вище не враховано – закладати раз на 2–3 роки.",
            "**Odoo Enterprise на власному сервері** можливий з планом Custom – ліцензія як вище плюс витрати на власний сервер; малим компаніям це рідко вигідно."],
           "python3 · selfhost",
           "Що роблять зовнішні фахівці – і що варто отримати письмово",
           ["**Налаштування сервера** (½ дня з готовою Docker-збіркою, інакше 1–2 дні): VPS у Німеччині, Docker або пакети, nginx з HTTPS, PostgreSQL, пошта, файрвол.",
            "**Бекапи** в друге місце з перевіреним відновленням – питати тест відновлення, а не лише бекап.",
            "**Моніторинг і оновлення**: хто помітить, якщо Odoo впав, хто ставить оновлення безпеки й як швидко.",
            "**Впровадження**: імпорт даних, налаштування, DATEV, документи, навчання – дні з таблиць вище.",
            "**Фіксований обсяг і передача**: перелік робіт, доступи у вас, документація – щоб можна було змінити підрядника."]),
}

for _lang, (_h, _p, _tab, _ul, _code, _h2, _ul2) in _SH.items():
    _b = ODOOSAP["t"][_lang]["body"]
    _i = [k for k, blk in enumerate(_b) if blk[0] == "table"][1] + 1     # after the result table
    _b[_i:_i] = [("h", _h), ("p", _p), ("table", _tab), ("code", "selfhost"), ("ul", _ul), ("h", _h2), ("ul", _ul2)]

for _lang, _s in {"en": " Plus: Odoo Community on your own server with an external specialist – when it pays off.",
                  "de": " Dazu: Odoo Community auf eigenem Server mit externem Dienstleister – wann es sich lohnt.",
                  "ru": " Плюс: Odoo Community на своём сервере с внешним специалистом – когда это окупается.",
                  "uk": " Плюс: Odoo Community на власному сервері із зовнішнім фахівцем – коли це окупається."}.items():
    ODOOSAP["t"][_lang]["summary"] += _s


# --- Приложение: свой сервер vs Odoo.sh (и Odoo Online для сравнения) по годам 1..5, 5 пользователей ---
ODOOSAP["code"]["years"] = ("python3 · 5 users, years 1–5: own server (Community / Enterprise), Odoo.sh, Odoo Online – replace the assumptions", """DAY, HOUR, USERS = 1000, 90, 5
CUSTOM, STANDARD = (35.90, 44.90), (19.90, 24.90)                       # €/user/month, yearly billing: 1st year, then regular
def lic(y, p=CUSTOM): return USERS * 12 * (p[0] if y == 1 else p[1])
V = {   # item: (Community own server, Enterprise own server, Odoo.sh, Odoo Online for reference)   – per year, y = 1..5
  "Server / project setup":          lambda y: (DAY//2, DAY//2, DAY//2, 0) if y == 1 else (0,)*4,
  "Implementation (configuration, data)": lambda y: (8*DAY, 6*DAY, 6*DAY, 6*DAY) if y == 1 else (0,)*4,
  "Training":                        lambda y: (2*DAY,)*4 if y == 1 else (DAY//2,)*4,
  "Licence (Custom / Standard, 5 users)":       lambda y: (0, lic(y), lic(y), lic(y, STANDARD)),
  "Hosting":                         lambda y: (12*30, 12*30, 12*74, 0),     # VPS 25 + off-site backup 5 | 1 worker, 10 GB, 1 staging
  "Administration (updates, backups, monitoring)": lambda y: (24*HOUR, 24*HOUR, 6*HOUR, 0),
  "Support cases (bot, mail, printing …)":         lambda y: (16*HOUR, 12*HOUR, 8*HOUR, 8*HOUR),
  "Upgrade to a new Odoo version":   lambda y: (5*DAY, 2*DAY, 1500, 500) if y == 3 else (0,)*4,
}
tot = [[0]*4 for _ in range(5)]
for item, f in V.items():
    for y in range(1, 6):
        for k, v in enumerate(f(y)): tot[y-1][k] += v
cum = [0]*4
for y, t in enumerate(tot, 1):
    cum = [c + v for c, v in zip(cum, t)]
    print(f"year {y}: " + "  ".join(f"{v:7.0f}" for v in t) + "   cumulative " + "  ".join(f"{c:7.0f}" for c in cum))

# year 1:   14460    14254    12802     9914
# year 2:    4460     6794     5342     2714
# year 3:    9460     8794     6842     3214   (version upgrade)
# year 4:    4460     6794     5342     2714
# year 5:    4460     6794     5342     2714   -> 5 years: 37300  43430  35670  21270""")

_Y = [["1", "14,460", "14,254", "12,802", "9,914"], ["2", "4,460", "6,794", "5,342", "2,714"],
      ["3 (new version)", "9,460", "8,794", "6,842", "3,214"], ["4", "4,460", "6,794", "5,342", "2,714"],
      ["5", "4,460", "6,794", "5,342", "2,714"], ["**5 years**", "**37,300**", "**43,430**", "**35,670**", "**21,270**"]]


_AP = {
    "en": dict(
        h="Appendix: own server or Odoo.sh – years 1 to 5, everything included",
        p="Odoo.sh is Odoo's own platform for Odoo Enterprise with custom modules: GitHub, staging copies, backups in three locations, monitoring – Odoo runs the servers, you or your partner run the code. It needs the Custom plan. Example: a company with 5 users that needs its own modules (otherwise Odoo Online is enough – we show it for reference). Odoo.sh prices from public price overviews with yearly billing: 57.60 per worker, 0.20 per GB and 14.40 per staging copy per month (USD values; check the euro price in the calculator on odoo.com/pricing). Day rate 1,000 €, hour 90 €.",
        items=[["Cost item", "Community, own server", "Enterprise, own server", "Odoo.sh", "Odoo Online (reference)"],
               ["Server / project setup (once)", "½ day – 500 € (prepared Docker setup)", "500 €", "½ day – 500 € (project, GitHub, domain)", "—"],
               ["Implementation: settings, data import, documents (once)", "8 days – 8,000 € (2 days for missing Enterprise apps)", "6 days – 6,000 €", "6,000 €", "6,000 €"],
               ["Training", "2 days – 2,000 €, then ½ day a year", "same", "same", "same"],
               ["Licence, 5 users", "0 €", "Custom: 2,154 € in year 1, then 2,694 €", "same", "Standard: 1,194 €, then 1,494 €"],
               ["Hosting per year", "360 € (VPS 25 € + off-site backup 5 € a month)", "360 €", "888 € (1 worker, 10 GB, 1 staging)", "included"],
               ["Administration per year: updates, backups, monitoring", "24 h – 2,160 €", "2,160 €", "6 h – 540 € (builds, module updates)", "—"],
               ["Support cases per year", "16 h – 1,440 €", "12 h – 1,080 €", "8 h – 720 €", "8 h – 720 €"],
               ["New Odoo version (year 3)", "5 days – 5,000 € (OpenUpgrade)", "2,000 € (Odoo upgrade service + tests)", "1,500 € (upgrade on staging, tests)", "500 € (tests)"]],
        years=("Year", "1", "5 years", ","),
        ycols=["Year", "Community, own server", "Enterprise, own server", "Odoo.sh", "Odoo Online"],
        sup_h="The small things: who fixes what",
        sup=["**\"The bot stopped working\"** (Telegram notifications, an integration): own server – the specialist checks process, log and token and restarts; Odoo.sh – if it is your own module, your partner; Odoo support only covers the standard. Either way: billed by the hour unless you have a flat rate.",
             "**\"Mail does not work\"**: own server – SPF/DKIM/DMARC in DNS, a relay or Gmail/Outlook (app password or OAuth), and many VPS providers block outgoing port 25; Odoo.sh / Online – Odoo's mail servers are included, you only set the DNS records for your domain.",
             "**\"Odoo is slow or down\"**: own server – disk full, too few workers, PostgreSQL; you notice it only with monitoring. Odoo.sh – Odoo monitors 24/7; slow own modules stay your partner's job.",
             "**\"Certificate expired\", \"backup missing\"**: own server – certbot renewal and restore tests are part of administration; Odoo.sh / Online – automatic.",
             "**\"Error after an update\"** in standard Odoo: Enterprise (all variants except Community) – Odoo support is included in the licence; Community – only your partner or the OCA community.",
             "**Training** is not a one-off: new employees, new functions, the new version – plan half a day a year. Short videos of your own processes save the most time.",
             "**Agree on support in writing**: reaction time (e.g. 4 hours on working days), monthly flat rate or hourly rate, who has which access, how emergencies are reported."],
        con=["Over 5 years with 5 users: **Odoo Online 21,270 €**, **Odoo.sh 35,670 €**, Community on your own server 37,300 €, Enterprise on your own server 43,430 €.",
             "**Odoo.sh beats your own server** although hosting costs more: administration, certificates, backups and upgrades are cheaper there. It is the right place when you need your own modules.",
             "**Community on your own server** pays off with in-house IT, more users (each additional Custom user costs about 539 € a year) or when the data must stay on your own server.",
             "**Enterprise on your own server** is the most expensive variant – only for special requirements (data location, integration into your own network)."]),
    "de": dict(
        h="Anhang: eigener Server oder Odoo.sh – Jahr 1 bis 5, alles inklusive",
        p="Odoo.sh ist Odoos eigene Plattform für Odoo Enterprise mit eigenen Modulen: GitHub, Staging-Kopien, Backups an drei Standorten, Monitoring – Odoo betreibt die Server, Sie oder Ihr Partner den Code. Voraussetzung ist der Custom-Plan. Beispiel: eine Firma mit 5 Anwendern, die eigene Module braucht (sonst reicht Odoo Online – zum Vergleich mit aufgeführt). Odoo.sh-Preise aus öffentlichen Preisübersichten bei jährlicher Zahlung: 57,60 pro Worker, 0,20 pro GB und 14,40 pro Staging-Kopie im Monat (USD-Werte; Euro-Preis im Rechner auf odoo.com/pricing prüfen). Tagessatz 1.000 €, Stunde 90 €.",
        items=[["Kostenposition", "Community, eigener Server", "Enterprise, eigener Server", "Odoo.sh", "Odoo Online (Vergleich)"],
               ["Server- / Projekteinrichtung (einmalig)", "½ Tag – 500 € (vorbereitetes Docker-Setup)", "500 €", "½ Tag – 500 € (Projekt, GitHub, Domain)", "—"],
               ["Einführung: Einstellungen, Datenimport, Belege (einmalig)", "8 Tage – 8.000 € (2 Tage für fehlende Enterprise-Apps)", "6 Tage – 6.000 €", "6.000 €", "6.000 €"],
               ["Schulung", "2 Tage – 2.000 €, danach ½ Tag pro Jahr", "gleich", "gleich", "gleich"],
               ["Lizenz, 5 Anwender", "0 €", "Custom: 2.154 € im 1. Jahr, danach 2.694 €", "gleich", "Standard: 1.194 €, danach 1.494 €"],
               ["Hosting pro Jahr", "360 € (VPS 25 € + externes Backup 5 € im Monat)", "360 €", "888 € (1 Worker, 10 GB, 1 Staging)", "inklusive"],
               ["Administration pro Jahr: Updates, Backups, Monitoring", "24 h – 2.160 €", "2.160 €", "6 h – 540 € (Builds, Modul-Updates)", "—"],
               ["Supportfälle pro Jahr", "16 h – 1.440 €", "12 h – 1.080 €", "8 h – 720 €", "8 h – 720 €"],
               ["Neue Odoo-Version (Jahr 3)", "5 Tage – 5.000 € (OpenUpgrade)", "2.000 € (Odoo-Upgrade-Service + Tests)", "1.500 € (Upgrade auf Staging, Tests)", "500 € (Tests)"]],
        years=("Jahr", "3 (neue Version)", "5 Jahre", "."),
        ycols=["Jahr", "Community, eigener Server", "Enterprise, eigener Server", "Odoo.sh", "Odoo Online"],
        sup_h="Die Kleinigkeiten: wer repariert was",
        sup=["**„Der Bot funktioniert nicht mehr“** (Telegram-Benachrichtigungen, eine Integration): eigener Server – der Dienstleister prüft Prozess, Log und Token und startet neu; Odoo.sh – ist es ein eigenes Modul, Ihr Partner; der Odoo-Support deckt nur den Standard. So oder so: nach Stunden, wenn keine Pauschale vereinbart ist.",
             "**„Die Mail geht nicht“**: eigener Server – SPF/DKIM/DMARC im DNS, ein Relay oder Gmail/Outlook (App-Passwort oder OAuth), und viele VPS-Anbieter sperren ausgehenden Port 25; Odoo.sh / Online – Odoos Mailserver sind inklusive, Sie setzen nur die DNS-Einträge Ihrer Domain.",
             "**„Odoo ist langsam oder weg“**: eigener Server – Platte voll, zu wenige Worker, PostgreSQL; bemerkt wird es nur mit Monitoring. Odoo.sh – Odoo überwacht rund um die Uhr; langsame eigene Module bleiben Sache Ihres Partners.",
             "**„Zertifikat abgelaufen“, „Backup fehlt“**: eigener Server – certbot-Erneuerung und Wiederherstellungstests gehören zur Administration; Odoo.sh / Online – automatisch.",
             "**„Fehler nach einem Update“** im Standard: Enterprise (alle Varianten außer Community) – Odoo-Support ist in der Lizenz enthalten; Community – nur Ihr Partner oder die OCA-Community.",
             "**Schulung** ist keine Einmalsache: neue Mitarbeiter, neue Funktionen, die neue Version – einen halben Tag pro Jahr einplanen. Kurze Videos der eigenen Abläufe sparen am meisten Zeit.",
             "**Support schriftlich vereinbaren**: Reaktionszeit (z. B. 4 Stunden an Werktagen), Monatspauschale oder Stundensatz, wer welche Zugänge hat, wie Notfälle gemeldet werden."],
        con=["Über 5 Jahre mit 5 Anwendern: **Odoo Online 21.270 €**, **Odoo.sh 35.670 €**, Community auf eigenem Server 37.300 €, Enterprise auf eigenem Server 43.430 €.",
             "**Odoo.sh schlägt den eigenen Server**, obwohl das Hosting mehr kostet: Administration, Zertifikate, Backups und Upgrades sind dort günstiger. Es ist der richtige Ort, wenn Sie eigene Module brauchen.",
             "**Community auf eigenem Server** lohnt sich mit eigener IT im Haus, mehr Anwendern (jeder weitere Custom-Anwender kostet etwa 539 € im Jahr) oder wenn die Daten auf dem eigenen Server bleiben müssen.",
             "**Enterprise auf eigenem Server** ist die teuerste Variante – nur bei besonderen Anforderungen (Datenstandort, Einbindung ins eigene Netz)."]),
    "ru": dict(
        h="Приложение: свой сервер или Odoo.sh – годы с 1-го по 5-й, всё включено",
        p="Odoo.sh – собственная платформа Odoo для Odoo Enterprise со своими модулями: GitHub, тестовые копии (staging), бэкапы в трёх местах, мониторинг – серверы обслуживает Odoo, код – вы или ваш партнёр. Нужен план Custom. Пример: компания на 5 пользователей, которой нужны свои модули (иначе хватит Odoo Online – он приведён для сравнения). Цены Odoo.sh – из публичных обзоров цен при оплате за год: 57,60 за worker, 0,20 за ГБ и 14,40 за тестовую копию в месяц (значения в USD; цену в евро проверить в калькуляторе на odoo.com/pricing). Ставка дня 1000 €, час 90 €.",
        items=[["Статья затрат", "Community, свой сервер", "Enterprise, свой сервер", "Odoo.sh", "Odoo Online (для сравнения)"],
               ["Настройка сервера / проекта (разово)", "½ дня – 500 € (готовая Docker-сборка)", "500 €", "½ дня – 500 € (проект, GitHub, домен)", "—"],
               ["Внедрение: настройки, импорт данных, документы (разово)", "8 дней – 8000 € (2 дня на недостающие приложения Enterprise)", "6 дней – 6000 €", "6000 €", "6000 €"],
               ["Обучение", "2 дня – 2000 €, потом ½ дня в год", "так же", "так же", "так же"],
               ["Лицензия, 5 пользователей", "0 €", "Custom: 2154 € в 1-й год, потом 2694 €", "так же", "Standard: 1194 €, потом 1494 €"],
               ["Хостинг в год", "360 € (VPS 25 € + внешний бэкап 5 € в месяц)", "360 €", "888 € (1 worker, 10 ГБ, 1 staging)", "включён"],
               ["Администрирование в год: обновления, бэкапы, мониторинг", "24 ч – 2160 €", "2160 €", "6 ч – 540 € (сборки, обновления модулей)", "—"],
               ["Обращения в поддержку в год", "16 ч – 1440 €", "12 ч – 1080 €", "8 ч – 720 €", "8 ч – 720 €"],
               ["Новая версия Odoo (3-й год)", "5 дней – 5000 € (OpenUpgrade)", "2000 € (сервис обновления Odoo + тесты)", "1500 € (обновление на staging, тесты)", "500 € (тесты)"]],
        years=("Год", "3 (новая версия)", "5 лет", " "),
        ycols=["Год", "Community, свой сервер", "Enterprise, свой сервер", "Odoo.sh", "Odoo Online"],
        sup_h="Мелочи: кто что чинит",
        sup=["**«Бот перестал работать»** (уведомления в Telegram, интеграция): свой сервер – специалист проверяет процесс, лог и токен и перезапускает; Odoo.sh – если это ваш модуль, то ваш партнёр; поддержка Odoo покрывает только стандарт. В любом случае – почасово, если не договорились об абонентской плате.",
             "**«Почта не работает»**: свой сервер – SPF/DKIM/DMARC в DNS, релей или Gmail/Outlook (пароль приложения или OAuth), а многие VPS-провайдеры блокируют исходящий порт 25; Odoo.sh / Online – почтовые серверы Odoo включены, вы только прописываете DNS-записи своего домена.",
             "**«Odoo тормозит или лежит»**: свой сервер – закончился диск, мало воркеров, PostgreSQL; заметно только при мониторинге. Odoo.sh – Odoo следит круглосуточно; медленные собственные модули – забота вашего партнёра.",
             "**«Истёк сертификат», «нет бэкапа»**: свой сервер – продление certbot и тесты восстановления входят в администрирование; Odoo.sh / Online – автоматически.",
             "**«Ошибка после обновления»** в стандартном Odoo: Enterprise (все варианты, кроме Community) – поддержка Odoo входит в лицензию; Community – только ваш партнёр или сообщество OCA.",
             "**Обучение** – не разовое: новые сотрудники, новые функции, новая версия – закладывать полдня в год. Больше всего времени экономят короткие видео своих процессов.",
             "**Поддержку оформить письменно**: время реакции (например, 4 часа в рабочие дни), абонентская плата или почасовая ставка, у кого какие доступы, как сообщать об аварии."],
        con=["За 5 лет на 5 пользователей: **Odoo Online 21 270 €**, **Odoo.sh 35 670 €**, Community на своём сервере 37 300 €, Enterprise на своём сервере 43 430 €.",
             "**Odoo.sh выгоднее своего сервера**, хотя хостинг дороже: администрирование, сертификаты, бэкапы и обновления версий там дешевле. Это правильное место, когда нужны свои модули.",
             "**Community на своём сервере** окупается при своём ИТ-специалисте, большем числе пользователей (каждый следующий пользователь Custom – около 539 € в год) или когда данные обязаны оставаться на своём сервере.",
             "**Enterprise на своём сервере** – самый дорогой вариант, только при особых требованиях (где хранятся данные, работа во внутренней сети)."]),
    "uk": dict(
        h="Додаток: власний сервер чи Odoo.sh – роки з 1-го по 5-й, усе включено",
        p="Odoo.sh – власна платформа Odoo для Odoo Enterprise зі своїми модулями: GitHub, тестові копії (staging), бекапи в трьох місцях, моніторинг – сервери обслуговує Odoo, код – ви або ваш партнер. Потрібен план Custom. Приклад: компанія на 5 користувачів, якій потрібні свої модулі (інакше вистачить Odoo Online – наведено для порівняння). Ціни Odoo.sh – з публічних оглядів цін при оплаті за рік: 57,60 за worker, 0,20 за ГБ і 14,40 за тестову копію на місяць (значення в USD; ціну в євро перевірити в калькуляторі на odoo.com/pricing). Ставка дня 1000 €, година 90 €.",
        items=[["Стаття витрат", "Community, власний сервер", "Enterprise, власний сервер", "Odoo.sh", "Odoo Online (для порівняння)"],
               ["Налаштування сервера / проєкту (разово)", "½ дня – 500 € (готова Docker-збірка)", "500 €", "½ дня – 500 € (проєкт, GitHub, домен)", "—"],
               ["Впровадження: налаштування, імпорт даних, документи (разово)", "8 днів – 8000 € (2 дні на відсутні застосунки Enterprise)", "6 днів – 6000 €", "6000 €", "6000 €"],
               ["Навчання", "2 дні – 2000 €, потім ½ дня на рік", "так само", "так само", "так само"],
               ["Ліцензія, 5 користувачів", "0 €", "Custom: 2154 € у 1-й рік, потім 2694 €", "так само", "Standard: 1194 €, потім 1494 €"],
               ["Хостинг на рік", "360 € (VPS 25 € + зовнішній бекап 5 € на місяць)", "360 €", "888 € (1 worker, 10 ГБ, 1 staging)", "включено"],
               ["Адміністрування на рік: оновлення, бекапи, моніторинг", "24 год – 2160 €", "2160 €", "6 год – 540 € (збірки, оновлення модулів)", "—"],
               ["Звернення в підтримку на рік", "16 год – 1440 €", "12 год – 1080 €", "8 год – 720 €", "8 год – 720 €"],
               ["Нова версія Odoo (3-й рік)", "5 днів – 5000 € (OpenUpgrade)", "2000 € (сервіс оновлення Odoo + тести)", "1500 € (оновлення на staging, тести)", "500 € (тести)"]],
        years=("Рік", "3 (нова версія)", "5 років", " "),
        ycols=["Рік", "Community, власний сервер", "Enterprise, власний сервер", "Odoo.sh", "Odoo Online"],
        sup_h="Дрібниці: хто що лагодить",
        sup=["**«Бот перестав працювати»** (сповіщення в Telegram, інтеграція): власний сервер – фахівець перевіряє процес, лог і токен і перезапускає; Odoo.sh – якщо це ваш модуль, то ваш партнер; підтримка Odoo покриває лише стандарт. У будь-якому разі – погодинно, якщо не домовилися про абонплату.",
             "**«Пошта не працює»**: власний сервер – SPF/DKIM/DMARC у DNS, релей або Gmail/Outlook (пароль застосунку чи OAuth), а багато VPS-провайдерів блокують вихідний порт 25; Odoo.sh / Online – поштові сервери Odoo включені, ви лише прописуєте DNS-записи свого домену.",
             "**«Odoo гальмує або лежить»**: власний сервер – закінчився диск, мало воркерів, PostgreSQL; помітно лише з моніторингом. Odoo.sh – Odoo стежить цілодобово; повільні власні модулі – турбота вашого партнера.",
             "**«Сплив сертифікат», «немає бекапу»**: власний сервер – подовження certbot і тести відновлення входять в адміністрування; Odoo.sh / Online – автоматично.",
             "**«Помилка після оновлення»** у стандартному Odoo: Enterprise (усі варіанти, крім Community) – підтримка Odoo входить у ліцензію; Community – лише ваш партнер або спільнота OCA.",
             "**Навчання** – не разове: нові працівники, нові функції, нова версія – закладати пів дня на рік. Найбільше часу заощаджують короткі відео власних процесів.",
             "**Підтримку оформити письмово**: час реакції (наприклад, 4 години в робочі дні), абонплата чи погодинна ставка, у кого які доступи, як повідомляти про аварію."],
        con=["За 5 років на 5 користувачів: **Odoo Online 21 270 €**, **Odoo.sh 35 670 €**, Community на власному сервері 37 300 €, Enterprise на власному сервері 43 430 €.",
             "**Odoo.sh вигідніший за власний сервер**, хоча хостинг дорожчий: адміністрування, сертифікати, бекапи й оновлення версій там дешевші. Це правильне місце, коли потрібні свої модулі.",
             "**Community на власному сервері** окупається з власним ІТ-фахівцем, більшою кількістю користувачів (кожен наступний користувач Custom – близько 539 € на рік) або коли дані мають залишатися на власному сервері.",
             "**Enterprise на власному сервері** – найдорожчий варіант, лише за особливих вимог (де зберігаються дані, робота у внутрішній мережі)."]),
}

for _lang, _a in _AP.items():
    _yh, _y3, _tot, _sep = _a["years"]
    _rows = [[r[0]] + [v.replace(",", _sep) for v in r[1:]] for r in _Y]
    _rows[2][0], _rows[5][0] = _y3, f"**{_tot}**"
    _b = ODOOSAP["t"][_lang]["body"]
    _b[-1:-1] = [("h", _a["h"]), ("p", _a["p"]), ("table", _a["items"]), ("table", [_a["ycols"]] + _rows),
                 ("code", "years"), ("h", _a["sup_h"]), ("ul", _a["sup"]), ("ul", _a["con"])]
