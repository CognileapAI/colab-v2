// S-04 업로드 모달이 바깥 세계와 만나는 **얼굴 셋**.
// 화면은 어느 쪽이 실서버인지 모른다 (집 관례 — `components/detail/types.ts`·`detailSource.ts`).
//
// 타입은 전부 생성물에서 온다 — 여기서 계약 스키마를 다시 선언하지 않는다
// (`CLAUDE.md §3-6·§3-7` · `frontend/src/generated/README.md`).
import type { Schemas } from '../../api/client';
import type { LineageSource } from '../lineage/types';

export type FileKind = Schemas['FileKind'];
export type UploadReceipt = Schemas['UploadReceipt'];
export type UploadStatus = Schemas['UploadStatus'];
export type UploadFileRef = Schemas['UploadFileRef'];
export type DatasetCreate = Schemas['DatasetCreate'];
export type UploadLineageParent = Schemas['UploadLineageParent'];
export type ProjectRow = Schemas['ProjectRow'];
export type ProjectCreate = Schemas['ProjectCreate'];

/** 만료됐거나 없는 업로드 (`Policy §7.1`·§9 「이 파일은 더 이상 없어요」 · 계약 404). */
export class UploadGone extends Error {}

/** 아직 구현되지 않은 op (`PLAN-SoT §9-㊹` 501 표). */
export class NotImplemented extends Error {}

/**
 * 전송이 **원장을 세운 뒤** 끊겼다 — 그 전송은 아직 살아 있고 **재개할 수 있다**.
 *
 * 이 오류가 없으면 화면은 「어느 전송이 실패했는지」를 몰라 재시도를 **새 전송**으로
 * 보낼 수밖에 없고, 그러면 원장이 시도마다 하나씩 는다(사용자가 본 「실패 세트 2개」).
 * `uploadId` 를 들고 나오는 것이 재개의 유일한 실마리다.
 */
export class TransferInterrupted extends Error {
  constructor(message: string, readonly uploadId: string) {
    super(message);
    this.name = 'TransferInterrupted';
  }
}

/** 놓은 파일 한 건 + 사람이 고른 종류. **축은 여기 없다** — 서버가 파일에서 판별한다(`〈63〉-㉰`). */
export interface PickedFile {
  file: File;
  kind: FileKind;
  /** 폴더째 드롭에서 왔을 때의 `폴더/이름` 상대 경로 (`dropTree.ts` · `〈337〉`). 낱개 파일은 없음. */
  relativePath?: string;
}

/** 후주입 확정이 돌려주는 `DatasetFile` 들. 축은 **판별의 결과**다. */
export type DatasetFile = Schemas['DatasetFile'];

/** 이미 그 축을 쓰는 격자가 있다 (`〈58〉` 상한 · 계약 409). */
export class GridAxisTaken extends Error {}

/** 확정할 격자가 없다 — 판별에 실패했거나 형상이 어긋났다 (계약 400 · `〈66〉`). */
export class NoResolvedGrid extends Error {}

/** `create` 의 선택 인자 — 프리사인드 전송(〈338〉)에서만 의미를 갖는다. */
export interface UploadCreateOptions {
  /** 배너·목록에 보일 묶음 이름. */
  sourceLabel?: string;
  /** 미완결 전송을 이어올릴 때 — 같은 파일을 다시 고른 뒤 이 id 로 재개한다. */
  resumeUploadId?: string;
  onProgress?: (p: { sentBytes: number; totalBytes: number }) => void;
}

/** 미완결 전송 한 건 (`listIncompleteUploadTransfers` · 〈338〉). */
export interface IncompleteTransferItem {
  uploadId: string;
  sourceLabel: string;
  uploadedFiles: number;
  plannedFiles: number;
  uploadedBytes: number;
  plannedBytes: number;
  createdAt: string;
  expiresAt: string;
}

export interface UploadSource {
  /** `createUpload` — 접수. 이 응답이 `uploadId`·`fileId` 를 FE 표면에 처음 내린다.
   *  프리사인드 전송이 서면(저장 모드 s3) 그 경로로, 아니면(501) form-data 로 폴백한다. */
  create(files: PickedFile[], opts?: UploadCreateOptions): Promise<UploadReceipt>;
  /** 내 미완결 전송 — 이어올리기 배너. 프리사인드가 안 서는 환경(501)에서는 빈 배열. */
  incomplete?(): Promise<IncompleteTransferItem[]>;
  /** 미완결 전송을 지운다 (S3 조각까지). */
  abortTransfer?(uploadId: string): Promise<void>;
  /** `getUploadStatus` — 이벤트 ②~⑦ 의 결과만 읽는다. 만료면 `UploadGone`. */
  status(uploadId: string): Promise<UploadStatus>;
  /** `createDataset` — **등록 전환**. 이것을 부르기 전에는 D3 에 행이 없다 (`〈64〉`). */
  register(body: DatasetCreate): Promise<{ datasetId: string }>;
  /**
   * `attachUploadGridFiles` — **격자 후주입 확정.**
   * 짝(데이터셋 ↔ 업로드)은 어디에도 저장되지 않는다 — **화면이 들고 있다가 여기서 동봉한다.**
   */
  attachGrid(datasetId: string, uploadId: string): Promise<DatasetFile[]>;
}

