// 상세 헤더 — **줄마다 한 가지만 말한다** (`Policy_데이터셋_상세 §8`).
// ① 제목 = 사람이 붙인 이름 ② 파일명(작게·고정폭) ③ 한 줄 요약 ④ 판단에 쓰는 칩만.
// 소유자·올린 사람·포맷은 여기 두지 않는다 — 기본 정보가 라벨:값으로 맡는다 (§12 v1.6 중복 3건 제거).
import { VerifiedBadge } from '../approval/VerifiedBadge';
import { VerificationAction } from '../approval/VerificationAction';
import type { ApprovalSource } from '../approval/types';
import type { DatasetDetail } from './types';

/**
 * ⭑ **⟨버그 15 · A안⟩ 설명문의 전각 슬래시 `／` 는 **표시 단계에서만** 줄로 나눈다.**
 *
 * 그 `／` 는 시드 `summary` 12건 42개에 사람이 손으로 적은 **원천 문서 문단의 이음매**다
 * (`infra/staging/manifest-s2.json` · 원문 `sessions/S2b-DATASET-DESCRIPTIONS.md` · 2026-08-26 Ted 승인).
 * **저장·검색·계약은 손대지 않는다** — 재시드는 운영 접촉이고 승인문을 다시 열게 된다.
 * 목록·검색 카드(`.hit-summary`)도 종전 한 줄 그대로다. 나누는 곳은 상세 헤더 하나뿐이다.
 *
 * `／` 가 없으면 조각이 1개라 **종전과 완전히 같은 한 줄**로 선다 — 사용자가 넣는 설명이 그쪽이다
 * (`RegisterArea` 는 300자 한 줄 입력이라 `／` 관례가 없다).
 *
 * ⚠ 정본 `Policy_데이터셋_상세 §8` 은 이 자리를 「③ 한 줄 요약」이라 부른다. 여러 줄로 펼치는 것은
 * **Ted 최종 확인 대기**이고, 되돌리려면 이 커밋 하나를 되돌리면 된다.
 */
const SUMMARY_SEPARATOR = '／';

function summarySegments(summary: string): string[] {
  return summary
    .split(SUMMARY_SEPARATOR)
    .map((s) => s.trim())
    .filter((s) => s.length > 0);
}

export function DetailHeader(props: {
  detail: DatasetDetail;
  approvalSource: ApprovalSource;
  onChanged?: (() => void) | undefined;
  /**
   * ⭑ **WU-A3 이 낸 자리** — 상세 수정 진입점(`DatasetEditEntry`). 권한이 꺼졌으면 그 컴포넌트가
   * 스스로 `null` 이 되므로 여기는 조건을 알지 못한다 (P-12 · 판정은 한 곳에서만).
   * 뒤 WU 가 진입점을 늘리더라도 헤더는 이 슬롯 하나만 안다.
   */
  editAction?: React.ReactNode;
}) {
  const d = props.detail;
  const segments = d.summary ? summarySegments(d.summary) : [];
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
            {segments.length > 1 ? (
              <>
                <p className="dh-sum-lead" data-testid="dh-sum-lead">
                  {segments[0]}
                </p>
                <ul className="dh-sum-list" data-testid="dh-sum-list">
                  {segments.slice(1).map((seg) => (
                    <li key={seg}>{seg}</li>
                  ))}
                </ul>
              </>
            ) : (
              d.summary
            )}
          </div>
        ) : null}
        <div className="dh-tags" data-testid="dh-tags">
          {d.topic ? <span className="chip chip--neutral">{d.topic}</span> : null}
          <span className={`lvl lvl-${Math.min(d.processingLevel, 3)}`}>
            Lv{d.processingLevel}
          </span>
          {/* 잠긴 상세도 헤더 태그까지는 보인다 (`§3.3` · P-13) */}
          {d.accessState === '잠김' ? <span className="chip chip--warning">잠김</span> : null}
          {/* Verified 배지 — **표시 전용**이다 (`§8` · `Policy_승인_처리 §1.5`).
              ⭑ WU-P6 이 자리(`VerifiedBadgeSlot`)를 실물로 갈아 끼웠다. */}
          <VerifiedBadge verified={props.detail.verification.verified} />
        </div>
      </div>
      {/* 헤더 우측 **한 자리**가 상태 × 보는 사람에 따라 셋으로 갈린다
          (승인 요청 / 승인 / 승인 취소). 규칙은 `Policy_승인_처리 §8` 이 정본이다.
          ⭑ WU-P6 이 채웠다 — 판정은 서버의 `actions` 세 칸이 한다 (P-7). */}
      {/* ⭑ WU-A3 — 수정 진입점. 승인 자리와 **다른 판정**이라 다른 슬롯에 선다
          (승인은 서버 `actions` 세 칸 · 수정은 `업로드·편집` 스위치). */}
      {props.editAction ? (
        <div className="dh-edit" data-slot="dataset-edit-entry">
          {props.editAction}
        </div>
      ) : null}
      <VerificationAction
        detail={props.detail}
        source={props.approvalSource}
        onChanged={props.onChanged}
      />
    </div>
  );
}
