# Страница «Odoo lernen»: видеокурсы Odoo eLearning, документация Odoo 18 и наши инструкции, по разделам. 6 языков.
# Ссылки проверены 2026-11-18 (curl 200). Курсы: www.odoo.com/slides/<slug> – видео на английском с субтитрами,
# интерфейс сайта есть на de_DE, fr_FR, uk_UA, ru_RU (el – английский). Документация Odoo 18: en, de, fr (ru/uk/el – нет).
# Проверка ссылок (курс переехал / 404): python3 src/check_learn_links.py
# Новый курс/ссылку: добавить в CATS; новый раздел – ключ в CATS и название/описание в CAT_TX для всех 6 языков.

SLUG = "learn.html"

ICON = ('<path d="M2.5 9 12 4.5 21.5 9 12 13.5z"/><path d="M6.5 11v4.5c0 1.4 2.5 3 5.5 3s5.5-1.6 5.5-3V11"/>'
        '<path d="M21.5 9v5"/>')

DOC = "https://www.odoo.com/documentation/18.0/"
DOC_LANG = {"de": "de/", "fr": "fr/"}                  # остальные языки – английская документация
SLIDES_LANG = {"de": "de_DE/", "fr": "fr_FR/", "uk": "uk_UA/", "ru": "ru_RU/"}

# ключ раздела: (видеокурсы [(slug, название курса)], документация [(путь, название)], наши статьи [slug блога])
CATS = [
    ("help", [], [("applications/general/email_communication.html", "E-mail"),
                  ("applications/general/iot/devices/printer.html", "IoT: printers"),
                  ("applications/sales/point_of_sale/configuration/epos_printers.html", "POS: ePOS printers")],
     ["odoo-help-email-not-working-checklist", "odoo-help-telegram-bot-not-responding-checklist",
      "odoo-help-printing-pdf-receipt-label-printer-checklist", "odoo-email-setup-gmail-outlook-app-password-two-step-verification"]),
    ("start", [("getting-started-15", "Getting Started"), ("features-and-global-settings-34", "Features and Global Settings")],
     [("applications/essentials.html", "Essentials"), ("applications/general/users.html", "Users"),
      ("applications/productivity/discuss.html", "Discuss")],
     ["odoo-costs-licence-hosting-implementation-germany", "odoo-vs-sap-business-one-real-cost-salon-bakery-warehouse-car-repair"]),
    ("sales", [("crm-16", "CRM"), ("sales-17", "Sales"), ("subscription-20", "Subscription"), ("rental-48", "Rental")],
     [("applications/sales/crm.html", "CRM"), ("applications/sales/sales.html", "Sales"),
      ("applications/general/integrations/mail_plugins.html", "Mail plugins (Outlook, Gmail)")],
     ["crm-germany-what-people-search-google-autocomplete", "odoo-outlook-gmail-whatsapp-integration-step-by-step"]),
    ("acc", [("accounting-and-invoicing-19", "Accounting and Invoicing"), ("odoo-academy-e-invoicing-464", "Odoo Academy: e-invoicing"),
             ("masterclass-accounting-19-507", "Masterclass Accounting 19")],
     [("applications/finance/accounting.html", "Accounting"), ("applications/finance/fiscal_localizations/germany.html", "Germany (localisation, DATEV)")],
     ["odoo-datev-export-step-by-step-community-enterprise"]),
    ("stock", [("inventory-24", "Inventory"), ("purchase-23", "Purchase"), ("barcode-30", "Barcode"),
               ("masterclass-inventory-19-484", "Masterclass Inventory 19")],
     [("applications/inventory_and_mrp/inventory.html", "Inventory"), ("applications/inventory_and_mrp/purchase.html", "Purchase"),
      ("applications/inventory_and_mrp/barcode.html", "Barcode")], []),
    ("mrp", [("mrp-manufacturing-shop-floor-29", "MRP – Manufacturing & Shop Floor"), ("quality-334", "Quality"), ("plm-455", "PLM"),
             ("masterclass-mrp-19-506", "Masterclass MRP 19")],
     [("applications/inventory_and_mrp/manufacturing.html", "Manufacturing"), ("applications/inventory_and_mrp/quality.html", "Quality")], []),
    ("pos", [("point-of-sale-28", "Point of Sale"), ("masterclass-pos-18-19-435", "Masterclass POS 18/19"), ("appointments-463", "Appointments"),
             ("internet-of-things-iot-175", "Internet of Things (IoT)")],
     [("applications/sales/point_of_sale.html", "Point of Sale"), ("applications/productivity/appointments.html", "Appointments"),
      ("applications/general/iot.html", "IoT")], []),
    ("services", [("project-timesheets-21", "Project & Timesheets"), ("field-service-49", "Field Service"), ("helpdesk-51", "Helpdesk"),
                  ("planning-60", "Planning")],
     [("applications/services/project.html", "Project"), ("applications/services/field_service.html", "Field Service"),
      ("applications/services/helpdesk.html", "Helpdesk")], []),
    ("web", [("website-ecommerce-25", "Website & eCommerce"), ("marketing-27", "Marketing"),
             ("events-63", "Events"), ("surveys-62", "Surveys")],
     [("applications/websites/website.html", "Website"), ("applications/websites/ecommerce.html", "eCommerce"),
      ("applications/marketing/email_marketing.html", "Email Marketing")], []),
    ("hr", [("human-resources-32", "Human Resources")], [("applications/hr.html", "Human resources")], []),
    ("docs", [("documents-22", "Documents"), ("sign-61", "Sign"), ("knowledge-461", "Knowledge"),
              ("spreadsheet-dashboards-390", "Spreadsheet & Dashboards")],
     [("applications/productivity/documents.html", "Documents"), ("applications/productivity/sign.html", "Sign"),
      ("applications/productivity/knowledge.html", "Knowledge")], []),
    ("custom", [("studio-31", "Studio"), ("technical-training-58", "Technical Training"),
                ("technical-training-introduction-to-development-318", "Introduction to development")],
     [("applications/studio.html", "Studio"), ("developer/tutorials.html", "Developer tutorials")], []),
    ("admin", [("masterclass-odoo-sh-500", "Masterclass Odoo.sh")], [],
     ["odoo-automation-savings-backup-monitoring-staging-upgrade-contractor-checklist", "odoo-docker-compose-extra-addons-nginx", "odoo-stage-restore-stop-cron-jobs", "certbot-nginx-auto-renewal",
      "odoo-server-security-logs-secrets-ports-encryption", "odoo-production-hardening-housekeeping-monitoring",
      "telegram-bot-odoo-monitoring-deploy-stage-copy", "odoo-main-problems-limitations-devops-tips"]),
]

