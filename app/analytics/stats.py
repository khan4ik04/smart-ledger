"""통계 계산과 차트.

입력 df는 db.get_transactions()의 결과 형식을 따른다.

"""

from __future__ import annotations

import pandas as pd


def summary(df: pd.DataFrame) -> dict[str, int]:
    """{'income': 총수입, 'expense': 총지출(양수), 'balance': 수입-지출}을 반환한다."""
    income = int(df.loc[df["amount"] > 0, "amount"].sum())
    expense = int(-df.loc[df["amount"] < 0, "amount"].sum())
    return {"income": income, "expense": expense, "balance": income - expense}


def by_category(df: pd.DataFrame) -> pd.DataFrame:
    """지출만 카테고리별로 합산. 열: category, total(양수), ratio(0~1). total 내림차순."""
    expenses = df.loc[df["amount"] < 0]
    result = expenses.groupby("category")["amount"].sum().mul(-1).rename("total").reset_index()
    result = result.sort_values("total", ascending=False, kind="stable").reset_index(drop=True)
    if result.empty:
        result["ratio"] = pd.Series(dtype=float)
    else:
        result["ratio"] = result["total"] / result["total"].sum()
    return result


def by_month(df: pd.DataFrame) -> pd.DataFrame:
    """월별 합계. 열: month('YYYY-MM'), income, expense(양수)."""
    data = df[["date", "amount"]].copy()
    data["month"] = pd.to_datetime(data["date"]).dt.strftime("%Y-%m")
    data["income"] = data["amount"].clip(lower=0)
    data["expense"] = -data["amount"].clip(upper=0)
    return data.groupby("month", as_index=False)[["income", "expense"]].sum()


def category_pie(df: pd.DataFrame):
    """카테고리별 지출 비율 원형 차트 (plotly Figure)."""
    raise NotImplementedError("TODO(분석·시각화): category_pie 구현")


def monthly_line(df: pd.DataFrame):
    """월별 지출 추이 선 그래프 (plotly Figure)."""
    raise NotImplementedError("TODO(분석·시각화): monthly_line 구현")
