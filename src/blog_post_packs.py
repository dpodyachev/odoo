# Статья 37: Odoo Success Packs – цены 2026 (odoo.com/de_DE/pricing-packs, 19.11.2026) и наши пакеты часов: в Германии
# примерно вдвое дешевле, и на 3–15 % ниже даже самых низких цен Odoo в других странах. Языки: en, de, ru, uk.
# Цифры наших пакетов – config.PACKS; при изменении цен поправить таблицы здесь.

PACKS_POST = {
    "slug": "odoo-success-packs-prices-alternative-half-price",
    "date": "2026-11-19",
    "tags": ["Odoo", "Success Packs", "Costs", "Support"],
    "code": {
        "calc": ("python · price per hour and saving – put in your own numbers", """# Odoo Success Packs, odoo.com/de_DE/pricing-packs, 19.11.2026 (excl. VAT)
odoo = {"Starter": (4, 587.06, 499.00), "Basis": (25, 3100, 2635), "Standard": (50, 5500, 4675),
        "Custom": (100, 9900, 8415), "Pro": (200, 19800, 16830)}
ours = [239, 1375, 2450, 4450, 8600]          # 2027.pp.ua/#packs, no VAT (§ 19 UStG)

for (name, (h, regular, new)), our in zip(odoo.items(), ours):
    print(f"{name:9}{h:4} h  Odoo {regular / h:6.2f} / {new / h:6.2f} €/h"
          f"   ours {our / h:5.2f} €/h  ->  {1 - our / new:4.0%} below the new-customer price")

# Starter    4 h  Odoo 146.77 / 124.75 €/h   ours 59.75 €/h  ->   52% below the new-customer price
# Basis     25 h  Odoo 124.00 / 105.40 €/h   ours 55.00 €/h  ->   48% below the new-customer price
# Standard  50 h  Odoo 110.00 /  93.50 €/h   ours 49.00 €/h  ->   48% below the new-customer price
# Custom   100 h  Odoo  99.00 /  84.15 €/h   ours 44.50 €/h  ->   47% below the new-customer price
# Pro      200 h  Odoo  99.00 /  84.15 €/h   ours 43.00 €/h  ->   49% below the new-customer price"""),
    },
    "links": [
        ("Odoo Success Packs (odoo.com, DE)", "https://www.odoo.com/de_DE/pricing-packs"),
        ("Our hour packs", "@page:#packs"),
        ("Blog: what Odoo really costs in Germany", "@blog:odoo-costs-licence-hosting-implementation-germany"),
        ("Blog: automating Odoo operations", "@blog:odoo-automation-savings-backup-monitoring-staging-upgrade-contractor-checklist"),
    ],
    "t": {},
}


def _d(title, summary, intro, note, h, odoo_p, odoo_table, odoo_ul, our_p, our_table, our_ul, why_ul, diff_table,
       diff_ul, odoo_better, steps, closing, links):
    return {"title": title, "summary": summary, "body": [
        ("p", intro), ("note", note),
        ("h", h[0]), ("p", odoo_p), ("table", odoo_table), ("ul", odoo_ul),
        ("h", h[1]), ("p", our_p), ("table", our_table), ("ul", our_ul), ("code", "calc"),
        ("h", h[2]), ("ul", why_ul),
        ("h", h[3]), ("table", diff_table), ("ul", diff_ul),
        ("h", h[4]), ("ul", odoo_better),
        ("h", h[5]), ("ol", steps),
        ("h", h[6]), ("p", closing),
        ("links", links)]}


_ODOO_ROWS = [("Starter", "4", "587.06", "499.00", "146.77", "124.75"),
              ("Basis", "25", "3,100", "2,635", "124.00", "105.40"),
              ("Standard", "50", "5,500", "4,675", "110.00", "93.50"),
              ("Custom", "100", "9,900", "8,415", "99.00", "84.15"),
              ("Pro", "200", "19,800", "16,830", "99.00", "84.15")]
_OUR_ROWS = [("Start", "4", "239", "59.75", "124.75", "52"),
             ("Basic", "25", "1,375", "55.00", "105.40", "48"),
             ("Standard", "50", "2,450", "49.00", "93.50", "48"),
             ("Plus", "100", "4,450", "44.50", "84.15", "47"),
             ("Pro", "200", "8,600", "43.00", "84.15", "49")]


