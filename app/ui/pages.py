"""각 화면을 그리는 함수. main.py가 메뉴에 따라 호출한다.

TODO(담당: UI)
- 대시보드 꾸미기, 입력 폼 검증, 조회 필터, 파일 업로드 흐름, 예산 설정 화면
- 아직 구현되지 않은 모듈은 NotImplementedError → '준비 중' 표시
"""

from __future__ import annotations

import datetime as dt
import sqlite3
from collections.abc import Callable

import streamlit as st

from app import db


def _not_ready(name: str) -> None:
    st.info(f"'{name}' 기능은 준비 중입니다.")


def _try(name: str, fn: Callable[[], None]) -> None:
    try:
        fn()
    except NotImplementedError:
        _not_ready(name)


def dashboard(conn: sqlite3.Connection) -> None:
    st.header("대시보드")
    df = db.get_transactions(conn)
    if df.empty:
        st.write("아직 거래 내역이 없습니다. '내역 입력' 또는 '파일 가져오기'에서 추가하세요.")
        return

    def _render() -> None:
        from app.analytics import stats

        s = stats.summary(df)
        c1, c2, c3 = st.columns(3)
        c1.metric("수입", f"{s['income']:,}원")
        c2.metric("지출", f"{s['expense']:,}원")
        c3.metric("잔액", f"{s['balance']:,}원")
        st.plotly_chart(stats.category_pie(df), width="stretch")

    _try("통계", _render)


def add_entry(conn: sqlite3.Connection) -> None:
    st.header("내역 입력")
    with st.form("add_tx", clear_on_submit=True):
        date = st.date_input("날짜", value=dt.date.today())
        kind = st.radio("구분", ["지출", "수입"], horizontal=True)
        description = st.text_input("내용 (가맹점명 등)")
        amount = st.number_input("금액 (원)", min_value=0, step=1000)
        category = st.text_input("카테고리", value="미분류")
        memo = st.text_input("메모")
        submitted = st.form_submit_button("저장")
    if submitted:
        if not description or amount <= 0:
            st.error("내용과 금액을 입력하세요.")
            return
        signed = -int(amount) if kind == "지출" else int(amount)
        db.add_transaction(conn, date.isoformat(), description, signed, category, memo)
        st.success("저장했습니다.")


def history(conn: sqlite3.Connection) -> None:
    st.header("내역 조회")
    df = db.get_transactions(conn)
    st.dataframe(df, width="stretch", hide_index=True)


def import_file(conn: sqlite3.Connection) -> None:
    st.header("파일 가져오기")
    uploaded = st.file_uploader("은행 거래 내역 (CSV / Excel)", type=["csv", "xlsx"])
    if uploaded is None:
        return

    def _render() -> None:
        from app.importer import categorizer, loader

        df = loader.load_file(uploaded, filename=uploaded.name)
        df = loader.remove_duplicates(df, db.get_transactions(conn))
        df = categorizer.categorize_frame(df, categorizer.load_rules())
        st.dataframe(df, width="stretch", hide_index=True)
        if st.button(f"{len(df)}건 저장"):
            db.add_transactions(conn, df)
            st.success("저장했습니다.")

    _try("파일 가져오기", _render)


def statistics(conn: sqlite3.Connection) -> None:
    st.header("통계")

    def _render() -> None:
        from app.analytics import stats

        df = db.get_transactions(conn)
        st.plotly_chart(stats.monthly_line(df), width="stretch")
        st.dataframe(stats.by_category(df), width="stretch", hide_index=True)

    _try("통계", _render)


def budgets(conn: sqlite3.Connection) -> None:
    st.header("예산 설정")
    _not_ready("예산 설정")
