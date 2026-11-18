# Проверка ссылок страницы learn.html: HTTP-код и «This course has now moved here: …» у курсов Odoo eLearning.
# Запуск: python3 src/check_learn_links.py   (код выхода 1, если есть проблемы; переехавший курс – заменить в learn_page.CATS)
import concurrent.futures as cf
import re
import sys
import urllib.request

sys.path.insert(0, __file__.rsplit("/", 1)[0])
import learn_page as L  # noqa: E402

urls = [("https://www.odoo.com/" + p + "slides/" + s) for p in ["", *set(L.SLIDES_LANG.values())] for _, cs, _, _ in L.CATS for s, _ in cs]
urls += [L.DOC + dl + d for dl in ["", *set(L.DOC_LANG.values())] for _, _, ds, _ in L.CATS for d, _ in ds]


def check(u):
    try:
        req = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as r:
            html = r.read().decode("utf-8", "ignore")
            m = re.search(r"has now moved here[\s\S]{0,400}?(/slides/[a-z0-9-]+-\d+)", html)
            return u, r.status, ("moved -> " + m.group(1)) if m else ""
    except Exception as e:  # noqa: BLE001
        return u, getattr(e, "code", 0), str(e)[:80]


bad = 0
with cf.ThreadPoolExecutor(8) as ex:
    for u, code, note in ex.map(check, urls):
        if code != 200 or note:
            bad += 1
            print(code, u, note)
print(f"{len(urls)} links checked, {bad} problems")
sys.exit(1 if bad else 0)
