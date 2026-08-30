// F-03 새 프로젝트 · F-04 프로젝트 정보 수정 — 목업 `프로젝트_260817.html` 의 두 모달.
//
// **한 컴포넌트다.** 목업은 둘을 따로 그렸지만 칸 구성이 같다 — 유형 · 이름 · 설명 · 기간 ·
// 연결 주소. 갈리는 것은 셋뿐이라 그것만 인자로 받는다:
//   ① 제목·확인 버튼 글자   ② 대상 블록(F-04 에만 있다)   ③ **유형을 고를 수 있는가**
// 두 벌로 나누면 「이름은 필수」·「종료가 시작보다 앞선다」 같은 규칙이 두 곳에 생겨 갈라진다.
//
// 지키는 것 —
//  · **유형은 만든 뒤에 바꾸지 않는다** (계약 `ProjectUpdate` 산문). F-04 에서는 읽기 전용이고
//    목업이 그 자리에 적어 둔 안내문("유형은 나중에 바꿀 수 없어요 …")을 그대로 보여준다.
//  · **정의·범위 안내는 새 프로젝트 모달에만 둔다** (`Policy_프로젝트 §8` 정의·범위 안내 행) —
//    「만들기 직전이 이 경계가 필요한 유일한 순간이다」. 목록 설명에 섞지 않는다.
//  · **연결 주소는 설명·기간과 다른 묶음**이다 (`§1.2`·`§8`). `계보` 표시를 붙인 카드로 뗀다.
//  · 주소 모양이 아니어도 **막지 않는다** (`§9`) — 논문 고유 번호처럼 주소가 아닌 값도 받는다.
import { useId, useState } from 'react';
import type { ProjectCreate, ProjectDetail, ProjectType, ProjectUpdate } from './types';

const TYPES: ProjectType[] = ['국가과제', '논문'];

/** `YYYY-MM` 두 칸. 계약 `ProjectPeriod` 는 연·월까지다 — 일자를 받지 않는다 (`§5`). */
type Period = { start: string; end: string };

type PeriodBody = { start: string | null; end: string | null } | null;

function periodBody(period: Period): PeriodBody {
  if (!period.start && !period.end) return null;
  return { start: period.start || null, end: period.end || null };
}

export type ProjectFormMode =
  | { kind: '새 프로젝트' }
  | { kind: '정보 수정'; detail: ProjectDetail };

