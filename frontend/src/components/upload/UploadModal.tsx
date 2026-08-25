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
import {
  GridAxisTaken,
  NoResolvedGrid,
  UploadGone,
  type FileKind,
  type LineageStepContext,
  type LineageStepRender,
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
  const [attaching, setAttaching] = useState(false);
  const statusTimer = useRef(0);

  const attach = props.attach;
  /** 후주입 모드의 기본 파일 종류. 사람이 격자를 붙이러 왔으므로 격자가 기본이다. */
  const defaultKind: FileKind = attach ? '기준 격자 파일' : '본체';

  // 놓은 파일(이름·종류)이 바뀌면 접수를 다시 한다. 파일 종류는 접수 시점에 정해져 있어야 한다
  // (이벤트 `FileRef.kind` 가 required 다). **축은 보내지 않는다** — 서버가 파일에서 판별한다.
  const signature = picked.map((p) => `${p.file.name}:${p.file.size}:${p.kind}`).join('|');
  useEffect(() => {
    if (picked.length === 0) {
      setUploadId(null);
      setStatus(null);
      return;
    }
    let alive = true;
    void upload
      .create(picked)
      .then((receipt) => {
        if (!alive) return;
        setUploadId(receipt.uploadId);
        const firstBody = receipt.files.find((f) => f.kind === '본체') ?? receipt.files[0];
        setName((cur) => cur || (firstBody ? nameFromFile(firstBody.fileName) : ''));
      })
      .catch(() => {
        // §9 업로드 중단 — 「올리다가 끊겼어요. 다시 시도해 주세요.」 파일 놓기부터 다시 한다.
        if (alive) setUploadId(null);
      });
    return () => {
      alive = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [signature, upload]);

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

  function pick(files: File[]) {
    // 파일 종류 기본값은 `본체` 다. 격자는 사람이 골라 바꾼다 (`P2.md §2-20`).
    // **후주입 모드에서는 기본값이 `기준 격자 파일` 이다** — 사람이 격자를 붙이러 왔다.
    setPicked((cur) => [...cur, ...files.map((file) => ({ file, kind: defaultKind }))]);
  }

  function setKind(index: number, kind: FileKind) {
    setPicked((cur) => cur.map((p, i) => (i === index ? { ...p, kind } : p)));
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
    if (!uploadId) return;
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
          {/* 뷰어 — 등록과 무관하게 여기까지 된다 */}
          <FileDropCard picked={picked} onPick={pick} onKind={setKind} />

          {picked.length > 0 && (
            <>
              <PreviewPanel
                source={props.sources.preview}
                uploadId={uploadId}
                hasReferenceGrid={hasReferenceGrid}
                grid={{
                  hasGrid: hasReferenceGrid,
                  skipped: gridSkipped,
                  verifying: gridVerifying,
                  ...(gridRejection ? { gridRejection } : {}),
                  onPickGrid: pickGrid,
                  // **건너뛰기가 기본 경로다** — 잃는 것은 「지도 위 위치」 하나뿐이다 (`§E.1`)
                  onSkipGrid: () => setGridSkipped(true),
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
                    onClick={requestClose}
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
