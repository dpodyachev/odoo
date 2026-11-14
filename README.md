# Goldberg · Odoo Services

Статический сайт об услугах Odoo для DACH (Германия, Австрия, Швейцария). Языки: DE (по умолчанию), EN, FR, UK, RU.
Без cookies, трекинга, внешних шрифтов и скриптов.

## Структура

- `src/config.py` — контакты, данные для Impressum, Cal.com, цены и пакеты.
- `src/lang_<xx>.py` — тексты на каждом языке (ключи одинаковые во всех файлах).
- `src/build.py` — генератор: `python3 src/build.py` → `site/<xx>/index.html`, `impressum.html`, `datenschutz.html`, `sitemap.xml`, `robots.txt`.
- `site/` — готовый сайт (коммитится). `site/index.html` + `assets/lang.js` выбирают язык по настройкам браузера, по умолчанию `/de/`.
- `site/_headers` — заголовки безопасности для Cloudflare Pages (CSP и др.).

## Cloudflare Pages

Workers & Pages → Create → Pages → Connect to Git → этот репозиторий.
Framework preset: None · Build command: *(пусто)* · Build output directory: `site`.
Потом Custom domains → `goldberg.pp.ua`.

## Перед публикацией

1. Заполнить в `src/config.py`: `OWNER_NAME`, `OWNER_STREET`, `OWNER_CITY`, `VAT_ID` (Impressum обязателен, § 5 DDG).
2. Завести Cal.com и вписать `CAL_URL` (пока кнопка «Termin buchen» ведёт в Telegram).
3. `python3 src/build.py`, проверить, закоммитить.
