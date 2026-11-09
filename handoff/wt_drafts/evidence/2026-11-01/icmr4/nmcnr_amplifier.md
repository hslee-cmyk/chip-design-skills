# nmcnr_amplifier -- 동작 조건·정지 원인·ICMR 기능 기준 권고 (독립 회로 분석, 2026-11-01)

- 대상: `skills/analog-gmid-design/assets/library/nmcnr_amplifier.{topology,sizing_spec}.json` (master `08048939`), 원문 Leung·Mok·Ki 1999 ICECS -- 로컬 PDF `skills/analog-gmid-design/assets/library/sources/nmcnr_amplifier__leung_1999/source.pdf` (웹: IEEE Xplore 유료, 공개 링크·문서 번호 없음 -- paper.md:5).
- 쓰기 범위: 이 파일 + `nmcnr_amplifier_files/`(스크립트·로그). 저장소·계획·topology·spec·git 쓰기 0. 엔진·SPICE는 실행만, library 경로 그대로(u13_real 미사용). 출력 TEMP: `%TEMP%/icmr4_nmcnr_{s2_a6lx1,e7lkb371,f5dhmf38}`(엔진), `%TEMP%/icmr4_nmcnr_spice`(SPICE).
- 주의(자기 보고): `assets/topology_to_markdown.py`가 실행 때 `assets/library/nmcnr_amplifier.topology.md`(미추적)를 저장소에 썼다 -- 즉시 `nmcnr_amplifier_files/topology_connectivity.md`로 옮겼다(저장소 상태 원복 확인, git status 해당 파일 없음). 다른 회로 agent도 같은 도구를 쓰면 같은 일이 생긴다.

## 1. 토폴로지 해석 (연결 + 원문만, analog-grammar 태그 미사용) -- 확신도 높음

connectivity 표 = `nmcnr_amplifier_files/topology_connectivity.md`. 원문 Fig. 3 (PDF p.4 = 저널 p.602 왼쪽 위; topology `source_manifest`의 'p.601'은 쪽 오기 -- paper.md:6) 를 잘라 net 단위로 대조(`nmcnr_amplifier_files/fig3_crop.png`): 15 MOS·Cm1·Cm2·Rm·CL 연결 모두 일치, RL 25 kΩ은 그림에 없고 Table 1 측정 부하(p.602 'loading condition 100pF//25kΩ').

| 단 | 소자(net) | 해석 | 근거 |
|---|---|---|---|
| 1단 | M101(pmos 꼬리, VB1) → NodeTail → M102(Vin_n)/M103(Vin_p) pmos 입력쌍 → NodeF1/F2 접힘 노드 ← M104/M105(nmos 싱크, VB2) / M106/M107(nmos 캐스코드, VB3) → NodeM1/NodeM2 ← M108(diode)/M109 pmos 단순 거울 | PMOS 입력 folded cascode, 단일 출력 NodeM2, 부하 = 비캐스코드 pmos 거울 | 원문 p.601(PDF p.3) 5절 'first ... gain stage are implemented by M101-M109'; 연결표 NodeF1·F2·M1·M2 행 |
| 2단 | M201(pmos CS, gate NodeM2) → NodeC ← M203(nmos diode) → M204 거울 → NodeS2 ← M202(pmos 전류원, VB4) | 비반전 단(NodeM2↑ → I201↓ → I204↓ → NodeS2↑) | 'M201-M204' 같은 쪽 |
| 3단 | M301(nmos CS, gate NodeS2) / M302(pmos 전류원, VB5) → Vout | 반전 출력단 (A 급) | 'M301-M302' 같은 쪽 |
| 보상 | Cm1(NodeM2–NodeCM), Cm2(NodeS2–NodeCM), Rm(NodeCM–Vout) | 원문 structure 4: 두 Miller C의 공통 노드 뒤 null 저항 하나, Rm = 1/gm3 이면 RHP 영점 제거 | p.600(PDF p.2) 'structure 4 ... setting Rm=1/gm3' |
| 부호 | Vin_p → NodeM2 반전, 2단 비반전, 3단 반전 → Vin_p 비반전 입력 | NMC 조건(바깥 고리 A2·A3 < 0, 안 고리 A3 < 0) 충족 | 위 KCL 유도, topology ports 주석의 2026-09-17 소신호 확인과 일치 |
| bulk | 미선언 → DEC-61·O-188 기본(nmos = vss, pmos = vdd) | 원문 그림은 3단자 기호(근거 없음) | — |

