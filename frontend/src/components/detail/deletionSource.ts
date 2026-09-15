// 데이터셋 삭제 두 op 의 실서버 구현 (`DL-1`). 타입은 전부 생성물에서 온다.
//
// **픽스처 폴백을 두지 않는다.** 상세(`detailSource.ts`)는 읽기라 픽스처로 그려도 화면이
// 거짓말을 하지 않지만, 삭제는 **되돌리는 전이가 없는 경로**다 — 픽스처가 성공을 흉내 내면
// 화면은 지웠다고 말하고 데이터는 그대로 있다. 실패는 실패로 보여야 한다
// (`fileSource.ts`·`uploadSource.ts` 머리말과 같은 이유).
//
// 파급 조회도 같은 자리에 둔다 — 모달이 그 값을 못 읽으면 **삭제 버튼이 비활성**이어야 하고,
// 그 판정을 하려면 두 호출이 한 얼굴 뒤에 있어야 한다.
import { api } from '../../api/client';
import { DatasetGone, NotImplemented, type DatasetDeletionSource, type DeletionImpact } from './types';

/** 오류 봉투(`ErrorEnvelope.message`)의 문장. 없으면 `undefined` — 지어내지 않는다. */
function serverMessage(error: unknown): string | undefined {
  const m = (error as { message?: unknown } | undefined)?.message;
  return typeof m === 'string' && m.length > 0 ? m : undefined;
}

export function apiDeletionSource(): DatasetDeletionSource {
  return {
    async impact(datasetId): Promise<DeletionImpact> {
      const r = await api.GET('/datasets/{datasetId}/deletion-impact', {
        params: { path: { datasetId } },
      });
      // 404 = 경계 밖·묘비·무존재가 **한 자리로 접힌 것**이다 (P-9·P-10). 화면은 셋을 못 가른다.
      if (r.response.status === 404) throw new DatasetGone();
      if (r.response.status === 501) throw new NotImplemented();
      // 403 = 소유자도 교수도 아니다. 서버 문장이 있으면 그대로 보여 준다.
      if (!r.data) throw new Error(serverMessage(r.error) ?? '삭제 파급을 불러오지 못했어요.'); // [정본 무근거 · `DL-1`]
      return r.data;
    },

    async remove(datasetId): Promise<void> {
      const r = await api.DELETE('/datasets/{datasetId}', {
        params: { path: { datasetId } },
      });
      if (r.response.status === 404) throw new DatasetGone();
      if (r.response.status === 501) throw new NotImplemented();
      if (!r.response.ok) throw new Error(serverMessage(r.error) ?? '데이터를 지우지 못했어요.'); // [정본 무근거 · `DL-1`]
    },
  };
}

/** 화면이 쓰는 기본 출처. **픽스처로 떨어지는 갈래가 없다** — 위 머리말이 이유를 적었다. */
export function defaultDeletionSource(): DatasetDeletionSource {
  return apiDeletionSource();
}
