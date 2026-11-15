# Статья 11: Odoo 17 бесплатно – где запустить, база, filestore (R2), Cloudflare Tunnel/Access/R2. Все 6 языков внутри.

FREE = {
    "slug": "odoo-17-free-hosting-database-filestore",
    "date": "2026-11-15",
    "tags": ["Odoo 17", "Hosting", "Oracle Cloud", "Cloudflare", "R2", "PostgreSQL"],
    "code": {
        "compose": ("docker-compose.yml · amd64 + arm64", """services:
  db:
    image: postgres:16
    environment:
      POSTGRES_USER: odoo
      POSTGRES_PASSWORD: change-me
      POSTGRES_DB: postgres
    volumes: [db:/var/lib/postgresql/data]
    restart: unless-stopped
  odoo:
    image: odoo:17
    depends_on: [db]
    environment:
      HOST: db
      USER: odoo
      PASSWORD: change-me
    ports: ["127.0.0.1:8069:8069"]      # only local – the tunnel or nginx is the way in
    volumes:
      - filestore:/var/lib/odoo
      - ./extra-addons:/mnt/extra-addons
    restart: unless-stopped
volumes: {db: {}, filestore: {}}"""),
        "tunnel": ("bash · Cloudflare Tunnel", """# Zero Trust → Networks → Tunnels → Create a tunnel (cloudflared)
# → choose OS/arch → copy the install command with your token:
sudo cloudflared service install <TOKEN>

# same dialog → Public hostname:
#   odoo.example.com  →  Service: HTTP  localhost:8069

# odoo.conf – Odoo sits behind a proxy now:
proxy_mode = True"""),
        "fs": ("Odoo · FS Storage (OCA fs_storage + fs_attachment)", """pip install fsspec s3fs        # in the Odoo image / venv

# Settings → Technical → FS Storage → New
#   Protocol:       s3
#   Directory path: <bucket>/odoo-attachments
#   Options:
{
  "endpoint_url": "https://<ACCOUNT_ID>.r2.cloudflarestorage.com",
  "key": "<R2 Access Key ID>",
  "secret": "<R2 Secret Access Key>",
  "client_kwargs": {"region_name": "auto"}
}
#   [x] Use as default for attachments"""),
        "backup": ("sh · /etc/cron.daily/odoo-r2", """#!/bin/sh
# rclone remote "r2" (rclone config → provider: Cloudflare R2)
set -e
D=$(date +%F)
cd /opt/odoo
docker compose exec -T db pg_dump -U odoo -Fc mydb > /tmp/mydb-$D.dump
rclone copy /tmp/mydb-$D.dump r2:backups/db/ && rm /tmp/mydb-$D.dump
# filestore volume: docker volume inspect odoo_filestore → Mountpoint
rclone sync /var/lib/docker/volumes/odoo_filestore/_data/filestore/mydb r2:backups/filestore/mydb"""),
    },
    "links": [
        ("Oracle Cloud Free Tier – Always Free resources", "https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm"),
        ("Google Cloud – free tier (e2-micro)", "https://cloud.google.com/free/docs/free-cloud-features"),
        ("Odoo pricing – One App Free", "https://www.odoo.com/pricing"),
        ("OCA/storage – fs_storage, fs_attachment", "https://github.com/OCA/storage"),
        ("Cloudflare R2 pricing", "https://developers.cloudflare.com/r2/pricing/"),
        ("Cloudflare Tunnel", "https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/"),
        ("Neon – free plan", "https://neon.com/pricing"),
        ("Supabase – free plan", "https://supabase.com/pricing"),
        ("Blog: Odoo with docker compose, extra-addons and nginx", "@blog:odoo-docker-compose-extra-addons-nginx"),
        ("Blog: Cloudflare Access step by step", "@blog:cloudflare-access-zero-trust-step-by-step"),
        ("Blog: protect the Odoo database manager", "@blog:nginx-apache-password-protect-odoo-database-manager"),
    ],
    "t": {},
}

