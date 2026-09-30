# gain-budget-gmid-sizing -- Phase 2 `20-dead-code-dup` design

버전 v1.2 (2026-09-23. v1.2에서 §5.1 복제 제거·승격 경계(사용자 결정)와 §8 P2 행 판정 유형·oracle 정정 -- P2 실측 반영. v1.1은 승인됨(`20260923-20-dead-code-dup-design`). v1.1에서 §3 NEW-TOPO·§6.4 일반성 기준 추가 -- 사용자 지시 "현재에 있는 회로만으로 삭제여부를 결정하지 말고, 향후 추가되는 모든 topology를 커버할 수 있도록 설계되어야 해"). 정본 인용 규칙은 계획 N9.4 -- 이 문서는 계획서와 `00-common`의 정의를 재서술하지 않고 절 번호로 인용한다.
읽은 계획 절(N9.1 표): N3.10, N3.11 TS6, N6.1·N6.2 Phase 2, N6.3, WP-14, DF-21·DF-23(DF-29~DF-34), U-02, N9.2·N9.4.

실측 원자료(이 문서의 모든 수치의 출처, 같은 폴더 `docs/03-analysis/gain-budget-gmid-sizing-20-dead-code-dup/`):
`d_inventory.json`·`dup_inventory.json`·`d-dup-summary.md`(D 48개·DUP 19개의 호출부 전수), `probe_inventory.json`·`df23_inventory.json`·
`probe-df23-summary.md`(probe 42개·DF-23 전수), `u02_tables.md`(아래 §9 제안표의 기계 분류판, 생성기 `mk_tables.py`).
측정 시점 = gate `master` `1e2e243`. 측정은 읽기 전용이었고 저장소를 바꾸지 않았다.

---

## 1. 범위 (N9.2-1)

계획 N6.1 Phase 2 행이 정본이다. 이 Phase가 구현하는 것:

* **TS6**(N3.11): probe 정리 -- 승격 / 삭제 / `tests/probes/` 이동, 운영 도구 `derive_achievable_bounds.py`를 `tests/tools/`로 이동, probe 안의 엔진 로직 복제를 엔진 정본 호출로 교체.
* **레지스트리 등급 D 처리**(U-02): 삭제 / `tests` 이관 / 보류(배선은 Phase 4, 모듈 이동은 Phase 3).
* **DUP 통합**: 레지스트리 §2 '상태' 열이 **행동 보존 통합 가능**이라고 적은 개념만. 실측 결과 두 개다 -- `W 계산 W=L*ID/IDu`, `KCL 엣지`.
* **DF-23 전수 목록**: 엔진 소스의 소자·넷·회로 이름 리터럴과 topology 파일 경로 전수(DF-29~DF-34 포함). Phase 2는 **목록과 기록**이고 일반 규칙으로의 교체는 Phase 4·7a다(DF-23 행).

범위 밖(명시): 동작이 바뀌는 수정 전부, `_metric_folded_cascode_*`·`_cmrr_diff_pair_tail`처럼 **데이터가 실제로 고르는** metric의 통합(레지스트리 §2 상태 '4회로 재측정 후' -- 7a), ★ 표시 개념(회로 해석 공동분석 -- 6a), 모듈 이동(Phase 3).

---

## 2. 인터페이스 (N9.2-2)

이 Phase는 새 계산을 만들지 않는다. 바뀌는 것은 **경로와 호출 관계**다.

### 2.1 test·probe 배치

| 경로 | 내용 | 쓰는 card |
|---|---|---|
| `A/tests/probes/<이름>.py` | 승격하지 않는 probe(진단 스크립트). pytest가 수집하지 않는 디렉터리 이름 -- 판정식 T(design `10-test-separation` §7)의 대상에서도 `probes/**`가 이미 빠져 있다 | P2 |
| `A/tests/unit/test_probe_<주제>.py` | 승격한 probe가 되는 pytest test | P3 |
| `A/tests/tools/derive_achievable_bounds.py` | 운영 도구 이동(code 커밋으로 추가 → test 커밋으로 원본 삭제, N3.11 TS6 문장) | P2 |
| `A/tests/fixtures/` 대신 `A/tests/unit/`·`A/tests/legacy_moved/`를 새로 만들지 않는다 | D 이관분은 **소비자 test 파일 옆**(`A/tests/unit/` 또는 `A/tests/tools/`)에 둔다 | P6 |

