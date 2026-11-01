import json

import pandas as pd

from app.importer.categorizer import (
    UNCATEGORIZED,
    add_rule,
    categorize,
    categorize_frame,
    load_rules,
)


def test_categorize_matches_keyword_and_handles_unknown_store():
    rules = {"카페": ["스타벅스"]}

    assert categorize("스타벅스 강남점", rules) == "카페"
    assert categorize("처음 보는 가게", rules) == UNCATEGORIZED


def test_short_keywords_do_not_match_inside_other_words():
    rules = {
        "수입": ["이자"],
        "통신": ["KT"],
        "편의점": ["CU"],
    }

    assert categorize("이자카야", rules) == UNCATEGORIZED
    assert categorize("KTX 승차권", rules) == UNCATEGORIZED
    assert categorize("CUCKOO 정수기", rules) == UNCATEGORIZED
    assert categorize("KT 요금", rules) == "통신"
    assert categorize("CU 편의점", rules) == "편의점"


def test_categorize_frame_uses_amount_sign_and_keeps_input_unchanged():
    rules = {
        "카페": ["스타벅스"],
        "수입": ["급여"],
    }
    transactions = pd.DataFrame(
        {
            "description": [
                "스타벅스 환불",
                "급여",
                "스타벅스",
                "급여",
            ],
            "amount": [2500, -1000, -4500, 100000],
        }
    )

    result = categorize_frame(transactions, rules)

    assert result["category"].tolist() == [
        UNCATEGORIZED,
        UNCATEGORIZED,
        "카페",
        "수입",
    ]
    assert "category" not in transactions.columns


def test_add_rule_saves_to_temporary_file(tmp_path):
    rules_path = tmp_path / "category_rules.json"

    result = add_rule("카페", "새 매장", rules_path)

    assert result == {"카페": ["새 매장"]}
    assert json.loads(rules_path.read_text(encoding="utf-8")) == result


def test_default_rules_recognize_english_merchant_names():
    rules = load_rules()

    assert categorize("STARBUCKS Store", rules) == "카페"
    assert categorize("McDonald's #123", rules) == "식비"
    assert categorize("Netflix.com", rules) == "문화·여가"