/**
 * 팔레트 한 값. **⟨동결 4회 해제 · `PLAN-SoT §9-〈88〉` 묶음 4⟩ 생성 타입으로 갈아 끼웠다.**
 *
 * 이전 판은 「`fe-core` 계약에 `listPalettes` 중계가 없어 생성 타입이 존재하지 않는다」며
 * 화면이 필요로 하는 최소 모양을 손으로 적고 「중계가 열리면 갈아 끼운다」고 남겨 뒀다.
 * **그 중계가 없어서 실서버 렌더가 한 번도 시작되지 않았다**(스윕 `D-1`). 이제 열렸고,
 * 여기서 계약 스키마를 다시 선언하지 않는다 (`CLAUDE.md §3-6·§3-7`).
 */
export type PaletteOption = Schemas['PaletteOption'];

/**
 * 렌더 작업·요청 — **중계라 계약이 `core-viz.yaml` 정의를 `$ref` 로 그대로 쓴다.**
 * 생성물에 그대로 있으므로 여기서 다시 선언하지 않는다.
 *
 * 소비 규칙 셋(`sessions/P2-viz-report.md §13`) — ⑴ 실패는 4xx 가 아니라 **200 + `failure`**
 * ⑵ `stage` 는 `그리는 중` 일 때만 있다 ⑶ `partialFailure` 는 `status` 를 `실패` 로 만들지 않는다.
 */
export type RenderJob = Schemas['RenderJob'];
export type RenderRequest = Schemas['RenderRequest'];
/** 완료된 렌더 결과. **`oneOf` 다** — 단일 이미지(stage 1)와 타일(stage 2) 갈래가 갈린다(`〈85〉`). */
export type RenderResult = Schemas['RenderResult'];

export interface PreviewSource {
  /** 팔레트 값의 **유일한 출처**. 화면이 목록을 지어내지 않는다. */
  palettes(): Promise<PaletteOption[]>;
  createRender(req: RenderRequest): Promise<RenderJob>;
  getRender(renderId: string): Promise<RenderJob>;
}

export interface ProjectSource {
  list(): Promise<ProjectRow[]>;
  create(body: ProjectCreate): Promise<{ projectId: string; name: string }>;
}

export interface UploadSources {
  upload: UploadSource;
  preview: PreviewSource;
  projects: ProjectSource;
  /** ③ 계보 확정의 읽기 출처 (`components/lineage/`). **쓰기 op 이 없는 것이 설계다.** */
  lineage: LineageSource;
}

/**
 * ③ 계보 확정이 얹히는 자리.
 * **골격은 자리와 표시기까지만 만든다** — 카드·확신도·부모 역할은 `components/lineage/` 소유다.
 * 아무도 얹지 않으면 모달이 집 안의 `LineageStep` 을 세운다 (`S1-fe`, W3).
 */
export interface LineageStepContext {
  uploadId: string;
  /** ① 에서 사람이 적는 중인 이름 — 제안 조회의 단서로만 쓴다 (`listUploadLineageSuggestions`). */
  datasetNameDraft: string;
  /** 고른 주제. 아직 안 골랐으면 `null` (`P2.md §2-17` — 미정이 정상 상태다). */
  topic: string | null;
  /** 표시기의 확정 건수(`③ 계보 확정 0 / 3`)를 갱신한다. 0건이면 부르지 않는다. */
  onLineageProgress(p: { confirmed: number; total: number }): void;
  /** 등록 요청에 실릴 **확인된** 계보 관계. 사람이 확인한 것만 온다. */
  onLineageParentsChange(parents: UploadLineageParent[]): void;
}

export type LineageStepRender = (ctx: LineageStepContext) => React.ReactNode;

/** 주제 고정 4값 (`Policy §5` · `〈55〉` DB CHECK). **빈 값 = 미정**이고 그것이 정상 상태다. */
export const TOPICS = ['강우·강수', '식생·NDVI', '지형·DEM', '토지피복·LULC'] as const;
