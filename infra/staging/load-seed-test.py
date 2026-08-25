#!/usr/bin/env python3
"""load-seed.py 의 시험 — 표준 라이브러리만 쓴다.

실행 = `python3 infra/staging/load-seed-test.py`

**왜 mock HTTP 서버인가.** 도구가 지켜야 할 것 절반이 「무엇을 부르지 않았는가」다
(`S2-EXEC-PLAN §14.4` R-3·R-6·R-11). 호출 자체를 세지 않으면 그 절반은 단언할 자리가 없다.
그래서 시험은 함수를 흉내내지 않고 **실제 HTTP 표면**을 세워 요청을 기록한다 —
multipart 순서 짝(R-9)도 그 자리에서만 실물로 확인된다.

이 시험은 staging 에 접속하지 않는다.
"""
import json
import os
import shutil
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import importlib.util

_spec = importlib.util.spec_from_file_location("load_seed", HERE / "load-seed.py")
load_seed = importlib.util.module_from_spec(_spec)
# `@dataclass` 가 자기 모듈을 sys.modules 에서 되찾으므로 exec 전에 등록해야 한다.
sys.modules["load_seed"] = load_seed
_spec.loader.exec_module(load_seed)


# ── mock core-api ────────────────────────────────────────────────────────────
# 계약(`contracts/seams/fe-core.yaml`)의 op 4 건만 세운다. 그 밖의 경로는 404 를 내고
# 기록에 남긴다 — 도구가 계약 밖 op 을 부르면 시험이 그것을 본다(R-1).

class FakeState:
    def __init__(self, page_size=20):
        self.page_size = page_size
        self.datasets = []          # {datasetId, name, fileCount, lineageState}
        self.uploads = {}           # uploadId -> [{fileName, kind}]
        self.calls = []             # (method, path)
        self.multipart = []         # [(fileNames, fileKinds)]
        self.seen_auth = []
        self.fail_create_dataset_on = set()   # name 집합 — 그 이름이면 500
        self._seq = 0

    def next_id(self, prefix):
        self._seq += 1
        return f"{prefix}{self._seq:022d}"[:26].ljust(26, "0")

    def writes(self):
        return [c for c in self.calls if c[0] in ("POST", "PUT", "DELETE")]


class Handler(BaseHTTPRequestHandler):
    state: FakeState = None

    def log_message(self, *a):
        pass

    def _json(self, code, body):
        raw = json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def _record(self):
        self.state.calls.append((self.command, self.path.split("?")[0]))
        self.state.seen_auth.append(self.headers.get("Authorization", ""))

    def do_GET(self):
        self._record()
        st = self.state
        if self.path.split("?")[0] == "/api/v1/datasets":
            from urllib.parse import parse_qs, urlparse
            q = parse_qs(urlparse(self.path).query)
            cur = int(q.get("cursor", ["0"])[0])
            page = st.datasets[cur:cur + st.page_size]
            nxt = cur + st.page_size
            return self._json(200, {
                "items": [dict(d) for d in page],
                "totalCount": len(st.datasets),
                "nextCursor": str(nxt) if nxt < len(st.datasets) else None,
            })
        return self._json(404, {"code": "NOT_FOUND"})

    def do_POST(self):
        self._record()
        st = self.state
        path = self.path.split("?")[0]
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length)

        if path == "/api/v1/uploads":
            names, kinds = _parse_multipart(body, self.headers.get("Content-Type", ""))
            st.multipart.append((names, kinds))
            uid = st.next_id("U")
            st.uploads[uid] = [{"fileName": n, "kind": k} for n, k in zip(names, kinds)]
            return self._json(201, {
                "uploadId": uid,
                "files": [{"fileId": st.next_id("F"), "fileName": n,
                           "kind": k, "byteSize": 1} for n, k in zip(names, kinds)],
            })

        if path == "/api/v1/datasets":
            req = json.loads(body)
            name = req["name"]
            if name in st.fail_create_dataset_on:
                return self._json(500, {"code": "SERVER_ERROR"})
            up = st.uploads.pop(req["uploadId"], None)
            if up is None:
                return self._json(404, {"code": "NOT_FOUND"})
            did = st.next_id("D")
            st.datasets.append({
                "datasetId": did,
                "name": name,
                "fileCount": len(up),
                "lineageState": "확정" if req.get("lineageParents") else "원천",
            })
            return self._json(201, {"datasetId": did, "name": name})

        if path.startswith("/api/v1/datasets/") and path.endswith("/grid-files"):
            did = path.split("/")[4]
            req = json.loads(body)
            up = st.uploads.pop(req["uploadId"], None)
            if up is None:
                return self._json(404, {"code": "NOT_FOUND"})
            for d in st.datasets:
                if d["datasetId"] == did:
                    d["fileCount"] += len(up)
                    return self._json(201, {"items": [{"fileId": st.next_id("F")} for _ in up]})
            return self._json(404, {"code": "NOT_FOUND"})

        return self._json(404, {"code": "NOT_FOUND"})

    def do_DELETE(self):
        self._record()
        return self._json(404, {"code": "NOT_FOUND"})


