#!/usr/bin/env bash
# 파이프라인 fail-closed 증명 — 원장·롤백 대상·잠금·표식이 **거짓 green 을 못 내는지** 시험한다.
#
# `verify/selftest.sh` 가 판정기(헬스·본문·타깃·승인·체인)를 맡고, 이 파일은 **기억**을 맡는다 —
# 릴리스 원장이 「직전 green」을 잘못 짚으면 롤백은 옳은 스크립트로 틀린 곳에 간다.
#
# 운영 스택을 건드리지 않는다. `docker` 는 PATH 껍데기로 갈아 끼우고, 상태 디렉터리는 임시본이다.
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
FAILED=0; N=0
ck() { # $1=라벨 $2=기대 $3=실제
  N=$((N+1))
  if [ "$2" = "$3" ]; then echo "  PASS  [$1] $3"
  else echo "  FAIL  [$1] 기대 「$2」 · 실제 「$3」"; FAILED=$((FAILED+1)); fi
}

export COLAB_PIPELINE_STATE_DIR="$TMP/state"
. "$HERE/lib.sh"

# ── 이미지 실물 픽스처. `images_exist` 가 「있다」고 답할 태그를 여기서 정한다.
mkdir -p "$TMP/bin"
cat > "$TMP/bin/docker" <<'SH'
#!/usr/bin/env bash
# 껍데기. 두 모드다.
#  ⓐ 기본 — `image inspect <ref>` 만 답한다. EXISTING_TAGS 에 있는 태그만 존재로 친다.
#  ⓑ DOCKER_FAKE_STORE 가 있으면 **이미지 ID 를 가진 실물 흉내**를 낸다(`ref<TAB>id` 한 줄씩).
#     `tag` 도 답한다 — X-6 의 사후 검증(붙인 뒤 ID 대조)을 시험하려면 ID 가 필요하기 때문이다.
#     DOCKER_FAKE_TAG_FAIL 에 든 대상은 tag 가 **실패**하고,
#     DOCKER_FAKE_TAG_NOOP 에 든 대상은 tag 가 **성공을 말하지만 아무것도 바꾸지 않는다**
#     (= 「붙였다」가 참인데 「가리킨다」가 거짓인 자리. `|| true` 를 떼는 것만으로는 못 잡는다).
if [ -n "${DOCKER_FAKE_STORE:-}" ]; then
  TAB="$(printf '\t')"
  if [ "${1:-}" = image ] && [ "${2:-}" = inspect ]; then
    ref="${!#}"
    line="$(grep -m1 -- "^${ref}${TAB}" "$DOCKER_FAKE_STORE" 2>/dev/null)" || exit 1
    [ -n "$line" ] || exit 1
    printf '%s\n' "${line#*${TAB}}"; exit 0
  fi
  #  ⓒ `docker inspect -f … <컨테이너>` — 저장소의 `container/<이름>` 행이 그 컨테이너가 물고 있는
  #     이미지 참조다. `serving_release_tag` 가 「지금 서빙 중인 것」을 실물에서 읽는 자리를 시험한다.
  if [ "${1:-}" = inspect ]; then
    ref="${!#}"
    line="$(grep -m1 -- "^container/${ref}${TAB}" "$DOCKER_FAKE_STORE" 2>/dev/null)" || exit 1
    [ -n "$line" ] || exit 1
    printf '%s\n' "${line#*${TAB}}"; exit 0
  fi
  if [ "${1:-}" = tag ]; then
    src="${2:-}"; dst="${3:-}"
    case " ${DOCKER_FAKE_TAG_FAIL:-} " in *" $dst "*) echo "fake: tag 거부 $dst" >&2; exit 1 ;; esac
    case " ${DOCKER_FAKE_TAG_NOOP:-} " in *" $dst "*) exit 0 ;; esac
    sl="$(grep -m1 -- "^${src}${TAB}" "$DOCKER_FAKE_STORE" 2>/dev/null)" || exit 1
    grep -v -- "^${dst}${TAB}" "$DOCKER_FAKE_STORE" > "$DOCKER_FAKE_STORE.n" 2>/dev/null
    printf '%s%s%s\n' "$dst" "$TAB" "${sl#*${TAB}}" >> "$DOCKER_FAKE_STORE.n"
    mv "$DOCKER_FAKE_STORE.n" "$DOCKER_FAKE_STORE"; exit 0
  fi
  exit 1
