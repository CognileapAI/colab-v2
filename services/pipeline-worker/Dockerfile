# pipeline-worker 이미지.
#
# ⭑ **이전 판은 「빈 단위」였다** — pip install 이 한 줄도 없고 CMD 가 헬스 서버 단독이었다.
#   그래서 이 컨테이너는 **살아 있다고 대답만 하고 아무것도 하지 않았고**, `upload.ready` 가
#   영원히 false 라 FE 가 1초마다 무한 폴링했다. `〈73〉` 이 실측으로 밝힌 그 자리를 여기서 닫는다:
#   **비동기 기계를 걷어내는 것이 아니라 켜는 것이다.**
#
# 의존은 requirements.txt(전이까지 전부 핀한 닫힘)만 쓴다 — core-api Dockerfile 과 같은 규칙이다.
# requirements.in 을 설치하면 같은 Dockerfile 이 날마다 다른 트리를 만든다.
# ── 1단계: 빌드 ─────────────────────────────────────────────────────────────
# **왜 두 단계인가 (2026-08-31 실측 · 배포 계획서 §6-1).** `pyhdf` 는 **linux/arm64 휠을 내지 않는다**
# (PyPI 실측: mac-arm64 · linux-**x86_64** · win 뿐). dev EC2 가 arm64(t4g)라 거기서는 소스로 컴파일해야
# 하고, 한 단계 빌드면 **실행 이미지에 컴파일러가 그대로 남는다.** 빌드 도구는 여기서 쓰고 버린다.
# x86_64(현 staging)에서는 휠이 있어 아래 경로 값이 쓰이지 않는다 — 두 아키텍처가 같은 파일로 돈다.
FROM python:3.12-slim AS builder

ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 PIP_NO_CACHE_DIR=1

RUN apt-get update \
 && apt-get install -y --no-install-recommends build-essential libhdf4-alt-dev zlib1g-dev libjpeg-dev \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /tmp/requirements.txt
# `pyhdf` 소스 빌드가 HDF4 를 찾는 자리. 데비안은 헤더를 `/usr/include/hdf`, 라이브러리를
# `/usr/lib/<multiarch>` 에 두고 **`alt` 변종**(netCDF 인터페이스를 뺀 것)으로 이름을 짓는다 —
# `mfhdfalt`·`dfalt`. 경로를 손으로 박으면 아키텍처가 바뀔 때 조용히 틀리므로 `dpkg-architecture` 로 묻는다.
RUN INCLUDE_DIRS=/usr/include/hdf \
    LIBRARY_DIRS=/usr/lib/$(dpkg-architecture -qDEB_HOST_MULTIARCH) \
    LIBRARIES=mfhdfalt,dfalt,jpeg,z \
    pip install --no-deps --prefix=/install -r /tmp/requirements.txt

# ── 2단계: 실행 ─────────────────────────────────────────────────────────────
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 PIP_NO_CACHE_DIR=1
WORKDIR /app

# geo 스택(rasterio·pyhdf·netCDF4·pyproj)이 여기 들어온다. **core-api 에는 한 줄도 안 들어간다**
# (`CLAUDE.md §3-4` · `banned-import` 게이트). 그 분리가 이 배포 단위가 따로 있는 이유다.
# OS 공유 라이브러리 — **실측 최소 집합**. viz-render 와 같은 결손이다:
# rasterio 휠의 `libgdal-*.so.38` 이 `libexpat.so.1` 을 OS 에서 찾는다. 두 단위가 같은 휠을 쓰므로
# 결손도 같다 — 한쪽만 고치면 나머지 한쪽이 조용히 남는다.
# `libhdf4-0-alt`·`libjpeg62-turbo` 는 **소스로 지은 `pyhdf` 가 실행 때 찾는 것**이다(arm64 경로).
# x86_64 에서는 휠이 제 것을 싣고 오므로 남는 무게일 뿐이다 — 한 파일로 두 아키텍처를 덮는 값이다.
RUN apt-get update \
 && apt-get install -y --no-install-recommends libexpat1 libhdf4-0-alt libjpeg62-turbo \
 && rm -rf /var/lib/apt/lists/*

COPY --from=builder /install /usr/local

# **회귀 방지 — geo 스택 import 가 성립하지 않으면 빌드가 실패한다.** 근거는 viz-render 와 같다.
# ⭑ 2단계 빌드에서는 이 검사가 **실행 이미지**를 본다 — 빌드 단계에서 통과해도 공유 라이브러리를
#   실행 이미지에 안 옮겼으면 여기서 죽는다. 그것이 이 자리를 옮기지 않은 이유다.
RUN python -c "import rasterio, rasterio._env, netCDF4, h5py, pyproj, pyhdf.SD; print('geo import OK', rasterio.__gdal_version__)"

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
