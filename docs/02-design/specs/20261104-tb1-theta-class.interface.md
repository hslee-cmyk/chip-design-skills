# TB-1 θ 분류 필드·종속 멤버 선택 interface card (card id `20261104-tb1-theta-class`)

- 작성 2026-11-04. 커밋 안 함, 독립 검증 전. **card base = GL-1·IT-1 + IT-2·EO-1 범위 4·card C를 포함한 master**(오케스트레이터가 sha를 적는다).
- **test 작성 주체는 소스를 보지 않고 이 문서만 쓴다.** `E/` = `skills/analog-gmid-design/gmid_engine/`.
- **§5 기대값 표는 base 확정 뒤 오케스트레이터가 채운다. 채워지기 전에 library 기대값 test를 동결하지 않는다.** 표를 채운 주체가 오케스트레이터임(작성자 ≠ 기대값 분리)을 판정 기록에 적는다.

## 1. 필드와 블록

```text
device: theta_class = {MOS: ThetaClass(kind)}     # kind ∈ {"S","B","F"}, gmid_engine.sizing
theta_class(snapshot, has_gbw_target, has_rout_limit, has_settling, *, donors, counters) -> GraphSnapshot   # gmid_engine.sizing.theta_class, S0 블록, bool 셋 = 블록 extras
DcInputs 칸: has_gbw_target, has_rout_limit, has_settling (bool, 값은 읽지 않음)
```

- `build_kernel_context`가 `DcInputs`의 세 칸을 넘긴다. PM 선언은 입력이 아니다. T-T1의 PM 유무 조합은 분류 불변을 단언한다.

- `build_kernel_context`가 `dc_writer_plan` 앞에 부른다. 같은 입력 재호출 = 재사용.
- 블록 READS에 `("device","dc_coord")` 없음, topology 태그 없음(블록 객체 `theta_class.reads`로 단언).
- 분류 규칙:

| kind | 구조 정의 |
|---|---|
| S | 매크로 활성 회로에서 gain 제약 전달 뷰 주경로 이득 블록의 AC 역할 `input`. rout 선언 버퍼 블록 출력노드에 source가 닿는 follower |
| F | AC 역할 `cascode`·`pass`·`follower`, 매크로 비활성 회로의 `input` |
| B | `load`·`mirror`·`diode_load`·`tail_source`, 어느 블록에도 들지 않는 MOS, FF 묶음 셀 |

- 매크로 활성 = `gbw_target_hz` 선언, 또는 정착 선언 있음 + GBW 미선언. 선언 **값**은 결과를 바꾸지 않는다.
- S1v가 없는 S1(블록 없음) → 전부 B. `off` 선언 MOS → B.

## 2. 쓰기 계획

```text
dc_writer_plan(snapshot, target_nets, input_dc_declared, *, donors, counters)
build_kernel_context(s1graph, inputs, lut, *, donors, counters)
```

출력 필드 형식은 그대로: `node.dc_writer`, `device.dc_coord`(`DeviceCoord(role, relation, partner)`), `graph.dc_tie_breaks`, `device.dc_self_referential`.

**정준 위치 키** = `device.dc_colour` 오름차순(정점마다 유일·이름 무관). 표의 "앞" = 값이 작은 쪽. **궤도 대표** = `graph.orbits`에서 크기 ≥ 2인 궤도의 `dc_colour` 최소 멤버. toy는 `dc_colour`·`orbits`를 스냅샷 필드로 직접 넣어 순서를 정하고, 기대값은 그 값에서 손으로 낸다.

**`kvl_branch` 고리의 종속 멤버**
- B 멤버가 있으면 B가 종속. B 안 순위(앞이 먼저 종속): diode → 대칭 궤도 대표 → 소스 사슬 하류(source 넷 전압이 다른 고리 멤버의 VGS로 정해지는 멤버) → 정준 위치.
- B가 없으면 독립 유지 순위: diode → 뒤 stage → 정준 위치. 남는 쪽이 종속.
- 대칭 고리 쌍은 대표 고리 선택의 상. 이미 다른 등식에 종속된 멤버는 후보가 아니다.

**그 밖 비트리 관계**(같은 (gate, source) 평행 등): 독립 유지 순위 = diode → R13 S·뒤 stage → 대칭 궤도 대표 → 정준 위치.

