# pipeline-worker 이미지.
#
# ⭑ **이전 판은 「빈 단위」였다** — pip install 이 한 줄도 없고 CMD 가 헬스 서버 단독이었다.
#   그래서 이 컨테이너는 **살아 있다고 대답만 하고 아무것도 하지 않았고**, `upload.ready` 가
#   영원히 false 라 FE 가 1초마다 무한 폴링했다. `〈73〉` 이 실측으로 밝힌 그 자리를 여기서 닫는다:
#   **비동기 기계를 걷어내는 것이 아니라 켜는 것이다.**
#
# 의존은 requirements.txt(전이까지 전부 핀한 닫힘)만 쓴다 — core-api Dockerfile 과 같은 규칙이다.
# requirements.in 을 설치하면 같은 Dockerfile 이 날마다 다른 트리를 만든다.
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 PIP_NO_CACHE_DIR=1
WORKDIR /app

# geo 스택(rasterio·pyhdf·netCDF4·pyproj)이 여기 들어온다. **core-api 에는 한 줄도 안 들어간다**
# (`CLAUDE.md §3-4` · `banned-import` 게이트). 그 분리가 이 배포 단위가 따로 있는 이유다.
COPY requirements.txt /app/requirements.txt
RUN pip install --no-deps -r /app/requirements.txt

COPY src/ /app/src/
ENV PYTHONPATH=/app/src COLAB_HEALTH_PORT=8000

# 비루트로 돈다.
RUN useradd --system --create-home --uid 10001 colab
USER colab

EXPOSE 8000
# **헬스 + 워커 루프**. 헬스만 걸면 아무것도 안 하는 컨테이너가 healthy 로 보이고,
# 루프만 걸면 오케스트레이터가 생사를 못 본다 — `app.worker:main` 이 둘을 함께 돈다.
# 접속 문자열·경계 주체·저장처는 환경변수로만 들어온다. 이미지에 값을 굽지 않는다.
CMD ["python", "-m", "colab_pipeline.app.worker"]
