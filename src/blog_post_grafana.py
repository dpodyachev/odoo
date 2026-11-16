# Статья 20: Grafana за nginx на подпути /grafana/ рядом с Odoo – docker только на 127.0.0.1, env, location ^~,
#            Basic Auth, Authorization "", websocket, опасный auth.proxy.  Статья 21: аудит безопасности nginx перед Odoo –
#            HSTS, двойной X-Frame-Options, cookie Secure/SameSite, старый nginx/Ubuntu 20.04. Все 6 языков. Обезличено.

GRAFANA = {
    "slug": "grafana-behind-nginx-subpath-odoo",
    "date": "2026-11-16",
    "tags": ["Grafana", "nginx", "Docker", "Security", "Monitoring", "Odoo"],
    "code": {
        "run": ("bash · Grafana only on localhost", """cd ~/grafana
docker network create grafana 2>/dev/null || true

# -p 127.0.0.1:3000:3000  instead of  -p 3000:3000  (that one listens on 0.0.0.0 and bypasses ufw)
docker run -d --restart unless-stopped --name grafana --hostname grafana --net=grafana \\
  -p 127.0.0.1:3000:3000 \\
  --env-file $PWD/grafana-docker.env \\
  -v $PWD/config/grafana.ini:/etc/grafana/grafana.ini \\
  -v $PWD/datasources:/etc/grafana/provisioning/datasources \\
  -v $PWD/var_lib_grafana:/var/lib/grafana \\
  grafana/grafana:13.3.1          # pin a version instead of :latest

sudo ss -ltnp | grep 3000          # must show 127.0.0.1:3000, not 0.0.0.0:3000"""),
        "env": ("grafana-docker.env", """GF_SECURITY_ADMIN_USER=admin
GF_SECURITY_ADMIN_PASSWORD=<long random password>

# Grafana lives under https://erp.example.com/grafana/
GF_SERVER_DOMAIN=erp.example.com
GF_SERVER_ROOT_URL=https://erp.example.com/grafana/   # explicit https, not %(protocol)s
GF_SERVER_SERVE_FROM_SUB_PATH=true

GF_SECURITY_COOKIE_SECURE=true
GF_USERS_ALLOW_SIGN_UP=false
GF_AUTH_ANONYMOUS_ENABLED=false
GF_SECURITY_ALLOW_EMBEDDING=true    # only if dashboards are shown in an Odoo iframe

# login via a header from the proxy – OFF unless you need single sign-on (see below)
GF_AUTH_PROXY_ENABLED=false"""),
        "nginx": ("/etc/nginx/sites-enabled/odoo.conf · inside server { listen 443 ssl; ... }", """location ^~ /grafana/ {
    auth_basic "grafana";
    auth_basic_user_file /etc/nginx/.htpasswd_grafana;
    proxy_set_header Authorization "";       # do not pass the nginx login to Grafana
    proxy_set_header X-WEBAUTH-USER "";      # never trust an auth-proxy header from the client
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_pass http://127.0.0.1:3000;        # no /grafana/ here – Grafana expects the sub-path itself
}

# Grafana Live (websocket)
location ^~ /grafana/api/live/ {
    auth_basic "grafana";
    auth_basic_user_file /etc/nginx/.htpasswd_grafana;
    proxy_set_header Authorization "";
    proxy_set_header X-WEBAUTH-USER "";
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;
    proxy_pass http://127.0.0.1:3000;
}"""),
        "htpasswd": ("bash · password file and reload", """sudo apt install apache2-utils
sudo htpasswd -c /etc/nginx/.htpasswd_grafana admin      # without -c to add more users
sudo chown root:www-data /etc/nginx/.htpasswd_grafana && sudo chmod 640 /etc/nginx/.htpasswd_grafana
sudo nginx -t && sudo systemctl reload nginx
docker restart grafana                                   # env is read only at container start"""),
        "check": ("bash · checks from outside", """curl -s -o /dev/null -w '%{http_code}\\n' http://erp.example.com:3000/     # 000 = closed (good)
curl -s -o /dev/null -w '%{http_code}\\n' https://erp.example.com/grafana/ # 401 = nginx asks for a password
curl -s -o /dev/null -w '%{http_code}\\n' -u admin:'…' https://erp.example.com/grafana/login   # 200

# on the server: who listens where, and what Grafana says
sudo ss -ltnp | grep -E ':3000|:9090|:9100|:9187'
docker logs --tail 30 grafana"""),
        "sso": ("one login instead of two (auth proxy done right)", """# grafana-docker.env
GF_AUTH_PROXY_ENABLED=true
GF_AUTH_PROXY_HEADER_NAME=X-WEBAUTH-USER
GF_AUTH_PROXY_HEADER_PROPERTY=username      # username or email – nothing else
GF_AUTH_PROXY_AUTO_SIGN_UP=true
GF_AUTH_PROXY_WHITELIST=172.18.0.1          # gateway of the docker network = nginx on the host

# nginx: after Basic Auth, nginx itself tells Grafana who the user is
proxy_set_header X-WEBAUTH-USER $remote_user;"""),
        "fw": ("bash · extra guard: drop outside traffic to container ports", """# Docker writes its own iptables rules – ufw does not see them. DOCKER-USER is checked first:
sudo iptables -I DOCKER-USER -i eth0 -p tcp -m conntrack --ctorigdstport 3000 -j DROP
sudo iptables -S DOCKER-USER
# persist: sudo apt install iptables-persistent && sudo netfilter-persistent save"""),
    },
    "links": [
        ("Grafana: run behind a reverse proxy", "https://grafana.com/tutorials/run-grafana-behind-a-proxy/"),
        ("Grafana: auth proxy authentication", "https://grafana.com/docs/grafana/latest/setup-grafana/configure-security/configure-authentication/auth-proxy/"),
        ("Grafana: configure with environment variables", "https://grafana.com/docs/grafana/latest/setup-grafana/configure-grafana/#override-configuration-with-environment-variables"),
        ("nginx: location – how a location is selected", "https://nginx.org/en/docs/http/ngx_http_core_module.html#location"),
        ("Docker: packet filtering and firewalls (DOCKER-USER)", "https://docs.docker.com/engine/network/packet-filtering-firewalls/"),
        ("Blog: nginx security audit in front of Odoo", "@blog:nginx-security-audit-odoo-hsts-cookies-x-frame-options"),
        ("Blog: Odoo server security – logs, secrets, ports, encryption", "@blog:odoo-server-security-logs-secrets-ports-encryption"),
        ("nginx for Odoo skill for AI agents (Markdown)", "https://2027.pp.ua/skill_odoo_nginx.md"),
    ],
    "t": {},
}

AUDIT = {
    "slug": "nginx-security-audit-odoo-hsts-cookies-x-frame-options",
    "date": "2026-11-16",
    "tags": ["Security", "nginx", "Odoo", "HSTS", "Cookies", "Audit"],
    "code": {
        "before": ("curl · what the audit saw", """$ curl -s -D - -o /dev/null https://erp.example.com/web/login
HTTP/1.1 200 OK
Server: nginx/1.18.0 (Ubuntu)
X-Frame-Options: DENY
Set-Cookie: session_id=…; Expires=…; Max-Age=7776000; HttpOnly; Path=/
X-Frame-Options: SAMEORIGIN
                                  # no Strict-Transport-Security, no X-Content-Type-Options"""),
        "fix": ("nginx · server { listen 443 ssl; ... } – the whole fix", """server_tokens off;                                   # Server: nginx (no version)

proxy_hide_header X-Frame-Options;                   # drop Odoo's own value ...
add_header X-Frame-Options "SAMEORIGIN" always;      # ... and send exactly one
add_header X-Content-Type-Options "nosniff" always;
add_header Strict-Transport-Security "max-age=31536000" always;

# cookies: Secure + SameSite
proxy_cookie_flags ~ secure samesite=lax;            # nginx >= 1.19.3 (Ubuntu 22.04/24.04)
# proxy_cookie_path / "/; Secure; SameSite=Lax";     # nginx 1.18 (Ubuntu 20.04) – workaround"""),
        "after": ("curl · after the fix", """$ curl -s -D - -o /dev/null https://erp.example.com/web/login
HTTP/1.1 200 OK
Server: nginx
X-Frame-Options: SAMEORIGIN
X-Content-Type-Options: nosniff
Strict-Transport-Security: max-age=31536000
Set-Cookie: session_id=…; HttpOnly; Path=/; Secure; SameSite=Lax

$ curl -s -D - -o /dev/null https://erp.example.com/web/login | grep -ci x-frame-options
1"""),
        "inherit": ("nginx · the add_header inheritance trap", """server {
    add_header Strict-Transport-Security "max-age=31536000" always;   # server level
    location ~* /web/static/ {
        add_header Cache-Control "public, no-transform";   # own add_header =>
        # HSTS / X-Frame-Options of the server level are NOT sent here any more – repeat them:
        add_header Strict-Transport-Security "max-age=31536000" always;
        add_header X-Content-Type-Options "nosniff" always;
        proxy_pass http://odoo;
    }
}
# tidier: put the headers into /etc/nginx/snippets/security-headers.conf and include it in every such location"""),
        "os": ("bash · is the OS still supported?", """lsb_release -ds; nginx -v
pro status                       # Ubuntu Pro / ESM attached?
sudo pro attach <token>          # free for up to 5 machines – security updates for 20.04 again
apt list --upgradable 2>/dev/null | grep -i security | head"""),
        "check": ("bash · re-check (from outside)", """H=https://erp.example.com
for p in / /web/login /web/static/src/img/favicon.ico /grafana/ /does-not-exist; do
  echo "== $p"; curl -s -D - -o /dev/null "$H$p" | grep -iE '^(HTTP|server|strict|x-frame|x-content)'
done
curl -sI http://erp.example.com/ | grep -iE '^(HTTP|location)'        # 301 -> https"""),
    },
    "links": [
        ("MDN: Strict-Transport-Security", "https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Strict-Transport-Security"),
        ("MDN: X-Frame-Options", "https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/X-Frame-Options"),
        ("MDN: Set-Cookie – Secure, SameSite", "https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Set-Cookie"),
        ("nginx: proxy_cookie_flags", "https://nginx.org/en/docs/http/ngx_http_proxy_module.html#proxy_cookie_flags"),
        ("nginx: add_header (inheritance, always)", "https://nginx.org/en/docs/http/ngx_http_headers_module.html#add_header"),
        ("Ubuntu release cycle (end of standard support)", "https://ubuntu.com/about/release-cycle"),
        ("Blog: Grafana behind nginx under /grafana/", "@blog:grafana-behind-nginx-subpath-odoo"),
        ("Blog: Odoo server security – logs, secrets, ports, encryption", "@blog:odoo-server-security-logs-secrets-ports-encryption"),
        ("nginx for Odoo skill for AI agents (Markdown)", "https://2027.pp.ua/skill_odoo_nginx.md"),
    ],
    "t": {},
}

