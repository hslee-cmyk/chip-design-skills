# card·design 낡음 감사 -- O-186·O-187·O-188 기준 (2026-10-30)

- 역할: card·design 낡음 감사자(감사만). card·계획·design·git 쓰기 0. 이 파일만 Write.
- 기준(결정 원문): `wt/_drafts/user_decisions.md` 마지막 세 행 O-186(Q-TH1 (A)·(L2)), O-187(Q-KV1 일괄 + r2r (i)), O-188(bulk 미선언 = kind별 레일 기본, DEC-61 확인). 영향 목록: `evidence/2026-10-30/plan_v6385_approval_items_v4b.md` §1.8·§1.9·§2.8·§3, 보조 `evidence/2026-10-29/plan_v6385_design_impact2.md`(DI2, K1~K22 -- design v1.15.3 HEAD `792cd0bd` 기준), `evidence/2026-10-30/gmid_multiroot.md` §5.2·§5.3(MR).
- 형식·분류 어휘: `evidence/2026-10-29/card_audit_{A,B,C}.md`(master `1b1f2eac` 병합)를 따른다.
- 계획 v6.38.5(`wt/plan-v6385`, HEAD `8bcdde3a`)는 작성자가 반영 중이라 판단 기준에서 뺐다. 읽은 곳은 TB-1·IT-1+IT-2 행(병합 순서 사실 확인)뿐이다.
- 엔진 코드는 읽지 않았다. design·card 본문의 엔진 줄 인용은 원칙 8에 따라 판정 근거로 쓰지 않았다(재작성 범위 기록으로만).

## 0. 실측 방법

- card 대상: master `docs/02-design/specs/` 94 파일(`_TEMPLATE` 제외) = 단위 48(card 47 + `20261021-it2-common.md`).
- design 대상: master `docs/02-design/features/gain-budget-gmid-sizing.*.design.md`(40·41 = v1.14.2, `plan_version: 6.37`)와 `wt/design-v115`(브랜치 `design/v115` HEAD `ef573444`, 40·41·42 = v1.15.3, master 미병합 30커밋).
  - `git -C wt/design-v115 diff --stat 792cd0bd HEAD -- docs/02-design/` = 0 → DI2 줄 번호가 지금도 맞다(실측). DI2의 K-행 가운데 40:449·462·1107·1122·1780·1913·2162·2174·2193, 41:644·874·880·882·1406·1521·1698·1703·1722·1759~1763, 42:67·134·267·311을 직접 열어 문언을 재확인했다.
- grep 묶음(카드·design 모두): `가장 큰 VGS|largest|rightmost|vgs_for_gm_id|vgs_root|역산|gm/ID 축|gm/ID_lo|start.row|일대일|gm/ID 큰 쪽|U-51|U-124|U-126` / `같은 gm/ID|ID, gm/ID, L|ConservedPoint|ly_point|slice_density|W_need|J_slice|DEC-84|DEC-89|LY1` / `J12|M21|M22|OrderHints|order_hints|R13|DEC-95 (3)|DEC-104 (3)|이름 키|tie-break|정준 라벨|S/B/F/X|(X)` / `bulk|벌크|body` × `미선언|누락|결함|정정|기본`.
- card 상태: `.ai/verification/<id>.json` 유무(master 트리·`git ls-tree integ/it12`), `git log --oneline master --grep=<id>` / `--all --grep=<id>` 커밋 수, `git merge-base --is-ancestor`.
- 진행 중 작업: `git worktree list` = 4개(master·`wt/design-v115`·`wt/integ-it12`·`wt/plan-v6385`). `integ-it12`·`design-v115`의 `.bkit` 밖 미커밋 0. it2 역할 브랜치(`role/code/it2a`·`it2b`·`spec/it2`·`design/it2c-o79`)는 모두 `integ/it12`에 들어 있음. `card/it2c`(IT-2c 재동결본) 마지막 커밋 2026-10-24, 코드 0.
- 그 밖 design(offset-strategy·offset-trim·oracle-portability·analog-topology-json-library·gain-budget 00/05/10/20/30) 같은 grep = 0건.

## 1. 분류 집계

