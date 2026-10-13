# erfc_ota -- topology connectivity table

소스: `assets/heldout/erfc_ota.topology.json`. 이 파일은 `topology_to_markdown.py`가 topology.json에서 그대로 파생시킨 것 -- 손으로 고치지 말고 topology.json을 고친 뒤 다시 생성할 것. (생성 방법: 이 도구의 옛 로더(legacy/stick_diagram.py)가 `symmetry` 키를 요구하고 netlist `bulk` 키를 받지 못해, 빈 `symmetry`를 넣고 `bulk`를 뺀 임시 사본으로 생성했다 -- 이 표는 bulk를 보여 주지 않으므로 내용은 같다. bulk: NMOS=gnd, PMOS=vdd(topology `_bulk_comment`, 사용자 B-3).)

## ⚠️ 자동 플래그 (사람 재확인 필요)

- **고아 net(단자 1개, source/drain 기준)**: vcp
  이 회로 안에서 이 net을 source/drain으로 쓰는 소자가 하나뿐입니다 -- 외부 포트(정상)이거나, 실제로는 다른 소자와 연결돼야 하는데 이름이 잘못 붙었을 가능성이 있습니다.
- **구동 소자 없는 net(gate로만 참조됨)**: vin_n, vin_p
  이 net을 source/drain으로 쓰는 소자가 topology.json에 없습니다 -- 외부 입력 핀이면 정상이지만, 내부에서 생성돼야 하는 신호라면 그걸 만드는 소자/감지망이 누락된 것일 수 있습니다.

## 📄 출처 매니페스트 (`source_manifest`)

- 그림/쪽: Sensors 2025 25(8) 2523, PDF p.8 Figure 6 (+CL from p.13 text / p.14 Table 2)
- 소자 29개, 수동소자 6개 (로더가 netlist·passive_elements 개수와 대조)

## Net별 연결 표 (이 net에 물린 모든 단자)

| Net | 연결된 단자 (device.terminal) | 단자 수 |
|---|---|---|
| `A` | M11.source, M13.drain, M2A.source, M2B.source | 4 |
| `B` | M12.source, M14.drain, M1A.source, M1B.source | 4 |
| `X` | CBAT1_L.t1, M17B.drain, M18A.gate, M2B.drain, M3B.gate, M3C.drain, R1.t0 | 7 |
| `Y` | CBAT1_R.t1, M17A.gate, M18B.drain, M1B.drain, M4B.gate, M4C.drain, R2.t1 | 7 |
| `Z` | M19.gate, M20.gate, M3A.gate, M4A.gate, R1.t1, R2.t0 | 6 |
| `gnd` | CL.t1, I05B_L.t1, I05B_R.t1, M15.drain, M16.drain, M17A.source, M18A.source, M3A.source, M3B.source, M4A.source, M4B.source | 11 |
| `n_m10d` | M10.drain, M8.source | 2 |
| `n_m11d` | I05B_L.t0, M11.drain, M15.gate | 3 |
| `n_m12d` | I05B_R.t0, M12.drain, M16.gate | 3 |
| `n_m13g` | IC_L.t1, M13.gate, M15.source | 3 |
| `n_m14g` | IC_R.t1, M14.gate, M16.source | 3 |
| `n_m17ad` | M17A.drain, M17B.source | 2 |
| `n_m18ad` | M18A.drain, M18B.source | 2 |
| `n_m3ad` | M3A.drain, M3C.source | 2 |
| `n_m4ad` | M4A.drain, M4C.source | 2 |
| `n_m5g` | CBAT1_L.t0, M19.drain, M5.gate | 3 |
| `n_m5s` | M1A.drain, M3B.drain, M5.source | 3 |
| `n_m6g` | CBAT1_R.t0, M20.drain, M6.gate | 3 |
| `n_m6s` | M2A.drain, M4B.drain, M6.source | 3 |
| `n_m7d` | CBAT2.t0, M10.gate, M5.drain, M7.drain, M9.gate | 5 |
| `n_m8g` | CBAT2.t1, M21.drain, M7.gate, M8.gate | 4 |
| `n_m9d` | M7.source, M9.drain | 2 |
| `out` | CL.t0, M6.drain, M8.drain | 3 |
| `vcn` | M17B.gate, M18B.gate, M19.source, M20.source, M21.gate, M3C.gate, M4C.gate | 7 |
| `vcp` ⚠️ | M21.source | 1 |
| `vdd` | IC_L.t0, IC_R.t0, M10.source, M13.source, M14.source, M9.source | 6 |
| `vin_n` ⚠️ | M12.gate, M2A.gate, M2B.gate | 3 |
| `vin_p` ⚠️ | M11.gate, M1A.gate, M1B.gate | 3 |

