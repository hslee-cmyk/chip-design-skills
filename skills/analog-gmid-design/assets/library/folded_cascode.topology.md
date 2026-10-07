# folded_cascode -- topology connectivity table

소스: `library/folded_cascode.topology.json`. 이 파일은 `topology_to_markdown.py`가 topology.json에서 그대로 파생시킨 것 -- 손으로 고치지 말고 topology.json을 고친 뒤 다시 생성할 것.

## ⚠️ 자동 플래그 (사람 재확인 필요)

- **구동 소자 없는 net(gate로만 참조됨)**: bias3, vin_n, vin_p
  이 net을 source/drain으로 쓰는 소자가 topology.json에 없습니다 -- 외부 입력 핀이면 정상이지만, 내부에서 생성돼야 하는 신호라면 그걸 만드는 소자/감지망이 누락된 것일 수 있습니다.

## Net별 연결 표 (이 net에 물린 모든 단자)

| Net | 연결된 단자 (device.terminal) | 단자 수 |
|---|---|---|
| `Vg10` | M10.drain, M8.source | 2 |
| `Vg7` | M5.drain, M7.drain, M7.gate, M8.gate | 4 |
| `Vg9` | M10.gate, M7.source, M9.drain, M9.gate | 4 |
| `X` | M1.drain, M3.drain, M6.source | 3 |
| `Y` | M2.drain, M4.drain, M5.source | 3 |
| `bias3` ⚠️ | M5.gate, M6.gate | 2 |
| `gnd` | CL.t1, M10.source, M11.source, M9.source, MN.source | 5 |
| `out` | CL.t0, M6.drain, M8.drain | 3 |
| `tail` | M1.source, M11.drain, M2.source | 3 |
| `vb1` | Ibg.t0, M3.gate, M4.gate, MP.drain, MP.gate | 5 |
| `vb2` | Ibg.t1, M11.gate, MN.drain, MN.gate | 4 |
| `vdd` | M3.source, M4.source, MP.source | 3 |
| `vin_n` ⚠️ | M1.gate | 1 |
| `vin_p` ⚠️ | M2.gate | 1 |

## 소자별 연결 표 (name/kind/source/drain/gate)

| Name | Kind | Source | Drain | Gate |
|---|---|---|---|---|
| M1 | nmos | `tail` | `X` | `vin_n` |
| M10 | nmos | `gnd` | `Vg10` | `Vg9` |
| M11 | nmos | `gnd` | `tail` | `vb2` |
| M2 | nmos | `tail` | `Y` | `vin_p` |
| M3 | pmos | `vdd` | `X` | `vb1` |
| M4 | pmos | `vdd` | `Y` | `vb1` |
| M5 | pmos | `Y` | `Vg7` | `bias3` |
| M6 | pmos | `X` | `out` | `bias3` |
| M7 | nmos | `Vg9` | `Vg7` | `Vg7` |
| M8 | nmos | `Vg10` | `out` | `Vg7` |
| M9 | nmos | `gnd` | `Vg9` | `Vg9` |
| MN | nmos | `gnd` | `vb2` | `vb2` |
| MP | pmos | `vdd` | `vb1` | `vb1` |

## 수동 소자 표 (R/C 등 -- netlist 밖 `passive_elements`)

| Name | Kind | Terminals |
|---|---|---|
| CL | capacitor | `out`, `gnd` |

## ⚡ Ideal source 표 (전류원/전압원 -- netlist 밖 `ideal_sources`, **구현 불가 소자**)

| Name | Kind | Terminals | Value | Implementable |
|---|---|---|---|---|
| Ibg | current_source | `vb1`, `vb2` | 미상 | ⚠️ False |

⚠️ 위 소자는 실제 회로에 없는 **이상적 모델링 소자**다(예: 논문의 외부 레퍼런스 전류원/전압원) -- `implementable: false`. sizing/layout 파이프라인(`sizing_recipe.py`/`stick_diagram.py`)이 이 배열을 참조할 일이 생기면 반드시 걸러내고 실제 트랜지스터로 구현하지 말 것.

총 13개 소자 + 1개 수동소자 + 1개 ideal source, 14개 net.
