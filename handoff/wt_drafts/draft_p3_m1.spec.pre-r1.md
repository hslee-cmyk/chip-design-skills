---
id: 20261002-p3-move-mod1-gmid-lut
phase: 3
evidence_type: equivalence
gate_change: no
approval: 20260930-30-module-split-design
---
## 의도

design `30-module-split` **v8.5**(사용자 승인 UD-0 `20260930-30-module-split-design`, 답 2026-10-02 "승인 (Recommended)") §8 M행·§8.1·§2.2·§3·§10, card **M1**(첫 이동 card).
A = `skills/analog-gmid-design/assets`, SR = `A/sizing_recipe.py`, MOD1 = `A/gmid_lut.py`(계획 N3.10 521행 `| MOD1 | gmid_lut.py | LUT 인터페이스·보간·역산·곡선 검사·보간 오차 |`).

**무엇을 하는가**: D0b가 다시 쓴 레지스트리 '이관 목적지' 열과 N3.10 표(UD-0 개정 적용본)로 `move_plan plan`이 **MOD1(`gmid_lut.py`)에 배정한 최상위 단위 전부**를 SR에서 새 파일 `A/gmid_lut.py`로
**바이트 그대로** 옮기고, SR에는 그 이름들의 명시 재수출 줄 하나만 남긴다(design §2.2: `from gmid_lut import a, b, _c`, `import *` 금지, def 래퍼 금지). 함수 몸체·클래스·문장은 한 토큰도 바꾸지 않는다(계획 533행
"이동 전후 함수별 `ast.dump` 해시 동일 + import 줄만 차이"). 배정 집합은 card base에서 도구가 낸다 -- 이 card는 단위 목록을 손으로 정하지 않는다(작성 전 실측 2의 8단위는 모의 base의 관찰).

**MOD 파일 머리(design D-30)**: `gmid_lut.py`의 import 줄 = card base에서 돌린 `plan`의 `mod_imports["gmid_lut.py"]` **그대로**(이름마다 import 한 번 -- 원본 SR의 import 줄을 모아 붙이지 않는다).
모의 base에서 `["from __future__ import annotations", "import math", "import numpy as np"]` 세 줄이었다(작성 전 실측 3). MOD1은 번호 1이라 D-22의 '파일 끝 import'(MOD8·MOD9 몫)는 해당 없다.
SR 재수출 줄 위치는 **SR import 머리 바로 뒤**(D-22 -- 남은 모듈 수준 문장이 import 시점에 읽기 전에 묶인다; 모의 base에서 SR 45행 `import numpy as np` 뒤).

**왜 이 card가 첫 번째인가(design §8.1)**: ORDER(작은 번호부터 -- 새 MOD 파일이 잔여 shim을 import할 일이 없다). MOD1 단위는 트리 안에서 MOD1 단위만 참조한다(PLAN-LAYER `upward` 0 -- 작성 전 실측 3) --
그래서 `gmid_lut.py`는 엔진 파일을 하나도 import하지 않는다(ORDER 발견 0, IMPORT-ANY 단독 import 성공).

**착수 조건(design §8.1·§9.1 -- 전부 gate `master`에 병합)**: Phase 2 DoD PASS(충족 `2eefda1`), 확정 순서의 B34 → b26pre → backfill → B26-1 → B33(33) → **T0·FU·G1(32) → D0a → D0b**,
면제 묶기(34)·범위 정책(35). G1이 없으면 V3 대상 def 22·변이 590(작성 전 실측 8 -- design §4 F5), T0가 없으면 계약 test 위치 가정(F6), D0b가 없으면 배정 근거(레지스트리 열)가 없다.
D0b 병합부터 F2까지 동결(D-27)이 걸린 상태에서 시작한다.

**만들면 배선**: 새 def가 없다(옮긴 정의만). 새 파일 `gmid_lut.py`의 소비자는 SR의 재수출 줄(그리고 그것을 거쳐 SR 이름을 읽는 추적 파일 46개 -- 작성 전 실측 9)이고, `theta_search`·`sizing_layout_convergence`
등 뒤 MOD가 `mod_imports`로 `from gmid_lut import …`를 직접 쓴다(모의 M6 `from gmid_lut import SemiEmpiricalGmIdLUT`). 판정 도구 `move_plan check`는 이 card의 `equivalence.commands`에 들어간다(design §2.4 (ii)).

## 관찰 가능한 계약

1. **범위(diff, auditor)**: 이 card `Change-Id` 커밋들의 diff = `A/gmid_lut.py`(추가) + `A/sizing_recipe.py`(수정) 두 파일뿐이다. `git diff --name-only <base> <code_commit> -- tools` 빈 출력(design §8 M행 `tools/**` 변경 0, D-16),
   test·문서·레지스트리·library·`A/` 밖 0. test 커밋 0(판정 유형 근거).
