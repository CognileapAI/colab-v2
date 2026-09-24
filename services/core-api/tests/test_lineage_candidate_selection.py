"""WU1a — 계보 후보 선정(순수 도메인 함수).

계약·중계·모델은 건드리지 않는다. 여기서 재는 것은 **core-api 가 D3 에서 무엇을 고르는가** 뿐이다.
전략 두 벌(`recent` 무필터 최근순 · `filtered` 이름/주제 필터)을 **둘 다** 구현해 나란히 재는 이유는
`R-K3-RESUME.md` 「게이트 ① 판정」의 Ted 결정 ③ 이 아직 열려 있기 때문이다 — 한쪽만 구현하면
그 결정이 측정 없이 기본값으로 굳는다.
"""
import pytest

from conftest import ACC_A_RES, ACC_B_PROF, DS_A1, DS_A2, DS_B1, LAB_A, LAB_B, scoped_ro
from colab_core.domains import d3_catalog, d4_lineage

TOPIC_RAIN = "강우·강수"
TOPIC_VEG = "식생·NDVI"

#: 시험이 만드는 데이터셋. 시드(DSA1·DSA2·DSB1)를 고치지 않는다 — 시드를 흔들면
#: 다른 시험의 개수 오라클이 함께 흔들린다(`conftest._rollback_p2_rows` 머리말과 같은 이유).
DS_VEG = "00000000000000000000DSVEG1"
#: ⚠ ULID 알파벳에는 `I`·`L`·`O`·`U` 가 없다 — `DSRAIN3` 은 도메인 CHECK 에 걸린다.
DS_RAIN3 = "00000000000000000000DSRN03"
DS_BARE = "00000000000000000000DSBARE"


def _seed(sql, dataset_id, *, name, topic, modified, source_label=None,
          lab=LAB_A, account=ACC_A_RES):
    sql("""INSERT INTO d3_dataset(id, lab_id, owner_account_id, uploader_account_id,
                                  source_label, uploaded_at, last_modified_at)
           VALUES(:id, :lab, :account, :account, :source, :modified, :modified)""",
        {"id": dataset_id, "lab": lab, "account": account,
         "source": source_label, "modified": modified},
        account_id=account, lab_id=lab)
    sql("""INSERT INTO d3_dataset_description(dataset_id, lab_id, name, topic, summary)
           VALUES(:id, :lab, :name, :topic, :summary)""",
        {"id": dataset_id, "lab": lab, "name": name, "topic": topic, "summary": "시험 자료"},
        account_id=account, lab_id=lab)


def _upload(name_draft=None, *, subject=None, file_name="upload.csv", part_count=1):
    """`core-ai.yaml#LineageSuggestionRequest` 와 **같은 모양**의 입력. 계약을 고치지 않는다."""
    meta = {"file": {"fileName": file_name, "kind": "본체"}}
    if part_count > 1:
        meta["file"]["partCount"] = part_count
    if name_draft is not None:
        meta["datasetNameDraft"] = name_draft
    if subject is not None:
        meta["subject"] = subject
    return meta


def _ids(candidates):
    return [c.core.dataset_id for c in candidates]


def _select(session, **kwargs):
    kwargs.setdefault("lab_id", LAB_A)
    kwargs.setdefault("upload_meta", _upload())
    return d3_catalog.select_lineage_candidates(session, **kwargs)


def test_최근순은_상한_k_를_넘지_않고_최근이_앞선다(session_factory, sql):
    _seed(sql, DS_RAIN3, name="A 강우 3차 가공", topic=TOPIC_RAIN,
          modified="2026-03-01T00:00:00Z", source_label="기상청")
    with scoped_ro(session_factory, ACC_A_RES, LAB_A) as session:
        every = _select(session, strategy="recent", k=20)
        capped = _select(session, strategy="recent", k=2)
    assert _ids(every) == [DS_RAIN3, DS_A2, DS_A1], "최근 수정순(desc)이 아니다"
    assert _ids(capped) == [DS_RAIN3, DS_A2], "상한 k 를 넘겨 실었다"


