/**
 * WhatsApp Web DOM helpers (selectors from out/wa-dom-probe.json 2026-09-07).
 *
 * SOURCE selectors (discovered via CDP probe on linked session):
 * - Chat list pane: #pane-side, [data-testid="chat-list"]
 * - Rows: [data-testid="list-item-N"] / [data-testid="cell-frame-container"]
 * - Title: [data-testid="cell-frame-title"] span[title]
 * - Time: [data-testid="cell-frame-primary-detail"]
 * - Preview: [data-testid="cell-frame-secondary"]
 * - Unread: [data-testid="icon-unread-count"]
 * - Search: [data-testid="chat-list-search-container"] input[data-tab="3"]
 * - Open chat title: [data-testid="conversation-info-header-chat-title"]
 * - Messages: [data-testid="conversation-panel-messages"] [data-testid="msg-container"]
 * - Msg text: [data-testid="selectable-text"], meta via [data-pre-plain-text]
 * - Compose: [data-testid="conversation-compose-box-input"] (contenteditable)
 * - Send: appears after text as [data-icon="send"] / aria-label Send; Enter also works
 *
 * Never invent HTTP private APIs. Never print cookies/tokens.
 */
import { evaluate } from "./headless_cdp.mjs";

function log(msg) {
  process.stderr.write(`[wa_dom] ${msg}\n`);
}

const REDACT_PHONE = /\+?\d[\d\s\-()]{6,}\d/g;

function redact(s, max = 120) {
  if (s == null) return null;
  let t = String(s).replace(REDACT_PHONE, "[num]").replace(/\s+/g, " ").trim();
  if (t.length > max) t = t.slice(0, max) + "…";
  return t;
}

/** Parse chat rows currently visible in the left pane. */
const LIST_CHATS_EXPR = (limit) => `(() => {
  const limit = ${Number(limit) || 20};
  const list =
    document.querySelector('[data-testid="chat-list"]') ||
    document.querySelector('#pane-side');
  if (!list) return { ok: false, error: "chat-list not found", chats: [] };
  const rows = [...list.querySelectorAll('[data-testid^="list-item-"]')];
  const chats = [];
  for (const row of rows) {
    if (chats.length >= limit) break;
    const cell = row.querySelector('[data-testid="cell-frame-container"]') || row;
    const titleEl = cell.querySelector('[data-testid="cell-frame-title"] span[title]') ||
      cell.querySelector('[data-testid="cell-frame-title"] span[dir="auto"]') ||
      cell.querySelector('span[title]');
    let title = titleEl
      ? (titleEl.getAttribute("title") || titleEl.textContent || "").trim()
      : "";
    // Skip non-chat rows (Archived header etc.)
    if (!title || /^Archived$/i.test(title)) continue;
    // Strip accessibility prefix like "1 unread message"
    title = title.replace(/^\\d+\\s+unread messages?/i, "").trim();
    const timeEl = cell.querySelector('[data-testid="cell-frame-primary-detail"]');
    const previewEl = cell.querySelector('[data-testid="cell-frame-secondary"]');
    const unreadEl = cell.querySelector('[data-testid="icon-unread-count"]');
    let unread = null;
    if (unreadEl) {
      const u = (unreadEl.textContent || "").trim();
      const n = parseInt(u, 10);
      unread = Number.isFinite(n) ? n : u || true;
    }
    let preview = previewEl ? (previewEl.textContent || "").trim() : null;
    if (preview) {
      preview = preview.replace(/^wds-ic-\\w+/g, "").trim();
      preview = preview.replace(/\\+?\\d[\\d\\s\\-]{6,}\\d/g, "[num]");
      if (preview.length > 100) preview = preview.slice(0, 100) + "…";
    }
    chats.push({
      title,
      unread,
      preview,
      time: timeEl ? (timeEl.textContent || "").trim() : null,
    });
  }
  return { ok: true, chats };
})()`;

export async function listChats(session, { limit = 20 } = {}) {
  const result = await evaluate(session, LIST_CHATS_EXPR(limit));
  if (!result?.ok) throw new Error(result?.error || "listChats failed");
  return result.chats || [];
}