fi
[ "${1:-}" = image ] || exit 1
[ "${2:-}" = inspect ] || exit 1
ref="${!#}"; tag="${ref##*:}"
case " ${EXISTING_TAGS:-} " in *" $tag "*) exit 0 ;; esac
exit 1
SH
chmod +x "$TMP/bin/docker"
export PATH="$TMP/bin:$PATH"

echo "── P1 원장이 비면 롤백 대상이 **없다** (조용히 자리표시로 떨어지지 않는다)"
export EXISTING_TAGS="aaa bbb"
if ledger_rollback_target "" >/dev/null 2>&1; then ck P1 "대상없음" "대상있음"; else ck P1 "대상없음" "대상없음"; fi

echo "── P2 green 릴리스 둘 중 **직전**(현재 제외)을 짚는다"
ledger_append deploy aaa aaa green "1차"
ledger_append deploy bbb bbb green "2차"
ck P2 "aaa" "$(ledger_rollback_target bbb)"

echo "── P3 **red 릴리스는 롤백 대상이 아니다**"
ledger_append deploy ccc ccc red "3차 실패"
export EXISTING_TAGS="aaa bbb ccc"
ck P3 "bbb" "$(ledger_rollback_target ccc)"

echo "── P4 **이미지가 없는 릴리스는 롤백 대상이 아니다** (원장 한 줄 ≠ 롤백 가능)"
export EXISTING_TAGS="aaa"
ck P4 "aaa" "$(ledger_rollback_target bbb)"

echo "── P5 원장에 있어도 이미지가 하나도 없으면 **실패한다** (0건을 성공으로 읽지 않는다)"
export EXISTING_TAGS=""
if ledger_rollback_target "" >/dev/null 2>&1; then ck P5 "실패" "성공"; else ck P5 "실패" "실패"; fi

echo "── P6 승인 행은 롤백 대상이 아니다 (종류가 deploy 여야 한다)"
export EXISTING_TAGS="zzz"
ledger_append approve zzz zzz green "승인자=Ted 본것=화면"
if [ -z "$(ledger_rollback_target "" 2>/dev/null)" ]; then ck P6 "대상없음" "대상없음"; else ck P6 "대상없음" "대상있음"; fi

echo "── P7 원장 보존 = 30건 (넘치면 오래된 것부터 잘린다)"
COLAB_LEDGER_KEEP=30
for i in $(seq 1 40); do ledger_append deploy "s$i" "s$i" green "n$i"; done
ck P7 "30" "$(wc -l < "$(ledger_path)" | tr -d ' ')"

echo "── P8 실패 표식은 **다음 성공에서만** 사라진다"
mark_failed "시험" "일부러"
ck P8 "있음" "$([ -f "$(failmark_path)" ] && echo 있음 || echo 없음)"
mark_success "s40"
ck P8b "없음" "$([ -f "$(failmark_path)" ] && echo 있음 || echo 없음)"
ck P8c "있음" "$([ -s "$(success_path)" ] && echo 있음 || echo 없음)"

echo "── P9 요약줄이 검사 대상 0건을 **green 으로 말하지 않는다**"
( FAILED=0; SKIPPED=0; CHECKED=0; verdict "0건 시험" ) >"$TMP/o" 2>&1
if grep -q "RED (검사 대상 0건" "$TMP/o"; then ck P9 "RED" "RED"; else ck P9 "RED" "$(cat "$TMP/o")"; fi

echo "── P10 롤백: 대상을 안 밝히면 **거부한다** (기본값으로 자리표시에 가지 않는다)"
N=$((N+1))
if "$HERE/../rollback.sh" >/dev/null 2>&1; then
  echo "  FAIL  [P10] 대상 없이도 롤백이 진행됐다"; FAILED=$((FAILED+1))
