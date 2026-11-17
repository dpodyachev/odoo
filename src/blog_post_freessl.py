# Статья 26: бесплатный HTTPS – certbot + python3-certbot-nginx, продление (cron или systemd timer+service), бесплатные
# альтернативы (acme.sh, lego, Caddy, Traefik, модуль ACME в nginx; CA: Let's Encrypt, ZeroSSL, Google), сертификаты на IP
# (Let's Encrypt, 6 дней), бесплатные имена: Hetzner your-server.de, nip.io/sslip.io, traefik.me, ipq.co – IPv4 и IPv6.
# DNS-примеры проверены 2026-11-17 (DoH); про сервисы – по их страницам. Все 6 языков.

FREESSL = {
    "slug": "free-https-certbot-alternatives-nip-io-sslip-io-ip-certificates",
    "date": "2026-11-17",
    "tags": ["nginx", "certbot", "Let's Encrypt", "DNS", "systemd", "Odoo"],
    "code": {
        "install": ("bash · certbot with the nginx plugin", """# Debian / Ubuntu package (older certbot, but fine for domain names)
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d odoo.example.com -d www.odoo.example.com
#   finds the server block with this server_name, adds ssl_certificate + redirect 80 -> 443, reloads nginx

# newest certbot (needed e.g. for IP certificates: >= 5.4) – snap, as recommended by the certbot project
sudo apt remove certbot python3-certbot-nginx
sudo snap install --classic certbot && sudo ln -sf /snap/bin/certbot /usr/bin/certbot

# only get the certificate, do not touch the nginx config (nginx in Docker, own config management)
sudo certbot certonly --webroot -w /var/www/certbot -d odoo.example.com"""),
        "cron": ("/etc/cron.d/certbot-renew · variant 1: cron", """# twice a day at a random minute; renew does nothing until a certificate has < 30 days left
SHELL=/bin/bash
PATH=/usr/sbin:/usr/bin:/sbin:/bin
17 3,15 * * * root sleep $((RANDOM \\% 3600)); certbot renew -q --deploy-hook "systemctl reload nginx"

# note: % must be escaped as \\% in crontab; the Debian package already ships /etc/cron.d/certbot
# that runs only on systems WITHOUT systemd – there the certbot.timer does the job"""),
        "timer": ("/etc/systemd/system/certbot-renew.{service,timer} · variant 2: systemd", """# certbot-renew.service
[Unit]
Description=Renew Let's Encrypt certificates
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
ExecStart=/usr/bin/certbot renew -q --deploy-hook "systemctl reload nginx"

# certbot-renew.timer
[Unit]
Description=certbot renew twice a day

[Timer]
OnCalendar=*-*-* 03,15:17:00
RandomizedDelaySec=1h
Persistent=true            # missed while the server was off -> runs after boot

[Install]
WantedBy=timers.target

# activate and check
sudo systemctl daemon-reload && sudo systemctl enable --now certbot-renew.timer
systemctl list-timers | grep -i certbot     # do not run two timers: apt/snap already bring certbot.timer / snap.certbot.renew.timer
sudo certbot renew --dry-run                # rehearsal against the staging server
journalctl -u certbot-renew.service -n 50   # what happened last time"""),
        "ip": ("bash · certificate for an IP address (Let's Encrypt, valid 6 days)", """# certbot >= 5.4 for webroot; the nginx plugin cannot install IP certificates yet
sudo certbot certonly --preferred-profile shortlived \\
     --webroot -w /var/www/certbot --ip-address 203.0.113.10
sudo certbot certonly --preferred-profile shortlived \\
     --webroot -w /var/www/certbot --ip-address 2001:db8::10

# nginx: point to the files yourself
ssl_certificate     /etc/letsencrypt/live/203.0.113.10/fullchain.pem;
ssl_certificate_key /etc/letsencrypt/live/203.0.113.10/privkey.pem;

# 6 days -> renewal MUST be automatic, with a reload hook
sudo certbot reconfigure --cert-name 203.0.113.10 --deploy-hook "systemctl reload nginx\""""),
        "dns": ("DNS answers, checked on 2026-11-17", """name                                               A                AAAA
10.0.0.1.nip.io                                    10.0.0.1         -
10-0-0-1.nip.io                                    10.0.0.1         -
app.10.0.0.1.nip.io                                10.0.0.1         -
0a000001.nip.io  (hex)                             10.0.0.1         -
10-0-0-1.sslip.io                                  10.0.0.1         -
2a01-4f8-c17-b8f--2.sslip.io                       -                2a01:4f8:c17:b8f::2
2a01-4f8-c17-b8f--2.nip.io                         -                2a01:4f8:c17:b8f::2
10.0.0.1.traefik.me / 10-0-0-1.traefik.me          10.0.0.1         -
mysite.traefik.me  (no IP in the name)             127.0.0.1        -
static.137.100.245.188.clients.your-server.de      188.245.100.137  -
1.2.3.4.ipq.co                                     NXDOMAIN (ipq.co only knows names created in its web form)

# check yourself
dig +short 203-0-113-10.sslip.io
dig +short AAAA 2001-db8--10.sslip.io
getent hosts 10.0.0.1.nip.io"""),
        "demo": ("bash · Odoo demo on a fresh VPS with HTTPS, without a domain", """IP=203.0.113.10                      # public IPv4 of the server
NAME=odoo.${IP//./-}.sslip.io        # odoo.203-0-113-10.sslip.io
# nginx: server_name $NAME; proxy_pass to Odoo (see the Odoo + nginx article)
sudo certbot --nginx -d "$NAME" --non-interactive --agree-tos -m admin@example.com
curl -sI "https://$NAME/web/login" | head -1"""),
    },
    "links": [
        ("Blog: certbot – automatic renewal for nginx on the host and in Docker", "@blog:certbot-nginx-auto-renewal"),
        ("Blog: tools to check SSL certificate expiry", "@blog:ssl-certificate-expiry-check-tools"),
        ("Blog: Odoo with docker-compose, extra addons and nginx", "@blog:odoo-docker-compose-extra-addons-nginx"),
        ("Blog: nginx security audit in front of Odoo", "@blog:nginx-security-audit-odoo-hsts-cookies-x-frame-options"),
        ("Let's Encrypt: IP address and 6-day certificates", "https://letsencrypt.org/2026/01/15/6day-and-ip-general-availability"),
        ("Let's Encrypt: rate limits", "https://letsencrypt.org/docs/rate-limits/"),
        ("nip.io / sslip.io", "https://nip.io/"),
        ("traefik.me", "https://traefik.me/"),
        ("nginx: ngx_http_acme_module", "https://nginx.org/en/docs/http/ngx_http_acme_module.html"),
        ("acme.sh", "https://github.com/acmesh-official/acme.sh"),
        ("lego", "https://github.com/go-acme/lego"),
    ],
    "t": {},
}


def _f(title, summary, intro, note, h, cb_ul, ren_p, ren_ul, alt_tbl, alt_p, ip_p, ip_ul, dom_p, dom_tbl, use_ul, pit_ul, closing, links):
    return {"title": title, "summary": summary, "body": [
        ("p", intro), ("note", note),
        ("h", h[0]), ("code", "install"), ("ul", cb_ul),
        ("h", h[1]), ("p", ren_p), ("code", "cron"), ("code", "timer"), ("ul", ren_ul),
        ("h", h[2]), ("table", alt_tbl), ("p", alt_p),
        ("h", h[3]), ("p", ip_p), ("code", "ip"), ("ul", ip_ul),
        ("h", h[4]), ("p", dom_p), ("table", dom_tbl), ("code", "dns"),
        ("h", h[5]), ("ul", use_ul), ("code", "demo"),
        ("h", h[6]), ("ul", pit_ul),
        ("h", h[7]), ("p", closing),
        ("links", links)]}


