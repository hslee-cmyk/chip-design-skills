# IT-1 dispute 세 건 분석과 해소 권고 (2026-10-21)

대상: card `20261021-it1-input-tie-removal`, code `role/code/it1` `14e0ca2a`(worktree `wt/it1-code`), test `role/test/it1` `0366ddb4`.
방법: 읽기 전용. `git -C`만 썼고, 실패 출력을 읽으려고 it1-code worktree에서 단일 test만 돌렸다. 엔진 값은 scratchpad probe(`scratchpad/it1-dispute/probe_ties.py`)로 쟀다. worktree 상태는 바꾸지 않았다(`git status` 깨끗함).

읽은 근거:
- dispute `docs/02-design/disputes/20261021-it1-input-tie-removal.md`(it1-code)
- spec·interface card(master)
- 승인 `.ai/approvals/20261021-it1-o13-scope.md`
- design 41 §4.7-1(666-674)·§6.7-1a(1686-1694)
- design 40 §6-8 8항(1609-1616)·1907행
- 계획 U-62(2144행)·F-IT6(1385행)

## 요약 표

| # | red test | (a) 틀린 쪽 | (b) 소비자 표·K-3 목록 | (d) 해소·주체 | 기준 약화 |
|---|---|---|---|---|---|
| 1 | `test_s2_values::test_block_reads_declared_as_contract[dc_columns]` | **test**(기대 집합이 낡음) | 파일은 K-3 목록에 있음(`:183-197`, `:181`). 줄 `:148`은 목록 밖. 필드 행은 spec card graph 표에 있음 | test 작성 주체: `READS["dc_columns"]`에 `("node","port_direction")` 추가 | 아님(정확 일치 단언 유지) |
| 2 | `test_current_basis::test_current_ties_and_variables_match_8e46548` ×6 | **test 기준선**(동작 변경의 승인된 결과) | **목록 밖**(S-2 성격, 보고 대상) | 사용자에게 K-3 목록 확장을 1줄로 보고 → 감사 변화표(커밋 3) → test 주체가 커밋 3b에서 갱신(`8e46548 값 + IT-1 Δ`, 원인 칸 포함) | 아님(정확 일치, 독립 손유도 Δ). 목록 밖이라 확장 보고 필요 |
| 3 | `test_orbit_ties::test_ds_flip_symmetry_bit_identical[names0]` | **test harness**(단언 대상은 S1 필드인데 harness가 S0 쓰기 계획까지 지어 정지에 걸림). 엔진 정지는 올바른 fail-closed | **목록 밖**(S-2 성격, 보고 대상). S-3(code 쪽 θ 키 다중 뿌리)은 아님 | test 주체: 뒤집은 쪽 case는 S1까지만 지어 대칭 단언 6개를 **그대로** 비교. 정지 단언은 바꾸지 말고 **추가**만 할 수 있음. design 40 §6-8에 정지 경로 1줄 보강 권고(오케스트레이터) | toy를 바꾸거나 정지 단언으로 바꾸면 **약화**(design 40:1907의 d/s 비트 동일 범위를 줄임). 그렇게 하려면 사용자 승인 필요. harness만 고치면 약화 아님 |

정리하면, code를 고칠 필요는 없다. 세 건 모두 test 쪽에서 맞춘다. 2와 3은 승인 기록의 K-3 test 목록 밖이라, 범위 확장을 사용자에게 보고해야 한다. 기준 약화가 아니어서 결정은 가볍다.

---

## 1. `test_block_reads_declared_as_contract[dc_columns]`

**(a) test가 틀렸다.** 근거는 셋이다.
- design 41:672(§4.7-1 5항): "`dc_columns` READS에 `("node", "port_direction")`을 더한다".
- spec card graph 표의 마지막 행: "`node.port_direction` | `dc_columns` READS에 추가(41:672) | `dc_columns.input_roots`".
- 같은 test 작성 주체가 같은 변경에서 쓴 `test_writer_plan.py:530`도 `("node","port_direction") in set(dc_columns.reads)`를 단언한다.

