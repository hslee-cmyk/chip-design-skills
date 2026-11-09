# backfill 결함 card `20261001-b26-backfill-interdig-final-audit` -- 착수 키트(세 역할 브리프 + 착수 확인)

작성 2026-10-01. 기준: gate `master` `0f23786`(`a796468`과 `tools/`·`skills/`·`workspaces/` 차이 0 -- `git diff --quiet a796468 0f23786 -- tools skills workspaces` 같음).
사용자 결정: U-BF '결함으로 고침 (Recommended)'(2026-10-01 19:19 KST) -- 승인 기록 `20261001-b26-backfill-interdig-fix`(decision, 초안 `approval_20261001-b26-backfill-interdig-fix.md`).
순서: B34 → b26pre(`20260930-b26-pre-test-strengthen`) → **이 card** → B26-1. card `phase: 3`(사용자 결정 Q-B34-PHASE "phase 3 + 정정 기록 (Recommended)", 2026-10-01 21:14 KST -- decision 기록 `20261001-b26-phase3-cards`).
**phase 표기(r1 정정)**: 이 키트의 측정·모의(0.3·0.5·0.6, `b26bf_kit/`)는 결정 전(phase 2)에 돌았다. 측정 명령의 `--gmid-phase=2`는 측정 당시 값이고 **판정 명령은 `--gmid-phase=3`**이다(phase 2·3의 test 결과·strict 집합·N/A 허용은 같다 -- 결정 질문 원문의 사실). 키트 스크립트 `sim_launch_bf.sh`(104~119행 `("2", …, [aid])` 기대), `run_fullsuite.sh`·`run_v3_tool.sh`·`v3_replica.py`(`--gmid-phase=2`)는 phase 2 전제 그대로다 -- 다시 돌리려면 `("3", "red-green", "no", [aid, "20261001-b26-phase3-cards"])`·`--gmid-phase=3`으로 바꾼다(이번 판에서 스크립트는 고치지 않았다).
저장소 쓰기·상태 변경 git 없음. 측정·모의는 scratch `C:/g128`(끝나고 삭제)에서만. 스크립트 `_drafts/b26bf_kit/`(결과 사본 `b26bf_kit/out/` -- setup·V3 대상/실행/병합·전체 회귀·library 계측·모의 출력).
대상 산출물: `draft_b26_backfill_audit.spec.md`(재검증·측정 반영판, 직전판 `.spec.v3.md`), `approval_20261001-b26-backfill-interdig-fix.md`(정정판, 직전판 `.v1.md`), 이 문서.

**착수 0단계 실행 = `bash _drafts/backfill_launch.sh --scratch /c/g<번호> local` → push 단독 → `after-push`**(스크립트는 push하지 않는다. 읽기 전용 확인만은 `backfill_launch.sh conds`).
아래 (가)~(아)와 '병합 도구 V3 대상 4'는 그 `pre`·`v3count` 단계가 기계적으로 한다: measured rev = card '작성 전 실측' 머리 '**measured at `<rev>`**'의 마지막 출현 단일 출처(지금 `2183f2e` -- 2026-10-06 착수 재측정), 그 뒤 sizing_recipe.py·selftest 내용이 바뀌었으면(`git diff --quiet <measured> <gate>` -- B34 SR docstring −1은 measured `2183f2e`가 이미 품는다) 멈춤 = (가)(나), b26pre test 있음·이 card test 없음 = (다),
card 머리 approval 줄 두 기록이 gate에 있고 U-BF 기록 blob = 초안 = (라), 착수 조건 1~5(card 본문 명령 그대로, 조건 4·5는 명령 둘) = (마)(바)(사)(아), V3 대상 수 = gate 캐시 `mutate_changed.py`를 scratch 복제본에서 실제로 돌린 `targets_by_def`(4가 아니거나 키가 없으면 멈춤).
`dd60db6` 재확인(card '작성 전 실측' 0, 2026-10-02): 줄 인용 차이 0, 조건 exit 128·128·0·128·128. 남은 것은 V3 card 34·35(조건 1·2), `20261001-b26-phase3-cards`(조건 4 -- B34 0단계 P), B34·b26pre 판정 기록(조건 5). 모래상자 `C:/g170`에서 전 과정 통과(0.6 아래 '2026-10-02 모의').
`2183f2e` 착수 재측정(2026-10-06, B34 병합본 + 판정 기록): B34 code `2eb7e55`가 sizing_recipe.py `resolve_stack_layout` docstring 한 덩어리(6510~6512, 3줄 → 2줄, 동작 무관)를 바꿔 6513행 이후 줄이 전부 −1이다(전수 대조 불일치 0). 그래서 이 문서와 card의 sizing_recipe 줄 인용을 −1로 고쳤다(수정 후보 **11799·11878**). 날짜·rev가 적힌 과거 측정 기록(13행 위, 0.6 '2026-10-02 모의')의 줄은 그 rev 기준 그대로 둔다. 0.1·0.3 표는 측정 사슬이 B34 docstring 변경 전이지만 인용 줄을 `2183f2e` 기준으로 환산해 적었다(글은 같다). 조건 exit 0·0·0·0·128(조건 5의 b26pre 판정 기록만 없음).

**착수 0단계(반드시, 다른 단계 전에 -- 읽기 전용)**: 이 키트는 B34·b26pre가 **아직 gate에 없는** 상태에서 모의 사슬(a796468 + B34 코드 + b26pre 시제품 test)로 쟀다. 착수 때는 두 card가 병합된 gate `master`에서 다음을 다시 돌리고 출력으로 판단한다.
```
R=/c/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills
git -C "$R" diff --stat 2183f2e gate/master -- skills/analog-gmid-design/assets/sizing_recipe.py      # (가) 비어 있어야(b26pre는 test만). 0f23786..2183f2e의 차이는 B34 docstring 1 hunk(6510~6512, 순 −1줄, 동작 무관)뿐이고 이미 card·이 문서 줄 인용에 −1로 반영했다 -- 그 밖의 차이가 나오면 멈추고 다시 잰다
git -C "$R" show gate/master:skills/analog-gmid-design/assets/sizing_recipe.py | sed -n '11757,11758p;11768,11772p;11783,11793p;11797,11801p;11876,11880p'   # (나) 아래 0.1 표와 같은 글
git -C "$R" ls-tree --name-only gate/master -- skills/analog-gmid-design/assets/tests/contracts/ | grep -c 'test_b26pre_existing_paths.py\|test_b26_backfill_interdig.py'   # (다) 1(b26pre 파일만)
git -C "$R" ls-tree --name-only gate/master -- .ai/approvals/ | grep -c 20261001-b26-backfill-interdig-fix   # (라) 1(gate `19eb475`에 올림 -- 2026-10-02 정정, 예전 '0 -- 0.8 D에서 올린다'는 낡음)
git -C "$R" ls-tree -r --name-only gate/master -- .ai/verification/ | grep -c '20260930-v3-changed-stmt-scope'   # (마) 1 이상(V3 범위 card 병합)
git -C "$R" ls-tree -r --name-only gate/master -- .ai/verification/ | grep -c '20260930-v3-exempt-binding'      # (바) 1 이상(V3 면제 묶기 card 병합)
git -C "$R" ls-tree --name-only gate/master -- .ai/approvals/ | grep -c 20261001-b26-phase3-cards               # (사) 1(phase 3 decision 기록 -- B34 순서 0 커밋 전에 올라가 있어야 한다)
git -C "$R" ls-tree --name-only gate/master -- docs/03-analysis/gain-budget-gmid-sizing-20-dead-code-dup/ | grep -c phase2-dod.md   # (아) 1(Phase 2 DoD 기록 -- 판정 PASS인지 파일에서 확인)
```
(가)(나)가 맞으면 card 인용 줄·수정 후보 줄(11799·11878)은 그대로다. 어긋나면 card '의도'·'거부해야 할 입력'의 줄 번호를 다시 재고, `b26bf_kit/v3_targets.py`로 V3 대상을 다시 잰다(0.3).
(다)가 0이면 b26pre가 아직 병합되지 않은 것이다 -- 착수하지 않는다(순서 조건; 0.3의 V3 수치는 b26pre test가 base에 있다는 전제다).
(마)가 0이면 범위 card가 아직 병합되지 않은 것이다 -- 착수하지 않는다(현행 도구로 V3 FAIL, 생존 19 -- 0.3). (마)가 1 이상이면 **병합된** `tools/gates/mutate_changed.py`(`git -C "$R" archive gate/master tools/gates`를 scratch에 푼 사본)의 `changed_defs`·`mutants`로
`base = gate master`, `head = base + 수정 후보(11799·11878 삭제)` 사본에서 이 def의 V3 대상 수를 다시 잰다(0.3 방법, `b26bf_kit/v3_targets.py`의 선택 함수를 시제품 `scope_proto.py` 대신 병합 도구로). **대상이 4가 아니면 멈춘다**(사전 수치 4는 시제품 N2w 기준이다) -- card 'V3' 항목과 이 표를 다시 쓴 뒤 착수한다.
(바)(사)(아) 중 하나라도 아니면 착수하지 않는다(card '결정 필요 항목' 착수 조건 1·3·4).

---

## 0. 착수 확인 결과(오케스트레이터용)

### 0.1 spec card 재검증(gate `master` `0f23786`, archive 사본 `C:/g128/gm`)

