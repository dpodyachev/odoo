# Статья 10: Cloudflare Access (Zero Trust) по шагам; связь с Pages Functions (Basic Auth) и демо /test/, /test2/.
# Ссылки "@blog:<slug>" build.py превращает в ссылку на статью на языке страницы.

ACCESS = {
    "slug": "cloudflare-access-zero-trust-step-by-step",
    "date": "2026-11-15",
    "tags": ["Cloudflare", "Zero Trust", "Access", "SSO", "Odoo"],
    "code": {
        "check": ("bash", """curl -sI https://2027.pp.ua/test2/ | grep -iE "^HTTP|^location"
# HTTP/2 302
# location: https://<team>.cloudflareaccess.com/cdn-cgi/access/login/2027.pp.ua?...

# the same page through every other hostname - must ALSO redirect
for h in goldberg.pp.ua www.goldberg.pp.ua goldberg-odoo.pages.dev; do
  printf "%-28s " $h; curl -s -o /dev/null -w "%{http_code}\\n" https://$h/test2/
done"""),
        "service_token": ("bash · machine access with a service token", """curl -H "CF-Access-Client-Id: <id>.access" \\
     -H "CF-Access-Client-Secret: <secret>" \\
     https://stage.example.com/web/webclient/version_info"""),
        "logout": ("URL", """https://2027.pp.ua/cdn-cgi/access/logout"""),
    },
    "links": [
        ("Demo: /test2/ – Cloudflare Access (e-mail code)", "https://2027.pp.ua/test2/"),
        ("Demo: /test/ – Basic Auth via Cloudflare Pages Functions (admin / @1hotkey)", "https://2027.pp.ua/test/"),
        ("Blog: nginx/Apache Basic Auth and what to close in Odoo", "@blog:nginx-apache-password-protect-odoo-database-manager"),
        ("Cloudflare Zero Trust – Access documentation", "https://developers.cloudflare.com/cloudflare-one/policies/access/"),
        ("Cloudflare Pages Functions – middleware", "https://developers.cloudflare.com/pages/functions/middleware/"),
    ],
    "t": {},
}

