"""파일 가져오기·자동 분류 (담당: 데이터 처리)."""

from .loader import load_file, remove_duplicates
from .categorizer import (
    load_rules,
    save_rules,
    add_rule,
    categorize,
    categorize_frame,
)

__all__ = [
    "load_file",
    "remove_duplicates",
    "load_rules",
    "save_rules",
    "add_rule",
    "categorize",
    "categorize_frame",
]