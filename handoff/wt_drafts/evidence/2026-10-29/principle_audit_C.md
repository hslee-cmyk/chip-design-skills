# 근본원칙 감사 C 묶음(원칙 11~16) -- 승인 전부터 어긴 곳 전수 재검토

- 작성: 2026-10-29, 원칙 감사자 C(읽기·측정만, 문서·데이터 수정 0, git 읽기만).
- 원칙 정본: `chip-design-skills/CLAUDE.md` C. 값과 회로 11~16(+ 판정에 쓴 20 '승인됐다는 근거가 아니다').
- 대상 판: 계획 master `chip-design-skills/docs/01-plan/features/*.plan.md`(v6.38.4) + 계획 v6.38.5 worktree `wt/plan-v6385`(HEAD `45a31ff1`), design `wt/design-v115`(HEAD `ef573444`) 40·41·42, 회로 데이터 master `skills/analog-gmid-design/assets/{library,heldout}`·`sky130_pdk_decl.json`, 결정 기록 `wt/_drafts/user_decisions.md`, 대기열 `wt/_drafts/topology_correction_queue.md`.
- 측정 폴더 `wt/_drafts/evidence/2026-10-29/principle_audit_C/`:
  - `grep_ctx.py`(정규식 문맥 추출), `heldout_hits_plan_design.txt`·`heldout_hits_plan_design_dedup.txt`·`heldout_hits_decisions.txt`(held-out 언급 전수), `convention_hits.txt`(관례·통상·임의), `box_hits.txt`('10번'·상자), `const_hits.txt`·`design_const_hits.txt`(자리값·여유·기본값), `tag_hits.txt`(태그 근거), `dec_rows_names.txt`(DEC 행별 회로·소자 이름 빈도), `spec_dump.py`→`spec_values.txt`(13 spec 값과 출처 kind·origin·record), `measure_summary.py`→`measure_summary.txt`(M1~M4).
- 한계(확신도에 반영): 7 MB 문서를 전부 통독하지 않았다. 원칙별 정규식 전수 grep → 걸린 자리의 앞뒤 문맥과 근거 문서를 읽었다. design 40·41은 grep 수준이다. 엔진 코드는 출처 확인용(`dof_rank_sample_count` 소비자)으로만 봤다(원칙 8 용도 제한).

---

## 0. 결론 요약

1. **held-out 오염이 가장 크다.** U-75 선정 규칙('엔진 개발(코드·test 픽스처·structure.json 사실·spec 값 조정·발동표 측정)에 쓰지 않은 회로')과 U-76 (5)('held-out 실패를 고치려고 엔진을 바꾸면 그 회로는 개발 회로로 옮긴다')를 4회로 중 3회로가 이미 어겼다(cnr_ota·erfc_ota 강, r2r_opamp 중). rfc_ota는 경미(인용만)다. 오염된 결정은 승인 O-173(card DR-1)·O-174(erfc 규칙과 bulk 정정)·O-118(r2r F 포트)이다. 열린 권고 Q-CB1·Q-ZG1은 승인되면 오염을 더 키운다. 특히 Q-CB1은 held-out spec에 상자를 더하고 그 하한을 held-out oracle 실측으로 고르자는 안이라 **'spec 값 조정'에 정면으로 해당**한다.
   - 근거 문서(`cbox_rereview.md`·`erfc_region.md`·`flow_derivation.md`)는 DEC-98·U-75·U-76을 한 번도 언급하지 않았다(M4: 0/0/0). 반대로 r2r 감사(`audit_r2r_fport_cmr.md`)는 오염 여부를 사용자 판단으로 올렸다. 그런데 결정 뒤 U-76 (5) 귀결(개발 회로로 옮기기)은 적용되지 않았다.
   - master 계획 N6.36 DR-1의 착수 조건이 '**유일 소비자 = heldout `cnr_ota`**'이고 완료 조건 (3)이 'cnr_ota 단계 A가 다음 정지 사유까지 진행'이다. 계획 문언이 held-out을 엔진 개발 대상으로 명시한 셈이다(M3).
