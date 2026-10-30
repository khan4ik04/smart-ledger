
"""은행 거래 내역 파일 가져오기."""

from __future__ import annotations

from pathlib import Path
from typing import BinaryIO

import pandas as pd


REQUIRED_COLUMNS = ["date", "description", "amount"]

COLUMN_ALIASES = {
    "date": [
        "date",
        "거래일",
        "거래일시",
        "날짜",
        "일자",
        "거래일자",
    ],
    "description": [
        "description",
        "적요",
        "거래내용",
        "내용",
        "가맹점명",
        "거래점",
    ],
    "amount": [
        "amount",
        "거래금액",
        "금액",
    ],
    "deposit": [
        "입금액",
        "입금",
        "입금금액",
    ],
    "withdrawal": [
        "출금액",
        "출금",
        "출금금액",
    ],
    "memo": [
        "memo",
        "메모",
        "비고",
    ],
}


def _clean_amount(value) -> int:
    """금액 문자열을 정수로 변환한다."""

    if pd.isna(value) or str(value).strip() == "":
        return 0

    text = str(value).strip()
    negative = text.startswith("-") or (
        text.startswith("(") and text.endswith(")")
    )

    text = (
        text.replace(",", "")
        .replace("원", "")
        .replace("₩", "")
        .replace(" ", "")
        .replace("+", "")
        .replace("-", "")
        .replace("(", "")
        .replace(")", "")
    )

    amount = int(float(text))

    return -amount if negative else amount


def _find_column(df: pd.DataFrame, names: list[str]):
    """컬럼 이름을 비교하여 해당 컬럼을 찾는다."""

    normalized = {
        str(col).strip().casefold(): col
        for col in df.columns
    }

    for name in names:
        if name.casefold() in normalized:
            return normalized[name.casefold()]

    return None


def load_file(
    source: str | Path | BinaryIO,
    filename: str | None = None,
) -> pd.DataFrame:
    """CSV 또는 Excel 파일을 표준 DataFrame으로 변환한다."""

    if filename:
        extension = Path(filename).suffix.lower()
    elif isinstance(source, (str, Path)):
        extension = Path(source).suffix.lower()
    else:
        extension = Path(getattr(source, "name", "")).suffix.lower()

    if extension == ".csv":
        try:
            df = pd.read_csv(source, encoding="utf-8-sig")
        except UnicodeDecodeError:
            if hasattr(source, "seek"):
                source.seek(0)
            df = pd.read_csv(source, encoding="cp949")

    elif extension in [".xlsx", ".xls"]:
        df = pd.read_excel(source)

    else:
        raise ValueError("CSV 또는 Excel 파일만 지원합니다.")

    date_col = _find_column(df, COLUMN_ALIASES["date"])
    description_col = _find_column(
        df, COLUMN_ALIASES["description"]
    )

    if date_col is None or description_col is None:
        raise ValueError("날짜 또는 거래내용 컬럼을 찾을 수 없습니다.")

    amount_col = _find_column(df, COLUMN_ALIASES["amount"])
    deposit_col = _find_column(df, COLUMN_ALIASES["deposit"])
    withdrawal_col = _find_column(df, COLUMN_ALIASES["withdrawal"])

    if amount_col is not None:
        amount = df[amount_col].apply(_clean_amount)

    elif deposit_col is not None or withdrawal_col is not None:
        deposit = (
            df[deposit_col].apply(_clean_amount)
            if deposit_col is not None
            else 0
        )

        withdrawal = (
            df[withdrawal_col].apply(_clean_amount).abs()
            if withdrawal_col is not None
            else 0
        )

        amount = deposit - withdrawal

    else:
        raise ValueError("금액 컬럼을 찾을 수 없습니다.")

    memo_col = _find_column(df, COLUMN_ALIASES["memo"])

    result = pd.DataFrame({
        "date": pd.to_datetime(
            df[date_col], errors="coerce"
        ).dt.strftime("%Y-%m-%d"),
        "description": df[description_col].fillna("").astype(str).str.strip(),
        "amount": amount,
    })

    result["memo"] = (
        df[memo_col].fillna("").astype(str)
        if memo_col is not None
        else ""
    )

    result = result.dropna(subset=["date"])
    result = result[result["description"] != ""]

    return result.reset_index(drop=True)


def remove_duplicates(
    new: pd.DataFrame,
    existing: pd.DataFrame,
) -> pd.DataFrame:
    """기존 DB 거래와 중복되는 거래를 제거한다."""

    if new.empty:
        return new.copy()

    result = new.copy()

    result = result.drop_duplicates(
        subset=REQUIRED_COLUMNS
    )

    if existing is not None and not existing.empty:
        existing_keys = set(
            zip(
                existing["date"].astype(str),
                existing["description"].astype(str),
                pd.to_numeric(
                    existing["amount"], errors="coerce"
                ).fillna(0),
            )
        )

        new_keys = list(
            zip(
                result["date"].astype(str),
                result["description"].astype(str),
                pd.to_numeric(
                    result["amount"], errors="coerce"
                ).fillna(0),
            )
        )

        result = result.loc[
            [
                key not in existing_keys
                for key in new_keys
            ]
        ]

    return result.reset_index(drop=True)
