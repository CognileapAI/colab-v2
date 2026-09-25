"""K3 `WU-S1a` — 업로드와 후보의 **축 대조 비교기**. 순수 함수만이고 DB 에 닿지 않는다.

왜 한 벌인가 — 신호를 **계산하는 쪽**(`WU-S1b` 적격·순위 · `WU-S5` 규칙 팔)과 모델의 인용을
**검증하는 쪽**(`WU-S2`)이 다른 함수를 쓰면, 「인용 오류 0건」이 참인 이유가 「모델이 맞혔다」가
아니라 「두 함수가 서로 다른 것을 봤다」가 된다. 그래서 계산과 검증은 **같은 함수**다
(`dev-package/prd/rounds/R-K3-STRUCTURE.md` 「의존 그래프」).

축은 **다섯뿐**이다(intent `2026-09-24-k3-abstention-by-structure.md` Q3a) —
기간 겹침 · CRS 정규화 동등 · 격자 정규화 동등 · 변수 교집합 ≥1 · 파일명 토큰 접두.
정본 없는 축은 만들지 않는다. 계약의 `evidence.field` enum 과 **같은 문자열**을 쓴다
(`contracts/seams/core-ai.yaml` `ParentCandidateSuggestion.evidence`).

두 규율을 접지 않는다.
  ① **한쪽 값이 없으면 「안 맞았다」가 아니라 근거가 없다.** 비교 결과에 그 축의 항목 자체가
     서지 않는다 — 미지와 불일치를 한 칸에 접으면 확신도 파생이 거짓말을 한다.
  ② **여기서 판정하지 않는다.** 폐기·확신도 부여·응답 조립은 부르는 쪽(`WU-S2`)의 일이다.
"""
from __future__ import annotations

import dataclasses
import re
from datetime import date, datetime, timezone
from typing import Any, Literal, Mapping, Sequence

EvidenceField = Literal["period", "crs", "grid", "variables", "fileName"]
#: 계약 enum 과 같은 순서·같은 문자열. 근거 한 줄의 **나열 순서**도 이 순서다(결정적).
EVIDENCE_FIELDS: tuple[EvidenceField, ...] = ("period", "crs", "grid", "variables", "fileName")
#: 계약 `evidence.*Value` 의 maxLength. 넘는 값은 자른다 — 계약 밖 길이를 만들지 않는다.
MAX_VALUE_LEN = 200
#: `AiRationale` 은 화면에서 한 줄로 선다(`contracts/schemas/common.json`). 상한을 여기서 건다.
MAX_RATIONALE_LEN = 120
_MAX_RATIONALE_VALUE = 40
#: `AiConfidence` 3값 중 **파생으로 나올 수 있는 둘**. 「모름」은 나오지 않는다 —
#: 그 자리는 빈 제안이다(`R-K3-STRUCTURE.md` WU-S0 ⓒ).
CONFIDENCE_SURE = "확실"
CONFIDENCE_VAGUE = "애매"

_WS = re.compile(r"\s+")
#: **좁은 정규화다.** 공백·대소문자를 접고, `EPSG` 뒤의 구분자(`:`·공백·`_`·`-`)만 `:` 로 모은다.
#: WKT 해석·datum 조회·축 순서 판정은 **하지 않는다** — 그것은 geo 라이브러리의 일이고
#: core-api 는 geo 라이브러리를 import 하지 않는다(`AGENTS.md` 경계).
_EPSG = re.compile(r"^epsg[\s:_-]*(\d+)$")
#: 토큰 규칙은 `d3_catalog.lineage_candidate_tokens`(`d3_catalog.py:356-409`)의 것과 **같다**.
#: 그 함수는 `datasetNameDraft` 까지 섞어 후보 **선정**에 쓰는 값이라 이 축(파일명)에 그대로
#: 쓸 수 없고, `d3_catalog` 를 import 하면 `WU-S1b` 가 이 모듈을 부르는 순간 순환이 된다.
#: 그래서 **파일명만 보는 좁은 사본**을 두고 출처를 여기 적는다(후속: 공통 자리로 올린다).
_TOKEN_BOUNDARY = re.compile(r"[^0-9A-Za-z가-힣]+")
_LATIN_TOKEN = re.compile(r"^[0-9a-z]+$")


