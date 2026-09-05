#!/usr/bin/env python3
"""프론트 정적 번들(`frontend/dist`)을 웹 버킷에 올린다 (`PLAN-SoT §9 〈342〉-㉮` · 계획서 G7).

AWS CLI 를 쓰지 않는다 — `kernel/s3.py`(자작 SigV4) 가 이미 있고 신규 런타임 의존 0 이 규율이다.
제품 패키지 밖(`ops/`)이라 배포 이미지에 실리지 않는다. 자격증명은 `kernel/aws_credentials.py` 사슬
(env → ECS → IMDS) — 운영자 키(`S3.md §1` 2)로 로컬에서 돌린다.

규칙
  · 확장자별 `Content-Type` — 모르는 확장자는 **거부**한다(`application/octet-stream` 으로 접지 않는다 —
    브라우저가 스크립트를 텍스트로 받으면 조용히 빈 화면이다).
  · 캐시 두 갈래 — `assets/*`(해시 이름) = `public, max-age=31536000, immutable` · 그 외(`index.html` 등) = `no-cache`.
  · **순서 = assets 먼저, `index.html` 마지막.** 새 index 가 먼저 보이면 아직 없는 해시 파일을 가리켜 깨진 화면이 뜬다.
  · `--dry-run` 은 계획(키·타입·캐시·순서)만 출력하고 아무것도 올리지 않는다.
사용
    .venv/bin/python ops/deploy_web.py --dist ../../frontend/dist --bucket colab-platform-web-dev [--region ap-northeast-2] [--dry-run]
"""
from __future__ import annotations

import argparse
import pathlib
import sys
from dataclasses import dataclass
from typing import Any

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

CONTENT_TYPES: dict[str, str] = {
    ".html": "text/html; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".mjs": "text/javascript; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".svg": "image/svg+xml",
    ".woff2": "font/woff2",
    ".woff": "font/woff",
    ".json": "application/json",
    ".map": "application/json",
    ".png": "image/png",
    ".ico": "image/x-icon",
    ".webp": "image/webp",
    ".txt": "text/plain; charset=utf-8",
}
IMMUTABLE = "public, max-age=31536000, immutable"
NO_CACHE = "no-cache"


@dataclass(frozen=True)
class Upload:
    key: str
    path: pathlib.Path
    content_type: str
    cache_control: str


def plan(dist: pathlib.Path) -> list[Upload]:
    """dist 를 훑어 올릴 순서로 돌려준다 — assets 먼저, `index.html` 마지막. 모르는 확장자는 거부."""
    if not (dist / "index.html").is_file():
        raise SystemExit(f"index.html 이 없다: {dist} — `npm run build` 먼저")
    items: list[Upload] = []
    unknown: list[str] = []
    for p in sorted(x for x in dist.rglob("*") if x.is_file()):
        key = p.relative_to(dist).as_posix()
        ctype = CONTENT_TYPES.get(p.suffix.lower())
        if ctype is None:
            unknown.append(key)
            continue
        cache = IMMUTABLE if key.startswith("assets/") else NO_CACHE
        items.append(Upload(key=key, path=p, content_type=ctype, cache_control=cache))
    if unknown:
        raise SystemExit("확장자를 모르는 파일이 있다 — CONTENT_TYPES 에 더하고 다시: " + ", ".join(unknown))
    items.sort(key=lambda u: (0 if u.key.startswith("assets/") else 1, 1 if u.key == "index.html" else 0, u.key))
    return items


def sync(items: list[Upload], client: Any) -> int:
    """계획 순서대로 `put_object`. 돌려주는 것은 올린 바이트 수."""
    total = 0
    for u in items:
        payload = u.path.read_bytes()
        client.put_object(u.key, payload, u.content_type, cache_control=u.cache_control)
        total += len(payload)
    return total


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dist", required=True, help="빌드 산출물 디렉터리 (frontend/dist)")
    ap.add_argument("--bucket", required=True, help="웹 버킷 이름")
    ap.add_argument("--region", default="ap-northeast-2")
    ap.add_argument("--dry-run", action="store_true", help="계획만 출력")
    a = ap.parse_args(argv)
    items = plan(pathlib.Path(a.dist))
    for u in items:
        print(f"  {u.key:<60} {u.content_type:<32} {u.cache_control}")
    if a.dry_run:
        print(f"(dry-run) {len(items)} 파일 — 올리지 않았다")
        return 0
    from colab_core.kernel.s3 import S3Client  # noqa: E402

    client = S3Client(bucket=a.bucket, region=a.region)
    total = sync(items, client)
    print(f"올렸다: {len(items)} 파일 · {total} B → s3://{a.bucket} (index.html 마지막)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
