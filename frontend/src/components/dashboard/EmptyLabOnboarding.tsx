// 빈 연구실 온보딩 — 데이터 0건일 때 (`Policy_홈_대시보드 §3.3` · §8).
//
// **데이터가 한 건이라도 올라오면 빈 홈은 채워진 홈으로 바뀐다** (§1.3-9). 계보가 붙기를
// 기다리지 않는다 — 그래서 판정 값은 `datasetCount` 하나다.
//
// 검색 히어로는 여기 없다. **자리를 그대로 두고 예고 상태로** 두는 것은 히어로 자신의
// 몫이다 (§8 「빈 연구실 히어로」) — 자리가 매일 바뀌면 다시 찾아야 한다.
import { useNavigate } from 'react-router-dom';

/** §3.3 안내 문구 축자. 화면이 다시 쓰지 않는다. */
const LEAD = '아직 올라온 데이터가 없어요. 과거 데이터를 한꺼번에 옮기지 않아도 돼요. 지금 쓰는 데이터 한 건부터 시작하세요.';

/** §3.3 복구 3단계. 순서를 바꾸지 않는다. */
const STEPS = ['첫 데이터 업로드', '계보 확인', '구성원 초대'];

export function EmptyLabOnboarding() {
  const navigate = useNavigate();
  return (
    <section className="dash-card" data-card="onboarding">
      <div className="dash-card-head">
        <h2>이렇게 시작해요</h2>
      </div>
      <p className="dash-lead">{LEAD}</p>
      <ol className="dash-steps">
        {STEPS.map((step, i) => (
          <li key={step}>
            <span className="dash-step-no">{i + 1}</span>
            {step}
          </li>
        ))}
      </ol>
      <button type="button" className="dash-open-catalog" onClick={() => navigate('/datasets')}>
        데이터셋 카탈로그 열기
      </button>
    </section>
  );
}
