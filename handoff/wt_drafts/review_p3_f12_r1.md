# 독립 재검토 r1 -- F1 `20261002-p3-callers-update` · F2 `20261002-p3-shim-delete` r1 · 승인 초안 `20261002-p3-f1-workspaces-write-path`

검토 2026-10-02. 기준 gate `master` `4a286f0`(= 로컬 `master`·HEAD). 검토자는 초안·키트·승인 초안을 쓰지 않았다.
실제 저장소 읽기 전용(`git -C`, `set -e`) -- 시작·끝 HEAD `4a286f0`, `status --porcelain` 37줄, reflog 첫 줄 같음.
스크래치 `C:/g240`만 사용(`git -c core.autocrlf=false clone --no-local` 작업 트리에서, origin 제거, 빈 hooksPath, TMP/TEMP = `C:/g240/tmp`), 끝에 `C:/g240` 삭제.

## 0. 판정

**B 2 · S 2 · minor 7.**
* F2 r1: 경미 1건(m1)만 -- 그대로 진행 가능.
* 승인 초안: **B1**(새 행의 부수 효과 -- 사용자·메인 세션·비 gmid agent가 `workspaces/<하위>/**/*.py` 전부를 못 쓰게 됨, 사용자에게 보이지 않음), **S1**(커밋 트레일러 지시 오류).
  해시·형식·사용자 원문·D-11 순서 무관 주장은 모두 맞다.
* F1 r1: **B2**(계약 3 (가)가 '결정 필요 항목' 2 도우미에서 반드시 FAIL -- 면제 경로 없음), **S2**(판정기 계약에 모듈 객체 흐름의 fail-closed 문장 없음 -- 내 공격 4/4 속음).
  이전 검토 B1·S1~S4와 minor 14건은 모두 해소됐다(1절).

## 1. 이전 검토(review_p3_f12) 해소 확인

| 항목 | r1 판 | 판단 |
|---|---|---|
| B1 `_REQUIRED_ENGINE_IMPORT` | 계약 2 (iv) "import한 모듈 ∩ 엔진 모듈 집합 ≠ ∅", V5 ③ '비교 완화 1' | 해소 |
| S1 (a)~(d) | 3 (가) 표지 정규화·(마) 이름 없는 import·D-17 모듈 속성만·`setattr`/`delattr`/monkeypatch, 거부 입력 h1~h4 | 해소(h1~h5 재현 -- 3절) |
| S2 계약 1·4 불일치 | 역할 밖 커밋 없앰, 대상은 F1 base 하나에서 계산, 계약 7 'Change-Id 커밋들' | 해소 |
| S3 쓰기 경로 | 사용자 답 (가) + `plan_tables` 승인 초안 | 해소(단 승인 초안 B1·S1) |
| S4 앵커 줄별 규칙 | 부재·경로 5줄 / 정의 1줄 / import 1줄 | 해소(4절) |
| m1~m14 | 결정 5·6 닫힘·착수 조건 (2)(3), r1 names 키 사슬, V5 ①~⑤, TS6 순서, m6 F2 삭제 집합, m7 엔진 파일 계산, m8 unresolved, m9 착수 조건 (3), F2 m10·m11, m12 `==`, m13 인용, m14 `mk_chain_r1.sh` | 모두 반영 |

m14 확인: `mk_chain_r1.sh`를 `C:/g240/c`에서 그대로 돌려 사슬을 다시 만들었고(exit 0, F2 삭제 49·ACF 2), `f12_equiv.py`를 M9 정정판 → F1 모의에 돌린 결과가
작성자 `out/equiv_r1_f1.json`과 **summary·파일별 판정·failed 목록까지 같다**(71 · PASS 63 · FAIL 8, D-17 차이 0). (내 Python에는 numpy가 없어 `sim_m_d31`의 import 확인만 실패로 찍혔다 -- 정적 판정과 무관.)

## 2. 승인 초안 `20261002-p3-f1-workspaces-write-path`