## 소자별 연결 표 (name/kind/source/drain/gate)

| Name | Kind | Source | Drain | Gate |
|---|---|---|---|---|
| M10 | pmos | `vdd` | `n_m10d` | `n_m7d` |
| M11 | pmos | `A` | `n_m11d` | `vin_p` |
| M12 | pmos | `B` | `n_m12d` | `vin_n` |
| M13 | pmos | `vdd` | `A` | `n_m13g` |
| M14 | pmos | `vdd` | `B` | `n_m14g` |
| M15 | pmos | `n_m13g` | `gnd` | `n_m11d` |
| M16 | pmos | `n_m14g` | `gnd` | `n_m12d` |
| M17A | nmos | `gnd` | `n_m17ad` | `Y` |
| M17B | nmos | `n_m17ad` | `X` | `vcn` |
| M18A | nmos | `gnd` | `n_m18ad` | `X` |
| M18B | nmos | `n_m18ad` | `Y` | `vcn` |
| M19 | pmos | `vcn` | `n_m5g` | `Z` |
| M1A | pmos | `B` | `n_m5s` | `vin_p` |
| M1B | pmos | `B` | `Y` | `vin_p` |
| M20 | pmos | `vcn` | `n_m6g` | `Z` |
| M21 | pmos | `vcp` | `n_m8g` | `vcn` |
| M2A | pmos | `A` | `n_m6s` | `vin_n` |
| M2B | pmos | `A` | `X` | `vin_n` |
| M3A | nmos | `gnd` | `n_m3ad` | `Z` |
| M3B | nmos | `gnd` | `n_m5s` | `X` |
| M3C | nmos | `n_m3ad` | `X` | `vcn` |
| M4A | nmos | `gnd` | `n_m4ad` | `Z` |
| M4B | nmos | `gnd` | `n_m6s` | `Y` |
| M4C | nmos | `n_m4ad` | `Y` | `vcn` |
| M5 | nmos | `n_m5s` | `n_m7d` | `n_m5g` |
| M6 | nmos | `n_m6s` | `out` | `n_m6g` |
| M7 | pmos | `n_m9d` | `n_m7d` | `n_m8g` |
| M8 | pmos | `n_m10d` | `out` | `n_m8g` |
| M9 | pmos | `vdd` | `n_m9d` | `n_m7d` |

## 수동 소자 표 (R/C 등 -- netlist 밖 `passive_elements`)

| Name | Kind | Terminals |
|---|---|---|
| CBAT1_L | capacitor | `n_m5g`, `X` |
| CBAT1_R | capacitor | `n_m6g`, `Y` |
| CBAT2 | capacitor | `n_m7d`, `n_m8g` |
| CL | capacitor | `out`, `gnd` |
| R1 | resistor | `X`, `Z` |
| R2 | resistor | `Z`, `Y` |

## ⚡ Ideal source 표 (전류원/전압원 -- netlist 밖 `ideal_sources`, **구현 불가 소자**)

| Name | Kind | Terminals | Value | Implementable |
|---|---|---|---|---|
| I05B_L | current_source | `n_m11d`, `gnd` | 1e-06 | ⚠️ False |
| I05B_R | current_source | `n_m12d`, `gnd` | 1e-06 | ⚠️ False |
| IC_L | current_source | `vdd`, `n_m13g` | 2e-07 | ⚠️ False |
| IC_R | current_source | `vdd`, `n_m14g` | 2e-07 | ⚠️ False |

⚠️ 위 소자는 실제 회로에 없는 **이상적 모델링 소자**다(예: 논문의 외부 레퍼런스 전류원/전압원) -- `implementable: false`. sizing/layout 파이프라인(`sizing_recipe.py`/`stick_diagram.py`)이 이 배열을 참조할 일이 생기면 반드시 걸러내고 실제 트랜지스터로 구현하지 말 것.

총 29개 소자 + 6개 수동소자 + 4개 ideal source, 28개 net.