그런데 `test_s2_values.py:148-153`의 `READS["dc_columns"]`는 옛 집합 그대로라서 두 단언이 동시에 참일 수 없다. code는 card대로 바뀌었다.

**(b)** 이 필드 변화는 spec card graph 표(I2·I6)에 있는 계약이다. `test_s2_values.py`도 K-3 목록에 있다(`:183-197`, `+:181`). 다만 목록이 적은 줄 범위에 `:148`(READS 표)이 빠졌을 뿐이다. 목록 밖 소비자가 아니므로 S-2·S-3에 해당하지 않는다.

**(c)** 물리와는 무관하고 계약 표의 문제다. graph 정본 점검:
- `port_direction`은 S1 필드이고 writer는 기존 그대로다.
- `dc_columns`는 READS로 읽기만 한다. 둘째 생산자는 없다.

**(d)** 주체는 test 작성 주체다. 할 일은 `READS["dc_columns"]`에 `("node","port_direction")`을 더하는 것이다. 이유 칸에는 'K-3(41:672), 약화 아님'을 적는다. 정확 일치 단언을 그대로 두므로 기준 약화가 없다.

## 2. `test_current_ties_and_variables_match_8e46548` (6 파라미터)

### 실측

단일 test 실행으로 `(len(ties), len(variables))`을 쟀다.

| 회로 | 기준선(8e46548) | IT-1 head |
|---|---|---|
| current_reuse_telescopic_ota | (29, 38) | **(30, 38)**: tie +1, 변수 그대로 |
| folded_cascode | (0, 16) | (0, 17) |
| ngcc_3stage_ff | (0, 21) | (0, 22) |
| nmcnr_amplifier | (0, 23) | (0, 24) |
| two_stage_ota | (0, 10) | (0, 11) |
| two_stage_ota_sf | (0, 12) | (0, 13) |

나머지 셋은 그대로다.
- common_gate: 입력이 하나라 y 키 이름만 바뀐다.
- 입력 DC 선언 회로 2개(pushpull_follower_buffer·sf_pushpull_output_opamp): 무동작이다.

이 결과는 계획 F-IT2('2입력 6회로')와 맞는다. 참고로 브리핑의 '여섯 개 모두 tie +1'은 정확하지 않다. tie가 +1인 회로는 current_reuse 하나이고, 나머지 다섯은 **변수 +1**이다.

### (c) 물리: 같은 DC 엣지를 지우면 `cycle_vgs` 종속이 θ 변수가 되는 이유

θ 스키마(`sizing/theta_schema.py:135-141`)는 `dc_coord.role == writer`인 MOS마다 `ln_idu` 성분 하나를 만든다. 종속 소자(`parallel_vgs`·`cycle_vgs`·`fixed_vgs`)는 VGS를 나무 경로가 정하므로 θ 성분이 없다.

옛 규칙에서는 같은 DC 엣지(`input_tie`, Kruskal 최상위 순위)가 두 입력 포트를 이었다. 그래서 차동쌍의 꼬리 노드를 거치는 경로 `inn–CS–inp`와 tie 엣지가 순환 하나를 만들었다. 그 순환의 MOS 하나가 `cycle_vgs` 종속이 되어, 등식 VGS2 = VGS1(같은 DC)이 강제됐다.

새 규칙에서는 tie 엣지가 없으므로 `inn–CS–inp`는 나무다. 두 MOS가 모두 writer가 되어 θ `ln_idu`가 1 늘어난다. 이것은 design 41 §4.7-1 3항, 곧 '종속 수 = 같은 DC 엣지 없는 G_vgs(F 한 점)의 순환 수'의 직접 결과다.

### two_stage_ota 손계산

넷리스트(library topology)는 다음과 같다.
- M1 (D3, vin_n, CS), M2 (O1, vin_p, CS)
- M3 (D3, D3, vdd), M4 (O1, D3, vdd)
- M5 (CS, bias, gnd), M6 (OUT, O1, vdd), M7 (OUT, bias, gnd)

G_vgs 엣지(gate–source)는 다음과 같다.
- M3·M4: D3–vdd (평행)
- M6: O1–vdd
- M1: vin_n–CS
- M2: vin_p–CS
- M5·M7: bias–gnd (평행)

