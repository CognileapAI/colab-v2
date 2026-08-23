// 미리보기 컨트롤. **정본이 준 컨트롤은 둘뿐이다** — 팔레트와 구간 수
// (`core-viz.yaml#RenderStyle` 주석 · `P2-EXEC §4 W2 P2-viz ⑵`).
//
// ⚠ **팔레트 목록의 출처는 `listPalettes` 인데 그 op 이 FE 표면에 없다.**
// `contracts/seams/core-viz.yaml:169` 의 `/palettes` 는 내부 seam 이고,
// 동결된 `fe-core.yaml` 에는 중계가 없다(`D2c` C1 열린 항목 ① 이 그대로 열려 있다).
// **그래서 이름을 지어내 목록을 만들지 않는다** — 완료된 렌더가 실제로 쓴 팔레트 키
// (`legend.palette`)를 그대로 되쓰고, 고르는 자리는 **왜 못 고르는지 밝힌 채** 비워 둔다.
// 계약을 고치는 것은 이 레인의 자리가 아니다 (`CLAUDE.md §4` — 멈추고 보고한다).

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
            사람에게 보여 줄 이름이 아니고, 정본에도 팔레트 이름이 없다 (`P2-viz-report §8 V-1`) */}
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
