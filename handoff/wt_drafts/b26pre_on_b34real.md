# b26pre 사전 실행 -- 실제 B34 코드(T d504784 + K 2eb7e55) 병합 모의 위 (2026-10-06)

작성: 리허설 agent. 실제 저장소·`_drafts` 기존 파일은 읽기만 했다(이 파일만 씀). 모래상자 `/c/g297`(TMP·TEMP·TMPDIR 그 안, 끝나고 삭제).
gate master `7243f28`. 복제 = 작업 트리 저장소 `git -c core.autocrlf=false clone --no-hardlinks --no-local --single-branch`, 두 역할 브랜치는 복제본에만 `refs/b34/{test,code}`로 fetch, origin 제거.

## 0. 결론

**kit 그대로는 `b26pre_launch.sh local`이 pre에서 멈춘다(drift 1건, 원인 = 실제 B34가 sizing_recipe.py docstring을 고침).** 그 한 줄만 모래상자 사본에서 완화하면 나머지는 기대값 그대로다.

| 항목 | 기대 | 실제 B34 병합 모의 | 판정 |
|---|---|---|---|
| `conds` | 0·0·0·0·0 | exit **0·0·0·0·0**, 조건 3 규약 0, approval 줄 gate에 있음, `targets_by_def` 3, 역할 브랜치 없음, rc 0 | 같음 |
| `local` pre | 통과 | **멈춤** `b26pre_launch.sh:246`(engine_since) ← `:198~199` "measured dd60db6 뒤 sizing_recipe.py가 바뀌었다" | **drift** |
| `local`(SR 검사만 'B34 Change-Id 커밋 허용'으로 바꾼 모래상자 사본) | -- | pre OK(SD·SR 바꾼 커밋 2개 = `2eb7e55`·병합 커밋, 둘 다 Change-Id B34), `_approved_ids` 39, plan_tables_hash `16b899d1…` → card: parse_spec_card `('3','test-only','no',['20261001-b26-phase3-cards'],[],11)`, **interface 기존 함수 19** = IFC_FUNCS, 밑줄 0 → final OK | 같음 |
| push(EL4) → `after-push` | 통과 | accept-log 한 줄(`c023eb2 → 4f52ed7`) → after-push OK | 같음 |
| 변이 전 dry run(19 시제품 + B34 병합 코드) | 19 passed | seed 0 **19 passed**, seed 1 **19 passed** | 같음 |
| interface card 행 | 19 | **19**(B34 실제 코드는 def 증감·이름 변화 없음) | 같음 |
| V3 주표 대상(실제 card-35 도구, B1..H4) | 20/20 | **20/20 targeted**, 전체 **301 / not_targeted 2,141**(레코드 2,442, defs 32), scope_proto N2w 대칭차 0, 순서 일치 | 같음 |
| 주표 죽임 | 18, 생존 2(backfill) | **18 죽음**, 생존 = `body[10].body[1]`·`body[12]`(backfill, 실제 B34 줄 SR 11799·11878 = card 11800·11879). 죽인 test 이름이 card 표 1과 같음. 기준·복원 19 passed | 같음 |
| (덤) B26-1 v5 V3(C4B..H5) | 299/2,136 | **299 / 2,136**(2,435, defs 32), 대칭차 0, EQ4: range `const-` targeted, `[0]` `const-` absent | 같음 |
| (덤) B34 계약 test + b26pre 시제품 함께(두 순서, seed 1) | -- | 62 passed / 62 passed(순서 간섭 없음) | 정보 |

실행 중 실제 저장소에서 auditor가 B34 병합 `c851e54`(role/audit, 부모 d504784·2eb7e55, 트레일러 Role: doc·Change-Id B34)를 만들었다. 그 트리 `4d0c2b4`는 모의 병합 `46a2d7f` 트리와 **같다** -- 위 수치는 실제 병합본 엔진 그대로다.

## 1. 실제 B34 코드(2eb7e55)가 바꾸는 것 중 하류에 닿는 것

* **sizing_recipe.py도 바뀐다**(5줄, docstring만): `resolve_stack_layout` docstring 4번(6510~6512, 3줄 → 2줄, 순 -1). def 해시(docstring 제외)는 그대로라 V3 대상은 늘지 않는다(v5 299 그대로). 하지만 **SR 6512 이후 줄이 전부 1 당겨진다**(9363→9362, 9404→9403, 11696→11695, 11800→11799, 11879→11878, 11881→11880).
  card들이 전제한 "B34는 stick_diagram만" / "sizing_recipe 차이 0"이 깨진다. SR 6507~6509(b26pre 계약 5가 인용하는 3번 항목)는 그대로다.