FREESSL["t"]["en"] = _f(
    "Free HTTPS without your own domain: certbot, alternatives, nip.io, sslip.io and IP certificates",
    "certbot with python3-certbot-nginx, renewal by cron or by a systemd timer and service, free alternatives (acme.sh, lego, Caddy, Traefik, the ACME module of nginx), Let's Encrypt certificates for an IP address, and free host names – Hetzner your-server.de, nip.io, sslip.io, traefik.me, ipq.co – with IPv4 and IPv6 examples and which one is good for what.",
    "A test Odoo on a new server, a demo for a customer, a stage before the DNS is ready – HTTPS is needed from the first day, a domain not always. Here is what we use: certbot and its nginx plugin, two ways to renew automatically, the free alternatives, certificates directly for an IP address, and the free host names that point to any IP.",
    "Short version: `apt install certbot python3-certbot-nginx` + `certbot --nginx -d name` – done; renewal runs by `certbot.timer`, or by your own cron/timer with a deploy hook. No domain: `203-0-113-10.sslip.io` resolves to that IP and gets a normal Let's Encrypt certificate via HTTP-01. No name at all: a Let's Encrypt certificate for the IP itself (6 days, certbot ≥ 5.4). Names with private IPs (`192.168…nip.io`) cannot get a public certificate. Production needs your own domain.",
    ["certbot and python3-certbot-nginx", "Renewal: cron or systemd timer + service", "Free alternatives to certbot", "A certificate for an IP address",
     "Free host names: your-server.de, nip.io, sslip.io, traefik.me, ipq.co", "Which one for what", "Pitfalls", "Conclusion"],
    ["**`--nginx`** reads the nginx configuration, finds the `server` block by `server_name`, answers the HTTP-01 challenge through it, writes `ssl_certificate` and the redirect and reloads nginx. The `server_name` must already be in the config.",
     "**`certonly --webroot`** only gets the certificate: nginx serves `/.well-known/acme-challenge/` from a folder, and the config stays yours – the right choice for nginx in Docker or a config from git.",
     "**apt or snap.** The distribution package is older but updated with the system; the snap is always current. New features (IP certificates, profiles) need a current certbot.",
     "**Port 80 must be reachable from the internet** for HTTP-01 – also later, for every renewal. Closing 80 in the firewall breaks the renewal in 60 days."],
    "Let's Encrypt certificates live 90 days (shorter in the coming years), certbot renews when fewer than 30 days remain. Both packages already bring a timer – check it before adding your own. Your own cron or timer makes sense with a deploy hook (reload nginx or the Docker container only after a real renewal) or on systems where the package timer is missing.",
    ["**cron or timer?** Both work. The timer has `Persistent=true` (catches up after downtime), logs in `journalctl` and a random delay without tricks; cron is simpler and everywhere.",
     "**`--deploy-hook`** runs only after a certificate was actually renewed – no needless reloads twice a day. It is saved in `/etc/letsencrypt/renewal/<name>.conf`, so a later plain `certbot renew` keeps it.",
     "**Test**: `certbot renew --dry-run` makes a full rehearsal against the staging server without touching the real certificates."],
    [["Tool", "What it is", "When"],
     ["**acme.sh**", "a shell script, no dependencies; default CA is ZeroSSL, Let's Encrypt with `--server letsencrypt`; DNS APIs of ~150 providers; installs its own cron entry", "servers without Python, wildcards via DNS-01, routers and NAS"],
     ["**lego**", "one Go binary, HTTP-01, TLS-ALPN-01 and DNS-01 for many DNS providers", "CI, containers, wildcards"],
     ["**Caddy**", "web server with automatic HTTPS: certificates and renewal without any client", "new small setups instead of nginx"],
     ["**Traefik**", "reverse proxy for Docker with ACME built in (`certresolver`)", "many containers with labels"],
     ["**nginx ACME module**", "`ngx_http_acme_module`, official, package `nginx-module-acme` (nginx ≥ 1.29); HTTP-01, no wildcards", "nginx from nginx.org packages, without certbot"],
     ["**Other free CAs**", "ZeroSSL (ACME with EAB keys, created automatically by acme.sh), Google Trust Services (EAB from a Google Cloud project)", "a second CA as a fallback or for rate limits"]],
    "For Odoo behind nginx on Debian/Ubuntu, certbot with the nginx plugin is still the simplest: one package, one command, the timer is included. The others pay off for wildcards (DNS-01), in container setups or when you replace nginx anyway.",
    "Since January 2026 Let's Encrypt issues certificates for IPv4 and IPv6 addresses. They use the `shortlived` profile and are valid for 6 days; validation only by HTTP-01 or TLS-ALPN-01. certbot supports this from 5.3 (`--ip-address`), webroot with IP from 5.4; the nginx plugin cannot install them yet.",
    ["**6 days** – renewal must be automatic and must reload nginx; one missed weekend and the browser shows an error.",
     "**Good for** an admin panel, an API endpoint or a test server without a name. **Not for** Odoo users: cookies, links in e-mails and portal URLs belong to a name.",
     "**IPv6**: works the same way, the address is written as is (`--ip-address 2001:db8::10`)."],
    "Wildcard DNS services return the IP that is written in the host name. You need no account and no DNS setup – the name works immediately, and for a public IP a normal Let's Encrypt certificate (HTTP-01) can be issued for it.",
    [["Service", "IPv4", "IPv6", "Certificate"],
     ["**Hetzner** (rDNS of the server)", "`static.137.100.245.188.clients.your-server.de` → 188.245.100.137 (octets reversed)", "no default name", "HTTP-01 works; the rate limit of `your-server.de` is shared with all Hetzner customers"],
     ["**nip.io**", "`10.0.0.1.nip.io`, `10-0-0-1.nip.io`, `app.10-0-0-1.nip.io`, hex `0a000001.nip.io`", "`2a01-4f8-c17-b8f--2.nip.io` (dashes, `--` = `::`)", "HTTP-01 for public IPs, no wildcard"],
     ["**sslip.io**", "the same formats: `203-0-113-10.sslip.io`", "`2001-db8--10.sslip.io`", "same as nip.io – the same operators; if one domain hits a limit, use the other"],
     ["**traefik.me**", "`10.0.0.1.traefik.me`, `10-0-0-1.traefik.me`; any other name → 127.0.0.1", "not documented", "the free wildcard certificate download was discontinued in 2025 (its private key was public anyway)"],
     ["**ipq.co**", "no IP in the name: you choose `myname.ipq.co` (or `fdns.uk`) in a web form and give the IP", "not documented", "a normal A record → HTTP-01; record updates are not implemented yet"]],
    ["**A demo or test of Odoo on a fresh VPS** – `odoo.<ip-with-dashes>.sslip.io` + `certbot --nginx`: valid HTTPS in two minutes, before the customer's DNS exists.",
     "**Local network, Docker on the laptop** – `app.192-168-1-20.nip.io` gives names to containers without `/etc/hosts`. A public certificate is impossible (Let's Encrypt cannot reach a private IP, and DNS-01 needs control of the zone) – use `mkcert` or self-signed. Routers with DNS rebind protection (FRITZ!Box, dnsmasq, pfSense) block answers with private IPs – add the domain to the exceptions.",
     "**Hetzner name** – fine for a few days; the name changes with the IP, and the shared rate limit can stop you on a busy day.",
     "**ipq.co** – when you want a short readable name without your own domain; an old one-person service – not for anything important.",
     "**Production** – your own domain. It costs a few euros a year, survives a server move, and e-mails, cookies, SPF/DKIM and the trust of users depend on it."],
    ["**Rate limits** of Let's Encrypt: 50 certificates per registered domain per week and 5 for the same set of names. nip.io, sslip.io and your-server.de are not on the Public Suffix List – thousands of users share these limits.",
     "**Everything is public**: each issued certificate lands in the Certificate Transparency logs (crt.sh). The name `odoo.203-0-113-10.sslip.io` tells everybody the IP of your test Odoo – close it with a password or an IP filter.",
     "**AAAA first**: if the name has an IPv6 address, Let's Encrypt validates over IPv6. A wrong or unreachable AAAA record breaks the validation even when IPv4 is fine.",
     "**Wildcards** (`*.example.com`) only with DNS-01 – not with nip.io and the like, only on your own domain with a DNS API (acme.sh, lego, certbot DNS plugins).",
     "**Two timers** (package + your own) are harmless – certbot locks itself – but confusing; keep one."],
    "For a quick test a name from sslip.io or nip.io plus certbot is enough – real HTTPS in minutes, no domain. For an IP without a name there are now 6-day certificates. For production Odoo – a domain, certbot or an alternative, automatic renewal with a reload hook and an expiry check. We set this up for Odoo installations of companies in Germany, Austria and Switzerland.",
    "Links")