def _parse_multipart(body, content_type):
    """`files` 와 `fileKinds` 를 **보낸 순서 그대로** 뽑는다 (R-9 단언용)."""
    boundary = content_type.split("boundary=")[1].encode()
    names, kinds = [], []
    for part in body.split(b"--" + boundary):
        if b"\r\n\r\n" not in part:
            continue
        head, val = part.split(b"\r\n\r\n", 1)
        val = val.rstrip(b"\r\n-")
        if b'name="files"' in head:
            fn = head.split(b'filename="')[1].split(b'"')[0]
            names.append(fn.decode())
        elif b'name="fileKinds"' in head:
            kinds.append(val.decode())
    return names, kinds


# ── 시험 뼈대 ────────────────────────────────────────────────────────────────

MANIFEST_3 = {
    "datasets": [
        {"key": "D-A", "round": 1, "name": "가 데이터셋", "topic": "식생·NDVI",
         "files": [{"path": "a1.nc", "kind": "본체"}, {"path": "a2.nc", "kind": "본체"}]},
        {"key": "D-B", "round": 1, "name": "나 데이터셋", "topic": "강우·강수",
         "files": [{"path": "b1.nc", "kind": "본체"},
                   {"path": "g_lat.npy", "kind": "기준 격자 파일"}]},
        {"key": "D-C", "round": 2, "name": "다 데이터셋", "topic": "식생·NDVI",
         "files": [{"path": "c1.nc", "kind": "본체"}],
         "lineageParents": [{"parentKey": "D-A", "parentRole": "주입력",
                             "method": "Nearest", "origin": "사람이 직접 연결"}]},
    ]
}


