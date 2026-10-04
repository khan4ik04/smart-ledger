"""은행 거래 내역 파일 가져오기.

TODO(담당: 데이터 처리)
- 은행별 열 이름 차이를 흡수하는 변환 규칙 (최소 2개 은행)
- 금액 문자열 정리 ("1,234원" → 1234), 출금/입금 열 → 부호 있는 amount
- 중복 제거: (date, description, amount)가 같은 행
"""

from __future__ import annotations

from pathlib import Path
from typing import BinaryIO

import pandas as pd

REQUIRED_COLUMNS = ["date", "description", "amount"]


def load_file(source: str | Path | BinaryIO, filename: str | None = None) -> pd.DataFrame:
    """CSV 또는 Excel 파일을 읽어 표준 형식 DataFrame으로 반환한다.

    반환 DataFrame 열: date('YYYY-MM-DD' 문자열), description(str), amount(int), memo(str)
    category 열은 여기서 만들지 않는다 (categorizer가 담당).
    """
    raise NotImplementedError("TODO(데이터 처리): load_file 구현")


def remove_duplicates(new: pd.DataFrame, existing: pd.DataFrame) -> pd.DataFrame:
    """이미 DB에 있는 거래(existing)와 겹치는 행을 new에서 제거해 반환한다."""
    raise NotImplementedError("TODO(데이터 처리): remove_duplicates 구현")
