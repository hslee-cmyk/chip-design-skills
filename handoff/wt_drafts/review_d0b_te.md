# 독립 검토 -- D0b T-E 표본 수명·`search_shared_finger_w` 보강(te 편집, `d0b_te_vs_p4.md` 처리안 (c))

검토자: 독립 verifier(작성자 아님). 대상: `draft_p3_d0b.spec.md`·`d0b_briefs.md`·`draft_p4_first.spec.md`·`p4_first_briefs.md` 대 각 `*.pre-te.bak`(diff 전수).
저장소 `chip-design-skills`는 `git -C` 읽기 전용, gate `master` = `863a037cc0d774bb984006ea39966c5e4dd741ab`(rev-parse 확인).
(검토 중 gate가 `22fd126`(b26bf 병합)으로 fast-forward됨 -- `863a037..22fd126` diff에 `search_shared_finger_w`·`SharedFingerWCandidate`·`_quantize_to_grid` 등장 0, 엔진 변경은 `sizing_recipe.py` 9줄뿐이라 ② 결론 불변.)
게이트 도구는 `git archive 863a037 tools/gates`를 `/c/g408`에, 엔진은 같은 커밋 `assets`·`run_harness.py`를 `/c/g408/arc`·`/c/g408/eng`에 꺼냈다(TMP·TEMP = `C:/g408/tmp`, cd 없음, 끝나고 삭제).

## 판정

**B 0 · S 1 · minor 6.** 처리안 (c)의 수명 규칙 자체는 건전하고 기계로 강제된다(①). 새 표본 `search_shared_finger_w`는 gate에서 A-6 근거가 모두 재현되고 Phase 3·4 초안 어디에도 삭제·이관 대상이 아니다(②).
S 1건은 te 편집이 test-author 브리프에 **표본 27**을 지시문으로 넣은 것이다. D0b base는 B26-1 병합 뒤라 상수가 29여야 한다(③).

---

## ① 수명 규칙의 건전성·강제 가능성 -- PASS(minor 2)

* **누락 = FAIL, skip 아님**: spec oracle (d)-1 133행, brief 6 '표본 수명'이 skip·`pytest.skip`·조건부 `continue`를 금하고, 어긋난 표본을 모아 test 본문 하나의 빈 목록 `assert`로 판정한다.
  반례 R-E2(정의와 레지스트리 행을 함께 삭제)를 거부 표에 넣었고 V10 ⑥에 R-E2를 더했다. '게이트는 실제로 거부한다'를 보이는 경로가 있다.
  R-E2 측정 열은 '미측정'이지만 S-7이 test-author 착수 전에 재고 멈춤 조건을 둔다(T-E가 FAIL하지 않으면 멈춤). 허용할 수 있는 순서다.
  gate 레지스트리에서 세 표본의 함수 행은 각각 하나뿐이다(§7 491·507·508행). R-E2 '그 행'은 모호하지 않다.
* **삭제 card가 자기 test 커밋에서 표를 고치고 V5에 올림**: gate `weakening_diff.py`로 확인했다. 단위 이름은 `_units`(58~82행)가 정하는데, 최상위 비-def 문장은 모두 `<module>`이다.
  상수 원소를 지우면 `consts` SequenceMatcher `delete` 때문에 `<module>` '리터럴 변경' 발견이 1건 나온다. 승인 기록이 없으면 FAIL이다(design 05 V5 판정식 535행 '판정식 한 줄 이상 ∧ 승인 기록 없음').
  그래서 삭제 card가 표본을 몰래 줄이면 V5가 막는다. 결과적으로 기준 약화에는 사용자 승인이 필요하다. test-author(삭제 card)가 고치고 auditor가 V5로 재므로 작성자≠검증자와도 맞는다.
* **대체 표본 금지**: 문언은 일관된다(spec 135행, p4 7a, p4 brief 1.1 7a 행, 3.1 diff 점검). 다만 아래 m-2를 보라.
* **m-1(책임 공백)**: 133행은 '배정이 바뀌어도 FAIL'이라 한다. 그런데 134행의 고칠 주체는 '지우거나 옮기는 card'뿐이다.
  배정을 바꾸는 card(배선으로 참조자가 생김, 레지스트리 칸 변경, N3.10 개정)가 고칠 수 있는지, 새 기대값을 어디서 가져오는지(손적용인지 도구 출력 복사인지)는 정해져 있지 않다.
  예를 들어 Phase 4가 '만들면 배선'으로 `search_shared_finger_w`를 MOD8 단위에서 부르면 A-5가 되어 줄기가 바뀔 수 있다. 그 경우는 FAIL로 드러나고 V5도 걸리므로 안전은 유지된다. 절차만 비어 있다.
  권고: '지우거나 옮기거나 **배정을 바꾸는** card가 … 새 기대값은 그 card spec의 손적용 근거로(도구 출력 복사 금지)'.
