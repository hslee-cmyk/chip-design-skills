# 독립 재검토 r3 -- F1 `20261002-p3-callers-update` r3 · 판정기 시제품 `f12_equiv.py` r3 · 승인 초안 `20261002-p3-f1-workspaces-write-path` r3

검토 2026-10-02. 기준 gate `master` `4a286f0`(= 로컬 HEAD). 검토자는 초안·키트·승인 초안을 쓰지 않았다(단, S1 문장의 원 문언은 이 검토 계열 r2가 제안한 것이다 -- 아래 2절).
실제 저장소 읽기 전용(`git -C`, `set -e`) -- 시작·끝 HEAD `4a286f0`, `status --porcelain` 37줄·md5 `dcc7b56b…`, reflog 첫 줄 같음.
스크래치 `C:/g269`만(사슬 = `mk_chain_r1.sh C:/g269/c <작업 트리>` -- 작업 트리에서 `-c core.autocrlf=false clone --no-local`, origin 제거, 빈 hooksPath, TMP/TEMP = `C:/g269/tmp`), 끝에 `C:/g269` 삭제.
사슬: M9 정정 `dff61a3` = F1 모의 base, F1 모의 `d88eb87`, F2 모의 `1e755a2`(해시는 시각 따라 다름 -- 저자 `9cb99e4`/`d9662f4`).

## 0. 판정

**B 0 · S 1 · minor 2.**
r3는 r2의 S1·m2·m3·m4·m1을 모두 반영했고 저자 수치는 전부 재현된다. 다만 **S1 문장 자체가 넓다**(r2 검토가 제안한 문언의 '또는 최상위가 아닌 스코프' 몫) --
한 엔진 모듈에만 묶인 이름까지 목록 단위로 돌려 V5 ⑤를 5 → 10으로 늘리고, 진짜 동등한 변경(T1·T3·T7·T8 good)을 FAIL/멈춤으로 만든다.
'서로 다른 엔진 모듈에 묶인 이름'으로 좁혀도 T1·T3(와 새 변형 T7·T8)이 모두 FAIL로 남는다(시제품 실측). **좁힌 문언으로 고치고 진행**을 권고한다(질문 아님 -- 사용자 승인 전 초안 안의 선택, r2 판정기보다 엄격).

## 1. (1) 셈 -- 독립 스캔(F1 모의 base `dff61a3`, 추적 `.py` 345 전수)

내 스캐너(판정기 코드 미사용): 엔진 모듈 = base `A/*.py` 줄기 전부(판정기 ENG보다 넓음), 묶임 = 엔진 모듈 `import` 문 + **첫 인자가 엔진 이름 문자열 상수인 모든 호출**(함수 이름 무관)의 결과를 `Name`에 대입.

| 셈 | base `dff61a3` | head `d88eb87` |
|---|---|---|
| 최상위가 아닌 스코프의 엔진 `import` **문** 별칭 | **0** | 0 |
| 최상위가 아닌 스코프의 import **호출 대입** | **2파일** -- `test_restore_plan_functions.py` `sr = _import("sizing_recipe")` 113·120·127·134·140행(5함수), `test_ts6_dead_probes.py:229` `module = importlib.import_module("sizing_recipe")` | 1파일(`test_restore_plan_functions.py`, 5곳 모두 `gmid_lut`) |
| r3 문언(두 번 이상 또는 비최상위) | 2파일(`sr`, `module`) | 1파일(`sr`) |
| **서로 다른 엔진 모듈 ≥2에 묶인 이름** | **0** | **0** |

→ 저자 정정이 맞다. r2 검토의 '0'은 import 문만 센 값이었다(r2 4절 S1 '현재 노출' 문장 정정). 대상 71 밖 0도 같음.

## 2. (2) S1 문장의 범위 -- 원칙과 시제품 측정

