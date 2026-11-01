# SPDX-License-Identifier: MIT
from math import inf

import pandas as pd
import pytest

from app import db
from app.analytics.budget import BudgetStatus, check_budgets


@pytest.mark.parametrize(
    ("spent", "level"),
    [(790, "ok"), (800, "warning"), (999, "warning"), (1000, "over"), (1250, "over")],
)
def test_check_budgets_thresholds(spent, level):
    df = pd.DataFrame({"category": ["카페"], "amount": [-spent]})

    status = check_budgets(df, {"카페": 1000})[0]

    assert status.category == "카페"
    assert status.budget == 1000
    assert status.spent == spent
    assert status.ratio == pytest.approx(spent / 1000)
    assert status.level == level


def test_check_budgets_sums_only_expenses_for_each_budget(conn):
    db.add_transaction(conn, "2026-10-01", "테스트 카페 1", -300, "카페")
    db.add_transaction(conn, "2026-10-02", "테스트 카페 2", -500, "카페")
    db.add_transaction(conn, "2026-10-03", "테스트 환불", 10000, "카페")
    db.add_transaction(conn, "2026-10-03", "테스트 식사", -1100, "식비")
    db.add_transaction(conn, "2026-10-04", "예산 없는 테스트", -9999, "쇼핑")

    result = check_budgets(db.get_transactions(conn), {"카페": 1000, "식비": 1000, "교통": 5000})

    assert {status.category: status for status in result} == {
        "카페": BudgetStatus("카페", 1000, 800, 0.8, "warning"),
        "식비": BudgetStatus("식비", 1000, 1100, 1.1, "over"),
        "교통": BudgetStatus("교통", 5000, 0, 0.0, "ok"),
    }


@pytest.mark.parametrize(
    ("amounts", "spent", "ratio", "level"),
    [
        ([], 0, 0.0, "ok"),
        ([0], 0, 0.0, "ok"),
        ([500], 0, 0.0, "ok"),
        ([-500], 500, inf, "over"),
    ],
)
def test_check_budgets_zero_budget(amounts, spent, ratio, level):
    df = pd.DataFrame({"category": ["카페"] * len(amounts), "amount": amounts})

    assert check_budgets(df, {"카페": 0}) == [BudgetStatus("카페", 0, spent, ratio, level)]


def test_check_budgets_no_transactions(conn):
    budgets = {"카페": 1000, "식비": 0}
    expected = [BudgetStatus("카페", 1000, 0, 0.0, "ok"), BudgetStatus("식비", 0, 0, 0.0, "ok")]

    assert check_budgets(db.get_transactions(conn), budgets) == expected
    assert check_budgets(pd.DataFrame(), budgets) == expected


def test_check_budgets_without_budgets():
    df = pd.DataFrame({"category": ["카페"], "amount": [-500]})

    assert check_budgets(df, {}) == []


def test_check_budgets_does_not_change_inputs():
    df = pd.DataFrame({"category": ["카페", "카페", "식비"], "amount": [-300, 1000, -500]})
    budgets = {"카페": 1000, "식비": 500}
    before_df = df.copy(deep=True)
    before_budgets = budgets.copy()

    check_budgets(df, budgets)

    pd.testing.assert_frame_equal(df, before_df)
    assert budgets == before_budgets
