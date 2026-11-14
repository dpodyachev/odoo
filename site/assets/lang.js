// Выбор языка по настройкам браузера; по умолчанию — немецкий. Ничего не сохраняет (без cookies/localStorage).
(function () {
  var supported = ["de", "en", "fr", "uk", "ru"], pick = "de";
  var list = navigator.languages || [navigator.language || ""];
  for (var i = 0; i < list.length; i++) {
    var l = String(list[i]).toLowerCase().slice(0, 2);
    if (l === "ua") l = "uk";
    if (supported.indexOf(l) >= 0) { pick = l; break; }
  }
  location.replace("/" + pick + "/" + location.hash);
})();
