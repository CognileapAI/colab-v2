# Stage 2 상태 마감 실측 — 항목 셋 (2026-08-30)

／ 브랜치 `wt/lane1-measure` · `main` 병합 = fast-forward(`cfc98e3`) · 운영 스택 무접촉(읽기 전용 조회만)
／ 판정의 정본 = `dev-package/work-items.yaml` · 판정자 = 게이트 `work-item-consistency`

---

## 0. 지시문과 레포의 차이 1건

지시문이 가리킨 `dev-package/sessions/STAGE2-MAP-20260830.md` 는 **없다**(`sessions/` 전수 확인 · 최신 지도는 08-28·08-29 판).
지도를 근거로 쓰지 않고 **실물 증거로만** 판정했다 — 지도는 보고서이고 증거가 권위다.

## 1. 전범위 백업 — 완료 정의 4행 전건 충족 · `partial` → `done`

근거 회차 = `~/colab-v2-backups/staging-backup.log` `2026-08-30T03:30:02`~`03:30:38`
(**크론 무인** · `crontab` `30 3 * * *` → `run-scheduled.sh backup-full.sh` · 본 체크아웃)

| 행 | 요구 | 실측 |
|---|---|---|
| ⑴ | 한 회차가 platform · ai · 볼륨 둘 산출 · 요약줄 GREEN | platform 27,379 B(표 23 · 행 389) · ai 5,132 B(표 6 · 행 91) · `vol-uploads` 341,527,870 B · `vol-previews` 6,472,714 B · 요약줄 `전범위 백업 GREEN — 원장 2 프로파일 ＋ 볼륨 2 개 · 보관처 규약 밖 파일 0` |
| ⑵ | 볼륨별 최소 건수 합격선 통과 | uploads `V6 135건 >= 67` · previews `V6 39건 >= 19`. 합격선 실물 `volume-lib.sh:33-34` = 67·19 이고 `config.example.env:74-75` 가 **같은 값** |
| ⑶ | 미선언·빈 값은 RED | `verify-volume-artifact.sh` V6 3상태 분기 코드 확인 ＋ **픽스처 `VF19` 실행**(미선언이 **오직 V6 로** RED) · `selftest-volume.sh` fixture **24건 전부 기대대로** |
| ⑷ | 크론 **무인** 회차 1건이 위 셋 만족 | `LAST-SUCCESS.txt` `2026-08-30T03:30:38+0900 backup-full.sh OK` — 전일 `08-29 03:30:41` 에 이어 **2회 연속** |

⚠ previews 의 `SKIP V5`(오라클 `none`)는 **승인된 명시 면제**이고 요약줄이 건수를 드러낸다 — **합격선 V6 는 건너뛰지 않고 실제로 쟀다.**

## 2. 별칭 재부착 실패 삼킴 — 완료 정의 2행 전건 충족 · `open` → `done`

- ⑴ 삼킴 구문 **전수 부재** — `infra/staging/**` 의 `docker tag` 5자리 중 무조건 성공 경로 **0건**(`deploy.sh:110` 은 `|| abort`, 나머지는 주석). 판정은 `pipeline/lib.sh:175 alias_reattach()` 의 종료코드 ＋ 사후 `image inspect` **이미지 ID 대조** · 호출 자리 `deploy.sh:225` 는 **원장 green 앞** · `rollback.sh:120` 도 같은 함수 재사용
- ⑵ 실패 픽스처 **실행** — P15·P16·P20 ＋ 양성 대조군 P14·P18 ＋ P26 · `pipeline selftest GREEN (54건)` ＋ `verify selftest GREEN (22건)`
- ⭑ **껍데기가 아니라 실배포로 행사됐다** — 2026-08-30 배포 회차가 별칭 재부착을 실제로 돌렸고 원장이 `별칭재부착GREEN digest이력=6종` 을 적었다(`release-ledger.tsv` `10:41:50+0900 · cfc98e302ae4 · green`) · 대조 실물 = `image-digest-ledger.tsv` **6행**(6종 전건 · 대상 0건이 아니다). 블로커 `#45` 가 「다음 실배포에서 갈린다」고 적어 둔 그 회차다
- ⚠ 남는 `[미확인]` = **실롤백 회차 1건** · 완료 정의 2행 밖이라 닫는 근거로도 막는 근거로도 쓰지 않았다

## 3. 항목 상태 대장·검사기 — 완료 정의 ⓐ~ⓔ 전건 충족 · `in_progress` → `done`

- ⓐ 대장 **95항목**(84 → 95) · ⓑ `work-item-consistency` **green · 불일치 0**(㈐ 70행 · ㈏ 49건 · ㈑ 33행 · ㈒ 6건 · ㈓ 0건 · 검사 대상 밖 9건 ＋ 항목표 아닌 표 1건을 **요약줄이 드러낸 채** 통과)
- ⓒ `work-item-selftest` **green · 10 케이스**(대조군 1 · red 증명 **9**) — 완료 정의는 「8」로 적혀 있으나 실물은 **9** 다. **정의를 고치지 않는다** — 증명이 **늘어난** 것이지 범위가 줄어든 것이 아니다
- ⓓ **`conflict` 0건** — 이 조건이 이 항목을 닫는 것이다
- ⓔ 배선 3자리(`03-HANDOFF` 머리말 · `CLAUDE.md:119-121` · `gates/README.md`) 실물 확인

