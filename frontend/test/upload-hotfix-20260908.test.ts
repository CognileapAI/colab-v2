/**
 * X-9 · 업로드 마법사 핫픽스 4건 — CSS 원문 ＋ 순수 함수 계측 시험.
 *
 * 오라클 = `dev-package/reports/R-D/upload-step3-overlap-20260908.md` §1 · §2-(c) · §3-(2) · §3-(3).
 * 화면을 그리지 않고 원문을 읽어 잰다 — jsdom 은 스타일을 계산하지 않는다
 * (`design-fix-20260908.test.ts` · `css-residual-rc11.test.ts` 와 같은 규율).
 *
 *   F4 ㈎ 등록 카드 4장(`card is-on`)이 `.card-b` gap 규칙을 받는다 ＋ ③ 두 카드 사이 gap
 *   F3 ㈏ `데이터셋 이름` 라벨에 `필수` 배지가 있다 (강제는 이미 `UploadModal.submit()`)
 *   F1 ㈐ 기간 역전 판정이 순수 함수 하나로 서 있다 ＋ 문면은 서버 축자 재사용
 *   F2 ㈑ 서버 오류가 `{step, message}` 로 갈무리되고 다른 단계에 새지 않는다
 */
// @ts-expect-error — 타입 선언 없이 런타임만 쓴다(vitest 는 node 위에서 돈다).
import { readFileSync } from 'node:fs';
// @ts-expect-error — 같은 이유.
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';
import { PERIOD_INVERTED_MESSAGE, isPeriodInverted } from '../src/components/upload/periodParts';
import { clearedOnStepChange, messageForStep } from '../src/components/upload/registerError';

declare const process: { cwd(): string };

