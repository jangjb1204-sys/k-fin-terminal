# K-Fin Terminal

한국어 기반 미국주식 금융 터미널입니다. 토스증권 Open API만 사용해 미국 주식/ETF, 한국 주식, USD/KRW 환율, 캔들 차트, 종목정보, 매수 유의사항을 다룹니다. 개인용 커스텀 앱이라 로그인 기능은 제거했고, 옵션/주문 기능도 제외했습니다.

## 로컬 실행

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
streamlit run app.py
```

브라우저에서 `http://localhost:8501`을 엽니다.

## 기능

- 단일 사용자: 로그인 없이 토스 시장 데이터, 차트, 포트폴리오, 종목정보 조회
- 로컬 저장: 포트폴리오, 기본 종목, 레이아웃 설정 저장
- 데이터: 토스증권 현재가, 캔들, USD/KRW 환율, 종목 기본정보, 매수 유의사항
- 차트: 토스 캔들 기반 가격선, 거래량, MA20. RSI/MACD/Bollinger는 계산 확장 예정
- 기간/인터벌: `1mo`, `3mo`, `6mo`, `1y`, `2y`, `5y`, `10y` 및 토스 지원 인터벌 `1d`, `1m`
- 포트폴리오: 수동 입력/수정, 평가금액, 손익
- UI: 상단 전역 메뉴, 명령창, 토스 전용 상태 버튼, 토스 시세 스트립, 실제 전환 탭, 드래그/리사이즈 레이아웃
- 옵션/주문: 현재 범위에서 제외

## Docker 실행

```bash
cp .env.example .env
docker compose up --build
```

## 필요한 API 키

토스증권 데이터를 보려면 아래 두 키가 필요합니다.

```bash
TOSS_CLIENT_ID=your_client_id
TOSS_CLIENT_SECRET=your_client_secret
```

우선순위는 [API_KEYS.md](API_KEYS.md)에 정리했습니다.

## 데이터 정책

앱은 실제처럼 보이는 가짜 숫자를 만들지 않습니다.

- `실제 데이터`: 계약된 실시간 API 또는 검증 가능한 실시간 소스
- `지연 데이터`: 토스증권 Open API처럼 실시간 보장 범위가 명시되지 않은 조회 데이터
- `API 필요`: 키, 권한, 유료 데이터 계약이 필요한 데이터
- `데이터 없음`: 소스가 빈 응답을 반환했거나 티커가 지원되지 않음

## 배포

```bash
cp .env.example .env
docker compose up -d --build
```

운영 서버에서는 Nginx/Caddy로 HTTPS를 종료하고, Streamlit은 내부 포트로만 노출하세요. 사용자/포트폴리오/레이아웃은 운영 DB로 이전하는 것이 좋습니다.

## 레이아웃 커스터마이징

`모니터` 또는 `레이아웃` 탭의 패널 경계와 박스는 브라우저에서 드래그/리사이즈할 수 있습니다. 현재 데모 레이아웃은 브라우저 `localStorage`에 저장됩니다.
