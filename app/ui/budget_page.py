"""Budget settings screen for Smart Ledger (Streamlit).

UI layer only. Persistence is delegated to ``app.db`` and budget calculations
are delegated to ``app.analytics.budget.check_budgets``.
"""

from __future__ import annotations

import datetime as dt
import math
import sqlite3
from collections.abc import Mapping
from dataclasses import asdict, is_dataclass
from typing import Any

import pandas as pd
import streamlit as st

from app import db

DEFAULT_CATEGORIES = (
    "식비",
    "카페",
    "편의점",
    "교통",
    "쇼핑",
    "통신",
    "문화·여가",
    "교육",
    "미분류",
)


def _money(amount: int | float) -> str:
    return f"{int(amount):,}원"


def _item_dict(item: Any) -> dict[str, Any]:
    if isinstance(item, Mapping):
        return dict(item)
    if is_dataclass(item) and not isinstance(item, type):
        return asdict(item)
    if hasattr(item, "_asdict"):
        return dict(item._asdict())
    required = ("category", "spent", "budget", "ratio", "level")
    if all(hasattr(item, name) for name in required):
        return {name: getattr(item, name) for name in required}
    raise TypeError("check_budgets 결과 형식을 확인해 주세요.")


def _budget_rows(results: Any) -> list[dict[str, Any]]:
    """Convert the common DataFrame/list/dict output shapes into UI rows.

    The actual spending and status are always produced by check_budgets; the
    UI does not reimplement the teammates' budget calculation.
    """
    if isinstance(results, pd.DataFrame):
        raw_rows = results.to_dict("records")
    elif isinstance(results, Mapping):
        if "category" in results and "spent" in results:
            raw_rows = [dict(results)]
        else:
            raw_rows = []
            for name, status in results.items():
                row = _item_dict(status)
                row.setdefault("category", name)
                raw_rows.append(row)
    elif isinstance(results, (tuple, list)):
        raw_rows = [_item_dict(item) for item in results]
    else:
        raise TypeError("지원하지 않는 check_budgets 결과 형식입니다.")

    rows = []
    for row in raw_rows:
        if not {"category", "spent", "budget", "ratio", "level"}.issubset(row):
            raise ValueError("check_budgets 결과에 필요한 컬럼이 없습니다.")
        category = str(row["category"])
        limit = int(row["budget"])
        spent = int(row["spent"])
        ratio = float(row["ratio"])
        level = str(row["level"])
        if limit < 0 or spent < 0 or math.isnan(ratio):
            raise ValueError("예산 계산 결과에 유효하지 않은 값이 있습니다.")
        rows.append(
            {
                "category": category,
                "budget": limit,
                "spent": spent,
                "ratio": ratio,
                "level": level,
            }
        )
    return sorted(rows, key=lambda item: item["category"])


def _budgets_dict(value: Any) -> dict[str, int]:
    """Accept the DB get_budgets contract: {category: budget_amount}."""
    if not isinstance(value, Mapping):
        raise TypeError("db.get_budgets()는 카테고리별 금액 사전을 반환해야 합니다.")
    return {str(name): int(amount) for name, amount in value.items()}


def _month_transactions(conn: sqlite3.Connection, month: str) -> pd.DataFrame:
    # Filter on the UI side: the shared DB API may return transactions for all dates.
    frame = db.get_transactions(conn)
    if frame.empty:
        return frame
    dates = pd.to_datetime(frame["date"], errors="coerce")
    return frame.loc[dates.dt.strftime("%Y-%m").eq(month)].copy()


def render_budget_page(conn: sqlite3.Connection) -> None:
    """Render the budget form and progress indicators using the shared APIs."""
    from app.analytics import budget

    st.title("🎯 예산 설정")
    st.caption("월별 카테고리 예산을 설정하고 지출 현황을 확인해 보세요.")

    today = dt.date.today()
    years = list(range(today.year - 5, today.year + 3))
    first, second = st.columns(2)
    with first:
        year = st.selectbox("연도", years, index=years.index(today.year), key="budget_year")
    with second:
        month_number = st.selectbox(
            "월", list(range(1, 13)), index=today.month - 1, key="budget_month"
        )
    selected_month = f"{year:04d}-{month_number:02d}"

    try:
        existing = _budgets_dict(db.get_budgets(conn, selected_month))
    except (ValueError, TypeError, sqlite3.Error, NotImplementedError) as exc:
        st.error(f"저장된 예산을 불러오지 못했습니다: {exc}")
        return

    month_df = _month_transactions(conn, selected_month)
    observed = (
        month_df.loc[month_df["amount"] < 0, "category"].dropna().astype(str).tolist()
        if not month_df.empty
        else []
    )
    category_options = sorted(set(DEFAULT_CATEGORIES) | set(existing) | set(observed))

    st.subheader("📝 카테고리 예산 등록")
    with st.form("budget_setting_form"):
        left, right = st.columns(2)
        with left:
            category = st.selectbox("카테고리", category_options)
            custom = st.text_input("새 카테고리 (선택)", placeholder="예: 여행")
        with right:
            selected_category = custom.strip() or category
            current_limit = existing.get(selected_category, 0)
            amount = st.number_input(
                "월 예산 (원)", min_value=0, value=int(current_limit), step=10000
            )
            st.caption("0원도 입력할 수 있습니다.")
        submitted = st.form_submit_button("예산 저장", type="primary")

    if submitted:
        selected_category = custom.strip() or category
        if not selected_category:
            st.error("카테고리를 입력해 주세요.")
        else:
            try:
                db.set_budget(conn, selected_category, selected_month, int(amount))
            except (ValueError, TypeError, sqlite3.Error, NotImplementedError) as exc:
                st.error(f"예산 저장에 실패했습니다: {exc}")
            else:
                st.success(f"{selected_month} · {selected_category}: {_money(amount)} 저장 완료")
                # Show saved budgets on the same rerun, without needing browser reload.
                existing = _budgets_dict(db.get_budgets(conn, selected_month))

    st.subheader("📊 이번 달 예산 사용 현황")
    if not existing:
        st.info("설정된 예산이 없습니다. 위에서 카테고리별 예산을 추가해 주세요.")
        return

    try:
        results = budget.check_budgets(month_df, existing)
        rows = _budget_rows(results)
    except (ValueError, TypeError, KeyError, NotImplementedError) as exc:
        st.error(f"예산 계산 결과를 표시하지 못했습니다: {exc}")
        return

    if not rows:
        st.info("표시할 예산 항목이 없습니다.")
        return

    table = []
    for row in rows:
        name = row["category"]
        limit = row["budget"]
        spent = row["spent"]
        ratio = row["ratio"]
        st.markdown(f"**{name}** — {_money(spent)} / {_money(limit)}")
        st.progress(min(max(ratio, 0.0), 1.0))

        percent = "계산 불가" if not math.isfinite(ratio) else f"{ratio:.0%}"
        status = row["level"]
        if status == "over" or ratio >= 1.0:
            st.error(f"{name}: 예산에 도달했거나 초과했습니다. ({percent})")
        elif status == "warning" or ratio >= 0.8:
            st.warning(f"{name}: 예산의 80% 이상을 사용했습니다. ({percent})")
        else:
            st.caption(f"사용률 {percent}")
        table.append(
            {
                "카테고리": name,
                "예산 (원)": limit,
                "사용액 (원)": spent,
                "사용률": percent,
                "상태": status,
            }
        )
    with st.expander("예산 상세 표"):
        st.dataframe(pd.DataFrame(table), width="stretch", hide_index=True)