### 왜 넓은가
T1의 원인은 '파일 하나짜리 별칭표가 사용 자리의 스코프를 풀지 않는다'인데, 그 결함이 **판정을 바꾸는 것은 같은 이름이 서로 다른 모듈에 묶일 때뿐**이다.
한 이름의 엔진 바인딩이 (base·head 각각) 모두 같은 모듈이면, 사용 자리가 어느 바인딩으로 풀리든 같은 모듈이고 별칭표의 답과 같다 -- 스코프를 풀 필요가 없다.
`test_restore_plan_functions.py`의 `sr`은 base 5곳 모두 `sizing_recipe`, head 5곳 모두 `gmid_lut` -- 모호함이 없고 (나)(다)가 기계적으로 판정한다(r2 판정기가 그렇게 PASS 판정했다).
r3 문언은 이것을 목록 단위로 돌려 ① V5 ⑤ +5(그 5 diff는 `_import` 문자열 리터럴 변경이라 ②에도 이미 보인다 -- 사용자가 같은 줄을 두 번 승인), ② 수집되지 않는 probe·workspaces에 함수 안 `import X as m` 하나만 있어도 착수 조건 (3)·(바) (iii)으로 **멈추고 묻게** 만든다(모의 0이지만 M10·T1·T0 뒤 F1 base에서 생길 수 있음).
이 넓음은 r3 저자가 아니라 r2 검토 문언('…또는 최상위가 아닌 스코프에서 묶이면')에서 왔다 -- r3는 그 문언을 정확히 구현했다.

### 좁힌 문언(제안)
> **같은 이름이 파일 안(base·head 각각)에서 서로 다른 엔진 모듈에 묶이면**(묶임 = 엔진 모듈 `import X [as a]`, 상수 엔진 이름 import 호출 결과의 `Name` 대입 -- 스코프·횟수 무관, 모듈은 점 경로 전체로 비교) 그 이름을 읽거나 묶는 단위와 그 이름의 묶는 자리를 목록 단위로 둔다.
> 한 엔진 모듈에만 묶인 이름은 어느 스코프에서 몇 번 묶여도 (나)에서 그 모듈로 푼다(어느 바인딩으로 풀려도 같은 모듈). **head에만 서로 다른 모듈 묶음이 새로 생기면 FAIL**.

### 시제품 측정(`f12_equiv.py` r3의 `multibound` 조건 한 줄만 `len({모듈}) > 1`로 바꾼 사본 `eq_alt`)
F1 모의(승인 목록 r2 5단위, `--d17` 포함): **PASS 62 · LISTED 6 · FAIL 3**, 71파일 판정·실패 키·목록 단위가 r2 판정기 결과와 **파일마다 같음**(`test_restore_plan_functions.py` 목록 단위 = `_import` 1). 승인 없이 62/1/8(r2와 같음).
r3 판(같은 사슬): 10단위 → 62/6/3, 5단위 → 62/5/4(그 파일 `listed_changes_approved`), 승인 없이 62/0/9 -- **저자 수치 모두 재현**.

공격(base = `dff61a3` + 합성 파일, head = `d88eb87` + 변이, `--only`, 승인 목록 5단위; probe = `tests/probes/zz_t.py`, contracts = `tests/contracts/test_zz_t.py`. 이름 `diode_vds_window`·`allocate_stack_headroom`은 모의에서 `gmid_sizing_engine`에만 있음):

| 입력 | 모양 | r2 | r3 | 좁힌 문언 |
|---|---|---|---|---|
| T1 bad | 최상위 `import gmid_lut as sr`, 함수 안 `import gmid_sizing_engine as sr` | PASS(속음) | FAIL `listed_changes_approved`(+probe `listed_collected`) | **FAIL** `multibind_new_none` |
| T3 bad | 함수 안이 `sr = importlib.import_module("gmid_sizing_engine")` | PASS(속음) | FAIL | **FAIL** `multibind_new_none` |
| T7 bad(새) | 최상위 바인딩 없음, 두 함수가 각각 `import_module("gmid_lut")`·`("gmid_sizing_engine")` | PASS(속음) | FAIL | **FAIL** `multibind_new_none` |
| T8 bad(새) | 최상위 `import gmid_sizing_engine as sr` + 함수 안 `global sr; import gmid_lut as sr` | FAIL `attr_same` | FAIL | **FAIL** `multibind_new_none`·`attr_same` |
| T6(새) | base가 섞임(최상위 SR, 함수 안 SD) → head 둘 다 MOD4 | FAIL `attr_same` | FAIL `listed_changes_approved` | **FAIL** `listed_changes_approved`(base 목록 단위) |
| T1·T3·T7·T8 good | 모든 바인딩을 정의 모듈 하나로(진짜 동등) | PASS | **FAIL**(contracts `listed_changes_approved`, probe `+listed_collected` = 멈춤) | **PASS** |