A = `skills/analog-gmid-design/assets`. 새 디렉터리는 `probes/`와(이미 계획 N3.11에 있는 이름) `tools/`(이미 있음)뿐이다.

### 2.2 이동·삭제 규칙

1. **삭제**: 엔진 소스에서 함수·클래스 정의와 그것만 쓰는 헬퍼를 지운다. 같은 커밋에서 레지스트리 행을 지운다(계획 N0.3 '대체하면 같은 커밋에서 옛 함수 삭제+레지스트리 갱신').
2. **이관**: 코드는 **바이트 그대로** 옮긴다(이름·본문·docstring 불변). 옮긴 뒤 import 경로만 바뀐다. code-author가 새 위치에 추가하는 커밋과 test-author가 원본을 지우는 커밋을 나눈다(N3.11 TS6의 운영 도구 이동 규칙을 이관 전부에 적용).
3. **통합**(DUP): 중복 쪽 호출부를 정본 호출로 바꾸고 중복 정의를 지운다. 정본의 시그니처는 바꾸지 않는다. 바꿔야 하면 그것은 행동 보존이 아니므로 이 Phase가 아니다.
4. **probe 복제 제거**: probe 안에서 엔진 식을 다시 쓴 곳을 엔진 정본 호출로 바꾼다. probe의 출력 의미가 바뀌면 그 probe는 이 Phase에서 건드리지 않고 목록에 남긴다(삭제·승격 대상이 아닌 진단 스크립트).

---

## 3. 판정식 (N9.2-3)

숫자를 박지 않는다(WP-03). 모두 `영역: 없음(스키마)`.

| ID | 판정 | 식 | 입력 |
|---|---|---|---|
| E-LIB | 회로 동작 보존 | ∀ 회로 c ∈ library(로드 가능한 것 전부): `load_topology(c)`와 `run_topology_pipeline(c)`의 출력이 base와 병합본에서 같다 | `A/library/*.topology.json` |
| E-INST | 하네스 동작 보존 | 사이징 스펙이 선언되고 지금 실행되는 회로(파일럿·`folded_cascode`)의 `instance.json` 키 정렬 sha256이 base와 같다(같은 경로에서 비교 -- `10-test-separation` C8 계약 5와 같은 절차) | `workspaces/run_harness.py` |
| E-AST | 이관 동일성 | 이관한 정의의 docstring 포함 `ast.dump`가 base와 병합본에서 같다 | 이관 대상 |
| DIFF-DUP | DUP 차등 | 중복 함수와 정본 함수를 **같은 입력 전수**에 돌려 출력이 같다. 입력 전수 = 그 개념이 실제로 쓰이는 library 회로의 소자·노드 전부(합성 입력이 아니라 실행 가능한 회로에서 뽑는다) | 회로 로드 결과 |
| GONE | 삭제 확인 | 삭제한 이름이 `A/*.py`·`workspaces/run_harness.py`·`A/tests/**`에서 AST 참조 0 | 병합본 |
| PROBE-DUP | probe 복제 0 | `tests/tools/engine_dup_scan.py`(P4가 만든다)가 `A/tests/probes/**`에서 엔진 정본과 같은 식의 재구현을 0건으로 보고 | 병합본 |
| REG | 레지스트리 정합 | 레지스트리 §7 D 목록의 남은 항목 집합 = U-02 승인표의 '보류' 집합, 삭제·이관 항목이 §7에 없다 | 레지스트리 |
| NEW-TOPO | **미래 topology 커버** | 라이브러리에 없는 합성 topology(새 회로 이름·새 넷 이름·소자 수가 다른 넷리스트)로 (i) `load_topology`·`run_topology_pipeline`이 base와 병합본에서 같은 결과를 내고 (ii) 삭제한 선언 키를 쓰면 **명시적 `ValueError`**가 나며(조용한 무동작·기본값 대입이 아니다) (iii) 그 키가 하던 판정을 일반 경로 선언으로 쓰면 값이 나온다 | 합성 topology(test-author 구성) |

