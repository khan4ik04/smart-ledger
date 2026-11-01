import pandas as pd
import pytest

from app.importer.loader import (
    _clean_amount,
    load_file,
    remove_duplicates,
)


def test_clean_amount_handles_unicode_minus():
    assert _clean_amount("−7000") == -7000


def test_load_file_with_korean_columns_and_amount_formats(tmp_path):
    source = tmp_path / "transactions.csv"
    pd.DataFrame(
        {
            "거래일": ["2026-10-01", "2026-10-02"],
            "거래내용": ["월급", "카페"],
            "금액": ["1,000원", "(500)"],
        }
    ).to_csv(source, index=False, encoding="utf-8-sig")

    result = load_file(source)

    assert result["description"].tolist() == ["월급", "카페"]
    assert result["amount"].tolist() == [1000, -500]


def test_load_file_with_deposit_and_withdrawal_columns(tmp_path):
    source = tmp_path / "transactions.csv"
    pd.DataFrame(
        {
            "거래일": ["2026-10-01", "2026-10-02"],
            "거래내용": ["월급", "카페"],
            "입금액": ["2,000", ""],
            "출금액": ["", "500"],
        }
    ).to_csv(source, index=False, encoding="utf-8-sig")

    result = load_file(source)

    assert result["amount"].tolist() == [2000, -500]


def test_load_file_reads_cp949_csv(tmp_path):
    source = tmp_path / "transactions.csv"
    pd.DataFrame(
        {
            "거래일": ["2026-10-01"],
            "거래내용": ["급여"],
            "금액": ["1000"],
        }
    ).to_csv(source, index=False, encoding="cp949")

    result = load_file(source)

    assert result["description"].tolist() == ["급여"]
    assert result["amount"].tolist() == [1000]


def test_load_file_accepts_mixed_date_formats(tmp_path):
    source = tmp_path / "transactions.csv"
    pd.DataFrame(
        {
            "거래일": ["2026-10-01", "2026.10.02", "2026/10/03"],
            "거래내용": ["A", "B", "C"],
            "금액": [-100, -200, -300],
        }
    ).to_csv(source, index=False, encoding="utf-8-sig")

    result = load_file(source)

    assert result["date"].tolist() == [
        "2026-10-01",
        "2026-10-02",
        "2026-10-03",
    ]


def test_load_file_reports_rows_with_unreadable_dates(tmp_path):
    source = tmp_path / "transactions.csv"
    pd.DataFrame(
        {
            "거래일": ["2026-10-01", "날짜오류"],
            "거래내용": ["정상 거래", "날짜 없는 거래"],
            "금액": [-100, -200],
        }
    ).to_csv(source, index=False, encoding="utf-8-sig")

    with pytest.raises(ValueError, match="행이 있습니다: 3"):
        load_file(source)


def test_remove_duplicates_matches_existing_db_but_preserves_file_repeats():
    transaction = {
        "date": "2026-10-01",
        "description": "같은 가게",
        "amount": -1000,
        "memo": "",
    }
    new = pd.DataFrame([transaction, transaction])
    existing = pd.DataFrame([transaction])

    result = remove_duplicates(new, existing)

    assert len(result) == 1
    assert result.iloc[0]["description"] == "같은 가게"


def test_remove_duplicates_keeps_identical_transactions_in_new_file():
    transaction = {
        "date": "2026-10-01",
        "description": "같은 가게",
        "amount": -1000,
        "memo": "",
    }

    result = remove_duplicates(
        pd.DataFrame([transaction, transaction]),
        pd.DataFrame(),
    )

    assert len(result) == 2


def test_remove_duplicates_respects_repeated_records_already_in_db():
    transaction = {
        "date": "2026-10-01",
        "description": "같은 가게",
        "amount": -1000,
        "memo": "",
    }

    result = remove_duplicates(
        pd.DataFrame([transaction, transaction]),
        pd.DataFrame([transaction, transaction]),
    )

    assert result.empty


def test_load_file_rejects_legacy_xls(tmp_path):
    source = tmp_path / "transactions.xls"
    source.write_bytes(b"")

    with pytest.raises(ValueError, match="CSV 또는 XLSX"):
        load_file(source)
