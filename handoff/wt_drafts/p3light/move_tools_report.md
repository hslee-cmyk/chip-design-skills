# Phase 3 가벼운 이동 도구 보고서 (p3light/tools)

작성 2026-10-07. 절차: `_drafts/p3light/PROCEDURE.md`(남기는 것 3·4). 시험 복제본 `/c/g451/repo`(gmid-light `6df4bd7`에서 `git clone --no-hardlinks`), 작업 뒤 삭제.
gmid-light 작업 트리·메인 저장소는 건드리지 않았다(읽기만).

## 0. 재사용한 것(새로 만들기 전 확인)

| 재료 | 쓰임 |
|---|---|
| `_drafts/p3kit_m2_m9/move_plan_sim.py`(sha256 6ac0cf24…) | `tools/mp_core.py`로 복사. D0a `plan` 시제품 = design 30 §6.2 규칙 A-0~A-7(계획 N3.10 '대표 대상' + 레지스트리 '이관 목적지' 열)로 배정·`mod_imports`·`reexports`·PLAN-LAYER 목록을 낸다. 바꾼 곳은 `load_gates` 하나(아래) |
| `_drafts/p3kit_m2_m9/g1_core.py`(= `g1_kit/g1_core.py`, sha256 b3c4e391…) | `tools/g1_core.py`로 복사. G1 시제품 `SourceIndex`(단위·global_names·binding_origin). 저장소 `tools/gates`에는 G1이 없으므로 `mp_core.load_gates`가 `reachability` 이름 공간에 exec로 주입한다 -- **저장소 파일을 고치지 않는다**(옛 키트는 `install_proto.py`로 복제본의 gate 파일을 고쳤다) |
| `_drafts/p3kit_m2_m9/gen_move.py` | `move.py` 생성 규칙의 틀(MOD 파일 = `mod_imports` + 단위 바이트, split 파일 = 범위 삭제 + 재수출 한 줄, 완전 shim). 고친 점: W-2 머리 끝 계산(`sys.path.*` 식 문장 뒤 import까지), W-3 모듈 docstring 없음, 단위 노드를 plan 상태에서 직접 받음(키 재검색 없음), 줄 끝(CRLF) 보존 |
| 메인 커밋 `6c8287f`의 `e_inst_p3.py`·`e_lib_p3.py` | `run_checks.sh`가 base·head 두 판에서 같은 사본으로 잰다(gmid-light 트리의 `docs/03-analysis/gain-budget-gmid-sizing-30-module-split/scripts/`에 있는 같은 파일을 head 판에서 꺼내 씀) |
| design 30 §2.2(shim·재수출 위치·D-22), §6.2(규칙), §6.3(`MP_ARGS`), §10(IMPORT-ANY·E5) | 도구 규칙·명령 |
| `m_cards_plan.md` W-1~W-12, `m2_m9_open_items.md` O-1~O-8 | 각 MOD 예상 문제(§5) |

## 1. 만든 도구 (`_drafts/p3light/tools/`)

| 파일 | 내용 |
|---|---|
| `move.py <MODn>` | HEAD에서 `mp_core.compute_plan`(문장 키 = 바인딩 이름, `MP_ARGS` = design 30 §6.3)으로 배정을 계산하고 그 MOD 단위만 옮긴다. MOD 파일 = `mod_imports[card]` + 단위 원본 줄(바로 위에 붙은 주석 줄 포함) 바이트 그대로, docstring 없음, MOD≥8이면 번호≥7 모듈 import는 파일 끝(D-22). split 파일 = 단위 줄 삭제 + `from <MOD> import <이름 정렬>` 한 줄(앞머리 묶음 마지막 import 뒤, ACF처럼 `sys.path` 뒤면 `# noqa: E402`, SD→MOD8·9는 파일 끝). N3.10·`--keep` 밖 파일이 비면 완전 shim(docstring + `__future__` + N3.10 모듈 import 줄 + 새 재수출). 고정 D-19: `rail_declaration`·`RailDeclaration` → MOD2(plan이 다르게 내면 멈추고 알림). **멈춤**: `upward`·`cycles`·`unassigned`·`conflicts`·`import_time_high` 비지 않음, 이 card의 `import_conflicts`, card 파일 존재, 앞 card 미적용(mod_imports가 없는 MOD를 가리킴), 대상 .py가 HEAD와 다름. `reg_mismatch`는 보고만(`--strict-registry`면 멈춤). `--dry-run`, `--commit`(평문 메시지 한 커밋), `--report`. 줄 끝(CRLF) 보존 |
| `ast_check.py <base> <head>` | move/mp_core와 코드 공유 없는 독립 판정. 바뀐 파일 전체에서 D1 함수·클래스(중첩 포함) `ast.dump`(docstring 제외) 해시 다중집합 같음 / D2 중복 정의 증가 0 / D3 import 아닌 최상위 문장 다중집합 같음(docstring 포함) / D4 차이는 import 줄뿐·`import *` 0·새 파일 모듈 docstring 0 / D5 symtable 미해석 전역 이름 증가 0(옮긴 정의의 import 누락) / D6 원 파일에서 나간 이름이 새 정의 모듈에서 재수출됨 / .py 아닌 파일 변경 0 |
| `run_checks.sh <root> <base> <head> <out> [회로…]` | (1) ast_check (2) 두 판을 **같은 경로**의 임시 `git worktree`(`<out>/wt`)에 차례로 떠서 IMPORT-ANY · 전체 pytest(PT3 모양: gate `pytest_gate.ini`, `--gmid-phase=3`, junit) · E-LIB(`e_lib_p3.py`) · E-INST(`e_inst_p3.py`, 기본 `current_reuse_telescopic_ota folded_cascode`) -- 스크립트는 메인 `6c8287f` 사본을 한 번 꺼내 두 판에 같은 사본 (3) 비교: pytest id별 결과 같음, E-LIB 해시 같음, E-INST 출력 키 같음(`engine_origin`만 제외, 경로가 모두 worktree assets 안인지 따로), stdout 사본 같음(`elapsed=` 가림). 결과는 `<out>/summary.txt`에 단계마다 append. base 측정 캐시. 저장소 작업 트리·브랜치는 건드리지 않는다(worktree는 재고 지운다) |
| `mp_core.py`·`g1_core.py` | 재사용 사본(§0) |
| `rep_append.py` | 보고서 바이너리 append |

