# SPDX-License-Identifier: MIT
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


@pytest.fixture
def transactions():
    return pd.DataFrame(
        [
            ("2026-01-03", -2000, "카페"),
            ("2025-12-30", -7000, "식비"),
            ("2026-01-01", 20000, "카페"),
            ("2025-12-02", -3000, "카페"),
            ("2026-01-04", -5000, "식비"),
            ("2026-02-01", 3000, "급여"),
            ("2026-01-05", 0, "카페"),
        ],
        columns=["date", "amount", "category"],
    )


def test_by_category_counts_only_expenses(transactions):
    result = stats.by_category(transactions)
    assert list(result.columns) == ["category", "total", "ratio"]
    assert list(result["category"]) == ["식비", "카페"]
    assert list(result["total"]) == [12000, 5000]
    assert list(result["ratio"]) == pytest.approx([12 / 17, 5 / 17])
    assert result["ratio"].sum() == pytest.approx(1)


def test_by_month_sorts_across_years(transactions):
    expected = pd.DataFrame(
        {
            "month": ["2025-12", "2026-01", "2026-02"],
            "income": [0, 20000, 3000],
            "expense": [10000, 7000, 0],
        }
    )
    pd.testing.assert_frame_equal(stats.by_month(transactions), expected)


def test_empty_db_returns_empty_tables_with_columns(conn):
    df = db.get_transactions(conn)
    categories = stats.by_category(df)
    months = stats.by_month(df)
    assert categories.empty
    assert list(categories.columns) == ["category", "total", "ratio"]
    assert months.empty
    assert list(months.columns) == ["month", "income", "expense"]


def test_income_only_has_no_expense_categories():
    df = pd.DataFrame({"date": ["2026-09-01"], "amount": [1000], "category": ["급여"]})
    assert stats.by_category(df).empty
    assert stats.by_month(df).to_dict("records") == [
        {"month": "2026-09", "income": 1000, "expense": 0}
    ]


def test_statistics_do_not_change_input(transactions):
    before = transactions.copy(deep=True)
    stats.summary(transactions)
    stats.by_category(transactions)
    stats.by_month(transactions)
    pd.testing.assert_frame_equal(transactions, before)


def test_category_pie_chart_uses_expense_totals(transactions):
    fig = stats.category_pie(transactions)
    trace = fig.data[0]
    assert trace.type == "pie"
    assert list(trace.labels) == ["식비", "카페"]
    assert list(trace.values) == [12000, 5000]


def test_monthly_line_chart_uses_sorted_expenses(transactions):
    fig = stats.monthly_line(transactions)
    trace = fig.data[0]
    assert trace.type == "scatter"
    assert trace.mode == "lines+markers"
    assert list(trace.x) == ["2025-12", "2026-01", "2026-02"]
    assert list(trace.y) == [10000, 7000, 0]


@pytest.mark.parametrize("amounts", [[], [1000], [0]])
def test_charts_handle_no_expenses(amounts):
    df = pd.DataFrame(
        {
            "date": ["2026-09-01"] * len(amounts),
            "amount": amounts,
            "category": ["급여"] * len(amounts),
        }
    )
    pie = stats.category_pie(df)
    line = stats.monthly_line(df)
    assert sum(len(trace.values) for trace in pie.data) == 0
    assert pie.layout.annotations[0].text == "지출 내역이 없습니다."
    if df.empty:
        assert line.layout.annotations[0].text == "거래 내역이 없습니다."
    else:
        assert list(line.data[0].y) == [0]


def test_charts_do_not_change_input(transactions):
    before = transactions.copy(deep=True)
    stats.category_pie(transactions)
    stats.monthly_line(transactions)
    pd.testing.assert_frame_equal(transactions, before)
