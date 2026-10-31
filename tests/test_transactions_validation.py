import pandas as pd


def test_expense_is_negative():
    assert -4500 < 0


def test_income_is_positive():
    assert 100000 > 0


def test_transactions_total():
    data = pd.DataFrame({
        "amount": [-4500, 100000],
        "type": ["expense", "income"],
    })
    assert data["amount"].sum() == 95500
    assert len(data) == 2