"""Fixed-list operator revocation uses the real account-admin role and real sessions."""
from __future__ import annotations

import copy
import importlib
import json
import subprocess
import sys
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker

from conftest import DS_A1, LAB_A, TOKEN_PROF, auth
from test_operator_designation import LAB_C

PASSWORD = "전환-시험-초기암호-123"
NORMAL = "전환-시험-정상암호-456"
CLI = Path(__file__).parents[1] / "ops/reconcile_service_operators.py"


@pytest.fixture
def transition_case(p2_client, admin_db_url):
    client = p2_client(session_secret="operator-transition-test-secret")
    engine = create_engine(admin_db_url)
    owner = create_engine(make_url(admin_db_url).set(username="postgres", password=None))
    with engine.connect() as db:
        original = list(db.execute(text("SELECT account_id FROM account_admin.service_operator")).scalars())
    accounts = []
    for label in ("keep", "revoke"):
        email = f"transition-{label}-{uuid.uuid4().hex}@example.com"
        made = client.post("/api/v1/admin/accounts", headers=auth(TOKEN_PROF), json={
            "email": email, "name": label, "labId": LAB_A, "role": "교수",
            "operator": True, "initialPassword": PASSWORD,
        })
        assert made.status_code == 201, made.text
        login = client.post("/api/v1/sessions", json={"accountName": email, "password": PASSWORD})
        changed = client.put("/api/v1/me/password", headers=auth(login.json()["token"]),
                             json={"newPassword": NORMAL})
        assert changed.status_code == 200, changed.text
        accounts.append({"id": made.json()["accountId"], "email": email,
                         "token": changed.json()["token"]})
    with engine.begin() as db:
        for account_id in original:
            db.execute(text("DELETE FROM account_admin.service_operator WHERE account_id=:id"), {"id": account_id})
    keep, revoke = accounts
    case = {"client": client, "engine": engine, "owner": owner,
            "created_ids": [row["id"] for row in accounts],
            "factory": sessionmaker(engine), "keep": keep, "revoke": revoke,
            "selection": {"actorId": keep["id"],
                          "keep": [{"accountId": keep["id"], "reason": "시스템 운영 담당"}],
                          "revoke": [{"accountId": revoke["id"], "reason": "교수 관리자 전환"}]}}
    try:
        yield case
    finally:
        with engine.begin() as db:
            db.execute(text("DELETE FROM account_admin.service_operator"))
            for account_id in original:
                db.execute(text("INSERT INTO account_admin.service_operator VALUES (:id, now())"), {"id": account_id})
        # Preserve audit FKs while keeping later tests' A/B member fixtures unchanged.
        with owner.begin() as db:
            for account_id in case["created_ids"]:
                db.execute(text("UPDATE d1_account SET lab_id=:lab WHERE id=:id"), {"id": account_id, "lab": LAB_C})
                db.execute(text("UPDATE d2_member_role SET lab_id=:lab WHERE account_id=:id"), {"id": account_id, "lab": LAB_C})
        engine.dispose()
        owner.dispose()


def _module():
    spec = importlib.util.find_spec("colab_core.kernel.operator_transition")
    assert spec is not None, "원자적 고정 목록 계정 전환 구현이 없다"
    return importlib.import_module("colab_core.kernel.operator_transition")


def _state(case):
    with case["owner"].connect() as db:
        return {
            "accounts": [tuple(row) for row in db.execute(text("""
                SELECT a.id, a.lab_id, m.role, c.status, c.password_hash, c.session_version,
                       EXISTS(SELECT 1 FROM account_admin.service_operator o WHERE o.account_id=a.id)
                FROM d1_account a JOIN account_admin.login_credential c ON c.account_id=a.id
                LEFT JOIN d2_member_role m ON m.account_id=a.id AND m.lab_id=a.lab_id
                WHERE a.id IN (:keep, :revoke) ORDER BY a.id
            """), {"keep": case["keep"]["id"], "revoke": case["revoke"]["id"]})],
            "sessions": [tuple(row) for row in db.execute(text("""
                SELECT account_id, id, revoked_at FROM account_admin.login_session
                WHERE account_id IN (:keep, :revoke) ORDER BY id
            """), {"keep": case["keep"]["id"], "revoke": case["revoke"]["id"]})],
            "data": [tuple(row) for row in db.execute(text("SELECT id, lab_id FROM d3_dataset ORDER BY id"))],
        }


def test_dry_run_does_not_change_accounts_sessions_or_data(transition_case):
    module = _module()
    case = transition_case
    before = _state(case)
    plan = module.OperatorTransition(case["factory"]).prepare(case["selection"])
    assert _state(case) == before
    assert plan["beforeOperatorIds"] == sorted([case["keep"]["id"], case["revoke"]["id"]])
    assert plan["afterOperatorIds"] == [case["keep"]["id"]]
    assert "email" not in json.dumps(plan) and "password" not in json.dumps(plan)


