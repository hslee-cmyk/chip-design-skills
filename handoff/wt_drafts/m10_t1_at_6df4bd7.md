# M10·T1 초안 -- gate `master` `6df4bd7` 재확인 (2026-10-07)

대상: `draft_p3_m10.spec.md`(r3), `draft_p3_t1.spec.md`(r3), `m10_t1_open_items.md`. 초안은 고치지 않았다 -- 아래는 제안 편집뿐이다.
방법: 실제 저장소는 읽기만 했다(`git -C … show/rev-parse/diff/ls-tree/grep`). `git archive 6df4bd7 tools/gates skills/analog-gmid-design/assets workspaces/run_harness.py <레지스트리>`를 `C:/g425/t`에 풀고 TMP/TEMP를 `C:/g425/tmp`로 두었다. 작업이 끝난 뒤 `C:/g425`를 지웠고, 저장소 HEAD `6df4bd7`과 status(`.bkit` 2파일만 M)는 그대로다.

## 0. `863a037..6df4bd7`에서 바뀐 것

* `git diff --name-only 863a037 6df4bd7 -- tools skills workspaces <레지스트리>`의 결과는 두 파일이다: `A/sizing_recipe.py`, `A/tests/contracts/test_b26_backfill_interdig.py`(새 파일, test 5개).
  나머지는 `.ai/verification/20261001-b26-backfill-interdig-final-audit*`, `.ai/approvals/20260930-b26-b40-reason-key.md`, `docs/02-design/specs/20260930-b26-rail-accessor-set.{spec,interface}.md`다. design 30·계획·`docs/03-analysis/…30-module-split/` 변경은 0이다.
* SR diff는 −5/+4이고 4개 hunk가 모두 `run_matching_safety_with_finger_growth` 안(11755~11878행)에 있다. docstring 1→2줄, 주석 2줄 교체, `_backfill_interdig_ok(result)` 호출 2줄 삭제다. 최상위 이름 증감은 0이다.
* blob이 `6c724de` = `863a037` = `6df4bd7`로 같은 것: H `614a933`, 레지스트리 `f2320d2`, `tools/gates` 트리 `f2356aa`, SD `9993047`, DR `aa27193`, TL `e014a7a`.

## 1. M10

| 항목 | 결과 |
|---|---|
| H·레지스트리·`tools/gates` | 바이트 같음(위 blob). `gate_config.json` `after_phase3` 첫 원소 = 진입점(그대로) |
| SR 줄 인용 | `floorplan_target.get("max_aspect_ratio")` 8984행 그대로(SR). `_topology_ref_relpath` 8942행 그대로(SD). 초안이 인용하는 SR 줄 가운데 11755행 이후는 없어 영향 0 |
| E-INST 기준 | backfill 판정 기록에서 `folded_cascode`·파일럿 instance.json 원바이트 해시가 base = 병합본이다(`8cd006a5…`·`7dc9f2e2…`, `folded_cascode` relaxed_pairs 빈 것). 계약 6 (c)의 `ef3cd996…`(b34 기록 `base_folded_cascode.json` -- 6df4bd7에 있음)와 `e_inst_p3.py` `h()`(separators 포함, 52~53행)는 그대로다 |
| `parse_spec_card`(6df4bd7 판) | 예외 없음, phase 3·red-green·gate_change no·approval [`20260930-30-module-split-design`], 절 11 |
| `interface_card.py --root <6df4bd7 사본>` | exit 0, **기존 함수 10**(`run_harness` 3·SD 3·SR 2·DR 2) + 신규 시그니처 1행(진입점). r3와 같다. `--out` 없이 돌리면 `docs/02-design/specs/<id>.interface.md`에 쓰려다 사본에서 FileNotFoundError가 난다(측정 절차 메모일 뿐 초안 영향 없음) |
| **V3 인벤토리(`run_harness.py::run`)** | gate `mutate_changed.inventory`와 `reachability.build_graph`로 직접 쟀다. **6c724de 63 → 863a037 64 → 6df4bd7 64**. 늘어난 1개는 `contracts/test_b26pre_existing_paths.py::test_b26pre_ofcb_lutless_repair`이고, 경로는 test → SR `optimize_full_circuit_budget` → `_build_theta_evaluator._evaluate` → `workspaces/current-reuse-telescopic-ota-report/spice/stage1_psrr_ngspice_crosscheck.py::report` → 그 파일 `::run` → `run_harness.py::run`(이름 과대 근사)이다. backfill test는 들지 않는다(863a037→6df4bd7 증감 0). 정렬 첫 원소가 이 b26pre test로 바뀌었다(b34 두 개보다 앞) |

