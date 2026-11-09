# T0 키트 점검 -- gate `master` `6df4bd7` (b26pre·backfill 병합 뒤, B26-1 spec card 커밋 뒤)

작성 2026-10-07. 읽기 전용 점검이다. 키트, 초안, 승인 기록은 고치지 않았다. 실제 저장소는 `git -C`로 읽기만 했다.
측정은 `C:/g421`에서만 했다. clone은 `-c core.autocrlf=false`로 받고 origin을 지웠다. TMP/TEMP는 `C:/g421/tmp`로 두었고, 끝에 폴더를 지웠다.
출력 사본은 세션 scratchpad `g421_out/`에 있다. 게이트 캐시는 `git archive 6df4bd7 tools/gates`로 만들었다. Python 3.14.2.
끝난 뒤 실제 저장소 상태: HEAD = gate/master = `6df4bd7`, reflog 최상단이 그대로이고, `git status`는 세션 시작 snapshot과 같다.

## 결론

**멈출 것 없음(STOP 0). A군 0, 계약 표와 수치 변화 0.** `2183f2e..6df4bd7`에서 판정에 닿는 변경은 다음 셋뿐이다.
`sizing_recipe.py` 4+/5-(11755~11878 `run_matching_safety_with_finger_growth`의 docstring·주석과 `_backfill_interdig_ok` 호출 2줄 삭제), 새 계약 test 두 파일이다.
`tools/`, 계획서, `docs/02-design/features`, `run_harness.py`, design 10, unit selftest 3파일, A군 3파일은 바뀌지 않았다.

* (라) 새 두 파일은 모두 **B군**(F1 몫)이다. T0 범위는 그대로다.
* (아) `step0_v4.sh` 결과는 **지금 `판단: MATCH`**이다. `v4_summary.txt`, 생성 interface card, `diff_paths.txt`가 r2t(`out/r2t_4a286f0/`)와 **바이트 같다**.
  그러나 MATCH 줄은 **지금 채우지 않는다**. B26-1(과 B33) 병합 뒤에 다시 재서 채운다. 이유는 3절에 있다.
* V5는 새 파일과 무관하다. 모의 T에서 `diff_paths`(contracts 3), 발견 4, `diff_hash` `ac45a98a…`가 r2t와 같다.
* 문장 drift는 6건이다(아래 E1~E6). 모두 사실 문장이나 판정 규칙 문구이고 계약은 바뀌지 않는다. E2는 (사) 판정 규칙 문구라 착수 0단계 전에 고치는 편이 좋다.

## 1. 변경 범위(`2183f2e..6df4bd7`, `.ai/verification/**` 제외)

`.ai/approvals/20260930-b26-b40-reason-key.md`, b26pre·backfill·B26-1 spec card와 interface card(6파일), `sizing_recipe.py`,
`tests/contracts/test_b26_backfill_interdig.py`(206줄), `tests/contracts/test_b26pre_existing_paths.py`(593줄).
`git diff --stat 2183f2e 6df4bd7 -- tools docs/01-plan docs/02-design/features workspaces/run_harness.py`은 빈 출력이다.
그래서 `test_lint.py` 705(`read`)·719(`--diff-filter=AM`)·731(`rch._approved_ids(root, ns.head)`) 인용은 그대로 맞는다.
계획서 534·688·993행과 design 30 577·611·1183행 인용도 그대로다.

## 2. 착수 0단계 (가)~(사)

