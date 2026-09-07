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
import {
  ACCESS_LABEL,
  ACCESS_NOTE,
  ACCESS_STATES,
  LAB_DEFAULT_LABEL,
  LAB_DEFAULT_NOTE,
  type AccessState,
} from '../common/accessState';
import { PermissionGate } from '../../permission/PermissionGate';
import { QUICK_PROJECT_NOTE } from '../common/toastCopy';
import { formatExtension, formatPeriodWithInterval } from '../detail/format';
import { extensionOf } from './FileDropCard';
import { EMPTY_PARTS, assemble, type PeriodParts } from './periodParts';
import { PeriodCalendarPopover } from './PeriodCalendarPopover';
import {
  CATEGORIES,
  DATA_TYPES,
  PROCESSING_LEVELS,
  bilingual,
  findAxis,
  type AxisValue,
} from './axisDict';

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

/**
 * 등록 3단계 (PRD-12) — 「분류 체계와 자유 입력은 성격이 다르고, 가공 단계가 뒤 논리를
 * 좌우해 가장 먼저 정해야 한다」. 종전 세 라벨(`자동 메타데이터 확인`·`소속 프로젝트 지정`·
 * `계보 확정`)은 단계 수만 같았고 내용물이 전부 달랐다.
 */
export const STEP_LABELS: Record<Step, string> = {
  1: '① 분류',
  2: '② 메타데이터 입력',
  3: '③ 연결',
};

/** 카드 부제 두 줄 — rev2 `card-h .sub` 축자. */
export const CLASSIFY_SUBTITLE = '목록 필터가 이 세 축을 그대로 받아요';
export const METADATA_SUBTITLE = '파일에서 읽는 값은 확장자·용량뿐이에요';

/** PRD-40 · 판정 ⓐ — 종료 칸의 안내 한 줄. rev2 `prVe` 자리 문면 축자. */
export const PERIOD_SINGLE_POINT_HINT = '한 시점이면 비워 둬요';

/**
 * ⭑ **⟨WU-B6 · PRD-19⟩ Lv0 전용 출처 블록의 문면 — rev1 축자다.**
 *
 * 「원시 데이터라 부모가 없어요」가 이 블록이 서는 이유다: Lv0 은 부모가 없어 **계보로는
 * 출처를 말할 수 없고**, 그 자리를 두 칸이 메운다.
 * ⛔ **`필수` 배지를 붙이지 않는다** — 두 칸은 선택 입력이다. rev2 목업이 필수 배지를
 *    그렸으나 **정본은 「선택 입력」이고 목업 배지를 채택하지 않는다**(PRD-19 감사 교차 확인).
 */
export const LV0_SOURCE_NOTICE = '원시 데이터라 부모가 없어요. 대신 어디서 언제 받았는지를 남겨요.';
export const LV0_SOURCE_URL_PLACEHOLDER = '예: https://cds.climate.copernicus.eu/...';
export const LV0_SOURCE_DATE_PLACEHOLDER = '예: 2026-08-20';
/** 이 블록이 열리는 유일한 조건 — ① 이 고른 자기 Lv 다. 파생 Lv 가 아니다. */
export const LV0 = 'Lv0';

/**
 * 축 값 하나의 정의 줄 (PRD-04 축자 형식) — `<b>{정의}</b> · 예: {예시}`.
 * 가공 단계만 뒤에 줄을 바꿔 부가 안내를 덧붙인다.
 */
function AxisDefLine(props: { value: AxisValue | null; testId: string; withExtra?: boolean }) {
  if (!props.value) return null;
  return (
    <p className="axis-def" data-testid={props.testId}>
      <b>{props.value.def}</b> · 예: {props.value.example}
      {props.withExtra ? (
        <>
          <br />
          {props.value.extra}
        </>
      ) : null}
    </p>
  );
}

