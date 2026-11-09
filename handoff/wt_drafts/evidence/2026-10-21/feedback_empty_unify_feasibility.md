# spec `feedback` 빈 list `()` 의미 통일 실현 가능성 -- β=1 폐루프로 (2026-10-21)

- 기준: 저장소 `chip-design-skills` master `c237d96e`, 읽기 전용. 경로 약어 `E/` = `skills/analog-gmid-design/gmid_engine/`, `O/` = `skills/analog-gmid-design/tools/spice_oracle/`, `A/` = `skills/analog-gmid-design/assets/`.
- 측정 스크립트·결과: `C:/Users/HSLEE/AppData/Local/Temp/claude/C--Users-HSLEE-Documents-Todoc-fpga-chip-design-skills/63c6146a-ab1d-4035-a169-bae810986922/scratchpad/noise_beta1/toy.py`, 같은 폴더 `toy_results.jsonl`.
- 표기: 근거 없는 주장은 '미확인'.

## 0. 결론 먼저

1. `()` 의미가 갈린 곳은 **엔진 잡음 한 곳뿐**이다: `E/metrics/noise_plan.py:9-10, 40-41`(`NoisePlan("open")` = 입력 고정 개루프 출력 잡음). 나머지 독자는 모두 β=1 루프다(§1 표).
2. `open` 모드가 영향을 주는 metric은 `noise_out_int_vrms` **하나**다(`E/metrics/ss_metrics.py:319-321` -- 다른 잡음 metric 3개는 feedback과 무관하게 개루프 전달 뷰). 그런데 `()` 회로 12개 중 `noise_out_int_vrms` 제약을 가진 회로는 **0개**다(§3). 통일해도 지금 코퍼스의 판정 결과는 바뀌지 않는다(값이 계산되는 경로 자체가 없다).
3. `open` 모드는 승인된 결정에 근거가 없다. DEC-96 (3)·design 41 §7.1 표 1753행은 `noise_out_int_vrms` 를 "**폐루프** 출력 적분 잡음"으로만 정의한다. `open` 은 U8 구현 커밋 `f59a7636`(2026-10-09)에서 들어온 as-built 확장이다. UD 9번(`wt/_drafts/user_decisions.md:133`)은 "없으면 beta=1 루프"다. 통일은 결정과 충돌하지 않고 오히려 결정에 맞춘다(§5).
4. 엔진 구현은 **새 계·새 생산자 없이** 가능하다: β=1 닫힘 = 포트 전달 뷰 열(같은 G·C, 같은 가중 w)에 대한 rank-1 닫힘이다. 출력 잡음 전달은 Z_k,cl = Z_k / (1 + σ·H)(σ = 기준점 Re H(0)의 부호, H = 같은 열의 포트 전달 = β=1 PM이 쓰는 T = A와 같은 양). `graph.ss_nodal`·`icm_config` 의 반전 입력 식별은 **필요 없다**(가중 w로 DM만 닫으므로). 단 미구현이고 극점·꼬리 처리(§2.3)는 design이 정해야 한다.
5. 오라클은 지금 `()` 회로의 `noise_out_int_vrms` 를 **잴 수 없다**(`unavailable`, `O/oracle_noise.py:252-261`). 같은 β=1 닫힘(VCVS `Ecl_`)은 안정성 과도용으로 이미 있다(`O/oracle_netlist.py:589-593, 633-642`) -- `.noise` 용으로 옮기는 코드는 새로 써야 한다.
6. **권고: 옵션 B(β=1 폐루프로 통일, 엔진 rank-1 닫힘 + 오라클 Ecl `.noise`)**. 단 착수 순서는 계획 먼저(N3.8·DEC-96 (3) 문언에 `()` = β=1 폐루프를 적고) -> design 41 §7.3 -> 구현. 당장 판정이 바뀌는 회로가 없으므로 급하지 않다. 최소 조치로는 옵션 C(`()` -> 정의 불능, 개루프 의미 삭제)가 같은 커밋 하나로 가능하다.

## 1. `()`·None·tuple 독자 전수와 각자의 의미

