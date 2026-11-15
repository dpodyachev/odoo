# Статьи 8–9: пароль на страницу (nginx/Apache) + что закрыть в Odoo; пароли, утечки, перебор, 2FA в Odoo.
# Факты по Odoo сверены с исходниками Odoo 17 (web/controllers/database.py, service/db.py, base/models/res_users.py,
# auth_totp_mail_enforce, auth_password_policy).

AUTH = {
    "slug": "nginx-apache-password-protect-odoo-database-manager",
    "date": "2026-11-15",
    "tags": ["nginx", "Apache", "Basic Auth", "Odoo", "Security"],
    "code": {
        "htpasswd": ("bash", """sudo apt install apache2-utils            # provides htpasswd (also for nginx)
sudo htpasswd -c -B /etc/nginx/.htpasswd admin    # -c = new file, -B = bcrypt
sudo htpasswd -B /etc/nginx/.htpasswd anna         # add another user (without -c!)
sudo chown root:www-data /etc/nginx/.htpasswd && sudo chmod 640 /etc/nginx/.htpasswd"""),
        "nginx_basic": ("nginx", """location /intern/ {
    auth_basic           "Intern";
    auth_basic_user_file /etc/nginx/.htpasswd;
}"""),
        "apache_basic": ("Apache – VirtualHost or .htaccess", """<Location "/intern/">
    AuthType Basic
    AuthName "Intern"
    AuthUserFile /etc/apache2/.htpasswd
    Require valid-user
</Location>
# .htaccess works too, but only if the directory allows it: AllowOverride AuthConfig"""),
        "nginx_odoo": ("nginx – inside the Odoo server block", """# 1) database manager: office IP only, then a password on top
location ~ ^/web/database/ {
    allow 203.0.113.10;          # office / VPN
    deny  all;
    auth_basic           "Odoo DB";
    auth_basic_user_file /etc/nginx/.htpasswd;
    proxy_pass http://odoo;
}

# 2) installed apps list of the website module - nobody outside needs it
location = /website/info { return 404; }

# 3) slow down password guessing on the login form
#    (in the http block: limit_req_zone $binary_remote_addr zone=odoologin:10m rate=10r/m;)
location = /web/login {
    limit_req zone=odoologin burst=5 nodelay;
    proxy_pass http://odoo;
}"""),
        "apache_odoo": ("Apache – the same for mod_proxy", """<LocationMatch "^/web/database/">
    Require ip 203.0.113.10
</LocationMatch>
<Location "/website/info">
    Require all denied
</Location>"""),
        "odoo_conf": ("odoo.conf", """[options]
list_db = False                ; database manager off: create/drop/backup/restore are refused
dbfilter = ^mydb$              ; exactly one database (or ^%d$ = database named like the subdomain)
admin_passwd = <long random>   ; master password - Odoo stores it hashed after the first save
proxy_mode = True              ; real client IPs in logs (needed for limits and fail2ban)"""),
        "check": ("bash", """curl -s -o /dev/null -w "%{http_code}\\n" https://odoo.example.com/web/database/manager   # 401/403 from outside
curl -s -o /dev/null -w "%{http_code}\\n" https://odoo.example.com/web/database/selector  # 401/403
curl -s -o /dev/null -w "%{http_code}\\n" https://odoo.example.com/website/info           # 404
curl -s -o /dev/null -w "%{http_code}\\n" https://odoo.example.com/web/login              # 200
curl -s -u admin:WRONG -o /dev/null -w "%{http_code}\\n" https://2027.pp.ua/test/          # 401 - try it"""),
    },
    "links": [
        ("nginx: ngx_http_auth_basic_module", "https://nginx.org/en/docs/http/ngx_http_auth_basic_module.html"),
        ("Apache: Authentication and Authorization", "https://httpd.apache.org/docs/2.4/howto/auth.html"),
        ("Odoo 17: System configuration (security)", "https://www.odoo.com/documentation/17.0/administration/on_premise/deploy.html"),
        ("Demo: /test/ on this site (Cloudflare Pages Functions)", "https://2027.pp.ua/test/"),
    ],
    "t": {},
}

PWD = {
    "slug": "password-leaks-brute-force-2fa-odoo",
    "date": "2026-11-15",
    "tags": ["Security", "Passwords", "2FA", "Odoo", "fail2ban"],
    "code": {
        "hibp": ("bash · Pwned Passwords (k-anonymity)", """# only the first 5 characters of the SHA-1 hash leave your machine - never the password
read -rs -p "Password: " P; echo
H=$(printf '%s' "$P" | sha1sum | awk '{print toupper($1)}'); unset P
curl -s "https://api.pwnedpasswords.com/range/${H:0:5}" | grep -i "^${H:5}:" \\
  && echo "^ found in leaks (number = how often) - change it" || echo "not found in known leaks\""""),
        "cooldown": ("Odoo – Settings → Technical → System Parameters", """base.login_cooldown_after     = 5     # failed logins before the pause (0 = off)
base.login_cooldown_duration  = 60    # pause in seconds
auth_password_policy.minlength = 12   # module auth_password_policy"""),
        "fail2ban_filter": ("/etc/fail2ban/filter.d/odoo-login.conf", """[Definition]
failregex = ^.* INFO \\S+ odoo\\.addons\\.base\\.models\\.res_users: Login failed for db:\\S+ login:.* from <HOST>$
ignoreregex ="""),
        "fail2ban_jail": ("/etc/fail2ban/jail.d/odoo.conf", """[odoo-login]
enabled  = true
port     = http,https
filter   = odoo-login
logpath  = /var/log/odoo/odoo.log
maxretry = 5
findtime = 600
bantime  = 3600
# Odoo in Docker: the ban must hit the DOCKER-USER chain, e.g.
# action = iptables-allports[name=odoo, chain=DOCKER-USER]"""),
        "log": ("Odoo log", """... INFO mydb odoo.addons.base.models.res_users: Login failed for db:mydb login:admin from 198.51.100.7
... INFO mydb odoo.addons.base.models.res_users: Login successful for db:mydb login:anna from 203.0.113.10"""),
    },
    "links": [
        ("Have I Been Pwned", "https://haveibeenpwned.com/"),
        ("Pwned Passwords API (k-anonymity)", "https://haveibeenpwned.com/API/v3#PwnedPasswords"),
        ("Mozilla Monitor", "https://monitor.mozilla.org/"),
        ("Google Password Checkup", "https://passwords.google.com/checkup"),
        ("Odoo 17: Two-factor authentication", "https://www.odoo.com/documentation/17.0/applications/general/users/2fa.html"),
    ],
    "t": {},
}