| 확인 | 결과 | 조치 |
|---|---|---|
| 엔진 `a796468` → `0f23786` | `tools/`·`skills/`·`workspaces/` 차이 0 | 줄 번호 그대로 |
| 인용 줄(sizing_recipe.py) | def 머리 11711, docstring `interdig_ok` 11757~11758, backfill 주석 11768~11769·건너뜀 11771~11772, `_finalize` 앞 주석 11783~11785·정의 11786~11793, 루프 안 수리 11797·backfill **11799**·`if result.ok:` 11800·성공 분기 `_finalize` 11801, 루프 뒤 수리 11876·backfill **11878**·`_finalize` 11879 | 그대로 |
| 소비처 | `git grep interdig_ok -- '*.py'`: 엔진 자신 + `A/tests/unit/test_selftest_sizing_recipe.py:1480`(`is not None`)뿐. 비코드 히트(`.ai/context.md` 6, `.ai/verification/20260930-p9-kcl-edges/` AST 덤프 2)는 소비처 아님 | 소비처 문장에 `-- '*.py'` 범위를 적음 |
| 엔진 안 호출부 | `run_matching_safety_with_finger_growth(` 호출은 `optimize_full_circuit_budget` 9368 하나(`_lut_by_kind`가 있을 때), 결과는 9397에서 `pr["relaxed_pairs"]` → `pipeline_result` | 그대로 |
| `.ai/context.md` 1558~1561 | 세션17 '알려진 한계'(`interdig_ok=False` 실제 사례 self-test 미확인) 그대로 | -- |
| 이름 충돌 | `test_b26_backfill_interdig.py`·`b26bf` -- `A/` 0건 | -- |
| `A/tests/contracts`의 `interdig_ok`·`relaxed_pairs` | 0건 | -- |
| 계획서·설계·레지스트리 소비자 | `interdig_ok`·`run_matching_safety_with_finger_growth` 0건(레지스트리 159행 `_try_interdigitation_table_match`는 다른 함수) | -- |
| B26-1 접점 | B26-1 초안 '사이트 교체 -- SD 13줄 + SR 2줄'의 SR 2줄 = 이 def의 두 `repair_matching_safety` 호출(11797·11876) | 인계 문장 그대로 |
| 승인 기록 초안 | 질문 원문·선택지 설명을 세션 jsonl과 바이트 대조: 원문은 `쟽니다`(질문 1곳 + 선택지 0 설명 1곳, 오타 그대로) -- 승인 기록은 jsonl 원문 그대로 `쟽니다`(오타 보존, 독립 검토 `review_backfill_kit.md` §1 True). 저장소 밖 `_drafts/…` 경로 3곳 | 0.2 |

### 0.2 승인 기록 초안 정정(`approval_20261001-b26-backfill-interdig-fix.md`, 직전판 `.v1.md`)

* 승인 기록은 jsonl 원문 그대로 `쟽니다`(오타 보존) -- 질문 본문 1곳·선택지 0 설명 1곳. 원문 인용은 고치지 않는다(`user_decisions.md` 60행 정정도 jsonl 원문이 `쟽니다`라고 적는다).
* 저장소 밖 경로(`_drafts/b26_backfill_question.md`, `_drafts/review_b26pre.md`, `_drafts/review2_b26pre.md`) 3곳 -- 커밋되는 기록이 가리킬 수 없는 경로라 "질문 준비 문서(저장소 밖 작업 초안)"와 "배경 사실은 spec card `20261001-b26-backfill-interdig-final-audit` '의도'"로 바꿨다. 결정 문장·범위 설명·재검토는 그대로.
* 형식: `---` 시작, LF, BOM 없음, HTML 주석 없음, `merge_gate.py parse-approval` 통과(0.5).

### 0.3 V3 측정(이 card -- 모의 사슬, `b26bf_kit/setup_v3.py`·`v3_targets.py`·`run_v3_tool.sh`·`v3_replica.py`)

모의 사슬(격리 복제본 `C:/g128/sim/r`, origin 없음, 빈 hooksPath):
`P0 = a796468` → `B1 = P0 + B34 코드`(stick_diagram 4 def, `mk_g106.py`와 같은 치환) → `BP = B1 + b26pre 시제품 test`(`proto_v2_test_b26pre.py` → `A/tests/contracts/test_b26pre_existing_paths.py`)
→ `H = BP + 수정 후보(11799·11878 두 줄 삭제) + 이 card 시제품 test`(`proto_bf_test.py` → `A/tests/contracts/test_b26_backfill_interdig.py`), `T = BP + 시제품 test만`.
V3 범위 = `BP..H`(이 card의 base = b26pre 병합본이라는 순서 전제).

변이 실행 = gate `master` 판 `mutate_changed.py`(archive 사본 `C:/g128/gate0`, 캐시와 같은 blob)의 `main`을 `--base BP --head H --gmid-phase=2 --gmid-strict=`(측정 당시 값 -- 판정 명령은 `--gmid-phase=3`)로 실제로 돌렸다(`run_v3_tool.sh` -- 직렬이라 22 변이 뒤 중단).
나머지 75 변이는 같은 도구 함수(`changed_defs`·`mutants`·`_replace_def`·`inventory`·`test_nodeid`)와 같은 pytest 인자로 작업 사본 6개에서 병렬 실행(`v3_replica.py`). 겹친 3 변이의 결과는 도구와 같았다. 인벤토리 기준 실행 통과.

| 범위 규칙 | 바뀐 def | 대상 변이 | 죽음 | 생존 | 판정 |
|---|---|---|---|---|---|
| **현재 도구**(바뀐 def의 변이 전부) | `sizing_recipe.run_matching_safety_with_finger_growth` 하나(인벤토리 71 test) | 97 | 78 | **19** | FAIL(생존 19 -- 전부 이 card가 바꾸지 않은 문장) |
| **N2w**(범위 card `20260930-v3-changed-stmt-scope`, `_drafts/v3scope_kit/scope_proto.py` `select(…, "N2w")`; 실제 도구 a17b8bd로 대상 4·not_targeted 93 PASS 재확인 (card 35 병합본 a17b8bd 사전 실행 2026-10-02 — 공식 병합 뒤 재확인)) | 같음 | **4** | 4 | **0** | PASS |
| (참고) N2b(승인 당시 정의) | 같음 | 4 | 4 | 0 | -- |

N2w 대상 4(모두 죽음): `stmt_delete:body[9]`(for 루프 전체), `stmt_delete:body[9].body[1]`(`if result.ok:` 블록, head 11799), `stmt_delete:body[11]`(루프 뒤 `_finalize`, head 11877), `early_return:body[1]`.

현재 도구 생존 19(head 줄 = `H`의 sizing_recipe.py, base 줄은 11799 앞이면 같고 뒤면 +1, 11878 뒤면 +2):
| head 줄 | 변이 | 문장 | 메모 |
|---|---|---|---|
| 11714 | `const±` `args.defaults[0].elts[0·1]`, `args.defaults[2]`(6) | 기본 인자 `gm_id_bounds=(2.0, 30.0)`, `max_rounds=5` | 모든 호출이 이 인자를 명시(엔진 9371·test) -- 기본값 미사용 |
| 11771·11772 | `stmt_delete` `body[6].body[0].body[0]`·`…body[0].body[0]`(2) | backfill의 `if entry["interdig_ok"] is not None: continue` | **수정 뒤 생긴 등가 후보**: backfill이 반환마다 `_finalize`에서 한 번만 불리므로 건너뛰기 가드가 무의미해졌다 |
| 11777 | `stmt_delete` `body[6].body[0].body[2].body[0].body[1]` | backfill 안 `break` | 쌍마다 3b 체크가 하나뿐이면 등가 |
| 11795 | `stmt_delete:body[8]` | `result = None` | 등가(루프 안·뒤에서 반드시 대입) |
| 11800 | `stmt_delete:body[9].body[1].body[0]` | 성공 분기 `_finalize` | b26pre의 'N2d만' 등가 후보(base 11801)와 같은 문장 |
| 11809 | `stmt_delete:body[9].body[2]` | `import re` | 모듈에 `re`가 이미 있으면 등가 |
| 11815 | `const±` `…left.elts[0·1].args[0]`(3) | `m.group(1)`/`m.group(2)` 순번 | 3c 실패 쌍 파싱 -- 기존 test 공백 |
| 11831 | `const-:body[9].body[7].value.slice` | `a, b = failing_3c[0]` | 3c 실패 쌍이 하나뿐인 입력만 있음 -- 기존 test 공백 |
| 11849 | `cmp_flip:body[9].body[15].body[0].value.test.values[1].ops[0]` | `reason` 3항식의 `fix["growth"] is not None` | 기존 test 공백 |
| 11869·11870 | `stmt_delete` `body[9].body[18]`·`…body[0]`(2) | 핑거증가 뒤 `cur_ctx` 사이징 갱신 루프 | 기존 test 공백(반환 ctx를 보는 test 없음) |

**해석**: 이 card는 B34 뒤라 범위 card(N2w) 병합 뒤에 돈다(B34 card '판정 규칙': P10 → P10b → Phase 2 DoD → V3 binding → V3 scope → B34). 그 규칙으로 대상 4·생존 0 -- 면제·추가 test 불필요.
만약 범위 card 전에 착수하면(순서가 바뀌면) 현재 도구로 생존 19가 이 card의 V3 FAIL이 된다 -- 착수하지 말고 오케스트레이터가 순서를 다시 본다(이 card가 만든 생존은 11771·11772 둘뿐이고 그 둘도 N2w 대상이 아니다).
B26-1 인계: 수정 뒤 head에서 11799·11878 문장이 사라졌다(B26-1의 V3 생존 몫 2개 소멸, 예상대로). B26-1 모의 head·대상 수는 이 card 병합본에서 다시 잰다.

### 0.4 library 영향(DEC-40 입력 -- `b26bf_kit/lib_measure.py`·`run_lib.sh`)

