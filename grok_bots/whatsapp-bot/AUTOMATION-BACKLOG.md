# WhatsApp-Bot automation backlog

Capture → script only; never invent endpoints. Skeletons below are OK; live HTTP replay needs capture.

Legend: **script** = runnable skeleton/docs · **runbook** = README-only · **HTTP replay N/A** = capture attempted 2026-09-07, zero endpoints (opaque WS/protobuf) · **browserUse Live** = operational UI path · **headless CDP Live** = Wave H DOM runner

Capture evidence: `out/wa-network-capture.json`, `out/wa-network-summary.md` (`events=0`, `endpoints=0`; cookie names only: `wa_ul`, `wa_web_access_token`, `wa_web_lang_pref`).

## Wave 0 — session
| slug | goal | status |
| --- | --- | --- |
| `qr-link` | Open web.whatsapp.com; request_box_help for QR scan once; confirm linked | **runbook** · scripts exist (docs) · capture attempted · HTTP replay N/A |
| `auth-export` | Export session artifacts to `/home/box/whatsapp-auth/auth.env` | **runbook** → `export_cookies.py` · capture attempted · HTTP replay N/A |
| `auth-check` | Prove keys present; optional weak probe; quiet fail → re-QR | **script** · capture attempted · HTTP replay N/A |

## Wave 1 — read
| slug | goal | status |
| --- | --- | --- |
| `chats-list` | List recent chats (name, unread, last preview) | **script** exists · capture attempted · **HTTP replay N/A** · **browserUse Live** · **headless CDP Live** |
| `messages-read` | Read last N messages in a named/jid chat | **script** exists · capture attempted · **HTTP replay N/A** · **browserUse Live** · **headless CDP Live** |
| `chats-search` | Search chats/contacts by query | **script** exists · capture attempted · **HTTP replay N/A** · **browserUse Live** · **headless CDP Live** |

## Wave 2 — write (confirm-gated)
| slug | goal | status |
| --- | --- | --- |
| `message-send` | Send text to chat (`--confirm`) | **script** exists (dry-run / browser docs) · capture attempted · **HTTP replay N/A** · **browserUse Live** · **headless CDP Live** (confirm-gated) |
| `message-mark-read` | Mark chat read (`--confirm`) | **script** exists · capture attempted · **HTTP replay N/A** · **browserUse Live** |

## Wave 3 — media / contacts
| slug | goal | status |
| --- | --- | --- |
| `media-download` | Download media from a message id | **script** exists · capture attempted · **HTTP replay N/A** · **browserUse Live** |
| `contact-info` | Profile/about for a contact | **script** exists · capture attempted · **HTTP replay N/A** · **browserUse Live** |

## Wave 4 — hygiene
| slug | goal | status |
| --- | --- | --- |
| `har-diff` | Diff captured traffic vs expected URL shapes | **script** exists · `expected-urls.json` empty (opaque capture) · HTTP replay N/A |
| `batch-runner` | Run a named batch of read-only scripts | **script** exists · capture attempted · HTTP replay N/A |


## Wave H — headless Chrome (CDP, no browserUse GUI)
| slug / module | goal | status |
| --- | --- | --- |
| `_lib/headless_cdp.mjs` | Connect DISPLAY→CDP; attach WA page; `assertLinked` | **Live** (2026-09-07) |
| `_lib/wa_dom.mjs` | listChats / searchChats / openChat / readMessages / sendText | **Live** · selectors from `out/wa-dom-probe.json` |
| `_lib/run_headless.mjs` | JSON CLI (`list-chats`, `search-chats`, `read-messages`, `send-text`) | **Live** · exit 0/1/2 |
| `chats-list` etc. `--mode=headless` | Python shells out to runner | **Live** · verified list-chats |
| Docs | `docs/headless-chrome.md` | **done** |

Notes: Node 20 needs `NODE_OPTIONS=--experimental-websocket`. Mutating send still requires `--confirm`. Prefer live `(N) WhatsApp` target over interstitial tabs. QR death → re-link (`qr-link`).

## Hard rules
- Mutating: `--confirm` required. No bulk spam. No inventing WA private APIs.
- Prefer captured network replay; fall back to **headless CDP** (`docs/headless-chrome.md`) or browserUse when protobuf/WS is opaque (current state — see `docs/browser-path.md`).
- Checkout of secrets never lands in GitHub.
