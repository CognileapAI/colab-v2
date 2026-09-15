# 명시 작업 상태 증거

새 task는 기존 `.git` common-dir runtime을 유지한다. `work-state`는 인계 증거의
소비자이며 별도 task 저장소를 만들지 않는다. PR 게시는 사용자가 수행한다.
Issue 쓰기는 대상·내용을 먼저 제시하고 별도 승인받는다.
로컬 검증 통과는 GitHub 게시·병합 사실 인증이나 제품 배포 완료가 아니다.

```sh
COLAB_WORK_STATE_MODE=work-state COLAB_WORK_STATE_INPUT=/path/to/state.json ./gates/run.sh work-item-consistency
python3 scripts/harness/work_state.py --input /path/to/state.json
```

명시 새 모드에 input이 없으면 78. 기본은 `.agents/harness.yaml`의
`transition.mode: legacy-compatibility`를 확인한 뒤 기존 235항목 제품 대조를 그대로 실행한다.
새 모드는 legacy 문서 없이 동작한다. 기존 env override와 19개 음성/대조 시험은 유지한다.

## 공개 소비자 API

`work_state.validate(value: dict, root: Path) -> dict[id, issue]`는 모든 선언을 검증한 뒤
id 색인을 돌려준다. planning/seam 소비자는 이 결과를 사용하고 CI 판정을 복제하지 않는다.
실패는 `StateError`, 입력 부재는 그 하위 `ReadinessError`다. CLI 종료코드는 각각 1/78이다.

입력 schema는 `colab-work-state/1`, `issues`는 비어 있지 않은 배열이다.
각 issue는 `id`(로컬 ID), `number`(미게시 null 또는 양의 정수), `state`(open/closed),
`dependencies`(로컬 ID 배열)를 가진다. ID/Issue 번호 중복·없는 의존·순환은 거절한다.
`product`는 title/owner/status/stage/entry_conditions/completion_def_ref/evidence_ref/deadline
및 required_gates 9필드가 필수다. 기존 제품 schema·status·stage·기한·conflict 판정부를 문서 읽기 없이 재사용한다.
완료 정의는 비어 있지 않은 로컬 참조로 선언한다. partial/done에는 evidence_ref가 필요하다.
Issue closed와 product done이 일치해야 하며 deadline의 unknown은 준비 실패다.
지원하지 않는 최상위·Issue·product 필드는 조용히 무시하지 않고 거절한다.

closed에는 다음 두 증거가 모두 필요하다. open도 증거를 선언하면 검사한다.

- `pr`: `head_sha`, `merge_sha` full SHA, `merged: true`, `ci`(CI 요약 객체),
  `artifact_root`(root 기준 또는 절대 producer bundle 경로). `verify_ci_bundle`을 재사용한다.
  number/repository/base_ref 및 `record: {path, sha256}`도 필수다. 취득 레코드는
  `colab-github-pr-record/1`, source(repository/number/endpoint/transport=gh-api/fetched_at),
  record(gh PR 응답의 number/state/merged/merged_at/head.sha/merge_commit_sha/base.ref/base.repo.full_name)다.
  실제 gh 읽기 조회에서 받은 필드를 보존하며 로컬 hash는 원격 서명 인증이 아니다.
- `task`: `task_id`, `run_id`, `checkout_id`, `report_sha256`. 현재 runtime 레코드와
  실제 report hash·commit/tree·before/after·선언 산출물을 기존 lifecycle 판정부로 확인한다.
  task report commit은 PR head와 같아야 한다. closed의 의존도 모두 closed여야 한다.
  `binding`은 해당 task에 명시 선언된 artifact 경로다. artifact schema는
  `colab-work-binding/1`, item_id, completion_def(path/sha256), required_gates이며
  완료 정의 파일·작업 항목·task 선언·실제 report gate 집합을 모두 대조한다.

GitHub에서 받은 자료의 로컬 정합 검사다. 임의 JSON을 만든 것만으로 원격 provenance를
인증하지 않는다. 닫힘 문자열만으로 완료를 인정하지 않는다.

## 안전한 이전 초안과 기존 결정 색인

`--export-ledger`는 표준 출력에 **로컬 검토 초안**만 내보낸다. 원문은 수정하지 않는다.
필드는 id/title/status/stage/depends_on/completion_def 존재 여부/source_ref/원문 item hash다.
note·evidence·완료본문·HANDOFF 원문은 출력하지 않는다. 게시용 확정 자료가 아니다.
`--decision-index`는 기존 PLAN 결정번호·원문 행 hash·source_ref만 내보낸다.
기존 기록 이동·삭제·accepted 상태 생성은 하지 않는다.

`--transition-complete`는 명시 retired 설정, 원본 항목의 Issue 번호 연결,
legacy 소비자 실파일 검사와 HANDOFF 분류 완료가 없으면 거절한다.
소비자 검사는 지정 파일뿐 아니라 scripts/gates/.agents/skills를 고정 범위로 훑는다.
tests와 읽기 전용 export/색인 판정부 자신만 제외한다. 설정에서 파일 목록을 줄여 0건으로 만들 수 없다.
현재 Issue 미게시·HANDOFF 별도 검토·legacy 소비자 잔존으로 호환 종료를 주장할 수 없다.
종료에는 `transition.closure_evidence`의 mapping/handoff `{path,sha256}` 및
external_pr_records(PR35/38 취득 레코드 참조)가 추가로 필수다. mapping은 ledger hash와
각 id/source hash/kind(issue 또는 historical-done)/issue_number, handoff는 원본 hash와
classifications(row_sha256/kind/issue_number) 목록을 검증한다. §4 블로커 표의 모든 번호행
원행 hash와 exact set이 같아야 하며 EOL만 LF로 정규화한다. kind는 issue/security-excluded/
historical-resolved/unclassified이고 마지막 상태가 남으면 종료를 거절한다. 외부 제공 total은 믿지 않는다.
과거 done은 원본 hash로 보존하며 새 허구 PR을 요구하지 않는다. 현재 이 기록들은 없으며 생성하지 않았다.
HANDOFF 과거 '비밀2건' 계수는 ledger active57의 제외 ID 목록이 아니다.

## seam / planning 소비자

동일 `COLAB_WORK_STATE_MODE=work-state`와 `COLAB_WORK_STATE_INPUT`을 사용한다.
seam 새 인용은 같은 저장소의 전체 GitHub Issue/PR URL을 실제 검증된 번호와 대조한다.
ADR은 존재하는 `docs/decisions/<번호>-<이름>.md`와 구조·accepted 상태를 검사한다.
legacy 결정번호/사용자승인 문자열만으로 새 인용을 승인하지 않는다.
CI seam 기준은 event base full SHA이며 HEAD 자기 대조를 거절한다. local 새 모드도
`COLAB_SC_BASELINE` 명시가 필요하다. 기본 legacy 인용은 검사 대상 호환 건수를 출력한다.
planning 새 merged 항목은 manifest `work_item_id`가 검증된 closed 작업에 연결돼야 한다.
HTML↔MD와 원본↔적용 사본 hash·미등재 사본 검사는 계속 수행한다.
기존 적용 자료는 기본 legacy 모드에서 호환 건수를 드러내며 새 증거를 꾸며내지 않는다.
