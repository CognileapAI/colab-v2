// S-08 미등록 미리보기의 타입·포트. **타입은 전부 생성물에서 온다** — 여기서 다시 선언하지 않는다
// (`CLAUDE.md §3-7` · `frontend/README.md`). 이 파일이 새로 만드는 것은 화면 쪽 어휘뿐이다.
import type { Schemas } from '../../api/client';
import type { PreviewPiece, TargetDescription } from './pick';

export type RenderJob = Schemas['RenderJob'];
export type RenderStage = Schemas['RenderStage'];
export type RenderResult = Schemas['RenderResult'];
export type PartialFailure = Schemas['PartialFailure'];
export type UploadFileRef = Schemas['UploadFileRef'];

/**
 * **파일 헤더에서 읽은 값만** 담는 자리 (정본 §8.1 기본정보 — 포맷·크기·좌표계·기간·변수·격자).
 * 전부 선택 항목인 것이 요점이다 — **못 받은 항목은 화면에서 자리째 빠진다.**
 * 사람이 붙이는 값(이름·주제·소속 프로젝트)은 **여기에 자리 자체가 없다.**
 *
 * ⚠ 지금 FE 표면(`fe-core.yaml`)이 실제로 실어 주는 것은 `byteSize` 하나이고,
 * `variable` 은 완료된 렌더의 `legend.variable`(실제로 그린 값)에서만 온다.
 * 포맷·좌표계·기간·격자는 **동결 계약이 미등록 업로드에 대해 내려 주지 않는다** —
 * 지어내지 않고 자리를 뺀다 (`DR-9` — 못 읽은 것은 `[미상]`이고 만들어 넣지 않는다).
 */
export interface PreviewBasicInfo {
  format?: string;
  byteSize?: number;
  crs?: string;
  period?: string;
  variable?: string;
  grid?: string;
}

/**
 * S-04 모달 → S-08 로 **미리보기를 그대로 이어 붙이는** 짐 (정본 §8.1 미리보기 · §7.2 전이).
 * `renderId` 가 이어짐의 실물이다 — 이것이 있으면 S-08 은 **다시 그리지 않고 이어서 본다.**
 */
export interface PreviewHandoff {
  uploadId: string;
  renderId?: string;
  /**
   * 짝 파일 없이 그려 봤는가 (정본 §8 「`짝 파일 없이 그려 보기`」). **S-04 가 아는 사실**이라
   * 이어받는다 — S-08 이 지어내면 다시 그릴 때 앞과 다른 그림이 나온다. 없으면 계약 기본값 false.
   */
  withoutReferenceGrid?: boolean;
  basicInfo: PreviewBasicInfo;
  files: UploadFileRef[];
}

/**
 * 다시 그리기 요청. 표현 컨트롤은 정본에서 둘뿐이고(팔레트·구간 수), **고르개 셋(WU-C3)이
 * 얹히는 자리는 그 옆이다** — 계약 `RenderTarget.fileIds` · `RenderRequest.variable`·`instant`.
 * 셋 다 **선택**이다: 생략하면 서버가 고른다(계약 산문 축자).
 */
export interface RerenderInput {
  uploadId: string;
  palette: string;
  classCount: number;
  withoutReferenceGrid: boolean;
  /** 그릴 조각. 생략하면 대상 전체다 — 500MB 폴백이 여기로 온다. */
  fileIds?: string[] | undefined;
  /** 그릴 값 하나. 생략하면 viz-render 가 고른다. */
  variable?: string | undefined;
  /** 그릴 시각. 생략하면 첫 시각이다. */
  instant?: string | undefined;
}

/**
 * 미리보기 결과가 **없는 것으로 답해졌다** (정본 §8.1 수명 · §9 「수명이 지난 파일」).
 * 만료된 렌더의 타일은 FE 에 **410 이 아니라 401 로 보인다** (`P2-viz-report` 부록 `A-1`) —
 * 그 401 도 여기로 온다. **「권한이 없다」로 말하지 않는다.**
 */
export class PreviewGone extends Error {}

/** 어느 표현으로도 못 그린다 (415). **등록·다운로드·계보 확정은 그대로 된다** (정본 §9). */
export class NotRenderableError extends Error {
  constructor(
    message: string,
    readonly renderableFormats: string[],
  ) {
    super(message);
  }
}

/** 미리보기를 만들 수 없다 — 그리는 서버에 못 닿음(503 중계). 등록은 막지 않는다. */
export class PreviewUnavailable extends Error {}

export interface PreviewSource {
  /** 렌더 작업 조회. **실패는 200 + `failure`** 라 여기서 예외가 되지 않는다. */
  get(renderId: string): Promise<RenderJob>;
  /** 컨트롤을 바꿨을 때만 부른다. */
  create(input: RerenderInput): Promise<RenderJob>;
  /** 타일 한 장을 찔러 본다. 401 = 만료 (서명이 결과 수명과 함께 죽는다, `〈68〉`-ⓓ). */
  probeTile(url: string): Promise<'ok' | 'expired'>;
  /**
   * WU-C3 — 대상의 조각 목록. **413 폴백과 파일 고르개의 유일한 후보 출처다.**
   * 선택 메서드인 것은 이 포트를 이미 구현한 자리(시험 픽스처 포함)를 깨지 않기 위해서다 —
   * 없으면 폴백을 하지 않고 **기존 실패 경로**로 간다(없는 것을 지어내지 않는다).
   */
  files?(): Promise<PreviewPiece[]>;
  /** WU-C3 — 변수·시각 후보와 **서버 기본값** (`describeTarget` 중계). */
  describe?(): Promise<TargetDescription>;
}
