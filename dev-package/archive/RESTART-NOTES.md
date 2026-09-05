# RESTART — 옮겨 온 경위·실측 서술

> **`dev-package/RESTART.md` 에서 옮겨 온 긴 경위·실측 문단이다** (2026-09-05 문서 정리 회차).
> **한 글자도 고치지 않았다.** 원 문서 줄 번호를 함께 적는다(정리 직전 판 기준 · 459줄).
> 부팅 절차와 env 키 표는 `RESTART.md` 에 그대로 있다 — 여기 있는 것은 **왜 그렇게 됐는가**다.

---


<!-- 원 RESTART.md L44 -->
> 원장(`~/colab-v2-releases/release-ledger.tsv`)은 `deploy.sh` 가 배포마다 append 하므로 **문서보다 늦게 낡지 않는다.**

<!-- 원 RESTART.md L45 -->
> 형식 = 탭 6칸(`시각·종류·SHA·태그·판정·비고` — `infra/staging/pipeline/lib.sh`). `awk` 는 `deploy`＋`green` 행의 **태그 칸**만 읽는다.

<!-- 원 RESTART.md L46 -->
> **원장에 green 행이 없으면** `awk` 가 1 을 반환하고 변수가 빈 채로 남는데, 그러면 `compose.i2.yml` 의 `${COLAB_RELEASE_TAG:?}` 가 거부한다 —

<!-- 원 RESTART.md L47 -->
> 즉 **뜨지 않는다.** 기본값·별칭으로 조용히 떨어지는 경로가 없다(2026-08-29 확인 = 빈 값에서 compose 거부).

<!-- 원 RESTART.md L48 -->
> ／ 2026-08-29 실측 = 이 한 줄의 출력 `30b3e0a7b3f3` · `LAST-SUCCESS.txt` 의 태그와 같다 · 그 태그로 이미지 6종 전부 존재.

<!-- 원 RESTART.md L49 -->
> ／ **막히면** 아래를 그대로 쳐도 된다(**이 값은 2026-08-29 시점이고 다음 배포 뒤에는 낡는다**):

<!-- 원 RESTART.md L50 -->
> `COLAB_RELEASE_TAG=30b3e0a7b3f3 docker compose -f infra/staging/compose.i2.yml --env-file ~/.colab-v2-staging.env up -d`


<!-- 원 RESTART.md L53 -->
> `I3` 첫 실배포 이후 `compose.i2.yml` 의 앱 6종이 이미지를 `${COLAB_RELEASE_TAG:?}` 로 요구한다.

<!-- 원 RESTART.md L54 -->
> **그 값을 넣는 자리는 `deploy.sh:77` 하나뿐이고 env 파일에는 없다** — 2026-08-29 실측

<!-- 원 RESTART.md L55 -->
> (`grep -c '^COLAB_RELEASE_TAG=' <env 파일>` = **0** · 값은 출력하지 않았다).

<!-- 원 RESTART.md L56 -->
> 즉 **종전 명령 그대로는 compose 가 거부하고 아무것도 뜨지 않는다.**

<!-- 원 RESTART.md L57 -->
> **현재 서빙 태그 = `30b3e0a7b3f3`**(2026-08-29 실측 · `docker ps` 의 앱 5종 이미지 태그).

<!-- 원 RESTART.md L58 -->
> 다음 배포 뒤에는 **원장 `~/colab-v2-releases/release-ledger.tsv` 의 마지막 green `deploy` 행**이 그 값이다.

<!-- 원 RESTART.md L59 -->
> ⚠ **별칭 `i2` 로 대신하지 않는다** — 별칭 재부착이 실패를 삼키는 결함이 열려 있어(`03-HANDOFF §4 #45` · 항목 `X-6`)

<!-- 원 RESTART.md L60 -->
> **옛 이미지가 뜨고도 정상으로 보일 수 있다.** 릴리스 태그를 명시한다.

<!-- 원 RESTART.md L61 -->
> ／ 이전 ~~`docker compose -f infra/staging/compose.i2.yml --env-file ~/.colab-v2-staging.env up -d`~~ (**낡았다**)


