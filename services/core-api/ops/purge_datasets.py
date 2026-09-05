#!/usr/bin/env python3
"""데이터셋 행을 **목록으로 못 박아** 지운다 — 일회성 운영 도구 (`PLAN-SoT §9 〈360〉`).

⛔ **제품 기능이 아니다.** `deleteDataset` 은 `NOT_IMPLEMENTED_P1` 이고 이 스크립트가 그것을
여는 것도 아니다. **바이트가 이미 없어진 데이터셋의 원장 행**(＝ 제품이 표현할 수 없는 상태)을
운영자가 치우는 자리이고, 그 사유·승인자·대상 목록은 `§9` 행에 남는다. 제품 패키지 밖(`ops/`)이라
배포 이미지에 실리지 않는다.

**왜 스크립트인가** — 앱에 삭제 경로가 없고(P1 범위) 삭제 시 계보 처리 정책(`〈195〉`·`〈202〉`)이
미구현이다. 5행을 위해 제품 표면을 여는 것은 `CLAUDE.md §5` 「범위 늘리기」다.

## 반드시 알아야 하는 것 넷

1. ⭑ **소유자 롤은 RLS 를 우회하지 않는다.** `ops/app-role.sql` = `colab_owner … NOBYPASSRLS` 이고
   테넌트 표는 전부 **FORCE ROW LEVEL SECURITY** 다. 경계를 안 걸면 `DELETE` 가 **0행에 조용히
   성공**한다 — `〈358〉` 이 읽기에서 당한 함정의 쓰기판이다. 그래서 트랜잭션 안에서
   `set_config('app.current_lab', <lab>, true)` 를 **먼저** 건다(`kernel/scope.GUC_LAB` 과 같은 이름).
2. ⭑ **순서가 있다.** `d3_dataset(id)` 로 가는 진짜 FK 다섯(`d3_dataset_description`·
   `d3_dataset_autometa`·`d3_file`·`d4_lineage_edge` child/parent·`d4_lineage_unknown`)에 **CASCADE 가
   없다.** 게다가 `d3_file` DELETE 는 statement 트리거 `sync_dataset_file_count` 를 깨우고 그것이
   `d3_dataset.file_count` 를 갱신하므로 **`d3_file` 을 `d3_dataset` 보다 먼저** 지워야 한다.
3. ⛔ **손대지 않는 표** — `d8_activity`·`d8_download` 는 `deny_update_delete` 트리거가 DELETE 를
   예외로 막는다(감사 기록이다). FK 가 아니라 bare 컬럼이라 남겨도 무결성이 깨지지 않는다.
   `d5_upload*` 은 `dataset_id` 자체가 없다 — 무접촉.
4. ⭑ **0행 삭제를 성공으로 세지 않는다.** dry-run 이 센 표별 행수와 실집행 `rowcount` 가 **정확히
   일치**하고 `d3_dataset` 삭제가 **인자 개수와 같을 때만** COMMIT 한다. 하나라도 어긋나면 ROLLBACK.

## 쓰는 법 (EC2 위 · `docs/DEPLOY.md §6-1` 의 격리 실행과 같은 모양)

    docker run --rm --network host --user 0 \\
      -v /etc/colab/platform-owner-db.url:/s/owner.url:ro \\
      -v <이 파일>:/tmp/purge.py:ro \\
      colab-v2/core-api:dev python /tmp/purge.py \\
        --db-url-file /s/owner.url --lab <LAB_ID> --id <ULID> [--id ...]      # dry-run
      ... 같은 명령 ＋ --yes-delete                                            # 실집행

⚠ 접속 문자열은 **파일 경로로만** 받는다. 값은 argv·로그·예외 어디에도 싣지 않는다.
"""
from __future__ import annotations

import argparse
import pathlib
import re
import sys

#: 지우는 순서. **`d3_dataset` 이 마지막이다** (위 2번).
#: `(표, WHERE 절, 설명)` — WHERE 는 `%(ids)s` 하나만 바인딩한다.
DELETE_PLAN: list[tuple[str, str, str]] = [
    ("d3_file", "dataset_id = any(%(ids)s)", "조각 — 먼저 지운다(file_count 트리거)"),
    ("d3_dataset_description", "dataset_id = any(%(ids)s)", "사람이 적은 정보"),
    ("d3_dataset_autometa", "dataset_id = any(%(ids)s)", "자동 판독값"),
    ("d4_lineage_edge",
     "child_dataset_id = any(%(ids)s) or parent_dataset_id = any(%(ids)s)",
     "계보 간선 — 자식·부모 양쪽"),
    ("d4_lineage_unknown", "dataset_id = any(%(ids)s)", "계보 미상 표기"),
    ("d2_dataset_access", "dataset_id = any(%(ids)s)", "공개 범위"),
    ("d2_dataset_access_grant", "dataset_id = any(%(ids)s)", "개별 허용"),
    ("d2_dataset_access_request", "dataset_id = any(%(ids)s)", "접근 요청"),
    ("d2_verification_request", "dataset_id = any(%(ids)s)", "승인 요청"),
    ("d2_verified", "dataset_id = any(%(ids)s)", "승인 기록"),
    ("d6_project_dataset", "dataset_id = any(%(ids)s)", "프로젝트 묶음"),
    ("d3_dataset", "id = any(%(ids)s)", "대장 — 마지막"),
]

#: ⛔ 절대 건드리지 않는 표. 이름을 코드에 적어 두는 것이 규율이다.
NEVER_TOUCH = ("d8_activity", "d8_download", "d5_upload", "d5_upload_file",
               "d5_upload_transfer", "d5_upload_transfer_file")

