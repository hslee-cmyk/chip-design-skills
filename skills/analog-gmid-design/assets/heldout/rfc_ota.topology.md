# rfc_ota -- topology connectivity table

소스: `assets/heldout/rfc_ota.topology.json`. 이 파일은 `topology_to_markdown.py`가 topology.json에서 그대로 파생시킨 것 -- 손으로 고치지 말고 topology.json을 고친 뒤 다시 생성할 것. (생성 방법: 이 도구의 옛 로더(legacy/stick_diagram.py)가 `symmetry.matching_pairs` 키를 요구해, 빈 `symmetry`(`{"matching_pairs": []}`)를 넣은 임시 사본으로 생성했다 -- 사람 태그를 정본에 넣지 않기 위해서다. 연결 내용은 정본과 같고, 판독본 wt/_heldout/A_rfc/A_rfc.topology.md 와 본문이 같다.)

## ⚠️ 자동 플래그 (사람 재확인 필요)

- **구동 소자 없는 net(gate로만 참조됨)**: vin_n, vin_p
  이 net을 source/drain으로 쓰는 소자가 topology.json에 없습니다 -- 외부 입력 핀이면 정상이지만, 내부에서 생성돼야 하는 신호라면 그걸 만드는 소자/감지망이 누락된 것일 수 있습니다.

## 📄 출처 매니페스트 (`source_manifest`)

- 그림/쪽: UPC RFC 2024 p.28 Fig.6(코어 17 MOS) + p.34 Fig.9(바이어스 18 MOS + RB) + p.37 Fig.11(CL)
- 소자 35개, 수동소자 2개 (로더가 netlist·passive_elements 개수와 대조)

## Net별 연결 표 (이 net에 물린 모든 단자)

| Net | 연결된 단자 (device.terminal) | 단자 수 |
|---|---|---|
| `G3` | M11.drain, M2b.drain, M3a.gate, M3b.gate | 4 |
| `G4` | M12.drain, M1b.drain, M4a.gate, M4b.gate | 4 |
| `G9` | M10.gate, M5.drain, M7.drain, M9.gate | 4 |
| `S11` | M11.source, M3b.drain | 2 |
| `S12` | M12.source, M4b.drain | 2 |
| `S7` | M7.source, M9.drain | 2 |
| `S8` | M10.drain, M8.source | 2 |
| `VBN1` | Q12.gate, Q2.gate, Q3.gate, Q4.drain, Q6.drain | 5 |
| `VBN2` | M11.gate, M12.gate, M5.gate, M6.gate, Q1.gate, Q10.drain, Q13.gate, Q17.gate, Q4.gate, Q5.drain, Q5.gate | 11 |
| `VBP1` | M0.gate, Q1.drain, Q11.gate, Q15.drain, Q7.gate, Q8.drain, Q9.gate | 7 |
| `VBP2` | M7.gate, M8.gate, Q10.gate, Q13.drain, Q14.drain, Q14.gate, Q16.drain, Q6.gate, Q8.gate | 9 |
| `X` | M1a.drain, M3a.drain, M5.source | 3 |
| `Y` | M2a.drain, M4a.drain, M6.source | 3 |
| `b_q11d` | Q10.source, Q11.drain | 2 |
| `b_q13s` | Q12.drain, Q13.source | 2 |
| `b_q1s` | Q1.source, Q2.drain | 2 |
| `b_q4s` | Q3.drain, Q4.source | 2 |
| `b_q7d` | Q6.source, Q7.drain | 2 |
| `b_q9d` | Q8.source, Q9.drain | 2 |
| `b_rb` | Q2.source, RB.t0 | 2 |
| `b_su` | Q15.gate, Q16.gate, Q17.drain, Q18.drain | 4 |
| `gnd` | CL.t1, M3a.source, M3b.source, M4a.source, M4b.source, Q12.source, Q15.source, Q16.source, Q17.source, Q18.gate, Q3.source, Q5.source, RB.t1 | 13 |
| `out` | CL.t0, M6.drain, M8.drain | 3 |
| `tail` | M0.drain, M1a.source, M1b.source, M2a.source, M2b.source | 5 |
| `vdd` | M0.source, M10.source, M9.source, Q11.source, Q14.source, Q18.source, Q7.source, Q9.source | 8 |
| `vin_n` ⚠️ | M2a.gate, M2b.gate | 2 |
| `vin_p` ⚠️ | M1a.gate, M1b.gate | 2 |

## 소자별 연결 표 (name/kind/source/drain/gate)

| Name | Kind | Source | Drain | Gate |
|---|---|---|---|---|
| M0 | pmos | `vdd` | `tail` | `VBP1` |
| M10 | pmos | `vdd` | `S8` | `G9` |
| M11 | nmos | `S11` | `G3` | `VBN2` |
| M12 | nmos | `S12` | `G4` | `VBN2` |
| M1a | pmos | `tail` | `X` | `vin_p` |
| M1b | pmos | `tail` | `G4` | `vin_p` |
| M2a | pmos | `tail` | `Y` | `vin_n` |
| M2b | pmos | `tail` | `G3` | `vin_n` |
| M3a | nmos | `gnd` | `X` | `G3` |
| M3b | nmos | `gnd` | `S11` | `G3` |
| M4a | nmos | `gnd` | `Y` | `G4` |
| M4b | nmos | `gnd` | `S12` | `G4` |
| M5 | nmos | `X` | `G9` | `VBN2` |
| M6 | nmos | `Y` | `out` | `VBN2` |
| M7 | pmos | `S7` | `G9` | `VBP2` |
| M8 | pmos | `S8` | `out` | `VBP2` |
| M9 | pmos | `vdd` | `S7` | `G9` |
| Q1 | nmos | `b_q1s` | `VBP1` | `VBN2` |
| Q10 | pmos | `b_q11d` | `VBN2` | `VBP2` |
| Q11 | pmos | `vdd` | `b_q11d` | `VBP1` |
| Q12 | nmos | `gnd` | `b_q13s` | `VBN1` |
| Q13 | nmos | `b_q13s` | `VBP2` | `VBN2` |
| Q14 | pmos | `vdd` | `VBP2` | `VBP2` |
| Q15 | nmos | `gnd` | `VBP1` | `b_su` |
| Q16 | nmos | `gnd` | `VBP2` | `b_su` |
| Q17 | nmos | `gnd` | `b_su` | `VBN2` |
| Q18 | pmos | `vdd` | `b_su` | `gnd` |
| Q2 | nmos | `b_rb` | `b_q1s` | `VBN1` |
| Q3 | nmos | `gnd` | `b_q4s` | `VBN1` |
| Q4 | nmos | `b_q4s` | `VBN1` | `VBN2` |
| Q5 | nmos | `gnd` | `VBN2` | `VBN2` |
| Q6 | pmos | `b_q7d` | `VBN1` | `VBP2` |
| Q7 | pmos | `vdd` | `b_q7d` | `VBP1` |
| Q8 | pmos | `b_q9d` | `VBP1` | `VBP2` |
| Q9 | pmos | `vdd` | `b_q9d` | `VBP1` |

## 수동 소자 표 (R/C 등 -- netlist 밖 `passive_elements`)

| Name | Kind | Terminals |
|---|---|---|
| CL | capacitor | `out`, `gnd` |
| RB | resistor | `b_rb`, `gnd` |

총 35개 소자 + 2개 수동소자 + 0개 ideal source, 27개 net.