E-LIB·E-INST는 이 Phase의 모든 card가 공통으로 낸다(계획 N6.3 '동작 보존 Phase는 실행 가능한 회로 전부에서 equivalence'). **NEW-TOPO는 삭제를 포함하는 card 전부가 낸다**(§6.4).

---

## 4. 실패 경로 (N9.2-4)

Phase 4 전이라 N3.14 실패 클래스가 없다(`10-test-separation` §8과 같은 상황). 이 Phase의 실패는 다음으로 끝난다.

| ID | 경우 | 결과 | 처리 |
|---|---|---|---|
| F1 | 삭제 대상이 실은 운영 경로에서 불린다(측정 누락) | E-LIB 또는 E-INST FAIL | 삭제를 되돌리고 그 항목을 '보류'로 옮긴다(U-02 승인표 개정은 사용자 승인) |
| F2 | 이관 뒤 import 순환·경로 오류 | V1 FAIL(수집 오류) | 이관 위치를 바꾸거나 되돌린다. 새 shim을 만들지 않는다(Phase 3 소관) |
| F3 | DUP 차등에서 출력이 다르다 | DIFF-DUP FAIL | **통합하지 않는다.** 두 함수가 실제로 다른 개념이라는 뜻이므로 레지스트리 §2 상태를 고치고(사용자 확인) 담당 Phase로 넘긴다 |
| F4 | probe 복제를 엔진 호출로 바꾸니 probe 출력이 달라진다 | 그 probe는 대상에서 뺀다 | 차이를 기록하고(결함 후보) DF 등록을 제안한다 |
| F5 | 삭제로 `workspaces/**` 진단 스크립트가 깨진다 | 판정 대상 아님(경로 밖) | 사용자 확인 사항으로 보고한다(§9 결정 필요 2) |

---

## 5. TS6 -- probe 정리

실측(42개 전수, `probe_inventory.json`): 전부 `if __name__` 없는 최상위 스크립트이고 pytest 형식은 0개다. 18개가 엔진 식을 34곳에서 다시 구현한다. 15개에 Windows 절대 경로가 박혀 있다. 산출물(`.result.txt` 등)은 `.gitignore`에 걸려 커밋된 것이 0건이다.

* **삭제(3)**: DF-21이 이름을 댄 셋이고 실측으로 근거가 확인됐다 -- `probe_mirror_common_L_wiring`(엔진에서 없앤 `_L_ROLE_MULTIPLIERS`를 읽어 import 즉시 AttributeError), `probe_node_voltage_audit`(감사 대상 `audit_vsb_consistency`가 이미 배선돼 존재 이유 소멸), `probe_vs_semantics`(읽는 필드가 `vs`→`vsb`로 바뀌어 전 소자 skip, 무동작).
* **승격(7)**: 계획 TS6 행의 일곱 후보는 전부 실재한다. **단 `probe_physical_consistency`는 그대로 승격하지 않는다** -- 엔진 호출이 1건뿐이고 `propagate_node_voltages`·`_metric_kcl_residual`·`derive_vsb_from_nodes`·레일 집합을 손으로 재구현했으며, 낡은 `vs` 필드를 `.get("vs", 0.0)`으로 읽어 한 절이 항상 무동작이다. 승격 전에 P4(복제 제거)를 먼저 적용하고, 무동작 절은 **판정을 만들 수 없으면 승격 대상에서 빼고 목록에 남긴다**(무동작 test 금지, 계획 N4.2 V7 취지).
* **이동(나머지 32)**: `A/tests/probes/`로 옮긴다. 절대 경로 15건은 이동 커밋에서 `assets_dir` 기준 상대 경로로 바꾼다(경로만, 계산 불변).
* **엔진 복제 제거**: 정본별 복제 수 -- `size_transistor` 6, `is_diode_connected` 5, LUT IDu 조회 4, `true_current_mirror_groups` 4, 레일 집합 3, 그 밖 1건씩(합 34). IDu 재구현 4건은 LUT private 멤버(`lut._query`·`lut._log_ID`·`lut._w_ref_effective`)를 직접 건드린다 -- 공개 경로(`gm_id_to_id_density`)로 바꾼다.