| 항목 | 6df4bd7 결과(`t0_facts`·`w1_lines`·`shim_import_reads`) | 판정 |
|---|---|---|
| `t0_facts` 2183f2e 대비 | 다른 키는 `filename_literal_tests`(contracts 11 → **12**, +`test_b26pre_existing_paths.py` 5건)와 `contracts_files`(+2파일) 둘뿐이다. `glob_sites`·`setattr_outside_tools`·`monkeypatch_in_tests`·`ic5_names_alldepth`·`cited_lines`·`m6_scan_names`·`rdef_*`·`binding_files_probe`·`_SIZING_RECIPE_all`·`design10_table`은 2183f2e와 같다 | 예상한 차이 |
| (가) | ic5 21개는 각각 정확히 1곳이고 줄도 2183f2e와 같다(SR 변경이 11755 뒤라 ic5 대상 줄이 밀리지 않음). `rdef_duplicate_names` {}. `rdef_probe`: SR 5개 = SR, `load_topology` = SD, `rail_declaration`·`RailDeclaration` = [](B26-1 전), `_L_ROLE_MULTIPLIERS` 0 | 성립(rail은 B26-1 뒤 다시 잼) |
| (나) | `binding_files_probe["rail_declaration"]` = [](B26-1 전) | B26-1 뒤 다시 잼 |
| (다) | `cited_lines`(dup_w_calc 56·72·75·442, df35 206, ts6_probe_relocate 528, ts6_dead_probes 60·221·222·229·261·262, dup_kcl_edges 35)가 바이트 같다 | 성립 |
| **(라)** | 새 contracts 파일 2개를 card '작성 전 실측' 9의 규칙(파일 경로 리터럴 + 엔진 소스 AST/텍스트 읽기 = 정의 위치 가정)으로 분류했다. 아래 표 | **A군 0 → B군 2(F1)** |
| (마) | `m6_scan_names`는 19eb475·2183f2e와 같고 계약 9 목록과도 같다 | 성립 |
| (바) | 2183f2e와 같다. B34 `sys.path` setattr 1건과 disc35 AST 노드 setattr 1건뿐이고, 새 두 파일에는 setattr·monkeypatch·glob이 0건이다 | 성립(2183 D3는 여전히 미반영 -- E5) |
| (사) | `w1_lines`는 `p3ud6_kit/out/w1_lines.json`과 `rev` 밖 **바이트 같다**(3파일·24행·7이름, DR 13행 `import os`). `shim_reads`는 **바이트가 다르다**: hit 32 → 36, 새 4건은 모두 `bound_by: from stick_diagram`의 `sizing_recipe.Transistor`다(test_b26pre_existing_paths.py:56, test_b26_backfill_interdig.py:72, `.ai/verification/20260930-b26-pre-test-strengthen/scripts/v4_oracle.py:22`, `.ai/verification/20261001-b26-backfill-interdig-final-audit/scripts/order7/contract2.py:29`). 계약 11 (c)는 'N3.10 파일에서 `from … import`로 받은 이름'을 빼므로, (c) 잔여는 **3파일·7이름 그대로**다(SD 경유 아닌 hit = 7, 4a286f0과 같다) | 계약 11 표 그대로. 단 키트의 '바이트 같음' 판단 문구는 고쳐야 한다(E2) |

**(라) 분류 근거(AST·텍스트 실측)**

| 파일 | import | 엔진 이름 사용(모듈.속성) | 파일 이름 리터럴 | 엔진 소스 읽기 | 분류 |
|---|---|---|---|---|---|
| `test_b26pre_existing_paths.py`(19 test) | 33 `import sizing_recipe`, 34 `import stick_diagram`(30행 `__file__`은 `sys.path`용) | `sizing_recipe.`{`size_transistor`, `Transistor`, `SizingContext`, `optimize_full_circuit_budget`, `run_matching_safety_with_finger_growth`×6, `resolve_stack_layout`}, `stick_diagram.`{`build_stick_diagram`, `run_full_circuit_audit_from_topology`, `propose_vertical_stack_id_gap_fill`×2, `load_topology`×2, `find_differential_pair_candidates`×2} | 5건(132·134·409·458·569행). 모두 docstring의 oracle 출처 서술(`sizing_recipe.py 9363~9367` 등)이다 | 0(ast·read_text·open·inspect·importlib 0) | **B군** |
| `test_b26_backfill_interdig.py`(5 test) | 49 `import sizing_recipe`(46~48행 `sys.path`) | `sizing_recipe.`{`size_transistor`, `Transistor`, `SizingContext`, `run_matching_safety_with_finger_growth`} | 0 | 0 | **B군** |

두 파일 모두 '모듈 이름으로 import'하는 B군이다. shim이 살아 있는 동안 통과하므로 F1(호출부 갱신) 몫이다.
`sizing_recipe.Transistor`는 SR이 SD에서 받은 이름이라 완전 shim에도 재수출로 남는다(계약 11 (a)와 같은 근거).
docstring 줄 번호 인용(`sizing_recipe.py 9363~9367` 등)은 판정이 아니라 서술이다. M card 이동 뒤에는 낡은 서술이 되므로 F1·M card의 문서 drift 후보로 적는다.

## 3. (아) step0_v4 -- 지금 MATCH, 그러나 채우는 것은 B26-1·B33 병합 뒤

실행: `env TMP=… bash p3kit_t0/step0_v4.sh C:/g421/iso 6df4bd7… C:/g421/cache/tools/gates _drafts/draft_p3_t0.spec.md C:/g421/out/step0_v4`(exit 0).