양쪽 모두 probe·contracts 두 자리에서 같은 결과(표는 한 줄로 합침). → 좁힌 문언은 T1/T3 공격을 다시 열지 않고, r3가 거부하던 진짜 동등 변경만 PASS로 되돌린다.
남는 우회는 '엔진 바인딩으로 인식되지 않는 묶음'(예: `sys.modules[…]`, 비상수 호출) -- 이것은 (바)의 탈출 자리·(가) 문장 비교 몫이고 두 문언에 같다.

### 고칠 곳(좁힌 문언 채택 시)
계약 3 (바) S1 문장과 '이유'(그대로 유효), 착수 조건 (3) 괄호(측정 대상 = 서로 다른 모듈 묶음 파일 수 -- 모의 0; 함수 안 같은 모듈 묶음 2파일은 참고로만), '현재 목록' S1 줄(모의 0 → `test_restore_plan_functions` 1), 계약 8 ⑤(모의 승인 목록 5 그대로), '거부해야 할 입력' T1 줄(T7 한 줄 추가 권장),
'작성 전 실측' 5c 표의 good 행(→ PASS), `f12_equiv.py` `multibound` 조건. 문언을 r3 그대로 두기로 하면 아래 4절 방식으로 10단위를 보인다.

## 3. (3) r2 지적 반영 확인

* **S1(T1·T3)**: r3 판 FAIL(위 표) -- 저자 5c와 같다(`<bind sr>`·`inner` 목록, probe `listed_collected`).
* **m2 파일 집합**: head에만 있는 `tests/contracts/test_zz_new.py` -- r2 `absent`(무계수) → r3 **FAIL `file_set_same`**. 계약 3 첫 줄 문장 확인.
* **m3 수집 규칙**: chain head `tools/gates/pytest_gate.ini` = `testpaths = skills/analog-gmid-design/assets/tests`, `norecursedirs = tools`(python_files 없음 → pytest 기본) -- 판정기는 head 트리에서 읽는다.
  `tests/tools/test_zz_rev.py` good: r2 LISTED → r3 **FAIL `listed_collected`**, A1b·A2·A10·A3: r3 `listed_changes_approved`·`listed_collected` 4/4. `tests/contracts/test_zz_rev.py`는 good LISTED·A 4/4 FAIL로 r2와 같음(회귀 없음).
  `tests/conftest.py`에 `collect_ignore`·`pytest_ignore_collect` 없음(`pytest_collection_modifyitems`는 xfail 표시·섞기만 -- 수집 집합 불변) -- 문언의 '수집' 정의가 맞다.
* **m4**: 실측 6 끝에 '기계화하지 않은 것'(LISTED = (i) 이름 수준만, diff 대조·(ii) 미기계화) 확인.
* 다중 바인딩 스캔 수치(base 2·head 1·head 신규 0, 행 번호 113·120·127·134·140·229): 1절 독립 스캔과 같다.
* T0 모의 selftest PASS 3은 이번에 다시 돌리지 않았다(r3 변경은 selftest 3파일에 다중 바인딩이 없어 영향 없음 -- 1절 스캔 0).

## 4. (4) m1 인용과 F1 V5 ⑤ 제시 방식