else echo "  PASS  [P10] 거부"; fi

echo "── P11 배포: 타깃을 안 밝히면 **거부한다**"
N=$((N+1))
if "$HERE/../deploy.sh" >/dev/null 2>&1; then
  echo "  FAIL  [P11] 타깃 없이도 배포가 진행됐다"; FAILED=$((FAILED+1))
else echo "  PASS  [P11] 거부"; fi

echo "── P12 배포: prod 타깃은 **거부한다** (승인 없이 도는 경로가 없다)"
N=$((N+1))
if "$HERE/../deploy.sh" --target prod >/dev/null 2>&1; then
  echo "  FAIL  [P12] prod 로 배포가 진행됐다"; FAILED=$((FAILED+1))
else echo "  PASS  [P12] 거부"; fi

echo "── P13 배포: 필수 설정이 비면 **빌드 전에** 멈춘다 (⑦ 까지 가지 않는다)"
# 2026-08-28 첫 staging 배포는 게이트·태그보존·빌드·백업을 다 치르고 ⑦ 에서 죽었다.
# 이제 그 판정이 ⓪-b 로 앞당겨졌는지 — **빌드 줄이 나오지 않는지** 로 확인한다.
# 픽스처 env 는 가짜 값이다. 실물 env 파일도 도커도 건드리지 않는다.
mkdir -p "$TMP/pf"; : > "$TMP/pf/dummy"
: > "$TMP/pf/no-owner.env"
while read -r k; do
  [ -n "$k" ] || continue
  [ "$k" = COLAB_OWNER_PASSWORD ] && continue
  case "$k" in
    *_FILE) printf '%s=%s\n' "$k" "$TMP/pf/dummy" ;;
    *_DIR)  printf '%s=%s\n' "$k" "$TMP/pf" ;;
    *)      printf '%s=fixture-not-a-real-secret\n' "$k" ;;
  esac >> "$TMP/pf/no-owner.env"
done < <(env -i PATH="$PATH" bash -c '. "$1"; preflight_required_keys' _ "$HERE/../preflight.sh")

COLAB_STAGING_ENV="$TMP/pf/no-owner.env" "$HERE/../deploy.sh" --target staging >"$TMP/d" 2>&1; DRC=$?
N=$((N+1))
if [ "$DRC" -eq 0 ]; then echo "  FAIL  [P13] 필수 설정이 비었는데 배포가 진행됐다"; FAILED=$((FAILED+1))
elif ! grep -q "COLAB_OWNER_PASSWORD" "$TMP/d"; then
  echo "  FAIL  [P13] 멈추긴 했으나 어느 키가 없는지 말하지 않는다"; FAILED=$((FAILED+1))
elif grep -q "이미지 빌드" "$TMP/d"; then
  echo "  FAIL  [P13] 빌드까지 간 뒤에 멈췄다 — 프리플라이트가 늦다"; FAILED=$((FAILED+1))
else echo "  PASS  [P13] 빌드 전에 거부 · 빠진 키 이름을 말한다"; fi
N=$((N+1))
if grep -q "fixture-not-a-real-secret" "$TMP/d"; then
  echo "  FAIL  [P13b] 배포 출력에 설정 값이 섞였다"; FAILED=$((FAILED+1))
else echo "  PASS  [P13b] 출력에 값이 없다"; fi


# ══ X-6 별칭 재부착 — 「실패를 삼키고 다음 줄에서 GREEN 을 찍는」 모양이 없는지 ═══════
# 종전 `deploy.sh` ⑫ 는 `docker tag … 2>/dev/null || true` 였다. 아래 넷은 그 무조건 성공
# 경로가 실제로 사라졌는지를 **실패 픽스처로** 못 박는다.
store_seed() { # $1=릴리스 태그 → 6종의 :$1 을 새 ID 로, :i2 를 **옛 ID** 로 심는다
  : > "$TMP/images"
  for n in "${RELEASE_IMAGES[@]}"; do
    printf 'colab-v2/%s:%s\tsha256:new%s000000000000\n' "$n" "$1" "$n" >> "$TMP/images"
    printf 'colab-v2/%s:i2\tsha256:old%s000000000000\n'  "$n" "$n" >> "$TMP/images"
  done
}
alias_points_to() { # $1=서비스 $2=태그 → :i2 가 :$2 와 같은 ID 인가
  local a b TAB; TAB="$(printf '\t')"
  a="$(grep -m1 -- "^colab-v2/$1:i2${TAB}" "$TMP/images" | cut -f2)"
  b="$(grep -m1 -- "^colab-v2/$1:$2${TAB}" "$TMP/images" | cut -f2)"
  [ -n "$a" ] && [ "$a" = "$b" ]
}
export DOCKER_FAKE_STORE="$TMP/images"

