// 미리보기 렌더 중계 2 op + 팔레트 출처.
//
// **소비 규칙은 `sessions/P2-viz-report.md §13`·부록 A 가 준 것을 그대로 따른다.**
// ⑴ 실패는 4xx 가 아니라 **200 + `failure`** 다 — 여기서 status 로 실패를 판정하지 않는다.
// ⑵ `tileUrlTemplate` 은 **불투명 문자열**이다(`〈68〉` 서명 포함). 뜯거나 다시 조립하지 않는다.
// ⑶ 만료된 렌더의 타일은 FE 에 **401** 로 온다 — 사람 권한 문제가 아니라 만료다.
import { api } from '../../api/client';
import { NotImplemented, type PaletteOption, type PreviewSource, type RenderRequest } from './types';

/**
 * ⭑ **⟨동결 4회 해제 · `PLAN-SoT §9-〈88〉` 묶음 4⟩ `listPalettes` 중계가 열렸다.**
 *
 * 이전 판은 여기서 **항상 예외를 던졌다.** `fe-core.yaml` 이 「`style.palette` 값 집합의
 * FE 도달 경로는 이 개정이 열지 않는다 — 열린 항목으로 보고한다」라고 명시적으로 비워 둔
 * 자리였기 때문이다. 그 결과 `PreviewPanel` 의 `palette` 가 빈 문자열로 남아
 * **`createRender` 가 한 번도 불리지 않았다** — 즉 **실서버에서 미리보기 렌더가 단 한 번도
 * 시작되지 않았다**(`sessions/S1-CONTRACT-GAP-SWEEP.md` `D-1`).
 * 프런트 시험이 전부 픽스처 소스를 주입해서 **이 파일만 죽어 있는 것을 아무도 못 봤다.**
 *
 * **여전히 지어내지 않는다** — 목록을 하드코딩하면 viz-render 가 모르는 키를 보내게 되고,
 * 그 순간 `RenderStyle.palette` 의 정본이 화면으로 옮겨 앉는다. 못 닿으면 **던진다**:
 * 빈 목록은 「고를 것이 없다」는 답이고 참인 것은 「물어보지 못했다」이다.
 */
export class PalettesUnreachable extends Error {}

export function apiPreviewSource(): PreviewSource {
  return {
    async palettes(): Promise<PaletteOption[]> {
      const r = await api.GET('/preview-palettes');
      if (r.response.status === 501) throw new NotImplemented();
      // 503 = `RENDER_UNAVAILABLE`. **빈 배열로 접지 않는다** — 화면이 「팔레트가 없다」고
      // 말하는데 사실은 「그리는 서버에 못 닿았다」가 된다 (`〈87〉-㉯` 가 검색에서 금지한 접기).
      if (!r.data) throw new PalettesUnreachable('팔레트 목록을 받지 못했어요.');
      return r.data.items ?? [];
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
