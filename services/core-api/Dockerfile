# core-api — walking skeleton 이미지 (WU-I2).
#
# 의존은 requirements.txt(전이까지 전부 핀한 닫힘)만 쓴다. requirements.in 을 설치하면
# 같은 Dockerfile 이 날마다 다른 트리를 만든다 — 그 재현성이 이 파일의 유일한 목적이다.
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 PIP_NO_CACHE_DIR=1
WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-deps -r /app/requirements.txt

COPY src/ /app/src/
ENV PYTHONPATH=/app/src

RUN useradd --system --create-home --uid 10001 colab
USER colab

EXPOSE 8000
# 접속 문자열·주체 표는 환경변수로만 들어온다 (kernel/config.py). 이미지에 값을 굽지 않는다.
CMD ["python", "-m", "uvicorn", "--factory", "colab_core.app.main:create_app", \
     "--host", "0.0.0.0", "--port", "8000"]
