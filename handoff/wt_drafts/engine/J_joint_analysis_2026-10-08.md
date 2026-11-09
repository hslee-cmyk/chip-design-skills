# J 공동분석 패킷 -- SP1(u1-sp1) 산출 기준 (2026-10-08)

> **성격**: 회로 해석 **제안서**다. 결정은 사용자 몫이고, 이 문서는 topology·spec·structure.json 어느 것도 바꾸지 않았다.
> 각 절은 독립적으로 읽히게 썼고 끝에 `Decision needed`를 둔다.

## 0. 공통 사항

**측정 기준**
- 엔진: 브랜치 `u1-sp1`(worktree `wt/u1-sp1`, HEAD `7c757e8`), `build_s1v(s1, None, count_budget=N_S=2·12·49·49·5, stop_on_unsupported=False)`.
  S1 입력은 `_scratch_u1/common.py`의 `s1_of()`를 그대로 썼다(`supplies_for`). 덤프 스크립트는 scratchpad에 두었다(저장소 밖).
- 넷 표: `assets/topology_to_markdown.py`로 4회로를 새로 생성했다(scratchpad 출력, library의 `.topology.md`는 건드리지 않음). 아래 표는 그 출력에서 관련 행만 옮겼다.
- 지문: `s1v_rule_fp = e6c195f2…1aef`. topology_fp: ngcc `bd0dab46…6d84`, nmcnr `0f1551b3…83e9`, 파일럿 `025d0aed…c383`, sf `d8fd0296…721d`.

**SP1 정지 현황(9회로 실측)**

| 회로 | 정지(unsupported) | review_needed |
|---|---|---|
| ngcc_3stage_ff | `undeclared_loop_constraint` ×1 (loop:M8:V1) | `composite_block_pending_ratify` ×2, `loop_polarity_undefined` ×2, L 동치류 {M8, M14} 주인 `name_order` |
| nmcnr_amplifier | `undeclared_loop_constraint` ×1 (loop:M201:NodeM2) | `loop_polarity_undefined` ×4 |
| current_reuse (파일럿) | `cs_output_low_impedance` ×1 (Vx, CM 루프 뷰) | `mixed_drive_signal_drain` ×3, `loop_polarity_undefined` ×4 (+ info `cm_loop_unconstrained`) |
| sf_pushpull_output_opamp | `composite_dag_not_chain` ×2, `loop_record_only` ×9 | `composite_block_pending_ratify` ×5, `mixed_drive_unresolved_group` ×8, L 동치류 3개 `name_order` |
| 나머지 5회로 | 없음 | 없음 |

**구조로 못 가르는 DC 역할 그룹**(S1 `dc_role` review_needed, J-U3-c): 라이브러리 전체 **4그룹 10소자** = sf 3그룹 8소자({M6, M9, M17}, {M8, M11}, {M14, M16, M20}) + ngcc 1그룹 2소자({M8, M14}).
(요청문의 "sf 4그룹 10소자"는 라이브러리 전체 수치다 -- sf만은 3그룹 8소자.)

**structure.json에 '쓸 것'에 대한 주의(모든 절 공통)**
- 형식: `{schema_version, topology_hash, rule_hash, facts[{concept, subject, value, status:"ratified", evidence{rule, nets[]}, approval_id}]}`. `subject`·`value`는 문자열이다.
- **현재 엔진이 소비하는 concept는 둘뿐**이다: `drive_kind`(`build_s1v`가 넷 구동 종류를 고정)와 `stage_members`(stage A의 declared 대조, 유도 입력 아님).
  아래 절의 다른 concept(`loop_role`, `feedforward_cell`, `ac_ground_exception`, `dc_role`, `l_class_owner` 등)은 **소비 코드가 없다**.
  "만들면 반드시 배선" 원칙에 따라 그 사실을 쓰려면 소비 코드를 같이 넣어야 하고, 그것은 공유 엔진 코드 변경이므로 **별도 승인 대상**이다.
- `rule_hash`는 `S1V_RULE_FILES` 바이트 지문이라, 새 concept 소비 코드가 들어가면 바뀐다. 사실 파일은 **코드 변경 뒤에** 작성해야 stale(`structure_fact_stale`)로 되돌아가지 않는다.
- `stage_a`는 `declared_loop_cuts`를 `build_s1v`에 넘기지 않는다(`pipeline/stage_a.py:101`). 따라서 spec에 루프 안정도 제약을 선언해도 지금은 `undeclared_loop_constraint`가 풀리지 않는다(J-B 선택지 B2의 선행 배선).

---

## J-A. ngcc_3stage_ff -- 세 단이 Vout에서 복합 블록 하나로 합쳐진다

### A.1 넷 표 (전체 16소자, 3수동소자)

| Net | 연결 단자 |
|---|---|
| `TAIL` | M0.drain, M1.source, M2.source |
| `ND` | M1.drain, M3.drain, M3.gate, M4.gate, M6B.gate |
| `V1` | Cm1.t0, M14.gate, M2.drain, M4.drain, M8.gate |
| `NP` | M10.gate, M8.drain, M9.drain, M9.gate |
| `V2` | Cm2.t0, M10.drain, M11.drain, M13.gate |
| `NX` | M5.drain, M6A.drain, M6A.gate, M6B.drain, M7.gate |
| `Vout` | CL.t0, Cm1.t1, Cm2.t1, M12.drain, M13.drain, M14.drain, M7.drain |
| `VBP` / `VBN` | M0·M5·M12 gate / M11 gate (외부 바이어스) |
| `vdd` / `gnd` | 레일 |

| 소자 | S / D / G | 소자 | S / D / G |
|---|---|---|---|
| M0 p | vdd / TAIL / VBP | M8 n | gnd / NP / V1 |
| M1 p | TAIL / ND / Vinn | M9 p | vdd / NP / NP |
| M2 p | TAIL / V1 / Vinp | M10 p | vdd / V2 / NP |
| M3 n | gnd / ND / ND | M11 n | gnd / V2 / VBN |
| M4 n | gnd / V1 / ND | M12 p | vdd / Vout / VBP |
| M5 p | vdd / NX / VBP | M13 n | gnd / Vout / V2 |
| M6A n | gnd / NX / NX | M14 n | gnd / Vout / V1 |
| M6B n | gnd / NX / ND | M7 n | gnd / Vout / NX |

수동: Cm1 (V1–Vout), Cm2 (V2–Vout), CL (Vout–gnd).

### A.2 엔진이 유도한 것과 멈춘 이유
- 전달 뷰 셀: M1·M2·M4·M6B·M7·M8·M10·M13·M14 = CS(순방향), M3·M6A·M9 = diode_load, M0·M5·M11·M12 = off. stage 시작 = {M1, M2, M8, M13, M14}, 미러 입력 = {ND, NP, NX}.
- 구동 종류: Vout만 `current`(drain 진입, 출구 없음), 나머지 전압.
- `stage_dist`: V1 = 1, V2 = 2, **Vout = 1**. Vout이 1인 이유는 M14(V1→Vout)와 M7(ND→NX→Vout 미러 연장)이 지름길을 만들기 때문이다.
- 블록 1(입력쌍)은 규칙 9(c) 미러 연장으로 ND→M6B→NX(M6A diode)→M7까지 이어져 **출력이 (V1, Vout) 둘**이 된다. 블록 2(M8, V2), 블록 3(M13·M14, Vout)이 모두 Vout을 공유하므로
  DEC-81 합류 조건이 성립하고, 네 블록 키 {(V1, Vout), (V2), (Vout), (Vout)}가 **복합 블록 하나**(cells 16, chain True)로 묶인다.