grep: `feedback` (tests·legacy 제외 108행), `noise_plan`, `NoiseDecl`, `beta`, oracle `feedback_passives`.

| 독자 | 위치 | `()`(빈) | None / PendingMark | 비지 않은 tuple |
|---|---|---|---|---|
| spec 정의(정본) | `E/authoring/spec_elements.py:19-20` | "되먹임 수동소자 없음 = **β=1 루프**, UD 9번" | `{"pending"}` -> PendingMark | 절단 규칙 L2 |
| 루프 뷰 유도 | `E/authoring/spec_views.py:90-98` | `ViewDecl(loop, beta=BETA_UNITY, weights=port.weights, sense=port.sense)` = **β=1**(포트 뷰와 같음) | None -> `ViewDecl(loop)`(유도 안 함), Pending -> pending 뷰 | β 루프 `cuts` |
| 제약 뷰 | `E/authoring/spec_constraints.py:19-20` | β=1 포트 뷰 | pending 전파 | β 루프 |
| spec 모델 | `E/authoring/spec_model.py:105` | `beta` = unity(빈 list) | -- | declared |
| PM | `E/metrics/loop_analysis.py:13-14` | "빈 list 면 β = 1 -- 포트 전달 뷰 Factor 하나(T = A)" | -- | ProbeFactor(Middlebrook) |
| 탐색 단계 A 절단 | `E/pipeline/stage_a.py:22, 165` | β=1 은 내부 절단 아님(`beta != declared` 만 수집) | -- | 테스트벤치 루프 |
| 잡음 선언 블록 | `E/search/noise_decl.py:7`, `E/search/search_context.py:184` | "빈 tuple = **되먹임 없음**" -> `NoiseDecl(())` | PendingMark·None -> None | tuple 그대로 |
| 잡음 선언 형식 | `E/metrics/noise_types.py:24` | "빈 tuple 이면 **되먹임 없음**" | 결정 대기 | -- |
| **잡음 계획** | `E/metrics/noise_plan.py:9-10, 40-41` | **`open`: 입력 고정 개루프 출력 잡음(입력 단락)** | `undefined` `noise_feedback_undeclared` | `closed`(입력 쪽 단자 자유) |
| 잡음 적분 | `E/metrics/noise_integral.py:7` | "되먹임 없음이면 입력 고정 계" | -- | 폐루프 계 |
| ss 평가 | `E/metrics/ss_metrics.py:26-27, 319-332, 412` | `free = frozenset()` -> 입력 고정 계 | undefined | `plan.free_nets` |
| 출발 하한(파일럿) | `E/search/iv_noise.py:11, 33` | 해당 없음(β 미전달 `feedback_factor_beta_unavailable` 은 선언 회로 몫) | -- | -- |
| 오라클 PM | `O/oracle_simulate.py:44-45, 1079-1083` | `feedback_passives` 없음 -> **L = A(β=1)**, `pm_definition = beta_1`, 닫힘 부호 = 기준점 Re A 부호 | -- | β 루프 넷리스트 |
| 오라클 루프 넷리스트 | `O/oracle_netlist.py:1286-1293` | `meta.loop = None` | -- | 루프 넷리스트 작성 |
| 오라클 잡음 폐루프 | `O/oracle_noise.py:252-261` | **`unavailable`**("feedback_passives 가 없어 루프 넷리스트가 없다") | -- | `.loop.cir` `.noise` |

다른 의미를 쓰는 곳: 엔진 잡음 사슬(`noise_decl`·`noise_types`·`noise_plan`·`noise_integral`·`ss_metrics` docstring) 하나뿐이다. 오라클 잡음은 의미를 정하지 않고 '잴 수 없음'이다(β=1 도 개루프도 아님). `E/graph/*` 의 `feedback_shared`·`local_feedback`(`E/graph/s1_values.py:97`, `E/graph/s1v_values.py:120`)은 레이아웃·루프 분류 어휘로 spec feedback과 무관하다.

