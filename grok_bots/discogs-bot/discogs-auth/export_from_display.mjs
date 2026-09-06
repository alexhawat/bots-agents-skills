#!/usr/bin/env node
// Read Discogs cookies from THIS agent's Chrome (DISPLAY → CDP port) via
// official sand-host cdp-cookies. Write auth.env. Never print values.
// Never copy the jar into the workspace checkout — only a path pointer.
import { writeFileSync, chmodSync, mkdirSync } from "node:fs";
import { dirname } from "node:path";
import { connectBrowser, readCookies } from "/home/box/sand-host/box-scripts/cdp-cookies.mjs";
import { SAND_BOX_CDP_PORT_BASE } from "/home/box/sand-host/box-scripts/box-contract.generated.mjs";

// Path resolution mirrors _lib/auth.py and export_cookies.py so the exporter
// and the loader can never disagree about where the jar lives.
//
// Resolved per call, never snapshotted into a module constant: this file is
// usually run as a CLI with the env already set, but it is also importable,
// and a caller that sets DISCOGS_* after import must still get the path it
// asked for. Same contract as out_path()/work_dir() in export_cookies.py.
export function outPath() {
  if (process.env.DISCOGS_AUTH_ENV) return process.env.DISCOGS_AUTH_ENV;
  const base = process.env.DISCOGS_AUTH_DIR || "/home/box/discogs-auth";
  return `${base}/auth.env`;
}

export function workDir() {
  return process.env.DISCOGS_WORK_AUTH || "/workspace/discogs-scripts/_auth";
}

const UA =
  "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36";

function displayNumber() {
  const d = process.env.DISPLAY || "";
  const m = /:(\d+)/.exec(d);
  if (!m) throw new Error("DISPLAY unset");
  return Number.parseInt(m[1], 10);
}

const port = SAND_BOX_CDP_PORT_BASE + displayNumber();
const browser = await connectBrowser(port);
let jar;
try {
  jar = await readCookies(browser);
} finally {
  browser.close();
}

const byName = new Map();
for (const c of jar.values()) {
  const domain = String(c.domain || "").toLowerCase();
  if (!domain.includes("discogs")) continue;
  if (!c.name || !c.value) continue;
  const prev = byName.get(c.name);
  // Prefer www / .www over login.discogs.com for site session cookies
  const score = (domain.includes("www.discogs") ? 2 : 0) + (domain === ".discogs.com" ? 1 : 0);
  const prevScore = prev
    ? (String(prev.domain).includes("www.discogs") ? 2 : 0) +
      (prev.domain === ".discogs.com" ? 1 : 0)
    : -1;
  if (!prev || score >= prevScore) byName.set(c.name, c);
}

const names = [...byName.keys()];
if (!names.includes("session") && !names.includes("sid")) {
  console.log(`fail port=${port} discogs_named=${names.length} no session/sid`);
  process.exit(1);
}
const parts = names.map((n) => `${n}=${byName.get(n).value}`);
const text = `COOKIE=${parts.join("; ")}\nUSER_AGENT=${UA}\n`;
const out = outPath();
mkdirSync(dirname(out), { recursive: true });
writeFileSync(out, text, { mode: 0o600 });
chmodSync(out, 0o600);
// Pointer only — never duplicate the secret into the checkout.
const workDirPath = workDir();
mkdirSync(workDirPath, { recursive: true });
writeFileSync(`${workDirPath}/AUTH_PATH.txt`, `${out}\n`, { mode: 0o644 });
console.log(
  `ok source=cdp:${port} cookies=${names.length} names=${JSON.stringify(names.sort())} path=${out}`
);