* **m-2(대체 금지의 기계 강제 범위)**: V5는 삽입(`insert` opcode)을 발견으로 내지 않는다. 그래서 '대체 표본을 더하지 않는다'는 #2에서는 p4 brief 3.1 auditor 점검으로만 지켜진다.
  그 뒤의 일반 card에는 같은 점검 문장이 없다. 표본을 더하는 것은 강화 쪽이라 위험은 낮다. 규칙 문장에 'auditor가 T diff에서 원소 추가 0을 본다'를 붙이면 닫힌다.

## ② `search_shared_finger_w` = A-6(D0a det5 규칙) 재측정 @ `863a037` -- PASS(minor 1)

* **레지스트리 행 없음**: gate 레지스트리에서 이 이름은 158행에만 있다. 158행 함수 칸의 첫 토큰은 `SharedFingerWCandidate`이고, 이 이름은 그 행 비고 칸에 나온다.
  함수 표 파서(머리에 `함수`·`이관 목적지`, 첫 백틱 토큰)로 뽑은 키 집합에도 없다. A-3·A-4는 해당하지 않는다. 클래스가 아니므로 A-2도 해당하지 않는다.
* **N3.10 토큰 아님**: `git grep 863a037 -- docs/01-plan`이 0이다. A-1이 해당하지 않는다.
* **엔진 안 참조자 0**: `assets/*.py`와 `workspaces/run_harness.py` 전수를 AST로 보았다. `Name`·`Attribute`·`import` 참조가 0이고 SD에 `__main__` 블록이 없다.
  `git grep`으로 본 사용처는 SD 6179 def, `tests/unit/test_selftest_stick_diagram.py:24` import, `workspaces/current-reuse-telescopic-ota-report/stick.py`, 문서뿐이다. A-5가 해당하지 않으므로 A-6이다.
* **R(u)**: def는 6179~6233행이다(card 문장과 같다). 몸체가 참조하는 최상위 이름은 `SharedFingerWCandidate`(ClassDef)와 `_quantize_to_grid`(FunctionDef) 둘뿐이다.
  `_quantize_to_grid`는 레지스트리 475행, 칸 `stick_diagram(공용 유틸로 추출 가능)`이다. 식별자 토큰 중 MOD 줄기는 `stick_diagram` 하나라 A-4 MOD7이다. 최댓값이 MOD7이므로 기대 `stick_diagram`가 맞다.
  UD-6 키트 `plan_names_{base,q,rg}.json` 셋 모두에서 `stick_diagram.py::search_shared_finger_w` = `stick_diagram.py`/`A-6`이다(재생성 뒤에도 A-6). A-7 단위는 base·q 모두 `MultiLeafHubParityVerdict`·`check_multi_leaf_hub_parity` 둘뿐이다.
* **m-3(근거 문장 부정확)**: spec 167행은 `SharedFingerWCandidate`를 '칸 `stick_diagram`, MOD7'로 적는다. 하지만 det5 규칙(A-2가 A-4보다 먼저)과 키트에서 그 단위는 **A-2**이고, 참조자는 이 표본 자신뿐이다.
  단조 고정점에서 `_quantize_to_grid`가 MOD7에 앉고, (e3)에 따라 배정된 MOD만 세므로 결과는 MOD7로 같다. 그래서 기대값은 맞고 근거 서술만 틀리다. 'A-2(참조자 = 이 단위), 고정점에서 `_quantize_to_grid` A-4 MOD7이 정한다'로 고칠 것을 권한다.
* **삭제·이관 예정 없음**: `draft_p*.spec.md` 27개와 `draft_phase4_design.md` 전수를 grep했다. 이름이 나오는 곳은 D0b 표·p4 7a 이유 문장, 그리고 p4 계약 4의 **docstring 언급 수정**(36·212행)뿐이다.
  docstring 수정은 참조를 만들지 않으므로 배정은 그대로다. 부르는 두 단위(`SharedFingerWCandidate`·`_quantize_to_grid`)도 어느 초안의 삭제·이관 목록에 없다(D0a 106행은 A-7 예시 언급일 뿐이다).

## ③ 표본 수 산술 27 / 24 / base red 23 -- 지금 관찰로는 PASS, 지시문으로는 **S-1**

