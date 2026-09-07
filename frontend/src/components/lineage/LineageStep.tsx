// ③ 계보 확정 — 정본 `Policy_업로드와_계보_확정.md` §8 「AI 제안 영역」·「가공 단계 칸」.
//
// 이 화면이 지키는 것 (`CLAUDE.md §3` AI 응답 규격 · `P2-EXEC §4` · `P2.md §2-9`)
//  - **뒤진 범위를 먼저 밝힌다.** 제안보다 위에 「어느 연구실의 몇 건을 살펴봤는가」가 선다.
//  - **[모두 승인] 이 없다.** 확인·수정·거절을 항목마다 받는다. 묶음 승인 버튼을 두지 않는다.
//  - 확신도는 `확실|애매|모름` **enum**이고 퍼센트·점수를 붙이지 않는다. **근거는 필수**다.
//  - **사람이 `수정` 하면 AI 행동이 아니다** — 확신도 칩을 걷고 경로를 `manual` 로
//    바꾸며 **확인을 다시 받는다** (정본 §8 `수정 버튼`).
//  - **제안 0건은 정직한 빈 상태**다. 억지 제안을 만들지 않고, **등록은 그대로 끝까지 간다** —
//    AI 없이도 v2 는 완결된 제품이다.
//  - **AI 제안은 사용자가 눌러 받는 보조다** (`PLAN-SoT §9 〈197〉`·`〈203〉` · `LV-2`).
//    마운트만으로 부르지 않는다 — 사람이 시작하지 않은 조회는 「고장」과 「원래 0건」을
//    같은 무게로 흘려보내고, 사용자가 고장을 모르게 만든다(`〈197〉`-㉰).
//    누르기 전에는 **직접 연결이 기본 자리**이고, 호출 횟수는 **누른 횟수**와 같다.
//  - **아무것도 저장하지 않는다.** 확인된 관계는 `createDataset` 의 `lineageParents` 로만 간다.
//  - **가공 방식은 관계에 붙는다** — 데이터셋이 아니라 「자식 ← 부모」 한 쌍의 라벨이다.
//  - ⭑ **⟨반전 2026-09-07 · `〈194〉` 반전 · PRD-03·07·10 · 미결-2 ⓐ⟩ 가공 단계 Lv 는
//    **사람이 ① 분류에서 고른다**(`processingLevelUserSet`). 이 화면은 그 값을 **기준으로
//    쓰기만 하고 바꾸거나 잠그지 않는다.**
//    ／ 종전 ~~「가공 단계 Lv 를 화면이 계산하지 않는다. 파생값이고 core 가 계산한다
//    (`PLAN-SoT §9-⑳`)」~~ — 그 문장은 **레벨이 오직 계보에서만 나오던 때**의 것이다.
//    ⚠ **파생 계산 자체는 그대로 core 몫이다** — 아래 미리보기는 확인된 부모의 표시 Lv 로
//    만든 **추정**이고, 판정은 서버 응답(`processingLevelDerived`)이 한다.
//  - **규칙은 하나다 — 부모 Lv ≤ 자기 Lv.** 같은 단계는 허용이고, 초과 후보는 **보이되
//    고를 수 없다**(숨기지 않는다). **서버 400 이 최종 방어선**이고 이 화면은 그 앞이다.
import { useCallback, useEffect, useRef, useState } from 'react';
import type { LineageStepContext } from '../upload/types';
import {
  LV_VALUES,
  levelOf,
  displayLevel,
  PARENT_ROLES,
  type AiConfidence,
  type DatasetRow,
  type LineageOrigin,
  type LineageSource,
  type LineageSuggestionResponse,
  type ParentCandidateSuggestion,
  type ParentCard,
  type ParentRole,
  type ProcessingMethodSuggestion,
  type UploadLineageParent,
} from './types';
// ⭑ **⟨WU-B10 · PRD-31⟩ 찾기·연결 UI 와 초과 사유 문면은 `ParentPicker` 한 벌뿐이다** —
//   상세 계보 모달(`LineageFixModal`)이 **같은 컴포넌트·같은 함수**를 부른다. 종전에는 이
//   화면 안의 `picker()`·`overReason()` 이 유일본이었고, 모달이 사본을 뜨면 PRD-07·08·09 의
//   규칙이 두 벌이 된다.
import { ParentPicker, parentOverReason } from './ParentPicker';
import './lineage.css';

