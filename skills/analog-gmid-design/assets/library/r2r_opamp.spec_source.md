# r2r_opamp (held-out C, 판독 이름 C_r2r) -- spec 원문 표 추출

원문: R. Hogervorst, J. P. Tero, R. G. H. Eschauzier, J. H. Huijsing, *A Compact Power-Efficient 3 V CMOS Rail-to-Rail Input/Output
Operational Amplifier for VLSI Cell Libraries*, IEEE JSSC 29(12), Dec. 1994, pp.1505-1513.

- 웹: https://repository.tudelft.nl/file/File_0fc107fa-6796-4bae-9159-8537a431f171 (TU Delft repository 공개본)
- 로컬 PDF: `C:/Users/HSLEE/Documents/Todoc/fpga/wt/_heldout/tudelft_0fc1.pdf`
- 쪽 표기: **PDF 쪽(1~9)** 과 저널 쪽(PDF p.1 = JSSC p.1505)을 같이 적는다. 회로도 = PDF p.6 (JSSC p.1510) **Fig.13**, spec = PDF p.8 (JSSC p.1512) **Table I**.
- 판독 기록: `wt/_heldout/C_r2r/VERIFY.md`, 원문 표 확대 이미지 `wt/_heldout/C_r2r/img/table1_a.png`·`table1_b.png`.

