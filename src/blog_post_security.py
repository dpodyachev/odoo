# Статья 19: безопасность сервера Odoo – секреты и персональные данные в URL и логах, ротация паролей и ключей,
# закрытые порты (Docker обходит ufw), шифрование трафика между серверами (в т.ч. от «своего» админа). Все 6 языков.

SECURITY = {
    "slug": "odoo-server-security-logs-secrets-ports-encryption",
    "date": "2026-11-16",
    "tags": ["Security", "Odoo", "nginx", "PostgreSQL", "TLS", "GDPR"],
    "code": {
        "find": ("bash · do your logs contain secrets or personal data?", """# tokens / passwords in query strings (nginx in Docker: docker logs <nginx-container>)
grep -cE '[?&](auth|token|key|api_key|password|passwd|secret)=' /var/log/nginx/access.log
# phone numbers in URLs
grep -cE '[?&](phone|phone_number|mobile|tel)=' /var/log/nginx/access.log
# who can read the logs?
ls -l /var/log/nginx/ /var/log/odoo/ ; sudo find / -xdev -name '*.log' -perm -o=r 2>/dev/null | head
# pm2 / node integrations often log full requests
grep -rlE 'password|Authorization|Bearer' ~/.pm2/logs/ 2>/dev/null"""),
        "nginx": ("nginx · log the path, not the query string", """# http { ... }
log_format noquery '$remote_addr - [$time_local] "$request_method $uri $server_protocol" '
                   '$status $body_bytes_sent $request_time "$http_user_agent"';
access_log /var/log/nginx/access.log noquery;

# only for one integration location – or no access log at all there
location /integration/ {
    access_log /var/log/nginx/integration.log noquery;
    proxy_pass http://odoo;
}

# logrotate: keep 14 days, not forever  (/etc/logrotate.d/nginx: rotate 14, daily, compress)
# Docker: json-file log driver with max-size / max-file, otherwise the log grows endlessly"""),
        "header": ("the token belongs in a header", """# bad: ends up in access logs, proxies, browser history, Referer headers, monitoring
GET /integration/call?auth=SECRET&phone=4917…

# good: header (not logged by default) + data in the POST body
curl -X POST https://erp.example.com/integration/call \\
     -H "Authorization: Bearer $INTEGRATION_TOKEN" \\
     -H "Content-Type: application/json" \\
     -d '{"call_id": "…", "status": "CALL_START"}'
# and only over HTTPS – also inside the data centre"""),
        "rotate": ("bash / sql · rotating secrets without drama", """# 1) PostgreSQL role of Odoo (short restart of Odoo)
sudo -u postgres psql -c '\\password odoo'          # new long password
sudo editor /etc/odoo/odoo.conf                   # db_password = <new>
sudo systemctl restart odoo                       # or: docker compose up -d odoo

# 2) Odoo master password (database manager): admin_passwd in odoo.conf, restart

# 3) Odoo API keys of integrations: create a new key for the technical user,
#    switch the integration, then delete the old key (Preferences > Account Security)
#    overview in SQL:
SELECT u.login, k.name, k.create_date FROM res_users_apikeys k JOIN res_users u ON u.id = k.user_id ORDER BY k.create_date;

# 4) SSH keys: one key per person, remove leavers from authorized_keys on ALL hosts
grep -H '' ~/.ssh/authorized_keys /home/*/.ssh/authorized_keys 2>/dev/null | awk '{print $1, $NF}'

# 5) after rotation: search for the old value in logs, configs, git history, CI secrets"""),
        "ports": ("bash · which ports are open – from inside and from outside", """# inside: what listens on all interfaces (0.0.0.0 / [::])
sudo ss -tlnp | awk 'NR==1 || $4 ~ /^(0\\.0\\.0\\.0|\\[::\\]|\\*):/'

# outside: from another network (your laptop, not the server itself)
nmap -Pn -p 22,80,443,5432,6379,8069,8072,27017,3000-6000 erp.example.com

# typical findings that must NOT be public:
#   8069/8072 Odoo directly (bypasses nginx, TLS, Basic Auth, rate limits)
#   5432 PostgreSQL, 6432 PgBouncer, 27017 MongoDB, 6379 Redis
#   3000–5555 node/pm2 integrations bound to 0.0.0.0"""),
        "docker": ("docker · published ports bypass ufw", """# docker-compose.yml – bind to localhost (nginx on the host) or do not publish at all
services:
  odoo:
    ports: ["127.0.0.1:8069:8069", "127.0.0.1:8072:8072"]
  db:
    # no "ports:" – reachable only inside the compose network

# ufw does not see Docker's rules: block in the DOCKER-USER chain instead
sudo iptables -I DOCKER-USER -i eth0 -p tcp -m multiport --dports 8069,8072,5432,27017 -j DROP
# plus a firewall at the cloud provider: default deny, allow 80/443 (+ SSH only from VPN/office)"""),
        "tls": ("postgresql / odoo.conf · encrypt Odoo ↔ PostgreSQL", """# postgresql.conf (DB server)
ssl = on
ssl_cert_file = '/etc/postgresql/tls/server.crt'
ssl_key_file  = '/etc/postgresql/tls/server.key'      # chmod 600, owner postgres
ssl_min_protocol_version = 'TLSv1.2'

# pg_hba.conf – only encrypted connections from the Odoo host
hostssl  all  odoo  10.0.0.5/32  scram-sha-256
hostnossl all all   0.0.0.0/0    reject

# odoo.conf
db_sslmode = verify-full          # checks the certificate (CA in ~/.postgresql/root.crt of the odoo user)

# replication (on the replica, primary_conninfo): ... sslmode=verify-full

# check: which connections are encrypted?
SELECT a.client_addr, a.usename, s.ssl, s.version FROM pg_stat_ssl s JOIN pg_stat_activity a USING (pid) WHERE a.client_addr IS NOT NULL;"""),
        "wg": ("wireguard · one encrypted network between all servers", """# /etc/wireguard/wg0.conf on the Odoo server (keys: wg genkey | tee priv | wg pubkey > pub)
[Interface]
Address = 10.99.0.1/24
PrivateKey = <odoo-server-private-key>
ListenPort = 51820

[Peer]                      # DB server
PublicKey = <db-server-public-key>
AllowedIPs = 10.99.0.2/32
Endpoint = 10.0.0.10:51820

# then: db_host = 10.99.0.2 and PostgreSQL listens only on 10.99.0.2
sudo systemctl enable --now wg-quick@wg0"""),
        "audit": ("bash · who did what as root", """# sudo log with the full command line (auditd)
sudo apt install auditd
echo '-a always,exit -F arch=b64 -F euid=0 -F auid>=1000 -F auid!=unset -S execve -k rootcmd' | sudo tee /etc/audit/rules.d/rootcmd.rules
sudo augenrules --load
sudo ausearch -k rootcmd -i | tail

# secrets readable only by the service user
sudo chmod 640 /etc/odoo/odoo.conf && sudo chown root:odoo /etc/odoo/odoo.conf
sudo find /opt /etc -name '*.env' -o -name '*.conf' -perm -o=r 2>/dev/null | xargs grep -l -iE 'password|token|secret' 2>/dev/null"""),
    },
    "links": [
        ("Blog: password protection with nginx – and what to close in Odoo", "@blog:nginx-apache-password-protect-odoo-database-manager"),
        ("Blog: leaked passwords, brute force and 2FA in Odoo", "@blog:password-leaks-brute-force-2fa-odoo"),
        ("Blog: Cloudflare Access (Zero Trust) step by step", "@blog:cloudflare-access-zero-trust-step-by-step"),
        ("Odoo security skill for AI agents (Markdown)", "https://2027.pp.ua/skill_odoo_security.md"),
        ("Blog: nginx security audit in front of Odoo – HSTS, X-Frame-Options, cookies", "@blog:nginx-security-audit-odoo-hsts-cookies-x-frame-options"),
        ("Blog: Grafana behind nginx under /grafana/", "@blog:grafana-behind-nginx-subpath-odoo"),
        ("PostgreSQL: secure TCP/IP connections with SSL", "https://www.postgresql.org/docs/current/ssl-tcp.html"),
        ("Docker: packet filtering and firewalls (DOCKER-USER)", "https://docs.docker.com/engine/network/packet-filtering-firewalls/"),
        ("OWASP: information exposure through query strings", "https://owasp.org/www-community/vulnerabilities/Information_exposure_through_query_strings_in_url"),
        ("WireGuard: quick start", "https://www.wireguard.com/quickstart/"),
    ],
    "t": {},
}