- 경로 부호(엔진 출력, CS = −1): Vinn→ND→NX→Vout −1, Vinn→ND→V1→NP→V2→Vout −1, Vinn→ND→V1→Vout −1, Vinp→V1→NP→V2→Vout +1, Vinp→V1→Vout +1.
  여기 가중이 Vinn −½, Vinp +½이므로 **다섯 경로가 모두 같은 위상으로 더해진다**(feedforward가 주경로와 동위상 -- NGCC의 요구와 맞다).
- 정지: 전달 뷰는 `composite_block_pending_ratify`(review)로 멈추고, 실제 unsupported 정지는 루프 뷰 `loop:M8:V1`의 `undeclared_loop_constraint`다(J-B).

### A.3 해석 선택지

| 안 | 내용 | 결과 |
|---|---|---|
| A1 | 엔진 출력 그대로 -- Vout 복합 블록 하나 | gain 예산을 단별로 나눌 수 없다. 격자 곱 Π의 밑이 16셀이라 GB4 상한 격자가 매우 커진다. NGCC 조건(gmf1 = gm1, gmf2 = gm2)을 블록 단위로 표현할 수 없다. |
| **A2(권장)** | **주경로 사슬 B1→B2→B3 + feedforward 셀 2묶음** | B1 = {M1, M2, M0(tail), M3, M4} 출력 V1. B2 = {M8, M9, M10, M11} 출력 V2(비반전 단: CS + PMOS 미러). B3 = {M13, M12} 출력 Vout. FF1(gmf1) = {M6B, M5, M6A, M7}: 입력 탭 ND(B1 내부 미러 노드), 출력 Vout. FF2(gmf2) = {M14}: 입력 V1, 출력 Vout. Vout은 gm3·gmf2·gmf1 세 트랜스컨덕턴스의 합류 노드로 B3에 둔다. |
| A3 | B1이 두 출력(V1, Vout)을 갖는 블록 + M14는 B3의 둘째 입력 | 전기적으로는 A2와 같다(규칙 9(c)를 건드리지 않는다). 하지만 FF1의 DOF(M6B/M3, M7/M6A 비)와 그 극점(NX)이 B1 예산에 섞이고, B1 gain을 "V1 전압 이득 + Vout 트랜스컨덕턴스"의 두 종류로 정의해야 한다. |

### A.4 권장: A2 -- 근거
- **NGCC 원리**(You, Embabi, Sánchez-Sinencio, IEEE JSSC 32(12), 1997; 분석은 Leung & Mok, IEEE TCAS-I 48(9), 2001): 주경로는 gm1·gm2·gm3 세 단이고, gmf1(입력→출력)과 gmf2(1단 출력→출력)는
  **별도 feedforward 트랜스컨덕터**다. 영점 상쇄 조건이 gmf1 = gm1, gmf2 = gm2라는 **비율 조건**으로 주어지므로, feedforward를 독립 셀 묶음으로 두어야 이 조건을 제약으로 쓸 수 있다.
  gmf2 = gm2(gm14 = gm8)는 이미 2026-10-08 J14에서 비율 matching으로 ratified됐다(출처 기록: Lee et al. JSTS 2007, source_manifest Fig. 3).
- 이 회로의 gmf1은 입력쌍 전류를 미러로 재사용한다: ND(M3 diode)→M6B가 복사 → NX에서 M5 바이어스와의 차가 M6A diode로 → M7. 따라서 gmf1 = gm1·(gm6B/gm3)·(gm7/gm6A).
  NGCC 조건 gmf1 = gm1은 (W/L)6B/(W/L)3 × (W/L)7/(W/L)6A = 1 이라는 **비율 조건**이 된다(도면 M6A:M7 = 1:2면 M6B:M3 = 1:2). 수치 비율은 사용자 확정 대상이며 여기서 정하지 않는다.
- **gain·극점 귀속**(A2 기준):
  - DC 이득: A0 = (gm1/G1)(gm2,eff/G2)(gm3/Go) + (gm1/G1)(gmf2/Go) + gmf1/Go. 여기서 gm2,eff = gm8·(gm10/gm9), G1 = gds2 + gds4, G2 = gds10 + gds11, Go = gds12 + gds13 + gds14 + gds7.
    첫 항이 1/(gm2,eff/G2)배 이상 크므로 **gain 예산은 B1·B2·B3 곱에만 배분**하고 feedforward 항은 §2 MNA 경로 기여로 계산한다(예산 항목 없음).
  - 극점 노드: V1(Cm1 Miller로 지배극), V2(Cm2), Vout(CL) = 주 극점 3개. ND·NP = 미러 극점(B1·B2 내부), **NX = FF1 고유 극점**(gm6A/C_NX). FF 셀의 부하 기여(Cgs14가 V1에, gds7·gds14가 Vout에)는 해당 노드의 G·C에 들어간다.
  - GBW ≈ gm1/Cm1(+ gmf1 기여는 고주파에서 작다). 보상 규칙(GB5)은 NMC와 같은 극점 배치에 영점 상쇄 조건을 더한 것으로 다룬다.
- 측정 근거: 엔진의 경로 부호 다섯 개가 모두 동위상이라 A2의 feedforward 귀속과 모순이 없다. 복합 블록이 생긴 원인은 FF 셀이 Vout `stage_dist`를 1로 당긴 것이고 회로 구조 자체의 모호성이 아니다.

### A.5 승인 시 structure.json에 쓸 사실(제안)

| concept | subject | value | evidence.nets |
|---|---|---|---|
| `block_chain` | `Vout` | `V1>V2>Vout` | V1, V2, Vout |
| `block_output` | `B1` | `V1` (ND→M6B 미러 연장은 B1 밖) | ND, V1 |
| `feedforward_cell` | `M14` | `ff2:V1->Vout` | V1, Vout |
| `feedforward_cell` | `M6B` | `ff1:ND->Vout` | ND, NX |
| `feedforward_cell` | `M6A` | `ff1:ND->Vout` | NX |
| `feedforward_cell` | `M7` | `ff1:ND->Vout` | NX, Vout |
| `feedforward_cell` | `M5` | `ff1_bias` | NX |

`approval_id`는 승인 기록 id, `evidence.rule` = `J-A NGCC decomposition`. **모두 신규 concept**이라 소비 코드(composite_blocks 앞에서 FF 셀을 주경로 블록 구성에서 빼고 B3 합류 입력으로 붙이는 것)가 선행돼야 한다.
비율 조건(gmf1 = gm1)은 structure 사실이 아니라 sizing 제약 후보로 따로 기록한다.

**Decision needed**: ngcc의 Vout 복합 블록을 (A1) 그대로 둘지, (A2) 주경로 3단 + feedforward 셀 2묶음으로 분해할지, (A3) B1 이중 출력으로 둘지. **권장 A2** + gmf1 = gm1 비율 조건을 sizing 제약 후보로 등록할지 여부.

---

## J-B. ngcc·nmcnr 루프 뷰 -- (2) Miller + (3-b)로 분류된 중첩 Miller 루프

### B.1 넷 표

ngcc: A.1 표 참조(Cm1 V1–Vout, Cm2 V2–Vout).

nmcnr_amplifier (15소자, 5수동소자, 레일 vdd +0.9 / vss −0.9):

