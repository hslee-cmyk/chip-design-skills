---
id: 20261001-b26-backfill-interdig-final-audit
phase: 2
evidence_type: red-green
gate_change: no
---
## 의도

`run_matching_safety_with_finger_growth`(A/sizing_recipe.py, A = `skills/analog-gmid-design/assets`)가 돌려주는 `relaxed_pairs[i]["interdig_ok"]`가 **같은 반환의 `audit`과 어긋나는** 입력이 있다.
이 card는 그 불일치를 red test로 고정하고, `interdig_ok`를 반환 `audit`(최종 물리 구조)으로 채우게 고친다.

**결함으로 보는 근거 -- 코드 자신이 적은 의도(a796468, 원문 그대로)**:
* `_finalize` 앞 주석, A/sizing_recipe.py:11784~11786:
  > `# 이 함수의 **모든** 반환 지점에서 최종 rows/ctx를 내보내기 전에 반드시 이 euler`
  > `# 정리를 거치고 그 결과로 audit을 다시 계산한다 -- 그래야 반환되는 audit이 실제로`
  > `# 저장/보고될 최종 물리 구조와 항상 일치한다(저장 버그와 같은 종류의 불일치 재발 방지).`
* `_backfill_interdig_ok` 안 주석, A/sizing_recipe.py:11769~11770:
  > `# 완화를 적용한 라운드에는 아직 그 결과가 반영된 audit이 없어 interdig_ok=None으로`
  > `# 남겨뒀다 -- 다음 라운드에 새로 계산된 audit_result가 나오면 그 3b 체크로 채운다.`
* 반환 docstring(같은 파일 11758~11759): `"relaxed_pairs": [{"pair":(a,b), "reason":"gm_id_budget_exceeded", "trim_recommended":True, "interdig_ok":bool|None}, ...]`.

**어떻게 어긋나는가(base 동작)**:
* `_backfill_interdig_ok`는 `interdig_ok`가 `None`인 항목만 채운다(11772~11773 `if entry["interdig_ok"] is not None: continue`).
* 루프 안(11800)과 루프 뒤(11879)에서 **euler 정리 전** audit으로 먼저 부른다. 그 뒤 `_finalize`(11787~11794)가 정리한 행으로 audit을 다시 계산하고 같은 backfill을 부르지만, 이미 채워진 항목은 건너뛴다.
* 그래서 정리가 완화 쌍이 든 행을 바꾸면(아래 재현), `interdig_ok`는 **정리 전 행**의 3b이고 반환 `audit`·`rows`는 **정리 후 행**이다.
* 경위: backfill은 세션17(완화 도입), `_finalize`는 세션31(2026-08-13)에 들어왔다. `.ai/context.md` 1558~1561(세션17 '알려진 한계')은 "`interdig_ok`가 `False`로 나오는 실제 사례 … 는 아직 self-test로 직접 확인 안 함"이라고 적었다.

**재현(합성, a796468·a796468+B34 둘 다 같음 -- `_drafts/b26pre_v2_scripts/bf_repro.py`)**:
* 행 `{"seg1": [Ma, Mb, Mp]}`: `Ma(nmos, source="n2", drain="n1", gate="ga")`, `Mb(nmos, source="n4", drain="n2", gate="gb")`, `Mp(nmos, source="n2", drain="n5", gate="gp")`, 모두 `n_fingers=1`, `finger_w=W0`, `stack_id="seg1"`.
  넷 `n2`가 차수 3, `n1`·`n4`·`n5`가 차수 1이라 이 행은 euler-blocked다(`build_stick_diagram(행)["seg1"].status == "blocked"` 실측).
* 매칭 `[("Ma","Mb")]`, `{("Ma","Mb"): "offset"}`, `lut_by_kind={"nmos": toy_lut}`, metrics `{}`, constraints `[]`, `gm_id_bounds=(11.9, 12.1)`(핑거증가가 gm/ID 위반 → 완화).
* 결과(max_rounds 1·2·3·5, metrics 있음·없음 모두 같다):
  * `relaxed_pairs == [{"pair": ("Ma","Mb"), …, "interdig_ok": False}]`
  * 반환 `audit`의 `3b. interdigitation[Ma/Mb] [참고용 -- 이 kind는 필수 아님]`은 `ok = True`
  * 반환 `rows == {"seg1_seg0": [Mp], "seg1_seg1": [Mb, Ma]}`(정리가 행을 둘로 나눴다)
  * `unresolved_reason`: max_rounds=1이면 `"max_rounds_exceeded"`(루프 뒤 11879 경로), 2 이상이면 `"relaxed_to_layout"`(루프 안 11800 경로)