ACCESS["t"]["de"] = {
    "title": "Cloudflare Access (Zero Trust) Schritt für Schritt – und wann es besser ist als ein Passwort",
    "summary": "Anmeldung per E-Mail-Code oder SSO vor jeder Website oder jedem Testsystem – ohne eine Zeile Code. Einrichtung in fünf Schritten, Vergleich mit Basic Auth über Pages Functions, Stolperfallen und Odoo-Praxis.",
    "body": [
        ("p", "Auf dieser Website gibt es zwei Demo-Seiten mit gleichem Inhalt und unterschiedlichem Schutz: `/test/` mit **Basic Auth über Cloudflare Pages Functions** (ein gemeinsames Passwort, geprüft von einer kleinen Funktion) und `/test2/` mit **Cloudflare Access** (persönliche Anmeldung per E-Mail-Code). Dieser Artikel erklärt Access und wann man welches nimmt."),
        ("h", "Was ist Cloudflare Access?"),
        ("p", "Access ist Teil von Cloudflare Zero Trust. Es steht vor einer Website oder Anwendung und lässt nur durch, wer sich angemeldet hat **und** von einer Richtlinie erlaubt ist. Anmelden kann man sich per Einmal-Code an die E-Mail-Adresse, über Google, Microsoft, GitHub oder ein Firmen-SSO. Der Free-Tarif erlaubt bis zu 50 Benutzer."),
        ("h", "Access oder Basic Auth?"),
        ("table", [
            ["", "Basic Auth (Pages Functions / nginx)", "Cloudflare Access"],
            ["Zugang", "ein gemeinsames Passwort", "persönlich pro E-Mail, Gruppe oder Domain"],
            ["Jemandem den Zugang entziehen", "Passwort für alle ändern", "eine Adresse aus der Richtlinie löschen"],
            ["Anmeldung", "Browserfenster, Passwort", "E-Mail-Code, Google, Microsoft, GitHub, SSO"],
            ["Protokoll", "nein", "ja, wer sich wann angemeldet hat"],
            ["Code auf der Website", "Funktion + Secret (`/test/`) bzw. nginx-Konfiguration", "keiner – alles im Dashboard"],
            ["Maschinen (API, Webhooks)", "einfach: Benutzer/Passwort im Header", "Service-Token nötig"],
            ["Voraussetzung", "keine", "Domain bzw. Pages-Projekt im Cloudflare-Konto"],
        ]),
        ("p", "Faustregel: **ein Passwort für eine Handvoll Leute** – Basic Auth. **Personen, Rollen, Protokoll, SSO** – Access."),
        ("h", "Einrichtung in fünf Schritten"),
        ("ol", [
            "**Zero Trust aktivieren.** dash.cloudflare.com → Zero Trust → Teamnamen wählen (daraus wird `<team>.cloudflareaccess.com`) → Tarif Free. Cloudflare kann eine Zahlungsmethode verlangen, der Free-Tarif kostet nichts.",
            "**Anmeldemethode.** Zero Trust → Settings → Authentication → Login methods → „One-time PIN“ hinzufügen. Optional Google, Microsoft oder GitHub.",
            "**Anwendung anlegen.** Access → Applications → Add → Self-hosted. Domain und Pfad eintragen, z. B. `2027.pp.ua` + `test2`. Sitzungsdauer wählen (hier 24 h).",
            "**Richtlinie.** Action „Allow“, Include → „Emails“ (einzelne Adressen) oder „Emails ending in“ (z. B. `@firma.de`). Ohne passende Richtlinie kommt niemand hinein.",
            "**Alle Adressen schützen.** Dieselbe Seite ist oft über mehrere Namen erreichbar: eigene Domain, Spiegel-Domains, `projekt.pages.dev`. Jede davon als weiteres Ziel (Destination) in die Anwendung eintragen.",
        ]),
        ("note", "Genau Schritt 5 wird oft vergessen: Bei der Demo `/test2/` war die Seite zunächst nur auf 2027.pp.ua geschützt – über goldberg.pp.ua und goldberg-odoo.pages.dev wäre sie offen gewesen. Darum immer alle Hostnamen prüfen."),
        ("h", "Prüfen"),
        ("code", "check"),
        ("p", "Abmelden geht über eine feste Adresse:"),
        ("code", "logout"),
        ("h", "Access vor Odoo"),
        ("ul", [
            "**Stage- und Testsysteme** komplett hinter Access legen – Kunden und Tester melden sich mit ihrer E-Mail an, ohne zusätzliche Odoo-Konten zu verraten.",
            "**Datenbank-Manager** (`/web/database/*`) für die Produktion: eigene Access-Anwendung nur für diesen Pfad, Zugang nur für Administratoren.",
            "**API, Webhooks, mobile App** können keine interaktive Anmeldung: für diese Pfade eine „Bypass“-Richtlinie oder einen Service-Token verwenden.",
            "**Wichtig:** Access schützt nur den Weg über Cloudflare. Ist der Odoo-Server direkt per IP erreichbar, ist der Schutz umgangen – Firewall nur für Cloudflare-IPs öffnen oder Cloudflare Tunnel nutzen und den Header `Cf-Access-Jwt-Assertion` prüfen.",
        ]),
        ("code", "service_token"),
        ("links", "Demos und Dokumentation"),
    ],
}

