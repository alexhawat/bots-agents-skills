#!/usr/bin/env node
/**
 * Capture WhatsApp Web network traffic via sand-host CDP (Network domain).
 * NEVER logs Cookie / Authorization header values.
 */
import { writeFileSync, mkdirSync } from "node:fs";
import { dirname } from "node:path";
import {
  connectBrowser,
  listPageTargets,
  attachToPage,
  detachSession,
  readCookies,
} from "/home/box/sand-host/box-scripts/cdp-cookies.mjs";
import { SAND_BOX_CDP_PORT_BASE } from "/home/box/sand-host/box-scripts/box-contract.generated.mjs";

const OUT_JSON = "/workspace/whatsapp-scripts/out/wa-network-capture.json";
const OUT_MD = "/workspace/whatsapp-scripts/out/wa-network-summary.md";
const CAPTURE_MS = Number(process.env.WA_CAPTURE_MS || 75000);
const HOST_RE = /(whatsapp|facebook|fbcdn|whatsapp\.net)/i;
const SECRET_QUERY_KEYS = new Set([
  "token",
  "access_token",
  "auth",
  "authorization",
  "sig",
  "signature",
  "code",
  "session",
  "key",
  "api_key",
  "apikey",
  "secret",
  "password",
  "wa_web_access_token",
]);

function displayNumber() {
  const d = process.env.DISPLAY || "";
  const m = /:(\d+)/.exec(d);
  if (!m) throw new Error("DISPLAY unset");
  return Number.parseInt(m[1], 10);
}

function redactUrl(raw) {
  try {
    const u = new URL(raw);
    for (const k of [...u.searchParams.keys()]) {
      if (
        SECRET_QUERY_KEYS.has(k.toLowerCase()) ||
        /token|secret|auth|sig|key|password|session/i.test(k)
      ) {
        u.searchParams.set(k, "REDACTED");
      }
    }
    return u.toString();
  } catch {
    return String(raw).replace(
      /([?&](?:token|access_token|auth|authorization|sig|signature|code|session|key|api_key|apikey|secret|password|wa_web_access_token)=)[^&]*/gi,
      "$1REDACTED"
    );
  }
}

function hostOf(url) {
  try {
    return new URL(url).hostname.toLowerCase();
  } catch {
    return "";
  }
}

function pathPatternOf(url) {
  try {
    const u = new URL(url);
    // Collapse long hex/id segments for pattern summary
    const path = u.pathname
      .replace(/\/[0-9a-f]{16,}/gi, "/:hex")
      .replace(/\/\d{6,}/g, "/:id")
      .replace(/\/[A-Za-z0-9_-]{32,}/g, "/:tokenish");
    return `${u.hostname}${path}`;
  } catch {
    return url.split("?")[0];
  }
}

function isInterestingHost(host) {
  return HOST_RE.test(host);
}

function redactHeaders(headers) {
  if (!headers || typeof headers !== "object") return undefined;
  const out = {};
  for (const [k, v] of Object.entries(headers)) {
    const lk = k.toLowerCase();
    if (
      lk === "cookie" ||
      lk === "authorization" ||
      lk === "proxy-authorization" ||
      lk === "set-cookie" ||
      lk === "x-fb-session-id" ||
      /auth|token|cookie|secret|credential/i.test(lk)
    ) {
      out[k] = "REDACTED";
    } else {
      out[k] = typeof v === "string" && v.length > 200 ? `${v.slice(0, 80)}…` : v;
    }
  }
  return out;
}

function emptyResult(reason, extra = {}) {
  return {
    ok: false,
    failure: reason,
    capturedAt: new Date().toISOString(),
    captureMs: CAPTURE_MS,
    endpoints: [],
    events: [],
    cookieNames: [],
    ...extra,
  };
}

async function listAllTargets(browser) {
  const result = await browser.send("Target.getTargets");
  return (result.targetInfos ?? []).map((info) => ({
    targetId: info.targetId,
    type: info.type,
    url: info.url ?? "",
    title: info.title ?? "",
  }));
}

