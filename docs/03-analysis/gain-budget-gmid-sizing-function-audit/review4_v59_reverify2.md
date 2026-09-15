# plan v5.9 3차 검증 (patch_v59c 반영본)

- 대상: 작업 트리 plan(1015줄). 사본은 scratchpad `review4/plan_v59c.md`. v59b 사본과 줄 단위 diff 전수를 읽음
- 직접 확인한 사실(실측)
  - `library/sf_pushpull_output_opamp.topology.json`(커밋 4ea001f)
    - netlist: M1(g vin_p, d N1), M2(g vin_n, d N2), 공통 source TAIL, M3/M4 tail 미러(IBias vdd→NB)
    - M9 → N910 → M10 → Y, M16 → N1516 → M15 → Y
    - 버퍼: M17(pmos, g N5, d N17), M18(pmos, s N17, d vss, g Y), M19(nmos, s N20, d vdd, g Y), M20(nmos, g N13, d N20), M22(nmos, s vout, d vdd, g N17), M21(pmos, s vout, d vss, g N20)
    - passive: R1a[N5, N1], R1b[N7, N2], R1c[N12, N13], Cc[Y, agnd], CL[vout, agnd]
    - `_paper_target_spec`: supplies_v vdd 1.8 / vss 0 / agnd 0.9, IBias 50 µA, CL 1 pF, dc_gain ≥ 65 dB, gbw ≥ 60 MHz, rout ≤ 1000 Ω, R1·Cc 유도
    - `supply_nets` 키 없음
  - `pushpull_follower_buffer`(12b7e69)
    - 레일 표기 vss, CL[vout, agnd], vin DC = agnd, rout ≤ 1000, minimize power, buffer_bandwidth report_only
    - bias gate VPB1·VNB1은 gate에만 붙음. `supply_nets` 없음
  - `two_stage_ota_sf`
    - inherits `_spec_two_stage_ota` + two_stage_ota sizing_roles, 추가 CL 3 pF@vout, rout ≤ 1000, 감지 노드 vout
    - `run_harness.py:112` `"CL": 3e-12`. `supply_nets` 없음
  - sf opamp 버퍼 bias 넷
    - N5 = {M6.g, M5.d, M9.g, M17.g, R1a}
    - N13 = {M14.g, M13.d, M16.g, M20.g, R1c}
    - 둘 다 gate에만 붙은 넷이 아니다
  - `stick_diagram.py:3147` `_RAIL_NETS = frozenset({"vdd","gnd","vss"})`, `sizing_recipe.py:3882-3883`(DF-26 줄 인용 맞음)
  - **작업 트리 `two_stage_ota.topology.json`에 커밋 안 된 connectivity 변경**: M1.gate `vin_p` → `vin_n`, M2.gate `vin_n` → `vin_p`

## 1. 지난 지적 5건 해소 여부

| 지적 | 판정 | 근거(plan.md 새 줄) | 해소 방식이 만든 문제 |
|---|---|---|---|
| N1 막음(파일럿 Cf1/Cf2 → (iii) 정지) | 해소 | 304: 루프 탐지 그래프에서 교류접지와 뷰의 여기 포트 넷을 제거한다. Cf1[Vom, Vip]·Cf2[Vop, Vim]는 출력노드–여기 포트 사이 부하가 된다. (iii)은 "여기 포트가 아닌 노드로 돌아오는 수동 되먹임"으로 좁혀졌다 | A4, A5 |
| N2 높음(class-AB) | 부분 해소 | 304: pass 셀은 방향 없는 2단자라 폐경로 엣지로 세지 않는다(M9a/M9b 역병렬 루프 해소). 419: 같은 출력노드로 합류하는 병렬 셀은 한 블록이라 `계산 규칙 있음`. 836 J3도 같은 취지 | **A1(높음)**: 한 블록인데 입력 넷이 둘이다 |
| N3 높음(레일 넷 미정의) | 해소 | 237 DEC-60: `supply_nets`(topology, 넷 목록)와 `supplies`(spec, 전압)로 분리하고, 기존 4개 회로는 전환기 이름 집합(DF-26)을 쓴다. 276, 301, 326, 348, 936. 794 6a 착수 조건에 U-26(b) | A3(IC11 시점) |
| 이월 #9 높음(`wall_clock_budget_s`) | 해소 | 211 DEC-34 기본안 300 s 공통, 878 U-26(c), 795 6b 착수 조건 | 없음 |
| N4 중간(S1 키·ratified 무효화) | 해소 | 326 키에 `supply_nets`(topology 해시)와 `supplies` 해시, 340 전이 조건에 레일 전압 선언 변경 | 없음 |

### 검사 1의 (a)~(d) 답

