// S-05 데이터셋 상세의 화면 상태 타입.
// 표기·값 집합은 전부 계약 생성물에서 온다 — 여기서 다시 선언하지 않는다 (CLAUDE.md §3-6·§3-7).
import type { components } from '../../generated/fe-core';

type S = components['schemas'];

export type DatasetDetail = S['DatasetDetail'];
export type DatasetBasicInfo = S['DatasetBasicInfo'];
export type AccountRef = S['AccountRef'];

/**
 * 묘비(삭제된 데이터셋)다. **상세 화면이 없다** (`Policy_데이터셋_상세 §7`) — 계약은 404 를 낸다.
 * 못 그리는 다른 이유(501·네트워크)와 섞지 않는다. 섞으면 살아 있는 데이터를 지워졌다고 말한다.
 */
export class DatasetGone extends Error {}

/** 아직 구현되지 않은 op (`PLAN-SoT §9-㊹` 501 표). */
export class NotImplemented extends Error {}

/**
 * 상세를 채우는 곳. 실서버(`getDataset`)와 픽스처가 같은 얼굴을 쓴다 —
 * 서버가 501 을 그만 내면 화면 코드는 한 줄도 바뀌지 않는다.
 */
export interface DetailSource {
  get(datasetId: string): Promise<DatasetDetail>;
}

// ── 파일 관리 (`PLAN-SoT §9 〈175〉` — 회의 결정 · 정본 산문 밖) ─────────────────────────

/** 등록된 데이터셋의 조각 하나. `byteSize` 가 `null` 이면 **모르는 것**이지 0 이 아니다 (`〈175〉-(가)`). */
export type DatasetFile = S['DatasetFile'];
export type FileKind = S['FileKind'];
/** 다운로드 티켓 — `url` 이 바이트다. 클라이언트는 그것을 **그대로 내비게이션**한다 (`〈175〉-(다)`). */
export type DownloadTicket = S['DownloadTicket'];

/** 없거나 경계 밖인 파일·데이터셋 (계약 404). `UploadGone` 과 같은 관례 — 다른 실패와 섞지 않는다. */
export class FileGone extends Error {}

/**
 * 그 데이터셋의 **마지막 본체 파일**이다 — 본체 ≥ 1 불변식 (`DataModel §4.3` · `〈175〉-(라)` · 계약 409).
 * `message` 는 서버가 보낸 문장 그대로다 — 화면은 그것을 바꾸지 않고 보여 준다.
 */
export class LastBodyFile extends Error {}

/**
 * 파일 관리가 서버와 만나는 얼굴 (`listDatasetFiles` · `downloadDataset`/`downloadDatasetFile` ·
 * `addDatasetFile` · `replaceDatasetGridFile` · `deleteDatasetGridFile`).
 * **픽스처 폴백이 없다** — 쓰기 경로라 실패는 실패로 보여야 한다 (`uploadSource.ts` 머리말과 같은 이유).
 */
export interface FileSource {
  /** 조각 목록. **사람이 `보기` 를 눌렀을 때만** 부른다 (`Policy_데이터셋_상세 §5`). */
  list(datasetId: string): Promise<DatasetFile[]>;
  /** `fileId` 가 있으면 파일 하나, 없으면 묶음(zip) 티켓. 이 응답 시점에 다운로드 이력이 쌓인다. */
  downloadTicket(datasetId: string, fileId?: string): Promise<DownloadTicket>;
  /** 본체 후주입. `기준 격자 파일` 은 여기가 아니라 `attachUploadGridFiles`(격자 추가 모달)다 — 서버가 400 을 낸다. */
  add(datasetId: string, file: File, kind: FileKind, relativePath?: string): Promise<DatasetFile>;
  /** 파일 갈아 끼우기 — 축 배정은 그대로. 축 뒤집기(`flipAxes`)는 이 화면의 조작이 아니다. */
  replace(datasetId: string, fileId: string, file: File): Promise<DatasetFile>;
  /** 삭제. 마지막 본체면 `LastBodyFile`. */
  remove(datasetId: string, fileId: string): Promise<void>;
}
