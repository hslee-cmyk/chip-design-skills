---
id: 20261104-tb1-theta-class
phase: 해당 없음 (DEC-86 -- merge_gate 미사용, N6.3 절차)
evidence_type: red-green
gate_change: no
---

> **[상태 2026-11-04] spec card -- 커밋 안 함, 독립 검증 전.** 사실 재측정 = 같은 폴더 `measure_facts.py` → `facts.txt`, `measure_gcb7.py` → `gcb7_master.jsonl`·`gcb7_integ_it12.jsonl`(읽기 전용, 평가 0, LUT 0). 줄 = master `7620f5ee`·`integ/it12` `b9351eac`. 실제 base에서 어긋나므로 범위 정본은 이름이다. `E/` = `skills/analog-gmid-design/gmid_engine/`. `P:` = gain-budget 계획 v6.38.8 N6.29 = P:2417~2433(범위 5 = P:2427, 완료 = P:2431). `D40:` = design 40 v1.16.3, `D41:` = design 41.

## 착수 조건

| # | 무엇 | 상태 |
|---|---|---|
| 1 | design 40 §2.4.8·§3.7-4·§3.2-3, 41 §5.3.3·§4.7-1 2 | v1.16.4(`design/v1164`)가 master에 병합된 뒤 충족. J-T1~J-T7 = 위임 A-34, 정준 위치 키·서명 = 위임 A-37 |
| 2 | GC-B7 | 처리(위임 A-30). ≠ 0이어도 범위 유지, 저항 방향 규칙은 이 card에 없다 |
| 3 | M-KV1c | 미측정 표지(O-225, P:2433). LA-1 측정 시점 |
| 4 | **base** | **미충족**: GL-1 → IT-1 + IT-2 → EO-1 범위 4 → card C를 포함한 master(P:1361~1366, D40:2216). 지금 master에 판정 기록 없음 |
| 5 | library 13 회귀 전제 | `fix/o181-tests` = 위임 A-31 처리 중 |

