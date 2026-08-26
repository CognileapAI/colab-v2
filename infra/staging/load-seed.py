#!/usr/bin/env python3
"""S2 초기 데이터 적재 도구 — 공개 API 만 부른다.

명세 = `dev-package/sessions/S2-EXEC-PLAN.md §14`(요구 R-1~R-11) · 멱등 설계 = 같은 문서 `§5.4`.
판정 `〈106〉` — **멱등은 이 도구가 자기 재실행에 대해 보장한다.** 제품(계약·스키마·core-api)은
손대지 않는다.

**DB 에 접속하지 않는다.** DB 드라이버를 import 하지 않는 것이 `㊾-③`(「적재는 DB 직접 INSERT 가
아니라 화면이 쓰는 경로 그대로」) 위반을 코드로 불가능하게 만드는 수단이다 (R-2).

부르는 op 은 계약(`contracts/seams/fe-core.yaml`)의 넷뿐이다 (R-1) —
`listDatasets` · `createUpload` · `createDataset` · `attachUploadGridFiles`.
`deleteDataset` 은 501 이고, 삭제는 이 도구의 동작이 아니다 (R-6).

⚠ **이 도구가 대체하지 않는 것 = S-04 업로드 모달의 실사용 시험.** 도구는 FE 코드를 지나지
않고 그 모달이 부르는 **서버 표면**을 재현한다 (`§14.2` 결손 · `§14.3` 회차 ① 은 화면으로).

실행
    load-seed.py --base-url URL --token-file PATH --manifest PATH --source-root PATH [--round N]

시험 = `python3 infra/staging/load-seed-test.py` (staging 무의존)
"""
from __future__ import annotations

import argparse
import json
import mimetypes
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from dataclasses import dataclass, field
from pathlib import Path

API = "/api/v1"


class Abort(Exception):
    """중단 조건. 다음 데이터셋으로 넘어가지 않는다 (R-7 · `CLAUDE.md §4`)."""


# ── 결과 ─────────────────────────────────────────────────────────────────────

@dataclass
class Result:
    exit_code: int = 0
    loaded: int = 0
    skipped: int = 0
    attached: int = 0
    write_calls: int = 0
    log: list[str] = field(default_factory=list)
    report: str = ""


# ── HTTP — 표준 라이브러리만 ─────────────────────────────────────────────────

class Client:
    """토큰은 헤더에만 실린다. 로그·보고서에 적지 않는다 (R-8)."""

    def __init__(self, base_url: str, token: str):
        self.base = base_url.rstrip("/")
        self._token = token
        self.write_calls = 0

    def _send(self, req: urllib.request.Request):
        req.add_header("Authorization", f"Bearer {self._token}")
        if req.get_method() != "GET":
            self.write_calls += 1
        try:
            with urllib.request.urlopen(req, timeout=600) as r:
                raw = r.read()
                return r.status, (json.loads(raw) if raw else {})
        except urllib.error.HTTPError as e:
            raw = e.read()
            try:
                body = json.loads(raw)
            except Exception:
                body = {"raw": raw[:400].decode("utf-8", "replace")}
            return e.code, body
        except urllib.error.URLError as e:
            raise Abort(f"core-api 에 닿지 못했다 — {e.reason}") from None

    def get(self, path: str, params: dict | None = None):
        url = f"{self.base}{path}"
        if params:
            url += "?" + urllib.parse.urlencode(params)
        return self._send(urllib.request.Request(url, method="GET"))

    def post_json(self, path: str, body: dict):
        raw = json.dumps(body, ensure_ascii=False).encode()
        req = urllib.request.Request(f"{self.base}{path}", data=raw, method="POST")
        req.add_header("Content-Type", "application/json")
        return self._send(req)

    def post_multipart(self, path: str, files: list[tuple[str, Path]], kinds: list[str]):
        """`files` 와 `fileKinds` 를 **같은 순서**로 싣는다.

        ⚠ 순서가 어긋나도 서버는 오류를 내지 않는다 — 격자 파일이 본체로 접수될 뿐이다
        (`contracts/seams/fe-core.yaml:231` · R-9). 그래서 여기서 단언한다.
        """
        if len(files) != len(kinds):
            raise Abort(f"files {len(files)} 과 fileKinds {len(kinds)} 의 짝이 어긋났다")

        boundary = "----colab" + uuid.uuid4().hex
        buf = bytearray()
        for (name, p), kind in zip(files, kinds):
            ctype = mimetypes.guess_type(name)[0] or "application/octet-stream"
            buf += f"--{boundary}\r\n".encode()
            buf += (f'Content-Disposition: form-data; name="files"; '
                    f'filename="{name}"\r\n').encode()
            buf += f"Content-Type: {ctype}\r\n\r\n".encode()
            buf += p.read_bytes()
            buf += b"\r\n"
        for kind in kinds:
            buf += f"--{boundary}\r\n".encode()
            buf += b'Content-Disposition: form-data; name="fileKinds"\r\n\r\n'
            buf += kind.encode() + b"\r\n"
        buf += f"--{boundary}--\r\n".encode()

        req = urllib.request.Request(f"{self.base}{path}", data=bytes(buf), method="POST")
        req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
        return self._send(req)


