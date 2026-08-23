#!/usr/bin/env python3
"""seam-consistency 게이트 엔진 (WU-D2c §2-13 · 〈61〉-㉠·㉡).

contract-lint 는 seams 만, event-lint 는 events 만 본다 — 이 게이트가 그 **사이**를 본다.
DR-7 은 게이트를 통과해서가 아니라 게이트가 없어서 살아남았다 (D2c.md §2-13).

검사 4종 (--check 로 하나만도 돌 수 있다):
  ge        G-e 산문 위임 참조 검증 — 계약 산문 속 seam 파일명·op 이름·이벤트 타입·
            「X seam」 위임 문구가 **실재하는 대상**을 가리키는지.
  gb        G-b `const` 능력 주장 검증 — 이벤트의 `source: {const: X}` 마다 X 의 HTTP seam 에
            그 이벤트를 촉발하는 op 이 실재하고 그 op 이 집계 루트 ID 를 다루는지.
  citation  〈61〉-㉠ 정본 근거 대조 — 기준선(git HEAD 또는 디렉터리) 대비 **신설된**
            op·스키마·파라미터 전수에 정본 인용 또는 `[정본 무근거]`/`[사용자 승인]` 표기가
            있는지. 근거 칸 공란 1건이라도 red. **근거의 내용이 옳은지는 판정하지 않는다.**
  flow      〈61〉-㉡ 흐름 완주 검사 — 사람 고정 fixture(E-04 단계표)의 각 단계에
            호출 가능한 op/이벤트가 실재하고, 식별자 종류가 단계 사이에 이어지며,
            이벤트의 source 촉발점이 HTTP 입구로 실재하는지. 끊긴 자리를 목록으로 낸다.
            **G-e 와 축이 다르다 — 섞지 않는다** (D2c.md §7-7).

원칙 (CLAUDE.md §4): 도구 부재·대상 0건·fixture 부재는 전부 red. skip 없음.

환경변수 (selftest 전용 — 평시엔 건드리지 않는다)
  COLAB_SC_SEAM_DIR     seam 디렉터리 (기본 contracts/seams)
  COLAB_SC_EVENTS_DIR   이벤트 디렉터리 (기본 contracts/events)
  COLAB_SC_BASELINE     ㉠ 기준선 — "git:HEAD"(기본) 또는 seam 사본 디렉터리 경로
  COLAB_SC_FLOW_FIXTURE ㉡ fixture (기본 gates/fixtures/seam-consistency/e04-flow.json)
  COLAB_SC_ALLOWLIST    allow-list (기본 gates/config/seam-consistency-allowlist.toml)
                        — selftest fixture 는 자기 allow-list 를 들고 다닌다 (WU-D3b 와 같은 이유)
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

try:
    import yaml
except ImportError:  # 도구 부재는 red 다 — 검사를 못 한 것은 통과가 아니다.
    print("::error::seam-consistency red — pyyaml 이 없다. 검사를 못 한 것은 통과가 아니다.")
    sys.exit(1)

try:
    import tomllib
except ImportError:
    print("::error::seam-consistency red — python 3.11+ (tomllib) 이 필요하다.")
    sys.exit(1)

ERRORS: list[str] = []


def err(check: str, msg: str) -> None:
    ERRORS.append(f"[{check}] {msg}")


def env_path(name: str, default: Path) -> Path:
    v = os.environ.get(name)
    return Path(v) if v else default


# ── 레지스트리 — seam·이벤트 계약을 한 번 읽는다 ───────────────────────────────

class Registry:
    def __init__(self, seam_dir: Path, events_dir: Path):
        self.seam_dir = seam_dir
        self.events_dir = events_dir
        self.seams: dict[str, dict] = {}          # 파일명 → 파싱 트리
        self.seam_texts: dict[str, str] = {}      # 파일명 → 원문
        self.ops: dict[str, set[str]] = {}        # 파일명 → operationId 집합
        self.all_ops: set[str] = set()
        self.events: dict[str, dict] = {}         # 파일명 → 파싱 트리
        self.event_types: set[str] = set()
        self.source_consts: list[tuple[str, str, str]] = []  # (이벤트파일, 이벤트타입, source)

        for p in sorted(seam_dir.glob("*.y*ml")):
            text = p.read_text(encoding="utf-8")
            try:
                doc = yaml.safe_load(text)
            except yaml.YAMLError as e:
                err("registry", f"{p.name} 파싱 실패: {e}")
                continue
            self.seams[p.name] = doc or {}
            self.seam_texts[p.name] = text
            ids = set()
            for path_item in (doc or {}).get("paths", {}).values():
                if not isinstance(path_item, dict):
                    continue
                for v in path_item.values():
                    if isinstance(v, dict) and "operationId" in v:
                        ids.add(v["operationId"])
            self.ops[p.name] = ids
            self.all_ops |= ids

        for p in sorted(events_dir.glob("*.json")):
            try:
                doc = json.loads(p.read_text(encoding="utf-8"))
            except json.JSONDecodeError as e:
                err("registry", f"{p.name} 파싱 실패: {e}")
                continue
            self.events[p.name] = doc
            for name, d in doc.get("$defs", {}).items():
                if not isinstance(d, dict):
                    continue
                if name == "EventType" and isinstance(d.get("enum"), list):
                    self.event_types |= set(d["enum"])
                props = d.get("properties", {})
                if isinstance(props, dict):
                    t = props.get("type", {})
                    s = props.get("source", {})
                    if isinstance(t, dict) and isinstance(s, dict) \
                            and "const" in t and "const" in s:
                        self.source_consts.append((p.name, t["const"], s["const"]))

        if not self.seams:
            err("registry", f"seam 계약이 0건이다 ({seam_dir}). 대상 0건은 green-by-skip 이다.")
        if not self.events:
            err("registry", f"이벤트 계약이 0건이다 ({events_dir}).")

    def op_block(self, seam_file: str, op_id: str, depth: int = 3) -> str:
        """op 의 YAML 블록 + 같은 파일 components $ref 를 depth 단계까지 이어붙인 원문."""
        text = self.seam_texts.get(seam_file, "")
        block = self._extract_op(text.splitlines(), op_id)
        seen: set[tuple[str, str]] = set()
        frontier = block
        ref_re = re.compile(r"(?:([\w.-]+\.ya?ml))?#/components/(?:schemas|parameters|responses)/(\w+)")
        for _ in range(depth):
            refs = {(m.group(1) or seam_file, m.group(2))
                    for m in ref_re.finditer(frontier)} - seen
            if not refs:
                break
            seen |= refs
            frontier = "".join(
                self._extract_component(self.seam_texts.get(f, "").splitlines(), name)
                for f, name in refs)
            block += frontier
        return block

    @staticmethod
    def _extract_op(lines: list[str], op_id: str) -> str:
        for i, ln in enumerate(lines):
            if re.search(rf"^\s*operationId:\s*{re.escape(op_id)}\s*$", ln):
                # 경로 키 줄(예: '  /uploads:')까지 거슬러 올라간다 — path 레벨 parameters 를 포함하기 위해서다
                j = i
                while j > 0 and not re.match(r"^\s{2}/\S*:", lines[j]):
                    j -= 1
                indent = len(lines[j]) - len(lines[j].lstrip())
                k = j + 1
                while k < len(lines):
                    ln2 = lines[k]
                    if ln2.strip() and (len(ln2) - len(ln2.lstrip())) <= indent:
                        break
                    k += 1
                return "\n".join(lines[j:k]) + "\n"
        return ""

    @staticmethod
    def _extract_component(lines: list[str], name: str) -> str:
        for i, ln in enumerate(lines):
            if re.match(rf"^    {re.escape(name)}:\s*$", ln):
                k = i + 1
                while k < len(lines):
                    ln2 = lines[k]
                    if ln2.strip() and (len(ln2) - len(ln2.lstrip())) <= 4:
                        break
                    k += 1
                return "\n".join(lines[i:k]) + "\n"
        return ""


def walk_strings(node):
    if isinstance(node, dict):
        for k, v in node.items():
            if isinstance(k, str):
                yield k
            yield from walk_strings(v)
    elif isinstance(node, list):
        for v in node:
            yield from walk_strings(v)
    elif isinstance(node, str):
        yield node


# ── G-e 산문 위임 참조 검증 ───────────────────────────────────────────────────

OP_VERB = re.compile(
    r"^(create|get|list|update|delete|add|replace|remove|link|unlink|save|approve|"
    r"reject|request|cancel|confirm|set|download)[A-Z][A-Za-z0-9]*$")
FILE_REF = re.compile(r"[\w./-]*?([\w-]+\.(?:yaml|yml|json))")
BACKTICK = re.compile(r"`([^`\n]+)`")
EVENT_TOKEN = re.compile(r"^[a-z][a-z-]*\.[a-z][a-z-]*$")
# 「X seam」 위임 문구 — 합성어(이벤트/업로드)거나 백틱 이름일 때만 후보로 삼는다.
SEAM_PHRASE = re.compile(r"(`[^`\s]+`|[\w가-힣-]+(?:[/·][\w가-힣-]+)+)\s*seam")


def check_ge(reg: Registry, allow: dict) -> int:
    aliases = set(allow.get("ge", {}).get("seam-aliases", []))
    aliases |= {Path(f).stem for f in reg.seams} | {Path(f).stem for f in reg.events}
    known_files = {f for f in reg.seams} | {f for f in reg.events}
    for schemas_dir in {reg.seam_dir.parent / "schemas", reg.events_dir.parent / "schemas"}:
        if schemas_dir.is_dir():
            known_files |= {p.name for p in schemas_dir.glob("*.json")}
    checked = 0
    reported: set[tuple[str, str]] = set()  # 같은 (파일, 대상) 은 한 번만 적는다

    def scan(origin: str, s: str):
        nonlocal checked
        # ① 파일명 참조 — 실재 파일이어야 한다
        for m in FILE_REF.finditer(s):
            base = m.group(1)
            checked += 1
            if base not in known_files and (origin, base) not in reported:
                reported.add((origin, base))
                err("G-e", f"{origin}: 산문이 실재하지 않는 계약 파일을 가리킨다 — `{base}`")
        # ② 백틱 토큰 — op 이름·이벤트 타입
        for m in BACKTICK.finditer(s):
            tok = m.group(1).strip()
            if tok.endswith((".yaml", ".yml", ".json")) or "#" in tok or " " in tok:
                continue
            head = tok.split(".")[0]
            if OP_VERB.match(head):
                checked += 1
                if head not in reg.all_ops:
                    err("G-e", f"{origin}: 산문이 실재하지 않는 op 을 가리킨다 — `{head}`")
            elif EVENT_TOKEN.match(tok):
                # 속성 경로(`delivery.attempt`)와 구분한다 — 실제 EventType 접두(upload·file·preview…)
                # 로 시작하는 점 표기만 이벤트 참조로 센다.
                prefixes = {t.split(".")[0] for t in reg.event_types}
                if tok in reg.event_types:
                    checked += 1
                elif tok.split(".")[0] in prefixes:
                    checked += 1
                    err("G-e", f"{origin}: 산문이 실재하지 않는 이벤트 타입을 가리킨다 — `{tok}`")
        # ③ 「X seam」 위임 문구 — X 의 각 성분이 등록된 seam 별칭이어야 한다
        for m in SEAM_PHRASE.finditer(s):
            phrase = m.group(1).strip("`")
            for part in re.split(r"[/·]", phrase):
                part = part.strip()
                if not part:
                    continue
                checked += 1
                if part not in aliases:
                    err("G-e", f"{origin}: 「{phrase} seam」 위임 — `{part}` 은 등록된 seam 이 아니다. "
                               f"받을 수 없는 곳에 위임한 산문이다 (DR-7 · SEAM-AUDIT I-02)")

    for fname, doc in reg.seams.items():
        for s in walk_strings(doc):
            scan(fname, s)
    for fname, doc in reg.events.items():
        for s in walk_strings(doc):
            scan(fname, s)
    return checked


# ── G-b `const` 능력 주장 검증 ────────────────────────────────────────────────

def check_gb(reg: Registry, allow: dict) -> int:
    gb = allow.get("gb", {})
    http_sources: dict = gb.get("http-sources", {})
    internal: dict = gb.get("internal-sources", {})
    root_id = gb.get("aggregate-root", "uploadId")
    checked = 0
    if not reg.source_consts:
        err("G-b", "source const 를 가진 이벤트가 0건이다 — 대상 0건은 green-by-skip 이다.")
    for ev_file, ev_type, source in reg.source_consts:
        checked += 1
        if source in internal:
            continue  # 이유가 allow-list 에 적혀 있다 (HTTP 표면이 없는 배포 단위)
        seam_file = http_sources.get(source)
        if not seam_file:
            err("G-b", f"{ev_file}: `{ev_type}` 의 source `{source}` 가 allow-list 의 "
                       f"http-sources 에도 internal-sources 에도 없다 — 능력 주장의 주인이 미상이다.")
            continue
        if seam_file not in reg.seams:
            err("G-b", f"{ev_file}: source `{source}` 의 seam 파일이 없다 — {seam_file}")
            continue
        # 촉발 op — 그 seam 안에서 이벤트 타입을 명시적으로 거는 op 을 찾는다
        triggers = [op for op in reg.ops[seam_file]
                    if ev_type in reg.op_block(seam_file, op)]
        if not triggers:
            err("G-b", f"{ev_file}: `{ev_type}` 은 source 가 `{source}` const 인데 "
                       f"{seam_file} 에 그 이벤트를 촉발한다고 말하는 op 이 0건이다 "
                       f"(SEAM-AUDIT I-01·I-05 — 능력 주장만 있고 입구가 없다).")
            continue
        if not any(root_id in reg.op_block(seam_file, op) for op in triggers):
            err("G-b", f"{ev_file}: `{ev_type}` 의 촉발 op {triggers} 가 집계 루트 "
                       f"`{root_id}` 를 다루지 않는다.")
    return checked


# ── 〈61〉-㉠ 정본 근거 대조 ──────────────────────────────────────────────────

CITATION = re.compile(
    r"〈\d+〉|§|Policy|PRD|DataModel|DATAMODEL|SEAM-AUDIT|DOMAINS|CLAUDE\.md|"
    r"sessions/|PLAN-SoT|정본 무근거|사용자 승인|"
    # 계약 정본 인용 — 〈54〉 가 이벤트 seam 을 정본으로 확정했으므로 계약 상호 인용도 근거다
    r"envelope\.json|core-pipeline\.json|core-viz\.yaml|core-ai\.yaml|common\.json")


def load_baseline(reg: Registry) -> Registry | None:
    spec = os.environ.get("COLAB_SC_BASELINE", "git:HEAD")
    if spec.startswith("git:"):
        ref = spec[4:]
        import tempfile
        tmp = Path(tempfile.mkdtemp(prefix="sc-baseline-"))
        (tmp / "seams").mkdir()
        (tmp / "events").mkdir()
        for fname in list(reg.seams) or []:
            rel = (reg.seam_dir / fname).resolve().relative_to(REPO_ROOT)
            r = subprocess.run(["git", "-C", str(REPO_ROOT), "show", f"{ref}:{rel.as_posix()}"],
                               capture_output=True, text=True)
            if r.returncode == 0:
                (tmp / "seams" / fname).write_text(r.stdout, encoding="utf-8")
            # 기준선에 없던 파일 = 파일째 신설. 빈 기준선으로 취급한다.
        for fname in list(reg.events):
            rel = (reg.events_dir / fname).resolve().relative_to(REPO_ROOT)
            r = subprocess.run(["git", "-C", str(REPO_ROOT), "show", f"{ref}:{rel.as_posix()}"],
                               capture_output=True, text=True)
            if r.returncode == 0:
                (tmp / "events" / fname).write_text(r.stdout, encoding="utf-8")
        return Registry(tmp / "seams", tmp / "events")
    base_dir = Path(spec)
    if not base_dir.is_dir():
        err("㉠", f"기준선 디렉터리가 없다: {base_dir}. 기준선 없는 근거 대조는 검사가 아니다.")
        return None
    ev = base_dir / "events" if (base_dir / "events").is_dir() else reg.events_dir
    seams = base_dir / "seams" if (base_dir / "seams").is_dir() else base_dir
    return Registry(seams, ev)


def op_node(doc: dict, op_id: str) -> dict:
    for path_item in doc.get("paths", {}).values():
        if isinstance(path_item, dict):
            for v in path_item.values():
                if isinstance(v, dict) and v.get("operationId") == op_id:
                    return v
    return {}


def check_citation(reg: Registry, allow: dict) -> int:
    base = load_baseline(reg)
    if base is None:
        return 0
    checked = 0
    for fname, doc in reg.seams.items():
        base_ops = base.ops.get(fname, set())
        new_ops = sorted(reg.ops[fname] - base_ops)
        comp = doc.get("components", {}) or {}
        base_doc = base.seams.get(fname, {}) or {}
        base_comp = base_doc.get("components", {}) or {}
        for op in new_ops:
            checked += 1
            node = op_node(doc, op)
            desc = str(node.get("description", "") or "")
            if not desc.strip():
                err("㉠", f"{fname}: 신설 op `{op}` 의 근거 칸이 공란이다 (description 없음). "
                          f"근거 없이 들어오는 op 은 red 다 (㉠-1).")
            elif not CITATION.search(desc):
                err("㉠", f"{fname}: 신설 op `{op}` 의 description 에 정본 인용도 "
                          f"`[정본 무근거]`/`[사용자 승인]` 표기도 없다 (㉠-1).")
        for section in ("schemas", "parameters"):
            cur = comp.get(section, {}) or {}
            old = (base_comp.get(section, {}) or {})
            for name in sorted(set(cur) - set(old)):
                checked += 1
                node = cur.get(name) or {}
                sdesc = str(node.get("description", "") or "")
                if not CITATION.search(sdesc):
                    # 스키마 자체 근거가 없으면, 필드 전수가 각자 근거를 들어야 한다
                    props = node.get("properties", {}) or {}
                    field_ok = props and all(
                        CITATION.search(str((p or {}).get("description", "") or ""))
                        for p in props.values())
                    if not field_ok:
                        err("㉠", f"{fname}: 신설 {section[:-1]} `{name}` 의 근거 칸이 "
                                  f"공란이다 (㉠-2) — 스키마에도 필드에도 인용·표기가 없다.")
                else:
                    for pname, p in (node.get("properties", {}) or {}).items():
                        checked += 1
                        pdesc = str((p or {}).get("description", "") or "")
                        # 필드는 자기 인용 또는 스키마 인용을 승계한다 — 둘 다 없으면 red
                        if pdesc.strip() and not CITATION.search(pdesc) \
                                and not CITATION.search(sdesc):
                            err("㉠", f"{fname}: 신설 필드 `{name}.{pname}` 근거 공란 (㉠-2)")
    print(f"# ㉠ — 기준선 대비 신설 검사 대상 {checked}건 "
          f"(신설 0건이면 대조할 것이 없어 green 이다 — 기준선이 곧 현재라는 뜻)")
    return checked


# ── 〈61〉-㉡ 흐름 완주 검사 ──────────────────────────────────────────────────

def check_flow(reg: Registry, allow: dict) -> int:
    fixture = env_path("COLAB_SC_FLOW_FIXTURE",
                       REPO_ROOT / "gates/fixtures/seam-consistency/e04-flow.json")
    if not fixture.is_file():
        err("㉡", f"흐름 fixture 가 없다: {fixture}. 사람 고정 픽스처 없이 ㉡ 은 돌 수 없다 "
                  f"(E04-step-op-map — 기계는 단계 분해를 못 한다).")
        return 0
    try:
        flow = json.loads(fixture.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        err("㉡", f"흐름 fixture 파싱 실패: {e}")
        return 0
    steps = flow.get("steps", [])
    if not steps:
        err("㉡", "흐름 fixture 의 단계가 0건이다.")
        return 0

    broken: list[str] = []
    deferred: list[str] = []
    produced: set[str] = set()
    gb = allow.get("gb", {})
    http_sources: dict = gb.get("http-sources", {})

    for st in steps:
        sid, name = st.get("step", "?"), st.get("name", "?")
        label = f"단계 {sid}({name})"
        if st.get("deferred"):
            deferred.append(f"{label} — 의도적 이월: {st['deferred']}")
            continue
        kind = st.get("kind")
        ids = st.get("ids", [])
        blocks = ""
        # ㉡-1 호출 가능한 op/이벤트 실재
        if kind == "op":
            seam = st.get("seam", "fe-core.yaml")
            for op in ids:
                if op not in reg.ops.get(seam, set()):
                    broken.append(f"{label}: op `{op}` 이 {seam} 에 없다 (㉡-1)")
                else:
                    blocks += reg.op_block(seam, op)
        elif kind == "event":
            for ev in ids:
                if ev not in reg.event_types:
                    broken.append(f"{label}: 이벤트 `{ev}` 가 EventType enum 에 없다 (㉡-1)")
                else:
                    blocks += "".join(json.dumps(d, ensure_ascii=False)
                                      for d in reg.events.values())
            # ㉡-3 source 촉발점이 HTTP 입구로 실재하는가 (DR-7 재발 방지)
            src = st.get("source_const")
            if src and src in http_sources:
                seam_file = http_sources[src]
                trig = [op for op in reg.ops.get(seam_file, set())
                        if any(ev in reg.op_block(seam_file, op) for ev in ids)]
                if not trig:
                    broken.append(f"{label}: source `{src}` const 인데 {seam_file} 에 "
                                  f"촉발 op 이 0건 (㉡-3 — DR-7 의 모양 그대로)")
        else:
            broken.append(f"{label}: kind 미상 `{kind}` — fixture 오류")
            continue
        # ㉡-2 식별자 종류 연결 — 앞 단계가 생산한 종류만 입력으로 요구할 수 있다
        for need in st.get("inputs", []):
            if need in st.get("external_inputs", {}):
                continue  # 흐름 밖에서 오는 식별자 — fixture 가 이유를 적었다
            if need not in produced:
                broken.append(f"{label}: 입력 `{need}` 를 어느 앞 단계도 생산하지 않았다 (㉡-2)")
            if blocks and need not in blocks:
                broken.append(f"{label}: fixture 는 입력 `{need}` 라는데 계약 op 블록에 "
                              f"그 식별자가 없다 (㉡-2 — fixture↔계약 드리프트)")
        for out in st.get("outputs", []):
            if blocks and out not in blocks:
                broken.append(f"{label}: fixture 는 출력 `{out}` 이라는데 계약에 없다 (㉡-2)")
            produced.add(out)

    print(f"# ㉡ — 단계 {len(steps)}건 재생 (이월 {len(deferred)}건)")
    for d in deferred:
        print(f"#   ↩ {d}")
    if broken:
        print("# ㉡ 끊긴 자리 목록 (㉡-4):")
        for b in broken:
            print(f"#   ✗ {b}")
            err("㉡", b)
    else:
        print("# ㉡ 끊긴 자리: 없음 (㉡-4)")
    return len(steps)


# ── 진입 ─────────────────────────────────────────────────────────────────────

def main() -> int:
    which = "all"
    args = sys.argv[1:]
    if args and args[0] == "--check":
        which = args[1]
    seam_dir = env_path("COLAB_SC_SEAM_DIR", REPO_ROOT / "contracts/seams")
    events_dir = env_path("COLAB_SC_EVENTS_DIR", REPO_ROOT / "contracts/events")
    allow_path = env_path("COLAB_SC_ALLOWLIST",
                          REPO_ROOT / "gates/config/seam-consistency-allowlist.toml")
    if not allow_path.is_file():
        print(f"::error::seam-consistency red — allow-list 가 없다: {allow_path}")
        return 1
    allow = tomllib.loads(allow_path.read_text(encoding="utf-8"))

    reg = Registry(seam_dir, events_dir)
    counts = {}
    if which in ("all", "ge"):
        counts["G-e"] = check_ge(reg, allow)
    if which in ("all", "gb"):
        counts["G-b"] = check_gb(reg, allow)
    if which in ("all", "citation"):
        counts["㉠"] = check_citation(reg, allow)
    if which in ("all", "flow"):
        counts["㉡"] = check_flow(reg, allow)
    if not counts:
        print(f"::error::seam-consistency red — 알 수 없는 검사 '{which}'")
        return 2

    if ERRORS:
        for e in ERRORS:
            print(f"::error::seam-consistency red — {e}")
        return 1
    summary = " · ".join(f"{k} {v}건" for k, v in counts.items())
    print(f"seam-consistency green — {summary}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