| Net | 연결 단자 |
|---|---|
| `NodeTail` | M101.drain, M102.source, M103.source |
| `NodeF1` / `NodeF2` | M102.drain, M104.drain, M106.source / M103.drain, M105.drain, M107.source |
| `NodeM1` | M106.drain, M108.drain, M108.gate, M109.gate |
| `NodeM2` | Cm1.t0, M107.drain, M109.drain, M201.gate |
| `NodeC` | M201.drain, M203.drain, M203.gate, M204.gate |
| `NodeS2` | Cm2.t0, M202.drain, M204.drain, M301.gate |
| `NodeCM` | Cm1.t1, Cm2.t1, Rm.t0 |
| `Vout` | CL.t0, M301.drain, M302.drain, RL.t0, Rm.t1 |

소자: M101 p(vdd/NodeTail/VB1), M102 p(NodeTail/NodeF1/Vin_n), M103 p(NodeTail/NodeF2/Vin_p), M104·M105 n(vss/F1·F2/VB2), M106·M107 n(F1·F2/NodeM1·NodeM2/VB3), M108 p(vdd/NodeM1/NodeM1), M109 p(vdd/NodeM2/NodeM1),
M201 p(vdd/NodeC/NodeM2), M202 p(vdd/NodeS2/VB4), M203 n(vss/NodeC/NodeC), M204 n(vss/NodeS2/NodeC), M301 n(vss/Vout/NodeS2), M302 p(vdd/Vout/VB5). 수동: Cm1(NodeM2–NodeCM), Cm2(NodeS2–NodeCM), Rm(NodeCM–Vout), CL·RL(Vout–vss).

단 부호(손 유도): nmcnr 1단 Vin_p→NodeM2 반전, 2단 NodeM2→NodeS2 **비반전**(M201 CS + M203/M204 미러), 3단 NodeS2→Vout 반전. ngcc도 2단(M8 + M9/M10 미러) 비반전, 3단 반전. 두 회로 모두 NMC 표준 극성이다.

### B.2 엔진이 유도한 것과 멈춘 이유

| 회로 | 루프(노드열 / 소자) | 분류 | 끊는 점 |
|---|---|---|---|
| ngcc | V1→NP→V2→Vout→V1 / M8, M10, M13, Cm1 (바깥 Miller: Cm1이 2·3단을 감쌈) | miller + loop_view | (M8, V1) |
| ngcc | V1→NP→V2→Vout→V1 / M8, M10, Cm2, Cm1 (Cm2–Cm1 직렬 용량 경로) | miller + loop_view | (M8, V1) |
| ngcc | V1→Vout→V1 / M14, Cm1 | miller | -- |
| ngcc | V2→Vout→V2 / M13, Cm2 (안쪽 Miller) | miller | -- |
| nmcnr | NodeM2→NodeC→NodeS2→Vout→NodeCM→NodeM2 / M201, M204, M301, Rm, Cm1 (바깥) | miller + loop_view | (M201, NodeM2) |
| nmcnr | NodeM2→NodeC→NodeS2→NodeCM→NodeM2 / M201, M204, Cm2, Cm1 (직렬 용량) | miller + loop_view | (M201, NodeM2) |
| nmcnr | NodeS2→Vout→NodeCM→NodeS2 / M301, Rm, Cm2 (안쪽) | miller | -- |

- 루프 뷰 하나씩(`loop:M8:V1`, `loop:M201:NodeM2`)이 생기고, 포트쌍 CM 루프가 아니므로 안정도 제약 미선언 → `undeclared_loop_constraint` 정지.
- **(3-b)가 붙은 원인(실측)**: 복귀 경로 판정에 쓰는 `dist`는 수동소자 엣지 비용 0이라 Cm1·Cm2가 앞 노드와 뒤 노드의 거리를 같게 만든다.
  nmcnr `dist`: NodeM2 1, NodeC 2, **NodeS2 1, Vout 1, NodeCM 1**. 그래서 순방향 소자 M204(NodeC 2 → NodeS2 1)와 M301(1 → 1, 동률)이 '복귀 경로'로 세어지고, "복귀 경로에 능동 셀" 조건이 성립한다.
  ngcc도 같다(V2 1, Vout 1; M10: NP 2 → V2 1). 즉 이 루프들의 실제 되먹임 소자는 **보상 커패시터뿐**이고, (3-b) 판정은 거리 동률이 만든 결과다.
- 극성: 모두 커패시터를 지나므로 0(`loop_polarity_undefined`).

### B.3 선택지

| 안 | 내용 | 결과(실측·근거) |
|---|---|---|
| **B1(권장)** | 중첩 Miller 루프를 **보상 내부 루프**로 ratify -- 루프 뷰를 만들지 않고 GB5(보상)만 받는다. 안정도는 전체 루프 제약(선언된 `pm_ss_deg`: ngcc ≥ 63.4°, nmcnr ≥ 70°)과 개루프 극점의 우반면 부재(P = 0)로 덮는다. | 루프 뷰 0 → `undeclared_loop_constraint`와 루프 뷰 극성 review가 사라진다. 계획 N3.2-2 (2)의 예시 문장("nmcnr 중첩 Miller" = (2), 루프 뷰를 만들지 않는다)과 일치. P = 0은 사용자 결정 Q10(최종 판정 = Nyquist Z = N + P, .pz 독립 측정)이 이미 오라클에서 잰다. |
| B2 | 안쪽 루프마다 별도 안정도 제약 선언(루프 뷰 `loop:M8:V1` 등에 PM 하한) | spec 값이 새로 필요하다(사용자 값, 문헌 근거 없음). 그 루프를 M8 gate에서 끊은 PM은 표준 설계 지표가 아니라서 값의 근거를 만들기 어렵다. 게다가 `stage_a`가 `declared_loop_cuts`를 넘기지 않아 배선부터 필요하다. |
| B3 | 규칙 변경: (3-b) 복귀 경로를 수동소자 엣지를 뺀 `stage_dist`로 판정 | **실측(scratch monkeypatch, 9회로)**: nmcnr는 루프 뷰가 사라지지만 **파일럿 CMFB 루프가 (4) `record_only` 4개로 떨어지고**, ngcc는 루프 뷰가 오히려 2개(`loop:M13:V2` 추가)가 되며, sf는 루프 뷰 6개 + `undeclared_loop_constraint`가 새로 생긴다. 규칙만으로 가르면 다른 회로를 깨므로 기각. |

### B.4 권장: B1 -- 근거
- **회로 원리**: NMC/NGCC에서 Cm1·Cm2가 만드는 국소 되먹임은 개루프 증폭기 **내부**의 극점 분리 장치다. 설계 문헌은 이 루프들의 안정도를 별도 PM으로 지정하지 않고,
  전체 단위 이득 되먹임의 전달함수(비지배 복소 극점 쌍의 감쇠)로 다룬다 -- Eschauzier, Kerklaan, Huijsing, IEEE JSSC 27(12), 1992(NMC/MNMC); Leung & Mok, IEEE TCAS-I 48(9), 2001(NMC·NMCNR·NGCC 비교, Butterworth 배치).
  안쪽 루프 조건(예: gm2/Cm2, gm3/CL가 GBW의 정해진 배수)은 그 전체 전달함수 배치에서 나오는 결과다.
