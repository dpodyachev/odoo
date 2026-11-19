T = {
    "meta_title": 'Odoo Architecture, Development & Migration for DACH – Goldberg Odoo Services',
    "meta_desc": 'Odoo for companies in Germany, Austria and Switzerland: architecture, custom module development, integrations (DATEV, e-invoicing, Shopware, JTL, DHL, DPD), migrations and performance. Fixed prices, remote from Stuttgart.',
    "nav": {"services": "Services", "dach": "DATEV & e-invoicing", "bot": "Monitoring", "prices": "Pricing",
            "about": "About", "blog": 'Blog & how-tos', "contact": "Contact"},
    "kicker": 'Odoo architecture · Development · Integration · Migration · Performance',
    "h1": 'Odoo <span>that just works.</span>',
    "sub": 'Architecture, development, integrations, migrations and performance for Odoo Community and Enterprise – remote from Stuttgart for Germany, Austria and Switzerland, with fixed prices and one dedicated contact.',
    "cta_book": "Book a call – 30 min free",
    "badges": ["Fixed prices, no surprises", "24/7 monitoring", "Updates without downtime", "Odoo 14 to 19",
               "GDPR-compliant with a DPA"],
    "hero_card": ["Odoo reachable", "Backup successful", "Disk – warning", "Errors in log today",
                  "Your server, watched around the clock"],
    "services_title": "Services",
    "services_intro": 'From architecture to further development – technical work on your Odoo without agency overhead. Licences: directly from Odoo S.A. · End-user support: via partners.',
    "services": [('install', 'Architecture & setup', 'A concept for modules, data flow and servers – then the build: Odoo on your server (contract in your name), Docker, PostgreSQL, SSL, backups. Cleanly documented and handed over to you.'), ('support', 'Development & customisation', 'Custom modules and extensions in Python and OWL, reports, automations – versioned in Git, tested on a copy, with a way back.'), ('fix', 'Troubleshooting', "Odoo won't start, is slow, an update fails, e-mails don't go out? Analysis of logs and database, a clear cause, a lasting fix."), ('update', 'Updates & migration', 'Updates as a planned project: first on a test copy, then in production with a way back. Version upgrades (e.g. 14 → 17) including adapting custom modules.'), ('integration', 'Integration & interfaces', 'DATEV, e-invoicing, online shops, carriers, banks and custom interfaces (REST, XML-RPC) – designed, developed and tested.'), ('server', 'Performance & security', 'PostgreSQL and worker tuning, load tests, slow-query analysis, hardening of servers and access – measured before and after every change.')],
    "dach_title": "What Odoo needs to do in Germany, Austria and Switzerland",
    "dach_intro": "A standard installation is rarely enough here. I set these up for you – and keep them up to date.",
    "dach": [
        ('Accounting', 'Charts of accounts, closing & DATEV', 'German accounting in Odoo – set up so your tax advisor can take over without rework.', ['Charts of accounts SKR03 / SKR04, tax keys and rates', 'Balance sheet and P&L under HGB; BWA via DATEV or as a custom report', 'DATEV export (EXTF) with document images, test export before month-end closing']),
        ('Mandatory since 2025', 'E-invoicing: XRechnung & ZUGFeRD', 'Since 1 Jan 2025 companies in Germany must be able to receive e-invoices; from 2027/2028 (depending on turnover) they must also send them in B2B. Odoo can do it – when configured properly.', ['ZUGFeRD / Factur-X (PDF with XML) and XRechnung (UBL/CII)', 'Leitweg-ID for public authorities, validator checks', 'Receiving and automatically capturing incoming e-invoices']),
        ('Taxes & payments', 'ELSTER, SEPA and direct debit', 'From the VAT pre-return to the payment run – less manual work in accounting.', ['VAT pre-return (USt-VA) from Odoo, submission to ELSTER (depending on edition via a module or via DATEV)', 'SEPA credit transfers and SEPA direct debit with mandate management', 'GiroCode (EPC QR) on invoices, bank statements in CAMT format']),
        ('GoBD', 'Proper bookkeeping under GoBD', 'Run Odoo audit-proof: entries stay unalterable and traceable, data can be exported for tax audits.', ['Locking of posted entries, lock dates, audit trail', 'Data export for tax audits (data carrier provision, Z3)', 'Retention periods, help with the process documentation (Verfahrensdokumentation)']),
        ('GDPR', 'Hosting in Germany or the EU', 'Your data stays in Europe – on a server of your choice, secured and documented.', ['Server and database in Germany or the EU (e.g. Hetzner, IONOS)', 'Encrypted backups within the EU, tested restores', 'DPA under Art. 28 GDPR, access only as needed']),
        ('Commerce', 'E-commerce & logistics', 'Orders, stock and shipping flow automatically between your shop, Odoo and the carrier.', ['Shopware, JTL-Wawi, WooCommerce', 'DHL, DPD, GLS: labels and tracking', 'Syncing prices, stock and invoices']),
        ('AT · CH', 'Austria & Switzerland', 'Local requirements without detours.', ['Austria: e-invoices to the federal government (ebInterface / PEPPOL)', 'Switzerland: QR-bill, VAT (MWST), CHF and EUR side by side', 'Multilingual documents (DE / FR / EN)']),
    ],
    "dach_note": 'Note: no software is “GoBD-certified” by itself – what matters is the setup, the processes and the process documentation. I take care of the technical part and align it with your tax advisor.',
    "impl_title": 'Odoo implementation step by step',
    "impl_intro": 'An implementation starts with a thorough analysis of your business and the design of the architecture, goes through development, testing and training your team, and ends with a phased go-live and ongoing support.',
    "impl": [
        ('Kick-off & analysis', 'Map business processes, review German accounting requirements, define goals and scope.'),
        ('Concept & architecture', 'Modules, interfaces, data migration and servers – a clear plan with a fixed price or budget.'),
        ('Setup & localisation', 'Installation and German localisation: taxes, SKR03/04, XRechnung/ZUGFeRD, DATEV and ELSTER.'),
        ('Workshops & development', 'Tailor CRM, inventory, manufacturing, sales and accounting to your company – customising where the standard falls short.'),
        ('Testing', 'Test runs with real processes: document flow, correct postings, invoices, interfaces.'),
        ('Training', 'Training for users and key users, short guides for daily work.'),
        ('Go-live & oversight', 'Phased start in production, then monitoring, updates as a project and further development.'),
    ],
    "yearly": 'Paid annually: {p} / year – 2 months free',
    "bot_title": "Monitoring bot: your Odoo at a glance – right in Telegram",
    "bot_intro": 'Every oversight plan includes my monitoring bot. It checks your server continuously and reports problems before your staff notice them. On request I set the bot up as a separate instance for your team.',
    "bot_points": [
        ("Availability:", "Odoo, database, web server, SSL certificate, disk space."),
        ("Errors:", "Odoo and nginx logs summarised – only what matters, no noise."),
        ("Background jobs:", "scheduled actions (cron) and queues, stuck jobs."),
        ("Backups:", "every night – with checks that they can really be restored."),
        ("Updates at the push of a button:", "pull code → update modules → restart, with rollback to the previous state."),
        ('Users & activity:', '/users shows who works in Odoo today, who is online right now and who is most active – a basis for licences and cleaning up old accounts.'),
        ('AI analysis with /analyze:', 'logs, response times and server load are summarised, and an AI explains the cause in plain words and suggests the fix. Passwords and keys are masked first; used only with your consent.'),
    ],
    "bot_note": "Sample data – names and addresses redacted.",
    "bot_online": "bot · online",
    "chat_caption": "What the bot looks like day to day (example).",
    "chat": [
        {"who": "me", "html": "/status"},
        {"who": "bot", "html": "<b>PROD</b> · ▒▒▒▒▒.de<br>✅ Odoo active, 200 OK in 0.21 s<br>✅ PostgreSQL · 2.4 GB<br>"
                               "⚠️ Disk 86 % (12 GB free)<br>✅ SSL valid until 23 Feb<br>✅ Backup 03:00 · 1.1 GB"},
        {"who": "me", "html": "/errors"},
        {"who": "bot", "html": "<b>Errors today: 2</b><br>• sale.order: Expected singleton (2×)<br>"
                               "<i>Serialization conflicts hidden: 14</i>"},
        {"who": "me", "html": "/update"},
        {"who": "bot", "html": "<b>/update PROD</b> · ▒▒▒▒<br>Changed modules (3): sale_custom, stock_report, l10n_de_datev",
         "buttons": ["▶️ Update 3 modules", "Cancel"]},
        {"who": "bot", "html": "✅ Done in 1 min 40 s, 0 errors<br>Restart Odoo to load the new code.",
         "buttons": ["🔄 Restart Odoo"]},
    ],
    "process_title": "How we work together",
    "process": [
        ("Intro call", "30 minutes by video or Telegram – free. You tell me where it hurts."),
        ("Health check or quote", "I review your system and give you a fixed price or a suitable plan."),
        ("Implementation", "First on a test copy, then in production – at a time that suits you."),
        ('Technical oversight', 'Regular analysis, updates as a tested project and further development – with a report and predictable monthly costs.'),
    ],
    "prices_title": "Pricing",
    "prices_intro": "Transparent and predictable. Small tasks billed by time, projects at a fixed price after a health check.",
    "offer": {"title": 'Introductory offer', "text": 'For new clients: the first {h} hours at {p}/h instead of 65 € – valid until {d}. A good way to get to know each other: a small fix, an update or a health check.', "cta": 'Book now', "date": '%d %b %Y'},
    "per_month": "/ month",
    "incl_hours": "{h} hours of work included",
    "reaction": {"2": "Response within 2 business days", "1": "Response next business day",
                 "4h": "Response within 4 h (Mon–Fri 9–18)"},
    "plans": {'basic': {'name': 'Basic', 'desc': 'Technical oversight for smaller systems.', 'features': ['Monitoring bot & monthly analysis with report', 'Security updates as a tested project', 'Backup concept with restore test']}, 'business': {'name': 'Business', 'desc': 'Oversight and further development for companies that work in Odoo every day.', 'features': ['Everything in Basic', 'Customisations and modules from the included hours', 'Quarterly report: performance, database, risks']}, 'premium': {'name': 'Premium', 'desc': 'For business-critical systems.', 'features': ['Everything in Business', 'Quarterly architecture review & roadmap', 'Yearly load test with report']}},
    "plans_note": 'Extra hours: €65 / h. Cancel monthly. Weekend work by arrangement: €95 / h. Licences: directly from Odoo S.A. · End-user support: via partners.',
    "table_title": "Individual services",
    "table_head": ["Service", "Price"],
    "units": {"h": "/ hour", "fix": "fixed price", "from": "from", "pct": 'of the project'},
    "price_names": {
        "hourly_support": ('Development & technical work', 'customisations, analyses, planned work – billed in 15-minute steps'),
        "hourly_urgent": ('Urgent troubleshooting', 'incident or outage – analysis and fix under time pressure, weekends included'),
        "healthcheck": ("Odoo health check", "server, backups, modules, performance, security – written report with action plan"),
        "diagnosis": ("Initial incident diagnosis", "up to 2 h of debugging, then billed by time (€95 / h)"),
        "install": ('Setup to a concept', 'Odoo + PostgreSQL in Docker on your server, SSL, backups, e-mail, monitoring'),
        "module_update": ("Module update with rollback", "git pull, update on a test copy, update in production"),
        "migration": ("Version migration", "e.g. Odoo 14 → 17, including a test run on a copy"),
        "datev": ("DATEV export", "setup, account mapping, test export with your tax office"),
        "einvoice": ("E-invoicing (XRechnung / ZUGFeRD)", "sending and receiving, validation, Leitweg-ID"),
        "shop": ("Shop integration", "Shopware, JTL-Wawi, WooCommerce"),
        "shipping": ("Carrier integration", "DHL, DPD, GLS – labels, tracking"),
        "qrbill": ("Swiss QR-bill", "QR-IBAN, references, VAT"),
        "monitoring": ('Grafana & Prometheus setup', 'Exporters for server, PostgreSQL, Docker, nginx; dashboards and alerts'),
        "loadtest": ('Load test with Locust', 'scenarios, test copy, measurement, report with recommendations'),
        "replica": ('PostgreSQL read replica for Odoo 18/19', 'streaming replication, db_replica_host, measurement with/without replica, review of custom modules'),
        "bot": ("Monitoring bot for your team", "your own instance, set up for your server"),
    },
    "vat_note": "All prices in EUR. Under § 19 UStG (small business scheme) no VAT is charged. Billed monthly by time in 15-minute steps or at the agreed fixed price.",
    "kleinunternehmer": "Small business owner under § 19 UStG (German VAT Act) – no VAT is charged.",
    "cases_title": "Typical fixed-price cases",
    "cases": [
        ("“Odoo is down after a server update”",
         "Initial diagnosis, root cause (e.g. Python package, database, proxy), fix and a short report on how to prevent it.",
         "usually €190 + 1–2 h × €95"),
        ("“We need e-invoices by the end of the year”",
         "Set up ZUGFeRD/XRechnung, check master data, validate test invoices, train the team.",
         "from €900 fixed price"),
        ('“Our Odoo runs – but nobody looks after it”', 'Health check, then technical oversight in the Business plan: monitoring, updates as a project, quarterly report.', '€490 once + €690 / month'),
    ],
    "about_title": "About me",
    "about": [
        'I have been developing and running Odoo systems for many years – from architecture and custom modules to production systems with hundreds of modules.',
        'I work on Odoo projects for companies in retail, logistics, services and call centres: architecture, development, integrations, migrations and performance. I live in Stuttgart and work remotely for clients across the DACH region – on-site visits in the Stuttgart area by arrangement.',
        'For larger projects I have a well-practised development team: Odoo developers (Python, OWL), analysts and testers. New modules, interfaces and migrations follow a clear process from requirements to testing – and I remain your single contact.',
        "You get one dedicated contact who knows your system – no ticket queue, no hand-offs.",
    ],
    "about_facts": ['University degree (specialist): automation of technological processes and production, electromechanics (state university, Ukraine; anabin H+)', "Odoo 14 – 19, Community & Enterprise", "Linux · Docker · PostgreSQL · nginx",
                    "Python, OWL, XML-RPC / REST", "Git-based deployments with rollback",
                    "Languages: Ukrainian, Russian (native) · English (B2) · Greek, German (basic)",
                    'Own team: development, analysis, QA'],
    "faq_title": "FAQ",
    "faq": [
        ("Community or Enterprise?", "Both. I'll also help you decide – Community with selected OCA modules is often enough."),
        ("Do you only work remotely?", "Yes, via SSH or VPN – secure and with no travel costs. On-site in the Stuttgart area too."),
        ("How is access to our data handled?",
         "With a data processing agreement (DPA) under the GDPR. Access only as far as needed, time-limited on request."),
        ("What if an update goes wrong?",
         "Updates run on a copy first. In production the previous code state is saved – rolling back takes minutes."),
        ('We already have an Odoo partner.', "No problem – I'm happy to take over architecture, development, performance and servers while your partner handles the business processes."),
        ('Do you sell licences or hosting?', "No. You buy licences directly from Odoo S.A.; the server runs in your name at a provider of your choice (e.g. Hetzner). End-user support for everyday questions is handled by partners – I'm happy to name contacts."),
        ("How do you bill?", "Monthly by time in 15-minute steps or at the agreed fixed price, by bank transfer."),
    ],
    "contact_title": "Let's talk",
    "contact_text": "Tell me briefly which Odoo version you use and where it hurts – I usually reply the same business day.",
    "contact_note": "No contact form, no cookies – just Telegram, e-mail or a call.",
    "footer_tag": 'Odoo architecture, development, integration, migration and performance for Germany, Austria and Switzerland.',
    "footer_note": "This website uses no cookies and no tracking.",
    "impressum": "Legal notice",
    "privacy": "Privacy",
    "legal_note": "Translation for convenience. The German version is legally binding:",
    "impressum_page": {
        "title": "Legal notice (Impressum)",
        "html": """
<h2>Information pursuant to § 5 DDG</h2>
<p>{name}<br>{street}<br>{city}<br>{country}</p>
<h2>Contact</h2>
<p>E-mail: {email}<br>Telegram: {telegram}<br>Phone: {phone}<br>WhatsApp: {whatsapp}</p>
<h2>VAT</h2>
<p>{vat}</p>
<h2>Responsible for content pursuant to § 18 (2) MStV</h2>
<p>{name}, address as above</p>
<h2>Consumer dispute resolution</h2>
<p>I am neither willing nor obliged to take part in dispute resolution proceedings before a consumer arbitration board.
My services are aimed at businesses.</p>
<h2>Liability for links</h2>
<p>This website contains links to external third-party websites (e.g. Telegram, Cal.com) whose content I cannot influence.
The respective provider is responsible for that content.</p>
""",
    },
    "privacy_page": {
        "title": "Privacy policy",
        "html": """
<h2>1. Controller</h2>
<p>{name}, {street}, {city}, {country}<br>E-mail: {email}</p>
<h2>2. In short</h2>
<p>This website sets <b>no cookies</b>, uses <b>no tracking</b>, no analytics, no advertising pixels, no embedded third-party
content and no externally loaded fonts. There is no contact form. Your browser's local storage is not used either.</p>
<h2>3. Hosting and server logs</h2>
<p>The website is served via Cloudflare Pages (Cloudflare, Inc., 101 Townsend St, San Francisco, CA 94107, USA).
When you visit, Cloudflare processes technically necessary data (IP address, date and time, page requested, browser type)
to deliver the site and protect it from attacks. Legal basis: Art. 6(1)(f) GDPR (legitimate interest in secure, stable operation).
Cloudflare is certified under the EU-US Data Privacy Framework; a data processing agreement with standard contractual clauses is in place.
I do not analyse this data myself.</p>
<h2>4. Contact by e-mail or Telegram</h2>
<p>If you write to me, I process your details (name, contact data, message content) to answer your request
(Art. 6(1)(b) GDPR – pre-contractual measures, otherwise (f)). The data is deleted once the request is settled and no statutory
retention obligations apply. E-mail is handled by Google Gmail (Google Ireland Ltd., Dublin). Telegram is operated by
Telegram Messenger Inc. (Dubai, UAE); using it is voluntary and subject to Telegram's privacy policy – you can always e-mail instead.</p>
<h2>5. Booking a call (Cal.com)</h2>
<p>The “Book a call” button leads to Cal.com (Cal.com, Inc., USA). Only if you book an appointment there does Cal.com process
your details (name, e-mail, requested time) under its own privacy policy. Legal basis: Art. 6(1)(b) GDPR.</p>
<h2>6. Your rights</h2>
<p>You have the right of access (Art. 15), rectification (Art. 16), erasure (Art. 17), restriction of processing (Art. 18),
data portability (Art. 20) and objection (Art. 21 GDPR). An informal e-mail is enough.</p>
<h2>7. Right to complain</h2>
<p>You can lodge a complaint with a data protection supervisory authority, e.g. the State Commissioner for Data Protection
and Freedom of Information Baden-Württemberg, Lautenschlagerstraße 20, 70173 Stuttgart, Germany.</p>
<h2>8. Data processing for clients</h2>
<p>If I get access to personal data of your company while supporting your Odoo system, we conclude a separate data processing
agreement (Art. 28 GDPR).</p>
<p class="small">Last updated: November 2026</p>
""",
    },
    "mon_title": 'Monitoring with Grafana & Prometheus',
    "mon_intro": 'When Telegram alerts are not enough: dashboards with history, metrics and alerts for your Odoo – on your own server, your data stays with you.',
    "mon": [
        ('node_exporter', 'Server', 'CPU, memory, disks, network and load – with weeks of history.'),
        ('postgres_exporter', 'PostgreSQL', 'Connections, slow queries, locks, database size, replication.'),
        ('cAdvisor', 'Docker', 'Resources per container: Odoo, workers, database, helper services.'),
        ('blackbox · nginx', 'Availability', 'External response times, HTTP errors, SSL certificate expiry.'),
        ('Odoo · Loki', 'Application', 'Workers, cron run times, queues (queue_job) and errors from the logs.'),
        ('Alertmanager', 'Alerts', 'Notifications via Telegram or e-mail – with thresholds that fit your business.'),
    ],
    "mon_note": 'Runs alongside the monitoring bot or on its own. Setup at a fixed price, ongoing evaluation within an oversight plan.',
    "lt_title": 'Load testing with Locust',
    "lt_intro": 'Can your Odoo handle 50, 100 or 300 concurrent users – and what happens at month-end closing? I simulate real workflows with Locust, measure the limits and show where it gets stuck. Always on a test copy, never on the live system.',
    "lt_types_title": 'Which tests – and what they show',
    "lt_types": [('Performance testing', "The umbrella term: how fast and stable Odoo responds under defined conditions – your system's real performance instead of guesses."), ('Load testing', 'The expected number of users on a normal day: are the targets met, e.g. p95 under 1 second?'), ('Stress testing', 'Beyond the limit: where does the system break, how does it show – and does it recover on its own?'), ('Spike testing', 'A sudden rush: month-end closing, a newsletter, a sales day – can Odoo take the jump?'), ('Endurance / soak testing', 'Normal load for many hours: memory leaks, growing queues, worker restarts.'), ('Volume testing', 'Large amounts of data: millions of journal items, big warehouses, long lists and reports.'), ('Scalability testing', 'What do more workers, CPU, RAM or a second server really bring – measured, not estimated.')],
    "lt": [('locust', 'Scenarios based on your workflows', 'Sales create quotations, the warehouse validates deliveries, accounting issues invoices, customers order in the web shop – weighted, with realistic pauses.'), ('JSON-RPC · HTTP', 'Real Odoo calls', 'Login, search, list and form views, create, confirm, PDF reports – via the same interface the browser uses. Test data is generated automatically.'), ('ramp-up', 'Load stages & peaks', 'Step by step from 10 to 50, 100, 300 users; sustained load over hours (memory leaks) and peaks such as month-end or sales days.'), ('p95 · p99', 'Measurable metrics', 'Response times (median, p95, p99), error rate and requests per second – live in the Locust UI and in Grafana next to CPU, RAM and PostgreSQL.'), ('workers · pg', 'Finding bottlenecks', 'Number of workers and memory limits, slow SQL queries and missing indexes, locks, connections (pgbouncer), nginx, slow modules and computed fields.'), ('report', 'Report with before/after', 'How many users the system handles today, where the limit is, what each measure gains – re-measured every time. You keep the scenarios for future upgrades.')],
    "lt_code": 'Example scenario (locustfile.py)',
    "lt_note": 'Ideal before go-live, before a version upgrade or when Odoo is "sometimes slow". Fixed price after a short scenario review.',
    "lt_shots": {"caps": ['Locust web UI: statistics per request (median, 95%, 99%, failures)', 'Charts: requests/s, response times p50/p95 and user count while ramping up to 80 users'], "note": 'A real Locust run (80 virtual users: sales, warehouse, accounting) against a demo environment – no client data. Click to enlarge.', "full": 'Full screen'},
    "slides_title": 'Examples from projects',
    "slides_intro": 'Excerpts from real implementations – customer data made unrecognisable.',
    "slide_alt": 'Example {n}',
    "slides_prev": 'Previous example',
    "slides_next": 'Next example',
    "slides_goto": 'Show example {n}',
    "theme_toggle": 'Light / dark theme',
    "echeck": {'hero_link': 'Free e-invoicing check for Odoo – 2 minutes', 'title': 'E-invoicing check for Odoo', 'kicker': 'Free · 5 questions · 2 minutes', 'intro': "Is your Odoo ready for mandatory e-invoicing in Germany? Answer five short questions – you'll see right away where you stand and what to do.", 'privacy': 'Your answers stay in your browser. Nothing is stored or transmitted – unless you send me the result yourself.', 'answers': ['Yes', 'Partly', "No / don't know"], 'q': [('Receiving', 'Can you receive XRechnung and ZUGFeRD invoices and read the XML data – not just view the PDF?', 'Mandatory for all companies since 1 Jan 2025.', 'Set up intake: e-invoices via a mailbox or upload into Odoo, XML captured automatically as vendor bills.'), ('Sending', 'Does your Odoo create customer invoices as ZUGFeRD/Factur-X or XRechnung?', 'Mandatory from 1 Jan 2027 for prior-year turnover above €800,000, from 1 Jan 2028 for everyone (B2B).', 'Set the format per customer (ZUGFeRD for companies, XRechnung for authorities) and enable it in the invoice layout.'), ('Master data', 'Are VAT IDs, full addresses and – for authorities – Leitweg-ID or buyer reference maintained for your customers?', 'Missing mandatory fields are the most common reason for rejected e-invoices.', 'Review and clean master data; configure Odoo so gaps show up before an invoice goes out.'), ('Validation', 'Are your e-invoices validated against the standard before sending (e.g. with the KoSIT validator)?', 'A PDF that looks fine can still be an invalid e-invoice.', 'Validate test invoices and fix typical errors in Odoo (tax categories, units, rounding).'), ('Archive', 'Are incoming and outgoing e-invoices kept in their original XML in a GoBD-compliant way?', 'For e-invoices the XML is the original – not the PDF. Retention: 8 years.', 'Store XML attachments unalterably in Odoo, ensure backups and an export for tax audits.')], 'submit': 'Show result', 'need_all': 'Please answer all five questions.', 'score': 'Your result: {s} of 10 points', 'levels': [('Urgent action needed', "Your Odoo is not ready for e-invoicing yet. The good news: with the right setup it's done in a few days."), ('Good basis – with gaps', 'Some things already work, but the open points can lead to rejected invoices or trouble in a tax audit.'), ('Well prepared', 'Your Odoo is largely ready. A quick outside look is still worth it – for validation and archiving.')], 'todo': 'What to tackle:', 'cta_title': 'Free 30-minute audit', 'cta_text': "E-invoicing in Odoo is exactly my field. I'll review your system together with you – 30 minutes, free and without obligation. You get a clear list of what's missing and what it costs.", 'cta_book': 'Book a call – with result', 'cta_mail': 'Send result by e-mail', 'cta_tg': 'Send result via Telegram', 'copied': 'Result copied – just paste it into the Telegram chat.', 'mail_subject': 'E-invoicing check: {s}/10 – request for a free audit', 'mail_intro': 'Hello, here is my result from the e-invoicing check:', 'mail_outro': 'Odoo version:\nCompany:\nPreferred date:'},
    "bot_more_title": 'Dynamic reports, handy bots',
    "bot_more_intro": 'Instead of hunting through dashboards, ask the bot – the answer arrives in seconds, on your phone or at your desk.',
    "chat2": [{'caption': 'Who works in Odoo today? (example, names changed)', 'msgs': [{'who': 'me', 'html': '/users'}, {'who': 'bot', 'html': '<b>▒▒▒ PROD: users in the last 24 h</b><br>In the Odoo web client: 88<br>Online now: 37<br>Logins: 398 (47 users)<br>Active internal users: 147<br>Actions today (since 00:00), users: 74<pre>edits chatter\n  568      9  Taras Wendel\n  534     67  Oleh Brandt\n  499     54  Lukas Feld\n  495    115  Daria Moos\n  481     60  Sofia Kern</pre>Last action:<pre>🟢 13.11 16:43  Ivan Roth\n🟢 13.11 16:43  Marta Lind\n🟢 13.11 16:42  Olena Weiss\n🟢 13.11 16:41  Anna Berg\n🟢 13.11 16:40  Irina Falk</pre>'}]}, {'caption': 'The cause in plain words instead of 5,000 log lines (example).', 'msgs': [{'who': 'me', 'html': '/analyze shop.▒▒▒.de'}, {'who': 'bot', 'html': '🔎 <b>Analysis shop.▒▒▒.de</b> · 24 h<br>✅ HTTP 200 in 0.24 s · SSL until 14 Feb<br>CPU 31 % · RAM 62 % · Disk 71 %<br>Odoo log: ERROR 12 · WARNING 40<br>• SerializationFailure 9× – cron “Stock levels”<br>• nginx 502 3× at 03:12<br>🤖 <b>AI summary:</b> the 502 errors coincide with the nightly backup – all workers were busy. Recommendation: move the backup to 04:00, raise the cron time limit.', 'buttons': ['📋 Details', '🛠 Create ticket']}]}],
    "lb": {"close": 'Close', "zoom_in": 'Zoom in', "zoom_out": 'Zoom out', "full": 'Full screen'},
    "map": {'title': 'Projects in Germany, Switzerland and Ukraine', 'caption': 'Places where I have supported Odoo projects.', 'home': 'Stuttgart – my base', 'c': {'frankfurt': 'Frankfurt', 'berlin': 'Berlin', 'stuttgart': 'Stuttgart', 'ulm': 'Ulm', 'luzern': 'Lucerne', 'kyiv': 'Kyiv', 'poltava': 'Poltava', 'dnipro': 'Dnipro', 'odesa': 'Odesa', 'kherson': 'Kherson'}},
}

# пакеты часов (config.PACKS) – сравнение с Odoo Success Packs
T.update({'packs_title': 'Hour packs – cheaper than the Odoo Success Packs', 'packs_intro': 'Prepaid hours for analysis, design, development, integration, migration, performance and training – the same pack sizes as Odoo, at a lower price. Possible because routine work (backups, monitoring, test copies, updates) is automated on our side.', 'packs_head': ['Pack', 'Hours', 'Price', 'per hour', 'Odoo Success Pack¹'], 'packs_note': 'Valid for 12 months, billed in 15-minute steps, monthly overview of the remaining hours. No extra fee for maintaining your own modules. On-site visits: travel time and costs as incurred. ¹ Odoo S.A. list price for new customers (with 15% discount) according to odoo.com/pricing-packs, as of 19 Nov 2026; Odoo prices vary by country, plus VAT. Our prices: no VAT (§ 19 UStG, German small business).'})
