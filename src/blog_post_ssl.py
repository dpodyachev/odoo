# Статья 7: проверка срока SSL/TLS-сертификата, инструменты Linux/Windows, история, eMudhra (октябрь–ноябрь 2026).
# Источники по eMudhra — в блоке ("links", ...).

SSL = {
    "slug": "ssl-certificate-expiry-check-tools",
    "date": "2026-11-15",
    "tags": ["TLS", "SSL", "openssl", "PowerShell", "eMudhra"],
    "code": {
        "linux_dns": ("bash · Linux – where am I, where does the name point", """hostname -f                       # full name of THIS server
hostname -I                       # its IP addresses
dig +short A    2027.pp.ua        # where the domain points (IPv4)
dig +short AAAA 2027.pp.ua        # IPv6 - often forgotten, often the culprit
dig +short CAA  goldberg.pp.ua    # which CAs may issue for the domain
nslookup goldberg.pp.ua           # the same, available almost everywhere"""),
        "linux_openssl": ("bash · Linux – openssl", """H=2027.pp.ua

# validity, subject, issuer of the certificate actually served
openssl s_client -connect $H:443 -servername $H </dev/null 2>/dev/null \\
  | openssl x509 -noout -dates -subject -issuer

# is the chain valid? 0 (ok) is the only good answer
openssl s_client -connect $H:443 -servername $H </dev/null 2>&1 | grep "Verify return code"

# does it expire within 14 days? (exit code 1 = yes)
openssl s_client -connect $H:443 -servername $H </dev/null 2>/dev/null \\
  | openssl x509 -noout -checkend $((14*86400)) && echo "ok for 14+ days"

# the whole chain, one certificate after another
openssl s_client -connect $H:443 -servername $H -showcerts </dev/null 2>/dev/null \\
  | grep -E "^ *[0-9] s:|^ *i:"

# mail server with STARTTLS
openssl s_client -connect mail.example.com:587 -starttls smtp </dev/null 2>/dev/null \\
  | openssl x509 -noout -enddate"""),
        "linux_more": ("bash · Linux – curl, nmap, local file", """curl -svI https://2027.pp.ua 2>&1 | grep -E "expire date|subject:|issuer:|SSL certificate verify"
nmap -p 443 --script ssl-cert goldberg.pp.ua
openssl x509 -in /etc/letsencrypt/live/odoo.example.com/cert.pem -noout -enddate   # file on disk"""),
        "badssl": ("bash · practise on broken certificates", """for h in expired self-signed untrusted-root wrong.host incomplete-chain; do
  printf "%-20s " $h
  openssl s_client -connect $h.badssl.com:443 -servername $h.badssl.com -verify_hostname $h.badssl.com \\
    </dev/null 2>&1 | grep "Verify return code"
done"""),
        "windows": ("PowerShell · Windows", """Resolve-DnsName 2027.pp.ua                            # DNS (like dig)
nslookup goldberg.pp.ua
Test-NetConnection 2027.pp.ua -Port 443               # is 443 reachable at all?

# read the certificate - even an invalid one (the callback accepts everything)
$h   = "2027.pp.ua"
$tcp = [Net.Sockets.TcpClient]::new($h, 443)
$ssl = [Net.Security.SslStream]::new($tcp.GetStream(), $false, { $true })
$ssl.AuthenticateAsClient($h)
$c = [Security.Cryptography.X509Certificates.X509Certificate2]$ssl.RemoteCertificate
"{0}`nIssuer:  {1}`nValid to: {2}  ({3} days)" -f $c.Subject, $c.Issuer, $c.NotAfter, ($c.NotAfter - (Get-Date)).Days
$ssl.Dispose(); $tcp.Dispose()

# is the chain trusted by Windows itself?
$chain = [Security.Cryptography.X509Certificates.X509Chain]::new()
$chain.Build($c); $chain.ChainStatus | Select-Object Status, StatusInformation"""),
        "emudhra": ("bash · does my certificate chain to eMudhra?", """H=goldberg.pp.ua
openssl s_client -connect $H:443 -servername $H -showcerts </dev/null 2>/dev/null \\
  | grep -iE "emSign|eMudhra" && echo "eMudhra in the chain -> replace" || echo "no eMudhra"
dig +short CAA goldberg.pp.ua   # only "emsign.com" here? -> add the new CA first"""),
    },
    "links": [
        ("SSL Labs Server Test", "https://www.ssllabs.com/ssltest/"),
        ("crt.sh – Certificate Transparency", "https://crt.sh/"),
        ("badssl.com – test hosts", "https://badssl.com/"),
        ("certkit: eMudhra / InCommon distrust (timeline)", "https://www.certkit.io/blog/emudhra-internet2-incommon-distrust"),
        ("The Hacker News: Eight eMudhra CA keys compromised", "https://thehackernews.com/2026/10/eight-emudhra-ca-keys-compromised.html"),
        ("Qualys: identifying compromised eMudhra certificates", "https://blog.qualys.com/product-tech/2026/10/23/how-to-identify-compromised-emudhra-certificates-with-qualys-cve-2026-111943-and-cve-2026-111944"),
    ],
    "t": {},
}

