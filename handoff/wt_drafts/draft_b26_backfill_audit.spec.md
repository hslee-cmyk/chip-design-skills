---
id: 20261001-b26-backfill-interdig-final-audit
phase: 3
evidence_type: red-green
gate_change: no
approval: 20261001-b26-backfill-interdig-fix
approval: 20261001-b26-phase3-cards
---
## 의도

`run_matching_safety_with_finger_growth`(A/sizing_recipe.py, A = `skills/analog-gmid-design/assets`)가 돌려주는 `relaxed_pairs[i]["interdig_ok"]`가 **같은 반환의 `audit`과 어긋나는** 입력이 있다.
이 card는 그 불일치를 red test로 고정하고, `interdig_ok`를 반환 `audit`(최종 물리 구조)으로 채우게 고친다.

**결함으로 보는 근거 -- 코드 자신이 적은 의도(gate `master` `2183f2e` 줄 번호, 원문 그대로 -- 글은 `0f23786`·a796468과 같고, B34가 6510~6512 docstring을 한 줄 줄여 이 card의 sizing_recipe 줄 인용은 그 판보다 전부 −1이다)**:
* `_finalize` 앞 주석, A/sizing_recipe.py:11783~11785:
  > `# 이 함수의 **모든** 반환 지점에서 최종 rows/ctx를 내보내기 전에 반드시 이 euler`
  > `# 정리를 거치고 그 결과로 audit을 다시 계산한다 -- 그래야 반환되는 audit이 실제로`
  > `# 저장/보고될 최종 물리 구조와 항상 일치한다(저장 버그와 같은 종류의 불일치 재발 방지).`
* `_backfill_interdig_ok` 안 주석, A/sizing_recipe.py:11768~11769:
  > `# 완화를 적용한 라운드에는 아직 그 결과가 반영된 audit이 없어 interdig_ok=None으로`
  > `# 남겨뒀다 -- 다음 라운드에 새로 계산된 audit_result가 나오면 그 3b 체크로 채운다.`
* 반환 docstring(같은 파일 11757~11758): `"relaxed_pairs": [{"pair":(a,b), "reason":"gm_id_budget_exceeded", "trim_recommended":True, "interdig_ok":bool|None}, ...]`.
* 첫 주석은 **audit**이 최종 물리 구조와 일치한다고 말하고, `interdig_ok`를 직접 말하지 않는다. 둘째 주석은 `interdig_ok`를 audit의 3b 체크로 채운다고 말한다. 결함이라는 판단은 두 주석을 **결합한 해석**이다. 그래서 고칠지는 사용자 결정 U-BF로 정했고(2026-10-01 답 '결함으로 고침 (Recommended)', 승인 기록 `20261001-b26-backfill-interdig-fix`), 계약 1의 oracle은 그 결정이다.

**어떻게 어긋나는가(base 동작)**:
* `_backfill_interdig_ok`는 `interdig_ok`가 `None`인 항목만 채운다(11771~11772 `if entry["interdig_ok"] is not None: continue`).
* 루프 안(11799)과 루프 뒤(11878)에서 **euler 정리 전** audit으로 먼저 부른다. 그 뒤 `_finalize`(11786~11793)가 정리한 행으로 audit을 다시 계산하고 같은 backfill을 부르지만, 이미 채워진 항목은 건너뛴다.
* 그래서 정리가 완화 쌍이 든 행을 바꾸면(아래 재현), `interdig_ok`는 **정리 전 행**의 3b이고 반환 `audit`·`rows`는 **정리 후 행**이다.
* 경위: backfill은 세션17(완화 도입), `_finalize`는 세션31(2026-08-13)에 들어왔다. `.ai/context.md` 1558~1561(세션17 '알려진 한계')은 "`interdig_ok`가 `False`로 나오는 실제 사례 … 는 아직 self-test로 직접 확인 안 함"이라고 적었다.

**재현(합성, a796468·a796468+B34 둘 다 같음 -- `_drafts/b26pre_v2_scripts/bf_repro.py`; 독립 검토가 gate `0f23786` 사본에서 다시 재서 같았다)**:
* 행 `{"seg1": [Ma, Mb, Mp]}`: `Ma(nmos, source="n2", drain="n1", gate="ga")`, `Mb(nmos, source="n4", drain="n2", gate="gb")`, `Mp(nmos, source="n2", drain="n5", gate="gp")`, 모두 `n_fingers=1`, `finger_w=W0`, `stack_id="seg1"`.
  넷 `n2`가 차수 3, `n1`·`n4`·`n5`가 차수 1이라 이 행은 euler-blocked다(`build_stick_diagram(행)["seg1"].status == "blocked"` 실측).
* 매칭 `[("Ma","Mb")]`, `{("Ma","Mb"): "offset"}`, `lut_by_kind={"nmos": toy_lut}`, metrics `{}`, constraints `[]`, `gm_id_bounds=(11.9, 12.1)`(핑거증가가 gm/ID 위반 → 완화).
* 결과(max_rounds 1·2·3·5, metrics 있음·없음 모두 같다):
  * `relaxed_pairs == [{"pair": ("Ma","Mb"), …, "interdig_ok": False}]`
  * 반환 `audit`의 `3b. interdigitation[Ma/Mb] [참고용 -- 이 kind는 필수 아님]`은 `ok = True`(offset 쌍에서 3b는 참고용 체크다 -- 필수는 3c라 `audit.ok`는 계속 `False`)
  * 반환 `rows == {"seg1_seg0": [Mp], "seg1_seg1": [Mb, Ma]}`(정리가 행을 둘로 나눴다)
  * `unresolved_reason`: max_rounds=1이면 `"max_rounds_exceeded"`(루프 뒤 11878 경로), 2 이상이면 `"relaxed_to_layout"`(루프 안 11799 경로)