| 항목 | 옛 규칙 | 새 규칙 |
|---|---|---|
| 순환 | M4∥M3, M7∥M5, 그리고 tie 순환 {vin_n–CS–vin_p–tie} | M4∥M3, M7∥M5 |
| 종속 | M4, M7, M2(`cycle_vgs`) = 3 | M4, M7 = 2 |
| writer | M1, M3, M5, M6 = 4 | M1, M2, M3, M5, M6 = 5 |
| y 키 | `input_common_mode` 1 | `vin_p`(뿌리 넷) 1 |

L·전류·Cc·y OUT 성분은 변하지 않는다. 따라서 Δ변수 = +1(`ln_idu M2`)이다.

probe 실측도 같다.
- dc_coord: M1·M2·M3·M5·M6이 writer/tree, M4·M7이 dependent/parallel_vgs.
- 변수 11개 = Cc, I(M3), I(M4), I(M6), ln_idu{M1, M2, M3, M5, M6}, y{OUT, vin_p}.

손계산과 일치한다.

### current_reuse (파일럿) 실측

옛 규칙에서는 tie 엣지가 두 순환(M1a/M1b 쪽, M4a/M4b 쪽)을 만들어 종속이 둘이었다. 새 규칙에서는 포트 경로가 둘인 v1 고리 하나만 남는다. ΔV 소거 KVL이 그 고리 멤버 M1b 하나를 `cycle_vgs` 종속으로 만들고(41:670 '파일럿 VGS1a − VGS1b = VGS4a − VGS4b, M1b'), M4b는 writer가 된다.

M4b의 `ln_idu`는 자기동형 궤도로 M4a에 묶인다. 그래서 tie가 30이 되고(`ln_idu` tie 9개 안에 M4a~M4b가 있음), 변수 38은 그대로다.

**전류 tie는 7개 그대로다**(M19~M10, M18a~M9a, M1a~M1b, M17~M8, M22~M13, M25~M15, M20a~M11a). 이 test가 원래 지키던 U17 ①-d 전류 기저 열 순서 회복('전류 묶음 7', design 40 1614행)은 깨지지 않았다.

### (a)·(b)

동작 변경은 승인 범위 안이다. 승인 기록 `scope`가 '같은 DC 종속 0', 'θ y', 'test 기대·S0 기준선 갱신'을 덮고, design 41 3항도 같다. 따라서 code가 틀린 것이 아니고 기준선이 낡은 것이다.

그러나 `test_current_basis.py`는 spec card·interface card의 'test 작성 주체 몫' 목록에 **없다**. 승인 기록 '범위 설명'은 test 기대 갱신을 그 목록으로 한정한다. code 작성자가 dispute 근거 2에 '소비자 표 밖(S-2)이므로 보고'라고 적은 판단이 맞다. 이것은 소비자 집합이 늘어난 경우이고, 계획 N6.5는 이를 보고하라고 한다.

### (d) 권고

1. 사용자에게 1줄로 보고하고 확장 승인을 받는다: "IT-1 K-3 test 목록에 `test_current_basis.py`(BASELINE_8E46548)와 `test_orbit_ties.py`를 더함, 기준 약화 아님". 승인 기록 frontmatter의 `scope`('test 기대·S0 기준선 갱신')로 덮인다고 볼 여지도 있지만, '범위 설명'의 목록 한정이 더 좁다. 그래서 확장을 보고하는 쪽을 기본안으로 둔다.
2. 감사가 커밋 3에서 쓰는 9회로 변화표에 이 6행의 원인 칸을 넣는다. 원인은 'writer +1 = 옛 cycle_vgs 입력쌍 소자, current_reuse는 그 소자가 궤도 tie로 흡수'다.
3. test 작성 주체가 커밋 3b에서 기준선을 갱신한다. 권고 꼴은 `8e46548` 값을 지우지 않고 회로별 `IT-1 Δ`와 원인 주석으로 적는 것이다. 이렇게 하면 기준선 출처의 추적성이 유지된다. 선택 사항으로, current_reuse 전류 tie 수 7을 별도로 단언하면 원래 목적이 더 분명해진다.

