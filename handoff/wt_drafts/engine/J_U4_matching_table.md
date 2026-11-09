# J-U4 대조표 -- 레이아웃 matching 분류 (SYNTHESIS Q8 (i)(iii), 2026-10-07 / 2026-10-08 갱신: J14 1번 소비 블록 세분)

**갱신(2026-10-08)**: 사용자 ratify J14 1번(파일럿 소비 블록 미러 2묶음 분할)을 위상 무관 규칙 '소비 블록 세분'으로 구현했다
(브랜치 `ng-match-split`). 파일럿의 해당 행은 **[ratified]**, 나머지 행은 여전히 확인 요청이다.

**확인 요청(회로 해석)**: 아래는 새 블록 `s1_matching_groups`(브랜치 `ng-graph-match`, `gmid_engine/graph/matching_groups.py`)가
9회로에서 실제로 낸 값이다(작성자 실행값, 기대값 아님). 행마다 맞음/틀림을 표시해 주시면 ratify 기록으로 옮긴다.
규칙 정의 원문은 `gmid_engine/graph/CONTRACT.md` 4.5a. supplies_v 는 계약 7절과 같다(분류는 supplies 를 읽지 않는다).

## 0. 규칙 요약 (모두 connectivity 만으로 판정, 회로·소자 이름 미사용)

- **블록** = DC 전도 그래프에서 레일을 지운 연결 성분(레일 아닌 넷으로 이어진 가지 묶음).
- **바이어스 넷 B** = '바이어스 블록'의 넷. 바이어스 블록 = 입력 포트 넷이 없고, 블록 안 diode 아닌 MOS 의 gate 가 모두
  교류접지(레일·gate 전용 외부 넷) 또는 다른 바이어스 블록의 넷인 블록(최대 고정점).
- **루프 신호 넷 L** = 영향 그래프(MOS g→d·g→s·s→d, 저항 양방향, 커패시터·이상원 제외)의 강연결 성분 중 MOS 엣지를 품고
  가지 하나 안에서 닫히지 않는 성분의 넷. (Miller 커패시터로만 닫히는 고리, self-cascode diode 같은 가지 안 고리는 제외)
- **소비 소자** = 같은 (kind, gate, source) 묶음(gate 비레일)에 diode 가 있을 때, diode 가 없는 블록에 있는 diode 아닌 멤버.
  - gate ∈ B -> 소비 소자 `bias_distribution`(레이아웃 matching 제외, 근거 기록) / gate ∈ L -> `feedback_shared`(제외, 기록)
  - 남은 diode 쪽 멤버가 2개 이상이면 mirror, **같은 블록에 모인 소비 소자끼리 2개 이상이면 아래 '소비 블록 세분'**
  - **소비 블록 세분**(J14 1번): 그 블록의 소비 소자 중 drain = derived 차동쌍 공통 source -> 꼬리(diode 와 비율 미러
    `tail_ratio`, bias_distribution 에서 빠짐) / drain = diode 넷 -> bias_distribution 만(그룹 없음) / drain 이 대응 넷 짝인 두 소자 ->
    대칭쌍 mirror(`consumer_symmetric`) / 셋 다 해당 없으면 옛 그대로 블록 전체 `consumer_block`.
  - **대응 넷 짝** = derived 2멤버 차동쌍의 두 drain 에서 시작해, 같은 소자 구성(segment 별 (분류, kind))의 DC 가지 두 개가
    짝 넷을 같은 자리에 가지면 나머지 자리 넷끼리 짝을 더한다(고정점, 레일 제외, 충돌 넷 제거).
  - gate 가 B·L 어디에도 없으면(신호가 실린 diode 넷을 다른 블록이 읽는 신호 미러) 묶음 전체 mirror(`signal_cross_block`)
- **차동쌍(diff_pair)** = 같은 (kind, 비레일 source) 묶음에서 바이어스 형제(DC 역할 diode/bias, gate 교류접지, 또는 gate 가
  자기 DC 가지 위 넷 = 자기 가지 전류가 gate 를 정하는 바이어스 다리)를 먼저 빼고, 남은 gate 가 2개 이상. 남은 멤버 2 -> derived.
- **branch_symmetric** = derived 그룹(mirror·diff_pair·찾은 branch_symmetric)의 각 멤버 drain 위에 source 를 둔 같은 kind MOS 를
  gate 별로 모아 source 가 2개 이상이면 새 그룹(고정점까지).