```
test_lint(iface, base..T) exit 1
test_lint(rail): …/test_b26_rail_accessor.py 없음(B26-1 전) -- 생략
v4_iface.json verdict FAIL files 7
  FAIL (1) test_selftest_sizing_recipe.py test_s009_revalidate_finger_override 719
  FAIL (1) test_selftest_sizing_recipe.py test_s009_revalidate_finger_override 744
counts {('(2)', 'NO-SUBJECT'): 241, ('(1)', 'FAIL'): 2, ('(2)', 'UNJUDGED'): 78} UNJUDGED 78
UNJUDGED assert 식 = TS2 병합본(caac910) 식: 78 / 78, 다름 []
FAIL ids ['skills/analog-gmid-design/assets/tests/unit/test_selftest_sizing_recipe.py::test_s009_revalidate_finger_override']
판단: MATCH
```

`v4_summary.txt`, `t0.ifc.md`(기존 함수 6), `diff_paths.txt`(7파일)는 `p3kit_t0/out/r2t_4a286f0/`의 같은 이름 파일과 `cmp` 결과 같다.
새 두 파일은 T0 diff 밖이라 V4 대상이 아니다(`--diff-filter=AM`). b26pre·backfill은 unit selftest 3파일을 바꾸지 않았다(`git diff --name-only 4a286f0 6df4bd7 -- tests/unit` 빈 출력).

**지금 MATCH 줄을 채우면 안 되는 이유**(그래서 "B26-1/B33 뒤에만"):
1. 승인 기록 105행 자리표시자 문언이 "착수 0단계(`p3kit_t0/step0_v4.sh`) **B26-1 병합본** 재측정 = <…>"이다. 6df4bd7 값으로 채우면 기록이 사실과 맞지 않는다.
2. B26-1 spec card(이제 gate에 있음, `docs/02-design/specs/20260930-b26-rail-accessor-set.spec.md` 518~530행 계약 12 입력 갱신)는
   **`test_selftest_sizing_recipe.py` 15곳**(180·237·289·457·585·878·1008·1899·1924·1987·2079·2161·2227·2273·2459행, `supply_nets`·`rails=`)을 바꾼다.
   또 test가 `RailDeclaration`을 `stick_diagram.rail_declaration(<topology dict>)`로 얻게 한다(186~187행). 그래서 V4가 파일 전체를 보는 그 파일의 내용, test_s009 줄 번호(지금 T 719·744 / base 714·739), UNJUDGED 집합이 달라질 수 있다.
3. B26-1 뒤에는 card 백틱 토큰 `rail_declaration`이 엔진 정의(SD)와 맞아 interface card에 `stick_diagram.rail_declaration` 행이 더해진다(`t0_launch.sh` IFC_OPT).
   그러면 피검이 7개가 되고, unit 3파일에서 `rail_declaration(...)` 출력이 판정식 양쪽에 남는 줄이 새 규칙 (1) FAIL이 될 수 있다. 사용자 답은 test_s009 id 하나만 덮는다.
4. `step0_v4.sh`는 `test_b26_rail_accessor.py`가 있을 때만 그 파일도 lint한다. 지금은 생략된다(위 출력 2행).
5. `t0_launch.sh pre`는 measured rev가 PRED 5개(B26-1·B33 포함) 판정 기록을 담기를 요구한다(315행). B33(`tools/gates/reachability.py`)은 V4가 읽는 `_approved_ids`의 모듈이기도 하다.
   그래서 MATCH 측정 rev = measured rev = B33 병합 뒤 gate master여야 한 줄로 맞는다.

결론: **지금 재면 MATCH(r2t와 바이트 같음)다. 그러나 MATCH 줄은 B26-1·B33 병합 뒤 착수 0단계 (아)에서 다시 재서 채운다.** 지금 값은 "b26pre·backfill은 V4 결과를 바꾸지 않았다"는 리허설 증거로만 쓴다.

모래상자 `t0_launch.sh --repo … conds`(gate = 로컬 bare 사본, 실제 저장소 무관) 결과: `1:0 2:0 3:0 4:0 5:0 6:0 7:128 8:128 9:128 10:0 11:128` → exit 3.
조건 5·6(b26pre·backfill)은 lc_pred_ok까지 통과한다. 남은 것은 7 B26-1, 8 B33, 9 rail test, 11 V4 면제 기록뿐이다. spec 초안 measured rev는 '없음'(정상)이다.

