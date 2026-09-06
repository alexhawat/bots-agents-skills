"""Token classification, hit normalization, dedupe and ranking."""
from __future__ import annotations

import pytest
from _lib.discogs_search import (
    SearchHit,
    extract_tokens,
    hit_from_autocomplete,
    hit_from_public,
    looks_like_barcode,
    looks_like_catno,
    merge_hits,
    rank_hits,
)


@pytest.mark.parametrize("tok", ["0123456789012", "5099749534728", "012345678"])
def test_barcodes_recognized(tok):
    assert looks_like_barcode(tok)


@pytest.mark.parametrize("tok", ["DMO-55454", "WARP123", "abc", "1234567"])
def test_non_barcodes_rejected(tok):
    assert not looks_like_barcode(tok)


def test_barcode_ignores_separators():
    assert looks_like_barcode("5099 749-534728")


def test_catno_and_barcode_are_mutually_exclusive():
    assert looks_like_catno("DMO-55454")
    assert not looks_like_catno("5099749534728")


def test_extract_tokens_splits_catnos_barcodes_and_free_text():
    catnos, barcodes, hints = extract_tokens("Aphex Twin WARP 123 5099749534728")
    assert any("WARP" in c.upper() for c in catnos)
    assert "5099749534728" in barcodes
    assert "Aphex" in hints and "Twin" in hints


def test_extract_tokens_dedupes_case_insensitively():
    catnos, _, _ = extract_tokens("DMO-55454 dmo-55454")
    assert len(catnos) == 1


def test_extract_tokens_on_empty_input():
    assert extract_tokens("") == ([], [], "")
    assert extract_tokens("   ") == ([], [], "")


def test_hit_from_public_splits_artist_from_title():
    hit = hit_from_public({"id": 7, "type": "release", "title": "Aphex Twin - Xtal",
                           "year": "1992", "uri": "/release/7", "format": ["Vinyl"]})
    assert hit.artists == "Aphex Twin"
    assert hit.title == "Xtal"
    assert hit.url == "https://www.discogs.com/release/7"
    assert hit.is_release


def test_hit_from_public_joins_barcode_list_when_no_catno():
    hit = hit_from_public({"id": 1, "type": "release", "title": "T",
                           "barcode": ["111", "222"]})
    assert hit.catno == "111, 222"


def test_hit_from_autocomplete_uses_key_release_for_masters():
    hit = hit_from_autocomplete({
        "__typename": "MasterRelease", "discogsId": 5,
        "keyRelease": {"title": "KeyTitle", "released": "1999",
                       "primaryArtists": [{"displayName": "X"}]},
    })
    assert hit.title == "KeyTitle"
    assert hit.artists == "X"
    assert not hit.is_release


def test_merge_dedupes_the_same_release_from_both_sources():
    hits = [
        SearchHit(kind="release", discogs_id=1, title="T", source="public"),
        SearchHit(kind="Release", discogs_id=1, title="T", source="autocomplete"),
    ]
    merged = merge_hits(hits)
    assert len(merged) == 1
    assert merged[0].source == "autocomplete"  # autocomplete preferred


def test_merge_drops_hits_without_an_id():
    assert merge_hits([SearchHit(kind="release", discogs_id=0, title="T")]) == []


def test_merge_keeps_distinct_kinds_of_the_same_id():
    hits = [
        SearchHit(kind="Release", discogs_id=1, title="T"),
        SearchHit(kind="Artist", discogs_id=1, title="A"),
    ]
    assert len(merge_hits(hits)) == 2


def test_ranking_puts_releases_above_masters_above_artists():
    hits = [
        SearchHit(kind="Artist", discogs_id=3, title="A"),
        SearchHit(kind="MasterRelease", discogs_id=2, title="M"),
        SearchHit(kind="Release", discogs_id=1, title="R"),
    ]
    assert [h.discogs_id for h in rank_hits(hits)] == [1, 2, 3]


def test_exact_catno_match_outranks_a_plain_release():
    hits = [
        SearchHit(kind="Release", discogs_id=1, title="Other"),
        SearchHit(kind="Release", discogs_id=2, title="Match", catno="DMO-55454"),
    ]
    ranked = rank_hits(hits, query="DMO-55454", prefer_tokens=["DMO-55454"])
    assert ranked[0].discogs_id == 2


def test_ranking_is_stable_for_an_empty_list():
    assert rank_hits([]) == []
