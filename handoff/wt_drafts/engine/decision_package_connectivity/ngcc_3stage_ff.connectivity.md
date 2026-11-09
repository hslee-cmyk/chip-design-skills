# ngcc_3stage_ff -- topology connectivity table

소스: `C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills/skills/analog-gmid-design/assets/library\ngcc_3stage_ff.topology.json`. 이 파일은 `topology_to_markdown.py`가 topology.json에서 그대로 파생시킨 것 -- 손으로 고치지 말고 topology.json을 고친 뒤 다시 생성할 것.

## ⚠️ 자동 플래그 (사람 재확인 필요)

- **구동 소자 없는 net(gate로만 참조됨)**: VBN, VBP, Vinn, Vinp
  이 net을 source/drain으로 쓰는 소자가 topology.json에 없습니다 -- 외부 입력 핀이면 정상이지만, 내부에서 생성돼야 하는 신호라면 그걸 만드는 소자/감지망이 누락된 것일 수 있습니다.

## Net별 연결 표 (이 net에 물린 모든 단자)

| Net | 연결된 단자 (device.terminal) | 단자 수 |
|---|---|---|
| `ND` | M1.drain, M3.drain, M3.gate, M4.gate, M6B.gate | 5 |
| `NP` | M10.gate, M8.drain, M9.drain, M9.gate | 4 |
| `NX` | M5.drain, M6A.drain, M6A.gate, M6B.drain, M7.gate | 5 |
| `TAIL` | M0.drain, M1.source, M2.source | 3 |
| `V1` | Cm1.t0, M14.gate, M2.drain, M4.drain, M8.gate | 5 |
| `V2` | Cm2.t0, M10.drain, M11.drain, M13.gate | 4 |
| `VBN` ⚠️ | M11.gate | 1 |
| `VBP` ⚠️ | M0.gate, M12.gate, M5.gate | 3 |
| `Vinn` ⚠️ | M1.gate | 1 |
| `Vinp` ⚠️ | M2.gate | 1 |
| `Vout` | CL.t0, Cm1.t1, Cm2.t1, M12.drain, M13.drain, M14.drain, M7.drain | 7 |
| `gnd` | CL.t1, M11.source, M13.source, M14.source, M3.source, M4.source, M6A.source, M6B.source, M7.source, M8.source | 10 |
| `vdd` | M0.source, M10.source, M12.source, M5.source, M9.source | 5 |

## 소자별 연결 표 (name/kind/source/drain/gate)

| Name | Kind | Source | Drain | Gate |
|---|---|---|---|---|
| M0 | pmos | `vdd` | `TAIL` | `VBP` |
| M1 | pmos | `TAIL` | `ND` | `Vinn` |
| M10 | pmos | `vdd` | `V2` | `NP` |
| M11 | nmos | `gnd` | `V2` | `VBN` |
| M12 | pmos | `vdd` | `Vout` | `VBP` |
| M13 | nmos | `gnd` | `Vout` | `V2` |
| M14 | nmos | `gnd` | `Vout` | `V1` |
| M2 | pmos | `TAIL` | `V1` | `Vinp` |
| M3 | nmos | `gnd` | `ND` | `ND` |
| M4 | nmos | `gnd` | `V1` | `ND` |
| M5 | pmos | `vdd` | `NX` | `VBP` |
| M6A | nmos | `gnd` | `NX` | `NX` |
| M6B | nmos | `gnd` | `NX` | `ND` |
| M7 | nmos | `gnd` | `Vout` | `NX` |
| M8 | nmos | `gnd` | `NP` | `V1` |
| M9 | pmos | `vdd` | `NP` | `NP` |

## 수동 소자 표 (R/C 등 -- netlist 밖 `passive_elements`)

| Name | Kind | Terminals |
|---|---|---|
| CL | capacitor | `Vout`, `gnd` |
| Cm1 | capacitor | `V1`, `Vout` |
| Cm2 | capacitor | `V2`, `Vout` |

총 16개 소자 + 3개 수동소자 + 0개 ideal source, 13개 net.
