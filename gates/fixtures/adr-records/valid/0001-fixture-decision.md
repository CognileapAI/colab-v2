# ADR-0001: 시험용 결정은 필수 절을 모두 갖춘다

- 상태: proposed
- 날짜: 2026-09-25
- 대체함: 없음
- 대체됨: 없음

## 배경
adr-records 게이트의 정상 대조군이다.

## 결정
필수 절 여섯 개를 모두 적는다.

## 검토한 대안
절을 비워 두는 안은 게이트가 red 로 막는다.

## 결과와 감수한 비용
fixture 파일 하나를 유지한다.

## 재검토 조건
`.agents/harness.yaml` `adr_gate.required_sections` 가 바뀌면 함께 고친다.

## 근거
`scripts/tests/test_harness_record_gates.py`
