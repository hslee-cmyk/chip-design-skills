# offset trim 2단계 검증용 시험 회로 초안 (사용자 승인 전)

* 근거: design `docs/02-design/features/offset-trim.design.md` §16.1(trim-design 0f7332a), 사용자 결정 T-9·T-17(`wt/_drafts/user_decisions.md`).
* 상태: **초안이다. 사용자 승인 전에는 쓰지 않는다**(T-9). topology(connectivity)와 spec 값은 사용자 몫이고, 회로 해석은 공동분석이다. 그래서 후보 3개를 내고 하나를 권고한다.
* 저장소는 고치지 않았다. 로드 검사는 격리 복제본 `wt/_scratch_trimfix`(master 944020f, detached)에서만 돌렸고 끝난 뒤 지웠다.

## 1. 후보 비교

| | A `trimfx_two_stage_ota` | B `trimfx_ota5t` | C `trimfx_fd_rcmfb` |
|---|---|---|---|
| 회로 | library `two_stage_ota` 복사(Miller 2단, 7 MOS + Rz·Cc·CL) | 5T OTA(5 MOS + CL). two_stage_ota 1단과 같은 연결, 입력 이름만 맞바꿈 | 완전 차동 1단 + 저항 감지 CMFB(5 MOS + Rcm1·Rcm2 + CL1·CL2), 새로 씀 |
| connectivity 승인 | **새로 승인할 연결 없음**: connectivity_fp 가 library 와 같다(`740df3eb…`, 로드로 확인) | 새 연결(입력 게이트 맞바꿈 포함) 승인 필요 | 새 연결과 회로 해석 승인 필요 |
| 차동 입력(derived diff_pair) | 충족: `diff_pair (M1, M2) derived` | 충족: 같음 | 충족: 같음 |
| 출력 균형 기준 | 단일 출력 -> `node_voltage_targets_v.OUT` 필요(사용자 값) | 단일 출력 -> `node_voltage_targets_v.out` 필요(사용자 값) | **차동 출력 -> 기준 선언 불필요** |
| `offset_in_sigma_mv` 제약 없음 | 충족 | 충족 | 충족 |
| `offset_trim` 선언 | 자리 있음(값 null, 후보 제시) | 같음 | 같음 |
| `origin: fixture`, library 밖 | 충족(초안 폴더) | 충족 | 충족 |
| headroom 창이 비지 않는 (쌍, 극성) | 예상 충족(아래 2절), **1단계 후보표로만 확정** | 예상 충족 | 예상 충족 |
| 목적에 전력·면적 축 | 충족 -- 엔진이 축을 (전력, 면적)으로 고정(DEC-77, `spec_settings.py`). 예산 선언은 PA-1 대기 그대로 | 같음 | 같음 |
| 로더(`load_topology`·`load_sizing_spec`) | 통과(값 자리 채운 변형) | 통과(값 자리 채운 변형) | 통과(초안 그대로도 통과 -- 사용자 값 자리가 offset_trim 뿐) |
| 단계 A(`run_stage_a`, 실 LUT) | **ok, exit 0**, review 0, 정지 0 | **ok, exit 0**, review 0, 정지 0 | **stopped, exit 2** -- CM 루프 '기록만'(`loop_record_only … global_feedback_or_cross_coupled`) 2건 + `dc_role_unresolved_group M3,M4` |
| 주입 쌍(n_p, n_n) 예상 | (O1, D3) | (d1, out) | (vom, vop) |
| 장점 | 연결이 이미 사용자 확정. spec 값 대부분이 two_stage_ota 실제 결정 기록. library 회로와 같은 연결이라 trim 선언 없는 실행을 library 결과와 대조하기 쉽다 | 가장 작다(탐색·SPICE·MC 시간 최소). 극성·DC 해석이 교과서 수준으로 명확 | 기준 DC 결정이 필요 없다. 대칭이라 계통 offset ≈ 0 |
| 단점 | 소자·θ 가 B 보다 많다(보상 Rz·Cc 포함) -> 2단계·TR-7 MC 시간이 길다. 출력 기준 DC 사용자 값 필요 | 새 topology 승인 필요. 회로별 spec 결정 기록이 없어 값 대부분이 다른 회로 차용. 출력 기준 DC 사용자 값 필요 | **지금 엔진으로는 단계 A 에서 정지** -> structure.json 사실(dc_role·ac_ground_exception 류) 사용자 승인과 rule_hash 절차(T-11·T-16)가 먼저 필요. 새 회로라 해석 부담이 가장 크다 |

**권고: A.** 새로 승인할 연결이 없고(지문 동일), 단계 A 가 그대로 통과하며, spec 값 대부분이 실제 사용자 결정 기록이다. 사용자가 새로 정할 값은 출력 기준 DC 하나와 trim 세 값뿐이다. 실행 시간이 문제가 되면 B 를 차선으로 둔다. C 는 structure.json 사실 승인이 선행돼야 하므로 지금은 권고하지 않는다.

