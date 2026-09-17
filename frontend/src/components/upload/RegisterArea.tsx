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
import { formatExtension } from '../detail/format';
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
  type LineageStepContext,
  type LineageStepRender,
  type PickedProject,
  type ProjectSource,
  type ProjectType,
  type UploadStatus,
} from './types';

/** 관측 간격의 단위 6값 — **정본은 DB CHECK** 다 (PRD-17 · `M-6`). */
export const INTERVAL_UNITS = ['초', '분', '시', '일', '월', '년'] as const;

/**
 * ⭑ **⟨2026-09-14 · 기획자 9/13 구두 피드백 · Ted 재판정 대기⟩ 단위의 표시 라벨.**
 * 기획서 rev2 의 단위 사다리 표기는 `연·월·일·시간·분·초` 다. **저장값은 위 6값 그대로**이고
 * (계약·DB CHECK 무변) 여기서 바뀌는 것은 셀렉트에 보이는 글자뿐이다.
 * ⛔ 라벨을 저장값으로 쓰지 않는다 — `option value` 는 `INTERVAL_UNITS` 의 값이다.
 */
export const INTERVAL_UNIT_LABEL: Record<(typeof INTERVAL_UNITS)[number], string> = {
  초: '초',
  분: '분',
  시: '시간',
  일: '일',
  월: '개월',
  년: '년',
};

/**
 * ⭑ **⟨2026-09-14⟩ 필수/선택 표시는 배지 **하나**다.**
 *
 * 종전에는 두 벌이었다 — 필수는 `<span class="reqtag">필수</span>` 배지이고 선택은 라벨
 * 문자열 끝의 `(선택)` 괄호였다. 같은 뜻의 표시가 모양이 다르면 사람은 그 둘을 같은 축의
 * 값으로 읽지 못하고, 괄호 쪽은 라벨 길이에 묻힌다. 기획서 rev2 는 라벨 옆 작은 표 하나로
 * 통일한다 — 여기서는 `필수`/`선택` 두 값을 같은 컴포넌트가 낸다.
 */
export function FieldTag(props: { required?: boolean }) {
  return props.required ? (
    <span className="reqtag">필수</span>
  ) : (
    <span className="opttag">선택</span>
  );
}

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
export const CLASSIFY_SUBTITLE = '어떤 자료인지 고르고, 가공 단계에 맞는 데이터를 연결해요.';
export const METADATA_SUBTITLE = '확장자·용량을 확인하고 아래 정보를 입력해 주세요.';

/**
 * PRD-40 · 판정 ⓐ — 종료 칸의 안내 한 줄. rev2 `prVe` 자리 문면 축자.
 * ⭑ **⟨개정 2026-09-14 · 레인 A4⟩ 자리는 칸 **안**이다** ／ 종전 ~~컨트롤 뒤 `p.fieldnote`~~ —
 *    rev2 목업에서 이 문면은 `#prVe` 즉 **종료 반쪽의 빈 값 표기**이고 별도 문단이 아니다.
 */
export const PERIOD_SINGLE_POINT_HINT = '한 시점이면 비워 둬요';

/** 시작 반쪽의 빈 값 표기 — rev2 `#prVs` 축자. */
export const PERIOD_START_PLACEHOLDER = '날짜를 골라요';

/** 기간 칸 두 반쪽의 이름 — rev2 `.dr-k` 축자. */
export const PERIOD_HALF_LABELS = { start: '시작', end: '종료' } as const;

/**
 * ⭑ **⟨2026-09-14 · 레인 A4⟩ 변수 표의 제목 한 줄 — rev2 `fieldlbl` 축자.**
 * 표 전체의 이름이라 **입력 하나를 가리키지 않는다** — `label` 이 아니라 섹션 제목이고,
 * 그래서 선택 배지도 달지 않는다(괄호 안 문면이 「여러 개」와 「대표 하나」를 이미 말한다).
 */
export const VARIABLES_FIELD_HINT = '(여러 개 · 대표 변수 하나를 골라요)';
export const VARIABLES_FIELD_LABEL = `변수 ${VARIABLES_FIELD_HINT}`;

