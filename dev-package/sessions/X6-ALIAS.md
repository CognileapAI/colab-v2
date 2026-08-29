# X-6 — 별칭 재부착 실패 삼킴 (2026-08-29)

정본 완료 정의 = `work-items.yaml` 의 `X-6` 2행. 근거 = `PLAN-SoT §9 〈185〉-㉸`-⑵.
경계 = 배포·파이프라인 **미실행** · 운영 스택 무접촉 · 이미지 태그 무변경 · `gates/**` 읽기만.

## 1. 무엇이 결함이었나

`deploy.sh` ⑫ 가 두 가지를 동시에 틀렸다.

1. **무조건 성공** — `docker tag "colab-v2/$n:$TAG" "colab-v2/$n:i2" 2>/dev/null || true`
2. **순서** — 그 줄이 `ledger_append … green` · `mark_success` **뒤**에 있었다.

재부착이 실패해도 원장에는 이미 green 이 적혀 있었고, 복원 리허설(`compose.throwaway.yml`)은
`:i2` 라는 이름으로 이미지를 찾으므로 **옛 이미지를 리허설하며 통과**를 낼 수 있었다.
이 레포 대표 실패형(green-by-skip)과 같은 무늬다.

## 2. 어떻게 고쳤나 — 세 상태

`pipeline/lib.sh` 에 `alias_reattach()` 를 세우고, `deploy.sh` ⑫ 를 **원장보다 앞으로** 옮겼다.

- **요구되면 검사한다** — 6종 각각에 대해 붙인 뒤 `docker image inspect -f '{{.Id}}'` 로
  `:i2` 와 `:$TAG` 의 **이미지 ID 를 대조**한다. 「붙였다」와 「가리킨다」는 다르다.
- **명시 면제** — `--skip-alias-reattach` 일 때만 넘어가고, 원장에 `별칭재부착SKIP(6종)` 로 **건수가 남는다.**
- **아무 말도 없으면 실패한다** — `abort "별칭 재부착"` → 원장 red · 실패 표식 · `exit 70`.
- 성공 0건도 red 다(대상 0건 = red).

### 정상 부재와 실패를 어떻게 갈랐나

이 자리는 ④ 빌드가 방금 `colab-v2/$n:$TAG` 를 구운 뒤다.

- **대상 `:i2` 의 부재** = 첫 배포에서 정상. 그러나 그것은 `docker tag` 의 **결과**이지 실패가 아니다
  — 붙이면 생긴다. 그래서 사후 조회는 붙인 **뒤에** 하고, 이때의 부재는 red 다.
- **원본 `:$TAG` 의 부재** = 어떤 경우에도 정상이 아니다(굽지 않았거나 이름을 잃었다) → red.

즉 부재를 **원본/대상**으로 갈랐고, 정상 부재(첫 배포)를 실패로 읽지 않는다(픽스처 P18).

## 3. 실패 픽스처 (`pipeline/selftest.sh` · 16건 → 25건)

도커 껍데기에 `DOCKER_FAKE_STORE`(ref→이미지 ID) 모드와 `tag` 응답을 붙였다.
운영 도커를 부르지 않는다.

| # | 픽스처 | 기대 |
|---|---|---|
| P14·P14b | 정상 재부착 (양성 대조군) | GREEN · `:i2` 가 새 ID |
| P15·P15b | `docker tag` 실패 | RED · `:i2` 는 옛 ID |
| P16 | tag 가 **성공을 말했는데 안 붙음** | RED (사후 검증만이 잡는다) |
| P17 | 원본 `:$TAG` 부재 | RED |
| P18 | 첫 배포(`:i2` 부재) | GREEN |
| P19 | 릴리스 태그 미지정 | RED |
| P20 | `deploy.sh` 에 `docker tag … \|\| true` 없음 · `alias_reattach` 호출 있음 | PASS |

**변이 시험 2회.**
- 변이① 옛 모양(무조건 성공)으로 되돌림 → `pipeline selftest: RED (실패 5건 / 25건)` — P15·P16·P17·P19·P20 red.
- 변이② **`|| true` 만 뗀** 상태(사후 검증 없음) → **P16 만 red.**
  = 사후 검증이 실제로 벌어들이는 것이 무엇인지의 실물. 둘 다 복원 후 GREEN.

