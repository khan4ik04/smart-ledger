"""가맹점명 키워드 기반 자동 카테고리 분류.

TODO(담당: 데이터 처리)
- data/category_rules.json 규칙 사용
- 사용자 규칙 추가·저장 기능
- 대소문자·공백 차이 무시
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

DEFAULT_RULES_PATH = Path(__file__).resolve().parents[2] / "data" / "category_rules.json"
UNCATEGORIZED = "미분류"


def load_rules(path: str | Path = DEFAULT_RULES_PATH) -> dict[str, list[str]]:
    """{카테고리: [키워드, ...]} 규칙을 읽는다."""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def categorize(description: str, rules: dict[str, list[str]]) -> str:
    """거래 설명에 포함된 키워드로 카테고리를 정한다. 못 찾으면 '미분류'."""
    raise NotImplementedError("TODO(데이터 처리): categorize 구현")


def categorize_frame(df: pd.DataFrame, rules: dict[str, list[str]]) -> pd.DataFrame:
    """df의 description을 보고 category 열을 채운 사본을 반환한다."""
    raise NotImplementedError("TODO(데이터 처리): categorize_frame 구현")