| 판정 | 수 | 대상 |
|---|---|---|
| 그대로 | 46 | 옛 card 40개(20260921~20261001, 상태 표지 있음, O-186~188 낡은 문언 0), `20260923-probe-promote-differential`(표지가 '현행 규칙 아님'을 이미 말함 -- 덧붙임은 선택), `20261021-it0-baseline`(측정 기록), `20261021-it2a`·`it2b`(기록, 해당 문언 0), `20261021-it2c`·`it2d`(자체 파일 0건 -- 공통 문서 경유 조건부는 it2-common 행) |
| 상태 표지 후보(실행 완료 기록) | 0 | 새로 달 표지 없음(아래 3·4 행은 이미 '대체됨·재동결 필요' 표지가 있음) |
| 내용 개정 필요(착수 전 card -- 재동결 때, 계획 병합 뒤 착수 조건) | 2(조건부) | `20261021-it2-common`(서명 불변 줄 `order_hints` -- it2c·it2d가 이 절을 씀), `20261021-it1-input-tie-removal`(재동결 때 `order_hints` 서명·종속 멤버 기대값) -- 둘 다 **TB-1과의 병합 순서 의존**(불확실 U1) |
| 즉시 정지·보고(진행 중 card) | **0** | 진행 중 card 구현·test·판정 worktree 없음(위 0절 실측) |
| design 개정 필요 | design/v115 40·41·42 -- 항목 45개(3절) | Q-TH1 (A) 25, (L2) 4, Q-KV1 16(DI2 K1~K22 중 재확인분 + O-187 최종 문언 갱신), O-188 0 |

- TB-1·LY1·MOD7·MOD8·DE-1·LA-1·EO-1·GL-1·(A) 재작성 card에는 **spec card 파일이 없다**(specs 폴더 최신 = `20261021-*`; spec card·interface card 절차는 폐기 -- `card_audit_A.md` §2 근거 P 119~121). 이 card들의 낡은 문언은 전부 design 40·41·42 안 절에 있다 → 3절.
- O-188(bulk 미선언 = 레일 기본): card·design에 미선언을 결함·누락으로 다루는 문언 **0건**. design은 이미 DEC-61과 같다(40:1875 '`bulk 기본 규칙(NMOS = 최저 레일, PMOS = 최고 레일)은 유지`', 41:603, 42:106 '61 벌크 기본값 OK'). card 쪽 걸린 것은 `20261001-topology-md-sync.spec.md:181`의 조사 기록 '(body·bulk 없음)'뿐 -- 사실 기록이라 그대로.

## 2. card별 표 (그대로가 아닌 것 + 경계 사례)

