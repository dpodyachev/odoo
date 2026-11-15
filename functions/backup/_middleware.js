// /backup/* – Basic Auth (secret BACKUP_USERS = "user:pass" per line or comma).
// The browser uploads/downloads directly to/from R2 with pre-signed URLs, so CSP must allow the R2 host.
import { same } from "../../lib/status.js";

function decode(b64) {
  try {
    const bin = atob(b64);
    return new TextDecoder().decode(Uint8Array.from(bin, (c) => c.charCodeAt(0)));
  } catch { return ""; }
}

export async function onRequest(ctx) {
  const { request, env, next, data } = ctx;
  const list = String(env.BACKUP_USERS || "").split(/[\n,]+/).map((s) => s.trim()).filter((s) => s.includes(":"));
  const h = request.headers.get("Authorization") || "";
  if (h.startsWith("Basic ")) {
    const pair = decode(h.slice(6).trim());
    for (const u of list) {
      if (same(pair, u)) {
        data.user = u.split(":")[0];
        const res = await next();
        const out = new Response(res.body, res);
        out.headers.set("Cache-Control", "no-store, private");
        out.headers.set("X-Robots-Tag", "noindex, nofollow");
        out.headers.set("Referrer-Policy", "no-referrer");
        out.headers.set("Content-Security-Policy",
          "default-src 'self'; img-src 'self' data:; style-src 'self'; script-src 'self'; " +
          `connect-src 'self' https://${env.R2_ACCOUNT_ID}.r2.cloudflarestorage.com; ` +
          "base-uri 'none'; form-action 'none'; frame-ancestors 'none'");
        return out;
      }
    }
  }
  return new Response("401 – Anmeldung erforderlich / Authentication required\n", {
    status: 401,
    headers: { "WWW-Authenticate": 'Basic realm="Goldberg backup", charset="UTF-8"', "Cache-Control": "no-store",
               "Content-Type": "text/plain; charset=utf-8" },
  });
}
