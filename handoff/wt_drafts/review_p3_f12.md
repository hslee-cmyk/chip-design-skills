# 독립 검토 -- F1 `20261002-p3-callers-update`(equivalence) · F2 `20261002-p3-shim-delete`(red-green)

검토 2026-10-02. 기준 gate `master` `4a286f0`(= 로컬 `master`, HEAD). 검토자는 두 초안·키트를 쓰지 않았다.
실제 저장소 읽기 전용(`git -C`, `set -e`) -- 시작·끝 HEAD `4a286f0`, `status --porcelain` 37줄, reflog 첫 줄 같음.
스크래치 `C:/g224`만 사용(격리 복제본 `--no-local`, origin 제거, 빈 hooksPath, TMP/TEMP = `C:/g224/tmp`), 끝에 `C:/g224` 삭제.

## 0. 판정

**B 1 · S 4 · minor 14.** F2는 경미 사항만 있다(그대로 진행 가능). F1은 B1·S1~S4를 고쳐야 card 커밋 전 조건이 된다.
`parse_spec_card`(gate `4a286f0` `tools/gates/role_paths.py`): 두 초안 모두 OK(id·phase 3·evidence_type·gate_change no·approval `20260930-30-module-split-design`).

## 1. 재현

* **배정(D-31 plan)**: `plan_d31.py`를 `4a286f0` + G1 시제품 설치 복제본에서 다시 돌림(엔진은 `dd60db6..4a286f0` 변경 0).
  `F12_STMTKEY=hash` → 작성자 `out/plan_d31h.json`과 배정 (단위 → MOD, 규칙) **완전 같음**(403, A-4 229, A-5 64, MOD 8·18·82·102·21·11·SD 110·32·17, upward·cycles 0).
  키 미지정(names) → `out/plan_d31.json`과 완전 같음(upward 1·cycles 1).
* **사용자 답 판(names 키 + D-11 (가) MOD1 토큰)**: 계획 521행에 `_QUERY_CACHE_MAX`를 더한 복제본 커밋에서 names 키 → upward·cycles·unassigned·conflicts 0, MOD 8·18·82·**104**·21·11·SD **111**·**30**·**16**.
  hash 판(카드 모의)과 MOD가 다른 문장 3개: `_COMPENSATION_REGISTRY`·`_L_ROLE_TARGETS`(MOD8 → MOD4), `INSTANCE_TOP_FIELDS`(MOD9 → SD 잔류 -- SD 재수출에서 빠짐). → minor m2.
* **모의 트리(M1~M9·F1·F2)는 다시 만들지 않았다**: 사슬에 키트에 없는 손 단계가 있다(`3f61526` M9 정정, `2fd53cc`의 `test_restore_plan_functions.py` `_import` 4곳 보정, `dd60db6`용 G1 설치 판 차이 --
  현재 `install_proto.py`는 `dd60db6`에서 `앵커 mc print: 0개`로 멈춤). 작성자 수치 PT3·E-INST·equiv 변이 3건은 재현하지 못했다(m14).
* **판정기 공격(아래 S1)**: 작성자 `f12_equiv.py`를 실제 트리(`4a286f0` + G1 시제품)의 합성 probe 한 파일에 돌림 -- 변이 5개 중 **4개가 PASS(속음)**.

## 2. B