# ---------------------------------------------------------------------------------------------------------------------
AUTH["t"]["de"] = {
    "title": "Passwortschutz mit nginx und Apache – und was man bei Odoo von außen schließen sollte",
    "summary": "HTTP Basic Auth mit htpasswd in nginx und Apache, IP-Freigaben, und die Odoo-Adressen, die nicht öffentlich sein sollten: Datenbank-Manager, Datenbank-Auswahl, /website/info – plus list_db und Login-Bremse.",
    "body": [
        ("h", "Basic Auth in 3 Minuten"),
        ("p", "Der Webserver fragt Benutzername und Passwort ab, bevor die Anfrage überhaupt die Anwendung erreicht. Einfach, robust und gut geeignet für Admin-Bereiche, Testsysteme und interne Seiten. Wichtig: nur über **HTTPS** – sonst gehen die Zugangsdaten im Klartext über die Leitung."),
        ("code", "htpasswd"),
        ("code", "nginx_basic"),
        ("code", "apache_basic"),
        ("note", "Ausprobieren: Die Seite https://2027.pp.ua/test/ ist genauso geschützt – hier allerdings über Cloudflare Pages Functions, weil diese Website statisch ist. Benutzername und Passwort liegen als Secret bei Cloudflare, nicht im Git-Repository."),
        ("h", "Was bei Odoo nicht öffentlich sein sollte"),
        ("table", [
            ["Adresse", "Was dort ist", "Empfehlung"],
            ["`/web/database/manager`", "Datenbank-Manager: anlegen, kopieren, löschen, sichern, wiederherstellen", "schließen (IP + Passwort) und `list_db = False`"],
            ["`/web/database/selector`", "Liste aller Datenbanken", "schließen"],
            ["`/web/database/*` (create, drop, backup, restore, duplicate, change_password, list)", "die Aktionen dahinter, geschützt nur durch das Master-Passwort", "schließen; mit `list_db = False` lehnt Odoo sie ab"],
            ["`/website/info`", "Liste installierter Apps und Version (Modul website)", "404 nach außen"],
            ["`/web/login`", "Anmeldung", "offen lassen, aber bremsen (siehe unten)"],
            ["`/xmlrpc/2/*`, `/jsonrpc`", "API für Schnittstellen", "nur offen, wenn Integrationen sie brauchen – dann mit API-Schlüsseln statt Passwörtern"],
        ]),
        ("p", "Der Datenbank-Manager ist der gefährlichste Punkt: Mit dem Master-Passwort kann man dort die gesamte Datenbank herunterladen oder löschen. Er gehört nie ungeschützt ins Internet."),
        ("h", "nginx vor Odoo"),
        ("code", "nginx_odoo"),
        ("h", "Apache vor Odoo"),
        ("code", "apache_odoo"),
        ("h", "Und in Odoo selbst"),
        ("code", "odoo_conf"),
        ("ul", [
            "`list_db = False` schaltet die Datenbankverwaltung ab – Odoo verweigert dann Anlegen, Löschen, Sichern und Wiederherstellen über Web und RPC. Backups macht man ohnehin besser mit `pg_dump` auf dem Server.",
            "Ein starkes `admin_passwd` bleibt trotzdem Pflicht.",
            "Ohne `proxy_mode = True` sieht Odoo hinter nginx nur dessen IP – dann greifen weder die Login-Bremse noch fail2ban richtig.",
        ]),
        ("h", "Prüfen"),
        ("code", "check"),
        ("links", "Weiterführend"),
    ],
}

AUTH["t"]["en"] = {
    "title": "Password protection with nginx and Apache – and what to close in Odoo",
    "summary": "HTTP Basic Auth with htpasswd in nginx and Apache, IP allow-lists, and the Odoo URLs that should not be public: database manager, database selector, /website/info – plus list_db and a login brake.",
    "body": [
        ("h", "Basic Auth in 3 minutes"),
        ("p", "The web server asks for a user name and password before the request even reaches the application. Simple, robust and well suited for admin areas, test systems and internal pages. Important: **HTTPS only** – otherwise credentials travel in plain text."),
        ("code", "htpasswd"),
        ("code", "nginx_basic"),
        ("code", "apache_basic"),
        ("note", "Try it: https://2027.pp.ua/test/ is protected the same way – here via Cloudflare Pages Functions, because this website is static. User name and password are stored as a secret at Cloudflare, not in the Git repository."),
        ("h", "What should not be public in Odoo"),
        ("table", [
            ["URL", "What is there", "Recommendation"],
            ["`/web/database/manager`", "database manager: create, duplicate, drop, back up, restore", "close (IP + password) and `list_db = False`"],
            ["`/web/database/selector`", "list of all databases", "close"],
            ["`/web/database/*` (create, drop, backup, restore, duplicate, change_password, list)", "the actions behind it, protected only by the master password", "close; with `list_db = False` Odoo refuses them"],
            ["`/website/info`", "installed apps and version (website module)", "404 from outside"],
            ["`/web/login`", "login", "keep open, but slow it down (see below)"],
            ["`/xmlrpc/2/*`, `/jsonrpc`", "API for integrations", "open only if integrations need it – then with API keys instead of passwords"],
        ]),
        ("p", "The database manager is the most dangerous spot: with the master password anyone can download or delete the whole database there. It never belongs on the internet unprotected."),
        ("h", "nginx in front of Odoo"),
        ("code", "nginx_odoo"),
        ("h", "Apache in front of Odoo"),
        ("code", "apache_odoo"),
        ("h", "And in Odoo itself"),
        ("code", "odoo_conf"),
        ("ul", [
            "`list_db = False` switches database management off – Odoo then refuses create, drop, backup and restore via web and RPC. Backups are better done with `pg_dump` on the server anyway.",
            "A strong `admin_passwd` is still a must.",
            "Without `proxy_mode = True`, Odoo behind nginx only sees nginx's IP – then neither the login brake nor fail2ban work properly.",
        ]),
        ("h", "Checks"),
        ("code", "check"),
        ("links", "Further reading"),
    ],
}