* 소비처(gate `0f23786` `git grep interdig_ok -- '*.py'`): 엔진 자신과 `A/tests/unit/test_selftest_sizing_recipe.py:1480`(`is not None`만 단언)뿐이다. 이 값을 읽어 분기하는 운영 코드는 없다.
  `optimize_full_circuit_budget`은 `relaxed_pairs`를 `pipeline_result`로 넘긴다(보고 경로).

**사용자 결정**(엔진 관찰 가능 동작 변경): U-BF '결함으로 고침 (Recommended)'(2026-10-01) -- 승인 기록 `20261001-b26-backfill-interdig-fix`(`target_kind: decision`). 그 기록이 gate `master`에 있어야 착수한다(착수 조건).

## 관찰 가능한 계약

피검 함수: `sizing_recipe.run_matching_safety_with_finger_growth`(시그니처 불변). 입력을 만드는 데만 쓰는 기존 공개 심볼(피검이 아니다): `sizing_recipe.size_transistor`.

공통 입력: 위 '재현'의 행·매칭·인자. `W0`·사이징 항목 `S`·`ctx`는 `_drafts/draft_b26pre.spec.md` '공통 입력(계약 1~3)'과 같은 정의다(`size_transistor(gm=200e-6, gm_id=12.0, L=0.5e-6, lut=toy_lut, vds=0.6)`, `SizingContext(sized={…: dict(S)}, topology_path=<합성 topology>)`).
합성 topology는 `tmp_path`에 쓰고 `supply_nets: ["vdd", "gnd"]`를 선언한다(B26-1 뒤에도 같은 판정). 새 test 파일 하나: `A/tests/contracts/test_b26_backfill_interdig.py`, 함수 이름 `test_b26bf_`·도우미 `_b26bf_`로 시작.

1. **반환 `interdig_ok` = 반환 audit의 3b**(모든 반환 경로) -- 피검 `sizing_recipe.run_matching_safety_with_finger_growth`
   * `res = run_matching_safety_with_finger_growth({"seg1": 행}, [("Ma","Mb")], {("Ma","Mb"): "offset"}, ctx, {"nmos": toy_lut}, {}, [], gm_id_bounds=(11.9, 12.1), max_rounds=m)`.
   * 판정 `CONSISTENT(res)`: `[e["pair"] for e in res["relaxed_pairs"]] == [("Ma","Mb")]`이고, 각 항목 `e`(쌍 `(a, b)`)에 대해 `res["audit"].checks` 중 이름이 `"3b."`로 시작하고 `f"[{a}/{b}]"`를 담은 체크가 정확히 1개이며 `e["interdig_ok"] is <그 체크>.ok`다.
   * (a) 루프 안 경로: `m = 2` → `res["unresolved_reason"] == "relaxed_to_layout"`이고 `CONSISTENT(res)`.
   * (b) 루프 뒤 경로: `m = 1` → `res["unresolved_reason"] == "max_rounds_exceeded"`이고 `CONSISTENT(res)`.
   * 두 경우를 별개 test 함수로 둔다.
   * **반환 자리마다 test(원칙 -- '모든 반환 경로'를 test로 덮는다)**: 이 함수의 반환 자리는 다섯이다(gate `2183f2e` A/sizing_recipe.py 줄 -- `0f23786`보다 −1, `unresolved_reason` 값으로 구별 -- 반환 docstring에 적힌 관찰 가능한 값):
     (i) 성공 `None`(`return` 11802~11804), (ii) `"relaxed_to_layout"`(11828~11830, 위 (a)), (iii) `"pair_not_found"`(11836~11838), (iv) 증가 미적용 `"no_finger_w"`·`"gm_id_violation"`·`"growth_not_applicable"`(11862~11864), (v) `"max_rounds_exceeded"`(11880~11883, 위 (b)).
     `relaxed_pairs`가 비어 있지 않을 수 있는 자리마다 `CONSISTENT(res)` test를 하나씩 둔다. (iii)·(iv)는 완화된 쌍이 이미 있는 상태에서 **다음 라운드의 다른 쌍**이 그 사유로 멈추는 입력이 필요하다
     (예: 매칭 쌍 둘 -- 첫 쌍은 위 gm/ID 범위로 완화, 둘째 쌍은 `finger_w` 없음(`"no_finger_w"`) 또는 증가가 적용되지 않는 쌍(`"growth_not_applicable"` -- 파일럿 `current_reuse_telescopic_ota`가 이 사유로 완화 2쌍을 든 채 반환한다, 독립 검토 실측 `_drafts/review_backfill_kit.md` §3)).
     (i)은 반환 docstring이 "완화가 적용된 뒤에도 `audit.ok`는 여전히 그 pair의 3c FAIL을 정직하게 반영한다"고 적어 `relaxed_pairs`가 비지 않은 채 도달하지 않는 자리다(미측정 -- 서술 근거).
     **합성 입력을 만들지 못한 자리는 그 사실을 적는다**: test-author는 시도한 입력과 결과(`unresolved_reason`·`relaxed_pairs`)를 새 test 파일 머리 docstring과 보고에 적고, 그 자리는 구조 보장(수정 뒤 모든 반환이 정리 함수 `_finalize`를 거치고 그 안의 backfill이 최종 audit으로 채운다)으로 남는다 -- auditor가 병합본 코드에서 반환 자리마다 `_finalize` 경유를 읽어 판정 기록에 적는다.
     (a)(b) 밖의 자리 test는 base에서 red일 필요가 없다(관계 단언이라 base에서 정리가 행을 바꾸지 않는 입력이면 green이다). red 증거는 (a)(b)다.
   * 기대값의 근거는 사용자 결정 U-BF(oracle (d), 아래 oracle 절)다. 그 결정의 근거는 위 11783~11785 주석(반환 audit = 최종 물리 구조)과 11768~11769 주석(interdig_ok는 audit의 3b 체크로 채운다)의 결합이다. 기대 `True`를 숫자로 박지 않고 반환 audit과의 일치로 적는다.
