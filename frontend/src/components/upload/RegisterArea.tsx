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
//    ⭑ ⟨19차 · PRD-28⟩ 화면이 좌우 두 칸(`up-split` · 미리보기 2 : 입력 3)으로 갈리면서
//    그 「아래」가 **오른쪽 칸 안의 아래**가 됐다. 요약 레일은 여전히 없다 — 오른쪽 칸은
//    요약이 아니라 **사람이 적는 자리**다. 좁은 폭에서는 한 칸으로 접혀 종전 배치가 된다.
//  - `데이터셋 만들기` 는 ③ 에서만. `등록 취소` 는 같은 줄 **왼쪽 끝**에 떨어뜨린다.
import { VariableTable, type VariableRow } from '../common/VariableTable';
import { useEffect, useState } from 'react';
import { PermissionGate } from '../../permission/PermissionGate';
import { QUICK_PROJECT_NOTE } from '../common/toastCopy';
import { formatExtension, formatPeriodWithInterval } from '../detail/format';
import { extensionOf } from './FileDropCard';
import { GRANULARITIES, assemble, partsFor, type PeriodParts } from './periodParts';

import {
  TOPICS,
  type LineageStepContext,
  type LineageStepRender,
  type PickedProject,
  type ProjectRow,
  type ProjectSource,
  type ProjectType,
  type UploadStatus,
} from './types';

/** 관측 간격의 단위 6값 — **정본은 DB CHECK** 다 (PRD-17 · `M-6`). */
export const INTERVAL_UNITS = ['초', '분', '시', '일', '월', '년'] as const;

export type Step = 1 | 2 | 3;

/**
 * ⑫ 「지금 할 일」 안내 3문면 — rev1 `syncFoot()` 의 등록 갈래 **축자**.
 *
 * 진행 줄이 「무슨 일이 있었나」를 말하므로 이 자리는 **「이제 무엇을 하나」만** 말한다.
 * ⚠ **문면을 단계 이름에 맞춰 고쳐 적지 않는다** — 축자가 정본이고, 어긋나는 자리는
 *    고치지 말고 보고한다(`rounds/R-A2.md §1` · 판정 없이 고치지 않는다).
 */
export const FOOT_HINTS: Record<Step, string> = {
  1: '분류를 고르고 다음에서 데이터 정보를 입력하세요',
  2: '데이터 정보를 입력하고 다음에서 연결하세요',
  3: '연결을 마쳤으면 데이터셋을 만드세요',
};

/** ① 분석이 안 끝났을 때의 안내 — rev1 `syncFoot()` 의 장면1 갈래 축자. */
export const NEXT_BLOCKED_HINT = '분석이 끝나면 다음으로 넘어갈 수 있어요';

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
function AutoField(props: { label: string; value: string; testId?: string }) {
  return (
    <div className="form-row">
      <label>
        {props.label}
        <span className="autotag">자동</span>
      </label>
      <input
        className="inp mono"
        type="text"
        readOnly
        value={props.value}
        {...(props.testId ? { 'data-testid': props.testId } : {})}
      />
    </div>
  );
}

/**
 * 최소 단위가 연 칸들 한 줄 (PRD-18 · docx `D-2-1` 축자 요구).
 *
 * **자리마다 칸 하나다** — 한 칸에 `2025-06-01 00:00` 을 통째로 받으면 「어느 자리까지
 * 말하는가」가 다시 사람의 타이핑에 맡겨진다. 그것이 최소 단위를 세운 이유와 어긋난다.
 * 비운 하위 자리는 **저장할 때** 채워진다(`assemble`) — 화면이 미리 0 을 적어 넣지 않는다.
 */
