import pandas as pd
import pytest

from app import db


def test_add_and_get(conn):
    tx_id = db.add_transaction(conn, "2026-09-01", "스타벅스", -5600, "카페")
    df = db.get_transactions(conn)
    assert len(df) == 1
    row = df.iloc[0]
    assert row["id"] == tx_id
    assert row["amount"] == -5600
    assert row["category"] == "카페"


def test_default_category_is_uncategorized(conn):
    db.add_transaction(conn, "2026-09-01", "무언가", -1000)
    assert db.get_transactions(conn).iloc[0]["category"] == "미분류"


def test_filter_by_date_and_category(conn):
    db.add_transaction(conn, "2026-08-31", "A", -100, "카페")
    db.add_transaction(conn, "2026-09-01", "B", -200, "카페")
    db.add_transaction(conn, "2026-09-30", "C", -300, "교통")
    db.add_transaction(conn, "2026-10-01", "D", -400, "카페")

    sept = db.get_transactions(conn, start="2026-09-01", end="2026-09-30")
    assert list(sept["description"]) == ["B", "C"]

    cafe = db.get_transactions(conn, category="카페")
    assert list(cafe["description"]) == ["A", "B", "D"]


def test_empty_result_has_columns(conn):
    df = db.get_transactions(conn)
    assert df.empty
    assert list(df.columns) == db.database.TRANSACTION_COLUMNS


def test_update(conn):
    tx_id = db.add_transaction(conn, "2026-09-01", "A", -100)
    assert db.update_transaction(conn, tx_id, category="식비", amount=-150)
    row = db.get_transactions(conn).iloc[0]
    assert row["category"] == "식비"
    assert row["amount"] == -150


def test_update_rejects_unknown_field(conn):
    tx_id = db.add_transaction(conn, "2026-09-01", "A", -100)
    with pytest.raises(ValueError):
        db.update_transaction(conn, tx_id, id=999)


def test_delete(conn):
    tx_id = db.add_transaction(conn, "2026-09-01", "A", -100)
    assert db.delete_transaction(conn, tx_id)
    assert not db.delete_transaction(conn, tx_id)
    assert db.get_transactions(conn).empty


def test_add_transactions_bulk(conn):
    df = pd.DataFrame(
        {
            "date": ["2026-09-01", "2026-09-02"],
            "description": ["GS25", "급여"],
            "amount": [-3200, 850000],
        }
    )
    assert db.add_transactions(conn, df) == 2
    result = db.get_transactions(conn)
    assert list(result["category"]) == ["미분류", "미분류"]
    assert result["amount"].sum() == 846800


def test_budgets(conn):
    db.set_budget(conn, "카페", "2026-09", 50000)
    db.set_budget(conn, "카페", "2026-09", 60000)  # 덮어쓰기
    db.set_budget(conn, "교통", "2026-09", 30000)
    db.set_budget(conn, "카페", "2026-10", 40000)
    assert db.get_budgets(conn, "2026-09") == {"카페": 60000, "교통": 30000}


def test_negative_budget_rejected(conn):
    with pytest.raises(ValueError):
        db.set_budget(conn, "카페", "2026-09", -1)


def test_default_db_path_is_project_root():
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    assert db.database.DEFAULT_DB_PATH == root / "ledger.db"