# ─────────────────────────── 값 ───────────────────────────
@dataclasses.dataclass(frozen=True)
class _Axes:
    """대조에 쓰는 여섯 값. 기간은 ISO 8601 문자열(계약 `Timestamp`)이거나 `datetime` 이다."""

    file_name: str | None = None
    crs: str | None = None
    grid: str | None = None
    variables: tuple[str, ...] = ()
    period_start: Any = None
    period_end: Any = None


@dataclasses.dataclass(frozen=True)
class UploadAxes(_Axes):
    @classmethod
    def from_file_meta(cls, meta: Mapping[str, Any]) -> "UploadAxes":
        """계약 `UploadedFileMeta` 모양에서 축만 뽑는다(`routes/ingestion.py:497-534` 가 조립한 그 값).

        **없는 열쇠를 지어내지 않는다** — 없으면 `None` 이고, `None` 인 축은 근거가 되지 않는다.
        """
        raw = meta.get("variables") or ()
        return cls(file_name=meta.get("fileName"), crs=meta.get("crs"),
                   grid=meta.get("gridDescription"),
                   variables=tuple(v for v in raw if isinstance(v, str) and v),
                   period_start=meta.get("periodStart"), period_end=meta.get("periodEnd"))


@dataclasses.dataclass(frozen=True)
class CandidateAxes(_Axes):
    #: 후보 데이터셋 ID. 비교에는 쓰이지 않고 **부르는 쪽이 짝을 잃지 않게** 들고 다닌다.
    dataset_id: str = ""

    @classmethod
    def from_autometa(cls, dataset_id: str, row: Mapping[str, Any]) -> "CandidateAxes":
        """`d3_dataset_autometa` 한 행(`db/platform/schema.sql:557-568`)에서 축만 뽑는다.

        열 이름 그대로 읽는다 — 묶음 이름은 `bundle_file_name`(조각 이름이 아니다 · §4.3).
        """
        raw = row.get("variables") or ()
        return cls(dataset_id=dataset_id, file_name=row.get("bundle_file_name"),
                   crs=row.get("crs"), grid=row.get("grid"),
                   variables=tuple(v for v in raw if isinstance(v, str) and v),
                   period_start=row.get("period_start"), period_end=row.get("period_end"))


@dataclasses.dataclass(frozen=True)
class Evidence:
    """근거 한 건 = 계약 `evidence` 항목과 같은 세 칸. **주장이 아니라 대조 결과다.**"""

    field: EvidenceField
    upload_value: str
    candidate_value: str

    def to_dict(self) -> dict[str, str]:
        return {"field": self.field, "uploadValue": self.upload_value,
                "candidateValue": self.candidate_value}

    @classmethod
    def from_claim(cls, claim: Any) -> "Evidence | None":
        """모델이 **인용한** 한 건을 값으로 바꾼다. 규격을 어기면 `None` — 그 항목만 버린다."""
        if not isinstance(claim, Mapping):
            return None
        field = claim.get("field")
        up, cand = claim.get("uploadValue"), claim.get("candidateValue")
        if field not in EVIDENCE_FIELDS or not isinstance(up, str) or not isinstance(cand, str):
            return None
        if not up.strip() or not cand.strip():
            return None
        return cls(field, _clip(up), _clip(cand))


# ─────────────────────────── 정규화 ───────────────────────────
def _text(value: Any) -> str:
    return "" if value is None else _WS.sub(" ", str(value)).strip()


def _norm(value: Any) -> str:
    return _text(value).casefold()


def _norm_crs(value: Any) -> str:
    text = _norm(value)
    found = _EPSG.match(text)
    return f"epsg:{found.group(1)}" if found else text


def _clip(value: Any) -> str:
    return _text(value)[:MAX_VALUE_LEN]