**이름은 어느 키에도 없다.** 소자·넷 이름 전단사 뒤 종속 멤버(이름 사상 적용)가 같다.

**ratify**(`<회로>.structure.json`, concept `dependent_member`, subject = 멤버 이름 정렬 JSON 배열, value = 종속 소자 이름):

| 입력 | 결과 |
|---|---|
| 고리 사실 = 유도 결과 | 그대로(무동작) |
| 고리 사실 ≠ 유도 결과 | `StructureUnresolvedError` 계열 정지, 사유 `structure_fact_mismatch` |
| 고리 밖 사실 | 그 멤버로 override |
| value가 멤버 아님, subject가 유도 관계와 다름 | `structure_fact_mismatch` |
| 그 관계 없음 | `structure_fact_orphan` |
| 사실 없음 | 유도 그대로 |

정지 예외 클래스는 기존 `structure_fact_*` 사유와 같은 것을 쓴다. test는 사유 문자열로 단언한다.

**W4 뿌리**: 최소 (구조 색, 정준 위치) 후보가 둘 이상이면 `StructureUnresolvedError`, `detail["rule_branch"] == "dc_colour_not_unique"`. `dc_tie_breaks`의 decision에 `w4_root` 없음. 나머지 decision 그대로. 주입은 같은 `dc_colour`를 가진 W4 후보를 스냅샷 필드로 넣어 만든다.

**그대로**: 비트리 저항 `dc_resistor_cycle` 정지, 입력 점 규칙(IT-1), `off` 제외(EO-1).

## 3. 없어지는 이름

`gmid_engine.sizing`의 `OrderHints`, `NO_ORDER_HINTS`, `TIE_ROOT`, 인자 `order_hints`. `E/`(tests 포함) 단어 grep 0. test 헬퍼 `build_ctx_u4`의 `order_hints` 인자도 지운다.

## 4. test 목록

oracle: (손) 합성 회로 연결에서 손 유도, (식) 이 문서 규칙, (비교) 전단사 쌍 비교, (회로) §5 표. 두 객체는 `open_run()`으로만. 기대값을 피검 함수로 만들지 않는다.

| id | 위치 | 내용 | oracle | base 결과 |
|---|---|---|---|---|
| T-T1 | `tests/sizing/test_theta_class.py`(신규) | 표 행마다 합성 toy 분류. 매크로 활성 네 조합(GBW·정착·PM 유무), 선언 값만 바꿔도 불변, rout follower S, 블록 밖 B, FF 셀 B, S1v 없음 전부 B | (손) | red(부재) |
| T-T2 | 같은 파일 | `reads`에 `dc_coord` 없음, 쓰기 계획 앞 호출(필드가 계획 전 스냅샷에 있음), writer 하나 | (식) | red(부재) |
| T-T3 | `tests/sizing/test_writer_plan.py` | 고리 안 B 순위 toy 넷: diode 우선, 궤도 대표, 소스 사슬 하류, 정준 위치 | (손) | red |
| T-T4 | 같은 파일 | B 없는 고리 toy 셋: diode 독립, 뒤 stage 독립, 정준 위치 | (손) | red |
| T-T5 | 같은 파일 | 평행 관계와 고리에 같은 diode가 함께 있는 toy: 평행에서 diode 독립 유지, 고리 선택은 남은 멤버 | (손) | red. red가 안 나면 green 유지로 적고 이유를 쓴다 |
| T-T6 | 같은 파일 | 이름 전단사 metamorphic: 고리 toy와 **고리 밖 toy 각 1 이상**. base는 이름 키로 갈려 red. 고리 밖 red toy를 못 찾으면 멈추고 보고 | (비교) | red |
| T-T7 | 같은 파일 | ratify 네 갈래(일치·불일치·override·orphan) + 멤버 아님. 합성 사실 | (식) | red |
| T-T8 | `tests/graph/test_structure_load.py` | concept 어휘에 `dependent_member`. **library 사실 파일 2개가 stale 없이 적용됨**(`findings` 0, 파일 이름은 사실 파일 있는 회로 전수) | (식) | head 기준 |
| T-T9 | `tests/sizing/test_writer_plan.py` | W4 동률 주입 정지, 어휘에 `w4_root` 없음 | (식) | red(base = 기록·진행) |
| T-T10 | `tests/sizing/test_kernel_context.py` | `order_hints` 인자 `TypeError`. `stage_b` 경로: `views` 없으면 건너뜀 | (식) | red |
| T-T11 | 옛 OrderHints test 정리: `conftest.py`, `test_kernel_run.py`, `test_s2_values.py`, `test_size_and_seal.py`, `test_writer_plan.py` | 지운 대상은 `retired_tests`, 이름 동률 기대값은 바꾼 규칙으로 다시 쓰고 `broken_tests` 이유 O-187·O-189·O-194 | -- | -- |
| T-T12 | `tests/integration/`(평가 0, LUT 0 S0 경로) | §5 표 대조, 회로별 정지 사유 `cnr_ota`·`erfc_ota` | (회로) | red(회로에 따라) |