* 원래 취지와 다를 수 있는 점(보고): design §16.1 은 '시험 회로'를 따로 두라고 했다. A 는 연결이 library 회로와 같은 **사본**이라 '별도 회로'라기보다 '별도 spec'에 가깝다. 요구 조건(library spec 무변경, library 밖, origin fixture)은 모두 지키지만, 사용자가 '다른 회로'를 뜻했다면 B 를 고르면 된다.
* 차동 출력 후보가 꼭 필요하면 대안 D: library `current_reuse_telescopic_ota` 를 복사하고 spec 에서 `offset_in_sigma_mv` 와 그것을 참조하는 `offset_sys_mv`(value_from_constraint)를 빼는 안. 연결 승인 불필요·structure.json 이미 있음·상보 입력쌍 두 개(D-7)까지 시험되지만 MOS 51개라 2단계·MC 가 가장 무겁다. 이번에는 초안을 만들지 않았다.

## 2. headroom 예상(확정은 1단계 후보표)

크기를 정한 점이 없어 실측하지 못했다. 바닥 = VDSAT + tol_vdsat(수십~200 mV 범위 예상).

* sink(주입 넷 -> gnd): 창 = V(n). 주입 넷은 모두 PMOS 부하 쪽 드레인이라 V(n) ≈ vdd − |VSG| 이하가 아닌 이상 1 V 안팎 -> 넉넉할 것.
* source(vdd -> 주입 넷): 창 = vdd − V(n). A 의 D3·B 의 d1 은 다이오드 넷이라 |VSG(M3)|, A 의 O1 은 |VSG(M6)|, B 의 out 은 출력 기준(0.9 V 후보면 0.9 V), C 는 |VSG(M3)|. 수백 mV -> 바닥보다 클 것으로 예상하나 **약반전 큰 gm/ID 점에서는 좁아질 수 있다**.

## 3. 사용자가 정할 값

| # | 값 | 후보 A | 후보 B | 후보 C | 제안 후보와 근거 |
|---|---|---|---|---|---|
| U1 | 시험 회로 선택 | | | | 권고 A |
| U2 | connectivity 승인 | 원본 사본 확인만 | 새 연결(입력 맞바꿈) 승인 | 새 연결·해석 승인 + structure.json 사실 | 각 폴더 `*.connectivity.md` |
| U3 | `offset_trim.residual_offset_v` (V_res) | 사용자 값 | 사용자 값 | 사용자 값 | **0.002 V**: 시험용으로 N = 3(셀 7개)이 되게. 선형 근사 2^N − 1 ≥ (k·σ_in + \|V_sys\|)/V_res, k = 3, σ_in ≈ 3.3 mV(가정: current_reuse 사용자 예산을 크기 기준으로만 빌림) -> 4.95 -> N = 3. 1단계 σ_in·\|V_sys\| 실측 후 다시 고르기를 권고 |
| U4 | `offset_trim.coverage_multiple` (k) | 사용자 값 | 사용자 값 | 사용자 값 | **3**: 가우스 양측 포함 erf(k/√2) = 99.73 %(4 면 99.994 %) |
| U5 | `offset_trim.trim_temperature_c` | 사용자 값 | 사용자 값 | 사용자 값 | **27.0**: 실행 LUT 측정 조건 temp_c = 27.0(sky130_lut_v2 슬라이스 npz, corner tt) -- design §5.3 정확 일치 규칙. 계획 D-12(T-6) 27 °C 와 같다 |
| U6 | 출력 기준 DC `node_voltage_targets_v` | OUT | out | 불필요 | **0.9 V** = (vdd + gnd)/2(supplies_v 유도, 스윙 대칭점). 대안: 입력 CM 과 같게(β=1) -- input_dc 를 수로 정할 때만 |
| U7 | 다른 회로 값 차용 승인 | two_stage_ota 결정 재사용(전부) | GBW 7 MHz·PM 70°·면적 1.5e-8 m²·CL 3 pF 차용 | GBW·PM·면적 차용(two_stage_ota), CL1·CL2 1 pF·감지 저항 engine(current_reuse) | record 마다 `[… 재사용]`·`[… 값 차용]` 표시 |
| U8 | `offset_excess <=` 유지 여부 | 유지(강등 경로 확인용) | 유지 | 유지 | trim 선언과 함께면 판정에서 빠지고 보고만(§5.2). 빼도 요구 조건 무관 |
| U9 | gain 제약 | 있음(57 dB, 재사용) | 없음(보고만) | 없음(보고만) | 1단 회로는 시험 목적과 무관한 실패를 줄이려고 뺐다 |
| U10 | 남은 결정 대기 | input_dc SP-2, intended_region CI-18, budgets PA-1, front_budget_s PA-2, front_points_rule AC-3 | 같음 | 같음 | library 와 같은 상태로 두었다(엔진이 대기를 '미선언'으로 투영 -- 실행 차단 아님, 단계 A 로 확인) |
| U11 | 승인 뒤 저장 위치 | | | | library 밖. 예: `skills/analog-gmid-design/assets/fixture/trim/`(파일 이름 stem = circuit, spec 은 topology 와 같은 폴더) -- 사용자 결정 |