class LoaderCase(unittest.TestCase):
    def setUp(self):
        self.state = FakeState()
        Handler.state = self.state
        self.srv = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()
        self.base = f"http://127.0.0.1:{self.srv.server_address[1]}"

        self.tmp = Path(tempfile.mkdtemp())
        self.src = self.tmp / "src"
        self.src.mkdir()
        for d in MANIFEST_3["datasets"]:
            for f in d["files"]:
                (self.src / f["path"]).write_bytes(b"x" * 8)
        self.manifest = self.tmp / "m.json"
        self.manifest.write_text(json.dumps(MANIFEST_3, ensure_ascii=False))
        self.tokenfile = self.tmp / "tok"
        self.tokenfile.write_text("SECRET-TOKEN-VALUE\n")

    def tearDown(self):
        self.srv.shutdown()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def run_tool(self, **kw):
        return load_seed.run(
            base_url=self.base,
            token=self.tokenfile.read_text().strip(),
            manifest_path=self.manifest,
            source_root=self.src,
            **kw,
        )

    # ── ① 신규 적재 ──────────────────────────────────────────────────────────
    def test_fresh_load_creates_every_dataset(self):
        r = self.run_tool()
        self.assertEqual(r.exit_code, 0, r.report)
        self.assertEqual(len(self.state.datasets), 3)
        self.assertEqual({d["name"] for d in self.state.datasets},
                         {"가 데이터셋", "나 데이터셋", "다 데이터셋"})
        self.assertGreater(r.write_calls, 0)

    def test_file_count_matches_plan(self):
        self.run_tool()
        by = {d["name"]: d["fileCount"] for d in self.state.datasets}
        self.assertEqual(by["가 데이터셋"], 2)
        self.assertEqual(by["나 데이터셋"], 2)
        self.assertEqual(by["다 데이터셋"], 1)

    # ── ② 재실행 멱등 (완료 조건 ②) ─────────────────────────────────────────
    def test_rerun_makes_zero_write_calls(self):
        self.run_tool()
        before = len(self.state.datasets)
        self.state.calls.clear()
        r2 = self.run_tool()
        self.assertEqual(r2.exit_code, 0, r2.report)
        self.assertEqual(len(self.state.datasets), before, "재실행이 데이터셋을 늘렸다")
        self.assertEqual(self.state.writes(), [], "재실행이 쓰기 호출을 냈다")
        self.assertEqual(r2.write_calls, 0)
        self.assertEqual(r2.skipped, 3)

    # ── ③ 동명 건너뜀 ───────────────────────────────────────────────────────
    def test_skips_dataset_that_already_exists(self):
        self.state.datasets.append(
            {"datasetId": "D" + "0" * 25, "name": "나 데이터셋",
             "fileCount": 2, "lineageState": "원천"})
        r = self.run_tool()
        self.assertEqual(r.exit_code, 0, r.report)
        self.assertEqual(len(self.state.datasets), 3)
        self.assertEqual(sum(1 for d in self.state.datasets if d["name"] == "나 데이터셋"), 1)

    # ── ④ 부분 실패 후 재개 ─────────────────────────────────────────────────
    def test_resume_after_partial_failure_does_not_duplicate(self):
        self.state.fail_create_dataset_on = {"나 데이터셋"}
        r1 = self.run_tool()
        self.assertNotEqual(r1.exit_code, 0, "실패했는데 0 을 냈다")
        made = len(self.state.datasets)
        self.assertLess(made, 3)

        self.state.fail_create_dataset_on = set()
        r2 = self.run_tool()
        self.assertEqual(r2.exit_code, 0, r2.report)
        self.assertEqual(len(self.state.datasets), 3)
        names = [d["name"] for d in self.state.datasets]
        self.assertEqual(len(names), len(set(names)), "재개가 중복을 만들었다")

    def test_stops_at_first_failure(self):
        """R-7 — 실패하면 다음 데이터셋으로 넘어가지 않는다."""
        self.state.fail_create_dataset_on = {"가 데이터셋"}
        r = self.run_tool()
        self.assertNotEqual(r.exit_code, 0)
        self.assertEqual(len(self.state.datasets), 0)

    # ── ⑤ 순회 (R-4) ────────────────────────────────────────────────────────
    def test_follows_pagination_to_last_page(self):
        """첫 페이지만 읽으면 뒤쪽 이름을 못 보고 중복 적재한다."""
        self.state.page_size = 1
        for n in ("가 데이터셋", "나 데이터셋", "다 데이터셋"):
            self.state.datasets.append(
                {"datasetId": self.state.next_id("D"), "name": n,
                 "fileCount": {"가 데이터셋": 2, "나 데이터셋": 2, "다 데이터셋": 1}[n],
                 "lineageState": "확정" if n == "다 데이터셋" else "원천"})
        r = self.run_tool()
        self.assertEqual(r.exit_code, 0, r.report)
        self.assertEqual(len(self.state.datasets), 3, "순회가 짧아 중복 적재했다")
        self.assertEqual(r.skipped, 3)

    # ── ⑥ 중단 조건 ─────────────────────────────────────────────────────────
    def test_duplicate_name_aborts_without_writing(self):
        for _ in range(2):
            self.state.datasets.append(
                {"datasetId": self.state.next_id("D"), "name": "가 데이터셋",
                 "fileCount": 2, "lineageState": "원천"})
        self.state.calls.clear()
        r = self.run_tool()
        self.assertNotEqual(r.exit_code, 0, "멱등이 이미 깨졌는데 진행했다")
        self.assertEqual(self.state.writes(), [])

    def test_file_count_over_plan_aborts(self):
        self.state.datasets.append(
            {"datasetId": self.state.next_id("D"), "name": "가 데이터셋",
             "fileCount": 99, "lineageState": "원천"})
        r = self.run_tool()
        self.assertNotEqual(r.exit_code, 0)

    # ── ⑦ 격자 이어붙임 (상태 ㈁) ────────────────────────────────────────────
    def test_under_count_attaches_grid_only(self):
        self.state.datasets.append(
            {"datasetId": self.state.next_id("D"), "name": "나 데이터셋",
             "fileCount": 1, "lineageState": "원천"})
        r = self.run_tool()
        self.assertEqual(r.exit_code, 0, r.report)
        row = [d for d in self.state.datasets if d["name"] == "나 데이터셋"][0]
        self.assertEqual(row["fileCount"], 2, "격자를 이어 붙이지 않았다")
        self.assertEqual(sum(1 for d in self.state.datasets if d["name"] == "나 데이터셋"), 1)
        grid_calls = [c for c in self.state.calls if c[1].endswith("/grid-files")]
        self.assertEqual(len(grid_calls), 1)

    # ── ⑧ 계약 준수 ─────────────────────────────────────────────────────────
    def test_multipart_keeps_files_and_kinds_in_matching_order(self):
        """R-9 — 어긋나도 서버가 오류를 내지 않는 자리다."""
        self.run_tool()
        self.assertTrue(self.state.multipart)
        for names, kinds in self.state.multipart:
            self.assertEqual(len(names), len(kinds), "짝이 어긋났다")
        by_name = {tuple(n): tuple(k) for n, k in self.state.multipart}
        self.assertIn(("b1.nc", "g_lat.npy"), by_name)
        self.assertEqual(by_name[("b1.nc", "g_lat.npy")], ("본체", "기준 격자 파일"))

    def test_never_calls_delete(self):
        """R-6 — `deleteDataset` 은 501 이고 삭제는 도구의 동작이 아니다."""
        self.run_tool()
        self.assertEqual([c for c in self.state.calls if c[0] == "DELETE"], [])

    def test_only_contract_operations_are_called(self):
        """R-1 — 호출 op 4 건 한정."""
        self.run_tool()
        allowed = {("GET", "/api/v1/datasets"), ("POST", "/api/v1/datasets"),
                   ("POST", "/api/v1/uploads")}
        for method, path in self.state.calls:
            if path.endswith("/grid-files") and method == "POST":
                continue
            self.assertIn((method, path), allowed, f"계약 밖 호출: {method} {path}")

    def test_lineage_parent_is_resolved_to_dataset_id(self):
        self.run_tool()
        row = [d for d in self.state.datasets if d["name"] == "다 데이터셋"][0]
        self.assertEqual(row["lineageState"], "확정", "계보 부모가 실리지 않았다")

    # ── ⑨ 비밀 취급 (R-8) ───────────────────────────────────────────────────
    def test_token_is_sent_but_never_appears_in_report(self):
        r = self.run_tool()
        self.assertTrue(any("SECRET-TOKEN-VALUE" in a for a in self.state.seen_auth),
                        "토큰이 전송되지 않았다")
        self.assertNotIn("SECRET-TOKEN-VALUE", r.report)
        for line in r.log:
            self.assertNotIn("SECRET-TOKEN-VALUE", line)

    # ── ⑩ 실행 기록 (R-10) ──────────────────────────────────────────────────
    def test_report_records_decision_per_dataset(self):
        self.run_tool()
        r = self.run_tool()
        self.assertIn("나 데이터셋", r.report)
        self.assertIn("건너뜀", r.report)


if __name__ == "__main__":
    unittest.main(verbosity=2)
