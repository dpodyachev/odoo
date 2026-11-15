// /backup/ – list + direct multipart upload to R2 via pre-signed URLs (API: /backup/api/*, Basic Auth).
(function () {
  var L = {
    de: { s3: "Per S3-Tool hochgeladen (aws s3 / rclone), ohne Beschreibung:", upload: "+ Hochladen", up_title: "Neue Datei", f_title: "Titel", drop: "Datei auswählen oder hierher ziehen", f_desc: "Beschreibung",
          note: "Die Datei geht direkt in Cloudflare R2 (privater Bucket). Große Dateien werden in Teilen hochgeladen – Tab bis zum Ende offen lassen.",
          save: "Hochladen", cancel: "Abbrechen", files: "Dateien", loading: "Lädt…", empty: "Noch keine Dateien.", download: "Herunterladen",
          delete: "Löschen", confirm: "Diese Datei endgültig löschen?", nofile: "Bitte eine Datei auswählen.", done: "Fertig", err: "Fehler",
          prep: "Vorbereitung…", finishing: "Abschließen…", unfinished: "unvollständig", total: "Dateien", nodesc: "Keine Beschreibung.", leave: "Upload läuft – wirklich verlassen?" },
    en: { s3: "Uploaded with an S3 tool (aws s3 / rclone), no description:", upload: "+ Upload", up_title: "New file", f_title: "Title", drop: "Choose a file or drop it here", f_desc: "Description",
          note: "The file goes directly to Cloudflare R2 (private bucket). Large files are uploaded in parts – keep this tab open until it finishes.",
          save: "Upload", cancel: "Cancel", files: "Files", loading: "Loading…", empty: "No files yet.", download: "Download",
          delete: "Delete", confirm: "Delete this file permanently?", nofile: "Please choose a file.", done: "Done", err: "Error",
          prep: "Preparing…", finishing: "Finishing…", unfinished: "incomplete", total: "files", nodesc: "No description.", leave: "Upload in progress – leave anyway?" },
    ru: { s3: "Загружено S3-инструментом (aws s3 / rclone), без описания:", upload: "+ Загрузить", up_title: "Новый файл", f_title: "Заголовок", drop: "Выберите файл или перетащите сюда", f_desc: "Описание",
          note: "Файл идёт напрямую в Cloudflare R2 (приватный bucket). Большие файлы грузятся частями – не закрывайте вкладку до конца.",
          save: "Загрузить", cancel: "Отмена", files: "Файлы", loading: "Загрузка…", empty: "Файлов пока нет.", download: "Скачать",
          delete: "Удалить", confirm: "Удалить этот файл навсегда?", nofile: "Выберите файл.", done: "Готово", err: "Ошибка",
          prep: "Подготовка…", finishing: "Завершение…", unfinished: "не догружен", total: "файлов", nodesc: "Без описания.", leave: "Идёт загрузка – всё равно уйти?" },
    uk: { s3: "Завантажено S3-інструментом (aws s3 / rclone), без опису:", upload: "+ Завантажити", up_title: "Новий файл", f_title: "Заголовок", drop: "Виберіть файл або перетягніть сюди", f_desc: "Опис",
          note: "Файл іде напряму в Cloudflare R2 (приватний bucket). Великі файли вантажаться частинами – не закривайте вкладку до кінця.",
          save: "Завантажити", cancel: "Скасувати", files: "Файли", loading: "Завантаження…", empty: "Файлів поки немає.", download: "Завантажити файл",
          delete: "Видалити", confirm: "Видалити цей файл назавжди?", nofile: "Виберіть файл.", done: "Готово", err: "Помилка",
          prep: "Підготовка…", finishing: "Завершення…", unfinished: "не довантажено", total: "файлів", nodesc: "Без опису.", leave: "Йде завантаження – все одно піти?" },
  };
  var FLAG = { de: "de", en: "gb", ru: "ru", uk: "ua" };
  var saved = ""; try { saved = localStorage.getItem("st-lang") || ""; } catch (e) {}
  var lang = L[saved] ? saved : (navigator.language || "en").slice(0, 2).toLowerCase();
  if (!L[lang]) lang = "en";
  var T = L[lang];
  document.documentElement.lang = lang;
  function $(id) { return document.getElementById(id); }
  function el(tag, cls, text) { var e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; }

  var bar = document.querySelector(".st-actions");
  var sw = el("nav", "langs st-langs"); sw.setAttribute("aria-label", "Language");
  Object.keys(L).forEach(function (k) {
    var a = el("a"); a.href = "#"; a.lang = k; a.title = k.toUpperCase();
    var fl = el("img", "flag"); fl.alt = ""; fl.width = 20; fl.height = 14; fl.src = "/assets/flags/" + FLAG[k] + ".svg";
    a.appendChild(fl); a.appendChild(el("span", "lc", k.toUpperCase()));
    if (k === lang) a.setAttribute("aria-current", "true");
    a.addEventListener("click", function (ev) { ev.preventDefault(); try { localStorage.setItem("st-lang", k); } catch (e) {} location.reload(); });
    sw.appendChild(a);
  });
  bar.insertBefore(sw, bar.firstChild);
  document.querySelectorAll("[data-t]").forEach(function (e) { if (T[e.dataset.t]) e.textContent = T[e.dataset.t]; });

  function size(n) {
    var u = ["B", "KB", "MB", "GB", "TB"], i = 0;
    while (n >= 1024 && i < u.length - 1) { n /= 1024; i++; }
    return (i ? n.toFixed(n < 10 ? 2 : 1) : n) + " " + u[i];
  }
  function fmt(ts) { try { return new Date(ts).toLocaleString(lang); } catch (e) { return ""; } }
  function api(path, opt) {
    return fetch("/backup/api/" + path, opt).then(function (r) {
      return r.json().catch(function () { return {}; }).then(function (d) { if (!r.ok) throw new Error(d.error || ("HTTP " + r.status)); return d; });
    });
  }
  function post(path, body) { return api(path, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) }); }

  // ---------------- list
  var open = location.hash.slice(1);
  function load() {
    api("list").then(function (d) {
      var ul = $("bk-list"); ul.textContent = "";
      var total = 0;
      d.items = d.items.concat(d.ext || []);
      d.items.forEach(function (it) { if (it.state === "ok") total += it.size || 0; });
      $("bk-sum").textContent = d.items.length ? d.items.length + " " + T.total + " · " + size(total) : "";
      if (!d.items.length) { ul.appendChild(el("li", "st-empty", T.empty)); return; }
      d.items.forEach(function (it) {
        var li = el("li", "bk-item" + (it.state !== "ok" ? " bk-bad" : "")); li.id = it.id || "";
        var head = el("button", "bk-head"); head.type = "button"; head.setAttribute("aria-expanded", "false");
        head.appendChild(el("b", "", it.title || it.name));
        head.appendChild(el("span", "bk-sz", it.state === "ok" ? size(it.size) : "⚠ " + T.unfinished));
        head.appendChild(el("small", "", (it.ext ? "S3 · " : "") + it.name + " · " + fmt(it.created) + (it.user ? " · " + it.user : "")));
        var body = el("div", "bk-body"); body.hidden = true;
        body.appendChild(el("pre", "st-log", it.ext ? T.s3 + "\n" + it.key : (it.desc || T.nodesc)));
        var btns = el("div", "bk-btns");
        if (it.state === "ok") {
          var dl = el("a", "btn primary small", "⬇ " + T.download); dl.href = it.ext ? "/backup/api/xdl?key=" + encodeURIComponent(it.key) : "/backup/api/dl/" + it.id; dl.rel = "noreferrer";
          btns.appendChild(dl);
        }
        var del = el("button", "st-btn danger", T.delete); del.type = "button";
        del.addEventListener("click", function () {
          if (!confirm(T.confirm + "\n\n" + (it.title || it.name))) return;
          api(it.ext ? "xitem?key=" + encodeURIComponent(it.key) : "item/" + it.id, { method: "DELETE" }).then(load).catch(function (e) { alert(T.err + ": " + e.message); });
        });
        btns.appendChild(del);
        body.appendChild(btns);
        head.addEventListener("click", function () {
          body.hidden = !body.hidden; head.setAttribute("aria-expanded", String(!body.hidden));
          if (!body.hidden && it.id) history.replaceState(null, "", "#" + it.id);
        });
        if (it.id && open === it.id) { body.hidden = false; head.setAttribute("aria-expanded", "true"); }
        li.appendChild(head); li.appendChild(body); ul.appendChild(li);
      });
    }).catch(function (e) { $("bk-list").textContent = T.err + ": " + e.message; });
  }
  load();

  // ---------------- upload
  var form = $("bk-form"), file = null, busy = false, aborter = null;
  $("bk-new").addEventListener("click", function () { form.hidden = false; $("bk-title").focus(); });
  $("bk-cancel").addEventListener("click", function () {
    if (busy) { if (aborter) aborter(); return; }
    form.hidden = true;
  });
  function pick(f) { if (!f) return; file = f; $("bk-fname").textContent = f.name + " · " + size(f.size); if (!$("bk-title").value) $("bk-title").value = f.name; }
  $("bk-file").addEventListener("change", function () { pick(this.files[0]); });
  var drop = $("bk-drop");
  ["dragenter", "dragover"].forEach(function (t) { drop.addEventListener(t, function (e) { e.preventDefault(); drop.classList.add("over"); }); });
  ["dragleave", "drop"].forEach(function (t) { drop.addEventListener(t, function (e) { e.preventDefault(); drop.classList.remove("over"); }); });
  drop.addEventListener("drop", function (e) { if (e.dataTransfer.files[0]) pick(e.dataTransfer.files[0]); });
  window.addEventListener("beforeunload", function (e) { if (busy) { e.preventDefault(); e.returnValue = T.leave; return T.leave; } });

  function putPart(url, blob, onProgress, xhrs) {
    return new Promise(function (ok, fail) {
      var x = new XMLHttpRequest(); xhrs.push(x);
      x.open("PUT", url);
      x.upload.onprogress = function (e) { onProgress(e.loaded); };
      x.onload = function () {
        var et = x.getResponseHeader("ETag");
        if (x.status >= 200 && x.status < 300 && et) ok(et); else fail(new Error("part HTTP " + x.status + (et ? "" : " (no ETag)")));
      };
      x.onerror = function () { fail(new Error("network")); };
      x.onabort = function () { fail(new Error("cancelled")); };
      x.send(blob);
    });
  }

  form.addEventListener("submit", function (ev) {
    ev.preventDefault();
    if (busy) return;
    if (!file) { $("bk-prog").textContent = T.nofile; return; }
    busy = true; $("bk-save").disabled = true;
    var prog = $("bk-prog"), fill = $("bk-fill"); $("bk-bar").hidden = false; fill.style.width = "0";
    prog.textContent = T.prep;
    var id, partSize, count, done = {}, loaded = {}, etags = [], xhrs = [], cancelled = false, t0 = Date.now();
    aborter = function () { cancelled = true; xhrs.forEach(function (x) { try { x.abort(); } catch (e) {} }); };
    function show() {
      var sum = 0; for (var k in loaded) sum += loaded[k];
      var pct = file.size ? Math.min(100, sum / file.size * 100) : 100;
      var sec = (Date.now() - t0) / 1000, speed = sec > 1 ? sum / sec : 0;
      fill.style.width = pct.toFixed(1) + "%";
      prog.textContent = pct.toFixed(1) + " % · " + size(sum) + " / " + size(file.size) + (speed ? " · " + size(speed) + "/s" : "");
    }
    function one(n) {
      var start = (n - 1) * partSize, blob = file.slice(start, Math.min(file.size, start + partSize));
      var tries = 0;
      function attempt() {
        if (cancelled) return Promise.reject(new Error("cancelled"));
        return post("parts", { id: id, ns: [n] }).then(function (d) {
          return putPart(d.urls[n], blob, function (b) { loaded[n] = b; show(); }, xhrs);
        }).then(function (et) { etags.push({ n: n, etag: et }); loaded[n] = blob.size; show(); }, function (e) {
          if (cancelled || ++tries >= 4) throw e;
          loaded[n] = 0;
          return new Promise(function (r) { setTimeout(r, 1500 * tries); }).then(attempt);
        });
      }
      return attempt();
    }
    post("init", { title: $("bk-title").value, desc: $("bk-desc").value, name: file.name, size: file.size, type: file.type })
      .then(function (d) {
        id = d.id; partSize = d.partSize; count = Math.max(1, Math.ceil(file.size / partSize));
        var next = 1;
        function worker() { if (next > count) return Promise.resolve(); var n = next++; return one(n).then(worker); }
        var ws = []; for (var i = 0; i < Math.min(4, count); i++) ws.push(worker());
        return Promise.all(ws);
      })
      .then(function () { prog.textContent = T.finishing; return post("complete", { id: id, parts: etags }); })
      .then(function () {
        prog.textContent = "✓ " + T.done + " · " + size(file.size);
        busy = false; file = null; form.reset(); $("bk-fname").textContent = ""; $("bk-save").disabled = false;
        open = id; load();
      })
      .catch(function (e) {
        busy = false; $("bk-save").disabled = false; aborter();
        prog.textContent = "✗ " + T.err + ": " + e.message;
        if (id) post("abort", { id: id }).catch(function () {});
      });
  });
})();
