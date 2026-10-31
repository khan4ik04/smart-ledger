"""Streamlit pages for Smart Ledger.

UI layer only: all database operations go through ``app.db``.
Run from the repository root: ``streamlit run app/main.py``.
"""

from __future__ import annotations

import datetime as dt
import sqlite3
from collections.abc import Callable

import pandas as pd
import streamlit as st

from app import db


# Visual layer only. All calculations and database operations remain unchanged.
_THEME_CSS = """
<style>
/* Smart Ledger — subtle midnight / indigo theme */
:root {
  --sl-accent: #9098ff;
  --sl-border: rgba(150, 164, 205, 0.16);
  --sl-panel: rgba(31, 38, 57, 0.76);
  --sl-text-muted: #aebbd0;
}

[data-testid="stAppViewContainer"] {
  background:
    radial-gradient(ellipse 55% 33% at 80% -8%, rgba(96, 104, 205, 0.16), transparent),
    #0e1118;
}
[data-testid="stSidebar"] {
  background: linear-gradient(175deg, #1b2030 0%, #131824 100%);
  border-right: 1px solid var(--sl-border);
}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h1,
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h2 {
  letter-spacing: -0.02em;
}
[data-testid="stSidebar"] [role="radiogroup"] label {
  border-radius: 10px;
  padding: 0.28rem 0.45rem;
  transition: background 0.15s ease;
}
[data-testid="stSidebar"] [role="radiogroup"] label:hover {
  background: rgba(144, 152, 255, 0.10);
}

/* Give the page a clear hierarchy without enlarging it too much. */
[data-testid="stMainBlockContainer"] {
  padding-top: 2.65rem;
  max-width: 1120px;
}
h1 { font-weight: 780 !important; letter-spacing: -0.045em !important; }
h2, h3 { letter-spacing: -0.025em !important; }
[data-testid="stCaptionContainer"] { color: var(--sl-text-muted); }
hr { border-color: var(--sl-border) !important; }

/* Summary tiles */
[data-testid="stMetric"] {
  background: var(--sl-panel);
  border: 1px solid var(--sl-border);
  border-radius: 16px;
  padding: 17px 19px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.10);
}
[data-testid="stMetricLabel"] { color: #aebbd0; }
[data-testid="stMetricValue"] {
  font-size: clamp(1.35rem, 2.45vw, 2.15rem);
  font-weight: 740;
  letter-spacing: -0.035em;
}

/* Input surfaces */
[data-testid="stForm"] {
  background: rgba(30, 36, 52, 0.46);
  border: 1px solid rgba(144, 152, 255, 0.22);
  border-radius: 18px;
  padding: 22px 20px 12px;
  box-shadow: 0 10px 32px rgba(0, 0, 0, 0.10);
}
[data-testid="stTextInput"] input,
[data-testid="stNumberInput"] input,
[data-testid="stDateInput"] input,
[data-testid="stSelectbox"] [data-baseweb="select"] {
  border-radius: 10px;
}
[data-testid="stFormSubmitButton"] button[kind="primary"],
button[kind="primary"] {
  background: linear-gradient(110deg, #6574eb, #8c78d5);
  border: 0;
  border-radius: 10px;
  font-weight: 680;
  box-shadow: 0 4px 15px rgba(109, 113, 227, 0.16);
}
[data-testid="stFormSubmitButton"] button[kind="primary"]:hover,
button[kind="primary"]:hover {
  background: linear-gradient(110deg, #7583f4, #9985e4);
  border: 0;
}
[data-testid="stDataFrame"] {
  border: 1px solid var(--sl-border);
  border-radius: 12px;
  overflow: hidden;
}
[data-testid="stExpander"] {
  border-radius: 12px;
  border-color: var(--sl-border);
}
[data-testid="stAlert"] { border-radius: 12px; }

/* Small, understated page eyebrow */
.sl-eyebrow {
  display: inline-flex;
  align-items: center;
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.15em;
  text-transform: uppercase;
  color: #a7afff;
  margin: 0 0 0.4rem;
}
.sl-eyebrow::before {
  content: "";
  display: inline-block;
  width: 6px;
  height: 6px;
  margin-right: 9px;
  background: #a7afff;
  border-radius: 50%;
}
@media (max-width: 720px) {
  [data-testid="stMainBlockContainer"] { padding-top: 1.1rem; }
  [data-testid="stForm"] { padding: 14px 12px 8px; }
  [data-testid="stMetric"] { padding: 12px; }
}
</style>
"""


def _page_style() -> None:
    """Apply global visual tweaks without touching backend/business logic."""
    st.markdown(_THEME_CSS, unsafe_allow_html=True)
    st.markdown('<div class="sl-eyebrow">SMART LEDGER / PERSONAL FINANCE</div>', unsafe_allow_html=True)


def _not_ready(name: str) -> None:
    st.info(f"'{name}' 기능은 준비 중입니다.")