echo "── P14 별칭 재부착이 **정상**이면 green 이고 :i2 가 새 이미지를 가리킨다 (양성)"
store_seed r1; unset DOCKER_FAKE_TAG_FAIL DOCKER_FAKE_TAG_NOOP
if alias_reattach r1 >/dev/null 2>&1; then ck P14 "GREEN" "GREEN"; else ck P14 "GREEN" "RED"; fi
ck P14b "가리킨다" "$(alias_points_to core-api r1 && echo 가리킨다 || echo 옛것)"

echo "── P15 docker tag 가 **실패**하면 판정이 red 다 (무조건 성공 경로가 없다)"
store_seed r2; unset DOCKER_FAKE_TAG_NOOP
export DOCKER_FAKE_TAG_FAIL="colab-v2/viz-render:i2"
if alias_reattach r2 >/dev/null 2>&1; then ck P15 "RED" "GREEN"; else ck P15 "RED" "RED"; fi
ck P15b "옛것" "$(alias_points_to viz-render r2 && echo 가리킨다 || echo 옛것)"

echo "── P16 tag 가 **성공을 말했는데 안 붙은** 경우도 red 다 (붙였다 ≠ 가리킨다 · 사후 검증)"
# || true 만 떼면 이 자리는 여전히 green 이 난다. 종료코드가 0 이기 때문이다.
store_seed r3; unset DOCKER_FAKE_TAG_FAIL
export DOCKER_FAKE_TAG_NOOP="colab-v2/ai-service:i2"
if alias_reattach r3 >/dev/null 2>&1; then ck P16 "RED" "GREEN"; else ck P16 "RED" "RED"; fi

echo "── P17 **원본이 없으면** red 다 (정상 부재는 대상 :i2 쪽이지 원본 쪽이 아니다)"
store_seed r4; unset DOCKER_FAKE_TAG_FAIL DOCKER_FAKE_TAG_NOOP
grep -v -- "^colab-v2/frontend:r4$(printf '\t')" "$TMP/images" > "$TMP/i.n"; mv "$TMP/i.n" "$TMP/images"
if alias_reattach r4 >/dev/null 2>&1; then ck P17 "RED" "GREEN"; else ck P17 "RED" "RED"; fi

echo "── P18 **첫 배포**(:i2 가 아직 없음)는 정상이다 — 부재를 실패로 읽지 않는다"
: > "$TMP/images"
for n in "${RELEASE_IMAGES[@]}"; do printf 'colab-v2/%s:r5\tsha256:new%s000000000000\n' "$n" "$n" >> "$TMP/images"; done
if alias_reattach r5 >/dev/null 2>&1; then ck P18 "GREEN" "GREEN"; else ck P18 "GREEN" "RED"; fi

echo "── P19 릴리스 태그를 **안 밝히면** 거부한다 (기본값으로 아무 이미지나 가리키지 않는다)"
if alias_reattach "" >/dev/null 2>&1; then ck P19 "RED" "GREEN"; else ck P19 "RED" "RED"; fi

echo "── P20 deploy.sh ⑫ 에 **무조건 성공 경로가 없다** (docker tag … || true 소멸)"
N=$((N+1))
# 주석은 뺀다 — 이 파일은 그 옛 모양을 **주석으로 인용**하고 있다(무엇을 고쳤는지 남기려고).
if grep -vE '^[[:space:]]*#' "$HERE/../deploy.sh" | grep -q 'docker tag .*|| *true'; then
  echo "  FAIL  [P20] deploy.sh 에 docker tag … || true 가 남아 있다"; FAILED=$((FAILED+1))