VERIFY_ROWS = {  # общая часть таблицы кодов: (код, текст по языкам)
    "0": {"de": "alles in Ordnung", "en": "all good", "fr": "tout est en ordre", "el": "όλα εντάξει", "uk": "усе гаразд", "ru": "всё в порядке"},
    "10": {"de": "Zertifikat abgelaufen", "en": "certificate has expired", "fr": "certificat expiré", "el": "το πιστοποιητικό έχει λήξει", "uk": "сертифікат прострочено", "ru": "сертификат просрочен"},
    "18": {"de": "selbstsigniert", "en": "self-signed", "fr": "auto-signé", "el": "αυτο-υπογεγραμμένο", "uk": "самопідписаний", "ru": "самоподписанный"},
    "19": {"de": "selbstsigniertes Zertifikat in der Kette (unbekannte Root)", "en": "self-signed certificate in the chain (unknown root)", "fr": "certificat auto-signé dans la chaîne (racine inconnue)", "el": "αυτο-υπογεγραμμένο στην αλυσίδα (άγνωστη ρίζα)", "uk": "самопідписаний у ланцюжку (невідомий root)", "ru": "самоподписанный в цепочке (неизвестный root)"},
    "20": {"de": "Aussteller nicht gefunden – Zwischenzertifikat fehlt oder Root nicht vertraut", "en": "issuer not found – intermediate missing or root not trusted", "fr": "émetteur introuvable – intermédiaire manquant ou racine non approuvée", "el": "δεν βρέθηκε εκδότης – λείπει ενδιάμεσο ή η ρίζα δεν είναι έμπιστη", "uk": "не знайдено видавця – бракує проміжного або root не довірений", "ru": "не найден издатель – нет промежуточного или root не доверенный"},
    "21": {"de": "unvollständige Kette (Server liefert das Zwischenzertifikat nicht mit)", "en": "incomplete chain (server does not send the intermediate)", "fr": "chaîne incomplète (le serveur n’envoie pas l’intermédiaire)", "el": "ελλιπής αλυσίδα (ο server δεν στέλνει το ενδιάμεσο)", "uk": "неповний ланцюжок (сервер не віддає проміжний сертифікат)", "ru": "неполная цепочка (сервер не отдаёт промежуточный сертификат)"},
    "62": {"de": "Name passt nicht (mit -verify_hostname)", "en": "hostname mismatch (with -verify_hostname)", "fr": "nom d’hôte non concordant (avec -verify_hostname)", "el": "το όνομα δεν ταιριάζει (με -verify_hostname)", "uk": "ім’я не збігається (з -verify_hostname)", "ru": "имя не совпадает (с -verify_hostname)"},
}


def _codes(lang, head):
    return [head] + [[f"`{k}`", v[lang]] for k, v in VERIFY_ROWS.items()]