/**
 * ① 분류 — 세 축(분류·유형·가공 단계)을 고르는 첫 단계 (PRD-12 · 04 · 33 ⑴).
 *
 * 지키는 것
 *  - 셋 다 **필수**이고 셋 다 **기본 선택값**이 있다(`기상·기후 인자`·`재분석자료`·`Lv2`).
 *  - 옵션 표기는 **국문＋영문 병기**, 저장값은 **국문 단일**이다(미결-13 ⓐ).
 *  - 유형 아래 한 줄 더 — `참고 · {특이사항 및 주의점}` (PRD-33 ⑴). **저장을 막지 않는다.**
 *  - ⛔ 유형↔가공 단계 조합 검증을 만들지 않는다(미결-14 ⓐ).
 */
function StepClassify(props: {
  category: string;
  onCategory: (v: string) => void;
  dataType: string;
  onDataType: (v: string) => void;
  level: string;
  onLevel: (v: string) => void;
}) {
  const cat = findAxis(CATEGORIES, props.category);
  const type = findAxis(DATA_TYPES, props.dataType);
  const lv = findAxis(PROCESSING_LEVELS, props.level);
  return (
    <div className="card is-on" data-testid="reg-s1">
      <div className="card-h">
        <h3>{STEP_LABELS[1]}</h3>
        <span className="sub" data-testid="reg-s1-sub">
          {CLASSIFY_SUBTITLE}
        </span>
      </div>
      <div className="card-b">
        <div className="form-row">
          <label htmlFor="reg-category">
            분류
            <span className="reqtag">필수</span>
          </label>
          <select
            id="reg-category"
            className="sel"
            data-testid="reg-category"
            value={props.category}
            onChange={(e) => props.onCategory(e.target.value)}
          >
            {/* 빈 값은 「아직 안 골랐다」이고 그때 `다음` 이 막힌다(수용 기준 2). */}
            <option value="">아직 고르지 않음</option>
            {CATEGORIES.map((v) => (
              <option key={v.value} value={v.value}>
                {bilingual(v)}
              </option>
            ))}
          </select>
          <AxisDefLine value={cat} testId="reg-category-def" />
        </div>

        <div className="form-row">
          <label htmlFor="reg-datatype">
            유형
            <span className="reqtag">필수</span>
          </label>
          <select
            id="reg-datatype"
            className="sel"
            data-testid="reg-datatype"
            value={props.dataType}
            onChange={(e) => props.onDataType(e.target.value)}
          >
            <option value="">아직 고르지 않음</option>
            {DATA_TYPES.map((v) => (
              <option key={v.value} value={v.value}>
                {bilingual(v)}
              </option>
            ))}
          </select>
          <AxisDefLine value={type} testId="reg-datatype-def" />
          {/* PRD-33 ⑴ — 정의 줄 **다음 줄**의 회색 한 줄. 문면은 표의 `특이사항 및 주의점` 축자다 */}
          {type ? (
            <p className="axis-note muted" data-testid="reg-datatype-note">
              참고 · {type.extra}
            </p>
          ) : null}
        </div>

        <div className="form-row">
          <label htmlFor="reg-level">
            가공 단계
            <span className="reqtag">필수</span>
          </label>
          {/* ⚠ 빈 선택지가 없다 — 기본값 `Lv2` 가 늘 서 있어 「비어 있음」이 성립하지 않는다.
              계보에서 나온 파생값(`processingLevel`)과 **다른 칸**이다(미결-2 ⓐ). */}
          <select
            id="reg-level"
            className="sel"
            data-testid="reg-level"
            value={props.level}
            onChange={(e) => props.onLevel(e.target.value)}
          >
            {PROCESSING_LEVELS.map((v) => (
              <option key={v.value} value={v.value}>
                {v.label}
              </option>
            ))}
          </select>
          <AxisDefLine value={lv} testId="reg-level-def" withExtra />
        </div>
      </div>
    </div>
  );
}

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
 * ② 메타데이터 입력 — 이름·설명·기간·좌표계·격자·확장자(자동)·용량(자동)·변수 표·
 * 부가 정보(관측 간격·공개 범위)·대표 그림 (PRD-12).
 *
 * ⚠ **대표 그림은 왼쪽 미리보기 칸이 이미 그린다**(`PreviewPanel` · `WU-A10` · PRD-20) —
 *    같은 칸을 두 곳에 그리지 않는다.
 * ⚠ **공개 범위의 값 칸은 WU-B4 몫이다** — 여기서는 자리만 세운다.
 */
