# 사용자 결정 패키지 v2 (2026-10-01, gate master `a796468` 기준)

한눈에 보기: **결정 완료 11건** · **지금 필요 2묶음(B26-1 U3~U5, Phase 3 4건)** · **Phase 4 착수 때 약 15건** · **사용자 작업 2건**.
원천: `user_decisions.md`(결정의 정본), `git log gate/master`, 각 초안 파일(아래 '파일' 열). 옛 판(9-30, `7535799`)은 `decision_package.v1.md`.
카드 순서(사용자 지정): P10 → P10b → **Phase 2 DoD** → V3 면제 묶기 → V3 범위 정책 → B34 → **B26-1** → B33 → **Phase 3**(G1·T0·D0a…) → … → Phase 4.

---

## 1. 결정 완료

| id | 한 줄 내용 | 날짜 | 기록 위치 / 커밋 |
|---|---|---|---|
| E1 정정 | P9: design 20 E1·§6.2·§8 P9 행 정정(P9 = `kcl_series_union` 중복 엣지만 정본 호출로) | 09-30 | 설계 `6398a28`, 승인 `20260930-p9-e1-correction`(`ab90ec5`) |
| topology 주석 보류 | current_reuse 1250·1281·1872, nmcnr 74 주석 정정은 보류 | 09-30 | 백로그 B29(gate `.ai/context.md`) |
| D1 | Phase 2 E4 기준값 = da03c0e 대 Phase 2 마지막 병합본 같은 경로 비교 | 09-30 | 설계 `2140da8`, 승인 `20260930-phase2-e4-baseline`(`b7d2570`) |
| D2 | P3c 보류분은 추가 card 없이 E2 문구대로, DoD '남긴 관찰'에 기록 | 09-30 | 승인 불필요. Phase 2 DoD 기록에 적을 몫 |
| A2 | DEC-60 넷 전환기 종료 + DF-19·26 넷 몫 MG1 분리 + B26-1·B34를 Phase 3 전에 | 10-01 | 승인 `20260930-b26-before-phase3`(`2d58fd8`), 계획 정정 `8356c1e` |
| A3 | E4 PT = `--gmid-phase=2` + `--gmid-dod` 두 실행 | 10-01 | 설계 `fe638ab`, 승인 `20260930-phase2-e4-phase`(`2d58fd8`) |
| A1-a | V3 면제 = 변이 id@함수 원본 해시, 해시 같을 때만 적용(강화) | 10-01 | 승인 초안 `approval_20260930-v3-exempt-binding.md` -- **gate 미커밋**(card 커밋 뒤 rev-parse로 채움) |
| A1-b + 정정 | V3 범위 N2(바뀐 문장+제어문+삭제 주변+새 def 전체+early_return), 정정: T6 = 같은 블록 뒤쪽에서 바뀐 이름 읽는 문장 전부. **약화 승인** | 10-01 | 승인 초안 `approval_20260930-v3-changed-stmt-scope.md` -- **gate 미커밋** |
| B33 | V7 레지스트리·생성자 간선 게이트 변경(미도달 115 → 39, 인벤토리 1.31배) | 10-01 | 승인 초안 `approval_20260930-v7-registry-edges.md` -- **gate 미커밋** |
| B33 Q1 | 생성자 간선은 호출 위치(`Cls(...)`·`raise Cls`)만, 팩토리 모양은 면제 승인 처리 | 10-01 | 같은 기록 범위 설명 |
| (참고) B28 | V3 이력 복제본 게이트 변경 -- `user_decisions.md`에는 없고 gate에 기록만 | 09-30 | 승인 `20260930-v3-history-clone`(`ab90ec5`) |

---

## 2. 지금 필요한 결정 (다음 card를 막는 것, 순서대로)

### 2-1. B26-1 U3·U4·U5 -- B26-1 착수 전 (질문 문안 **아직 없음**: `b26_1_survivor_question.md` 준비 필요)

| 항목 | 질문 | 선택지 | 권고 | 막는 것 | 파일 |
|---|---|---|---|---|---|
| **U3** | 계획한 계약으로도 죽지 않는 V3 대상 변이(기존 동작: finger growth, euler fixup, LUT 없는 repair, 바뀐 호출 뒤 문장)를 어떻게 처리하나 | (1) 앞선 test-only card로 기존 동작 test를 먼저 보강·병합 / (2) def 해시에 묶은 decision 면제(A1-a 규칙, **판정 약화**) | **(1)** -- 약화 없음, test가 실제 동작에 배선됨 | B26-1 착수 조건 8 | `draft_b26_1.spec.md` '결정 필요 항목' U3 |
| **U4** | A2 범위에 B40(gate 없는 입력 반환에서 `unavailable_reason` 키 삭제 = 관찰 가능한 출력 변경)을 더하나 | 추가 승인(decision) / 안 받음 → B40을 card에서 빼고 백로그 | 추가 승인 | 착수 조건 10 | 같은 곳 U4, `review2_b26_1.md` M2 |
| **U5** | P9 계약 test 2개의 시그니처 단언 갱신(V5, `target_kind: diff`) | 승인 / 거부 | 승인(기대값 의미 불변, 매개변수 원소만 늘어남) | 착수 조건 9(test-author 착수 전) | 같은 곳 U5 |
| (조건부) | 기존 픽스처에 `supply_nets`·`rails=` 추가를 `weakening_diff`가 표시하면 V5 승인 | 발생 시 | -- | B26-1 병합 | 같은 card '작성 전 실측' 7 |

