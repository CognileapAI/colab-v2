// ③ 계보 확정 — 정본 `Policy_업로드와_계보_확정.md` §8 「가공 단계 칸」.
//
// 이 화면이 지키는 것 (`P2-EXEC §4` · `P2.md §2-9`)
//  - ⭑ **⟨개정 2026-09-14 · 기획자 9/13 피드백 「반쪽 AI 제거」 · Ted 재판정 대기 · 판정문 ㉮⟩
//    이 화면에 **AI 제안 영역이 없다.** 앞 데이터는 **사람이 직접 고르는 것 하나**다.
//    ／ 종전 ~~「뒤진 범위를 먼저 밝힌다」·「[모두 승인] 이 없다」·「확신도는 `확실|애매|모름`
//    enum 이고 근거는 필수」·「사람이 `수정` 하면 AI 행동이 아니다」·「제안 0건은 정직한
//    빈 상태」·「AI 제안은 사용자가 눌러 받는 보조다(`PLAN-SoT §9 〈197〉`·`〈203〉` · `LV-2`)」~~
//    — 그 여섯은 **제안이 이 화면에 있던 때**의 규율이다. 제안이 없으면 지킬 대상도 없다.
//    ⚠ **계약·서비스는 그대로다** — `listUploadLineageSuggestions` 엔드포인트와
//    `LineageSource.suggestions` 중계는 남아 있고, **부르는 자리가 사라졌을 뿐이다.**
//    ⛔ 그래서 규율 여섯을 **지운 것이 아니라 적용 대상이 0건**이 됐다 — 판정이 뒤집혀
//    제안이 돌아오면 이 문단째 되살린다.
//  - **AI 없이도 v2 는 완결된 제품이다** (`CLAUDE.md §3`). 이 화면이 그 성질의 끝이다.
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
import { useEffect, useState } from 'react';
import type { LineageStepContext } from '../upload/types';
import {
  levelOf,
  displayLevel,
  derivedLevelFromParents,
  levelMismatchNotice,
  DEFAULT_PARENT_ROLE,
  type ParentCandidateRow,
  type LineageSource,
  type ParentCard,
  type UploadLineageParent,
} from './types';
// ⭑ **⟨WU-B10 · PRD-31⟩ 찾기·연결 UI 와 초과 사유 문면은 `ParentPicker` 한 벌뿐이다** —
//   상세 계보 모달(`LineageFixModal`)이 **같은 컴포넌트·같은 함수**를 부른다. 종전에는 이
//   화면 안의 `picker()`·`overReason()` 이 유일본이었고, 모달이 사본을 뜨면 PRD-07·08·09 의
//   규칙이 두 벌이 된다.
import { ParentPicker, parentOverReason, parentPeriodLabel } from './ParentPicker';
import { useParentCandidates } from './useParentCandidates';
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