function PartRow(props: {
  side: 'start' | 'end';
  sideLabel: string;
  parts: PeriodParts;
  open: readonly { key: keyof PeriodParts; label: string; width: 2 | 4 }[];
  onChange: (v: PeriodParts) => void;
}) {
  return (
    <span className="partrow" data-testid={`reg-period-${props.side}-parts`}>
      <span className="pr-side">{props.sideLabel}</span>
      {props.open.map((spec) => (
        <span className="pr-cell" key={spec.key}>
          <input
            id={`reg-period-${props.side}-${spec.key}`}
            className="inp pr-in"
            type="text"
            inputMode="numeric"
            maxLength={spec.width}
            size={spec.width}
            aria-label={`${props.sideLabel} ${spec.label}`}
            data-testid={`reg-period-${props.side}-${spec.key}`}
            value={props.parts[spec.key]}
            onChange={(e) => props.onChange({ ...props.parts, [spec.key]: e.target.value })}
          />
          <span className="pr-unit">{spec.label}</span>
        </span>
      ))}
    </span>
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
  variables: VariableRow[];
  onVariables: (v: VariableRow[]) => void;
  onVariablesBlocked: (message: string) => void;
  periodStart: string;
  onPeriodStart: (v: string) => void;
  periodEnd: string;
  onPeriodEnd: (v: string) => void;
  crs: string;
  onCrs: (v: string) => void;
  // ⭑ **⟨19차 해제 · PRD-18⟩ 기간의 최소 단위와 그 단위가 여는 칸.**
  granularity: string;
  onGranularity: (v: string) => void;
  startParts: PeriodParts;
  onStartParts: (v: PeriodParts) => void;
  endParts: PeriodParts;
  onEndParts: (v: PeriodParts) => void;
  // ⭑ **⟨19차 해제 · PRD-17⟩ 관측 간격 — 숫자 한 칸 ＋ 단위 셀렉트.**
  intervalValue: string;
  onIntervalValue: (v: string) => void;
  intervalUnit: string;
  onIntervalUnit: (v: string) => void;
  nameError: boolean;
  summaryError: boolean;
}) {
  const bodies = (props.status?.files ?? []).filter((f) => f.kind === '본체');
  // 조각의 확장자는 **데이터셋당 1값**이다 (`P-5` · PRD-32) — 첫 조각이 곧 전체다.
  const extension = extensionOf(bodies[0]?.fileName ?? '');
  const sliced = bodies.length > 1;
  const bytes = bodies.reduce((s, f) => s + f.byteSize, 0);
  // 조각이 여러 건이면 용량은 `조각 합계`, 기간은 `조각 합집합` 으로 라벨을 바꿔 단다 (§8).
  const sizeLabel = sliced ? '용량 (조각 합계)' : '용량';
  const periodLabel = sliced ? '기간 (조각 합집합)' : '기간';
  // 고른 단위가 여는 칸. **빈 배열 = 미지정**이고 그때는 종전 날짜 칸 두 개를 쓴다.
  const openParts = partsFor(props.granularity);

  // 관측 간격 — **반쪽인가.** 한쪽만 채워지면 서버가 400 이다(pair 규율).
  const rawValue = props.intervalValue.trim();
  const half = rawValue.length > 0 !== props.intervalUnit.length > 0;
  const previewInterval =
    rawValue.length > 0 && props.intervalUnit
      ? { value: Number(rawValue), unit: props.intervalUnit }
      : null;

  // 미리보기가 쓰는 기간 — 지금 열려 있는 입력 방식에서 조립한다.
  const previewStart =
    openParts.length === 0
      ? props.periodStart && `${props.periodStart}T00:00:00Z`
      : assemble(props.startParts, props.granularity);
  const previewEnd =
    openParts.length === 0
      ? props.periodEnd && `${props.periodEnd}T00:00:00Z`
      : assemble(props.endParts, props.granularity);
  const previewPeriod = previewStart
    ? { start: previewStart, end: previewEnd || null, granularity: props.granularity || null }
    : null;

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
          {/* ⭑ **⟨19차 해제 · PRD-21⟩ `포맷` 이 아니라 `확장자` 다.** rev1 축자 —
              「파일에서 읽는 값은 확장자·용량뿐이에요」. 판별 결과 문자열을 이 자리에 그리면
              `.hdf` 하나로 HDF4·HDF5 를 단정하게 된다(`P-10`·`R-09`). 조립은 상세와 **같은
              함수**가 한다 — 같은 값이 두 화면에서 다르게 적히는 자리를 만들지 않는다. */}
          <AutoField
            label="확장자"
            testId="reg-extension"
            value={extension ? formatExtension(extension, null) : ''}
          />
          <AutoField label={sizeLabel} value={bytes ? humanSize(bytes) : ''} />
          {/* ⭑ **⟨PRD-28⟩ `격자` 는 이 줄에서 빠져 아래 짧은 값 세 칸 줄로 갔다.**
              rev1 축자 = 「짧은 값 세 개(기간·좌표계·격자)는 한 줄에 넣었다. 2+1 로 갈리면
              마지막 줄이 반쯤 빈다」. 자동으로 읽는 값이라는 성질은 그대로라 `자동` 표시와
              읽기 전용은 따라간다 — 자리만 옮겼다. */}
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
            파이프라인이 채울 자리가 영영 막힌다 (`UploadModal.submit`).
            ⭑ **⟨WU-B2 · PRD-16⟩ 변수는 한 칸이 아니라 5열 표다** — 「변수 3개에 단위
            1개면 어느 변수 것인지 알 수 없다」(rev1 축자). 표 자체는 `VariableTable`
            하나이고 상세가 같은 것을 읽기 전용으로 그린다. */}
        <div className="form-row">
          <label>변수 (선택)</label>
          <VariableTable
            rows={props.variables}
            onRows={props.onVariables}
            onBlocked={props.onVariablesBlocked}
          />
        </div>
        {/* ⭑ **⟨PRD-28⟩ 짧은 값 세 개가 한 줄이다** — 기간 · 좌표계 · 격자.
            기간은 **두 칸이 한 값**이라(`DataPeriod`) 한 칸 안에서 시작~끝을 잇는다.
            ⛔ 2+1 로 갈라 두 줄로 쓰지 않는다 — 마지막 줄이 반쯤 빈다(rev1 축자). */}
        <div className="form-3" data-testid="reg-short-row">
          <div className="form-row">
            <label htmlFor="reg-period-granularity">{periodLabel} (선택)</label>
            {/* ⭑ **⟨19차 해제 · PRD-18⟩ 최소 단위 셀렉트가 기간 입력 **앞**에 선다.**
                고른 단위까지만 칸이 열린다 — `분` 이면 연·월·일·시·분 다섯이 Start/End 각각.
                **안 고른 상태(미지정)가 기본이고 정상이다** — 그때는 종전 날짜 칸 두 개
                그대로다(기존 전 행이 그 상태이고 재선택을 강제하지 않는다 · PRD-18 축자). */}
            <select
              id="reg-period-granularity"
              className="sel"
              data-testid="reg-period-granularity"
              aria-label="기간 최소 단위"
              value={props.granularity}
              onChange={(e) => props.onGranularity(e.target.value)}
            >
              <option value="">최소 단위 미지정</option>
              {GRANULARITIES.map((g) => (
                <option key={g} value={g}>
                  {g}
                </option>
              ))}
            </select>
            {openParts.length === 0 ? (
              <span className="pair">
                <input
                  id="reg-period-start"
                  className="inp"
                  type="date"
                  data-testid="reg-period-start"
                  value={props.periodStart}
                  onChange={(e) => props.onPeriodStart(e.target.value)}
                />
                <span className="tilde">~</span>
                {/* 비우면 무기한·진행 중이다 — 없는 끝을 지어내게 하지 않는다 (14차 해제). */}
                <input
                  id="reg-period-end"
                  className="inp"
                  type="date"
                  aria-label={`${periodLabel} 끝 (비우면 진행 중)`}
                  data-testid="reg-period-end"
                  value={props.periodEnd}
                  onChange={(e) => props.onPeriodEnd(e.target.value)}
                />
              </span>
            ) : (
              <>
                <PartRow
                  side="start"
                  sideLabel="시작"
                  parts={props.startParts}
                  open={openParts}
                  onChange={props.onStartParts}
                />
                <PartRow
                  side="end"
                  sideLabel="끝 (비우면 진행 중)"
                  parts={props.endParts}
                  open={openParts}
                  onChange={props.onEndParts}
                />
              </>
            )}
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
          <AutoField label="격자" value="" />
        </div>

        {/* ⭑ **⟨19차 해제 · PRD-17 · 미결-4 ⓐ⟩ 관측 간격 — 부가 정보의 선택 입력.**
            숫자 한 칸 ＋ 단위 셀렉트로 받는다. **저장은 두 칸 구조화**이고(자유 텍스트로
            접으면 「1시간 이하」 같은 조건 검색이 영영 안 선다) 화면이 `10분` 을 조립한다.
            ⛔ **등록 게이트가 아니다** — 비운 채 만들기를 눌러도 등록된다. */}
        <div className="form-row">
          <label htmlFor="reg-interval-value">관측 간격 (선택)</label>
          <span className="pair">
            <input
              id="reg-interval-value"
              className="inp"
              type="text"
              inputMode="numeric"
              data-testid="reg-interval-value"
              placeholder="예: 10분 · 1시간 · 1일"
              value={props.intervalValue}
              onChange={(e) => props.onIntervalValue(e.target.value)}
            />
            <select
              className="sel"
              aria-label="관측 간격 단위"
              data-testid="reg-interval-unit"
              value={props.intervalUnit}
              onChange={(e) => props.onIntervalUnit(e.target.value)}
            >
              <option value="">단위</option>
              {INTERVAL_UNITS.map((u) => (
                <option key={u} value={u}>
                  {u}
                </option>
              ))}
            </select>
          </span>
          {/* **반쪽은 서버가 400 이다** — 화면은 그 사실을 미리 알린다. 판정을 흉내 내
              막지는 않는다(문구의 정본은 서버 봉투다 · WU-A4 가 세운 규율 그대로). */}
          {half ? (
            <p className="warn" data-testid="reg-interval-half">
              숫자와 단위를 함께 적어 주세요
            </p>
          ) : null}
        </div>

        {/* ⭑ **⟨19차 해제 · PRD-35⟩ 등록 미리보기** — 상세·목록과 **같은 함수**로 그린다.
            사람이 지금 적은 값이 상세에서 어떻게 보일지를 등록 전에 보여 준다.
            간격이 비면 괄호가 없다 — 빈 괄호를 그리지 않는다. */}
        <p className="regprev" data-testid="reg-period-preview">
          {formatPeriodWithInterval(previewPeriod, previewInterval)}
        </p>
        {/* ⭑ **⟨PRD-15⟩ 설명은 필수이고 칸은 세 줄이다.**
            rev1 축자 = 「필수로 만든 칸이 한 줄이면 **짧게 쓰라는 신호**가 된다」 —
            그래서 `필수` 배지와 `textarea rows=3` 이 한 벌이다.
            ⛔ 칸 아래 안내 문구를 두지 않는다 — rev1 이 없앴다(설명 대신 칸을 키운다). */}
        <div className="form-row">
          <label htmlFor="reg-summary">
            설명
            <span className="reqtag">필수</span>
          </label>
          <textarea
            id="reg-summary"
            className="inp"
            data-testid="reg-summary"
            rows={3}
            maxLength={300}
            value={props.summary}
            onChange={(e) => props.onSummary(e.target.value)}
          />
          {props.summaryError && (
            <p className="warn" data-testid="reg-summary-error">
              설명을 적어 주세요
            </p>
          )}
        </div>
      </div>
    </div>
  );
}