### 2-2. Phase 3 design 승인 4건 -- 지금 물을 수 있음, phase 3 card 병합은 Phase 2 DoD 뒤 (문안 준비 완료)

| 항목 | 질문 | 선택지 | 권고 | 막는 것 | 파일 |
|---|---|---|---|---|---|
| **UD-0** | design `30-module-split`(10모듈 분할, card 16건) + 문서 개정(N3.10 표·534행·N3.12.3·00-common·10 §5.6) 승인. 기준에 닿는 기본값 **D-9**(판정 기록 증거 스크립트·`probe_stage_partition.py`는 import 갱신 안 함, 기록 커밋에서만 재실행) · **D-17**(probe 8개 대입 14줄을 새 모듈로, "import 줄 외 동일" 검사에서 그 줄만 제외) 포함 | 승인 / 승인 + 추가 표 개정 위임 / 수정 요청((a)·(b) 지정) / 보류 | **승인**(추가 표 개정은 나오면 다시 묻기) | Phase 3 전체 | `phase3_approval_question.md`, `draft_phase3_design_v6.md`, `p3_doc_amendments.md` |
| **D-19** | B26-1이 만드는 `rail_declaration`을 둘 모듈 | (가) MOD2 `topology_authoring`(선언 검사 함수들과 같은 곳, B37a `port_declaration`도) / (나) MOD3 `circuit_state_graph`(유일한 호출자 옆) | **(가)** | N3.10 MOD2 행 문안, Phase 4 #47 모듈 | 같은 질문 문안 |
| **UD-5** | 게이트 변경 G1(옮긴 정의를 새 정의로 안 봄, V3·V6·V7) 승인과 방식 -- 둘 다 약화 없음 | (가) 전역 이동 인식 규칙(1회) / (나) 승인 기록에 선언한 이동만(M card 8건마다 승인 1건) / 보류 | **(가)** | G1 → M card 전부(이동 card는 지금 변이 ~1.6만 개로 판정 불가) | 같은 문안, `draft_p3_g1.spec.md` |
| **UD-1** | U-03: 추적 안 된 `workspaces/smoke_run_harness_session18_save.py`가 shim 삭제로 깨짐 | (가) 깨지게 둠 / (나) 지금 추적 추가 + F1에서 갱신 / (다) 삭제(사용자 작업) | **(가)**(계획 기본안) | F1/F2 shim 삭제 | 같은 문안 |

답을 받은 뒤 기록: UD-0·D-19 → `20260930-30-module-split-design`(diff), UD-5 → `20260930-p3-gate-move-aware`(diff), UD-1 → design 기록 범위 설명.
뒤에 올 것(지금 아님): T0·T1·F1 V5 승인(test 커밋 뒤), D0b가 계산하는 추가 N3.10 개정.

---

## 3. Phase 4 착수 때 결정 (`draft_phase4_design.v05.md` §7)

### 3-1. 회로 해석 공동분석 -- UD-17a~e (`ud17_coanalysis_pack.md`, 기본안 없음)