FREESSL["t"]["de"] = _f(
    "Kostenloses HTTPS ohne eigene Domain: certbot, Alternativen, nip.io, sslip.io und IP-Zertifikate",
    "certbot mit python3-certbot-nginx, Verlängerung per cron oder systemd-Timer und -Service, kostenlose Alternativen (acme.sh, lego, Caddy, Traefik, das ACME-Modul von nginx), Let's-Encrypt-Zertifikate für eine IP-Adresse und kostenlose Hostnamen – Hetzner your-server.de, nip.io, sslip.io, traefik.me, ipq.co – mit Beispielen für IPv4 und IPv6 und wofür welcher taugt.",
    "Ein Test-Odoo auf einem neuen Server, eine Demo für einen Kunden, eine Stage, bevor das DNS steht – HTTPS braucht man ab dem ersten Tag, eine Domain nicht immer. Hier, was wir nutzen: certbot und sein nginx-Plugin, zwei Wege zur automatischen Verlängerung, die kostenlosen Alternativen, Zertifikate direkt für eine IP-Adresse und die kostenlosen Hostnamen, die auf jede IP zeigen.",
    "Kurzfassung: `apt install certbot python3-certbot-nginx` + `certbot --nginx -d name` – fertig; verlängert wird über `certbot.timer` oder einen eigenen cron/Timer mit Deploy-Hook. Keine Domain: `203-0-113-10.sslip.io` löst auf diese IP auf und bekommt per HTTP-01 ein normales Let's-Encrypt-Zertifikat. Gar kein Name: ein Let's-Encrypt-Zertifikat für die IP selbst (6 Tage, certbot ≥ 5.4). Namen mit privaten IPs (`192.168…nip.io`) bekommen kein öffentliches Zertifikat. Für die Produktion braucht man eine eigene Domain.",
    ["certbot und python3-certbot-nginx", "Verlängerung: cron oder systemd-Timer + Service", "Kostenlose Alternativen zu certbot", "Ein Zertifikat für eine IP-Adresse",
     "Kostenlose Hostnamen: your-server.de, nip.io, sslip.io, traefik.me, ipq.co", "Was wofür", "Fallstricke", "Fazit"],
    ["**`--nginx`** liest die nginx-Konfiguration, findet den `server`-Block über `server_name`, beantwortet darüber die HTTP-01-Challenge, schreibt `ssl_certificate` und die Weiterleitung und lädt nginx neu. Der `server_name` muss schon in der Konfiguration stehen.",
     "**`certonly --webroot`** holt nur das Zertifikat: nginx liefert `/.well-known/acme-challenge/` aus einem Ordner, die Konfiguration bleibt Ihre – richtig für nginx in Docker oder eine Konfiguration aus git.",
     "**apt oder snap.** Das Distributionspaket ist älter, wird aber mit dem System aktualisiert; das Snap ist immer aktuell. Neue Funktionen (IP-Zertifikate, Profile) brauchen ein aktuelles certbot.",
     "**Port 80 muss aus dem Internet erreichbar sein** für HTTP-01 – auch später, bei jeder Verlängerung. Port 80 in der Firewall zu schließen, bricht die Verlängerung in 60 Tagen."],
    "Let's-Encrypt-Zertifikate gelten 90 Tage (in den nächsten Jahren kürzer), certbot verlängert, wenn weniger als 30 Tage übrig sind. Beide Pakete bringen bereits einen Timer mit – erst prüfen, dann einen eigenen anlegen. Ein eigener cron oder Timer lohnt sich mit Deploy-Hook (nginx oder den Docker-Container nur nach echter Verlängerung neu laden) oder auf Systemen ohne Paket-Timer.",
    ["**cron oder Timer?** Beides funktioniert. Der Timer hat `Persistent=true` (holt nach einer Ausfallzeit nach), loggt ins `journalctl` und verzögert zufällig ohne Tricks; cron ist einfacher und überall vorhanden.",
     "**`--deploy-hook`** läuft nur, wenn ein Zertifikat tatsächlich verlängert wurde – kein unnötiges Neuladen zweimal am Tag. Er wird in `/etc/letsencrypt/renewal/<name>.conf` gespeichert, ein späteres einfaches `certbot renew` behält ihn.",
     "**Test**: `certbot renew --dry-run` macht eine vollständige Probe gegen den Staging-Server, ohne die echten Zertifikate anzufassen."],
    [["Werkzeug", "Was es ist", "Wann"],
     ["**acme.sh**", "ein Shell-Skript ohne Abhängigkeiten; Standard-CA ist ZeroSSL, Let's Encrypt mit `--server letsencrypt`; DNS-APIs von rund 150 Anbietern; legt einen eigenen cron-Eintrag an", "Server ohne Python, Wildcards per DNS-01, Router und NAS"],
     ["**lego**", "eine Go-Binärdatei, HTTP-01, TLS-ALPN-01 und DNS-01 für viele DNS-Anbieter", "CI, Container, Wildcards"],
     ["**Caddy**", "Webserver mit automatischem HTTPS: Zertifikate und Verlängerung ohne Client", "neue kleine Setups statt nginx"],
     ["**Traefik**", "Reverse Proxy für Docker mit eingebautem ACME (`certresolver`)", "viele Container mit Labels"],
     ["**nginx-ACME-Modul**", "`ngx_http_acme_module`, offiziell, Paket `nginx-module-acme` (nginx ≥ 1.29); HTTP-01, keine Wildcards", "nginx aus den nginx.org-Paketen, ohne certbot"],
     ["**Weitere kostenlose CAs**", "ZeroSSL (ACME mit EAB-Schlüsseln, die acme.sh automatisch anlegt), Google Trust Services (EAB aus einem Google-Cloud-Projekt)", "eine zweite CA als Rückfall oder wegen Ratenlimits"]],
    "Für Odoo hinter nginx auf Debian/Ubuntu ist certbot mit dem nginx-Plugin immer noch am einfachsten: ein Paket, ein Befehl, der Timer ist dabei. Die anderen lohnen sich für Wildcards (DNS-01), in Container-Setups oder wenn man nginx ohnehin ersetzt.",
    "Seit Januar 2026 stellt Let's Encrypt Zertifikate für IPv4- und IPv6-Adressen aus. Sie nutzen das Profil `shortlived` und gelten 6 Tage; Validierung nur per HTTP-01 oder TLS-ALPN-01. certbot unterstützt das ab 5.3 (`--ip-address`), Webroot mit IP ab 5.4; das nginx-Plugin kann sie noch nicht installieren.",
    ["**6 Tage** – die Verlängerung muss automatisch laufen und nginx neu laden; ein verpasstes Wochenende, und der Browser zeigt einen Fehler.",
     "**Gut für** ein Admin-Panel, einen API-Endpunkt oder einen Testserver ohne Namen. **Nicht für** Odoo-Anwender: Cookies, Links in E-Mails und Portal-URLs gehören zu einem Namen.",
     "**IPv6**: funktioniert genauso, die Adresse wird wie sie ist geschrieben (`--ip-address 2001:db8::10`)."],
    "Wildcard-DNS-Dienste liefern die IP zurück, die im Hostnamen steht. Kein Konto, keine DNS-Einrichtung – der Name funktioniert sofort, und für eine öffentliche IP lässt sich dafür ein normales Let's-Encrypt-Zertifikat (HTTP-01) ausstellen.",
    [["Dienst", "IPv4", "IPv6", "Zertifikat"],
     ["**Hetzner** (rDNS des Servers)", "`static.137.100.245.188.clients.your-server.de` → 188.245.100.137 (Oktette umgekehrt)", "kein Standardname", "HTTP-01 funktioniert; das Ratenlimit von `your-server.de` teilen sich alle Hetzner-Kunden"],
     ["**nip.io**", "`10.0.0.1.nip.io`, `10-0-0-1.nip.io`, `app.10-0-0-1.nip.io`, hex `0a000001.nip.io`", "`2a01-4f8-c17-b8f--2.nip.io` (Bindestriche, `--` = `::`)", "HTTP-01 für öffentliche IPs, keine Wildcards"],
     ["**sslip.io**", "dieselben Formate: `203-0-113-10.sslip.io`", "`2001-db8--10.sslip.io`", "wie nip.io – dieselben Betreiber; stößt eine Domain an ein Limit, die andere nehmen"],
     ["**traefik.me**", "`10.0.0.1.traefik.me`, `10-0-0-1.traefik.me`; jeder andere Name → 127.0.0.1", "nicht dokumentiert", "der kostenlose Download eines Wildcard-Zertifikats wurde 2025 eingestellt (sein privater Schlüssel war ohnehin öffentlich)"],
     ["**ipq.co**", "keine IP im Namen: man wählt `meinname.ipq.co` (oder `fdns.uk`) in einem Webformular und gibt die IP an", "nicht dokumentiert", "ein normaler A-Record → HTTP-01; Änderungen des Eintrags sind noch nicht umgesetzt"]],
    ["**Demo oder Test von Odoo auf einem frischen VPS** – `odoo.<ip-mit-bindestrichen>.sslip.io` + `certbot --nginx`: gültiges HTTPS in zwei Minuten, bevor das DNS des Kunden existiert.",
     "**Lokales Netz, Docker auf dem Laptop** – `app.192-168-1-20.nip.io` gibt Containern Namen ohne `/etc/hosts`. Ein öffentliches Zertifikat ist unmöglich (Let's Encrypt erreicht keine private IP, und DNS-01 braucht die Kontrolle über die Zone) – `mkcert` oder selbst signiert nutzen. Router mit DNS-Rebind-Schutz (FRITZ!Box, dnsmasq, pfSense) blockieren Antworten mit privaten IPs – die Domain zu den Ausnahmen hinzufügen.",
     "**Hetzner-Name** – für ein paar Tage in Ordnung; der Name ändert sich mit der IP, und das geteilte Ratenlimit kann an einem vollen Tag bremsen.",
     "**ipq.co** – wenn man einen kurzen lesbaren Namen ohne eigene Domain will; ein alter Ein-Personen-Dienst – für nichts Wichtiges.",
     "**Produktion** – eine eigene Domain. Sie kostet ein paar Euro im Jahr, überlebt einen Serverumzug, und E-Mails, Cookies, SPF/DKIM und das Vertrauen der Anwender hängen daran."],
    ["**Ratenlimits** von Let's Encrypt: 50 Zertifikate pro registrierter Domain und Woche und 5 für dieselbe Namensmenge. nip.io, sslip.io und your-server.de stehen nicht auf der Public Suffix List – Tausende Nutzer teilen sich diese Limits.",
     "**Alles ist öffentlich**: jedes ausgestellte Zertifikat landet in den Certificate-Transparency-Logs (crt.sh). Der Name `odoo.203-0-113-10.sslip.io` verrät jedem die IP Ihres Test-Odoo – mit Passwort oder IP-Filter schützen.",
     "**Zuerst AAAA**: hat der Name eine IPv6-Adresse, validiert Let's Encrypt über IPv6. Ein falscher oder unerreichbarer AAAA-Record bricht die Validierung, auch wenn IPv4 stimmt.",
     "**Wildcards** (`*.example.com`) nur per DNS-01 – nicht mit nip.io und Co., nur auf der eigenen Domain mit DNS-API (acme.sh, lego, certbot-DNS-Plugins).",
     "**Zwei Timer** (Paket + eigener) sind harmlos – certbot sperrt sich selbst –, aber verwirrend; einen behalten."],
    "Für einen schnellen Test reicht ein Name von sslip.io oder nip.io plus certbot – echtes HTTPS in Minuten, ohne Domain. Für eine IP ohne Namen gibt es jetzt 6-Tage-Zertifikate. Für produktives Odoo – eine Domain, certbot oder eine Alternative, automatische Verlängerung mit Reload-Hook und eine Ablaufprüfung. Das richten wir für Odoo-Installationen von Unternehmen in Deutschland, Österreich und der Schweiz ein.",
    "Links")