SSL["t"]["de"] = {
    "title": "Wann läuft das SSL-Zertifikat ab? Werkzeuge für Linux und Windows – und was eMudhra damit zu tun hat",
    "summary": "TLS in einer Minute, Online-Prüfungen, openssl/dig/curl unter Linux, PowerShell unter Windows, die Bedeutung der Verify-Codes, Lehren aus der Geschichte und der aktuelle Fall eMudhra.",
    "body": [
        ("h", "TLS in einer Minute"),
        ("p", "TLS (früher SSL) leistet zwei Dinge: Es **verschlüsselt** die Verbindung zwischen Browser und Server, und es **beweist**, dass der Server wirklich zu dieser Domain gehört. Den Beweis liefert das Zertifikat: Domain + öffentlicher Schlüssel + Unterschrift einer Zertifizierungsstelle (CA)."),
        ("p", "Geprüft wird eine **Kette**: Server-Zertifikat → Zwischenzertifikat (Intermediate) → Root-Zertifikat. Nur die Roots sind in Browsern und Betriebssystemen hinterlegt. Fehlt das Zwischenzertifikat oder entzieht ein Browser der Root das Vertrauen, ist auch ein „gültiges“ Zertifikat plötzlich wertlos. Und jedes Zertifikat hat ein festes Ablaufdatum (`notAfter`)."),
        ("h", "Online prüfen"),
        ("ul", [
            "**SSL Labs Server Test** – Kette, Ablauf, Protokolle, Bewertung A–F. Gründlich, dauert 1–2 Minuten.",
            "**crt.sh** – alle jemals für Ihre Domain ausgestellten Zertifikate aus den Certificate-Transparency-Logs. Ideal, um vergessene Subdomains und fremde Aussteller zu finden.",
            "**badssl.com** – Testseiten mit absichtlich kaputten Zertifikaten zum Üben.",
        ]),
        ("h", "Linux: Name und DNS zuerst"),
        ("p", "Die Hälfte aller „Zertifikatsprobleme“ sind DNS-Probleme: Die Domain zeigt auf den falschen Server oder ein vergessener IPv6-Eintrag führt woandershin."),
        ("code", "linux_dns"),
        ("h", "Linux: openssl s_client"),
        ("p", "Wichtig ist `-servername`: Damit wird SNI gesendet. Ohne SNI liefert ein Server mit mehreren Domains oft ein ganz anderes Zertifikat – und man prüft das falsche."),
        ("code", "linux_openssl"),
        ("table", _codes("de", ["Verify return code", "Bedeutung"])),
        ("code", "linux_more"),
        ("code", "badssl"),
        ("h", "Windows: PowerShell"),
        ("p", "Ohne zusätzliche Software: DNS, Port und Zertifikat direkt mit PowerShell. Wer Git für Windows installiert hat, hat in der Git Bash außerdem `openssl` und kann die Linux-Befehle oben verwenden."),
        ("code", "windows"),
        ("h", "Was mit Zertifikaten schon passiert ist"),
        ("ul", [
            "**2018 – Symantec:** Chrome und Firefox entzogen nach wiederholten Fehlern allen Symantec-Zertifikaten das Vertrauen. Millionen Websites mussten wechseln.",
            "**30.09.2021 – DST Root CA X3:** Die alte Let's-Encrypt-Root lief ab. Moderne Browser merkten nichts, aber alte Android-Geräte, OpenSSL 1.0.x und viele Skripte und Schnittstellen brachen ab.",
            "**2024 – Entrust:** Chrome und andere beendeten das Vertrauen für neue Entrust-Zertifikate.",
            "**Kürzere Laufzeiten:** Nach dem CA/Browser-Forum-Beschluss SC-081 sinkt die maximale Laufzeit schrittweise: 200 Tage ab März 2026, 100 Tage ab März 2027, 47 Tage ab März 2029. Let's Encrypt verschickt seit 2025 keine Ablauf-E-Mails mehr.",
        ]),
        ("h", "Aktuell: eMudhra (Oktober–November 2026)"),
        ("p", "Am 17. Oktober 2026 wurde bekannt, dass acht Zwischenzertifikate der indischen CA eMudhra mit zu schwachen, rekonstruierbaren Schlüsseln erzeugt worden waren (Schlüsselzeremonie im April 2025). Mozilla hat der Root **emSign ECC Root CA – G3** am 20. Oktober das Vertrauen entzogen, Chrome am 27. Oktober. Am 22. Oktober kündigte eMudhra den Ausstieg aus dem öffentlichen TLS-Geschäft an. Laut eMudhra und Fachberichten folgt die RSA-Root **emSign Root CA – G1**: Microsoft entfernt sie am 16. November, Apple am 30. November."),
        ("code", "emudhra"),
        ("ul", [
            "Kommt eMudhra/emSign in der Kette vor: Zertifikat bei einer anderen CA neu ausstellen – auch RSA-Zertifikate von eMudhra sind keine Dauerlösung mehr.",
            "CAA-Einträge prüfen: Erlaubt die Domain nur `emsign.com`, kann keine andere CA ausstellen.",
            "Nicht nur Webserver: auch Load-Balancer, VPN, Mailserver und Geräte mit manuell importierten Zertifikaten.",
        ]),
        ("h", "Allgemeine Tipps"),
        ("ul", [
            "Von außen prüfen, was **tatsächlich ausgeliefert** wird – nicht die Datei auf der Festplatte.",
            "Immer mit SNI (`-servername`) und immer die **ganze Kette** prüfen.",
            "Alarm bei 21, 14 und 7 Tagen – nicht erst am Ablauftag.",
            "Inventar aller Zertifikate führen: Domains, Subdomains, Mail, VPN, Geräte; crt.sh hilft beim Finden.",
            "Erneuerung automatisieren (siehe Artikel zu certbot) – bei 47-Tage-Zertifikaten geht es nicht mehr anders.",
        ]),
        ("links", "Quellen und Werkzeuge"),
    ],
}

