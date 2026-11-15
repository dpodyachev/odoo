# Статьи 5–6: Odoo в docker-compose + nginx; certbot и автопродление. Формат — как в blog_posts.py.
# FR/EL — в blog_posts_fr.py / blog_posts_el.py.

COMPOSE = {
    "slug": "odoo-docker-compose-extra-addons-nginx",
    "date": "2026-11-15",
    "tags": ["Docker", "odoo.conf", "extra-addons", "nginx"],
    "code": {
        "tree": ("/srv/odoo", """/srv/odoo/
├── docker-compose.yml
├── .env                      # passwords - never in Git
├── config/odoo.conf          # mounted as a directory
├── addons/
│   ├── custom/               # your own modules
│   └── oca/
│       ├── web/              # one OCA repository = one folder of modules
│       └── server-tools/
└── nginx/odoo.conf           # only for variant A (nginx in compose)"""),
        "compose": ("docker-compose.yml", """services:
  db:
    image: postgres:16
    restart: unless-stopped
    environment:
      POSTGRES_USER: odoo
      POSTGRES_PASSWORD: ${PG_PASSWORD}
      POSTGRES_DB: postgres
    volumes:
      - db-data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U odoo"]
      interval: 10s

  odoo:
    image: odoo:17
    restart: unless-stopped
    depends_on:
      db:
        condition: service_healthy
    command: odoo -c /etc/odoo/odoo.conf
    volumes:
      - ./config:/etc/odoo:ro                              # the directory, not a single file
      - ./addons/custom:/mnt/extra-addons/custom:ro
      - ./addons/oca:/mnt/extra-addons/oca:ro
      - odoo-data:/var/lib/odoo                            # filestore + sessions
    # variant A: no "ports" here - nginx reaches odoo over the compose network
    # variant B (nginx on the host): publish ONLY on localhost
    # ports:
    #   - "127.0.0.1:8069:8069"
    #   - "127.0.0.1:8072:8072"

volumes:
  db-data:
  odoo-data:"""),
        "conf": ("config/odoo.conf", """[options]
; paths INSIDE the container; Odoo adds its own core addons itself
addons_path = /mnt/extra-addons/custom,/mnt/extra-addons/oca/web,/mnt/extra-addons/oca/server-tools
data_dir = /var/lib/odoo

db_host = db
db_port = 5432
db_user = odoo
db_password = change-me              ; same as PG_PASSWORD in .env
list_db = False
admin_passwd = change-me-too

proxy_mode = True                    ; behind nginx: trust X-Forwarded-* headers
workers = 4
max_cron_threads = 1
gevent_port = 8072                   ; websocket (live chat, notifications)
limit_memory_soft = 2147483648
limit_memory_hard = 2684354560
limit_time_cpu = 600
limit_time_real = 1200"""),
        "nginx": ("nginx – odoo.conf", """upstream odoo     { server odoo:8069; }       # variant B: 127.0.0.1:8069
upstream odoochat { server odoo:8072; }       # variant B: 127.0.0.1:8072

map $http_upgrade $connection_upgrade { default upgrade; '' close; }

server {
    listen 80;
    server_name odoo.example.com;
    location /.well-known/acme-challenge/ { root /var/www/certbot; }
    location / { return 301 https://$host$request_uri; }
}

server {
    listen 443 ssl;
    http2 on;                         # nginx < 1.25.1: "listen 443 ssl http2;" instead
    server_name odoo.example.com;
    ssl_certificate     /etc/letsencrypt/live/odoo.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/odoo.example.com/privkey.pem;

    client_max_body_size 200m;
    proxy_read_timeout 720s;
    proxy_connect_timeout 720s;
    proxy_send_timeout 720s;

    proxy_set_header X-Forwarded-Host  $http_host;
    proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Real-IP         $remote_addr;

    location /websocket {
        proxy_pass http://odoochat;
        proxy_set_header Upgrade    $http_upgrade;
        proxy_set_header Connection $connection_upgrade;
        proxy_set_header X-Forwarded-Host  $http_host;
        proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Real-IP         $remote_addr;
    }

    location / {
        proxy_redirect off;
        proxy_pass http://odoo;
    }

    gzip on;
    gzip_types text/css text/plain application/json application/javascript text/xml;
}"""),
        "nginx_compose": ("docker-compose.yml – variant A", """  nginx:
    image: nginx:1.27
    restart: unless-stopped
    depends_on: [odoo]
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx:/etc/nginx/conf.d:ro                       # directory again
      - /etc/letsencrypt:/etc/letsencrypt:ro
      - ./certbot-www:/var/www/certbot:ro"""),
        "check": ("bash", """# which addons paths did Odoo really load?
docker compose logs odoo | grep "addons paths"

# is the config the one you think?
docker compose exec odoo grep -E "^(addons_path|proxy_mode|workers)" /etc/odoo/odoo.conf

# nginx: syntax + reload without downtime
docker compose exec nginx nginx -t && docker compose exec nginx nginx -s reload   # variant A
sudo nginx -t && sudo systemctl reload nginx                                       # variant B

# Odoo must NOT answer from outside on 8069 (variant B)
curl -m 5 -sI http://<server-ip>:8069/web/login || echo "closed - good\""""),
    },
    "t": {
        "de": {
            "title": "Odoo mit docker-compose: extra-addons, odoo.conf und nginx – im Container oder auf dem Host",
            "summary": "Wie man eigene und OCA-Module richtig einhängt, was in die odoo.conf gehört und wie nginx Odoo samt Websocket sauber weiterleitet – in beiden Varianten.",
            "body": [
                ("p", "Eine Odoo-Installation mit docker-compose ist schnell gestartet – die typischen Probleme kommen danach: Module tauchen nicht auf, Änderungen an der Konfiguration wirken nicht, der Chat verbindet sich nicht, oder Odoo ist plötzlich direkt aus dem Internet erreichbar. Hier ein Aufbau, der sich bewährt hat."),
                ("h", "Verzeichnisstruktur"),
                ("code", "tree"),
                ("h", "docker-compose.yml"),
                ("code", "compose"),
                ("ul", [
                    "**Verzeichnisse statt Einzeldateien mounten.** Wird nur `odoo.conf` als Datei eingehängt, sieht der Container nach `sed -i` oder einem Editor, der die Datei neu schreibt, die Änderung nicht – die neue Datei hat einen anderen Inode. Mit `./config:/etc/odoo` gibt es dieses Problem nicht.",
                    "Module `:ro` einhängen: Odoo braucht dort keine Schreibrechte.",
                    "Das offizielle Image läuft als Benutzer `odoo` (UID 101). Bei Bind-Mounts für Daten: `chown -R 101:101`.",
                ]),
                ("h", "odoo.conf"),
                ("code", "conf"),
                ("ul", [
                    "In `addons_path` stehen **Pfade im Container**, nicht auf dem Host.",
                    "Ein OCA-Repository ist ein Ordner mit vielen Modulen – **jedes Repository einzeln** eintragen. Der übergeordnete Ordner `oca/` allein reicht nicht.",
                    "Neue Module erscheinen erst nach Neustart und „Apps → App-Liste aktualisieren“ (oder `-u base`). Ohne `__manifest__.py` im Modulordner ist es kein Modul.",
                    "`proxy_mode = True` ist hinter nginx Pflicht – sonst sieht Odoo `http` statt `https` und die Client-IP von nginx.",
                ]),
                ("h", "nginx: eine Konfiguration, zwei Varianten"),
                ("p", "Odoo 17 braucht zwei Ziele: `8069` für alles und `8072` für `/websocket` (Live-Chat, Benachrichtigungen). Die Konfiguration ist in beiden Varianten gleich – nur die `upstream`-Adressen unterscheiden sich."),
                ("code", "nginx"),
                ("h", "Variante A: nginx im selben docker-compose"),
                ("code", "nginx_compose"),
                ("p", "nginx erreicht Odoo über den Dienstnamen `odoo` im Compose-Netz. Odoo veröffentlicht **keine** Ports – von außen ist nur nginx auf 80/443 sichtbar. Zertifikate kommen vom Host (`/etc/letsencrypt`, schreibgeschützt)."),
                ("h", "Variante B: nginx auf dem Host"),
                ("p", "Odoo-Ports nur auf `127.0.0.1` veröffentlichen (siehe auskommentierte `ports` oben), in nginx `upstream` auf `127.0.0.1:8069` und `127.0.0.1:8072` setzen."),
                ("note", "Achtung: `\"8069:8069\"` ohne `127.0.0.1` öffnet Odoo für das ganze Internet – **auch wenn ufw den Port sperrt**. Docker trägt seine Regeln direkt in iptables ein, an ufw vorbei."),
                ("h", "Prüfen"),
                ("code", "check"),
            ],
        },
        "en": {
            "title": "Odoo with docker-compose: extra-addons, odoo.conf and nginx – in a container or on the host",
            "summary": "How to mount your own and OCA modules correctly, what belongs in odoo.conf, and how nginx proxies Odoo including the websocket – in both variants.",
            "body": [
                ("p", "An Odoo installation with docker-compose starts quickly – the typical problems come afterwards: modules don't show up, config changes have no effect, the chat won't connect, or Odoo is suddenly reachable directly from the internet. Here is a setup that has proven itself."),
                ("h", "Directory layout"),
                ("code", "tree"),
                ("h", "docker-compose.yml"),
                ("code", "compose"),
                ("ul", [
                    "**Mount directories, not single files.** If only `odoo.conf` is mounted as a file, the container won't see changes made by `sed -i` or an editor that rewrites the file – the new file has a different inode. With `./config:/etc/odoo` that problem is gone.",
                    "Mount modules `:ro`: Odoo needs no write access there.",
                    "The official image runs as user `odoo` (UID 101). For bind mounts with data: `chown -R 101:101`.",
                ]),
                ("h", "odoo.conf"),
                ("code", "conf"),
                ("ul", [
                    "`addons_path` contains **paths inside the container**, not on the host.",
                    "An OCA repository is a folder with many modules – list **each repository separately**. The parent folder `oca/` alone is not enough.",
                    "New modules appear only after a restart and \"Apps → Update Apps List\" (or `-u base`). Without `__manifest__.py` in the folder it is not a module.",
                    "`proxy_mode = True` is mandatory behind nginx – otherwise Odoo sees `http` instead of `https` and nginx's IP instead of the client's.",
                ]),
                ("h", "nginx: one config, two variants"),
                ("p", "Odoo 17 needs two targets: `8069` for everything and `8072` for `/websocket` (live chat, notifications). The config is the same in both variants – only the `upstream` addresses differ."),
                ("code", "nginx"),
                ("h", "Variant A: nginx in the same docker-compose"),
                ("code", "nginx_compose"),
                ("p", "nginx reaches Odoo via the service name `odoo` on the compose network. Odoo publishes **no** ports – from outside only nginx on 80/443 is visible. Certificates come from the host (`/etc/letsencrypt`, read-only)."),
                ("h", "Variant B: nginx on the host"),
                ("p", "Publish the Odoo ports on `127.0.0.1` only (see the commented-out `ports` above), and point the nginx `upstream` to `127.0.0.1:8069` and `127.0.0.1:8072`."),
                ("note", "Warning: `\"8069:8069\"` without `127.0.0.1` opens Odoo to the whole internet – **even if ufw blocks the port**. Docker writes its rules straight into iptables, bypassing ufw."),
                ("h", "Checks"),
                ("code", "check"),
            ],
        },
        "uk": {
            "title": "Odoo у docker-compose: extra-addons, odoo.conf і nginx – у контейнері чи на хості",
            "summary": "Як правильно змонтувати власні й OCA-модулі, що має бути в odoo.conf і як nginx коректно проксить Odoo разом із websocket – в обох варіантах.",
            "body": [
                ("p", "Odoo в docker-compose запускається швидко, а типові проблеми починаються потім: модулі не з'являються, зміни конфігу не діють, чат не підключається, або Odoo раптом доступний напряму з інтернету. Ось схема, яка себе виправдала."),
                ("h", "Структура каталогів"),
                ("code", "tree"),
                ("h", "docker-compose.yml"),
                ("code", "compose"),
                ("ul", [
                    "**Монтуйте каталоги, а не окремі файли.** Якщо змонтовано лише файл `odoo.conf`, контейнер не побачить змін після `sed -i` або редактора, який перезаписує файл: у нового файлу інший inode. З `./config:/etc/odoo` цієї проблеми немає.",
                    "Модулі монтуйте з `:ro`: Odoo не потрібні права на запис туди.",
                    "Офіційний образ працює від користувача `odoo` (UID 101). Для bind-mount з даними: `chown -R 101:101`.",
                ]),
                ("h", "odoo.conf"),
                ("code", "conf"),
                ("ul", [
                    "В `addons_path` пишуться **шляхи всередині контейнера**, а не на хості.",
                    "OCA-репозиторій – це каталог із багатьма модулями. Кожен репозиторій треба вказати **окремо**, батьківського `oca/` недостатньо.",
                    "Нові модулі з'являються лише після перезапуску й «Додатки → Оновити список» (або `-u base`). Без `__manifest__.py` у каталозі це не модуль.",
                    "`proxy_mode = True` за nginx обов'язковий, інакше Odoo бачить `http` замість `https` і IP nginx замість клієнта.",
                ]),
                ("h", "nginx: один конфіг, два варіанти"),
                ("p", "Odoo 17 потрібні дві адреси: `8069` для всього і `8072` для `/websocket` (чат, сповіщення). Конфіг однаковий в обох варіантах, відрізняються лише адреси в `upstream`."),
                ("code", "nginx"),
                ("h", "Варіант А: nginx у тому самому docker-compose"),
                ("code", "nginx_compose"),
                ("p", "nginx звертається до Odoo за іменем сервісу `odoo` у мережі compose. Odoo **не** публікує порти, ззовні видно лише nginx на 80/443. Сертифікати беруться з хоста (`/etc/letsencrypt`, лише читання)."),
                ("h", "Варіант Б: nginx на хості"),
                ("p", "Порти Odoo публікуються лише на `127.0.0.1` (див. закоментовані `ports` вище), а в `upstream` nginx вказуються `127.0.0.1:8069` і `127.0.0.1:8072`."),
                ("note", "Увага: `\"8069:8069\"` без `127.0.0.1` відкриває Odoo всьому інтернету, **навіть якщо ufw блокує порт**. Docker пише свої правила прямо в iptables, повз ufw."),
                ("h", "Перевірка"),
                ("code", "check"),
            ],
        },
        "ru": {
            "title": "Odoo в docker-compose: extra-addons, odoo.conf и nginx – в контейнере или на хосте",
            "summary": "Как правильно смонтировать свои и OCA-модули, что должно быть в odoo.conf и как nginx корректно проксирует Odoo вместе с websocket – в обоих вариантах.",
            "body": [
                ("p", "Odoo в docker-compose запускается быстро, а типичные проблемы начинаются потом: модули не появляются, изменения конфига не действуют, чат не подключается, или Odoo вдруг доступен напрямую из интернета. Вот схема, которая себя оправдала."),
                ("h", "Структура каталогов"),
                ("code", "tree"),
                ("h", "docker-compose.yml"),
                ("code", "compose"),
                ("ul", [
                    "**Монтируйте каталоги, а не отдельные файлы.** Если смонтирован только файл `odoo.conf`, контейнер не увидит изменений после `sed -i` или редактора, который перезаписывает файл: у нового файла другой inode. С `./config:/etc/odoo` этой проблемы нет.",
                    "Модули монтируйте с `:ro`: Odoo не нужны права на запись туда.",
                    "Официальный образ работает от пользователя `odoo` (UID 101). Для bind-mount с данными: `chown -R 101:101`.",
                ]),
                ("h", "odoo.conf"),
                ("code", "conf"),
                ("ul", [
                    "В `addons_path` пишутся **пути внутри контейнера**, а не на хосте.",
                    "OCA-репозиторий – это каталог со многими модулями. Каждый репозиторий нужно указать **отдельно**, родительского `oca/` недостаточно.",
                    "Новые модули появляются только после перезапуска и «Приложения → Обновить список» (или `-u base`). Без `__manifest__.py` в каталоге это не модуль.",
                    "`proxy_mode = True` за nginx обязателен, иначе Odoo видит `http` вместо `https` и IP nginx вместо клиента.",
                ]),
                ("h", "nginx: один конфиг, два варианта"),
                ("p", "Odoo 17 нужны два адреса: `8069` для всего и `8072` для `/websocket` (чат, уведомления). Конфиг одинаковый в обоих вариантах, отличаются только адреса в `upstream`."),
                ("code", "nginx"),
                ("h", "Вариант А: nginx в том же docker-compose"),
                ("code", "nginx_compose"),
                ("p", "nginx обращается к Odoo по имени сервиса `odoo` в сети compose. Odoo **не** публикует порты, снаружи виден только nginx на 80/443. Сертификаты берутся с хоста (`/etc/letsencrypt`, только чтение)."),
                ("h", "Вариант Б: nginx на хосте"),
                ("p", "Порты Odoo публикуются только на `127.0.0.1` (см. закомментированные `ports` выше), а в `upstream` nginx указываются `127.0.0.1:8069` и `127.0.0.1:8072`."),
                ("note", "Внимание: `\"8069:8069\"` без `127.0.0.1` открывает Odoo всему интернету, **даже если ufw блокирует порт**. Docker пишет свои правила прямо в iptables, в обход ufw."),
                ("h", "Проверка"),
                ("code", "check"),
            ],
        },
    },
}

