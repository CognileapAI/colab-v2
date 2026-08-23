# viz-render — D7 Visualization (WU-P2 · `〈63〉-㉮` 로 처음 채워졌다).
#
# **geo 라이브러리가 이 이미지에만 들어간다** (`CLAUDE.md §3-4`). core-api 이미지에
# rasterio·netCDF4·pyhdf 가 없다는 사실이 불변규칙 4 의 배포 쪽 표현이다.
#
# ⚠ 헬스 경로·포트를 바꾸지 않았다 — `/healthz` · 8100. staging(`infra/staging/`)이
#    그 값으로 배선돼 있고 `infra/` 는 이 레인의 소유 디렉터리가 아니다.
#    다만 **응답 본문의 `implemented` 가 false → true 로 바뀐다** (이제 실제로 구현됐다).
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /app

# 런타임 의존은 닫힘 파일 하나로 고정한다 — 같은 입력이면 같은 트리.
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --disable-pip-version-check -r /app/requirements.txt

COPY src/ /app/src/
ENV PYTHONPATH=/app/src

# 그릴 파일의 자리와 서비스 자격 증명. **둘 다 없어도 프로세스는 뜨고**,
# 자격 증명이 없으면 렌더 표면이 503 을 낸다 (인증을 끄지 않는다 — `kernel/config.py`).
ENV COLAB_VIZ_SOURCE_ROOT=/srv/viz-sources

RUN useradd --system --create-home --uid 10001 colab \
 && mkdir -p /srv/viz-sources && chown colab /srv/viz-sources
USER colab

EXPOSE 8100
CMD ["python", "-m", "uvicorn", "--factory", "colab_viz.app.main:create_app", \
     "--host", "0.0.0.0", "--port", "8100"]