### 맞는 것(독립 재측정)
* `target_kind: plan_tables` 전환이 맞다: `plan_tables_hash` = `read_plan_tables_text` 넷 표 + `role_paths.read_write_paths`(merge_gate 158~175행) -- 행 추가로 `7167e028…` → **`31828c5e059dd41ed7a89f4d8757c402f9f7a61340411444d8101855f0623b57`**(내 스크립트로 재계산, 같음).
  EL3·EL4(868행)는 해시가 바뀐 계획 커밋에 `target_kind == "plan_tables" and target == h_after` 기록을 요구하고, 248행이 `plan_tables`에 `diff_*` 키를 금한다. 선례 `20260921-plan-githooks-row`(쓰기 경로표 한 행, `plan_tables`, `target` = 개정 뒤 해시)와 같은 모양.
  receive 2단계(1079행)도 커밋 뒤 old 트리에서 성립. 머리 `parse_approval_header` OK.
* D-11 순서 무관: 해시만 보면 맞다 -- D-11만 `7167e028…`(N3.10은 해시 입력 밖), 행+D-11 = D-11 뒤 행 = `31828c5e…`.
* 사용자 원문: 내 비교 스크립트(jsonl 바이트 읽기, header `[F1] 쓰기 경로`)로 AskUserQuestion 1건(`toolu_01PokFaLT31S8ep6tYfPQJmx`, uuid `c5b9d12d-…`, `05:30:10.108Z`, 사이드체인 아님),
  질문 문장·선택지 3개 라벨·설명·답(`toolUseResult.answers`와 tool_result 본문 둘 다) 모두 초안 인용과 바이트 같음, multiSelect false, annotations `{}`. BOM·CRLF 없음. 작성자 `verify_approval_f1wp.py`도 다시 돌려 ALL OK.
* `allowed()`(개정 판): 16파일 모두 code-author 허용, test-author·auditor·오케스트레이터 거부. `workspaces/a/__init__.py`·`workspaces/a/conftest.py`·`workspaces/a/b/conftest.py`·`workspaces/x.py`·`**/sitecustomize.py`·`*.pth`·`__pycache__/**` = `판정 환경` 우선 사용자만. `classify` = None. pytest 수집(`pytest_gate.ini` testpaths = A/tests)·계약 test가 읽는 workspaces 하위 파일은 `.json`뿐 -- 판정 트리 영향 없음.

### B1 -- 새 행은 '16파일을 code-author에게 준다'가 아니라 `workspaces/<하위>/**/*.py` 전체를 **code-author 전용으로 잠근다**(사용자에게 보이지 않은 효과)
`overlaps_any`(role_paths 338행)가 쓰이는 세 곳 -- hook EL1(role_hooks 124행: 메인 세션·비 gmid agent는 표와 겹치는 경로만 오케스트레이터 규칙으로 판정), EL3·EL4(merge_gate 784행: 겹치면 트레일러 필수, `doc`·`user`는 겹치는 경로를 그 주체 행으로 판정) --
에서 개정 전에는 이 경로들이 '역할 밖'(누구나 쓰고 트레일러 없이 커밋)이었는데, 개정 뒤에는 실측(개정 판 `allowed`):
* 추적 `.py` **38개**(깊이 3: 22, 깊이 4: 16 -- current-reuse 32(그중 `spice/` 14)·two-stage 4·**`workspaces/verilog-rtl-workspace/desc-opt/{gen_html,launch_all}.py`** 2·…)와 앞으로 생길 모든 하위 `.py`가 code-author만 허용.
* 사용자(`Role: user` -- 맞는 행 없음 → 거부)·트레일러 없는 커밋(겹침 → 트레일러 필수 → 거부)·메인 세션·`verilog-rtl-*` 등 비 gmid agent(EL1 오케스트레이터 규칙 → 거부)가 모두 막힌다. gmid와 무관한 `verilog-rtl-workspace`도 포함.
* 추가로 `workspaces/a/b/__init__.py`(두 조각 아래 `__init__`)는 개정 전 '역할 밖' → 개정 뒤 code-author 허용(`판정 환경` 행은 `workspaces/*/__init__.py` 한 조각뿐) -- 판정 트리 밖이라 위험은 낮다.
질문 설명은 "F1 code 커밋이 16개를 함께 고칩니다. 역할 분리와 게이트 검사가 그대로 적용됩니다"뿐이었고, 초안 '범위 설명'의 '덮는 것'도 code-author 권한만 적는다. 다른 주체의 쓰기 상실은 사용자 몫(권한 설정) 결정인데 보이지 않았다 → **이 기록으로 커밋하지 말고 부수 효과를 보여 다시 확인**한다(원칙 기본안: 표를 바꾸는 쪽이 아니라 묻는 쪽 -- 행 문언이 승인 대상이므로).
질문 선택지 제안: (가) 그대로(부수 효과 수용 -- 범위 설명에 '덮는 것'으로 38파일·막히는 주체 명기) / (나) 두 gmid 작업 폴더로 좁힘(`workspaces/current-reuse-telescopic-ota-report/**/*.py`·`workspaces/two-stage-ota-report/**/*.py` 두 행 -- 해시 다시 계산, verilog-rtl-workspace 해방) / (다) (가)나 (나)에 같은 glob의 `사용자 | … | -- | 없음` 행을 더해 사용자 커밋(`Role: user`)은 계속 허용.
어느 답이든 '범위 설명'에 막히는 주체·파일 수를 적는다.

