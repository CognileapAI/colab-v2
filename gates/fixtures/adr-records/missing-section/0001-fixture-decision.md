# ADR-0001: 시험용 결정에서 필수 절 하나가 빠졌다

- 상태: proposed
- 날짜: 2026-09-25
- 대체함: 없음
- 대체됨: 없음

## 배경
adr-records 게이트의 red 대조군이다. 「재검토 조건」 절이 없다.

## 결정
필수 절 하나를 뺀다.

## 검토한 대안
빠짐없이 적는 안은 valid fixture 가 맡는다.

## 결과와 감수한 비용
fixture 파일 하나를 유지한다.

## 근거
`scripts/tests/test_harness_record_gates.py`