U-02의 '삭제 11개'는 계획서에 3개만 이름이 있다(DF-21). 나머지 8개의 정본 목록은 계획서 어디에도 없다 -- **이 design이 실측으로 대신 정한다**: 삭제는 DF-21 3개로 하고, 나머지는 이동으로 보존한다(삭제하지 않는 쪽이 되돌리기 쉽고, 이동 뒤 복제 제거로 '엔진 식 재구현 0'이라는 DoD는 그대로 달성된다). 이 해석은 U-02 승인의 일부다(§9).

### 5.1 복제 제거(P4)와 승격(P3)의 경계 (사용자 결정 2026-09-23)

계획 N3.11 TS6은 "probe 안의 엔진 로직 복제를 엔진 정본 호출로 교체"라고 적는다. 그대로 두면 **승격한 test에서도** 재구현을
정본 호출로 바꾸게 되는데, 그러면 기대값을 피검 함수로 만드는 것이라 V4 규칙 (1)에 걸린다(계획 N4.2 V4). 실측: 승격 후보 7개 중
3개가 재구현을 가진다. 그래서 대상을 나눈다.

| 대상 | 규칙 | 근거 |
|---|---|---|
| `A/tests/probes/`에 남는 진단 스크립트(P4) | 엔진 식 재구현을 **정본 호출로 교체**한다 | 진단은 판정이 아니므로 자기참조 문제가 없고, 정의가 하나여야 엔진이 바뀔 때 같이 따라간다(WP-14) |
| 승격해 test가 되는 것(P3) | 재구현을 **oracle로 유지**한다. 다만 그것이 엔진 코드를 옮겨 적은 것이면(V4 규칙 (2) '피검 식 재서술') 문헌 식이나 다른 계산 경로로 **다시 세운다** | test의 기대값은 피검 구현과 달라야 한다(계획 N3.12.3 oracle 종류 (b)) |

승격 test가 엔진과 독립 재구현을 **나란히 비교**하는 형태(대조형)라면 V4 규칙 (1)이 걸릴 수 있다 -- 그때는 C13
(`20260923-v4-decision-exempt`)이 연 `target_kind: decision` 면제를 쓰고, 승인 기록에 "재구현이 독립 방법이고 엔진 출력을
기대값으로 쓰지 않는다"를 근거로 적는다(C9 선례 `20260923-c9-v4-exempt`).

승격 후보별 실측 분류(원자료 `probe_inventory.json`, 소스 확인 2026-09-23):

| probe | 재구현의 성격 | 처리 |
|---|---|---|
| `probe_gm_id_monotonicity` | 엔진의 VGS 선택(`_solve_vgs`)과 별개로 강반전 가지 해를 세워 **나란히 비교**(대조형) | 승격, oracle 유지. V4 (1)이 걸리면 면제 승인 |
| `probe_prevention_wiring` | `gate == drain`이라는 **물리 정의**를 직접 쓴다(엔진 복제가 아니다) | 승격, oracle 유지 |
| `probe_physical_consistency` | 프로토타입 알고리즘 재현 + 레일 집합·VDD 상수 재선언. 게다가 낡은 `vs` 필드를 읽어 한 절이 무동작 | 무동작 절의 판정을 세울 수 있으면 승격, 아니면 **승격에서 빼고 진단으로 남긴다**(무동작 test 금지) |
| 나머지 4개 | 재구현 없음(엔진 정본 호출) | 승격 |

---

## 6. DUP 통합

레지스트리 §2에서 '행동 보존 통합 가능'인 개념 둘만 이 Phase의 대상이다.

### 6.1 W 계산 (P8)

