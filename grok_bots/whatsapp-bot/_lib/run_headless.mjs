#!/usr/bin/env node
/**
 * Headless WhatsApp runner — CDP to agent's linked Chrome.
 *
 * Usage:
 *   NODE_OPTIONS=--experimental-websocket DISPLAY=:30 \
 *     node _lib/run_headless.mjs <command> [--json-args '...'] [--limit N] ...
 *
 * Commands: list-chats | search-chats | read-messages | send-text | assert-linked
 * Stdout: JSON only. Stderr: progress.
 * Exit: 0 ok, 1 auth/QR dead, 2 error.
 *
 * Never prints cookies, tokens, or auth.env values.
 */
import { connectWa, disconnect, assertLinked } from "./headless_cdp.mjs";
import {
  listChats,
  searchChats,
  openChat,
  readMessages,
  sendText,
} from "./wa_dom.mjs";

function log(msg) {
  process.stderr.write(`[run_headless] ${msg}\n`);
}

function parseArgs(argv) {
  const out = { command: null, jsonArgs: {}, flags: {} };
  const args = [...argv];
  if (args.length === 0) return out;
  out.command = args.shift();
  while (args.length) {
    const a = args.shift();
    if (a === "--json-args") {
      const raw = args.shift() || "{}";
      try {
        out.jsonArgs = JSON.parse(raw);
      } catch (e) {
        throw new Error(`invalid --json-args: ${e.message}`);
      }
    } else if (a === "--limit") {
      out.flags.limit = Number.parseInt(args.shift(), 10);
    } else if (a === "--query") {
      out.flags.query = args.shift();
    } else if (a === "--chat" || a === "--title") {
      out.flags.chat = args.shift();
    } else if (a === "--text") {
      out.flags.text = args.shift();
    } else if (a === "--confirm") {
      out.flags.confirm = true;
    } else if (a.startsWith("--")) {
      const key = a.slice(2).replace(/-/g, "_");
      const val = args[0] && !args[0].startsWith("--") ? args.shift() : true;
      out.flags[key] = val;
    }
  }
  return out;
}

function emit(obj) {
  process.stdout.write(JSON.stringify(obj) + "\n");
}

async function main() {
  if (typeof WebSocket === "undefined") {
    emit({
      ok: false,
      error:
        "WebSocket missing — set NODE_OPTIONS=--experimental-websocket (Node 20)",
    });
    process.exit(2);
  }

  let parsed;
  try {
    parsed = parseArgs(process.argv.slice(2));
  } catch (e) {
    emit({ ok: false, error: e.message });
    process.exit(2);
  }

  const { command, jsonArgs, flags } = parsed;
  if (!command) {
    emit({
      ok: false,
      error: "usage: run_headless.mjs <list-chats|search-chats|read-messages|send-text|assert-linked>",
    });
    process.exit(2);
  }

  const limit = flags.limit ?? jsonArgs.limit ?? 20;
  const query = flags.query ?? jsonArgs.query;
  const chat = flags.chat ?? jsonArgs.chat ?? jsonArgs.title;
  const text = flags.text ?? jsonArgs.text;
  const confirm = !!(flags.confirm || jsonArgs.confirm);

  let browser, pageSessionId;
  try {
    const conn = await connectWa();
    browser = conn.browser;
    pageSessionId = conn.pageSessionId;
    const session = { browser, pageSessionId };

    const linked = await assertLinked(session);
    if (!linked) {
      emit({ ok: false, error: "not_linked", hint: "QR dead or interstitial — re-link via qr-link" });
      process.exit(1);
    }

    if (command === "assert-linked") {
      emit({ ok: true, linked: true });
      return;
    }

    if (command === "list-chats") {
      const chats = await listChats(session, { limit });
      emit({ ok: true, mode: "headless", count: chats.length, chats });
      return;
    }

    if (command === "search-chats") {
      if (!query) {
        emit({ ok: false, error: "--query required" });
        process.exit(2);
      }
      const chats = await searchChats(session, query, { limit });
      emit({ ok: true, mode: "headless", query, count: chats.length, chats });
      return;
    }

    if (command === "read-messages") {
      if (chat) {
        await openChat(session, chat);
      }
      const result = await readMessages(session, { limit });
      emit({
        ok: true,
        mode: "headless",
        chat: result.chat,
        count: (result.messages || []).length,
        messages: result.messages,
      });
      return;
    }

    if (command === "send-text") {
      if (!confirm) {
        emit({
          ok: false,
          error: "confirm_required",
          hint: "pass --confirm to send (mutating)",
          dry_run: true,
          chat: chat || null,
          text_len: text != null ? String(text).length : 0,
        });
        process.exit(2);
      }
      if (!chat) {
        emit({ ok: false, error: "--chat required" });
        process.exit(2);
      }
      if (text == null || text === "") {
        emit({ ok: false, error: "--text required" });
        process.exit(2);
      }
      await openChat(session, chat);
      const sent = await sendText(session, text);
      emit({ ok: true, mode: "headless", sent: true, chat, text_len: sent.len });
      return;
    }

    emit({ ok: false, error: `unknown command: ${command}` });
    process.exit(2);
  } catch (e) {
    const msg = String(e?.message || e).slice(0, 400);
    log(`error: ${msg}`);
    if (/QR|not_linked|Scan to log/i.test(msg)) {
      emit({ ok: false, error: "not_linked", detail: msg });
      process.exit(1);
    }
    emit({ ok: false, error: msg });
    process.exit(2);
  } finally {
    await disconnect(browser, pageSessionId);
  }
}

await main();
