# T0·FU 착수 준비 독립 검토 -- 2026-10-02

검토자 = 작성자 아님. 기준 gate `master` `4a286f0`(시작·끝 같음). 실제 저장소는 `git -C` 읽기만 했다(HEAD·reflog 첫 줄 `4a286f0`, `status --porcelain` 37줄 -- 시작과 같음. `role/audit/20260930-v3-changed-stmt-scope`는 검토 중 다른 주체가 만들었고 내가 만든 것이 아니다).
스크래치는 `C:/g242`만 썼다. 작업 트리에서 `-c core.autocrlf=false --no-local`로 복제하고 origin을 지운 뒤 모래상자 gate(bare)를 붙였으며, 빈 hooksPath와 TMP/TEMP `C:/g242/tmp`를 썼다. 끝에 지웠다.
예외: redteam `run_all.py`가 TMP를 무시하고 `C:\Windows\Temp\gmid-redteam\20261002-171457-direct`에 썼다. 그 디렉터리만 지웠고 부모 디렉터리는 그대로 두었다.
작성자 키트(`p3kit_t0`·`p3kit_fu`)는 사전 측정 대조용으로만 돌렸다. 판정 근거는 내 스크립트로 냈다.

## 판정 요약

| card | 판정 | B | S | minor |
|---|---|---|---|---|
| T0 `20260930-p3-tests-location-free` | **착수 불가(B 1 해소 전)** | 1 | 4 | 5 |
| FU `20261002-p3-future-annotations` | **조건부 착수 가능(B 1은 0단계 절차 보강으로 해소)** | 1 | 0 | 4 |

---

## T0

### B (막는 결함)

**T0-B1. V4가 `--interface-card` 단독으로 FAIL한다.** 계약 11(UD-6 W-1)이 unit selftest 3파일을 diff에 넣으면서 생긴 문제로, 사전 측정에 없던 결과다.
- 측정 조건: 모래상자 T = 계약 1~4 키트 시제품 + 계약 11 import 3줄, base `4a286f0`. 도구는 gate 판 `test_lint.py --root <T 트리> --base 4a286f0 --head T --interface-card <생성본(기존 함수 6)> --module-dir A`.
- 결과: **verdict FAIL, exit 1**.
  - `tests/unit/test_selftest_sizing_recipe.py::test_s009_revalidate_finger_override` 719·744행이 규칙 (1) FAIL이다(피검 `size_transistor`가 판정식 양쪽에 들어간다).
  - 같은 파일에 UNJUDGED 78개가 더 나온다.
  - 두 줄은 T0이 고치지 않는 기존 줄이다. base 트리에서 같은 파일만 lint해도 FAIL이다.
- 원인: V4는 `--diff-filter=AM` 파일 전체를 lint한다. 24행 import만 바뀌어도 3천 줄짜리 selftest 전체가 V4 대상이 된다.
- 브리프 3.2 V4 행("`--interface-card` 단독으로 PASS -- findings 76 전부 NO-SUBJECT")은 unit 파일을 건드리기 전인 `19eb475` 시제품 값이라 지금은 틀리다.
- 키트 `v_tools.sh`의 `--subject` 373개 방식은 지금도 'PASS'로 나오지만 **공허하다**.
  - 원인: `v4_subjects.txt`가 CRLF이고 `read -r`가 `\r`을 남긴다. 그래서 subject 373개가 하나도 맞지 않아 findings가 전부 NO-SUBJECT가 된다.
  - `\r`을 떼고 다시 돌리면 FAIL이다. 규칙 (1) FAIL은 SR selftest 4건과 DR selftest 1건, (2) FAIL은 8건이다.