FREE["t"]["de"] = {
    "title": "Odoo 17 kostenlos betreiben: Server, Datenbank, Filestore – alle Optionen mit ihren Haken",
    "summary": "Wo läuft Odoo 17 gratis, warum die Datenbank nicht in die Cloudflare-Cloud gehört, wie der Filestore in R2 landet und wie Cloudflare Tunnel, Access und R2 das Ganze absichern.",
    "body": [
        ("p", "„Kann ich Odoo kostenlos laufen lassen – und Datenbank und Dateien gleich bei Cloudflare ablegen?“ Die kurze Antwort: **Server ja, Dateien ja, Datenbank nein.** Hier alle Varianten mit ihren Eigenheiten."),
        ("note", "Kurzfassung: Odoo + PostgreSQL zusammen in docker compose auf **Oracle Cloud Always Free** (ARM, bis 24 GB RAM). Erreichbar über **Cloudflare Tunnel**, Datenbank-Manager hinter **Cloudflare Access**, Backups und optional der Filestore in **Cloudflare R2**."),
        ("h", "Was Odoo braucht"),
        ("ul", [
            "**Python-Anwendung** (odoo-bin) – realistisch ab 2 GB RAM, für einen Test reicht 1 GB mit Swap.",
            "**PostgreSQL** – nah an Odoo, am besten auf demselben Server.",
            "**Filestore** – Anhänge, Bilder, Assets. Standard: Verzeichnis auf der Platte (`/var/lib/odoo/filestore/<db>`).",
        ]),
        ("h", "Wo Odoo gratis laufen kann"),
        ("table", [
            ["Variante", "Ressourcen", "Für Odoo?", "Haken"],
            ["**Oracle Cloud Always Free** (Ampere A1, ARM)", "bis 4 vCPU, 24 GB RAM, 200 GB Disk, 10 TB Traffic/Monat", "**ja** – auch kleiner Produktivbetrieb", "Kreditkarte zur Prüfung; ARM-Instanzen in beliebten Regionen oft „Out of capacity“; untätige Instanzen kann Oracle zurückfordern; kein SLA"],
            ["Google Cloud e2-micro", "0,25–2 vCPU, 1 GB RAM, 30 GB Disk, nur US-Regionen", "nur Test mit Swap", "1 GB RAM ist knapp; 1 GB ausgehender Traffic/Monat frei"],
            ["AWS Free Plan", "Guthaben (bis 200 $) für 6 Monate", "zeitlich begrenzt", "danach kostenpflichtig"],
            ["Render u. ä. PaaS (Free)", "~512 MB RAM", "nein", "schläft bei Inaktivität, kein dauerhafter Speicher"],
            ["Odoo Online „One App Free“", "SaaS von Odoo", "nur Standard", "eine App, keine eigenen Module, kein Serverzugang"],
            ["Eigene Hardware (alter PC, Raspberry Pi 5 / 8 GB)", "was da ist", "ja", "Strom, Internetanschluss, eigene Backups; mit Tunnel ohne offene Ports"],
            ["Zum Vergleich: Hetzner CAX11", "2 vCPU ARM, 4 GB RAM, 40 GB", "ja", "kein Gratis-Angebot, aber ca. 4–5 €/Monat und planbar"],
        ]),
        ("note", "Oracle-Tipps: Region bei der Registrierung bewusst wählen (nicht änderbar), bei „Out of capacity“ später erneut oder eine kleinere Form (z. B. 2 vCPU / 12 GB) probieren. Die offiziellen Images `odoo:17` und `postgres:16` gibt es auch für arm64."),
        ("code", "compose"),
        ("h", "Datenbank: warum nicht bei Cloudflare"),
        ("p", "Odoo spricht nur **PostgreSQL**. Cloudflare bietet kein gehostetes PostgreSQL: **D1** ist SQLite, **Hyperdrive** ist ein Verbindungs-Pool für Workers zu einer externen Datenbank – beides hilft Odoo nicht."),
        ("p", "Externe Gratis-Datenbanken gibt es, aber Odoo schickt pro Seitenaufruf Hunderte kleine Abfragen. Bei 20–50 ms Latenz zu einem anderen Rechenzentrum werden daraus Sekunden pro Klick."),
        ("table", [
            ["Option", "Gratis-Umfang", "Für Odoo?"],
            ["Cloudflare D1", "SQLite", "nein – kein PostgreSQL"],
            ["Cloudflare Hyperdrive", "Pool für Workers", "nein – keine Datenbank"],
            ["Neon Free", "0,5 GB, schläft nach Inaktivität", "nur Spielerei; Latenz, Kaltstart"],
            ["Supabase Free", "500 MB, pausiert nach 1 Woche Inaktivität", "nur Spielerei; Latenz"],
            ["**PostgreSQL im selben docker compose**", "so viel wie der Server hat", "**ja**"],
        ]),
        ("h", "Filestore: drei Wege zu R2"),
        ("ol", [
            "**OCA `fs_storage` + `fs_attachment`** (Repository OCA/storage, Zweig 17.0): Anhänge werden direkt im R2-Bucket gespeichert (über fsspec/s3fs). Der Server-Speicher wächst nicht, Dateien überleben einen Server-Verlust. Pro Anhang ein Aufruf zu R2 – kleine Dateien und Assets kann man in der Datenbank oder lokal lassen; das Modul kann das pro Dateityp steuern.",
            "**R2 als Verzeichnis einhängen** (rclone mount, s3fs-fuse): funktioniert, ist aber langsam und beim Schreiben empfindlich. Für Produktion nicht zu empfehlen.",
            "**Filestore lokal, Backup nach R2** – am einfachsten und robust: täglich `pg_dump` und `rclone sync` in den Bucket. 10 GB in R2 sind gratis, Download (Egress) kostet nie etwas.",
        ]),
        ("code", "fs"),
        ("code", "backup"),
        ("note", "Die Wiederherstellung immer auch testen: Dump auf einem Stage-System einspielen, Filestore zurückkopieren, Cron-Jobs vorher stoppen."),
        ("h", "Cloudflare davor"),
        ("ul", [
            "**Cloudflare Tunnel** (gratis): `cloudflared` baut die Verbindung von innen auf – keine offenen Ports, keine öffentliche IP nötig. Funktioniert auch für den Odoo-Websocket (`/websocket`).",
            "**Cloudflare Access**: `/web/database/*` oder das ganze Testsystem nur für bestimmte E-Mail-Adressen.",
            "**R2**: Backups und Filestore, S3-kompatibel (aws cli, rclone).",
            "In `odoo.conf` `proxy_mode = True` setzen, sonst sieht Odoo die falsche IP und das falsche Schema.",
        ]),
        ("code", "tunnel"),
        ("h", "Empfehlung"),
        ("ul", [
            "**Test / Demo / Schulung:** Oracle Always Free oder eigene Hardware + Tunnel + Access.",
            "**Kleiner Produktivbetrieb gratis:** Oracle Always Free, aber mit täglichem Backup nach R2 und getesteter Wiederherstellung – ein Gratis-Konto hat kein SLA.",
            "**Produktiv ohne Überraschungen:** kleiner VPS für 4–5 €/Monat, Backups nach R2.",
            "**Nur Standard-Apps, keine eigenen Module:** Odoo Online „One App Free“.",
        ]),
        ("links", "Links"),
    ],
}

