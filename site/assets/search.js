// Поиск по сайту: индекс assets/search-index.json (строит src/search_index.py). Слова запроса – И; точное слово весит больше,
// начало слова (от 2 букв) – тоже находит: pg_d → pg_dump. Результаты – на языке страницы, разделы со ссылкой на #якорь.
(function () {
  var box = document.getElementById("results"), q = document.getElementById("q");
  if (!box || !q) return;
  var lang = box.dataset.lang, idx = null, keys = null, timer = null;
  var STOP = {the: 1, and: 1, or: 1, a: 1, an: 1, of: 1, to: 1, in: 1, on: 1, for: 1, with: 1, how: 1, is: 1, odoo: 1};

  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return {"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;"}[c]; }); }

  function terms(s) {
    return (s.toLowerCase().match(/[a-z0-9][a-z0-9_.\-\/]*/g) || [])
      .map(function (t) { return t.replace(/^[._\-\/]+|[._\-\/]+$/g, ""); })
      .filter(function (t) { return t.length > 1 && !STOP[t]; });
  }

  function lookup(t) {           // {docIndex: score} для одного слова: точное совпадение + слова, начинающиеся с t
    var hit = {}, m = [];
    if (idx.w[t]) m.push([t, 1]);
    if (t.length >= 2) keys.forEach(function (k) { if (k !== t && k.indexOf(t) === 0) m.push([k, 0.6]); });
    if (!m.length && t.length >= 4) keys.forEach(function (k) { if (k.indexOf(t) > 0) m.push([k, 0.3]); });   // внутри слова: dump → pg_dump
    m.forEach(function (km) {
      idx.w[km[0]].forEach(function (p) {
        var v = p[1] * km[1];
        if (!hit[p[0]] || hit[p[0]].s < v) hit[p[0]] = {s: v, w: km[0]};
        else hit[p[0]].s += v * 0.1;
      });
    });
    return hit;
  }

  function run() {
    var ts = terms(q.value), url = new URL(location.href);
    if (q.value) url.searchParams.set("q", q.value); else url.searchParams.delete("q");
    history.replaceState(null, "", url);
    if (!ts.length) { box.innerHTML = ""; return; }
    var acc = null;
    ts.forEach(function (t) {
      var h = lookup(t), next = {};
      Object.keys(h).forEach(function (d) {
        if (acc === null) next[d] = {s: h[d].s, w: [h[d].w]};
        else if (acc[d]) next[d] = {s: acc[d].s + h[d].s, w: acc[d].w.concat(h[d].w)};
      });
      acc = next;
    });
    var res = Object.keys(acc).map(function (d) { return [+d, acc[d]]; })
      .sort(function (a, b) { return b[1].s - a[1].s; });
    // не больше 3 разделов одной страницы
    var per = {}, out = [];
    res.forEach(function (r) {
      var u = idx.d[r[0]][0].split("#")[0];
      per[u] = (per[u] || 0) + 1;
      if (per[u] <= 3 && out.length < 40) out.push(r);
    });
    if (!out.length) { box.innerHTML = '<p class="post-note">' + esc(box.dataset.none) + "</p>"; return; }
    box.innerHTML = '<p class="post-meta">' + out.length + " " + esc(box.dataset.n) + "</p>" + out.map(function (r) {
      var d = idx.d[r[0]], page = d[0].split("#")[0], t = idx.p[page] || {};
      var title = t[lang] || t.en || page || "Goldberg";
      var href = "/" + lang + "/" + d[0];
      var uniq = r[1].w.filter(function (w, i, a) { return a.indexOf(w) === i; });
      return '<article class="post-card search-hit"><h2><a href="' + esc(href) + '">' + esc(title) + "</a></h2>" +
        ((d[1][lang] || d[1].en) ? '<p class="search-sec">› <a href="' + esc(href) + '">' + esc(d[1][lang] || d[1].en) + "</a></p>" : "") +
        '<p class="post-meta">' + esc(box.dataset.words) + ": " + uniq.map(function (w) { return "<code>" + esc(w) + "</code>"; }).join(" ") +
        ' · <span class="search-url">/' + esc(lang + "/" + d[0]) + "</span></p></article>";
    }).join("");
  }

  function load(then) {
    if (idx) return then();
    fetch(box.dataset.index).then(function (r) { return r.json(); }).then(function (j) {
      idx = j; keys = Object.keys(j.w); then();
    });
  }

  q.addEventListener("input", function () { clearTimeout(timer); timer = setTimeout(function () { load(run); }, 150); });
  q.form.addEventListener("submit", function () { load(run); });
  var init = new URL(location.href).searchParams.get("q");
  if (init) { q.value = init; load(run); }
})();