2. **바뀌지 않는 것**: 같은 입력에서 `rows`(행 키와 소자 이름·`n_fingers`·`stack_id`), `audit`의 체크 이름·`ok` 목록, `unresolved_pair`·`unresolved_reason`·`growth_rounds` 길이는 base와 같다.
   (backfill은 `relaxed_pairs` 항목만 쓴다.) 이 계약은 auditor가 base·병합본에서 같은 호출로 대조한다(영구 test로 base 값을 박지 않는다).
3. **기존 test 불변**: 기존 test 전부가 병합본에서 PASS한다. 특히 `test_selftest_sizing_recipe.py`의 L4e(`interdig_ok is not None`, `unresolved_reason == "relaxed_to_layout"`, `audit.ok` False)는 그대로다.

구현 방식은 code-author 몫이다. 사전 측정한 후보 하나: 루프 안·루프 뒤의 사전 backfill 호출(11799·11878) 두 줄을 지우고 정리 함수 안의 호출만 남긴다(모든 반환이 정리 함수를 거치므로 항목은 반드시 채워진다).
그때 11768~11769 주석과 반환 docstring의 `interdig_ok` 설명을 '최종 audit(정리 뒤)으로 채운다'로 고친다(코드 주석·docstring은 V 판정 밖이지만 거짓 서술로 남기지 않는다).

**이름(입력·판정용 -- test-author가 소스 열람 없이 쓰는 이름)**:
* 피검 진입점: `sizing_recipe.run_matching_safety_with_finger_growth(rows, matching_pairs, pair_sensitivity, ctx, lut_by_kind, metrics_specs, constraints, gm_id_bounds=…, max_rounds=…)` -- 앞 7개는 위치 인자, `gm_id_bounds`·`max_rounds`는 키워드로 준다. 정확한 시그니처는 interface card 심볼 표가 정본이다.
* 입력용 기존 공개 심볼: `sizing_recipe.size_transistor`, 클래스 SizingContext(필드 `sized`·`topology_path`, 생성자로만 쓴다), 클래스 Transistor(이름·kind는 위치 인자, 나머지 `source`·`drain`·`gate`·`n_fingers`·`finger_w`·`stack_id`는 키워드), 픽스처 `toy_lut`(LUT 메서드 `gm_gds_ratio`).
* 반환 dict 키: `relaxed_pairs`(원소 키 `pair`·`interdig_ok`)·`audit`·`unresolved_reason`.
* `unresolved_reason` 값(반환 자리 구별, 계약 1): `None`, `"relaxed_to_layout"`, `"pair_not_found"`, `"no_finger_w"`, `"gm_id_violation"`, `"growth_not_applicable"`, `"max_rounds_exceeded"`.
* 결과 객체 필드: AuditResult `.checks`(목록), AuditCheck `.name`(str)·`.ok`(bool).
* 체크 이름 접두사: `"3b."`.

## 신규 시그니처

| 모듈 | 심볼 | 시그니처 |
|---|---|---|

## 판정 유형 근거

red-green이다. 관찰 가능한 반환값(`relaxed_pairs[i]["interdig_ok"]`)이 바뀐다.
* red: test 커밋만 있는 상태(base 엔진)에서 계약 1의 두 test가 `AssertionError`로 실패한다(`e["interdig_ok"] is c.ok` -- False 대 True). 새 심볼이 없어 '단언 red'다.
  사전 측정(`bf_redgreen.py`): base 사본 seed 0·1에서 2 failed. 독립 검토(gate `0f23786` 사본)에서도 `assert False is True`로 같은 이유의 실패를 확인했다.
* green: 수정 후보 사본에서 seed 0·1·7 모두 2 passed.
* V2 회귀(사전 측정, `bf_fullsuite.py`, `A/tests` 전체, seed 1): 수정 후보 사본 888 passed·15 xfailed·2 failed, base 사본 886 passed·15 xfailed·4 failed.
  두 사본의 2 failed는 같은 test(`test_ts6_probe_relocate`의 `.git` 필요 2개 -- archive 사본 한계)이고, base의 나머지 2 failed는 이 card의 red 시제품 2개다. 두 사본 모두 contracts에 시제품 두 파일(b26pre 17, b26bf 2)을 넣고 쟀다. 이 측정은 B34가 없는 사본에서만 했다(아래 '재현할 수치'의 auditor 몫).