FREE["t"]["en"] = {
    "title": "Running Odoo 17 for free: server, database, filestore – every option and its catch",
    "summary": "Where Odoo 17 runs for free, why the database does not belong in Cloudflare, how the filestore ends up in R2, and how Cloudflare Tunnel, Access and R2 secure the setup.",
    "body": [
        ("p", "“Can I run Odoo for free – and keep the database and files at Cloudflare?” Short answer: **server yes, files yes, database no.** Here are all the options and their quirks."),
        ("note", "TL;DR: Odoo + PostgreSQL together in docker compose on **Oracle Cloud Always Free** (ARM, up to 24 GB RAM). Reachable via **Cloudflare Tunnel**, database manager behind **Cloudflare Access**, backups and optionally the filestore in **Cloudflare R2**."),
        ("h", "What Odoo needs"),
        ("ul", [
            "**A Python application** (odoo-bin) – realistically 2 GB RAM or more; 1 GB with swap is enough for a test.",
            "**PostgreSQL** – close to Odoo, ideally on the same server.",
            "**A filestore** – attachments, images, assets. Default: a directory on disk (`/var/lib/odoo/filestore/<db>`).",
        ]),
        ("h", "Where Odoo can run for free"),
        ("table", [
            ["Option", "Resources", "For Odoo?", "Catch"],
            ["**Oracle Cloud Always Free** (Ampere A1, ARM)", "up to 4 vCPU, 24 GB RAM, 200 GB disk, 10 TB traffic/month", "**yes** – even small production", "credit card for verification; ARM capacity often “out of capacity” in popular regions; Oracle may reclaim idle instances; no SLA"],
            ["Google Cloud e2-micro", "0.25–2 vCPU, 1 GB RAM, 30 GB disk, US regions only", "test only, with swap", "1 GB RAM is tight; 1 GB egress/month free"],
            ["AWS Free Plan", "credits (up to $200) for 6 months", "temporary", "paid afterwards"],
            ["Render & similar PaaS (free)", "~512 MB RAM", "no", "sleeps when idle, no persistent disk"],
            ["Odoo Online “One App Free”", "SaaS by Odoo", "standard only", "one app, no custom modules, no server access"],
            ["Own hardware (old PC, Raspberry Pi 5 / 8 GB)", "whatever you have", "yes", "power, internet line, your own backups; no open ports with a tunnel"],
            ["For comparison: Hetzner CAX11", "2 vCPU ARM, 4 GB RAM, 40 GB", "yes", "not free, but about €4–5/month and predictable"],
        ]),
        ("note", "Oracle tips: pick the home region carefully at sign-up (it cannot be changed); on “out of capacity” retry later or try a smaller shape (e.g. 2 vCPU / 12 GB). The official `odoo:17` and `postgres:16` images exist for arm64 too."),
        ("code", "compose"),
        ("h", "Database: why not at Cloudflare"),
        ("p", "Odoo only speaks **PostgreSQL**. Cloudflare has no hosted PostgreSQL: **D1** is SQLite, **Hyperdrive** is a connection pool for Workers to an external database – neither helps Odoo."),
        ("p", "Free external databases exist, but Odoo sends hundreds of small queries per page. With 20–50 ms latency to another data centre that adds up to seconds per click."),
        ("table", [
            ["Option", "Free tier", "For Odoo?"],
            ["Cloudflare D1", "SQLite", "no – not PostgreSQL"],
            ["Cloudflare Hyperdrive", "pool for Workers", "no – not a database"],
            ["Neon Free", "0.5 GB, sleeps when idle", "toy only; latency, cold start"],
            ["Supabase Free", "500 MB, paused after 1 week of inactivity", "toy only; latency"],
            ["**PostgreSQL in the same docker compose**", "as much as the server has", "**yes**"],
        ]),
        ("h", "Filestore: three ways to R2"),
        ("ol", [
            "**OCA `fs_storage` + `fs_attachment`** (repository OCA/storage, branch 17.0): attachments are stored directly in the R2 bucket (via fsspec/s3fs). The server disk does not grow, files survive losing the server. Each attachment is a call to R2 – small files and assets can stay in the database or on disk; the module can control this per file type.",
            "**Mount R2 as a directory** (rclone mount, s3fs-fuse): works, but slow and fragile on writes. Not recommended for production.",
            "**Filestore on disk, backup to R2** – simplest and robust: a daily `pg_dump` and `rclone sync` to the bucket. 10 GB in R2 are free, downloads (egress) never cost anything.",
        ]),
        ("code", "fs"),
        ("code", "backup"),
        ("note", "Always test the restore too: load the dump on a stage system, copy the filestore back, stop cron jobs first."),
        ("h", "Cloudflare in front"),
        ("ul", [
            "**Cloudflare Tunnel** (free): `cloudflared` connects from the inside – no open ports, no public IP needed. Works for the Odoo websocket (`/websocket`) too.",
            "**Cloudflare Access**: `/web/database/*` or the whole test system only for selected e-mail addresses.",
            "**R2**: backups and filestore, S3-compatible (aws cli, rclone).",
            "Set `proxy_mode = True` in `odoo.conf`, otherwise Odoo sees the wrong IP and scheme.",
        ]),
        ("code", "tunnel"),
        ("h", "Recommendation"),
        ("ul", [
            "**Test / demo / training:** Oracle Always Free or own hardware + Tunnel + Access.",
            "**Small production for free:** Oracle Always Free, but with daily backups to R2 and a tested restore – a free account has no SLA.",
            "**Production without surprises:** a small VPS for €4–5/month, backups to R2.",
            "**Standard apps only, no custom modules:** Odoo Online “One App Free”.",
        ]),
        ("links", "Links"),
    ],
}

