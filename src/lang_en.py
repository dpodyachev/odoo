T = {
    "meta_title": "Odoo Support, Installation & Integration for DACH – Goldberg Odoo Services",
    "meta_desc": "Odoo services for companies in Germany, Austria and Switzerland: installation, support, troubleshooting, "
                 "updates, DATEV, e-invoicing (XRechnung/ZUGFeRD), Shopware, JTL, DHL, DPD. Fixed prices, remote from Stuttgart.",
    "nav": {"services": "Services", "dach": "DATEV & e-invoicing", "bot": "Monitoring", "prices": "Pricing",
            "about": "About", "contact": "Contact"},
    "kicker": "Odoo · Germany · Austria · Switzerland",
    "h1": "Odoo support <span>that just works.</span>",
    "sub": "Installation, support, troubleshooting and integrations for Odoo Community and Enterprise – "
           "remote from Stuttgart, with fixed prices and one dedicated contact.",
    "cta_book": "Book a call – 30 min free",
    "badges": ["Fixed prices, no surprises", "24/7 monitoring", "Updates without downtime", "Odoo 14 to 19",
               "GDPR-compliant with a DPA"],
    "hero_card": ["Odoo reachable", "Backup successful", "Disk – warning", "Errors in log today",
                  "Your server, watched around the clock"],
    "services_title": "Services",
    "services_intro": "From the first server to ongoing operations – one person, no agency overhead.",
    "services": [
        ("install", "Installation & setup",
         "Odoo on your server or in the cloud: Docker, PostgreSQL, SSL, reverse proxy, e-mail, automatic backups. "
         "Cleanly documented and handed over to you."),
        ("support", "Support & maintenance",
         "Security updates, backups with restore tests, monitoring, user questions and small changes – predictable every month."),
        ("fix", "Troubleshooting",
         "Odoo won't start, is slow, an update fails, e-mails don't go out? Fast log analysis, a clear root cause, a lasting fix."),
        ("update", "Updates & migration",
         "Module updates without downtime, version upgrades (e.g. 14 → 17) – always tested on a copy first, "
         "with a way back if something goes wrong."),
        ("integration", "Integration",
         "DATEV, e-invoicing, online shops, carriers, banks and custom interfaces (REST, XML-RPC)."),
        ("server", "Servers & DevOps",
         "Linux, Docker, nginx, PostgreSQL: performance tuning, hardening (ports, access, certificates), disk space and log rotation."),
    ],
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
        ('Go-live & support', 'Phased start in production, then monitoring, updates and support.'),
    ],
    "yearly": 'Paid annually: {p} / year – 2 months free',
    "bot_title": "Monitoring bot: your Odoo at a glance – right in Telegram",
    "bot_intro": "Every support plan includes my monitoring bot. It checks your server continuously and reports problems "
                 "before your team notices them. You can also get the bot for yourself.",
    "bot_points": [
        ("Availability:", "Odoo, database, web server, SSL certificate, disk space."),
        ("Errors:", "Odoo and nginx logs summarised – only what matters, no noise."),
        ("Background jobs:", "scheduled actions (cron) and queues, stuck jobs."),
        ("Backups:", "every night – with checks that they can really be restored."),
        ("Updates at the push of a button:", "pull code → update modules → restart, with rollback to the previous state."),
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
        ("Ongoing care", "Monitoring, updates and fast help – with predictable monthly costs."),
    ],
    "prices_title": "Pricing",
    "prices_intro": "Transparent and predictable. Small tasks billed by time, projects at a fixed price after a health check.",
    "per_month": "/ month",
    "incl_hours": "{h} hours of work included",
    "reaction": {"2": "Response within 2 business days", "1": "Response next business day",
                 "4h": "Response within 4 h (Mon–Fri 9–18)"},
    "plans": {
        "basic": {"name": "Basic", "desc": "For small teams who want peace of mind.",
                  "features": ["Monitoring bot & nightly backups", "Security updates", "Short monthly report"]},
        "business": {"name": "Business", "desc": "For companies that work in Odoo every day.",
                     "features": ["Everything in Basic", "Module updates without downtime", "Quarterly restore test"]},
        "premium": {"name": "Premium", "desc": "For business-critical systems.",
                    "features": ["Everything in Business", "Emergency line on weekends too*", "Quarterly review & roadmap"]},
    },
    "plans_note": "Extra hours within a plan: €65 / h. Cancel monthly. * Weekend work is billed at €95 / h.",
    "table_title": "Individual services",
    "table_head": ["Service", "Price"],
    "units": {"h": "/ hour", "fix": "fixed price", "from": "from"},
    "price_names": {
        "hourly_support": ("Support & maintenance", "changes, user questions, planned work – billed in 15-minute steps"),
        "hourly_urgent": ("Urgent, weekend, troubleshooting", "incidents, outages, debugging under time pressure"),
        "healthcheck": ("Odoo health check", "server, backups, modules, performance, security – written report with action plan"),
        "diagnosis": ("Initial incident diagnosis", "up to 2 h of debugging, then billed by time (€95 / h)"),
        "install": ("Installation & setup", "Odoo + PostgreSQL in Docker, SSL, backups, e-mail, monitoring"),
        "module_update": ("Module update with rollback", "git pull, update on a test copy, update in production"),
        "migration": ("Version migration", "e.g. Odoo 14 → 17, including a test run on a copy"),
        "datev": ("DATEV export", "setup, account mapping, test export with your tax office"),
        "einvoice": ("E-invoicing (XRechnung / ZUGFeRD)", "sending and receiving, validation, Leitweg-ID"),
        "shop": ("Shop integration", "Shopware, JTL-Wawi, WooCommerce"),
        "shipping": ("Carrier integration", "DHL, DPD, GLS – labels, tracking"),
        "qrbill": ("Swiss QR-bill", "QR-IBAN, references, VAT"),
        "monitoring": ('Grafana & Prometheus setup', 'Exporters for server, PostgreSQL, Docker, nginx; dashboards and alerts'),
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
        ("“Our Odoo runs – but nobody looks after it”",
         "Health check, then monitoring, backups and updates in the Business plan.",
         "€490 once + €690 / month"),
    ],
    "about_title": "About me",
    "about": [
        "I'm a DevOps engineer and have worked with Odoo for many years – from installation and custom modules to running "
        "several production systems with hundreds of modules.",
        "I look after Odoo for companies in trade, logistics, services and call centers: servers, updates, integrations and "
        "monitoring. I live in Stuttgart and work remotely for clients across the DACH region – on-site visits in the "
        "Stuttgart area by arrangement.",
        "You get one dedicated contact who knows your system – no ticket queue, no hand-offs.",
    ],
    "about_facts": ["Odoo 14 – 19, Community & Enterprise", "Linux · Docker · PostgreSQL · nginx",
                    "Python, OWL, XML-RPC / REST", "Git-based deployments with rollback",
                    "Languages: German, English, Greek, Ukrainian, Russian"],
    "faq_title": "FAQ",
    "faq": [
        ("Community or Enterprise?", "Both. I'll also help you decide – Community with selected OCA modules is often enough."),
        ("Do you only work remotely?", "Yes, via SSH or VPN – secure and with no travel costs. On-site in the Stuttgart area too."),
        ("How is access to our data handled?",
         "With a data processing agreement (DPA) under the GDPR. Access only as far as needed, time-limited on request."),
        ("What if an update goes wrong?",
         "Updates run on a copy first. In production the previous code state is saved – rolling back takes minutes."),
        ("We already have an Odoo partner.",
         "No problem – I'm happy to take care of operations, servers and monitoring while your partner handles business processes."),
        ("How do you bill?", "Monthly by time in 15-minute steps or at the agreed fixed price, by bank transfer."),
    ],
    "contact_title": "Let's talk",
    "contact_text": "Tell me briefly which Odoo version you use and where it hurts – I usually reply the same business day.",
    "contact_note": "No contact form, no cookies – just Telegram, e-mail or a call.",
    "footer_tag": "Odoo support, installation and integration for Germany, Austria and Switzerland.",
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
<p>E-mail: <a href="mailto:{email}">{email}</a><br>Telegram: {telegram}</p>
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
<p>{name}, {street}, {city}, {country}<br>E-mail: <a href="mailto:{email}">{email}</a></p>
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
    "mon_note": 'Runs alongside the monitoring bot or on its own. Setup at a fixed price, operation within a support plan.',
    "slides_title": 'Examples from projects',
    "slides_intro": 'Excerpts from real implementations – customer data made unrecognisable.',
    "slide_alt": 'Example {n}',
    "slides_prev": 'Previous example',
    "slides_next": 'Next example',
    "slides_goto": 'Show example {n}',
    "theme_toggle": 'Light / dark theme',
    "echeck": {'hero_link': 'Free e-invoicing check for Odoo – 2 minutes', 'title': 'E-invoicing check for Odoo', 'kicker': 'Free · 5 questions · 2 minutes', 'intro': "Is your Odoo ready for mandatory e-invoicing in Germany? Answer five short questions – you'll see right away where you stand and what to do.", 'privacy': 'Your answers stay in your browser. Nothing is stored or transmitted – unless you send me the result yourself.', 'answers': ['Yes', 'Partly', "No / don't know"], 'q': [('Receiving', 'Can you receive XRechnung and ZUGFeRD invoices and read the XML data – not just view the PDF?', 'Mandatory for all companies since 1 Jan 2025.', 'Set up intake: e-invoices via a mailbox or upload into Odoo, XML captured automatically as vendor bills.'), ('Sending', 'Does your Odoo create customer invoices as ZUGFeRD/Factur-X or XRechnung?', 'Mandatory from 1 Jan 2027 for prior-year turnover above €800,000, from 1 Jan 2028 for everyone (B2B).', 'Set the format per customer (ZUGFeRD for companies, XRechnung for authorities) and enable it in the invoice layout.'), ('Master data', 'Are VAT IDs, full addresses and – for authorities – Leitweg-ID or buyer reference maintained for your customers?', 'Missing mandatory fields are the most common reason for rejected e-invoices.', 'Review and clean master data; configure Odoo so gaps show up before an invoice goes out.'), ('Validation', 'Are your e-invoices validated against the standard before sending (e.g. with the KoSIT validator)?', 'A PDF that looks fine can still be an invalid e-invoice.', 'Validate test invoices and fix typical errors in Odoo (tax categories, units, rounding).'), ('Archive', 'Are incoming and outgoing e-invoices kept in their original XML in a GoBD-compliant way?', 'For e-invoices the XML is the original – not the PDF. Retention: 8 years.', 'Store XML attachments unalterably in Odoo, ensure backups and an export for tax audits.')], 'submit': 'Show result', 'need_all': 'Please answer all five questions.', 'score': 'Your result: {s} of 10 points', 'levels': [('Urgent action needed', "Your Odoo is not ready for e-invoicing yet. The good news: with the right setup it's done in a few days."), ('Good basis – with gaps', 'Some things already work, but the open points can lead to rejected invoices or trouble in a tax audit.'), ('Well prepared', 'Your Odoo is largely ready. A quick outside look is still worth it – for validation and archiving.')], 'todo': 'What to tackle:', 'cta_title': 'Free 30-minute audit', 'cta_text': "E-invoicing in Odoo is exactly my field. I'll review your system together with you – 30 minutes, free and without obligation. You get a clear list of what's missing and what it costs.", 'cta_book': 'Book a call – with result', 'cta_mail': 'Send result by e-mail', 'cta_tg': 'Send result via Telegram', 'copied': 'Result copied – just paste it into the Telegram chat.', 'mail_subject': 'E-invoicing check: {s}/10 – request for a free audit', 'mail_intro': 'Hello, here is my result from the e-invoicing check:', 'mail_outro': 'Odoo version:\nCompany:\nPreferred date:'},
}