2. **MOVE-AST(design §3) -- `move_plan check` 발견 0(auditor)**: 판정 도구 = `tools/migrate/move_plan.py`를 마지막으로 바꾼 판정 기록의 `code_commit`(지금 예정 D0a)에서 `git show`로 꺼낸 사본(design D-16·§10 `MPC`).
   `"$PY" "$S/move_plan.py" check --root "$ISO" --base <base> --head <merge> --card gmid_lut.py "${MP_ARGS[@]}"`(`MP_ARGS` = design §6.3 bash 배열) → exit 0, `findings`의 11종
   (`move-set`·`move-rejected`·`changed`·`lost`·`rebind`·`future`·`import-dup`·`stmt-order`·`order`·`shim`·`cache`) 모두 빈 목록. 그리고 일관성 점검(증거로 세지 않는다 -- design §10 E2 ③): `assigned` 수 = `moved_units` 수,
   `moved_units`의 목적지가 모두 `A/gmid_lut.py`, `moved_defs` 키 집합 = 아래 계약 4 V3 JSON `moved`의 `to` 집합.
3. **바이트 이동(auditor, 독립 측정 -- `check`와 다른 식)**: (a) `gmid_lut.py`의 최상위 문장 = `mod_imports["gmid_lut.py"]`(card base `plan`) 줄을 차례로 파싱한 import 문장들 + 그 뒤의 옮긴 단위들. 옮긴 단위마다
   `ast.dump(node)`(docstring **포함**, `include_attributes=False`)가 base SR의 같은 단위와 같다. 모듈 docstring·그 밖의 새 문장 0('결정 필요 항목' M1-1). (b) 병합본 SR 최상위 문장 열 = base SR 최상위 문장 열에서
   옮긴 단위를 뺀 열에 재수출 `ImportFrom(module='gmid_lut', level=0)` **하나**를 import 머리 바로 뒤(base에서 첫 비-import 문장 앞)에 끼운 것(`ast.dump` 열 비교). 재수출 이름 집합 = 옮긴 단위가 바인딩하는 이름 전부
   (`_` 접두 포함, 이름순, `as` 없음). (c) `from __future__ import annotations`가 `gmid_lut.py`의 첫 문장이다(SR 35행과 같은 기능 집합 -- G1 M-4·`check` `future`).
4. **게이트(auditor, 판정 때 gate `master` 판 도구 -- G1·면제 묶기·범위 정책 병합본)**: V3 exit 0, JSON `defs` = `[]`, `mutants` = 0, `survivors` = `[]`, `move_rejected` = `{}`, `not_targeted` = 0, `targets_by_def` = `{}`
   (범위 정책 키 -- design §8 M행·§5.5.2, §10 E2 ①); `moved`는 비지 않는다(옮긴 def가 실제로 이동 인식됨 -- 공허 방지). V6 exit 0, `findings` `[]`, `move_rejected` `{}`. V7 exit 0, `new_defs` `[]`, `move_rejected` `{}`.
   V5 `diff_paths` `[]`(test diff 없음). V4는 interface card 표가 비어 `--interface-card`만 주면 `ERROR`이므로 FU 선례대로 card가 옮기는 대표 심볼을 subject로 준다
   (`--subject gmid_lut:SemiEmpiricalGmIdLUT --subject gmid_lut:GmIdLUT` → `PASS`, `files` `[]`). V8·V9 도입 Phase 4 -- N/A.
5. **IMPORT-ANY(design §3·§10 `import_any` 그대로, D-22 (3))**: 병합본 체크아웃에서 `IMPORT-ANY tried=<n> expected=<n> failed=0` 한 줄, `FAIL`·`INVALID` 줄 없음, 함수 종료 코드 0. 기대 수 = `import_layering` `present` ∪ 트리에 있는
   `--split` 파일(모의 base 5 → 병합본 6: `gmid_lut` 추가).
6. **동작 보존(auditor, base·병합본 같은 조건 -- design §8 M행 (c))**:
   (a) **PT3 전체**(design §10 `PT3`) base·병합본: 수집 test id 집합이 같고 id마다 결과(passed/failed/error/skipped/xfailed)가 같다, 실패 0. (V1 판정과 별도로 id별 대조를 판정 기록에 남긴다.)
   (b) **E-LIB**(`e_lib.py` 사본, sha256 `045f65c8cc05e98699518ca123ef8aac0c93b6b51932179aae707e1d21f46201`) 출력 JSON 전체가 base와 같다(`hash` 포함 -- design D-28: M card는 `e_lib.py` 그대로, 뺄 키 없음).
   (c) **E-INST**(`e_inst_p3.py` -- design D-28 정본, design 커밋의 `docs/03-analysis/gain-budget-gmid-sizing-30-module-split/scripts/e_inst_p3.py`) 파일럿(`current_reuse_telescopic_ota`)·`folded_cascode`: 출력 JSON의 키 중
   `engine_origin`을 뺀 전부가 base와 같고(`raw_sha256`·`without_topology_ref_sha256`·`field_sha256`·`exists`·`fail_in_stdout`·`path_string_hits`·`topology_ref_equals_expected_contract1` 등), 병합본 `engine_origin`의 모든 경로가 `<iso>` 안이며
   `gmid_lut`을 포함한다(로드된 엔진 모듈 목록이 바뀌는 것이 이 card의 정의 -- 출처 확인이지 동작 차이가 아니다). stdout 사본은 `elapsed=<초>s`를 가리면 같다. base와 병합본은 **같은 체크아웃 경로**에서 차례로 잰다.