- 고칠 것(사용자 몫이 들어 있다):
  - (가) `20260923-c9-v4-exempt` 선례처럼 decision 승인 기록으로 `…/test_selftest_sizing_recipe.py::test_s009_revalidate_finger_override`의 규칙 (1)을 면제한다. 사용자 승인이 필요하므로 spec card '결정 필요 항목'에 새 항목으로 올린다.
  - (나) 아니면 B26-1이 같은 파일(계약 12, 15곳)을 고치면서 이 면제를 이미 받았는지 착수 0단계에서 확인한다. 받았다면 T0 head에서 `_approved_ids`로 그대로 면제된다.
  - 어느 쪽이든 브리프 V4 행을 고친다. 기대를 'FAIL 2 → 면제 뒤 PASS'로 바꾸고, UNJUDGED 78의 oracle 대조를 basis에 적게 한다(선례 `20260923-d-delete-telescopic` V4 basis 'UNJUDGED 52').
  - `v_tools.sh`의 `while read -r x` 줄에는 `x=${x%$'\r'}`를 넣는다.

### S (보완)

- **T0-S1. 계약 4 사실 문장과 auditor 계약 4 확인이 지금 트리에서 거짓이다.**
  - 계약 4는 "저장소 전체 `git grep -n _SIZING_RECIPE` = 이 파일 다섯 줄뿐, 계획서·design 소비자 0"이라고 적었고, 브리프 '계약 확인'은 "`_SIZING_RECIPE` 저장소 전체 0건"을 요구한다.
  - 그런데 `4a286f0`의 design 30에 577·611·1183행 세 줄이 있다(UD-0 design 커밋 `6c8287f`). 병합본에서 저장소 전체 grep은 0건이 아니라 3건이다.
  - 범위를 '추적 `.py` 0건(design 30 서술 3줄은 소비자 아님)'으로 바꾼다. 그대로 두면 auditor 재시도 원인이 된다.
- **T0-S2. 브리프 1절(test-author)이 계약 11을 빠뜨렸다.**
  - 입력이 "'관찰 가능한 계약' 1~10"으로 적혀 있다(96행).
  - W-1 작성 지시("6. (UD-6 W-1) 계약 11 -- unit selftest 3파일 24행 …", 140~143행)가 **3절 auditor 블록 안**에 잘못 놓였다.
  - 1절 '모양 요구'를 8번으로 옮기고 입력을 1~11로 고친다. 자기 실행 명령에 unit 3파일도 넣는다(지금은 contracts 4파일뿐).
- **T0-S3. 착수 0단계에 계약 11 재측정이 없다.**
  - card는 '작성 전 실측' 첫 문단에서 "착수 때 B26-1 계약 12가 세 파일 24행 이름 목록을 바꾸는지와 위 수치를 다시 잰다"고 적었다.
  - 그러나 브리프 머리 0단계 (가)~(바)와 `t0_launch.sh kit-cmds`는 `t0_facts.py`만 돌린다(`t0_launch.sh`는 12:08 판이라 UD-6 전이다).
  - `p3ud6_kit/w1_lines.py`·`p3fq_kit/shim_import_reads.py` 재실행과 (사) 판단 항목을 더한다.
  - 함께 볼 것: B26-1 계약 12가 SR selftest 24행에 SD 이름(`RailDeclaration` 등)을 `sizing_recipe` 경유로 넣었는지. 넣었다면 계약 11 (c) 잔여가 늘어난다.
- **T0-S4. 계약 10은 지금 모의할 수 없다.**
  - `test_b26_rail_accessor.py`가 B26-1 병합 전이라 없고, 키트 `make_synth.py`에도 계약 10 트리가 없다.
  - 내 확인: B26-1 초안 계약 3(102행)이 "test가 `stick_diagram.rail_declaration`을 바꿔 센다"이다. 그러니 '모듈 속성 교체' 가정은 초안과 맞다.
  - 공식 재시도 전 규칙(test + 옛 코드 변이 dry run)에 따라, B26-1 병합 직후 test-author 착수 **전에** 오케스트레이터가 계약 10 합성 트리를 한 번 돌린다. `load_topology`와 `rail_declaration`을 각각 새 파일로 옮기고 재수출한 뒤 base 옛 계수 test는 FAIL(계수 0), 시제품은 PASS인지 본다.
  - 이 단계를 브리프 4절 순서에 넣는다.

