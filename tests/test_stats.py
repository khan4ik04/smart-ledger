import pandas as pd
import pytest

from app import db
from app.analytics import stats


def test_summary_uses_signed_amounts(conn):
    db.add_transaction(conn, "2026-09-01", "급여", 100000, "수입")
    db.add_transaction(conn, "2026-09-02", "카페", -5000, "카페")
    db.add_transaction(conn, "2026-09-03", "식사", -12000, "식비")
    db.add_transaction(conn, "2026-09-04", "변동 없음", 0)

    assert stats.summary(db.get_transactions(conn)) == {
        "income": 100000,
        "expense": 17000,
        "balance": 83000,
    }


@pytest.mark.parametrize(
    ("amounts", "expected"),
    [
        ([], {"income": 0, "expense": 0, "balance": 0}),
        ([1000, 2000], {"income": 3000, "expense": 0, "balance": 3000}),
        ([-1000, -2000], {"income": 0, "expense": 3000, "balance": -3000}),
    ],
)
def test_summary_handles_empty_and_one_sided_data(amounts, expected):
    df = pd.DataFrame({"amount": amounts})
    assert stats.summary(df) == expected