async function main() {
  mkdirSync(dirname(OUT_JSON), { recursive: true });
  const port = SAND_BOX_CDP_PORT_BASE + displayNumber();
  const meta = {
    display: process.env.DISPLAY || "",
    port,
    captureMs: CAPTURE_MS,
    startedAt: new Date().toISOString(),
  };

  let browser;
  try {
    browser = await connectBrowser(port);
  } catch (err) {
    const fail = emptyResult(`connectBrowser failed: ${String(err)}`, { meta });
    writeOutputs(fail);
    console.log(`fail connect port=${port}`);
    process.exit(0);
  }

  const byRequestId = new Map();
  const events = [];
  let networkEnabled = false;
  const sessions = [];

  try {
    // Cookie names only (values never written)
    let cookieNames = [];
    try {
      const jar = await readCookies(browser);
      const nameSet = new Set();
      for (const c of jar.values()) {
        const domain = String(c.domain || "").toLowerCase();
        if (!domain.includes("whatsapp")) continue;
        if (c.name) nameSet.add(`${c.name} @ ${domain}`);
      }
      cookieNames = [...nameSet].sort();
    } catch (err) {
      console.error(`cookie names read failed: ${String(err)}`);
    }

    const targets = await listAllTargets(browser);
    const waTargets = targets.filter((t) => {
      const u = (t.url || "").toLowerCase();
      return (
        u.includes("whatsapp") ||
        u.includes("facebook") ||
        (t.type === "page" && u.includes("web.whatsapp"))
      );
    });
    // Prefer page + service_worker for WA
    const attachList =
      waTargets.length > 0
        ? waTargets
        : (await listPageTargets(browser)).filter((t) =>
            /whatsapp/i.test(t.url)
          );

    browser.onEvent((msg) => {
      const method = msg.method;
      const params = msg.params || {};
      if (
        method !== "Network.requestWillBeSent" &&
        method !== "Network.responseReceived" &&
        method !== "Network.webSocketCreated" &&
        method !== "Network.webSocketWillSendHandshakeRequest" &&
        method !== "Network.webSocketHandshakeResponseReceived" &&
        method !== "Network.requestWillBeSentExtraInfo" &&
        method !== "Network.responseReceivedExtraInfo"
      ) {
        return;
      }

      if (method === "Network.requestWillBeSent") {
        const req = params.request || {};
        const url = req.url || "";
        const host = hostOf(url);
        if (!isInterestingHost(host) && !isInterestingHost(params.documentURL || "")) {
          // still keep if initiator is WA page and host matches later via response
          if (!HOST_RE.test(url) && !HOST_RE.test(params.documentURL || "")) return;
        }
        if (!HOST_RE.test(host) && !HOST_RE.test(url)) return;

        const entry = {
          requestId: params.requestId,
          method: req.method || "GET",
          url: redactUrl(url),
          resourceType: params.type || params.resourceType || "",
          mimeType: "",
          status: null,
          documentURL: params.documentURL
            ? redactUrl(params.documentURL)
            : undefined,
          timestamp: params.timestamp,
          wallTime: params.wallTime,
          initiatorType: params.initiator?.type,
        };
        // Do NOT store headers with secrets; only note presence
        if (req.headers) {
          const names = Object.keys(req.headers).map((h) => h.toLowerCase());
          entry.requestHeaderNames = names.filter(
            (n) => !["cookie", "authorization", "proxy-authorization"].includes(n)
          );
          if (names.includes("cookie")) entry.hasCookieHeader = true;
          if (names.includes("authorization")) entry.hasAuthorizationHeader = true;
        }
        byRequestId.set(params.requestId, entry);
        events.push({
          kind: "request",
          ...entry,
        });
        return;
      }

      if (method === "Network.responseReceived") {
        const res = params.response || {};
        const url = res.url || "";
        const host = hostOf(url);
        if (!HOST_RE.test(host) && !HOST_RE.test(url)) return;
        const prev = byRequestId.get(params.requestId) || {
          requestId: params.requestId,
          method: "",
          url: redactUrl(url),
        };
        prev.mimeType = res.mimeType || prev.mimeType || "";
        prev.status = res.status ?? null;
        prev.resourceType = params.type || prev.resourceType || "";
        prev.url = redactUrl(url);
        if (res.headers) {
          const names = Object.keys(res.headers).map((h) => h.toLowerCase());
          prev.responseHeaderNames = names.filter((n) => n !== "set-cookie");
          if (names.includes("set-cookie")) prev.hasSetCookie = true;
        }
        byRequestId.set(params.requestId, prev);
        events.push({
          kind: "response",
          requestId: params.requestId,
          method: prev.method,
          url: prev.url,
          resourceType: prev.resourceType,
          mimeType: prev.mimeType,
          status: prev.status,
        });
        return;
      }

      if (method === "Network.webSocketCreated") {
        const url = params.url || "";
        if (!HOST_RE.test(hostOf(url)) && !HOST_RE.test(url)) return;
        const entry = {
          requestId: params.requestId,
          method: "WS",
          url: redactUrl(url),
          resourceType: "websocket",
          mimeType: "",
          status: null,
        };
        byRequestId.set(params.requestId, entry);
        events.push({ kind: "websocketCreated", ...entry });
        return;
      }

      if (method === "Network.webSocketWillSendHandshakeRequest") {
        const req = params.request || {};
        const url = req.url || "";
        if (!HOST_RE.test(hostOf(url)) && !HOST_RE.test(url)) return;
        events.push({
          kind: "websocketHandshakeRequest",
          requestId: params.requestId,
          method: "GET",
          url: redactUrl(url),
          resourceType: "websocket",
          mimeType: "",
          // header NAMES only
          requestHeaderNames: req.headers
            ? Object.keys(req.headers)
                .map((h) => h.toLowerCase())
                .filter((n) => !["cookie", "authorization"].includes(n))
            : [],
        });
        return;
      }

      if (method === "Network.webSocketHandshakeResponseReceived") {
        const res = params.response || {};
        const url = res.url || "";
        // url may be empty; update by requestId
        const prev = byRequestId.get(params.requestId);
        if (prev) {
          prev.status = res.status ?? prev.status;
          prev.mimeType = res.headers?.["content-type"] || prev.mimeType;
        }
        events.push({
          kind: "websocketHandshakeResponse",
          requestId: params.requestId,
          url: prev?.url || (url ? redactUrl(url) : ""),
          status: res.status ?? null,
          resourceType: "websocket",
          mimeType: "",
        });
      }
    });

    // Enable Network on interesting targets
    for (const t of attachList) {
      try {
        const sessionId = await attachToPage(browser, t.targetId);
        if (!sessionId) {
          console.error(`attach failed target=${t.targetId} type=${t.type}`);
          continue;
        }
        sessions.push(sessionId);
        await browser.send(
          "Network.enable",
          {
            maxTotalBufferSize: 0,
            maxResourceBufferSize: 0,
            maxPostDataSize: 0,
          },
          sessionId
        );
        networkEnabled = true;
        console.error(
          `Network.enable ok target=${t.type} url=${String(t.url).slice(0, 80)} session=${sessionId.slice(0, 8)}…`
        );
      } catch (err) {
        console.error(`Network.enable failed for ${t.type}: ${String(err)}`);
      }
    }

    // Also try auto-attach for workers/iframes that appear during capture
    try {
      await browser.send("Target.setAutoAttach", {
        autoAttach: true,
        waitForDebuggerOnStart: false,
        flatten: true,
      });
      browser.onEvent(async (msg) => {
        if (msg.method !== "Target.attachedToTarget") return;
        const info = msg.params?.targetInfo;
        const sid = msg.params?.sessionId;
        if (!sid || !info) return;
        const u = (info.url || "").toLowerCase();
        if (
          !(
            u.includes("whatsapp") ||
            u.includes("facebook") ||
            u.includes("fbcdn") ||
            info.type === "service_worker" ||
            info.type === "shared_worker"
          )
        ) {
          return;
        }
        try {
          await browser.send(
            "Network.enable",
            {
              maxTotalBufferSize: 0,
              maxResourceBufferSize: 0,
              maxPostDataSize: 0,
            },
            sid
          );
          sessions.push(sid);
          networkEnabled = true;
          console.error(`auto Network.enable ${info.type} ${u.slice(0, 60)}`);
        } catch {
          /* ignore */
        }
      });
    } catch (err) {
      console.error(`setAutoAttach: ${String(err)}`);
    }

    if (!networkEnabled) {
      const fail = emptyResult("Network.enable failed on all targets", {
        meta,
        targets: attachList.map((t) => ({
          type: t.type,
          url: String(t.url).slice(0, 120),
        })),
        cookieNames,
      });
      writeOutputs(fail);
      console.log("fail Network.enable");
      return;
    }

    console.error(`capturing for ${CAPTURE_MS}ms…`);
    await new Promise((r) => setTimeout(r, CAPTURE_MS));

    const endpoints = [...byRequestId.values()].map((e) => ({
      method: e.method || "",
      url: e.url,
      resourceType: e.resourceType || "",
      mimeType: e.mimeType || "",
      status: e.status,
      hasCookieHeader: e.hasCookieHeader || false,
      hasAuthorizationHeader: e.hasAuthorizationHeader || false,
    }));

    const result = {
      ok: true,
      failure: null,
      capturedAt: new Date().toISOString(),
      captureMs: CAPTURE_MS,
      meta: {
        ...meta,
        endedAt: new Date().toISOString(),
        attachedTargets: attachList.map((t) => ({
          type: t.type,
          url: String(t.url).slice(0, 160),
        })),
        sessionCount: sessions.length,
        eventCount: events.length,
      },
      endpoints,
      events: events.slice(0, 2000), // cap
      cookieNames,
    };
    writeOutputs(result);
    console.log(
      `ok events=${events.length} endpoints=${endpoints.length} patterns=${summarizePatterns(endpoints).length} cookies=${cookieNames.length}`
    );
  } catch (err) {
    const fail = emptyResult(`capture error: ${String(err)}`, { meta });
    writeOutputs(fail);
    console.log(`fail error=${String(err)}`);
  } finally {
    for (const sid of sessions) {
      await detachSession(browser, sid).catch(() => {});
    }
    try {
      browser.close();
    } catch {
      /* ignore */
    }
  }
}