AUTH["t"]["uk"] = {
    "title": "Пароль на сторінку в nginx і Apache – і що закрити в Odoo ззовні",
    "summary": "HTTP Basic Auth із htpasswd у nginx і Apache, доступ за IP та адреси Odoo, які не мають бути публічними: менеджер баз, вибір бази, /website/info. Плюс list_db і гальмо для логіну.",
    "body": [
        ("h", "Basic Auth за 3 хвилини"),
        ("p", "Вебсервер питає логін і пароль ще до того, як запит дійде до застосунку. Просто, надійно й добре підходить для адмінок, тестових систем і внутрішніх сторінок. Важливо: **лише через HTTPS**, інакше логін і пароль ідуть мережею відкритим текстом."),
        ("code", "htpasswd"),
        ("code", "nginx_basic"),
        ("code", "apache_basic"),
        ("note", "Спробуйте: сторінка https://2027.pp.ua/test/ захищена так само, але через Cloudflare Pages Functions, бо цей сайт статичний. Логін і пароль зберігаються як секрет у Cloudflare, а не в Git-репозиторії."),
        ("h", "Що в Odoo не має бути публічним"),
        ("table", [
            ["Адреса", "Що там", "Рекомендація"],
            ["`/web/database/manager`", "менеджер баз: створити, скопіювати, видалити, бекап, відновлення", "закрити (IP + пароль) і `list_db = False`"],
            ["`/web/database/selector`", "список усіх баз", "закрити"],
            ["`/web/database/*` (create, drop, backup, restore, duplicate, change_password, list)", "самі дії, захищені лише майстер-паролем", "закрити; з `list_db = False` Odoo їх відхиляє"],
            ["`/website/info`", "встановлені застосунки й версія (модуль website)", "404 ззовні"],
            ["`/web/login`", "вхід", "лишити відкритим, але пригальмувати (див. нижче)"],
            ["`/xmlrpc/2/*`, `/jsonrpc`", "API для інтеграцій", "відкривати лише якщо потрібно інтеграціям, і тоді з API-ключами замість паролів"],
        ]),
        ("p", "Менеджер баз – найнебезпечніше місце: з майстер-паролем там можна завантажити або видалити всю базу. Без захисту йому не місце в інтернеті."),
        ("h", "nginx перед Odoo"),
        ("code", "nginx_odoo"),
        ("h", "Apache перед Odoo"),
        ("code", "apache_odoo"),
        ("h", "І в самому Odoo"),
        ("code", "odoo_conf"),
        ("ul", [
            "`list_db = False` вимикає керування базами: Odoo відмовляє у створенні, видаленні, бекапі й відновленні і через веб, і через RPC. Бекапи все одно краще робити `pg_dump` на сервері.",
            "Сильний `admin_passwd` однаково обов'язковий.",
            "Без `proxy_mode = True` Odoo за nginx бачить лише IP nginx, і тоді ні гальмо логіну, ні fail2ban нормально не працюють.",
        ]),
        ("h", "Перевірка"),
        ("code", "check"),
        ("links", "Докладніше"),
    ],
}

AUTH["t"]["ru"] = {
    "title": "Пароль на страницу в nginx и Apache – и что закрыть в Odoo снаружи",
    "summary": "HTTP Basic Auth с htpasswd в nginx и Apache, доступ по IP и адреса Odoo, которые не должны быть публичными: менеджер баз, выбор базы, /website/info. Плюс list_db и тормоз для логина.",
    "body": [
        ("h", "Basic Auth за 3 минуты"),
        ("p", "Веб-сервер спрашивает логин и пароль ещё до того, как запрос дойдёт до приложения. Просто, надёжно и хорошо подходит для админок, тестовых систем и внутренних страниц. Важно: **только через HTTPS**, иначе логин и пароль идут по сети открытым текстом."),
        ("code", "htpasswd"),
        ("code", "nginx_basic"),
        ("code", "apache_basic"),
        ("note", "Попробуйте: страница https://2027.pp.ua/test/ защищена так же, но через Cloudflare Pages Functions, потому что этот сайт статический. Логин и пароль хранятся как секрет в Cloudflare, а не в Git-репозитории."),
        ("h", "Что в Odoo не должно быть публичным"),
        ("table", [
            ["Адрес", "Что там", "Рекомендация"],
            ["`/web/database/manager`", "менеджер баз: создать, скопировать, удалить, бэкап, восстановление", "закрыть (IP + пароль) и `list_db = False`"],
            ["`/web/database/selector`", "список всех баз", "закрыть"],
            ["`/web/database/*` (create, drop, backup, restore, duplicate, change_password, list)", "сами действия, защищённые только мастер-паролем", "закрыть; с `list_db = False` Odoo их отклоняет"],
            ["`/website/info`", "установленные приложения и версия (модуль website)", "404 снаружи"],
            ["`/web/login`", "вход", "оставить открытым, но притормозить (см. ниже)"],
            ["`/xmlrpc/2/*`, `/jsonrpc`", "API для интеграций", "открывать только если нужно интеграциям, и тогда с API-ключами вместо паролей"],
        ]),
        ("p", "Менеджер баз – самое опасное место: с мастер-паролем там можно скачать или удалить всю базу. Без защиты ему не место в интернете."),
        ("h", "nginx перед Odoo"),
        ("code", "nginx_odoo"),
        ("h", "Apache перед Odoo"),
        ("code", "apache_odoo"),
        ("h", "И в самом Odoo"),
        ("code", "odoo_conf"),
        ("ul", [
            "`list_db = False` выключает управление базами: Odoo отказывает в создании, удалении, бэкапе и восстановлении и через веб, и через RPC. Бэкапы всё равно лучше делать `pg_dump` на сервере.",
            "Сильный `admin_passwd` всё равно обязателен.",
            "Без `proxy_mode = True` Odoo за nginx видит только IP nginx, и тогда ни тормоз логина, ни fail2ban нормально не работают.",
        ]),
        ("h", "Проверка"),
        ("code", "check"),
        ("links", "Подробнее"),
    ],
}

