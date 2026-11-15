// Выбор языка по настройкам браузера; по умолчанию — de. Ничего не сохраняет (без cookies/localStorage).
// Файл генерируется src/build.py из config.LANGS.
(function () {
  var supported = ["de", "en", "fr", "el", "uk", "ru"], pick = "de";
  var list = navigator.languages || [navigator.language || ""];
  for (var i = 0; i < list.length; i++) {
    var l = String(list[i]).toLowerCase().slice(0, 2);
    if (l === "ua") l = "uk";
    if (supported.indexOf(l) >= 0) { pick = l; break; }
  }
  location.replace("/test/" + pick + "/");
})();
