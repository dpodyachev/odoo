# Общие настройки сайта. Меняйте здесь, затем: python3 src/build.py
BASE_URL = "https://2027.pp.ua"         # основной домен (canonical/hreflang/sitemap); зеркала на других доменах ссылаются сюда
BRAND = "Goldberg"                        # название в шапке
BRAND_SUB = "Odoo Services"
TELEGRAM = "https://t.me/podyachev"
TELEGRAM_HANDLE = "@podyachev"
EMAIL = "dpodiatschev@gmail.com"
CAL_URL = "https://cal.com/dmytro-podiatschev-xvsnlm"                              # ссылка Cal.com (https://cal.com/<имя>/30min); пусто — кнопка «Termin buchen» ведёт в Telegram

# Данные для Impressum — ОБЯЗАТЕЛЬНО заполнить перед публикацией (§ 5 DDG)
OWNER_NAME = "Dmytro Podiatschev – Schwaben Odoo Service"
OWNER_STREET = "Weimarer Straße 47"
OWNER_CITY = "71065 Sindelfingen"
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

SLIDE_INTERVAL_MS = 5000   # карусель site/slides/slide*.jpg|png|webp

LANG_NAMES = {"de": "Deutsch", "en": "English", "fr": "Français", "el": "Ελληνικά", "uk": "Українська", "ru": "Русский"}
# флаг в переключателе языков (site/assets/flags/<код>.svg); язык без записи — только буквы.
# ru.svg — бело-сине-белый флаг (по желанию владельца).
FLAGS = {"de": "de", "en": "gb", "fr": "fr", "el": "gr", "uk": "ua", "ru": "ru"}

# верификация поисковиков: <meta name="..." content="..."> на всех страницах
SITE_VERIFY = {"msvalidate.01": "D751EC3EE3CBDD643934E8536E0E6939"}  # Bing Webmaster Tools

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
