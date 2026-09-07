#!/usr/bin/env node
/**
 * Redacted DOM probe for WhatsApp Web via headless CDP.
 * Writes /workspace/whatsapp-scripts/out/wa-dom-probe.json
 * Never dumps message text with phone numbers; truncates previews.
 */
import { writeFileSync, mkdirSync } from "node:fs";
import { connectWa, evaluate, disconnect, assertLinked } from "./headless_cdp.mjs";

const OUT = "/workspace/whatsapp-scripts/out/wa-dom-probe.json";

function log(m) {
  process.stderr.write(`[probe] ${m}\n`);
}

const { browser, pageSessionId, port, targetId } = await connectWa();
const session = { browser, pageSessionId };
try {
  const linked = await assertLinked(session);
  log(`linked=${linked} port=${port} target=${String(targetId).slice(0, 8)}…`);

  const probe = await evaluate(
    session,
    `(() => {
      const app = document.querySelector("#app") || document.body;
      const testids = new Set();
      const walk = (root) => {
        if (!root || !root.querySelectorAll) return;
        for (const el of root.querySelectorAll("[data-testid]")) {
          const v = el.getAttribute("data-testid");
          if (v) testids.add(v);
          if (testids.size >= 80) break;
        }
      };
      walk(app);

      const pane =
        document.querySelector("#pane-side") ||
        document.querySelector('[data-testid="chat-list"]') ||
        document.querySelector('[aria-label="Chat list"]');
      const paneLen = pane ? (pane.outerHTML || "").length : 0;
      const paneTag = pane
        ? {
            tag: pane.tagName,
            id: pane.id || null,
            testid: pane.getAttribute("data-testid"),
            aria: pane.getAttribute("aria-label"),
            childCount: pane.children ? pane.children.length : 0,
          }
        : null;

      // Sample cell structure (redacted)
      const cells = [
        ...document.querySelectorAll('[data-testid="cell-frame-container"]'),
        ...document.querySelectorAll('[data-testid="list-item-"]'),
      ].slice(0, 3);
      // Also try role=listitem under pane
      const listItems = pane
        ? [...pane.querySelectorAll('[role="listitem"], [role="row"]')].slice(0, 5)
        : [];

      const sampleCell = (el) => {
        if (!el) return null;
        const titleEl =
          el.querySelector('[data-testid="cell-frame-title"]') ||
          el.querySelector("span[title]") ||
          el.querySelector('[dir="auto"]');
        const title = titleEl
          ? (titleEl.getAttribute("title") || titleEl.textContent || "").slice(0, 40)
          : null;
        const previewEl =
          el.querySelector('[data-testid="last-msg-row"]') ||
          el.querySelector('[data-testid="cell-frame-secondary"]');
        let preview = previewEl ? (previewEl.textContent || "").trim().slice(0, 40) : null;
        // Redact phone-like sequences
        if (preview) preview = preview.replace(/\\+?\\d[\\d\\s\\-]{6,}\\d/g, "[num]");
        const attrs = {};
        for (const a of el.attributes || []) {
          if (a.name.startsWith("data-") || a.name === "aria-label" || a.name === "role") {
            attrs[a.name] = String(a.value).slice(0, 80);
          }
        }
        const childTestids = [...el.querySelectorAll("[data-testid]")]
          .map((c) => c.getAttribute("data-testid"))
          .filter(Boolean)
          .slice(0, 20);
        return { title, preview, attrs, childTestids, tag: el.tagName };
      };

      // Compose / conversation hints
      const compose =
        document.querySelector('[data-testid="conversation-compose-box-input"]') ||
        document.querySelector('div[contenteditable="true"][data-tab="10"]') ||
        document.querySelector('footer [contenteditable="true"]');
      const msgList =
        document.querySelector('[data-testid="conversation-panel-messages"]') ||
        document.querySelector('#main [role="application"]') ||
        document.querySelector('[data-testid="msg-container"]');

      return {
        title: document.title,
        href: location.href,
        testids: [...testids].slice(0, 80),
        paneSide: { length: paneLen, meta: paneTag },
        sampleCells: cells.map(sampleCell),
        sampleListItems: listItems.map(sampleCell),
        composeFound: !!compose,
        composeTestid: compose ? compose.getAttribute("data-testid") : null,
        msgListFound: !!msgList,
        msgListTestid: msgList ? msgList.getAttribute("data-testid") : null,
        // Structural selectors presence map
        selectors: {
          "data-testid=chat-list": !!document.querySelector('[data-testid="chat-list"]'),
          "data-testid=cell-frame-container": !!document.querySelector('[data-testid="cell-frame-container"]'),
          "data-testid=cell-frame-title": !!document.querySelector('[data-testid="cell-frame-title"]'),
          "data-testid=chat-list-search": !!document.querySelector('[data-testid="chat-list-search"]'),
          "data-testid=conversation-compose-box-input": !!document.querySelector('[data-testid="conversation-compose-box-input"]'),
          "data-testid=conversation-panel-messages": !!document.querySelector('[data-testid="conversation-panel-messages"]'),
          "data-testid=msg-container": !!document.querySelector('[data-testid="msg-container"]'),
          "data-testid=send": !!document.querySelector('[data-testid="send"]'),
          "data-testid=compose-btn-send": !!document.querySelector('[data-testid="compose-btn-send"]'),
          "#pane-side": !!document.querySelector("#pane-side"),
          "#main": !!document.querySelector("#main"),
          "canvas": !!document.querySelector("canvas"),
        },
      };
    })()`
  );

  const out = {
    probed_at: new Date().toISOString(),
    linked: linked,
    port,
    ...probe,
  };
  mkdirSync("/workspace/whatsapp-scripts/out", { recursive: true });
  writeFileSync(OUT, JSON.stringify(out, null, 2));
  log(`wrote ${OUT} testids=${(probe.testids || []).length}`);
  console.log(JSON.stringify({ ok: true, linked, testid_count: (probe.testids || []).length, out: OUT }));
} catch (e) {
  log(`error: ${e.message}`);
  console.log(JSON.stringify({ ok: false, error: String(e.message).slice(0, 200) }));
  process.exitCode = 2;
} finally {
  await disconnect(browser, pageSessionId);
}