- **(a) 루프 탐지에서 루프가 잘못 지워지는가**
  - 파일럿 CMFB: Vom/Vop → R1/R2 → Voc → M37a → Vcmfb(diode) → M7 → Vx → M1a·M2a → Vom1 → M26/M16 → Vop/Vom. 경로에 여기 포트(Vip/Vim)도, 교류접지도 없다. Voc는 R1/R2 단자라 교류접지 (2)에서 빠진다. 수동 경로가 내부 노드(Voc)로 돌아오므로 루프로 **남는다**.
  - LDO형 분압 되먹임: 분압점은 여기 포트가 아니라서 루프로 남고 (iii) `기록만`으로 정지한다. 의도대로다.
  - **단,** Vx → N1a2a 엣지가 "전류 구동 source->drain"으로 잡히는지는 판정 기준(노드 구동 종류냐 셀 분류냐)이 모호하다. 차동 전달 뷰에서 M1a는 CS로 분류되므로 셀 기준으로 읽으면 이 엣지가 사라지고 CMFB 루프를 못 찾는다(A4).
  - pass 무방향 규칙은 pass만 지나는 루프를 조용히 지운다(A5).
- **(b) 병렬 셀 한 블록 규칙이 `계산 규칙 있음`으로 판정되는가**
  - 파일럿 M15(g Vg15)·M16(g Vop1)은 입력 넷이 서로 다른 병렬 셀이다. 443 블록 국소 모델은 "블록 입력 넷을 단위 신호로 구동"하는 단일 입력 모델이라, J3의 두 선택 모두에서 입력 넷이 둘인 블록이 되고 계산 규칙이 정의되지 않는다(A1).
  - sf opamp M21/M22는 CD 버퍼다. 419는 이득 블록 DAG만 다루므로, 버퍼 블록 두 사슬(M18→M22, M19→M21)이 vout에서 합류하는 경우는 `계산 규칙 있음`/`기록만` 어느 쪽인지 정의가 없다(A2).
- **(c) 전환기 해석이 DF-26·IC11·U-26 담당 Phase와 순환 없이 맞는가**
  - 기존 4개 회로: 전환기 이름 집합 → Phase 4에서 U-26(a)와 DF-19·26로 교체. 순환 없음.
  - 신규 회로: 6a 착수 조건 U-26(b)와 GB0 필수 게이트가 맞는다.
  - 문제는 IC11 하나다(A3).
- **(d) IC11 담당 Phase 4가 DEC-60 구현 Phase와 맞는가**
  - DF-19·DF-26(Phase 4)과는 맞는다.
  - 그러나 IC11 test가 요구하는 agnd 3레일 회로는 신규 두 회로뿐이다. 이 회로들의 `supply_nets`는 U-26(b) 6a이고, `SPECS` 이관은 "DEC-60 구현 뒤"(113, 877)다. Phase 4 안에서는 IC11 test를 채울 수 없다(A3).

## 2. 신규 회로 사실 대조

| plan.md:줄 | 서술 | 실측 | 판정 |
|---|---|---|---|
| 111 | library 7개 | 7개(+ `_TEMPLATE`) | 일치 |
| 113 | agnd 레일 두 회로 이관은 DEC-60 뒤, `two_stage_ota_sf`는 사이징 착수 시 | spec 기록 일치 | 일치 |
| 318 | sf opamp 순수 follower M18/M19/M21/M22 | 네 소자 모두 drain이 레일(vss/vdd)이고 source가 신호 | 일치 |
| 845 J12 | M1/M2 차동쌍, R1a/b/c 3조, Cc Y–agnd(Miller 아님), 출력 캐스코드 M9/M10·M15/M16, 버퍼 M17~M22, IBias, vdd/vss/agnd. pushpull CL vout–agnd | 모두 일치 | 일치 |
| 877 U-25 | sf opamp 수치 전부, pushpull vin DC agnd·CL·Rout·전력·대역폭 보고, two_stage_ota_sf 상속 + CL 3 pF@vout + Rout ≤ 1 kΩ, 감지 vout | `_paper_target_spec` 3개와 `run_harness.py:112` CL 3e-12 모두 일치 | 일치 |
| 736 DF-26 | sizing_recipe 3882~3883, stick_diagram 3147 | 일치 | 일치 |
| 751 I-A14 | "사용자 확정 정정이 WP-08 일괄 반영 **대기 중**" | 작업 트리 two_stage_ota.topology.json의 M1/M2 gate 이미 교체(커밋 전) | **불일치(A7)** |
| 815 7b DoD | 단독 버퍼와 opamp 내장 버퍼(M17~M22) 사이징 결과 대조 | 내장 버퍼의 bias gate N5·N13은 신호 경로 소자(M5.d/R1a, M13.d/R1c)가 붙은 넷이다. 단독 버퍼의 VPB1·VNB1은 gate에만 붙은 교류접지다 | 전제 불일치(A6) |