test 의존(통일하면 바뀌는 것): `E/tests/metrics/test_noise_plan.py:32-33`(`mode == "open"`), `E/tests/metrics/test_noise_integral.py:59`(`d["mode"] == "open"`), `E/tests/metrics/noise_cases.py:146-149`(`mode="open"` 기본, `NoiseDecl(feedback=())`), `E/tests/metrics/test_noise_devices.py:58`, `E/tests/search/test_search_context.py:264`(선언 값 자체 -- 통일과 무관하게 유지 가능).

## 2. 지금의 폐루프 모드와 β=1 닫힘에 필요한 것

### 2.1 지금 폐루프 모드(선언 소자)

- `noise_plan`: 소자마다 입력 포트 넷 쪽 단자(정확히 1개)를 `free_nets` 로 둔다(`E/metrics/noise_plan.py:42-53`).
- `ss_metrics._noise_job`: 고정 = `ledger.base − free`, 계 = `ledger.full((), free)`, 감지 행 = 전달 뷰 감지(`E/metrics/ss_metrics.py:322-332`). `ledger.base` = 교류접지 ∪ 입력 넷(`ss_metrics.py:102`).
- 즉 '닫힘'은 입력 넷을 미지수로 푸는 것이고, 실제 되먹임 경로는 topology 수동소자(Cf 등)가 이미 G·C 에 들어 있어서 성립한다. 소자가 없는 `()` 에는 풀 단자도, 닫을 경로도 없다.

### 2.2 소자 없는 β=1 닫힘 -- 기존 양만으로

계는 순수 nodal(`E/metrics/mna_types.py:57-79` -- G, C, BG, BC, sense_rows; 가지 전류 미지수·VCVS 스탬프 없음). 그래서 '출력을 입력에 잇는' 이상 원은 스탬프로 넣을 수 없다. 대신 포트 전달 뷰 열을 쓰면 닫힘이 rank-1 갱신이 된다:

- 포트 전달 뷰 열 j(가중 w_k 로 입력 넷 구동, 같은 G·C -- `ss_metrics.py:26` "개루프 세 metric 은 gain metric 과 같은 계·같은 전달 뷰 열")에서 x = A⁻¹(b_j·u + e), H = s·x(u = 1, e = 0).
- 닫힘 u = −σ·(s·x)(σ = Re H(0) 부호, 음되먹임). 잡음원 k 에 대해 v_out = Z_k + H·u -> **Z_k,cl = Z_k / (1 + σ·H)**. 같은 식이 kT/C 항 T_s 에도 그대로다.
- 필요한 양 Z_k, H 는 `noise_transfer` 가 이미 같은 수반 풀이에서 낸다(`E/metrics/noise_transfer.py:5-7` -- 열 j 가 주어지면 H 도 계산; 입력 환산 분모). 새 조립 0, 새 풀이 0.
- 이 H 는 β=1 PM 의 T = A(`loop_analysis.py:13-14`, 같은 포트 뷰 weights·sense -- `spec_views.py:98`)와 같은 정의다. 오라클 β=1 도 같은 꼴: `Ecl_<넷>` 이 입력 넷을 g = −σ·w_k·H 로 구동(`O/oracle_netlist.py:589-593`).
- 차동: 가중 w 가 DM 만 나눠 닫고 입력 CM 은 고정 -- 사용자 결정 O-68 (2)(`user_decisions.md:689`, DM 만 닫음 (in+ − in−) = −(Vop − Von))와 같은 꼴이다. 단일 출력·차동 입력(two_stage_ota 등)도 같은 가중 닫힘이라 반전 입력 식별이 필요 없다. 물리 follower(in− = out, in+ = AC 접지)와는 입력 CM 이 H/2 만큼 움직이는 성분만 다르다(CM 이득 × H/2 -- CMRR 이 크면 작음, 크기는 미확인).
- `graph.ss_nodal`·`icm_config`·`kvl_sensitivity`: 현재 엔진 코드에 **없다**(`grep -rn "ss_nodal\|icm_config\|kvl_sensitivity" E/` 결과 0, tests 제외). design 41 v1.12.4 IT-2 범위(41:730-739)의 DC 측정 구성 블록이다. 잡음은 이 DC 계(`conductance_matrix`, G 만)가 아니라 소신호 MNA(`ss.circuit` -> `_Ledger`, G·C)를 쓴다. 따라서 잡음 β=1 닫힘은 그 필드를 읽을 이유가 없고, 읽지 않으므로 둘째 생산자 문제도 없다. 반전 입력 식별(41:734 (1))도 가중 닫힘에서는 쓰지 않는다.

