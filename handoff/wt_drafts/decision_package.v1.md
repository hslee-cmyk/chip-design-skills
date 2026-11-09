# 사용자 결정 패키지 (2026-09-30, gate master 7535799 기준)

범위: `_drafts/`의 준비 초안에서 **진짜 사용자 몫**(spec·회로 해석·기준 변경·승인)만 모았다. 이미 결정된 것(`user_decisions.md`: P9 E1 정정 승인·topology.json 주석 보류, Phase 2 DoD D1 E4 기준값·D2 P3c)은 뺐다.
원칙 기본안(묻지 않는 것)은 맨 끝 '알림(기본안)' 표에 따로 적었다. 수치는 모두 초안의 실측값이고, 괄호 안에 파일을 적었다.

준비 상태: `draft_v3_decision_question.md`·`draft_v3_exempt_binding.spec.md`·`draft_v3_scope_policy.spec.md` -- **준비 중(아직 없음)**. A1은 `v3_scope_systemic.md`와 `draft_b26_1.spec.md`, `review_b34.md`를 근거로 적었다.
`draft_b34.spec.md`는 `review_b34.md` 권고 방향으로 수정하는 중이다. B34 항목은 그 권고를 기준으로 적었다(옛 (a)/(b)는 참고).
Phase 4 design은 v0.2다(`draft_phase4_design.v02.md`와 내용 같음, v0.3 없음).

---

## (A) 지금 필요 -- 다음 card(B28 후속: V3 게이트, E4, B26-1, B34)

### A1. V3 판정 범위 -- B26-1 U1과 B34 V3를 한 결정으로 (review_b34 S5 권고)

**질문**: V3(변이 검사)가 "AST가 바뀐 def의 본문 전체"를 변이하는데, 이 대상을 **"diff가 닿은 문장 + 새 def"로 좁히는 게이트 규칙 변경**(약화)을 승인하는가?
**왜 사용자 몫**: 판정 기준의 적용 범위를 줄이는 게이트 변경이다. 기준 약화이므로 DEC-40에 따라 사용자 승인이 필요하다(`v3_scope_systemic.md` §4).

실측 배경(`v3_scope_systemic.md` §1·§2, `draft_b26_1.spec.md` V3 계획):
* B26-1: 바뀌는 def 31개, 변이 **2,472개** 중 diff가 닿은 변이 **106개**. 나머지 2,366개는 이 card가 쓰지 않은 기존 문장이다.
* 전수 실행 비용(직렬): 하한 ≈3.4 h, 상한 ≈122 h(≈5.1일). def 하나의 인벤토리 실행에 177~192 s가 든다.
* 면제 누수 결함: 변이 id가 def 해시나 card에 묶이지 않아서, B26-1 면제 목록이 B34 대상 1,402개 중 **619개**를 조용히 면제한다. 선례 `20260922-ic3-v3-exempt`의 14경로도 지금 살아 있다(14/14).
* `_metric_kcl_residual`은 인벤토리가 0이다(`_METRICS_REGISTRY` dict 경유). 변이 57개가 전부 FAIL이 된다. 이름으로 직접 부르는 test 1개를 더하면 인벤토리가 1이 된다. 이 test는 어느 안을 고르든 넣는다.

| 선택지 | 결과(실측) | 필요한 승인 |
|---|---|---|
| **(가) 게이트 규칙으로 좁힘 + 면제 id를 def 해시·card에 묶음 (권고)** | B26-1 실행 106개: 하한 ≈9분, 상한 ≈5.3 h. 좁힌 범위 밖의 변이 수는 `not_targeted`로 출력하고 기존 test 공백은 백로그로 넘긴다. 누수 619건이 막힌다 | 게이트 변경 spec card 1장(`gate_change: yes`, phase 0.5, B28 형식) + `target_kind: diff` 승인 1건(범위 설명에 "약화 승인"으로 명시). design 05 §10 V3 ①·⑤와 계획 N4.2 V3 문구를 개정한다. `plan_tables` 승인은 필요 없다 |
| (나) 좁히지 않음. 면제 누수 수정(강화)만 하고 B26-1은 전수 실행 (c) | 3.4~122 h가 걸린다. 생존 변이를 죽이는 test 보강이 레일과 무관한 기존 동작(예: `_build_theta_evaluator` 498변이 중 닿은 것 3개)까지 번진다 | 게이트 변경 승인 1건(강화여도 게이트 변경이라 필요) |
| (다) card마다 변이 id 목록으로 면제 | 누수를 알면서 받는 안이다(뒤 card에서 619건이 조용히 면제된다) | card마다 decision 승인 |
| ((b) card 재분할) | 대상 합이 2,472개 이상이라 비용이 줄지 않는다 | -- |