기준 약화는 아니다. 정확 일치 단언이 그대로이고 새 값은 손유도 Δ로 독립 확인된다.

### 물리 관찰(분쟁 아님, 기록만)

입력 DC를 선언하지 않은 비대칭 회로를 보자. two_stage_ota처럼 궤도 tie가 0인 회로에서는 M2 `ln_idu`가 M1과 독립인 θ가 되고, 탐색은 입력 DC 차이(VGS2 − VGS1)를 자유롭게 고른다.

이것은 계획 B2('v1 입력 포트 차 고리는 제약을 만들지 않는다')가 정한 동작이다. 실제 폐루프에서는 그 차이가 오프셋 수준으로 정해지지만, 이 card의 범위는 아니다. 입력 창과 ICMR은 IT-2가 맡는다.

## 3. `test_ds_flip_symmetry_bit_identical[names0]` (가장 중요)

### 실패 위치(실측)

traceback은 `canon_cases.make_case:96 → build_kernel_context → writer_plan.py:225`에서 `StructureUnresolvedError {reason: unsupported_rule_branch, rule_branch: input_port_multiple_roots, nets: ('inn','inp')}`를 낸다.

정지는 harness가 커널 컨텍스트(S0 쓰기 계획)를 짓는 단계에서 난다. test의 단언 6개는 모두 S1 대칭 필드(`graph/s1 orbits.devices·nodes`, `dc_colour` 두 열, `current_symmetry`)라서 하나도 실행되지 않았다.

다른 세 파라미터는 green이다. names1(M3 뒤집기), names2(M5), names3(MOS 5개 모두)에서는 입력 두 포트가 같은 성분에 있거나 F 있는 성분에 들어가기 때문이다.

### 손유도: 왜 M1만 뒤집으면 뿌리가 둘인가

sym_doc 넷리스트는 다음과 같다.
- M1 (o1, inp, t), M2 (o2, inn, t)
- M5 (t, vb, gnd)
- M3 (o1, pb, vdd), M4 (o2, pb, vdd)
- vb·pb는 bias(선언)이다.

원래 G_vgs:
- inp–t (M1), inn–t (M2) → 성분 {inp, t, inn}
- F는 없고 입력 포트가 2개다. 뿌리는 그중 최소 하나, 나머지 포트는 트리 경로로 쓰인다. 뿌리 1개.

M1만 뒤집으면(drain t, source o1):
- inp–o1 (M1), inn–t (M2) → 성분 {inp, o1}과 {inn, t}
- 둘 다 F가 없고 각각 입력 포트가 있다. 입력 W4 뿌리가 2개다.
- design 41 §4.7-1 4항대로 정지한다. 규칙이 정확히 실행된 것이다.

### (c-1) 새 규칙이 엔진 결과를 D/S 라벨에 의존하게 만드는가?

그렇다. 다만 그 의존은 **이미 사용자가 결정한 정의**이고, 새로 생긴 위반이 아니다.

design 40 §6-8 8항 '비트 동일 범위'(1613행, 사용자 결정 2026-10-13 "1은 권고", 범위 (라))는 다음과 같다.

> topology의 d/s 표기는 **물리 방향 선언**이다(사용자만 수정하는 정본, 엔진은 고치지 않는다). … **MOS d/s 표기 맞바꿈**에 대해서는 **대칭 결과**(궤도, 정준 위치, `dc_colour`)가 비트 동일이고, 전류 부호는 표기 기준 방향 변환(뒤집은 소자 f = −1을 원소·상에 곱함)을 적용하면 동일하다. **사이징 결과**(writer 계획, θ 스키마, ties, front)는 선언 방향을 따르므로 비트 동일 대상이 아니다. 근거: 엔진 51개 파일이 표기 source를 물리 source로 쓴다 … 틀린 선언은 봉인 7(VDS − VDsat ≥ tol)이 거부한다: 선언 VDS ≤ 0이라 창 안에 근이 없어 `no_root_in_window`(fail-closed).

design 40 1907행 test 표는 다음과 같다.