elif ! grep -q 'alias_reattach "$TAG"' "$HERE/../deploy.sh"; then
  echo "  FAIL  [P20] deploy.sh 가 alias_reattach 를 부르지 않는다"; FAILED=$((FAILED+1))
else echo "  PASS  [P20] 무조건 성공 경로 없음 · 판정 함수 호출 확인"; fi


# ══ X-6 형제② 별칭 신선도 — 「리허설이 무엇을 리허설하는지 재지 않는」 모양이 없는지 ═══
# 복원 리허설(`compose.throwaway.yml`)은 6종을 전부 `:i2` 로 띄운다. 그 이름이 **언제 것인지**
# 묻지 않으면 옛 이미지를 리허설하고 통과를 낸다. 아래는 그 대조가 실물로 도는지를 못 박는다.
serve_as() { # $1=서빙 태그 → 살아 있는 core-api 가 그 태그를 물고 있다고 심는다
  local TAB; TAB="$(printf '\t')"
  grep -v -- "^container/colab_v2_staging_core_api${TAB}" "$TMP/images" > "$TMP/i.n" 2>/dev/null
  printf 'container/colab_v2_staging_core_api%scolab-v2/core-api:%s\n' "$TAB" "$1" >> "$TMP/i.n"
  mv "$TMP/i.n" "$TMP/images"
}

echo "── P21 서빙 태그를 **실물(컨테이너가 문 이미지)** 에서 읽는다 (원장 마지막 줄이 아니다)"
store_seed s1; serve_as s1
ck P21 "s1" "$(serving_release_tag)"

echo "── P22 :i2 가 서빙 태그와 **같은 이미지**면 신선도 green (양성 대조군)"
unset DOCKER_FAKE_TAG_FAIL DOCKER_FAKE_TAG_NOOP
alias_reattach s1 >/dev/null 2>&1
if alias_fresh "$(serving_release_tag)" >/dev/null 2>&1; then ck P22 "GREEN" "GREEN"; else ck P22 "GREEN" "RED"; fi

echo "── P23 :i2 가 **옛 이미지**를 가리키면 red 다 (재부착이 빠진 배포·롤백 뒤의 상태)"
store_seed s2; serve_as s2   # :i2 는 old… 인 채로 둔다(재부착 안 함)
if alias_fresh "$(serving_release_tag)" >/dev/null 2>&1; then ck P23 "RED" "GREEN"; else ck P23 "RED" "RED"; fi

echo "── P24 :i2 가 **아예 없으면** red 다 (쓰는 자리의 부재는 정상 부재가 아니다)"
store_seed s3; serve_as s3
grep -v -- ":i2$(printf '\t')" "$TMP/images" > "$TMP/i.n"; mv "$TMP/i.n" "$TMP/images"
if alias_fresh "$(serving_release_tag)" >/dev/null 2>&1; then ck P24 "RED" "GREEN"; else ck P24 "RED" "RED"; fi

echo "── P25 서빙 컨테이너를 못 읽으면 **태그를 지어내지 않는다** (기본값으로 떨어지지 않는다)"
store_seed s4   # container/ 행 없음
if serving_release_tag >/dev/null 2>&1; then ck P25 "실패" "성공"; else ck P25 "실패" "실패"; fi
echo "── P25b 서빙이 **별칭**(:i2)을 물고 있으면 그것도 「모른다」다 — 별칭은 신원이 아니다"
serve_as i2
if serving_release_tag >/dev/null 2>&1; then ck P25b "실패" "성공"; else ck P25b "실패" "실패"; fi