2. **관례를 정의로 쓴 공통 상자·임계가 남아 있다.** 그중 '10번' θ 커패시터 상자 [0.1 pF, 10 pF]가 가장 크다. 계획이 스스로 ⚠로 표지했지만 권고 Q-CB1 (나)는 보상 C 쪽에 그대로 유지한다. 그 밖에 '8번' 저항 상자, 구조 가드 √2·2, PM 70°(folded는 '6회로 중 5회로 관례'가 근거), CM PM 60°, 파일럿 CMRR·PSRR 60 dB가 있다. 또 `dof_rank_sample_count = 10`은 계획이 '근거 없는 상수라 삭제'(N3.7)했는데도 13/13 spec에 남아 있다. 출처 칸도 지워진 규칙 `N3.7 '기본 10'`을 가리킨다(M1, 실측).
3. **규칙 문언의 회로 이름(원칙 12)**: DEC 행 문언에서 규칙 자체가 회로 이름에 기대는 경우는 찾지 못했다. 이름은 '파일럿 적용'·'예'·ratified 사실로만 나온다(`dec_rows_names.txt`). 문제는 일반성 측정 쪽이다. 발동 회로가 held-out 하나뿐이고 library 발동이 0인 규칙이 5개다(DR-1 저항 망, DR-1 0 전류 MOS, Q-ZG1 기하, Q-CB1 결합 C, O-118 F 포트). 이 규칙들은 library에서 n/N을 잴 수 없다.
4. **원칙끼리 충돌한다(사용자 해석이 필요하다).** 원칙 12('일반성은 library·heldout 전수로 잰다')와 U-75('발동표 측정에 쓰지 않음')가 부딪힌다. 13회로 무동작·발동 계수(DEC-102 (d), headroom-chain M-H2, graph-consumption N4-0, IT-0)는 '검증 관측'으로 읽으면 허용되고, U-75 문언대로 읽으면 위반이다. 이 감사는 다음처럼 갈랐다.
   - 보고만 했으면 '관측'이다.
   - 그 계수로 규칙의 범위나 필요를 정했으면 '위반'이다(예: '13회로 해당 = erfc 셋뿐 → library 영향 0').
5. 논문 값(원칙 13): 사용자가 명시 지정한 값(O-129·O-130·O-145·nmcnr gain 100·ngcc gain 111)은 원칙을 지킨다. 반면 '기본안대로/권고대로'로 확정된 논문 값이 library 6건 이상, held-out 12건(전부 origin = paper)이다. 그 값들은 다른 공정·전압(AMS 0.8 µm, 0.18 µm, 3.3 V)에서 달성된 값을 sky130 1.8 V 목표로 옮긴 것이고, 실현 가능성은 재지 않았다.

---

## 1. 위반 표

심각도: 높음 = 엔진 개발·판정 결과를 바꾼다 / 중 = 결정 근거가 원칙과 어긋나지만 영향이 한정된다 / 낮음 = 문서·인용만. 확신도: 높음 = 실측·원문 대조 / 중 = 기록 대조 / 낮음 = 기록 미발견에 근거.

