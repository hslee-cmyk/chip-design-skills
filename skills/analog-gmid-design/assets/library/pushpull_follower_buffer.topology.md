# pushpull_follower_buffer -- topology connectivity table

소스: `library/pushpull_follower_buffer.topology.json`. 이 파일은 `topology_to_markdown.py`가 topology.json에서 그대로 파생시킨 것 -- 손으로 고치지 말고 topology.json을 고친 뒤 다시 생성할 것.

## ⚠️ 자동 플래그 (사람 재확인 필요)

- **구동 소자 없는 net(gate로만 참조됨)**: VNB1, VPB1, vin
  이 net을 source/drain으로 쓰는 소자가 topology.json에 없습니다 -- 외부 입력 핀이면 정상이지만, 내부에서 생성돼야 하는 신호라면 그걸 만드는 소자/감지망이 누락된 것일 수 있습니다.

## Net별 연결 표 (이 net에 물린 모든 단자)

| Net | 연결된 단자 (device.terminal) | 단자 수 |
|---|---|---|
| `A` | M1.gate, M3.source, M5.drain | 3 |
| `B` | M2.gate, M4.source, M6.drain | 3 |
| `VNB1` ⚠️ | M6.gate | 1 |
| `VPB1` ⚠️ | M5.gate | 1 |
| `gnd` | M2.drain, M3.drain, M6.source | 3 |
| `vdd` | M1.drain, M4.drain, M5.source | 3 |
| `vin` ⚠️ | M3.gate, M4.gate | 2 |
| `vout` | M1.source, M2.source | 2 |

## 소자별 연결 표 (name/kind/source/drain/gate)

| Name | Kind | Source | Drain | Gate |
|---|---|---|---|---|
| M1 | nmos | `vout` | `vdd` | `A` |
| M2 | pmos | `vout` | `gnd` | `B` |
| M3 | pmos | `A` | `gnd` | `vin` |
| M4 | nmos | `B` | `vdd` | `vin` |
| M5 | pmos | `vdd` | `A` | `VPB1` |
| M6 | nmos | `gnd` | `B` | `VNB1` |

총 6개 소자 + 0개 수동소자 + 0개 ideal source, 8개 net.