# ---------------------------------------------------------------- tables
_ERR = {
    "en": [["Symptom", "Cause", "Fix"],
           ["401 after entering the nginx password, Grafana log: `password-auth.invalid`", "nginx passes its Basic Auth header on; Grafana checks it as its own login", "`proxy_set_header Authorization \"\";`"],
           ["Page loads without styles, JS errors, blank screen", "regex locations for `.js/.css` or `/static/` send Grafana's files to Odoo", "`location ^~ /grafana/` – `^~` stops the regex search"],
           ["Redirect loop or redirect to `http://`", "`root_url` built from `%(protocol)s` or without `/grafana/`", "`GF_SERVER_ROOT_URL=https://…/grafana/`"],
           ["404 on `/grafana/…`", "`proxy_pass http://127.0.0.1:3000/grafana/;` doubles the path, or `SERVE_FROM_SUB_PATH` missing", "`proxy_pass` without a URI + `SERVE_FROM_SUB_PATH=true`"],
           ["“Origin not allowed”, live panels do not update", "websocket `/grafana/api/live/` not proxied with Upgrade headers", "second location as above"],
           ["Port 3000 still reachable from outside", "container still published on 0.0.0.0", "`-p 127.0.0.1:3000:3000`, recreate the container"]],
    "de": [["Symptom", "Ursache", "Lösung"],
           ["401 nach dem nginx-Passwort, im Grafana-Log: `password-auth.invalid`", "nginx reicht seinen Basic-Auth-Header weiter; Grafana prüft ihn als eigenes Login", "`proxy_set_header Authorization \"\";`"],
           ["Seite ohne Styles, JS-Fehler, leerer Bildschirm", "Regex-Locations für `.js/.css` oder `/static/` schicken Grafanas Dateien an Odoo", "`location ^~ /grafana/` – `^~` stoppt die Regex-Suche"],
           ["Redirect-Schleife oder Weiterleitung auf `http://`", "`root_url` aus `%(protocol)s` oder ohne `/grafana/`", "`GF_SERVER_ROOT_URL=https://…/grafana/`"],
           ["404 auf `/grafana/…`", "`proxy_pass http://127.0.0.1:3000/grafana/;` verdoppelt den Pfad, oder `SERVE_FROM_SUB_PATH` fehlt", "`proxy_pass` ohne URI + `SERVE_FROM_SUB_PATH=true`"],
           ["„Origin not allowed“, Live-Panels aktualisieren nicht", "Websocket `/grafana/api/live/` ohne Upgrade-Header", "zweite Location wie oben"],
           ["Port 3000 von außen weiter erreichbar", "Container noch auf 0.0.0.0 veröffentlicht", "`-p 127.0.0.1:3000:3000`, Container neu anlegen"]],
    "fr": [["Symptôme", "Cause", "Correction"],
           ["401 après le mot de passe nginx, journal Grafana : `password-auth.invalid`", "nginx transmet son en-tête Basic Auth ; Grafana le vérifie comme sa propre connexion", "`proxy_set_header Authorization \"\";`"],
           ["Page sans styles, erreurs JS, écran vide", "des locations regex pour `.js/.css` ou `/static/` envoient les fichiers de Grafana à Odoo", "`location ^~ /grafana/` – `^~` arrête la recherche regex"],
           ["Boucle de redirection ou redirection vers `http://`", "`root_url` construit avec `%(protocol)s` ou sans `/grafana/`", "`GF_SERVER_ROOT_URL=https://…/grafana/`"],
           ["404 sur `/grafana/…`", "`proxy_pass http://127.0.0.1:3000/grafana/;` double le chemin, ou `SERVE_FROM_SUB_PATH` absent", "`proxy_pass` sans URI + `SERVE_FROM_SUB_PATH=true`"],
           ["« Origin not allowed », les panneaux live ne se mettent pas à jour", "websocket `/grafana/api/live/` sans en-têtes Upgrade", "deuxième location comme ci-dessus"],
           ["Port 3000 toujours accessible de l'extérieur", "conteneur encore publié sur 0.0.0.0", "`-p 127.0.0.1:3000:3000`, recréer le conteneur"]],
    "el": [["Σύμπτωμα", "Αιτία", "Λύση"],
           ["401 μετά τον κωδικό του nginx, στο log του Grafana: `password-auth.invalid`", "το nginx προωθεί την κεφαλίδα Basic Auth· το Grafana την ελέγχει ως δική του σύνδεση", "`proxy_set_header Authorization \"\";`"],
           ["Σελίδα χωρίς στυλ, σφάλματα JS, κενή οθόνη", "regex locations για `.js/.css` ή `/static/` στέλνουν τα αρχεία του Grafana στο Odoo", "`location ^~ /grafana/` – το `^~` σταματά την αναζήτηση regex"],
           ["Βρόχος ανακατεύθυνσης ή ανακατεύθυνση σε `http://`", "`root_url` από `%(protocol)s` ή χωρίς `/grafana/`", "`GF_SERVER_ROOT_URL=https://…/grafana/`"],
           ["404 στο `/grafana/…`", "το `proxy_pass http://127.0.0.1:3000/grafana/;` διπλασιάζει τη διαδρομή ή λείπει το `SERVE_FROM_SUB_PATH`", "`proxy_pass` χωρίς URI + `SERVE_FROM_SUB_PATH=true`"],
           ["«Origin not allowed», τα live panels δεν ενημερώνονται", "websocket `/grafana/api/live/` χωρίς κεφαλίδες Upgrade", "δεύτερο location όπως παραπάνω"],
           ["Η θύρα 3000 είναι ακόμη προσβάσιμη απ' έξω", "το container δημοσιεύεται ακόμη στο 0.0.0.0", "`-p 127.0.0.1:3000:3000`, αναδημιουργία του container"]],
    "uk": [["Симптом", "Причина", "Рішення"],
           ["401 після пароля nginx, у лозі Grafana: `password-auth.invalid`", "nginx передає свій заголовок Basic Auth далі, і Grafana перевіряє його як власний вхід", "`proxy_set_header Authorization \"\";`"],
           ["Сторінка без стилів, помилки JS, порожній екран", "regex-location для `.js/.css` або `/static/` віддають файли Grafana в Odoo", "`location ^~ /grafana/`: `^~` зупиняє пошук regex"],
           ["Нескінченний редирект або редирект на `http://`", "`root_url` зібраний через `%(protocol)s` або без `/grafana/`", "`GF_SERVER_ROOT_URL=https://…/grafana/`"],
           ["404 на `/grafana/…`", "`proxy_pass http://127.0.0.1:3000/grafana/;` подвоює шлях, або немає `SERVE_FROM_SUB_PATH`", "`proxy_pass` без URI + `SERVE_FROM_SUB_PATH=true`"],
           ["«Origin not allowed», live-панелі не оновлюються", "websocket `/grafana/api/live/` проксується без заголовків Upgrade", "другий location, як вище"],
           ["Порт 3000 досі відкритий ззовні", "контейнер усе ще опублікований на 0.0.0.0", "`-p 127.0.0.1:3000:3000`, перестворити контейнер"]],
    "ru": [["Симптом", "Причина", "Решение"],
           ["401 после пароля nginx, в логе Grafana: `password-auth.invalid`", "nginx передаёт свой заголовок Basic Auth дальше, и Grafana проверяет его как собственный вход", "`proxy_set_header Authorization \"\";`"],
           ["Страница без стилей, ошибки JS, пустой экран", "regex-location для `.js/.css` или `/static/` отдают файлы Grafana в Odoo", "`location ^~ /grafana/`: `^~` останавливает поиск regex"],
           ["Бесконечный редирект или редирект на `http://`", "`root_url` собран через `%(protocol)s` или без `/grafana/`", "`GF_SERVER_ROOT_URL=https://…/grafana/`"],
           ["404 на `/grafana/…`", "`proxy_pass http://127.0.0.1:3000/grafana/;` удваивает путь, или нет `SERVE_FROM_SUB_PATH`", "`proxy_pass` без URI + `SERVE_FROM_SUB_PATH=true`"],
           ["«Origin not allowed», live-панели не обновляются", "websocket `/grafana/api/live/` проксируется без заголовков Upgrade", "второй location, как выше"],
           ["Порт 3000 всё ещё открыт снаружи", "контейнер всё ещё опубликован на 0.0.0.0", "`-p 127.0.0.1:3000:3000`, пересоздать контейнер"]],
}

_FIND = {
    "en": [["Finding", "Risk", "Fix"],
           ["No HSTS", "first request over http can be intercepted and downgraded (SSL stripping)", "`Strict-Transport-Security: max-age=31536000`"],
           ["Two different `X-Frame-Options` (DENY + SAMEORIGIN)", "browser behaviour undefined; scanners report a misconfiguration", "`proxy_hide_header` + one `add_header … always`"],
           ["`session_id` without `Secure`", "cookie may be sent over plain http", "`proxy_cookie_flags ~ secure samesite=lax`"],
           ["`session_id` without `SameSite`", "weaker CSRF protection, depends on browser defaults", "`SameSite=Lax`"],
           ["`Server: nginx/1.18.0 (Ubuntu)`", "version disclosure; the OS is out of standard support", "`server_tokens off`; Ubuntu Pro or migration"]],
    "de": [["Befund", "Risiko", "Lösung"],
           ["Kein HSTS", "die erste Anfrage über http kann abgefangen und herabgestuft werden (SSL-Stripping)", "`Strict-Transport-Security: max-age=31536000`"],
           ["Zwei verschiedene `X-Frame-Options` (DENY + SAMEORIGIN)", "Browserverhalten undefiniert; Scanner melden eine Fehlkonfiguration", "`proxy_hide_header` + ein `add_header … always`"],
           ["`session_id` ohne `Secure`", "Cookie kann über unverschlüsseltes http gesendet werden", "`proxy_cookie_flags ~ secure samesite=lax`"],
           ["`session_id` ohne `SameSite`", "schwächerer CSRF-Schutz, abhängig von Browser-Standards", "`SameSite=Lax`"],
           ["`Server: nginx/1.18.0 (Ubuntu)`", "Versionsangabe; das Betriebssystem hat keinen Standard-Support mehr", "`server_tokens off`; Ubuntu Pro oder Umzug"]],
    "fr": [["Constat", "Risque", "Correction"],
           ["Pas de HSTS", "la première requête en http peut être interceptée et rétrogradée (SSL stripping)", "`Strict-Transport-Security: max-age=31536000`"],
           ["Deux `X-Frame-Options` différents (DENY + SAMEORIGIN)", "comportement du navigateur indéfini ; les scanners signalent une mauvaise configuration", "`proxy_hide_header` + un seul `add_header … always`"],
           ["`session_id` sans `Secure`", "le cookie peut partir en http non chiffré", "`proxy_cookie_flags ~ secure samesite=lax`"],
           ["`session_id` sans `SameSite`", "protection CSRF plus faible, dépend des valeurs par défaut du navigateur", "`SameSite=Lax`"],
           ["`Server: nginx/1.18.0 (Ubuntu)`", "version divulguée ; l'OS n'a plus de support standard", "`server_tokens off` ; Ubuntu Pro ou migration"]],
    "el": [["Εύρημα", "Κίνδυνος", "Λύση"],
           ["Χωρίς HSTS", "το πρώτο αίτημα μέσω http μπορεί να υποκλαπεί και να υποβαθμιστεί (SSL stripping)", "`Strict-Transport-Security: max-age=31536000`"],
           ["Δύο διαφορετικά `X-Frame-Options` (DENY + SAMEORIGIN)", "απροσδιόριστη συμπεριφορά browser· οι σαρωτές το αναφέρουν ως λάθος ρύθμιση", "`proxy_hide_header` + ένα `add_header … always`"],
           ["`session_id` χωρίς `Secure`", "το cookie μπορεί να σταλεί μέσω απλού http", "`proxy_cookie_flags ~ secure samesite=lax`"],
           ["`session_id` χωρίς `SameSite`", "ασθενέστερη προστασία CSRF, εξαρτάται από τις προεπιλογές του browser", "`SameSite=Lax`"],
           ["`Server: nginx/1.18.0 (Ubuntu)`", "αποκάλυψη έκδοσης· το λειτουργικό δεν έχει πλέον τυπική υποστήριξη", "`server_tokens off`· Ubuntu Pro ή μετάβαση"]],
    "uk": [["Знахідка", "Ризик", "Виправлення"],
           ["Немає HSTS", "перший запит по http можна перехопити й понизити до http (SSL stripping)", "`Strict-Transport-Security: max-age=31536000`"],
           ["Два різні `X-Frame-Options` (DENY + SAMEORIGIN)", "поведінка браузера не визначена, сканери бачать помилку конфігурації", "`proxy_hide_header` + один `add_header … always`"],
           ["`session_id` без `Secure`", "cookie може піти по незашифрованому http", "`proxy_cookie_flags ~ secure samesite=lax`"],
           ["`session_id` без `SameSite`", "слабший захист від CSRF, усе залежить від налаштувань браузера за замовчуванням", "`SameSite=Lax`"],
           ["`Server: nginx/1.18.0 (Ubuntu)`", "видно версію, а ОС вже без стандартної підтримки", "`server_tokens off`; Ubuntu Pro або переїзд"]],
    "ru": [["Находка", "Риск", "Исправление"],
           ["Нет HSTS", "первый запрос по http можно перехватить и понизить до http (SSL stripping)", "`Strict-Transport-Security: max-age=31536000`"],
           ["Два разных `X-Frame-Options` (DENY + SAMEORIGIN)", "поведение браузера не определено, сканеры видят ошибку конфигурации", "`proxy_hide_header` + один `add_header … always`"],
           ["`session_id` без `Secure`", "cookie может уйти по незашифрованному http", "`proxy_cookie_flags ~ secure samesite=lax`"],
           ["`session_id` без `SameSite`", "защита от CSRF слабее, всё зависит от настроек браузера по умолчанию", "`SameSite=Lax`"],
           ["`Server: nginx/1.18.0 (Ubuntu)`", "видна версия, а ОС уже без стандартной поддержки", "`server_tokens off`; Ubuntu Pro или переезд"]],
}