| # | 문서/데이터·줄 | 요지 | 위반 원칙 | 근거(실측·원문) | 원칙 재유도 결론 | 결론 변화 | 영향 결정/card | 심각도 | 확신도 |
|---|---|---|---|---|---|---|---|---|---|
| V-01 | master plan N6.36 `gain-budget-gmid-sizing.plan.md:2337-2346`, 표 :1224; v6385 :2348-2352·:1231 | card DR-1(고정값 저항 망 노드 writer)의 착수 조건 '유일 소비자 = heldout `cnr_ota`', 완료 조건 (3) 'cnr_ota 단계 A가 다음 정지 사유까지 진행'. 계기 = 재감사 `backlog_reaudit_parts/B_N53.md:39` I-H1 'heldout 2회로 엔진 미실행 → 필요(엔진 일반성)' | 16(DEC-98 (4)·U-75 선정 규칙·U-76 (5)), 12(library 발동 0), 9(소비자가 held-out뿐) | M3 실측 문언; B_N53 I-H1 행에 DEC-98 검토 없음 | 규칙(Ohm + KCL 선형 해, 게이트 전류 0)은 물리로 일반형이고 상수·이름이 0이라 library toy만으로도 세울 수 있다. 다만 held-out 실패를 고치려는 엔진 변경이므로 U-76 (5)상 cnr_ota는 개발 회로가 된다 | **있음**: 규칙은 유지 가능, cnr_ota의 held-out 지위는 유지 불가(또는 card 보류 + A' 엔진 실패로 남김) | O-173 BL-DR1·C14, card DR-1 | 높음 | 높음 |
| V-02 | v6385 N6.36 범위 'VDS = 0 묶음' :2348(708~2000자), 완료 조건 (8) :2350; O-174(`user_decisions.md:1155`) | 구조적 0 전류 MOS → VDS = 0 묶음 규칙. 13회로 발동 = erfc M19~M21뿐(library 0). 분석 `erfc_region.md` 전부 erfc 기반. 완료 조건 (8) 'erfc_ota 단계 A … 발동하고 다음 정지 사유까지 진행' | 16, 12, 9 | M3; M4(erfc_region DEC-98 0회) | 물리(KCL 항등 0 전류 → 채널 전압 0, gm = 0 소스·드레인 대칭)는 일반형이다. 하지만 동기·검증·완료 조건이 held-out 하나뿐이다 | **있음**: erfc는 개발 회로로 옮겨야 한다 | O-173 Q-4(C10)→O-174, card DR-1 | 높음 | 높음 |
| V-03 | `topology_correction_queue.md` #1, master `6705b911`(erfc M19·M20 bulk = vcn, M21 = vcp) | 엔진 규칙(DR-1 'bulk = 고정 쪽일 때만')의 적용 조건을 맞추려고 held-out topology connectivity를 바꿨다 | 16(held-out 데이터를 엔진 쪽에 맞춤), 15는 절차 준수(대기열·일괄 반영 지시) | `erfc_ota.topology.json` `_bulk_comment`; 원문 Fig.6은 3단자 기호(bulk 근거 없음) | bulk = source는 물리 근거(접합 누설 VDS +0.246 V)가 있는 해석이다(원칙 14 충족). 그러나 계기가 엔진 규칙이다 | **있음**: 정정은 유지할 수 있으나 erfc held-out 지위가 깨진다(V-02와 같은 귀결) | O-174 | 중 | 높음 |
| V-04 | v6385 N5.3 Q-CB1 :1166, DR-1 완료 조건 (10) :2350, Q-ZG1 연동 :2348; 근거 `cbox_rereview.md` §2.4 (iii)·§1 4 | erfc 결합 C(CBAT1_L/R·CBAT2)를 '회로별 spec 선언 상자'로 바꾸고 하한을 **erfc oracle `.tran` SR sweep 실측 경계(1.0 pF FAIL·1.5 pF PASS)**로 정해 held-out spec에 data 커밋하자는 권고. 근거에 cnr_ota 53.8 fF MIM도 인용 | **16(spec 값 조정 -- U-75 문언에 명시된 금지 항목)**, 12(결합 C 판별 규칙 발동 = erfc 셋뿐), 11(격자 경계점 선택, 공통 상자 '10번' 잔존) | M4(cbox_rereview DEC-98·U-75·U-76 0회); `cbox_rereview.md:123` '누가: card SF-1의 held-out data 커밋 계열' | 결합 C 하한의 물리 결정자(α·SR)는 대신호 양이라 엔진 손계산 불가(O-122)이고, spec 선언 말고는 자리가 없다는 분석 결론 자체는 맞다. 그러나 그 선언을 **held-out 실측으로 채우는 순간 held-out 정의가 깨진다** | **있음**: 권고 (나)는 held-out 지위를 유지하면 채택 불가 → (마) front 공백 수용(fail-closed, A' 판정에 'oracle_only_fail'로 기록) 또는 erfc 개발 회로 전환 뒤 (나) | Q-CB1(대기), '10번'·N13 재질문, DEC-105 (10)(a) | 높음 | 높음 |
| V-05 | v6385 N5.3 Q-ZG1 :1163, N6.36 :2348(f_HP 상한 U1~U4, 기하 = W_min·L_min) | 0 전류 MOS 기하 규칙의 유도·실측(f_HP 0.9/18.7 kHz, t_slew = erfc 원문 계단 600 mV·SR 19.32 V/µs → 31 ns, 정류 표류 s6)이 모두 erfc다. '13회로에서 이 꼴은 erfc CBAT 셋뿐' | 16, 12 | `flow_derivation.md`(M4 0회) | 상한식은 이미 있는 양에서 나오고 상수가 0이라 물리 일반형이다. 결론(면적 최소 기하)은 library toy로도 세울 수 있다. 다만 검증 근거가 held-out뿐이다 | 내용 변화 없음 / **지위 변화 있음**(V-02와 같음) | Q-ZG1(대기), DR-1 | 중 | 높음 |
| V-06 | v6385 N3.8 :680(F 성분 미선언 입력 포트 함께 구동), :345 O-118 3번; F-IT9 :1451 | r2r 감사 뒤 KCL ICMR 구동 규칙을 뒤집었다. 코퍼스에서 이 꼴은 r2r뿐(F-IT9). 계획은 '이미 본 것·근거 아님·구현 근거 library toy'로 표지 | 16(U-76 (5) 귀결 미적용), 12(library 발동 0) | `audit_r2r_fport_cmr.md:10·230-232`(오염 여부를 사용자 판단으로 상신) | 규칙(모든 입력 포트를 같은 x로 구동 = SPICE servo와 같은 구성)은 물리 일반형이다. 하지만 정의 불능 → 정의됨으로 바뀐 계기가 held-out 관측이다 | 내용 변화 없음 / **지위: 사용자 판단 필요**(통보 뒤 결정이었으나 U-76 (5) 적용 여부는 묻지 않음) | O-118 3번 | 중 | 중 |
| V-07 | v6385 SF-1 범위(R_min 종류) :2195(3316·4826·6141자) | R_min 규칙의 '유도'에 heldout rfc_ota RB 1412 Ω를 쓰고, toy (c3)을 'rfc_ota RB 1412 Ω 꼴'로 둔다. '선례: heldout cnr_ota 저항 값' | 16(경미 -- 근거 인용) | 문언 | 같은 문단에 library current_reuse R_S 1816 Ω가 있고, 규칙은 PDK 선언에서 유도된다 → held-out 없이 성립한다 | 없음(인용만 빼면 된다) | SF-1 | 낮음 | 높음 |
| V-08 | v6385 DEC-102 (d) :301, headroom-chain M-H2 :491·:115, graph-consumption N4-0 :97·:552, GC-B7 :791 | 13회로(library 9 + heldout 4) 무동작·발동 계수. GC-B7은 관찰 대상에 r2r RL·rfc RB·cnr x37/x40/x9를 넣었고, 착수 실측 = 'library 9 + heldout' | 16 대 12 **원칙 충돌** | U-75 문언 '발동표 측정' 대 CLAUDE.md 12 '일반성은 library·heldout 전수로 잰다' | 무동작 보고 = 관측이라 허용된다. 계수가 규칙 범위·필요를 정하면 위반이다. GC-B7 질문은 library 저항(nmcnr RL·sf R1a~c·current_reuse R1)만으로 세울 수 있다 | 해석에 따라 다름 → 사용자 결정 | DEC-102, HC M-H2, GC N4-0, GC-B7 | 중 | 중 |
| V-09 | `user_decisions.md:154`('10번', 2026-10-08), v6385 DEC-105 (10)(a) :304, Q-CB2 :1167; library spec 커패시터 상자 9 | θ 커패시터 상자 [0.1 pF, 10 pF] = 보상 C '통상 이 범위' 관례(파일럿 500 fF). 물리 결정자 없음. 하한에 붙는 사례가 있다(PM 목표 없는 3회로 Cc, ngcc Cm2 -- STEP2 N7) | 11 | 계획 :1166·:1167이 스스로 ⚠ 표지; `cbox_rereview.md` | 하한 후보 = PDK 최소 MIM 치수 규칙 × camimc(PDK 선언에서 유도 가능), 또는 마디 기생 바닥(엔진 MNA 양). 상한 = 이미 있는 spec 면적 제약(`area_search_m2`)이 막는다 → **공통 상수 없이 유도할 길이 있다**(이 감사에서 값은 재지 않음) | **있음**(관례 상자 → PDK·면적 유도) | '10번', N13, DEC-105 (10)(a), Q-CB1 (나)의 보상 C 유지분, Q-CB2 | 높음 | 높음 |
| V-10 | `user_decisions.md:153`('8번', 2026-10-08), DEC-105 (10)(c) | θ 저항 상자 current_reuse R1·R2 [10 kΩ, 10 MΩ], sf_pushpull R1a~c [1 kΩ, 1 MΩ] -- 10진 폭 판단값. 유도 기록 없음 | 11 | 결정 행·계획 문언(유도식 없음) | 결정자 후보: CMFB 감지 R은 출력 부하(R ≫ r_out 조건)와 면적, 자기바이어스 R은 KVL 고리(O-127 V_R 종속 -- 값 미선언 DC 경로 저항은 이미 고리 종속 원칙)에서 나온다 | 있을 수 있음(미측정) | '8번', DEC-104 R 상자·O-127 | 중 | 중 |
| V-11 | 13/13 `*.sizing_spec.json` `human.search.dof_rank_sample_count = 10`(source `plan_rule N3.7 '기본 10'`); 계획 :643 | 계획 N3.7은 '옛 기본 10은 근거 없는 상수라 v6.18에서 삭제(감사 A13)', 선언은 '출처 필수', 없으면 유도 규칙(일반 위치 1점 + 확인 1점)이라 적는다. 데이터는 지워진 규칙을 출처로 대며 10을 선언한다. 소비자 = `E/search/residual_probe.py:5` | 11(출처가 지워진 규칙인 상수) | M1 실측 13/13; card 배정 grep 0 | 선언을 지우면 유도 규칙(2점)이 적용된다 | **있음**(10 → 유도 규칙) | 데이터 정리(SF-1 data 계열에 넣을지 사용자 확인) | 중 | 높음 |
| V-12 | library 6회로 `offset_excess <= √2`, 7회로 `noise_excess_th <= 2`(2026-10-08 Q3 (3)·Q11 "네 제안대로") | 구조 가드 경계 = '부하 기여 ≤ 입력쌍 기여'(비 1). √2·2는 비 1에서 유도되지만 **비 1 자체가 설계 선호 관례**다 | 11 | `spec_values.txt` | 물리 결정자 = 시스템 offset·잡음 요구(spec)다. 요구가 없으면 '보고만'이 원칙형이다(DEC-96 (1) nqs_ratio 처리와 같은 꼴) | 있을 수 있음(가드 → 보고) | Q3 (3), Q11, DEC-21·DEC-96 | 중 | 중 |
| V-13 | O-140 D1(`user_decisions.md:969`) folded PM ≥ 70 '**library 관례, 6회로 중 5회로**'; 파일럿 PM 70(2026-10-07 '1~7은 기본안대로'); CM PM ≥ 60(2026-10-08 6번 '제안한 값', '45° 미만 링잉') | 다수결·경험칙을 spec 값의 근거로 썼다 | 11, 13(관례를 정의로) | 결정 원문 | PM 하한의 물리 결정자 = 정착(울림) 요구 또는 응용 β다. 선언이 있는 회로는 그 양에서 유도하고, 없으면 사용자 지정값이어야 한다. sf·two_stage·two_stage_sf PM 70은 사용자 '70도 이상' 명시라 해당하지 않는다 | 있을 수 있음 | O-140 D1, 2026-10-07 항목 2, 2026-10-08 6번 | 중 | 높음 |
| V-14 | 파일럿 `ratio_ss_db >= 60`×2(CMRR·PSRR), two_stage_ota `gain_ss_db >= 57` | 출처 = 'U-35(2026-09-17) user_spec 기입' -- 오케스트레이터가 옛 값을 user_spec으로 분류했다. `user_decisions.md`에 사용자 지정 기록 0건(grep 'U-35'·'60 dB' 0). two_stage 57은 T-27 '결정값 재사용' | 11, 13 | `spec_values.txt`; 계획 U-35 :2438 | 출처를 사용자에게 다시 확인받거나, 근거 없는 값으로 보고 삭제·재지정해야 한다 | 있을 수 있음 | U-35, T-27 | 중 | 중 |
| V-15 | 파일럿 `gain_ss_db >= 54`(= 옛 엔진 실측 57.03 dB − 3 dB 마진) | 자기 실측에 마진 상수를 붙인 값 | 11 | spec record; O-133이 삭제 결정 | O-133 (가) 삭제(원천 = static 오차 0.1 %) | 이미 결정됨 -- data 커밋(SF-1) 대기, master 데이터에는 남음 | O-133, SF-1 | 낮음 | 높음 |
| V-16 | 파일럿 `classab_centering_dev_v <= 0.15` | 물리 결정자 없음 | 11 | 계획 Q-CA1 :1164 | 이미 삭제 권고·대기 | 처리 중 | Q-CA1 | 낮음 | 높음 |
| V-17 | library 9 `area_search_m2` 예산(0.005~0.04 mm², 2026-10-08 결정 11 'B로 표의 값 그대로') | 표 값의 유도 기록을 찾지 못했다(user_decisions·계획·history grep) | 11 | grep | 사용자가 채택한 값이라 '사용자 지정'으로 볼 수 있다. 다만 표 작성 근거 확인이 필요하다 | 미정 | 결정 11 | 낮음 | 낮음 |
| V-18 | held-out `rfc_ota` `input_dc = 1.02 V`(원문 ICMR [0.3, 1.74] **중앙값**, HA-1), `erfc_ota` 0.8 V(원문) | 중앙값은 '상자 중심 자리값' 꼴(O-127이 결함 유형으로 정함). library는 O-168·DEC-106으로 입력 CM = 엔진 변수로 바뀌었는데 held-out은 고정값이 남았다 | 11 | spec record | DEC-106 일반 규칙을 그대로 적용하면 엔진 변수가 된다. 단 held-out spec을 바꾸는 것이므로 '형식 이관(규칙 균일 적용, 엔진 결과 무관)'으로만, A' 판정 전에, 사용자 승인으로 해야 한다 | 있을 수 있음 | HA-1, O-168·O-170 U-128 | 중 | 높음 |
| V-19 | library 논문 값 '기본안' 확정: ngcc GBW 10 MHz·PM 63.4°·ICMR 0.6 V·CL 10 pF, nmcnr GBW 816 kHz·CL 100 pF(U-39 2026-09-21 '기본안대로'), 파일럿 Cf/Cs 500 fF(2026-10-07 '기본안대로'); held-out 제약 12건 전부 origin = paper('권고대로'·U8 '권고대로'·D-9 '권고안') | 원문 달성값(다른 공정·전압)을 sky130 1.8 V 확정값으로 옮겼다. r2r는 3.3 V 값(gain 85 dB·UGF 2.6 MHz·PM 66°)을 1.8 V에 '목표 유지' | 13(+20) | `spec_values.txt`(M2: heldout user_spec·paper 12, library user_spec·paper 9) | 원칙 13은 '사용자 지정분만 확정'이다. '기본안/권고대로' 승인은 형식상 지정이지만 원칙 20상 재확인 대상이다. 실현 가능성(sky130 손계산 상한)을 재지 않았다. held-out 값은 지금 바꾸면 그 자체가 spec 조정이므로 **동결 + 원문 값 출처 기록 유지**가 원칙형이다(A'가 '둘 다 실패 = 판정 불능'으로 처리) | library: 있을 수 있음 / held-out: 동결 권고 | U-39, 2026-10-07 항목 4, held-out A·B·C·D spec 결정 | 중(library)·낮음(held-out) | 중 |
| V-20 | O-122 근거 'library spec 슬루 선언 0(**heldout만**)'(`user_decisions.md:853`); 계획 :681 '현 코퍼스에서는 held-out 평가가 여기에 해당' | held-out을 영향 범위 논거로 썼다 | 16(경미, 관측) | 계획이 스스로 '영향 보고이고 판단 근거가 아님'으로 표지 | 결정의 주근거(60점 실측 = library 5회로 -- `slew_estimate_vs_bound.md:3·21` 'heldout 회로는 쓰지 않았다')는 library다 | 없음 | O-122 | 낮음 | 높음 |
| V-21 | v6385 SD-1 D2 :2076(rfc_ota `Cstab` 0.5 pF topology 추가, O-76 (3)) | connectivity 변경인데 `topology_correction_queue.md`에 행이 없다(card 데이터 커밋으로만 계획) | 15(대기열 등록 절차) | 대기열 파일 #1·#2만 | 사용자가 이름·연결을 확인했고 반영 시점(SD-1)도 정해져 있다. 대기열 행만 빠졌다 | 없음(절차 보완) | O-76 (3), SD-1 | 낮음 | 높음 |
| V-22 | held-out `erfc_ota.topology.json` 태그 `compensation`; library 9 + `_TEMPLATE` 태그 4종 | analog-grammar 산물이 데이터에 남아 있다. 계획은 '읽지 않음'·LT-1에서 삭제로 정했다(F-LT3) | 14(데이터 잔존만, 근거 사용은 발견 못 함) | `tag_hits.txt` -- 근거로 쓴 자리 0. design 40 :964의 `budget_reference_device` 9건은 옛 선언과 새 규칙의 대조용 | 없음 | 없음 | LT-1 | 낮음 | 중 |

### 1.1 원칙 12(규칙 문언의 회로 이름) -- 위반 0, 단 일반성 측정 불가 규칙 5개

- DEC-01~DEC-106·WP 행 전수 이름 빈도(`dec_rows_names.txt`): 이름은 '파일럿 적용(ratified)'·'예'·회로별 spec 값·연결 판독 사실로만 나온다. DEC-09·15·27은 '소자 이름 리터럴 금지 = 구조 규칙 E·I' 상태를 적는다. 규칙 문장 자체가 회로 이름을 조건으로 쓰는 경우는 찾지 못했다.
- 일반성 측정 불가(발동 = held-out 1회로, library 0) 규칙 5개: DR-1 저항 망(cnr), DR-1 VDS = 0 묶음(erfc), Q-ZG1 0 전류 MOS 기하(erfc), Q-CB1 결합 C 판별(erfc), O-118 F 성분 포트(r2r). 원칙 12가 요구하는 n/N이 library에서는 정의되지 않는다(0/0). 남는 근거는 toy뿐이다.

---

## 2. held-out 오염 목록과 처리안

| 회로 | 오염 자리 | 정의 위반 / 검증 관측 | 상태 |
|---|---|---|---|
| cnr_ota | card DR-1 저항 망(유일 소비자, 완료 조건 (3)) -- V-01; IT-0·단계 A 정지 실측이 card 근거; Q-CB1의 '53.8 fF MIM' 논거; SF-1 R_min 선례 인용 | **정의 위반**(엔진 개발 대상) + 인용 | 오염 -- 강 |
| erfc_ota | O-173 C10(intended_region triode spec 선언 -- O-174가 대체), O-174 VDS = 0 규칙(발동 유일), topology bulk 정정(`6705b911`), Q-ZG1 유도·실측, Q-CB1 oracle SR sweep으로 held-out spec 상자 하한 제안, DR-1 완료 조건 (8)·(10) | **정의 위반**(엔진 개발 + spec 조정 제안 + 데이터 변경) | 오염 -- 강 |
| r2r_opamp | O-118 3번 F 포트 규칙 변경(감사 실측이 계기, 유일 사례) | 위반 소지(사용자에게 통보한 뒤 결정, U-76 (5) 미적용) | 오염 -- 중 |
| rfc_ota | SF-1 R_min '유도' 예·toy (c3) 꼴 인용; SD-1 Cstab 추가(DUT/응용 망 원칙의 균일 적용, 엔진 결과 무관) | 인용 = 관측 수준, Cstab = 등록 정정 | 경미 -- 인용 삭제로 회복 |

처리안(대안 비교):

| 안 | 내용 | 원칙 정합 | 비용·위험 |
|---|---|---|---|
| (가) **U-76 (5) 그대로 적용 -- 권고** | cnr_ota·erfc_ota(그리고 사용자 판단에 따라 r2r_opamp)를 개발 회로로 옮긴다(위치는 `assets/library` 또는 지위 표지 -- design 몫). A' 일반성 판정 전에 새 held-out 2~3개를 사용자가 고른다(U-75 사용자 몫). DR-1·Q-ZG1·O-118 규칙의 근거·red를 library 또는 합성 toy로 다시 세운다(V-07 인용 삭제 포함). Q-CB1 (나)는 개발 회로가 된 erfc에서만 허용된다 | 16·12·20 충족, 규칙 내용(물리 일반형)은 보존 | 새 held-out 선정·등록 비용. A' 일반성 근거가 rfc_ota 하나로 줄어든다 |
| (나) 오염 결정 철회, held-out 유지 | DR-1의 cnr·erfc 갈래, O-174 규칙, Q-CB1·Q-ZG1을 철회하거나 보류한다. erfc bulk 정정을 되돌릴지는 사용자 결정(정정 자체는 물리 근거가 있어 되돌릴 이유가 약하다). A'에서 cnr·erfc는 '엔진 실패'로 남아 U-76 (1)상 단계 ② 미완료(fail-closed) | 16 형식상 회복 | 이미 본 사실(erfc 분석 3편, r2r 감사)은 지울 수 없어 '맹검' 성질이 실제로는 회복되지 않는다. 결국 고치면 (가)로 간다 |
| (다) held-out 정의 완화 | U-75 '발동표 측정·엔진 개발 금지'를 '판정 전 관측 허용'으로 고친다 | ⚠ 원칙 위반 경고: DEC-98 (4) 일반성 증거가 in-sample이 된다. 기준 약화라 사용자 승인 사항(원칙 18) | 비용 최소, 일반성 주장 약화 |

- V-08 원칙 충돌의 처리안: '무동작·발동 계수의 **보고**는 관측으로 허용, 그 계수로 규칙 범위·필요·값을 정하는 것은 금지'로 U-75 문언을 명확히 한다(사용자 결정). 이 해석이면 DEC-102 (d)·M-H2·N4-0은 유지되고, GC-B7 착수 실측과 Q-CB1·Q-ZG1의 '13회로 해당 = erfc뿐' 논거는 위반이다.

---

## 3. 재질문이 필요한 승인 결정

| 결정 | 이유(원칙) | 질문 요지 |
|---|---|---|
| O-173 BL-DR1(card DR-1)·C14(held-out 4회로 확정) | 16 -- 두 결정이 동시에 승인됐지만 DR-1의 유일 소비자가 held-out이라 U-76 (5)와 충돌한다(V-01) | cnr_ota를 개발 회로로 옮길지, DR-1 저항 망 갈래를 보류할지 |
| O-174(+ O-173 Q-4/C10) | 16(V-02·V-03) | erfc_ota 지위(개발 회로 전환 여부). bulk 정정 유지 여부 |
| O-118 3번(r2r F 포트) | 16(V-06) -- 결정 때 U-76 (5) 귀결은 묻지 않았다 | r2r_opamp를 개발 회로로 옮길지 |
| '10번'(2026-10-08)·N13(2026-10-14)·DEC-105 (10)(a) | 11(V-09) | 보상 C 상자를 PDK 최소 MIM·면적 제약에서 유도하는 안으로 바꿀지(Q-CB2와 묶음) |
| '8번'(2026-10-08) | 11(V-10) | 저항 상자의 물리 결정자(부하 조건·고리 종속)로 다시 유도할지 |
| 2026-10-08 Q3 (3)·Q11(구조 가드 √2·2) | 11(V-12) | offset·잡음 요구가 없는 회로는 '보고만'으로 바꿀지 |
| O-140 D1(folded PM 70, '관례'), 2026-10-07 항목 2(파일럿 PM 70 기본안), 2026-10-08 6번(CM PM 60) | 11·13(V-13) | 사용자 지정값으로 다시 확정할지, 정착 등 결정자에서 유도할지 |
| U-35(2026-09-17)·T-27 -- 파일럿 CMRR·PSRR 60 dB, two_stage gain 57 dB | 11·13(V-14) | 사용자가 정한 값인지 확인, 아니면 삭제·재지정 |
| 2026-10-08 결정 11(면적 예산 표) | 11(V-17, 확신도 낮음) | 표 값의 근거 확인 |
| HA-1(rfc input_dc 1.02 V 중앙값) | 11(V-18) | DEC-106 규칙을 held-out에 균일 적용할지(형식 이관, A' 전) |
| U-39(2026-09-21)·2026-10-07 항목 4 -- library 논문 값 기본안 | 13·20(V-19) | 사용자 지정으로 유지할지, sky130 손계산 상한을 잰 뒤 재지정할지 |
| (데이터 정리, 결정 아님) `dof_rank_sample_count = 10` 13/13 | 11(V-11) | 선언 삭제(유도 규칙 적용)를 어느 data 커밋에 넣을지 |
| (열린 권고) Q-CB1 (나)·Q-ZG1 (나) | 16·12(V-04·V-05) | held-out 지위를 유지하면 Q-CB1 (나)는 채택 불가 -- 처리안 (가)/(나) 선택 뒤 다시 상정 |

---

## 4. 원래 취지와 다름 / 권고 실측 출처

- 원래 취지와 다름: 이 감사는 문서·데이터를 바꾸지 않았다. 처리안 (가)는 U-75 '4회로 확정'(O-173)의 취지(held-out 4개로 일반성 판정)와 다르다. 그래서 사용자 결정 사항이다.
- 권고 실측 출처: M1(`measure_summary.txt` -- spec 13/13 `dof_rank_sample_count` 10·출처 N3.7), M2(제약 출처 분류), M3(계획 문언의 held-out 단독 발동·완료 조건), M4(근거 문서의 DEC-98·U-75·U-76 언급 0회). 나머지는 `heldout_hits_*.txt`·`box_hits.txt`·`convention_hits.txt`·`spec_values.txt`의 줄 번호 대조다.
- 이 감사가 재지 않은 것: V-09 보상 C의 PDK 최소 MIM 유도값, V-10 저항 상자 결정자 수치, V-19 sky130 손계산 실현 가능성 상한. 권고 전에 별도로 재야 한다(원칙 21).