def _try(name: str, fn: Callable[[], None]) -> None:
    """Keep unfinished teammates' optional modules from breaking the UI."""
    try:
        fn()
    except NotImplementedError:
        _not_ready(name)


def _money(value: int) -> str:
    return f"{int(value):,}원"


def _signed_amount(kind: str, amount: int) -> int:
    """The team-wide data contract: expenses negative, income positive."""
    value = int(amount)
    if value <= 0:
        raise ValueError("금액은 0원보다 커야 합니다.")
    if kind not in ("지출", "수입"):
        raise ValueError("구분을 다시 선택해 주세요.")
    return -value if kind == "지출" else value


def _display_table(frame: pd.DataFrame) -> None:
    """Show an easy-to-read copy without changing the DataFrame from DB."""
    view = frame.copy()
    view["구분"] = view["amount"].apply(lambda amount: "지출" if amount < 0 else "수입")
    view = view.rename(
        columns={
            "id": "번호",
            "date": "날짜",
            "description": "내용",
            "amount": "금액 (원)",
            "category": "카테고리",
            "memo": "메모",
        }
    )
    columns = ["번호", "날짜", "구분", "내용", "금액 (원)", "카테고리", "메모"]
    st.dataframe(view[columns], use_container_width=True, hide_index=True)


def dashboard(conn: sqlite3.Connection) -> None:
    _page_style()
    st.title("💰 스마트 가계부")
    st.caption("한눈에 확인하는 수입 · 지출 · 잔액")
    df = db.get_transactions(conn)
    if df.empty:
        st.info("아직 거래 내역이 없습니다. 왼쪽 '내역 입력'에서 첫 거래를 추가해 보세요.")
        return

    from app.analytics import stats

    def render() -> None:
        totals = stats.summary(df)
        col1, col2, col3 = st.columns(3)
        col1.metric("총 수입", _money(totals["income"]))
        col2.metric("총 지출", _money(totals["expense"]))
        col3.metric("잔액", _money(totals["balance"]))

        st.subheader("📊 카테고리별 지출")
        if (df["amount"] < 0).any():
            st.plotly_chart(stats.category_pie(df), use_container_width=True)
        else:
            st.info("아직 지출 내역이 없어 그래프를 표시할 수 없습니다.")

    _try("통계", render)
    st.subheader("최근 거래")
    latest = df.sort_values(["date", "id"], ascending=False).head(8)
    _display_table(latest)


