// 화면 문면의 **한 자리** — PRD-43 「공통 토스트 한 개와 문면 21행」.
//
// 왜 한 곳인가: 같은 문장을 두 벌 적으면 한쪽만 고쳐지는 날이 온다. PRD-43 수용 기준이
// 「21행이 전부 코드에 있고 **하드코드 중복이 0건**이다(한 곳에서 온다)」인 이유다.
// 시험 `test/toast-copy-20260906.test.tsx` 가 `src/` 전체를 훑어 그 0건을 실측한다.
//
// ⛔ **문면을 고쳐 적지 않는다.** 축자 원천은 PRD-43 표이고, 표가 `…` 로 줄인 행(`S-04`)과
//    표가 종류만 적은 행(`E-07` 「편집 토스트 3종」)은 그 표가 가리키는 rev2 원문에서 떴다.
//    다르게 적을 사유를 찾으면 고치지 말고 보고한다 (`rounds/R-A2.md §1`).
//
// ⚠ **이 파일은 문면만 갖는다.** 각 문면을 화면 어느 자리에서 부르는지는 **그 자리를 담는
//    WU** 가 정한다(라운드 파일 §2-① 축자). 여기서 화면을 바꾸지 않는다.

/* ── U-14 · 업로드 장면1 — 분석 상태 칩 ─────────────────────────────── */
export const ANALYZING_CHIP = '분석 중';
export const ANALYZED_CHIP = '분석 완료';

/* ── `#24` ㉯ · Ted 판정 ⑧ — 같은 장면(업로드 장면1)의 두 문면.
   **2026-09-12 Ted 확정 · PRD-34/43 개정 〈386〉.** ────────────────────────
   PRD-43 표 21행에는 대응 행이 없어 `COPY_ROW_IDS`·`COPY_ROWS`·`FIXED_COPY` 에
   등재하지 않는다 — 등재하면 확정되지 않은 문면이 그 표에 든다. 자리표 등재는
   문면표 개정 뒤다. 문면의 자리가 이 모듈 하나인 규약은 그대로 지킨다. */
// 문면 확정 2026-09-12 · PRD-34/43 개정 〈386〉
/** `다음 →`(`reg-open`)이 비활성인 이유. 분석 미완 갈래에서만 선다. */
export const REG_OPEN_ANALYZING_REASON = '분석이 끝나면 다음으로 갈 수 있어요.';
// 문면 확정 2026-09-12 · PRD-34/43 개정 〈386〉
/**
 * 분석 중 경과 시간. **클라이언트 벽시계**다 — 상태 응답에 진행 수치가 없어
 * 조각 수 진행률을 적지 않는다(없는 것을 퍼센트로 지어내지 않는다).
 */
export function analyzeElapsed(seconds: number): string {
  return `${seconds}초 경과`;
}

/* ── U-17 · 업로드 장면1 ────────────────────────────────────────────── */
export const UPLOAD_DONE = '파일을 올렸어요. 등록을 시작할 수 있어요';

/* ── P-06 · 미리보기 ────────────────────────────────────────────────── */
export const PREVIEW_DREW_ONE = '파일에서 바로 한 장을 그렸어요';

/* ── P-07 · 업로드 미리보기 푸터 ─────────────────────────────────────── */
export const UPLOAD_PREVIEW_FOOT =
  '첫 변수를 미리 그렸어요 · 확장보기(⤢)에서 확대하고 좌표를 읽을 수 있어요';

/* ── V-01 · 뷰어 머리 ＋ 힌트 ────────────────────────────────────────── */
/**
 * 뷰어 머리는 **좌표계 값이 앞에 붙는다** — rev2 원문도 `d.meta.crs + ' · PNG + 경계 좌표'` 다.
 * 좌표계는 데이터셋마다 다르므로 고정 문자열로 적으면 남의 좌표계를 그리게 된다.
 */
export const VIEWER_HEAD_SUFFIX = ' · PNG + 경계 좌표';
export function viewerHead(crs: string): string {
  return `${crs}${VIEWER_HEAD_SUFFIX}`;
}
export const VIEWER_HINT = '휠로 확대하고 끌어서 움직여요';

/* ── B-10 · 등록 ② 기간 ─────────────────────────────────────────────── */
export const PERIOD_CLEARED = '기간을 지웠어요';
export const PERIOD_START_NEEDED = '시작할 날을 골라 주세요';

