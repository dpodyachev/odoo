// Minimal AWS Signature V4 for Cloudflare R2's S3 API (no dependencies).
// Secrets: R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY, R2_BUCKET.
const enc = new TextEncoder();
const hex = (buf) => [...new Uint8Array(buf)].map((b) => b.toString(16).padStart(2, "0")).join("");
const sha256 = async (s) => hex(await crypto.subtle.digest("SHA-256", typeof s === "string" ? enc.encode(s) : s));
async function hmac(key, s) {
  const k = await crypto.subtle.importKey("raw", typeof key === "string" ? enc.encode(key) : key, { name: "HMAC", hash: "SHA-256" }, false, ["sign"]);
  return crypto.subtle.sign("HMAC", k, enc.encode(s));
}
// RFC 3986 encoding as S3 expects it
const rfc = (s) => encodeURIComponent(s).replace(/[!'()*]/g, (c) => "%" + c.charCodeAt(0).toString(16).toUpperCase());
const encPath = (key) => key.split("/").map(rfc).join("/");

export function r2conf(env) {
  const c = { acc: env.R2_ACCOUNT_ID, id: env.R2_ACCESS_KEY_ID, secret: env.R2_SECRET_ACCESS_KEY, bucket: env.R2_BUCKET };
  if (!c.acc || !c.id || !c.secret || !c.bucket) throw new Error("R2 secrets missing");
  c.host = `${c.acc}.r2.cloudflarestorage.com`;
  return c;
}

async function signingKey(secret, date) {
  let k = await hmac("AWS4" + secret, date);
  for (const p of ["auto", "s3", "aws4_request"]) k = await hmac(k, p);
  return k;
}

function stamp() {
  const iso = new Date().toISOString().replace(/[-:]/g, "").replace(/\.\d{3}/, "");   // 20261115T172700Z
  return { amz: iso, date: iso.slice(0, 8) };
}

const canonQuery = (q) => Object.keys(q).sort().map((k) => `${rfc(k)}=${rfc(String(q[k]))}`).join("&");

// Pre-signed URL (browser uploads a part / downloads directly from R2).
export async function presign(c, method, key, query = {}, expires = 3600) {
  const { amz, date } = stamp();
  const scope = `${date}/auto/s3/aws4_request`;
  const q = { ...query, "X-Amz-Algorithm": "AWS4-HMAC-SHA256", "X-Amz-Credential": `${c.id}/${scope}`, "X-Amz-Date": amz,
              "X-Amz-Expires": String(expires), "X-Amz-SignedHeaders": "host" };
  const path = `/${c.bucket}/${encPath(key)}`;
  const creq = [method, path, canonQuery(q), `host:${c.host}\n`, "host", "UNSIGNED-PAYLOAD"].join("\n");
  const sts = ["AWS4-HMAC-SHA256", amz, scope, await sha256(creq)].join("\n");
  const sig = hex(await hmac(await signingKey(c.secret, date), sts));
  return `https://${c.host}${path}?${canonQuery(q)}&X-Amz-Signature=${sig}`;
}

// Signed server-side request (create / complete / abort multipart upload).
export async function s3(c, method, key, query = {}, body = "", headers = {}) {
  const { amz, date } = stamp();
  const scope = `${date}/auto/s3/aws4_request`;
  const path = `/${c.bucket}/${encPath(key)}`;
  const h = { host: c.host, "x-amz-content-sha256": await sha256(body), "x-amz-date": amz };
  for (const [k, v] of Object.entries(headers)) h[k.toLowerCase()] = String(v).trim();
  const names = Object.keys(h).sort();
  const creq = [method, path, canonQuery(query), names.map((n) => `${n}:${h[n]}\n`).join(""), names.join(";"), h["x-amz-content-sha256"]].join("\n");
  const sts = ["AWS4-HMAC-SHA256", amz, scope, await sha256(creq)].join("\n");
  const sig = hex(await hmac(await signingKey(c.secret, date), sts));
  h.authorization = `AWS4-HMAC-SHA256 Credential=${c.id}/${scope}, SignedHeaders=${names.join(";")}, Signature=${sig}`;
  delete h.host;
  const qs = canonQuery(query);
  return fetch(`https://${c.host}${path}${qs ? "?" + qs : ""}`, { method, headers: h, body: method === "GET" || method === "HEAD" ? undefined : body });
}
