"""2세대 검색 평가셋 — 실물 측정과 **기대값 도출**을 한 곳에 모은 모듈.

**이 세대가 1세대와 갈리는 지점은 하나다 — 기대값을 어디서 얻는가.**

1세대(`eval/s2b-alayer/`)의 기대값은 산문 정본을 옮긴 것이었고, 그 산문은 설명 본문이
적재되기 전에 쓰였다. 그래서 「이 낱말은 이 적재분에 없다」고 단언하는 기대가 여럿 남았고,
실물에는 그 낱말이 있었다. 건별로 기대를 고치면 같은 노후를 회차마다 다시 다투게 된다.

**2세대는 기대값을 데이터에서 계산한다.** 근거는 셋뿐이다.

- `d3_dataset_description` 의 `name` · `topic` · `summary` **실측 원문**
- `ai-service` 사전·그래프의 **실측 확장 결과**
- 릴리즈가 내세우는 검색 성질 = **낱말 접두 매칭** (형태소 분석은 폐기됐다)

⛔ **검색 결과를 보고 기대를 적지 않는다.** 그렇게 만들면 평가셋은 아무것도 검사하지 못하고
오늘의 동작을 정의상 정답으로 박는 변경 감지기가 된다. 그래서 이 모듈은 제품의 SQL·tsvector·
`ts_rank` 를 **기대 계산에 쓰지 않는다** — 순수 파이썬 낱말 나누기로 따로 센다.

**낱말 나누기 규칙(감사 가능하게 못 박는다).** 낱말 = `[0-9A-Za-z가-힣]+` 의 최대 연속.
매칭 = 어떤 낱말이 검색어로 **시작**하면 맞은 것(대소문자 무시). 낱말 **가운데**는 맞지
않는다 — 그것을 맞히려면 형태소 분석이 필요하고 그 수단은 폐기됐으므로 릴리즈가 내세우는
성질이 아니다. 하이픈 등으로 갈리는 검색어(`GK-2A`)는 두 셈법이 갈리는 자리라 **평가셋에
넣지 않는다**(`cases.json` 에 없다).
"""
from __future__ import annotations

import json
import pathlib
import re
import subprocess

REPO = pathlib.Path(__file__).resolve().parents[2]
HERE = pathlib.Path(__file__).resolve().parent
CASES = HERE / "cases.json"
EVALSET = HERE / "evalset-g2.json"
BASELINE = HERE / "baseline-g2.json"
MANIFEST = REPO / "infra" / "staging" / "manifest-s2.json"
CATALOG_PY = REPO / "services" / "core-api" / "src" / "colab_core" / "domains" / "d3_catalog.py"

DEFAULT_PG = "colab_v2_staging_pg"
DEFAULT_AI = "colab_v2_staging_ai_service"
DEFAULT_DB = "colab_platform"
DEFAULT_ROLE = "postgres"
SQL_LIMIT = 50
FIELDS = ("name", "topic", "summary")


class Unmeasurable(RuntimeError):
    """잴 수 없었다. **통과가 아니라 실패로 끝난다.**"""


# ── 낱말 접두 매칭 — 기대값 도출의 유일한 규칙 ─────────────────────────────

_WORD = re.compile(r"[0-9A-Za-z가-힣]+")


def words(text: str) -> list[str]:
    return _WORD.findall(text.lower())


def hits_for_word(data: dict[str, dict], word: str) -> dict[str, list[str]]:
    """한 낱말이 걸리는 데이터셋 → 어느 칸에서 걸렸는가. **실측 본문에서만 센다.**"""
    w = word.lower()
    if not w:
        return {}
    out: dict[str, list[str]] = {}
    for key, rec in data.items():
        fields = [f for f in FIELDS if any(x.startswith(w) for x in words(rec[f] or ""))]
        if fields:
            out[key] = fields
    return out


def loose(data: dict[str, dict], term: str) -> dict[str, list[str]]:
    """검색어의 **아무 낱말이나** 걸리는 집합 = 참 집합의 **상계**."""
    merged: dict[str, list[str]] = {}
    for w in words(term):
        for k, f in hits_for_word(data, w).items():
            merged.setdefault(k, [])
            merged[k] = sorted(set(merged[k]) | set(f))
    return merged


def strict(data: dict[str, dict], term: str) -> set[str]:
    """검색어의 **모든 낱말**이 걸리는 집합 = 참 집합의 **하계**."""
    ws = words(term)
    if not ws:
        return set()
    acc: set[str] | None = None
    for w in ws:
        s = set(hits_for_word(data, w))
        acc = s if acc is None else (acc & s)
    return acc or set()


# ── 실물 측정 ───────────────────────────────────────────────────────────────

def docker(container: str, args: list[str], stdin: str | None = None) -> str:
    cmd = ["docker", "exec"] + (["-i"] if stdin is not None else []) + [container] + args
    try:
        p = subprocess.run(cmd, input=stdin, capture_output=True, text=True, timeout=180)
    except FileNotFoundError as e:
        raise Unmeasurable(f"docker 를 못 찾았다: {e}") from e
    except subprocess.TimeoutExpired as e:
        raise Unmeasurable(f"{container} 응답 없음(180s 초과)") from e
    if p.returncode != 0:
        raise Unmeasurable(f"{container} 실행 실패(rc={p.returncode}): {p.stderr.strip()[:400]}")
    return p.stdout