## 4. 범위 수치 대조(card·브리프 숫자 vs 6df4bd7)

T0는 test를 옮기지 않는다(test id 불변, 바뀐 경로 8). 아래 표는 card와 브리프가 적은 수와 지금 수를 나란히 놓은 것이다.

| 수 | card·브리프 | 6df4bd7 | 비고 |
|---|---|---|---|
| 바뀌는 파일(계약 8, `t0_carry.sh` EXPECT8) | 8 | 8(B26-1 전 모의 T는 7 -- rail test 없음) | 그대로 |
| 계약 11 | 3파일·3줄·7이름(서로 다른 6) | 같음 | 그대로 |
| ic5 표 | 21 | 21, 각 1곳 | 그대로 |
| interface card 기존 함수 | 6(+ B26-1 뒤 `rail_declaration` 1) | 6 | 그대로 |
| V4 모의 T | FAIL 2(test_s009) · UNJUDGED 78 · NO-SUBJECT 241 · files 7 | 같음 | 그대로 |
| V5 모의 T | 발견 4(비교 완화 1 + 리터럴 3), `diff_paths` contracts 3 | 같음, `diff_hash` `ac45a98ab1c50478…` = r2t | 그대로 |
| 세 contracts 파일 수집 id | 141 | 141(ic5 9 + dup_w_calc 106 + ts6_dead_probes 26) | 그대로 |
| unit 3파일 수집 id | -- | 82(TL 10 + SR 68 + DR 4) | 참고 |
| 전체 PT3 수집 id | 브리프 1062(4a286f0)·1105(2183f2e) | **1129**(`--collect-only --gmid-phase=3`, 12초). b26pre +19, backfill +5. 판정 수는 b26bf 판정 기록 V1 "M 1114 passed·15 xfailed"(직접 재지 않음) | 브리프 숫자만 낡음(E4) -- 판정은 관계라 영향 없음 |
| `filename_literal_tests` contracts | spec 1 '10'(cd64170) / 키트 v9 '11' | **12** | E3 |

## 5. V5 diff 경로·해시와 새 test 파일의 관계

* `weakening_diff`의 `diff_paths`는 발견이 있는 경로(T0 diff 안의 contracts 3파일)뿐이다. `diff_hash`는 그 경로들의 base/head blob으로 정해진다.
  새 두 파일은 T0 diff 밖이다(T0가 바꾸지 않음, 계약 8). 그래서 경로에도 해시에도 들어갈 수 없다.
* 세 경로의 base blob은 `4a286f0..6df4bd7`에서 바뀌지 않았다(`git diff --name-only` 빈 출력). 그래서 같은 모의 T의 해시가 r2t와 같다(`ac45a98a…`).
  실제 해시는 1차 T1에서 `t0_carry.sh prep`이 잰다. 그 값은 B26-1이 이 세 파일을 바꾸는지에 달려 있다. B26-1 계약 12는 `test_dup_w_calc`·`test_ic5`·`test_ts6_dead_probes`를 대상으로 적지 않았지만, 착수 0단계 (다)가 확인한다.
* `t0_carry.sh` EXPECT8, `diff_paths ⊆ 바뀐 경로` 단언(230행), `findings path = diff_paths`(232행)는 새 파일과 무관하다.
* 승인 초안 `approval_20260930-p3-tests-location-free.md`에는 새 파일을 언급할 자리가 없다. 바꿀 것 없음.

## 6. 인용 줄 이동

* 엔진·test 쪽 인용은 이동 0이다. SR 37·38·42·45·1411~1412, TL 26, DR 30, unit 24행, test_s009 719·744(T)/714·739(base), 계약 test 인용 줄 모두 그대로다(SR 변경은 11755행 뒤, -1줄).
  `ic5_names_alldepth`도 줄까지 같다. `tools/gates` 인용(test_lint 705·719·731 등)도 그대로다.
* **키트 안 drift(6df4bd7과 무관, 키트 자체 변경 때문)**: `t0_briefs.md:44`의 "`stage_pre` → `meas_rev`, 124~129행"이 가리키는 곳은
  현재 `t0_launch.sh`(2026-10-07 13:05판)에서 `meas_rev()` **127~132행**이다(E6).

## 7. 제안 편집(정확한 문자열 -- 적용은 오케스트레이터)