def test_필터는_모집단을_좁히고_최근순_정렬을_유지한다(session_factory, sql):
    _seed(sql, DS_VEG, name="A 식생 NDVI 월평균", topic=TOPIC_VEG,
          modified="2026-03-02T00:00:00Z", source_label="국립기상과학원")
    with scoped_ro(session_factory, ACC_A_RES, LAB_A) as session:
        filtered = _select(session, strategy="filtered", k=20,
                           upload_meta=_upload("식생 NDVI 월평균 재처리", subject=TOPIC_VEG,
                                               file_name="NDVI_mean_202305.tif"))
        recent = _select(session, strategy="recent", k=20)
    assert _ids(filtered) == [DS_VEG], "필터가 좁히지 못했다"
    assert set(_ids(recent)) > set(_ids(filtered)), "필터 결과가 무필터 모집단의 부분집합이 아니다"


def test_필터가_0건이면_최근순으로_떨어진다(session_factory, sql):
    with scoped_ro(session_factory, ACC_A_RES, LAB_A) as session:
        fallen = _select(session, strategy="filtered", k=20,
                         upload_meta=_upload("쿼카쿼카쿼카", file_name="쿼카쿼카쿼카.csv"))
        recent = _select(session, strategy="recent", k=20)
    assert _ids(fallen) == _ids(recent), "0건 필터가 빈 후보로 끝났다"
    assert all(c.matched_by == ("recent",) for c in fallen), \
        "폴백을 필터 적중으로 적었다 — 무엇이 골랐는지가 기록에서 사라진다"


def test_가공_단계는_판정된_후보에만_실린다(session_factory, sql):
    _seed(sql, DS_BARE, name="A 출처 미상 자료", topic=TOPIC_RAIN,
          modified="2026-03-03T00:00:00Z", source_label=None)
    with scoped_ro(session_factory, ACC_A_RES, LAB_A) as session:
        got = {c.core.dataset_id: c.processing_level for c in _select(
            session, strategy="recent", k=20,
            lineage_summaries=d4_lineage.LineageSummaryAdapter(session))}
    # 부모 0 · 출처 표기 있음 → `원천` 이라 Lv0 이 판정된 값이다.
    assert got[DS_A1] == 0
    # 부모 1 · 확정일이 최신 → `확정` 이라 파생 Lv1 이 판정된 값이다.
    assert got[DS_A2] == 1
    # 부모 0 · 출처 표기 없음 · 사람 값 없음 → `확인 필요`. **모르면 열쇠를 만들지 않는다.**
    assert got[DS_BARE] is None, "판정이 없는 후보에 Lv 를 지어냈다"


def test_계보_요약_포트가_없으면_가공_단계를_지어내지_않는다(session_factory, sql):
    with scoped_ro(session_factory, ACC_A_RES, LAB_A) as session:
        got = _select(session, strategy="recent", k=20)
    assert [c.processing_level for c in got] == [None] * len(got)


def test_다른_연구실_후보는_어느_전략에서도_보이지_않는다(session_factory, sql):
    with scoped_ro(session_factory, ACC_A_RES, LAB_A) as session:
        a_recent = _ids(_select(session, strategy="recent", k=20))
        a_filtered = _ids(_select(session, strategy="filtered", k=20,
                                  upload_meta=_upload("B 토지피복 원자료",
                                                      subject="토지피복·LULC")))
    with scoped_ro(session_factory, ACC_B_PROF, LAB_B) as session:
        b_recent = _ids(_select(session, lab_id=LAB_B, strategy="recent", k=20))
    assert DS_B1 not in a_recent and DS_B1 not in a_filtered
    assert b_recent == [DS_B1]
    assert DS_A1 not in b_recent and DS_A2 not in b_recent


def test_lab_id_인자는_경계가_아니다(session_factory, sql):
    """경계는 세션의 RLS 가 건다. 인자를 바꿔도 결과가 바뀌면 경계가 두 벌인 것이다."""
    with scoped_ro(session_factory, ACC_A_RES, LAB_A) as session:
        mine = _ids(_select(session, lab_id=LAB_A, strategy="recent", k=20))
        spoofed = _ids(_select(session, lab_id=LAB_B, strategy="recent", k=20))
    assert mine == spoofed and DS_B1 not in spoofed