정본 `size_transistor`(`W=L*ID/IDu`). 실측: **정본의 엔진 호출부가 1곳뿐이고 그 1곳이 삭제 대상 D 함수**(`converge_with_parasitics`)다 -- 정본이 죽어 있고 인라인 사본이 살아 있는 상태다. 인라인은 레지스트리가 적은 4곳이 아니라 **6곳**이다(`find_optimal_sizing:946`, `diode_vds_window:3645`, `solve_stacked_diode_pair:3723`·`:3746`, `apply_diode_self_consistent_gm_id:3873`, `make_matching_feasibility_check.check:7393`). 레지스트리 §2의 중복 셀(`feasible_gm_ids`·`search_gm_id_for_role`·`feasible_L_window`)은 현 소스와 맞지 않는다(docstring에만 남았거나 인라인 대입이 없다) -- 같은 card에서 레지스트리를 실측대로 고친다.

* 통합 방향: 6곳을 `size_transistor` 호출로 바꾼다. 정본 시그니처 불변.
* 차등 test(DIFF-DUP): 통합 전 인라인 식과 정본이 **같은 입력 전수**에서 같은 값을 내는지. 입력은 library 회로에서 실제로 나오는 (gm, gm_id, L, vds, vsb) 조합 전부.

### 6.2 KCL 엣지 (P9)

정본 `stick_diagram._kcl_and_matching_edges`. 중복 `kcl_series_union`(같은 엣지를 따로 구현, 57줄)과 `_metric_kcl_residual`의 엣지 생성부. 둘 다 엔진 운영 경로에 있다(각 2곳).

* 차등 test: library 회로 전부에서 두 함수가 만드는 엣지 집합이 같은지(집합 동일성, 순서 무관).
* 다르면 F3 -- 통합하지 않고 레지스트리 상태를 고친다.

### 6.3 이 Phase가 통합하지 않는 것

`_metric_folded_cascode_gain_db`·`_metric_folded_cascode_pm_deg`·`_cmrr_diff_pair_tail`은 선언으로 고르는 metric이고 **일반 대체가 아직 준비되지 않았다**(레지스트리 §2 상태 '4회로 재측정 후'). 통합은 7a(gain metric 통일)의 몫이다. 이 Phase는 건드리지 않는다.

### 6.4 삭제 판정의 일반성 기준 (사용자 지시 2026-09-23)

**"지금 library 9회로가 고르지 않는다"는 삭제 근거가 아니다.** 앞으로 추가될 topology가 그 경로를 고를 수 있기 때문이다(계획 N9.3 새 토폴로지 추가 절차). 삭제는 아래 넷을 모두 만족할 때만 한다.

| 기준 | 내용 | 확인 방법 |
|---|---|---|
| G-1 | **데이터 도달 경로가 없다** -- 그 함수가 선언(`circuit_family`·metric type·보상 함수 키 등)이나 파일 이름 규약으로 선택되지 않는다 | 레지스트리 등록 딕셔너리 전수와 선언 스키마를 AST로 훑어 그 이름이 값으로 등록돼 있는지 |
| G-2 | **코드 참조가 없다** -- 엔진·하네스에서 호출되지 않는다(호출자가 자기도 삭제 대상이면 사슬로 함께 본다) | `d_inventory.json`의 경로군별 참조 전수 |
| G-3 | **일반 대체가 있거나, 애초에 일반화가 불가능하다** -- (a) 회로 무관 정본이 선언만으로 같은 판정을 내거나 (b) 그 함수가 특정 회로의 파일 경로·넷 이름을 코드에 박아 두어 **다른 topology에 적용하면 틀린 값을 준다** | 대체 함수의 입력이 선언에서 오는지 확인, 또는 박힌 리터럴 위치(`df23_inventory.json`) |
| G-4 | **삭제 뒤 그 선택지를 쓰면 명시적으로 거부된다** -- 조용한 무동작·기본값 대입이 없다 | NEW-TOPO (ii). 현 엔진은 모르는 `circuit_family`·metric type에 즉시 `ValueError`를 낸다(`sizing_recipe.py:5652`·`:5875`) |