SSL["t"]["en"] = {
    "title": "When does the SSL certificate expire? Tools for Linux and Windows – and what eMudhra has to do with it",
    "summary": "TLS in one minute, online checks, openssl/dig/curl on Linux, PowerShell on Windows, what the verify codes mean, lessons from history and the current eMudhra case.",
    "body": [
        ("h", "TLS in one minute"),
        ("p", "TLS (formerly SSL) does two things: it **encrypts** the connection between browser and server, and it **proves** that the server really belongs to that domain. The proof is the certificate: domain + public key + the signature of a certificate authority (CA)."),
        ("p", "What gets verified is a **chain**: server certificate → intermediate → root. Only the roots are stored in browsers and operating systems. If the intermediate is missing, or a browser stops trusting the root, even a \"valid\" certificate is suddenly worthless. And every certificate has a fixed expiry date (`notAfter`)."),
        ("h", "Checking online"),
        ("ul", [
            "**SSL Labs Server Test** – chain, expiry, protocols, grade A–F. Thorough, takes 1–2 minutes.",
            "**crt.sh** – every certificate ever issued for your domain, from the Certificate Transparency logs. Ideal for finding forgotten subdomains and unexpected issuers.",
            "**badssl.com** – test sites with deliberately broken certificates to practise on.",
        ]),
        ("h", "Linux: name and DNS first"),
        ("p", "Half of all \"certificate problems\" are DNS problems: the domain points to the wrong server, or a forgotten IPv6 record leads somewhere else."),
        ("code", "linux_dns"),
        ("h", "Linux: openssl s_client"),
        ("p", "`-servername` matters: it sends SNI. Without SNI, a server hosting several domains often returns a completely different certificate – and you check the wrong one."),
        ("code", "linux_openssl"),
        ("table", _codes("en", ["Verify return code", "Meaning"])),
        ("code", "linux_more"),
        ("code", "badssl"),
        ("h", "Windows: PowerShell"),
        ("p", "No extra software needed: DNS, port and certificate straight from PowerShell. If Git for Windows is installed, Git Bash also has `openssl`, so the Linux commands above work too."),
        ("code", "windows"),
        ("h", "What has already happened to certificates"),
        ("ul", [
            "**2018 – Symantec:** after repeated failures, Chrome and Firefox distrusted all Symantec certificates. Millions of sites had to switch.",
            "**30 Sep 2021 – DST Root CA X3:** the old Let's Encrypt root expired. Modern browsers didn't notice, but old Android devices, OpenSSL 1.0.x and many scripts and integrations broke.",
            "**2024 – Entrust:** Chrome and others stopped trusting new Entrust certificates.",
            "**Shorter lifetimes:** under CA/Browser Forum ballot SC-081 the maximum lifetime drops step by step: 200 days from March 2026, 100 days from March 2027, 47 days from March 2029. Let's Encrypt stopped sending expiry e-mails in 2025.",
        ]),
        ("h", "Right now: eMudhra (October–November 2026)"),
        ("p", "On 17 October 2026 it became known that eight intermediate certificates of the Indian CA eMudhra had been generated with weak, recoverable keys (key ceremony in April 2025). Mozilla distrusted the root **emSign ECC Root CA – G3** on 20 October, Chrome on 27 October. On 22 October eMudhra announced its exit from the public TLS business. According to eMudhra and industry reports, the RSA root **emSign Root CA – G1** follows: Microsoft removes it on 16 November, Apple on 30 November."),
        ("code", "emudhra"),
        ("ul", [
            "If eMudhra/emSign appears in the chain: reissue the certificate with another CA – RSA certificates from eMudhra are no long-term fix either.",
            "Check CAA records: if the domain only allows `emsign.com`, no other CA can issue.",
            "Not just web servers: load balancers, VPN, mail servers and appliances with manually imported certificates too.",
        ]),
        ("h", "General tips"),
        ("ul", [
            "Check from outside what is **actually served** – not the file on disk.",
            "Always use SNI (`-servername`) and always check the **whole chain**.",
            "Alert at 21, 14 and 7 days – not on the expiry day.",
            "Keep an inventory of all certificates: domains, subdomains, mail, VPN, appliances; crt.sh helps to find them.",
            "Automate renewal (see the certbot article) – with 47-day certificates there is no other way.",
        ]),
        ("links", "Sources and tools"),
    ],
}

