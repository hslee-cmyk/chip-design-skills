# 2차 독립 검토: `draft_phase4_design.md` v0.3 (Phase 4 `40-defect-fixes`)

검토자 = 작성자도 1차 검토자도 아님. 저장소 읽기 전용(쓰기 0, 상태 변경 git 0). 기준 gate `master` HEAD = `7535799`(재확인).
스크래치 `C:/g57`(`git archive HEAD skills/analog-gmid-design skills/analog-grammar workspaces/run_harness.py tools install.py` 사본 + `runh.py`·`m.py`, 끝나면 삭제). `$PY` = `C:/Python314/python.exe -B`.
입력: 대상 v0.3, `phase4_revision_log.md`, 1차 검토 `review_phase4_design.md`, 그리고 v0.3 작성 뒤(또는 v0.3이 쓰지 않은) 입력 `prep_b37_ports.md`(22:51), `review_b34.md`·`b34_revision_log.md`·`draft_b34.spec.md`(10-01 10:51 최신), `draft_v3_exempt_binding.spec.md`, `draft_v3_scope_policy.spec.md`·`draft_v3_decision_question.md`, `draft_b33.spec.md`, `draft_phase3_design_v4.md`(22:39), `user_decisions.md`(10-01, A2·A3 승인), `v3_scope_systemic.md`.

---

## 0. 요약

| 등급 | # | 제목 |
|---|---|---|
| **blocking** | B1 | #48(V3 범위)이 새 입력과 정면으로 어긋난다: 새 spec은 이것을 **기준 약화 + 사용자 결정 A1(선택지 1·2·3 대기)**로 두고 대상 정의(N2 = 바뀐 문장 + 감싸는 제어문)·출력(`not_targeted`)·선행(면제 누수 수정 먼저)·승인 형태가 다르다. v0.3은 사용자 결정 없이 '게이트 변경 승인'만으로 #1의 선행에 넣었고, 선택지 1(현 규칙 유지)일 때의 경로가 없다 |
| **blocking** | B2 | #50의 red 형태(`xfail(strict=True, raises=AssertionError)`)가 근거 없이 정해졌다. HEAD 코드상 `propagate_node_voltages`가 `rail_lo` 넷을 **0.0으로 박는다**(SR 3727 함수 본문). #21만 병합된 엔진에서 S_B(0.9, −0.9)는 원점 이동이 아니라 다른 회로로 평가된다 -- F4 분류가 `hi`면 폭 0.9 V 회로(예외 가능성), `span`이면 S_A와 같은 입력(XPASS). #25(DF-27)가 먼저 병합되면 축 밖 vsb는 `lut_axis_out_of_range`(SealViolation). 어느 경우도 `AssertionError`가 아니어서 #50은 병합본에서 FAIL(또는 strict XPASS FAIL)한다 |
| should-fix | S1 | B34 범위가 좁혀졌다(최신 card: 4 def, phase 2, approval `20260930-b26-before-phase3`). v0.3 #45·부록 C.3·C.4의 "21곳 전부 #45에서 R"은 틀렸고, 인계(B26-1 #1 / B35 / 백로그)가 v0.3 어느 card에도 없다 |
| should-fix | S2 | B37 준비 자료와 #47이 9곳 어긋난다(진입점 E1만 vs E1~E3, `direction` 소비자, 픽스처 17, DEC-40 아님, pre 아님, #17 선행 불필요, B37b 없음, B38 중복, 사용자 확인 2) |
| should-fix | S3 | UD-14는 이미 승인됐다(A2, 기록 id `20260930-b26-before-phase3`). 결정 표·§3.2·§9에 '대기'로 남아 있다 |
| should-fix | S4 | `v3_scope_systemic.md`는 v0.3 작성 전부터 있었다(mtime 22:17 < v0.3 22:36). "ls 확인, 없다"는 사실이 아니고 §8.4 [미확인] 수치를 채울 수 있다 |
| should-fix | S5 | B33이 게이트 card(`20260930-v7-registry-edges`, phase 0.5)가 됐다. v0.3 §1.4·§8.2는 낡았고, 부록 C '운영 도달' 열은 B33이 고치는 그래프 결함(레지스트리 간선 누락·이름 폴백 누수)을 그대로 물려받아 과소/과대 계수된다 |
| should-fix | S6 | Phase 3 design은 v4가 최신이다. v4에는 v0.3 §3.1이 요구한 "Phase 3 전 병합 card가 정해지면 D0b 재측정" 줄이 없다(A2 승인으로 이미 정해졌는데). #48과 G1이 같은 V3 대상 선택 지점을 바꾸는 순서도 어디에도 없다 |
| should-fix | S7 | §10.6 감도 전파 허용오차: τ 크기는 유도됐으나 **한쪽(+τ)·레일 하나씩·max**는 계획에서 유도되지 않는다. 계획의 같은 종류 선례(N3.6 `tol_I = tol_V × gm`, N3.8 'AC gain = 노드 허용오차를 소신호 감도로 전파')는 1차 선형 상한(합)이다 |
| should-fix | S8 | #43 margin 분모와 KVL 판정 경계가 정의되지 않았다. 계획 N3.6 항목 8은 `멤버 수 × tol_V`, HEAD는 `1e-9 × max(vdd, 1)`(SR 7069). "margin = 위반/`tol_V`"는 어느 소자의 tol_V인지 없다 |
| should-fix | S9 | #13 발동 계수 측정 방법이 없다. CC-8 `activations_out`은 계측을 단 기능의 발동만 센다 -- D·I 지점은 #13 전에 계측이 없으므로 그대로 재면 전부 0 → 전부 R(거부)로 잘못 분류된다 |
| should-fix | S10 | `P3?` 열 모순: #19·#47이 '조건부 pre'인데 전이적으로 #6(CC-4a, Phase 4 선두)에 의존한다 |
| should-fix | S11 | #10이 X 지점의 잡는 타입을 'LUT 정의역 오류'로 좁히는데, 그 오류(`lut_axis_out_of_range`)는 #25(DF-27)가 만든다. #25 → #10 간선이 없다 |
| should-fix | S12 | 사용자 결정·착수 승인 목록이 불완전하다(A1 V3 범위, 면제 누수 수정 승인, B37 확인 2건, B33 승인 인지) |
| minor | M1~M8 | 7411 vsb 조건식 기본값 누락, `derived_spec` 면제 소비 주장, V4 면제 누수 메커니즘, `rail_voltages` 보관 위치, redteam 번호 충돌, F16 검출력 서술, 선행 열 빈칸, prep_b37의 `_TEMPLATE` 오기 |