CAT_TX = {
    "de": {"help": ("Wenn etwas nicht geht", "Checklisten für die häufigsten Fälle: E-Mail, Bot, Drucken – erst selbst prüfen, dann uns die richtigen Angaben schicken."),
           "start": ("Erste Schritte", "Oberfläche, Suche und Filter, Benutzer und Rechte, Chat – und was Odoo kostet."),
           "sales": ("Verkauf und CRM", "Leads, Angebote, Aufträge, Abos, Vermietung, Outlook und Gmail."),
           "acc": ("Buchhaltung, Rechnungen, DATEV", "Rechnungen, E-Rechnung (XRechnung), Bank, Steuern, Export für den Steuerberater."),
           "stock": ("Lager und Einkauf", "Wareneingang, Lieferungen, Inventur, Barcode-Scanner, Bestellungen beim Lieferanten."),
           "mrp": ("Fertigung und Qualität", "Stücklisten, Fertigungsaufträge, Werkstatt, Qualitätsprüfungen, Änderungen (PLM)."),
           "pos": ("Kasse, Termine, Geräte", "Kasse im Laden, Online-Terminbuchung, Drucker, Waagen und Scanner über die IoT-Box."),
           "services": ("Projekte und Service", "Projekte, Zeiterfassung, Außendienst, Helpdesk, Einsatzplanung."),
           "web": ("Website, Shop, Marketing", "Website, Onlineshop, E-Mail-Marketing, Veranstaltungen, Umfragen."),
           "hr": ("Personal", "Mitarbeiter, Urlaub, Spesen, Bewerbungen."),
           "docs": ("Dokumente und Signatur", "Dokumente, elektronische Unterschrift, Wissensdatenbank, Tabellen und Dashboards."),
           "custom": ("Anpassen", "Studio ohne Programmierung, Einstieg in die Entwicklung eigener Module."),
           "admin": ("Betrieb und Hosting", "Für Administratoren: Docker, Backups, Zertifikate, Sicherheit, Monitoring, Odoo.sh.")},
    "en": {"help": ("When something does not work", "Checklists for the most common cases: e-mail, bot, printing – check yourself first, then send us the right details."),
           "start": ("Getting started", "Interface, search and filters, users and rights, chat – and what Odoo costs."),
           "sales": ("Sales and CRM", "Leads, quotations, orders, subscriptions, rental, Outlook and Gmail."),
           "acc": ("Accounting, invoices, DATEV", "Invoices, e-invoicing (XRechnung), bank, taxes, export for the tax advisor."),
           "stock": ("Inventory and purchase", "Receipts, deliveries, stock counts, barcode scanners, purchase orders."),
           "mrp": ("Manufacturing and quality", "Bills of materials, manufacturing orders, shop floor, quality checks, engineering changes (PLM)."),
           "pos": ("Till, appointments, devices", "Point of sale in the shop, online booking, printers, scales and scanners via the IoT box."),
           "services": ("Projects and services", "Projects, timesheets, field service, helpdesk, planning."),
           "web": ("Website, shop, marketing", "Website, online shop, e-mail marketing, events, surveys."),
           "hr": ("Human resources", "Employees, time off, expenses, recruitment."),
           "docs": ("Documents and signature", "Documents, electronic signature, knowledge base, spreadsheets and dashboards."),
           "custom": ("Customising", "Studio without programming, first steps in developing your own modules."),
           "admin": ("Operations and hosting", "For administrators: Docker, backups, certificates, security, monitoring, Odoo.sh.")},
    "fr": {"help": ("Quand quelque chose ne marche pas", "Listes de contrôle pour les cas les plus fréquents : e-mail, bot, impression – vérifier soi-même d'abord, puis nous envoyer les bonnes informations."),
           "start": ("Premiers pas", "Interface, recherche et filtres, utilisateurs et droits, discussion – et ce que coûte Odoo."),
           "sales": ("Ventes et CRM", "Pistes, devis, commandes, abonnements, location, Outlook et Gmail."),
           "acc": ("Comptabilité, factures, DATEV", "Factures, facturation électronique (XRechnung), banque, taxes, export pour le conseiller fiscal."),
           "stock": ("Stock et achats", "Réceptions, livraisons, inventaires, lecteurs de codes-barres, commandes fournisseurs."),
           "mrp": ("Fabrication et qualité", "Nomenclatures, ordres de fabrication, atelier, contrôles qualité, modifications (PLM)."),
           "pos": ("Caisse, rendez-vous, appareils", "Point de vente en magasin, prise de rendez-vous en ligne, imprimantes, balances et lecteurs via la box IoT."),
           "services": ("Projets et services", "Projets, feuilles de temps, interventions sur site, assistance, planning."),
           "web": ("Site web, boutique, marketing", "Site web, boutique en ligne, e-mail marketing, événements, sondages."),
           "hr": ("Ressources humaines", "Employés, congés, notes de frais, recrutement."),
           "docs": ("Documents et signature", "Documents, signature électronique, base de connaissances, tableurs et tableaux de bord."),
           "custom": ("Personnaliser", "Studio sans programmation, premiers pas dans le développement de modules."),
           "admin": ("Exploitation et hébergement", "Pour les administrateurs : Docker, sauvegardes, certificats, sécurité, supervision, Odoo.sh.")},
    "el": {"help": ("Όταν κάτι δεν λειτουργεί", "Λίστες ελέγχου για τις πιο συχνές περιπτώσεις: e-mail, bot, εκτύπωση – πρώτα έλεγχος από εσάς, μετά μας στέλνετε τα σωστά στοιχεία."),
           "start": ("Πρώτα βήματα", "Περιβάλλον, αναζήτηση και φίλτρα, χρήστες και δικαιώματα, συνομιλία – και πόσο κοστίζει το Odoo."),
           "sales": ("Πωλήσεις και CRM", "Δυνητικοί πελάτες, προσφορές, παραγγελίες, συνδρομές, ενοικίαση, Outlook και Gmail."),
           "acc": ("Λογιστική, τιμολόγια, DATEV", "Τιμολόγια, ηλεκτρονική τιμολόγηση (XRechnung), τράπεζα, φόροι, εξαγωγή για τον φοροτεχνικό."),
           "stock": ("Αποθήκη και αγορές", "Παραλαβές, αποστολές, απογραφή, σαρωτές barcode, παραγγελίες σε προμηθευτές."),
           "mrp": ("Παραγωγή και ποιότητα", "Λίστες υλικών, εντολές παραγωγής, χώρος παραγωγής, έλεγχοι ποιότητας, αλλαγές (PLM)."),
           "pos": ("Ταμείο, ραντεβού, συσκευές", "Ταμείο στο κατάστημα, online κρατήσεις, εκτυπωτές, ζυγαριές και σαρωτές μέσω IoT box."),
           "services": ("Έργα και υπηρεσίες", "Έργα, φύλλα χρόνου, υπηρεσίες πεδίου, helpdesk, προγραμματισμός."),
           "web": ("Ιστότοπος, κατάστημα, μάρκετινγκ", "Ιστότοπος, ηλεκτρονικό κατάστημα, e-mail marketing, εκδηλώσεις, έρευνες."),
           "hr": ("Ανθρώπινο δυναμικό", "Υπάλληλοι, άδειες, έξοδα, προσλήψεις."),
           "docs": ("Έγγραφα και υπογραφή", "Έγγραφα, ηλεκτρονική υπογραφή, βάση γνώσεων, υπολογιστικά φύλλα και dashboards."),
           "custom": ("Προσαρμογή", "Studio χωρίς προγραμματισμό, πρώτα βήματα στην ανάπτυξη δικών σας modules."),
           "admin": ("Λειτουργία και φιλοξενία", "Για διαχειριστές: Docker, αντίγραφα ασφαλείας, πιστοποιητικά, ασφάλεια, παρακολούθηση, Odoo.sh.")},
    "uk": {"help": ("Коли щось не працює", "Чек-листи для найчастіших випадків: пошта, бот, друк – спершу перевірити самим, потім надіслати нам потрібні дані."),
           "start": ("Перші кроки", "Інтерфейс, пошук і фільтри, користувачі та права, чат – і скільки коштує Odoo."),
           "sales": ("Продажі та CRM", "Ліди, пропозиції, замовлення, підписки, оренда, Outlook і Gmail."),
           "acc": ("Бухгалтерія, рахунки, DATEV", "Рахунки, е-рахунки (XRechnung), банк, податки, експорт для податкового консультанта."),
           "stock": ("Склад і закупівлі", "Надходження, відвантаження, інвентаризація, сканери штрихкодів, замовлення постачальникам."),
           "mrp": ("Виробництво та якість", "Специфікації, виробничі замовлення, цех, перевірки якості, зміни (PLM)."),
           "pos": ("Каса, запис, пристрої", "Каса в магазині, онлайн-запис, принтери, ваги й сканери через IoT-box."),
           "services": ("Проєкти та сервіс", "Проєкти, облік часу, виїзний сервіс, helpdesk, планування."),
           "web": ("Сайт, магазин, маркетинг", "Сайт, інтернет-магазин, email-маркетинг, події, опитування."),
           "hr": ("Персонал", "Працівники, відпустки, витрати, найм."),
           "docs": ("Документи та підпис", "Документи, електронний підпис, база знань, таблиці й дашборди."),
           "custom": ("Налаштування під себе", "Studio без програмування, перші кроки в розробці власних модулів."),
           "admin": ("Експлуатація та хостинг", "Для адміністраторів: Docker, бекапи, сертифікати, безпека, моніторинг, Odoo.sh.")},
    "ru": {"help": ("Когда что-то не работает", "Чек-листы для самых частых случаев: почта, бот, печать – сначала проверить самим, потом прислать нам нужные данные."),
           "start": ("Первые шаги", "Интерфейс, поиск и фильтры, пользователи и права, чат – и сколько стоит Odoo."),
           "sales": ("Продажи и CRM", "Лиды, предложения, заказы, подписки, аренда, Outlook и Gmail."),
           "acc": ("Бухгалтерия, счета, DATEV", "Счета, электронные счета (XRechnung), банк, налоги, экспорт для налогового консультанта."),
           "stock": ("Склад и закупки", "Поступления, отгрузки, инвентаризация, сканеры штрихкодов, заказы поставщикам."),
           "mrp": ("Производство и качество", "Спецификации, производственные заказы, цех, проверки качества, изменения (PLM)."),
           "pos": ("Касса, запись, устройства", "Касса в магазине, онлайн-запись, принтеры, весы и сканеры через IoT-box."),
           "services": ("Проекты и сервис", "Проекты, учёт времени, выездной сервис, helpdesk, планирование."),
           "web": ("Сайт, магазин, маркетинг", "Сайт, интернет-магазин, email-маркетинг, мероприятия, опросы."),
           "hr": ("Персонал", "Сотрудники, отпуска, расходы, найм."),
           "docs": ("Документы и подпись", "Документы, электронная подпись, база знаний, таблицы и дашборды."),
           "custom": ("Настройка под себя", "Studio без программирования, первые шаги в разработке своих модулей."),
           "admin": ("Эксплуатация и хостинг", "Для администраторов: Docker, бэкапы, сертификаты, безопасность, мониторинг, Odoo.sh.")},
}

