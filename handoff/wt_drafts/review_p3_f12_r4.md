# 독립 재검토 r4 -- F1 `20261002-p3-callers-update` r4 · 판정기 시제품 `f12_equiv.py` r4

검토 2026-10-06. 검토자는 초안·키트를 쓰지 않았다(S1 좁힌 문언의 원 제안은 이 검토 계열 r3 2절).
대상: `draft_p3_f1.spec.md`(r3 = `*.pre-r4.md`), `p3kit_f12/f12_equiv.py`(r3 = `f12_equiv.pre-r4.bak`).
실제 저장소 읽기 전용(`git -C`, `set -e`). 시작·끝 HEAD `7243f28`, `status --porcelain` 38줄·md5 `76eea762…` 같음, reflog 첫 줄 같음.
스크래치 `C:/g293`만(TMP/TEMP = `C:/g293/tmp`), 끝에 삭제.

## 0. 판정

**B 0 · S 0 · minor 3.**
S1 문장은 r3 2절 권고 문언의 요소를 빠짐없이 담았다(점 경로 전체 비교 포함). 좁힌 규칙은 T1/T3/T7/T8 bad와 h1~h5·A1b/A2/A3/A10·zz_rev·T5를 여전히 거부하고, good 변형은 PASS다.
F1 모의 결과는 PASS 62 · LISTED 6 · FAIL 3이고 승인 목록은 5단위다. 저자가 근거로만 넘긴 회귀도 이번에 **직접 다시 돌렸다**(123 판정). 저자 수치와 모두 같다.
minor 셋은 '⑤ 제시 방법'의 문구 문제다(gate V5 동작과 어긋나는 표현 둘, 정의되지 않은 해시 하나). 진행해도 된다.

## 1. 사슬 -- 두 가지로 만들어 비교

* **A(저자 방식)**: `mk_chain_r1.sh` 스크래치 사본. `4a286f0`에서 시작하고, G1 설치기만 `g1_kit/install_proto.py.pre-35.bak`로 바꿨다.
  커밋 = M9 정정 `6ad3475`(F1 모의 base), F1 모의 `6381278`, F2 모의 `d173b3e`.
* **B(현재 설치기)**: `7243f28`에서 시작하고 현재 `install_proto.py`를 썼다. 원 스크립트는 1단계(D-11 토큰)에서 `assert t.count(o) == 1`로 멈춘다.
  `7243f28` 계획서에는 이미 D-11이 들어 있기 때문이다(`29d2fc2`). 그래서 사본에서는 1단계를 '이미 있으면 건너뜀 + 빈 커밋'으로 바꿨다.
  커밋 = `0ef102c`, `b24819c`, `96ffcff`.
* **결과 차이 없음.** 두 사슬의 M9 정정·F1 모의·F2 모의에서 `assets` 트리 해시가 같다(`6614ba2…`·`df0724f…`·`0806c27…`).
  `workspaces` 트리와 `tools/gates/pytest_gate.ini`(`5d89b98…`)도 같다. 다른 것은 `tools/` 트리뿐이다(card 35 `mutate_changed.py`·redteam·G1 설치판).
  `f1sim_names.json`은 바이트가 같다. r4 F1 판정(승인 5단위·무승인)은 71파일 `files` 전체가 A=B로 같다. gate V5(`7243f28` `weakening_diff.py`)도 두 사슬에서 FAIL 10, `diff_hash e079e9dc…`로 같다.
  공격 123판정은 사슬 A에서만 돌렸다. 판정기 입력(위 트리들)이 같으므로 B에서도 같다.
* 참고: 원 `mk_chain_r1.sh`는 지금 그대로 실행되지 않는다. 현재 설치기는 `4a286f0`에서 exit 1로 멈추고, `7243f28`에서는 D-11 assert에 걸린다. 다시 실행하려면 r4 '작성 전 실측' 5d처럼 사본에서 고친 내용을 적어 두어야 한다(m3).

## 2. S1 문장 -- 권고 문언과 대조(계약 3 (바), 148~151행)

