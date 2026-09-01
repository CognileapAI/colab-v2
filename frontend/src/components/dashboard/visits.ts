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

/**
 * 시점 표기 — 목업이 쓰는 상대 시각이다 (`홈_대시보드_260817.html` 축자 「어제」·「3일 전」).
 * 절대 날짜를 쓰면 「언제 일인가」를 사람이 매번 계산해야 한다.
 */
export function relativeTime(iso: string, now: Date = new Date()): string {
  const days = Math.floor((now.getTime() - new Date(iso).getTime()) / 86_400_000);
  if (days <= 0) return '오늘';
  if (days === 1) return '어제';
  return `${days}일 전`;
}