* spec 표는 29행(143~171행)이다. B26-1 뒤 둘(`RailDeclaration`·`rail_declaration`, ×)을 빼면 27이다. ×는 `_topology_ref_relpath`·`check_topology_name_uniqueness`·`search_shared_finger_w` 셋이라 ○는 24다.
* gate 레지스트리로 재측정했다. ○ 24개 모두 행이 있고, 칸이 기대 줄기와 정확히 같은 것은 `run_topology_pipeline_with_finger_fixup` 하나다. 그래서 **base red 23/24**이고, 더한 × 표본은 red 크기를 바꾸지 않는다. 
* **S-1**: te 편집이 `d0b_briefs.md` 1.1-6(117행)에 '표본 **27**(B26-1 뒤 둘 제외 …)'을 **상수 지시문**으로 넣었다. 같은 브리프의 auditor 점검(168행)과 p4 card P3-12·p4 brief P3-12('초안 기대 27')도 27이다.
  그런데 D0b base는 **B26-1 병합 뒤**다(spec 17행, brief S-2). spec 173행도 '그 병합 전에는 대조하지 않는다'고 하므로, D0b base에서 test 상수는 **29**(○ 24·× 5)여야 한다.
  117행은 같은 문장에서 `rail_declaration`의 기대값(`topology_authoring`)까지 주고 있어 자기모순이다. 이대로면 test-author가 B26-1 표본 둘을 빼고, auditor는 '27'과 대조해 그 누락을 통과시킨다. 동어반복 방지 표본(A-2·A-1 B26-1 단위)을 조용히 잃는 경로다.
  pre-te 판 117행에는 개수가 없었으므로 te 편집이 들여온 결함이다. 고칠 곳: brief 117·168행을 '29(D0b base = B26-1 병합 판; 지금 관찰 27은 그 둘을 뺀 수)'로, p4 card·p4 brief P3-12를 '초안 기대 29, #2 7a 뒤 26'으로 바꾼다. S-7에서 B26-1이 레지스트리 행을 더했는지(× → ○ 바뀜, 행 있는 수·red 크기 변화)도 함께 재도록 적는다.

## ④ V4 `test_lint` 규칙 (1)·(4) 위반 강제 여부 -- PASS(minor 1)

* gate `test_lint.py`를 확인했다. (4)는 `_judgements(fn)`으로 **test 함수 본문**의 `Assert`·assert 호출만 센다(중첩 def 제외, 531~543행). (3)은 본문 판정이 모두 `if`·`try` 아래일 때 FAIL이다.
  계약은 '빈 목록 `assert`를 T-E 본문에'라고 요구하므로 (4)·(3)을 만족시키는 쪽이다.
