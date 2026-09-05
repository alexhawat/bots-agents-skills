# Capture notes — vinyl-photo-identify

Hybrid script: no dedicated Discogs image-search capture.

Reuses autocomplete + UserReleaseData from:
- `../barcode-or-catno-lookup/capture/` (barcode.har, curls.txt)
- `../price-suggest/` (UserReleaseData sha)

OCR is local (`tesseract`); vision `--query` is supplied by the agent.
