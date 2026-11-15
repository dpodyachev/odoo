// Telegram webhook: a photo (or image file) with a caption -> new /status/ entry.
// Caption: first line = title, rest = log text. A text reply to the bot's confirmation is appended to that entry.
// Secrets: STATUS_BOT_TOKEN (BotFather), STATUS_TG_SECRET (webhook header), STATUS_TG_CHATS (allowed chat ids).
import { saveItem, appendText, IMG_TYPES, MAX_IMG } from "../../../lib/status.js";

const OK = () => new Response("ok");

async function tg(env, method, body) {
  return fetch(`https://api.telegram.org/bot${env.STATUS_BOT_TOKEN}/${method}`, {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body),
  }).then((r) => r.json()).catch(() => ({}));
}

export async function onRequestPost({ request, env }) {
  if (!env.STATUS_BOT_TOKEN || !env.STATUS_KV) return OK();
  let upd;
  try { upd = await request.json(); } catch { return OK(); }
  const msg = upd.message;
  if (!msg) return OK();
  const chat = String(msg.chat?.id || "");
  const allowed = String(env.STATUS_TG_CHATS || "").split(/[\s,]+/).filter(Boolean);
  if (!allowed.includes(chat)) {
    await tg(env, "sendMessage", { chat_id: chat, text: `⛔ Not allowed. Your chat id: ${chat}` });
    return OK();
  }
  const user = msg.from?.username ? "@" + msg.from.username : (msg.from?.first_name || "telegram");
  const base = new URL(request.url).origin;

  // text reply to a confirmation -> append to that entry
  const ref = (msg.reply_to_message?.text || "").match(/ID: ([0-9a-z]{9}[0-9a-f]{6})/);
  if (msg.text && ref) {
    const hits = await appendText(env, ref[1], msg.text);
    await tg(env, "sendMessage", { chat_id: chat, reply_to_message_id: msg.message_id,
      text: hits === null ? "❌ Entry not found (expired?)" : `➕ Added${hits ? ` · masked: ${hits}` : ""}\n${base}/status/#${ref[1]}` });
    return OK();
  }
  if (msg.text?.startsWith("/start") || msg.text?.startsWith("/help")) {
    await tg(env, "sendMessage", { chat_id: chat, text:
      "Send a screenshot with a caption: first line = title, the rest = log.\n" +
      "Reply to my confirmation with more text to append it.\nEntries are deleted after 30 days.\n" + base + "/status/" });
    return OK();
  }

  let fileId = null, mime = "image/jpeg";
  if (msg.photo?.length) fileId = msg.photo[msg.photo.length - 1].file_id;
  else if (msg.document && IMG_TYPES.includes(msg.document.mime_type)) { fileId = msg.document.file_id; mime = msg.document.mime_type; }

  const caption = msg.caption || msg.text || "";
  const [first, ...rest] = caption.split("\n");
  let img = null;
  if (fileId) {
    const f = await tg(env, "getFile", { file_id: fileId });
    const p = f.result?.file_path;
    if (p) {
      const r = await fetch(`https://api.telegram.org/file/bot${env.STATUS_BOT_TOKEN}/${p}`);
      if (r.ok) { img = await r.arrayBuffer(); if (p.endsWith(".png")) mime = "image/png"; else if (p.endsWith(".webp")) mime = "image/webp"; }
    }
    if (!img || img.byteLength > MAX_IMG) {
      await tg(env, "sendMessage", { chat_id: chat, text: "❌ Could not load the image (max 20 MB)" });
      return OK();
    }
  }
  if (!img && !caption.trim()) return OK();
  const r = await saveItem(env, { title: first || (img ? "Screenshot" : "Log"), text: rest.join("\n"), user, img, mime });
  await tg(env, "sendMessage", { chat_id: chat, reply_to_message_id: msg.message_id,
    text: `✅ Saved${r.hits ? ` · masked: ${r.hits}` : ""}\n${base}/status/#${r.id}\nID: ${r.id}\n(reply to this message to add more text)` });
  return OK();
}
