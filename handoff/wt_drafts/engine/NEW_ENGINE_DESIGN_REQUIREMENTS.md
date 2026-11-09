# 새 gm/ID 엔진 설계 요건 (NEW_ENGINE_DESIGN_REQUIREMENTS)

- 작성 2026-10-07. 문서 정독·설계 제안만 했다(코드·저장소 수정 없음).
- 기준: 메인 저장소 `chip-design-skills` HEAD `a21a24f`(계획서·design·references는 tag `legacy-engine-v1` = `6df4bd7`과 diff 0 -- 행 번호 동일).
  - P = `docs/01-plan/features/gain-budget-gmid-sizing.plan.md`(1193행, 전체 정독), H = 같은 폴더 `.history.md`.
  - C00 = `docs/02-design/features/gain-budget-gmid-sizing.00-common.design.md`, C30 = `...30-module-split.design.md`.
  - R = `_drafts/engine/ROADMAP.md`, LP = `_drafts/engine/layout_pipeline_analysis.md`, DP = `_drafts/engine/decision_package_specs.md`, S6a = `_drafts/engine/6a_structure_prep.md`, PA = `_drafts/engine/power_area_min_study.md`.
  - 옛 엔진 = `skills/analog-gmid-design/legacy/`(SR = `sizing_recipe.py` 12,013줄, SD = `stick_diagram.py` 9,010줄).
- 사용자 확정 입력(`_drafts/user_decisions.md` 2026-10-07 항목): 새 엔진은 계획서 N3 아키텍처로 `skills/analog-gmid-design/gmid_engine/`에 새로 짓는다, 옛 엔진은 참고·대조 기준선, gate·역할 분리 인프라 꺼짐(가벼운 절차), 범위 = library 9회로 전부·구조 유도(태그 없이)·노드전압 DC 정본·(전력, 면적) front·9회로 ngspice 합격, 기간 약 1달(합리적 사유면 2달), 레이아웃 규칙 (c) 전부 채택, 대원칙 "같은 값을 반복 계산하는 loop를 만들지 마라", 그리고 추가 대원칙 "엔진을 한 파일에 몰아 쓰지 말고 기능별 파일로 쪼개라".
- 표기: **[추측]** = 실측·원문 근거 없이 추론한 것. **[제안]** = 이 문서의 설계 제안(사용자 결정 아님, WP-16에 따라 원칙에서 유도한 기본안).

---

## 1. 대원칙과 구조적 강제 방법

원칙마다 (가) 계획서 원문(행 번호) (나) 새 엔진에서 '규칙 문장'이 아니라 **구조로** 강제하는 방법 (다) 그것을 고정하는 test를 적는다. test는 gate가 아니라 **일반 pytest**로 `gmid_engine/tests/structure/`에 두고 매 변경 뒤 전체 실행(가벼운 절차 '남기는 것' 4)에 들어간다.

### 1.1 계산 재사용 -- "같은 값을 반복 계산하는 loop를 만들지 마라" (사용자 2026-10-07)

(가) 원문
- NFR-2(P 182): "같은 계산을 호출부마다 반복하지 않는다. **캐시 키는 그 계산이 실제로 읽는 모든 가변 상태의 내용 지문**이다. 캐시는 상한을 두고 초과 시 LRU로 밀어낸다(캐싱 중단 금지). ... 같은 실행 안에서 같은 입력 해시로 같은 계산 블록을 다시 계산한 횟수는 0이어야 한다 ... 최적화 판단 근거는 cProfile과 중복 인자 계측 기록이다(WP-10)."
- WP-10(P 292): "반복문 안의 계산은 쓰는 순간 캐시하고(상한 필수), 최적화 근거는 cProfile과 중복 인자 계측으로 만든다."
- SC-d(P 407) "지문 불일치 = 캐시 없음", SC-e(P 408) "metric과 계산 블록은 실제로 읽은 S2 필드를 기록한다", SC-b(P 405) "필드마다 쓰기 카운터 ... `setdefault`로 기존 값을 건너뛰지 않는다".
- S2 memo(P 366, P 410): "블록마다 입력·출력을 선언하고, 결과는 입력 내용 해시로 S2에 memo한다. 전역 metric은 봉인 스냅샷마다 한 번 계산한다."
- IC10(P 830): "캐시 키가 가변 상태를 놓침 -- `ctx.sized`만 바꾸고 같은 metric 호출 시 옛 값 미반환".
- DF-07(P 919) "캐시 상한 도달 시 LRU가 아니라 캐싱을 멈춘다", DF-13(P 925) "`id(lut)` 키 캐시와 상한 없는 캐시".
- N3.7 GB4(P 461): "7b에서 ... 다시 계산할 때는 이 GB4 격자 표에서 ... 행만 거르는 필터로 하고 LUT 격자를 다시 돌지 않는다."
- DEC-30(P 225), FR-7(P 173), N1.1 (d)(P 139): 실패 포함 계산 결과를 버리지 않는다.
- DEC-74(P 268): 감도 게이트는 "S0 지문이 바뀔 때 + 최종 해에서"만(정의가 고정된 동안 같은 것을 다시 재지 않는다).