### 2.3 design 이 정해야 할 것(미구현)

- 극점·격자: `noise_integral` 의 첫 격자와 상한 시작점은 "계의 유한 극점"(`noise_integral.py:8-9`)이다. 나눗셈 닫힘만 하면 폐루프 극점(1 + σH = 0의 근, UGF 근처 peaking)이 격자에 없다. 두 길: (a) G_cl = G + σ·BG_j·s, C_cl = C + σ·BC_j·s(rank-1, 같은 블록 안 지역 값)로 폐루프 계를 만들어 극점·풀이를 그대로 쓰기, (b) 나눗셈 + 이분 오차 제어에 맡기기. (a)가 기존 경로(계 하나 -> 극점 -> 적분)를 그대로 쓴다. 어느 쪽이든 새 graph 필드·cache 는 필요 없다(같은 `metrics_ss` 블록 안 지역 계산, 기존 closed 모드의 `ledger.full((), free)` 과 같은 위치).
- 불안정: β=1 루프가 불안정하면(T 에 우반면 극점 또는 폐루프 우반면 극점) 적분은 정의 불능이어야 한다. PM 쪽 `loop_open_rhp_poles`(`loop_analysis.py:17-21`)와 같은 판정 자리를 쓸지 정해야 한다.
- σ: Re H(0) = 0 이면 정의 불능(오라클 `O/oracle_simulate.py:1083-1092` 과 같은 규칙).
- 회로 종류: common_gate_amplifier(단일 입력 CG, 비반전)·pushpull_follower_buffer(이미 follower, |A|≈1 -> β=1 루프 이득 ≈ 1)에서 β=1 닫힘은 수학적으로 정의되지만 물리 의미는 약하다. PM 도 이미 같은 정의를 쓰고 있으므로(UD 9) 일관성은 유지된다.

## 3. 회로별 선언과 동작 변화 크기

`A/library/*.sizing_spec.json`·`A/heldout/*.sizing_spec.json` 13개 실측(python 으로 `human.feedback`·`human.constraints` 읽음):

| 회로 | feedback | 잡음 제약 |
|---|---|---|
| current_reuse_telescopic_ota(파일럿) | `[Cf1, Cf2]` | `noise_out_int_vrms` |
| two_stage_ota, two_stage_ota_sf, folded_cascode, ngcc_3stage_ff, nmcnr_amplifier, sf_pushpull_output_opamp, common_gate_amplifier | `[]` | `noise_excess_th` 만 |
| pushpull_follower_buffer | `[]` | 없음(보고만) |
| heldout cnr_ota, erfc_ota, r2r_opamp, rfc_ota | `[]` | 없음 |

`[]` 회로 = 12개(library 8 + heldout 4). 13번째 `[]` 는 test 픽스처 `E/tests/authoring/fixtures/spec/fx_spec_ref.sizing_spec.json:16` 이다(요청의 '13'이 이것을 센 것인지는 미확인).

- `noise_excess_th`·`noise_th_in_v2hz`·`noise_fc_in_hz` 는 `FIELD_OUT` 이 아니라 항상 `("view", "open", ...)` 개루프 전달 뷰다(`ss_metrics.py:319-321`) -- feedback 의미와 무관, **통일해도 값 불변**.
- `noise_out_int_vrms` 는 요청될 때만 계산된다(`ss_metrics.py:403-412` -- `noisy` 요청 목록). `[]` 회로는 이 metric 을 요청하지 않으므로 지금 판정·보고 변화 **0**.
- 따라서 변화는 "앞으로 누군가 `[]` 회로에 `noise_out_int_vrms` 제약을 선언할 때"의 값 정의다.

