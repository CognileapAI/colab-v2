"""S3 객체 키용 경로 정규화 — 순수 함수.

차이 계산(diff)이 경로 문자열 비교로 동작하므로 정규화는 결정적이어야 한다.
핵심은 NFC: macOS 는 파일명을 자모 분해(NFD)로, Windows 는 완성형(NFC)으로 준다.
정규화 없이는 같은 폴더를 두 OS 에서 올릴 때 전부 새 파일로 인식된다 —
한글 파일명이 흔한 환경에서 반드시 터지는 문제다. 규칙은 프론트
`normalizeName.ts` 와 한 글자도 다르면 안 된다 — 양쪽 테스트가 같은 벡터를 쓴다.
"""
from __future__ import annotations

import unicodedata

# 최종 키({lab_id}/{…}/src/ 접두사 포함)의 UTF-8 상한 — S3 키 한계와 같다
MAX_KEY_BYTES = 1024

_CONTROL = {c: None for c in (*range(0x00, 0x20), 0x7F)}


def normalize_relative_path(raw: str) -> str:
    """브라우저가 준 webkitRelativePath 를 S3 키 조각으로 정규화한다.

    거부해야 할 입력(정규화 후 아무 세그먼트도 안 남음)이면 ValueError.
    규칙 순서 — 백슬래시 → NFC → 세그먼트 정리 → 제어문자 → 앞뒤 공백·마침표.
    """
    text = unicodedata.normalize("NFC", raw.replace("\\", "/"))
    segments: list[str] = []
    for seg in text.split("/"):
        if seg in ("", ".", ".."):
            continue
        seg = seg.translate(_CONTROL).strip(" .")
        if seg in ("", ".", ".."):  # 다듬은 뒤 다시 검사 — " .. " 같은 위장 통과 방지
            continue
        segments.append(seg)
    if not segments:
        raise ValueError(f"경로에 남는 세그먼트가 없다: {raw!r}")
    return "/".join(segments)


def join_under_base(base_path: str, relative_path: str) -> str:
    """업로드 대상 폴더(base_path)와 클라이언트 상대 경로를 결합한다.

    결합 **전에** 각각 정규화하고 결합 **후에** 다시 정규화한다 —
    `..` 가 결합 시점에 되살아나 묶음 밖으로 탈출하는 것을 막기 위해서다.
    결과가 base 로 시작하지 않으면 ValueError (정규화가 `..` 를 제거하므로
    실제로는 도달 불가한 이중 안전망이다).
    """
    base = normalize_relative_path(base_path) if base_path.strip(" /.") else ""
    rel = normalize_relative_path(relative_path)
    joined = normalize_relative_path(f"{base}/{rel}" if base else rel)
    if base and not joined.startswith(base + "/"):
        raise ValueError(f"결합 결과가 대상 폴더를 벗어났다: {joined!r} ⊄ {base!r}")
    return joined


def ensure_key_length(key: str) -> str:
    """최종 키의 UTF-8 길이를 검사한다. 넘으면 ValueError."""
    size = len(key.encode("utf-8"))
    if size > MAX_KEY_BYTES:
        raise ValueError(f"객체 키가 {MAX_KEY_BYTES}바이트를 넘는다 ({size}바이트): {key[:80]!r}…")
    return key
