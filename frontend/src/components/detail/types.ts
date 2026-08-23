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

/**
 * 상세를 채우는 곳. 실서버(`getDataset`)와 픽스처가 같은 얼굴을 쓴다 —
 * 서버가 501 을 그만 내면 화면 코드는 한 줄도 바뀌지 않는다.
 */
export interface DetailSource {
  get(datasetId: string): Promise<DatasetDetail>;
}