FREE["t"]["fr"] = {
    "title": "Faire tourner Odoo 17 gratuitement : serveur, base de données, filestore – toutes les options et leurs pièges",
    "summary": "Où Odoo 17 tourne gratuitement, pourquoi la base de données n’a pas sa place chez Cloudflare, comment le filestore va dans R2, et comment Cloudflare Tunnel, Access et R2 sécurisent l’ensemble.",
    "body": [
        ("p", "« Puis-je faire tourner Odoo gratuitement – et mettre la base et les fichiers chez Cloudflare ? » Réponse courte : **serveur oui, fichiers oui, base de données non.** Voici toutes les options et leurs particularités."),
        ("note", "En bref : Odoo + PostgreSQL ensemble dans docker compose sur **Oracle Cloud Always Free** (ARM, jusqu’à 24 Go de RAM). Accès via **Cloudflare Tunnel**, gestionnaire de bases derrière **Cloudflare Access**, sauvegardes et éventuellement le filestore dans **Cloudflare R2**."),
        ("h", "Ce dont Odoo a besoin"),
        ("ul", [
            "**Une application Python** (odoo-bin) – en pratique 2 Go de RAM ou plus ; 1 Go avec swap suffit pour un test.",
            "**PostgreSQL** – proche d’Odoo, idéalement sur le même serveur.",
            "**Un filestore** – pièces jointes, images, assets. Par défaut : un répertoire sur disque (`/var/lib/odoo/filestore/<db>`).",
        ]),
        ("h", "Où Odoo peut tourner gratuitement"),
        ("table", [
            ["Option", "Ressources", "Pour Odoo ?", "Piège"],
            ["**Oracle Cloud Always Free** (Ampere A1, ARM)", "jusqu’à 4 vCPU, 24 Go RAM, 200 Go disque, 10 To de trafic/mois", "**oui** – même une petite production", "carte bancaire pour vérification ; ARM souvent « out of capacity » dans les régions populaires ; Oracle peut récupérer les instances inactives ; pas de SLA"],
            ["Google Cloud e2-micro", "0,25–2 vCPU, 1 Go RAM, 30 Go disque, régions US uniquement", "test seulement, avec swap", "1 Go de RAM c’est juste ; 1 Go de trafic sortant/mois gratuit"],
            ["AWS Free Plan", "crédits (jusqu’à 200 $) pendant 6 mois", "temporaire", "payant ensuite"],
            ["Render & autres PaaS (gratuit)", "~512 Mo RAM", "non", "s’endort en cas d’inactivité, pas de disque persistant"],
            ["Odoo Online « One App Free »", "SaaS d’Odoo", "standard uniquement", "une seule app, pas de modules personnalisés, pas d’accès serveur"],
            ["Matériel personnel (vieux PC, Raspberry Pi 5 / 8 Go)", "ce que vous avez", "oui", "électricité, connexion, vos propres sauvegardes ; aucun port ouvert avec un tunnel"],
            ["À titre de comparaison : Hetzner CAX11", "2 vCPU ARM, 4 Go RAM, 40 Go", "oui", "pas gratuit, mais env. 4–5 €/mois et prévisible"],
        ]),
        ("note", "Astuces Oracle : choisir la région avec soin à l’inscription (non modifiable) ; en cas de « out of capacity », réessayer plus tard ou prendre une forme plus petite (p. ex. 2 vCPU / 12 Go). Les images officielles `odoo:17` et `postgres:16` existent aussi en arm64."),
        ("code", "compose"),
        ("h", "Base de données : pourquoi pas chez Cloudflare"),
        ("p", "Odoo ne parle que **PostgreSQL**. Cloudflare ne propose pas de PostgreSQL hébergé : **D1** est du SQLite, **Hyperdrive** est un pool de connexions pour Workers vers une base externe – aucun des deux n’aide Odoo."),
        ("p", "Des bases externes gratuites existent, mais Odoo envoie des centaines de petites requêtes par page. Avec 20–50 ms de latence vers un autre centre de données, cela fait des secondes par clic."),
        ("table", [
            ["Option", "Offre gratuite", "Pour Odoo ?"],
            ["Cloudflare D1", "SQLite", "non – pas PostgreSQL"],
            ["Cloudflare Hyperdrive", "pool pour Workers", "non – pas une base"],
            ["Neon Free", "0,5 Go, s’endort en cas d’inactivité", "pour jouer ; latence, démarrage à froid"],
            ["Supabase Free", "500 Mo, mis en pause après 1 semaine d’inactivité", "pour jouer ; latence"],
            ["**PostgreSQL dans le même docker compose**", "autant que le serveur", "**oui**"],
        ]),
        ("h", "Filestore : trois chemins vers R2"),
        ("ol", [
            "**OCA `fs_storage` + `fs_attachment`** (dépôt OCA/storage, branche 17.0) : les pièces jointes sont stockées directement dans le bucket R2 (via fsspec/s3fs). Le disque du serveur ne grossit pas, les fichiers survivent à la perte du serveur. Chaque pièce jointe = un appel à R2 – les petits fichiers et assets peuvent rester en base ou sur disque ; le module le règle par type de fichier.",
            "**Monter R2 comme répertoire** (rclone mount, s3fs-fuse) : fonctionne, mais lent et fragile en écriture. Déconseillé en production.",
            "**Filestore sur disque, sauvegarde vers R2** – le plus simple et robuste : `pg_dump` et `rclone sync` quotidiens vers le bucket. 10 Go dans R2 sont gratuits, le téléchargement (egress) ne coûte jamais rien.",
        ]),
        ("code", "fs"),
        ("code", "backup"),
        ("note", "Testez toujours aussi la restauration : charger le dump sur un système de stage, recopier le filestore, arrêter les tâches cron avant."),
        ("h", "Cloudflare devant"),
        ("ul", [
            "**Cloudflare Tunnel** (gratuit) : `cloudflared` se connecte depuis l’intérieur – aucun port ouvert, pas besoin d’IP publique. Fonctionne aussi pour le websocket d’Odoo (`/websocket`).",
            "**Cloudflare Access** : `/web/database/*` ou tout le système de test réservé à certaines adresses e-mail.",
            "**R2** : sauvegardes et filestore, compatible S3 (aws cli, rclone).",
            "Mettre `proxy_mode = True` dans `odoo.conf`, sinon Odoo voit la mauvaise IP et le mauvais schéma.",
        ]),
        ("code", "tunnel"),
        ("h", "Recommandation"),
        ("ul", [
            "**Test / démo / formation :** Oracle Always Free ou matériel personnel + Tunnel + Access.",
            "**Petite production gratuite :** Oracle Always Free, mais avec sauvegarde quotidienne vers R2 et restauration testée – un compte gratuit n’a pas de SLA.",
            "**Production sans surprise :** un petit VPS à 4–5 €/mois, sauvegardes vers R2.",
            "**Apps standard uniquement, sans modules personnalisés :** Odoo Online « One App Free ».",
        ]),
        ("links", "Liens"),
    ],
}

