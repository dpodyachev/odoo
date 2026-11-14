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

Проект `goldberg-odoo` (direct upload, https://goldberg-odoo.pages.dev). Ключи — в `.cloudflare` (в .gitignore, не коммитить).

```bash
python3 src/build.py
export CLOUDFLARE_API_TOKEN=… CLOUDFLARE_ACCOUNT_ID=…
npx -y wrangler@3.114.0 pages deploy site --project-name goldberg-odoo --branch main
```
Свой домен: Pages → goldberg-odoo → Custom domains → `goldberg.pp.ua`.

## Перед публикацией

1. Заполнить в `src/config.py`: `OWNER_NAME`, `OWNER_STREET`, `OWNER_CITY`, `VAT_ID` (Impressum обязателен, § 5 DDG).
3. `python3 src/build.py`, проверить, закоммитить.
