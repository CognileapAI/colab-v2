// S-04 업로드 **전체 화면 모달** — 정본 `Policy_업로드와_계보_확정.md` §7·§8·§9.
//
// 이 파일이 모달의 골격이다. ③ 은 `components/lineage/LineageStep` 이 이 골격 위에 얹는다 —
// 얹는 자리는 `lineageStep` 슬롯 하나이고, 넘겨받는 것은 `LineageStepContext`(`types.ts`)다.
//
// 골격이 지키는 것
//  - **화면이 아니라 모달**이다. 라우트를 만들지 않는다 (`Policy_공통_기반 §2.3`).
//  - 등록 단계가 열려 있을 때만 닫기 확인을 받는다. 뷰어만 보던 상태면 잃을 것이 없다.
//  - **미리보기는 등록 내내 접히지 않는다** (§8 — 정본이 그렇게 못 박았다).
//  - **등록 결정 게이트 전에는 D3 에 아무것도 만들지 않는다** (`〈64〉` — `createDataset` 호출 자체가 없다).
//  - 임시 업로드 원장(`d5_*`)은 그 진술의 대상이 아니다 — 접수는 파일을 처리하기 위한 상태다.
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAccount } from '../../permission/session';
import { LineageStep } from '../lineage/LineageStep';
import type { ParentCard } from '../lineage/types';
import { Toast } from '../common/Toast';
import { type AccessState } from '../common/accessState';
import {
  ANALYZED_CHIP,
  ANALYZING_CHIP,
  FILE_REMOVED_NOTICE,
  isValidSourceDownloadedOnShape,
  SOURCE_DOWNLOADED_ON_INVALID,
  UPLOAD_CLOSE_KEEP,
  UPLOAD_CLOSE_LEAVE,
  UPLOAD_CLOSE_TITLE,
  uploadCloseMessage,
} from '../common/toastCopy';
import { collectDrop } from './dropTree';
import { ESC_LAYER_ATTR } from './escLayer';
import { FileDropCard, keepOneExtension, MIXED_EXTENSION_NOTICE } from './FileDropCard';
import { PreviewPanel } from './PreviewPanel';
import { LV0, RegisterArea, type Step } from './RegisterArea';
import {
  DEFAULT_CATEGORY,
  DEFAULT_DATA_TYPE,
  DEFAULT_PROCESSING_LEVEL,
  MISSING_CATEGORY_MESSAGE,
} from './axisDict';
import {
  emptyVariableRow,
  variablesPayload,
  type VariableRow,
} from '../common/VariableTable';
import { EMPTY_PARTS, assemble, type PeriodParts } from './periodParts';
import { previewNavigation } from '../preview/handoff';
import { forgetPending, rememberPending } from './pendingStore';
import {
  GridAxisTaken,
  NoResolvedGrid,
  RegisterRejected,
  TransferInterrupted,
  UploadGone,
  type FileKind,
  type LineageStepContext,
  type LineageStepRender,
  type IncompleteTransferItem,
  type PickedFile,
  type PickedProject,
  type UploadLineageParent,
  type UploadSources,
  type UploadStatus,
} from './types';

/**
 * 닫기 확인보다 **위에 있는 층**이 스스로 붙이는 표식 (PRD-39 ⑭ · 확장보기 · 찾기 · 계보 수정).
 * 표식이 떠 있는 동안 업로드 모달은 Esc 를 처리하지 않는다.
 *
 * ⭑ ⟨advisor ② · F7⟩ **정의는 `escLayer.ts` 로 내렸다** — 위 층들이 이 파일을 import 하면
 *   `UploadModal → PreviewPanel → PreviewExpandOverlay → UploadModal` 순환이 선다.
 *   여기서는 종전 import 경로를 유지하려고 그대로 다시 내보내기만 한다.
 */
export { ESC_LAYER_ATTR } from './escLayer';

/** 업로드 상태 확인 간격. 이벤트 ②~⑦ 의 결과가 오기를 기다린다. */
const STATUS_POLL_MS = 1000;

/**
 * ① 파일 분석 **3단계** 표시 — rev1 `pbStatus` 문면 축자.
 *
 * 종전 표시는 바이트 진행 바 하나였다. 바이트가 100% 여도 서버가 헤더를 읽는 동안은
 * 아무 말이 없어, 사람은 끝난 줄 알고 [다음]을 누르고 빈 칸을 본다. 세 단계가 그 사이를 말한다.
 *
 * ⚠ **rev1 의 `파일 읽는 중…` 은 여기 서지 않는다** — 화면이 가진 사실은 「전송 중 /
 *    접수됨·미준비 / 준비됨」 셋이고, 넷째 단계를 세울 근거가 없다. 없는 상태를 지어내
 *    문면만 늘리면 화면이 거짓을 말한다.
 */
export const RECEIVING_STAGE = '파일 올리는 중…';
export const ANALYZE_STAGES = [
  RECEIVING_STAGE,
  '확장자·용량 확인 중…',
  '분석 완료 · 확장자와 용량을 읽었어요',
] as const;

/**
 * ③ 파일 빼기 고지 — 문면의 자리는 `common/toastCopy.ts` 하나다 (PRD-43).
 * 여기서는 이미 이 이름으로 부르던 곳을 위해 다시 내보내기만 한다.
 */
export { FILE_REMOVED_NOTICE };

/** 파일명에서 데이터셋 이름 초안을 만든다 (`Policy §5` — 기본값 = 파일명에서 생성). */
function nameFromFile(fileName: string): string {
  const dot = fileName.lastIndexOf('.');
  return dot > 0 ? fileName.slice(0, dot) : fileName;
}

/**
 * **격자 후주입 모드.** 들어오면 이 모달은 「기준 격자 추가」가 된다.
 *
 * 사람에게 그 조작은 **파일 업로드**다(Ted 2026-08-25 판정 · 사용자 관점 우선) — 그래서
 * 새 화면 개념을 만들지 않고 이 모달을 그대로 쓴다. 진행 표시 · 감지 · 판별 사다리 ·
 * 11 상태가 전부 같은 코드다. 바뀌는 것은 **끝의 한 걸음**뿐이다:
 * 「연구실에 등록」 대신 「이 데이터셋에 반영」이고, 그때 `uploadId` 와 `datasetId` 가
 * 한 요청으로 간다. **짝은 이 컴포넌트의 상태로만 존재한다** — 서버에 보관되지 않는다.
 */
export interface GridAttachTarget {
  datasetId: string;
  datasetName?: string | undefined;
  /** 반영이 끝난 뒤 상세를 다시 읽게 하는 자리. */
  onAttached?: (() => void) | undefined;
}

