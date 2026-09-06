"""Buyer purchases parsing. Orders have no GraphQL API, so HTML drift is the risk."""
from __future__ import annotations

from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture(scope="module")
def orders():
    from conftest import load_script
    return load_script("orders-list", "orders")


@pytest.fixture(scope="module")
def purchases_html() -> str:
    return (FIXTURES / "purchases.html").read_text()


def test_parses_every_order_row(orders, purchases_html):
    rows = orders.parse_purchases(purchases_html)
    assert [r["order_id"] for r in rows] == ["1000000-1", "1000000-2"]


def test_rows_without_an_order_link_are_skipped(orders, purchases_html):
    assert len(orders.parse_purchases(purchases_html)) == 2  # third row dropped


def test_extracts_seller_total_date_and_status(orders, purchases_html):
    first = orders.parse_purchases(purchases_html)[0]
    assert first["seller"] == "AcmeRecords"
    assert "24.00" in first["total"]
    assert "Sep 1, 2026" in first["date"]
    assert first["status"] == "Shipped"


def test_status_comes_from_the_aria_label(orders, purchases_html):
    second = orders.parse_purchases(purchases_html)[1]
    assert second["status"] == "Order Received"


def test_duplicate_order_ids_are_collapsed(orders):
    row = (
        '<tr class="shortcut_navigable"><td data-header="Order: ">'
        '<a href="/sell/order/1000000-1"> 1000000-1 </a></td></tr>'
    )
    assert len(orders.parse_purchases(row * 3)) == 1


def test_empty_html_yields_no_orders(orders):
    assert orders.parse_purchases("") == []
    assert orders.parse_purchases("<html><body>no table</body></html>") == []


def test_every_row_has_the_documented_keys(orders, purchases_html):
    for row in orders.parse_purchases(purchases_html):
        assert set(row) == {"order_id", "date", "seller", "status", "total"}


def test_missing_optional_cells_become_none_not_crash(orders):
    row = (
        '<tr class="shortcut_navigable"><td data-header="Order: ">'
        '<a href="/sell/order/2000000-9"> 2000000-9 </a></td></tr>'
    )
    (parsed,) = orders.parse_purchases(row)
    assert parsed["order_id"] == "2000000-9"
    assert parsed["seller"] is None
    assert parsed["total"] is None