| card | 상태 실측 | 판정 | 낡은 문언(파일:행 인용) | 어긋나는 결정 |
|---|---|---|---|---|
| `20261021-it2-common` | 판정본 = `integ/it12`(it2a·it2b 판정 기록 `.ai/verification/20261021-it2a-snapshot-derive.json`·`-it2b-kernel-window.json` -- `git ls-tree integ/it12`), master 미병합(`integ/it12` master 대비 95커밋 앞). IT-2c·IT-2d 몫은 미구현(판정 기록 0, `--all --grep` 0). 머리 '[대체 표지 2026-10-29] … 재동결 필요' 있음 | 내용 개정 필요(조건부) | master `:255`, `integ/it12` `:259`, `card/it2c` `:276` 모두 "서명 불변 진입점(행동 red를 맡는 자리): `dc_writer_plan(snapshot, target_nets, input_dc_declared, order_hints=NO_ORDER_HINTS)`" | O-187 '옛 OrderHints 삭제(card TB-1)'. TB-1이 IT-1+IT-2 통합 병합보다 먼저 master에 들어가면 이 줄은 낡는다. 계획 v6.38.5 TB-1 행(1250, 읽기만)은 'IT-1·DR-1과 같은 통합 병합 금지, 나중 card가 rebase' -- 선후가 고정돼 있지 않다 → 불확실 U1 |
| `20261021-it1-input-tie-removal`(spec·interface) | `integ/it12`에서 판정 PASS(판정 기록 `integ/it12:.ai/verification/20261021-it1-input-tie-removal.json`), master 미병합, master `--grep` 1·`--all` 13. 머리 '[대체 표지] 대체됨 -- 현행 계획 card IT-1(범위 재작성) + card 0 IT-0b, 재동결 필요' | 내용 개정 필요(재동결 때, 조건부) | interface `:15`·spec `:77` "서명 불변 진입점: `dc_writer_plan(…, order_hints=NO_ORDER_HINTS)`"; interface `:28` "포트 경로가 둘 이상인 v1 고리는 … 그 고리 멤버 하나가 `cycle_vgs` 종속이다"(어느 멤버인지는 현 as-built 키를 따른 손계산 기대값 -- spec `:63` T-a '종속 목록 = 손계산') | O-187: 종속 멤버 = 고리 B 멤버, B 안 순위 diode → 대칭 궤도 대표 → 소스 사슬 하류 → DEC-97 정준 라벨(이름 키 철회), OrderHints 삭제. 재동결본이 TB-1 앞에 병합되면 기대값은 옛 규칙, 뒤면 새 규칙 -- 불확실 U1. 범위 밖 판단: interface `:27` W4 뿌리 '(구조 색, 이름) 최소'는 고리 종속 멤버가 아니라 쓰기 나무 뿌리 규칙이라 O-187 대상으로 보지 않음(불확실 U2) |
| `20261021-it2c-icm-config`·`20261021-it2d-refine-front` | 미구현(판정 기록 0, `--all --grep` 0). 머리 '[대체 표지] 대체됨 -- 재동결 필요'. 재동결 진행본 `card/it2c` `d95c8ff8`(2026-10-24, 코드 0) | 그대로(자체 파일) / 공통 문서 경유 조건부 | 자체 파일의 O-186~188 낡은 문언 0. `card/it2c` it2c spec `:59`·`:114`는 `device.bulk` READS -- DEC-61 기본과 같아 O-188과 맞음 | -- (it2-common 행 참조) |
| `20260923-probe-promote-differential` | 판정 기록 master `.ai/verification/…json` 있음, master `--grep` 2. 머리 '[상태 표지 2026-10-29] 실행·병합 완료 기록 -- 현행 규칙·절차 아님' | 그대로(덧붙임 선택) | interface `:15` "> 목표 gm/ID를 만족하는 **가장 큰 VGS 해**(rightmost root)를 격자 위에서 찾는다." (옛 `sizing_recipe._solve_vgs` docstring 인용) | O-186 '가장 큰 VGS 해' 규칙 철회. 표지가 이미 현행 아님을 말하고 산출물은 O-180으로 지워짐(+O180 덧붙임). 원하면 표지 끝에 "'가장 큰 VGS 해' 규칙은 철회됐다(O-186 -- θ 역산 키 = ln IDu)." 한 문장 |
| `20261021-it0-baseline` | `integ/it12` 판정 기록 있음 | 그대로 | `:38` M-I1 '종속 소자 목록·분류 … 덤프' -- 측정 기록 | -- |
| 나머지 40개(gate·ts·ic·probe·d·b26·df·v3·dup·p9·p10·registry·restore·topology-md-sync·rejudge-cache·caa970b·sections-major-merge·v4-decision-exempt 등) | 1b1f2eac 표지 있음(83 파일 중 표지 문자열 포함) | 그대로 | O-186~188 grep 0 | -- |

## 3. design 개정 목록 (대상 = `wt/design-v115` v1.15.3; master v1.14.2에도 같은 문언이 줄 번호만 달리 있음)

판정 어휘: **개정** = 결정과 정면으로 어긋남 / **개정(문언)** = 결정 취지는 같고 용어·표기만 낡음 / **확인** = 결정 문언만으로 개정 여부가 갈림(불확실 칸).

### 3.1 Q-TH1 (A) -- θ 독립 좌표·역산 키 = ln IDu, gm/ID = 순방향 조회 필드(writer 하나), ID = max(gm_req/g(ln IDu), R8), 남는 gm/ID 부등식 = 순방향 제약 행, '가장 큰 VGS 해' 철회