export async function searchChats(session, query, { limit = 20 } = {}) {
  const q = String(query || "");
  log(`searchChats query_len=${q.length}`);
  // Focus + fill search input
  const filled = await evaluate(
    session,
    `(() => {
      const input =
        document.querySelector('[data-testid="chat-list-search-container"] input[data-tab="3"]') ||
        document.querySelector('[data-testid="chat-list-search-container"] input') ||
        document.querySelector('input[aria-label="Search or start a new chat"]') ||
        document.querySelector('div[contenteditable="true"][data-tab="3"]');
      if (!input) return { ok: false, error: "search input not found" };
      input.focus();
      if (input.tagName === "INPUT") {
        const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, "value")?.set;
        if (setter) setter.call(input, ${JSON.stringify(q)});
        else input.value = ${JSON.stringify(q)};
        input.dispatchEvent(new Event("input", { bubbles: true }));
        input.dispatchEvent(new Event("change", { bubbles: true }));
      } else {
        document.execCommand("selectAll", false, null);
        document.execCommand("insertText", false, ${JSON.stringify(q)});
        input.dispatchEvent(new InputEvent("input", { bubbles: true, data: ${JSON.stringify(q)} }));
      }
      return { ok: true };
    })()`
  );
  if (!filled?.ok) throw new Error(filled?.error || "search fill failed");
  await new Promise((r) => setTimeout(r, 800));
  const chats = await listChats(session, { limit });
  // Clear search so the pane is not left filtered for later calls
  try {
    await evaluate(
      session,
      `(() => {
        const cancel =
          document.querySelector('[data-testid="x-alt"]') ||
          document.querySelector('[aria-label="Cancel"]') ||
          document.querySelector('[aria-label="Back"]') ||
          document.querySelector('button[aria-label*="Cancel"]') ||
          document.querySelector('[data-testid="search-input-cancel"]');
        if (cancel) { cancel.click(); return "cancel"; }
        const input =
          document.querySelector('[data-testid="chat-list-search-container"] input[data-tab="3"]') ||
          document.querySelector('[data-testid="chat-list-search-container"] input') ||
          document.querySelector('input[aria-label="Search or start a new chat"]');
        if (input) {
          input.focus();
          const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, "value")?.set;
          if (setter) setter.call(input, "");
          else input.value = "";
          input.dispatchEvent(new Event("input", { bubbles: true }));
          return "cleared";
        }
        return "none";
      })()`
    );
    // Escape via CDP
    await session.browser.send(
      "Input.dispatchKeyEvent",
      { type: "keyDown", key: "Escape", code: "Escape", windowsVirtualKeyCode: 27, nativeVirtualKeyCode: 27 },
      session.pageSessionId
    );
    await session.browser.send(
      "Input.dispatchKeyEvent",
      { type: "keyUp", key: "Escape", code: "Escape", windowsVirtualKeyCode: 27, nativeVirtualKeyCode: 27 },
      session.pageSessionId
    );
    await new Promise((r) => setTimeout(r, 400));
  } catch {
    /* ignore */
  }
  return chats;
}