**B1 -- 계약 2 (iv)가 `test_d_move_tests.py:69`에서 equivalence test-first를 불가능하게 한다.**
`_REQUIRED_ENGINE_IMPORT = {"regression_runner": "sizing_recipe"}`는 `assert required_import in imported_modules(source)`(229·237행)로 **`A/tests/tools/regression_runner.py`가 그 모듈을 import함**을 단언한다.
regression_runner는 code-author 경로(K)이고 F1이 반드시 바꾼다(17행 `from sizing_recipe import (…)` -- E3 대상). 계약 2 (iv)대로 값을 'R-DEF 정의 모듈 하나'로 바꾸면
T만 얹은 F1 base(regression_runner는 아직 SR만 import)에서 FAIL → 계획 680행 "equivalence면 base에서 통과 확인"·V2 실패. 값을 그대로 두면 병합본에서 FAIL(작성자 모의 PT3 실측 그대로).
한 값으로 두 트리를 통과할 수 없다(regression_runner는 여러 MOD에서 읽으므로 '정의 모듈 하나'도 정의되지 않는다).
기본안(원칙: 판정 뜻 보존 -- '도구가 엔진 정의를 베끼지 않고 엔진을 import한다'): 이 앵커를 **"import한 모듈 ∩ 엔진 모듈 집합 ≠ ∅"**(엔진 모듈 집합 = 계획 N3.10 표 파일 줄기 ∪ 그 트리에 있는 shim 파일 줄기)로 바꾼다 --
base·병합본 모두 통과, 복사 금지 단언(234~235행)은 그대로. 'sizing_recipe 고정'에서 '엔진 모듈 아무것'으로 넓히므로 V5 승인 목록에 이름으로("비교 완화 1: `_REQUIRED_ENGINE_IMPORT`").

## 3. S

**S1 -- 계약 3 판정기(정규화 AST + 해석 + 정의 모듈 + D-17)가 속는다(실측 4/5).** 계약 3 (가)는 엔진 import 문을 **지운** 뒤 비교하고, (나)(다)는 이름·출처만 본다 -- import의 위치·존재가 판정에서 사라진다.
합성 probe(`tests/probes/zz_attack.py`, base `0b9f173`) 변이, `f12_equiv.py` 결과:

| 변이 | 실제 동작 | 판정기 |
|---|---|---|
| h1 `from sizing_recipe import spec_fingerprint`를 `if __name__ == "__main__": main()` **뒤**로 | 스크립트 실행 시 `NameError` | **PASS** |
| h2 `setattr(sr, "load_derived_bounds", …)` → `setattr(importlib.import_module("design_report"), …)` | 계측 대상 모듈이 바뀜(F8 그 고장) | **PASS** |
| h3 이름을 읽지 않는 `import sizing_recipe`(순서 고정용) 삭제 | `test_restore_plan_functions.py:54` 모양 -- 순서 보장 소실 | **PASS** |
| h4 `sr.x = wrapped = (…)` → `sr.x = (…)`(사슬의 지역 대상 탈락) | `wrapped` `NameError` | **PASS** |
| h5 import를 `if False:` 블록 안으로 | 정의 안 됨 | FAIL(새 `if` 노드 때문) |

h1·h3은 계약 문언 자체의 구멍(지우는 정규화), h2·h4는 계약 2 (iii)·3 (라)의 범위 구멍이다. probe·workspaces는 V1·IMPORT-ANY가 실행하지 않으므로(IMPORT-ANY는 `__main__` 블록을 돌리지 않는다) 이 변이들은 F9가 막으려던 '조용한 파손'이다.
고칠 문언(설계 질문 아님 -- 계약 강화):
(a) (가) 정규화는 엔진 import 문을 **지우지 않고 그 자리에 표지 문장**으로 바꾼다(같은 자리의 연속한 엔진 import 묶음 = 표지 하나 -- 1→N 분할 허용, 묶는 이름 집합은 (나)가 본다). 새 별칭 import는 원래 import 바로 뒤에 둔다(계약 2 (ii)).
(b) 이름을 읽지 않는 엔진 import(현재 `test_restore_plan_functions.py:54` 1건)의 목적지 규칙을 계약 2에 둔다 -- 기본안: N3.10 MOD10 진입 모듈 import(트리의 엔진 전부를 먼저 묶는다는 원래 목적; 모의 `f12_f1sim.py` 규칙 (5)와 같음).
(c) D-17 표지는 **모듈 속성 대상만** 바꾸고 그 밖의 대상(`Name` 등)은 남긴다.
(d) 계약 2 (iii)·3 (나)(라)에 `setattr`/`delattr`/`monkeypatch.setattr`(모듈 식 첫 인자 + 상수 이름)을 넣는다 -- design §7.2가 "Phase 3 시작 때 대입문과 `setattr` 두 형태로 다시 잰다"고 했고, B26-1 계수 test(T0 계약 10)가 `monkeypatch.setattr`를 들인다. 실측 3의 'setattr 0'은 B26-1 미병합 판이다.
'거부해야 할 입력'에 h1·h2·h4 세 줄을 더한다(판정기 자기 점검).
(작성자 시제품 (나)는 `set(base) <= set(head)` 부분집합인데 계약 문언은 "같다" -- auditor 몫이지만 m12로 적음.)