<!-- 원 RESTART.md L63 -->
> ⛔ **⟨개정 2026-08-29 · `PLAN-SoT §9 〈186〉`⟩ `COLAB_RELEASE_TAG=prev` 로 띄우지 마라 — 스키마 정합이 보장되지 않는다.**

<!-- 원 RESTART.md L64 -->
> `:prev` 는 **원장에 없는 수동 빌드본**(2026-08-27)이다(`§9 〈185〉-㉷`-⑵). 현행 릴리스 `30b3e0a7b3f3` 의 migrator 가

<!-- 원 RESTART.md L65 -->
> 스키마를 이미 앞으로 옮겼고, 마이그레이션은 **forward-only** 라 되돌리지 않는다(`〈168〉-㉲`).

<!-- 원 RESTART.md L66 -->
> 즉 `:prev` 로 띄우면 **구코드 ↔ 신스키마** 로 붙는다 — 그 조합이 맞는다는 증거가 없다.

<!-- 원 RESTART.md L67 -->
> **되돌릴 세대는 실질 2세대가 아니라 1세대다** — 릴리스 태그와 별칭 `i2` 는 **같은 이미지**를 가리키고,

<!-- 원 RESTART.md L68 -->
> 나머지 하나(`:prev`)가 위의 정합 미보장본이다. 낙관적으로 세지 않는다.


<!-- 원 RESTART.md L163 -->
  > ⭑ **⟨개정 2026-08-29 · `PLAN-SoT §9 〈185〉-㉲`⟩ 이 줄은 이제 참이다.** 2026-08-29 배포에서

<!-- 원 RESTART.md L164 -->
  > `cloudflared` 가 **재생성되며 선언이 적용돼 `healthy`** 가 됐다(실측 — 8개 전부 `healthy`).

<!-- 원 RESTART.md L165 -->
  > ⚠ **함정 하나를 남긴다** — 선언은 `cloudflared tunnel --metrics 127.0.0.1:20241 ready` 이고

<!-- 원 RESTART.md L166 -->
  > (distroless 라 `CMD-SHELL` 을 못 쓴다) **`--metrics` 를 `ready` 뒤에 놓으면 오류를 내면서 종료코드 0** 이다.

<!-- 원 RESTART.md L167 -->
  > 아무것도 안 보는 헬스체크가 되고, 그건 이 레포의 대표 실패형이다.

<!-- 원 RESTART.md L168 -->
  > ／ 이전 원문 —

<!-- 원 RESTART.md L169 -->
  > ⚠ 2026-08-28 이전에는 이 줄이 **참이 아니었다.** `cloudflared` 만 헬스체크 선언이 없어

<!-- 원 RESTART.md L170 -->
  > 실물은 7개만 헬스체크를 가졌고(실측 8개 중 7개 `healthy`, cloudflared 는 「헬스체크없음」),

<!-- 원 RESTART.md L171 -->
  > `verify-deploy.sh` ② 가 구조적으로 RED 를 냈다. `compose.i2.yml` 에 `cloudflared` 헬스체크를

<!-- 원 RESTART.md L172 -->
  > 선언해 고쳤다 — **선언은 다음 배포에서 컨테이너가 재생성될 때 적용된다.** 그 전까지는

<!-- 원 RESTART.md L173 -->
  > 돌고 있는 컨테이너가 옛 선언이라 이 줄이 여전히 거짓이고 판정기도 RED 다.

<!-- 원 RESTART.md L249 -->
> **참고 — staging 실물도 같이 쟀다(2026-08-30 · 읽기 전용).** `schema-diff` 두 체인 다 **드리프트 0**,

<!-- 원 RESTART.md L250 -->
> `autometa-loss` 대조 대상 **0건**(⭑ 이 값은 **stage 2 배포 전**이라 낡았다 — 2026-08-31 재측 = 발행 3 · 반영 3 · 미반영 0), `preview-tile-slot` 지도 타일 **0건**. 위 게이트 전용 DB 로 잰 값과 같은 결론이다.