| # | 자리(v115) | 낡은 문언 | 판정 | master 대응 |
|---|---|---|---|---|
| T1 | 42:63 | "`11 가장 오른쪽 근 \| -- \| OK \| E/lut/vgs_root.py:17`" | 개정(규칙 철회 → 상태 OK가 아니라 재작성 범위) | 42:62 |
| T2 | 41:564 | "새 엔진 좌표는 쓰기 소자 ln IDu(DEC-88)이고 **강반전 분지에서 gm_id와 일대일**이라 rank가 같다" | 개정(▲DOF 653 사실 정정: pfet 혹은 중간 반전에 있어 일대일 전제 깨짐) | 41:590 |
| T3 | 41:514 | "자유 축: S∪F 소자의 같은 VGS 묶음 VGS 축(**= gm/ID 축**)" | 개정(다가 좌표 → 축 동일 진술 틀림) | 41:540 부근 |
| T4 | 41:516 | "값은 S0 수준 필드 `start.row`(**gm/ID·L**) … VGS는 **`vgs_for_gm_id`로 구하고**" | 개정(B 고정값 역산 = gm/ID→VGS) | 41:542 |
| T5 | 41:868~892 §5.3.3 '(a) gm/ID 역산' | 870 "P: '(a) 필요 gm에서 `gm_id = gm / ID` 역산'", 887 "S 소자의 역산(ID 기지)이 실패하면 … `gm_id_out_of_interval`", 889 "VGS는 `lut.vgs_for_gm_id`(gm/ID 역산 지표 tol_V (i), N3.6)로 구한다" | 개정(역산 대상 → ln IDu, ID = max(gm_req/g(ln IDu), R8) 순방향) | 41:930 등 |
| T6 | 41:846 | "결정 \| S·F 소자 gm/ID(θ 좌표는 ln IDu, DEC-88)" | 개정(문언 -- 결정 변수를 ln IDu로, gm/ID는 파생 필드) | 해당 절 |
| T7 | 41:891 | "matching 그룹 … 묶인 S·F 소자는 **gm/ID 축 하나**" | 개정(문언 -- 축 = ln IDu) | 해당 절 |
| T8 | 41:989 | "VGS는 `vgs_for_gm_id`로 구한다"(§5.3.7 L 목표) | 개정 | 41:1023 |
| T9 | 41:992 | "gm/ID 범위: 동치류 멤버의 §6 출발 구간 [gm/ID_lo, gm/ID_hi] 안의 LUT gm/ID 점" | 개정(격자 축) | 해당 절 |
| T10 | 41:1000 | "diode 멤버는 VDS = VGS(gm/ID, L)로 계산한다" | 개정(VGS(ln IDu, L) 순방향) | 해당 절 |
| T11 | 41:1019 | "자유·폴백 후보: S 자유 축과 F 폴백 축의 **gm/ID 격자**" | 개정 | 해당 절 |
| T12 | 41:1238 | "신규 `layer0_inverse.py` \| (a) gm/ID 역산(`lut.vgs_for_gm_id`, §4.1 분류)" | 개정(재작성 범위 표) | 41:1279 |
| T13 | 41:1270 | "DEC-71 (4)(a) \| gm_id = gm/ID 역산 \| §5.3.3" | 개정(대응표) | 해당 표 |
| T14 | 41:1319 E9 | "A^L0 축 규칙: (S∪F) **gm/ID** + L 전부 …" | 개정(문언) | 해당 표 |
| T15 | 41:471~472 §4.1 | "단조 \| 역산 허용(`vgs_for_gm_id`, `vgs_for_current_density`)" | 개정(`vgs_for_gm_id` 역산 소비 삭제 -- `vgs_for_current_density`는 유지) | 41:498 |
| T16 | 41:1497~1532 §6 출발 구간 | 1520 "7. gm/ID 선택 … **S·F 출발값은 구간 안의 최댓값**", 1525 "소자마다 gm/ID = gm/ID_lo + t·(gm/ID_hi − gm/ID_lo)", 1526 steps(gm/ID span), 1532 "1회차에서는 gm/ID를 gm/ID_lo로 두고" | 개정(구간·사다리 축 = ln IDu; '최댓값' 기준을 ln IDu 어느 끝으로 옮길지는 확인 -- 불확실 U3) | 41 §6 같은 절 |
| T17 | 41:1549, 41:1572, 41:1608 | "`vdsat_curve`로 역산한 값이 gm/ID_k,lo", "`ft_curve`를 역산해 gm/ID_k,hi", "f_T(gm/ID_lo, L) ≥ f_np에서 L의 최댓값" | 개정(gm/ID 축 곡선 역산 → ln IDu 축 순방향 / 남는 부등식 = 순방향 제약 행) | 같은 절 |
| T18 | 41:1719 | "`loop_lo`·`loop_hi` … VGS_m − VGS(gm/ID_hi,m) ≥ 0, VGS(gm/ID_lo,m) − VGS_m ≥ 0(**`vgs_for_gm_id`**, 그 점 VDS·VSB)" | 개정 | 41:1700 |
| T19 | 41:1727 | "목적(**기준 = gm/ID 큰 쪽**, §6.1-7 과 같다): (i) 위반 최소화 … (ii) 가장 낮은 위치 … 최대화" | 개정(★U-124 'gm/ID 큰 쪽 위치' → ln IDu 위치로 다시 정의, O-186) | 41:1708 |
| T20 | 41:1909 | "LUT γ를 넣어 **부하 gm/ID 상한을 역산**하고" | 개정(남는 gm/ID 부등식 = 순방향 제약 행) | 같은 절 |
| T21 | 41:1988 test 행 | "(a) 이름 없는 CS·캐스코드 toy 손계산(목표 gain → L, **gm 요구 → gm/ID**)" | 개정(test 문언) | 같은 표 |
| T22 | 40:116 | "lut → 41 §6 \| 신규 `ft_curve`… `idu_curve(...)`(**gm/ID 축 곡선**)" ; 40:2161 U3 같은 곡선 | 개정(곡선 축) | 40:179 부근·U3 행 |
| T23 | 40:1389 tol_V 정의 행 | "지표 배정: … **층 0 gm/ID 역산 = gm/ID 역산 지표**" (41:889 같은 지표 인용) | 개정(소비자 소멸 → 지표 (ii) ID 환산 하나 -- MR §5.3) | 해당 행 |
| T24 | 40:1067 | "보상 단 폴백(U-51) -- 삭제 … : **보상 단 gm/ID는 θ에 포함한다**(DEC-04, 그대로)" | 개정(문언 -- ★U-51 문언 변경: θ 좌표 = ln IDu) | 해당 절 |
| T25 | 42:313 D-TB1c | "R7 가드 필드 `device: start.guard` = 소자별 `GuardInterval(gm_id_lo, gm_id_hi, sources)`" (41:1597 가드 형식 문단도 같은 축) | 확인(가드 구간을 ln IDu 상자로 바꿀지, gm/ID 순방향 제약 행으로 둘지 -- O-186 문언으로 갈림, 불확실 U4) | 같은 행 |

