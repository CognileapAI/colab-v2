// S-04 등록 단계 — 정본 §8 등록 3단계 표시기 · 등록 단계 배치 · ① 자동 메타데이터 · ② 소속 프로젝트.
//
// **③ 계보 확정의 알맹이는 이 파일이 아니다** (`components/lineage/LineageStep`).
// 여기서는 ③ 의 **자리와 표시기**까지만 만들고, 그 안은 슬롯(`lineageStep`)이 채운다.
//
// 지키는 것
//  - 번호는 등록 단계에서 `①②③` 으로 다시 시작한다. 앞 두 가지에는 번호가 없다.
//  - **한 번에 한 단계만 보인다.** 나머지 둘은 화면에서 빠진다.
//  - **막지 않는다** — 앞 단계를 채웠는지 검사하지 않는다.
//  - 등록 카드는 미리보기 **아래로 이어 붙는다.** 옆에 요약 레일을 세우지 않는다.
//  - `데이터셋 만들기` 는 ③ 에서만. `등록 취소` 는 같은 줄 **왼쪽 끝**에 떨어뜨린다.
import { useEffect, useState } from 'react';
import { PermissionGate } from '../../permission/PermissionGate';
import { TOPICS, type LineageStepContext, type LineageStepRender, type ProjectRow, type ProjectSource, type UploadStatus } from './types';

export type Step = 1 | 2 | 3;

const STEP_LABELS: Record<Step, string> = {
  1: '① 자동 메타데이터 확인',
  2: '② 소속 프로젝트 지정',
  3: '③ 계보 확정',
};

function humanSize(bytes: number): string {
  if (bytes >= 1024 ** 3) return `${(bytes / 1024 ** 3).toFixed(1)} GB`;
  if (bytes >= 1024 ** 2) return `${Math.round(bytes / 1024 ** 2)} MB`;
  return `${Math.round(bytes / 1024)} KB`;
}

/** 자동으로 읽은 칸 한 개 — 읽기 전용 + `자동` 표시. 사람이 다시 타이핑하지 않는다 (§8). */
function AutoField(props: { label: string; value: string }) {
  return (
    <div className="form-row">
      <label>
        {props.label}
        <span className="autotag">자동</span>
      </label>
      <input className="inp mono" type="text" readOnly value={props.value} />
    </div>
  );
}