ULID = re.compile(r"^[0-9A-HJKMNP-TV-Z]{26}$")


def _check_plan_disjoint_from_never_touch() -> None:
    """계획표가 금지 표를 건드리지 않음을 **기동 때** 증명한다 (시험이 이 함수를 부른다)."""
    planned = {t for t, _, _ in DELETE_PLAN}
    bad = planned & set(NEVER_TOUCH)
    if bad:
        raise SystemExit(f"삭제 계획에 금지 표가 들어 있다: {sorted(bad)}")


def _counts(cur, ids: list[str]) -> dict[str, int]:
    out: dict[str, int] = {}
    for table, where, _desc in DELETE_PLAN:
        cur.execute(f"select count(*) from {table} where {where}", {"ids": ids})
        out[table] = cur.fetchone()[0]
    return out


def main(argv: list[str] | None = None) -> int:
    _check_plan_disjoint_from_never_touch()
    ap = argparse.ArgumentParser(description="데이터셋 행을 목록으로 지운다 (일회성 운영 도구)")
    ap.add_argument("--db-url-file", required=True,
                    help="소유자 롤 접속 URL 파일(0600). 값은 argv 에 싣지 않는다.")
    ap.add_argument("--lab", required=True, help="연구실 id — RLS 경계. 없으면 0행이 지워진다.")
    ap.add_argument("--id", action="append", dest="ids", required=True,
                    help="지울 데이터셋 id. 여러 번 준다. ⛔ 조건문이 아니라 목록이다.")
    ap.add_argument("--yes-delete", action="store_true",
                    help="이것이 없으면 dry-run 이다 — 세기만 하고 지우지 않는다.")
    a = ap.parse_args(argv)

    for value, what in [(a.lab, "--lab")] + [(i, "--id") for i in a.ids]:
        if not ULID.match(value):
            print(f"{what} 값이 ULID 26자가 아니다: {value!r}", file=sys.stderr)
            return 2
    if len(set(a.ids)) != len(a.ids):
        print("--id 에 중복이 있다 — 목록을 다시 만든다.", file=sys.stderr)
        return 2

    import psycopg  # 컨테이너 안에만 있다 — 모듈 상단에 두면 시험이 못 읽는다.

    url = pathlib.Path(a.db_url_file).read_text(encoding="utf-8").strip()
    if not url:
        print("접속 URL 파일이 비어 있다.", file=sys.stderr)
        return 2
    url = url.replace("postgresql+psycopg", "postgresql")

    ids = list(a.ids)
    mode = "실집행" if a.yes_delete else "dry-run"
    print(f"── purge_datasets — {mode} · 대상 {len(ids)}건 · 연구실 {a.lab}")
    for i in ids:
        print(f"   · {i}")

    with psycopg.connect(url, connect_timeout=15, autocommit=False) as conn:
        with conn.cursor() as cur:
            # ⭑ 경계를 **먼저** 건다. 이것이 없으면 아래 전부가 0행이다.
            cur.execute("select set_config('app.current_lab', %s, true)", (a.lab,))

            planned = _counts(cur, ids)
            print("\n── 표별 예정 행수 (경계가 걸린 상태에서 센 값)")
            width = max(len(t) for t, _, _ in DELETE_PLAN)
            for table, _where, desc in DELETE_PLAN:
                print(f"   {table:<{width}}  {planned[table]:>5}   {desc}")
            print(f"   {'계':<{width}}  {sum(planned.values()):>5}")

            if planned["d3_dataset"] == 0 or planned["d3_file"] == 0:
                print("\n⛔ `d3_dataset` 또는 `d3_file` 이 0 이다 — **경계 미설정 또는 잘못된 id** 로 본다. "
                      "중단한다(0행 삭제를 성공으로 세지 않는다).", file=sys.stderr)
                conn.rollback()
                return 3
            if planned["d3_dataset"] != len(ids):
                print(f"\n⛔ `d3_dataset` 이 {planned['d3_dataset']} 건인데 인자는 {len(ids)} 건이다 "
                      "— 목록과 실물이 어긋난다. 중단한다.", file=sys.stderr)
                conn.rollback()
                return 3

            if not a.yes_delete:
                print("\n── dry-run 이다. 아무것도 지우지 않았다. 지우려면 `--yes-delete` 를 준다.")
                conn.rollback()
                return 0

            print("\n── 삭제 (단일 트랜잭션)")
            actual: dict[str, int] = {}
            for table, where, _desc in DELETE_PLAN:
                cur.execute(f"delete from {table} where {where}", {"ids": ids})
                actual[table] = cur.rowcount
                print(f"   {table:<{width}}  {cur.rowcount:>5}")

            mismatch = {t: (planned[t], actual[t]) for t, _, _ in DELETE_PLAN
                        if planned[t] != actual[t]}
            if mismatch:
                print(f"\n⛔ 예정과 실측이 다르다 {mismatch} — **ROLLBACK**.", file=sys.stderr)
                conn.rollback()
                return 4
            if actual["d3_dataset"] != len(ids):
                print(f"\n⛔ `d3_dataset` 삭제가 {actual['d3_dataset']} 건이다 (기대 {len(ids)}) "
                      "— **ROLLBACK**.", file=sys.stderr)
                conn.rollback()
                return 4

            conn.commit()
            print(f"\n── COMMIT. 데이터셋 {actual['d3_dataset']} 건 · 행 합계 {sum(actual.values())} 건.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
