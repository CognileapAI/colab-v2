> spec: dev-package/prd/specs/AI-SEARCH-ONTOLOGY-VERSIONS.md
# 온톨로지 내용 버전·해석 의존 실행 계획

부모 단일 writer, 독립 읽기 전용 reviewer. 기존 미커밋 단계①/② 변경 보존. 배포 없음.

- [x] 기존 D9/D3 경계 확인·사양 작성·독립 설계 검토.
- [x] RED: `services/ai-service/tests/test_ontology_manifest.py`, `services/core-api/tests/test_search_ontology.py`.
- [x] D9 읽기: `app/ontology_manifest.py::load_manifest(engine)`에서 한 SQL → 정렬 digest.
- [x] Port: `services/core-api/src/colab_core/ports/ontology.py::validate_manifest(value)`에서 형식/내용 해시 검증.
- [x] DB: `0035_search_ontology.py`와 schema에 D3 release/head/binding/dependency, FORCE RLS.
- [x] D3: `publish(session, manifest, expected_previous)`, `bind(session, fact_id, expected_version, concept_ids)`,
  `current_bindings(session, dataset_id)`, `requeue(session, limit=100)` 구현.
- [x] 집중 10건 GREEN, core 1267/ai 146건 회귀, 신규 실제 사전 DB 포함 5건. migration/schema/RLS/import/work-item/DB 경계 통과.
- [x] 독립 수용 검토: 의존 누락/조회 경합 RED→GREEN, 재검토 차단 0. intent 대조·대장/인계 갱신.

## 구현 계약과 검증 예

```python
# 발행은 이전 버전 비교를 요구한다. 처음에는 None.
publish(session, manifest, expected_previous=None)
# 개념이 없어도 discovery 의존이 생긴다.
bind(session, fact_id, expected_version=manifest['version'], concept_ids=[])
# 새 단어가 생기면 이 연결도 오래된 것으로 판정한다.
assert current_bindings(session, dataset_id) == []
assert len(requeue(session, limit=1)) == 1
assert requeue(session, limit=1) == []
```

각 검사 로그는 `dev-package/reports/ai-search-ontology/`에 보관한다.
완료 조건은 위 사양의 로컬 기반 구현/검증이며 실제 에이전트·일일 스케줄러 가동은 별도다.