TX = {
    "de": {"nav": "Odoo lernen", "title": "Odoo lernen: Videos, Anleitungen, Hilfe",
           "intro": "Die offiziellen Videokurse und Handbücher von Odoo, nach Aufgaben sortiert – dazu unsere eigenen Anleitungen und Checklisten für typische Probleme.",
           "note": "Die Videos von Odoo eLearning sind auf Englisch mit Untertiteln; die Kursseiten öffnen sich mit deutscher Oberfläche. Die Odoo-Dokumentation (Version 18) gibt es auf Deutsch.",
           "videos": "Videokurse (Odoo eLearning)", "docs": "Dokumentation (Odoo 18)", "ours": "Unsere Anleitungen", "toc": "Bereiche"},
    "en": {"nav": "Learn Odoo", "title": "Learn Odoo: videos, guides, help",
           "intro": "Odoo's official video courses and manuals, sorted by task – plus our own guides and checklists for typical problems.",
           "note": "The Odoo eLearning videos are in English with subtitles. The Odoo documentation (version 18) is linked in English.",
           "videos": "Video courses (Odoo eLearning)", "docs": "Documentation (Odoo 18)", "ours": "Our guides", "toc": "Sections"},
    "fr": {"nav": "Apprendre Odoo", "title": "Apprendre Odoo : vidéos, guides, aide",
           "intro": "Les cours vidéo et manuels officiels d'Odoo, classés par tâche – avec nos propres guides et listes de contrôle pour les problèmes courants.",
           "note": "Les vidéos Odoo eLearning sont en anglais avec sous-titres ; les pages des cours s'ouvrent en français. La documentation Odoo (version 18) existe en français.",
           "videos": "Cours vidéo (Odoo eLearning)", "docs": "Documentation (Odoo 18)", "ours": "Nos guides", "toc": "Rubriques"},
    "el": {"nav": "Μάθετε Odoo", "title": "Μάθετε Odoo: βίντεο, οδηγοί, βοήθεια",
           "intro": "Τα επίσημα μαθήματα βίντεο και εγχειρίδια του Odoo, ταξινομημένα ανά εργασία – μαζί με τους δικούς μας οδηγούς και λίστες ελέγχου για συνηθισμένα προβλήματα.",
           "note": "Τα βίντεο του Odoo eLearning είναι στα αγγλικά με υπότιτλους. Η τεκμηρίωση του Odoo (έκδοση 18) υπάρχει στα αγγλικά.",
           "videos": "Μαθήματα βίντεο (Odoo eLearning)", "docs": "Τεκμηρίωση (Odoo 18)", "ours": "Οι οδηγοί μας", "toc": "Ενότητες"},
    "uk": {"nav": "Вивчити Odoo", "title": "Вивчити Odoo: відео, інструкції, допомога",
           "intro": "Офіційні відеокурси й посібники Odoo, розкладені за задачами, – плюс наші власні інструкції та чек-листи для типових проблем.",
           "note": "Відео Odoo eLearning – англійською із субтитрами; сторінки курсів відкриваються з українським інтерфейсом. Документація Odoo (версія 18) – англійською (української та російської версій немає).",
           "videos": "Відеокурси (Odoo eLearning)", "docs": "Документація (Odoo 18)", "ours": "Наші інструкції", "toc": "Розділи"},
    "ru": {"nav": "Изучить Odoo", "title": "Изучить Odoo: видео, инструкции, помощь",
           "intro": "Официальные видеокурсы и руководства Odoo, разложенные по задачам, – плюс наши собственные инструкции и чек-листы для типичных проблем.",
           "note": "Видео Odoo eLearning – на английском с субтитрами; страницы курсов открываются с русским интерфейсом. Документация Odoo (версия 18) – на английском (русской и украинской версий нет).",
           "videos": "Видеокурсы (Odoo eLearning)", "docs": "Документация (Odoo 18)", "ours": "Наши инструкции", "toc": "Разделы"},
}


