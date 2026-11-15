// /status/* – Basic Auth for several users (secret STATUS_USERS = "user:pass" per line).
// Exception: the Telegram webhook, which proves itself with the secret header instead.
import { users, same } from "../../lib/status.js";

function decode(b64) {
  try {
    const bin = atob(b64);
    return new TextDecoder().decode(Uint8Array.from(bin, (c) => c.charCodeAt(0)));
  } catch { return ""; }
}

function harden(res) {
  const out = new Response(res.body, res);
  out.headers.set("Cache-Control", "no-store, private");
  out.headers.set("X-Robots-Tag", "noindex, nofollow");
  out.headers.set("Referrer-Policy", "no-referrer");
  return out;
}

export async function onRequest(ctx) {
  const { request, env, next, data } = ctx;
  const path = new URL(request.url).pathname;

  if (path === "/status/api/telegram") {
    const got = request.headers.get("X-Telegram-Bot-Api-Secret-Token") || "";
    const want = env.STATUS_TG_SECRET || "";
    if (request.method === "POST" && want && same(got, want)) return next();
    return new Response("forbidden", { status: 403 });
  }

  const h = request.headers.get("Authorization") || "";
  if (h.startsWith("Basic ")) {
    const pair = decode(h.slice(6).trim());
    for (const u of users(env)) {
      if (same(pair, u)) { data.user = u.split(":")[0]; return harden(await next()); }
    }
  }
  return new Response("401 – Anmeldung erforderlich / Authentication required\n", {
    status: 401,
    headers: { "WWW-Authenticate": 'Basic realm="Goldberg status", charset="UTF-8"', "Cache-Control": "no-store",
               "Content-Type": "text/plain; charset=utf-8" },
  });
}