FREE["t"]["el"] = {
    "title": "Odoo 17 δωρεάν: server, βάση δεδομένων, filestore – όλες οι επιλογές και οι παγίδες τους",
    "summary": "Πού τρέχει δωρεάν το Odoo 17, γιατί η βάση δεν ανήκει στο Cloudflare, πώς το filestore πηγαίνει στο R2 και πώς τα Cloudflare Tunnel, Access και R2 ασφαλίζουν το σύνολο.",
    "body": [
        ("p", "«Μπορώ να τρέξω το Odoo δωρεάν – και να βάλω βάση και αρχεία στο Cloudflare;» Σύντομη απάντηση: **server ναι, αρχεία ναι, βάση όχι.** Ακολουθούν όλες οι επιλογές με τις ιδιαιτερότητές τους."),
        ("note", "Με λίγα λόγια: Odoo + PostgreSQL μαζί σε docker compose στο **Oracle Cloud Always Free** (ARM, έως 24 GB RAM). Πρόσβαση μέσω **Cloudflare Tunnel**, ο διαχειριστής βάσεων πίσω από **Cloudflare Access**, αντίγραφα ασφαλείας και προαιρετικά το filestore στο **Cloudflare R2**."),
        ("h", "Τι χρειάζεται το Odoo"),
        ("ul", [
            "**Μια εφαρμογή Python** (odoo-bin) – ρεαλιστικά 2 GB RAM και πάνω· για δοκιμή αρκεί 1 GB με swap.",
            "**PostgreSQL** – κοντά στο Odoo, ιδανικά στον ίδιο server.",
            "**Ένα filestore** – συνημμένα, εικόνες, assets. Προεπιλογή: φάκελος στον δίσκο (`/var/lib/odoo/filestore/<db>`).",
        ]),
        ("h", "Πού μπορεί να τρέξει δωρεάν"),
        ("table", [
            ["Επιλογή", "Πόροι", "Για Odoo;", "Παγίδα"],
            ["**Oracle Cloud Always Free** (Ampere A1, ARM)", "έως 4 vCPU, 24 GB RAM, 200 GB δίσκος, 10 TB κίνηση/μήνα", "**ναι** – ακόμη και μικρή παραγωγή", "κάρτα για επαλήθευση· ARM συχνά «out of capacity» σε δημοφιλείς περιοχές· η Oracle μπορεί να ανακτήσει αδρανή instances· χωρίς SLA"],
            ["Google Cloud e2-micro", "0,25–2 vCPU, 1 GB RAM, 30 GB δίσκος, μόνο περιοχές ΗΠΑ", "μόνο δοκιμή, με swap", "1 GB RAM είναι λίγο· 1 GB εξερχόμενη κίνηση/μήνα δωρεάν"],
            ["AWS Free Plan", "πίστωση (έως 200 $) για 6 μήνες", "προσωρινά", "μετά επί πληρωμή"],
            ["Render & παρόμοια PaaS (δωρεάν)", "~512 MB RAM", "όχι", "«κοιμάται» όταν δεν χρησιμοποιείται, χωρίς μόνιμο δίσκο"],
            ["Odoo Online «One App Free»", "SaaS της Odoo", "μόνο τα βασικά", "μία εφαρμογή, χωρίς δικά σας modules, χωρίς πρόσβαση στον server"],
            ["Δικό σας hardware (παλιός PC, Raspberry Pi 5 / 8 GB)", "ό,τι έχετε", "ναι", "ρεύμα, σύνδεση, δικά σας backups· με tunnel χωρίς ανοιχτές θύρες"],
            ["Για σύγκριση: Hetzner CAX11", "2 vCPU ARM, 4 GB RAM, 40 GB", "ναι", "όχι δωρεάν, αλλά περίπου 4–5 €/μήνα και προβλέψιμο"],
        ]),
        ("note", "Συμβουλές για Oracle: επιλέξτε προσεκτικά την περιοχή κατά την εγγραφή (δεν αλλάζει)· σε «out of capacity» δοκιμάστε αργότερα ή μικρότερο μέγεθος (π.χ. 2 vCPU / 12 GB). Οι επίσημες εικόνες `odoo:17` και `postgres:16` υπάρχουν και για arm64."),
        ("code", "compose"),
        ("h", "Βάση δεδομένων: γιατί όχι στο Cloudflare"),
        ("p", "Το Odoo μιλά μόνο **PostgreSQL**. Το Cloudflare δεν προσφέρει φιλοξενούμενη PostgreSQL: το **D1** είναι SQLite, το **Hyperdrive** είναι pool συνδέσεων για Workers προς εξωτερική βάση – κανένα δεν βοηθά το Odoo."),
        ("p", "Υπάρχουν δωρεάν εξωτερικές βάσεις, αλλά το Odoo στέλνει εκατοντάδες μικρά ερωτήματα ανά σελίδα. Με 20–50 ms καθυστέρηση προς άλλο data center, αυτό γίνεται δευτερόλεπτα ανά κλικ."),
        ("table", [
            ["Επιλογή", "Δωρεάν όριο", "Για Odoo;"],
            ["Cloudflare D1", "SQLite", "όχι – δεν είναι PostgreSQL"],
            ["Cloudflare Hyperdrive", "pool για Workers", "όχι – δεν είναι βάση"],
            ["Neon Free", "0,5 GB, «κοιμάται» όταν δεν χρησιμοποιείται", "μόνο για παιχνίδι· καθυστέρηση, cold start"],
            ["Supabase Free", "500 MB, παύση μετά από 1 εβδομάδα αδράνειας", "μόνο για παιχνίδι· καθυστέρηση"],
            ["**PostgreSQL στο ίδιο docker compose**", "όσο έχει ο server", "**ναι**"],
        ]),
        ("h", "Filestore: τρεις δρόμοι προς το R2"),
        ("ol", [
            "**OCA `fs_storage` + `fs_attachment`** (αποθετήριο OCA/storage, κλάδος 17.0): τα συνημμένα αποθηκεύονται απευθείας στο bucket του R2 (μέσω fsspec/s3fs). Ο δίσκος του server δεν μεγαλώνει, τα αρχεία επιβιώνουν αν χαθεί ο server. Κάθε συνημμένο είναι μία κλήση στο R2 – μικρά αρχεία και assets μπορούν να μείνουν στη βάση ή στον δίσκο· το module το ρυθμίζει ανά τύπο αρχείου.",
            "**Προσάρτηση του R2 ως φακέλου** (rclone mount, s3fs-fuse): δουλεύει, αλλά είναι αργό και ευαίσθητο στις εγγραφές. Δεν συνιστάται για παραγωγή.",
            "**Filestore στον δίσκο, backup στο R2** – το πιο απλό και αξιόπιστο: καθημερινά `pg_dump` και `rclone sync` στο bucket. Τα 10 GB στο R2 είναι δωρεάν, η λήψη (egress) δεν χρεώνεται ποτέ.",
        ]),
        ("code", "fs"),
        ("code", "backup"),
        ("note", "Δοκιμάζετε πάντα και την επαναφορά: φόρτωση του dump σε σύστημα stage, επιστροφή του filestore, πρώτα διακοπή των cron jobs."),
        ("h", "Το Cloudflare μπροστά"),
        ("ul", [
            "**Cloudflare Tunnel** (δωρεάν): το `cloudflared` συνδέεται από μέσα – χωρίς ανοιχτές θύρες, χωρίς δημόσια IP. Δουλεύει και για το websocket του Odoo (`/websocket`).",
            "**Cloudflare Access**: `/web/database/*` ή ολόκληρο το δοκιμαστικό σύστημα μόνο για συγκεκριμένα e-mail.",
            "**R2**: backups και filestore, συμβατό με S3 (aws cli, rclone).",
            "Ορίστε `proxy_mode = True` στο `odoo.conf`, αλλιώς το Odoo βλέπει λάθος IP και σχήμα.",
        ]),
        ("code", "tunnel"),
        ("h", "Πρόταση"),
        ("ul", [
            "**Δοκιμή / demo / εκπαίδευση:** Oracle Always Free ή δικό σας hardware + Tunnel + Access.",
            "**Μικρή παραγωγή δωρεάν:** Oracle Always Free, αλλά με καθημερινό backup στο R2 και δοκιμασμένη επαναφορά – ο δωρεάν λογαριασμός δεν έχει SLA.",
            "**Παραγωγή χωρίς εκπλήξεις:** μικρός VPS για 4–5 €/μήνα, backups στο R2.",
            "**Μόνο βασικές εφαρμογές, χωρίς δικά σας modules:** Odoo Online «One App Free».",
        ]),
        ("links", "Σύνδεσμοι"),
    ],
}