function summarizePatterns(endpoints) {
  const map = new Map();
  for (const e of endpoints) {
    const pat = `${e.method || "?"} ${pathPatternOf(e.url)}`;
    const prev = map.get(pat) || {
      pattern: pat,
      method: e.method,
      hostPath: pathPatternOf(e.url),
      resourceTypes: new Set(),
      mimeTypes: new Set(),
      count: 0,
      sampleUrl: e.url.split("?")[0],
    };
    prev.count += 1;
    if (e.resourceType) prev.resourceTypes.add(e.resourceType);
    if (e.mimeType) prev.mimeTypes.add(e.mimeType);
    map.set(pat, prev);
  }
  return [...map.values()]
    .map((p) => ({
      ...p,
      resourceTypes: [...p.resourceTypes],
      mimeTypes: [...p.mimeTypes],
    }))
    .sort((a, b) => b.count - a.count || a.pattern.localeCompare(b.pattern));
}

function looksRestOrGraphql(endpoints) {
  const restish = [];
  const wsOnly = [];
  for (const e of endpoints) {
    const u = e.url.toLowerCase();
    const rt = (e.resourceType || "").toLowerCase();
    if (rt === "websocket" || e.method === "WS") {
      wsOnly.push(e);
      continue;
    }
    if (
      /\/graphql|\/api\/|\/v\d+\//i.test(u) ||
      (e.mimeType || "").includes("json") ||
      rt === "xhr" ||
      rt === "fetch"
    ) {
      restish.push(e);
    }
  }
  return { restish, wsOnly };
}

