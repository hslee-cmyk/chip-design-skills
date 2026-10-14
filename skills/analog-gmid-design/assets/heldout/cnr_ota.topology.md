# cnr_ota -- topology connectivity table

소스: `assets/heldout/cnr_ota.topology.json`. 이 파일은 `topology_to_markdown.py`가 topology.json에서 그대로 파생시킨 것 -- 손으로 고치지 말고 topology.json을 고친 뒤 다시 생성할 것. (생성 방법: 이 도구의 옛 로더(legacy/stick_diagram.py)가 netlist 의 `bulk` 키를 받지 못하고 `symmetry.matching_pairs` 키를 요구해, bulk 를 `_bulk` 주석 키로 옮기고 빈 `symmetry`(`{"matching_pairs": []}`)를 넣은 임시 사본으로 생성했다 -- 사람 태그를 정본에 넣지 않기 위해서다. 연결 내용은 정본과 같고(bulk 연결은 이 표에 없다 -- wt/_heldout/D_cnr/VERIFY.md 2절 소자 표), 판독본 wt/_heldout/D_cnr/D_cnr.topology.md 와 본문이 같다.)

## ⚠️ 자동 플래그 (사람 재확인 필요)

- **구동 소자 없는 net(gate로만 참조됨)**: VIN, VIP
  이 net을 source/drain으로 쓰는 소자가 topology.json에 없습니다 -- 외부 입력 핀이면 정상이지만, 내부에서 생성돼야 하는 신호라면 그걸 만드는 소자/감지망이 누락된 것일 수 있습니다.

## 📄 출처 매니페스트 (`source_manifest`)

- 그림/쪽: cnr_ota_sky130nm@8c839f7 CNR_OTA.sch (documents/CNR_OTA_SKY130NM/CNR_OTA.svg), 계층 펼침 MOS 72개(MOS 셀 인스턴스 47개, 버스 펼침) + R 6 + C 2 + TB 부하 C 2
- 소자 72개, 수동소자 10개 (로더가 netlist·passive_elements 개수와 대조)

## Net별 연결 표 (이 net에 물린 모든 단자)

