# Общие настройки сайта. Меняйте здесь, затем: python3 src/build.py
BASE_URL = "https://goldberg.pp.ua"      # домен на Cloudflare Pages (для canonical/hreflang/sitemap)
BRAND = "Goldberg"                        # название в шапке
BRAND_SUB = "Odoo Services"
TELEGRAM = "https://t.me/podyachev"
TELEGRAM_HANDLE = "@podyachev"
EMAIL = "dpodiatschev@gmail.com"
CAL_URL = "https://cal.com/dmytro-podiatschev-xvsnlm"                              # ссылка Cal.com (https://cal.com/<имя>/30min); пусто — кнопка «Termin buchen» ведёт в Telegram

# Данные для Impressum — ОБЯЗАТЕЛЬНО заполнить перед публикацией (§ 5 DDG)
OWNER_NAME = "Schwaben Odoo Service"
OWNER_STREET = "Sindelfingen-Goldberg"
OWNER_CITY = "Region Stuttgart, Baden-Württemberg"
OWNER_COUNTRY = "Deutschland"
# Одна из строк: USt-IdNr. / Kleinunternehmer §19 UStG / пусто
VAT_ID = "KLEINUNTERNEHMER"   # маркер: тексты по-языкам в lang_*.py (kleinunternehmer)

LANGS = ["de", "en", "fr", "uk", "ru"]     # первый — язык по умолчанию
LANG_NAMES = {"de": "Deutsch", "en": "English", "fr": "Français", "uk": "Українська", "ru": "Русский"}

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
    ("bot",            "390 €", "from_fix"),
]
PLANS = [
    # key,       price/month, hours, reaction
    ("basic",    "290 €", "3",  "2"),
    ("business", "690 €", "8",  "1"),
    ("premium",  "1 490 €", "20", "4h"),
]