**S2 -- 계약 1과 계약 4가 서로 맞지 않는다.** 계약 4: 역할 밖 커밋을 F1 test 커밋 전에 넣고 "F1 base는 그 커밋 뒤 master, 계약 1의 대상 계산은 그 커밋을 포함한 트리에서". 그러면 16파일은 이미 importer가 아니라 대상 집합에서 빠지는데,
계약 1 끝은 "F1 병합본(과 계약 4의 역할 밖 커밋)이 바꾼 파일 집합 = 이 집합"이라 16파일만큼 어긋나 FAIL이 정해진다. 또 그 커밋은 F1 판정 전에 gate `master`에 들어가 있어(역할 밖 커밋은 역할 커밋과 같은 push 불가 -- 05 §9.2-4) auditor가 FAIL을 내도 되돌릴 경로가 card에 없다.
고칠 문언: 대상 계산 기준 = 역할 밖 커밋의 **부모**, 계약 3·7을 그 커밋에 먼저 재고 PASS일 때만 push(실패 시 처리 문장). 단 S3의 답이 (가)면 이 계약 전체가 사라진다.

**S3 -- 역할 밖 커밋 기본안은 design 05의 '역할 밖' 정의 밖이다(사용자 질문).** 기계적으로는 통과한다: `workspaces/<하위>/*.py`는 N3.12.2 어느 행 glob에도 맞지 않아(`workspaces/*.py`는 한 조각, `workspaces/*/__init__.py`만 판정 환경) EL1이 즉시 통과시키고
EL3 §8.2-1·EL4 §9.2-3이 트레일러 없는 병합 아닌 커밋을 통과시킨다. 그러나 05 §8.2-1이 그 통과의 근거를 "**gmid 밖 작업**(review31 N-01)"으로 적었고, F1의 16파일 갱신은 gmid card 몫이다(UD-1 답 원문 "추적 파일은 전부 F1에서 갱신").
이 경로를 쓰면 오케스트레이터가 spec card·목적지 표(interface card)·구현을 모두 쥐고 게이트는 그 커밋을 검사하지 않는다(작성자≠검증자 위반 모양). 선례도 반대다 -- analog-grammar 파일이 쓰기 경로표에 없을 때 B26-1은 역할 밖 커밋을 쓰지 않고
게이트 공백(B36, `plan_tables` 승인)으로 미뤘다(계획 DF-19 행). 쓰기 경로표 개정은 `plan_tables` 승인 = 사용자 몫이라 오케스트레이터가 정할 수 없다 → **질문 QA**(아래 5절). D-17 대입 2줄(`diagnose_cmrr_cmfb.py:24`·`diagnose_cmrr_psrr.py:20`)도 이 16파일 안이다.

**S4 -- 계약 2 (iv) 'R-DEF로 바꾼다'가 앵커 7줄 중 5줄에서 정의되지 않는다.** R-DEF는 "그 test가 판정하는 **이름**의 정의 파일, 정확히 하나"인데:
`test_d_delete_dead.py:74`·`test_d_delete_telescopic.py:117`(지운 이름의 **부재** 판정 범위 -- 정의 0), `test_d_move_tests.py:73`(옮긴 이름이 엔진에서 사라짐 -- 정의 0), `test_df35_harness_paths.py:206`(하네스 ASSETS 경로 판정 -- 이름 없음),
`test_d_move_tests.py:69`(B1 -- 이름 여럿). 정의되는 것은 `test_dup_w_calc.py:56`(`size_transistor`·새 함수)과 `test_ts6_probe_relocate.py:528`(진입 함수 이름을 고르면)뿐이다. test-author가 소스를 못 읽으므로 계약이 줄마다 정해야 한다.
기본안(원칙 '범위를 좁히지 않는다'): 부재·경로 앵커는 `"sizing_recipe.py"`를 **계획 N3.10 표의 MOD 파일 전부가 있다**로 바꾼다(`stick_diagram.py`는 그대로 -- 넓힘, F1 base·병합본 모두 참), 528행은 같은 규칙 또는 MOD10 진입 함수 R-DEF, 69행은 B1. 모두 V5 승인 목록에 줄별로.