/** 안내 줄 축자 (PRD-07 rev1). `Lv0` 이면 범위 문면이 `Lv0` 하나다. */
function scopeNotice(selfLv: number): string {
  const range = selfLv === 0 ? 'Lv0' : `Lv0~Lv${selfLv}`;
  return `지금 이 데이터는 Lv${selfLv} · ${range} 가공 전 데이터만 연결할 수 있어요.`;
}

/**
 * ⭑ **⟨PRD-27 · WU-B8 · 미결-6 ⓐ⟩ 「기록 없음」 선언 체크박스의 라벨 — 축자다.**
 * ／ 종전 문면(rev1 `#unknownChk` 의 한 줄)은 폐기됐다 — docx `J-20` 「무슨 말인지 잘 이해가
 * 안될 것 같습니다」를 조성진이 두 번 적었다. ⛔ **그 문자열은 코드 어디에도 남기지 않는다** —
 * 주석에도 적지 않는다(시험이 `src`·`test` 전체에서 0건을 센다).
 */
export const LINEAGE_UNKNOWN_LABEL = '가공 전 데이터를 못 찾았어요 — 기록 없이 등록할게요';

/**
 * 확정 부모가 1건 이상일 때 체크박스에 붙는 **사유 한 줄** (미결-6 ⓐ).
 * ⛔ 숨기지 않고, 연결을 지우지도 않는다 — docx `D-6-1` 「가공 전 데이터가 있는데 저
 * 체크박스가 나타나는게 이상하다」를 **비활성 ＋ 사유**로 해소한다.
 */
export const LINEAGE_UNKNOWN_DISABLED_REASON =
  '가공 전 데이터를 이어 붙였어요. 연결을 지우면 다시 고를 수 있어요.';


/** 가공 방식 제안 한 건 — 어느 **관계**에 붙일지가 정해져야 확인할 수 있다. */
interface MethodCard {
  key: string;
  text: string;
  confidence: AiConfidence | null;
  rationale: string;
  appliesToParentDatasetId: string | null;
  confirmed: boolean;
}

function isParentCandidate(s: { kind: string }): s is ParentCandidateSuggestion {
  return s.kind === '가공 전 데이터';
}
function isProcessingMethod(s: { kind: string }): s is ProcessingMethodSuggestion {
  return s.kind === '가공 방식';
}

/** 확신도 칩. **숫자를 붙이지 않는다** — 확신도에 퍼센트가 없다 (`common.json#AiConfidence`). */
function ConfidenceChip(props: { value: AiConfidence }) {
  return (
    <span className={`conf conf-${props.value}`} data-testid="lin-confidence">
      {props.value}
    </span>
  );
}

