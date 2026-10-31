# 기여 가이드

## 개발 환경

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
```

## 작업 순서

1. **이슈 확인** — 할 일은 모두 이슈로 등록합니다. 본인을 Assignee로 지정하세요.
2. **브랜치 생성** — `dev`에서 새 브랜치를 만듭니다.
   ```bash
   git switch dev && git pull
   git switch -c feature/csv-import     # 버그면 fix/..., 문서면 docs/...
   ```
3. **작업 + 테스트** — 새 함수에는 `tests/`에 테스트를 추가합니다.
   ```bash
   pytest && ruff check .
   ```
4. **커밋** — [Conventional Commits](https://www.conventionalcommits.org/ko/) 형식
   ```
   feat: 은행 CSV 가져오기 추가
   fix: 금액 쉼표 파싱 오류 수정
   docs: README 설치 방법 보완
   test: categorizer 테스트 추가
   refactor: / chore:
   ```
5. **PR 생성** — 대상 브랜치는 `dev`. 본문에 `Closes #이슈번호`. 팀원 1명 이상 승인 + CI 통과 후 **Merge pull request**.
6. 리뷰 요청을 받으면 **48시간 이내**에 리뷰합니다.

## 규칙

- 모든 작업은 `dev`로 PR을 보냅니다. `dev`에 직접 push 하지 않습니다.
- `main`은 최종 완성본 전용입니다. 프로젝트가 끝났을 때 **팀장만** `dev`의 최종 버전을 `main`에 반영합니다. 팀원은 `main`에 push·PR 하지 않습니다.
- 기여도 확인을 위해 **반드시 본인 GitHub 계정**으로 커밋합니다.
  ```bash
  git config user.name "본인 GitHub 아이디"
  git config user.email "GitHub에 등록한 이메일"
  ```
- **실제 개인 거래 내역 파일·`ledger.db`는 절대 커밋하지 않습니다.** 테스트에는 가짜 데이터만 사용합니다.
- 다른 모듈의 DB 접근은 `app.db`의 함수만 사용합니다 (SQL 직접 작성 금지).
- 모듈 간 함수 이름·인자·반환 형식을 바꿀 때는 [docs/architecture.md](docs/architecture.md)를 함께 수정하고 팀에 공유합니다.
- 새 라이브러리를 추가하면 PR에 라이선스를 적습니다. GPL 계열은 사용하지 않습니다.

## 모듈 담당

| 모듈 | 담당 |
|---|---|
| `app/db/` | 팀장 / 백엔드 |
| `app/importer/` | 데이터 처리 |
| `app/analytics/` | 분석·시각화 |
| `app/ui/`, `app/main.py` | UI |
| `tests/`, `.github/`, 문서 | 테스트·문서화 |