ACCESS["t"]["en"] = {
    "title": "Cloudflare Access (Zero Trust) step by step – and when it beats a password",
    "summary": "Login with an e-mail code or SSO in front of any website or test system – without a line of code. Setup in five steps, comparison with Basic Auth via Pages Functions, pitfalls and Odoo practice.",
    "body": [
        ("p", "This website has two demo pages with the same content and different protection: `/test/` with **Basic Auth via Cloudflare Pages Functions** (one shared password, checked by a small function) and `/test2/` with **Cloudflare Access** (personal login with an e-mail code). This article explains Access and when to use which."),
        ("h", "What is Cloudflare Access?"),
        ("p", "Access is part of Cloudflare Zero Trust. It sits in front of a website or application and only lets through people who have signed in **and** are allowed by a policy. Sign-in works with a one-time code sent to the e-mail address, with Google, Microsoft, GitHub or company SSO. The free plan allows up to 50 users."),
        ("h", "Access or Basic Auth?"),
        ("table", [
            ["", "Basic Auth (Pages Functions / nginx)", "Cloudflare Access"],
            ["Access", "one shared password", "personal, per e-mail, group or domain"],
            ["Revoking someone", "change the password for everyone", "remove one address from the policy"],
            ["Login", "browser box, password", "e-mail code, Google, Microsoft, GitHub, SSO"],
            ["Audit log", "no", "yes, who signed in when"],
            ["Code on the website", "function + secret (`/test/`) or nginx config", "none – everything in the dashboard"],
            ["Machines (API, webhooks)", "easy: user/password in a header", "service token needed"],
            ["Requirement", "none", "domain or Pages project in the Cloudflare account"],
        ]),
        ("p", "Rule of thumb: **one password for a handful of people** – Basic Auth. **People, roles, audit log, SSO** – Access."),
        ("h", "Setup in five steps"),
        ("ol", [
            "**Enable Zero Trust.** dash.cloudflare.com → Zero Trust → choose a team name (it becomes `<team>.cloudflareaccess.com`) → Free plan. Cloudflare may ask for a payment method; the free plan costs nothing.",
            "**Login method.** Zero Trust → Settings → Authentication → Login methods → add \"One-time PIN\". Optionally Google, Microsoft or GitHub.",
            "**Create the application.** Access → Applications → Add → Self-hosted. Enter domain and path, e.g. `2027.pp.ua` + `test2`. Choose a session duration (24 h here).",
            "**Policy.** Action \"Allow\", Include → \"Emails\" (single addresses) or \"Emails ending in\" (e.g. `@company.com`). Without a matching policy nobody gets in.",
            "**Protect every hostname.** The same page is often reachable under several names: your own domain, mirror domains, `project.pages.dev`. Add each of them as another destination of the application.",
        ]),
        ("note", "Step 5 is the one people forget: for the `/test2/` demo the page was first protected only on 2027.pp.ua – through goldberg.pp.ua and goldberg-odoo.pages.dev it would have been open. So always check every hostname."),
        ("h", "Check"),
        ("code", "check"),
        ("p", "Signing out uses a fixed address:"),
        ("code", "logout"),
        ("h", "Access in front of Odoo"),
        ("ul", [
            "Put **stage and test systems** completely behind Access – clients and testers sign in with their e-mail, without exposing extra Odoo accounts.",
            "**Database manager** (`/web/database/*`) in production: a separate Access application for just that path, admins only.",
            "**API, webhooks, the mobile app** cannot do an interactive login: use a \"Bypass\" policy or a service token for those paths.",
            "**Important:** Access only protects the way through Cloudflare. If the Odoo server is reachable directly by IP, the protection is bypassed – open the firewall to Cloudflare IPs only, or use Cloudflare Tunnel, and verify the `Cf-Access-Jwt-Assertion` header.",
        ]),
        ("code", "service_token"),
        ("links", "Demos and documentation"),
    ],
}