**결함 1건(r3 문장 사실 오류)**: M10 초안 168행은 b26pre test에 대해 "`run`·`run_harness`·`subprocess` 이름 0이라 `run()` 인벤토리에 들지 않는다"고 적었다. 이는 틀렸다. 인벤토리는 test 본문 이름이 아니라 호출 그래프 닫힘으로 정해진다. 판정 영향은 없다(그 test는 V1 PASS이고 파일 19개 전체가 약 11 s -- b26pre 기록 `kill_results.jsonl` `sec` 10.7~11.9). V3 시간은 죽는 변이마다 그 test 1개만큼 늘 수 있다.

### M10 제안 편집

1. **10행(머리 괄호)**: "gate `master` `863a037` 판 -- … test 1파일(`A/tests/contracts/test_b26pre_existing_paths.py`)뿐" → 아래로 바꾼다.
   > gate `master` `6df4bd7` 판 -- `6c724de`(…)에 b26pre spec card 개정·test·판정 기록, backfill spec·interface card·test·code·판정 기록, B40 승인 기록, B26-1 spec·interface card를 더한 판. `git diff --name-only 6c724de 6df4bd7 -- tools skills workspaces <레지스트리>` = test 2파일(`A/tests/contracts/test_b26pre_existing_paths.py`·`test_b26_backfill_interdig.py`) + `A/sizing_recipe.py`(`run_matching_safety_with_finger_growth` 본문 −5/+4 -- 11755행 이후, 이 card가 인용하는 줄 밖) -- H·레지스트리·`tools/gates` 바이트 같음
2. **167~169행(작성 전 실측 머리)**: 끝에 r4 문장을 더한다.
   > r4(2026-10-07): gate `master`는 **`6df4bd7`**. `863a037..6df4bd7`(`3004096` backfill test·`495bb0e` code·`0bb2278` 병합·`22fd126` 판정 기록·`a6eaec3` B40 승인·`6df4bd7` B26-1 spec·interface card)의 `tools`·`workspaces`·레지스트리 diff는 0이다. `skills` diff는 `A/sizing_recipe.py`(11755~11878행, `run_matching_safety_with_finger_growth` 안 -- 최상위 이름 증감 0, 이 card가 인용하는 SR 8984행·SD 8942행 그대로)와 새 test `A/tests/contracts/test_b26_backfill_interdig.py`(test 5)뿐이다. backfill 판정 기록상 E-INST `folded_cascode`·파일럿 instance.json은 base와 바이트 같다.
3. **168행 정정(사실 오류)**: "(… 새 파일, `run`·`run_harness`·`subprocess` 이름 0이라 `run()` 인벤토리에 들지 않는다)" → 아래로 바꾼다.
   > (… 새 파일 -- 그 test 하나 `test_b26pre_ofcb_lutless_repair`가 SR `optimize_full_circuit_budget` → `_build_theta_evaluator._evaluate` → `workspaces/current-reuse-telescopic-ota-report/spice/stage1_psrr_ngspice_crosscheck.py::report`·`::run`의 이름 과대 근사로 `run()` 인벤토리에 든다: gate 도구로 잰 인벤토리 `6c724de` 63 → `863a037`·`6df4bd7` 64; backfill test 5개는 들지 않는다)
4. **180행(작성 전 실측 6 인벤토리)**: 문장 끝에 덧붙인다.
   > (모의 사슬 `2183f2e` 기준 관찰. gate `6df4bd7`에서는 b26pre test 1이 더해져 64 → 시제품 test를 더하면 71이고, 정렬 첫 원소가 `contracts/test_b26pre_existing_paths.py::test_b26pre_ofcb_lutless_repair`다 -- r4 실측)