echo "── P26 rollback.sh 가 되돌린 뒤 :i2 를 **재부착하고**, 그 판정이 원장 green 보다 **앞**이다"
N=$((N+1))
RB="$HERE/../rollback.sh"
RBSRC="$(grep -vE '^[[:space:]]*#' "$RB")"
LA="$(printf '%s\n' "$RBSRC" | grep -n 'alias_reattach "\$TAG"' | head -1 | cut -d: -f1)"
LG="$(printf '%s\n' "$RBSRC" | grep -n 'ledger_append rollback .*green "직전 green' | head -1 | cut -d: -f1)"
if [ -z "$LA" ]; then
  echo "  FAIL  [P26] rollback.sh 가 alias_reattach 를 부르지 않는다 — 되돌린 뒤 :i2 가 걷어낸 이미지를 가리킨다"; FAILED=$((FAILED+1))
elif [ -z "$LG" ]; then
  echo "  FAIL  [P26] rollback.sh 의 원장 green 줄을 찾지 못했다 — 순서를 판정할 수 없다"; FAILED=$((FAILED+1))
elif [ "$LA" -ge "$LG" ]; then
  echo "  FAIL  [P26] 재부착 판정이 원장 green 뒤에 있다 — green 을 적어 놓고 죽는 모양이다"; FAILED=$((FAILED+1))
else echo "  PASS  [P26] 재부착 호출 있음 · 원장 green 보다 앞($LA < $LG)"; fi

echo "── P27 리허설(throwaway-stack.sh)이 :i2 신선도를 **잰다** (안 재고 띄우지 않는다)"
N=$((N+1))
TW="$HERE/../restore/throwaway-stack.sh"
TWSRC="$(grep -vE '^[[:space:]]*#' "$TW")"
if ! printf '%s\n' "$TWSRC" | grep -q 'alias_fresh'; then
  echo "  FAIL  [P27] throwaway-stack.sh 가 alias_fresh 를 부르지 않는다 — 옛 이미지를 리허설할 수 있다"; FAILED=$((FAILED+1))
elif ! printf '%s\n' "$TWSRC" | grep -q 'serving_release_tag'; then
  echo "  FAIL  [P27] 서빙 태그를 실물에서 읽지 않는다 — 무엇과 대조하는지가 없다"; FAILED=$((FAILED+1))
elif ! printf '%s\n' "$TWSRC" | grep -q 'skip_ack .*신선도'; then
  echo "  FAIL  [P27] 명시 면제 경로에 건수가 남지 않는다 — 승인된 SKIP 이 아니다"; FAILED=$((FAILED+1))
else
  # 신선도 판정이 compose up **보다 앞**이어야 한다. 뒤면 이미 옛 것을 띄운 뒤다.
  LF="$(printf '%s\n' "$TWSRC" | grep -n 'step_zero_fresh || exit 1' | head -1 | cut -d: -f1)"
  LU="$(printf '%s\n' "$TWSRC" | grep -n 'compose -p "\$PROJ" -f "\$CF" up -d' | head -1 | cut -d: -f1)"
  if [ -n "$LF" ] && [ -n "$LU" ] && [ "$LF" -lt "$LU" ]; then
    echo "  PASS  [P27] 신선도 대조 있음 · 기동보다 앞($LF < $LU) · 면제는 건수를 남긴다"
  else echo "  FAIL  [P27] 신선도 판정이 기동보다 앞이 아니다 (${LF:-없음} / ${LU:-없음})"; FAILED=$((FAILED+1)); fi
fi

echo "── P28 서빙 태그 대조 — 실제로 그 태그가 서빙 중이면 green (양성 대조군)"
store_seed t1; serve_as t1
if serving_tag_is t1 >/dev/null 2>&1; then ck P28 "GREEN" "GREEN"; else ck P28 "GREEN" "RED"; fi

echo "── P29 **옛 태그가 서빙 중인데 되돌렸다고 말하면** red 다 (헬스는 이것을 묻지 않는다)"
if serving_tag_is t2 >/dev/null 2>&1; then ck P29 "RED" "GREEN"; else ck P29 "RED" "RED"; fi

echo "── P30 서빙을 못 읽으면 red 다 (모르는 것을 일치로 읽지 않는다)"
store_seed t3   # container/ 행 없음
if serving_tag_is t3 >/dev/null 2>&1; then ck P30 "RED" "GREEN"; else ck P30 "RED" "RED"; fi