### S1 -- 커밋 지시 "오케스트레이터, 트레일러 없음"은 게이트가 거부한다
`docs/01-plan/**`·`.ai/approvals/**`는 오케스트레이터 행(626·628행)과 겹쳐 트레일러가 필수다(784행 → `judge_trailers({})` = "`Role: …`가 정확히 하나가 아니다" -- 실측). 선례 `49e5f65`(githooks 행)·최근 문서 커밋(`a5566c8`·`6c8287f`) 모두 `Role: doc`.
→ "한 커밋(`Role: doc`, Change-Id 없음)"으로 고친다.

### minor
* m2 D-11 승인 초안의 `target` 예측값 `441b80e1…`은 `compute_diff_hash`(336행)가 base·head **blob**을 쓰므로 D-11 커밋의 부모가 `f2f4d2ee…`(이 행 없음)일 때만 맞다. 이 행이 먼저 들어가면 D-11 `target`이 바뀐다(D-11 초안은 '커밋 뒤 계산'으로 이미 감쌌다). 이 초안의 '순서 무관' 문장을 "`plan_tables_hash` 기준(D-11 diff 해시는 순서에 따라 다름)"으로 한정.
* m3 '측정' 문단의 `read_write_paths` 행 수 68 → 69 확인(같음). '16개' 표현은 '대상 16, 행이 덮는 추적 `.py` 38'로(B1과 같이).

## 3. 동등 판정기 r1(`f12_equiv.py`)

### 재현
* 실제 F1 모의(M9 정정판 → F1 모의): PASS 63 · FAIL 8 -- 작성자 수치와 파일·실패 식까지 같다.
* 작성자 h1~h5 재구성(새 합성 probe `zz_h.py`: 순서용 `import sizing_recipe`, `sr` 별칭, from-import, 사슬 `sr.x = wrapped = (…)`, `setattr`, `__main__`; good = 규칙대로 -- 순서용 → MOD9(모의 MOD10 대용), D-17 → MOD4·MOD5):

| head | 판정기 |
|---|---|
| good | **PASS** |
| h1 from-import를 `__main__` 블록 뒤로 | FAIL (가) |
| h2 사슬 대입 대상 하나를 `import_module("instance_report_builder")`로 | FAIL (라)(마) |
| h2s `setattr` 첫 인자를 `import_module("design_report")`로 | FAIL (나)(라) |
| h3 순서용 import 삭제 | FAIL (마) |
| h4 `wrapped` 사슬 탈락 | FAIL (가) |
| h5 import 셋을 `if False:` 안으로 | FAIL (가) |
| `setattr` 대상에 호출자 아닌 MOD5 추가 | FAIL (나)(라) |

### 내 새 공격(합성 probe `zz_rev.py`, base = M9 정정판 + probe, good = 규칙대로 -- good PASS 확인 뒤 good 위 변이; 각 변이는 `import gmid_lut as _x`를 같은 import 묶음에 더하고 한 자리만 `_x`로 바꾼다 -- `gmid_lut`(MOD1)에는 그 이름이 없어 실행 시 깨진다)