FREESSL["t"]["fr"] = _f(
    "HTTPS gratuit sans domaine à soi : certbot, alternatives, nip.io, sslip.io et certificats pour IP",
    "certbot avec python3-certbot-nginx, renouvellement par cron ou par un timer et un service systemd, alternatives gratuites (acme.sh, lego, Caddy, Traefik, le module ACME de nginx), certificats Let's Encrypt pour une adresse IP, et noms d'hôte gratuits – Hetzner your-server.de, nip.io, sslip.io, traefik.me, ipq.co – avec des exemples IPv4 et IPv6 et l'usage de chacun.",
    "Un Odoo de test sur un nouveau serveur, une démo pour un client, un stage avant que le DNS soit prêt – le HTTPS est nécessaire dès le premier jour, un domaine pas toujours. Voici ce que nous utilisons : certbot et son plugin nginx, deux façons de renouveler automatiquement, les alternatives gratuites, des certificats directement pour une adresse IP, et les noms d'hôte gratuits qui pointent vers n'importe quelle IP.",
    "En bref : `apt install certbot python3-certbot-nginx` + `certbot --nginx -d nom` – c'est fait ; le renouvellement passe par `certbot.timer` ou par votre propre cron/timer avec un deploy hook. Pas de domaine : `203-0-113-10.sslip.io` pointe vers cette IP et obtient un certificat Let's Encrypt normal par HTTP-01. Aucun nom : un certificat Let's Encrypt pour l'IP elle-même (6 jours, certbot ≥ 5.4). Les noms avec IP privées (`192.168…nip.io`) ne peuvent pas avoir de certificat public. La production demande un domaine à soi.",
    ["certbot et python3-certbot-nginx", "Renouvellement : cron ou timer + service systemd", "Alternatives gratuites à certbot", "Un certificat pour une adresse IP",
     "Noms d'hôte gratuits : your-server.de, nip.io, sslip.io, traefik.me, ipq.co", "Lequel pour quoi", "Pièges", "Conclusion"],
    ["**`--nginx`** lit la configuration nginx, trouve le bloc `server` par `server_name`, y répond au défi HTTP-01, écrit `ssl_certificate` et la redirection et recharge nginx. Le `server_name` doit déjà être dans la configuration.",
     "**`certonly --webroot`** obtient seulement le certificat : nginx sert `/.well-known/acme-challenge/` depuis un dossier, et la configuration reste la vôtre – le bon choix pour nginx dans Docker ou une configuration dans git.",
     "**apt ou snap.** Le paquet de la distribution est plus ancien mais mis à jour avec le système ; le snap est toujours à jour. Les nouveautés (certificats IP, profils) demandent un certbot récent.",
     "**Le port 80 doit être joignable depuis Internet** pour HTTP-01 – aussi plus tard, à chaque renouvellement. Fermer le 80 dans le pare-feu casse le renouvellement dans 60 jours."],
    "Les certificats Let's Encrypt durent 90 jours (moins dans les années à venir), certbot les renouvelle quand il reste moins de 30 jours. Les deux paquets installent déjà un timer – le vérifier avant d'en ajouter un. Un cron ou un timer à vous a du sens avec un deploy hook (recharger nginx ou le conteneur Docker seulement après un vrai renouvellement) ou sur les systèmes sans timer de paquet.",
    ["**cron ou timer ?** Les deux fonctionnent. Le timer a `Persistent=true` (rattrape après un arrêt), journalise dans `journalctl` et a un délai aléatoire sans astuce ; cron est plus simple et partout.",
     "**`--deploy-hook`** ne s'exécute qu'après un vrai renouvellement – pas de rechargement inutile deux fois par jour. Il est enregistré dans `/etc/letsencrypt/renewal/<nom>.conf`, un simple `certbot renew` ultérieur le garde.",
     "**Test** : `certbot renew --dry-run` fait une répétition complète contre le serveur de staging sans toucher aux vrais certificats."],
    [["Outil", "Ce que c'est", "Quand"],
     ["**acme.sh**", "un script shell sans dépendances ; CA par défaut ZeroSSL, Let's Encrypt avec `--server letsencrypt` ; API DNS d'environ 150 fournisseurs ; installe sa propre entrée cron", "serveurs sans Python, wildcards par DNS-01, routeurs et NAS"],
     ["**lego**", "un binaire Go, HTTP-01, TLS-ALPN-01 et DNS-01 pour de nombreux fournisseurs DNS", "CI, conteneurs, wildcards"],
     ["**Caddy**", "serveur web avec HTTPS automatique : certificats et renouvellement sans client", "nouvelles petites installations à la place de nginx"],
     ["**Traefik**", "reverse proxy pour Docker avec ACME intégré (`certresolver`)", "beaucoup de conteneurs avec des labels"],
     ["**Module ACME de nginx**", "`ngx_http_acme_module`, officiel, paquet `nginx-module-acme` (nginx ≥ 1.29) ; HTTP-01, pas de wildcard", "nginx des paquets nginx.org, sans certbot"],
     ["**Autres CA gratuites**", "ZeroSSL (ACME avec clés EAB, créées automatiquement par acme.sh), Google Trust Services (EAB depuis un projet Google Cloud)", "une deuxième CA en secours ou à cause des limites"]],
    "Pour Odoo derrière nginx sur Debian/Ubuntu, certbot avec le plugin nginx reste le plus simple : un paquet, une commande, le timer est inclus. Les autres valent la peine pour les wildcards (DNS-01), dans les environnements à conteneurs ou quand on remplace nginx de toute façon.",
    "Depuis janvier 2026, Let's Encrypt émet des certificats pour des adresses IPv4 et IPv6. Ils utilisent le profil `shortlived` et sont valables 6 jours ; validation seulement par HTTP-01 ou TLS-ALPN-01. certbot le gère depuis la 5.3 (`--ip-address`), le webroot avec IP depuis la 5.4 ; le plugin nginx ne sait pas encore les installer.",
    ["**6 jours** – le renouvellement doit être automatique et recharger nginx ; un week-end manqué et le navigateur affiche une erreur.",
     "**Bien pour** un panneau d'administration, un point d'accès API ou un serveur de test sans nom. **Pas pour** les utilisateurs d'Odoo : les cookies, les liens des e-mails et les URL du portail appartiennent à un nom.",
     "**IPv6** : fonctionne de la même façon, l'adresse s'écrit telle quelle (`--ip-address 2001:db8::10`)."],
    "Les services DNS wildcard renvoient l'IP écrite dans le nom d'hôte. Pas de compte, pas de configuration DNS – le nom marche tout de suite, et pour une IP publique on peut obtenir un certificat Let's Encrypt normal (HTTP-01).",
    [["Service", "IPv4", "IPv6", "Certificat"],
     ["**Hetzner** (rDNS du serveur)", "`static.137.100.245.188.clients.your-server.de` → 188.245.100.137 (octets inversés)", "pas de nom par défaut", "HTTP-01 fonctionne ; la limite de `your-server.de` est partagée par tous les clients Hetzner"],
     ["**nip.io**", "`10.0.0.1.nip.io`, `10-0-0-1.nip.io`, `app.10-0-0-1.nip.io`, hexa `0a000001.nip.io`", "`2a01-4f8-c17-b8f--2.nip.io` (tirets, `--` = `::`)", "HTTP-01 pour les IP publiques, pas de wildcard"],
     ["**sslip.io**", "les mêmes formats : `203-0-113-10.sslip.io`", "`2001-db8--10.sslip.io`", "comme nip.io – les mêmes opérateurs ; si un domaine atteint une limite, prendre l'autre"],
     ["**traefik.me**", "`10.0.0.1.traefik.me`, `10-0-0-1.traefik.me` ; tout autre nom → 127.0.0.1", "non documenté", "le téléchargement gratuit d'un certificat wildcard a cessé en 2025 (sa clé privée était de toute façon publique)"],
     ["**ipq.co**", "pas d'IP dans le nom : on choisit `monnom.ipq.co` (ou `fdns.uk`) dans un formulaire web et on donne l'IP", "non documenté", "un enregistrement A normal → HTTP-01 ; la modification de l'enregistrement n'est pas encore disponible"]],
    ["**Démo ou test d'Odoo sur un VPS neuf** – `odoo.<ip-avec-tirets>.sslip.io` + `certbot --nginx` : un HTTPS valide en deux minutes, avant que le DNS du client existe.",
     "**Réseau local, Docker sur le portable** – `app.192-168-1-20.nip.io` donne des noms aux conteneurs sans `/etc/hosts`. Un certificat public est impossible (Let's Encrypt ne joint pas une IP privée, et DNS-01 exige le contrôle de la zone) – utiliser `mkcert` ou un certificat auto-signé. Les routeurs avec protection contre le DNS rebinding (FRITZ!Box, dnsmasq, pfSense) bloquent les réponses avec IP privées – ajouter le domaine aux exceptions.",
     "**Nom Hetzner** – correct pour quelques jours ; le nom change avec l'IP, et la limite partagée peut bloquer un jour chargé.",
     "**ipq.co** – quand on veut un nom court et lisible sans domaine à soi ; un vieux service tenu par une personne – pour rien d'important.",
     "**Production** – un domaine à soi. Il coûte quelques euros par an, survit à un déménagement de serveur, et les e-mails, les cookies, SPF/DKIM et la confiance des utilisateurs en dépendent."],
    ["**Limites** de Let's Encrypt : 50 certificats par domaine enregistré et par semaine, et 5 pour le même ensemble de noms. nip.io, sslip.io et your-server.de ne sont pas sur la Public Suffix List – des milliers d'utilisateurs se partagent ces limites.",
     "**Tout est public** : chaque certificat émis arrive dans les journaux Certificate Transparency (crt.sh). Le nom `odoo.203-0-113-10.sslip.io` donne à tout le monde l'IP de votre Odoo de test – le protéger par mot de passe ou filtre IP.",
     "**AAAA d'abord** : si le nom a une adresse IPv6, Let's Encrypt valide en IPv6. Un enregistrement AAAA faux ou injoignable fait échouer la validation même si l'IPv4 est correcte.",
     "**Wildcards** (`*.example.com`) seulement par DNS-01 – pas avec nip.io et consorts, uniquement sur votre domaine avec une API DNS (acme.sh, lego, plugins DNS de certbot).",
     "**Deux timers** (paquet + le vôtre) sont sans danger – certbot se verrouille lui-même – mais déroutants ; en garder un."],
    "Pour un test rapide, un nom de sslip.io ou nip.io plus certbot suffit – un vrai HTTPS en quelques minutes, sans domaine. Pour une IP sans nom, il y a désormais les certificats de 6 jours. Pour un Odoo en production – un domaine, certbot ou une alternative, un renouvellement automatique avec hook de rechargement et une surveillance de l'expiration. Nous mettons cela en place pour les installations Odoo d'entreprises en Allemagne, en Autriche et en Suisse.",
    "Liens")

