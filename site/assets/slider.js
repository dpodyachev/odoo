// Карусель примеров: смена слайда каждые data-interval мс, пауза при наведении/фокусе и на скрытой вкладке.
(function () {
  document.querySelectorAll(".slider").forEach(function (root) {
    var imgs = root.querySelectorAll(".slides img"), dots = root.querySelectorAll(".sl-dots button");
    var n = imgs.length, cur = 0, timer = null, ms = +root.dataset.interval || 5000, paused = false;
    if (n < 2) { root.querySelectorAll("button").forEach(function (b) { b.hidden = true; }); return; }
    function show(i) {
      imgs[cur].classList.remove("on"); dots[cur].removeAttribute("aria-current");
      cur = (i + n) % n;
      imgs[cur].classList.add("on"); dots[cur].setAttribute("aria-current", "true");
      var next = imgs[(cur + 1) % n]; if (next.loading === "lazy") next.loading = "eager";
    }
    function start() { stop(); if (!paused && !document.hidden) timer = setInterval(function () { show(cur + 1); }, ms); }
    function stop() { if (timer) clearInterval(timer); timer = null; }
    root.querySelector(".sl-prev").addEventListener("click", function () { show(cur - 1); start(); });
    root.querySelector(".sl-next").addEventListener("click", function () { show(cur + 1); start(); });
    dots.forEach(function (d, i) { d.addEventListener("click", function () { show(i); start(); }); });
    root.addEventListener("pointerenter", function (e) { if (e.pointerType === "mouse") { paused = true; stop(); } });
    root.addEventListener("pointerleave", function (e) { if (e.pointerType === "mouse") { paused = false; start(); } });
    root.addEventListener("focusin", function () { paused = true; stop(); });
    root.addEventListener("focusout", function () { paused = false; start(); });
    document.addEventListener("visibilitychange", start);
    root.addEventListener("lb:open", function () { paused = true; stop(); });
    root.addEventListener("lb:close", function () { paused = false; start(); });
    imgs[1].loading = "eager";
    start();
  });
})();

