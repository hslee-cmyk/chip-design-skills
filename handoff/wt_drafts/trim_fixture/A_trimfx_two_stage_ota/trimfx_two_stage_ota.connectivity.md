# trimfx_two_stage_ota -- connectivity 표 (후보 A, 초안·사용자 확인용)

* 출처 파일: `wt/_drafts/trim_fixture/A_trimfx_two_stage_ota/trimfx_two_stage_ota.topology.json`
* 만든 방법: 새 엔진 로더 `gmid_engine.authoring.load_topology`(master 944020f, 격리 worktree)로 읽은 `TopologyDoc`에서 직접 뽑았다. `assets/topology_to_markdown.py`는 옛 로더(legacy/stick_diagram.py) 의존이라 쓰지 않았다(T-13 이관 전).
* connectivity_fp = `740df3eb841fce5be20dd0de4179adacf511e51f309d92ebb16459d4111e4954` -- library `two_stage_ota`와 **같다**(로드로 확인). 연결은 원본 복사이고 바꾼 것이 없다.
* 회로: Miller 2단 OTA. 1단 = NMOS 차동쌍 M1·M2 + PMOS 거울 M3(다이오드)·M4 + 꼬리 M5. 2단 = PMOS 공통 소스 M6 + NMOS 전류원 M7. 보상 Rz-Cc 직렬(O1-OUT). 출처 Maloberti p.28-33, 사용자 확정 TQ Q4/Q4'.

## Net별 연결 표

| Net | 구분 | 연결된 단자 | 단자 수 |
|---|---|---|---|
| `CS` | 내부 | M1.source, M2.source, M5.drain | 3 |
| `D3` | 내부 | M1.drain, M3.drain, M3.gate, M4.gate | 4 |
| `N_cc_rz` | 내부 | Cc.t0, Rz.t1 | 2 |
| `O1` | 내부 | M2.drain, M4.drain, M6.gate, Rz.t0 | 4 |
| `OUT` | 포트 single_ended_output | CL.t0, Cc.t1, M6.drain, M7.drain | 4 |
| `bias` | 외부 바이어스(bias_inputs) | M5.gate, M7.gate | 2 |
| `gnd` | 레일 | CL.t1, M5.source, M7.source | 3 |
| `vdd` | 레일 | M3.source, M4.source, M6.source | 3 |
| `vin_n` | 포트 differential_input_n | M1.gate | 1 |
| `vin_p` | 포트 differential_input_p | M2.gate | 1 |

## 소자별 단자

| 소자 | kind | drain | gate | source | bulk |
|---|---|---|---|---|---|
| M1 | nmos | D3 | vin_n | CS | (생략 -- 엔진 기본 규칙) |
| M2 | nmos | O1 | vin_p | CS | (생략 -- 엔진 기본 규칙) |
| M3 | pmos | D3 | D3 | vdd | (생략 -- 엔진 기본 규칙) |
| M4 | pmos | O1 | D3 | vdd | (생략 -- 엔진 기본 규칙) |
| M5 | nmos | CS | bias | gnd | (생략 -- 엔진 기본 규칙) |
| M6 | pmos | OUT | O1 | vdd | (생략 -- 엔진 기본 규칙) |
| M7 | nmos | OUT | bias | gnd | (생략 -- 엔진 기본 규칙) |

| 2단자 소자 | kind | t0 | t1 |
|---|---|---|---|
| CL | capacitor | OUT | gnd |
| Cc | capacitor | N_cc_rz | OUT |
| Rz | resistor | O1 | N_cc_rz |

## trim에 관계된 엔진 유도(실측, 사람 재확인용)

* S1 matching group(`build_s1`): `diff_pair (M1, M2) derived`, `mirror (M3, M4) derived`, `mirror (M5, M7) derived`.
* 주입 쌍(design §9.1 규칙 적용 예상): n_p = `differential_input_p` 멤버(M2)의 drain = **O1**, n_n = M1의 drain = **D3**. 두 게이트가 모두 포트라 극성 판정이 가능하다.
* 출력 단일 -- 균형 기준 = V(OUT) = spec `node_voltage_targets_v.OUT`(사용자 값).
