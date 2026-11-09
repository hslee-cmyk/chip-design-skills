# trimfx_ota5t -- connectivity 표 (후보 B, 초안·사용자 확인용)

* 출처 파일: `wt/_drafts/trim_fixture/B_trimfx_ota5t/trimfx_ota5t.topology.json`
* 만든 방법: 새 엔진 로더 `load_topology`(master 944020f, 격리 worktree)로 읽어 직접 뽑았다(옛 `topology_to_markdown.py` 미사용, T-13 이관 전).
* connectivity_fp = `818d1570e8eb4c2307aa85e65fbe204ba542fd82ba3b48f6cd57cfa35dcad479`
* 회로: 5 트랜지스터 OTA. library `two_stage_ota` 1단(M1~M5)과 같은 연결에서 2단·보상을 떼고 1단 출력을 out 포트로 둠. **바꾼 점(사람 확인 필요)**: 단일 단에서 vin_p -> out 이 비반전이 되도록 두 입력 게이트 넷을 맞바꿨다(two_stage_ota 에서는 M1.gate = vin_n, M2.gate = vin_p).
* 넷 이름 대응: d1 = two_stage_ota 의 D3, out = O1, tail = CS.

## Net별 연결 표

| Net | 구분 | 연결된 단자 | 단자 수 |
|---|---|---|---|
| `bias` | 외부 바이어스(bias_inputs) | M5.gate | 1 |
| `d1` | 내부 | M1.drain, M3.drain, M3.gate, M4.gate | 4 |
| `gnd` | 레일 | CL.t1, M5.source | 2 |
| `out` | 포트 single_ended_output | CL.t0, M2.drain, M4.drain | 3 |
| `tail` | 내부 | M1.source, M2.source, M5.drain | 3 |
| `vdd` | 레일 | M3.source, M4.source | 2 |
| `vin_n` | 포트 differential_input_n | M2.gate | 1 |
| `vin_p` | 포트 differential_input_p | M1.gate | 1 |

## 소자별 단자

| 소자 | kind | drain | gate | source | bulk |
|---|---|---|---|---|---|
| M1 | nmos | d1 | vin_p | tail | (생략 -- 엔진 기본 규칙) |
| M2 | nmos | out | vin_n | tail | (생략 -- 엔진 기본 규칙) |
| M3 | pmos | d1 | d1 | vdd | (생략 -- 엔진 기본 규칙) |
| M4 | pmos | out | d1 | vdd | (생략 -- 엔진 기본 규칙) |
| M5 | nmos | tail | bias | gnd | (생략 -- 엔진 기본 규칙) |

| 2단자 소자 | kind | t0 | t1 |
|---|---|---|---|
| CL | capacitor | out | gnd |

## 극성 확인(사람 재확인용)

vin_p 상승 -> M1 전류 증가 -> M3 전류 증가 -> 거울 M4 가 out 으로 더 많이 공급 -> out 상승. vin_n 상승 -> M2 가 out 에서 더 많이 끌어냄 -> out 하강. 따라서 vin_p -> out 비반전.

## trim에 관계된 엔진 유도(실측)

* S1 matching group: `diff_pair (M1, M2) derived`, `mirror (M3, M4) derived`.
* 주입 쌍(design §9.1 예상): n_p = M1.drain = **d1**, n_n = M2.drain = **out**.
* 출력 단일 -- 균형 기준 = V(out) = spec `node_voltage_targets_v.out`(사용자 값).