def _de_num(s):
    """1,375 → 1.375; 59.75 → 59,75 (deutsche Schreibweise; für ru/uk – пробел и запятая)."""
    return s.replace(",", "§").replace(".", ",").replace("§", ".")


def _ru_num(s):
    return s.replace(",", " ").replace(".", ",") if "," in s and "." not in s else s.replace(".", ",")


def _odoo_table(head, num, cur="€"):
    return [head] + [[n, h, f"{num(r)} {cur}", f"{num(nw)} {cur}", f"{num(a)} {cur}", f"{num(b)} {cur}"]
                     for n, h, r, nw, a, b in _ODOO_ROWS]


def _our_table(head, num, cur="€"):
    return [head] + [[n, h, f"{num(p)} {cur}", f"{num(a)} {cur}", f"{num(b)} {cur}", f"−{s} %"]
                     for n, h, p, a, b, s in _OUR_ROWS]


_ID = lambda s: s  # noqa: E731

PACKS_POST["t"]["en"] = _d(
    "Odoo Success Packs: 2026 prices – and hour packs for about half the price",
    "What Odoo's Success Packs cost in Germany in November 2026 (Starter to Pro, 4 to 200 consultant hours), the price per hour (99–147 €, 84–125 € with the new-customer discount), why other countries see other prices, and our hour packs of the same sizes for about half – including what is the same, what differs and when Odoo's own pack is the better choice.",
    "A Success Pack is a prepaid block of consultant hours from Odoo S.A. for implementation, training and configuration. The price is on odoo.com – but only as a pack price. Divided by the hours, it is easy to compare with any other offer. We did that, and put our own hour packs of the same sizes next to it.",
    "Odoo prices from odoo.com/de_DE/pricing-packs on 19 November 2026, excluding VAT. Odoo shows different prices depending on the visitor's country, and changes prices and discounts – check before deciding. We are an independent Odoo service provider, not Odoo S.A. and not an Odoo partner; Odoo is a trademark of Odoo S.A.",
    ["Odoo Success Packs: prices in Germany", "Our hour packs: about half the price", "Why we can be cheaper", "What is the same – and what differs", "When Odoo's own pack is the better choice", "Step by step: choose the pack size", "Conclusion"],
    "Five packs from 4 to 200 hours. New customers get 15 % off their first pack:",
    _odoo_table(["Pack", "Hours", "Returning customers", "New customers (−15 %)", "€/h returning", "€/h new"], _ID),
    ["**99–147 € per hour**, or **84–125 €** with the new-customer discount – and the discount applies to the first pack only.",
     "Odoo's footnotes: travel time is billed and travel costs are charged separately; **maintaining additional modules or lines of code costs an extra monthly fee**.",
     "**Performance problems** need a pack of at least 50 hours – they are not covered by the free support.",
     "**Other countries, other prices**: from some countries the same page shows considerably lower prices – we saw 280 € to 9,180 € for new customers. Customers in Germany get the prices above."],
    "Same sizes, prepaid, valid for 12 months, used in 15-minute steps:",
    _our_table(["Pack", "Hours", "Price", "€/h", "Odoo €/h (new customers)", "Saving"], _ID),
    ["**About half** of Odoo's new-customer price in every pack size – and 55–59 % below the regular price for returning customers.",
     "**Even below Odoo's lowest prices**: compared with the cheapest country prices we found (280–9,180 €), our packs are still 3–15 % cheaper.",
     "**No VAT is added** to our prices (small business, § 19 UStG). Odoo adds 19 %. For companies that can deduct input VAT this makes no difference – compare net prices, and it is still about half. For those who cannot (doctors, insurance brokers, associations, small businesses themselves) it is another 19 %.",
     "The hours can be used for **operations too**: updates, migration, server, backups, monitoring, performance – from the 4-hour pack on."],
    ["**Routine work is automated.** Backups with a restore test, monitoring, test copies of the database, updates – scripts and bots do that, not consultant hours. We describe exactly how in this blog.",
     "**No sales and partner overhead.** No licence sales targets, no account managers, no ticket levels – you talk to the person who does the work.",
     "**Remote first.** Most work happens remotely from Stuttgart; on-site visits only when they help, billed as incurred.",
     "**Fewer hours for the same result.** With direct database and server access, a lot of diagnosis takes minutes instead of meetings."],
    [["", "Odoo Success Pack", "Our hour pack"],
     ["Who does the work", "Odoo S.A. consultants", "independent Odoo service provider (not an Odoo partner)"],
     ["Price per hour (Germany)", "84–125 € (new), 99–147 €", "43–59.75 €"],
     ["VAT", "+19 %", "none (§ 19 UStG)"],
     ["Maintenance of own modules", "extra monthly fee", "no extra fee – time is taken from the pack"],
     ["Performance problems", "pack of 50 hours or more", "from the 4-hour pack"],
     ["Server, backups, monitoring", "Odoo Online / Odoo.sh", "also own servers (Community and Enterprise)"],
     ["Travel", "time and costs billed", "billed as incurred"],
     ["Validity, billing", "not stated on the page", "12 months, 15-minute steps, monthly balance"]],
    ["The comparison is about the **price per hour**. What an hour delivers depends on the task – ask both for a scope before you buy.",
     "Odoo's packs are made for **Odoo Enterprise customers**. Our packs work for **Community and Enterprise**, on Odoo Online, Odoo.sh or your own server."],
    ["**Licence and contract questions** – only Odoo S.A. decides about your subscription, users and Enterprise licence terms.",
     "**You want everything from the vendor**: one contract for licence, hosting and consulting.",
     "**Odoo Online without access to the server or database** – there, all parties, including us, are limited to configuration and Studio.",
     "If you are unsure, take our smallest pack for an analysis – and decide with the result in hand."],
    ["**List the tasks** for the next 12 months: setup, data import, training, updates, migration, integrations.",
     "**Estimate in hours** – or ask us for an estimate; a first analysis takes about an hour.",
     "**Add 20 %** for questions and small changes along the way.",
     "**Pick the next bigger pack** – unused hours are cheaper than a second small pack.",
     "**Compare per hour, net**, with the same scope – Odoo, a partner and us."],
    "Odoo's Success Packs are good value for what they include – but at 84–147 € per hour in Germany they are not the cheapest way to get Odoo work done. Our hour packs have the same sizes and cost about half; even against Odoo's lowest country prices they are 3–15 % cheaper. The difference comes from automation, not from fewer hours: routine work is done by scripts, and the hours go into what you actually need.",
    "Links")