function StepOne(props: {
  status: UploadStatus | null;
  name: string;
  onName: (v: string) => void;
  topic: string;
  onTopic: (v: string) => void;
  summary: string;
  onSummary: (v: string) => void;
  variables: string;
  onVariables: (v: string) => void;
  periodStart: string;
  onPeriodStart: (v: string) => void;
  periodEnd: string;
  onPeriodEnd: (v: string) => void;
  crs: string;
  onCrs: (v: string) => void;
  nameError: boolean;
}) {
  const bodies = (props.status?.files ?? []).filter((f) => f.kind === '본체');
  const sliced = bodies.length > 1;
  const bytes = bodies.reduce((s, f) => s + f.byteSize, 0);
  // 조각이 여러 건이면 용량은 `조각 합계`, 기간은 `조각 합집합` 으로 라벨을 바꿔 단다 (§8).
  const sizeLabel = sliced ? '용량 (조각 합계)' : '용량';
  const periodLabel = sliced ? '기간 (조각 합집합)' : '기간';

  return (
    <div className="card is-on" data-testid="reg-s1">
      <div className="card-h">
        <h3>{STEP_LABELS[1]}</h3>
      </div>
      <div className="card-b">
        <div className="fieldlbl">파일에서 자동으로 읽었어요</div>
        <div className="form-2" data-testid="reg-auto">
          {/* ⭑ 2026-09-02 · `#62` — 변수·기간·좌표계가 여기서 빠지고 아래 `사람이 적어요`
              로 내려갔다. 정본 `VAL-006` = 「변수·기간·좌표계는 자유 입력 · 선택 입력」이고
              `POLICY-20260825-001` 핵심규칙 1 = 「자동으로 읽는 값은 포맷과 용량뿐」이다.
              `격자` 는 여기 남는다 — 격자 파일을 붙인 뒤 서버가 세는 값이라 층이 다르고
              (`〈74〉`), 계약 `DatasetCreate` 에 적을 자리가 없다. */}
          <AutoField label="포맷" value="" />
          <AutoField label={sizeLabel} value={bytes ? humanSize(bytes) : ''} />
          <AutoField label="격자" value="" />
        </div>

        {/* §9 헤더에서 메타데이터를 읽지 못함 — 등록은 막지 않는다 */}
        {props.status?.metadataComplete === false && (
          <p className="warn" data-testid="reg-auto-failed">
            파일에서 정보를 읽지 못했어요. 기간·좌표계를 직접 적어 주세요.
          </p>
        )}

        <div className="fieldlbl">사람이 적어요</div>
        <div className="form-row">
          <label htmlFor="reg-name">데이터셋 이름</label>
          <input
            id="reg-name"
            className="inp"
            data-testid="reg-name"
            maxLength={80}
            value={props.name}
            onChange={(e) => props.onName(e.target.value)}
          />
          {props.nameError && (
            <p className="warn" data-testid="reg-name-error">
              데이터셋 이름을 적어 주세요
            </p>
          )}
        </div>
        <div className="form-2">
          <div className="form-row">
            <label htmlFor="reg-topic">주제</label>
            {/* 고정 4값. **빈 값(미정)이 정상 상태**다 — 4값 CHECK 는 「값이 있다면 넷 중 하나」다 */}
            <select
              id="reg-topic"
              className="sel"
              data-testid="reg-topic"
              value={props.topic}
              onChange={(e) => props.onTopic(e.target.value)}
            >
              <option value="">아직 고르지 않음</option>
              {TOPICS.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
          </div>
          <div className="form-row">
            <label htmlFor="reg-lv">
              가공 단계
              <span className="autotag">계보에서 자동</span>
            </label>
            {/* Lv 를 사람이 지어내지 않는다 (§8 가공 단계 칸) */}
            <input
              id="reg-lv"
              className="inp"
              type="text"
              data-testid="reg-lv"
              readOnly
              value="계보를 확정하면 정해져요"
            />
          </div>
        </div>
        {/* 변수·기간·좌표계 — **사람이 적는 자유 입력이다** (정본 스펙 18·19·20 · `VAL-006`).
            형식 검사를 하지 않는다. 비면 요청에 싣지 않는다 — 빈 값을 저장하면 나중에
            파이프라인이 채울 자리가 영영 막힌다 (`UploadModal.submit`). */}
        <div className="form-row">
          <label htmlFor="reg-variables">변수 (선택)</label>
          <input
            id="reg-variables"
            className="inp"
            data-testid="reg-variables"
            placeholder="tp · t2m 처럼 가운뎃점으로 나열해요"
            value={props.variables}
            onChange={(e) => props.onVariables(e.target.value)}
          />
        </div>
        <div className="form-2">
          <div className="form-row">
            <label htmlFor="reg-period-start">{periodLabel} 시작 (선택)</label>
            <input
              id="reg-period-start"
              className="inp"
              type="date"
              data-testid="reg-period-start"
              value={props.periodStart}
              onChange={(e) => props.onPeriodStart(e.target.value)}
            />
          </div>
          <div className="form-row">
            {/* 비우면 무기한·진행 중이다 — 없는 끝을 지어내게 하지 않는다 (14차 해제). */}
            <label htmlFor="reg-period-end">{periodLabel} 끝 (비우면 진행 중)</label>
            <input
              id="reg-period-end"
              className="inp"
              type="date"
              data-testid="reg-period-end"
              value={props.periodEnd}
              onChange={(e) => props.onPeriodEnd(e.target.value)}
            />
          </div>
        </div>
        <div className="form-row">
          <label htmlFor="reg-crs">좌표계 (선택)</label>
          <input
            id="reg-crs"
            className="inp"
            data-testid="reg-crs"
            placeholder="EPSG:5179"
            value={props.crs}
            onChange={(e) => props.onCrs(e.target.value)}
          />
        </div>
        <div className="form-row">
          <label htmlFor="reg-summary">설명 (선택)</label>
          <input
            id="reg-summary"
            className="inp"
            data-testid="reg-summary"
            maxLength={300}
            value={props.summary}
            onChange={(e) => props.onSummary(e.target.value)}
          />
        </div>
      </div>
    </div>
  );
}

function StepTwo(props: {
  source: ProjectSource;
  picked: { projectId: string; name: string }[];
  onPicked: (v: { projectId: string; name: string }[]) => void;
}) {
  const [rows, setRows] = useState<ProjectRow[] | null>(null);
  const [sel, setSel] = useState('');
  const [dup, setDup] = useState(false);
  const [quickOpen, setQuickOpen] = useState(false);
  const [qType, setQType] = useState<'국가과제' | '논문'>('국가과제');
  const [qName, setQName] = useState('');

  useEffect(() => {
    let alive = true;
    void props.source
      .list()
      .then((r) => alive && setRows(r))
      .catch(() => alive && setRows([]));
    return () => {
      alive = false;
    };
  }, [props.source]);

  const labEmpty = rows !== null && rows.length === 0;

  function add() {
    const row = (rows ?? []).find((r) => r.projectId === sel) ?? (rows ?? [])[0];
    if (!row) return;
    if (props.picked.some((p) => p.projectId === row.projectId)) {
      setDup(true);
      return;
    }
    setDup(false);
    props.onPicked([...props.picked, { projectId: row.projectId, name: row.name }]);
  }

  async function quickCreate() {
    if (!qName.trim()) return;
    const made = await props.source.create({ type: qType, name: qName.trim() });
    props.onPicked([...props.picked, made]);
    setQName('');
    setQuickOpen(false);
  }

  return (
    <div className="card is-on" data-testid="reg-s2">
      <div className="card-h">
        <h3>{STEP_LABELS[2]}</h3>
        <span className="sub">선택 · 여러 개 가능</span>
      </div>
      <div className="card-b">
        {props.picked.length > 0 ? (
          <div className="chips" data-testid="reg-proj-chips">
            {props.picked.map((p) => (
              <span className="chip chip--info" key={p.projectId}>
                {p.name}
                <button
                  type="button"
                  className="chipx"
                  aria-label={`${p.name} 빼기`}
                  onClick={() =>
                    props.onPicked(props.picked.filter((q) => q.projectId !== p.projectId))
                  }
                >
                  ×
                </button>
              </span>
            ))}
          </div>
        ) : (
          <p className="muted" data-testid="reg-proj-empty">
            아직 고른 프로젝트가 없어요.
          </p>
        )}

        {/* 연구실 프로젝트 0건 — 선택 목록과 `+ 추가` 를 끄고 빠른 생성만 남긴다 (§8) */}
        {labEmpty ? (
          <p className="muted" data-testid="reg-proj-none">
            아직 연구실에 만들어진 프로젝트가 없어요. 담지 않고 넘어가도 되고, 여기서 하나 만들어도
            돼요.
          </p>
        ) : (
          <div className="projpick">
            <select
              className="sel"
              data-testid="reg-proj-select"
              value={sel}
              onChange={(e) => setSel(e.target.value)}
            >
              {(rows ?? []).map((r) => (
                <option key={r.projectId} value={r.projectId}>
                  {r.name}
                </option>
              ))}
            </select>
            <button type="button" className="btn btn-secondary btn-sm" onClick={add}>
              + 추가
            </button>
          </div>
        )}
        {dup && (
          <p className="warn" data-testid="reg-proj-dup">
            이미 담은 프로젝트예요
          </p>
        )}

        {/* 빠른 생성 — `프로젝트 생성` 이 꺼지면 **버튼 자체를 숨긴다** (E-01 · P-12).
            **인라인을 유지하고 모달을 열지 않는다** — 전체 화면 모달 위에 모달을 또 얹지 않는다 */}
        <PermissionGate requires="프로젝트 생성">
          {!quickOpen ? (
            <button
              type="button"
              className="btn btn-ghost btn-sm"
              data-testid="reg-proj-quick-open"
              onClick={() => setQuickOpen(true)}
            >
              + 여기서 새 프로젝트 만들기
            </button>
          ) : (
            <div className="qproj" data-testid="reg-proj-quick">
              <div className="qh">새 프로젝트</div>
              <div className="qf">
                <select
                  className="sel"
                  aria-label="유형"
                  value={qType}
                  onChange={(e) => setQType(e.target.value as '국가과제' | '논문')}
                >
                  <option value="국가과제">국가과제</option>
                  <option value="논문">논문</option>
                </select>
                <input
                  className="inp"
                  aria-label="과제·논문 이름"
                  placeholder="과제·논문 이름"
                  value={qName}
                  onChange={(e) => setQName(e.target.value)}
                />
                <button
                  type="button"
                  className="btn btn-primary btn-sm"
                  onClick={() => void quickCreate()}
                >
                  만들고 담기
                </button>
                <button
                  type="button"
                  className="btn btn-ghost btn-sm"
                  onClick={() => setQuickOpen(false)}
                >
                  취소
                </button>
              </div>
              <p className="qnote">
                여기서는 유형과 이름만 받아요. 프로젝트 화면에서 나중에 채우면 돼요.
              </p>
            </div>
          )}
        </PermissionGate>
      </div>
    </div>
  );
}

function StepThree(props: {
  sourceLabel: string;
  onSourceLabel: (v: string) => void;
  lineageStep?: LineageStepRender | undefined;
  ctx: LineageStepContext;
}) {
  return (
    <div className="card is-on" data-testid="reg-s3">
      <div className="card-h">
        <h3>{STEP_LABELS[3]}</h3>
      </div>
      <div className="card-b">
        {/* 원천 표기 칸은 ③ 과 같은 단계에 함께 보인다 (§8 등록 단계 배치) */}
        <div className="form-row">
          <label htmlFor="reg-source">원천 표기 (선택)</label>
          <input
            id="reg-source"
            className="inp"
            data-testid="reg-source"
            maxLength={60}
            value={props.sourceLabel}
            onChange={(e) => props.onSourceLabel(e.target.value)}
          />
        </div>

        {/* ③ 계보 확정이 얹히는 자리. 모달이 기본으로 `LineageStep` 을 넘긴다 */}
        <div className="lineage-slot" data-testid="reg-lineage-slot">
          {props.lineageStep ? (
            props.lineageStep(props.ctx)
          ) : (
            <p className="muted">계보 확정을 열 수 없어요.</p>
          )}
        </div>
      </div>
    </div>
  );
}

export function RegisterArea(props: {
  step: Step;
  onStep: (s: Step) => void;
  fileName: string;
  lineage: { confirmed: number; total: number } | null;
  status: UploadStatus | null;
  projectSource: ProjectSource;
  name: string;
  onName: (v: string) => void;
  topic: string;
  onTopic: (v: string) => void;
  summary: string;
  onSummary: (v: string) => void;
  variables: string;
  onVariables: (v: string) => void;
  periodStart: string;
  onPeriodStart: (v: string) => void;
  periodEnd: string;
  onPeriodEnd: (v: string) => void;
  crs: string;
  onCrs: (v: string) => void;
  sourceLabel: string;
  onSourceLabel: (v: string) => void;
  projects: { projectId: string; name: string }[];
  onProjects: (v: { projectId: string; name: string }[]) => void;
  nameError: boolean;
  registerError: string | null;
  lineageStep?: LineageStepRender | undefined;
  lineageCtx: LineageStepContext;
  onCancel: () => void;
  onSubmit: () => void;
}) {
  const { step } = props;
  return (
    <div className="regarea" data-testid="reg-area">
      {/* 표시기 — 한 번에 한 단계만 보이고, 눌러서 아무 단계로나 간다 (§8) */}
      <div className="regsteps" data-testid="reg-steps">
        {([1, 2, 3] as Step[]).map((s) => (
          <button
            type="button"
            key={s}
            className={s === step ? 'is-active' : ''}
            aria-current={s === step ? 'step' : undefined}
            onClick={() => props.onStep(s)}
          >
            {STEP_LABELS[s]}
            {/* 확정할 제안이 0건이면 건수를 붙이지 않는다 — `0 / 0` 은 아무것도 말하지 않는다 */}
            {s === 3 && props.lineage && props.lineage.total > 0 && (
              <span className="cnt">
                {props.lineage.confirmed} / {props.lineage.total}
              </span>
            )}
          </button>
        ))}
        {/* 줄 끝에 등록할 파일 이름을 고정한다 (가로 720px 이하에서는 CSS 가 감춘다) */}
        <span className="rs-f" data-testid="reg-file">
          {props.fileName}
        </span>
      </div>

      <div className="up-steps">
        {step === 1 && (
          <StepOne
            status={props.status}
            name={props.name}
            onName={props.onName}
            topic={props.topic}
            onTopic={props.onTopic}
            summary={props.summary}
            onSummary={props.onSummary}
            variables={props.variables}
            onVariables={props.onVariables}
            periodStart={props.periodStart}
            onPeriodStart={props.onPeriodStart}
            periodEnd={props.periodEnd}
            onPeriodEnd={props.onPeriodEnd}
            crs={props.crs}
            onCrs={props.onCrs}
            nameError={props.nameError}
          />
        )}
        {step === 2 && (
          <StepTwo source={props.projectSource} picked={props.projects} onPicked={props.onProjects} />
        )}
        {step === 3 && (
          <StepThree
            sourceLabel={props.sourceLabel}
            onSourceLabel={props.onSourceLabel}
            lineageStep={props.lineageStep}
            ctx={props.lineageCtx}
          />
        )}
      </div>

      {props.registerError && (
        <p className="warn" role="alert" data-testid="reg-error">
          {props.registerError}
        </p>
      )}

      <div className="reg-actions" data-testid="reg-actions">
        {/* 앞으로 가는 버튼들과 나란히 붙어 있으면 잘못 눌린다 — 왼쪽 끝에 따로 (§8) */}
        <button
          type="button"
          className="btn btn-secondary up-cancel"
          data-testid="reg-cancel"
          onClick={props.onCancel}
        >
          등록 취소
        </button>
        <span className="sp" />
        {step > 1 && (
          <button
            type="button"
            className="btn btn-secondary"
            data-testid="reg-prev"
            onClick={() => props.onStep((step - 1) as Step)}
          >
            ← 이전
          </button>
        )}
        {step < 3 ? (
          <button
            type="button"
            className="btn btn-primary"
            data-testid="reg-next"
            onClick={() => props.onStep((step + 1) as Step)}
          >
            다음 →
          </button>
        ) : (
          <button
            type="button"
            className="btn btn-primary"
            data-testid="reg-done"
            onClick={props.onSubmit}
          >
            데이터셋 만들기 →
          </button>
        )}
      </div>
    </div>
  );
}