SSL["t"]["uk"] = {
    "title": "Коли закінчується SSL-сертифікат? Інструменти для Linux і Windows – і до чого тут eMudhra",
    "summary": "TLS за хвилину, онлайн-перевірки, openssl/dig/curl у Linux, PowerShell у Windows, що означають коди Verify, уроки історії та актуальна ситуація з eMudhra.",
    "body": [
        ("h", "TLS за хвилину"),
        ("p", "TLS (раніше SSL) робить дві речі: **шифрує** з'єднання між браузером і сервером і **доводить**, що сервер справді належить цьому домену. Доказ – сертифікат: домен + відкритий ключ + підпис центру сертифікації (CA)."),
        ("p", "Перевіряється **ланцюжок**: сертифікат сервера → проміжний (intermediate) → кореневий (root). У браузерах і ОС зберігаються лише root-сертифікати. Якщо проміжного бракує або браузер перестав довіряти root, навіть «дійсний» сертифікат раптом нічого не вартий. І в кожного сертифіката є фіксована дата закінчення (`notAfter`)."),
        ("h", "Перевірка онлайн"),
        ("ul", [
            "**SSL Labs Server Test** – ланцюжок, термін, протоколи, оцінка A–F. Ретельно, займає 1–2 хвилини.",
            "**crt.sh** – усі сертифікати, коли-небудь видані на ваш домен, з журналів Certificate Transparency. Ідеально, щоб знайти забуті піддомени й несподіваних видавців.",
            "**badssl.com** – тестові сайти з навмисно зламаними сертифікатами для тренування.",
        ]),
        ("h", "Linux: спершу ім'я і DNS"),
        ("p", "Половина «проблем із сертифікатом» – це проблеми DNS: домен вказує не на той сервер або забутий IPv6-запис веде деінде."),
        ("code", "linux_dns"),
        ("h", "Linux: openssl s_client"),
        ("p", "Важливий ключ `-servername`: він надсилає SNI. Без SNI сервер із кількома доменами часто віддає зовсім інший сертифікат, і ви перевіряєте не той."),
        ("code", "linux_openssl"),
        ("table", _codes("uk", ["Verify return code", "Що означає"])),
        ("code", "linux_more"),
        ("code", "badssl"),
        ("h", "Windows: PowerShell"),
        ("p", "Без додаткових програм: DNS, порт і сертифікат прямо з PowerShell. Якщо встановлено Git for Windows, у Git Bash є ще й `openssl`, і команди для Linux вище теж працюють."),
        ("code", "windows"),
        ("h", "Що вже траплялося із сертифікатами"),
        ("ul", [
            "**2018 – Symantec:** після повторних порушень Chrome і Firefox перестали довіряти всім сертифікатам Symantec. Мільйонам сайтів довелося переходити.",
            "**30.09.2021 – DST Root CA X3:** закінчився старий root Let's Encrypt. Сучасні браузери нічого не помітили, а старі Android, OpenSSL 1.0.x і багато скриптів та інтеграцій зламалися.",
            "**2024 – Entrust:** Chrome та інші перестали довіряти новим сертифікатам Entrust.",
            "**Коротші терміни:** за рішенням CA/Browser Forum SC-081 максимальний термін скорочується поступово: 200 днів із березня 2026, 100 днів із березня 2027, 47 днів із березня 2029. Let's Encrypt із 2025 року не надсилає листів про закінчення терміну.",
        ]),
        ("h", "Зараз: eMudhra (жовтень–листопад 2026)"),
        ("p", "17 жовтня 2026 року стало відомо, що вісім проміжних сертифікатів індійського CA eMudhra створено зі слабкими ключами, які можна відновити (церемонія генерації ключів у квітні 2025). Mozilla перестала довіряти root **emSign ECC Root CA – G3** 20 жовтня, Chrome – 27 жовтня. 22 жовтня eMudhra оголосила про вихід із публічного TLS-бізнесу. За даними eMudhra і галузевих оглядів, наступний – RSA-root **emSign Root CA – G1**: Microsoft видаляє його 16 листопада, Apple – 30 листопада."),
        ("code", "emudhra"),
        ("ul", [
            "Якщо в ланцюжку є eMudhra/emSign: перевипустіть сертифікат в іншому CA. RSA-сертифікати eMudhra теж уже не довгострокове рішення.",
            "Перевірте CAA-записи: якщо домен дозволяє лише `emsign.com`, інший CA сертифікат не видасть.",
            "Не лише вебсервери: балансувальники, VPN, поштові сервери й пристрої з вручну імпортованими сертифікатами.",
        ]),
        ("h", "Загальні поради"),
        ("ul", [
            "Перевіряйте ззовні те, що **реально віддається**, а не файл на диску.",
            "Завжди з SNI (`-servername`) і завжди **весь ланцюжок**.",
            "Алерт за 21, 14 і 7 днів, а не в день закінчення.",
            "Ведіть перелік усіх сертифікатів: домени, піддомени, пошта, VPN, пристрої; crt.sh допоможе їх знайти.",
            "Автоматизуйте продовження (див. статтю про certbot): із 47-денними сертифікатами інакше не вийде.",
        ]),
        ("links", "Джерела та інструменти"),
    ],
}

