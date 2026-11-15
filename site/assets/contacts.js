(function () {
  var s = atob("==AUFdUUaZFXfR1XYVlVZg0FIwUBb0UXNtBHKkFOCUxAXghDPgRTI10QCUxCLIAAKMQAGczTYElQUVlRW1kHbYwBNFQRFFlQBMPrG0xG380XCAABP0QC4UUVNBhCIVhBWAESOp1UX1FVf5xVFR1WQNkCKEkDTAkAdFQFWABBN1VTfQhDeNxENUhRA1kUbdlVf1BVSVVVVxkVTRUTe1EVG4RFR0ACwIQAAwwHPsEUQZFXe91Vc91UeRxUZdEWGlQAIcwHGN0DK0hBMhQBOoACvIhCFRQARMQDIAwFL0kXNFkDTgwBGBUTRowBH4AVD0RFiYkVNJwALogDFhzHEAxAJMgAb0ESNtlAaYwAdgAAXAkCJEUWI11XRQBGb8QTVZkAMVRFA4QAY0EH".split("").reverse().join("")), k = "goldberg-odoo", b = new Uint8Array(s.length);
  for (var i = 0; i < s.length; i++) b[i] = s.charCodeAt(i) ^ k.charCodeAt(i % k.length);
  var C = JSON.parse(new TextDecoder().decode(b)); window.GC = C;
  function f(t) { return t.replace(/\{(\w+)\}/g, function (_, n) { return C[n] || ""; }); }
  function run() {
    document.querySelectorAll("[data-ch],[data-ct],[data-cx]").forEach(function (e) {
      var v = e.getAttribute("data-ch"); if (v) e.setAttribute("href", f(v));
      v = e.getAttribute("data-ct"); if (v) { e.title = f(v); e.setAttribute("aria-label", f(v)); }
      v = e.getAttribute("data-cx"); if (v) e.textContent = f(v);
    });
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", run); else run();
})();