* V3: 바뀌는 def는 `run_matching_safety_with_finger_growth` 하나다(중첩 정리 함수·backfill 함수 포함). 대상 변이 수는 auditor가 착수 시 그 시점 V3 범위 규칙(V3 scope card 병합 여부)으로 잰다.
  사전 측정(판정 수치 아님, `_drafts/b26_backfill_briefs.md` 0.3, base = a796468 + B34 코드 + b26pre 시제품 test, head = 그 + 수정 후보 + 이 card 시제품 test, gate `master` 판 `mutate_changed.py` 함수·인자):
  범위 card 규칙(N2w)으로 대상 **4**·생존 **0**. 현재 도구(def 변이 전부)로는 97 중 생존 19 -- 모두 이 card가 바꾸지 않은 문장(기본 인자 상수 6, `result = None`, `import re`, 성공 분기 `_finalize`(b26pre 'N2d만' 등가 후보), 3c 쌍 파싱·핑거증가 뒤 ctx 갱신의 기존 test 공백 등)이고, 수정으로 새로 생긴 것은 backfill 건너뛰기 가드 2(11771·11772 -- 반환마다 한 번만 불려 등가 후보)뿐이다.
  실제 도구(a17b8bd `mutate_changed.py`, `backfill_launch.sh` v3count) 재확인: 이 card 시제품 test 없이 b26pre 시제품 test만 base에 있는 상태에서도 대상 **4**·not_targeted **93**, 4/4 killed(V3 PASS) (card 35 병합본 a17b8bd 사전 실행 2026-10-02 — 공식 병합 뒤 재확인). 착수 판정 수치는 auditor 몫이다.
  이 card는 B34 뒤(= 범위 card 병합 뒤)라 N2w가 적용된다. 범위 card 전에 착수하지 않는다.
  이 card를 `20260930-b26-pre-test-strengthen`(b26pre) **뒤**에 두면 그 card의 계약 2·3 test가 이 def 인벤토리에 들어 대부분의 반환 경로 변이를 죽인다(b26pre 사전 측정: 이 def의 표 1 문장 12개 중 9개 죽음, 남는 3개가 11799·11878와 등가 후보 11801).
* V7: 새 def 없음.

## oracle 종류와 출처

* 계약 1 -- **(d) 사용자 결정**: U-BF 승인 기록 `20261001-b26-backfill-interdig-fix`(`target_kind: decision`, target `U-BF-BACKFILL-INTERDIG`, 머리 `approval:` 줄). 결정 문장은 '`relaxed_pairs[i]["interdig_ok"]`를 반환 audit(euler 정리 뒤 최종 물리 구조)의 3b 판정으로 채운다'이다.
  * test 주석의 `oracle 대조:`에는 그 승인 기록 id를 적는다. 두 코드 주석(A/sizing_recipe.py 11783~11785, 11768~11769 원문)은 결정의 근거로 인용할 뿐 oracle 종류가 아니다.
  * 입력은 **(a) 구성**이다. 넷 차수(`n2` 차수 3, `n1`·`n4`·`n5` 차수 1 -- 홀수 차수 넷 4개)로 euler-blocked이고, 좁은 gm/ID 범위(11.9~12.1, 사이징 값 12.0 둘레)로 핑거증가가 막혀 완화된다.
  * 관계 단언이 V4 (1) '피검 함수로 기대값 만들기'가 아닌 이유: 결정된 계약이 **같은 반환 안 두 필드의 일치 자체**다. 어느 한쪽 값을 피검 호출로 얻어 숫자로 박지 않는다.
  * 검토가 선택안으로 든 구성 쪽 독립 단언(최종 rows의 `{Ma, Mb}` 행 → `interdig_ok is True`)은 넣지 않는다. rows 모양을 영구 test로 고정해 code-author 자유도를 줄이고, rows 불변은 계약 2(auditor 대조) 몫이기 때문이다.
* 계약 2 -- (c) 기존 동작 기준선. 기준선 = 착수 시 gate `master`(지금 `2183f2e` -- 엔진은 a796468에서 B34 변경(stick_diagram, sizing_recipe docstring 1곳)만 다르다 -- 다르면 auditor가 그 base에서 다시 잰다), auditor 대조.
* 작성자≠검증자: 시제품(`_drafts/b26pre_v2_scripts/proto_bf_test.py`)과 수정 후보 측정은 오케스트레이터 사전 측정 전용이다. test-author·code-author·auditor에게 건네지 않는다.

## 거부해야 할 입력

* base 엔진(사전 backfill이 정리 전 audit으로 먼저 채움) -- 계약 1 두 test 실패.
* 루프 안 또는 루프 뒤 경로 한쪽만 고친 엔진 -- 해당 경로 test 실패(그래서 두 경로를 별개 test로 둔다). 독립 검토 실측: 11799만 지우면 m=1 test 실패, 11878만 지우면 m≥2 test 실패.
* 정리 함수 안의 backfill까지 지운 엔진 -- `interdig_ok`가 `None`으로 남아 계약 1(`is c.ok`)과 기존 L4e(`is not None`) 실패.

