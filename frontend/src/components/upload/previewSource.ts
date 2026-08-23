// 미리보기 렌더 중계 2 op + 팔레트 출처.
//
// **소비 규칙은 `sessions/P2-viz-report.md §13`·부록 A 가 준 것을 그대로 따른다.**
// ⑴ 실패는 4xx 가 아니라 **200 + `failure`** 다 — 여기서 status 로 실패를 판정하지 않는다.
// ⑵ `tileUrlTemplate` 은 **불투명 문자열**이다(`〈68〉` 서명 포함). 뜯거나 다시 조립하지 않는다.
// ⑶ 만료된 렌더의 타일은 FE 에 **401** 로 온다 — 사람 권한 문제가 아니라 만료다.
import { api } from '../../api/client';
import { NotImplemented, type PaletteOption, type PreviewSource, type RenderRequest } from './types';

/**
 * ⛔ **`listPalettes` 의 FE 중계가 동결 계약에 없다.**
 * `fe-core.yaml`(`/previews` 산문)이 「`style.palette` 값 집합의 FE 도달 경로(`listPalettes` 중계)는
 * 이 개정이 열지 않는다 — 열린 항목으로 보고한다」라고 **명시적으로 열어 둔 채 남겼다.**
 * 그래서 이 화면에는 팔레트 값을 얻을 계약 경로가 없다.
 *
 * **지어내지 않는다** — 목록을 하드코딩하면 viz-render 가 모르는 키를 보내게 되고,
 * 그 순간 `RenderStyle.palette` 의 정본이 화면으로 옮겨 앉는다(`P2-viz` 가 `listPalettes` 를
 * 만든 이유가 정확히 그것이다). 대신 **닿지 않는다는 사실을 그대로 던지고**, 화면은 정본 §9 의
 * 「그리는 서버에 연결 못 함」 문구로 정직하게 알린 뒤 **등록은 막지 않는다.**
 * 중계가 열리면 이 함수 하나만 바뀐다.
 */
export class PalettesUnreachable extends Error {}

export function apiPreviewSource(): PreviewSource {
  return {
    async palettes(): Promise<PaletteOption[]> {
      throw new PalettesUnreachable('listPalettes 중계가 fe-core 계약에 없다.');
    },

    async createRender(req: RenderRequest) {
      const r = await api.POST('/previews', { body: req });
      if (r.response.status === 501) throw new NotImplemented();
      if (!r.data) throw new Error('미리보기를 시작하지 못했어요.');
      return r.data;
    },

    async getRender(renderId: string) {
      const r = await api.GET('/previews/{renderId}', { params: { path: { renderId } } });
      if (r.response.status === 501) throw new NotImplemented();
      if (!r.data) throw new Error('미리보기 상태를 읽지 못했어요.');
      return r.data;
    },
  };
}