// Полноэкранный просмотр: клик по слайду → весь экран; ←/→ и свайп — листать; +/−, колесо, щипок, двойной клик — зум;
// при зуме изображение двигается мышью/пальцем; Esc, ✕ или клик по фону — выход.
(function () {
  // .slider — карусель; .lb-group — набор картинок-кнопок (напр. скриншоты Locust), тот же просмотр
  document.querySelectorAll(".slider, .lb-group").forEach(function (root) {
    var isSlider = root.classList.contains("slider");
    var imgs = [].slice.call(root.querySelectorAll(isSlider ? ".slides img" : "img")), n = imgs.length, d = root.dataset;
    if (!n) return;
    var lb = document.createElement("div");
    lb.className = "lb"; lb.hidden = true;
    lb.setAttribute("role", "dialog"); lb.setAttribute("aria-modal", "true"); lb.setAttribute("aria-label", d.lFull || "");
    lb.innerHTML = '<div class="lb-stage"><img class="lb-img" alt=""></div>' +
      '<div class="lb-bar"><span class="lb-count"></span>' +
      '<button type="button" class="lb-out">−</button><button type="button" class="lb-in">+</button>' +
      '<button type="button" class="lb-x">✕</button></div>' +
      '<button type="button" class="lb-prev">‹</button><button type="button" class="lb-next">›</button>';
    document.body.appendChild(lb);
    var q = function (s) { return lb.querySelector(s); }, img = q(".lb-img"), stage = q(".lb-stage");
    [[".lb-x", d.lClose], [".lb-in", d.lIn], [".lb-out", d.lOut], [".lb-prev", d.lPrev], [".lb-next", d.lNext]].forEach(function (p) {
      q(p[0]).setAttribute("aria-label", p[1] || ""); q(p[0]).title = p[1] || ""; });
    if (n < 2) { q(".lb-prev").hidden = q(".lb-next").hidden = true; }
    var i = 0, s = 1, tx = 0, ty = 0, back = null, ptrs = {}, start = null, moved = false, downOnBg = false;
    function apply() {
      var r = stage.getBoundingClientRect(), mx = Math.max(0, (img.offsetWidth * s - r.width) / 2), my = Math.max(0, (img.offsetHeight * s - r.height) / 2);
      tx = Math.max(-mx, Math.min(mx, tx)); ty = Math.max(-my, Math.min(my, ty));
      img.style.transform = "translate(" + tx + "px," + ty + "px) scale(" + s + ")";
      lb.classList.toggle("zoomed", s > 1.01);
    }
    function zoom(f) { var ns = Math.max(1, Math.min(6, s * f)); tx *= ns / s; ty *= ns / s; s = ns; if (s === 1) { tx = ty = 0; } apply(); }
    function show(k) {
      i = (k + n) % n; s = 1; tx = ty = 0;
      img.src = imgs[i].getAttribute("src"); img.alt = imgs[i].alt;
      q(".lb-count").textContent = (i + 1) + " / " + n; apply();
    }
    function open(k) {
      back = document.activeElement; root.dispatchEvent(new CustomEvent("lb:open"));
      lb.hidden = false; document.documentElement.classList.add("lb-open"); show(k); q(".lb-x").focus();
    }
    function close() {
      lb.hidden = true; document.documentElement.classList.remove("lb-open"); root.dispatchEvent(new CustomEvent("lb:close"));
      if (back && back.focus) back.focus();
    }
    if (isSlider) root.querySelector(".slides").addEventListener("click", function () {
      var on = imgs.findIndex(function (x) { return x.classList.contains("on"); }); open(on < 0 ? 0 : on); });
    else imgs.forEach(function (x, k) { (x.closest("button") || x).addEventListener("click", function () { open(k); }); });
    q(".lb-x").addEventListener("click", close);
    q(".lb-in").addEventListener("click", function () { zoom(1.5); });
    q(".lb-out").addEventListener("click", function () { zoom(1 / 1.5); });
    q(".lb-prev").addEventListener("click", function () { show(i - 1); });
    q(".lb-next").addEventListener("click", function () { show(i + 1); });
    document.addEventListener("keydown", function (e) {
      if (lb.hidden) return;
      if (e.key === "Escape") close();
      else if (e.key === "ArrowLeft") show(i - 1);
      else if (e.key === "ArrowRight") show(i + 1);
      else if (e.key === "+" || e.key === "=") zoom(1.5);
      else if (e.key === "-" || e.key === "_") zoom(1 / 1.5);
      else if (e.key === "Tab") { // фокус остаётся внутри окна
        var f = [].slice.call(lb.querySelectorAll("button:not([hidden])")), a = f.indexOf(document.activeElement);
        e.preventDefault(); f[(a + (e.shiftKey ? -1 : 1) + f.length) % f.length].focus();
      } else return;
      e.preventDefault();
    });
    stage.addEventListener("wheel", function (e) { e.preventDefault(); zoom(e.deltaY < 0 ? 1.2 : 1 / 1.2); }, { passive: false });
    img.addEventListener("dblclick", function () { if (s > 1.01) { s = 1; tx = ty = 0; apply(); } else zoom(2.5); });
    img.addEventListener("load", apply);
    window.addEventListener("resize", function () { if (!lb.hidden) apply(); });
    function dist() { var p = Object.keys(ptrs).map(function (k) { return ptrs[k]; }); return Math.hypot(p[0].x - p[1].x, p[0].y - p[1].y); }
    stage.addEventListener("pointerdown", function (e) {
      if (!Object.keys(ptrs).length) downOnBg = e.target === stage;
      ptrs[e.pointerId] = { x: e.clientX, y: e.clientY }; if (stage.setPointerCapture) stage.setPointerCapture(e.pointerId); moved = false;
      start = Object.keys(ptrs).length === 2 ? { pinch: dist(), s: s } : { x: e.clientX, y: e.clientY, tx: tx, ty: ty };
    });
    stage.addEventListener("pointermove", function (e) {
      if (!ptrs[e.pointerId] || !start) return;
      ptrs[e.pointerId] = { x: e.clientX, y: e.clientY };
      if (start.pinch) { var ns = Math.max(1, Math.min(6, start.s * dist() / start.pinch)); tx *= ns / s; ty *= ns / s; s = ns; apply(); moved = true; return; }
      var dx = e.clientX - start.x, dy = e.clientY - start.y;
      if (Math.abs(dx) + Math.abs(dy) > 6) moved = true;
      if (s > 1.01) { tx = start.tx + dx; ty = start.ty + dy; apply(); }
    });
    function up(e) {
      if (!ptrs[e.pointerId]) return;
      var dx = start && !start.pinch ? e.clientX - start.x : 0, dy = start && !start.pinch ? e.clientY - start.y : 0;
      delete ptrs[e.pointerId];
      if (Object.keys(ptrs).length) { var k = Object.keys(ptrs)[0]; start = { x: ptrs[k].x, y: ptrs[k].y, tx: tx, ty: ty }; return; }
      if (start && !start.pinch && s <= 1.01 && Math.abs(dx) > 50 && Math.abs(dx) > Math.abs(dy)) show(i + (dx < 0 ? 1 : -1));
      else if (!moved && downOnBg) close(); // клик по тёмному фону
      start = null;
    }
    stage.addEventListener("pointerup", up); stage.addEventListener("pointercancel", up);
  });
})();