### minor

- m1. V5 실측: import 3줄은 V5 발견을 내지 않는다. 그리고 `diff_paths`가 '발견 있는 경로'뿐이라 **diff_hash 밖**이다. `diff_paths` = contracts 3파일, 발견 4 = 비교 완화 1 + 리터럴 3으로 사전 측정과 같다.
  - card '결정 필요 항목'의 "낸다면 …"을 실측 문장으로 바꾼다.
  - 승인 기록 범위 설명에 'import 3줄은 공개하지만 해시 대상은 아니다'를 적는다. 해시가 그 3줄을 덮는다고 읽히지 않게 하려는 것이다.
- m2. 브리프 V1 행의 "1008 passed 15 xfailed"는 `19eb475` 값이다. `4a286f0`에서는 base·T 모두 **1047 passed 15 xfailed, id 1062**이고 (판정, id) 집합 차이 0이다(내 측정).
- m3. '작성 전 실측' 5의 design 10 §5.6 '파일' 열 개정은 이미 반영됐다(`6c8287f` -- 머리 "파일(설명, Phase 3 전 위치)").
  - 그래서 `t0_facts.py`의 `design10_table.header`가 `[]`로 나온다. 0단계 대조에서 예상된 차이라고 적는다. `_SIZING_RECIPE_all`의 design 3줄도 같다.
- m4. 거부 입력 경계: R-DEF는 '파일 수'로 센다. 그래서 **같은 파일 안 이중 def**(정의 2개, 파일 1개)는 계약 3 test가 통과시킨다.
  - ic5는 함수 수로 세므로 잡는다.
  - base와 같은 한계이고 `rdef_duplicate_names` {}는 실측이다. 다만 '거부해야 할 입력'에 '범위 밖(파일 단위)'으로 한 줄 적는다.
  - 모듈 최상위 `if`/`try` 안 바인딩은 R-DEF가 보지 않는다. 결과가 0개라 FAIL 쪽으로 깨지므로 안전하다.
- m5. 키트 `v_tools.sh` V4 CRLF 결함(B1)은 `md_sync_kit/v4_subjects.py` 출력에도 그대로 있다. md 일치 판정 기록 V4 basis는 '373개 subject PASS'라고 적었다. 그 test는 엔진을 부르지 않아 결론은 같을 가능성이 높다. 그래도 같은 방식이 다른 card 증거에 쓰였는지 백로그로 확인한다.

### 확인된 것(재현)
- `parse_spec_card`(gate 판 `role_paths`): phase 3·test-only·gate no·approval 2(순서 그대로)·절 11·phase_order 안.
- `interface_card.py`: 기존 함수 6개이고 키트 `t0.interface.generated.md`와 바이트가 같다.
  - SD에 `rail_declaration`을 정의한 합성 트리에서는 `stick_diagram.rail_declaration` 행이 더해진다. `IFC_OPT` 분기와 맞는다.
- test-first(T 단독, base 위): PT3 전체가 base와 T 모두 1047 passed 15 xfailed(id 1062)이고 결과 차이 0이다.
- 계약 11:
  - (c) 잔여: base 3파일·7이름 → T 0.
  - (b) T 한 프로세스에서 `test_mod.<이름> is E.<이름>` 7/7 True.
- 계약 6·7·거부 합성 트리(`4a286f0`): 사전 측정과 같다.
  - move: 옛 test 3 FAIL + `_L_ROLE` 공허 PASS, 새 test 4 PASS.
  - copy: 새 test는 `size_transistor`만 FAIL, 옛 test는 4 PASS.
  - rebind: 새 test는 `_L_ROLE`만 FAIL.