def test_모르는_전략과_0_이하_k_는_거부한다(session_factory, sql):
    with scoped_ro(session_factory, ACC_A_RES, LAB_A) as session:
        with pytest.raises(ValueError):
            _select(session, strategy="관련도순", k=20)
        with pytest.raises(ValueError):
            _select(session, strategy="recent", k=0)


@pytest.mark.parametrize("meta,expected", [
    (_upload("강수 — WGS84 변환·연구대상지 crop 표본 (Lv.1)", file_name="hsr_sample.npy"),
     ["강수", "wgs84", "변환", "연구대상지", "crop", "표본", "hsr", "sample"]),
    # 확장자는 토큰이 아니다 — `.npy` 가 코퍼스 절반을 끌고 온다.
    (_upload(None, file_name="Prediction_20230501.npy"), ["prediction"]),
    # 라틴 2글자(`Lv`·`GK`·`2A`·`m`)와 숫자만인 조각(`100`)은 신호가 아니라 잡음이다.
    (_upload("GK-2A NDVI 100 m 월평균", file_name="2A.tif"), ["ndvi", "월평균"]),
])
def test_토큰은_확장자와_두글자_라틴_조각을_버린다(meta, expected):
    assert d3_catalog.lineage_candidate_tokens(meta) == expected


# ═══════ 자식 자신 제외 — Ted 결정 ⑦ (intent 「판정 기록 2회차」 7 · 2026-09-24) ═══════
#
# luna 실측의 J5 대조군에서 **억지 선택 6건 중 5건이 자식 자신**이었다
# (`dev-package/reports/k3-lineage-probe/README.md` 「luna 실측」). 제안을 묻는 시점의
# 업로드는 아직 데이터셋이 아니라 뺄 ID 가 없는데, 같은 자료가 이미 등록돼 있으면 그
# 데이터셋이 후보에 서고, 정답 부모가 사라진 자리에서 모델이 그것을 고른다.
#
# ⛔ 빼는 조건은 **이름 초안과 파일명이 둘 다 같을 때뿐**이다 — 이름만 같은 다른 판본은
#   사람이 실제로 고를 수 있는 부모라 남긴다(같은 이름의 다음 판이 이전 판의 자식인 경우).
TWIN_NAME = "A 강우 재적재 표본"
TWIN_FILE = "twin_sample.npy"
#: LAB_A 의 쌍둥이 — 업로드와 이름·파일명이 둘 다 같다. **모집단에서 가장 최근**이라
#: 상한 k 앞에서 빠지는지를 이 한 건이 가른다.
DS_TWIN = "00000000000000000000DSTWN1"
#: LAB_B 의 같은 이름·같은 파일명. 경계가 한 벌이면 어느 쪽 세션에서도 남의 것은 안 보인다.
DS_TWIN_B = "00000000000000000000DSTWNB"


def _seed_file(sql, dataset_id, file_id, *, file_name, kind="본체",
               lab=LAB_A, account=ACC_A_RES):
    sql("""INSERT INTO d3_file (id, lab_id, dataset_id, kind, file_name,
                                size_bytes, storage_key)
           VALUES (:id, :lab, :dataset, :kind, :file_name, 7, :key)""",
        {"id": file_id, "lab": lab, "dataset": dataset_id, "kind": kind,
         "file_name": file_name, "key": f"k/{file_id}"},
        account_id=account, lab_id=lab)


def _seed_twin(sql, dataset_id=DS_TWIN, file_id="00000000000000000000000FT1", *,
               name=TWIN_NAME, file_name=TWIN_FILE, modified="2026-05-01T00:00:00Z",
               lab=LAB_A, account=ACC_A_RES):
    _seed(sql, dataset_id, name=name, topic=TOPIC_RAIN, modified=modified,
          source_label="기상청", lab=lab, account=account)
    _seed_file(sql, dataset_id, file_id, file_name=file_name, lab=lab, account=account)


