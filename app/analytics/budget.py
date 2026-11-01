"""예산 대비 사용률과 경고."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from app.analytics.stats import by_category

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
    """한 달치 거래와 {카테고리: 예산(0 이상)}으로 설정된 예산별 상태를 계산한다.

    지출(음수)만 합산하며 spent는 양수이다. 거래가 없는 카테고리도 반환한다.
    예산이 0원이면 지출이 없을 때 ratio=0.0/ok, 지출이 있으면 ratio=inf/over이다.
    UI 진행 막대에는 min(status.ratio, 1.0)을 사용하고, 0원 예산은 별도로 표시한다.
    """
    spent_by_category = {}
    if not df.empty:
        spent_by_category = by_category(df).set_index("category")["total"].to_dict()

    result = []
    for category, budget in budgets.items():
        spent = int(spent_by_category.get(category, 0))
        if budget == 0:
            ratio = float("inf") if spent else 0.0
        else:
            ratio = spent / budget

        if ratio >= OVER_RATIO:
            level = "over"
        elif ratio >= WARNING_RATIO:
            level = "warning"
        else:
            level = "ok"
        result.append(BudgetStatus(category, budget, spent, ratio, level))
    return result