SSL["t"]["ru"] = {
    "title": "Когда истекает SSL-сертификат? Инструменты для Linux и Windows – и при чём тут eMudhra",
    "summary": "TLS за минуту, онлайн-проверки, openssl/dig/curl в Linux, PowerShell в Windows, что значат коды Verify, уроки истории и актуальная ситуация с eMudhra.",
    "body": [
        ("h", "TLS за минуту"),
        ("p", "TLS (раньше SSL) делает две вещи: **шифрует** соединение между браузером и сервером и **доказывает**, что сервер действительно принадлежит этому домену. Доказательство – сертификат: домен + открытый ключ + подпись удостоверяющего центра (CA)."),
        ("p", "Проверяется **цепочка**: сертификат сервера → промежуточный (intermediate) → корневой (root). В браузерах и ОС хранятся только root-сертификаты. Если промежуточного не хватает или браузер перестал доверять root, даже «действительный» сертификат вдруг ничего не стоит. И у каждого сертификата есть фиксированная дата окончания (`notAfter`)."),
        ("h", "Проверка онлайн"),
        ("ul", [
            "**SSL Labs Server Test** – цепочка, срок, протоколы, оценка A–F. Тщательно, занимает 1–2 минуты.",
            "**crt.sh** – все сертификаты, когда-либо выданные на ваш домен, из журналов Certificate Transparency. Идеально, чтобы найти забытые поддомены и неожиданных издателей.",
            "**badssl.com** – тестовые сайты с намеренно сломанными сертификатами для тренировки.",
        ]),
        ("h", "Linux: сначала имя и DNS"),
        ("p", "Половина «проблем с сертификатом» – это проблемы DNS: домен указывает не на тот сервер или забытая IPv6-запись ведёт в другое место."),
        ("code", "linux_dns"),
        ("h", "Linux: openssl s_client"),
        ("p", "Важен ключ `-servername`: он отправляет SNI. Без SNI сервер с несколькими доменами часто отдаёт совсем другой сертификат, и вы проверяете не тот."),
        ("code", "linux_openssl"),
        ("table", _codes("ru", ["Verify return code", "Что значит"])),
        ("code", "linux_more"),
        ("code", "badssl"),
        ("h", "Windows: PowerShell"),
        ("p", "Без дополнительных программ: DNS, порт и сертификат прямо из PowerShell. Если установлен Git for Windows, в Git Bash есть ещё и `openssl`, и команды для Linux выше тоже работают."),
        ("code", "windows"),
        ("h", "Что уже случалось с сертификатами"),
        ("ul", [
            "**2018 – Symantec:** после повторных нарушений Chrome и Firefox перестали доверять всем сертификатам Symantec. Миллионам сайтов пришлось переходить.",
            "**30.09.2021 – DST Root CA X3:** истёк старый root Let's Encrypt. Современные браузеры ничего не заметили, а старые Android, OpenSSL 1.0.x и многие скрипты и интеграции сломались.",
            "**2024 – Entrust:** Chrome и другие перестали доверять новым сертификатам Entrust.",
            "**Короче сроки:** по решению CA/Browser Forum SC-081 максимальный срок сокращается постепенно: 200 дней с марта 2026, 100 дней с марта 2027, 47 дней с марта 2029. Let's Encrypt с 2025 года не присылает писем об истечении срока.",
        ]),
        ("h", "Сейчас: eMudhra (октябрь–ноябрь 2026)"),
        ("p", "17 октября 2026 года стало известно, что восемь промежуточных сертификатов индийского CA eMudhra созданы со слабыми ключами, которые можно восстановить (церемония генерации ключей в апреле 2025). Mozilla перестала доверять root **emSign ECC Root CA – G3** 20 октября, Chrome – 27 октября. 22 октября eMudhra объявила об уходе из публичного TLS-бизнеса. По данным eMudhra и отраслевых обзоров, следующий – RSA-root **emSign Root CA – G1**: Microsoft удаляет его 16 ноября, Apple – 30 ноября."),
        ("code", "emudhra"),
        ("ul", [
            "Если в цепочке есть eMudhra/emSign: перевыпустите сертификат в другом CA. RSA-сертификаты eMudhra тоже уже не долгосрочное решение.",
            "Проверьте CAA-записи: если домен разрешает только `emsign.com`, другой CA сертификат не выдаст.",
            "Не только веб-серверы: балансировщики, VPN, почтовые серверы и устройства с вручную импортированными сертификатами.",
        ]),
        ("h", "Общие советы"),
        ("ul", [
            "Проверяйте снаружи то, что **реально отдаётся**, а не файл на диске.",
            "Всегда с SNI (`-servername`) и всегда **всю цепочку**.",
            "Алерт за 21, 14 и 7 дней, а не в день окончания.",
            "Ведите список всех сертификатов: домены, поддомены, почта, VPN, устройства; crt.sh поможет их найти.",
            "Автоматизируйте продление (см. статью про certbot): с 47-дневными сертификатами иначе не получится.",
        ]),
        ("links", "Источники и инструменты"),
    ],
}

