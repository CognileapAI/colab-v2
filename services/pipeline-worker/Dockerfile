# pipeline-worker — walking skeleton 이미지 (WU-I2).
#
# 이 단위는 아직 비어 있다. 그래서 이미지도 **런타임 의존이 0** 이다 —
# pip install 이 한 줄도 없고, 들어가는 것은 소스 트리와 표준 라이브러리뿐이다.
# 실제 스택(프레임워크·큐 클라이언트 등)은 이 단위를 채우는 WU 가 고른다.
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /app
COPY src/ /app/src/
ENV PYTHONPATH=/app/src COLAB_HEALTH_PORT=8000

# 비루트로 돈다.
RUN useradd --system --create-home --uid 10001 colab
USER colab

EXPOSE 8000
CMD ["python", "-m", "colab_pipeline.app.health"]
