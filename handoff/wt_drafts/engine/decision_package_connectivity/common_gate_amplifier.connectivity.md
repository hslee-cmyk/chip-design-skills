# common_gate_amplifier -- topology connectivity table

소스: `C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills/skills/analog-gmid-design/assets/library\common_gate_amplifier.topology.json`. 이 파일은 `topology_to_markdown.py`가 topology.json에서 그대로 파생시킨 것 -- 손으로 고치지 말고 topology.json을 고친 뒤 다시 생성할 것.

## ⚠️ 자동 플래그 (사람 재확인 필요)

- **고아 net(단자 1개, source/drain 기준)**: gnd, vdd
  이 회로 안에서 이 net을 source/drain으로 쓰는 소자가 하나뿐입니다 -- 외부 포트(정상)이거나, 실제로는 다른 소자와 연결돼야 하는데 이름이 잘못 붙었을 가능성이 있습니다.
- **구동 소자 없는 net(gate로만 참조됨)**: VNBias1, VNBias2, VPBias1
  이 net을 source/drain으로 쓰는 소자가 topology.json에 없습니다 -- 외부 입력 핀이면 정상이지만, 내부에서 생성돼야 하는 신호라면 그걸 만드는 소자/감지망이 누락된 것일 수 있습니다.

## Net별 연결 표 (이 net에 물린 모든 단자)

| Net | 연결된 단자 (device.terminal) | 단자 수 |
|---|---|---|
| `VNBias1` ⚠️ | M1.gate | 1 |
| `VNBias2` ⚠️ | M2.gate | 1 |
| `VPBias1` ⚠️ | M3.gate | 1 |
| `gnd` ⚠️ | M1.source | 1 |
| `vdd` ⚠️ | M3.source | 1 |
| `vin` | M1.drain, M2.source | 2 |
| `vout` | M2.drain, M3.drain | 2 |

## 소자별 연결 표 (name/kind/source/drain/gate)

| Name | Kind | Source | Drain | Gate |
|---|---|---|---|---|
| M1 | nmos | `gnd` | `vin` | `VNBias1` |
| M2 | nmos | `vin` | `vout` | `VNBias2` |
| M3 | pmos | `vdd` | `vout` | `VPBias1` |

총 3개 소자 + 0개 수동소자 + 0개 ideal source, 7개 net.