echo "── P31 rollback.sh 가 서빙 태그를 대조한다 · 그 판정이 원장 green 보다 앞이다"
N=$((N+1))
LS_="$(printf '%s\n' "$RBSRC" | grep -n 'serving_tag_is "\$TAG"' | head -1 | cut -d: -f1)"
if [ -z "$LS_" ]; then
  echo "  FAIL  [P31] rollback.sh 가 serving_tag_is 를 부르지 않는다 — 옛 이미지로 살아 있어도 GREEN 이 난다"; FAILED=$((FAILED+1))
elif [ -n "$LG" ] && [ "$LS_" -ge "$LG" ]; then
  echo "  FAIL  [P31] 서빙 태그 대조가 원장 green 뒤에 있다"; FAILED=$((FAILED+1))
else echo "  PASS  [P31] 서빙 태그 대조 있음 · 원장 green 보다 앞($LS_ < $LG)"; fi


# ══ 스케줄 실행 껍데기 — 「아무것도 안 하고 성공을 보고하는」 모양이 없는지 ═══════════
# 이 자리가 이 레포 대표 실패형(green-by-skip)의 가장 나쁜 모양이다. 크론이 5분마다 부르는데
# 그 회차가 **아무것도 하지 않았을 때**를 「성공」으로 적으면 두 가지가 동시에 무너진다.
#   ⓐ `LAST-SUCCESS.txt` 는 「파이프라인이 아예 안 돈 경우」를 잡는 표식인데(watch.sh ③),
#      안 돈 회차가 그 표식을 갱신하면 **그 표식은 영원히 아무것도 못 잡는다.**
#   ⓑ `DEPLOY-FAILED.txt` 는 「**다음 성공에서만** 사라진다」가 계약인데(lib.sh mark_failed),
#      안 돈 회차가 지우면 **진짜 배포 실패가 5분 뒤 조용히 사라진다.**
# 그래서 「할 일 없음」과 「배포 green」은 **다른 종료코드**여야 하고 껍데기가 그것을 갈라야 한다.
# 실물 `watch.sh` 를 그대로 시험한다 — 사본 옆에 가짜 `run-pipeline.sh` 를 두고 부른다.
WT="$TMP/wt"; mkdir -p "$WT"
cp "$HERE/watch.sh" "$HERE/lib.sh" "$WT/"
watch_case() { # $1=가짜 run-pipeline 종료코드 → 상태 디렉터리를 새로 깔고 watch.sh 를 한 번 돌린다
  printf '#!/usr/bin/env bash\nexit %s\n' "$1" > "$WT/run-pipeline.sh"; chmod +x "$WT/run-pipeline.sh"
  rm -rf "$TMP/wstate"; mkdir -p "$TMP/wstate"
  COLAB_PIPELINE_STATE_DIR="$TMP/wstate" "$WT/watch.sh" >/dev/null 2>&1
  WRC=$?
}
wmark()  { [ -f "$TMP/wstate/$FAILED_MARK" ] && echo 있음 || echo 없음; }
wsucc()  { [ -s "$TMP/wstate/$LAST_SUCCESS" ] && echo 있음 || echo 없음; }

echo "── P32 배포가 **실제로 돌아 green** 이면 성공 표식이 갱신된다 (양성 대조군)"
watch_case 0
ck P32 "있음" "$(wsucc)"

echo "── P33 **할 일 없음**(새 커밋 없음)은 성공이 아니다 — LAST-SUCCESS 를 갱신하지 않는다"
# 갱신하면 「크론은 도는데 배포는 8주째 안 됐다」를 잡을 표식이 사라진다.
watch_case 66
ck P33 "없음" "$(wsucc)"