SECURITY["t"]["en"] = {
    "title": "Odoo server security: secrets in logs, password rotation, closed ports and encrypted traffic between servers",
    "summary": "What a real audit found – an integration token and phone numbers in the nginx access log – and the four things to check on every Odoo installation: secrets and personal data in URLs and logs, rotation of passwords and keys, ports that must not be public, and encryption of traffic between servers, including against your own admins.",
    "body": [
        ("p", "During a routine check of a production Odoo installation with a call-centre integration, the nginx access log turned up something unpleasant: every request of the integration carried its **access token in the URL** (`?auth=…`), together with **customer phone numbers**. Thousands of lines a day, kept for days, readable by every administrator, copied into backups and monitoring. Nobody had done anything wrong on purpose – the integration simply sent its parameters as a GET query."),
        ("note", "Short version: no secrets and no personal data in URLs; logs only with paths and a limited retention; rotate passwords and keys on a schedule and when people leave; only 80/443 public (Docker bypasses ufw!); encrypt traffic between Odoo, PostgreSQL, replica and integrations – a private network is not a secure network."),
        ("h", "1. Secrets and personal data in URLs and logs"),
        ("p", "A query string is logged everywhere: nginx access logs, load balancers and CDNs, the browser history, `Referer` headers to third-party sites, APM and monitoring tools. Whoever can read one of these places has the token – and with it the integration. Phone numbers are personal data under the GDPR: storing them in logs for weeks without purpose is a compliance problem of its own."),
        ("code", "find"),
        ("code", "header"),
        ("code", "nginx"),
        ("ul", [
            "Move tokens into a header (`Authorization`) and data into the POST body; then rotate the token – the old one is in the logs.",
            "Log only `$uri` (path without query string) – or no access log at all for integration endpoints.",
            "Limit retention: logrotate (14–30 days), Docker `max-size`/`max-file`; delete old logs containing secrets.",
            "Logs readable only by root/adm; integration logs (pm2, node) often contain full requests with passwords – check them too.",
        ]),
        ("h", "2. Rotating passwords and keys"),
        ("p", "A secret that never changes is eventually known to everyone who ever had access: former employees, contractors, an old laptop, a chat history. Rotation limits how long a leak is useful."),
        ("ul", [
            "**Inventory first:** a list of all secrets – PostgreSQL roles, `admin_passwd`, Odoo API keys, integration tokens, SMTP, payment/shipping/bank credentials, SSH keys, cloud tokens – with owner and date of the last change.",
            "**When:** immediately when someone with access leaves or a leak is suspected; otherwise on a schedule (e.g. every 6–12 months for shared secrets).",
            "**How without downtime:** create the new key, switch the consumer, then revoke the old one. For the Odoo database password a short restart is enough.",
            "**Where:** not in git, not in chat; files `chmod 600`/`640`, a password manager or secret store for the team.",
        ]),
        ("code", "rotate"),
        ("h", "3. Ports: only 80 and 443 to the outside"),
        ("code", "ports"),
        ("p", "The classic trap: the firewall (`ufw`) shows “deny”, yet Odoo is reachable on 8069 from the internet. Docker writes its own iptables rules for published ports and bypasses ufw. Publish only on `127.0.0.1` or not at all, and block in the `DOCKER-USER` chain – plus a provider firewall in front of the server."),
        ("code", "docker"),
        ("h", "4. Traffic between servers can be read"),
        ("p", "Odoo ↔ PostgreSQL, primary ↔ replica, Odoo ↔ integrations often run unencrypted “because it is the internal network”. But inside that network sit other virtual machines, the hosting provider's infrastructure – and administrators. Anyone with root on one of the hosts or access to the network path can record the traffic with `tcpdump`: customer data, invoices, session cookies, API tokens. That includes a dishonest or careless admin of your own."),
        ("code", "tls"),
        ("p", "If several services need protection at once, a WireGuard network between the servers is the simplest blanket: everything between the hosts is encrypted, services listen only on the tunnel address."),
        ("code", "wg"),
        ("h", "5. Against the insider: least privilege and traceability"),
        ("ul", [
            "Personal accounts instead of one shared user with passwordless sudo; SSH keys per person; remove leavers on all hosts the same day.",
            "Secrets readable only by the service user (`odoo.conf` 640, `.env` 600) – config and log files with `644` and passwords are common.",
            "Log root commands (auditd) and ship logs to a place the admin of the server cannot edit.",
            "2FA for the cloud console, the domain registrar, Cloudflare, GitHub – that is where the keys to everything are.",
            "After a person leaves: rotate everything they could read, not only their login.",
        ]),
        ("code", "audit"),
        ("h", "Checklist"),
        ("ul", [
            "No tokens/passwords/phone numbers in URLs; access logs without query strings; retention ≤ 30 days.",
            "Inventory of secrets with owner and date; rotation on leaving and on schedule.",
            "From outside only 80/443 (and SSH from known addresses); Docker ports on 127.0.0.1; DOCKER-USER rules; provider firewall.",
            "PostgreSQL with `ssl = on`, `hostssl` and `db_sslmode = verify-full`; replication and integrations over TLS or WireGuard.",
            "Personal admin accounts, auditd, 2FA on all consoles, secrets not world-readable.",
        ]),
        ("links", "Links"),
    ],
}