5. **158행(M10-6)**: "`contracts/test_b34_grammar_explicit.py` 두 test가 새 test보다 먼저 돈다" → "`contracts/test_b26pre_existing_paths.py` 1·`contracts/test_b34_grammar_explicit.py` 2가 새 test보다 먼저 돈다(gate `6df4bd7` 인벤토리 -- 작성 전 실측 6 r4)". `m10_t1_open_items.md` 35행 M10-6도 같은 뜻으로 고친다(앞에 "`contracts/test_b26pre_existing_paths.py::test_b26pre_ofcb_lutless_repair` 1·"을 더한다).
6. **196행(작성 전 실측 12 r3 줄) 뒤**: 한 줄을 더한다.
   > r4(gate `6df4bd7` `tools/gates`·`A`·H `git archive` 사본 `C:/g425`, TMP/TEMP 그 아래, cd 없음, 끝에 삭제): `parse_spec_card` 예외 없음·같은 값(절 11), `interface_card.py --root C:/g425/t --out <사본 안>` exit 0, 기존 함수 10 + 신규 1행(같은 이름·정의 모듈).
7. **13 (iii)·계약 그 밖**: 바꿀 것 없다. 계약 10의 base 값(16 → 17, `22·16·1·1·1`)과 레지스트리 줄 번호(27·376·441~445)는 레지스트리 blob이 같아 유효하다.

## 2. T1

| 항목 | 결과 |
|---|---|
| 매핑 범위 | 새 test `contracts/test_b26_backfill_interdig.py`는 `unit/` 밖이고 `test_selftest` 문자열도 0이다(b26pre 파일도 0). `6c724de..6df4bd7` tests diff = contracts 2파일 추가(A)뿐. SR 변경은 함수 본문 안이라 R-DEF(최상위 바인딩)가 같다. 따라서 **T1 매핑 대상(옛 4파일 212 test)·규칙·k는 바뀌지 않는다** |
| V5 7경로 base blob | `6c724de` = `863a037` = `6df4bd7`: ts3 `0791457`, `test_probe_revalidation_scope.py` `4f3b7ae`, `test_probe_role_L_derivation.py` `ceefa7e`, SR selftest `aeddecf`, SD selftest `fe724a8`, DR selftest `50dae17`, TL selftest `7d6e893`. `diff_hash` `aad79872…0131`은 7경로 blob만의 함수이고 그 입력이 그대로라 **같은 모의 사슬에서 같은 값**이다. 실제 base에서는 T0가 옛 파일을 고치므로 값이 바뀔 수 있다는 기존 문장(실측 7 끝)도 그대로 유효하다. 참고: 실측 7의 옛 파일 base blob(DR `56cc5a1`·SR `5396d84`·TL `1ad977e`)은 T0 W-1 대역을 거친 사슬 값이라 gate blob과 다르다(SD `fe724a8`만 같음). 오류는 아니다 |
| V4 면제 | `.ai/approvals`에서 `863a037..6df4bd7` 사이 추가는 `20260930-b26-b40-reason-key.md` 하나이고 V4와 무관하다. `20260923-c9-v4-exempt`(s052·s054, `test_selftest_sizing_recipe.py` id)는 그대로다. `20261002-p3-t0-v4-s009-exempt`는 아직 gate에 없고, T0 판정 기록(`20260930-p3-tests-location-free`)도 없다. 초안 서술과 같다 |
| PT3 총수 | gate V1(backfill 판정 기록): base `863a037` 1109 passed·15 xfailed → 병합본(= `6df4bd7` 트리의 skills/tools) **1114 passed·15 xfailed**, 기존 id 결과 변화 0, 새 5 PASS. `6c724de` 대비 +24(b26pre 19 + backfill 5) |
| `parse_spec_card`(6df4bd7 판) | 예외 없음, phase 3·test-only·gate_change no·approval 3개, 절 11 |
| `interface_card.py --root <6df4bd7 사본>` | exit 0, **기존 함수 6**(SR `optimize_full_circuit_budget`·`size_transistor`·`width_from_id_density`·`check_quasi_static`·`_build_theta_evaluator`, SD `load_topology`), 신규 시그니처 빈 표. r2와 같다(정의 모듈은 M1~M9 미병합이라 SR·SD -- 이름 6개 같음) |