이 def의 엔진 안 호출부는 `optimize_full_circuit_budget`(9368) 하나다. E-LIB 정의(`load_topology`·`run_topology_pipeline`, stick_diagram)는 이 def에 닿지 않는다(정적). 그래서 harness 실행(`run_harness.run`)마다 이 def를 감싸
(반환을 읽기만) 호출별 `relaxed_pairs` 항목의 반환 `interdig_ok`와 같은 반환 audit의 3b를 대조했다. 사본: base = `BP` 트리(a796468 + B34 + b26pre 시제품), fix = `H` 트리(+ 수정 후보). PYTHONHASHSEED 0.

| 회로(library 9) | harness SPECS | base: 호출 / 완화 항목 / 불일치(= 수정이 바꾸는 항목) | fix: 같은 셋 | `instance.json` sha256(키 정렬 JSON) base = fix | 비고 |
|---|---|---|---|---|---|
| `current_reuse_telescopic_ota`(파일럿) | 있음 | 1 / 2 / **0** | 1 / 2 / 0 | 같음 `1b9a4d4c…` | 완화 2쌍: `M4a/M4b` interdig_ok True(3b True), `M3a/M3b` **False(3b False)** -- 실제 회로의 첫 `interdig_ok=False` 관찰(`.ai/context.md` 1558 '알려진 한계'의 사례). 사유 `growth_not_applicable`. 핵심 반환 해시(`core_sha`, interdig_ok 제외) base = fix |
| `folded_cascode` | 있음 | 1 / 0 / 0 | 1 / 0 / 0 | 같음 `e690b95d…` | 완화 없음(무발동) |
| `two_stage_ota` | 있음 | 0 / -- / -- | 0 | 산출 없음(두 사본 같음) | harness가 `optimize_full_circuit_budget` 안 `ValueError`('stage1_out' 그룹 VDS 합 KVL 불일치)로 이 def 전에 멈춤 -- `a796468`(B34 없음)에서도 같음, 이 card와 무관 |
| `nmcnr_amplifier` | 있음 | 0 / -- / -- | 0 | 산출 없음(두 사본 같음) | `ValueError`(모든 theta 격자점 infeasible, 'stage2_diode_ref' 예산) -- `a796468`에서도 같음, 이 card와 무관 |
| 나머지 5(`common_gate_amplifier`·`ngcc_3stage_ff`·`pushpull_follower_buffer`·`sf_pushpull_output_opamp`·`two_stage_ota_sf`) | 없음 | 호출 경로 없음 | -- | -- | `load_topology` 9/9 ok(두 사본), 계측 중 호출 0 |

**결론(DEC-40 입력)**: library에서 수정 후보가 `interdig_ok`를 바꾸는 항목 **0**(완화가 생기는 유일한 회로인 파일럿에서도 정리 전후 3b가 같다). `instance.json`에는 `interdig_ok` 키가 없고 두 사본 해시가 같다.
→ 재생성할 기준선 없음. 기존 test 전체에서도 어긋나는 호출 0(독립 검토 계측)이라, 값이 바뀌는 곳은 이 card의 합성 입력뿐이다. 실행 시간: 파일럿 ~430초, folded ~50초(두 사본 병렬).

### 0.5 red-green·전체 회귀(B34 위 -- 그동안 B34 없는 사본에서만 잼)

| 측정 | 결과 |
|---|---|
| red(`T` = BP + 시제품 test, base 엔진, archive 사본·seed 0·1) | 2 failed -- 둘 다 `AssertionError: assert False is True`, `where True = AuditCheck(name='3b. interdigitation[Ma/Mb] [참고용 -- 이 kind는 필수 아님]', ok=True, detail='seg1_seg1: 인접').ok` |
| green(`H`, seed 0·1) | 2 passed |
| `A/tests` 전체, `T` git 복제본(seed 1) | 2 failed(위 red 2개뿐)·888 passed·15 xfailed, 435초 |
| `A/tests` 전체, `H` git 복제본(seed 1) | **890 passed·15 xfailed·실패 0**, 433초 (`.git`이 있는 복제본이라 `test_ts6_probe_relocate` 2개도 통과 -- 예전 archive 사본의 '2 failed'는 환경 한계였음) |
| V4(base 판 `test_lint.py`, 모의 interface card, `BP..T`) | PASS, 판정 (2) `NO-SUBJECT` 2건 -- 1.4 |

이 수치로 card '재현할 수치'의 'auditor 몫(미측정)' -- B34 위 전체 회귀 -- 를 사전 측정으로 채웠다(판정은 여전히 auditor가 착수 base에서 다시 잰다).

### 0.6 모의 결과(`b26bf_kit/sim_launch_bf.sh` -- `C:/g128/sim2/r` = gate `master` `0f23786` 복제, bare 가짜 gate `C:/g128/sim2/gate.git`)

| 단계 | 결과 |
|---|---|
| 0 모래상자 | `C:/g128/sim3/r` = `0f23786`(origin 없음, 빈 hooksPath), 가짜 gate = bare 복제(hook 없음 -- EL4는 `merge_gate.py receive`를 직접). 게이트 캐시 `…/.git/gmid-gate-cache/0f237862…`(`role_paths.tree_blobs`→`extract_blobs`→`dir_matches`, 22파일, `interface_card.py`가 gate master blob과 바이트 동일) |
| D 승인 기록 | 초안 그대로 복사, LF·BOM 없음·HTML 주석 없음, `merge_gate.py parse-approval` 통과(`target_kind decision`, `target_list ["U-BF-BACKFILL-INTERDIG"]`, `diff_path []`) → `Role: doc` 커밋(경로 = 기록 하나) |
| B spec+interface | 초안 복사 → **게이트 캐시의** `interface_card.py <절대 spec> --root <R> --out <절대 interface>` exit 0, 관찰 가능한 계약 **4행**(0.7-2), 신규 시그니처 0행 → `Role: doc` 커밋 |
| P 파싱 | (결정 전 card로 모의 -- 지금 card는 phase 3·approval 2줄) `parse_spec_card`: phase 2·red-green·gate_change no·approval `[20261001-b26-backfill-interdig-fix]`·절 11. phase 2 ∈ `phase_order`. HEAD 트리에서 기록 머리 파싱·`load_approvals`에 있음. `reachability._approved_ids` 36 → 37(+`U-BF-BACKFILL-INTERDIG` 하나 -- 변이·test id 모양이 아니라 V3·V4·V7 면제에 닿지 않음). `gate_change_ok(HEAD)` False(gate_change no라 쓰이지 않음) |
| E EL4 | `merge_gate.py receive --git-dir <gate.git> --old 0f23786 --new <B>`(D·B 두 커밋) → **exit 0**. 대조: 트레일러 없는 커밋 하나를 더한 것 → **exit 1** "[EL4 거부] …: 트레일러 Role: code/test/audit/doc/user가 정확히 하나가 아니다([])"(게이트가 실제로 거부함) |

(모의 커밋 해시는 모래상자 것이다. EL3(커밋 hook)는 모의하지 않았다 -- 빈 hooksPath, 선례와 같은 범위. 실제 착수는 B34·b26pre 병합 뒤 gate master라 base가 다르다 -- 0단계로 확인.)

**2026-10-02 모의(`backfill_launch.sh`, 모래상자 `C:/g170` -- 끝나고 삭제)**: 실제 저장소 복제(gate `master` `dd60db6`) + 모의 선행(V3 묶기·범위 판정 기록 자리표시, 범위 card 흉내 = `mutate_changed.py` main을 시제품 `scope_proto` N2w 대상 수만 내는 shim, `20261001-b26-phase3-cards` 기록 초안 그대로, B34 흉내 SD 한 줄 + 판정 기록 자리표시)
→ bare 가짜 gate(실제 `pre-receive`·`gate-runner.py` = EL4), 복제본 `core.hooksPath=.githooks`(EL3) → `b26pre_launch.sh local`·push·`after-push` → b26pre 병합 흉내(시제품 test + 판정 기록 자리표시, gate에 hook 없이 올림) → 이 스크립트.
결과: `conds` 0·0·0·0·0 → `local`(pre: approval 줄 2건 gate에 있음·U-BF blob = 초안; v3count: scratch 복제본에서 수정 후보 11800·11879(dd60db6 줄 -- B34 병합본 `2183f2e`에서는 11799·11878) 삭제(numstat 0 2) → 대상 **4**·not_targeted 93; card: parse_spec_card `('3', 'red-green', 'no', [U-BF, phase3-cards], [], 11)`, interface 4행) → push EL4 통과(accept-log 한 줄) → `after-push` OK.
대조: `--scratch` 없이 `local` → exit 2, scratch 경로 규칙 밖 → 멈춤, `targets_by_def` 없는 도구 출력(범위 card 전 판) → 멈춤, 트레일러 없는 표 경로 커밋 → EL3 차단.