* **stick_diagram.py 줄 이동이 모의(mk_b1)보다 크다**: 모의는 코드 8줄만 지웠다(-4/-8). 실제는 주석 블록(1027~1030, -1)·docstring 다수(1889 -1, 3072 -1, 3354~3365 -2 등)까지 고쳐 SD 9025 → 9011줄(모의 9017).
  dd60db6 줄 → 실제 B34: 1504→1499, 1567→**1562**(card는 B34 사본 1563), 2051→2045, 2114→2108, 2686→2680, 3282→3275, 4529→4515, 6453→6439, 6796→6782, 6892→6878, 6894→6880, 7532→7518. 928은 그대로.

## 2. drift -- file:line (고치지 않았다)

### b26pre
| 파일:줄 | 지금 | 실제 B34에서 |
|---|---|---|
| `b26pre_launch.sh:198~199` | `g diff --quiet "$M" "$H" -- "$SR"` 아니면 멈춤 | **멈춤**(실측). 제안: SD 루프(`:200~203`)처럼 `rev-list --full-history M..H -- SR` 커밋이 전부 `Change-Id $B34ID`이면 통과. 모래상자 사본에서 이 한 줄만 바꿔 위 표 전부 통과 |
| `b26pre_launch.sh:194`(주석)·`:205`(echo "sizing_recipe 차이 0") | SR 불변 전제 | 문구를 'SR·SD 변경 커밋 전부 B34'로 |
| `draft_b26pre.spec.md:471` | "B34 병합(stick_diagram 4 def) … sizing_recipe.py 차이 0 … 예 1567 → B34 사본 1563" | B34는 SR docstring도 고친다(def 해시 불변). 1567 → **1562** |
| `draft_b26pre.spec.md:357·358`(표 1 trace 두 행) | `SD 1567(b34 1563)` | `b34 1562` |
| `draft_b26pre.spec.md:484` | `1567(…, B34 사본 1563)` | 1562 |
| (정보, 고칠 필요 없음) 표 1·작성 전 실측의 SR·SD 줄 | measured `dd60db6` 줄로 적혀 있음 | measured 기준이라 맞다. 실제 B34 위 위치는 §1 이동표 |

### backfill (같은 원인)
| 파일:줄 | 지금 | 실제 B34에서 |
|---|---|---|
| `backfill_launch.sh:213` | `g diff --quiet "$M" "$H" -- "$SR" "$SELFT"` 아니면 멈춤 | **멈춘다**(SR docstring). selftest는 B34가 안 바꾼다. b26pre와 같은 방식(B34 Change-Id 허용) 필요 |
| `backfill_launch.sh:208`(주석) | "B34는 stick_diagram만" | SR docstring도 |
| `backfill_launch.sh:287` | `exp={11800:…,11879:…}` 줄 글 assert(gate `H` = B34 뒤) | **AssertionError** -- 실제 B34 뒤 두 줄은 **11799·11878**(그 줄 글 확인함). 줄 번호를 B34 뒤 값으로 바꾸거나 글로 찾아야 한다(`:282`·`:293`·`:295` 메시지도 11800·11879) |
| `draft_b26_backfill_audit.spec.md:153` | "B34는 stick_diagram의 4 def만 바꾸고 sizing_recipe는 바꾸지 않는다" | SR docstring 1곳(6510~6512) 바뀜. def 해시 불변이라 V3 무관 |
| `b26_backfill_briefs.md:18` | `(가) 비어 있어야(B34는 stick_diagram만…)` | 비지 않는다(`2eb7e55` SR 5줄) |
| `post35_kit/p35_heads.py:120` | REV SR 11800·11879 글 확인 | post-B34 REV면 `BF_error`(11799·11878) |