### T1 제안 편집

1. **12행(의도 머리 괄호)**: "gate `master` `863a037` 판 -- … `A/tests/contracts/test_b26pre_existing_paths.py` 추가 1파일(test 19, b26pre 2차 시도)뿐이고 `2db7622`→`863a037`은 문서만이다. 그 파일은 … PT3 총수만 +19" → 아래로 바꾼다.
   > gate `master` `6df4bd7` 판 -- 작성 전 실측을 잰 `6c724de`와 비교해 `skills`·`tools` 변경은 test 2파일 추가(`A/tests/contracts/test_b26pre_existing_paths.py` test 19 -- b26pre, `A/tests/contracts/test_b26_backfill_interdig.py` test 5 -- backfill)와 `A/sizing_recipe.py` `run_matching_safety_with_finger_growth` 본문 −5/+4(최상위 이름 증감 0)뿐이다. 두 test 파일은 `unit/` 밖이고 옛 4파일·ts3·probe 2파일과 무관하다(7경로 blob이 `6c724de`·`6df4bd7`에서 같음 -- r4 실측). 그래서 T1 매핑·V5 해시·V4 영향은 0이고 PT3 총수만 +24다. 커밋 직전 재확인 '작성 전 실측' 11 (iv)
2. **156행(작성 전 실측 머리 r3 문장)**: "gate `master` `863a037`에서도 유효하다 … PT3 총수(실측 4)는 그 판에서 +19다." → 아래로 바꾼다.
   > gate `master` `6df4bd7`에서도 유효하다: `skills`·`tools` 차이는 머리에 적은 test 2파일과 SR 함수 본문 1곳뿐이다(V5 7경로 blob `0791457`·`4f3b7ae`·`ceefa7e`·`aeddecf`·`fe724a8`·`50dae17`·`7d6e893`이 `6c724de`·`863a037`·`6df4bd7`에서 같음 -- r4). 독립 검토 r2가 `2db7622`에서 매핑·V5 해시·V4를 같은 값으로 냈다. PT3 총수(실측 4)는 그 판에서 +24다(gate 실측: `863a037` 1109 passed → `6df4bd7` 트리 1114 passed, 15 xfailed -- backfill 판정 기록 V1).
3. **178행(작성 전 실측 10) 끝**: 한 줄을 더한다.
   > r4(gate `6df4bd7` `tools/gates`·`A`·H 사본 `C:/g425`, 끝에 삭제): `parse_spec_card` 예외 없음·approval 3·절 11; `interface_card.py --root <6df4bd7 사본>` exit 0, 기존 함수 같은 6(정의 모듈 SR·SD -- M1~M9 미병합), 신규 시그니처 빈 표.
4. 그 밖(계약 1~11·R-1~R-12·재현할 수치·결정 필요 항목): 바꿀 것 없다. 계약 6의 ts3 줄 인용(27~30·68행)은 blob이 같아 그대로다. 계약 7의 "옛 id 꼴 0" 대상에 새 contracts 2파일이 더해지지만 두 파일 모두 `test_selftest` 문자열이 0이다.

## 3. open items(`m10_t1_open_items.md`)

* 35행 M10-6: 위 M10 편집 5대로 고친다.
* 4행 근거 판: `2183f2e`(r1 측정) 표기는 이력이라 그대로 둔다. 원하면 10행 r2 문단 뒤에 한 줄을 더한다: "r4(2026-10-07): gate `6df4bd7` 재확인 -- `_drafts/m10_t1_at_6df4bd7.md`. 결론: 사용자 질문 수 변화 0, M10 사실 문장 1 정정(b26pre test가 `run()` 인벤토리에 듦)".
* 사용자 질문은 그대로 T1-2 하나다.