**실측 표본(검사 3)**: 7건을 다시 쟀고 7건 모두 v0.3과 일치했다(§3). 다만 같은 측정에서 v0.3 부록 C에 없는 vsb 기본값 지점 1곳(SR 7411)이 나왔다(M1).
**의존 그래프(검사 5)**: 선행 열 전체(+#48~#51, C1·C2·C3)로 위상 정렬이 된다 -- **비순환**. 모순은 S10·S11과 B1(조건부 경로 누락)뿐이다.

---

## 1. 1차 검토 지적의 처리 확인 (검사 1)

| 1차 | v0.3 처리 | 판정 |
|---|---|---|
| B1 nmcnr ±0.9를 MG1에 | #21 = `{vdd 1.8, vss 0.0}`, 전환은 #51(#22 뒤) | **해소** |
| B2-1 IC11 oracle·#23 간선 | §10.6 식, #22·#50 선행에 #23 | 해소. 단 식 형태는 S7 |
| B2-2 감도 전파 함수 소유 | #50 test 쪽 helper | 해소. 단 red 형태는 **B2(새 blocking)** |
| B2-3 two_stage 실행 가능성 | 4회로 실측(F15), 대상 folded로 교체 | **해소**(재측정 일치, §3) |
| B2-4 #17 → #22 | 추가 | 해소 |
| B3 N9.1 필수(`fallback_events`·I-C11·인터페이스 5) | §10·§11·부록 C | 대부분 해소. 부록 C의 B34 21곳 배정 오류(S1), 운영 도달 열(S5), 발동 측정 방법(S9)이 남음 |
| B4 B35 분류 | UD-15 (2), 비교표, 레일 수 상한 원칙 §4.1 | 해소 |
| S1 Phase 3 v3 | 입력 v3, MOD 표기, 교차 항목 | 부분. v4가 나왔고 교차 항목이 v4에 반영되지 않음(S6) |
| S2·S3 UD-2·UD-3 | P-13·P-14 | 해소 |
| S4 간선 | C1→#19, #21→#19, #33 선행 #6, #9 선행 #6, #45 install.py, #31·#13·#24 | 해소(그래프 비순환 재확인) |
| S5 D-5 | F18 실측, 표 행 #2 / 함수 #41 | 해소 |
| S6 `Error:` | #26 G7 | 해소 |
| S7 probe rail-set·P3c | #17 test 커밋, §9-8 | 해소 |
| S8 B37 | role 유도·부재 거부·B38 | 해소였으나 **새 입력 prep_b37과 어긋남(S2)** |
| S9 UD-13 형식 | 게이트 변경 card #48 | 당시 권고대로 처리. 그러나 **새 입력이 약화·사용자 결정으로 분류(B1)** |
| S10 lint 배선 | PT 계약 test | 해소 |
| S11 U-25 | 범위 밖 + 사유 | 해소 |
| S12 CC-5 deepcopy | AST 0(F19) | 해소 |
| M1~M9 | 개정 기록 표대로 | 해소. M6(`derived_spec`)의 '면제 소비' 주장은 부정확(M2) |

---

## 2. 새 입력과의 모순 전수 (검사 2)

| # | 새 입력 | v0.3 위치 | 모순 내용 | 등급 |
|---|---|---|---|---|
| 2-1 | `draft_v3_decision_question.md`, `draft_v3_scope_policy.spec.md` | §4.3 마지막 행, §4.5 끝 문장, §5.12 #48, §3.2 #1 조건 (4), §3.3 첫 줄, §7.3 #48 행, §8.1, §8.4 대응, §9-7 | (a) 새 spec은 이 변경을 **판정 범위 축소 = 약화**로 보고 사용자 결정(A1, 선택지 1/2/3)을 요구한다. v0.3 §8.4는 오히려 "decision으로 좁히면 약화 은폐"라고만 쓰고 #48 자체의 약화 여부와 사용자 선택을 다루지 않는다. (b) 대상 정의: v0.3 '닿은 문장 + 새 def' ≈ N1, 새 spec 기본 N2(+ 감싸는 제어문 T4), D1 대안. (c) 출력: v0.3 '제외 변이 id 목록' vs 새 spec `not_targeted`·`targets_by_def`(실행하지 않음). (d) 승인: v0.3 'plan_tables 승인 + 게이트 변경 승인' vs 새 spec "N4.2 이 칸은 `plan_tables_hash` 입력이 아니다", `target_kind: diff` 승인 1건. (e) id·phase: `20260930-v3-changed-stmt-scope`, phase 0.5. (f) redteam: v0.3 3종 vs 새 spec 5단계(`33-v3-changed-scope`). (g) 선택지 1이면 #48은 없고 B26-1은 V3 전수 + 확정 생존 298 처리 -- v0.3에 이 경로 없음 | **B1** |
| 2-2 | `draft_v3_exempt_binding.spec.md` | §5.12, §7.3, §8.1 | 면제 누수 수정(강화, `20260930-v3-exempt-binding`)이 "어느 정책이든 먼저 병합"인데 v0.3에 없다. #48의 선행이 B28뿐으로 적혀 있다. 또 이 card는 V4 면제 누수를 백로그로 넘겼는데 #50은 V4 규칙 (1) 면제를 새로 받는다(M3) | B1에 포함 |
| 2-3 | `user_decisions.md` A2(10-01) | §3.2 #1 조건 (3), §7.1 UD-14, §5.1 #1 선행, 부록 B 8행 | UD-14(DEC-60 전환기 종료 + DF-19·26 분리 + B26-1·**B34** Phase 3 전)는 **승인됨**. 기록 id 후보 `20260930-b26-before-phase3`. v0.3은 대기 결정으로 둔다. A1(V3 범위)은 "아직 묻지 않음" -- v0.3 결정 목록에 없다 | S3, S12 |
| 2-4 | `draft_b34.spec.md`(10-01 10:51)·`b34_revision_log.md`·`review_b34.md` | §1.4, §4.3 B34 행, §5.1 #45, 부록 C.1 SD 1057 행, C.3 "#45에서 전부 R", C.4 "B34 21" | 최신 B34 = def 4개(`_import_analog_grammar`·`find_idiom_matches`·`find_stack_edges`·`audit_theta_root_direction`), phase 2, gate_change no, approval `20260930-b26-before-phase3`. 사이트 9·10·10b·13·14 + `propose_device_roles_gap_fill` 3966~3970 `unavailable_reason` → **B26-1(#1)**, 사이트 5~8 → **B35**, 사이트 4(`forks`)·12·3533~3535 → **백로그**, SR `resolve_stack_layout` 6509~6512 docstring 포함. v0.3 #45는 "폴백 12·전파 9·`unavailable_reason` 2 삭제"(v1 범위), #1 계약에 인계 없음, UD-15 (2)=Y일 때 사이트 5~8의 집이 없음 | S1 |
| 2-5 | `prep_b37_ports.md` | §5.4 #47, §3.3 `B34 ─> B26-2 ─> B37`, §4.3 #47 행, §7.2 P-12, §7.4 '#47로 바뀌는 E-LIB', §9-12 B38, §8.1 'B37 영향 실측' | (a) 진입점 E1만 → prep은 E1(`load_topology`→`propose_device_roles_gap_fill`)·E2(`propose_vertical_stack_id_gap_fill`, 지금 기능 꺼짐)·E3(SR `resolve_stack_layout` 6572) 전부. (b) SR `input_referred_offset_pairs`(4511~4519)가 이미 `direction`을 읽는다 -- 같은 접근자로 교체해야 MG2가 키 삭제만 남는다. v0.3은 "`direction`은 읽지 않는다"만 쓰고 기존 소비자를 다루지 않는다. (c) role·`direction` 모순 → 거부(기본안). (d) `ports` 누락 거부는 selftest 합성 픽스처 **17곳** 보강(test-author) 필요. (e) E-LIB meta 5회로 차이를 **실측**했고 기대값이 바뀌는 test 0 → **DEC-40 아님(확인 사안)**. v0.3은 [미확인] + DEC-40 목록. (f) 선행 = B34 → B26-1 → CC-4a(파일 충돌 순차), **B26-2(#17) 불필요**. (g) prep은 Phase 4 레일 묶음(pre 아님). v0.3은 '조건부 pre'. (h) B37b(AG 라이브러리 `HINT_*` 제거, B36 뒤)가 v0.3에 card로 없다. (i) v0.3의 새 백로그 B38(바이어스 힌트)은 prep §1.1상 `HINT_BIAS`는 결과 무영향이고 B37b가 라이브러리 경로의 `HINT_*` 전부를 CLI 경계로 옮긴다 -- B38은 B37b에 흡수되거나 근거를 다시 써야 한다. (j) 사용자 확인 2건(자동 채움 소실 3회로·레이아웃 그룹 변화, `Vom1`/`Vop1`) 없음 | S2 |
| 2-6 | `draft_b33.spec.md` | §1.4(B33 = 인프라 백로그), §8.2('G1에서 처리되는지 확인'), 부록 A B5·부록 C '운영 도달' 열, F17 '운영 도달 52', §8.4 | B33은 별도 게이트 card(phase 0.5, 권고 순서 B33 → G1). 부록 C는 HEAD `build_graph`로 도달을 쟀다 -- 레지스트리 값 함수가 미도달로 나온다(예: `_metric_flicker_plus_thermal_sum`·`_metric_smallsignal_ratio_db`·`_metric_smallsignal_gain_db`는 `_METRICS_REGISTRY` 5091·5108·5109행 등록인데 C.2에서 '아니오(근사)'). 또 B33은 V3 인벤토리를 2.35배로 키운다(33,991 → 79,809 쌍) -- §8.4 비용 추론에 빠짐 | S5 |
| 2-7 | `draft_phase3_design_v4.md` | 머리 입력 목록, §3.1 '(Phase 3 초안 v3 기준)', §3.1 교차 항목, §3.2 끝 문단 | v4 §1 범위 밖은 여전히 "정본 확정(B26, Phase 4)"이고 재측정 조건은 P9·P10뿐 -- B26-1·B34 Phase 3 전 착수(A2 승인)를 반영하지 않았다. v0.3이 요구한 교차 줄이 v4에 없다. 또 G1(v4 §8, `mutate_changed.py` V3 대상 선택에 이동 제외)과 #48/scope-policy(같은 대상 선택 지점)의 병합 순서가 두 문서 어디에도 없다. MOD 배정(A-3, D-3, D-5, D-10)은 v3와 같다 -- 이 부분 v0.3 내용은 유효 | S6 |
| 2-8 | `v3_scope_systemic.md` | 머리 '아직 없는 입력', §8.4 '[미확인 -- 없음]', §9 첫 항목 | 파일이 있다(22:17). B26-1 2,472 변이 / 3.4~122 h, B34 1,395, 확정 생존 B26-1 298·B34 75 등 수치가 §8.4에 들어갈 수 있다 | S4 |
| 2-9 | redteam 번호 | #48 | G1 `32-moved-defs`(v4 D-18), B33 `33-v7-graph-edges`(v4) 대 B33 spec `32-v7-registry-edges`, 면제 누수 `32-v3-exempt-binding`, scope-policy `33-v3-changed-scope` -- 네 card가 두 번호를 다툰다. v0.3 책임은 아니나 #48 interface에 번호를 박지 말 것 | M5 |

---

## 3. v0.3 새 실측 표본 재측정 (검사 3)

명령은 모두 `C:/g57/repo`(HEAD 사본)에서. 결과 원자료는 `C:/g57/run_summary.jsonl`·`m.py` 출력(삭제 전 여기 옮김).

| # | v0.3 사실 | 명령 | 재측정 | 판정 |
|---|---|---|---|---|
| 1 | F15 two_stage `ValueError` 'stage1_out' VDS 합 2.37965 V, diff +0.579654, M4 0.9172·M2 0.9·M5 0.5625, exit 0 | `$PY C:/g57/runh.py two_stage_ota nmcnr_amplifier`(하네스 `run_harness.py <key>` 2병렬, rc·stdout 기록) | 같은 문구·수치, **rc 0**, 19.9 s | 일치 |
| 2 | F15 nmcnr 모든 θ infeasible, `stage2_diode_ref` 예산 1.5 V 중 0.525 V, M203 ∈ [0.6375, 0.975], exit 0 | 같은 실행 | 같음, **rc 0**, 19.4 s | 일치 |
| 3 | F15 folded 끝까지, `audit_ok=False`·`floorplan_ok=False`, 단독 43 s | 보고 디렉터리를 사본에 만든 뒤 `runh.py folded_cascode` | `instance.json` 저장, 두 플래그 False, **rc 0**, 37.6 s | 일치 |
| 4 | F17 예외를 다시 던지지 않는 except 핸들러 59(SR 47·SD 5·하네스 3·도구 4) | `m.py`: `A/*.py` + 하네스, `ExceptHandler` 중 본문에 `Raise` 없는 것 | 59(SR 47, SD 5, run_harness 3, sky130_lut_sweep 2, audit_current_forced 1, topology_to_markdown 1) | 일치 |
| 5 | 부록 C.2 `.get("vsb", 0.0)` SR 31곳, `setdefault("vsb", …)` SR 7579·SD 4605 | 같은 스크립트, `.get("vsb", <식>)`·`.setdefault("vsb", …)` | 리터럴 0.0 기본값 31(줄 목록 동일), setdefault 2(같음). **추가: SR 7411 `_e.get("vsb", ref_vds if ref_dev is not None else 0.0)`** -- 조건식 기본값이라 v0.3 규칙 밖 | 일치 + M1 |
| 6 | F21 `_TEMPLATE`에 `ports` 키 없음 | `json.load(library/_TEMPLATE.topology.json)` | `"ports" in d` = False | 일치(prep_b37 §4.2 C3의 "`ports: null`"이 틀림 -- M8) |
| 7 | F16 source가 선언 레일이 아닌 NMOS: folded 2(M7·M8), current_reuse 12 | `load_topology` 후 `kind == "nmos"`·`source ∉ supply_nets` | folded 2(M7, M8), current_reuse 12, (참고) two_stage 2(M1, M2), nmcnr 2(M106, M107) | 일치(해석은 M6) |

current_reuse 411 s 실행은 재측정하지 않았다(시간). 코드 판독 2건: SR 3727 `propagate_node_voltages`는 `for n in rail_lo: nodes[n] = 0.0`(본문 29~30행), SR 3789 `derive_vsb_from_nodes`는 `return (vdd - v) if kind == "pmos" else v`(B2 근거). SR 7068~7069 KVL 판정 `abs(total - vdd) > 1e-9 * max(vdd, 1.0)`(S8 근거).

---

## 4. blocking 상세

### B1. #48(V3 범위)이 새 입력과 어긋나고 사용자 결정 A1이 빠졌다

* **근거**: 2-1·2-2 표. `draft_v3_scope_policy.spec.md` '약화인가 -- 원문 대조': "판정 기준의 적용 범위를 줄이는 게이트 변경이므로 약화로 다루고 사용자 승인을 받는다". `draft_v3_decision_question.md`: 선택지 1(유지)·2(N2, 권고)·3(D1). `user_decisions.md`: "아직 묻지 않음: A1 V3 범위 정책".
* **문제**: v0.3은 #48을 '오케스트레이터 decision이 아니라 게이트 변경 card'로 바꾼 것으로 1차 S9를 닫았다고 보지만, 게이트 변경이어도 **약화이므로 사용자가 고를 일**이다(메모리 '작성자≠검증자': 기준 약화는 사용자 승인). v0.3 §4.5·§7.3은 '게이트 변경 승인'만 적어 약화 승인 명시가 없다. 대상 정의도 새 spec의 N2(감싸는 제어문 포함, B26-1 기준 N1 139 → N2 176)보다 좁다(약화 폭이 더 크다). 선택지 1이 나오면 #1 선행이 성립하지 않는데 대체 경로가 없다.
* **수정**:
  1. §5.12 #48을 새 spec(`20260930-v3-changed-stmt-scope`, phase 0.5)의 **인용**으로 바꾸고 대상 정의·출력 키·redteam·승인 형태를 재서술하지 않는다(N9.4).
  2. 선행 사슬: 면제 누수 수정(`20260930-v3-exempt-binding`) → (A1이 2·3이면) scope card → #1. A1 = 1이면 #1은 V3 전수(B26-1 card 'V3 계획' (c))로 간다는 분기를 §3.2·§3.3에 적는다.
  3. §7.1에 A1을 사용자 결정으로 올리거나(권고 2, 근거는 새 질문 문서) "Phase 4 밖 결정, 결과에 따라 #1 경로가 갈린다"고 §7.3에 적는다. §4.5 문장에 "범위 축소는 약화 -- 사용자 승인"을 더한다.
  4. §9-7의 "plan_tables 승인"을 지운다(새 spec 실측: N4.2 V3 칸은 `plan_tables_hash` 입력 아님).

### B2. #50의 red 형태가 HEAD 코드와 맞지 않는다

* **근거**:
  * #50 계약: "#22 전까지 `pytest.mark.xfail(strict=True, raises=AssertionError, reason="DF-24, #22에서 해제")`", §10.6 "base(#22 전)에서 nmos vsb는 S_B에서 |Δ| = 0.9 V만큼 틀린다(F16의 M7·M8)".
  * SR 3727 `propagate_node_voltages(by_name, sized, vdd, rail_hi=_DEFAULT_RAIL_HI, rail_lo=_DEFAULT_RAIL_LO)`: `for n in rail_hi: nodes[n] = vdd`, `for n in rail_lo: nodes[n] = 0.0`. 낮은 레일은 **선언 전압과 무관하게 0.0**이다. #50의 선행은 #21·#23뿐이고 #17(기본 인자)·#22(DF-24)는 뒤다.
  * §10.4는 F4 20줄을 `span`/`hi`로 분류한다. S_B(0.9, −0.9)에서 노드전압 전파의 `vdd` 인자가 `hi`(0.9)면 엔진은 폭 0.9 V 회로를 푼다(실제 폭 1.8 V) -- 헤드룸 배정·KVL이 달라져 `InfeasibleSizingError`류 예외가 날 수 있다. `span`(1.8)이면 rail_hi = 1.8·rail_lo = 0.0으로 S_A와 **같은 입력** -- vsb 차이가 생기지 않아 XPASS.
  * #25(DF-27)는 #50과 순서가 정해져 있지 않다. #25가 먼저면 S_B에서 vsb가 VS 축 [0, 0.8] 밖이 되는 순간 `lut_axis_out_of_range`(SealViolation, `ValueError` 하위)다.
  * §10.6 자신도 "섭동 평가가 실패하면 ERROR(PASS로 세지 않는다)"라고 한다.
* **문제**: 위 어느 경우에도 base 실패는 `AssertionError`가 아니다. pytest는 `raises=`와 다른 예외를 일반 FAIL로, strict xfail의 통과를 FAIL로 보고하므로 #50은 자기 병합본 V1에서 FAIL한다. "DF-24 검출 NMOS 2"(F16)는 이 경로에서 실제 red가 무엇인지 보여 주지 않는다. card 형태(test-only + xfail V5 승인 + V4 면제)가 전부 이 가정 위에 있다.
* **수정**:
  1. §8.1 '#50 평가점 선정'에 **"#21 상당 사본에서 folded S_B 평가가 base로 무엇을 내는지(예외 클래스 / 값 차이) 실측"**을 넣고, red 형태는 그 실측으로 정한다(card 처리 속도 규칙: 사실 문장은 쓰는 자리에서 재측정).
  2. 선택지를 design에 적는다: (a) #50 선행에 #17을 넣고 rail_lo 0.0 고정이 사라진 엔진에서 판정 -- 그래도 DF-24 nmos 분기(`return v`)로 vsb가 음수가 되면 #25 전후로 형태가 갈리므로 #25와의 순서를 고정한다. (b) `raises=(AssertionError, InfeasibleSizingError)`처럼 실측된 클래스 집합으로 적는다(넓게 잡는 것은 V5 승인 범위 설명에 명시). (c) #50을 없애고 판정기를 #22 안에 두되 helper 소비자를 같은 card의 test로 한다(만들면 배선 충족, 1차 B2-2의 선택지).
  3. §10.6 'DF-24 검출력' 문단을 실측 결과로 다시 쓴다(M6 참조).

---

## 5. should-fix 상세

### S1. B34 범위 축소 반영(2-4)
* §5.1 #45 대상: 최신 card 범위(4 def + docstring 전부 + SR 6509~6512) 인용, phase 2, approval `20260930-b26-before-phase3`. 'Phase 4 card 50건' 계수에서 #45를 Phase 2 card로 표시.
* 부록 C.3·C.4: 21곳을 '#45 R'에서 사이트별 담당으로 쪼갠다 -- #45: 사이트 1~3·11·11b, **#1**: 9·10·10b·13·14·3966~3970, **B35**: 5~8, 백로그: 4·12·3533~3535. C.1 SD 1057 행은 R #45 유지.
* §5.1 #1 대상에 인계 사이트를 넣는다(B26-1 card 개정과 같은 내용).
* UD-15 (2)=Y(어댑터)이면 B35의 '운영 함수 8개에 `rails` 키워드' 작업이 없으므로 사이트 5~8 삭제의 집을 #17로 명시한다.

### S2. B37 준비 자료 반영(2-5)
* #47을 prep §4.1의 B37a로 바꾼다: 접근자 1개, E1·E2·E3 배선, SR `input_referred_offset_pairs` 교체, 누락·모르는 role·role/`direction` 모순 거부. 선행 = #45 → #1 → #6(순차 병합), #17 간선 삭제(§3.3 도식 포함). `P3?` = Y(Phase 4 레일 묶음).
* oracle (c)의 [미확인]을 prep §3.2 실측(5회로 meta 차이 표, SPECS 4회로·audit 9/9 불변)으로 바꾸고 'E-LIB 기대 차이표 밖 차이 = FAIL'. §7.4에서 '#47로 바뀌는 E-LIB'을 빼고 §7.3에 **확인 기록**(DEC-40 아님, test 기대값 변경 0)으로.
* test 커밋: selftest 합성 픽스처 17곳에 `ports` 보강(test-author, code 커밋과 분리).
* B37b(AG `HINT_*` 제거 → CLI 경계)를 조건부 card로 추가(선행 #46·#47). B38은 B37b에 흡수하거나 '바이어스 힌트는 결과 무영향(prep §1.1)'이라는 근거로 닫는다.
* 사용자 확인 2건(prep §5)을 §7.3에.

### S3. UD-14 승인 반영(2-3)
§7.1에서 UD-14 행을 지우고 §7.3/머리에 "A2 승인(2026-10-01) -- 기록 `20260930-b26-before-phase3`(계획 정정 커밋과 함께)"로 적는다. §3.2 #1 조건 (3)·부록 B 8행도 같이. B34 Phase 3 전 착수도 같은 기록이 덮는다(최신 B34 card approval 줄과 일치).

### S4. `v3_scope_systemic.md` 존재(2-8)
머리 '아직 없는 입력' 문장과 §9 첫 항목을 고치고 §8.4 '전반 확장'에 card별 수치(B26-1 2,472 / N2 176, B34 1,395, 확정 생존 298·75, 인벤토리 시간 177~192 s)를 넣는다. 이 파일이 cd64170 기준이라는 점(엔진 동일)도 적는다.

### S5. B33 반영(2-6)
* §1.4 인프라 백로그에서 B33을 빼고 '게이트 card `20260930-v7-registry-edges`(phase 0.5, Q1 사용자 결정, B33 → G1 권고)'로 인용. §8.2 문장 삭제.
* 부록 A B5·부록 C: '운영 도달' 값은 **HEAD V7 그래프(레지스트리 간선 없음·비운영 이름 폴백 누수 있음) 기준**이라고 머리에 적고, F17의 '운영 도달 52'를 같은 단서로. B33 병합 뒤 재측정 조건을 §10.1-5에 추가. 처리 열(R/I/X/F/N)이 도달 열에 기대지 않는다는 점(발동 규칙이 판정)을 명시하면 설계 영향은 없다.
* §8.4에 B33이 V3 인벤토리를 키우는 효과(실행 시간 증가, 새 인벤토리 test 기준 실행 실패 = ERROR)를 한 줄.

### S6. Phase 3 v4 교차(2-7)
입력을 v4로 바꾸고(내용 차이는 MOD 배정 없음), §3.1 교차 항목을 "**A2 승인으로 B26-1·B34가 Phase 3 전으로 확정 -- Phase 3 v4에 D0b 원자료 재측정 조건(P9·P10과 같은 방식) 추가 필요**"로 갱신해 Phase 3 design 쪽 요청으로 §9에 올린다. G1과 scope card가 `mutate_changed.py`의 같은 대상 선택(`changed_defs` 호출 앞)을 바꾸므로 병합 순서(둘 다 #1 전)를 §3.2에 적는다.

### S7. §10.6 허용오차 식
* 유도된 것: τ = 평가점 소자 tol_V 최댓값(N3.6), 전압 양의 tol_V(kind, L, VDS) -- 새 상수 없음, topology 무관(`supply_nets`만 읽음).
* 유도되지 않은 것: (i) **+τ 한쪽** 차분 -- 비단조·꺾임 근처에서 과소. (ii) **레일 하나씩의 max** -- S_B와 S_A의 전압 오차는 여러 노드에 동시에 들어가므로 1차 상한은 Σ_r |Δq_r|이지 max_r가 아니다. 계획의 같은 종류 선례(N3.6 `tol_I = tol_V × gm`, N3.8 'AC gain = 노드 허용오차를 소신호 감도로 전파한 값')가 선형 상한이다. max는 가짜 red 위험.
* 수정: tol_q = Σ_{r ∈ supply_nets} max(|q(r +τ) − q|, |q(r −τ) − q|)(1차 상한, ±τ). 이 형태를 UD-0 원칙 기본안 행으로 두고 근거를 N3.6·N3.8로 적는다. 이산 양(finger 수 등)은 섭동이 경계를 넘으면 tol_q가 커져 판정이 약해지므로 판정 기록에 양별 tol_q를 남긴다고 계약에 적는다. Δ(folded (1.8,0)→(0.9,−0.9))는 'Δ = −span/2, 계획 IC11 예와 U-26 (a)의 분할 레일 형태'로 유도 근거를 한 줄.

### S8. #43 margin·판정 경계
* 계획 N3.6 항목 8: `kvl_branch` 등식 잔차 ≤ **멤버 수 × tol_V**. N3.14 739행: 층 0 `local_infeasible`(SEAL_VIOLATION 하위, 기둥 KVL 포함)은 '예외 없음(실패 레코드), margin = 위반 크기'. 749행: margin = 위반 / 그 항목의 허용오차.
* v0.3 §11.2: "margin = 위반/`tol_V`" -- 기둥의 어느 소자 tol_V인지 없고, 판정 경계는 HEAD의 `1e-9 × max(vdd, 1)`(SR 7069) 그대로인지 계획 경계로 바꾸는지 없다. 바꾸면 동작 변경(작은 잔차가 통과), 안 바꾸면 margin 분모와 판정 경계가 서로 다른 양이다.
* 수정: #43 계약에 경계 = Σ_{멤버} tol_V(kind, L, VDS)(항목 8의 '멤버 수 × tol_V'를 소자별 값으로 -- 같은 값이면 계획 문구와 일치) 또는 '경계는 그대로, margin = 위반 / (멤버 수 × max tol_V)' 중 하나를 원칙 기본안으로 적고, 예외(`SealViolationError`) 대 실패 레코드(`local_infeasible`) 중 어느 쪽인지 N3.14 739·742행으로 정한다. #43은 #23(tol_V)을 이미 선행으로 둔다.

### S9. #13 발동 계수 측정 방법
* §10.1-4: "CC-8 `activations_out` 방식, 대상 = 하네스 4회로 + E-LIB 9회로". 그러나 `activations_out`은 card가 계측을 단 기능만 센다(`00-common` §11). D·I 지점(약 62 + 2 + 5)은 #13 전에는 계측이 없다 -- 그대로 재면 0 → DEC-76에 따라 전부 R(거부)로 바뀌고, 실제로 발동하는 지점이 정본 실행을 깨뜨린다.
* 수정: 측정 방법을 design에 정한다 -- 예: (a) 사본에 지점별 임시 계수 래퍼를 넣은 scratch 측정(저장소 쓰기 0), (b) `sys.monitoring` LINE 이벤트로 기본값 분기 실행 여부(scope-policy spec '작성 전 실측' 3이 같은 방법을 썼다). `.get(k, d)`는 키가 없을 때만 발동이므로 '줄 실행'이 아니라 '키 부재'를 재야 한다 -- (a)가 맞다. 측정 결과는 #13 spec card '작성 전 실측'에 표로.

### S10. `P3?` 열 모순
위상 정렬 실측: #19의 조상 = {#17, #18, #21, #20, #6, #5, …}, #47의 조상 = {#6, #5, …}. #6(CC-4a)은 Phase 4 선두(Phase 3 DoD 뒤)이므로 #19·#47은 Phase 3 전에 할 수 없다. 둘 다 `Y`로 고친다(#47은 S2 수정과 같이). #17·#18은 조상에 #6이 없어 '조건부 pre'가 성립한다.

### S11. #10 → #25 간선
#10 "X(15곳)의 잡는 타입을 LUT 정의역 오류로 좁힘". 그 오류의 정본은 `lut_axis_out_of_range`(SEAL_VIOLATION, 계획 LR3·DF-27) = #25. 선행에 #25를 넣거나, #10에서 좁힐 타입을 지금 HEAD에 있는 클래스로 명시하고 #25가 그 뒤 다시 좁힌다고 적는다(같은 핸들러 15곳을 두 card가 고침 -- §3.4 충돌 집합에도 추가).

### S12. 사용자 결정·착수 승인 목록(검사 6)
| 항목 | 지금 v0.3 | 고칠 것 |
|---|---|---|
| UD-14 | 대기 결정 | 승인됨 → 삭제, 기록 id 인용(S3) |
| **A1 V3 범위(1/2/3)** | 없음(#48을 결정 없이) | §7.1에 추가 또는 Phase 4 밖 결정으로 §7.3 착수 조건에(B1) |
| 면제 누수 수정 승인 `20260930-v3-exempt-binding` | 없음 | §7.3(강화지만 게이트 변경 승인 필요, scope card·#1 선행) |
| B33 게이트 승인·Q1 | 없음 | Phase 4 결정은 아니므로 §7.3에 '게이트 선행(인지)'로 한 줄 -- V3 인벤토리와 V7 판정이 바뀐다 |
| B37 확인 2건 | 없음 | §7.3 확인 기록(S2) |
| UD-1·4·5·6·7·8·9·10·15 | 있음 | 유지(회로 해석·계획 지정·기존 승인 번복·skill 경계). 최소성 문제 없음 |
| UD-6 | 권고 포함 | 유지. 단 (C)는 topology 선언 수정이라 메모리 규칙상 connectivity가 아닌 vsid·`stage_devices` 메타데이터여도 '회로 해석'이므로 공동분석 -- v0.3 서술과 일치 |
| #50 V4·V5 승인 | §7.3·§7.4 | B2 결과에 따라 형태 변경 |
결론: 최소성은 지켜졌다(새로 늘릴 '결정'은 A1 하나). 완전성은 위 4줄이 빠졌다.

---

## 6. minor

* **M1** SR 7411 `_vsb = _e.get("vsb", ref_vds if ref_dev is not None else 0.0)`(`_hr_resolve_vertical_group`)이 부록 C.2·§1.5-6·§9-6에 없다. 조건식 기본값이라 측정 규칙 밖이지만, 7579 `setdefault("vsb", ref_vds)`와 같은 묶음(주석 7406~7410이 그 관계를 적는다)이고 `0.0` 갈래가 조용한 기본값이다. C.2 vsb 행에 더하고 §9-6을 "31곳 + 조건식 1곳(7411)"으로.
* **M2** §4.3 "`derived_spec` 재사용 … 6a 면제 기록의 'Phase 4 후보' 한 건이 Phase 4 안에서 소비된다": 승인 기록 `20260930-restore-unwired-until-6a` 재검토 절은 "spec 변형이 필요한 **첫 운영 사용처**(하네스 조사·탐색 card)에서 배선"이다. #50(test-only)·#29(auditor 비교)는 운영 사용처가 아니다(B33 R3도 test 경유 도달을 세지 않는다). 면제는 그대로 남는다고 고친다.
* **M3** #50의 V4 규칙 (1) 면제는 test id(`<파일>::<test>`)에 묶이고 test 본문 해시에 묶이지 않는다 -- 면제 누수 수정 card가 같은 부류 결함을 V4 백로그로 넘겼다. #50 승인 범위 설명에 '이 test 본문이 바뀌면 재승인'을 적고 백로그 id를 인용.
* **M4** §10.4 "spec 로드당 1회, spec 객체에 보관": spec dict에 키를 더하면 `instance.json`·E-INST 정규화 해시가 바뀌어 #21 equivalence가 깨질 수 있다. 보관 위치를 spec 밖(로드 결과 객체·`RailDeclaration`과 같은 계층)으로 적는다.
* **M5** redteam 번호 충돌(2-9). #48(또는 scope card) interface에 번호를 박지 말고 '작성 전 실측의 `ls attacks`'로.
* **M6** F16·§10.6 'DF-24 검출력' 서술: DF-24의 nmos 분기는 source가 레일인 소자에도 `V(source)`를 그대로 돌려준다 -- rail_lo가 실제 전위로 바뀐 엔진에서는 레일 source NMOS도 틀린다. 반대로 rail_lo 0.0 고정이 남아 있으면(지금) 어느 소자도 0.9 V 오차가 나지 않는다. '비레일 source NMOS 수'는 검출력 지표가 아니다(B2와 같이 고침).
* **M7** 선행 열 빈칸: #37(DF-08·22 red-green) 선행 = UD-4만(#6 없음), #42(W-3) '-', C2(DF-09 `(2−α)A`, TS4 red와 같은 대상) 선행 없음. 실패 클래스를 쓰지 않으면 맞지만 그 판단을 한 단어로 적는다. 그래프는 비순환이다(§0).
* **M8** prep_b37 §4.2 C3 "`_TEMPLATE`은 `ports: null`"은 틀렸다(§3 #6: 키 없음). B37a spec card가 v0.3 F21을 쓰도록 §5.4 #47에 '`_TEMPLATE` `ports` 키 없음(재측정)'을 남긴다.

---

## 7. 검사 4 결론 -- I-C11(§11)·IC11 허용오차(§10.6)는 계획에서 유도되는가

* **§11 I-C11**: 현 상태(F15, 재측정 일치)·선택지 (A)/(B)/(C)·권고는 계획 DEC-70·71·U-09와 엔진 메시지에서 나온다. 새 상수 없음, (B)의 규칙은 이름 없는 규칙(topology 무관). 결정은 사용자 몫으로 올바르게 분류됐다. 남는 것은 #43의 판정 경계·margin 분모(S8)뿐이다.
* **§10.6**: τ와 전압 양 허용오차는 유도됐고 topology 무관이다. 한쪽 차분·max 결합은 계획에서 유도되지 않는다(S7). 그리고 이 식을 쓰는 #50의 base red 형태가 코드와 맞지 않는다(B2). 원칙 '상수를 임의로 만들지 마라' 위반은 없다(Δ는 근거 한 줄만 추가).

## 8. 권고 처리 순서
1. B1: A1 질문(이미 준비됨)을 사용자에게 먼저 -- 답에 따라 #48/#1 경로를 확정하고 §5.12를 새 spec 인용으로.
2. B2: #50 red 형태 실측(#21 상당 사본, folded S_B) → card 형태 확정. S7 식 수정과 함께.
3. S1·S2·S3·S5: 새 입력 반영(문서만).
4. S6: Phase 3 v4 쪽 재측정 조건 요청.
5. S8·S9·S10·S11·S12, minor.

## 산출물·정리
scratch `C:/g57`(사본 `repo`, `runh.py`, `m.py`, `run_*.log`, `run_summary.jsonl`)은 측정 뒤 삭제했다. 저장소 쓰기·상태 변경 git 없음(`git archive`·`rev-parse`·`status`만).