FREE["t"]["uk"] = {
    "title": "Odoo 17 безкоштовно: сервер, база даних, filestore – усі варіанти та їхні підводні камені",
    "summary": "Де Odoo 17 працює безкоштовно, чому базі даних не місце в Cloudflare, як filestore потрапляє в R2 і як Cloudflare Tunnel, Access та R2 захищають усю конструкцію.",
    "body": [
        ("p", "«Чи можна запустити Odoo безкоштовно – і тримати базу та файли в Cloudflare?» Коротка відповідь: **сервер – так, файли – так, база – ні.** Нижче всі варіанти з їхніми особливостями."),
        ("note", "Коротко: Odoo + PostgreSQL разом у docker compose на **Oracle Cloud Always Free** (ARM, до 24 ГБ RAM). Доступ через **Cloudflare Tunnel**, менеджер баз за **Cloudflare Access**, бекапи та за бажання filestore – у **Cloudflare R2**."),
        ("h", "Що потрібно Odoo"),
        ("ul", [
            "**Python-застосунок** (odoo-bin) – реалістично від 2 ГБ RAM; для тесту вистачить 1 ГБ зі swap.",
            "**PostgreSQL** – поруч з Odoo, найкраще на тому ж сервері.",
            "**Filestore** – вкладення, зображення, assets. За замовчуванням – каталог на диску (`/var/lib/odoo/filestore/<db>`).",
        ]),
        ("h", "Де Odoo може працювати безкоштовно"),
        ("table", [
            ["Варіант", "Ресурси", "Для Odoo?", "Нюанси"],
            ["**Oracle Cloud Always Free** (Ampere A1, ARM)", "до 4 vCPU, 24 ГБ RAM, 200 ГБ диска, 10 ТБ трафіку/міс.", "**так** – навіть невеликий прод", "картка для перевірки; ARM у популярних регіонах часто «Out of capacity»; простоюючі інстанси Oracle може забрати; без SLA"],
            ["Google Cloud e2-micro", "0,25–2 vCPU, 1 ГБ RAM, 30 ГБ диска, лише регіони США", "лише тест зі swap", "1 ГБ RAM замало; 1 ГБ вихідного трафіку/міс. безкоштовно"],
            ["AWS Free Plan", "кредити (до 200 $) на 6 місяців", "тимчасово", "потім платно"],
            ["Render та подібні PaaS (free)", "~512 МБ RAM", "ні", "засинає без активності, немає постійного диска"],
            ["Odoo Online «One App Free»", "SaaS від Odoo", "лише стандарт", "один застосунок, без власних модулів, без доступу до сервера"],
            ["Власне залізо (старий ПК, Raspberry Pi 5 / 8 ГБ)", "що є", "так", "електрика, інтернет, власні бекапи; з тунелем без відкритих портів"],
            ["Для порівняння: Hetzner CAX11", "2 vCPU ARM, 4 ГБ RAM, 40 ГБ", "так", "не безкоштовно, але ≈ 4–5 €/міс. і передбачувано"],
        ]),
        ("note", "Поради щодо Oracle: регіон обирайте уважно під час реєстрації (змінити не можна); при «Out of capacity» повторіть пізніше або візьміть меншу конфігурацію (напр. 2 vCPU / 12 ГБ). Офіційні образи `odoo:17` і `postgres:16` є і для arm64."),
        ("code", "compose"),
        ("h", "База даних: чому не в Cloudflare"),
        ("p", "Odoo працює лише з **PostgreSQL**. Хостингу PostgreSQL у Cloudflare немає: **D1** – це SQLite, **Hyperdrive** – пул з'єднань для Workers до зовнішньої бази. Odoo не допомагає ні те, ні інше."),
        ("p", "Безкоштовні зовнішні бази існують, але Odoo робить сотні дрібних запитів на кожну сторінку. За затримки 20–50 мс до іншого дата-центру це перетворюється на секунди на кожен клік."),
        ("table", [
            ["Варіант", "Безкоштовно", "Для Odoo?"],
            ["Cloudflare D1", "SQLite", "ні – не PostgreSQL"],
            ["Cloudflare Hyperdrive", "пул для Workers", "ні – не база"],
            ["Neon Free", "0,5 ГБ, засинає без активності", "лише погратися; затримка, холодний старт"],
            ["Supabase Free", "500 МБ, пауза після тижня без активності", "лише погратися; затримка"],
            ["**PostgreSQL у тому ж docker compose**", "скільки має сервер", "**так**"],
        ]),
        ("h", "Filestore: три шляхи до R2"),
        ("ol", [
            "**OCA `fs_storage` + `fs_attachment`** (репозиторій OCA/storage, гілка 17.0): вкладення зберігаються одразу в бакеті R2 (через fsspec/s3fs). Диск сервера не росте, файли переживуть втрату сервера. Кожне вкладення – запит до R2; дрібні файли й assets можна лишити в базі або на диску, модуль налаштовує це за типом файлу.",
            "**Змонтувати R2 як каталог** (rclone mount, s3fs-fuse): працює, але повільно й нестабільно на запис. Для продакшену не раджу.",
            "**Filestore на диску, бекап у R2** – найпростіше й надійно: щодня `pg_dump` і `rclone sync` у бакет. 10 ГБ у R2 безкоштовні, завантаження (egress) не коштує нічого.",
        ]),
        ("code", "fs"),
        ("code", "backup"),
        ("note", "Обов'язково перевіряйте й відновлення: залийте дамп на stage, поверніть filestore, а перед тим зупиніть cron-завдання."),
        ("h", "Cloudflare попереду"),
        ("ul", [
            "**Cloudflare Tunnel** (безкоштовно): `cloudflared` підключається зсередини – жодних відкритих портів і публічної IP. Працює й для websocket Odoo (`/websocket`).",
            "**Cloudflare Access**: `/web/database/*` або вся тестова система – лише для вибраних e-mail.",
            "**R2**: бекапи й filestore, сумісний з S3 (aws cli, rclone).",
            "В `odoo.conf` поставте `proxy_mode = True`, інакше Odoo бачить неправильні IP і схему.",
        ]),
        ("code", "tunnel"),
        ("h", "Рекомендація"),
        ("ul", [
            "**Тест / демо / навчання:** Oracle Always Free або власне залізо + Tunnel + Access.",
            "**Невеликий прод безкоштовно:** Oracle Always Free, але з щоденним бекапом у R2 і перевіреним відновленням – безкоштовний акаунт не має SLA.",
            "**Прод без сюрпризів:** невеликий VPS за 4–5 €/міс., бекапи в R2.",
            "**Лише стандартні застосунки, без своїх модулів:** Odoo Online «One App Free».",
        ]),
        ("links", "Посилання"),
    ],
}

