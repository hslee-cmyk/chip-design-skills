# B26-1 사전 실행 -- 실제 B34 병합본(c851e54) 위 (2026-10-06)

작성: 사전 실행 agent. 실제 저장소는 읽기만 했다(git -C, set -e). `_drafts`는 이 파일만 썼다(launch·carry·spec 수정 없음 -- sha256 앞뒤 같음).
모래상자 `/c/g303`(TMP·TEMP·TMPDIR 그 안, 끝나고 삭제).

## 0. 결론

**멈춤 1건(실제 kit 그대로 돌리면 `pre`에서 멈춘다) + 줄 앵커 이동(spec:15 SD 12줄, 다른 문서 SR 줄 -1).** 그 하나만 모래상자 사본에서 고친 뒤에는 끝까지 통과했다.

| # | 위치 | drift | 근거 |
|---|---|---|---|
| D1 (멈춤) | `b26_1_launch.sh:85` `ALLOW_SR="20260930-p9-kcl-edges 20261001-b26-backfill-interdig-final-audit"` | 실제 B34 code 커밋 `2eb7e55`(Change-Id `20260930-b34-grammar-explicit`)가 **sizing_recipe.py도 바꾼다**(`resolve_stack_layout` docstring 6507~6509, 3줄 → 2줄, 순 -1). `engine_since`가 `[중단] measured 7535799 뒤 확정 순서 밖 커밋 2eb7e55 … SR를 바꿨다`(`b26_1_launch.sh:314`)로 멈춘다. 모의 B34(mk_b1)는 SD만 바꿔서 지난 실행(g282)은 통과했다 | 실제 `local1` 실행 rc 1. 사본에서 ALLOW_SR에 B34 id를 넣으면 통과(아래 §2) |
| D2 (앵커) | `draft_b26_1.spec.md:15` SD 사이트 줄 | 모의 b1 `1014·1571·1613·2092·2168·3133·3238·3973·4152·4288·4304·4351·4373` → 실제 B34 base **`1014·1570·1612·2090·2166·3130·3235·3967·4146·4282·4298·4345·4367`**(13줄 모두 같은 글·같은 def, 1014만 그대로). SR `2207·4293`은 그대로(불변 맞음) | 실제 B34는 docstring·주석 줄 수도 바꿔(1026 주석 -1, 1888 -1, 3071 -1, 3356 -3) 모의보다 -1~-6 더 당겨진다. 모의 줄 목록을 실제 base에 대면 1014 말고 12줄이 사이트가 아니다(`b26v4_head.SITE_SD_B1`의 `_check_sites`가 실패) |
| D3 | `draft_b26_1.spec.md:30` "1073 이후 사이트가 4줄 당겨진다. 예: 1575 → 1571" | 실제: 1575 → 1570(5줄). docstring 몫이 "따로 더해진다"는 문장은 맞다 | 위 표 |
| D4 | `draft_b26_1.spec.md:38~44` 인계 표 b1 열 | 실제 base 줄: 9 `2394~2395`(b1 2396~2397), `2404~2405`(2406~2407), 10b `2434~2435`(2436~2437), 13 `4046~4048`(4052~4054), B40 `3941~3945`(3947~3951); B35 인계 10 `2489`(2491), 14 `4062`(4068); spec:56 `candidates is None` `2414` | 글 일치로 찾음(각 1개) |
| D5 | `draft_b26_1.spec.md:52` docstring 인용 "도달 불가 -- 삭제는 B26-1", 줄 3932~3933·2349~2350 | 실제 B34 구절은 **"도달 불가 -- 삭제는 B26-1/B35/백로그"**(SD 11곳). 두 def 자리 = `propose_device_roles_gap_fill` 3907~3908, `refine_…` 2343~2344(실제 base). 인용 구절은 실제 구절의 앞부분이라 찾기는 되지만 B26-1이 고칠 문안은 이 실제 문구 기준으로 다시 적어야 한다 | `git grep "삭제는 B26-1" c851e54` |
| D6 | `draft_b26_1.spec.md:71~72` SR 줄 | B34 SR 변경(6507~6509, -1) 뒤라 -1: 6881→6880, 6886→6885, 6920→6919, 6931→6930, 6948→6947, 7282→7281, 8003→8002, 8091→8090. 4086·4361·4626·4650·4991·2207·4293은 그대로 | 7243f28 대 모래상자 base 글 대조 |

