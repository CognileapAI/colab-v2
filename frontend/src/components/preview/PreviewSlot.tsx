/**
 * 미리보기 **자리 선점 틀** (축 ① · `intent/2026-09-08-preview-slot.md ①` · R-C spec 「자리 선점 상태기계」).
 *
 * 요구는 하나다 — **그림이 완성돼야 자리가 생기면 안 된다.** 파일을 고른 순간(업로드 장면2)·
 * 상세를 연 순간 이미 `4:3` 상자가 서 있고, 그 **안쪽만** 바뀐다:
 *
 *   idle(`.vizph`) → drawing(진행 3단계) → done(그림+범례) | failed(`.vizerr` · salvage 유지)
 *
 * ⚠ **바깥 치수는 네 상태에서 한 픽셀도 바뀌지 않는다** — 비율은 CSS 토큰 `--pv-frame-ratio`
 *   한 자리(`preview.css`)에 있고 WU-C4·C5 가 같은 토큰을 다시 쓴다.
 * ⚠ **문면을 만들지 않는다** — 이 파일에 한국어 화면 글자는 없다. 안내·오류 문구는 전부
 *   호출부가 이미 갖고 있는 정본 문면(`UNAVAILABLE`·`UnavailableNotice`·진행 3단계)이다.
 * ⚠ 확장보기(㈎)·격자 업로드 블록은 이 틀 **밖·같은 컨테이너 안**에 그대로 남는다(존치 규칙).
 * ⚠ ⭑ ⟨증보 2026-09-12 · R-BUGFIX-260912 `#25`⑵ · spec v2 §6 ㉮⟩ 존치 규칙에 **「틀 위 줄」**이
 *   더해진다 — `controls` 로 받은 줄(파일·변수·시각 고르개)은 이 틀 **밖·틀보다 앞선 형제**로
 *   서고, 틀 안 스크롤(`.pv-frame-in` · `overflow:auto`)에 실리지 않는다. 배치 규약이 이
 *   부품 한 곳에 모이므로 호출부 세 곳에 같은 JSX 순서를 복제하지 않는다. 줄과 틀 사이
 *   여백은 컨테이너(`.pv-frame-wrap`)의 gap 하나가 갖는다 — 자식은 margin 을 지지 않는다.
 */
import type { ReactNode } from 'react';
import './preview.css';

/**
 * 상태 네 값. **목록 길이 자체가 시험의 오라클이다**(green-by-skip 방지 — 상태가 줄면 red).
 * 값은 상태기계 원문의 순서 그대로다.
 */
export const PREVIEW_SLOT_STATES = ['idle', 'drawing', 'done', 'failed'] as const;

export type PreviewSlotState = (typeof PREVIEW_SLOT_STATES)[number];

export interface PreviewSlotProps {
  /** 지금 안쪽이 무엇을 그리는가. **바깥 상자에는 영향을 주지 않는다.** */
  state: PreviewSlotState;
  /** 화면마다 다른 표식(업로드·상세). 기본값은 공용 이름 하나다. */
  testId?: string;
  /** 틀 **밖·틀보다 앞** 고정 줄. 틀 안 스크롤에 실리지 않는다. */
  controls?: ReactNode;
  children: ReactNode;
}

/**
 * 4:3 틀. 바깥(`.pv-frame`)이 비율과 치수를 쥐고, 안쪽(`.pv-frame-in`)만 상태에 따라 갈린다.
 * 상태는 `data-preview-slot-state` 로 드러난다 — jsdom 이 계산 스타일을 주지 않으므로
 * 시험은 이 표식과 클래스, 그리고 CSS 원문을 읽어 잰다.
 */
export function PreviewSlot(props: PreviewSlotProps) {
  return (
    <div className="pv-frame-wrap">
      {props.controls}
      <div
        className="pv-frame"
        data-testid={props.testId ?? 'preview-slot'}
        data-preview-slot="4x3"
        data-preview-slot-state={props.state}
      >
        <div className="pv-frame-in">{props.children}</div>
      </div>
    </div>
  );
}
