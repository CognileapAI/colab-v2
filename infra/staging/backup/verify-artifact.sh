#!/usr/bin/env bash
# 백업 산출물 검사 — fail-closed.
#
# 이 스크립트의 존재 이유: 2026-07-11~08-17 동안 20바이트 빈 gzip 이 8주 내내
# "성공" 으로 기록됐다 (dev-package/DEPLOY-CURRENT.md §8). 그때의 가드는
# 파일 크기와 `gzip -t` 만 봤다. 여기서는 **내용이 쓸모 있는가**를 본다.
#
# 사용: verify-artifact.sh <파일.sql.gz> [--skip-age]
# 종료코드: 0 = 전 항목 통과 / 1 = 하나라도 실패
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$HERE/lib.sh"
load_config

FILE="${1:-}"
SKIP_AGE=0
[ "${2:-}" = "--skip-age" ] && SKIP_AGE=1
[ -n "$FILE" ] || { echo "사용: verify-artifact.sh <파일.sql.gz> [--skip-age]" >&2; exit 2; }

FAILED=0
echo "검사 대상: $(basename "$FILE")"

# C1 존재 · 최소 크기 (빈 gzip 은 20바이트다 — 1KiB 를 밑돌면 즉시 red)
if [ ! -f "$FILE" ]; then
  fail "C1 파일 존재 — 없음"
  echo "결과: RED (실패 1건)"; exit 1
fi
SIZE=$(wc -c < "$FILE" | tr -d ' ')
if [ "$SIZE" -ge 1024 ]; then pass "C1 파일 존재·크기 ${SIZE}B"; else fail "C1 크기 ${SIZE}B < 1024B (빈 gzip 은 20B 다)"; fi

# C2 gzip 무결성 (잘린 파일을 여기서 잡는다)
if gzip -t "$FILE" 2>/dev/null; then pass "C2 gzip 무결성"; else fail "C2 gzip 무결성 — 손상·절단"; fi

# C3~C5 압축 해제 내용 검사 — 한 번의 스트림으로 센다
STATS=$(gunzip -c "$FILE" 2>/dev/null | awk '
  BEGIN{bytes=0;tab=0;copy=0;rows=0;incopy=0}
  {bytes+=length($0)+1}
  /^CREATE TABLE/{tab++}
  incopy==1 && /^\\\.$/{incopy=0; next}
  incopy==1{rows++; next}
  /^COPY .* FROM stdin;/{copy++; incopy=1}
  /^INSERT INTO /{rows++}
  END{print bytes, tab, copy, rows}')
BYTES=$(echo "$STATS" | awk '{print $1}')
TABLES=$(echo "$STATS" | awk '{print $2}')
COPIES=$(echo "$STATS" | awk '{print $3}')
ROWS=$(echo "$STATS" | awk '{print $4}')
BYTES=${BYTES:-0}; TABLES=${TABLES:-0}; COPIES=${COPIES:-0}; ROWS=${ROWS:-0}

if [ "$BYTES" -gt 0 ]; then pass "C3 해제 후 ${BYTES}B"; else fail "C3 해제 결과 0바이트 — 이것이 8주 사건의 실물이다"; fi
if [ "$TABLES" -ge "$COLAB_BACKUP_MIN_TABLES" ]; then pass "C4 CREATE TABLE ${TABLES}개 (>= $COLAB_BACKUP_MIN_TABLES)"; else fail "C4 CREATE TABLE ${TABLES}개 < $COLAB_BACKUP_MIN_TABLES — 스키마가 없거나 덤프가 중간에 끊겼다"; fi
if [ "$ROWS" -ge "$COLAB_BACKUP_MIN_ROWS" ]; then pass "C5 데이터 행 ${ROWS}건 (COPY 블록 ${COPIES}개)"; else fail "C5 데이터 행 ${ROWS}건 < $COLAB_BACKUP_MIN_ROWS — 테이블만 있고 내용이 없다"; fi

# C6 신선도 — 오래된 파일은 "오늘 백업이 돌았다" 의 증거가 아니다.
#     이전 성공본이 그대로 남아 있는 상황을 성공으로 오독하지 않기 위한 검사다.
if [ "$SKIP_AGE" -eq 1 ]; then
  echo "  SKIP  C6 신선도 (--skip-age)"
else
  NOW=$(date +%s); MT=$(date -r "$FILE" +%s 2>/dev/null || echo 0)
  AGE_MIN=$(( (NOW - MT) / 60 ))
  if [ "$AGE_MIN" -le "$COLAB_BACKUP_MAX_AGE_MIN" ]; then pass "C6 신선도 ${AGE_MIN}분 (<= $COLAB_BACKUP_MAX_AGE_MIN)"; else fail "C6 신선도 ${AGE_MIN}분 > $COLAB_BACKUP_MAX_AGE_MIN — 오래된 잔존 파일이다"; fi
fi

if [ "$FAILED" -eq 0 ]; then echo "결과: GREEN"; exit 0; else echo "결과: RED (실패 ${FAILED}건)"; exit 1; fi