> d/s 비트 동일 범위(§6-8 D-3, (라)) | (a) d/s 표기만 맞바꾼 입력 … | `tests/search/test_orbit_ties.py::test_ds_flip_symmetry_bit_identical` … | 궤도·정준 위치·`dc_colour`(노드·원소) 비트 동일, 전류 부호는 … 동일. **ties·writer 계획·θ 스키마·front는 비교하지 않는다(선언 방향을 따름)**.

계획 U-62(2144행, 닫힘)는 다음과 같다.

> d/s 표기를 뒤집은 입력은 대칭 결과만 비트 동일(전류 부호는 표기 기준 방향 변환 뒤)·사이징 결과는 선언 방향(범위 (라) …, 틀린 선언은 봉인 7 거부)

계획 DEC-97 (3)(4)는 '방향 없음'을 MOS d/s까지 넓혔지만, 그 범위는 대칭 탐색(S1)뿐이다.

새 정지는 writer 계획, 곧 **사이징 결과**에서 난다. 계획과 design이 요구하는 불변식(S1 대칭 결과의 d/s 비트 동일)은 건드리지 않는다. 실제로 S1 필드는 정지 전에 이미 쓰였다.

### (c-2) IT-1 전에는 `input_tie`가 그 의존을 숨겼는가?

부분적으로 그렇다.
- 쓰기 계획 자체는 IT-1 전에도 라벨을 따랐다. 엣지가 inp–t인지 inp–o1인지가 라벨로 정해졌다.
- 다만 같은 DC 엣지가 inp–inn을 늘 한 성분으로 묶었다. 그래서 라벨이 성분을 갈라도 뿌리 수가 1로 유지되고, S0 쓰기 계획이 정지 없이 지어졌다.
- 그 결과 names0 toy는 S0을 통과했다. 거부가 있었다면 봉인 7(사이징 단계)에서만 났을 것이다. 이 test는 `build_sctx=False`라 거기까지 가지 않았다.

즉 `input_tie`는 라벨 의존의 **위상적 표출(뿌리 수)**을 가렸을 뿐, 라벨 의존 자체가 없었던 것은 아니다.

### (c-3) 이 정지는 올바른 fail-closed인가, 물리 불변식에 대한 회귀인가?

**올바른 fail-closed다.** names0 선언은 물리적으로 불가능하다.
- M1을 drain = t, source = o1로 선언하면 NMOS 전류의 기준 방향은 t → o1이다.
- o1의 DC KCL에서 o1에 닿는 소자는 M3(PMOS, vdd → o1 전류 유입), M1, 그리고 DC 전류가 없는 CL1뿐이다. 선언대로라면 I3 + I1 = 0을 양의 전류 둘로 만족해야 하므로 해가 없다.
- 선언 VDS = V(t) − V(o1)도 실제 동작점에서 음수다. design 40이 말하는 '틀린 선언'(선언 VDS ≤ 0)에 해당한다.

바른 선언에서는 MOS마다 라벨이 바이어스와 일치하는 하나뿐이다. 0 전류 자기 맞바꿈은 이미 `ds_self_swap_zero_current`로 정지한다(design 40 1616행). 따라서 '바른 선언 사이에서 결과가 라벨에 의존'하는 경우는 생기지 않는다. 계획이나 design이 요구하는 물리 불변식(대칭 결과의 궤도·라벨 대칭)에 대한 회귀가 아니다.

다른 점은 거부 **경로**뿐이다. 이전에는 봉인 7 `no_root_in_window`(사이징 중)였고, 지금은 이 toy처럼 뒤집기가 입력 포트를 다른 G_vgs 성분으로 가르는 경우 탐색 전 S0에서 `input_port_multiple_roots`로 멈춘다. 그런데 이 정지의 사유는 '미구현 분기(DEC-76)'라고 표시된다. 진짜 원인인 '틀린 d/s 선언'을 직접 말하지 않는 진단 품질 문제다. 정합성 결함은 아니다. 새 규칙을 만드는 것은 DEC-76 범위 밖이므로 백로그로 둔다.

### (c-4) source 단자는 라벨에서 오는가, 바이어스에서 오는가?