SECURITY["t"]["de"] = {
    "title": "Sicherheit des Odoo-Servers: Geheimnisse in Logs, Passwort-Rotation, geschlossene Ports und verschlüsselter Verkehr zwischen Servern",
    "summary": "Was ein echtes Audit fand – ein Integrations-Token und Telefonnummern im nginx-Access-Log – und die vier Dinge, die man bei jeder Odoo-Installation prüfen sollte: Geheimnisse und personenbezogene Daten in URLs und Logs, Rotation von Passwörtern und Schlüsseln, Ports, die nicht öffentlich sein dürfen, und Verschlüsselung des Verkehrs zwischen Servern, auch gegenüber den eigenen Admins.",
    "body": [
        ("p", "Bei einer Routineprüfung einer produktiven Odoo-Installation mit Callcenter-Anbindung zeigte das nginx-Access-Log etwas Unangenehmes: Jede Anfrage der Integration trug ihr **Zugriffstoken in der URL** (`?auth=…`), zusammen mit **Telefonnummern von Kunden**. Tausende Zeilen pro Tag, tagelang aufbewahrt, für jeden Administrator lesbar, in Backups und Monitoring kopiert. Niemand hatte absichtlich etwas falsch gemacht – die Integration schickte ihre Parameter einfach als GET-Query."),
        ("note", "Kurzfassung: keine Geheimnisse und keine personenbezogenen Daten in URLs; Logs nur mit Pfaden und begrenzter Aufbewahrung; Passwörter und Schlüssel planmäßig und beim Ausscheiden von Personen rotieren; nur 80/443 öffentlich (Docker umgeht ufw!); Verkehr zwischen Odoo, PostgreSQL, Replica und Integrationen verschlüsseln – ein privates Netz ist kein sicheres Netz."),
        ("h", "1. Geheimnisse und personenbezogene Daten in URLs und Logs"),
        ("p", "Ein Query-String wird überall protokolliert: nginx-Access-Logs, Load Balancer und CDNs, Browserverlauf, `Referer`-Header an fremde Seiten, APM- und Monitoring-Werkzeuge. Wer einen dieser Orte lesen kann, hat das Token – und damit die Integration. Telefonnummern sind personenbezogene Daten im Sinne der DSGVO: Sie wochenlang ohne Zweck in Logs zu speichern, ist ein eigenes Compliance-Problem."),
        ("code", "find"),
        ("code", "header"),
        ("code", "nginx"),
        ("ul", [
            "Tokens in einen Header (`Authorization`) und Daten in den POST-Body verlegen; danach das Token rotieren – das alte steht in den Logs.",
            "Nur `$uri` protokollieren (Pfad ohne Query-String) – oder für Integrations-Endpunkte gar kein Access-Log.",
            "Aufbewahrung begrenzen: logrotate (14–30 Tage), Docker `max-size`/`max-file`; alte Logs mit Geheimnissen löschen.",
            "Logs nur für root/adm lesbar; Integrations-Logs (pm2, node) enthalten oft vollständige Anfragen mit Passwörtern – auch prüfen.",
        ]),
        ("h", "2. Passwörter und Schlüssel rotieren"),
        ("p", "Ein Geheimnis, das sich nie ändert, kennt irgendwann jeder, der je Zugriff hatte: frühere Mitarbeiter, Dienstleister, ein alter Laptop, ein Chatverlauf. Rotation begrenzt, wie lange ein Leck nützlich ist."),
        ("ul", [
            "**Zuerst Inventur:** eine Liste aller Geheimnisse – PostgreSQL-Rollen, `admin_passwd`, Odoo-API-Schlüssel, Integrations-Tokens, SMTP, Zugangsdaten für Zahlung/Versand/Bank, SSH-Schlüssel, Cloud-Tokens – mit Verantwortlichem und Datum der letzten Änderung.",
            "**Wann:** sofort, wenn jemand mit Zugriff ausscheidet oder ein Leck vermutet wird; sonst planmäßig (z. B. alle 6–12 Monate für geteilte Geheimnisse).",
            "**Wie ohne Ausfall:** neuen Schlüssel anlegen, den Verbraucher umstellen, dann den alten widerrufen. Für das Odoo-Datenbankpasswort genügt ein kurzer Neustart.",
            "**Wo:** nicht in git, nicht im Chat; Dateien `chmod 600`/`640`, ein Passwortmanager oder Secret Store für das Team.",
        ]),
        ("code", "rotate"),
        ("h", "3. Ports: nach außen nur 80 und 443"),
        ("code", "ports"),
        ("p", "Die klassische Falle: Die Firewall (`ufw`) zeigt „deny“, und trotzdem ist Odoo auf 8069 aus dem Internet erreichbar. Docker schreibt für veröffentlichte Ports eigene iptables-Regeln und umgeht ufw. Nur auf `127.0.0.1` oder gar nicht veröffentlichen und in der Kette `DOCKER-USER` sperren – dazu eine Firewall des Providers vor dem Server."),
        ("code", "docker"),
        ("h", "4. Verkehr zwischen Servern kann mitgelesen werden"),
        ("p", "Odoo ↔ PostgreSQL, Primary ↔ Replica, Odoo ↔ Integrationen laufen oft unverschlüsselt, „weil es das interne Netz ist“. Aber in diesem Netz sitzen andere virtuelle Maschinen, die Infrastruktur des Hosters – und Administratoren. Wer root auf einem der Hosts oder Zugang zum Netzwerkpfad hat, kann den Verkehr mit `tcpdump` mitschneiden: Kundendaten, Rechnungen, Session-Cookies, API-Tokens. Das schließt einen unredlichen oder unachtsamen eigenen Admin ein."),
        ("code", "tls"),
        ("p", "Wenn mehrere Dienste gleichzeitig geschützt werden sollen, ist ein WireGuard-Netz zwischen den Servern die einfachste Decke: Alles zwischen den Hosts ist verschlüsselt, Dienste lauschen nur auf der Tunneladresse."),
        ("code", "wg"),
        ("h", "5. Gegen den Innentäter: minimale Rechte und Nachvollziehbarkeit"),
        ("ul", [
            "Persönliche Konten statt eines gemeinsamen Benutzers mit Sudo ohne Passwort; SSH-Schlüssel pro Person; Ausgeschiedene am selben Tag auf allen Hosts entfernen.",
            "Geheimnisse nur für den Dienstbenutzer lesbar (`odoo.conf` 640, `.env` 600) – Konfigurations- und Logdateien mit `644` und Passwörtern sind häufig.",
            "Root-Befehle protokollieren (auditd) und Logs an einen Ort schicken, den der Admin des Servers nicht ändern kann.",
            "2FA für Cloud-Konsole, Domain-Registrar, Cloudflare, GitHub – dort liegen die Schlüssel zu allem.",
            "Nach dem Ausscheiden einer Person: alles rotieren, was sie lesen konnte, nicht nur ihren Login.",
        ]),
        ("code", "audit"),
        ("h", "Checkliste"),
        ("ul", [
            "Keine Tokens/Passwörter/Telefonnummern in URLs; Access-Logs ohne Query-Strings; Aufbewahrung ≤ 30 Tage.",
            "Inventur der Geheimnisse mit Verantwortlichem und Datum; Rotation beim Ausscheiden und planmäßig.",
            "Von außen nur 80/443 (und SSH von bekannten Adressen); Docker-Ports auf 127.0.0.1; DOCKER-USER-Regeln; Provider-Firewall.",
            "PostgreSQL mit `ssl = on`, `hostssl` und `db_sslmode = verify-full`; Replikation und Integrationen über TLS oder WireGuard.",
            "Persönliche Admin-Konten, auditd, 2FA auf allen Konsolen, Geheimnisse nicht für alle lesbar.",
        ]),
        ("links", "Links"),
    ],
}