AUTH["t"]["fr"] = {
    "title": "Protéger une page par mot de passe avec nginx et Apache – et ce qu’il faut fermer dans Odoo",
    "summary": "HTTP Basic Auth avec htpasswd sous nginx et Apache, listes d’IP autorisées, et les adresses Odoo qui ne doivent pas être publiques : gestionnaire de bases, sélecteur de base, /website/info – plus list_db et un frein à la connexion.",
    "body": [
        ("h", "Basic Auth en 3 minutes"),
        ("p", "Le serveur web demande un identifiant et un mot de passe avant même que la requête n’atteigne l’application. Simple, robuste, idéal pour les espaces d’administration, les systèmes de test et les pages internes. Important : **uniquement en HTTPS** – sinon les identifiants circulent en clair."),
        ("code", "htpasswd"),
        ("code", "nginx_basic"),
        ("code", "apache_basic"),
        ("note", "Essayez : la page https://2027.pp.ua/test/ est protégée de la même façon – ici via Cloudflare Pages Functions, car ce site est statique. L’identifiant et le mot de passe sont stockés comme secret chez Cloudflare, pas dans le dépôt Git."),
        ("h", "Ce qui ne doit pas être public dans Odoo"),
        ("table", [
            ["Adresse", "Contenu", "Recommandation"],
            ["`/web/database/manager`", "gestionnaire de bases : créer, dupliquer, supprimer, sauvegarder, restaurer", "fermer (IP + mot de passe) et `list_db = False`"],
            ["`/web/database/selector`", "liste de toutes les bases", "fermer"],
            ["`/web/database/*` (create, drop, backup, restore, duplicate, change_password, list)", "les actions elles-mêmes, protégées seulement par le mot de passe maître", "fermer ; avec `list_db = False`, Odoo les refuse"],
            ["`/website/info`", "applications installées et version (module website)", "404 depuis l’extérieur"],
            ["`/web/login`", "connexion", "laisser ouvert, mais freiner (voir plus bas)"],
            ["`/xmlrpc/2/*`, `/jsonrpc`", "API pour les intégrations", "ouvrir seulement si des intégrations en ont besoin – alors avec des clés API au lieu de mots de passe"],
        ]),
        ("p", "Le gestionnaire de bases est le point le plus dangereux : avec le mot de passe maître, on peut y télécharger ou supprimer toute la base. Il n’a jamais sa place sur Internet sans protection."),
        ("h", "nginx devant Odoo"),
        ("code", "nginx_odoo"),
        ("h", "Apache devant Odoo"),
        ("code", "apache_odoo"),
        ("h", "Et dans Odoo lui-même"),
        ("code", "odoo_conf"),
        ("ul", [
            "`list_db = False` désactive la gestion des bases – Odoo refuse alors création, suppression, sauvegarde et restauration, par le web comme par RPC. Les sauvegardes se font de toute façon mieux avec `pg_dump` sur le serveur.",
            "Un `admin_passwd` robuste reste indispensable.",
            "Sans `proxy_mode = True`, Odoo derrière nginx ne voit que l’IP de nginx – ni le frein de connexion ni fail2ban ne fonctionnent alors correctement.",
        ]),
        ("h", "Vérifier"),
        ("code", "check"),
        ("links", "Pour aller plus loin"),
    ],
}

AUTH["t"]["el"] = {
    "title": "Κωδικός σε σελίδα με nginx και Apache – και τι πρέπει να κλείσει στο Odoo",
    "summary": "HTTP Basic Auth με htpasswd σε nginx και Apache, λίστες επιτρεπόμενων IP και οι διευθύνσεις του Odoo που δεν πρέπει να είναι δημόσιες: διαχείριση βάσεων, επιλογή βάσης, /website/info – συν list_db και φρένο στη σύνδεση.",
    "body": [
        ("h", "Basic Auth σε 3 λεπτά"),
        ("p", "Ο web server ζητά όνομα χρήστη και κωδικό πριν καν το αίτημα φτάσει στην εφαρμογή. Απλό, αξιόπιστο και ιδανικό για περιοχές διαχείρισης, δοκιμαστικά συστήματα και εσωτερικές σελίδες. Σημαντικό: **μόνο μέσω HTTPS** – αλλιώς τα στοιχεία περνούν ως απλό κείμενο."),
        ("code", "htpasswd"),
        ("code", "nginx_basic"),
        ("code", "apache_basic"),
        ("note", "Δοκιμάστε: η σελίδα https://2027.pp.ua/test/ προστατεύεται με τον ίδιο τρόπο – εδώ μέσω Cloudflare Pages Functions, επειδή αυτό το site είναι στατικό. Το όνομα χρήστη και ο κωδικός αποθηκεύονται ως secret στο Cloudflare, όχι στο αποθετήριο Git."),
        ("h", "Τι δεν πρέπει να είναι δημόσιο στο Odoo"),
        ("table", [
            ["Διεύθυνση", "Τι υπάρχει εκεί", "Σύσταση"],
            ["`/web/database/manager`", "διαχείριση βάσεων: δημιουργία, αντιγραφή, διαγραφή, backup, επαναφορά", "κλείσιμο (IP + κωδικός) και `list_db = False`"],
            ["`/web/database/selector`", "λίστα όλων των βάσεων", "κλείσιμο"],
            ["`/web/database/*` (create, drop, backup, restore, duplicate, change_password, list)", "οι ίδιες οι ενέργειες, προστατευμένες μόνο με τον master κωδικό", "κλείσιμο· με `list_db = False` το Odoo τις απορρίπτει"],
            ["`/website/info`", "εγκατεστημένες εφαρμογές και έκδοση (module website)", "404 προς τα έξω"],
            ["`/web/login`", "σύνδεση", "ανοιχτό, αλλά με φρένο (βλ. παρακάτω)"],
            ["`/xmlrpc/2/*`, `/jsonrpc`", "API για διασυνδέσεις", "ανοιχτό μόνο αν το χρειάζονται διασυνδέσεις – τότε με API keys αντί για κωδικούς"],
        ]),
        ("p", "Η διαχείριση βάσεων είναι το πιο επικίνδυνο σημείο: με τον master κωδικό μπορεί κανείς να κατεβάσει ή να διαγράψει ολόκληρη τη βάση. Δεν έχει θέση στο internet χωρίς προστασία."),
        ("h", "nginx μπροστά από το Odoo"),
        ("code", "nginx_odoo"),
        ("h", "Apache μπροστά από το Odoo"),
        ("code", "apache_odoo"),
        ("h", "Και μέσα στο ίδιο το Odoo"),
        ("code", "odoo_conf"),
        ("ul", [
            "Το `list_db = False` απενεργοποιεί τη διαχείριση βάσεων – το Odoo απορρίπτει δημιουργία, διαγραφή, backup και επαναφορά, μέσω web και RPC. Τα backups γίνονται ούτως ή άλλως καλύτερα με `pg_dump` στον server.",
            "Ένας ισχυρός `admin_passwd` παραμένει απαραίτητος.",
            "Χωρίς `proxy_mode = True`, το Odoo πίσω από nginx βλέπει μόνο την IP του nginx – τότε ούτε το φρένο σύνδεσης ούτε το fail2ban λειτουργούν σωστά.",
        ]),
        ("h", "Έλεγχος"),
        ("code", "check"),
        ("links", "Περισσότερα"),
    ],
}