| 항목 | 질문 | 선택지 | 판단 자료 | 막는 card |
|---|---|---|---|---|
| **UD-17a** | folded M1·M2 선언 | (1) kind → nmos / (2) pmos 유지 + source↔drain 교환 / (3) 원문이 pmos 입력 → 여러 소자 거울상 연결 | tail에서 KCL 불가, 연결 패턴은 NMOS 입력 폴디드 전형. **새 발견: (1)·(2)로 극성(0.4 V)만 고쳐도 X·Y 충돌이 1.2 V로 남는다** -- tail 컬럼 KVL 공백(vds 합 0.6 대 VDD 1.8)이라 **UD-17c의 입력 CM 선언 없이는 F26·F27 해소 안 됨** | #53 |
| **UD-17b** | `kcl_fold_M5`·`M6` 부호(I6 = I3 − I1?) | UD-17a 답에서 KCL로 유도 | 교과서형이면 I6 = I5 = 0.5 µA(지금 1.0) → M5~M10 재계산 | #53 |
| **UD-17c** | folded 컬럼 공백(tail 1.2 V, Y 0.5 V, out 1.0 V)을 어디서 정하나 | (i) `bias3`·출력 CM·**입력 CM** 선언(새 필드 + 엔진 해석, 승인) / (ii) 엔진이 fold_group 컬럼 KVL 풀이(외부 DC 없으면 해가 하나로 안 정해짐) / (iii) 두고 SEAL_VIOLATION으로 멈춤 | 지금 선언할 필드 없음(`ports`에 DC 값 없음) | #53 갈래 |
| **UD-17d** | current_reuse Vom1·Vop1 DC를 무엇이 정하나 | (i) 출력단 VGS 0.677 V(컬럼 분할 선언) / (ii) 컬럼 0.9 V(M16·M26 VGS 변경) / (iii) 다른 것(CMFB 등) | **(i)이면 아래 반쪽 최소합 0.9 V > 0.677 V → M5 vds 0.027 V, 꼬리 M5 triode** = 설계 변경 필요. M2a·M2b vsb 0.9227이 진짜 축 밖이 되어 UD-17e 질문이 번짐 | #54, DoD E3·E8 |
| **UD-17e** | M9a·M18a(그리고 M2a·M2b) bulk | (i) vdd(지금 가정, vsb 0.825 축 밖, 오차 0.7 %) / (ii) 자기 source(n-well) | **두 json 모두 `bulk` 필드 없음 -- 엔진은 레일 bulk(NMOS=gnd, PMOS=vdd)를 가정**. (ii)는 connectivity(사용자) + 엔진 배선 card | #54, #22 |

### 3-2. 그 밖의 Phase 4 결정

| 항목 | 질문 | 권고(기본안) | 막는 card | 파일 |
|---|---|---|---|---|
| **UD-0(P4)** | Phase 4 design 승인(P-1~P-32 + 계획 정정 §9) | 승인 | Phase 4 전체 | v05 §7.2·§9 |
| **UD-18** | B37a Q1 동작 변경 수용(3회로 자동 채움 소실·그룹 변화) / Q2 `ports` 선언 확인(ngcc·sf_pushpull·two_stage_ota_sf·pushpull·common_gate) / Q3 sf_pushpull 그룹을 계약 test로 고정(대안 = 비등가 변이 면제 = 약화) | Q1 수용, Q2 표대로 확인, **Q3 고정** | #47 | `draft_b37a_approval_question.md` |
| **P4-UD-1** | 레일 극성 | (C) 구조 규칙 + 예외만 `supply_roles`(9/9 규칙 판정, 파일 수정 0) | #17, #19 | `b26_decision_table.md` |
| **U-26 (a)** | `supplies_v` 제안표 확인(two_stage·current_reuse·folded `{vdd 1.8, gnd 0}`, nmcnr `{0.9, −0.9}`) | 확인 기록(질문 아님) | #21 | v05 §7.3 P-14 |
| **U-04** | 픽스처/정본 spec 구분 | `origin: canonical \| fixture` 필수 | #37 | 계획 1079행 |
| **U-05** | 비단조 곡선 이분 역산 | 단조 구간별 근 전부 + 호출자 선택 규칙 | #31 | 계획 1080행 |
| **U-09 (UD-6)** | I-C11 해소 | #43 실패 명시화는 무조건. nmcnr는 (C) topology 정정부터, two_stage는 (A) DEC-70 Phase로 이관 | #44, E2 | v05 §11 |
| **U-A** | theta 작성 묶음 4함수 | 배선 | C1, #19 | `prep_deferred_rows.md` |
| **U-B** | `find_diode_stacks` | 삭제(current_reuse만 18 대 16 차이, ★diode 정의 공동분석) | 6a S1 | 같은 곳 |
| **U-C** | `find_differential_and_mirror_forks` | 6a 공동분석까지 유지(면제) | #19 | 같은 곳 |
| **U-D** | `check_mirror_symmetry` | 7b I-A13 바탕으로 배선(기존 U-02 삭제 승인 번복) | 7b | 같은 곳 |
| **UD-15 / B36** | (1) analog-grammar 소속·게이트 편입 (2) B35 방식 (3) mid 레일 grammar 매핑 | (1) 별도 skill + gmid 게이트 편입 (2) X analog-grammar 확장 (3) 공동분석 -- 선언 레일은 `RAIL_Z`, 라벨은 hi/lo만 | #46·#17·#49·#19·#52 | v05 §7.1 비교표, `prep_b34_b35_grammar.md` |
| **DEC-40 기준선**(발생 시 건별) | U-27 새 LUT 옛 격자점 차이(UD-b), U-30 `W_bounds` 하한 1 → 0.42 µm로 바뀌는 θ*·finger(UD-a; folded M3·M4, nmcnr M202), current_reuse `cmrr_estimate_db` 73.145 → 73.380, #53·#54 topology 변경 결과 | auditor 비교표 받은 뒤 승인 | #27, #29, #18, #53·#54 | `prep_u27_u30.md` §4.1, v05 §7.4 |
| **#53·#54 topology 수정 승인** | UD-17 답 뒤 library json 수정(쓰기 경로 WP-07·U-16) | UD-17 답에 따라 | #53, #54 | v05 §7.3 |