PACKS_POST["t"]["de"] = _d(
    "Odoo Success Packs: Preise 2026 – und Stundenpakete zum halben Preis",
    "Was die Odoo Success Packs in Deutschland im November 2026 kosten (Starter bis Pro, 4 bis 200 Beraterstunden), der Preis pro Stunde (99–147 €, mit Neukundenrabatt 84–125 €), warum andere Länder andere Preise sehen, und unsere Stundenpakete in denselben Größen zum etwa halben Preis – mit Gemeinsamkeiten, Unterschieden und der Frage, wann das Paket von Odoo die bessere Wahl ist.",
    "Ein Success Pack ist ein vorausbezahltes Kontingent an Beraterstunden von Odoo S.A. für Einführung, Schulung und Konfiguration. Der Preis steht auf odoo.com – allerdings nur als Paketpreis. Geteilt durch die Stunden lässt er sich mit jedem anderen Angebot vergleichen. Genau das haben wir gemacht und unsere Stundenpakete in denselben Größen danebengestellt.",
    "Odoo-Preise laut odoo.com/de_DE/pricing-packs am 19. November 2026, zzgl. USt. Odoo zeigt je nach Land des Besuchers unterschiedliche Preise und ändert Preise und Rabatte – vor einer Entscheidung bitte prüfen. Wir sind ein unabhängiger Odoo-Dienstleister, weder Odoo S.A. noch Odoo-Partner; Odoo ist eine Marke der Odoo S.A.",
    ["Odoo Success Packs: Preise in Deutschland", "Unsere Stundenpakete: etwa zum halben Preis", "Warum wir günstiger sein können", "Was gleich ist – und was sich unterscheidet", "Wann das Paket von Odoo die bessere Wahl ist", "Schritt für Schritt: die Paketgröße wählen", "Fazit"],
    "Fünf Pakete von 4 bis 200 Stunden. Neukunden erhalten 15 % Rabatt auf das erste Paket:",
    _odoo_table(["Paket", "Stunden", "Bestandskunden", "Neukunden (−15 %)", "€/h Bestand", "€/h Neukunde"], _de_num),
    ["**99–147 € pro Stunde**, mit Neukundenrabatt **84–125 €** – und der Rabatt gilt nur für das erste Paket.",
     "Die Fußnoten von Odoo: Reisezeit wird abgerechnet, Reisekosten separat; **für die Wartung zusätzlicher Module oder Codezeilen fallen zusätzliche monatliche Gebühren an**.",
     "**Performance-Probleme** erfordern ein Paket mit mindestens 50 Stunden – der kostenlose Support deckt sie nicht ab.",
     "**Andere Länder, andere Preise**: Aus manchen Ländern zeigt dieselbe Seite deutlich niedrigere Preise – wir haben für Neukunden 280 € bis 9.180 € gesehen. Kunden in Deutschland erhalten die Preise oben."],
    "Gleiche Größen, vorausbezahlt, 12 Monate gültig, Verbrauch im 15-Minuten-Takt:",
    _our_table(["Paket", "Stunden", "Preis", "€/h", "Odoo €/h (Neukunden)", "Ersparnis"], _de_num),
    ["**Etwa die Hälfte** des Neukundenpreises von Odoo – in jeder Paketgröße; gegenüber dem regulären Preis für Bestandskunden 55–59 % weniger.",
     "**Sogar unter den niedrigsten Odoo-Preisen**: Verglichen mit den günstigsten Länderpreisen, die wir gefunden haben (280–9.180 €), sind unsere Pakete noch 3–15 % günstiger.",
     "**Keine Umsatzsteuer** auf unsere Preise (Kleinunternehmer, § 19 UStG). Odoo berechnet 19 %. Für vorsteuerabzugsberechtigte Unternehmen spielt das keine Rolle – vergleichen Sie netto, es bleibt etwa die Hälfte. Wer keinen Vorsteuerabzug hat (Ärzte, Versicherungsmakler, Vereine, Kleinunternehmer), spart weitere 19 %.",
     "Die Stunden gelten **auch für den Betrieb**: Updates, Migration, Server, Backups, Monitoring, Performance – schon ab dem 4-Stunden-Paket."],
    ["**Routinearbeit ist automatisiert.** Backups mit Wiederherstellungstest, Monitoring, Testkopien der Datenbank, Updates – das erledigen Skripte und Bots, nicht Beraterstunden. Wie genau, beschreiben wir in diesem Blog.",
     "**Kein Vertriebs- und Partner-Overhead.** Keine Lizenz-Verkaufsziele, keine Account-Manager, keine Ticket-Ebenen – Sie sprechen mit der Person, die die Arbeit macht.",
     "**Remote zuerst.** Die meiste Arbeit läuft remote aus Stuttgart; Vor-Ort-Termine nur, wenn sie helfen, nach Aufwand.",
     "**Weniger Stunden für dasselbe Ergebnis.** Mit direktem Zugriff auf Datenbank und Server dauert viele Diagnose Minuten statt Meetings."],
    [["", "Odoo Success Pack", "Unser Stundenpaket"],
     ["Wer arbeitet", "Berater der Odoo S.A.", "unabhängiger Odoo-Dienstleister (kein Odoo-Partner)"],
     ["Preis pro Stunde (Deutschland)", "84–125 € (Neukunden), 99–147 €", "43–59,75 €"],
     ["Umsatzsteuer", "+19 %", "keine (§ 19 UStG)"],
     ["Wartung eigener Module", "zusätzliche monatliche Gebühr", "keine Zusatzgebühr – Zeit aus dem Paket"],
     ["Performance-Probleme", "Paket ab 50 Stunden", "ab dem 4-Stunden-Paket"],
     ["Server, Backups, Monitoring", "Odoo Online / Odoo.sh", "auch eigene Server (Community und Enterprise)"],
     ["Reise", "Zeit und Kosten werden berechnet", "nach Aufwand"],
     ["Gültigkeit, Abrechnung", "auf der Seite nicht angegeben", "12 Monate, 15-Minuten-Takt, monatliche Übersicht"]],
    ["Verglichen wird der **Preis pro Stunde**. Was eine Stunde bringt, hängt von der Aufgabe ab – lassen Sie sich vor dem Kauf von beiden einen Umfang nennen.",
     "Die Pakete von Odoo sind für **Odoo-Enterprise-Kunden** gedacht. Unsere Pakete gelten für **Community und Enterprise**, auf Odoo Online, Odoo.sh oder Ihrem eigenen Server."],
    ["**Lizenz- und Vertragsfragen** – über Abonnement, Benutzer und Enterprise-Lizenzbedingungen entscheidet nur Odoo S.A.",
     "**Alles vom Hersteller**: ein Vertrag für Lizenz, Hosting und Beratung.",
     "**Odoo Online ohne Zugriff auf Server oder Datenbank** – dort sind alle, auch wir, auf Konfiguration und Studio beschränkt.",
     "Wenn Sie unsicher sind: Nehmen Sie unser kleinstes Paket für eine Analyse – und entscheiden Sie mit dem Ergebnis in der Hand."],
    ["**Aufgaben auflisten** für die nächsten 12 Monate: Einrichtung, Datenimport, Schulung, Updates, Migration, Schnittstellen.",
     "**In Stunden schätzen** – oder uns schätzen lassen; eine erste Analyse dauert etwa eine Stunde.",
     "**20 % Puffer** für Fragen und kleine Änderungen unterwegs.",
     "**Das nächstgrößere Paket wählen** – ungenutzte Stunden sind günstiger als ein zweites kleines Paket.",
     "**Pro Stunde und netto vergleichen**, bei gleichem Umfang – Odoo, ein Partner und wir."],
    "Die Success Packs von Odoo sind ihr Geld wert – aber mit 84–147 € pro Stunde in Deutschland nicht der günstigste Weg, Odoo-Arbeit erledigen zu lassen. Unsere Stundenpakete haben dieselben Größen und kosten etwa die Hälfte; selbst gegenüber den niedrigsten Länderpreisen von Odoo sind sie 3–15 % günstiger. Der Unterschied kommt aus der Automatisierung, nicht aus weniger Stunden: Routinearbeit erledigen Skripte, und die Stunden fließen in das, was Sie wirklich brauchen.",
    "Links")