7. **ORDER·CACHE-ID·SHIM**: 계약 2의 `order`·`cache`·`shim` 발견 0이 판정이다. 풀어 쓰면 -- `gmid_lut.py`의 import가 가리키는 트리 파일 0(N3.10 번호 ≥ 1 파일과 split 파일 import 없음); 모듈 최상위 빈 dict 캐시를
   전역 읽기로 쓰는 단위가 캐시와 다른 파일에 있는 것 0(MOD1 단위에는 모듈 캐시가 없다 -- `_QUERY_CACHE_MAX`는 정수 상한, 인스턴스 캐시는 `self` 속성); SR의 새 최상위 문장은 재수출 줄뿐이고 재수출 이름마다 SR 바인딩 출처 =
   `("def", A/gmid_lut.py, 이름)`.
8. **중간 상태 이름 해석(auditor, design §10 E3·E3b의 python을 그대로 재사용한 card 단위 관찰 -- 강화, '결정 필요 항목' M1-3)**:
   (a) **E3 식**(§10 `E3_AST`)을 base·병합본에 돌려 D-9 제외 집합 밖 파일 목록이 같다 -- 이 card는 shim 모듈(SR·TL·DR) importer를 더하거나 빼지 않는다(F1 몫). 거부 확인: 두 판 모두 `stmt`·`call` 줄이 0이 아니다.
   (b) **E3b 식**(§10 `E3B_AST`)에서 `stick_diagram`을 이 card가 단위를 내보내는 split 파일 줄기(M1: `sizing_recipe`)로 바꾼 사본을 `<base> <merge>`로 돌리면 `LIVE moved_out=<m> base_files_reading_moved_out=<f>`(m > 0, f > 0)이고,
   `E3b FAIL` 줄 집합 = 같은 사본을 `<base> <base>`로 돌린 `E3b FAIL` 줄 집합(지금 있는 표지 이름 `<동적 이름>`만 -- 새 FAIL 0), `ERROR` 없음. 단위를 내보내지 않는 split 파일(M1: SD·TL·DR·ACF)은 같은 사본이 `E3b INVALID`(m = 0)이고
   그것을 기록만 한다(정의상 대상 없음).
9. **레지스트리 정합(REG-DEST 유지)**: 병합본에서 `plan`(같은 `MPC` 사본, `--rev <merge>`)이 exit 0, 판정 목록 일곱 모두 빈 목록, (단위 키 → MOD) 사상이 base `plan`과 같다(옮긴 단위는 규칙 `A-0`) --
   D0b 계약 test `contracts/test_p3_registry_dest.py`가 PT3 안에서 PASS하는 것과 같은 사실을 auditor가 한 번 더 적는다.

## 신규 시그니처

| 모듈 | 심볼 | 시그니처 |
|---|---|---|

## 판정 유형 근거

**equivalence, test 커밋 0.** 계획 N3.12.3(686행) "동작을 보존하는 변경(TS1, Phase 2 통합, **Phase 3 이동**)은 `equivalence`", design §8 M행 "equivalence(test 커밋 0 가능 -- 05 §9.2 289행)".
test 커밋 0의 규칙·게이트 근거는 FU spec(`20261002-p3-future-annotations`) '판정 유형 근거'와 같다(design 05 §10-4 289행 M^1 = `old`, `merge_gate.py` equivalence는 빈 test 사슬을 거부하지 않음,
redteam 20(e) 정상 흐름). 브랜치 `role/test/<id>`는 커밋 0으로 만들어 둔다(FU 작성 전 실측 15와 같은 절차).

**신규 시그니처가 비는 이유**: 옮긴 심볼은 새 심볼이 아니다 -- G1 `moved_defs`가 22 def 전부를 '옮긴 정의'로 인정하고(계약 4 `moved`), 같은 이름이 SR 재수출로 계속 import된다. 표에 넣으면 red 수집 플러그인이
'base에 없는 심볼'로 읽는데 equivalence card에는 red가 없다.

**계획 838행(V2) 'Phase 3 AST 해시 동일'을 대신하는 것**: 계약 2(`check` -- G1 `moved_defs`의 (종류, 키, `def_hash`) 대조 + 옮긴 클래스 안 def 해시 + 제자리 단위 해시)와 계약 3(독립 `ast.dump` 열 비교, docstring 포함).
V2 basis는 이 두 문장을 쓴다.

**red-green으로 하지 않는 이유**: "`gmid_lut.py`가 있다"를 단언하는 test는 base에서 실패해 형식상 red가 되지만, 운영 동작이 바뀌지 않으므로(계약 6) red-green은 동작 변경을 기록하게 된다. 위치 단언을 영구 test로 두는 것은 T0가
없앤 '정의 파일 가정'을 다시 들이는 것이다(design §7.1 A군) -- 위치의 영구 판정은 D0b 계약 test(`reg_mismatch` = [], 규칙 `A-0`)가 이미 맡는다(계약 9).

**V3 규모(작성 전 실측 8)**: G1 시제품 판 V3 대상 def 0·변이 0. G1이 없으면(gate `dd60db6` 판 도구의 대상 선택 식) 새 파일 `gmid_lut.py`의 def 22개 전부가 대상, 변이 590개 -- 인벤토리 test가 죽이지 못하면 전부 생존.

## oracle 종류와 출처