<!-- 원 RESTART.md L252 -->
#### ⭑ ⟨개정 2026-08-31 · `PLAN-SoT §9 〈235〉`⟩ ㉯ **이제 선언한다** — `COLAB_PREVIEW_TILE_DIR`


<!-- 원 RESTART.md L254 -->
> ⭑ **닫혔다.** 미리보기 볼륨을 **이름은 그대로 둔 채**(백업이 이름으로 문다) **호스트 경로에 바인드된 named volume** 으로 바꿨고,

<!-- 원 RESTART.md L255 -->
> 그 경로를 `~/.colab-v2-staging.env` 의 `COLAB_STAGING_PREVIEWS_DIR` 과 `~/.colab-v2-test.env` 의 `COLAB_PREVIEW_TILE_DIR` **두 자리에 같은 값**으로 적었다.

<!-- 원 RESTART.md L256 -->
> **실측** = 2026-08-31 재배포 뒤 그 자리에 지도 타일 1건이 놓였고 게이트 `preview-tile-slot` 이 **green** 이다. 이관은 sha256 집계로 대조했다(39 = 39).

<!-- 원 RESTART.md L257 -->
> ⚠ ~~**`autometa-loss` 는 아직 red 다 — 그러나 사유가 바뀌었다.** 「stage 2 가 안 돌아서」가 아니라

<!-- 원 RESTART.md L258 -->
> **「이 게이트가 읽는 적용 DB 에 접수분이 구조적으로 0건이라서」**다(staging 실물로 재면 green — 발행 3 · 반영 3 · 미반영 0). **`03-HANDOFF §4` #50.**~~

<!-- 원 RESTART.md L259 -->
> ⭑ **⟨2026-08-31 해소 · Ted 판정 `〈237〉`⟩ 닫혔다.** 대조 정본을 **staging 실물**로 옮겼다 — 아래 `㉰`. `autometa-loss` **green**.

<!-- 원 RESTART.md L260 -->
> ／ **종전 문면은 지우지 않는다** — 아래가 그것이다.


<!-- 원 RESTART.md L262 -->
##### ／ 이전 ⟨2026-08-30⟩ 아직 선언할 수 없는 값


<!-- 원 RESTART.md L264 -->
`preview-tile-slot` 은 **자리(미리보기 산출물 루트)** 를 받아야 판정으로 넘어간다. 그런데 그 자리가 **아직 없다.**


<!-- 원 RESTART.md L266 -->
- 배포의 워커에 `COLAB_WORKER_STAGE2`·`COLAB_WORKER_PREVIEW_DIR` 이 **둘 다 없다**(`docker inspect` 실측).

<!-- 원 RESTART.md L267 -->
- 유일한 미리보기 볼륨은 `viz-render` 의 렌더 산출물 자리이고, **도커 내부라 게이트를 돌리는 사용자가 못 읽는다.**

<!-- 원 RESTART.md L268 -->
- 그래서 **없는 자리를 지어내지 않는다.** `PV-1` 이 그 볼륨을 호스트 경로로 내주면 그때 이 값을 적는다.


<!-- 원 RESTART.md L270 -->
> ⭑ **⟨증보 2026-08-30 · 워크트리 `lane-pv1`⟩ 위 세 줄 중 첫 줄이 닫혔다 — 나머지 둘은 그대로다.**

<!-- 원 RESTART.md L271 -->
> **배포 선언을 붙였다** — `infra/staging/compose.i2.yml` 의 `pipeline-worker` 에

<!-- 원 RESTART.md L272 -->
> `COLAB_WORKER_STAGE2: "on"` · `COLAB_WORKER_PREVIEW_DIR`(= `viz-render` 의 `COLAB_VIZ_PREVIEW_DIR` 과 같은 값) ·

<!-- 원 RESTART.md L273 -->
> `previews` 볼륨(**쓰기**). 회귀는 시험이 진다(`services/pipeline-worker/tests/test_stage2_deployment_declaration.py` 5건).

<!-- 원 RESTART.md L274 -->
> ⚠ **그래도 이 값은 아직 못 적는다 — 이유가 하나 더 있었다.** 배선이 트리에 있는 것과 **도는 배포에 있는 것**은 다르고

