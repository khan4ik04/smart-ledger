"""예산 대비 사용률과 경고.

TODO(담당: 분석·시각화)
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

WARNING_RATIO = 0.8
OVER_RATIO = 1.0


@dataclass
class BudgetStatus:
    category: str
    budget: int
    spent: int  # 양수
    ratio: float  # spent / budget
    level: str  # 'ok' | 'warning'(80% 이상) | 'over'(100% 이상)


def check_budgets(df: pd.DataFrame, budgets: dict[str, int]) -> list[BudgetStatus]:
    """한 달치 거래(df)와 {카테고리: 예산}으로 카테고리별 상태를 계산한다."""
    raise NotImplementedError("TODO(분석·시각화): check_budgets 구현")