통과해야 하는 것: 반환 `interdig_ok`를 최종 audit으로 채우는 엔진.

## library 회로 적용 여부

`relaxed_pairs`가 비어 있지 않고 완화 쌍의 행이 정리로 바뀌는 회로에서만 값이 달라진다(그 외는 무동작).
이 def의 엔진 안 호출부는 `optimize_full_circuit_budget`(gate `2183f2e` 9368, 결과는 9397에서 `pipeline_result["relaxed_pairs"]`) 하나라, library 9회로 중 harness `SPECS`에 있는 4회로의 `run_harness.run`만 닿는다(`load_topology`·`run_topology_pipeline`은 닿지 않는다).
사전 측정(판정 수치 아님, `_drafts/b26bf_kit/lib_measure.py`, a796468 + B34 + b26pre 시제품 사본 대 그 + 수정 후보 사본, 이 def를 감싸 반환만 읽음):
* `current_reuse_telescopic_ota`: 호출 1, 완화 2쌍(`M4a/M4b` `interdig_ok` True, `M3a/M3b` False) -- 둘 다 반환 audit 3b와 같다(불일치 0). 두 사본의 `interdig_ok`·`instance.json` 해시·그 밖 반환(rows·audit·사유) 같다.
* `folded_cascode`: 호출 1, 완화 0. `two_stage_ota`·`nmcnr_amplifier`: harness가 이 def 전에 `ValueError`로 멈춘다(두 사본·a796468 모두 같음, 이 card와 무관). 나머지 5회로: 호출 경로 없음.
* 따라서 library에서 수정이 바꾸는 값은 0이다. auditor는 E-INST 두 회로를 base·병합본에서 같은 방식으로 다시 재고(비교 대상은 저장소에 커밋된 `instance.json`이 아니라 **base에서 다시 만든** `instance.json`이다 -- 재생성본의 raw 해시가 커밋 파일과 base·수정 모두 같게 다르다, `_drafts/review_backfill_kit.md` m4), 달라지는 회로가 있으면 회로·쌍·전후 값을 판정 기록에 적는다.
참고(독립 검토 계측, `_drafts/review2_b26pre.md` §8): 기존 `A/tests` 전체에서 정리 함수가 비어 있지 않은 `relaxed_pairs`를 본 호출은 1회(합성 Ma/Mb selftest)이고, 사전값과 최종값이 어긋난 호출은 0회다.

## 무동작 판정 입력(무발동 값)

`relaxed_pairs == []`인 모든 호출(완화가 없으면 backfill이 할 일이 없다), 그리고 완화 쌍의 행이 정리 전후로 같은 호출(사전 audit과 최종 audit의 3b가 같다 -- 기존 L4e가 그 예).

## 재현할 수치

사전 측정(판정 수치 아님, scratch `C:/g106`, 스크립트 `_drafts/b26pre_v2_scripts/`):
* `bf_repro.py base|b34`: 위 '재현' 결과, 두 사본 같음.
* `bf_redgreen.py`: base red 2 failed(seed 0·1), 수정 후보 green 2 passed(seed 0·1·7), 수정 후보에서 b26pre 시제품 17 passed, `test_selftest_sizing_recipe.py` 66 passed·2 xfailed, `test_selftest_stick_diagram.py` 130 passed·1 xfailed.
* `bf_fullsuite.py`: 위 V2 회귀 수치(B34 없는 사본).
* 독립 검토(`_drafts/review_b26pre.md` §1 B1): 무작위 퍼즈 400건 중 1건에서도 11799 삭제가 결과를 바꿨다(같은 종류의 불일치).
* 독립 2차 검토(`_drafts/review2_b26pre.md` §2, gate `0f23786` 사본): base 886 passed·15 xfailed·4 failed, 수정 후보 888 passed·15 xfailed·2 failed -- 위 수치와 같다. 부분 수정 판별도 위 '거부해야 할 입력' 그대로다.
* B34 위 사전 측정(`_drafts/b26bf_kit/`, scratch `C:/g128`, 모의 사슬 a796468 → +B34 코드 → +b26pre 시제품 test(`BP`) → +이 card 시제품 test(`T`) → +수정 후보(`H`), git 복제본·seed 1):
  `T` 2 failed(red 2개뿐, `assert False is True`)·888 passed·15 xfailed, `H` 890 passed·15 xfailed·실패 0(`.git`이 있는 복제본이라 `test_ts6_probe_relocate`도 통과).
  auditor는 V2 회귀를 착수 base(B34·b26pre 병합본)에서 다시 잰다.

## 결정 필요 항목

* **U-BF(사용자 결정 -- 정해짐)**: 2026-10-01 답 '결함으로 고침 (Recommended)'(권고안 = 고친다, 이 card를 b26pre 뒤·B26-1 앞에). 승인 기록 `20261001-b26-backfill-interdig-fix`(`target_kind: decision`)를 이 card보다 **먼저**(별도 `Role: doc` 커밋) gate `master`에 올리고(올림 -- `19eb475`), 머리 블록의 `approval:` 줄이 그 기록을 가리킨다.
  계약 1의 oracle (d)가 이 기록이므로 기록이 gate `master`에 없으면 test-author에게 넘기지 않는다.