<!-- 원 RESTART.md L275 -->
> (재배포가 아직이다), 재배포를 해도 **미리보기 볼륨은 named volume 이라 게이트 사용자가 못 읽는다** —

<!-- 원 RESTART.md L276 -->
> 실측 = `docker volume inspect` 가 주는 마운트 지점이 **`Permission denied`**. 호스트 경로로 내주려면 볼륨 형태를

<!-- 원 RESTART.md L277 -->
> 바꿔야 하고 그것은 백업 범위를 함께 건드린다. **판정 사항으로 올렸다 — `03-HANDOFF §4` #49.**

<!-- 원 RESTART.md L278 -->
> **빈 임시 디렉터리를 지어내지 않는다는 위 판단은 그대로 둔다.**


<!-- 원 RESTART.md L280 -->
⚠ 같은 이유로 `autometa-loss` 도 **대조 대상 0건**이다 — 워커가 stage 1 만 돌아 `file.header-parsed` 가

<!-- 원 RESTART.md L281 -->
발행되지 않는다. **둘 다 「입력을 안 줘서」가 아니라 「stage 2 가 아직 안 돌아서」 red 다.**


<!-- 원 RESTART.md L303 -->
⭑ **⟨개정 2026-08-29⟩ `services/ai-service/.venv` 를 세웠다.** 실측 = 환경 없이 `72 passed · 26 errors` · 위 env 를 채우면 **98 passed**.

<!-- 원 RESTART.md L304 -->
／ 이전 ~~`services/ai-service/.venv` 는 없다 — 4개 서비스 중 유일하게 빠져 있다~~. 세우는 줄 (`services/ai-service` 에서):

<!-- 원 RESTART.md L312 -->
> ⭑ **`autometa-loss` 는 이제 위 ㉮ 의 적용 DB 를 읽지 않는다.** 대조 정본은 **staging 실물 platform DB** 다.

<!-- 원 RESTART.md L313 -->
> **왜** — 이 게이트의 질문이 「**실제로 접수한 것 중 메타가 빠진 것이 있는가**」이므로 정답지가 실물이어야 한다.

<!-- 원 RESTART.md L314 -->
> ㉮ 의 적용 DB 는 `schema-diff` 와 **공유하는 스키마 전용 일회용 DB** 라 업로드·데이터셋이 **영영 0건**이고,

<!-- 원 RESTART.md L315 -->
> 「대조 대상 0건도 red」가 이 게이트의 설계이므로 **그 배선으로는 어떤 회차에도 green 이 될 수 없었다.** 그것이 `#50` 이었다.


<!-- 원 RESTART.md L337 -->
> ⛔ **`COLAB_PG_NETWORK` 를 전역에 두는 길은 여전히 막혀 있다**(앞 ㉮ 의 세 함정 중 셋째).

<!-- 원 RESTART.md L338 -->
> 이 배선은 그 길을 쓰지 않는다 — **호스트에서 staging 망의 DB 에 직접 닿는다**(2026-08-31 실측).

<!-- 원 RESTART.md L339 -->
> 그래서 `db-selftest` 는 뒤집히지 않는다(실측 = green).

<!-- 원 RESTART.md L340 -->
> ／ **실측 2026-08-31** — 이 선언으로 `autometa-loss` **green**: 발행 **3** · 반영 **3** · 면제 **0** · 미반영 **0**.

<!-- 원 RESTART.md L341 -->
> staging 스택 **무접촉**(8/8 healthy · 쓰기 0건 · 재배포 0건).



<!-- 원 RESTART.md L346 -->
> **왜** — 연구실 경계(`FORCE ROW LEVEL SECURITY` · 공개 스키마 **21 표** 실측)가 걸리는 롤로 원장을 조회하면

<!-- 원 RESTART.md L347 -->
> **예외가 아니라 0 이 돌아온다.** 0 은 「없다」와 모양이 같아서, 그 0 을 「데이터 없음」으로 읽은 사고가 실제로 났다.

<!-- 원 RESTART.md L348 -->
> 그래서 이 게이트는 세기 전에 **롤을 판정한다** — 관리자 롤이 아니면 red · **경계 롤로 같은 질의를 한 번 더 돌려