def _g(title, summary, intro, note, h, ul_risk, p_env, p_nginx, p_why, p_sso, p_after, links):
    """Тело статьи про Grafana – одинаковая структура для всех языков."""
    return {"title": title, "summary": summary, "body": [
        ("p", intro), ("note", note),
        ("h", h[0]), ("ul", ul_risk), ("code", "run"), ("code", "fw"),
        ("h", h[1]), ("p", p_env), ("code", "env"),
        ("h", h[2]), ("p", p_nginx), ("code", "nginx"), ("ul", p_why), ("code", "htpasswd"),
        ("h", h[3]), ("table", _ERR[h[6]]),
        ("h", h[4]), ("p", p_sso[0]), ("code", "sso"), ("p", p_sso[1]),
        ("h", h[5]), ("code", "check"), ("p", p_after),
        ("links", links)]}


def _a(title, summary, intro, note, h, lang, p_hsts, ul_xfo, p_cookie, ul_trap, p_os, p_result, links):
    """Тело статьи про аудит nginx."""
    return {"title": title, "summary": summary, "body": [
        ("p", intro), ("note", note), ("code", "before"),
        ("h", h[0]), ("table", _FIND[lang]),
        ("h", h[1]), ("p", p_hsts),
        ("h", h[2]), ("ul", ul_xfo),
        ("h", h[3]), ("p", p_cookie),
        ("h", h[4]), ("code", "fix"), ("code", "after"),
        ("h", h[5]), ("ul", ul_trap), ("code", "inherit"),
        ("h", h[6]), ("p", p_os), ("code", "os"),
        ("h", h[7]), ("code", "check"), ("p", p_result),
        ("links", links)]}


# ================================================================ EN
GRAFANA["t"]["en"] = _g(
    "Grafana behind nginx under /grafana/ next to Odoo: localhost only, env settings and a working location",
    "How to hide a Grafana container that listens on port 3000 for the whole internet: publish it on 127.0.0.1 only, configure the sub-path in the env file, protect it with nginx Basic Auth and avoid the three traps – the forwarded Authorization header, regex locations stealing the static files, and an auth proxy that lets anyone in.",
    "A typical monitoring setup next to Odoo: Prometheus, node_exporter, postgres_exporter and Grafana in Docker on the same server. During a check of such a server, Grafana was started with `-p 3000:3000` – and answered on `http://erp.example.com:3000` for everybody, although `ufw` allowed only SSH, 80 and 443. Worse, Grafana's **auth proxy** was switched on with an empty whitelist: anyone who could reach port 3000 and sent the right header would be logged in without a password. This article shows how to move Grafana behind the existing nginx under `https://erp.example.com/grafana/`.",
    "Short version: `-p 127.0.0.1:3000:3000`; `GF_SERVER_ROOT_URL=https://erp.example.com/grafana/` + `GF_SERVER_SERVE_FROM_SUB_PATH=true`; in nginx `location ^~ /grafana/` with Basic Auth, `proxy_set_header Authorization \"\"` and `proxy_pass http://127.0.0.1:3000;` without a path; auth proxy off – or only with a whitelist.",
    ["1. Close the port", "2. Grafana env file", "3. nginx location", "4. Typical errors", "5. One login instead of two", "6. Check", "en"],
    ["`-p 3000:3000` means `0.0.0.0:3000` **and** `[::]:3000`. Docker inserts its own iptables rules in front of ufw – `ufw status` looks fine, the port is still open.",
     "Grafana itself is not the only risk: the dashboards show server names, databases, sometimes SQL queries of the Odoo database.",
     "Exporters (9100, 9187, 9090) without `ports:` stay inside the Docker network – Prometheus reaches them by container name."],
    "Grafana reads every `grafana.ini` option from `GF_<SECTION>_<KEY>` variables. The important part for a sub-path: the public URL with the path, and `serve_from_sub_path`, so Grafana itself answers under `/grafana/`. Write `https` explicitly – `%(protocol)s` is the protocol Grafana itself listens on (http), so its redirects would go to `http://`.",
    "The location goes into the existing Odoo `server` block for port 443 – certificate, HSTS and the other headers apply to Grafana too.",
    ["**`^~`** – nginx picks regex locations (`~* \\.(js|css|png)$`, `~ /static/`) before a plain prefix. Most Odoo configs have such locations for caching, and they would send `/grafana/public/build/*.js` to Odoo. `^~` stops the regex search for this prefix.",
     "**`Authorization \"\"`** – the browser sends the nginx Basic Auth login in this header with every request. Grafana sees it and tries to log in with these credentials → 401, in its log `password-auth.invalid`.",
     "**`X-WEBAUTH-USER \"\"`** – if auth proxy is ever switched on, a client must never be able to set this header itself.",
     "**`proxy_pass` without a URI** – with `serve_from_sub_path` Grafana expects the full path `/grafana/…`; `proxy_pass http://127.0.0.1:3000/;` would cut it off."],
    ["With Basic Auth in nginx and Grafana's own login you log in twice. If that bothers you, let nginx tell Grafana who the user is – but only with a whitelist, so Grafana trusts the header from nginx and nobody else.",
     "The whitelist is the IP that Grafana sees as the client: with `-p 127.0.0.1:3000:3000` this is the gateway of the Docker network (`docker network inspect grafana`). Without a whitelist – the situation from the beginning – the header from any client is trusted."],
    "Expected: port 3000 closed from outside, `/grafana/` asks for the nginx password, then Grafana opens with styles and live updates. If Grafana dashboards are embedded in Odoo (iframe), `GF_SECURITY_ALLOW_EMBEDDING=true` and `X-Frame-Options: SAMEORIGIN` in nginx are enough – same domain.",
    "Links")

AUDIT["t"]["en"] = _a(
    "nginx security audit in front of Odoo: HSTS, duplicate X-Frame-Options, session cookie without Secure/SameSite, old nginx",
    "Four findings of a real security scan of an Odoo server – missing HSTS, two different X-Frame-Options, session_id without Secure and SameSite, nginx 1.18 on Ubuntu 20.04 – what each one means, the six lines of nginx that fixed them, and the add_header trap that hides headers again.",
    "An external security scan of a production Odoo server (Odoo behind nginx on Ubuntu 20.04) reported: no HSTS, `X-Frame-Options` sent twice with different values, the `session_id` cookie without `Secure` and `SameSite`, and an old nginx. None of it is an open door, but each one weakens the protection of the login session – and all of it was fixed in a quarter of an hour without touching Odoo.",
    "Short version: in the 443 server block `server_tokens off`, `proxy_hide_header X-Frame-Options` + one `add_header X-Frame-Options SAMEORIGIN always`, `nosniff`, HSTS for a year, and cookie flags (`proxy_cookie_flags ~ secure samesite=lax`, on nginx 1.18 via `proxy_cookie_path`). Then check with curl – including the locations that have their own `add_header`.",
    ["What the audit found", "HSTS", "Why X-Frame-Options came twice", "session_id: Secure and SameSite", "The fix", "The add_header trap", "“Old nginx” – how critical?", "Re-check"],
    "en",
    "Without HSTS the browser tries `http://` first when a user types the domain, and gets the redirect to https from the server. On a hostile Wi-Fi exactly this first unencrypted request can be intercepted and the user kept on http (SSL stripping). With `Strict-Transport-Security` the browser remembers for `max-age` seconds that the domain is https only. Start without `includeSubDomains` and `preload` until every subdomain really has https – HSTS cannot be withdrawn quickly from browsers that have stored it. Careful approach: `max-age=86400` for a day, then a year.",
    ["Odoo itself sets `X-Frame-Options: DENY` on the login page and parts of the backend (protection against clickjacking).",
     "The nginx config had its own `add_header X-Frame-Options \"SAMEORIGIN\"` – result: two headers with different values. Browsers then behave inconsistently, scanners report it as a misconfiguration.",
     "Simply deleting the nginx line is not enough: then only the login page is protected, all other pages have no header at all (we saw exactly that on the first re-check).",
     "Correct: `proxy_hide_header X-Frame-Options;` removes Odoo's value, `add_header … always` sets one value on every response. `SAMEORIGIN` instead of `DENY` if something on the same domain embeds Odoo or Grafana in an iframe."],
    "Odoo (up to 17) sets `session_id` with `HttpOnly` and `Path=/` only. `Secure` ensures that the browser never sends the cookie over unencrypted http – together with HSTS this closes session theft by interception. `SameSite=Lax` keeps the cookie away from cross-site POST requests (CSRF) but still sends it on normal link clicks; `Strict` would break links from e-mails into Odoo. nginx sets the flags on the way out: `proxy_cookie_flags` from nginx 1.19.3, on nginx 1.18 (Ubuntu 20.04) a workaround via `proxy_cookie_path` that appends the flags to the path.",
    ["`add_header` is inherited from the `server` block into a `location` **only if that location has no `add_header` of its own**. Odoo configs often have a location for static files with `add_header Cache-Control` – the security headers disappear exactly there.",
     "Without `always`, `add_header` only applies to 200, 201, 204, 206, 301, 302, 303, 304, 307, 308 – not to 401, 404 or 502.",
     "So check several URLs: a normal page, the login, a static file, a 404, and every extra location (e.g. `/grafana/`)."],
    "nginx 1.18 from Ubuntu's repository gets backported security fixes – the version number alone is not a vulnerability, and `server_tokens off` only removes it from the header. The real problem behind it: Ubuntu 20.04 left standard support in May 2025. Without Ubuntu Pro (ESM) the server gets no security updates – not for nginx, OpenSSL or the kernel. Until the planned migration to Ubuntu 24.04, attach the free Ubuntu Pro; on the new server use `proxy_cookie_flags` instead of the workaround.",
    "After the fix every checked URL returned exactly one `X-Frame-Options: SAMEORIGIN`, `nosniff`, HSTS for a year, the cookie with `Secure; SameSite=Lax`, and `Server: nginx` without a version. Odoo itself, its config and its users did not notice anything.",
    "Links")