참고(개정 불요로 판단): 40:115 `vgs_for_gm_id` 인터페이스 '기존 OK' 행은 재작성 범위 표기만 바뀜(T15와 같은 변경에서), 40:2013 DF-10 '역산은 단조 구간 밖에서 근을 내지 않고 실패' = fail-closed 규칙이라 결정과 맞음, 42:336 D-AR 'IDu(g, L) ≤ I·L²/A_min'은 이미 순방향 꼴.

### 3.2 Q-TH1 (L2) -- 레이아웃 보존량 (ID, gm/ID, L) → (ID, VGS, L)

| # | 자리(v115) | 낡은 문언 | 판정 | master |
|---|---|---|---|---|
| L1 | 40:473 `ly_point` 행 | "`device: ly_point` = 소자별 `ConservedPoint(kind, L_m, ID_A, **gm_id**, vds_V, vsb_V)` -- 보존량·동작점만"; 칸별 소비자 "`gm_id` = `ly_slice_density`·`ly_canonical_naming`·`ly_finger_candidates`·`layout_outputs`" | 개정(보존 칸 gm_id → VGS, 소비자 넷 재배선) | 40:562 |
| L2 | 40:480 `ly_slice_density` 행 | "폭 슬라이스별 **보존량 실현**(`slice_density`)" -- READS `ly_point`(gm_id) → 슬라이스 전류밀도 조회가 gm/ID→VGS 역산(MR §5.2: 실행 소비자 `layout/slice_density.py`) | 개정(J_slice(VGS) 순방향 -- pfet 다근 81/440 소멸) | 40:569 부근 |
| L3 | 40:1328 §3.10.2 | "(i) nf 조정(**같은 (ID, gm/ID, L)**에서 finger_w를 줄임)" | 개정 | 40:1352 |
| L4 | 40:482 `ly_attrs` 행 | "`W_m`은 보존량이 아니라 sizing 참고 W(파생값 W = ID/(ID/W)(**gm/ID**, L, VDS, VSB), O-24)" | 개정(문언 -- 파생 식의 좌표, 불확실 U5: 파생 식 자체는 sizing 점 값이라 결과 동일 가능) | 같은 행 |

