T = {
    "meta_title": "Odoo Support, Installation & Integration für DACH – Goldberg Odoo Services",
    "meta_desc": "Odoo-Betreuung für Unternehmen in Deutschland, Österreich und der Schweiz: Installation, Support, "
                 "Fehlerbehebung, Updates, DATEV, E-Rechnung (XRechnung/ZUGFeRD), Shopware, JTL, DHL, DPD. Festpreise, remote aus Stuttgart.",
    "nav": {"services": "Leistungen", "dach": "DATEV & E-Rechnung", "bot": "Monitoring", "prices": "Preise",
            "about": "Über mich", "contact": "Kontakt"},
    "kicker": "Odoo · Deutschland · Österreich · Schweiz",
    "h1": "Odoo-Betreuung, <span>die einfach läuft.</span>",
    "sub": "Installation, Support, Fehlerbehebung und Integrationen für Odoo Community und Enterprise – "
           "remote aus Stuttgart, mit Festpreisen und einem festen Ansprechpartner.",
    "cta_book": "Termin buchen – 30 Min. kostenlos",
    "badges": ["Festpreise statt Überraschungen", "Monitoring rund um die Uhr", "Updates ohne Ausfall",
               "Odoo 14 bis 19", "DSGVO-konform mit AV-Vertrag"],
    "hero_card": ["Odoo erreichbar", "Backup erfolgreich", "Festplatte – Warnung", "Fehler im Log heute",
                  "Ihr Server, rund um die Uhr im Blick"],
    "services_title": "Leistungen",
    "services_intro": "Vom ersten Server bis zur laufenden Betreuung – alles aus einer Hand, ohne Agentur-Overhead.",
    "services": [
        ("install", "Installation & Einrichtung",
         "Odoo auf Ihrem Server oder in der Cloud: Docker, PostgreSQL, SSL, Reverse-Proxy, E-Mail, automatische Backups. "
         "Sauber dokumentiert und an Sie übergeben."),
        ("support", "Support & Wartung",
         "Sicherheits-Updates, Backups mit Wiederherstellungstest, Überwachung, Benutzerfragen und kleine Anpassungen – "
         "monatlich planbar."),
        ("fix", "Fehlerbehebung",
         "Odoo startet nicht, ist langsam, das Update bricht ab, E-Mails gehen nicht raus? Schnelle Analyse der Logs, "
         "klare Ursache, nachhaltige Lösung."),
        ("update", "Updates & Migration",
         "Modul-Updates ohne Stillstand, Versionswechsel (z. B. 14 → 17) – immer zuerst auf einer Kopie getestet, "
         "mit Rückweg, falls etwas schiefgeht."),
        ("integration", "Integration",
         "DATEV, E-Rechnung, Online-Shops, Versanddienstleister, Banken und eigene Schnittstellen (REST, XML-RPC)."),
        ("server", "Server & DevOps",
         "Linux, Docker, nginx, PostgreSQL: Performance-Tuning, Absicherung (Ports, Zugänge, Zertifikate), "
         "Speicherplatz und Log-Rotation."),
    ],
    "dach_title": "Was Odoo in Deutschland, Österreich und der Schweiz können muss",
    "dach_intro": "Die Standard-Installation reicht hier selten. Diese Themen richte ich für Sie ein – und halte sie aktuell.",
    "dach": [
        ("Buchhaltung", "DATEV-Export für Ihren Steuerberater",
         "Buchungssätze und Belege aus Odoo im DATEV-Format – Ihre Kanzlei importiert sie direkt, ohne Abtippen.",
         ["Buchungsstapel (DATEV-Format, EXTF) und Belegbilder", "Kontenrahmen SKR03 / SKR04, Steuerschlüssel",
          "Abstimmung mit der Kanzlei, Testexport vor dem Monatsabschluss"]),
        ("Pflicht ab 2025", "E-Rechnung: XRechnung & ZUGFeRD",
         "Seit 1. 1. 2025 müssen Unternehmen in Deutschland E-Rechnungen empfangen können, ab 2027/2028 (je nach Umsatz) "
         "auch im B2B versenden. Odoo kann das – richtig eingerichtet.",
         ["ZUGFeRD / Factur-X (PDF mit XML) und XRechnung (UBL/CII)", "Leitweg-ID für Behörden, Prüfung mit Validator",
          "Empfang und automatische Erfassung eingehender E-Rechnungen"]),
        ("Handel", "E-Commerce & Logistik",
         "Bestellungen, Bestände und Versand automatisch zwischen Shop, Odoo und Paketdienst.",
         ["Shopware, JTL-Wawi, WooCommerce", "DHL, DPD, GLS: Etiketten und Sendungsverfolgung",
          "Abgleich von Preisen, Beständen und Rechnungen"]),
        ("AT · CH", "Österreich & Schweiz",
         "Lokale Anforderungen ohne Umwege.",
         ["Österreich: E-Rechnung an den Bund (ebInterface / PEPPOL)", "Schweiz: QR-Rechnung, MWST, CHF und EUR parallel",
          "Mehrsprachige Belege (DE / FR / EN)"]),
    ],
    "bot_title": "Monitoring-Bot: Ihr Odoo im Blick – direkt in Telegram",
    "bot_intro": "Zu jedem Supportvertrag gehört mein Monitoring-Bot. Er prüft Ihren Server laufend und meldet Probleme, "
                 "bevor Ihre Mitarbeiter sie bemerken. Auf Wunsch bekommen Sie den Bot auch selbst.",
    "bot_points": [
        ("Verfügbarkeit:", "Odoo, Datenbank, Webserver, SSL-Zertifikat, Speicherplatz."),
        ("Fehler:", "Odoo- und nginx-Logs zusammengefasst – nur das Wichtige, ohne Rauschen."),
        ("Hintergrundjobs:", "geplante Aktionen (Cron) und Warteschlangen, hängende Jobs."),
        ("Backups:", "jede Nacht – mit Kontrolle, dass sie wirklich wiederherstellbar sind."),
        ("Updates per Knopfdruck:", "Code holen → Module aktualisieren → Neustart, mit Rücksprung auf den vorherigen Stand."),
    ],
    "bot_note": "Beispieldaten – Namen und Adressen geschwärzt.",
    "bot_online": "Bot · online",
    "chat_caption": "So sieht der Bot im Alltag aus (Beispiel).",
    "chat": [
        {"who": "me", "html": "/status"},
        {"who": "bot", "html": "<b>PROD</b> · ▒▒▒▒▒.de<br>✅ Odoo aktiv, 200 OK in 0,21 s<br>✅ PostgreSQL · 2,4 GB<br>"
                               "⚠️ Festplatte 86 % (12 GB frei)<br>✅ SSL gültig bis 23.02.<br>✅ Backup 03:00 · 1,1 GB"},
        {"who": "me", "html": "/errors"},
        {"who": "bot", "html": "<b>Fehler heute: 2</b><br>• sale.order: Expected singleton (2×)<br>"
                               "<i>Serialisierungskonflikte ausgeblendet: 14</i>"},
        {"who": "me", "html": "/update"},
        {"who": "bot", "html": "<b>/update PROD</b> · ▒▒▒▒<br>Geänderte Module (3): sale_custom, stock_report, l10n_de_datev",
         "buttons": ["▶️ 3 Module aktualisieren", "Abbrechen"]},
        {"who": "bot", "html": "✅ Fertig in 1 min 40 s, 0 Fehler<br>Neustart von Odoo nötig, um neuen Code zu laden.",
         "buttons": ["🔄 Odoo neu starten"]},
    ],
    "process_title": "So arbeiten wir zusammen",
    "process": [
        ("Erstgespräch", "30 Minuten per Video oder Telegram – kostenlos. Sie schildern, wo es hakt."),
        ("Health-Check oder Angebot", "Ich prüfe Ihr System und nenne einen Festpreis oder ein passendes Paket."),
        ("Umsetzung", "Zuerst auf einer Testkopie, dann in Produktion – zu einem Zeitpunkt, der Ihnen passt."),
        ("Laufende Betreuung", "Monitoring, Updates und schnelle Hilfe – mit planbaren monatlichen Kosten."),
    ],
    "prices_title": "Preise",
    "prices_intro": "Transparent und planbar. Kleine Aufgaben nach Aufwand, Projekte zum Festpreis nach Health-Check.",
    "per_month": "/ Monat",
    "incl_hours": "{h} Std. Arbeit inklusive",
    "reaction": {"2": "Reaktion innerhalb von 2 Werktagen", "1": "Reaktion am nächsten Werktag",
                 "4h": "Reaktion in 4 Std. (Mo–Fr 9–18 Uhr)"},
    "plans": {
        "basic": {"name": "Basic", "desc": "Für kleine Teams, die Ruhe wollen.",
                  "features": ["Monitoring-Bot & nächtliche Backups", "Sicherheits-Updates", "Monatlicher Kurzbericht"]},
        "business": {"name": "Business", "desc": "Für Unternehmen, die täglich mit Odoo arbeiten.",
                     "features": ["Alles aus Basic", "Modul-Updates ohne Stillstand", "Wiederherstellungstest pro Quartal"]},
        "premium": {"name": "Premium", "desc": "Für geschäftskritische Systeme.",
                    "features": ["Alles aus Business", "Notfall-Hotline auch am Wochenende*", "Quartals-Review & Roadmap"]},
    },
    "plans_note": "Zusätzliche Stunden im Paket: 65 € / Std. Laufzeit monatlich kündbar. "
                  "* Wochenend-Einsätze werden mit 95 € / Std. berechnet.",
    "table_title": "Einzelleistungen",
    "table_head": ["Leistung", "Preis"],
    "units": {"h": "/ Std.", "fix": "Festpreis", "from": "ab"},
    "price_names": {
        "hourly_support": ("Support & Wartung", "Anpassungen, Benutzerfragen, geplante Arbeiten – im 15-Minuten-Takt"),
        "hourly_urgent": ("Dringend, Wochenende, Troubleshooting", "Störung, Ausfall, Fehlersuche unter Zeitdruck"),
        "healthcheck": ("Odoo Health-Check", "Server, Backups, Module, Performance, Sicherheit – mit schriftlichem Bericht und Maßnahmenplan"),
        "diagnosis": ("Erstdiagnose einer Störung", "bis 2 Std. Fehlersuche, danach nach Aufwand (95 € / Std.)"),
        "install": ("Installation & Einrichtung", "Odoo + PostgreSQL in Docker, SSL, Backups, E-Mail, Monitoring"),
        "module_update": ("Modul-Update mit Rücksprung", "git pull, Update auf Testkopie, Update in Produktion"),
        "migration": ("Versions-Migration", "z. B. Odoo 14 → 17, inkl. Testlauf auf Kopie"),
        "datev": ("DATEV-Export", "Einrichtung, Kontenzuordnung, Testexport mit Ihrer Kanzlei"),
        "einvoice": ("E-Rechnung (XRechnung / ZUGFeRD)", "Versand und Empfang, Validierung, Leitweg-ID"),
        "shop": ("Shop-Anbindung", "Shopware, JTL-Wawi, WooCommerce"),
        "shipping": ("Versand-Anbindung", "DHL, DPD, GLS – Etiketten, Tracking"),
        "qrbill": ("Schweizer QR-Rechnung", "QR-IBAN, Referenzen, MWST"),
        "monitoring": ('Grafana & Prometheus einrichten', 'Exporter für Server, PostgreSQL, Docker, nginx; Dashboards und Alarme'),
        "bot": ("Monitoring-Bot für Ihr Team", "eigene Instanz, Einrichtung für Ihren Server"),
    },
    "vat_note": "Alle Preise in EUR. Gemäß § 19 UStG (Kleinunternehmerregelung) wird keine Umsatzsteuer berechnet. Abrechnung monatlich nach Aufwand im 15-Minuten-Takt bzw. zum vereinbarten Festpreis.",
    "kleinunternehmer": "Kleinunternehmer gemäß § 19 UStG – es wird keine Umsatzsteuer berechnet.",
    "cases_title": "Typische Fälle zum Festpreis",
    "cases": [
        ("„Odoo ist nach dem Server-Update down“",
         "Erstdiagnose, Ursache (z. B. Python-Paket, Datenbank, Proxy), Behebung und kurzer Bericht, wie es nicht wieder passiert.",
         "meist 190 € + 1–2 Std. × 95 €"),
        ("„Wir brauchen E-Rechnungen bis Jahresende“",
         "ZUGFeRD/XRechnung einrichten, Stammdaten prüfen, Testrechnungen validieren, Team einweisen.",
         "ab 900 € Festpreis"),
        ("„Unser Odoo läuft – aber niemand kümmert sich“",
         "Health-Check, danach Monitoring, Backups und Updates im Business-Paket.",
         "490 € einmalig + 690 € / Monat"),
    ],
    "about_title": "Über mich",
    "about": [
        "Ich bin DevOps-Engineer und arbeite seit vielen Jahren mit Odoo – von der Installation über eigene Module bis zum "
        "Betrieb mehrerer Produktivsysteme mit Hunderten von Modulen.",
        "Ich betreue Odoo für Unternehmen aus Handel, Logistik, Dienstleistung und Callcenter: Server, Updates, "
        "Integrationen und Überwachung. Ich lebe in Stuttgart und arbeite remote für Kunden in ganz DACH – "
        "Termine vor Ort in der Region Stuttgart nach Absprache.",
        "Bei mir haben Sie einen festen Ansprechpartner, der Ihr System kennt – keine Ticket-Warteschlange, keine Weiterleitung.",
    ],
    "about_facts": ["Odoo 14 – 19, Community & Enterprise", "Linux · Docker · PostgreSQL · nginx",
                    "Python, OWL, XML-RPC / REST", "Git-basierte Deployments mit Rollback",
                    "Kommunikation: Deutsch, Englisch, Ukrainisch, Russisch"],
    "faq_title": "Häufige Fragen",
    "faq": [
        ("Community oder Enterprise?", "Beides. Ich helfe auch bei der Entscheidung – oft reicht Community mit gezielten OCA-Modulen."),
        ("Arbeiten Sie nur remote?", "Ja, über SSH bzw. VPN – sicher und ohne Anfahrtskosten. In der Region Stuttgart auch vor Ort."),
        ("Wie ist der Zugriff auf unsere Daten geregelt?",
         "Mit einem Auftragsverarbeitungsvertrag (AVV) nach DSGVO. Zugänge nur so weit wie nötig, auf Wunsch zeitlich begrenzt."),
        ("Was, wenn ein Update schiefgeht?",
         "Updates laufen zuerst auf einer Kopie. In Produktion wird der vorherige Code-Stand gesichert – ein Rücksprung dauert Minuten."),
        ("Wir haben schon einen Odoo-Partner.",
         "Kein Problem – ich übernehme gern Betrieb, Server und Monitoring, während Ihr Partner die Fachprozesse betreut."),
        ("Wie wird abgerechnet?", "Monatlich nach Aufwand im 15-Minuten-Takt oder zum vereinbarten Festpreis, per Überweisung."),
    ],
    "contact_title": "Lassen Sie uns sprechen",
    "contact_text": "Schreiben Sie kurz, welche Odoo-Version Sie nutzen und wo es hakt – ich melde mich in der Regel am selben Werktag.",
    "contact_note": "Kein Kontaktformular, keine Cookies – einfach Telegram, E-Mail oder Termin.",
    "footer_tag": "Odoo-Support, Installation und Integration für Deutschland, Österreich und die Schweiz.",
    "footer_note": "Diese Website verwendet keine Cookies und kein Tracking.",
    "impressum": "Impressum",
    "privacy": "Datenschutz",
    "legal_note": "",
    "impressum_page": {
        "title": "Impressum",
        "html": """
<h2>Angaben gemäß § 5 DDG</h2>
<p>{name}<br>{street}<br>{city}<br>{country}</p>
<h2>Kontakt</h2>
<p>E-Mail: <a href="mailto:{email}">{email}</a><br>Telegram: {telegram}</p>
<h2>Umsatzsteuer</h2>
<p>{vat}</p>
<h2>Verantwortlich für den Inhalt nach § 18 Abs. 2 MStV</h2>
<p>{name}, Anschrift wie oben</p>
<h2>Verbraucherstreitbeilegung</h2>
<p>Ich bin nicht bereit und nicht verpflichtet, an Streitbeilegungsverfahren vor einer Verbraucherschlichtungsstelle teilzunehmen.
Meine Leistungen richten sich an Unternehmen.</p>
<h2>Haftung für Links</h2>
<p>Diese Website enthält Links zu externen Websites Dritter (z. B. Telegram, Cal.com), auf deren Inhalte ich keinen Einfluss habe.
Für diese Inhalte ist der jeweilige Anbieter verantwortlich.</p>
""",
    },
    "privacy_page": {
        "title": "Datenschutzerklärung",
        "html": """
<h2>1. Verantwortlicher</h2>
<p>{name}, {street}, {city}, {country}<br>E-Mail: <a href="mailto:{email}">{email}</a></p>
<h2>2. Kurz gesagt</h2>
<p>Diese Website setzt <b>keine Cookies</b>, verwendet <b>kein Tracking</b>, keine Analyse-Tools, keine Werbe-Pixel,
keine eingebetteten Inhalte Dritter und keine extern geladenen Schriften. Es gibt kein Kontaktformular.
Auch der lokale Speicher Ihres Browsers (Local Storage) wird nicht verwendet.</p>
<h2>3. Hosting und Server-Logfiles</h2>
<p>Die Website wird über Cloudflare Pages bereitgestellt (Cloudflare, Inc., 101 Townsend St, San Francisco, CA 94107, USA).
Beim Aufruf verarbeitet Cloudflare technisch notwendige Daten (IP-Adresse, Datum und Uhrzeit, aufgerufene Seite, Browsertyp),
um die Seite auszuliefern und vor Angriffen zu schützen. Rechtsgrundlage ist Art. 6 Abs. 1 lit. f DSGVO
(berechtigtes Interesse an einem sicheren, stabilen Betrieb). Cloudflare ist nach dem EU-US Data Privacy Framework zertifiziert;
es besteht ein Vertrag zur Auftragsverarbeitung mit Standardvertragsklauseln. Ich selbst werte diese Daten nicht aus.</p>
<h2>4. Kontakt per E-Mail oder Telegram</h2>
<p>Wenn Sie mir schreiben, verarbeite ich Ihre Angaben (Name, Kontaktdaten, Inhalt der Nachricht), um Ihre Anfrage zu beantworten
(Art. 6 Abs. 1 lit. b DSGVO – vorvertragliche Maßnahmen, sonst lit. f). Die Daten werden gelöscht, sobald die Anfrage erledigt ist
und keine gesetzlichen Aufbewahrungspflichten bestehen.
E-Mails laufen über Google Gmail (Google Ireland Ltd., Dublin). Telegram wird von Telegram Messenger Inc. (Dubai, VAE) betrieben;
die Nutzung ist freiwillig und unterliegt den Datenschutzbestimmungen von Telegram – alternativ können Sie jederzeit per E-Mail schreiben.</p>
<h2>5. Terminbuchung (Cal.com)</h2>
<p>Der Button „Termin buchen“ führt zu Cal.com (Cal.com, Inc., USA). Erst wenn Sie dort einen Termin buchen, werden Ihre Angaben
(Name, E-Mail, gewünschter Termin) von Cal.com verarbeitet. Es gelten die Datenschutzbestimmungen von Cal.com.
Rechtsgrundlage: Art. 6 Abs. 1 lit. b DSGVO.</p>
<h2>6. Ihre Rechte</h2>
<p>Sie haben das Recht auf Auskunft (Art. 15), Berichtigung (Art. 16), Löschung (Art. 17), Einschränkung der Verarbeitung (Art. 18),
Datenübertragbarkeit (Art. 20) und Widerspruch (Art. 21 DSGVO). Eine formlose E-Mail genügt.</p>
<h2>7. Beschwerderecht</h2>
<p>Sie können sich bei einer Datenschutz-Aufsichtsbehörde beschweren, z. B. beim Landesbeauftragten für den Datenschutz und die
Informationsfreiheit Baden-Württemberg, Lautenschlagerstraße 20, 70173 Stuttgart.</p>
<h2>8. Auftragsverarbeitung für Kunden</h2>
<p>Wenn ich im Rahmen der Odoo-Betreuung Zugriff auf personenbezogene Daten Ihres Unternehmens erhalte, schließen wir dafür
einen gesonderten Vertrag zur Auftragsverarbeitung (Art. 28 DSGVO).</p>
<p class="small">Stand: November 2026</p>
""",
    },
    "mon_title": 'Monitoring mit Grafana & Prometheus',
    "mon_intro": 'Wenn Telegram-Meldungen nicht reichen: Dashboards mit Verlauf, Kennzahlen und Alarmen für Ihr Odoo – auf Ihrem eigenen Server, Ihre Daten bleiben bei Ihnen.',
    "mon": [
        ('node_exporter', 'Server', 'CPU, Arbeitsspeicher, Festplatten, Netzwerk und Last – mit Verlauf über Wochen.'),
        ('postgres_exporter', 'PostgreSQL', 'Verbindungen, langsame Abfragen, Sperren, Datenbankgröße, Replikation.'),
        ('cAdvisor', 'Docker', 'Ressourcen je Container: Odoo, Worker, Datenbank, Hilfsdienste.'),
        ('blackbox · nginx', 'Erreichbarkeit', 'Antwortzeiten von außen, HTTP-Fehler, Ablauf der SSL-Zertifikate.'),
        ('Odoo · Loki', 'Anwendung', 'Worker, Cron-Laufzeiten, Warteschlangen (queue_job) und Fehler aus den Logs.'),
        ('Alertmanager', 'Alarme', 'Meldungen per Telegram oder E-Mail – mit Schwellen, die zu Ihrem Betrieb passen.'),
    ],
    "mon_note": 'Läuft parallel zum Monitoring-Bot oder eigenständig. Einrichtung zum Festpreis, Betreuung im Supportpaket.',
    "slides_title": 'Beispiele aus Projekten',
    "slides_intro": 'Ausschnitte aus echten Umsetzungen – Kundendaten unkenntlich gemacht.',
    "slide_alt": 'Beispiel {n}',
    "slides_prev": 'Vorheriges Beispiel',
    "slides_next": 'Nächstes Beispiel',
    "slides_goto": 'Beispiel {n} anzeigen',
}