- **놓치지 않는 것**: Bode PM은 개루프 전달함수가 안정(P = 0)할 때만 유효하다. 안쪽 루프가 불안정하면 개루프 극점이 우반면에 생기므로, P = 0 검사(Q10 결정, .pz)가 그 경우를 잡는다.
- 루프의 부호도 회로 원리와 맞다: 바깥 Cm1 루프 = 2단(+)·3단(−) → 음되먹임, 안쪽 Cm2 = 3단(−) → 음되먹임. Cm2–Cm1 직렬 용량 경로는 비반전 2단을 감싸는 용량 결합(+)으로, 독립 루프가 아니라 Vout(NodeCM)에 묶인 수동망의 메시다(NMC 영점·NMCNR Rm 처리 대상, J7 결정 "nmcnr Rm → M301"과 같은 소관).

### B.5 승인 시 structure.json에 쓸 사실(제안)

| 회로 | concept | subject | value | evidence.nets |
|---|---|---|---|---|
| ngcc | `loop_role` | `loop:M8:V1` | `compensation_internal` | V1, NP, V2, Vout |
| nmcnr | `loop_role` | `loop:M201:NodeM2` | `compensation_internal` | NodeM2, NodeC, NodeS2, NodeCM, Vout |

`evidence.rule` = `J-B nested Miller = (2) only; stability via pm_ss_deg + open-loop P=0`. **신규 concept** -- 소비 코드(`_loop_findings`/루프 뷰 생성에서 ratified `compensation_internal` 끊는 점을 루프 뷰로 만들지 않는 분기)가 선행돼야 한다.
같은 승인으로 "전체 루프 metric의 판정에 P = 0 조건이 포함된다"는 것을 MOD5/오라클 쪽 확인 항목으로 남긴다.

**Decision needed**: 중첩 Miller 보상 루프를 (B1) 전체 PM + 개루프 P = 0으로 덮는 보상 내부 루프로 볼지, (B2) 안쪽 루프마다 별도 안정도 제약을 둘지. **권장 B1**(B3 규칙 변경은 실측으로 기각).

---

## J-C. current_reuse(파일럿) CMFB 경로 -- 레플리카 M58이 CM 루프 뷰에서 신호가 된다

### C.1 넷 표 (CMFB·레플리카 부분)

| Net | 연결 단자 |
|---|---|
| `Vx` | M1a.source, M1b.source, **M58.source**, M6.drain, M7.drain |
| `Vy` | M4a.source, M4b.source, M5.drain, **M63.source** |
| `N58_57` | M57.source, M58.drain |
| `Vbias2` | M2a.gate, M2b.gate, M57.drain, M57.gate, M58.gate, M68.drain |
| `N64_63` | M63.drain, M64.source |
| `Vbias3` | M3a.gate, M3b.gate, M61.drain, M63.gate, M64.drain, M64.gate |
| `N1a2a` / `N1b2b` | M1a.drain, M2a.source / M1b.drain, M2b.source |
| `Voc` | M37a.gate, R1.t1, R2.t0 (R1: Vom–Voc, R2: Voc–Vop) |
| `Ncmfb_tail` | M37a.source, M37b.source, M38.drain |
| `Vcmfb` | M36a.drain, M36a.gate, M37a.drain, **M7.gate** |
| `N36b` | M36b.drain, M36b.gate, M37b.drain |
| `Voc_des` | M37b.gate, M39.drain, M39.gate, M40.source |

| 소자 | S / D / G | 소자 | S / D / G |
|---|---|---|---|
| M58 p | Vx / N58_57 / Vbias2 | M63 n | Vy / N64_63 / Vbias3 |
| M57 p | N58_57 / Vbias2 / Vbias2 | M64 n | N64_63 / Vbias3 / Vbias3 |
| M68 n | gnd / Vbias2 / Vbias4 | M61 p | vdd / Vbias3 / Vbias1 |
| M6 p | vdd / Vx / Vbias1 | M7 p | vdd / Vx / Vcmfb |
| M37a n | Ncmfb_tail / Vcmfb / Voc | M37b n | Ncmfb_tail / N36b / Voc_des |
| M38 n | gnd / Ncmfb_tail / Vbias4 | M36a·M36b p | diode (Vcmfb, N36b) |
| M1a·M1b p | Vx / N1a2a·N1b2b / Vip·Vim | M2a·M2b p | N1a2a·N1b2b / Vom1·Vop1 / Vbias2 |

### C.2 엔진이 유도한 것과 멈춘 이유
- 전달 뷰(기모드): Vbias2·Vbias3는 J1 술어로 교류접지(`bias_dependent`, 사슬 출발 N58_57·Vx / N64_63·Vy), Vx·Vy 등은 가상접지. M58·M63 = off. 문제 없음.
- CM 루프 뷰 `loop:M37a:Voc`(포트쌍 CM 루프 대응, `cm_pair`, info `cm_loop_unconstrained`): Voc를 여기하면 M37a→Vcmfb→M7이 Vx를 움직이고, **Vbias2가 `bias_moving`**(레플리카 사슬 출발 Vx가 움직임)이 된다. 그 결과
  - M58 = CS(degeneration), M2a/M2b = CS(degeneration, gate Vbias2가 신호), M1a/M1b = CG.
  - Vx 구동 종류 = `mixed_bias_drain` → **전압**(drain 쪽 M6·M7의 DC 역할이 바이어스 전류원). 그래서 블록 {Voc→Vx}(M37a 입력, M7 미러)가 **출력노드 Vx(낮은 임피던스: M1a·M1b·M58 source)**로 끝나 `cs_output_low_impedance` 정지.
  - 혼재 노드 3개 `mixed_drive_signal_drain`: N1a2a(M1a), N1b2b(M1b), N58_57(M58 -- DC 역할 규칙 5 '신호 소자').

### C.3 역할 해석
- **M58/M57 (그리고 대칭으로 M63/M64)**: Vx(입력쌍 공통 source)에서 출발해 M58→M57(diode)→Vbias2→M68(전류원)로 내려가는 **레플리카 바이어스 사슬**이다. 전류는 M68이 정한다.
  Vbias2 = V(Vx) − VSG58 − VSG57이라 캐스코드 M2a/M2b의 gate가 입력 공통모드를 따라가며 M1a/M1b의 VSD를 일정하게 유지한다(레플리카 바이어스 캐스코드). M63/M64/M61은 NMOS 쪽 같은 구조(Vbias3 = V(Vy) + VGS63 + VGS64).
  → **DC 역할은 신호 소자가 아니라 바이어스 생성(레플리카)**이다.
- **구조 증거(9회로 실측)**: "소자 X의 drain에서 같은 DC 가지(중간 노드에 다른 전류 단자 없음)를 직렬로 따라가면 X 자신의 gate 넷에 닿는다" = **복합 diode** 패턴을 9회로 전수로 찾으면
  **파일럿 M58(→M57→Vbias2), M63(→M64→Vbias3)**과 **sf의 M5·M6·M7·M8·M13·M14**(J-D)에서만 발동하고 나머지 7회로는 0이다. 즉 M58·M63은 sf의 자기바이어스 캐스코드 기준과 같은 '복합 diode 기준'이다(계획 N3.2-2 (나)가 "파일럿 레플리카 루프도 같은 형태"라고 적은 관찰과 일치).
- **'M58 전류 분할'(J11 파일럿 항목, J1과 함께)**: Vx KCL은 I6 + I7 = I1a + I1b + I58이고 I58 = I68(고정)이다. 입력쌍 한쪽 전류는 (I6 + I7 − I68)/2. NMOS 쪽도 I5 = I4a + I4b + I61.
  이것은 DC 전류 예산(꼬리 비율, GB7) 항목이고 AC 신호 경로가 아니다. AC로 M58은 M68이 전류를 고정하므로 Vx에 gds 차수 부하만 준다.