ACCESS["t"]["fr"] = {
    "title": "Cloudflare Access (Zero Trust) pas à pas – et quand c’est mieux qu’un mot de passe",
    "summary": "Connexion par code e-mail ou SSO devant n’importe quel site ou système de test – sans une ligne de code. Mise en place en cinq étapes, comparaison avec Basic Auth via Pages Functions, pièges et pratique avec Odoo.",
    "body": [
        ("p", "Ce site comporte deux pages de démonstration au contenu identique et à la protection différente : `/test/` avec **Basic Auth via Cloudflare Pages Functions** (un mot de passe partagé, vérifié par une petite fonction) et `/test2/` avec **Cloudflare Access** (connexion personnelle par code e-mail). Cet article explique Access et quand choisir l’un ou l’autre."),
        ("h", "Qu’est-ce que Cloudflare Access ?"),
        ("p", "Access fait partie de Cloudflare Zero Trust. Il se place devant un site ou une application et ne laisse passer que les personnes connectées **et** autorisées par une règle. La connexion se fait par code à usage unique envoyé par e-mail, via Google, Microsoft, GitHub ou un SSO d’entreprise. L’offre gratuite permet jusqu’à 50 utilisateurs."),
        ("h", "Access ou Basic Auth ?"),
        ("table", [
            ["", "Basic Auth (Pages Functions / nginx)", "Cloudflare Access"],
            ["Accès", "un mot de passe partagé", "personnel, par e-mail, groupe ou domaine"],
            ["Retirer l’accès à quelqu’un", "changer le mot de passe pour tous", "supprimer une adresse de la règle"],
            ["Connexion", "fenêtre du navigateur, mot de passe", "code e-mail, Google, Microsoft, GitHub, SSO"],
            ["Journal", "non", "oui, qui s’est connecté et quand"],
            ["Code sur le site", "fonction + secret (`/test/`) ou configuration nginx", "aucun – tout dans le tableau de bord"],
            ["Machines (API, webhooks)", "simple : identifiant/mot de passe dans un en-tête", "service token nécessaire"],
            ["Prérequis", "aucun", "domaine ou projet Pages dans le compte Cloudflare"],
        ]),
        ("p", "Règle simple : **un mot de passe pour quelques personnes** – Basic Auth. **Personnes, rôles, journal, SSO** – Access."),
        ("h", "Mise en place en cinq étapes"),
        ("ol", [
            "**Activer Zero Trust.** dash.cloudflare.com → Zero Trust → choisir un nom d’équipe (il devient `<team>.cloudflareaccess.com`) → offre Free. Cloudflare peut demander un moyen de paiement ; l’offre gratuite ne coûte rien.",
            "**Méthode de connexion.** Zero Trust → Settings → Authentication → Login methods → ajouter « One-time PIN ». En option Google, Microsoft ou GitHub.",
            "**Créer l’application.** Access → Applications → Add → Self-hosted. Saisir domaine et chemin, p. ex. `2027.pp.ua` + `test2`. Choisir la durée de session (ici 24 h).",
            "**Règle.** Action « Allow », Include → « Emails » (adresses individuelles) ou « Emails ending in » (p. ex. `@entreprise.fr`). Sans règle correspondante, personne n’entre.",
            "**Protéger tous les noms d’hôte.** La même page est souvent accessible sous plusieurs noms : votre domaine, des domaines miroirs, `projet.pages.dev`. Ajoutez chacun comme destination supplémentaire de l’application.",
        ]),
        ("note", "C’est l’étape 5 qu’on oublie : pour la démo `/test2/`, la page n’était d’abord protégée que sur 2027.pp.ua – via goldberg.pp.ua et goldberg-odoo.pages.dev, elle aurait été ouverte. Vérifiez donc toujours tous les noms d’hôte."),
        ("h", "Vérifier"),
        ("code", "check"),
        ("p", "La déconnexion passe par une adresse fixe :"),
        ("code", "logout"),
        ("h", "Access devant Odoo"),
        ("ul", [
            "Placer entièrement **les systèmes de préproduction et de test** derrière Access – clients et testeurs se connectent avec leur e-mail, sans exposer de comptes Odoo supplémentaires.",
            "**Gestionnaire de bases** (`/web/database/*`) en production : une application Access dédiée à ce seul chemin, réservée aux administrateurs.",
            "**API, webhooks, application mobile** ne peuvent pas se connecter de façon interactive : utiliser une règle « Bypass » ou un service token pour ces chemins.",
            "**Important :** Access ne protège que le passage par Cloudflare. Si le serveur Odoo est joignable directement par son IP, la protection est contournée – n’ouvrir le pare-feu qu’aux IP de Cloudflare ou utiliser Cloudflare Tunnel, et vérifier l’en-tête `Cf-Access-Jwt-Assertion`.",
        ]),
        ("code", "service_token"),
        ("links", "Démos et documentation"),
    ],
}