FREESSL["t"]["el"] = _f(
    "Δωρεάν HTTPS χωρίς δικό σας domain: certbot, εναλλακτικές, nip.io, sslip.io και πιστοποιητικά για IP",
    "certbot με python3-certbot-nginx, ανανέωση με cron ή με systemd timer και service, δωρεάν εναλλακτικές (acme.sh, lego, Caddy, Traefik, το module ACME του nginx), πιστοποιητικά Let's Encrypt για διεύθυνση IP, και δωρεάν ονόματα host – Hetzner your-server.de, nip.io, sslip.io, traefik.me, ipq.co – με παραδείγματα IPv4 και IPv6 και ποιο για τι.",
    "Ένα δοκιμαστικό Odoo σε νέο server, μια επίδειξη για πελάτη, ένα stage πριν είναι έτοιμο το DNS – το HTTPS χρειάζεται από την πρώτη μέρα, ένα domain όχι πάντα. Αυτά χρησιμοποιούμε: certbot και το plugin του για nginx, δύο τρόποι αυτόματης ανανέωσης, οι δωρεάν εναλλακτικές, πιστοποιητικά απευθείας για διεύθυνση IP και τα δωρεάν ονόματα host που δείχνουν σε οποιαδήποτε IP.",
    "Συνοπτικά: `apt install certbot python3-certbot-nginx` + `certbot --nginx -d όνομα` – τέλος· η ανανέωση γίνεται από το `certbot.timer` ή από δικό σας cron/timer με deploy hook. Χωρίς domain: το `203-0-113-10.sslip.io` επιλύεται σε αυτή την IP και παίρνει κανονικό πιστοποιητικό Let's Encrypt μέσω HTTP-01. Χωρίς κανένα όνομα: πιστοποιητικό Let's Encrypt για την ίδια την IP (6 ημέρες, certbot ≥ 5.4). Ονόματα με ιδιωτικές IP (`192.168…nip.io`) δεν μπορούν να πάρουν δημόσιο πιστοποιητικό. Η παραγωγή χρειάζεται δικό σας domain.",
    ["certbot και python3-certbot-nginx", "Ανανέωση: cron ή systemd timer + service", "Δωρεάν εναλλακτικές του certbot", "Πιστοποιητικό για διεύθυνση IP",
     "Δωρεάν ονόματα host: your-server.de, nip.io, sslip.io, traefik.me, ipq.co", "Ποιο για τι", "Παγίδες", "Συμπέρασμα"],
    ["Το **`--nginx`** διαβάζει τη ρύθμιση του nginx, βρίσκει το μπλοκ `server` από το `server_name`, απαντά μέσω αυτού στην πρόκληση HTTP-01, γράφει `ssl_certificate` και την ανακατεύθυνση και φορτώνει ξανά το nginx. Το `server_name` πρέπει να υπάρχει ήδη στη ρύθμιση.",
     "Το **`certonly --webroot`** παίρνει μόνο το πιστοποιητικό: το nginx σερβίρει το `/.well-known/acme-challenge/` από έναν φάκελο και η ρύθμιση μένει δική σας – η σωστή επιλογή για nginx σε Docker ή ρύθμιση από git.",
     "**apt ή snap.** Το πακέτο της διανομής είναι παλαιότερο αλλά ενημερώνεται με το σύστημα· το snap είναι πάντα τρέχον. Οι νέες δυνατότητες (πιστοποιητικά IP, προφίλ) χρειάζονται πρόσφατο certbot.",
     "**Η θύρα 80 πρέπει να είναι προσβάσιμη από το internet** για το HTTP-01 – και αργότερα, σε κάθε ανανέωση. Αν κλείσετε την 80 στο firewall, η ανανέωση σπάει σε 60 ημέρες."],
    "Τα πιστοποιητικά Let's Encrypt διαρκούν 90 ημέρες (λιγότερο τα επόμενα χρόνια) και το certbot τα ανανεώνει όταν μένουν λιγότερες από 30 ημέρες. Και τα δύο πακέτα φέρνουν ήδη timer – ελέγξτε τον πριν προσθέσετε δικό σας. Δικό σας cron ή timer έχει νόημα με deploy hook (επαναφόρτωση του nginx ή του container Docker μόνο μετά από πραγματική ανανέωση) ή σε συστήματα χωρίς timer πακέτου.",
    ["**cron ή timer;** Λειτουργούν και τα δύο. Ο timer έχει `Persistent=true` (καλύπτει μετά από διακοπή), καταγράφει στο `journalctl` και έχει τυχαία καθυστέρηση χωρίς κόλπα· το cron είναι απλούστερο και υπάρχει παντού.",
     "Το **`--deploy-hook`** τρέχει μόνο αφού ανανεωθεί πραγματικά ένα πιστοποιητικό – χωρίς άσκοπες επαναφορτώσεις δύο φορές τη μέρα. Αποθηκεύεται στο `/etc/letsencrypt/renewal/<όνομα>.conf`, άρα ένα απλό `certbot renew` αργότερα το κρατά.",
     "**Δοκιμή**: το `certbot renew --dry-run` κάνει πλήρη πρόβα στον server staging χωρίς να αγγίξει τα πραγματικά πιστοποιητικά."],
    [["Εργαλείο", "Τι είναι", "Πότε"],
     ["**acme.sh**", "script shell χωρίς εξαρτήσεις· προεπιλεγμένη CA η ZeroSSL, Let's Encrypt με `--server letsencrypt`· DNS API από ~150 παρόχους· εγκαθιστά δική του εγγραφή cron", "servers χωρίς Python, wildcards μέσω DNS-01, routers και NAS"],
     ["**lego**", "ένα εκτελέσιμο Go, HTTP-01, TLS-ALPN-01 και DNS-01 για πολλούς παρόχους DNS", "CI, containers, wildcards"],
     ["**Caddy**", "web server με αυτόματο HTTPS: πιστοποιητικά και ανανέωση χωρίς client", "νέες μικρές εγκαταστάσεις αντί για nginx"],
     ["**Traefik**", "reverse proxy για Docker με ενσωματωμένο ACME (`certresolver`)", "πολλά containers με labels"],
     ["**Module ACME του nginx**", "`ngx_http_acme_module`, επίσημο, πακέτο `nginx-module-acme` (nginx ≥ 1.29)· HTTP-01, χωρίς wildcards", "nginx από τα πακέτα του nginx.org, χωρίς certbot"],
     ["**Άλλες δωρεάν CA**", "ZeroSSL (ACME με κλειδιά EAB, που τα δημιουργεί αυτόματα το acme.sh), Google Trust Services (EAB από έργο Google Cloud)", "δεύτερη CA ως εφεδρεία ή λόγω ορίων"]],
    "Για Odoo πίσω από nginx σε Debian/Ubuntu, το certbot με το plugin του nginx παραμένει το απλούστερο: ένα πακέτο, μία εντολή, ο timer περιλαμβάνεται. Τα άλλα αξίζουν για wildcards (DNS-01), σε περιβάλλοντα containers ή όταν αντικαθιστάτε ούτως ή άλλως το nginx.",
    "Από τον Ιανουάριο του 2026 η Let's Encrypt εκδίδει πιστοποιητικά για διευθύνσεις IPv4 και IPv6. Χρησιμοποιούν το προφίλ `shortlived` και ισχύουν 6 ημέρες· επικύρωση μόνο με HTTP-01 ή TLS-ALPN-01. Το certbot το υποστηρίζει από την 5.3 (`--ip-address`), το webroot με IP από την 5.4· το plugin του nginx δεν μπορεί ακόμη να τα εγκαταστήσει.",
    ["**6 ημέρες** – η ανανέωση πρέπει να είναι αυτόματη και να φορτώνει ξανά το nginx· ένα χαμένο Σαββατοκύριακο και ο browser δείχνει σφάλμα.",
     "**Καλό για** πίνακα διαχείρισης, endpoint API ή δοκιμαστικό server χωρίς όνομα. **Όχι για** τους χρήστες του Odoo: cookies, σύνδεσμοι σε e-mails και URL του portal ανήκουν σε όνομα.",
     "**IPv6**: λειτουργεί με τον ίδιο τρόπο, η διεύθυνση γράφεται όπως είναι (`--ip-address 2001:db8::10`)."],
    "Οι υπηρεσίες wildcard DNS επιστρέφουν την IP που είναι γραμμένη στο όνομα host. Χωρίς λογαριασμό, χωρίς ρύθμιση DNS – το όνομα δουλεύει αμέσως, και για δημόσια IP μπορεί να εκδοθεί κανονικό πιστοποιητικό Let's Encrypt (HTTP-01).",
    [["Υπηρεσία", "IPv4", "IPv6", "Πιστοποιητικό"],
     ["**Hetzner** (rDNS του server)", "`static.137.100.245.188.clients.your-server.de` → 188.245.100.137 (ανεστραμμένα οκτάδια)", "χωρίς προεπιλεγμένο όνομα", "το HTTP-01 λειτουργεί· το όριο του `your-server.de` το μοιράζονται όλοι οι πελάτες της Hetzner"],
     ["**nip.io**", "`10.0.0.1.nip.io`, `10-0-0-1.nip.io`, `app.10-0-0-1.nip.io`, hex `0a000001.nip.io`", "`2a01-4f8-c17-b8f--2.nip.io` (παύλες, `--` = `::`)", "HTTP-01 για δημόσιες IP, χωρίς wildcard"],
     ["**sslip.io**", "οι ίδιες μορφές: `203-0-113-10.sslip.io`", "`2001-db8--10.sslip.io`", "όπως το nip.io – οι ίδιοι διαχειριστές· αν ένα domain φτάσει σε όριο, χρησιμοποιήστε το άλλο"],
     ["**traefik.me**", "`10.0.0.1.traefik.me`, `10-0-0-1.traefik.me`· κάθε άλλο όνομα → 127.0.0.1", "δεν τεκμηριώνεται", "η δωρεάν λήψη wildcard πιστοποιητικού σταμάτησε το 2025 (το ιδιωτικό του κλειδί ήταν έτσι κι αλλιώς δημόσιο)"],
     ["**ipq.co**", "χωρίς IP στο όνομα: επιλέγετε `toonomamou.ipq.co` (ή `fdns.uk`) σε φόρμα web και δίνετε την IP", "δεν τεκμηριώνεται", "κανονική εγγραφή A → HTTP-01· η αλλαγή της εγγραφής δεν έχει υλοποιηθεί ακόμη"]],
    ["**Επίδειξη ή δοκιμή του Odoo σε νέο VPS** – `odoo.<ip-με-παύλες>.sslip.io` + `certbot --nginx`: έγκυρο HTTPS σε δύο λεπτά, πριν υπάρξει το DNS του πελάτη.",
     "**Τοπικό δίκτυο, Docker στο laptop** – το `app.192-168-1-20.nip.io` δίνει ονόματα στα containers χωρίς `/etc/hosts`. Δημόσιο πιστοποιητικό είναι αδύνατο (η Let's Encrypt δεν φτάνει σε ιδιωτική IP, και το DNS-01 απαιτεί έλεγχο της ζώνης) – χρησιμοποιήστε `mkcert` ή αυτο-υπογεγραμμένο. Routers με προστασία DNS rebinding (FRITZ!Box, dnsmasq, pfSense) μπλοκάρουν απαντήσεις με ιδιωτικές IP – προσθέστε το domain στις εξαιρέσεις.",
     "**Όνομα Hetzner** – εντάξει για λίγες μέρες· το όνομα αλλάζει με την IP, και το κοινό όριο μπορεί να σας σταματήσει μια φορτωμένη μέρα.",
     "**ipq.co** – όταν θέλετε σύντομο ευανάγνωστο όνομα χωρίς δικό σας domain· παλιά υπηρεσία ενός ατόμου – για τίποτα σημαντικό.",
     "**Παραγωγή** – δικό σας domain. Κοστίζει λίγα ευρώ τον χρόνο, επιβιώνει από μετακόμιση server, και από αυτό εξαρτώνται e-mails, cookies, SPF/DKIM και η εμπιστοσύνη των χρηστών."],
    ["**Όρια** της Let's Encrypt: 50 πιστοποιητικά ανά καταχωρημένο domain την εβδομάδα και 5 για το ίδιο σύνολο ονομάτων. Τα nip.io, sslip.io και your-server.de δεν είναι στη Public Suffix List – χιλιάδες χρήστες μοιράζονται αυτά τα όρια.",
     "**Όλα είναι δημόσια**: κάθε εκδοθέν πιστοποιητικό καταλήγει στα logs Certificate Transparency (crt.sh). Το όνομα `odoo.203-0-113-10.sslip.io` λέει σε όλους την IP του δοκιμαστικού σας Odoo – προστατέψτε το με κωδικό ή φίλτρο IP.",
     "**Πρώτα το AAAA**: αν το όνομα έχει διεύθυνση IPv6, η Let's Encrypt επικυρώνει μέσω IPv6. Μια λάθος ή απρόσιτη εγγραφή AAAA χαλάει την επικύρωση ακόμη κι αν το IPv4 είναι σωστό.",
     "**Wildcards** (`*.example.com`) μόνο με DNS-01 – όχι με nip.io και παρόμοια, μόνο στο δικό σας domain με DNS API (acme.sh, lego, DNS plugins του certbot).",
     "**Δύο timers** (πακέτου + δικός σας) είναι αβλαβείς – το certbot κλειδώνει τον εαυτό του – αλλά προκαλούν σύγχυση· κρατήστε έναν."],
    "Για μια γρήγορη δοκιμή αρκεί ένα όνομα από το sslip.io ή το nip.io συν certbot – πραγματικό HTTPS σε λεπτά, χωρίς domain. Για IP χωρίς όνομα υπάρχουν πλέον πιστοποιητικά 6 ημερών. Για Odoo σε παραγωγή – domain, certbot ή εναλλακτική, αυτόματη ανανέωση με hook επαναφόρτωσης και έλεγχος λήξης. Τα στήνουμε για εγκαταστάσεις Odoo εταιρειών στη Γερμανία, την Αυστρία και την Ελβετία.",
    "Σύνδεσμοι")