| 변이 | 실제 동작 | 판정기 |
|---|---|---|
| A1b `vars(sr)["allocate_stack_headroom"]` → `vars(_x)[…]` | `KeyError` | **PASS(속음)** |
| A2 `helper(sr)`(함수 안에서 `m.diode_vds_window`) → `helper(_x)` | `AttributeError` | **PASS(속음)** |
| A10 `alias = sr; alias.diode_vds_window` → `alias = _x` | `AttributeError` | **PASS(속음)** |
| A3 동적 `getattr(sr, n)` → `getattr(_x, n)` | `AttributeError` | **PASS(속음)** |
| A1 `sr.__dict__[…]` | -- | good도 FAIL(모듈 정체성이 base·head에서 달라 (나)가 늘 FAIL -- 보수적, fail-closed) |
| A5 원본 읽기 `_o = sr.x`를 재수출 MOD `_cm.x`로 | 같은 객체 | FAIL (다) -- 맞음 |
| A4 D-17 '같은 값의 대입 문장 여럿'(`sr.x = _w` / `_cm.x = _w`, 계약 2 (iii)이 허용) | 같음 | **FAIL (가) -- 거짓 FAIL** |

### B2 -- 계약 3 (가)는 '결정 필요 항목' 2 도우미에서 기본안대로 고쳐도 반드시 FAIL한다(면제 경로 없음)
8 FAIL의 성격:
* T0 미적용 selftest 3(`ast_same`·`from_same`): 모의 산물. F1 base에서는 T0가 비엔진 이름을 출처 import로 바꿔 두고 F1은 엔진 이름만 바꾸므로 PASS가 된다 -- 착수 조건 (2)가 막는다. **수용**.
* 동적·부재 도우미 5(`test_d_delete_dead`·`test_d_delete_telescopic`·`test_dup_w_calc`의 `_import_sizing_recipe()`, `test_ts6_dead_probes.py:229`, `test_dup_kcl_edges.py:35` `_sd()`): 작성자는 '모의가 기본안 미적용'이라 했지만 **기본안을 적용해도 4/5는 FAIL이다**. 실측(F1 모의 위에 기본안대로 고침):
  `test_dup_w_calc`(두 이름 모두 MOD4 -- 목적지 하나라 import 호출 문자열만 바꿈) → PASS, `test_ts6_dead_probes`(부재 단언을 '모든 N3.10 모듈'로 -- 루프) → **FAIL (가)(나)**.
  `test_d_delete_*`는 레지스트리 넷이 MOD5(`_METRICS_REGISTRY`)·MOD4(나머지 셋)로 갈라져 도우미가 이름을 받아야 하고, `_sd()`는 SD 잔류(`kcl_series_union`)·삭제(`_kcl_and_matching_edges`) 이름을 함께 읽어 같은 이유로 문 모양이 바뀐다
  (판정기의 모듈 식 인식은 `import_module/_import/__import__(상수)`뿐이라 `_sd()` 같은 도우미 호출은 표지가 되지 않는다). 계약 3 (가)가 빼는 것은 '1 (c)(d)의 줄'뿐이므로 auditor는 F1을 FAIL로 내야 한다 -- equivalence card가 자기 계약을 만족할 수 없다(이전 B1과 같은 꼴).
  **8 FAIL은 equivalence card의 기대 상태로 수용할 수 없다**: 3은 착수 조건으로 0이 되지만 4는 계약 문언을 고쳐야 0이 된다.
고칠 문언(원칙 기본안 -- 질문 아님): 계약 3 (가)(나)의 제외에 "**'결정 필요 항목' 2 도우미 def와 그 반환 모듈을 쓰는 줄**(auditor가 F1 base에서 목록화 -- 모의 5파일)"을 더하고, 그 줄은
(i) V5 ⑤ 승인 diff 대조, (ii) 정적 확인 -- 도우미가 이름마다 돌려주는 모듈 = interface card '이름 → 정의 모듈' 표(R-DEF), 부재 단언 범위 = N3.10 '파일' 열 전부, (iii) 계약 6 (a) PT3에서 그 test id 결과 같음(모두 수집되는 계약 test다)으로 판정한다. '재현할 수치'의 FAIL 8은 "3 = T0 몫(착수 조건 (2)), 5 = 계약 3 제외 대상(위 (i)~(iii))"으로 적는다.