# ── 조회 — `listDatasets` 전수 순회 (§5.4.2) ─────────────────────────────────

def build_index(client: Client) -> dict[str, list[dict]]:
    """`nextCursor` 가 null 이 될 때까지 순회한다 (R-4).

    첫 페이지만 읽고 「없다」 하면 뒤쪽 이름을 못 보고 그대로 중복 적재한다.
    이름 조건 파라미터가 계약에 없으므로 대조는 도구 안에서 한다 — 서버에 이름 조건을
    새로 여는 것은 계약 개정이다 (`§5.4.2`).
    """
    index: dict[str, list[dict]] = {}
    cursor = None
    seen = 0
    while True:
        params = {"cursor": cursor} if cursor else {}
        status, body = client.get(f"{API}/datasets", params)
        if status != 200:
            raise Abort(f"listDatasets 가 {status} 를 냈다 — {body}")
        for row in body.get("items", []):
            index.setdefault(row["name"], []).append(row)
            seen += 1
        cursor = body.get("nextCursor")
        if not cursor:
            total = body.get("totalCount")
            if isinstance(total, int) and seen != total:
                raise Abort(f"순회가 {seen} 건인데 totalCount 는 {total} 이다")
            return index


# ── 판정 (§5.4.4) ────────────────────────────────────────────────────────────

def decide(name: str, planned: int, index: dict[str, list[dict]]) -> tuple[str, dict | None]:
    rows = index.get(name, [])
    if len(rows) > 1:
        raise Abort(f"「{name}」 이름이 {len(rows)} 건이다 — 멱등이 이미 깨졌다")
    if not rows:
        return "적재", None
    row = rows[0]
    have = row["fileCount"]
    if have == planned:
        return "건너뜀", row
    if have < planned:
        return "이어붙임", row
    raise Abort(f"「{name}」 의 fileCount {have} 가 계획치 {planned} 를 넘는다 — 원인 미상")


# ── 적재 ─────────────────────────────────────────────────────────────────────

def _files_of(ds: dict, source_root: Path, kinds: set[str] | None = None):
    out = []
    for f in ds["files"]:
        if kinds is not None and f["kind"] not in kinds:
            continue
        p = source_root / f["path"]
        if not p.is_file():
            raise Abort(f"원천 파일이 없다 — {f['path']}")
        out.append((Path(f["path"]).name, p, f["kind"]))
    return out


def _create_upload(client: Client, entries):
    files = [(n, p) for n, p, _ in entries]
    kinds = [k for _, _, k in entries]
    status, body = client.post_multipart(f"{API}/uploads", files, kinds)
    if status != 201:
        raise Abort(f"createUpload 가 {status} 를 냈다 — {body}")
    return body["uploadId"]


def load_dataset(client: Client, ds: dict, source_root: Path, resolved: dict[str, str]) -> str:
    entries = _files_of(ds, source_root)
    upload_id = _create_upload(client, entries)

    body: dict = {"uploadId": upload_id, "name": ds["name"]}
    for key in ("topic", "summary", "sourceLabel"):
        if ds.get(key) is not None:
            body[key] = ds[key]

    parents = []
    for parent in ds.get("lineageParents", []):
        pid = resolved.get(parent["parentKey"])
        if not pid:
            raise Abort(f"계보 부모 {parent['parentKey']} 의 datasetId 를 모른다 "
                        f"— 부모가 먼저 적재돼야 한다")
        item = {"parentDatasetId": pid, "origin": parent.get("origin", "사람이 직접 연결")}
        if parent.get("parentRole"):
            item["parentRole"] = parent["parentRole"]
        if parent.get("method"):
            item["method"] = parent["method"]
        parents.append(item)
    if parents:
        # [모두 승인] 이 아니다 — 부모·역할은 `SEED-DATA §4.1` 이 확정한 값이고
        # 도구는 그것을 옮기기만 한다 (`CLAUDE.md §3-2` · `§14.3`).
        body["lineageParents"] = parents

    status, resp = client.post_json(f"{API}/datasets", body)
    if status != 201:
        raise Abort(f"createDataset 가 {status} 를 냈다 — {resp}")
    return resp["datasetId"]


#: 축 판별을 기다리는 상한(초). 워커 루프가 5초 주기이므로 여러 바퀴를 덮는다.
GRID_AXIS_TIMEOUT = 180.0