/**
 * ② 소속 프로젝트 지정 — **한 표 ＋ 유형 열** (`WU-A7R` · PRD-23 개정본 · 2026-09-06 판정
 * 미결-r2-3 ⓐ 「두 패널 분리를 걷고 한 표 ＋ 유형 열로 간다」).
 *
 * 지키는 것
 *  - **표 한 장**이고 열은 `유형` · `이름` · `해제` 다. 칩이 아니라 행이고 위에서 아래로 쌓인다.
 *  - 유형 배지는 **저장값 `kind`**(`PickedProject.type`)에서 읽는다. 이름 문자열 정규식으로
 *    판정하지 않는다 — 이름이 바뀌면 배지가 틀린다(수용 기준 4행).
 *  - **0건이면 표 자체를 숨긴다.** 빈 표·빈 패널을 남기지 않는다.
 *  - `+ 새 프로젝트 만들기` 는 영역 맨 아래 **한 곳**에만 둔다. 패널마다 두면 docx image6 의
 *    실사용 오독이 두 곳으로 는다. 누르면 유형을 **먼저** 고르는 칸이 뜬다.
 *  - 계약·서버·DB 변경 0 — 유형값은 `ProjectRow.type` 에 이미 있다.
 */
export function StepTwo(props: {
  source: ProjectSource;
  picked: PickedProject[];
  onPicked: (v: PickedProject[]) => void;
}) {
  const [rows, setRows] = useState<ProjectRow[] | null>(null);
  const [sel, setSel] = useState('');
  const [dup, setDup] = useState(false);
  const [quickOpen, setQuickOpen] = useState(false);
  const [qType, setQType] = useState<ProjectType>('국가과제');
  const [qName, setQName] = useState('');
  /** 서버가 되돌린 거절 문면(이름 중복 등) — 화면이 문장을 새로 짓지 않는다 (`WU-A7R`). */
  const [qError, setQError] = useState<string | null>(null);

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
    props.onPicked([...props.picked, { projectId: row.projectId, name: row.name, type: row.type }]);
  }

  async function quickCreate() {
    if (!qName.trim()) return;
    // **거절을 삼키지 않는다** — 이름 중복(PRD-42)이 400 ＋ 축자 문면으로 온다. 문면은
    // 서버가 적어 보낸 것을 그대로 띄운다(`projectSource.create`).
    try {
      const made = await props.source.create({ type: qType, name: qName.trim() });
      setQError(null);
      props.onPicked([...props.picked, made]);
      setQName('');
      setQuickOpen(false);
    } catch (e) {
      setQError(e instanceof Error ? e.message : '프로젝트를 만들지 못했어요.');
    }
  }

  return (
    <div className="card is-on" data-testid="reg-s2">
      <div className="card-h">
        <h3>{STEP_LABELS[2]}</h3>
        <span className="sub">선택 · 여러 개 가능</span>
      </div>
      <div className="card-b">
        {/* 표 한 장 — 유형이 섞여 보이던 칩 나열을 **열**로 가른다 (`WU-A7R` · PRD-23 개정본).
            **0건이면 표가 화면에 없다** — 빈 표를 남기면 담은 것이 있는 것처럼 읽힌다. */}
        {props.picked.length > 0 && (
          <table className="projtable" data-testid="reg-proj-table">
            <thead>
              <tr>
                <th scope="col">유형</th>
                <th scope="col">이름</th>
                <th scope="col">해제</th>
              </tr>
            </thead>
            <tbody>
              {props.picked.map((p) => (
                <tr className="projrow" key={p.projectId}>
                  <td className="pr-k">
                    {/* 저장값에서 온다 — 이름 문자열로 유형을 짐작하지 않는다 */}
                    <span className="chip chip--info" data-testid="reg-proj-row-kind">
                      {p.type}
                    </span>
                  </td>
                  <td className="pr-n" data-testid="reg-proj-row-name">
                    {p.name}
                  </td>
                  <td className="pr-x">
                    <button
                      type="button"
                      className="btn btn-ghost btn-sm"
                      aria-label={`${p.name} 해제`}
                      onClick={() =>
                        props.onPicked(props.picked.filter((q) => q.projectId !== p.projectId))
                      }
                    >
                      해제
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
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
              + 새 프로젝트 만들기
            </button>
          ) : (
            <div className="qproj" data-testid="reg-proj-quick">
              <div className="qh">새 프로젝트</div>
              <div className="qf">
                <select
                  className="sel"
                  aria-label="유형"
                  value={qType}
                  onChange={(e) => setQType(e.target.value as ProjectType)}
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
              {qError && (
                <p className="warn" role="alert" data-testid="reg-proj-quick-error">
                  {qError}
                </p>
              )}
              {/* PRD-43 `J-12` — 문면은 `toastCopy.ts` 한 곳에서 온다(하드코드 중복 0건) */}
              <p className="qnote">{QUICK_PROJECT_NOTE}</p>
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
  variables: VariableRow[];
  onVariables: (v: VariableRow[]) => void;
  onVariablesBlocked: (message: string) => void;
  periodStart: string;
  onPeriodStart: (v: string) => void;
  periodEnd: string;
  onPeriodEnd: (v: string) => void;
  crs: string;
  onCrs: (v: string) => void;
  // ⭑ ⟨19차 해제 · PRD-17·18⟩ 최소 단위·자리 칸·관측 간격 — StepOne 으로 그대로 흘린다.
  granularity: string;
  onGranularity: (v: string) => void;
  startParts: PeriodParts;
  onStartParts: (v: PeriodParts) => void;
  endParts: PeriodParts;
  onEndParts: (v: PeriodParts) => void;
  intervalValue: string;
  onIntervalValue: (v: string) => void;
  intervalUnit: string;
  onIntervalUnit: (v: string) => void;
  sourceLabel: string;
  onSourceLabel: (v: string) => void;
  projects: PickedProject[];
  onProjects: (v: PickedProject[]) => void;
  nameError: boolean;
  summaryError: boolean;
  registerError: string | null;
  lineageStep?: LineageStepRender | undefined;
  lineageCtx: LineageStepContext;
  onCancel: () => void;
  onSubmit: () => void;
}) {
  const { step } = props;
  /**
   * 분석이 아직 안 끝났는가 (① · rev1 `anNext.disabled`).
   * `status` 가 아직 없으면 **접수·분석 중**이다 — 모르는 것을 끝났다고 하지 않는다.
   */
  const analyzing = !props.status?.ready;
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
            onVariablesBlocked={props.onVariablesBlocked}
            periodStart={props.periodStart}
            onPeriodStart={props.onPeriodStart}
            periodEnd={props.periodEnd}
            onPeriodEnd={props.onPeriodEnd}
            crs={props.crs}
            onCrs={props.onCrs}
            granularity={props.granularity}
            onGranularity={props.onGranularity}
            startParts={props.startParts}
            onStartParts={props.onStartParts}
            endParts={props.endParts}
            onEndParts={props.onEndParts}
            intervalValue={props.intervalValue}
            onIntervalValue={props.onIntervalValue}
            intervalUnit={props.intervalUnit}
            onIntervalUnit={props.onIntervalUnit}
            nameError={props.nameError}
            summaryError={props.summaryError}
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

      {/* ⑫ 행동 줄 — **바닥 고정**이고(고정은 CSS `.reg-actions` 가 갖는다) 왼쪽에
          「지금 할 일」 한 줄을 둔다. 분석이 안 끝났으면 그 사실이 먼저다. */}
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
        <span className="uf-hint" data-testid="reg-foot-hint">
          {analyzing ? NEXT_BLOCKED_HINT : FOOT_HINTS[step]}
        </span>
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
            /* ① 분석이 끝나기 전에는 넘어가지 않는다 — rev1 `anNext.disabled`.
               넘어가 봐야 자동으로 읽힌 값이 아직 없어 빈 칸만 보인다. */
            disabled={analyzing}
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