PACKS_POST["t"]["ru"] = _d(
    "Odoo Success Packs: цены 2026 – и пакеты часов почти вдвое дешевле",
    "Сколько стоят Success Packs Odoo в Германии в ноябре 2026 (от Starter до Pro, 4–200 часов консультанта), цена часа (99–147 €, со скидкой новым клиентам 84–125 €), почему в других странах цены другие, и наши пакеты часов тех же размеров примерно за полцены – что одинаково, что отличается и когда пакет самой Odoo лучше.",
    "Success Pack – это предоплаченный блок часов консультантов Odoo S.A. на внедрение, обучение и настройку. Цена есть на odoo.com, но только за пакет. Если разделить на часы, её легко сравнить с любым другим предложением. Мы так и сделали и поставили рядом свои пакеты часов тех же размеров.",
    "Цены Odoo – с odoo.com/de_DE/pricing-packs на 19 ноября 2026, без НДС. Odoo показывает разные цены в зависимости от страны посетителя и меняет цены и скидки – проверяйте перед решением. Мы – независимый поставщик услуг по Odoo, не Odoo S.A. и не партнёр Odoo; Odoo – товарный знак Odoo S.A.",
    ["Odoo Success Packs: цены в Германии", "Наши пакеты часов: примерно вдвое дешевле", "Почему мы можем быть дешевле", "Что одинаково – и что отличается", "Когда пакет самой Odoo – лучший выбор", "Шаг за шагом: как выбрать размер пакета", "Итог"],
    "Пять пакетов от 4 до 200 часов. Новые клиенты получают скидку 15 % на первый пакет:",
    _odoo_table(["Пакет", "Часов", "Постоянные клиенты", "Новые клиенты (−15 %)", "€/ч постоянные", "€/ч новые"], _ru_num),
    ["**99–147 € в час**, со скидкой новым клиентам **84–125 €** – и скидка действует только на первый пакет.",
     "Сноски Odoo: время в пути оплачивается, дорожные расходы – отдельно; **за сопровождение дополнительных модулей или строк кода берётся отдельная ежемесячная плата**.",
     "**Проблемы производительности** требуют пакета не меньше 50 часов – бесплатная поддержка их не покрывает.",
     "**Другие страны – другие цены**: из некоторых стран та же страница показывает заметно более низкие цены – мы видели 280–9 180 € для новых клиентов. Клиентам в Германии показываются цены выше."],
    "Те же размеры, предоплата, действуют 12 месяцев, списание по 15 минут:",
    _our_table(["Пакет", "Часов", "Цена", "€/ч", "Odoo €/ч (новые клиенты)", "Экономия"], _ru_num),
    ["**Почти вдвое дешевле** цены Odoo для новых клиентов – в каждом размере пакета; по сравнению с обычной ценой для постоянных клиентов – на 55–59 % меньше.",
     "**Даже ниже самых низких цен Odoo**: по сравнению с самыми дешёвыми ценами по странам, которые мы нашли (280–9 180 €), наши пакеты всё равно дешевле на 3–15 %.",
     "**НДС не добавляется** (малый предприниматель, § 19 UStG). Odoo добавляет 19 %. Для компаний с вычетом входного НДС это не важно – сравнивайте нетто, всё равно примерно половина. Кто вычета не имеет (врачи, страховые брокеры, объединения, сами малые предприниматели), экономит ещё 19 %.",
     "Часы можно тратить **и на эксплуатацию**: обновления, миграцию, сервер, бэкапы, мониторинг, производительность – уже с пакета на 4 часа."],
    ["**Рутина автоматизирована.** Бэкапы с проверкой восстановления, мониторинг, тестовые копии базы, обновления – это делают скрипты и боты, а не часы консультанта. Как именно – описываем в этом блоге.",
     "**Без накладных расходов продаж и партнёрства.** Нет планов продаж лицензий, аккаунт-менеджеров и уровней тикетов – вы говорите с тем, кто делает работу.",
     "**Сначала удалённо.** Большая часть работы – удалённо из Штутгарта; выезды – только когда они помогают, по фактическим расходам.",
     "**Меньше часов на тот же результат.** С прямым доступом к базе и серверу многая диагностика занимает минуты, а не встречи."],
    [["", "Odoo Success Pack", "Наш пакет часов"],
     ["Кто работает", "консультанты Odoo S.A.", "независимый поставщик услуг по Odoo (не партнёр Odoo)"],
     ["Цена часа (Германия)", "84–125 € (новые), 99–147 €", "43–59,75 €"],
     ["НДС", "+19 %", "нет (§ 19 UStG)"],
     ["Сопровождение своих модулей", "отдельная ежемесячная плата", "без доплаты – время из пакета"],
     ["Проблемы производительности", "пакет от 50 часов", "с пакета на 4 часа"],
     ["Сервер, бэкапы, мониторинг", "Odoo Online / Odoo.sh", "и на своих серверах (Community и Enterprise)"],
     ["Выезды", "время и расходы оплачиваются", "по фактическим расходам"],
     ["Срок, учёт", "на странице не указан", "12 месяцев, шаг 15 минут, ежемесячный отчёт"]],
    ["Сравнивается **цена часа**. Что даёт час, зависит от задачи – попросите у обеих сторон объём работ до покупки.",
     "Пакеты Odoo рассчитаны на **клиентов Odoo Enterprise**. Наши – для **Community и Enterprise**, на Odoo Online, Odoo.sh или своём сервере."],
    ["**Вопросы лицензии и договора** – о подписке, пользователях и условиях Enterprise решает только Odoo S.A.",
     "**Всё от производителя**: один договор на лицензию, хостинг и консультации.",
     "**Odoo Online без доступа к серверу и базе** – там все, включая нас, ограничены настройками и Studio.",
     "Если сомневаетесь – возьмите наш самый маленький пакет на анализ и решайте с результатом на руках."],
    ["**Выпишите задачи** на 12 месяцев: настройка, импорт данных, обучение, обновления, миграция, интеграции.",
     "**Оцените в часах** – или попросите оценку у нас; первый анализ занимает около часа.",
     "**Добавьте 20 %** на вопросы и мелкие изменения по ходу.",
     "**Берите следующий по размеру пакет** – неиспользованные часы дешевле второго маленького пакета.",
     "**Сравнивайте за час и нетто** при одинаковом объёме – Odoo, партнёра и нас."],
    "Success Packs Odoo стоят своих денег – но при 84–147 € в час в Германии это не самый дешёвый способ получить работу по Odoo. Наши пакеты часов тех же размеров стоят примерно вдвое меньше; даже по сравнению с самыми низкими ценами Odoo в других странах они дешевле на 3–15 %. Разница – от автоматизации, а не от меньшего числа часов: рутину делают скрипты, а часы идут на то, что вам действительно нужно.",
    "Ссылки")

