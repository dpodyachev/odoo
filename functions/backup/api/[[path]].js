// /backup/api/* – large files in R2 (binding BACKUP_R2) with direct browser upload via S3 multipart + pre-signed URLs.
//   GET    list                 -> entries (newest first)
//   POST   init {title,desc,name,size,type}   -> {id, uploadId, partSize}
//   POST   parts {id, ns:[1,2]} -> {urls:{n:url}}   pre-signed UploadPart URLs (1 h)
//   POST   complete {id, parts:[{n,etag}]}
//   POST   abort {id}
//   POST   fetch {url,title,desc}  -> server downloads the URL and streams it into R2
//   GET    dl/<id>              -> 302 to a pre-signed download URL (10 min)
//   DELETE item/<id>
import { json, newId } from "../../../lib/status.js";
import { r2conf, presign, s3 } from "../../../lib/s3.js";

const MB = 1024 * 1024;
const MAX_PARTS = 10000;
const MAX_DESC = 20000;
const metaKey = (id) => `meta/${id}.json`;
const validId = (id) => /^[0-9a-z]{9,20}$/.test(id || "");

async function getMeta(env, id) {
  if (!validId(id)) return null;
  const o = await env.BACKUP_R2.get(metaKey(id));
  return o ? o.json() : null;
}
const putMeta = (env, m) => env.BACKUP_R2.put(metaKey(m.id), JSON.stringify(m), { httpMetadata: { contentType: "application/json" } });

function cleanName(s) {
  const n = String(s || "file").replace(/[\u0000-\u001f\u007f/\\]+/g, "_").replace(/^\.+/, "").trim().slice(0, 180);
  return n || "file";
}

const pub = (m) => ({ id: m.id, title: m.title, desc: m.desc, name: m.name, size: m.size, type: m.type,
                      user: m.user, created: m.created, state: m.state, src: m.src });