G-3 (b)가 telescopic 계열에 해당한다. `_load_telescopic_topology_cached`는 **파일럿 topology 경로를 코드에 박아** 열고(`sizing_recipe.py:5071`), 그 체인은 파일럿 넷 이름(`Vbias1`~`Vbias4`·`Vip`·`Vim`·`Vcmfb`·`Vop1`·`Vom1`)으로 31소자 부분망을 세운다(DF-29). **어떤 새 회로가 이 family를 선언하더라도 그 회로가 아니라 파일럿 값을 계산한다** -- 남겨 두는 것이 미래 topology에 대해 더 위험하다. 대체는 회로 무관 MNA `_metric_smallsignal_ratio_db`이고 입력을 선언(여기·감지 넷)에서 받는다. 삭제 뒤 그 family를 선언하면 G-4대로 등록 목록을 알려주는 `ValueError`가 난다.

반대로 G-1이 걸리는 항목(선언으로 도달 가능한데 일반 대체가 아직 없는 것)은 **현재 회로가 안 쓰더라도 삭제하지 않고 보류**한다.

---

## 7. 레지스트리 D 처리와 U-02 제안

분류 규칙(기계적, `mk_tables.py`):

| 규칙 | 조건 | 기본 제안 |
|---|---|---|
| R-0 | 저장소 전체 참조 0 | 삭제(§6.4 G-1~G-4 확인 뒤) |
| R-1 | 참조가 test·probe(+문서)뿐 | `tests` 이관 또는 보류 |
| R-2 | 엔진 참조가 있으나 호출자가 D·self-test | 소유자를 따라간다(삭제 사슬이면 삭제, 이관 대상이면 함께 이관) |
| R-3 | 참조가 `workspaces` 진단 스크립트뿐 | 사용자 확인 |
| R-4 | 운영 경로 참조 있음 | 유지 + 레지스트리 등급 정정 |

**R-0~R-4는 코드 참조만 센다.** 선언으로 고르는 경로(레지스트리 등록 값, 파일 이름 규약)는 이 계수에 잡히지 않으므로, 삭제 제안은 전부 §6.4의 G-1(데이터 도달 경로 없음)을 따로 확인한 뒤에만 유효하다. card마다 auditor가 G-1~G-4와 NEW-TOPO를 재측정한다.

실측 결과: R-0 7, R-1 18, R-2 13, R-3 1, R-4 9 (합 48). 항목별 표는 `u02_tables.md`, 근거(경로:줄)는 `d_inventory.json`.

주의: 레지스트리 §7의 제목은 '운영 경로 호출 0'인데 **9개는 운영 경로에 살아 있다**(R-4). 등급 자체가 틀린 것이므로 이 Phase가 정정한다.

---

## 8. 역할별 산출물 -- spec card 목록 (N9.2-5)