- **M37b**: CMFB 차동쌍의 기준쪽(gate Voc_des = M39/M40 diode 스택이 만든 원하는 CM). CM 루프 뷰에서는 CG(출력 N36b는 M36b diode에서 끝나는 막다른 가지)로, M37a의 source degeneration 역할을 한다 → 유효 gm_CMFB ≈ gm37a/2(gm37a = gm37b일 때). 신호 경로가 아니라 루프 내부의 degeneration 부하다. matching은 {M37a, M37b} diff_pair, {M36a, M36b} 대칭 부하.
- **M7**(J4): DC로는 M6과 함께 Vx에 꼬리 전류를 공급하는 전류원(J-U4 2026-10-08 '꼬리 비율 미러 {M36a, M7}')이고, AC로는 gate Vcmfb로 CM 오차 전류를 Vx에 주입하는 K8형 측면 주입이다. 두 역할 공존이 정상이다.

### C.4 선택지

| 안 | 내용 | 결과(scratch 실측) |
|---|---|---|
| **C1(권장)** | **J1 예외 기록**: CMFB 루프 뷰(`loop:M37a:Voc`)에서만 Vbias2를 교류접지로 본다(레플리카는 따라 움직이지만 신호 전류를 싣지 않는다). CM 전달 뷰·전원 뷰에서는 J1 그대로(움직임). | Vbias2 접지로 계산하면: M2a/M2b = CG(캐스코드), M1a/M1b = CG, M58 = CG(막다른 가지), Vx = **전류 구동**(자동), N1a2a/N1b2b = 전류, N58_57 = 전압. 블록 = {Voc → (Vom1, Vop1)}(M37a 입력, M7 미러, M1a/b·M2a/b 캐스코드, M6 tail) → 출력단 {Vom}, {Vop}. **`cs_output_low_impedance`·혼재 3건 모두 사라지고** 남는 것은 극성 review 4건 + info 1건. |
| C2 | J1 그대로 두고 `drive_kind` 사실만 ratify(Vx = current, N58_57 = voltage, N1a2a/N1b2b = current) | 지금 로더로 바로 쓸 수 있다. 실측: 정지와 혼재 기록은 사라지지만 **M2a/M2b가 CS(degeneration)로 남아 블록 출력이 N1a2a/N1b2b에서 끊기고, Vom1/Vop1은 어느 블록의 출력도 아니다**(출력단 블록이 입력으로만 읽는다). 분할이 불완전해 gain 모델이 M2a/M2b를 놓친다. |
| C3 | Vbias2 움직임을 정식 루프로 보고 M58 경로를 CM 루프의 일부로 유지(현 상태 + review) | 레플리카가 CM 루프 이득에 들어가는 1차 경로처럼 취급된다. 실제로는 M68이 전류를 고정해 M58이 신호 전류를 내지 않으므로 회로 원리와 맞지 않고 정지가 남는다. |

### C.5 권장: C1 -- 근거
- CM 루프 이득 = gm_CMFB,eff · (M7 미러) · (M1a/b CG 전류 이득 ≈ 1) · (Vom1/Vop1 CM 임피던스) · (출력단 이득) · (R1/R2 평균). M2a의 gate가 레플리카로 움직여도 M2a는 M1a와 직렬이라 **채널 전류는 M1a가 정한다** -- 캐스코드 동작은 그대로이고, gate 추종은 N1a2a의 소신호 전압(M1a의 ro 변조)만 바꾸는 2차 효과다. 따라서 루프 뷰의 극점·이득을 1차로 정할 때 Vbias2를 접지로 보는 것이 맞고, 잔여 효과는 오라클(ngspice CM 루프)이 잰다.
- 반대로 CM 전달 뷰(CMRR)·ICMR·전원 뷰에서는 레플리카 추종이 **설계 목적 그 자체**(입력 CM이 바뀌어도 M1 VSD 유지)라 J1의 "움직이는 뷰에서는 접지가 아니다"를 유지해야 한다. C1은 J1을 루프 뷰 하나에서만 예외 처리하므로 J1의 결론을 뒤집지 않는다(J1 본문: "규칙이 끊지 못한 넷이 나온 경우에만 예외로 기록").
- DC 역할은 위 복합 diode 증거대로 M58·M63 = **레플리카(복합 diode 기준)**로 ratify하는 것을 함께 권한다(J-D와 같은 규칙으로 처리되면 회로 이름 없는 일반 규칙이 된다).

### C.6 승인 시 structure.json에 쓸 사실(제안)

| concept | subject | value | evidence.nets | 소비 코드 |
|---|---|---|---|---|
| `ac_ground_exception` | `Vbias2` | `loop:M37a:Voc` | Vbias2, N58_57, Vx | 신규(`view_ac_ground`) |
| `dc_role` | `M58` | `diode_reference_composite` (레플리카, 전류 = I_M68) | Vx, N58_57, Vbias2 | 신규(`dc_roles` 규칙 (4) 상속 -- 현재 미구현 J-U3-b) |
| `dc_role` | `M63` | `diode_reference_composite` (레플리카, 전류 = I_M61) | Vy, N64_63, Vbias3 | 신규 |
| `drive_kind` | `Vx` | `current` | Vx | **기존 concept(바로 소비됨)** -- C1 아래에서는 엔진이 이미 current로 내므로 중복 확인용 |

C2를 택하면 `drive_kind` 4건(Vx current, N58_57 voltage, N1a2a current, N1b2b current)만 쓰면 되고 코드 변경은 없지만 C.4의 블록 공백이 남는다.

**Decision needed**: (C1) CMFB 루프 뷰에서만 Vbias2를 교류접지로 보는 J1 예외 + M58/M63 = 레플리카 DC 역할, (C2) drive_kind 사실만, (C3) 현 상태 유지 중 무엇으로 할지. **권장 C1**(J11 'M58 전류 분할'은 GB7 DC 예산 항목 I_tail,eff = I6 + I7 − I68로 확정).

---

## J-D. sf_pushpull_output_opamp -- 못 가르는 DC 역할 그룹, 혼재 ×8, DAG 비사슬 ×2, M6↔M8·M5↔M7 matching

### D.1 넷 표 (22소자, 5수동, 이상전류원 IBias)

| Net | 연결 단자 |
|---|---|
| `TAIL` | M1.source, M2.source, M3.drain |
| `N1` | M1.drain, M10.gate, M5.gate, R1a.t1 |
| `N5` | M17.gate, M5.drain, M6.gate, M9.gate, R1a.t0 |
| `N56` | M5.source, M6.drain |
| `N2` | M12.gate, M2.drain, M7.gate, R1b.t1 |
| `N7` | M11.gate, M7.drain, M8.gate, R1b.t0 |
| `N78` | M7.source, M8.drain |
| `N910` | M10.source, M9.drain |
| `N1112` | M11.drain, M12.source |
| `N12` | M12.drain, M13.gate, M15.gate, R1c.t0 |
| `N13` | M13.drain, M14.gate, M16.gate, M20.gate, R1c.t1 |
| `N1314` | M13.source, M14.drain |
| `N1516` | M15.source, M16.drain |
| `Y` | Cc.t0, M10.drain, M15.drain, M18.gate, M19.gate |
| `N17` | M17.drain, M18.source, M22.gate |
| `N20` | M19.source, M20.drain, M21.gate |
| `vout` | CL.t0, M21.source, M22.source |
| `NB` | IBias.t1, M3.gate, M4.drain, M4.gate |

