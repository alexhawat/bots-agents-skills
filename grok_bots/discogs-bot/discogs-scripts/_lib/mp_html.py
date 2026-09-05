"""Parse Discogs marketplace HTML rows (tr.shortcut_navigable)."""
from __future__ import annotations

import html as html_mod
import re
from typing import Any

_ROW_RE = re.compile(
    r'<tr([^>]*class="[^"]*shortcut_navigable[^"]*"[^>]*)>(.*?)</tr>',
    re.IGNORECASE | re.DOTALL,
)
_ATTR_RE = re.compile(r'([a-zA-Z0-9_-]+)\s*=\s*"([^"]*)"')
_ATTR_BARE_RE = re.compile(r"([a-zA-Z0-9_-]+)\s*=\s*([^\s>]+)")
_ITEM_HREF_RE = re.compile(r'href="(/sell/item/(\d+)[^"]*)"', re.IGNORECASE)
_TITLE_RE = re.compile(
    r'<a[^>]*class="[^"]*item_description_title[^"]*"[^>]*>(.*?)</a>',
    re.IGNORECASE | re.DOTALL,
)
_PRICE_RE = re.compile(
    r'<span\s+class="price"([^>]*)>(.*?)</span>',
    re.IGNORECASE | re.DOTALL,
)
_SELLER_BTN_RE = re.compile(
    r'data-seller-username="([^"]+)"',
    re.IGNORECASE,
)
_SELLER_LINK_RE = re.compile(
    r'href="/seller/([^/"]+)/profile"',
    re.IGNORECASE,
)
_SHIP_RE = re.compile(
    r"Ships From:</span>\s*([^<]+)",
    re.IGNORECASE,
)
_MEDIA_COND_RE = re.compile(
    r'Media Condition:.*?<span>\s*([^<\n]+)',
    re.IGNORECASE | re.DOTALL,
)
_SLEEVE_COND_RE = re.compile(
    r'class="item_sleeve_condition"[^>]*>([^<]+)',
    re.IGNORECASE,
)
_TAG_RE = re.compile(r"<[^>]+>")


def _attrs(blob: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for m in _ATTR_RE.finditer(blob):
        out[m.group(1)] = m.group(2)
    for m in _ATTR_BARE_RE.finditer(blob):
        k, v = m.group(1), m.group(2)
        if k not in out:
            out[k] = v.strip('"')
    return out


def _strip_tags(s: str) -> str:
    return html_mod.unescape(_TAG_RE.sub("", s)).strip()


def parse_marketplace_rows(html: str) -> list[dict[str, Any]]:
    """Extract listings from sell/list or sell/release HTML pages."""
    rows: list[dict[str, Any]] = []
    for m in _ROW_RE.finditer(html):
        tr_attrs = _attrs(m.group(1))
        body = m.group(2)
        release_id = tr_attrs.get("data-release-id")

        item_id = None
        item_path = None
        im = _ITEM_HREF_RE.search(body)
        if im:
            item_path = im.group(1).split("?")[0]
            item_id = im.group(2)

        title = None
        tm = _TITLE_RE.search(body)
        if tm:
            title = _strip_tags(tm.group(1))

        currency = None
        price_value = None
        price_text = None
        pm = _PRICE_RE.search(body)
        if pm:
            pa = _attrs(pm.group(1))
            currency = pa.get("data-currency")
            pv = pa.get("data-pricevalue")
            if pv is not None:
                try:
                    price_value = float(pv)
                except ValueError:
                    price_value = pv
            price_text = _strip_tags(pm.group(2))

        seller = None
        sm = _SELLER_BTN_RE.search(body)
        if sm:
            seller = sm.group(1)
        else:
            sm2 = _SELLER_LINK_RE.search(body)
            if sm2:
                seller = sm2.group(1)

        ships_from = None
        sf = _SHIP_RE.search(body)
        if sf:
            ships_from = sf.group(1).strip()

        media = None
        mm = _MEDIA_COND_RE.search(body)
        if mm:
            media = mm.group(1).strip()
        sleeve = None
        sl = _SLEEVE_COND_RE.search(body)
        if sl:
            sleeve = sl.group(1).strip()

        rows.append(
            {
                "release_id": int(release_id) if release_id and release_id.isdigit() else release_id,
                "item_id": int(item_id) if item_id else None,
                "item_url": f"https://www.discogs.com{item_path}" if item_path else None,
                "title": title,
                "currency": currency,
                "price": price_value,
                "price_text": price_text,
                "seller": seller,
                "ships_from": ships_from,
                "media_condition": media,
                "sleeve_condition": sleeve,
            }
        )
    return rows
