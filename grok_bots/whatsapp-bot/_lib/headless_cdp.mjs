#!/usr/bin/env node
/**
 * Headless CDP bridge for WhatsApp Web on THIS agent's Chrome.
 * Uses official sand-host cdp-cookies helpers. Never prints cookies/tokens.
 *
 * Port = SAND_BOX_CDP_PORT_BASE + displayNumber from DISPLAY
 * (same pattern as /home/box/whatsapp-auth/export_from_display.mjs).
 *
 * Node 20: run with NODE_OPTIONS=--experimental-websocket (or node --experimental-websocket).
 */
import {
  connectBrowser,
  listPageTargets,
  attachToPage,
  detachSession,
} from "/home/box/sand-host/box-scripts/cdp-cookies.mjs";
import { SAND_BOX_CDP_PORT_BASE } from "/home/box/sand-host/box-scripts/box-contract.generated.mjs";

const WA_URL = "https://web.whatsapp.com/";
const READY_TIMEOUT_MS = 30000;
const POLL_MS = 400;

function log(msg) {
  process.stderr.write(`[headless_cdp] ${msg}\n`);
}

export function displayNumber() {
  const d = process.env.DISPLAY || "";
  const m = /:(\d+)/.exec(d);
  if (!m) throw new Error("DISPLAY unset — set e.g. DISPLAY=:30");
  return Number.parseInt(m[1], 10);
}

export function cdpPort() {
  return SAND_BOX_CDP_PORT_BASE + displayNumber();
}

/**
 * Runtime.evaluate helper — awaitPromise + returnByValue.
 * @param {{ browser: object, pageSessionId: string }} session
 * @param {string} expression
 */
export async function evaluate(session, expression) {
  const { browser, pageSessionId } = session;
  const result = await browser.send(
    "Runtime.evaluate",
    {
      expression,
      awaitPromise: true,
      returnByValue: true,
    },
    pageSessionId
  );
  if (result?.exceptionDetails != null) {
    const text =
      result.exceptionDetails.exception?.description ||
      result.exceptionDetails.text ||
      "Runtime.evaluate exception";
    const err = new Error(String(text).slice(0, 400));
    err.exceptionDetails = result.exceptionDetails;
    throw err;
  }
  return result?.result?.value;
}

/**
 * Heuristic: chat list / search visible ⇒ linked; QR / "Scan to log in" ⇒ not.
 * Also false for the "WhatsApp is open elsewhere" interstitial (confirm-popup only).
 */
export async function assertLinked(session) {
  const linked = await evaluate(
    session,
    `(() => {
      const body = document.body ? document.body.innerText : "";
      if (/Scan to log in|Scan the QR|Link with phone number|Use WhatsApp on your phone/i.test(body)) {
        return false;
      }
      // Multi-tab interstitial
      if (/WhatsApp is open in another window|use WhatsApp here/i.test(body)) {
        // Still may become linked after clicking — but not yet
        const chatList =
          document.querySelector('[data-testid="chat-list"]') ||
          document.querySelector('#pane-side') ||
          document.querySelector('[aria-label="Chat list"]');
        if (!chatList) return false;
      }
      const search =
        document.querySelector('[data-testid="chat-list-search"]') ||
        document.querySelector('[data-testid="search"]') ||
        document.querySelector('[data-testid="search-input"]') ||
        document.querySelector('div[contenteditable="true"][data-tab="3"]') ||
        document.querySelector('[aria-label="Search input textbox"]') ||
        document.querySelector('[aria-label*="Search"]');
      const chatList =
        document.querySelector('[data-testid="chat-list"]') ||
        document.querySelector('#pane-side') ||
        document.querySelector('[aria-label="Chat list"]') ||
        document.querySelector('[data-testid="cell-frame-container"]');
      if (chatList || search) return true;
      const canvas = document.querySelector("canvas");
      if (canvas && canvas.width > 100 && canvas.height > 100 && !chatList) return false;
      if (/\\(\\d+\\)\\s*WhatsApp/i.test(document.title)) return true;
      return false;
    })()`
  );
  return !!linked;
}

