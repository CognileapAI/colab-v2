// 미리보기 컨트롤. **정본이 준 컨트롤은 둘뿐이다** — 팔레트와 구간 수
// (`core-viz.yaml#RenderStyle` 주석 · `P2-EXEC §4 W2 P2-viz ⑵`).
//
// ⚠ **낡은 주석 정정(2026-08-28).** 이전 판은 「팔레트 목록을 주는 서버 동작이 계약에 없다」고
// 적었으나 **지금은 계약·구현 둘 다 있다** — `contracts/seams/fe-core.yaml` 의 `listPalettes` 와
// 그것을 `GET /preview-palettes` 로 중계하는 `services/core-api/.../routes/preview.py`.
// 그러니 이 자리가 비어 있는 이유는 **계약이 없어서가 아니라 이 화면의 범위가 「보기만」이기
// 때문이다** — S-08 에서 표현을 바꾸는 것은 정본 §8.1 에 없고(`정본 무근거`),
// Ted 2026-08-28 완료 정의도 「표현 변경 없음 · 팔레트 컨트롤은 범위 밖」으로 못 박았다.
// 다시 그릴 때 쓰는 팔레트 키는 **완료된 렌더가 실제로 쓴 값**(`legend.palette`)뿐이고,
// 화면이 이름을 지어내지 않는다. 목록을 붙이려면 완료 정의를 먼저 고친다.

/** 정본이 준 값 그대로: 3~9 단계, 기본 6 (`Policy_데이터셋_상세 §5 시각화 구간 수`). */
export const CLASS_COUNTS = [3, 4, 5, 6, 7, 8, 9] as const;
export const DEFAULT_CLASS_COUNT = 6;

export function PreviewControls(props: {
  classCount: number;
  onClassCount: (n: number) => void;
  disabled: boolean;
}) {
  return (
    <div className="pv-controls" aria-label="미리보기 표현">
      <div className="pv-control" data-testid="palette-control">
        <span className="pv-control-label" id="pv-palette-label">
          팔레트
        </span>
        {/* 후보를 화면이 만들지 않는다. 팔레트 키는 viz-render 소유의 불투명 값이라
            사람에게 보여 줄 이름이 아니고, 정본에도 팔레트 이름이 없다 (`P2-viz-report §8 V-1`).
            **목록을 못 불러오는 것이 아니라 이 화면에서 고르지 않는 것이다** — 위 주석 참조. */}
        <p className="pv-muted">고를 수 있는 팔레트 목록을 아직 불러올 수 없어요.</p>
      </div>

      <div className="pv-control">
        <label className="pv-control-label" htmlFor="pv-classcount">
          구간 수
        </label>
        <select
          id="pv-classcount"
          value={String(props.classCount)}
          disabled={props.disabled}
          onChange={(e) => props.onClassCount(Number(e.currentTarget.value))}
        >
          {CLASS_COUNTS.map((n) => (
            <option key={n} value={String(n)}>
              {n}
            </option>
          ))}
        </select>
      </div>
    </div>
  );
}
