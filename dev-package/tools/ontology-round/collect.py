"""온톨로지 회차 1단계 — 자료 목록 수집(읽기 전용).

지난 회차 이후 올라온 자료의 이름·설명·등록 칸·파일 확장자·검색 근거 상태를 JSON 으로 모은다.
DB 에는 아무것도 쓰지 않는다. 트랜잭션은 읽기 전용이다.

  # dev (운영자 환경 래퍼 · SSH · 백업 롤 — 자격 값은 출력하지 않는다)
  python3 collect.py --source dev --out <회차 폴더>/datasets.json [--since 2026-09-26T00:00:00+00:00]
  # 로컬·일회용 DB
  python3 collect.py --database-url postgresql://… --out datasets.json

종료코드: 0 성공 · 1 판정 실패(응답이 JSON 배열이 아님) · 78 준비 실패(자격·도구 부재).
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import pathlib
import shutil
import subprocess
import sys

# 백업 롤(colab_backup)은 BYPASSRLS 다. 경계 없는 앱 롤로 세면 행이 있어도 0 으로 보인다(.agents/rules/deploy.md 10번).
SQL_BODY = r"""
SELECT coalesce(json_agg(x ORDER BY x->>'uploadedAt'), '[]'::json) FROM (
  SELECT json_build_object(
    'id', d.id::text, 'labId', d.lab_id::text, 'name', dd.name, 'summary', dd.summary,
    'topic', dd.topic, 'category', dd.category, 'dataType', dd.data_type,
    'observationInterval', CASE WHEN dd.observation_interval_value IS NULL THEN NULL
        ELSE json_build_object('value', dd.observation_interval_value, 'unit', dd.observation_interval_unit) END,
    'gridDescription', dd.human_grid_description,
    'sourceLabel', d.source_label, 'sourceUrl', d.source_url,
    'uploadedAt', d.uploaded_at, 'fileCount', d.file_count,
    'fileExtensions', (SELECT json_object_agg(ext, n) FROM (
        SELECT lower(coalesce(substring(f.file_name from '\.([A-Za-z0-9]+)$'), '')) AS ext, count(*) AS n
        FROM d3_file f WHERE f.dataset_id = d.id GROUP BY 1) e),
    'evidence', (SELECT json_build_object(
        'rows', count(*), 'reviewed', count(*) FILTER (WHERE e.status = 'reviewed'),
        'keys', (SELECT json_agg(DISTINCT k ORDER BY k) FROM d3_search_evidence e2,
                 jsonb_object_keys(e2.facts) k WHERE e2.dataset_id = d.id))
      FROM d3_search_evidence e WHERE e.dataset_id = d.id)
  ) AS x
  FROM d3_dataset d JOIN d3_dataset_description dd ON dd.dataset_id = d.id
  WHERE d.deleted_at IS NULL
) s;
"""
SQL = "SET row_security = off;\nSET default_transaction_read_only = on;\n" + SQL_BODY

REMOTE = r"""set -euo pipefail
sql="$(mktemp)"; trap 'rm -f "$sql"' EXIT
cat > "$sql" <<'SQL'
__SQL__
SQL
chmod 644 "$sql"
sudo test -f /etc/colab/backup-platform-db.url
sudo docker run --rm --network host --user 0 \
  -v /etc/colab/backup-platform-db.url:/s/c.url:ro -v "$sql":/s/q.sql:ro postgres:16-alpine \
  sh -c 'psql -X -q -v ON_ERROR_STOP=1 -tA "$(sed -E "s#^postgresql\+psycopg://#postgresql://#" /s/c.url)" -f /s/q.sql'
"""


def _ready_fail(msg: str) -> "NoReturn":  # noqa: F821
    print("준비 실패: " + msg, file=sys.stderr)
    raise SystemExit(78)


def fetch_dev() -> str:
    wrapper = pathlib.Path(os.environ.get(
        "COLAB_DEV_ENV_WRAPPER", pathlib.Path.home() / ".config/colab-platform/with-dev-env.sh"))
    if not wrapper.is_file():
        _ready_fail(f"운영자 환경 래퍼가 없다 — {wrapper} (dev-package/tools/ontology-round/README.md 「설정」)")
    ssh = ('exec ssh -i "$COLAB_DEV_KEY_FILE" -o IdentitiesOnly=yes -o BatchMode=yes '
           '-o ConnectTimeout=20 "$COLAB_DEV_SSH" "bash -s"')
    r = subprocess.run([str(wrapper), "bash", "-c", ssh],
                       input=REMOTE.replace("__SQL__", SQL).encode(), capture_output=True)
    if r.returncode != 0:
        _ready_fail("dev 조회가 실패했다\n" + r.stderr.decode(errors="replace")[-800:])
    return r.stdout.decode()


def fetch_url(url: str) -> str:
    url = url.replace("postgresql+psycopg://", "postgresql://")
    if shutil.which("psql"):
        r = subprocess.run(["psql", "-X", "-q", "-v", "ON_ERROR_STOP=1", "-tA", url, "-c", SQL],
                           capture_output=True)
        if r.returncode != 0:
            _ready_fail("psql 조회 실패\n" + r.stderr.decode(errors="replace")[-800:])
        return r.stdout.decode()
    try:
        import psycopg  # core-api venv 에 있다
    except ImportError:
        _ready_fail("psql 도 psycopg 도 없다 — services/core-api/.venv/bin/python 으로 실행한다")
    with psycopg.connect(url) as c:
        c.execute("SET row_security = off")
        c.execute("SET default_transaction_read_only = on")
        return json.dumps(c.execute(SQL_BODY).fetchone()[0])


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--source", choices=["dev"])
    src.add_argument("--database-url")
    ap.add_argument("--since", help="이 시각(ISO 8601) 뒤에 올라온 자료만 — 지난 회차 state.json 의 collectedAt")
    ap.add_argument("--out", type=pathlib.Path, required=True)
    a = ap.parse_args(argv)
    raw = fetch_dev() if a.source == "dev" else fetch_url(a.database_url)
    line = next((x for x in reversed(raw.strip().splitlines()) if x.startswith("[")), None)
    if line is None:
        print("판정 실패: JSON 배열 응답이 없다", file=sys.stderr)
        return 1
    rows = json.loads(line)
    total = len(rows)
    if a.since:
        rows = [r for r in rows if (r.get("uploadedAt") or "") > a.since]
    out = {"schema": "colab-ontology-round-collect/1", "source": a.source or "database-url",
           "collectedAt": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
           "since": a.since, "totalLive": total, "datasets": rows}
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"datasets": len(rows), "totalLive": total, "since": a.since, "out": str(a.out)},
                     ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
