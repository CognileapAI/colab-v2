# 파일 자격·접속 코드와 DB 계정의 겹침 실측

회차 `R-LOGIN-BACKOFFICE` 작업 6 · 검토 조건 ① 의 근거 기록. 2026-09-12.

## 무엇을 물었나

백오피스의 「비활성화」는 `account_admin.login_credential.status` 를 고친다. 그 열을 보는 코드가
DB 자격 경로 하나뿐이면, 같은 사람이 파일 자격(`credentials.json`)이나 접속 코드(`subjects.json`)
를 함께 가지고 있을 때 비활성화가 그 경로에는 닿지 않는다. 그래서 두 가지를 각각 확인했다 —
㈎ 코드가 그 열을 보는가 ㈏ dev 에서 실제로 겹치는 계정이 몇인가.

## ㈎ 코드 — 실측 결과 red 였고 이 회차에서 닫았다

- 종전 `kernel/authn.py` 의 `TrackedPasswordIssuer`(파일 자격)·`TrackedPlantedCodeIssuer`(접속 코드)
  는 `status` 를 **한 번도 조회하지 않았다**. 비활성 계정이 두 경로로 201 을 받았다(RED 로그 2건).
- 이제 두 발급기가 `DatabaseCredentialStore.status_for_account` 로 계정 상태를 보고, 활성이 아니면
  `AccountInactive` 를 올린다. 응답은 「자격이 틀렸다」와 **한 글자도 다르지 않고**(401 같은 봉투),
  실패 제한 버킷도 종전과 같이 세지 않는다.
- `None`(DB 자격 행 없음)은 「활성」이 아니라 **의견 없음**으로 읽는다. 백오피스가 만진 적 없는
  도구 계정을 조용히 끊지 않기 위해서다.
- 시험 = `services/core-api/tests/test_account_status.py` 의
  `test_inactive_account_cannot_log_in_through_the_legacy_file_credential` ·
  `test_inactive_account_cannot_log_in_through_a_planted_access_code`.

## ㈏ dev 실물 겹침 건수 — `[미확인]`

**문서에서 닿지 않는다.** 두 파일은 레포에 없고 EC2 의 시크릿 자리에만 있다 —
`infra/dev/compose.yml` 이 `${COLAB_DEV_SECRETS_DIR}/subjects.json` ·
`${COLAB_DEV_SECRETS_DIR}/credentials.json` 을 `/etc/colab/` 로 바인드 마운트한다.
내용물을 적은 문서는 레포에 없다(`docs/DEPLOY.md` 는 배치 절차만 적는다). 추정값을 쓰지 않는다.

재려면 dev 호스트에서 아래 한 벌을 돈다. **계정 식별자만 세고 해시·토큰은 출력하지 않는다.**

```bash
# ① 두 파일의 accountId 목록 (값이 아니라 식별자만)
sudo python3 -c 'import json,sys
ids=set()
for p in ("/etc/colab/subjects.json","/etc/colab/credentials.json"):
    try: raw=json.load(open(p))
    except FileNotFoundError: continue
    ids|={v["accountId"] for v in raw.values() if "accountId" in v}
print("\n".join(sorted(ids)))' > /tmp/file-identities.txt
wc -l /tmp/file-identities.txt

# ② DB 자격을 가진 계정과의 교집합 건수
psql "$ACCOUNT_ADMIN_URL" -At -c "SELECT count(*) FROM account_admin.login_credential
  WHERE account_id = ANY(string_to_array(pg_read_file('/tmp/file-identities.txt'), E'\n'))"
```

`pg_read_file` 이 막힌 배치라면 ①의 목록을 `VALUES` 로 붙여 같은 교집합을 센다.

## 이 값이 판정을 바꾸는가

바꾸지 않는다. 겹침이 0건이어도 ㈎ 의 결함은 결함이다 — 백오피스가 계정 하나를 비활성화한
뒤 그 계정에 파일 자격을 심는 순간 겹침이 생기고, 그때 검사기는 아무 말도 하지 않는다.
겹침 건수는 **이미 새어 나갔는지**를 말할 뿐이고, 그 답은 아직 `[미확인]` 이다.
