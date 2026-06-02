# 로그인, 세션, API 키, 배포 보안

## 현재 구현 범위

- Streamlit 로컬 앱
- PBKDF2 비밀번호 해시 기반 개발용 로그인
- 사용자별 JSON 파일 저장
- API 키는 환경변수에서 읽음
- 실제 주문은 잠금 상태

## 운영 환경에서 바꿔야 할 부분

1. 인증: Auth.js, Supabase Auth, Cognito, Auth0, 사내 OIDC 중 하나를 사용하세요.
2. 세션: HTTPS 전용 쿠키, `HttpOnly`, `Secure`, `SameSite`, 세션 만료와 강제 로그아웃이 필요합니다.
3. API 키 저장: `.terminal_data` JSON에 민감정보를 저장하지 말고 KMS, Vault, Secret Manager를 사용하세요.
4. 브로커 주문: Paper/Live 계좌와 버튼을 명확히 분리하고, Live 주문은 2단계 확인과 서버측 리스크 체크를 거치세요.
5. 로그: API 키, 계좌번호, 주문 토큰을 기록하지 마세요.

## Nginx 예시

```nginx
server {
    listen 443 ssl http2;
    server_name terminal.example.com;

    ssl_certificate /etc/letsencrypt/live/terminal.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/terminal.example.com/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-Proto https;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```
