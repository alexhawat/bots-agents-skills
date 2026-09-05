#!/usr/bin/env node
// Read Discogs cookies from THIS agent's Chrome (DISPLAY → CDP port) via
// official sand-host cdp-cookies. Write auth.env. Never print values.
import { writeFileSync, chmodSync, copyFileSync, mkdirSync } from "node:fs";
import { connectBrowser, readCookies } from "/home/box/sand-host/box-scripts/cdp-cookies.mjs";
import { SAND_BOX_CDP_PORT_BASE } from "/home/box/sand-host/box-scripts/box-contract.generated.mjs";

const OUT = "/home/box/discogs-auth/auth.env";
const WORK = "/workspace/discogs-scripts/_auth/auth.env";
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
writeFileSync(OUT, text, { mode: 0o600 });
chmodSync(OUT, 0o600);
mkdirSync("/workspace/discogs-scripts/_auth", { recursive: true });
copyFileSync(OUT, WORK);
chmodSync(WORK, 0o600);
console.log(
  `ok source=cdp:${port} cookies=${names.length} names=${JSON.stringify(names.sort())} path=${OUT}`
);