* 소비처(HEAD `git grep interdig_ok`): 엔진 자신과 `A/tests/unit/test_selftest_sizing_recipe.py:1480`(`is not None`만 단언)뿐이다. 이 값을 읽어 분기하는 운영 코드는 없다.
  `optimize_full_circuit_budget`은 `relaxed_pairs`를 `pipeline_result`로 넘긴다(보고 경로).

**사용자 결정 필요**(엔진 관찰 가능 동작 변경): `_drafts/b26_backfill_question.md`. 결정 전에는 착수하지 않는다(착수 조건).

## 관찰 가능한 계약

공통 입력: 위 '재현'의 행·매칭·인자. `W0`·사이징 항목 `S`·`ctx`는 `_drafts/draft_b26pre.spec.md` '공통 입력(계약 1~3)'과 같은 정의다(`size_transistor(gm=200e-6, gm_id=12.0, L=0.5e-6, lut=toy_lut, vds=0.6)`, `SizingContext(sized={…: dict(S)}, topology_path=<합성 topology>)`).
합성 topology는 `tmp_path`에 쓰고 `supply_nets: ["vdd", "gnd"]`를 선언한다(B26-1 뒤에도 같은 판정). 새 test 파일 하나: `A/tests/contracts/test_b26_backfill_interdig.py`, 함수 이름 `test_b26bf_`·도우미 `_b26bf_`로 시작.

1. **반환 `interdig_ok` = 반환 audit의 3b**(모든 반환 경로)
   * `res = run_matching_safety_with_finger_growth({"seg1": 행}, [("Ma","Mb")], {("Ma","Mb"): "offset"}, ctx, {"nmos": toy_lut}, {}, [], gm_id_bounds=(11.9, 12.1), max_rounds=m)`.
   * 판정 `CONSISTENT(res)`: `[e["pair"] for e in res["relaxed_pairs"]] == [("Ma","Mb")]`이고, 각 항목 `e`(쌍 `(a, b)`)에 대해 `res["audit"].checks` 중 이름이 `"3b."`로 시작하고 `f"[{a}/{b}]"`를 담은 체크가 정확히 1개이며 `e["interdig_ok"] is <그 체크>.ok`다.
   * (a) 루프 안 경로: `m = 2` → `res["unresolved_reason"] == "relaxed_to_layout"`이고 `CONSISTENT(res)`.
   * (b) 루프 뒤 경로: `m = 1` → `res["unresolved_reason"] == "max_rounds_exceeded"`이고 `CONSISTENT(res)`.
   * 두 경우를 별개 test 함수로 둔다.
   * 기대값의 근거는 위 11784~11786 주석(반환 audit = 최종 물리 구조)과 11769~11770 주석(interdig_ok는 audit의 3b 체크로 채운다)의 결합이다. 기대 `True`를 숫자로 박지 않고 반환 audit과의 일치로 적는다.
2. **바뀌지 않는 것**: 같은 입력에서 `rows`(행 키와 소자 이름·`n_fingers`·`stack_id`), `audit`의 체크 이름·`ok` 목록, `unresolved_pair`·`unresolved_reason`·`growth_rounds` 길이는 base와 같다.
   (backfill은 `relaxed_pairs` 항목만 쓴다.) 이 계약은 auditor가 base·병합본에서 같은 호출로 대조한다(영구 test로 base 값을 박지 않는다).
3. **기존 test 불변**: 기존 test 전부가 병합본에서 PASS한다. 특히 `test_selftest_sizing_recipe.py`의 L4e(`interdig_ok is not None`, `unresolved_reason == "relaxed_to_layout"`, `audit.ok` False)는 그대로다.

구현 방식은 code-author 몫이다. 사전 측정한 후보 하나: 루프 안·루프 뒤의 사전 backfill 호출(11800·11879) 두 줄을 지우고 `_finalize` 안의 호출만 남긴다(모든 반환이 `_finalize`를 거치므로 항목은 반드시 채워진다).
그때 11769~11770 주석과 반환 docstring의 `interdig_ok` 설명을 '최종 audit(정리 뒤)으로 채운다'로 고친다(코드 주석·docstring은 V 판정 밖이지만 거짓 서술로 남기지 않는다).