export async function onRequest({ request, env, params, data }) {
  if (!env.BACKUP_R2) return json({ error: "R2 binding missing" }, 500);
  const parts = params.path || [];
  const [op, arg] = parts;
  const m = request.method;
  let c;
  try { c = r2conf(env); } catch (e) { return json({ error: e.message }, 500); }

  if (m === "GET" && op === "list") {
    const keys = [], other = [];
    let cursor;
    do {
      const r = await env.BACKUP_R2.list({ cursor, limit: 1000 });
      for (const o of r.objects) {
        if (o.key.startsWith("meta/")) keys.push(o.key);
        else if (!o.key.startsWith("files/")) other.push(o);          // uploaded with aws s3 / rclone / wrangler
      }
      cursor = r.truncated ? r.cursor : undefined;
    } while (cursor);
    const items = (await Promise.all(keys.sort().map(async (k) => {
      const o = await env.BACKUP_R2.get(k);
      return o ? o.json().catch(() => null) : null;
    }))).filter(Boolean).map(pub);
    other.sort((a, b) => b.uploaded - a.uploaded);
    const ext = other.map((o) => ({ key: o.key, title: o.key, name: o.key.split("/").pop(), size: o.size,
                                    created: o.uploaded.getTime(), state: "ok", ext: true }));
    return json({ items, ext });
  }

  if (m === "GET" && op === "dl") {
    const meta = await getMeta(env, arg);
    if (!meta || meta.state !== "ok") return json({ error: "not found" }, 404);
    const disp = `attachment; filename="${meta.name.replace(/[^\x20-\x7e]|"/g, "_")}"; filename*=UTF-8''${encodeURIComponent(meta.name)}`;
    const url = await presign(c, "GET", meta.key, { "response-content-disposition": disp }, 600);
    return new Response(null, { status: 302, headers: { Location: url } });
  }

  // objects outside files/ (uploaded with S3 tools): addressed by key
  if (op === "xdl" || op === "xitem") {
    const key = new URL(request.url).searchParams.get("key") || "";
    if (!key || key.startsWith("meta/") || key.startsWith("files/")) return json({ error: "bad key" }, 400);
    if (m === "GET" && op === "xdl") {
      const name = key.split("/").pop() || "file";
      const disp = `attachment; filename="${name.replace(/[^\x20-\x7e]|"/g, "_")}"; filename*=UTF-8''${encodeURIComponent(name)}`;
      return new Response(null, { status: 302, headers: { Location: await presign(c, "GET", key, { "response-content-disposition": disp }, 600) } });
    }
    if (m === "DELETE" && op === "xitem") { await env.BACKUP_R2.delete(key); return json({ ok: true }); }
  }

  if (m === "DELETE" && op === "item") {
    const meta = await getMeta(env, arg);
    if (!meta) return json({ error: "not found" }, 404);
    if (meta.state === "uploading" && meta.uploadId) await s3(c, "DELETE", meta.key, { uploadId: meta.uploadId }).catch(() => {});
    await env.BACKUP_R2.delete([meta.key, metaKey(meta.id)]);
    return json({ ok: true });
  }

  if (m !== "POST") return json({ error: "not found" }, 404);
  let body;
  try { body = await request.json(); } catch { return json({ error: "bad json" }, 400); }

  if (op === "fetch") {
    let src;
    try { src = new URL(String(body.url || "").trim()); } catch { return json({ error: "bad url" }, 400); }
    if (!/^https?:$/.test(src.protocol)) return json({ error: "only http/https" }, 400);
    const r = await fetch(src.toString(), { redirect: "follow", headers: { "User-Agent": "goldberg-backup/1.0" } });
    if (!r.ok || !r.body) return json({ error: `source HTTP ${r.status}` }, 502);
    const cd = r.headers.get("content-disposition") || "";
    const fromCd = (cd.match(/filename\*=UTF-8''([^;]+)/i) || [])[1];
    let name = fromCd ? decodeURIComponent(fromCd) : (cd.match(/filename="?([^";]+)"?/i) || [])[1];
    if (!name) { try { name = decodeURIComponent(new URL(r.url).pathname.split("/").pop()); } catch { name = ""; } }
    name = cleanName(body.name || name || src.hostname);
    const type = (r.headers.get("content-type") || "application/octet-stream").split(";")[0].trim();
    const id = newId();
    const key = `files/${id}/${name}`;
    const len = Number(r.headers.get("content-length"));
    const enc = r.headers.get("content-encoding");
    let size;
    if (Number.isFinite(len) && len > 0 && !enc) {
      const obj = await env.BACKUP_R2.put(key, r.body, { httpMetadata: { contentType: type } });   // native streaming
      size = obj.size;
    } else {                                                     // unknown length: multipart, 16 MB parts
      const PART = 16 * MB;
      const up = await env.BACKUP_R2.createMultipartUpload(key, { httpMetadata: { contentType: type } });
      const done = [];
      const reader = r.body.getReader();
      let buf = new Uint8Array(PART), fill = 0, n = 0;
      size = 0;
      try {
        for (;;) {
          const { value, done: end } = await reader.read();
          if (value) {
            let off = 0;
            while (off < value.length) {
              const take = Math.min(PART - fill, value.length - off);
              buf.set(value.subarray(off, off + take), fill); fill += take; off += take;
              if (fill === PART) { done.push(await up.uploadPart(++n, buf)); size += fill; buf = new Uint8Array(PART); fill = 0; }
            }
          }
          if (end) break;
        }
        if (fill || !n) { done.push(await up.uploadPart(++n, buf.subarray(0, fill))); size += fill; }
        await up.complete(done);
      } catch (e) { await up.abort().catch(() => {}); return json({ error: "transfer failed: " + e.message }, 502); }
    }
    const meta = { id, key, name, type, size, src: src.toString().replace(/\/\/[^/@]*@/, "//"),
                   title: String(body.title || "").trim().slice(0, 200) || name,
                   desc: String(body.desc || "").slice(0, MAX_DESC),
                   user: data.user || "", created: Date.now(), state: "ok" };
    await putMeta(env, meta);
    return json({ ok: true, item: pub(meta) });
  }

  if (op === "init") {
    const size = Number(body.size);
    if (!Number.isFinite(size) || size < 0) return json({ error: "bad size" }, 400);
    const partSize = Math.max(64 * MB, Math.ceil(size / (MAX_PARTS - 100) / MB) * MB);
    if (size > partSize * MAX_PARTS) return json({ error: "file too large" }, 413);
    const id = newId();
    const name = cleanName(body.name);
    const type = /^[\w.+-]+\/[\w.+-]+$/.test(body.type || "") ? body.type : "application/octet-stream";
    const key = `files/${id}/${name}`;
    const r = await s3(c, "POST", key, { uploads: "" }, "", { "content-type": type });
    const xml = await r.text();
    const uploadId = (xml.match(/<UploadId>([^<]+)<\/UploadId>/) || [])[1];
    if (!r.ok || !uploadId) return json({ error: "R2 init failed", status: r.status }, 502);
    const meta = { id, key, uploadId, partSize, name, type, size,
                   title: String(body.title || "").trim().slice(0, 200) || name,
                   desc: String(body.desc || "").slice(0, MAX_DESC),
                   user: data.user || "", created: Date.now(), state: "uploading" };
    await putMeta(env, meta);
    return json({ id, uploadId, partSize });
  }

  const meta = await getMeta(env, body.id);
  if (!meta) return json({ error: "not found" }, 404);

  if (op === "parts") {
    if (meta.state !== "uploading") return json({ error: "not uploading" }, 409);
    const ns = (Array.isArray(body.ns) ? body.ns : []).map(Number).filter((n) => Number.isInteger(n) && n >= 1 && n <= MAX_PARTS).slice(0, 50);
    const urls = {};
    for (const n of ns) urls[n] = await presign(c, "PUT", meta.key, { partNumber: String(n), uploadId: meta.uploadId }, 3600);
    return json({ urls });
  }

  if (op === "complete") {
    if (meta.state !== "uploading") return json({ error: "not uploading" }, 409);
    const list = (Array.isArray(body.parts) ? body.parts : [])
      .map((p) => ({ n: Number(p.n), etag: String(p.etag || "").replace(/[<>&]/g, "") }))
      .filter((p) => Number.isInteger(p.n) && p.etag).sort((a, b) => a.n - b.n);
    if (!list.length) return json({ error: "no parts" }, 400);
    const xml = "<CompleteMultipartUpload>" +
      list.map((p) => `<Part><PartNumber>${p.n}</PartNumber><ETag>${p.etag}</ETag></Part>`).join("") + "</CompleteMultipartUpload>";
    const r = await s3(c, "POST", meta.key, { uploadId: meta.uploadId }, xml, { "content-type": "application/xml" });
    const out = await r.text();
    if (!r.ok || /<Error>/.test(out)) return json({ error: "R2 complete failed", status: r.status, detail: (out.match(/<Code>([^<]+)/) || [])[1] }, 502);
    const head = await env.BACKUP_R2.head(meta.key);
    meta.size = head ? head.size : meta.size;
    meta.state = "ok";
    delete meta.uploadId;
    await putMeta(env, meta);
    return json({ ok: true, item: pub(meta) });
  }

  if (op === "abort") {
    if (meta.state === "uploading" && meta.uploadId) await s3(c, "DELETE", meta.key, { uploadId: meta.uploadId }).catch(() => {});
    if (meta.state !== "ok") await env.BACKUP_R2.delete(metaKey(meta.id));
    return json({ ok: true });
  }

  return json({ error: "not found" }, 404);
}