/* ── B-32 · 등록 ② 대표 그림 ────────────────────────────────────────── */
export const THUMB_REPLACED = '직접 올린 그림으로 바꿨어요';
export const THUMB_RESTORED = '자동 생성본으로 되돌렸어요';

/* ── L-08 · L-11 · L-14 · 등록 ③ 계보 ───────────────────────────────── */
export const LINK_REMOVED = '연결을 지웠어요';
export const LINK_ADDED = '직접 연결했어요. 계보에 들어가요';
export const UNRECORDED_ON = '기록 없음으로 표시했어요';
export const UNRECORDED_OFF = '기록 없음 표시를 지웠어요';

/* ── J-08 · J-12 · 등록 ③ 프로젝트 ──────────────────────────────────── */
export const PROJECT_UNPICKED = '프로젝트 지정을 뺐어요';
export const QUICK_PROJECT_NOTE = '유형과 이름만 받아요. 나머지는 프로젝트 화면에서 채워요.';

/* ── F-11 · 행동 줄 ─────────────────────────────────────────────────── */
/** 계보 건수는 **보간값**이다 — 고정 숫자로 적으면 0건인 사람에게도 숫자가 보인다. */
export function datasetCreated(lineageCount: number): string {
  return `데이터셋을 만들었어요 (계보 연결 ${lineageCount}건). 상세 화면으로 넘어가요`;
}

/* ── S-04 · S-05 · 찾기 모달 ────────────────────────────────────────── */
/** PRD-43 표가 `…` 로 줄인 행. 축자는 rev2 원문(`toast('…')`)에서 떴다. */
export const STAGE_TOO_HIGH =
  '이 데이터보다 높은 단계라 연결할 수 없어요. 분류에서 가공 단계를 확인해 주세요';
export const PICK_TARGET_FIRST = '연결할 데이터를 먼저 골라 주세요';

/* ── X-05 · 계보 수정 모달 ──────────────────────────────────────────── */
/** `S-05` 와 **같은 문면**이다. 표에 행이 둘이라고 문자열을 둘 적지 않는다. */
export const PICK_TARGET_FIRST_IN_EDIT = PICK_TARGET_FIRST;

/* ── D-01 · D-07 · D-13 · N-11 · 상세 ───────────────────────────────── */
export const BACK_TO_ORIGIN = '들어온 곳으로 돌아가요. 필터와 스크롤 위치는 그대로예요';
/**
 * `D-07` 기간 축약은 **문면이 아니라 표기 규칙**이라 조립 자리가 따로 있다 —
 * `detail/format.ts` 의 `formatPeriod`. 여기 다시 구현하면 두 벌이 된다.
 */
export const PERIOD_ABBREV_EXAMPLE = '2025-06 ~ 09';
/** 본체 건수는 **보간값**이다 (`D-13`). */
export function bodyPieceHead(bodyCount: number): string {
  return `본체 ${bodyCount}개 · 같은 데이터를 월로 자른 조각이에요`;
}
export const LINEAGE_GRAPH_HINT = '각 데이터를 누르면 그 상세로 가요';

/* ── E-07 · 상세 편집 토스트 3종 ────────────────────────────────────── */
export const EDIT_MODE_ON = '편집 모드예요. 값을 고치고 저장을 누르세요';
export const EDIT_SAVED = '편집 내용을 저장했어요';
export const EDIT_CANCELED = '편집을 취소했어요';

/* ── PRD-16 — 변수 표 (21행 밖) ──────────────────────────────────────── */
/**
 * ⭑ **⟨WU-B2 · PRD-16⟩ 마지막 변수 행 삭제 차단 문면.** rev1 축자 그대로다.
 * **PRD-43 표의 21행이 아니다** — 그 표는 R-A 회차의 문면 목록이고 이 문장은 이번 회차가
 * 처음 세운다. 그래서 `COPY_ROWS`·`FIXED_COPY` 에 넣지 않는다(21 이라는 계수가 그 표의
 * 오라클이다). 같은 문장을 **서버도 400 문면으로 쓴다** — 그쪽 자리는
 * `routes/catalog.py` 의 `AT_LEAST_ONE_VARIABLE` 이고, 층이 달라 한 파일에 못 모은다.
 */
export const AT_LEAST_ONE_VARIABLE = '변수는 하나 이상 있어야 해요';