def _instant(value: Any) -> datetime | None:
    """ISO 8601 문자열·`datetime`·`date` 를 **타임존 없는 UTC** 순간으로 읽는다."""
    if isinstance(value, datetime):
        moment = value
    elif isinstance(value, date):
        moment = datetime(value.year, value.month, value.day)
    else:
        text = _text(value).replace("Z", "+00:00").replace("z", "+00:00")
        if not text:
            return None
        try:
            moment = datetime.fromisoformat(text)
        except ValueError:
            try:
                moment = datetime.fromisoformat(text[:10])
            except ValueError:
                return None
    if moment.tzinfo is not None:
        moment = moment.astimezone(timezone.utc).replace(tzinfo=None)
    return moment


def _file_tokens(name: Any) -> list[str]:
    stem = _text(name).rpartition(".")[0] or _text(name)
    tokens: list[str] = []
    for raw in _TOKEN_BOUNDARY.split(stem):
        token = raw.casefold()
        if not token or token.isdigit():
            continue
        if _LATIN_TOKEN.match(token):
            if len(token) < 3:
                continue
        elif len(token) < 2:
            continue
        if token not in tokens:
            tokens.append(token)
    return tokens


# ─────────────────────────── 축별 대조 ───────────────────────────
def _period_text(axes: _Axes) -> str:
    start = _text(axes.period_start)
    if not start:
        return ""
    end = _text(axes.period_end)
    return f"{start}~{end}" if end else start


def _periods_overlap(upload: _Axes, cand: _Axes) -> bool:
    """닫힌 구간의 겹침. **양쪽 모두 시작이 있어야** 비교가 성립하고, 없는 끝은 열린 구간이다."""
    u_start, c_start = _instant(upload.period_start), _instant(cand.period_start)
    if u_start is None or c_start is None:
        return False
    u_end, c_end = _instant(upload.period_end), _instant(cand.period_end)
    if u_end is not None and u_end < c_start:
        return False
    if c_end is not None and c_end < u_start:
        return False
    return True


def _shared_variables(upload: _Axes, cand: _Axes) -> tuple[list[str], list[str]]:
    """교집합을 **casefold 기준**으로 고르고 정규화된 이름 순으로 세운다(나열 순서와 무관)."""
    by_norm = {_norm(v): v for v in cand.variables if _text(v)}
    pairs = sorted({_norm(v): v for v in upload.variables if _norm(v) in by_norm}.items())
    return [up for _, up in pairs], [by_norm[key] for key, _ in pairs]


def _axis_text(field: EvidenceField, axes: _Axes) -> str:
    """그 축의 **실제 값** — 인용 대조의 기준이다."""
    if field == "period":
        return _period_text(axes)
    if field == "crs":
        return _text(axes.crs)
    if field == "grid":
        return _text(axes.grid)
    if field == "variables":
        return ", ".join(_text(v) for v in axes.variables)
    return _text(axes.file_name)


def compare(upload: UploadAxes, cand: CandidateAxes) -> tuple[Evidence, ...]:
    """맞는 축만 근거로 돌려준다. 순서는 `EVIDENCE_FIELDS` 고정이고 부작용이 없다."""
    found: list[Evidence] = []
    if _periods_overlap(upload, cand):
        found.append(Evidence("period", _clip(_period_text(upload)), _clip(_period_text(cand))))
    if _norm_crs(upload.crs) and _norm_crs(upload.crs) == _norm_crs(cand.crs):
        found.append(Evidence("crs", _clip(upload.crs), _clip(cand.crs)))
    if _norm(upload.grid) and _norm(upload.grid) == _norm(cand.grid):
        found.append(Evidence("grid", _clip(upload.grid), _clip(cand.grid)))
    up_vars, cand_vars = _shared_variables(upload, cand)
    if up_vars:
        found.append(Evidence("variables", _clip(", ".join(up_vars)),
                              _clip(", ".join(cand_vars))))
    if _file_name_matches(upload.file_name, cand.file_name):
        found.append(Evidence("fileName", _clip(upload.file_name), _clip(cand.file_name)))
    return tuple(found)