### m1 -- 바이트 대조
세션 jsonl 12642행(0-기준 12641) = uuid `8e9a12fb-1940-4634-a484-4dac99aef542`, `type: assistant`, `2026-10-02T09:14:47.244Z`, `isSidechain: false`, content 블록 = `text` 1개.
승인 초안의 둘째 ```` ```text ```` 펜스 내용이 그 text의 줄 하나와 **바이트 같음**(앞 공백 2칸 포함), 승인 초안 BOM·CR 없음. 둘째 답 `08:18:56.717Z` 존재.
'답 뒤 고지(동의가 아니다)'로 표시됐고 '결정 뒤의 알림이라 동의 근거가 아니다'를 명시 -- 맞다.
'13081줄까지 사용자 텍스트 0': 13081행 = `10:09:42Z`(r3 파일 19:11 KST 직전) -- 그 시점까지 맞음.
* **minor m1'** -- 이후 13286행 `10:52:13Z` 사용자 텍스트 "응, 질문 다시 올려"가 있다(바로 앞 `10:46:58Z` 보고의 'T0-V4 질문 … 다시 올리겠습니다'에 대한 답 -- 이 승인 범위와 무관). 승인 기록을 커밋할 때 '세션 기록 끝까지' 문장을 커밋 시점 행 번호로 다시 재거나 '이 r3 작성 시점(13081행)까지'로 한정 표현을 유지한다. 같은 `10:46:58Z` 보고는 V5 5 → 10을 알렸는데 이것도 이 승인(write path)과 무관하다.

### F1 test 커밋 때 V5 ⑤ 승인 질문에 보일 것(어느 문언이든 공통)
1. **수치의 출처**: 목록은 auditor가 **실제 F1 base**에서 계산한 것을 보인다(모의 10/5는 예보일 뿐) -- 실제 수가 모의와 다르면 차이와 이유를 먼저 적는다.
2. **단위마다 한 줄**: `경로::단위` · 목록 사유(탈출 자리 종류 / 도우미 호출 / S1 다중 바인딩) · 그 test 커밋에서의 **실제 diff 줄(전·후 원문)** · 단위 diff 해시 -- 계약 3 (바) (i)이 'diff = 승인 diff'로 대조하므로 승인 대상은 이름이 아니라 그 diff다.
3. **묶음 구분**: ⑤-a 탈출 자리·도우미 5단위(`_import_sizing_recipe` 3파일, `_sd`, `test_sizing_recipe_module_has_no_l_role_multipliers_attribute`)와 ⑤-b S1 단위를 나눠 보인다.
4. **r3 문언 유지 시 ⑤-b(5단위 `test_lut_conditions_*`)**: 각 단위의 바뀐 줄은 `sr = _import("sizing_recipe")` → `sr = _import("<R-DEF 모듈>")` 한 줄뿐이고 **그 줄은 ② import 호출 문자열 리터럴 변경(모의 9 -- 5파일)에 이미 들어 있다**는 것을 함께 적어, 같은 줄을 두 번 세지 않게 한다(V5 발견 합계는 줄 기준 한 번).
   그리고 '왜 목록인가'를 한 문장으로 -- "함수 안에서 엔진 모듈을 묶는 이름은 판정기가 스코프를 풀지 않으므로 기계 판정 대신 사람 승인으로 둔다(5곳 모두 같은 모듈이라 모호함은 없다)". 승인 = 5 diff 그대로 승인.
5. **좁힌 문언 채택 시**: ⑤ = ⑤-a 5단위뿐이고 그 5 리터럴 변경은 ②로만 보인다(그리고 (나)(다)가 기계 판정). 질문 문안에 '모의 5 = r2 판과 같음'만 적으면 된다.
6. 승인 기록 범위 설명에는 ① 그 목록(단위·diff 해시), ② 계산한 F1 base 커밋, ③ 적용 문언(r3 넓은 판 / 좁힌 판)을 남긴다.

## 5. minor

* **m1'** 위 4절 -- 승인 초안 '세션 기록 끝까지' 문장의 시점 한정(커밋 때 재측정).
* **m2'** 좁힌 문언을 채택하면 '모듈'은 점 경로 전체로 비교한다고 적는다(지금 시제품은 첫 성분 `split(".")[0]` -- 엔진은 패키지가 없어 영향 0이지만 auditor 독립 구현의 모호함 제거).

## 6. 재현(스크래치, 삭제됨)

```bash
bash p3kit_f12/mk_chain_r1.sh C:/g269/c <작업 트리>                    # dff61a3 d88eb87 1e755a2
python -B my/scan.py C:/g269/c/r <rev> out.json                        # 1절 독립 스캔(base·head)
python -B eq_r3.py C:/g269/c/r dff61a3 d88eb87 o.json --d17 C:/g269/c/out/f1sim_names.json [--approved ap10|ap5]   # 62/6/3 · 62/5/4 · 62/0/9
python -B eq_r2.py … --approved ap5     ; python -B eq_alt.py … [--approved ap5]   # 62/6/3 (r2 = alt, 71파일 같음) · alt 무승인 62/1/8
bash my/mkc.sh ; python -B my/runatt.py # 공격 커밋(plumbing) 29종(head) × r2·r3·alt = 87 판정
python -B my/quote2.py                  # m1 바이트 대조 + 이후 사용자 텍스트 탐색
```