export function UploadModal(props: {
  sources: UploadSources;
  lineageStep?: LineageStepRender | undefined;
  attach?: GridAttachTarget | undefined;
  onClose: () => void;
}) {
  const account = useAccount();
  const navigate = useNavigate();
  const { upload } = props.sources;

  const [picked, setPicked] = useState<PickedFile[]>([]);
  const [uploadId, setUploadId] = useState<string | null>(null);
  const [status, setStatus] = useState<UploadStatus | null>(null);
  const [statusIssue, setStatusIssue] = useState<{ message: string; retrying: boolean; gone?: boolean } | null>(null);
  const [statusRetry, setStatusRetry] = useState(0);
  const [registerOpen, setRegisterOpen] = useState(false);
  const [step, setStep] = useState<Step>(1);
  const [confirmClose, setConfirmClose] = useState(false);
  /** 실제 그림은 데이터셋 등록 뒤 별도 PUT할 때까지 모달이 보존한다. */
  const [representativeFile, setRepresentativeFile] = useState<File | null>(null);
  /** 등록 성공 뒤 그림 PUT만 재시도하기 위한 불변 식별자. */
  const [createdDatasetId, setCreatedDatasetId] = useState<string | null>(null);
  /** 비동기 드롭 수집도 등록 완료 전 렌더의 상태를 다시 쓰지 못하게 하는 불변 표식. */
  const committedDatasetIdRef = useRef<string | null>(null);

  const [name, setName] = useState('');
  // 파일명에서 만든 **자동 초안**. 종료 확인 판정에서 이름 칸을 「사람이 적은 값」으로 세려면
  // 초안과 견줄 자리가 필요하다 — 초안 그대로면 사람은 아직 아무것도 적지 않은 것이다 (WU-A9).
  const [nameDraft, setNameDraft] = useState('');
  const [topic, setTopic] = useState('');
  // ⭑ **⟨WU-B3 · PRD-01·02·03⟩ 분류 3축 — 기본 선택값이 있고 그대로 실려 나간다.**
  // 계약 `DatasetCreate.required` 에 `category`·`dataType` 이 올라(20차 ㉯) 서버가 400
  // 「분류를 골라 주세요」를 내므로, 화면은 **늘 값을 실어 보낸다**.
  // ⛔ 기본값은 「사람이 적은 값」이 아니다 — `hasHumanInput` 이 이 셋을 세지 않는다.
  const [category, setCategory] = useState(DEFAULT_CATEGORY);
  const [dataType, setDataType] = useState(DEFAULT_DATA_TYPE);
  const [level, setLevel] = useState(DEFAULT_PROCESSING_LEVEL);
  const [summary, setSummary] = useState('');
  const [sourceLabel, setSourceLabel] = useState('');
  // ⭑ **⟨WU-B6 · PRD-19⟩ Lv0 전용 두 칸.** `sourceLabel` 옆에 두되 **다른 축**이다 —
  //   그쪽은 Lv 무관 상시 노출이고 이 둘만 ① 의 Lv 로 표시가 갈린다(미결-11 ⓐ).
  //   ⛔ Lv 를 바꿔도 **값을 지우지 않는다** — 되돌아오면 적어 둔 것이 그대로 있어야 한다.
  //      「숨은 동안 전송하지 않는다」는 저장을 지우는 것이 아니라 **싣지 않는 것**이다.
  const [sourceUrl, setSourceUrl] = useState('');
  const [sourceDownloadedOn, setSourceDownloadedOn] = useState('');
  // ⭑ ⟨advisor ② F1 · WU-B6⟩ 형상 오류 인라인 문구 — 칸 아래에 선다. 값을 고치면 지운다.
  const [sourceDownloadedOnError, setSourceDownloadedOnError] = useState<string | null>(null);
  // ⭑ **⟨20차 해제 · PRD-11 · WU-B4 · advisor ② ㊁⟩ 공개 범위 — 처음은 `null` 이다.**
  // `null` = **사람이 셀렉트를 건드리지 않았다** 이고, 그대로 등록하면 요청에서 열쇠가
  // 빠져 서버가 연구실 기본값을 따른다(PRD-11 「NULL = 연구실 기본값 · 현행 의미 유지」).
  // ⛔ 기본값을 골라 넣지 않는다 — 넣으면 연구실 기본값을 바꿔도 옛 값으로 굳고,
  //    기본값이 `잠김` 인 연구실에서 파일만 올린 사람의 데이터셋이 `열림` 으로 저장된다.
  const [accessState, setAccessState] = useState<AccessState | null>(null);
  // 변수·기간·좌표계 — **사람이 적는 자유 입력** (정본 `VAL-006` · 스펙 18·19·20).
  // 화면은 문자열로 들고 있다가 제출 자리에서 계약 형상으로 바꾼다.
  // ⭑ **⟨WU-B2 · PRD-16⟩ 변수는 문자열이 아니라 5열 행 집합이다.** 한 행으로 시작한다 —
  // 「행이 0개인 데이터셋은 허용하지 않는다」와 「+ 변수 추가」가 같은 규율이고, 빈 첫 행은
  // 제출 자리에서 걸러진다(`variablesPayload`)라 「안 적었다」가 그대로 표현된다.
  const [variables, setVariables] = useState<VariableRow[]>([emptyVariableRow()]);
  // 마지막 행 삭제 차단 고지. 공통 토스트를 탄다(PRD-43 과 같은 컴포넌트).
  const [variableNotice, setVariableNotice] = useState<string | null>(null);
  const [crs, setCrs] = useState('');
  const [gridDescription, setGridDescription] = useState('');
  // ⭑ **⟨19차 해제 · PRD-18⟩ 기간의 최소 단위.** `''` = 미지정이고 그것이 기본이자 정상이다 —
  // 계약의 `granularity` 는 그때 `null` 로 나가고 기간 자체가 실리지 않는다.
  // ⭑ **⟨R-C · WU-C8 · §5-14⟩ 이 셋을 채우는 자리는 달력 팝오버 **하나**다** — 종전
  //   날짜 두 칸(`periodStart`·`periodEnd`)은 인라인 칸과 함께 걷혔다.
  const [granularity, setGranularity] = useState('');
  const [startParts, setStartParts] = useState<PeriodParts>({ ...EMPTY_PARTS });
  const [endParts, setEndParts] = useState<PeriodParts>({ ...EMPTY_PARTS });
  // ⭑ **⟨19차 해제 · PRD-17⟩ 관측 간격 두 칸.** 화면은 문자열로 쥐고 보낼 때 숫자로 만든다 —
  // 입력 중인 `1` 과 `10` 사이를 숫자로 쥐면 지우는 순간 값이 튄다.
  const [intervalValue, setIntervalValue] = useState('');
  const [intervalUnit, setIntervalUnit] = useState('');
  const [projects, setProjects] = useState<PickedProject[]>([]);
  const [lineage, setLineage] = useState<{ confirmed: number; total: number } | null>(null);
  const [lineageParents, setLineageParents] = useState<UploadLineageParent[]>([]);
  /**
   * ⭑ **⟨WU-B5 · PRD-09⟩ 사후 충돌 건수.** 1건 이상이면 `데이터셋 만들기` 가 비활성이다.
   * ⛔ 연결을 지우지 않는다 — 되돌리면 이 수가 0 이 되고 버튼이 다시 눌린다.
   */
  const [lineageConflicts, setLineageConflicts] = useState(0);
  /**
   * ⭑ **⟨WU-B5 · PRD-09⟩ ③ 의 연결 카드.** ③ 은 단계 이동마다 언마운트되므로
   * 이 상태가 모달에 있어야 「① 에 다녀와도 연결이 남는다」가 성립한다.
   */
  const [lineageCards, setLineageCards] = useState<ParentCard[]>([]);
  /**
   * ⭑ **⟨WU-B8 · PRD-27⟩ 「가공 전 데이터를 못 찾았어요」 선언.**
   * ③ 이 단계 이동마다 언마운트되므로 연결 카드와 같이 모달이 쥔다.
   */
  const [lineageUnknown, setLineageUnknown] = useState(false);
  const [gridSkipped, setGridSkipped] = useState(false);
  /** ③ 파일을 뺐다는 고지. 토스트가 스스로 사라질 때 함께 내린다. */
  const [removedNotice, setRemovedNotice] = useState(false);
  const [mixedGlobal, setMixedGlobal] = useState(false);
  const [nameError, setNameError] = useState(false);
  //: ⭑ **⟨19차 해제 · PRD-15⟩ 설명도 이름과 같은 자리에 선다** — 필수 칸이 둘이 됐다.
  //: 서버가 400 을 내지만, 사람을 왕복시키지 않고 **적을 칸으로 먼저 데려간다**.
  const [summaryError, setSummaryError] = useState(false);
  const [registerError, setRegisterError] = useState<string | null>(null);
  // 접수(create) 실패. **`registerError` 와 섞지 않는다** — 그 자리는 등록 카드 안이라
  // 접수 시점엔 닫혀 있고, `submit()` 이 그것을 null 로 지운다. 수명이 다른 두 사실이다.
  const [intakeError, setIntakeError] = useState<string | null>(null);
  // 같은 파일로 다시 시도하는 유일한 길 — 재실행 트리거가 `signature` 뿐이라
  // 파일이 그대로면 effect 가 다시 돌지 않았다. `resumeArm` 을 재사용하지 않는다(이름이 거짓이 된다).
  const [retryArm, setRetryArm] = useState(0);
  // 전송 진행률 (`§D.7` ① — 실재·크기 비례라 **여기만 퍼센트가 정직하다**).
  // 접수가 끝나면 null 로 되돌린다 — 안 그러면 `격자 전송 중` 이 뒤 상태를 영구히 가린다.
  const [transfer, setTransfer] = useState<{ sentBytes: number; totalBytes: number } | null>(null);
  const [attaching, setAttaching] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const submitLock = useRef(false);
  /** 닫힌 모달의 register/대표 그림 응답은 화면 전이와 상태를 바꾸지 못한다. */
  const mutationLifecycle = useRef(0);
  useEffect(() => {
    const current = ++mutationLifecycle.current;
    return () => {
      if (mutationLifecycle.current === current) mutationLifecycle.current += 1;
    };
  }, []);
  // S-08 로 넘길 짐 중 **이 모달만 아는 것** — 어느 렌더를 이어 보게 할지와, 짝 파일 없이 그렸는지.
  const [rendered, setRendered] = useState<{
    renderId: string;
    withoutReferenceGrid: boolean;
  } | null>(null);
  // 미완결 프리사인드 전송 (〈338〉) — 저장 모드 s3 에서만 값이 온다 (local 은 빈 배열)
  const [incomplete, setIncomplete] = useState<IncompleteTransferItem[]>([]);
  // 재개 대상: 표시용 상태 + 접수 effect 가 읽는 ref. **성공 시에만 비운다** — 상태를
  // deps 로 쓰면 성공 직후 effect 가 한 번 더 돌아 같은 파일이 새 업로드로 중복 접수된다
  // (시험 「resumeUploadId 를 싣는다」가 실제로 잡아낸 실수).
  const [resumeId, setResumeId] = useState<string | null>(null);
  const resumeRef = useRef<string | null>(null);
  // 재개의 **출처**. `banner` = 사람이 [이어서 올리기]를 눌렀다 — 파일을 다시 고르는 것이 정본
  // 흐름이라 유지한다. `failure` = 실패가 자동으로 무장한 것 — **다른 파일을 놓으면 버린다**.
  // 안 버리면 파일을 바꿔 다시 하려는 사람에게 「같은 파일을 다시 골라야 해요」가 뜬다.
  const resumeFromRef = useRef<'banner' | 'failure' | null>(null);
  /** 실패로 재개를 무장한 시점의 파일 서명 — 이것과 달라지면 그 무장은 무효다. */
  const armedSignatureRef = useRef<string>('');
  // ⭑ ⟨advisor ② · F3⟩ 배경 클릭의 **눌린 자리**. 모달 안에서 눌러 배경에서 뗀 드래그는
  //   click.target 이 공통 조상(배경)이 되므로, 눌린 자리까지 배경일 때만 닫는다.
  const downOnBackdrop = useRef(false);
  const [resumeArm, setResumeArm] = useState(0);
  const statusTimer = useRef(0);
  const bodyRef = useRef<HTMLDivElement>(null);
  useEffect(() => { if (bodyRef.current) bodyRef.current.scrollTop = 0; }, [step, registerOpen]);

  /*
   * PRD-13 — **모달을 열 때마다 ① 로 되돌린다.** rev1 축자 = 「단계가 둘일 때는 안 드러났고
   * 셋이 되며 나왔다」.
   *
   * ⭑ ⟨advisor ② · F5⟩ **리셋은 `UploadEntry:71` 언마운트가 한다** — 그 자리가
   * `{open && <UploadModal …/>}` 라 닫을 때 이 컴포넌트가 통째로 사라지고, 다시 열면
   * `useState(1)`·`useState(false)` 초깃값이 그대로 ① 이다. 여기 있던 마운트 전용
   * `useEffect(…, [])` 는 그 초깃값을 한 번 더 쓰는 무동작이었고, 「DOM 잔존 구현이어도
   * 같다」를 증명하지도 못했다(그 구현에서는 마운트가 일어나지 않는다). 지운다 —
   * 하는 일이 없는 코드가 규칙을 지키는 것처럼 읽히는 자리를 남기지 않는다.
   * ⚠ 모달을 DOM 에 남기는 구현으로 바꾸려면 **그 커밋이** 이 리셋을 다시 세워야 한다.
   */

  const attach = props.attach;
  /** 후주입 모드의 기본 파일 종류. 사람이 격자를 붙이러 왔으므로 격자가 기본이다. */
  const defaultKind: FileKind = attach ? '기준 격자 파일' : '본체';

  // 미완결 전송 목록 (〈338〉) — 후주입 모드에서는 묻지 않는다 (격자를 붙이러 온 자리다).
  const refreshIncomplete = useCallback(() => {
    if (attach || !upload.incomplete) return;
    void upload.incomplete().then(setIncomplete).catch(() => setIncomplete([]));
  }, [attach, upload]);
  useEffect(() => {
    refreshIncomplete();
  }, [refreshIncomplete]);

  // 놓은 파일(이름·종류)이 바뀌면 접수를 다시 한다. 파일 종류는 접수 시점에 정해져 있어야 한다
  // (이벤트 `FileRef.kind` 가 required 다). **축은 보내지 않는다** — 서버가 파일에서 판별한다.
  // 폴더 드롭에서는 다른 폴더의 같은 이름·같은 크기가 실재하므로 상대 경로가 정체성에 든다
  const signature = picked
    .map((p) => `${p.relativePath ?? p.file.name}:${p.file.size}:${p.kind}`)
    .join('|');
  useEffect(() => {
    if (picked.length === 0) {
      setUploadId(null);
      setStatus(null);
      return;
    }
    let alive = true;
    // 새 접수 동안 이전 파일의 ready·그림을 등록 근거로 쓰지 않는다.
    setUploadId(null);
    setStatus(null);
    setRendered(null);
    setIntakeError(null);
    // ⚠ **실패로 무장한 재개는 파일이 바뀌면 버린다.** 안 버리면 파일을 바꿔 다시 하려는
    //    사람에게 「이어올리려면 같은 파일을 다시 골라야 해요」가 뜬다 — 그는 바꾸려던 것이다.
    //    사람이 배너에서 직접 누른 재개(`banner`)는 유지한다: 같은 파일을 다시 고르는 것이 그 흐름이다.
    if (resumeFromRef.current === 'failure' && signature !== armedSignatureRef.current) {
      resumeRef.current = null;
      resumeFromRef.current = null;
    }
    const label = picked.length === 1 && picked[0]
      ? (picked[0].relativePath ?? picked[0].file.name)
      : `파일 ${picked.length}건`;
    const resume = resumeRef.current;
    setTransfer(null);
    // 정수 퍼센트가 바뀔 때만 상태를 옮긴다 — `xhr.upload.onprogress` 는 초당 수십 번 온다.
    let lastPct = -1;
    void upload
      .create(picked, { sourceLabel: label,
                        ...(resume ? { resumeUploadId: resume } : {}),
                        onProgress: (p) => {
                          if (!alive || p.totalBytes <= 0) return;
                          const pct = Math.round((p.sentBytes / p.totalBytes) * 100);
                          if (pct === lastPct) return;
                          lastPct = pct;
                          setTransfer(p);
                        } })
      .then((receipt) => {
        if (!alive) return;
        setTransfer(null);
        setUploadId(receipt.uploadId);
        // **접수는 됐고 등록은 안 됐다** — 새로고침해도 이 업로드로 돌아올 수 있게 적어 둔다.
        if (account?.labId) rememberPending(account.labId, receipt.uploadId);
        if (resume) {                      // 이어올리기가 접수까지 갔다 — 배너 항목이 사라진다
          resumeRef.current = null;
          resumeFromRef.current = null;
          setResumeId(null);
        }
        refreshIncomplete();
        const firstBody = receipt.files.find((f) => f.kind === '본체') ?? receipt.files[0];
        const draft = firstBody ? nameFromFile(firstBody.fileName) : '';
        setNameDraft(draft);
        setName((cur) => cur || draft);
      })
      .catch((e: unknown) => {
        // §9 업로드 중단 — 「올리다가 끊겼어요. 다시 시도해 주세요.」 파일 놓기부터 다시 한다.
        // 재개 중이었다면 배너가 남아 있어 같은 자리에서 다시 시도할 수 있다.
        if (!alive) return;
        setTransfer(null);
        setUploadId(null);
        // **엔진이 만든 문장을 그대로 올린다** — `transferSource`·`uploadSource` 의 문장은 이미
        // 사람 말이고 무엇이 잘못됐는지 말한다(거부된 파일 이름·사유·재개 안내). 여기서 뭉개면
        // 사람은 「눌렀는데 아무 일도 안 일어난다」만 본다.
        setIntakeError(
          e instanceof Error && e.message ? e.message : '올리다가 끊겼어요. 다시 시도해 주세요.',
        );
        // **원장이 이미 선 실패**라면 그 전송을 재개 대상으로 무장한다 — [다시 시도]가
        // 「새로 시작」이 아니라 「이어서」가 된다. 이것이 없으면 시도마다 원장이 하나씩 는다.
        if (e instanceof TransferInterrupted) {
          resumeRef.current = e.uploadId;
          resumeFromRef.current = 'failure';
          armedSignatureRef.current = signature;
        }
        // 원장이 선 뒤에 실패했으면 **이어올리기 배너**가 뜬다 — 빠진 파트만 다시 올라간다.
        // 새 UI 를 만들지 않고 이미 있는 정본 경로를 쓴다.
        refreshIncomplete();
      });
    return () => {
      alive = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [signature, upload, resumeArm, retryArm]);

  // 이벤트 ②~⑦ 의 결과를 읽는다 — 새 사실을 만들지 않는다.
  useEffect(() => {
    setStatusIssue(null);
    if (!uploadId) return;
    let alive = true;
    let failures = 0;
    const tick = async () => {
      try {
        const s = await upload.status(uploadId);
        if (!alive) return;
        failures = 0;
        setStatusIssue(null);
        setStatus(s);
        if (!s.ready && !s.failure) statusTimer.current = window.setTimeout(tick, STATUS_POLL_MS);
      } catch (e) {
        if (!alive) return;
        if (e instanceof UploadGone) {
          setStatusIssue({ message: '이 파일은 더 이상 없어요. 다시 올려 주세요.', retrying: false, gone: true });
          return;
        }
        failures += 1;
        const retrying = failures < 3;
        setStatusIssue({
          message: retrying
            ? '분석 상태를 확인하지 못했어요. 연결을 다시 확인하고 있어요.'
            : '분석 상태를 확인하지 못했어요. 다시 시도해 주세요.',
          retrying,
        });
        if (retrying) statusTimer.current = window.setTimeout(tick, STATUS_POLL_MS * failures);
      }
    };
    void tick();
    return () => {
      alive = false;
      window.clearTimeout(statusTimer.current);
    };
  }, [uploadId, upload, statusRetry]);

  const hasReferenceGrid = picked.some((p) => p.kind === '기준 격자 파일');
  /**
   * ① 분석 단계 1·2·3. **모르면 앞 단계에 둔다** — 끝났다고 말한 뒤 아니었던 것이
   * 이 화면에서 제일 나쁜 실패다(사람이 [다음]을 눌러 빈 칸을 본다).
   */
  const analyzeStage: 1 | 2 | 3 = !uploadId ? 1 : status?.ready ? 3 : 2;
  // 진행률은 본체+격자 **합계**다. 그래서 격자 블록에 그것을 넘기는 것은 **격자만 올릴 때뿐**이다
  // — 본체가 섞여 있으면 그 퍼센트는 격자의 진행이 아니고, 화면이 틀린 말을 하게 된다.
  const gridOnly = picked.length > 0 && picked.every((p) => p.kind === '기준 격자 파일');
  // 격자를 올린 뒤 워커가 축을 확정하거나 거절할 때까지 — `ready` 가 그 판정을 포함한다
  // (`〈79〉`·`§E.3b` — 「본체 감지가 끝났고 함께 올라온 격자의 축이 확정되거나 거절됐다」).
  const gridVerifying = hasReferenceGrid && status !== null && !status.ready && !status.failure;
  // ⟨동결 4회 해제 · `PLAN-SoT §9-〈88〉` 묶음 7⟩ **워커가 거절한 격자의 사유.**
  // 이전에는 이 사실이 seam 을 건너오지 않아, 화면이 등록 **전** 거절 상태를 만들 근거가
  // **viz-render 의 렌더 실패 문장**뿐이었다 — 판정자와 인용처가 다른 기계였다(스윕 `B-2`).
  // 거절된 격자는 `files` 에 행이 없어 **말없이 사라진다**. 그 자리를 이것이 말한다.
  const gridRejection = status?.gridRejections?.[0] ?? null;
  const bodyName =
    picked.find((p) => p.kind === '본체')?.file.name ?? picked[0]?.file.name ?? '';
  // 헤더에서 읽은 값 중 FE 표면이 실제로 실어 주는 것은 `byteSize` 하나다 (`preview/types.ts`)
  const bodyByteSize = (status?.files.find((f) => f.kind === '본체') ?? status?.files[0])?.byteSize;

  /**
   * **사람이 입력한 값이 하나라도 있나** — 종료 확인의 판정식이다 (WU-A9 · PRD-14 · 미결-15 ⓐ).
   *
   * 세는 것 = ①②③ 의 **사람 입력 필드 전부 ＋ 확정된 계보 부모 건수**.
   *  - ① 이름(자동 초안과 다를 때만) · 주제 · 변수 · 기간 시작·끝 · 좌표계 · 설명
   *  - ② 담은 프로젝트·논문 건수
   *  - ③ 원천 표기 · **확정된** 계보 부모 건수(`LineageStep` 이 확인된 것만 올린다)
   *  - ② 관측 간격 값·단위 · 기간 최소 단위
   *
   * 세지 않는 것 = **자동으로 채워진 값**. 파일명에서 만든 이름 초안 · 확장자 · 용량 ·
   * 읽기 전용 가공 단계 칸 · (R-B 가 더할) 기본 선택값 `Lv2`·`연구실 구성원 전체`.
   * 사람이 고르지 않은 기본값은 「잃을 것」이 아니다 — 그것까지 세면 파일만 올린 사람이
   * 매번 되묻히고, 그것이 고치려던 바로 그 증상이다.
   */
  const hasHumanInput =
    (name.trim() !== '' && name !== nameDraft) ||
    topic.trim() !== '' ||
    summary.trim() !== '' ||
    variables.some((v) => v.name.trim() !== '') ||
    crs.trim() !== '' ||
    sourceLabel.trim() !== '' ||
    // ⭑ ⟨WU-B6 · PRD-19⟩ Lv0 두 칸도 사람이 적은 값이다 — 빠져 있으면 출처만 적은
    //   사용자가 Esc 한 번에 되묻히지 않고 잃는다(`advisor ② · F2` 와 같은 자리).
    sourceUrl.trim() !== '' ||
    sourceDownloadedOn.trim() !== '' ||
    // ⭑ ⟨advisor ② · F2⟩ 관측 간격 3필드도 사람이 적은 값이다. 빠져 있으면 간격만 적은
    //   사용자가 Esc·배경 클릭 한 번에 되묻히지 않고 잃는다 — PRD-14 가 없애려던 반대 증상.
    intervalValue.trim() !== '' ||
    intervalUnit.trim() !== '' ||
    granularity.trim() !== '' ||
    projects.length > 0 ||
    // ⭑ ⟨WU-A9R · PRD-14 증분⟩ 담은 프로젝트 건수와 **대표 그림 교체 여부**를 함께 센다.
    //   둘 다 사람이 고른 것이라 닫으면 사라진다. 자동 채움값(`Lv2`·`연구실 구성원 전체`·
    //   확장자·용량)은 여전히 세지 않는다.
    representativeFile !== null ||
    gridDescription.trim() !== '' ||
    // ⭑ ⟨advisor ② · F3⟩ 세 축도 **사람이 고르는 칸**이다. 기본값 그대로면 세지 않고
    //   (파일만 올린 사람을 되묻지 않는다), 기본값에서 바꾼 순간부터 「잃을 것」이 된다.
    category !== DEFAULT_CATEGORY ||
    dataType !== DEFAULT_DATA_TYPE ||
    level !== DEFAULT_PROCESSING_LEVEL ||
    // ⭑ ⟨WU-B4 · PRD-11⟩ 공개 범위도 같은 규율이다 — 고른 순간부터 「잃을 것」이다.
    accessState !== null ||
    lineageParents.length > 0 ||
    // ⭑ ⟨advisor ② · Fix 3⟩ **확인 전 연결 카드도 사람이 고른 것이다**(PRD-14 「입력한 값
    //   하나라도」). 카드 상태 승격 전에는 언마운트로 소실돼 셀 수 없었고, 지금은 남는다.
    lineageCards.length > 0;

  const onLineageProgress = useCallback(
    (p: { confirmed: number; total: number }) => setLineage(p),
    [],
  );
  const onLineageParentsChange = useCallback(
    (parents: UploadLineageParent[]) => setLineageParents(parents),
    [],
  );
  const onLineageConflictChange = useCallback((count: number) => setLineageConflicts(count), []);
  const onLineageUnknownChange = useCallback((next: boolean) => setLineageUnknown(next), []);
  /**
   * ⭑ **⟨WU-B8 · PRD-27⟩ 실제로 실리는 값 — 화면과 요청이 한 식을 쓴다.**
   * 확정 부모가 1건이라도 있으면 **서버가 400** 이고(「모른다」와 「이것이 부모다」를 한
   * 요청에 담을 수 없다), Lv0 이면 판정 ⑷ 가 이미 `원천` 이라 물을 것이 없다. 체크한 뒤
   * ① 로 돌아가 Lv0 을 고르거나 부모를 붙인 경로에서 옛 `true` 가 그대로 실리는 것을 막는다.
   */
  const lineageUnknownEffective =
    lineageUnknown && lineageParents.length === 0 && level !== 'Lv0';
  /** 안내 줄의 `분류에서 바꾸기` — **자리로 보낼 뿐 값을 고치지 않는다**(PRD-07 축자). */
  const onGoToClassify = useCallback(() => setStep(1), []);
  // ③ 의 슬롯은 그대로 두되, **아무도 얹지 않으면 빈 자리로 남기지 않는다** — 계보 확정은
  // 업로드의 일부이지 선택 부품이 아니다. 바깥에서 넘긴 것이 있으면 그것이 이긴다.
  const lineageStep: LineageStepRender =
    props.lineageStep ?? ((c) => <LineageStep source={props.sources.lineage} ctx={c} />);

  const lineageCtx: LineageStepContext = useMemo(
    () => ({
      uploadId: uploadId ?? '',
      datasetNameDraft: name,
      topic: topic || null,
      // ⭑ **⟨WU-B5 · PRD-07⟩ ① 이 고른 자기 Lv 가 연결 규칙의 기준값이다.**
      processingLevelUserSet: level,
      onGoToClassify,
      onLineageProgress,
      onLineageParentsChange,
      onLineageConflictChange,
      parents: lineageCards,
      onParentsChange: setLineageCards,
      lineageUnknown,
      onLineageUnknownChange,
    }),
    [uploadId, name, topic, level, lineageCards, lineageUnknown, onGoToClassify,
     onLineageProgress, onLineageParentsChange, onLineageConflictChange,
     onLineageUnknownChange],
  );

  /**
   * 격자 파일을 **그 업로드에 직접** 붙인다 (`§E.5` — 재사용·추천 없음).
   * ⚠ **역할은 요청이 선언한다** — `kind` 를 실어 접수하고, 원장 행은 워커가 축을 확정한
   * 뒤에 선다(`〈79〉-㈎`). 화면은 축을 묻지도, 정하지도 않는다.
   */
  function pickGrid(files: File[]) {
    if (files.length === 0 || createdDatasetId) return;
    setGridSkipped(false);
    setPicked((cur) => [
      ...cur,
      ...files.map((file) => ({ file, kind: '기준 격자 파일' as FileKind })),
    ]);
  }

  function pick(files: File[], paths?: ReadonlyMap<File, string>) {
    if (createdDatasetId) return;
    const filtered = keepOneExtension(picked, files);
    setMixedGlobal(filtered.dropped > 0);
    if (!filtered.kept.length) return;
    files = filtered.kept;
    // 파일 종류 기본값은 `본체` 다. 격자는 사람이 골라 바꾼다 (`P2.md §2-20`).
    // **후주입 모드에서는 기본값이 `기준 격자 파일` 이다** — 사람이 격자를 붙이러 왔다.
    // 폴더째 드롭이면 상대 경로가 함께 온다 (`dropTree.ts` · `〈337〉`).
    setPicked((cur) => [
      ...cur,
      ...files.map((file) => {
        const relativePath = paths?.get(file);
        return { file, kind: defaultKind, ...(relativePath ? { relativePath } : {}) };
      }),
    ]);
  }

  function setKind(index: number, kind: FileKind) {
    if (createdDatasetId) return;
    setPicked((cur) => cur.map((p, i) => (i === index ? { ...p, kind } : p)));
  }

  /**
   * ③ **파일 빼기 — 즉시 반영하고 초기화를 고지한다** (rev1 `removeFile()`).
   *
   * 뺀 파일이 남긴 것은 파일 하나가 아니다: 접수(`uploadId`)·분석 상태·자동으로 만든 이름
   * 초안이 전부 그 파일에서 왔다. 목록에서만 지우면 화면은 **없는 파일의 분석 결과**를
   * 계속 보인다. 그래서 고지 문면이 「입력하던 내용은 사라져요」다 — 화면이 실제로 그렇게 한다.
   *
   * ⚠ 마지막 파일을 빼면 등록 단계도 걷는다 — 등록할 대상이 없는 등록 카드는 빈 폼이다.
   */
  function removeFile(index: number | null) {
    // 데이터셋이 생긴 뒤 원본 업로드를 지워 새 create 경로로 돌아갈 수 없다.
    if (createdDatasetId) return;
    setPicked((cur) => index === null ? [] : cur.filter((_, i) => i !== index));
    setRemovedNotice(true);
    // 파일에서 온 것은 파일과 함께 내린다. 접수·상태는 `signature` effect 가 다시 세운다.
    setName('');
    setNameDraft('');
    setTopic('');
    setSummary('');
    setSourceLabel('');
    setVariables([emptyVariableRow()]);
    setCrs('');
    setGridDescription('');
    setGranularity('');
    setIntervalValue('');
    setIntervalUnit('');
    setAccessState(null);
    setLineageUnknown(false);
    setNameError(false);
    setSummaryError(false);
    setVariableNotice(null);
    setRegisterOpen(false);
    setStep(1);
    setRegisterError(null);
    setIntakeError(null);
    setRendered(null);
    setGridSkipped(false);
    setRepresentativeFile(null);
    // ⭑ 세 축도 파일과 함께 **기본 선택값으로** 되돌린다 — 고지 문면이 「입력하던 내용은
    //   사라져요」이고, 사람이 고른 분류가 남으면 화면이 고지와 다른 말을 한다.
    setCategory(DEFAULT_CATEGORY);
    setDataType(DEFAULT_DATA_TYPE);
    setLevel(DEFAULT_PROCESSING_LEVEL);
    // 고지 문면이 「입력하던 내용은 사라져요」다 — 등록 ②③ 의 사람 입력도 함께 내린다.
    // 남겨 두면 파일을 빼고 등록을 다시 열었을 때 지운 파일의 기간·프로젝트·계보가 남아
    // 화면이 고지와 다른 말을 한다.
    setStartParts({ ...EMPTY_PARTS });
    setEndParts({ ...EMPTY_PARTS });
    // ⭑ ⟨WU-B6 · PRD-19⟩ 두 칸도 함께 내린다 — 고지 문면이 「입력하던 내용은 사라져요」다.
    setSourceUrl('');
    setSourceDownloadedOn('');
    setProjects([]);
    setLineage(null);
    setLineageParents([]);
    // ⭑ ⟨advisor ② · Fix 1⟩ 승격된 연결 카드와 충돌 계수도 함께 내린다. 카드 상태가 ③ 에서
    //   이 모달로 올라오면서 파일과 함께 언마운트되던 수명이 없어졌다 — 지우지 않으면
    //   파일을 다시 올린 사람에게 지운 파일의 연결과 `확인 필요` 칩이 그대로 보인다.
    setLineageCards([]);
    setLineageConflicts(0);
    setTransfer(null);
  }

  /**
   * ② **모달 전역 드롭 수신** — 종전에는 드롭존 라벨에만 걸려 있어, 모달이 화면을 가득
   * 채우는데도 그 라벨 밖에 놓으면 브라우저가 파일을 **새 탭으로 열어** 작업이 통째로 날아갔다.
   * 모달이 서 있는 동안 `document` 가 받아 기본 동작을 막고 같은 `pick()` 으로 보낸다.
   */
  useEffect(() => {
    const onDragOver = (e: DragEvent) => e.preventDefault();
    const onDrop = (e: DragEvent) => {
      e.preventDefault();
      if (committedDatasetIdRef.current || !e.dataTransfer) return;
      void collectDrop(e.dataTransfer).then((dropped) => {
        if (committedDatasetIdRef.current || dropped.length === 0) return;
        const paths = new Map(
          dropped.flatMap((d) => (d.relativePath ? [[d.file, d.relativePath] as const] : [])),
        );
        pick(dropped.map((d) => d.file), paths.size > 0 ? paths : undefined);
      });
    };
    document.addEventListener('dragover', onDragOver);
    document.addEventListener('drop', onDrop);
    return () => {
      document.removeEventListener('dragover', onDragOver);
      document.removeEventListener('drop', onDrop);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [defaultKind, picked]);

  /**
   * 「보기만 할게요」 — **등록하지 않겠다는 선택**이고, 정본 §7.2 전이표가 이 선택의 도착지를
   * `미등록 파일 미리보기(S-08)` 로 못 박았다. 모달만 닫으면 파일이 그냥 버려져 그 전이가
   * 제품에 없는 것이 된다(Ted 2026-08-28 완료 정의 ①). 여기서 만드는 사실은 **없다** —
   * `createDataset` 을 부르지 않고, 이미 접수된 업로드의 주소로 이동할 뿐이다.
   */
  function viewOnly() {
    if (!uploadId) {
      // 접수가 아직/못 됐으면 보낼 주소가 없다. **주소를 지어내지 않는다** — 닫기만 한다.
      props.onClose();
      return;
    }
    const nav = previewNavigation({
      uploadId,
      ...(rendered ? { renderId: rendered.renderId } : {}),
      ...(rendered ? { withoutReferenceGrid: rendered.withoutReferenceGrid } : {}),
      // 헤더에서 읽은 값만 넘긴다 — 사람이 붙인 이름·주제는 등록 전이라 자리 자체가 없다
      basicInfo: { ...(bodyByteSize !== undefined ? { byteSize: bodyByteSize } : {}) },
      files: status?.files ?? [],
    });
    props.onClose();
    navigate(nav.to, { state: nav.state });
  }

  function requestClose() {
    // 사람이 적거나 확인한 것이 있을 때만 묻는다 (WU-A9 · PRD-14 · 미결-15 ⓐ).
    // 종전에는 `registerOpen` 만 봤다 — 등록 단계를 열어만 보고 닫아도 되물어서,
    // 잃을 것이 없는 사람에게 확인이 걸렸다. **문면은 그대로 두고 조건만 고친다.**
    if (hasHumanInput) setConfirmClose(true);
    else props.onClose();
  }

  /**
   * Esc 우선순위 (PRD-39 ⑭) — **확장보기 → 찾기 → 계보 수정 → 닫기 확인 → 업로드**.
   *
   * 앞의 세 층은 이 모달이 그리지 않는다(R-B). 그래서 층을 이름으로 찾지 않고, 그 층이
   * 스스로 붙이는 표식 `data-esc-layer` 하나만 본다 — 표식이 하나라도 떠 있으면 업로드는
   * Esc 를 먹지 않는다. 위 층이 없을 때만 닫기 확인 → 업로드 순으로 내려간다.
   * 층이 스스로 표식을 붙이므로 여기에 층 목록을 적어 두 벌로 만들지 않는다.
   */
  useEffect(() => {
    function onKeyDown(e: KeyboardEvent) {
      if (e.key !== 'Escape') return;
      if (document.querySelector(`[${ESC_LAYER_ATTR}]`)) return;
      e.preventDefault();
      if (confirmClose) {
        setConfirmClose(false);
        return;
      }
      // ⭑ ⟨advisor ② · F4⟩ 판정식은 `requestClose()` 한 곳이다 — 갈래를 복제하지 않는다.
      requestClose();
    }
    document.addEventListener('keydown', onKeyDown);
    return () => document.removeEventListener('keydown', onKeyDown);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [confirmClose, hasHumanInput]);

  /**
   * 「이 데이터셋에 반영」 — 후주입의 **마지막 한 걸음**.
   * 화면이 들고 있던 `uploadId` 를 `datasetId` 옆에 놓아 보낸다. 그 짝은 여기서만 존재했다.
   */
  async function confirmAttach() {
    if (!uploadId || !attach) return;
    setAttaching(true);
    setRegisterError(null);
    try {
      await upload.attachGrid(attach.datasetId, uploadId);
      attach.onAttached?.();
      props.onClose();
    } catch (e) {
      setRegisterError(
        e instanceof UploadGone
          ? '이 파일은 더 이상 없어요. 다시 올려 주세요.'
          : e instanceof GridAxisTaken
            ? '이 데이터셋에는 그 축의 기준 격자 파일이 이미 있어요. 바꾸려면 교체를 쓰세요.'
            : e instanceof NoResolvedGrid
              ? '올린 파일에서 위도·경도를 정하지 못했어요. 위 안내를 확인해 주세요.'
              : '격자를 반영하지 못했어요. 잠시 뒤 다시 시도해 주세요.',
      );
    } finally {
      setAttaching(false);
    }
  }

  /**
   * 화면의 문자열 → 계약(`DatasetCreate`)의 형상. **적은 칸만 실린다.**
   *
   * ⚠ **정본과 어긋나는 자리 하나** — 스펙 19 는 기간을 「`2025-06 ~ 2025-09`」한 칸의
   * 자유 문장으로 그린다. 계약 `DataPeriod` 는 `start`·`end` 두 `date-time` 이라
   * 그 문장을 담을 자리가 없다. **Ted 판정(2026-09-02)이 「두 칸 ＋ 끝 선택」으로
   * 정리했고**(14차 해제), **스펙 문면 갱신은 레포 밖에 남아 있다.**
   */
  function humanMetadata(): Record<string, unknown> {
    const out: Record<string, unknown> = {};
    // ⭑ **⟨WU-B2 · PRD-16⟩ 객체 배열이다.** 이름이 빈 행은 싣지 않고, 한 행도 안 적었으면
    // **열쇠 자체를 안 싣는다** — 빈 배열은 이제 400(「변수는 하나 이상 있어야 해요」)이라
    // 파일만 올린 사람이 그 문면에 막히면 안 된다.
    const vars = variablesPayload(variables);
    if (vars) out.variables = vars;
    if (crs.trim()) out.crs = crs.trim();
    // **끝은 조건부다** (계약 `DataPeriod.end`: `[string, "null"]` · 14차 해제).
    // 끝을 비우면 무기한이라는 뜻으로 `null` 을 **명시해서** 보낸다 — 열쇠를 빼지 않는
    // 이유는 계약이 `ProjectPeriod` 와 같은 required-but-nullable 모양이라서다.
    // 시작이 비면 기간 자체를 싣지 않는다 — 시작 없는 끝은 기간이 아니다.
    // ⭑ **⟨19차 해제 · PRD-18 · R-C WU-C8 §5-14⟩ 조립의 재료는 자리 칸들 하나다.**
    // 달력 팝오버의 `적용` 이 최소 단위와 자리 칸을 **함께** 채운다 — 단위 없이 자리 칸만
    // 찬 상태는 만들어지지 않는다. 안 고르고 지나가면 기간 열쇠 자체가 안 실린다(종전과 같다).
    // ⛔ **실리는 열쇠는 무변이다** — `period.start`·`end`·`granularity` 그대로다.
    const assembled = granularity
      ? { start: assemble(startParts, granularity), end: assemble(endParts, granularity) }
      : { start: null, end: null };
    if (assembled.start) {
      out.period = {
        start: assembled.start,
        // ⭑ **⟨PRD-40 · 판정 ⓐ⟩ 화면에서만 비운다 — 저장은 `period_end = period_start`.**
        // 「한 시점」은 끝이 없는 것이 아니라 **시작과 같은 끝**이다. `null` 로 보내면
        // 그 자료가 「무기한·진행 중」으로 읽혀 한 시점 자료와 구별되지 않는다.
        // ⛔ 스키마·계약·CHECK 는 무변이다 — 조립만 화면이 한다.
        end: assembled.end || assembled.start,
        // `''` 은 「미지정」이고 계약은 그것을 `null` 로 말한다 — 빈 문자열을 보내지 않는다.
        granularity: granularity || null,
      };
    }
    // ⭑ **⟨19차 해제 · PRD-17⟩ 관측 간격 — 두 칸이 **다 차야** 싣는다.**
    // 반쪽이면 아예 안 실어 보내는 것이 아니라 **그대로 보내 서버 400 을 받는다** —
    // 화면이 조용히 버리면 사용자는 적었다고 믿고 떠난다(문구의 정본은 서버 봉투다).
    const rawInterval = intervalValue.trim();
    if (rawInterval || intervalUnit) {
      out.observationInterval = {
        value: rawInterval ? Number(rawInterval) : null,
        unit: intervalUnit || null,
      };
    }
    // ⭑ **⟨WU-B3 · PRD-01·02·03⟩ 세 축은 늘 실린다.** 계약 `required` 가 앞의 둘을
    // 잡았고(20차 ㉯), 기본 선택값이 있어 빈 값으로 나갈 자리가 없다.
    // ⚠ `category`·`dataType` 은 여기서 싣지 않는다 — 계약 `required` 라 `register()`
    //    호출부가 **명시로** 싣는다(타입 검사가 그 자리를 본다).
    if (level) out.processingLevelUserSet = level;
    if (gridDescription.trim()) out.gridDescription = gridDescription.trim();
    // ⭑ **⟨WU-B6 · PRD-19⟩ Lv0 두 칸은 「보이는 동안 적은 것」만 싣는다.**
    //
    // 화면이 숨긴 값을 몰래 보내면 사용자가 지운 적 없는 값이 저장되고, 상세에 그 값이
    // 뜨는 순간 「내가 적은 적 없는 출처」가 된다. 그래서 **표시 조건과 전송 조건을 같은
    // 식으로 둔다**(`RegisterArea` 의 `ctx.processingLevelUserSet === 'Lv0'`).
    // ⚠ 서버는 이 조건을 걸지 않는다 — Lv1 이상에서 값이 와도 저장한다(PRD-19). 여기 조건은
    //   **화면이 숨긴 값을 안 보낸다**는 화면 쪽 규율이고, 서버의 거절 규칙이 아니다.
    // ⛔ 빈 문자열을 `null` 로 실어 보내지 않는다 — 안 적은 것과 비우라는 것은 다르고,
    //    등록은 「안 적었다」뿐이다(수정 경로가 비우는 자리를 따로 가진다).
    if (level === LV0) {
      if (sourceUrl.trim()) out.sourceUrl = sourceUrl.trim();
      if (sourceDownloadedOn.trim()) out.sourceDownloadedOn = sourceDownloadedOn.trim();
    }
    return out;
  }

  async function submit() {
    if (submitLock.current) return;
    if (createdDatasetId) {
      const lifecycle = mutationLifecycle.current;
      submitLock.current = true;
      setSubmitting(true);
      setRegisterError(null);
      try {
        if (representativeFile) {
          if (!upload.putRepresentativeImage) throw new Error('representative image unavailable');
          await upload.putRepresentativeImage(createdDatasetId, representativeFile);
        }
        if (lifecycle !== mutationLifecycle.current) return;
        props.onClose();
        navigate(`/datasets/${createdDatasetId}`);
      } catch {
        if (lifecycle === mutationLifecycle.current) {
          setRegisterError('데이터셋은 만들었지만 대표 그림을 저장하지 못했어요. 고른 그림을 그대로 두고 다시 시도해 주세요.');
        }
      } finally {
        submitLock.current = false;
        if (lifecycle === mutationLifecycle.current) setSubmitting(false);
      }
      return;
    }
    if (!uploadId) {
      // 등록 게이트는 접수 성패와 무관하게 상시 서 있다. 접수가 실패했으면 여기서 **말없이
      // return** 했다 — 사람은 [등록]을 눌렀는데 아무 일도 안 일어났다. 두 번째 침묵을 닫는다.
      setRegisterError(intakeError ?? '올리다가 끊겼어요. 다시 시도해 주세요.');
      return;
    }
    if (!name.trim()) {
      // §9 이름 없이 데이터셋 만들기 — 이름 칸으로 초점을 옮긴다
      setNameError(true);
      // ⭑ ⟨WU-B3⟩ 이름 칸은 ② 메타데이터 입력에 있다 — 적을 칸으로 데려간다.
      setStep(2);
      window.setTimeout(() => document.getElementById('reg-name')?.focus(), 0);
      return;
    }
    setNameError(false);
    if (!summary.trim()) {
      // PRD-15 — 설명이 필수다. 계약 `DatasetCreate.required` 와 같은 판정을 화면이 먼저 한다.
      setSummaryError(true);
      setStep(2);
      window.setTimeout(() => document.getElementById('reg-summary')?.focus(), 0);
      return;
    }
    setSummaryError(false);
    // ⭑ ⟨advisor ② · F3⟩ 분류·유형은 계약 `DatasetCreate.required` 다 — 화면이 먼저 막는다.
    //   막기만 하고 세워 두면 사람은 ③ 에서 ① 의 빈 칸을 못 본다. 이름·설명 경로와 같은
    //   규율로 **적을 칸이 있는 단계로 데려가고 그 칸에 초점을 준다.**
    if (!category || !dataType) {
      setStep(1);
      setRegisterError(MISSING_CATEGORY_MESSAGE);
      window.setTimeout(() => document.getElementById('reg-category')?.focus(), 0);
      return;
    }
    // ⭑ ⟨advisor ② F1 · WU-B6⟩ 형상 오류는 여기서 막는다 — 서버 400 이 화면에 닿지 않고
    //   일반 실패 문구(`catch`)로 덮이던 자리다(재시도로 해소되지 않는 원인을 재시도하라는
    //   안내가 되므로 사용자를 막다른 길로 보낸다). 값이 있고(칸이 비었으면 선택이라 넘어간다)
    //   형상이 틀렸을 때만 막는다 — `humanMetadata()` 와 같은 조건(`level === LV0`)이다.
    if (
      level === LV0 &&
      sourceDownloadedOn.trim() &&
      !isValidSourceDownloadedOnShape(sourceDownloadedOn.trim())
    ) {
      setStep(3);
      setSourceDownloadedOnError(SOURCE_DOWNLOADED_ON_INVALID);
      window.setTimeout(() => document.getElementById('reg-source-downloaded-on')?.focus(), 0);
      return;
    }
    setSourceDownloadedOnError(null);
    setRegisterError(null);
    const lifecycle = mutationLifecycle.current;
    submitLock.current = true;
    setSubmitting(true);
    try {
      const made = await upload.register({
        uploadId,
        name: name.trim(),
        // **미정을 표현할 수 있어야 한다** — 4값 CHECK 는 「값이 있다면 넷 중 하나」다
        topic: topic || null,
        // ⭑ **⟨19차 해제 · PRD-15⟩ `null` 이 아니다** — 계약이 `type: string` 으로 닫았고
        // 위에서 빈 값을 이미 걸렀다.
        summary: summary.trim(),
        sourceLabel: sourceLabel.trim() || null,
        // ⭑ **⟨WU-B3 · 20차 ㉯⟩ 계약 `required` 라 열쇠를 **명시**한다** — `humanMetadata()` 의
        // 펼침은 `Record<string, unknown>` 이라 타입 검사가 이 둘을 못 본다.
        category,
        dataType,
        // ⭑ **⟨advisor ② ㊁ · PRD-11⟩ 공개 범위 — 사람이 골랐을 때만 실린다.**
        // 안 골랐으면 열쇠 자체가 없고, 서버는 `d2_dataset_access` 행을 만들지 않는다
        // (NULL = 연구실 기본값 · 「현행 의미 유지」). 골랐으면 그 값을 그대로 쓴다.
        ...(accessState === null ? {} : { accessState }),
        // 사람이 항목마다 확인한 것만 온다. 일괄 승인 필드가 아니다
        lineageParents,
        // ⭑ **⟨WU-B8 · PRD-27⟩ 선언했을 때만 싣는다** — 열쇠 없음과 `false` 는 같은 뜻이고,
        //   그 상태의 계보 상태는 `기록 없음` 이 아니라 `확인 필요` 다.
        ...(lineageUnknownEffective ? { lineageUnknown: true } : {}),
        projectIds: projects.map((p) => p.projectId),
        // **빈 칸은 싣지 않는다** — 폼 기본값이 지나간 것을 「사람이 적었다」로 저장하면
        // 파이프라인이 나중에 채울 자리가 영영 막힌다 (서버 `_human_metadata` 와 같은 규율).
        ...humanMetadata(),
      });
      if (lifecycle !== mutationLifecycle.current) return;
      // 데이터셋은 이 시점에 이미 생겼다. 뒤의 그림 PUT이 실패해도 같은 ID를 재사용한다.
      committedDatasetIdRef.current = made.datasetId;
      setCreatedDatasetId(made.datasetId);
      // 등록까지 끝난 임시 업로드는 그림 저장 성공 여부와 무관하게 정리한다.
      if (uploadId && account?.labId) forgetPending(account.labId, uploadId);
      if (representativeFile) {
        try {
          if (!upload.putRepresentativeImage) throw new Error('representative image unavailable');
          await upload.putRepresentativeImage(made.datasetId, representativeFile);
          if (lifecycle !== mutationLifecycle.current) return;
        } catch {
          if (lifecycle !== mutationLifecycle.current) return;
          setRegisterError('데이터셋은 만들었지만 대표 그림을 저장하지 못했어요. 고른 그림을 그대로 두고 다시 시도해 주세요.');
          return;
        }
      }
      if (lifecycle !== mutationLifecycle.current) return;
      props.onClose();
      navigate(`/datasets/${made.datasetId}`);
    } catch (e) {
      if (lifecycle !== mutationLifecycle.current) return;
      // ⭑ **⟨R-C · WU-C8 · R-B §5-31 판정⟩ 서버 400 을 일반 문구로 덮지 않는다.**
      //
      // 400 = 서버가 **어느 칸이 왜 막혔는지** 적어 보낸 거절이다(기간 역전·변수 0건 …).
      // 그것을 「잠시 뒤 다시 시도해 주세요」로 덮으면 사람은 고칠 칸을 못 찾고 같은 값으로
      // 다시 누른다(B3 유산). 문면은 **서버 것을 그대로** 올린다 — 화면이 다시 지으면
      // 서버와 두 얼굴이 된다. ⛔ 새 문면을 만들지 않는다.
      // ⚠ 400 **밖**은 종전 그대로다 — 500·끊김은 사람이 고칠 것이 없다.
      setRegisterError(
        e instanceof UploadGone
          ? '이 파일은 더 이상 없어요. 다시 올려 주세요.'
          : e instanceof RegisterRejected
            ? e.message
            : '데이터셋을 만들지 못했어요. 잠시 뒤 다시 시도해 주세요.',
      );
    } finally {
      submitLock.current = false;
      if (lifecycle === mutationLifecycle.current) setSubmitting(false);
    }
  }

  return (
    <div
      className={`modal-back mb-takeover${!registerOpen && !attach ? ' up-empty' : ''}`}
      data-testid="upload-backdrop"
      // ⭑ ⟨WU-A9R · PRD-44⟩ 어두운 배경을 누르면 닫힌다. **닫기 확인을 그대로 탄다** —
      //   `requestClose()` 하나만 부르므로 × 버튼·Esc 와 판정식이 갈릴 자리가 없다.
      //   `event.target === event.currentTarget` 이라 모달 **안쪽** 클릭은 여기 닿지 않는다.
      //   ⭑ ⟨advisor ② · F3⟩ 누른 자리도 배경이어야 한다 — 모달 안에서 눌러 배경에서 뗀
      //   드래그(텍스트 선택)는 click.target 이 배경이 되어 확인 없이 취소되던 자리다.
      onMouseDown={(e) => {
        downOnBackdrop.current = e.target === e.currentTarget;
      }}
      onClick={(e) => {
        if (e.target === e.currentTarget && downOnBackdrop.current) requestClose();
      }}
    >
      <div
        className="modal modal-takeover"
        role="dialog"
        aria-modal="true"
        aria-label={attach ? '기준 격자 추가' : '업로드'}
        data-testid="upload-modal"
        data-mode={attach ? 'grid-attach' : 'register'}
        data-scene={registerOpen ? 'register' : picked.length ? 'analyze' : 'pick'}
      >
        <div className="modal-h">
          <h3>{attach ? '기준 격자 추가' : picked.length === 0 ? '파일 올리기' : '업로드'}</h3>
          {/* 상단 메뉴가 가려져도 **어느 연구실에 올리는지**가 보인다 (§8) */}
          <span className="mh-lab" data-testid="upload-lab">
            <b>{account?.labName ?? ''}</b>에 올려요
          </span>
          <button type="button" className="x" data-testid="upload-close" aria-label="업로드 닫기" onClick={requestClose}>
            ×
          </button>
        </div>

        <div className="modal-b up-body" ref={bodyRef}>
          {/* 올리다 만 전송 — 숨기지 않는다. 이어올리거나 지워야 사라진다 (〈338〉) */}
          {!attach && incomplete.length > 0 && (
            <aside className="up-banner" data-testid="up-incomplete" aria-live="polite">
              {incomplete.map((item) => (
                <div className="ub-row" key={item.uploadId}>
                  <span className="ub-txt">
                    <b>올리다 만 업로드가 있어요</b> — {item.sourceLabel} ·{' '}
                    {item.uploadedFiles}/{item.plannedFiles} 파일
                  </span>
                  <button
                    type="button"
                    className={resumeId === item.uploadId ? 'ub-btn is-armed' : 'ub-btn'}
                    data-testid={`up-resume-${item.uploadId}`}
                    onClick={() => {
                      resumeRef.current = item.uploadId;
                      resumeFromRef.current = 'banner';
                      setResumeId(item.uploadId);
                      setResumeArm((n) => n + 1);
                    }}
                  >
                    이어서 올리기
                  </button>
                  <button
                    type="button"
                    className="ub-btn"
                    data-testid={`up-discard-${item.uploadId}`}
                    onClick={() => {
                      if (account?.labId) forgetPending(account.labId, item.uploadId);
                      void upload.abortTransfer?.(item.uploadId).then(refreshIncomplete);
                      if (resumeId === item.uploadId) {
                        resumeRef.current = null;
                        setResumeId(null);
                      }
                    }}
                  >
                    지우기
                  </button>
                </div>
              ))}
              {resumeId && (
                <p className="ub-hint" data-testid="up-resume-hint">
                  같은 파일을 다시 끌어다 놓으면 남은 조각부터 이어서 올라가요.
                </p>
              )}
            </aside>
          )}
          {/* 뷰어 — 등록과 무관하게 여기까지 된다 */}
          {!registerOpen && <FileDropCard picked={picked} onPick={pick} onKind={setKind} onRemove={removeFile} />}


          {/* 접수 실패 — **방금 놓은 파일**에 대한 것이라 드롭 카드 바로 아래다.
              위쪽 이어올리기 배너와 섞지 않는다: 그쪽은 「재개 가능」, 이쪽은 「다시 시작」이라
              사람이 할 일이 다르다. 클래스는 `RegisterArea` 의 오류와 같은 `.warn`. */}
          {/* 전송 진행률 (`§D.7` ① — 실재·크기 비례). **문구를 붙이지 않는다** — `§E.2` 에
              본체 전송 상태 행이 없고, 없는 문구를 지어내지 않는다(`S3.md §4`).
              격자만 올릴 때는 격자 블록이 제 문구와 함께 그린다 — 여기서 두 번 그리지 않는다. */}
          {transfer && !gridOnly && transfer.totalBytes > 0 && (
            <progress
              className="gridbar"
              data-testid="up-transfer-progress"
              max={100}
              value={Math.min(100, Math.round((transfer.sentBytes / transfer.totalBytes) * 100))}
            />
          )}

          {/* ① 파일 분석 3단계 — 바이트 진행 바가 못 말하는 구간을 말한다 (rev1 `pbStatus`).
              단계는 **화면이 실제로 아는 사실**에서만 온다: 접수 전 / 접수됨·미준비 / 준비됨. */}
          {picked.length > 0 && !status?.failure && !intakeError && !statusIssue && (
            <div
              className="up-analyze"
              data-testid="up-analyze"
              data-stage={String(analyzeStage)}
              role="status"
              aria-live="polite"
            >
              <span
                className={analyzeStage === 3 ? 'chip chip--success' : 'chip chip--neutral'}
                data-testid="up-analyze-chip"
              >
                {analyzeStage === 3 ? ANALYZED_CHIP : ANALYZING_CHIP}
              </span>
              <span className="an-txt">{ANALYZE_STAGES[analyzeStage - 1]}</span>
            </div>
          )}

          {/* ⭑ ⟨WU-B2 · PRD-16⟩ 마지막 변수 행 삭제 차단 고지 — 같은 토스트 컴포넌트다. */}
          {variableNotice && (
            <Toast
              message={variableNotice}
              testId="up-variable-toast"
              onDismiss={() => setVariableNotice(null)}
            />
          )}

          {/* ③ 파일 빼기 고지 — 공통 토스트를 탄다(PRD-43). 스스로 사라진다. */}
          {statusIssue && (
            <div className="warn" role={statusIssue.retrying ? 'status' : 'alert'} data-testid="up-status-error">
              {statusIssue.message}
              {!statusIssue.retrying && !statusIssue.gone && (
                <button type="button" className="btn btn-secondary" data-testid="up-status-retry"
                  onClick={() => setStatusRetry((n) => n + 1)}>
                  다시 시도
                </button>
              )}
            </div>
          )}
          {removedNotice && (
            <Toast
              message={FILE_REMOVED_NOTICE}
              testId="up-removed-toast"
              onDismiss={() => setRemovedNotice(false)}
            />
          )}

          {mixedGlobal && <Toast message={MIXED_EXTENSION_NOTICE} testId="up-mixed-global" onDismiss={() => setMixedGlobal(false)} />}
          {status?.failure && (
            <div className="warn" role="alert" data-testid="up-analysis-failure">
              <p>파일 분석을 마치지 못했어요 · {status.failure.reason}</p>
              <p>파일과 기준 격자를 확인한 뒤 다시 시도해 주세요.</p>
              <button type="button" className="btn btn-secondary" onClick={() => setRetryArm((n) => n + 1)}>다시 올려 분석</button>
            </div>
          )}

          {intakeError && (
            <p className="warn" role="alert" data-testid="up-intake-error">
              {intakeError}
              <button
                type="button"
                className="btn btn-secondary"
                data-testid="up-intake-retry"
                onClick={() => setRetryArm((n) => n + 1)}
              >
                다시 시도
              </button>
            </p>
          )}

          {/* ⭑ **⟨19차 · PRD-28⟩ 좌우 두 칸 — 미리보기 2 : 입력 3.**
              rev1 축자 = 「좌우를 반씩 쓰던 것을 미리보기 2 : 입력 3 으로」. 비율은 CSS
              (`.up-split`)가 갖는다 — 화면 코드가 폭을 계산하지 않는다. 좁은 폭에서는
              한 칸으로 접히고, 그때 순서는 미리보기 → 입력 그대로다. */}
          {picked.length > 0 && (
            <div className="up-split" data-testid="up-split">
              <div className="up-split-preview" data-testid="up-split-preview">
              <PreviewPanel
                key={signature}
                source={props.sources.preview}
                autoPreview={registerOpen && Boolean(status?.renderable)}
                renderable={status?.ready ? status.renderable ?? undefined : undefined}
                uploadId={uploadId}
                hasReferenceGrid={hasReferenceGrid}
                onRender={setRendered}
                representativeFile={representativeFile}
                representativeOnly={Boolean(createdDatasetId)}
                representativeDisabled={submitting}
                onRepresentativeFileChange={(file) => {
                  setRepresentativeFile(file);
                  if (createdDatasetId) setRegisterError(null);
                }}
                {...(!createdDatasetId ? { grid: {
                  hasGrid: hasReferenceGrid,
                  skipped: gridSkipped,
                  verifying: gridVerifying,
                  ...(gridRejection ? { gridRejection } : {}),
                  onPickGrid: pickGrid,
                  // **건너뛰기가 기본 경로다** — 잃는 것은 「지도 위 위치」 하나뿐이다 (`§E.1`)
                  onSkipGrid: () => setGridSkipped(true),
                  ...(gridOnly && transfer ? { transfer } : {}),
                } } : {})}
              />
              {registerOpen && !createdDatasetId ? <details className="up-file-management">
                <summary>올린 파일 {picked.length}개 · 추가·변경</summary>
                <FileDropCard picked={picked} onPick={pick} onKind={setKind} onRemove={removeFile} />
              </details> : null}
              </div>

              {/* 오른쪽 칸 — 사람이 적는 자리. 등록 게이트도 여기 선다(요약 레일이 아니다). */}
              <div className="up-split-form" data-testid="up-split-form">
              {/* 후주입 확정 — 등록 게이트와 **같은 자리**다. 화면 개념을 늘리지 않는다.
                  판별이 끝나기 전에는 누를 수 없다 — 축이 정해져야 반영할 것이 있다. */}
              {attach ? (
                <div className="reggate" data-testid="grid-attach-gate">
                  <div>
                    <div className="rg-t">
                      이 기준 격자를 {attach.datasetName ?? '이 데이터셋'}에 반영할까요?
                    </div>
                    <div className="rg-s">
                      반영하면 지도형 미리보기가 생겨요. 데이터는 새로 만들어지지 않아요.
                    </div>
                  </div>
                  <div className="rg-a">
                    <button
                      type="button"
                      className="btn btn-secondary"
                      data-testid="grid-attach-cancel"
                      onClick={requestClose}
                    >
                      그만두기
                    </button>
                    <button
                      type="button"
                      className="btn btn-strong"
                      data-testid="grid-attach-confirm"
                      disabled={!uploadId || !status?.ready || attaching}
                      onClick={() => void confirmAttach()}
                    >
                      이 데이터셋에 반영
                    </button>
                  </div>
                </div>
              ) : null}

              {attach && registerError ? (
                <p className="err" data-testid="grid-attach-error" role="alert">
                  {registerError}
                </p>
              ) : null}

              {/* 등록 결정 게이트 — 미리보기 아래 **상시**. 등록이 의무가 아님이 화면에서 읽힌다 */}
              {!attach && !registerOpen ? (
              <div className="reggate" data-testid="reg-gate">
                <div>
                  <div className="rg-t">이 파일을 연구실에 등록할까요?</div>
                  <div className="rg-s">등록하면 계보가 쌓이고 검색·공유가 돼요.</div>
                </div>
                <div className="rg-a">
                  <button
                    type="button"
                    className="btn btn-secondary"
                    data-testid="reg-viewonly"
                    // **등록하지 않겠다는 선택**이다 — 여기서 `submit()` 을 부르면 등록을
                    // 거절한 사람에게 데이터셋이 생긴다. `submit()` 이 `onClose()` 도 부르는 탓에
                    // 모달이 정상으로 닫혀 눈에 안 띄었다 (`S1-PLAN §5.2` — `S1-fe` 가 닫는다).
                    // 모달을 닫고 **S-08 로 보낸다** — 정본 §7.2 전이표의 도착지다.
                    onClick={viewOnly}
                  >
                    보기만 할게요
                  </button>
                  <button
                    type="button"
                    className="btn btn-strong"
                    data-testid="reg-open"
                    disabled={!uploadId || !status?.ready || Boolean(status?.failure) || Boolean(statusIssue) || Boolean(intakeError)}
                    onClick={() => {
                      setRegisterOpen(true);
                      setStep(1);
                    }}
                  >
                    다음 →
                  </button>
                </div>
              </div>
              ) : null}

            {/* 등록 카드는 앞의 파일 놓기·미리보기 **아래로 그대로 이어 붙는다.**
                옆에 요약 레일을 세우지 않는다 (§8 등록 단계 배치).
                  ⭑ ⟨PRD-28⟩ 그 「아래」가 **오른쪽 칸 안의 아래**가 됐다 — 순서는 그대로다. */}
            {!attach && registerOpen && !createdDatasetId && (
              <RegisterArea
                step={step}
                onStep={setStep}
                fileName={bodyName}
                fileCount={picked.length}
                onRemoveFiles={() => removeFile(null)}
                lineage={lineage}
                status={status}
                projectSource={props.sources.projects}
                name={name}
                onName={setName}
                topic={topic}
                onTopic={setTopic}
                summary={summary}
                onSummary={setSummary}
                variables={variables}
                onVariables={setVariables}
                onVariablesBlocked={setVariableNotice}
                crs={crs}
                onCrs={setCrs}
                gridDescription={gridDescription}
                onGridDescription={setGridDescription}
                granularity={granularity}
                onGranularity={setGranularity}
                startParts={startParts}
                onStartParts={setStartParts}
                endParts={endParts}
                onEndParts={setEndParts}
                intervalValue={intervalValue}
                onIntervalValue={setIntervalValue}
                intervalUnit={intervalUnit}
                onIntervalUnit={setIntervalUnit}
                sourceLabel={sourceLabel}
                onSourceLabel={setSourceLabel}
                sourceUrl={sourceUrl}
                onSourceUrl={setSourceUrl}
                sourceDownloadedOn={sourceDownloadedOn}
                onSourceDownloadedOn={(v) => {
                  setSourceDownloadedOn(v);
                  setSourceDownloadedOnError(null);
                }}
                sourceDownloadedOnError={sourceDownloadedOnError}
                projects={projects}
                onProjects={setProjects}
                category={category}
                onCategory={setCategory}
                dataType={dataType}
                onDataType={setDataType}
                level={level}
                onLevel={setLevel}
                accessState={accessState}
                onAccessState={setAccessState}
                nameError={nameError}
                summaryError={summaryError}
                registerError={registerError}
                lineageStep={lineageStep}
                lineageCtx={lineageCtx}
                lineageConflicts={lineageConflicts}
                onCancel={requestClose}
                submitting={submitting}
                submitLabel={createdDatasetId
                  ? representativeFile ? '대표 그림 다시 저장' : '자동 그림으로 완료'
                  : undefined}
                onSubmit={() => void submit()}
              />
            )}
            {!attach && registerOpen && createdDatasetId ? (
              <div className="card is-on" data-testid="up-created-recovery">
                <div className="card-h">
                  <h3>데이터셋은 생성됨</h3>
                  <span className="sub">대표 그림 저장만 마무리해 주세요.</span>
                </div>
                <div className="card-b">
                  {registerError ? <p className="warn" role="alert">{registerError}</p> : null}
                  <p className="muted">등록 정보와 원본 파일은 이미 저장되어 더는 바꿀 수 없어요.</p>
                  <div className="reg-actions">
                    <span className="sp" />
                    <button
                      type="button"
                      className="btn btn-primary"
                      disabled={submitting}
                      onClick={() => void submit()}
                    >
                      {submitting
                        ? '저장 중…'
                        : representativeFile ? '대표 그림 다시 저장' : '자동 그림으로 완료'}
                    </button>
                  </div>
                </div>
              </div>
            ) : null}
              </div>
            </div>
          )}

        </div>
      </div>

      {/* 닫기 확인 — 사람이 한 확인이 소리 없이 사라지지 않는다 (§8) */}
      {confirmClose && (
        <div className="modal-back confirm-back">
          <div className="modal" data-testid="upload-close-confirm">
            <div className="modal-h">
              <h3>{UPLOAD_CLOSE_TITLE}</h3>
            </div>
            <div className="modal-b">
              {/* ⭑ ⟨WU-A9R · PRD-34⟩ 본문이 상황별 3종이다. 문면·갈래는 `toastCopy.ts` 가
                  쥐고 있고 여기서는 지금 상태만 넘긴다 — 화면이 문장을 짓지 않는다. */}
              <p>
                {uploadCloseMessage({
                  hasHumanInput,
                  lineageCount: lineageParents.length,
                })}
              </p>
            </div>
            <div className="modal-f">
              <button
                type="button"
                className="btn btn-secondary"
                onClick={() => setConfirmClose(false)}
              >
                {UPLOAD_CLOSE_KEEP}
              </button>
              <button type="button" className="btn btn-strong" onClick={props.onClose}>
                {UPLOAD_CLOSE_LEAVE}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
