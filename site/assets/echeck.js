// E-Rechnung-Check: считает результат в браузере. Ничего не сохраняет и не отправляет —
// посетитель сам выбирает: Cal.com (ответы в заметке), письмо (mailto) или Telegram (текст копируется в буфер).
(function () {
  document.querySelectorAll(".echeck").forEach(function (form) {
    var sec = form.closest("section"), D = JSON.parse(sec.querySelector(".ec-data").textContent);
    var res = sec.querySelector(".ec-result"), err = sec.querySelector(".ec-err"), summary = "";
    function fmt(s, v) { return s.replace("{s}", v); }
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      var total = 0, lines = [], todo = [], missing = false;
      D.q.forEach(function (q, i) {
        var c = form.querySelector('input[name="q' + (i + 1) + '"]:checked');
        if (!c) { missing = true; return; }
        var v = +c.value; total += v;
        lines.push((i + 1) + ". " + q[0] + ": " + D.answers[2 - v]);
        if (v < 2) todo.push(q);
      });
      err.hidden = !missing;
      if (missing) return;
      var lvl = D.levels[total <= 4 ? 0 : total <= 8 ? 1 : 2];
      res.querySelector(".ec-score").textContent = fmt(D.score, total);
      res.querySelector(".ec-level").textContent = lvl[0];
      res.querySelector(".ec-text").textContent = lvl[1];
      res.dataset.level = total <= 4 ? "low" : total <= 8 ? "mid" : "high";
      var ul = res.querySelector(".ec-todo ul"); ul.textContent = "";
      todo.forEach(function (q) { var li = document.createElement("li"), b = document.createElement("b");
        b.textContent = q[0] + ": "; li.appendChild(b); li.appendChild(document.createTextNode(q[1])); ul.appendChild(li); });
      res.querySelector(".ec-todo").hidden = !todo.length;
      summary = D.title + ": " + total + "/10\n" + lines.join("\n");
      var sep = D.cal.indexOf("?") < 0 ? "?" : "&";
      res.querySelector(".ec-book").href = D.cal + sep + "notes=" + encodeURIComponent(summary);
      res.querySelector(".ec-mail").href = "mailto:" + ((window.GC || {}).email || "") + "?subject=" + encodeURIComponent(fmt(D.mail_subject, total)) +
        "&body=" + encodeURIComponent(D.mail_intro + "\n\n" + summary + "\n\n" + D.mail_outro + "\n");
      res.hidden = false; res.focus({ preventScroll: true });
      res.scrollIntoView({ behavior: "smooth", block: "start" });
    });
    sec.querySelector(".ec-tg").addEventListener("click", function () {
      if (!summary || !navigator.clipboard) return;
      navigator.clipboard.writeText(summary).then(function () { sec.querySelector(".ec-copied").hidden = false; }, function () {});
    });
  });
})();