PACKS_POST["t"]["uk"] = _d(
    "Odoo Success Packs: ціни 2026 – і пакети годин майже вдвічі дешевші",
    "Скільки коштують Success Packs Odoo в Німеччині в листопаді 2026 (від Starter до Pro, 4–200 годин консультанта), ціна години (99–147 €, зі знижкою новим клієнтам 84–125 €), чому в інших країнах ціни інші, і наші пакети годин тих самих розмірів приблизно за пів ціни – що однакове, що відрізняється і коли пакет самої Odoo кращий.",
    "Success Pack – це передплачений блок годин консультантів Odoo S.A. на впровадження, навчання й налаштування. Ціна є на odoo.com, але лише за пакет. Якщо поділити на години, її легко порівняти з будь-якою іншою пропозицією. Ми так і зробили й поставили поруч свої пакети годин тих самих розмірів.",
    "Ціни Odoo – з odoo.com/de_DE/pricing-packs на 19 листопада 2026, без ПДВ. Odoo показує різні ціни залежно від країни відвідувача та змінює ціни й знижки – перевіряйте перед рішенням. Ми – незалежний постачальник послуг з Odoo, не Odoo S.A. і не партнер Odoo; Odoo – торговельна марка Odoo S.A.",
    ["Odoo Success Packs: ціни в Німеччині", "Наші пакети годин: приблизно вдвічі дешевше", "Чому ми можемо бути дешевшими", "Що однакове – і що відрізняється", "Коли пакет самої Odoo – кращий вибір", "Крок за кроком: як вибрати розмір пакета", "Підсумок"],
    "П'ять пакетів від 4 до 200 годин. Нові клієнти отримують знижку 15 % на перший пакет:",
    _odoo_table(["Пакет", "Годин", "Постійні клієнти", "Нові клієнти (−15 %)", "€/год постійні", "€/год нові"], _ru_num),
    ["**99–147 € за годину**, зі знижкою новим клієнтам **84–125 €** – і знижка діє лише на перший пакет.",
     "Виноски Odoo: час у дорозі оплачується, витрати на дорогу – окремо; **за супровід додаткових модулів чи рядків коду стягується окрема щомісячна плата**.",
     "**Проблеми продуктивності** потребують пакета щонайменше на 50 годин – безкоштовна підтримка їх не покриває.",
     "**Інші країни – інші ціни**: з деяких країн та сама сторінка показує помітно нижчі ціни – ми бачили 280–9 180 € для нових клієнтів. Клієнтам у Німеччині показуються ціни вище."],
    "Ті самі розміри, передплата, діють 12 місяців, списання по 15 хвилин:",
    _our_table(["Пакет", "Годин", "Ціна", "€/год", "Odoo €/год (нові клієнти)", "Економія"], _ru_num),
    ["**Майже вдвічі дешевше** за ціну Odoo для нових клієнтів – у кожному розмірі пакета; порівняно зі звичайною ціною для постійних клієнтів – на 55–59 % менше.",
     "**Навіть нижче за найнижчі ціни Odoo**: порівняно з найдешевшими цінами за країнами, які ми знайшли (280–9 180 €), наші пакети все одно дешевші на 3–15 %.",
     "**ПДВ не додається** (малий підприємець, § 19 UStG). Odoo додає 19 %. Для компаній із вирахуванням вхідного ПДВ це неважливо – порівнюйте нетто, все одно приблизно половина. Хто вирахування не має (лікарі, страхові брокери, об'єднання, самі малі підприємці), заощаджує ще 19 %.",
     "Години можна витрачати **й на експлуатацію**: оновлення, міграцію, сервер, бекапи, моніторинг, продуктивність – уже з пакета на 4 години."],
    ["**Рутину автоматизовано.** Бекапи з перевіркою відновлення, моніторинг, тестові копії бази, оновлення – це роблять скрипти й боти, а не години консультанта. Як саме – описуємо в цьому блозі.",
     "**Без накладних витрат продажів і партнерства.** Немає планів продажу ліцензій, акаунт-менеджерів і рівнів тікетів – ви говорите з тим, хто робить роботу.",
     "**Спершу віддалено.** Більшість роботи – віддалено зі Штутгарта; виїзди – лише коли вони допомагають, за фактичними витратами.",
     "**Менше годин на той самий результат.** З прямим доступом до бази й сервера багато діагностики займає хвилини, а не зустрічі."],
    [["", "Odoo Success Pack", "Наш пакет годин"],
     ["Хто працює", "консультанти Odoo S.A.", "незалежний постачальник послуг з Odoo (не партнер Odoo)"],
     ["Ціна години (Німеччина)", "84–125 € (нові), 99–147 €", "43–59,75 €"],
     ["ПДВ", "+19 %", "немає (§ 19 UStG)"],
     ["Супровід власних модулів", "окрема щомісячна плата", "без доплати – час із пакета"],
     ["Проблеми продуктивності", "пакет від 50 годин", "з пакета на 4 години"],
     ["Сервер, бекапи, моніторинг", "Odoo Online / Odoo.sh", "і на власних серверах (Community та Enterprise)"],
     ["Виїзди", "час і витрати оплачуються", "за фактичними витратами"],
     ["Строк, облік", "на сторінці не вказано", "12 місяців, крок 15 хвилин, щомісячний звіт"]],
    ["Порівнюється **ціна години**. Що дає година, залежить від задачі – попросіть в обох сторін обсяг робіт до купівлі.",
     "Пакети Odoo розраховані на **клієнтів Odoo Enterprise**. Наші – для **Community та Enterprise**, на Odoo Online, Odoo.sh або власному сервері."],
    ["**Питання ліцензії й договору** – про підписку, користувачів і умови Enterprise вирішує лише Odoo S.A.",
     "**Усе від виробника**: один договір на ліцензію, хостинг і консультації.",
     "**Odoo Online без доступу до сервера й бази** – там усі, включно з нами, обмежені налаштуваннями та Studio.",
     "Якщо вагаєтеся – візьміть наш найменший пакет на аналіз і вирішуйте з результатом на руках."],
    ["**Випишіть задачі** на 12 місяців: налаштування, імпорт даних, навчання, оновлення, міграція, інтеграції.",
     "**Оцініть у годинах** – або попросіть оцінку в нас; перший аналіз займає близько години.",
     "**Додайте 20 %** на питання й дрібні зміни по ходу.",
     "**Беріть наступний за розміром пакет** – невикористані години дешевші за другий маленький пакет.",
     "**Порівнюйте за годину й нетто** за однакового обсягу – Odoo, партнера й нас."],
    "Success Packs Odoo варті своїх грошей – але за 84–147 € на годину в Німеччині це не найдешевший спосіб отримати роботу з Odoo. Наші пакети годин тих самих розмірів коштують приблизно вдвічі менше; навіть порівняно з найнижчими цінами Odoo в інших країнах вони дешевші на 3–15 %. Різниця – від автоматизації, а не від меншої кількості годин: рутину роблять скрипти, а години йдуть на те, що вам справді потрібно.",
    "Посилання")
