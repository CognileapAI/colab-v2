// 최근 활동 — 연구실 전체의 활동과 **내가 열어 본 것**을 한 목록에 섞는다
// (`Policy_홈_대시보드 §5` · §8). 자리는 왼쪽 `우리 연구실` 구획이다.
//
// ⚠ **내 열람은 서버에 없다** (§10 축자 「열람 기록은 서버에 남기지 않는다」 · 2026-08-07
// 인터뷰). 그래서 이 컴포넌트가 브라우저 저장소에서 읽고, 그 사실을 목록 아래 한 줄로
// 밝힌다 — 기기를 바꿨을 때 목록이 달라지는 이유를 미리 알려야 한다.
import { useNavigate } from 'react-router-dom';
import { readVisits, relativeTime, type Visit } from './visits';
import type { Activity } from './types';
import type { Slot } from './useDashboard';

/** [가정] 최근 3건 (§5 · §11 — 실제 활동량을 보고 정한다고 정본이 열어 두었다). */
export const RECENT_LIMIT = 3;

/** §8 「열람 기록 안내 줄」 — 내 열람 줄이 하나도 없어도 **같은 자리에 남긴다**. */
const DEVICE_NOTE = '내가 열어 본 기록은 이 기기에만 남아요. 다른 기기에서는 연구실 활동만 보여요.';

type Line = {
  key: string;
  name: string;
  /** `호랑이가 올림` · `내가 열어 봄` — 행마다 **누가 한 일인지** 적는다 (§5). */
  who: string;
  at: string;
  path: string;
};

/**
 * 두 출처를 한 목록으로 섞어 **시점 최신순**으로 놓는다 (§5).
 * 행위자가 보는 사람 자신이면 이름 대신 `내가` 로 적는다 (§5 축자).
 */
export function mergeLines(
  activities: Activity[],
  visits: Visit[],
  myAccountId: string | null,
): Line[] {
  const fromServer: Line[] = activities.map((a) => ({
    key: `a:${a.activityId}`,
    name: a.target.name,
    who: `${a.actor.accountId === myAccountId ? '내가' : `${a.actor.name}가`} ${a.action}`,
    at: a.occurredAt,
    path: a.target.kind === '데이터셋' ? `/datasets/${a.target.id}` : `/projects/${a.target.id}`,
  }));
  const mine: Line[] = visits.map((v) => ({
    key: `v:${v.kind}:${v.id}`,
    name: v.name,
    who: '내가 열어 봄',
    at: v.at,
    path: v.kind === '데이터셋' ? `/datasets/${v.id}` : `/projects/${v.id}`,
  }));
  return [...fromServer, ...mine]
    .sort((x, y) => (x.at < y.at ? 1 : x.at > y.at ? -1 : 0))
    .slice(0, RECENT_LIMIT);
}

export function RecentActivity(props: { slot: Slot<Activity[]>; myAccountId: string | null }) {
  const navigate = useNavigate();
  const lines =
    props.slot.kind === '있음' ? mergeLines(props.slot.value, readVisits(), props.myAccountId) : [];

  return (
    <section className="dash-card" data-card="recent">
      <div className="dash-card-head">
        <h2>최근 활동</h2>
        <span className="dash-quiet-note">최근 {RECENT_LIMIT}건</span>
      </div>
      {props.slot.kind === '실패' ? (
        <p className="dash-error">최근 활동을 불러오지 못했어요.</p>
      ) : props.slot.kind !== '있음' ? (
        <p className="dash-loading">불러오는 중이에요.</p>
      ) : lines.length === 0 ? (
        // §8 「카드별 0 상태」 — 무엇이 채워질 자리인지 한 줄로 적는다.
        <p className="dash-zero">데이터나 프로젝트가 생기면 여기에 누가 무엇을 했는지 쌓여요.</p>
      ) : (
        <ul className="dash-recent">
          {lines.map((line) => (
            <li key={line.key}>
              <button type="button" onClick={() => navigate(line.path)}>
                <span className="dash-recent-name">{line.name}</span>
                <span className="dash-recent-who">{line.who}</span>
                <time dateTime={line.at}>{relativeTime(line.at)}</time>
              </button>
            </li>
          ))}
        </ul>
      )}
      {/* 구분선을 두고 한 줄. **내 열람 줄이 없어도 같은 자리에 남긴다** (§8). */}
      <p className="dash-device-note">{DEVICE_NOTE}</p>
    </section>
  );
}
