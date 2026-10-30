
"""가맹점명 키워드 기반 자동 카테고리 분류."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

DEFAULT_RULES_PATH = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "category_rules.json"
)

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

    existing = [
        item.casefold() for item in rules[category]
    ]

    if normalized not in existing:
        rules[category].append(keyword)

    save_rules(rules, path)

    return rules


def categorize(
    description: str,
    rules: dict[str, list[str]],
) -> str:
    """거래 설명에 포함된 키워드로 카테고리를 정한다."""

    description = "".join(
        str(description).casefold().split()
    )

    for category, keywords in rules.items():
        for keyword in keywords:
            keyword = "".join(
                str(keyword).casefold().split()
            )

            if keyword and keyword in description:
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

    result["category"] = result["description"].apply(
        lambda x: categorize(x, rules)
    )

    return result