### B26-1 (참고 -- 이번 실행 범위 밖이지만 실제 코드로 확인)
| 파일:줄 | 지금(모의 b1) | 실제 B34 병합본 |
|---|---|---|
| `b26_1_launch.sh:85` `ALLOW_SR` | P9·backfill만 | B34(`2eb7e55`, Change-Id B34)가 SR을 바꿔 `:136`에서 **멈춘다**(`--no-merges`). `20260930-b34-grammar-explicit` 추가 필요 |
| `draft_b26_1.spec.md:16` 사이트 줄 | SD 1014·1571·1613·2092·2168·3133·3238·3973·4152·4288·4304·4351·4373 | **1014·1570·1612·2090·2166·3130·3235·3967·4146·4282·4298·4345·4367**(13줄 전부 `_RAIL_NETS`/씨앗 줄 확인). SR 2207·4293 그대로(확인) |
| `draft_b26_1.spec.md:30` | "B34 코드 변경만으로 1073 이후 4줄 당겨진다. 예: 1575 → 1571" | 실제 5줄(주석 -1 포함), 1575 → 1570, 뒤로 갈수록 docstring 몫이 더해짐(-6~-14) |
| `draft_b26_1.spec.md:40~44`(인계 표 b1 열) | 2396~2397·2406~2407·2436~2437·4052~4054·3947~3951 | 2394~2395·2404~2405·2434~2435·4046~4048·3941~3945 |
| `draft_b26_1.spec.md:46` | b1 2491·4068 | 2489·4062 |
| `draft_b26_1.spec.md:52` | docstring 3932~3933·2349~2350 | 실제 B34 docstring 위치 3907~3908·2343~2344 |
| `draft_b26_1.spec.md:149` | 4152·4288·4304·4351·4373(b1) | 4146·4282·4298·4345·4367 |
| `b26_scripts/b26v4_head.py:13` `SITE_SD_B1` | 모의 b1 줄 | 실제 B34 트리에서 13줄 중 12줄 불일치 → `_check_sites` **AssertionError**. 실제 줄(위 :16 행)로 바꾸면 H4·C4B·H5 생성 정상(v4 301, v5 299 재현) |
| `post35_kit/p35_heads.py:62`(mk_b1)·`:97`(`assert n == 1`) | REV + mk_b1 | REV가 B34 병합본이면 mk_b1의 `def_replace`가 옛 문장을 못 찾고, B1 = REV라 `n == 1`도 깨진다. b1 = REV archive 그대로 써야 한다(모래상자에서 그렇게 해서 위 수치) |

spec은 이미 "착수할 때 auditor가 실제 병합본에서 다시 잰다"(`draft_b26_1.spec.md:17`)고 적었으므로 B26-1 줄은 정보다. 키트 쪽(`b26_1_launch.sh:85`, `b26v4_head.py:13`)은 동작을 멈추게 한다.

## 3. 방법 메모

* 모래상자: `master` ff d504784 → `merge --no-ff 2eb7e55`("merge 20260930-b34-grammar-explicit", Role: doc·Change-Id B34 -- a17b8bd·5a602d4 선례 형식, 실제 c851e54와 같은 형식) → `audit:` 자리표시(V1~V10 PASS + DRY_RUN, gate_config·pre-receive 경로만 모래상자로). bare 가짜 gate = 실제 `pre-receive`·`gate-runner.py`, 복제본 hooksPath `.githooks` + `.claude/hooks/role_*.py` 복사.
* launch는 `--repo /c/g297/r --state /c/g297/st/… --wt /c/g297/wt`. 원본 그대로 1회(멈춤 확인) → `:198`만 바꾼 사본(`launch_common.sh` 동봉)으로 local·after-push.
* dry run: gate `4f52ed7` archive 사본에 `test_b26pre_existing_paths.py` = `proto_v2_test_b26pre.py` 17(계약 10은 card v3 단언 'Mx1·Mx2 중 정확히 하나') + `proto_test_b26pre_trace.py` 2(card 계약 11대로 `layer1_fallback` 원소 제외), `pytest_gate.ini`·`--gmid-phase=3`.
* V3: `b26_scripts` 사본(경로 치환, `SITE_SD_B1`만 실제 줄) + `b26v4c.py`로 B1(=46a2d7f)·H4·C4B·H5 생성, `post35_kit/p35_v3count.py`(가짜 pytest, 도구 = B1의 `tools/gates`).
* 죽임: H4 id의 문장을 B1 def에서 대응(`rails=` 키워드 제거 ast.dump, 반복문은 머리만, 같은 모양이 둘 이상이면 같은 깊이·가장 가까운 경로 -- finger growth 4개가 여기 해당, 머리 문장 하나가 앞에 끼어 순번 +1)시켜 실제 도구 `mutants`·`_replace_def`로 B1 사본에 같은 연산자 변이 → 시제품 파일만 seed 1.

## 4. 격리

* 실제 저장소: 쓰기 0(HEAD 7243f28, status md5 `76eea762…`, reflog 354 -- 시작·끝 같음). refs 목록 md5만 달라졌다 -- 실행 중 auditor의 `role/audit/20260930-b34-grammar-explicit` → `c851e54`(실제 B34 판정 진행), 이 작업과 무관.
* EL1이 `git -c core.hooksPath=…` 직접 호출을 거부했다(모래상자 log 명령 -- 읽기라 `-c` 없이 다시 실행). 
* `/c/g297` 삭제.