ACCESS["t"]["el"] = {
    "title": "Cloudflare Access (Zero Trust) βήμα-βήμα – και πότε είναι καλύτερο από έναν κωδικό",
    "summary": "Σύνδεση με κωδικό e-mail ή SSO μπροστά από οποιοδήποτε site ή δοκιμαστικό σύστημα – χωρίς ούτε μία γραμμή κώδικα. Ρύθμιση σε πέντε βήματα, σύγκριση με Basic Auth μέσω Pages Functions, παγίδες και πρακτική με Odoo.",
    "body": [
        ("p", "Σε αυτό το site υπάρχουν δύο σελίδες επίδειξης με ίδιο περιεχόμενο και διαφορετική προστασία: η `/test/` με **Basic Auth μέσω Cloudflare Pages Functions** (ένας κοινός κωδικός, ελέγχεται από μια μικρή συνάρτηση) και η `/test2/` με **Cloudflare Access** (προσωπική σύνδεση με κωδικό e-mail). Το άρθρο εξηγεί το Access και πότε να διαλέξετε το καθένα."),
        ("h", "Τι είναι το Cloudflare Access;"),
        ("p", "Το Access είναι μέρος του Cloudflare Zero Trust. Μπαίνει μπροστά από ένα site ή μια εφαρμογή και αφήνει να περάσουν μόνο όσοι έχουν συνδεθεί **και** επιτρέπονται από μια πολιτική. Η σύνδεση γίνεται με κωδικό μίας χρήσης στο e-mail, μέσω Google, Microsoft, GitHub ή εταιρικού SSO. Το δωρεάν πακέτο επιτρέπει έως 50 χρήστες."),
        ("h", "Access ή Basic Auth;"),
        ("table", [
            ["", "Basic Auth (Pages Functions / nginx)", "Cloudflare Access"],
            ["Πρόσβαση", "ένας κοινός κωδικός", "προσωπική, ανά e-mail, ομάδα ή domain"],
            ["Ανάκληση πρόσβασης", "αλλαγή κωδικού για όλους", "διαγραφή μίας διεύθυνσης από την πολιτική"],
            ["Σύνδεση", "παράθυρο browser, κωδικός", "κωδικός e-mail, Google, Microsoft, GitHub, SSO"],
            ["Καταγραφή", "όχι", "ναι, ποιος συνδέθηκε και πότε"],
            ["Κώδικας στο site", "συνάρτηση + secret (`/test/`) ή ρύθμιση nginx", "κανένας – όλα στο dashboard"],
            ["Μηχανές (API, webhooks)", "απλό: χρήστης/κωδικός σε header", "χρειάζεται service token"],
            ["Προϋπόθεση", "καμία", "domain ή έργο Pages στον λογαριασμό Cloudflare"],
        ]),
        ("p", "Απλός κανόνας: **ένας κωδικός για λίγα άτομα** – Basic Auth. **Άτομα, ρόλοι, καταγραφή, SSO** – Access."),
        ("h", "Ρύθμιση σε πέντε βήματα"),
        ("ol", [
            "**Ενεργοποίηση Zero Trust.** dash.cloudflare.com → Zero Trust → επιλογή ονόματος ομάδας (γίνεται `<team>.cloudflareaccess.com`) → πακέτο Free. Το Cloudflare μπορεί να ζητήσει τρόπο πληρωμής· το δωρεάν πακέτο δεν χρεώνεται.",
            "**Μέθοδος σύνδεσης.** Zero Trust → Settings → Authentication → Login methods → προσθήκη «One-time PIN». Προαιρετικά Google, Microsoft ή GitHub.",
            "**Δημιουργία εφαρμογής.** Access → Applications → Add → Self-hosted. Domain και διαδρομή, π.χ. `2027.pp.ua` + `test2`. Επιλογή διάρκειας συνεδρίας (εδώ 24 ώρες).",
            "**Πολιτική.** Action «Allow», Include → «Emails» (μεμονωμένες διευθύνσεις) ή «Emails ending in» (π.χ. `@etaireia.gr`). Χωρίς ταιριαστή πολιτική δεν μπαίνει κανείς.",
            "**Προστασία όλων των ονομάτων.** Η ίδια σελίδα είναι συχνά προσβάσιμη από πολλά ονόματα: δικό σας domain, mirror domains, `project.pages.dev`. Προσθέστε το καθένα ως επιπλέον προορισμό (destination) της εφαρμογής.",
        ]),
        ("note", "Το βήμα 5 είναι αυτό που ξεχνιέται: στην επίδειξη `/test2/` η σελίδα αρχικά προστατευόταν μόνο στο 2027.pp.ua – μέσω goldberg.pp.ua και goldberg-odoo.pages.dev θα ήταν ανοιχτή. Γι' αυτό ελέγχετε πάντα όλα τα ονόματα."),
        ("h", "Έλεγχος"),
        ("code", "check"),
        ("p", "Η αποσύνδεση γίνεται από σταθερή διεύθυνση:"),
        ("code", "logout"),
        ("h", "Access μπροστά από το Odoo"),
        ("ul", [
            "**Συστήματα stage και δοκιμών** ολόκληρα πίσω από το Access – πελάτες και testers συνδέονται με το e-mail τους, χωρίς να εκτίθενται επιπλέον λογαριασμοί Odoo.",
            "**Διαχείριση βάσεων** (`/web/database/*`) στην παραγωγή: ξεχωριστή εφαρμογή Access μόνο για αυτή τη διαδρομή, μόνο για διαχειριστές.",
            "**API, webhooks, mobile app** δεν μπορούν να κάνουν διαδραστική σύνδεση: για αυτές τις διαδρομές πολιτική «Bypass» ή service token.",
            "**Σημαντικό:** το Access προστατεύει μόνο τη διαδρομή μέσω Cloudflare. Αν ο server του Odoo είναι προσβάσιμος απευθείας μέσω IP, η προστασία παρακάμπτεται – ανοίξτε το firewall μόνο για IP του Cloudflare ή χρησιμοποιήστε Cloudflare Tunnel, και ελέγχετε την κεφαλίδα `Cf-Access-Jwt-Assertion`.",
        ]),
        ("code", "service_token"),
        ("links", "Επιδείξεις και τεκμηρίωση"),
    ],
}

