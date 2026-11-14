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
    imgs[1].loading = "eager";
    start();
  });
})();