**E1** `_drafts/draft_p3_t0.spec.md` 238행('작성 전 실측' 7). 아래 old를 찾아 new로 바꾼다.
```
old: 7. 기존 계약 test: 바뀌는 것이 계약 test 자체 -- V5 승인 경로(결정 필요 항목). B군 11파일은 F1(v5: + `test_b34_grammar_explicit.py`, `test_b26_rail_accessor.py`의 이름 호출 test).
new: 7. 기존 계약 test: 바뀌는 것이 계약 test 자체 -- V5 승인 경로(결정 필요 항목). B군 11파일은 F1(v5: + `test_b34_grammar_explicit.py`, `test_b26_rail_accessor.py`의 이름 호출 test;
   `6df4bd7` 재측정: + b26pre `test_b26pre_existing_paths.py`(33·34행 `import sizing_recipe`·`import stick_diagram`, 모듈 속성 호출 11종) + backfill `test_b26_backfill_interdig.py`(49행 `import sizing_recipe`, 4종) -- 둘 다 엔진 소스 읽기 0).
```

**E1'** 같은 파일 247~249행('작성 전 실측' 9) 끝에 아래 문장을 더한다. old는 249행의 끝 구절이다.
```
old: A군이 새로 나오면 이 card의 범위를 넓히는 개정(spec card 재작성)이고, B군은 F1 목록에 더한다.
new: A군이 새로 나오면 이 card의 범위를 넓히는 개정(spec card 재작성)이고, B군은 F1 목록에 더한다.
   (`6df4bd7` 재측정, `_drafts/t0_at_6df4bd7.md` 2절) b26pre `test_b26pre_existing_paths.py` = **B군**(파일 이름 리터럴 5건 132·134·409·458·569행은 모두 docstring의 oracle 출처 서술, ast·read_text·open 0),
   backfill `test_b26_backfill_interdig.py` = **B군**(리터럴 0, 엔진 소스 읽기 0). A군 0 -- 범위 그대로. 두 파일의 `sizing_recipe.Transistor`(SR이 SD에서 받은 이름)는 계약 11 (c) 정의상 잔여 밖.
```

**E2** `_drafts/t0_launch.sh` 260행 주석과 `_drafts/t0_briefs.md` 31행((사) 판단 규칙). `shim_reads`는 바이트 대조가 아니라 (c) 잔여로 판단해야 한다.
```
t0_launch.sh
old: #   (사) p3ud6_kit/out/w1_lines.json·shim_reads_4a286f0.json과 rev 밖 대조 -- 3파일·7이름·출처 줄 그대로면 계약 11 표 그대로. 이름이 늘거나(B26-1이 SD 이름을
new: #   (사) w1_lines는 p3ud6_kit/out/w1_lines.json과 rev 밖 바이트 대조. shim_reads는 바이트가 아니라 계약 11 (c) 잔여(hits 중 bound_by가 'from stick_diagram'(N3.10 파일)이 아닌 것)가
#        3파일·7이름인지로 본다(6df4bd7: hits 36 = 4a286f0 32 + b26pre·backfill의 sizing_recipe.Transistor 4건, 모두 from stick_diagram -- 잔여 7 그대로). 이름이 늘거나(B26-1이 SD 이름을

t0_briefs.md 31행
old: **(사)(r2t, S3) 계약 11 재측정**: `w1_lines`·`shim_reads`를 `p3ud6_kit/out/w1_lines.json`·`p3ud6_kit/out/shim_reads_4a286f0.json`과 `rev` 밖 대조 -- 3파일·7이름·각 파일 import 줄 모양(한 줄 괄호)·엔진 쪽 출처 줄이 그대로인지.
new: **(사)(r2t, S3) 계약 11 재측정**: `w1_lines`를 `p3ud6_kit/out/w1_lines.json`과 `rev` 밖 대조(3파일·7이름·각 파일 import 줄 모양(한 줄 괄호)·엔진 쪽 출처 줄), `shim_reads`는 바이트가 아니라
(c) 잔여(`bound_by`가 `from stick_diagram`이 아닌 hit)가 3파일·7이름인지로 본다(`6df4bd7`: hits 36, 새 4건 = b26pre·backfill 계약 test와 판정 스크립트의 `sizing_recipe.Transistor` -- 모두 SD 경유, 잔여 7 그대로).
```