## 4. minor

* m1 **W-1·D-11 답 반영 안 됨**: F1 '결정 필요 항목' 5·6이 아직 "Q2 답이 (가)면 …"·"Q1 답에 따라" 조건문이다. 두 답 모두 (가)(user_decisions 2026-10-02) -- 5는 "W-1 (가)로 T0가 닫음"으로, 계약 2 (i)의 '엔진 밖 출처' 문장에
  "F1 base에서 shim 경유 비엔진 이름 읽기 0(T0) -- 아니면 멈춤"을 착수 확인으로(그렇지 않으면 `import numpy as np` 새 줄이 계약 3 (가)에서 FAIL -- 비엔진 import는 정규화가 남긴다). 6은 "D-11 (가)로 닫힘".
* m2 **모의 배정이 승인 키와 다르다**: 모의는 `F12_STMTKEY=hash`(시제품 키)인데 D0a 계약 2 키는 바인딩 이름이고 D-11 답은 그 키 위의 MOD1 토큰이다. 1절 재현대로 3문장이 다르고, SD 재수출은 58 → 57·F2 삭제 50 → 49(SD가 `INSTANCE_TOP_FIELDS`를 정의로 가짐)일 것이다.
  '재현할 수치'에 "hash 키 판 -- 승인 판(names + D-11 (가))과 3문장 다름"을 적고 F2 수치도 같은 주석.
* m3 **V5 '발견 10'은 기대 목록이 아니다**: 모의는 앵커·TS6·결정 2 도우미를 고치지 않은 판이다. 실제 V5 승인 목록 = conftest 1(무조건) + import 호출 문자열 9(5파일) + 앵커 7줄(S4·B1 규칙별) + TS6 비교 대상 1(QB) + 결정 2 도우미(`_import_sizing_recipe` 3파일 동적·`test_ts6_dead_probes.py:229` 부재 → 모든 N3.10·`test_dup_kcl_edges.py:35` `_sd()`).
* m4 **TS6 병합 순서 (1)은 도달 불가**: #2(`d4-delete-unwired`)는 `phase: 4`이고 계획 991행 "이전 Phase DoD PASS"라 Phase 3 DoD(F2 뒤) 전에 병합될 수 없다. 두 경우 처리는 해롭지 않으나, 질문은 F1 V5 때 **한 번**만 하고 #2 D1은 F1 답을 따르는 무동작으로 둔다(#2 계약 8 61행이 이미 그렇게 적음 -- 두 card 문언은 정합).
* m5 Q3 (다) 선택지 설명에 "이후 어떤 코드 변경으로도 이 test는 FAIL하지 않는다(고정된 두 이력 blob 대조)"를 명시 -- 판정 약화 크기를 사용자가 보게(QB 문안 반영).
* m6 ACF 삭제 집합(F2 계약 2)의 reader가 F1 계약 1 (b)에 없다 -- 지금 0이지만 '정의 하나'로 (b)를 "F2 계약 2의 SD·ACF 삭제 집합"으로. E3b는 SD만 보므로 ACF reader는 DoD도 못 잡는다.
* m7 계약 1 "엔진 파일 `A/*.py` 제외 -- M card가 이미 MOD에서 직접 import": split 밖 엔진 파일(`topology_to_markdown.py:29` `from stick_diagram import load_topology`)은 M card가 안 고친다. 지금은 SD 잔류 이름뿐이라 무해 -- 제외 대신 같은 식으로 계산(대상이면 code-author 경로).
* m8 결정 3(정의 없는 이름) '같은 문장 중 N3.10 번호 최대 모듈'은 임의 규칙(동작 같음은 맞다). 계약 3 (다)에 "정의 없는 이름은 (다) 대상 아님, (나)에서 base·head 모두 unresolved"를 적는다.
* m9 D-17 정밀 정의('base에서 덮어쓴 모듈 단위의 F1 base 위치')와 승인 원문("`binding_origin`으로 찾은 호출자 모듈 전부")이 모의 14/14 같지만, 실제 F1 base에서 다르면 멈추고 묻는다는 문장을 계약 2 (iii)에.
* m10 F2 계약 5 `present 9(MOD10 = M10 card가 더해 10)` → F2 head에는 M10이 있으므로 **10**(계약 13 표 E0과 맞춤).
* m11 F2 '작성 전 실측' 5의 `reg_check.py` 절 제목 확인은 지금 잴 수 있다 -- `4a286f0` 판은 정의를 `assets/*.py` glob으로 모으고 절 제목은 `### … (N)` 개수 형식만 본다(파일 존재 대조 없음으로 보임). 모의 F2 head에서 exit 코드를 적어 두면 착수 확인이 줄어든다.
* m12 작성자 판정 시제품 (나)가 부분집합 비교 -- 계약 문언("같다")과 다름. auditor 독립 구현 몫이나 '재현할 수치' PASS 63에 영향 가능.
* m13 design §7.1 v5 B행: `test_b34_grammar_explicit.py`는 V3 인벤토리 조건이라 F1도 `<MOD>.<이름>(…)` 속성 호출 모양을 유지해야 한다 -- 계약 2 (ii)가 사실상 지키지만 근거를 인용해 test-author가 `from MOD import n`으로 바꾸지 않게.
* m14 키트에 모의 사슬(`3f61526`·`2fd53cc`) 생성 스크립트가 없다(손 정정 2곳) -- 독립 재현 불가. 재현할 수치가 '관찰'임을 적었으므로 경미.

