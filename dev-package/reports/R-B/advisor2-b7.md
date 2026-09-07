# Gate ② 수용 검토 — WU-B7 (p3-axis-filters · 32bf620 + ae43a7c · base 5adf9b4)

For:
- M-10 가 라운드 축자대로 1회로 묶였고(생성 컬럼 ADD 1 · GIN CREATE 1 · 델타 SQL 계수), 드리프트 대조군 ㈑-b/㈑-c 가 오라클의 유효성을 기계로 증명한다. R-A 이월 `nc` 검색이 기존 행(㈑)·신규 행(㈎) 양쪽에서 닫혔다.
- 3축 AND · `미지정` 파수꼴 · 패싯 · 상세 3행이 서버 13 + FE 9 시험으로 서고, `processingLevel` 정수 판정 무변(WU-B5 회귀 시험 포함). 파수꼴 정본은 서버 상수 1곳, 계약·FE 는 사본 표기.
- 폐기 비용: 0019 를 되돌리면 `nc`·신규 변수 행 색인 부재로 회귀. 설계 ㈏(미러 열 + 생성 컬럼 유지)는 실패 표면이 가장 좁다.

Against:
- 레인이 세운 불변식 「행 표가 정본 · 배열은 사본 · 트리거만 쓴다」를 **레인이 손댄 같은 파일**(`d3_catalog.py`)의 `_APPLY_AUTOMETA` 가 깨고 있는데 그대로 통과했다. 등록 경로 순서(autometa INSERT → replace_variables → apply_autometa)에서 행 0개면 헤더 유래 배열이 미러에 들어가고, 이후 행 변경 한 번에 '{}' 로 사라진다. 게이트 11종 전부 green 인 채로 색인이 비결정적이다 — 이 결함은 게이트가 못 재는 종류다.
- 라운드 WU-B7 본문 명령문 「홈 데이터 맵이 주제 축을 넘기던 자리를 분류 축으로 바꾼다」가 미집행. 레인 논거(byCategory 신설 = 20차 밖)는 성립하지만 라운드 파일과 20차 승인 범위의 불일치를 Ted 가 판정해야 하며, 레인이 스스로 「받는 쪽만」으로 재정의한 것이다.

Verdict: **approve-with-changes** — Fixes ①·② 병합 전 필수. ③~⑤ Ted 항목/후속.

Risks:
1. 실 DB 0019 백필: 0016 이후 등록되어 헤더 유래 변수명만 배열에 있던 데이터셋(행 표 0개)은 배열이 '{}' 로 덮여 변수명 검색 회귀. DO 단언은 「행 표와 같다」만 세므로 이 손실을 못 잡는다.
2. 분류 미러의 앱 롤 런타임 경로(PATCH category → trigger UPDATE autometa) 시험 0건 — 정책상 통과가 예상되나 실측 없음. (`rls-effect` 게이트는 본체 음성·메타 양성·cross-tenant 3종만 재고 트리거를 안 본다.)
3. `replace_variables` DELETE→행별 INSERT 로 N+1 회 미러 재작성(생성 컬럼·GIN 포함). 현 규모 허용, 대량 편집 시 병목.

Missed (레인 보고에 없는 것):
- `d3_catalog.py:131-133` 산문 「트리거는 M-10 소속이라 아직 없다」· `:958` 이 0019 이후에도 그대로 — 레인이 편집한 파일 안의 사실 낡음.
- contract-breaking 기록 JSON(ae43a7c)에 base ref 필드 없음. 노트 축자 기준은 b982100(리베이스 전). b982100..5adf9b4 는 계약 +81 행(B6 추가분)이므로 낡은 base 는 초과 검출 방향(안전)이나, 리베이스 후 재실행 근거가 기록에 없다.
- `AppliedConditions` 칩이 3축 조건을 안 그린다(`hasConditions` 는 축 포함). 수용 기준 밖 · UX 후속.
- 「가공 단계」 상세 값(`Lv2`)과 wire 파라미터(정수 2)는 다르다 — FE 가 `slice(2)` 로 변환. 축 옵션 문자열끼리는 동일하므로 수용 기준(문자열 일치)은 축 옵션 기준으로 충족. 서버 시험은 category·dataType 만 검증(Lv 는 FE 시험).
- 공유 적용 DB 를 0019 로 올린 사실과 §11 「공유 적용 DB 에 마이그레이션을 올리지 않았다」가 문면상 충돌 — 스키마 전용 DB 를 가리키는 것으로 읽히나 노트 한 줄 정정 필요.

Fixes:
① **[병합 전 필수]** `_APPLY_AUTOMETA` 에서 `variables` 갱신을 제거(또는 `apply_autometa` 가 `variables` 를 받지 않게) — PRD-16 「트리거만 쓴다」 정합. `AUTOMETA_FROM_EVENTS` 의 `variables` 처리와 `autometa-loss` 게이트 영향을 함께 확인(config toml 에는 `variables` 없음 · 코드 튜플에는 있음). 회귀 시험 1건 추가: 변수 행 0개로 등록 + held.variables 비어 있지 않을 때 `autometa.variables == []`.
   ⚠ 대안(헤더 유래 변수명을 색인에 남기려면): 배열을 「행 표 ∪ 헤더」로 재정의하고 0019 DO 단언·트리거식·산문을 그에 맞춰 바꾼다 — 이는 설계 변경이라 Ted 판정. 기본값은 제거.
② **[병합 전 필수]** `contract-breaking` 을 `COLAB_BREAKING_BASE_REF=5adf9b4` 로 재실행하고 기록에 base 를 남긴다(병합 직전 전건 게이트와 함께).
③ `d3_catalog.py:131-133`·`:958` 산문을 0019 이후 상태로 정정(「트리거가 유지한다 · 0019」).
④ 앱 롤 시험 1건: PATCH `category` 뒤 `search` 로 그 분류 낱말이 잡히는가(`test_axis_filters.py` 또는 `test_variable_rows.py`).
⑤ Ted 항목으로 등재: ⓐ `AXIS_UNSET_NUDGE` 문면 확정(`[미상]` 차용분) ⓑ 홈 데이터 맵 분류 축 전환 → `LabDataMap.byCategory` 후속 WU(20차 밖 여부 판정) ⓒ M-10 가정 ⓐ 의존 명시 유지.
⑥ 후속: `d3_dataset_variable_mirror` 를 statement-level(`REFERENCING NEW TABLE/OLD TABLE`)로 전환하는 개선 항목 기록(현 회차 범위 밖).
