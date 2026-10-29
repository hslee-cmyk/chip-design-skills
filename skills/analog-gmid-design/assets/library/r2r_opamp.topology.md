# r2r_opamp -- topology connectivity table

소스: `assets/library/r2r_opamp.topology.json`. 이 파일은 `topology_to_markdown.py`가 topology.json에서 그대로 파생시킨 것 -- 손으로 고치지 말고 topology.json을 고친 뒤 다시 생성할 것. (생성 방법: 이 도구의 옛 로더(legacy/stick_diagram.py)가 `symmetry.matching_pairs` 키를 요구해, 빈 `symmetry`({matching_pairs: []})를 넣은 임시 사본으로 생성했다 -- connectivity 동일.)

## ⚠️ 자동 플래그 (사람 재확인 필요)

- **구동 소자 없는 net(gate로만 참조됨)**: Vinn, Vinp
  이 net을 source/drain으로 쓰는 소자가 topology.json에 없습니다 -- 외부 입력 핀이면 정상이지만, 내부에서 생성돼야 하는 신호라면 그걸 만드는 소자/감지망이 누락된 것일 수 있습니다.

## 📄 출처 매니페스트 (`source_manifest`)

- 그림/쪽: tudelft_0fc1.pdf p.6 (JSSC p.1510) Fig.13 (+CL·RL from p.8 (JSSC p.1512) Table I 머리)
- 소자 31개, 수동소자 4개 (로더가 netlist·passive_elements 개수와 대조)

## 🔌 외부 바이어스 입력 (`bias_inputs` -- gate 전용 선언 net, connectivity 불변)

`vb1`, `vb3`, `vb4`, `vb5n`, `vb6n`

## Net별 연결 표 (이 net에 물린 모든 단자)

| Net | 연결된 단자 (device.terminal) | 단자 수 |
|---|---|---|
| `VDD` | Ib1.t0, Ib2.t0, M11.source, M12.source, M21.source, M25.source, M29.drain, M31.source, M6.source, M7.source | 10 |
| `VSS` | CL.t1, Ib4.t1, Ib5.t1, Ib6.t1, M10.source, M17.source, M18.source, M24.source, M26.source, M9.source, RL.t1 | 11 |
| `Vinn` ⚠️ | M1.gate, M3.gate | 2 |
| `Vinp` ⚠️ | M2.gate, M4.gate | 2 |
| `Vo` | CL.t0, CM1.t1, CM2.t1, M25.drain, M26.drain, RL.t0 | 6 |
| `n_abn` | Ib2.t1, M19.gate, M23.drain, M23.gate, M27.gate | 5 |
| `n_abp` | Ib5.t0, M20.gate, M22.drain, M22.gate, M28.gate | 5 |
| `n_fn1` | M1.drain, M15.source, M17.drain | 3 |
| `n_fn2` | M16.source, M18.drain, M2.drain | 3 |
| `n_fp1` | M11.drain, M13.source, M3.drain | 3 |
| `n_fp2` | M12.drain, M14.source, M4.drain | 3 |
| `n_gn` | CM2.t0, M16.drain, M19.source, M20.drain, M26.gate | 5 |
| `n_gp` | CM1.t0, M14.drain, M19.drain, M20.source, M25.gate | 5 |
| `n_m21` | M21.drain, M21.gate, M22.source | 3 |
| `n_m24` | M23.source, M24.drain, M24.gate | 3 |
| `n_m31` | M30.drain, M31.drain, M31.gate, M8.gate | 4 |
| `n_m6` | M5.drain, M6.drain, M6.gate, M7.gate | 4 |
| `n_m9` | M10.gate, M8.drain, M9.drain, M9.gate | 4 |
| `n_mn` | M15.drain, M17.gate, M18.gate, M27.source, M28.drain | 5 |
| `n_mp` | M11.gate, M12.gate, M13.drain, M27.drain, M28.source | 5 |
| `n_t29` | Ib6.t0, M29.source, M30.source | 3 |
| `tail_n` | Ib4.t0, M10.drain, M3.source, M4.source, M5.source | 5 |
| `tail_p` | Ib1.t1, M1.source, M2.source, M7.drain, M8.source | 5 |
| `vb1` ℹ️ | M13.gate, M14.gate | 2 |
| `vb3` ℹ️ | M5.gate | 1 |
| `vb4` ℹ️ | M15.gate, M16.gate | 2 |
| `vb5n` ℹ️ | M30.gate | 1 |
| `vb6n` ℹ️ | M29.gate | 1 |

