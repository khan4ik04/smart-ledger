# 💰 Smart Ledger — 스마트 가계부 관리 시스템

은행 거래 내역을 불러와 지출을 **자동으로 분류**하고, **예산 초과를 알려 주며**, 월별 소비 패턴을 **그래프**로 보여 주는 Python 기반 오픈소스 가계부입니다.
모든 데이터는 사용자 PC의 SQLite 파일에만 저장되며 외부로 전송되지 않습니다.

[![CI](../../actions/workflows/ci.yml/badge.svg)](../../actions/workflows/ci.yml)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)

## 주요 기능

| 기능 | 상태 |
|---|---|
| 수입·지출 등록·수정·삭제·조회 | ✅ 완료 |
| 은행 CSV/Excel 가져오기 + 중복 제거 | ✅ 완료 |
| 가맹점명 키워드 자동 카테고리 분류 | ✅ 완료 |
| 월별·카테고리별 통계와 그래프 | ✅ 완료 |
| 카테고리별 예산 + 80%·100% 경고 | 🟡 DB 완료, 계산·화면 진행 중 |

## 설치 및 실행

```bash
git clone https://github.com/khan4ik04/smart-ledger.git
cd smart-ledger
python -m venv .venv
# Windows: .venv\Scripts\activate   /   macOS·Linux: source .venv/bin/activate
pip install -r requirements-dev.txt
streamlit run app/main.py
```

브라우저에서 http://localhost:8501 이 열립니다. 예시 데이터는 `data/sample_transactions.csv`입니다.

## 테스트

```bash
pytest --cov=app
ruff check .
```

## 프로젝트 구조

```
app/
  main.py          Streamlit 진입점
  db/              SQLite 저장소 (거래 CRUD, 예산)
  importer/        파일 가져오기, 자동 카테고리 분류
  analytics/       통계, 차트, 예산 경고
  ui/              화면
data/              예시 데이터, 분류 규칙(category_rules.json)
docs/              설계 문서
tests/             pytest 테스트
```

모듈 간 함수 규약은 [docs/architecture.md](docs/architecture.md)를 참고하세요.

## 기여하기

[CONTRIBUTING.md](CONTRIBUTING.md)를 먼저 읽어 주세요. 분류 키워드 추가는 `data/category_rules.json`만 고치면 되는 좋은 첫 기여입니다.

## 사용한 오픈소스

| 프로젝트 | 용도 | 라이선스 |
|---|---|---|
| [Streamlit](https://github.com/streamlit/streamlit) | 웹 UI | Apache 2.0 |
| [pandas](https://github.com/pandas-dev/pandas) | 데이터 처리 | BSD-3-Clause |
| [Plotly](https://github.com/plotly/plotly.py) | 차트 | MIT |
| [openpyxl](https://foss.heptapod.net/openpyxl/openpyxl) | Excel 읽기 | MIT |
| [pytest](https://github.com/pytest-dev/pytest) | 테스트 | MIT |
| [SQLite](https://www.sqlite.org) | 데이터베이스 | Public Domain |

## 라이선스

[MIT](LICENSE) © 2026 Smart Ledger Team