/**
 * ⭑ **⟨WU-B6 · PRD-19⟩ Lv0 전용 출처 블록의 문면 — rev1 축자다.**
 *
 * 「원시 데이터라 부모가 없어요」가 이 블록이 서는 이유다: Lv0 은 부모가 없어 **계보로는
 * 출처를 말할 수 없고**, 그 자리를 두 칸이 메운다.
 * ⛔ ~~**`필수` 배지를 붙이지 않는다** — 두 칸은 선택 입력이다. rev2 목업이 필수 배지를
 *    그렸으나 **정본은 「선택 입력」이고 목업 배지를 채택하지 않는다**(PRD-19 감사 교차 확인).~~
 * ⭑ **⟨개정 2026-09-14 · 기획자 9/13 구두 피드백 · Ted 재판정 대기⟩ Lv0 이면 `출처 주소`·
 *    `내려받은 날` 에 `필수` 배지가 선다.** 목업 배지를 채택한다 — 부모가 없는 Lv0 에서는
 *    그 두 칸이 계보를 대신하는 **유일한 출처 기록**이라 비면 원천을 말할 방법이 없다.
 */
export const LV0_SOURCE_URL_PLACEHOLDER = '예: https://cds.climate.copernicus.eu/...';
export const LV0_SOURCE_DATE_PLACEHOLDER = '예: 2026-08-20';
/** 이 블록이 열리는 유일한 조건 — ① 이 고른 자기 Lv 다. 파생 Lv 가 아니다. */
export const LV0 = 'Lv0';

/**
 * ⭑ **⟨2026-09-14⟩ 원천 블록의 제목 — 기획서 rev2 `srcBlock` 축자.**
 * 「원천」이 무엇인지를 제목이 바로 말한다 — **연구실 밖 출처**다. 종전 라벨 `원천 표기` 는
 * 칸 이름과 블록 이름을 겸해 둘 다 흐렸다.
 */