**B34 쪽(review_b34 권고, 약화 없음)**: B34는 이 결정과 관계없이 약화가 필요 없는 **좁힌 범위**로 간다.
* 범위: `_import_analog_grammar`의 except를 raise로 바꾸고, 인벤토리가 작은 def 4개(`find_idiom_matches`·`find_stack_edges`·`find_differential_and_mirror_forks`·`audit_theta_root_direction`)의 부재 분기를 지운다.
* 변이는 **118개**다. 계약 1·2·3·5·6·7은 def 1개(변이 12)만 고쳐도 성립한다(실측 126/126 `ImportError`).
* `propose_theta_kcl_gap_fill`(242변이, 생존 추정 약 48)과 `unavailable_reason` 삭제(계약 4)는 백로그로 보낸다.
* 운영 경로의 큰 def(`refine_…`·`propose_device_roles_gap_fill` 등)에 있는 도달 불가 분기 삭제는 B26-1·B35로 넘긴다. 그러면 같은 def를 한 번만 변이하고, 추가 V3 비용이 0이다.
* 옛 (a)안(base 생존 면제)은 약화이고 비용이 두 배다(base 전수 + head 전수). 사용자가 초안 전체 범위를 원할 때만 다시 연다.

* **권고**: (가). B34는 좁힌 범위로 간다.
* **막는 것**: B26-1 착수 조건 4. B34 V3 판정 방식. (가)이면 게이트 card가 B26-1보다 먼저 병합돼야 한다.
* **언제**: **지금**.

### A2. B26-1 U2 + B34 앞당김 -- decision 승인 1건(묶을 수 있음)

**질문**: 다음 셋을 한 번에 승인하는가(`draft_b26_u2_approval_question.md`의 질문 원문 그대로)?
1. DEC-60 레일 '넷' 전환기 종료: `supply_nets`가 없으면 `load_topology`가 거부한다. 레일 전압 전환기는 MG1까지 둔다.
2. DF-19·DF-26의 넷 몫을 MG1에서 분리한다(B26-1~4).
3. B26-1을 Phase 3 전(Phase 2 진행 중)에 착수한다.

여기에 **B34를 Phase 2 진행 중에 앞당기는 것**도 같은 기록으로 받을 수 있다(`review_b34.md` B1: 지금 card의 `approval: 20260923-20-dead-code-dup-design`은 "동작이 바뀌는 수정"을 덮지 않는다).

**왜 사용자 몫**: 사용자가 확정한 DEC-60의 한시 조항과 기한을 바꾸는 일이고, Phase 4 DF를 Phase 3 전으로 당기는 순서 변경이다. 선례는 U-39와 DF-35·DF-36이다.

| 선택지 | 결과 |
|---|---|
| **승인(권고)** | 편집 파일이 2개(stick_diagram·sizing_recipe)다. Phase 3 모듈 분리 뒤에 하면 6개 모듈로 흩어진다. 전제(`supply_nets` 없는 회로)는 9/9 선언(U-26 (b))으로 이미 없어졌다. 판정 표(`plan_tables_hash`)는 바뀌지 않는다 |
| 1·2만 승인, 착수는 Phase 3 뒤 | B26-1을 새 모듈에서 한다(편집 범위가 커진다) |
| 보류 | DEC-60을 그대로 둔다. 넷과 전압을 MG1에서 함께 처리하게 되어 넷 판정이 U-26 (a)를 기다려 Phase 4 끝까지 밀린다 |

* **막는 것**: B26-1(착수 조건 1·2, 계획 정정 `draft_b26_plan_patch.md` 커밋), B34 card의 `approval` 줄.
* 이 결정은 **Phase 3 design 승인(UD-0) 전에** 나야 한다. B26-1을 당기면 D0b의 `_RAIL_NETS` 목적지가 바뀌기 때문이다(`draft_phase4_design.md` 178행).
* **언제**: **지금**.

### A3. E4의 `PT` phase -- 기준 해석 변경

**질문**: Phase 2 DoD E4의 `PT`를 `--gmid-phase=2`로 읽고 `--gmid-dod` 실행을 E4에 더하는가(`draft_e4_clarify.md` 3항)?
**왜 사용자 몫**: design 20 §10은 10 §10의 PT 정의(`--gmid-phase=1`)를 "그대로" 쓰라고 한다. phase 값에 따라 xfail 조건과 엄격 집합이 달라지므로 판정 기준을 바꾸는 일이다(`dryrun_phase2_e4.md` ③).