범위 밖(앞 card 키트, 같은 원인 -- B34가 SR을 바꿈):

| # | 위치 | drift |
|---|---|---|
| E1 (멈춤) | `b26pre_launch.sh:198` `g diff --quiet "$M" "$H" -- "$SR"`(M = `draft_b26pre.spec.md` measured `dd60db6`) | dd60db6..c851e54 SR 차이 있음(exit 1) → b26pre `pre`가 "sizing_recipe.py가 바뀌었다"로 멈춘다. 주석 `:194` "SR 불변"도 틀린다. spec 인용 SR 9363~ 등(6509 뒤)은 -1 |
| E2 (멈춤) | `backfill_launch.sh:213` 같은 `diff --quiet M H -- SR SELFT` | 같은 이유로 멈춘다 |
| E3 (앵커) | `backfill_launch.sh:287·293·295`(+`:19`·`:282` 주석) 수정 후보 `11800·11879` | 실제 B34 위에서는 **11799·11878**(글 그대로). `:287` 단정이 실패한다. `draft_b26_backfill_audit.spec.md:22·27·39·59·70·155`의 SR 줄(11758~11881)도 -1. `post35_kit/p35_heads.py` BF 빌드도 같은 줄 상수 |

## 1. 모래상자 구성(/c/g303)

* `r` = 실제 작업 트리 저장소 `git -c core.autocrlf=false clone --no-hardlinks --no-local --no-checkout`(+ autocrlf false 설정 뒤 checkout), master `7243f28`. 실제 `role/audit/20260930-b34-grammar-explicit`(c851e54)는 이 복제본에만 fetch.
* 선형 스택(빈 hooksPath):
  1. `master` ff → `c851e54`(실제 B34 병합, 첫 부모 d504784)
  2. `4c89a4e` audit: B34 판정 기록 자리표시(V1~V10 PASS + DRY_RUN) + gate_config·pre-receive 경로만 모래상자로
  3. `2303d62` test(b26pre): 시제품 `proto_v2_test_b26pre.py`·`proto_test_b26pre_trace.py` 무수정 복사 → `39a0f9b` 자리표시
  4. `c556a0c` test(backfill): `proto_bf_test.py` → `cfea82b` code: SR `_backfill_interdig_ok(result)` 두 줄(글로 찾음 = **11799·11878**) 삭제, numstat `0 2` → `01c839f` 자리표시
* bare `gate.git` = 실제 `pre-receive`·`gate-runner.py`(EL4), accept-log 2줄. `r`: remote gate, hooksPath `.githooks`(EL3), `.claude/hooks` 복사.
* 참고(실행 중 실제 gate 이동): 실제 gate master가 `7243f28` → `2183f2e`(c851e54 ff + B34 판정 기록, V1~V7·V10 PASS, V8·V9 N/A, `.ai/verification/`만 추가)로 움직였다. 모래상자 스택 모양(ff + audit)과 같고 엔진 차이 없음.
* 시제품 test(실제 B34 위, gate ini, `--gmid-phase=3`): `39a0f9b`(b26pre 병합, backfill 전) **19 passed + bf 2 failed**(red, b26pre test-only base PASS), `01c839f`(backfill 뒤) **21 passed**(green).

## 2. b26_1_launch.sh

