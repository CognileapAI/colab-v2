/**
 * 오라클 — 파일명·경로 정규화가 **서버와 한 글자도 다르지 않다**.
 *
 * 벡터는 `services/core-api/tests/test_objectpath.py` 의 것을 **그대로** 옮겼다.
 * 서버 `kernel/objectpath.py` 머리말이 「규칙은 프론트 `normalizeName.ts` 와 한 글자도
 * 다르면 안 된다 — 양쪽 테스트가 같은 벡터를 쓴다」고 요구한다. 그 짝이 없어서
 * 한글 파일명 업로드가 dev 에서 통째로 막혔다(2026-09-02).
 *
 * ⚠ 한 쪽 규칙을 바꾸면 **양쪽 파일과 양쪽 시험을 함께** 고친다.
 */
import { describe, expect, it } from 'vitest';
import { normalizeName } from '../src/components/upload/normalizeName';

describe('normalizeName — 서버 objectpath 와 같은 규칙', () => {
  it('규칙 1 · 백슬래시가 슬래시가 된다', () => {
    expect(normalizeName('data\\geo\\points.csv')).toBe('data/geo/points.csv');
  });

  it('규칙 2 · NFD 입력이 NFC 가 된다 — 이 모듈의 존재 이유', () => {
    const nfd = '실험/데이터 1.csv'.normalize('NFD');   // macOS 가 주는 형태
    const nfc = '실험/데이터 1.csv'.normalize('NFC');   // Windows 가 주는 형태
    expect(nfd).not.toBe(nfc);                          // 실제로 바이트가 다르다
    expect(normalizeName(nfd)).toBe(nfc);
    expect(normalizeName(nfc)).toBe(nfc);
  });

  it('규칙 2b · 실제로 터졌던 이름 — 「자료설명.pptx」', () => {
    expect(normalizeName('자료설명.pptx'.normalize('NFD')))
      .toBe('자료설명.pptx'.normalize('NFC'));
  });

  it('규칙 3 · 빈 세그먼트·`.`·`..` 가 빠진다', () => {
    expect(normalizeName('./a//b/../c.csv')).toBe('a/b/c.csv');
    expect(normalizeName('../../etc/passwd')).toBe('etc/passwd');
  });

  it('규칙 4 · 제어문자가 빠진다', () => {
    expect(normalizeName('a\x00b/c\x1f\x7fd.csv')).toBe('ab/cd.csv');
  });

  it('규칙 5 · 세그먼트 앞뒤의 공백·마침표만 다듬는다 — 가운데는 보존', () => {
    expect(normalizeName(' data. / report. .csv')).toBe('data/report. .csv');
    expect(normalizeName('data ./ x.csv ')).toBe('data/x.csv');
    expect(normalizeName('a/ .. /b.csv')).toBe('a/b.csv');
  });

  it('규칙 6 · 아무것도 안 남으면 **원본을 그대로** 돌려준다 — 판정은 서버가 한다', () => {
    // 서버는 여기서 ValueError 를 내고 그 사유가 `rejected[].reason` 으로 화면에 오른다.
    // 프론트가 먼저 던지면 서버의 구체적 사유 대신 프론트의 짐작이 보인다.
    for (const raw of ['', '/', '..', './..', ' . ', '\\', '\x00']) {
      expect(normalizeName(raw)).toBe(raw);
    }
  });
});