@pytest.mark.parametrize("invalid", ["overlap", "duplicate", "unclassified", "unknown",
                                      "last", "self", "reason", "not-professor", "inactive-actor"])
def test_invalid_selection_is_refused_without_changes(transition_case, invalid):
    module = _module()
    case = transition_case
    selection = copy.deepcopy(case["selection"])
    if invalid == "overlap":
        selection["keep"].append(selection["revoke"][0])
    elif invalid == "duplicate":
        selection["revoke"] *= 2
    elif invalid == "unclassified":
        selection["revoke"] = []
    elif invalid == "unknown":
        selection["revoke"][0]["accountId"] = "0000000000000000000000NONE"
    elif invalid == "last":
        selection["revoke"] += selection["keep"]
        selection["keep"] = []
    elif invalid == "self":
        selection["actorId"] = case["revoke"]["id"]
    elif invalid == "reason":
        selection["revoke"][0]["reason"] = " "
    else:
        with case["owner"].begin() as db:
            if invalid == "not-professor":
                db.execute(text("UPDATE d2_member_role SET role='연구원' WHERE account_id=:id"),
                           {"id": case["revoke"]["id"]})
            else:
                db.execute(text("UPDATE account_admin.login_credential SET status='inactive' WHERE account_id=:id"),
                           {"id": case["keep"]["id"]})
    before = _state(case)
    with pytest.raises(module.TransitionRefused):
        module.OperatorTransition(case["factory"]).prepare(selection)
    assert _state(case) == before


@pytest.mark.parametrize("drift", ["role", "status", "operator", "hash"])
def test_plan_drift_and_wrong_hash_refuse_the_whole_batch(transition_case, drift):
    module = _module()
    case = transition_case
    service = module.OperatorTransition(case["factory"])
    plan = service.prepare(case["selection"])
    digest = module.plan_sha256(plan)
    with case["owner"].begin() as db:
        if drift == "role":
            db.execute(text("UPDATE d2_member_role SET role='연구원' WHERE account_id=:id"), {"id": case["revoke"]["id"]})
        elif drift == "status":
            db.execute(text("UPDATE account_admin.login_credential SET status='inactive' WHERE account_id=:id"), {"id": case["revoke"]["id"]})
        elif drift == "operator":
            db.execute(text("DELETE FROM account_admin.service_operator WHERE account_id=:id"), {"id": case["keep"]["id"]})
        else:
            digest = "0" * 64
    before = _state(case)
    with pytest.raises(module.TransitionRefused):
        service.apply(plan, digest)
    assert _state(case) == before


def test_apply_revokes_only_system_role_and_old_sessions_then_is_idempotent(transition_case):
    module = _module()
    case = transition_case
    service = module.OperatorTransition(case["factory"])
    plan = service.prepare(case["selection"])
    before = _state(case)
    result = service.apply(plan, module.plan_sha256(plan))
    assert result == {"changed": 1, "alreadyApplied": False}
    after = _state(case)
    assert after["data"] == before["data"]
    for old, new in zip(before["accounts"], after["accounts"]):
        assert new[:5] == old[:5]  # account, affiliation, professor role, status, password
        assert new[5] == old[5] + (old[0] == case["revoke"]["id"])
        assert new[6] == (old[0] == case["keep"]["id"])
    client = case["client"]
    assert client.get("/api/v1/me-v2", headers=auth(case["revoke"]["token"])).status_code == 401
    assert client.get("/api/v1/admin/accounts-v2", headers=auth(case["keep"]["token"])).status_code == 200
    login = client.post("/api/v1/sessions", json={"accountName": case["revoke"]["email"], "password": NORMAL})
    assert login.status_code == 201, login.text
    headers = auth(login.json()["token"])
    me = client.get("/api/v1/me-v2", headers=headers).json()
    assert me["role"] == "교수" and me["labId"] == LAB_A and me["canManageServiceAccounts"] is False
    assert client.get("/api/v1/admin/accounts-v2", headers=headers).status_code == 403
    assert client.get(f"/api/v1/datasets/{DS_A1}", headers=headers).status_code == 200
    before_second = _state(case)
    assert service.apply(plan, module.plan_sha256(plan)) == {"changed": 0, "alreadyApplied": True}
    assert _state(case) == before_second


