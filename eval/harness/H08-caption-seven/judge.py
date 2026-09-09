#!/usr/bin/env python3
"""Static literal font-size audit; stdlib only, no computed-style claims."""
from decimal import Decimal
from pathlib import Path
import re
import sys

FILES = ('detail.css', 'upload.css', 'lineageGraph.css')
NUMBER = r'[+-]?(?:[0-9]*\.[0-9]+|[0-9]+)(?:[eE][+-]?[0-9]+)?'
PX = re.compile(rf'({NUMBER})px', re.IGNORECASE)
ANCHOR = {'.vizerr', '.warn'}


class PreparationError(ValueError):
    pass


def without_comments(css):
    """Replace comments with whitespace, preserving offsets and property line numbers."""
    parts = []
    i = 0
    quote = None
    while i < len(css):
        char = css[i]
        if quote:
            parts.append(char)
            if char == '\\' and i + 1 < len(css):
                i += 1
                parts.append(css[i])
            elif char == quote:
                quote = None
        elif char in '\"\'':
            quote = char
            parts.append(char)
        elif css.startswith('/*', i):
            end = css.find('*/', i + 2)
            if end < 0:
                raise PreparationError('unterminated CSS comment')
            parts.append(''.join('\n' if c == '\n' else ' ' for c in css[i:end + 2]))
            i = end + 1
        else:
            parts.append(char)
        i += 1
    if quote:
        raise PreparationError('unterminated CSS string')
    return ''.join(parts)


def declarations(css):
    """Scan declaration boundaries, respecting strings/functions and nested rules.

    This is a literal scanner, not a CSS engine. Non-literal values remain unknown.
    Structural corruption fails preparation instead of yielding a partial inventory.
    """
    css = without_comments(css)
    stack = []
    brackets = []
    quote = None
    start = 0
    i = 0
    found = []
    while i < len(css):
        char = css[i]
        if quote:
            if char == '\\':
                i += 1
            elif char == quote:
                quote = None
        elif char in '\"\'':
            quote = char
        elif char in '([':
            brackets.append(char)
        elif char in ')]':
            if not brackets or brackets.pop() != {')': '(', ']': '['}[char]:
                raise PreparationError('unbalanced CSS parentheses/brackets')
        elif not brackets and char in '{};':
            chunk = css[start:i]
            if char == '{':
                stack.append(chunk.strip())
            else:
                match = re.fullmatch(r'\s*(font-size)\s*:\s*(.*?)\s*', chunk,
                                     re.IGNORECASE | re.DOTALL)
                if stack and match:
                    line = css.count('\n', 0, start + match.start(1)) + 1
                    found.append((line, stack[-1], match[2]))
                if char == '}':
                    if not stack:
                        raise PreparationError('unbalanced CSS braces')
                    stack.pop()
            start = i + 1
        i += 1
    if stack or brackets or quote or css[start:].strip():
        raise PreparationError('incomplete CSS structure')
    return found


def inventory(fixture):
    expected = set()
    anchors = []
    for name in FILES:
        rows = declarations((fixture / name).read_text(encoding='utf-8'))
        if not rows:
            raise PreparationError(f'{name}: no font-size declarations')
        seen_lines = set()
        for line, selector, value in rows:
            if line in seen_lines:
                raise PreparationError(f'{name}:{line}: multiple font-size declarations on one line unsupported')
            seen_lines.add(line)
            match = PX.fullmatch(value)
            number = Decimal(match[1]) if match else None
            if number is not None and number < 13:
                expected.add(f'{name}:{line}')
            if name == 'upload.css' and {s.strip() for s in selector.split(',')} == ANCHOR:
                anchors.append(number)
    if anchors != [Decimal(13)]:
        raise PreparationError('existing error-body rule must have one literal 13px declaration')
    return expected


def judge(text, expected):
    # Only the final three nonblank lines carry findings; prose never supplies missing coordinates.
    lines = [re.sub(r'^\s*[-*]\s+', '', line).strip() for line in text.splitlines() if line.strip()]
    if len(lines) < 3:
        return False
    keys = (r'지목\s*:', r'목록\s*:', r'무접촉(?:\([^\n]*\))?\s*:')
    for key in keys:
        if sum(bool(re.match(key, line)) for line in lines) != 1:
            return False
    count = re.fullmatch(r'지목:\s*([0-9]+)곳', lines[-3])
    listing = re.fullmatch(r'목록:\s*(.*)', lines[-2])
    untouched = re.fullmatch(r'무접촉\(이미 13px\):\s*(.*?)\s+(' + NUMBER + r')px', lines[-1])
    if not count or not listing or not untouched:
        return False
    coords = [item.strip() for item in listing[1].split('·')] if listing[1] else []
    if any(not re.fullmatch(r'(?:detail|upload|lineageGraph)\.css:[1-9][0-9]*', item) for item in coords):
        return False
    selectors = [s.strip() for s in untouched[1].split(',')]
    return (int(count[1]) == len(coords) == len(expected)
            and len(coords) == len(set(coords)) and set(coords) == expected
            and len(selectors) == 2 and set(selectors) == ANCHOR
            and Decimal(untouched[2]) == 13)


def main():
    try:
        expected = inventory(Path(__file__).resolve().parent / 'fixture')
    except (OSError, UnicodeError, PreparationError) as exc:
        print(f'expect preparation — {exc}', file=sys.stderr)
        return 78
    try:
        passed = judge(sys.stdin.read(), expected)
    except (UnicodeError, ValueError):
        passed = False
    if not passed:
        print('expect red — final count/list/untouched fields must match the static inventory exactly', file=sys.stderr)
    return 0 if passed else 1


if __name__ == '__main__':
    sys.exit(main())