**E3** `_drafts/draft_p3_t0.spec.md` 219~220행('키트 v9' 문단). old는 219행 안의 한 구절이다.
```
old: 1의 'contracts 10파일'은 `0f23786`부터 **11파일**(`test_df23_inventory.py` 2건 -- 320·367행 합성 입력 문자열, A군 아님).
new: 1의 'contracts 10파일'은 `0f23786`부터 **11파일**(`test_df23_inventory.py` 2건 -- 320·367행 합성 입력 문자열, A군 아님), `6df4bd7`(b26pre 병합 뒤)부터 **12파일**(`test_b26pre_existing_paths.py` 5건 -- docstring 서술, A군 아님).
```

**E4** `_drafts/t0_briefs.md` 162행과 212행(PT3 관찰 수). 두 곳 모두 아래 old 구절을 new로 바꾼다.
```
old: gate `master` `2183f2e`(B34 병합 뒤) 관찰 **1090 passed 15 xfailed, id 1105**(B34 +43)
new: gate `master` `2183f2e`(B34 병합 뒤) 관찰 **1090 passed 15 xfailed, id 1105**(B34 +43), `6df4bd7`(b26pre·backfill 병합 뒤) 수집 **id 1129**(+19·+5, 판정 기록 b26bf V1 M 1114 passed·15 xfailed)
```
(162행에는 `**` 없이 "gate `master` `2183f2e`(B34 병합 뒤) 관찰은 1090 passed 15 xfailed, id 1105"로 적혀 있다. 그 끝에 같은 괄호 구절 "`6df4bd7` 수집 id 1129(b26bf V1 1114 passed·15 xfailed)"를 더한다.)

**E5** `_drafts/t0_briefs.md` 93행(0.3 표 backfill 행). 사실 정정이다.
```
old: | backfill `20261001-b26-backfill-interdig-final-audit` | 엔진(SD `run_matching_safety_with_finger_growth`·`_fixup_euler_blocked_rows` 근처), 새 계약 test `test_b26_backfill_interdig.py` | 분류, R-DEF 유일성 |
new: | backfill `20261001-b26-backfill-interdig-final-audit` | 엔진(**SR** `run_matching_safety_with_finger_growth` 11755~11878 -- docstring·주석과 `_backfill_interdig_ok` 호출 2줄 삭제, 4+/5-), 새 계약 test `test_b26_backfill_interdig.py` | `6df4bd7` 확인: B군, R-DEF 중복 {}, ic5 줄 불변 |
```
같은 표 92행 b26pre 행의 '착수 때' 칸 "A/B군 분류, `rglob` 전수 스캔 토큰 충돌 없음" 뒤에는 "-- `6df4bd7` 확인: B군, glob 0"을 더한다.
2183f2e 점검의 D3(spec 244~246행 disc35 분류 문장)는 이미 반영되어 있다. 지금 판에서 남은 조치는 없다.

**E6** `_drafts/t0_briefs.md` 44행(키트 안 줄 인용). 같은 줄의 다른 문구는 그대로 둔다.
```
old: `t0_launch.sh pre`(`stage_pre` → `meas_rev`, 124~129행)
new: `t0_launch.sh pre`(`stage_pre` → `meas_rev`, 127~132행)
```

**(선택) E7** `_drafts/t0_launch.sh` 255행 "rdef_probe(SR 4개, …)"와 `t0_briefs.md` 27행 (가)의 SR 이름 4개(`size_transistor`·`check_quasi_static`·`_build_theta_evaluator`·`audit_vsb_consistency`).
`t0_facts.py`의 probe에는 `width_from_id_density`도 있어 SR 5개다(2183f2e 점검도 'SR 5개'로 적었다).
판정에는 영향이 없다. 맞추려면 "SR 4개"를 "SR 5개(+ width_from_id_density)"로 바꾼다.

**바꾸지 않는 것**: `approval_20261002-p3-t0-v4-s009-exempt.md`의 `<MATCH 결과 줄 …>`(3절 -- B26-1·B33 뒤 채움), `approval_20260930-p3-tests-location-free.md`(5절),
`t0_carry.sh`(EXPECT8·diff_paths 단언은 새 파일과 무관), spec 계약 1~11·'결정 필요 항목'(수치 불변).

## 8. 남은 것(B26-1·B33 병합 뒤 다시 잴 것)

(가)·(나) `rail_declaration` = SD 1과 binding_files, (다) B26-1 계약 12가 A군 3파일·unit 3파일 줄을 밀었는지, (사) SR selftest 24행 이름 목록 변화,
**(아) MATCH 재측정(rail test lint 포함, interface card 7행 가능) → 그 판단 줄로 면제 기록 채움**, (자) 계약 10 dry run, measured 줄 삽입.