export function LineageStep(props: { source: LineageSource; ctx: LineageStepContext }) {
  const { source, ctx } = props;
  // ⭑ ⟨개정 2026-09-14⟩ `uploadId` 를 더 쓰지 않는다 — **제안 조회의 인자였고** 그 조회가
  //   사라졌다. `ctx.uploadId` 는 계약(`LineageStepContext`)에 그대로 남는다.
  const { onLineageProgress, onLineageParentsChange, onLineageConflictChange } = ctx;
  // ⭑ **⟨WU-B5 · PRD-09⟩ 연결 카드는 모달이 쥔다** — 이 화면은 단계 이동 때마다
  //   언마운트되므로 여기 `useState` 로 두면 ① 에 다녀오는 순간 연결이 사라진다.
  const parents = ctx.parents;
  const setParents = ctx.onParentsChange;
  /** ① 에서 고른 자기 Lv. **기준값**이고, 안 골랐으면 `null` 이라 규칙이 서지 않는다. */
  const selfLv = levelOf(ctx.processingLevelUserSet);
  /**
   * ⭑ **⟨R-LTH-REVIEW-1 · 카드 ⑩ ⓐ 「차단은 늘지 않는다」⟩ 부모 선택 상한의 기준 Lv.**
   * 자기 Lv 가 계산값을 따라가는 중이면 `null` — 상한·사후 충돌을 걸지 않는다(부모를 확인하면
   * 자기 Lv 가 최대 부모 Lv ＋ 1 로 따라간다). 사람이 고른 뒤에는 `selfLv` 그대로다.
   * ⚠ 불일치 줄·「기록 없음」 표시는 `selfLv` 를 쓴다 — 여기서 바꾸지 않는다. 상한 안내 줄(`lin-lv-scope`)은
   *   추종 중에는 상한이 없으므로 서지 않는다(대체 문면 없음) — 사람이 고른 뒤에는 `selfLv` 문면 그대로다.
   */
  const ceilingLv = ctx.processingLevelFollowsDerived ? null : selfLv;
  /**
   * ⭑ **⟨PRD-27 · WU-B8⟩ 「기록 없음」 체크박스의 두 성질.**
   *  · **확정 부모 ≥1 → 비활성 ＋ 사유 한 줄.** 칸은 **사라지지 않고** 연결도 지우지 않는다.
   *  · **자기 Lv 가 `Lv0` → 보이지 않는다.** 판정 ⑷ 가 이미 `원천` 으로 가르므로 물을 것이
   *    없다 — 물으면 「원시 데이터인데 왜 못 찾았냐고 묻나」가 된다.
   */
  const confirmedParentCount = parents.filter((p) => p.confirmed).length;
  const unknownDisabled = confirmedParentCount > 0;
  const unknownVisible = selfLv !== 0;

  const {
    candidates,
    candidateError,
    nextCursor,
    loadingMore,
    loadMoreError,
    loadCandidates,
    loadMore,
    retry,
  } = useParentCandidates(source);
  /** 찾기 모달의 가공 단계 셀렉트. `null` = 전체 (PRD-08). */
  const [levelFilter, setLevelFilter] = useState<number | null>(null);
  const [adding, setAdding] = useState(false);

  // 확인된 것만 위로 올린다. 여기가 「사람이 확인한 것만 커밋된다」의 화면 쪽 끝이다.
  useEffect(() => {
    const out: UploadLineageParent[] = parents
      .filter((p) => p.confirmed)
      .map((p) => ({
        parentDatasetId: p.parentDatasetId,
        // ⭑ **⟨개정 2026-09-14 · 레인 A6⟩ 계약 기본값을 고정해 싣는다.**
        //   ／ 종전 ~~카드의 셀렉트가 고른 `p.role`~~ — 그 셀렉트가 없어졌다(목업 `.li-f`).
        //   ⛔ **필드를 빼지 않는다** — 계약에 그대로 있는 값이고, 서버 기본값에 기대면
        //   요청만 보고는 무엇이 실렸는지 읽히지 않는다.
        parentRole: DEFAULT_PARENT_ROLE,
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

  /** 셀렉트 상태를 보존한다. 실제 조회는 `ParentPicker.onSearch`가 모든 조건을 함께 보낸다. */
  function changeLevelFilter(next: number | null) {
    setLevelFilter(next);
  }

  /**
   * ⭑ **⟨PRD-09⟩ 사후 충돌 건수.** 확인된 부모 중 자기 Lv 를 넘는 것.
   * **연결을 지우지 않는다** — 세기만 하고, 막는 것은 `데이터셋 만들기` 버튼 하나다.
   */
  const conflicts = parents.filter(
    (p) => ceilingLv !== null && p.parentLevel !== null && p.parentLevel > ceilingLv,
  );

  useEffect(() => {
    onLineageConflictChange(conflicts.length);
  }, [conflicts.length, onLineageConflictChange]);

  /**
   * 파생 Lv **미리보기** — 확인된 부모의 표시 Lv 중 최대 + 1, 상한 3(`LV_CAP`).
   * ⚠ **판정이 아니다.** 등록 전에는 서버가 계산한 값이 없어(데이터셋이 아직 없다)
   *   화면이 같은 식으로 미리 보여 줄 뿐이고, 저장 뒤의 정본은 응답의
   *   `processingLevelDerived` 다. 부모 Lv 를 하나라도 모르면 미리보기를 만들지 않는다.
   *
   * ⭑ **⟨R-LTH-REVIEW-1 · spec §6 ㉱⟩ 식의 자리가 `common/processingLevel.ts` 로 옮겨졌다** —
   *   ① 분류의 **기본 선택값**이 같은 식을 따르므로(`UploadModal`) 두 자리가 한 함수를 부른다.
   */
  const derivedPreview = derivedLevelFromParents(parents);
  const mismatch = selfLv !== null && derivedPreview !== null && derivedPreview !== selfLv;

  function patch(key: string, next: Partial<ParentCard>) {
    setParents((cur) => cur.map((p) => (p.key === key ? { ...p, ...next } : p)));
  }

  /**
   * ⭑ **⟨개정 2026-09-14 · 기획서 rev2 목업 `pickFind()`⟩ 고른 순간 카드가 서고 그것이 곧
   *   확정이다** (`confirmed: true`). ／ 종전 ~~`confirmed: false` 로 세우고 카드의 `확인`
   *   버튼이 확정했다~~ — 목업 `.li-act` 에 그 버튼이 없다.
   * ⚠ **「사람이 확인한 것만 커밋된다」가 무너진 것이 아니다** — 고르는 행위 자체가 사람의
   *   확인이고, 화면에는 AI 제안이 0건이다(`판정문 ㉮`).
   * 가공 방식은 여기서 받지 않는다 — **카드 안의 칸**이 빈 값에서 시작한다.
   */
  function addParent(row: ParentCandidateRow) {
    setAdding(false);
    setParents((cur) => [
      ...cur,
      {
        key: `직접:${row.datasetId}:${cur.length}`,
        parentDatasetId: row.datasetId,
        parentDatasetName: row.name,
        confidence: null,
        rationale: null,
        origin: 'manual',
        confirmed: true,
        method: '',
        confirmedMethodText: null,
        // 후보 줄이 들고 온 표시 Lv — 사후 충돌을 재는 값이다(PRD-09).
        // ⭑ ⟨WU-C9⟩ 표시 규칙은 네 자리와 같은 `displayLevel` 이다.
        parentLevel: displayLevel(row),
        // 목업 `.li-sub` 가 되읽는 두 값. 후보 줄과 **같은 출처**라 문면이 갈리지 않는다.
        parentCategory: 'category' in row ? row.category : null,
        parentPeriod: 'period' in row ? row.period : null,
      },
    ]);
  }

  function picker(onPick: (row: ParentCandidateRow) => void, testid: string) {
    return (
      <ParentPicker
        selfLv={ceilingLv}
        candidates={candidates}
        error={candidateError}
        onRetry={retry}
        onClose={() => setAdding(false)}
        levelFilter={levelFilter}
        onLevelFilterChange={changeLevelFilter}
        onSearch={loadCandidates}
        nextCursor={nextCursor}
        loadingMore={loadingMore}
        loadMoreError={loadMoreError}
        onLoadMore={loadMore}
        onPick={(row) => { onPick(row); setAdding(false); }}
        testId={testid}
      />
    );
  }

  /** 직접 연결 — **이 화면의 유일한 연결 경로**다 (AI 제안 영역이 사라졌다). */
  const addBlock = (
    <div className="lin-add">
      {/**
        * 연결 0건 빈 상태 — 기획서 rev2 `#linHint` 축자. **버튼 바로 위**다.
        * ⭑ ⟨개정 2026-09-14⟩ 종전 주석이 가르던 상대(`lin-empty` — 「살펴봤는데 없었다」)는
        * 제안과 함께 사라졌다. 이 줄은 **아직 아무것도 잇지 않았다**는 사실만 말한다.
        */}
      {parents.length === 0 && (
        <p className="lin-hint" data-testid="lin-hint">아직 연결한 가공 전 데이터가 없어요</p>
      )}
      <button
        type="button"
        className="btn btn-secondary btn-sm"
        data-testid="lin-add"
        onClick={() => {
          loadCandidates({
            ...(levelFilter !== null ? { processingLevel: levelFilter } : {}),
            limit: 25,
          });
          setAdding((v) => !v);
        }}
      >
        + 가공 전 데이터 추가
      </button>
      {adding && picker(addParent, 'lin-picker')}
    </div>
  );

  return (
    <section className="lin" data-testid="lin-step">
      {/* ⭑ **⟨PRD-07⟩ 연결 규칙 안내 — 이 단계의 맨 위다.** 문면은 rev1 축자이고
          `분류에서 바꾸기` 는 ① 로 데려가는 길이다. ⛔ **자기 Lv 를 여기서 바꾸지 않는다.**
          자기 Lv 를 아직 안 골랐으면(`null`) 기준값이 없어 이 줄이 서지 않는다.
          ⭑ ⟨R-LTH-REVIEW-1 · 카드 ⑩ ⓐ⟩ 계산값을 따라가는 중(`ceilingLv === null`)에도 서지 않는다 —
          상한이 풀려 있어 「…만 연결할 수 있어요」가 없는 제한을 말하게 된다. */}
      {selfLv !== null && ceilingLv !== null && (
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
          {/* ⭑ ⟨R-LTH-REVIEW-1 · ㉲⟩ 문면은 공용 함수 하나다 — 상세 헤더가 같은 것을 부른다. */}
          {levelMismatchNotice(selfLv as number, derivedPreview as number)}
        </p>
      )}

      {/* ⭑ ⟨개정 2026-09-14 · 기획자 9/13 · 판정 대기⟩ 이 자리에 있던 **제안 안내 넷**
          (`lin-scope` 뒤진 범위 · `lin-unavailable` 조회 실패 · `lin-degraded` 부분 응답 ·
          `lin-raw` 원자료 추정)을 걷었다. **넷 다 제안 응답에서만 나오던 값**이고, 부를
          자리가 없어져 그릴 값 자체가 없다. ⛔ 문면을 다른 자리로 옮기지 않았다 —
          제안이 돌아오면 이 넷도 함께 돌아온다. */}
      <div className="lin-cards" data-testid="lin-cards">
        {parents.map((p) => {
        // 목업 `.li-sub` 한 줄 = 분류 · 기간. 둘 다 모르면 줄 자체를 세우지 않는다.
        const info = [p.parentCategory ?? null, parentPeriodLabel(p.parentPeriod)]
          .filter(Boolean)
          .join(' · ');
        return (
          <div className="lin-card" data-testid="lin-card" key={p.key}>
            {/* ⭑ **⟨개정 2026-09-14 · 목업 `.li-top`⟩ 머리 = 종류 · 이름 · Lv · `직접 연결`.**
                ／ 종전 ~~이름 ＋ `확인함`~~ — `확인함` 은 `확인` 버튼의 상태였고 그 버튼이 없다. */}
            <div className="lin-h">
              <span className="lin-kind">가공 전 데이터</span>
              <span className="lin-name" data-testid="lin-card-name">{p.parentDatasetName}</span>
              {p.parentLevel !== null && (
                <span className="lin-lv" data-testid="lin-card-lv">Lv{p.parentLevel}</span>
              )}
              <span className="lin-manual">직접 연결</span>
              {/* ⭑ **⟨PRD-09⟩ 사후 충돌 표시.** 연결은 남고 이 칩만 붙는다 —
                  되돌리면 칩이 사라지고 `데이터셋 만들기` 가 다시 눌린다. */}
              {ceilingLv !== null && p.parentLevel !== null && p.parentLevel > ceilingLv && (
                <span className="chip chip--warning" data-testid="lin-need-check">
                  확인 필요
                </span>
              )}
            </div>

            {info && (
              <p className="lin-card-info" data-testid="lin-card-info">{info}</p>
            )}

            {/* ⭑ ⟨개정 2026-09-14⟩ 확신도 칩(`lin-confidence`)과 근거 줄(`lin-rationale`)을
                걷었다 — **둘 다 제안만 채우던 칸**이고, 사람이 직접 고른 연결에는 값이 없다.
                `ParentCard.confidence`·`rationale` 은 계약 타입이라 그대로 두고 `null` 이다. */}

            {/* ⭑ **⟨개정 2026-09-14 · 레인 A6 · 사용자 결정⟩ 부모 역할 셀렉트(`lin-role`)를 걷었다.**
                목업 `.li-f` 에 그 칸이 없다. 업로드 화면은 역할을 묻지 않고 요청에는
                계약 기본값 `주입력` 이 고정으로 실린다(`DEFAULT_PARENT_ROLE`).
                ⛔ **고치는 길은 남아 있다** — 상세의 계보 수정(`LineageFixModal`)이 그 자리다.
                ⚠ 계약(`UploadLineageParent.parentRole`)·DB 는 무변이다. */}
            <div className="lin-f">
              {/* ⭑ ⟨개정 2026-09-14⟩ 가공 방식은 **사람이 적는 칸 하나**다.
                  ／ 종전 ~~제안을 확인한 문장이 있으면 `lin-method-done` 으로 대신 그렸다~~ —
                  `confirmedMethodText` 를 채우던 것은 가공 방식 제안 카드뿐이고 그것이
                  사라졌다. 요청은 `method` 한 자리로만 실린다(둘 다 실으면 400 이다). */}
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
            </div>

            {/* ⭑ **⟨개정 2026-09-14 · 목업 `.li-act`⟩ 버튼은 `지우기` 하나다.**
                ／ 종전 ~~`확인`·`수정`·`거절` 셋~~ — `확인` 은 연결 자체가 대신하고,
                `수정` 의 자리는 **지우고 다시 고르기**이며, `거절` 의 이름이 `지우기` 다.
                ⛔ **묶음 승인 버튼은 여전히 없다.** */}
            <div className="lin-a">
              <button
                type="button"
                className="btn btn-ghost btn-sm"
                data-testid="lin-del"
                onClick={() => setParents((cur) => cur.filter((x) => x.key !== p.key))}
              >
                지우기
              </button>
            </div>
          </div>
        );
        })}

        {/* ⭑ ⟨개정 2026-09-14⟩ 가공 방식 **제안 카드**(`lin-method-card`)를 걷었다 —
            그 카드는 제안 응답의 `가공 방식` 항목만으로 생겼다. 가공 방식 자체는 남아 있고,
            **사람이 관계마다 직접 적는다**(위 `lin-method` 칸). */}
      </div>

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

      {/* ⭑ ⟨개정 2026-09-14 · 기획자 9/13 · 판정 대기⟩ 직접 연결이 **이 자리 하나**다.
          ／ 종전 ~~`{!asked && addBlock}` ＋ `lin-ask` 버튼(`AI 제안 받기`·안내문 `lin-ask-note`)
          ＋ `{asked && addBlock}`~~ — 제안을 부르기 전후로 자리를 옮기던 구성이고, 부를 것이
          없어져 **자리가 하나로 합쳐졌다.** */}
      {addBlock}

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