* **card `phase` -- 결정됨**: 머리 `phase: 3`(사용자 결정 Q-B34-PHASE "phase 3 + 정정 기록 (Recommended)"(2026-10-01, AskUserQuestion [card phase])). 순서는 Phase 2 DoD 뒤·Phase 3 M card 전 그대로이고, 머리 둘째 `approval: 20261001-b26-phase3-cards`(decision)이
  그 근거다(승인 기록 `20260930-b26-before-phase3` ③의 'Phase 2 진행 중' 문구 정정). 그 기록도 이 card보다 먼저 gate `master`에 올린다. auditor V1 명령은 `--gmid-phase=3`, Phase 2 DoD의 N6.3 목록에 들지 않는다.
* 순서(원칙 기본안): B34 → b26pre(`20260930-b26-pre-test-strengthen`) → **이 card** → B26-1.
  * B34와는 동작 접점이 없다. B34(병합 `c851e54`, code `2eb7e55`)는 stick_diagram 4 def(`_import_analog_grammar`·`find_idiom_matches`·`find_stack_edges`·`audit_theta_root_direction`)의 동작과 docstring 여럿을 바꾸고, sizing_recipe는 `resolve_stack_layout` docstring 한 곳(6510~6512, 3줄 → 2줄, 동작 무관 -- docstring을 뺀 AST로 바뀐 def 0)만 바꿨다. 그 −1줄 때문에 이 card의 sizing_recipe 줄 인용(6513행 이후)은 B34 병합본에서 전부 −1이다('작성 전 실측' 착수 재측정 문단). b26pre가 B34 뒤라 이 card도 전이로 B34 뒤다.
  * b26pre와 대상 문장이 겹치지 않는다(b26pre는 11799·11878를 test로 고정하지 않는다).
  * B26-1은 이 def의 수리 호출(11797·11876, 지울 backfill 줄 바로 앞)에 `rails=rails`를 붙이므로, 이 card가 먼저 들어가면 B26-1 V3에서 11799·11878 생존 몫이 사라진다(문장이 head에 없다).
* **착수 조건**(확정 순서 P10b → Phase 2 DoD → V3 면제 묶기 → V3 범위 정책 → B34 → b26pre → **이 card** → B26-1 → B33 → Phase 3 M card). 오케스트레이터가 순서 0 커밋 전에 gate `master`에서 확인한다.
  명령은 `H=$(git -C "$R" rev-parse gate/master)`로 커밋 id를 먼저 얻고 `"$H:<경로>"`로 쓴다(MSYS2 bash가 `gate/master:.ai/…` 인자를 경로 목록으로 바꿔 깨뜨린다 -- `phase2_dod_brief.md` 실측). 하나라도 아니면 착수하지 않는다.
  1. V3 면제 묶기 card `20260930-v3-exempt-binding` 병합: `git -C "$R" cat-file -e "$H:.ai/verification/20260930-v3-exempt-binding.json"`.
  2. V3 범위 정책 card `20260930-v3-changed-stmt-scope` 병합: `git -C "$R" cat-file -e "$H:.ai/verification/20260930-v3-changed-stmt-scope.json"`(범위 card 전이면 현행 도구로 V3 FAIL -- 생존 19, 'V3' 항목).
     병합된 `tools/gates/mutate_changed.py`(`git -C "$R" archive "$H" tools/gates`로 푼 사본)로 이 def의 V3 대상 수를 다시 잰다(`_drafts/b26_backfill_briefs.md` 0.3 방법). **4가 아니면 멈춘다**(사전 수치 4는 시제품 `scope_proto.py` N2w 기준이다. 실제 도구 a17b8bd로 대상 4·not_targeted 93 재확인 -- 모래상자, b26pre 시제품 test가 base에 있으면 V3 PASS 4/4 killed (card 35 병합본 a17b8bd 사전 실행 2026-10-02 — 공식 병합 뒤 재확인)).
  3. Phase 2 DoD PASS: `docs/03-analysis/gain-budget-gmid-sizing-20-dead-code-dup/phase2-dod.md`가 `$H`에 있고 **판정 줄이 PASS다**(`phase2_dod_brief.md` 마지막 단계의 커밋). 파일 존재만으로는 충족이 아니다(브리핑은 FAIL도 결과 파일에 적게 한다 -- review_b26_1_two_attempt m4).
     판정 줄 형식(결과 파일 규약): `## 판정` 제목 바로 다음의 단독 한 줄 `판정: PASS` 또는 `판정: FAIL`(앞뒤 공백·다른 글자 없음, 파일 전체에 정확히 1줄). PASS는 E0~E5 행과 N6.3 1~5가 모두 PASS일 때만이고 auditor가 결과 파일에 쓴다(오케스트레이터는 옮기기만 한다).
     `D2=docs/03-analysis/gain-budget-gmid-sizing-20-dead-code-dup/phase2-dod.md; test "$(git -C "$R" show "$H:$D2" | tr -d '\r' | grep -cx '판정: \(PASS\|FAIL\)')" = 1 && git -C "$R" show "$H:$D2" | tr -d '\r' | grep -qx '판정: PASS'` → exit 0이어야 한다(파일 없음·판정 줄 없음·둘 이상·FAIL이면 1).
  4. decision 기록 두 건이 gate `master`에 커밋되어 있다: `git -C "$R" cat-file -e "$H:.ai/approvals/20261001-b26-phase3-cards.md"`, `git -C "$R" cat-file -e "$H:.ai/approvals/20261001-b26-backfill-interdig-fix.md"`(머리 `approval:` 두 줄의 전제, 계약 1 oracle (d)).
  5. 순서상 앞 card 병합: B34 `git -C "$R" cat-file -e "$H:.ai/verification/20260930-b34-grammar-explicit.json"`, 바로 앞 b26pre `git -C "$R" cat-file -e "$H:.ai/verification/20260930-b26-pre-test-strengthen.json"`.