| 선택지 | 결과(드라이런, 증거 아님) |
|---|---|
| **`--gmid-phase=2` + `--gmid-dod` 추가(기본안)** | phase 2 기본 실행과 dod 실행 모두 798 passed, 15 xfailed, 실패 0(각각 약 311 s, 256 s). `phase2_dod_brief.md`와 일치한다 |
| 문언대로 `--gmid-phase=1` | 재지 않았다. Phase 1 DoD용 정의라 Phase 2 검사가 아니다. 브리핑과 설계서의 `--gmid-dod` 불일치도 남는다 |

* 1·2항(스크립트 출처, `-B -P` 옵션 명시)은 절차를 명확히 하는 것이라 승인이 필요 없다.
* **막는 것**: Phase 2 DoD E4 판정 → Phase 3 착수 조건.
* **언제**: **지금**(Phase 2 DoD 전).

### A4. (A 참고) 지금 결정은 아니지만 A1과 연결되는 것

* B34 card는 A1·A2 결정을 받은 뒤 review_b34의 blocking 3건(B1 approval, B2 `Match` 비교 정규화, B3 test가 진입점을 본문에서 직접 호출)을 고쳐 다시 낸다. 이것은 오케스트레이터 몫이다.

---

## (B) Phase 3 착수 시 (조건: Phase 2 DoD PASS, B28 병합 완료)

| ID | 질문 | 왜 사용자 몫 | 선택지·결과(실측) | 권고 | 막는 것 / 언제 |
|---|---|---|---|---|---|
| **UD-0** | Phase 3 design(`draft_phase3_design_v4.md`) 승인. D-1~D-18 기본값과 문서 개정(N3.10 표, 533·534행, N3.12.3, 00-common 103·431행, 10 §5.6)을 함께 덮는다 | 계획서 표와 판정 문구 개정은 승인 대상(DEC-51) | 기본값 18건은 §9.3 표를 보면 된다 | 승인 | Phase 3 전체. A2보다 뒤에 |
| **UD-1** | U-03: 추적 안 된 `workspaces` 스크립트가 shim 삭제로 깨지는 것을 허용하는가 | 계획이 사용자 결정으로 지정했다(N7.2) | 추적 파일은 전부 F1에서 갱신한다. 깨지는 것은 추적 안 된 **1개**(`smoke_run_harness_session18_save.py`)다 | 허용(계획 기본안) | F1/F2 shim 삭제. Phase 3 착수 시 |
| **UD-5** | G1 게이트 변경(이동 인식) 승인 + 방식 선택 | 게이트 변경은 사용자 승인. 두 방식 모두 약화 금지를 만족하므로 비용 선택이 사용자 몫이다 | (가) 전역 이동 인식 규칙: 게이트 변경 1회, 거짓 거부 0, 반례 전부 거부. (나) 승인 기록에 선언된 이동만 인정: 게이트 변경 1회 + M card 8개마다 승인 1건. 선언이 이관표와 두 번 적힌다 | (가) | G1 → M card 전부. Phase 3 착수 시 |
| **UD-6** | T0 V5 승인(test 커밋 뒤 diff 해시로) | 기준 변경(DEC-40) | 판정 범위 확대 + 유일성 검사 추가, 기대값 불변, 죽은 상수 삭제 | 승인 | T0. **T0 test 커밋 뒤** |
| **UD-7** | D군 probe·진단 스크립트 8파일(대입 14줄) 처리 | probe를 둘지, 기능 범위를 어디까지 할지 | 기본안: F1에서 덮어쓰기 대상을 호출자 모듈 전부로 바꾸고 oracle 예외. 대안: '동작 안 하는 probe'로 표시만 | 기본안 | F1. **주의: v4 안에서 서로 다르다.** §9.2 표에는 UD-7이 남아 있고, §9.3 D-17은 기본안으로 흡수했다고 적었다. 대안을 원할 때만 답하면 된다 |
| **B33 Q1** | V7 호출 그래프 R2(생성자 간선)의 범위 + 게이트 변경 승인 `20260930-v7-registry-edges` | 게이트 변경 | (a) 호출 위치(`Cls(...)`·`raise Cls`)만: 팩토리 모양은 거짓 FAIL이 되고 면제 승인으로 드러난다. (b) 이름 참조 전부: `isinstance`·`except`만 쓰는 클래스가 거짓 PASS가 된다. HEAD 미도달 수는 두 안 모두 **39**(지금 비용 차 0). R1+R2+R3 적용 시 미도달이 115 → 39로 준다 | (a) | B33 card. G1과 같은 파일을 쓰므로 **B33 → G1 순서**를 권고한다. Phase 3 착수 전(G1 전) |

