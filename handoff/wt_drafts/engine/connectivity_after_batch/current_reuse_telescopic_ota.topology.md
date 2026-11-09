# current_reuse_telescopic_ota -- topology connectivity table

소스: `C:/Users/HSLEE/Documents/Todoc/fpga/wt/topo-batch/skills/analog-gmid-design/assets/library/current_reuse_telescopic_ota.topology.json`. 이 파일은 `topology_to_markdown.py`가 topology.json에서 그대로 파생시킨 것 -- 손으로 고치지 말고 topology.json을 고친 뒤 다시 생성할 것.

## ⚠️ 자동 플래그: 없음 (구조적으로는 이상 없음 -- §8 정직한 한계 참고)

## ℹ️ 해소된 플래그 (근거 있음 -- `_known_dangling_nets` 참고)

- **`Vim`**: opamp의 differential input 신호(음극) -- 칩 외부에서 인가되는 핀이라 topology.json 안에 이걸 구동하는 소자가 없는 게 정상(2026-08-03 사용자 확인, 아래 ports 참고).
- **`Vip`**: opamp의 differential input 신호(양극) -- Vim과 동일 사유, 외부 인가 핀.
- **`Voc`**: R1/R2로 최종 출력 Vom/Vop를 평균해 구동됨(위 passive_elements 참고) -- topology_to_markdown.py의 '구동 소자 없는 net' 플래그는 netlist(트랜지스터)만 보므로 여전히 뜬다, 하지만 passive_elements를 포함하면 실제로는 고아가 아니다.

## Net별 연결 표 (이 net에 물린 모든 단자)

| Net | 연결된 단자 (device.terminal) | 단자 수 |
|---|---|---|
| `N11a11b` | M11a.drain, M11a.gate, M11b.source | 3 |
| `N11b` | M11b.drain, M11b.gate, M12.drain, M9a.gate | 4 |
| `N14a14b` | M13.drain, M14a.drain, M14a.gate, M9b.gate | 4 |
| `N14a_14b` | M14a.source, M14b.drain, M14b.gate | 3 |
| `N1a2a` | M1a.drain, M2a.source | 2 |
| `N1b2b` | M1b.drain, M2b.source | 2 |
| `N20a20b` | M20a.drain, M20a.gate, M20b.source | 3 |
| `N20b` | M18a.gate, M20b.drain, M20b.gate, M21.drain | 4 |
| `N23a24b` | M23a.source, M24b.drain, M24b.gate | 3 |
| `N24b23a` | M18b.gate, M22.drain, M23a.drain, M23a.gate | 4 |
| `N36b` | M36b.drain, M36b.gate, M37b.drain | 3 |
| `N3a4a` | M3a.source, M4a.drain | 2 |
| `N3b4b` | M3b.source, M4b.drain | 2 |
| `N58_57` | M57.source, M58.drain | 2 |
| `N64_63` | M63.drain, M64.source | 2 |
| `N_cc_rz1` | Cc1.t1, Rz1.t0 | 2 |
| `N_cc_rz2` | Cc2.t1, Rz2.t0 | 2 |
| `Ncmfb_tail` | M37a.source, M37b.source, M38.drain | 3 |
| `Vbias1` | Iref.t0, M13.gate, M17.gate, M18_bg.drain, M18_bg.gate, M22.gate, M6.gate, M60.gate, M61.gate, M8.gate | 10 |
| `Vbias2` | M2a.gate, M2b.gate, M57.drain, M57.gate, M58.gate, M68.drain | 6 |
| `Vbias3` | M3a.gate, M3b.gate, M61.drain, M63.gate, M64.drain, M64.gate | 6 |
| `Vbias4` | M10.gate, M12.gate, M19.gate, M21.gate, M38.gate, M5.gate, M60.drain, M66.drain, M66.gate, M68.gate | 10 |
| `Vcmfb` | M36a.drain, M36a.gate, M37a.drain, M7.gate | 4 |
| `Vg15` | M15.gate, M8.drain, M9a.source, M9b.drain | 4 |
| `Vg25` | M17.drain, M18a.source, M18b.drain, M25.gate | 4 |
| `Vim` ℹ️ | Cf2.t1, Cs2.t0, M1b.gate, M4b.gate | 4 |
| `Vip` ℹ️ | Cf1.t1, Cs1.t0, M1a.gate, M4a.gate | 4 |
| `Voc` ℹ️ | M37a.gate, R1.t1, R2.t0 | 3 |
| `Voc_des` | M37b.gate, M39.drain, M39.gate, M40.source | 4 |
| `Vom` | CL2.t0, Cc1.t0, Cf1.t0, M15.drain, M16.drain, R1.t0 | 6 |
| `Vom1` | M18a.drain, M18b.source, M19.drain, M26.gate, M2a.drain, M3a.drain, Rz2.t1 | 7 |
| `Vop` | CL1.t0, Cc2.t0, Cf2.t0, M25.drain, M26.drain, R2.t1 | 6 |
| `Vop1` | M10.drain, M16.gate, M2b.drain, M3b.drain, M9a.drain, M9b.source, Rz1.t1 | 7 |
| `Vx` | M1a.source, M1b.source, M58.source, M6.drain, M7.drain | 5 |
| `Vy` | M4a.source, M4b.source, M5.drain, M63.source | 4 |
| `gnd` | CL1.t1, CL2.t1, Cs1.t1, Cs2.t1, Iref.t1, M10.source, M12.source, M14b.source, M16.source, M19.source, M21.source, M24b.source, M26.source, M38.source, M40.drain, M40.gate, M5.source, M66.source, M68.source | 19 |
| `vdd` | M11a.source, M13.source, M15.source, M17.source, M18_bg.source, M20a.source, M22.source, M25.source, M36a.source, M36b.source, M39.source, M6.source, M60.source, M61.source, M7.source, M8.source | 16 |

