#!/usr/bin/env python3
"""`dev-package/work-items.yaml` 전용 3-way 병합 드라이버.

무엇을 해소하나 (D4 · `rules/colab-rules.md §4-2`)
  병렬 레인은 각자 `items:` **끝에 자기 WU 블록을 덧붙인다.** 텍스트 병합기에게 그것은 같은
  자리의 다른 변경이라 두 번째 레인부터 리베이스가 등재 커밋에서 충돌한다. 2026-09-06 R-A 회차의
  FE 레인 3개가 그렇게 걸렸고, 손 해소 중 YAML 이 한 번 깨졌다.
  ⇒ **덧붙임은 충돌이 아니다.** 그 사실을 드라이버가 안다.

규칙 (`§4-2` 축자를 기계로 옮긴 것)
  · 결과의 뼈대는 **HEAD(ours) 판 전체**다.
  · 상대(theirs)가 새로 만든 WU 블록만 **끝에 덧붙인다.** 같은 id 의 옛 블록은 남기지 않는다.
  · 「양쪽 다 취함」을 하지 않는다 — 블록이 엇갈려 섞인다.
  · 한쪽만 고친 블록은 고친 쪽을 취한다. **양쪽이 서로 다르게 고쳤으면 충돌이다.**
  · 마지막에 `yaml.safe_load` 로 파싱과 **id 유일성**을 확인한다.
  · ⚠ **의심스러우면 exit 1.** 그때는 표준 충돌 표식을 남겨 사람이 본다 — 조용히 고르지 않는다.

호출 (`.gitattributes` 의 `merge=work-items` 가 이 이름을 가리킨다)
    git config merge.work-items.driver "python3 dev-package/tools/merge-work-items.py %O %A %B"
    git config merge.work-items.name   "work-items.yaml 덧붙임 병합"
  %O 공통 조상 · %A 우리(HEAD · **결과를 여기에 쓴다**) · %B 상대.
  종료코드 0 = 깨끗이 병합 · 0 이 아니면 git 이 충돌로 판정한다.
"""
import re
import subprocess
import sys

BLOCK_START = re.compile(r"^  - ")
ID_RE = re.compile(r"^\s*-?\s*id:\s*(\S+)")


def split_blocks(text):
    """(머리말, [(id, 블록문자열)]) — 블록은 `  - ` 줄부터 다음 `  - ` 줄 직전까지."""
    lines = text.splitlines(keepends=True)
    first = None
    for i, ln in enumerate(lines):
        if BLOCK_START.match(ln):
            first = i
            break
    if first is None:
        return text, []
    head = "".join(lines[:first])
    blocks, cur = [], [lines[first]]
    for ln in lines[first + 1:]:
        if BLOCK_START.match(ln):
            blocks.append("".join(cur))
            cur = [ln]
        else:
            cur.append(ln)
    blocks.append("".join(cur))
    out = []
    for b in blocks:
        m = ID_RE.match(b.splitlines()[0].lstrip().rstrip("\n")) or ID_RE.search(b)
        out.append((m.group(1).strip('"\'') if m else None, b))
    return head, out


def as_map(blocks):
    d, order = {}, []
    for bid, txt in blocks:
        if bid is None:
            return None, None            # id 없는 블록 = 형식을 모른다 → 손을 뗀다
        if bid in d:
            return None, None            # 입력 자체가 이미 중복이다 → 손을 뗀다
        d[bid] = txt
        order.append(bid)
    return d, order


def bail(o_path, a_path, b_path, why):
    """의심스러우면 표준 충돌 표식을 남기고 물러선다. 조용히 한쪽을 고르지 않는다."""
    sys.stderr.write("work-items 병합 드라이버: 손을 뗀다 — %s\n" % why)
    try:
        subprocess.run(["git", "merge-file", "--marker-size=7",
                        "-L", "HEAD (ours)", "-L", "공통 조상", "-L", "병합 대상 (theirs)",
                        a_path, o_path, b_path], check=False)
    except Exception:
        pass                              # git 이 없으면 %A 를 그대로 둔다 — 어차피 충돌 처리다
    return 1