FREESSL["t"]["uk"] = _f(
    "Безкоштовний HTTPS без власного домену: certbot, альтернативи, nip.io, sslip.io і сертифікати на IP",
    "certbot з python3-certbot-nginx, продовження через cron або systemd timer і service, безкоштовні альтернативи (acme.sh, lego, Caddy, Traefik, ACME-модуль nginx), сертифікати Let's Encrypt на IP-адресу і безкоштовні імена хостів – Hetzner your-server.de, nip.io, sslip.io, traefik.me, ipq.co – з прикладами для IPv4 та IPv6 і що для чого.",
    "Тестовий Odoo на новому сервері, демо для клієнта, stage, поки DNS ще не готовий, – HTTPS потрібен з першого дня, а домен не завжди. Ось чим ми користуємось: certbot і його плагін для nginx, два способи автоматичного продовження, безкоштовні альтернативи, сертифікати прямо на IP-адресу і безкоштовні імена хостів, що вказують на будь-яку IP.",
    "Коротко: `apt install certbot python3-certbot-nginx` + `certbot --nginx -d ім'я` – готово; продовження – через `certbot.timer` або власний cron/таймер з deploy hook. Немає домену: `203-0-113-10.sslip.io` резолвиться в цю IP і отримує звичайний сертифікат Let's Encrypt через HTTP-01. Немає жодного імені: сертифікат Let's Encrypt на саму IP (6 днів, certbot ≥ 5.4). Імена з приватними IP (`192.168…nip.io`) публічний сертифікат отримати не можуть. Для продакшну потрібен власний домен.",
    ["certbot і python3-certbot-nginx", "Продовження: cron або systemd timer + service", "Безкоштовні альтернативи certbot", "Сертифікат на IP-адресу",
     "Безкоштовні імена: your-server.de, nip.io, sslip.io, traefik.me, ipq.co", "Що для чого", "Підводні камені", "Висновок"],
    ["**`--nginx`** читає конфігурацію nginx, знаходить блок `server` за `server_name`, через нього відповідає на HTTP-01, дописує `ssl_certificate` і редирект і перезавантажує nginx. `server_name` уже має бути в конфігу.",
     "**`certonly --webroot`** лише отримує сертифікат: nginx віддає `/.well-known/acme-challenge/` з папки, а конфіг лишається вашим – правильний вибір для nginx у Docker або конфігу з git.",
     "**apt чи snap.** Пакет дистрибутива старіший, зате оновлюється разом із системою; snap – завжди свіжий. Нові можливості (сертифікати на IP, профілі) потребують свіжого certbot.",
     "**Порт 80 має бути доступний з інтернету** для HTTP-01 – і потім, на кожне продовження. Закриєте 80 у фаєрволі – продовження зламається за 60 днів."],
    "Сертифікати Let's Encrypt живуть 90 днів (найближчими роками – менше), certbot продовжує їх, коли лишається менше 30 днів. Обидва пакети вже ставлять таймер – спершу перевірте його, а потім додавайте свій. Власний cron чи таймер має сенс із deploy hook (перезавантажити nginx або Docker-контейнер лише після реального продовження) або там, де таймера з пакета немає.",
    ["**cron чи таймер?** Працюють обидва. У таймера є `Persistent=true` (наздожене після простою), лог у `journalctl` і випадкова затримка без хитрощів; cron простіший і є всюди.",
     "**`--deploy-hook`** виконується лише після реального продовження сертифіката – без зайвих перезавантажень двічі на день. Він зберігається в `/etc/letsencrypt/renewal/<ім'я>.conf`, тож пізніший простий `certbot renew` його не загубить.",
     "**Перевірка**: `certbot renew --dry-run` робить повну репетицію на staging-сервері, не чіпаючи справжніх сертифікатів."],
    [["Інструмент", "Що це", "Коли"],
     ["**acme.sh**", "shell-скрипт без залежностей; CA за замовчуванням – ZeroSSL, Let's Encrypt з `--server letsencrypt`; DNS API ~150 провайдерів; сам ставить запис у cron", "сервери без Python, wildcard через DNS-01, роутери і NAS"],
     ["**lego**", "один бінарник на Go, HTTP-01, TLS-ALPN-01 і DNS-01 для багатьох DNS-провайдерів", "CI, контейнери, wildcard"],
     ["**Caddy**", "вебсервер з автоматичним HTTPS: сертифікати і продовження без клієнта", "нові невеликі інсталяції замість nginx"],
     ["**Traefik**", "reverse proxy для Docker з вбудованим ACME (`certresolver`)", "багато контейнерів з labels"],
     ["**ACME-модуль nginx**", "`ngx_http_acme_module`, офіційний, пакет `nginx-module-acme` (nginx ≥ 1.29); HTTP-01, без wildcard", "nginx з пакетів nginx.org, без certbot"],
     ["**Інші безкоштовні CA**", "ZeroSSL (ACME з ключами EAB, acme.sh створює їх сам), Google Trust Services (EAB з проєкту Google Cloud)", "друга CA про запас або через ліміти"]],
    "Для Odoo за nginx на Debian/Ubuntu certbot з плагіном nginx досі найпростіший: один пакет, одна команда, таймер у комплекті. Решта виправдана для wildcard (DNS-01), у контейнерних інсталяціях або коли nginx усе одно замінюєте.",
    "З січня 2026 року Let's Encrypt видає сертифікати на адреси IPv4 і IPv6. Вони використовують профіль `shortlived` і діють 6 днів; перевірка лише через HTTP-01 або TLS-ALPN-01. certbot підтримує це з версії 5.3 (`--ip-address`), webroot з IP – з 5.4; плагін nginx поки не вміє їх встановлювати.",
    ["**6 днів** – продовження має бути автоматичним і перезавантажувати nginx; пропустили вихідні – і браузер показує помилку.",
     "**Підходить для** адмінпанелі, API-ендпоінта чи тестового сервера без імені. **Не для** користувачів Odoo: cookies, посилання в листах і URL порталу прив'язані до імені.",
     "**IPv6**: працює так само, адреса пишеться як є (`--ip-address 2001:db8::10`)."],
    "Wildcard DNS-сервіси повертають IP, записану в імені хоста. Ні акаунта, ні налаштувань DNS – ім'я працює одразу, і для публічної IP на нього можна отримати звичайний сертифікат Let's Encrypt (HTTP-01).",
    [["Сервіс", "IPv4", "IPv6", "Сертифікат"],
     ["**Hetzner** (rDNS сервера)", "`static.137.100.245.188.clients.your-server.de` → 188.245.100.137 (октети у зворотному порядку)", "стандартного імені немає", "HTTP-01 працює; ліміт `your-server.de` спільний для всіх клієнтів Hetzner"],
     ["**nip.io**", "`10.0.0.1.nip.io`, `10-0-0-1.nip.io`, `app.10-0-0-1.nip.io`, hex `0a000001.nip.io`", "`2a01-4f8-c17-b8f--2.nip.io` (дефіси, `--` = `::`)", "HTTP-01 для публічних IP, без wildcard"],
     ["**sslip.io**", "ті самі формати: `203-0-113-10.sslip.io`", "`2001-db8--10.sslip.io`", "як nip.io – ті самі власники; якщо один домен уперся в ліміт, беріть інший"],
     ["**traefik.me**", "`10.0.0.1.traefik.me`, `10-0-0-1.traefik.me`; будь-яке інше ім'я → 127.0.0.1", "не задокументовано", "безкоштовне завантаження wildcard-сертифіката припинили у 2025 (його приватний ключ і так був публічним)"],
     ["**ipq.co**", "IP в імені немає: обираєте `myname.ipq.co` (або `fdns.uk`) у вебформі і вказуєте IP", "не задокументовано", "звичайний A-запис → HTTP-01; змінювати запис поки не можна"]],
    ["**Демо чи тест Odoo на новому VPS** – `odoo.<ip-через-дефіси>.sslip.io` + `certbot --nginx`: валідний HTTPS за дві хвилини, ще до появи DNS клієнта.",
     "**Локальна мережа, Docker на ноутбуці** – `app.192-168-1-20.nip.io` дає імена контейнерам без `/etc/hosts`. Публічний сертифікат неможливий (Let's Encrypt не дістане до приватної IP, а DNS-01 потребує контролю над зоною) – `mkcert` або самопідписаний. Роутери із захистом від DNS rebinding (FRITZ!Box, dnsmasq, pfSense) блокують відповіді з приватними IP – додайте домен у винятки.",
     "**Ім'я від Hetzner** – на кілька днів годиться; ім'я змінюється разом з IP, а спільний ліміт може зупинити в завантажений день.",
     "**ipq.co** – коли потрібне коротке зрозуміле ім'я без власного домену; старий сервіс однієї людини – не для чогось важливого.",
     "**Продакшн** – власний домен. Він коштує кілька євро на рік, переживе переїзд сервера, і від нього залежать листи, cookies, SPF/DKIM і довіра користувачів."],
    ["**Ліміти** Let's Encrypt: 50 сертифікатів на зареєстрований домен на тиждень і 5 на той самий набір імен. nip.io, sslip.io і your-server.de не входять у Public Suffix List – тисячі користувачів ділять ці ліміти.",
     "**Усе публічно**: кожен виданий сертифікат потрапляє в логи Certificate Transparency (crt.sh). Ім'я `odoo.203-0-113-10.sslip.io` повідомляє всім IP вашого тестового Odoo – закрийте його паролем або фільтром IP.",
     "**Спершу AAAA**: якщо в імені є IPv6-адреса, Let's Encrypt перевіряє через IPv6. Хибний чи недоступний AAAA-запис ламає перевірку, навіть коли IPv4 у порядку.",
     "**Wildcard** (`*.example.com`) – лише через DNS-01: не з nip.io та подібними, а тільки на власному домені з DNS API (acme.sh, lego, DNS-плагіни certbot).",
     "**Два таймери** (з пакета + свій) не шкодять – certbot сам себе блокує, – але плутають; лишіть один."],
    "Для швидкого тесту досить імені від sslip.io чи nip.io плюс certbot – справжній HTTPS за хвилини, без домену. Для IP без імені тепер є 6-денні сертифікати. Для робочого Odoo – домен, certbot або альтернатива, автоматичне продовження з hook перезавантаження і контроль терміну дії. Ми налаштовуємо це для інсталяцій Odoo компаній у Німеччині, Австрії та Швейцарії.",
    "Посилання")