## 소자별 연결 표 (name/kind/source/drain/gate)

| Name | Kind | Source | Drain | Gate |
|---|---|---|---|---|
| M10 | nmos | `gnd` | `Vop1` | `Vbias4` |
| M11a | pmos | `vdd` | `N11a11b` | `N11a11b` |
| M11b | pmos | `N11a11b` | `N11b` | `N11b` |
| M12 | nmos | `gnd` | `N11b` | `Vbias4` |
| M13 | pmos | `vdd` | `N14a14b` | `Vbias1` |
| M14a | nmos | `N14a_14b` | `N14a14b` | `N14a14b` |
| M14b | nmos | `gnd` | `N14a_14b` | `N14a_14b` |
| M15 | pmos | `vdd` | `Vom` | `Vg15` |
| M16 | nmos | `gnd` | `Vom` | `Vop1` |
| M17 | pmos | `vdd` | `Vg25` | `Vbias1` |
| M18_bg | pmos | `vdd` | `Vbias1` | `Vbias1` |
| M18a | pmos | `Vg25` | `Vom1` | `N20b` |
| M18b | nmos | `Vom1` | `Vg25` | `N24b23a` |
| M19 | nmos | `gnd` | `Vom1` | `Vbias4` |
| M1a | pmos | `Vx` | `N1a2a` | `Vip` |
| M1b | pmos | `Vx` | `N1b2b` | `Vim` |
| M20a | pmos | `vdd` | `N20a20b` | `N20a20b` |
| M20b | pmos | `N20a20b` | `N20b` | `N20b` |
| M21 | nmos | `gnd` | `N20b` | `Vbias4` |
| M22 | pmos | `vdd` | `N24b23a` | `Vbias1` |
| M23a | nmos | `N23a24b` | `N24b23a` | `N24b23a` |
| M24b | nmos | `gnd` | `N23a24b` | `N23a24b` |
| M25 | pmos | `vdd` | `Vop` | `Vg25` |
| M26 | nmos | `gnd` | `Vop` | `Vom1` |
| M2a | pmos | `N1a2a` | `Vom1` | `Vbias2` |
| M2b | pmos | `N1b2b` | `Vop1` | `Vbias2` |
| M36a | pmos | `vdd` | `Vcmfb` | `Vcmfb` |
| M36b | pmos | `vdd` | `N36b` | `N36b` |
| M37a | nmos | `Ncmfb_tail` | `Vcmfb` | `Voc` |
| M37b | nmos | `Ncmfb_tail` | `N36b` | `Voc_des` |
| M38 | nmos | `gnd` | `Ncmfb_tail` | `Vbias4` |
| M39 | pmos | `vdd` | `Voc_des` | `Voc_des` |
| M3a | nmos | `N3a4a` | `Vom1` | `Vbias3` |
| M3b | nmos | `N3b4b` | `Vop1` | `Vbias3` |
| M40 | pmos | `Voc_des` | `gnd` | `gnd` |
| M4a | nmos | `Vy` | `N3a4a` | `Vip` |
| M4b | nmos | `Vy` | `N3b4b` | `Vim` |
| M5 | nmos | `gnd` | `Vy` | `Vbias4` |
| M57 | pmos | `N58_57` | `Vbias2` | `Vbias2` |
| M58 | pmos | `Vx` | `N58_57` | `Vbias2` |
| M6 | pmos | `vdd` | `Vx` | `Vbias1` |
| M60 | pmos | `vdd` | `Vbias4` | `Vbias1` |
| M61 | pmos | `vdd` | `Vbias3` | `Vbias1` |
| M63 | nmos | `Vy` | `N64_63` | `Vbias3` |
| M64 | nmos | `N64_63` | `Vbias3` | `Vbias3` |
| M66 | nmos | `gnd` | `Vbias4` | `Vbias4` |
| M68 | nmos | `gnd` | `Vbias2` | `Vbias4` |
| M7 | pmos | `vdd` | `Vx` | `Vcmfb` |
| M8 | pmos | `vdd` | `Vg15` | `Vbias1` |
| M9a | pmos | `Vg15` | `Vop1` | `N11b` |
| M9b | nmos | `Vop1` | `Vg15` | `N14a14b` |