크기 추정(toy, 엔진·회로 실측 아님 -- 2극 증폭기 A(s) = A0/((1+s/p1)(1+s/p2)), 입력 환산 S_in = 1e-16·(1 + 1e5/f) V²/Hz, f = 1 Hz~100 GHz 적분; 결과 `toy_results.jsonl`):

| 비슷한 회로(spec 하한 사용) | A0 | GBW | p2 | open(개루프) Vrms | β=1 폐루프 Vrms | 비(rms) |
|---|---|---|---|---|---|---|
| two_stage_ota(gain ≥ 57 dB, GBW ≥ 7 MHz) | 57 dB | 7 MHz | 15.4 MHz | 6.85 mV | 35.5 µV | 193 |
| ngcc_3stage_ff(gain ≥ 111 dB, GBW ≥ 10 MHz) | 111 dB | 10 MHz | 22 MHz | 2.05 V | 41.7 µV | 49 225 |
| folded_cascode 꼴(가정 70 dB, 20 MHz) | 70 dB | 20 MHz | 60 MHz | 29.8 mV | 57.5 µV | 517 |

- 물리 해석: 열잡음 항은 open ≈ S_in·A0·GBW·π/2, β=1 ≈ S_in·GBW·π/2 -> 전력비 ≈ A0(1/f 항은 더 크다 -- 저주파에서 |A|² = A0² 가 1/f 를 그대로 키움). ngcc 처럼 open 값이 레일을 넘는(2 V rms) 경우가 있어, 개루프 출력 적분 잡음은 고이득 증폭기에서 물리적으로 의미 없는 값이다. β=1 폐루프 값은 입력 환산 잡음을 폐루프 대역(≈ GBW)으로 자른 값이라 spec 단위(µVrms)와 맞는다.
- p2 배치(2.2·GBW, 3·GBW)는 가정이다. 실제 회로 값은 미확인(봉인 스냅샷에서 엔진 잡음을 돌린 측정 없음 -- 사이징된 스냅샷 실행은 이 작업 범위·턴 안에서 하지 않음).

## 4. 오라클

- 지금: `noise_closed_loop` 는 `meta.loop` 가 없으면 `status = unavailable`(`O/oracle_noise.py:252-261`). `meta.loop` 는 `feedback_passives` 가 있을 때만 생긴다(`O/oracle_netlist.py:1286-1293`). -> `[]` 회로 `noise_out_int_vrms` 는 개루프로도 β=1 로도 재지 않는다.
- 재사용 가능한 부품: `stability_netlist(mode="beta_1")`(`O/oracle_netlist.py:585-642`)가 입력 넷의 테스트벤치 원(`Cac_·Vac_·Vdc_·Ldc_·Efb_·Vofs_·Lfb_`)을 빼고 `Ecl_<넷> <넷> ecl_<넷> <출력쌍> g`, g = −σ·w_k 로 β=1 루프를 닫는다(동작점 유지: V0 = V_op − g·H_op). `.noise v(out) Vcl_<넷>` 으로 쓰려면 Vcl 의 PULSE 를 DC 로 바꾼 `.noise` 용 변형과 그 측정 함수(`oracle_noise.py` 의 적분 되풀이 재사용)가 새로 필요하다. 과도용으로 choke 를 `Itb_`·`.ic` 로 바꾼 부분(`oracle_netlist.py:596-603`)이 `.noise`(AC)에서도 필요한지는 미확인(AC 에서는 큰 L 이 열린 회로라 원래 choke 를 둬도 될 가능성 -- 미측정).
- ngspice `.noise` 가 E(VCVS) 닫힘 넷리스트에서 정상 동작하는지·엔진 rank-1 값과 맞는지: 미측정.
- 엔진·오라클 정의 일치: 둘 다 같은 포트 가중 w·같은 부호 σ(Re A(0))·DM 만 닫음 -> 같은 정의(PM β=1 과도 같은 정의 -- `oracle_simulate.py:1083` vs `spec_views.py:98`).

## 5. 계획·결정 문언과의 충돌 점검

