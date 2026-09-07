# WU-B6 · Lv0 출처 칸 — 게이트 ② 수용 검토 (df99a9c vs b982100)

For:
- 5 수용 기준이 시험과 1:1 대응하고 폐기된 판정(「Lv0 필수 400」·「Lv1 값 400」)의 회귀 시험이 서버 ⑴⑵·FE ㈎ `.reqtag` 0건으로 박혀 있다. 서버·계약·DB 어디에도 Lv 분기가 없다.
- 마이그레이션은 열 2개 추가만이고 backfill 0 · NO FORCE 구간 불요 사유가 0015/0017 대비로 명시됐다. 드리프트 ㈏㈐㈑-b 가 오라클의 오라클임을 증명한다.
- 계약 3 스키마 optional · basicInfo 열쇠 집합 시험 갱신 · DatasetRow 미확장(WU-B7 몫) — 범위 이탈 0.

Against:
- 이 WU 가 새로 연 입력 경로 하나가 사용자를 막다른 길로 보낸다. `RegisterArea` 의 `reg-source-downloaded-on` 은 `type` 없는 텍스트 칸이고, 사용자가 `2026.08.20`·`8/20` 을 적으면 서버는 400 을 내지만 `UploadModal.submit` 의 catch(`:805-810`)는 `UploadGone` 외 전부를 「데이터셋을 만들지 못했어요. 잠시 뒤 다시 시도해 주세요.」로 덮는다. 재시도로 해소되지 않는 원인을 재시도하라고 안내한다. 계약 문면이 「서버가 400 으로 되돌린다」로 500 을 막은 것은 맞으나, 그 400 이 화면에 닿지 않으면 사용자에게는 500 과 구별되지 않는다.
- 수정 폼도 같은 칸이 `TEXT_FIELDS` 텍스트박스다(기간 두 칸은 `type="date"`). 같은 폼 안에서 날짜 입력 방식이 둘로 갈린다.

Verdict: approve-with-changes — F1 을 병합 전 필수로 집행. 나머지 후속.

Risks:
1. 등록 ③ 날짜 오타 → 일반 실패 문구 → 사용자 이탈. (F1)
2. 상세 안내가 파생 Lv 기준이라 사람 Lv≥1＋부모 0건 신규 행에 「Lv0 인데 … 비어 있어요」와 B5 불일치 경고가 동시에 뜬다. 라운드 축자(「파생 Lv 가 Lv0 인 기존 행」)를 따른 결과이므로 결함이 아니라 문면 충돌 위험 — WU-B11 판정표에서 실물 확인.
3. 적용 DB `alembic upgrade head` 가 게이트 밖(§후속-1, 레인마다 반복) — 이 WU 의 결함은 아니나 R-B 통합 전 게이트 승격 판단 필요.

Missed:
- 수정 폼(`DatasetEditForm`)이 PATCH 400 을 어떻게 표면화하는지 세션 노트·시험 어디에도 없다. 등록과 같은 덮어쓰기라면 F1 범위에 포함.
- `_is_date` 는 Python 3.11 `date.fromisoformat` 이라 `20260820`·`2026-W34-1` 도 통과한다. DB `date` 캐스트도 받으므로 500 은 아니지만 계약 `format: date`(RFC3339 full-date) 보다 넓다. 후속 메모.
- `validate_human_metadata` 의 `changes.get(k) is not None and k in changes` 는 앞 절만으로 충분(중복 조건). 동작 영향 0.

Fixes:
- **F1 (병합 전 필수)** — 날짜 형상 오류가 사용자에게 닿게 한다. 택일:
  ㈀ 등록 `submit()` 직전과 수정 폼 저장 직전에 `sourceDownloadedOn.trim()` 이 `^\d{4}-\d{2}-\d{2}$` ∧ 유효 날짜가 아니면 전송하지 않고 해당 칸 아래에 인라인 문구를 세운다(문면은 서버 400 과 동일 `내려받은 날은 날짜(YYYY-MM-DD)다.` 를 재사용 — 저작 금지). placeholder `예: 2026-08-20` 유지.
  ㈁ 두 칸을 `type="date"` 로 바꾼다 — 단, placeholder 가 브라우저에서 표시되지 않아 PRD-19 placeholder 축자와 충돌하므로 ㈀ 우선.
  시험: FE 1건(오타 입력 → `createDataset` 미호출 ∧ 문구 표시).
- F2 (후속) — `UploadModal.submit` catch 가 서버 400 `message` 를 그대로 노출하는 경로가 없다. B3 몫이었던 일반 실패 문구를 400 ↔ 그 외로 가르는 것은 별 WU 로 등재.
- F3 (후속) — `_is_date` 를 `^\d{4}-\d{2}-\d{2}$` 선검사＋`fromisoformat` 으로 좁혀 계약 `format: date` 와 일치시킨다.
- F4 (기록) — 세션 노트 「자기 표시」에 F1 의 근거(400 이 화면에 닿지 않음)를 한 줄 추가. 게이트 기록 9건은 commit=df99a9c 로 일치 — 재실행 불요.