- 계획 쪽 대응(참고, 판단 기준 아님): DEC-84 283·DEC-89 (1) 288·LY1 1042 -- 작성자가 반영 중.
- (L2)로 생기는 gm 이동(중앙 2.6~6.2 %, 최대 18~39 %)은 DEC-89 (2) 재평가가 판정 -- design 40:1165~1168 '레이아웃 뒤' 절은 이미 재평가를 쓰므로 개정 불요.

### 3.3 Q-KV1 (O-187) -- (다) B 멤버 종속, R13 = 쓰기 계획 앞 S0·X 칸 삭제, writer = R6 값 대상은 고리 B 멤버 중 writer 역할만, B 안 순위 diode → 대칭 궤도 대표 → 소스 사슬 하류 → DEC-97 정준 라벨, (f1′) ② '뒤 stage 독립' + 남는 tie 정준 라벨, J12-f 'M21/M22' 문언 개정, OrderHints 삭제

DI2 K-번호를 그대로 쓴다. ⚠ DI2 K3·K10은 O-187 **이전** 권고 문언이다(K3 'B 안 순위 = diode → 대칭 궤도 대표 → **이름**', K10 'ratified는 B 안에서만, 아니면 정지') -- 개정 때는 O-187 최종 문언(소스 사슬 하류 → 정준 라벨, (f1′))을 써야 한다.