## 신규 시그니처

| 모듈 | 심볼 | 시그니처 |
|---|---|---|

## 판정 유형 근거

red-green이다. 관찰 가능한 반환값(`relaxed_pairs[i]["interdig_ok"]`)이 바뀐다.
* red: test 커밋만 있는 상태(base 엔진)에서 계약 1의 두 test가 `AssertionError`로 실패한다(`e["interdig_ok"] is c.ok` -- False 대 True). 새 심볼이 없어 '단언 red'다.
  사전 측정(`bf_redgreen.py`): base 사본 seed 0·1에서 2 failed.
* green: 수정 후보 사본에서 seed 0·1·7 모두 2 passed.
* V2 회귀(사전 측정, `bf_fullsuite.py`, `A/tests` 전체, seed 1): 수정 후보 사본 888 passed·15 xfailed·2 failed, base 사본 886 passed·15 xfailed·4 failed.
  두 사본의 2 failed는 같은 test(`test_ts6_probe_relocate`의 `.git` 필요 2개 -- archive 사본 한계)이고, base의 나머지 2 failed는 이 card의 red 시제품 2개다. 두 사본 모두 contracts에 시제품 두 파일(b26pre 17, b26bf 2)을 넣고 쟀다.
* V3: 바뀌는 def는 `run_matching_safety_with_finger_growth` 하나다(중첩 `_backfill_interdig_ok`·`_finalize` 포함). 대상 변이 수는 auditor가 착수 시 그 시점 V3 범위 규칙(V3 scope card 병합 여부)으로 잰다.
  이 card를 `20260930-b26-pre-test-strengthen`(b26pre) **뒤**에 두면 그 card의 계약 2·3 test가 이 def 인벤토리에 들어 대부분의 반환 경로 변이를 죽인다(b26pre 사전 측정: 이 def의 표 1 문장 12개 중 9개 죽음, 남는 3개가 11800·11879와 등가 후보 11802).
* V7: 새 def 없음.

## oracle 종류와 출처

* 계약 1 -- (b) 문서화된 의도: 위 두 코드 주석(파일:줄 원문 인용). 기대값은 '반환 audit의 3b와 같다'는 관계이고, 피검 호출로 숫자를 만들지 않는다. 입력은 (a) 구성(넷 차수로 euler-blocked, 좁은 gm/ID 범위로 완화).
* 계약 2 -- (c) 기존 동작 기준선(a796468), auditor 대조.
* 작성자≠검증자: 시제품(`_drafts/b26pre_v2_scripts/proto_bf_test.py`)과 수정 후보 측정은 오케스트레이터 사전 측정 전용이다. test-author·code-author·auditor에게 건네지 않는다.

## 거부해야 할 입력

* base 엔진(사전 backfill이 정리 전 audit으로 먼저 채움) -- 계약 1 두 test 실패.
* 루프 안 또는 루프 뒤 경로 한쪽만 고친 엔진 -- 해당 경로 test 실패(그래서 두 경로를 별개 test로 둔다).
* `_finalize`의 backfill까지 지운 엔진 -- `interdig_ok`가 `None`으로 남아 계약 1(`is c.ok`)과 기존 L4e(`is not None`) 실패.

통과해야 하는 것: 반환 `interdig_ok`를 최종 audit으로 채우는 엔진.

## library 회로 적용 여부

사전 측정하지 않았다. `relaxed_pairs`가 비어 있지 않고 완화 쌍의 행이 정리로 바뀌는 회로에서만 값이 달라진다(그 외는 무동작).
auditor가 E-LIB(9회로 `optimize_full_circuit_budget` 결과의 `pipeline_result["relaxed_pairs"]` base 대 병합본)를 잰다. 달라지는 회로가 있으면 회로·쌍·전후 값을 판정 기록에 적는다.

## 무동작 판정 입력(무발동 값)

`relaxed_pairs == []`인 모든 호출(완화가 없으면 backfill이 할 일이 없다), 그리고 완화 쌍의 행이 정리 전후로 같은 호출(사전 audit과 최종 audit의 3b가 같다 -- 기존 L4e가 그 예).

