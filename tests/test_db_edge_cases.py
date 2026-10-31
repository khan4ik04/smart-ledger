# SPDX-License-Identifier: MIT
"""app/db/database.py의 경계 조건 테스트."""

import pandas as pd

from app.db import database as dbm


def test_add_transactions_empty_dataframe_returns_zero(conn):
    assert dbm.add_transactions(conn, pd.DataFrame()) == 0
    assert dbm.get_transactions(conn).empty


def test_add_transactions_uses_default_category_and_memo(conn):
    df = pd.DataFrame([{"date": "2026-10-01", "description": "스타벅스", "amount": -4500}])
    assert dbm.add_transactions(conn, df) == 1

    row = dbm.get_transactions(conn).iloc[0]
    assert row["category"] == "미분류"
    assert row["memo"] == ""
    assert row["amount"] == -4500


def test_update_transaction_without_fields_returns_false(conn):
    tx_id = dbm.add_transaction(conn, "2026-10-01", "GS25", -3000)
    assert dbm.update_transaction(conn, tx_id) is False