async function waitForWaReady(session, timeoutMs = READY_TIMEOUT_MS) {
  const start = Date.now();
  while (Date.now() - start < timeoutMs) {
    const state = await evaluate(
      session,
      `(() => {
        const body = document.body ? document.body.innerText : "";
        const chatList =
          document.querySelector('[data-testid="chat-list"]') ||
          document.querySelector('#pane-side') ||
          document.querySelector('[aria-label="Chat list"]') ||
          document.querySelector('[data-testid="cell-frame-container"]');
        const search =
          document.querySelector('[data-testid="chat-list-search"]') ||
          document.querySelector('div[contenteditable="true"][data-tab="3"]') ||
          document.querySelector('[aria-label*="Search"]');
        if (chatList || search) return "linked";
        if (/Scan to log in|Scan the QR|Link with phone number/i.test(body)) return "qr";
        if (/WhatsApp is open in another window/i.test(body)) return "elsewhere";
        if (document.querySelector('[data-testid="confirm-popup"]')) return "popup";
        return "loading";
      })()`
    ).catch(() => "loading");
    if (state === "linked" || state === "qr") return state;
    // brief wait on interstitial — caller may try another target
    if (state === "elsewhere" || state === "popup") return state;
    await new Promise((r) => setTimeout(r, POLL_MS));
  }
  return "timeout";
}

async function scoreWaPage(browser, targetId) {
  const sid = await attachToPage(browser, targetId);
  if (!sid) return { score: -1, sessionId: null, state: "noattach" };
  try {
    const info = await evaluate(
      { browser, pageSessionId: sid },
      `(() => {
        const title = document.title || "";
        const body = document.body ? document.body.innerText.slice(0, 500) : "";
        const chatList = !!(
          document.querySelector('[data-testid="chat-list"]') ||
          document.querySelector('#pane-side') ||
          document.querySelector('[aria-label="Chat list"]') ||
          document.querySelector('[data-testid="cell-frame-container"]')
        );
        const search = !!(
          document.querySelector('[data-testid="chat-list-search"]') ||
          document.querySelector('div[contenteditable="true"][data-tab="3"]') ||
          document.querySelector('[aria-label*="Search"]')
        );
        const elsewhere = /WhatsApp is open in another window/i.test(body);
        const qr = /Scan to log in|Scan the QR/i.test(body);
        const unreadTitle = /\\(\\d+\\)\\s*WhatsApp/i.test(title);
        return { title, chatList, search, elsewhere, qr, unreadTitle };
      })()`
    );
    let score = 0;
    if (info?.chatList) score += 100;
    if (info?.search) score += 50;
    if (info?.unreadTitle) score += 40;
    if (info?.title === "WhatsApp" && !info?.elsewhere) score += 5;
    if (info?.elsewhere) score -= 50;
    if (info?.qr) score -= 100;
    return { score, sessionId: sid, state: info, keep: true };
  } catch (e) {
    await detachSession(browser, sid).catch(() => {});
    return { score: -1, sessionId: null, state: String(e.message).slice(0, 80) };
  }
}

async function findOrCreateWaTarget(browser) {
  // Prefer raw Target.getTargets so we can see titles
  const raw = await browser.send("Target.getTargets");
  const pages = (raw.targetInfos || []).filter(
    (info) =>
      info.type === "page" &&
      typeof info.url === "string" &&
      /web\.whatsapp\.com/i.test(info.url)
  );

  if (pages.length === 0) {
    log("no WhatsApp tab — creating target");
    const created = await browser.send("Target.createTarget", { url: WA_URL });
    if (!created?.targetId) throw new Error("Target.createTarget failed");
    return { targetId: created.targetId, url: WA_URL, title: "" };
  }

  // Rank by title hint first (avoid attaching to every dead tab)
  pages.sort((a, b) => {
    const score = (t) => {
      const title = t.title || "";
      if (/\(\d+\)\s*WhatsApp/i.test(title)) return 100;
      if (title === "WhatsApp") return 10;
      return 0;
    };
    return score(b) - score(a);
  });

  log(`found ${pages.length} WA page(s); top title=${JSON.stringify((pages[0].title || "").slice(0, 40))}`);

  // Probe top few
  let best = null;
  const probeN = Math.min(pages.length, 5);
  for (let i = 0; i < probeN; i++) {
    const p = pages[i];
    const scored = await scoreWaPage(browser, p.targetId);
    log(`probe ${String(p.targetId).slice(0, 8)}… score=${scored.score} title=${JSON.stringify((p.title || "").slice(0, 30))}`);
    if (scored.sessionId && scored.keep) {
      // detach unless this is the winner we'll keep — pick highest
      if (!best || scored.score > best.score) {
        if (best?.sessionId) await detachSession(browser, best.sessionId).catch(() => {});
        best = { ...scored, targetId: p.targetId, url: p.url, title: p.title };
      } else {
        await detachSession(browser, scored.sessionId).catch(() => {});
      }
    }
    if (best && best.score >= 100) break; // good enough (has chat list)
  }

  if (best && best.score >= 0) {
    // already attached
    return {
      targetId: best.targetId,
      url: best.url,
      title: best.title,
      pageSessionId: best.sessionId,
      score: best.score,
    };
  }

  // Fallback: first page
  return { targetId: pages[0].targetId, url: pages[0].url, title: pages[0].title };
}

