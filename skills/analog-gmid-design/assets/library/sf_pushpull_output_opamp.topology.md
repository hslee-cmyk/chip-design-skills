# sf_pushpull_output_opamp -- topology connectivity table

소스: `assets/library/sf_pushpull_output_opamp.topology.json`. 이 파일은 `topology_to_markdown.py`가 topology.json에서 그대로 파생시킨 것 -- 손으로 고치지 말고 topology.json을 고친 뒤 다시 생성할 것.

## ⚠️ 자동 플래그 (사람 재확인 필요)

- **구동 소자 없는 net(gate로만 참조됨)**: vin_n, vin_p
  이 net을 source/drain으로 쓰는 소자가 topology.json에 없습니다 -- 외부 입력 핀이면 정상이지만, 내부에서 생성돼야 하는 신호라면 그걸 만드는 소자/감지망이 누락된 것일 수 있습니다.

## 📄 출처 매니페스트 (`source_manifest`)

- 그림/쪽: Allen Lecture 26, Page 26-6
- 소자 22개, 수동소자 5개 (로더가 netlist·passive_elements 개수와 대조)

## Net별 연결 표 (이 net에 물린 모든 단자)

| Net | 연결된 단자 (device.terminal) | 단자 수 |
|---|---|---|
| `N1` | M1.drain, M10.gate, M5.gate, R1a.t1 | 4 |
| `N1112` | M11.drain, M12.source | 2 |
| `N12` | M12.drain, M13.gate, M15.gate, R1c.t0 | 4 |
| `N13` | M13.drain, M14.gate, M16.gate, M20.gate, R1c.t1 | 5 |
| `N1314` | M13.source, M14.drain | 2 |
| `N1516` | M15.source, M16.drain | 2 |
| `N17` | M17.drain, M18.source, M22.gate | 3 |
| `N2` | M12.gate, M2.drain, M7.gate, R1b.t1 | 4 |
| `N20` | M19.source, M20.drain, M21.gate | 3 |
| `N5` | M17.gate, M5.drain, M6.gate, M9.gate, R1a.t0 | 5 |
| `N56` | M5.source, M6.drain | 2 |
| `N7` | M11.gate, M7.drain, M8.gate, R1b.t0 | 4 |
| `N78` | M7.source, M8.drain | 2 |
| `N910` | M10.source, M9.drain | 2 |
| `NB` | IBias.t1, M3.gate, M4.drain, M4.gate | 4 |
| `TAIL` | M1.source, M2.source, M3.drain | 3 |
| `Y` | Cc.t0, M10.drain, M15.drain, M18.gate, M19.gate | 5 |
| `agnd` | CL.t1, Cc.t1 | 2 |
| `vdd` | IBias.t0, M11.source, M17.source, M19.drain, M22.drain, M6.source, M8.source, M9.source | 8 |
| `vin_n` ⚠️ | M2.gate | 1 |
| `vin_p` ⚠️ | M1.gate | 1 |
| `vout` | CL.t0, M21.source, M22.source | 3 |
| `vss` | M14.source, M16.source, M18.drain, M20.source, M21.drain, M3.source, M4.source | 7 |

## 소자별 연결 표 (name/kind/source/drain/gate)

| Name | Kind | Source | Drain | Gate |
|---|---|---|---|---|
| M1 | nmos | `TAIL` | `N1` | `vin_p` |
| M10 | pmos | `N910` | `Y` | `N1` |
| M11 | pmos | `vdd` | `N1112` | `N7` |
| M12 | pmos | `N1112` | `N12` | `N2` |
| M13 | nmos | `N1314` | `N13` | `N12` |
| M14 | nmos | `vss` | `N1314` | `N13` |
| M15 | nmos | `N1516` | `Y` | `N12` |
| M16 | nmos | `vss` | `N1516` | `N13` |
| M17 | pmos | `vdd` | `N17` | `N5` |
| M18 | pmos | `N17` | `vss` | `Y` |
| M19 | nmos | `N20` | `vdd` | `Y` |
| M2 | nmos | `TAIL` | `N2` | `vin_n` |
| M20 | nmos | `vss` | `N20` | `N13` |
| M21 | pmos | `vout` | `vss` | `N20` |
| M22 | nmos | `vout` | `vdd` | `N17` |
| M3 | nmos | `vss` | `TAIL` | `NB` |
| M4 | nmos | `vss` | `NB` | `NB` |
| M5 | pmos | `N56` | `N5` | `N1` |
| M6 | pmos | `vdd` | `N56` | `N5` |
| M7 | pmos | `N78` | `N7` | `N2` |
| M8 | pmos | `vdd` | `N78` | `N7` |
| M9 | pmos | `vdd` | `N910` | `N5` |

## 수동 소자 표 (R/C 등 -- netlist 밖 `passive_elements`)

| Name | Kind | Terminals |
|---|---|---|
| CL | capacitor | `vout`, `agnd` |
| Cc | capacitor | `Y`, `agnd` |
| R1a | resistor | `N5`, `N1` |
| R1b | resistor | `N7`, `N2` |
| R1c | resistor | `N12`, `N13` |

## ⚡ Ideal source 표 (전류원/전압원 -- netlist 밖 `ideal_sources`, **구현 불가 소자**)

| Name | Kind | Terminals | Value | Implementable |
|---|---|---|---|---|
| IBias | current_source | `vdd`, `NB` | 미상 | ⚠️ False |

⚠️ 위 소자는 실제 회로에 없는 **이상적 모델링 소자**다(예: 논문의 외부 레퍼런스 전류원/전압원) -- `implementable: false`. sizing/layout 파이프라인(`sizing_recipe.py`/`stick_diagram.py`)이 이 배열을 참조할 일이 생기면 반드시 걸러내고 실제 트랜지스터로 구현하지 말 것.

총 22개 소자 + 5개 수동소자 + 1개 ideal source, 23개 net.