(c) 동작 보존: PT3 test id별 결과, E-LIB·E-INST 출력 -- 기대값 = base 실행 결과(auditor가 격리 복제본에서 같은 명령으로). (a) 구성: 계약 3의 기대 모양(옮긴 단위 `ast.dump` = 원본, SR = 원본 − 옮긴 단위 + 재수출 한 줄)은
계획 533·534행과 design §2.2에서 손으로 정하고, 배정 집합은 card base의 `plan` 출력(D0b 레지스트리가 정한 것 -- 이 card가 바꾸지 않는 입력)이다. 판정 도구 `move_plan check`는 D0a `code_commit` 사본이고
code-author가 같은 card에서 바꿀 수 없다(D-16). auditor는 계약 3·6·8의 대조식을 독립으로 쓴다 -- `C:/g200` 모의 스크립트(`_drafts/p3kit_m1/`)는 작성 전 실측용 시제품이고 판정 도구가 아니다(작성자≠검증자).

## 거부해야 할 입력

auditor 판정기 자기 점검(병합본 사본에 하나씩 커밋해 판정기가 실제로 거부하는지 먼저 확인 -- 모의 실측은 작성 전 실측 10):
| ID | 변형(병합본 기준) | 거부해야 할 판정 |
|---|---|---|
| R-1 | 옮긴 def 하나의 몸체 상수 토큰 하나를 바꿈(`_invq_newton`) | 계약 2 `move-set`·`move-rejected`·`changed`·`lost`·`shim` + 계약 3 + 계약 4 V3 `defs` 비지 않음 |
| R-2 | SR 재수출 줄에서 이름 하나(`GmIdLUT`)를 뺌 | 계약 2 `rebind`(SR 잔류 단위가 그 이름을 읽음)·`shim` (c) + 계약 3 (b) + 계약 8 (b) 새 FAIL. **G1(V3·V6·V7)은 이것을 거부하지 않는다**(M-2는 원본 자리에 이름이 없는 것을 허용) -- `check`가 맡는 몫 |
| R-3 | `gmid_lut.py`에 `import sizing_recipe` 한 줄 | 계약 2 `order` + 계약 5 IMPORT-ANY FAIL(`gmid_lut` 단독 import가 순환 부분 초기화로 `ImportError`) |
| R-4 | `gmid_lut.py`에 `import numpy as np`를 두 번 | 계약 2 `import-dup`·`move-rejected`(M-4 연쇄)·`changed`·`lost`·`rebind` + 계약 4 V3 `defs` 17 |
| R-5 | `gmid_lut.py`의 `from __future__ import annotations` 줄을 뺌 | 계약 2 `move-rejected`(8단위 모두 M-4 `__future__`)·`move-set`·`changed`·`lost`·`rebind` + 계약 3 (c) + 계약 4 V3 `defs` 22. `future` 발견 자체는 비어 있다 -- D0a 계약 4 `future`는 `moved_defs` `units`의 목적 파일만 보는데 옮긴 단위가 0이 되기 때문(문언대로의 동작, 거부는 `move-rejected`가 한다) |
| R-6 | 다른 MOD(MOD5) 배정 단위 `estimate_mismatch_sigma`를 함께 옮김 | 계약 2 `move-set`(배정 밖 이동 1) + 계약 3 (a). G1(V3·V6·V7)은 바이트 이동이라 거부하지 않는다 -- 이관표 대조는 `check` 몫 |
| R-7 | `gmid_lut.py` 머리에 모듈 docstring 한 줄 | 계약 2 `changed`(새 문장 단위) + 계약 3 (a) -- '결정 필요 항목' M1-1이 (나)로 정해지면 이 행은 지운다 |

## library 회로 적용 여부

적용 -- E-LIB 9회로(`load_topology`·`run_topology_pipeline` 경로 -- LUT 클래스를 지나지 않아 이 card의 대조선 역할), E-INST 파일럿·`folded_cascode`(하네스 `run()`이 `SemiEmpiricalGmIdLUT`로 실제 LUT를 읽는다 --
옮긴 클래스를 실제로 지난다). 회로·넷·소자 이름은 이 card의 도구·판정식에 없다(topology 무관 -- 배정은 레지스트리·N3.10·소스 구조에서만).

## 무동작 판정 입력(무발동 값)

새 산출물 필드 없음. library 회로 전부·기존 test 전부의 판정·산출물이 base와 같다(계약 6). 발동 계수 ID 없음.

## 재현할 수치

(모의 base = gate `dd60db6` + FU 대역 + UD-0 v8.5 개정 + G1 시제품 + D0a 시제품(D-31 규칙 재구현) + D0b 재생성 대역 = 복제본 `4b2ab85`, 모의 head = `a206346`(M1 이동, 모듈 docstring 없음), 스크래치 `C:/g200`, 2026-10-02 --
**전부 관찰**: 실제 base(B34·B26-1·B33 등 병합 뒤)에서 auditor가 다시 잰다)
* 배정 MOD1 8단위(모두 SR): `GmIdLUT`(52~73행, def 2)·`_multilinear_interp`(141~203)·`_multilinear_interp_point_multi`(206~251)·문장 `_QUERY_CACHE_MAX = 400000`(257)·`SemiEmpiricalGmIdLUT`(259~672, def 15)·`_invq_newton`(1343~1353)·
  `build_toy_lut`(1356~1394)·`lut_conditions_from_npz`(4782~4803) -- 줄은 gate `dd60db6` SR(모의 base SR과 blob 같음 `97a6c7bb…`). 규칙 A-1 5·A-4 2·A-5 1.
