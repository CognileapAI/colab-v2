"""선언된 의존이 없는데 시험이 **조용히 사라지는** 자리를 막는다 (`CLAUDE.md §4`).

발단 — `pytest.importorskip("h5py")` 6 자리(`h5py` 5 · `jsonschema` 1)가 있었다.
둘 다 **선언·핀된 의존**이다(`requirements.in:7` `h5py` · `requirements-dev.in:5` `jsonschema`
· `requirements.txt` 에 `h5py==3.16.0` · `jsonschema==4.26.0`).
그 의존이 이미지에서 빠지면 시험은 **red 가 아니라 skip** 이 되고 요약줄은 green 을 찍는다.
사라지는 시험 중 둘은 **HSR 격자 off-by-one**(값만 한 칸 밀리고 그림은 멀쩡한 오류)을
지키는 자리라, 그 자리가 조용히 비는 것이 이 레포의 대표 실패형이다.

**세 상태로 만든다** — 선언된 의존이 있으면 **검사한다** · 명시적으로 면제하면
**건수를 드러낸 채** 넘어간다 · 아무 말도 없으면 **실패한다**.
"""
from __future__ import annotations

import pytest

import depgate


class _Blocked:
    """`import <name>` 을 실패시키는 가짜 importer."""

    def __init__(self, name: str) -> None:
        self.name = name

    def find_module(self, fullname, path=None):  # pragma: no cover - 구형 API
        return None


@pytest.fixture
def block(monkeypatch):
    def _block(name: str):
        def _fake_import(mod: str):
            if mod == name:
                raise ImportError(f"No module named {mod!r}")
            raise AssertionError(f"예상 밖 import: {mod}")

        monkeypatch.setattr(depgate, "_import", _fake_import)

    return _block


@pytest.fixture(autouse=True)
def _reset_counter(monkeypatch):
    monkeypatch.setattr(depgate, "_EXEMPTED", {})


# ── 상태 ① 대상 있음 → 검사한다 ───────────────────────────────────────────
def test_a_declared_and_installed_dependency_is_returned_not_skipped():
    """h5py 는 선언·설치돼 있다. 모듈이 그대로 돌아오고 건너뛴 건수는 0 이다."""
    mod = depgate.require_dep("h5py")
    assert mod.__name__ == "h5py"
    assert depgate.exempted_counts() == {}


# ── 상태 ② 명시적 면제 → 통과하되 건수를 드러낸다 ─────────────────────────
def test_an_explicitly_exempted_missing_dependency_skips_but_surfaces_its_count(
    block, monkeypatch
):
    block("h5py")
    monkeypatch.setenv(depgate.EXEMPT_ENV, "h5py")
    with pytest.raises(BaseException) as exc:
        depgate.require_dep("h5py")
    assert exc.typename == "Skipped", f"면제는 skip 이어야 한다 — 실제 {exc.typename}"
    assert depgate.exempted_counts() == {"h5py": 1}, "면제 건수가 세어지지 않는다"


def test_the_exempted_count_reaches_the_summary_line(block, monkeypatch):
    """건수가 세어지기만 하고 **요약줄에 안 나오면** 숨긴 것과 같다."""
    block("h5py")
    monkeypatch.setenv(depgate.EXEMPT_ENV, "h5py")
    for _ in range(3):
        with pytest.raises(BaseException):
            depgate.require_dep("h5py")
    line = depgate.summary_line()
    assert line is not None
    assert "h5py" in line and "3" in line, f"요약줄이 건수를 숨긴다: {line!r}"


def test_an_exemption_for_another_name_does_not_cover_this_one(block, monkeypatch):
    """면제는 이름별이다 — 하나를 면제했다고 나머지가 열리지 않는다."""
    block("h5py")
    monkeypatch.setenv(depgate.EXEMPT_ENV, "jsonschema")
    with pytest.raises(BaseException) as exc:
        depgate.require_dep("h5py")
    assert exc.typename == "Failed"


# ── 상태 ③ 아무 말도 없음 → 실패한다 ──────────────────────────────────────
def test_a_missing_dependency_with_no_exemption_fails_and_never_skips(block, monkeypatch):
    block("h5py")
    monkeypatch.delenv(depgate.EXEMPT_ENV, raising=False)
    with pytest.raises(BaseException) as exc:
        depgate.require_dep("h5py")
    assert exc.typename == "Failed", (
        f"선언된 의존이 없는데 {exc.typename} 이다 — skip 은 green-by-skip 이다"
    )
    assert "h5py" in str(exc.value)


def test_an_empty_exemption_variable_is_not_an_exemption(block, monkeypatch):
    """`VAR=` 같은 빈 값이 관대한 쪽으로 떨어지지 않는다(`CLAUDE.md §4`)."""
    block("h5py")
    monkeypatch.setenv(depgate.EXEMPT_ENV, "")
    with pytest.raises(BaseException) as exc:
        depgate.require_dep("h5py")
    assert exc.typename == "Failed"


def test_a_wildcard_is_not_honoured_as_a_blanket_exemption(block, monkeypatch):
    """`*` 로 전부 면제하는 문은 두지 않는다 — 이름으로만 면제한다."""
    block("h5py")
    monkeypatch.setenv(depgate.EXEMPT_ENV, "*")
    with pytest.raises(BaseException) as exc:
        depgate.require_dep("h5py")
    assert exc.typename == "Failed"


# ── 선언 자체가 없으면 실패한다 ────────────────────────────────────────────
def test_an_undeclared_dependency_fails_even_when_it_is_importable():
    """아무 데도 선언되지 않은 이름은 **설치돼 있어도** 통과시키지 않는다.

    선언 없는 의존은 이미지에 있을 근거가 없다 — 있는 것은 우연이다.
    """
    with pytest.raises(BaseException) as exc:
        depgate.require_dep("json")
    assert exc.typename == "Failed"
    assert "선언" in str(exc.value)


def test_an_undeclared_dependency_cannot_be_exempted_either(monkeypatch):
    monkeypatch.setenv(depgate.EXEMPT_ENV, "json")
    with pytest.raises(BaseException) as exc:
        depgate.require_dep("json")
    assert exc.typename == "Failed"


# ── 선언 목록을 실제로 읽는다 (0건이면 red) ───────────────────────────────
def test_the_declaration_list_is_read_from_the_requirement_files_and_is_not_empty():
    """모수를 센다 — 선언 목록이 0 건이면 위의 판정이 전부 무의미해진다."""
    names = depgate.declared_names()
    assert len(names) > 0, "선언 목록이 0 건이다 — 검사 대상이 없다"
    assert "h5py" in names and "jsonschema" in names


def test_every_importorskip_on_a_declared_dependency_is_gone():
    """형제를 남기지 않는다 — 같은 모양이 다른 파일에 살아 있으면 고친 것이 아니다."""
    from pathlib import Path

    tests_dir = Path(__file__).parent
    offenders = []
    for p in sorted(tests_dir.rglob("*.py")):
        if p.name == Path(__file__).name:
            continue
        for i, line in enumerate(p.read_text("utf-8").splitlines(), 1):
            if "pytest.importorskip(" in line:
                offenders.append(f"{p.name}:{i}")
    assert offenders == [], f"green-by-skip 잔존: {offenders}"