export async function openChat(session, title) {
  const want = String(title || "").trim();
  if (!want) throw new Error("openChat: empty title");
  log(`openChat title_len=${want.length}`);
  const result = await evaluate(
    session,
    `(() => {
      const wantRaw = ${JSON.stringify(want)};
      const norm = (s) => {
        let t = String(s || "").trim();
        t = t.replace(/^\\d+\\s+unread messages?/i, "").trim();
        t = t.replace(/\\s*\\(You\\)\\s*$/i, "").trim();
        t = t.replace(/\\s+/g, " ").trim();
        return t.toLowerCase();
      };
      const wantN = norm(wantRaw);
      const list =
        document.querySelector('[data-testid="chat-list"]') ||
        document.querySelector('#pane-side');
      if (!list) return { ok: false, error: "chat-list not found", candidates: [] };
      // Prefer list-item rows (self-chat uses message-yourself-row, not cell-frame-container)
      const rows = [...list.querySelectorAll('[data-testid^="list-item-"]')];
      const fallbackRows = rows.length
        ? rows
        : [...list.querySelectorAll('[data-testid="cell-frame-container"]')];
      const entries = [];
      const seenNorm = new Set();
      for (const row of fallbackRows) {
        const cell =
          row.querySelector('[data-testid="cell-frame-container"]') ||
          row.querySelector('[data-testid="message-yourself-row"]') ||
          row;
        const titleEl = cell.querySelector('[data-testid="cell-frame-title"] span[title]') ||
          cell.querySelector('[data-testid="cell-frame-title"] span[dir="auto"]') ||
          row.querySelector('[data-testid="cell-frame-title"] span[title]') ||
          row.querySelector('span[title]');
        let title = titleEl
          ? (titleEl.getAttribute("title") || titleEl.textContent || "").trim()
          : "";
        title = title.replace(/^\\d+\\s+unread messages?/i, "").trim();
        if (!title) continue;
        const n = norm(title);
        if (seenNorm.has(n)) continue;
        seenNorm.add(n);
        const clickable =
          row.querySelector('[data-testid="cell-frame-container"]') ||
          row.querySelector('[data-testid="message-yourself-row"]') ||
          row.querySelector('[role="gridcell"][tabindex="0"]') ||
          cell;
        entries.push({ title, n, clickable });
      }
      const candidates = entries.map((e) => e.title).slice(0, 8);
      const pickUnique = (matches) => {
        if (matches.length !== 1) return null;
        const el = matches[0].clickable;
        el.scrollIntoView({ block: "center" });
        const r = el.getBoundingClientRect();
        // Prefer CDP mouse click from Node (element.click is unreliable for WA list)
        el.click();
        return {
          ok: true,
          title: matches[0].title,
          x: Math.round(r.left + r.width / 2),
          y: Math.round(r.top + r.height / 2),
        };
      };
      // 1. exact normalized
      let hit = pickUnique(entries.filter((e) => e.n === wantN));
      if (hit) return hit;
      // 2. unique startswith / prefix
      hit = pickUnique(
        entries.filter((e) => e.n.startsWith(wantN) || wantN.startsWith(e.n))
      );
      if (hit) return hit;
      // 3. unique contains
      hit = pickUnique(
        entries.filter((e) => e.n.includes(wantN) || wantN.includes(e.n))
      );
      if (hit) return hit;
      return {
        ok: false,
        error: "title not found in visible list",
        scanned: fallbackRows.length,
        candidates,
      };
    })()`
  );
  if (!result?.ok) {
    const err = new Error(result?.error || "openChat failed");
    if (result?.candidates) err.candidates = result.candidates;
    if (result?.scanned != null) err.scanned = result.scanned;
    if (result?.candidates?.length) {
      err.message = `${result.error || "openChat failed"} | candidates=${JSON.stringify(result.candidates)}`;
    }
    throw err;
  }
  // CDP mouse click — element.click() often no-ops on WA chat rows (incl. self-chat)
  if (
    result.x != null &&
    result.y != null &&
    session?.browser?.send &&
    session?.pageSessionId
  ) {
    try {
      await session.browser.send(
        "Input.dispatchMouseEvent",
        { type: "mousePressed", x: result.x, y: result.y, button: "left", clickCount: 1 },
        session.pageSessionId
      );
      await session.browser.send(
        "Input.dispatchMouseEvent",
        { type: "mouseReleased", x: result.x, y: result.y, button: "left", clickCount: 1 },
        session.pageSessionId
      );
    } catch {
      /* element.click already attempted */
    }
  }
  await new Promise((r) => setTimeout(r, 600));
  // Confirm header
  const open = await evaluate(
    session,
    `(() => {
      const el = document.querySelector('[data-testid="conversation-info-header-chat-title"]');
      if (!el) return null;
      return (el.getAttribute("title") || el.textContent || "").trim();
    })()`
  );
  return { opened: result.title, headerTitle: open };
}