function StepMeta(props: {
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
  crs: string;
  onCrs: (v: string) => void;
  // ⭑ **⟨19차 해제 · PRD-18⟩ 기간의 최소 단위와 그 단위가 여는 칸 — 값은 달력 팝오버가 받는다.**
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
  // ⭑ **⟨20차 해제 · PRD-11 · WU-B4⟩ 공개 범위 — 부가 정보의 셀렉트 한 칸.**
  //   `null` = 아직 고르지 않았다(연구실 기본값을 따른다 · advisor ② ㊁).
  accessState: AccessState | null;
  onAccessState: (v: AccessState | null) => void;
  // ⭑ ⟨PRD-33 ⑵⟩ 설명 칸 아래 힌트가 읽는 두 축. 값 자체는 ① 이 쥐고 있다.
  category: string;
  level: string;
}) {
  const bodies = (props.status?.files ?? []).filter((f) => f.kind === '본체');
  // ⭑ **⟨R-C · WU-C8 · R-B §5-14 판정⟩ 기간을 받는 길은 **달력 팝오버 하나**다.**
  //   종전에는 인라인 칸(최소 단위 셀렉트 ＋ 날짜 두 칸 / 자리 칸 두 줄)과 팝오버가 나란히
  //   살아 두 벌이었다 — 같은 값을 두 자리에서 받으면 어느 쪽이 이기는지 화면이 말하지 않고,
  //   rev2 목업에는 팝오버 하나뿐이다. 인라인 칸을 걷고 팝오버만 남긴다.
  //   ⛔ 요청에 실리는 열쇠는 **무변**이다 — `granularity`·`startParts`·`endParts` 그대로이고
  //      팝오버의 `적용` 이 그 셋을 한 번에 채운다(`humanMetadata`).
  const [periodPopOpen, setPeriodPopOpen] = useState(false);
  // PRD-33 ⑵ — 고른 분류의 `메타데이터 항목` ＋ 고른 가공 단계의 `메타데이터 필수 항목`.
  // ⛔ **Lv0 은 넣지 않는다** — 그 두 칸은 별도 칸(PRD-19 · WU-B6) 소관이다.
  const catHint = findAxis(CATEGORIES, props.category);
  const lvHint = props.level === 'Lv0' ? null : findAxis(PROCESSING_LEVELS, props.level);
  const summaryHints = [catHint?.extra, lvHint?.extra].filter((t): t is string => !!t);
  // 조각의 확장자는 **데이터셋당 1값**이다 (`P-5` · PRD-32) — 첫 조각이 곧 전체다.
  const extension = extensionOf(bodies[0]?.fileName ?? '');
  const sliced = bodies.length > 1;
  const bytes = bodies.reduce((s, f) => s + f.byteSize, 0);
  // 조각이 여러 건이면 용량은 `조각 합계`, 기간은 `조각 합집합` 으로 라벨을 바꿔 단다 (§8).
  const sizeLabel = sliced ? '용량 (조각 합계)' : '용량';
  const periodLabel = sliced ? '기간 (조각 합집합)' : '기간';
  // 관측 간격 — **반쪽인가.** 한쪽만 채워지면 서버가 400 이다(pair 규율).
  const rawValue = props.intervalValue.trim();
  const half = rawValue.length > 0 !== props.intervalUnit.length > 0;
  const previewInterval =
    rawValue.length > 0 && props.intervalUnit
      ? { value: Number(rawValue), unit: props.intervalUnit }
      : null;

  // 미리보기가 쓰는 기간 — 팝오버가 채운 자리 칸에서 조립한다(`humanMetadata` 와 같은 재료).
  const previewStart = props.granularity ? assemble(props.startParts, props.granularity) : '';
  const previewEnd = props.granularity ? assemble(props.endParts, props.granularity) : '';
  const previewPeriod = previewStart
    ? { start: previewStart, end: previewEnd || null, granularity: props.granularity || null }
    : null;

  return (
    <div className="card is-on" data-testid="reg-s2">
      <div className="card-h">
        <h3>{STEP_LABELS[2]}</h3>
        <span className="sub" data-testid="reg-s2-sub">
          {METADATA_SUBTITLE}
        </span>
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
          {/* ⭑ **⟨WU-B3 · PRD-03 · 미결-2 ⓐ⟩ 가공 단계 칸은 ① 분류로 갔다.**
              사람이 고르는 값이 됐고(`processingLevelUserSet`), 계보 계산값과 어긋나면
              **경고만** 낸다 — 등록을 막지 않는다. 읽기 전용 안내 칸은 그래서 사라졌다. */}
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
          {/* ⭑ ⟨advisor ② · F1⟩ `daterange` = rev2 `.daterange{position:relative}` —
              달력 팝오버(`.dr-pop`)가 이 칸을 기준으로 뜬다. 이 클래스가 없으면
              `position:absolute` 가 화면 전체를 기준으로 잡는다. */}
          <div className="form-row daterange">
            {/* ⭑ ⟨WU-C8 · §5-14⟩ 값 칸이 없다 — 누르면 달력 팝오버가 뜨고 거기서만 받는다.
                `htmlFor` 는 그 버튼을 가리킨다(라벨이 가리킬 칸이 여기 남아 있지 않다). */}
            <label htmlFor="reg-period-open">{periodLabel} (선택)</label>
            {/* ⭑ **⟨PRD-40 · 판정 ⓐ⟩ 종료는 비울 수 있다.** 필수 표시를 걷고 안내 한 줄을 둔다 —
                저장은 `period_end = period_start` 로 채워지고(`UploadModal.humanMetadata`)
                표시는 시작=끝이면 한 값으로 그린다(PRD-35 괄호 병기 그대로). */}
            <p className="fieldnote" data-testid="reg-period-single-hint">
              {PERIOD_SINGLE_POINT_HINT}
            </p>
            {/* ㈏ 달력 팝오버 (R-A′ 이관 · PRD-18 · WU-C8 §5-14) — 기간을 받는 **유일한 길**.
                버튼 문면은 §5-15 판정이 채택한 것을 그대로 둔다. */}
            <button
              type="button"
              id="reg-period-open"
              className="btn btn-secondary btn-sm"
              data-testid="reg-period-open"
              aria-haspopup="dialog"
              aria-expanded={periodPopOpen}
              onClick={() => setPeriodPopOpen((v) => !v)}
            >
              달력에서 고르기
            </button>
            {periodPopOpen && (
              <PeriodCalendarPopover
                granularity={props.granularity}
                startParts={props.startParts}
                endParts={props.endParts}
                onApply={(v) => {
                  props.onGranularity(v.granularity);
                  props.onStartParts(v.startParts);
                  props.onEndParts(v.endParts);
                }}
                onClear={() => {
                  props.onStartParts({ ...EMPTY_PARTS });
                  props.onEndParts({ ...EMPTY_PARTS });
                }}
                onClose={() => setPeriodPopOpen(false)}
              />
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
        {/* ⭑ **⟨PRD-33 ⑵⟩ 설명 칸 **아래** 힌트** — 고른 분류의 `메타데이터 항목` ＋ 고른
            가공 단계의 `메타데이터 필수 항목`. 문면은 PRD-01·03 표 축자이고 화면이 짓지 않는다.
            ⛔ Lv0 은 이 줄에 없다(별도 칸 소관 · PRD-19 · WU-B6).
            ⚠ **칸(`form-row`) 바깥이다** — rev1 이 없앤 「칸 아래 안내 문구」는 설명 칸 자체를
               해설하던 문단이고, 이 줄은 **고른 분류가 요구하는 항목**이라 성격이 다르다. */}
        {summaryHints.length > 0 && (
          <p className="fieldnote" data-testid="reg-summary-hint">
            {summaryHints.join(' · ')}
          </p>
        )}

        {/* ⭑ **⟨20차 해제 · PRD-11 · WU-B4⟩ 공개 범위 — WU-B3 이 세운 자리를 채운다.**
            표기 3값은 rev1 셀렉트 축자(`연구실 구성원 전체`·`나만 보기`·`지정한 사람만` ·
            미결-1 ⓐ)이고 저장은 `열림`·`잠김`·`지정 공개` 다. 대응표는 `common/accessState.ts`
            **한 자리**에 있다 — 상세 헤더 칩·공개 범위 설명·수정 폼이 같은 표를 읽는다.
            ⚠ **rev2 목업의 3값(전체 공개·조건부 공개·비공개)을 쓰지 않는다** — 기준축이
              연구실 **밖**이라 한 칸씩 어긋난다(PRD-11 대응표 · 미결-1 ⓐ 가 rev1 을 확정했다).
            기본 선택은 `연구실 구성원 전체` 라 대개 그대로 두고 넘어간다. */}
        <div className="form-row" data-testid="reg-visibility-slot">
          <label htmlFor="reg-visibility">공개 범위</label>
          <select
            id="reg-visibility"
            className="sel"
            data-testid="reg-visibility"
            value={props.accessState ?? ''}
            onChange={(e) =>
              props.onAccessState(e.target.value === '' ? null : (e.target.value as AccessState))
            }
          >
            {/* ⭑ **⟨advisor ② ㊁⟩ 첫 칸은 값이 아니라 「아직 고르지 않았다」다.**
                이 상태로 등록하면 요청에 열쇠가 빠지고 서버가 연구실 기본값을 쓴다 —
                PRD-11 「NULL = 연구실 기본값(현행 의미 유지)」. */}
            <option value="">{LAB_DEFAULT_LABEL}</option>
            {ACCESS_STATES.map((v) => (
              <option key={v} value={v}>
                {ACCESS_LABEL[v]}
              </option>
            ))}
          </select>
          {/* 고른 값의 **범위**를 한 줄로 적는다 — `지정한 사람만` 은 허용 목록 0건으로
              시작해 사실상 `나만 보기` 와 같다는 사실이 여기서 드러난다(PRD-11 ⚠). */}
          <p className="fieldnote" data-testid="reg-visibility-note">
            {props.accessState === null ? LAB_DEFAULT_NOTE : ACCESS_NOTE[props.accessState]}
          </p>
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
    <div className="card is-on" data-testid="reg-projects">
      <div className="card-h">
        <h3>연관 프로젝트·논문</h3>
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

/**
 * ③ 연결 — **계보 부모 ＋ 원천 표기 ＋ 연관 프로젝트·논문이 한 단계에 있다** (PRD-12).
 *
 * rev2 축자 = 「계보 = 어디서 왔나(상류) · 프로젝트·논문 = 어디에 쓰나(하류)」. 둘은
 * 카드 두 장이고 단계는 하나다 — 종전처럼 ②③ 으로 갈라 두지 않는다.
 *
 * ⭑ **⟨WU-B6 · PRD-19⟩ Lv0 전용 두 칸(`sourceUrl`·`sourceDownloadedOn`)이 자리를 채웠다.**
 *    ① 이 고른 Lv 가 `Lv0` 일 때만 그린다 — 바꾸면 **즉시** 열리고 닫힌다(파생 상태가 아니라
 *    `props.ctx.processingLevelUserSet` 을 그대로 읽으므로 ① 의 변경이 그대로 반영된다).
 *    ⛔ **숨은 동안에는 값을 싣지 않는다** — 그 판정은 `UploadModal.submit` 이 같은 조건으로 한다.
 * ⚠ 원천 표기(`sourceLabel`)는 **Lv 무관 상시 노출**이고 그것은 이 블록 밖에 있다(미결-11 ⓐ) —
 *    Lv 로 갈리는 것은 아래 두 칸의 표시뿐이다.
 */
function StepThree(props: {
  sourceLabel: string;
  onSourceLabel: (v: string) => void;
  /** ⭑ ⟨WU-B6 · PRD-19⟩ Lv0 전용 두 칸. **표시 조건은 `ctx.processingLevelUserSet`** 이다. */
  sourceUrl: string;
  onSourceUrl: (v: string) => void;
  sourceDownloadedOn: string;
  onSourceDownloadedOn: (v: string) => void;
  /** ⭑ ⟨advisor ② F1 · WU-B6⟩ 형상 오류 인라인 문구. `null` 이면 서지 않는다. */
  sourceDownloadedOnError: string | null;
  lineageStep?: LineageStepRender | undefined;
  ctx: LineageStepContext;
  projectSource: ProjectSource;
  projects: PickedProject[];
  onProjects: (v: PickedProject[]) => void;
}) {
  return (
    <div data-testid="reg-s3">
    <div className="card is-on">
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
        {/* ⭑ **⟨WU-B6 · PRD-19⟩ Lv0 전용 두 칸.** 슬롯 자체는 늘 있고 Lv0 이 아니면
            **안이 비었다** — 자리를 없애면 시험이 「블록이 없다」와 「Lv0 이 아니다」를 못 가른다. */}
        <div className="form-row" data-testid="reg-source-lv0-slot">
          {props.ctx.processingLevelUserSet === LV0 ? (
            <div data-testid="reg-source-lv0">
              <div className="form-row">
                <label htmlFor="reg-source-url">출처 주소 (선택)</label>
                <input
                  id="reg-source-url"
                  className="inp"
                  data-testid="reg-source-url"
                  placeholder={LV0_SOURCE_URL_PLACEHOLDER}
                  value={props.sourceUrl}
                  onChange={(e) => props.onSourceUrl(e.target.value)}
                />
              </div>
              <div className="form-row">
                <label htmlFor="reg-source-downloaded-on">내려받은 날 (선택)</label>
                <input
                  id="reg-source-downloaded-on"
                  className="inp"
                  data-testid="reg-source-downloaded-on"
                  placeholder={LV0_SOURCE_DATE_PLACEHOLDER}
                  value={props.sourceDownloadedOn}
                  onChange={(e) => props.onSourceDownloadedOn(e.target.value)}
                />
                {/* ⭑ ⟨advisor ② F1 · WU-B6⟩ 칸 바로 아래에 선다 — 서버 400 문면을 그대로 쓴다. */}
                {props.sourceDownloadedOnError ? (
                  <p className="warn" role="alert" data-testid="reg-source-downloaded-on-error">
                    {props.sourceDownloadedOnError}
                  </p>
                ) : null}
              </div>
              <p className="muted" data-testid="reg-source-lv0-notice">
                {LV0_SOURCE_NOTICE}
              </p>
            </div>
          ) : null}
        </div>
      </div>
    </div>

    {/* 어디에 쓰나(하류) — 같은 단계 안의 두 번째 카드다 (`WU-A7R` 표 그대로 재사용) */}
    <StepTwo
      source={props.projectSource}
      picked={props.projects}
      onPicked={props.onProjects}
    />
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
  crs: string;
  onCrs: (v: string) => void;
  // ⭑ ⟨19차 해제 · PRD-17·18 · WU-C8 §5-14⟩ 최소 단위·자리 칸·관측 간격 — StepMeta 로
  //    그대로 흘린다. 종전 날짜 두 칸(`periodStart`·`periodEnd`)은 인라인 칸과 함께 걷혔다.
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
  /** ⭑ ⟨WU-B6 · PRD-19⟩ Lv0 전용 두 칸. **표시 조건은 `ctx.processingLevelUserSet`** 이다. */
  sourceUrl: string;
  onSourceUrl: (v: string) => void;
  sourceDownloadedOn: string;
  onSourceDownloadedOn: (v: string) => void;
  sourceDownloadedOnError: string | null;
  projects: PickedProject[];
  onProjects: (v: PickedProject[]) => void;
  // ⭑ ⟨WU-B3 · PRD-01·02·03⟩ 분류 3축 — ① 이 고르고 ② 의 힌트가 읽는다.
  category: string;
  onCategory: (v: string) => void;
  dataType: string;
  onDataType: (v: string) => void;
  level: string;
  onLevel: (v: string) => void;
  // ⭑ ⟨20차 해제 · PRD-11 · WU-B4⟩ 공개 범위 — ② 부가 정보로 그대로 흘린다.
  accessState: AccessState | null;
  onAccessState: (v: AccessState | null) => void;
  nameError: boolean;
  summaryError: boolean;
  registerError: string | null;
  lineageStep?: LineageStepRender | undefined;
  lineageCtx: LineageStepContext;
  /** ⭑ **⟨WU-B5 · PRD-09⟩ 사후 충돌 건수.** 1건 이상이면 마지막 게이트가 막힌다. */
  lineageConflicts?: number | undefined;
  onCancel: () => void;
  onSubmit: () => void;
}) {
  const { step } = props;
  /**
   * 분석이 아직 안 끝났는가 (① · rev1 `anNext.disabled`).
   * `status` 가 아직 없으면 **접수·분석 중**이다 — 모르는 것을 끝났다고 하지 않는다.
   */
  const analyzing = !props.status?.ready;
  /**
   * ① 의 **분류·유형이 비어 있으면 `다음` 이 막힌다** (수용 기준 2).
   *
   * ⚠ **표시기 이동은 막지 않는다** — rev1 `UI-003` 축자 「언제나 · 눌러서 아무 단계로나
   *    이동」과 병존하는 자리다. 순차 이동(`다음`)만 ① 의 빈 값에서 서고, 임의 이동과
   *    마지막 게이트(`데이터셋 만들기`)는 종전 그대로다.
   * ⚠ 가공 단계는 기본값 `Lv2` 가 늘 서 있어 빈 상태가 성립하지 않는다.
   */
  const classifyBlocked = step === 1 && (!props.category || !props.dataType);
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
          <StepClassify
            category={props.category}
            onCategory={props.onCategory}
            dataType={props.dataType}
            onDataType={props.onDataType}
            level={props.level}
            onLevel={props.onLevel}
          />
        )}
        {step === 2 && (
          <StepMeta
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
            accessState={props.accessState}
            onAccessState={props.onAccessState}
            category={props.category}
            level={props.level}
          />
        )}
        {step === 3 && (
          <StepThree
            sourceLabel={props.sourceLabel}
            onSourceLabel={props.onSourceLabel}
            sourceUrl={props.sourceUrl}
            onSourceUrl={props.onSourceUrl}
            sourceDownloadedOn={props.sourceDownloadedOn}
            onSourceDownloadedOn={props.onSourceDownloadedOn}
            sourceDownloadedOnError={props.sourceDownloadedOnError}
            lineageStep={props.lineageStep}
            ctx={props.lineageCtx}
            projectSource={props.projectSource}
            projects={props.projects}
            onProjects={props.onProjects}
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
            disabled={analyzing || classifyBlocked}
            onClick={() => props.onStep((step + 1) as Step)}
          >
            다음 →
          </button>
        ) : (
          <button
            type="button"
            className="btn btn-primary"
            data-testid="reg-done"
            /* ⭑ **⟨WU-B5 · PRD-09⟩ 자기 Lv 를 넘는 연결이 남아 있으면 막는다.**
               ⛔ **연결을 지우지 않는다** — 사람이 한 연결을 시스템이 되돌리지 않고,
               되돌리는 것은 사람이다(자기 Lv 를 올리거나 그 연결을 지운다). 그러면
               이 수가 0 이 되고 버튼이 다시 눌린다. 서버 400 이 그 뒤에 또 선다. */
            disabled={(props.lineageConflicts ?? 0) > 0}
            onClick={props.onSubmit}
          >
            데이터셋 만들기 →
          </button>
        )}
      </div>
    </div>
  );
}
