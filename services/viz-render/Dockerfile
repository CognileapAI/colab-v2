# viz-render — D7 Visualization (WU-P2 · `〈63〉-㉮` 로 처음 채워졌다).
#
# **geo 라이브러리가 이 이미지에만 들어간다** (`CLAUDE.md §3-4`). core-api 이미지에
# rasterio·netCDF4·pyhdf 가 없다는 사실이 불변규칙 4 의 배포 쪽 표현이다.
#
# ⚠ 헬스 경로·포트를 바꾸지 않았다 — `/healthz` · 8100. staging(`infra/staging/`)이
#    그 값으로 배선돼 있고 `infra/` 는 이 레인의 소유 디렉터리가 아니다.
#    다만 **응답 본문의 `implemented` 가 false → true 로 바뀐다** (이제 실제로 구현됐다).
# ── 1단계: 빌드 ─────────────────────────────────────────────────────────────
# **왜 두 단계인가 (2026-08-31 실측 · 배포 계획서 §6-1).** `pyhdf` 는 **linux/arm64 휠을 내지 않는다**
# (PyPI 실측: mac-arm64 · linux-**x86_64** · win 뿐). dev EC2 가 arm64(t4g)라 거기서는 소스로 컴파일해야
# 하고, 한 단계 빌드면 **실행 이미지에 컴파일러가 그대로 남는다.** 빌드 도구는 여기서 쓰고 버린다.
# x86_64(현 staging)에서는 휠이 있어 아래 경로 값이 쓰이지 않는다 — 두 아키텍처가 같은 파일로 돈다.
# ⚠ 이 값들은 pipeline-worker 의 것과 **같아야 한다** — 두 단위가 같은 `pyhdf` 를 쓴다.
FROM python:3.12-slim AS builder

ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 PIP_NO_CACHE_DIR=1

RUN apt-get update \
 && apt-get install -y --no-install-recommends build-essential libhdf4-alt-dev zlib1g-dev libjpeg-dev \
 && rm -rf /var/lib/apt/lists/*

# 런타임 의존은 닫힘 파일 하나로 고정한다 — 같은 입력이면 같은 트리.
COPY requirements.txt /tmp/requirements.txt
# `pyhdf` 소스 빌드가 HDF4 를 찾는 자리(데비안 `alt` 변종 = netCDF 인터페이스를 뺀 것).
# 경로를 손으로 박지 않고 `dpkg-architecture` 로 묻는다 — 아키텍처가 바뀌면 조용히 틀리기 때문이다.
RUN INCLUDE_DIRS=/usr/include/hdf \
    LIBRARY_DIRS=/usr/lib/$(dpkg-architecture -qDEB_HOST_MULTIARCH) \
    LIBRARIES=mfhdfalt,dfalt,jpeg,z \
    pip install --disable-pip-version-check --prefix=/install -r /tmp/requirements.txt

# ── 2단계: 실행 ─────────────────────────────────────────────────────────────
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /app

# OS 공유 라이브러리 — **실측으로 확정한 최소 집합**.
# rasterio 휠이 싣고 오는 `rasterio.libs/libgdal-*.so.38` 이 `libexpat.so.1` 을 OS 에서 찾는다.
# 그것 하나가 없어 staging 의 렌더가 `RENDER_UNKNOWN_ERROR: ImportError libexpat.so.1` 로 끝났다.
# 실측 = 컨테이너 내부 `find site-packages -name '*.so*' -exec ldd {} +` 의 `not found` 중
# **해시 접미사가 없는 것은 `libexpat.so.1` 하나뿐**이다 (해시본은 휠 번들이라 RPATH 로 풀린다).
# 「혹시 몰라서」 더 넣지 않는다.
# `libhdf4-0-alt`·`libjpeg62-turbo` 는 **소스로 지은 `pyhdf` 가 실행 때 찾는 것**이다(arm64 경로).
RUN apt-get update \
 && apt-get install -y --no-install-recommends libexpat1 libhdf4-0-alt libjpeg62-turbo \
 && rm -rf /var/lib/apt/lists/*

COPY --from=builder /install /usr/local

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