| # | id(초안) | 대상 | 판정 유형 | oracle | 산출물 |
|---|---|---|---|---|---|
| P1 | `probe-dead-delete` | DF-21 probe 3개 삭제 | test-only | (a) 구성 -- 삭제 전 실행 결과(import 실패·무동작)를 기록 | probe 3개 삭제 |
| P2 | `probe-relocate` | probe 32개 → `tests/probes/`(이동 깊이 보정 22), `derive_achievable_bounds.py` → `tests/tools/`, 절대 경로 12파일 상대화 | **equivalence** -- 도구 이동에 code 커밋과 병합이 생겨 test-only 모양(병합 0·`code_commit: null`)이 성립하지 않는다(1차 시도 auditor가 base 판 merge gate로 실측) | (c) 이동 전후 동일성. **E-AST는 쓰지 않는다** -- 경로 줄을 바꾸는 것이 목적이라 32개 전부 `ast.dump`가 달라진다. spec card 계약 2(경로 줄 말고는 base blob과 동일)·계약 3(유도 경로가 이동 전과 같은 실제 경로)이 그 자리를 대신한다 | 이동 |
| P3 | `probe-promote` | 승격 7개(또는 `probe_physical_consistency` 제외 6개) → `unit/test_probe_*.py` | test-only | (c) probe가 이미 보던 판정을 assert로 | pytest test |
| P4 | `probe-engine-dup` | probe 안 엔진 식 재구현 34곳 → 정본 호출, 스캐너 `tests/tools/engine_dup_scan.py` 신설 | test-only + 도구(code) | (a) 스캐너의 합성 입력, (c) 교체 전후 probe 출력 동일 | PROBE-DUP 0 |
| P5 | `d-delete-dead` | R-0 7 + `junction_cap` 삭제(§6.4 G-1~G-4 확인) | equivalence | (c) E-LIB·E-INST + (a) NEW-TOPO 합성 topology | 엔진 소스 축소, 레지스트리 갱신 |
| P5b | `d-delete-telescopic` | telescopic 사슬 5 + `_cmfb_amp_gain_diode_load` 삭제와 `_CMRR_/_PSRR_REGISTRY` 키 제거 | equivalence | (c) E-LIB·E-INST + (a) NEW-TOPO: 삭제한 family 선언 시 `ValueError`, 같은 판정을 일반 경로(`_metric_smallsignal_ratio_db`) 선언으로 하면 값이 나옴 | 회로 전용 경로 제거 |
| P6 | `d-move-tests` | R-1 중 test 전용 + 동반 레코드를 `tests`로 이관 | equivalence | (c) E-AST·E-LIB·E-INST | 이관 |
| P7 | `registry-grade-fix` | R-4 9개 등급 정정, §2 중복 셀 실측 반영, D 목록 갱신, E0 도구 `A/tests/tools/reg_check.py` | red-green(도구 code 커밋 -- 2026-09-30 정정, spec card `20260930-registry-grade-fix`) | (a) 도구 합성 입력, (d) 레지스트리·실측 원자료 | 레지스트리, 도구 |
| P8 | `dup-w-calc` | 인라인 6곳 → `size_transistor` | equivalence | (c) DIFF-DUP + E-LIB·E-INST | 중복 제거 |
| P9 | `dup-kcl-edges` | `kcl_series_union`·`_metric_kcl_residual` 엣지 → 정본 | equivalence | (c) DIFF-DUP + E-LIB·E-INST | 중복 제거 |
| P10 | `df23-inventory` | DF-23 전수 목록 문서화(`df23_inventory.json` 기준 266건)와 레지스트리 기록, 신규 148건의 담당 Phase 배정 | test-only(문서) | (d) 실측 원자료 | 목록 |

card 하나의 단위는 계획 N3.12.3(관찰 가능한 계약 하나)이다. P5·P6·P8·P9는 equivalence라 code·test 두 역할이 모두 움직인다.

---

## 9. 착수 조건과 사용자 결정 (N9.2-7)

* 공통(N6.1): 이 문서의 사용자 승인(DEC-51). 이전 Phase(1) DoD PASS -- 기록 `docs/03-analysis/gain-budget-gmid-sizing-10-test-separation/phase1-dod.md`(전 항목 PASS, 2026-09-23).
* **U-02**(계획 N7): 아래 세 가지를 묶어 일괄 승인받는다.
  1. **D 48개의 항목별 처리** -- §6.4 일반성 기준(G-1~G-4)을 통과한 것만 삭제하고, 나머지는 §7 분류 규칙의 기본 제안대로(삭제 R-0 7 + 사슬 7, `tests` 이관 R-1 중 test 전용, 보류(Phase 3 이동·Phase 4 배선), 유지·등급 정정 R-4 9). 항목별 표는 `u02_tables.md`.
  2. **probe 삭제 목록을 DF-21 3개로 한정**(§5). 계획서의 '11개'는 이름이 3개만 있어 나머지는 이동으로 보존한다.
  3. **`workspaces` 진단 스크립트 영향**: `check_mirror_symmetry`·`_cmfb_amp_gain_diode_load`·`SharedFingerWCandidate`는 `workspaces/**`의 진단 스크립트에서만 쓰인다. 삭제하면 그 스크립트가 깨진다. 기본안은 **삭제하고 스크립트는 그대로 둔다**(판정 경로 밖, 필요하면 그때 되살린다).
