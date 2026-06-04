# API 키 정리

개인용 앱이라 로그인은 필요 없습니다. API 키는 로컬 `.env`, Streamlit Secrets, Docker 환경변수, 또는 서버 Secret Manager에 넣습니다. 브라우저에 직접 노출하면 안 됩니다.

## 필수

| 키 | 용도 | 없을 때 |
|---|---|---|
| `TOSS_CLIENT_ID` | 토스증권 OAuth2 토큰 발급 | 토스 데이터가 `API 필요` |
| `TOSS_CLIENT_SECRET` | 토스증권 OAuth2 토큰 발급 | 토스 데이터가 `API 필요` |

## 토스증권 사용 범위

- 사용: OAuth 토큰, 현재가, 캔들, USD/KRW 환율, 종목 기본정보, 매수 유의사항
- 제외: 주문 생성, 주문 정정, 주문 취소, 옵션
- 제거: 뉴스 API, Gemini, SEC, DART, 별도 지수/원자재/금리 데이터 API

토스증권 OAuth는 client당 유효 토큰이 1개라서 앱 서버에서 토큰을 캐시합니다. 운영에서 서버 인스턴스를 여러 개 띄우면 외부 캐시나 단일 API 프록시를 두는 편이 안정적입니다.
