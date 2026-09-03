// 없는 주소. 문구의 정본은 `Policy_공통_기반` v1.6 `§2.4` 「없는 주소」 행이다.
//
// ⛔ **묘비 문구를 여기에 쓰지 않는다.** 「이 데이터는 지워졌어요」(`Policy_데이터셋_상세 §9`)는
//    **있었던 것이 지워졌다**는 사실을 말한다. 주소가 배정되지 않은 것은 그것과 다른 일이고,
//    섞으면 있지도 않았던 데이터를 있었다고 말하게 된다. 그래서 중립 한 줄이다.
import { Link } from 'react-router-dom';

export function NotFoundPage() {
  return (
    <div className="notfound" data-screen="not-found">
      <p data-testid="not-found-message">이 주소에는 화면이 없어요.</p>
      <Link to="/lab">연구실로 돌아가기</Link>
    </div>
  );
}
