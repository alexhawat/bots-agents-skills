# Capture notes — marketplace-add-to-cart

- Date: 2026-09-05
- HAR: `wave4.har` (copy of wantlist-add-remove/capture/wave4.har)
- Curls: `../../wantlist-add-remove/capture/curls.txt`
- Cart add (from curls / analytics referrer in HAR):
  - `GET https://www.discogs.com/sell/cart/?add=4345527582&ev=…` (ev redacted/omitted in script)
- Follow-on: `POST /sell/cart/update_tax` (tax refresh; not required for add)
- Cookies/secrets redacted; never log Cookie.
