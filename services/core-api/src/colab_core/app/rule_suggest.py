"""K3 `WU-S5` — **규칙 기반 계보 제안 팔.** 모델을 부르지 않는다.

왜 core-api 인가 (라운드 `R-K3-STRUCTURE.md` WU-S5 축자)
  이 팔이 쓰는 입력은 D3 신호(`domains.d3_lineage_signals`)와 후보 자동 메타이고
  **둘 다 core-api 안에만 있다.** ai-service 에 두려면 신호를 계약에 실어 보내야 하는데
  그것은 열린 권고 ① 로 기각됐다(보내면 모델이 그대로 베껴 돌려주고 core-api 는 자기가
  보낸 값을 자기가 검증하게 된다). 그리고 이 팔은 **모델에 닿지 않으므로** 저쪽 배포
  단위에 둘 이유 자체가 없다 — 그 단위의 존재 이유가 모델 접속이다(`CLAUDE.md §3-1`).

무엇이 같고 무엇이 다른가
  · **Port 가 같다** — `ports.LineageSuggestionPort.suggest` 서명 그대로다. 라우트는 어느
    팔인지 모른 채 `app.state.suggestions` 를 부른다.
  · **판정 규칙이 같다** — 근거·확신도·근거 한 줄은 전부 `d3_lineage_signals` 한 벌에서
    나온다(`WU-S2` 가 모델의 인용을 검증할 때 쓰는 그 함수들이다). 두 벌이면 실측의
    두 팔 비교가 「같은 자로 잰 두 값」이 아니게 된다.
  · **상위 k 절단이 같다**(Ted 판정 2회차 5) — `relay.SUGGESTION_LIMIT` 한 상수다.
  · 다른 것은 **근거의 산지**뿐이다: 모델 팔은 모델이 인용하고 core-api 가 검증하며,
    이 팔은 core-api 가 직접 대조한다. 그래서 이 팔에는 **폐기라는 사건이 없다.**

**저장이 없다 · 실행 원장에 행이 없다.** 제안은 이 함수 안에서 태어나 응답과 함께 죽는다
(`ai-no-lineage-write`). D10 실행 원장(`db/ai`)은 ai-service 의 표이고 core-api 는 그 배포
단위를 import 하지 않는다(`import-boundary` 계약 1) — 그러므로 모델을 부르지 않은 이 팔의
`not_called` 행을 여기서 남길 방법이 없고, 없는 자리를 만들지도 않는다.
"""
from __future__ import annotations

from typing import Any

from ..domains import d3_lineage_signals
from ..kernel.ids import Ulid
from .relay import (PARENT_SUGGESTION_KIND, SUGGESTION_LIMIT,
                    HttpLineageSuggestionRelay, honest_empty_suggestions)

__all__ = ["ARM_MODEL", "ARM_RULES", "LINEAGE_SUGGESTER_ARM", "NO_MATCHING_AXIS_REASON",
           "SUGGESTION_LIMIT", "RuleBasedLineageSuggester", "build_lineage_suggester",
           "resolve_arm"]

#: ⭑ **다섯 번째 영(零) 상태의 사유 한 줄.** 적격 후보를 **전부 대조했고** 맞는 축이 하나도
#: 없었다 — 「못 물어봤다」도 「Lv 를 안 골랐다」(`routes/ingestion.LEVEL_REQUIRED_REASON`)도
#: 아니다. 고칠 사람이 다르므로 문구를 접지 않는다(`relay.honest_empty_suggestions` 산문).
#: ⚠ 사유 코드 enum 을 새로 만들지 않는다 — 오늘 이 값을 읽는 FE 소비자가 0건이고, 읽는
#: 쪽이 생기는 회차가 코드를 정한다(라운드 `WU-S1` 축자).
NO_MATCHING_AXIS_REASON = "대조 축이 맞는 후보가 없습니다."

#: 팔 이름 두 값. `"both"` 를 두지 않는다 — 두 팔을 합치는 규칙을 지금 정하면 **측정 전에
#: 결정이 굳는다**(라운드 WU-S5). 실측은 팔을 하나씩 세워 같은 적격 집합에 돌린다.
ARM_MODEL = "model"
ARM_RULES = "rules"
ARMS = (ARM_MODEL, ARM_RULES)

#: ⛔ **환경변수가 아니다.** 팔 선택은 **측정으로 바뀔 값**이지 배포마다 다를 값이 아니다
#: (`routes/ingestion.LINEAGE_CANDIDATE_STRATEGY` 와 같은 규율 · 라운드 WU-S5 축자).
#: 기본은 **현행 유지**이고, 모르는 값은 여기로 떨어진다(`kernel/config.py` 선례 —
#: 오타가 새 동작을 켜지 않는다).
LINEAGE_SUGGESTER_ARM = ARM_MODEL

#: ⭑ **부모 역할의 잠정 어림이다 — 판정이 아니다.** 파일명 토큰이 이어지거나 변수 이름이
#: 겹치면 그 후보의 값이 이 파일 **안으로 들어왔을** 가능성이 크고(같은 계열의 산출물),
#: 좌표계·격자·기간만 같은 것은 **같은 틀에서 만들어졌다**는 뜻이라 보조에 가깝다.
#: ⚠ 근거는 이 한 문단뿐이다. 정본은 **사람이 확인할 때 고른다**(`Policy §5 부모 역할` —
#: 「제안값이고 사람이 바꿀 수 있다」). 실측(`WU-S6`)이 이 어림의 값어치를 잰다.
_PRIMARY_INPUT_FIELDS = frozenset({"fileName", "variables"})


def _parent_role(found: tuple) -> str:
    return ("주입력" if {item.field for item in found} & _PRIMARY_INPUT_FIELDS
            else "보조입력")