**라벨(선언)에서 온다.** 근거:
- design 40 1613행: "topology의 d/s 표기는 물리 방향 선언(사용자만 수정하는 정본, 엔진은 고치지 않는다)", "엔진 51개 파일이 표기 source를 물리 source로 쓴다".
- 계획 U-62도 같다.
- 바이어스로 source를 다시 정하는 규칙은 계획에 없다. 틀린 선언을 바이어스로 고치지 않고 봉인 7로 거부하는 것이 정본이다(fail-closed).

### (a)·(b)

**test harness가 틀렸다.** test가 지키려는 계약은 S1 대칭 결과인데, harness `make_case`가 S0 쓰기 계획까지 짓기 때문에 계약 밖의 정지에 걸린다. code와 규칙은 design 41 §4.7-1 4항 그대로다.

`test_orbit_ties.py`는 K-3 목록에 **없다**. code 작성자가 dispute에서 'S-3 해당 여부는 test 주체가 정함'이라고 적었지만, S-3은 code 쪽 멈춤 조건(`_solve_input_window` θ 키에 다중 뿌리 경로가 남는 경우)이라 해당하지 않는다. 이 건은 S-2와 같은 성격의 '목록 밖 소비자'로, 보고 대상이다.

### (d) 권고 (주체: test 작성 주체, 사용자에게는 목록 확장 보고. 2와 함께 1줄)

1. **harness만 고친다.** 뒤집은 쪽(그리고 대칭으로 원본 쪽도) case를 S1 대칭 블록까지만 짓고(`build_s1` 출력의 `graph/s1` 필드), 기존 단언 6개를 바꾸지 않고 비교한다. 이 방법은 기준 약화가 아니고 design 40:1907을 그대로 지킨다. S1 필드를 읽는 정확한 API는 test 주체가 interface로 확인한다.
2. 선택 사항: 같은 names0 입력으로 커널 컨텍스트를 지으면 `input_port_multiple_roots` 정지가 난다는 단언을 **추가**한다. 이렇게 하면 '틀린 선언 → fail-closed'가 실제로 거부됨을 고정할 수 있다. 바꾸는 것이 아니라 더하는 것이다.
3. **하지 말 것**: names0 파라미터를 지우는 것, toy를 바꿔 M1 뒤집기를 피하는 것, 대칭 단언을 정지 단언으로 바꾸는 것. 셋 다 design 40:1907의 'd/s 표기만 맞바꾼 입력' 범위를 줄이므로 **기준 약화**이고 사용자 승인이 필요하다.
4. 계획·design(S-7): design 40 §6-8 8항의 "틀린 선언은 봉인 7이 거부한다"에 다음 1줄을 보강할 것을 권고한다(오케스트레이터 몫). "d/s 반대 선언이 입력 포트를 다른 G_vgs 성분으로 가르면 탐색 전 S0 `input_port_multiple_roots` 정지(IT-1, 41 §4.7-1 4)". 현 문언과 모순되지는 않지만 거부 경로가 하나 더 생겼다. '구현이 design과 다르면 design부터' 원칙에 따라 병합 전에 넣는 것이 맞다. 규칙 변경이 아니라 기술 보강이라 사용자 결정은 필요 없다.

## 4. 그 밖의 점검

### 4.1 `achievability` READS에서 `node.dc_writer` 제거

diff `0366ddb4..14e0ca2a`에서 바뀐 것은 다음과 같다.
- `metrics/achievability.py`: `REL_TIE` import, `_dof`의 `tie:<넷>` 등식 3줄, READS의 `("node","dc_writer")`가 지워졌다.
- `metrics/CONTRACT.md` 2줄과 docstring도 바뀌었다.

**design 지시와 맞는다.** design 41:672(§4.7-1 5항)에 "`achievability`의 `tie:<넷>` 등식 삭제"가 있다. 그 등식이 `dc_writer`의 유일한 사용처였으므로 READS를 남겨 두면 읽지 않는 필드를 선언하게 된다. 그러면 입력 버전에 거짓 의존이 생기고 graph 정본 규칙(READS = 실제 읽기)에 어긋난다. 따라서 제거가 맞다.

