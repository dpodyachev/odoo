// /status/api/*  (Basic Auth is already checked by functions/status/_middleware.js)
//   GET    list            -> [{id,title,created,user,img,masked}]
//   GET    item/<id>       -> {id,title,text,created,user,img}
//   GET    img/<id>        -> image bytes
//   POST   upload          multipart: file?, title, text
//   DELETE item/<id>
import { saveItem, json, IMG_TYPES, MAX_IMG } from "../../../lib/status.js";

const ID = /^[0-9a-z]{9}[0-9a-f]{6}$/;

export async function onRequest({ request, env, params, data }) {
  if (!env.STATUS_KV) return json({ error: "storage not configured" }, 500);
  const [what, id] = params.path || [];
  const m = request.method;

  if (m === "GET" && what === "list") {
    const items = [];
    let cursor;
    do {
      const r = await env.STATUS_KV.list({ prefix: "meta:", cursor, limit: 1000 });
      for (const k of r.keys) {
        const md = k.metadata || {};
        items.push({ id: k.name.slice(5), title: md.t || "", created: md.c || 0, user: md.u || "", img: !!md.m, masked: md.s || 0 });
      }
      cursor = r.list_complete ? null : r.cursor;
    } while (cursor && items.length < 2000);
    return json(items);
  }

  if (id && !ID.test(id)) return json({ error: "bad id" }, 400);

  if (m === "GET" && what === "item" && id) {
    const meta = await env.STATUS_KV.getWithMetadata(`meta:${id}`);
    if (!meta.metadata) return json({ error: "not found" }, 404);
    const text = (await env.STATUS_KV.get(`text:${id}`)) || "";
    const md = meta.metadata;
    return json({ id, title: md.t, text, created: md.c, user: md.u, img: !!md.m, masked: md.s || 0 });
  }

  if (m === "GET" && what === "img" && id) {
    const r = await env.STATUS_KV.getWithMetadata(`img:${id}`, { type: "arrayBuffer" });
    if (!r.value) return new Response("not found", { status: 404 });
    const mime = IMG_TYPES.includes(r.metadata?.m) ? r.metadata.m : "application/octet-stream";
    return new Response(r.value, { headers: { "Content-Type": mime, "X-Content-Type-Options": "nosniff",
                                              "Content-Disposition": `inline; filename="${id}"` } });
  }

  if (m === "POST" && what === "upload") {
    let form;
    try { form = await request.formData(); } catch { return json({ error: "bad form" }, 400); }
    const title = String(form.get("title") || "").trim();
    const text = String(form.get("text") || "");
    const file = form.get("file");
    let img = null, mime = "";
    if (file && typeof file === "object" && file.size) {
      if (!IMG_TYPES.includes(file.type)) return json({ error: "only png, jpeg, webp, gif" }, 400);
      if (file.size > MAX_IMG) return json({ error: "image larger than 20 MB" }, 400);
      img = await file.arrayBuffer(); mime = file.type;
    }
    if (!img && !text.trim()) return json({ error: "empty" }, 400);
    const r = await saveItem(env, { title, text, user: data.user, img, mime });
    return json({ ok: true, ...r });
  }

  if (m === "DELETE" && what === "item" && id) {
    await Promise.all(["meta", "text", "img"].map((p) => env.STATUS_KV.delete(`${p}:${id}`)));
    return json({ ok: true });
  }

  return json({ error: "not found" }, 404);
}