class RuleBasedLineageSuggester:
    """`ports.LineageSuggestionPort` — **모델 없이 대조만으로 내는 답.**

    받은 후보는 이미 적격이다(`select_lineage_candidates(upload_level=...)` 가 후손·자기
    자신을 걸렀다) — 이 팔은 그 뒤의 **순수 계산**이고 DB 도 세션도 들지 않는다. 그래서
    연구실 경계(RLS)는 후보를 고른 그 자리가 이미 그었고 여기서 다시 긋지 않는다.
    """

    def suggest(self, *, lab_id: str, lab_name: str, account_id: str,
                file_meta: dict[str, Any], candidates: list[dict[str, Any]],
                searched_count: int, dataset_name_draft: str | None,
                subject: str | None, processing_level: int,
                upload_axes: Any, candidate_axes: dict[str, Any]) -> dict[str, Any]:
        found: list[tuple[int, dict[str, Any], tuple]] = []
        for candidate in candidates:
            axes = candidate_axes.get(candidate.get("datasetId"))
            if axes is None:
                # 본문은 왔는데 대조 축이 없다 — **없는 축을 지어내지 않는다.**
                continue
            evidence = d3_lineage_signals.compare(upload_axes, axes)
            if evidence:
                found.append((len(evidence), candidate, evidence))
        # **검증된 신호 종류 수 내림차순.** 동률의 갈림은 후보가 들어온 순서 — 그것이
        # `select_lineage_candidates` 가 매긴 순위다. `sorted` 가 안정 정렬이라 동률에서
        # 원래 순서가 그대로 선다(새 순위를 이 자리에서 만들지 않는다).
        # ⚠ 라운드 초안의 `last_modified_at` 은 **이 표면에 오지 않는다** — 나르는 것은
        #   계약 본문과 대조 축뿐이고, 여기서 DB 를 다시 읽으면 「보낸 값」과 「순위에 쓴
        #   값」이 갈린다(`WU-S2` 가 인용 검증에서 막아 둔 그 자리).
        found.sort(key=lambda row: -row[0])
        suggestions = [self._suggestion(candidate, evidence)
                       for _, candidate, evidence in found[:SUGGESTION_LIMIT]]
        if not suggestions:
            # **살펴봤고 없었다.** 「억지 제안을 만들지 않는다」가 구조로 나오는 자리다 —
            # 규칙 팔에는 모델이 없으므로 그럴듯한 한 건이 끼어들 틈 자체가 없다.
            return honest_empty_suggestions(
                lab_id=lab_id, lab_name=lab_name, searched_count=searched_count,
                reason=NO_MATCHING_AXIS_REASON)
        return {
            "degraded": False,
            "scope": {"labId": lab_id, "labName": lab_name, "searchedCount": searched_count},
            # **원자료라고 주장하지 않는다** — 정본은 판정 방법을 적지 않았다
            # (ai-service `app/main.py` 의 같은 자리와 같은 사유).
            "rawDataLikely": False,
            "suggestions": suggestions,
        }

    @staticmethod
    def _suggestion(candidate: dict[str, Any], evidence: tuple) -> dict[str, Any]:
        """제안 한 장 = 계약 `ParentCandidateSuggestion`. **이름·Lv 는 후보에서 온다.**"""
        out: dict[str, Any] = {
            "suggestionId": str(Ulid.generate()),
            "kind": PARENT_SUGGESTION_KIND,
            # 확신도·근거 한 줄의 산지는 `WU-S2` 와 **같은 함수**다. 대조한 것이 곧 근거라
            # 이 팔에서는 `derive_confidence` 가 `None` 을 낼 수 없다(0종은 위에서 빠진다).
            "confidence": d3_lineage_signals.derive_confidence(evidence),
            "rationale": d3_lineage_signals.rationale(evidence),
            "parentDatasetId": candidate.get("datasetId"),
            "parentDatasetName": candidate.get("name"),
            "suggestedParentRole": _parent_role(evidence),
            "evidence": [item.to_dict() for item in evidence],
        }
        level = candidate.get("processingLevel")
        if level is not None:
            # **모르면 열쇠를 만들지 않는다** — `0` 을 실으면 「Lv0 이다」로 읽힌다(계약 산문).
            out["parentProcessingLevel"] = level
        return out


def resolve_arm(arm: str | None = None) -> str:
    """고를 팔 하나. **모르는 값·오타는 기본(`model`)으로 떨어진다.**

    `None` 은 「이 부름이 팔을 고르지 않았다」이고 그때 정본은 모듈 상수다 —
    「고르지 않았다」와 「모르는 값을 골랐다」는 다른 사실이지만 **떨어지는 자리는 같다.**
    """
    picked = LINEAGE_SUGGESTER_ARM if arm is None else arm
    return picked if picked in ARMS else ARM_MODEL


def build_lineage_suggester(base_url: str | None, *, arm: str | None = None):
    """조립 루트(`app/main.create_app`)가 부르는 **팔 고르는 자리 한 곳.**

    ⭑ `arm` 은 **부름마다 고르는 자리**다 — 실측(`WU-S6`)이 같은 적격 집합에 두 팔을
    나란히 돌리려면 환경을 바꾸지 않고 팔을 고를 수 있어야 한다. 제품 경로는 이 인자를
    넘기지 않고 모듈 상수를 그대로 탄다.
    """
    if resolve_arm(arm) == ARM_RULES:
        return RuleBasedLineageSuggester()
    # ai-service 주소가 없어도 중계를 세운다 — 그쪽이 **0건 + degraded** 를 만들어 낸다.
    return HttpLineageSuggestionRelay(base_url)