참고: 레지스트리 §7 보류 행(C의 U-A~U-D)을 Phase 3 D0b **전에** 정하면, 삭제로 정한 행은 옮기지 않아 이동 card 수가 준다(`prep_deferred_rows.md` §4).

---

## (C) Phase 4 착수 시 (`draft_phase4_design.md` v0.2 §7.1)

| ID | 질문 | 왜 사용자 몫 | 선택지·결과(실측) | 권고 | 막는 card |
|---|---|---|---|---|---|
| **UD-0(P4)** | Phase 4 design 승인. P-1~P-12 기본안과 계획 정정을 함께 덮는다 | DEC-51 | -- | 승인 | Phase 4 전체 |
| **UD-1 = D1** | 레일 극성(높은/낮은 레일)을 어떻게 정하나 | 회로 해석 규칙(공동분석) | (A) 구조 규칙만: 이관 0, 예외 회로는 막힌다. (B) 스키마 필수 선언: 9개 파일 수정 + 승인 기록. **(C) 구조 규칙 기본 + 예외만 `supply_roles`**: 9/9가 규칙으로 판정되어 파일 수정 0. CONFLICT·선언 모순은 거부하고 `supplies_v` 전압 순서와 대조한다 | (C). 원칙상 "극성은 항상 사람이 확정"을 우선하면 (B) | #17 B26-2, #19. B26-2를 Phase 3 전으로 당기면(조건부 pre) 그때 |
| **UD-2 = D2** | 소신호 MNA에서 선언 레일 전부를 교류접지로 두나 | 동작 변경 + 기준선 변경 | **(i) 예**: 바뀌는 metric은 current_reuse `cmrr_estimate_db` 73.145 → 73.380(**+0.235 dB**, 제약 ≥60 대비 여유 13 dB, 완화 방향) 하나이고 나머지는 차 0이다. 현재는 vdd가 CM 1 V당 28.3 mV 움직인다. (ii) 낮은 레일만: 오차가 그대로 남고, agnd 회로의 CL·Cc가 자유 노드가 된다 | (i) + DEC-40 기준선 승인 1건 | #18 B26-3 |
| **UD-3** | U-26 (a) `supplies_v` 값과 nmcnr 분할 레일 전환 시점 | spec 값 | two_stage·current_reuse·folded = `{vdd:1.8, gnd:0}`, nmcnr = `{vdd:0.9, vss:−0.9}`를 MG1에서 반영 | 그대로 | #21 MG1, #22, #44 |
| **UD-4** | U-04 픽스처와 정본 spec 구분 | 계획 지정(N7.2) | `origin: canonical \| fixture` 필수, 픽스처는 유도 임계값을 읽지 않음 | 계획 기본안 | #37 |
| **UD-5** | U-05 비단조 곡선 이분 역산 | 계획 지정 | 단조 구간별 근 전부 + 호출자 선택 규칙(DEC-11 확장), B24 (b)를 red 후보로 | 계획 기본안 | #31 |
| **UD-6** | U-09/I-C11 해소(two_stage stage1_out, nmcnr stage2_diode_ref) | 회로 해석·connectivity(WP-07) | Phase 4에서 connectivity 제안표를 받아 사용자가 확인한다. **제안표 준비 문서는 아직 없다** | 계획 기본안 | #43, #44 |
| **UD-7 = U-A** | theta 작성 묶음 4함수(`propose_theta_kcl_gap_fill` 등) | 회로 해석 규칙(WP-06) + topology 데이터 | **배선**: `load_topology`에서 제안을 계산하고 '검토 필요' 게이트를 둔다. DEC-62 경로가 지금 이것뿐이고, theta가 0인 회로가 5개다. 대안 **삭제**: 6a 전까지 새 회로 사이징 경로가 없어진다 | 배선 | C1, #19 B26-4 lint |
| **UD-8 = U-B** | `find_diode_stacks` 묶음 | ★ diode 정의(공동분석) | **삭제**: `is_diode` = gate==drain. 8/9 회로 결과 동일, current_reuse만 18 대 16(`M58`·`M63`). 대안: 6a '이웃 diode' 엣지 원형으로 유지 | 삭제 | 6a S1 |
| **UD-9 = U-C** | `find_differential_and_mirror_forks` | ★ diffpair/mirror 정본(공동분석) | **6a 공동분석까지 유지(비운영 면제)**: 운영 함수가 못 찾는 관계를 4회로에서 이 함수가 낸다. 대안 삭제: 유일한 검출이 사라진다 | 유지 | #19 B26-4 lint 면제 |
| **UD-10 = U-D** | `check_mirror_symmetry` 묶음 | 기존 승인 U-02 3항(삭제)을 번복하는 일 | **7b I-A13 바탕으로 배선**(7b까지 면제). 대안: U-02대로 삭제(test_ic5 V5 포함) | 배선 | 7b |
| **UD-11** | DEC-40 -- U-27 새 LUT | 기준 변경 | 목표는 옛 격자점(5 VS 점) 비트 동일이다. 다르면 원인을 보고하고 승인받는다. 재생성은 240조합 ≈22시간 | 결과가 나온 뒤 건별 | #27 |
| **UD-12** | DEC-40 -- U-30 교체(`W_bounds` 하한 1 µm → 0.42 µm, difftap.2) | 기준 변경 | 4회로 θ*·floorplan이 바뀐다. 영향 후보: folded M3·M4 1.017 µm, nmcnr M202 1.02 µm | auditor 비교표를 받은 뒤 건별 | #29 |
| **UD-15 (B36)** | analog-grammar의 소속과 게이트 편입 | skill 경계·공유 설정, 판정 표 개정 | **(a) 별도 skill + gmid 게이트 범위 편입**: N3.12.2 행 추가, 게이트 도구 6개. (b) analog-gmid-design으로 흡수: 단독 CLI 삭제나 DUP를 감수해야 한다. 어느 쪽이든 `plan_tables` 승인과 게이트 변경 승인 2건이 필요하다 | (a) | #46. 단독으로 앞당길 수 있다. B35를 확장안으로 하면 B35의 착수 조건이 된다(아래 알림 2) |