SECURITY["t"]["fr"] = {
    "title": "Sécurité du serveur Odoo : secrets dans les journaux, rotation des mots de passe, ports fermés et trafic chiffré entre serveurs",
    "summary": "Ce qu'un vrai audit a trouvé – un jeton d'intégration et des numéros de téléphone dans le journal d'accès nginx – et les quatre points à vérifier sur chaque installation Odoo : secrets et données personnelles dans les URL et les journaux, rotation des mots de passe et des clés, ports qui ne doivent pas être publics, et chiffrement du trafic entre serveurs, y compris face à ses propres administrateurs.",
    "body": [
        ("p", "Lors d'un contrôle de routine d'une installation Odoo de production avec intégration de centre d'appels, le journal d'accès nginx a révélé quelque chose de désagréable : chaque requête de l'intégration portait son **jeton d'accès dans l'URL** (`?auth=…`), avec des **numéros de téléphone de clients**. Des milliers de lignes par jour, conservées pendant des jours, lisibles par chaque administrateur, copiées dans les sauvegardes et la supervision. Personne n'avait mal agi volontairement – l'intégration envoyait simplement ses paramètres en requête GET."),
        ("note", "En bref : aucun secret ni donnée personnelle dans les URL ; des journaux avec les chemins seulement et une durée de conservation limitée ; rotation des mots de passe et des clés selon un calendrier et au départ des personnes ; seuls 80/443 publics (Docker contourne ufw !) ; chiffrer le trafic entre Odoo, PostgreSQL, réplique et intégrations – un réseau privé n'est pas un réseau sûr."),
        ("h", "1. Secrets et données personnelles dans les URL et les journaux"),
        ("p", "Une chaîne de requête est journalisée partout : journaux d'accès nginx, répartiteurs de charge et CDN, historique du navigateur, en-têtes `Referer` vers des sites tiers, outils d'APM et de supervision. Qui peut lire l'un de ces endroits possède le jeton – et donc l'intégration. Les numéros de téléphone sont des données personnelles au sens du RGPD : les conserver des semaines dans des journaux sans finalité est un problème de conformité en soi."),
        ("code", "find"),
        ("code", "header"),
        ("code", "nginx"),
        ("ul", [
            "Placer les jetons dans un en-tête (`Authorization`) et les données dans le corps POST ; puis faire tourner le jeton – l'ancien est dans les journaux.",
            "Ne journaliser que `$uri` (chemin sans chaîne de requête) – ou pas de journal d'accès du tout pour les points d'entrée d'intégration.",
            "Limiter la conservation : logrotate (14–30 jours), Docker `max-size`/`max-file` ; supprimer les anciens journaux contenant des secrets.",
            "Journaux lisibles seulement par root/adm ; les journaux d'intégration (pm2, node) contiennent souvent des requêtes complètes avec mots de passe – les vérifier aussi.",
        ]),
        ("h", "2. Rotation des mots de passe et des clés"),
        ("p", "Un secret qui ne change jamais finit par être connu de tous ceux qui y ont eu accès : anciens employés, prestataires, un vieux portable, un historique de messagerie. La rotation limite la durée pendant laquelle une fuite est exploitable."),
        ("ul", [
            "**D'abord l'inventaire :** une liste de tous les secrets – rôles PostgreSQL, `admin_passwd`, clés API Odoo, jetons d'intégration, SMTP, identifiants de paiement/transport/banque, clés SSH, jetons cloud – avec responsable et date du dernier changement.",
            "**Quand :** immédiatement au départ d'une personne ayant eu accès ou en cas de fuite suspectée ; sinon selon un calendrier (par ex. tous les 6–12 mois pour les secrets partagés).",
            "**Comment sans interruption :** créer la nouvelle clé, basculer le consommateur, puis révoquer l'ancienne. Pour le mot de passe de base d'Odoo, un court redémarrage suffit.",
            "**Où :** pas dans git, pas dans le chat ; fichiers `chmod 600`/`640`, un gestionnaire de mots de passe ou un coffre à secrets pour l'équipe.",
        ]),
        ("code", "rotate"),
        ("h", "3. Ports : seulement 80 et 443 vers l'extérieur"),
        ("code", "ports"),
        ("p", "Le piège classique : le pare-feu (`ufw`) affiche « deny » et pourtant Odoo est joignable sur 8069 depuis Internet. Docker écrit ses propres règles iptables pour les ports publiés et contourne ufw. Publier seulement sur `127.0.0.1` ou pas du tout, et bloquer dans la chaîne `DOCKER-USER` – plus un pare-feu de l'hébergeur devant le serveur."),
        ("code", "docker"),
        ("h", "4. Le trafic entre serveurs peut être lu"),
        ("p", "Odoo ↔ PostgreSQL, primaire ↔ réplique, Odoo ↔ intégrations circulent souvent en clair « parce que c'est le réseau interne ». Mais dans ce réseau se trouvent d'autres machines virtuelles, l'infrastructure de l'hébergeur – et des administrateurs. Quiconque a root sur l'un des hôtes ou accès au chemin réseau peut enregistrer le trafic avec `tcpdump` : données clients, factures, cookies de session, jetons API. Cela inclut un administrateur maison malhonnête ou négligent."),
        ("code", "tls"),
        ("p", "Si plusieurs services doivent être protégés à la fois, un réseau WireGuard entre les serveurs est la couverture la plus simple : tout ce qui passe entre les hôtes est chiffré, les services n'écoutent que sur l'adresse du tunnel."),
        ("code", "wg"),
        ("h", "5. Contre l'initié : moindre privilège et traçabilité"),
        ("ul", [
            "Comptes personnels au lieu d'un utilisateur partagé avec sudo sans mot de passe ; clés SSH par personne ; retirer les partants le jour même sur tous les hôtes.",
            "Secrets lisibles seulement par l'utilisateur du service (`odoo.conf` 640, `.env` 600) – les fichiers de configuration et de journal en `644` avec des mots de passe sont fréquents.",
            "Journaliser les commandes root (auditd) et envoyer les journaux là où l'administrateur du serveur ne peut pas les modifier.",
            "2FA pour la console cloud, le bureau d'enregistrement du domaine, Cloudflare, GitHub – c'est là que se trouvent les clés de tout.",
            "Après le départ d'une personne : faire tourner tout ce qu'elle pouvait lire, pas seulement son identifiant.",
        ]),
        ("code", "audit"),
        ("h", "Liste de contrôle"),
        ("ul", [
            "Pas de jetons/mots de passe/numéros de téléphone dans les URL ; journaux d'accès sans chaîne de requête ; conservation ≤ 30 jours.",
            "Inventaire des secrets avec responsable et date ; rotation au départ et selon calendrier.",
            "De l'extérieur seulement 80/443 (et SSH depuis des adresses connues) ; ports Docker sur 127.0.0.1 ; règles DOCKER-USER ; pare-feu de l'hébergeur.",
            "PostgreSQL avec `ssl = on`, `hostssl` et `db_sslmode = verify-full` ; réplication et intégrations via TLS ou WireGuard.",
            "Comptes administrateur personnels, auditd, 2FA sur toutes les consoles, secrets non lisibles par tous.",
        ]),
        ("links", "Liens"),
    ],
}

