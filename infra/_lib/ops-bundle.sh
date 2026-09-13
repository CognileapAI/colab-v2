#!/usr/bin/env bash
# 운영 소스 번들 사슬 — dev·prod 가 **같은 한 벌**을 부른다 (`〈395〉` · WU-D2 후속).
#
# 왜 여기 있나 — 종전에 이 사슬은 `infra/dev/ship.sh` **안에만** 있었고 prod 에는 아예 없었다.
# 복사해 두면 한쪽만 고쳐져 갈린다(경로·모드·검증기 이름). `infra/_lib/ship-gate.sh` 와 같은 이유다.
#
# 사슬이 하는 것 넷 —
#   ⑴ 배포 sha 의 운영 probe 소스를 묶고 hash manifest 를 만든다(`infra/ops/build-source-bundle.sh`).
#   ⑵ 원격에서 **manifest 의 archive_sha256 과 실제 tar 를 대조**한다(전송 중 바뀌면 여기서 멈춘다).
#   ⑶ 같은 sha 가 이미 있으면 `verify-reimport.sh`, 없으면 풀고 `verify-source.sh`.
#   ⑷ `dispatch-current.sh`·`verify-source.sh` 를 `/opt/colab-ops/bin` 에 root 0755 로 심는다.
#
# 부르는 쪽 = `infra/dev/ship.sh` · `infra/prod/ship.sh`.
# 시험 = `infra/dev/tests/ship-gate.sh` · `infra/prod/tests/ship-gate.sh`.

# ── ops_bundle_build <저장소> <후보 sha> <dist> ───────────────────────────────
#: 두 값을 채운다 — OPS_BUNDLE_TAR · OPS_BUNDLE_MANIFEST.
#: ⚠ 번들의 내용은 **커밋 트리**다. 워크트리의 미추적 파일은 들어가지 않는다 —
#:   `/opt/colab-repo` 로 가는 레포 tar 와 역할이 다르다(그쪽은 실제 파일 트리다).
ops_bundle_build() {
  local repo="$1" sha="$2" dist="$3"
  "$repo/infra/ops/build-source-bundle.sh" --repo "$repo" --sha "$sha" --output "$dist"
  OPS_BUNDLE_TAR="$dist/colab-ops-source-$sha.tar.gz"
  OPS_BUNDLE_MANIFEST="$dist/colab-ops-source-$sha.manifest"
}

# ── ops_bundle_prepare_cmd ───────────────────────────────────────────────────
#: 원격 디렉터리 준비 한 줄(stdout). `/opt/colab-v2` 는 로그인 사용자, `/opt/colab-ops` 는 root.
ops_bundle_prepare_cmd() {
  printf '%s' 'sudo mkdir -p /opt/colab-v2/images /opt/colab-ops/bin /opt/colab-ops/versions && sudo chown $(id -u):$(id -g) /opt/colab-v2 /opt/colab-v2/images && sudo chown -R root:root /opt/colab-ops && sudo chmod 0755 /opt/colab-ops /opt/colab-ops/bin /opt/colab-ops/versions'
}

# ── ops_bundle_remote_snippet <sha> <tar 파일명> <manifest 파일명> ────────────
#: 원격 `&&` 사슬(stdout). 부르는 쪽이 `docker load … && <이것> && …` 로 잇는다.
#: 끝에 `&&` 를 붙이지 않는다 — 이음새는 부르는 쪽이 정한다.
ops_bundle_remote_snippet() {
  local sha="$1" tar_base="$2" man_base="$3"
  printf '%s' "test \"\$(sha256sum /opt/colab-v2/images/$tar_base | cut -d' ' -f1)\" = \
       \"\$(sed -n 's/^# archive_sha256=//p' /opt/colab-v2/images/$man_base)\" && \
  if sudo test -e /opt/colab-ops/versions/$sha; then \
    sudo /opt/colab-ops/versions/$sha/infra/ops/verify-reimport.sh \
      --source /opt/colab-ops/versions/$sha \
      --incoming-manifest /opt/colab-v2/images/$man_base --current-sha $sha; \
  else \
    sudo mkdir /opt/colab-ops/versions/$sha && \
    sudo tar xzf /opt/colab-v2/images/$tar_base -C /opt/colab-ops/versions/$sha && \
    sudo cp /opt/colab-v2/images/$man_base /opt/colab-ops/versions/$sha/OPS_SOURCE_MANIFEST && \
    sudo chown -R root:root /opt/colab-ops/versions/$sha && \
    sudo chmod 0600 /opt/colab-ops/versions/$sha/OPS_SOURCE_MANIFEST && \
    sudo /opt/colab-ops/versions/$sha/infra/ops/verify-source.sh \
      --source /opt/colab-ops/versions/$sha \
      --manifest /opt/colab-ops/versions/$sha/OPS_SOURCE_MANIFEST --current-sha $sha; \
  fi && \
  sudo install -o root -g root -m 0755 /opt/colab-ops/versions/$sha/infra/ops/dispatch-current.sh /opt/colab-ops/bin/dispatch-current.sh && \
  sudo install -o root -g root -m 0755 /opt/colab-ops/versions/$sha/infra/ops/verify-source.sh /opt/colab-ops/bin/verify-source.sh"
}