소자: M1·M2 n(TAIL/N1·N2/vin_p·vin_n), M3 n(vss/TAIL/NB), M4 n diode(NB); 왼쪽 PMOS: M6 p(vdd/N56/N5), M5 p(N56/N5/N1), M9 p(vdd/N910/N5), M10 p(N910/Y/N1), M17 p(vdd/N17/N5);
오른쪽 PMOS: M8 p(vdd/N78/N7), M7 p(N78/N7/N2), M11 p(vdd/N1112/N7), M12 p(N1112/N12/N2); NMOS: M14 n(vss/N1314/N13), M13 n(N1314/N13/N12), M16 n(vss/N1516/N13), M15 n(N1516/Y/N12), M20 n(vss/N20/N13);
버퍼: M18 p(N17/vss/Y), M19 n(N20/vdd/Y), M21 p(vout/vss/N20), M22 n(vout/vdd/N17). 수동: R1a(N5–N1), R1b(N7–N2), R1c(N12–N13), Cc(Y–agnd), CL(vout–agnd).

### D.2 엔진이 유도한 것과 멈춘 이유
- DC 역할 review 그룹(J-U3-c): {M6, M9, M17}(gate N5, source vdd), {M8, M11}(gate N7), {M14, M16, M20}(gate N13, source vss). 그룹 안에 gate = drain diode가 없고 gate가 신호 넷이라 "기준이 그룹 안에 없다" → 전원 잠정 '신호 소자'.
- 그 결과 M5·M6·M7·M8·M9·M11·M13·M14·M16·M17·M20이 모두 stage를 시작하는 CS가 되고(시작 셀 16개), 블록이 N56, N78, N1314, (N1112, N12), (N1516, N910, Y) 등 복합 블록 5개로 쪼개진다.
  그중 둘은 앞 블록이 서로 다른 stage에서 갈라져 들어와 `composite_dag_not_chain`.
- 혼재 노드 8개(`mixed_drive_unresolved_group`): N56, N78, N910, N1112, N1314, N1516, N17, N20 -- drain 쪽이 위 그룹 소자.
- 루프 9개 모두 `record_only`: {N1, N5}(M5, R1a), {N1, N56, N5}, {N5, N56}(M6, M5)와 오른쪽·NMOS 쪽 같은 형태 각 3개.
- **DC 역할만 바꿔 본 실측(scratch)**: M6·M8·M14 = diode 기준, M9·M17·M11·M16·M20 = 바이어스 전류원으로 바꿔도 `composite_dag_not_chain` 1, `record_only` 9, 혼재 3이 남는다.
  원인은 규칙 9(c)의 미러 인식이 단순 diode(gate = drain)만 보기 때문이다 -- 이 회로의 기준은 **복합 diode**다.

### D.3 회로 해석
- 이 회로는 **current-mirror(대칭) OTA + push-pull 소스 팔로워 출력단**이다(Allen L26 p.26-6). 입력쌍 M1/M2의 부하는 **저항 자기바이어스 캐스코드 미러의 기준쪽**이다:
  - 왼쪽: M6(gate N5) 위에 캐스코드 M5(gate N1), 그 사이 R1a(N5–N1). 전류 경로 vdd→M6→N56→M5→N5→R1a→N1→M1. M6의 gate N5가 **자기 가지의 아래쪽 노드**에서 오므로 M6+M5+R1a는 하나의 diode처럼 동작한다(복합 diode). 출력: M9/M10(N5/N1 gate) → Y, M17(N5) → N17.
  - 오른쪽: M8/M7/R1b 같은 구조, 출력 M11/M12 → N12. NMOS: M14/M13/R1c가 N12 전류를 받는 기준, 출력 M16/M15 → Y, M20 → N20.
- 따라서 이득 노드는 **Y 하나**(캐스코드 미러 두 출력의 합, gm_eff = B·gm1)이고, N1/N5·N2/N7·N12/N13은 저임피던스 미러 입력(블록 내부 노드)이다.
  Y→M18/M19(팔로워)→N17/N20→M22/M21(팔로워)→vout은 버퍼 블록이고, M17·M20은 미러 출력으로 팔로워 바이어스 전류를 주되 그 전류가 신호를 따라 변한다(원문 "the bias currents through M18 and M19 vary with the signal" → J12-d 기본안 K8 측면 주입).
- **복합 diode 구조 판정(9회로 실측)**: J-C에 적은 '같은 DC 가지를 따라가면 자기 gate에 닿는 소자' 패턴이 sf에서 정확히 M5·M6·M7·M8·M13·M14에 발동하고(파일럿 M58·M63 외 다른 회로 0), 9개 `record_only` 루프는 전부 이 세 복합 diode {M6, M5, R1a}, {M8, M7, R1b}, {M14, M13, R1c} 내부에 있다.

### D.4 선택지

| 안 | 내용 | 결과 |
|---|---|---|
| **D1(권장)** | **복합 diode 기준을 diode로 ratify**(J12-h 결론): M6·M8·M14 = 미러 기준(diode_reference, 복합), M5·M7·M13 = 캐스코드 기준(같은 복합 diode 멤버), M9·M17·M11·M16·M20 = 그 미러의 출력(DC 바이어스 전류원, AC로는 gate 신호를 받는 K8형). 내부 루프 9개 = diode 내부 국소 루프(루프로 세지 않음). | 기대 구조: 이득 블록 {Y} 하나(입력쌍 + 세 미러, stage 1) + 버퍼 블록 {vout}(M17·M20 측면 주입). 복합 블록·DAG 비사슬·record_only·혼재 8건이 함께 해소될 것으로 본다. **단 DC 역할만으로는 부족함을 실측했으므로**(D.2) 규칙 9(c) 미러 인식과 루프 분류 (나)에 '복합 diode'를 넣는 코드 변경이 필요하다(일반 구조 규칙: 9회로 중 이 8소자에서만 발동). |
| D2 | 그룹을 '신호 소자'로 유지(현 상태)하고 복합 블록 경계만 ratify | 텍스트북 구조(단일 이득단)와 맞지 않는 4~5단 분할이 남는다. gain 예산이 존재하지 않는 단들에 배분된다. 비권장. |
| D3 | sf를 'unsupported 회로'로 보고 결과만 보고 | 9회로 전부 포함 결정(2026-10-07)과 충돌. 비권장. |

### D.5 M6↔M8, M5↔M7은 matching 대상인가 -- 예(권장)
- 두 쌍은 차동쌍의 **좌우 부하**다: 같은 DC 전류(I_tail/2), 같은 구조(기준 + 캐스코드 + 저항), 대칭 노드 짝(N1↔N2, N5↔N7, N56↔N78). 5T OTA의 미러 부하 쌍과 같은 자리라
  입력환산 offset에 (gm6/gm1)·σ_VT6 형태로 들어간다. 출력 쪽 비대칭(오른쪽만 NMOS 미러를 한 번 더 거침)은 미러 **출력**에서 생기므로 입력쪽 반쪽 대칭과 무관하다.
- 현재 J-U4 표는 이 둘을 서로 다른 gate 묶음(N5 {M6, M9, M17}, N7 {M8, M11})으로만 잡아 대칭쌍 그룹이 없다(판단 3 대기, matching_swing_spec_proposal §8.2).
- 권장 matching: `branch_symmetric` {M6, M8}, {M5, M7}, 저항 {R1a, R1b}; 미러 비율 그룹 {M6: M9, M17}, {M8: M11}, {M14: M16, M20}; 대칭 출력 {M9, M11}·{M10, M12}(B배 출력, 계통 offset 0 조건 = 좌우 미러비 동일, NMOS 미러 1:1).