- 레이아웃에는 derived matching 그룹만 전달, 제외 기록(disposition)은 status `proposed` 로 결과에 남긴다.

## 1. 회로별 결과

### common_gate_amplifier
- matching 그룹 0, 제외 기록 0 (같은 gate 묶음·같은 source 차동 후보 없음).

### current_reuse_telescopic_ota (파일럿)
| kind | members | 근거(nets) | 비고 |
|---|---|---|---|
| diff_pair | M1a, M1b | source Vx, gate Vip/Vim | 옛 규칙: +M58 3소자 review_needed |
| diff_pair | M4a, M4b | source Vy, gate Vip/Vim | 옛 규칙: +M63 3소자 review_needed |
| diff_pair | M37a, M37b | source Ncmfb_tail, gate Voc/Voc_des | CMFB 비교쌍 |
| branch_symmetric | M2a, M2b | gate Vbias2, M1a/M1b 위 | |
| branch_symmetric | M3a, M3b | gate Vbias3, M4a/M4b 위 | |
| mirror (consumer_symmetric) | M10, M19 | gate Vbias4, drain Vop1/Vom1 (대응 짝) | **[ratified J14-1]** 출력단 좌우 대칭쌍 |
| mirror (consumer_symmetric) | M8, M17 | gate Vbias1, drain Vg15/Vg25 (대응 짝) | **[ratified J14-1]** class-AB 좌우 대칭쌍 |
| mirror (tail_ratio) | M38, M5, M66 | gate Vbias4, M5 drain Vy = 차동쌍 M4a/M4b 공통 source, M38 drain Ncmfb_tail = CMFB 차동쌍 M37a/M37b 공통 source | **[ratified J14-1 (M5) / 판단 7 2026-10-08 (M38)]** 꼬리 -- diode 와 비율 미러 |
| mirror (tail_ratio) | M6, M18_bg | gate Vbias1, M6 drain Vx = 차동쌍 M1a/M1b 공통 source | **[ratified J14-1]** 꼬리 -- diode 와 비율 미러 |
| bias_distribution | M10, M12, M19, M21, M68 | Vbias4 / diode M66 | M68(drain Vbias2 = diode M57 넷) **[ratified J14-1]** |
| bias_distribution | M13, M17, M22, M60, M61, M8 | Vbias1 / diode M18_bg | M61(drain Vbias3 = diode M64 넷) **[ratified J14-1]** |
| mirror (tail_ratio) | M36a, M7 | gate Vcmfb (CMFB 루프 신호 넷), M7 drain Vx = 차동쌍 M1a/M1b 공통 source | **[ratified 2026-10-08]** CMFB 구동 꼬리 -- diode 와 비율 미러(옛 분류 feedback_shared) |
| bias_sibling | M58 | source Vx, gate Vbias2 | gate 가 자기 가지(Vx–gnd: M58, M57, M68) 위 |
| bias_sibling | M63 | source Vy, gate Vbias3 | gate 가 자기 가지(Vy–vdd: M63, M64, M61) 위 |

M57/M58(같은 gate, 쌓임, seed 없음) -> branch_symmetric 0 (AGI §6.3 과 같음).
대응 넷 짝: N1a2a↔N1b2b, N3a4a↔N3b4b, Vom1↔Vop1, Vg15↔Vg25, Vcmfb↔N36b. (M10/M19·M8/M17 이 bias_distribution 기록에도 남는
것은 'diode M66/M18_bg 와의 비율 관계 제외'라는 뜻이고, 서로의 대칭쌍 matching 은 위 그룹이다.)

### folded_cascode
| kind | members | 근거 | 비고 |
|---|---|---|---|
| diff_pair | M1, M2 | source tail | |
| mirror (whole) | M9, M10 | gate Vg9 | 같은 블록 |
| mirror (consumer_symmetric) | M3, M4 | gate vb1 (diode MP), drain X/Y (차동쌍 drain 짝) | 접힘 전류원 대칭쌍 -- 멤버는 이전과 같고 rule 만 바뀜 |
| branch_symmetric | M5, M6 | gate bias3, M4/M3 위 | M3/M4 mirror 를 seed 로 |
| branch_symmetric | M7, M8 | gate Vg7, M9/M10 위 | M7 은 diode(캐스코드 미러 diode 쪽) |
| bias_distribution | M3, M4 | vb1 / diode MP | 바이어스 블록 {MN, Ibg, MP} |
| mirror (tail_ratio) | M11, MN | gate vb2, M11 drain tail = 차동쌍 M1/M2 공통 source | **[ratified 판단 7, 2026-10-08]** 꼬리 -- diode 와 비율 미러 |

