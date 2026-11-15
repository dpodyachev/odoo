// Basic Auth для /test/* на Cloudflare Pages (Pages Functions).
// Логин и пароль НЕ в репозитории: секрет TEST_AUTH = "login:password" задан в Cloudflare
// (wrangler pages secret put TEST_AUTH --project-name goldberg-odoo). Нет секрета — доступ закрыт.

function same(a, b) {               // сравнение без утечки по времени
  if (a.length !== b.length) return false;
  let d = 0;
  for (let i = 0; i < a.length; i++) d |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return d === 0;
}

function decode(b64) {              // base64 → UTF-8 строка
  try {
    const bin = atob(b64);
    return new TextDecoder().decode(Uint8Array.from(bin, (c) => c.charCodeAt(0)));
  } catch { return ""; }
}

export async function onRequest({ request, env, next }) {
  const expected = env.TEST_AUTH || "";
  const h = request.headers.get("Authorization") || "";
  if (expected && h.startsWith("Basic ") && same(decode(h.slice(6).trim()), expected)) {
    const res = await next();
    const out = new Response(res.body, res);
    out.headers.set("Cache-Control", "no-store");
    out.headers.set("X-Robots-Tag", "noindex, nofollow");
    return out;
  }
  return new Response("401 – Anmeldung erforderlich / Authentication required\n", {
    status: 401,
    headers: {
      "WWW-Authenticate": 'Basic realm="Goldberg test area", charset="UTF-8"',
      "Cache-Control": "no-store",
      "Content-Type": "text/plain; charset=utf-8",
    },
  });
}