* **B26-1 card에 넣을 인계(오케스트레이터)**: 이 card 병합 뒤 B26-1의 모의 head·V3 대상 수('V3 대상 301')·Q1 문안을 **그 병합본에서 다시 잰다**.
  * E6 finger growth 행 6 → 4(11809 `_backfill_interdig_ok(result)` 행 삭제, 루프 뒤 11888 행도 사라짐 -- 모의 v4 head 줄. 실제 B34 병합본 위 같은 head(`p35_heads` H4, 2026-10-06)에서는 11808·11887).
  * 한 문장이 빠지면 같은 블록 뒤 문장의 AST 경로 순번이 당겨진다(예 `body[10].body[2]` → `body[10].body[1]`). 모의 head의 경로·줄은 새로 찾는다.

## 작성 전 실측

**measured at `dd60db6`**(착수 0단계 재확인 2026-10-02, 아래 0 -- `_drafts/backfill_launch.sh`가 읽는 measured rev 단일 출처): `a796468..dd60db6`에서 sizing_recipe.py(blob `97a6c7bb`)·`A/tests/unit/test_selftest_sizing_recipe.py` 같음 -- 이 card의 줄 인용은 그대로다.

**measured at `2183f2e`**(착수 재측정 2026-10-06, gate master `2183f2e` = B34 병합 `c851e54` + B34 판정 기록, 저장소 읽기 전용 `git -C … show 2183f2e:<경로>`, scratch `C:/g314` -- 이 문단이 measured rev 단일 출처의 마지막 출현이다):
* `dd60db6..2183f2e`에서 sizing_recipe.py는 blob `97a6c7bb` → `2a7a1a04`. 바꾼 커밋은 B34 code `2eb7e55`(Change-Id `20260930-b34-grammar-explicit`) 하나이고 차이는 `resolve_stack_layout` docstring 한 덩어리(6510~6512 3줄 → 6510~6511 2줄, 순 −1줄)뿐이다. docstring을 뺀 AST로 바뀐 def 0(동작 무관).
  6509행까지는 같고 6513행 이후는 옛 n행 글 = 새 n−1행 글(전수 대조 불일치 0). `A/tests/unit/test_selftest_sizing_recipe.py`는 같다(1480·1481 그대로).
* 그래서 이 card의 sizing_recipe 줄 인용(6513행 이후 -- 11xxx·9368·9397)을 이 판 기준으로 전부 −1 고쳤다(글은 같다): 수정 후보 **11799·11878**(`_backfill_interdig_ok(result)`), `_finalize` 앞 주석 11783~11785·정의 11786~11793, backfill 주석 11768~11769·건너뜀 11771~11772, 반환 docstring 11757~11758, 루프 안 수리 11797·성공 분기 11800~11804, 반환 자리 11802~11804·11828~11830·11836~11838·11862~11864·11880~11883, 루프 뒤 수리 11876, 엔진 안 호출 9368·결과 9397.
  **계약 안 줄 번호**: '관찰 가능한 계약' 1의 반환 자리 줄((i)~(v))과 근거 주석 줄, 그 절 끝 구현 후보 줄(11799·11878)·주석 줄(11768~11769)은 **숫자만** −1 고쳤다(계약 문장·판정은 그대로).
  아래 0의 줄 번호(11712·11758~…·11800·11879)는 `dd60db6` 시점 기록이라 그대로 둔다. '작성 전 실측' 1의 줄 번호는 이 판 기준으로 고쳤다.
* 승인 기록 `20261001-b26-backfill-interdig-fix`(gate `19eb475`, 초안과 바이트 같음 -- 커밋된 기록이라 고치지 않는다)의 줄 번호(11784~11786·11769~11770)는 **B34 전 판**(`a796468`~`7243f28`, sizing_recipe blob `97a6c7bb`) 기준이다. 이 판에서는 11783~11785·11768~11769(글 같음).
* `interdig_ok` 소비처 같다(`git grep interdig_ok 2183f2e -- '*.py'`: 엔진 + selftest 1480·1481). gate 판 `mutate_changed.py`의 `targets_by_def` 3회.
* '착수 조건' 1~5(card 명령, `2183f2e`): 1·2·3·4 exit 0, 5는 B34 0·b26pre 128(b26pre 판정 기록 없음 -- b26pre 병합 전). 승인 기록 두 건 gate에 있음.

