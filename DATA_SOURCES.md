# 데이터 출처와 제한 사항

| 영역 | 기본 소스 | 상태 표시 | 제한 |
|---|---|---|---|
| 미국 주식/ETF | Yahoo Finance via `yfinance` | 지연 데이터 | 실시간 보장 없음, 호출 제한 가능 |
| 지수 | Yahoo Finance | 지연 데이터 | 일부 지수 심볼 미지원 가능 |
| 금리 | Yahoo Finance `^TNX` | 지연 데이터 | 수익률 표기 방식 확인 필요 |
| 원자재 | Yahoo Finance futures symbols | 지연 데이터 | 선물 만기/연속물 차이 |
| 환율 | Yahoo Finance FX symbols | 지연 데이터 | 은행 고시환율과 다를 수 있음 |
| 한국 주식 | Yahoo Finance `.KS`, `.KQ` | 지연 데이터 | 일부 종목/거래량 제한 |
| 뉴스 | Yahoo Finance News | 지연 데이터 | 제공 기사 수와 원문 접근 제한 |
| 배당/ETF 보유 | 제공자별 API | API 필요 | Yahoo 무료 데이터는 제한적 |

## 권장 상용/API 소스

- 미국 근실시간/집계 시세: Polygon.io, IEX Cloud, Nasdaq Data Link
- SEC: `data.sec.gov/submissions` 및 `companyfacts`, `SEC_USER_AGENT` 필수
- 한국 DART: OpenDART, `DART_OPEN_API_KEY` 필요
- 포트폴리오: 현재는 수동 입력/로컬 저장
- AI 번역/분석: Gemini API

## 가짜 데이터 금지 정책

실패한 API 응답을 임의 숫자로 대체하지 않습니다. UI에는 항상 다음 중 하나를 표시합니다.

- `실제 데이터`
- `지연 데이터`
- `API 필요`
- `데이터 없음`

포트폴리오의 예시 행은 로그인 직후 기능 확인을 위한 사용자 파일 초기값이며, 사용자가 수정/삭제할 수 있습니다. 시장 가격 자체는 API 응답이 없으면 계산하지 않습니다.
