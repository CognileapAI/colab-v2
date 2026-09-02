// 연구실 정보 **읽기 표시**의 유일한 자리. 홈의 읽기 모달과 `연구실 설정 > 연구실 정보` 탭이
// 이것 하나를 함께 쓴다 — 두 벌로 두면 항목 순서·이름이 갈린다
// (`DataModel_공통_기반 §2` 「연구실을 정의하는 유일한 자리다」).
import { EMPTY, orEmpty } from '../detail/format';
import type { Lab } from './labSource';

/** `Policy_홈_대시보드 §5` 「연구실 정보 항목」 — 여덟 칸. 순서와 이름을 바꾸지 않는다. */
export const LAB_INFO_FIELDS: { name: string; of: (lab: Lab) => string }[] = [
  { name: '연구실 이름', of: (l) => l.name },
  { name: '소속 대학', of: (l) => orEmpty(l.university) },
  { name: '학부/학과', of: (l) => orEmpty(l.department) },
  { name: '책임교수', of: (l) => orEmpty(l.principalInvestigator) },
  { name: '연구 분야', of: (l) => orEmpty(l.researchField) },
  { name: '구성원 수', of: (l) => `${l.memberCount}명` },
  { name: '데이터 공개 범위', of: (l) => l.defaultVisibility ?? EMPTY },
  { name: '한 줄 소개', of: (l) => orEmpty(l.introduction) },
];

export function LabInfoGrid(props: { lab: Lab }) {
  return (
    <dl className="lab-info-grid">
      {LAB_INFO_FIELDS.map((f) => (
        <div key={f.name}>
          <dt>{f.name}</dt>
          <dd>{f.of(props.lab)}</dd>
        </div>
      ))}
    </dl>
  );
}
