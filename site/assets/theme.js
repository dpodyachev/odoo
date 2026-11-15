// Кнопка ☀️/🌙: переключает светлую/тёмную тему на текущей странице. Выбор не сохраняется (без cookies/localStorage).
(function () {
  var root = document.documentElement, mq = window.matchMedia("(prefers-color-scheme: dark)");
  document.querySelectorAll(".theme").forEach(function (btn) {
    function cur() { return root.dataset.theme || (mq.matches ? "dark" : "light"); }
    function paint() { var d = cur() === "dark"; btn.textContent = d ? "☀️" : "🌙"; btn.setAttribute("aria-pressed", d ? "true" : "false"); }
    btn.addEventListener("click", function () { root.dataset.theme = cur() === "dark" ? "light" : "dark"; paint(); });
    if (mq.addEventListener) mq.addEventListener("change", paint);
    paint(); btn.hidden = false;
  });
})();

// Переключатель языков: остаёмся в том же разделе (#loadtest и т. п.). Берём #hash из адреса,
// а если его нет — раздел, который сейчас на экране. id разделов одинаковы во всех языках.
(function () {
  function here() {
    var best = "";
    document.querySelectorAll("main section[id], section[id]").forEach(function (s) {
      if (s.getBoundingClientRect().top <= 120) best = s.id;
    });
    return best && window.scrollY > 200 ? "#" + best : "";
  }
  document.querySelectorAll(".langs a").forEach(function (a) {
    a.addEventListener("click", function () {
      var h = location.hash || here();
      if (h) a.href = a.href.split("#")[0] + h;
    });
  });
})();
