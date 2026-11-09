# nmcnr_amplifier -- topology connectivity table

소스: `C:/Users/HSLEE/Documents/Todoc/fpga/wt/topo-batch/skills/analog-gmid-design/assets/library/nmcnr_amplifier.topology.json`. 이 파일은 `topology_to_markdown.py`가 topology.json에서 그대로 파생시킨 것 -- 손으로 고치지 말고 topology.json을 고친 뒤 다시 생성할 것.

## ⚠️ 자동 플래그 (사람 재확인 필요)

- **구동 소자 없는 net(gate로만 참조됨)**: VB1, VB2, VB3, VB4, VB5, Vin_n, Vin_p
  이 net을 source/drain으로 쓰는 소자가 topology.json에 없습니다 -- 외부 입력 핀이면 정상이지만, 내부에서 생성돼야 하는 신호라면 그걸 만드는 소자/감지망이 누락된 것일 수 있습니다.

## Net별 연결 표 (이 net에 물린 모든 단자)

| Net | 연결된 단자 (device.terminal) | 단자 수 |
|---|---|---|
| `NodeC` | M201.drain, M203.drain, M203.gate, M204.gate | 4 |
| `NodeCM` | Cm1.t1, Cm2.t1, Rm.t0 | 3 |
| `NodeF1` | M102.drain, M104.drain, M106.source | 3 |
| `NodeF2` | M103.drain, M105.drain, M107.source | 3 |
| `NodeM1` | M106.drain, M108.drain, M108.gate, M109.gate | 4 |
| `NodeM2` | Cm1.t0, M107.drain, M109.drain, M201.gate | 4 |
| `NodeS2` | Cm2.t0, M202.drain, M204.drain, M301.gate | 4 |
| `NodeTail` | M101.drain, M102.source, M103.source | 3 |
| `VB1` ⚠️ | M101.gate | 1 |
| `VB2` ⚠️ | M104.gate, M105.gate | 2 |
| `VB3` ⚠️ | M106.gate, M107.gate | 2 |
| `VB4` ⚠️ | M202.gate | 1 |
| `VB5` ⚠️ | M302.gate | 1 |
| `Vin_n` ⚠️ | M102.gate | 1 |
| `Vin_p` ⚠️ | M103.gate | 1 |
| `Vout` | CL.t0, M301.drain, M302.drain, RL.t0, Rm.t1 | 5 |
| `vdd` | M101.source, M108.source, M109.source, M201.source, M202.source, M302.source | 6 |
| `vss` | CL.t1, M104.source, M105.source, M203.source, M204.source, M301.source, RL.t1 | 7 |

## 소자별 연결 표 (name/kind/source/drain/gate)

| Name | Kind | Source | Drain | Gate |
|---|---|---|---|---|
| M101 | pmos | `vdd` | `NodeTail` | `VB1` |
| M102 | pmos | `NodeTail` | `NodeF1` | `Vin_n` |
| M103 | pmos | `NodeTail` | `NodeF2` | `Vin_p` |
| M104 | nmos | `vss` | `NodeF1` | `VB2` |
| M105 | nmos | `vss` | `NodeF2` | `VB2` |
| M106 | nmos | `NodeF1` | `NodeM1` | `VB3` |
| M107 | nmos | `NodeF2` | `NodeM2` | `VB3` |
| M108 | pmos | `vdd` | `NodeM1` | `NodeM1` |
| M109 | pmos | `vdd` | `NodeM2` | `NodeM1` |
| M201 | pmos | `vdd` | `NodeC` | `NodeM2` |
| M202 | pmos | `vdd` | `NodeS2` | `VB4` |
| M203 | nmos | `vss` | `NodeC` | `NodeC` |
| M204 | nmos | `vss` | `NodeS2` | `NodeC` |
| M301 | nmos | `vss` | `Vout` | `NodeS2` |
| M302 | pmos | `vdd` | `Vout` | `VB5` |

## 수동 소자 표 (R/C 등 -- netlist 밖 `passive_elements`)

| Name | Kind | Terminals |
|---|---|---|
| CL | capacitor | `Vout`, `vss` |
| Cm1 | capacitor | `NodeM2`, `NodeCM` |
| Cm2 | capacitor | `NodeS2`, `NodeCM` |
| RL | resistor | `Vout`, `vss` |
| Rm | resistor | `NodeCM`, `Vout` |

총 15개 소자 + 5개 수동소자 + 0개 ideal source, 18개 net.
