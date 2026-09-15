#!/usr/bin/env bash
# Query the builder that buildx will actually use, including native and remote builders.
build_require_platform() {
  local target="$1" info platform
  info="$(docker buildx inspect --bootstrap 2>/dev/null)" || {
    echo '::gate-readiness-failure::gate=build-platform|detail=선택한 buildx builder를 준비하지 못했다' >&2
    return 78
  }
  for platform in $(printf '%s\n' "$info" | sed -n 's/^Platforms:[[:space:]]*//p' | tr ',*' '  '); do
    # buildx reports the base ARM64 target as arm64/v8 on some builders.
    [ "$platform" != linux/arm64/v8 ] || platform=linux/arm64
    [ "$platform" != "$target" ] || return 0
  done
  echo "::gate-readiness-failure::gate=build-platform|detail=선택한 builder가 $target 빌드를 지원하지 않는다" >&2
  return 78
}
