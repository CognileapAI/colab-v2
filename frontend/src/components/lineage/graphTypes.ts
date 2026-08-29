// ④ S-05 상세의 **계보 그래프**가 바깥과 만나는 얼굴.
//
// 타입은 전부 계약 생성물에서 온다 — 여기서 스키마를 다시 선언하지 않는다
// (`CLAUDE.md §3-6·§3-7`). 업로드 단계의 `types.ts` 와 어휘를 나눠 쓰되,
// 그쪽 파일은 건드리지 않는다 — 다른 화면의 다른 op 이다.
import type { Schemas } from '../../api/client';

export type LineageGraph = Schemas['LineageGraph'];
export type LineageNode = Schemas['LineageNode'];
export type LineageEdge = Schemas['LineageEdge'];
export type LineageState = Schemas['LineageState'];

/** 노드가 서는 칸. 가로축은 데이터만 세운다 (`Policy_데이터셋_상세 §1-2`). */
export type LineageColumn = 0 | 1 | 2 | 3;

/** 가로축 라벨 — 순서가 곧 정본의 축이다 (`§8` 원천 → 가공 전 → 이 데이터 → 파생). */
export const COLUMN_KINDS: LineageNode['kind'][] = ['원천', '가공 전', '이 데이터', '파생'];

/**
 * 계보를 채우는 곳. 실서버(`getDatasetLineage`)와 픽스처가 같은 얼굴을 쓴다 —
 * 서버가 붙는 순간 화면 코드는 한 줄도 바뀌지 않는다.
 */
export interface LineageGraphSource {
  get(datasetId: string): Promise<LineageGraph>;
}