## 5. 작성자 제기 항목별 판단

| 항목 | 판단 |
|---|---|
| design 누락 F1 대상 -- 앵커 7줄·6파일 | 7줄은 모두 design §7.1 B행에 **있다**(`:74`, `:108-117`, `:69·73`, `:206`, `:56`, `:528`). design 누락은 TS6 `668-673` 하나(계약 1 (d)) -- design 정정 목록 처리 맞음. 단 처리 규칙은 S4·B1 |
| 다중 목적지 별칭 34 | 원칙 기본안(식 자리를 이름별 정의 모듈로) 타당 -- 질문 아님. m13 인용 추가 |
| workspaces 16파일 + 역할 밖 커밋 | **사용자 질문 QA**(S3). 게이트는 통과시키나 design 05 §8.2-1 '역할 밖 = gmid 밖'과 B36 선례에 어긋남 |
| 이미 깨진 `diagnose_cmrr_cmfb` import | 기본안 타당(깨진 상태 유지, design 20 §5.4-3 선례) -- 질문 아님, m8 |
| ACF 임시 재수출 `_as_set`·`_theta_evidence_for_pair` | 기본안 '지운다' 타당(WP-14, §2.2와 같은 규칙, reader 0) -- 질문 아님, design §8 F2 행 사실 갱신. m6 |
| D-11·W-1 정합 | 내용은 정합, 문언이 답 전 상태(m1), 모의 키 불일치(m2) |
| TS6 (다) 두 병합 순서 | F1·#2 문언 정합. 순서 (1)은 도달 불가(m4). 질문은 QB 한 번 |
| V5 승인 필요(10건) | 범주는 맞고 수는 아님(m3). 승인 목록에 B1·S4 규칙별 줄 포함 |

## 6. 사용자 질문(진짜 사용자 몫 2건)