ACCESS["t"]["uk"] = {
    "title": "Cloudflare Access (Zero Trust) покроково – і коли це краще за пароль",
    "summary": "Вхід за кодом з e-mail або через SSO перед будь-яким сайтом чи тестовою системою – без жодного рядка коду. Налаштування в п'ять кроків, порівняння з Basic Auth через Pages Functions, пастки та практика з Odoo.",
    "body": [
        ("p", "На цьому сайті є дві демо-сторінки з однаковим вмістом і різним захистом: `/test/` із **Basic Auth через Cloudflare Pages Functions** (один спільний пароль, який перевіряє невелика функція) і `/test2/` із **Cloudflare Access** (особистий вхід за кодом з e-mail). Ця стаття пояснює Access і коли що обирати."),
        ("h", "Що таке Cloudflare Access?"),
        ("p", "Access – частина Cloudflare Zero Trust. Він стоїть перед сайтом чи застосунком і пропускає лише тих, хто увійшов **і** кому це дозволяє політика. Увійти можна за одноразовим кодом на e-mail, через Google, Microsoft, GitHub або корпоративний SSO. Безкоштовний тариф – до 50 користувачів."),
        ("h", "Access чи Basic Auth?"),
        ("table", [
            ["", "Basic Auth (Pages Functions / nginx)", "Cloudflare Access"],
            ["Доступ", "один спільний пароль", "особистий: за e-mail, групою або доменом"],
            ["Забрати доступ у когось", "змінити пароль для всіх", "видалити одну адресу з політики"],
            ["Вхід", "вікно браузера, пароль", "код на e-mail, Google, Microsoft, GitHub, SSO"],
            ["Журнал", "немає", "є: хто й коли входив"],
            ["Код на сайті", "функція + секрет (`/test/`) або конфіг nginx", "жодного – усе в панелі"],
            ["Машини (API, вебхуки)", "просто: логін/пароль у заголовку", "потрібен service token"],
            ["Умова", "немає", "домен або Pages-проєкт в акаунті Cloudflare"],
        ]),
        ("p", "Просте правило: **один пароль на кількох людей** – Basic Auth. **Люди, ролі, журнал, SSO** – Access."),
        ("h", "Налаштування в п'ять кроків"),
        ("ol", [
            "**Увімкнути Zero Trust.** dash.cloudflare.com → Zero Trust → вибрати назву команди (з неї буде `<team>.cloudflareaccess.com`) → тариф Free. Cloudflare може попросити картку, але Free нічого не коштує.",
            "**Спосіб входу.** Zero Trust → Settings → Authentication → Login methods → додати «One-time PIN». За бажанням – Google, Microsoft або GitHub.",
            "**Створити застосунок.** Access → Applications → Add → Self-hosted. Вказати домен і шлях, наприклад `2027.pp.ua` + `test2`. Вибрати тривалість сесії (тут 24 год).",
            "**Політика.** Action «Allow», Include → «Emails» (окремі адреси) або «Emails ending in» (наприклад `@firma.ua`). Без відповідної політики ніхто не ввійде.",
            "**Захистити всі адреси.** Та сама сторінка часто доступна під кількома іменами: власний домен, дзеркала, `project.pages.dev`. Кожне додайте як ще одне призначення (destination) застосунку.",
        ]),
        ("note", "Саме крок 5 найчастіше забувають: у демо `/test2/` сторінку спершу захистили лише на 2027.pp.ua, а через goldberg.pp.ua і goldberg-odoo.pages.dev вона була б відкрита. Тому завжди перевіряйте всі імена хостів."),
        ("h", "Перевірка"),
        ("code", "check"),
        ("p", "Вихід – за фіксованою адресою:"),
        ("code", "logout"),
        ("h", "Access перед Odoo"),
        ("ul", [
            "**Stage і тестові системи** повністю за Access: клієнти й тестувальники входять зі своїм e-mail, без зайвих облікових записів Odoo назовні.",
            "**Менеджер баз** (`/web/database/*`) на проді: окремий застосунок Access лише для цього шляху, доступ лише адміністраторам.",
            "**API, вебхуки, мобільний застосунок** не можуть пройти інтерактивний вхід: для цих шляхів – політика «Bypass» або service token.",
            "**Важливо:** Access захищає лише шлях через Cloudflare. Якщо сервер Odoo доступний напряму за IP, захист обходиться. Відкрийте фаєрвол лише для IP Cloudflare або використайте Cloudflare Tunnel і перевіряйте заголовок `Cf-Access-Jwt-Assertion`.",
        ]),
        ("code", "service_token"),
        ("links", "Демо та документація"),
    ],
}