/**
 * Try to click "Use WhatsApp here" on interstitial if present.
 */
async function maybeAcceptHere(session) {
  const clicked = await evaluate(
    session,
    `(() => {
      const body = document.body ? document.body.innerText : "";
      if (!/WhatsApp is open in another window|use WhatsApp here/i.test(body)) return false;
      const buttons = [...document.querySelectorAll("button, div[role='button']")];
      const btn = buttons.find((b) => /use WhatsApp here|Continue/i.test(b.innerText || ""));
      if (btn) { btn.click(); return true; }
      // data-testid confirm
      const pop = document.querySelector('[data-testid="popup-controls-ok"], [data-testid="confirm-popup"] button');
      if (pop) { pop.click(); return true; }
      return false;
    })()`
  ).catch(() => false);
  if (clicked) {
    log("clicked Use WhatsApp here / confirm");
    await new Promise((r) => setTimeout(r, 2000));
  }
  return !!clicked;
}

/**
 * Connect to agent's Chrome via CDP and attach to WhatsApp Web page.
 * @returns {Promise<{ browser, port, pageSessionId, targetId }>}
 */
export async function connectWa() {
  if (typeof WebSocket === "undefined") {
    throw new Error(
      "WebSocket global missing — run with NODE_OPTIONS=--experimental-websocket (Node 20)"
    );
  }
  const port = cdpPort();
  log(`connecting CDP port=${port} DISPLAY=${process.env.DISPLAY || "?"}`);
  const browser = await connectBrowser(port);
  let pageSessionId = null;
  let targetId = null;
  try {
    const target = await findOrCreateWaTarget(browser);
    targetId = target.targetId;
    if (target.pageSessionId) {
      pageSessionId = target.pageSessionId;
    } else {
      pageSessionId = await attachToPage(browser, targetId);
    }
    if (!pageSessionId) throw new Error("attachToPage returned null");

    const url = await evaluate({ browser, pageSessionId }, "location.href").catch(() => "");
    if (!/web\.whatsapp\.com/i.test(String(url || ""))) {
      log("navigating to web.whatsapp.com");
      await browser.send("Page.enable", {}, pageSessionId).catch(() => {});
      await browser.send("Page.navigate", { url: WA_URL }, pageSessionId);
      await new Promise((r) => setTimeout(r, 1500));
    }

    await maybeAcceptHere({ browser, pageSessionId });

    let ready = await waitForWaReady({ browser, pageSessionId });
    // If we landed on interstitial and click helped, re-wait
    if (ready === "elsewhere" || ready === "popup") {
      await maybeAcceptHere({ browser, pageSessionId });
      ready = await waitForWaReady({ browser, pageSessionId }, 15000);
    }
    log(`wa ready state=${ready} score=${target.score ?? "?"}`);
    return { browser, port, pageSessionId, targetId };
  } catch (err) {
    if (pageSessionId) await detachSession(browser, pageSessionId).catch(() => {});
    browser.close();
    throw err;
  }
}

export async function disconnect(browser, pageSessionId = null) {
  if (!browser) return;
  try {
    if (pageSessionId) await detachSession(browser, pageSessionId);
  } catch {
    /* ignore */
  }
  try {
    browser.close();
  } catch {
    /* ignore */
  }
}

export default {
  connectWa,
  evaluate,
  disconnect,
  assertLinked,
  displayNumber,
  cdpPort,
};
