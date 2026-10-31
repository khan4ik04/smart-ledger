# Changelog

이 프로젝트의 주요 변경 사항을 기록합니다. 형식은 [Keep a Changelog](https://keepachangelog.com/ko/1.1.0/)를 따르고, 버전은 [Semantic Versioning](https://semver.org/lang/ko/)을 따릅니다.

## [Unreleased]

### Added
- 프로젝트 초기 구조, 모듈 인터페이스, CI 설정
- 거래 내역 DB(SQLite) 기본 CRUD, 월별 예산 저장
- 은행 CSV/Excel 가져오기 (한글 열 이름, 입금·출금 열, cp949), 중복 제거
- 가맹점명 키워드 기반 자동 카테고리 분류, 사용자 규칙 추가(`add_rule`)
- 수입·지출 요약, 월별·카테고리별 통계, Plotly 차트
- Streamlit 화면: 대시보드, 내역 입력, 내역 조회·수정·삭제, 파일 가져오기, 통계
- DB 경계 조건 테스트

### Changed
- CI가 `dev` 브랜치 push에서도 실행되도록 변경