- 계약 9 토큰: `+` 102줄에 0.
- V3 PASS `targets []`, V6 PASS `targets []`, V7 PASS `new_defs []`.
- `t0_facts` `4a286f0` 대 `19eb475`: ic5 21개 각 1곳, rdef 중복 {}, SR 4개, `rail_declaration` [](B26-1 전), setattr 0, monkeypatch = df36 chdir 4. 차이는 위 m3와 md 일치 test 추가뿐이다.
- `t0_launch.sh`(모래상자: 선행 5 card 판정 기록·`test_b26_rail_accessor.py` 자리표시자·gate_path를 모래상자로 바꾼 커밋 + measured 줄을 넣은 초안 사본):
  - 옵션을 단계 뒤에 두거나 `--state`가 빠지거나 `--repo`에 실제 저장소 별칭을 주면 exit 2로 거부한다.
  - `kit-cmds`·`conds`(10/10 exit 0)·`local`(pre→card→final, 커밋 `6282628`)·`after-push`가 모두 통과했다.
  - worktree·push 명령은 출력만 한다.

---

## FU

### B (막는 결함)

**FU-B1. '재현할 수치'와 V10이 `dd60db6` 판 절대값인데, 착수 0단계가 그 값을 다시 재지 않는다.**
- 브리프 머리는 "착수 때 FU base에서 다시 잰다(0단계)"라고 적었다. 그러나 0단계 명령과 `fu_launch.sh kit-cmds`는 diff·grep·sed·승인 기록 grep뿐이다.
- `pre`는 measured 뒤 DR·ACF·레지스트리 변경만 본다.
- B34·b26pre·backfill·B26-1이 병합되면 다음이 바뀌는데 `pre`는 통과한다.
  - test 수(1047/1062).
  - E-LIB `hash`: B26-1이 `load_topology` meta에 `rails`를 더한다. design 30 E5가 그래서 `e_lib_p3.py`로 그 키를 뺀다.
  - E-INST `raw_sha256`일 가능성이 크다.
- 그러면 브리프 V10("spec '재현할 수치' 재실행 -- PT3 수, E-LIB hash, E-INST raw_sha256 둘")이 숫자 불일치로 FAIL한다. 대역 head `bc3fd5d`도 스크래치에서 지워져 재현할 수 없다.
- 고칠 것(둘 중 하나):
  - (가) 0단계에 `fu_pt3.sh`·`fu_elib_einst.sh`·`fu_codeobj.py`를 FU base와 두 줄 대역 head에서 다시 돌리는 명령과 판단 항목을 넣는다. 그리고 '재현할 수치'를 그 판 값으로 갈아 쓴다.
  - (나) '재현할 수치'를 '같은 판 base = 병합본' 꼴로 바꾸고 판에 따라 바뀌는 절대값을 뺀다. 코드 객체 수와 `f94f7895…`는 DR·ACF만 보므로 그대로 둘 수 있다.

### minor

- m1. 계약 1 판정기 자기 점검 입력에 **빈 줄 추가**(future 줄 다음 줄에 빈 줄)와 **주석이 붙은 future 줄**이 없다.
  - 이 둘은 AST 부분(`H = B[:1]+[I]+B[1:]`)을 통과하고 diff 부분('지운 줄 0·바뀐 줄 0·파일마다 한 줄')만 잡는다. 내 독립 판정기 실측: ast=True, diff=False.
  - diff 부분이 공허하지 않음을 보이려면 이 둘을 '거부해야 할 입력'에 더한다.
  - 중복 future 두 줄, 기능 둘, 첫 줄, coding 주석 뒤 docstring 앞, 첫 import 뒤는 모두 FAIL로 확인했다.
- m2. 계약 3(b) `e_lib.py` sha256 `045f65c8…`은 **CRLF 작업 트리 사본** 값이다. `git show`(LF) 사본은 `41b72d7d…`(blob `00fbb20f`)다.
  - 브리프대로 `autocrlf=false` 격리 복제본에서 꺼내면 해시가 다르게 나온다. blob id나 두 해시를 함께 적는다.