SECURITY["t"]["el"] = {
    "title": "Ασφάλεια server Odoo: μυστικά στα logs, εναλλαγή κωδικών, κλειστές θύρες και κρυπτογραφημένη κίνηση μεταξύ servers",
    "summary": "Τι βρήκε ένας πραγματικός έλεγχος – ένα token διασύνδεσης και αριθμούς τηλεφώνου στο access log του nginx – και τα τέσσερα πράγματα που πρέπει να ελέγχετε σε κάθε εγκατάσταση Odoo: μυστικά και προσωπικά δεδομένα σε URL και logs, εναλλαγή κωδικών και κλειδιών, θύρες που δεν πρέπει να είναι δημόσιες, και κρυπτογράφηση της κίνησης μεταξύ servers, και απέναντι στους δικούς σας διαχειριστές.",
    "body": [
        ("p", "Σε έναν έλεγχο ρουτίνας μιας εγκατάστασης Odoo παραγωγής με διασύνδεση τηλεφωνικού κέντρου, το access log του nginx αποκάλυψε κάτι δυσάρεστο: κάθε αίτημα της διασύνδεσης κουβαλούσε το **token πρόσβασης στο URL** (`?auth=…`), μαζί με **αριθμούς τηλεφώνου πελατών**. Χιλιάδες γραμμές την ημέρα, κρατημένες για μέρες, αναγνώσιμες από κάθε διαχειριστή, αντιγραμμένες σε αντίγραφα ασφαλείας και παρακολούθηση. Κανείς δεν έκανε σκόπιμα λάθος – η διασύνδεση απλώς έστελνε τις παραμέτρους της ως GET query."),
        ("note", "Συνοπτικά: κανένα μυστικό και κανένα προσωπικό δεδομένο σε URL· logs μόνο με διαδρομές και περιορισμένη διάρκεια διατήρησης· εναλλαγή κωδικών και κλειδιών προγραμματισμένα και όταν φεύγουν άτομα· μόνο 80/443 δημόσια (το Docker παρακάμπτει το ufw!)· κρυπτογραφήστε την κίνηση μεταξύ Odoo, PostgreSQL, replica και διασυνδέσεων – ένα ιδιωτικό δίκτυο δεν είναι ασφαλές δίκτυο."),
        ("h", "1. Μυστικά και προσωπικά δεδομένα σε URL και logs"),
        ("p", "Ένα query string καταγράφεται παντού: access logs του nginx, load balancers και CDN, ιστορικό browser, κεφαλίδες `Referer` προς τρίτους ιστότοπους, εργαλεία APM και παρακολούθησης. Όποιος μπορεί να διαβάσει ένα από αυτά έχει το token – και μαζί του τη διασύνδεση. Οι αριθμοί τηλεφώνου είναι προσωπικά δεδομένα κατά τον GDPR: η αποθήκευσή τους για εβδομάδες σε logs χωρίς σκοπό είναι ξεχωριστό πρόβλημα συμμόρφωσης."),
        ("code", "find"),
        ("code", "header"),
        ("code", "nginx"),
        ("ul", [
            "Μεταφέρετε τα tokens σε κεφαλίδα (`Authorization`) και τα δεδομένα στο σώμα του POST· μετά αλλάξτε το token – το παλιό είναι στα logs.",
            "Καταγράφετε μόνο το `$uri` (διαδρομή χωρίς query string) – ή καθόλου access log για τα endpoints διασύνδεσης.",
            "Περιορίστε τη διατήρηση: logrotate (14–30 ημέρες), Docker `max-size`/`max-file`· διαγράψτε παλιά logs με μυστικά.",
            "Logs αναγνώσιμα μόνο από root/adm· τα logs διασυνδέσεων (pm2, node) περιέχουν συχνά ολόκληρα αιτήματα με κωδικούς – ελέγξτε τα κι αυτά.",
        ]),
        ("h", "2. Εναλλαγή κωδικών και κλειδιών"),
        ("p", "Ένα μυστικό που δεν αλλάζει ποτέ το ξέρουν τελικά όλοι όσοι είχαν ποτέ πρόσβαση: πρώην υπάλληλοι, συνεργάτες, ένα παλιό laptop, ένα ιστορικό συνομιλίας. Η εναλλαγή περιορίζει πόσο καιρό είναι χρήσιμη μια διαρροή."),
        ("ul", [
            "**Πρώτα απογραφή:** λίστα όλων των μυστικών – ρόλοι PostgreSQL, `admin_passwd`, κλειδιά API του Odoo, tokens διασυνδέσεων, SMTP, διαπιστευτήρια πληρωμών/αποστολών/τράπεζας, κλειδιά SSH, tokens cloud – με υπεύθυνο και ημερομηνία τελευταίας αλλαγής.",
            "**Πότε:** αμέσως όταν φεύγει κάποιος με πρόσβαση ή υπάρχει υποψία διαρροής· αλλιώς προγραμματισμένα (π.χ. κάθε 6–12 μήνες για κοινά μυστικά).",
            "**Πώς χωρίς διακοπή:** δημιουργήστε το νέο κλειδί, αλλάξτε τον καταναλωτή, μετά ανακαλέστε το παλιό. Για τον κωδικό βάσης του Odoo αρκεί μια σύντομη επανεκκίνηση.",
            "**Πού:** όχι σε git, όχι σε chat· αρχεία `chmod 600`/`640`, password manager ή secret store για την ομάδα.",
        ]),
        ("code", "rotate"),
        ("h", "3. Θύρες: προς τα έξω μόνο 80 και 443"),
        ("code", "ports"),
        ("p", "Η κλασική παγίδα: το firewall (`ufw`) δείχνει «deny» και παρ' όλα αυτά το Odoo είναι προσβάσιμο στη 8069 από το Internet. Το Docker γράφει δικούς του κανόνες iptables για δημοσιευμένες θύρες και παρακάμπτει το ufw. Δημοσιεύστε μόνο σε `127.0.0.1` ή καθόλου, και μπλοκάρετε στην αλυσίδα `DOCKER-USER` – συν firewall του παρόχου μπροστά από τον server."),
        ("code", "docker"),
        ("h", "4. Η κίνηση μεταξύ servers μπορεί να διαβαστεί"),
        ("p", "Odoo ↔ PostgreSQL, primary ↔ replica, Odoo ↔ διασυνδέσεις συχνά τρέχουν χωρίς κρυπτογράφηση «επειδή είναι το εσωτερικό δίκτυο». Όμως σε αυτό το δίκτυο βρίσκονται άλλες εικονικές μηχανές, η υποδομή του παρόχου – και διαχειριστές. Όποιος έχει root σε έναν από τους hosts ή πρόσβαση στη διαδρομή του δικτύου μπορεί να καταγράψει την κίνηση με `tcpdump`: δεδομένα πελατών, τιμολόγια, session cookies, API tokens. Αυτό περιλαμβάνει και έναν ανέντιμο ή απρόσεκτο δικό σας διαχειριστή."),
        ("code", "tls"),
        ("p", "Αν πρέπει να προστατευτούν πολλές υπηρεσίες μαζί, ένα δίκτυο WireGuard μεταξύ των servers είναι η απλούστερη κουβέρτα: όλα μεταξύ των hosts κρυπτογραφούνται, οι υπηρεσίες ακούν μόνο στη διεύθυνση του tunnel."),
        ("code", "wg"),
        ("h", "5. Απέναντι στον εσωτερικό: ελάχιστα δικαιώματα και ιχνηλασιμότητα"),
        ("ul", [
            "Προσωπικοί λογαριασμοί αντί για έναν κοινό χρήστη με sudo χωρίς κωδικό· κλειδιά SSH ανά άτομο· αφαιρέστε όσους φεύγουν την ίδια μέρα από όλους τους hosts.",
            "Μυστικά αναγνώσιμα μόνο από τον χρήστη της υπηρεσίας (`odoo.conf` 640, `.env` 600) – αρχεία ρυθμίσεων και logs με `644` και κωδικούς είναι συνηθισμένα.",
            "Καταγράφετε τις εντολές root (auditd) και στέλνετε τα logs κάπου που ο διαχειριστής του server δεν μπορεί να τα αλλάξει.",
            "2FA για την κονσόλα cloud, τον registrar του domain, το Cloudflare, το GitHub – εκεί είναι τα κλειδιά για όλα.",
            "Όταν φεύγει κάποιος: αλλάξτε ό,τι μπορούσε να διαβάσει, όχι μόνο τη σύνδεσή του.",
        ]),
        ("code", "audit"),
        ("h", "Λίστα ελέγχου"),
        ("ul", [
            "Όχι tokens/κωδικούς/τηλέφωνα σε URL· access logs χωρίς query strings· διατήρηση ≤ 30 ημέρες.",
            "Απογραφή μυστικών με υπεύθυνο και ημερομηνία· εναλλαγή όταν φεύγει κάποιος και προγραμματισμένα.",
            "Από έξω μόνο 80/443 (και SSH από γνωστές διευθύνσεις)· θύρες Docker σε 127.0.0.1· κανόνες DOCKER-USER· firewall παρόχου.",
            "PostgreSQL με `ssl = on`, `hostssl` και `db_sslmode = verify-full`· αναπαραγωγή και διασυνδέσεις μέσω TLS ή WireGuard.",
            "Προσωπικοί λογαριασμοί διαχειριστών, auditd, 2FA σε όλες τις κονσόλες, μυστικά όχι αναγνώσιμα από όλους.",
        ]),
        ("links", "Σύνδεσμοι"),
    ],
}