(UD-13·UD-14는 A1·A2와 같은 결정이라 여기서 뺐다.)

---

## (D) 사용자만 할 수 있는 작업

| 작업 | 이유 | 시점 |
|---|---|---|
| `install.py`의 `SKILLS`에 `"analog-grammar"` 추가 | EL1이 Claude의 쓰기를 거부하는 사용자 경로다. 지금 설치본은 늘 B34 폴백으로 돈다. B34 뒤에는 이것이 없으면 조용히 틀리는 대신 **명시적으로 실패**한다 | B34 병합 전후(가능하면 병합 전) |

---

## 알림(기본안) -- 묻지 않음, 원칙으로 정함

| 항목 | 기본안 | 근거(파일) |
|---|---|---|
| B34 폴백 제거 | analog-grammar는 필수 의존이고, 없으면 명시적 `ImportError`를 낸다 | 조용한 폴백 금지(`prep_b34_b35_grammar.md` §3.1, P-10) |
| V3 면제 id를 def 해시·card에 묶기 | 강화(누수 619건 차단). 다만 게이트 변경이라 A1의 승인에 들어간다 | `v3_scope_systemic.md` §4 |
| 인벤토리를 빠른 test부터 실행, 병렬화 | 판정 불변 | 같은 문서 |
| E4 1·2항(스크립트 출처, `-B -P`) | 절차 명확화 | `draft_e4_clarify.md` |
| Phase 3 D-1~D-18, Phase 4 P-1~P-12 | UD-0으로 확정 | 각 design §9.3 / §7.2 |
| U-30 `min_finger_w` = 0.42 µm | 계획이 이미 닫았다. 사용자 몫은 결과 승인(UD-12)뿐이다 | `prep_u27_u30.md` §4.1 |
| B33 R1·R2를 V3와 공유하는 `build_graph`에 둠 | 스펙('같은 그래프')에서 정해진다 | `draft_b33.spec.md` |
| 정보: `max_finger_w` 40 µm > 모델 bin W 상한 7.0 µm | 값은 바꾸지 않는다. 결정이 필요하면 원할 때(7a SPICE 대조) | `prep_u27_u30.md` UD-c |
| 백로그 B38: gate master의 instance.json 2개가 낡음 | 재생성은 기준선 변경(DEC-40)이라 그때 승인. 지금 결정 아님 | `draft_e4_clarify.md` |

**초안 간 불일치(오케스트레이터 정리 필요, 사용자 결정 아님)**:
1. Phase 3 v4의 UD-7: §9.2 표에는 남아 있고, §9.3 D-17에는 흡수했다고 적혀 있다.
2. B35 처리 방식이 서로 다르다.
   * Phase 4 v0.2 P-11: B26-2의 SD 호출부 어댑터.
   * `draft_b26_1.spec.md` 48~51행과 `prep_b34_b35_grammar.md` §3.2: 어댑터를 기각하고 analog-grammar 확장((1))을 택했다.
   * 확장안이면 UD-15(B36)가 B35의 착수 조건이 된다.