### D.6 승인 시 structure.json에 쓸 사실(제안)

| concept | subject | value | evidence.nets |
|---|---|---|---|
| `dc_role` | `M6` / `M8` / `M14` | `diode_reference_composite` | (N56, N5, N1) / (N78, N7, N2) / (N1314, N13, N12) |
| `dc_role` | `M5` / `M7` / `M13` | `diode_reference_composite_cascode` | 같은 가지 |
| `dc_role` | `M9`, `M17`, `M11`, `M16`, `M20` (각 1행) | `bias_current_source` (미러 출력, AC는 K8) | gate 넷 N5 / N7 / N13 |
| `mirror_input` | `N5`, `N1`, `N7`, `N2`, `N13`, `N12` (각 1행) | `composite_diode` | 해당 가지 |
| `loop_role` | `{N1,N5}`·`{N1,N56,N5}`·`{N5,N56}` 등 9행 | `composite_diode_internal` | 루프 노드 |
| `drive_kind` | `N17`, `N20` | `voltage` (J12-b 기본안: 팔로워 출력) | -- (**기존 concept**) |
| `drive_kind` | `N910`, `N1112`, `N1516` | `current` (미러 출력 → 캐스코드 source) | -- (**기존 concept**) |
| `l_class_owner` | `{M6,M9,M17}` / `{M8,M11}` / `{M14,M16,M20}` | `M6` / `M8` / `M14` (diode 기준 규칙, 지금은 name_order로 M17·M11·M14) | -- |
| matching(J14) | `{M6,M8}`, `{M5,M7}`, `{R1a,R1b}` | `branch_symmetric` | 대칭 넷 짝 |

`drive_kind` 5건 외에는 신규 concept다. **근본 처리는 사실 목록보다 '복합 diode' 일반 규칙 1개**(미러 인식·DC 역할·루프 분류에 공통)가 낫다 -- 회로 이름 없이 구조로 판정되고 9회로 실측에서 파일럿 2·sf 6소자에만 발동한다. 이 경우 structure.json에는 ratify 기록(규칙 산출 대조 확인)만 남는다.

**Decision needed**: (1) sf 세 그룹을 저항 자기바이어스 캐스코드 미러의 **복합 diode 기준**으로 해석(D1)하고 이를 일반 구조 규칙(코드 변경, 승인 필요)으로 구현할지, 사실 목록으로 개별 ratify할지. (2) M6↔M8·M5↔M7(+R1a↔R1b)을 `branch_symmetric` matching으로 확정할지. **권장: D1을 일반 규칙으로 + matching 확정**.

---

## J-E. 입력 DC·헤드룸 -- nmcnr 0 V, sf 0.9 V, 파일럿 입력 창

### E.1 현 선언(spec)과 구조식

| 회로 | 전원 | spec `input_dc` | 입력 창(구조식) |
|---|---|---|---|
| nmcnr | vdd +0.9 / vss −0.9 | **`pending: SP-2`**(값 없음. "0 V"는 agnd 관례 가정이지 선언이 아니다) | PMOS 입력·폴디드: Vin,max = vdd − VSDsat101 − VSG102; Vin,min = vss + VDSsat104 − \|Vthp\| < vss → vss로 자름 |
| sf_pushpull | vdd 1.8 / vss 0 / agnd 0.9 | **`net: agnd` (0.9 V)**, user_spec U-25(2026-09-21) | NMOS 입력: Vin,min = VGS1(VSB = V_TAIL) + VDSAT3; Vin,max = vdd − VSG6 − I1·R1a + Vthn |
| 파일럿 | vdd 1.8 / gnd 0 | `pending: SP-2` | 상보 입력: VDSAT5 + VGS4 ≤ Vin ≤ VDD − VSDsat6 − VSG1(창 폭 = VDD − VGS4 − VSG1 − VDSAT5 − VSDsat6) |

LUT 수치(matching_swing_spec_proposal §2.4·§7·§8의 측정을 인용 -- **이 패킷에서 재측정하지 않음**, W 5 µm 한 슬라이스·bulk = 레일 가정):
- nmcnr: VSG102 1.06–1.20 V(L ≥ 0.5 µm) → Vin,max = −0.26 ~ −0.48 V; L 0.18 µm에서도 ≈ −0.06 V. **0 V는 모든 L bin에서 창 밖.**
- sf: Vin,min = 0.83–0.99 V → **0.9 V는 하한에 걸린다**(입력 gm/ID ≳ 15, 꼬리 VDSAT ≲ 0.12 V일 때만 포함). 상한(위 식)은 ≈ 1.3 V 규모라 여유는 위쪽에 있다.
- 파일럿: 창 폭 L 0.15 µm(pfet) +0.14 V, L 0.18 µm −0.02 V, L 0.5 µm −0.15 V, 창 하한 ≈ 0.79 V. **pfet 최단 bin에서만 열린다.**

### E.2 선택지(회로별)

| 회로 | 안 | 결과 |
|---|---|---|
| nmcnr | **E-n1(권장)** SP-2 (c): 값 없이 W4 자유 변수(창 안), 결과에 '요구 입력 공통모드' 보고. agnd 0 V 관례는 nmcnr에 적용하지 않는다고 확정 | 탐색 가능. 새 상수 없음. 원문 앵커(단위 이득 팔로워 0.5 V 계단)는 `icmr_v ≥ 0.5 V` 제안과 함께 창 폭 제약으로 쓴다(제안서 §7) |
| | E-n2 0 V를 선언 | 모든 bin에서 창 밖 → 탐색 전 달성 불가 보고(결정 Q4-(6)). 회로가 쓸모없어진다 |
| | E-n3 창 중앙값(예: −0.5 V 근처)을 숫자로 선언 | 근거가 bin·gm/ID에 따라 움직이는 값을 상수로 박는 것이라 비권장(상수 금지 원칙) |
| sf | **E-s1(권장)** 0.9 V(agnd) 유지 + `icm_margin_v ≥ 0` 제약으로 탐색 | agnd는 이 분할전원 구조의 아날로그 접지(사용자 확인 2026-10-08: Cc가 agnd에 붙는 dual supply)라 입력 기준점으로 맞다. 창 하한이 입력 gm/ID·꼬리 VDSAT를 구속하지만 불가능은 아니다. 실제 위험은 입력이 아니라 **4-팔로워 출력단 창**(L 0.15 +0.11 V, bulk = 레일이면 vout 범위 음수) -- 별도 실현가능성 보고 |
| | E-s2 입력 DC를 창 중앙(≈1.1 V)으로 변경 | spec(user_spec) 변경이 필요하고 agnd 기준 설계 의도와 어긋난다 |
| 파일럿 | **E-p1(권장)** SP-2 (c) 유지(값 없음, 창 안 자유 변수) + "창이 pfet L 0.15 µm bin에서만 열린다"를 탐색 공간 구조 경고로 보고. 창이 비면 탐색 전 달성 불가 | 새 상수 없음. 논문 ICMR 결과값 [0.5765, 0.9001] V는 0.18 µm 공정 값이라 쓰지 않는다(논문 값 인용 금지 원칙) |
| | E-p2 입력 DC 값을 선언 | SC 응용에서 입력 CM은 기준 스위치가 정하는 한 점이라 회로 밖 결정이다 -- 사용자 시스템 값이 있을 때만 |