**입력 공통모드(x)가 움직일 때 기능이 무너지는 순서(물리 유도, DC 양 -- 원칙 3):**
- **위로**: M101 포화 끝 `x_hi = V_DD − V_DSAT,101 − V_SG,102(x)` (V_SG에 body 효과 포함, bulk = vdd). 넘으면 M101 triode → 꼬리 전류 감소 → gm1 감소(약반전이면 gm1 ∝ I) + 접힘 가지 전류 증가(I106 = I104 − I102)로 ro107·ro109 감소 → 증분 DC 이득이 매끄럽게 떨어짐. 더 올라가면 M102/M103 차단 → servo 붕괴.
- **아래로**: M102 포화 조건 `V_F ≤ x + |V_tp|` → `x_lo = V_F − |V_tp|` (보통 < 0) → **레일(vss)에서 잘림**. V_F는 VB3 − V_GS,106로 x와 무관, M104 VDS도 x와 무관 → 레일까지 이득 평탄.
- 출력은 servo로 묶여 2·3단은 x와 무관.

**SPICE 실측(AI 손계산 gm/ID 설계 9점 R1~R6 -- 측정 매개변수, 설계 권고 아님; `spice_ref.py`, `spice_ref.jsonl`, `analyze_ref.jsonl`, `gain_drop_at_region_end.jsonl`)**: 9/9 설계에서 위 끝 첫 영역 이탈 = **M101**, 아래 끝 = **레일 0 V**(이득 변화 < 0.3 dB), 영역 끝에서 이득 저하 = **1.08~2.84 dB**(9/9). 유도와 일치 -- 판정 **맞음**.

| 설계 | L | 입력쌍/꼬리 gm/ID | x0 | G(x0) dB | 영역 창 위 끝(M101) |
|---|---|---|---|---|---|
| R1b | 1 µm | 15 / 10 | 0.3 | 122.7 | 0.582 V |
| R2b | 1 µm | 24 / 18 | 0.9 | 126.2 | 1.094 V |
| R4 | 1 µm | 28 / 24 | 0.9 | 128.1 | 1.197 V |
| R5 (입력쌍 bulk = source, 정보용) | 1 µm | 24 / 18 | 0.9 | 126.3 | 1.107 V |
| R6 | 0.5 µm | 24 / 18 | 0.9 | 110.1 | 1.153 V |
| R3 | 0.25 µm | 15 / 10 | 0.3 | 79.7 | 0.780 V |
| R1 | 1 µm | 15 / 10 | **0.9** | 101.7 | **x0에서 이미 M101 triode** |

→ sky130 pfet_01v8(L = 1 µm에서 V_SG ≈ 1.0 V @ gm/ID 15) 입력쌍은 x = agnd 0.9 V를 쓰려면 입력쌍 약반전(gm/ID ≳ 24)·꼬리 V_DSAT 작게가 **필요**하고, follower 범위 끝 1.15 V(O-154 Q4)까지 포화를 지키려면 R4급(≈ 28/24)이 필요하다(R2b는 56 mV 모자람). bulk = source 묶기는 +13 mV뿐(R5) -- 해법 아님.

## 2. 엔진 정지 원인 (master HEAD 실측) -- 분류

실행: `nmcnr_amplifier_files/run_engine.py`(공개 진입점 run_stage_a → run_stage_b → build_kernel_context → build_search_context → find_front, library 경로 그대로), 기록 `engine_run.jsonl`, 아카이브 `%TEMP%/icmr4_nmcnr_*/s3/*/runs.jsonl`.