| Net | 연결된 단자 (device.terminal) | 단자 수 |
|---|---|---|
| `IBPSR` | IDC.t1, x1[0].M1.gate, x1[1].M1.gate, x1[2].M1.gate, x1[3].M1.gate, x23[0].M1.gate, x23[1].M1.gate, x23[2].M1.gate, x23[3].M1.gate, x24.M1.drain, x24.M1.gate, x25.M1.gate, x29.M1.gate, x36[0].M1.gate, x36[1].M1.gate, x36[2].M1.gate, x36[3].M1.gate, x4[0].M1.gate, x4[1].M1.gate, x4[2].M1.gate, x4[3].M1.gate | 21 |
| `LPCO` | C1.t0, C2.t1, x37.t1, x38.t0, x42.M1.gate | 5 |
| `VBN1` | x10.M1.gate, x12.M1.drain, x13[0].M1.gate, x13[1].M1.gate, x15.M1.drain | 5 |
| `VBN2` | x1.M1.gate, x21.M1.drain, x2[0].M1.gate, x2[1].M1.gate, x4.M1.drain | 5 |
| `VBP` | x25.M1.drain, x26.M1.drain, x26.M1.gate, x28[0].M1.gate, x28[1].M1.gate, x28[2].M1.gate, x28[3].M1.gate, x28[4].M1.gate, x28[5].M1.gate, x44.M1.gate | 10 |
| `VBP1` | x16[0].M1.gate, x16[1].M1.gate, x18.M1.gate, x19.M1.drain, x20.M1.gate, x22.M1.drain | 6 |
| `VBP2` | x11.M1.gate, x2.M1.drain, x5[0].M1.gate, x5[1].M1.gate, x7.M1.gate, x8.M1.drain | 6 |
| `VCBN1` | x42.M1.drain, x45.M1.drain, x45.M1.gate, x52.M1.gate | 4 |
| `VCBN2` | x43.M1.drain, x46.M1.drain, x46.M1.gate, x47.M1.gate, x48.M1.gate | 5 |
| `VCBP` | x49.M1.gate, x50.M1.gate, x51.M1.drain, x51.M1.gate, x52.M1.drain | 5 |
| `VCN` | x14[0].M1.gate, x14[1].M1.gate, x15.M1.gate, x28[0].M1.drain, x28[1].M1.drain, x28[2].M1.drain, x28[3].M1.drain, x28[4].M1.drain, x28[5].M1.drain, x30.M1.drain, x30.M1.gate, x3[0].M1.gate, x3[1].M1.gate, x4.M1.gate | 14 |
| `VCON` | C2.t0, x35.M1.source, x38.t1, x4[0].M1.drain, x4[1].M1.drain, x4[2].M1.drain, x4[3].M1.drain | 7 |
| `VCONN` | x13[0].M1.drain, x13[1].M1.drain, x14[0].M1.source, x14[1].M1.source, x47.M1.drain | 5 |
| `VCONP` | x16[0].M1.drain, x16[1].M1.drain, x17[0].M1.source, x17[1].M1.source, x49.M1.drain | 5 |
| `VCOP` | C1.t1, x1[0].M1.drain, x1[1].M1.drain, x1[2].M1.drain, x1[3].M1.drain, x33.M1.source, x37.t0 | 7 |
| `VCOPN` | x2[0].M1.drain, x2[1].M1.drain, x3[0].M1.source, x3[1].M1.source, x48.M1.drain | 5 |
| `VCOPP` | x50.M1.drain, x5[0].M1.drain, x5[1].M1.drain, x6[0].M1.source, x6[1].M1.source | 5 |
| `VCP` | x12.M1.gate, x17[0].M1.gate, x17[1].M1.gate, x19.M1.gate, x21.M1.gate, x27.M1.drain, x27.M1.gate, x29.M1.drain, x6[0].M1.gate, x6[1].M1.gate, x8.M1.gate | 11 |
| `VCR` | x31.M1.gate, x39.t1, x40.t0 | 3 |
| `VCREF` | x31.M1.source, x36[0].M1.drain, x36[1].M1.drain, x36[2].M1.drain, x36[3].M1.drain, x43.M1.gate, x9.t0 | 7 |
| `VDD_1V8` | x11.M1.source, x16[0].M1.source, x16[1].M1.source, x18.M1.source, x20.M1.source, x26.M1.source, x27.M1.source, x28[0].M1.source, x28[1].M1.source, x28[2].M1.source, x28[3].M1.source, x28[4].M1.source, x28[5].M1.source, x31.M1.drain, x33.M1.drain, x35.M1.drain, x40.t1, x44.M1.source, x49.M1.source, x50.M1.source, x51.M1.source, x5[0].M1.source, x5[1].M1.source, x7.M1.source | 24 |
| `VIN` ⚠️ | x22.M1.gate | 1 |
| `VIP` ⚠️ | x2.M1.gate | 1 |
| `VON` | CL2.t0, x14[0].M1.drain, x14[1].M1.drain, x17[0].M1.drain, x17[1].M1.drain, x35.M1.gate | 6 |
| `VOP` | CL1.t0, x33.M1.gate, x3[0].M1.drain, x3[1].M1.drain, x6[0].M1.drain, x6[1].M1.drain | 6 |
| `VS` | x2.M1.source, x22.M1.source, x23[0].M1.drain, x23[1].M1.drain, x23[2].M1.drain, x23[3].M1.drain | 6 |
| `VSC` | x42.M1.source, x43.M1.source, x44.M1.drain | 3 |
| `VSS` | CL1.t1, CL2.t1, IDC.t0, x1.M1.source, x10.M1.source, x13[0].M1.source, x13[1].M1.source, x1[0].M1.source, x1[1].M1.source, x1[2].M1.source, x1[3].M1.source, x23[0].M1.source, x23[1].M1.source, x23[2].M1.source, x23[3].M1.source, x24.M1.source, x25.M1.source, x29.M1.source, x2[0].M1.source, x2[1].M1.source, x3.t0, x30.M1.source, x36[0].M1.source, x36[1].M1.source, x36[2].M1.source, x36[3].M1.source, x45.M1.source, x46.M1.source, x47.M1.source, x48.M1.source, x4[0].M1.source, x4[1].M1.source, x4[2].M1.source, x4[3].M1.source, x52.M1.source, x9.t1 | 36 |
| `net1` | x7.M1.drain, x8.M1.source | 2 |
| `net2` | x1.M1.drain, x4.M1.source | 2 |
| `net3` | x11.M1.drain, x12.M1.source | 2 |
| `net4` | x18.M1.drain, x19.M1.source | 2 |
| `net5` | x10.M1.drain, x15.M1.source | 2 |
| `net6` | x20.M1.drain, x21.M1.source | 2 |
| `net7` | x3.t1, x39.t0 | 2 |

