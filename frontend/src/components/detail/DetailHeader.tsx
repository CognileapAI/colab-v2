// 상세 헤더 — **줄마다 한 가지만 말한다** (`Policy_데이터셋_상세 §8`).
// ① 제목 = 사람이 붙인 이름 ② 파일명(작게·고정폭) ③ 한 줄 요약 ④ 판단에 쓰는 칩만.
// 소유자·올린 사람·포맷은 여기 두지 않는다 — 기본 정보가 라벨:값으로 맡는다 (§12 v1.6 중복 3건 제거).
import { VerifiedBadgeSlot } from '../../placeholders/VerifiedBadgeSlot';
import type { DatasetDetail } from './types';

export function DetailHeader(props: { detail: DatasetDetail }) {
  const d = props.detail;
  return (
    <div className="dt-header" data-testid="detail-header">
      <div className="dh-main">
        <h1>{d.name}</h1>
        {d.fileName ? (
          <div className="dh-file" data-testid="dh-file">
            {d.fileName}
          </div>
        ) : null}
        {d.summary ? (
          <div className="dh-sum" data-testid="dh-sum">
            {d.summary}
          </div>
        ) : null}
        <div className="dh-tags" data-testid="dh-tags">
          {d.topic ? <span className="chip chip--neutral">{d.topic}</span> : null}
          <span className={`lvl lvl-${Math.min(d.processingLevel, 3)}`}>
            Lv{d.processingLevel}
          </span>
          {/* 잠긴 상세도 헤더 태그까지는 보인다 (`§3.3` · P-13) */}
          {d.accessState === '잠김' ? <span className="chip chip--warning">잠김</span> : null}
          {/* Verified 배지 — 표시 전용이고 모양·조건은 E-06(WU-P6)이 채운다 (`§8`) */}
          <VerifiedBadgeSlot />
        </div>
      </div>
      {/* 헤더 우측 **한 자리**가 상태 × 보는 사람에 따라 셋으로 갈린다
          (승인 요청 / 승인 / 승인 취소). 규칙은 E-06 정책이 정한다 — WU-P6 이 채운다 */}
      <div className="dh-act" data-slot="verification-action" data-fills-in="WU-P6" />
    </div>
  );
}
