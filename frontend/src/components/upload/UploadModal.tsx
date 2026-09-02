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
import { FileDropCard } from './FileDropCard';
import { PreviewPanel } from './PreviewPanel';
import { RegisterArea, type Step } from './RegisterArea';
import { previewNavigation } from '../preview/handoff';
import { forgetPending, rememberPending } from './pendingStore';
import {
  GridAxisTaken,
  NoResolvedGrid,
  TransferInterrupted,
  UploadGone,
  type FileKind,
  type LineageStepContext,
  type LineageStepRender,
  type IncompleteTransferItem,
  type PickedFile,
  type UploadLineageParent,
  type UploadSources,
  type UploadStatus,
} from './types';

/** 업로드 상태 확인 간격. 이벤트 ②~⑦ 의 결과가 오기를 기다린다. */
const STATUS_POLL_MS = 1000;

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
  const [registerOpen, setRegisterOpen] = useState(false);
  const [step, setStep] = useState<Step>(1);
  const [confirmClose, setConfirmClose] = useState(false);

  const [name, setName] = useState('');
  const [topic, setTopic] = useState('');
  const [summary, setSummary] = useState('');
  const [sourceLabel, setSourceLabel] = useState('');
  const [projects, setProjects] = useState<{ projectId: string; name: string }[]>([]);
  const [lineage, setLineage] = useState<{ confirmed: number; total: number } | null>(null);
  const [lineageParents, setLineageParents] = useState<UploadLineageParent[]>([]);
  const [gridSkipped, setGridSkipped] = useState(false);
  const [nameError, setNameError] = useState(false);
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
  // S-08 로 넘길 짐 중 **이 모달만 아는 것** — 어느 렌더를 이어 보게 할지와, 짝 파일 없이 그렸는지.
  const [rendered, setRendered] = useState<{
    renderId: string;
    withoutReferenceGrid: boolean;
  } | null>(null);
  // 미완결 프리사인드 전송 (〈174〉) — 저장 모드 s3 에서만 값이 온다 (local 은 빈 배열)
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
  const [resumeArm, setResumeArm] = useState(0);
  const statusTimer = useRef(0);

  const attach = props.attach;
  /** 후주입 모드의 기본 파일 종류. 사람이 격자를 붙이러 왔으므로 격자가 기본이다. */
  const defaultKind: FileKind = attach ? '기준 격자 파일' : '본체';

  // 미완결 전송 목록 (〈174〉) — 후주입 모드에서는 묻지 않는다 (격자를 붙이러 온 자리다).
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
        setName((cur) => cur || (firstBody ? nameFromFile(firstBody.fileName) : ''));
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
    if (!uploadId) return;
    let alive = true;
    const tick = async () => {
      try {
        const s = await upload.status(uploadId);
        if (!alive) return;
        setStatus(s);
        if (!s.ready && !s.failure) statusTimer.current = window.setTimeout(tick, STATUS_POLL_MS);
      } catch (e) {
        if (!alive) return;
        if (e instanceof UploadGone) setRegisterError('이 파일은 더 이상 없어요. 다시 올려 주세요.');
      }
    };
    void tick();
    return () => {
      alive = false;
      window.clearTimeout(statusTimer.current);
    };
  }, [uploadId, upload]);

  const hasReferenceGrid = picked.some((p) => p.kind === '기준 격자 파일');
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

  const onLineageProgress = useCallback(
    (p: { confirmed: number; total: number }) => setLineage(p),
    [],
  );
  const onLineageParentsChange = useCallback(
    (parents: UploadLineageParent[]) => setLineageParents(parents),
    [],
  );
  // ③ 의 슬롯은 그대로 두되, **아무도 얹지 않으면 빈 자리로 남기지 않는다** — 계보 확정은
  // 업로드의 일부이지 선택 부품이 아니다. 바깥에서 넘긴 것이 있으면 그것이 이긴다.
  const lineageStep: LineageStepRender =
    props.lineageStep ?? ((c) => <LineageStep source={props.sources.lineage} ctx={c} />);

  const lineageCtx: LineageStepContext = useMemo(
    () => ({
      uploadId: uploadId ?? '',
      datasetNameDraft: name,
      topic: topic || null,
      onLineageProgress,
      onLineageParentsChange,
    }),
    [uploadId, name, topic, onLineageProgress, onLineageParentsChange],
  );

  /**
   * 격자 파일을 **그 업로드에 직접** 붙인다 (`§E.5` — 재사용·추천 없음).
   * ⚠ **역할은 요청이 선언한다** — `kind` 를 실어 접수하고, 원장 행은 워커가 축을 확정한
   * 뒤에 선다(`〈79〉-㈎`). 화면은 축을 묻지도, 정하지도 않는다.
   */
  function pickGrid(files: File[]) {
    if (files.length === 0) return;
    setGridSkipped(false);
    setPicked((cur) => [
      ...cur,
      ...files.map((file) => ({ file, kind: '기준 격자 파일' as FileKind })),
    ]);
  }

  function pick(files: File[], paths?: ReadonlyMap<File, string>) {
    // 파일 종류 기본값은 `본체` 다. 격자는 사람이 골라 바꾼다 (`P2.md §2-20`).
    // **후주입 모드에서는 기본값이 `기준 격자 파일` 이다** — 사람이 격자를 붙이러 왔다.
    // 폴더째 드롭이면 상대 경로가 함께 온다 (`dropTree.ts` · `〈173〉`).
    setPicked((cur) => [
      ...cur,
      ...files.map((file) => {
        const relativePath = paths?.get(file);
        return { file, kind: defaultKind, ...(relativePath ? { relativePath } : {}) };
      }),
    ]);
  }

  function setKind(index: number, kind: FileKind) {
    setPicked((cur) => cur.map((p, i) => (i === index ? { ...p, kind } : p)));
  }

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
    // 등록 단계를 연 채 닫으면 사람이 한 확인이 사라진다 — 그때만 묻는다 (§8 모달 닫기)
    if (registerOpen) setConfirmClose(true);
    else props.onClose();
  }

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

  async function submit() {
    if (!uploadId) {
      // 등록 게이트는 접수 성패와 무관하게 상시 서 있다. 접수가 실패했으면 여기서 **말없이
      // return** 했다 — 사람은 [등록]을 눌렀는데 아무 일도 안 일어났다. 두 번째 침묵을 닫는다.
      setRegisterError(intakeError ?? '올리다가 끊겼어요. 다시 시도해 주세요.');
      return;
    }
    if (!name.trim()) {
      // §9 이름 없이 데이터셋 만들기 — 이름 칸으로 초점을 옮긴다
      setNameError(true);
      setStep(1);
      window.setTimeout(() => document.getElementById('reg-name')?.focus(), 0);
      return;
    }
    setNameError(false);
    setRegisterError(null);
    try {
      const made = await upload.register({
        uploadId,
        name: name.trim(),
        // **미정을 표현할 수 있어야 한다** — 4값 CHECK 는 「값이 있다면 넷 중 하나」다
        topic: topic || null,
        summary: summary.trim() || null,
        sourceLabel: sourceLabel.trim() || null,
        // 사람이 항목마다 확인한 것만 온다. 일괄 승인 필드가 아니다
        lineageParents,
        projectIds: projects.map((p) => p.projectId),
      });
      props.onClose();
      // 등록까지 끝났다 — 「설정이 안 끝난 업로드」에서 지운다.
      if (uploadId && account?.labId) forgetPending(account.labId, uploadId);
      navigate(`/datasets/${made.datasetId}`);
    } catch (e) {
      setRegisterError(
        e instanceof UploadGone
          ? '이 파일은 더 이상 없어요. 다시 올려 주세요.'
          : '데이터셋을 만들지 못했어요. 잠시 뒤 다시 시도해 주세요.',
      );
    }
  }

  return (
    <div className="modal-back mb-takeover">
      <div
        className="modal modal-takeover"
        role="dialog"
        aria-modal="true"
        aria-label={attach ? '기준 격자 추가' : '업로드'}
        data-testid="upload-modal"
        data-mode={attach ? 'grid-attach' : 'register'}
      >
        <div className="modal-h">
          <h3>{attach ? '기준 격자 추가' : '업로드'}</h3>
          {/* 상단 메뉴가 가려져도 **어느 연구실에 올리는지**가 보인다 (§8) */}
          <span className="mh-lab" data-testid="upload-lab">
            <b>{account?.labName ?? ''}</b>에 올려요
          </span>
          <button type="button" className="x" data-testid="upload-close" onClick={requestClose}>
            ×
          </button>
        </div>

        <div className="modal-b up-body">
          {/* 올리다 만 전송 — 숨기지 않는다. 이어올리거나 지워야 사라진다 (〈174〉) */}
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
          <FileDropCard picked={picked} onPick={pick} onKind={setKind} />

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

          {picked.length > 0 && (
            <>
              <PreviewPanel
                source={props.sources.preview}
                uploadId={uploadId}
                hasReferenceGrid={hasReferenceGrid}
                onRender={setRendered}
                grid={{
                  hasGrid: hasReferenceGrid,
                  skipped: gridSkipped,
                  verifying: gridVerifying,
                  ...(gridRejection ? { gridRejection } : {}),
                  onPickGrid: pickGrid,
                  // **건너뛰기가 기본 경로다** — 잃는 것은 「지도 위 위치」 하나뿐이다 (`§E.1`)
                  onSkipGrid: () => setGridSkipped(true),
                  ...(gridOnly && transfer ? { transfer } : {}),
                }}
              />

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
              {!attach ? (
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
                    onClick={() => {
                      setRegisterOpen(true);
                      setStep(1);
                    }}
                  >
                    연구실에 등록 →
                  </button>
                </div>
              </div>
              ) : null}
            </>
          )}

          {/* 등록 카드는 앞의 파일 놓기·미리보기 **아래로 그대로 이어 붙는다.**
              옆에 요약 레일을 세우지 않는다 (§8 등록 단계 배치) */}
          {!attach && registerOpen && (
            <RegisterArea
              step={step}
              onStep={setStep}
              fileName={bodyName}
              lineage={lineage}
              status={status}
              projectSource={props.sources.projects}
              name={name}
              onName={setName}
              topic={topic}
              onTopic={setTopic}
              summary={summary}
              onSummary={setSummary}
              sourceLabel={sourceLabel}
              onSourceLabel={setSourceLabel}
              projects={projects}
              onProjects={setProjects}
              nameError={nameError}
              registerError={registerError}
              lineageStep={lineageStep}
              lineageCtx={lineageCtx}
              onCancel={() => setRegisterOpen(false)}
              onSubmit={() => void submit()}
            />
          )}
        </div>
      </div>

      {/* 닫기 확인 — 사람이 한 확인이 소리 없이 사라지지 않는다 (§8) */}
      {confirmClose && (
        <div className="modal-back confirm-back">
          <div className="modal" data-testid="upload-close-confirm">
            <div className="modal-h">
              <h3>업로드를 닫을까요?</h3>
            </div>
            <div className="modal-b">
              <p>확인한 계보와 입력한 내용이 사라져요. 데이터셋은 만들어지지 않아요.</p>
            </div>
            <div className="modal-f">
              <button
                type="button"
                className="btn btn-secondary"
                onClick={() => setConfirmClose(false)}
              >
                계속 작성
              </button>
              <button type="button" className="btn btn-strong" onClick={props.onClose}>
                닫고 나가기
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
