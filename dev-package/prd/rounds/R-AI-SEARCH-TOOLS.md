> spec: dev-package/prd/specs/AI-SEARCH-TOOLS.md
# 버전 전송과 갱신 도구 실행 계획

부모 단일 writer, 독립 읽기 전용 reviewer. 기존 변경 보존, 배포 없음.

- [x] 실물 계약/인증/버전·lease 점검, 사양과 독립 설계 검토.
- [x] HTTP 생산자/소비자, scoped 도구의 실패 테스트 RED.
- [x] core-ai /ontology-manifest 계약 및 생성 wire 상수, 서비스 토큰/읽기 endpoint.
- [x] OntologyHttpClient.load_manifest(): timeout, 실제 bytes 상한, redirect 거부, 내용 검증.
- [x] SearchRefreshTools.sync_manifest/claim/read/complete: 핸들 제한과 read 이후 재검증/원자적 저장.
- [x] 집중/전체 회귀 및 contract-lint/generated-up-to-date/import/DB/AI-write 게이트.
- [x] 독립 수용 검토, intent 대조, 대장·인계 기록.

```python
version = tools.sync_manifest()
handle = tools.claim(limit=1)[0]['handle']
source = tools.read(handle)
assert source['ontology_version'] == version
# 임의 사실 문장은 받지 않는다. 식별자는 내용 버전에서 유효해야 한다.
result = tools.complete(handle, expected_version=version, concept_ids=[])
```

다음 단위: ontology 개념 내용 조회와 실제 제한 agent 실행 조율, 일일 실행 상태/재시도, 검색 연결.