(HEAD = gate `master` `a796468`, 2026-10-01, 저장소 읽기 전용, scratch `C:/g106`. 그 뒤 gate `master`가 `0f23786`으로 움직였으나 `git diff --quiet a796468 0f23786 -- skills`가 같음이라 인용 줄 번호는 그대로다 -- 독립 2차 검토가 `0f23786` 사본에서 인용 줄을 다시 읽어 확인했다. 착수 키트(`_drafts/b26_backfill_briefs.md` 0.1, gate `master` `0f23786` archive 사본 `C:/g128`)가 인용 줄·소비처·이름 충돌·계획서 소비자를 한 번 더 재서 같았다.)
0. **착수 0단계 재확인**(2026-10-02, gate `master` `dd60db6`, 저장소 읽기 전용, 모래상자 `C:/g170` -- 측정 뒤 삭제. 스크립트 `_drafts/backfill_launch.sh`):
   * `a796468..dd60db6`에서 sizing_recipe.py(blob `97a6c7bb`)·stick_diagram.py·`A/tests/unit/test_selftest_sizing_recipe.py`·`tools/` 같음 -- 인용 줄(11712·11758~11759·11768~11773·11784~11794·11798~11802·11877~11884, selftest 1480)과 수정 후보 줄(11800·11879)을 다시 읽어 같다.
     `interdig_ok` 소비처도 같다(엔진 + selftest 1480·1481). 승인 기록 `20261001-b26-backfill-interdig-fix`는 gate `19eb475`에 커밋됐고 blob이 초안과 바이트 같다.
   * '착수 조건' 1~5(card 본문 명령 그대로, `backfill_launch.sh conds` -- 조건 4·5는 명령 두 개, 둘 다 0이어야 충족): `dd60db6`에서 exit 128·128·0·128·128. 조건 4는 U-BF 기록만 있고 `20261001-b26-phase3-cards`가 없어 128이다(B34 0단계가 올린다).
   * 조건 2의 'V3 대상 다시 재기'는 `backfill_launch.sh v3count`가 한다: gate 캐시 `mutate_changed.py`(범위 card 병합 판)를 scratch 복제본에서 base = gate `master`, head = base + 수정 후보로 돌려 `targets_by_def`의 대상 수를 읽고, 4가 아니거나 출력에 `targets_by_def`가 없으면(범위 card 미병합) 멈춘다.
   * 모래상자(`dd60db6` + 판정 기록 자리표시 4개(V3 묶기·범위·B34·b26pre) + b26pre 시제품 test(`test_b26pre_existing_paths.py`) + `20261001-b26-phase3-cards` 기록, 범위 card 흉내 = `mutate_changed.py` main을 시제품 `scope_proto` N2w 대상 수만 내는 shim으로, 가짜 gate = 실제 `pre-receive`·`gate-runner.py`(EL4), 복제본 EL3):
     조건 exit 0·0·0·0·0 → `local`(v3count 대상 **4**·not_targeted 93(= 97 − 4, briefs 0.3과 같음) → parse_spec_card `('3', 'red-green', 'no', ['20261001-b26-backfill-interdig-fix', '20261001-b26-phase3-cards'], [], 11)`, interface card 기존 함수 **4행**·신규 시그니처 0행, EL3 통과) → push EL4 통과 → `after-push` OK.
     대조: `--scratch` 없이 `local` → exit 2, 범위 card 전 도구 출력(`targets_by_def` 없음) → 멈춤, 트레일러 없는 표 경로 커밋 → EL3 차단.
1. 사실 문장 재측정: 인용 줄은 HEAD 사본 `sed -n 11754,11799p`·`11876,11884p`로 다시 읽었다(11757~11758 docstring, 11768~11769·11771~11772 backfill, 11783~11785 주석, 11786~11793 `_finalize`, 11799·11878 호출). 소비처는 HEAD 사본 `grep -rn interdig_ok`(엔진 밖은 selftest 1480행뿐, `.ai/context.md` 기록 제외).
2. 이름 충돌: `test_b26_backfill_interdig.py`·`b26bf`는 `A/tests/`에 0건이다. `glob(` 패턴(`*.topology.json`·`*.py` 전수 스캔)과 겹치지 않는다(사전 측정 전체 실행에 같은 접두 파일을 넣고 충돌 없음).
3. 원칙의 계약화: '거짓 기준값 금지'(기존 불일치를 정답으로 고정하지 않음)는 계약 1이 관계로 적는다. '정본은 topology 무관'은 합성 입력·선언 레일로 적었다.
4. 쓰기 경로: test = gmid-test-author, 엔진 수정 = gmid-code-author(A/sizing_recipe.py), 판정 = auditor. 승인 기록 = 오케스트레이터.
5. 계획서 소비자: 지우거나 옮기는 이름이 없다(`_backfill_interdig_ok`는 중첩 def로 남는다).
6. 미배선: 새 def 없음.
7. 기존 계약 test: `A/tests/contracts`에 `interdig_ok`·`relaxed_pairs` 참조 0건(selftest만). V5 없음.
8. interface card 추출(gate 캐시 `interface_card.py`, `0f23786`): 이 card 사본으로 다시 돌려 추출 심볼을 확인했다(`_drafts/b26pre_revision_log.md` v2 → v3). 착수 키트 모의(승인 기록 커밋 뒤 이 card + `approval:` 줄)에서도 관찰 가능한 계약 4행(`run_matching_safety_with_finger_growth`·`size_transistor`·`GmIdLUT.gm_gds_ratio`·`SemiEmpiricalGmIdLUT.gm_gds_ratio`), 신규 시그니처 0행.