function writeOutputs(result) {
  const patterns = summarizePatterns(result.endpoints || []);
  const { restish, wsOnly } = looksRestOrGraphql(result.endpoints || []);
  const json = {
    ...result,
    summary: {
      uniquePatterns: patterns.length,
      endpointCount: (result.endpoints || []).length,
      restOrGraphqlLooking: restish.length,
      websocketLooking: wsOnly.length,
      topPatterns: patterns.slice(0, 40).map((p) => ({
        pattern: p.pattern,
        count: p.count,
        resourceTypes: p.resourceTypes,
        mimeTypes: p.mimeTypes,
        sampleUrl: p.sampleUrl,
      })),
    },
  };
  writeFileSync(OUT_JSON, JSON.stringify(json, null, 2), { mode: 0o644 });

  const lines = [];
  lines.push("# WhatsApp Web network capture summary");
  lines.push("");
  lines.push(`- Captured at: ${result.capturedAt}`);
  lines.push(`- DISPLAY/port: ${result.meta?.display || process.env.DISPLAY} / ${result.meta?.port}`);
  lines.push(`- Duration: ${result.captureMs}ms`);
  lines.push(`- OK: ${result.ok}`);
  if (result.failure) lines.push(`- Failure: ${result.failure}`);
  lines.push(`- Endpoints: ${(result.endpoints || []).length}`);
  lines.push(`- Unique host/path patterns: ${patterns.length}`);
  lines.push(
    `- REST/GraphQL-looking (xhr/fetch/json/api/graphql): ${restish.length}`
  );
  lines.push(`- WebSocket-looking: ${wsOnly.length}`);
  lines.push(
    `- API shape: ${
      restish.length === 0 && wsOnly.length > 0
        ? "mostly/only WebSocket (plus static assets if any)"
        : restish.length > 0
          ? "HTTP REST/XHR/GraphQL-looking endpoints present (plus WS if any)"
          : patterns.length === 0
            ? "no matching traffic captured"
            : "HTTP asset/other traffic; see patterns"
    }`
  );
  lines.push("");
  lines.push("## Cookie names (whatsapp domains, names only)");
  lines.push("");
  if ((result.cookieNames || []).length === 0) {
    lines.push("_none_");
  } else {
    for (const n of result.cookieNames) lines.push(`- \`${n}\``);
  }
  lines.push("");
  lines.push("## Unique URL path patterns");
  lines.push("");
  if (patterns.length === 0) {
    lines.push("_empty — no whatsapp/facebook/fbcdn hosts observed during window_");
  } else {
    for (const p of patterns) {
      lines.push(
        `- \`${p.pattern}\` ×${p.count} types=[${p.resourceTypes.join(",")}] mime=[${p.mimeTypes.join(",")}]`
      );
    }
  }
  lines.push("");
  lines.push("## Top 20 (redacted samples)");
  lines.push("");
  for (const p of patterns.slice(0, 20)) {
    lines.push(`1. \`${p.pattern}\` — sample \`${p.sampleUrl}\``);
  }
  lines.push("");
  writeFileSync(OUT_MD, lines.join("\n"), { mode: 0o644 });
}

await main();
