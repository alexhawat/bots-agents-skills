"""Collection row normalization and the GraphQL failure branches."""
from __future__ import annotations

import json

import pytest
from _lib import collection_fetch
from _lib.collection_fetch import (
    CSV_COLUMNS,
    artist_blob,
    fetch_page,
    format_blob,
    item_to_row,
    primary_label_catno,
    public_row,
    year_int,
)
from _lib.errors import DiscogsAPIError, DiscogsAuthError


def test_artist_blob_joins_and_falls_back_to_nested_name():
    rel = {"primaryArtists": [
        {"displayName": "A"},
        {"displayName": None, "artist": {"name": "B"}},
        {"displayName": ""},
    ]}
    assert artist_blob(rel) == "A / B"


def test_artist_blob_handles_missing_and_null():
    assert artist_blob({}) == ""
    assert artist_blob({"primaryArtists": None}) == ""


def test_format_blob_omits_quantity_one_but_keeps_multiples():
    single = {"formats": [{"name": "Vinyl", "quantity": "1", "description": ["LP"]}]}
    assert format_blob(single) == "Vinyl — LP"
    double = {"formats": [{"name": "Vinyl", "quantity": "2", "description": ["LP"]}]}
    assert format_blob(double) == "2 x Vinyl — LP"


def test_format_blob_drops_empty_names():
    """Regression: the pre-_lib copy appended '' for nameless formats."""
    rel = {"formats": [{"name": "", "quantity": "1", "description": ["LP"]}]}
    assert format_blob(rel) == "LP"
    assert not format_blob(rel).startswith(" —")


@pytest.mark.parametrize(
    ("released", "expected"),
    [("1984", 1984), ("1984-05-01", 1984), ("", None), (None, None), ("n/a", None), (1999, 1999)],
)
def test_year_int(released, expected):
    assert year_int(released) == expected


def test_primary_label_prefers_the_LABEL_role():
    rel = {"labels": [
        {"labelRole": "SERIES", "catalogNumber": "S-1", "label": {"name": "Series"}},
        {"labelRole": "LABEL", "catalogNumber": "L-1", "label": {"name": "Label"}},
    ]}
    assert primary_label_catno(rel) == ("Label", "L-1")


def test_primary_label_falls_back_to_first_and_normalizes_none_catno():
    assert primary_label_catno({"labels": []}) == ("", "")
    rel = {"labels": [{"labelRole": "SERIES", "catalogNumber": "none",
                       "label": {"name": "Only"}}]}
    assert primary_label_catno(rel) == ("Only", "")


def test_item_to_row_builds_absolute_urls_and_keeps_all_csv_columns():
    item = {
        "discogsId": 42,
        "addedAt": "2026-01-01T00:00:00Z",
        "folder": {"name": "Tango"},
        "release": {"discogsId": 7, "title": "T", "siteUrl": "/release/7-T",
                    "released": "1984", "primaryArtists": [{"displayName": "A"}],
                    "formats": [{"name": "Vinyl", "quantity": "1", "description": []}],
                    "labels": [{"labelRole": "LABEL", "catalogNumber": "C-1",
                                "label": {"name": "L"}}]},
    }
    row = item_to_row(item)
    assert row["url"] == "https://www.discogs.com/release/7-T"
    assert row["collection_item_id"] == 42
    assert row["release_id"] == 7
    assert row["folder"] == "Tango"
    assert set(CSV_COLUMNS) <= set(row)


def test_item_to_row_synthesizes_a_url_when_siteurl_is_absent():
    row = item_to_row({"discogsId": 1, "release": {"discogsId": 99}})
    assert row["url"] == "https://www.discogs.com/release/99"


def test_public_row_strips_the_private_release_blob():
    row = item_to_row({"discogsId": 1, "release": {"discogsId": 2}})
    assert "_release" in row
    assert "_release" not in public_row(row)
    assert list(public_row(row)) == CSV_COLUMNS


def _patch_response(monkeypatch, payload):
    monkeypatch.setattr(collection_fetch, "graphql_get", lambda *a, **k: payload)


def test_graphql_errors_are_reported_as_api_errors_not_dead_session(monkeypatch):
    """Regression: viewer was checked first, so real API errors read as 'session dead'."""
    _patch_response(monkeypatch, {"errors": [{"message": "PersistedQueryNotFound"}],
                                  "data": {"viewer": None}})
    with pytest.raises(DiscogsAPIError) as ei:
        fetch_page({"COOKIE": "x"})
    assert "PersistedQueryNotFound" in str(ei.value)


def test_null_viewer_without_errors_is_an_auth_error(monkeypatch):
    _patch_response(monkeypatch, {"data": {"viewer": None}})
    with pytest.raises(DiscogsAuthError):
        fetch_page({"COOKIE": "x"})


def test_fetch_page_returns_items_and_total(monkeypatch):
    _patch_response(monkeypatch, {"data": {"viewer": {"offsetCollectionItems": {
        "collectionItems": [{"discogsId": 1}], "totalCount": 1}}}})
    items, total = fetch_page({"COOKIE": "x"})
    assert total == 1
    assert items == [{"discogsId": 1}]


def test_iter_stops_at_limit(monkeypatch):
    page = {"data": {"viewer": {"offsetCollectionItems": {
        "collectionItems": [{"discogsId": i} for i in range(50)], "totalCount": 500}}}}
    _patch_response(monkeypatch, page)
    got = list(collection_fetch.iter_collection_items({"COOKIE": "x"}, limit=7, progress=False))
    assert len(got) == 7


def test_rows_from_the_redacted_har_fixture_normalize(collection_har):
    """The shipped fixture must stay parseable — it backs `make smoke`."""
    har = json.loads(collection_har.read_text())
    payload = json.loads(har["log"]["entries"][0]["response"]["content"]["text"])
    items = payload["data"]["viewer"]["offsetCollectionItems"]["collectionItems"]
    assert items
    for row in (item_to_row(i) for i in items):
        assert row["release_id"]
        assert row["url"].startswith("https://www.discogs.com/release/")
