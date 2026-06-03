# 단일 사용자, API 키, 배포 보안

## 현재 구현 범위

- Streamlit 로컬 앱
- 로그인 없음
- 단일 사용자용 로컬 JSON 파일 저장
- API 키는 환경변수에서 읽음
- 실제 주문은 잠금 상태

## 운영 환경에서 바꿔야 할 부분

1. 앱을 혼자 보더라도 HTTPS는 사용하세요.
2. API 키는 `.terminal_data` JSON에 저장하지 말고 Streamlit Secrets, Vercel Environment Variables, Secret Manager를 사용하세요.
3. 브로커 주문: Paper/Live 계좌와 버튼을 명확히 분리하고, Live 주문은 2단계 확인과 서버측 리스크 체크를 거치세요.
4. 로그: API 키, 계좌번호, 주문 토큰을 기록하지 마세요.
5. 공개 URL을 공유하지 않는 개인용이라면 별도 로그인은 생략해도 됩니다. URL이 유출될 수 있는 환경이면 Vercel Password Protection이나 Cloudflare Access를 붙이세요.

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
