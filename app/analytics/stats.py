# SPDX-License-Identifier: MIT
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
    import plotly.express as px

    data = by_category(df)
    fig = px.pie(data, names="category", values="total", title="카테고리별 지출 비율")
    fig.update_traces(
        textinfo="label+percent",
        hovertemplate="%{label}<br>%{value:,.0f}원 (%{percent})<extra></extra>",
    )
    fig.update_layout(legend_title_text="카테고리")
    if data.empty:
        fig.add_annotation(
            text="지출 내역이 없습니다.",
            x=0.5,
            y=0.5,
            xref="paper",
            yref="paper",
            showarrow=False,
        )
    return fig


def monthly_line(df: pd.DataFrame):
    """월별 지출 추이 선 그래프 (plotly Figure)."""
    import plotly.express as px

    data = by_month(df)
    fig = px.line(
        data,
        x="month",
        y="expense",
        markers=True,
        title="월별 지출 추이",
        labels={"month": "월", "expense": "지출 (원)"},
    )
    fig.update_traces(hovertemplate="%{x}<br>%{y:,.0f}원<extra></extra>")
    fig.update_xaxes(type="category")
    fig.update_yaxes(rangemode="tozero", tickformat=",")
    if data.empty:
        fig.add_annotation(
            text="거래 내역이 없습니다.",
            x=0.5,
            y=0.5,
            xref="paper",
            yref="paper",
            showarrow=False,
        )
    return fig