# ---------------------------------------------------------------------------------------------------------------------
PWD["t"]["de"] = {
    "title": "Passwörter geleakt? Prüfen, und Odoo gegen Durchprobieren schützen – mit 2FA",
    "summary": "Wo man prüft, ob E-Mail und Passwort in Datenlecks auftauchen, ohne das Passwort preiszugeben – und was Odoo selbst kann: Login-Bremse, Passwortlänge, Zwei-Faktor-Anmeldung, API-Schlüssel, fail2ban.",
    "body": [
        ("h", "Steht meine Adresse in einem Datenleck?"),
        ("ul", [
            "**Have I Been Pwned** – E-Mail-Adresse eingeben, man sieht, in welchen bekannten Lecks sie vorkommt. Für eigene Domains gibt es eine Domain-Suche mit Benachrichtigung.",
            "**Mozilla Monitor** – dieselben Daten, mit laufender Überwachung per E-Mail.",
            "**Google Password Checkup** – prüft im Chrome/Google-Konto gespeicherte Passwörter.",
        ]),
        ("h", "Steht ein Passwort in Leaks – ohne es zu verraten?"),
        ("p", "Die Pwned-Passwords-API arbeitet mit **k-Anonymität**: Es werden nur die ersten 5 Zeichen des SHA-1-Hashes gesendet, der Server liefert alle passenden Hash-Enden zurück, der Vergleich passiert lokal. Das Passwort selbst verlässt den Rechner nie."),
        ("code", "hibp"),
        ("note", "Passwörter niemals in beliebige „Ist mein Passwort sicher?“-Formulare im Internet eintippen. Die k-Anonymitäts-Methode oben oder ein Passwortmanager mit eingebauter Leck-Prüfung (Bitwarden, 1Password, KeePassXC) sind sicher."),
        ("h", "Odoo: was schon eingebaut ist"),
        ("p", "**Login-Bremse.** Nach 5 Fehlversuchen von derselben IP-Adresse wartet Odoo 60 Sekunden, bevor die nächste Anmeldung von dort geprüft wird. Beides lässt sich in den Systemparametern ändern. Die Zählung läuft pro Odoo-Prozess – bei mehreren Workern ist sie also weicher, als die Zahl vermuten lässt."),
        ("code", "cooldown"),
        ("ul", [
            "**Mindestlänge** für Passwörter: Modul `auth_password_policy` (Parameter oben, z. B. 12).",
            "**Zwei-Faktor-Anmeldung (2FA):** Modul `auth_totp` – jeder Benutzer aktiviert sie in seinen Einstellungen mit einer Authenticator-App. Mit `auth_totp_mail_enforce` lässt sie sich in den Allgemeinen Einstellungen **erzwingen**: nur für Mitarbeiter oder für alle Benutzer.",
            "**API-Schlüssel** statt Passwörtern für Schnittstellen (Einstellungen des Benutzers → Kontosicherheit). Ein Schlüssel lässt sich einzeln widerrufen, und 2FA blockiert die Integration nicht.",
            "Den Benutzer `admin` umbenennen bzw. ein eigenes Login verwenden – `admin` wird als Erstes durchprobiert.",
        ]),
        ("h", "fail2ban: Angreifer auf Netzwerkebene aussperren"),
        ("p", "Odoo schreibt jeden Anmeldeversuch ins Log – mit IP-Adresse:"),
        ("code", "log"),
        ("p", "Daraus macht fail2ban eine Sperre in der Firewall. Voraussetzungen: `log_level` mindestens `info` (die Meldungen sind INFO) und `proxy_mode = True` hinter nginx – sonst steht im Log die IP von nginx."),
        ("code", "fail2ban_filter"),
        ("code", "fail2ban_jail"),
        ("h", "Checkliste"),
        ("ul", [
            "Datenbank-Manager geschlossen, `list_db = False` (siehe Artikel zu nginx/Apache).",
            "2FA für alle internen Benutzer erzwungen.",
            "Mindestlänge 12+, Passwortmanager im Team.",
            "Login-Bremse aktiv, zusätzlich `limit_req` in nginx oder fail2ban.",
            "Integrationen mit API-Schlüsseln, nicht mit Benutzerpasswörtern.",
            "Firmen-Domain bei Have I Been Pwned überwachen lassen.",
        ]),
        ("links", "Werkzeuge und Dokumentation"),
    ],
}