SSL["t"]["fr"] = {
    "title": "Quand le certificat SSL expire-t-il ? Outils pour Linux et Windows – et le rôle d’eMudhra",
    "summary": "TLS en une minute, vérifications en ligne, openssl/dig/curl sous Linux, PowerShell sous Windows, la signification des codes Verify, les leçons de l’histoire et le cas actuel d’eMudhra.",
    "body": [
        ("h", "TLS en une minute"),
        ("p", "TLS (anciennement SSL) fait deux choses : il **chiffre** la connexion entre le navigateur et le serveur, et il **prouve** que le serveur appartient bien à ce domaine. La preuve, c’est le certificat : domaine + clé publique + signature d’une autorité de certification (CA)."),
        ("p", "Ce qui est vérifié, c’est une **chaîne** : certificat du serveur → intermédiaire → racine. Seules les racines sont enregistrées dans les navigateurs et les systèmes. Si l’intermédiaire manque, ou si un navigateur retire sa confiance à la racine, même un certificat « valide » ne vaut soudain plus rien. Et chaque certificat a une date d’expiration fixe (`notAfter`)."),
        ("h", "Vérifier en ligne"),
        ("ul", [
            "**SSL Labs Server Test** – chaîne, expiration, protocoles, note A–F. Complet, 1 à 2 minutes.",
            "**crt.sh** – tous les certificats jamais émis pour votre domaine, issus des journaux Certificate Transparency. Idéal pour trouver des sous-domaines oubliés et des émetteurs inattendus.",
            "**badssl.com** – sites de test avec des certificats volontairement défectueux pour s’entraîner.",
        ]),
        ("h", "Linux : d’abord le nom et le DNS"),
        ("p", "La moitié des « problèmes de certificat » sont des problèmes de DNS : le domaine pointe vers le mauvais serveur, ou un enregistrement IPv6 oublié mène ailleurs."),
        ("code", "linux_dns"),
        ("h", "Linux : openssl s_client"),
        ("p", "`-servername` est essentiel : il envoie le SNI. Sans SNI, un serveur hébergeant plusieurs domaines renvoie souvent un tout autre certificat – et l’on vérifie le mauvais."),
        ("code", "linux_openssl"),
        ("table", _codes("fr", ["Verify return code", "Signification"])),
        ("code", "linux_more"),
        ("code", "badssl"),
        ("h", "Windows : PowerShell"),
        ("p", "Sans logiciel supplémentaire : DNS, port et certificat directement depuis PowerShell. Si Git pour Windows est installé, Git Bash fournit aussi `openssl`, et les commandes Linux ci-dessus fonctionnent."),
        ("code", "windows"),
        ("h", "Ce qui est déjà arrivé aux certificats"),
        ("ul", [
            "**2018 – Symantec :** après des manquements répétés, Chrome et Firefox ont retiré leur confiance à tous les certificats Symantec. Des millions de sites ont dû changer.",
            "**30/09/2021 – DST Root CA X3 :** l’ancienne racine de Let’s Encrypt a expiré. Les navigateurs récents n’ont rien remarqué, mais d’anciens appareils Android, OpenSSL 1.0.x et de nombreux scripts et interfaces ont cessé de fonctionner.",
            "**2024 – Entrust :** Chrome et d’autres ont cessé de faire confiance aux nouveaux certificats Entrust.",
            "**Durées plus courtes :** selon la décision SC-081 du CA/Browser Forum, la durée maximale baisse par étapes : 200 jours dès mars 2026, 100 jours dès mars 2027, 47 jours dès mars 2029. Let’s Encrypt n’envoie plus d’e-mails d’expiration depuis 2025.",
        ]),
        ("h", "En ce moment : eMudhra (octobre–novembre 2026)"),
        ("p", "Le 17 octobre 2026, on a appris que huit certificats intermédiaires de l’autorité indienne eMudhra avaient été générés avec des clés faibles et reconstituables (cérémonie de clés en avril 2025). Mozilla a retiré sa confiance à la racine **emSign ECC Root CA – G3** le 20 octobre, Chrome le 27 octobre. Le 22 octobre, eMudhra a annoncé quitter le marché public du TLS. D’après eMudhra et des articles spécialisés, la racine RSA **emSign Root CA – G1** suit : Microsoft la retire le 16 novembre, Apple le 30 novembre."),
        ("code", "emudhra"),
        ("ul", [
            "Si eMudhra/emSign apparaît dans la chaîne : faire réémettre le certificat par une autre CA – les certificats RSA d’eMudhra ne sont plus une solution durable non plus.",
            "Vérifier les enregistrements CAA : si le domaine n’autorise que `emsign.com`, aucune autre CA ne peut émettre.",
            "Pas seulement les serveurs web : répartiteurs de charge, VPN, serveurs de messagerie et appareils avec certificats importés à la main.",
        ]),
        ("h", "Conseils généraux"),
        ("ul", [
            "Vérifier depuis l’extérieur ce qui est **réellement servi** – pas le fichier sur le disque.",
            "Toujours avec SNI (`-servername`) et toujours **toute la chaîne**.",
            "Alerte à 21, 14 et 7 jours – pas le jour de l’expiration.",
            "Tenir un inventaire de tous les certificats : domaines, sous-domaines, messagerie, VPN, appareils ; crt.sh aide à les trouver.",
            "Automatiser le renouvellement (voir l’article sur certbot) – avec des certificats de 47 jours, il n’y a pas d’autre moyen.",
        ]),
        ("links", "Sources et outils"),
    ],
}