def test_cli_requires_hash_and_does_not_print_connection_secrets(transition_case, tmp_path, admin_db_url):
    assert CLI.is_file(), "고정 목록 전환 CLI가 없다"
    case = transition_case
    url_file = tmp_path / "database-url"
    url_file.write_text(admin_db_url)
    selection = tmp_path / "selection.json"
    selection.write_text(json.dumps(case["selection"]))
    plan = tmp_path / "plan.json"
    command = [sys.executable, str(CLI), "--database-url-file", str(url_file)]
    inventory = subprocess.run(command + ["list"], capture_output=True, text=True)
    assert inventory.returncode == 0, inventory.stderr
    assert {row["accountId"] for row in json.loads(inventory.stdout)["operators"]} == {
        case["keep"]["id"], case["revoke"]["id"]}
    dry = subprocess.run(command + ["prepare", "--selection", str(selection), "--output", str(plan)], capture_output=True, text=True)
    assert dry.returncode == 0, dry.stderr
    digest = json.loads(dry.stdout)["planSha256"]
    before = _state(case)
    refused = subprocess.run(command + ["apply", "--plan", str(plan)], capture_output=True, text=True)
    assert refused.returncode != 0 and _state(case) == before
    applied = subprocess.run(command + ["apply", "--plan", str(plan), "--plan-sha256", digest], capture_output=True, text=True)
    assert applied.returncode == 0, applied.stderr
    assert json.loads(applied.stdout)["changed"] == 1
    assert admin_db_url not in dry.stdout + dry.stderr + refused.stdout + refused.stderr + applied.stdout + applied.stderr


def test_failure_during_session_revocation_rolls_back_operator_and_version(transition_case):
    module = _module()
    case = transition_case
    service = module.OperatorTransition(case["factory"])
    plan = service.prepare(case["selection"])
    before = _state(case)
    # A real storage failure after operator DELETE and credential UPDATE catches per-step commits.
    with case["owner"].begin() as db:
        db.execute(text("""CREATE FUNCTION account_admin.reject_transition_test() RETURNS trigger
            LANGUAGE plpgsql AS $$ BEGIN RAISE EXCEPTION 'test storage failure'; END $$"""))
        db.execute(text("""CREATE TRIGGER reject_transition_test BEFORE UPDATE ON account_admin.login_session
            FOR EACH ROW EXECUTE FUNCTION account_admin.reject_transition_test()"""))
    try:
        with pytest.raises(SQLAlchemyError):
            service.apply(plan, module.plan_sha256(plan))
        assert _state(case) == before
    finally:
        with case["owner"].begin() as db:
            db.execute(text("DROP TRIGGER reject_transition_test ON account_admin.login_session"))
            db.execute(text("DROP FUNCTION account_admin.reject_transition_test()"))


def test_concurrent_account_creation_is_serialized_and_invalidates_plan(transition_case):
    module = _module()
    case = transition_case
    service = module.OperatorTransition(case["factory"])
    plan = service.prepare(case["selection"])
    before = _state(case)
    # Stall the real create-account API while it holds its existing creation lock.
    with case["owner"].begin() as db:
        db.execute(text("""CREATE FUNCTION public.pause_transition_creation() RETURNS trigger
            LANGUAGE plpgsql AS $$ BEGIN PERFORM pg_advisory_xact_lock(1131379991);
            RETURN NEW; END $$"""))
        db.execute(text("""CREATE TRIGGER pause_transition_creation BEFORE INSERT ON d1_account
            FOR EACH ROW EXECUTE FUNCTION public.pause_transition_creation()"""))
    blocker = case["owner"].connect()
    blocker.begin()
    blocker.execute(text("SELECT pg_advisory_xact_lock(1131379991)"))
    pool = ThreadPoolExecutor(max_workers=2)
    try:
        def create_concurrent():
            response = case["client"].post("/api/v1/admin/accounts", headers=auth(case["keep"]["token"]), json={
                "email": f"concurrent-{uuid.uuid4().hex}@example.com", "name": "동시 생성",
                "labId": LAB_A, "role": "교수", "operator": True, "initialPassword": PASSWORD})
            if response.status_code == 201:
                case["created_ids"].append(response.json()["accountId"])
            return response

        created = pool.submit(create_concurrent)

        def wait_for_lock(key):
            deadline = time.monotonic() + 5
            while time.monotonic() < deadline:
                with case["owner"].connect() as db:
                    if db.execute(text("SELECT count(*) FROM pg_locks WHERE locktype='advisory' AND objid=:key AND NOT granted"),
                                  {"key": key}).scalar_one():
                        return True
                time.sleep(0.02)
            return False

        assert wait_for_lock(1131379991), "실제 계정 생성이 시험 장벽에 도달하지 않았다"
        applied = pool.submit(service.apply, plan, module.plan_sha256(plan))
        assert wait_for_lock(1131379081), "전환이 진행 중인 계정 생성 잠금을 기다리지 않았다"
        blocker.commit()
        assert created.result(timeout=5).status_code == 201
        with pytest.raises(module.TransitionRefused):
            applied.result(timeout=5)
        assert _state(case) == before
    finally:
        blocker.close()
        pool.shutdown(wait=True)
        with case["owner"].begin() as db:
            db.execute(text("DROP TRIGGER pause_transition_creation ON d1_account"))
            db.execute(text("DROP FUNCTION public.pause_transition_creation()"))