> 저장소 등록 메모(2026-10-14): 아래 §1~§3 은 판독본 `wt/_heldout/C_r2r/C_r2r.spec_source.md` 를 옮기고 각 값에 원문 링크·쪽을 붙인 것이다.
> 사이징 spec 은 `r2r_opamp.sizing_spec.json` 이고, 사용자 결정(user_decisions.md 2026-10-14 held-out C D-9 확정 "sky130 1.8 V로 옮기고 spec을
> 다시 정함 (권고안)", 2026-10-13 "D1~D8은 권고대로", 2026-10-14 "C1~C3 모두 권고대로")에 따라 아래만 옮겼다:
>
> | spec 자리 | 값 | 원문(모두 위 웹 링크·로컬 PDF) |
> |---|---|---|
> | `supplies_v` | VDD 1.8, VSS 0 | 이식 결정값(D-9). 원 측정 3.3 V = PDF p.8 (JSSC p.1512) Table I 머리 |
> | 제약 `gain_ss_db >=` | 85 | PDF p.8 (JSSC p.1512) Table I opamp1 'Open-loop gain 85 dB' |
> | 제약 `gbw_ss_hz >=` | 2.6e6 | PDF p.8 (JSSC p.1512) Table I opamp1 'Unity-gain frequency 2.6 MHz' (CL 10 pF); PDF p.7 (JSSC p.1511) 본문 |
> | 제약 `pm_ss_deg >=` | 66 | PDF p.8 (JSSC p.1512) Table I opamp1 'Unity-gain phase margin 66°' (CL 10 pF); PDF p.7 (JSSC p.1511) 본문 |
> | 결정 대기 `pending_constraints` `supply_current_dc` (U-75) | (180e-6 A, 판정 안 함) | PDF p.8 (JSSC p.1512) Table I 'Quiescent current 180 µA' (3.3 V). 레일 전류 선언 경로 없음(N12) -- A·B 와 같은 이유 |
> | `input_dc` | 결정 대기 U-75 | 원문에 측정 입력 CM 값 없음(Table I·PDF p.7 본문은 CMR 범위만) |
> | `element_values.CM1`·`CM2` | 2e-12 F | PDF p.6 (JSSC p.1510) Fig.13 '2p CM1'·'CM2 2p' |
> | `element_values.CL` (measurement_load, topology Vo-VSS) | 10e-12 F | PDF p.8 (JSSC p.1512) Table I 머리 'Cload = 10 pF'; PDF p.7 (JSSC p.1511) 본문 'with a load capacitor of 10 pF' (C-1 (가)) |
> | `element_values.RL` (measurement_load, topology Vo-VSS) | 10e3 Ω | PDF p.8 (JSSC p.1512) Table I 머리 'Rload = 10 kΩ' -- 다른 끝 미기재, VSS 로 둠(§0) (C-1 (가)) |
> | `element_values.Ib1`·`Ib2`·`Ib4`·`Ib5`·`Ib6` | 4e-6, 7e-6, 4e-6, 7e-6, 2e-6 A | PDF p.6 (JSSC p.1510) Fig.13 'Ib1 4u'·'Ib2 7u'·'Ib4 4u'·'Ib5 7u'·'Ib6 2u' (C-2, 원 값 그대로) |
> | `node_voltage_targets_v` (Vb1~Vb6) | 결정 대기 CI-15 = 엔진 도출 | PDF p.6 (JSSC p.1510) Fig.13 원 값은 §3 표(C-3: 선언하지 않음) |
>
> slew 는 넣지 않았다(D-9 권고안). 보고만(spec 에 넣지 않음): 면적, 공급 범위, 출력 전류, CMR, 출력 스윙, offset, 잡음, CMRR, 정착 시간 -- §1 표.

## 0. 측정 부하 표현 (사용자 2026-10-14 C-1 (가))

사용자 D-6 (가)는 "측정 부하는 topology 밖 spec 쪽". 그러나 spec 스키마(`gmid_engine/authoring/spec_elements.py`, SPEC_CONTRACT.md 0절
'측정 부하 표지')의 `measurement_load` 는 `element_values.<topology 수동소자 이름>` 에만 붙는다(topology 에 없는 이름은 `element_unknown`).
선례 held-out A(`rfc_ota` CL out-gnd)·B(`erfc_ota` CL out-gnd)와 library 8회로(nmcnr 는 CL·RL 둘 다 Vout-agnd)는 전부 부하를 topology
`passive_elements` 에 넣고 spec 에서 `measurement_load: true` 로 표시했다. 그래서 C-1 (가)로 D-6 (가)를 바꿔 같은 방식을 따랐다:
topology `passive_elements` 에 `CL`(10 pF, Vo-VSS)·`RL`(10 kΩ, Vo-VSS)을 넣고 spec `element_values` 에서 `measurement_load: true` 로 표시했다
(면적 축 `area_search_m2` 에서 빠진다). 이 두 소자 추가 때문에 topology `connectivity_fp` 가 판독본(3d57f484...)과 달라졌다(c3d35d15...;
판독본에 CL·RL 만 더한 사본의 지문과 같음을 실측). `source_manifest.passive_count` 도 2 -> 4.

**RL 의 다른 끝 = VSS 로 둔 이유**: 원문 Table I 머리(PDF p.8, JSSC p.1512)는 'Rload = 10 kΩ' 만 적고 반대쪽 단자(VSS 인지 중간 전압인지)를
적지 않았다. 중간 전압(예: 공급 절반)으로 끝을 잡으려면 이상 전압원이 필요한데 엔진 graph S1 이 이상 전압원을 받지 않는다
(`graph/s1_values.py` `SUPPORTED_SOURCE_KINDS = ("current_source",)`). 그래서 레일 VSS 에 물렸다. 출력 DC 가 VSS 위에 있으면 RL 이 그만큼
DC 전류를 끌어가므로, 중간 전압 끝으로 측정했을 원 조건보다 DC 부하가 가혹할 수 있다.

## 1. Table I (opamp1 = Fig.13) -- PDF p.8 (JSSC p.1512)

Table I 머리: "Measurement results, Vsupply = 3.3 V, Rload = 10 kΩ, Cload = 10 pF, TA = 27 °C, unless otherwise stated".
opamp1 = Fig.13(Miller 보상, 이 topology), opamp2 = Fig.14(cascoded-Miller, 참고). 모든 값은 **실측**이다.

| 항목 | opamp1 (Fig.13) | opamp2 (Fig.14, 참고) | 단위 | 조건 |
|---|---|---|---|---|
| Die area | 0.04 | 0.04 | mm² | |
| Supply voltage range | 2.5 - 6 | 2.5 - 6 | V | |
| Quiescent current | 180 | 180 | µA | 3.3 V |
| Peak output current | 3 | 3 | mA | |
| Common-mode input range | VSS-0.4 to VDD+0.5 | 같음 | V | Vsup 3 V ~ 6 V |
| Common-mode input range | VSS-0.4 to VDD-1.4 | 같음 | V | Vsup 2.5 V ~ 2.9 V |
| Output voltage swing | VSS+0.1 to VDD-0.2 | 같음 | V | RL 10 kΩ |
| Offset voltage | 4.0 | 5.0 | mV | |
| Input noise voltage @10 kHz | 22 | 31 | nV/√Hz | |
| CMRR | 70 | 70 | dB | Vcm: VSS-0.4~VSS+1, VSS+1.3~VDD-1.3, VDD-1~VDD+0.5 |
| CMRR | 43 | 43 | dB | Vcm: VSS+1~VSS+1.3, VDD-1.3~VDD-1 (take-over 구간) |
| Open-loop gain | 85 | 87 | dB | |
| Unity-gain frequency | 2.6 | 6.4 | MHz | CL 10 pF |
| Unity-gain phase margin | 66 | 53 | ° | CL 10 pF |
| Slew rate | 2 | 4 | V/µs | Vcm: VSS+1.3~VDD-1.3 |
| Slew rate | 4 | 8 | V/µs | Vcm: VSS-0.4~VSS+1, VDD-1~VDD+0.5 |
| Large-signal settling (1%) | 440 | 275 | ns | Vstep 1 V |
| Small-signal settling (1%) | 220 | 180 | ns | Vstep 100 mV |

## 2. 본문 보조 값 (쪽 = PDF 쪽 / JSSC 쪽)

| 항목 | 값 | 출처 |
|---|---|---|
| 소비 전력 | 0.5 mW @ 3 V 공급 | PDF p.1 (JSSC p.1505) Introduction 끝 |
| 대역폭 대 전력비 | 4 MHz/mW (opamp1), 11 MHz/mW (opamp2), CL 10 pF | PDF p.1 (JSSC p.1505) Abstract, PDF p.6 (JSSC p.1510) |
| 공정 | 1 µm BiCMOS(CMOS 소자만), Vt,n = 0.64 V, Vt,p = -0.75 V | PDF p.6 (JSSC p.1510) VI 절 |
| 입력단 gm 변동 | 공통모드 범위 전체에서 약 15 % | PDF p.3 (JSSC p.1507), PDF p.8 (JSSC p.1512) 결론 |
| gm 제어 동작 구간 | P쌍만 VSS~VSS+1 V, 둘 다 VSS+1.3~VDD-1.3 V, N쌍만 VDD-1~VDD | PDF p.2 (JSSC p.1506) |
| 공급 감지(M29~M31) | 공급 2.9 V 미만에서 M8(P 전류 스위치)을 끔 | PDF p.3 (JSSC p.1507) |
| 공급 2.5~2.9 V CMR | VSS-0.4 to VDD-1.4 V | PDF p.7 (JSSC p.1511) 본문, Table I |
| 출력단 정지 전류 | 공급 전압에 무관(떠 있는 전류원 M27-M28 이 class-AB 제어 M19-M20 과 같은 구조) | PDF p.1 Abstract, PDF p.5 (JSSC p.1509) |
| 출력 극점 | ωout ≈ gm,out / CL (식 (4)) | PDF p.5~6 (JSSC p.1509~1510) V 절 |
| Miller 커패시터 | CM1 = CM2 = 2 pF | PDF p.6 (JSSC p.1510) Fig.13 |
| UGF·PM 본문 | 'unity-gain frequency of 2.6 MHz, with a load capacitor of 10 pF. The unity-gain phase margin is 66°' | PDF p.7 (JSSC p.1511) |

## 3. 바이어스 원 (Fig.13, 3.3 V 설계값) -- PDF p.6 (JSSC p.1510)

| 이름 | 종류 | 값 | 넷(topology) | 레일 기준(D-7 확정) | 1.8 V 이식 시 사실 |
|---|---|---|---|---|---|
| Ib1 | 이상 전류원 | 4 µA | VDD -> tail_p | | |
| Ib2 | 이상 전류원 | 7 µA | VDD -> n_abn | | |
| Ib4 | 이상 전류원 | 4 µA | tail_n -> VSS | | |
| Ib5 | 이상 전류원 | 7 µA | n_abp -> VSS | | |
| Ib6 | 이상 전류원 | 2 µA | n_t29 -> VSS (D-5 sink) | | |
| Vb1 | 이상 전압원 | 1.3 V | vb1 (bias_inputs) | VDD-1.3 | 원 값 그대로면 0.5 V |
| Vb3 | 이상 전압원 | 1.2 V | vb3 (bias_inputs) | VSS+1.2 | 1.2 V |
| Vb4 | 이상 전압원 | 1.2 V | vb4 (bias_inputs) | VSS+1.2 | 1.2 V |
| Vb5 | 이상 전압원 | 1.3 V | vb5n (bias_inputs) | VDD-1.3 | 0.5 V |
| Vb6 | 이상 전압원 | 1.8 V | vb6n (bias_inputs) | VSS+1.8 | 1.8 V = VDD |

번호 Ib3·Vb2 는 Fig.13 에 없다(결번).

## 4. 1.8 V 이식에서 원 회로 의미가 바뀌는 곳 (사실만)

- PDF p.3 (JSSC p.1507): 공급 2.9 V 미만에서 M29~M31 공급 감지가 M8 을 끈다 -- 1.8 V 는 이 문턱 아래다.
- PDF p.2 (JSSC p.1506) gm 제어 구간을 1.8 V 에 그대로 대입하면: 'P쌍만' VSS~VSS+1 V = 0~1.0 V 와 'N쌍만' VDD-1~VDD = 0.8~1.8 V 가 겹치고,
  '둘 다' VSS+1.3~VDD-1.3 V = 1.3~0.5 V 는 빈 구간이 된다(원문 3.3 V 기준 구간을 산술 대입만 한 것).
- PDF p.3 (JSSC p.1507) '출력단은 VGS 2개 적층 허용' 전제와 M21-M22·M23-M24 두 단 diode 적층.
- PDF p.6 (JSSC p.1510) Vt,n 0.64 V / Vt,p -0.75 V 공정 기준 바이어스값.
