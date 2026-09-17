#!/usr/bin/env bash
# Doctor repository snapshot. This is separate from the executable ops source bundle.
repo_bundle_build() { # repository, short SHA, full SHA, output directory
  local repo="$1" sha="$2" full_sha="$3" dist="$4" p stage
  local paths=(db gates services/core-api/ops infra contracts) missing=()
  for p in "${paths[@]}"; do [ -e "$repo/$p" ] || missing+=("$p"); done
  if [ "${#missing[@]}" -gt 0 ]; then
    echo "레포 tar 대상이 없다: ${missing[*]} — 판정 레포가 불완전해진다" >&2
    return 2
  fi
  REPO_TGZ="$dist/colab-repo-$sha.tgz"
  REPO_MANIFEST="$dist/colab-repo-$sha.manifest"
  mkdir -p "$dist"
  git -C "$repo" archive --format=tar "$full_sha" "${paths[@]}" | gzip -n > "$REPO_TGZ"
  stage="$(mktemp -d)"
  (
    trap 'rm -rf "$stage"' EXIT
    tar xzf "$REPO_TGZ" -C "$stage"
    {
      echo "# source_sha=$sha"; echo "# source_full_sha=$full_sha"
      (cd "$stage" && find . -type f -print0 | sort -z | xargs -0 sha256sum)
    } > "$REPO_MANIFEST"
    chmod 0600 "$REPO_MANIFEST"
  )
}

repo_bundle_remote_snippet() { # full SHA, archive basename, manifest basename
  local full_sha="$1" archive="$2" manifest="$3"
  printf '%s' "sudo mkdir -p /opt/colab-repo-releases/$full_sha && \
  sudo tar xzf /opt/colab-v2/images/$archive -C /opt/colab-repo-releases/$full_sha --overwrite && \
  sudo install -m 0600 /opt/colab-v2/images/$manifest /opt/colab-repo-releases/$full_sha/OPS_SOURCE_MANIFEST"
}