## 4. 형제 훑기 — `infra/staging/**` · `gates/**`

`|| true` 34자리 · `2>/dev/null` · `set -e` 무력화 · 관대한 기본값(`${VAR:-…}`)을 전수 열거했다.
`I3-BUILD §3` 의 9건과 중복 계상하지 않는다. **새로 판정한 것 = 아래.**

| 자리 | 판정 | 근거 |
|---|---|---|
| `deploy.sh:213` `docker tag … \|\| true` | **결함 — 고침** | 이 항목 본체 |
| `deploy.sh` ⑫ 순서(원장 green 이 재부착보다 앞) | **결함 — 고침** | green 을 적어 놓고 죽는 모양 |
| `rollback.sh` — 롤백 뒤 `:i2` **재부착 없음** | **결함(미수정) — 보고만** | 되돌린 뒤에도 `:i2` 가 걷어낸 이미지를 가리킨다. 같은 무늬이나 **완료 정의 밖**(덧붙이지 않는다). 오케스트레이터 판정 자리 |
| `compose.throwaway.yml` 이 `:i2` 의 **신선도를 재지 않음** | **결함(미수정) — 보고만** | 리허설이 무엇을 리허설하는지 자기 검사가 없다. 완료 정의 밖 |
| `restore/preflight.sh:133` `check-image-digests --record \|\| true` | 의도됨 | 바로 다음 줄 `[ -s "$DIGEST_OUT" ]` 가 실물을 본다 → 실패는 P8 fail 로 나온다 |
| `restore/verify-restored.sh:66` 같은 모양 | 의도됨 | 기록 실패 시 `$NOW` 가 비고 `diff -q` 가 어긋나 ④-b fail 이 난다 |
| `rollback.sh:86` · `deploy.sh:199` `verify-deploy.sh \|\| true` | 의도됨 | 판정은 `$VOK` 가 이미 쥐었다. 이 호출은 **실패 출력 재현용**이다 |
| `restore/rehearsal.sh` 51·88 `up … \|\| true` | 의도됨 | `up` 이 실패하면 그 안에서 `ng` 가 이미 계수한다 |
| `restore/rehearsal.sh` 91·97 `CREATE ROLE`/`GRANT … \|\| true` | 의도됨 | 재실행 대비. 실패하면 뒤의 음성/양성 조회가 red 를 낸다 |
| `backup/*.sh` `find … -delete \|\| true` · `docker rm -f \|\| true` | 의도됨 | 청소·트랩. 판정 경로가 아니다 |
| `grep -c … \|\| true` 7자리 | 의도됨 | `grep` 은 0건에 1 을 낸다. 계수는 뒤에서 판정된다 |
| `shift \|\| true` 2자리 | 의도됨 | 인자 소비. 필수성은 `${1:?}` 가 쥔다 |
| `gates/tools/_lock.sh`·`_venv.sh` 3자리 | 의도됨 | fd 닫기 · 스탬프 읽기. 읽기만 하고 손대지 않았다 |
| `pipeline/approval/approve.sh:33` `rev-parse … \|\| echo unknown` | 의도됨(약함) | 값을 숨기지 않고 `unknown` 으로 **드러낸다.** 다만 `deploy.sh` 는 같은 자리에서 `die` 한다 — 비대칭 1건, 기록만 남긴다 |
| 관대한 기본값 `${VAR:-…}` | 의도됨 | 남은 것은 전부 **신원 기본값**(컨테이너·DB·이미지 이름)이지 합격선이 아니다 |

## 5. 수치 · 미확인

- `pipeline/selftest.sh` — 16건 → **25건** GREEN. `verify/selftest.sh` — **22건** GREEN(불변).
- `gates/run.sh work-item-consistency` — **불일치 11건**(기준선 동일). `planning-freshness` — green.
- `[미확인]` — 실물 배포 회차에서의 동작. 배포 실행이 이번 경계 밖이라 껍데기 픽스처로만 쟀다.
  푸는 법 = 다음 실배포 회차에서 ⑫-a 로그와 원장의 `별칭재부착GREEN` 표기를 확인한다.
- `[미확인]` — `rollback.sh`·`compose.throwaway.yml` 두 형제의 처리. 완료 정의 밖이라 손대지 않았다.