/**
 * ⭑ **⟨advisor ② F1 · WU-B6⟩ 내려받은 날 형상 오류.** 서버 400 문면과 **같은 문장**이다
 * (`services/core-api/src/colab_core/app/routes/catalog.py:885`). 화면이 다르게 적으면
 * 같은 오류가 두 문구로 보인다 — 저작 금지, 이 상수를 그대로 재사용한다.
 * ⛔ PRD-43 표의 21행이 아니다(`AT_LEAST_ONE_VARIABLE` 과 같은 사유) — `FIXED_COPY` 에 넣지 않는다.
 */
export const SOURCE_DOWNLOADED_ON_INVALID = '내려받은 날은 날짜(YYYY-MM-DD)다.';

/**
 * `SOURCE_DOWNLOADED_ON_INVALID` 판정 함수. 서버 `_is_date`(advisor ② F3)와 같은 형상만
 * 통과시킨다 — `^\d{4}-\d{2}-\d{2}$` ∧ 유효한 달력 날짜. 등록·수정 두 자리가 이 하나를 쓴다.
 */
const SOURCE_DOWNLOADED_ON_SHAPE = /^(\d{4})-(\d{2})-(\d{2})$/;
export function isValidSourceDownloadedOnShape(value: string): boolean {
  const match = SOURCE_DOWNLOADED_ON_SHAPE.exec(value);
  if (!match) return false;
  const y = Number(match[1]);
  const m = Number(match[2]);
  const d = Number(match[3]);
  const parsed = new Date(Date.UTC(y, m - 1, d));
  return (
    parsed.getUTCFullYear() === y && parsed.getUTCMonth() === m - 1 && parsed.getUTCDate() === d
  );
}

/* ── PRD-32 · PRD-31 — 표에 다시 적지 않는 축자 2건 ─────────────────── */
// PRD-43 축자 — 「이미 요구로 서 있는 토스트 축자 2건은 여기 다시 적지 않는다 …
// **같은 컴포넌트를 쓴다**」. 21행에 세지 않지만 같은 자리에서 온다.
/** 확장자 혼합 안내 — rev1 `H-37` 축자. 한 글자도 바꾸지 않는다 (PRD-32). */
export const MIXED_EXTENSION_NOTICE = '확장자가 다른 파일은 뺐어요. 한 번에 한 종류만 묶어요';
/** 상세 계보 모달에서 부모를 더했을 때 — rev1 `H-46` 축자 (PRD-31). 담는 WU 가 여기서 부른다. */
export const PRE_LINEAGE_ADDED = '가공 전 데이터를 추가했어요. 직접 연결로 남아요';
/** 업로드 장면1 파일 빼기 고지 — rev1 `removeFile()` 축자 (PRD-39 ③). */
export const FILE_REMOVED_NOTICE = '파일을 뺐어요. 입력하던 내용은 사라져요';

/* ── PRD-34 · PRD-14 · 업로드 종료 확인 모달 (WU-A9R) ───────────────── */
// PRD-43 표의 21행은 아니다. 그래도 문면의 자리는 **여기 하나**다 — 화면에 다시 적으면
// 같은 문장이 두 벌이 되고, 그것이 PRD-43 「한 곳」이 막으려던 바로 그 상태다.
// ⛔ 축자 원천 = rev2 원문 `10_적용전/업로드_계보_260905_rev2_이태헌.html` 의
//    `closeUpload()`(본문 3종) · 확인 모달 마크업(제목·버튼). 개발 세션이 새로 짓지 않는다.

/** 확인 모달 제목 — 상황이 셋이어도 제목은 하나다 (PRD-34). */
export const UPLOAD_CLOSE_TITLE = '업로드를 닫을까요?';
/** 왼쪽 버튼. 종전 `계속 작성` 을 rev2 축자 `계속하기` 로 바꾼다 (PRD-34). */
export const UPLOAD_CLOSE_KEEP = '계속하기';
/** 오른쪽 버튼. rev2 축자 그대로 유지. */
export const UPLOAD_CLOSE_LEAVE = '닫고 나가기';

/* ── `#34` 세 번째 선택지 — **2026-09-12 Ted 확정 · PRD-34/43 개정 〈386〉.** ──
   rev2 원문에 대응 문장이 없어 개발 세션이 적었고, 2026-09-12 Ted 확정 · PRD-34/43
   개정 〈386〉 으로 문면이 확정됐다. 자리표 2행 신설 전까지는 PRD-43 표
   (`COPY_ROW_IDS`·`COPY_ROWS`·`FIXED_COPY`)에 등재하지 않는다 — 등재하면 21행 표가
   확정되지 않은 문면을 담는다.
   뜻 = **이 브라우저의 미완결 기억 삭제**. 서버 접수 행은 24시간 만료 스윕이 정리한다. */
