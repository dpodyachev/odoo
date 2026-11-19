# Общие настройки сайта. Меняйте здесь, затем: python3 src/build.py
BASE_URL = "https://2027.pp.ua"         # основной домен (canonical/hreflang/sitemap); зеркала на других доменах ссылаются сюда
BRAND = "Goldberg"                        # название в шапке
BRAND_SUB = "Odoo Services"

# Личные контакты НЕ хранятся в git (репозиторий публичный): src/private.json (в .gitignore) или
# переменная окружения SITE_PRIVATE = base64(JSON) — в GitHub Action из секрета SITE_PRIVATE.
# Ключи: telegram, telegram_handle, email, phone, phone_display, whatsapp, street, city.
# На сайте они попадают только в закодированном виде (assets/contacts.js) и подставляются в браузере.
def _load_private():
    import base64, json, os
    f = os.path.join(os.path.dirname(os.path.abspath(__file__)), "private.json")
    if os.path.exists(f):
        with open(f, encoding="utf-8") as fh:
            return json.load(fh)
    if os.environ.get("SITE_PRIVATE", "").strip():
        return json.loads(base64.b64decode(os.environ["SITE_PRIVATE"].strip()).decode("utf-8"))
    return None


PRIVATE = _load_private()
_P = PRIVATE or {}
TELEGRAM = _P.get("telegram", "")
TELEGRAM_HANDLE = _P.get("telegram_handle", "")
EMAIL = _P.get("email", "")
PHONE = _P.get("phone", "")              # пусто — значок не показывать
PHONE_DISPLAY = _P.get("phone_display", PHONE)
WHATSAPP = _P.get("whatsapp", "")
LINKEDIN = "https://www.linkedin.com/in/dpodyachev"     # пусто — не показывать
CAL_URL = "https://cal.com/dmytro-podiatschev-xvsnlm"                              # ссылка Cal.com (https://cal.com/<имя>/30min); пусто — кнопка «Termin buchen» ведёт в Telegram

# Данные для Impressum — ОБЯЗАТЕЛЬНО заполнить перед публикацией (§ 5 DDG); улица и город — в private.json
OWNER_NAME = "Dmytro Podiatschev – Schwaben Odoo Service"
OWNER_STREET = _P.get("street", "")
OWNER_CITY = _P.get("city", "")
OWNER_COUNTRY = "Deutschland"
# Одна из строк: USt-IdNr. / Kleinunternehmer §19 UStG / пусто
VAT_ID = "KLEINUNTERNEHMER"   # маркер: тексты по-языкам в lang_*.py (kleinunternehmer)

LANGS = ["de", "en", "fr", "el", "uk", "ru"]     # первый — язык по умолчанию

# Цены (EUR, netto). Названия — в lang_*.py по ключу.
PRICES = [
    # key,            price,   unit
    ("hourly_support", "65 €", "h"),
    ("hourly_urgent",  "95 €", "h"),
    ("healthcheck",    "490 €", "fix"),
    ("diagnosis",      "190 €", "fix"),
    ("install",        "990 €", "from_fix"),
    ("module_update",  "190 €", "from_fix"),
    ("migration",      "1 500 €", "from"),
    ("datev",          "1 200 €", "from"),
    ("einvoice",       "900 €", "from"),
    ("shop",           "1 500 €", "from"),
    ("shipping",       "900 €", "from"),
    ("qrbill",         "600 €", "from"),
    ("monitoring",     "590 €", "from_fix"),
    ("loadtest",       "890 €", "from"),
    ("replica",        "+10 %", "pct"),      # надбавка к проекту
    ("bot",            "390 €", "from_fix"),
]
# Einstiegsangebot для новых клиентов (блок над тарифами). Срок обязателен; после даты блок
# пропадает при следующей сборке. Убрать совсем: OFFER = None
OFFER = {"price": "49 €", "hours": 5, "until": "2027-03-31"}

PLANS = [
    # key,       price/month, hours, reaction
    ("basic",    "290 €", "3",  "2"),
    ("business", "690 €", "8",  "1"),
    ("premium",  "1 490 €", "20", "4h"),
]

# Пакеты часов (предоплата, 12 мес.) – те же размеры, что Odoo Success Packs; последняя колонка – цена Odoo для новых
# клиентов (−15 %) с odoo.com/pricing-packs на 19.11.2026 (цены Odoo зависят от страны: из ЕС видно 499/2635/4675/8415/16830,
# минимальный региональный вариант – 280/1445/2550/4590/9180; наши ниже обоих). Убрать блок: PACKS = []
PACKS = [
    # name,       hours, price,     odoo
    ("Start",     4,   "239 €",   "499 €"),
    ("Basic",     25,  "1 375 €", "2 635 €"),
    ("Standard",  50,  "2 450 €", "4 675 €"),
    ("Plus",      100, "4 450 €", "8 415 €"),
    ("Pro",       200, "8 600 €", "16 830 €"),
]

SLIDE_INTERVAL_MS = 5000   # карусель site/slides/slide*.jpg|png|webp

LANG_NAMES = {"de": "Deutsch", "en": "English", "fr": "Français", "el": "Ελληνικά", "uk": "Українська", "ru": "Русский"}
# флаг в переключателе языков (site/assets/flags/<код>.svg); язык без записи — только буквы.
# ru.svg — бело-сине-белый флаг (по желанию владельца).
FLAGS = {"de": "de", "en": "gb", "fr": "fr", "el": "gr", "uk": "ua", "ru": "ru"}

# верификация поисковиков: <meta name="..." content="..."> на всех страницах
SITE_VERIFY = {"msvalidate.01": "D751EC3EE3CBDD643934E8536E0E6939"}  # Bing Webmaster Tools

# IndexNow (Bing, Yandex, Seznam, Naver …): ключ публичный, файл /<ключ>.txt создаёт build.py,
# после деплоя GitHub Action отправляет список URL из sitemap.xml. Пусто — выключено.
INDEXNOW_KEY = "39731d66220babc103a1e35f4f79b3ce"

# значок пункта меню «Цены» (подпись — во всплывающей подсказке); по умолчанию €
PRICE_ICON = {"en": "$", "uk": "₴", "ru": "₴"}

# карта в «Über mich»: города с проектами (lon, lat, позиция подписи: e/w/s); home — свой офис
MAP_CITIES = [
    ("frankfurt", 8.68, 50.11, "e"), ("berlin", 13.40, 52.52, "e"), ("stuttgart", 9.18, 48.78, "w"),
    ("ulm", 9.99, 48.40, "e"), ("luzern", 8.31, 47.05, "e"),
    ("kyiv", 30.52, 50.45, "w"), ("poltava", 34.55, 49.59, "e"), ("dnipro", 35.05, 48.46, "s"),
    ("odesa", 30.72, 46.48, "w"), ("kherson", 32.61, 46.64, "s"),
]
MAP_HOME = "stuttgart"
# подпись проекта под городом — только на широких экранах (≥1200px), см. .map .proj в style.css
MAP_PROJECTS = {"berlin": "Teufel Raumfeld", "frankfurt": "infomir.eu", "stuttgart": "DXC · Luxoft",
                "ulm": "BMW · Harman", "luzern": "Radio AzuraCast"}