def add_entry(conn: sqlite3.Connection) -> None:
    _page_style()
    st.title("➕ 내역 입력")
    st.caption("새 거래를 입력하면 내역 조회와 대시보드에 바로 반영됩니다.")

    with st.form("add_transaction", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            date = st.date_input("날짜", value=dt.date.today())
            kind = st.radio("구분", ["지출", "수입"], horizontal=True)
            amount = st.number_input("금액 (원)", min_value=0, value=0, step=1000)
        with col2:
            description = st.text_input("내용 / 가맹점명", placeholder="예: 스타벅스")
            category = st.text_input("카테고리", value="미분류")
            memo = st.text_input("메모 (선택)")
        submitted = st.form_submit_button("거래 저장  →", type="primary")

    if submitted:
        if not description.strip():
            st.error("내용 / 가맹점명을 입력해 주세요.")
        else:
            try:
                signed_amount = _signed_amount(kind, amount)
            except ValueError as exc:
                st.error(str(exc))
            else:
                tx_id = db.add_transaction(
                    conn,
                    date.isoformat(),
                    description.strip(),
                    signed_amount,
                    category.strip() or "미분류",
                    memo.strip(),
                )
                st.success(f"거래가 저장되었습니다. (번호: {tx_id})")

    st.subheader("최근 입력 내역")
    frame = db.get_transactions(conn)
    if frame.empty:
        st.info("표시할 거래가 없습니다.")
    else:
        recent = frame.sort_values(["date", "id"], ascending=False).head(5)
        _display_table(recent)


def _edit_or_delete(conn: sqlite3.Connection, frame: pd.DataFrame) -> None:
    """Optional CRUD controls using the backend API (no SQL in UI)."""
    with st.expander("✏️ 선택한 거래 수정 / 삭제"):
        id_list = frame["id"].astype(int).tolist()
        labels = {
            int(row.id): f"#{row.id} · {row.date} · {row.description} · {_money(row.amount)}"
            for row in frame.itertuples(index=False)
        }
        tx_id = st.selectbox("거래 선택", options=id_list, format_func=lambda value: labels[value])
        selected = frame.loc[frame["id"] == tx_id].iloc[0]
        kind = "지출" if int(selected["amount"]) < 0 else "수입"

        with st.form(f"edit_tx_{tx_id}"):
            new_date = st.date_input("날짜", value=dt.date.fromisoformat(str(selected["date"])))
            new_kind = st.radio(
                "구분", ["지출", "수입"],
                index=0 if kind == "지출" else 1,
                horizontal=True,
            )
            new_desc = st.text_input("내용", value=str(selected["description"]))
            new_amount = st.number_input(
                "금액 (원)", min_value=0, value=abs(int(selected["amount"])), step=1000
            )
            new_category = st.text_input("카테고리", value=str(selected["category"]))
            new_memo = st.text_input("메모", value=str(selected["memo"]))
            save = st.form_submit_button("수정 저장")

        if save:
            if not new_desc.strip():
                st.error("내용을 입력해 주세요.")
            else:
                try:
                    signed = _signed_amount(new_kind, new_amount)
                except ValueError as exc:
                    st.error(str(exc))
                else:
                    db.update_transaction(
                        conn, tx_id, date=new_date.isoformat(), description=new_desc.strip(),
                        amount=signed, category=new_category.strip() or "미분류",
                        memo=new_memo.strip(),
                    )
                    st.session_state["ui_notice"] = "거래가 수정되었습니다."
                    st.rerun()

        confirmed = st.checkbox("이 거래를 삭제하는 것에 동의합니다.", key=f"confirm_{tx_id}")
        if st.button("거래 삭제", disabled=not confirmed):
            db.delete_transaction(conn, tx_id)
            st.session_state["ui_notice"] = "거래가 삭제되었습니다."
            st.rerun()


def history(conn: sqlite3.Connection) -> None:
    _page_style()
    st.title("📋 내역 조회")
    notice = st.session_state.pop("ui_notice", None)
    if notice:
        st.success(notice)

    all_tx = db.get_transactions(conn)
    if all_tx.empty:
        st.info("등록된 거래가 없습니다. '내역 입력'에서 거래를 추가하세요.")
        return

    date_min = dt.date.fromisoformat(str(all_tx["date"].min()))
    date_max = dt.date.fromisoformat(str(all_tx["date"].max()))
    a, b = st.columns(2)
    with a:
        start = st.date_input("시작 날짜", value=date_min, key="history_start")
    with b:
        end = st.date_input("종료 날짜", value=date_max, key="history_end")
    if start > end:
        st.warning("시작 날짜가 종료 날짜보다 늦을 수 없습니다.")
        return

    categories = ["전체", *sorted(all_tx["category"].dropna().unique().tolist())]
    c, d = st.columns(2)
    with c:
        chosen_category = st.selectbox("카테고리", categories)
    with d:
        chosen_kind = st.selectbox("구분", ["전체", "지출", "수입"])

    df = db.get_transactions(
        conn,
        start=start.isoformat(),
        end=end.isoformat(),
        category=None if chosen_category == "전체" else chosen_category,
    )
    if chosen_kind == "지출":
        df = df.loc[df["amount"] < 0]
    elif chosen_kind == "수입":
        df = df.loc[df["amount"] > 0]

    st.caption(f"조회 결과: {len(df)}건")
    if df.empty:
        st.info("조건에 맞는 거래가 없습니다.")
        return
    df = df.sort_values(["date", "id"], ascending=False)
    _display_table(df)
    _edit_or_delete(conn, df)


def import_file(conn: sqlite3.Connection) -> None:
    _page_style()
    st.title("📁 파일 가져오기")
    st.caption("팀 테스트에는 실제 계좌 내역이 아닌 가짜 CSV 파일만 사용하세요.")
    uploaded = st.file_uploader("CSV / Excel 파일", type=["csv", "xlsx"])
    if uploaded is None:
        return

    def render() -> None:
        from app.importer import categorizer, loader

        df = loader.load_file(uploaded, filename=uploaded.name)
        df = loader.remove_duplicates(df, db.get_transactions(conn))
        df = categorizer.categorize_frame(df, categorizer.load_rules())
        if df.empty:
            st.info("새로 가져올 거래가 없습니다.")
            return
        st.dataframe(df, use_container_width=True, hide_index=True)
        if st.button(f"{len(df)}건 저장"):
            count = db.add_transactions(conn, df)
            st.success(f"{count}건 저장했습니다.")

    _try("파일 가져오기", render)


def statistics(conn: sqlite3.Connection) -> None:
    _page_style()
    st.title("📈 통계")
    df = db.get_transactions(conn)
    if df.empty:
        st.info("통계를 보려면 먼저 거래 내역을 추가하세요.")
        return

    def render() -> None:
        from app.analytics import stats

        totals = stats.summary(df)
        c1, c2, c3 = st.columns(3)
        c1.metric("수입", _money(totals["income"]))
        c2.metric("지출", _money(totals["expense"]))
        c3.metric("잔액", _money(totals["balance"]))
        if (df["amount"] < 0).any():
            st.plotly_chart(stats.category_pie(df), use_container_width=True)
            st.plotly_chart(stats.monthly_line(df), use_container_width=True)
            st.subheader("카테고리별 지출")
            st.dataframe(stats.by_category(df), use_container_width=True, hide_index=True)
        else:
            st.info("아직 지출 내역이 없습니다.")

    _try("통계", render)


def budgets(conn: sqlite3.Connection) -> None:
    _page_style()
    st.title("🎯 예산 설정")
    _not_ready("예산 설정")