* `mod_imports["gmid_lut.py"]` = `from __future__ import annotations` / `import math` / `import numpy as np`. SR 재수출 = `from gmid_lut import GmIdLUT, SemiEmpiricalGmIdLUT, _QUERY_CACHE_MAX, _invq_newton, _multilinear_interp, _multilinear_interp_point_multi, build_toy_lut, lut_conditions_from_npz`(SR 46행).
* `check` exit 0, 발견 11종 모두 0, `assigned` 8·`moved_units` 8·`moved_defs` 22. 독립 `ast.dump`(docstring 포함) 8/8 같음, SR(base − 옮긴 단위) = SR(병합본 − 재수출 1줄).
* V3(G1 시제품) PASS `defs` []·`mutants` 0·`move_rejected` {}·`moved` 22; V6 PASS `findings` []; V7 PASS `new_defs` []. G1 없는 대상 선택 식: def 22·변이 590.
* IMPORT-ANY base `tried=5 expected=5 failed=0`, 병합본 `tried=6 expected=6 failed=0`.
* PT3 base·병합본 1054 passed·15 xfailed, test id 1069(D0b 계약 test 대역 7 포함), 결과 차이 0(352.9 s / 339.4 s).
* E-LIB `hash` `1d2e3bf6acf762ebea14aa526405bfe63db9632cfab68672b93948c2be3b7a8f`(base = 병합본, JSON 전체 같음). E-INST(`e_inst_p3.py` `7d26134a…`) 파일럿·`folded_cascode`: 22키 중 `engine_origin`만 다름(병합본에 `gmid_lut` 추가),
  `raw_sha256` `2fc426d9ef3a9623898d54a3ee712c64913460770f3361c830938c11a1eb863d`·`ef3cd9963d0a80ac6e07ea5909286db1d8e67d8351a355c8aafd7a01fc9bb3f0`, `without_topology_ref_sha256` `185b675e…`·`0ca6746f…`(FU 판 수치와 같음), stdout 가림 사본 같음.
* E3 식 base·병합본 `stmt` 69·`call` 9·제외 밖 66파일(같음). E3b 식(SR 사본) `LIVE moved_out=8 base_files_reading_moved_out=46 pre_existing=1`, FAIL 9줄(모두 `<동적 이름>`, 계약 test 4파일) = base 자기 대조 FAIL 9줄. SD·TL·DR·ACF 사본 `INVALID`(m = 0).
* `plan`(병합본) exit 0·일곱 목록 0·사상 차이 0(옮긴 8단위 `A-0`).

## 결정 필요 항목

모두 **기본안이 있다**(원칙 유도 -- 사용자 질문 아님). M1-2만 card 작성 전에 오케스트레이터가 D0a/D0b 쪽에서 닫아야 한다.
* **M1-1 MOD 파일 모듈 docstring**: D0a 계약 4 `changed`는 "head 단위 중 옮긴 단위가 아니고 base 같은 파일에 같은 단위가 없는 것"이라 새 MOD 파일의 모듈 docstring(문장 단위)을 `changed`로 잡는다(모의: docstring 있는 head `8a93f24` →
  `changed` 1, 없는 head → 0). 그리고 DoD E6(`--card ALL`)도 그것을 `changed`로 잡는다(`--allow-changed`는 M10 둘뿐). **기본안 (가)**: M card의 MOD 파일에는 모듈 docstring을 두지 않는다(이동 card = 이동만, card당 한 책임) --
  docstring은 Phase 4 이후 card가 더한다. 대안 (나): D0a 계약 2의 '모듈 docstring 배정 제외'와 같은 읽기로 D0a 계약 4 `changed`·`lost`에서 파일 첫 문장 문자열 `Expr`을 빼고(SHIM (b)도 docstring을 허용한다) design §3 MOVE-AST (b) 문언을 맞춘다 --
  D0a는 미병합이라 spec 초안 개정으로 가능하지만 판정 도구 범위가 넓어진다(약화 방향 아님: docstring은 동작 없음). 기본안은 문서·도구 개정이 0이다.
