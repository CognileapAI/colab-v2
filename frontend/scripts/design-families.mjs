// Canonical token family prefixes — one list shared by design-lint.mjs (rules a · c) and design-docs.mjs (gate h tables).
// Spec S-DESIGN-STRUCTURE-P5-20260924 (advisor ②): the two scripts used to keep their own copies.
export const CANON_FAMILIES = ['color', 'space', 'text', 'radius', 'font', 'shadow', 'leading', 'tracking', 'fg', 'bg', 'accent'];
export const COLOR_FAMILIES = ['color', 'fg', 'bg', 'accent', 'shadow'];
export const CANON_PREFIX = new RegExp(`^--(${CANON_FAMILIES.join('|')})-`);
export const COLOR_FAMILY = new RegExp(`^--(${COLOR_FAMILIES.join('|')})-`);