## 소자별 연결 표 (name/kind/source/drain/gate)

| Name | Kind | Source | Drain | Gate |
|---|---|---|---|---|
| x1.M1 | nmos | `VSS` | `net2` | `VBN2` |
| x10.M1 | nmos | `VSS` | `net5` | `VBN1` |
| x11.M1 | pmos | `VDD_1V8` | `net3` | `VBP2` |
| x12.M1 | pmos | `net3` | `VBN1` | `VCP` |
| x13[0].M1 | nmos | `VSS` | `VCONN` | `VBN1` |
| x13[1].M1 | nmos | `VSS` | `VCONN` | `VBN1` |
| x14[0].M1 | nmos | `VCONN` | `VON` | `VCN` |
| x14[1].M1 | nmos | `VCONN` | `VON` | `VCN` |
| x15.M1 | nmos | `net5` | `VBN1` | `VCN` |
| x16[0].M1 | pmos | `VDD_1V8` | `VCONP` | `VBP1` |
| x16[1].M1 | pmos | `VDD_1V8` | `VCONP` | `VBP1` |
| x17[0].M1 | pmos | `VCONP` | `VON` | `VCP` |
| x17[1].M1 | pmos | `VCONP` | `VON` | `VCP` |
| x18.M1 | pmos | `VDD_1V8` | `net4` | `VBP1` |
| x19.M1 | pmos | `net4` | `VBP1` | `VCP` |
| x1[0].M1 | nmos | `VSS` | `VCOP` | `IBPSR` |
| x1[1].M1 | nmos | `VSS` | `VCOP` | `IBPSR` |
| x1[2].M1 | nmos | `VSS` | `VCOP` | `IBPSR` |
| x1[3].M1 | nmos | `VSS` | `VCOP` | `IBPSR` |
| x2.M1 | nmos | `VS` | `VBP2` | `VIP` |
| x20.M1 | pmos | `VDD_1V8` | `net6` | `VBP1` |
| x21.M1 | pmos | `net6` | `VBN2` | `VCP` |
| x22.M1 | nmos | `VS` | `VBP1` | `VIN` |
| x23[0].M1 | nmos | `VSS` | `VS` | `IBPSR` |
| x23[1].M1 | nmos | `VSS` | `VS` | `IBPSR` |
| x23[2].M1 | nmos | `VSS` | `VS` | `IBPSR` |
| x23[3].M1 | nmos | `VSS` | `VS` | `IBPSR` |
| x24.M1 | nmos | `VSS` | `IBPSR` | `IBPSR` |
| x25.M1 | nmos | `VSS` | `VBP` | `IBPSR` |
| x26.M1 | pmos | `VDD_1V8` | `VBP` | `VBP` |
| x27.M1 | pmos | `VDD_1V8` | `VCP` | `VCP` |
| x28[0].M1 | pmos | `VDD_1V8` | `VCN` | `VBP` |
| x28[1].M1 | pmos | `VDD_1V8` | `VCN` | `VBP` |
| x28[2].M1 | pmos | `VDD_1V8` | `VCN` | `VBP` |
| x28[3].M1 | pmos | `VDD_1V8` | `VCN` | `VBP` |
| x28[4].M1 | pmos | `VDD_1V8` | `VCN` | `VBP` |
| x28[5].M1 | pmos | `VDD_1V8` | `VCN` | `VBP` |
| x29.M1 | nmos | `VSS` | `VCP` | `IBPSR` |
| x2[0].M1 | nmos | `VSS` | `VCOPN` | `VBN2` |
| x2[1].M1 | nmos | `VSS` | `VCOPN` | `VBN2` |
| x30.M1 | nmos | `VSS` | `VCN` | `VCN` |
| x31.M1 | nmos | `VCREF` | `VDD_1V8` | `VCR` |
| x33.M1 | nmos | `VCOP` | `VDD_1V8` | `VOP` |
| x35.M1 | nmos | `VCON` | `VDD_1V8` | `VON` |
| x36[0].M1 | nmos | `VSS` | `VCREF` | `IBPSR` |
| x36[1].M1 | nmos | `VSS` | `VCREF` | `IBPSR` |
| x36[2].M1 | nmos | `VSS` | `VCREF` | `IBPSR` |
| x36[3].M1 | nmos | `VSS` | `VCREF` | `IBPSR` |
| x3[0].M1 | nmos | `VCOPN` | `VOP` | `VCN` |
| x3[1].M1 | nmos | `VCOPN` | `VOP` | `VCN` |
| x4.M1 | nmos | `net2` | `VBN2` | `VCN` |
| x42.M1 | pmos | `VSC` | `VCBN1` | `LPCO` |
| x43.M1 | pmos | `VSC` | `VCBN2` | `VCREF` |
| x44.M1 | pmos | `VDD_1V8` | `VSC` | `VBP` |
| x45.M1 | nmos | `VSS` | `VCBN1` | `VCBN1` |
| x46.M1 | nmos | `VSS` | `VCBN2` | `VCBN2` |
| x47.M1 | nmos | `VSS` | `VCONN` | `VCBN2` |
| x48.M1 | nmos | `VSS` | `VCOPN` | `VCBN2` |
| x49.M1 | pmos | `VDD_1V8` | `VCONP` | `VCBP` |
| x4[0].M1 | nmos | `VSS` | `VCON` | `IBPSR` |
| x4[1].M1 | nmos | `VSS` | `VCON` | `IBPSR` |
| x4[2].M1 | nmos | `VSS` | `VCON` | `IBPSR` |
| x4[3].M1 | nmos | `VSS` | `VCON` | `IBPSR` |
| x50.M1 | pmos | `VDD_1V8` | `VCOPP` | `VCBP` |
| x51.M1 | pmos | `VDD_1V8` | `VCBP` | `VCBP` |
| x52.M1 | nmos | `VSS` | `VCBP` | `VCBN1` |
| x5[0].M1 | pmos | `VDD_1V8` | `VCOPP` | `VBP2` |
| x5[1].M1 | pmos | `VDD_1V8` | `VCOPP` | `VBP2` |
| x6[0].M1 | pmos | `VCOPP` | `VOP` | `VCP` |
| x6[1].M1 | pmos | `VCOPP` | `VOP` | `VCP` |
| x7.M1 | pmos | `VDD_1V8` | `net1` | `VBP2` |
| x8.M1 | pmos | `net1` | `VBP2` | `VCP` |