**2026-10-06 사전 실행(실제 B34 병합본 `2183f2e` 위, 모래상자 `C:/g314` -- 끝나고 삭제)**: 실제 저장소 복제(`-c core.autocrlf=false`) → 합성 `audit`(gate 경로만) → bare 가짜 gate(실제 `pre-receive`·`gate-runner.py` = EL4), 복제본 EL3
→ b26pre 병합 모의(시제품 `proto_v2_test_b26pre.py`·`proto_test_b26pre_trace.py` 무수정 `Role: test` + 판정 기록 자리표시, gate에 hook 없이 올림) → 이 스크립트(card measured `2183f2e`, 수정 후보 11799·11878).
결과: `conds` 0·0·0·0·0 → `local`(pre: measured 앵커 2개 -- 마지막 `2183f2e`, SR·selftest 변경 커밋 0, `_approved_ids` 39, plan hash `16b899d1…`; v3count: 수정 후보 11799·11878 삭제 → 대상 **4**·not_targeted **93**·4/4 killed V3 PASS; card: parse_spec_card `('3', 'red-green', 'no', [U-BF, phase3-cards], [], 11)`, interface 4행·36줄) → push EL4 통과(accept-log 한 줄) → `after-push` OK.
`engine_since` 허용 규칙(함수 본문을 뽑아 따로 시험): measured `dd60db6`이면 B34 `2eb7e55`(Change-Id `20260930-b34-grammar-explicit`)를 허용하고 통과, 트레일러 없는 SR 커밋은 rc 1로 멈춤.
변이 전 dry run(새 test = 시제품 `proto_bf_test.py` + 옛 코드, b26pre 시제품 함께): seed 0·1 각각 **2 failed**·19 passed(`assert False is True`), 수정 후보(11799·11878 삭제) seed 0·1 각각 21 passed.

### 0.7 착수 직전에 다시 볼 것

0. **착수 0단계 명령**(이 문서 머리, (가)~(아) -- `backfill_launch.sh pre`·`v3count`가 한다). B34·b26pre `audit:` 커밋과 V3 면제 묶기·범위 card 판정 기록, `20261001-b26-phase3-cards` 기록, Phase 2 DoD PASS 기록이 gate `master`에 있고, 병합 도구로 잰 V3 대상이 4이며, `git -C "$R" branch --list 'role/*'`가 비어 있어야 한다(역할 브랜치가 있으면 문서 커밋 push가 EL1 거부).
1. **승인 기록 원문 대조** -- 완료(독립 검토 `review_backfill_kit.md` §1: jsonl 원문 `쟽니다`, 초안과 바이트 같음). 커밋 전에 초안이 바뀌지 않았는지만 본다.
2. **interface card**: 게이트 캐시(`<git-common-dir>/gmid-gate-cache/<gate master 전체 sha>/interface_card.py`)로 만든다. 모의 결과는 '관찰 가능한 계약' 4행(`run_matching_safety_with_finger_growth`·`size_transistor`·`GmIdLUT.gm_gds_ratio`·`SemiEmpiricalGmIdLUT.gm_gds_ratio`), 신규 시그니처 0행. 행 수가 다르면 card 백틱 토큰과 엔진 def 이름이 바뀐 것이다 -- 확인하고 멈춘다.
3. 셸: hook(`role_guard.py`)은 `(cd … && …)`·`cd` 뒤 상대 경로 쓰기 대상·변수 든 `rm`·**저장소 `.git` 안을 가리키는 인자**를 거부한다. 이번 작업에서 `ls <R>/.git/gmid-gate-cache/`(Bash·PowerShell 둘 다)가 `[EL1 거부] 저장소 내부를 가리키는 인자`로 거부됐다 -- 0.8의 `$CACHE/…` 호출이 거부되면 `sim_launch_bf.sh`처럼 스크립트 파일 안에서 부른다(`bash <스크립트>`).
4. 모의 커밋은 `--trailer "Role: doc"`만 썼다(문서 커밋 선례). 역할 커밋은 `--trailer "Role: …" --trailer "Change-Id: 20261001-b26-backfill-interdig-final-audit"`.

### 0.8 명령 시퀀스(오케스트레이터, MSYS bash -- 0.7 통과 뒤)

**2026-10-02 정정**: 실행은 `backfill_launch.sh`(`--scratch /c/g<번호> local` → push 단독 → `after-push`)로 한다. 아래 D(승인 기록)는 이미 끝났다 -- `20261001-b26-backfill-interdig-fix`는 gate `19eb475`에 있다(다시 올리지 않는다). 아래 목록은 스크립트가 하는 일의 참고용이다.

```bash
R=/c/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills
DR=/c/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts
W=/c/Users/HSLEE/Documents/Todoc/fpga/wt
PY=C:/Python314/python.exe
ID=20261001-b26-backfill-interdig-final-audit
AID=20261001-b26-backfill-interdig-fix
git -C "$R" fetch gate
test "$(git -C "$R" rev-parse --abbrev-ref HEAD)" = master
test "$(git -C "$R" rev-parse HEAD)" = "$(git -C "$R" rev-parse gate/master)"
test -z "$(git -C "$R" branch --list 'role/*')"
test -z "$(git -C "$R" status --porcelain -- docs/ .ai/approvals/)"
GM=$(git -C "$R" rev-parse gate/master)
CACHE=$(git -C "$R" rev-parse --path-format=absolute --git-common-dir)/gmid-gate-cache/$GM
# D. 승인 기록(decision) -- spec card보다 먼저
cp "$DR/approval_$AID.md" "$R/.ai/approvals/$AID.md"
$PY -B "$CACHE/merge_gate.py" parse-approval "$R/.ai/approvals/$AID.md"
git -C "$R" add -- ".ai/approvals/$AID.md"
git -C "$R" commit --trailer "Role: doc" -m "docs: 승인 기록 $AID(U-BF 결정 -- relaxed_pairs interdig_ok를 반환 audit(euler 정리 뒤)의 3b로 채우도록 수정, target_kind decision; card $ID 착수 조건)"
# B. spec card + interface card(게이트 캐시의 interface_card.py, 절대 경로)
cp "$DR/draft_b26_backfill_audit.spec.md" "$R/docs/02-design/specs/$ID.spec.md"
$PY -B "$CACHE/interface_card.py" "$R/docs/02-design/specs/$ID.spec.md" --root "$R" --out "$R/docs/02-design/specs/$ID.interface.md"
git -C "$R" add -- "docs/02-design/specs/$ID.spec.md" "docs/02-design/specs/$ID.interface.md"
git -C "$R" commit --trailer "Role: doc" -m "docs: spec card $ID(run_matching_safety_with_finger_growth relaxed_pairs interdig_ok = 반환 audit 3b, red-green, approval $AID·20261001-b26-phase3-cards) + interface card"
# 확인(push 전): parse_spec_card -> phase 3, red-green, gate_change no, approval [$AID, 20261001-b26-phase3-cards] (sim_launch_bf.sh P 단계와 같은 코드 -- 그 스크립트의 기대는 phase 2 전제라 고쳐 쓴다, 머리 'phase 표기')
# 20261001-b26-phase3-cards 기록은 B34 순서 0 커밋 전에 이미 gate에 있다(0단계 (사)) -- 여기서 다시 올리지 않는다
# push -- 단독 실행, 전체 출력 확인(병렬·tail 금지)
git -C "$R" push gate master:master
git -C "$R" fetch gate
git -C "$R" merge --ff-only gate/master
test "$(git -C "$R" rev-parse HEAD)" = "$(git -C "$R" rev-parse gate/master)"
# 순서 1: test worktree
git -C "$R" worktree add "$W/$ID-test" -b "role/test/$ID" gate/master
```
이어서 §12 순서 2(test-author, 1절) → 3(auditor freeze·base, 3.1) → 4(code worktree, 부모 = T) → 5(code-author, 2절) → 6(병합) → 7(auditor 판정, 3.2·3.3) → 8(push) → 정리 → **B26-1 재측정 인계**(card '결정 필요 항목' 마지막 묶음).

---

## 1. test-author 브리프(gmid-test-author, §12 순서 2)

