// 연구실 정보의 읽기·쓰기를 **한 곳**에 둔다.
//
// 읽기는 홈의 읽기 모달(`components/dashboard/LabInfoModal.tsx`)과
// `연구실 설정 > 연구실 정보` 탭이 **같은 값**을 본다 (계약 `getLab` 산문 축자).
// 그래서 `GET /lab` 배선을 두 벌 두지 않는다 — 대시보드 배선도 이 파일을 부른다.
//
// 편집은 `updateLab` 하나뿐이고 **`연구실 설정` 스위치가 켜진 사람만**이다
// (`Policy_역할과_권한 나-2` 「연구실 정보 편집 · `연구실 설정` · 거절한다. 읽기는 전 구성원」).
// 화면의 숨김은 안내이고 판정은 서버다 (같은 문서 7절) — 그래서 여기서 권한을 보지 않는다.
import { api } from '../../api/client';
import type { components } from '../../generated/fe-core';

type S = components['schemas'];
export type Lab = S['Lab'];
export type LabUpdate = S['LabUpdate'];

type Envelope = { message?: string } | undefined;

/** 실서버와 시험 대역이 같은 얼굴을 쓴다 (`DashboardSource` 와 같은 무늬). */
export interface LabSource {
  read(): Promise<Lab>;
  update(changes: LabUpdate): Promise<Lab>;
}

export function apiLabSource(): LabSource {
  return {
    async read() {
      const r = await api.GET('/lab', {});
      // 문구를 화면이 지어내지 않는다 — 서버 봉투의 message 를 그대로 올린다.
      if (!r.data) throw new Error((r.error as Envelope)?.message || '연구실 정보를 불러오지 못했어요.');
      return r.data;
    },
    async update(changes) {
      const r = await api.PATCH('/lab', { body: changes });
      if (!r.data) throw new Error((r.error as Envelope)?.message || '연구실 정보를 저장하지 못했어요.');
      return r.data;
    },
  };
}