### ngcc_3stage_ff
| kind | members | 근거 | 비고 |
|---|---|---|---|
| diff_pair | M1, M2 | source TAIL | |
| mirror (signal_cross_block) | M3, M4, M6B | gate ND (diode M3) | **판단 2**: M6B 는 다른 블록(NX)의 feedforward 탭 |
| mirror (signal_cross_block) | M6A, M7 | gate NX (diode M6A) | **판단 2** |
| mirror (signal_cross_block) | M9, M10 | gate NP (diode M9) | **판단 2** |
| mirror (whole) | M8, M14 | gate V1, source gnd (diode 없음) | **[ratified 2026-10-08 J14]** 비율 matching 그룹 -- NGCC 조건 gmf2 = gm2 (gm14 = gm8), 불일치 시 우반면 영점이 남음. 세분 규칙 대상 아님(diode 없음) -> 결과 불변 |
| mirror (whole) | M0, M12, M5 | gate VBP (외부 바이어스) | **판단 4** |

### nmcnr_amplifier
| kind | members | 근거 | 비고 |
|---|---|---|---|
| diff_pair | M102, M103 | source NodeTail | |
| mirror (whole) | M108, M109 | gate NodeM1 | |
| mirror (whole) | M104, M105 | gate VB2 (외부) | |
| mirror (signal_cross_block) | M203, M204 | gate NodeC (diode M203) | **판단 2**: 2단 신호 미러(블록 다름) |
| branch_symmetric | M106, M107 | gate VB3, M104/M105 위 | |

### pushpull_follower_buffer
- matching 그룹 0, 제외 기록 0.

### sf_pushpull_output_opamp
| kind | members | 근거 | 비고 |
|---|---|---|---|
| diff_pair | M1, M2 | source TAIL | |
| mirror (whole) | M6, M9, M17 | gate N5 (diode 없음, M6 은 M5 와 self-cascode diode) | **판단 3** (J-U3-c review 묶음) |
| mirror (whole) | M8, M11 | gate N7 | **판단 3** |
| mirror (whole) | M14, M16, M20 | gate N13 | **판단 3** |
| branch_symmetric | M5, M10 | gate N1, M6/M9 위 | |
| branch_symmetric | M7, M12 | gate N2, M8/M11 위 | |
| branch_symmetric | M13, M15 | gate N12, M14/M16 위 | |
| mirror (tail_ratio) | M3, M4 | gate NB, M3 drain TAIL = 차동쌍 M1/M2 공통 source (diode M4, 바이어스 블록 {IBias, M4}) | **[ratified 판단 7, 2026-10-08]** 꼬리 -- diode 와 비율 미러 |

### two_stage_ota
| kind | members | 근거 |
|---|---|---|
| diff_pair | M1, M2 | source CS |
| mirror (whole) | M3, M4 | gate D3 |
| mirror (whole) | M5, M7 | gate bias (외부) -- **판단 4** |

### two_stage_ota_sf
| kind | members | 근거 |
|---|---|---|
| diff_pair | M1, M2 | source CS |
| mirror (whole) | M3, M4 | gate D3 |
| mirror (whole) | M5, M7, M9 | gate bias (외부) -- **판단 4** |

## 2. 사용자 판단이 필요한 점 (작성자 기본안 = 위 결과)

1. ~~같은 블록 소비 소자끼리 mirror~~ -> **2026-10-08 ratify(J14 1번)**: 파일럿 2묶음 분할을 '소비 블록 세분'으로 반영. folded
   M3/M4 는 같은 규칙에서 대칭쌍(`consumer_symmetric`)으로 남는다 -- 이 결과 확인 요청.
2. **신호 미러가 블록을 넘는 경우**(ngcc ND·NX·NP, nmcnr NodeC): diode 넷이 바이어스 넷이 아니고 루프 넷도 아니어서 묶음 전체를
   mirror 로 두었다(승인 문언의 '소비 소자'를 'diode 가 만든 바이어스 노드를 읽는 소자'로 읽음). 이것들을 bias_distribution 처럼
   제외해야 하는지.
