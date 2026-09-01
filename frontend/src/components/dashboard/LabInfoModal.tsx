// 연구실 정보 읽기 모달 — `우리 연구실` 라벨을 누르면 열린다 (`Policy_홈_대시보드 §8`).
//
// **읽기는 전 구성원, 편집 버튼만 권한자** (§6 축자). 편집 화면(연구실 설정)이 권한자
// 전용이라 그 화면을 못 여는 사람은 자기 연구실이 어떤 곳인지 볼 방법이 없었다.
//
// **값을 여기서 고치지 않는다** (§1.2 · §5.2 — 값의 주인은 E-01 연구실 설정이다).
// 편집 버튼은 그 화면으로 보내기만 한다.
import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { PermissionGate } from '../../permission/PermissionGate';
import { EMPTY, orEmpty } from '../detail/format';
import type { DashboardSource, Lab } from './types';

/** §5 「연구실 정보 항목」 — 여덟 칸. 순서와 이름을 바꾸지 않는다. */
const FIELDS: { name: string; of: (lab: Lab) => string }[] = [
  { name: '연구실 이름', of: (l) => l.name },
  { name: '소속 대학', of: (l) => orEmpty(l.university) },
  { name: '학부/학과', of: (l) => orEmpty(l.department) },
  { name: '책임교수', of: (l) => orEmpty(l.principalInvestigator) },
  { name: '연구 분야', of: (l) => orEmpty(l.researchField) },
  { name: '구성원 수', of: (l) => `${l.memberCount}명` },
  { name: '데이터 공개 범위', of: (l) => l.defaultVisibility ?? EMPTY },
  { name: '한 줄 소개', of: (l) => orEmpty(l.introduction) },
];

export function LabInfoModal(props: { source: DashboardSource; onClose: () => void }) {
  const navigate = useNavigate();
  const [lab, setLab] = useState<Lab | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;
    props.source
      .lab()
      .then((value) => alive && setLab(value))
      .catch((e: unknown) => {
        if (alive) setError(e instanceof Error ? e.message : '연구실 정보를 불러오지 못했어요.');
      });
    return () => {
      alive = false;
    };
  }, [props.source]);

  return (
    <div className="modal-back" role="dialog" aria-modal="true" aria-label="연구실 정보">
      <div className="modal lab-info">
        <h2>연구실 정보</h2>
        {error ? <p className="dash-error">{error}</p> : null}
        {lab ? (
          <dl className="lab-info-grid">
            {FIELDS.map((f) => (
              <div key={f.name}>
                <dt>{f.name}</dt>
                <dd>{f.of(lab)}</dd>
              </div>
            ))}
          </dl>
        ) : null}
        <div className="modal-foot">
          {/* 편집 버튼만 권한자에게 (§6). 읽기는 열고 **버튼만 숨긴다.** */}
          <PermissionGate requires="연구실 설정">
            <button type="button" onClick={() => navigate('/lab-settings')}>
              연구실 정보 편집
            </button>
          </PermissionGate>
          <button type="button" onClick={props.onClose}>
            닫기
          </button>
        </div>
      </div>
    </div>
  );
}