**병합 = TB-1 단독**(표 #5), 자리 = card C 뒤, HC-S 쪽 순서는 N6.1 진행 순서. 뒤따름 = HC-1 → LA-1a + LA-1. 파일 겹침 IT·EO-1·DR-1(같은 통합 병합 금지, 나중 card가 rebase).

**쓰기 계획 종속 기대값은 IT 뒤 base에서 정한다.** `integ/it12`와 master의 종속 목록이 이미 다르다(예: folded `M1`, nmcnr `M102`, `gcb7_*.jsonl` `dependents`). EO-1 범위 4도 쓰기 계획의 `off` 제외를 고친다. 그래서 이 card는 계획의 손 판정 목록만 입력으로 적고, 표를 **test freeze 직전에 base sha 위 S0 실행으로 다시 재서** 오케스트레이터가 interface card §5에 채운다. 채운 주체(작성자 ≠ 기대값 분리)를 판정 기록에 적는다. 기대값은 연결에서 손으로 유도하고 base 출력을 복사하지 않는다.

## 의도

쓰기 계획 앞 S0 분류 필드 `device: theta_class`(R13)를 만들고, 쓰기 계획의 비트리 종속 선택을 이름 키에서 물리 순위와 정준 위치로 바꾼다(DEC-64 (v2), DEC-95 (3)). W4 뿌리 동률은 기록 대신 정지한다. R6 ⇄ HC-1 순환을 끊고(O-144 J3), 고리의 B 멤버가 종속이 되게 한다.

사용자 결정: O-144 J3, O-146 K2, O-187, O-189, O-190, O-192, O-194 K8. 위임: A-27, A-30. 승인 사실은 근거가 아니다(O-208). 변경 종류 = **동작 변경**(쓰기 계획 종속 값 변화).

## 관찰 가능한 계약

1. **필드.** `device: theta_class` = MOS마다 `ThetaClass(kind ∈ {"S","B","F"})`. writer = `theta_class` 블록 하나, `dc_writer_plan` **앞**. X 칸 없음. READS에 `device.dc_coord`·topology 태그 없음.
2. **분류**(D41 §5.3.3 표, E8·E10).
   - 매크로 활성 = `gbw_target_hz` 선언 또는 '정착 선언 있음 + GBW 미선언'. 값은 읽지 않는다.
   - S = 매크로 활성 회로의 gain 제약 전달 뷰 주경로 이득 블록 AC 역할 `input`, 그리고 rout 선언 버퍼 블록의 출력 follower.
   - F = `cascode`·`pass`·`follower`, 매크로 비활성 회로의 `input`.
   - B = `load`·`mirror`·`diode_load`·`tail_source`, 어느 블록에도 들지 않는 소자, FF 묶음 셀.
3. **`kvl_branch` 고리 종속**(D40 §3.7-4 (a)). B 멤버가 있으면 B가 종속: diode → 대칭 궤도 대표 → 소스 사슬 하류 → DEC-97 정준 위치. B가 없으면 ① diode 독립 → ② 뒤 stage 독립 → 정준 위치. 대칭 고리 쌍은 대표 고리 선택의 상. 후보는 다른 등식에 이미 종속되지 않은 멤버.
4. **고리 밖 비트리**(같은 절 (b)). ratified override → ① diode → ② R13 S·뒤 stage 독립 → 대칭 궤도 대표 → 정준 위치. 이름 키 0. ②는 S0 구조 사실만 읽는다.
5. **ratify.** concept `dependent_member`. 고리 = confirm(다르면 `structure_fact_mismatch` 정지, 덮지 않음). 고리 밖 = override. 멤버 아님·subject 불일치 = `structure_fact_mismatch`. 관계 없음 = `structure_fact_orphan`. 사실 없음 = 유도 그대로.
6. **이름 전단사 불변.** 소자·넷 이름을 전단사로 바꿔도 종속 멤버와 front 정규화 해시가 이름 사상 뒤 같다. 적용 범위 = 고리 안팎.
7. **W4 뿌리**(범위 5, P:2427). 최소 (구조 색, 정준 위치) 후보가 둘 이상이면 `StructureUnresolvedError`(`rule_branch` = `dc_colour_not_unique`). `graph.dc_tie_breaks` decision 어휘에서 `w4_root` 없음. library 발동 0.
8. **삭제.** `OrderHints`·`NO_ORDER_HINTS`·`order_hints` 인자·`TIE_ROOT` 엔진 grep 0. `dc_writer_plan(snapshot, target_nets, input_dc_declared)`, `build_kernel_context(s1graph, inputs, lut, *, donors, counters)`.

**TB-1에 없는 것**: 저항 θ 방향 규칙과 '방향 확정' 칸(A-30), R-1′ 필드(HC-1), `start.guard`(LA-1a), 술어 인스턴스 필드(LA-1 15 (c)), '바이어스 구동 레일 source 셀' 속성(SB-1).

**재점검 표지(A-30, LA-1 완료 13 입력)**: nmcnr `RL`(Vout–agnd, 중간 레일)은 전류 방향이 동작점에 따라 바뀌는 실제 미정 1건이다. 권고 방향 = 값 선언 R의 I_R = V_R/R. 연결·KCL 유도만, SPICE 미측정. 계수 정의('양 끝 비레일')는 이 건과 cnr `x40`을 못 잡는다 -- 정정은 계획 몫.

## 재작성 범위

(엔진 인용 = 재작성 범위만, 원칙 8. 옛 코드는 같은 변경에서 삭제.)

| 파일(`E/`) | 줄 | 범위 | 근거 |
|---|---|---|---|
| `sizing/theta_class.py` | 신규 | `@compute_block theta_class` | 필드 writer 하나 |
| `sizing/s2_values.py` | master :204-215(`integ/it12` :207~) | `OrderHints`·`NO_ORDER_HINTS`·`TIE_ROOT` 삭제, `ThetaClass`·writer 이름·`BRANCH` 사유 추가, `DcInputs` 칸(J-T1) | |
| `sizing/writer_plan.py` | `_edges`, 트리 선택, 뿌리 동률 | **전체 재작성 범위**: 엣지 키·종속 선택. 트리 → writer BFS·`dc_self_referential`은 부분 | 이름 키가 구조 전체에 있다 |
| `sizing/kernel_context.py` | :4·:7·:37·:41·:53·:58-59·:86 | 인자 삭제, `theta_class` 호출을 쓰기 계획 앞에, `PLAN_WRITERS` | |
| `sizing/dc_inputs.py` | | 선언 사실 투영(J-T1) | |
| `sizing/__init__.py` | :93·:123·:125·:188·:194 | export | |
| `graph/s1v_values.py`·`graph/structure_load.py`·S1v 필드 | | concept 추가, 사실 필드(J-T2) | **rule_fp 대상 파일**(J-T3) |
| `assets/library/{current_reuse_telescopic_ota,nmcnr_amplifier}.structure.json` | `rule_hash` | 재기록(J-T3). connectivity·사실 내용 0 변경 | |
| `sizing/CONTRACT.md`, `_module_map.py`(J-T7), 소유표 D40 §2.4.8, 레지스트리 §2 | | 갱신 | |

test 주체 몫: `tests/sizing/{conftest.py, test_kernel_run.py, test_s2_values.py, test_size_and_seal.py, test_writer_plan.py}`. 지운 대상 test는 `retired_tests`, 이름 동률 기대값 교체는 `broken_tests`에 이유 'O-187'·'O-189'·'O-194'.

## 채택된 판단(위임 A-34, design v1.16.4 반영)

| # | 빈칸 | 권고 | 대안 |
|---|---|---|---|
| J-T1 | 선언 사실(GBW·rout·정착 유무)이 `theta_class`에 오는 길. `DcInputs`에 그 칸이 없다 | `DcInputs`에 유무 칸을 더하고 블록 extras로 넘긴다. spec 투영의 기존 자리, 값 읽지 않음 | S1v 필드로 ⚠ graph 층이 spec 값 판정을 더 맡음 |
| J-T2 | `dependent_member` 사실이 쓰기 계획에 오는 길. 사실은 단계 A의 `build_s1v(structure=)`까지만 온다 | S1v 새 필드 `graph/s1v: dependent_facts`(사실 그대로, 소비자 = `dc_writer_plan`). 대조·정지는 쓰기 계획 | `build_kernel_context` 인자 ⚠ 옛 OrderHints 경로 복원 |
| J-T3 | `s1v_values.py`는 `S1V_RULE_FILES`다. 고치면 `structure_rule_fp`가 바뀌어 library 사실 파일 2개가 `structure_fact_stale`이 되고 **사실이 조용히 안 쓰인다**(`structure_load.py:148`) | 같은 변경에서 두 파일 `rule_hash`만 재기록, 어휘 추가뿐임을 판정 기록에 적고, '사실이 여전히 적용됨' test를 둔다 | 재기록 안 함 ⚠ ratified 사실 소실. 재기록 위임 = A-34(전 card 공통 규칙). IT·EO-1도 이 파일들을 고치면 먼저 재기록됐는지 base에서 확인 |
| J-T4 | 키 하나로는 B 안 diode(종속 우선)와 평행 관계 ① diode(독립)가 충돌한다 | 두 단계: (1) 고리 밖 비트리(평행 등)를 (b) 순위로 먼저 정해 평행 변을 대표로 줄임 (2) 남은 그래프에서 분류별 키로 Kruskal. '이미 종속된 멤버 제외' 문언의 구현 | 전역 키 하나 ⚠ 위 충돌 |
| J-T5 | S1v 없는 `build_kernel_context`(test 28 파일 64곳). 제품 경로는 `stage_b.py:140`이 `views` 없으면 건너뛴다 | 블록 없음 → 정의 그대로 전부 B(`kernel_fields`의 기존 `.get` 꼴). 제품 경로 가드 test 추가 | 정지 ⚠ test 64곳 수정, 얻는 안전 없음 |
| J-T6 | EO-1의 `off` 선언 MOS 분류 규칙 없음 | 분류 값은 B(블록 밖 정의), 소비자가 `region_decl`로 뺀다. base에서 확인 | 필드에서 뺌 ⚠ 소비자마다 키 없음 처리 |
| J-T7 | D40 §2.4.8 'sizing 첫 층'인데 블록은 `s2_values.py`(첫 층)를 import한다 | `current_basis.py`와 같은 둘째 층. 쓰기 계획은 필드 키만 읽어 블록 import 불필요. 구조 규칙이 판정 | 첫 층 ⚠ 같은 층 import |

**표지**: 계획·design 입력 목록의 'L 동치류'는 S/B/F 정의에 소비처가 없다. 블랭킷 READS 금지(규칙 L-3)라 읽지 않는다. 필요가 드러나면 멈추고 보고.

## 신규 시그니처

| 모듈 | 심볼 | 시그니처 |
|---|---|---|
| `gmid_engine.sizing.theta_class` | `theta_class` | `@compute_block`, `theta_class(snapshot, has_gbw_target, has_rout_limit, has_settling, *, donors, counters)` |
| `gmid_engine.sizing.s2_values` | `ThetaClass` | frozen dataclass `(kind)` |
| `gmid_engine.graph.s1v_values` | `CONCEPT_DEPENDENT_MEMBER` | `"dependent_member"` |
| `gmid_engine.sizing.s2_values` | `DcInputs` 칸 | `has_gbw_target`, `has_rout_limit`, `has_settling`(bool) |

**정준 위치 키** = `device.dc_colour` 오름차순. **궤도 대표** = 크기 ≥ 2 궤도의 `dc_colour` 최소 멤버(A-37). 단독 정준 위치 필드는 만들지 않는다(graph 규칙 3).

이름 충돌: `theta_class`·`ThetaClass`·`dependent_member`·`dc_colour_not_unique`·`test_theta_class` 모두 0(master·`integ/it12`). `structure_fact_mismatch`·`_orphan`은 기존 어휘 재사용.

## graph 단일 정본

* 새 필드 `device: theta_class`(소비자 = `dc_writer_plan`, 뒤 card HC-1·LA-1a·LA-1), `graph/s1v: dependent_facts`(소비자 = `dc_writer_plan`). 필드마다 writer 하나.
* 소스 사슬 하류는 G_vgs source 넷을 그 자리에서 읽는다. 새 필드 0. 고리는 `graph.rel_kvl_branch`, 궤도는 `graph.orbits`, stage는 S1v를 READS. 재계산 0.
* `dc_coord` 역할과 같은 정의의 X 칸 없음. cache·memo·sctx 슬롯·사본 0.
* 층 순서: S2 양('GB5 gm 요구') 입력 0.
* GL-1 래칫: `ratchet.new` 0. 모듈 수준 `ThetaClass(...)` 상수(`vt_assign` 새 키)와 `writer_plan` 재작성의 새 클래스 가변 속성을 두지 않는다.

## 판정 유형 근거

| 다리 | 상태 |
|---|---|
| 정의 toy | 계약 1~8, 합성 회로 손계산 |
| 봉인 불변식·E-0 단언 | 유지(종속 다이오드 W 정의역, 전 소자 포화는 봉인이 판정) |
| 이름 전단사 metamorphic | 지금. 고리 밖 base red toy는 test 주체가 확보(계획 검증 33 D-4) |
| 기존 회귀 | 새 test 체계 전체, 0 failed. base에 실패가 남으면 목록을 올리고 판정을 멈춘다 |
| S0 종속 표(library 13, 평가 0) | 지금. 위 '기대값' 대조, 회로별 정지 사유 기록 |
| 연기 시험 | `current_reuse_telescopic_ota`(4고리 B 종속)·`pushpull_follower_buffer`(B 없는 follower 고리). 선택 확정은 검증자 |
| 13회로 변화표·front, I_Q 대 oracle(E-1), SPICE | **보류**: 변화표 = LA-1 측정 시점(LA-1 완료 13), SPICE = OP-5·CL-1(A-5·A-10). 변화표 칸은 고리 안 종속(O-187) / 고리 밖 끝 키(O-189)로 유지 |

→ 병합해도 '미완료'. 병합 판단 = O-226.

**red.** (i) current_reuse 종속 목록(S0) (ii) 이름 전단사 toy (iii) W4 동률 주입(base = 기록·진행) (iv) ratify 불일치·고아. 새 인자 `TypeError`만의 실패는 red가 아니다.

## oracle 종류와 출처

(a) 구성으로 정답이 정해진 합성 회로·연결에서 손 유도. library 종속 기대값은 (d) 회로 해석 결론(계획 P:2431 목록, 원문 = `assets/library/sources/`). base 출력 복사 금지.

## 거부해야 할 입력

W4 동률 → `dc_colour_not_unique` 정지. 고리 사실 불일치·멤버 아님 → `structure_fact_mismatch`. 관계 없는 사실 → `structure_fact_orphan`. 비트리 저항(`dc_resistor_cycle`)은 그대로(DR-1 몫).

## library 회로 적용 여부

S0 표 13회로. 현재 탐색 전 정지: `cnr_ota` = `dc_resistor_cycle`, `erfc_ota` = `mos_zero_current_structural`(둘 다 DR-1 대상, 이 card 뒤). 분모·사유를 따로 적는다. held-out 0개.

## 무동작 판정 입력

R13이 선택을 바꾸지 않는 회로(평행 관계만, 이름과 정준 위치가 같은 결론)는 종속 목록 불변. `theta_class`만 바뀐 입력은 쓰기 계획 입력 버전이 달라질 수 있으나 값은 같다. 사실 파일 없는 회로는 유도 그대로.

## 재현할 수치

S0 표: 회로별 종속 멤버·관계, 옛 대 새, 원인 칸, `w4_root` 기록 수(0), `dc_colour_not_unique` 발동(0). 판정 기록 값만 인용.

## 결정 필요 항목

사용자 질문 없음(O-226). 채택 끝 = A-34·A-37. M-KV1c 발동이면 재점검에서 design 보완.

## 원래 취지와 다름

1. GC-B7 정지·승인을 위임으로(A-30).
2. J-T2 새 S1v 필드, J-T1 `DcInputs` 칸: 계획 '이름·블록은 design'인데 design이 못 정함.
3. J-T3 사용자 ratify 파일 `rule_hash` 재기록.
4. 13회로 변화표·E-1 대조 유보(O-225).
5. 기대값을 card 머리에서 못 박지 않고 base에서 다시 잼.

## 절차

N6.3·N3.12.3 역할 분리(폐기된 gate·push 제외). test 주체는 interface card만. 판정 기록 = `.ai/verification/20261104-tb1-theta-class.json`. N6.3 넷 + 같은 입력 재계산 0, 구현 뒤 design ↔ 구현 gap(D-TB1a·D-TB1d·D-IT1b).

## 작성 전 실측

`facts.txt`: 옛 이름 소비자, 충돌, concept, 겹침(`kernel_context.py` 0, 나머지 있음). `gcb7_*`: θ 저항·종속 목록. **안 잼**: IT·EO-1 뒤 base(병합 전), 궤도·사슬 순위의 실제 결과, M-KV1c, 고리 밖 base red(M-NM1 상한 29/55묶음·9/13회로는 계획 인용), LUT·front.