## 3. 새 문제

| # | 분류 | 심각도 | plan.md:줄 | 내용 | 수정 제안 문장 |
|---|---|---|---|---|---|
| A1 | 모순 | 높음 | 419, 443, 836(J3), 843(J10) | 419·J3는 병렬 CS(M15/M16)가 "어느 선택에서도 한 블록 안의 병렬 셀"이라 `계산 규칙 있음`이라고 한다. 그러나 두 셀의 입력 넷이 다르다(M16.g = Vop1, M15.g = Vg15, 그 사이는 pass M9a/M9b). J10 기본안(독립 버퍼 블록)을 따르면 M15 입력은 버퍼 블록 출력이고, J3가 Vg15를 stage1 출력으로 정하면 M16 입력은 stage1 내부 노드다. 어느 쪽이든 입력 넷이 둘인 블록인데, 443 블록 국소 모델은 "블록 입력 넷은 단위 신호로 구동"하는 단일 입력 모델이다. 계산 규칙이 없는 것을 `계산 규칙 있음`으로 선언한 셈이고, 이는 N9.2-8(열린 질문 금지)과도 충돌한다. 파일럿 7b 할당의 전제다 | 443에 추가: "병렬 셀의 입력 넷이 여럿이면, 그 입력 넷들을 잇는 pass·CD 구간을 블록 노드 집합에 넣어 입력 넷을 하나(분기점)로 만든다. 이 구간은 J10의 독립 버퍼 블록 예외다." 843 J10 기본안에 "병렬 셀 입력을 잇는 pass·CD 구간은 뒤 이득 블록에 흡수"를 넣고, 836 J3의 "한 블록 안의 병렬 셀" 뒤에 "(N3.8 다중 입력 흡수 규칙)"을 붙인다 |
| A2 | 누락 | 중간 | 90, 419, 845(J12) | 419의 `계산 규칙 있음` 판정은 이득 블록만 다룬다. sf opamp와 `pushpull_follower_buffer`의 버퍼는 Y(또는 vin)에서 두 follower 사슬로 갈라져 vout에서 합류한다. 버퍼 블록 = "CD·pass로 끝나는 구간"(90)이라 사슬마다 블록이 되면 버퍼 블록 사이 합류가 생기는데, 이것이 `기록만`인지 한 블록인지 규칙이 없다 | 90 버퍼 블록 정의에 "한 입력 넷에서 갈라져 같은 출력노드로 합류하는 follower 사슬 묶음은 버퍼 블록 하나(블록 노드 집합에 중간 노드 포함, `계산 규칙 있음`)"를 넣는다 |
| A3 | 순환(시점) | 높음 | 646(IC11), 792, 794, 878(U-26 (b)), 113, 877 | IC11(Phase 4 활성)은 레일 선언 (vdd 1.8 / vss 0 / agnd 0.9)과 (+0.9 / −0.9 / 0)에서 VGS·VDS·VSB·gm_id·W·metric 불변을 요구한다. agnd 3레일 회로는 신규 두 회로뿐인데, 이 회로들의 `supply_nets`는 U-26(b) **6a**이고 `SPECS` 이관은 "DEC-60 구현 뒤"(113, 877)다. 게다가 전환기 이름 집합에는 agnd가 없다(DF-26). 따라서 Phase 4에서 IC11 test를 만들 수도 PASS할 수도 없다 | 646 test를 "Phase 4: 기존 2레일 회로(파일럿)를 (vdd 1.8 / gnd 0)와 (+0.9 / −0.9)로 원점 이동해 불변. agnd 3레일 케이스는 신규 회로 `supply_nets`·이관 뒤(6a 이후) 추가"로 나누거나, 878 U-26(b) 시점을 "Phase 4"로 당기고 792 Phase 4 범위에 "신규 agnd 회로 SPECS 이관"을 넣는다 |
| A4 | 모호 | 중간 | 85, 304, 306, 309 | 루프 탐지 엣지 "전류 구동 source->drain"이 노드 구동 종류(85) 기준인지 셀 분류(306 우선순위) 기준인지 정해지지 않았다. 차동 전달 뷰에서 M1a/M1b는 CS이므로 셀 기준이면 Vx → N1a2a 엣지가 없고, 309 예시의 CMFB 루프(Vx → M1a/M1b CG)를 전달 뷰 그래프에서 찾지 못한다. 그러면 6a DoD의 루프 탐지 대조(J11)가 어긋난다 | 304 엣지 정의를 "source 노드가 85의 전류 구동 노드이면 셀 분류와 무관하게 source->drain 엣지를 둔다(루프 탐지 그래프 한정)"로 쓰고, "파일럿 CMFB 루프가 이 그래프에서 탐지돼야 한다"를 318 (iii) 측정 항목에 넣는다 |
| A5 | 잔여 | 중간 | 304 | pass 셀을 "방향 없는 2단자, 폐경로 방향 엣지로 세지 않음"으로 두면, 역병렬 pass 쌍의 내부 왕복만이 아니라 **pass를 한 번 통과하는 진짜 되먹임 루프**(floating battery를 거쳐 출력단 게이트로 돌아오는 경로만 있는 회로)도 조용히 사라진다. 파일럿은 M16 경로가 따로 있어 영향이 없다 | "pass 묶음은 한 방향 통과 1회를 허용하고, 같은 pass 묶음 안에서의 왕복(역병렬 쌍 내부 순환)만 폐경로에서 제외한다"로 바꾼다 |
| A6 | 모순(전제) | 중간 | 815(7b DoD), 845(J12) | 7b DoD는 같은 버퍼 스펙에서 단독 버퍼와 opamp 내장 버퍼(M17~M22)의 사이징·극점·출력 구동 판정을 대조한다. 그런데 내장 버퍼의 전류원 gate N5·N13은 신호 경로 소자가 붙은 넷(M5.d·R1a, M13.d·R1c)이라 교류접지가 아니고, 단독 버퍼의 VPB1·VNB1은 교류접지다. 두 결과가 같다는 기대가 구조상 성립하지 않을 수 있으며, J12의 "같은 구조인지"도 아직 미결이다 | 815 항목을 "J12에서 두 버퍼를 같은 구조로 ratify한 경우에 한해, 내장 버퍼의 N5·N13을 교류접지로 고정한 블록 국소 모델 결과와 단독 버퍼 결과를 대조(차이는 bias 넷 신호 결합으로 보고)"로 바꾼다 |
| A7 | 사실 불일치 | 중간 | 751(I-A14) | plan은 two_stage_ota 극성 정정이 "WP-08 일괄 반영 대기 중"이라고 쓰지만, 작업 트리 `two_stage_ota.topology.json`은 이미 M1/M2 gate가 교체돼 있다(커밋 전). topology connectivity 변경은 승인 기록(U-16, EL4 대상)이 필요하고, S0 지문과 `smallsignal_gain_db`·오프셋 부호 기대값(DEC-40)에 영향이 있다 | 751을 "반영(2026-09-15, 승인 기록 id). 영향 조사(`smallsignal_gain_db` 부호, `input_referred_offset` 쌍)는 Phase 4 첫 실행 비교표에서"로 갱신하고, topology 변경은 승인 기록과 함께 plan과 별도 커밋으로 나눈다(또는 plan 서술대로 되돌린다) |
| A8 | 누락 | 낮음 | 809(Phase 4 DoD), 792 | 792에서 IC11을 Phase 4에 활성으로 넣었지만 Phase 4 DoD(809)에 IC11 PASS가 없다 | 809에 "IC11 PASS(A3 분할 시 2레일 케이스)"를 추가한다 |
| A9 | 과잉(N0.1 중복) | 낮음 | 729(DF-19), 736(DF-26) | DF-19와 DF-26이 같은 위치(`_DEFAULT_RAIL_HI/LO`, `_RAIL_NETS`)·같은 Phase·같은 변경 단위를 가리키는 한 결함이다 | DF-26을 DF-19 비고로 합친다("agnd를 레일로 읽지 못함 포함"). IC11·U-26 참조는 DF-19로 바꾼다 |

## 4. 집계와 판정

- 지난 지적 5건: N1·N3·#9·N4는 해소, N2는 부분 해소(A1로 이어짐)
- 새 문제 9건: 막음 0, 높음 2(A1, A3), 중간 5(A2, A4, A5, A6, A7), 낮음 2(A8, A9)
- 신규 회로 사실은 J12·U-25·318·113·DF-26 모두 실측과 일치. I-A14만 작업 트리와 불일치(A7)

**커밋 불가.** 문서만으로 풀리는 높음 2건을 먼저 고쳐야 한다: A1(병렬 셀 한 블록을 `계산 규칙 있음`으로 선언했지만 입력 넷이 둘인 블록 모델이 없다. 파일럿 7b 할당의 전제)과 A3(IC11 Phase 4 활성에 필요한 agnd 회로 데이터가 6a 이후에야 생긴다). A7은 plan 결함은 아니지만, 작업 트리의 topology connectivity 변경이 승인 기록 없이 plan과 함께 커밋될 위험이라 커밋을 나눌 것을 권한다.
