from __future__ import annotations

import copy
import importlib.util
import json
import pathlib
import stat
import os
import sys

import pytest


MODULE_PATH = pathlib.Path(__file__).parents[1] / "maintenance.py"


def load_module():
    spec = importlib.util.spec_from_file_location("product_maintenance", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def association(arn: str) -> dict:
    return {"EventType": "viewer-request", "FunctionARN": arn}


def distribution_config(spa_arn: str) -> dict:
    base = {
        "CallerReference": "original-reference",
        "Enabled": True,
        "DefaultCacheBehavior": {
            "TargetOriginId": "web",
            "FunctionAssociations": {"Quantity": 1, "Items": [association(spa_arn)]},
        },
        "CacheBehaviors": {
            "Quantity": 2,
            "Items": [
                {"PathPattern": "/api/*", "TargetOriginId": "api", "FunctionAssociations": {"Quantity": 0}},
                {"PathPattern": "/previews/*", "TargetOriginId": "previews", "FunctionAssociations": {"Quantity": 0}},
            ],
        },
        "Origins": {"Quantity": 1, "Items": [{"Id": "web", "DomainName": "origin.invalid"}]},
    }
    return base


class FakeAws:
    def __init__(self, config: dict, *, etag: str = "E1", reject_update: bool = False,
                 function_status: int = 503):
        self.config = copy.deepcopy(config)
        self.etag = etag
        self.reject_update = reject_update
        self.function_status = function_status
        self.calls: list[list[str]] = []

    def __call__(self, args: list[str], input_json: dict | None = None) -> dict:
        self.calls.append(args)
        action = args[1:3]
        if action == ["cloudfront", "describe-function"]:
            return {"ETag": "F1", "FunctionSummary": {"Name": "maintenance", "FunctionMetadata": {
                "FunctionARN": "arn:aws:cloudfront::123456789012:function/maintenance", "Stage": "LIVE"}}}
        if action == ["cloudfront", "test-function"]:
            return {"TestResult": {"FunctionErrorMessage": "", "FunctionOutput": json.dumps({
                "response": {"statusCode": self.function_status}})}}
        if action == ["cloudfront", "get-distribution-config"]:
            return {"ETag": self.etag, "DistributionConfig": copy.deepcopy(self.config)}
        if action == ["cloudfront", "get-distribution"]:
            return {"Distribution": {"Id": "DIST1", "Status": "Deployed"}}
        if action == ["cloudfront", "update-distribution"]:
            if self.reject_update or args[args.index("--if-match") + 1] != self.etag:
                raise RuntimeError("PreconditionFailed")
            self.config = copy.deepcopy(input_json)
            self.etag = "E2" if self.etag == "E1" else "E3"
            return {"Distribution": {"Status": "InProgress"}}
        if action == ["cloudfront", "wait"]:
            return {}
        raise AssertionError(args)


class Response:
    def __init__(self, status: int, url: str):
        self.status = status
        self.url = url

    def geturl(self):
        return self.url

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False


def access_probe(request, timeout: float):
    assert timeout > 0
    if request.full_url == "https://private.invalid/health":
        assert request.headers["X-colab-operator"] == "secret"
        return Response(200, request.full_url)
    if request.full_url == "https://origin.invalid/health":
        return Response(403, request.full_url)
    raise AssertionError(request.full_url)


def write_config(tmp_path, *, function_arn="arn:aws:cloudfront::123456789012:function/maintenance"):
    header = tmp_path / "operator.header"
    header.write_text("secret\n", encoding="utf-8")
    header.chmod(0o600)
    state = tmp_path / "maintenance-state.json"
    config = tmp_path / "operator.json"
    config.write_text(json.dumps({
        "distribution_id": "DIST1",
        "maintenance_function_arn": function_arn,
        "maintenance_function_name": "maintenance",
        "state_file": str(state),
        "private_seed": {
            "url": "https://private.invalid/health",
            "header_name": "X-Colab-Operator",
            "header_file": str(header),
            "public_origin_probe_url": "https://origin.invalid/health",
        },
    }), encoding="utf-8")
    return config, state


def test_enter_blocks_default_api_and_previews_and_preserves_original(tmp_path):
    module = load_module()
    original = distribution_config("arn:aws:cloudfront::123456789012:function/spa")
    aws = FakeAws(original)
    config, state_path = write_config(tmp_path)

    result = module.execute("enter", config, run_aws=aws, open_url=access_probe)

    assert result["state"] == "active"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    assert state["original_distribution_config"] == original
    assert stat.S_IMODE(state_path.stat().st_mode) == 0o600
    assert sum(call[1:3] == ["cloudfront", "test-function"] for call in aws.calls) == 3
    behaviors = [aws.config["DefaultCacheBehavior"], *aws.config["CacheBehaviors"]["Items"]]
    assert all(b["FunctionAssociations"] == {"Quantity": 1, "Items": [association(result["maintenance_function_arn"])]}
               for b in behaviors)
    assert original["DefaultCacheBehavior"]["FunctionAssociations"]["Items"][0]["FunctionARN"].endswith("/spa")


def test_etag_conflict_leaves_entering_state_and_never_claims_active(tmp_path):
    module = load_module()
    aws = FakeAws(distribution_config("arn:aws:cloudfront::123456789012:function/spa"), reject_update=True)
    config, state_path = write_config(tmp_path)

    with pytest.raises(RuntimeError, match="PreconditionFailed"):
        module.execute("enter", config, run_aws=aws, open_url=access_probe)

    state = json.loads(state_path.read_text(encoding="utf-8"))
    assert state["state"] == "entering"


def test_leave_restores_exact_original_after_readback_verification(tmp_path):
    module = load_module()
    original = distribution_config("arn:aws:cloudfront::123456789012:function/spa")
    aws = FakeAws(original)
    config, state_path = write_config(tmp_path)
    module.execute("enter", config, run_aws=aws, open_url=access_probe)

    result = module.execute("leave", config, run_aws=aws, open_url=access_probe)

    assert result["state"] == "restored"
    assert aws.config == original
    assert json.loads(state_path.read_text(encoding="utf-8"))["state"] == "restored"


def test_missing_private_seed_verification_fails_before_aws_write(tmp_path):
    module = load_module()
    config, _ = write_config(tmp_path)
    raw = json.loads(config.read_text(encoding="utf-8"))
    del raw["private_seed"]
    config.write_text(json.dumps(raw), encoding="utf-8")
    aws = FakeAws(distribution_config("arn:aws:cloudfront::123456789012:function/spa"))

    with pytest.raises(module.ReadinessError, match="private_seed"):
        module.execute("enter", config, run_aws=aws, open_url=access_probe)

    assert aws.calls == []


def test_enter_rejects_live_function_that_does_not_return_503(tmp_path):
    module = load_module()
    config, state_path = write_config(tmp_path)
    aws = FakeAws(distribution_config("arn:aws:cloudfront::123456789012:function/spa"), function_status=200)

    with pytest.raises(module.ReadinessError, match="503"):
        module.execute("enter", config, run_aws=aws, open_url=access_probe)

    assert not state_path.exists()
    assert not any(call[1:3] == ["cloudfront", "update-distribution"] for call in aws.calls)


def test_status_rejects_interrupted_enter_without_mutating_cloudfront(tmp_path):
    module = load_module()
    config, state_path = write_config(tmp_path)
    state_path.write_text(json.dumps({"schema": "colab-product-maintenance/1", "state": "entering"}), encoding="utf-8")
    state_path.chmod(0o600)
    aws = FakeAws(distribution_config("arn:aws:cloudfront::123456789012:function/spa"))

    with pytest.raises(module.ReadinessError, match="active"):
        module.execute("status", config, run_aws=aws, open_url=access_probe)
    assert aws.calls == []


def test_active_enter_is_idempotent_only_after_remote_verification(tmp_path):
    module = load_module()
    original = distribution_config("arn:aws:cloudfront::123456789012:function/spa")
    aws = FakeAws(original)
    config, _ = write_config(tmp_path)
    module.execute("enter", config, run_aws=aws, open_url=access_probe)
    updates = sum(call[1:3] == ["cloudfront", "update-distribution"] for call in aws.calls)

    result = module.execute("enter", config, run_aws=aws, open_url=access_probe)

    assert result["state"] == "active"
    assert sum(call[1:3] == ["cloudfront", "update-distribution"] for call in aws.calls) == updates


def test_entering_requires_explicit_resume_and_can_recover_active_remote(tmp_path):
    module = load_module()
    original = distribution_config("arn:aws:cloudfront::123456789012:function/spa")
    aws = FakeAws(original)
    config, state_path = write_config(tmp_path)
    active = module.execute("enter", config, run_aws=aws, open_url=access_probe)
    active["state"] = "entering"
    state_path.write_text(json.dumps(active), encoding="utf-8")
    state_path.chmod(0o600)

    with pytest.raises(module.ReadinessError, match="resume"):
        module.execute("enter", config, run_aws=aws, open_url=access_probe)
    result = module.execute("enter", config, resume=True, run_aws=aws, open_url=access_probe)
    assert result["state"] == "active"


def test_leave_rejects_distribution_id_changed_from_state(tmp_path):
    module = load_module()
    aws = FakeAws(distribution_config("arn:aws:cloudfront::123456789012:function/spa"))
    config, _ = write_config(tmp_path)
    module.execute("enter", config, run_aws=aws, open_url=access_probe)
    raw = json.loads(config.read_text(encoding="utf-8"))
    raw["distribution_id"] = "OTHER"
    config.write_text(json.dumps(raw), encoding="utf-8")
    with pytest.raises(module.ReadinessError, match="distribution_id"):
        module.execute("leave", config, run_aws=aws, open_url=access_probe)


def test_unexpected_cache_behavior_is_rejected_as_public_bypass(tmp_path):
    module = load_module()
    original = distribution_config("arn:aws:cloudfront::123456789012:function/spa")
    original["CacheBehaviors"]["Items"].append({"PathPattern": "/downloads/*", "FunctionAssociations": {"Quantity": 0}})
    original["CacheBehaviors"]["Quantity"] = 3
    config, state_path = write_config(tmp_path)
    with pytest.raises(module.ReadinessError, match="예상하지 않은"):
        module.execute("enter", config, run_aws=FakeAws(original), open_url=access_probe)
    assert not state_path.exists()


def test_private_seed_redirect_is_rejected_before_secret_can_follow(tmp_path):
    module = load_module()
    config, _ = write_config(tmp_path)
    def redirected(request, timeout):
        return Response(200, "https://redirected.invalid/health")
    with pytest.raises(module.ReadinessError, match="redirect"):
        module.execute("enter", config, run_aws=FakeAws(distribution_config("spa")), open_url=redirected)


def test_leave_state_write_failure_reenters_maintenance_and_records_active(tmp_path, monkeypatch):
    module = load_module()
    original = distribution_config("arn:aws:cloudfront::123456789012:function/spa")
    aws = FakeAws(original)
    config, state_path = write_config(tmp_path)
    module.execute("enter", config, run_aws=aws, open_url=access_probe)
    real_write = module._write_state

    def fail_restored(path, value):
        if value.get("state") == "restored":
            raise OSError("disk full")
        real_write(path, value)

    monkeypatch.setattr(module, "_write_state", fail_restored)
    with pytest.raises(RuntimeError, match="점검 상태로 복구"):
        module.execute("leave", config, run_aws=aws, open_url=access_probe)

    state = json.loads(state_path.read_text(encoding="utf-8"))
    assert state["state"] == "active"
    assert module._digest(aws.config) == state["maintenance_digest"]


def test_sigkill_after_restore_can_be_resumed_to_maintenance(tmp_path):
    module = load_module()
    original = distribution_config("arn:aws:cloudfront::123456789012:function/spa")
    aws = FakeAws(original)
    config, state_path = write_config(tmp_path)
    active = module.execute("enter", config, run_aws=aws, open_url=access_probe)
    restoring = dict(active, state="restoring")
    state_path.write_text(json.dumps(restoring), encoding="utf-8")
    state_path.chmod(0o600)
    aws.config = copy.deepcopy(original)
    aws.etag = "E3"

    with pytest.raises(module.ReadinessError, match="resume"):
        module.execute("enter", config, run_aws=aws, open_url=access_probe)
    result = module.execute("enter", config, resume=True, run_aws=aws, open_url=access_probe)

    assert result["state"] == "active"
    assert module._digest(aws.config) == result["maintenance_digest"]


def test_aws_subprocess_inherits_local_and_controller_lock_fds(tmp_path):
    module = load_module()
    local = (tmp_path / "local.lock").open("a+")
    controller_read, controller_write = os.pipe()
    try:
        module._LOCK_FDS[:] = [local.fileno(), controller_read]
        code = "import json,os,sys; [os.fstat(int(x)) for x in sys.argv[1:]]; print(json.dumps({'inherited': True}))"
        result = module._default_run_aws([sys.executable, "-c", code, str(local.fileno()), str(controller_read)])
        assert result == {"inherited": True}
    finally:
        module._LOCK_FDS.clear()
        local.close()
        os.close(controller_read)
        os.close(controller_write)