# ================================================================ DE
GRAFANA["t"]["de"] = _g(
    "Grafana hinter nginx unter /grafana/ neben Odoo: nur localhost, env-Einstellungen und eine funktionierende Location",
    "Wie man einen Grafana-Container versteckt, der auf Port 3000 fürs ganze Internet lauscht: nur auf 127.0.0.1 veröffentlichen, den Unterpfad in der env-Datei konfigurieren, mit nginx Basic Auth schützen und drei Fallen vermeiden – den weitergereichten Authorization-Header, Regex-Locations, die die statischen Dateien stehlen, und einen Auth-Proxy, der jeden hereinlässt.",
    "Ein typisches Monitoring neben Odoo: Prometheus, node_exporter, postgres_exporter und Grafana in Docker auf demselben Server. Bei der Prüfung eines solchen Servers lief Grafana mit `-p 3000:3000` – und antwortete auf `http://erp.example.com:3000` für alle, obwohl `ufw` nur SSH, 80 und 443 erlaubte. Schlimmer: Grafanas **Auth-Proxy** war mit leerer Whitelist eingeschaltet – wer Port 3000 erreichte und den passenden Header schickte, wäre ohne Passwort eingeloggt. Der Artikel zeigt, wie Grafana hinter den vorhandenen nginx unter `https://erp.example.com/grafana/` umzieht.",
    "Kurzfassung: `-p 127.0.0.1:3000:3000`; `GF_SERVER_ROOT_URL=https://erp.example.com/grafana/` + `GF_SERVER_SERVE_FROM_SUB_PATH=true`; in nginx `location ^~ /grafana/` mit Basic Auth, `proxy_set_header Authorization \"\"` und `proxy_pass http://127.0.0.1:3000;` ohne Pfad; Auth-Proxy aus – oder nur mit Whitelist.",
    ["1. Port schließen", "2. env-Datei von Grafana", "3. nginx-Location", "4. Typische Fehler", "5. Ein Login statt zwei", "6. Prüfen", "de"],
    ["`-p 3000:3000` bedeutet `0.0.0.0:3000` **und** `[::]:3000`. Docker setzt eigene iptables-Regeln vor ufw – `ufw status` sieht gut aus, der Port ist trotzdem offen.",
     "Nicht nur Grafana selbst ist das Risiko: Die Dashboards zeigen Servernamen, Datenbanken, manchmal SQL-Abfragen der Odoo-Datenbank.",
     "Exporter (9100, 9187, 9090) ohne `ports:` bleiben im Docker-Netz – Prometheus erreicht sie über den Containernamen."],
    "Grafana liest jede `grafana.ini`-Option aus Variablen `GF_<SECTION>_<KEY>`. Wichtig für einen Unterpfad: die öffentliche URL mit Pfad und `serve_from_sub_path`, damit Grafana selbst unter `/grafana/` antwortet. `https` ausdrücklich schreiben – `%(protocol)s` ist das Protokoll, auf dem Grafana selbst lauscht (http), seine Weiterleitungen gingen dann auf `http://`.",
    "Die Location kommt in den vorhandenen Odoo-`server`-Block für Port 443 – Zertifikat, HSTS und die übrigen Header gelten dann auch für Grafana.",
    ["**`^~`** – nginx wählt Regex-Locations (`~* \\.(js|css|png)$`, `~ /static/`) vor einem einfachen Präfix. Die meisten Odoo-Konfigurationen haben solche Locations fürs Caching, und sie würden `/grafana/public/build/*.js` an Odoo schicken. `^~` stoppt die Regex-Suche für dieses Präfix.",
     "**`Authorization \"\"`** – der Browser sendet das nginx-Basic-Auth-Login in diesem Header bei jeder Anfrage. Grafana sieht ihn und versucht, sich damit anzumelden → 401, im Log `password-auth.invalid`.",
     "**`X-WEBAUTH-USER \"\"`** – falls der Auth-Proxy je eingeschaltet wird, darf ein Client diesen Header nie selbst setzen können.",
     "**`proxy_pass` ohne URI** – mit `serve_from_sub_path` erwartet Grafana den vollen Pfad `/grafana/…`; `proxy_pass http://127.0.0.1:3000/;` würde ihn abschneiden."],
    ["Mit Basic Auth in nginx und Grafanas eigenem Login meldet man sich zweimal an. Wen das stört: nginx sagt Grafana, wer der Benutzer ist – aber nur mit Whitelist, damit Grafana dem Header von nginx vertraut und niemandem sonst.",
     "Die Whitelist ist die IP, die Grafana als Client sieht: bei `-p 127.0.0.1:3000:3000` das Gateway des Docker-Netzes (`docker network inspect grafana`). Ohne Whitelist – die Lage vom Anfang – wird dem Header jedes Clients vertraut."],
    "Erwartet: Port 3000 von außen zu, `/grafana/` fragt nach dem nginx-Passwort, danach öffnet Grafana mit Styles und Live-Updates. Werden Grafana-Dashboards in Odoo eingebettet (iframe), genügen `GF_SECURITY_ALLOW_EMBEDDING=true` und `X-Frame-Options: SAMEORIGIN` in nginx – gleiche Domain.",
    "Links")

AUDIT["t"]["de"] = _a(
    "nginx-Sicherheitsaudit vor Odoo: HSTS, doppelter X-Frame-Options, Session-Cookie ohne Secure/SameSite, altes nginx",
    "Vier Befunde eines echten Sicherheitsscans eines Odoo-Servers – fehlendes HSTS, zwei verschiedene X-Frame-Options, session_id ohne Secure und SameSite, nginx 1.18 auf Ubuntu 20.04 – was sie bedeuten, die sechs nginx-Zeilen, die sie behoben haben, und die add_header-Falle, die Header wieder verschwinden lässt.",
    "Ein externer Sicherheitsscan eines produktiven Odoo-Servers (Odoo hinter nginx auf Ubuntu 20.04) meldete: kein HSTS, `X-Frame-Options` doppelt mit verschiedenen Werten, das Cookie `session_id` ohne `Secure` und `SameSite`, und ein altes nginx. Nichts davon ist eine offene Tür, aber jedes schwächt den Schutz der Login-Sitzung – und alles war in einer Viertelstunde behoben, ohne Odoo anzufassen.",
    "Kurzfassung: im 443-Server-Block `server_tokens off`, `proxy_hide_header X-Frame-Options` + ein `add_header X-Frame-Options SAMEORIGIN always`, `nosniff`, HSTS für ein Jahr und Cookie-Flags (`proxy_cookie_flags ~ secure samesite=lax`, auf nginx 1.18 über `proxy_cookie_path`). Dann mit curl prüfen – auch die Locations mit eigenem `add_header`.",
    ["Was das Audit fand", "HSTS", "Warum X-Frame-Options doppelt kam", "session_id: Secure und SameSite", "Die Korrektur", "Die add_header-Falle", "„Altes nginx“ – wie kritisch?", "Nachprüfen"],
    "de",
    "Ohne HSTS versucht der Browser zuerst `http://`, wenn jemand die Domain eintippt, und bekommt vom Server die Weiterleitung auf https. In einem fremden WLAN kann genau diese erste unverschlüsselte Anfrage abgefangen und der Nutzer auf http gehalten werden (SSL-Stripping). Mit `Strict-Transport-Security` merkt sich der Browser für `max-age` Sekunden, dass die Domain nur https kennt. Ohne `includeSubDomains` und `preload` beginnen, bis wirklich jede Subdomain https hat – HSTS lässt sich aus Browsern, die es gespeichert haben, nicht schnell zurückholen. Vorsichtig: `max-age=86400` für einen Tag, dann ein Jahr.",
    ["Odoo setzt selbst `X-Frame-Options: DENY` auf der Login-Seite und in Teilen des Backends (Schutz gegen Clickjacking).",
     "Die nginx-Konfiguration hatte ein eigenes `add_header X-Frame-Options \"SAMEORIGIN\"` – Ergebnis: zwei Header mit verschiedenen Werten. Browser verhalten sich dann uneinheitlich, Scanner melden eine Fehlkonfiguration.",
     "Einfach die nginx-Zeile zu löschen reicht nicht: Dann ist nur die Login-Seite geschützt, alle anderen Seiten haben gar keinen Header (genau das zeigte die erste Nachprüfung).",
     "Richtig: `proxy_hide_header X-Frame-Options;` entfernt Odoos Wert, `add_header … always` setzt einen Wert auf jeder Antwort. `SAMEORIGIN` statt `DENY`, wenn etwas auf derselben Domain Odoo oder Grafana in einem iframe einbettet."],
    "Odoo (bis 17) setzt `session_id` nur mit `HttpOnly` und `Path=/`. `Secure` sorgt dafür, dass der Browser das Cookie nie über unverschlüsseltes http sendet – zusammen mit HSTS schließt das Sitzungsdiebstahl durch Mitlesen. `SameSite=Lax` hält das Cookie von seitenübergreifenden POST-Anfragen (CSRF) fern, sendet es aber bei normalen Link-Klicks; `Strict` würde Links aus E-Mails in Odoo kaputt machen. nginx setzt die Flags auf dem Rückweg: `proxy_cookie_flags` ab nginx 1.19.3, auf nginx 1.18 (Ubuntu 20.04) ein Workaround über `proxy_cookie_path`, der die Flags an den Pfad anhängt.",
    ["`add_header` wird aus dem `server`-Block nur dann in eine `location` vererbt, **wenn diese Location kein eigenes `add_header` hat**. Odoo-Konfigurationen haben oft eine Location für statische Dateien mit `add_header Cache-Control` – genau dort verschwinden die Sicherheits-Header.",
     "Ohne `always` gilt `add_header` nur für 200, 201, 204, 206, 301, 302, 303, 304, 307, 308 – nicht für 401, 404 oder 502.",
     "Also mehrere URLs prüfen: eine normale Seite, das Login, eine statische Datei, eine 404 und jede zusätzliche Location (z. B. `/grafana/`)."],
    "nginx 1.18 aus dem Ubuntu-Repository bekommt zurückportierte Sicherheitskorrekturen – die Versionsnummer allein ist keine Schwachstelle, und `server_tokens off` entfernt sie nur aus dem Header. Das eigentliche Problem dahinter: Ubuntu 20.04 hat den Standard-Support im Mai 2025 verlassen. Ohne Ubuntu Pro (ESM) bekommt der Server keine Sicherheitsupdates – weder für nginx noch für OpenSSL oder den Kernel. Bis zum geplanten Umzug auf Ubuntu 24.04 das kostenlose Ubuntu Pro anbinden; auf dem neuen Server `proxy_cookie_flags` statt des Workarounds verwenden.",
    "Nach der Korrektur lieferte jede geprüfte URL genau ein `X-Frame-Options: SAMEORIGIN`, `nosniff`, HSTS für ein Jahr, das Cookie mit `Secure; SameSite=Lax` und `Server: nginx` ohne Version. Odoo selbst, seine Konfiguration und seine Benutzer haben nichts bemerkt.",
    "Links")

