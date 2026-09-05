"""경로 정규화 오라클 — `kernel/objectpath.py`.

차이 계산이 경로 문자열 비교로 동작하므로 정규화는 결정적이어야 한다.
특히 NFC: macOS 는 파일명을 자모 분해(NFD)로, Windows 는 완성형(NFC)으로 준다 —
정규화가 없으면 같은 폴더를 두 OS 에서 올릴 때 전부 새 파일로 인식된다.

DB·AWS 불필요 — 순수 단위 테스트다.
"""
from __future__ import annotations

import unicodedata

import pytest

from colab_core.kernel.objectpath import (
    MAX_KEY_BYTES,
    ensure_key_length,
    join_under_base,
    normalize_relative_path,
)


# ── 규칙 1 · 백슬래시 ───────────────────────────────────────────────────────

def test_backslash_becomes_slash():
    assert normalize_relative_path("data\\geo\\points.csv") == "data/geo/points.csv"


# ── 규칙 2 · NFC — 이 모듈의 존재 이유 ─────────────────────────────────────

def test_nfd_input_normalizes_to_nfc():
    nfd = unicodedata.normalize("NFD", "실험/데이터 1.csv")   # macOS 가 주는 형태
    nfc = unicodedata.normalize("NFC", "실험/데이터 1.csv")   # Windows 가 주는 형태
    assert nfd != nfc                                        # 실제로 바이트가 다르다
    assert normalize_relative_path(nfd) == normalize_relative_path(nfc) == nfc


# ── 규칙 3 · 빈 세그먼트 · `.` · `..` 제거 ─────────────────────────────────

def test_dot_dotdot_and_empty_segments_dropped():
    assert normalize_relative_path("./a//b/../c.csv") == "a/b/c.csv"


def test_escape_attempt_is_neutralized():
    # `..` 는 에러가 아니라 제거다 — 탈출 자체가 성립하지 않는다
    assert normalize_relative_path("../../etc/passwd") == "etc/passwd"


# ── 규칙 4 · 제어문자 제거 ─────────────────────────────────────────────────

def test_control_chars_stripped():
    assert normalize_relative_path("a\x00b/c\x1f\x7fd.csv") == "ab/cd.csv"


# ── 규칙 5 · 세그먼트 앞뒤 공백·마침표 제거 (Windows 압축 해제 함정) ────────

def test_segment_trailing_spaces_and_dots_trimmed():
    # 앞뒤만 다듬는다 — 세그먼트 중간의 공백·마침표("report. .csv"의 내부)는 보존된다
    assert normalize_relative_path(" data. / report. .csv") == "data/report. .csv"
    assert normalize_relative_path("data ./ x.csv ") == "data/x.csv"


def test_segment_that_empties_after_trim_is_dropped():
    assert normalize_relative_path("a/ .. /b.csv") == "a/b.csv"


# ── 규칙 6 · 아무것도 안 남으면 거부 ────────────────────────────────────────

@pytest.mark.parametrize("raw", ["", "/", "..", "./..", " . ", "\\", "\x00"])
def test_nothing_left_raises(raw):
    with pytest.raises(ValueError):
        normalize_relative_path(raw)


# ── 결정성 — 두 번 돌려도 같다 ──────────────────────────────────────────────

def test_idempotent():
    once = normalize_relative_path(unicodedata.normalize("NFD", " 실험\\결과 1.csv"))
    assert normalize_relative_path(once) == once


# ── 규칙 7 · 최종 키 길이 (접두사 포함 1024바이트) ─────────────────────────

def test_key_length_limit():
    ok = "k" * MAX_KEY_BYTES
    assert ensure_key_length(ok) == ok
    with pytest.raises(ValueError):
        ensure_key_length("k" * (MAX_KEY_BYTES + 1))
    # 길이는 글자 수가 아니라 UTF-8 바이트다 — 한글은 3바이트
    with pytest.raises(ValueError):
        ensure_key_length("한" * 342)      # 1026바이트


# ── base_path 결합 (§3 — 결합 전 각각 정규화, 결합 후 재정규화 + 시작 검증) ──

def test_join_under_empty_base():
    assert join_under_base("", "data/geo/points.csv") == "data/geo/points.csv"


def test_join_under_folder_node():
    assert join_under_base("data/geo", "points.csv") == "data/geo/points.csv"


def test_join_neutralizes_escape_from_base():
    # `..` 가 결합 시점에 되살아나 묶음 밖으로 나가지 못한다
    assert join_under_base("data", "../secret.csv") == "data/secret.csv"


def test_join_normalizes_base_too():
    nfd_base = unicodedata.normalize("NFD", "실험")
    assert join_under_base(nfd_base, "a.csv") == unicodedata.normalize("NFC", "실험") + "/a.csv"


def test_join_rejects_empty_result():
    with pytest.raises(ValueError):
        join_under_base("", "..")