def main(argv):
    if len(argv) < 4:
        sys.stderr.write("사용: merge-work-items.py %O %A %B\n")
        return 2
    o_path, a_path, b_path = argv[1], argv[2], argv[3]
    try:
        o_txt = open(o_path, encoding="utf-8").read()
        a_txt = open(a_path, encoding="utf-8").read()
        b_txt = open(b_path, encoding="utf-8").read()
    except Exception as e:
        return bail(o_path, a_path, b_path, "입력을 못 읽었다 (%s)" % e)

    if a_txt == b_txt:
        return 0

    o_head, o_blocks = split_blocks(o_txt)
    a_head, a_blocks = split_blocks(a_txt)
    b_head, b_blocks = split_blocks(b_txt)
    O, _ = as_map(o_blocks)
    A, a_order = as_map(a_blocks)
    B, b_order = as_map(b_blocks)
    if A is None or B is None or O is None:
        return bail(o_path, a_path, b_path, "id 없는 블록이거나 입력에 중복 id 가 있다")

    # 머리말(주석·`items:`)은 통째로 3-way 한다. 여기까지 양쪽이 다르게 고쳤으면 사람이 본다.
    if a_head == b_head:
        head = a_head
    elif a_head == o_head:
        head = b_head
    elif b_head == o_head:
        head = a_head
    else:
        return bail(o_path, a_path, b_path, "머리말을 양쪽이 서로 다르게 고쳤다")

    result, conflicts = [], []
    for bid in a_order:
        a_b, b_b, o_b = A[bid], B.get(bid), O.get(bid)
        if b_b is None:
            if o_b is None or a_b != o_b:
                result.append(a_b)                 # 우리가 새로 만들었거나 고쳤다 → 남긴다
            # 상대가 지웠고 우리는 안 건드렸다 → 삭제를 따른다(아무것도 넣지 않는다)
            continue
        if a_b == b_b or b_b == o_b:
            result.append(a_b)
        elif a_b == o_b:
            result.append(b_b)                     # 상대만 고쳤다
        else:
            conflicts.append(bid)                  # 양쪽이 다르게 고쳤다
            result.append(a_b)
    # 상대가 새로 만든 블록은 **끝에 덧붙인다** (§4-2 축자)
    for bid in b_order:
        if bid not in A:
            if bid in O:
                conflicts.append(bid)              # 우리가 지운 것을 상대가 고쳤다
            result.append(B[bid])

    if conflicts:
        return bail(o_path, a_path, b_path,
                    "같은 WU 를 양쪽이 다르게 고쳤다 — %s" % ", ".join(sorted(set(conflicts))))

    merged = head + "".join(result)

    # ── 마지막 관문: 파싱되는가 · id 가 유일한가 ──────────────────────────────
    try:
        import yaml
    except Exception:
        return bail(o_path, a_path, b_path, "PyYAML 이 없어 결과를 검증할 수 없다")
    try:
        doc = yaml.safe_load(merged)
    except Exception as e:
        return bail(o_path, a_path, b_path, "결과가 YAML 로 파싱되지 않는다 (%s)" % e)
    items = (doc or {}).get("items")
    if not isinstance(items, list) or not items:
        return bail(o_path, a_path, b_path, "결과에 `items:` 목록이 없다")
    ids = [it.get("id") for it in items if isinstance(it, dict)]
    if len(ids) != len(items):
        return bail(o_path, a_path, b_path, "id 없는 항목이 남았다")
    dup = sorted({i for i in ids if ids.count(i) > 1})
    if dup:
        return bail(o_path, a_path, b_path, "id 중복 — %s" % ", ".join(map(str, dup)))

    with open(a_path, "w", encoding="utf-8") as f:
        f.write(merged)
    sys.stderr.write("work-items 병합: 항목 %d건 · 상대 신규 %d건 덧붙임\n"
                     % (len(ids), sum(1 for bid in b_order if bid not in A)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