| 문언 | 위치 | `()` = β=1 폐루프 통일과 |
|---|---|---|
| UD 9 "선언된 되먹임 수동소자가 있으면 그 beta 루프, 없으면 beta=1 루프" | `wt/_drafts/user_decisions.md:133` | PM 결정이지만 spec 정의 정본(`spec_elements.py:19-20`)이 이를 인용 -- **일치** |
| DEC-96 (3) `noise_out_int_vrms`(폐루프 출력 적분 잡음), 파일럿만 제약, 나머지는 `noise_excess_th` | 계획 296행 | 폐루프만 정의 -- **일치**(open 은 정의에 없음) |
| 계획 N3.8 잡음 "파일럿 폐루프 모드는 선언된 되먹임 요소로 루프를 닫고" | 계획 599행 | 선언 소자 경우만 적음 -- `()` 경우는 **공백**, 계획에 한 줄 추가 필요 |
| design 41 §7.1 표 `noise_out_int_vrms` = "폐루프 … 선언된 되먹임 β로 루프를 닫은 테스트벤치" | design 41:1753 | **일치**, `()` 공백 |
| design 41 §7.3 폐루프 모드(Cf1·Cf2) | design 41:1829-1833 | `()` 공백 |
| design 41 §7.6 오라클 폐루프 metric = 파일럿 조건 | design 41:1882-1883 | `()` 공백 |
| O-68 (2) 차동 DM 만 닫음 | `user_decisions.md:689` | DC ICMR 측정 구성 결정. 잡음 β=1 가중 닫힘도 DM 만 -- **같은 꼴**, 인용 가능 |
| `open` 모드 | `noise_plan.py:9-10`, 커밋 `f59a7636` | 계획·design·user_decisions 어디에도 승인 문언 없음(grep "open"·"입력 고정"·"개루프 출력 잡음" 0) -- **as-built 이탈**, 통일은 이것을 지우는 것 |

결론: 승인된 결정과 충돌하지 않는다. 다만 `()` 경우를 계획(N3.8 잡음·DEC-96 (3))에 먼저 적어야 한다(계획 먼저 규칙). 지금 `open` 은 계획에 없는 as-built 결정이라 '원래 취지와 다름' 보고 대상이다.

## 6. 옵션

| 옵션 | 내용 | 범위 | 장점 | 단점 |
|---|---|---|---|---|
| A 현행 유지 | `()` = 잡음에서만 개루프 | 0 | 작업 없음 | 한 spec 값이 두 뜻(사용자가 피하려는 오류), 고이득 회로에서 물리 무의미 값(레일 초과) |
| **B β=1 폐루프 통일(권고)** | 엔진: `noise_plan` `()` -> `"unity"` 모드, `_noise_job` 이 포트 전달 뷰 열로 rank-1 닫힘(Z/(1+σH) 또는 G_cl·C_cl); 오라클: `beta_1` Ecl `.noise` | 계획 N3.8·DEC-96 (3) 한 줄 -> design 41 §7.3·§7.6 -> 엔진(`noise_plan`·`ss_metrics`·`noise_integral` 극점) + 오라클(`oracle_noise`·`oracle_netlist`) + test 5곳 | 정의 하나, PM 과 같은 H·같은 가중·같은 σ, 새 graph 필드·cache 0, 반전 입력 식별 불필요 | 오라클 새 함수, 극점·불안정 판정 design 필요, 지금 코퍼스엔 소비 제약 없음(가치는 미래 선언용) |
| C `()` -> 정의 불능 | `noise_plan` `()` 도 `undefined`(`noise_feedback_beta1_unimplemented` 같은 사유) | `noise_plan.py`·docstring 3곳·test 3곳 | 즉시 잘못된 의미 제거, 판정 변화 0 | 기능 공백(β=1 잡음 값을 못 냄) |

권고 = B. 순서: 계획 개정(`()` = β=1 폐루프, 포트 전달 뷰 가중 닫힘, DM 만 -- O-68 (2) 인용, σ = Re H(0) 부호) -> design 41 §7.3 '폐루프 모드' β=1 갈래·§7.6 오라클 `beta_1` `.noise` -> design-validator·계획 대조 gap -> 구현. B 가 늦어지면 그 사이 C 를 먼저 넣어 두 의미를 없앤다(C 의 코드는 B 에서 그대로 대체된다 -- 버려지는 코드 없음: `undefined` 갈래가 `unity` 갈래로 바뀜).

