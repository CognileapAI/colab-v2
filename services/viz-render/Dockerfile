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

# OS 공유 라이브러리 — **실측으로 확정한 최소 집합**.
# rasterio 휠이 싣고 오는 `rasterio.libs/libgdal-*.so.38` 이 `libexpat.so.1` 을 OS 에서 찾는다.
# 그것 하나가 없어 staging 의 렌더가 `RENDER_UNKNOWN_ERROR: ImportError libexpat.so.1` 로 끝났다.
# 실측 = 컨테이너 내부 `find site-packages -name '*.so*' -exec ldd {} +` 의 `not found` 중
# **해시 접미사가 없는 것은 `libexpat.so.1` 하나뿐**이다 (해시본은 휠 번들이라 RPATH 로 풀린다).
# 「혹시 몰라서」 더 넣지 않는다.
RUN apt-get update \
 && apt-get install -y --no-install-recommends libexpat1 \
 && rm -rf /var/lib/apt/lists/*

# 런타임 의존은 닫힘 파일 하나로 고정한다 — 같은 입력이면 같은 트리.
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --disable-pip-version-check -r /app/requirements.txt

# **회귀 방지 — 이미지 안에서 geo 스택 import 가 성립하지 않으면 빌드가 실패한다.**
# 이 결손은 게이트·시험 어디에도 걸리지 않았다. 렌더 요청이 실제로 들어오기 전까지 무증상이고,
# 헬스는 200 을 계속 냈다. 검사를 빌드 단계에 두면 **결손 이미지가 애초에 만들어지지 않는다** —
# 배포 뒤에 알려 주는 것보다 앞이다. 목록은 requirements.in 의 직접 geo 의존과 같다.
RUN python -c "import rasterio, rasterio._env, netCDF4, pyhdf.SD, PIL.Image; print('geo import OK', rasterio.__gdal_version__)"

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
