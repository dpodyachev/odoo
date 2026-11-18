# Схематичные «макеты экранов» для статей-инструкций: окно приложения, чат, терминал – inline SVG.
# Цвета берутся из CSS-переменных сайта (классы .mk-*), поэтому картинки работают в светлой и тёмной теме.
# Это схемы, а не скриншоты: подписи интерфейса упрощены, логотипов нет.
from html import escape as _e

W = 680


def _t(x, y, s, cls="mk-tx", size=13, weight=None, anchor=None, mono=False):
    a = f' text-anchor="{anchor}"' if anchor else ""
    w = f' font-weight="{weight}"' if weight else ""
    f = ' font-family="ui-monospace,Menlo,Consolas,monospace"' if mono else ""
    return f'<text x="{x}" y="{y}" class="{cls}" font-size="{size}"{w}{a}{f}>{_e(s)}</text>'


def _frame(h, title, path):
    return (f'<svg class="mock" viewBox="0 0 {W} {h}" role="img" aria-label="{_e(title)}" xmlns="http://www.w3.org/2000/svg">'
            f'<rect x="1" y="1" width="{W - 2}" height="{h - 2}" rx="10" class="mk-bg"/>'
            f'<path d="M1 34h{W - 2}" class="mk-ln"/>'
            '<circle cx="18" cy="17.5" r="5" class="mk-dot"/><circle cx="34" cy="17.5" r="5" class="mk-dot"/><circle cx="50" cy="17.5" r="5" class="mk-dot"/>'
            + _t(70, 22, title, "mk-tx", 13, "700") + _t(W - 14, 22, path, "mk-mu", 12, anchor="end"))


def app(title, path, side, active, rows, note=None):
    """side: пункты меню слева; active: индекс выделенного; rows: [(слева, справа, выделить?)] – таблица справа."""
    h = max(70 + 30 * len(side), 70 + 32 * len(rows)) + (34 if note else 0)
    s = [_frame(h, title, path), f'<path d="M170 34v{h - 35}" class="mk-ln"/>']
    for i, it in enumerate(side):
        y = 58 + 30 * i
        if i == active:
            s.append(f'<rect x="8" y="{y - 17}" width="154" height="26" rx="6" class="mk-hl"/>')
        s.append(_t(20, y, it, "mk-tx" if i == active else "mk-mu", 13, "700" if i == active else None))
    for i, r in enumerate(rows):
        left, right, hl = r[0], r[1], len(r) > 2 and r[2]
        y = 60 + 32 * i
        if hl:
            s.append(f'<rect x="182" y="{y - 19}" width="{W - 196}" height="28" rx="6" class="mk-hl"/>')
        s.append(_t(194, y, left, "mk-tx", 13, "700" if i == 0 else None))
        s.append(_t(W - 26, y, right, "mk-ok" if hl else "mk-mu", 13, "700" if hl else None, anchor="end"))
        if i == 0:
            s.append(f'<path d="M182 {y + 10}h{W - 196}" class="mk-ln"/>')
    if note:
        s.append(_t(194, h - 16, "➜ " + note, "mk-ac", 13, "700"))
    return "".join(s) + "</svg>"


def chat(title, path, msgs):
    """msgs: [(время, текст, вид)] вид: ok / warn / bad / me."""
    h = 52 + 46 * len(msgs)
    s = [_frame(h, title, path)]
    for i, (tm, txt, kind) in enumerate(msgs):
        y = 46 + 46 * i
        x, w = (W - 470, 456) if kind == "me" else (14, 520)
        s.append(f'<rect x="{x}" y="{y}" width="{w}" height="36" rx="12" class="mk-b-{kind}"/>')
        s.append(_t(x + 14, y + 23, txt, "mk-tx", 13))
        s.append(_t(x + w - 10, y + 23, tm, "mk-mu", 11, anchor="end"))
    return "".join(s) + "</svg>"


def term(title, lines):
    """lines: строки; начинающиеся с '$ ' – команды, с '# ' – комментарии, с '! ' – выделенные."""
    h = 56 + 22 * len(lines)
    s = [_frame(h, title, "")]
    for i, ln in enumerate(lines):
        y = 58 + 22 * i
        cls = "mk-ac" if ln.startswith("$ ") else "mk-mu" if ln.startswith("# ") else "mk-ok" if ln.startswith("! ") else "mk-tx"
        s.append(_t(16, y, ln[2:] if ln.startswith("! ") else ln, cls, 13, mono=True))
    return "".join(s) + "</svg>"