## 7. 실현 가능성 점검표

| 항목 | 상태 | 근거 |
|---|---|---|
| 필요한 양 존재 | Z_k, H(같은 수반 풀이) 있음 | `E/metrics/noise_transfer.py:5-7` |
| 포트 전달 뷰 열·가중 | 있음(β=1 루프 뷰 = 포트 뷰 weights·sense) | `E/authoring/spec_views.py:98`, `E/metrics/ss_metrics.py:26` |
| 부호 σ | 엔진 PM 은 부호 무관(T(0) 기준) -> 잡음용 σ 는 H(0) 실수부에서 새로 읽음(같은 블록 지역 값) | `loop_analysis.py:15-16`, 오라클 `oracle_simulate.py:1083` |
| 단위 | V(Vrms), 기존 `out_int_vrms` 그대로 | `E/metrics/registry.py:54` |
| 대표값 | toy: β=1 35~58 µVrms vs open 6.8 mV~2 V(비 193~49 225) | §3 표, `toy_results.jsonl` |
| 엔진 경로 | `noise_plan` -> `_noise_job` -> `noise_integral`(계 극점·적분) | `ss_metrics.py:319-332, 412`, `noise_integral.py:7-9` |
| graph 규칙 | 새 필드·cache·sctx 슬롯 0; 같은 `metrics_ss` 블록 안 지역 계산(기존 closed 모드와 같은 자리); `ss_nodal`/`icm_config` 미사용 -> 둘째 생산자 없음 | §2.2 |
| 오라클 경로 | 부품 있음(`stability_netlist` beta_1), `.noise` 용 함수 없음 | `O/oracle_netlist.py:585-642`, `O/oracle_noise.py:252-261` |
| 소비자 | 지금 `[]` 회로의 `noise_out_int_vrms` 제약 0 -> 값 소비 0 | §3 |

## 8. 동작 변화 목록(옵션 B)

1. `noise_plan(ss, NoiseDecl(()))` -> `mode "open"` 대신 β=1 모드(이름은 design 몫). `free_nets` 없음, 대신 닫힘 열 정보.
2. `noise_out_int_vrms` 를 `[]` 회로에 요청하면 값이 open 대비 대략 √A0 배 이상 작아진다(toy 193~49 225 배, rms).
3. 루프가 불안정하거나 σ 를 못 정하면 `noise_out_int_vrms` 정의 불능(새 사유 코드 -- design 몫).
4. `noise_excess_th`·`noise_th_in_v2hz`·`noise_fc_in_hz`·`noise_report`: 불변(`ss_metrics.py:319-321`).
5. 파일럿(선언 Cf1·Cf2): 불변(`closed` 갈래 그대로).
6. 오라클 `[]` 회로 `noise_out_int_vrms`: `unavailable` -> 측정값(새 함수 생긴 뒤).
7. test: `test_noise_plan.py:32-33`, `test_noise_integral.py:59`, `noise_cases.py:146-149`(기본 mode "open"), `test_noise_devices.py:58` 기대값 변경 -- test author 몫(작성자 ≠ 검증자).
8. docstring: `noise_plan.py:9-10`, `noise_types.py:24`, `noise_decl.py:7`, `noise_integral.py:7`, `ss_metrics.py:26-27`.

## 9. 미확인

- 실제 회로(봉인 스냅샷)에서 엔진 open vs β=1 값: 미측정(toy 만).
- 물리 follower 닫힘(in− = out, in+ 접지)과 가중 DM 닫힘의 잡음 차이(CM 이득 항): 미측정.
- ngspice `.noise` 가 `Ecl_` VCVS 닫힘 넷리스트에서 정상 동작하는지, choke 치환이 `.noise` 에도 필요한지: 미측정.
- 12개 `[]` 회로의 β=1 루프 안정성(PM 값·우반면 극점) 현황: 이 작업에서 보지 않음.
- 요청의 '13 회로' 집계 기준: library 8 + heldout 4 = 12 + test 픽스처 1 로 추정, 미확인.
