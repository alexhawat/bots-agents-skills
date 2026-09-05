"""Marketplace row parsing — the layer most exposed to Discogs markup drift."""
from __future__ import annotations

from _lib.mp_html import parse_marketplace_rows


def test_parses_the_captured_sample_row(marketplace_row_html):
    rows = parse_marketplace_rows(marketplace_row_html)
    assert rows, "sample-row.html should yield at least one listing"
    r = rows[0]
    assert isinstance(r["item_id"], int)
    assert r["item_url"].startswith("https://www.discogs.com/sell/item/")
    assert r["seller"]
    assert r["price"] is None or isinstance(r["price"], (float, str))


def test_every_documented_key_is_present(marketplace_row_html):
    expected = {
        "release_id", "item_id", "item_url", "title", "currency", "price",
        "price_text", "seller", "ships_from", "media_condition", "sleeve_condition",
    }
    for row in parse_marketplace_rows(marketplace_row_html):
        assert set(row) == expected


def test_empty_and_junk_html_yield_no_rows():
    assert parse_marketplace_rows("") == []
    assert parse_marketplace_rows("<html><body><p>nothing</p></body></html>") == []


def test_ids_are_ints_and_price_is_float():
    html = """
    <tr class="shortcut_navigable" data-release-id="249504">
      <td><a class="item_description_title" href="/sell/item/12345-x">Some &amp; Title</a></td>
      <td><span class="price" data-currency="EUR" data-pricevalue="12.50">&euro;12.50</span></td>
      <td><a href="/seller/AcmeRecords/profile">AcmeRecords</a></td>
      <td><span>Ships From:</span> Netherlands</td>
    </tr>
    """
    (row,) = parse_marketplace_rows(html)
    assert row["release_id"] == 249504
    assert row["item_id"] == 12345
    assert row["price"] == 12.50
    assert row["currency"] == "EUR"
    assert row["seller"] == "AcmeRecords"
    assert row["title"] == "Some & Title"  # entities unescaped


def test_seller_button_attribute_wins_over_profile_link():
    html = """
    <tr class="shortcut_navigable" data-release-id="1">
      <td><a class="item_description_title" href="/sell/item/1-x">T</a></td>
      <td data-seller-username="ButtonSeller"></td>
      <td><a href="/seller/LinkSeller/profile">LinkSeller</a></td>
    </tr>
    """
    (row,) = parse_marketplace_rows(html)
    assert row["seller"] == "ButtonSeller"


def test_non_numeric_price_falls_back_to_the_raw_string():
    html = """
    <tr class="shortcut_navigable" data-release-id="1">
      <td><a class="item_description_title" href="/sell/item/1-x">T</a></td>
      <td><span class="price" data-currency="EUR" data-pricevalue="N/A">n/a</span></td>
    </tr>
    """
    (row,) = parse_marketplace_rows(html)
    assert row["price"] == "N/A"


def test_missing_fields_become_none_rather_than_raising():
    html = '<tr class="shortcut_navigable"><td>nothing useful</td></tr>'
    (row,) = parse_marketplace_rows(html)
    assert row["item_id"] is None
    assert row["seller"] is None
    assert row["price"] is None