* **M1-2 문장 단위 키와 `_QUERY_CACHE_MAX`(D0a·D0b 착수 전에 닫을 것 -- 이 card 단위 집합의 안정성)**: D0a 계약 2는 문장 단위 키를 "바인딩하는 이름을 이은 것"으로 정했는데, D0b 착수 키트·design 부록 A F5v85의 수치(배정 403·A-4 229·A-5 64·
  `upward` 0)는 G1 시제품의 `<stmt:해시>` 키로 잰 것이다(D0b spec '시제품 한계' -- 상수 행 7개가 비대상). 이 card 모의에서 같은 규칙을 **계약 문언의 키**로 다시 돌리면 상수 행 7개 중 4개의 배정이 바뀌고
  (`_COMPENSATION_REGISTRY`·`_L_ROLE_TARGETS` MOD8 → MOD4, `INSTANCE_TOP_FIELDS` MOD9 → MOD7, **`_QUERY_CACHE_MAX` MOD1 → MOD4**), `upward` 1(`SemiEmpiricalGmIdLUT -> _QUERY_CACHE_MAX`)·`cycles` 1(MOD1 ↔ MOD4)이 생긴다 --
  레지스트리 277행 함수 칸이 `_QUERY_CACHE_MAX`이고 목적지 칸이 `gmid_sizing_engine.py(+ S0 …)`(A-4 → MOD4)이며 소비자는 MOD1 토큰 `SemiEmpiricalGmIdLUT`뿐이다. 그러면 D0b가 멈추고(design D0b 행 '`upward` → N3.10 토큰(D-11)') 별도 승인이 필요하다.
  **기본안**: D0b가 자기 base에서 계약 문언 키로 계산해 이 충돌을 보면, design §9 원칙 P2(트리 안 참조 없는 도우미는 부르는 쪽 MOD 책임에 맞으면 내려간다 -- `_multilinear_interp_point_multi`·`metric_unit_scale` 선례)대로
  N3.10 MOD1 '대표 대상'에 `_QUERY_CACHE_MAX` 토큰 하나를 더하는 diff를 D-11 별도 승인(`target_kind: diff`)으로 받는다. 모의(복제본 가지 커밋에 그 토큰만 더함): `upward` 0·`cycles` 0, MOD1 단위 = 위 8단위 그대로, `reg_mismatch` 80(재생성 전, 행 1 늘어남).
  어느 길이든 **M1 단위 집합은 같은 8단위**다(키 방식만 다르고 결과 같음 -- 작성 전 실측 2). 오케스트레이터 할 일: D0a·D0b spec 초안에 이 관찰을 사실로 적고(D0b 재생성 표가 상수 행 7개를 대상으로 바꾸는지), M1 card 커밋 전에 D0b 판정 기록의
  `_QUERY_CACHE_MAX` 배정이 `gmid_lut.py`인지 확인한다.
* **M1-3 계약 8(E3·E3b 식의 card 단위 사용)**: design §8 M행에는 없는 판정이다(design은 E3·E3b를 DoD로만 둔다). 판정을 더하는 쪽(강화)이고 도구는 §10 python 그대로라 기본안 = 계약에 둔다. 표지 이름 처리만 DoD와 다르다:
  DoD E3b는 표지(`<동적 이름>` 등)를 base에 있어도 FAIL로 세지만(v8 B2), card 단위 사용은 'base 자기 대조와 같은 FAIL 집합'(새 FAIL 0)으로 본다 -- SR 사본에는 지금 계약 test 4파일의 `getattr(sr, name)` 9줄이 표지로 남아 있어
  DoD 식 그대로면 이동과 무관하게 FAIL이다(그 9줄은 F1이 `sizing_recipe` import를 바꿀 때 사라진다). 대안: 계약 8을 빼고 DoD에만 둔다.
* **M1 밖(참고 -- 이 card의 결정 아님)**: 뒤 card 모의에서 드러난 것 -- M4·M8·M9의 완전 shim이 unit selftest의 엔진 밖 이름 import(`from topology_library import math` 등)를 깨 PT3 수집 오류가 난다(SHIM (b) 문언 -- M4 착수 전 결정),
  ACF 재수출 줄 위치(M2·M9)는 어느 판정도 보지 않는다. 상세는 `_drafts/m_cards_plan.md` W-1·W-2. M1은 SR이 완전 shim이 되지 않아(잔여 단위·import 그대로) 해당 없다.
* **id 날짜**: 초안 id `20261002-p3-move-mod1-gmid-lut`(slug는 design §8 `p3-move-mod<n>-<이름>`). card 커밋 날짜에 맞춰 바꾼다.

## 작성 전 실측