// 문면 확정 2026-09-12 · PRD-34/43 개정 〈386〉
export const UPLOAD_CLOSE_FORGET = '이 브라우저에서 감추기';
// 문면 확정 2026-09-12 · PRD-34/43 개정 〈386〉
export const UPLOAD_CLOSE_FORGET_NOTE =
  '이 브라우저에서 감추면 올리다 만 기록이 이 브라우저에서만 사라져요. 서버에 접수된 것은 24시간 뒤 저절로 정리돼요.';

/** 데이터셋 생성 요청을 보낸 뒤 응답을 기다리는 동안. 서버 요청 자체는 닫기로 취소되지 않는다. */
export const UPLOAD_CLOSE_CREATING = '저장 요청은 이미 서버로 갔어요. 지금 닫아도 요청을 취소할 수 없어 데이터셋과 입력한 내용이 남을 수 있어요.';
/** 데이터셋 생성이 끝난 뒤 대표 그림 PUT을 기다리거나 그 실패를 복구하는 동안. */
export const UPLOAD_CLOSE_CREATED = '데이터셋과 연결한 계보는 이미 저장됐어요. 지금 닫아도 대표 그림 저장 요청의 결과가 남을 수 있어요.';

/** ⑴ 파일만 — 사람 입력 0 · 확정 계보 0. */
export const UPLOAD_CLOSE_FILE_ONLY = '올린 파일이 취소돼요. 원본 파일은 그대로라 다시 올리면 돼요.';
/** ⑵ 입력 있음 — 사람 입력 ≥1 · 확정 계보 0. */
export const UPLOAD_CLOSE_INPUT_ONLY = '적은 내용이 사라지고, 데이터셋은 만들어지지 않아요. 원본 파일은 그대로예요.';
/**
 * ⑶ 입력＋계보 — 사람 입력 ≥1 · 확정 계보 ≥1. 건수는 **보간값**이다.
 * 고정 숫자로 적으면 1건인 사람에게도 남의 건수가 보인다 (PRD-34 수용 기준).
 */
export function uploadCloseWithLineage(lineageCount: number): string {
  return `적은 내용과 연결한 계보 ${lineageCount}건이 사라지고, 데이터셋은 만들어지지 않아요. 원본 파일은 그대로예요.`;
}

/**
 * 상황 → 본문. 판정 기준은 PRD-34 표 그대로다 — 사람 입력 유무와 **확정된** 계보 건수.
 * 화면이 if 를 세 겹 쓰지 않게 갈래를 여기서 닫는다.
 */
export function uploadCloseMessage(state: {
  hasHumanInput: boolean;
  lineageCount: number;
  saveState?: 'pre-create' | 'creating' | 'created';
}): string {
  if (state.saveState === 'creating') return UPLOAD_CLOSE_CREATING;
  if (state.saveState === 'created') return UPLOAD_CLOSE_CREATED;
  if (!state.hasHumanInput) return UPLOAD_CLOSE_FILE_ONLY;
  return state.lineageCount > 0
    ? uploadCloseWithLineage(state.lineageCount)
    : UPLOAD_CLOSE_INPUT_ONLY;
}

/* ── PRD-43 표 그 자체 ──────────────────────────────────────────────── */

/** PRD-43 표의 행 id. **순서도 표 그대로**다. */
export const COPY_ROW_IDS = [
  'U-14', 'U-17', 'P-06', 'P-07', 'V-01', 'B-10', 'B-32',
  'L-08', 'L-11', 'L-14', 'J-08', 'J-12', 'F-11',
  'S-04', 'S-05', 'X-05', 'D-01', 'D-07', 'D-13', 'N-11', 'E-07',
] as const;

export type CopyRowId = (typeof COPY_ROW_IDS)[number];

export type CopyRow = {
  /** PRD-43 표의 「자리」 열. */
  place: string;
  /**
   * 그 행이 내보내는 문면 전부. 보간행(`F-11`·`D-13`·`V-01`)은 **예시 인자로 만든 값**이라
   * 화면이 이 배열을 그리지 않는다 — 화면은 위 상수·함수를 부른다. 이 배열은 「21행이
   * 전부 있는가」를 시험이 셀 수 있게 두는 목록이다.
   */
  texts: readonly string[];
};