| 실행 | E_B | 결과 | 끝점 SLSQP 정지 문자열 |
|---|---|---|---|
| 1 (test 관례 상자, E_B 40) | 40 | 단계 A ok·B ok, front 0 | power·area 모두 `start_eval_budget`, accepted 0 (층 0이 이미 kernel 66회 > 40) |
| 2 | 1000 | front 0, kernel 470 | `slsqp_4` ×2 (aborts candidate_failure 4·3) |
| 3 (spec 상자 그대로, E_B 유도 `derived_once:floor(B/median_t_eval)` = 1119, B 300 s) | 1119 | front 0, kernel 595, wall 138 s | `slsqp_4` ×2 |

공통 사실: `l_search stops: []`(L-b 안 돎), **평가 3회 실행 전부 L 칸 0 (L ∈ [0.15, 0.18] µm, `cells` 전부 0)**, `layer0_minimal`의 `refinements_out_of_scope`에 'GB4 gain 표(DEC-71 (3)(6)·DEC-73)'. 봉인점 이득 44.06 dB(o206 `o206_compare.txt` 3행, SPICE 41.85 dB), 봉인 평가의 gain 행 정규화 위반 c 최대 −1.44 ~ −1.60(정의 미확인 -- 값 환산은 안 함). 단계 B(GB4)는 1단 NodeM2 100.7 dB·2단 73 dB 'found'(`%TEMP%/icmr4_nmcnr_s2_a6lx1/out/nmcnr_amplifier.stage_b.md`) -- 물리적으로 100 dB 달성 가능(R1b 122.7 dB @ L 1 µm, R6 110 dB @ 0.5 µm; L 0.25 µm R3 79.7 dB).

**원인과 분류**
1. **엔진 결함(재작성 범위)** -- 근본 원인: 출발점 L 칸이 gain 요구로 정해지지 않고(층 0 = 봉인 여유 중심, gain→L 역산 범위 밖), 끝점 풀이(solve_eps)는 L 칸을 바꾸지 않으며, L-b는 front 점에만 돈다 → 최소 L 칸에서 100 dB가 물리적으로 불가능하면 front 0으로 끝남. 계획 LA-1 완료 조건 9 (a) 'ss 제약 선언 library 회로마다 front ≥ 1'·(b) `slsqp_4` 비율 보고(plan.md:2003) 미충족 상태 그대로. (원칙 8: as-built 인용은 재작성 범위 지목 용도만.)
2. **spec 선언 문제(이미 결정, data 미반영)** -- `swing_out_v ≥ 0.5`(spec :128-139)가 거의 모든 봉인 점에서 c ≈ −19.6으로 위반. O-154 Q3이 이 제약 삭제·출력 범위 [0.65, 1.15] V 선언으로 대체를 결정(data 커밋 = SF-1) -- L 문제를 고쳐도 이 행이 남으면 front를 막을 수 있다.
3. **spec 선언 문제(새 결정 필요)** -- ICMR 판정(icmr_v, spec :116-127)은 O-206·O-211에 따라 기능 기준 미선언 = 정의 불능. master 엔진은 아직 옛 영역 행 정의로 icmr_v를 계산(c ≈ +16.8, 통과로 셈 -- as-built, 재작성 범위 IT-2c·DE-1·SF-1).
4. **spec 정리 후보** -- `gain_ss_db`가 `constraints`(:81-92, 2026-10-13 결정)와 `pending_constraints`(:171-176, SP-4 '참고')에 동시에 있음(낡은 대기 표지).
5. topology 연결 문제: **없음**(Fig. 3과 net 단위 일치).
6. 관찰(결함 아님, 정보): 봉인점은 '타당성 확인용' 중심이라 물리 대표성이 없다 -- Vout 1.686 V(RL 31 µA, M302 V_SD 0.114 V), 입력쌍 W 1180/12129 µm·전류 76/929 µA(1:12), M101 W 45.8 mm, 모든 L ≈ 0.155 µm(o206 `o206_seal_dump.jsonl`). o206의 ICMR 위 끝(영역 행 M302 0.422 V)은 출력이 VDD 근처에 묶인 탓이라 회로 성질이 아니다.