### ⛔ 비어 있던 배선 한 자리 — 이 회차가 채웠다

`work-item-consistency` 와 형제 `planning-freshness` 가 **어느 CI 잡에서도 돌지 않았다**(`ci.yml` 전수 확인).
`work-item-selftest` 만 `gate-selftest` 잡의 집합 `selftest` 에 실려 **「판정기가 red 를 낼 수 있다」만 증명**했고,
**정작 판정 자체는 CI 에 없었다.** 증명만 있고 판정이 없으면 **상태 드리프트가 그대로 `main` 에 들어간다** —
「검사기가 통과를 보고했는데 아무것도 검사하지 않은 것」의 한 변종이다.

**신설 = `planning-gates` 잡** (`.github/workflows/ci.yml`)
- 경로 필터 `dev-package/**` ＋ **`gates/**`** — 판정기가 바뀌어도 다시 판정한다
- pyyaml 핀은 `gates/requirements.txt` **하나를 재사용**(판을 두 곳에 적지 않는다 — 갈리면 조용한 쪽이 이긴다)
- **`import yaml` 설치 확인 스텝**을 게이트 앞에 둔다 — 모듈 부재가 게이트 red 로 **위장**하면 원인이 한 겹 멀어진다

## 4. 게이트 실측 (이 회차 · 본 체크아웃)

```
work-item-consistency: 대장 95건 · ㈐ 70행 · ㈏ 49건 · ㈑ 33행 · ㈒ 6건 · ㈓ conflict 0건
work-item-consistency: green — 대장과 산문의 불일치 0
planning-freshness green — 15개 임베드 블록 전부 원본과 일치.
```

⭑ 편집 직후 게이트가 **불일치 2건**(`W-1`·`X-6` 의 `03-HANDOFF §1` 표기)을 **스스로 잡아냈고**,
그 둘을 대장에 맞춰 걷은 뒤 green 이 됐다. **판정자는 기억이 아니라 게이트다** 가 실제로 작동한 자리다.

## 5. 이 회차가 세지 않은 것

- **실롤백 회차의 별칭 재부착** — `[미확인]`. 푸는 법 = 승인된 롤백 회차 1건의 원장·digest 이력 대조
- **`X-6` 형제 탐색** — 대장 `note` 는 `[미확인]` 이라 적고 블로커 `#45` 는 `X6-ALIAS §4` 가 34 자리를 전수 판정해 **해소됐다**고 적는다. **두 산문이 갈린다** — 어느 쪽도 지우지 않았고, 완료 정의 2행 밖이라 판정하지 않았다
- **`planning-gates` 잡의 CI 실행** — 로컬 green 만 쟀다. 실제 CI 회차는 다음 push 에서 처음 돈다

---

## `PLAN-SoT §9` 등재문 (번호 미발급 — 오케스트레이터가 채운다)

> **〈　〉 Stage 2 상태 마감 3건 — 그리고 판정기가 CI 에 없었다** (2026-08-30)
>
> ⑴ **전범위 백업 `done`** — 완료 정의 4행을 **크론 무인 회차**(`2026-08-30 03:30:02`~`03:30:38`)로 전건 실측. 산출물 4종 · 요약줄 `전범위 백업 GREEN` · 볼륨 합격선 uploads `135 >= 67` · previews `39 >= 19`(합격선 실물 `volume-lib.sh:33-34` ↔ `config.example.env:74-75` 두 자리 일치) · 미선언 RED 성질은 픽스처 `VF19` 로 증명(`selftest-volume.sh` 24건). `LAST-SUCCESS.txt` **2회 연속**.
> ⑵ **별칭 재부착 실패 삼킴 `done`** — 완료 정의 2행 충족. 삼킴 구문 전수 **0건** · 판정은 이미지 ID 대조 · 픽스처 P15·P16·P20 실행(`pipeline selftest 54건` · `verify selftest 22건`). ⭑ **껍데기가 아니라 실배포로 행사됐다** — `2026-08-30T10:41:50 cfc98e302ae4 green` 원장에 `별칭재부착GREEN digest이력=6종` · `image-digest-ledger.tsv` **6행**. 블로커 `#45` 가 예고한 「다음 실배포」가 그 회차다. **남는 `[미확인]` = 실롤백 1건**(완료 정의 밖).
> ⑶ **항목 상태 대장·검사기 `done`** — ⓐ~ⓔ 전건. 대장 95항목 · **conflict 0** · 게이트 green · selftest 10 케이스(red 증명 **9** — 정의의 「8」보다 늘었고 **정의는 고치지 않았다**).
> ⑷ ⛔ **이 회차의 적출 — 판정기가 CI 에서 한 번도 돌지 않았다.** `work-item-consistency`·`planning-freshness` 가 어느 잡에도 없었고, `work-item-selftest` 만 실려 **「red 를 낼 수 있다」만 증명**하고 있었다. **증명만 있고 판정이 없으면 상태 드리프트가 그대로 `main` 에 들어간다.** 신설 `planning-gates` 잡 — 경로 필터에 **`gates/**` 를 포함**(판정기가 바뀌어도 다시 판정) · pyyaml 핀 재사용 · 모듈 부재가 게이트 red 로 위장하지 않도록 설치 확인 스텝 선행.
> ⑸ 편집 직후 게이트가 **불일치 2건을 스스로 잡아** 산문을 대장에 맞춰 걷게 했다 — 이 기구가 설계대로 동작한 실물 증거다.