echo "── P34 **할 일 없음이 직전 실패 표식을 건드리지 않는다** — 지우지도 덮어쓰지도 않는다"
# 지우면 진짜 실패가 5분 뒤 사라지고, 덮어쓰면 **무엇이 실패했는지**가 사라진다. 둘 다 안 된다.
printf '#!/usr/bin/env bash\nexit 66\n' > "$WT/run-pipeline.sh"; chmod +x "$WT/run-pipeline.sh"
rm -rf "$TMP/wstate"; mkdir -p "$TMP/wstate"
( COLAB_PIPELINE_STATE_DIR="$TMP/wstate"; . "$WT/lib.sh"; mark_failed "마이그레이션" "원래사유" ) >/dev/null 2>&1
COLAB_PIPELINE_STATE_DIR="$TMP/wstate" "$WT/watch.sh" >/dev/null 2>&1
ck P34 "있음" "$(wmark)"
ck P34b "원래사유보존" "$(grep -q '원래사유' "$TMP/wstate/$FAILED_MARK" 2>/dev/null && echo 원래사유보존 || echo 덮였다)"

echo "── P34c 할 일 없음은 **실패도 아니다** — 없던 표식을 새로 만들지 않는다"
watch_case 66
ck P34c "없음" "$(wmark)"

echo "── P35 겹침·fetch 실패(75)는 고장이 아니다 — 표식을 만들지 않는다"
watch_case 75
ck P35 "없음" "$(wmark)"

echo "── P36 진짜 실패는 표식을 만든다 (양성 대조군)"
watch_case 65
ck P36 "있음" "$(wmark)"

echo "── P37 run-pipeline.sh 의 **「새 커밋 없음」 갈래가 exit 0 이 아니다**"
N=$((N+1))
NOOP="$(grep -vE '^[[:space:]]*#' "$HERE/run-pipeline.sh" | grep -A2 '새 커밋 없음' | grep -oE 'exit [0-9]+' | head -1)"
if [ -z "$NOOP" ]; then
  echo "  FAIL  [P37] 「새 커밋 없음」 갈래의 exit 를 찾지 못했다 — 판정할 수 없다"; FAILED=$((FAILED+1))
elif [ "$NOOP" = "exit 0" ]; then
  echo "  FAIL  [P37] 아무것도 안 한 회차가 exit 0 을 낸다 — 부르는 쪽이 배포 성공과 못 가른다"; FAILED=$((FAILED+1))
else echo "  PASS  [P37] 할 일 없음 = $NOOP (배포 green 과 다른 코드)"; fi

echo "── P38 install-schedule.sh 가 설치 뒤 **읽어서 확인**한다 (「설치했다」≠「걸려 있다」)"
N=$((N+1))
ISSRC="$(grep -vE '^[[:space:]]*#' "$HERE/install-schedule.sh")"
if ! printf '%s\n' "$ISSRC" | grep -q 'verify_installed'; then
  echo "  FAIL  [P38] 설치 후 재확인 경로가 없다 — crontab - 의 종료코드만 보고 있다"; FAILED=$((FAILED+1))
else echo "  PASS  [P38] 설치 후 재확인 있음"; fi

echo "── P39 install-schedule.sh 가 **기존 crontab 을 통째로 날리지 않는다**"
# `crontab -l 2>/dev/null` 은 「크론탭이 없다」와 「crontab 명령이 실패했다」를 같은 빈 출력으로 만든다.
# 그 빈 출력을 그대로 `crontab -` 에 넣으면 **백업 블록까지 사라진 채** 「설치됨」이 찍힌다.
N=$((N+1))
if ! printf '%s\n' "$ISSRC" | grep -q 'PRE_N'; then
  echo "  FAIL  [P39] 설치 전 줄 수를 세지 않는다 — 통째로 날아가도 알 수 없다"; FAILED=$((FAILED+1))
else echo "  PASS  [P39] 설치 전후 줄 수 대조 있음"; fi

unset DOCKER_FAKE_STORE DOCKER_FAKE_TAG_FAIL DOCKER_FAKE_TAG_NOOP
export EXISTING_TAGS="aaa"

echo
echo "── 판정기 selftest 도 이어서 돈다"
"$HERE/../verify/selftest.sh" || FAILED=$((FAILED+1))

echo
if [ "$FAILED" -ne 0 ]; then echo "pipeline selftest: RED (실패 ${FAILED}건 / ${N}건 + 판정기)"; exit 1; fi
echo "pipeline selftest: GREEN (${N}건 + 판정기 전건 기대대로)"