**동작시키는 데 필요한 조치(순서)**
1. (사용자 선언) SP-2 input_dc = `{"net": "agnd"}` -- §3 근거. 출력 묶음점(servo) = agnd도 함께(§4 d-2).
2. (사용자 선언) icmr_v 기능 기준 칸 -- §3 권고 A.
3. (이미 결정, data) SF-1에서 swing_out_v 삭제 + 출력 범위 [0.65, 1.15] V, SR(O-129)·정착(O-145·O-148) spec 반영.
4. (엔진 재작성) LA-1: gain 요구에서 L 칸을 고르는 출발(DEC-71 역산) 또는 끝점 풀이 실패 시 L 칸 이동 -- 완료 조건 9 (a)(b). 이것 없이는 1~3을 해도 front 0이 남을 가능성이 높다(실측: L 칸 0에서 gain c 최대 −1.44).
5. (엔진 재작성) O-205·O-206·O-211 ICMR 창(기능 기준 함수 = DE-1 (e), graph.ss_nodal writer 선행) -- 그 전까지 ICMR 판정은 정의 불능 표지가 맞다.
6. (oracle) 최종 판정 .dc servo + 점별 .tf.

## 3. ICMR 기능 기준 권고

**기준점 x0 (권고 = 봉인점 = spec input_dc = agnd 0.9 V, 출력 묶음 = agnd 0.9 V)**: 유도 -- 원문 측정 구성은 단위 이득 follower + 0.5 V 계단(p.602 Table 1 주, Fig. 6), 사용자 결정 O-154 Q4 출력 범위 [0.65, 1.15] V '중심 agnd 0.9 V'·O-145 계단 0.65→1.15 V. follower는 V_in = V_out이므로 범위 중심의 입력 DC = agnd. 새 상수 0(supplies_v.agnd 참조), 선례 = pushpull_follower_buffer·sf_pushpull input_dc `{"net": "agnd"}`. ⚠ 물리: x0 = 0.9에서 R1(15/10)은 정의 불능(M101 triode), R2b·R4·R6은 성립 -- 엔진이 입력쌍 약반전 영역을 찾아야 한다(O-205·O-207로 LUT 정의역 안 약반전 허용).

**허용 저하 후보(대칭 비교, 증분 DC 이득 = 원칙 3·DEC-67 DC 양, 판정 꼴 = 출력 범위 (b)와 같은 '기준점 대비 허용 저하')**

| 안 | 정의 | 상수 | 물리·사용 맥락 | 실측(9 설계) | 판정 |
|---|---|---|---|---|---|
| **A (권고)** | 허용 저하 = G(x0) − `value_from_constraint: gain_ss_db` → 창 안 모든 점 G(x) ≥ 100 dB | 0 (spec gain 참조) | 원문이 정한 이 증폭기의 기능 = 'DC gain > 100dB'(p.602 Table 1, p.599 '~100dB'), follower 사용에서 정적 오차 1/A도 이 이득이 정함 → 'ICMR 안에서 선언 이득을 지킨다'(데이터시트 관례와 같은 뜻). gain spec이 바뀌면 자동으로 따라감 | 기능 끝이 영역 끝보다 0.07~0.33 V 바깥 → 영역 행(M101)이 묶음(8/8 성립 설계); G(x0) − 100 < 영역 끝 저하(1.1~2.8 dB)일 때만 기능 기준이 묶음. G(x0) < 100이면 'nominal_fail'(엔진 봉인점 o206 §2: spice 41.8 dB → nominal_fail) = gain 제약 실패와 같은 뜻 | **조건부** -- 꼴이 (b) '선언 허용 저하'를 '유도 허용 저하(기준점 의존)'로 읽는 것이라 O-211 RR-3 문언(기준점 대비 허용 저하)과 형식은 같고 뜻은 절대 하한 → ⑩ 모순 점검·SF-1 칸 꼴(value_from_constraint 허용 여부) 확인 필요 |
| B(X) | 허용 저하 = X dB (사용자 선언 상수) | 1 (새 사용자 값) | 원문에 ICMR 정의·이득-대-CM 곡선 없음(Table 1 행 목록에 ICMR 없음) → X 근거 없음. current_reuse의 −3 dB는 그 원문 Fig. 10 근거라 옮길 수 없음(원칙 13) | X = 3·6 dB: 9/9 영역 행이 묶음(기능 기준 무력); X = 1 dB: 8/9 기능이 20~50 mV 먼저 묶음 | 조건부(사용자 값 필요, 원칙 11) |
| C | 정착 ε(O-148 0.1 %)에서 A ≥ 1/ε (60 dB) | 0 | O-134 정착 최종값 = 같은 구성 DC 해라 정적 이득 오차가 정착 정의에 들지 않음 → 유도 근거 없음, gain spec보다 약함 | — | **틀림**(정의 불일치) |
| D | A ∧ B | 1 | A가 B보다 약하면 B, 강하면 A | — | B와 같은 문제 |