export function ProjectFormModal(props: {
  mode: ProjectFormMode;
  onSubmit(input: ProjectCreate | ProjectUpdate): Promise<void>;
  onClose(): void;
}) {
  const editing = props.mode.kind === '정보 수정' ? props.mode.detail : null;
  const titleId = useId();

  const [type, setType] = useState<ProjectType>(editing?.type ?? '국가과제');
  const [name, setName] = useState(editing?.name ?? '');
  const [description, setDescription] = useState(editing?.description ?? '');
  const [period, setPeriod] = useState<Period>({
    start: editing?.period?.start ?? '',
    end: editing?.period?.end ?? '',
  });
  const [link, setLink] = useState(editing?.link ?? '');
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit() {
    // 오류 문구는 `Policy_프로젝트 §9` 의 것을 **그대로** 쓴다. 새 한국어를 만들지 않는다.
    if (!name.trim()) {
      setError('이름을 적어 주세요. 나중에 찾을 때 쓰는 유일한 이름이에요.');
      return;
    }
    if (period.start && period.end && period.end < period.start) {
      setError('종료가 시작보다 앞서요. 다시 골라 주세요.');
      return;
    }
    setError(null);
    setBusy(true);
    try {
      const common = {
        name: name.trim(),
        description: description.trim() || null,
        period: periodBody(period),
        link: link.trim() || null,
      };
      // **`type` 은 수정 본문에 넣지 않는다** — 계약이 그 열쇠를 갖고 있지 않고,
      // 서버는 계약에 없는 필드를 400 으로 되돌린다 (`routes/project.py::update_project`).
      await props.onSubmit(editing ? common : { ...common, type });
      props.onClose();
    } catch (e) {
      setError(e instanceof Error ? e.message : '저장하지 못했어요.');
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="pj-modal-back" data-testid="project-form-modal">
      <div className="pj-modal" role="dialog" aria-modal="true" aria-labelledby={titleId}>
        <div className="pj-modal-h">
          <h3 id={titleId}>{props.mode.kind === '새 프로젝트' ? '새 프로젝트' : '프로젝트 정보 수정'}</h3>
          <button type="button" className="pj-x" onClick={props.onClose} aria-label="창 닫기">
            ×
          </button>
        </div>

        <div className="pj-modal-b">
          {/* F-04 대상 블록 — 무엇을 고치고 있는지가 폼 위에 먼저 보인다 (목업 `target`) */}
          {editing ? (
            <div className="pj-target" data-testid="project-form-target">
              <div className="pj-tn">{editing.name}</div>
              <div className="pj-tm">
                {editing.type} · 데이터셋 {editing.datasets.length}개
              </div>
            </div>
          ) : null}

          <div className="pj-row">
            <label htmlFor={`${titleId}-type`}>유형</label>
            {editing ? (
              // 읽기 전용이다 — 만든 뒤에는 바꾸지 않는다 (계약 산문).
              <p className="pj-readonly" data-testid="project-form-type-fixed">
                {editing.type}
              </p>
            ) : (
              <div className="pj-seg" id={`${titleId}-type`}>
                {TYPES.map((t) => (
                  <button
                    key={t}
                    type="button"
                    className={t === type ? 'on' : ''}
                    aria-pressed={t === type}
                    onClick={() => setType(t)}
                  >
                    {t}
                  </button>
                ))}
              </div>
            )}
          </div>

          <div className="pj-row">
            <label htmlFor={`${titleId}-name`}>이름</label>
            <input
              id={`${titleId}-name`}
              className="pj-inp"
              value={name}
              maxLength={100}
              placeholder="예: 낙동강 유역 홍수기 강우-유출 응답 분석"
              onChange={(e) => setName(e.target.value)}
            />
          </div>

          {/* **만들기 직전이 이 경계가 필요한 유일한 순간이다** (§8) — 수정에는 두지 않는다 */}
          {editing ? null : (
            <p className="pj-defnote" data-testid="project-form-scope-note">
              프로젝트 1건은 국가과제 또는 논문 1건이에요. 여러 연구실이 함께 하는 공동연구는
              아직 지원하지 않아요.
            </p>
          )}

          <div className="pj-row">
            <label htmlFor={`${titleId}-desc`}>설명</label>
            <textarea
              id={`${titleId}-desc`}
              className="pj-tarea"
              value={description}
              maxLength={500}
              placeholder="이 과제·논문이 무엇인지 몇 줄로 적어 주세요."
              onChange={(e) => setDescription(e.target.value)}
            />
          </div>

          <div className="pj-row">
            <label htmlFor={`${titleId}-start`}>기간</label>
            <div className="pj-2col">
              <input
                id={`${titleId}-start`}
                className="pj-inp"
                type="month"
                value={period.start}
                onChange={(e) => setPeriod((p) => ({ ...p, start: e.target.value }))}
              />
              <span className="pj-tilde">~</span>
              <input
                className="pj-inp"
                type="month"
                aria-label="종료"
                value={period.end}
                onChange={(e) => setPeriod((p) => ({ ...p, end: e.target.value }))}
              />
            </div>
            <p className="pj-hint">진행 중이면 종료를 비워 둬도 돼요.</p>
          </div>

          {/* 설명·기간과 **다른 묶음**이다 (§1.2·§8). 그것이 이 화면의 중심 결정이다. */}
          <div className="pj-fgroup" data-testid="project-form-link-group">
            <div className="pj-fgroup-h">
              <span className="t">성과와 잇는 자리</span>
              <span className="chip chip--lineage">계보</span>
            </div>
            <div className="pj-row">
              <label htmlFor={`${titleId}-link`}>연결 주소</label>
              <input
                id={`${titleId}-link`}
                className="pj-inp"
                value={link}
                maxLength={500}
                placeholder="논문 주소 · 논문 고유 번호 · 과제 공고 주소"
                onChange={(e) => setLink(e.target.value)}
              />
              {/* 주소 모양을 **검사하지 않는다** (§9) — 받아 적기만 한다 (§1.3-3) */}
              <p className="pj-hint">받아 적기만 해요 — 나중에 붙여도 돼요.</p>
            </div>
          </div>

          {editing ? (
            <p className="pj-muted">
              유형은 나중에 바꿀 수 없어요 — 잘못 골랐으면 새로 만들고 이 프로젝트를 닫아 주세요.
            </p>
          ) : null}

          {error ? (
            <p className="pj-err" role="alert" data-testid="project-form-error">
              {error}
            </p>
          ) : null}
        </div>

        <div className="pj-modal-f">
          <button type="button" className="btn btn-secondary" onClick={props.onClose}>
            취소
          </button>
          <button type="button" className="btn btn-primary" disabled={busy} onClick={() => void submit()}>
            {editing ? '저장' : '만들기'}
          </button>
        </div>
      </div>
    </div>
  );
}
