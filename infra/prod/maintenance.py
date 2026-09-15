#!/usr/bin/env python3
"""CloudFront 운영 점검 진입·상태·해제 경계."""

from __future__ import annotations

import argparse
import copy
import fcntl
import hashlib
import json
import os
import pathlib
import stat
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from collections.abc import Callable
from typing import Any


SCHEMA = "colab-product-maintenance/1"
REQUIRED_PATTERNS = {"/api/*", "/previews/*"}
_LOCK_FDS: list[int] = []


class ReadinessError(RuntimeError):
    """필수 입력 또는 검증 경로가 없어 변경을 시작할 수 없다."""


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


_NO_REDIRECT_OPENER = urllib.request.build_opener(_NoRedirect)


def _open_no_redirect(request, timeout: float):
    return _NO_REDIRECT_OPENER.open(request, timeout=timeout)


def _digest(value: dict[str, Any]) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def _write_state(path: pathlib.Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(value, stream, ensure_ascii=False, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        directory_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _load_json(path: pathlib.Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ReadinessError(f"JSON을 읽을 수 없다: {path}") from exc
    if not isinstance(value, dict):
        raise ReadinessError(f"JSON 객체가 아니다: {path}")
    return value


def _load_config(path: pathlib.Path) -> dict[str, Any]:
    value = _load_json(path)
    for key in ("distribution_id", "maintenance_function_arn", "maintenance_function_name", "state_file", "private_seed"):
        if not value.get(key):
            raise ReadinessError(f"설정에 {key}가 필요하다")
    private = value["private_seed"]
    if not isinstance(private, dict):
        raise ReadinessError("private_seed는 객체여야 한다")
    for key in ("url", "header_name", "header_file", "public_origin_probe_url"):
        if not private.get(key):
            raise ReadinessError(f"private_seed.{key}가 필요하다")
    return value


def _default_run_aws(args: list[str], input_json: dict[str, Any] | None = None) -> dict[str, Any]:
    temporary: str | None = None
    command = list(args)
    try:
        if input_json is not None:
            fd, temporary = tempfile.mkstemp(prefix="colab-cloudfront-", suffix=".json")
            with os.fdopen(fd, "w", encoding="utf-8") as stream:
                json.dump(input_json, stream, ensure_ascii=False)
            option = "--event-object" if command[1:3] == ["cloudfront", "test-function"] else "--distribution-config"
            prefix = "fileb://" if option == "--event-object" else "file://"
            command.extend((option, f"{prefix}{temporary}"))
        valid_fds = []
        for lock_fd in _LOCK_FDS:
            try:
                os.fstat(lock_fd)
            except OSError:
                continue
            valid_fds.append(lock_fd)
        done = subprocess.run(command, text=True, capture_output=True, check=False, pass_fds=tuple(valid_fds))
        if done.returncode:
            raise RuntimeError(f"AWS 명령 실패({done.returncode}): {done.stderr.strip()[:240]}")
        return json.loads(done.stdout) if done.stdout.strip() else {}
    finally:
        if temporary is not None:
            os.unlink(temporary)


def _probe_private_access(config: dict[str, Any], open_url: Callable[..., Any]) -> None:
    private = config["private_seed"]
    if not private["url"].startswith("https://") or not private["public_origin_probe_url"].startswith("https://"):
        raise ReadinessError("private_seed 검증 URL은 모두 https여야 한다")
    header_path = pathlib.Path(private["header_file"])
    try:
        mode = stat.S_IMODE(header_path.stat().st_mode)
        secret = header_path.read_text(encoding="utf-8").strip()
    except OSError as exc:
        raise ReadinessError("private_seed.header_file을 읽을 수 없다") from exc
    if mode != 0o600 or not secret:
        raise ReadinessError("private_seed.header_file은 비어 있지 않은 0600 파일이어야 한다")
    request = urllib.request.Request(private["url"], headers={private["header_name"]: secret})
    try:
        with open_url(request, timeout=10) as response:
            if response.geturl() != request.full_url:
                raise ReadinessError("비공개 seed redirect를 허용하지 않는다")
            if not 200 <= response.status < 300:
                raise ReadinessError(f"비공개 seed 경로 상태가 {response.status}다")
    except urllib.error.HTTPError as exc:
        if 300 <= exc.code < 400:
            raise ReadinessError("비공개 seed redirect를 허용하지 않는다") from exc
        raise ReadinessError(f"비공개 seed 경로 상태가 {exc.code}다") from exc
    except urllib.error.URLError as exc:
        raise ReadinessError("비공개 seed 경로를 검증하지 못했다") from exc

    public_request = urllib.request.Request(private["public_origin_probe_url"])
    try:
        with open_url(public_request, timeout=10) as response:
            if response.geturl() != public_request.full_url:
                raise ReadinessError("공개 origin probe redirect를 허용하지 않는다")
            public_status = response.status
    except urllib.error.HTTPError as exc:
        public_status = exc.code
    except urllib.error.URLError as exc:
        raise ReadinessError("공개 origin 차단을 검증하지 못했다") from exc
    if public_status not in (401, 403, 404):
        raise ReadinessError(f"공개 origin이 차단되지 않았다(status={public_status})")


def _behavior_set(distribution: dict[str, Any]) -> list[dict[str, Any]]:
    default = distribution.get("DefaultCacheBehavior")
    cache = distribution.get("CacheBehaviors")
    if not isinstance(default, dict) or not isinstance(cache, dict):
        raise ReadinessError("CloudFront 기본/캐시 동작 구성을 읽을 수 없다")
    items = cache.get("Items") or []
    if not isinstance(items, list):
        raise ReadinessError("CloudFront CacheBehaviors.Items가 목록이 아니다")
    if len(items) != 2:
        raise ReadinessError("예상하지 않은 CloudFront cache behavior가 있어 공개 우회를 판정할 수 없다")
    by_pattern = {item.get("PathPattern"): item for item in items if isinstance(item, dict)}
    if set(by_pattern).intersection(REQUIRED_PATTERNS) != REQUIRED_PATTERNS:
        raise ReadinessError("CloudFront /api/* 및 /previews/* 동작이 모두 필요하다")
    if sum(1 for item in items if item.get("PathPattern") in REQUIRED_PATTERNS) != 2:
        raise ReadinessError("CloudFront 필수 동작이 중복됐다")
    return [default, by_pattern["/api/*"], by_pattern["/previews/*"]]


def _maintenance_config(original: dict[str, Any], function_arn: str) -> dict[str, Any]:
    changed = copy.deepcopy(original)
    for behavior in _behavior_set(changed):
        associations = behavior.get("FunctionAssociations") or {"Quantity": 0}
        items = [item for item in associations.get("Items", []) if item.get("EventType") != "viewer-request"]
        items.append({"EventType": "viewer-request", "FunctionARN": function_arn})
        behavior["FunctionAssociations"] = {"Quantity": len(items), "Items": items}
    return changed


def _verify_maintenance_function(config: dict[str, Any], run_aws: Callable[..., dict[str, Any]]) -> None:
    name = config["maintenance_function_name"]
    described = run_aws(["aws", "cloudfront", "describe-function", "--name", name, "--stage", "LIVE"])
    summary = described.get("FunctionSummary") or {}
    metadata = summary.get("FunctionMetadata") or {}
    etag = described.get("ETag")
    if (metadata.get("FunctionARN") != config["maintenance_function_arn"] or
            metadata.get("Stage") != "LIVE" or not isinstance(etag, str)):
        raise ReadinessError("점검 함수의 LIVE ARN 또는 ETag가 설정과 일치하지 않는다")
    for uri in ("/", "/api/healthz", "/previews/probe"):
        event = {"version": "1.0", "context": {"eventType": "viewer-request"}, "viewer": {"ip": "192.0.2.1"},
                 "request": {"method": "GET", "uri": uri, "querystring": {}, "headers": {}, "cookies": {}}}
        tested = run_aws(["aws", "cloudfront", "test-function", "--name", name, "--if-match", etag,
                          "--stage", "LIVE"], event)
        result = tested.get("TestResult") or {}
        if result.get("FunctionErrorMessage"):
            raise ReadinessError(f"점검 함수 LIVE 시험이 {uri}에서 오류를 반환했다")
        try:
            output = json.loads(result["FunctionOutput"])
            status = int(output["response"]["statusCode"])
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise ReadinessError(f"점검 함수 LIVE 시험 출력을 {uri}에서 판독하지 못했다") from exc
        if status != 503:
            raise ReadinessError(f"점검 함수 LIVE 시험이 {uri}에서 503 대신 {status}를 반환했다")


def _get_distribution(config: dict[str, Any], run_aws: Callable[..., dict[str, Any]]) -> tuple[str, dict[str, Any]]:
    result = run_aws(["aws", "cloudfront", "get-distribution-config", "--id", config["distribution_id"]])
    etag, distribution = result.get("ETag"), result.get("DistributionConfig")
    if not isinstance(etag, str) or not isinstance(distribution, dict):
        raise ReadinessError("CloudFront 구성 또는 ETag를 읽지 못했다")
    return etag, distribution


def _require_deployed(config: dict[str, Any], run_aws: Callable[..., dict[str, Any]]) -> None:
    result = run_aws(["aws", "cloudfront", "get-distribution", "--id", config["distribution_id"]])
    distribution = result.get("Distribution") or {}
    if distribution.get("Id") != config["distribution_id"] or distribution.get("Status") != "Deployed":
        raise ReadinessError("CloudFront distribution이 Deployed 상태가 아니다")


def _update_and_verify(config: dict[str, Any], expected: dict[str, Any], etag: str,
                       run_aws: Callable[..., dict[str, Any]]) -> str:
    run_aws(["aws", "cloudfront", "update-distribution", "--id", config["distribution_id"], "--if-match", etag], expected)
    run_aws(["aws", "cloudfront", "wait", "distribution-deployed", "--id", config["distribution_id"]])
    _require_deployed(config, run_aws)
    current_etag, current = _get_distribution(config, run_aws)
    if _digest(current) != _digest(expected):
        raise RuntimeError("CloudFront 배포 뒤 읽기 검증이 일치하지 않는다")
    return current_etag


def _verify_active(config: dict[str, Any], state: dict[str, Any], run_aws, open_url) -> dict[str, Any]:
    if state.get("state") != "active":
        raise ReadinessError("active 점검 상태가 아니다")
    if state.get("distribution_id") != config["distribution_id"]:
        raise ReadinessError("상태의 distribution_id가 현재 설정과 다르다")
    _probe_private_access(config, open_url)
    _verify_maintenance_function(config, run_aws)
    _require_deployed(config, run_aws)
    etag, current = _get_distribution(config, run_aws)
    if etag != state.get("maintenance_etag") or _digest(current) != state.get("maintenance_digest"):
        raise RuntimeError("현재 CloudFront 점검 구성이 기록과 다르다")
    return state


def _resume_to_active(config: dict[str, Any], state: dict[str, Any], state_path: pathlib.Path,
                      run_aws, open_url) -> dict[str, Any]:
    _probe_private_access(config, open_url)
    _verify_maintenance_function(config, run_aws)
    _require_deployed(config, run_aws)
    current_etag, current = _get_distribution(config, run_aws)
    original = state.get("original_distribution_config")
    if not isinstance(original, dict) or _digest(original) != state.get("original_digest"):
        raise RuntimeError("보존한 원설정이 손상됐다")
    maintenance = _maintenance_config(original, config["maintenance_function_arn"])
    if _digest(maintenance) != state.get("maintenance_digest"):
        raise RuntimeError("점검 함수 또는 보존 기록이 달라졌다")
    current_digest = _digest(current)
    if current_digest == state["maintenance_digest"]:
        state.update(state="active", maintenance_etag=current_etag)
        _write_state(state_path, state)
        return state
    if current_digest != state["original_digest"]:
        raise RuntimeError("중단 뒤 CloudFront 구성이 원설정·점검설정 어느 쪽도 아니다")
    new_etag = _update_and_verify(config, maintenance, current_etag, run_aws)
    state.update(state="active", maintenance_etag=new_etag)
    _write_state(state_path, state)
    return state


def _recover_after_leave_failure(config: dict[str, Any], state: dict[str, Any], state_path: pathlib.Path,
                                 run_aws, open_url, cause: Exception) -> None:
    try:
        _resume_to_active(config, state, state_path, run_aws, open_url)
    except Exception as recovery_error:
        unknown = dict(state, state="unknown", error="leave와 점검 복구가 모두 실패했다")
        try:
            _write_state(state_path, unknown)
        except Exception:
            pass
        raise RuntimeError("해제 실패 뒤 실제 CloudFront 상태를 확인하지 못했다") from recovery_error
    raise RuntimeError("해제 실패 후 점검 상태로 복구했다") from cause


def execute(action: str, config_path: pathlib.Path, *, resume: bool = False, run_aws=_default_run_aws,
            open_url=_open_no_redirect) -> dict[str, Any]:
    config = _load_config(pathlib.Path(config_path))
    state_path = pathlib.Path(config["state_file"])
    lock_path = pathlib.Path(f"{state_path}.lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a+", encoding="utf-8") as lock:
        os.chmod(lock_path, 0o600)
        fcntl.flock(lock, fcntl.LOCK_EX)
        lock_fds = [lock.fileno()]
        for env_name in ("COLAB_PRODUCT_RESEED_LOCK_FD", "COLAB_DEPLOY_LOCK_FD", "COLAB_PRODUCT_RELEASE_LOCK_FD"):
            controller_fd = os.environ.get(env_name)
            if not controller_fd:
                continue
            try:
                parsed_fd = int(controller_fd)
                os.fstat(parsed_fd)
            except (ValueError, OSError) as exc:
                raise ReadinessError(f"{env_name}가 열린 fd가 아니다") from exc
            lock_fds.append(parsed_fd)
        _LOCK_FDS[:] = lock_fds
        state = _load_json(state_path) if state_path.exists() else None
        if state is not None and state.get("distribution_id") not in (None, config["distribution_id"]):
            raise ReadinessError("상태의 distribution_id가 현재 설정과 다르다")
        if action == "status":
            if state is None or state.get("state") != "active":
                raise ReadinessError("active 점검 상태가 아니다")
            return _verify_active(config, state, run_aws, open_url)
        if action == "enter":
            if state is not None and state.get("state") == "active":
                return _verify_active(config, state, run_aws, open_url)
            if state is not None and state.get("state") in ("entering", "restoring"):
                if not resume:
                    raise ReadinessError(f"{state.get('state')} 상태 재개에는 사람의 --resume 선언이 필요하다")
                return _resume_to_active(config, state, state_path, run_aws, open_url)
            if state is not None and state.get("state") not in ("restored",):
                raise ReadinessError(f"기존 점검 상태가 {state.get('state')}다 — 사람이 기록을 확인해야 한다")
            _probe_private_access(config, open_url)
            _verify_maintenance_function(config, run_aws)
            etag, original = _get_distribution(config, run_aws)
            maintenance = _maintenance_config(original, config["maintenance_function_arn"])
            state = {
                "schema": SCHEMA,
                "state": "entering",
                "distribution_id": config["distribution_id"],
                "maintenance_function_arn": config["maintenance_function_arn"],
                "original_etag": etag,
                "original_distribution_config": original,
                "original_digest": _digest(original),
                "maintenance_digest": _digest(maintenance),
            }
            _write_state(state_path, state)
            current_etag = _update_and_verify(config, maintenance, etag, run_aws)
            state.update(state="active", maintenance_etag=current_etag)
            _write_state(state_path, state)
            return state
        if action == "leave":
            if state is None or state.get("state") != "active":
                raise ReadinessError("active 점검 기록이 있어야 해제할 수 있다")
            current_etag, current = _get_distribution(config, run_aws)
            if current_etag != state.get("maintenance_etag") or _digest(current) != state.get("maintenance_digest"):
                raise RuntimeError("점검 중 CloudFront 구성이 바뀌었다 — 해제를 중단한다")
            original = state.get("original_distribution_config")
            if not isinstance(original, dict) or _digest(original) != state.get("original_digest"):
                raise RuntimeError("보존한 원설정이 손상됐다 — 해제를 중단한다")
            state.update(state="restoring", restoring_from_etag=current_etag)
            _write_state(state_path, state)
            try:
                restored_etag = _update_and_verify(config, original, current_etag, run_aws)
                state.update(state="restored", restored_etag=restored_etag)
                _write_state(state_path, state)
                return state
            except Exception as exc:
                _recover_after_leave_failure(config, state, state_path, run_aws, open_url, exc)
        raise ValueError(action)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="product CloudFront 점검 상태 관리")
    parser.add_argument("--action", required=True, choices=("enter", "status", "leave"))
    parser.add_argument("--config", required=True, type=pathlib.Path)
    parser.add_argument("--resume", action="store_true", help="사람이 확인한 entering 상태만 명시적으로 재개")
    args = parser.parse_args(argv)
    try:
        result = execute(args.action, args.config, resume=args.resume)
    except ReadinessError as exc:
        print(f"::gate-readiness-failure:: {exc}", file=sys.stderr)
        return 78
    except (RuntimeError, OSError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(json.dumps({key: value for key, value in result.items() if key not in ("original_distribution_config",)},
                     ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
