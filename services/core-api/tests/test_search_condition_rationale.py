from colab_core.app.search_conditions import explain_unverified_conditions


BASE = "연구실 안 9건에서 ‘강수’가 이름에 맞았어요 — 기간·지역·품질은 직접 봐 주세요."


def test_names_each_requested_condition_that_search_cannot_verify() -> None:
    line = explain_unverified_conditions(
        BASE,
        "2019년 전국 자료 중 결측률 0%인 직접 관측 100m 강수를 찾아줘",
    )

    assert "기간" in line
    assert "지역" in line
    assert "품질" in line
    assert "직접 관측" in line
    assert "확인하지 못했어요" in line
    assert "\n" not in line and "\r" not in line


def test_does_not_turn_summary_words_into_a_verified_file_role() -> None:
    line = explain_unverified_conditions(BASE, "검증용 정답 파일을 찾아줘")

    assert "파일 역할" in line
    assert "확인하지 못했어요" in line
    assert "검증용 파일이에요" not in line


def test_keeps_existing_rationale_for_a_query_without_extra_conditions() -> None:
    assert explain_unverified_conditions(BASE, "강수 데이터 찾아줘") == BASE


def test_keeps_the_existing_explanation_and_one_line_contract() -> None:
    line = explain_unverified_conditions(BASE, "오차가 없는 예측 자료")

    assert line.startswith(BASE)
    assert line.endswith("확인하지 못했어요.")
    assert "품질" in line and "파일 역할" in line