/** 주석은 걷어내고 읽는다 — 선언만 잰다. */
const read = (rel: string): string =>
  String(readFileSync(resolve(process.cwd(), rel), 'utf8')).replace(/\/\*[\s\S]*?\*\//g, '');

const UPLOAD_CSS = read('src/components/upload/upload.css');
/** TSX 는 주석 제거 없이 원문 그대로 읽는다 — 겨누는 것이 선언이 아니라 마크업이다. */
const REGISTER_TSX = String(
  readFileSync(resolve(process.cwd(), 'src/components/upload/RegisterArea.tsx'), 'utf8'),
);

/** 어떤 선택자를 담고 있는 규칙 하나 — 선택자 목록과 선언 블록을 함께 돌려준다. */
function rule(css: string, needle: string): { selectors: string; body: string } {
  const at = css.indexOf(needle);
  expect(at, `선택자 부재: ${needle}`).toBeGreaterThan(-1);
  const open = css.indexOf('{', at);
  const close = css.indexOf('}', open);
  const prev = css.lastIndexOf('}', at);
  return {
    selectors: css.slice(prev + 1, open).trim(),
    body: css.slice(open + 1, close),
  };
}

describe('F4 ㈎ 등록 카드 여백 — `card is-on` 이 컨테이너 gap 을 받는다', () => {
  it('`.card-b` 세로 gap 규칙의 선택자가 `card is-on` 카드를 덮는다', () => {
    const gap = rule(UPLOAD_CSS, '.up-card > .card-b');
    // 등록 카드 4장은 `class="card is-on"` 이다(reg-s1 · reg-s2 · reg-projects · ③).
    expect(gap.selectors).toContain('.card.is-on > .card-b');
    // 값은 종전 그대로 재사용한다 — 새 치수 리터럴을 만들지 않는다.
    expect(gap.body.replace(/\s/g, '')).toContain('gap:12px');
  });

  it('③ 을 감싸는 `reg-s3` 도 세로 gap 을 진다 — 두 카드가 경계선으로 붙지 않는다', () => {
    const gap = rule(UPLOAD_CSS, '[data-testid="reg-s3"]');
    expect(gap.body.replace(/\s/g, '')).toContain('flex-direction:column');
    expect(gap.body.replace(/\s/g, '')).toContain('gap:16px');
  });

  it('등록 카드 4장이 여전히 `card is-on` 이다 — 시험이 겨누는 자리가 바뀌지 않았다', () => {
    expect(REGISTER_TSX.match(/className="card is-on"/g)?.length).toBe(4);
  });
});

describe('F3 ㈏ 필수 배지 ↔ 실제 강제', () => {
  it('`데이터셋 이름` 라벨에 `필수` 배지가 있다', () => {
    const at = REGISTER_TSX.indexOf('htmlFor="reg-name"');
    expect(at, '`reg-name` 라벨 부재').toBeGreaterThan(-1);
    const label = REGISTER_TSX.slice(at, REGISTER_TSX.indexOf('</label>', at));
    expect(label).toContain('<span className="reqtag">필수</span>');
  });

  it('`설명` 배지와 **같은 것**을 쓴다 — 두 벌을 만들지 않는다', () => {
    expect(REGISTER_TSX.match(/<span className="reqtag">필수<\/span>/g)?.length).toBeGreaterThan(1);
  });
});

describe('F1 ㈐ 기간 역전 — 클라이언트 선검사', () => {
  it('종료가 시작보다 앞서면 역전이다', () => {
    expect(isPeriodInverted('2026-09-19', '2026-09-13')).toBe(true);
  });

  it('같은 날짜는 역전이 아니다 — 시작=끝은 한 점의 기간이다(PRD-40 판정 ⓐ)', () => {
    expect(isPeriodInverted('2026-09-13', '2026-09-13')).toBe(false);
  });

  it('정상 순서는 역전이 아니다', () => {
    expect(isPeriodInverted('2026-09-13', '2026-09-19')).toBe(false);
  });

  it('한쪽이 비면 다투지 않는다 — 종료는 비울 수 있다', () => {
    expect(isPeriodInverted('2026-09-19', null)).toBe(false);
    expect(isPeriodInverted(null, '2026-09-19')).toBe(false);
    expect(isPeriodInverted('', '')).toBe(false);
  });

  it('조립된 시각값(`assemble` 산출)도 같은 판정이다 — 자리 수가 달라도 섞이지 않는다', () => {
    expect(isPeriodInverted('2026-09-19T00:00:00Z', '2026-09-13T23:59:59Z')).toBe(true);
    expect(isPeriodInverted('2026-09-13T00:00:00Z', '2026-09-13')).toBe(false);
  });

  it('문면은 서버 축자 그대로다 — 화면이 두 번째 문장을 만들지 않는다', () => {
    expect(PERIOD_INVERTED_MESSAGE).toBe('기간의 종료는 시작보다 앞설 수 없다.');
  });

  it('기간 칸이 그 문면을 자기 옆에 낸다 — 바닥 배너만으로 끝내지 않는다', () => {
    expect(REGISTER_TSX).toContain('data-testid="reg-period-error"');
  });
});

describe('F2 ㈑ 서버 오류의 단계 범위', () => {
  const step2 = { step: 2 as const, message: '기간의 종료는 시작보다 앞설 수 없다.' };

  it('② 에서 난 문면은 ② 에서만 보인다', () => {
    expect(messageForStep(step2, 2)).toBe(step2.message);
  });

  it('③ 은 ② 의 문면을 절대 보이지 않는다', () => {
    expect(messageForStep(step2, 3)).toBeNull();
    expect(messageForStep(step2, 1)).toBeNull();
  });

  it('단계를 옮기면 지워진다', () => {
    expect(clearedOnStepChange(step2, 3)).toBeNull();
    expect(clearedOnStepChange(step2, 2)).toEqual(step2);
  });

  it('단계와 무관한 파일·접수 오류(`step: null`)는 어느 단계에서도 보인다', () => {
    const anyStep = { step: null, message: '이 파일은 더 이상 없어요. 다시 올려 주세요.' };
    expect(messageForStep(anyStep, 1)).toBe(anyStep.message);
    expect(messageForStep(anyStep, 3)).toBe(anyStep.message);
    expect(clearedOnStepChange(anyStep, 3)).toEqual(anyStep);
  });

  it('오류가 없으면 어느 단계에서도 비어 있다', () => {
    expect(messageForStep(null, 2)).toBeNull();
    expect(clearedOnStepChange(null, 2)).toBeNull();
  });
});