SECURITY["t"]["uk"] = {
    "title": "Безпека сервера Odoo: секрети в логах, ротація паролів, закриті порти й шифрування трафіку між серверами",
    "summary": "Що знайшов реальний аудит (токен інтеграції та номери телефонів у access-лозі nginx) і чотири речі, які варто перевірити на кожній інсталяції Odoo: секрети й персональні дані в URL та логах, ротація паролів і ключів, порти, які не мають бути відкриті назовні, і шифрування трафіку між серверами, зокрема від власних адмінів.",
    "body": [
        ("p", "Під час планової перевірки продуктивної інсталяції Odoo з інтеграцією кол-центру в access-лозі nginx знайшлося неприємне: кожен запит інтеграції ніс свій **токен доступу в URL** (`?auth=…`) разом із **номерами телефонів клієнтів**. Тисячі рядків на день, які зберігаються днями, доступні кожному адміністратору й потрапляють у бекапи та моніторинг. Ніхто не помилився навмисно, інтеграція просто передавала параметри GET-запитом."),
        ("note", "Коротко: жодних секретів і персональних даних в URL; у логах лише шляхи й обмежений термін зберігання; ротація паролів і ключів за графіком і при звільненні людей; назовні відкриті лише 80/443 (Docker обходить ufw!); шифруйте трафік між Odoo, PostgreSQL, реплікою та інтеграціями, бо приватна мережа — це ще не безпечна мережа."),
        ("h", "1. Секрети й персональні дані в URL та логах"),
        ("p", "Рядок запиту записується всюди: в access-логи nginx, балансувальники й CDN, історію браузера, заголовки `Referer` до сторонніх сайтів, інструменти APM і моніторингу. Хто може прочитати бодай одне з цих місць, той має токен, а з ним і доступ до інтеграції. Номери телефонів — персональні дані в розумінні GDPR: зберігати їх тижнями в логах без мети — окрема проблема з відповідністю."),
        ("code", "find"),
        ("code", "header"),
        ("code", "nginx"),
        ("ul", [
            "Перенесіть токени в заголовок (`Authorization`), а дані в тіло POST. Після цього замініть токен, бо старий уже лежить у логах.",
            "Пишіть у лог лише `$uri` (шлях без рядка запиту) або взагалі вимкніть access-лог для точок інтеграції.",
            "Обмежте термін зберігання: logrotate (14–30 днів), Docker `max-size`/`max-file`. Старі логи із секретами видаліть.",
            "Логи мають бути доступні лише root/adm. Логи інтеграцій (pm2, node) часто містять повні запити з паролями, тож перевірте й їх.",
        ]),
        ("h", "2. Ротація паролів і ключів"),
        ("p", "Секрет, який ніколи не змінюється, рано чи пізно знає кожен, хто колись мав доступ: колишні співробітники, підрядники, старий ноутбук, історія чату. Ротація обмежує час, протягом якого витік можна використати."),
        ("ul", [
            "**Спершу інвентаризація:** список усіх секретів (ролі PostgreSQL, `admin_passwd`, API-ключі Odoo, токени інтеграцій, SMTP, доступи до платежів, доставки й банку, SSH-ключі, хмарні токени) із відповідальним і датою останньої зміни.",
            "**Коли:** одразу, щойно йде людина з доступом або є підозра на витік; в інших випадках за графіком (наприклад, раз на 6–12 місяців для спільних секретів).",
            "**Як без простою:** створіть новий ключ, перемкніть на нього споживача, а потім відкличте старий. Для пароля бази Odoo досить короткого перезапуску.",
            "**Де зберігати:** не в git і не в чаті. Файли з правами `chmod 600`/`640`, для команди — менеджер паролів або сховище секретів.",
        ]),
        ("code", "rotate"),
        ("h", "3. Порти: назовні лише 80 і 443"),
        ("code", "ports"),
        ("p", "Класична пастка: файрвол (`ufw`) показує «deny», а Odoo все одно доступний з інтернету на порту 8069. Docker прописує для опублікованих портів власні правила iptables і обходить ufw. Публікуйте порти лише на `127.0.0.1` або не публікуйте зовсім, блокуйте в ланцюжку `DOCKER-USER` і додайте файрвол провайдера перед сервером."),
        ("code", "docker"),
        ("h", "4. Трафік між серверами можна перехопити"),
        ("p", "Odoo ↔ PostgreSQL, майстер ↔ репліка, Odoo ↔ інтеграції часто працюють без шифрування, «бо це ж внутрішня мережа». Але в цій мережі є інші віртуальні машини, інфраструктура хостера й адміністратори. Будь-хто з root на одному з хостів чи доступом до мережевого шляху може записати трафік через `tcpdump`: дані клієнтів, рахунки, сесійні cookie, API-токени. Це стосується й нечесного чи неуважного власного адміна."),
        ("code", "tls"),
        ("p", "Якщо треба захистити кілька сервісів одразу, найпростіше рішення — мережа WireGuard між серверами: усе між хостами шифрується, а сервіси слухають лише на адресі тунелю."),
        ("code", "wg"),
        ("h", "5. Від внутрішнього порушника: мінімум прав і відстежуваність"),
        ("ul", [
            "Персональні облікові записи замість одного спільного користувача із sudo без пароля, окремий SSH-ключ для кожної людини, а тих, хто пішов, видаляйте з усіх хостів того ж дня.",
            "Секрети мають бути доступні лише користувачу сервісу (`odoo.conf` 640, `.env` 600). Файли конфігурації й логів із правами `644` і паролями всередині трапляються часто.",
            "Записуйте команди root (auditd) і відправляйте логи туди, де адмін сервера не зможе їх змінити.",
            "Увімкніть 2FA для хмарної консолі, реєстратора домену, Cloudflare, GitHub, бо саме там ключі до всього.",
            "Коли людина йде, змініть усе, що вона могла прочитати, а не лише її логін.",
        ]),
        ("code", "audit"),
        ("h", "Чек-лист"),
        ("ul", [
            "Жодних токенів, паролів і телефонів в URL; access-логи без рядків запиту; зберігання не довше 30 днів.",
            "Інвентаризація секретів із відповідальним і датою; ротація при звільненні й за графіком.",
            "Ззовні лише 80/443 (і SSH з відомих адрес); порти Docker на 127.0.0.1; правила DOCKER-USER; файрвол провайдера.",
            "PostgreSQL з `ssl = on`, `hostssl` і `db_sslmode = verify-full`; реплікація й інтеграції через TLS або WireGuard.",
            "Персональні облікові записи адмінів, auditd, 2FA на всіх консолях, секрети недоступні всім підряд.",
        ]),
        ("links", "Посилання"),
    ],
}