### E.3 권장 -- 근거
- 입력 DC는 회로가 아니라 **사용 환경**(앞단·기준 스위치)이 정하는 값이고, 회로가 정하는 것은 창이다. 선언이 없는 nmcnr·파일럿은 창 안 자유 변수(SP-2 (c), G7-U2 기본안)가 원칙에 맞고, 선언이 있는 sf는 그 선언(agnd)이 회로 정의(분할 전원 중간 레일)와 일치하므로 유지한다.
- 세 회로 모두 수치가 bulk 연결 가정에 민감하다(bulk = 레일, 결정 Q4-(6) 유지). 창 경계는 LUT 한 슬라이스 값이라 SPICE DC 스윕(오라클 U6)으로 확인한다.

### E.4 승인 시 기록
structure.json 사실이 아니라 **spec/결정 기록** 항목이다: nmcnr·파일럿 `input_dc` = `pending: SP-2` 유지 + SP-2 정책 (c) 확정, sf `input_dc` 유지, 세 회로에 `icm_margin_v`(제안 metric) 보고·제약 연결. spec 파일 수정은 사용자 승인 후 별도 작업.

**Decision needed**: (1) SP-2 정책을 (c)(창 안 자유 변수 + 보고)로 확정하고 nmcnr에 0 V 관례를 적용하지 않을지, (2) sf 입력 DC 0.9 V(agnd)를 유지할지, (3) 파일럿을 pfet 최단 bin 경고와 함께 탐색할지. **권장: (1) 예 (2) 유지 (3) 예**.

---

## J-F. 그 밖의 SP1 review_needed

### F.1 `loop_polarity_undefined` (파일럿 ×4, nmcnr ×4, ngcc ×2) -- 계획 J7(Cc–Rz 직렬 루프 극성)
- 엔진 규칙: 커패시터를 지나는 사이클은 극성 0(저주파 경로 없음) → 그 사이클이 루프 뷰에 속하면 review.
- 파일럿 CM 루프 뷰의 사이클 6개 중 DC 경로 사이클 4개(M25·M26·pass 경유)는 **극성 −1(음되먹임)**으로 정상이고, 미정의 2개는 출력단 M26(또는 M16)을 **Miller 보상 Cc2–Rz2(Cc1–Rz1)가 우회**하는 사이클이다. 이것은 별도 되먹임이 아니라 보상 커패시터를 통한 feedforward 경로(우반면 영점 -- J7 결정 "Rz1 → M16, Rz2 → M26" R = 1/gm으로 상쇄)다.
- nmcnr·ngcc의 미정의 극성은 J-B의 Miller 루프 뷰에서만 나온다(전달 뷰의 (2) 단독 루프에는 극성 review가 붙지 않는다). **J-B B1을 택하면 이 6건은 사라진다.**

| 안 | 내용 |
|---|---|
| **F1-a(권장)** | 루프 **뷰의 극성 = 그 뷰의 DC 경로 사이클 극성**(파일럿 CM 루프 = −1). 커패시터 사이클은 극성을 `ac_only`로 기록(info)하고 GB5 보상 후보 목록에만 올린다 |
| F1-b | 수동소자 엣지 +1, 루프 극성 = 능동 셀 부호 곱(고주파 극성). 파일럿 Cc 사이클은 +1이 되어 "양되먹임"처럼 보이므로 해석 주석이 필요하다 |

승인 시: 일반 규칙 변경(`_loops`의 F_LOOP_POLARITY 조건 -- DC 사이클이 하나라도 있으면 그 극성 사용). structure.json에 쓴다면 `loop_polarity` / `loop:M37a:Voc` / `-1`(신규 concept).

### F.2 `composite_block_pending_ratify` (ngcc ×2)
J-A의 결론으로 닫힌다(A2 채택 시 복합 블록 0).

### F.3 ngcc L 동치류 {M8, M14} 주인 tie(`name_order`, review_needed)
- 두 소자는 gate V1·source gnd를 공유한다. 2026-10-08 J14로 비율 matching(gm14 = gm8, NGCC gmf2 = gm2) ratified → 같은 L이 맞다.
- DEC-17 순서(tail → 첫 stage tail → diode → 이름)에서 둘 다 해당이 없어 이름순으로 **M14**가 주인이 된다. 이 tie-break 때문에 rename 불변성 측정에서 ngcc 1건이 사상 밖으로 바뀐다(`measure_out.txt`, CONTRACT 10.3 불변량 2의 문서화된 예외).
- 권장: 주인 = **M8**(주경로 2단 입력. FF 셀은 주경로를 복사하는 쪽이라 주경로 소자가 기준이 되는 것이 회로 원리에 맞다). 일반 규칙으로는 "feedforward로 ratify된 셀보다 주경로 stage 시작 셀 우선"(J-A A2의 사실을 입력으로 씀).
- DC 역할({M8, M14} 기준 없는 그룹): **신호 소자**로 ratify. DC 전류는 V1이 균형점에서 ND와 같아지는 조건(V1 ≈ VGS3)으로 M3 diode에 묵시적으로 미러된다 -- 2단 OTA의 계통 offset 0 조건과 같은 관계이고 sizing 제약 후보다(바이어스 전류원으로 보면 stage가 사라진다 -- 계획 용어집 실측과 같은 이유).
- 승인 시: `l_class_owner` / `{M8,M14}` / `M8`, `dc_role` / `M8`·`M14` / `signal`(신규 concept).

### F.4 sf L 동치류 3개 `name_order`
J-D D1(복합 diode 기준) 채택 시 diode 기준 규칙으로 M6·M8·M14가 주인이 된다(실측 emulation에서 `current_source_member` 규칙으로 M6·M8·M14 확인).

**Decision needed**: (1) 루프 극성 규칙 F1-a(뷰 극성 = DC 사이클 극성, 커패시터 사이클 ac_only) 채택 여부, (2) ngcc {M8, M14} 주인 = M8과 DC 역할 = 신호 소자 확정 여부. **권장: (1) F1-a (2) 예**.

---

## 부록. 결정 요약과 코드 변경 의존

| 항목 | 권장 | 기존 concept만으로 가능? | 필요한 엔진 변경(별도 승인) |
|---|---|---|---|
| J-A | A2 주경로 3단 + FF 2묶음 | 아니오 | 복합 블록 앞에서 FF 셀 분리·B3 합류 입력 |
| J-B | B1 보상 내부 루프 | 아니오 | `loop_role` 소비(루프 뷰 생성 생략) |
| J-C | C1 루프 뷰 한정 J1 예외 + M58/M63 레플리카 | 부분(C2는 가능하나 불완전) | `ac_ground_exception` 소비, DC 역할 상속(J-U3-b) |
| J-D | D1 복합 diode 일반 규칙 + matching | 아니오(`drive_kind` 5건만 가능) | 복합 diode 판정(미러 입력·DC 역할·루프 (나)) |
| J-E | SP-2 (c), sf 0.9 V 유지 | spec/결정 기록 | 없음(`icm_margin_v` metric은 MOD5 제안) |
| J-F | F1-a 극성, ngcc 주인 M8 | 아니오 | 극성 규칙, L 주인 규칙 |

판정 순서(계획 N7.1): J-C(J1·J11) → J-D(J12-h·J12-d) → J-A(J12 ngcc) → J-B(J11·J7) → J-F → J-E(SP-2). J-C·J-D의 '복합 diode' 규칙이 공통 입력이므로 먼저 정하면 나머지 판정의 실측이 바뀐다.