| # | 자리(v115) | 낡은 문언(재확인) | 판정 | master |
|---|---|---|---|---|
| K1 | 40:449 `theta_class` 행 | "`kind` ∈ {S, F, B, **`"X"`(쓰기 계획 종속: `dc_coord.relation` ∈ {`cycle_vgs`, `fixed_vgs`}…)**}"; "sizing 층 4: 쓰기 계획 블록 `dc_writer_plan` **다음** S0 블록"; 입력에 `device.dc_coord`; "TB-1 병합 때 엔진 소비자 0" | 개정(X 삭제, 쓰기 계획 앞, `dc_coord` 입력 삭제, 첫 소비자 = `dc_writer_plan`) | 없음(v1.15 신설) |
| K2 | 40:462 쓰기 계획 필드 행 | writer `dc_writer_plan` READS에 `theta_class` 없음, `dc_coord` 값 = 옛 선택 | 개정(READS 추가·값 변화 표기) | 해당 행 |
| K3 | 40:1107 §3.7 4 | "종속 소자 선택 DEC-95 (3): ratified 선택(`structure.json`)과 ② **'GB5 gm 요구·뒤 stage 독립'**을 Kruskal 엣지 키 앞에 둔다. ②의 입력은 S1v stage 번호다" | 개정(전면: B 멤버 있으면 B 종속·B 안 순위 O-187, ①②는 B 없는 고리만, ② = '뒤 stage 독립'만, 남는 tie = 정준 라벨) | 40:1222 |
| K4 | 40:1122 상태 표 | "DEC-95 (3) 전체 순서 \| PART(① 구조 색·이름만)" | 개정(증거 칸·card = TB-1) | 40:1237 |
| K5 | 40:1780 §8 R14 | "DEC-95 (3) ratified·② 없음 → 복원(§3.7)" | 개정(문언) | 40:1727 |
| K6 | 40:2162 §11 U4 | "DEC-95 (3) 전체 순서" | 개정(TB-1로 이관) | 40:2071 |
| K7·K8 | 40:2174 U15·40:2193 TB-1 행 | "master 병합 = 행동 소비자 card(HC-1·LA-1) 가운데 먼저 … (O-149)", "병합 때 엔진 소비자 0(O-146 K2)", 범위 1·2만 | 개정(TB-1 단독 병합·writer_plan 배선·OrderHints 삭제 범위) | -- |
| K9 | 40:905~913 `structure.json` concept 표 | 고리 종속 선택 concept 없음 | 확인(O-187 (f1′)은 '사용자 ratify가 다르면 정지·보고'라 ratify 입력 자리 필요 여부를 design이 정함 -- 불확실 U6, graph 규칙 6) | 해당 표 |
| K10 | 40:1913 J12-f | "루프 종속 gm_id 소자 선택·합류 노드 KCL \| 엔진 유도 \| 열림" | 개정(문언 -- (f1′) 규칙으로 엔진 유도, ratify 대조 칸, 'gm_id' → ln IDu) | 40:1858 |
| K11 | 41:644 IT-1 test interface | "`dc_writer_plan(…, order_hints=NO_ORDER_HINTS)`(**서명 불변**)" | 개정(OrderHints 삭제 -- IT-1 시점 한정 표기) | 41:674 |
| K12 | 41:874 '분류의 정본' | R13 X(제외) 대응 | 개정 | 해당 절 |
| K13 | 41:880 '제외' 행 | "`dc_coord.relation` = `cycle_vgs`·`fixed_vgs`, DEC-64 v2 고리 종속 멤버" -- B(diode)가 종속이 된다는 문장 없음 | 개정(문장 추가) | 41:923 |
| K14 | 41:882 B 행 | "고리 종속이면 후보마다 DEC-104 R6 블록 값" -- 대상 한정 없음 | 개정(**R6 값 대상 = 고리 B 멤버 가운데 쓰기 계획 writer 역할만**, 종속 B는 커널 고리 등식 -- graph 규칙 1) | 해당 행 |
| K15 | 41:1759~1763 R6 블록 | `LoopDep(b_ln_idu, …)` -- B ln IDu 대상 한정 없음; 41:900·905 '변수·출력 = B 소자 ln IDu' | 개정(K14와 같음) | 해당 절 |
| K16 | 41:1406 E11 | "`ThetaClass(kind ∈ {"S","B","F","X"})`, writer = … **쓰기 계획 다음** S0 블록" | 개정 | -- |
| K17 | 41:1521·41:1698·41:1722 | "쓰기 계획 v2 고리 등식(**X**)", "고리 종속 멤버(**X**)는 층 0이 고르지 않고" | 개정(문언 -- X 기호 → `dc_coord` 종속) | 41:1680 등(X 표기 없음, 문맥 같음) |
| K18 | 41:1703 | "종속 소자는 **DEC-95 (3) 우선순위**로 이미 정해져 있다" | 개정(문언 -- 개정 DEC-95 (3)) | 41:1685 |
| K19 | 41:1277 대응표 | "DEC-104 R13·(3)(a) \| **S/B/F/X** 분류 S0 필드" | 개정(문언) | -- |
| K20 | 42:311 D-TB1a | "S/B/F/X 분류 … (`E/sizing/theta_class.py`, **쓰기 계획 다음**), 입력 = S1v `Block.roles`·**`device.dc_coord`**" | 개정 | -- |
| K21 | 42:134·42:267 D-GB7c | "DEC-95 (3)은 일부만(`E/sizing/writer_plan.py:13-17`)" | 개정(card = TB-1, 확인 칸) | 42:133·263 |
| K22 | 42:67 | "ratified 선택(J12-c·f)을 읽는 곳이 없다(`structure.json` **로더 MISS**)" | 개정(문언 -- DI2 N1 실측: 로더 있음, 남은 MISS = 고리 선택 READS. K9와 짝) | 42:67 부근 |

- r2r (i)(M19/M20·M27/M28 = pass(F)): design 40·41·42에 r2r 언급 0건(`grep -c r2r` = 0) → 개정 대상 없음.
- DEC-104 (3)(a) 옛 문언: design은 (3)(a)를 인용만 함(41:874·1277·1406, 40:449) -- K1·K12·K16·K19로 덮임.
- 40:918 `l_owner_name_order`(L 동치류 주인의 이름 순서)는 고리 종속 멤버 선택이 아니라 O-187 범위 밖(불확실 U7로 기록).

### 3.4 O-188

- design 개정 0(1절 근거). 참고: 승인 문서 v4b §2.8 상호작용 줄 "topology 정정 대기열(r2r 벌크)"는 낡은 사실이다 -- 대기열 #3은 2026-10-30 철회 표지가 이미 있음(`wt/_drafts/topology_correction_queue.md:9`). evidence 문서라 감사 대상 밖, 보고만.

## 4. ★graph 단일 정본 칸