# ================================================================ FR
GRAFANA["t"]["fr"] = _g(
    "Grafana derrière nginx sous /grafana/ à côté d'Odoo : localhost uniquement, réglages env et une location qui fonctionne",
    "Comment cacher un conteneur Grafana qui écoute sur le port 3000 pour tout Internet : le publier uniquement sur 127.0.0.1, configurer le sous-chemin dans le fichier env, le protéger par Basic Auth nginx et éviter trois pièges – l'en-tête Authorization transmis, les locations regex qui volent les fichiers statiques et un auth proxy qui laisse entrer n'importe qui.",
    "Une supervision typique à côté d'Odoo : Prometheus, node_exporter, postgres_exporter et Grafana dans Docker sur le même serveur. Lors du contrôle d'un tel serveur, Grafana tournait avec `-p 3000:3000` – et répondait sur `http://erp.example.com:3000` pour tout le monde, alors que `ufw` n'autorisait que SSH, 80 et 443. Pire : l'**auth proxy** de Grafana était activé avec une liste blanche vide – quiconque atteignait le port 3000 avec le bon en-tête serait connecté sans mot de passe. Cet article montre comment placer Grafana derrière le nginx existant sous `https://erp.example.com/grafana/`.",
    "En bref : `-p 127.0.0.1:3000:3000` ; `GF_SERVER_ROOT_URL=https://erp.example.com/grafana/` + `GF_SERVER_SERVE_FROM_SUB_PATH=true` ; dans nginx `location ^~ /grafana/` avec Basic Auth, `proxy_set_header Authorization \"\"` et `proxy_pass http://127.0.0.1:3000;` sans chemin ; auth proxy désactivé – ou seulement avec liste blanche.",
    ["1. Fermer le port", "2. Le fichier env de Grafana", "3. La location nginx", "4. Erreurs typiques", "5. Une connexion au lieu de deux", "6. Vérifier", "fr"],
    ["`-p 3000:3000` signifie `0.0.0.0:3000` **et** `[::]:3000`. Docker insère ses propres règles iptables avant ufw – `ufw status` semble correct, le port reste ouvert.",
     "Grafana n'est pas le seul risque : les tableaux de bord montrent noms de serveurs, bases de données, parfois des requêtes SQL de la base Odoo.",
     "Les exporters (9100, 9187, 9090) sans `ports:` restent dans le réseau Docker – Prometheus les joint par le nom du conteneur."],
    "Grafana lit chaque option de `grafana.ini` depuis des variables `GF_<SECTION>_<KEY>`. L'essentiel pour un sous-chemin : l'URL publique avec le chemin et `serve_from_sub_path`, pour que Grafana réponde lui-même sous `/grafana/`. Écrire `https` explicitement – `%(protocol)s` est le protocole sur lequel Grafana écoute (http), ses redirections iraient donc vers `http://`.",
    "La location va dans le bloc `server` Odoo existant du port 443 – certificat, HSTS et les autres en-têtes s'appliquent aussi à Grafana.",
    ["**`^~`** – nginx choisit les locations regex (`~* \\.(js|css|png)$`, `~ /static/`) avant un simple préfixe. La plupart des configurations Odoo en ont pour le cache, et elles enverraient `/grafana/public/build/*.js` à Odoo. `^~` arrête la recherche regex pour ce préfixe.",
     "**`Authorization \"\"`** – le navigateur envoie la connexion Basic Auth de nginx dans cet en-tête à chaque requête. Grafana la voit et tente de se connecter avec → 401, dans son journal `password-auth.invalid`.",
     "**`X-WEBAUTH-USER \"\"`** – si l'auth proxy est un jour activé, un client ne doit jamais pouvoir fixer cet en-tête lui-même.",
     "**`proxy_pass` sans URI** – avec `serve_from_sub_path`, Grafana attend le chemin complet `/grafana/…` ; `proxy_pass http://127.0.0.1:3000/;` le couperait."],
    ["Avec Basic Auth dans nginx et la connexion propre de Grafana, on se connecte deux fois. Si cela gêne : nginx dit à Grafana qui est l'utilisateur – mais seulement avec une liste blanche, pour que Grafana fasse confiance à l'en-tête venant de nginx et de personne d'autre.",
     "La liste blanche est l'IP que Grafana voit comme client : avec `-p 127.0.0.1:3000:3000`, c'est la passerelle du réseau Docker (`docker network inspect grafana`). Sans liste blanche – la situation du début – l'en-tête de n'importe quel client est accepté."],
    "Attendu : port 3000 fermé depuis l'extérieur, `/grafana/` demande le mot de passe nginx, puis Grafana s'ouvre avec styles et mises à jour live. Si des tableaux Grafana sont intégrés dans Odoo (iframe), `GF_SECURITY_ALLOW_EMBEDDING=true` et `X-Frame-Options: SAMEORIGIN` dans nginx suffisent – même domaine.",
    "Liens")

AUDIT["t"]["fr"] = _a(
    "Audit de sécurité nginx devant Odoo : HSTS, X-Frame-Options en double, cookie de session sans Secure/SameSite, vieux nginx",
    "Quatre constats d'un vrai scan de sécurité d'un serveur Odoo – HSTS absent, deux X-Frame-Options différents, session_id sans Secure ni SameSite, nginx 1.18 sur Ubuntu 20.04 – ce qu'ils signifient, les six lignes nginx qui les ont corrigés, et le piège add_header qui fait disparaître à nouveau les en-têtes.",
    "Un scan de sécurité externe d'un serveur Odoo de production (Odoo derrière nginx sur Ubuntu 20.04) signalait : pas de HSTS, `X-Frame-Options` envoyé deux fois avec des valeurs différentes, le cookie `session_id` sans `Secure` ni `SameSite`, et un vieux nginx. Rien de tout cela n'est une porte ouverte, mais chaque point affaiblit la protection de la session – et tout a été corrigé en un quart d'heure sans toucher à Odoo.",
    "En bref : dans le bloc server 443, `server_tokens off`, `proxy_hide_header X-Frame-Options` + un seul `add_header X-Frame-Options SAMEORIGIN always`, `nosniff`, HSTS pour un an et les drapeaux de cookie (`proxy_cookie_flags ~ secure samesite=lax`, sur nginx 1.18 via `proxy_cookie_path`). Puis vérifier avec curl – y compris les locations qui ont leur propre `add_header`.",
    ["Ce que l'audit a trouvé", "HSTS", "Pourquoi X-Frame-Options arrivait en double", "session_id : Secure et SameSite", "La correction", "Le piège add_header", "« Vieux nginx » – à quel point est-ce critique ?", "Revérifier"],
    "fr",
    "Sans HSTS, le navigateur essaie d'abord `http://` quand on tape le domaine, et reçoit du serveur la redirection vers https. Sur un Wi-Fi hostile, c'est précisément cette première requête non chiffrée qui peut être interceptée pour garder l'utilisateur en http (SSL stripping). Avec `Strict-Transport-Security`, le navigateur retient pendant `max-age` secondes que le domaine est en https uniquement. Commencer sans `includeSubDomains` ni `preload` tant que chaque sous-domaine n'a pas vraiment https – HSTS ne se retire pas vite des navigateurs qui l'ont mémorisé. Prudemment : `max-age=86400` pour un jour, puis un an.",
    ["Odoo pose lui-même `X-Frame-Options: DENY` sur la page de connexion et une partie du backend (protection contre le clickjacking).",
     "La configuration nginx avait son propre `add_header X-Frame-Options \"SAMEORIGIN\"` – résultat : deux en-têtes aux valeurs différentes. Les navigateurs réagissent alors de façon incohérente, les scanners signalent une mauvaise configuration.",
     "Supprimer simplement la ligne nginx ne suffit pas : seule la page de connexion est alors protégée, toutes les autres pages n'ont plus d'en-tête du tout (c'est exactement ce qu'a montré la première revérification).",
     "Correct : `proxy_hide_header X-Frame-Options;` retire la valeur d'Odoo, `add_header … always` pose une seule valeur sur chaque réponse. `SAMEORIGIN` plutôt que `DENY` si quelque chose sur le même domaine intègre Odoo ou Grafana dans une iframe."],
    "Odoo (jusqu'à 17) pose `session_id` seulement avec `HttpOnly` et `Path=/`. `Secure` garantit que le navigateur n'envoie jamais le cookie en http non chiffré – avec HSTS, cela ferme le vol de session par interception. `SameSite=Lax` tient le cookie à l'écart des requêtes POST inter-sites (CSRF) tout en l'envoyant lors des clics normaux sur des liens ; `Strict` casserait les liens des e-mails vers Odoo. nginx ajoute les drapeaux au retour : `proxy_cookie_flags` à partir de nginx 1.19.3, sur nginx 1.18 (Ubuntu 20.04) un contournement via `proxy_cookie_path` qui ajoute les drapeaux au chemin.",
    ["`add_header` n'est hérité du bloc `server` dans une `location` **que si cette location n'a pas d'`add_header` propre**. Les configurations Odoo ont souvent une location pour les fichiers statiques avec `add_header Cache-Control` – c'est exactement là que les en-têtes de sécurité disparaissent.",
     "Sans `always`, `add_header` ne s'applique qu'aux codes 200, 201, 204, 206, 301, 302, 303, 304, 307, 308 – pas à 401, 404 ou 502.",
     "Vérifier donc plusieurs URL : une page normale, la connexion, un fichier statique, une 404 et chaque location supplémentaire (par ex. `/grafana/`)."],
    "Le nginx 1.18 du dépôt Ubuntu reçoit des correctifs de sécurité rétroportés – le numéro de version seul n'est pas une vulnérabilité, et `server_tokens off` ne fait que le retirer de l'en-tête. Le vrai problème derrière : Ubuntu 20.04 est sorti du support standard en mai 2025. Sans Ubuntu Pro (ESM), le serveur ne reçoit plus de mises à jour de sécurité – ni pour nginx, ni pour OpenSSL, ni pour le noyau. Jusqu'à la migration prévue vers Ubuntu 24.04, rattacher l'Ubuntu Pro gratuit ; sur le nouveau serveur, utiliser `proxy_cookie_flags` au lieu du contournement.",
    "Après la correction, chaque URL vérifiée renvoyait exactement un `X-Frame-Options: SAMEORIGIN`, `nosniff`, HSTS pour un an, le cookie avec `Secure; SameSite=Lax` et `Server: nginx` sans version. Odoo, sa configuration et ses utilisateurs n'ont rien remarqué.",
    "Liens")