* (1)은 판정 문장 양쪽에 **같은 피검 호출**이 있을 때 FAIL이다(585~597행). 기대값이 모듈 상수 리터럴이고 피검(D0b: `move_plan:main`, #2: interface card 22행)은 하위 프로세스로만 불리므로, 양쪽 어디에도 피검 호출이 없다. 그래서 NO-SUBJECT이고, (1)을 강제로 어기게 만드는 계약 문장은 없다.
  #2 7a는 상수 원소 삭제뿐이고 `assert` 위치를 바꾸지 않는다고 명시한다.
* **m-4**: brief 6 '도우미 안 `assert` 금지'는 문맥상 빈 목록 단언에 한정된다. 그런데 계약 11 (b)의 도구 출력 머리 단언(모듈 범위 캐시 도우미에 두기 쉽다)까지 금하는 것으로 읽힐 수 있다.
  둘 다 규칙 위반을 강제하지는 않는다(본문 assert가 하나라도 있으면 (4) PASS). '(이 빈 목록 단언은)'처럼 범위를 한정하는 말을 넣으면 오독이 없다.
* 계약 11 (f)의 이유 문장은 '여러 상수로 나누지 않는다 -- V5 단위가 `<module>` 하나로 정해진다'이다. 그러나 최상위 상수가 여럿이어도 V5 단위는 `<module>`이다(`_units`). 요구는 무해하지만 근거가 과장되어 있다. 정확한 근거는 'T-E 함수 안에 두지 않는다'뿐이다.

## ⑤ #2 계약 7a·V5 목록 8건의 card·brief 일치 -- PASS(minor 2)

* card 7a(59~64행), 의도 22행, equivalence 128행, (d) 출처 137행, V5 기록 항목 186행·(d) 188~190행, 목록 194~196행 '9 … `<module>`'과 '1~8 중 4 제외 7 + 9 = 8건'이 서로 맞는다.
  brief 쪽도 맞는다: 쓰기 경로 여섯 파일(101~104행), 1.1 7a 행, 1.4·2.3 기대, 3.1 `--name-only` 여섯 파일과 diff 점검, 'V5 사전 측정 기대 8건(3.3 V5 목록)'(목록은 실제로 3.3에 있다, 249행), 3.3 V4·V5 행, 목록 9번, 원문 요구 (d).
  card와 brief 사이에 숫자·파일·단위 불일치는 없다.
* **m-5**: card 196행 '1~8 중 5만 남고(4 제외 7건)'는 '1~8 중 다섯째 하나만 남는다'로 오독된다. '1~8에서 4가 빠져 7건(D1 = (마)로 4·5 중 5)'처럼 고치는 편이 낫다.
  p4 brief 1.1 7a 행의 '이름이 남은 문자열이 그 파일에 없어야 계약 3과도 맞다'는 card 계약 3·7a('GONE은 이 파일의 문자열 상수를 잡지 않는다')와 어긋난다. 계약 3은 AST `Name`·`Attribute`·`import`·def만 센다. 결과(세 원소 삭제)는 같으니 문구만 고칠 것.
* **m-6(사용자 승인 원문에 들어가는 사실)**: p4 V5 (d) 이유(189~190행)와 D0b 132·167행에는 '행 있는 A-6·A-7 단위는 재생성 뒤 자기 칸으로 **A-4**가 된다'는 문장이 있다. 키트 `plan_names_rg.json`에서 `check_multi_leaf_hub_parity`는 A-4지만 `MultiLeafHubParityVerdict`는 **A-2**다.
  D0b 132행의 '재생성 뒤 행 있는 표본의 `rule`은 A-4가 된다'는 일반화도 틀렸다(A-1·A-2·A-K 표본은 그대로다). 결론('잃는 보호 = 없어지는 단위의 칸 drift guard')은 유지된다.
  V5 기록에 원문으로 들어가는 문장이므로 'A-4(레코드 클래스는 A-2)'로 고칠 것.

## ⑥ `parse_spec_card`·interface card 바이트 동일 @ gate -- PASS

`/c/g408/tools/gates`(863a037)로 `role_paths.parse_spec_card`와 `interface_card.py --root C:/g408/arc`를 pre-te 판과 te 판에 각각 돌렸다.

| card | parse_spec_card(pre-te / te) | interface card exit | 생성본 sha256(pre-te = te) |
|---|---|---|---|
| D0b `20260930-p3-registry-dest` | 둘 다 OK -- phase 3·red-green·gate_change no·approval 2개·절 11·activated/noop [] | 0 / 0 | `f2f23e65…44bc75` **바이트 같음**(두 표 빈 표, '기존 함수 0') |
| #2 `20261002-d4-delete-unwired` | 둘 다 OK -- phase 4·equivalence·gate_change no·approval 1개·절 11 | 0 / 0 | `1bdbddbc…7cf52` **바이트 같음**(관찰 가능한 계약 표 22행) |

te 편집이 계약 절에 더한 백틱 토큰(`_P3RD_FACT_SAMPLES`, `<module>`, 이미 22행에 있는 세 이름, test 경로)은 생성본을 바꾸지 않는다.

---

## 고칠 것 요약

| 등급 | 위치 | 내용 |
|---|---|---|
| S-1 | `d0b_briefs.md` 117·168행, `draft_p4_first.spec.md` P3-12, `p4_first_briefs.md` P3-12 | 표본 수 27 → D0b base(B26-1 병합 판) 기준 29(#2 7a 뒤 26). '지금 관찰 27'은 괄호 사실로만 |
| m-1 | spec 133~135행 | 배정을 바꾸는 card도 고칠 주체에 넣고, 새 기대값 출처(손적용, 도구 출력 복사 금지)를 명시 |
| m-2 | spec 135행 | '원소 추가 0'을 auditor 점검으로(V5는 삽입을 잡지 않음) |
| m-3 | spec 167행 | `SharedFingerWCandidate`는 A-2(칸이 아니라 참조자), 결과 MOD7은 `_quantize_to_grid`가 정함 |
| m-4 | brief 6, spec 11 (f) | '도우미 안 assert 금지'의 범위 한정, '여러 상수' 근거 정정 |
| m-5 | card 196행, p4 brief 1.1 7a 행 | '5만 남고' 문구, '계약 3과도 맞다' 문구 |
| m-6 | p4 V5 (d), spec 132·167행 | 재생성 뒤 `MultiLeafHubParityVerdict`는 A-2 -- 'A-4가 된다' 일반화 정정 |