### 3-3. 백로그 중 사용자 확인이 필요한 것 (B39~B47은 아직 gate 백로그 미반영 -- `backlog_additions.md`)

| 항목 | 확인할 것 | 시점 |
|---|---|---|
| **B47** | 낡은 추적 파일 `library/folded_cascode.topology.md`(M1/M2 gate가 json과 반대) 재생성 커밋 승인 + 다른 library md 일치 여부 확인 | UD-17 공동분석 전이 좋음(표를 헷갈리지 않게) |
| **B36** | = UD-15 (1). B35를 확장안으로 하면 B35 착수 조건 | Phase 4(단독으로 앞당길 수 있음) |
| B39 | 사이트 4 등가 생존 변이(`>= 2`→`>= 1`) 면제 승인 | B39 처리 card 때 |
| B29 | 보류된 topology 주석 정정을 언제 풀지 | 사용자가 원할 때 |

---

## 4. 사용자 작업 (Claude가 할 수 없음)

| 작업 | 이유 | 시점 |
|---|---|---|
| `install.py` `SKILLS`에 `"analog-grammar"` 추가(27~29행) | 쓰기 경로 N3.12.2 '사용자'. 없으면 B34 뒤 설치본이 **명시적 ImportError**로 실패(지금은 조용한 폴백) | **B34 병합 전후, 가능하면 전** |
| 원본 회로도로 UD-17 체크리스트 확인 | connectivity·kind·bulk는 사용자만 고침. 넷 단자 목록을 회로도와 한 넷씩 대조(folded: Maloberti p.34~38, current_reuse: Vom1·Vop1·CMFB·bulk) | Phase 4 #53·#54 전 (`ud17_coanalysis_pack.md` §5) |
| (UD-1 (다)를 고를 때만) `smoke_run_harness_session18_save.py` 삭제 | 추적 안 된 사용자 파일 | Phase 3 F2 전 |

---

## 5. 알림 -- 원칙 기본안 (묻지 않음)

| 항목 | 기본안 | 근거 |
|---|---|---|
| Phase 3 D-1~D-25(D-9·D-17·D-19 제외) | UD-0이 덮음. 코드 배치·판정 절차, 회로 해석 없음 | design 30 §9.3 |
| Phase 4 P-1~P-32 | UD-0(P4)이 덮음. 새로 P-26~P-32: 클램프 거부 계획대로, 충돌 노드에서 vsb 유도 금지(SEAL_VIOLATION), 축 밖 오류 고유 클래스, 선형 외삽 불가, VS 상한 1.8 V, IC11 우선순위 current_reuse → folded | v05 §7.2 |
| B34 | 새 승인 불필요(A2가 덮음, V3·V7 면제 0) | `b34_commit_plan.md` §1 |
| B37a 형식 규칙 | `ports` 누락·형식 오류·모순 거부, `ports: {}` 수용, '출력은 포트만'은 B37b 결정으로 | `draft_b37a_approval_question.md` §2 |
| U-30 `min_finger_w` = 0.42 µm | 계획이 닫음. 사용자 몫은 결과 승인(DEC-40)뿐 | `prep_u27_u30.md` §4.1 |
| 정보: `max_finger_w` 40 µm > 모델 bin W 상한 7.0 µm | 값 유지, 결정은 원할 때(7a SPICE 대조) | 같은 곳 UD-c |
| U-27 VS 간격 0.2 V | 유지, 보간 오차 기록 → 백로그 B51((v0.9.2 번호 정정) 옛 제안 번호 B48은 오케스트레이터 백로그 B48(test_lint 빈 컨테이너 오탐)과 겹쳐 B51로 -- Phase 4 design §9-12) | v05 P-5 |
| `_metric_kcl_residual` 이름 직접 호출 test | 어느 안이든 추가(인벤토리 0 → 1) | `draft_b26_1.spec.md` V3 계획 4 |

**초안 간 정리 필요(오케스트레이터 몫, 사용자 결정 아님)**: `draft_phase4_design.md`와 `.v05.md`는 내용이 같다(cmp 동일) -- 둘 다 v0.5. A1-a·A1-b·B33 승인 기록 3건은 아직 gate에 없다(해당 card 커밋 때 rev-parse 채워 커밋).