# ================================================================ EL
GRAFANA["t"]["el"] = _g(
    "Grafana πίσω από nginx στο /grafana/ δίπλα στο Odoo: μόνο localhost, ρυθμίσεις env και ένα location που δουλεύει",
    "Πώς κρύβουμε ένα container Grafana που ακούει στη θύρα 3000 για όλο το διαδίκτυο: δημοσίευση μόνο στο 127.0.0.1, ρύθμιση της υποδιαδρομής στο αρχείο env, προστασία με nginx Basic Auth και αποφυγή τριών παγίδων – η προωθημένη κεφαλίδα Authorization, τα regex locations που «κλέβουν» τα στατικά αρχεία και ένα auth proxy που αφήνει τον καθένα να μπει.",
    "Μια τυπική παρακολούθηση δίπλα στο Odoo: Prometheus, node_exporter, postgres_exporter και Grafana σε Docker στον ίδιο server. Σε έλεγχο ενός τέτοιου server, το Grafana έτρεχε με `-p 3000:3000` – και απαντούσε στο `http://erp.example.com:3000` για όλους, παρότι το `ufw` επέτρεπε μόνο SSH, 80 και 443. Χειρότερα: το **auth proxy** του Grafana ήταν ενεργό με κενή whitelist – όποιος έφτανε στη θύρα 3000 με τη σωστή κεφαλίδα θα συνδεόταν χωρίς κωδικό. Το άρθρο δείχνει πώς μεταφέρουμε το Grafana πίσω από τον υπάρχοντα nginx στο `https://erp.example.com/grafana/`.",
    "Συνοπτικά: `-p 127.0.0.1:3000:3000`· `GF_SERVER_ROOT_URL=https://erp.example.com/grafana/` + `GF_SERVER_SERVE_FROM_SUB_PATH=true`· στον nginx `location ^~ /grafana/` με Basic Auth, `proxy_set_header Authorization \"\"` και `proxy_pass http://127.0.0.1:3000;` χωρίς διαδρομή· auth proxy απενεργοποιημένο – ή μόνο με whitelist.",
    ["1. Κλείσιμο της θύρας", "2. Το αρχείο env του Grafana", "3. Το location του nginx", "4. Τυπικά σφάλματα", "5. Μία σύνδεση αντί για δύο", "6. Έλεγχος", "el"],
    ["Το `-p 3000:3000` σημαίνει `0.0.0.0:3000` **και** `[::]:3000`. Το Docker βάζει δικούς του κανόνες iptables πριν από το ufw – το `ufw status` φαίνεται σωστό, η θύρα όμως μένει ανοιχτή.",
     "Ο κίνδυνος δεν είναι μόνο το ίδιο το Grafana: τα dashboards δείχνουν ονόματα server, βάσεις, μερικές φορές ερωτήματα SQL της βάσης Odoo.",
     "Οι exporters (9100, 9187, 9090) χωρίς `ports:` μένουν μέσα στο δίκτυο Docker – ο Prometheus τους βρίσκει με το όνομα του container."],
    "Το Grafana διαβάζει κάθε επιλογή του `grafana.ini` από μεταβλητές `GF_<SECTION>_<KEY>`. Το σημαντικό για υποδιαδρομή: η δημόσια URL με τη διαδρομή και το `serve_from_sub_path`, ώστε το Grafana να απαντά το ίδιο στο `/grafana/`. Γράψτε ρητά `https` – το `%(protocol)s` είναι το πρωτόκολλο στο οποίο ακούει το ίδιο το Grafana (http), άρα οι ανακατευθύνσεις του θα πήγαιναν σε `http://`.",
    "Το location μπαίνει στο υπάρχον block `server` του Odoo για τη θύρα 443 – πιστοποιητικό, HSTS και οι υπόλοιπες κεφαλίδες ισχύουν και για το Grafana.",
    ["**`^~`** – ο nginx επιλέγει τα regex locations (`~* \\.(js|css|png)$`, `~ /static/`) πριν από ένα απλό πρόθεμα. Οι περισσότερες ρυθμίσεις Odoo τα έχουν για caching, και θα έστελναν το `/grafana/public/build/*.js` στο Odoo. Το `^~` σταματά την αναζήτηση regex για αυτό το πρόθεμα.",
     "**`Authorization \"\"`** – ο browser στέλνει τη σύνδεση Basic Auth του nginx σε αυτή την κεφαλίδα σε κάθε αίτημα. Το Grafana τη βλέπει και προσπαθεί να συνδεθεί με αυτήν → 401, στο log `password-auth.invalid`.",
     "**`X-WEBAUTH-USER \"\"`** – αν ποτέ ενεργοποιηθεί το auth proxy, ένας client δεν πρέπει ποτέ να μπορεί να ορίσει μόνος του αυτή την κεφαλίδα.",
     "**`proxy_pass` χωρίς URI** – με `serve_from_sub_path` το Grafana περιμένει την πλήρη διαδρομή `/grafana/…`· το `proxy_pass http://127.0.0.1:3000/;` θα την έκοβε."],
    ["Με Basic Auth στον nginx και τη δική του σύνδεση του Grafana, συνδέεστε δύο φορές. Αν αυτό ενοχλεί: ο nginx λέει στο Grafana ποιος είναι ο χρήστης – αλλά μόνο με whitelist, ώστε το Grafana να εμπιστεύεται την κεφαλίδα από τον nginx και από κανέναν άλλο.",
     "Η whitelist είναι η IP που βλέπει το Grafana ως client: με `-p 127.0.0.1:3000:3000` είναι το gateway του δικτύου Docker (`docker network inspect grafana`). Χωρίς whitelist – η κατάσταση από την αρχή – γίνεται αποδεκτή η κεφαλίδα από οποιονδήποτε client."],
    "Αναμενόμενο: θύρα 3000 κλειστή απ' έξω, το `/grafana/` ζητά τον κωδικό του nginx, μετά ανοίγει το Grafana με στυλ και live ενημερώσεις. Αν dashboards του Grafana ενσωματώνονται στο Odoo (iframe), αρκούν `GF_SECURITY_ALLOW_EMBEDDING=true` και `X-Frame-Options: SAMEORIGIN` στον nginx – ίδιο domain.",
    "Σύνδεσμοι")

AUDIT["t"]["el"] = _a(
    "Έλεγχος ασφαλείας nginx μπροστά από Odoo: HSTS, διπλό X-Frame-Options, cookie συνεδρίας χωρίς Secure/SameSite, παλιός nginx",
    "Τέσσερα ευρήματα πραγματικού σαρωτή ασφαλείας σε server Odoo – χωρίς HSTS, δύο διαφορετικά X-Frame-Options, session_id χωρίς Secure και SameSite, nginx 1.18 σε Ubuntu 20.04 – τι σημαίνει το καθένα, οι έξι γραμμές nginx που τα διόρθωσαν και η παγίδα του add_header που ξανακρύβει κεφαλίδες.",
    "Ένας εξωτερικός σαρωτής ασφαλείας σε παραγωγικό server Odoo (Odoo πίσω από nginx σε Ubuntu 20.04) ανέφερε: χωρίς HSTS, `X-Frame-Options` δύο φορές με διαφορετικές τιμές, το cookie `session_id` χωρίς `Secure` και `SameSite`, και παλιό nginx. Τίποτα από αυτά δεν είναι ανοιχτή πόρτα, αλλά το καθένα αποδυναμώνει την προστασία της συνεδρίας – και όλα διορθώθηκαν σε ένα τέταρτο χωρίς να αγγίξουμε το Odoo.",
    "Συνοπτικά: στο block server 443 `server_tokens off`, `proxy_hide_header X-Frame-Options` + ένα `add_header X-Frame-Options SAMEORIGIN always`, `nosniff`, HSTS για ένα χρόνο και σημαίες cookie (`proxy_cookie_flags ~ secure samesite=lax`, σε nginx 1.18 μέσω `proxy_cookie_path`). Μετά έλεγχος με curl – και στα locations με δικό τους `add_header`.",
    ["Τι βρήκε ο έλεγχος", "HSTS", "Γιατί το X-Frame-Options ερχόταν διπλό", "session_id: Secure και SameSite", "Η διόρθωση", "Η παγίδα του add_header", "«Παλιός nginx» – πόσο κρίσιμο είναι;", "Επανέλεγχος"],
    "el",
    "Χωρίς HSTS, ο browser δοκιμάζει πρώτα `http://` όταν κάποιος πληκτρολογεί το domain, και παίρνει από τον server την ανακατεύθυνση σε https. Σε εχθρικό Wi-Fi, ακριβώς αυτό το πρώτο μη κρυπτογραφημένο αίτημα μπορεί να υποκλαπεί και ο χρήστης να μείνει σε http (SSL stripping). Με `Strict-Transport-Security` ο browser θυμάται για `max-age` δευτερόλεπτα ότι το domain είναι μόνο https. Ξεκινήστε χωρίς `includeSubDomains` και `preload` μέχρι κάθε subdomain να έχει πραγματικά https – το HSTS δεν ανακαλείται γρήγορα από browsers που το έχουν αποθηκεύσει. Προσεκτικά: `max-age=86400` για μία μέρα, μετά ένας χρόνος.",
    ["Το ίδιο το Odoo βάζει `X-Frame-Options: DENY` στη σελίδα σύνδεσης και σε μέρη του backend (προστασία από clickjacking).",
     "Η ρύθμιση του nginx είχε δικό της `add_header X-Frame-Options \"SAMEORIGIN\"` – αποτέλεσμα: δύο κεφαλίδες με διαφορετικές τιμές. Οι browsers συμπεριφέρονται τότε ασυνεπώς, οι σαρωτές το αναφέρουν ως λάθος ρύθμιση.",
     "Η απλή διαγραφή της γραμμής του nginx δεν αρκεί: τότε προστατεύεται μόνο η σελίδα σύνδεσης, όλες οι άλλες σελίδες δεν έχουν καθόλου κεφαλίδα (ακριβώς αυτό έδειξε ο πρώτος επανέλεγχος).",
     "Σωστά: το `proxy_hide_header X-Frame-Options;` αφαιρεί την τιμή του Odoo, το `add_header … always` βάζει μία τιμή σε κάθε απάντηση. `SAMEORIGIN` αντί για `DENY` αν κάτι στο ίδιο domain ενσωματώνει το Odoo ή το Grafana σε iframe."],
    "Το Odoo (έως το 17) ορίζει το `session_id` μόνο με `HttpOnly` και `Path=/`. Το `Secure` εξασφαλίζει ότι ο browser δεν στέλνει ποτέ το cookie μέσω μη κρυπτογραφημένου http – μαζί με το HSTS κλείνει την κλοπή συνεδρίας μέσω υποκλοπής. Το `SameSite=Lax` κρατά το cookie μακριά από διαδικτυακά POST αιτήματα από άλλους ιστότοπους (CSRF), αλλά το στέλνει σε κανονικά κλικ συνδέσμων· το `Strict` θα χαλούσε τους συνδέσμους από e-mail προς το Odoo. Ο nginx προσθέτει τις σημαίες στην επιστροφή: `proxy_cookie_flags` από nginx 1.19.3, σε nginx 1.18 (Ubuntu 20.04) μια λύση μέσω `proxy_cookie_path` που προσθέτει τις σημαίες στη διαδρομή.",
    ["Το `add_header` κληρονομείται από το block `server` σε ένα `location` **μόνο αν αυτό το location δεν έχει δικό του `add_header`**. Οι ρυθμίσεις Odoo έχουν συχνά location για στατικά αρχεία με `add_header Cache-Control` – ακριβώς εκεί εξαφανίζονται οι κεφαλίδες ασφαλείας.",
     "Χωρίς `always`, το `add_header` ισχύει μόνο για 200, 201, 204, 206, 301, 302, 303, 304, 307, 308 – όχι για 401, 404 ή 502.",
     "Άρα ελέγξτε αρκετές URL: μια κανονική σελίδα, τη σύνδεση, ένα στατικό αρχείο, ένα 404 και κάθε επιπλέον location (π.χ. `/grafana/`)."],
    "Ο nginx 1.18 από το αποθετήριο του Ubuntu λαμβάνει μεταφερμένες διορθώσεις ασφαλείας – ο αριθμός έκδοσης μόνος του δεν είναι ευπάθεια, και το `server_tokens off` απλώς τον αφαιρεί από την κεφαλίδα. Το πραγματικό πρόβλημα πίσω από αυτό: το Ubuntu 20.04 βγήκε από την τυπική υποστήριξη τον Μάιο του 2025. Χωρίς Ubuntu Pro (ESM) ο server δεν λαμβάνει ενημερώσεις ασφαλείας – ούτε για nginx, ούτε για OpenSSL ή τον πυρήνα. Μέχρι τη σχεδιασμένη μετάβαση σε Ubuntu 24.04, συνδέστε το δωρεάν Ubuntu Pro· στον νέο server χρησιμοποιήστε `proxy_cookie_flags` αντί για τη λύση.",
    "Μετά τη διόρθωση κάθε ελεγμένη URL επέστρεφε ακριβώς ένα `X-Frame-Options: SAMEORIGIN`, `nosniff`, HSTS για ένα χρόνο, το cookie με `Secure; SameSite=Lax` και `Server: nginx` χωρίς έκδοση. Το ίδιο το Odoo, η ρύθμισή του και οι χρήστες του δεν παρατήρησαν τίποτα.",
    "Σύνδεσμοι")