CERTBOT = {
    "slug": "certbot-nginx-auto-renewal",
    "date": "2026-11-15",
    "tags": ["nginx", "certbot", "Let's Encrypt", "systemd"],
    "code": {
        "host": ("bash · nginx on the host", """sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d odoo.example.com
# certbot edits the nginx server block and reloads nginx itself"""),
        "webroot": ("bash · nginx in docker-compose", """# nginx serves /.well-known/acme-challenge/ from ./certbot-www (see the Odoo + nginx article)
sudo apt install certbot
sudo certbot certonly --webroot -w /srv/odoo/certbot-www -d odoo.example.com
# certificates land in /etc/letsencrypt, mounted read-only into the nginx container"""),
        "hook": ("/etc/letsencrypt/renewal-hooks/deploy/reload-nginx.sh", """#!/bin/sh
# runs ONLY after a certificate was actually renewed
# nginx on the host:
systemctl reload nginx
# nginx in docker-compose (use this line instead):
# docker compose -f /srv/odoo/docker-compose.yml exec -T nginx nginx -s reload"""),
        "timer_check": ("bash", """systemctl list-timers | grep -i certbot      # certbot.timer (apt) or snap.certbot.renew.timer (snap)
sudo certbot renew --dry-run                  # full rehearsal against the staging server
sudo certbot certificates                     # domains and expiry dates"""),
        "timer": ("/etc/systemd/system/certbot-renew.service + .timer", """# certbot-renew.service
[Unit]
Description=Renew Let's Encrypt certificates

[Service]
Type=oneshot
ExecStart=/usr/bin/certbot renew --quiet

# certbot-renew.timer
[Unit]
Description=Twice a day: certbot renew

[Timer]
OnCalendar=*-*-* 03,15:17:00
RandomizedDelaySec=1h
Persistent=true

[Install]
WantedBy=timers.target

# enable:
#   sudo systemctl daemon-reload && sudo systemctl enable --now certbot-renew.timer"""),
        "cron": ("/etc/cron.d/certbot-renew", """17 3,15 * * * root certbot renew --quiet"""),
        "monitor": ("bash · check-cert.sh", """#!/bin/sh
# exit code 1 and a message if the certificate expires in less than 14 days
D=odoo.example.com
END=$(echo | openssl s_client -servername $D -connect $D:443 2>/dev/null | openssl x509 -noout -enddate | cut -d= -f2)
echo | openssl s_client -servername $D -connect $D:443 2>/dev/null \\
  | openssl x509 -noout -checkend $((14*86400)) >/dev/null \\
  || { echo "certificate for $D expires: $END"; exit 1; }"""),
    },
    "t": {
        "de": {
            "title": "Certbot für nginx – und wie die Erneuerung nie vergessen wird",
            "summary": "Zertifikat holen (nginx auf dem Host oder im Container), automatisch erneuern per systemd-Timer oder Cron, nginx nach der Erneuerung neu laden und den Ablauf selbst überwachen.",
            "body": [
                ("p", "Ein abgelaufenes Zertifikat legt Odoo genauso lahm wie ein Serverausfall: Browser blockieren die Seite, Schnittstellen und Apps brechen ab. Zwei Entwicklungen machen das Thema dringender: Let's Encrypt verschickt **seit 2025 keine Ablauf-E-Mails mehr**, und die Laufzeit der Zertifikate wird **schrittweise verkürzt** (Ziel: 45 Tage bis 2028). Manuelles Erneuern ist damit keine Option mehr."),
                ("h", "1. Zertifikat holen"),
                ("p", "**nginx auf dem Host** – das nginx-Plugin erledigt alles:"),
                ("code", "host"),
                ("p", "**nginx im docker-compose** – Methode `webroot`: nginx im Container liefert die Prüfdatei aus, certbot läuft auf dem Host:"),
                ("code", "webroot"),
                ("h", "2. nginx nach der Erneuerung neu laden"),
                ("p", "certbot erneuert die Dateien – aber nginx liefert weiter das alte Zertifikat aus dem Speicher aus, bis es neu geladen wird. Ein Deploy-Hook wird **nur nach einer tatsächlichen Erneuerung** ausgeführt:"),
                ("code", "hook"),
                ("p", "Nicht vergessen: `chmod +x` für das Skript."),
                ("h", "3. Automatisch erneuern"),
                ("p", "Das Debian/Ubuntu-Paket bringt bereits einen systemd-Timer mit (zweimal täglich), die Snap-Variante ebenfalls. Erneuert wird, sobald weniger als 30 Tage übrig sind. Prüfen:"),
                ("code", "timer_check"),
                ("p", "Fehlt der Timer (z. B. bei pip-Installation), einen eigenen anlegen. Ich bevorzuge systemd-Timer gegenüber Cron: Ausgaben landen im Journal (`journalctl -u certbot-renew`), und `Persistent=true` holt verpasste Läufe nach einem Neustart nach."),
                ("code", "timer"),
                ("p", "Die Cron-Variante in einer Zeile:"),
                ("code", "cron"),
                ("h", "4. Selbst überwachen – nicht auf E-Mails verlassen"),
                ("p", "Automatik kann still scheitern: DNS geändert, Port 80 geschlossen, Hook-Fehler. Deshalb den tatsächlich ausgelieferten Ablaufzeitpunkt von außen prüfen – täglich, mit Alarm:"),
                ("code", "monitor"),
                ("ul", [
                    "Das Skript per Timer täglich starten und bei Exit-Code 1 eine Nachricht schicken (E-Mail, Telegram-Bot).",
                    "Mit Prometheus übernimmt das der `blackbox_exporter`: Metrik `probe_ssl_earliest_cert_expiry`, Alarm bei weniger als 14 Tagen.",
                    "Nach jeder Änderung an nginx oder DNS einmal `certbot renew --dry-run`.",
                ]),
            ],
        },
        "en": {
            "title": "Certbot for nginx – and how renewal is never forgotten",
            "summary": "Getting the certificate (nginx on the host or in a container), renewing automatically with a systemd timer or cron, reloading nginx after renewal and monitoring the expiry yourself.",
            "body": [
                ("p", "An expired certificate takes Odoo down just like a server outage: browsers block the site, integrations and apps fail. Two changes make this more urgent: Let's Encrypt **stopped sending expiry e-mails in 2025**, and certificate lifetimes are being **shortened step by step** (target: 45 days by 2028). Renewing by hand is no longer an option."),
                ("h", "1. Get the certificate"),
                ("p", "**nginx on the host** – the nginx plugin does everything:"),
                ("code", "host"),
                ("p", "**nginx in docker-compose** – the `webroot` method: nginx in the container serves the challenge file, certbot runs on the host:"),
                ("code", "webroot"),
                ("h", "2. Reload nginx after renewal"),
                ("p", "certbot renews the files – but nginx keeps serving the old certificate from memory until it is reloaded. A deploy hook runs **only after an actual renewal**:"),
                ("code", "hook"),
                ("p", "Don't forget `chmod +x` for the script."),
                ("h", "3. Renew automatically"),
                ("p", "The Debian/Ubuntu package already ships a systemd timer (twice a day), and so does the snap. Renewal happens once fewer than 30 days are left. Check:"),
                ("code", "timer_check"),
                ("p", "If the timer is missing (e.g. a pip install), create your own. I prefer systemd timers to cron: output goes to the journal (`journalctl -u certbot-renew`), and `Persistent=true` catches up on runs missed during a reboot."),
                ("code", "timer"),
                ("p", "The cron variant in one line:"),
                ("code", "cron"),
                ("h", "4. Monitor it yourself – don't rely on e-mails"),
                ("p", "Automation can fail silently: DNS changed, port 80 closed, a broken hook. So check the expiry of the certificate actually being served, from outside – daily, with an alert:"),
                ("code", "monitor"),
                ("ul", [
                    "Run the script daily via a timer and send a message on exit code 1 (e-mail, Telegram bot).",
                    "With Prometheus, the `blackbox_exporter` does it: metric `probe_ssl_earliest_cert_expiry`, alert below 14 days.",
                    "After every change to nginx or DNS, run `certbot renew --dry-run` once.",
                ]),
            ],
        },
        "uk": {
            "title": "Certbot для nginx – і як ніколи не забути про продовження",
            "summary": "Отримати сертифікат (nginx на хості або в контейнері), продовжувати автоматично через systemd-таймер або cron, перезавантажувати nginx після продовження і самостійно стежити за терміном.",
            "body": [
                ("p", "Прострочений сертифікат кладе Odoo так само, як падіння сервера: браузери блокують сайт, інтеграції й застосунки перестають працювати. Дві зміни роблять тему ще гострішою: Let's Encrypt **з 2025 року більше не надсилає листи про закінчення терміну**, а термін дії сертифікатів **поступово скорочують** (мета – 45 днів до 2028 року). Продовжувати вручну вже не варіант."),
                ("h", "1. Отримати сертифікат"),
                ("p", "**nginx на хості**: плагін nginx робить усе сам:"),
                ("code", "host"),
                ("p", "**nginx у docker-compose**: метод `webroot`, nginx у контейнері віддає файл перевірки, а certbot працює на хості:"),
                ("code", "webroot"),
                ("h", "2. Перезавантажити nginx після продовження"),
                ("p", "certbot оновлює файли, але nginx віддає старий сертифікат із пам'яті, доки його не перезавантажити. Deploy-hook виконується **лише після реального продовження**:"),
                ("code", "hook"),
                ("p", "Не забудьте `chmod +x` для скрипта."),
                ("h", "3. Продовжувати автоматично"),
                ("p", "Пакет Debian/Ubuntu уже містить systemd-таймер (двічі на день), версія зі snap – теж. Сертифікат продовжується, коли лишається менше 30 днів. Перевірка:"),
                ("code", "timer_check"),
                ("p", "Якщо таймера немає (наприклад, certbot поставлено через pip), створіть свій. Я віддаю перевагу systemd-таймерам, а не cron: вивід іде в журнал (`journalctl -u certbot-renew`), а `Persistent=true` доганяє запуски, пропущені через перезавантаження."),
                ("code", "timer"),
                ("p", "Варіант із cron в один рядок:"),
                ("code", "cron"),
                ("h", "4. Стежити самому, а не чекати листів"),
                ("p", "Автоматика може зламатися тихо: змінили DNS, закрили порт 80, помилка в hook. Тому перевіряйте термін сертифіката, який реально віддається, ззовні – щодня, з алертом:"),
                ("code", "monitor"),
                ("ul", [
                    "Запускати скрипт щодня таймером і при коді виходу 1 надсилати повідомлення (e-mail, Telegram-бот).",
                    "З Prometheus це робить `blackbox_exporter`: метрика `probe_ssl_earliest_cert_expiry`, алерт, коли лишається менше 14 днів.",
                    "Після кожної зміни nginx або DNS один раз запускати `certbot renew --dry-run`.",
                ]),
            ],
        },
        "ru": {
            "title": "Certbot для nginx – и как никогда не забыть о продлении",
            "summary": "Получить сертификат (nginx на хосте или в контейнере), продлевать автоматически через systemd-таймер или cron, перезагружать nginx после продления и самому следить за сроком.",
            "body": [
                ("p", "Просроченный сертификат кладёт Odoo так же, как падение сервера: браузеры блокируют сайт, интеграции и приложения перестают работать. Два изменения делают тему ещё острее: Let's Encrypt **с 2025 года больше не присылает письма об истечении срока**, а срок действия сертификатов **постепенно сокращают** (цель – 45 дней к 2028 году). Продлевать вручную уже не вариант."),
                ("h", "1. Получить сертификат"),
                ("p", "**nginx на хосте**: плагин nginx делает всё сам:"),
                ("code", "host"),
                ("p", "**nginx в docker-compose**: метод `webroot`, nginx в контейнере отдаёт файл проверки, а certbot работает на хосте:"),
                ("code", "webroot"),
                ("h", "2. Перезагрузить nginx после продления"),
                ("p", "certbot обновляет файлы, но nginx отдаёт старый сертификат из памяти, пока его не перезагрузить. Deploy-hook выполняется **только после реального продления**:"),
                ("code", "hook"),
                ("p", "Не забудьте `chmod +x` для скрипта."),
                ("h", "3. Продлевать автоматически"),
                ("p", "Пакет Debian/Ubuntu уже содержит systemd-таймер (дважды в день), версия из snap – тоже. Сертификат продлевается, когда остаётся меньше 30 дней. Проверка:"),
                ("code", "timer_check"),
                ("p", "Если таймера нет (например, certbot поставлен через pip), создайте свой. Я предпочитаю systemd-таймеры, а не cron: вывод идёт в журнал (`journalctl -u certbot-renew`), а `Persistent=true` догоняет запуски, пропущенные из-за перезагрузки."),
                ("code", "timer"),
                ("p", "Вариант с cron в одну строку:"),
                ("code", "cron"),
                ("h", "4. Следить самому, а не ждать писем"),
                ("p", "Автоматика может сломаться тихо: сменили DNS, закрыли порт 80, ошибка в hook. Поэтому проверяйте срок сертификата, который реально отдаётся, снаружи – ежедневно, с алертом:"),
                ("code", "monitor"),
                ("ul", [
                    "Запускать скрипт ежедневно таймером и при коде выхода 1 отправлять сообщение (e-mail, Telegram-бот).",
                    "С Prometheus это делает `blackbox_exporter`: метрика `probe_ssl_earliest_cert_expiry`, алерт, когда остаётся меньше 14 дней.",
                    "После каждого изменения nginx или DNS один раз запускать `certbot renew --dry-run`.",
                ]),
            ],
        },
    },
}