3. **diode 없는 같은 gate 묶음**(sf 3묶음; ngcc {M8, M14} 는 2026-10-08 ratified -- mirror(whole) 유지): 분류 규칙은 diode 가 있는 묶음에만 건다 -- 이 4묶음은 J-U3-c 에서
   이미 review 대상이며 mirror 로 남았다. sf 3묶음은 M5/M6 등 self-cascode diode 를 기준으로 하는 미러로 보인다.
4. **외부 바이어스 gate 묶음**(two_stage M5/M7, two_stage_sf M5/M7/M9, ngcc M0/M12/M5, nmcnr M104/M105): diode 가 회로 밖이라
   bias_distribution 규칙이 걸리지 않고 mirror 다. 서로 다른 블록의 꼬리·출력 전류원을 matching 할지.
5. **feedback_shared 정의**: 커패시터를 빼서 Miller 보상 고리는 루프로 보지 않는다(nmcnr NodeC·ngcc NP 가 feedback 으로 잡히지
   않는 이유). 커패시터 CMFB(스위치드 커패시터 등)는 이 정의로 못 잡는다 -- 9회로에는 없음.
6. **차동쌍 '신호 gate' 조건**(G5-03 의 입력 포트/대칭 대응 gate 정확히 2)은 U5(대칭·뷰)가 없어 넣지 않았다. 바이어스 형제 제외만
   으로 9회로 차동쌍은 모두 2멤버 derived 다.
7. ~~혼자인 꼬리 소비 소자~~ -> **2026-10-08 ratify(판단 7, "A는 나도 동의해")**: 블록에 혼자인 꼬리도 tail_ratio. 파일럿 M38,
   folded M11, sf M3 반영. 남았던 질문(feedback_shared 묶음의 꼬리 M7)도 **2026-10-08 결정("꼬리 비율 미러 {M36a, M7}로 분류")**으로
   해결 -- 꼬리 규칙을 루프 신호 gate 묶음에도 건다. 그 결과 9회로 feedback_shared 기록은 0건(규칙은 꼬리 아닌 소비 소자용으로 남음).

## 3. 일반성 측정 (library 밖, 작성자 측)

- topogen 합성 3종(syn_cs_load·syn_diffpair5·syn_follower): diode 바이어스 블록 -> 다른 블록 전류원이 있어 bias_distribution
  1건씩. branch_symmetric·feedback_shared·bias_sibling 0 (그 구조 없음 = 무동작). syn_cascode 는 이상 전압원으로 기존과 같이 정지.
- 손 변형: diffpair5 꼬리에 M58/M57형 다리 추가 -> diff_pair 유지 + bias_sibling 1 + 그 다리의 같은 gate 쌍은 branch_symmetric 0;
  NMOS 캐스코드 2단 -> branch_symmetric 2(재귀 전파).
- 이름 치환 3벌·순서 섞기 3벌·극성 뒤집기: 분류가 치환표를 따라감 42/42, 단 복제: 모든 kind 수 정확히 2배.
- (2026-10-08 세분) 위 합성·손 변형 6종 결과는 세분 전후 완전히 같다(소비 블록 2개 이상 묶음이 없음 = 무동작). 세분이 실제로
  걸리는 합성 변형 syn_dp_split(NMOS 차동쌍 + PMOS 부하 Pa/Pb(diode Pr 바이어스 블록) + NMOS 꼬리 Ye·접힘 싱크 Na/Nb(diode Nr
  바이어스 블록)): {Pa, Pb}·{Na, Nb} consumer_symmetric, {Nr, Ye} tail_ratio. 변형 불변량 7종 회로 49/49 통과, 복제 2배.
- (2026-10-08 판단 7) 혼자인 꼬리 반영 뒤: syn_diffpair5 와 손 변형 3종(꼬리 형제·캐스코드 2단·둘 다)의 꼬리 Ye 가 bias_distribution ->
  {Ye, Yf} tail_ratio(바이어스 diode 를 쓰는 차동쌍 꼬리 구조가 있음). 차동쌍이 없는 syn_cs_load·syn_follower 는 불변(무동작).
  변형 불변량 49/49, 복제 2배.
- (2026-10-08 M7 결정) 꼬리 규칙을 feedback_shared 묶음까지 넓힌 뒤 합성 회로·손 변형 7종 결과는 판단 7 직후와 같다(합성에는 루프
  신호 넷이 없음). 9회로에서 바뀐 것은 파일럿 M7 하나.