def page_html(lang, E, url, posts):
    """posts: {slug: post} – для названий наших статей на нужном языке."""
    X, C = TX[lang], CAT_TX[lang]
    sl = "https://www.odoo.com/" + SLIDES_LANG.get(lang, "") + "slides/"
    dl = DOC + DOC_LANG.get(lang, "")
    ext = ' target="_blank" rel="noopener"'
    toc = " ".join(f'<a class="post-tag" href="#{k}">{E(C[k][0])}</a>' for k, *_ in CATS)
    cards = []
    for key, courses, docs, ours in CATS:
        cols = []
        if ours:
            li = []
            for s in ours:
                p = posts.get(s)
                if p:
                    t = p["t"].get(lang) or p["t"]["en"]
                    li.append(f'<li><a href="{url(lang, "blog/" + s + ".html")}">{E(t["title"])}</a></li>')
            if li:
                cols.append(f'<div><h3>{E(X["ours"])}</h3><ul>{"".join(li)}</ul></div>')
        if courses:
            cols.append(f'<div><h3>▶ {E(X["videos"])}</h3><ul>'
                        + "".join(f'<li><a href="{sl}{s}"{ext}>{E(n)} ↗</a></li>' for s, n in courses) + "</ul></div>")
        if docs:
            cols.append(f'<div><h3>{E(X["docs"])}</h3><ul>'
                        + "".join(f'<li><a href="{dl}{p}"{ext}>{E(n)} ↗</a></li>' for p, n in docs) + "</ul></div>")
        cards.append(f'<section class="post-card learn-cat" id="{key}"><h2>{E(C[key][0])}</h2><p>{E(C[key][1])}</p>'
                     f'<div class="learn-cols">{"".join(cols)}</div></section>')
    return (f'<main class="sec blog"><div class="wrap narrow"><h1>{E(X["title"])}</h1><p class="intro">{E(X["intro"])}</p>'
            f'<p class="post-note">{E(X["note"])}</p><p class="post-tags learn-toc"><b>{E(X["toc"])}:</b> {toc}</p>'
            f'<div class="post-list">{"".join(cards)}</div></div></main>')
