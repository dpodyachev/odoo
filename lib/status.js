// Shared helpers for /status/* (Cloudflare Pages Functions + Workers KV).
// Storage: KV namespace bound as STATUS_KV. Every key expires after TTL seconds (KV removes it itself).
//   meta:<id>  value "" + metadata {t,c,u,m,s}   – list without extra reads
//   text:<id>  log text (already masked)
//   img:<id>   image bytes (metadata {m: mime})

export const TTL = 30 * 24 * 3600;                 // 30 days
export const MAX_IMG = 20 * 1024 * 1024;           // KV value limit is 25 MiB
export const MAX_TEXT = 200 * 1024;
export const IMG_TYPES = ["image/png", "image/jpeg", "image/webp", "image/gif"];

export function newId() {                          // newest first in KV's lexicographic order
  const inv = (1e13 - Date.now()).toString(36).padStart(9, "0");
  const rnd = crypto.getRandomValues(new Uint8Array(3));
  return inv + [...rnd].map((b) => b.toString(16).padStart(2, "0")).join("");
}

// Mask secrets in log text. Returns { text, hits }.
const RULES = [
  [/(-----BEGIN [A-Z ]*PRIVATE KEY-----)[\s\S]*?(-----END [A-Z ]*PRIVATE KEY-----)/g, "$1\n****\n$2"],
  [/\b(Authorization\s*:\s*(?:Bearer|Basic|Token)\s+)\S+/gi, "$1****"],
  [/([a-z][a-z0-9+.-]*:\/\/[^:\s\/@]+:)[^@\s]+@/gi, "$1****@"],
  [/\b([a-z0-9_.-]*(?:pass(?:word|wd)?|pwd|secret|token|api[_-]?key|access[_-]?key|private[_-]?key|client[_-]?secret|auth[_-]?key))(["']?\s*[:=]\s*)(?:(["'])[^"'\n]{1,300}\3|[^\s"',;]{3,})/gi,
    (m, k, sep, q) => `${k}${sep}${q || ""}****${q || ""}`],
  [/\bAKIA[0-9A-Z]{16}\b/g, "AKIA****"],
  [/\bgh[pousr]_[A-Za-z0-9]{30,}\b/g, "gh*_****"],
  [/\bgithub_pat_[A-Za-z0-9_]{20,}\b/g, "github_pat_****"],
  [/\bcfat_[A-Za-z0-9]{30,}\b/g, "cfat_****"],
  [/\bxox[abprs]-[A-Za-z0-9-]{10,}\b/g, "xox*-****"],
  [/\bsk-[A-Za-z0-9_-]{20,}\b/g, "sk-****"],
  [/\b\d{8,10}:[A-Za-z0-9_-]{35}\b/g, "<telegram-bot-token ****>"],
  [/\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b/g, "<jwt ****>"],
];

export function mask(text) {
  let hits = 0, out = String(text || "");
  for (const [re, rep] of RULES) {
    out = out.replace(re, (...a) => { hits++; return typeof rep === "function" ? rep(...a) : a[0].replace(new RegExp(re.source, re.flags.replace("g", "")), rep); });
  }
  return { text: out, hits };
}

export async function saveItem(env, { title, text, user, img, mime }) {
  const id = newId();
  const m = mask(text);
  const t = mask(title).text.slice(0, 160);
  const opts = { expirationTtl: TTL };
  if (img) await env.STATUS_KV.put(`img:${id}`, img, { ...opts, metadata: { m: mime } });
  await env.STATUS_KV.put(`text:${id}`, m.text.slice(0, MAX_TEXT), opts);
  await env.STATUS_KV.put(`meta:${id}`, "", { ...opts, metadata: { t, c: Date.now(), u: user || "", m: img ? mime : "", s: m.hits } });
  return { id, hits: m.hits };
}

export async function appendText(env, id, more) {
  const cur = await env.STATUS_KV.get(`text:${id}`);
  const meta = await env.STATUS_KV.getWithMetadata(`meta:${id}`);
  if (cur === null || !meta.metadata) return null;
  const m = mask(more);
  const left = Math.max(60, Math.round((meta.metadata.c + TTL * 1000 - Date.now()) / 1000));   // keep original expiry
  await env.STATUS_KV.put(`text:${id}`, (cur ? cur + "\n" : "") + m.text, { expirationTtl: left });
  await env.STATUS_KV.put(`meta:${id}`, "", { expirationTtl: left, metadata: { ...meta.metadata, s: (meta.metadata.s || 0) + m.hits } });
  return m.hits;
}

export function users(env) {                       // STATUS_USERS: "user:pass" per line or comma
  return String(env.STATUS_USERS || "").split(/[\n,]+/).map((s) => s.trim()).filter((s) => s.includes(":"));
}

export function same(a, b) {
  if (a.length !== b.length) return false;
  let d = 0;
  for (let i = 0; i < a.length; i++) d |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return d === 0;
}

export function json(data, status = 200) {
  return new Response(JSON.stringify(data), { status, headers: { "Content-Type": "application/json; charset=utf-8" } });
}