사용 순서(card 하나): `python -B move.py MODn --root <repo> --commit` → `bash run_checks.sh <repo> <이동 전 커밋> HEAD <저장소 밖 out>` → exit 0이면 다음 card.

## 2. 시험 1 -- MOD1, base 6df4bd7(조정자 알림 전 기준)

* `move.py MOD1`: plan `upward`·`cycles`·`unassigned`·`conflicts`·`import_time_high` 0, `reg_mismatch` 80(D0b 열 재생성 없음 -- 보고만), `import_conflicts` 2(MOD2·MOD9 `__future__` -- FU 전, MOD1과 무관). 배정 합계 = `m_cards_plan` r1 표와 같다(MOD1 8·MOD2 18·MOD3 82·MOD4 104·MOD5 21·MOD6 11·SD 잔류 111·MOD8 30·MOD9 16·ACF 2, 규칙 A-1 61·A-2 38·A-3 1·A-4 235·A-5 57·A-6 7·A-7 2·A-K 2).
* MOD1 8단위(SR): `GmIdLUT`·`_multilinear_interp`·`_multilinear_interp_point_multi`·`_QUERY_CACHE_MAX`(+붙은 주석 3줄)·`SemiEmpiricalGmIdLUT`·`_invq_newton`(A-5)·`build_toy_lut`(A-6)·`lut_conditions_from_npz`. `gmid_lut.py` 640줄, 머리 import `from __future__ import annotations`·`import math`·`import numpy as np`. SR 재수출 1줄(45행 `import numpy as np` 뒤). diff 641+/634−.
* `ast_check.py 6df4bd7 6b1b9b0`: PASS(def 283 = 283, 최상위 문장 217 = 217, 더해진 import 4줄뿐).
* **거부 확인(만든 판정이 실제로 거부하는지, 같은 복제본 임시 커밋)**: 몸체 토큰 하나 변경 → D1·D3 FAIL / SR에 같은 def 남김 → D1·D2·D3 FAIL / `gmid_lut.py`의 `import math` 삭제 → D5 FAIL / 최상위 대입 하나 추가 → D3 FAIL / `import *` 추가 → D4 FAIL / 메서드 docstring 변경 → D3 FAIL / 재수출 이름 하나 빼기 → **처음 판은 PASS(사각)** → D6을 더해 FAIL로 고침.
* 발견·고친 결함: (a) symtable(Python 3.14)이 주석 있는 모듈에 `__conditional_annotations__`를 만들어 D5 거짓 FAIL(MOD3·4·5·8·9 연쇄 모의) → dunder 이름 제외. (b) move.py 완전 shim 판정이 plan 노드와 다시 읽은 트리 노드를 `id()`로 비교해 **완전 shim을 한 번도 만들지 못함**(M4 TL·M8 SR·M9 DR이 옛 import를 남김) → 시작 줄로 비교하게 고침, 고친 판 M8 SR·M9 DR 완전 shim 확인. (c) 하위 bash에 `APPDATA`·`HOME`이 비면 numpy import 실패·git 사용자 미상 → run_checks가 기본값을 export, 복제본에 user 설정.

## 3. 시험 2 -- MOD1 검증 묶음 결과

**base 6df4bd7 → head 6b1b9b0(MOD1 이동)** -- `run_checks.sh`가 head 판 `folded_cascode` E-INST를 재는 중에 조정자의 중단 지시로 멈췄다. 그때까지 나온 산출물은 손으로 비교했다.
* ast_check PASS. IMPORT-ANY base 5/0, head 6/0(실패 0).
* pytest: base·head 둘 다 1114 passed·15 xfailed. test id 1129개의 결과가 하나도 다르지 않다.
* E-LIB 해시 같다(`1d2e3bf6…`).
* E-INST `current_reuse_telescopic_ota`: 다른 키는 `engine_origin` 하나뿐이고 더해진 모듈은 `gmid_lut`다. stdout 사본도 같다. `folded_cascode`는 base만 쟀고 head는 재지 못했다.