### S2 -- 판정기 계약에 '모듈 객체가 속성·상수 이름 밖으로 흐르는 자리'의 fail-closed 문장이 없다(내 공격 4/4 속음)
3 (가)는 모듈 식을 표지 하나로 지우고 (나)는 '모듈 식 속성·getattr류 상수 이름'만 푼다. 그래서 모듈 객체가 인자로 넘어가거나(A2), 다른 이름에 대입되거나(A10), `vars()`로 읽히거나(A1b), 동적 `getattr`(A3)로 쓰이면
그 모듈을 아무 MOD로 바꿔도 (가)~(마)가 모두 참이다. probe·workspaces는 V1·IMPORT-ANY가 실행하지 않으므로 F9가 막으려던 '조용한 파손' 모양 그대로다.
현재 위험 크기(실측 -- M9 정정판에서 대상 71파일의 엔진 모듈 별칭 Load 중 '속성 값·getattr/hasattr/setattr/delattr(상수)' 밖 자리 스캔): 6파일 -- 위 B2의 도우미 5 + `test_restore_plan_functions.py:59` `_import` 도우미(판정기가 import 호출로 인식). 모두 PT3가 실행하는 계약 test라 지금 F1에서 조용한 파손은 없다.
그러나 F1 base(M10·T1·T0·B26-1 뒤)에서 새로 생길 수 있고 auditor 독립 구현이 같은 구멍을 가질 수 있다 → 계약 3에 한 문장: "엔진 모듈 객체가 속성 접근·getattr류 상수 이름·D-17 대입/호출 밖으로 쓰이는 자리(인자, 다른 이름 대입, `vars()`/`__dict__`, 반환, 동적 이름)가 있는 파일은 (가)~(마) PASS로 판정하지 않는다 --
F1 base에서 목록화해 B2의 (i)~(iii) 경로로 판정하고, 그 목록 밖에서 head에 새로 생기면 FAIL". '거부해야 할 입력'에 A2(모듈 객체 인자 전달)·A3(동적 getattr 모듈 교체) 두 줄을 더한다.

### minor
* m4 계약 2 (iii)이 허용하는 '같은 값의 대입 문장 여럿'을 3 (가)가 정규화하지 않는다(A4 거짓 FAIL -- 계약 문언 3 (가)도 '한 문장 안 첫 모듈 속성 대상 자리'만 접는다). 또 값 식이 문장마다 다시 평가되면(`… = lambda …` 두 번) 계측 래퍼가 둘이 된다.
  기본안: 2 (iii)에서 '같은 값의 대입 문장 여럿'을 빼고 사슬 대입 하나로 고정(호출형은 같은 Name 값 인자만 허용) -- 문언 둘을 맞춘다.
* m5 D-17 기대 집합('그 이름을 전역으로 읽는 F1 base 엔진 모듈')은 MOD끼리 `from … import`로만 읽는다는 전제다. 어떤 MOD가 다른 MOD를 `import X as y; y.name`으로 부르면 정의 모듈이 집합에서 빠져 계측을 잃는다. 모의 M9 정정판의 MOD 파일에 엔진 모듈 `import`/`import_module` 0(analog-grammar 동적 import 1 -- 엔진 아님).
  착수 조건 (3)에 "F1 base MOD 파일의 엔진 모듈 속성 접근 0 -- 아니면 정의 모듈을 집합에 더하고 묻는다"를 붙인다.

## 4. 앵커 5줄 'N3.10 MOD 파일 전부가 있다' -- 약화 아님(확인)