## 수동 소자 표 (R/C 등 -- netlist 밖 `passive_elements`)

| Name | Kind | Terminals |
|---|---|---|
| CL1 | capacitor | `Vop`, `gnd` |
| CL2 | capacitor | `Vom`, `gnd` |
| Cc1 | capacitor | `Vom`, `N_cc_rz1` |
| Cc2 | capacitor | `Vop`, `N_cc_rz2` |
| Cf1 | capacitor | `Vom`, `Vip` |
| Cf2 | capacitor | `Vop`, `Vim` |
| Cs1 | capacitor | `Vip`, `gnd` |
| Cs2 | capacitor | `Vim`, `gnd` |
| R1 | resistor | `Vom`, `Voc` |
| R2 | resistor | `Voc`, `Vop` |
| Rz1 | resistor | `N_cc_rz1`, `Vop1` |
| Rz2 | resistor | `N_cc_rz2`, `Vom1` |

## ⚡ Ideal source 표 (전류원/전압원 -- netlist 밖 `ideal_sources`, **구현 불가 소자**)

| Name | Kind | Terminals | Value | Implementable |
|---|---|---|---|---|
| Iref | current_source | `Vbias1`, `gnd` | 1.2e-06 | ⚠️ False |

⚠️ 위 소자는 실제 회로에 없는 **이상적 모델링 소자**다(예: 논문의 외부 레퍼런스 전류원/전압원) -- `implementable: false`. sizing/layout 파이프라인(`sizing_recipe.py`/`stick_diagram.py`)이 이 배열을 참조할 일이 생기면 반드시 걸러내고 실제 트랜지스터로 구현하지 말 것.

총 51개 소자 + 12개 수동소자 + 1개 ideal source, 37개 net.