def psql(container: str, db: str, role: str, sql: str) -> list[list[str]]:
    out = docker(container, ["psql", "-U", role, "-d", db, "-At", "-F", "\x1f",
                             "-v", "ON_ERROR_STOP=1", "-q", "-f", "-"], stdin=sql)
    return [line.split("\x1f") for line in out.splitlines() if line != ""]


GROUND_TRUTH_SQL = (
    "SELECT d.id, dd.name, COALESCE(dd.topic,''), COALESCE(dd.summary,''), dd.updated_at "
    "FROM d3_dataset d JOIN d3_dataset_description dd ON dd.dataset_id = d.id "
    "WHERE d.deleted_at IS NULL ORDER BY dd.name;"
)


def measure_ground_truth(pg: str, db: str, role: str) -> tuple[dict[str, dict], dict[str, str]]:
    """(D 코드 → 이름·주제·설명 실측, 데이터셋 id → D 코드).

    **이름↔D 코드 대응의 정본은 적재 매니페스트다** — 여기서 이름을 다시 적지 않는다.
    매니페스트와 실물이 어긋나면 **잰 값이 평가셋의 값이 아니므로 못 쟀다로 끝낸다.**
    """
    if not MANIFEST.is_file():
        raise Unmeasurable(f"적재 매니페스트가 없다: {MANIFEST}")
    by_name = {d["name"]: d["key"] for d in json.loads(MANIFEST.read_text(encoding="utf-8"))["datasets"]}
    rows = psql(pg, db, role, GROUND_TRUTH_SQL)
    if not rows:
        raise Unmeasurable("대상 데이터셋 0건 — 잴 것이 없다. **0건은 통과가 아니다**")
    data: dict[str, dict] = {}
    ids: dict[str, str] = {}
    unknown = []
    for dataset_id, name, topic, summary, updated_at in rows:
        key = by_name.get(name)
        if key is None:
            unknown.append(name)
            continue
        ids[dataset_id] = key
        data[key] = {"name": name, "topic": topic, "summary": summary, "updated_at": updated_at}
    missing = sorted(set(by_name.values()) - set(data))
    if missing:
        raise Unmeasurable(f"매니페스트가 적은 데이터셋이 실물에 없다: {missing}")
    if unknown:
        raise Unmeasurable(f"매니페스트에 없는 데이터셋이 실물에 있다: {unknown}")
    empty = sorted(k for k, v in data.items() if not v["summary"].strip())
    if empty:
        raise Unmeasurable(f"설명 본문이 빈 데이터셋이 있다: {empty} — 설명에서 기대를 뽑는 평가셋이 성립하지 않는다")
    return data, ids


STAGE1 = r'''
import json, sys
from colab_ai.kernel.config import Settings
from colab_ai.kernel.db import make_engine
from colab_ai.app.dictionaries import SqlDictionaries
s = Settings.from_env()
if not s.dict_db_url:
    sys.stderr.write("dict_db_url 미배선 — 사전 확장을 못 잰다\n")
    raise SystemExit(3)
d = SqlDictionaries(make_engine(s.dict_db_url))
out = {}
for it in json.loads(sys.stdin.read()):
    e = d.expand(tuple(it["terms"]), it["query"])
    out[it["id"]] = {"terms": list(e.terms), "topic": e.topic}
sys.stdout.write(json.dumps(out, ensure_ascii=False))
'''


def measure_expansion(ai: str, cases: list[dict]) -> dict[str, dict]:
    payload = json.dumps([{"id": c["id"], "terms": c["terms"], "query": c["query"]} for c in cases],
                         ensure_ascii=False)
    raw = docker(ai, ["python", "-c", STAGE1], stdin=payload)
    try:
        got = json.loads(raw)
    except json.JSONDecodeError as e:
        raise Unmeasurable(f"사전 확장 산출이 JSON 이 아니다: {raw[:200]!r}") from e
    if set(got) != {c["id"] for c in cases}:
        raise Unmeasurable("사전 확장이 일부 질의를 안 냈다 — 건너뛴 채 진행하지 않는다")
    return got


# ── 기대값 도출 ─────────────────────────────────────────────────────────────

