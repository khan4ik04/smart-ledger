"""가맹점명 키워드 기반 자동 카테고리 분류."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd

DEFAULT_RULES_PATH = Path(__file__).resolve().parents[2] / "data" / "category_rules.json"

UNCATEGORIZED = "미분류"


def load_rules(
    path: str | Path = DEFAULT_RULES_PATH,
) -> dict[str, list[str]]:
    """카테고리 규칙을 JSON 파일에서 읽는다."""

    path = Path(path)

    if not path.exists():
        return {}

    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_rules(
    rules: dict[str, list[str]],
    path: str | Path = DEFAULT_RULES_PATH,
) -> None:
    """카테고리 규칙을 JSON 파일에 저장한다."""

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(rules, f, ensure_ascii=False, indent=4)


def add_rule(
    category: str,
    keyword: str,
    path: str | Path = DEFAULT_RULES_PATH,
) -> dict[str, list[str]]:
    """사용자 키워드 규칙을 추가하고 저장한다."""

    category = category.strip()
    keyword = keyword.strip()

    if not category or not keyword:
        raise ValueError("카테고리와 키워드를 입력해야 합니다.")

    rules = load_rules(path)

    if category not in rules:
        rules[category] = []

    normalized = keyword.casefold()

    existing = [item.casefold() for item in rules[category]]

    if normalized not in existing:
        rules[category].append(keyword)

    save_rules(rules, path)

    return rules


def categorize(
    description: str,
    rules: dict[str, list[str]],
    amount: int | float | None = None,
) -> str:
    """거래 설명과 금액 부호를 기준으로 카테고리를 정한다."""

    description = " ".join(str(description).casefold().split())

    for category, keywords in rules.items():
        if amount is not None:
            if category == "수입" and amount <= 0:
                continue
            if category != "수입" and amount >= 0:
                continue

        for keyword in keywords:
            keyword = " ".join(str(keyword).casefold().split())

            if not keyword:
                continue

            if keyword.isascii() and keyword.isalnum():
                pattern = rf"(?<![a-z0-9]){re.escape(keyword)}(?![a-z0-9])"
                matched = re.search(pattern, description) is not None
            elif keyword == "이자":
                matched = re.search(r"이자(?![가-힣])", description) is not None
            else:
                matched = keyword.replace(" ", "") in description.replace(" ", "")

            if matched:
                return category

    return UNCATEGORIZED


def categorize_frame(
    df: pd.DataFrame,
    rules: dict[str, list[str]],
) -> pd.DataFrame:
    """거래 DataFrame에 category 열을 추가한다."""

    if "description" not in df.columns:
        raise ValueError("description 컬럼이 필요합니다.")

    result = df.copy()

    if "amount" in result.columns:
        result["category"] = result.apply(
            lambda row: categorize(row["description"], rules, row["amount"]),
            axis=1,
        )
    else:
        result["category"] = result["description"].apply(lambda value: categorize(value, rules))

    return result