PWD["t"]["en"] = {
    "title": "Leaked passwords? How to check – and how to protect Odoo against guessing, with 2FA",
    "summary": "Where to check whether an e-mail address or password appears in data breaches without revealing the password – and what Odoo does itself: login brake, password length, two-factor login, API keys, fail2ban.",
    "body": [
        ("h", "Is my address in a data breach?"),
        ("ul", [
            "**Have I Been Pwned** – enter an e-mail address and see which known breaches it appears in. For your own domains there is a domain search with notifications.",
            "**Mozilla Monitor** – the same data, with ongoing monitoring by e-mail.",
            "**Google Password Checkup** – checks passwords saved in Chrome / your Google account.",
        ]),
        ("h", "Is a password in leaks – without revealing it?"),
        ("p", "The Pwned Passwords API uses **k-anonymity**: only the first 5 characters of the SHA-1 hash are sent, the server returns all matching hash suffixes, and the comparison happens locally. The password itself never leaves your machine."),
        ("code", "hibp"),
        ("note", "Never type passwords into random \"is my password safe?\" forms on the internet. The k-anonymity method above, or a password manager with a built-in breach check (Bitwarden, 1Password, KeePassXC), is safe."),
        ("h", "Odoo: what is already built in"),
        ("p", "**Login brake.** After 5 failed attempts from the same IP address, Odoo waits 60 seconds before it checks the next login from there. Both values can be changed in the system parameters. The counting is per Odoo process – with several workers it is softer than the number suggests."),
        ("code", "cooldown"),
        ("ul", [
            "**Minimum password length:** module `auth_password_policy` (parameter above, e.g. 12).",
            "**Two-factor login (2FA):** module `auth_totp` – each user enables it in their preferences with an authenticator app. With `auth_totp_mail_enforce` it can be **enforced** in General Settings: employees only or all users.",
            "**API keys** instead of passwords for integrations (user preferences → Account Security). A key can be revoked individually, and 2FA does not block the integration.",
            "Rename the `admin` user or use your own login – `admin` is the first one attackers try.",
        ]),
        ("h", "fail2ban: lock attackers out at the network level"),
        ("p", "Odoo logs every login attempt – with the IP address:"),
        ("code", "log"),
        ("p", "fail2ban turns this into a firewall ban. Requirements: `log_level` at least `info` (the messages are INFO) and `proxy_mode = True` behind nginx – otherwise the log shows nginx's IP."),
        ("code", "fail2ban_filter"),
        ("code", "fail2ban_jail"),
        ("h", "Checklist"),
        ("ul", [
            "Database manager closed, `list_db = False` (see the nginx/Apache article).",
            "2FA enforced for all internal users.",
            "Minimum length 12+, a password manager for the team.",
            "Login brake active, plus `limit_req` in nginx or fail2ban.",
            "Integrations with API keys, not user passwords.",
            "Have your company domain monitored by Have I Been Pwned.",
        ]),
        ("links", "Tools and documentation"),
    ],
}

PWD["t"]["uk"] = {
    "title": "Паролі витекли? Як перевірити – і як захистити Odoo від перебору, з 2FA",
    "summary": "Де перевірити, чи є e-mail і пароль у витоках, не розкриваючи сам пароль, і що вміє сам Odoo: гальмо логіну, довжина пароля, двофакторний вхід, API-ключі, fail2ban.",
    "body": [
        ("h", "Чи є моя адреса у витоку?"),
        ("ul", [
            "**Have I Been Pwned** – вводите e-mail і бачите, у яких відомих витоках він є. Для власних доменів є пошук за доменом зі сповіщеннями.",
            "**Mozilla Monitor** – ті самі дані з постійним моніторингом поштою.",
            "**Google Password Checkup** – перевіряє паролі, збережені в Chrome / акаунті Google.",
        ]),
        ("h", "Чи є пароль у витоках – не розкриваючи його?"),
        ("p", "API Pwned Passwords працює за принципом **k-анонімності**: надсилаються лише перші 5 символів SHA-1-хешу, сервер повертає всі закінчення хешів із цим початком, а порівняння відбувається локально. Сам пароль ніколи не покидає комп'ютер."),
        ("code", "hibp"),
        ("note", "Ніколи не вводьте паролі в будь-які форми «чи надійний мій пароль?» в інтернеті. Безпечні – метод k-анонімності вище або менеджер паролів із вбудованою перевіркою витоків (Bitwarden, 1Password, KeePassXC)."),
        ("h", "Odoo: що вже вбудовано"),
        ("p", "**Гальмо логіну.** Після 5 невдалих спроб з однієї IP-адреси Odoo чекає 60 секунд, перш ніж перевірити наступний вхід звідти. Обидва значення змінюються в системних параметрах. Лічильник ведеться окремо в кожному процесі Odoo, тож за кількох воркерів захист м'якший, ніж здається з цифри."),
        ("code", "cooldown"),
        ("ul", [
            "**Мінімальна довжина** пароля: модуль `auth_password_policy` (параметр вище, наприклад 12).",
            "**Двофакторний вхід (2FA):** модуль `auth_totp` – кожен користувач вмикає його у своїх налаштуваннях через застосунок-автентифікатор. З `auth_totp_mail_enforce` його можна **зробити обов'язковим** у загальних налаштуваннях: лише для співробітників або для всіх.",
            "**API-ключі** замість паролів для інтеграцій (налаштування користувача → Безпека облікового запису). Ключ можна відкликати окремо, і 2FA не блокує інтеграцію.",
            "Перейменуйте користувача `admin` або використовуйте власний логін: `admin` перебирають першим.",
        ]),
        ("h", "fail2ban: блокувати атакувальників на рівні мережі"),
        ("p", "Odoo пише в лог кожну спробу входу разом з IP-адресою:"),
        ("code", "log"),
        ("p", "fail2ban перетворює це на блокування у фаєрволі. Умови: `log_level` не нижче `info` (ці повідомлення мають рівень INFO) і `proxy_mode = True` за nginx, інакше в лозі буде IP nginx."),
        ("code", "fail2ban_filter"),
        ("code", "fail2ban_jail"),
        ("h", "Чек-лист"),
        ("ul", [
            "Менеджер баз закрито, `list_db = False` (див. статтю про nginx/Apache).",
            "2FA обов'язкова для всіх внутрішніх користувачів.",
            "Мінімальна довжина 12+, менеджер паролів для команди.",
            "Гальмо логіну ввімкнено, плюс `limit_req` у nginx або fail2ban.",
            "Інтеграції – з API-ключами, а не з паролями користувачів.",
            "Домен компанії – під моніторингом Have I Been Pwned.",
        ]),
        ("links", "Інструменти та документація"),
    ],
}

