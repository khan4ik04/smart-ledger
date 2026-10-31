"""SQLite 저장소.

규칙
- 금액(amount)은 원 단위 정수. 지출은 음수, 수입은 양수.
- 날짜(date)는 'YYYY-MM-DD' 문자열.
- 다른 모듈은 이 파일의 함수만 사용하고 SQL을 직접 쓰지 않는다.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd

DEFAULT_DB_PATH = Path("ledger.db")

TRANSACTION_COLUMNS = ["id", "date", "description", "amount", "category", "memo"]

SCHEMA = """
CREATE TABLE IF NOT EXISTS transactions (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    date        TEXT    NOT NULL,
    description TEXT    NOT NULL,
    amount      INTEGER NOT NULL,
    category    TEXT    NOT NULL DEFAULT '미분류',
    memo        TEXT    NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(date);

CREATE TABLE IF NOT EXISTS budgets (
    category TEXT    NOT NULL,
    month    TEXT    NOT NULL,          -- 'YYYY-MM'
    amount   INTEGER NOT NULL,          -- 월 예산 (양수)
    PRIMARY KEY (category, month)
);
"""


def connect(
    db_path: str | Path = DEFAULT_DB_PATH, check_same_thread: bool = True
) -> sqlite3.Connection:
    """DB 연결을 열고 테이블이 없으면 만든다. ':memory:'는 테스트용.

    Streamlit은 여러 스레드에서 연결을 쓰므로 check_same_thread=False로 연다.
    """
    conn = sqlite3.connect(str(db_path), check_same_thread=check_same_thread)
    conn.row_factory = sqlite3.Row
    init_db(conn)
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    conn.commit()


def add_transaction(
    conn: sqlite3.Connection,
    date: str,
    description: str,
    amount: int,
    category: str = "미분류",
    memo: str = "",
) -> int:
    """거래 1건을 저장하고 새 id를 반환한다."""
    cur = conn.execute(
        "INSERT INTO transactions (date, description, amount, category, memo) "
        "VALUES (?, ?, ?, ?, ?)",
        (date, description, int(amount), category, memo),
    )
    conn.commit()
    return int(cur.lastrowid)


def add_transactions(conn: sqlite3.Connection, df: pd.DataFrame) -> int:
    """여러 건을 한 번에 저장한다 (importer 결과 저장용). 저장한 건수를 반환한다.

    df에는 date, description, amount 열이 필수이고 category, memo는 선택이다.
    """
    if df.empty:
        return 0
    data = df.copy()
    if "category" not in data:
        data["category"] = "미분류"
    if "memo" not in data:
        data["memo"] = ""
    rows = [
        (str(r.date), str(r.description), int(r.amount), str(r.category), str(r.memo or ""))
        for r in data.itertuples(index=False)
    ]
    conn.executemany(
        "INSERT INTO transactions (date, description, amount, category, memo) "
        "VALUES (?, ?, ?, ?, ?)",
        rows,
    )
    conn.commit()
    return len(rows)


def get_transactions(
    conn: sqlite3.Connection,
    start: str | None = None,
    end: str | None = None,
    category: str | None = None,
) -> pd.DataFrame:
    """조건에 맞는 거래를 날짜순 DataFrame으로 반환한다 (열: TRANSACTION_COLUMNS).

    start, end는 'YYYY-MM-DD'이며 둘 다 포함(inclusive)한다.
    """
    sql = "SELECT id, date, description, amount, category, memo FROM transactions WHERE 1=1"
    params: list[object] = []
    if start:
        sql += " AND date >= ?"
        params.append(start)
    if end:
        sql += " AND date <= ?"
        params.append(end)
    if category:
        sql += " AND category = ?"
        params.append(category)
    sql += " ORDER BY date, id"
    rows = conn.execute(sql, params).fetchall()
    return pd.DataFrame([dict(r) for r in rows], columns=TRANSACTION_COLUMNS)


_UPDATABLE = {"date", "description", "amount", "category", "memo"}


def update_transaction(conn: sqlite3.Connection, tx_id: int, **fields: object) -> bool:
    """지정한 필드만 수정한다. 수정되면 True."""
    unknown = set(fields) - _UPDATABLE
    if unknown:
        raise ValueError(f"수정할 수 없는 필드: {sorted(unknown)}")
    if not fields:
        return False
    assignments = ", ".join(f"{name} = ?" for name in fields)
    cur = conn.execute(
        f"UPDATE transactions SET {assignments} WHERE id = ?",
        [*fields.values(), tx_id],
    )
    conn.commit()
    return cur.rowcount > 0


def delete_transaction(conn: sqlite3.Connection, tx_id: int) -> bool:
    cur = conn.execute("DELETE FROM transactions WHERE id = ?", (tx_id,))
    conn.commit()
    return cur.rowcount > 0


def set_budget(conn: sqlite3.Connection, category: str, month: str, amount: int) -> None:
    """카테고리의 월 예산을 저장한다 (이미 있으면 덮어쓴다). month는 'YYYY-MM'."""
    if amount < 0:
        raise ValueError("예산은 0 이상이어야 합니다.")
    conn.execute(
        "INSERT INTO budgets (category, month, amount) VALUES (?, ?, ?) "
        "ON CONFLICT(category, month) DO UPDATE SET amount = excluded.amount",
        (category, month, int(amount)),
    )
    conn.commit()


def get_budgets(conn: sqlite3.Connection, month: str) -> dict[str, int]:
    """해당 월의 {카테고리: 예산} 사전을 반환한다."""
    rows = conn.execute("SELECT category, amount FROM budgets WHERE month = ?", (month,)).fetchall()
    return {r["category"]: r["amount"] for r in rows}