def _await_grid_axes(client: Client, upload_id: str, expected: int) -> dict:
    """축 판별이 **끝날 때까지** 기다린다. 돌려주는 것은 마지막 상태 본문이다.

    ⚠ **이 기다림이 없어서 `#31` 이 났다.** 접수와 축 판별 사이는 **비동기 seam** 이다 —
    `createUpload` 는 바이트만 받고, 축은 pipeline-worker 가 나중에 정해 원장 행을 세운다
    (`〈79〉-㈎`). 곧바로 `attachUploadGridFiles` 를 부르면 그 행이 아직 없어서 서버가
    **400 「축이 확정된 기준 격자 파일이 없다」** 를 낸다. 도구가 못 기다린 것을 서버 결함으로
    읽으면 안 된다 — 그래서 여기서 **사실이 설 때까지** 기다리고, 안 서면 그 사실을 적는다.

    끝났다고 보는 조건 둘 — 축이 확정된 파일이 기대 건수만큼 생겼거나, `gridRejections` 가
    비어 있지 않다(거절도 결론이다). 어느 쪽도 아니면 상한까지 기다렸다가 중단한다.
    """
    deadline = time.monotonic() + GRID_AXIS_TIMEOUT
    body: dict = {}
    while True:
        status, body = client.get(f"{API}/uploads/{upload_id}")
        if status != 200:
            raise Abort(f"getUploadStatus 가 {status} 를 냈다 — {body}")
        settled = [f for f in body.get("files", []) if f.get("gridAxis")]
        if len(settled) >= expected or body.get("gridRejections"):
            return body
        if time.monotonic() >= deadline:
            raise Abort(
                f"축 판별이 {GRID_AXIS_TIMEOUT:.0f}초 안에 끝나지 않았다 "
                f"(확정 {len(settled)}/{expected} · 거절 0) — 워커가 도는지 먼저 본다")
        time.sleep(2.0)


def attach_grid(client: Client, ds: dict, source_root: Path, dataset_id: str) -> None:
    entries = _files_of(ds, source_root, kinds={"기준 격자 파일"})
    if not entries:
        raise Abort(f"「{ds['name']}」 이 계획치에 못 미치는데 붙일 격자 파일이 없다")
    upload_id = _create_upload(client, entries)
    _await_grid_axes(client, upload_id, len(entries))
    status, body = client.post_json(f"{API}/datasets/{dataset_id}/grid-files",
                                    {"uploadId": upload_id})
    if status != 201:
        raise Abort(f"attachUploadGridFiles 가 {status} 를 냈다 — {body}")


# ── 실행 ─────────────────────────────────────────────────────────────────────

def run(base_url: str, token: str, manifest_path: Path, source_root: Path,
        rounds: list[int] | None = None) -> Result:
    manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    datasets = manifest["datasets"]
    if rounds:
        datasets = [d for d in datasets if d.get("round") in rounds]

    client = Client(base_url, token)
    res = Result()
    lines: list[str] = []

    def say(msg: str) -> None:
        lines.append(msg)
        print(msg, file=sys.stderr)

    resolved: dict[str, str] = {}
    try:
        # 조회가 `createUpload` 보다 먼저다 — 뒤집으면 건너뛰는 경우에도 업로드가
        # 접수되고, 그 업로드는 수명이 다할 때까지 남는다 (`§8` 3-B-0).
        index = build_index(client)
        for ds in datasets:
            name = ds["name"]
            planned = len(ds["files"])
            action, row = decide(name, planned, index)   # R-3 — 건너뛰는 인자를 두지 않는다

            if action == "건너뜀":
                resolved[ds["key"]] = row["datasetId"]
                res.skipped += 1
                say(f"  건너뜀   [{ds['key']}] {name} (fileCount {row['fileCount']})")
            elif action == "이어붙임":
                attach_grid(client, ds, source_root, row["datasetId"])
                resolved[ds["key"]] = row["datasetId"]
                res.attached += 1
                say(f"  이어붙임 [{ds['key']}] {name} "
                    f"({row['fileCount']} → {planned})")
            else:
                did = load_dataset(client, ds, source_root, resolved)
                resolved[ds["key"]] = did
                res.loaded += 1
                say(f"  적재     [{ds['key']}] {name} (파일 {planned})")
    except Abort as e:
        say(f"  중단 — {e}")
        res.exit_code = 1

    res.write_calls = client.write_calls
    res.log = lines
    res.report = "\n".join(lines + [
        "",
        f"적재 {res.loaded} · 건너뜀 {res.skipped} · 이어붙임 {res.attached} "
        f"· 쓰기 호출 {res.write_calls}",
    ])
    return res


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="S2 초기 데이터 적재 — 공개 API 만 부른다")
    ap.add_argument("--base-url", required=True)
    ap.add_argument("--token-file", required=True,
                    help="주체 토큰 파일. 값은 로그·산출물에 적지 않는다 (R-8)")
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--source-root", required=True)
    ap.add_argument("--round", type=int, action="append", dest="rounds",
                    help="회차 지정. 생략하면 전량 — 완료 조건 ② 는 전량 재실행으로 판정한다")
    a = ap.parse_args(argv)

    token = Path(a.token_file).read_text(encoding="utf-8").strip()
    if not token:
        print("토큰 파일이 비어 있다", file=sys.stderr)
        return 2

    res = run(base_url=a.base_url, token=token, manifest_path=Path(a.manifest),
              source_root=Path(a.source_root), rounds=a.rounds)
    print(res.report)
    return res.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