**원문 범위와의 대조**: 원문은 ICMR을 정의·측정하지 않음 -- 유일한 앵커는 follower 0.5 V 계단(p.602) = 사용자 결정 출력 범위 [0.65, 1.15]. 안 A + 영역 행에서 R2b ICMR = [0 (레일), 1.094] V → 폭 1.094 V ≥ icmr_v 0.5(통과)인데 **follower 범위 위 끝 1.15 V를 포함하지 못함**; R4 [0, 1.197] V·R6 [0, 1.153] V는 포함. 즉 **icmr_v '폭 ≥ 0.5 V'는 위치를 보지 않아 follower 사용 기능을 보장하지 못한다**(B87 '출력 범위 ∩ ICMR(β=1)' backlog와 같은 문제) -- §4 d-3.

**엔진 계산 꼴(안 A)**: 점별 이득 = DE-1 (e)와 같은 순수 함수(LUT 재조회 + ω→0 노달, 반복 0), 창 끝 = [x0, 영역 행 끝] 위 첫 교차 근 찾기(K_max 상한), 출력 '추정' 표지 → oracle .dc servo + .tf. 기준값 100 dB는 spec 제약 READS(새 필드·사본 0, graph 규칙 1·4).

## 4. 사용자 선언 필요 목록 (d)

1. **SP-2 input_dc** = `{"net": "agnd", source}` (권고, 유도 §3). ⚠ 입력쌍 약반전 강제.
2. **출력 DC 묶음점**: servo ICMR의 출력 = 봉인점 출력인데 지금은 엔진 자유(봉인점 1.686 V). follower 사용과 맞추려면 V_out = agnd. 선택지: (가) `node_voltage_targets_v`(CI-15) `{"Vout": {"value_v": 0.9}}` -- ⚠ 원칙 11(supplies 값 사본); (나) 노드 목표 형식에 net 참조(`{"net": "agnd"}`) 추가 = SF-1 범위 확장 -- 권고 (나), (나) 전 임시 (가)는 ⚠ 표지와 함께만.
3. **icmr_v 기능 기준 칸**(O-206·O-211): 기준점 = 봉인점(1번 선언 뒤 agnd), 허용 저하 = 안 A. 아울러 **icmr_v 의미 재검토**: '폭 ≥ 0.5 V' 대신 '창 ⊇ 출력 범위 [0.65, 1.15] V(β = 1)' 또는 icm_margin_v 꼴 -- 원래 취지와 다름(2026-10-08 Q4 (4) 결정 변경) 후보, 사용자 결정.
4. **intended_region**(CI-18) = `{}`(전 소자 포화 명시) -- 15 소자 모두 증폭·전류원·캐스코드·diode(M108·M203 diode는 항상 포화), triode·스위치 의도 소자 없음(Fig. 3). `off` 선언 소자 0 → `judged_by` 칸 불필요(O-202 (4) 해당 없음).
5. **pending_constraints gain_ss_db(SP-4) 낡은 표지 삭제**(constraints에 이미 결정 2026-10-13).
6. 이미 결정·data 대기(SF-1): swing_out_v 삭제·출력 범위(O-154), SR(O-129), 정착(O-145·O-148).
7. front_budget_s(PA-2) -- 실행 3에서 B 300 s·E_B 유도 1119로 막지 않음(참고).

## 5. 대기열 후보 (e)

- connectivity 정정 **0건**(Fig. 3 대조 일치).
- 메타데이터(connectivity 아님, 정보): topology `source`·`source_manifest.figure`의 'Fig.3 p.601' → 원문 쪽 p.602(paper.md:6이 이미 오기로 기록). 사용자 판단.

