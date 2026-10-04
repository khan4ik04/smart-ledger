"""실행: streamlit run app/main.py"""

import sys
from pathlib import Path

import streamlit as st

# `streamlit run app/main.py`로 실행해도 `import app`이 되도록 저장소 루트를 경로에 추가
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import db  # noqa: E402
from app.ui import pages  # noqa: E402

PAGES = {
    "대시보드": pages.dashboard,
    "내역 입력": pages.add_entry,
    "내역 조회": pages.history,
    "파일 가져오기": pages.import_file,
    "통계": pages.statistics,
    "예산 설정": pages.budgets,
}


@st.cache_resource
def get_connection():
    return db.connect(check_same_thread=False)


def main() -> None:
    st.set_page_config(page_title="스마트 가계부", page_icon="💰", layout="wide")
    st.sidebar.title("💰 스마트 가계부")
    choice = st.sidebar.radio("메뉴", list(PAGES))
    PAGES[choice](get_connection())


main()