PWD["t"]["ru"] = {
    "title": "Пароли утекли? Как проверить – и как защитить Odoo от перебора, с 2FA",
    "summary": "Где проверить, есть ли e-mail и пароль в утечках, не раскрывая сам пароль, и что умеет сам Odoo: тормоз логина, длина пароля, двухфакторный вход, API-ключи, fail2ban.",
    "body": [
        ("h", "Есть ли мой адрес в утечке?"),
        ("ul", [
            "**Have I Been Pwned** – вводите e-mail и видите, в каких известных утечках он есть. Для своих доменов есть поиск по домену с уведомлениями.",
            "**Mozilla Monitor** – те же данные с постоянным мониторингом по почте.",
            "**Google Password Checkup** – проверяет пароли, сохранённые в Chrome / аккаунте Google.",
        ]),
        ("h", "Есть ли пароль в утечках – не раскрывая его?"),
        ("p", "API Pwned Passwords работает по принципу **k-анонимности**: отправляются только первые 5 символов SHA-1-хеша, сервер возвращает все окончания хешей с этим началом, а сравнение происходит локально. Сам пароль никогда не покидает компьютер."),
        ("code", "hibp"),
        ("note", "Никогда не вводите пароли в любые формы «надёжен ли мой пароль?» в интернете. Безопасны – метод k-анонимности выше или менеджер паролей со встроенной проверкой утечек (Bitwarden, 1Password, KeePassXC)."),
        ("h", "Odoo: что уже встроено"),
        ("p", "**Тормоз логина.** После 5 неудачных попыток с одного IP-адреса Odoo ждёт 60 секунд, прежде чем проверить следующий вход оттуда. Оба значения меняются в системных параметрах. Счётчик ведётся отдельно в каждом процессе Odoo, так что при нескольких воркерах защита мягче, чем кажется по цифре."),
        ("code", "cooldown"),
        ("ul", [
            "**Минимальная длина** пароля: модуль `auth_password_policy` (параметр выше, например 12).",
            "**Двухфакторный вход (2FA):** модуль `auth_totp` – каждый пользователь включает его в своих настройках через приложение-аутентификатор. С `auth_totp_mail_enforce` его можно **сделать обязательным** в общих настройках: только для сотрудников или для всех.",
            "**API-ключи** вместо паролей для интеграций (настройки пользователя → Безопасность учётной записи). Ключ можно отозвать отдельно, и 2FA не блокирует интеграцию.",
            "Переименуйте пользователя `admin` или используйте свой логин: `admin` перебирают первым.",
        ]),
        ("h", "fail2ban: блокировать атакующих на уровне сети"),
        ("p", "Odoo пишет в лог каждую попытку входа вместе с IP-адресом:"),
        ("code", "log"),
        ("p", "fail2ban превращает это в блокировку в файрволе. Условия: `log_level` не ниже `info` (эти сообщения имеют уровень INFO) и `proxy_mode = True` за nginx, иначе в логе будет IP nginx."),
        ("code", "fail2ban_filter"),
        ("code", "fail2ban_jail"),
        ("h", "Чек-лист"),
        ("ul", [
            "Менеджер баз закрыт, `list_db = False` (см. статью про nginx/Apache).",
            "2FA обязательна для всех внутренних пользователей.",
            "Минимальная длина 12+, менеджер паролей для команды.",
            "Тормоз логина включён, плюс `limit_req` в nginx или fail2ban.",
            "Интеграции – с API-ключами, а не с паролями пользователей.",
            "Домен компании – под мониторингом Have I Been Pwned.",
        ]),
        ("links", "Инструменты и документация"),
    ],
}

PWD["t"]["fr"] = {
    "title": "Mots de passe divulgués ? Comment vérifier – et protéger Odoo contre les tentatives répétées, avec 2FA",
    "summary": "Où vérifier si une adresse e-mail ou un mot de passe figure dans des fuites sans révéler le mot de passe – et ce qu’Odoo fait lui-même : frein de connexion, longueur minimale, double authentification, clés API, fail2ban.",
    "body": [
        ("h", "Mon adresse figure-t-elle dans une fuite ?"),
        ("ul", [
            "**Have I Been Pwned** – saisissez une adresse e-mail et voyez dans quelles fuites connues elle apparaît. Pour vos propres domaines, il existe une recherche par domaine avec notifications.",
            "**Mozilla Monitor** – les mêmes données, avec une surveillance continue par e-mail.",
            "**Google Password Checkup** – vérifie les mots de passe enregistrés dans Chrome / le compte Google.",
        ]),
        ("h", "Un mot de passe est-il dans des fuites – sans le révéler ?"),
        ("p", "L’API Pwned Passwords utilise la **k-anonymité** : seuls les 5 premiers caractères du hash SHA-1 sont envoyés, le serveur renvoie toutes les fins de hash correspondantes, et la comparaison se fait en local. Le mot de passe ne quitte jamais votre machine."),
        ("code", "hibp"),
        ("note", "Ne tapez jamais vos mots de passe dans des formulaires « mon mot de passe est-il sûr ? » trouvés sur Internet. La méthode par k-anonymité ci-dessus, ou un gestionnaire de mots de passe avec contrôle de fuites intégré (Bitwarden, 1Password, KeePassXC), est sûre."),
        ("h", "Odoo : ce qui est déjà intégré"),
        ("p", "**Frein de connexion.** Après 5 échecs depuis la même adresse IP, Odoo attend 60 secondes avant de vérifier la connexion suivante depuis celle-ci. Les deux valeurs se règlent dans les paramètres système. Le comptage se fait par processus Odoo – avec plusieurs workers, il est donc plus souple que le chiffre ne le laisse penser."),
        ("code", "cooldown"),
        ("ul", [
            "**Longueur minimale** des mots de passe : module `auth_password_policy` (paramètre ci-dessus, p. ex. 12).",
            "**Double authentification (2FA) :** module `auth_totp` – chaque utilisateur l’active dans ses préférences avec une application d’authentification. Avec `auth_totp_mail_enforce`, on peut l’**imposer** dans les paramètres généraux : employés seulement ou tous les utilisateurs.",
            "**Clés API** au lieu de mots de passe pour les intégrations (préférences de l’utilisateur → Sécurité du compte). Une clé se révoque individuellement, et la 2FA ne bloque pas l’intégration.",
            "Renommer l’utilisateur `admin` ou utiliser un identifiant propre – `admin` est le premier testé par les attaquants.",
        ]),
        ("h", "fail2ban : bloquer les attaquants au niveau réseau"),
        ("p", "Odoo journalise chaque tentative de connexion – avec l’adresse IP :"),
        ("code", "log"),
        ("p", "fail2ban en fait un blocage dans le pare-feu. Conditions : `log_level` au moins `info` (ces messages sont de niveau INFO) et `proxy_mode = True` derrière nginx – sinon le journal affiche l’IP de nginx."),
        ("code", "fail2ban_filter"),
        ("code", "fail2ban_jail"),
        ("h", "Liste de contrôle"),
        ("ul", [
            "Gestionnaire de bases fermé, `list_db = False` (voir l’article nginx/Apache).",
            "2FA imposée à tous les utilisateurs internes.",
            "Longueur minimale 12+, un gestionnaire de mots de passe pour l’équipe.",
            "Frein de connexion actif, plus `limit_req` dans nginx ou fail2ban.",
            "Intégrations avec des clés API, pas avec des mots de passe d’utilisateurs.",
            "Faire surveiller le domaine de l’entreprise par Have I Been Pwned.",
        ]),
        ("links", "Outils et documentation"),
    ],
}

