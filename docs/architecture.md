# 설계: 모듈 구조와 함수 규약

```
 ┌──────────── ui (Streamlit) ────────────┐
 │  대시보드 · 입력 · 조회 · 가져오기 · 통계 · 예산 │
 └──────┬───────────────┬─────────────────┘
        │               │
   importer         analytics
 (loader,          (stats, budget)
  categorizer)          │
        └──────┬────────┘
               ▼
              db  ──►  ledger.db (SQLite, 사용자 PC에만 저장)
```

## 공통 데이터 형식

거래 DataFrame (모든 모듈이 이 형식을 주고받음)

| 열 | 타입 | 설명 |
|---|---|---|
| id | int | DB에서 부여 (가져오기 단계에는 없음) |
| date | str | `YYYY-MM-DD` |
| description | str | 가맹점명·내용 |
| amount | int | 원 단위. **지출은 음수, 수입은 양수** |
| category | str | 분류 실패 시 `미분류` |
| memo | str | 비어 있을 수 있음 |

## 함수 규약

### `app.db` — 팀장 ✅ 구현됨
- `connect(db_path="ledger.db") -> Connection`
- `add_transaction(conn, date, description, amount, category="미분류", memo="") -> int`
- `add_transactions(conn, df) -> int`
- `get_transactions(conn, start=None, end=None, category=None) -> DataFrame`
- `update_transaction(conn, tx_id, **fields) -> bool`
- `delete_transaction(conn, tx_id) -> bool`
- `set_budget(conn, category, month, amount)` / `get_budgets(conn, month) -> dict[str, int]`

### `app.importer` — 데이터 처리
- `loader.load_file(source, filename=None) -> DataFrame` (date, description, amount, memo)
- `loader.remove_duplicates(new, existing) -> DataFrame`
- `categorizer.load_rules(path) -> dict[str, list[str]]` ✅
- `categorizer.categorize(description, rules) -> str`
- `categorizer.categorize_frame(df, rules) -> DataFrame`

### `app.analytics` — 분석·시각화
- `stats.summary(df) -> {"income", "expense", "balance"}`
- `stats.by_category(df) -> DataFrame(category, total, ratio)`
- `stats.by_month(df) -> DataFrame(month, income, expense)`
- `stats.category_pie(df)`, `stats.monthly_line(df) -> plotly Figure`
- `budget.check_budgets(df, budgets) -> list[BudgetStatus]`

### `app.ui` — UI
- `pages.*(conn)` 화면 함수. 미구현 모듈은 `NotImplementedError` → "준비 중" 표시.