(재측정 = gate `master` **`dd60db6`**(작업 시작 판), 2026-10-02. **작업 중 gate `master`가 `36e170e`로 나아갔다**(`8b1f929`·`dd01d1d`·`5a602d4`·`3e835e0` 면제 묶기(34) 병합·판정 기록, `6c8287f` design 30 v8.5 + 문서 개정, `36e170e` 승인 기록) --
그 판에서 다시 확인(읽기 전용): 엔진 `A/*.py`·`workspaces/run_harness.py`·레지스트리·`tools/migrate` diff 0, SR blob 같음(`97a6c7bb…`), 계획 N3.10 519~530행 = 이 실측이 복제본에 적용한 UD-0 v8.5 개정과 **글자까지 같음**,
`docs/03-analysis/gain-budget-gmid-sizing-30-module-split/scripts/e_inst_p3.py` sha256 `7d26134a…`(아래 측정 사본과 같음), 승인 기록 `.ai/approvals/20260930-30-module-split-design.md` 생김(blob `b956e7ce`, card 목록 111행 `p3-move-mod<n>-<이름>`),
`tools/gates` 차이는 면제 묶기 5파일뿐(V3 출력에 `exempt_ignored`·`survivor_bindings` -- design §10 E2 '기준이 아니다'). 그래서 아래 M1 수치는 `36e170e` 기준에서도 그대로이고, G1 시제품 설치 앵커는 G1 card가 새 base에서 다시 잰다.)
(작업 시작 판 `dd60db6`, 2026-10-02. 실제 저장소 쓰기 없음 -- 격리 복제본 `C:/g200/r`(`git clone --no-local`, TMP/TEMP `C:/g200/tmp`, 작업 끝에 `C:/g200` 삭제).
B34·b26pre·backfill·B26-1·B33·면제 묶기 뒤 판·범위 정책·T0·FU·G1·D0a·D0b는 **모두 미병합**이라 복제본 사슬로 대역했다: `dd60db6` → `33956d2` FU 대역(DR 28행·ACF 38행 앞 `from __future__ import annotations`) →
`1654062` UD-0 v8.5 N3.10 개정(`p3_doc_amendments.md` §1 (a)(가)~(d)·§9 (e)~(h) 8블록, '현재' 정확 일치 단언) → `5f46934` G1 시제품(`install_proto.py` `5790433c…` + `g1_core.py` `b3c4e391…`) →
`0446e34` D0a 대역(`move_plan_proto.py` `d2f3da97…` + D0a 계약 2 v8.4/v8.5 문언으로 다시 얹은 D-31 규칙·`mod_imports`·`import_conflicts` + 계약 4 문언의 `check` 11종 -- 스크래치 재구현, `_drafts/p3kit_m1/move_plan_sim.py`) →
`4b2ab85` D0b 대역(`regen_registry.py --write` 대상 347·중첩 7·비대상 25, `보류(Phase 3)` → `보류(Phase 4)` 9칸, 계약 test 시제품) = **M1 모의 base**. 이동 생성기 `_drafts/p3kit_m1/gen_move.py` → `a206346`(모의 head).
B26-1·B34 등이 SR을 바꾸면 줄 번호는 바뀌고 단위 집합은 바뀌지 않을 것으로 본다(두 card 사이트에 MOD1 단위 없음 -- design §6.4 표) -- 실제 base에서 다시 잰다.)

1. 사실 문장 재측정: `git show dd60db6:<plan>` 521행 MOD1 행 원문(위 '의도'), UD-0 (e)로 `_multilinear_interp_point_multi` 토큰 추가. SR: future 35행, import 머리 끝 45행(`import numpy as np`), 8단위 줄(재현할 수치), 파일 blob `97a6c7bb…`(모의 base와 같음).
   레지스트리(`dd60db6`): MOD1 단위 행 69·73~83·277~281·454(목적지 칸 `gmid_sizing_engine.py`), 489·490(§7 `_invq_newton`·`build_toy_lut` -- `tests/ 픽스처`, `보류(Phase 4)`), 497(§7 `lut_conditions_from_npz` -- `circuit_state_graph S0`, `보류(Phase 6a)`).
   D0b 재생성 뒤 그 칸이 `gmid_lut`이 된다(모의 `plan` 규칙 A-4 2 = `_invq_newton`·`build_toy_lut`). §7 단위는 **옮기고 D 유지**(design D-10) -- 이 card는 §7 처리 칸을 바꾸지 않는다.
2. 단위 집합(관찰): 모의 base `plan` exit 0, 배정 403, 판정 목록 일곱 0, MOD1 8단위(전부 SR). 같은 규칙을 D0b 재생성 **전** 트리(`5f46934` + D0a 대역)에 돌린 값 = design 부록 A F5v85·D0b spec 실측 3과 같음
   (배정 403, A-1 60·A-4 229·A-5 64·A-2 38·A-6 7·A-K 2·A-7 2·A-3 1, `reg_mismatch` 79, `_kv_table` = `instance_report_builder.py`) -- 재구현이 D0b 키트 결과를 재현한다. 문장 키를 계약 문언(바인딩 이름)으로 바꾼 판은 '결정 필요 항목' M1-2.
3. `mod_imports`·PLAN-LAYER: `mod_imports["gmid_lut.py"]` 3줄(재현할 수치), `import_conflicts` 0, `upward` 0 -- MOD1 단위의 트리 안 참조는 MOD1 단위뿐(ORDER 발견 0과 같은 사실).
4. 쓰기 경로(계획 N3.12.2): `A/gmid_lut.py`·`A/sizing_recipe.py` = gmid-code-author(엔진 소스). test-author 산출물 없음(test 커밋 0). 판정 기록·계약 2~9 측정 = auditor. `tools/**`는 누구도 바꾸지 않는다(D-16).
5. 계획서 소비자: 이 card는 이름을 지우거나 이름을 바꾸지 않는다(위치만 -- 재수출로 같은 import 경로 유지). `git grep -n gmid_lut dd60db6 -- '*.py' docs/01-plan docs/02-design` → 계획 521·543행, history 4162·5218·5231·5249행(문서 서술), `.py` 0.
   새 파일 이름 `gmid_lut.py`는 `dd60db6`에 없다(`git ls-tree` 빈 출력).
6. 미배선: 새 def 0. V7 `new_defs` [](G1 시제품) -- 면제 불필요.
7. 기존 계약 test: MOD1 이름을 읽는 계약 test(`dd60db6`) = `test_restore_plan_functions.py`(`sr.lut_conditions_from_npz` 모듈 속성 호출 -- B군, 재수출로 유지, F1 몫), `test_d_delete_dead.py`(`fT`·`junction_cap` GONE 검사 -- `_engine_files()` glob이 새 파일을 포함),
   `test_probe_dup_scan.py:157`(합성 소스 문자열 -- 입력), `tests/conftest.py:160`(`from sizing_recipe import build_toy_lut` -- B군, F1). T0 A군(`test_ic5.py` `_DOMAIN_TABLE` 21키, `test_dup_w_calc.py:442` `size_transistor`, `test_ts6_dead_probes.py` `_L_ROLE_MULTIPLIERS`·`audit_vsb_consistency`)에
   MOD1 단위 0 -- T0 없이도 M1 모의 PT3 결과 차이 0(재현할 수치). 조정 불필요, V5 없음.