이름 규칙: 접두 `test_theta_class_…`, `test_dependent_member_…`, `test_w4_root_tie_…`. `test_ic`로 시작하지 않고 `ic1`·`ic2`·`ic9`·`ic10`·`rule_g`·`rule_k_`·`g10`을 담지 않는다. 작성 뒤 `--collect-only -k <각 식>` 수를 base와 함께 보고.

단언 금지: `ThetaClass` 밖 내부 키 구조, 엣지 정렬 키 모양, 처리 단계 수, `input_version` 문자열.

## 5. library 기대값 (base 확정 뒤 채움)

입력(계획 P:2431 손 판정, 확정 아님):

| 회로 | 기대 |
|---|---|
| `current_reuse_telescopic_ota` | 4고리 종속 M15·M16·M25·M26 → M11b·M14a·M20b·M23a(소스 사슬 하류) |
| `pushpull_follower_buffer`, `sf_pushpull_output_opamp` | follower 고리 = ② 뒤 stage 독립 + 정준 위치 |
| `r2r_opamp` | 다이오드 B 고리 = 소스 사슬 하류 M23·M22. 다이오드 없는 고리 = M-KV1c 미측정(LA-1 측정 시점), 단언하지 않음 |
| `cnr_ota`, `erfc_ota` | 탐색 전 정지(DR-1 몫), 사유만 |
| 나머지 | 고리 0이면 평행 관계만 |

| 칸 | 값 |
|---|---|
| base sha | (채움) |
| 회로별 기대 종속 + 유도 근거 | (채움: 연결에서 손 유도, base 출력 복사 금지) |

## 6. 판정 측정 (audit)

격리 복제본. 무거운 실행은 회로마다 프로세스, 순차, 케이스마다 append.

| # | 측정 | 합격 |
|---|---|---|
| T-1 | red-green: T-T1~T-T7·T-T9~T-T10 red 사유 기록, head 통과 | 충족 |
| T-2 | grep(§3), `rg theta_class` writer 하나, READS | 0·하나 |
| T-3 | 전체 test 체계 + `tests/structure`. base에 실패가 남으면 목록을 올리고 판정을 멈춘다 | 전체 0 failed, 구조 위반 0 |
| T-4 | N6.3 넷 + 같은 입력 재계산 0, 새 필드 소비자 ≥ 1(`theta_class`·`dependent_facts`), GL-1 `ratchet.new` 0, 모듈 수준 `ThetaClass` 상수 없음, `writer_plan` 새 클래스 가변 속성 없음 | 통과 |
| T-5 | S0 표 13회로(평가 0): 옛 대 새, 원인 칸 O-187 / O-189 | §5 일치, 미설명 0 |
| T-6 | **`structure.json` 변경은 `rule_hash` 줄뿐**(`git diff`), connectivity 변경 0 | 충족 |
| T-7 | 연기 시험 2회로. 예외나 직전에 없던 정지 사유면 병합 금지·보고. 선택을 기록 | 예외 0 |
| T-8 | 결정성 비트 동일, design ↔ 구현 gap(D-TB1a·D-TB1d·D-IT1b) | 동일, Major 0 |
| 보류 | 13회로 변화표·front·I_Q 대 oracle = LA-1 측정 시점, SPICE = OP-5·CL-1, M-KV1c, nmcnr `RL` 방향 재점검(A-30). 판정 기록 '미완료(보류 다리…)' | 통과로 세지 않음 |