ACCESS["t"]["ru"] = {
    "title": "Cloudflare Access (Zero Trust) по шагам – и когда это лучше пароля",
    "summary": "Вход по коду из e-mail или через SSO перед любым сайтом или тестовой системой – без единой строки кода. Настройка в пять шагов, сравнение с Basic Auth через Pages Functions, ловушки и практика с Odoo.",
    "body": [
        ("p", "На этом сайте есть две демо-страницы с одинаковым содержимым и разной защитой: `/test/` с **Basic Auth через Cloudflare Pages Functions** (один общий пароль, его проверяет небольшая функция) и `/test2/` с **Cloudflare Access** (личный вход по коду из e-mail). Эта статья объясняет Access и когда что выбирать."),
        ("h", "Что такое Cloudflare Access?"),
        ("p", "Access – часть Cloudflare Zero Trust. Он стоит перед сайтом или приложением и пропускает только тех, кто вошёл **и** кому это разрешает политика. Войти можно по одноразовому коду на e-mail, через Google, Microsoft, GitHub или корпоративный SSO. Бесплатный тариф – до 50 пользователей."),
        ("h", "Access или Basic Auth?"),
        ("table", [
            ["", "Basic Auth (Pages Functions / nginx)", "Cloudflare Access"],
            ["Доступ", "один общий пароль", "личный: по e-mail, группе или домену"],
            ["Забрать доступ у кого-то", "сменить пароль для всех", "удалить один адрес из политики"],
            ["Вход", "окно браузера, пароль", "код на e-mail, Google, Microsoft, GitHub, SSO"],
            ["Журнал", "нет", "есть: кто и когда входил"],
            ["Код на сайте", "функция + секрет (`/test/`) или конфиг nginx", "никакого – всё в панели"],
            ["Машины (API, вебхуки)", "просто: логин/пароль в заголовке", "нужен service token"],
            ["Условие", "нет", "домен или Pages-проект в аккаунте Cloudflare"],
        ]),
        ("p", "Простое правило: **один пароль на несколько человек** – Basic Auth. **Люди, роли, журнал, SSO** – Access."),
        ("h", "Настройка в пять шагов"),
        ("ol", [
            "**Включить Zero Trust.** dash.cloudflare.com → Zero Trust → выбрать имя команды (из него будет `<team>.cloudflareaccess.com`) → тариф Free. Cloudflare может попросить карту, но Free ничего не стоит.",
            "**Способ входа.** Zero Trust → Settings → Authentication → Login methods → добавить «One-time PIN». По желанию – Google, Microsoft или GitHub.",
            "**Создать приложение.** Access → Applications → Add → Self-hosted. Указать домен и путь, например `2027.pp.ua` + `test2`. Выбрать длительность сессии (здесь 24 ч).",
            "**Политика.** Action «Allow», Include → «Emails» (отдельные адреса) или «Emails ending in» (например `@firma.ru`). Без подходящей политики никто не войдёт.",
            "**Защитить все адреса.** Одна и та же страница часто доступна под несколькими именами: свой домен, зеркала, `project.pages.dev`. Каждое добавьте как ещё одно назначение (destination) приложения.",
        ]),
        ("note", "Именно шаг 5 чаще всего забывают: в демо `/test2/` страницу сначала защитили только на 2027.pp.ua, а через goldberg.pp.ua и goldberg-odoo.pages.dev она была бы открыта. Поэтому всегда проверяйте все имена хостов."),
        ("h", "Проверка"),
        ("code", "check"),
        ("p", "Выход – по фиксированному адресу:"),
        ("code", "logout"),
        ("h", "Access перед Odoo"),
        ("ul", [
            "**Stage и тестовые системы** целиком за Access: клиенты и тестировщики входят со своим e-mail, без лишних учётных записей Odoo наружу.",
            "**Менеджер баз** (`/web/database/*`) на проде: отдельное приложение Access только для этого пути, доступ только администраторам.",
            "**API, вебхуки, мобильное приложение** не могут пройти интерактивный вход: для этих путей – политика «Bypass» или service token.",
            "**Важно:** Access защищает только путь через Cloudflare. Если сервер Odoo доступен напрямую по IP, защита обходится. Откройте файрвол только для IP Cloudflare или используйте Cloudflare Tunnel и проверяйте заголовок `Cf-Access-Jwt-Assertion`.",
        ]),
        ("code", "service_token"),
        ("links", "Демо и документация"),
    ],
}