**QA -- F1 쓰기 경로(S3, `plan_tables` 승인 여부)**
* header: `[F1] 쓰기 경로`
* question: "[F1] shim 삭제 전에 고쳐야 하는 추적 파일 중 workspaces 하위 폴더 진단 스크립트 16개(current-reuse 12·two-stage 4, 덮어쓰기 계측 2줄 포함)는 계획 쓰기 경로표의 어느 역할에도 없습니다. 게이트상으로는 '역할 밖' 커밋으로 넣을 수 있지만 설계는 역할 밖을 gmid 밖 작업용으로 정했고, analog-grammar(B36)도 같은 공백을 표 개정으로 미뤘습니다. 어떻게 할까요?"
* 선택지:
  1. **"(가) 쓰기 경로표에 행 추가 (Recommended)"** -- "계획 N3.12.2에 code-author의 `workspaces/*/**/*.py` 행을 더하는 판정 표 개정을 승인받고, F1 code 커밋이 16개를 함께 고칩니다. 역할 분리와 게이트 검사가 그대로 적용됩니다."
  2. "(나) 오케스트레이터 역할 밖 커밋" -- "F1 test 커밋 전에 오케스트레이터가 트레일러 없는 커밋으로 고치고 F1 auditor가 같은 판정기로 잽니다. 표는 그대로지만 구현을 오케스트레이터가 하고 게이트는 그 커밋을 검사하지 않습니다."
  3. "(다) 사용자가 직접 수정" -- "F1이 정한 목적지 표와 바꿀 모양을 드리면 세션 밖에서 직접 고칩니다. F1 판정 전에 들어가 있어야 합니다."

**QB -- TS6 비교 test(F1 V5, Phase 4 #2 D1과 같은 질문 -- 한 번만)**
* header: `[F1] TS6`
* question: "[F1] shim 삭제 전에 tests/tools/derive_achievable_bounds.py의 `import sizing_recipe as sr`(와 sr. 속성 줄)를 바꿔야 하는데, TS6 이동 계약 test(test_moved_tool_matches_base_except_path_lines)는 지금 도구가 2026-09-23 이동 때와 경로 줄 밖에서 같기를 요구해 실패합니다. 어떻게 할까요?"
* 선택지:
  1. **"(다) 이동 커밋끼리 대조 (Recommended)"** -- "test가 지금 도구 대신 이동 커밋(9d6800e)의 도구를 원본(939f926)과 비교합니다. '이동이 경로 줄만 바꿨다'는 검증은 남지만, 이후 어떤 도구 변경으로도 이 test는 실패하지 않습니다(Phase 4 첫 card도 같은 규칙)."
  2. "(가) 기준선에 import 치환 반영" -- "비교 기준을 '이동 때 원본 + F1의 import 치환'으로 바꿉니다. 치환 밖 줄은 지금처럼 그대로여야 하고, 도구를 고치는 card마다 기준을 다시 고칩니다."
  3. "(나) 허용 줄에 import 줄 추가" -- "경로 줄 정의에 shim 모듈 import 줄과 그 속성 참조 줄을 더합니다. 단순하지만 그 줄들의 다른 변경도 통과시키는 완화입니다."
  4. "(라) 비교 test 은퇴" -- "이동 검증은 2026-09-23 판정 기록에 남아 있으므로 이 test를 지웁니다. 가장 간단하지만 판정 하나가 사라집니다."

그 밖(B1·S1·S2·S4·minor)은 원칙 기본안으로 card 문언을 고칠 일이고 사용자 질문이 아니다. B1·S4의 test 판정 변경은 F1 test 커밋 뒤 V5 승인(design §9.2 '뒤에 올 승인')에 줄별로 든다.

## 7. 재현 명령(스크래치, 삭제됨)

```bash
git clone -q --no-local <repo> C:/g224/r; git -C C:/g224/r remote remove origin; git -C C:/g224/r checkout --detach 4a286f0
python -B _drafts/g1_kit/install_proto.py C:/g224/r            # installed 4 -> 커밋 a976b09
F12_STMTKEY=hash python -B _drafts/p3kit_f12/plan_d31.py --root C:/g224/r --rev a976b09 <MP_ARGS>   # = out/plan_d31h.json
python -B _drafts/p3kit_f12/plan_d31.py --root C:/g224/r --rev <a976b09 + 계획 521행 _QUERY_CACHE_MAX 토큰> <MP_ARGS>   # names + D-11 (가)
# S1: base 0b9f173(합성 probe) -> h1 20b54bc / h2 581813c / h3 e65576f / h4 1ffaaef / h5 f13b6ec
python -B _drafts/p3kit_f12/f12_equiv.py C:/g224/r 0b9f173 <h> out.json --d17 d17.json   # h1~h4 PASS, h5 FAIL
```
