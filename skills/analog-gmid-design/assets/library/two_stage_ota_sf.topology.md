# two_stage_ota_sf -- topology connectivity table

소스: `library/two_stage_ota_sf.topology.json`. 이 파일은 `topology_to_markdown.py`가 topology.json에서 그대로 파생시킨 것 -- 손으로 고치지 말고 topology.json을 고친 뒤 다시 생성할 것.

## ⚠️ 자동 플래그 (사람 재확인 필요)

- **구동 소자 없는 net(gate로만 참조됨)**: bias, vin_n, vin_p
  이 net을 source/drain으로 쓰는 소자가 topology.json에 없습니다 -- 외부 입력 핀이면 정상이지만, 내부에서 생성돼야 하는 신호라면 그걸 만드는 소자/감지망이 누락된 것일 수 있습니다.

## Net별 연결 표 (이 net에 물린 모든 단자)

| Net | 연결된 단자 (device.terminal) | 단자 수 |
|---|---|---|
| `CS` | M1.source, M2.source, M5.drain | 3 |
| `D3` | M1.drain, M3.drain, M3.gate, M4.gate | 4 |
| `O1` | Cc.t0, M2.drain, M4.drain, M6.gate | 4 |
| `OUT` | Cc.t1, M6.drain, M7.drain, M8.gate | 4 |
| `bias` ⚠️ | M5.gate, M7.gate, M9.gate | 3 |
| `gnd` | CL.t1, M5.source, M7.source, M9.source | 4 |
| `vdd` | M3.source, M4.source, M6.source, M8.drain | 4 |
| `vin_n` ⚠️ | M1.gate | 1 |
| `vin_p` ⚠️ | M2.gate | 1 |
| `vout` | CL.t0, M8.source, M9.drain | 3 |

## 소자별 연결 표 (name/kind/source/drain/gate)

| Name | Kind | Source | Drain | Gate |
|---|---|---|---|---|
| M1 | nmos | `CS` | `D3` | `vin_n` |
| M2 | nmos | `CS` | `O1` | `vin_p` |
| M3 | pmos | `vdd` | `D3` | `D3` |
| M4 | pmos | `vdd` | `O1` | `D3` |
| M5 | nmos | `gnd` | `CS` | `bias` |
| M6 | pmos | `vdd` | `OUT` | `O1` |
| M7 | nmos | `gnd` | `OUT` | `bias` |
| M8 | nmos | `vout` | `vdd` | `OUT` |
| M9 | nmos | `gnd` | `vout` | `bias` |

## 수동 소자 표 (R/C 등 -- netlist 밖 `passive_elements`)

| Name | Kind | Terminals |
|---|---|---|
| CL | capacitor | `vout`, `gnd` |
| Cc | capacitor | `O1`, `OUT` |

총 9개 소자 + 2개 수동소자 + 0개 ideal source, 10개 net.