* J: 없음.

---

## 10. DoD 측정 명령 (N9.2-6)

auditor가 Phase 2 마지막 card 병합본의 격리 복제본 `<iso>`에서 실행한다. `PT`는 `10-test-separation` §10 정의를 그대로 쓴다.

| ID | N6.2 `2` 조건 | 명령 | 통과 기준 |
|---|---|---|---|
| E0 | 승인된 D 목록 처리 | `$PY <iso>/skills/analog-gmid-design/assets/tests/tools/reg_check.py --registry <iso>/docs/03-analysis/gain-budget-gmid-sizing.function-registry.md --root <iso>` (P7이 만든다) | exit 0: §7 모든 행이 엔진에 실재(삭제·이관 항목 0), `처리` 열이 '보류(Phase n)' 형식, §1 집계 = §7 행 수. (2026-09-30 정정: U-02 승인 기록에 '보류' 목록이 없어 '승인표 보류 집합과 같음'을 처리 열 형식 검사로 기계화, 도구는 게이트 변경을 피해 tests/tools에 둔다 -- spec card `20260930-registry-grade-fix`) |
| E1 | DUP 차등 test PASS 후 옛 함수 삭제 | `PT <iso>/…/tests/unit -k "dup_"` 그리고 `git -C <iso> grep -n "kcl_series_union\|_multilinear_interp_point_multi"` | 차등 test PASS, 삭제한 이름의 참조 0 |
| E2 | probe 엔진 식 재구현 0 | `$PY <iso>/skills/analog-gmid-design/assets/tests/tools/engine_dup_scan.py --root <iso>` | exit 0, 발견 0 |
| E3 | DF-23 전수 목록 | `git -C <iso> cat-file -e HEAD:docs/03-analysis/gain-budget-gmid-sizing-20-dead-code-dup/df23_inventory.json` 와 목록 항목 수 대조 | 목록이 있고 항목마다 담당 Phase가 적혀 있다 |
| E5 | 미래 topology 커버 | 합성 topology(라이브러리 밖 이름·넷)로 `PT <iso>/…/tests/unit -k new_topology` | PASS -- 로드·파이프라인 동일, 삭제한 선언 키는 `ValueError`, 일반 경로 선언은 값 산출 |
| E4 | 동작 보존 | `PT` 전체(실패 0)와 E-LIB·E-INST 재측정 | Phase 1 DoD와 같은 값(회로 9/9 로드, instance.json 해시 동일) |

---

## 11. 열린 질문 (N9.2-8)

없다. §9의 세 항목은 U-02 승인으로 닫는다(열린 질문이 아니라 사용자 결정 대기 항목이다). 실측에서 나온 다음 두 가지는 **계획서 개정 요청**으로 올린다.

1. **레일 넷 이름 리터럴 63건에 DF 번호가 없다**(`vdd` 49·`gnd` 25·`vss` 4 중). `supply_nets`가 topology.json에 선언돼 있는데 코드가 이름을 직접 쓰고, 같은 레일 집합이 최소 세 곳에 따로 선언돼 있다(`sizing_recipe:3893-3894`, `sizing_recipe:8592`, `stick_diagram:3167`). `_metric_supply_current`는 `'vdd'`만 보는데 세 회로는 `vss`·`agnd`를 쓴다. → DF 신설 요청(담당 Phase 4, MG1 레일 이름 변경과 같은 자리).
2. **DF-29·DF-30의 사정권이 기록보다 넓다**. DF-29는 공유 함수 둘(`_telescopic_open_loop_device_names`·`_telescopic_class_ab_open_loop_gains`)과 `_CMRR_REGISTRY`·`_PSRR_REGISTRY` 키까지, DF-30은 `_METRIC_UNITS`와 `if mtype == "folded_cascode_*"` 분기 3곳까지 함께 움직여야 한다. → DF 표 비고 보강 요청.