## 소자별 연결 표 (name/kind/source/drain/gate)

| Name | Kind | Source | Drain | Gate |
|---|---|---|---|---|
| M1 | pmos | `tail_p` | `n_fn1` | `Vinn` |
| M10 | nmos | `VSS` | `tail_n` | `n_m9` |
| M11 | pmos | `VDD` | `n_fp1` | `n_mp` |
| M12 | pmos | `VDD` | `n_fp2` | `n_mp` |
| M13 | pmos | `n_fp1` | `n_mp` | `vb1` |
| M14 | pmos | `n_fp2` | `n_gp` | `vb1` |
| M15 | nmos | `n_fn1` | `n_mn` | `vb4` |
| M16 | nmos | `n_fn2` | `n_gn` | `vb4` |
| M17 | nmos | `VSS` | `n_fn1` | `n_mn` |
| M18 | nmos | `VSS` | `n_fn2` | `n_mn` |
| M19 | nmos | `n_gn` | `n_gp` | `n_abn` |
| M2 | pmos | `tail_p` | `n_fn2` | `Vinp` |
| M20 | pmos | `n_gp` | `n_gn` | `n_abp` |
| M21 | pmos | `VDD` | `n_m21` | `n_m21` |
| M22 | pmos | `n_m21` | `n_abp` | `n_abp` |
| M23 | nmos | `n_m24` | `n_abn` | `n_abn` |
| M24 | nmos | `VSS` | `n_m24` | `n_m24` |
| M25 | pmos | `VDD` | `Vo` | `n_gp` |
| M26 | nmos | `VSS` | `Vo` | `n_gn` |
| M27 | nmos | `n_mn` | `n_mp` | `n_abn` |
| M28 | pmos | `n_mp` | `n_mn` | `n_abp` |
| M29 | nmos | `n_t29` | `VDD` | `vb6n` |
| M3 | nmos | `tail_n` | `n_fp1` | `Vinn` |
| M30 | nmos | `n_t29` | `n_m31` | `vb5n` |
| M31 | pmos | `VDD` | `n_m31` | `n_m31` |
| M4 | nmos | `tail_n` | `n_fp2` | `Vinp` |
| M5 | nmos | `tail_n` | `n_m6` | `vb3` |
| M6 | pmos | `VDD` | `n_m6` | `n_m6` |
| M7 | pmos | `VDD` | `tail_p` | `n_m6` |
| M8 | pmos | `tail_p` | `n_m9` | `n_m31` |
| M9 | nmos | `VSS` | `n_m9` | `n_m9` |

## 수동 소자 표 (R/C 등 -- netlist 밖 `passive_elements`)

| Name | Kind | Terminals |
|---|---|---|
| CL | capacitor | `Vo`, `VSS` |
| CM1 | capacitor | `n_gp`, `Vo` |
| CM2 | capacitor | `n_gn`, `Vo` |
| RL | resistor | `Vo`, `VSS` |

## ⚡ Ideal source 표 (전류원/전압원 -- netlist 밖 `ideal_sources`, **구현 불가 소자**)

| Name | Kind | Terminals | Value | Implementable |
|---|---|---|---|---|
| Ib1 | current_source | `VDD`, `tail_p` | 4e-06 | ⚠️ False |
| Ib2 | current_source | `VDD`, `n_abn` | 7e-06 | ⚠️ False |
| Ib4 | current_source | `tail_n`, `VSS` | 4e-06 | ⚠️ False |
| Ib5 | current_source | `n_abp`, `VSS` | 7e-06 | ⚠️ False |
| Ib6 | current_source | `n_t29`, `VSS` | 2e-06 | ⚠️ False |

⚠️ 위 소자는 실제 회로에 없는 **이상적 모델링 소자**다(예: 논문의 외부 레퍼런스 전류원/전압원) -- `implementable: false`. sizing/layout 파이프라인(`sizing_recipe.py`/`stick_diagram.py`)이 이 배열을 참조할 일이 생기면 반드시 걸러내고 실제 트랜지스터로 구현하지 말 것.

총 31개 소자 + 4개 수동소자 + 5개 ideal source, 28개 net.