FREESSL["t"]["ru"] = _f(
    "Бесплатный HTTPS без своего домена: certbot, альтернативы, nip.io, sslip.io и сертификаты на IP",
    "certbot с python3-certbot-nginx, продление через cron или systemd timer и service, бесплатные альтернативы (acme.sh, lego, Caddy, Traefik, ACME-модуль nginx), сертификаты Let's Encrypt на IP-адрес и бесплатные имена хостов – Hetzner your-server.de, nip.io, sslip.io, traefik.me, ipq.co – с примерами для IPv4 и IPv6 и что для чего.",
    "Тестовый Odoo на новом сервере, демо для клиента, stage, пока DNS ещё не готов, – HTTPS нужен с первого дня, а домен не всегда. Вот чем мы пользуемся: certbot и его плагин для nginx, два способа автоматического продления, бесплатные альтернативы, сертификаты прямо на IP-адрес и бесплатные имена хостов, которые указывают на любой IP.",
    "Коротко: `apt install certbot python3-certbot-nginx` + `certbot --nginx -d имя` – готово; продление – через `certbot.timer` или свой cron/таймер с deploy hook. Нет домена: `203-0-113-10.sslip.io` резолвится в этот IP и получает обычный сертификат Let's Encrypt через HTTP-01. Нет никакого имени: сертификат Let's Encrypt на сам IP (6 дней, certbot ≥ 5.4). Имена с приватными IP (`192.168…nip.io`) публичный сертификат получить не могут. Для продакшна нужен свой домен.",
    ["certbot и python3-certbot-nginx", "Продление: cron или systemd timer + service", "Бесплатные альтернативы certbot", "Сертификат на IP-адрес",
     "Бесплатные имена: your-server.de, nip.io, sslip.io, traefik.me, ipq.co", "Что для чего", "Подводные камни", "Итог"],
    ["**`--nginx`** читает конфигурацию nginx, находит блок `server` по `server_name`, через него отвечает на HTTP-01, дописывает `ssl_certificate` и редирект и перезагружает nginx. `server_name` уже должен быть в конфиге.",
     "**`certonly --webroot`** только получает сертификат: nginx отдаёт `/.well-known/acme-challenge/` из папки, а конфиг остаётся вашим – правильный выбор для nginx в Docker или конфига из git.",
     "**apt или snap.** Пакет дистрибутива старее, зато обновляется вместе с системой; snap – всегда свежий. Новые возможности (сертификаты на IP, профили) требуют свежего certbot.",
     "**Порт 80 должен быть доступен из интернета** для HTTP-01 – и потом, на каждое продление. Закроете 80 в файрволе – продление сломается через 60 дней."],
    "Сертификаты Let's Encrypt живут 90 дней (в ближайшие годы – меньше), certbot продлевает их, когда остаётся меньше 30 дней. Оба пакета уже ставят таймер – сначала проверьте его, потом добавляйте свой. Свой cron или таймер имеет смысл с deploy hook (перезагрузить nginx или Docker-контейнер только после реального продления) или там, где таймера из пакета нет.",
    ["**cron или таймер?** Работают оба. У таймера есть `Persistent=true` (догонит после простоя), лог в `journalctl` и случайная задержка без хитростей; cron проще и есть везде.",
     "**`--deploy-hook`** выполняется только после реального продления сертификата – без лишних перезагрузок дважды в день. Он сохраняется в `/etc/letsencrypt/renewal/<имя>.conf`, так что последующий простой `certbot renew` его не потеряет.",
     "**Проверка**: `certbot renew --dry-run` делает полную репетицию на staging-сервере, не трогая настоящие сертификаты."],
    [["Инструмент", "Что это", "Когда"],
     ["**acme.sh**", "shell-скрипт без зависимостей; CA по умолчанию – ZeroSSL, Let's Encrypt с `--server letsencrypt`; DNS API ~150 провайдеров; сам ставит запись в cron", "серверы без Python, wildcard через DNS-01, роутеры и NAS"],
     ["**lego**", "один бинарник на Go, HTTP-01, TLS-ALPN-01 и DNS-01 для многих DNS-провайдеров", "CI, контейнеры, wildcard"],
     ["**Caddy**", "веб-сервер с автоматическим HTTPS: сертификаты и продление без клиента", "новые небольшие инсталляции вместо nginx"],
     ["**Traefik**", "reverse proxy для Docker со встроенным ACME (`certresolver`)", "много контейнеров с labels"],
     ["**ACME-модуль nginx**", "`ngx_http_acme_module`, официальный, пакет `nginx-module-acme` (nginx ≥ 1.29); HTTP-01, без wildcard", "nginx из пакетов nginx.org, без certbot"],
     ["**Другие бесплатные CA**", "ZeroSSL (ACME с ключами EAB, acme.sh создаёт их сам), Google Trust Services (EAB из проекта Google Cloud)", "вторая CA про запас или из-за лимитов"]],
    "Для Odoo за nginx на Debian/Ubuntu certbot с плагином nginx до сих пор самый простой: один пакет, одна команда, таймер в комплекте. Остальные оправданы для wildcard (DNS-01), в контейнерных инсталляциях или когда nginx всё равно заменяете.",
    "С января 2026 года Let's Encrypt выдаёт сертификаты на адреса IPv4 и IPv6. Они используют профиль `shortlived` и действуют 6 дней; проверка только через HTTP-01 или TLS-ALPN-01. certbot поддерживает это с версии 5.3 (`--ip-address`), webroot с IP – с 5.4; плагин nginx пока не умеет их устанавливать.",
    ["**6 дней** – продление должно быть автоматическим и перезагружать nginx; пропустили выходные – и браузер показывает ошибку.",
     "**Подходит для** админки, API-эндпоинта или тестового сервера без имени. **Не для** пользователей Odoo: cookies, ссылки в письмах и URL портала привязаны к имени.",
     "**IPv6**: работает так же, адрес пишется как есть (`--ip-address 2001:db8::10`)."],
    "Wildcard DNS-сервисы возвращают IP, записанный в имени хоста. Ни аккаунта, ни настройки DNS – имя работает сразу, и для публичного IP на него можно получить обычный сертификат Let's Encrypt (HTTP-01).",
    [["Сервис", "IPv4", "IPv6", "Сертификат"],
     ["**Hetzner** (rDNS сервера)", "`static.137.100.245.188.clients.your-server.de` → 188.245.100.137 (октеты в обратном порядке)", "стандартного имени нет", "HTTP-01 работает; лимит `your-server.de` общий для всех клиентов Hetzner"],
     ["**nip.io**", "`10.0.0.1.nip.io`, `10-0-0-1.nip.io`, `app.10-0-0-1.nip.io`, hex `0a000001.nip.io`", "`2a01-4f8-c17-b8f--2.nip.io` (дефисы, `--` = `::`)", "HTTP-01 для публичных IP, без wildcard"],
     ["**sslip.io**", "те же форматы: `203-0-113-10.sslip.io`", "`2001-db8--10.sslip.io`", "как nip.io – те же владельцы; если один домен упёрся в лимит, берите другой"],
     ["**traefik.me**", "`10.0.0.1.traefik.me`, `10-0-0-1.traefik.me`; любое другое имя → 127.0.0.1", "не документировано", "бесплатную раздачу wildcard-сертификата прекратили в 2025 (его приватный ключ и так был публичным)"],
     ["**ipq.co**", "IP в имени нет: выбираете `myname.ipq.co` (или `fdns.uk`) в веб-форме и указываете IP", "не документировано", "обычная A-запись → HTTP-01; менять запись пока нельзя"]],
    ["**Демо или тест Odoo на новом VPS** – `odoo.<ip-через-дефисы>.sslip.io` + `certbot --nginx`: валидный HTTPS за две минуты, ещё до появления DNS клиента.",
     "**Локальная сеть, Docker на ноутбуке** – `app.192-168-1-20.nip.io` даёт имена контейнерам без `/etc/hosts`. Публичный сертификат невозможен (Let's Encrypt не достучится до приватного IP, а DNS-01 требует контроля над зоной) – `mkcert` или самоподписанный. Роутеры с защитой от DNS rebinding (FRITZ!Box, dnsmasq, pfSense) блокируют ответы с приватными IP – добавьте домен в исключения.",
     "**Имя от Hetzner** – на несколько дней годится; имя меняется вместе с IP, а общий лимит может остановить в загруженный день.",
     "**ipq.co** – когда нужно короткое понятное имя без своего домена; старый сервис одного человека – не для чего-то важного.",
     "**Продакшн** – свой домен. Он стоит несколько евро в год, переживёт переезд сервера, и от него зависят письма, cookies, SPF/DKIM и доверие пользователей."],
    ["**Лимиты** Let's Encrypt: 50 сертификатов на зарегистрированный домен в неделю и 5 на один и тот же набор имён. nip.io, sslip.io и your-server.de не входят в Public Suffix List – тысячи пользователей делят эти лимиты.",
     "**Всё публично**: каждый выданный сертификат попадает в логи Certificate Transparency (crt.sh). Имя `odoo.203-0-113-10.sslip.io` сообщает всем IP вашего тестового Odoo – закройте его паролем или фильтром IP.",
     "**Сначала AAAA**: если у имени есть IPv6-адрес, Let's Encrypt проверяет через IPv6. Неверная или недоступная AAAA-запись ломает проверку, даже когда IPv4 в порядке.",
     "**Wildcard** (`*.example.com`) – только через DNS-01: не с nip.io и подобными, а только на своём домене с DNS API (acme.sh, lego, DNS-плагины certbot).",
     "**Два таймера** (из пакета + свой) не вредят – certbot сам себя блокирует, – но путают; оставьте один."],
    "Для быстрого теста хватает имени от sslip.io или nip.io плюс certbot – настоящий HTTPS за минуты, без домена. Для IP без имени теперь есть 6-дневные сертификаты. Для рабочего Odoo – домен, certbot или альтернатива, автоматическое продление с hook перезагрузки и контроль срока действия. Мы настраиваем это для инсталляций Odoo компаний в Германии, Австрии и Швейцарии.",
    "Ссылки")
