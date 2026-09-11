#!/usr/bin/env python3
"""I4 정적 집행 — trace 배선, 알람 정책, 데이터 레지던시를 대조한다."""
from __future__ import annotations

import argparse
import re
import sys
import tomllib
from pathlib import Path


REQUIRED_SYSTEMS = {"s3-data", "rds-platform", "cloudfront", "openai"}
REQUIRED_TARGETS = {"deploy-verification", "service-health", "backup-freshness"}


def _load(path: Path) -> dict:
    try:
        with path.open("rb") as stream:
            return tomllib.load(stream)
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise ValueError(f"{path}를 읽을 수 없다: {exc}") from exc


def check(args) -> list[str]:
    errors: list[str] = []
    residency = _load(args.residency)
    alarms = _load(args.alarms)
    compose = args.compose.read_text(encoding="utf-8")

    home = residency.get("home_region")
    if home != "ap-northeast-2":
        errors.append(f"home_region은 ap-northeast-2여야 한다: {home!r}")
    systems = {item.get("id"): item for item in residency.get("systems", [])
               if isinstance(item, dict)}
    missing = REQUIRED_SYSTEMS - set(systems)
    if missing:
        errors.append(f"레지던시 시스템 누락: {sorted(missing)}")
    regions = re.findall(r"COLAB_(?:CORE|WORKER|VIZ)_S3_REGION:\s*([^\s#]+)", compose)
    if len(regions) < 3 or any(region != home for region in regions):
        errors.append(f"dev compose S3 region이 home과 다르다: {regions}")
    for name in ("s3-data", "rds-platform"):
        item = systems.get(name, {})
        if item.get("processing_location") != home or item.get("korea_guaranteed") is not True:
            errors.append(f"{name} 국내 리전 선언이 맞지 않는다")
    cloudfront = systems.get("cloudfront", {})
    if (cloudfront.get("processing_location") != "global-edge"
            or cloudfront.get("origin_region") != home
            or cloudfront.get("korea_guaranteed") is not False):
        errors.append("CloudFront global edge/서울 origin 선언이 맞지 않는다")
    openai = systems.get("openai", {})
    if (openai.get("processing_location") != "provider-managed"
            or openai.get("korea_guaranteed") is not False):
        errors.append("OpenAI 처리 위치를 국내 고정으로 주장하면 안 된다")
    sent = set(openai.get("data_sent", []))
    excluded = set(openai.get("data_excluded", []))
    if not {"search_query_text", "uploaded_file_metadata_for_lineage_suggestion"} <= sent:
        errors.append("OpenAI 전송 데이터 범위가 빠졌다")
    if not {"source_file_bytes", "database_credentials", "aws_credentials", "session_tokens"} <= excluded:
        errors.append("OpenAI 비전송 민감 데이터 범위가 빠졌다")

    if alarms.get("interval_seconds") != 300:
        errors.append("알람 probe 주기는 정확히 300초여야 한다")
    threshold = alarms.get("failure_threshold")
    if not isinstance(threshold, int) or isinstance(threshold, bool) or not 1 <= threshold <= 100:
        errors.append("failure_threshold는 1~100 정수여야 한다")
    if alarms.get("notification") != "https_webhook_file":
        errors.append("알림 목적지는 레포 밖 HTTPS webhook 파일이어야 한다")
    if set(alarms.get("targets", [])) != REQUIRED_TARGETS:
        errors.append("알람 대상은 deploy/service-health/backup 셋이어야 한다")

    source = args.repo / "services/core-api/src/colab_core/kernel/observability.py"
    copies = [
        args.repo / "services/ai-service/src/colab_ai/kernel/observability.py",
        args.repo / "services/pipeline-worker/src/colab_pipeline/kernel/observability.py",
        args.repo / "services/viz-render/src/colab_viz/kernel/observability.py",
    ]
    try:
        canonical = source.read_bytes()
        if not canonical:
            errors.append("관측 커널 정본이 비었다")
        for path in copies:
            if path.read_bytes() != canonical:
                errors.append(f"관측 커널 복제본 drift: {path}")
    except OSError as exc:
        errors.append(f"관측 커널을 읽을 수 없다: {exc}")
    required_text = {
        "services/core-api/src/colab_core/app/main.py": "TraceMiddleware",
        "services/viz-render/src/colab_viz/app/main.py": "TraceMiddleware",
        "services/ai-service/src/colab_ai/app/main.py": "TraceMiddleware",
        "services/core-api/src/colab_core/app/relay.py": "current_traceparent",
        "services/pipeline-worker/src/colab_pipeline/app/worker.py": "structured_worker_summary",
    }
    for relative, needle in required_text.items():
        try:
            body = (args.repo / relative).read_text(encoding="utf-8")
        except OSError:
            errors.append(f"관측 배선 파일 부재: {relative}")
        else:
            if needle not in body:
                errors.append(f"관측 배선 누락: {relative} → {needle}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--residency", type=Path, required=True)
    parser.add_argument("--alarms", type=Path, required=True)
    parser.add_argument("--compose", type=Path, required=True)
    parser.add_argument("--repo", type=Path, required=True)
    args = parser.parse_args()
    try:
        errors = check(args)
    except ValueError as exc:
        errors = [str(exc)]
    if errors:
        for error in errors:
            print(f"::error::ops-observability red — {error}")
        return 1
    print("ops-observability green — trace 배선 5자리 · 국내 리전 3자리 · 외부 처리 2자리 · 알람 대상 3건")
    return 0


if __name__ == "__main__":
    sys.exit(main())
