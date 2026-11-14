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

Проект `goldberg-odoo` (direct upload, https://2027.pp.ua/de/ https://goldberg-odoo.pages.dev). Ключи — в `.cloudflare` (в .gitignore, не коммитить).

```bash
python3 src/build.py
export CLOUDFLARE_API_TOKEN=… CLOUDFLARE_ACCOUNT_ID=…
npx -y wrangler@3.114.0 pages deploy site --project-name goldberg-odoo --branch main
```
Домены: основной `2027.pp.ua` (CNAME @ → goldberg-odoo.pages.dev; он же `BASE_URL` в config.py для canonical/sitemap).
Зеркала: добавить в Pages → goldberg-odoo → Custom domains; canonical у всех указывает на основной домен.

## Автодеплой

`.github/workflows/deploy.yml`: при каждом push в `main` GitHub Actions собирает сайт (`src/build.py`) и выкладывает его на Cloudflare Pages.
Секреты репозитория (Settings → Secrets and variables → Actions): `CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ACCOUNT_ID`.
Ручной запуск: Actions → Deploy to Cloudflare Pages → Run workflow.

## Слайды (примеры внедрения)

Положить картинки в `site/slides/` с именами `slide1.jpg`, `slide2.jpg`, … (также .png/.webp), кадр карусели 2:1 (картинка вписывается целиком), ширина ~1600–1800 px, до 300 КБ.
Сборка сама находит все файлы и строит карусель внизу страницы (смена каждые 5 с — `SLIDE_INTERVAL_MS` в config.py).
Удалил файл — слайд исчез; нет файлов — блока нет. После замены: `python3 src/build.py` и деплой.

## Перед публикацией

1. Заполнить в `src/config.py`: `OWNER_NAME`, `OWNER_STREET`, `OWNER_CITY`, `VAT_ID` (Impressum обязателен, § 5 DDG).
3. `python3 src/build.py`, проверить, закоммитить.