| 항목 | 결과 |
|---|---|
| 새 cache·memo·sctx·사본을 만드는 낡은 문언 | 0. (L2)의 `ly_point` 칸 교체(gm_id → VGS)는 기존 승인 사본 부채(O-27, 40:473 '사본 부채')의 칸만 바뀌고 새 사본은 아님 -- 개정 때 VGS를 `dc_op` 필드 참조로 둘지 사본 칸으로 둘지 확인 필요(O-27 범위 안이어야 함) |
| writer 둘 위험 | K14·K15: (다)에서 종속 B 멤버 ln IDu를 R6 블록과 커널 고리 등식이 함께 쓸 수 있음 -- O-187 writer 결정('R6 값 대상 = B 멤버 중 writer 역할만')을 design에 넣지 않으면 graph 규칙 1 위반 |
| 같은 정의 = 필드 하나 | K1: X 칸은 `dc_coord.role`과 같은 정의의 둘째 칸 → 삭제가 규칙 3과 맞음. T6·T7: gm/ID를 결정 변수로 두면 ln IDu와 같은 자유도의 두 표현 -- (A)로 해소 |
| 정본 자리 없음(규칙 6) | (L1)의 pfet 다근 근 선택 자리 없음(81/440) → (L2)로 소멸. K9 ratify 입력 concept 자리는 design에서 정할 몫(U6) |

## 5. 즉시 정지·보고 대상

**없음.** 진행 중 card 구현·test·판정이 없다(worktree 4개 = master·design-v115·integ-it12·plan-v6385, 미커밋 0, it2 역할 브랜치 전부 `integ/it12`에 포함). 진행 중인 것은 design v1.15.3(`wt/design-v115`, 검증 대기)뿐이고 3절 목록이 그 개정 대상이다. ⚠ design v1.15.3 승인·병합 전에 3절을 반영해야 한다(지금 그대로 승인하면 O-186·O-187과 어긋나는 design이 승인된다).

## 6. 불확실 항목

| ID | 내용 | 갈림 |
|---|---|---|
| U1 | it2-common `:255`·IT-1 `:15`/`:77`의 `order_hints` 서명 줄과 IT-1 재동결 종속 기대값 | TB-1 대 IT-1+IT-2 통합 병합 선후(계획 v6.38.5 '나중 card가 rebase' -- 고정 안 됨). IT 먼저면 그대로, TB-1 먼저면 개정 |
| U2 | IT-1 interface `:27` W4 뿌리 '(구조 색, 이름) 최소' | O-187 '이름 키 철회'가 고리 종속 멤버 순위에만 걸리는지, 쓰기 나무 뿌리에도 걸리는지. 결정 원문은 'B 안 순위'·'DEC-64·95 이름 키'만 적음 → 범위 밖으로 판단 |
| U3 | 41:1520 'S·F 출발값은 구간 안의 최댓값'(gm/ID) | ln IDu 좌표로 옮길 때 '최댓값'의 대응(ln IDu 아래 끝 vs gm/ID 순방향 최대점) -- pfet 비단조로 같지 않음. O-186 U-124 문언만 '위치로 다시 정의' |
| U4 | 42:313·41:1597 R7 가드 `GuardInterval(gm_id_lo, gm_id_hi)` | ln IDu 상자 vs 순방향 제약 행 |
| U5 | 40:482 `W_m` 파생 식 좌표 | 값은 같을 수 있어 문언 정정만일 수 있음 |
| U6 | 40:905~913 `structure.json` 고리 선택 concept | (f1′) '사용자 ratify가 다르면 정지·보고'에 입력 자리가 필요한지 |
| U7 | 40:918 `l_owner_name_order` | O-187 범위 밖으로 판단(L 동치류 주인) |

## 7. 자기 점검(원칙)

- 지적은 직접 연 파일 줄로만 했다(DI2 K-행은 재확인한 것만 씀, K3·K10은 O-187 최종 문언으로 갱신). '없음' 주장(O-188 결함 문언 0, r2r design 0, 진행 중 card 0)은 DEC-61 원문(계획 260)·대기열 철회 표지·worktree·브랜치 실측 뒤에만 했다(원칙 22).
- 개정안은 결정 범위 안 문언만 적었다(새 규칙·상수·필드 0). 판단이 갈리는 곳은 U1~U7.
- as-built 엔진을 근거로 쓰지 않았다(MR §5.2·DI2 엔진 인용 = 재작성 범위 표기로만).
- 회로 이름은 실측·인용 문언에만 있다.
