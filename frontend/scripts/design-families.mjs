// Canonical token family prefixes — one list shared by design-lint.mjs (rules a · c) and design-docs.mjs (gate h tables).
// Spec S-DESIGN-STRUCTURE-P5-20260924 (advisor ②): the two scripts used to keep their own copies.
export const CANON_FAMILIES = ['color', 'space', 'text', 'radius', 'font', 'shadow', 'leading', 'tracking', 'fg', 'bg', 'accent'];
export const COLOR_FAMILIES = ['color', 'fg', 'bg', 'accent', 'shadow'];
export const CANON_PREFIX = new RegExp(`^--(${CANON_FAMILIES.join('|')})-`);
export const COLOR_FAMILY = new RegExp(`^--(${COLOR_FAMILIES.join('|')})-`);

// Width steps and input conditions (spec S-DEVICE-WIDTH-INPUT-20260926 V1 · V13) — design-lint.mjs condition i judges
// @media against them; the design-system document ⑨ tables are hand-written and vitest
// (device-width-input-20260926-L4) compares them with these values.
export const WIDTH_STEPS = [
  { name: '휴대폰', min: null, max: 640 },
  { name: '패드 세로', min: 641, max: 900 },
  { name: '패드 가로', min: 901, max: 1180 },
  { name: 'PC', min: 1181, max: null },
];
export const WIDTH_MAX = WIDTH_STEPS.map(s => s.max).filter(v => v != null);
export const WIDTH_MIN = WIDTH_STEPS.map(s => s.min).filter(v => v != null);
// Input conditions allowed in @media (우려 11ⓐ) — only these two spellings. (pointer: fine) · (hover: none) · any-* are red.
export const INPUT_ALLOWED = ['(pointer: coarse)', '(hover: hover)'];