| r3 2절 권고 요소 | r4 문장 |
|---|---|
| 같은 이름이 파일 안(base·head 각각)에서 서로 다른 엔진 모듈에 묶이면 | 같음(굵게) |
| 묶임 = `import X [as a]`, 상수 엔진 이름 import 호출 결과의 `Name` 대입 | 같음(`import_module/_import/__import__` 명시) |
| 스코프·횟수 무관 | '스코프와 횟수는 따지지 않고' |
| **모듈은 점 경로 전체로 비교** | '모듈은 점 경로 전체로 비교한다' -- 있음 |
| 그 이름을 읽거나 묶는 단위와 묶는 자리를 목록 단위로 | 같음(+ '최상위 import 문이 단위 밖이라도', 묶는 자리 변경도 (i) 승인 대상) |
| 한 엔진 모듈에만 묶인 이름은 어느 스코프에서 몇 번 묶여도 (나)에서 그 모듈로 푼다 | 같음(이유 괄호 포함) |
| head에만 새로 생기면 FAIL | 같음 |

바이트 단위로 같지는 않다(문장을 셋으로 나누고 순서를 바꿨다). 다만 빠지거나 넓어진 절은 없다.
착수 조건 (3)(38~42행)과 계약 8 ⑤(182~183행)도 같은 문언(점 경로 전체)으로 바뀌었다. '참고로만' 2파일은 목록이 아니라고 명시했다.
r3 넓은 판의 흔적('두 번 이상'·'최상위가 아닌')은 이력 문장(159·259~260·363~364행, 5d 'r3 판' 열)에만 남아 있다. 규칙 문장에는 없다.
시제품: `multibound`는 `len({모듈}) > 1` 한 줄이다. 모듈은 첫 성분(`split(".")[0]`)이고, 이 사실은 docstring과 실측 262행에 적혀 있다(엔진에 패키지가 없어 결과는 같다 -- r3 m2' 처리됨).

독립 스캔(판정기 코드를 쓰지 않음. 엔진 = 그 트리 `A/*.py` 줄기 전부. 비엔진 추적 `.py` 330 = 345 − 엔진 15):

| | F1 모의 base | F1 모의 head |
|---|---|---|
| 서로 다른 엔진 모듈에 묶인 이름 | **0** | **0** |
| 한 모듈·함수 안/여러 번(참고) | 2파일 -- `test_restore_plan_functions.py` `sr` 113·120·127·134·140(모두 `sizing_recipe`), `test_ts6_dead_probes.py:229` `module` | 1파일(`sr` 5곳 모두 `gmid_lut`) |

착수 조건 (3) 괄호와 '현재 목록' S1 줄(모의 0)이 맞다.

## 3. 측정 -- 사슬 A, 판정기 r4 / r3(`pre-r4.bak`) / r2(`pre-r3.bak`), 같은 승인 목록 `out/approved_v5_5_mock.txt`(5단위)

### F1 모의(`--d17` 포함)

| 판정기 | 승인 5단위 | 승인 없음 |
|---|---|---|
| **r4** | **PASS 62 · LISTED 6 · FAIL 3**(FAIL = selftest 3 `ast_same`·`from_same`) | 62 · 1 · 8(도우미 5파일 `listed_changes_approved`) |
| r3 | 62 · 5 · 4(+`test_restore_plan_functions.py` `listed_changes_approved`) | 62 · 0 · 9 |
| r2 | 62 · 6 · 3 | 62 · 1 · 8 |

r4와 r2는 71파일의 판정·실패 키·목록 단위가 파일마다 같다(두 승인 조건 모두).
`test_restore_plan_functions.py`는 LISTED이고 목록 단위는 `['_import']`, 바뀐 목록 단위는 []다. 5단위 목록 = `_import_sizing_recipe` 3파일 · `_sd` · `test_sizing_recipe_module_has_no_l_role_multipliers_attribute`. **저자 수치가 재현된다.**

### 공격·회귀(base = F1 모의 base + 합성 파일, head = F1 모의 + 변이, `--only`, 승인 5단위)

| 입력 | r4 | r3 | r2 |
|---|---|---|---|
| h-good(`probes/zz_attack.py`) | PASS | PASS | PASS |
| h1 · h4 · h5 | FAIL `ast_same` | 같음 | 같음(h5 r2는 '세지 않음 · 제외' -- 아래) |
| h2 · h2b | FAIL `attr_same`·`d17_same`·`nameless_ok` | 같음 | 같음 |
| h3 | FAIL `nameless_ok` | 같음 | 같음 |
| zz_rev good / A1b·A2·A10·A3(`probes/`) | FAIL `listed_collected` / FAIL `listed_changes_approved`·`listed_collected` ×4 | 같음 | 같음 |
| test_zz_rev good / A ×4(`contracts/`) | LISTED / FAIL `listed_changes_approved` ×4 | 같음 | 같음 |
| test_zz_rev good / A ×4(`tests/tools/`, m3) | FAIL `listed_collected` / FAIL `…approved`·`listed_collected` ×4 | 같음 | LISTED / `…approved`만 |
| **T1 bad** | **FAIL `multibind_new_none`** | FAIL `…approved`(+probe `listed_collected`) | PASS(속음) |
| **T3 bad** | **FAIL `multibind_new_none`** | 같음 | PASS(속음) |
| **T7 bad** | **FAIL `multibind_new_none`** | 같음 | PASS(속음) |
| **T8 bad** | **FAIL `multibind_new_none`·`attr_same`** | 같음 | FAIL `attr_same` |
| **T1·T3·T7·T8 good** | **PASS ×4** | FAIL ×4(넓은 판) | PASS |
| T6(base가 이미 섞임 SR/SD → head 둘 다 GSE) | FAIL `listed_changes_approved`(+probe `listed_collected`) | 같음 | FAIL `attr_same` |
| T5(head에만 `contracts/test_zz_new.py`) | FAIL `file_set_same` | 같음 | 판정 안 됨(예외) |

T 행은 probe(`tests/probes/zz_t.py`)와 contracts(`tests/contracts/test_zz_t.py`) 두 자리에서 같은 결과다(probe 쪽 r3·T6에만 `listed_collected`가 더해진다).
합성 파일은 h·A 계열이 저자 `out/att_r1`·`out/att_r2` 원본 그대로다. T 계열은 이번에 새로 썼다(최상위·함수 자리에서 `sr.diode_vds_window`·`sr.allocate_stack_headroom`을 읽고, 두 이름은 모의에서 `gmid_sizing_engine`에만 있다).
- h5 r2: 첫 병렬 실행이 중간에 끊겼고, 이어서 돌릴 때 이 칸은 다시 돌리지 않았다. r2 판정은 r2 시절 기록 `out/att_r2/r2.H.h5.txt`(FAIL `ast_same`)를 따른다. r4·r3는 이번 실측이다.
- T5 r2: r2 판정기가 파일 집합 검사 전에 예외(`list index out of range`)로 끝났다. r2 판에 파일 집합 검사가 없었다는 r3 m2의 지적과 맞는다.

**결론**: 좁힌 규칙 때문에 다시 열린 공격은 없다. r3와 판정이 달라진 것은 진짜 동등한 good 4종(→ PASS)과 F1 모의 `test_restore_plan_functions.py`(→ LISTED, 승인 5단위)뿐이다.
저자 5d '회귀' 항목은 '부분집합이라 같다'는 논증으로 넘어갔다. 실측해 보니 논증대로 h·A·zz_rev·T5 판정이 r3와 키 단위까지 같다.

## 4. '⑤ 제시 방법' -- gate V5 기계(`7243f28` `tools/gates/weakening_diff.py`)와의 정합

gate V5 동작:
- 발견 단위는 (경로, 단위 = 함수 qualname / `<module>` / `__main__`, 패턴)이다.
- 승인 대조는 head 트리 `.ai/approvals/*.md` 중 `target_kind: diff`인 기록의 `target:` 해시 집합이다.
- 그 해시는 **발견이 있는 경로만**(정렬해서) `경로\tbase blob\thead blob` 줄로 만든 sha256 **하나**(커밋 단위, 파일 blob 수준)다.

F1 모의 실측(base `6ad3475` → `6381278`): FAIL, 발견 10 = conftest 무조건 승인 1 + 리터럴 변경 9.
9의 내역은 `_import_sizing_recipe` ×3, `test_lut_conditions_*` ×5, `test_sizing_recipe_module_has_no_l_role_multipliers_attribute` 1이다(5파일). `diff_paths` 6, `diff_hash e079e9dc…`.
`_sd`(`test_dup_kcl_edges.py`)는 모의에서 바뀌지 않아 발견이 없다.

맞는 점:
- (1) 실제 F1 base에서 계산하고 모의와의 차이를 먼저 적는다는 원칙이 맞다.
- (3) ⑤-a/⑤-b 구분이 맞다.
- (5) F1 base 커밋과 적용 문언을 남기는 것이 맞다.
- "②와 같은 발견을 두 번 세지 않는다"는 취지도 맞다. ⑤-a의 바뀌는 4단위는 그 자체가 ② 9건 중 4건이다.
- '모의 5 = r2 판과 같음'도 맞다(3절 표).
- 계약 8 ① 해시가 test 커밋 diff 해시라는 서술은 gate와 맞는다.

### minor
* **m1 -- "V5 발견 합계는 줄 기준 한 번만 센다"(⑤ (4))**: gate는 줄이 아니라 (경로·단위·패턴)으로 센다. 한 단위에서 리터럴 줄이 여럿 바뀌어도 발견은 1이다.
  '발견(경로::단위·패턴) 기준 한 번'으로 고쳐야 승인 질문의 수가 gate 출력(`findings` 길이)과 맞는다. 모의라면 ⑤-a의 바뀌는 4단위는 ② 9건 안에 이미 들어 있고, 합계는 10이다.
* **m2 -- "단위 diff 해시"(⑤ (2)·(5))가 정의되지 않았다**: gate가 내는 해시는 커밋 단위 `diff_hash` 하나뿐이다. 단위별 해시는 어디에도 식이 없다.
  그래서 auditor가 (바) (i) 'diff = 승인 diff'를 독립으로 재현할 수 없다. 둘 중 하나로 정한다.
  - (가) 단위 해시의 식을 적는다. 예: base·head 단위 `ast.get_source_segment` 원문 쌍의 sha256.
  - (나) 단위 해시를 빼고 '실제 diff 줄(전·후 원문)'과 gate `diff_hash`(승인 기록 `target`)만 쓴다.
  추가로 한 문장이 있어야 한다. **S1 묶는 자리(최상위 `import X as sr`)의 변경은 V5 발견이 아니다**(별칭 이름은 `Constant`가 아니다). 그래서 그 파일에 다른 발견이 없으면 gate `diff_hash` 경로 집합에 들지 않는다.
  이 경우 승인 구속은 범위 설명의 원문 인용과 (바) (i) auditor 대조뿐이다. ⑤-b는 모의 0이라 지금 영향은 없다.
* **m3 -- 재현 경로**: '작성 전 실측' 5d는 G1 설치기를 `pre-35.bak`으로 바꿨다고만 적었다. `mk_chain_r1.sh` 본문은 아직 `../g1_kit/install_proto.py`와 `4a286f0`을 가리킨다.
  스크립트에 설치기 경로 인자를 두거나 5d에 사본 수정 두 가지(설치기 · 7243f28 시작 시 D-11 단계 건너뜀)를 적어 두면, 다음 검토자가 같은 시행착오를 반복하지 않는다. 이번에 확인한 대로 결과는 어느 쪽이든 같다.

## 5. 재현(스크래치 `C:/g293`, 삭제됨)

```bash
cp -r p3kit_f12 g1_kit C:/g293/kitA/ ; cp g1_kit/install_proto.py.pre-35.bak C:/g293/kitA/g1_kit/install_proto.py
bash C:/g293/kitA/p3kit_f12/mk_chain_r1.sh C:/g293/cA <작업 트리>        # 6ad3475 6381278 d173b3e
# kitB: 7243f28 시작 + D-11 단계 '있으면 건너뜀·빈 커밋' + 현재 install_proto.py → 0ef102c b24819c 96ffcff
python -B scan.py C:/g293/cA/r <rev> out.json                          # 2절 독립 스캔
python -B {f12_equiv.py|pre-r4.bak|pre-r3.bak} C:/g293/cA/r <M9F> <F1> o.json --d17 cA/out/f1sim_names.json [--approved approved_v5_5_mock.txt]
run_par.sh / resume.sh                                                 # 공격 커밋(plumbing) 41 head × r4·r3·r2 = 123 판정, xargs -P 6
python -B weakening_diff@7243f28 --root C:/g293/c{A,B}/r --base <M9F> --head <F1>   # FAIL 10 · e079e9dc…
```