- m3. spec '결정 필요 항목'·'작성 전 실측' 9와 브리프 S-1의 '기록이 아직 gate에 없다'는 이제 거짓이다.
  - `4a286f0`에 `.ai/approvals/20260930-30-module-split-design.md`가 있고, 108·112행에 FU id와 D-29 원문이 있다. `fu_launch.sh` 조건 1·2도 0이다.
  - 착수 때 문장을 고친다. spec이 인용한 범위 정책 card '244행'은 커밋된 spec에서 **249행**이다.
- m4. redteam 20(e) equivalence·test-only 정상 흐름을 모래상자에서 돌리면 둘 다 EL4 단계에서 `jsonschema import 실패`로 FAIL한다.
  - `sb.clean_env`가 APPDATA를 지워서 생기는 환경 문제이고 card 결함이 아니다. 다만 spec 판정 유형 근거 (iii)의 '오거부 0'을 이번에 다시 확인하지 못했다.
  - gate 판 `merge_gate.py` 1137~1166(red-green만 빈 test 사슬을 거부), `role_hooks.py` 913~914·926·1066~1070, `role_commit_gate.py` 98~99, design 05 289행은 `4a286f0`에서도 인용과 같다.

### 확인된 것(재현)
- `dd60db6..4a286f0`에서 `A/`·`run_harness.py` diff가 **0**이다. 그래서 spec 수치는 `4a286f0`에서도 그대로 성립한다.
  - 내 측정(base `4a286f0` → 두 줄 head `e92d852`)이 spec과 같다.
  - E-LIB `hash` `1d2e3bf6…`, E-INST `folded_cascode` `raw_sha256` `ef3cd996…`, `without_topology_ref_sha256` `0ca6746f…`, PT3 1047/15·id 1062·결과 차이 0.
  - 파일럿 E-INST는 시간 때문에 생략했다.
- 계약 1·2 독립 판정기: DR·ACF 모두 PASS.
  - 코드 객체 같음 DR 16·ACF 5, 다름 0.
  - `__annotate__` 차이 DR 5·ACF 4.
  - 몸체에 문장 하나를 넣으면 FAIL이다.
- V3 PASS(`targets` DR·ACF, `mutants` 0). V5 PASS `diff_paths` []. V6 PASS `findings` []. V7 PASS `new_defs` [].
- V4는 `--interface-card`만 주면 ERROR(exit 2)이고, `--subject` 둘을 주면 PASS `files` []다. 모두 gate `4a286f0` 판 도구로 쟀다.
- card 35(V3 범위)의 '`def`만 본다' 한계는 그대로라 FU V3가 늘지 않는다(커밋된 spec 249행).
- `parse_spec_card`: phase 3·equivalence·approval 1·절 11. interface card는 두 표가 빈 행이고 키트 생성본과 바이트가 같다.
- `fu_launch.sh`(모래상자, T0 S 커밋 뒤 gate): `kit-cmds`·`conds`(13/13 exit 0)·`local`(커밋 `20139c6`)·`after-push`·`roles`가 통과했다.
  - `roles`는 worktree가 없으면 '빠진 것' 명령을 출력하고, 세 worktree를 만든 뒤에는 `role/test` = S·커밋 0·audit/code가 그 위에 있음을 확인한다.
  - 옵션 순서 가드는 T0와 같다.

---

## B34..B33 병합 뒤 착수를 막는 것(정리)
1. **T0-B1**: V4 규칙 (1) FAIL(`test_s009` 2줄). decision 면제 승인(사용자)이 있거나 B26-1이 같은 면제를 이미 받아야 한다.
2. **FU-B1**: 0단계에서 '재현할 수치'를 FU base로 다시 재거나(PT3 수·E-LIB·E-INST가 B26-1로 바뀐다) base = 병합본 꼴로 바꿔야 한다.
3. T0-S1~S4: `_SIZING_RECIPE` 문장, 브리프 1절 계약 11 누락, 0단계 계약 11 재측정, 계약 10 dry run을 B26-1 직후에 넣는 것.
4. 두 card 공통: measured 줄은 지금 초안에 없다. 의도대로 `pre`가 거부하는 것을 모래상자에서 확인했다.