## 6. 보고 5묶음

**(1) bkit 단계표** -- 이 작업은 분석·권고(코드 변경 0): 계획 해당 없음(권고 산출물) | design 해당 없음 | 검증 안 함(작성자 ≠ 검증자 -- 권고는 독립 검증 대상) | 승인 안 함(사용자 몫) | test 해당 없음 | code 해당 없음 | 구현 gap 해당 없음 | 감사 안 함.

**(2) 단계별 점검표** -- graph 단일 정본: 권고 A = spec 제약 READS, 새 필드·cache·사본 0(설계 판단, 코드 없음) / G-10·블록 안 재계산·소비자·구조 분할: 해당 없음(코드 변경 0) / 회로 이름 0: 권고 규칙에 회로·소자 이름 없음(기준 = spec 제약·supplies 참조) / fail-closed: 미선언 = 정의 불능 유지 / 상수 발명 0: 안 A·x0 모두 참조 유도, 측정 설계 R1~R6 값은 측정 매개변수로 표지 / DC·AC 분리: 증분 DC 이득·영역 행 = DC 해석 / 계획 먼저: 형식 확장(d-2 (나))은 SF-1 계획 범위 확장 필요 / 작성자 ≠ 검증자: 이 문서는 독립 검증 전 / 일반성 n/N: 1/13(이 회로만 실측) / 만들면 배선: 해당 없음.

**(3) 원래 취지와 다름** -- (i) icmr_v '폭' → '출력 범위 포함' 재검토 제안(2026-10-08 Q4 (4)); (ii) 안 A는 O-211 '기준점 대비 허용 저하'를 '유도 저하(= 절대 하한)'로 읽음 -- 형식 일치·뜻 다름 표지; (iii) node_voltage_targets_v net 참조 형식 = SF-1 범위 확장.

**(4) 권고 실측 출처** -- 직접 잼: 엔진 3회(`engine_run.jsonl`, TEMP s3 runs/evals), SPICE 11 sweep(`spice_ref.jsonl`·`analyze_ref.jsonl`·`gain_drop_at_region_end.jsonl`, 넷리스트·로그 `%TEMP%/icmr4_nmcnr_spice/nmcnr_*.{cir,log}`, 모델 sha = LUT meta 대조 통과), Fig. 3 crop 대조, 단계 B 보고서. 인용(agent·기존 기록): o206 `wt/_drafts/evidence/2026-10-31/o206_icmr/o206_compare.txt`(봉인점 44.06 dB·SPICE 41.85 dB·nominal_fail), o206_seal_dump.jsonl.

**(5) 권고 확인표(권고 A·SP-2)** -- ① 지적 사실 재확인: spec :22-24·:116-139·:171-176 직접 읽음, 정지 사유 3회 실측 ② 계획 grep: N3.8 'ICMR 기능 기준'·'출력 범위 판정 꼴'(plan.md:729 부근), LA-1 완료 9(plan.md:2003), DE-1/SF-1 행(:1329·:1333) ③ 원칙 전수: 1(물리 -- 실측 9설계)·3·11(⚠ d-2 (가))·13·14·16(library) 점검 ④ 대안표: §3 표(A·B·C·D), d-2 (가)/(나) ⑤ 실현 가능성: R2b·R4·R6 SPICE 성립, R1 x0 = 0.9 불성립 ⑥ 열린 결정·design 영향: SF-1 칸 꼴, DE-1 (e) 함수, B87 backlog, LA-1 ⑦ 원래 취지: (3) 참조 ⑧ 원문: p.599·p.600·p.601·p.602 + 로컬 PDF ⑨ 물리: §1 유도 = SPICE 9/9 일치(맞음); 안 A '조건부' ⑩ 결정 간 모순 점검: **안 함 -- 권고 작성자가 아닌 점검자 몫**(O-211 RR-3 문언과 안 A의 관계, O-154 Q4·O-145와 icmr_v 재검토의 관계를 대조해야 함; 그 전 권고 상정 금지 -- 원칙 26 ⑩).