PWD["t"]["el"] = {
    "title": "Διέρρευσαν κωδικοί; Πώς ελέγχετε – και πώς προστατεύετε το Odoo από δοκιμές κωδικών, με 2FA",
    "summary": "Πού ελέγχετε αν ένα e-mail ή ένας κωδικός εμφανίζεται σε διαρροές χωρίς να αποκαλύψετε τον κωδικό – και τι κάνει το ίδιο το Odoo: φρένο σύνδεσης, ελάχιστο μήκος, σύνδεση δύο παραγόντων, API keys, fail2ban.",
    "body": [
        ("h", "Υπάρχει η διεύθυνσή μου σε διαρροή;"),
        ("ul", [
            "**Have I Been Pwned** – εισάγετε e-mail και βλέπετε σε ποιες γνωστές διαρροές εμφανίζεται. Για δικά σας domains υπάρχει αναζήτηση ανά domain με ειδοποιήσεις.",
            "**Mozilla Monitor** – τα ίδια δεδομένα, με συνεχή παρακολούθηση μέσω e-mail.",
            "**Google Password Checkup** – ελέγχει κωδικούς αποθηκευμένους στον Chrome / στον λογαριασμό Google.",
        ]),
        ("h", "Υπάρχει ένας κωδικός σε διαρροές – χωρίς να τον αποκαλύψω;"),
        ("p", "Το API του Pwned Passwords λειτουργεί με **k-ανωνυμία**: στέλνονται μόνο οι πρώτοι 5 χαρακτήρες του SHA-1 hash, ο server επιστρέφει όλες τις καταλήξεις που ταιριάζουν και η σύγκριση γίνεται τοπικά. Ο ίδιος ο κωδικός δεν φεύγει ποτέ από τον υπολογιστή σας."),
        ("code", "hibp"),
        ("note", "Μην πληκτρολογείτε ποτέ κωδικούς σε τυχαίες φόρμες «είναι ασφαλής ο κωδικός μου;» στο internet. Ασφαλή είναι η μέθοδος k-ανωνυμίας παραπάνω ή ένας password manager με ενσωματωμένο έλεγχο διαρροών (Bitwarden, 1Password, KeePassXC)."),
        ("h", "Odoo: τι είναι ήδη ενσωματωμένο"),
        ("p", "**Φρένο σύνδεσης.** Μετά από 5 αποτυχημένες προσπάθειες από την ίδια IP, το Odoo περιμένει 60 δευτερόλεπτα πριν ελέγξει την επόμενη σύνδεση από εκεί. Και οι δύο τιμές αλλάζουν στις παραμέτρους συστήματος. Η μέτρηση γίνεται ανά διεργασία Odoo – με πολλούς workers είναι πιο χαλαρή απ' ό,τι δείχνει ο αριθμός."),
        ("code", "cooldown"),
        ("ul", [
            "**Ελάχιστο μήκος** κωδικού: module `auth_password_policy` (παράμετρος παραπάνω, π.χ. 12).",
            "**Σύνδεση δύο παραγόντων (2FA):** module `auth_totp` – κάθε χρήστης την ενεργοποιεί στις προτιμήσεις του με μια εφαρμογή authenticator. Με το `auth_totp_mail_enforce` μπορεί να γίνει **υποχρεωτική** στις γενικές ρυθμίσεις: μόνο για υπαλλήλους ή για όλους.",
            "**API keys** αντί για κωδικούς στις διασυνδέσεις (προτιμήσεις χρήστη → Ασφάλεια λογαριασμού). Ένα key ανακαλείται μεμονωμένα και το 2FA δεν μπλοκάρει τη διασύνδεση.",
            "Μετονομάστε τον χρήστη `admin` ή χρησιμοποιήστε δικό σας login – το `admin` δοκιμάζεται πρώτο.",
        ]),
        ("h", "fail2ban: αποκλεισμός επιτιθέμενων σε επίπεδο δικτύου"),
        ("p", "Το Odoo καταγράφει κάθε προσπάθεια σύνδεσης – μαζί με τη διεύθυνση IP:"),
        ("code", "log"),
        ("p", "Το fail2ban το μετατρέπει σε αποκλεισμό στο firewall. Προϋποθέσεις: `log_level` τουλάχιστον `info` (τα μηνύματα είναι επιπέδου INFO) και `proxy_mode = True` πίσω από nginx – αλλιώς το log δείχνει την IP του nginx."),
        ("code", "fail2ban_filter"),
        ("code", "fail2ban_jail"),
        ("h", "Λίστα ελέγχου"),
        ("ul", [
            "Διαχείριση βάσεων κλειστή, `list_db = False` (βλ. άρθρο για nginx/Apache).",
            "2FA υποχρεωτικό για όλους τους εσωτερικούς χρήστες.",
            "Ελάχιστο μήκος 12+, password manager για την ομάδα.",
            "Φρένο σύνδεσης ενεργό, συν `limit_req` στον nginx ή fail2ban.",
            "Διασυνδέσεις με API keys, όχι με κωδικούς χρηστών.",
            "Παρακολούθηση του domain της εταιρείας από το Have I Been Pwned.",
        ]),
        ("links", "Εργαλεία και τεκμηρίωση"),
    ],
}