**보고할 이탈은 있다.** spec card graph 표는 `node.dc_writer`와 `device.dc_coord`의 소비자로 `achievability`를 적었다.
- `device.dc_coord`는 base(`0366ddb4`)의 achievability READS에도 원래 없었다(실측). 표가 처음부터 부정확했다.
- `node.dc_writer` 소비자에서 achievability가 빠지는 것은 계획 N6.5의 '소비자 집합이 늘거나 줄면 보고'에 해당한다.
- 그런데 dispute 문서에는 이 이야기가 없다. code 작성자의 보고 누락이므로 오케스트레이터가 보고에 넣어야 한다.

I6(바뀐 필드마다 엔진 소비자 ≥ 1)는 여전히 충족한다. `node.dc_writer`에는 `dc_columns`·`scc_order`·`theta_schema`가, `device.dc_coord`에는 `dc_columns`·`theta_schema`가 남는다. 사용자 결정은 필요 없고, 보고와 card 표 정정(감사 판정 기록 I-2에 기록)으로 충분하다.

**구조 DOF 변화는 예상된 것이다.** `_dof`는 변수 대 등식(KCL·res·fix·옛 tie)으로 구조 DOF를 낸다. tie 등식 v(inn) = v(inp)가 없어지면, 2입력 입력 DC 미선언 회로마다 입력 노드 전압의 자유도가 1 늘어난다. 이것이 계획 B2('입력 포트 차 고리 제약 없음')와 design 41 3항의 의도한 결과다.

다만 `DofReport.status`(square/under 등)나 achievability 판정·사유가 회로별로 바뀌는지는 이번에 재지 않았다. 감사 9회로 변화표(IT-0 M-I 목록의 'DOF' 칸)에서 회로별 Δ와 status 변화를 확인해야 한다. status가 바뀌어 판정·사유가 달라지면 그것도 원인 칸에 적어야 한다.

### 4.2 전체 suite 백그라운드 실행

- `scratchpad/it1-code/t3.txt`: **끝나지 않았다.** 22:03에 22%였고 22:10에도 22% 근처라 진행 중이다. 실패 요약 줄이 아직 없다.
- 직전의 완주 실행 `t2.txt`(22:00 종료, 1233 s)의 결과는 `8 failed, 3484 passed, 1 deselected`다. 실패 8개는 알려진 red 8개와 정확히 같다(test_current_basis 6, test_s2_values[dc_columns] 1, test_orbit_ties[names0] 1). **알려진 8개 밖의 실패는 0건**이다.
  - 구조 규칙 요약(rule_a~m, copy_manifest)은 모두 위반 0이다.
  - t2는 커밋 `14e0ca2a`(22:01:43) 직전의 worktree 내용으로 돌았다. 커밋 diff는 dispute 문서 하나가 더해진 것 외에 같은 코드로 보이지만, t3 완주로 확정해야 한다.

## 5. 원칙 자기 점검(권고가 근본원칙과 맞는지)

- **graph 단일 정본**: 권고에 새 cache·사본·슬롯이 없다. #1은 READS 선언을 실제 읽기에 맞추는 일이고, 4.1은 읽지 않는 READS를 지우는 일이다. 둘 다 정본 쪽이다.
- **작성자 ≠ 검증자**: code 작성자는 test를 고치지 않는다. 기준선 수치는 감사 변화표가 근거이고 test 주체가 커밋한다. 여기서 쓴 값은 판정이 아니라 분석용 실측이다.
- **기준 약화**: 권고안 세 건 모두 약화가 아니다. #3의 '지우기·toy 변경·정지 단언으로 대체'는 약화이므로 권하지 않고, 하려면 사용자 승인이 필요하다고 적었다.
- **우회·skip 금지**: #3의 harness 수정은 단언을 건너뛰는 것이 아니다. 계약 대상(S1)만 짓는 것이다. 정지가 '실제로 거부함'은 선택 사항 2의 추가 단언으로 고정할 수 있다.
- **원래 취지와 다른 점**: 없다. 다만 다음 둘은 범위 보고 대상이다.
  - K-3 목록 밖 test 2개(test_current_basis, test_orbit_ties)
  - spec card 소비자 표의 achievability 행 정정