SSL["t"]["el"] = {
    "title": "Πότε λήγει το πιστοποιητικό SSL; Εργαλεία για Linux και Windows – και τι σχέση έχει η eMudhra",
    "summary": "Το TLS σε ένα λεπτό, έλεγχοι online, openssl/dig/curl σε Linux, PowerShell σε Windows, τι σημαίνουν οι κωδικοί Verify, διδάγματα από την ιστορία και η τρέχουσα υπόθεση eMudhra.",
    "body": [
        ("h", "Το TLS σε ένα λεπτό"),
        ("p", "Το TLS (παλαιότερα SSL) κάνει δύο πράγματα: **κρυπτογραφεί** τη σύνδεση μεταξύ browser και server και **αποδεικνύει** ότι ο server ανήκει πράγματι στο domain. Η απόδειξη είναι το πιστοποιητικό: domain + δημόσιο κλειδί + υπογραφή μιας αρχής πιστοποίησης (CA)."),
        ("p", "Αυτό που ελέγχεται είναι μια **αλυσίδα**: πιστοποιητικό server → ενδιάμεσο (intermediate) → ρίζα (root). Μόνο οι ρίζες είναι αποθηκευμένες σε browsers και λειτουργικά συστήματα. Αν λείπει το ενδιάμεσο ή αν ένας browser πάψει να εμπιστεύεται τη ρίζα, ακόμη και ένα «έγκυρο» πιστοποιητικό ξαφνικά δεν αξίζει τίποτα. Και κάθε πιστοποιητικό έχει σταθερή ημερομηνία λήξης (`notAfter`)."),
        ("h", "Έλεγχος online"),
        ("ul", [
            "**SSL Labs Server Test** – αλυσίδα, λήξη, πρωτόκολλα, βαθμός A–F. Διεξοδικό, διαρκεί 1–2 λεπτά.",
            "**crt.sh** – όλα τα πιστοποιητικά που εκδόθηκαν ποτέ για το domain σας, από τα αρχεία Certificate Transparency. Ιδανικό για ξεχασμένα subdomains και απρόσμενους εκδότες.",
            "**badssl.com** – δοκιμαστικές σελίδες με σκόπιμα χαλασμένα πιστοποιητικά για εξάσκηση.",
        ]),
        ("h", "Linux: πρώτα όνομα και DNS"),
        ("p", "Τα μισά «προβλήματα πιστοποιητικού» είναι προβλήματα DNS: το domain δείχνει σε λάθος server ή μια ξεχασμένη εγγραφή IPv6 οδηγεί αλλού."),
        ("code", "linux_dns"),
        ("h", "Linux: openssl s_client"),
        ("p", "Το `-servername` είναι σημαντικό: στέλνει SNI. Χωρίς SNI, ένας server με πολλά domains συχνά επιστρέφει εντελώς άλλο πιστοποιητικό – και ελέγχετε το λάθος."),
        ("code", "linux_openssl"),
        ("table", _codes("el", ["Verify return code", "Σημασία"])),
        ("code", "linux_more"),
        ("code", "badssl"),
        ("h", "Windows: PowerShell"),
        ("p", "Χωρίς επιπλέον λογισμικό: DNS, θύρα και πιστοποιητικό απευθείας από το PowerShell. Αν είναι εγκατεστημένο το Git for Windows, το Git Bash έχει και `openssl`, οπότε δουλεύουν και οι εντολές Linux παραπάνω."),
        ("code", "windows"),
        ("h", "Τι έχει ήδη συμβεί με τα πιστοποιητικά"),
        ("ul", [
            "**2018 – Symantec:** μετά από επανειλημμένες παραβάσεις, Chrome και Firefox έπαψαν να εμπιστεύονται όλα τα πιστοποιητικά της Symantec. Εκατομμύρια sites χρειάστηκε να αλλάξουν.",
            "**30/09/2021 – DST Root CA X3:** έληξε η παλιά ρίζα της Let's Encrypt. Οι σύγχρονοι browsers δεν κατάλαβαν τίποτα, αλλά παλιές συσκευές Android, το OpenSSL 1.0.x και πολλά scripts και διασυνδέσεις σταμάτησαν να λειτουργούν.",
            "**2024 – Entrust:** ο Chrome και άλλοι έπαψαν να εμπιστεύονται νέα πιστοποιητικά της Entrust.",
            "**Μικρότερη διάρκεια:** με την απόφαση SC-081 του CA/Browser Forum η μέγιστη διάρκεια μειώνεται σταδιακά: 200 ημέρες από τον Μάρτιο 2026, 100 ημέρες από τον Μάρτιο 2027, 47 ημέρες από τον Μάρτιο 2029. Η Let's Encrypt δεν στέλνει πλέον e-mail λήξης από το 2025.",
        ]),
        ("h", "Τώρα: eMudhra (Οκτώβριος–Νοέμβριος 2026)"),
        ("p", "Στις 17 Οκτωβρίου 2026 έγινε γνωστό ότι οκτώ ενδιάμεσα πιστοποιητικά της ινδικής CA eMudhra είχαν δημιουργηθεί με αδύναμα κλειδιά που μπορούν να ανακτηθούν (τελετή δημιουργίας κλειδιών τον Απρίλιο 2025). Η Mozilla έπαψε να εμπιστεύεται τη ρίζα **emSign ECC Root CA – G3** στις 20 Οκτωβρίου, ο Chrome στις 27 Οκτωβρίου. Στις 22 Οκτωβρίου η eMudhra ανακοίνωσε την αποχώρησή της από τη δημόσια αγορά TLS. Σύμφωνα με την eMudhra και εξειδικευμένα δημοσιεύματα, ακολουθεί η ρίζα RSA **emSign Root CA – G1**: η Microsoft την αφαιρεί στις 16 Νοεμβρίου, η Apple στις 30 Νοεμβρίου."),
        ("code", "emudhra"),
        ("ul", [
            "Αν η eMudhra/emSign εμφανίζεται στην αλυσίδα: επανέκδοση του πιστοποιητικού από άλλη CA – ούτε τα RSA πιστοποιητικά της eMudhra είναι πια μόνιμη λύση.",
            "Ελέγξτε τις εγγραφές CAA: αν το domain επιτρέπει μόνο `emsign.com`, καμία άλλη CA δεν μπορεί να εκδώσει.",
            "Όχι μόνο web servers: load balancers, VPN, mail servers και συσκευές με χειροκίνητα εισαγμένα πιστοποιητικά.",
        ]),
        ("h", "Γενικές συμβουλές"),
        ("ul", [
            "Ελέγχετε απ' έξω τι **σερβίρεται πραγματικά** – όχι το αρχείο στον δίσκο.",
            "Πάντα με SNI (`-servername`) και πάντα **ολόκληρη την αλυσίδα**.",
            "Ειδοποίηση στις 21, 14 και 7 ημέρες – όχι την ημέρα της λήξης.",
            "Κρατήστε κατάλογο όλων των πιστοποιητικών: domains, subdomains, mail, VPN, συσκευές· το crt.sh βοηθά να τα βρείτε.",
            "Αυτοματοποιήστε την ανανέωση (βλ. άρθρο για certbot) – με πιστοποιητικά 47 ημερών δεν γίνεται αλλιώς.",
        ]),
        ("links", "Πηγές και εργαλεία"),
    ],
}