export async function readMessages(session, { limit = 20 } = {}) {
  const result = await evaluate(
    session,
    `(() => {
      const limit = ${Number(limit) || 20};
      const pane = document.querySelector('[data-testid="conversation-panel-messages"]');
      if (!pane) return { ok: false, error: "message pane not found — open a chat first", messages: [] };
      const nodes = [...pane.querySelectorAll('[data-testid="msg-container"]')];
      const slice = nodes.slice(-limit);
      const messages = slice.map((m) => {
        const preEl = m.querySelector("[data-pre-plain-text]") || m.closest("[data-pre-plain-text]");
        const pre = preEl ? preEl.getAttribute("data-pre-plain-text") : null;
        const textEl =
          m.querySelector('[data-testid="selectable-text"]') ||
          m.querySelector("span.selectable-text") ||
          m.querySelector(".copyable-text span");
        let body = textEl ? (textEl.innerText || textEl.textContent || "").trim() : "";
        // Strip trailing time glued onto body (e.g. "hello03:02")
        body = body.replace(/\\d{1,2}:\\d{2}(\\s*[AP]M)?$/i, "").trim();
        body = body.replace(/\\+?\\d[\\d\\s\\-]{6,}\\d/g, "[num]");
        if (body.length > 200) body = body.slice(0, 200) + "…";
        const meta = m.querySelector('[data-testid="msg-meta"]');
        const time = meta ? (meta.textContent || "").replace(/[^0-9:APMapm\\s]/g, "").trim().slice(0, 20) : null;
        const incoming = !!m.querySelector('[data-testid="tail-in"]');
        const outgoing = !!m.querySelector('[data-testid="tail-out"]');
        // Prefer pre-plain for author/time
        let author = null;
        let preTime = null;
        if (pre) {
          const m2 = /^\\[(.+?)\\]\\s*(.+?):\\s*$/.exec(pre);
          if (m2) { preTime = m2[1]; author = m2[2]; }
        }
        let direction = "unknown";
        if (incoming) direction = "in";
        else if (outgoing) direction = "out";
        else if (!incoming) direction = "out"; // own bubbles often omit tail-out
        const id =
          m.getAttribute("data-id") ||
          (m.closest("[data-id]") && m.closest("[data-id]").getAttribute("data-id")) ||
          null;
        return {
          id,
          direction,
          author: author ? String(author).slice(0, 60) : null,
          time: time || preTime,
          body,
        };
      });
      const header = document.querySelector('[data-testid="conversation-info-header-chat-title"]');
      const chat = header
        ? (header.getAttribute("title") || header.textContent || "").trim()
        : null;
      return { ok: true, chat, messages };
    })()`
  );
  if (!result?.ok) throw new Error(result?.error || "readMessages failed");
  return result;
}

/**
 * Type into compose box and send. Caller must gate with --confirm.
 * Uses Input.insertText + Enter via CDP when available.
 */
export async function sendText(session, text) {
  const body = String(text ?? "");
  if (!body) throw new Error("sendText: empty text");
  log(`sendText len=${body.length}`);

  const focused = await evaluate(
    session,
    `(() => {
      const box = document.querySelector('[data-testid="conversation-compose-box-input"]');
      if (!box) return { ok: false, error: "compose box not found — open a chat first" };
      box.focus();
      box.click();
      return { ok: true };
    })()`
  );
  if (!focused?.ok) throw new Error(focused?.error || "compose focus failed");

  // Prefer CDP Input.insertText for reliable contenteditable typing
  const { browser, pageSessionId } = session;
  try {
    await browser.send("Input.insertText", { text: body }, pageSessionId);
  } catch {
    // Fallback: execCommand
    await evaluate(
      session,
      `(() => {
        const box = document.querySelector('[data-testid="conversation-compose-box-input"]');
        box.focus();
        document.execCommand("insertText", false, ${JSON.stringify(body)});
        box.dispatchEvent(new InputEvent("input", { bubbles: true, data: ${JSON.stringify(body)} }));
        return true;
      })()`
    );
  }
  await new Promise((r) => setTimeout(r, 300));

  // Click send if visible, else Enter
  const sent = await evaluate(
    session,
    `(() => {
      const sendBtn =
        document.querySelector('[data-testid="compose-btn-send"]') ||
        document.querySelector('button[aria-label="Send"]') ||
        document.querySelector('[data-icon="send"]')?.closest("button, div[role=button]") ||
        document.querySelector('span[data-icon="send"]')?.closest("button, div[role=button]");
      if (sendBtn) { sendBtn.click(); return { ok: true, via: "click" }; }
      return { ok: false, via: null };
    })()`
  );

  if (!sent?.ok) {
    // Enter key
    await browser.send(
      "Input.dispatchKeyEvent",
      { type: "keyDown", key: "Enter", code: "Enter", windowsVirtualKeyCode: 13, nativeVirtualKeyCode: 13 },
      pageSessionId
    );
    await browser.send(
      "Input.dispatchKeyEvent",
      { type: "keyUp", key: "Enter", code: "Enter", windowsVirtualKeyCode: 13, nativeVirtualKeyCode: 13 },
      pageSessionId
    );
    log("send via Enter");
  } else {
    log("send via click");
  }
  await new Promise((r) => setTimeout(r, 500));
  return { ok: true, len: body.length };
}

export default {
  listChats,
  searchChats,
  openChat,
  readMessages,
  sendText,
  redact,
};