| 단계 | 결과 |
|---|---|
| `conds`(실제 kit) | `1:0 … 9:0 10:128 11:0`, D2 = 규약 전체 = 0, b40-reason-key만 gate에 없음 → exit 3(기대) |
| `local1`(실제 kit) | **멈춤 D1** (`:314`) |
| `local1`(사본, ALLOW_SR + B34 id 한 줄만 다름) | pre OK: SD·SR·P9T 변경 커밋 5개 = `2eb7e55` SD·SR(B34), `a410f31` SD(P9), `cfea82b` SR(backfill), `6bf510b` P9T. 새 test 없음, P9 시그니처 test 2개 있음. `_approved_ids` 39, plan_tables_hash `16b899d1…`(그대로). appr: 2614 B, decision `U4-B40-UNAVAILABLE-REASON-KEY`, final-appr OK |
| push #1 → `after-push-appr` | EL4 통과 / 조건 1~11 전부 0 |
| `local2` | approval 3건 parse OK, parse_spec_card `('3','red-green','no',[3건],[],12)`, **interface 행 46 = IFC_ROWS(신규 2)**, 371줄, final OK |
| push #2 → `after-push` | EL4 통과 / B1 = S `8256710` |

## 3. 1차 시도 모의 + carry `check`(실제 kit 그대로)

* T1 `2592b84`(Role: test): P9 시그니처 test 2개를 승인 기록 4 '범위 설명'대로 + 인벤토리 probe test(`test_p35_inventory_probe.py`). EL3 통과.
* K1 `08e704d`(Role: code) = T1 + v5 head를 **실제 base 위에서** 빌드(`b26v4_head.build_head("v4")` + `b26v4c.cleanup` C1·C2 -- C4는 base에 이미 있음). `SITE_SD_B1`을 D2의 실제 13줄로 바꿔야 빌드된다(원래 목록은 `_check_sites` 실패). 바뀐 파일 SD·SR 2개(108+/83-).
* `base_check.json` = 게이트 캐시 `weakening_diff.py --base B1 --head T1`: **FAIL, 발견 정확히 2 = 두 시그니처 test**, diff_paths = [P9 경로], diff_hash `d18daf1c552e5071…`(g282 값과 다름 -- B1·T1이 다르니 당연).
* V3 = 게이트 캐시(실제 card 35 도구) `mutate_changed.py --base B1 --head K1`, 가짜 pytest(`range(i + 0, len(chains))`만 생존): exit 1, **mutants 299 / not_targeted 2,136**(레코드 2,435), defs 32, scope_proto N2w 대칭차 0, `--out` 순서 일치, **생존 1 = U3** `stick_diagram:find_differential_pair_candidates:const-:body[8].body[3].body[1].body[0].iter.args[0].right`. 소요 8분.
  * 묶기 해시 = **`3fe8fe6646e677c9…`** -- g282(모의 B34)의 `cdab7b02…`와 다르다. 실제 B34가 이 def docstring을 바꿨기 때문(묶기 해시 = def 전체 ast.dump, docstring 포함). 기록 5 target은 어차피 1차 실측값으로 채우므로 kit 수정은 필요 없다. 미리 적어 둔 해시가 있으면 쓰지 말 것.
* `b26_1_carry.sh check`(실제 kit, 옵션만 모래상자): **rc 0** -- dispute 없음, V5 base_check = 재실행 = diff-hash, 발견 단위 = 두 시그니처 test, V3 생존 1 = U3, K1 def 묶기 해시 따로 계산 일치, 노드 = `range(… + 1, …)`의 1.

## 4. 그대로인 것

* spec 경로 `5f643a9`·design 05·`role_hooks.py`·`merge_gate.py` 인용: B34는 tools·docs를 바꾸지 않는다(diff 0).
* SD 32행 `from __future__ import annotations` 그대로. 승인 기록 4 초안 21행 P9 병합 sha는 이미 `93b18db`(지난 n1 해소됨).
* V3 299(spec:333·362·396), IFC_ROWS 46(`b26_1_launch.sh:92`), P9 시그니처 test 이름(launch `:146`, carry `:92`), carry 핀 2개.

## 5. 격리

* 실제 저장소: 이 작업은 쓰기 0(fetch는 복제본 안으로만). status md5 앞뒤 같음 `76eea762…`. HEAD·reflog·refs 변화(master/gate → `2183f2e`, B34 role 브랜치 3개 삭제)는 실행 중 오케스트레이터의 B34 병합이다.
* `_drafts` launch·carry·spec·승인 초안·fill_u3·launch_common sha256 앞뒤 같음. `_drafts`에 상태 파일·보관 디렉터리 생기지 않음.
* `/c/g303` 삭제.
