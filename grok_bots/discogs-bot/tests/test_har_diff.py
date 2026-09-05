"""har-diff: drift detection over captured GraphQL operations."""
from __future__ import annotations

import json

import pytest

SHA_A = "d07fa55f88404b5d0e5253faf962ed104ad1efd3af871c9281b76e874d4a2bf4"
SHA_B = "ab4a277f4c5d9da56ba17d4b88643c51a1935f500813133c55fe5a340625d06f"


@pytest.fixture(scope="module")
def diff(request):
    from conftest import load_script
    return load_script("har-diff", "diff")


def test_extracts_operations_from_the_shipped_curls_fixture(diff, scripts_root):
    ops = diff.extract_ops(scripts_root / "har-diff" / "fixtures" / "sample-curls.txt")
    assert "AddReleasesToWantlist" in ops
    assert SHA_A in ops["AddReleasesToWantlist"]


def test_known_operations_fixture_matches_the_sample_curls(diff, scripts_root):
    expected = diff.load_fixture(scripts_root / "har-diff" / "fixtures" / "known-operations.json")
    observed = diff.extract_ops(scripts_root / "har-diff" / "fixtures" / "sample-curls.txt")
    for name, sha in expected.items():
        if name in observed and observed[name]:
            assert sha in observed[name], f"{name} drifted"


def test_extracts_from_the_redacted_wave4_har(diff, scripts_root):
    """The shipped HAR must stay diffable — READMEs point at it."""
    ops = diff.extract_ops(scripts_root / "wantlist-add-remove" / "capture" / "wave4.har")
    assert "AddReleaseToCollection" in ops
    assert "RemoveCollectionItemNote" in ops


def test_url_encoded_get_persisted_queries_are_found(diff, tmp_path):
    p = tmp_path / "curls.txt"
    p.write_text(
        "curl 'https://www.discogs.com/service/catalog/api/graphql"
        "?operationName=ViewerCollectionListData"
        "&extensions=%7B%22persistedQuery%22%3A%7B%22sha256Hash%22%3A%22" + SHA_A + "%22%7D%7D'\n"
    )
    ops = diff.extract_ops(p)
    assert SHA_A in ops["ViewerCollectionListData"]


def test_drift_is_detected_when_a_hash_changes(diff, tmp_path):
    fixture = tmp_path / "known.json"
    fixture.write_text(json.dumps({"operations": {"AddReleasesToWantlist": SHA_B}}))
    expected = diff.load_fixture(fixture)
    observed = {"AddReleasesToWantlist": {SHA_A}}
    assert expected["AddReleasesToWantlist"] not in observed["AddReleasesToWantlist"]


def test_a_named_op_with_no_hash_is_not_a_false_match(diff, tmp_path):
    p = tmp_path / "curls.txt"
    p.write_text('--data-raw \'{"operationName":"AddReleasesToWantlist","variables":"X"}\'\n')
    ops = diff.extract_ops(p)
    assert ops.get("AddReleasesToWantlist") == set()


def test_malformed_har_falls_back_to_text_scraping(diff, tmp_path):
    p = tmp_path / "broken.har"
    p.write_text(
        f'not json at all operationName="AddReleasesToWantlist" sha256Hash="{SHA_A}"'
    )
    ops = diff.extract_ops(p)
    assert "AddReleasesToWantlist" in ops