def derive_case(case: dict, data: dict[str, dict], expansion: list[str]) -> dict:
    """한 건의 기대와 **그 기대가 왜 그것인가**(도출 근거)를 함께 만든다.

    도출 근거에는 **어느 데이터셋의 어느 칸에 그 낱말이 있었는가**가 들어간다. 사람이 원문을
    열어 대조할 수 있어야 감사 가능한 기대다.
    """
    kind = case["kind"]
    if kind == "out_of_scope":
        return {"kind": kind, "expected": None,
                "derivation": {"규칙": "기대값을 도출하지 않는다", "사유": case["사유"],
                               "이월_출처": case["이월_출처"]}}

    per_term = {t: {"상계": loose(data, t), "하계": sorted(strict(data, t))} for t in expansion}

    if kind == "derived_exact":
        if len(expansion) != 1:
            raise Unmeasurable(
                f"{case['id']}: 확장 뒤 검색어가 {len(expansion)}개다 — derived_exact 는 1개일 때만 성립한다. "
                "사전이 움직였다는 뜻이므로 cases.json 의 kind 를 다시 정해야 한다")
        term = expansion[0]
        matched = hits_for_word(data, term)
        return {
            "kind": kind, "expected": sorted(matched),
            "derivation": {
                "규칙": "이름·주제·설명의 낱말 중 검색어로 시작하는 것이 하나라도 있으면 기대에 든다(대소문자 무시)",
                "검색어": term,
                "걸리는_근거": {k: {"칸": v, "발췌": _excerpt(data[k], v, term)} for k, v in sorted(matched.items())},
                "안_걸리는_이유": {k: "이름·주제·설명 어느 낱말도 이 검색어로 시작하지 않는다"
                                  for k in sorted(set(data) - set(matched))},
            },
        }

    if kind == "derived_bounds":
        upper = sorted(set().union(*[set(v["상계"]) for v in per_term.values()]) if per_term else set())
        lower = sorted(set.intersection(*[set(v["하계"]) for v in per_term.values()]) if per_term else set())
        return {
            "kind": kind, "expected": {"하계": lower, "상계": upper},
            "derivation": {
                "규칙": "검색어 결합 규칙(OR/AND)이 정본에서 유보돼 있다. 어느 쪽이든 성립하는 경계만 기대로 삼는다 — "
                        "결과는 각 검색어 매칭의 **교집합 이상, 합집합 이하**여야 한다. 이 평가셋은 결합 규칙을 정하지 않는다.",
                "검색어별": {t: {"상계": sorted(v["상계"]), "하계": v["하계"]} for t, v in per_term.items()},
            },
        }

    if kind == "derived_field_order":
        term = expansion[0] if len(expansion) == 1 else None
        if term is None:
            raise Unmeasurable(f"{case['id']}: 순위 비교는 검색어 1개일 때만 도출한다")
        matched = hits_for_word(data, term)
        by_name = sorted(k for k, f in matched.items() if "name" in f)
        by_body = sorted(k for k, f in matched.items() if "name" not in f)
        if not by_name or not by_body:
            raise Unmeasurable(
                f"{case['id']}: 이름 매칭 {by_name} · 본문만 매칭 {by_body} — 한쪽이 비어 순위 비교가 성립하지 않는다")
        return {
            "kind": kind, "expected": {"앞": by_name, "뒤": by_body},
            "derivation": {
                "규칙": "색인 가중치가 이름 A · 주제 B · 설명 C 로 선언돼 있다(생성 컬럼 search_vector). "
                        "따라서 이름에 낱말이 있는 데이터셋이 설명에만 있는 데이터셋보다 앞선다.",
                "검색어": term,
                "이름에_있음": {k: _excerpt(data[k], ["name"], term) for k in by_name},
                "본문에만_있음": {k: _excerpt(data[k], matched[k], term) for k in by_body},
            },
        }

    raise Unmeasurable(f"모르는 기대 갈래: {kind}")


def _excerpt(rec: dict, fields: list[str], term: str) -> dict[str, str]:
    """기대의 근거가 된 **원문 조각**. 사람이 대조할 수 있어야 감사 가능하다."""
    out = {}
    t = term.lower()
    for f in fields:
        text = rec[f] or ""
        for m in _WORD.finditer(text):
            if m.group(0).lower().startswith(t):
                lo, hi = max(0, m.start() - 25), min(len(text), m.end() + 25)
                out[f] = ("…" if lo else "") + text[lo:hi] + ("…" if hi < len(text) else "")
                break
    return out


def build_evalset(cases_doc: dict, data: dict[str, dict], expansions: dict[str, dict]) -> dict:
    items = []
    for case in cases_doc["cases"]:
        exp = expansions[case["id"]]["terms"]
        rec = {"id": case["id"], "query": case["query"], "terms": case["terms"],
               "expansion": exp, "확인하려는_것": case.get("확인하려는_것", case.get("사유"))}
        rec.update(derive_case(case, data, exp))
        items.append(rec)
    return {
        "_설명": [
            "⚠ 손으로 고치지 않는다. `python3 eval/s2b-alayer-g2/derive.py --write` 가 실물에서 다시 만든다.",
            "기대값의 출처는 **적재된 이름·주제·설명 원문과 사전 확장 실측**뿐이다. 검색 결과는 기대 계산에 쓰이지 않는다.",
        ],
        "ground_truth": {
            "대상_데이터셋": len(data),
            "최신_설명_갱신시각": max(v["updated_at"] for v in data.values()),
            "출처": "colab_v2_staging_pg · colab_platform · d3_dataset_description (읽기 전용 SELECT)",
            "칸별_길이": {k: {"이름": len(v["name"]), "주제": len(v["topic"]), "설명": len(v["summary"])}
                          for k, v in sorted(data.items())},
        },
        "items": items,
    }