FREE["t"]["ru"] = {
    "title": "Odoo 17 бесплатно: сервер, база данных, filestore – все варианты и их подводные камни",
    "summary": "Где Odoo 17 работает бесплатно, почему базе данных не место в Cloudflare, как filestore попадает в R2 и как Cloudflare Tunnel, Access и R2 защищают всю конструкцию.",
    "body": [
        ("p", "«Можно ли запустить Odoo бесплатно – и держать базу и файлы в Cloudflare?» Короткий ответ: **сервер – да, файлы – да, база – нет.** Ниже все варианты с их особенностями."),
        ("note", "Коротко: Odoo + PostgreSQL вместе в docker compose на **Oracle Cloud Always Free** (ARM, до 24 ГБ RAM). Доступ через **Cloudflare Tunnel**, менеджер баз за **Cloudflare Access**, бэкапы и при желании filestore – в **Cloudflare R2**."),
        ("h", "Что нужно Odoo"),
        ("ul", [
            "**Python-приложение** (odoo-bin) – реалистично от 2 ГБ RAM; для теста хватит 1 ГБ со swap.",
            "**PostgreSQL** – рядом с Odoo, лучше всего на том же сервере.",
            "**Filestore** – вложения, картинки, assets. По умолчанию – каталог на диске (`/var/lib/odoo/filestore/<db>`).",
        ]),
        ("h", "Где Odoo может работать бесплатно"),
        ("table", [
            ["Вариант", "Ресурсы", "Для Odoo?", "Нюансы"],
            ["**Oracle Cloud Always Free** (Ampere A1, ARM)", "до 4 vCPU, 24 ГБ RAM, 200 ГБ диска, 10 ТБ трафика/мес.", "**да** – даже небольшой прод", "карта для проверки; ARM в популярных регионах часто «Out of capacity»; простаивающие инстансы Oracle может забрать; без SLA"],
            ["Google Cloud e2-micro", "0,25–2 vCPU, 1 ГБ RAM, 30 ГБ диска, только регионы США", "только тест со swap", "1 ГБ RAM мало; 1 ГБ исходящего трафика/мес. бесплатно"],
            ["AWS Free Plan", "кредиты (до 200 $) на 6 месяцев", "временно", "потом платно"],
            ["Render и подобные PaaS (free)", "~512 МБ RAM", "нет", "засыпает без активности, нет постоянного диска"],
            ["Odoo Online «One App Free»", "SaaS от Odoo", "только стандарт", "одно приложение, без своих модулей, без доступа к серверу"],
            ["Своё железо (старый ПК, Raspberry Pi 5 / 8 ГБ)", "что есть", "да", "электричество, интернет, свои бэкапы; с туннелем без открытых портов"],
            ["Для сравнения: Hetzner CAX11", "2 vCPU ARM, 4 ГБ RAM, 40 ГБ", "да", "не бесплатно, но ≈ 4–5 €/мес. и предсказуемо"],
        ]),
        ("note", "Советы по Oracle: регион выбирайте внимательно при регистрации (сменить нельзя); при «Out of capacity» повторите позже или возьмите конфигурацию поменьше (напр. 2 vCPU / 12 ГБ). Официальные образы `odoo:17` и `postgres:16` есть и для arm64."),
        ("code", "compose"),
        ("h", "База данных: почему не в Cloudflare"),
        ("p", "Odoo работает только с **PostgreSQL**. Хостинга PostgreSQL у Cloudflare нет: **D1** – это SQLite, **Hyperdrive** – пул соединений для Workers к внешней базе. Odoo не помогает ни то, ни другое."),
        ("p", "Бесплатные внешние базы существуют, но Odoo делает сотни мелких запросов на каждую страницу. При задержке 20–50 мс до другого дата-центра это превращается в секунды на каждый клик."),
        ("table", [
            ["Вариант", "Бесплатно", "Для Odoo?"],
            ["Cloudflare D1", "SQLite", "нет – не PostgreSQL"],
            ["Cloudflare Hyperdrive", "пул для Workers", "нет – не база"],
            ["Neon Free", "0,5 ГБ, засыпает без активности", "только поиграться; задержка, холодный старт"],
            ["Supabase Free", "500 МБ, пауза после недели без активности", "только поиграться; задержка"],
            ["**PostgreSQL в том же docker compose**", "сколько есть у сервера", "**да**"],
        ]),
        ("h", "Filestore: три пути в R2"),
        ("ol", [
            "**OCA `fs_storage` + `fs_attachment`** (репозиторий OCA/storage, ветка 17.0): вложения сохраняются сразу в бакет R2 (через fsspec/s3fs). Диск сервера не растёт, файлы переживут потерю сервера. Каждое вложение – запрос в R2; мелкие файлы и assets можно оставить в базе или на диске, модуль настраивает это по типу файла.",
            "**Смонтировать R2 как каталог** (rclone mount, s3fs-fuse): работает, но медленно и нестабильно на запись. Для продакшена не советую.",
            "**Filestore на диске, бэкап в R2** – проще всего и надёжно: ежедневно `pg_dump` и `rclone sync` в бакет. 10 ГБ в R2 бесплатны, скачивание (egress) не стоит ничего.",
        ]),
        ("code", "fs"),
        ("code", "backup"),
        ("note", "Обязательно проверяйте и восстановление: залейте дамп на stage, верните filestore, а перед этим остановите cron-задачи."),
        ("h", "Cloudflare впереди"),
        ("ul", [
            "**Cloudflare Tunnel** (бесплатно): `cloudflared` подключается изнутри – никаких открытых портов и публичного IP. Работает и для websocket Odoo (`/websocket`).",
            "**Cloudflare Access**: `/web/database/*` или вся тестовая система – только для выбранных e-mail.",
            "**R2**: бэкапы и filestore, совместим с S3 (aws cli, rclone).",
            "В `odoo.conf` поставьте `proxy_mode = True`, иначе Odoo видит неправильные IP и схему.",
        ]),
        ("code", "tunnel"),
        ("h", "Рекомендация"),
        ("ul", [
            "**Тест / демо / обучение:** Oracle Always Free или своё железо + Tunnel + Access.",
            "**Небольшой прод бесплатно:** Oracle Always Free, но с ежедневным бэкапом в R2 и проверенным восстановлением – у бесплатного аккаунта нет SLA.",
            "**Прод без сюрпризов:** небольшой VPS за 4–5 €/мес., бэкапы в R2.",
            "**Только стандартные приложения, без своих модулей:** Odoo Online «One App Free».",
        ]),
        ("links", "Ссылки"),
    ],
}
