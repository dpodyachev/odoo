// /status/ viewer + /status/upload form. Data: /status/api/* (Pages Functions + KV), protected by Basic Auth.
(function () {
  var L = {
    de: { upload: "+ Hochladen", delete: "Löschen", loading: "Lädt…", empty: "Noch keine Einträge.", foot: "Einträge werden nach 30 Tagen automatisch gelöscht.",
          back: "← Übersicht", up_title: "Neuer Eintrag", drop: "Screenshot auswählen, hierher ziehen oder mit Strg+V einfügen", f_title: "Titel",
          f_text: "Log / Beschreibung", mask_note: "Passwörter, Tokens und Schlüssel im Text werden beim Speichern automatisch maskiert. Screenshots nicht – bitte selbst prüfen.",
          save: "Speichern", saving: "Speichere…", saved: "Gespeichert", masked: "maskiert", confirm: "Diesen Eintrag löschen?", noimg: "ohne Bild", open: "Original öffnen", err: "Fehler" },
    en: { upload: "+ Upload", delete: "Delete", loading: "Loading…", empty: "No entries yet.", foot: "Entries are deleted automatically after 30 days.",
          back: "← Overview", up_title: "New entry", drop: "Choose a screenshot, drop it here or paste it with Ctrl+V", f_title: "Title",
          f_text: "Log / description", mask_note: "Passwords, tokens and keys in the text are masked automatically when saving. Screenshots are not – check them yourself.",
          save: "Save", saving: "Saving…", saved: "Saved", masked: "masked", confirm: "Delete this entry?", noimg: "no image", open: "Open original", err: "Error" },
    ru: { upload: "+ Загрузить", delete: "Удалить", loading: "Загрузка…", empty: "Записей пока нет.", foot: "Записи удаляются автоматически через 30 дней.",
          back: "← Обзор", up_title: "Новая запись", drop: "Выберите скриншот, перетащите сюда или вставьте Ctrl+V", f_title: "Заголовок",
          f_text: "Лог / описание", mask_note: "Пароли, токены и ключи в тексте маскируются автоматически при сохранении. Скриншоты – нет, проверьте их сами.",
          save: "Сохранить", saving: "Сохраняю…", saved: "Сохранено", masked: "замаскировано", confirm: "Удалить эту запись?", noimg: "без картинки", open: "Открыть оригинал", err: "Ошибка" },
    uk: { upload: "+ Завантажити", delete: "Видалити", loading: "Завантаження…", empty: "Записів поки немає.", foot: "Записи видаляються автоматично через 30 днів.",
          back: "← Огляд", up_title: "Новий запис", drop: "Виберіть скриншот, перетягніть сюди або вставте Ctrl+V", f_title: "Заголовок",
          f_text: "Лог / опис", mask_note: "Паролі, токени й ключі в тексті маскуються автоматично під час збереження. Скриншоти – ні, перевірте їх самі.",
          save: "Зберегти", saving: "Зберігаю…", saved: "Збережено", masked: "замасковано", confirm: "Видалити цей запис?", noimg: "без картинки", open: "Відкрити оригінал", err: "Помилка" },
  };
  var lang = (navigator.language || "en").slice(0, 2).toLowerCase();
  var T = L[lang] || L.en;
  document.documentElement.lang = L[lang] ? lang : "en";
  document.querySelectorAll("[data-t]").forEach(function (el) { if (T[el.dataset.t]) el.textContent = T[el.dataset.t]; });
  function $(id) { return document.getElementById(id); }
  function fmt(ts) { try { return new Date(ts).toLocaleString(lang); } catch (e) { return ""; } }

  // ---------------- viewer
  if (document.querySelector("[data-view]")) {
    var items = [], cur = -1, cache = {};
    function render() {
      $("st-count").textContent = items.length ? (cur + 1) + " / " + items.length : "0";
      $("st-prev").disabled = $("st-next").disabled = items.length < 2;
      $("st-del").hidden = !items.length;
      document.querySelectorAll(".st-list a").forEach(function (a, i) { a.classList.toggle("on", i === cur); if (i === cur) a.scrollIntoView({ block: "nearest", inline: "nearest" }); });
      if (!items.length) { $("st-img").innerHTML = '<p class="st-empty">' + T.empty + "</p>"; $("st-title").textContent = ""; $("st-meta").textContent = ""; $("st-log").textContent = ""; return; }
      var it = items[cur];
      $("st-title").textContent = it.title || "–";
      $("st-meta").textContent = fmt(it.created) + (it.user ? " · " + it.user : "") + (it.masked ? " · 🔒 " + it.masked + " " + T.masked : "");
      if (it.img) {
        var src = "/status/api/img/" + it.id;
        $("st-img").innerHTML = '<a href="' + src + '" target="_blank" rel="noopener" title="' + T.open + '"><img alt="" src="' + src + '"></a>';
      } else { $("st-img").innerHTML = '<p class="st-empty">' + T.noimg + "</p>"; }
      $("st-log").textContent = cache[it.id] !== undefined ? cache[it.id] : T.loading;
      if (cache[it.id] === undefined) {
        var want = it.id;
        fetch("/status/api/item/" + it.id).then(function (r) { return r.json(); }).then(function (d) {
          cache[want] = d.text || ""; if (items[cur] && items[cur].id === want) $("st-log").textContent = cache[want];
        });
      }
      if (location.hash !== "#" + it.id) history.replaceState(null, "", "#" + it.id);
    }
    function go(i) { if (!items.length) return; cur = (i + items.length) % items.length; render(); }
    function list() {
      $("st-list").innerHTML = items.map(function (it, i) {
        return '<a href="#' + it.id + '" data-i="' + i + '"><b></b><small>' + fmt(it.created) + "</small></a>";
      }).join("");
      document.querySelectorAll(".st-list a").forEach(function (a, i) {
        a.querySelector("b").textContent = (items[i].img ? "🖼 " : "📝 ") + (items[i].title || "–");
        a.addEventListener("click", function (e) { e.preventDefault(); go(i); });
      });
    }
    function load() {
      fetch("/status/api/list").then(function (r) { return r.json(); }).then(function (d) {
        items = Array.isArray(d) ? d : []; list();
        var h = location.hash.slice(1), k = items.findIndex(function (x) { return x.id === h; });
        cur = k >= 0 ? k : (items.length ? 0 : -1); render();
      }).catch(function () { $("st-img").innerHTML = '<p class="st-empty">' + T.err + "</p>"; });
    }
    $("st-prev").addEventListener("click", function () { go(cur - 1); });
    $("st-next").addEventListener("click", function () { go(cur + 1); });
    document.addEventListener("keydown", function (e) {
      if (/INPUT|TEXTAREA/.test(document.activeElement.tagName)) return;
      if (e.key === "ArrowLeft") go(cur - 1); else if (e.key === "ArrowRight") go(cur + 1);
    });
    window.addEventListener("hashchange", function () {
      var k = items.findIndex(function (x) { return "#" + x.id === location.hash; }); if (k >= 0 && k !== cur) go(k);
    });
    $("st-del").addEventListener("click", function () {
      if (!items.length || !confirm(T.confirm)) return;
      fetch("/status/api/item/" + items[cur].id, { method: "DELETE" }).then(function () {
        items.splice(cur, 1); if (cur >= items.length) cur = items.length - 1; list(); render();
      });
    });
    load();
  }

  // ---------------- upload
  if (document.querySelector("[data-upload]")) {
    var file = null, drop = $("st-drop");
    function setFile(f) {
      if (!f || !/^image\//.test(f.type)) return;
      file = f;
      var r = new FileReader();
      r.onload = function () { $("st-preview").src = r.result; $("st-preview").hidden = false; };
      r.readAsDataURL(f);
      if (!$("st-title-in").value) $("st-title-in").value = f.name && f.name !== "image.png" ? f.name.replace(/\.[a-z]+$/i, "") : "";
    }
    $("st-file").addEventListener("change", function () { setFile(this.files[0]); });
    ["dragover", "dragenter"].forEach(function (ev) { drop.addEventListener(ev, function (e) { e.preventDefault(); drop.classList.add("over"); }); });
    ["dragleave", "drop"].forEach(function (ev) { drop.addEventListener(ev, function () { drop.classList.remove("over"); }); });
    drop.addEventListener("drop", function (e) { e.preventDefault(); setFile(e.dataTransfer.files[0]); });
    document.addEventListener("paste", function (e) {
      var it = [].slice.call((e.clipboardData || {}).items || []).find(function (x) { return x.kind === "file" && /^image\//.test(x.type); });
      if (it) { e.preventDefault(); setFile(it.getAsFile()); }
    });
    $("st-form").addEventListener("submit", function (e) {
      e.preventDefault();
      var fd = new FormData();
      if (file) fd.append("file", file, file.name || "screenshot.png");
      fd.append("title", $("st-title-in").value);
      fd.append("text", $("st-text-in").value);
      $("st-save").disabled = true; $("st-result").textContent = T.saving;
      fetch("/status/api/upload", { method: "POST", body: fd }).then(function (r) { return r.json(); }).then(function (d) {
        $("st-save").disabled = false;
        if (!d.ok) { $("st-result").textContent = T.err + ": " + (d.error || ""); return; }
        location.href = "/status/#" + d.id;
      }).catch(function () { $("st-save").disabled = false; $("st-result").textContent = T.err; });
    });
  }
})();