export function LineageStep(props: { source: LineageSource; ctx: LineageStepContext }) {
  const { source, ctx } = props;
  const { uploadId, onLineageProgress, onLineageParentsChange, onLineageConflictChange } = ctx;
  // ⭑ **⟨WU-B5 · PRD-09⟩ 연결 카드는 모달이 쥔다** — 이 화면은 단계 이동 때마다
  //   언마운트되므로 여기 `useState` 로 두면 ① 에 다녀오는 순간 연결이 사라진다.
  const parents = ctx.parents;
  const setParents = ctx.onParentsChange;
  /** ① 에서 고른 자기 Lv. **기준값**이고, 안 골랐으면 `null` 이라 규칙이 서지 않는다. */
  const selfLv = levelOf(ctx.processingLevelUserSet);
  /**
   * ⭑ **⟨PRD-27 · WU-B8⟩ 「기록 없음」 체크박스의 두 성질.**
   *  · **확정 부모 ≥1 → 비활성 ＋ 사유 한 줄.** 칸은 **사라지지 않고** 연결도 지우지 않는다.
   *  · **자기 Lv 가 `Lv0` → 보이지 않는다.** 판정 ⑷ 가 이미 `원천` 으로 가르므로 물을 것이
   *    없다 — 물으면 「원시 데이터인데 왜 못 찾았냐고 묻나」가 된다.
   */
  const confirmedParentCount = parents.filter((p) => p.confirmed).length;
  const unknownDisabled = confirmedParentCount > 0;
  const unknownVisible = selfLv !== 0;

  const [resp, setResp] = useState<LineageSuggestionResponse | null>(null);
  const [unavailable, setUnavailable] = useState(false);
  const [methods, setMethods] = useState<MethodCard[]>([]);
  const [candidates, setCandidates] = useState<DatasetRow[] | null>(null);
  /** 찾기 모달의 가공 단계 셀렉트. `null` = 전체 (PRD-08). */
  const [levelFilter, setLevelFilter] = useState<number | null>(null);
  const [adding, setAdding] = useState(false);
  /** 사용자가 제안을 부른 적이 있는가. **부르기 전에는 결과 영역 자체가 없다.** */
  const [asked, setAsked] = useState(false);
  const [asking, setAsking] = useState(false);

  // 이름 초안·주제는 **해석 단서일 뿐**이라 값이 바뀔 때마다 다시 물으면 타이핑마다 왕복이 된다.
  // 조회는 업로드 한 건당 한 번이고, 단서는 그 시점 값을 읽는다.
  const clues = useRef({ datasetNameDraft: ctx.datasetNameDraft, subject: ctx.topic });
  clues.current = { datasetNameDraft: ctx.datasetNameDraft, subject: ctx.topic };

  /**
   * 제안 조회 — **버튼이 부른다.** 마운트·`uploadId` 변화로는 돌지 않는다(완료 정의 ⓐ·ⓔ).
   * 다시 누르면 앞의 결과를 지우고 새로 받는다 — 옛 결과가 새 판정처럼 남지 않게.
   */
  const askSuggestions = useCallback(() => {
    if (!uploadId || asking) return;
    const { datasetNameDraft, subject } = clues.current;
    setAsking(true);
    setAsked(true);
    setUnavailable(false);
    setResp(null);
    void source
      .suggestions(uploadId, {
        ...(datasetNameDraft ? { datasetNameDraft } : {}),
        ...(subject ? { subject } : {}),
      })
      .then((r) => {
        setResp(r);
        setParents((cur) => [
          // 사람이 직접 이어 붙인 것은 **AI 결과가 갈아 끼워도 남는다** — 사람 행동이기 때문.
          ...cur.filter((p) => p.origin === 'manual'),
          ...r.suggestions.filter(isParentCandidate).map((s) => ({
            key: s.suggestionId,
            parentDatasetId: s.parentDatasetId,
            parentDatasetName: s.parentDatasetName,
            role: s.suggestedParentRole,
            confidence: s.confidence,
            rationale: s.rationale,
            // `ai` = **AI 가 제안하고 사람이 확인한 것**. 「AI 가 만든 것」이 아니다 —
            // AI 는 계보를 쓰지 않는다 (`CLAUDE.md §3-2`). 값의 뜻은 `LineageOrigin` 이 정본.
            // ⚠ 이 값을 **화면에 그대로 보여주지 않는다** — 사용자 문구는 아직 미정이다.
            origin: 'ai' as LineageOrigin,
            confirmed: false,
            method: '',
            confirmedMethodText: null,
            picking: false,
            // ⭑ **⟨WU-C9 · 21차 해제 ⑸ · 질의 23⟩ 제안이 부모 Lv 를 실어 온다.**
            //    실려 오면 화면이 **서버 400 전에** 충돌을 경고할 수 있다. 열쇠가 없으면
            //    종전대로 `null` 이고 충돌로 세지 않는다 — **지어내지 않는다**.
            //    판정의 정본은 여전히 서버 400 이다(§5-23).
            parentLevel: s.parentProcessingLevel ?? null,
          })),
        ]);
        setMethods(
          r.suggestions.filter(isProcessingMethod).map((s) => ({
            key: s.suggestionId,
            text: s.methodText,
            confidence: s.confidence,
            rationale: s.rationale,
            appliesToParentDatasetId: s.appliesToParentDatasetId ?? null,
            confirmed: false,
          })),
        );
      })
      .catch(() => {
        // **제안을 못 받는 것과 등록을 못 하는 것은 다르다.** 알리기만 하고 길은 그대로 둔다.
        setUnavailable(true);
      })
      .finally(() => setAsking(false));
  }, [uploadId, source, asking]);

  // 확인된 것만 위로 올린다. 여기가 「사람이 확인한 것만 커밋된다」의 화면 쪽 끝이다.
  useEffect(() => {
    const out: UploadLineageParent[] = parents
      .filter((p) => p.confirmed)
      .map((p) => ({
        parentDatasetId: p.parentDatasetId,
        parentRole: p.role,
        origin: p.origin,
        // 제안을 확인한 문장과 직접 적은 문장은 **같은 자리로 접힌다** — 둘 다 실으면 400 이다.
        ...(p.confirmedMethodText
          ? { confirmedMethodText: p.confirmedMethodText }
          : p.method.trim()
            ? { method: p.method.trim() }
            : {}),
      }));
    onLineageParentsChange(out);
  }, [parents, onLineageParentsChange]);

  useEffect(() => {
    // 표시기의 `③ 계보 확정 0 / N`. **0건이면 부르지 않는다** (`upload/types.ts`).
    if (parents.length === 0) return;
    onLineageProgress({ confirmed: parents.filter((p) => p.confirmed).length, total: parents.length });
  }, [parents, onLineageProgress]);

  const loadCandidates = useCallback(
    (level: number | null = levelFilter, force = false) => {
      if (candidates && !force) return;
      setCandidates(null);
      void source
        .candidates(level)
        .then((rows) => setCandidates(rows))
        .catch(() => setCandidates([]));
    },
    [candidates, source, levelFilter],
  );

  /** 셀렉트가 바뀌면 **다시 묻는다** — 거르는 자리는 서버다(질의 파라미터 · PRD-08). */
  function changeLevelFilter(next: number | null) {
    setLevelFilter(next);
    loadCandidates(next, true);
  }

  /**
   * ⭑ **⟨PRD-09⟩ 사후 충돌 건수.** 확인된 부모 중 자기 Lv 를 넘는 것.
   * **연결을 지우지 않는다** — 세기만 하고, 막는 것은 `데이터셋 만들기` 버튼 하나다.
   */
  const conflicts = parents.filter(
    (p) => selfLv !== null && p.parentLevel !== null && p.parentLevel > selfLv,
  );

  useEffect(() => {
    onLineageConflictChange(conflicts.length);
  }, [conflicts.length, onLineageConflictChange]);

  /**
   * 파생 Lv **미리보기** — 확인된 부모의 표시 Lv 중 최대 + 1, 상한 3(`LV_CAP`).
   * ⚠ **판정이 아니다.** 등록 전에는 서버가 계산한 값이 없어(데이터셋이 아직 없다)
   *   화면이 같은 식으로 미리 보여 줄 뿐이고, 저장 뒤의 정본은 응답의
   *   `processingLevelDerived` 다. 부모 Lv 를 하나라도 모르면 미리보기를 만들지 않는다.
   */
  const known = parents.filter((p) => p.confirmed).map((p) => p.parentLevel);
  const derivedPreview =
    known.length === 0 || known.some((v) => v === null)
      ? null
      // 상한은 `LV_VALUES` 의 마지막 값이다 — 목록을 넓히면 여기가 따라 넓어진다.
      : Math.min(Math.max(...(known as number[])) + 1, LV_VALUES[LV_VALUES.length - 1] as number);
  const mismatch = selfLv !== null && derivedPreview !== null && derivedPreview !== selfLv;

  function patch(key: string, next: Partial<ParentCard>) {
    setParents((cur) => cur.map((p) => (p.key === key ? { ...p, ...next } : p)));
  }

  /** `수정` — 이 순간부터 AI 행동이 아니다. 칩을 걷고 경로를 바꾸고 확인을 무른다. */
  function editTo(key: string, row: DatasetRow) {
    patch(key, {
      parentDatasetId: row.datasetId,
      parentDatasetName: row.name,
      confidence: null,
      rationale: null,
      origin: 'manual',
      confirmed: false,
      confirmedMethodText: null,
      picking: false,
      parentLevel: displayLevel(row),
    });
  }

  function addParent(row: DatasetRow) {
    setAdding(false);
    setParents((cur) => [
      ...cur,
      {
        key: `직접:${row.datasetId}:${cur.length}`,
        parentDatasetId: row.datasetId,
        parentDatasetName: row.name,
        role: '주입력',
        confidence: null,
        rationale: null,
        origin: 'manual',
        confirmed: false,
        method: '',
        confirmedMethodText: null,
        picking: false,
        // 후보 줄이 들고 온 표시 Lv — 사후 충돌을 재는 값이다(PRD-09).
        // ⭑ ⟨WU-C9⟩ 표시 규칙은 네 자리와 같은 `displayLevel` 이다.
        parentLevel: displayLevel(row),
      },
    ]);
  }

  function confirmMethod(m: MethodCard, targetId: string) {
    patch(targetId, { confirmedMethodText: m.text, method: '' });
    setMethods((cur) => cur.map((x) => (x.key === m.key ? { ...x, confirmed: true } : x)));
  }

  function picker(onPick: (row: DatasetRow) => void, testid: string) {
    return (
      <ParentPicker
        selfLv={selfLv}
        candidates={candidates}
        levelFilter={levelFilter}
        onLevelFilterChange={changeLevelFilter}
        onPick={onPick}
        testId={testid}
      />
    );
  }

  const scope = resp?.scope;

  /** 직접 연결 — **누르기 전에는 이 자리가 기본**이라 AI 영역보다 위에 선다(완료 정의 ⓑ). */
  const addBlock = (
    <div className="lin-add">
      <button
        type="button"
        className="btn btn-secondary btn-sm"
        data-testid="lin-add"
        onClick={() => {
          loadCandidates(levelFilter, true);
          setAdding((v) => !v);
        }}
      >
        앞 데이터 직접 추가
      </button>
      {adding && picker(addParent, 'lin-picker')}
    </div>
  );

  return (
    <section className="lin" data-testid="lin-step">
      {/* ⭑ **⟨PRD-07⟩ 연결 규칙 안내 — 이 단계의 맨 위다.** 문면은 rev1 축자이고
          `분류에서 바꾸기` 는 ① 로 데려가는 길이다. ⛔ **자기 Lv 를 여기서 바꾸지 않는다.**
          자기 Lv 를 아직 안 골랐으면(`null`) 기준값이 없어 이 줄이 서지 않는다. */}
      {selfLv !== null && (
        <p className="lin-scope-lv" data-testid="lin-lv-scope">
          {scopeNotice(selfLv)}{' '}
          <button type="button" className="lin-link" data-testid="lin-goto-classify"
                  onClick={ctx.onGoToClassify}>
            분류에서 바꾸기
          </button>
        </p>
      )}

      {/* ⭑ **⟨PRD-09⟩ 사후 충돌 — 연결은 그대로 두고 등록만 막는다.** */}
      {conflicts.length > 0 && (
        <p className="lin-note lin-conflict" role="alert" data-testid="lin-conflict-note">
          {parentOverReason(selfLv as number)}
        </p>
      )}

      {/* ⭑ **⟨PRD-10⟩ 불일치는 경고만이다 — 저장을 막지 않는다.** */}
      {mismatch && (
        <p className="lin-note" data-testid="lin-lv-mismatch">
          {`고른 가공 단계는 Lv${selfLv}이고, 연결한 데이터로 계산하면 Lv${derivedPreview}이에요. 그대로 두어도 등록돼요.`}
        </p>
      )}

      {/* **범위를 먼저 밝힌다** — 무엇을 근거로 삼았는지가 제안보다 위에 선다 */}
      {scope && (
        <p className="lin-scope" data-testid="lin-scope">
          {scope.searchedCount === 0 ? (
            <>
              <b>{scope.labName}</b>에 아직 살펴볼 데이터가 없어요.
            </>
          ) : (
            <>
              <b>{scope.labName}</b>의 데이터 {scope.searchedCount}건을 살펴봤어요.
            </>
          )}
        </p>
      )}

      {unavailable && (
        <p className="lin-note" data-testid="lin-unavailable">
          지금은 계보 제안을 받을 수 없어요. 아래에서 직접 이어 붙이거나, 그대로 등록해도 돼요.
        </p>
      )}

      {resp?.degraded && (
        <p className="lin-note" data-testid="lin-degraded">
          지금은 계보 제안을 온전히 받지 못했어요. 직접 이어 붙이거나 그대로 등록해도 돼요.
        </p>
      )}

      {resp?.rawDataLikely && (
        <p className="lin-note" data-testid="lin-raw">
          가공한 흔적이 없어 원자료로 보여요. 앞 데이터 없이 <b>원천 표기</b>만 적고 등록해도 돼요.
        </p>
      )}

      <div className="lin-cards" data-testid="lin-cards">
        {parents.map((p) => (
          <div className="lin-card" data-testid="lin-card" key={p.key}>
            <div className="lin-h">
              <span className="lin-name">{p.parentDatasetName}</span>
              {p.confidence && <ConfidenceChip value={p.confidence} />}
              {p.confirmed && <span className="lin-ok">확인함</span>}
              {/* ⭑ **⟨PRD-09⟩ 사후 충돌 표시.** 연결은 남고 이 칩만 붙는다 —
                  되돌리면 칩이 사라지고 `데이터셋 만들기` 가 다시 눌린다. */}
              {selfLv !== null && p.parentLevel !== null && p.parentLevel > selfLv && (
                <span className="chip chip--warning" data-testid="lin-need-check">
                  확인 필요
                </span>
              )}
            </div>

            {p.rationale && (
              <p className="lin-why" data-testid="lin-rationale">
                {p.rationale}
              </p>
            )}

            <div className="lin-f">
              <label>
                <span>부모 역할</span>
                <select
                  className="sel"
                  data-testid="lin-role"
                  value={p.role}
                  onChange={(e) => patch(p.key, { role: e.target.value as ParentRole })}
                >
                  {PARENT_ROLES.map((r) => (
                    <option key={r} value={r}>
                      {r}
                    </option>
                  ))}
                </select>
              </label>

              {/* 제안을 확인한 문장이 있으면 그 자리를 쓴다 — 두 자리를 동시에 채우지 않는다 */}
              {p.confirmedMethodText ? (
                <p className="lin-method-done" data-testid="lin-method-done">
                  가공 방식 · {p.confirmedMethodText}
                </p>
              ) : (
                <label>
                  <span>가공 방식 (선택)</span>
                  <input
                    className="inp"
                    data-testid="lin-method"
                    maxLength={120}
                    value={p.method}
                    onChange={(e) => patch(p.key, { method: e.target.value })}
                  />
                </label>
              )}
            </div>

            {/* 항목마다 셋. **묶음 승인 버튼은 없다.** */}
            <div className="lin-a">
              <button
                type="button"
                className="btn btn-strong btn-sm"
                data-testid="lin-confirm"
                onClick={() => patch(p.key, { confirmed: true, picking: false })}
              >
                확인
              </button>
              <button
                type="button"
                className="btn btn-secondary btn-sm"
                data-testid="lin-edit"
                onClick={() => {
                  loadCandidates(levelFilter, true);
                  patch(p.key, { picking: !p.picking });
                }}
              >
                수정
              </button>
              <button
                type="button"
                className="btn btn-ghost btn-sm"
                data-testid="lin-reject"
                onClick={() => setParents((cur) => cur.filter((x) => x.key !== p.key))}
              >
                거절
              </button>
            </div>

            {p.picking && picker((row) => editTo(p.key, row), 'lin-edit-picker')}
          </div>
        ))}

        {/* 가공 방식 제안 — **관계에 붙는 값**이라 어느 부모와의 관계인지가 정해져야 확인된다 */}
        {methods
          .filter((m) => !m.confirmed)
          .map((m) => {
            const target = parents.find((p) => p.parentDatasetId === m.appliesToParentDatasetId);
            return (
              <div className="lin-card lin-mcard" data-testid="lin-method-card" key={m.key}>
                <div className="lin-h">
                  <span className="lin-name">가공 방식 · {m.text}</span>
                  {m.confidence && <ConfidenceChip value={m.confidence} />}
                </div>
                <p className="lin-why" data-testid="lin-rationale">
                  {m.rationale}
                </p>
                <p className="lin-mparent" data-testid="lin-method-parent">
                  {target
                    ? `「${target.parentDatasetName}」 와의 관계에 붙어요.`
                    : '어느 관계에 붙일지 알 수 없어요. 앞 데이터를 먼저 확인해 주세요.'}
                </p>
                <div className="lin-a">
                  <button
                    type="button"
                    className="btn btn-strong btn-sm"
                    data-testid="lin-confirm"
                    disabled={!target}
                    onClick={() => target && confirmMethod(m, target.key)}
                  >
                    확인
                  </button>
                  <button
                    type="button"
                    className="btn btn-ghost btn-sm"
                    data-testid="lin-reject"
                    onClick={() => setMethods((cur) => cur.filter((x) => x.key !== m.key))}
                  >
                    거절
                  </button>
                </div>
              </div>
            );
          })}
      </div>

      {/* 제안 0건 = **정직한 빈 상태.** 억지 카드를 만들지 않고, 등록은 그대로 끝까지 간다.
          ⚠ **0건의 뜻이 셋이라 문구를 가른다** (`PLAN-SoT §9 〈211〉`-㉮-⑵ 「화면이 그대로 적는다」).
          제안 기능은 **데이터가 없으면 무엇이든 0건**이라, 셋을 한 문구로 접으면 화면이
          「살펴봤는데 없다」를 언제나 말하게 된다 — 그것이 이 항목의 green-by-skip 형태다.
            ㈎ `nothing-to-search` — 뒤질 대상이 0건이었다. **제안이 가능했던 적이 없다.**
            ㈏ `searched-none`    — 뒤질 대상이 있었고 서비스가 답했는데 **0건이 참인 답**이다.
                                    **제안이 가능했으나 하지 않은 것**이고, 이 자리가 음성 판정이다.
            ㈐ `not-asked`        — 물어보지 못했다(`degraded`). 「없다」가 아니라 **모른다**다. */}
      {resp && !unavailable && parents.length === 0 && methods.length === 0 && (
        <p
          className="lin-empty"
          data-testid="lin-empty"
          data-kind={
            resp.degraded
              ? 'not-asked'
              : (scope?.searchedCount ?? 0) === 0
                ? 'nothing-to-search'
                : 'searched-none'
          }
        >
          {resp.degraded ? (
            <>
              앞선 데이터가 있는지 <b>확인하지 못했어요</b> — 없다는 뜻은 아니에요. 직접 이어 붙이거나,
              그대로 등록해도 돼요.
            </>
          ) : (scope?.searchedCount ?? 0) === 0 ? (
            <>
              연구실에 앞선 데이터가 아직 없어서 <b>살펴볼 것이 없었어요.</b> 그대로 등록하면{' '}
              <b>계보는 「기록 없음」</b>으로 남고 나중에 상세 화면에서 이을 수 있어요.
            </>
          ) : (
            <>
              데이터 {scope?.searchedCount}건을 살펴봤지만 <b>앞선 데이터를 찾지 못했어요.</b> 직접 이어
              붙이거나, 그대로 등록해도 돼요 — <b>계보는 「기록 없음」</b>으로 남고 나중에 상세 화면에서
              이을 수 있어요.
            </>
          )}
        </p>
      )}

      {/* `PLAN-SoT §9 〈139〉`·`〈140〉` — 종전 문구는 「`보조입력` 으로 표시한 부모는…」
          이었다. 그런데 **화면에 그 표시를 하는 자리가 없다**(부모 역할은 묻지 않고
          서버 기본값 `주입력`). 정할 수 없는 값을 설명하면 사용자는 그 컨트롤을 찾다가
          못 찾고, **안 보이는 기능이 있다고 믿는다.**
          대신 **고칠 수 있다는 사실**을 말한다 — `〈127〉` 로 상세에서 고치는 길이 열렸다.

          ⭑ ⟨개정 2026-09-03 · `PLAN-SoT §9 〈296〉`-㉲ · 근거 `〈288〉`-㉴-⑹⟩ **두 번째 문장을 갈았다.**
            종전 = 「다르면 상세 화면에서 바꿀 수 있고, **바꾼 값은 계보를 고쳐도 그대로 남아요.**」
            그 문장은 **없는 컨트롤을 안내한다** — 위 주석이 금지한 바로 그 실패형이다. `〈194〉` 축자
            「사람이 고르는 것은 **부모**이고 레벨은 그 결과다 (예외 없음)」이고, 해제 13차 `〈276〉` 가
            `processingLevel` 쓰기 경로를 계약에서 걷었다. 즉 **「바꾼 값」이라는 것이 존재하지 않고**,
            계보를 고치면 가공 단계는 **반드시 따라 바뀐다.** 정본에 이 자리의 문면이 따로 없어
            `〈194〉` 축자에서 만들었다. */}
      {/* ⭑ **⟨반전 2026-09-07 · `〈194〉` 반전 · PRD-03·07·10⟩ 이 자리의 문단을 걷었다.**
          종전 = 「가공 단계는 이어 붙인 앞선 데이터에서 **자동으로 정해져요.** 다르면 상세
          화면에서 앞선 데이터를 고치면 함께 바뀌어요.」 — 그 두 문장은 **자동 보정이 규칙이던
          때**의 것이고, 미결-2 ⓐ 로 **사람이 ① 에서 고르는 값**이 되면서 둘 다 거짓이 됐다.
          ⛔ **대체 문장을 지어내지 않았다** — 이 자리가 하던 설명(어떻게 정해지는가 · 어긋나면
          어떻게 되는가)은 위 두 축자 문면이 그대로 맡는다: 안내 줄(PRD-07)과 불일치 줄(PRD-10). */}

      {/* **누르기 전에는 직접 연결이 기본 자리다** — AI 제안 영역이 화면을 선점하지 않는다.
          부른 뒤에는 결과 아래로 내려가, 제안을 훑고 나서 직접 잇는 순서가 된다. */}
      {!asked && addBlock}

      {/* `LV-2` — **부르는 주체가 사용자다.** 호출은 업로드 1건당 1회가 아니라 누른 횟수만큼. */}
      <div className="lin-ask">
        <button
          type="button"
          className="btn btn-secondary btn-sm"
          data-testid="lin-ask"
          disabled={asking || !uploadId}
          onClick={askSuggestions}
        >
          {asking ? '앞 데이터를 찾아보는 중이에요…' : asked ? 'AI 제안 다시 받기' : 'AI 제안 받기'}
        </button>
        {!asked && (
          <p className="muted" data-testid="lin-ask-note">
            앞 데이터는 <b>직접 이어 붙이는 것이 기본</b>이에요. 필요하면 AI 제안을 받아 볼 수 있어요.
          </p>
        )}
      </div>

      {asked && addBlock}

      {/* ⭑ **⟨PRD-27 · WU-B8 · 미결-6 ⓐ⟩ 「기록 없음」 선언.**
          이 체크박스가 **「모른다고 선언했다」와 「아직 안 골랐다」를 가른다** — 종전에는
          부모가 0건이면 서버가 자동으로 표시를 붙여 둘이 한 값으로 접혔다. 체크하지 않고
          등록하면 계보 상태는 `확인 필요` 이고, 체크해야 `기록 없음` 이다.
          ⛔ **Lv0 이면 칸 자체가 없다** — 판정 ⑷ 가 이미 `원천` 으로 가른다.
          ⛔ **확정 부모가 있으면 비활성이되 사라지지 않는다** — 사유 한 줄이 왜인지 말한다. */}
      {unknownVisible && (
        <div className="lin-unknown" data-testid="lin-unknown">
          <label htmlFor="lin-unknown-check">
            <input
              id="lin-unknown-check"
              type="checkbox"
              data-testid="lin-unknown-check"
              checked={ctx.lineageUnknown && !unknownDisabled}
              disabled={unknownDisabled}
              onChange={(e) => ctx.onLineageUnknownChange(e.target.checked)}
            />
            {LINEAGE_UNKNOWN_LABEL}
          </label>
          {unknownDisabled && (
            <p className="lin-unknown-why muted" data-testid="lin-unknown-why">
              {LINEAGE_UNKNOWN_DISABLED_REASON}
            </p>
          )}
        </div>
      )}
    </section>
  );
}