## 수동 소자 표 (R/C 등 -- netlist 밖 `passive_elements`)

| Name | Kind | Terminals |
|---|---|---|
| C1 | capacitor | `LPCO`, `VCOP` |
| C2 | capacitor | `VCON`, `LPCO` |
| CL1 | capacitor | `VOP`, `VSS` |
| CL2 | capacitor | `VON`, `VSS` |
| x3 | resistor | `VSS`, `net7` |
| x37 | resistor | `VCOP`, `LPCO` |
| x38 | resistor | `LPCO`, `VCON` |
| x39 | resistor | `net7`, `VCR` |
| x40 | resistor | `VCR`, `VDD_1V8` |
| x9 | resistor | `VCREF`, `VSS` |

## ⚡ Ideal source 표 (전류원/전압원 -- netlist 밖 `ideal_sources`, **구현 불가 소자**)

| Name | Kind | Terminals | Value | Implementable |
|---|---|---|---|---|
| IDC | current_source | `VSS`, `IBPSR` | 2e-06 | ⚠️ False |

⚠️ 위 소자는 실제 회로에 없는 **이상적 모델링 소자**다(예: 논문의 외부 레퍼런스 전류원/전압원) -- `implementable: false`. sizing/layout 파이프라인(`sizing_recipe.py`/`stick_diagram.py`)이 이 배열을 참조할 일이 생기면 반드시 걸러내고 실제 트랜지스터로 구현하지 말 것.

총 72개 소자 + 10개 수동소자 + 1개 ideal source, 35개 net.