<!-- 원 RESTART.md L349 -->
> 값이 갈리는지**를 본다. 갈리지 않으면 경계가 아무것도 가르지 못한 것이므로 그것도 red 다.


<!-- 원 RESTART.md L355 -->
- ⚠ **`COLAB_AUTOMETA_STAGING_DB_URL` 과 겹쳐 쓰지 않는다 — 둘은 다른 것이다.**

<!-- 원 RESTART.md L356 -->
  앞 `㉰` 은 **누구로 붙어서 어느 DB 를 세는가**(관리자 롤 · 읽기 전용 접속 URL)이고,

<!-- 원 RESTART.md L357 -->
  이 `㉱` 은 **무엇과 대조하는가**(경계 롤 이름)다. 한 변수로 합치면 게이트가 어느 DB 를 보는지 다시 모르게 된다

<!-- 원 RESTART.md L358 -->
  — 변수 겹침으로 게이트가 엉뚱한 DB 를 본 사고가 이미 있었다.

<!-- 원 RESTART.md L359 -->
- **선언된 롤이 정말 경계 롤이어야 한다** — `NOSUPERUSER`·`NOBYPASSRLS`·비소유자.

<!-- 원 RESTART.md L360 -->
  관리자 롤 이름을 여기 적으면 두 조회가 같은 롤로 돌아 값이 같아지고, 게이트가 **그것을 red 로 잡는다.**

<!-- 원 RESTART.md L361 -->
- **면제·스위치가 없다.** 「이 환경에서는 롤 검사를 건너뛴다」는 경로를 두지 않았다 (`CLAUDE.md §4`).

<!-- 원 RESTART.md L362 -->
- ／ **실측 2026-09-01** — 이 선언으로 `autometa-loss` **green**: 계수 롤 `rolsuper=true`·`rolbypassrls=true` ·

<!-- 원 RESTART.md L363 -->
  `FORCE RLS` 표 **21** · **경계 대조 = 관리자 롤 `3|3|0|0` ↔ 경계 롤 `0|0|0|0`(갈렸다)** ·

<!-- 원 RESTART.md L364 -->
  발행 **3** · 반영 **3** · 면제 **0** · 미반영 **0**. staging 스택 **무접촉**(쓰기 0건 · 전 조회 `BEGIN READ ONLY … ROLLBACK`).

<!-- 원 RESTART.md L393 -->
> ／ **실측 2026-09-04**(호스트 재부팅 45분 뒤) — 재부팅 직후 `docker ps -a` 에 `a2_pg`·`ai_pg` 가 **둘 다 없었고**

<!-- 원 RESTART.md L394 -->
> `schema-diff` 가 `Host is unreachable` 로 red 였다. 위 순서대로 다시 세운 뒤

<!-- 원 RESTART.md L395 -->
> `schema-diff` · `migration-single-head` · `rls-effect` · `rls-effect-selftest` · `db-selftest` **다섯 다 green**,

<!-- 원 RESTART.md L396 -->
> `autometa-loss` · `preview-tile-slot` · `artifact-ownership` **셋도 green**.

<!-- 원 RESTART.md L397 -->
> **staging 스택 무접촉**(8/8 healthy · 재기동 0회 · 쓰기 0건).

<!-- 원 RESTART.md L398 -->
> ／ 전량 `./gates/run.sh all -j 1` = **`── 계 : green 50 / red(판정) 0 / red(준비) 0`**.

<!-- 원 RESTART.md L399 -->
> ⚠ 앞선 회차는 `service-tests-core-api`·`rls-effect-selftest` 둘이 red 였다 — **둘 다 간헐이다**

<!-- 원 RESTART.md L400 -->
>   (단독 재실행에서 각각 green · `service-tests-core-api` 는 같은 env 로 4회 중 3회 red · 1회 green ·

<!-- 원 RESTART.md L401 -->
>   실패 케이스가 매번 갈리고 계수도 7·7·9 로 달랐다). **간헐을 green 으로 적지 않는다 — 재실행한 사실과 함께 적는다.**