export const SOURCE_BLOCK_TITLE = '원천 · 연구실 밖 출처';
export const SOURCE_NAME_PLACEHOLDER = '예: GK2A · 국가기상위성센터';

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
 *  - 셋 다 **필수**이고 처음에는 비어 있다. 사용자가 직접 골라야 다음 단계로 이동한다.
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
            <FieldTag required />
          </label>
          <select
            id="reg-category"
            className="sel"
            data-testid="reg-category"
            value={props.category}
            onChange={(e) => props.onCategory(e.target.value)}
          >
            <option value="">직접 선택해 주세요</option>
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
            <FieldTag required />
          </label>
          <select
            id="reg-datatype"
            className="sel"
            data-testid="reg-datatype"
            value={props.dataType}
            onChange={(e) => props.onDataType(e.target.value)}
          >
            <option value="">직접 선택해 주세요</option>
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
            <FieldTag required />
          </label>
          {/* ⚠ 빈 선택지가 없다 — 값이 늘 서 있어 「비어 있음」이 성립하지 않는다.
              계보에서 나온 파생값(`processingLevel`)과 **다른 칸**이다(미결-2 ⓐ).
              ⭑ **⟨개정 2026-09-13 · R-LTH-REVIEW-1 · spec §6 ㉱⟩ 서 있는 값은 ③ 에서 확정한
                 부모의 **계산값**이다**(부모 0건이면 `Lv0` · 카드 ⑩ ⓐ / 부모 Lv 미상이면 `Lv2` 유지).
                 ／ 종전 ~~기본값 `Lv2` 가 늘 서 있어~~ — 판정은 `UploadModal` 이 쥔다
                 (이 칸은 값을 그리고 고른 것을 올려 보낼 뿐이다). */}
          <select
            id="reg-level"
            className="sel"
            data-testid="reg-level"
            value={props.level}
            onChange={(e) => props.onLevel(e.target.value)}
          >
            <option value="">직접 선택해 주세요</option>
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
  summary: string;
  onSummary: (v: string) => void;
  variables: VariableRow[];
  onVariables: (v: VariableRow[]) => void;
  onVariablesBlocked: (message: string) => void;
  crs: string;
  onCrs: (v: string) => void;
  gridDescription: string;
  onGridDescription: (v: string) => void;
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

  // 미리보기가 쓰는 기간 — 팝오버가 채운 자리 칸에서 조립한다(`humanMetadata` 와 같은 재료).
  const previewStart = props.granularity ? assemble(props.startParts, props.granularity) : '';
  const previewEnd = props.granularity ? assemble(props.endParts, props.granularity) : '';

  return (
    <div className="card is-on" data-testid="reg-s2">
      <div className="card-h">
        <h3>{STEP_LABELS[2]}</h3>
        <span className="sub" data-testid="reg-s2-sub">
          {METADATA_SUBTITLE}
        </span>
      </div>
      <div className="card-b">
        <div className="fieldlbl">파일 정보</div>
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

        <div className="form-row">
          {/* ⭑ ⟨개정 2026-09-14⟩ 이름은 종전부터 등록 게이트였고 표시만 없었다 —
              같은 배지로 그 사실을 화면에 적는다. */}
          <label htmlFor="reg-name">
            데이터셋 이름
            <FieldTag required />
          </label>
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
        {/* ⭑ **⟨개정 2026-09-14 · 기획자 9/13 구두 피드백 · Ted 재판정 대기⟩ `주제` 칸이 없다.**
            기획서 rev2 우측 폼에 그 칸이 없다 — 분류 축(`category`)이 같은 일을 하고,
            두 축을 같은 화면에서 받으면 어느 쪽으로 거를지 사람이 고를 수 없다.
            ⛔ 읽기 쪽(목록 열·상세 칩·필터)은 **무변**이고 계약 `topic` 도 그대로 있다 —
               등록 폼이 값을 만들지 않을 뿐이다(`topic` 은 계약에서 optional).
            ⭑ **⟨WU-B3 · PRD-03 · 미결-2 ⓐ⟩ 가공 단계 칸은 ① 분류로 갔다.** */}
        {/* ⭑ **⟨2026-09-14 · 레인 A4⟩ 기간이 데이터셋 이름 바로 아래다.**
            ／ 종전 ~~짧은 값 한 줄(`form-3`)의 첫 칸~~ — rev2 목업 ② 본문의 위→아래 순서는
            이름 → 기간 → (관측 간격·좌표계·격자) → 설명 → 변수 → 공개 범위이고,
            사용자 지적(2026-09-14 · 스크린샷 대조)이 지목한 것이 그 순서다.
            ⭑ ⟨advisor ② · F1⟩ `daterange` = rev2 `.daterange{position:relative}` —
            달력 팝오버(`.dr-pop`)가 이 칸을 기준으로 뜬다. 이 클래스가 없으면
            `position:absolute` 가 화면 전체를 기준으로 잡는다. */}
        <div className="form-row daterange">
          {/* ⭑ ⟨개정 2026-09-14 · 기획자 9/13 구두 피드백 · Ted 재판정 대기⟩ 기간은 필수다 —
              시간축을 모르면 이 자료가 언제 것인지 목록에서 가를 수 없다. */}
          <label htmlFor="reg-period-open">
            {periodLabel}
            <FieldTag required />
          </label>
          {/* ⭑ **⟨2026-09-14 · 레인 A4⟩ 칸 자체가 rev2 `#prField` 다.**
              ／ 종전 ~~`달력에서 고르기` 작은 버튼 ＋ 그 아래 안내 문단~~ — 넓은 칸이 두
              반쪽으로 갈려 있어야 「시작과 끝 **두 개**를 받는다」로 읽힌다(rev2 `.dr-half`
              주석 축자). 작은 버튼 한 개는 그 사실을 화면에 적지 않는다.
              ⛔ **기간을 받는 길은 여전히 달력 팝오버 하나다**(WU-C8 §5-14) — 이 칸은 값을
                 직접 받지 않고 팝오버를 여닫기만 한다. 최소 단위·시각 규칙·`적용` 무변. */}
          <button
            type="button"
            id="reg-period-open"
            className="dr-field"
            data-testid="reg-period-open"
            aria-haspopup="dialog"
            aria-expanded={periodPopOpen}
            onClick={() => setPeriodPopOpen((v) => !v)}
          >
            <span className="dr-half">
              <span className="dr-ico" aria-hidden="true">
                <svg
                  width="15"
                  height="15"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <rect x="3" y="4" width="18" height="18" rx="2" />
                  <path d="M16 2v4M8 2v4M3 10h18" />
                </svg>
              </span>
              <span className="dr-txt">
                <span className="dr-k">{PERIOD_HALF_LABELS.start}</span>
                <span
                  className={previewStart ? 'dr-v' : 'dr-v ph'}
                  data-testid="reg-period-start-value"
                >
                  {previewStart || PERIOD_START_PLACEHOLDER}
                </span>
              </span>
            </span>
            <span className="dr-half">
              <span className="dr-ico" aria-hidden="true">
                <svg
                  width="15"
                  height="15"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <path d="M5 12h14M13 6l6 6-6 6" />
                </svg>
              </span>
              <span className="dr-txt">
                <span className="dr-k">{PERIOD_HALF_LABELS.end}</span>
                {/* ⭑ **⟨PRD-40 · 판정 ⓐ⟩ 종료는 비울 수 있다** — 문면은 무변이고 **자리만**
                    칸 안으로 들어왔다. 값이 차면 그 자리에 값을 적으므로 열쇠를 가른다 —
                    안내 열쇠(`reg-period-single-hint`)는 **빈 값일 때만** 선다. */}
                {previewEnd ? (
                  <span className="dr-v" data-testid="reg-period-end-value">
                    {previewEnd}
                  </span>
                ) : (
                  <span className="dr-v ph" data-testid="reg-period-single-hint">
                    {PERIOD_SINGLE_POINT_HINT}
                  </span>
                )}
              </span>
            </span>
          </button>
          <p className="fieldnote">자료가 다루는 시작과 종료 시점이에요. 한 시점이면 종료는 비워 두세요.</p>
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

        {/* ⭑ **⟨PRD-28 · 개정 2026-09-14 · 레인 A4⟩ 짧은 값 세 개가 한 줄이다** —
            관측 간격 · 좌표계 · 격자. ／ 종전 ~~기간 · 좌표계 · 격자~~ — rev2 목업의 `form-3`
            이 담은 셋이 이 셋이고, 기간은 두 칸이 한 값이라 위에서 제 행을 갖는다.
            ⛔ 2+1 로 갈라 두 줄로 쓰지 않는다 — 마지막 줄이 반쯤 빈다(rev1 축자).
            ⚠ 좁은 폭에서는 목업과 같이 2열로 접혀 `격자` 가 둘째 줄로 내려간다. */}
        <div className="form-3" data-testid="reg-short-row">
          {/* ⭑ **⟨19차 해제 · PRD-17 · 미결-4 ⓐ⟩ 관측 간격.**
              숫자 한 칸 ＋ 단위 셀렉트로 받는다. **저장은 두 칸 구조화**이고(자유 텍스트로
              접으면 「1시간 이하」 같은 조건 검색이 영영 안 선다) 화면이 `10분` 을 조립한다.
              #78 승인으로 신규 등록에서 필수다. 2026-09-15 선택 입력 판정은 개정됐다.
              숫자와 단위를 모두 받고 서버에서도 누락을 거절한다.
              ⭑ **⟨2026-09-14 · 레인 A4⟩ 자리는 짧은 값 한 줄의 첫 칸이다** ／ 종전 ~~제 행~~ —
                 rev2 목업이 기간 바로 아래 같은 줄에 좌표계·격자와 함께 둔다. */}
          <div className="form-row">
            <label htmlFor="reg-interval-value">
              관측 간격 입력
              <FieldTag required />
            </label>
            {/* 각색(이름만) — rev2 `.itv`. 수 칸이 늘고 단위 셀렉트가 고정 폭이다. */}
            <span className="itv">
              <input
                id="reg-interval-value"
                className="inp"
                type="text"
                inputMode="numeric"
                data-testid="reg-interval-value"
                placeholder="예: 10"
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
                    {INTERVAL_UNIT_LABEL[u]}
                  </option>
                ))}
              </select>
            </span>
            {/* **반쪽은 서버가 400 이다** — 화면은 그 사실을 미리 알린다. 판정을 흉내 내
                막지는 않는다(문구의 정본은 서버 봉투다 · WU-A4 가 세운 규율 그대로). */}
            {half ? (
              <p className="warn" data-testid="reg-interval-half">
                숫자를 입력하고 단위를 선택해주세요
              </p>
            ) : <p className="fieldnote">숫자를 입력하고 단위를 선택해주세요</p>}
          </div>
          <div className="form-row">
            <label htmlFor="reg-crs">
              좌표계 입력
              <FieldTag />
            </label>
            <input
              id="reg-crs"
              className="inp"
              data-testid="reg-crs"
              placeholder="예: EPSG:5179"
              value={props.crs}
              onChange={(e) => props.onCrs(e.target.value)}
            />
          </div>
          {/* ⭑ **⟨2026-09-14 · 레인 A4⟩ 라벨은 `격자` 이고 칸은 한 줄 입력이다.**
              ／ 종전 ~~라벨 `격자 설명` ＋ `textarea rows=2` ＋ 칸 아래 안내 한 줄~~ —
              rev2 목업의 이 칸은 `#metaGrid` **한 줄 입력**이고 안내 문단이 없다
              (`0.05° (~5km)` 같은 짧은 값 하나를 받는다). 두 줄 칸은 「길게 적으라」는
              신호라 목업과 어긋난다.
              ⛔ **저장 열쇠는 무변이다** — `gridDescription` 그대로이고 계약·서버 무접촉.
              ⚠ **종전 수용 기준과 충돌한다** — `dev-package/prd/specs/2026-09-12-issue-register-hints-parent-picker.md`
                 의 「격자 설명 칸의 안내 위치가 종전과 같다」. 안내 문단 자체가 사라지므로
                 **Ted 재판정 대기**로 적어 둔다(레인 보고서 「종전 판정 충돌」 절). */}
          <div className="form-row">
            <label htmlFor="reg-grid-description">
              격자 입력
              <FieldTag />
            </label>
            <input
              id="reg-grid-description"
              className="inp"
              data-testid="reg-grid-description"
              maxLength={1000}
              value={props.gridDescription}
              onChange={(e) => props.onGridDescription(e.target.value)}
              placeholder="예: 0.05° (~5km)"
            />
          </div>
        </div>

        {/* ⭑ **⟨PRD-15⟩ 설명은 필수이고 칸은 세 줄이다.**
            rev1 축자 = 「필수로 만든 칸이 한 줄이면 **짧게 쓰라는 신호**가 된다」 —
            그래서 `필수` 배지와 `textarea rows=3` 이 한 벌이다.
            ⛔ 칸 아래 안내 문구를 두지 않는다 — rev1 이 없앴다(설명 대신 칸을 키운다). */}
        <div className="form-row">
          <label htmlFor="reg-summary">
            설명
            <FieldTag required />
          </label>
          <textarea
            id="reg-summary"
            className="inp"
            data-testid="reg-summary"
            rows={3}
            maxLength={3000}
            value={props.summary}
            onChange={(e) => props.onSummary(e.target.value)}
          />
          {props.summaryError && (
            <p className="warn" data-testid="reg-summary-error">
              설명을 적어 주세요
            </p>
          )}
        </div>

        {/* 변수 — **사람이 적는 자유 입력이다** (정본 스펙 18·19·20 · `VAL-006`).
            형식 검사를 하지 않는다. 비면 요청에 싣지 않는다 — 빈 값을 저장하면 나중에
            파이프라인이 채울 자리가 영영 막힌다 (`UploadModal.submit`).
            ⭑ **⟨WU-B2 · PRD-16⟩ 변수는 한 칸이 아니라 5열 표다** — 「변수 3개에 단위
            1개면 어느 변수 것인지 알 수 없다」(rev1 축자). 표 자체는 `VariableTable`
            하나이고 상세가 같은 것을 읽기 전용으로 그린다.
            ⭑ **⟨2026-09-14 · 레인 A4⟩ 자리는 설명 **뒤**이고 이름표는 `label` 이 아니라
               섹션 제목(`fieldlbl`)이다.** ／ 종전 ~~데이터셋 이름 바로 아래 · `label` ＋
               `선택` 배지~~ — rev2 목업이 이 표를 설명 아래에 두고 위에 제목 한 줄을 단다.
               제목은 **입력 하나를 가리키지 않으므로** `label` 이 될 수 없고, 괄호 안 문면이
               「여러 개」와 「대표 하나」를 이미 말해 선택 배지가 겹친다. */}
        <div className="fieldlbl" data-testid="reg-variables-label">
          변수 <span className="muted">{VARIABLES_FIELD_HINT}</span>
        </div>
        <p className="fieldnote">변수마다 단위·값 범위·결측률을 적고, 자료를 대표할 변수 하나를 골라요.</p>
        <VariableTable
          rows={props.variables}
          onRows={props.onVariables}
          onBlocked={props.onVariablesBlocked}
        />

        {/* ⭑ **⟨20차 해제 · PRD-11 · WU-B4⟩ 공개 범위 — WU-B3 이 세운 자리를 채운다.**
            표기 3값은 rev1 셀렉트 축자(`연구실 구성원 전체`·`나만 보기`·`지정한 사람만` ·
            미결-1 ⓐ)이고 저장은 `열림`·`잠김`·`지정 공개` 다. 대응표는 `common/accessState.ts`
            **한 자리**에 있다 — 상세 헤더 칩·공개 범위 설명·수정 폼이 같은 표를 읽는다.
            ⚠ **rev2 목업의 3값(전체 공개·조건부 공개·비공개)을 쓰지 않는다** — 기준축이
              연구실 **밖**이라 한 칸씩 어긋난다(PRD-11 대응표 · 미결-1 ⓐ 가 rev1 을 확정했다).
            기본 선택은 `연구실 구성원 전체` 라 대개 그대로 두고 넘어간다. */}
        <div className="form-row" data-testid="reg-visibility-slot">
          <label htmlFor="reg-visibility">
            공개 범위
            <FieldTag />
          </label>
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
            {props.accessState === null ? LAB_DEFAULT_NOTE : ACCESS_NOTE[props.accessState]} 시스템 관리자와 이 연구실 교수 관리자는 관리 목적으로 접근할 수 있어요.
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
  const [rows, setRows] = useState<PickedProject[] | null>(null);
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
    if (!qName.trim()) { setQError('이름을 적어 주세요. 나중에 찾을 때 쓰는 유일한 이름이에요.'); return; }
    // **거절을 삼키지 않는다** — 이름 중복(PRD-42)이 400 ＋ 축자 문면으로 온다. 문면은
    // 서버가 적어 보낸 것을 그대로 띄운다(`projectSource.create`).
    try {
      const made = await props.source.create({ type: qType, name: qName.trim() });
      setQError(null);
      setRows((current) => [...(current ?? []), made]);
      setSel(made.projectId);
      props.onPicked([...props.picked, made]);
      setQName('');
      setQType('국가과제');
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
            <button type="button" className="btn btn-secondary btn-sm" data-testid="reg-proj-add" onClick={add}>
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
                  onClick={() => { setQuickOpen(false); setQName(''); setQType('국가과제'); setQError(null); }}
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
 * ⚠ ~~원천 표기(`sourceLabel`)는 **Lv 무관 상시 노출**이고 그것은 이 블록 밖에 있다(미결-11 ⓐ) —
 *    Lv 로 갈리는 것은 아래 두 칸의 표시뿐이다.~~
 * ⭑ **⟨개정 2026-09-14 · 기획자 9/13 구두 피드백 · Ted 재판정 대기⟩ 세 칸이 한 블록이다.**
 *    ／ 종전 ~~`원천 표기` 한 칸은 상시 · Lv0 두 칸만 조건부~~ — **원천 = 직접 상류가 연구실
 *    밖일 때만 묻는다.** 조건은 `Lv0` **또는** 연결 0건(`ctx.parents.length === 0`)이고,
 *    부모가 붙어 있으면 원천은 **부모 쪽 계보가 말하므로** 블록 전체가 사라진다.
 *    `내려받은 날` 은 그 안에서 다시 `Lv0` 일 때만 선다(기획서 `srcLv0` 축자).
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
  const lv0 = props.ctx.processingLevelUserSet === LV0;
  /**
   * ⭑ **⟨개정 2026-09-17 · #97⟩ 원천 블록이 서는 조건 — 연결 0건 하나다.**
   * ／ 종전 ~~`Lv0` **또는** 연결 0건~~ — Lv0 에 상위를 붙여도 블록이 남아 **계보가 이미
   * 말한 출처를 다시 적으라**고 읽혔다. 부모가 붙어 있으면 원천은 부모 쪽 계보가 말한다.
   * Lv0 이 연결할 수 있는 상위는 Lv0 뿐이라 이 단일 조건이 「Lv0 에 상위 연결」과 동치다.
   * ⛔ 숨은 동안의 값은 전송되지 않는다 — 그 판정은 `UploadModal` 이 **같은 식**으로 한다.
   */
  const sourceVisible = props.ctx.parents.length === 0;
  return (
    <div data-testid="reg-s3">
    <div className="card is-on">
      <div className="card-h">
        <h3>{STEP_LABELS[3]}</h3>
      </div>
      <div className="card-b">
        {/* ③ 계보 확정이 얹히는 자리. 모달이 기본으로 `LineageStep` 을 넘긴다 */}
        <div className="lineage-slot" data-testid="reg-lineage-slot">
          {props.lineageStep ? (
            props.lineageStep(props.ctx)
          ) : (
            <p className="muted">계보 확정을 열 수 없어요.</p>
          )}
        </div>
        {/* ⭑ **⟨개정 2026-09-14⟩ 원천 블록 — 계보 도구 **뒤**에 선다(기획서 `srcBlock` 자리).**
            앞에 두면 「부모를 붙이면 안 물어본다」는 규칙을 읽기 전에 칸부터 보게 된다. */}
        {sourceVisible ? (
          <div data-testid="reg-source-block" style={{ marginTop: 16 }}>
            <div className="fieldlbl" data-testid="reg-source-block-title">
              {SOURCE_BLOCK_TITLE}
            </div>
            <p className="fieldnote">연구실의 가공 전 데이터는 위에서 연결하고, 연구실 밖 출처는 아래에 적어요.</p>
            <div className="form-row">
              <label htmlFor="reg-source">출처 이름<FieldTag /></label>
              <input
                id="reg-source"
                className="inp"
                data-testid="reg-source"
                maxLength={60}
                placeholder={SOURCE_NAME_PLACEHOLDER}
                value={props.sourceLabel}
                onChange={(e) => props.onSourceLabel(e.target.value)}
              />
            </div>
            <div className="form-row">
              {/* #78: 신규 등록의 Lv0 출처 주소는 필수다. */}
              <label htmlFor="reg-source-url">
                출처 주소 입력
                <FieldTag required={lv0} />
              </label>
              <input
                id="reg-source-url"
                className="inp"
                data-testid="reg-source-url"
                placeholder={LV0_SOURCE_URL_PLACEHOLDER}
                value={props.sourceUrl}
                onChange={(e) => props.onSourceUrl(e.target.value)}
              />
            </div>
            {/* ⭑ **⟨WU-B6 · PRD-19⟩ Lv0 전용 칸.** 슬롯 자체는 블록 안에 늘 있고 Lv0 이
                아니면 **안이 비었다** — 자리를 없애면 시험이 「블록이 없다」와
                「Lv0 이 아니다」를 못 가른다. */}
            <div className="form-row" data-testid="reg-source-lv0-slot">
              {lv0 ? (
                <div data-testid="reg-source-lv0">
                  <div className="form-row">
                    <label htmlFor="reg-source-downloaded-on">
                      다운로드 일자 입력
                      <FieldTag required />
                    </label>
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
                </div>
              ) : null}
            </div>
          </div>
        ) : null}
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
  fileCount?: number;
  onRemoveFiles?: () => void;
  lineage: { confirmed: number; total: number } | null;
  status: UploadStatus | null;
  projectSource: ProjectSource;
  name: string;
  onName: (v: string) => void;
  summary: string;
  onSummary: (v: string) => void;
  variables: VariableRow[];
  onVariables: (v: VariableRow[]) => void;
  onVariablesBlocked: (message: string) => void;
  crs: string;
  onCrs: (v: string) => void;
  gridDescription: string;
  onGridDescription: (v: string) => void;
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
  submitting?: boolean;
  submitLabel?: string | undefined;
  /** 생성 요청 중 자식의 초안 상태는 보존하고 입력 표면만 감춘다. */
  interactionHidden?: boolean | undefined;
}) {
  const { step } = props;
  /**
   * 분석이 아직 안 끝났는가 (① · rev1 `anNext.disabled`).
   * `status` 가 아직 없으면 **접수·분석 중**이다 — 모르는 것을 끝났다고 하지 않는다.
   *
   * ⭑ ⟨`#40` 두 번째 잠금⟩ **「분석이 끝났다」는 `ready || failure` 다.** 워커는 실패에
   * `ready=False` 를 함께 쓰므로(`d5_ingestion.py` `_fail`) `ready` 만 보면 실패한 업로드가
   * 여기서 영영 ① 에 선다. 서버는 실패분의 등록을 201 로 받는다
   * (`test_dataset_registration.py` `test_a_failed_pipeline_does_not_block_registration`).
   * ⛔ 미리보기·격자 감지처럼 **분석 산출물이 실제로 필요한 자리는 `ready` 단독으로 남긴다.**
   */
  const analyzing = !(props.status?.ready || props.status?.failure);
  /**
   * ① 의 **분류·유형·가공 단계가 비어 있으면 다음 단계 이동이 막힌다** (수용 기준 2).
   */
  const classifyBlocked = step === 1 && (!props.category || !props.dataType || !props.level);
  return (
    <div
      className="regarea"
      data-testid="reg-area"
      hidden={props.interactionHidden}
      inert={props.interactionHidden ? true : undefined}
    >
      {/* 표시기 — 한 번에 한 단계만 보이고, 눌러서 아무 단계로나 간다 (§8) */}
      <div className="regsteps" data-testid="reg-steps">
        {([1, 2, 3] as Step[]).map((s) => (
          <button
            type="button"
            key={s}
            className={s === step ? 'is-active' : ''}
            aria-current={s === step ? 'step' : undefined}
            disabled={s > 1 && (!props.category || !props.dataType || !props.level)}
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
          <span className="rs-fn">{props.fileName}{(props.fileCount ?? 1) > 1 ? ` 외 ${(props.fileCount ?? 1) - 1}개` : ''}</span>
          {props.onRemoveFiles ? <button type="button" className="rs-x" aria-label="올린 파일 모두 빼기" onClick={props.onRemoveFiles}>×</button> : null}
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
            summary={props.summary}
            onSummary={props.onSummary}
            variables={props.variables}
            onVariables={props.onVariables}
            onVariablesBlocked={props.onVariablesBlocked}
            crs={props.crs}
            onCrs={props.onCrs}
            gridDescription={props.gridDescription}
            onGridDescription={props.onGridDescription}
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
            disabled={props.submitting || (props.lineageConflicts ?? 0) > 0}
            onClick={props.onSubmit}
          >
            {props.submitting ? '저장 중…' : props.submitLabel ?? '데이터셋 만들기 →'}
          </button>
        )}
      </div>
    </div>
  );
}