# ================================================================ UK
GRAFANA["t"]["uk"] = _g(
    "Grafana за nginx на /grafana/ поруч з Odoo: лише localhost, налаштування env і робочий location",
    "Як сховати контейнер Grafana, який слухає порт 3000 для всього інтернету: публікувати лише на 127.0.0.1, налаштувати підшлях в env-файлі, захистити через nginx Basic Auth і обійти три пастки. Це заголовок Authorization, що передається далі; regex-location, які перехоплюють статичні файли; і auth proxy, який пускає будь-кого.",
    "Типовий моніторинг поруч з Odoo: Prometheus, node_exporter, postgres_exporter і Grafana в Docker на тому самому сервері. Під час перевірки такого сервера Grafana була запущена з `-p 3000:3000` і відповідала на `http://erp.example.com:3000` усім, хоча `ufw` дозволяв лише SSH, 80 і 443. Гірше того, в Grafana був увімкнений **auth proxy** з порожнім whitelist. Будь-хто, хто дістався порту 3000 і надіслав потрібний заголовок, увійшов би без пароля. У статті показано, як перенести Grafana за наявний nginx на `https://erp.example.com/grafana/`.",
    "Коротко: `-p 127.0.0.1:3000:3000`; `GF_SERVER_ROOT_URL=https://erp.example.com/grafana/` + `GF_SERVER_SERVE_FROM_SUB_PATH=true`; у nginx `location ^~ /grafana/` з Basic Auth, `proxy_set_header Authorization \"\"` і `proxy_pass http://127.0.0.1:3000;` без шляху; auth proxy вимкнений або лише з whitelist.",
    ["1. Закрити порт", "2. env-файл Grafana", "3. location у nginx", "4. Типові помилки", "5. Один вхід замість двох", "6. Перевірка", "uk"],
    ["`-p 3000:3000` означає `0.0.0.0:3000` **і** `[::]:3000`. Docker ставить власні правила iptables перед ufw, тож `ufw status` виглядає нормально, а порт однаково відкритий.",
     "Ризик не лише в самій Grafana: дашборди показують імена серверів, бази, іноді SQL-запити до бази Odoo.",
     "Експортери (9100, 9187, 9090) без `ports:` лишаються всередині мережі Docker, і Prometheus звертається до них за іменем контейнера."],
    "Grafana читає будь-яку опцію `grafana.ini` зі змінних `GF_<SECTION>_<KEY>`. Для підшляху важливі дві речі: публічна URL зі шляхом і `serve_from_sub_path`, щоб Grafana сама відповідала на `/grafana/`. Пишіть `https` явно: `%(protocol)s` — це протокол, на якому слухає сама Grafana (http), тому її редиректи йшли б на `http://`.",
    "location додається в наявний блок `server` Odoo для порту 443. Тоді сертифікат, HSTS та інші заголовки діють і для Grafana.",
    ["**`^~`**: nginx обирає regex-location (`~* \\.(js|css|png)$`, `~ /static/`) раніше за простий префікс. Більшість конфігів Odoo має такі location для кешування, і вони відправили б `/grafana/public/build/*.js` в Odoo. `^~` зупиняє пошук regex для цього префікса.",
     "**`Authorization \"\"`**: браузер надсилає логін nginx Basic Auth у цьому заголовку з кожним запитом. Grafana його бачить і пробує ним увійти, звідси 401 і в лозі `password-auth.invalid`.",
     "**`X-WEBAUTH-USER \"\"`**: якщо auth proxy колись увімкнуть, клієнт не повинен мати змоги сам виставити цей заголовок.",
     "**`proxy_pass` без URI**: з `serve_from_sub_path` Grafana чекає повний шлях `/grafana/…`, а `proxy_pass http://127.0.0.1:3000/;` його обрізав би."],
    ["З Basic Auth у nginx і власним входом Grafana доводиться входити двічі. Якщо це заважає, nginx може сам повідомляти Grafana, хто користувач. Але лише з whitelist, щоб Grafana довіряла заголовку від nginx і ні від кого більше.",
     "Whitelist — це IP, який Grafana бачить як клієнта. При `-p 127.0.0.1:3000:3000` це шлюз мережі Docker (`docker network inspect grafana`). Без whitelist, як на початку статті, Grafana довіряє заголовку від будь-якого клієнта."],
    "Очікуваний результат: порт 3000 ззовні закритий, `/grafana/` питає пароль nginx, після чого Grafana відкривається зі стилями й live-оновленнями. Якщо дашборди Grafana вбудовані в Odoo (iframe), достатньо `GF_SECURITY_ALLOW_EMBEDDING=true` і `X-Frame-Options: SAMEORIGIN` у nginx, бо домен той самий.",
    "Посилання")

AUDIT["t"]["uk"] = _a(
    "Аудит безпеки nginx перед Odoo: HSTS, подвійний X-Frame-Options, cookie сесії без Secure/SameSite, старий nginx",
    "Чотири знахідки реального сканера безпеки на сервері Odoo: немає HSTS, два різні X-Frame-Options, session_id без Secure і SameSite, nginx 1.18 на Ubuntu 20.04. Що означає кожна, шість рядків nginx, які все виправили, і пастка add_header, через яку заголовки знову зникають.",
    "Зовнішній сканер безпеки на робочому сервері Odoo (Odoo за nginx на Ubuntu 20.04) повідомив: немає HSTS, `X-Frame-Options` приходить двічі з різними значеннями, cookie `session_id` без `Secure` і `SameSite`, і старий nginx. Жодна з цих знахідок не є відчиненими дверима, але кожна послаблює захист сесії. Усе виправили за чверть години й навіть не торкалися Odoo.",
    "Коротко: у блоці server 443 потрібні `server_tokens off`, `proxy_hide_header X-Frame-Options` плюс один `add_header X-Frame-Options SAMEORIGIN always`, `nosniff`, HSTS на рік і прапорці cookie (`proxy_cookie_flags ~ secure samesite=lax`, на nginx 1.18 через `proxy_cookie_path`). Потім перевірка curl, зокрема location з власним `add_header`.",
    ["Що знайшов аудит", "HSTS", "Чому X-Frame-Options приходив двічі", "session_id: Secure і SameSite", "Виправлення", "Пастка add_header", "«Старий nginx»: наскільки це критично?", "Повторна перевірка"],
    "uk",
    "Без HSTS браузер спершу пробує `http://`, коли домен вводять вручну, і отримує від сервера редирект на https. У чужому Wi-Fi саме цей перший незашифрований запит можна перехопити й залишити користувача на http (SSL stripping). З `Strict-Transport-Security` браузер на `max-age` секунд запам'ятовує, що домен працює лише по https. Починайте без `includeSubDomains` і `preload`, доки кожен піддомен справді не матиме https: HSTS не можна швидко відкликати з браузерів, які його вже запам'ятали. Обережний варіант: `max-age=86400` на добу, потім рік.",
    ["Odoo сам ставить `X-Frame-Options: DENY` на сторінці входу і частині бекенду (захист від clickjacking).",
     "У конфігу nginx був власний `add_header X-Frame-Options \"SAMEORIGIN\"`. У результаті приходили два заголовки з різними значеннями. Браузери тоді поводяться непослідовно, а сканери бачать помилку конфігурації.",
     "Просто видалити рядок у nginx недостатньо. Тоді захищена лише сторінка входу, а всі інші сторінки зовсім без заголовка; саме це показала перша повторна перевірка.",
     "Правильно так: `proxy_hide_header X-Frame-Options;` прибирає значення Odoo, а `add_header … always` ставить одне значення на кожну відповідь. `SAMEORIGIN` замість `DENY` потрібен, якщо щось на тому самому домені вбудовує Odoo або Grafana в iframe."],
    "Odoo (до 17 включно) ставить `session_id` лише з `HttpOnly` і `Path=/`. `Secure` гарантує, що браузер ніколи не надішле cookie по незашифрованому http; разом з HSTS це закриває крадіжку сесії через перехоплення. `SameSite=Lax` не пускає cookie в міжсайтові POST-запити (CSRF), але надсилає його при звичайних переходах за посиланнями. `Strict` зламав би посилання з листів в Odoo. nginx додає прапорці у відповідь: `proxy_cookie_flags` з nginx 1.19.3, а на nginx 1.18 (Ubuntu 20.04) обхідний шлях через `proxy_cookie_path`, який дописує прапорці до шляху.",
    ["`add_header` успадковується з блоку `server` у `location`, **лише якщо в цьому location немає власного `add_header`**. У конфігах Odoo часто є location для статики з `add_header Cache-Control`, і саме там заголовки безпеки зникають.",
     "Без `always` `add_header` діє лише для 200, 201, 204, 206, 301, 302, 303, 304, 307, 308, але не для 401, 404 чи 502.",
     "Тому перевіряйте кілька URL: звичайну сторінку, вхід, статичний файл, 404 і кожен додатковий location (наприклад, `/grafana/`)."],
    "nginx 1.18 з репозиторію Ubuntu отримує перенесені виправлення безпеки, тож номер версії сам по собі не вразливість, а `server_tokens off` лише ховає його із заголовка. Справжня проблема в іншому: Ubuntu 20.04 вийшла зі стандартної підтримки в травні 2025. Без Ubuntu Pro (ESM) сервер не отримує оновлень безпеки ні для nginx, ні для OpenSSL, ні для ядра. До запланованого переїзду на Ubuntu 24.04 підключіть безкоштовний Ubuntu Pro, а на новому сервері використовуйте `proxy_cookie_flags` замість обхідного шляху.",
    "Після виправлення кожна перевірена URL віддавала рівно один `X-Frame-Options: SAMEORIGIN`, `nosniff`, HSTS на рік, cookie з `Secure; SameSite=Lax` і `Server: nginx` без версії. Сам Odoo, його конфіг і користувачі нічого не помітили.",
    "Посилання")