8. V3 규모: G1 시제품 `mutate_changed.py --root C:/g200/r --base 4b2ab85 --head a206346 --pytest-ini … --gmid-phase=3 --gmid-strict=` → PASS, `targets` 2파일, `mutants` 0, `defs` [], `move_rejected` {}, `moved` 22(131 s).
   G1 없는 판(`git archive dd60db6 tools/gates`의 `changed_defs`·`mutants`, 정적 계수): def 22·변이 590. 범위 정책(35) 시제품이 키트에 없어 `not_targeted`·`targets_by_def` 키는 재지 못했다(G1 시제품 `G1_SCOPE=1`은 `scope_proto` 없음 -- FU 실측 8과 같은 한계) -- 대상 def가 0이라 두 키는 0·`{}`일 것으로 본다(판정 때 실측).
   V6 PASS `findings` [](104 s), V7 PASS `new_defs` [](99 s), `check` 58 s, `plan` 29 s.
   V4(base 판 `test_lint.py`) `--interface-card`만 → `ERROR`(exit 2, '피검 심볼이 없다'), `--subject gmid_lut:SemiEmpiricalGmIdLUT --subject gmid_lut:GmIdLUT` 추가 → `PASS`·`files` [](exit 0). V5 `PASS`·`diff_paths` [].
9. 읽는 쪽 범위: E3b 식 SR 사본 `base_files_reading_moved_out=46`(제외 집합 밖 추적 `.py` 중 옮긴 8이름을 `sizing_recipe`에서 읽는 파일) -- 전부 재수출로 계속 해석된다(새 FAIL 0). E3 식 importer 66파일 불변.
10. 거부 입력 실측(병합본 사본에 하나씩 커밋, 모의 `check` + G1 시제품 정적 V3 + 단독 import): R-1 `check` exit 1(`move-set` 2·`move-rejected` 1·`changed` 2·`lost` 2·`shim` 1), V3 대상 def 2·변이 141(G1 `build_toy_lut` M-4 연쇄 포함);
    R-2 `rebind` 9·`shim` 1, V3 0(G1은 거부하지 않음 -- `check` 몫 확인); R-3 `order` 1 + 단독 import `gmid_lut` `ImportError`(순환 부분 초기화); R-4 `import-dup` 1·`move-rejected` 3·`changed` 3·`lost` 3·`rebind` 2·`move-set` 3·`shim` 1, V3 def 17·변이 440;
    R-5 `move-rejected` 8(전부 M-4 `__future__`)·`move-set` 8·`changed` 8·`lost` 8·`rebind` 11·`shim` 1, `future` 0(옮긴 단위 0 -- 표 R-5 설명), V3 def 22·변이 590(G1 없는 판과 같다); R-6 `move-set` 1, V3 0;
    R-7(모듈 docstring, head `8a93f24`) `changed` 1(M1-1). 여섯 변형 모두 단독 import는 R-3만 FAIL. 원자료 `_drafts/p3kit_m1/out/neg_M1.jsonl`.
11. test 이름·모양: 새 test 없음.
12. 같음 판정: 계약 3은 `ast.dump` 문자열 열 비교(순서 포함), 계약 6 (a)는 test id별 결과 문자열, (b)는 JSON 전체, (c)는 `engine_origin`을 뺀 키별 값 비교 + `engine_origin` 경로 포함 조건. `set`을 `==`로 비교하는 계약 없음.
13. red 모양: red 없음(equivalence). 거부 확인은 auditor 측정.
14. 양식: gate `dd60db6` `tools/gates`(`git archive`)의 `role_paths.parse_spec_card(text, expect_id="20261002-p3-move-mod1-gmid-lut")` → exit 0, 머리 `phase` 3·`evidence_type` equivalence·`gate_change` no·`approval` 1,
    본문 절 11개(양식 순서 그대로). `interface_card.py <이 spec> --root <모의 base 트리>` → exit 0, '기존 함수 0개', 두 표 비어 있음(FU·D0b와 같은 모양 -- V4 subject 우회의 이유).
15. 앞 card 의존 재확인(오케스트레이터, card 커밋 직전): (i) gate `master`에 T0·FU·G1·D0a·D0b 판정 기록 (ii) D0b 판정 기록의 `plan` 출력에서 `gmid_lut.py` 배정 단위 목록·`mod_imports["gmid_lut.py"]` -- 이 card의 '재현할 수치'를 그 값으로 바꾼다
    (iii) `git diff --stat <D0b 병합> gate/master -- skills/analog-gmid-design/assets/*.py workspaces/run_harness.py tools docs/03-analysis/gain-budget-gmid-sizing.function-registry.md` 빈 출력(D-27 동결 -- 'D0b 병합~M1 base 구간은 DoD가 덮지 않는다').