## 재현할 수치

사전 측정(판정 수치 아님, scratch `C:/g106`, 스크립트 `_drafts/b26pre_v2_scripts/`):
* `bf_repro.py base|b34`: 위 '재현' 결과, 두 사본 같음.
* `bf_redgreen.py`: base red 2 failed(seed 0·1), 수정 후보 green 2 passed(seed 0·1·7), 수정 후보에서 b26pre 시제품 17 passed, `test_selftest_sizing_recipe.py` 66 passed·2 xfailed, `test_selftest_stick_diagram.py` 130 passed·1 xfailed.
* `bf_fullsuite.py`: 위 V2 회귀 수치.
* 독립 검토(`_drafts/review_b26pre.md` §1 B1): 무작위 퍼즈 400건 중 1건에서도 11800 삭제가 결과를 바꿨다(같은 종류의 불일치).

## 결정 필요 항목

* **U-BF(사용자 결정 -- 착수 조건)**: 이 불일치를 결함으로 고칠지. 질문 문안 `_drafts/b26_backfill_question.md`(권고 = 고친다, 이 card를 b26pre 뒤·B26-1 앞에).
  고치기로 하면 승인 기록(`target_kind: decision`, id 후보 `20261001-b26-backfill-interdig-fix`)을 커밋한 뒤 머리 블록에 `approval: <그 id>`를 더한다. 기록이 없는 동안은 줄을 두지 않는다.
* 순서(원칙 기본안): b26pre(`20260930-b26-pre-test-strengthen`) → **이 card** → B26-1. b26pre와 대상 문장이 겹치지 않는다(b26pre는 11800·11879를 test로 고정하지 않는다).
  B26-1은 이 def에 `rails=rails`를 붙이므로, 이 card가 먼저 들어가면 B26-1 V3에서 11800·11879 생존 몫이 사라진다(문장이 head에 없다).

## 작성 전 실측

(HEAD = gate `master` `a796468`, 2026-10-01, 저장소 읽기 전용, scratch `C:/g106`.)
1. 사실 문장 재측정: 인용 줄은 HEAD 사본 `sed -n 11755,11800p`·`11877,11885p`로 다시 읽었다(11758~11759 docstring, 11769~11770·11772~11773 backfill, 11784~11786 주석, 11787~11794 `_finalize`, 11800·11879 호출). 소비처는 HEAD 사본 `grep -rn interdig_ok`(엔진 밖은 selftest 1480행뿐, `.ai/context.md` 기록 제외).
2. 이름 충돌: `test_b26_backfill_interdig.py`·`b26bf`는 `A/tests/`에 0건이다. `glob(` 패턴(`*.topology.json`·`*.py` 전수 스캔)과 겹치지 않는다(사전 측정 전체 실행에 같은 접두 파일을 넣고 충돌 없음).
3. 원칙의 계약화: '거짓 기준값 금지'(기존 불일치를 정답으로 고정하지 않음)는 계약 1이 관계로 적는다. '정본은 topology 무관'은 합성 입력·선언 레일로 적었다.
4. 쓰기 경로: test = gmid-test-author, 엔진 수정 = gmid-code-author(A/sizing_recipe.py), 판정 = auditor. 승인 기록 = 오케스트레이터.
5. 계획서 소비자: 지우거나 옮기는 이름이 없다(`_backfill_interdig_ok`는 중첩 def로 남는다).
6. 미배선: 새 def 없음.
7. 기존 계약 test: `A/tests/contracts`에 `interdig_ok`·`relaxed_pairs` 참조 0건(selftest만). V5 없음.

test-author가 쓰는 이름: `sizing_recipe.run_matching_safety_with_finger_growth`(위치 인자 7개 + `gm_id_bounds=`·`max_rounds=`), `sizing_recipe.size_transistor`, `sizing_recipe.SizingContext`(`sized`·`topology_path`), `sizing_recipe.Transistor`(이름·kind 위치, 나머지 키워드),
반환 키 `relaxed_pairs`(원소 키 `pair`·`interdig_ok`)·`audit`·`unresolved_reason`, `AuditResult.checks`, `AuditCheck.name`·`.ok`, 픽스처 `toy_lut`(LUT 메서드 `gm_gds_ratio`).
