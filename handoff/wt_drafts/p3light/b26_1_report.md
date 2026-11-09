# B26-1 (20260930-b26-rail-accessor-set) 가벼운 절차 적용 보고

작업 장소: C:/Users/HSLEE/Documents/Todoc/fpga/gmid-light, 브랜치 phase3-light, base 6df4bd7.

## 1. 적용

- test 커밋 `90eedb2`: `git diff 6df4bd7 main-repo/role/test/20260930-b26-rail-accessor-set`(끝 212f76a, 10파일 +980/-89, 전부 `assets/tests/` 아래)를 그대로 `git apply --index`. 적용 뒤 인덱스가 212f76a 트리와 같음 확인(diff 0). 내용 수정 없음.
  - test 브랜치 커밋: 61751ab(새 파일 test_b26_rail_accessor.py), c247a76(계약 12 기존 test 입력 갱신, P9 시그니처 기대 갱신 U5), 212f76a(s015·s016 tmp topology -- dispute 해소).
- code 커밋 `cb0ef86`: role/code 끝 e92e6b8의 base는 c247a76(212f76a 아님). `git diff c247a76 e92e6b8 -- docs/03-analysis skills` = stick_diagram.py, sizing_recipe.py, function-registry.md(3파일 +163/-94). 제외: `docs/02-design/disputes/20260930-b26-rail-accessor-set.md`(dispute, 212f76a로 해소). `git diff 212f76a e92e6b8`에 보이는 test_selftest_sizing_recipe.py 차이는 212f76a의 역방향일 뿐이라 가져오지 않음.
  - 이 diff는 `_drafts/b26_1_k1v0/K1v0.diff`와 index 줄 외 동일.
  - function-registry.md는 엔진 소스는 아니지만 code-author 산출물(함수 정본표 갱신, 같은 커밋 규칙)이라 code 커밋에 포함.

## 2. 전체 pytest (head cb0ef86)

명령: `C:\Python314\python.exe -m pytest skills/analog-gmid-design/assets/tests --gmid-phase=3 --gmid-strict= -q -p no:cacheprovider -rfEx` (clone 루트에서).
결과: **1179 passed, 15 xfailed, 0 failed** (pytest 132.12s, 벽시계 134s). exit 0.
xfail 15개는 모두 기존 Phase 표식(IC1·IC2·IC4·IC6~IC11 Phase 4/6a/6b/6c, s051·s054·s157 I-C11 two_stage_ota stage1_out KVL Phase 4) -- B26-1과 무관, base부터 있던 것.

### 실패 분류
실패 0건 -- (a)(b)(c) 분류 대상 없음. 이 단계에서 test를 고친 것은 없다.

### 약화/변경 (test-author 커밋 212f76a까지에 이미 들어 있던 것 -- 그대로 가져옴, 이번 작업에서 추가로 고친 줄 없음)
test diff(6df4bd7..90eedb2)에서 지워진 판정 문장 3줄, skip/xfail 추가 0, 허용오차 확대 0(새 approx는 전부 새 test의 rel=1e-9):
- `tests/contracts/test_dup_kcl_edges.py` (P9 계약 2): `-    assert list(sig.parameters) == ["netlist", "matching_pairs"]` -> `["netlist", "matching_pairs", "rails"]` + rails 키워드 전용·기본값 없음·annotation RailDeclaration 판정 추가. 근거: spec card 계약 4, 사용자 승인 U5.
- `tests/contracts/test_dup_kcl_edges.py` (P9 계약 3): `-    assert list(sig.parameters) == ["transistors", "matching_pairs"]` -> `["transistors", "matching_pairs", "rails"]` + 같은 rails 판정. 근거 같음(U5).
- `tests/contracts/test_b34_grammar_explicit.py`: `-    assert stick_diagram.refine_differential_and_mirror_relations(fx) is None` -> `rails=rail_declaration({"supply_nets": ["vdd","gnd"]})`를 넘긴 같은 `is None` 판정(계약 12 rails= 입력 갱신, 판정 불변).
- 그 밖: s015·s016 fixture에 tmp topology(`supply_nets` 선언) 입력 추가(212f76a, dispute 결정 -- 판정·기대값 불변), 계약 4 함수 호출부에 `rails=` 입력 추가(SD selftest 49·SR selftest 2·probes 4·P9 2·b26pre 5·B34 11+4).

## 3. E-INST·E-LIB (base 6df4bd7 vs head cb0ef86)

스크립트: 메인 6c8287f에 들어온 `docs/03-analysis/gain-budget-gmid-sizing-30-module-split/scripts/e_inst_p3.py`·`e_lib_p3.py`(clone에도 같은 경로로 있음). base·head를 clone의 임시 worktree `/c/g450/base`·`/c/g450/head`에 떠서 실행(clone 작업 트리 오염 없음).

spec card가 예정한 출력 변화(계약 8): `load_topology` meta에 새 키 `"rails"`가 생기는 것만. 나머지(meta의 다른 키, transistors, `run_topology_pipeline` 출력)와 E-INST(파일럿·folded_cascode) instance.json 해시는 같아야 한다. `meta["rails"].nets` = 그 회로 `supply_nets`.

### E-LIB (library 9회로)
- MASK 없이: base `1d2e3bf6…a8f`, head `c1213331…2e8` -- 다름(예정된 `meta["rails"]` 추가 때문).
- MASK `rails`: base·head 모두 `1d2e3bf6acf762ebea14aa526405bfe63db9632cfab68672b93948c2be3b7a8f` -- **같음**. 9회로 모두 per_hash(load·V1_own_stack·V2_kind_stack) 같음, 9/9 load·V1·V2 ok.
- head `meta["rails"]` = `RailDeclaration(nets=…)`, 9회로 모두 nets 집합 = topology `supply_nets`(예: nmcnr {vdd,vss}, pushpull 2회로 {vdd,vss,agnd}, 나머지 {vdd,gnd}).

### E-INST (run_harness SPECS 4회로)
- current_reuse_telescopic_ota(파일럿): base·head instance.json raw_sha256 `2fc426d9ef3a…` 같음, file_bytes·masked·without_topology_ref 해시 전부 같음. stdout은 SLSQP elapsed 시간과 worktree 경로만 다르고 정규화 뒤 같음.
- folded_cascode: raw_sha256 `ef3cd9963d0a…` 같음(나머지 해시도 같음), stdout 정규화 뒤 같음.
- two_stage_ota: base·head 모두 같은 ValueError('stage1_out' 그룹 VDS 합 2.37965V vs vdd 1.8V KVL) -> instance 없음, exit 1. 기존 I-C11(Phase 4 xfail과 같은 원인), 양쪽 stdout 같음.
- nmcnr_amplifier: base·head 모두 같은 ValueError(모든 theta infeasible, 'stage2_diode_ref' 그룹) -> exit 1, 양쪽 stdout 같음.
- 결론: 계약 8의 E-INST 2회로 해시 동일 충족, 나머지 2회로도 base와 같은 실패.
- 참고: run_in_background(bash 하위)로 돌렸을 때는 numpy를 못 찾아(user site-packages 미적용으로 보임) 4회로 모두 import 실패 -- foreground에서 다시 돌린 결과가 위 값.

## 4. 결론
멈춤 없음. 커밋 90eedb2(test), cb0ef86(code). V3(생존 변이) 측정은 지시대로 돌리지 않음.