`4a286f0` 원문: `test_d_delete_dead.py:74`·`test_d_move_tests.py:73`의 `_REQUIRED_ENGINE_FILES`는 `_engine_files()` = `sorted(A.glob("*.py")) + [run_harness]`의 이름 집합에 들어 있어야 하는 비공허 전제(155·105행),
`test_d_delete_telescopic.py:117`은 `assert_engine_scope_present(files)`의 같은 전제, `test_df35_harness_paths.py:206`·`test_ts6_probe_relocate.py:528`은 'ASSETS에 엔진이 있다'는 전제다. 부재·경로 판정 자체(glob 스캔)는 바뀌지 않는다.
'SR 파일 하나가 있다' → 'N3.10 '파일' 열 10개가 모두 있다'는 F1 base·병합본·F2 뒤 모두 참이고, 각 줄이 지키려던 뜻(정의 위치 파일이 판정 범위 안에 실재)을 현재 정의 위치로 옮긴 것이다. SR 존재 요구가 빠지는 것은 F2가 SR을 지우는 이상 필연이고, 정의는 그 10개 안에 있다(D-31 배정 403 전부 MOD·SD·ACF).
→ **넓힘으로 보는 것이 맞다**(V5 ③ '넓힘' 줄별 기재 그대로). 단 `test_d_delete_dead`·`test_d_move_tests`는 같은 튜플에 `stick_diagram.py`가 남으므로 '바꾼다'는 SR 원소만 -- 초안 문언과 같다.

## 5. F1 `approval` 머리에 `plan_tables` 승인 id를 넣을지

게이트 사용처 실측: spec card `approval` 목록은 `merge_gate.gate_change_ok`(722~740행)만 읽고, 그것도 `gate_change: yes`일 때뿐이다(F1은 `no` -- 형식 검사 외 효과 0). 판정 기록 `approvals`(schema 205행)는 `rule6_dates_approvals`(470행)가 '파일 존재·머리 파싱'만 본다.
선례: `20260921-gate-output-utf8`(githooks 행 승인으로 풀린 card)은 `plan_tables` 승인을 머리에 넣지 않았고, 다중 `approval:` 선례는 있다(`20260929-probe-engine-dup` 3줄 등).
실제 의존(그 행이 gate `master` 계획에 있어야 code 커밋이 들어감)은 EL1·EL3·EL4 경로 검사가 이미 강제한다 -- 머리 목록은 그 의존을 강제하지 못한다.
**권고: 넣는다**(`approval: 20261002-p3-f1-workspaces-write-path` 둘째 줄, 판정 기록 `approvals`에도). 효과는 기록용 + rule6이 판정 기록 적재 때 그 승인 파일 존재를 확인하는 약한 검사뿐이고 비용 0. 단 B1 재확인 결과로 승인 id가 바뀌면 그 id로.

## 6. F2 r1

* m1 '작성 전 실측' 2 '이름 충돌' 줄이 편집 중 깨졌다: `` (`git grep "p3_shim_delete|p3sd_"` 0건, `dd60db6`·`4a286f0`)\|p3sd_"` 0건, `dd60db6`) `` -- 뒤쪽 중복 조각을 지운다(재측정: `4a286f0`에서 0건, 확인).
* 나머지 r1 변경(base 문언·삭제 49·`present` 10·E3b 49줄·`reg_check` exit 0·red-green r1 해시)은 F1 r1 사슬과 맞는다.

## 7. 재현 명령(스크래치, 삭제됨)

```bash
git -c core.autocrlf=false clone -q --no-local <repo> C:/g240/r; (origin 제거·빈 hooksPath) checkout --detach 4a286f0
python -B _drafts/p3kit_f12/verify_approval_f1wp.py C:/g240/r/tools/gates C:/g240/r            # ALL OK
python -B my/quote.py ; python -B my/allow.py      # 내 원문 대조·해시 4조합·allowed 행렬(before 68행 / after 69행)
bash _drafts/p3kit_f12/mk_chain_r1.sh C:/g240/c <repo>     # f6a6564(M9 정정) 1bee19c(F1 모의) 679408b(F2 모의)
python -B _drafts/p3kit_f12/f12_equiv.py C:/g240/c/r f6a6564 1bee19c out.json --d17 C:/g240/c/out/f1sim_names.json   # 71·63·8 = 작성자 json
# 기본안 도우미: 103d91b(test_dup_w_calc PASS, test_ts6_dead_probes FAIL)
# 공격: zz_rev base 30f4e87/base2, good cfa2fe8 PASS, A1b 5549a68·A2 8524545·A10 e5062ea·A3 5f6484f PASS(속음), A4 6e73947 FAIL, A5 983d56f FAIL
# h 재구성: zz_h base 402fa10, good a972a71 PASS, h1 90b0cae·h2 f9ba915·h2s 8123349·h3 88c3633·h4 3053597·h5 de6332c·d362c22 FAIL
```
