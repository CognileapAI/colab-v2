// 값 조회 자리 (`V-2` · `PLAN-SoT §9 〈294〉` · 15차 동결 해제).
//
// 정본 `Policy_데이터셋_상세 §8 값 조회` — 조회 자리는 **등록된 데이터셋 · 좌표 있는 자료 ·
// 본체를 볼 수 있는 사람**에만 선다. 이 파일이 그 셋을 각각 어떻게 지키는가:
//  · **등록된 데이터셋** = 이 구역은 데이터셋 상세(S-05)에만 마운트된다. S-08(미등록
//    미리보기)에는 세우지 않는다 — 그 화면에는 자리에 구운 산출물이 애초에 없다.
//  · **좌표 있는 자료** = `bounds` 가 없는 결과(②비지도형)에는 자리째 없다. 부모가
//    `bounds` 를 줄 때만 이 컴포넌트를 세운다.
//  · **본체를 볼 수 있는 사람** = 잠긴 데이터셋은 상세 화면이 본문째 막는다
//    (`LockedContent`) — 미리보기 구역 자체가 마운트되지 않는다. 서버도 같은 기준으로
//    막는다(403 · `lookupDatasetValue`).
//
// **약속하지 못하는 것을 먼저 말한다** (완료 정의 ⑷) — 답이 「한 칸」의 값이라는 것과,
// 좌표를 따로 입힌 격자에서는 「가장 가까운 칸」이라는 것을 서버가 값과 같은 응답에
// 실어 보내고 이 화면이 그것을 **그대로** 적는다. 화면이 문구를 지어내지 않는다.
//
// **다시 그리지 않는다** (완료 정의 ⑵) — 이 구역은 렌더를 시작하지도, 배율·범례를
// 건드리지도 않는다.
import { useRef, useState } from 'react';
import type { DatasetPreviewSource, ValueLookupResult } from './types';

type LookupState =
  | { phase: '고르기 전' }
  | { phase: '읽는 중'; point: { lat: number; lon: number } }
  | { phase: '읽음'; point: { lat: number; lon: number }; result: ValueLookupResult }
  | { phase: '못 읽음'; message: string };

/** 정본 §8 「그리는 서버에 연결 못 함」과 같은 결 — **값을 지어내지 않는다.** */
const UNAVAILABLE = '지금 값을 읽을 수 없어요. 잠시 뒤 다시 시도해 주세요.';

export function useValueLookup(source: DatasetPreviewSource) {
  const [state, setState] = useState<LookupState>({ phase: '고르기 전' });
  /**
   * 누름의 순번. **늦게 온 이전 응답이 최신 값을 덮지 않게** 한다 —
   * 이 화면에서 제일 나쁜 실패는 오류 없이 **다른 칸의 값**이 그려지는 것이라
   * (`〈294〉` 완료 정의의 ⚠), 순서 뒤집힘도 좌표 오산과 같은 등급으로 막는다.
   * 취소가 아니라 **무시**다 — 계약에 조회 취소가 없고, 서버는 이미 답을 만들었다.
   */
  const seq = useRef(0);

  const pick = (point: { lat: number; lon: number }) => {
    const mine = ++seq.current;
    setState({ phase: '읽는 중', point });
    void (async () => {
      try {
        const result = await source.lookupValue(point);
        if (seq.current !== mine) return;
        setState({ phase: '읽음', point, result });
      } catch {
        if (seq.current !== mine) return;
        setState({ phase: '못 읽음', message: UNAVAILABLE });
      }
    })();
  };
  return { state, pick };
}

/** 소수 넷째 자리 — 지도가 답하는 단위(한 칸)보다 잘게 쓰지 않는다. */
function coord(v: number): string {
  return v.toFixed(4);
}

export function ValueLookupPanel(props: { state: LookupState }) {
  const { state } = props;
  return (
    <div className="pv-value" data-testid="value-lookup" aria-live="polite">
      {state.phase === '고르기 전' ? (
        <p className="pv-muted">지도의 한 점을 누르면 그 자리의 값을 보여 줘요.</p>
      ) : null}

      {state.phase === '읽는 중' ? <p className="pv-muted">값을 읽는 중…</p> : null}

      {state.phase === '못 읽음' ? (
        <p className="pv-failure" role="alert" data-testid="value-lookup-unavailable">
          {state.message}
        </p>
      ) : null}

      {state.phase === '읽음' ? (
        <dl className="pv-value-body">
          <div>
            <dt>고른 자리</dt>
            <dd data-testid="value-lookup-point">
              {`위도 ${coord(state.point.lat)} · 경도 ${coord(state.point.lon)}`}
            </dd>
          </div>
          <div>
            <dt>값</dt>
            <dd data-testid="value-lookup-value">
              {state.result.available
                ? `${state.result.value}${state.result.unit ? ` ${state.result.unit}` : ''}`
                : /* **0 으로 바꾸지 않는다** (완료 정의 ⑸) — 「없음」이 답이다. */
                  '없음'}
            </dd>
          </div>
          {!state.result.available && state.result.unavailableReason ? (
            <div>
              <dt>사유</dt>
              {/* 서버가 가른 사유를 그대로 적는다 — 화면이 다시 분류하지 않는다 */}
              <dd data-testid="value-lookup-reason">{state.result.unavailableReason}</dd>
            </div>
          ) : null}
          <div>
            <dt>답하는 단위</dt>
            {/* ⑷ — 「원본 해상도 이상은 약속하지 않는다」를 값과 함께 말한다 */}
            <dd data-testid="value-lookup-exactness">{`한 칸 · ${state.result.exactness}`}</dd>
          </div>
        </dl>
      ) : null}
    </div>
  );
}
