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
