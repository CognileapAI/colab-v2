# frontend — walking skeleton 이미지 (WU-I2).
#
# 정적 배포다 (frontend/README). 서버 런타임을 두지 않는다 — 빌드 산출물을 nginx 가 낸다.
# 빌드를 이미지 안에서 돌리는 이유: 호스트의 dist/ 를 복사하면 "무엇이 배포됐는가" 가
# 커밋이 아니라 그때그때의 작업트리가 된다. PoC 가 8주 전 수동 빌드 이미지를 돌린 실패가 그것이다.
FROM node:22-slim AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci                       # exact 핀 — 같은 입력이면 같은 트리
COPY . .
RUN npm run build                # tsc --noEmit && vite build → dist/

FROM nginx:1.27-alpine
COPY --from=build /app/dist/ /usr/share/nginx/html/
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 8080