# ================================================================ RU
GRAFANA["t"]["ru"] = _g(
    "Grafana за nginx на /grafana/ рядом с Odoo: только localhost, настройки env и рабочий location",
    "Как спрятать контейнер Grafana, который слушает порт 3000 для всего интернета: публиковать только на 127.0.0.1, настроить подпуть в env-файле, защитить через nginx Basic Auth и обойти три ловушки. Это пробрасываемый заголовок Authorization; regex-location, которые перехватывают статику; и auth proxy, который пускает кого угодно.",
    "Типичный мониторинг рядом с Odoo: Prometheus, node_exporter, postgres_exporter и Grafana в Docker на том же сервере. При проверке такого сервера Grafana была запущена с `-p 3000:3000` и отвечала на `http://erp.example.com:3000` всем, хотя `ufw` разрешал только SSH, 80 и 443. Хуже того, в Grafana был включён **auth proxy** с пустым whitelist. Любой, кто достучался до порта 3000 и прислал нужный заголовок, вошёл бы без пароля. В статье показано, как перенести Grafana за существующий nginx на `https://erp.example.com/grafana/`.",
    "Коротко: `-p 127.0.0.1:3000:3000`; `GF_SERVER_ROOT_URL=https://erp.example.com/grafana/` + `GF_SERVER_SERVE_FROM_SUB_PATH=true`; в nginx `location ^~ /grafana/` с Basic Auth, `proxy_set_header Authorization \"\"` и `proxy_pass http://127.0.0.1:3000;` без пути; auth proxy выключен или только с whitelist.",
    ["1. Закрыть порт", "2. env-файл Grafana", "3. location в nginx", "4. Типичные ошибки", "5. Один вход вместо двух", "6. Проверка", "ru"],
    ["`-p 3000:3000` означает `0.0.0.0:3000` **и** `[::]:3000`. Docker ставит свои правила iptables раньше ufw, поэтому `ufw status` выглядит нормально, а порт всё равно открыт.",
     "Риск не только в самой Grafana: дашборды показывают имена серверов, базы, иногда SQL-запросы к базе Odoo.",
     "Экспортеры (9100, 9187, 9090) без `ports:` остаются внутри сети Docker, и Prometheus обращается к ним по имени контейнера."],
    "Grafana читает любую опцию `grafana.ini` из переменных `GF_<SECTION>_<KEY>`. Для подпути важны две вещи: публичный URL с путём и `serve_from_sub_path`, чтобы Grafana сама отвечала на `/grafana/`. Пишите `https` явно: `%(protocol)s` — это протокол, на котором слушает сама Grafana (http), поэтому её редиректы уходили бы на `http://`.",
    "location добавляется в существующий блок `server` Odoo для порта 443. Тогда сертификат, HSTS и остальные заголовки действуют и для Grafana.",
    ["**`^~`**: nginx выбирает regex-location (`~* \\.(js|css|png)$`, `~ /static/`) раньше простого префикса. В большинстве конфигов Odoo такие location есть для кэширования, и они отправили бы `/grafana/public/build/*.js` в Odoo. `^~` останавливает поиск regex для этого префикса.",
     "**`Authorization \"\"`**: браузер отправляет логин nginx Basic Auth в этом заголовке с каждым запросом. Grafana его видит и пытается им войти, отсюда 401 и в логе `password-auth.invalid`.",
     "**`X-WEBAUTH-USER \"\"`**: если auth proxy когда-нибудь включат, клиент не должен иметь возможности сам выставить этот заголовок.",
     "**`proxy_pass` без URI**: с `serve_from_sub_path` Grafana ждёт полный путь `/grafana/…`, а `proxy_pass http://127.0.0.1:3000/;` его обрезал бы."],
    ["С Basic Auth в nginx и собственным входом Grafana приходится входить дважды. Если это мешает, nginx может сам сообщать Grafana, кто пользователь. Но только с whitelist, чтобы Grafana доверяла заголовку от nginx и ни от кого больше.",
     "Whitelist — это IP, который Grafana видит как клиента. При `-p 127.0.0.1:3000:3000` это шлюз сети Docker (`docker network inspect grafana`). Без whitelist, как в начале статьи, Grafana доверяет заголовку от любого клиента."],
    "Ожидаемый результат: порт 3000 снаружи закрыт, `/grafana/` спрашивает пароль nginx, после чего Grafana открывается со стилями и live-обновлениями. Если дашборды Grafana встроены в Odoo (iframe), хватит `GF_SECURITY_ALLOW_EMBEDDING=true` и `X-Frame-Options: SAMEORIGIN` в nginx, потому что домен тот же.",
    "Ссылки")

AUDIT["t"]["ru"] = _a(
    "Аудит безопасности nginx перед Odoo: HSTS, двойной X-Frame-Options, cookie сессии без Secure/SameSite, старый nginx",
    "Четыре находки реального сканера безопасности на сервере Odoo: нет HSTS, два разных X-Frame-Options, session_id без Secure и SameSite, nginx 1.18 на Ubuntu 20.04. Что означает каждая, шесть строк nginx, которые всё исправили, и ловушка add_header, из-за которой заголовки снова пропадают.",
    "Внешний сканер безопасности на рабочем сервере Odoo (Odoo за nginx на Ubuntu 20.04) сообщил: нет HSTS, `X-Frame-Options` приходит дважды с разными значениями, cookie `session_id` без `Secure` и `SameSite`, и старый nginx. Ни одна из находок не открытая дверь, но каждая ослабляет защиту сессии. Всё исправили за четверть часа и даже не трогали Odoo.",
    "Коротко: в блоке server 443 нужны `server_tokens off`, `proxy_hide_header X-Frame-Options` плюс один `add_header X-Frame-Options SAMEORIGIN always`, `nosniff`, HSTS на год и флаги cookie (`proxy_cookie_flags ~ secure samesite=lax`, на nginx 1.18 через `proxy_cookie_path`). Потом проверка curl, в том числе location со своим `add_header`.",
    ["Что нашёл аудит", "HSTS", "Почему X-Frame-Options приходил дважды", "session_id: Secure и SameSite", "Исправление", "Ловушка add_header", "«Старый nginx»: насколько это критично?", "Повторная проверка"],
    "ru",
    "Без HSTS браузер сначала пробует `http://`, когда домен вводят вручную, и получает от сервера редирект на https. В чужом Wi-Fi именно этот первый незашифрованный запрос можно перехватить и оставить пользователя на http (SSL stripping). С `Strict-Transport-Security` браузер на `max-age` секунд запоминает, что домен работает только по https. Начинайте без `includeSubDomains` и `preload`, пока каждый поддомен действительно не будет на https: HSTS нельзя быстро отозвать из браузеров, которые его уже запомнили. Осторожный вариант: `max-age=86400` на сутки, потом год.",
    ["Odoo сам ставит `X-Frame-Options: DENY` на странице входа и в части бэкенда (защита от clickjacking).",
     "В конфиге nginx был свой `add_header X-Frame-Options \"SAMEORIGIN\"`. В итоге приходили два заголовка с разными значениями. Браузеры тогда ведут себя непоследовательно, а сканеры видят ошибку конфигурации.",
     "Просто удалить строку в nginx недостаточно. Тогда защищена только страница входа, а все остальные страницы совсем без заголовка; именно это показала первая повторная проверка.",
     "Правильно так: `proxy_hide_header X-Frame-Options;` убирает значение Odoo, а `add_header … always` ставит одно значение на каждый ответ. `SAMEORIGIN` вместо `DENY` нужен, если что-то на том же домене встраивает Odoo или Grafana в iframe."],
    "Odoo (до 17 включительно) ставит `session_id` только с `HttpOnly` и `Path=/`. `Secure` гарантирует, что браузер никогда не отправит cookie по незашифрованному http; вместе с HSTS это закрывает кражу сессии через перехват. `SameSite=Lax` не пускает cookie в межсайтовые POST-запросы (CSRF), но отправляет его при обычных переходах по ссылкам. `Strict` сломал бы ссылки из писем в Odoo. nginx добавляет флаги в ответ: `proxy_cookie_flags` с nginx 1.19.3, а на nginx 1.18 (Ubuntu 20.04) обходной путь через `proxy_cookie_path`, который дописывает флаги к пути.",
    ["`add_header` наследуется из блока `server` в `location`, **только если в этом location нет собственного `add_header`**. В конфигах Odoo часто есть location для статики с `add_header Cache-Control`, и именно там заголовки безопасности пропадают.",
     "Без `always` `add_header` действует только для 200, 201, 204, 206, 301, 302, 303, 304, 307, 308, но не для 401, 404 или 502.",
     "Поэтому проверяйте несколько URL: обычную страницу, вход, статический файл, 404 и каждый дополнительный location (например, `/grafana/`)."],
    "nginx 1.18 из репозитория Ubuntu получает перенесённые исправления безопасности, так что номер версии сам по себе не уязвимость, а `server_tokens off` лишь прячет его из заголовка. Настоящая проблема в другом: Ubuntu 20.04 вышла из стандартной поддержки в мае 2025. Без Ubuntu Pro (ESM) сервер не получает обновлений безопасности ни для nginx, ни для OpenSSL, ни для ядра. До запланированного переезда на Ubuntu 24.04 подключите бесплатный Ubuntu Pro, а на новом сервере используйте `proxy_cookie_flags` вместо обходного пути.",
    "После исправления каждый проверенный URL отдавал ровно один `X-Frame-Options: SAMEORIGIN`, `nosniff`, HSTS на год, cookie с `Secure; SameSite=Lax` и `Server: nginx` без версии. Сам Odoo, его конфиг и пользователи ничего не заметили.",
    "Ссылки")
