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
//  - **가공 단계 Lv 를 화면이 계산하지 않는다.** 파생값이고 core 가 계산한다(`PLAN-SoT §9-⑳`).
import { useCallback, useEffect, useRef, useState } from 'react';
import type { LineageStepContext } from '../upload/types';
import {
  PARENT_ROLES,
  type AiConfidence,
  type DatasetRow,
  type LineageOrigin,
  type LineageSource,
  type LineageSuggestionResponse,
  type ParentCandidateSuggestion,
  type ParentRole,
  type ProcessingMethodSuggestion,
  type UploadLineageParent,
} from './types';
import './lineage.css';

/** 부모 관계 한 건 — 화면 상태다. 저장되지 않았고, 확인해야만 등록 요청에 실린다. */
interface ParentCard {
  key: string;
  parentDatasetId: string;
  parentDatasetName: string;
  role: ParentRole;
  /** 제안에서 온 확신도. **사람이 수정하면 `null` 이 된다** — AI 행동이 아니게 되므로. */
  confidence: AiConfidence | null;
  rationale: string | null;
  origin: LineageOrigin;
  confirmed: boolean;
  /** 사람이 직접 적은 가공 방식 → 요청의 `method`. */
  method: string;
  /** 제안을 확인·수정한 가공 방식 → 요청의 `confirmedMethodText`. 둘 다 실으면 400 이다. */
  confirmedMethodText: string | null;
  /** `수정` 을 눌러 대상을 다시 고르는 중인가. */
  picking: boolean;
}

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
  const { uploadId, onLineageProgress, onLineageParentsChange } = ctx;

  const [resp, setResp] = useState<LineageSuggestionResponse | null>(null);
  const [unavailable, setUnavailable] = useState(false);
  const [parents, setParents] = useState<ParentCard[]>([]);
  const [methods, setMethods] = useState<MethodCard[]>([]);
  const [candidates, setCandidates] = useState<DatasetRow[] | null>(null);
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

  const loadCandidates = useCallback(() => {
    if (candidates) return;
    void source
      .candidates()
      .then((rows) => setCandidates(rows))
      .catch(() => setCandidates([]));
  }, [candidates, source]);

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
      },
    ]);
  }

  function confirmMethod(m: MethodCard, targetId: string) {
    patch(targetId, { confirmedMethodText: m.text, method: '' });
    setMethods((cur) => cur.map((x) => (x.key === m.key ? { ...x, confirmed: true } : x)));
  }

  function picker(onPick: (row: DatasetRow) => void, testid: string) {
    return (
      <div className="lin-picker" data-testid={testid}>
        {candidates === null ? (
          <p className="muted">연구실 데이터를 읽는 중이에요…</p>
        ) : candidates.length === 0 ? (
          <p className="muted">고를 수 있는 연구실 데이터가 아직 없어요.</p>
        ) : (
          <ul>
            {candidates.map((row) => (
              <li key={row.datasetId}>
                <button
                  type="button"
                  className="btn btn-ghost btn-sm"
                  data-testid={`lin-pick-${row.datasetId}`}
                  onClick={() => onPick(row)}
                >
                  {row.name}
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
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
          loadCandidates();
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
                  loadCandidates();
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
      {parents.length > 0 && (
        <p className="lin-note" data-testid="lin-lv-note">
          가공 단계는 이어 붙인 앞선 데이터에서 <b>자동으로 정해져요.</b> 다르면 상세 화면에서
          앞선 데이터를 고치면 함께 바뀌어요.
        </p>
      )}

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
    </section>
  );
}