@pytest.mark.parametrize("strategy", ["recent", "filtered"])
def test_이름과_파일명이_둘_다_같은_후보는_두_전략에서_모두_빠진다(
        strategy, session_factory, sql):
    _seed_twin(sql)
    with scoped_ro(session_factory, ACC_A_RES, LAB_A) as session:
        got = _ids(_select(session, strategy=strategy, k=20,
                           upload_meta=_upload(TWIN_NAME, subject=TOPIC_RAIN,
                                               file_name=TWIN_FILE)))
    assert DS_TWIN not in got, "이름·파일명이 둘 다 같은 후보가 남았다 — 모델이 자기 자신을 고른다"
    assert DS_A1 in got, "자기 자신을 빼면서 남의 후보까지 지웠다"


def test_이름만_같은_다른_판본은_남는다(session_factory, sql):
    """같은 이름의 다음 판은 이전 판의 **부모일 수 있다** — 이름 하나로 빼지 않는다."""
    _seed_twin(sql)
    with scoped_ro(session_factory, ACC_A_RES, LAB_A) as session:
        got = _ids(_select(session, strategy="recent", k=20,
                           upload_meta=_upload(TWIN_NAME, file_name="other_sample.npy")))
    assert DS_TWIN in got, "이름만 같은 다른 판본을 뺐다 — 사람이 고를 수 있는 부모가 사라진다"


def test_파일명만_같은_후보는_남는다(session_factory, sql):
    _seed_twin(sql)
    with scoped_ro(session_factory, ACC_A_RES, LAB_A) as session:
        got = _ids(_select(session, strategy="recent", k=20,
                           upload_meta=_upload("A 강우 다른 판본", file_name=TWIN_FILE)))
    assert DS_TWIN in got, "파일명만 같은 후보를 뺐다"


def test_자기_자신을_빼도_후보는_상한_k_를_넘지_않는다(session_factory, sql):
    """쌍둥이가 **모집단에서 가장 최근**이라 빼지 않으면 k=2 의 첫 자리에 선다.

    빼는 자리는 상한으로 자르기 **전**이다 — 자른 뒤에 빼면 k 자리 안에서만 사라진다.
    질의 하나가 k행만 읽어 오므로 빈 자리가 늘 채워지지는 않는다. 이 시험이 지키는
    불변식은 **「넘지 않는다」**이지 「언제나 k건」이 아니다.
    """
    _seed_twin(sql)
    meta = _upload(TWIN_NAME, file_name=TWIN_FILE)
    with scoped_ro(session_factory, ACC_A_RES, LAB_A) as session:
        filtered = _ids(_select(session, strategy="filtered", k=2, upload_meta=meta))
        recent = _ids(_select(session, strategy="recent", k=2, upload_meta=meta))
    assert DS_TWIN not in filtered and DS_TWIN not in recent, "자신이 남았다"
    assert len(filtered) <= 2 and len(recent) <= 2, \
        f"상한 k=2 를 넘겼다: filtered={filtered} recent={recent}"
    assert recent == [DS_A2], f"자신을 뺀 자리가 아니라 다른 후보가 사라졌다: {recent}"


def test_자기_자신_제외는_세션_경계_안에서_판정된다(session_factory, sql):
    """파일명을 읽는 질의도 이 세션의 RLS 를 그대로 탄다 — 경계를 두 벌로 만들지 않는다."""
    _seed_twin(sql)
    _seed_twin(sql, DS_TWIN_B, "00000000000000000000000FTB",
               lab=LAB_B, account=ACC_B_PROF)
    meta = _upload(TWIN_NAME, file_name=TWIN_FILE)
    with scoped_ro(session_factory, ACC_A_RES, LAB_A) as session:
        a_side = _ids(_select(session, strategy="recent", k=20, upload_meta=meta))
    with scoped_ro(session_factory, ACC_B_PROF, LAB_B) as session:
        b_side = _ids(_select(session, lab_id=LAB_B, strategy="recent", k=20,
                              upload_meta=meta))
    assert DS_TWIN not in a_side and DS_TWIN_B not in a_side
    assert DS_TWIN_B not in b_side and DS_TWIN not in b_side
    assert DS_A1 in a_side and DS_B1 in b_side
