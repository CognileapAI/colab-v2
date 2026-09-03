// S-05 데이터셋 상세의 화면 상태 타입.
// 표기·값 집합은 전부 계약 생성물에서 온다 — 여기서 다시 선언하지 않는다 (CLAUDE.md §3-6·§3-7).
import type { components } from '../../generated/fe-core';

type S = components['schemas'];

export type DatasetDetail = S['DatasetDetail'];
export type DatasetBasicInfo = S['DatasetBasicInfo'];
export type AccountRef = S['AccountRef'];
export type DatasetProjectUse = S['DatasetProjectUse'];

/**
 * **그릴 상세가 없다** — 계약 404 (`NotFound`). 세 경우가 여기 한 자리로 접힌다:
 * 남의 연구실 묘비 · 남의 연구실 생존 · 있었던 적 없는 id. **화면은 셋을 가를 수 없고,
 * 가르면 안 된다** — 구분해 주는 것 자체가 존재의 누설이다 (P-9·P-10).
 * 그래서 이 자리의 문구는 `Policy_공통_기반 §2.4` 의 **중립 한 줄**이다 (`〈296〉`-㉰).
 *
 * ⚠ **묘비와 이름을 섞지 않는다** — 아래 `DatasetTombstone` 이 그쪽이다.
 * 못 그리는 다른 이유(501·네트워크)와도 섞지 않는다. 섞으면 살아 있는 데이터를 지워졌다고 말한다.
 */
export class DatasetGone extends Error {}

/**
 * ⭑ **⟨신설 2026-09-03 · 17차 해제 · Ted 판정 ②⟩ 묘비다 — 계약 410 (`Gone`).**
 *
 * **보는 사람의 연구실에서 지워진 것**이고, 서버가 그 한 칸에만 410 을 낸다. 그 행은
 * 지워지기 전에 이미 그 사람 목록에 있던 것이라 「지워졌다」가 **새로 알리는 사실이 0** 이다.
 * 이 상태에서만 `Policy_데이터셋_상세 §9` 의 묘비 문구를 쓴다 — 404 에서 그 문구를 쓰면
 * **있지도 않았던 데이터를 있었다고 말하게 된다.**
 */
export class DatasetTombstone extends Error {}

/**
 * 상세를 채우는 곳. 실서버(`getDataset`)와 픽스처가 같은 얼굴을 쓴다 —
 * 서버가 501 을 그만 내면 화면 코드는 한 줄도 바뀌지 않는다.
 */
export interface DetailSource {
  get(datasetId: string): Promise<DatasetDetail>;
}