SECURITY["t"]["ru"] = {
    "title": "Безопасность сервера Odoo: секреты в логах, ротация паролей, закрытые порты и шифрование трафика между серверами",
    "summary": "Что нашёл реальный аудит (токен интеграции и номера телефонов в access-логе nginx) и четыре вещи, которые стоит проверить на каждой инсталляции Odoo: секреты и персональные данные в URL и логах, ротация паролей и ключей, порты, которые не должны быть открыты наружу, и шифрование трафика между серверами, в том числе от собственных админов.",
    "body": [
        ("p", "При плановой проверке продакшен-инсталляции Odoo с интеграцией колл-центра в access-логе nginx нашлось неприятное: каждый запрос интеграции нёс свой **токен доступа в URL** (`?auth=…`) вместе с **номерами телефонов клиентов**. Тысячи строк в день, которые хранятся днями, доступны каждому администратору и попадают в бэкапы и мониторинг. Никто не ошибся намеренно, интеграция просто передавала параметры GET-запросом."),
        ("note", "Коротко: никаких секретов и персональных данных в URL; в логах только пути и ограниченный срок хранения; ротация паролей и ключей по графику и при уходе людей; наружу открыты только 80/443 (Docker обходит ufw!); шифруйте трафик между Odoo, PostgreSQL, репликой и интеграциями, потому что частная сеть — это ещё не безопасная сеть."),
        ("h", "1. Секреты и персональные данные в URL и логах"),
        ("p", "Строка запроса записывается везде: в access-логи nginx, балансировщики и CDN, историю браузера, заголовки `Referer` на сторонние сайты, инструменты APM и мониторинга. Кто может прочитать хотя бы одно из этих мест, тот получает токен, а с ним и доступ к интеграции. Номера телефонов — персональные данные в смысле GDPR: хранить их неделями в логах без цели — отдельная проблема с соответствием."),
        ("code", "find"),
        ("code", "header"),
        ("code", "nginx"),
        ("ul", [
            "Перенесите токены в заголовок (`Authorization`), а данные в тело POST. После этого смените токен, потому что старый уже лежит в логах.",
            "Пишите в лог только `$uri` (путь без строки запроса) или совсем отключите access-лог для точек интеграции.",
            "Ограничьте срок хранения: logrotate (14–30 дней), Docker `max-size`/`max-file`. Старые логи с секретами удалите.",
            "Логи должны быть доступны только root/adm. Логи интеграций (pm2, node) часто содержат полные запросы с паролями, поэтому проверьте и их.",
        ]),
        ("h", "2. Ротация паролей и ключей"),
        ("p", "Секрет, который никогда не меняется, рано или поздно знает каждый, кто когда-либо имел доступ: бывшие сотрудники, подрядчики, старый ноутбук, история чата. Ротация ограничивает время, в течение которого утечкой можно воспользоваться."),
        ("ul", [
            "**Сначала инвентаризация:** список всех секретов (роли PostgreSQL, `admin_passwd`, API-ключи Odoo, токены интеграций, SMTP, доступы к платежам, доставке и банку, SSH-ключи, облачные токены) с ответственным и датой последней смены.",
            "**Когда:** сразу, как только уходит человек с доступом или есть подозрение на утечку; в остальных случаях по графику (например, раз в 6–12 месяцев для общих секретов).",
            "**Как без простоя:** создайте новый ключ, переключите на него потребителя, а затем отзовите старый. Для пароля базы Odoo хватит короткого перезапуска.",
            "**Где хранить:** не в git и не в чате. Файлы с правами `chmod 600`/`640`, для команды — менеджер паролей или хранилище секретов.",
        ]),
        ("code", "rotate"),
        ("h", "3. Порты: наружу только 80 и 443"),
        ("code", "ports"),
        ("p", "Классическая ловушка: файрвол (`ufw`) показывает «deny», а Odoo всё равно доступен из интернета на порту 8069. Docker прописывает для опубликованных портов собственные правила iptables и обходит ufw. Публикуйте порты только на `127.0.0.1` или не публикуйте вовсе, блокируйте в цепочке `DOCKER-USER` и добавьте файрвол провайдера перед сервером."),
        ("code", "docker"),
        ("h", "4. Трафик между серверами можно перехватить"),
        ("p", "Odoo ↔ PostgreSQL, мастер ↔ реплика, Odoo ↔ интеграции часто работают без шифрования, «потому что это внутренняя сеть». Но в этой сети есть другие виртуальные машины, инфраструктура хостера и администраторы. Любой, у кого есть root на одном из хостов или доступ к сетевому пути, может записать трафик через `tcpdump`: данные клиентов, счета, сессионные cookie, API-токены. Это касается и нечестного или невнимательного собственного админа."),
        ("code", "tls"),
        ("p", "Если нужно защитить сразу несколько сервисов, самое простое решение — сеть WireGuard между серверами: всё между хостами шифруется, а сервисы слушают только на адресе туннеля."),
        ("code", "wg"),
        ("h", "5. От внутреннего нарушителя: минимум прав и прослеживаемость"),
        ("ul", [
            "Персональные учётные записи вместо одного общего пользователя с sudo без пароля, отдельный SSH-ключ для каждого человека, а ушедших удаляйте со всех хостов в тот же день.",
            "Секреты должны быть доступны только пользователю сервиса (`odoo.conf` 640, `.env` 600). Файлы конфигурации и логов с правами `644` и паролями внутри встречаются часто.",
            "Записывайте команды root (auditd) и отправляйте логи туда, где админ сервера не сможет их изменить.",
            "Включите 2FA для облачной консоли, регистратора домена, Cloudflare, GitHub, потому что именно там ключи ко всему.",
            "Когда человек уходит, смените всё, что он мог прочитать, а не только его логин.",
        ]),
        ("code", "audit"),
        ("h", "Чек-лист"),
        ("ul", [
            "Никаких токенов, паролей и телефонов в URL; access-логи без строк запроса; хранение не дольше 30 дней.",
            "Инвентаризация секретов с ответственным и датой; ротация при уходе и по графику.",
            "Снаружи только 80/443 (и SSH с известных адресов); порты Docker на 127.0.0.1; правила DOCKER-USER; файрвол провайдера.",
            "PostgreSQL с `ssl = on`, `hostssl` и `db_sslmode = verify-full`; репликация и интеграции через TLS или WireGuard.",
            "Персональные учётные записи админов, auditd, 2FA на всех консолях, секреты недоступны всем подряд.",
        ]),
        ("links", "Ссылки"),
    ],
}