(나) 구조적 강제 [제안]
1. **불변 상태 + 내용 지문 객체**: S0·S1·S1v·S2 스냅샷·θ·LUT 표는 전부 `frozen` dataclass이고 생성 시 `fp`(sha256, 정규화 바이트)를 한 번 계산해 들고 다닌다. 값이 바뀌면 새 객체 = 새 지문이므로 "가변 상태를 놓친 키"(IC10)가 표현 불가능하다. `set_device_vds`류 제자리 갱신 API는 없다(writer는 새 스냅샷을 만든다, SC-a·SC-b).
2. **계산 블록 데코레이터 `@compute_block(name, reads=(...), domain=...)`**(`core/memo.py`): 블록 함수는 선언한 `reads` 필드의 **투영(projection) 객체만** 인자로 받는다. 키 = (블록 이름, 블록 코드 해시, 투영의 지문). 그래서 (i) 키가 실제로 읽는 상태를 모두 담고(NFR-2) (ii) 선언 밖 필드를 읽을 수 없어 SC-e reader 기록이 구성상 참이다(선언 = 실제 read). 지문 없는 가변 객체(dict·list·ndarray)를 넘기면 `TypeError`로 즉시 거부한다(`id()` 키 금지, DF-13).
3. **한 곳의 memo 레지스트리**: 모든 캐시는 `core.memo.Registry`에 등록된 `BoundedLRU`다. 모듈 전역 dict 캐시·`functools.lru_cache(maxsize=None)`·인스턴스 속성 캐시를 금지한다(lint test). 상한은 상수가 아니라 N3.5 식(P 412: 평가 수 상한 × 계산 블록 수)과 블록별 첫 평가 실측 조회 수에서 계산한다(WP-03). 상한 도달 시 LRU 퇴출(DF-07 금지 패턴 차단).
4. **카운터 내장**: 레지스트리가 블록마다 `hit / miss / evict / recompute_same_key`를 센다. `recompute_same_key`는 퇴출되지 않은 키가 다시 계산된 횟수(구조상 0이어야 함)와 퇴출 뒤 재계산(별도 집계, NFR-2)을 나눈다. 실행 보고(결과 JSON `perf.memo`)에 매번 쓴다.
5. **루프 불변식은 '컨텍스트 객체'로 밖으로**: 평가 커널은 `KernelContext`(S0 단위로 한 번 만듦: LUT 파생표, S1, S1v, GB4 상한표, 보상 목표, tol_V·tol_I 식 입력)를 받고 후보마다 θ만 바뀐다. `KernelContext` 생성 함수는 S0 지문당 1회만 호출됨을 계수기로 test한다(세션47 99.3% 사례 = 루프 안 `load_topology` 재파싱의 구조적 차단).
6. **실패도 캐시**: 평가 캐시 키 = (θ 각 성분 `float.hex`, S0 지문)(P 416). 값 = 성공 결과 또는 `FailureRecord`(N3.14). H 12.3 #2 실측(SLSQP 811회 중 784회 중복, 실패 미캐시)의 차단.
7. **부분 재계산**: θ 한 성분 변화가 닿는 블록만 miss가 나게 하는 것은 2의 투영 키로 자동이다(H 12.3 #6: FD 한 스텝에서 바뀐 소자 6.7/51인데 전부 재계산, 조인트 스캔이 warm 평가의 66%).

(다) test(§4.5에 상세): `test_memo_key_covers_reads`(IC10), `test_no_unregistered_cache`(lint), `test_kernel_context_built_once_per_s0`, `test_fd_step_recomputes_only_impact_set`, `test_no_duplicate_recompute_pipeline`(NFR-2 합격 기준 = 같은 키 재계산 0), `test_dup_arg_trace_hot_functions`.

### 1.2 기능별 파일 분할 -- "한 파일에 모두 코드로 작성되면 안 된다" (사용자 2026-10-07 추가 대원칙)

(가) 원문·실측 근거(옛 엔진에서 한 파일 집중이 낳은 비용)
- 사용자 원문: "작성되는 엔진은 한 화일안에 모두 코드로 작성되면 안 돼. 기능별로 적정한 화일로 쪼개져서 유지보수가 편하고 디버깅이 쉽도록 작성되어야 해. 이게 옛 엔진의 가장 중요한 결함인 것을 잊지마."
- 계획 N3.10(P 517): "import는 번호가 작은 모듈 쪽으로만, 순환 0, **파일당 한 책임**." DEC-46(P 240): "코드는 10모듈(N3.10)로". N5.1(P 903): "`sizing_recipe.py` 15,270줄(인라인 self-test 2,700줄), `stick_diagram.py` 12,936줄(3,946줄). `def test_` 0개."
- 실측 비용(계획·history 근거):
  1. **같은 개념이 여러 정의로 갈라짐**: H 12.3 #5 "diode 집합 16/1/20개(connectivity/role/find_diode_stacks), ratio 쌍 18개 중 11개는 connectivity상 미러 아님, **vsb 기록 경로 9곳**". 한 파일 안에서 정본을 찾지 못하고 새로 쓰는 일이 반복됐다(메모리 `feedback_record_before_compact_check_before_build`: 세션47에 이미 있는 것을 다시 만든 사례 5건).
  2. **죽은 코드·중복 누적**: H 5162행 함수 감사 -- SR 218함수 중 D(운영 호출 0) 27·DUP 11, SD 158함수 중 D 20·DUP 7. 계획 Phase 2(P 1001) 전체가 그 정리 작업이다.
  3. **숨은 교차 비용**: 세션47 평가 1회 비용의 99.3%가 `stack_kvl_vgs_limit()` 안의 `load_topology()` 재호출(H 2985~2989)이었다 -- 헤드룸 함수가 로더를 부르는 의존이 한 파일 안에 묻혀 있었다.
  4. **배치 오인**: H 5235 "`resolve_stack_layout`(실제 위치는 sizing_recipe.py:7025 -- §8.4 정정)" -- 레이아웃 함수가 사이징 파일에 있어 계획이 위치를 잘못 적었다.
  5. **구조 질의 분산**: R 49행 "옛 구조 질의가 소자 리스트를 각자 순회(sizing 24곳, stick 83곳) -- 통합 그래프 없음".
  6. **분할 자체의 비용**: 사후 분할(Phase 3)에 design 문서 C30 1,397행, 이동 card M1~M10·F1·F2, R 212행 산정 "Phase 3 이동 13.2 h", C30 §2.3 M10 하나의 뮤테이션 비용 추정 20~40분~3.2시간. 파일을 처음부터 나누면 이 비용이 0이다.
  7. **운영 metric의 회로 종속 은닉**: DF-29(P 941) 파일럿 넷 이름·경로가 박힌 metric 3개, DF-30·31(P 942·943) 회로 이름 키 -- 한 파일 레지스트리 안에 섞여 일반화 위반이 드러나지 않았다.

(나) 구조적 강제 [제안] -- 3.1절 상세
1. **MOD1~MOD10 = 하위 패키지(디렉터리)**, 그 안은 **파일 하나 = 한 개념 또는 한 계산 블록**. 패키지 밖에 공개하는 이름은 그 패키지 `__init__.py`의 `__all__`뿐이다.
2. **모듈 지도 매니페스트** `gmid_engine/_module_map.py`: 파일마다 {책임 한 문장, 구현하는 계획 ID(예: `DEC-63`, `N3.6 항목 7`), 계산 블록 이름(있으면)}. 파일이 지도에 없거나 지도 항목에 파일이 없으면 test FAIL. 한 파일이 서로 다른 개념(계획 ID 묶음)을 둘 이상 주장하면 FAIL.
3. **파일 간 import 계층**: 패키지 간은 번호 오름차순(core < MOD1 < ... < MOD10), 패키지 안은 `_module_map.py`가 정한 층 순서로만, 순환 0. 다른 패키지의 비공개 파일·`_` 이름 import 금지.
4. **파일 크기 상한은 두지 않는다**(사용자 2026-10-07). 대신 '한 파일에 너무 많은 함수'를 피하는 **파일 구성 규칙 A~D**(오케스트레이터 제안안, 사용자 승인 대기 -- 이 문서는 이 안으로 쓴다):
   - **(A) 파일당 독립 진입점 하나**: 그 파일의 공개 함수·클래스 중 같은 파일의 다른 정의에서 호출되지 않는 것이 정확히 1개. 예외: 레지스트리 등록 데코레이터로 묶인 같은 시그니처 변형군(예: metric 레지스트리 항목들)은 한 개념으로 센다.
   - **(B) 비공개 helper는 그 파일 진입점만 쓴다**: 두 파일이 쓰는 helper는 공용 helper 모듈로 옮긴다. 다른 파일의 `_` 이름 import 금지.
   - **(C) 캐시되는 계산 블록 하나 = 파일 하나**: 키·입력·무효화가 한 곳에 있다(1.1의 `@compute_block`이 파일당 하나).
   - **(D) test 파일은 원본 파일과 1:1**: `tests/<pkg>/test_<file>.py`.
   - 실측 근거(오케스트레이터 측정): 옛 `sizing_recipe.py` 정의 187개 중 178개가 한 호출 덩어리, 독립 진입점 14개; `stick_diagram.py` 독립 진입점 25개 -- 한 파일에 진입점 수십 개와 서로 얽힌 helper가 뭉친 것이 1.2 (가) 비용 1~6의 구조적 원인이다.

(다) test: `test_import_layering`, `test_no_import_cycles`, `test_public_api_only`, `test_module_map_complete`, **`test_one_entry_point_per_file`(A, AST: 파일별 공개 정의 중 파일 안 호출 그래프의 뿌리 수 = 1, 데코레이터 등록 변형군은 1로 셈)**, **`test_private_helpers_local`(B, AST: `_` 이름의 파일 밖 import 0, 두 파일 이상에서 쓰이는 helper 0 -- 공용 helper 모듈은 `_module_map.py`에 `kind="helper"`로 등록된 파일만 예외)**, `test_one_compute_block_per_file`(C, `@compute_block` 수 ≤ 1), `test_tests_mirror_sources`(D, 원본 파일마다 대응 test 파일 존재·고아 test 0), `test_no_inline_selftest`(엔진 파일에 `if __name__ == "__main__"`·self-test 0, WP-19·DEC-46).

### 1.3 상수 금지 (WP-03)

(가) WP-03(P 285): "상수를 임의로 만들지 않는다. 근거 선언값 하나만 두고 식을 코드로 계산해 캐시한다. 유도를 주석에 적고 결과 숫자를 박는 것은 해결이 아니다." DEC-20(P 215) `value_from_constraint`, DEC-72(P 266) `value_from_model_error`, N9.2-3(P 1175) "숫자를 박지 않는다". 사용자 2026-10-07: "상수는 배제하고 공정 PDK를 통해서 그 공정에서 사용할 오차를 계산하도록".

(나) 구조적 강제 [제안]
- **근거 원천 3종만 수치를 낸다**: 사람 선언(회로 spec·topology), PDK 선언(`core/pdk_decl.py`가 tlef `MANUFACTURINGGRID` 0.005 µm, difftap.2 최소폭 등 규칙 번호와 함께 읽음 -- P 796 U-30, 사용자 tlef 결정), LUT(파일과 메타). 나머지 수치는 **이 셋에서 계산하는 이름 있는 함수**의 반환값이고, 그 함수는 1.1의 memo로 한 번만 계산된다.
- 예: W 허용오차 상한 = `tol_V × (gm/ID)`(소자별), 하한 = `MANUFACTURINGGRID / (2·finger_w)`(R 331행) -- 두 식 모두 `layout/w_tolerance.py` 함수, 입력은 `lut/tolerance.py`의 tol_V와 `core/pdk_decl.py`의 격자.
- lint test `test_numeric_literals_derived`: 엔진 소스의 숫자 리터럴은 허용 집합 {0, 1, -1, 2(산술식), 인덱스} 밖이면 같은 줄 `# derive: <함수명>` 태그가 있고 그 함수가 존재해야 한다(옛 V6의 리터럴 규칙을 일반 test로 이식). 단위 환산 계수는 `core/units.py` 한 곳.

### 1.4 일반화 -- 회로·소자·넷 이름 하드코딩 금지 (WP-05, DEC-62)

(가) WP-05(P 287) "회로·소자·theta 이름과 매직넘버 금지", DEC-62(P 256) "새 토폴로지 추가는 데이터만으로", DF-23(P 935) "점검 대상은 ... 소자·넷·회로 이름과 topology 파일 경로 전부", DEC-60(P 254) 이름 집합으로 레일 판정 금지.
(나) 구조적 강제 [제안]: 엔진은 이름을 **값으로만** 다룬다(입력에서 읽은 문자열). `test_no_name_literals`: library 9회로 JSON에서 모든 소자·넷·포트·수동소자 이름과 회로 키를 모아, `gmid_engine/`(tests 제외) AST 문자열 상수와 교집합 0. 레일 이름(`vdd`, `gnd`, `vss`, `agnd` 등)도 같은 수집에 들어간다(레일은 `authoring.rails.rail_declaration`만 낸다). 회로별 분기(`if circuit ==`)·회로별 레지스트리 키도 같은 test가 잡는다. 무동작 증명(WP-05 후반)은 2.3의 규칙 분기 발동표로 한다.

### 1.5 결정론 (NFR-4)

(가) NFR-4(P 184): "모든 반복은 정렬된 시퀀스 위에서 한다(`set` 순회 금지). 같은 입력은 같은 산출물을 낸다." IC2(P 822).
(나) [제안] S1 API는 정렬된 `tuple`만 반환한다(내부 `frozenset`은 노출하지 않음). `core/determinism.py`의 `sorted_items()` 외 dict 순회 순서에 기대는 코드는 lint로 금지(`for x in <set>`·`set(...)` 직접 순회 AST 검출). 캐시 퇴출 순서가 결과에 영향을 주지 않도록 memo 값은 순수 함수 결과만 담는다.
(다) `test_order_shuffle_invariance`(IC2: 입력 JSON 소자 순서 섞기 × `PYTHONHASHSEED` 1~5 → 결과 JSON 정규화 해시 동일).

### 1.6 실패 규약 (N3.14)

(가) N3.14(P 734~751): 분류·예외·탐색 중 처리·exit code, "광범위 except로 이 규약을 우회하지 않는다 ... 탐색 루프는 '탐색 중 처리'가 실패 기록인 클래스만 이름으로 잡고 기반 클래스 `InfeasibleSizingError`를 잡지 않는다", SCHEMA_REJECTED는 `Exception` 직접 하위(P 746).
(나) [제안] 예외·`FailureRecord`·`FAILURE_CLASSES`·`exit_code_for`·`normalized_margin`을 **`core/failures.py`(층 0)**에 둔다(C00 §7.1의 MOD2/MOD4 분산 배치를 바꿈 -- 이유는 5절 충돌 C4). 그래서 MOD1(LUT 축 밖, LR3 P 507)부터 어디서나 같은 클래스를 raise할 수 있다. 탐색 루프는 `CANDIDATE_FAILURE_CLASSES` 튜플만 잡는다.
(다) `test_no_broad_except`(엔진 소스에 `except Exception`/`except ValueError`/`except InfeasibleSizingError` 0, 진입점 1곳 예외), `test_failure_classes_match_plan`(P N3.14 표 파싱 ↔ `FAILURE_CLASSES`), `test_exit_codes`(합성 raise → 진입점 exit code).

### 1.7 레일 선언 (DEC-60)

(가) DEC-60(P 254): "레일은 두 선언으로 정한다(넷 이름 집합으로 판정하지 않는다). 레일 넷 = topology `supply_nets` ... 레일 전압 = `supplies_v{넷: 전압}`." DEC-61(P 255) bulk 기본 규칙, IC11(P 831) 원점 이동 불변.
(나) [제안] `authoring/rails.py` `rail_declaration()`(B26-1 구현 이식, R 44행)이 유일한 레일 출처. **전환기 해석(스칼라 `vdd` 폴백)을 새 엔진에 만들지 않는다**(5절 C11) -- `supplies_v` 없는 회로 spec은 로드 거부. 숨은 레일 (iii) 판정(잎 가지치기 **전** DC 전도 그래프)은 `authoring/hidden_rails.py`.
(다) `test_rail_origin_shift_invariance`(IC11, 2레일·3레일), `test_supply_nets_required`, `test_hidden_rail_rejected`(공격 14 (a)(b)의 입력을 일반 test로).

### 1.8 그 밖에 그대로 가져가는 원칙
- 영역 표기 DEC-67(P 261): S1 엣지·metric·S2 필드에 `domain` 필수, `ss`·`ls`는 봉인 통과 스냅샷에서만(구조: `SealedSnapshot` 타입만 `ss`/`ls` 계산 함수의 인자로 허용 -- 봉인 전 객체는 타입이 달라 넘길 수 없음).
- 단일 writer SC-a(P 404)·노드 하나에 writer 하나(P 394): writer 권한표를 `sizing/writers.py` 상수 표 하나로 두고 S2 빌더만 쓴다.
- 만들면 배선 WP-01(P 283)·발동 0 분기 미구현 DEC-76(P 270): `_module_map.py`의 모든 공개 함수가 진입점에서 도달함을 `test_reachable_from_entry`로 확인(옛 V7의 일반 test판).
- 상상 금지 WP-17·작성자≠검증자 WP-13: 가벼운 절차 '남기는 것' 1(코드·test 작성 주체 분리)만 유지.

---

## 2. 아키텍처 -- 계획서 N3를 새 엔진에 적용

표의 판정: **유지** = 그대로 / **변경** = 오늘 결정·새 엔진 전제로 바뀜 / **버림** = gate·이관 전용이라 새 엔진에 없음.

| 계획 절(행) | 내용 | 판정 | 새 엔진에서 |
|---|---|---|---|
| N3.1 GB0~GB9(P 310~335) | 흐름·실행 구조(GB0~GB4는 S0당 1회, 후보마다 GB7→봉인→GB5→GB8) | 유지 + 변경 | 흐름 유지. 모듈 배정 변경: GB4·GB5를 MOD4에서 MOD5 쪽으로(C3). 실행 구조 문장(P 325)은 1.1의 `KernelContext` 분리로 구현 |
| N3.2 SP1(P 337~357) | 교류접지·여기 뷰·셀·구동 종류·stage·루프 | 유지 | 6a 열린 항목 ①~⑮(P 1162)는 알고리즘으로 정해 test로 고정(WP-21) |
| N3.3 S0~S3(P 359~380) | 지문·구조·뷰·동작점·사전정보·탐색 기억 | 유지 + 변경 | S0 '유도 규칙 코드 해시'는 패키지 소스 해시로 구현 [제안 -- `ast.dump` 호출 폐포보다 거칠지만 놓치지 않음]. status 전이·`structure.json`(ratified만) 유지. S3 경로 유지 |
| N3.4 W0~W4(P 382~397) | writer 티어 | 유지 + 변경 | W0의 전환기 전압 해석 삭제(C11) |
| N3.5 상태 계약·커널·최적화(P 398~420) | SC-a~e, 계산 블록 ②③④⑤→봉인→①→⑥, LRU 상한식, 실패 캐시 | 유지 + 변경 | 6b~7a 전환기 경로·전환기 writer 삭제(C8), 7b 순서를 처음부터. 실패 캐시 임시 지문 삭제(C9) |
| N3.6 봉인·허용오차(P 422~442) | 봉인 1~8, tol_V(LOO)·tol_I·K_max | 유지 | tol_V는 W 허용오차 상한에도 쓴다(사용자 결정). 계산 원천 이전(C21) |
| N3.7 결합·달성가능성·DOF·할당(P 444~484) | K1~K8, GB4, 층 0/내·중·외층, 보상 규칙, 출력 구동 | 유지(축소는 R D18 결정 대기) | 기본 경로(층 0 + 외층 SLSQP + ε-제약 두 방향). 정밀 경로·DOF 수치 rank는 DEC-76 원칙으로 '발동 시 구현' |
| N3.8 metric(P 486~499) | MNA gain, 블록 국소 모델, gmb, 잔차, 감도 게이트, 전력·면적, 스윙, verified_by, SPICE | 유지 | SPICE는 `tools/spice_oracle/`(엔진 import 없음, R 20행) |
| N3.9 LR1~LR9(P 501~513) | L 결정 규칙 | 유지 + 변경 | LR8·LR9의 레이아웃 연동은 오늘 레이아웃 규칙(W 보존·W_request)으로 구체화(2.2) |
| N3.10 모듈 구조(P 515~535) | MOD1~MOD10 단일 파일, 레지스트리 이관 목적지, 이동 규칙, shim | 변경 + 일부 버림 | MOD = 하위 패키지(1.2·3.1). 이관 목적지·이동 규칙·shim(P 533~535)은 버림(옮기지 않고 새로 짓는다). core(층 0) 추가 |
| N3.11 test 구조(P 537~565) | tests 배치, TS0~TS7 | 변경 + 일부 버림 | 배치는 `gmid_engine/tests/{unit,integration,contracts,regression,oracles,structure,perf}`로. TS0~TS6(옛 self-test 이관)은 버림. TS7(계약 test xfail→활성)은 유지 |
| N3.12 역할 분리(P 567~723), EL1~EL4 | 권한·쓰기 경로표·흐름·hook·gate | **버림** | 가벼운 절차의 '남기는 것'(코드/test 작성 주체 분리, 약화 보고, 변경당 커밋 1, 매 변경 뒤 전체 pytest)만 |
| N3.13 bisection(P 725~732) | 임계값 재도출 | 유지(기본 비활성) | DEC-75 선언으로만 |
| N3.14 실패 규약(P 734~751) | 분류·예외·exit code·margin | 유지 + 변경 | 위치를 core로(C4) |
| N3.15 spec 파일(P 753~763) | `sizing_spec.json` 7b | 변경 | 처음부터 회로 spec 파일(R D5). topology 필드 이관 절차는 버림(새 로더는 topology에서 sizing 필드를 읽지 않는다) |
| N3.16 명명·MG0~MG3(P 765~809) | 개념별 정본 이름, 단계 마이그레이션 | 유지 + 변경 | 정본 이름 표 유지. MG 단계·옛 키 거부의 '단계'는 버리고 로더 스키마가 정본 이름만 받음(옛 이름은 `SchemaRejectedError`) |
| N4.1 IC1~IC11(P 815~831) | 기지 사고 강제 test | 유지 | 새 API로 다시 씀(R 0.4) |
| N4.2 V1~V10(P 833~848), N4.3 공격(P 850~895) | auditor 검사·게이트 거부 증명 | **버림**(일부 이식) | V4(자기참조)·V6(lint)·V7(도달) 중 엔진 품질에 직결되는 판정은 1절의 일반 test로 이식. 공격 12·13·14는 로드 게이트 거부 test로 이식 |
| N5.2 DF(P 907~949) | 현존 결함 | 변경 | 고칠 대상이 아니라 **재발 금지 목록**(R 76행) -- DF마다 새 엔진 계약 test 1개 |
| N6 로드맵(P 989~1035) | Phase 0~7c | 변경 | 7절 순서로 대체. Phase 0.5~3은 버림 |
| N7 J·U(P 1039~1120) | 공동분석·사용자 결정 | 유지 | J는 R의 U2 한 번, U는 DP·R 4절과 6절 |
| N9 design 지침(P 1147~1193) | 문서 목록·필수 절 | 변경 | 05·10·20·30은 버림, 6a~7c는 R D1~D4 '인터페이스 명세 수준'으로(6절 E7) |

### 2.1 오늘 결정으로 바뀌는 것 요약
1. 옛 엔진 이동·분할(Phase 3, C30) → 새 패키지에 처음부터 기능별 파일.
2. gate·역할 분리(N3.12, V1~V10, EL1~EL4, 공격 28건, Phase 0.5, U-15·U-38·U-40) → 없음.
3. 레이아웃: "레이아웃 알고리즘 변경은 범위 밖"(P 160) → 레이아웃 규칙 (c) 채택(2.2).
4. 사이징 대상 회로 = 기존 4개(P 124) → 합격 시험은 9회로(스펙 값은 DP 36칸 결정 뒤).
5. 전환기(스칼라 vdd·전환기 writer·임시 지문·MG 단계) → 없음.

### 2.2 오늘 레이아웃 규칙의 아키텍처 반영 [제안]
- 흐름: GB6 해(θ*) → MOD4가 소자별 총 W·W 허용오차를 낸 **레이아웃 입력 계약**(3.3) → MOD7이 matching group마다 패턴을 **행 구성 단계에서 먼저** 고름(패턴표 우선, `interdigitate_layout`·`common_centroid_layout` 재사용) → 행별 finger_w·nf 선택(총 W를 허용오차 안에서 보존) → Euler·box 판정 → 실패 쌍을 **전부 모아**(첫 실패에서 멈추지 않음, LP §5 (c)4) 판정 → W를 바꿔야 하면 `W_requests`로 MOD8에 반환 → MOD8이 그 소자 W 고정 제약으로 MOD6 평가 커널을 다시 돌림(바뀐 소자의 W를 읽는 블록만 miss) → 새 계약으로 MOD7 재실행. 반복 상한·NONCONVERGENT는 N3.6 K_max 규칙(P 441, LR9 P 513).
- 차동쌍: common-centroid 우선, 시도 순서 (i) 같은 총 W에서 nf 조정 (ii) W_request 경유 W 조정, 둘 다 불가일 때만 interdigitation 완화 + 시도 기록(nf·W·실패 사유)을 결과 JSON에 남김(사용자 결정, R 329행).
- 패턴 함수 재사용 방식 [제안·기본안]: `legacy/stick_diagram.py`에서 `interdigitate_layout`·`common_centroid_layout`·하위 함수와 두 패턴표를 **본문 그대로 복사**해 `layout/patterns.py`에 두고 함수별 `ast.dump` 해시를 원본과 대조하는 test를 둔다. import로 쓰면 LEGACY.md '남은 의존'이 하나 늘어 옛 엔진 삭제를 막는다. `COMMON_CENTROID_PATTERNS` 주석의 '원문 재확인 권장'(R 327행)은 복사 card에서 1회 대조.
- LUT 폭 의존: finger_w ≠ LUT W_ref면 그 폭의 DC 슬라이스로 재확인(R 323행, lut_coverage_study 표 A: nfet W에 따라 같은 gm/ID의 ID/W가 −28%~+170%). 슬라이스는 (kind, finger_w) 키로 memo·디스크 캐시. 후보 finger_w 집합 정책은 6절 E5.

---

## 3. 모듈 책임·공개 인터페이스 초안, 데이터 계약

### 3.1 패키지 구조 (MOD = 하위 패키지, 파일 = 한 개념/한 계산 블록) [제안]

규칙
- 패키지 간 import: `core`(0) < `lut`(1) < `authoring`(2) < `graph`(3) < `sizing`(4) < `metrics`(5) < `search`(6) < `layout`(7) < `convergence`(8) < `report`(9) < `pipeline`(10). **작은 번호 쪽으로만**. 다른 패키지는 `from gmid_engine.<pkg> import <공개 이름>`만(`__init__.__all__`).
- 패키지 안 import: `_module_map.py`의 층 번호(아래 표 `층` 열) 오름차순만. 같은 층끼리 import 금지(순환 원천 차단).
- 파일 하나 = 한 개념(계획 ID 묶음 하나) 또는 한 계산 블록(N3.5 ②~⑥ 하나). 1.2의 규칙 A~D(독립 진입점 1, helper 파일 국소, 계산 블록 1 = 파일 1, test 1:1)를 따른다. 아래 표에서 한 칸에 여러 파일을 묶어 적은 것(예: `gain.py`·`gbw_pm.py`)은 각각 별도 파일이다. 표의 파일이 구현 중 진입점 둘 이상이 되면 쪼갠다(규칙 A가 FAIL로 알려 준다).
- 공용 helper 모듈은 패키지마다 `_helpers_<주제>.py`로 두고 `_module_map.py`에 `kind="helper"`로 등록(규칙 B 예외).
- test 배치: `gmid_engine/tests/<pkg>/test_<file>.py`(규칙 D) + 교차 관심사 `tests/{structure,contracts,integration,regression,oracles,perf}/`.
- 계획의 파일 이름(N3.10 `gmid_lut.py` 등)은 패키지 이름의 근거로 `_module_map.py`에 대응을 적는다(C2).

| 패키지(MOD, 계획 파일명) | 파일(층) | 책임 / 계획 ID |
|---|---|---|
| `core` (층 0, 계획에 없음 -- 신설) | `fingerprint.py`(0) | 정규화 바이트·sha256 지문, `Fingerprinted` 기반 (SC-d) |
| | `memo.py`(1) | `@compute_block`, `BoundedLRU`, `Registry`, 카운터 (NFR-2, WP-10, SC-e) |
| | `failures.py`(0) | N3.14 예외·`FailureRecord`·`FAILURE_CLASSES`·`exit_code_for`·`normalized_margin` |
| | `units.py`(0) | 단위 표·`DOMAINS`(C00 §5, DEC-53·67·68) |
| | `determinism.py`(0) | 정렬 순회 도우미 (NFR-4) |
| | `pdk_decl.py`(1) | PDK 선언 읽기: tlef `MANUFACTURINGGRID`, 최소 finger 폭(difftap.2), L 격자, 수동소자 단위 면적(U-36) -- 출처 규칙 번호 포함 (U-30, DEC-80 (i)) |
| | `instrument.py`(1) | 계측 ContextVar·`wrap_evaluate`/`wrap_search`(C00 §10.1), cProfile 옵션 |
| `lut` (MOD1, `gmid_lut.py`) | `table.py`(0) | npz 로드·메타(`lut_conditions_from_npz`, `w_ref_m`)·LUT 지문 (I-A5) |
| | `interp.py`(1) | 다선형 보간(옛 `_multilinear_interp*` 이식) |
| | `query.py`(2) | 점 조회(memo), 축 밖 거부 `lut_axis_out_of_range` (LR3, DF-27) |
| | `curves.py`(3) | (kind, L, vds, vsb) gm/ID 곡선 표, 단조성 검사 (N3.7 LUT 곡선 검사) |
| | `inverse.py`(4) | gm/ID→VGS rightmost root, ID 역산 (DEC-11, DF-10) |
| | `gmb.py`(3) | ∂ID/∂VSB (P 490) |
| | `vdsat.py`(3) | LUT (ID, gds, VDS)에서 VDsat 유도 (DF-25) |
| | `tolerance.py`(3) | tol_V(LOO 보간 오차) (N3.6, DEC-32) |
| | `slices.py`(2) | finger_w별 DC 슬라이스 로드·조회 (R 정정 3·5) |
| `authoring` (MOD2, `topology_authoring.py`) | `topology_load.py`(0) | topology JSON 읽기·linked 파일 합치기·이름 유일성(IC3). 역할 태그 키 무시 (R D13) |
| | `schema.py`(0) | 정본 이름 스키마·옛 이름 거부 (N3.16) |
| | `rails.py`(1) | `rail_declaration`(B26-1 이식) (DEC-60) |
| | `hidden_rails.py`(2) | 숨은 레일 (iii) 거부 (DEC-60, 공격 14) |
| | `spec_load.py`(1) | 회로 spec 파일 로드: constraints `source` 필수, 논문 출처 거부, `optional_stages` 화이트리스트 (N3.15, DEC-75, U-35) |
| `graph` (MOD3, `circuit_state_graph.py`) | `s0.py`(0) | S0 지문 조립 |
| | `s1_model.py`(0) | S1 dataclass(노드·소자·수동·이상원·관계 엣지·가지·기둥) (N3.3) |
| | `s1_build.py`(1) | `build_s1`과 생성 시 인덱스(`by_net_terminal`, `gs_groups`, `channel_adj`) (S6a 1.3) |
| | `dc_conduction.py`(2) | DC 전도 그래프·잎 가지치기 전/후 (DEC-70·71(1)) |
| | `columns.py`(3) | 가지·기둥 열거(노드-단순, 레일 쌍별) (DEC-71 (1)(3), J13) |
| | `relations.py`(2) | `equal_vgs`·`kcl_group`·`l_class`·`matching_*` 엣지 유도와 declared 대조 (GB1, DEC-09·17) |
| | `dc_roles.py`(3) | 소자 DC 역할 (1)~(5) (용어집 P 87) |
| | `gvgs_cycles.py`(3) | G_vgs 사이클 v0/v1/v2/VDS-1 (DEC-64) |
| | `views.py`(2) | 여기 뷰 수집(전달·루프), 대칭 축약 (N3.2-2·3) |
| | `ac_ground.py`(3) | 교류접지 (1)~(4) 바이어스 종속 넷 (N3.2-1, J1) |
| | `reachability.py`(4) | 최소 고정점 도달성·순방향 경로 (N3.2-3) |
| | `cells.py`(5) | 셀 CS/CG/CD/pass/diode(load), pass 묶음 (N3.2-3) |
| | `drive_kind.py`(6) | 입력 노드 구동 종류 (용어집 P 92) |
| | `bfs_cost.py`(6) | 엣지 비용·0-1 BFS (N3.2-4) |
| | `stages.py`(7) | stage 경계·블록 구성·출력노드·임피던스 등급·극점 노드 (N3.2-5·6) |
| | `loops.py`(8) | 루프 탐지·(0)~(4) 분류·끊는 점·극성 (N3.2-2·7) |
| | `buffers.py`(8) | 버퍼 묶음 R(u) (DEC-63) |
| | `output_direction.py`(8) | β/σ/κ 구조 분류 (DEC-65) |
| | `composite_blocks.py`(8) | 분기·합류 복합 블록 (DEC-81) |
| | `column_block_map.py`(8) | 기둥↔블록 매핑·공유 소자·덮는 기둥 ≥ 1 (DEC-71 (2)) |
| | `matching_groups.py`(8) | 레이아웃 계약용 matching group 레코드(diff_pair/mirror, hub, 필요 패턴) (LP §5 (b)) |
| | `rule_branches.py`(9) | 규칙 분기 발동표·`unsupported_rule_branch` 판정 (DEC-59) |
| | `status.py`(9) | status 전이·`structure.json` 로드/해시 게이트 (N3.3 전이표) |
| `sizing` (MOD4, `gmid_sizing_engine.py`) | `s2_model.py`(0) | S2 `dc` 스냅샷·`SealedSnapshot` 타입·버전 카운터 (N3.3 S2, SC-b) |
| | `writers.py`(1) | W0~W4 권한표·setter (N3.4, SC-a) |
| | `block_currents.py`(2) | 계산 블록 ② KCL·`value_dc_amp`·θ 전류 변수 (DEC-08·70) |
| | `block_lengths.py`(2) | 계산 블록 ③ L 동치류·LR1~LR7·knee (N3.9, DEC-16·17) |
| | `block_columns.py`(3) | 계산 블록 ④ 기둥·순환 블록 고정점(W1/W2, 적층 diode, CD source, `kvl_branch`) (SC-c, DEC-13·64) |
| | `block_widths.py`(4) | 계산 블록 ⑤ W(+ W_request 고정 W 입력) (P 106 1.18식) |
| | `seal.py`(5) | 봉인 1~8, tol_I·K_max (N3.6) |
| `metrics` (MOD5, `circuit_metrics.py`) | `ss_linearize.py`(0) | 봉인 스냅샷 → S2 `ss`(gm·gmb·gds·cgg·노드 C) |
| | `ls_fields.py`(0) | S2 `ls`(방향별 최대 전류·스윙·`c_slew`) (DEC-65) |
| | `mna_build.py`(1) | ω 무관 조립 1회(`build_ac_network` 계열 이식) |
| | `mna_solve.py`(2) | ω별 풀이·주파수 응답 |
| | `block_local.py`(2) | 블록 국소 소신호 모델 (N3.8, DEC-63) |
| | `gain.py`·`gbw_pm.py`·`rout.py`·`swing.py`·`offset.py`(3) | metric 각각 (DEC-05·66, I-A6, DEC-23) |
| | `power.py`·`area.py`(3) | 목적 축 (DEC-78·79 (a)) |
| | `residual.py`·`sensitivity_gate.py`(4) | 잔차·감도 게이트 (N3.8, DEC-74) |
| | `achievability.py`(4) | GB4 블록 gain 상한표 (N3.7) -- C3 정정으로 MOD4에서 이동 |
| | `compensation.py`(4) | GB5 보상 규칙·θ 제약 (DEC-70, N3.7 보상) -- C3 정정 |
| | `drive_constraints.py`(4) | 출력 구동·슬루 제약 (DEC-58) |
| | `registry.py`(5) | metric 레지스트리(이름·단위·domain·`verified_by`) (DEC-53) |
| `search` (MOD6, `theta_search.py`) | `kernel.py`(0) | `KernelContext`(S0당 1회)·평가 커널 조립(②③④⑤→봉인→①→⑥) (N3.5) |
| | `eval_cache.py`(1) | 평가·실패 캐시(메모리) (N3.5) |
| | `archive.py`(1) | S3 디스크 기록(append, 케이스마다 flush) (N3.3 S3, WP-11) |
| | `budget.py`(0) | DEC-34 식·LRU 상한·bin 예산 게이트 (DEC-34·80) |
| | `layer0_local.py`(2)·`layer0_assemble.py`(3) | 층 0 국소 문제·조립 (DEC-71) |
| | `pareto.py`(1) | 비지배 필터 (DEC-77) |
| | `slsqp_outer.py`(3)·`eps_sweep.py`(4) | 외층 SLSQP·ε-제약 두 방향 (DEC-54, N3.7 외층) |
| | `start_points.py`(2) | 시작점 선택 (N3.5) |
| `layout` (MOD7, `stick_diagram.py`) | `contract.py`(0) | 레이아웃 입력·출력 계약 스키마 (3.3) |
| | `w_tolerance.py`(1) | W 허용오차 상·하한 (사용자 결정) |
| | `euler.py`(1) | `build_graph`·`check_euler_condition`·`hierholzer`·`mirror_symmetric_trail` 복사 (LP §5 (a)) |
| | `patterns.py`(1) | 두 패턴표·`interdigitate_layout`·`common_centroid_layout` 복사 (사용자 결정) |
| | `pattern_select.py`(2) | 행 구성 단계 패턴 선택·차동쌍 완화 순서·시도 기록 |
| | `finger_geometry.py`(2) | 행별 finger_w·nf (단위폭 전파 금지, LP §5 (c)6) |
| | `rows.py`(3)·`box_shape.py`(2)·`floorplan.py`(4)·`coverage.py`(1) | 행 구성·box·floorplan·완전성 |
| `convergence` (MOD8, `sizing_layout_convergence.py`) | `w_requests.py`(0)·`loop.py`(1) | W_request 처리·수렴 루프(K_max), 완화 기록 (LR9, 사용자 결정) |
| `report` (MOD9, `instance_report_builder.py`) | `result_json.py`(0)·`front_table.py`(0)·`instance_adapter.py`(1)·`html.py`(1) | 결과 JSON·front 표·옛 instance.json 어댑터·HTML (DEC-77, R 54행) |
| `pipeline` (MOD10, `gmid_design_pipeline.py`) | `entry.py`(0)·`cli.py`(1) | `run_gmid_design_pipeline(spec, *, topology_path, search, output_dir, instrument=None, activations_out=None)`(C00 §10.1·C30 §2.3), exit code |

[추측] 파일 수는 약 85개(규칙 A 적용으로 구현 중 늘 수 있다). 크기 상한은 두지 않고 규칙 A~D만 판정한다.

### 3.2 공개 인터페이스 초안 (패키지 `__init__.__all__`) [제안]

| 패키지 | 공개 이름(시그니처 요지) |
|---|---|
| core | `Fingerprinted`, `fp_of(obj) -> str`, `compute_block(name, reads, domain)`, `Registry.snapshot() -> MemoStats`, 예외 클래스들, `FailureRecord`, `exit_code_for`, `normalized_margin`, `PdkDecl`, `load_pdk_decl(path) -> PdkDecl` |
| lut | `Lut`(frozen, `fp`), `load_lut(path) -> Lut`, `query(lut, kind, field, L, vgs, vds, vsb)`, `vgs_for_gm_id(lut, kind, gm_id, L, vds, vsb)`, `id_density(lut, ...)`, `gmb(...)`, `vdsat(...)`, `tol_v(lut) -> float`, `curve_check(lut) -> CurveReport`, `dc_slice(lut, kind, finger_w)` |
| authoring | `load_topology(path) -> TopologyDoc`, `load_circuit_spec(path, topology) -> CircuitSpec`, `rail_declaration(topology, spec) -> RailDeclaration` |
| graph | `build_s0(...) -> S0`, `build_s1(topology, rails) -> S1`, `build_views(s1, spec) -> tuple[View]`, `derive_structure(s1, views) -> Structure`(stage·블록·루프·버퍼·복합 블록·기둥 매핑·matching group·발동표), `load_ratified(path, s0) -> RatifiedFacts` |
| sizing | `S2Dc`, `SealedSnapshot`, `size_and_seal(ctx, theta) -> SealedSnapshot`(블록 ②~⑤ + 봉인, 실패 시 후보 실패 예외) |
| metrics | `linearize(sealed, ctx) -> SsLs`, `evaluate_metrics(sealed, ss_ls, ctx) -> Metrics`, `compensation_constraints(...)`, `achievability_table(ctx) -> GainBoundTable`, `metric_registry()` |
| search | `KernelContext.build(s0, s1, structure, spec, lut, pdk)`, `evaluate(ctx, theta) -> EvalResult`, `find_front(ctx, search) -> Front`, `solve_at_budget(ctx, budget) -> EvalResult` |
| layout | `LayoutInput`, `LayoutResult`, `run_layout(layout_input) -> LayoutResult`(W_requests 포함) |
| convergence | `converge(ctx, front_point) -> ConvergedPoint` |
| report | `write_result(path, ...)`, `write_instance_json(...)`, `render_html(...)` |
| pipeline | `run_gmid_design_pipeline(...) -> int` |

### 3.3 데이터 계약

**S1** (N3.3 P 364, S6a 1.2 그대로 + 보강): `S1 {key: (topology_fp, rule_fp, supplies_v_fp), nodes{name: Node(terminals, is_rail, ac_ground_class, port_role)}, devices{name: Device(kind, d, g, s, b, is_diode, dc_role)}, passives, sources, edges(tuple[RelEdge(type, domain, members, status, evidence{rule, nets})]), branches, columns}`. 불변·정렬 tuple. `column_block_map`·뷰별 속성은 S1v(`View`)·`Structure`에 둔다(P 364 '매핑은 S1v 확정 뒤'). 선언 태그(`same_as`, `budget_reference_device`, `matching_pairs`)는 status `declared` 엣지로만 싣고 유도 입력으로 쓰지 않는다(S6a 1.2).

**S2** (N3.3 P 366, DEC-67):
- `S2Dc {s1_key, theta_fp, version, node_v{node: (value, writer_tier, writer_id, version)}, path_values, conflicts, branch_i{branch: (value, source ∈ kcl|declared|theta, version)}, device_op{dev: (ID, gm_id, L, W, VGS, VDS, VSB)}(VGS/VDS/VSB는 node_v 파생), column_window}`.
- `SealedSnapshot(S2Dc)`: 봉인 1~8 통과 증명(항목별 잔차·tol)을 가진 별도 타입. `ss`·`ls` 계산 함수는 이 타입만 받는다.
- `Ss {input_version, dev{gm, gmb, gds, cgg, cgd(, cgs, cgb -- DF-28)}, node_c_farad, node_g}`, `Ls {input_version, i_out_max_source_amp, i_out_max_sink_amp, swing_limits, c_slew_farad}`.

**sizing → layout 계약** (LP §5 초안을 오늘 결정으로 고침) [제안]
```jsonc
{
  "contract_version": "layout-input/0.2",
  "pdk": {"manufacturing_grid_m": "<core.pdk_decl, tlef MANUFACTURINGGRID>",
          "min_finger_w_m": "<PDK 규칙 difftap.2>", "l_grid_m": "<PDK>"},   // 리터럴 없음(LP 185행의 숫자 대체)
  "devices": {"<dev>": {
      "kind": "...", "d": "...", "g": "...", "s": "...", "b": "...",
      "W_m": 0.0,                         // sizing 총 W(계약값)
      "W_tol_rel_upper": "tol_V * gm_id",  // 소자별 계산값(LP의 0.01 대체, 사용자 결정)
      "L_m": 0.0, "ID_A": 0.0, "gm_id": 0.0, "vds_V": 0.0, "vsb_V": 0.0,
      "self_biased_diode": true,           // diode 연결이면 finger_w 슬라이스 재보정 불필요(SD 참고문서 §8.3)
      "W_adjustable": true}},              // false = W_request 금지(활성 제약 소자) [제안]
  "matching_groups": [{"id": "...", "members": ["..."], "role": "diff_pair|mirror|...",
      "evidence": {"hub_net": "...", "gates": ["..."], "rule": "graph.matching_groups"},
      "preferred_pattern": "common_centroid",          // diff_pair
      "relaxation_allowed_after": ["nf_adjust", "w_request"], // 사용자 결정(완화 금지 아님)
      "allowed_patterns": ["common_centroid", "interdigitation"]}],
  "row_groups": [{"id": "...", "kind": "nmos", "body_net": "...", "members": ["..."]}]  // 기둥·matching group에서 유도
}
```
출력: 소자별 `{n_fingers, finger_w, rows[{row_id, n_fingers}], W_realized, W_err_rel, W_tol_lower = grid/(2·finger_w)}`(`W_err_rel`이 [하한 해상도로 표현 가능한 범위, 상한] 밖이면 그 결과는 무효), matching group별 `{pattern, method(pattern_table|rotation_exact|search), residual, dx, dy, ok, relaxed: bool, attempts[{nf, W, reason}]}`, 행별 Euler 결과, `W_requests[{device, W_new, reason}]`. 하한 > 상한이면 다른 finger_w·nf, 그래도 안 되면 W_request(R 331행).

---

## 4. 계산 재사용 설계 상세

### 4.1 캐시 표 [제안]

| 대상 | 위치 | 키(내용 지문) | 무효화 | 상한 | 수명 |
|---|---|---|---|---|---|
| LUT 점 조회 | `lut/query.py` | (lut.fp, kind, field, L, vgs, vds, vsb의 `float.hex`) | LUT 파일 바뀜 | N3.5 식 × 블록별 첫 평가 실측 조회 수 | 실행 |
| gm/ID 곡선 표 | `lut/curves.py` | (lut.fp, kind, L, vds, vsb) | LUT | 곡선 수 = 격자 L×VDS×VS 상한(계산) | 실행 + 디스크(E3) |
| VGS 역산 | `lut/inverse.py` | (곡선 키, gm_id) | LUT | 위와 같은 방식 | 실행 |
| tol_V(LOO) | `lut/tolerance.py` | lut.fp | LUT | 1 | 디스크(E3) |
| VDsat·gmb·knee | `lut/vdsat.py`·`gmb.py`·`sizing/block_lengths.py` | (lut.fp, kind, L, gm_id 또는 창, vsb) | LUT | 계산 | 실행 |
| finger_w DC 슬라이스 | `lut/slices.py` | (pdk.fp, model.fp, kind, finger_w) | 모델·PDK | 슬라이스 수 | 디스크(E3·E5) |
| topology·spec·PDK 로드 | `authoring/*`, `core/pdk_decl.py` | 파일 바이트 sha256 | 파일 바뀜 | 회로 수 | 실행 |
| S1 + 인덱스 | `graph/s1_build.py` | (topology.fp, rule.fp, supplies_v.fp) | 셋 중 하나 | 회로 수 | 실행 |
| 구조(S1v·stage·루프·기둥·발동표) | `graph/*` | (S1.fp, view 정의 fp) | S1·spec metric 선언 | 회로×뷰 | 실행 |
| GB4 상한표 | `metrics/achievability.py` | S0.fp | S0 | 1/S0 | 실행(7b 재계산은 필터, P 461) |
| `KernelContext` | `search/kernel.py` | S0.fp | S0 | 1/S0 | 실행 |
| 블록 ②③④⑤ | `sizing/block_*.py` | (블록 코드 해시, 투영(θ 성분·읽는 `dc` 필드) fp) | 읽는 성분 변화 | N3.5 식 | 실행 |
| 봉인 결과 | `sizing/seal.py` | S2Dc.fp | 스냅샷 | N3.5 식 | 실행 |
| `ss`/`ls` | `metrics/ss_linearize.py`·`ls_fields.py` | SealedSnapshot.fp | 스냅샷 | N3.5 식 | 실행 |
| MNA 조립 | `metrics/mna_build.py` | (Ss.fp, view.fp) | 그 둘 | N3.5 식 | 실행 |
| MNA ω 풀이 | `metrics/mna_solve.py` | (조립 fp, ω) | 조립 | ω 격자 수 × 조립 수 | 실행 |
| metric 전부 | `metrics/registry.py` 경유 | (SealedSnapshot.fp, metric 코드 해시) | 둘 | 스냅샷당 1 | 실행 |
| 감도 게이트 | `metrics/sensitivity_gate.py` | (S0.fp, metric 코드 해시) + 최종 해 | 둘 | 1 | 실행 (DEC-74) |
| 평가 결과(성공·실패) | `search/eval_cache.py` + S3 | (θ `float.hex`, S0.fp) | S0 | N3.5 식 | 실행 + 디스크 S3 |
| 층 0 국소 해 | `search/layer0_local.py` | (블록 id, gain bin, 고정 입력 fp, S0.fp) | 그 넷 | DEC-71 (6) 상한 | 실행 |
| ε-제약 풀이 | `search/eps_sweep.py` | (ε, 시작점 fp, S0.fp) | 그 셋 | ε 점 수 | 실행 |
| Euler·box 판정 | `layout/euler.py`·`box_shape.py` | 행의 (소자, kind, nf) 정렬 튜플 | 그 튜플 | 행 수 × 시도 | 실행 |
| 패턴 결과 | `layout/patterns.py` | (멤버, nf 튜플, n_rows) | 그 셋 | 그룹 × 시도 | 실행 |
| finger_w 후보 | `layout/finger_geometry.py` | (행 W 튜플, 격자, tol 튜플) | 그 셋 | 행 × 시도 | 실행 |
| W_request 재평가 | `convergence/loop.py` → `search.evaluate` | 고정 W가 θ 투영에 들어간 평가 키 | 고정 W | K_max | 실행 |
| SPICE 오라클 결과 | `tools/spice_oracle` | (넷리스트 sha256, 모델 fp, 해석 명령) | 셋 | 디스크 | 디스크 |

상한 원칙: 숫자 상수 없음 -- N3.5 식(P 412)으로 '그 실행에서 가능한 고유 키 수'의 상계를 계산하고 그 이상은 LRU. 정상 실행에서 퇴출 0이 되도록 상한을 잡고, 퇴출이 나면 보고(E2).

### 4.2 루프 불변식 배치
- 실행당 1회: PDK·LUT 로드, LUT 파생표(tol_V·곡선), topology·spec 로드.
- S0당 1회: S1·구조·GB4 상한표·`KernelContext`·감도 게이트.
- 후보 θ당: 블록 ②~⑤(투영 키로 부분 재사용)·봉인·`ss`/`ls`·MNA 조립 1회·metric.
- ω당: MNA 풀이만(조립 재사용, 세션47 28% 사례).
- 레이아웃 시도당: 기하 판정만. 전기 재계산은 W_request가 있을 때만(SD 참고문서 §9.5 "row_split 재시도는 gm/ID 그리드서치와 분리").

### 4.3 옛 엔진의 '같은 값 반복 계산' 사례와 차단

| # | 사례(근거) | 실측 | 새 엔진 차단 |
|---|---|---|---|
| 1 | 헤드룸 함수가 호출마다 `load_topology()`(H 2985) | 평가 비용 99.3%, 0.142 s→0.001 s | 로더는 파이프라인 시작 1회, `KernelContext` 밖에서 호출 불가(계층: sizing은 authoring 결과 객체만 받음) + `test_kernel_context_built_once_per_s0` |
| 2 | AC 응답이 ω마다 네트워크 재조립(H 2986) | 28%, 0.371 s→0.024 s | `mna_build`/`mna_solve` 파일 분리 + 조립 키에 ω 없음 |
| 3 | LUT `_query` 18,636회 중 12,891회 중복(H 2987) | 69.2%, 합계 평가 1,325→72.9 ms(18배) | `lut/query.py` memo + 곡선 표 선계산 |
| 4 | SLSQP 811회 중 784회 중복, 실패 미캐시(H 12.3 #2) | 71 s 중 55 s 무진전 | 실패 포함 평가 캐시 + margin(N3.14) |
| 5 | `propagate_node_voltages` 평가당 19회, 고유 인자 7(H 12.3 #4) | -- | 노드전압은 S2Dc 한 번 생성, 읽기만 |
| 6 | FD 한 스텝에 바뀐 소자 6.7/51인데 전부 재계산, 조인트 스캔 66%(H 12.3 #6) | -- | 투영 키 블록 memo |
| 7 | row_split 재시도마다 전체 최적화 재실행(SD 참고문서 §9.5) | 10분+ 무응답 | 레이아웃 기하 루프와 W_request 전기 루프 분리 |
| 8 | `_solve_vgs` 3중 재계산(메모리 세션30·31) | -- | 역산은 `lut/inverse.py` 한 곳 + memo |
| 9 | 캐시 상한 도달 시 캐싱 중단(DF-07), `id(lut)` 키·상한 없음(DF-13), Rz 캐시 키가 소자명뿐(DF-15) | -- | 레지스트리 단일화·지문 키·lint |
| 10 | 반대 방향 결함 -- **낡은 값 재사용**: vsb만 고치고 W·gds는 옛 vsb(DF-01, H 12.3 #3: 7/51 소자), 레이아웃 W 변경 뒤 sizing W 미갱신(LP §3 W1: 29/51) | -- | 불변 스냅샷 + 입력 버전 기록(SC-b) + 봉인 4(버전 일치) |
| 11 | presolve 16.5 s를 L 조합 루프 안에 둘 위험(H 601) | -- | S0당 1회 단계로 배치 |

### 4.4 계측
- 실행마다 결과 JSON `perf`: 블록별 `hit/miss/evict/recompute_same_key`, 평가 수, 평가 시간 중앙값, `KernelContext` 생성 수, wall-clock(C00 §10.3 필드 이식).
- `--profile <path>`: cProfile 통계를 파일로(누적 상위 함수·호출 수). 계획 NFR-2·6b의 '첫 작업 cProfile'은 **새 커널**에 대해 K4 완료 시점에 1회 기록하고, 층 구성 결정(R D18)의 근거로 쓴다(C7).
- 중복 인자 추적기 `core/instrument.py` `DupArgTracer`: `@hot` 표시 순수 함수(LUT 조회·역산·MNA 풀이 등)의 (함수, 인자 지문) 호출 수를 센다. memo를 통과한 '실제 계산' 호출만 센다.

### 4.5 계측을 test로 고정 [제안]

| test | 입력 | 판정 |
|---|---|---|
| `test_memo_key_covers_reads`(IC10) | 합성 블록: 선언 read 필드 하나만 바꾼 투영 | miss 1, 같은 내용 다른 객체 → hit |
| `test_compute_block_rejects_mutable` | dict·ndarray 인자 | `TypeError` |
| `test_no_unregistered_cache` | 엔진 소스 AST | 모듈 전역 dict/list 캐시, `lru_cache(maxsize=None)`, `id(` 키 0 |
| `test_kernel_context_built_once_per_s0` | 파일럿 θ 여러 개 평가 | 생성 계수 = 1 |
| `test_fd_step_recomputes_only_impact_set` | θ 한 성분 FD 섭동 | miss 블록 집합 = 그 성분을 읽는 블록 집합(구조 유도 기대값, 손계산 회로) |
| `test_no_duplicate_recompute_pipeline` | 작은 회로 E2E(`two_stage_ota` 또는 `common_gate_amplifier` -- 회로 선택은 실행 시간 실측 뒤) + 파일럿 평가 1회 | 모든 블록 `recompute_same_key == 0`, 퇴출 0이면 PASS(퇴출 정책 E2) |
| `test_dup_arg_trace_hot_functions` | 위와 같은 실행 | `@hot` 함수의 같은 인자 '실제 계산' 2회 이상 = 0 |
| `test_mna_assembly_not_per_omega` | 주파수 응답 1회 | 조립 계수 1, 풀이 계수 = ω 수 |
| `test_layout_retry_no_electrical_recompute` | W_request 없는 레이아웃 재시도 | `search.evaluate` 호출 0 |
| `test_profile_artifact`(slow) | 파일럿 E2E `--profile` | 프로파일 파일 생성·상위 함수 표 출력(시간 임계값은 두지 않음 -- 기계 의존) |

시간 수치는 판정에 쓰지 않는다(기계 의존). 계수(호출 수·miss 수)만 판정한다.

---

## 5. 계획서 안의 충돌·오늘 결정과 어긋나는 문장, 정정 제안

### 5.1 계획서(P) -- 24건

| # | 위치(행) | 문장 요지 | 충돌 대상 | 정정 제안 |
|---|---|---|---|---|
| C1 | N1.2 P 160 | "레이아웃 알고리즘 변경 -- MOD7로 옮기기만 한다" | 오늘 레이아웃 규칙 (c) 채택(W 보존·W_request·패턴 선행·행별 finger_w·차동쌍 완화 순서) | 범위 밖 행 삭제, 범위 안에 '레이아웃 규칙(사용자 2026-10-07)' 추가, LR8·LR9와 연결 |
| C2 | N3.10 P 515~535 | MOD = 단일 파일, 이관 목적지 열 정본, 이동 규칙·shim | 새 패키지·추가 대원칙(파일 분할) | MOD = 하위 패키지, 파일 = 한 개념, `_module_map.py` 정본, 이동·shim 문단 삭제, core(층 0) 추가 |
| C3 | N3.1 P 318·319(GB4·GB5 모듈 = MOD4) | GB4는 블록 국소 소신호 모델(N3.8 P 489, MOD5), GB5는 MNA에서 극점·영점 조립(P 480) | P 517 "import는 번호가 작은 쪽으로만" -- MOD4가 MOD5를 부르는 계층 위반 | GB4·GB5 모듈 열을 MOD5로(또는 MOD5와 MOD6 사이 하위 패키지). 3.1 표 반영 |
| C4 | LR3 P 507 | LUT 축 밖 = 구조화 실패 SEAL_VIOLATION | C00 §7.1 "N3.14 예외는 MOD4 이상에서만 raise", MOD1은 MOD4를 import 불가 | 실패 클래스를 core 층 0으로(C00 §7.1 개정) |
| C5 | NFR-2 P 182, N6.2 6b P 1024 | "계측 도구는 test-author 소유" | N6.3 P 1034·C00 §10 "계측 도구는 code-author 소유, 그 test는 test-author" -- 계획 내부 모순 | N6.3 쪽으로 통일(도구 = 코드 작성 주체, 도구 test = test 작성 주체) |
| C6 | NFR-2 P 182 | "LRU 퇴출로 인한 재계산은 퇴출 기록과 함께 별도 집계"(허용) | 사용자 대원칙 "값이 변하지 않는 한 재사용" | 상한을 실행의 고유 키 상계로 계산해 정상 실행 퇴출 0을 합격 기준으로, 퇴출 시 처리는 E2 결정 |
| C7 | NFR-2 P 182, N6.1 6b P 1006, N6.2 P 1024 | 6b 첫 작업 = 옛 `_evaluate` cProfile, 그 전에는 탐색 층 증감 결정 금지 | 옛 엔진은 참고용, R D18(층 0 최소형)은 계측 전 결정 | 대상을 새 커널로 바꾸고, D18은 '새 커널 cProfile 뒤 확정'으로 조건부화 |
| C8 | N3.5 P 404(SC-a 전환기 writer)·P 410(6b~7a 전환기 경로, `sizing_recipe.py _evaluate 8697행`) | 전환기 커널 순서 | 새 엔진은 처음부터 7b 순서 | 전환기 문장 삭제 |
| C9 | N3.5 P 416 | Phase 5~6a 임시 지문 | 새 엔진은 S0가 처음부터 있음 | 삭제 |
| C10 | DEC-26 P 221, N3.10 P 530·532 | `run_harness.canonical_spec()`만 정본, `SPECS`는 `workspaces/run_harness.py`에 남음 | 하네스는 `legacy/workspaces/`로 이동, 새 엔진은 회로 spec 파일(R D5) | spec 정본 = 회로 spec 파일, `derived_spec(why)` 규칙만 유지 |
| C11 | DEC-60 P 254, N3.4 W0 P 388, N3.16 P 772 | 스칼라 `vdd` 전환기 전압 해석(MG1까지) | 새 엔진에 MG1 없음 | `supplies_v` 필수, 전환기 문장 삭제(9회로 값 표기는 DP 묶음 B) |
| C12 | DEC-69 P 263, N3.16 P 801~806 | MG0~MG3 단계 마이그레이션 | 새 로더는 정본 이름만 | 단계 표를 '로더 스키마 = 정본 이름, 옛 이름 거부'로 대체(정본 이름 표 P 769~799는 유지) |
| C13 | N3.15 P 753~763, N6.1 7b P 1009 | `sizing_spec.json`은 7b, topology 필드 이관 절차 | 새 엔진은 처음부터 spec 파일 | Phase 표기 제거, 이관 절차 삭제 |
| C14 | 용어집 P 124, DEC-47 P 241 | '사이징 대상 회로 = 현재 기존 4개' | 합격 범위 9회로 | 정의를 '스펙이 선언된 library 회로'로만 두고 '현재 4개' 문구 삭제, 9회로 스펙 선언은 DP 결정 |
| C15 | N3.11 P 540 | test 경로 `assets/tests/` | 옛 test는 `legacy/tests/`, 새 test는 `gmid_engine/tests/` | 경로 갱신 |
| C16 | N3.12 P 567~723, DEC-37~42 P 231~236, N4.2 P 833~848, N4.3 P 850~895, N6.1 0.5 P 999, N0.1 P 23(보고 수치는 판정 기록에서만), N0.4 P 114~118(오케스트레이터·spec card·판정 기록), U-15·U-38·U-40 | 역할 분리·gate | gate 꺼짐(사용자 2026-10-07) | 계획서에서 '보류(gate 꺼짐)' 절로 묶어 내리고, 이식할 판정(lint·자기참조·도달)은 1절 일반 test로 |
| C17 | DEC-75 P 269 | "이 분기는 V6 lint 예외로 등록" | V6 없음 | `test_numeric_literals_derived`·`test_no_skip_branches`의 예외 목록 1곳으로 |
| C18 | U-34 P 1111 | `_paper_target_spec`의 `sky130_supplies_v` = 1.8 V | 파일은 MG0 뒤 `_declared_target_spec.supplies_v`(DP 14행 실측) | 문언 갱신 |
| C19 | DEC-79 P 273(판정 축 정본 = 레이아웃 면적, MOD8 루프), N6.1 7b P 1009 | 정본 유지 | R D4(판정 축을 탐색 축으로 축소, MOD8 범위 밖) -- 오늘 W_request 규칙 채택으로 MOD8 루프가 필요해짐 | D4 재검토(E4): MOD8은 범위 안, 판정 축 재필터 범위는 E4에서 |
| C20 | DEC-80 (i) P 274, N3.16 P 796, U-30 P 1107 | PDK 선언은 Phase 4 '한 곳 선언'(규칙 번호 출처) | 오늘 tlef 설치·`MANUFACTURINGGRID` 파싱(사용자) | `core/pdk_decl.py` 한 곳에서 tlef 격자 + 규칙 문서 값 + 수동소자 단위 면적을 출처와 함께 읽는다고 명시 |
| C21 | N3.6 P 439 | tol_V 방법 원천 `tests/probe_interp_scheme_loo.py` | 파일이 `legacy/tests/probes/`로 이동(추측 -- 정확한 하위 경로는 미확인) | 원천 경로 갱신, `lut/tolerance.py`가 정본 |
| C22 | N5.2 DF 표 P 907~949 '수정 Phase', N6.1 Phase 4 P 1003 | 옛 엔진 결함을 Phase 4에서 수정 | 옛 엔진 동결 | DF를 '재발 금지 계약' 열로 바꾸고 새 엔진 test 이름을 적음 |
| C23 | N9.1 P 1149~1170, DEC-51 P 245 | design 13문서, 각 문서 사용자 승인 | 05·10·20·30 무의미, 6a~7c 미작성, 가벼운 절차 | 문서 목록 축소, 승인 단위는 E7 |
| C24 | N6.3 P 1034 | 성능 측정 명령은 C00 §10(`assets/tests/tools/measure_search_perf.py`, 하네스 `run()`) | 경로·진입점 무효 | 새 진입점 `--profile`·결과 JSON `perf`로 대체(4.4) |

### 5.2 초안 문서(_drafts) -- 8건 (계획서 밖, 같은 오늘 결정과 어긋남)

| # | 위치 | 문장 | 정정 |
|---|---|---|---|
| D-a | R 93행(1.1 'W 정본') | "W = n_fingers × W_ref ... 레이아웃 어댑터는 W를 바꾸지 않는다" | R 317행 정정절대로 '총 W 보존, finger_w는 레이아웃이 고름'으로 본문 수정 |
| D-b | R 166행 K3 | "W = n × W_ref(D2)" 완료 조건 | 총 W 계약 + 허용오차로 |
| D-c | R 238행 D2 | 'finger 폭 = W_ref' 결정 항목 | 삭제(R 325행 정정 5와 같음) |
| D-d | R 276행 마일스톤 순 5 | "W = n × W_ref 하나(레이아웃이 바꾸지 않음)" | 수정 |
| D-e | R 18행·53행 | "MOD7은 옛 `stick_diagram.py`를 어댑터로 부름" | 2.2 복사 기본안(옛 엔진 삭제 가능성 유지) |
| D-f | LP 172행 (c)1 | "`max_snap_error`(예: 1%)" | tol_V × gm/ID 상한, 격자/(2 finger_w) 하한 |
| D-g | LP 174행 (c)3 | "차동쌍 common-centroid는 완화 금지" | 사용자 2026-10-07: nf·W 조정 모두 불가 시 완화 허용 + 기록 |
| D-h | LP 185~191행 계약 | `grid_step_m 5e-9`, `min_finger_w_m 4.2e-7`, `max_finger_w_m 4e-5`, `W_tol_rel 0.01` 리터럴 | PDK 선언·계산값 참조로(3.3). `max_finger_w`는 PDK 출처 미확인 [추측: 옛 엔진 상수] |

---

## 6. 열린 결정 항목(사용자 몫) -- DP(36칸·3.1 판정 정의·J 묶음)와 R 4절 D1~D18에 없는 것만

| # | 결정 | 기본안(원칙에서 유도) | 왜 사용자 몫인가 |
|---|---|---|---|
| E1 | 계획서 개정 일괄 승인: 5.1의 24건 정정 반영(누가·언제) | 정정안대로 한 번에 개정, gate 관련은 '보류' 절로 이동(삭제 아님) | 계획서 확정 결정(DEC·NFR) 변경 |
| E2 | memo LRU 퇴출 정책: 정상 실행 퇴출을 (a) 합격 실패로 볼지 (b) 보고만 할지 | (a): 상한을 고유 키 상계(N3.5 식)로 잡아 퇴출 0이 정상, 퇴출이 나면 상한 식 결함으로 FAIL. 메모리 부족 시에만 (b)로 | NFR-2(P 182)의 '퇴출 재계산 허용'과 대원칙의 충돌(C6) 해소 방향 |
| E3 | 실행 간 디스크 캐시 허용 범위: LUT 파생표(tol_V·곡선·슬라이스)·SPICE 결과·S3를 디스크에 두고 재사용할지, 위치(.gitignore 대상 `runs/cache/` 등) | 허용. 키 = 입력 파일 sha256 + 엔진 패키지 소스 해시(코드가 바뀌면 자동 무효). 위치 `skills/analog-gmid-design/gmid_engine/.cache/`(gitignore) [제안] | "한 번 계산한 값은 재사용"을 실행 간까지 넓힐지, 디스크 사용·저장소 규칙 |
| E4 | MOD8 W_request 수렴 루프를 1달 범위에 넣을지와 면적 판정 축 재필터(DEC-79 (b)) 범위 -- R D4·D18 재검토 | MOD8 루프는 범위 안(오늘 레이아웃 규칙이 요구). 판정 축 재필터는 보고만(레이아웃 면적을 front 표에 병기). 일정 영향 약 +15~25 h [추측] | 범위·일정 |
| E5 | 레이아웃 finger_w 후보 집합: (a) 미리 특성화한 DC 슬라이스 폭(PDK bin 폭 등)으로 제한 (b) 레이아웃이 고른 임의 폭을 그때 ngspice로 특성화(디스크 캐시) | (a) + 필요 시 (b) 1회 추가: (a)는 실행 중 SPICE 의존이 없고, (b)는 box 자유도가 크다. lut_coverage_study 표 A(nfet 폭 의존 −28%~+170%) 때문에 무보정 임의 폭은 금지 | 정확도·레이아웃 자유도·실행 시간의 절충 |
| E7 | design 승인 단위(가벼운 절차에서 DEC-51): R D0~D4 인터페이스 명세를 (a) 한 번에 승인 (b) 문서마다 승인 | (a) D0(공통 인터페이스·이 문서 3절)만 승인받고 D1~D4는 구현과 함께 갱신, 인터페이스 변경 2회 초과 시 보고(R R2) | 승인 절차 |

결정 개수: **6개(E1~E5, E7)**. 파일 크기 상한 항목(옛 E6)은 사용자 지시(상한 두지 않음)로 삭제했고, 대신 파일 구성 규칙 A~D(1.2)는 오케스트레이터가 사용자에게 올린 승인 대기 안이라 이 목록에 다시 넣지 않았다.

---

## 7. 구현 순서 (ROADMAP과 정합)

R 0.2 순서(GB0+S0/S1 → GB1 → GB2 → GB7 → GB8 핵심 → GB4 축소 → GB5 → GB6 → GB9 SPICE)를 유지하고 아래 차이만 둔다.

| 순 | 단위 | R 대응 | 차이와 이유 |
|---|---|---|---|
| 0 | **core 층**(`fingerprint`·`memo`·`failures`·`units`·`determinism`·`pdk_decl`·`instrument`) + `_module_map.py` + 구조 test 묶음(1절: 계층·순환·공개 API·지도·파일 구성 규칙 A~D·이름 리터럴·숫자 리터럴·except·self-test·캐시 lint) | R D0 '패키지 골격'에 포함 | **명시적으로 맨 앞**: 재사용·파일 분할 대원칙을 이후 모든 단위가 지키게 하는 장치라 뒤로 미루면 옛 엔진처럼 사후 덧대기가 된다(H 5037 "캐시는 전부 사후에 하나씩 덧댄 것") |
| 1 | K1 LUT(MOD1) + tol_V + gmb + VDsat + 축 밖 거부 | K1 | 같음. `lut/query.py` memo·`curves.py` 선계산을 이 단위 완료 조건에 |
| 2 | N1 GB0 로더·게이트(MOD2) | N1 | 스칼라 vdd 폴백 없음(C11) |
| 3 | N2~N9 구조(MOD3) | N2~N9 | 같음. 파일 단위는 3.1 표 |
| 4 | K2 GB7 DC 정본·봉인(MOD4) | K2 | 계산 블록 파일 4개 + `seal.py`, `@compute_block` 투영 키 |
| 5 | M1 `ss`·MNA·전력·면적(MOD5) | M1 | `mna_build`/`mna_solve` 분리 |
| 6 | K3·K4 커널(`KernelContext`)·결과 JSON·진입점 + **새 커널 cProfile 기록** | K3·K4 | cProfile을 여기 고정(C7), 4.5 test 묶음 활성 |
| 7 | K6 GB4 축소·K7 GB5(**MOD5에 배치**) | K6·K7 | 모듈 배치만 다름(C3) |
| 8 | K8 GB6(층 0 최소 + 외층 + ε 두 방향 + 비지배 필터) | K8 | 층 0 범위는 6의 cProfile 뒤 확정(R D18 조건부) |
| 9 | **L1 레이아웃(MOD7: 계약·W 허용오차·패턴 복사·행 구성)** + **L2 MOD8 W_request 루프** | 없음(R D4는 범위 밖) | **추가**: 오늘 레이아웃 규칙(사용자 채택)이 요구. E4 결정 대상. 파일럿 마일스톤에서는 W_request 0을 목표로 보고만 |
| 10 | K5 9회로 확장 DC(3레일·IC11·CD W2·`kvl_branch`·K8) | K5 | 같음 |
| 11 | P1~P7 SPICE 오라클·회귀, closure Z1~Z9 | 같음 | SPICE 결과 디스크 캐시(E3) |

일정 영향 [추측]: 0단위 core·구조 test 약 +8~12 h(R D0에 일부 포함), L1·L2 약 +15~25 h → R 합계 452 h 대비 약 +5~8%. 처리 용량 한계 기준(R 2.7) 달력 영향 약 +2~4일. 1달 목표 안에서 흡수 가능 여부는 R 6절 판단 규칙(4주 끝 마일스톤 1)으로 다시 잰다.


## 확정 사항 (사용자 2026-10-07) -- 이 절이 앞 절의 캐시·결정 항목보다 우선한다

1. **단일 정본 = Circuit State Graph(S0~S3).** 설계 상태(S1 구조, S2 dc/ss/ls 의 노드전압·가지전류·소자 op·gm·gds·용량, metric, 레이아웃 결과)는 graph 필드로만 존재한다. 필드마다 writer 1개, 값과 함께 그 값을 만든 입력 버전을 기록한다 -- **필드가 곧 캐시**(입력 버전이 같으면 재사용, 다르면 그 필드만 재계산). 별도 캐시 레지스트리에 설계 값을 두지 않는다.
2. **불변 스냅샷 + 구조 공유.** 갱신은 바뀐 노드만 새로 만들고 나머지는 이전 스냅샷과 공유. 현재 정본 = 채택된 스냅샷 포인터. 최적화 후보는 각자 스냅샷(제자리 수정·되돌리기 금지).
3. **S3 = 설계점 단위 기록**(계획 N3.3 371행): evals 요약(θ, ok/fail, 실패 분류, margin, metric, 제약 여유) + runs(θ*, front 점 목록). front 점과 채택 해는 S2 전체 스냅샷 참조를 보관(구조 공유), 나머지 평가는 요약만(θ로 결정론적 재생성 가능). 조회 함수 `node_across_front(node)`. 저장은 계획대로 `search_archive/<S0 지문>/`.
4. **graph 밖은 LUT 조회 memo 하나뿐**(공정 성질, 입력값 키, 불변 결과). LRU 퇴출은 이 memo 에만 적용, 상한은 한 평가 sweep 작업 집합으로 계산, 실행 내 같은 키 재계산 0 test.
5. **강제 test:** 계산 블록은 graph setter 로만 결과를 쓴다(모듈 수준 dict·전역 캐시 lint FAIL), 필드 writer 둘이면 FAIL, 입력 버전 같은데 재계산하면 FAIL.
6. 결정 기본안 승인: E1 계획서 개정 일괄(gate 절 폐기 표시, 충돌 24건 정정), E3 디스크 캐시 = S1 스냅샷·LUT 파생 표(지문 키) + 실패 캐시, E4 W_request 루프 범위 포함, E5 finger_w 후보 = PDK 특성화 폭 슬라이스(보간 금지), E7 MOD 별 짧은 design, 사용자 승인은 회로 해석 항목만. **범위 보강(사용자 2026-10-07 reference 검토 Q12 (iv), 계획 DEC-51)**: 구현이 끝난(9회로 합격을 낸) 공유 계산 블록(core·sizing·metrics·search 등)의 알고리즘을 바꾸면 9회로 전후 결과 차(노드전압·front·SPICE verdict)를 붙여 보고하고, SPICE verdict가 하나라도 바뀌면 사용자 확인을 받는다.
7. **L은 같은 PDK 모델 bin 안에서만 선형 보간**(사용자 2026-10-07 "나로 하자.", 같은 날 'L 앵커 이산값만'을 대체 -- 계획 N3.9 LR3·N3.6·U-27, worktree `plan-rev3` 커밋 `86115b1`). L = bin 선택(이산) + bin 안 연속. bin 경계를 넘는 보간·외삽 거부. bin 지도는 PDK 모델 파일 `lmin`/`lmax` 파싱(하드코딩 금지), L 점의 bin 소속은 시뮬레이터가 실제로 고른 bin(ngspice-46 실측: 경계값은 아래 bin). LUT L 격자 = 옛 12점 + 빠진 bin 경계 0.18·2·8·20 µm + 불연속 경계(기본안 0.18·0.25)의 반대쪽 bin 끝점 0.185·0.255 µm = 18점(30점 제안 철회). tol_V에 bin 안 L 방향 LOO 추가(2점 bin은 검증 중점). 영향: MOD1 `query.py`·`tolerance.py`의 'L 앵커 일치만' 계약(`gmid_engine/lut/CONTRACT.md` r2 4.0·`lut_l_not_anchor`)은 개정 대상이다. 외층 SLSQP는 bin 고정 L 연속, 이산 격자(LR5·DP) 후보는 LUT L 점. 근거·실측은 `lut_regen_plan.md` 0·1.2a·2절.
8. **reference 검토 Q1~Q12 추천안 일괄 채택**(사용자 2026-10-07 "B는 추천대로 해." -- 계획 worktree `plan-rev4` 커밋 `defdc24`, DEC-87~96, 질문·근거 `reference_review/SYNTHESIS.md` 2절). 이 절의 앞 항목과 앞 절(캐시·결정 항목)보다 우선한다:
   - LUT: 축별 저장 도함수 cubic-Hermite(VGS: ln ID + GM/ID 기울기, VDS: GDS/ID 기울기, VS 선형, L bin 안 선형), 같은 칸 역산, FC 검사(DEC-87). tol_V = 같은 방법 LOO를 2^p 환산 + 칸 중앙 ngspice 표본 test. 재생성 열 VDSAT·GMBS·CDD·CSS, 잡음 열 `SVG2_1HZ`·`SVG2_HF`, L 상한 20 µm, 생성기 수정, 앵커 kind 공통. 전 폭 AC·잡음 실행은 나중(U-27).
   - 외층 θ: 쓰기 소자 좌표 = ln IDu(gm_id는 파생 보고), 봉인 2 = ID 환산 지표, 봉인 7 = `VDS − VDsat ≥ +tol_VDsat`(VDSAT 열, 2/(gm/ID) 대체 금지)(DEC-88).
   - 레이아웃: (ID, gm/ID, L) 보존, 실현 W = ID/J_slice(fw), 허용오차 = max(상한, 하한) 후보 순위 기준 + '격자 지배' 기록, MOD7 결과마다 실현 기하로 커널 1회 + 봉인 재실행 후 freeze, diode도 노드전압·봉인 재계산, SPICE 합격 기하 = MOD8 수렴 스냅샷, 3열 기록(DEC-89, LY1·LY2·LY7·LY8).
   - SPICE 합격: 전도 예측 MOS가 꺼지면 FAIL(`off_current_A` 엔진 계산), CMRR·PSRR 판정, 슬루·정착 기록만, `spice_unverifiable[]` 사전 출력(DEC-90). 접합 용량 포함·Euler 공유 확산·PDK 접합 파라미터 정본(DEC-91).
   - GB5: 보상 수동소자 = θ 연속 + 전회로 MNA 판정, Rz = 구조 규칙 1/Σgm(J7) + θ 폴백, 근사식은 시작점·`comp_approx_gap`만(DEC-92).
   - matching·면적: role 5종(`diff_pair`·`mirror`·`branch_symmetric`·`bias_distribution`·`feedback_shared`), 레이아웃엔 앞 셋만, 행 접기는 비매칭 행만 자동, box 하드 게이트 없음(판정 축 면적이 목적), 판정 축 면적에 dummy·tap·well 포함, hub 병합은 면적 비교(DEC-93, LY4·LY5·LY9~LY11, J14).
   - 입력 게이트: gate 전용 바이어스 넷 선언 필수(6회로 정정 대기열), `source_manifest` 대조, 파일럿 CL1·CL2 각각 1 pF(DEC-94). follower body는 사용자 답 대기.
   - 탐색: LR10 bin 벡터 처리, ΔA_tie = 격자 × max(bbox 변), 종속 소자 구조 우선순위 + 이름 전단사 metamorphic, 시간 예산 보류(DEC-95).
   - 범위·보고: `nqs_ratio`·`mismatch_sigma_v` 보고(제약은 선언 시만), 합격 = TT 27 °C, 9회로 잡음·왜곡 스펙 없음, DRS 8섹션 결과 JSON 키는 범위 안·HTML은 마일스톤 뒤, 회로도 좌표 = S1 자동 배치(DEC-96).
9. **MetricSignature 어휘 통일**(사용자 2026-10-07 "A는 기본안으로 승인할께.", 계획 DEC-53·N3.16): `unit` ∈ `core/units.METRIC_UNITS`(`mv` 추가), `domain` ∈ `core/units.DOMAINS` 하나(`METRIC_DOMAINS` 삭제), `view_kind` ∈ None·transfer·loop·output_port·ratio(MOD5 레지스트리 어휘, 상수 한 곳), `objective_axis` ∈ `OBJECTIVE_AXES`. `pm_ss_deg` = loop, `rout_ss_ohm` = output_port, `area_search_m2` domain = geom. loop·output_port 뷰 제약은 7a design의 뷰 정의 전까지 pending 전용(로드는 하고 판정하지 않음).