def _file_name_matches(up_name: Any, cand_name: Any) -> bool:
    """토큰 **접두**다 — 짧은 쪽이 긴 쪽의 머리여야 한다. 중간 일치는 맞지 않는다."""
    cand_tokens = _file_tokens(cand_name)
    for token in _file_tokens(up_name):
        for other in cand_tokens:
            short, long_one = (token, other) if len(token) <= len(other) else (other, token)
            if long_one.startswith(short):
                return True
    return False


# ─────────────────────────── 인용 검증 · 파생 ───────────────────────────
def verify(claimed: Evidence, upload: UploadAxes, cand: CandidateAxes) -> bool:
    """모델이 인용한 한 건이 **실제 값과 대조되는가**. 결정적이고 I/O 가 없다.

    둘 다 참이어야 한다 — ⑴ 그 축이 실제로 맞는다(`compare` 가 같은 `field` 를 낸다)
    ⑵ 인용한 두 값이 각각 **실제 값 안에 있다**(정규화 부분문자열). 부분문자열을 허용하는
    이유는 계약이 값 길이를 200 으로 묶어서 모델이 긴 값의 일부만 옮겨 적을 수 있기 때문이고,
    **지어낸 값은 어느 쪽에도 없으므로** 그때는 거짓이다.
    """
    if not isinstance(claimed, Evidence) or claimed.field not in EVIDENCE_FIELDS:
        return False
    if claimed.field not in {item.field for item in compare(upload, cand)}:
        return False
    return (_cited_in(claimed.field, claimed.upload_value, _axis_text(claimed.field, upload))
            and _cited_in(claimed.field, claimed.candidate_value, _axis_text(claimed.field, cand)))


def _cited_in(field: EvidenceField, claim: str, actual: str) -> bool:
    normalize = _norm_crs if field == "crs" else _norm
    cited, real = normalize(claim), normalize(actual)
    return bool(cited) and cited in real


def derive_confidence(verified: Sequence[Evidence]) -> str | None:
    """**검증된 근거의 종류 수**에서 확신도를 파생한다 — 모델이 보낸 값은 읽지 않는다.

    같은 축 두 건은 한 종류다. 0 종이면 `None` 이고, 그 자리는 「모름」이 아니라 **빈 제안**이다.
    """
    kinds = {item.field for item in verified if item.field in EVIDENCE_FIELDS}
    if len(kinds) >= 2:
        return CONFIDENCE_SURE
    return CONFIDENCE_VAGUE if kinds else None


_LABELS: dict[str, str] = {"period": "기간", "crs": "좌표계", "grid": "격자",
                           "variables": "변수", "fileName": "파일명"}
_RATIONALE_TAIL = " 가 업로드 파일과 맞는다."


def rationale(verified: Sequence[Evidence]) -> str:
    """검증된 근거만으로 **고정 서식** 한 줄을 만든다. 자유 문장이 없고 줄바꿈이 없다.

    ⚠ 모델의 자연어를 화면에 옮기지 않는 이유가 이 함수의 존재 이유다 — 검증하지 못한 문장이
    사용자에게 가면 「검증된 근거」라는 약속이 반쪽이 된다(`R-K3-STRUCTURE.md` WU-S2).
    값은 후보 쪽 값을 적는다(무엇이 맞았는지를 후보에서 읽게).
    """
    picked: dict[str, str] = {}
    for item in verified:
        if item.field in _LABELS and item.field not in picked:
            picked[item.field] = _text(item.candidate_value)[:_MAX_RATIONALE_VALUE]
    parts = [f"{_LABELS[f]}({picked[f]})" for f in EVIDENCE_FIELDS if f in picked]
    if not parts:
        return ""
    line = " · ".join(parts) + _RATIONALE_TAIL
    while len(line) > MAX_RATIONALE_LEN and len(parts) > 1:
        parts.pop()
        line = " · ".join(parts) + _RATIONALE_TAIL
    return line[:MAX_RATIONALE_LEN]
