# ai-service — D9 Ontology · D10 AI Services (`K4-a` 로 처음 채워졌다).
#
# ⚠ 헬스 경로·포트를 바꾸지 않았다 — `/healthz` · 8200. staging(`infra/staging/`)이 그 값으로
#    배선돼 있고 `infra/` 는 이 레인의 소유 디렉터리가 아니다. 다만 **응답 본문의
#    `implemented` 가 false → true 로 바뀐다**(이제 검색 표면이 실제로 있다).
#
# ⚠ **DB URL 두 개는 아직 compose 에 없다** — `COLAB_AI_CATALOG_DB_URL`(D3 검색 색인, 읽기 전용
#    앱 롤) · `COLAB_AI_DB_URL`(`db/ai` 사전 3종). 배선은 인프라 레인의 일이고, 값이 없으면
#    이 서비스는 죽지 않고 **뒤진 범위를 먼저 밝힌 빈 결과 + degraded** 를 낸다.
#
# geo 라이브러리는 한 줄도 들어오지 않는다 (`gates/config/boundaries.toml` units.ai-service).
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /app

# 런타임 의존은 닫힘 파일 하나로 고정한다 — 같은 입력이면 같은 트리.
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --disable-pip-version-check -r /app/requirements.txt

COPY src/ /app/src/
ENV PYTHONPATH=/app/src

# 비루트로 돈다.
RUN useradd --system --create-home --uid 10001 colab
USER colab

EXPOSE 8200
CMD ["python", "-m", "uvicorn", "--factory", "colab_ai.app.main:create_app", \
     "--host", "0.0.0.0", "--port", "8200"]