```
역할: gmid-test-author. change id = 20261001-b26-backfill-interdig-final-audit (엔진 동작 변경, red-green, phase 3).
worktree: C:/Users/HSLEE/Documents/Todoc/fpga/wt/20261001-b26-backfill-interdig-final-audit-test (브랜치 role/test/20261001-b26-backfill-interdig-final-audit). 모든 명령은 절대 경로(git -C, cd 금지).
쓰기 경로: skills/analog-gmid-design/assets/tests/contracts/test_b26_backfill_interdig.py 하나(계획 N3.12.2 gmid-test-author 행 `A/tests/**`, tests/tools/** 제외).
입력: interface card docs/02-design/specs/20261001-b26-backfill-interdig-final-audit.interface.md(관찰 가능한 계약 4행 -- 피검은 run_matching_safety_with_finger_growth 하나,
      size_transistor·gm_gds_ratio 둘은 입력을 만드는 데만 쓴다), spec card의 '관찰 가능한 계약' 계약 1과 '이름' 목록, 'oracle 종류와 출처', '거부해야 할 입력'.
      oracle (d) = 승인 기록 .ai/approvals/20261001-b26-backfill-interdig-fix.md(읽어도 된다).
열람 금지: skills/analog-gmid-design/assets/*.py(엔진 소스 -- 특히 sizing_recipe.py), _drafts/** (오케스트레이터 시제품·측정 -- 기대값의 출처가 될 수 없다).
커밋: git -C <worktree> commit --trailer "Role: test" --trailer "Change-Id: 20261001-b26-backfill-interdig-final-audit" -m "test: …"
```

### 1.1 산출물(계약 1 그대로)

새 파일 하나: `A/tests/contracts/test_b26_backfill_interdig.py`. test 함수 이름은 `test_b26bf_`, 모듈 수준 도우미는 `_b26bf_`(또는 판정 도우미면 `assert`로 시작 -- 1.4)로 시작.

**합성 입력(구성 -- oracle (a) 입력)**: 행 하나 `{"seg1": [Ma, Mb, Mp]}`.
* `Ma = Transistor("Ma", "nmos", source="n2", drain="n1", gate="ga", n_fingers=1, finger_w=W0, stack_id="seg1")`
* `Mb = Transistor("Mb", "nmos", source="n4", drain="n2", gate="gb", n_fingers=1, finger_w=W0, stack_id="seg1")`
* `Mp = Transistor("Mp", "nmos", source="n2", drain="n5", gate="gp", n_fingers=1, finger_w=W0, stack_id="seg1")`
  -- 넷 `n2` 차수 3, `n1`·`n4`·`n5` 차수 1(홀수 차수 넷 4개 → euler-blocked). Mp가 Ma·Mb 사이에 끼어 '정리 전 행'과 '정리 뒤 행'의 3b가 다르게 된다.
* `W0`·사이징 항목 `S`: `r = size_transistor(gm=200e-6, gm_id=12.0, L=0.5e-6, lut=toy_lut, vds=0.6)`, `W0 = r.W`,
  `S = {"ID": r.ID, "W": W0, "L": 0.5e-6, "gm": r.gm, "gm_id": 12.0, "gds": r.gm / toy_lut.gm_gds_ratio(12.0, 0.5e-6, 0.6, 0.0), "kind": "nmos", "vds": 0.6, "vsb": 0.0}`.
* `ctx = SizingContext(sized={이름: dict(S) for 세 소자}, topology_path=<tmp_path의 합성 topology>)`. 합성 topology는 `tmp_path`에 쓰고 `supply_nets: ["vdd", "gnd"]`를 선언한다
  (`netlist` = 세 소자의 name·kind·source·drain·gate, `symmetry` = `{"matching_pairs": [], "dispositions": []}`, `schema_version: "2.0"`).
* 호출: `run_matching_safety_with_finger_growth({"seg1": 행}, [("Ma", "Mb")], {("Ma", "Mb"): "offset"}, ctx, {"nmos": toy_lut}, {}, [], gm_id_bounds=(11.9, 12.1), max_rounds=m)`
  -- 앞 7개 위치 인자, 뒤 둘 키워드. 좁은 gm/ID 범위(사이징 값 12.0 둘레)로 핑거증가가 막혀 완화(`relaxed_pairs`)가 생긴다.
* 픽스처 `toy_lut`·`tmp_path`는 conftest·pytest 것을 쓴다.

**두 test(별개 함수 -- 한쪽 경로만 고친 엔진을 각각 잡는다)**:
| test | m | 경로 | 단언 |
|---|---|---|---|
| 루프 안 | 2 | 완화 뒤 다음 라운드에서 3c 실패가 완화 쌍뿐 → `relaxed_to_layout` 반환 | `res["unresolved_reason"] == "relaxed_to_layout"` 그리고 `CONSISTENT(res)` |
| 루프 뒤 | 1 | 첫 라운드에 완화하고 루프가 끝남 → 루프 뒤 반환 | `res["unresolved_reason"] == "max_rounds_exceeded"` 그리고 `CONSISTENT(res)` |

`CONSISTENT(res)`(계약 1): `[e["pair"] for e in res["relaxed_pairs"]] == [("Ma", "Mb")]`, 그리고 항목 `e`(쌍 `(a, b)`)마다 `res["audit"].checks` 중 이름이 `"3b."`로 시작하고 `f"[{a}/{b}]"`를 담은 체크가 **정확히 1개**이며 `e["interdig_ok"] is <그 체크>.ok`.
(쌍 목록 단언은 입력마다 완화되는 쌍 목록으로 바꾼다 -- 아래 반환 자리 test는 쌍이 둘 이상일 수 있다.)

**반환 자리마다 test(계약 1 '반환 자리마다 test' -- 원칙: 계약 이름 '모든 반환 경로'를 test로 덮는다)**: 위 두 test는 반환 자리 (ii) `relaxed_to_layout`·(v) `max_rounds_exceeded`다.
`relaxed_pairs`가 비어 있지 않은 채 도달할 수 있는 나머지 자리 -- (iii) `"pair_not_found"`, (iv) 증가 미적용(`"no_finger_w"`·`"growth_not_applicable"`, 그리고 `allow_layout_relaxation=True`에서 완화된 쌍 뒤의 다른 사유) -- 마다 `CONSISTENT(res)` test를 하나씩 더한다.
입력은 card 계약 1의 예처럼 **매칭 쌍 둘**로 구성한다: 첫 쌍은 위와 같은 좁은 gm/ID 범위로 완화되고, 다음 라운드에서 둘째 쌍이 그 사유로 멈추게 한다(예: 둘째 쌍 소자의 `finger_w=None` → `"no_finger_w"`). 반환 `unresolved_reason`을 단언해 의도한 자리에 도달했는지 확인한다.
(i) 성공(`None`)은 card가 적은 대로 `relaxed_pairs`가 비지 않은 채 도달하지 않는 자리라 test하지 않는다(docstring 서술 근거 -- 만약 입력이 그 자리에 도달하면 그 test도 둔다).
**합성 입력을 만들지 못한 자리는 그 사실을 적는다**: 시도한 입력(소자·쌍·인자)과 실제 반환(`unresolved_reason`, `relaxed_pairs`)을 새 test 파일 머리 docstring과 보고에 적고, test를 억지로 만들지 않는다(그 자리는 구조 보장 -- auditor가 병합본 코드에서 확인). 이 test들은 base에서 red일 필요가 없다(관계 단언).

### 1.2 oracle 주석

각 test(또는 판정 도우미)에 `oracle 대조: 20261001-b26-backfill-interdig-fix (d) 사용자 결정 -- relaxed_pairs[i]["interdig_ok"]는 반환 audit(euler 정리 뒤 최종 물리 구조)의 3b 판정`.
기대값을 `True`/`False` 리터럴로 박지 않는다(관계 단언 -- 같은 반환 안 두 필드의 일치가 결정된 계약이다). 최종 rows 모양(`{Ma, Mb}` 행 등)도 단언하지 않는다(rows 불변은 계약 2, auditor 몫).

### 1.3 자기 점검(커밋 전, 판정 근거 아님)

* `C:/Python314/python.exe -P -m pytest <worktree>/skills/analog-gmid-design/assets/tests/contracts/test_b26_backfill_interdig.py --rootdir=<worktree> -q --gmid-phase=3 --gmid-strict=`(bash면 `export APPDATA=C:/Users/HSLEE/AppData/Roaming`)
  → base 엔진에서 루프 안·루프 뒤 두 test는 **둘 다 `AssertionError`이고 실패 문장이 `interdig_ok is …ok` 단언**이어야 한다(`unresolved_reason` 단언이나 쌍 목록·체크 개수 단언에서 실패하면 입력 구성이 틀렸다 -- 멈추고 보고). 반환 자리 test(1.1 끝)는 base에서 통과해도 된다 -- 실패하면 어느 단언에서인지 보고.
* PYTHONHASHSEED 두 값(예 0·1)에서 같은 결과.
* `A/tests` 전체 한 번: 새 파일 두 test 외 실패 0.

### 1.4 V4 메모

* 피검 호출 한 번의 반환 안 두 필드를 비교하는 관계 단언이다. 키트 실측(base 판 `test_lint.py`, 같은 interface card): 피검 호출을 도우미(`_b26bf_run`) 안에 두고 test가 단언하는 모양은 `PASS`(판정 (2) `NO-SUBJECT`), test 함수 안에서 직접 호출하고 단언하는 모양도 `PASS`(판정 (2) `UNJUDGED`). 어느 쪽이든 (1) FAIL은 나지 않았다.
* 판정을 도우미에 몰아넣으면 test 함수 자신에 단언이 없어 (4) FAIL이 될 수 있다 -- test 함수 본문에 `unresolved_reason` 단언을 두거나, 도우미 이름을 `assert`로 시작하게 한다.

---

## 2. code-author 브리프(gmid-code-author, §12 순서 5)

```
역할: gmid-code-author. change id = 20261001-b26-backfill-interdig-final-audit (red-green, phase 3).
base = gate master 863a037cc0d774bb984006ea39966c5e4dd741ab(spec card·interface card 커밋), T = 3004096c81b839998518c14c16d3cd2d6ec6c9bf(Role: test, 새 test 5개).
worktree: C:/Users/HSLEE/Documents/Todoc/fpga/wt/20261001-b26-backfill-interdig-final-audit-code (브랜치 role/code/20261001-b26-backfill-interdig-final-audit, 부모 = T 3004096c81b839998518c14c16d3cd2d6ec6c9bf). 절대 경로만(git -C <절대 경로>), cd·(cd … && …) 금지.
scratch: C:/g395 하나만(띄우기 직전 test ! -e 확인됨). TMP·TEMP·TMPDIR·PYTHONPYCACHEPREFIX·pytest --basetemp도 C:/g395 아래, "." 금지. 끝나면 C:/g395만 삭제(다른 C:/g* 금지).
쓰기 경로: skills/analog-gmid-design/assets/sizing_recipe.py 하나. test·문서·레지스트리는 쓰지 않는다(새 def·삭제 def 없음 -- 레지스트리 갱신 없음).
입력: spec card·interface card·T의 test. test가 틀렸다고 보면 고치지 말고 dispute(<worktree>/docs/02-design/disputes/20261001-b26-backfill-interdig-final-audit.md)를 쓰고 같은 트레일러로 커밋한 뒤 멈춘다.
커밋(트레일러는 정확히 두 개 -- Role·Change-Id만, Co-Authored-By 등 다른 트레일러 금지):
  git -C C:/Users/HSLEE/Documents/Todoc/fpga/wt/20261001-b26-backfill-interdig-final-audit-code commit --trailer "Role: code" --trailer "Change-Id: 20261001-b26-backfill-interdig-final-audit" -m "…"
```

### 2.1 바꿀 것(최소 수정 -- 구조 변경 없음)

`run_matching_safety_with_finger_growth` 안에서:
1. 루프 안 `current_rows, result = repair_matching_safety(…)` **바로 다음 줄** `_backfill_interdig_ok(result)`(base `863a037` 11799 -- `2183f2e`와 sizing_recipe.py 같음, 2026-10-07 재확인)를 지운다.
2. 루프 뒤 `current_rows, result = repair_matching_safety(…)` **바로 다음 줄** `_backfill_interdig_ok(result)`(11878)를 지운다.
3. 정리 함수 `_finalize` 안의 `_backfill_interdig_ok(fixed_audit)`(11792)는 **남긴다**(모든 반환 경로가 `_finalize`를 거치므로 항목은 반드시 최종 audit으로 채워진다).
4. 거짓 서술 정리(코드 동작 아님, V 판정 밖): `_backfill_interdig_ok` 안 주석(11768~11769 "다음 라운드에 새로 계산된 audit_result가 나오면 그 3b 체크로 채운다")과 반환 docstring의 `"interdig_ok":bool|None`(11758) 설명을
   "반환 직전 `_finalize`가 계산한 최종 audit(euler 정리 뒤)의 3b 체크로 채운다"는 뜻으로 고친다. 주석·docstring 외 다른 줄은 바꾸지 않는다.

**하지 말 것**: `_backfill_interdig_ok`의 `if entry["interdig_ok"] is not None: continue`(11771~11772) 건드리기, `_finalize` 구조·반환 dict 키·완화 정책(3c 요구, `audit.ok`) 변경, 새 함수·새 인자, 광범위 `except`(V6), 숫자 리터럴 추가(V6).
(사전 측정: 위 1·2만 지운 엔진에서 계약 1 두 test green, `A/tests` 전체 회귀 없음 -- 0.5. 한쪽만 지우면 반대쪽 test가 실패한다 -- card '거부해야 할 입력'.)

### 2.2 자기 확인(판정 근거 아님)

* 새 test 다섯 개(`test_b26_backfill_interdig.py`) PASS, `test_selftest_sizing_recipe.py`(L4e `interdig_ok is not None`)·`test_selftest_stick_diagram.py`·b26pre test 파일 PASS, `A/tests` 전체 실패 0(base 참고: 1109 passed·15 xfailed -- b26pre 판정 기록 T 수치, 그 뒤 test 변화 없음 → T 위 기대 1114 passed·15 xfailed).
* `git -C <worktree> diff 3004096c81b839998518c14c16d3cd2d6ec6c9bf -- skills/analog-gmid-design/assets/sizing_recipe.py`: 삭제 2줄 + 주석·docstring 줄만.

---

## 3. auditor 브리프(gmid-verification-auditor, §12 순서 3·7)

```
역할: gmid-verification-auditor. change id = 20261001-b26-backfill-interdig-final-audit, evidence_type red-green, phase 3, approval 20261001-b26-backfill-interdig-fix(decision)·20261001-b26-phase3-cards(decision -- card phase 3).
base = gate master 863a037cc0d774bb984006ea39966c5e4dd741ab(spec card·interface card 커밋 -- 판정 기록 base_commit = 이 값. 착수 시 gate master가 다르면 멈추고 보고).
T = 3004096c81b839998518c14c16d3cd2d6ec6c9bf(Role: test, 새 test 5개: in_loop_relaxed_to_layout, after_loop_max_rounds_exceeded, site_pair_not_found, site_no_finger_w, site_growth_not_applicable).
spec card: docs/02-design/specs/20261001-b26-backfill-interdig-final-audit.spec.md, interface card: 같은 폴더 .interface.md(관찰 가능한 계약 4행).
audit worktree: C:/Users/HSLEE/Documents/Todoc/fpga/wt/20261001-b26-backfill-interdig-final-audit-audit (브랜치 role/audit/20261001-b26-backfill-interdig-final-audit, 이미 만들어져 있음 -- 시작점 T).
scratch: 순서 3 = C:/g393, 순서 7 = C:/g394 -- 그 순서에 배정된 하나만(띄우기 직전 test ! -e 확인). TMP·TEMP·TMPDIR·PYTHONPYCACHEPREFIX·pytest --basetemp도 그 아래, "." 금지. 끝나면 그 폴더만 삭제(다른 C:/g* 금지).
격리: 모든 측정은 격리 복제본에서만(§12-7) -- git clone --no-hardlinks --no-local -c core.autocrlf=false -c core.longpaths=true --no-checkout <audit worktree> C:/g<n>/iso → git -C C:/g<n>/iso remote remove origin → test -z "$(git -C C:/g<n>/iso remote)" → checkout --detach <커밋>.
셸 가드(매 스크립트): set -euo pipefail, git은 git -C <절대 경로>만, cd·(cd … && …) 금지, 실제 저장소·다른 worktree에서 reset·checkout·branch·stash·clean 금지(쓰기는 자기 audit worktree의 판정 기록 경로만).
  시작·끝에 실제 저장소 C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills의 HEAD, git status --porcelain md5, reflog 줄 수, for-each-ref md5를 적어 같음을 확인(다르면 원인을 판정 기록 notes에).
리다이렉트 대상에 변수 경로(> $S/x)를 쓰지 말 것(EL1 role_guard가 거부) -- 출력은 스크립트 파일 안에서 쓰거나 리터럴 경로로.
환경: APPDATA=C:/Users/HSLEE/AppData/Roaming·HOME export, PYTHONIOENCODING=utf-8, $PY = C:/Python314/python.exe.
게이트 코드 = base 판: git -C <audit worktree> cat-file blob 863a037cc0d774bb984006ea39966c5e4dd741ab:tools/gates/<파일>로 C:/g<n>/gmid-gate-cache/863a037cc0d774bb984006ea39966c5e4dd741ab/에 추출(오케스트레이터 캐시 <git-common-dir>/gmid-gate-cache/863a037…와 파일마다 cmp 같음 확인), PYTHONPATH 앞, $PY -P.
  V1 명령의 -c 값은 이 경로의 pytest_gate.ini(디렉터리 이름이 gmid-gate-cache/<base 40자리>/여야 v1_command_check 통과).
V 도구(mutate_changed·test_lint·weakening_diff·source_lint·reachability)의 --base·--head에는 40자리 전체 sha만 쓴다(약칭·브랜치 이름·HEAD 금지). --root = 격리 복제본 루트(필수).
작성자(test·code) 보고와 오케스트레이터 사전 측정(이 문서 0절, card '재현할 수치'·'작성 전 실측')은 증거로 받지 않는다 -- 다시 잰다. 시제품(_drafts/b26pre_v2_scripts/proto_bf_test.py 등)은 열람·사용 금지.
판정 기록: .ai/verification/20261001-b26-backfill-interdig-final-audit.json + .ai/verification/20261001-b26-backfill-interdig-final-audit/{scripts,out}/. V5 basis에 64자리 16진 금지.
커밋: 순서 3은 **커밋하지 않는다**(산출물은 audit worktree에 쓰기만). 순서 7에서 병합 커밋 M(오케스트레이터가 만듦) 위에 정확히 한 커밋만 --
  git -C C:/Users/HSLEE/Documents/Todoc/fpga/wt/20261001-b26-backfill-interdig-final-audit-audit commit --trailer "Role: audit" --trailer "Change-Id: 20261001-b26-backfill-interdig-final-audit" -m "audit: …"
  (트레일러는 정확히 두 개 -- Co-Authored-By 등 다른 트레일러 금지.)
```

### 3.1 순서 3(freeze·base 확인 → `base_check.json`)

* **커밋하지 않는다**: base_check.json 등 산출물은 audit worktree에 쓰기만 하고 커밋하지 않는다(커밋은 순서 7에서 M 위 한 커밋).
* scratch `C:/g393`. T 해시 고정: `git -C <audit wt> rev-parse HEAD` = `3004096c81b839998518c14c16d3cd2d6ec6c9bf` = `role/test/<id>` 끝. `git -C <iso> log --format='%H %P' 863a037cc0d774bb984006ea39966c5e4dd741ab..3004096c81b839998518c14c16d3cd2d6ec6c9bf`가 첫 부모 사슬이고 커밋마다 `git interpret-trailers --parse`로 `Role: test`·`Change-Id: 20261001-b26-backfill-interdig-final-audit`.
* `git -C <iso> diff --name-only 863a037cc0d774bb984006ea39966c5e4dd741ab 3004096c81b839998518c14c16d3cd2d6ec6c9bf` = `skills/analog-gmid-design/assets/tests/contracts/test_b26_backfill_interdig.py` 하나(오케스트레이터 확인 2026-10-07 -- auditor가 다시 잰다).
* **red**: T 복제본(base 엔진)에서 계약 1의 두 test(`…in_loop_relaxed_to_layout`·`…after_loop_max_rounds_exceeded`)가 **둘 다 `AssertionError`로, `interdig_ok is <3b 체크>.ok` 단언에서** 실패해야 한다(card '판정 유형 근거': `assert False is True`, 3b 체크 `3b. interdigitation[Ma/Mb] [참고용 -- 이 kind는 필수 아님]` ok=True).
  반환 자리 test 3개(`…site_pair_not_found`·`…site_no_finger_w`·`…site_growth_not_applicable`)도 base에서 같은 `interdig_ok is …ok` 단언으로 red다(test-author 보고 -- 다시 잰다). card는 '(a)(b) 밖의 자리 test는 base에서 red일 필요가 없다'고만 적으므로 **red여도 허용**이다(red 증거는 (a)(b) 둘, 나머지 3개의 red는 `red.test_ids`에 넣어도 되고 basis에 따로 적어도 된다 -- 어느 쪽인지 basis에 적는다).
  `unresolved_reason`·쌍 목록·체크 개수 단언에서 실패하면 red 이유가 계약과 다르다 → test 결함으로 보고. PYTHONHASHSEED 두 값(0·1).
* 반환 자리 (iv) 중 `"gm_id_violation"`: test-author가 `relaxed_pairs`가 비지 않은 채 도달하는 입력을 만들지 못했다고 test 파일 머리 docstring에 적었다(구조 보장 자리) -- docstring에 시도한 입력·실제 반환이 적혀 있는지 확인하고, 3.2 '반환 경로 구조 확인'에서 병합본 코드로 덮는다.
* **판별력**(card '거부해야 할 입력'): base 사본에 (i) 11799만 지운 엔진 → 루프 뒤 test 실패, (ii) 11878만 지운 엔진 → 루프 안 test 실패, (iii) `_finalize` 안 11792까지 지운 엔진 → 두 test와 L4e 실패. 셋 중 하나라도 test가 못 잡으면 test 결함. 반환 자리 test 3개가 각 변형에서 어떻게 되는지도 표로 적는다(판정 근거 아님).
* base 기준값: V2 회귀용 `A/tests` 전체(base `863a037…` 복제본 -- 참고 관찰: b26pre 판정 기록 T 1109 passed·15 xfailed, 그 뒤 base까지 test·엔진 변화 0), E-INST 두 회로(3.3), 계약 2 대조용 호출 결과(3.3).
* base 판 `mutate_changed.py --root <iso> --base 863a037cc0d774bb984006ea39966c5e4dd741ab --head 3004096c81b839998518c14c16d3cd2d6ec6c9bf …`(test-only 구간 V3) 한 번 -- 출력 보관(기대 targets [] -- 엔진 diff 0).
* 끝에 스스로: `git -C <audit wt> status --porcelain`(산출물 미커밋), `git -C <audit wt> log --oneline role/test/20261001-b26-backfill-interdig-final-audit..HEAD` 빈 출력 -- 둘 다 `base_check.json`에 적는다. `C:/g393` 삭제.

### 3.2 순서 7(병합본 판정)

* scratch `C:/g394`. 순서 3 산출물(base_check.json 등)은 이미 audit worktree에 미커밋으로 있다 -- 이 순서 7의 한 커밋(M 위, `Role: audit`)에 판정 기록과 함께 넣는다.
* 시작 전 확인: audit worktree HEAD = M(오케스트레이터의 `merge --no-ff role/code/<id>`, 부모 둘 = T `3004096c…`·code 끝 K, 트레일러 `Role: doc`·`Change-Id: 20261001-b26-backfill-interdig-final-audit`, M 트리 = K 트리). 판정 커밋 직전: `git -C C:/Users/HSLEE/Documents/Todoc/fpga/wt/20261001-b26-backfill-interdig-final-audit-audit log --oneline --first-parent M..HEAD` 빈 출력(M 위에 아직 아무 커밋 없음), 커밋 뒤 정확히 1개.
* 판정 기록 `base_commit` = `863a037cc0d774bb984006ea39966c5e4dd741ab`, `test_commit` = T `3004096c81b839998518c14c16d3cd2d6ec6c9bf`, `code_commit` = K(M의 둘째 부모, 40자리), `evidence_type` "red-green", `approvals` = `["20261001-b26-backfill-interdig-fix", "20261001-b26-phase3-cards"]`. 병합본 측정은 M 복제본, 판정 V 도구의 `--head`는 M(40자리).
* **반환 경로 구조 확인(병합본 코드, AST·줄 인용으로 판정 기록 V2 basis 또는 notes에)**: 병합본 `run_matching_safety_with_finger_growth`의 **모든** `return`(중첩 def 안 제외)이 바로 앞에서 `_finalize(…)`를 거치고, `_finalize` 안 `_backfill_interdig_ok(fixed_audit)`가 남아 있으며, 루프 안·루프 뒤 사전 backfill 두 호출이 없음을 적는다.
  card 반환 자리 목록 (i)~(v)는 `"only_3b_failures_left"` 반환을 따로 세지 않는다 -- 이 값은 b26pre `test_b26pre_existing_paths.py` 계약 3(e)가 단언하는 반환이다. base `863a037` 줄로 11826 `reason = "relaxed_to_layout" if relaxed_pairs else "only_3b_failures_left"` → 11827 `_finalize` → (ii)와 같은 `return`(11828~11830)이다(오케스트레이터 읽기 2026-10-07 -- auditor가 병합본에서 다시 읽는다).
  이 반환에서 `relaxed_pairs`가 비지 않을 수 있는지 보고한다(위 3항식 그대로면 `"only_3b_failures_left"`는 `relaxed_pairs`가 빈 경우에만 나오므로 비지 않을 수 없다 -- 코드로 확인해 적는다). `"gm_id_violation"`(test 미구성 자리)도 같은 방식으로 `_finalize` 경유를 적는다.
* **V4 정보 항목**: 피검 호출이 도우미 `_b26bf_run` 안에 있어 test_lint가 `NO-SUBJECT` 정보 항목(약 20건)을 낸다 -- 이것은 FAIL이 아니다(판정 (2) 정보, 1.4·b26pre 선례 NO-SUBJECT 19). FAIL 0이면 PASS. 정보 항목 수는 basis에 적는다.

| V | 판정 | 근거·측정 |
|---|---|---|
| V1 | PASS 기대 | M 복제본 pytest 전체: `PYTHONPYCACHEPREFIX=C:/g394/pyc/v1_M PYTHONPATH=C:/g394/gmid-gate-cache/863a037cc0d774bb984006ea39966c5e4dd741ab C:/Python314/python.exe -P -m pytest -c C:/g394/gmid-gate-cache/863a037cc0d774bb984006ea39966c5e4dd741ab/pytest_gate.ini --rootdir=C:/g394/iso --confcutdir=C:/g394/iso C:/g394/iso/skills/analog-gmid-design/assets/tests --gmid-phase=3 --gmid-strict= -rA`(엄격 집합 = 빈 집합: base 판 `strict_set(base 트리, card)` = [] -- 오케스트레이터 2026-10-07 재측정, auditor가 다시 확인)(`-k`·`--deselect`·`-x` 없음). `merge_gate.v1_command_check(V1 문자열, old=863a037…, phase="3")` 위반 0. 참고 관찰(증거 아님): base 1109 passed·15 xfailed(b26pre 판정 기록 T 수치, 그 뒤 test 변화 0) → 새 test 5개면 병합본 1114 passed·15 xfailed. 판정은 관계(기존 id 같은 결과 + 새 id 전부 PASS) |
| V2 | PASS 기대 | red = 계약 1 두 test(`…in_loop_relaxed_to_layout`·`…after_loop_max_rounds_exceeded`, base, `AssertionError` -- `interdig_ok is …ok` 단언), 반환 자리 test 3개의 base red는 허용(3.1). green = 병합본에서 새 test 5개 전부 PASS. 새 test 외 base→병합본 판정이 바뀐 기존 test 0(계약 3, 특히 L4e·b26pre 계약 3(e)). 반환 경로 구조 확인(위 항목) 결과를 basis에 |
| V3 | PASS 기대 | `$PY -B <캐시>/mutate_changed.py --root C:/g394/iso --base 863a037cc0d774bb984006ea39966c5e4dd741ab --head <M 40자리> --pytest-ini <캐시>/pytest_gate.ini --python C:/Python314/python.exe --gmid-phase=3 --gmid-strict= --out C:/g394/out/v3.jsonl`. 범위 card `20260930-v3-changed-stmt-scope` 병합 판(`grep -c targets_by_def <캐시>/mutate_changed.py` ≥ 1 -- base 판 3회). 대상 def = `run_matching_safety_with_finger_growth` 하나. 참고 관찰(증거 아님, 오케스트레이터 2026-10-07 모래상자 `C:/g396`, base → base + 사전 후보(11799·11878 삭제), 새 test 없음): 아래 '사전 측정' 줄. 생존이 있으면 0.3 표의 분류와 대조 -- 등가 생존은 사용자 승인 기록(A1-a 형식) 없이 면제하지 않는다 |
| V4 | PASS 기대 | base 판 `test_lint.py --root C:/g394/iso --interface-card C:/g394/iso/docs/02-design/specs/20261001-b26-backfill-interdig-final-audit.interface.md --base 863a037cc0d774bb984006ea39966c5e4dd741ab --head 3004096c81b839998518c14c16d3cd2d6ec6c9bf`. FAIL 0이면 PASS -- `NO-SUBJECT` 정보 항목(약 20, 도우미 `_b26bf_run`)은 FAIL 아님(위 'V4 정보 항목'). basis는 `oracle 대조: `로 시작: 다섯 test의 기대(관계)가 승인 기록 `20261001-b26-backfill-interdig-fix` 결정 문장에서 왔는지, 피검 출력을 리터럴로 박지 않았는지 |
| V5 | PASS 기대 | base 판 `weakening_diff.py --root <iso> --base 863a037… --head <T 40자리>`·`--head <M 40자리>`: 기존 test·기준선 변경 0(새 파일 하나), `findings [] diff_paths [] diff_hash null`. → 3.4 DEC-40 |
| V6 | PASS 기대 | base 판 `source_lint.py --root <iso> --base 863a037… --head <M 40자리>`: 새 except·skip·숫자 리터럴 0(삭제 2줄 + 주석·docstring) |
| V7 | PASS(새 def 없음) | base 판 `reachability.py --root <iso> --base 863a037… --head <M 40자리>`: `new_defs []`, `_backfill_interdig_ok`는 `_finalize` 안 호출로 계속 도달 |
| V8 | N/A `도입 4: …`(base 판 계획서 `v_intro[V8]` = 4 -- `read_plan_tables`로 확인) | -- |
| V9 | N/A `도입 6b: …`(`v_intro[V9]` = 6b) | -- |
| V10 | PASS 기대 | card '재현할 수치'를 명령과 함께 재실행(`bf_repro` 상당 재현 -- auditor 독립 스크립트로), `reproduced_numbers`에 |

V3 사전 측정(증거 아님): base 판 `mutate_changed.py`(캐시와 바이트 같음, `targets_by_def` 3회), `--base 863a037cc0d774bb984006ea39966c5e4dd741ab --head` = base + 11799·11878 삭제(모래상자 커밋, numstat 0 2), `--gmid-phase=3 --gmid-strict=` → exit 0, `verdict PASS, mutants 4, killed 4, survivors [], not_targeted 93, targets_by_def {sizing_recipe.py::run_matching_safety_with_finger_growth: targeted 4, not_targeted 93, deleted_statements 2, def_header_changed false}`(새 test 없이 b26pre 실제 test만으로 4/4 죽음). 병합본(M, 새 test 포함)에서도 대상 4·생존 0이 기대값이다 -- 다르면(코드가 2줄 삭제 외 문장을 바꾸면 대상이 늘 수 있다) 분류해 적는다.

### 3.3 계약 2·library 대조(auditor 독립 스크립트)

* **계약 2(바뀌지 않는 것)**: 같은 합성 입력(m = 1·2·3·5, metrics 있음·없음)에서 base·병합본의 `rows`(행 키, 소자 이름·`n_fingers`·`stack_id`), `audit` 체크 이름·`ok`, `unresolved_pair`·`unresolved_reason`·`growth_rounds` 길이가 같고, 다른 것은 `relaxed_pairs[i]["interdig_ok"]`뿐.
* **library(E-LIB·E-INST)**: 이 def의 엔진 안 호출부는 `optimize_full_circuit_budget` 하나라 `load_topology`·`run_topology_pipeline`(E-LIB 9회로)은 닿지 않는다. 값이 바뀔 수 있는 곳은 harness 실행(`run_harness.run`)이다.
  E-INST 두 회로(`current_reuse_telescopic_ota`·`folded_cascode`)를 base·병합본에서 돌려 (a) `instance.json` 해시 같음 -- 비교 대상은 저장소에 **커밋된 `instance.json`이 아니라 base(수정 전)에서 다시 만든 `instance.json`**이다(재생성본 raw 해시 `7dc9f2e2…`·`8cd006a5…`가 커밋 파일 `586a2912…`·`d4ce00d7…`과 base·수정 모두 같게 다르다 -- `review_backfill_kit.md` m4. 커밋 파일과 비교하면 이 card와 무관한 차이가 잡힌다) (b) 이 def 호출마다 `relaxed_pairs` 항목의 `interdig_ok` 전후 값을 기록(감싸기 계측 -- 반환을 읽기만). 키트 사전 수치는 0.4 표.
  달라지는 회로·쌍이 나오면 회로·쌍·전후 값을 판정 기록에 적는다(승인 기록 '재검토').

### 3.4 DEC-40 확인(기준 약화)

* 이 card는 기존 기대값·기준선을 바꾸지 않는다: 기존 test 변경 0(L4e `is not None` 그대로), 저장소에 `interdig_ok`를 담은 기준선 파일 0(`git grep interdig_ok`의 비코드 히트는 `.ai/context.md` 기록과 과거 판정 기록 AST 덤프뿐 -- test가 읽지 않는다), `instance.json`에 `interdig_ok` 키 없음(0.4).
* 관찰 가능한 반환값 변경 자체는 기준 약화가 아니라 사용자 결정(decision 승인 `20261001-b26-backfill-interdig-fix`)이 덮는다. 판정 기록 `approvals` = `["20261001-b26-backfill-interdig-fix", "20261001-b26-phase3-cards"]`(card 머리 `approval:` 두 줄).
* library에서 값이 바뀌는 회로가 0이면(키트 사전 측정 0.4) 재생성할 기준선이 없다 -- DEC-40 승인 불필요를 근거(0.4 수치·V5 출력)와 함께 적는다. 0이 아니고 그 값이 어떤 기준선·보고 산출물에 들어가면 멈추고 오케스트레이터에 보고(DEC-40 승인 필요).

---

## 4. 순서 요약(오케스트레이터)

(V3 면제 묶기·범위 card 병합, Phase 2 DoD PASS(`2eefda1`), U-BF 기록(`19eb475`)은 끝나 있다. `20261001-b26-phase3-cards` 기록은 B34 0단계 P 커밋) → B34 병합·정리 → b26pre 병합·정리(`b26pre_launch.sh`) → `role/*` 0개 → **착수 0단계** `backfill_launch.sh --scratch /c/g<번호> local`(머리 (가)~(아) + v3count 대상 4) → 0.7 확인 → push 단독·전체 출력 확인 → `after-push` →
§12 순서 1(test worktree) → test-author(1절) → 순서 3 auditor(3.1) → 순서 4 code worktree(부모 T) → code-author(2절) → 순서 6 병합(병합 전 `git -C C:/Users/HSLEE/Documents/Todoc/fpga/wt/20261001-b26-backfill-interdig-final-audit-audit log --oneline role/test/20261001-b26-backfill-interdig-final-audit..HEAD` 출력이 비어야 한다 -- 비어 있지 않으면 순서 3 커밋이 섞인 것, 병합하지 말고 멈춤) → 순서 7 auditor(3.2~3.4) → 순서 8 push → 정리 →

**2026-10-07 착수 현황·고정값(이 절이 위 문단의 번호·경로를 구체화한다)**: base = gate master `863a037cc0d774bb984006ea39966c5e4dd741ab`(spec card S, push 끝), T = `3004096c81b839998518c14c16d3cd2d6ec6c9bf`(Role: test, 새 test 5개, 경로 = 새 파일 하나), audit worktree 이미 있음(`role/audit/<id>` = T).
```bash
R=/c/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills
W=/c/Users/HSLEE/Documents/Todoc/fpga/wt
ID=20261001-b26-backfill-interdig-final-audit
B=863a037cc0d774bb984006ea39966c5e4dd741ab
T=3004096c81b839998518c14c16d3cd2d6ec6c9bf
```
1. 순서 3: `test ! -e /c/g393` → auditor(3절 머리 블록 + 3.1, scratch `C:/g393`). **auditor는 커밋하지 않는다.** 끝 확인: `git -C "$W/$ID-audit" log --oneline "role/test/$ID..HEAD"` **빈 출력**, `git -C "$W/$ID-audit" status --porcelain`에 `.ai/verification/$ID…`만 미추적, `/c/g393` 지워짐.
2. 순서 4: `git -C "$R" worktree add "$W/$ID-code" -b "role/code/$ID" "$T"`.
3. 순서 5: `test ! -e /c/g395` → code-author(2절, scratch `C:/g395`). 끝 확인: `git -C "$W/$ID-code" log --format='%H %P' "$T..HEAD"`가 첫 부모 사슬, 커밋마다 트레일러 정확히 `Role: code`·`Change-Id: $ID` 두 개(Co-Authored-By 없음), `git -C "$W/$ID-code" diff --name-only "$T" HEAD` = `skills/analog-gmid-design/assets/sizing_recipe.py` 하나, `/c/g395` 지워짐.
4. 순서 6 병합(오케스트레이터, 단독 호출 -- role_guard 허용 형태 그대로):
   `git -C "$W/$ID-audit" merge --no-ff "role/code/$ID" -m "merge $ID" -m "Role: doc⏎Change-Id: $ID"`(⏎ = 실제 줄바꿈 -- 둘째 `-m`은 두 줄 `Role: doc` / `Change-Id: <id>`, 트레일러 정확히 두 개, Co-Authored-By 없음).
   확인: `git -C "$W/$ID-audit" log -1 --format='%P'` = `$T <code 끝 K>`, `HEAD^{tree}` = `role/code/$ID^{tree}`, `git -C "$W/$ID-audit" log -1 --format=%B`를 `interpret-trailers --parse`에 넣으면 두 줄.
5. 순서 7: `test ! -e /c/g394` → auditor(3절 머리 블록 + 3.2~3.4, scratch `C:/g394`, M = 4의 HEAD 40자리를 브리프에 적어 넘긴다). 끝 확인: `git -C "$W/$ID-audit" log --oneline --first-parent "<M>..HEAD"` = `Role: audit` 커밋 **정확히 1개**, 그 부모 = M, 트레일러 `Role: audit`·`Change-Id: $ID` 두 개, `/c/g394` 지워짐.
6. 순서 8 push -- **단독 실행, 전체 출력 확인**(병렬·`tail` 금지): `git -C "$W/$ID-audit" push gate "role/audit/$ID:master"`. 거부되면 정리하지 말고 출력 전체를 보고.
7. push 결과 확인 뒤에만: `git -C "$R" fetch gate`, `test "$(git -C "$R" rev-parse gate/master)" = "$(git -C "$W/$ID-audit" rev-parse HEAD)"`, `git -C "$R" merge --ff-only gate/master`.
8. 정리(7 확인 뒤): `worktree remove` audit·code·test 세 개, `git -C "$R" branch -D "role/audit/$ID" "role/code/$ID" "role/test/$ID"`, `test -z "$(git -C "$R" for-each-ref refs/heads/role/)"`, `/c/g393`·`/c/g394`·`/c/g395` 없음 확인(남았으면 그 폴더만 삭제).

**B26-1 인계**: 이 card 병합본에서 B26-1 모의 head·V3 대상 수('301')·Q1 문안 재측정(E6 finger growth 행 6 → 4, AST 경로 순번 당겨짐 -- card '결정 필요 항목').