/**
 * ⚠ **문자열을 여기 다시 적지 않는다** — 위 상수를 참조한다. 다시 적으면 이 파일 안에서만
 * 두 벌이 되고, 「한 곳에서 온다」가 파일 경계로만 성립하는 거짓이 된다.
 */
export const COPY_ROWS: Readonly<Record<CopyRowId, CopyRow>> = {
  'U-14': { place: '업로드 장면1 · 분석 상태 칩', texts: [ANALYZING_CHIP, ANALYZED_CHIP] },
  'U-17': { place: '업로드 장면1', texts: [UPLOAD_DONE] },
  'P-06': { place: '미리보기', texts: [PREVIEW_DREW_ONE] },
  'P-07': { place: '업로드 미리보기 푸터', texts: [UPLOAD_PREVIEW_FOOT] },
  'V-01': { place: '뷰어 머리 ＋ 힌트', texts: [viewerHead('EPSG:5179'), VIEWER_HINT] },
  'B-10': { place: '등록 ② 기간', texts: [PERIOD_CLEARED, PERIOD_START_NEEDED] },
  'B-32': { place: '등록 ② 대표 그림', texts: [THUMB_REPLACED, THUMB_RESTORED] },
  'L-08': { place: '등록 ③ 계보', texts: [LINK_REMOVED] },
  'L-11': { place: '등록 ③ 계보', texts: [LINK_ADDED] },
  'L-14': { place: '등록 ③ 계보', texts: [UNRECORDED_ON, UNRECORDED_OFF] },
  'J-08': { place: '등록 ③ 프로젝트', texts: [PROJECT_UNPICKED] },
  'J-12': { place: '등록 ③ 프로젝트 · 빠른 생성 안내', texts: [QUICK_PROJECT_NOTE] },
  'F-11': { place: '행동 줄', texts: [datasetCreated(3)] },
  'S-04': { place: '찾기 모달', texts: [STAGE_TOO_HIGH] },
  'S-05': { place: '찾기 모달', texts: [PICK_TARGET_FIRST] },
  'X-05': { place: '계보 수정 모달', texts: [PICK_TARGET_FIRST_IN_EDIT] },
  'D-01': { place: '상세 · 돌아가기', texts: [BACK_TO_ORIGIN] },
  'D-07': { place: '상세 · 기간 축약 표기', texts: [PERIOD_ABBREV_EXAMPLE] },
  'D-13': { place: '상세 · 파일 목록 머리', texts: [bodyPieceHead(4)] },
  'N-11': { place: '상세 · 계보 그래프 머리 힌트', texts: [LINEAGE_GRAPH_HINT] },
  'E-07': { place: '상세 편집 · 편집 토스트 3종', texts: [EDIT_MODE_ON, EDIT_SAVED, EDIT_CANCELED] },
};

/**
 * 보간이 없는 **고정 문면** 전부 — 「하드코드 중복 0건」 시험의 대상 목록이다.
 * 보간행(`F-11`·`D-13`·`V-01` 머리·`D-07` 예시)은 값이 인자에 따라 달라 문자열 검색의
 * 대상이 아니다. `V-01` 은 고정 꼬리(`VIEWER_HEAD_SUFFIX`)만 센다.
 */
export const FIXED_COPY: readonly string[] = [
  ANALYZING_CHIP, ANALYZED_CHIP, UPLOAD_DONE, PREVIEW_DREW_ONE, UPLOAD_PREVIEW_FOOT,
  VIEWER_HEAD_SUFFIX, VIEWER_HINT, PERIOD_CLEARED, PERIOD_START_NEEDED,
  THUMB_REPLACED, THUMB_RESTORED, LINK_REMOVED, LINK_ADDED, UNRECORDED_ON, UNRECORDED_OFF,
  PROJECT_UNPICKED, QUICK_PROJECT_NOTE, STAGE_TOO_HIGH, PICK_TARGET_FIRST, BACK_TO_ORIGIN,
  LINEAGE_GRAPH_HINT, EDIT_MODE_ON, EDIT_SAVED, EDIT_CANCELED,
  MIXED_EXTENSION_NOTICE, PRE_LINEAGE_ADDED, FILE_REMOVED_NOTICE,
  UPLOAD_CLOSE_TITLE, UPLOAD_CLOSE_KEEP, UPLOAD_CLOSE_LEAVE,
  UPLOAD_CLOSE_CREATING, UPLOAD_CLOSE_CREATED,
  UPLOAD_CLOSE_FILE_ONLY, UPLOAD_CLOSE_INPUT_ONLY,
];
