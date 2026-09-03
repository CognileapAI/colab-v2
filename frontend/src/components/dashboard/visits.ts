// 「내가 열어 본 것」 — **브라우저에만 둔다** (`Policy_홈_대시보드 §10` 축자 · 2026-08-07 인터뷰).
//
// 서버에 보내는 경로가 이 파일에 **없는 것**이 그 조항의 실물이다. 계약에도 열람을 받는
// op 이 없고 `d8_activity` 에도 열람 행이 없다 — 세 층이 같은 말을 한다.
//
// 저장 실패를 삼킨다. 사생활 모드·용량 초과에서 `localStorage` 는 던지는데, 그 예외로
// 홈이 죽으면 **부수 기능이 본 기능을 잡아먹는다.**
const KEY = 'colab.v2.visits';
const LIMIT = 10;

export type Visit = {
  kind: '데이터셋' | '프로젝트';
  id: string;
  name: string;
  /** ISO 8601. 서버 활동과 **같은 눈금**이라야 한 목록으로 섞인다. */
  at: string;
};

export function readVisits(): Visit[] {
  try {
    const raw = globalThis.localStorage?.getItem(KEY);
    const parsed: unknown = raw ? JSON.parse(raw) : [];
    if (!Array.isArray(parsed)) return [];
    return parsed.filter(
      (v): v is Visit =>
        !!v && typeof v.id === 'string' && typeof v.name === 'string' && typeof v.at === 'string',
    );
  } catch {
    return [];
  }
}

/** 같은 것을 다시 열면 시점만 올린다 — 같은 이름이 목록에 두 줄로 서지 않는다. */
export function recordVisit(visit: Omit<Visit, 'at'>, now: string = new Date().toISOString()): void {
  try {
    const rest = readVisits().filter((v) => !(v.kind === visit.kind && v.id === visit.id));
    const next = [{ ...visit, at: now }, ...rest].slice(0, LIMIT);
    globalThis.localStorage?.setItem(KEY, JSON.stringify(next));
  } catch {
    // 열람 기록은 부수 기능이다. 못 적어도 화면은 그대로 돈다.
  }
}

/** 그 시각이 속한 **그 지역 달력 날짜**의 0시. 사람이 「오늘」이라고 부르는 것의 시작이다. */
function startOfLocalDay(d: Date): number {
  return new Date(d.getFullYear(), d.getMonth(), d.getDate()).getTime();
}

/**
 * 시점 표기 — 목업이 쓰는 상대 시각이다 (`홈_대시보드_260817.html` 축자 「어제」·「3일 전」).
 * 절대 날짜를 쓰면 「언제 일인가」를 사람이 매번 계산해야 한다.
 *
 * ⭑ **2026-09-03 개정 — 24시간 창이 아니라 달력 날짜의 경계로 센다**
 * (`CODE-REVIEW-20260903` 부록 · 화면 소결함). 종전 계산은 지금에서 24시간을 빼는 창이라
 * **어제 23시에 연 것이 오늘 아침에 「오늘」로 보였다.** 사람이 말하는 「어제」는 시간
 * 간격이 아니라 날짜가 넘어갔느냐다.
 *
 * `Math.round` 인 이유 — 서머타임이 있는 지역에서는 하루가 23·25시간이라 `floor` 면 날짜
 * 차가 하나 어긋난다. 두 0시의 차는 언제나 하루의 정수배에 가깝다.
 */
export function relativeTime(iso: string, now: Date = new Date()): string {
  const days = Math.round((startOfLocalDay(now) - startOfLocalDay(new Date(iso))) / 86_400_000);
  if (days <= 0) return '오늘';
  if (days === 1) return '어제';
  return `${days}일 전`;
}