**base cb0ef86(B26-1 커밋 뒤, 조정자가 바꾼 기준) → head 444a8d8(MOD1 이동)** -- 도중에 멈췄다.
* move 결과는 6df4bd7 판과 같다: 8단위, `import_conflicts`는 MOD2·MOD9뿐, D-19 고정 위반 0. ast_check PASS.
* base 판: IMPORT-ANY 5/0, pytest 1179 passed·15 xfailed, E-LIB `c1213331…`. head 판의 pytest·E-LIB·E-INST는 중단으로 재지 못했다.

**MOD1~MOD9 연쇄 모의(cb0ef86, 이동과 ast_check만, 관찰용)**
* MOD1 → FU 대역(DR·ACF에 `from __future__` 한 줄, 스크래치에서만) → MOD2·3·4·5·6·8·9 순서로 진행했다. 모든 card에서 move exit 0, ast_check PASS, IMPORT-ANY 실패 0이다.
* 단위 수: MOD1 8, MOD2 **20**, MOD3 82, MOD4 104, MOD5 21, MOD6 11, MOD8 30, MOD9 16. MOD2에는 `rail_declaration`·`RailDeclaration`이 plan 규칙만으로 들어갔다(D-19 고정이 바꿀 것 없음).
* 완전 shim: M4에서 TL, M8에서 SR, M9에서 DR.
* 마지막 `import_layering` 발견은 2건이다: SD(7)→MOD9 import와 SD↔MOD9 순환. design D-22에서 예상한 대로이고 F2가 없앤다.
* 연쇄 마지막 상태(옛 도구 판)에서 전체 pytest를 돌렸더니 수집 오류 2건이 났다(아래 P-2).

## 4. 알게 된 문제(도구 결함은 고침, 남은 것은 card 몫)

* **P-1 FU 필요(M2·M9)**: DR·ACF에 `from __future__`가 없으면 plan `import_conflicts`가 생기고 move.py가 멈춘다. FU card(파일 머리에 한 줄)를 M2 전에 넣어야 한다.
* **P-2 완전 shim이 selftest import를 깬다(M4·M8·M9, W-1)**: `test_selftest_sizing_recipe.py:24`는 `_dc_replace`·`json`·`math`·`np`를, `test_selftest_design_report.py:24`는 `os`를, `test_selftest_topology_library.py`는 `math`를 shim에서 import한다. 모의 M9 상태에서 수집 오류 2건이 실측됐다(TL은 그 판 도구 결함 때문에 shim이 덜 비워져 드러나지 않았다). 해결은 T0 몫(test import를 출처 모듈로 바꾸는 test-only 수정)이다. `p3kit_m2_m9/t0w1_standin.py` 대역이 그 모양이다.
* **P-3 위치를 가정하는 계약 test(W-8, 실측 전 예상)**: `test_ic5` `_DOMAIN_TABLE`(M2부터), `test_dup_w_calc`(M4), `test_ts6_dead_probes`(M8)는 정의가 원 파일에 있다고 가정한다. 깨지면 PROCEDURE 2대로 보고서에 적는다. 이번 시험은 중단돼 M2 이후 pytest를 card별로 재지 못했다.
* **P-4 reg_mismatch 80**: D0b 레지스트리 열 재생성을 버려 레지스트리 열과 실제 배정이 80행 다르다. move.py는 보고만 하고 멈추지 않는다.
* **P-5 옮긴 뒤 원 파일에 빈 절 머리 주석이 남는다**(예: SR '# 1) LUT 인터페이스'). AST와 무관한 외관 문제다.
* **P-6 SHIM (c)**: 완전 shim SR·DR이 base의 `from stick_diagram import …` 줄을 남기고, 그 이름은 SD가 MOD2·3에서 재수출한다. F2 때 정리한다.
* **고친 도구 결함 3건**:
  * ast_check D5가 Python 3.14 `__conditional_annotations__`를 미해석 이름으로 잡는 거짓 FAIL을 냈다. 고쳤다.
  * move.py 완전 shim 판정이 `id()`로 비교돼 늘 false였다. 고쳐서 M4 TL·M8 SR·M9 DR이 완전 shim이 되는 것을 확인했다.
  * ast_check에 재수출 누락 사각이 있었다. D6을 추가해 이제 거부한다.
* **환경**: 하위 bash에서 `APPDATA`·`HOME`이 비면 numpy import와 git commit이 실패한다. run_checks.sh가 기본값을 export하고, 복제본에는 git user를 따로 설정했다.

## 5. 정리

조정자 중단 지시(엔진 재설계 예정, Phase 3 이동 보류 가능성)로 여기서 멈춘다. 도구 4개(move.py·ast_check.py·run_checks.sh·재사용 사본)는 `_drafts/p3light/tools/`에 남긴다. 시험 복제본 `/c/g451`은 확인 뒤 삭제했다. gmid-light와 메인 저장소는 수정하지 않았다.