## 4. 로드 검사 결과

환경: `wt/_scratch_trimfix`(git worktree add --detach master, 944020f), Python 3.14.2, 실 LUT `lut_data/sky130_lut_v2`. 검사 스크립트는 세션 scratchpad 에 두었다(저장소·초안 폴더 밖). 9회로는 돌리지 않았다 -- 시험 후보 3개만.

| 검사 | A | B | C |
|---|---|---|---|
| `load_topology` | 통과 | 통과 | 통과 |
| `load_sizing_spec` 초안 그대로 | 거부: `unknown_key human.offset_trim` + 출력 기준 DC 자리(`type value_v`, `source_record_missing decided`) | 같음 | 거부: `unknown_key human.offset_trim` 만 |
| offset_trim 뺀 변형 | 거부: 출력 기준 DC 자리 2건만 | 같음 | **통과** |
| offset_trim 빼고 사용자 값 자리를 첫 후보로 채운 변형 | 통과(origin fixture, 대기 5건) | 통과 | 통과 |
| `run_stage_a`(채운 변형, 구조 사실 없음) | ok / exit 0 | ok / exit 0 | stopped / exit 2 |

* `offset_trim` 거부는 예상된 것이다: master 의 `spec_schema.HUMAN_OPTIONAL` 에 아직 없다(TR-1 로더 확장 대상, design §5.1). 사용자 값 자리의 거부도 의도한 것이다(값 null = 미정).
* trim 세 값을 후보로 채우면 `{"residual_offset_v": 0.002, "coverage_multiple": 3, "trim_temperature_c": 27.0}` -- 형식은 §5.1(유한 양수·유한 수)을 만족한다. 로더 검사는 TR-1 뒤에만 가능.
* S1 matching group(`build_s1`): 세 후보 모두 `diff_pair (M1, M2) status derived`.

## 5. 확인하지 못한 것

* headroom 창(§9.2), t, σ_in, V_sys -- 크기를 정한 점이 없어 1단계(TR-2) 전에는 잴 수 없다. V_res 후보는 σ_in 가정값에 기대므로 1단계 뒤 재선택이 필요하다.
* `metric_structure.input_cells` 에 M1·M2 가 드는지(§9.1 쌍 규칙의 둘째 조건) -- 단계 A 보고서의 블록 역할(`M1 input`, `M2 input`, stage 1)로 미루어 들 것으로 보이나 그 필드를 직접 읽지는 않았다.
* 단계 B·탐색(GB4 달성가능성, front) -- 돌리지 않았다(로드 검사 범위 밖). 특히 B·C 의 차용 제약(GBW 7 MHz 등)이 달성 가능한지 모른다.
* `offset_trim` 섹션의 로더 동작(§5.2 공존 거부·강등, §5.3 온도 대조) -- TR-1 미구현이라 검사 불가.
* C 의 structure.json 사실로 단계 A 정지가 풀리는지 -- 사실 작성은 사용자 승인 대상이라 시도하지 않았다.
* 후보 B 의 소스 그림 쪽 번호는 two_stage_ota 의 출처(Maloberti p.28-33)를 그대로 적었다 -- 5T 단독 그림 번호는 확인하지 않았다.

## 6. 파일

| 폴더 | 파일 |
|---|---|
| `A_trimfx_two_stage_ota/` | `trimfx_two_stage_ota.topology.json`, `trimfx_two_stage_ota.sizing_spec.json`, `trimfx_two_stage_ota.connectivity.md` |
| `B_trimfx_ota5t/` | `trimfx_ota5t.topology.json`, `trimfx_ota5t.sizing_spec.json`, `trimfx_ota5t.connectivity.md` |
| `C_trimfx_fd_rcmfb/` | `trimfx_fd_rcmfb.topology.json`, `trimfx_fd_rcmfb.sizing_spec.json`, `trimfx_fd_rcmfb.connectivity.md` |

* 값 표기 규칙: 사용자 값 자리 = `value`/`value_v` null + `_user_value`(무엇인지) + `_candidate`(후보와 근거). 다른 spec 에서 옮긴 값은 원 결정 기록·날짜를 그대로 두고 record 앞에 `[… 재사용]`/`[… 값 차용]`을 붙였다 -- 이 회로 적용 승인은 아직 없다.
* 배선: 승인되면 이 파일이 TR-5b·5c·7 의 2단계 완료 조건 입력이 된다(design §16.1 승인 절차 (3)). 승인 전에는 어디에도 연결하지 않는다.


## 7. 사용자 결정 (2026-10-15 "권고대로", user_decisions.md T-24~T-28)

* 채택: A. trim 값 {0.002 V, k = 3, 27.0 °C}. 출력 기준 DC는 T-20 규칙 (e) -- 3절 U6의 0.9 V 후보는 폐기. offset_excess 유지, two_stage_ota 값 전부 재사용.
* 저장소 반영: `skills/analog-gmid-design/assets/fixture/trim/`, TR-1(로더 확장)과 '출력 기준 DC' 기능 병합 뒤. B·C 초안은 참고용으로만 남는다.
