# gain-budget-gmid-sizing -- Phase 4 `40-defect-fixes` design

> **[초안 v0.9.3 -- 저장소 미반영]** 정식 경로(계획 N9.1): `docs/02-design/features/gain-budget-gmid-sizing.40-defect-fixes.design.md`(현재 없음).
> **(v0.9.3)** 저장소를 다시 재지 않았다(저장소 읽기·쓰기 0). 입력은 7차 독립 검토 `review7_phase4_v092.md`, #21 실측 `p4_card21_rails_measure.md`(측정 판 `a796468`, 스크래치 `C:/g148` -- 그 보고의 작성자 측정, 판정 수치 아님), Phase 3 초안 v8.3(`draft_phase3_design_v8.md` 22:39 판 -- D-28 (e)·§10 E5 판정 python, 실측 `p3_scripts/p3v83_judge_scenarios.out.txt`, 읽기만), B26-1 card(`draft_b26_1.spec.md` 22:20 판, 읽기만), `b26_decision_table.md` §1.2(9회로 극성 표, 읽기만).
> **(v0.9.2)** 저장소를 다시 재지 않았다(저장소 읽기·쓰기 0). 입력은 `_drafts`의 결정·승인 초안과 Phase 3 초안 v8.2뿐이다(아래 v0.9.2 입력). 의존 그래프는 `p4v091_dag.py`(부록 A I1 -- U-BF 결함 card를 기본 노드로, Q-B34-PHASE·Q-P2DOD-E2 기록 간선 추가).
> **(v0.9) HEAD**: gate `master` = **`0f23786`**(시작·끝 같음, `git -C R rev-parse --short HEAD`). `git -C R diff --stat a796468 0f23786` = `.ai/approvals/20261001-p10b-v3-equiv.md`·P10b spec card 2파일뿐 -- 엔진·tests·tools·계획·`00-common` 변경 0이라 v0.8의 `a796468` 사실은 그대로 성립한다. v0.9에서 읽기만 해서 잰 것(`git show`·`git grep`·작업 트리 `sed` -- 쓰기·상태 변경 0. `git status --short` md5는 시작 `168fd530…`, 끝 `07dad982…` -- 차이는 저장소 루트의 추적 밖 `cfg_*.json` 15개(908 바이트, `gate_path`·`reachability_roots` 설정, 18:07~18:34 약 2분 간격 생성)뿐이고 이 작업이 만든 것이 아니다(이 작업은 엔진·게이트 도구를 실행하지 않았다) -- 오케스트레이터 확인 대상): SR `reconcile_vsb_from_nodes`·`audit_vsb_consistency` 시그니처·본문·호출부, `propagate_node_voltages` 호출부를 감싼 `except Exception`, `tests/probes/probe_full_research.py` 호출, 계획 698·1002·1101·1158·1159행, `00-common` 94~109행 절 위치, #26 재측정 grep, `merge_gate.rule10_phase`(부록 A H1~H6). 의존 그래프는 `p4v09_dag.py`(부록 A H5 -- 승인 시점 간선 포함).
> **(v0.8) HEAD**: gate `master` = `a796468` 그대로(`git -C R rev-parse --short HEAD`, 시작·끝 같음). v0.8에서 저장소를 읽기만 해서 잰 것: HEAD `git archive` 격리 복제본(스크래치 `C:/g104`, 끝에 삭제)에서 `test_ic11.py`를 `--gmid-dod` 유무로 실행(E3), `-k legacy`·`-k lut_axis`·전체 수집 수(E4·E5), `propagate_node_voltages` 시그니처·호출부, 계획 396·428·439·441·749·827행, `00-common` §7.1·§7.2·CC-9 관련 6줄(부록 A G2~G4). 의존 그래프는 `p4v08_dag.py`(부록 A G1).
> **(v0.7) HEAD**: v0.7은 저장소를 다시 재지 않았다(gate `master` = `a796468` 그대로 -- 3차 검토 §6이 HEAD 사실 11개를 재측정해 전부 일치). 이번에 읽기만 한 것: 계획 749행 margin 정규화식, `00-common` §7.2 `normalized_margin`(265행)·CC-9 행(559행). 의존 그래프는 `p4v07_dag.py`로 다시 돌렸다(부록 A F1).
> **(v0.6) HEAD**: 2026-10-01 v0.6 작성 시 gate `master` = **`a796468`**(`2d58fd8` 뒤: 계획 A2 정정 `8356c1e`, P10 test·판정 기록 `56b86c6`·`62ae24f`, P10b spec card `a796468`). v0.6에서 저장소에서 다시 잰 것은 library topology 두 개의 `bulk` 키 계수와 SR `bulk` 문자열 위치뿐이다(부록 A E2 -- `git show`로 스크래치 `C:/g93`에 꺼냄, 끝나면 삭제). 엔진 줄 인용은 v0.5 규칙 그대로(함수 이름이 정본).
> **(v0.5) HEAD 이동**: 2026-10-01 v0.5 작성 중 gate `master` = **`2d58fd8`**(`git rev-parse --short HEAD`). `7535799` 뒤 커밋은 P9 병합(`93b18db`·판정 기록 `766b5c2`), P10 문서·spec card(`0fa6ca2`·`b8d4c4d`), design 20 E4 정정(`fe638ab`), 승인 기록 2건(`2d58fd8`: `20260930-phase2-e4-phase`, **A2 `20260930-b26-before-phase3`**)이다. 엔진·하네스 변경은 `git diff --stat 7535799 HEAD -- skills/analog-gmid-design/assets/*.py workspaces tools` = **SD 1파일(+3 −14, `kcl_series_union` 안)**뿐이다 -- **SD 3041행 이후의 줄 번호는 HEAD에서 11 작다**(실측: `propose_device_roles_gap_fill` 3845 → 3834, `apply_device_roles_gap_fill` 4553 → 4542, `load_topology` 8550 → 8539; SD 3022행 이전·SR·하네스는 그대로). 이 문서의 SD 줄 인용은 `7535799` 값으로 두고(card 작성 전 실측이 다시 잰다), 함수 이름이 정본이다. 계획 정정안(`draft_b26_plan_patch.md`)은 아직 커밋 전이다(`git diff --stat 7535799 HEAD -- docs/01-plan` 빈 출력).
> 측정 시점(v0.4까지) = gate `master` **`7535799`**(2026-09-30, 2026-10-01 `git rev-parse --short HEAD`로 재확인). v0.2는 `cd64170`에서 쟀다. `git diff --stat cd64170 7535799 -- skills workspaces`는 **빈 출력**이고 바뀐 것은 `tools/gates`(B28 V3 이력 복제본: `mutate_changed.py`, redteam 공격 31)뿐이다. 그래서 v0.2의 엔진·하네스 사실(줄 번호 포함)은 HEAD에서 그대로 성립한다.
> 저장소·worktree 쓰기 0, git 상태 변경 0. v0.3 재측정 스크래치 `C:/g48`, **v0.4 재측정 스크래치 `C:/g61`**(HEAD `git archive` 사본 `repo` + 원점 이동 시뮬레이션 사본 `sim`, 끝나면 삭제). v0.4 측정 스크립트는 `_drafts/p4_scripts/`(`b2_patch.py`·`b2_eval.py`·`b2_compare.py`·`b2_run_*.sh`)에 남긴다. 발견별 변경 대응은 `phase4_revision_log.md`. v0.3 원본은 `draft_phase4_design.v03.md`, v0.2 원본은 `draft_phase4_design.v02.md`.

버전 v0.9.3(초안). v0.9.3 변경(7차 독립 검토 `review7_phase4_v092.md` 반영 -- blocking 0, should-fix 2(S1·S2), minor 4(m1~m4), 참고 R1 -- 와 #21 실측 `p4_card21_rails_measure.md`. 대응표는 `phase4_revision_log.md` v0.9.3 절. v0.9.2 원본은 `draft_phase4_design.v092.md`):
* **S1 빼낸 meta 키는 값 전체 정확 일치로 판정**: Phase 3 v8.3이 E5 판정식을 `hv == {"__dc__": "RailDeclaration", "nets": want}`(계약 밖 필드가 끼면 FAIL)로 고쳤다 -- 그 판 실측(`p3v83_judge_scenarios.out.txt` scenario p4)에서 `RailDeclaration`에 `polarity` 필드를 더한 시제품을 v8.2 식은 PASS, v8.3 식은 FAIL. Phase 4는 판정할 성분이 둘(`nets`·`polarity`)이고 #17이 `P3D`에 이미 있는 값을 바꾸므로 `bv == hv` 보호도 없다. P-37·#17 (c)·E11에 적었다: (a) 정확 일치 식 (b) `nets` 기대값 = **`P3D` library** `supply_nets`(`git show` -- HEAD에서 읽으면 그 사이 변경이 양쪽에 같은 값으로 들어간다. 그 사이 `supply_nets`를 바꾸는 card(#53~#55)가 있으면 그 card 차이표) (c) `polarity` 기대값 = design에 고정하는 9회로 표 `POLARITY_P4`(엔진 출력 아님 -- 지금 근거 `b26_decision_table.md` §1.2, `cd64170`. `P3D` library에서 판정 쪽 독립 구현으로 다시 재는 것, UD-1 답이 (C)가 아닐 때 출처를 선언으로 바꾸는 것, `e_lib_p3.py`의 `polarity` 직렬화 모양 확인이 **#17 card 작성 전 조건** -- 없으면 #17 card를 쓰지 않는다) (d) E11 통과 기준에 '빼낸 키 계약 판정 FAIL 0' (e) `ports`·`device_roles`(#47)도 같은 정확 일치(기대 = `P3D` 값 + #47 기대 차이표).
* **S2 빼는 키 목록을 판정 기준으로 design 본문에**: §6 E11 아래 'E11 빼는 키 표'에 `MASK_META_P4 = ("device_roles", "ports", "rails")`와 키마다 기대값·출처를 고정하고, '목록·출처를 바꾸려면 design 개정(승인 diff) -- auditor·DoD 브리핑은 늘리지 않는다'를 적었다(Phase 3 D-28 (e) 문장과 같은 지위). v0.9.2 E11의 'DoD 브리핑에 박는다'를 지웠다. 승인 질문 '기준에 닿는 것'에 (c)를 더했다(Phase 3 UD-0 (c)와 같은 자리). P-37은 원칙 기본안으로 남고, 목록은 그 표(사용자 몫 기준)가 정한다.
* **#21 [미확인] 닫음(실측 `p4_card21_rails_measure.md`)**: #21은 `meta`에 키를 더하지 않고 `RailDeclaration`에 필드를 더하지 않는다(`load_topology`는 spec을 받지 않는다 -- 계산 지점은 평가 문맥. 시제품 p20 → p21에서 E-LIB 해시(`rails` 포함) `c121333162fade9e` 같음, E-INST 두 회로 `raw_sha256` 같음). 그래서 #21 oracle (c) = **빼는 키·필드 없는 해시 같음**(E-LIB 9/9·E-INST, 보고 §5 문장), E11 목록에 #21 몫 없음. §10.4 '보관 위치'를 보고 권고대로 좁혔다(`load_topology`의 `meta`와 `RailDeclaration`에는 싣지 않는다 -- 실측 x2·x4가 그 오독의 두 형태이고, x4는 필드 집합을 보지 않는 masked-by-contract 판정이면 놓친다, 보고 §4.2).
* **m1** #1 oracle (c)에 '`meta["rails"]` 제외 + 계약값 정확 일치(card 계약 1·8)'를 더했다(#17 (c)와 같은 모양). **m2** 승인 질문·P-37 근거를 'Phase 2 완료 판정(승인된 선례)과 같은 방식'으로 좁히고, Phase 3 UD-0 (c)는 아직 사용자 답 전(대안 c-2 = B0 비교)이며 그 답과 무관하게 P-37이 그대로임을 적었다. **m3** #30 문서 몫의 커밋 주체(오케스트레이터 `Role: doc` 커밋, 그 card 병합과 같은 묶음), oracle 글자(§5 머리의 종류 표기 -- (b)·(c)가 없는 것), 면제 줄이 사라진 뒤 남는 승인 기록 `path::rule`의 스캐너·gate 영향 확인을 #30 card 작성 때 할 일로. **m4** `P3D`(Phase 3 DoD 측정 기록의 '대상' 커밋)를 §6 E2에서 한 번 정의하고 E2·E11이 같은 기호를 쓴다.
* **R1 U3 면제 기록 시점**: B26-1 card(22:20 판)가 '두 번 시도 절차'로 바뀌었다 -- 기록 `20261001-b26-v3-equiv-range`는 1차 시도(병합 안 함) code 커밋 K1 뒤 auditor 측정 해시로 **2차 시도 착수 전** 커밋 -- B26-1 card(`draft_b26_1.spec.md` 22:20 판) '두 번 시도 절차' 2·'승인 줄 배치' 5·착수 조건 8 인용: card 착수 조건은 아니고 2차 시도의 선행. v0.9.2의 'K 뒤·병합 전 -- 착수 조건 아님'(머리 v0.9.2 글머리, §3.2 #1 행, §3.3 도식, §5.1 #1, §7 'v0.9.2 대비'·요약, §7.3)을 이 card 인용으로 고쳤다.
* 그대로인 것: card 수(계약 49 + 조건부 5), 간선, 새 사용자 결정 0(S2 (c)는 새 결정이 아니라 UD-0 승인이 덮는 기준을 질문에 드러낸 것).

버전 v0.9.2(초안). v0.9.2 변경(v0.9.1 뒤의 사용자 결정·오케스트레이터 결정 반영 -- 독립 검토 회차 아님. 대응표는 `phase4_revision_log.md` v0.9.2 절. v0.9.1 원본은 `draft_phase4_design.v091.md`):
* **Q-B34-PHASE 결정됨**("phase 3 + 정정 기록 (Recommended)", 기록 `20261001-b26-phase3-cards`, decision): B34(#45)·B26pre·backfill·B26-1(#1) 네 card는 머리 `phase: 3`, 병합 순서는 그대로(Phase 2 DoD 뒤·Phase 3 M card 전), Phase 2 DoD N6.3 목록 밖, design 30 승인·U-03을 기다리지 않는다. 이 문서의 'phase 2' 표기(§1.3·§1.4·§3.1·§3.2·§3.3·§4.3·§5.1·§5.12·§7·§8.1·부록 C.3)를 'phase 3'으로 고쳤다. 간선은 바뀌지 않는다(§9-19 닫음).
* **U-BF 결정됨**("결함으로 고침 (Recommended)", 기록 `20261001-b26-backfill-interdig-fix`): backfill 결함 card `20261001-b26-backfill-interdig-final-audit`(red-green, phase 3)이 확정 순서 B26pre 뒤·B26-1 앞에 **조건 없이** 들어간다(v0.9의 '[U-BF 답이 고침이면]'을 지움, §3.2 새 행). DAG에서 시나리오 S9가 아니라 기본 노드다(부록 A I1).
* **B26-1 U3·U4·U5 결정됨**(B26 묶음 4문항): U3 "정리 2줄 + 면제 1" -- B26-1이 동작 불변 정리 C1·C2를 하고 `range` const− 1개만 변이 id@def 해시로 면제(약화 승인 1건, 기록 `20261001-b26-v3-equiv-range`는 ~~code 커밋 K 뒤 auditor 측정 해시로 병합 전 커밋 -- 착수 조건 아님~~ **(v0.9.3, R1)** 1차 시도(병합 안 함) code 커밋 K1 뒤 auditor 측정 해시로 **2차 시도 착수 전** 커밋 -- B26-1 card(`draft_b26_1.spec.md` 22:20 판) '두 번 시도 절차' 2·'승인 줄 배치' 5·착수 조건 8 인용: card 착수 조건은 아니고 2차 시도의 선행), U4 = 기록 `20260930-b26-b40-reason-key`(decision), U5 = 기록 `20261001-b26-p9-signature-update`(diff). v0.9의 **U2-a(SR 11802 등가 면제, N2d로 잴 때만)는 없어졌다** -- 최종 V3 규칙은 N2(b) + 넓힌 T6이고 N2d를 쓰지 않아 SR 11802는 대상 밖이다(`b26_survivor_final_question.md` 13·51행).
* **Q-P2DOD-E2 결정됨**("문구 정정 (Recommended)", 기록 `20261001-p2dod-e2-wording`): Phase 2 DoD E2 = 'exit 0, 면제되지 않은 발견 0(현재 면제 `20260929-p4-scan-exempt` 1건)'. 이 Phase의 몫은 그 기록 '재검토' 절 하나다 -- 면제를 해소하는 #30(VGS 기준 gm·gds 공개 조회)이 같은 card에서 design 20 §10 E2의 '현재 승인 … 1건' 문구를 고친다(§4.3 표·§5.6 #30). DAG: Phase 2 DoD ← 그 정정 기록(DoD 측정 판 H가 정정 커밋을 포함).
* **E-LIB 비교 모양을 Phase 3 v8.2 E5 선례에 맞춤(P-37 -- 원칙 기본안, UD-0이 덮음)**: Phase 3 v8.2(`draft_phase3_design_v8.md` 21:19 판, 읽기만)는 E5 기본안을 'Phase 2 DoD 대상 커밋 `P2D` 대 Phase 3 마지막 병합본, 사이 card가 의도적으로 바꾼 필드만 그 card 계약값으로 따로 판정(`MASK_META = ("rails",)` -- B26-1 계약값 `RailDeclaration(nets = supply_nets)`, `EXCL_INST` 없음), 나머지 해시 같음'으로 바꿨다(선례 `20260930-phase2-e4-baseline`, 원칙 '같은 상황의 사용자 선택을 따른다'). 이 문서 점검 결과: (1) **E2는 이미 같은 모양**이다(base = Phase 3 DoD 병합본, head = Phase 4 마지막 병합본, 바뀐 항목마다 원인 card id + DEC-40 기록). (2) **E11의 'E-LIB 재측정'은 비교 base와 모양이 적혀 있지 않았다** -- 같은 모양으로 적었다(base = Phase 3 DoD 대상 커밋 `P3D`, Phase 3 D-28의 `e_lib_p3.py` 한 사본, 빼는 meta 키 = 이 Phase card 계약에서 유도한 목록). (3) **Phase 4 card가 그 masked 필드를 다시 바꾼다**: #17(B26-2)이 `RailDeclaration`에 `polarity` 필드를 더하므로(§10.3) `meta["rails"]` 값이 Phase 4에서 또 바뀐다 -- #17 oracle (c)의 'E-LIB 9/9 [prep 무동작]'은 그 키에서 맞지 않는다. #17 (c)에 '`meta["rails"]`는 계약값(nets = `supply_nets`, polarity = 구조 규칙 결과)으로 따로, 그 밖 meta 해시 같음'을 더했다. #47(B37a)은 이미 E-LIB 기대 차이표(`meta["ports"]`·`meta["device_roles"]`)이고, #53·#54·#55는 topology 데이터 변경이라 그 card 차이표 + DEC-40이다. #21의 `rail_voltages` 보관 위치는 'spec dict 밖, `RailDeclaration`과 같은 계층'(§10.4)이다 -- `meta["rails"]` 안에 들어가는지는 [미확인](#21 작성 전 실측, 들어가면 #21 oracle과 E11 목록에 더한다). **(v0.9.3) 닫음 -- 들어가지 않는다**(실측 `p4_card21_rails_measure.md`: #21 oracle (c) = 빼는 키 없는 해시 같음, E11 목록에 #21 몫 없음). Phase 3 E5에는 영향이 없다(#17은 F2 뒤 단일 경로, P-35). §9-24는 닫았다. **(v0.9.3, S1·S2)** 빼낸 키의 계약값 판정은 값 전체 정확 일치이고, 목록과 출처(nets = `P3D` library, polarity = 고정 9회로 표)는 §6 'E11 빼는 키 표'가 판정 기준으로 정한다.
* **v0.9.1 m-2 정정**(`review_b26_final.md` F2, `pending_questions.md` '[Q-B34-PHASE 정정]'): card phase가 `strict_set`(1042행)에 쓰이는 것은 맞지만 phase 2(판정 기록 15건 `activated_ic_case` 합집합)·phase 3(0건) **둘 다 빈 집합**이고 저장소에 phase 2·3 `gmid_ic` 표식이 0개라, phase 2/3 선택이 바꾸는 것은 V1 `--gmid-phase=` 토큰·Phase DoD 집계·A2 ③ 문구뿐이다. v0.9.1의 '엄격 집합도 바뀐다'를 고쳤다(머리 v0.9.1 글머리와 §7 'v0.9 대비'는 기록으로 두고 §7 'v0.9.2 대비'·§9-19·부록 A H6에 정정).
* **백로그 번호(오케스트레이터 확정)**: 이 문서가 제안한 B48(VS 0.2 V 보간 오차)·B49(sf_pushpull 그룹 누락)·B50(측정 사본 analog-grammar 동봉)은 오케스트레이터 백로그가 B48(test_lint 빈 컨테이너 오탐)·B49(design 20 §8 P6·P8 판정 유형)·B50(층위1 폴백 중복)에 이미 썼으므로 **B51·B52·B53**으로 바꿨다(§1.4·§7.2 P-5·§9-12, v0.5 머리 기록 줄).
* 대기 목록: §7 요약의 'Phase 3 전 card를 막음' 행이 비었다(U-BF·Q-B34-PHASE·U2-a·U4·U5 모두 닫힘). card 수(계약 49 + 조건부 5)와 새 사용자 결정 0은 그대로다.

버전 v0.9.1(초안). v0.9.1 변경(6차 독립 검토 `review6_phase4_v09.md` 반영 -- blocking 0, should-fix 1, minor 2. 대응표는 `phase4_revision_log.md` v0.9.1 절. v0.9 원본은 `draft_phase4_design.v09.md`. 이번 판은 저장소를 다시 재지 않았고 m-2의 `merge_gate.py` 줄만 gate `master` `0f23786`에서 `git show`로 재확인했다):
* **R6-S1 P-36 vsb 비트 동일은 무동작이 아니다**: 6차 검토 실측에서 current_reuse reconcile이 호출마다 M58 vsb의 2 ulp 차이(1.11e-16 -- SR 7294 부분 그래프 `_bn_pair` 전파가 남긴 값)를 덮어써 정본 θ*(`L_class__M68`·`L_class__M8` 마지막 자리)와 metrics 해시가 바뀐다. §5.5 #23의 '무동작' 기대를 지우고 동작 변경으로 적었다(기대 차이표에서 F27 노드 충돌 거부 차이와 행을 가름). P-36·머리 N-S2·§9-26의 근거 문장 '같은 노드전압에서 다시 계산한 값의 일치'는 틀렸으므로 '저장값과 전체 그래프 재계산의 일치, 부분 그래프로 쓴 vsb가 ulp 단위로 다를 수 있음'으로 고쳤고, '두 함수 같은 규칙' 결론은 유지했다. §7.4에 DEC-40 예상 한 줄(current_reuse θ*·metrics 해시)을 더했다. 새 사용자 결정은 아니다(DEC-40 발생 시 건별). 승인 질문 UD-0에 한 문장을 더했다.
* **m-1** §7 결정 상태 요약에 계획 1158행을 더했다(1158·1159 두 행).
* **m-2** §7 '대비' 문단과 부록 A H6: card phase는 `rule10_phase`(V N/A 허용)뿐 아니라 V1 `--gmid-phase` 강제(1009~1010·1213행)와 같은 Phase 엄격 집합(1042행)에도 쓰인다 -- Q-B34-PHASE 답이 B34·B26-1·b26pre·backfill card의 V1 실행 옵션과 엄격 집합을 바꾼다. 결론은 '이 문서 card의 판정은 같다'로 좁혔다.

버전 v0.9(초안). v0.9 변경(5차 독립 검토 `review5_phase4_v08.md` 반영 -- blocking 0, should-fix 4, minor 9. 대응표는 `phase4_revision_log.md` v0.9 절. v0.8 원본은 `draft_phase4_design.v08.md`):
* **N-S1 앞당김 경로를 지운다(원칙 기본안 (가))**: #2·#3·#4·#17·#18의 선행인 UD-0·UD-1·UD-15는 Phase 4 착수 때(Phase 3 DoD 뒤) 올리는 승인 질문에 들어 있다. 그 질문 시점을 간선으로 넣으면 'D0b 전 앞당김'은 순환이다(부록 A H5 RC1·RC8·RC9 -- 5차 검토 실측 재현). 그래서 다섯 card는 **F2 뒤(Phase 4) 단일 경로**이고, UD-0 문안의 '앞당길 때는 D0b 전에만'을 지웠다. 근거: (1) 앞당김을 남기려면 D0b 전에 별도 사용자 질문이 하나 더 필요하다 -- 사용자 결정을 늘리는 쪽은 기본안이 될 수 없다(메모리 '결정은 원칙으로 기본안부터') (2) 앞당김의 이득은 작다 -- #2~#4는 Phase 3 이동 대상이 몇 함수 줄어드는 것뿐이고(§3.1 끝 문단), 계획 N3.10 '등급 D 함수는 옮기기 전에 처리한다'는 걸리지 않는다: D-1~D-7은 지금 U-02 승인으로 `보류(Phase 4)` 행이고 삭제·이관(등급 D)으로 바뀌는 것은 UD-0 승인 **뒤**라, Phase 3은 보류 행을 옮기는 것이지 D 함수를 옮기는 것이 아니다(비용 = Phase 4가 옮겨진 자리에서 지움 -- §3.2). #17·#18은 확정 순서 밖 (3) Phase 3 v7 D-27('기본값 F2 뒤, 앞당기려면 D0b 전')보다 좁은 선택이라 충돌하지 않는다. (나)(별도 승인을 D0b 전에 받는 경로)가 비순환이라는 것은 정보로만 남긴다(H5 N1). §9-9의 N6.1 정정이 유일 경로다.
* **N-S2 #23 범위를 형제 기본값까지 넓힌다**: HEAD `0f23786`에서 `tol=1e-6`이 세 함수에 있다 -- `propagate_node_voltages`(노드 충돌, SR 3729), `reconcile_vsb_from_nodes`(vsb 덮어쓰기 조건, 3808·3843), `audit_vsb_consistency`(vsb 감사 게이트, 3850~3851·3875). 그리고 `audit_vsb_consistency`는 자기 `tol`로 vsb를 비교하고 3863에서 `**kw`만 `propagate_node_voltages`로 넘겨 **이름이 가린다**(호출자가 `tol=`을 줘도 노드 충돌 쪽에 닿지 않는다). #23은 (i) 노드 충돌 허용오차를 두 함수에서 **키워드 전용 `node_tol`(기본값 없음)**로 받아 명시 전달하고 (ii) 두 함수의 vsb 비교 `tol`을 **없앤다** -- vsb 비교는 저장된 vsb와 전체 그래프 노드전압에서 `derive_vsb_from_nodes`로 다시 계산한 값의 일치이고 **비트 동일**이 원칙 기본안(새 상수 없음). **(v0.9.1, R6-S1 정정)** v0.9의 '같은 노드전압에서 다시 계산한 값'은 틀렸다 -- SR 7294·7449가 부분 그래프로 쓴 vsb가 남아 ulp 단위로 다를 수 있다(current_reuse M58 2 ulp). 그래서 '1e-6 → 0은 강화'는 audit에만 맞고, reconcile 쪽은 그 차이를 덮어써 current_reuse 정본 θ*가 바뀐다(동작 변경 -- §5.5 #23, §7.4 DEC-40). '두 함수 같은 규칙' 결론은 그대로다. 기본값을 없앨 때 **TypeError가 조용히 삼켜지는 경로**가 있다: 호출부 SR 7294·7449는 `except Exception: … = None`(7297·7451, 부록 C.1 `R #13`) 안이라 #13 전에 #23이 병합되면 인자 누락이 '노드값 없음'으로 바뀐다 -- 그래서 #23 oracle에 호출부 전수 AST 단언을 더했다(§5.5 #23, F36).
* **N-S3 CC-9 앞당김 정정 대상에 계획 N9.1 1159행**(`50-failure-cache` 행의 "`00-common` CC-9(`normalized_margin`)")을 더했다(§9-22) -- `40-defect-fixes` 행(1158행)으로 옮긴다. 계획 1002행(N6.1 Phase 5 '… margin 반환')은 실패 캐시의 margin 반환이라 **변경 없음**으로 적었다. 둘 다 `plan_tables_hash` 입력 밖(계획 698행 EL3 -- 입력은 N4.1 `담당 Phase`·`강제 test`, N4.2 `도입`, N6.1 `Phase` 열, N3.12.2)이라 승인 종류는 문안 diff(UD-0).
* **N-S4 DAG 스크립트**: `p4v08_dag.py`가 주석 안으로 삼킨 간선 3개(#6 → #10, #25 → #10, #17 → #18)를 별도 문장으로 복원하고 승인 시점 간선을 더한 `p4v09_dag.py`로 다시 돌렸다(부록 A H5 -- 23 시나리오 전부 기대대로, 예기치 않은 결과 0).
* minor m-1~m-9: 승인 질문 `00-common` 절 번호(§3.3), G4 265행 '읽기만'(m-1), §3.3 (i) 글머리의 v0.7 문장(m-2), #26 재측정 명령(m-3 -- HEAD에서 33줄), §10.7 첫 문장의 철회 근거(m-4), #13 `fallback_events` 값 문구(m-5), 반복 상한 문구 '없앰 -- 진전 없는 pass에서 끝남'(m-6), §9-25 `plan_tables_hash` 판단 확정(m-7), 대기 목록 갱신(B26pre U1 = 원칙 기본안, 새 **U-BF**·**Q-B34-PHASE** -- m-8), U-26 (a) 확인 대상 = 세 회로 값과 nmcnr 중간값만(m-9). 정보 3건(§10.6-0 분모의 앵커 단위, #14 θ*와 Phase 5 실행 기록, #26 'CGS+CGD+CGB ≈ CGG' 허용오차)도 한 줄씩 넣었다.

버전 v0.8(초안). v0.8 변경(4차 독립 검토 `review4_phase4_v07.md` 반영 -- blocking 1, should-fix 9, minor 6. 대응표는 `phase4_revision_log.md` v0.8 절. v0.7 원본은 `draft_phase4_design.v07.md`):
* **B1 E3·E11을 `--gmid-dod`로**: HEAD 복제본 실측(부록 A G2) -- `test_ic11.py`를 `--gmid-phase=4`만으로 돌리면 `pytest.fail()` 한 줄짜리 rail2가 **XFAIL**(3 xfailed), `--gmid-dod`를 더하면 **FAILED**(1 failed, 2 xfailed). E3 명령에 `--gmid-dod`를 넣고, E11은 `PT` 전체와 `PT --gmid-dod` 전체 **두 실행**(사용자 결정 A3 선례, design 20 E4와 같은 형식)이다.
* **S1 `-k` 선택을 node id 목록으로**: `-k legacy`는 HEAD에서 MG1과 무관한 test 1개(`test_ts3_no_print_verdicts.py::test_target_set_includes_legacy_scripts`)를 고르고, `-k lut_axis`는 0개다(부록 A G2). E4·E5·E10은 card interface card가 정하는 node id 목록을 실행하고 '수집 수 = 목록 수, 전부 PASS'로 판정한다.
* **S2 margin -- `normalized_margin`(CC-9)을 #23으로 앞당긴다**(원칙 기본안, UD-0이 덮음): 분모가 정의되는 레코드(#23 노드 충돌 = 봉인 항목 1, 분모 tol_V)는 수, 분모가 없는 레코드(#43 기둥 VDS 합 -- 계획 396행 '검사 대상이 아니다', #25 축 밖 -- LR3에 허용오차 없음)는 같은 함수가 `null`을 돌려준다. 계획 749행 '분모가 정의되지 않으면 `null`(빠뜨린 것과 구분)' 그대로이고, v0.7의 'IC9 때문에' 근거는 틀렸다(계획 IC9(827행)는 '중복 복붙 -- 레지스트리 정본 하나', 6b; 'margin을 계산하는 곳은 이 함수 하나'는 `00-common` §7.2의 문장이다). `00-common` 문구 정정은 §9-22(결정됨).
* **S3 #53 (i) 잠재 순환 제거**: 노드 고정 값의 스키마·읽기 경로를 #21·#22와 맞추면 하드 간선이 생기고 권고 #53 → #23은 없다. 읽기 경로는 먼저 병합되는 card가 만들고 다른 card가 재사용한다(§3.3). DAG에 R3·R4(순환 대조)·R5(비순환) 시나리오를 넣었다(부록 A G1).
* **S4 Phase 3 v7과 맞춤**(읽은 판: `draft_phase3_design_v7.md` mtime 2026-10-01 16:45:58, 178,205 바이트, sha256 `87c63513…a5dad85e` -- 작성 중 판): **D-27 엔진 card 동결**(D0b 병합 ~ F2 병합 동안 엔진 파일을 바꾸는 Phase 3 밖 card 병합 금지). #2·#3·#4·#17·#18은 확정 순서에 없으므로 **기본값 = F2 뒤(Phase 4)**, 앞당기면 **D0b 병합 전에만**(그때 v7 §9.1 재측정 (1)에 포함). v0.7의 '#2·#3·#4 Phase 3 전 아무 때나', 'B26-2·B26-3 Phase 3 전 가능'을 고쳤다.
* **S5 #55 엔진 몫 oracle**: 합성 topology(선언 `bulk`가 source 넷인 소자와 아닌 소자의 vsb), `bulk`가 netlist 밖이면 `SchemaRejectedError`, `bulk` 미선언 library 회로 무동작.
* **S6 근거 없는 기본 인자 제거를 #23 범위로**: `propagate_node_voltages(…, tol: float = 1e-6, max_passes: int = 50)`(SR 3727~3729). `tol` → 기본값 없는 인자, 호출부는 tol_V(계획 N3.6 439행, 봉인 항목 1 428행). `max_passes` → 제거(진전 없는 pass에서 멈추는 루프라 pass 수 ≤ 소자 수 + 1이 알고리즘에서 나온다). 노드에 tol_V를 대응시키는 규칙은 계획에 없어 기본안 + 정정 요청 §9-25.
* **S7 E-INST 해시를 바꾸는 #13을 §7.4에**: `fallback_events` 최상위 키가 4회로 E-INST와 Phase 3 D-25 기대 해시를 바꾼다. #14의 θ* 기록 위치 = 실행 기록 JSON(`instance.json` 밖)으로 정해 #14는 E-INST 불변을 계약으로 둔다.
* **S8 문서 밖 규칙을 문서 안으로**: #26 G1~G6 내용, F8 함수 목록, §8.4 측정 사실을 이 문서에 옮겼다. oracle (d) 출처는 커밋된 문서 -- 공동분석 확인표·B21 (c) 재현 입력은 `docs/03-analysis/gain-budget-gmid-sizing-40-defect-fixes/`에 커밋한다(§5.10, §5.5).
* **S9 P-34 원인 보존 두 줄**: 혼합 사유 집계 규칙, `SearchFailedError.record.detail`에 시작점별 마지막 실패 클래스·계수. #25 oracle에 실행 수준 판정.
* minor m1~m6(§10.6-0 margin 비교 규칙, §10.7 `except` 경로 표, §8.4 수집 수 886, E3 실행 범위, #1 행 (5) B26-1 v4 상태, §11.2 계획 396행 근거·§9-23 닫음).

버전 v0.7(초안). v0.7 변경(3차 독립 검토 `review3_phase4_v06.md` 반영 -- blocking 1, should-fix 7, minor 7. 대응표는 `phase4_revision_log.md` v0.7 절. v0.6 원본은 `draft_phase4_design.v06.md`):
* **B1 확정된 사용자 순서 채택**(`user_decisions.md` 2026-10-01 "card 순서" -- v0.6 작성 4분 뒤 기록): P10b → **Phase 2 DoD** → 면제 묶기(34) → 범위 정책(35) → B34(#45) → **B26pre**(`20260930-b26-pre-test-strengthen`, test-only) → B26-1(#1) → B33(33) → Phase 3. **B34·B26-1은 Phase 2 DoD N6.3 목록 밖**이다 -- §9-19를 읽기 **(나)**로 닫았다. Phase 3 부분("T0·G1(32)·D0a·D0b·M…")은 card **묶음**이고 실제 순서는 Phase 3 design(G1 → D0a, T0 독립)을 따른다(글자 그대로 간선으로 넣으면 순환 -- 부록 A F1 C2). #1 착수 조건에 Phase 2 DoD PASS와 B26pre 병합을 더했다.
* **S1 #43 margin = `null`**(계획 749행 '분모가 정의되지 않으면 null' 그대로 -- 새 분모를 만들지 않는다). 허용오차 기반 경계와 margin은 6b, margin 계산 함수 `normalized_margin`(CC-9, `00-common` §7.2)은 Phase 5(`50-failure-cache`). Phase 4의 margin 비교(§10.6-0·E2·#51)는 '둘 다 `null`이면 같음'.
* **S2 X 핸들러 규칙 하나로**(P-34 확장): X 지점은 후보를 배제하되 배제 사유를 클래스와 함께 모으고, 모든 후보가 축 밖으로 배제되면 `SealViolationError`(`lut_axis_out_of_range`)를 올린다. X 핸들러가 잡는 타입 = MOD1 정의역 오류, 변환은 집계 지점(MOD4 이상). #25가 만들고 #10이 유지한다. MOD1 정의역 오류 인터페이스는 §10.7.
* **S3·S4·S7 갈래 간선**: #54 엔진 갈래면 #23 → #54(하드)이고 권고 #54 → #23·#21은 없다. UD-17e (ii)가 #22 병합 **뒤**에 결정되면 #55가 엔진 몫(거부 해제 + 선언 bulk 읽기)까지 맡는다(기본). #53 UD-17c (i)·(ii)는 `propagate_node_voltages` 충돌 집합에 들고 #6 → #53, 노드 고정 전위의 출처는 하나(`supplies_v`와 한 스키마인지 card가 정함, DEC-68).
* **S5 #54 포화는 판정이 아니라 기록**: Phase 4에는 포화 경계를 정하는 계획 유도 규칙이 없다(DF-25는 6b). '선언 최소 vds' 상수(하네스 `min_vds_by_role` 0.2 -- DF-20이 없애는 폴백 상수)를 oracle에 쓰지 않는다.
* **S6 결정 목록**: 확정 순서를 결정됨에, B26-1 U3을 B26pre의 질문으로 바꿨다 -- 새 사용자 결정은 **B26pre U2(등가 후보 9개 처리) 하나**이고 그 권고안 (a)는 면제 = 판정 약화다.
* minor m1~m7(낡은 문장, P-33 승인 경로, MOD1 정의역 오류 인터페이스, τ 근거, #55 데이터 출처, #54 메타데이터 예시, DAG E3 주석).

버전 v0.6(초안). v0.6 변경(새 입력 반영 -- 독립 검토 회차 아님, 대응표는 `phase4_revision_log.md` v0.6 절. v0.5 원본은 `draft_phase4_design.v05.md`):
* **UD-17 공동분석 자료 반영**(`ud17_coanalysis_pack.md`, 이하 [pack]): (1) folded X·Y 충돌 1.6 V = 극성 부호 0.4 V(UD-17a 몫) + **tail 컬럼 KVL 공백 1.2 V**(입력 CM 미선언 -- UD-17c 몫). 그래서 **UD-17a만으로는 X·Y가 닫히지 않고(1.2 V 남음) UD-17a와 UD-17c가 함께 #53을 막는다**. X·Y가 닫혀도 출력 컬럼 1.0 V·Y 컬럼(Vg9) 0.5 V 공백이 남는다(F32). M7 vsb는 Vg9를 정하는 경로에 따라 0.95(Y 경로)/0.45(M9 경로)다. (2) current_reuse에서 UD-17d (i)(출력단 VGS 0.677 V가 의도)이면 꼬리 M5 vds가 0.0273 V(포화 밖 추정, 미측정)이고 **M2a·M2b vsb 0.9227이 파생값이 아니라 진짜 축 밖**이 된다 -- bulk 질문(UD-17e)이 M2a·M2b로 넓어진다(F33). (3) **topology에 `bulk` 필드가 없고(두 회로 0/13·0/51) 엔진은 레일 bulk만 가정한다**(SR `bulk`는 `derive_vsb_from_nodes` docstring 두 줄뿐) -- bulk = 자기 source 선택지는 사용자 connectivity 변경 + 승인된 엔진 배선 card가 필요하다(F34). (4) folded json 설명 주석 3곳이 connectivity와 어긋난다(F35, 메타데이터 정정 대상). → #53 범위·의존을 UD-17a + UD-17c 공동 게이트로 다시 쓰고(UD-17c 갈래별 판정 형태), #54를 UD-17d(Vom1·Vop1)로 좁히고 bulk를 **#55**(UD-17e, 데이터 + #22의 `bulk` 해석)로 나눴다. UD-17a~e 문구 정정, P-32 근거 정정.
* **Phase 3 초안 v6 반영**(`draft_phase3_design_v6.md`): `validate_theta_declaration_order` → **MOD3 확정**(W-1 #40 모듈), `optimize_full_circuit_budget` Phase 3 위치 MOD8·`load_topology` MOD3가 UD-0 N3.10 개정 문안(`p3_doc_amendments.md` §1)에 들어감, D-19는 **따로 묻는 질문**(MOD2/MOD3 -- #1·#17·#47 모듈), **D-22**(재수출·import 줄 위치, 함수 안 지연 import 우회 금지, IMPORT-ANY)의 Phase 4 몫 = 새 공유 기호의 모듈 배치 원칙 P-33·P-34(`FallbackEvent`·`record_fallback`, LUT 축 밖 오류의 raise 위치), **D-23**(phase 3 card는 Phase 2 DoD 뒤), D-24(무관), **D-25**(M10 진입점 test 회로 = 가장 싼 library 회로, 기록상 folded -- #23·#25·#53이 그 test 기대 해시를 바꾸면 DEC-40, §7.4).
* **B34 최종·B26-1 최신**: B34 최종판(`draft_b34.final.spec.md`, `b34_commit_plan.md`)이 **사이트 10·14를 B26-1 → B35로** 옮겼다(B26-1 card v4, 근거 `review2_b26_1.md` B2 E2·E2b -- 내어쓰기로 블록 전체가 V3 대상이 되고 생존 13 + 1). #1 몫 = 사이트 9·10b·13 + B40, B35(#49 또는 #17) 몫 = 5~8·10·14. B26-1 v4(작성 중, `b26_1_revision_log_v4.md` 없음)의 새 착수 조건 U3(계약으로도 죽지 않는 V3 생존 변이 -- 앞선 test-only card 또는 해시 묶음 면제)·U4(B40 추가 승인)·U5(P9 시그니처 단언 갱신 V5)를 반영했다. V3 수치는 review2 재측정(N2b 265 / 넓힌 T6 314~336, 생존 72 -- 사이트 10·14 포함)이 최신이고 v4 범위 재측정은 card 몫이다. 순서 문서 두 개(Phase 3 v6 §8.1 필수 순서 대 `b34_commit_plan.md` §1 작업 순서)가 Phase 2 DoD 위치에서 서로 순환한다 -- §9-19.
* **결정 목록**: B33(게이트 변경 승인 + Q1 "(a) 호출 위치만")을 결정됨으로(`user_decisions.md`). card 수: 계약 49 + 조건부 5(#55 추가 -- (v0.7 정정) v0.6 머리의 'card 수 50'은 §5.12 합계와 어긋난 문장이었다). 의존 그래프는 `p4v06_dag.py`로 갈래별 비순환(부록 A E3).

버전 v0.5(초안). v0.5 변경(새 입력 반영 -- 독립 검토 회차 아님, 대응표는 `phase4_revision_log.md` v0.5 절):
* **UD-17 분해**(`prep_ud17_f26_f27.md`): F26·F27의 원인을 회로별로 갈랐다. folded = 원인 3개((a) M1·M2 pmos 선언과 NMOS 입력 폴디드 캐스코드 연결 패턴의 충돌 -- `tail`에서 KCL 불가, (b)(c) fold_group singleton 우회가 Y·출력 컬럼 KVL을 닫지 않음), current_reuse = 원인 1개(첫 단 출력 Vom1을 컬럼은 0.9 V, 출력단 VGS 구속은 0.677 V로 정함 -- 꼬리 M5 VDS 27 mV). θ* 축 밖 소자는 folded 4개 전부·current_reuse M2a·M2b가 F27 파생이고 진짜 LUT 범위 문제는 current_reuse M9a·M18a(0.825 V, 클램프 오차 0.7 %)뿐이다. **folded의 지금 사이징은 비물리 동작점 위의 값**이다. UD-17을 **UD-17a~e**로 나누고(§7.1), 원칙 기본안 7개를 P-26~P-32로 확정했다(조용한 클램프 거부, 충돌 노드에서 vsb 유도 금지, 축 밖 오류 고유 클래스 전파, 외삽 금지, U-27 VS 상한 1.8 V 유지, #22 abs가 M7을 덮지 않음). 결과 card **#53**(folded, UD-17a·b·c)·**#54**(current_reuse, UD-17d·e)를 더하고, **파일럿(current_reuse, 계획 N0.4)이 #23 뒤 실패로 바뀌므로 E3 성공 단위·E8 `status=ok`가 #54에 걸린다**(§5.10, §6, §10.6-0). 부수 발견 M2a·M2b W 불일치(19.8 대 16.7 µm)는 #24(DF-01) 실사례, 축 밖 오류 오귀속은 #25 계약, gm/ID 근 모호성은 #31 기록으로 배치했다.
* **V3 수치**: A1-b 정정(2026-10-01 "규칙을 안내에 맞게 넓힘" -- 넓힌 T6)으로 B26-1 대상 228 → **294**(현실 하한 0.88 h, 미실행 줄 대상 6 → 9). B37a v2는 N2 대상 **81**(승인 당시 T6 분류기로 셈 -- 넓힌 T6 재분류 필요). B34 최종 4 def·55변이 55/55, 넓힌 T6 대상 10. B33 개정(blocking 3 반영)으로 V3 인벤토리 쌍 33,991 → **44,493(1.31배)**(v1 79,809 폐기). redteam 번호는 Phase 3 v5 D-18 확정(G1 32, B33 33, 면제 묶기 34, 범위 정책 35).
* **순서**: B34 → B26-1 고정(B26-1 착수 조건 4), 34·35 → B26-1, B34와 34·35 사이는 자유. Phase 3 v5가 v0.4 §9-11 요청(D0b 재측정 조건)을 반영했다.
* **결정 목록**: A1-b 정정을 결정됨으로, B37a 승인 질문 Q1~Q3를 **UD-18**로 올렸다(card approval 기록 = decision). 백로그 B39~B47 반영, v0.4의 VS 간격 제안 번호 B44는 `backlog_additions.md` B44(B34 docstring)와 겹쳐 **B48**로 바꿨다((v0.9.2) 오케스트레이터 백로그가 B48~B50을 다른 항목에 써서 **B51**로 다시 바꿨다 -- §9-12). 의존 그래프는 하드·권고 간선 모두 비순환(부록 A D4).

v0.4 변경(2차 독립 검토 `review2_phase4_v03.md` 반영):
* blocking 2건: **B1** V3 범위는 사용자 결정 A1과 새 게이트 card 둘(면제 묶기 `20260930-v3-exempt-binding`, 범위 정책 `20260930-v3-changed-stmt-scope`)의 **인용**으로 바꾸고, 선택지별 #1 경로(선택지 1 = 현 규칙 유지 포함)를 적었다(§3.2·§5.12·§7.1). **이 문서를 쓰는 동안 A1이 결정됐다**(`user_decisions.md` 2026-10-01: A1-a 면제 묶기 승인, A1-b **선택지 2 = N2**, def 머리 변경은 좁은 판 (b)) -- 표는 결정 기록으로 남기고 실행 경로는 2로 확정했다. **B2** #50의 red 형태를 `C:/g61`에서 실측했다(F25): #21만 병합된 엔진에서 folded S_B(+0.9, −0.9)는 S_A와 **비트 동일**이라 IC11 rail2는 처음부터 PASS다(어떤 xfail 형태도 strict FAIL). 그래서 #50을 없애고 IC11 rail2 test와 감도 전파 helper를 **MG1 #21의 test 커밋**으로 옮겼다(계획 N3.16 MG1 행 802행 "옛 키 거부 게이트 + IC11"). 같은 측정에서 **folded의 HEAD 실행 자체가 LUT VS 축 [0, 0.8] 밖을 조회한다**(F26: θ* 소자 vsb M1·M2 1.6, M5 1.8, M7 −0.65 -- 지금은 조용히 클램프)는 것이 나왔다. 축 밖을 거부하면 전 격자점 infeasible이므로 #25(DF-27)의 순서·IC11 대상 회로·E1·E2에 영향이 있다(§5.6 #25, §10.6). DF-24의 red는 #22의 함수 수준 합성 픽스처이고, IC11은 #22 전후로 계속 PASS다(§5.4, §10.6).
* should-fix 12건·minor 8건: B34 축소(4 def, phase 2) 반영과 사이트 인계, B37a/B37b 분할, UD-14 승인됨(A2), B33 게이트 card, Phase 3 v4 교차, §10.6 ±τ 레일별 합, #43 경계·margin, #13 발동 측정 방법, `P3?` 모순, #25 → #10, 결정·승인 목록, SR 7411 등. 대응표는 `phase4_revision_log.md` v0.4 절.

**(v0.9) Phase 3 판**: 5차 검토 시점 v7은 17:29:50 판(183,204 바이트, sha256 `40f7447b…dd4f103ac34`)이고 지금은 `draft_phase3_design_v8.md`(다른 agent 작성 중, 17:57:58, 183,440 바이트)가 있다. 이 문서는 v8을 고치지 않고, 닿는 문장(D-27·§8.1 'B26-2~B26-4의 자리'·§9.1 재측정 (1)·card `phase` 값 정리)은 '기본값 F2 뒤'로 같아 v0.9의 (가)와 충돌하지 않는다(v0.9는 '앞당기려면 D0b 전' 경로를 쓰지 않는 더 좁은 선택). 승인 질문 머리의 '확정본과 다시 대조' 조건이 그대로 덮는다.
정본 인용 규칙은 계획 N9.4 -- 이 문서는 계획서·`00-common`·`05`·`10`·`20`·Phase 3 초안(`30-module-split` **v7**(작성 중 판 -- (v0.8) 읽은 판 mtime 2026-10-01 16:45:58, 178,205 바이트, sha256 `87c63513…a5dad85e`. v0.7의 'v7 = v6 바이트 동일'은 v0.7 작성 시점(16:32)에만 맞았다 -- 4차 검토 S4. 모듈 배정 절(A-3·D-3·D-19·D-22·D-25)은 v6과 같고 새로 닿는 것은 D-26·**D-27**, §3.1 항목 7)·게이트 card 초안(면제 묶기·범위 정책·B33)의 정의를 재서술하지 않고 절 번호·id로 인용한다.
읽은 계획 절(N9.1 `40-defect-fixes` 행): N5.2 전체, N3.6, N3.10, N3.14, N3.16, N4.1 IC11, N4.2 V3·V4·V8, N6.1·N6.2 Phase 4, N6.3, N0.4(106·124행), `00-common` §6·§7·§10·§11·§14·§18, DEC-40·47·51·60·61·62·69·70·71·76, I-C11, U-04·05·09·25·26·27·30. N9.2 필수 절 대응은 부록 B.

**표기 규칙(이 문서 전체)**
* **[재측정]** = v0.2 때 `cd64170`에서 다시 잰 사실(엔진·하네스 변경 0이라 HEAD에서도 같다).
* **[재측정 v0.3]** = `7535799` 사본(`C:/g48/repo`)에서 잰 사실(부록 A).
* **[재측정 v0.4]** = `7535799` 사본(`C:/g61/repo`·`C:/g61/sim`)에서 잰 사실(부록 A v0.4 표).
* **[재측정 v0.5]** = HEAD `2d58fd8`에서 이번에 잰 사실(부록 A v0.5 표 -- `git` 읽기·`git show` 뿐, 스크래치 `C:/g74`).
* **[ud17]** = `prep_ud17_f26_f27.md`(HEAD `7535799` 사본 `C:/g67`, 스크립트·원자료 `_drafts/ud17_scripts/`)의 실측 인용. 엔진 소스는 SR·하네스 동일, SD는 `kcl_series_union`만 다르다.
* **[prep]** = 입력 준비 문서의 실측 인용. card 작성 전 실측(card 처리 속도 규칙)에서 다시 잰다.
* **[미확인]** = 실측 근거가 없는 문장. 착수 전 확인 대상이다.

**입력 문서**(`C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/`): `prep_phase4_scope.md`, `prep_b26_supply_nets.md`, `draft_b26_1.spec.md`, `draft_b26_plan_patch.md`, `b26_decision_table.md`, `prep_u27_u30.md`, `prep_deferred_rows.md`, `backlog_additions.md`, `user_decisions.md`, **`draft_phase3_design_v3.md`**(v0.2의 v2를 교체), `prep_b34_b35_grammar.md`, `review_b26_1.md`, (v0.3) `review_phase4_design.md`, (v0.4) `review2_phase4_v03.md`, `draft_phase3_design_v4.md`(v3 교체), `draft_v3_exempt_binding.spec.md`, `draft_v3_scope_policy.spec.md`, `draft_v3_decision_question.md`, `review_v3_cards.md`(두 V3 card는 이 검토로 **개정 중** -- 이 문서는 id·결정 형태만 인용하고 계약 문언은 인용하지 않는다), `v3_scope_systemic.md`, `draft_b34.spec.md`(10-01 최신, v2 2차 수정)·`b34_revision_log.md`, `draft_b26_1.spec.md`, `prep_b37_ports.md`, `draft_b33.spec.md`, `user_decisions.md`(10-01 A2·A3), `backlog_additions.md`(B39~B43).
**v0.3의 '아직 없는 입력' 문장 정정**: `v3_scope_systemic.md`는 v0.3 작성 전부터 있었다(mtime 22:17 < v0.3 22:36, 검토2 S4). §8.4에 card별 수치를 넣었다. 이 파일은 `cd64170` 기준이고 엔진 소스는 HEAD와 같다.
**v0.4 작성 시점에 아직 없는 입력**(`ls _drafts` 확인): `v3_cards_revision_log.md`, `draft_b37a.spec.md`, `review_b33.md`. 셋 모두 이 문서의 결정을 바꾸지 않는다 -- V3 두 card와 B33은 id·선후·승인 형태로만 인용하고, B37a는 `prep_b37_ports.md` §4.2 계약 목록을 card 작성 입력으로 지정한다.
**v0.5 입력**(10-01 13:03까지의 최신본): `prep_ud17_f26_f27.md`(+`ud17_scripts/out/`), `draft_b37a.spec.md` v2 + `b37a_revision_log.md` + `draft_b37a_approval_question.md`, `draft_b34.spec.md`(최종 -- 4 def, 55/55) + `b34_revision_log.md` §5·§6, `draft_b26_1.spec.md`(B34 인계 반영본) + `v3_cards_revision_log.md` §6(넓힌 T6 294), `draft_v3_scope_policy.spec.md`·`draft_v3_exempt_binding.spec.md`(v3 커밋용 확정) + 승인 기록 초안 `approval_20260930-v3-*.md`, `draft_b33.spec.md`(개정) + `b33_revision_log.md`, `backlog_additions.md`(B39~B47), `draft_phase3_design_v5.md` + `review3_phase3_v5.md`, `redteam_numbering.md`, `folded_cascode_nets.md`, `user_decisions.md`(A1-b 정정). v6 Phase 3 초안은 없다(`ls`).
**v0.6 입력**(10-01 14:40까지의 최신본): `ud17_coanalysis_pack.md`([pack] -- 넷 기준 표·충돌 경로·빠른 점검 F0~F3·C1, HEAD `a796468` 사본), `draft_phase3_design_v6.md`(D-22~D-25, §6.2·§6.4·§8.1·§9.1), `draft_b34.final.spec.md`·`b34_commit_plan.md`·`b34_revision_log.md` §7, `draft_b26_1.spec.md`(v4 작성 중 -- 머리·'의도'·'결정 필요 항목'은 v4, 'V3 계획' 절은 아직 옛 문안) + `review2_b26_1.md`, `user_decisions.md`(B33·Q1). `b26_1_revision_log_v4.md`는 **없다**(`ls`).
**v0.9 입력**: `review5_phase4_v08.md`(5차 독립 검토), `pending_questions.md`(Q-B34-PHASE, 17:37), `b26_backfill_question.md`(U-BF, 17:36), `b26pre_revision_log.md`(v1 → v2, 17:43 -- B26pre U1 = 원칙 기본안, U2 = 생존 3문장 처리), `draft_b26pre.spec.md`(v2), `draft_phase3_design_v8.md`(읽기만 -- 위 '(v0.9) Phase 3 판').
**v0.9.2 입력**: `user_decisions.md` 끝 절(2026-10-01 U-BF·Q-P2DOD-E2·B26 묶음 4문항 U3·U4·U5·Q-B34-PHASE), 승인 기록 초안 `approval_20261001-b26-phase3-cards.md`·`approval_20261001-p2dod-e2-wording.md`·`approval_20261001-b26-backfill-interdig-fix.md`·`approval_20260930-b26-b40-reason-key.md`·`approval_20261001-b26-p9-signature-update.md`, `b26_ask_payload.md`, `b26_survivor_final_question.md`, `pending_questions.md`('[Q-B34-PHASE 정정]'), `draft_b26_1.spec.md`(U3 면제 기록 시점), `draft_phase3_design_v8.md`(v8.2 -- E5·D-28, 읽기만), `backlog_commit_plan.md`(B48~B50 번호 충돌 -- 오케스트레이터 지시로 B51~B53).
**v0.8 입력**: `review4_phase4_v07.md`(4차 독립 검토), `draft_phase3_design_v7.md`(위 판 -- D-26·D-27, §8.1·§9.1), `b26_1_survivor_question.md`(16:41 생성 -- v0.7의 '없다'는 그 시점 사실), `draft_b26_1.spec.md`(v4, 16:41), `user_decisions.md`(A3 선례).
**v0.7 입력**: `review3_phase4_v06.md`(3차 독립 검토), `user_decisions.md`(2026-10-01 "card 순서"), `draft_b26pre.spec.md`(B26pre card -- '결정 필요 항목' U1~U3), `draft_phase3_design_v7.md`(= v6). `b26_1_survivor_question.md`는 **없다**(`ls`) -- B26pre card가 그 질문을 대체했다.

---

## 1. 목표와 범위

### 1.1 목표

Phase 4는 **동작을 바꾸는 첫 Phase**다. 계획 N5.2가 Phase 4에 배정한 결함(DF)을 red-green으로 고치고, 이후 Phase가 쓰는 공통 기반(N3.14 실패 규약, 옛 키 게이트, 성능·무동작 계측 도구)을 먼저 깐다. 끝나면 (1) 엔진이 실패를 삼키지 않고 N3.14 클래스와 exit code로 드러내며 (2) 레일·PDK 상수가 선언 한 곳에서만 오고(이름 집합·사본 0) (3) 조용한 폴백이 `fallback_events`로 계측되어 정본 실행에서 0이고 (4) 사이징 대상 회로의 전후 비교표가 판정 기록으로 남는다.

### 1.2 계획 원문

N6.1 Phase 4 행(계획 1001행):
> | 4 | TS4 → DF-35 → DF-36 → `00-common` CC-4의 앞부분(실패 클래스·`FailureRecord`·`exit_code_for`와 DF-37의 하네스 `run()` 몫) → CC-7·CC-8(측정·무동작 도구가 이후 card에 쓰이도록 Phase 4 앞쪽에 둔다) → 나머지. Phase 4 전체 범위: TS4, DF-01~15·18~20·22~24·26·27·35~37, **DF-34의 Phase 4 몫**(회로별 `_spec_*()`이 따로 복사한 PDK 상수 제거 -- 함수 자체를 데이터 항목으로 바꾸고 삭제하는 것은 7b다), MG1 레일 이름 변경(DEC-69), U-27 LUT 재생성, PDK 상수 한 곳 선언(U-30), Phase 2에서 배선을 고른 함수 배선, `fallback_events` 계측(V8), 기존 4개 회로 실행 가능성(I-C11), IC11 활성 | red-green | U-04, U-05, U-09, U-26, U-27 | `40-defect-fixes` |

N6.2 Phase 4 완료 조건(1019행):
> DF마다 red-green, V8 도입(정본 실행 `fallback_events` 0), 사이징 대상 회로 실행과 전후 비교표, IC11 2레일 케이스 PASS, MG1 옛 키(계획 `supplies`, spec 스칼라 `vdd` 선언, metric 인자 `supply_nets`) 거부 test PASS, DF-27 VS 축 밖 픽스처 거부, U-27 재생성 LUT의 옛 격자점 값 대조 기록(다르면 원인 보고, 기준선 변경은 DEC-40 승인), U-30 PDK 상수 교체 전후 self-test·사이징 대상 회로 비교표(`min_finger_w` = difftap.2 출처 기록, 바뀌는 기준선·기대값은 DEC-40 승인)

N9.1 `40-defect-fixes` 행(1158행, 반드시 담을 것 요지): DF별 red 형태와 수정 범위, N3.14 실패 클래스 도입, tol_V 함수 선도입, U-04·U-05, **`fallback_events` 스키마와 계측 지점 전수**(→ §10.1, 부록 C), exit code, **I-C11 해소 설계**(→ §11), `supply_nets`·`supplies_v` 레일 판정(DF-19·26)·vsb(DF-24)·IC11, MG1, DF-27 축 커버리지 게이트, U-27 절차·대조, U-30 선언과 전후 비교, `00-common` CC-4·CC-5·CC-7·CC-8, DF-35·36.

N6.3(공통): "성능: Phase 4부터 매 Phase 보고", "동작 변경 Phase(4 이후)는 DEC-47 대상 구분대로 측정하고 필요 없는 회로의 무동작을 증명한다."

### 1.3 범위 안

| 항목 | 계획 근거 | card 묶음(§5) |
|---|---|---|
| TS4 자기참조 기대값 제거 | N3.11 561행 "4(첫 작업)" | 선두 |
| N3.14 실패 클래스·`FailureRecord`·`exit_code_for`, 하네스 exit code(DF-18 exit 몫, DF-37 하네스 몫) | `00-common` §7.1, CC-4 앞부분 | 선두 |
| θ 탐색부 추출·계측 인터페이스·성능 도구(CC-7), `activations_out`·무동작 도구(CC-8) | `00-common` §10·§11 | 선두 |
| DF-01~15, 18~20, 22~24, 26, 27, 37 | N5.2 담당 Phase 열 | 실패 규약 / 노드전압 / 캐시 / 레일 / LUT / 개별 |
| DF-34 Phase 4 몫(PDK 상수 사본 제거) + U-30 | N5.2, U-30(닫힘) | LUT·PDK |
| MG1(레일 **전압**: `supplies_v`, `vdd` 유도 함수, 옛 키 거부) + CC-5 | N3.16 802행, DEC-69, `00-common` §6 | 레일 |
| DF-19·DF-26 넷 몫(B26-1~B26-4) | N5.2, 계획 정정안 `draft_b26_plan_patch.md`, **사용자 승인 A2**(2026-10-01, 기록 id `20260930-b26-before-phase3`) | 레일(B26-1은 Phase 3 M card 전 -- A2로 확정. **(v0.9.2) card 머리 `phase: 3`**(Q-B34-PHASE 결정, 기록 `20261001-b26-phase3-cards`) -- 이 문서의 간선·판정은 값과 무관, §9-19) |
| U-27 LUT 재생성·옛 격자점 대조(도구의 ngspice `Error:` 미검사 포함, #26 G7) | U-27(확정) | LUT·PDK |
| V8 `fallback_events`(스키마·지점 전수는 §10.1·부록 C) | N4.2 844행 V8 | 실패 규약(DF-14와 한 card) |
| I-C11(U-09) -- 실패 명시화(#43)와 해소(#44, UD-6) | 979·1084행 | 회로 |
| IC11 rail2 활성(대상 회로 = HEAD에서 끝까지 도는 2레일 회로, §5.4. test는 MG1 #21과 한 card -- 계획 N3.16 MG1 행) | N4.1 829행, N3.16 802행 | 레일 |
| 보류 행 배선(Phase 2에서 '배선'을 고른 함수) | N6.1 | 배선·삭제 |
| `tests/probe_physical_consistency.py`의 레일 이름 집합 재구현 교체 | 사용자 결정 기록 2026-09-30 Phase 2 DoD D2("스캐너 범위 밖 rail-set 재구현 1건") | 레일(#17 test 커밋) |
| 백로그 B21(b)(c)·B24·B26·B34~B37 | `.ai/context.md` 14939행 외 [prep]. **B34는 phase 3 card**((v0.9.2) Q-B34-PHASE -- `20260930-b34-grammar-explicit`, A2 기록 + `20261001-b26-phase3-cards`, Phase 2 DoD 뒤·Phase 3 M card 전, 범위 4 def -- 최신 card)이고 이 Phase에는 인계 사이트만 온다(§5.1 #1, §5.4 #17·#49, 부록 C.3) | 노드전압 / LUT / 레일 |
| (v0.5) UD-17 결과 card -- folded·current_reuse의 노드전압 충돌·축 밖 조회의 원인 해소(#53·#54, (v0.6) bulk는 #55) | DF-02·DF-27이 드러내는 정본 실행 실패의 원인(F26·F27, [ud17]). 계획 N6.2 '사이징 대상 회로 실행과 전후 비교표'·E8 파일럿 성능 보고가 이것 없이 성공 단위로 판정되지 않는다 | 회로(§5.10) |

### 1.4 범위 밖(명시)

* **이미 끝남**: DF-35(`34bc75e`), DF-36(`148bd6d`) -- 인용만 한다 [prep: `prep_phase4_scope.md` §0-2].
* **삭제로 해소**: DF-29 대상 5함수가 HEAD에 없다(P5b `d7bce7a`) [prep]. 계획 DF-29 행 닫힘은 계획 정정(§9).
* **다른 Phase**: DF-16·28·30(7a), DF-21(2), DF-25(6b), DF-31·33·DF-34의 함수 삭제 몫(7b), DF-32(6b·6c), IC11 rail3·reject(6a, `test_ic11.py` 표식 [재측정]), GB0 로드 게이트 일반형(6a), tol_V·tol_I를 쓰는 봉인 구현(6b), CGS·CGB 열의 **소비**(DF-28, 7a), U-36 수동소자 단위 면적 **값**(7b 전), SID_1F 잡음 metric 소비(7b 이후), `tol_I`(6b, P-3). (v0.9, 5차 검토 정보) #14가 θ*를 싣는 실행 기록 JSON은 계획 368행 S3 실행 기록(θ*·start별 결과 -- Phase 5 `runs.jsonl`)과 같은 개념이다 -- Phase 5(`50-failure-cache`)가 그 파일을 대체할지 읽을지를 정한다(DEC-68 저장 위치 하나. #14는 키 `theta_star` 하나만 두어 Phase 5가 흡수할 수 있게 한다).
* **B21 (a)와 P3c 재착수**: `tol_I`가 6b이므로 P3c 재착수 위치 = 6b의 `tol_I` card 뒤. 조건 (b) `supplies_v`는 #21, (c) DF-02는 #23에서 Phase 4 안에 충족된다(§9-8).
* **U-25 실행 `SPECS` 이관**(agnd 두 회로 `sf_pushpull_output_opamp`·`pushpull_follower_buffer`, 그리고 `two_stage_ota_sf`): **범위 밖**. 조건 "DEC-60 구현 뒤"는 #1·#17·#21이 병합되면 Phase 4 안에서 성립한다. 그래도 넣지 않는 이유: (1) 이관은 사이징 대상 회로를 늘리는 스펙 데이터 추가이지 결함 수정이 아니고 N6.1 Phase 4 범위 문구에 없다 (2) agnd 3레일 회로의 IC11은 6a(rail3)다 (3) 넣으면 E1·E2 대상이 바뀌어 Phase 4 전후 비교의 기준 집합이 흔들린다. 이관 시점은 6a(IC11 rail3와 함께) 또는 7b(`sizing_spec.json` 이관)이고, 그 Phase design이 정한다.
* **게이트 선행 card(이 Phase 밖, 인용만)**: (i) V3 면제 묶기 `20260930-v3-exempt-binding`(phase 0.5, 강화, 게이트 변경 승인 필요, redteam 34) (ii) V3 범위 정책 `20260930-v3-changed-stmt-scope`(phase 0.5, 약화 -- **사용자 결정 A1-b로 선택지 2 승인 + A1-b 정정으로 T6 넓힘**, 2026-10-01, redteam 35) (iii) **B33** V7 그래프 간선 `20260930-v7-registry-edges`(phase 0.5, 게이트 변경, 사용자 결정 Q1 포함, 권고 순서 B33 → G1, redteam 33 -- 독립 검토 `review_b33.md` blocking 3건 **반영 완료**(`b33_revision_log.md`), Q1은 v0.5 때 아직 묻지 않음 -- (v0.6) 승인 + Q1 (a)로 결정됨). 셋 다 판정 기준을 바꾸므로 이 Phase card의 V3·V7 판정 조건이 달라진다(§3.2, §8.4, 부록 C 머리). 두 V3 card는 v3(커밋용 확정)이고 승인 기록 초안이 있다(`approval_20260930-v3-exempt-binding.md`·`approval_20260930-v3-changed-stmt-scope.md`).
* **인프라 백로그**(엔진을 막을 때만, 메모리 규칙): B29·B30·B31·B32, B41~B43, (v0.5) B45(G1 계약 4 문장 -- G1 card 개정 몫), B46(V3 두 규칙 공통의 기존 한계: 연산자 집합·모듈 수준 상수), B47(추적 파일 `library/folded_cascode.topology.md`가 topology.json과 어긋남 -- 재생성 커밋은 사용자 확인 뒤. **UD-17a 공동분석은 이 추적 md가 아니라 topology.json에서 새로 뽑은 넷 표를 쓴다**: `folded_cascode_nets.md`(json 파생)로 `tail`·`X`·`Y` 연결이 [ud17] §2.1과 같음을 확인 -- 어긋난 것은 M1·M2 gate 넷뿐이라 (a)의 KCL 근거에 영향 없음 [재측정 v0.5: `folded_cascode_nets.md` 소자표 대조]). B40은 B26-1 card가 해소한다(그 card 범위, `b34_revision_log.md` §6). B44(B34 뒤 낡은 test docstring)는 다음에 그 파일을 고치는 card의 test 커밋에서 참조로 고친다(test-author 경로, 판정 불변 -- 이 Phase card가 `test_selftest_stick_diagram.py`를 고치면 그 card). B33은 v0.3까지 여기 있었으나 게이트 card가 됐다(위). v0.2가 여기 넣었던 `sky130_lut_sweep._parse_output`의 `Error:` 미검사는 **범위 안으로 옮겼다**(#26 G7 -- 이 Phase가 약 22시간 걸려 만드는 엔진 입력 LUT의 조용한 실패이므로 '엔진을 막는' 조건에 해당한다).
* **(v0.5) 새 백로그 제안**(번호는 `backlog_additions.md` 다음 번호 -- 오케스트레이터가 확정. **(v0.9.2) 확정: B51·B52·B53** -- v0.5~v0.9.1의 B48·B49·B50은 오케스트레이터 백로그가 test_lint 빈 컨테이너 오탐·design 20 §8 P6·P8 판정 유형·층위1 폴백 중복에 이미 썼다): **B51** VS 축 0.2 V 간격의 보간 오차 대 tol_V 판단(v0.4 P-5의 'B44' 제안 -- 번호 겹침으로 변경), **B52** sf_pushpull `resolve_stack_layout` 경로 3 결과가 M1~M4를 어느 그룹에도 넣지 않음(base·head 모두, `b37a_revision_log.md` §5 -- 기존 동작), **B53** 측정 브리핑 규칙: 엔진 사본은 `skills/analog-grammar`를 함께 복사한다([ud17] §6.3 -- 빠지면 current_reuse θ* 평가가 `vertical_stack_id` 순환 `ValueError`로 바뀐다. 근본 수정은 #45 B34이고 이것은 측정 절차 메모).
* **analog-grammar**: B34는 #45(phase 3 card -- (v0.9.2) Q-B34-PHASE, 인용), B36은 #46, B37은 **B37a #47**(SD·SR, Phase 4 레일 묶음)과 **B37b #52**(AG `HINT_*` 제거, 조건부 -- B36 뒤). **B35의 처리 방식은 UD-15에 묶은 사용자 결정이다**(§7.1). B29~B32·`_TEMPLATE`의 `supply_nets` 필드 부재(`review_b26_1.md` M2)는 인프라·문서 백로그. B34가 넘긴 사이트 4·12(백로그 **B39**)는 이 Phase 범위 밖이다(§5.1 #1 아래 인계 표).
* **`HINT_*` 이름 정규식의 바이어스 넷 추정**(v0.3의 새 백로그 B38 제안): **닫는다**. `HINT_BIAS`는 1c의 기본값이 이미 BIAS라 결과에 영향이 없고(`prep_b37_ports.md` §1.1), 라이브러리 경로의 `HINT_*` 전부를 CLI 경계로 옮기는 일은 B37b(#52)가 한다. B38 번호는 쓰지 않는다.

### 1.5 계획과 HEAD가 어긋나는 곳(이 design이 전제하는 정정)

1. N6.1 앞머리 순서의 DF-35·DF-36은 완료 -- 실제 순서는 **TS4 → CC-4 앞부분 → CC-7·CC-8 → 나머지** [prep].
2. DF 위치 열 줄 번호가 낡았다(DF-26 "3882~3883·3147" → 3714·3715·2983 [재측정]). 이 design은 **함수 이름**으로 인용하고, Phase 3 뒤에는 D0b 이관표의 MOD 파일을 따른다.
3. U-27 "SID_1F 열 추가"는 열이 이미 있다 [재측정] → "새 VS 축으로 함께 재스윕"으로 읽는다. 계획 158행 문장도 낡았다 [prep].
4. DF-19 비고의 "29개"는 옛 스캔이다. 넷 판정 운영 함수는 AST 전수 SR 14 · SD 14(상수 3 별도)이고 `run_harness` 4는 전압 선언(MG1)이다 [prep].
5. 레일 넷과 레일 전압을 한 변경 단위(MG1)로 묶은 문구 → 넷(B26) / 전압(MG1) 분리. 계획 정정안 `draft_b26_plan_patch.md`.
6. (v0.3) DF-24 위치 열 "`derive_vsb_from_nodes`(sizing_recipe.py 3957행 참고)"는 3789행 [재측정]. 그리고 vsb의 조용한 `0.0` 기본값이 SR에 **31곳**(`.get("vsb", 0.0)`)과 `setdefault` 2곳(SR 7579 `ref_vds`, SD 4605 `0.0`) 있다 [재측정 v0.3, 부록 C.2] -- DF-01·DF-24 행이 이 사이트를 적지 않는다. (v0.4) 조건식 기본값 1곳 추가: SR 7411 `_vsb = _e.get("vsb", ref_vds if ref_dev is not None else 0.0)`(`_hr_resolve_vertical_group`, 검토2 M1 재측정 일치) -- 7579 `setdefault("vsb", ref_vds)`와 같은 묶음이고 `0.0` 갈래가 조용한 기본값이다.
7. (v0.4) **folded_cascode의 HEAD 실행이 LUT VS 축 밖을 조회한다**(F26): 계획 DF-27 행은 "VS 축 밖 픽스처 거부"만 적고, 정본 실행 회로가 지금 축 밖에 있다는 사실(θ* vsb M1·M2 1.6, M5 1.8, M7 −0.65; 축 [0, 0.8])을 적지 않는다. #25가 병합되면 folded 정본 실행이 실패로 바뀐다(§5.6 #25).
8. (v0.5) **정본 실행 두 회로의 지금 사이징 결과는 노드전압이 일관되지 않은 동작점 위의 값이다**([ud17] §2). folded: 선언 M1·M2(pmos, source = `tail`)와 꼬리 NMOS sink M11이 `tail`에서 KCL로 함께 성립하지 않고(전류를 넣는 소자가 없다), feed `r_split_M1_M2`와 `kcl_fold_M6`(I6 = I1 + I3)이 M1 전류 방향을 반대로 읽는다. 연결 패턴은 NMOS 입력 폴디드 캐스코드의 전형이다 -- 판정은 사용자 몫(UD-17a). current_reuse: Vom1·Vop1을 텔레스코픽 컬럼은 0.9 V, 출력단 VGS 구속(`M10.vds_match_vgs_of = M16`)은 0.6773 V로 정하고 엔진이 둘을 맞추지 않아, 경로상 꼬리 M5 VDS가 27 mV(포화 밖)다(UD-17d). 계획 N0.4는 current_reuse를 **파일럿**(123행 '기존 4개 회로' [재측정 v0.5])으로 두므로, DF-02(#23)가 이 충돌을 거부로 바꾸면 파일럿 정본 실행·E8 성능 보고·IC11 대상이 함께 영향받는다. 계획 DF-02·DF-27 행은 이 사실을 적지 않는다(§9-16).
   **(v0.6 정밀화, [pack] §2.2·§4.2)**: folded의 원인 (a)(극성)를 고쳐도 X·Y 충돌은 1.2 V로 남는다 -- 1.6 V 중 0.4 V만 극성이고 1.2 V는 tail 컬럼(vdd → M3 → X → M1 → tail → M11 → gnd) KVL 공백이다(입력 CM이 선언되지 않아 singleton 우회가 M1에 vds 0.2만 준다). 그래서 folded의 동작점은 **UD-17a와 UD-17c가 함께** 정해야 닫힌다. current_reuse는 UD-17d (i)이면 Vom1 충돌이 사라지는 대신 꼬리 M5 vds 0.0273 V(포화 밖 추정)와 진짜 축 밖 M2a·M2b(0.9227 V)가 남는다(F33).

---

## 2. HEAD 사실 (재측정한 것만)

v0.2 명령: `C:/g36/remeasure.py`(cd64170). v0.3 명령: `C:/g48/m.py`·`reach.py`·`runall.sh`(7535799 사본). 표의 값은 그 출력이다.

| # | 사실 | 값 | 원 출처 | 비고 |
|---|---|---|---|---|
| F1 | 기준 커밋·design 문서 | HEAD `7535799`. design 4개(`00`·`05`·`10`·`20`), `40` 없음 | 검토 §4 | cd64170 이후 엔진·하네스 변경 0 [재측정 v0.3] |
| F2 | 레일 이름 집합 정의 위치 | SR `_DEFAULT_RAIL_HI/LO` 3714·3715, SD `_RAIL_NETS` 2983, SR `_rail_nets = frozenset(...)` 8003, MNA `fixed = {"gnd": 0.0}` SR 4086·4991 | `prep_b26_supply_nets.md` §1.1·§1.2 | 일치(검토 재측정도 일치) |
| F3 | 엔진이 `supply_nets`·`supplies_v`를 읽는 곳 | `"supply_nets"`: SR 4361 하나(metric 선언 키), SD 0. `"supplies_v"`: SR 0 | 같은 문서 | **엔진은 topology 최상위 `supply_nets`를 읽지 않는다** |
| F4 | 스칼라 `spec["vdd"]`·`.get("vdd")` 읽기(MG1 대상) | SR **20줄**: 1729, 3254, 4626, 4653, 7068, 7222, 7228, 7290, 7295, 7296, 7445, 7449, 7450, 8233, 8242, 8277, 8652, 10157, 10159, 10160 | `prep_phase4_scope.md` §3.4("21줄") | 8656은 오류 메시지 문자열. 7068은 `_hr_verify_group_kvl_sum`의 "직렬 VDS 합 = vdd" -- **레일 폭(hi − lo)으로 쓰는 읽기**다(§10.4) |
| F5 | 광범위 except 핸들러 수(DF-37) | SR `ValueError` 포함 26 · `Exception` 6 · `InfeasibleSizingError` 18, SD 4·0·0, 하네스 1·2·0 | `prep_phase4_scope.md` §3.6 | 일치 |
| F6 | 하네스 PDK·전압 사본 | `min_finger_w` 121 **`0.1e-6`**, 186·243·301 `1e-6` / `W_bounds` 117·172·241·297 / `L_min` 115·170·239·295 / `"vdd": 1.8` 105·142·234·288 / `min_vds_by_role` 118·173·242·300 | `prep_u27_u30.md` §3.1 | 일치 |
| F7 | 엔진 쪽 두 번째 정본(폴백 기본값) | `W_bounds` `(1e-6, 200e-6)` SR 11곳(1626, 1988, 2697, 2748, 3623, 5763, 6055, 6731, 7266, 7462, 8716), `spec.get("min_finger_w", …)` SR 9273, SD 기본 인자 5954·6043·6204 | `prep_u27_u30.md` §3.2 | 일치(부록 C.2의 `.get` 형태는 10곳, 1988은 다른 형태) |
| F8 | DF 대상 함수 정의 줄 | (v0.8, S8 -- v0.2 표를 옮김, `cd64170` 값, SD 3041행 이후는 P9 뒤 −11) SR `solve_id_for_target_gm` 1433, `_invert_gm_id_for_current` 1471, `lut_vdsat_headroom` 1591, `stack_kvl_vgs_limit` 1668, `resolve_feed_vds` 1971, `true_current_mirror_groups` 2191, `estimate_area_budget` 2765, `diode_vds_cached` 3206, `diode_vds_window` 3402, `solve_stacked_diode_pair` 3491, `propagate_node_voltages` 3727, `derive_vsb_from_nodes` 3789, `reconcile_vsb_from_nodes` 3808, `node_pole_estimate` 3917, `build_ac_network` 4067, `_metric_kcl_residual` 4267, `_metric_supply_current` 4339, `_mirror_ratio_error_pairs` 4388, `_metric_input_referred_offset` 4561, `_resolve_nulling_resistor_ohm` 4908, `_full_circuit_response` 4970, `validate_no_legacy_vs_key` 5217, `InfeasibleSizingError` 6429, `_hr_resolve_vertical_group` 7089, `spec_fingerprint` 7596, `resolve_constraint_references` 7821, `_build_theta_evaluator` 7930, `optimize_full_circuit_budget` 9075, `repair_infeasible_baseline` 10410, `revalidate_finger_override` 11299, `GmIdLUT` 52, `SemiEmpiricalGmIdLUT` 259, `_query`(메서드) 378, SD `load_topology` 8550(HEAD 8539). 함수 이름이 정본이고 줄은 card 작성 전 실측이 다시 잰다. 추가: SD `_import_analog_grammar` 1045, `propose_device_roles_gap_fill` 3845 | `prep_phase4_scope.md` §3.5 | 일치 |
| F9 | 캐시·폴백 결함 지점 | `_QUERY_CACHE_MAX` 257·390(DF-07), `idu_up = 1.0` 3539(DF-11). `setdefault("vsb", …)` 문자열은 3813·3857·7407·7579에 있으나 **3813·3857은 docstring, 7407은 주석이고 코드는 7579 한 줄**(`other_entry.setdefault("vsb", ref_vds)`, `_hr_resolve_vertical_group`)이다 | 검토 F9 | **정정(v0.3)**: DF-01 원인 코드 = 7579 하나. AST로 세면 `setdefault("vsb", …)` 코드는 SR 7579 + **SD 4605**(`apply_device_roles_gap_fill`, `0.0`) 둘 [재측정 v0.3] |
| F10 | 표본 LUT | 키 = L·VGS·VDS·VS·`corner`·`temp_c`·{ID,GM,GDS,CGG,CGD,SID_1F}_{n,p}. CGS·CGB 없음. L 12점, VS = [0, 0.2, 0.4, 0.6, 0.8]. sha256 `753d802a…f177f` | `prep_u27_u30.md` §2.1 | 일치 |
| F11 | 착수 조건 승인 기록 | `.ai/approvals/` **42개**(HEAD, `b7d2570`이 1개 추가) 중 U-04·U-05·U-09·U-26·U-27·U-30·`40-defect`·B26 해당 **0** | 검토 F11 | 수는 HEAD 이동분. **(v0.5)** HEAD `2d58fd8`: `ls .ai/approvals \| wc -l` = 44(`_TEMPLATE.md` 포함), **A2 `20260930-b26-before-phase3.md` 있음**, `20260930-phase2-e4-phase.md` 추가. U-04·05·09·26·27·30·면제 묶기·범위 정책 기록은 여전히 0 [재측정 v0.5] |
| F12 | 레지스트리 보류 표기 | `보류(Phase 3)` 9, `보류(Phase 4)` 14, `보류(Phase 6a)` 2 -- **표 행으로 세도 같다** | 검토 F12 | v0.2의 [미확인] 닫힘 |
| F13 | IC11 뼈대 | `tests/contracts/test_ic11.py`: `rail2` phase 4, `rail3`·`reject` phase 6a, 본문은 `pytest.fail()` 한 줄 [재측정 v0.3] | `prep_phase4_scope.md` §1.5 | 일치 |
| F14 | '자기참조' 표기 test | 판정 자기참조는 `test_selftest_sizing_recipe.py:1786` 하나 | `prep_deferred_rows.md` §1-2 | 일치 |
| **F15** | **하네스 정본 실행 4회로(HEAD 사본, `python run_harness.py <key>`)** | two_stage_ota: **`[FAIL] ValueError: 'stage1_out' 그룹의 VDS 합(2.37965V)이 vdd(1.8V)와 불일치(diff=+0.579654V)`** -- M4=0.9172(`vds_match_vgs_of` M6), M2=0.9(compensation), refs M5=0.5625, 36 s. nmcnr_amplifier: **`[FAIL] ValueError: 모든 theta 격자점이 infeasible`** -- 마지막 사유 `'stage2_diode_ref' 그룹(예산 1.5V, 미해결 ['M203'])… 0.525V를 배정할 곳이 없다… 구간 [M203∈[0.6375,0.975]]`, 36 s. folded_cascode: **끝까지 실행**(θ* `{'Ibg': 5e-07, …}`, `instance.json` 저장, `audit_ok=False`·`floorplan_ok=False` 그대로 저장), 단독 43 s. current_reuse_telescopic_ota: **끝까지 실행**(SLSQP 3 start, `instance.json` 저장, `audit_ok=False`), 4회로 병렬 중 411 s. **네 경우 모두 프로세스 exit code 0**(DF-18) | [재측정 v0.3] `C:/g48/run_*.log` | v0.2 E2의 [미확인] 닫힘. two_stage 실패 문구는 I-C11 known-limitation test(`test_selftest_sizing_recipe.py:2437` 'stage1_out'·'KVL')와 같다 |
| **F16** | source가 선언 레일이 아닌 NMOS 수 | folded_cascode 2(M7·M8), current_reuse 12 [재측정 v0.3] | -- | **(v0.4 정정, 검토2 M6)** 이 수는 DF-24 검출력 지표가 아니다. rail_lo 0.0 고정이 남은 엔진에서는 어느 소자도 vsb 오차가 나지 않고(F25 S1), 레일이 실제 전위로 고정된 엔진에서는 레일 source NMOS도 틀린다(F25 S3: M9·M10·M11·MN 모두 −0.9). 검출력은 F25로 잰다 |
| **F17** | 조용한 폴백 후보 전수(엔진 `A/*.py` + 하네스) | 예외를 다시 던지지 않는 except 핸들러 **59**(SR 47·SD 5·하네스 3·도구 4), 운영 도달 52. `.get(<문자열 키>, <리터럴>)` **112**(스칼라·튜플 77 + 빈 컨테이너 35). `setdefault` 49(그중 선언 값 기본값은 vsb 2). SD analog-grammar `None` 폴백 직접 12·전파 9(= `prep_b34_b35_grammar.md` §1.2, 줄 번호 HEAD 동일) | [재측정 v0.3] 부록 C | §10.1의 계측 지점 전수 근거 |
| **F18** | `test_ic5`의 표-함수 대조 | `missing = set(_DOMAIN_TABLE) - found_keys` → **표에 있는 함수가 없으면 FAIL**, 표에 없는 함수는 형식만 검사, `len(_DOMAIN_TABLE) == 21` [재측정 v0.3] | 검토 S5 '미측정' | D-5 표 행을 먼저 지우는 것은 안전, 함수를 먼저 지우면 FAIL(§5.9 #41) |
| **F19** | CC-5 깊은 복사 관용구 `json.loads(json.dumps(x))` | 엔진 모듈 AST 계수 **0**(`json.load(s)` 9곳 모두 파일 읽기) [재측정 v0.3] | 검토 S12 | `00-common` §14 CC-5 행 "AST 계수가 0이면 해당 없음" → 해당 없음 |
| **F20** | `sky130_lut_sweep._parse_output`(196~227행) | ngspice 출력의 `Error:` 줄을 검사하지 않는다. 검사는 파싱된 점 수(`len(id_v) != n`)뿐 [재측정 v0.3] | `prep_u27_u30.md` §2.2 | #26 G7 |
| **F21** | topology `ports` 모양 | library 9/9가 `{넷: {role, direction}}`. role 값 = `differential_input_n/p`·`single_ended_input`·`differential_output_n/p`·`single_ended_output`. `_TEMPLATE`에는 `ports` 키가 **없다**(검토의 'null'이 아님) [재측정 v0.3] | 검토 S8 | #47 |
| **F22** | 레일 이름 문자열 상수(AST `Constant`, 대소문자 그대로) | SR `vdd` 26·`VDD` 3·`gnd` 6·`GND` 2·`vss` 3·`VSS` 2, SD `vdd` 17·`gnd` 17·`vss` 1, 하네스 `vdd` 4 [재측정 v0.3] | -- | #19 lint 기준선(base FAIL 입력) |
| **F23** | `install.py` `SKILLS` | 27~29행에 `analog-grammar` 없음 [재측정 v0.3] | 검토 S4 | #45 병합 선행 사용자 작업 |
| **F24** | `derived_spec` 사용처 | `workspaces/run_harness.py`, `tests/contracts/test_restore_plan_functions.py` [재측정 v0.3] | 검토 M6 | #21·#22·#29·#51이 변형 spec을 이것으로 만든다 |
| **F25** | **원점 이동 시뮬레이션(검토2 B2)** -- HEAD 사본의 스칼라 `vdd` 읽기만 바꾼 사본(`b2_patch.py`), S_A = (1.8, 0), S_B = (+0.9, −0.9). 모드: **S1** = #21을 뜻대로 분류(노드전압 프레임 인자 7295·7296·7449·7450·8652 = 폭 1.8, 절대 전위 읽기 4626·10157·10159 = hi/lo, 4653·10160 = hi + lo, rail_lo 0.0 고정 그대로), **S2** = 노드전압 프레임 인자를 hi(0.9)로 잘못 분류, **S3** = 레일을 선언 전위로 고정(hi 0.9, lo −0.9)했지만 DF-24 vsb 식(nmos = V(source))은 그대로 | folded θ* 한 점(`_build_theta_evaluator(...)["evaluate"]`)과 하네스 전체 실행: **S1 = S_A 비트 동일**(θ*·소자 vds·vsb·gm_id·W·gm·gds·metric 전부). **S2**: M1·M2 vsb 1.6 → 0.7, M5 1.8 → 0.9, M1·M2 gm_id 17.564 → 17.5·W 3.41 → 7.28 µm, gain_db −0.037 dB. **S3**: nmos vsb가 −0.9 V 이동(M9·M10·M11·MN 0 → −0.9, M7 −0.65 → −1.55, M8 0.2 → −0.7), M8 gm_id 25.5 → 25.0·W 56.6 → 88.8 µm, gain_db −0.0117 dB. **어느 모드에서도 예외 없음**(값 차이만). current_reuse 하네스 전체 실행 S1: θ*·소자 양 전부 동일, metric 2개(`rail_referenced_voltage` type: `vg15_level_v` 0.97503 → 0.07503, `vop1_level_v` 0.67728 → −0.22272)가 **정확히 Δ = −0.9 V** 이동 | [재측정 v0.4] `C:/g61/out/full.jsonl`·`cr.jsonl`, 비교 `b2_compare.py` | #50의 xfail 형태 폐기 근거, #21 분류표(§10.4), IC11 판정기 자기 점검·전위형 metric(§10.6) |
| **F26** | **LUT 축 밖 조회(HEAD 값, 지금은 조용히 클램프 -- DF-27)** | 보간 함수 계수 래퍼(`b2_axes.py`, 축 L·VGS·VDS·VS): **folded θ***: 조회 403,847 중 VS 축 [0, 0.8] 밖 **436**(값 −0.65·1.6·1.8 -- θ* 소자 vsb M7 −0.65(nmos), M1·M2 1.6, M5 1.8(pmos)), L·VGS·VDS 축 밖 0. 하네스 전체 실행(격자 탐색 포함) 1,137. 축 밖을 `ValueError`로 거부하면 θ* 평가 = `InfeasibleSizingError`(M7), 전체 실행 = 400 격자점 전부 infeasible → `ValueError`. **current_reuse θ***: 조회 533,469 중 VS 축 밖 **3,537**(0.8125 ~ 1.5 대, 음수 없음 -- θ* vsb M2a·M2b 0.923, M9a·M18a 0.825), 다른 축 0, 거부 모드 θ* 평가 = `InfeasibleSizingError`(M9a). 전체 실행 16,235(−0.084 ~ −0.0375 포함) | [재측정 v0.4] `axes_folded.json`·`axes_cr.json`·`axis.jsonl`·`cr2.jsonl` | #25를 그대로 병합하면 두 회로의 정본 실행이 실패로 바뀐다(§5.6 #25 순서). **(v0.5, [ud17] §0·§1.1·§1.3 -- 수치 4개 재현 일치)** 축 밖 소자의 뿌리: folded 4개(M1·M2·M5·M7) **전부 F27 파생**(일관된 노드전압이면 M5 0.2, M7 0.45로 축 안, M1·M2는 UD-17a가 정함), current_reuse M2a·M2b(0.9227) F27 파생(일관값 0.7), **M9a·M18a(0.825)만 진짜 LUT 범위 문제**(SPICE 클램프 오차 ΔVGS 2.9 mV, IDu 0.7 %). 클램프 오차: folded M1·M2 ΔVGS +231 mV·IDu ×6.2, M5 +160 mV, M7은 요청점 자체가 순바이어스(일관값 대비 IDu 16.5배). current_reuse θ* 한 점 평가 안에서도 VS **2.05 V**(> 레일 폭 1.8)가 조회된다 -- 출처는 [미확인](#22·#25 작성 전 실측) |
| **F27** | **노드전압 경로 충돌(DF-02, 지금 엔진 미소비)** | `propagate_node_voltages(by_name, sized, vdd)`를 θ*에서: **folded** conflicts 4 -- M4@Y 1.6 V, M1@X 1.6 V, M9@Vg9 1.1 V, M8@out 1.0 V(connectivity 사실: PMOS 쌍 M1·M2의 source = `tail`, `tail`은 NMOS M11(source gnd)의 drain). **current_reuse** conflicts 4 -- M5@Vy, M64@Vbias3, M1a@N1a2a, M1b@N1b2b 모두 0.22272 V. unresolved 0(둘 다) | [재측정 v0.4] `nodes_folded.json`·`nodes_cr.json`(`b2_nodes.py`) | #23(conflicts > tol_V → SEAL_VIOLATION)이 병합되면 tol_V가 이 값보다 작은 한 **두 회로의 θ* 평가가 실패**한다. 원인이 topology 선언인지 엔진인지는 회로 해석 -- UD-17(§7.1). **(v0.5, [ud17] §1.2·§2 -- `trace_propagate`가 엔진과 노드값·충돌 수 일치)** 엔진은 이름순(`sorted`)으로 먼저 도달한 경로 값을 노드에 박고 나중 경로는 `conflicts`에만 남긴다. 그 뒤 `reconcile_vsb_from_nodes`가 먼저 박힌 값으로 vsb를 유도하고 사이징이 그 vsb로 LUT를 조회한다(충돌이 있어도 멈추지 않음 = 조용한 선택). 원인 후보: folded = (a) M1·M2 극성·단자 방향 선언(1.6 V 두 건 + 1.1 V 중 0.6 V) (b) fold_group singleton 우회(SR 7507~7563, 주석이 KVL 불일치를 인정)가 Y 컬럼 공백 0.5 V를 배정하지 않음 (c) 같은 우회가 출력 컬럼 공백 1.0 V를 배정하지 않음(`bias3`·출력 CM 미선언). current_reuse = Vom1 이중 구속 1개(0.9 대 0.6773 V, 네 충돌은 모두 그 0.2227 V의 전파). **(v0.6 정정, F32)** 위 (a)의 "1.6 V 두 건"은 극성 몫이 각 0.4 V뿐이다 -- 나머지 1.2 V는 tail 컬럼 KVL 공백(입력 CM 미선언)이라 (b)(c)와 같은 종류(UD-17c)다 |
| **F28** | **(v0.5) current_reuse 매칭쌍 W 불일치** | θ*에서 M2a W = 19.795 µm(LUT vsb **0**에서의 값 -- `gm_id_to_id_density` 역산 비트 일치), 매칭 파트너 M2b W = 16.701 µm(vsb 0.8 클램프에서의 값). 같은 ID·gm/ID·L인데 W가 18 % 다르다. M2a가 `L_cascode` θ의 권위 있는 소스(metric_stage_budget)라 reconcile 뒤 재사이징이 건너뛰어지는 것으로 보인다(clamp·외삽 두 모드에서 M2a W 같음) | [ud17] §6.1 | vsb 재유도 뒤 W 재계산 누락 = DF-01 '버전 혼재'의 실사례 후보(#24). 원인 경로가 SR 7579(F9)인지는 [미확인] -- #24 작성 전 실측 |
| **F29** | **(v0.5) 축 밖 거부 오류의 원인 오귀속** | VS 축 밖을 `ValueError`로 거부한 사본에서 current_reuse θ* = `InfeasibleSizingError` M9a "W_bounds 안에 드는 gm_id 후보가 없다", 전체 실행 = SLSQP 3회 전부 infeasible → `ValueError`(598.7 s, 시도별 사유 M63 'gm_id 후보 없음'·M39/M40·M11a) -- **어느 메시지에도 축 밖이 없다**(탐색 루프·후보 배제가 축 오류를 '후보 없음'으로 흡수) | [ud17] §4.1 | #25 계약(축 밖 오류 고유 클래스 전파 -- P-28), #10의 X 핸들러 좁히기와 같은 지점 |
| **F30** | **(v0.5) 외삽 감도** | 축 밖만 마지막 구간 기울기로 선형 외삽한 가상 LUT: current_reuse 전체 실행 θ* 이동(L_class__M68 0.511 → 0.466 µm 등), area 806.9 → 724.5 µm²(−10.2 %), gain −0.84 dB, cmrr −1.5 dB. M2b W 외삽 −12 % 대 SPICE −1.3 %. folded M7은 음수 방향 외삽이라 비물리 | [ud17] §4.2·§4.3 | 결과 숫자가 클램프 규칙에 의존한다 -- '작은 오차라 무해' 불성립. 외삽은 대안이 아니다(P-29) |
| **F31** | **(v0.5) gm/ID 근 모호성(계획 B20 종류)** | folded M1(pmos L 0.34 µm, gm/ID 17.5)은 곡선 평탄부(VS 0.8 곡선 …17.6, 17.5, 17.6, 17.5…) -- LUT와 SPICE가 같은 VS에서 근을 달리 고른다(VGS 1.073 대 1.012, IDu ×3). current_reuse M9a(pmos L 0.15 µm, gm/ID 15.5)는 VS ≤ 0.4에서 근이 둘(SPICE 첫 근 VGS 0.33~0.44, LUT 근 0.84) | [ud17] §1.3 주의·§6.4 | #31(DF-10 + B24 (b), UD-5)의 실회로 입력 기록 |

| **F32** | **(v0.6) folded 빠른 점검: 극성만 바꾸면 무엇이 남는가**([pack] §2.2 -- 엔진 `propagate_node_voltages`·`derive_vsb_from_nodes`(수정 없음)에 θ* vds를 고정해 넣고 연결만 바꿈. F0이 F27 충돌 4건을 값까지 재현) | F0 선언 그대로: Y 1.6·X 1.6·Vg9 1.1·out 1.0. **F1 M1·M2 kind → nmos**: Y 1.2·X 1.2·Vg9 0.7·out 1.0, 축 밖 M5 1.4·M7 −0.25(M1·M2는 0.2로 축 안). F2 pmos 유지 + source↔drain 교환: F1과 같은 노드값, 축 밖 M2 1.4·M5 1.4·M7 −0.25. **F3 = F1 + M1·M2 vds 1.4(X = Y = 1.6이 되게 맞춘 예시)**: out **1.0**, Vg9 0.95/0.45 = **0.5** 남음, M7 vsb 0.95(Y 경로) | [pack] §2.2 | X·Y 1.6 V = 극성 0.4(UD-17a) + tail 컬럼 1.2(UD-17c 입력 CM). X·Y를 닫아도 출력 컬럼 1.0 V·Y 컬럼(Vg9) 0.5 V 공백은 UD-17c(`bias3`·출력 CM 또는 엔진 규칙) 몫. **M7 vsb는 Vg9를 정하는 경로에 따라 0.95(Y 경로)/0.45(M9 경로)** -- [ud17]의 SPICE 일관값 0.45는 M9 경로 기준이다. 사이징·헤드룸 재배정은 다시 하지 않았다(노드전압만 재전파) |
| **F33** | **(v0.6) current_reuse 빠른 점검 C1 -- UD-17d (i)을 메타데이터로만 흉내** | `diffpair_branch_a`를 Vom1에서 위/아래로 나누고 아래 반쪽 예산 = V(Vom1) 0.6773 V로 묶으면(vds만 바꾸고 의존 replica 컬럼 재배정은 안 함): 아래 반쪽 0.6773 − M3a 0.2 − M4a 0.45 = **M5 vds 0.0273 V**(포화 여부 **[미측정] -- 판정 기준은 6b**(봉인 항목 7, VDsat 유도 DF-25). (v0.7) v0.6의 '포화 불가 -- 거부 예상'은 Phase 4에 없는 기준으로 쓴 문장이었다), 위 반쪽 M6·M7 vds 0.25 → 0.4727, Vx 1.55 → 1.3273, N1a2a 0.8773으로 일관. 그때 **M2a·M2b vsb 0.9227은 파생값이 아니라 진짜 축 밖**(LUT 0.8 초과, SPICE 클램프 오차 ΔVGS 23 mV·IDu 1.3 %). C1에 남은 M58·M64 충돌 2건은 replica 컬럼(vbias2_stack·vbias3_stack)을 재배정하지 않아서 생긴 것 | [pack] §4.2 (i) | (i)은 아래 세 소자 최소합 0.9 V를 0.677 V에 넣는 **설계 변경**(M4a vds·M5 vds·M3a vds 배분 또는 출력단 VGS)이 함께 있어야 동작점이 된다. (ii)(컬럼 0.9 V가 맞음)이면 M16·M26 VGS 0.9 V가 되어 compensation gm/ID 18.0과 충돌하고, M2a·M2b vsb는 0.7(축 안, [ud17] 일관값 -- (ii) 전제). prep의 'M2a·M2b = F27 파생'은 (ii)일 때만 맞다 |
| **F34** | **(v0.6) `bulk` 필드 부재** [재측정 v0.6] | library `folded_cascode.topology.json` 13소자·`current_reuse_telescopic_ota.topology.json` 51소자 중 `bulk` 키 **0**. SR에서 `bulk` 문자열은 `derive_vsb_from_nodes`(3789행) docstring 3795·3796행("NMOS (bulk=vss)", "PMOS (bulk=vdd)")뿐 -- 엔진은 레일 bulk만 가정하고 `bulk` 선언을 읽는 코드가 없다 | 부록 A E2, [pack] §1.2·§3.2·§4.3 | bulk = 자기 source(별도 n-well) 선택지(UD-17e (ii))는 (1) **connectivity 변경**(새 `bulk` 단자 -- 사용자만) (2) **엔진 배선**(스키마 수용 + `derive_vsb_from_nodes`가 선언 bulk를 읽음 -- 공유 코드, 승인된 card = #22의 DEC-61 몫, §5.4)이 둘 다 있어야 한다. 지금 `bulk` 키를 넣으면 엔진이 그것을 조용히 무시하는지 거부하는지는 [미확인](#22 작성 전 실측) |
| **F35** | **(v0.6) folded json 설명 주석이 connectivity와 어긋나는 곳 3** [재측정 v0.6] | (1) `symmetry._matching_pairs_comment` "M3/M4는 MP(gate=drain=**tail**)", "M9(gate=drain=**X**)" ↔ netlist MP gate=drain=`vb1`, M9 gate=drain=`Vg9` (2) `_netlist_correction_2026-08-05` "**X-branch(M5)** … **Y-branch(M6)**" ↔ M5.source = `Y`, M6.source = `X` (3) `_device_roles_comment_fold` "Y 노드(M4/M5/M7/M9)" ↔ 넷 Y = M2.drain·M4.drain·M5.source(M7·M9는 Y에 닿지 않음) | [pack] §1.4 | 판정 아님(connectivity는 사용자가 확정한 것). 주석은 메타데이터라 공동분석 확인 뒤 Claude가 고친다 -- #53의 데이터 커밋에 넣는다(같은 파일 순차 커밋, §3.4). 회로도 대조 때 주석이 아니라 json 파생 넷 표를 쓴다(B47) |
| **F36** | **(v0.9) 노드전압 사슬의 근거 없는 `tol=1e-6` 세 곳과 이름 가림** [재측정 v0.9, HEAD `0f23786`] | `propagate_node_voltages(…, tol: float = 1e-6, max_passes: int = 50)`(3727~3729, `diff > tol` → conflicts). `reconcile_vsb_from_nodes(ctx, by_name, vdd, tol: float = 1e-6)`(3808): 3831 `propagate_node_voltages(by_name, ctx.sized, vdd)`(tol 미전달), 3843 `old is None or abs(old - exp) > tol`이면 vsb 덮어씀. `audit_vsb_consistency(by_name, sized, vdd, tol: float = 1e-6, **kw)`(3850~3851): 3863 `propagate_node_voltages(by_name, sized, vdd, **kw)` -- 자기 `tol`은 3875 `abs(d) > tol`(vsb 비교)에만 쓰여 **`tol`이 `**kw`로 전달되지 않는다**(이름 가림). 운영 호출부: 7294(`_hr_resolve_vertical_group`, `try … except Exception: _uvsb_node = None` 7296~7298), 7449(같은 함수, `except Exception: _dvsb = None` 7450~7452), 8658 `reconcile_vsb_from_nodes(ctx, by_name, _vsb_vdd)`, 8892 `audit_vsb_consistency(by_name, ctx.sized, _vsb_vdd)`(그 결과가 있으면 `ValueError` -- 게이트). 비운영 호출부: `tests/probes/probe_full_research.py:142` `sr.audit_vsb_consistency(by, sized, VDD)`(일회성 진단 probe, pytest 수집 밖). `tests/contracts/test_ts6_dead_probes.py`의 `audit_vsb_consistency` 언급은 합성 소스 문자열(호출 아님) | `git -C R grep -n -w` 세 이름(부록 A H2) | #23 범위(§5.5). 기본값을 없애면 7294·7449의 `TypeError`는 `except Exception`이 삼켜 '노드값 없음'(None)으로 바뀐다 -- #13(DF-14, 부록 C.1 7297·7451 `R #13`)이 그 핸들러를 없애기 전에는 런타임 오류로 드러나지 않으므로 #23 oracle은 호출부 AST 단언을 둔다 |

**재측정하지 않고 인용하는 핵심 사실**(모두 [prep], card 작성 전 실측 대상): v0.2 §2 뒤 목록 그대로(U-27 도구 비트 재현, 구조 규칙 극성 9/9, CMRR 73.14488 → 73.38009, B26-1 scratch, 보류 행 25개, B34 재현, B35 사용처 12(운영 8)와 9회로 `RAILS∩넷 = supply_nets∩넷`, B26-1 검토 B1·B2·S1·S3).

---

## 3. card 묶음, 순서, 의존

### 3.1 Phase 3 모듈 파일과의 관계 (Phase 3 초안 **v6** 기준 -- (v0.8) v7에서 모듈 배정 절 변경 없음, 항목 7 D-27 추가)

계획상 Phase 4 착수 = Phase 3 DoD PASS 뒤(N6.1 공통). 아래 MOD 표기는 `00-common`이 정한 목적 모듈이거나 Phase 3 §6.2 A-3 계산 결과다. **최종 파일은 D0b 이관표**(Phase 3 §8 D0b)가 정한다. (v0.4) 입력을 Phase 3 초안 v4로 바꿨다. v3 → v4에서 MOD 배정(A-3, D-3, D-5, D-10)은 같아(검토2 2-7) 아래 표 내용은 바뀌지 않는다. 표의 "Phase 3 v3" 인용은 v4·v5의 같은 절을 가리킨다.
(v0.5) 입력을 Phase 3 초안 **v5**(`draft_phase3_design_v5.md`, 3차 검토 `review3_phase3_v5.md`)로 바꿨다. v4 → v5에서 이 문서에 닿는 것: (1) 머리·§9.1 재측정 조건 (1)에 **B34·B26-1 병합 뒤 엔진 줄·부록 A 재측정**이 들어갔다(v0.4 §9-11 요청 반영) (2) §6.4 **D-19**: `rail_declaration`·`RailDeclaration`을 MOD2(`topology_authoring.py`)에 둔다(N3.10 MOD2 대표 대상 추가 -- 3차 검토 S4가 근거 정정과 사용자 질문을 요청, 아직 결정 전). 같은 절이 **B37a `port_declaration`·`PortDeclaration`도 같은 MOD2**라고 적는다 -- #47 card의 모듈은 D-19 결정을 따른다 (3) D-18 redteam 번호 확정(G1 32·B33 33·면제 묶기 34·범위 정책 35) (4) G1 base = 33·34·35 병합 뒤, 옮긴 def·이동 후보 거부 def는 새 def(D-20), 면제 대조 불변(D-21), M card V3 JSON `not_targeted` = 0·`targets_by_def` = `{}`. (5) v5 §5.5.4의 'B33 V3 인벤토리 33,991 → 79,809'는 B33 개정 전 값이다(개정값 44,493 -- 3차 검토 S1 (iii), Phase 3 design 몫).
**(v0.6) 입력을 Phase 3 초안 v6(`draft_phase3_design_v6.md`)으로 바꿨다.** v5 → v6에서 이 문서의 모듈 표기에 닿는 것:
1. **A-3 계산 3건이 UD-0 N3.10 개정 문안에 들어갔다**(`p3_doc_amendments.md` §1, v6 §6.2·§9.1 'N3.10 개정 시점'): `load_topology` → MOD3, **`validate_theta_declaration_order` → MOD3(v6 확정** -- 호출하는 `_build_shared_current_joint_plan`·`_shared_current_groups_from_compensation`의 레지스트리 목적지가 `circuit_state_graph`), `optimize_full_circuit_budget` Phase 3 위치 MOD8(N3.10 MOD6 행의 백틱 토큰을 MOD8 행으로 옮김, 탐색부 추출 뒤 MOD6 = CC-7). 그 밖의 충돌은 D0b가 계산하면 **따로** 사용자 승인(D-11) -- 이 문서의 MOD 표기는 그 승인 전까지 '3건 + D-19'만 확정으로 본다.
2. **D-19는 따로 묻는 질문**이다(v6 §9.2): (가) MOD2(N3.10 MOD2 '대표 대상'에 `rail_declaration` 추가) / (나) MOD3(규칙 A-5, 표 개정 없음). `RailDeclaration`은 어느 쪽이든 MOD2(A-2). 이 문서의 영향: #1이 만든 `rail_declaration`의 Phase 4 위치(#17이 극성 필드를 더하는 `RailDeclaration`은 MOD2 고정), #47 접근자 `port_declaration`·`PortDeclaration`의 모듈("`rail_declaration` 옆"이 (가)면 MOD2, (나)면 MOD3).
3. **D-22**(재수출·import 줄 위치, 함수 안 지연 import 우회 금지, M card·F1의 IMPORT-ANY): Phase 4는 Phase 3 DoD(F2 -- SD의 MOD9 위쪽 재수출 삭제) 뒤라 중간 상태 순환은 물려받지 않는다. 물려받는 것은 **규칙**이다 -- Phase 4 card가 더하는 공유 기호도 'N3.10 import 규칙(번호가 작은 모듈 쪽으로만) + 함수 안 지연 import 금지'를 지켜야 한다. 그래서 두 곳의 배치를 원칙으로 정했다(P-33 `FallbackEvent`·`record_fallback`, P-34 LUT 축 밖 오류의 raise 위치 -- 아래 표). Phase 3 LAYER 판정(E1, `import_layering.py`)은 Phase 4 병합본에서도 V1 PT 계약 test로 계속 돈다 [미확인: Phase 3 DoD 뒤 `import_layering`이 상시 test인지 -- Phase 3 E1 정의 확인 대상].
4. **D-23**: phase 3 card(T0·D0a·D0b)의 병합은 Phase 2 DoD 뒤. Phase 4 card의 모듈 확정(D0b)도 그 뒤라는 뜻이다(§8.2).
5. **D-25**: M10 진입점 E-INST test의 회로 = 네 library 회로 중 E-INST 한 판이 가장 짧은 것(기록상 후보 folded_cascode 13~19 s). 그 test는 base 해시 대조라 **#23(F27)·#25(F26)·#53이 folded 결과를 바꾸면 그 card에서 기대 해시가 바뀐다** -- DEC-40(§7.4). current_reuse를 고르면 #54가 같은 처지다.
6. D-24(E3 AST 문자열 import)는 이 Phase와 무관하다.
7. **(v0.8, Phase 3 v7 D-27 -- 4차 검토 S4) 엔진 card 동결**: D0b 병합부터 F2 병합까지 엔진 파일(`A/*.py`, `workspaces/run_harness.py`)을 바꾸는 Phase 3 밖 card는 병합하지 않는다(v7 §8.1·§9.1). 확정 순서에 없는 엔진 card의 **기본값 = F2 뒤**이고, Phase 3 v7은 Phase 3 전에 넣으려면 **D0b 병합 전**에 병합하는 경로도 둔다. 이 문서에서 해당하는 card = #2·#3·#4(엔진 정의 삭제·이관 -- #4는 test-only지만 `A/*.py`의 D-7 정의를 옮긴다)와 #17·#18(B26-2·B26-3). **(v0.9, 5차 검토 N-S1) 이 다섯 card는 앞당김 경로를 쓰지 않는다 -- F2 뒤 단일 경로**: 선행인 UD-0(#2~#4)·UD-1·UD-15(#17 → #18)는 Phase 4 착수 때(Phase 3 DoD 뒤) 올리는 승인 질문에 들어 있어, 승인 시점 간선을 넣으면 D0b 전 앞당김은 순환이다(부록 A H5 RC1·RC8·RC9). v0.8의 'R1·R8·R9 비순환'은 승인 노드가 없는 그래프의 결론이었다. 앞당기려면 D0b 전에 별도 승인 질문이 필요한데(H5 N1 -- 비순환) 사용자 결정을 늘리는 쪽이라 기본안으로 두지 않는다(머리 v0.9 N-S1 근거). D-26(E3b, SD 임시 재수출 삭제 뒤 이름 해석)은 Phase 4가 물려받는 F2 뒤 상태의 판정이라 이 문서의 card 규칙을 바꾸지 않는다.

| card | 필요한 모듈 | 근거 |
|---|---|---|
| CC-4a·CC-4b | MOD2(`SchemaRejectedError`·`FailureRecord`), MOD4(N3.14 예외·`FAILURE_CLASSES`·`exit_code_for`) | `00-common` §7.1 |
| CC-5, MG1 | MOD2(`LEGACY_NAMES`·`load_json_checked`) | `00-common` §6.1 |
| CC-7a·CC-7b | **MOD8에서 추출해 MOD6으로**(Phase 3 v3 D-3: `optimize_full_circuit_budget`의 Phase 3 위치는 MOD8, 탐색부 추출 뒤 MOD6), MOD10(`instrument`). (v0.6) v6 UD-0 개정 문안은 N3.10 MOD6 행의 `` `optimize_full_circuit_budget` 탐색부 `` 백틱을 MOD8 행으로 옮긴다 -- 그러면 CC-7a가 MOD6에 만드는 추출 함수는 MOD6 '대표 대상'에 이름이 없다. 규칙 A-1이 아니라 A-5(소비자)로 정해지는 것은 문제가 아니지만, 계획 문구 '탐색부 = MOD6'을 CC-7a card가 추출 함수 이름으로 다시 적는다(§9-20) | `00-common` §10.1 435행, Phase 3 v6 A-3·D-3 |
| CC-8 | MOD10(`activations_out`) | `00-common` §11.2 |
| DF-02(tol_V) | MOD1 | 계획 N3.6 |
| 로드 경로(`load_topology`) 수정 card(B26-1·B34·B26-2·B37) | **MOD3**(Phase 3 v3 A-3: 표 MOD2였으나 구조 자동채움을 불러 MOD3. (v0.6) v6에서 UD-0 N3.10 개정 문안 3건 중 하나) | Phase 3 v6 §6.2·`p3_doc_amendments.md` §1 |
| (v0.6) `rail_declaration`(#1이 만듦)·`RailDeclaration`(#17이 극성 필드 추가) | `RailDeclaration` = **MOD2**(A-2). `rail_declaration` = **D-19 답**((가) MOD2 / (나) MOD3) | Phase 3 v6 §6.4·§9.2 D-19 |
| (v0.5) B37a 접근자 `port_declaration`·`PortDeclaration`(#47) | **`rail_declaration` 옆** -- D-19 (가)면 MOD2, (나)면 MOD3(v6: 사용자에게 따로 묻는 질문. B37a card 커밋 때 오케스트레이터가 결정대로 적는다) | Phase 3 v6 §6.4 |
| W-1 `theta-order-gate`(#40) | **MOD3**(`circuit_state_graph.py`) -- (v0.6) v6 확정: `validate_theta_declaration_order`가 부르는 두 함수의 레지스트리 목적지가 `circuit_state_graph`(129·131행)라 A-4로 MOD3, UD-0 N3.10 개정 문안. (v0.5까지 'D0b 확정 뒤') | Phase 3 v6 §6.2 |
| (v0.6) `FallbackEvent`·`record_fallback`·`collect_fallbacks`(#13) | **P-33**: I·D 지점이 있는 MOD 중 **가장 작은 번호**(D0b 이관표로 #13 작성 전 실측이 정한다. `FailureRecord`가 MOD2인 것과 같은 이유 -- 낮은 모듈이 높은 모듈을 import하지 않게). v0.5 §10.1-1의 'MOD4'는 MOD1~MOD3에 I·D 지점이 없을 때만 맞다. 함수 안 지연 import로 우회하지 않는다(D-22). **(v0.7, m2) 승인 경로**: 결과 모듈이 그 MOD의 N3.10 '대표 대상' 밖이면(예: I·D 지점이 MOD1에 있어 `FallbackEvent`가 LUT 모듈로 가는 경우) Phase 3 v6 D-11('그 밖의 충돌은 따로 사용자 승인')에 해당하는지 #13 작성 전 실측이 확인하고, 해당하면 그 승인이 #13의 착수 조건이다 | `00-common` §7.1 'N3.10 import 규칙', Phase 3 v6 D-22 |
| (v0.6) LUT 축 밖 오류(#25, `lut_axis_out_of_range`) | **P-34**: 검사·raise는 MOD1(보간 함수 입구)이지만 MOD1은 N3.14 예외(MOD4)를 raise할 수 없다(`00-common` §7.1 'raise 위치 규칙: N3.14 예외는 MOD4 이상'). 그래서 MOD1은 **MOD1에 정의한 정의역 오류**(축·값·격자 범위를 싣는다)를 내고, 그것을 처음 받는 MOD4 이상 호출부가 `SealViolationError`(레코드 항목 `lut_axis_out_of_range` + 소자)로 바꾼다 -- MOD3 `status` → MOD4 `StructureUnresolvedError`와 같은 모양. P-28(원인 바꿔 보고 금지)은 이 변환이 클래스·사유를 보존하는 것으로 지킨다. **(v0.7, S2)** X 핸들러(후보 배제)가 잡는 타입 = MOD1 정의역 오류이고, 변환은 집계 지점(MOD4 이상)에서 한다 -- X 핸들러 동작 규칙은 P-34 하나(§7.2), 인터페이스는 §10.7 | `00-common` §7.1, 계획 LR3·DF-27 |
| analog-grammar 어댑터(`_import_analog_grammar` 등) | D0b 확정 뒤(`prep_b34_b35_grammar.md` §4의 'MOD2' 가정은 Phase 3 v3 A-3 이전 판이라 쓰지 않는다) | Phase 3 v3 §6 |
| 그 밖 DF card | 고치는 함수가 Phase 3 뒤 있는 MOD 파일 | D0b 이관표 |

MOD10 진입점 시그니처는 Phase 3 v3 §2.3(`run_gmid_design_pipeline(spec, *, topology_path, search, output_dir)` -- v6 §2.3 같음)을 받고 CC-7·CC-8이 `instrument`·`activations_out`을 더한다. Phase 3 초안이 승인 전이므로 이 연결은 **Phase 3 design 승인 뒤 확정**이다.

**Phase 3 design 쪽 교차 항목(Phase 3 design에 요청 -- §9-11)** -- **(v0.5) Phase 3 v5가 반영했다**(재측정 조건 (1)에 B34·B26-1, §6.4 표). §1 범위 밖 문구 "레지스트리 §2 '정본 후보'의 정본 확정(B26, Phase 4)"는 그대로 맞다 -- 정본 확정은 B26-4(#19)의 몫이고 #19는 Phase 4다. 아래는 v0.4 요청 원문(기록): Phase 3 v4 머리의 재측정 조건은 P9·P10뿐이고, v4 §1 범위 밖은 여전히 "정본 확정(B26, Phase 4)"이다. 그런데 **A2 승인(2026-10-01)으로 B26-1(#1)과 B34(#45)는 Phase 3 전으로 확정됐다**(두 card 머리 `phase: 2`, `approval: 20260930-b26-before-phase3` -- (v0.9.2) 지금은 `phase: 3`, 기록 `20261001-b26-phase3-cards`, §9-19). 둘 다 SD·SR의 큰 def(`load_topology`·`propose_device_roles_gap_fill`·`_build_theta_evaluator` 등)를 바꾸고 새 def(`rail_declaration`)를 더하므로 D0b 이관표 원자료(정의 위치·참조 그래프·A-3 계산)가 바뀐다. 그래서 Phase 3 v4 머리의 재측정 조건에 **"B26-1·B34(및 Phase 3 전에 병합되는 #2·#3·#4)가 병합되면 D0b 작성 전 실측과 부록 A M6·M18·M22·G6을 그 병합본에서 다시 잰다(P9·P10과 같은 방식)"**를 더해야 하고, §1 범위 밖 문구 "B26, Phase 4"를 "B26-1은 Phase 3 전(A2), B26-2~4는 Phase 4"로 고쳐야 한다. 이 요청은 Phase 3 design 개정 몫이다(이 문서가 Phase 3 design을 고치지 않는다). 또 Phase 3 v3 D-10('보류(Phase 3) 9행은 옮기고 D 유지')과 이 문서 #2~#4(D-1~D-7 삭제·이관)는 대상 행이 달라 직접 충돌하지 않는다. 다만 #2~#4가 먼저 병합되면 Phase 3 이동 대상 수가 줄어든다.

### 3.2 Phase 3보다 먼저 할 수 있는 것

원칙 근거: 계획 N3.10 "등급 D 함수는 옮기기 전에 처리한다", 곧 지울 코드를 옮기지 않기 [prep: `prep_b26_supply_nets.md` §3.5]. **(v0.9, N-S1)** 이 절의 'Phase 3보다 먼저'는 확정 순서에 있는 card(B26pre·B26-1·B34)와 인용 card에만 남는다. #2·#3·#4·#17·#18은 F2 뒤 단일 경로다(§3.1 항목 7) -- D-1~D-7은 UD-0 승인 전까지 U-02의 `보류(Phase 4)` 행이라 N3.10의 '등급 D' 규칙이 Phase 3 이동에 걸리지 않는다(삭제·이관 등급은 UD-0 뒤에 생긴다).

| card | 앞당길 수 있는 조건 | 막히는 것 |
|---|---|---|
| **B26-1** `20260930-b26-rail-accessor-set`(#1) | **(0) (v0.7, 확정 순서 -- `user_decisions.md` 2026-10-01) Phase 2 DoD PASS**(B34·B26-1은 Phase 2 DoD N6.3 목록 밖)**와 B26pre `20260930-b26-pre-test-strengthen` 병합**(B34 뒤·B26-1 앞, test-only -- 아래 B26pre 행) **(v0.9.2)과 backfill 결함 card `20261001-b26-backfill-interdig-final-audit` 병합**(U-BF 결정 -- B26pre 뒤·B26-1 앞, 아래 backfill 행) (1) 계획 정정안 `draft_b26_plan_patch.md` 커밋(판정 표 무변경, N3.16 문구는 검토 S5대로 -- v0.5: 아직 커밋 전, **v0.6: `8356c1e`로 커밋됨**(커밋 메시지 '계획 정정(A2) … plan_tables_hash 불변')) (2) P9 병합 뒤 base(**v0.5: P9 병합됨 `93b18db`**) (3) **A2 승인 기록 `20260930-b26-before-phase3`이 gate에 있음**(**v0.5: `2d58fd8`로 gate에 들어갔다** [재측정 v0.5]) (4) **B34(#45) 병합**(B26-1 card 착수 조건 4 -- 순서 P9 → B34 → B26-1, `b34_revision_log.md` §6) (5) **V3 경로(A1 결정됨 -- 선택지 2, A1-b 정정으로 T6 넓힘)**: 면제 묶기 card `20260930-v3-exempt-binding`(A1-a 승인, P9·P10·P10b 뒤) → 범위 정책 card `20260930-v3-changed-stmt-scope`(#48, A1-b 승인) 병합 뒤 그 규칙으로 V3(B26-1 변이 2,472 → **294**, 승인 당시 정의로는 228). (v0.8, m5) B26-1 card v4(`draft_b26_1.spec.md` 16:41)는 'V3 계획' 절을 이 결정으로 이미 바꿨다 -- v4 모의 head 대상 301(N2b 235), 생존 27 → 남는 24(E6 13·E7 5·trace 2·등가 4, card 317행), 그 처리 질문 `b26_1_survivor_question.md` Q1(16:41)의 권고 1이 '앞선 test-only card + 등가 정리'다. B26pre(`draft_b26pre.spec.md` 16:07)의 수치(생존 34 → 새 test로 25 죽임, 등가 후보 9)와 측정 판이 다르다 -- 두 card의 수·등가 후보 목록 대조는 오케스트레이터 몫이고, 사용자 결정은 '등가 후보 처리' 하나(B26pre U2 = survivor Q1의 등가 몫)다 [prep] (6) spec card 보강(검토 `review_b26_1.md` B2·S1·S4·B1-3 -- **B34 인계 사이트는 반영됨**, `b34_revision_log.md` §6: 대상 def 32·변이 2,438(지금 규칙)). **(v0.6, B26-1 card v4 작성 중)**: (7) 인계 사이트 **10·14는 B35로**(`review2_b26_1.md` B2 E2·E2b -- 내어쓰기로 두 블록 부분 트리 전체가 N2 대상(T1)이 되고 기존 test·계획 계약으로 생존 13 + 1). #1 몫 = 9·10b·13 + B40 (8) ~~U3~~ **(v0.7) B26pre로 대체**: 계획된 계약으로도 죽지 않는 생존 변이 중 E6·E7 몫(v4 모의 head 재측정 34개)은 앞선 test-only card **B26pre**가 기존 동작 test로 25개를 죽이고(기준 약화 없음), 남는 **등가 후보 9개**의 처리가 **B26pre U2**(사용자 -- 권고 (a)는 A1-a 묶기 면제 = 판정 약화, (b) B26-1 auditor equivalence 판정, (c) 백로그 + V3 FAIL 감수). E1·E3·E4 몫은 B26-1 자기 계약(7(e)·4·14). **(v0.9, B26pre v2 -- `b26pre_revision_log.md` v1 → v2)** 위 수치는 v1 판이다. v2: base 32문장 중 29를 죽이고 남는 3(SR 11800·11802·11879)이 B26pre **U2**(그 card의 착수 조건 아님): (a) SR 11802 등가 면제 1건은 B26-1 V3를 N2d로 잴 때만 필요(N2w 규칙이면 대상 밖), (b) SR 11800·11879(`_backfill_interdig_ok`)는 등가가 아니라 **기존 결함으로 보이는 동작** -- 사용자 질문 **U-BF**(`b26_backfill_question.md`, 권고 = red-green 결함 card를 B26pre 뒤·B26-1 앞에). 그래서 v0.7~v0.8의 'B26pre U2 = 등가 후보 9개 처리(권고 (a) 묶기 면제)'는 **U-BF 하나 + 조건부 U2-a**로 바뀌었다 (9) **U4**: B40(`unavailable_reason` 키 삭제 = 관찰 가능한 출력 변경)이 A2 기록 범위 설명에 없음 -- 짧은 추가 승인 또는 B40을 범위에서 뺌 (10) **U5**: P9 계약 test 2개의 시그니처 단언 갱신 = V5 `target_kind: diff` 승인(작성자≠검증자). **(v0.9.2) (8)~(10) 결정됨**: U-BF = 결함 card(위 (0)), U4 = 기록 `20260930-b26-b40-reason-key`, U5 = 기록 `20261001-b26-p9-signature-update`, U3(B26-1 통합 질문 Q1 -- 등가 4개) = 정리 C1·C2 + `range` const− 1개 면제(기록 `20261001-b26-v3-equiv-range` -- (v0.9.3, R1) 1차 시도(병합 안 함) code 커밋 K1 뒤 auditor 측정 해시로 **2차 시도 착수 전** 커밋 -- B26-1 card(`draft_b26_1.spec.md` 22:20 판) '두 번 시도 절차' 2·'승인 줄 배치' 5·착수 조건 8 인용: card 착수 조건은 아니고 2차 시도의 선행). U2-a는 없어졌다(N2d를 쓰지 않음) | 초안 v4 작성 중(phase 2 → (v0.9.2) phase 3, approval A2 + `20261001-b26-phase3-cards`), 검토2 blocking B1(V3 계획 절 낡음)·B2(생존 72). (v0.7) B26pre U2 |
| **(v0.7) B26pre** `20260930-b26-pre-test-strengthen`(phase 2 → (v0.9.2) **phase 3**, test-only, **인용** -- `draft_b26pre.spec.md`, approval 후보 `20261001-b26-pre-test-strengthen`) | 확정 순서상 **B34(#45) 병합 뒤, B26-1(#1) 병합 전**(card U3 = 원칙 기본안, 결정 아님 -- card는 B34와 독립이지만 새 test가 B34 def 인벤토리를 늘려 B34 뒤에 둔다). 엔진·도구·레지스트리·library 변경 0, 새 test는 base PASS. ~~착수 조건 = card U1(원칙 기본안의 사용자 확인)~~ **(v0.9, card v2) U1은 원칙 기본안(결정 아님)**이고 card는 `gate_change: no`라 머리 `approval` 줄이 없다(`merge_gate.gate_change_ok`는 `gate_change: yes`일 때만 확인 -- card v2 실측). 확정 순서의 "B26-1(앞선 test 보강 card 포함)"이 card의 존재와 위치를 덮는다 | B26pre U2는 이 card를 막지 않고 **#1의 V3 계획**을 막는다 -- (v0.9) U2 = U-BF 답(사용자) + U2-a(N2d로 잴 때만). U-BF가 '결함으로 고친다'면 결함 card(`draft_b26_backfill_audit.spec.md`)가 B26pre 뒤·#1 앞에 온다(부록 A H5 S9 비순환). **(v0.9.2) U-BF 결정됨(고침)** -- 결함 card는 확정 순서에 들어갔다(아래 행, 부록 A I1 기본 노드). card 머리 `approval` 줄 = `20261001-b26-phase3-cards`(phase 값 근거) |
| **(v0.9.2) backfill** `20261001-b26-backfill-interdig-final-audit`(phase 3, red-green, **인용** -- `draft_b26_backfill_audit.spec.md`, approval `20261001-b26-backfill-interdig-fix`·`20261001-b26-phase3-cards`) | U-BF 결정(2026-10-01 "결함으로 고침 (Recommended)"): `run_matching_safety_with_finger_growth`의 `relaxed_pairs[i]["interdig_ok"]`를 반환 audit(euler 정리 뒤)의 3b로 채운다. 확정 순서 **B26pre 뒤·B26-1 앞**. 계약은 그 card 그대로(재서술하지 않음) | 없음(답 받음). Phase 3 v8.2 실측 인용: `interdig_ok`는 `pipeline_result`까지만 가고 `instance.json`·report에 닿지 않는다(E-INST 무변화 -- Phase 3 E5 `EXCL_INST` 없음) |
| **B34** `20260930-b34-grammar-explicit`(#45) | ~~phase 2 card로 확정~~ **(v0.9.2) phase 3 card**(Q-B34-PHASE, 기록 `20261001-b26-phase3-cards` -- 순서는 그대로 Phase 2 DoD 뒤·M card 전. Phase 3 전 앞당김 자체는 A2 기록이 덮는다). 범위 = 4 def(`_import_analog_grammar`·`find_idiom_matches`·`find_stack_edges`·`audit_theta_root_direction`) + docstring 전부(SR `resolve_stack_layout` 6509~6512 포함). V3는 **지금 규칙으로 변이 55, 기존 test·card 계약으로 55/55 죽음, 면제 0**(card '작성 전 실측' -- A1과 무관하게 판정 가능. N2(넓힌 T6 포함)로는 대상 10 -- `v3_cards_revision_log.md` §6). **(v0.7) 순서는 확정 순서 Phase 2 DoD → 34 → 35 → B34**(사용자 2026-10-01, `user_decisions.md` "card 순서"). v0.6의 '34·35와의 순서는 자유, 필수 선행은 P9뿐'은 기술 의존만 본 문장이었고 확정 순서로 대체한다. B26-1보다 **먼저**(같은 파일, B26-1 착수 조건 4). **(v0.6) 최종판**(`draft_b34.final.spec.md`, `b34_commit_plan.md`, 측정 `2d58fd8`/`8356c1e`): 변이 55·N2 대상 10 그대로, interface card 14행 전부 `stick_diagram`, 인계 사이트 10·14를 B26-1 → **B35**로(승인 기록 문구 'B26-1·B35로 넘김' 안). 작업 순서(커밋 계획 §1)는 P10 → P10b → **Phase 2 DoD** → 34 → 35 → B34 → B26-1 → B33 -- **(v0.7) 이것이 사용자 확정 순서다**(B26pre가 B34와 B26-1 사이에 들어감). Phase 3 v6 §9.1의 'Phase 2에 남은 것 = B34·B26-1 병합'과의 어긋남은 읽기 (나)로 닫았다(§9-19) | **병합 선행 사용자 작업**: `install.py` `SKILLS`에 `"analog-grammar"` 추가(F23). 이것 없이 병합하면 설치본은 조용히 틀리던 것이 명시적으로 실패하는 상태가 된다 |
| ~~B26-4 `b26-rail-literal-lint`(#19)~~ **(v0.4) Phase 3 전 불가** | 선행 #21(MG1)이 #20 → #6(CC-4a, Phase 4 선두)을 조상으로 가진다(검토2 S10 위상 정렬). 그래서 `P3?` = Y | -- |
| **d4-delete-unwired**(#2) | **(v0.9, N-S1) F2 뒤(Phase 4, #5 앞) 단일 경로 -- 앞당기지 않는다**(선행 UD-0이 Phase 4 착수 때 질문이라 D0b 전 앞당김은 순환, 부록 A H5 RC1. v0.8의 'D0b 전 앞당김 가능'은 지웠다). U-02 승인이 '보류(Phase 4 배선)'로 둔 행을 삭제로 바꾸는 것 -- UD-0으로 덮는다. **`test_ic5` `_DOMAIN_TABLE`의 D-4·D-5 두 행을 이 card에서 함께 지운다**(V5 1회, F18) | DEC-40 V5 승인 |
| **pole-oracle-to-tests**(#3) | 위와 같음((v0.9) F2 뒤 단일 경로 -- D-6 정의를 SR에서 옮긴다). 계획 DEC-25·DF-06 문장 정정 동반 | #12·#19보다 먼저 |
| **toy-lut-to-tests**(#4) | test-only 이관(D-7 정의를 `A/*.py`에서 tests로 옮기므로 엔진 파일이 바뀐다 -- (v0.9) F2 뒤 단일 경로) | (v0.8) v0.7의 'Phase 3 F1과 묶어도 된다'는 D-27(F1은 D0b~F2 구간)과 어긋나 지웠다 |

(v0.9, N-S1) 위 세 행은 표에 남겨 두지만 'Phase 3보다 먼저' 후보가 **아니다** -- 선행 UD-0이 Phase 4 착수 때 질문이라 F2 뒤 단일 경로다(§3.1 항목 7). B26-2·B26-3(#17·#18)도 같다: 선행 UD-1·UD-15가 같은 승인 질문(1차)에 있어 **F2 뒤(Phase 4) 단일 경로**이고 D0b~F2 사이에도 병합하지 않는다(D-27). v0.8의 'UD-1·UD-15가 일찍 결정돼 앞당기려면 D0b 전에만'은 그 결정이 승인 질문보다 일찍 올 수 없다는 점을 놓친 문장이라 지웠다(부록 A H5 RC8). Phase 3 v7/v8 §8.1 'B26-2~B26-4의 자리'의 '앞당기려면 D0b 전'은 Phase 3 쪽 일반 규칙이고 이 문서는 그 경로를 쓰지 않는다.

Phase 3 v4 §1은 "레지스트리 §2 '정본 후보'의 정본 확정(B26, Phase 4)"을 범위 밖으로 둔다. B26-1 당김은 A2로 **정해졌으므로**(Phase 3 D0b의 `_RAIL_NETS` 목적지가 바뀐다) Phase 3 design에 재측정 조건을 더하는 요청을 §3.1·§9-11에 둔다.

**A1별 #1 V3 경로(사용자 결정 A1 -- `draft_v3_decision_question.md`. 2026-10-01 결정: 선택지 2(N2, T3 (b)) -- 아래 표는 결정 근거 기록)**

| A1 | #1 앞의 게이트 card | #1의 V3 판정 | #1(과 뒤 엔진 card)이 떠안는 것 |
|---|---|---|---|
| 1 현 규칙 유지(def 전체) -- 택하지 않음 | 면제 묶기만(+ 데코레이터 NOOP 수정 별도 card) | V3 전수: 변이 2,472, 직렬 3.4 h ~ 129 h(현실 하한 약 19 h) | 어떤 test도 실행하지 않는 줄의 변이 **306개(개정 측정) 확정 생존** → test-author가 레일과 무관한 기존 동작 test를 쓰거나, card별 변이 id 면제(면제 묶기 뒤 `<id>@<def 해시>` 형식, 사용자 승인). B34·B26-2·B35·#47이 같은 큰 def를 다시 바꾸면 매번 반복 |
| **2 바뀐 문장 + 감싸는 제어문 + 삭제 지점 주변 + 새 def + 항상 `early_return`, def 머리 변경은 바뀐 매개변수를 읽는 문장까지(T3 (b)) -- 결정됨. (v0.5) A1-b 정정: T6 = 삭제 지점 바로 뒤 문장 + 바뀐 영역이 바꾸는 이름을 같은 블록 뒤쪽에서 읽는 문장(반복문 본문이면 위치 무관)** | 면제 묶기 → 범위 정책(#48) | 변이 **294**(승인 당시 T6로 228), 24.5분 ~ 15.6 h(현실 하한 0.88 h), 미실행 줄 대상 변이 9. **(v0.6)** P9·B34·인계 삭제를 넣은 재측정(`review2_b26_1.md` §2): N2b 265 / 넓힌 T6 314~336(사이트 10·14 포함), 생존 72 -- 10·14가 B35로 간 v4 범위의 값은 card 재측정 [미확인] | card가 쓴 코드의 test만. 놓치는 것 = 다른 블록·두 단계 이상 흐름·바뀌지 않은 문장의 기존 test 강도(승인 기록 문안). 대상 밖 변이 수(`not_targeted`)는 판정 기록에 남고 기존 test 공백 백로그로 간다 |
| (2a) 2 + def 머리 변경이면 본문 전체 -- 택하지 않음 | 같음 | 변이 1,309, 1.8 h ~ 71 h | B26-1 머리 변경 20개가 모두 키워드 `rails` 추가라 대상이 def 전체의 53% |
| 3 2 + 이름 한 단계 데이터 의존 -- 택하지 않음 | 같음(대상 정의 D1) | 변이 399, 33분 ~ 21 h | 2 + 바뀐 값을 쓰거나 대 주는 기존 문장의 test |

(수치는 B26-1 시뮬레이션 head 기준, V3 card 개정 뒤 재측정 -- `v3_cards_revision_log.md` §2. 개정 전 수치(N2 176, D1 506, 미실행 298)는 정의가 바뀌기 전 값이다. (v0.5) 선택지 2 행은 넓힌 T6 재측정 `v3_cards_revision_log.md` §6(+66 변이: `propose_device_roles_gap_fill` +18, `_branch_composite_pair` +12, `run_matching_safety_with_finger_growth` +8 등). 1·2a·3 행은 기각 대안이라 다시 재지 않았다.)

**같은 대상 선택 지점을 바꾸는 게이트 card의 병합 순서**: 범위 정책(#48)·G1(Phase 3 `20260930-p3-gate-move-aware`)은 둘 다 `mutate_changed.py`의 대상 선택(`changed_defs` 호출 앞)을 바꾸고, 면제 묶기는 같은 파일의 면제 적용을, B33은 V3 인벤토리 그래프(`reachability.build_graph`)를 바꾼다. 순서: **(P9·P10·P10b) → 면제 묶기(34) → 범위 정책(35) → #1** (Phase 2 진행 중, A1-a의 순서 문구), **P9 → B34(#45) → #1**, **B33(33) → G1(32)**, (v0.7) **확정 순서**(사용자 2026-10-01): P10b → Phase 2 DoD → 34 → 35 → B34 → B26pre → B26-1 → B33 → Phase 3(v0.5의 'B34와 34·35 사이는 자유'는 이 순서로 대체), **33·34·35 → G1**(Phase 3 v5 §5.5: G1 base = 셋 병합 뒤) → Phase 3 M card. (v0.5: P9는 `93b18db`로 병합됐다.) 뒤 card는 앞 card의 병합본을 base로 '작성 전 실측' 줄 번호와 무동작 목록(앞 card의 redteam 케이스)을 다시 잰다. 이동 규칙(계획 533행 '해시가 같은 함수는 V3 대상에서 뺀다')은 지금 도구에 없고 G1이 구현한다(V3 card 개정 S8 정정). 범위 정책 card는 'G1이 뺀 뒤 남은 대상 안에서 문장을 고른다'를 계약에 두고, G1 계약에 넣을 한 구절을 그 card '결정 필요 항목'에 적었다 -- 순서가 뒤바뀌면 나중 card가 그 구절대로 rebase한다. redteam 번호는 card에 박지 않고 작성 전 `ls tools/gates/redteam/attacks`로 정한다(네 card가 32·33을 다툰다 -- 검토2 2-9). **(v0.5) 정정**: 번호는 Phase 3 v5 D-18이 병합 순서와 무관하게 미리 나눴다 -- G1 `32-moved-defs`, B33 `33-v7-registry-edges`, 면제 묶기 `34-v3-exempt-binding`, 범위 정책 `35-v3-changed-scope`(세 초안 모두 반영, `redteam_numbering.md`). HEAD `2d58fd8`의 마지막 번호는 `31-v3-git-history` [재측정 v0.5]. 이 Phase의 card가 redteam 케이스를 더하면 36부터이고, 그때도 작성 전 `ls`로 확인한다.

### 3.3 순서

```
[확정 순서, 하드]  (v0.7, 사용자 2026-10-01 -- B34·B26-1은 Phase 2 DoD N6.3 목록 밖)
                   (P9 ✓93b18db·P10·P10b) ─> Phase 2 DoD ─> 면제 묶기(34, 20260930-v3-exempt-binding, A1-a) ─> 범위 정책 #48(35, 20260930-v3-changed-stmt-scope, A1-b = 선택지 2 + 넓힌 T6)
                   ─> B34(#45, phase 3; + plan-patch ✓8356c1e, A2 기록 ✓2d58fd8, 사용자 install.py 작업 뒤 병합)
                   ─> B26pre(20260930-b26-pre-test-strengthen, phase 3 test-only; (v0.9) U1 = 원칙 기본안)
                   ─> backfill 결함 card(20261001-b26-backfill-interdig-final-audit, phase 3, red-green; (v0.9.2) U-BF 결정 = 고침 -- 조건 없음)
                   ─> B26-1(#1, phase 3; + U4 ✓, U5 ✓, U3 ✓ -- (v0.9.3) 면제 기록 20261001-b26-v3-equiv-range는 1차 시도 K1 뒤·2차 시도 착수 전 -- card '두 번 시도 절차')
                   ((v0.9.2) 네 card `phase: 3` -- Q-B34-PHASE 결정 20261001-b26-phase3-cards, 간선 무관 §9-19. Phase 2 DoD ← Q-P2DOD-E2 정정 기록 20261001-p2dod-e2-wording)
                   ─> B33(33, 20260930-v7-registry-edges, 승인 + Q1 (a) 결정됨)
                   d4-delete-unwired(#2), pole-oracle-to-tests(#3), toy-lut-to-tests(#4), B26-2(#17)·B26-3(#18) -- 확정 순서 밖. (v0.9, N-S1) F2 뒤(Phase 4) 단일 경로 -- 선행 승인(UD-0·UD-1·UD-15)이 Phase 4 착수 때 질문
[Phase 3 게이트]   B33(33) ─> G1(32; base = 33·34·35 병합 뒤) ─> D0a ─> D0b(B26-1·B34 병합본에서 처음 계산 -- Phase 3 v6 §6.4)
                   D0b 병합 ━━ F2 병합: 엔진 card 동결(v7 D-27) -- 이 구간에 Phase 3 밖 엔진 card 병합 없음
                   Phase 2 DoD ─> T0·D0a·D0b 병합(D-23); B33 ─> T0(확정 순서 'B33 → Phase 3'). T0은 G1과 독립.
                   (확정 순서 원문의 "Phase 3(T0·G1(32)·D0a·D0b·M…)"은 card 묶음 목록이지 순서가 아니다 -- 글자 그대로 'T0·D0a·D0b → G1'을 넣으면 v6 §8.1 G1 → D0a와 순환, 부록 A F1 C2)
[UD-17 결과, Phase 순서와 독립 -- 결정이 오면 바로. (v0.6) 갈래별 간선은 §3.3 순서 근거 'UD-17']
                   UD-17d ─> #54(current_reuse Vom1·Vop1)  ┄┄(권고, 데이터 갈래만)┄┄> #23 ; UD-17d 엔진 갈래면 #23 ─> #54(권고 간선 없음) ; #54 ─> E3 성공 단위·E8(파일럿)
                   UD-17e(ii) bulk = 자기 source ─> 사용자 connectivity(`bulk` 단자) + #22(`bulk` 해석 -- 답이 #22 뒤면 #55가 엔진 몫까지) ─> #55 ─> E8 ; UD-17e(i) bulk = vdd ─> #55 없음, #27(VS 0~1.8)이 덮음 ; UD-17e ┄┄(권고)┄┄> #22
                   UD-17a ─> UD-17b, {UD-17a·b·c} ─> #53(folded -- 17a·17c 공동 게이트)  ┄┄(권고, (i-3)·(iii)만)┄┄> #23 ; UD-17c (i)·(ii)면 #6 ─> #53, (ii)면 #23 ─> #53
                   (v0.8) UD-17c (i): (i-1) supplies_v와 한 스키마 = #21 ─> #53 / (i-2) #22 고정 경로 재사용 = #22 ─> #53 -- 둘 다 권고 #53 ┄> #23 없음 ; (i-3) 따로 + #53이 먼저 경로 = #53 ─> #22(재사용)
[Phase 3]          (30-module-split) ── DoD PASS
[승인 시점, (v0.9)] Phase 3 DoD ─> 1차 질문(UD-0·UD-6·UD-1·UD-15) ─> 2차 질문(UD-4·UD-5·U-26 (a), UD-0 뒤에만)
                   UD-0 ─> 이 문서가 계약을 정하는 card 전부(#1·#45·B26pre·(v0.9.2) backfill은 자기 승인), U-26 (a) ─> #21
[Phase 4 선두, 순서 고정]
   TS4(#5) ─> CC-4a(#6) ─┬─> CC-7a(#7, equivalence) ─> CC-7b(#8, 계측·perf 도구)
                          └─> CC-8(#9, activations_out·noop 도구)        (00-common CC-8 행: "CC-4 앞부분 뒤")
   #2 ─> TS4(#5) (TS4 범위는 D-1 결정에 기댄다. (v0.9) #2는 F2 뒤 단일 경로라 §9-9의 계획 정정이 유일 경로)
[선두 뒤, 묶음끼리는 병렬 준비·순차 병합]
 실패 규약   CC-4b(#10, #25 뒤) ; DF-03(#11) ; DF-06(#12) ; DF-14+V8(#13, #9 뒤) ; DF-18(#14) ; DF-11(#15) ; DF-12(#16)
 레일        B26-2(#17, UD-1) ─> B26-3(#18)
             {#45, #1, #6, UD-18(B37a Q1~Q3)} ─> B37a(#47)          (파일 충돌 순차 병합. B26-2와 B37a는 동시 착수만 하지 않는다 -- 극성 불필요)
             {#23, CC-5(#20)} ─> MG1 + IC11 rail2(#21, nmcnr = {vdd 1.8, vss 0.0}; 대상 회로 규칙 §10.6-0 -- #54 전이면 실패 단위 검출력 실측이 착수 조건)
             {#17, #18, #21, #3, UD-7 결과 card, UD-9} ─> B26-4 lint(#19)
             {#21, #23, #17} ─> DF-24(#22) ─> nmcnr ±0.9 전환(#51)
             (#17 ─> #22 : `derive_vsb_from_nodes` 기본 인자를 둘 다 고친다)
 게이트      B36(#46, UD-15 결과 형태) ;  UD-15 (2)=X이면 {#17, #46, #19} ─> B35 grammar 확장(#49) ;  {#46, #47} ─> B37b(#52)
 노드전압    DF-02(#23, +tol_V, 충돌 노드 vsb 유도 금지, (v0.8) +normalized_margin(CC-9 앞당김), tol·max_passes 기본 인자 제거, (v0.9) reconcile/audit의 vsb `tol` 제거(비트 동일)·`node_tol` 명시 전달) ─> DF-01(#24, #22·#13 뒤; F28 M2a·M2b 실사례)
 LUT·PDK     DF-24(#22) ─> DF-27(#25) ═> U-27a(#26) ═> U-27b(#27) ─> U-30a(#28) ─> U-30b(#29)     (═> = 사이에 다른 card 병합 없이 연속, §5.6 #25)
             B24a(#30) ; DF-10+B24b(#31, #6 뒤)
 캐시        DF-07(#32) ; DF-13(#33, #6 뒤 -- U-27b와 독립) ; DF-15(#34)
 개별        DF-04(#35) ; DF-05(#36) ; DF-08+22(#37) ; DF-20(#38) ; DF-23(#39)
 배선        W-1(#40) ; W-2+D-5 함수 삭제(#41, #2 뒤) ; W-3(#42) ; (UD-7 결과) C1
 회로        I-C11 실패 명시화(#43) ─> I-C11 해소(#44, UD-6 결과) ; (위 UD-17 결과 행) #53, #54, #55
[마감]       Phase 4 DoD(§6) -- 마지막 동작 변경 card의 perf.json(파일럿 = current_reuse, #54 + (#55 또는 #27) 필요), 전후 비교표
```

순서 근거:
* 선두 5건은 N6.1·`00-common` §11.1 고정. CC-8의 선행은 `00-common` CC-8 행("DF-35·36·CC-4 앞부분 뒤") 그대로 #6이다(v0.2 도식의 CC-7b ─> CC-8은 표와 달라 고쳤다). CC-7 병합 다음 동작 변경 card부터 perf 측정, CC-8 병합 다음부터 무동작 판정이 card마다 적용된다.
* **MG1(#21)은 nmcnr 전압을 원점 이동 동등값 `{vdd: 1.8, vss: 0.0}`으로 둔다**(계획 U-26 (a) "실행 spec은 스칼라 `vdd: 1.8`로 원점 이동 동등"). 확정값 `{vdd: 0.9, vss: −0.9}` 전환은 **#22 병합 뒤 #51**이다(§5.4). (v0.4 참고) F25 S1이 보이듯 #21을 뜻대로 분류하면 음전위 선언도 비트 동일이라 #51을 #21에 합칠 수도 있다. 그래도 나눠 두는 이유: #22가 노드전압을 절대 프레임으로 옮기는 card라, 음전위 선언 회로가 그 전환의 무회귀를 #51에서 따로 보이는 편이 판정이 단순하다.
* **#21이 IC11 rail2 test를 가진다**(v0.4, v0.3 #50 흡수): 계획 N3.16 MG1 행이 "옛 키 거부 게이트 + IC11"을 한 변경 단위로 둔다. F25 S1 실측으로 #21만 병합된 엔진의 rail2는 처음부터 PASS다 -- 그러니 rail2는 #21의 분류 오류(S2)를 잡는 green 불변식이고, DF-24 red는 #22의 함수 수준 픽스처다(계획 DF-24 행의 red 형태 그대로).
* #21의 선행에 #23(`tol_V` -- IC11 허용오차의 입력)을 둔다. #22의 선행 = #21(`supplies_v`), #23, #17(`derive_vsb_from_nodes` 기본 인자를 #17도 고친다 -- 같은 함수 병합 충돌 방지).
* DF-27 → U-27 → U-30(U-27 선행 (1) = DF-27 red가 옛 표본 LUT에서 축 밖을 거부함을 먼저 확인, 기준선 승인 한 번). (v0.4) 여기에 **#22 → #25**와 **#25·#26·#27 연속 병합**을 더한다(F26: HEAD 값이 축 밖이라 #25만 병합된 상태가 길면 정본 실행 두 회로가 그동안 실패한다).
* (v0.4) **#25 → #10**: #10이 X 지점의 잡는 타입을 'LUT 정의역 오류'로 좁히는데 그 오류의 정본이 #25의 `lut_axis_out_of_range`다(검토2 S11).
* CC-5 → MG1: 옛 키 게이트 공통 형식이 먼저(DEC-69 "같은 변경 단위"). CC-5는 CC-4a 뒤.
* D-1 결정 → TS4, D-6 → DF-06·B26-4: 지울 코드를 고치지 않는다.
* #13은 #9 뒤: (v0.4 정정) 발동 계수 **측정**은 사본 계수 래퍼라 CC-8이 필요 없다(§10.1-4). 그래도 #9 뒤에 두는 이유는 #13이 발동 0 지점을 거부로 바꾸는 동작 변경 card라 CC-8의 무동작 증명(`noop_proof.py`, N6.3)으로 "library 회로에서 발동 0 → 산출물 동일"을 보여야 하기 때문이다.
* #33(DF-13)은 #6 뒤. v0.2의 #27 선행은 뺐다: 내용 지문은 새 LUT가 필요 없고, E6의 '새 해시로 지문이 바뀜' 기록은 #33이 먼저 병합돼 있어도 U-27b가 할 수 있다. 캐시 card를 22시간 재생성 뒤로 직렬화할 이유가 없다.
* W-2(#41)은 #2(표 행 삭제) 뒤. `test_ic5`는 표 행의 함수가 없을 때만 FAIL하므로(F18) 표 행을 먼저 지우고 함수는 대체(W-2)와 같은 card에서 지운다.
* **(v0.5) UD-17과 card 순서 -- 무엇이 기다리고 무엇이 기다리지 않는가**:
  * **기다리지 않는다**: #23(DF-02)·#25(DF-27)·#22(DF-24)는 결함 수정이고 red-green은 합성 픽스처다. 정본 실행 두 회로가 지금 조용히 틀린 동작점 위에 있으므로(§1.5-8), 원인 결정을 기다리며 #23·#25를 미루는 것은 조용한 실패를 연장하는 것이다(P-26·P-27). 정본 실행이 실패로 바뀌는 것은 기대 차이표 + DEC-40으로 받는다(§7.4).
  * **기다린다(하드 간선)**: #53 ← UD-17a·b·c(folded connectivity·`kcl_fold` 부호·`bias3`/출력 CM/(v0.6) 입력 CM은 사용자 몫), #54 ← UD-17d(current_reuse Vom1 결정. (v0.6) M9a/M18a(+M2a·M2b) bulk는 #55 ← UD-17e (ii)·#22 -- 아래 v0.6 항목). **Phase 4 DoD의 E3(성공 단위)·E8(파일럿 `status=ok`) ← #54**: 파일럿 = current_reuse(계획 N0.4 123행)이고 #23 뒤에는 #54 없이 끝까지 돌지 않는다(F27 충돌 0.2227 V. tol_V는 LUT 보간 오차라 이보다 작을 것으로 보지만 값은 [미확인] -- #23 판정 기록이 수로 남긴다. tol_V가 0.2227 V 이상이면 이 간선은 사라지고 그 사실을 기록한다). E1·E2는 실패 단위로도 판정이 정의돼 있어 #54를 기다리지 않는다.
  * **권고 순서(소프트 간선)**: #54 → #23, #53 → #23(둘 다 **데이터 갈래일 때만** -- (v0.7) 엔진 갈래면 하드 #23 → #53·#54가 대신하고 권고 간선은 없다. 둘을 같이 두면 순환, 부록 A F1 C3). 결정이 #23 착수 전에 오면 결과 card를 먼저 병합해 #23 이후 card(#21·#22·#24·#25~#29·#43·#51)의 E-INST·perf가 성공 단위로 남게 한다. 결정이 늦으면 #23은 그대로 가고, 그 사이 card의 E-INST는 실패 레코드 단위(§10.5)로 비교한다 -- 사후 sizing 경로의 회귀 검출력이 줄어드는 것은 판정 기록에 적는다.
  * **조건부**: #21의 IC11 rail2 -- base(= #23 뒤)에서 θ 평가가 끝나는 2레일 회로가 없으면(#54 전) 실패 단위로 판정하되, #21 작성 전 실측에서 **실패 단위 판정기가 S2·S3 합성 상태를 FAIL로 가르는지** 먼저 잰다. 가르지 못하면 #21은 #54를 기다린다(§10.6-0). #18의 current_reuse `cmrr_estimate_db` 차이표는 #18 base에서 current_reuse가 끝까지 돌 때만 보인다 -- #23 뒤·#54 전이면 실패 지점 앞이라 차이가 없고, 그 기준선 변경은 #54의 DEC-40에 합친다.
  * 결과 card가 엔진 규칙이면(UD-17c에서 'fold_group 컬럼 KVL을 엔진이 푼다'를 고르는 경우, UD-6 (B)와 같은 종류) 그 card는 #23 뒤(SEAL 경로 사용)이고 계획 개정을 동반한다.
  * **(v0.6) [pack] 반영 -- 갈래별 간선**(`p4v06_dag.py`가 갈래 조합마다 비순환을 확인, 부록 A E3. (v0.7) 확정 순서·엔진 갈래 간선을 더한 `p4v07_dag.py`, 부록 A F1):
    * **#53 ← UD-17a·b·c 전부(공동 게이트)**. UD-17a만 답이 와도 #53을 시작하지 않는다 -- 극성만 고치면 X·Y 충돌이 1.2 V로 남고(F32 F1) folded는 #23 뒤 여전히 실패라 #53의 판정(conflicts 0)이 성립하지 않는다. UD-17c 갈래: (i) 외부 DC 선언(`bias3`·출력 CM·**입력 CM**) = 선언할 필드가 지금 없어 새 스키마 필드 + 엔진 해석(공유 코드, 승인) -- (v0.9, 5차 검토 m-2) 권고 #53 → #23은 **(i-3)일 때만** 유지된다((i-1)·(i-2)는 권고 없음 -- 아래 v0.8 문장), CC-5(#20) 뒤면 새 필드가 옛 키 게이트 표에 걸리지 않게 card에서 확인. **(v0.7, S7)** 엔진 몫이 Phase 3 모듈 파일을 고치므로(P3? = Y) **하드 간선 #6 → #53**(Phase 4 선두 뒤), 그리고 `propagate_node_voltages` 계열 충돌 집합(§3.4)에 든다 **(v0.8, 4차 검토 S3) (i)의 노드 고정 값 -- 스키마와 읽기 경로를 각각 하나로, 그에 따른 간선**: (i-1) 고정 전위 선언을 `supplies_v`와 **한 스키마**로 두면 하드 #21 → #53(스키마를 #21이 만든다) (i-2) 엔진 읽기 경로로 #22가 만든 레일 고정 경로를 **재사용**하면 하드 #22 → #53 -- (i-1)·(i-2)에서는 **권고 #53 → #23이 없다**(#21·#22가 #23 뒤라 같이 두면 순환, 부록 A G1 C5·C6) (i-3) 따로 두고 #53이 #22보다 먼저 읽기 경로를 만들면 권고 #53 → #23을 유지하고 하드 #53 → #22를 두며 #22 계약에 '그 경로를 재사용(레일 고정 전위를 같은 경로로 넣음)'을 적는다(G1 S2a). 읽기 경로는 **먼저 병합되는 card가 만들고 다른 card가 재사용**한다 -- 둘 다 만들면 경로가 둘이 되고 간선도 순환한다(G1 C7). 어느 형태인지는 #53 card가 UD-17c 답 시점의 #21·#22 병합 상태로 정한다(#22가 이미 병합됐으면 (i-2)). (ii) 엔진 컬럼 KVL 규칙 = #6 → #53, #23 → #53(권고 간선 없음) (iii) 두고 멈춤 = #53은 UD-17a·b 데이터 정정 + 주석 3곳(F35)만이고 folded는 #23 뒤 실패로 남는다(그 사실을 #53 판정 기록과 §9-17 입력으로).
    * **#54 ← UD-17d**(bulk와 분리). 데이터 갈래면 권고 #54 → #23·#21 유지(#54는 #22를 기다리지 않는다). **(v0.7, S3) 엔진 규칙 갈래**('교차 그룹 노드 구속')면 **#23 → #54(하드), 권고 #54 → #23·#21은 없다**(#53 (ii)와 같은 형태 -- 둘을 같이 두면 순환, 부록 A F1 C3/S5). 그때 E3·E8은 #23 뒤 #54까지 실패 단위로 남고, 그 기간 #21에는 위 '조건부'(실패 단위 판정기의 S2·S3 검출력 실측이 착수 조건)가 적용된다. UD-17d (i)이면 #54는 메타데이터(컬럼 분할) **+ 설계 변경**(아래 세 소자 VDS 배분 또는 출력단 VGS -- 스펙/compensation 몫, 사용자)이 함께여야 M5 VDS가 의미 있는 값이 된다(F33 -- 포화 판정 자체는 6b, #54는 값을 기록). 설계 변경 없이 (i)만이면 #54 병합본에서도 current_reuse가 끝까지 돌지 않을 수 있고([미측정]) E3·E8은 §9-17 경로다.
    * **#55 ← UD-17e (ii)**: 사용자 connectivity(`bulk` 단자) + **#22**(DEC-61 `bulk` 해석 -- 하드 간선 #22 → #55). #22는 #23 뒤이므로 #55에는 권고 → #23 간선이 없다(있으면 #55 → #23 → #22 → #55 순환 -- v0.5의 단일 #54에 bulk를 두면 생기던 순환을 나눠서 없앴다). UD-17e (i)이면 #55 없음 -- M9a·M18a 0.825(와 UD-17d (i)일 때 M2a·M2b 0.9227)는 #27의 VS 0~1.8 V가 덮는다. **(v0.7, S4) UD-17e 답과 #22 병합의 선후**: #22는 UD-17e를 기다리지 않는다(§3.3 '기다리지 않는다'). 원칙 기본안: (a) UD-17e 답이 #22 착수 전에 오면 #22가 답대로 한다((ii) = 스키마 수용 + 선언 bulk 읽기, (i) = `bulk` 키 거부). 그래서 **UD-17e → #22는 권고 간선**이다(부록 A F1 S6 비순환) (b) 답이 #22 병합 **뒤**에 오고 (ii)이면 #22는 이미 '`bulk` 키 거부'만 넣은 상태라, **#55가 엔진 몫(거부 해제 + `derive_vsb_from_nodes`의 선언 bulk 읽기)을 함께 맡는다** -- 그때 #55는 데이터 + 엔진 card(P3? = Y, 선행 #22·#6, 공유 코드 승인 §7.3). 어느 경우든 엔진 몫과 첫 소비자(current_reuse 데이터)가 같은 card 사슬에 있다(만들면 배선). **E8 ← #54 + (#55 또는 #27)**: #25 병합 뒤 #27 전에는 축 밖으로 실패하므로 #25·#26·#27 연속 병합(P-24)이 E8 경로를 지킨다.

### 3.4 파일 충돌 집합(준비는 병렬, 병합은 순차)

[Phase 3 뒤 모듈 이름은 D0b 확정 전. 아래는 Phase 3 v3 A-3 반영]
* 평가 커널 빌더(`_build_theta_evaluator`/`_evaluate`, MOD6): DF-03·DF-01·DF-02·DF-14·CC-7a·B26-2(8003행 `_rail_nets`)·W-1.
* **MOD8(`optimize_full_circuit_budget`의 Phase 3 위치)**: CC-7a(추출 원천), DF-18(θ* 기록), U-30a(9273 `min_finger_w`), DF-20.
* MNA(MOD5): B26-3.
* **로드 경로(`load_topology`, MOD3)**: B26-1·B34·B26-2·B37(`propose_device_roles_gap_fill` 포함).
* 옛 키·spec 로드(MOD2): CC-5·MG1.
* LUT(MOD1): DF-07·DF-13·DF-27·B24a·DF-10·DF-02(tol_V)·U-30a(공정 기록 로더).
* 하네스(`workspaces/run_harness.py`): CC-4a·CC-7b·CC-8·DF-18·MG1·U-30a·DF-20·#51.
* `_hr_resolve_vertical_group`·`_hr_verify_group_kvl_sum`(평가 경로): DF-14·DF-01·MG1(7068·7222~7450 스칼라 `vdd`)·#43.
* (v0.4) 부록 C.1의 X 핸들러 15곳: #10(잡는 타입을 좁힘)·#25(`lut_axis_out_of_range`가 이 핸들러들을 지나간다 -- 순서 #25 → #10). (v0.7) 두 card의 X 핸들러 동작은 P-34 한 규칙이다(§7.2).
* (v0.4) `propagate_node_voltages`·`derive_vsb_from_nodes`·`reconcile_vsb_from_nodes`·(v0.9) `audit_vsb_consistency`: #17(기본 인자)·#21(인자 값의 뜻 분류)·#22(절대 프레임·DEC-61 식)·#23(conflicts 소비, (v0.5) 충돌 노드로 vsb 유도 금지 -- P-27, (v0.8) `tol`·`max_passes` 기본 인자 제거 -- S6, (v0.9) 두 vsb 함수의 `tol` 제거·`node_tol` 전달 -- N-S2)·**(v0.7) #53(UD-17c (i) 선언 고정 노드 읽기·(ii) 컬럼 KVL 규칙)**·**#55(UD-17e (ii) 답이 #22 뒤일 때 선언 bulk 읽기)**.
* (v0.5) fold_group singleton 우회(SR 7507~7563, `_hr_*` 경로): #53이 엔진 규칙 갈래를 고르면 그 card, 그 밖에 #14·#43과 같은 평가 경로.
* (v0.5) library topology 데이터(`folded_cascode.topology.json`·`current_reuse_telescopic_ota.topology.json`): #53·#54·(v0.6) #55(사용자 connectivity 수정 + Claude 메타데이터, WP-07·U-16 -- #53은 F35 주석 3곳 정정 포함), B47(추적 md 재생성), B29(current_reuse 주석 -- 보류). 같은 파일이라 순차 커밋. 사용자 정정은 대기열에 모았다가 "한꺼번에 반영해" 지시로 한 번에 반영하고 넷 표를 다시 뽑는다(메모리 규칙 -- [pack] §0).
* (v0.6) MOD3(`circuit_state_graph.py`): W-1(#40, `validate_theta_declaration_order` -- Phase 3 v6), 로드 경로 card(#1·#45·#17·#47), D-19 (나)면 `rail_declaration`.
* (v0.4, 이 Phase 밖이지만 V3·V7 판정을 바꿈) `tools/gates/mutate_changed.py`: 면제 묶기·범위 정책(#48)·G1. `tools/gates/reachability.py`: B33·G1(§3.2 순서).

### 3.5 한 card로 묶는 것(원칙)

| 묶음 | 근거 |
|---|---|
| DF-08 + DF-22 | 같은 함수, 계획 비고 |
| DF-14 + V8 계측 지점 | 계획 비고 "V8 계측 대상" |
| MG1 이름 변경 + 옛 키 거부 행 | DEC-69 "같은 변경 단위" |
| DF-02 + tol_V 함수 | N9.1 "tol_V 함수 선도입" + 만들면 배선(소비자 = DF-02 conflicts 판정) |
| MG1 + IC11 rail2 test(v0.4) | 계획 N3.16 MG1 행 "옛 키 거부 게이트 + IC11". F25 S1: #21만 병합된 엔진에서 rail2가 PASS -- 그래서 rail2의 첫 집은 #21이고, #22(DF-24)는 계획 DF-24 행의 함수 수준 픽스처가 red다. v0.3의 '#50 xfail strict → #22 해제' 묶음은 폐기 |
| DF-24의 두 몫(레일 절대 전위 고정 + DEC-61 vsb 식) | 나누면 그 사이 병합본이 F25 S3 상태(nmos vsb −0.9 V 오차)다 |
| DF-10 + B24 (b) | 같은 뿌리 후보 [prep, 뿌리 동일은 [미확인]] |
| W-2 + D-5 **함수** 삭제 | vsid 감사의 유효 1건(`cmfb_tail`)을 W-2 배선이 대체 -- 대체와 삭제를 한 card에 [prep]. D-5 **표 행**은 #2(F18) |
| U-30 + DF-34 Phase 4 몫 + 엔진 폴백 15곳 | 개념 하나에 저장 위치 하나(DEC-68) |
| B26-2 + probe rail-set 교체 | `tests/probe_physical_consistency.py` 40행 `RAIL_HI, RAIL_LO = {"vdd","VDD"}, {"gnd","GND","vss","VSS"}`, 49행 `{"vdd": VDD, "gnd": 0.0}`, 126행 극성 판정 [재측정 v0.3] -- 극성이 필요하므로 #17의 test 커밋(test-author 경로)에서 `supply_nets` + #17 극성 읽기로 교체 |

---

## 4. 원칙을 계약으로 (모든 card의 spec card '관찰 가능한 계약'에 전 범위로 넣는다)

### 4.1 topology 무관 (DEC-62, 사용자 원칙 2026-09-30)

* 새 함수와 고치는 사이트에 **소자·넷·회로 이름 리터럴과 topology 경로가 없다**. 판정은 선언(`supply_nets`, `supplies_v`, `ports`의 `role`, `bulk`, metric 선언)과 구조 술어에서만 읽는다.
* 판정기: card마다 (a) **합성 topology**(선례 `test_d_delete_telescopic.py` `_SYN_RAILS = ["rail_hi","rail_lo"]`)에서 기대값이 나오고 (b) **역방향**: 선언에 없는 넷이 `vdd`·`gnd` 같은 이름이어도 레일로 취급하지 않는다.
* 변환 불변: 레일 이름 바꾸기·원점 이동(IC11) -- 되돌리면 같다(허용오차는 §10.6).
* **코드가 정하는 개수 상한 금지**: 레일 수·극성별 레일 수에 코드 상한을 두지 않는다(같은 극성 레일이 여럿인 회로 -- 예: 레벨 시프터 -- 도 데이터만으로 들어와야 한다, DEC-62). 상한이 생기는 방식은 사용자 결정(UD-15)으로만 채택하고, 채택하면 DEC-62 예외와 그 해소 card를 계약에 적는다.
* 전 범위 강제: B26-4 lint(§5.4 #19, PT 계약 test로 상시 실행), DF-23 Phase 4 행.
* 무동작 증명: 기능이 필요 없는 library 회로에서 발동 계수 0·산출물 동일(`00-common` §11, CC-8 뒤).

### 4.2 조용한 폴백 금지

* 선언이 없으면 거부한다: CC-4a 전에는 `ValueError`(메시지에 선언 이름과 DEC 번호), CC-4a 뒤 로드 거부는 `SchemaRejectedError`(exit 7), 탐색 중 실패는 N3.14 클래스.
* **기본값 없는 인자**: 레일·PDK·전압 인자를 이름 집합·리터럴 기본값이나 `None`→기본값으로 두지 않는다.
* 광범위 except는 N3.14 클래스와 `SchemaRejectedError`를 다시 raise한다(DF-37). 탐색 루프는 `CANDIDATE_FAILURE_CLASSES`만 이름으로 잡는다.
* 남기는 폴백은 전부 `fallback_events`에 기록한다(V8, 스키마·지점·처리 규칙은 §10.1). 정본 실행에서 0이어야 한다.
* 게이트는 **'실제로 거부한다'를 먼저** 보인다(조용한 통과 합성 구현에서 test FAIL).
* 클램프 금지: LUT 축 밖 입력은 `lut_axis_out_of_range`(SEAL_VIOLATION)로(DF-27).
* (v0.5) **조용한 선택 금지**: 같은 노드에 두 경로가 다른 값을 줄 때 이름순 첫 경로를 고르고 그 값으로 다음 단계(vsb 유도·LUT 조회)를 계속하지 않는다(P-27, F27). 충돌 검사는 노드전압의 첫 소비자보다 앞에 둔다.
* (v0.5) **원인을 바꿔 보고하지 않는다**: 고유 클래스 오류(`lut_axis_out_of_range` 등)를 후보 배제가 '후보 없음' 같은 다른 사유로 바꿔 올리지 않는다(P-28, F29).
* (v0.5) **데이터 밖을 지어내지 않는다**: LUT 축 밖은 외삽하지 않는다. 축 연장은 실측 재생성(U-27)으로만 한다(P-29, F30).

### 4.3 만들면 배선

새 함수는 **만든 card에서** 운영 호출부가 부르고, 원래 문제가 있던 경로를 대체한다. 대체할 수 없으면 만들지 않고 사용자 승인을 구한다.

| 새 것 | 만드는 card | 같은 card의 소비자(대체하는 것) |
|---|---|---|
| `rail_declaration`·`RailDeclaration` | #1 | `load_topology` → 집합 판정 사이트 전부 |
| 극성 필드(hi/lo/mid, §10.3) | #17 | `trace_*`·`propagate_node_voltages`·`_metric_supply_current` 등, `probe_physical_consistency.py` 레일 집합(test 커밋) |
| (UD-15 (2)=X) analog-grammar `rails` 인자 | #49 | SD 운영 8함수의 AG 호출(`netclass.RAILS*` 이름 판정). (UD-15 (2)=Y이면 #17 안의 SD 호출부 어댑터가 같은 자리를 대체) |
| analog-grammar 명시적 의존 오류 | #45(phase 3 card -- (v0.9.2), 인용) | `_import_analog_grammar`의 `ImportError` 삼킴 + 작은 def 3개(`find_idiom_matches`·`find_stack_edges`·`audit_theta_root_direction`)의 부재 분기. 나머지 부재 분기는 도달 불가가 되고 삭제는 인계(#1: 9·10b·13 / B35: 5~8·10·14 / 백로그 B39 -- 부록 C.3) |
| role 기반 포트 접근자(B37a) | #47 | 운영 진입점 **E1**(`load_topology` → `propose_device_roles_gap_fill`)·**E2**(`propose_vertical_stack_id_gap_fill`, 지금 `inputs` 없음 = 기능 꺼짐)·**E3**(SR `resolve_stack_layout` 6572 경로 3) 전부 + SR `input_referred_offset_pairs`(4511~4519)의 `direction` 읽기 교체(`prep_b37_ports.md` §1.3·§4.2 C2·C4) |
| AG 라이브러리 이름 힌트 제거(B37b) | #52(조건부) | AG `classify_nets` 1c·1e의 `HINT_*`(NC 39~43) → `analyze.py` CLI 경계의 명시 가정(`assume` 보고) |
| N3.14 예외·`FAILURE_CLASSES`·`exit_code_for`·`FailureRecord` | #6 | 하네스 `run()` 종료 코드(모든 예외를 삼키고 exit 0, F15) |
| `LEGACY_NAMES`·`load_json_checked`·`reject_legacy_names` | #20 | 엔진의 파일 읽기 `json.load` 9곳(F19), `validate_no_legacy_vs_key`(삭제) |
| `rail_voltages(spec, rails)`(§10.4) | #21 | 스칼라 `spec["vdd"]` 읽기 20줄(F4) |
| IC11 rail2 test 본문 + 감도 전파 허용오차 helper(test 쪽, §10.6) | **#21의 test 커밋**(v0.3 #50 흡수) | `test_ic11.py` `rail2`의 `pytest.fail()` 한 줄(F13). helper의 소비자 = 같은 card의 `rail2` test(만들면 배선) |
| θ 탐색 함수(추출), `instrument`, `measure_search_perf.py` | #7·#8 | `optimize_full_circuit_budget` 인라인 탐색, N6.3 보고 |
| `activations_out`, `noop_proof.py` | #9 | N6.3 무동작 증명(#13의 '발동 0 → 거부' 지점 포함). (v0.4) §10.1-4 발동 계수 측정은 이 도구가 아니라 사본 계수 래퍼다 |
| `tol_V` 함수(MOD1) | #23 | `propagate_node_voltages` conflicts 판정(지금 미소비) -- (v0.8) 근거 없는 기본 인자 `tol=1e-6`을 대체, (v0.9) `reconcile_vsb_from_nodes`·`audit_vsb_consistency`도 같은 `node_tol`을 명시 전달(F36, P-36). #21의 IC11 허용오차가 두 번째 소비자 |
| (v0.8) `normalized_margin(magnitude, tol)`(CC-9, `00-common` §7.2 시그니처 그대로, MOD2) | **#23**(Phase 5에서 앞당김 -- S2) | #23 노드 충돌 `SealViolationError` 레코드의 margin(분모 tol_V -- 계획 749행). 같은 Phase의 #43·#25 레코드도 이 함수를 `tol=None`으로 불러 `null`을 얻는다(margin을 쓰는 곳은 이 함수 하나). Phase 5 실패 캐시 정렬(N3.5)은 다음 소비자 |
| 공정 기록 로더(PDK 상수, §10.2) | #28 | 하네스 4벌·엔진 폴백 15곳, 죽은 키 `L_min`은 `layout_grid_L_candidates(L_min=)`에 배선 |
| VGS 기준 gm·gds 공개 조회 | #30 | `gain_ranking`의 `lut._query` 직접 조회 → 면제 `20260929-p4-scan-exempt` 해제. (v0.9.2) + design 20 §10 E2의 '현재 승인 … 1건' 문구 정정(승인 `20261001-p2dod-e2-wording` 재검토 절 -- 같은 card) |
| `record_fallback`·`FallbackEvent`(§10.1) | #13 | 부록 C의 `I` 지점 + #13 발동 규칙으로 계측으로 남는 지점. 하네스 산출물 `fallback_events` 키(E1) |
| 레일 리터럴 lint 도구 + PT 계약 test | #19 | DF-19 위치 열(lint 산출로 대체), **모든 병합본 V1에서 PT로 상시 실행**(§5.4 #19), DoD E10 |
| V3 '바뀐 문장' 대상 선택(A1-b = 선택지 2) | #48 = 게이트 card `20260930-v3-changed-stmt-scope`(인용, 이 Phase 밖) | `mutate_changed.py` 대상 선택. 소비자 정의는 그 card |

* **`tol_I`는 Phase 4에서 만들지 않는다**(P-3): Phase 4 안에 엔진 소비자가 없다. P3c 재착수는 6b(§1.4, §9-8).
* **`derived_spec` 재사용**(검토 M6, 검토2 M2 정정): 변형 spec이 필요한 card(#21·#22의 원점 이동, #29의 U-30 전후, #51)는 새 변형 도구를 만들지 않고 하네스 `derived_spec(circuit, why, **overrides)`(F24)를 쓴다. **6a 면제 기록(`20260930-restore-unwired-until-6a`)은 그대로 남는다**: 그 기록의 재검토 절은 "spec 변형이 필요한 첫 **운영** 사용처"에서 배선한다고 적었고, #21의 IC11 test·#29의 auditor 비교는 운영 사용처가 아니다(B33 R3도 test 경유 도달을 세지 않는다). v0.3의 "Phase 4 안에서 소비된다"는 틀린 주장이라 지웠다.

### 4.4 캐싱 (NFR-2, N3.3)

* **새 캐시를 만들지 않는다.** 이미 있는 엔트리에 싣는다(B26-1: `_load_full_topology_cached`의 `meta["rails"]`).
* 고치는 캐시는 **상한 + LRU**(DF-07), 키는 **계산이 실제로 읽는 가변 상태의 내용 지문**(DF-13). **DF-13 지문은 LUT 로드 때 한 번 계산해 LUT 객체에 보관**한다(호출마다 계산 금지). 근거 하나 원칙에 따라 지문 = LUT 파일의 sha256(U-27b가 npz 메타·판정 기록에 남기는 값과 같은 값)이다. 메모리에서 만든 합성 LUT(test)는 배열 바이트의 sha256을 생성 시점에 한 번 계산한다.
* 새 선언 읽기(공정 기록, `supplies_v`)는 **실행당 한 번** 읽고 캐시한다. 유도값(`W_bounds` 하한 = `min_finger_w`, `rail_voltages`)은 함수 하나로 계산하고 결과를 보관한다.
* `fallback_events`는 평가 루프 안에서 발생할 수 있으므로 **(site, kind, device) 키로 집계**하고 첫 발생 detail과 계수만 남긴다(§10.1-1). 크기 상한 = 서로 다른 (site, kind, device) 수이고 θ 평가 수와 무관하다.
* 측정은 계측으로: CC-7 뒤 card마다 `perf.json`, 캐시 card는 적중·미적중 계수와 같은 입력 해시 재계산 수.
* 이미 있는 결함을 키우지 않는다: 경로 문자열 캐시 키(S0 지문 = 6a)는 재사용만 한다.

### 4.5 작성자 ≠ 검증자

모든 card의 red·기대값·픽스처는 test-author(interface card만), 구현은 code-author, 전후 비교표·perf·E-LIB·E-INST 수치는 auditor 판정 기록에서만 인용한다. 기존 test 기대값이 병합본과 다르면 test-author는 고치지 않고 dispute를 쓴다. 기준 약화·기준선 변경은 DEC-40 승인 없이 병합하지 않는다. **게이트 판정 범위를 바꾸는 일(V3 범위)은 오케스트레이터 선택이 아니다. 판정 범위 축소는 게이트 변경이어도 기준 약화이므로 사용자가 고른다(A1, §7.1) -- 2026-10-01 A1-b로 선택지 2가 결정돼 게이트 card `20260930-v3-changed-stmt-scope`와 승인 기록(`target_kind: diff`, 범위 설명에 "판정 기준 적용 범위 축소(약화) 승인" 명시)으로 간다.** 면제 묶기 card(강화)도 게이트 판정 기준 변경이라 승인 기록 한 건이 필요하다.

---

## 5. card 표

열: 판정 = 판정 유형(N3.12.3), oracle 종류 (a) 구성 (b) 독립 방법·문헌 (c) 동작 보존(base 결과) (d) 계획·원자료. `P3?` = Phase 3 모듈 파일 필요(Y) / Phase 3 전 가능(pre -- (v0.8) 엔진 파일을 바꾸는 card는 Phase 3 v7 D-27에 따라 D0b 병합 전에만. (v0.9) 이 문서에서 pre는 확정 순서의 #1과 인용 #45뿐이다 -- 승인 질문이 Phase 4 착수 때라 UD-0·UD-1·UD-15를 선행으로 갖는 card는 pre가 될 수 없다, §3.1 항목 7) / 무관(-). DoD = §6 ID.

### 5.1 Phase 3 전 후보

| # | id(초안) | 대상 | 판정 | oracle | 선행 | P3? | DoD |
|---|---|---|---|---|---|---|---|
| 1 | `20260930-b26-rail-accessor-set`(phase 3 -- (v0.9.2) Q-B34-PHASE) | DF-19·26 넷 몫 1(접근자 + 집합 판정 사이트 11함수) + **B34 인계 사이트**(아래 표 -- (v0.6) `refine_differential_and_mirror_relations` 사이트 9·10b, `propose_device_roles_gap_fill` 사이트 13과 3966~3970 `unavailable_reason` 키(B40): 이 card가 두 def 본문을 어차피 바꾸므로 **문장 하나짜리** 도달 불가 분기 삭제를 함께 한다. 사이트 10·14(블록 내어쓰기)는 B26-1 v4에서 **B35로** 넘어갔다 -- 블록 전체가 N2 대상이 되고 그 블록 값(netclass·idioms 유래)은 이 card의 계약이 아니라서. B40은 analog-grammar가 **있어도** gate 소자 없는 입력에 틀린 사유를 싣는 문제) | red-green | (a) 합성 레일 이름 topology. 역방향은 B26-1 사이트만으로 정해지는 값에 한정(검토 B2). (b) 이름 바꾸기 setup 불변. (c) E-LIB 9/9·E-INST -- **(v0.9.3, m1)** `meta["rails"]`는 이 card가 처음 더하므로 해시에서 빼고(card 계약 8) 계약값과 **값 전체 정확 일치**로 따로 판정한다: 병합본 `masked.rails` == `{"__dc__": "RailDeclaration", "nets": <card base library의 그 회로 `supply_nets` 정렬 집합>}`(card 계약 1 -- 계약 밖 필드 0, Phase 3 v8.3 E5 (iv)와 같은 식), base `<ABSENT>`. 그 밖 meta·`transistors`·`run_topology_pipeline` 반환·E-INST는 해시 같음 | (v0.7) **Phase 2 DoD**(확정 순서 -- #1은 DoD 밖), 계획 정정(✓ `8356c1e`), P9(✓), **A2 기록**(✓ `2d58fd8`), **면제 묶기 → #48 → #45**(확정 순서 34 → 35 → B34), **B26pre 병합**(v0.6 U3 대체), **(v0.9.2) backfill 결함 card 병합**(U-BF 결정 = 고침. U2-a는 소멸 -- N2d를 쓰지 않음), **U4**(✓ 기록 `20260930-b26-b40-reason-key`), **U5**(✓ 기록 `20261001-b26-p9-signature-update`), (v0.9.2) U3(✓ -- 면제 기록 `20261001-b26-v3-equiv-range`는 (v0.9.3, R1) 1차 시도 K1 뒤·2차 시도 착수 전, card '두 번 시도 절차' 2), 머리 approval `20261001-b26-phase3-cards`. 뒤: B33(하드, 확정 순서) | pre | E0·E10(부분) |
| 45 | `20260930-b34-grammar-explicit`(phase 3 -- (v0.9.2), **인용**) | B34 최신 card 범위: 4 def(`_import_analog_grammar` 재raise, `find_idiom_matches`·`find_stack_edges`·`audit_theta_root_direction`의 부재 분기 삭제) + docstring·주석 전부(SR `resolve_stack_layout` 6509~6512 포함, AST 해시 불변). 계약·V3 계획은 card 그대로(재서술하지 않음) | red-green | card '관찰 가능한 계약' 1~8 | A2 기록, (v0.7) **35(범위 정책) 병합**(확정 순서 Phase 2 DoD → 34 → 35 → B34). **병합 선행: 사용자 `install.py` 작업**(F23). 뒤: B26pre → (v0.9.2) backfill → #1 | pre | E0·E1 |

**B34 인계 사이트(최신 B34 card '의도' 3, 부록 C.3)** -- 사이트 번호는 B34 card 표:

| 사이트 | 함수 | 담당 | 조건 |
|---|---|---|---|
| 1·2·3·11·11b | `_import_analog_grammar`, `find_idiom_matches`, `find_stack_edges`, `audit_theta_root_direction` | **#45** | -- |
| 9·10b·13, 3966~3970 | `refine_differential_and_mirror_relations`, `propose_device_roles_gap_fill` | **#1** | B26-1 card '의도' 표·계약 13·14(`unavailable_reason` 키 삭제로 B40 해소, 분기 자체는 gate 소자 없는 입력 때문에 남김). (v0.6) B40은 A2 기록 범위 밖이라 U4 추가 승인이 필요하다(안 받으면 B40은 백로그로) |
| 5~8, **(v0.6) 10·14** | `suggest_vertical_stack_composites`, `find_verified_differential_and_mirror_relations`, `_propose_vertical_stack_ids`, `_propose_headroom_roles`, (v0.6) `refine_differential_and_mirror_relations` 사이트 10(`if _netclass_al is not None:` + 블록 2496~2523), `propose_device_roles_gap_fill` 사이트 14(`if _idioms_lcmf is not None:`·`else:` + 블록 4087~4111) | **B35** = UD-15 (2)=X이면 **#49**, (2)=Y이면 **#17**(어댑터 card가 같은 운영 함수의 AG 호출부를 바꾼다) | UD-15 (2). (v0.6) 10·14는 B34 최종판·B26-1 v4가 B26-1 → B35로 옮겼다(`b34_revision_log.md` §7). 그 card의 V3: 내어쓴 블록 부분 트리 전체가 N2 대상(T1)이고 기존 test가 못 죽이는 변이가 13 + 1(review2 E2·E2b) -- 블록이 만드는 값(`active_load_leg_candidates`·`signal_referenced_mirror_legs`·`branch_load_partner_candidates`, `cascoded_active_load_legs`)을 판정하는 계약이 B35 card에 있어야 한다 |
| 4, 12, 3533~3535 | `find_differential_and_mirror_forks`, `propose_theta_kcl_gap_fill` | **백로그 B39**(이 Phase 범위 밖 -- 사이트 4는 등가 변이 면제 승인이 필요, 12는 비운영·기존 생존 추정 약 48) | -- |
| 2 | `d4-delete-unwired` | 보류 D-1(`estimate_area_budget` → DF-09 닫힘)·D-2·D-3·D-4 함수 삭제 + **`test_ic5` `_DOMAIN_TABLE` D-4·D-5 두 행 삭제와 `len == 21` → 19**(V5 1회) | equivalence | (c) E-LIB·E-INST, (a) NEW-TOPO | UD-0, DEC-40 V5 승인 | Y(F2 뒤 단일 경로 -- (v0.9) 앞당김 없음, §3.1 항목 7) | E0 |
| 3 | `pole-oracle-to-tests` | D-6 → test oracle | equivalence | (c) 승격 test 판정 불변 | UD-0 | Y(F2 뒤 단일 경로 -- (v0.9) 앞당김 없음) | E0 |
| 4 | `toy-lut-to-tests` | D-7 → tests 픽스처 | test-only | (c) E-AST | UD-0 | Y(F2 뒤 단일 경로 -- `A/*.py`의 D-7 정의 이동, (v0.9) 앞당김 없음) | -- |

### 5.2 선두(순서 고정)

| # | id | 대상 | 판정 | oracle | 선행 | P3? | DoD |
|---|---|---|---|---|---|---|---|
| 5 | `ts4-selfref-oracle` | TS4 | red-green | (a)·(b) | #2(D-1 결정) -- D-1 삭제면 대상 = V4 lint 산출 목록 **[미확인: 그 산출이 0이면 TS4는 계획 정정으로 닫는다]** | Y | E0 |
| 6 | `cc4a-failure-classes` | CC-4 앞부분, 하네스 `run()` exit code(DF-18 exit 몫·DF-37 하네스 몫 -- 하네스 except 3곳 476·512·528, F15에서 4회로 모두 exit 0) | red-green | (a) 합성 raise → exit code, (d) 계획 N3.14 | #5 | Y | E0·E11 |
| 7 | `cc7a-search-extract` | θ 탐색부를 MOD8의 `optimize_full_circuit_budget`에서 추출해 MOD6으로 | equivalence | (c) E-INST·E-LIB | #6 | Y | E8 |
| 8 | `cc7b-perf-instrument` | `instrument`·`ContextVar`·`measure_search_perf.py` | red-green | (a) worktree 밖 경로 → exit 8, 실패 입력 → `status=failed` | #7 | Y | E8 |
| 9 | `cc8-noop-activations` | `activations_out`·`noop_proof.py` | red-green | (a) 발동 1건 → exit 9 등 | **#6**(`00-common` CC-8 행) | Y | E9 |

### 5.3 실패 규약(CC-4a 뒤)

| # | id | 대상 | 판정 | oracle | 선행 | P3? | DoD |
|---|---|---|---|---|---|---|---|
| 10 | `cc4b-df37-broad-except` | DF-37 광범위 except 재raise + 부록 C.1의 `F`(탐색 후보 실패 14곳)를 `CANDIDATE_FAILURE_CLASSES` 이름으로, `X`(후보점 배제 15곳)의 잡는 타입을 LUT 정의역 오류로 좁힘. **'LUT 정의역 오류'의 정본 = #25가 만드는 `lut_axis_out_of_range`(SEAL_VIOLATION, 계획 LR3·DF-27)와 HEAD에 이미 있는 LUT 역산 실패(`vgs_for_gm_id` 등이 내는 `ValueError` -- 클래스·발생 지점 목록은 card 작성 전 실측)**. 그래서 #25 뒤에 한다(검토2 S11). **(v0.7, S2) X 핸들러 동작은 P-34 규칙 그대로 유지한다**(#25가 만든 것을 되돌리지 않는다): 잡는 타입 = MOD1 정의역 오류(§10.7)와 HEAD LUT 역산 실패, 후보 하나 배제 + 배제 사유를 클래스와 함께 모음, 모든 후보가 축 밖으로 배제되면 집계 지점이 `SealViolationError`(`lut_axis_out_of_range`)를 올림 | red-green | (a) N3.14 예외를 던지는 합성 입력이 삼켜지지 않음, MOD1 정의역 오류가 X 지점에서 **후보 하나만** 배제하고 그 사유가 모이며(**모든 후보가 축 밖이면 `lut_axis_out_of_range` 실패 레코드 -- '후보 없음' 아님**, #25 계약 유지), 다른 `ValueError`(예: KVL 불일치)는 삼켜지지 않음 | #6, **#25** | Y | E0 |
| 11 | `df03-gate-failure-class` | DF-03 | red-green | (a) 위반 픽스처 → 탐색 계속·실패 기록 | #6 | Y | E0 |
| 12 | `df06-field-source-except` | DF-06(D-6 뒤 사이트 3, 부록 C.1 SR 4054 포함) | red-green | (a) 원천 없는 필드 → 구조화 실패 | #3, #6 | Y | E0 |
| 13 | `df14-v8-fallback-events` | DF-14 `except Exception` 5지점(부록 C.1 `R #13 (DF-14)`) 제거 + **V8 `fallback_events`(§10.1 스키마·기록 함수·하네스 산출 키) + 부록 C의 `I` 5지점 계측 + §10.1-4 발동 규칙 적용**(발동 0 → 거부, 발동 > 0 → 계측·원인 card 지정) + SR 5809 방어 폴백(DEC-76) | red-green | (a) 호출 실패 합성 → 실패 클래스, 폴백 발동 → `fallback_events` 1건(같은 site 반복 → 계수만 증가), 조용한 기본값 합성 구현에서 test FAIL. (c) **(v0.8, S7) 산출물에서 바뀌는 것은 `instance.json` 최상위 키 `fallback_events` 하나뿐**((v0.9, 5차 검토 m-5) 값은 #13 병합 시점의 계측 발동 목록이다 -- §10.1-4에서 '발동 > 0 → 계측·원인 card 지정'으로 남은 지점이 정본 실행에서 발동하면 비지 않는다. **빈 목록은 E1(DoD) 조건**이지 #13의 조건이 아니다): 그 키를 뺀 정규화 해시가 base와 같음. (v0.9) SR 7297·7451의 `except Exception` 제거는 #23의 `node_tol` 호출부(7294·7449)를 감싼 핸들러다 -- #13이 #23보다 먼저 병합되면 그 호출의 `TypeError`가 드러나고, 늦으면 #23의 호출부 AST 단언이 그 몫을 한다(F36). 키 추가로 4회로 E-INST 기대 해시와 Phase 3 D-25 M10 진입점 test 기대 해시가 바뀐다 -- 기대 차이표 + DEC-40(§7.4) | #6, **#9** | Y | E0·E1 |
| 14 | `df18-theta-star-record` | DF-18 나머지: θ* 기록. **(v0.8, S7) 기록 위치 = #6의 실행 기록 JSON(`instance.json` 밖)**, 키 `theta_star`. #6은 실패 실행에 그 파일을 쓰고, #14가 성공 실행에도 같은 파일을 쓰게 한다(파일 하나, 결과 종류 키로 구분). `instance.json`에 넣지 않는 이유: θ*는 탐색 결과이고 `instance.json`은 사이징 인스턴스라, 넣으면 E-INST·D-25 기대 해시가 이 card에서 한 번 더 바뀐다 | red-green | (a) 성공·실패 실행 모두 실행 기록 JSON에 `theta_star`(성공 = θ* 값, 실패 = `null` + 실패 클래스), base는 θ*를 출력만 함(red). (c) `instance.json` 정규화 해시가 base와 같음(4회로) | #6 | Y | E0 |
| 15 | `df11-stacked-diode-lut-fail` | DF-11 `idu_up = 1.0` 제거(SR 3538~3539) | red-green | (a) LUT 실패 주입 → 실패 클래스 | #6 | Y | E0 |
| 16 | `df12-offset-missing-gm` | DF-12 | red-green | (a) 손계산 오프셋 | #6 | Y | E0 |

#13 크기: 부록 C 기준 계측 후보는 `I` 5지점 + 발동 규칙 대상(부록 C.2 스칼라 기본값 중 담당 card가 없는 약 62곳(vsb `.get` 31 포함) + 조건식 기본값 1(SR 7411) + vsb `setdefault` 2, C.4)이다. 발동 계수를 잰 뒤(card 작성 전 실측, **측정 방법은 §10.1-4 -- CC-8 `activations_out`이 아니다**) 거부로 바뀌는 지점과 계측으로 남는 지점이 갈린다. 둘을 합쳐 한 card가 크면 **스키마·기록 함수·DF-14 card**와 **지점 적용 card**로 나눈다(나눠도 스키마 card가 최소 1지점을 배선해야 한다 -- 만들면 배선).

### 5.4 레일

| # | id | 대상 | 판정 | oracle | 선행 | P3? | DoD |
|---|---|---|---|---|---|---|---|
| 17 | `b26-rail-polarity` | B26-2: 극성(구조 규칙 + `supply_roles` 자리, §10.3), `trace_*`·방향 라벨·`propagate_node_voltages`/`derive_vsb_from_nodes` 기본 인자·`_metric_supply_current`·`_metric_rail_referenced_voltage`·`_metric_battery_centering_deviation`, B26-1에서 넘어온 SR 7282·8003·8091, **test 커밋: `probe_physical_consistency.py` 레일 집합 교체**. (UD-15 (2)=Y일 때만) SD 호출부 어댑터 + B34 인계 사이트 5~8·(v0.6) 10·14(도달 불가 분기) 삭제 -- 10·14 블록 값 판정 계약 동반(§5.1 인계 표) | red-green | (a) vss 회로 `trace_*` 가지 수, 합성 H1·H2·H4 거부, 합성 레일 이름 + 선언 밖 내부 넷 `vdd`. (b) 레일 이름 바꾸기에서 `load_topology` meta 불변(meta **전체** 불변은 B35 처리 뒤 -- X면 #49, Y면 이 card). (c) E-LIB 9/9·E-INST [prep 무동작] -- **(v0.9.2, P-37)** 단 `meta["rails"]`는 이 card가 `RailDeclaration`에 `polarity`를 더해 값이 바뀌므로 해시에서 빼고 계약값(nets = `supply_nets`, polarity = §10.3 구조 규칙 결과)으로 따로 판정, 그 밖 meta는 해시 같음(Phase 3 v8.2 E5 `MASK_META = ("rails",)`와 같은 모양). **(v0.9.3, S1)** 판정식은 값 전체 정확 일치: 병합본 `masked.rails` == `{"__dc__": "RailDeclaration", "nets": <card base library의 그 회로 `supply_nets` 정렬 집합>, "polarity": <§6 'E11 빼는 키 표' `POLARITY_P4`의 그 회로 값>}`(계약 밖 필드 0), base `masked.rails` == `{"__dc__": "RailDeclaration", "nets": 같은 집합}`(B26-1 계약 1 -- 아니면 INVALID). polarity 기대값은 엔진 출력이 아니라 고정 표다(출처와 #17 card 작성 전 조건은 그 표) -- Phase 3 v8.3 E5 (iv)와 같은 모양 | #1, #45, UD-1, (UD-15 결과). (v0.9) F2 뒤 단일 경로(UD-1·UD-15가 Phase 4 착수 때 질문) | Y(F2 뒤 단일 경로 -- (v0.9) 앞당김 없음, §3.2) | E0·E10 |
| 18 | `b26-mna-rail-ground` | B26-3: MNA 고정 노드 = 선언 레일 전부 → `also_fix`·`excite`로 덮어쓰기(P-13) | red-green + E-INST 차이표 | (a) 합성 회로 CM 응답, (c) 차이표(auditor θ* 재측정) | #17, DEC-40 1건(current_reuse `cmrr_estimate_db`, §7.4) | Y(F2 뒤 단일 경로 -- (v0.9) 앞당김 없음) | E0·E2 |
| 19 | `b26-rail-literal-lint` | B26-4: lint 도구 `A/tests/tools/rail_literal_scan.py` + **PT 계약 test `A/tests/contracts/test_rail_literal_lint.py`**(모든 병합본 V1에서 실행 -- 상시 배선) + 이름 상수 삭제 + 레지스트리 §2 정본 확정 + DF-19 위치 열 대체. 판정 규칙·면제 목록은 표 아래 | red-green(base lint FAIL -- F22, 병합본 0) | (a) 도구 합성 입력(면제 밖 리터럴 1개 → FAIL, 면제 목록 항목 → PASS, 조용한 통과 합성 구현 → test FAIL), (d) AST 전수 | #17, #18, **#21**, #3, **UD-7 결과 card(C1)**, UD-9 | **Y**(조상에 #21 → #20 → #6 -- 검토2 S10) | E10 |
| 20 | `cc5-legacy-gate-loader` | CC-5: `LEGACY_NAMES`·`load_json_checked`·`reject_legacy_names`, `json.load` 9곳 대체, `validate_no_legacy_vs_key` → `vs` 행. **깊은 복사 관용구는 해당 없음**(AST 계수 0, F19 -- 병합본에서 0 유지를 같은 test가 단언) | red-green | (d) 계획 N3.16에서 test-author가 옮긴 기대 목록 | #6 | Y | E4 |
| 21 | `mg1-rail-voltage` | MG1: `supplies_v`(하네스 `SPECS`: two_stage·current_reuse·folded = `{vdd: 1.8, gnd: 0.0}`, **nmcnr = `{vdd: 1.8, vss: 0.0}`(원점 이동 동등값)**), `rail_voltages` 유도 함수(§10.4), 스칼라 `vdd` 20줄을 폭(span)/절대 전위(hi·lo)로 분류해 교체(**노드전압 프레임 인자 5줄 = span**, §10.4 분류표), metric 인자 `supply_nets`·`rail_nets` 정리, 옛 키 행(`supplies`, spec `vdd`, metric `supply_nets`). **(v0.4) test 커밋에 IC11 `rail2` test 본문 + 감도 전파 허용오차 helper(§10.6, test 쪽, v0.3 #50 흡수)**: 대상 회로는 §10.6-0 규칙으로 고른다. **(v0.5)** #21 base는 #23 뒤라 #54 전이면 SPECS 2레일 회로 θ* 평가가 모두 실패로 끝날 수 있다(F27) -- 그때 실패 단위 판정기의 S2·S3 검출력 실측이 착수 조건이고, 검출 못 하면 #54 뒤로 미룬다(§3.3 순서 근거, §10.6-0). (v0.8, S2) 실패 단위의 margin 차원은 #23의 `normalized_margin` 값으로 정의된다(#23 노드 충돌 레코드는 수) -- 검출력 실측은 margin을 포함해 잰다. 이 card는 `propagate_node_voltages`의 rail_lo 0.0 고정과 `derive_vsb_from_nodes` 식을 **바꾸지 않는다**(노드전압은 최저 레일 기준 프레임 그대로 -- 그것을 절대 전위로 옮기는 것은 #22) | red-green + DEC-69 equivalence(키 매핑 뒤 θ*·metric·instance.json 동일 -- 4회로 모두 최저 레일 = 0 V라 성립) | (a) 옛 키 픽스처 거부. (b) **IC11 rail2**: base는 `supplies_v`·`rail_voltages`가 없어 S_B를 선언할 수 없어 실패(새 인터페이스 부재 red), 병합본은 S_A·S_B가 §10.6 허용오차 안(실측 F25: 뜻대로 분류한 원점 이동은 **비트 동일**). 판정기 자기 점검(F25 실측 근거): 노드전압 프레임 인자를 `hi`로 잘못 분류한 합성 구현에서 FAIL(실측 vsb 차 0.9 V), DF-24 부분 수정 상태(레일만 선언 전위로 고정, vsb 식 그대로)의 합성 구현에서 FAIL(실측 nmos vsb 차 −0.9 V, M8 gm_id 25.5 → 25.0). (c) ~~E-INST~~ **(v0.9.3, 실측 `p4_card21_rails_measure.md` §5) E-LIB 9/9·E-INST 해시 같음(빼는 키·필드 없음)**: card base 대 병합본에서 `e_lib.py`(MASK 없음) 해시가 같고 load 9/9 성공이다 -- `load_topology`의 `meta`는 `meta["rails"]`를 **포함해** 값이 같다(#21은 `meta`에 키를 더하지 않고 `RailDeclaration`에 필드를 더하지 않는다. 레일 전압은 spec dict 밖·`meta` 밖의 평가 문맥에 둔다, §10.4). E-INST는 SPECS 사이징 대상 회로에서 `instance.json` 정규화 해시가 같다(DEC-69 equivalence -- 4회로 최저 레일 0 V). 옛 키 행 중 `where="topology"`인 것(metric 인자 `supply_nets`, scope `/sizing_roles/metrics/*`)은 library 9회로 어디에서도 걸리지 않는다(load 9/9가 이를 판정), `where="harness_spec"`인 스칼라 `vdd`·`supplies` 행은 spec **루트** 키만 본다(자손을 훑으면 `supplies_v.vdd`가 걸려 E-INST가 실패한다). card base에 #17이 먼저 병합돼 있으면 `meta["rails"]`에 `polarity`가 있지만 #21은 그 값을 바꾸지 않으므로 같은 비교가 성립한다 | #20, **#23**(tol_V), U-26 (a) 확인 기록(§7.3), **#21 test 커밋의 V4 규칙 (1) 면제 승인**(§7.3), (조건부) #54 | Y | E4·E2·**E3** |
| ~~50~~ | ~~`ic11-rail2-oracle`~~ | **(v0.4) 폐지 -- #21로 흡수.** 실측(F25): #21만 병합된 엔진에서 folded S_B는 S_A와 비트 동일이라 rail2는 처음부터 PASS다. v0.3의 `xfail(strict=True, raises=AssertionError)`는 strict XPASS로 FAIL하고, `raises` 집합을 넓혀도 실패할 예외가 없다(#25 뒤 축 밖 거부는 S_A에서도 같이 난다 -- F26). 번호 50은 재사용하지 않는다 | -- | -- | -- | -- | -- |
| 22 | `df24-rail-absolute-vsb` | DF-24(DEC-61, 레일 0 V 가정 제거) **한 card에서 둘 다**: (i) `propagate_node_voltages`가 선언 레일을 `supplies_v` 전위로 고정(rail_lo 0.0 고정 제거, 노드전압이 절대 전위가 됨) (ii) vsb = abs(V(source) − V(bulk))(DEC-61 식 그대로), bulk 선언(`bulk` 필드)이 없으면 nmos = `supplies_v` 중 가장 낮은 전위 넷, pmos = 가장 높은 전위 넷(DEC-61), `vdd` 인자 제거. 순바이어스는 크기로 덮지 않고 봉인 항목 6(6b)이 거부한다(DEC-61) -- folded M7(HEAD vsb −0.65, F26)은 #22 뒤 0.65가 되고 순바이어스 여부는 6b 몫(UD-17 공동분석 자료에 적는다). **(v0.5) abs가 M7을 고치지 않는다**: 0.65는 일관된 노드전압의 값 0.45와도 다르다([ud17] §5.2-6) -- M7의 원인은 F27(UD-17a·c)이고 #22는 식만 바꾼다(P-31). 그래서 #22의 E-INST에서 folded M7 값이 바뀌어도 '해결'로 기록하지 않는다. 둘을 나누면 그 사이 병합본이 F25의 S3 상태(nmos vsb −0.9 V 오차)가 되므로 나누지 않는다. **(v0.6) `bulk` 필드(F34)**: 지금 topology에 `bulk` 키가 없고 엔진은 읽지 않는다. #22의 '선언 bulk 읽기' 몫은 **소비자가 있을 때만** 만든다(만들면 배선) -- UD-17e (ii)(bulk = 자기 source)가 결정되면 #22가 스키마 수용(`load_topology` 게이트 -- `bulk` 넷이 netlist 넷에 있음, 그 밖 거부)과 `derive_vsb_from_nodes`의 선언 bulk 읽기를 함께 하고 첫 소비자는 #55(current_reuse 데이터)다. (i)이면 #22는 DEC-61 기본 규칙(레일 극성)만 하고, `bulk` 키가 들어오면 **거부**한다(조용히 무시하지 않는다 -- 지금 엔진이 무시하는지 [미확인], #22 작성 전 실측). **(v0.7, S4)** #22 착수 시점에 UD-17e 답이 **없으면** #22는 거부만 넣는다(답을 기다리지 않는다). 나중에 (ii)가 오면 거부 해제와 선언 bulk 읽기는 **#55가 맡는다**(§5.10 #55, §3.3). UD-17e는 #22의 권고 선행이다. **(v0.8, S3) 노드 고정 값 읽기 경로 하나**: #53 UD-17c (i-3)이 #22보다 먼저 병합돼 고정 노드 읽기 경로를 만들었으면 #22는 선언 레일의 `supplies_v` 전위를 **그 경로로** 고정한다(두 번째 경로 금지 -- DEC-68, §3.3). #22가 먼저면 #22가 경로를 만들고 #53이 재사용한다((i-2)) | red-green | (a) **red = 계획 DF-24 행 그대로 '음전위 레일을 `supplies_v`에 둔 픽스처'**: 함수 수준 합성 입력(레일 `{hi: +0.9, lo: −0.9}`, 비레일 source nmos)에서 base는 V(source)를 돌려줘 기대값(abs(V(source) − V(lo)))과 다르다(일반 assert 실패 -- xfail 아님). (b) IC11 rail2(#21)가 base·병합본 모두 PASS(무회귀). (c) E-INST 4회로 동일(최저 레일 0 V에서는 절대 프레임 = 기존 프레임) | #21, **#23**, **#17** | Y | E0·E3 |
| 51 | `nmcnr-split-rail-spec` | nmcnr `SPECS` `supplies_v`를 확정값 `{vdd: 0.9, vss: −0.9}`로(U-26 (a)) | equivalence(IC11 불변 -- 무동작 card) | (c) #22 뒤 엔진에서 전후 비교: I-C11이 해소되지 않았으면 같은 실패 클래스·같은 margin(허용오차 §10.6 -- 레일별 1차 상한. (v0.7) #43 margin은 `null`이라 '둘 다 `null`이면 같음' -- §10.6-0) + 실패 전까지의 setup 양(노드전압은 −0.9 V 이동, VGS·VDS·VSB·gm_id·W 불변), 해소됐으면 E-INST 전부 | #22 (#44가 nmcnr를 해소하면 그 뒤) | Y | E2 |
| 46 | `b36-grammar-gate-scope` | B36 게이트 공백. UD-15 (1)=(a)이면 N3.12.2 행 추가 + 게이트 도구 6개 범위, (b)이면 흡수 이동 card | 게이트 변경(B28 형식) 또는 equivalence | (a) analog-grammar 수정 합성 커밋이 trailer 없이 거부됨, redteam 사례 | UD-15, plan_tables·게이트 변경 승인 | - | -- |
| 47 | `20260930-b37a-ports-roles`(phase 4, spec card **v2** -- **인용**) | **B37a**: role 기반 포트 접근자 1개(닫힌 role 어휘 6개, F21 -- 이름 정규식 없음), 운영 진입점 **E1·E2·E3 전부** 배선(값은 `load_topology` meta `"ports"`에서 한 번 -- 재계산·새 캐시 없음, E3는 `resolve_stack_layout`에 기본값 없는 키워드 `ports`), SR `input_referred_offset_pairs`의 `direction` 읽기 교체(MG2 몫은 키 삭제·옛 키 거부만 남음), `ports` 누락·빈 `ports`·입력 role 0개·모르는 role·**role과 `direction` 모순** 거부. `_TEMPLATE`은 `ports` 키가 없다(F21 재측정 -- prep §4.2 C3의 'ports: null'은 오기). 계약·V3 계획은 card 그대로(재서술하지 않음) | red-green + E-LIB 기대 차이표 | card 계약 1~9(v2). 요지: 이름 바꾸기 불변(library 판 = 레일 밖 **모든** 넷 -- base 3/9 FAIL, 합성 판 = 포트 넷만, 정규식 import 없음), `meta["device_roles"]` 반영, E2 차동 다리 간선 운영 동작, E3 그룹이 넷 이름과 무관 + sf_pushpull E3 값 고정(계약 5(b), UD-18 Q3), 거부(접근자 9 + `load_topology` 존재·레일 겹침 2 + 연결 파일 2), 명시적 `ports: {}` 수용, `direction` 소비자 교체, 기대 차이표 밖 차이 = FAIL. **[card v2 실측]** SPECS 4회로 평가·audit 9/9 불변, 보강 사본 새 실패 0·기대값 변경 0 → **DEC-40·V5 대상 아님**. 단 동작 변경(E-LIB 5회로·E3 3회로)과 `ports` 근거는 **사용자 승인 사안**(UD-18 Q1·Q2 -- v0.4의 '확인 사안'을 정정). test 커밋: selftest 합성 픽스처 **18곳**(17 + `test_s013`) 보강(test-author, code 커밋과 분리). **V3**: N2 대상 81(지금 규칙 659) -- 승인 당시 T6 분류기로 셈이라 **넓힌 T6로 재분류 필요**(card 착수 시 재측정, 81 이상). 모의 판정 80/81 죽음(계약 보강·기존 test 포함), 생존 1(`resolve_stack_layout` 경로 3 분기 삭제 -- 비등가, 계약 5(b)로 죽이는 기본안 = UD-18 Q3) | **#45 → #1 → #6**(셋 다 `load_topology`·`propose_device_roles_gap_fill`을 고쳐 순차 병합) + 34·35(V3 규칙) + **UD-18**. #17 간선 없음(극성 불필요 -- B26-2와는 같은 def `_build_theta_evaluator`라 동시 착수만 피한다). card approval = 기록 `20260930-b37a-ports-roles`(decision, 초안 `draft_b37a_approval_question.md` §3). 착수 시 E-LIB·E3 표를 다시 재고 다르면 멈춘다(card 계약 9, B26-1 뒤 E2 간선이 처음 켜짐) | **Y**(Phase 4 레일 묶음 -- prep §4.1). 모듈 = Phase 3 v6 D-19 답(따로 묻는 질문: (가) MOD2 / (나) MOD3, `rail_declaration` 옆) | E0 |
| 52 | `b37b-grammar-no-name-hints`(조건부) | **B37b**: AG `classify_nets` 라이브러리 경로의 `HINT_*`(1c·1e) 제거, 이름 힌트는 `analyze.py` CLI 경계의 명시 가정(`assume`에 보고). v0.3 B38(바이어스 힌트)을 흡수 | red-green(E-LIB 무변화 -- prep §3.2 p4 = p1) | (a) 합성 topology: 포트 아닌 내부 넷 `vo1`이 OUTPUT으로 분류되지 않음(B37a 뒤 red), 수동소자 단자 게이트 전용 넷에 1c 힌트 미적용 | **#46(B36, UD-15 (1))**, #47 | - | E0 |

**#19 lint 판정 규칙(계약)**:
* 대상 = 엔진 모듈 `A/*.py`(Phase 3 뒤 MOD1~MOD10). 하네스 `SPECS`의 `supplies_v` 키는 **선언 데이터**(DEC-62 'SPECS 데이터 항목')라 대상이 아니다.
* 발견 = 문자열 상수(`ast.Constant`, docstring 식 문장 제외) 중 casefold 값이 **스캔 어휘**에 드는 것. 스캔 어휘는 lint가 실행 시점에 읽는다: library 모든 topology의 `supply_nets` 합집합 ∪ analog-grammar `netclass`의 레일 이름 집합. 어휘를 lint 코드에 박지 않는다(topology 무관).
* spec 키 `"vdd"`도 센다 -- 그래서 #21이 선행이다(F4 20줄을 MG1이 없앤다).
* **면제 목록(전부, 이 밖은 0)**: (E-a) 예제 데이터 함수 `folded_cascode_example`·`two_stage_ota_example`(SD, `prep_b26_supply_nets.md` §1.4 '판정 아님') (E-b) UD-9가 유지로 결정되면 `find_differential_and_mirror_forks`(6a 공동분석까지) (E-c) UD-15 (2)=Y이면 어댑터의 정준 토큰 상수 (E-d) UD-15 (2)=X이면 analog-grammar CLI 경계 모듈(`analyze.py`)의 이름 집합 가정. 면제는 lint 입력 파일의 목록(함수·모듈 이름 단위)으로 두고 면제마다 근거 id를 적는다. E10 통과 기준에 이 목록이 그대로 들어간다.
* AG 파일(`skills/analog-grammar/assets/*.py`)은 UD-15 (2)=X일 때 #49가 lint 범위에 더한다.

### 5.5 노드전압

| # | id | 대상 | 판정 | oracle | 선행 | P3? | DoD |
|---|---|---|---|---|---|---|---|
| 23 | `df02-conflicts-seal-tolv` | DF-02 conflicts → SEAL_VIOLATION + `tol_V` 함수(MOD1, N3.6 식: (kind, L 앵커, VDS)별 LUT leave-one-out 보간 오차 최댓값, `tests/probe_interp_scheme_loo.py` 방법 승격) **(v0.4) 정본 실행 영향(F27)**: HEAD θ*에서 folded conflicts 최대 1.6 V, current_reuse 0.22272 V -- tol_V가 이보다 작으면 두 회로의 θ* 평가가 SEAL_VIOLATION으로 바뀌고 E-INST 기준선이 '끝까지 실행' → '실패 레코드'로 바뀐다(기대 차이표 + DEC-40, §7.4). 원인 해소는 UD-17(#53·#54). **(v0.5) 범위 추가(P-27)**: 충돌 검사는 노드전압의 첫 소비자(`reconcile_vsb_from_nodes`·vsb 유도) **앞**에 두고, 충돌이 tol_V를 넘는 노드의 값으로 vsb를 유도·LUT를 조회하는 경로가 남지 않게 한다(지금은 이름순 첫 경로 값을 조용히 채택 -- F27). **(v0.8, S2) `normalized_margin` 앞당김(CC-9)**: 노드 충돌 레코드 margin = `normalized_margin(최대 충돌 차, tol_V)`(계획 749행 '위반 크기 / 그 봉인 항목의 허용오차' -- 노드 충돌은 N3.6 봉인 항목 1 '같은 노드에 도달한 경로별 값의 최대 차 ≤ tol_V'(428행)라 분모가 정의된다). 함수 정의는 `00-common` §7.2 그대로(MOD2, `tol`이 `None`이거나 0이면 `None`). `00-common` 문구 정정은 이 design 승인 diff(§9-22). **(v0.8, S6 → v0.9, N-S2) 근거 없는 기본 인자 제거 -- 사슬 전체**(F36): (1) `propagate_node_voltages`의 `tol: float = 1e-6`은 **키워드 전용 `node_tol`(기본값 없음)**로 바꾼다(노드 충돌 허용오차 -- 값은 tol_V, 노드별 대응은 아래 기본안. 정확한 형(소자 → tol_V 함수 또는 소자별 값 사상)은 interface card가 정한다). (2) `reconcile_vsb_from_nodes`·`audit_vsb_consistency`도 같은 `node_tol`을 키워드 전용으로 받아 3831·3863의 `propagate_node_voltages` 호출에 **명시 전달**한다 -- `audit`의 `**kw` 전달에 기대지 않는다(지금은 `audit`의 자기 `tol`이 이름을 가려 호출자의 `tol=`이 노드 충돌 쪽에 닿지 않는다). (3) 두 함수의 vsb 비교 `tol: float = 1e-6`(3808·3843, 3851·3875)은 **인자째 없앤다**: vsb 비교는 저장된 vsb와 전체 그래프 노드전압에서 `derive_vsb_from_nodes`로 다시 계산한 값의 일치이고, 원칙 기본안 = **비트 동일**(`reconcile`은 `old != exp`이면 덮어씀 = 저장값이 곧 유도값, `audit`은 `d != 0`이면 보고). **(v0.9.1, 6차 검토 R6-S1 정정)** v0.9의 '같은 노드전압에서 다시 계산한 값'이라는 전제는 틀렸다: 정본 실행에서 SR 7294·7449(`_hr_resolve_vertical_group`)는 **부분 그래프**(`_bn_pair`)로 `propagate_node_voltages`를 돌려 vsb를 쓰고, 그 값이 reconcile 시점까지 남는다. 같은 노드라도 도달 경로가 다르면 부동소수 합의 순서가 달라 마지막 비트가 다를 수 있다(6차 검토 실측: current_reuse M58, 저장 `0x1.0000000000002p-2` 대 전체 그래프 재계산 `0x1.0000000000004p-2` = 2 ulp, reconcile 호출마다 1건). reconcile이 비트 동일로 그 차이를 덮어쓰므로 audit에는 차이가 남지 않는다(같은 실측에서 audit 게이트 발동 0). 근거: 새 상수를 만들지 않는다(메모리 '상수를 임의로 만들지 마라'), tol_V 계열로 바꾸면(값은 [미확인]이나 LUT 보간 오차라 1e-6 V보다 클 것으로 본다) 게이트가 느슨해지는 **기준 약화**라 사용자 승인 사안이고, 비트 동일은 강화라 원칙 안이다. 두 함수의 규칙이 같아야 하는 이유: `reconcile`이 허용오차 안의 옛 값을 남기면 비트 동일 `audit`이 그것을 잡는다(같은 규칙이어야 정합 -- (v0.9.1) 6차 검토 실측으로도 성립: reconcile을 1e-6 그대로 두고 audit만 비트 동일로 바꾸면 current_reuse에서 audit이 53회 모두 발동한다고 추론된다. 결론은 그대로, 바뀐 것은 위 전제뿐). (4) 호출부: 운영 7294·7449(`_hr_resolve_vertical_group`)·8658·8892가 `node_tol`을 넘긴다. **7294·7449는 `try … except Exception: … = None`(7297·7451) 안**이라 인자를 빠뜨려도 `TypeError`가 '노드값 없음'으로 삼켜진다(#13 전) -- 그래서 런타임 test가 아니라 아래 AST 단언으로 본다. 비운영 `tests/probes/probe_full_research.py:142`(pytest 수집 밖)는 #23의 test 커밋(test-author 경로 -- `tests/**`)에서 고친다. [재측정 v0.9, HEAD `0f23786` -- 부록 A H2] 노드에 tol_V(kind, L 앵커, VDS)를 대응시키는 규칙은 계획에 없다 -- 기본안 = 그 노드에 서로 다른 값을 준 두 경로 소자의 tol_V 중 **작은 쪽**(거부가 기본인 봉인 검사라 엄격한 쪽 -- §10.6-1 τ의 최댓값은 '같음'을 판정하는 허용오차라 반대 방향), 판정 기록에 값과 그 소자를 남기고 계획 한 줄 정정은 §9-25. `max_passes: int = 50`은 **인자째 없앤다 -- 반복은 진전으로 끝난다**: 루프는 진전 없는 pass에서 멈추고(HEAD 그대로) 진전 있는 pass는 미해결 소자를 하나 이상 지우므로 pass 수는 소자 수 + 1을 넘지 않는다(상한 인자·상수를 새로 두지 않는다. 계획 N3.6 `K_max`(441행)는 수치 반복의 상한이라 해당 없음 -- 5차 검토 §3이 루프 본문으로 증명 확인). HEAD 정본 실행의 `passes` 최댓값이 50 미만이면 제거는 무동작이다 [미측정 -- #23 작성 전 실측. 정보: 5차 검토의 구조 실측(library 9회로, 모든 소자에 `vds`를 준 `sized`)은 passes 2~3 -- 실제 실행 값이 아니라 판정 수치로 쓰지 않는다]. **(v0.9.1, R6-S1) vsb 비트 동일 규칙은 무동작이 아니다 -- 동작 변경으로 적는다**: 6차 검토 실측(검토자 측정 -- 판정 수치 아님, 정본 인자 하네스 4회로): two_stage_ota·nmcnr_amplifier는 F15 `ValueError`로 reconcile/audit에 닿지 않아 차이 없음, folded_cascode는 reconcile 5,200건 전부 `old is None`·audit 전부 `d == 0`이라 θ*·metrics 해시 같음(무동작), **current_reuse_telescopic_ota는 reconcile 54회 중 호출마다 1건 `0 < |old − exp| ≤ 1e-6`(M58, 최대 1.11e-16)이 덮어써져 SLSQP 경로가 갈리고 정본 θ*가 마지막 자리에서 바뀐다**(`L_class__M68` `0x1.124b078d0db2dp-21` → `0x1.124b078cff54cp-21`, `L_class__M8` `0x1.fcd9f04470762p-22` → `0x1.fcd9f044663dep-22`, metrics 해시 `5ff39866…` → `8b171811…`). 그래서 #23 기대: **current_reuse reconcile 지점 > 0, θ* 비트 변경, audit 게이트 발동 0** -- E-INST 기대 차이표에 넣고 DEC-40(§7.4)으로 받는다. #23 작성 전 실측이 이 수치를 다시 잰다(4회로 정본 실행의 `reconcile` 지점 `0 < |old − exp| ≤ 1e-6` 소자 수·`audit` 지점 `0 < |d| ≤ 1e-6` 소자 수). **기대 차이표에서 원인을 가른다**: 같은 회로라도 (가) 노드 충돌 거부(F27, SEAL_VIOLATION)로 생기는 차이와 (나) vsb 비트 동일 덮어쓰기로 생기는 θ* 마지막 자리 차이를 다른 행으로 적는다(실측은 두 규칙을 따로 켠 실행으로 가른다). `audit` 쪽 > 0이 나오면 그것은 게이트가 잡으려던 스테일 쓰기의 실례다(원인 card 지정 -- 허용오차를 되살려 덮지 않는다). (정보, 6차 검토 §4) 7294·7449 부분 그래프 전파의 다중 도달 차이가 1e-6을 넘는 사건이 current_reuse 정본 실행에서 7294 10,128건·7449 47,264건 있었다 -- P-27(충돌 노드로 vsb 유도 금지)이 이 두 지점에도 걸리므로 작성 전 실측은 전체 그래프 θ*뿐 아니라 이 두 지점의 충돌 규모도 잰다(F27 범위, v0.9 변경 아님). `rail_hi/lo` 기본 인자는 #17 몫(같은 함수 -- 순차 병합) | red-green | (a) 다중 도달 불일치 합성, **충돌 노드에 닿는 소자의 vsb 유도·LUT 조회 계수 0**(계수 래퍼 -- 조용한 선택 합성 구현에서 test FAIL), (v0.8) margin 손계산(위반 크기 / tol_V, 분모 0·`None` → `null` -- `00-common` CC-9 oracle 그대로), `node_tol`을 넘기지 않은 호출이 세 함수 모두에서 실패함(기본값 없음 -- 기본값을 남긴 합성 구현에서 test FAIL), **(v0.9, N-S2)** `audit_vsb_consistency(…, node_tol=t)`의 `t`가 `propagate_node_voltages`에 그대로 닿음(계수 래퍼 -- `**kw`에 기대 이름이 가려지는 합성 구현에서 test FAIL), vsb가 노드전압 재계산과 1e-7 V 다른 합성 항목을 `audit`이 보고하고 `reconcile`이 덮어씀(HEAD는 1e-6 기준이라 놓친다 -- red), **엔진 `A/*.py`·하네스·`tests/probes/**`의 세 함수 호출 전수(AST, `git grep -w` 세 이름으로 수집)가 `node_tol`을 키워드로 넘김**(7294·7449처럼 `except Exception` 안의 호출도 -- 하나를 빠뜨린 합성 구현에서 test FAIL), (d) **(v0.8, S8) B21 (c) 재현 입력 -- card '작성 전 실측'이 `docs/03-analysis/gain-budget-gmid-sizing-40-defect-fixes/`에 커밋한 파일과 그 커밋 해시**(`_drafts` 자료는 oracle 출처가 될 수 없다 -- `00-common` §9.3), (c) 정본 실행 4회로의 결과 종류·margin을 기대 차이표와 대조(표 밖 차이 = FAIL. #53·#54가 먼저 병합되면 그 회로 행은 성공 단위) | #6 (권고: #53·#54 뒤 -- §3.3) | Y | E0·E2 |
| 24 | `df01-vsb-recompute` | DF-01: vsb를 노드전압으로 고친 뒤 W·gm·gds 재계산(원인 코드 SR 7579 한 줄, F9). §10.1-4 발동 규칙에서 원인이 DF-01로 지정된 `vsb` 기본값 사이트. **(v0.5) 실사례 F28**: current_reuse 매칭쌍 M2a(vsb 0에서의 W 19.795 µm)·M2b(16.701 µm) -- 재유도 뒤 재사이징이 권위 소스 소자에서 건너뛰어지는 것으로 보인다. 작성 전 실측에서 원인 경로가 SR 7579 계열인지 확인하고, 다른 경로면 이 card 범위에 넣을지(같은 DF-01 뜻 '버전 혼재')를 card에서 정한다 -- 계획 DF-01 행에 없는 사이트면 §9 정정 요청 | red-green | (a) 버전 혼재 검출 픽스처, **매칭쌍(같은 ID·gm/ID·L·vsb)의 W가 같음**(합성 -- 한 소자만 재유도 전 vsb로 사이징한 구현에서 FAIL), (d) F28 실회로 기록(#54 뒤에는 current_reuse 실측으로) | #22, #23, #13 | Y | E0 |

### 5.6 LUT·PDK

| # | id | 대상 | 판정 | oracle | 선행 | P3? | DoD |
|---|---|---|---|---|---|---|---|
| 25 | `df27-lut-axis-gate` | DF-27(축 밖 입력 → `lut_axis_out_of_range`, 클램프 0). **(v0.4) 정본 실행 영향(F26)**: HEAD 값에서 folded θ*(VS 축 밖 436 조회 -- M7 −0.65, M1·M2 1.6, M5 1.8)와 current_reuse θ*(3,537 조회 -- 0.8125 ~ 1.5 대)가 축 밖이다. 그래서 **#22 뒤에 병합**(DEC-61 vsb = abs(V(source) − V(bulk))로 음수 vsb가 크기로 바뀐다)하고, **#25 → #26 → #27을 연속 병합**한다(사이에 다른 card 병합 없음 -- U-27b의 VS 축 0~1.8 V(계획 U-27)가 양수 쪽 0.8~1.8을 덮는다). #25·#26 병합본에서 두 회로 정본 실행이 축 밖 실패로 끝나는 것은 기대 차이표에 적고(DEC-40, §7.4), #27 병합본에서 다시 잰다. **(v0.5)** (i) folded의 축 밖 4소자는 전부 F27 파생이라 #23이 먼저 그 회로를 멈춘다 -- #25 차이표의 folded 행은 #23 뒤 실패 레코드 그대로일 수 있다. current_reuse는 M2a·M2b(F27 파생)와 M9a·M18a(진짜 범위, 0.825 V -- #27의 VS 0~1.8이 덮음, UD-17e가 bulk = 자기 source면 vsb 0) (ii) **축 밖 오류 고유 클래스 전파(P-28, F29)**: 부록 C.1 X 지점(후보 배제)이 `lut_axis_out_of_range`를 '후보 없음'으로 바꾸지 않는다. **(v0.7, S2 -- v0.6의 'X 핸들러에서 다시 올림'을 대체)** 이 card가 **P-34 규칙**을 만든다: X 지점은 MOD1 정의역 오류(§10.7)를 받으면 그 후보점 하나를 배제하고(후보 실패 = 탐색 중 처리) 배제 사유를 클래스·소자·축·값과 함께 모으며, 모든 후보가 축 밖으로 배제되면 집계 지점(MOD4 이상)이 `SealViolationError`(`lut_axis_out_of_range`, 소자·축·값)를 올린다 -- '후보 없음'으로 바꾸지 않는다. #10은 이 동작을 유지하고 나머지 타입만 좁힌다. **작성 전 실측에 X 15곳의 MOD 위치(D0b 이관표)와 각 지점의 집계 지점(모든 후보 실패를 판정하는 호출부)을 넣는다** -- 변환 지점이 MOD4 이상인지 확인. **(v0.8, m2) 같은 표에 MOD1 raise 지점부터 집계 지점·`SearchFailedError`까지 경로 위의 모든 `except ValueError`/`except Exception` 핸들러(F5: SR `ValueError` 포함 26·`Exception` 6, SD 4, 하네스 1·2 중 그 경로에 있는 것)를 넣는다** -- #25가 #10보다 먼저 병합되므로 그 사이에는 #10의 좁히기가 없다. **(v0.8, S9) 실행 수준 보존·혼합 사유**: P-34 두 줄(§7.2) -- 모든 시작점이 실패하면 `SearchFailedError.record.detail`에 시작점별 마지막 실패 클래스와 클래스별 배제 계수를 싣고, 후보 일부는 축 밖·나머지는 다른 사유인 혼합이면 집계 지점은 기존 클래스를 쓰되 `detail`에 배제 사유를 클래스별 계수로 싣는다. **(v0.8, S2) margin** = `normalized_margin(위반 크기, None)` = `null`(LR3는 축 범위에 허용오차를 두지 않는다 -- N3.6 봉인 항목 1~8 밖) (iii) 외삽 대안 없음(P-29), VS 축 상한 1.8 V 유지(P-30) -- 레일 폭을 넘는 vsb(실측 2.05 V, F26)는 연장 대상이 아니라 거부 대상이다. 2.05 V 조회의 출처는 이 card 작성 전 실측 | red-green | (a) vsb 0.9 V 픽스처 → `lut_axis_out_of_range`(옛 표본 LUT에서 -- 계획 U-27 선행 조건 (1)), 조용한 클램프 합성 구현에서 test FAIL, **(v0.5) 모든 후보가 축 밖인 합성 입력에서 실패 레코드의 클래스·사유가 `lut_axis_out_of_range`(소자·축·값)이고 '후보 없음'이 아님**(F29 형태 재현 -- 흡수 합성 구현에서 test FAIL), **(v0.7) 일부 후보만 축 밖인 합성 입력에서는 그 후보만 배제되고 탐색이 다른 후보로 계속됨**(첫 축 밖에서 바로 올리는 합성 구현에서 test FAIL), 외삽 합성 구현에서 test FAIL, **(v0.8, S9) 하네스 실행 수준(F29 재현 입력의 전체 실행판 -- `docs/03-analysis/gain-budget-gmid-sizing-40-defect-fixes/`에 커밋)에서 최종 `SearchFailedError` 레코드 `detail`에 `lut_axis_out_of_range`가 시작점별 마지막 실패 클래스로 보임**(배제 사유를 버리는 합성 구현에서 test FAIL), 혼합 사유 합성 입력에서 `detail`의 클래스별 계수가 입력과 같음. (c) 정본 실행 기대 차이표 | #6, **#22**(그래서 #23 -- `normalized_margin`) | Y | E5·E2 |
| 26 | `u27a-sweep-script` | U-27 도구 결함(`sky130_lut_sweep.py`, (v0.8, S8) 내용을 이 문서로 옮김 -- 줄은 `cd64170` [prep: `prep_u27_u30.md` §2.2], card 작성 전 `grep -n -e 'VS.iVS.' -e SID_1F -e xdut -e VS_GRID -e OUTPUT_DIR <A>/sky130_lut_sweep.py`로 다시 잰다 -- (v0.9, 5차 검토 m-3) v0.8 명령(`'VS{iVS}\|…'` 한 패턴)은 HEAD에서 0줄·rc 1이었다. 중괄호를 패턴에 넣지 않는 위 형태가 HEAD `0f23786`에서 33줄(267·275·276·108·73·75 포함)을 낸다, 부록 A H4): **G1** 체크포인트 이름이 VS **인덱스** 기반(`…_VS{iVS}.npz`, 267·275~276행) → VS **값** 기반 이름(간격이 바뀌면 다른 VS 결과를 조용히 재사용) **G2** 재사용 조건이 `"SID_1F" in d` 하나(268~272행) → 필요한 열 집합 전체(`ID,GM,GDS,CGG,CGD,CGS,CGB,SID_1F`)가 있을 때만 재사용 **G3** CGS·CGB 추출 경로 없음(소스가 접지 노드 `0`, 146~150·172~179행) → CGB = 벌크 여기에서 게이트 전류, CGS = 소스를 별도 전압원 노드로 분리해 여기 **G4** npz 메타 부족(329~333행) → `w_ref_m`·PDK 루트·커밋·모델 파일·ngspice 버전·스크립트 해시 기록 **G5** `VS_GRID` 상수(108행) → 상한 = library `supplies_v` 최대 차를 계산해 인자로(LR3, P-5), 간격은 기존 0.2 V **G6** 출력 경로가 저장소 assets 안(73·75·323행) → `--out` 인자(code worktree 밖 쓰기 0) + **G7: `_parse_output`이 ngspice 출력의 `Error:` 줄을 발견하면 조합 이름·줄을 담아 거부**(F20) | red-green | (a) 소형 격자, 옛 조합 비트 동일 재측정, CGS+CGD+CGB ≈ CGG((v0.9, 5차 검토 정보) '≈'의 허용오차는 아직 정의가 없다 -- card가 근거 있는 허용오차(예: 같은 ngspice 실행의 수치 정밀도에서 유도)를 정하지 못하면 이 항목은 판정이 아니라 차이 **기록**으로 둔다. 상수를 새로 박지 않는다), **`Error:` 줄이 있는 합성 ngspice 출력에서 base는 조용히 파싱(red) → 병합본 거부** | #25 | - | E6 |
| 27 | `u27b-lut-regen` | 재생성 + 옛 격자점 대조 + 새 해시 기록 + **VS 축 leave-one-out 보간 오차 기록**(정보, P-5) | red-green + 대조 기록 | (c) 옛 5 VS 점 × 기존 5열 비트 동일 기대 | #26, 다르면 DEC-40(§7.4) | - | E6 |
| 28 | `u30a-pdk-record-noop` | U-30 선언(§10.2) + MOD1 로더 + npz 해시 연결 + DF-34 Phase 4 몫 + 엔진 폴백 15곳 삭제 + 단위 m 통일 + `L_min` 배선, 값은 **기존 값**(무동작 단계) | red-green + equivalence | (d) PDK 규칙표, (c) E-INST | #27 | Y | E7 |
| 29 | `u30b-wbounds-min-finger` | `min_finger_w` = difftap.2, `W_bounds` 하한 유도 | red-green + 전후 비교표 | (d), (c) 비교표(auditor, 변형 spec은 `derived_spec`) | #28, DEC-40(§7.4) | Y | E7·E2 |
| 30 | `b24a-lut-vgs-query-api` | B24 (a) -- `gain_ranking`의 `lut._query` 직접 조회를 공개 조회로 바꿔 면제 `20260929-p4-scan-exempt`를 해소(§4.3). **(v0.9.2) 문서 몫**: 같은 card에서 design 20 §10 E2 통과 기준의 '현재 승인 `20260929-p4-scan-exempt` 1건' 문구를 고친다(승인 `20261001-p2dod-e2-wording` 재검토 절 -- 면제 0이면 '면제되지 않은 발견 0' = '발견 0'. 면제 집합이 줄어드는 쪽이라 새 사용자 결정은 아니다). **(v0.9.3, m3) 커밋 주체** = 오케스트레이터(`Role: doc` 커밋 -- code-author는 설계 문서를 쓰지 않는다), 그 card 병합과 같은 묶음(같은 gate push). 면제 줄이 사라진 뒤 승인 기록 `20260929-p4-scan-exempt`가 가리키는 `path::rule`이 남아도 probe 중복 스캐너·gate가 문제 삼지 않는지(쓰이지 않는 면제를 거부하는 규칙의 유무)는 #30 card 작성 때 확인한다 **[미확인]** | red-green | (a) 격자점 조회값 = 표 값. (v0.9.2) (d) 병합본에서 probe 중복 스캐너 출력에 면제 발견 0 [card 작성 때 확정]. (v0.9.3, m3) 글자는 §5 머리의 oracle 종류((a) 구성, (d) 계획·원자료 -- 여기 원자료 = 승인 기록 `20261001-p2dod-e2-wording` 재검토 절)라 (b)·(c)가 없는 것이지 번호 누락이 아니다 | #6 | Y | E0 |
| 31 | `df10-nonmonotone-inversion` | DF-10 + B24 (b). **(v0.5) 실회로 입력 기록 F31**(folded M1 평탄부, current_reuse M9a 두 근) -- card 작성 전 실측에서 이 두 소자를 UD-5 규칙(근 전부 + 호출자 선택 규칙)으로 다시 재고 W 차이를 기록 | red-green | (a) 비단조 합성 곡선, (d) F31 두 소자 기록 | UD-5, **#6** | Y | E0 |

### 5.7 캐시

| # | id | 대상 | 판정 | oracle | 선행 | P3? | DoD |
|---|---|---|---|---|---|---|---|
| 32 | `df07-lru-caches` | DF-07 | red-green | (a) 상한 초과 뒤 최근 키 적중 | #6 | Y | E0 |
| 33 | `df13-lut-content-key` | DF-13 `id(lut)` 키 → **LUT 로드 때 한 번 계산한 내용 지문**(§4.4) + 상한 | red-green | (a) 같은 내용 다른 객체 적중·다른 내용 미적중, 호출당 지문 재계산 0(계수 래퍼) | **#6** | Y | E0 |
| 34 | `df15-rz-cache-key` | DF-15(재현 먼저) | red-green(재현 안 되면 계획 정정 요청) | (a) | #6 | Y | E0 |

### 5.8 개별

| # | id | 대상 | 판정 | oracle | 선행 | P3? | DoD |
|---|---|---|---|---|---|---|---|
| 35 | `df04-device-name-exact` | DF-04 | red-green | (a) | #6 | Y | E0 |
| 36 | `df05-mirror-pairs-all` | DF-05 | red-green | (a) 3소자 미러 | #6 | Y | E0 |
| 37 | `df08-22-spec-origin` | DF-08·DF-22 + U-04 `origin` | red-green | (a) | UD-4(#6 불필요 -- N3.14 실패 클래스를 쓰지 않는다. `origin` 누락 거부가 `SchemaRejectedError`를 쓰기로 card에서 정하면 #6 추가) | Y | E0 |
| 38 | `df20-fallback-constants` | DF-20(vds 0.6/0.2, margin 0.05 -- SR 1564, `gm_id_bounds` `(2.0, 30.0)` 3곳, `_DEFAULT_METRIC_STAGE_BUDGET_GM_ID` 15.0 -- SR 1941·6042·10221, `min_vds_by_role` 읽기 3곳과 하네스 4벌) | red-green | (d) 유도 근거(DEC-27·DF-25 연결은 6b) | #13 | Y | E0·E1 |
| 39 | `df23-general-rules` | DF-23 Phase 4 행(P10 목록). **(v0.5)** P10 문서 커밋 `0fa6ca2`의 `docs/03-analysis/gain-budget-gmid-sizing-20-dead-code-dup/df23_inventory.json`(`measured_at` = `766b5c2`): 항목 515 중 `phase` = `"4"` **63**(그 밖 3: 61, 7a: 27, 7b: 46, 6b: 1, 해당 없음 317) [재측정 v0.5]. P10 card(`b8d4c4d`, test-only) 판정 뒤 확정 -- 63이 한 card로 크면 묶음(파일·규칙 종류)으로 나눈다 | red-green | (a) NEW-TOPO | P10 병합 | Y | E0 |

### 5.9 배선

| # | id | 대상 | 판정 | oracle | 선행 | P3? | DoD |
|---|---|---|---|---|---|---|---|
| 40 | `theta-order-gate` | W-1(`validate_theta_declaration_order` 배선 -- (v0.6) 모듈 **MOD3**, Phase 3 v6 확정) | red-green | (a) theta 순서만 뒤바꾼 픽스처 거부, 무동작 9/9 | #6 | Y | E0 |
| 41 | `euler-repair-wire` | W-2 배선 + **D-5 함수 `audit_vertical_stack_id_euler_feasibility` 삭제**(표 행은 #2가 이미 지웠다 -- F18로 중간 병합본 안전) | red-green + E-INST 전후 | (a) S146 blocked 그룹, (c) 행 배치 전후 | #2, 달라지면 DEC-40 | Y | E0·E2 |
| 42 | `roles-ratify-cli` | W-3 | red-green | (a) 합성 topology 사본 기록·재로드 | 없음(실패 클래스 미사용, 다른 card와 파일 충돌 없음 -- 검토2 M7) | Y | E0 |

### 5.10 회로 (I-C11, 설계는 §11)

| # | id | 대상 | 판정 | oracle | 선행 | P3? | DoD |
|---|---|---|---|---|---|---|---|
| 43 | `ic11c-explicit-failure` | I-C11 실패 명시화(UD-6과 무관하게 한다): two_stage `_hr_verify_group_kvl_sum`의 KVL 불일치 `ValueError`와 nmcnr 스택 예산 배정 불가를 N3.14 **`SealViolationError`**(항목 = 기둥 KVL, 소자, 위반 크기 -- 계획 N3.14 SEAL_VIOLATION 행(742행): 탐색 중 처리 = 실패 기록. (v0.7) 클래스 근거 = 기둥 KVL -- 739행 `local_infeasible` 정의가 기둥 KVL을 봉인 대상으로 든다. 이 card는 허용오차 기반 봉인 항목을 구현하지 않는다)로 바꾸고 탐색 루프가 `CANDIDATE_FAILURE_CLASSES`로 받아 후보 실패로 기록한 뒤 계속하게 한다. `local_infeasible` 실패 레코드(739행)는 층 0(DEC-71 기둥 조립, 미구현)의 몫이라 쓰지 않는다 -- 이 검사는 `_evaluate` 안의 헤드룸 해석 단계이지 층 0이 아니다. 모든 시작점 실패면 `SearchFailedError`(exit 6). **판정 경계는 HEAD 그대로**(`abs(Σ VDS − 폭) > 1e-9 × max(폭, 1)`, SR 7068~7069의 `vdd`만 #21이 폭으로 바꾼다), **(v0.7, S1) `FailureRecord.margin` = `null`**(계획 749행 '분모가 0이거나 정의되지 않으면 margin은 `null`' -- 이 검사는 허용오차를 가진 봉인 항목이 아니라 대수 불변식이라 분모가 정의되지 않는다. (v0.8) 계획 396행: '기둥 VDS 합 ≠ 레일 전압차'는 '검사 대상이 아니다', 층 0 기둥 KVL은 '새 검사 항목이 아니다'. v0.6의 'Σ tol_V' 분모는 철회). (v0.8, S2) margin은 #23의 `normalized_margin(위반 크기, None)`으로 만든다(margin을 쓰는 곳 하나), 위반 크기는 레코드에 그대로 둔다 -- 근거는 §11.2 | red-green | (a) 하네스 정본 실행 two_stage·nmcnr: base = `ValueError`·exit 0(F15), 병합본 = 실패 레코드 + exit 6(또는 해가 나오면 θ*). 메시지의 'stage1_out'·'KVL'은 유지(known-limitation test 3쌍이 계속 성립 -- `InfeasibleSizingError`가 `ValueError` 하위(SR 6429)이므로 xfail `raises=ValueError`도 성립), (v0.7) 실패 레코드 `margin`이 `null`이고 위반 크기가 기록됨 | #6, #10, #23(`normalized_margin` -- (v0.8). 그리고 #43 병합본의 E2 비교가 #23 뒤 상태를 전제) | Y | E2·E11 |
| 44 | `ic11c-resolve` | I-C11 해소 -- UD-6 선택지에 따라 내용이 정해진다(§11.3): (A) 계획 정정만(이 card 없음) / (B) DEC-70 부분 선행 구현 / (C) topology 선언 정정(공동분석 결과 반영). 어느 경우든 해소된 회로의 xfail 3건·known_limitation 3건 정리, V4 면제 `20260923-c9-v4-exempt` 재검토(백로그 B9·B12) | red-green(해소 시 xfail strict가 XPASS → 해제) | (c) E-INST 전후, (a) 합성 회로(B안), (d) 공동분석 확인표(C안 -- (v0.8, S8) topology 수정 승인 기록에 붙여 `docs/03-analysis/gain-budget-gmid-sizing-40-defect-fixes/`에 커밋한 판과 그 커밋 해시) | UD-6, #43 | Y | E2 |
| **53** | `ud17-folded-op-point`(v0.5, 결과 card. (v0.6) 범위 재정의) | **UD-17a와 UD-17c가 함께 정한다**(UD-17b는 17a를 따른다 -- 17a만으로는 X·Y 1.2 V·Vg9 0.7 V·out 1.0 V가 남는다, F32). 몫: (1) **데이터**: M1·M2 kind 또는 단자 방향(UD-17a, **connectivity는 사용자만 수정**), 그 결과를 따르는 `kcl_fold_M5`·`kcl_fold_M6` 부호와 M1·M2 role 재검토(UD-17b, 메타데이터 -- 공동분석 확인 뒤 Claude), **json 설명 주석 3곳 정정**(F35, 메타데이터) (2) **UD-17c 갈래** -- (i) 외부 DC 선언(`bias3` 전압·출력 CM·**입력 CM** = tail 컬럼): 선언할 필드가 지금 없어 **새 선언 필드(이름은 card에서 glob·옛 키 충돌 grep) + 엔진이 노드전압 전파에서 그 값을 고정 노드로 읽음**(공유 코드 = 승인된 card, 값은 사용자 스펙). 남는 전압은 컬럼 소자 VDS로 간다. **(v0.7, S7) 노드 고정 값의 출처는 하나**(DEC-68 '개념 하나에 저장 위치 하나'): 고정 노드 전위 선언은 #21 `supplies_v`(레일 고정 전위)·#22(선언 레일을 그 전위로 고정)와 같은 일이므로, `supplies_v`와 한 스키마(예: 레일 아닌 고정 DC 항목을 같은 선언 아래)로 둘지 레일이 아닌 고정 DC로 따로 둘지를 card가 정하되, 엔진이 노드 고정 값을 읽는 경로는 하나로 한다(두 선언이 같은 넷을 고정하면 거부). **(v0.8, S3) 형태별 간선**: (i-1) `supplies_v`와 한 스키마 = 하드 #21 → #53, (i-2) #22 고정 경로 재사용 = 하드 #22 → #53 -- 둘 다 권고 #53 → #23 없음, (i-3) 따로 + #53이 먼저 경로를 만듦 = 권고 유지 + 하드 #53 → #22(#22가 재사용, §5.4 #22). 경로는 먼저 병합되는 card가 만든다(§3.3) (ii) 엔진이 fold_group 컬럼 KVL을 푼다: SR fold_group singleton 우회(7507~7563)의 일반 규칙화 -- 계획 개정 동반, 이름 없는 규칙(topology 무관), 다른 회로 무동작 증명. 외부 DC 없이는 해가 하나로 안 정해지는 컬럼(출력 CM)은 거부로 끝난다 (iii) 두고 멈춤: 이 card는 (1)만이고 folded는 #23 뒤 실패로 남는다 | (i)·(ii): red-green + E-LIB·E-INST 전후 / (iii): 데이터 정정 + E-LIB·E-INST 전후 | (d) 공동분석 확인표(넷 기준 connectivity 표 -- topology.json에서 새로 뽑은 표, B47) -- **(v0.8, S8) 출처 = topology 수정 승인 기록(WP-07, §7.3)에 붙여 `docs/03-analysis/gain-budget-gmid-sizing-40-defect-fixes/`에 커밋한 판과 그 커밋 해시**([pack] §1.1·§1.2는 그 표의 초안 자료이지 출처가 아니다), (c) folded θ*에서 (i)·(ii)면 **conflicts 0·VS 축 밖 조회 0**((v0.8, S6) 최대 충돌 차를 수로 기록하고, #23 병합본이면 tol_V 기준, #23 전 병합이면 HEAD `tol` 1e-6 기준(더 엄격한 쪽, 기존 값 -- 새 상수 아님)으로 판정한 뒤 #23 병합 때 다시 잰다)(F26·F27 측정 방법 재사용), **M7 vsb가 Vg9의 두 경로(Y 경로·M9 경로)에서 같은 값**(F32: 지금 0.95 대 0.45 -- conflicts 0이면 따라 나오지만 M7을 따로 기록), (iii)이면 conflicts가 F32 F1 값(1.2/1.2/0.7/1.0)으로 줄었는지만 대조하고 '해소'로 기록하지 않는다. (a) (i)·(ii)면 합성 회로(선언 DC 고정 노드 / 컬럼 KVL), 다른 library 회로 무동작. **사이징 결과 판정은 하지 않는다**: 일관된 노드전압에서는 M7 W가 약 2.5 mm로 `W_bounds` 밖일 수 있어([ud17] §4.3) folded가 infeasible로 끝나는 것도 정당한 결과다 | **UD-17a·b·c 전부**, (v0.7) (i)·(ii) **#6**(엔진 몫, P3? = Y), (ii) #23, (v0.8) (i-1) #21·(i-2) #22(그때 권고 없음). 권고: (i-3)·(iii) #23 전(§3.3). (i)의 새 필드 이름은 CC-5(#20) `LEGACY_NAMES`와 겹치지 않는지 card 작성 전 grep(간선 아님). (i)·(ii)는 `propagate_node_voltages` 충돌 집합(§3.4 -- #17·#21·#22·#23과 순차 병합) | Y((i)·(ii)) / -((iii), 데이터) | E2 |
| **54** | `ud17-current-reuse-vom1`(v0.5, 결과 card. (v0.6) bulk를 #55로 분리) | **UD-17d 결과**: Vom1·Vop1 DC를 무엇이 정하는가. (i) 출력단 VGS 0.677 V가 의도 → `diffpair_branch_a` 컬럼을 Vom1·Vop1에서 위·아래로 나누고 아래 반쪽 예산을 출력단 VGS 쪽 기준 소자에 묶는 메타데이터(connectivity 그대로 -- 예: `budget_reference_device`로 M19(M10)에 묶는 [pack] C1 흉내. **기준 소자는 공동분석**) **+ 아래 세 소자(M3a·M4a·M5) 최소합 0.9 V를 0.677 V에 넣는 설계 변경**(M4a vds = compensation 결정, M5·M3a vds 배분, 또는 출력단 VGS -- 스펙·compensation 쪽, 사용자). 설계 변경 없이 분할만 하면 M5 vds 0.0273 V(F33, 포화 여부 [미측정] -- 판정 기준은 6b)다. 이때 M2a·M2b vsb 0.9227은 진짜 축 밖(UD-17e가 M2a·M2b로 넓어짐 -- #55/#27) (ii) 컬럼 0.9 V가 맞음 → M16·M26 VGS 0.9 V 스펙(compensation gm/ID 18.0과 충돌, class-AB 바이어스 재계산 -- `M10.vds_match_vgs_of = M16`은 KVL 사실이라 지우지 않는다) (iii) CMFB 등 다른 것이 정함 → 회로도 근거로 선언 위치 결정. 엔진 규칙 갈래('다른 그룹이 고정한 공유 노드를 컬럼 배정이 따른다' -- 교차 그룹 노드 구속)는 (i)의 메타데이터 대신 고를 수 있다 | 데이터 정정 + E-INST 전후 / red-green(엔진 규칙) | (d) 공동분석 확인표 -- **(v0.8, S8) 출처 = topology 수정 승인 기록에 붙여 `docs/03-analysis/gain-budget-gmid-sizing-40-defect-fixes/`에 커밋한 판과 그 커밋 해시**([pack] §3·§5 체크리스트는 초안 자료), (c) current_reuse θ*에서 conflicts 0((v0.8, S6) 최대 충돌 차 기록, tol 기준은 #53 칸과 같음)·replica 컬럼(vbias2_stack·vbias3_stack) 재배정 뒤 충돌 0(C1의 M58·M64 2건이 재배정 누락 산물인지 확인), 하네스 정본 실행 끝까지. **(v0.7, S5) 꼬리 M5 포화는 판정하지 않고 기록한다**(M5 VDS 값과 LUT 격자상 위치): Phase 4에는 포화 경계를 정하는 계획 유도 규칙이 없고(봉인 항목 7 'VDS − VDsat ≥ −tol_V'의 VDsat 유도 DF-25는 6b), '선언 최소 vds'로 읽힐 수 있는 하네스 `min_vds_by_role` 0.2는 DF-20(#38)이 없애는 근거 없는 폴백 상수라 oracle에 쓰지 않는다. UD-17d (i)의 설계 변경에서 사용자가 M5 vds 값을 스펙으로 정하면 그 값이 선언값이 되고, 그때만 그 값과 비교한다(E8 파일럿 조건 -- 축 밖은 #27 또는 #55), `cmrr_estimate_db` 등 기준선 변경은 DEC-40(#18 몫 합침 -- §3.3). (a) 엔진 규칙 갈래면 합성 회로 + 무동작 | **UD-17d**, (엔진 규칙) #23(하드). 권고: #23·#21 전 -- **데이터 갈래만**((v0.7, S3) 엔진 규칙 갈래면 권고 간선 없음 -- #53 (ii)와 같은 형태, 같이 두면 순환) | Y(엔진) / -(데이터) | E2·E3·E8 |
| **55** | `ud17-current-reuse-bulk`(v0.6, 결과 card -- UD-17e (ii)일 때만) | **UD-17e (ii) bulk = 자기 source**: current_reuse M9a·M18a(class-AB 배터리 pmos, vsb 0.825)와 UD-17d (i)이면 M2a·M2b(캐스코드 pmos, 0.9227)의 `bulk` 단자를 선언(**connectivity -- 사용자만**, F34). 엔진 쪽 선언 bulk 읽기는 **UD-17e 답이 #22 착수 전에 오면 #22의 DEC-61 몫**(승인된 엔진 card -- 소비자가 이 card라서 #22가 (ii)일 때만 그 몫을 넣는다, §5.4 #22). **(v0.7, S4) 답이 #22 병합 뒤에 오면 이 card가 엔진 몫(#22의 `bulk` 거부 해제 + `derive_vsb_from_nodes`의 선언 bulk 읽기)을 함께 맡는다**(원칙 기본안 -- 데이터 + 엔진 card, P3? = Y, 공유 코드 승인 §7.3). 매칭쌍 {M9a,M18a}·{M2a,M2b}는 같은 bulk 규칙(쌍의 한쪽만 바꾸지 않는다 -- 출처: topology `symmetry.matching_pairs` 선언, 두 쌍 모두 `current_forced: True`·`matching_sensitivity: ratio`, 3차 검토 HEAD 확인. 회로 해석이 아니라 선언 데이터). UD-17e (i)(bulk = vdd)이면 **이 card는 없다** -- 0.825·0.9227은 #27의 VS 0~1.8 V가 덮는다(P-30) | 데이터 정정 + E-INST 전후 | (d) 공동분석 확인표(회로도 body 연결) -- **(v0.8, S8) 출처 = topology 수정 승인 기록에 붙여 `docs/03-analysis/gain-budget-gmid-sizing-40-defect-fixes/`에 커밋한 판과 그 커밋 해시**([pack] §5 UD-17e는 초안 자료), (c) 해당 소자 θ* vsb = 0(축 안)·클램프·축 밖 조회 0, Vth·W 변화는 E-INST 차이표(DEC-40). 레이아웃 n-well 분리 면적은 이 Phase 판정 밖(기록만). **(v0.8, S5) 엔진 몫을 맡을 때(UD-17e (ii) 답이 #22 병합 뒤) -- #22 (ii)와 같은 계약**: (a) 합성 topology -- 선언 `bulk`가 source 넷인 소자(vsb 0)와 아닌 소자(vsb = abs(V(source) − V(bulk)))의 vsb(소자·넷 이름 무관, 이름을 바꿔도 같음), `bulk` 넷이 netlist 넷에 없으면 `SchemaRejectedError`, 거부 해제 전 base는 `bulk` 키를 거부(red), (c) `bulk`를 선언하지 않은 library 회로 무동작(CC-8 `noop_proof`, 발동 계수 0·산출물 동일) | **UD-17e (ii)**, 사용자 connectivity 수정, **#22**(하드), UD-17d (M2a·M2b 포함 여부). (v0.7) 엔진 몫을 맡으면 + #6(이미 #22의 조상)·공유 코드 승인 | -(데이터) / Y(답이 #22 뒤 -- 엔진 몫 포함) | E2·E8 |

### 5.11 조건부

| # | id | 조건 | 내용 |
|---|---|---|---|
| C1 | `theta-authoring-wire` 또는 `d4-delete-theta-authoring` | UD-7(U-A) 결과 | theta 작성 묶음 4함수 배선 또는 삭제. `propose_theta_kcl_gap_fill` 사이트(SD 3559·3561·3719)를 정리하므로 **#19의 선행** |
| C2 | `df09-area-blend` | D-1이 승인되지 않으면 | DF-09 `(2−α)A` 식 수정. 선행 없음(실패 클래스 미사용 -- TS4 red와 같은 대상이라 #5와 같은 묶음에서 순서만 정한다) |
| C3 = 49 | `b35-grammar-rails-arg` | UD-15 (2)=X | B34 인계 사이트 5~8·(v0.6) 10·14(도달 불가 분기) 삭제(10·14는 블록 내어쓰기 -- 블록 값 판정 계약 동반, §5.1 인계 표) + analog-grammar에 기본값 없는 `rails` 인자(`classify_nets(…, *, rails)`·`stack_edges(devs, *, rails)`, 나머지는 `imp.get(n) == RAIL_Z`), SD는 `meta["rails"]`(+#17 극성)를 넘긴다, CLI 경계로 이름 집합 가정 이동, lint 범위에 AG 추가, mid 레일은 UD-15 (3) 결과대로. oracle: (a) `prep_b34_b35_grammar.md` §3.4 합성 topology, (b) 레일 이름 바꾸기에서 `load_topology` meta **전체** 불변, (c) E-LIB 9/9·E-INST 2. 선행 #17, #46, #19 |
| -- | UD-8(U-B `find_diode_stacks` 묶음) 삭제 승인 시 | -- | 삭제 card는 **6a S1 card**(대체물인 S1 관계 엣지가 생기는 card)다. Phase 4에서 지우지 않는다(대체 전 삭제 금지) |

### 5.12 게이트 선행 card (이 Phase 밖 -- 인용만, 재서술하지 않는다)

v0.3의 #48(대상 정의·출력·redteam·승인 형태를 이 문서가 정함)은 **새 게이트 card의 인용으로 바꿨다**(검토2 B1, N9.4). 두 V3 card는 v3(1·2차 검토와 A1-b 정정 반영, 커밋용 확정 -- `v3_cards_revision_log.md` §5~§7)이고, 계약 문언·redteam 단계는 그 card가 정한다. redteam 번호는 Phase 3 v5 D-18 배정(33·34·35).

| # | card id(phase) | 무엇 | 판정 기준 변경의 성격 | 승인 | 이 Phase와의 관계 |
|---|---|---|---|---|---|
| -- | `20260930-v3-exempt-binding`(0.5, redteam 34) | V3 등가 변이 면제를 변이 id + def 해시에 묶음(해시 없는·다른 원소는 적용하지 않고 출력) | **강화**(면제 집합 축소) | 게이트 변경 승인 기록 1건(`target_kind: diff`) -- **A1-a 승인됨**(2026-10-01), 기록 초안 `approval_20260930-v3-exempt-binding.md`(diff_path 5), 커밋 대기 -- §7.3 | **P9·P10·P10b 뒤, #1보다 먼저**(A1-a). 묶는 해시 = def 원본(docstring·데코레이터 포함)의 `ast.dump` sha256(①의 대상 선택 해시와 분리). 기존 C8 면제 14원소는 더 적용되지 않는다(무손실 근거는 그 card). V4·V7 같은 부류 누수는 그 card가 백로그로 넘긴다(V4 면제를 test 함수 해시에 묶기 -- #21 V4 면제와 관계, §7.3) |
| 48 | `20260930-v3-changed-stmt-scope`(0.5, redteam 35) | V3 대상을 바뀐 def 안의 '바뀐 문장 + 감싸는 제어문 + 삭제 지점 바로 뒤 + **바뀐 이름을 같은 블록 뒤쪽에서 읽는 문장(반복문 본문이면 위치 무관)** + 바뀐 매개변수를 읽는 문장 + `early_return`'(+ 새 def 전체)으로 좁힘, 대상 밖 수는 `not_targeted`·`targets_by_def`로 출력 | **약화**(판정 범위 축소) | **A1-b = 선택지 2 승인됨 + A1-b 정정(T6 넓힘)**(2026-10-01). 승인 기록 초안 `approval_20260930-v3-changed-stmt-scope.md` 범위 설명에 "약화 승인"과 놓치는 것 ①~③(다른 블록·두 단계 이상·바뀌지 않은 문장의 기존 test 강도). 계획 N4.2 V3 칸은 `plan_tables_hash` 입력이 아니다(그 card 실측) -- v0.3 §9-7의 'plan_tables 승인'은 틀렸다 | 면제 묶기 뒤, #1 전, G1 전. **B26-1 대상 294**(승인 당시 228), B34 좁힌 범위 10, P9 실제 12(넓힌 T6 재측정 -- `v3_cards_revision_log.md` §6) |
| -- | `20260930-v7-registry-edges` = B33(0.5, redteam 33) | V7·V3 공유 그래프에 레지스트리 바인딩(R1, 바인딩 값의 문자열 상수는 간선 아님)·생성자 간선(R2)·dunder 속성 폴백 제거(R2'), V7 도달은 소스 파일만(R3) | V7: 거짓 FAIL 제거(소스 미도달 115 → 39) + 거짓 PASS(비운영 이름 폴백 누수 64 → 0) 제거. V3: 인벤토리 확대 **쌍 33,991 → 44,493(1.31배)**, 인벤토리 0 def 82 → 19, 중앙값 61 → 67(개정 card 사전 실측, 작성자 측정 -- 판정 수치 아님. v1 규칙의 79,809는 폐기) | 게이트 변경 승인 + **사용자 결정 Q1**(생성자 간선 범위 -- (v0.6) **결정됨: 승인 + Q1 (a) 호출 위치만**, 팩토리 모양은 거짓 FAIL → 면제 승인 처리) -- §7.3 '인지'. `review_b33.md` blocking 3건 **반영 완료**(`b33_revision_log.md`) | 권고 순서 B33 → G1(Phase 3 착수 전). 병합 뒤 부록 C '운영 도달' 열과 F17 '운영 도달 52'를 다시 잰다(§10.1-5). V3 인벤토리가 커지면 card별 V3 시간이 늘고, 새로 인벤토리에 든 test가 격리 복제본 기준 실행에서 실패하면 V3 ERROR다(§8.4) |

**합계**(v0.6): 이 문서가 계약을 정하는 card **49건** = #1((v0.9.2) phase 3, Phase 3 M card 전 -- A2·`20261001-b26-phase3-cards`) + #2~#44·#46·#47·#51(46건) + **UD-17 결과 card 2건(#53·#54 -- #44처럼 결정 결과가 내용을 정한다)**. 조건부에 **(v0.6) #55**(UD-17e (ii)일 때만 -- 아래 조건부 수 5)를 더했다. 인용만 하는 card 2건: #45(B34, (v0.9.2) phase 3), #48(V3 범위 게이트 card, A1-b로 확정). 조건부 **5건**(C1, C2, C3 = #49, #52, (v0.6) #55). 폐지 번호 50(#21로 흡수) -- 재사용하지 않는다. 한 문서로 둔다(N9.1).
(v0.4 합계: 47건 -- #53·#54가 없었다.)
**(v0.7)** 계약 card 수는 그대로 49, 조건부 5. **(v0.8)** 그대로(S2는 #23 범위 확장 -- 새 card 아님). card **B26pre**(`20260930-b26-pre-test-strengthen`, test-only -- (v0.9.2) phase 3)와 (v0.9.2) **backfill 결함 card**(`20261001-b26-backfill-interdig-final-audit`, red-green, phase 3 -- U-BF)는 #45처럼 **인용**만 하고 번호를 주지 않는다(§3.2 표 -- 계약은 그 card 그대로, #1의 착수 조건).

**card 단위 확인이 필요한 것**: #1은 크다(로드 경로/평가 경로 둘로 나눌 수 있다). #13은 §5.3 뒤 문단의 분할 규칙을 따른다.

---

## 6. DoD 표

auditor가 Phase 4 마지막 card 병합본의 격리 복제본 `<iso>`에서 실행한다. `PT` = `10-test-separation` §10 정의(`--gmid-phase=4`). **`PT`는 `<iso>/…/tests` 전체를 경로로 갖는다** -- 뒤에 파일·node id를 더해도 수집 범위는 전체 suite이고, 판정은 아래 '통과 기준'이 지정한 test의 결과로 읽는다(design 10 D4와 같은 관례, 4차 검토 m4). (v0.8, B1) `--gmid-dod` = `00-common` §9.3 'DoD 판정 실행 -- 표식 Phase가 현재 Phase인 케이스 전부 엄격'(xfail 표식이 남은 Phase 4 케이스는 XFAIL이 아니라 FAIL). `$PY` = `C:/Python314/python.exe -B`. 새 도구 경로는 해당 card가 만든다(이름은 초안 -- card 작성 전 test glob 충돌 grep).

| ID | N6.2 `4` 조건 | 명령 | 통과 기준 |
|---|---|---|---|
| E0 | DF마다 red-green | Phase 4 card마다 `.ai/verification/<id>.json`의 판정 유형·red 기록 | §5 card 전부 판정 기록 있음, red-green card는 base red + 병합본 green. N5.2에서 담당 Phase에 4가 있는 DF 전부가 card 또는 닫힘 기록에 대응 **[미확인: 판정 기록 필드 이름은 `00-common` §8.1 스키마에서 card 작성 때 확인]** |
| E1 | V8 도입(정본 실행 `fallback_events` 0) | 사이징 대상 4회로마다 하네스 정본 실행 → 산출물의 `fallback_events`(§10.1-2: 성공이면 `instance.json` 최상위, 실패면 실행 기록 JSON) | **4회로 모두** 키가 있고 빈 목록. 키가 없으면 FAIL(계측 미배선). two_stage·nmcnr가 #43 뒤 실패 레코드로 끝나도 실행 기록의 `fallback_events`가 비어 있어야 한다 |
| E2 | 사이징 대상 회로 실행과 전후 비교표 | base = **`P3D`**((v0.9.3, m4) 정의: Phase 3 DoD 측정 기록의 '대상' 커밋 -- Phase 3 design D-28의 `P2D`와 같은 정의 방식, 기록 경로는 Phase 3 design 확정본 DoD 절(§8.3 [미확인]). v0.9.2까지 여기서 'Phase 3 DoD 병합본'이라 부른 판과 같다. E11도 이 기호를 쓴다), head = Phase 4 마지막 병합본. 회로마다 하네스 정본 실행 결과를 §10.5 식으로 정규화해 비교 | 표가 판정 기록에 있고, 바뀐 항목마다 원인 card id와 DEC-40 승인 기록 id가 붙어 있다. two_stage·nmcnr는 base에서 `ValueError`(F15)이므로 비교 단위가 '결과 종류(θ* / 실패 클래스)·margin·실패 전 setup 양'이다((v0.8) margin = `normalized_margin` 값 -- #23 노드 충돌은 수, #43·#25는 `null`. 비교 규칙은 §10.5). (v0.4) folded·current_reuse도 #23(F27 conflicts)·#25(F26 축 밖) 뒤 실패 레코드로 바뀔 수 있다 -- 그 경우 같은 비교 단위를 쓰고 원인 card(#23·#25)와 DEC-40 기록을 붙인다. UD-17 결과로 해소되면 해소 전후 두 단(#53·#54·(v0.6) #55 행). UD-6 결과가 Phase 4 해소면 해소 전후 두 단 |
| E3 | IC11 2레일 케이스 PASS | **`PT --gmid-dod -rA <iso>/skills/analog-gmid-design/assets/tests/contracts/test_ic11.py`**((v0.8, B1) `--gmid-dod` 없이는 rail2가 비엄격 xfail이라 망가진 rail2가 XFAIL·맞는 rail2가 XPASS로 보여 판정할 수 없다 -- HEAD 실측 부록 A G2: 옵션 없음 = 3 xfailed, `--gmid-dod` = rail2 FAILED. 실행 범위는 `PT`대로 전체 suite) | `rail2` **PASSED**(`--gmid-dod` 실행에서 -- xfail 표식 없음 -- #21이 본문을 넣은 뒤 계속 PASS, §10.6의 결과 단위 불변), `rail3`·`reject` XFAIL(6a). 판정 기록에 대상 회로·평가점 θ·양별 tol_q·**판정 단위(성공/실패)**를 남긴다. **(v0.5) Phase 4 DoD에서는 성공 단위**(대상 회로 θ 평가가 끝남)여야 한다 -- 실패 단위는 card 중간 병합본에서만 허용(§10.6-0). 성공 단위가 되려면 #54(또는 #53)가 필요하다. (v0.6) #54는 UD-17d (i)이면 설계 변경(아래 반쪽 VDS 배분·출력단 VGS)이 함께여야 성공 단위를 준다(F33), #53은 UD-17c (iii)이면 성공 단위를 주지 않는다(F32). Phase 4 끝에 성공하는 SPECS 2레일 회로가 없으면 E3는 FAIL이고 N7 정정 요청(§9-17) |
| E4 | MG1 옛 키 거부 test PASS | **`PT --gmid-dod -rA <#20·#21 interface card의 node id 목록>`**((v0.8, S1) `-k "legacy"`는 HEAD에서 MG1과 무관한 `contracts/test_ts3_no_print_verdicts.py::test_target_set_includes_legacy_scripts` 1개를 골라 MG1 test 없이도 PASS -- 부록 A G2. design 20 E1의 `-k "dup_"` 함정과 같은 종류) | **수집된 목록 id 수 = 목록 수**(`-rA` 줄에서 목록의 id마다 PASSED 한 줄, 빠진 id = FAIL), 전부 PASS. 목록이 덮는 것: 계획 `supplies`, spec 스칼라 `vdd`, metric 인자 `supply_nets`(+`rail_nets`) 각각 `SchemaRejectedError`, 조용한 통과 합성 구현에서 test FAIL |
| E5 | DF-27 VS 축 밖 픽스처 거부 | **`PT --gmid-dod -rA <#25(와 #10) interface card의 node id 목록>`**((v0.8, S1) `-k "lut_axis"`는 HEAD에서 수집 0(exit 5) -- 나중에 이름이 겹치는 test가 생기면 E4와 같은 문제) | 수집된 목록 id 수 = 목록 수, 전부 PASS. 목록이 덮는 것: 축 밖 입력 → `lut_axis_out_of_range`, 클램프 0, 일부 후보만 축 밖이면 탐색 계속, 실행 수준 `SearchFailedError.detail`에 원인 보존(P-34) |
| E6 | U-27 옛 격자점 대조 기록 | auditor가 새 LUT와 옛 표본의 공통 격자를 열별 비교 → `grid_compare.json` | 기존 열 비트 동일, 아니면 원인 보고 + DEC-40 승인. 새 해시·VS 축 LOO 오차 기록 |
| E7 | U-30 전후 비교표 | #28: E-INST 동일, #29: self-test·사이징 대상 회로 비교 | `min_finger_w` 출처 = difftap.2 기록, 공정 기록 밖 PDK 사본 0, 바뀐 기준선마다 DEC-40 승인 |
| E8 | 성능 보고(N6.3) | `$PY <iso>/…/tests/tools/measure_search_perf.py --worktree <iso> --circuit <파일럿> --out <iso 밖>` | 마지막 동작 변경 card의 `perf.json` 존재, `status=ok`. **(v0.5) 파일럿 = `current_reuse_telescopic_ota`**(계획 N0.4 123행) -- #23 뒤에는 #54 없이 `status=failed`가 된다(F27). 그래서 E8은 #54에 걸린다. (v0.6) 그리고 #25 뒤 VS 축 밖(M9a·M18a 0.825, UD-17d (i)이면 M2a·M2b 0.9227)을 덮는 #27 또는 #55에 걸린다. 중간 card의 perf는 `status=failed`여도 기록으로 남긴다(판정 아님) |
| E9 | 무동작 증명(N6.3·DEC-47) | CC-8 뒤 card마다 `noop_proof.py` | card마다 `noop-<circuit>.json` PASS |
| E10 | DF-19 '운영부 레일 이름 리터럴 0' | `PT --gmid-dod -rA <#19 interface card의 node id 목록>` + `$PY <iso>/…/tests/tools/rail_literal_scan.py --root <iso>` **[파일 이름 초안 -- #19가 확정]** | (v0.8, S1) 수집된 목록 id 수 = 목록 수, 전부 PASS, 도구 exit 0, 발견 0. 면제 = §5.4 #19 면제 목록 그대로(UD-9·UD-15 결과로 정해진 항목만), 목록 밖 면제 0 |
| E11 | 전체 회귀·실패 규약 | **(v0.8, B1) 두 실행**: `PT -rA`(전체)와 `PT --gmid-dod -rA`(전체) -- 사용자 결정 A3(2026-10-01, Phase 2 E4를 `--gmid-phase=2`와 `--gmid-dod` 두 실행으로 고정)과 design 20 E4(`PT2` 전체와 `PT2 --gmid-dod` 전체)와 같은 형식. + E-LIB 재측정 + N3.14 대조 test. **(v0.9.2, P-37) E-LIB 재측정 = 선례 모양**(Phase 3 v8.3 E5·design 20 E4와 같다): `P3D`(E2 행 정의)와 Phase 4 마지막 병합본을 같은 경로에서 Phase 3 D-28의 `e_lib_p3.py` 한 사본으로 재고, **(v0.9.3, S2) 아래 'E11 빼는 키 표'의 `MASK_META_P4`** meta 키만 해시에서 빼서 그 표의 기대값과 **값 전체 정확 일치**로 따로 판정, topology 데이터를 바꾼 회로(#53·#54·#55)는 그 card 차이표 + DEC-40 기록으로, 나머지는 해시 같음. ~~빼는 키 목록은 card 계약에서 유도해 DoD 브리핑에 박는다~~ **(v0.9.3, S2) 목록과 출처는 아래 표가 정본(판정 기준)이다 -- DoD 브리핑은 옮기기만 한다**(#21은 실측으로 몫 없음) | **두 실행 모두 실패 0**(첫 실행은 다른 Phase 표식의 xfail이 XFAIL로 남아도 됨, 둘째 실행은 Phase 4 표식 케이스가 전부 엄격), E-LIB 9/9 로드 + (v0.9.2) 위 비교에서 목록 밖 차이 0 + **(v0.9.3, S1) 빼낸 키 계약 판정 FAIL 0**(아래 표 판정 (iii)·(iv)) |

**E11 빼는 키 표(v0.9.3 -- 7차 검토 S1·S2. 판정 기준이다: Phase 3 D-28 (e)와 같은 지위)**. `P3D` 뒤 Phase 4 card가 계약으로 바꾸는 `load_topology` meta 키만 해시에서 빼고, 빼낸 값은 아래 출처의 기대값과 **값 전체 정확 일치**(`==` -- 계약 밖 필드·키가 하나라도 있으면 FAIL)로 판정한다. 목록이나 출처를 바꾸려면(card 재작성, 새 card가 meta를 바꿈, 실측이 바뀜) **design 개정(승인 대상 diff)**이 필요하다 -- auditor·DoD 브리핑 작성자는 늘리지 않는다(해시에서 빼는 키를 늘리는 것은 판정을 약하게 하는 쪽이다). 이 표는 승인 질문 UD-0 '기준에 닿는 것' (c)가 덮는다.

`MASK_META_P4 = ("device_roles", "ports", "rails")` -- `e_lib_p3.py <root> <out.json> device_roles ports rails`(그 사본은 키 0개 이상을 받는다). E-INST 쪽 빼는 키는 없다(E-INST 비교는 E2 몫).

| 빼는 키 | 바꾸는 card | 기대값 -- HEAD `masked.<키>`(회로 c마다, 정확 일치) | 출처(엔진 출력에서 채우지 않는다) | `P3D` `masked.<키>` |
|---|---|---|---|---|
| `rails` | #17(B26-2, §10.3) | `{"__dc__": "RailDeclaration", "nets": NETS(c), "polarity": POLARITY_P4[c]}` -- 키는 정확히 이 셋 | `NETS(c)` = **`P3D` library** `<c>.topology.json` `supply_nets`의 정렬 집합(`git -C "$ISO" show "$P3D:skills/analog-gmid-design/assets/library/<c>.topology.json"` -- HEAD에서 읽으면 `P3D`~HEAD 사이 `supply_nets` 변경이 양쪽에 같은 값으로 들어가 걸리지 않는다, Phase 3 v8.3 m1과 같은 이유). 그 사이 `supply_nets`를 바꾸는 card(#53·#54·#55)가 있으면 그 회로는 그 card 차이표의 값. `POLARITY_P4` = 아래 고정 표 | `{"__dc__": "RailDeclaration", "nets": NETS(c)}` 정확 일치(B26-1 계약 1 -- Phase 3에서 들어온 값. 아니면 `E11 INVALID`: 비교 시작 판이 전제와 다르다) |
| `ports` | #47(B37a) | `P3D` 값에 #47 card v2 기대 차이표를 적용한 값 -- 표 밖 차이 0, 표 안 값 정확 일치 | #47 card v2 계약(기대 차이표 -- UD-18 Q1·Q2 승인 대상, card 계약 9: 착수 시 재측정해 다르면 멈춤)과 `P3D` library `ports` 선언 | 기준값(그대로 읽음) |
| `device_roles` | #47(B37a) | 위와 같은 방식 | #47 card v2 기대 차이표(UD-18 Q1 승인 대상) | 기준값(그대로 읽음) |

`POLARITY_P4`(9회로, §10.3 구조 규칙 결과 -- 출처 `b26_decision_table.md` §1.2, `cd64170` 측정: 소자 이름·레일 이름을 보지 않고 소자 종류와 source 단자만으로 얻음, CONFLICT 0, hi·lo 각 하나):

| 회로 | polarity |
|---|---|
| common_gate_amplifier | vdd = hi, gnd = lo |
| current_reuse_telescopic_ota | vdd = hi, gnd = lo |
| folded_cascode | vdd = hi, gnd = lo |
| ngcc_3stage_ff | vdd = hi, gnd = lo |
| nmcnr_amplifier | vdd = hi, vss = lo |
| pushpull_follower_buffer | vdd = hi, vss = lo, agnd = mid |
| sf_pushpull_output_opamp | vdd = hi, vss = lo, agnd = mid |
| two_stage_ota | vdd = hi, gnd = lo |
| two_stage_ota_sf | vdd = hi, gnd = lo |

**#17 card 작성 전 조건(이 표가 기준이 되려면 -- 작성자≠검증자)**: (1) 판정 쪽 독립 구현으로 `P3D` library에서 이 표를 다시 잰다 -- §10.3 구조 규칙(선언 레일이 PMOS source로만 = hi, NMOS source로만 = lo, 둘 다 아님 = mid, 둘 다 = 거부)을 topology JSON의 `supply_nets`·소자 종류·source 단자만 읽어 계산(엔진·#17 코드 import 없음). `cd64170` 표와 다르면 이 표를 고치는 design 개정 (2) UD-1 답이 (C)가 아니면(전 회로 `supply_roles` 필수) 출처 = `P3D` library `supply_roles` 선언 그대로(선언이 정본, 구조 규칙은 모순 거부 게이트) -- 표를 그 선언으로 바꾸는 design 개정. (C)이고 예외 회로가 `supply_roles`를 선언하면 그 회로는 선언값 (3) `e_lib_p3.py` 정규화가 `polarity` 값을 싣는 모양 확인 -- `dict`면 `{"__dict__": [["\"<넷>\"", "hi"], …]}`(키 정렬), `MappingProxyType` 같은 비 `dict` Mapping이면 `__repr__` 문자열이 되어 비교가 표현에 묶인다 **[미확인: #17 구현 형태]** -- 기대값 식의 직렬화 모양을 card interface에 고정한다. 셋 중 하나라도 없으면 #17 card를 쓰지 않는다(엔진 출력으로 기대값을 채우면 작성자=검증자 순환).

판정(DoD 블록은 Phase 3 §10 E5 블록과 판정 python을 따라 쓴다 -- 이 표가 그 `MASK_META`·계약값 자리): (i) **동등 확인(먼저, `P3D`)**: `e_lib_p3.py`(인자 없음) 출력이 더한 두 키 밖에서 `e_lib.py`와 같다 -- 아니면 `E11 INVALID` (ii) `e_lib_p3.py … device_roles ports rails` 결과 `hash`가 `P3D`와 HEAD에서 같고 회로 집합이 같고 HEAD에서 회로마다 `load` 성공(topology를 바꾼 회로는 위 E11 행대로 그 card 차이표 + DEC-40) (iii) `P3D` 쪽 `masked.rails`가 위 표 `P3D` 열과 정확히 같다 (iv) 회로마다 HEAD `masked.<키>`가 위 기대값과 `==` -- 아니면 `E11 E-LIB <키> 계약 FAIL <회로>`. 근거 실측: 계약 밖 필드(`polarity`)를 더한 시제품을 '성분만 보는' 식(Phase 3 v8.2)은 PASS, 정확 일치 식(v8.3)은 FAIL(`p3_scripts/p3v83_judge_scenarios.out.txt` p4). #21 실측에서도 같은 구멍이 재현됐다(`p4_card21_rails_measure.md` §4.2 x4: `rails` 필드 집합을 보지 않는 판정 PASS -- #21은 빼는 키가 없으므로 해시 같음 판정이 잡는다).

---

## 7. 사용자 결정 (진짜 사용자 몫만)

**UD-0 이 design 승인(DEC-51)**: 아래 '원칙 기본안'(§7.2)과 계획 정정 요청(§9)을 함께 덮는다.

v0.2 대비: UD-2(교류접지)·UD-3(`supplies_v` 값·시점)은 계획이 이미 정한 것이라 질문에서 뺐다(→ P-13·P-14, 남는 것은 §7.4의 DEC-40 기준선 승인과 §7.3의 U-26 (a) 확인 기록). UD-11·UD-12는 '발생 시 건별 DEC-40'이라 §7.4로 옮겼다. UD-13은 decision이 아니라 게이트 변경 card #48이다. B35 방식(v0.2 P-11)은 UD-15에 묶었다.

v0.3 대비(검토2 S3·S12·B1): **UD-14는 승인됐다**(A2, 2026-10-01 "승인 (Recommended)", 기록 id `20260930-b26-before-phase3` -- 계획 정정 커밋과 함께 쓴다. B34 Phase 3 전 착수도 같은 기록이 덮는다). 표에서 지우고 §7.3에 기록 id로 둔다. **A1(V3 범위)**은 Phase 4 card 전부의 V3 판정 범위를 정하므로 이 표에 올렸고, 이 문서를 쓰는 동안 **결정됐다**(선택지 2). **UD-17**(정본 실행 두 회로의 노드전압 충돌 공동분석)은 v0.4 실측(F26·F27)으로 새로 생겼다.

v0.5 대비: **UD-17을 UD-17a~e로 나눴다**(`prep_ud17_f26_f27.md` §5.1 -- 회로별 원인 분류). 원인이 원칙으로 정해지는 부분은 P-26~P-32로 확정했다. **UD-18**(B37a 승인 질문 Q1~Q3)을 올렸다 -- v0.4는 B37a의 E-LIB 차이를 '확인 사안'으로 적었으나 card v2 검토(`review_b37a.md` S1)가 동작 변경 수용·`ports` 근거 확인을 사용자 승인 사안으로 정정했다. **A1-b 정정**(2026-10-01, T6 넓힘)을 결정됨에 더했다.

v0.6 대비: UD-17a~e 문구를 공동분석 자료([pack])로 정밀하게 고쳤다 -- UD-17a는 혼자 #53을 열지 않고 UD-17c와 함께 연다(17c에 **입력 CM**을 더함), UD-17d에 선택지 (i)~(iii)과 (i)의 설계 변경 몫을 적고, UD-17e는 UD-17d (i)이면 M2a·M2b로 넓어지며 (ii)는 connectivity 변경 + 엔진 배선(#22)이 필요함을 적었다. B33(승인 + Q1 (a))을 결정됨으로 옮겼다. B26-1 card v4의 U3·U4·U5(#1 착수 조건)를 대기 목록에 더했다 -- (v0.7) U3 질문은 B26pre card가 대체했다(`b26_1_survivor_question.md`는 만들어지지 않았다).

v0.7 대비(3차 검토 S6): **확정 순서**(`user_decisions.md` 2026-10-01 "card 순서")를 결정됨에 더했다. B26-1 U3을 **B26pre**(`draft_b26pre.spec.md`)의 질문으로 바꿨다 -- card U1(원칙 기본안 '면제 없이 test 보강'의 사용자 확인)은 확정 순서 원문 "B26-1(앞선 test 보강 card 포함)"이 card의 존재·위치를 덮는다(기록 문구로 쓸지는 오케스트레이터 확인), card U3(순서)는 결정이 아니고 확정 순서와 같다. **새로 늘어나는 진짜 사용자 결정은 B26pre U2(등가 후보 9개 처리) 하나**다 -- 권고 (a) A1-a 묶기 면제는 판정 약화라 사용자 몫이다. 그 밖의 v0.7 변경(S1~S5·S7)은 원칙 기본안이나 오케스트레이터 정정이다. §9-19는 닫혔다.

v0.8 대비(4차 검토): 새 사용자 결정 **없음**. **S2 margin**은 원칙 기본안으로 닫았다 -- `normalized_margin`(CC-9)을 #23으로 앞당긴다(§9-22 결정됨, UD-0이 덮음. 근거: 계획 749행의 '`null` ≠ 빠뜨림'을 지키는 유일한 길이고, 함수는 `00-common` §7.2에 이미 정의된 한 줄이라 새 판정 규칙이 아니라 시점만 바뀐다. 만들면 배선 -- 첫 생산자 #23이 같은 card에서 부른다). 대안(계획 749행에 'CC-9 전에는 `null` + 위반 크기·분모 기록' 한 줄)은 승인 질문의 둘째 선택지로 남긴다. **B1 E3 `--gmid-dod`**는 사용자 결정 A3의 선례를 따른 판정 명령 정정이라 새 결정이 아니다. Phase 3 v7 D-27(S4)은 Phase 3 design 쪽 결정(그 UD-0)이고 이 문서는 따른다. B26-1 survivor 질문(`b26_1_survivor_question.md` Q1)과 B26pre U2는 같은 결정(등가 후보 처리)의 두 문안이라 하나로 센다(§3.2 #1 (5)).

v0.9 대비(5차 검토): 이 문서가 새로 만드는 사용자 결정은 **없다**. (1) N-S1(앞당김 경로)과 N-S2(vsb `tol` = 비트 동일, `node_tol` 명시 전달)는 원칙 기본안으로 닫았다(UD-0이 덮음 -- §7.2 P-35·P-36). (2) 대기 목록을 다시 뽑았다(`pending_questions.md`·`b26_backfill_question.md`·`b26pre_revision_log.md` v2): **B26pre U1은 원칙 기본안**(결정 아님 -- card v2, 기록 확인도 필요 없음), v0.7~v0.8의 'B26pre U2 = 등가 후보 9개'는 **U-BF**(`interdig_ok` backfill 불일치 -- 결함으로 고칠지, 사용자) **+ U2-a**(SR 11802 등가 면제, B26-1 V3를 N2d로 잴 때만)로 바뀌었다, **Q-B34-PHASE**(B34·B26-1·b26pre card `phase: 2` → `3` 여부, 기본안 3)가 새로 생겼다. 둘 다 이 Phase 승인 질문과 독립이고 #1(과 B34·B26pre)을 막는다. Q-B34-PHASE 답은 이 문서 card의 간선·판정을 바꾸지 않는다. **(v0.9.1, 6차 검토 m-2 정정)** v0.9의 'card phase는 V 검사 N/A 허용에만 쓴다'는 불완전했다: `merge_gate.rule10_phase`(532~549행)는 card phase를 현재 Phase와 대조하지 않고 V 검사 N/A 허용(도입 Phase보다 앞)에 쓰지만, `merge_gate.py`는 card phase를 두 곳에 더 쓴다 -- (i) V1 명령의 `--gmid-phase=<card phase>` 강제(1009~1010행 `v1_command_check`, 1213행에서 `phase=card["phase"]`로 호출), (ii) 같은 Phase의 기록된 card끼리 `activated_ic_case`를 합친 엄격 집합(1042행 `strict_set` -- 1210~1211행, old 트리 conftest에 `--gmid-phase` 옵션이 있을 때). 그래서 Q-B34-PHASE 답에 따라 **B34·B26-1·b26pre(와 backfill) card의 V1 실행 옵션과 엄격 집합**이 바뀐다. 이 문서 card는 phase "4" card끼리만 엄격 집합을 합치므로 판정이 같다(부록 A H6). 이 문서에서 바뀌는 것은 'phase 2' 표기 문장뿐이다(§9-19).

v0.9.2 대비(v0.9.1 뒤 결정 반영): 이 문서가 새로 만드는 사용자 결정은 **없다**. 대기였던 것이 모두 닫혔다 -- **U-BF**(결함으로 고침, 기록 `20261001-b26-backfill-interdig-fix` -- backfill card를 B26pre 뒤·B26-1 앞에), **Q-B34-PHASE**(phase 3 + 정정 기록, `20261001-b26-phase3-cards`), B26-1 **U3**(정리 2줄 + 면제 1, `20261001-b26-v3-equiv-range` -- ~~K 뒤~~ (v0.9.3) 1차 시도 K1 뒤·2차 시도 착수 전)·**U4**(`20260930-b26-b40-reason-key`)·**U5**(`20261001-b26-p9-signature-update`), **Q-P2DOD-E2**(문구 정정, `20261001-p2dod-e2-wording` -- 이 Phase 몫은 #30의 문서 정정). U2-a는 N2d를 쓰지 않아 소멸했다. v0.9.1 'm-2 정정'의 '엄격 집합도 바뀐다'는 틀렸다 -- phase 2·3 엄격 집합은 둘 다 빈 집합이라 같고(`review_b26_final.md` F2), 바뀌는 것은 V1 `--gmid-phase=` 토큰·Phase DoD 집계·A2 ③ 문구뿐이다. 원칙 기본안 **P-37**(E-LIB 비교 = 선례 모양, §6 E11·#17)을 더했다(Phase 3 v8.2 E5가 고른 사용자 선례 `20260930-phase2-e4-baseline` 모양을 따른다 -- 새 결정 아님).

v0.9.3 대비(7차 검토·#21 실측 반영): 새 사용자 결정은 **없다**. 다만 판정 기준을 질문에 드러냈다 -- E11에서 해시에서 빼는 meta 키 목록과 그 기대값 출처(§6 'E11 빼는 키 표')는 Phase 3 D-28처럼 사용자 몫 기준이라 UD-0 '기준에 닿는 것' (c)로 옮겼다(v0.9.2는 원칙 기본안 P-37 예시 끝에 두고 목록은 DoD 브리핑에 맡겼다 -- 7차 검토 S2). #21 [미확인]은 실측으로 닫혔다(빼는 키 없음). B26-1 U3 면제 기록 시점은 card의 '두 번 시도 절차'(1차 시도 K1 뒤·2차 시도 착수 전)를 인용한다. Phase 3 UD-0 (c)는 아직 사용자 답 전이고 P-37은 그 답과 무관하다(§7.2 P-37 근거).

**결정 상태 요약(v0.9, `user_decisions.md`·`pending_questions.md`·`b26_backfill_question.md` 대조 -- v0.8에서 B26pre 행 갱신, U-BF·Q-B34-PHASE 추가, N-S1·N-S2 기본안 추가. (v0.9.2) U-BF·Q-B34-PHASE·U3~U5·Q-P2DOD-E2를 결정됨으로, P-37 추가)**

| 상태 | 항목 |
|---|---|
| 결정됨 | A1-a(면제 묶기), A1-b(N2) + A1-b 정정(넓힌 T6), A2(= UD-14, 기록 `2d58fd8`, 계획 정정 `8356c1e`), A3(Phase 2 E4 -- 이 Phase 무관), Phase 2 D1·D2, (v0.6) B33 게이트 변경 승인 + Q1 "(a) 호출 위치만"(생성자 간선은 `Cls(...)`·`raise Cls`에서만), **(v0.7) card 순서 확정(2026-10-01)**: P10b → Phase 2 DoD → 34 → 35 → B34 → B26-1(앞선 test 보강 card B26pre 포함) → B33 → Phase 3(card 묶음 -- 실제 순서는 Phase 3 design), B34·B26-1은 Phase 2 DoD N6.3 목록 밖 **(v0.9.2)** U-BF "결함으로 고침"(기록 `20261001-b26-backfill-interdig-fix`), Q-B34-PHASE "phase 3 + 정정 기록"(`20261001-b26-phase3-cards`), B26-1 U3 "정리 2줄 + 면제 1"(`20261001-b26-v3-equiv-range`, (v0.9.3) 1차 시도 code 커밋 K1 뒤·2차 시도 착수 전), U4 "추가 승인 1건"(`20260930-b26-b40-reason-key`), U5 "갱신 승인"(`20261001-b26-p9-signature-update`), Q-P2DOD-E2 "문구 정정"(`20261001-p2dod-e2-wording` -- 이 Phase 몫 #30 문서 정정) |
| 대기 -- 이 Phase card를 막음 | UD-1(#17·#19), UD-4(#37), UD-5(#31), UD-6(#44), UD-7(C1·#19), UD-9(#19), UD-15(#46·#17·#49·#19·#52), **UD-17a + UD-17c(공동) + UD-17b(#53)**, **UD-17d(#54 → E3·E8)**, **UD-17e(#55 유무, #22·#55의 `bulk` 엔진 몫 위치)**, **UD-18(#47)** |
| ~~대기 -- Phase 3 전 card를 막음~~ **(v0.9.2) 없음** | v0.9.1 행의 U-BF·Q-B34-PHASE·B26pre U2-a·B26-1 U4·U5는 모두 닫혔다(위 결정됨 행 -- U2-a는 최종 V3 규칙이 N2d를 쓰지 않아 소멸). 네 card(#45·B26pre·backfill·#1)에 남은 것은 card 머리 `phase: 3`·`approval` 줄 개정과 승인 기록 커밋(오케스트레이터)뿐이다. ~~B26pre U1~~(v0.9: 원칙 기본안), ~~B26pre U2(등가 후보 9)~~(v0.9: U-BF + U2-a로 바뀜 -- v0.9.2 둘 다 닫힘) |
| 대기 -- 이 Phase 밖 card를 막음 | UD-8(6a S1), UD-10(7b), Phase 3 D-19(v6에서 따로 묻는 질문 -- `rail_declaration` 모듈, #1·#47 모듈에 전파) |
| 원칙 기본안(UD-0이 덮음, v0.8·v0.9) | S2 margin = `normalized_margin` #23 앞당김(§9-22 결정됨, `00-common` **§3.3** 표((v0.9, m-1) v0.8의 '§3.2'는 오기 -- 109행은 94행 '### 3.3 이 문서 자신의 분류' 아래)·§7.2·§13·§14 CC-9 행·§18.1·§18.2 문구 정정 diff와 **계획 N9.1 1158·1159행**(v0.9, N-S3 -- 1159행 `50-failure-cache` 행에서 CC-9 제거, 1158행 `40-defect-fixes` 행에 CC-9 추가. (v0.9.1, 6차 검토 m-1) v0.9의 이 칸은 1158행을 빠뜨렸다)을 UD-0 승인 diff에 포함 -- 줄별 문안은 §9-22), S6 `propagate_node_voltages` 기본 인자 제거(#23)와 노드 tol_V 대응 기본안(§9-25 계획 한 줄), S7 #14 θ* 위치 = 실행 기록 JSON, **(v0.9) P-35** #2·#3·#4·#17·#18 F2 뒤 단일 경로(N-S1), **P-36** 노드전압 사슬의 vsb 비교 = 비트 동일·`node_tol` 명시 전달(N-S2 -- (v0.9.1, R6-S1) current_reuse 정본 θ* 마지막 자리 변경, DEC-40은 §7.4 건별), **(v0.9.2) P-37** E-LIB 비교 = 선례 모양(P3D 대 Phase 4 마지막 병합본, card가 계약으로 바꾸는 meta 키만 따로 -- §6 E11·#17) |
| 사용자 작업(결정 아님) | `install.py` `SKILLS`에 `"analog-grammar"`(#45 병합 선행) |

### 7.1 결정 항목

| ID | 결정 | 권고(준비된 기본안) | 왜 사용자 몫인가 | 막는 card | 결정 자료 |
|---|---|---|---|---|---|
| **UD-1** | **D1 레일 극성** | **(C) 구조 규칙 기본 + 선택 필드 `supply_roles`(예외 회로만, §10.3)**. 규칙·게이트는 §10.3. library 9/9 규칙으로 판정 → 파일 수정 0 [prep] | 회로 해석 규칙(공동분석) | #17, #19 | `b26_decision_table.md` §1·§3 |
| **UD-4** | **U-04 픽스처/정본 구분** | 계획 기본안: spec에 `origin: canonical \| fixture` 필수 | 계획이 사용자 결정으로 지정(N7.2) | #37 | 계획 1079행 |
| **UD-5** | **U-05 비단조 곡선 이분 역산** | 계획 기본안: 단조 구간별 근 전부 반환 + 호출자 선택 규칙 명시 | 계획이 사용자 결정으로 지정 | #31 | 계획 1080행 |
| **UD-6** | **U-09 / I-C11 해소 방식**(§11) | 선택지 (A) 계획 정정: Phase 4는 #43 실패 명시화까지, 해소는 DEC-70(AC → DC 되먹임)·DEC-71(기둥 조립)을 구현하는 Phase로 옮긴다(U-09 재결정 + xfail 3건 만료 Phase 변경) / (B) DEC-70의 부분을 Phase 4에 선행 구현(엔진 규칙, 계획 개정) / (C) 회로별 topology 선언 정정(공동분석, WP-07). 회로마다 다를 수 있다. **권고: #43은 원칙상 무조건. nmcnr는 (C)부터**(엔진 메시지가 "선언되지 않은 소자/수동소자가 있거나 vertical_stack_id 선언이 실제 직렬 경로와 다르다"고 선언 쪽을 가리킨다 -- F15), **two_stage는 (A)**(원인이 compensation의 AC 결정 VDS와 DC KVL 불일치 -- 세션41에 사용자가 "DC/AC 조율 없이는 못 푸는 문제"로 기록, 그 일반 규칙이 DEC-70이고 계획 상태 '미구현'). 이 권고는 회로 해석(C)과 계획 범위(A·B) 판단을 포함하므로 결정은 사용자 몫이다 | 회로 해석·topology connectivity(WP-07), 계획 N7 U-09 재결정 | #44, E2 | §11, F15 |
| **UD-7** | **보류 행 U-A: theta 작성 묶음** | **배선** | 회로 해석 규칙 + topology 데이터 | C1, #19 | `prep_deferred_rows.md` §3.3 |
| **UD-8** | **보류 행 U-B: `find_diode_stacks` 묶음** | **삭제**. 삭제 card는 6a S1 card(§5.11) | ★ diode 정의(공동분석) | 6a S1 | 같은 문서 U-B |
| **UD-9** | **보류 행 U-C: `find_differential_and_mirror_forks`** | **6a ★ 공동분석까지 유지(비운영 면제)**, #19 면제 목록 E-b | ★ diffpair/mirror 정본(공동분석) | #19 | 같은 문서 U-C |
| **UD-10** | **보류 행 U-D: `check_mirror_symmetry` 묶음** | **7b I-A13의 바탕으로 배선**, 7b까지 미배선 면제. 기존 U-02 승인 3항 번복 | 기존 승인과 충돌 | 7b | 같은 문서 U-D |
| ~~UD-14~~ | **결정됨**(A2 승인 2026-10-01, 기록 `20260930-b26-before-phase3`) -- §7.3 | -- | -- | -- | `user_decisions.md` |
| ~~A1~~ | **결정됨**(2026-10-01, `user_decisions.md`): A1-a 면제 묶기 승인, A1-b **선택지 2(N2, def 머리 변경은 T3 (b))**, **A1-b 정정 "규칙을 안내에 맞게 넓힘"**(T6 = 같은 블록 뒤쪽에서 바뀐 이름을 읽는 문장 전부, 반복문 본문은 위치 무관 -- 놓치는 것을 '다른 블록·두 단계 이상'으로 한정) -- 범위 축소 = 기준 약화이므로 사용자 결정이었다(메모리 '작성자≠검증자', design 05 §2 판정 기준 소유 = 사용자). 승인 기록 2건은 §7.3 | -- | -- | #1 경로 확정(§3.2, B26-1 대상 294) | `draft_v3_decision_question.md`, `v3_cards_revision_log.md` §5·§6 |
| **UD-15** | **analog-grammar 묶음 결정 -- (1) 소속·게이트 편입, (2) B35 처리 방식, (3) 선언된 mid 레일의 grammar 매핑** | (1) **(a) 별도 skill + gmid 게이트 편입**. (2) **X(analog-grammar 확장)**: (1)이 (a)면 게이트·경로표 승인이 어차피 필요해 Y의 비용 이점(경로표 개정 불필요)이 사라지고, 아래 비교표에서 X만 DEC-62와 충돌하지 않는다. (3) **공동분석 항목**: 기본 제안은 "선언 레일은 극성과 무관하게 grammar에서 레일(`RAIL_Z`)로 보고, `SUPPLY`/`GROUND` 라벨은 hi/lo만 받는다(mid는 라벨 없음)" -- 사용자 확인 필요 | skill 경계·공유 설정, 판정 표 개정, **레일 수 상한 여부(DEC-62)와 교류접지 넷의 grammar 역할(회로 해석)** | #46, #17, #49, #19, #52 | `prep_b34_b35_grammar.md` §2.3·§3.2·§5, 아래 비교표 |
| ~~UD-17~~ | **(v0.5) UD-17a~e로 나눔**(아래 다섯 행). v0.4 기본안 (i)(#23은 계획대로, E-INST 변화는 기대 차이표 + DEC-40)은 P-26·P-27로 확정, (iii)(IC11 우선순위 current_reuse → folded)은 §10.6-0에 유지·보강 | -- | -- | -- | `prep_ud17_f26_f27.md` |
| **UD-17a** | **folded M1·M2 선언**: (1) kind를 nmos로(NMOS 입력 폴디드), (2) pmos 유지 + source/drain 교환(X·Y = source), (3) 원문(Maloberti p.34)이 정말 pmos 입력이고 꼬리를 다른 곳에 둬야 한다(거울상 연결 -- 여러 소자 connectivity 변경) -- 중 무엇인가. **(v0.6) 이 답만으로는 #53이 열리지 않는다**: 극성을 고쳐도 X·Y 충돌은 1.2 V(tail 컬럼 공백)로 남는다(F32 F1·F2) -- UD-17c와 함께 답해야 한다 | **기본안 없음(판단 자료만)**: `tail`에서 KCL 불가(M11 nmos sink와 pmos M1·M2가 모두 전류를 빼감), feed `r_split_M1_M2`와 `kcl_fold_M6`(I6 = I1 + I3)의 M1 전류 방향 모순, θ*에서 I6 = 1.0 µA(NMOS 입력 교과서 식이면 I3 − I1 = 0.5 µA), pmos가 gm/ID 17.5로 켜지려면 게이트 약 −1.04 V(레일 밖, SPICE), 연결 패턴이 NMOS 입력 폴디드 전형. (v0.6) (1)·(2)의 노드값은 같다(F32). (2)는 source가 고임피던스 폴딩 노드에 붙어 교과서형 입력단이 아니다 | **connectivity·kind는 사용자만 고친다**(메모리 'topology.json이 유일한 소스'), 회로 해석 | **#53(UD-17c와 공동)**, folded의 F26·F27 해소 전부, folded를 IC11 대상으로 쓰는 것 | [pack] §1.1·§1.2·§2.3·§5, [ud17] §2.1 (a)·§3.1 (추적 md는 쓰지 않음 -- B47) |
| **UD-17b** | folded `kcl_fold_M5`·`kcl_fold_M6` 부호(I6 = I3 − I1인가) -- UD-17a 결과를 따른다 | UD-17a 답에서 KCL로 유도(공동분석 확인 뒤 Claude가 메타데이터 갱신 -- 메모리 '국소 메타데이터는 바로, 단 회로위상 해석은 공동분석'). (v0.6) 교과서형이면 I6 = I5 = 0.75 − 0.25 = 0.5 µA로 M5~M10 전류가 절반 -- W·gain·pm·power 재계산(미측정). M1·M2 role(`headroom_role: cascode`·`gm_id_role: matching`·`fold_group: g_tail`)이 입력쌍과 맞는지도 같은 공동분석 | 메타데이터지만 전류 방향 해석이 회로위상 해석이라 공동분석 | #53 | [pack] §2.4 |
| **UD-17c** | folded 컬럼 공백 **세 개**를 어디서 정하나 -- (v0.6) **tail 컬럼 1.2 V(입력 CM: tail = Vin,cm − VGS1)**, Y 컬럼(Vg9) 0.5 V, 출력 컬럼 1.0 V: (i) 외부 DC(`bias3` 전압·출력 CM·입력 CM)를 **선언**한다 -- 선언할 필드가 지금 없어 새 필드 + 엔진 해석(공유 코드, 승인)이 필요하고 값은 사용자 스펙 (ii) 엔진이 fold_group 컬럼 KVL을 **푼다** (iii) 두고 기본안대로 멈춘다(#23 SEAL, folded 거부) | 기본안 없음. 판단 자료: 실제 회로에서 Vg7 = VGS9 + VGS7 ≈ 0.9 V(아래 다이오드가 정함), Y = V(bias3) + VSG5, out = 출력 CM, tail = Vin,cm − VGS1 -- 모두 선언 밖. 엔진 우회(SR 7507~7563) 주석이 KVL 불일치를 인정. (ii)는 외부 DC 없이 해가 하나로 안 정해지는 컬럼(출력 CM)이 남는다. **M7 vsb는 Vg9를 어느 경로가 정하느냐에 따라 0.95/0.45**(F32) -- (i)·(ii) 답이 그 경로를 정한다. 엔진 갈래는 계획 개정(DEC-70·71 근처, UD-6 (B)와 같은 종류) | 선언 대 엔진 규칙 = 회로 해석 + 계획 범위, 외부 DC 값 = 스펙 | **#53(UD-17a와 공동, 갈래 결정)** | [pack] §2.2·§2.5·§5 UD-17c |
| **UD-17d** | **current_reuse Vom1·Vop1 DC를 무엇이 정하는가**: (i) 출력단 VGS 0.677 V가 의도 -- 그러면 아래 반쪽 M3a·M4a·M5(최소합 0.9 V)를 0.677 V에 넣는 **설계 변경**(M4a vds·M5 vds·M3a vds 배분 또는 출력단 VGS)이 필요하다. 컬럼 분할 메타데이터만이면 M5 vds 0.0273 V(포화 밖 추정, 미측정 -- F33) (ii) 컬럼 배정 0.9 V가 맞음 -- M16·M26 VGS 0.9 V(compensation gm/ID 18.0과 충돌, class-AB 바이어스 재계산) (iii) 다른 것(첫 단 CMFB 등)이 정함 -- 회로도 근거로 선언 위치 결정. (i)·(iii)에는 엔진의 교차 그룹 노드 구속 갈래도 있다 | 기본안 없음. 판단 자료: 컬럼(`diffpair_branch_a`)은 0.9 V를 함의, `M10.vds_match_vgs_of = M16`(물리적으로 맞는 구속)은 0.6773 V, 네 충돌이 모두 이 0.2227 V의 전파, 지금 CMFB(M36~M40)는 M7 게이트(첫 단 위쪽 꼬리)를 움직인다. **(i)이면 M2a·M2b vsb 0.9227이 진짜 축 밖이 되어 UD-17e가 M2a·M2b로 넓어진다**(F33) | 회로 해석(Vom1을 CMFB가 정하나 출력단이 정하나) + 설계 변경 여부 | **#54**, **Phase 4 DoD E3(성공 단위)·E8(파일럿)**, #21 IC11 대상(조건부), UD-17e 범위 | [pack] §4.1·§4.2·§5 UD-17d |
| **UD-17e** | current_reuse pmos의 bulk: (i) vdd(지금 엔진 가정) (ii) 자기 source(별도 n-well, DEC-61 `bulk` 필드). 대상 = class-AB 배터리 M9a·M18a, **(v0.6) UD-17d (i)이면 캐스코드 M2a·M2b도** | 기본안 없음. (i)이면 vsb 0.825(M2a·M2b 0.9227) -- 진짜 LUT 범위 문제, #27(VS 0~1.8)이 덮음, 클램프 오차 0.7 %(M2a·M2b 1.3 %). (ii)이면 vsb 0 -- 단 **`bulk` 필드가 스키마·netlist·엔진 어디에도 없어**(F34) 사용자 connectivity 변경(새 `bulk` 단자)과 승인된 엔진 배선(#22의 DEC-61 몫)이 둘 다 필요하고, Vth·W가 바뀐다(미측정), n-well 분리 면적이 든다 | 소자 연결 사실(레이아웃·공정 선택) + connectivity | (ii)이면 **#55** 생성과 #22의 `bulk` 해석 몫, (i)이면 #27이 E8 경로 | [pack] §4.3·§5 UD-17e |
| **UD-18** | **B37a 승인 질문 Q1~Q3**(card approval `20260930-b37a-ports-roles`, decision) -- Q1 동작 변경 수용(E-LIB 5회로 자동 채움 소실·review 감소, E3 3회로 그룹 변화), Q2 `ports` 선언 확인(동작이 바뀌는 ngcc·sf_pushpull·two_stage_ota_sf + 선언이 판정 입력이 되는 pushpull·common_gate), Q3 sf_pushpull E3 값을 계약 test로 고정할지(비등가 생존 변이 1) | Q1 수용(이름 정규식 유도라 근거가 될 수 없음 -- 값의 옳고 그름은 6a J ratify), Q2 표대로 확인(틀린 회로는 `ports` 먼저 수정), **Q3 고정**(대안 = 비등가 변이 면제 = 판정 약화) | 동작 변경 수용·선언 근거 확인·판정 약화 대안 | #47 | `draft_b37a_approval_question.md` §1, card '결정 필요 항목' |

**UD-15 (2) 비교표(중립)** -- 두 안 모두 9회로 무동작(`RAILS ∩ 트랜지스터 넷 = supply_nets ∩ 트랜지스터 넷` 9/9, SD 운영 경로는 극성 미소비 [prep: §3.3])이다.

| 기준 | X: analog-grammar 확장(`rails` 인자) | Y: SD 호출부 어댑터(넷 이름 번역) |
|---|---|---|
| 고치는 파일 | analog-grammar `netclass`·`idioms`(+CLI), SD | SD만 |
| 필요한 승인 | UD-15 (1)의 plan_tables + 게이트 변경(#46) -- (1)=(a)면 **추가 0** | 경로표 개정 불필요. 단 B36 게이트 공백(#46)은 Y를 골라도 남아 (1)의 승인은 어차피 필요하다 |
| **레일 수 상한(DEC-62)** | 없음(선언 집합을 그대로 받는다) | **있음**: 극성마다 정준 토큰 수(analog-grammar 이름 집합 원소 5개)를 넘는 선언 레일은 명시적으로 거부해야 한다 = topology에 따라 거부하는 코드 상한. 같은 극성 레일이 여럿인 회로(레벨 시프터 H3 등)가 걸린다. 채택하면 DEC-62 예외 기록과 해소 card가 필요하다 |
| **mid 레일(선언된 `agnd`) 처리** | `rails` 집합에 넣고 라벨은 (3)의 결정대로 | 정준 토큰이 `VDD`/`GND` 극성 둘뿐이라 **mid를 어느 토큰으로 번역할지**가 정의되지 않는다. 어느 쪽을 골라도 grammar의 role 유도가 달라질 수 있다 → (3)과 같은 회로 해석 결정이 번역 규칙 안에 숨는다 |
| 이름 기반 판정 잔존 | analog-grammar 라이브러리 함수에서 0(이름 집합은 CLI 경계의 명시 가정으로만) | analog-grammar 내부는 그대로 이름 기반(일반화 미충족). SD는 이름 집합을 인코딩 통로로 참조 |
| B26-4 lint | AG 라이브러리까지 범위에 넣을 수 있다(면제 E-d는 CLI 모듈 하나) | 정준 토큰 리터럴을 lint 면제(E-c)로 둬야 한다 |
| 역변환 부담 | 없음 | `cls`·`imp`·`stack_edges`·`Match.ports`·입력 힌트를 전부 역치환해야 하고, 누락이 조용히 난다 -- 계약 "`load_topology` meta 전체 불변"으로 막아야 한다 |
| 극성 의존 | 극성(B26-2) 뒤 한 번에(API 1회 변경) | 극성으로 토큰을 고르므로 B26-2(UD-1) 선행 |
| 작업량 | card 1건 추가(#49) + AG test를 gmid `tests/contracts/`에 | #17 안에 흡수(card 수 불변) |
| 되돌림 비용 | analog-grammar API 변경(단독 CLI 사용자 영향) | 어댑터 삭제만 |

**사용자 작업(결정 아님)**: `install.py` `SKILLS`에 `"analog-grammar"` 추가(쓰기 주체가 사용자인 경로, F23). **#45 병합의 선행 조건**이다.

### 7.2 원칙 기본안(UD-0으로 확정 -- 따로 묻지 않는다)

| ID | 기본안 | 근거 |
|---|---|---|
| P-1 | `supply_nets` 없으면 거부, 이름 집합 대체 경로 없음 | 9/9 선언 완료(U-26 (b)), DEC-60 |
| P-2 | 보류 행 삭제·이관 D-1~D-7, 배선 W-1~W-3 | `prep_deferred_rows.md` §3.1·§3.2 |
| P-3 | `tol_V`는 DF-02와 한 card(MOD1), `tol_I`는 Phase 4에서 만들지 않음 | 만들면 배선 |
| P-4 | U-30 범위·선언 위치(§10.2), `max_finger_w`·`W_bounds` 상한·`stage_w_max`는 하네스 탐색 설정 공통 한 곳(값 유지). **정보 보고**: `max_finger_w` 40 µm > 모델 bin W 상한 7.0 µm(이번에 값을 바꾸지 않음) | DEC-68, `prep_u27_u30.md` |
| P-5 | U-27 VS 격자 = 상한은 `supplies_v` 최대 차에서 유도(= 계획 U-27의 0~1.8 V와 같은 값), 간격은 기존 0.2 V 유지. 0.2 V의 보간 오차는 #27에서 auditor가 VS 축 leave-one-out 오차로 **기록**(E6)하고, 간격을 바꿀지의 판단은 백로그 **B51**(v0.3의 'B39', v0.4의 'B44' 제안은 `backlog_additions.md`의 B39(B34 인계 사이트)·B44(B34 뒤 낡은 docstring)와 번호가 겹쳐 B48로 바꿨고, (v0.9.2) B48도 오케스트레이터 백로그(test_lint 오탐)와 겹쳐 **B51로 바꿨다**. 제안: "VS 축 보간 오차 대 tol_V 비교 -- 6b 봉인 설계 때 판단")로 둔다. (v0.5) 상한 1.8 V는 [ud17] 기본안 5와 같다(P-30) | 새 상수 금지, checklist §1 0.1 V 권장과의 차이 기록(검토 M7) |
| P-6 | U-27 → U-30 순서 | 기준선 승인 1회 |
| P-7 | 캐시(§4.4) | NFR-2 |
| P-8 | DF-23 Phase 4 범위 = P10 목록의 담당 4 행 | 계획 DF-23 |
| P-9 | 레일 인자는 기본값 없는 키워드 전용 | §4.2 |
| P-10 | B34: analog-grammar는 필수 의존이고 부재 시 명시적 오류 | 조용한 폴백 금지 |
| P-12 | B37 = **B37a #47 / B37b #52 분할**(`prep_b37_ports.md` §4.1·§5 '결정이 아닌 것'): `ports`의 `role`에서 입출력 유도(닫힌 어휘 6개), 진입점 E1~E3 전부 배선, SR `input_referred_offset_pairs`의 `direction` 읽기를 같은 접근자로 교체, `ports` 누락·모르는 role·role/`direction` 모순 거부(기본안 = 거부), 선행 #45 → #1 → #6(#17 아님), Phase 4 레일 묶음. 바이어스 힌트는 B37b가 흡수(B38 폐기). (v0.5, card v2) 명시적 `ports: {}` 수용, 포트 넷이 단자에 없음·레일이면 거부, offset 쌍이 있는데 입력 0이면 거부. '출력은 포트만'은 B37a 기록에서 빠져 **B37b(#52) card의 결정 항목**으로 갔다 | DEC-62, 계획 N3.15(`direction` 없음), prep §3 실측, `b37a_revision_log.md` §1 |
| **P-13** | **(v0.2 UD-2) 소신호 MNA에서 선언 레일 전부 교류접지**: `{r: 0 for r in supply_nets}` 다음 `also_fix`·`excite`로 덮어쓰기 | 계획 N0.4 106행 '교류접지 집합' 정의("레일 넷은 … AC구조에서는 모든 뷰의 교류접지다. 그 넷을 `ac_excite`로 선언한 전달 뷰만 예외"), DF-26 문구. 사용자에게는 결과 기준선(current_reuse `cmrr_estimate_db`)의 DEC-40 승인만 받는다(§7.4) |
| **P-14** | **(v0.2 UD-3) `supplies_v` 값**: nmcnr = 계획 확정값 `{vdd: 0.9, vss: −0.9}`(U-26 (a)), 적용 시점 = #22 뒤 #51(B1). #21에서는 원점 이동 동등값 `{vdd: 1.8, vss: 0.0}`. two_stage·current_reuse·folded = `{vdd: 1.8, gnd: 0.0}`(현 `SPECS` `vdd` 1.8, 세 회로 `supply_nets` = `['vdd','gnd']` [재측정 v0.3]) | 계획 U-26 (a). 세 회로 값은 계획이 정한 절차('제안표 → 사용자 확인')의 확인 기록이 착수 조건이다(§7.3) -- 결정 질문이 아니다 |
| **P-15** | U-25 실행 `SPECS` 이관은 범위 밖(§1.4) | N6.1 Phase 4 범위, IC11 rail3 = 6a |
| **P-16** | CC-5 깊은 복사 관용구 = 해당 없음(F19) | `00-common` §14 CC-5 행 |
| **P-17** | B26-4 lint는 PT 계약 test로 상시 실행, 면제 목록은 §5.4 #19에 전부 | 만들면 배선(검토 S10). 게이트 도구 변경이 아니라 test 추가라 게이트 변경 승인이 필요 없다 |
| **P-18** | D-5: 표 행은 #2, 함수는 #41 | F18(표에 없는 함수는 형식만 검사, 표 행의 함수가 없으면 FAIL) |
| **P-19** | 폴백 사이트 처리 규칙(§10.1-3·4) | DEC-76, V8, 조용한 폴백 금지 |
| **P-20** | U-27 도구 `Error:` 검사는 #26 범위(G7) | 이 Phase가 만드는 엔진 입력의 조용한 실패(검토 S6) |
| **P-21** | (v0.4) IC11 rail2 test·helper는 #21의 test 커밋, #22는 DF-24 두 몫(절대 프레임 고정 + DEC-61 식)을 한 card에서, red는 함수 수준 음전위 픽스처 | F25(S1 비트 동일, S3 부분 수정 상태의 오차), 계획 N3.16 MG1 행·DF-24 행 |
| **P-22** | (v0.4) IC11 허용오차 = ±τ 섭동의 레일별 1차 상한 합, 전위형 metric은 Δ만큼 이동한 값과 비교, 결과 단위 불변(§10.6) | 계획 N3.6 `tol_I = tol_V × gm`, N3.8 'AC gain = 노드 허용오차를 소신호 감도로 전파', N4.1 IC2 '연속 필드 ≤ tol_V 섭동의 감도 전파값' -- 모두 1차 선형 상한. F25 current_reuse 전위형 metric 2개 |
| **P-23** | (v0.4) #43 판정 경계는 HEAD 수치 경계 유지(폭은 #21). **(v0.7) margin = `null`**(v0.4~v0.6의 'margin 분모 = Σ_{멤버} tol_V' 철회 -- 분모가 정의되지 않는 대수 불변식). 허용오차 기반 경계는 6b. **(v0.8, S2) margin 함수 `normalized_margin`(CC-9)은 #23으로 앞당긴다**: 분모가 정의되는 #23 노드 충돌 레코드는 수, #43·#25 레코드는 같은 함수가 `tol=None`으로 `null`. 비교 규칙 §10.5·§10.6-0 | §11.2, 계획 396·428·749행, `00-common` §7.2(v0.7의 'IC9 때문에'는 근거 오인 -- 계획 IC9(827행)는 '중복 복붙 -- 레지스트리 정본 하나', 6b) |
| **P-24** | (v0.4) #22 → #25, #25·#26·#27 연속 병합, #25 → #10 | F26, 계획 U-27 선행 (1), 검토2 S11 |
| **P-25** | (v0.4) #13 발동 계수는 사본의 지점별 '키 부재·핸들러 진입' 계수 래퍼로 잰다(§10.1-4) | 검토2 S9: `activations_out`은 계측을 단 기능만 센다 |
| **P-26** | (v0.5) **조용한 클램프 거부는 계획대로**(DF-27 #25). UD-17 결정을 기다리지 않는다 | 조용한 폴백 금지. 클램프 값이 물리값과 최대 6배(M1 IDu)·16배(M7) 다름([ud17] §1.3) |
| **P-27** | (v0.5) **충돌 노드에서 vsb를 유도하지 않는다**: conflicts > tol_V이면 #23의 SEAL_VIOLATION으로 멈추고, 그 검사를 노드전압의 첫 소비자 앞에 둔다(#23 범위) | 이름순 첫 경로 선택은 조용한 선택이다. folded 축 밖 4소자 중 3(M5·M7, 극성을 고치면 M1·M2)과 current_reuse M2a·M2b가 그 파생(F26·F27) |
| **P-28** | (v0.5) **축 밖 오류는 고유 클래스로 끝까지 올린다** -- 후보 배제가 '후보 없음'으로 바꾸지 않는다(#25 계약, #10이 유지) | F29: 거부 사본의 current_reuse 두 실패 메시지가 원인(축 밖)을 가린다 |
| **P-29** | (v0.5) **선형 외삽은 대안이 아니다** -- 축 연장은 U-27 실측 데이터로만 | F30: M2b 외삽 −12 % 대 SPICE −1.3 %, M7은 음수 방향이라 비물리, 계획 U-27(재생성) |
| **P-30** | (v0.5) **U-27 VS 상한 1.8 V 유지**(P-5와 같은 값). 레일 폭을 넘는 vsb(실측 2.05 V)는 연장이 아니라 거부 대상 | DEC-61 \|V(s) − V(b)\| ≤ 레일 폭이면 물리적으로 나올 수 없는 값([ud17] §3.2) |
| **P-31** | (v0.5) **#22(DEC-61 abs)는 folded M7을 고친 것으로 기록하지 않는다**(abs(−0.65) = 0.65 ≠ 일관값 0.45). 순바이어스 거부는 6b(봉인 항목 6) | [ud17] §5.2-6, DEC-61 |
| **P-32** | (v0.5) **IC11 대상 = card base에서 θ 평가가 끝나는 SPECS 2레일 회로, 우선순위 current_reuse(파일럿, 원인 1개·진짜 축 밖 0.025 V) → folded(UD-17a 전에는 물리적 동작점이 없음)**. Phase 4 DoD의 E3는 성공 단위(§10.6-0) | 계획 N4.1 IC11 비교 양(VGS·VDS·VSB·gm_id·W·metric)은 성공한 평가에서만 정의된다. [ud17] 기본안 7. **(v0.6 근거 정정, F33)**: current_reuse의 '진짜 축 밖 0.025 V뿐'은 UD-17d (ii)일 때만 맞다 -- (i)이면 M2a·M2b 0.9227도 진짜 축 밖이고 설계 변경 없이는 M5가 포화 밖이다. 우선순위(current_reuse → folded)는 그대로 둔다: folded는 UD-17a·c 둘 다 있어야 동작점이 생기고(F32) current_reuse는 UD-17d 하나(+ 그 갈래의 설계 변경)로 닫힌다 |
| **P-33** | (v0.6) **`FallbackEvent`·`record_fallback`·수집기의 모듈 = I·D 지점이 있는 MOD 중 가장 작은 번호**(#13 작성 전 실측이 D0b 이관표로 정한다). 함수 안 지연 import로 import 규칙을 우회하지 않는다 | `00-common` §7.1(N3.10 import 규칙 -- 그래서 `FailureRecord`가 MOD2), Phase 3 v6 D-22('지연 import 우회 = skip'), §3.1. v0.5 §10.1-1의 'MOD4'는 이 규칙의 한 경우다 |
| **P-34** | (v0.6) **LUT 축 밖 오류의 raise 위치**: MOD1은 MOD1에 정의한 정의역 오류(축·값·격자 범위)를 내고, 처음 받는 MOD4 이상 호출부가 `SealViolationError`(항목 `lut_axis_out_of_range` + 소자)로 바꾼다. 변환은 클래스·사유를 보존한다(P-28). **(v0.7, S2) X 핸들러 규칙(#25가 만들고 #10이 유지 -- 두 card의 계약은 이 문장을 인용한다)**: X 핸들러가 잡는 타입 = MOD1 정의역 오류(§10.7)와 HEAD LUT 역산 실패. X 지점은 그 후보점 하나를 배제하고(후보 실패 = 탐색 중 처리) **배제 사유를 클래스·소자·축·값과 함께 모은다**. 모든 후보가 축 밖으로 배제되면 집계 지점(MOD4 이상 -- 모든 후보 실패를 판정하는 호출부)이 `SealViolationError`(`lut_axis_out_of_range`, 소자·축·값)를 올린다 -- '후보 없음'으로 바꾸지 않는다. 일부만 축 밖이면 탐색은 계속된다. X 핸들러가 MOD4 이상에 있어도 변환은 핸들러가 아니라 집계 지점에서 한다(후보 하나의 배제가 회로 실패가 되지 않게). **(v0.8, 4차 검토 S9) 원인 보존 두 줄**: (1) **혼합 사유**(일부 후보는 축 밖, 나머지는 역산 실패 등 다른 사유)이면 집계 지점은 축 밖 클래스로 바꾸지 않고 기존 클래스를 쓰되 `record.detail`에 배제 사유를 **클래스별 계수**로 싣는다(원인을 바꿔 보고하지 않음 -- P-28). 모든 후보가 축 밖일 때만 `lut_axis_out_of_range` (2) 한 층 위: 모든 시작점이 실패해 `SearchFailedError`가 되면 `record.detail`에 **시작점별 마지막 실패 클래스와 그 계수**(하위 레코드의 클래스·소자·축·값 포함)를 싣는다 -- F29의 증상('어느 메시지에도 축 밖이 없다')은 실행 수준이라 집계 지점만 고치면 한 층 위에서 되풀이된다 | `00-common` §7.1 'raise 위치 규칙: N3.14 예외는 MOD4 이상'(MOD3 `status` → MOD4 `StructureUnresolvedError`와 같은 모양), 3차 검토 S2(v0.6의 #25 '다시 올림'과 #10 '배제로만'이 반대 동작이었다) |
| **P-35** | (v0.9, 5차 검토 N-S1) **#2·#3·#4·#17·#18은 F2 뒤(Phase 4) 단일 경로** -- D0b 전 앞당김 경로를 두지 않는다. UD-0 문안의 '앞당길 때는 D0b 전에만'을 지운다. §9-9(N6.1 'TS4 첫 작업' 정정)가 유일 경로 | 선행 UD-0·UD-1·UD-15가 Phase 4 착수 때 질문이라 앞당김은 순환(부록 A H5 RC1·RC8·RC9). 앞당기려면 D0b 전 별도 질문이 필요하다(H5 N1) -- 사용자 결정을 늘리지 않는다. Phase 3 v7 D-27 '기본값 F2 뒤'와 같고 더 좁다. N3.10 '등급 D는 옮기기 전'은 D-1~D-7이 UD-0 전까지 `보류(Phase 4)` 행이라 걸리지 않는다(§3.2) |
| **P-36** | (v0.9, 5차 검토 N-S2) **노드전압 사슬의 허용오차**: 노드 충돌 허용오차는 세 함수(`propagate_node_voltages`·`reconcile_vsb_from_nodes`·`audit_vsb_consistency`)가 키워드 전용 `node_tol`(기본값 없음)로 받아 명시 전달하고, `reconcile`·`audit`의 vsb 비교 `tol=1e-6`은 인자째 없애 **비트 동일**로 비교한다. 호출부는 AST 단언으로 전수 확인(`except Exception` 안 호출 포함). 모두 #23 범위. **(v0.9.1, 6차 검토 R6-S1) 무동작이 아니다**: current_reuse에서 reconcile이 M58의 2 ulp 차이를 매 호출 덮어써 정본 θ*(`L_class__M68`·`L_class__M8` 마지막 자리)와 metrics 해시가 바뀐다 -- §5.5 #23 기대 차이표 + §7.4 DEC-40(발생 시 건별, 새 사용자 결정 아님) | 새 상수 금지 -- 비교 대상은 전체 그래프 노드전압에서 `derive_vsb_from_nodes`로 다시 계산한 값이다. (v0.9.1 정정) v0.9의 '같은 식·같은 노드전압의 재계산 일치'는 틀렸다: SR 7294·7449가 부분 그래프로 쓴 vsb가 reconcile 시점까지 남아 ulp 단위로 다를 수 있다(실측 current_reuse M58 2 ulp). 그래도 결론은 같다 -- reconcile이 비트 동일로 덮어쓰므로 audit에는 차이가 남지 않고(실측 발동 0), 두 함수가 같은 규칙이어야 정합한다, tol_V로 넓히는 것은 게이트 약화(사용자 몫), 이름 가림(F36)은 `**kw` 전달에 기대지 않아 없앤다. 기본값 제거의 `TypeError`가 `except Exception`(7297·7451)에 삼켜지는 경로가 있어 런타임 test만으로는 못 본다 |
| **P-37** | (v0.9.2) **E-LIB 비교 = 선례 모양**: Phase 4 DoD E11의 E-LIB 재측정은 Phase 3 DoD 대상 커밋 `P3D`와 Phase 4 마지막 병합본을 같은 경로에서 비교하고(Phase 3 D-28 `e_lib_p3.py` 한 사본), card가 계약으로 바꾸는 meta 키만 빼서 그 card 계약값·기대 차이표로 따로 판정, 나머지는 해시 같음. 빼는 키 = card 계약에서 유도(목록: `rails` -- #17 `polarity`, `ports`·`device_roles` -- #47; ~~#21은 [미확인]~~ **(v0.9.3) #21 몫 없음** -- 실측 `p4_card21_rails_measure.md`). topology 데이터를 바꾸는 #53·#54·#55는 그 card 차이표 + DEC-40. card 단위 equivalence에서도 #17은 `meta["rails"]`를 같은 모양으로 판정한다. **(v0.9.3, S1·S2)** 빼낸 키는 기대값과 **값 전체 정확 일치**(계약 밖 필드 0 -- Phase 3 v8.3 E5 (iv)와 같은 식)로 판정하고, 기대값은 엔진 출력이 아니라 선언에서 온다(nets = `P3D` library `supply_nets`, polarity = 고정 9회로 표). **빼는 키 목록과 출처는 이 원칙이 아니라 §6 'E11 빼는 키 표'(판정 기준)가 정하고**, 그 표는 승인 질문 UD-0 '기준에 닿는 것' (c)로 드러난다 -- 바꾸려면 design 개정 | 사용자 선례 `20260930-phase2-e4-baseline`("둘다 기본안으로 진행해") -- Phase 3 v8.2 E5(`MASK_META = ("rails",)`)가 같은 원칙으로 바꿨다. 같은 상황의 사용자 선택을 따른다(메모리 '결정은 원칙으로 기본안부터'). **(v0.9.3, m2)** 근거는 승인된 이 선례 하나로 충분하다 -- Phase 3 쪽 같은 모양(그 design UD-0 (c) 기본안)은 아직 사용자 답 전이고(대안 c-2 = B0 비교), 답이 c-2로 와도 P-37은 그대로다(Phase 4 비교 시작 판 `P3D`는 Phase 3 E5가 어느 판과 비교하는지와 무관하다) |

v0.2의 P-11(B35 = 어댑터)은 **지웠다**. 근거 열의 '조정자 지시'는 사용자 승인이 아니고, 비용 근거는 UD-15 (1)=(a)에서 사라지며, 어댑터의 레일 수 상한은 DEC-62와 충돌한다(검토 B4). B35는 UD-15 (2)로 옮겼다.

### 7.3 착수 조건 승인 기록(결정 질문이 아니라 계획·게이트가 요구하는 확인)

| 기록 | 내용 | 막는 card |
|---|---|---|
| U-26 (a) 확인 | two_stage·current_reuse·folded의 `supplies_v` 제안표(P-14) 확인. (v0.9, 5차 검토 m-9) nmcnr 값 `{vdd: 0.9, vss: −0.9}`는 계획 1101행이 이미 **확정**으로 적었으므로 다시 묻지 않는다 -- 확인 대상은 세 회로 값과 nmcnr의 MG1(#21)~DF-24(#22) 사이 **중간값** `{vdd: 1.8, vss: 0.0}`(원점 이동 동등, #51에서 확정값으로)뿐이다 | #21 |
| U-04·U-05·U-09·U-27·U-30 | 계획 N7.2가 Phase 4 착수 조건으로 지정(F11: 해당 승인 0) | 각 card |
| **A2 기록 `20260930-b26-before-phase3`**(승인됨 -- **(v0.5) gate에 있음 `2d58fd8`**) | DEC-60 넷 전환기 종료 + DF-19·26 넷 몫 MG1에서 분리 + B26-1·B34 Phase 3 전 착수. 계획 정정 커밋 **`8356c1e`**(v0.7 정정 -- v0.6까지 '아직 전'은 낡은 문장. §3.2는 이미 반영) | #1, #45 |
| **면제 묶기 게이트 변경 승인 `20260930-v3-exempt-binding`**(**A1-a 승인됨** 2026-10-01 -- 초안 `approval_20260930-v3-exempt-binding.md`, 문서 커밋 뒤 rev-parse로 채움) | 강화지만 게이트 판정 기준 변경이라 `target_kind: diff` 승인 1건. 범위 설명에 "강화: 기존 `20260922-ic3-v3-exempt` V3 원소 14개는 해시가 없어 더 적용되지 않는다" | #48, #1 |
| **범위 정책 승인 `20260930-v3-changed-stmt-scope`**(**A1-b + 정정 승인됨** -- 초안 `approval_20260930-v3-changed-stmt-scope.md`) | `target_kind: diff`, 범위 설명에 "판정 기준 적용 범위 축소(약화) 승인"과 놓치는 것 ①~③, 두 사용자 답 원문 | #1과 이후 엔진 card의 V3 |
| **B33 게이트 card `20260930-v7-registry-edges` 승인 + Q1**(인지 -- Phase 4 결정 아님. (v0.6) **둘 다 결정됨**: 승인 + Q1 "(a) 호출 위치만" -- `user_decisions.md` 2026-10-01 B33. 승인 기록 커밋은 card와 함께) | V7 도달 판정과 V3 인벤토리가 바뀐다(§5.12, 쌍 1.31배). Phase 3 착수 전 게이트 | Phase 3 이동 card(간접적으로 Phase 4 card의 V3·V7 기준) |
| **(v0.5) #53·#54 topology 수정 승인**(UD-17 답 뒤. (v0.6) #55 포함) | library topology.json 수정(사용자 connectivity + Claude 메타데이터 -- #53은 F35 주석 3곳 포함)은 쓰기 경로표 승인 기록(WP-07·U-16) 대상. S0 지문 변경 → `review_needed` 처리 | #53, #54, #55 |
| **(v0.6) 엔진 card 승인** -- #53 UD-17c (i)(새 외부 DC 선언 필드 + 엔진 해석 -- (v0.7) 노드 고정 값 출처 하나, `supplies_v`와의 관계 포함)·(ii)(컬럼 KVL 규칙, 계획 개정), #22의 `bulk` 해석 몫(UD-17e (ii) 답이 #22 착수 전일 때), **(v0.7) #55의 엔진 몫**(UD-17e (ii) 답이 #22 병합 뒤일 때 -- `bulk` 거부 해제 + 선언 bulk 읽기), (v0.7) #54 엔진 규칙 갈래(교차 그룹 노드 구속) | 공유 코드 변경은 승인 뒤 card로([pack] §0). (ii)는 계획 개정 동반 | #53, #22, #55, #54 |
| **(v0.6) B26-1 U4·U5**(B26-1 card v4) -- **(v0.9.2) 결정됨** | U4: 기록 `20260930-b26-b40-reason-key`(decision -- `unavailable_reason` 키 삭제만, 분기와 나머지 세 키는 그대로). U5: 기록 `20261001-b26-p9-signature-update`(`target_kind: diff`, V5 -- 새 기대 = 원래 두 매개변수 + 키워드 전용·기본값 없음 `rails: RailDeclaration`, 정확 일치 단언 유지). (v0.9.2) U3: 등가 면제 기록 `20261001-b26-v3-equiv-range`(decision, 약화 승인 1건 -- `range` const− 1개, ~~code 커밋 K 뒤 auditor 측정 해시로 병합 전 커밋, 착수 조건 아님~~ **(v0.9.3, R1)** 1차 시도(병합 안 함) code 커밋 K1 뒤 auditor 측정 해시로 **2차 시도 착수 전** 커밋 -- B26-1 card(`draft_b26_1.spec.md` 22:20 판) '두 번 시도 절차' 2·'승인 줄 배치' 5·착수 조건 8 인용: card 착수 조건은 아니고 2차 시도의 선행. U5 기록(1차 시도 T1 뒤)과 운반 blob·card 개정이 같은 `Role: doc` 커밋) | #1(2차 시도) |
| ~~(v0.7) B26pre 승인 기록 `20261001-b26-pre-test-strengthen`~~ **(v0.9) 필요 없음** | B26pre card v2: U1은 원칙 기본안(결정 아님)이고 `gate_change: no`라 머리 `approval` 줄이 없다(`merge_gate.gate_change_ok`는 `gate_change: yes`일 때만 확인). 판정 기록 `approvals[]`에 무엇을 적을지는 오케스트레이터(맥락으로 `20260930-b26-before-phase3`). **(v0.9.2)** Q-B34-PHASE 기록 `20261001-b26-phase3-cards`가 네 card 머리 `approval:` 줄이 된다(그 기록 범위 설명) -- B26pre도 그 줄을 가진다(phase 값 근거, 게이트 변경 아님) | -- |
| **(v0.9) U-BF 답** -- **(v0.9.2) 결정됨: 결함으로 고침** | 기록 `20261001-b26-backfill-interdig-fix`(`target_kind: decision`, 문안 `approval_20261001-b26-backfill-interdig-fix.md` -- 질문 원문은 세션 jsonl 그대로, `user_decisions.md` 정정 줄). red-green 결함 card `20261001-b26-backfill-interdig-final-audit`(`draft_b26_backfill_audit.spec.md`)를 B26pre 뒤·B26-1 앞에. U2-a(SR 11802 등가 면제)는 없어졌다 -- 최종 V3 규칙 N2(b) + 넓힌 T6에서 SR 11802는 대상 밖 | backfill card, #1 |
| **(v0.9) Q-B34-PHASE 답** -- **(v0.9.2) 결정됨: phase 3 + 정정 기록** | 기록 `20261001-b26-phase3-cards`(decision): #45·B26pre·backfill·#1 네 card 머리 `phase: 3`, 병합 순서 그대로(Phase 2 DoD 뒤·Phase 3 M card 전), A2 기록 ③의 'Phase 2 진행 중(card `phase: 2`)'을 새 기록으로 정정(옛 기록은 고치지 않음), design 30 승인·U-03을 기다리지 않음. 판정 기록 V1 `--gmid-phase=3`. 이 문서 card의 간선·판정은 같다(H6) | #45, B26pre, backfill, #1 |
| **(v0.9.2) Q-P2DOD-E2 기록 `20261001-p2dod-e2-wording`**(결정됨 -- "문구 정정", `target_kind: diff`) | Phase 2 DoD E2 통과 기준 = 'exit 0, 면제되지 않은 발견 0(현재 `20260929-p4-scan-exempt` 1건)'. Phase 2 DoD 측정 판 H가 이 정정 커밋을 포함해야 한다(Phase 2 몫). 이 Phase 몫 = 그 기록 '재검토' 절: 면제를 해소하는 #30이 같은 card에서 design 20 E2의 '현재 승인 … 1건' 문구를 고친다 | (Phase 2 DoD), #30 문서 몫 |
| #46 게이트 변경 승인 | UD-15 (1) 결과 | #46·#49·#52 |
| **#21 V4 규칙 (1) 면제**(v0.3 #50에서 옮김) | 불변식 test의 기대값(S_A 결과)이 피검 함수 호출(선례 `20260923-c9-v4-exempt`). **범위 설명에 "이 test 본문이 바뀌면 재승인"을 적는다** -- V4 면제는 test id에 묶이고 본문 해시에 묶이지 않는다(면제 묶기 card가 같은 부류 누수를 V4 백로그 (ii)로 넘김, 번호는 오케스트레이터가 부여) | #21 |
| **B37a 승인 기록 `20260930-b37a-ports-roles`**(decision -- B37a card 머리 approval. DEC-40·V5 아님 -- 기대값 변경 test 0) | **(v0.5) UD-18 Q1~Q3의 답**(§7.1)을 담는다. 초안 `draft_b37a_approval_question.md` §3. 기록에 '표를 잰 base 커밋'을 적고, 착수 시 재측정이 다르면 멈추고 다시 묻는다. v0.4의 ② '출력은 포트만'은 이 기록에서 빠져 B37b(#52) card 결정 항목으로 갔다 | #47 |

### 7.4 뒤에 올 DEC-40 승인(지금 결정할 것 아님, 발생 시 건별)

* current_reuse `cmrr_estimate_db` 기준선(P-13, #18) -- auditor가 θ*에서 다시 잰 값으로 [prep: 73.14488 → 73.38009].
* U-27 새 LUT 기존 열 차이(v0.2 UD-11, #27).
* U-30 교체로 바뀌는 θ*·기대값·finger 배정(v0.2 UD-12, #29) [prep 영향 후보: folded M3·M4 1.017 µm, nmcnr M202 1.02 µm].
* W-2 행 분할 감소로 바뀌는 E-INST(#41).
* `test_ic5` `_DOMAIN_TABLE` D-4·D-5 두 행 삭제와 `len` 21 → 19(#2, V5 1회).
* (v0.4) #23·#25·#26 병합본에서 folded·current_reuse 정본 실행이 '끝까지 실행' → 실패 레코드로 바뀌는 E-INST 기준선(F26·F27 -- 기대 차이표). UD-17 결과로 해소되면 그 card에서 다시.
* **(v0.9.1, 6차 검토 R6-S1) #23 vsb 비트 동일(P-36)로 바뀌는 current_reuse 정본 θ*·metrics 해시**: reconcile이 M58 vsb의 2 ulp 차이(SR 7294 부분 그래프 전파가 남긴 값)를 덮어써 SLSQP 경로가 갈린다 -- 검토자 실측 `L_class__M68`·`L_class__M8` 마지막 자리, metrics 해시 `5ff39866…` → `8b171811…`(#23 작성 전 실측이 다시 잰다). 노드 충돌 거부(F27)로 생기는 E-INST 차이와 별도 행으로 기대 차이표에 적는다. folded·two_stage·nmcnr은 이 규칙으로는 차이 없음(같은 실측).
* **(v0.8, 4차 검토 S7) #13 `fallback_events` 최상위 키 추가**: 4회로 E-INST 기대 해시와 Phase 3 D-25 M10 진입점 test 기대 해시가 #13에서 바뀐다(값은 빈 목록, 키를 뺀 정규화 해시는 동일 -- #13 계약). 기대 차이표 + DEC-40. #14는 θ*를 실행 기록 JSON에 두어 `instance.json`을 바꾸지 않는다(#14 계약 -- 바뀌면 그 card의 DEC-40).
* (v0.6) Phase 3 M10 진입점 E-INST test(D-25 -- 가장 싼 library 회로, 기록상 folded)의 기대 해시: #23·#25·#53(folded)이나 #54·#55(current_reuse를 골랐을 때)가 그 회로 결과를 바꾸면 그 card에서 바뀐다.
* (v0.5) #53·#54·(v0.6) #55 병합으로 바뀌는 folded·current_reuse의 E-LIB(topology 변경)·E-INST·θ*(결과 card 몫). #18의 current_reuse `cmrr_estimate_db` 기준선이 #18 시점에 보이지 않았으면(#23 뒤·#54 전) #54의 DEC-40에 합친다. #53 뒤 folded가 `W_bounds` 때문에 infeasible로 끝나는 것도 기준선 변경이다([ud17] §4.3).
* I-C11 xfail·known_limitation 정리(#44, UD-6 결과).
* 각 DF 수정으로 바뀌는 θ*(E2). (#47의 E-LIB 차이는 DEC-40이 아니라 §7.3 승인 기록(UD-18 Q1) -- 검토2 S2, v0.5 정정.)
* B26-1 기존 test에 `supply_nets`·`rails=` 추가가 V5로 잡히면 `target_kind: diff`.

---

## 8. 병렬 준비 계획

card 처리 속도 규칙(메모리): 사실 문장은 쓰는 자리에서 재측정, 새 이름은 test glob 충돌 grep, 원칙은 계약에 전 범위로, 삭제 전 계획서 소비자 grep, 병렬 가능한 준비는 항상 미리.

### 8.1 지금(Phase 2 남은 card·Phase 3 design 승인과 병렬)

| 준비 | 산출 | 막히는 것 |
|---|---|---|
| B26-1 spec card 보강 | 검토 `review_b26_1.md` B2·S1·S4·S5·M1~M6 반영 + ~~B34 인계 사이트~~(**v0.5 반영됨**) + 'V3 계획'을 A1 결과 경로로(§3.2 표, **수치 294** -- 넓힌 T6) + P9 병합본(`93b18db`, SD −11줄) 기준 줄 재측정 | ~~A2 기록~~(✓), A1(✓) |
| ~~A1 질문~~ | **완료**: A1-a·A1-b·A1-b 정정 결정(2026-10-01). 남은 것 = 승인 기록 2건 커밋(초안 있음), B26-1 card 'V3 계획' 갱신 | -- |
| V3 게이트 card 둘(면제 묶기·범위 정책) | **v3 커밋용 확정**(`v3_cards_revision_log.md` §5~§7). 남은 것(오케스트레이터): interface card 둘, 문서 커밋(design 05 ①·⑤, design 10 382행, 계획 N4.2), 승인 기록 rev-parse 채움, 백로그 B45·B46 반영 | P10·P10b 병합 |
| 계획 정정안 커밋 준비(`draft_b26_plan_patch.md`) + A2 기록 파일 | `plan_tables_hash` 전후 측정 | P9 병합 순서 |
| B34 spec card(#45) | **완료(최신 card, phase 2 → (v0.9.2) phase 3, 55/55)** -- 남은 것: 사용자 `install.py` 작업, ~~B26-1 인계 한 줄~~(v0.5 반영됨), 백로그 B39·B44 기록, P9 병합본(SD −11줄)에서 사이트 줄 재측정 | 사용자 `install.py` 작업(병합 전) |
| UD-15 결정 자료 | §7.1 비교표 + (3) mid 레일 공동분석 표(pushpull 두 회로의 `agnd` 연결: 커패시터 단자만 [prep]) | 없음 |
| B36 게이트 card 준비 | 도구 6개 glob 위치, V7 동적 import 간선 규칙, redteam 사례 | UD-15 |
| B37a spec card(#47) | **v2 완료** `draft_b37a.spec.md`(검토 `review_b37a.md` blocking 3 반영, `b37a_revision_log.md`). 남은 것: UD-18 질문(Q1~Q3 문안 `draft_b37a_approval_question.md`), 넓힌 T6로 V3 대상 재분류(81 → ?), Phase 3 D-19 결과로 모듈 이름, 오케스트레이터 문서 커밋 목록(준비 자료 §4.2 C1 문장·`references/analog-grammar-integration.md` §5 정정) | #45·#1·#6 병합, UD-18 |
| ~~UD-17 공동분석 자료~~ | **완료(v0.5 `prep_ud17_f26_f27.md`, v0.6 `ud17_coanalysis_pack.md`)**: 넷 기준 표(json 파생)·충돌 경로·빠른 점검 F0~F3·C1·회로도 체크리스트(§5). 남은 것 = 사용자와 공동분석(UD-17a~e 질문 -- 체크리스트 순서), 사용자 정정은 대기열에 모았다가 일괄 반영 | 사용자 |
| **#53·#54·#55 card 초안**(v0.5, v0.6 갱신) | UD-17 답이 오면 바로: 데이터 갈래면 topology 수정안(사용자 connectivity 확인 + 메타데이터 표 + F35 주석 3곳), 엔진 갈래면 spec card. 공통 '작성 전 실측' = conflicts·축 밖 조회 계수(F26·F27 스크립트 `p4_scripts/b2_axes.py`·`b2_nodes.py`, `ud17_scripts/ud17_eval.py`, [pack] 빠른 점검 방법 재사용). #54 (i)이면 M5 포화 여부와 replica 컬럼 재배정 뒤 충돌을 **실제로 잰다**(F33은 미측정). #55면 #22 작성 전 실측에 '`bulk` 키를 넣었을 때 지금 엔진 동작'(무시/거부)을 넣는다 | UD-17a+c(#53), UD-17d(#54), UD-17e (ii)(#55) |
| ~~(v0.6) B26-1 U3 선행 test-only card~~ **(v0.7) B26pre card** | **초안 있음** `draft_b26pre.spec.md`(id `20260930-b26-pre-test-strengthen`, phase 2 → (v0.9.2) 3, test-only): v4 모의 head에서 E6·E7 생존 34 재측정, 새 test로 25 죽임, 등가 후보 9 = card U2. 남은 것(오케스트레이터): U2 질문, B26-1 card 인계(착수 조건에 B26pre 병합, 계약 12 직접 호출 목록, 'V3 계획' E6·E7 줄). **(v0.9) card v2**(`b26pre_revision_log.md` v1 → v2): base 32문장 중 29 죽임, 남는 3 = U2(U-BF 질문 + U2-a), U1 = 원칙 기본안(기록 확인 불필요), red-green 결함 card 초안 `draft_b26_backfill_audit.spec.md` | ~~U-BF, Q-B34-PHASE~~ (v0.9.2) 둘 다 결정됨 -- 남은 것: 네 card 머리 `phase: 3`·`approval` 줄 개정과 기록 커밋(오케스트레이터) |
| I-C11 공동분석 자료(UD-6) | nmcnr `stage2_diode_ref` 그룹 멤버·직렬 경로 표(`topology_to_markdown.py` 넷 기준 표, 메모리 '회로도 판독은 넷 표로 재검증'), two_stage `stage1_out` VDS 출처 표(F15의 M4·M2·M5) | 사용자와 공동분석 |
| #2·#3·#4 spec card 초안 | 계획 소비자 grep, `test_ic5` 두 행(F18) | UD-0 |
| TS4 대상 실측(V4 lint 산출) | D-1 삭제 시 TS4 대상 | 없음 |
| U-30 C4 대상 픽스처 전수(AST) | #28 기존 test 영향 | 없음 |
| U-27 병렬화 판단 자료 | 조합 독립 실행 가능 여부 | 없음 |
| DF-15 재현 시도 | red 입력 또는 계획 정정 요청 | 없음 |
| **#13 발동 계수 실측**(측정 방법 §10.1-4 -- CC-8 도구를 기다리지 않는다) | 사본 계수 래퍼로 부록 C.1 `I` 5지점 + C.2 스칼라 기본값 지점(+ SR 7411)의 정본 실행 4회로·E-LIB 9회로 발동 계수 → 거부/계측 분류. `x.get(k) or <리터럴>`·조건식 기본값을 같은 규칙에 더해 다시 센다(부록 A 측정 한계) | 없음 |
| ~~#50 평가점 선정~~ | **완료(v0.4 F25·F26·F27)** -- #50은 폐지, 평가점·대상 회로 규칙은 §10.6-0 | -- |
| #21 분류표 초안 | F4 20줄 + 같은 함수의 레일 전위 리터럴 0.0 3곳을 §10.4의 네 가지 뜻(span·hi·lo·hi+lo)으로(F25 S1 모드가 쓴 분류가 출발점) | 없음 |
| **(v0.9.3) #17 polarity 기대값 독립 재측정**(§6 'E11 빼는 키 표'의 #17 card 작성 전 조건 (1)~(3)) | 판정 쪽 독립 구현(topology JSON의 `supply_nets`·소자 종류·source 단자만 -- 엔진 import 없음)으로 9회로 극성 → `POLARITY_P4`와 대조, `e_lib_p3.py`의 `polarity` 직렬화 모양 확인. 지금 판에서 미리 재고, 최종은 `P3D`에서 | #17 card 작성 |

### 8.2 Phase 3 진행 중

* 선두 5건(#5~#9) spec card 초안 -- 목적 모듈은 D0b 확정 뒤 파일:줄만 채운다.
* 파일 충돌 집합(§3.4)의 모듈 이름을 D0b로 확정.
* (v0.4) Phase 3 design에 D0b 재측정 조건 추가 요청(§3.1, §9-11). B33은 게이트 card로 Phase 3 착수 전 처리(§5.12) -- v0.3의 'G1에서 처리되는지 확인' 줄은 지웠다.
* (v0.4) B33 병합 뒤 부록 C '운영 도달' 열 재측정(§10.1-5).

### 8.3 Phase 4 착수 뒤

* 선두 5건 사이에 나머지 묶음의 **작성 전 실측을 한 벌로** 뽑는다.
* U-27b 재생성은 `run_in_background` + 조합마다 체크포인트 -- #26 병합 즉시 시작.
* auditor 측정 재사용: E-LIB·E-INST base 산출물은 Phase 3 DoD 기록을 base로 재사용 **[미확인: Phase 3 DoD 기록 형식이 아직 없다]**.

### 8.4 V3 전신 변이 비용이 Phase 4 일정에 미치는 영향

**측정된 것(B26-1 한 card)** [prep: `review_b26_1.md` B1]: (v0.8, S8 -- v0.2 문장을 옮김) `tools/gates/mutate_changed.py`는 AST가 바뀐 def의 **본문 전체**에 변이를 건다(A1 결정 전 규칙). B26-1은 def 약 32개를 바꾸고 변이는 약 2,465개다 -- 큰 것 `_build_theta_evaluator` 497(1,004줄), `propose_device_roles_gap_fill` 331, `optimize_full_circuit_budget` 229, `load_topology` 58. 인벤토리 `load_topology` 230 등, registry 경유 metric 인벤토리 0.

**현재 사실(v0.3, 검토 M3)**: B28(V3 이력 복제본)은 **이미 병합됐다**(`2b41e79` merge, `8790b24` 판정 기록). `mutate_changed.py`는 지금 `--head` 격리 복제본에서 변이를 실제로 돌리고, **기준 실행 실패는 ERROR(exit 2)**다(`dee338d`). 따라서 P8·DF-36의 '사이트만 대체 측정' 선례는 Phase 4에서 쓸 수 없다.

**대응(v0.3 → v0.4)**: v0.3은 V3 범위를 이 문서의 게이트 변경 card #48(대상 정의·출력 형식을 이 문서가 정함)로 바꿨으나, 판정 범위 축소는 게이트 변경이어도 약화라 사용자 결정 A1의 몫이고 정의는 새 게이트 card가 정한다(검토2 B1). v0.4는 그 card를 인용만 한다(§5.12).

**대응(v0.4)**: #48은 사용자 결정 A1의 결과다(§7.1) -- **선택지 2로 결정됨**. #1은 면제 묶기 → #48 병합 뒤 착수한다.

**card별 수치**(`v3_scope_systemic.md`(cd64170, 엔진 = HEAD)·범위 정책 card '작성 전 실측' 1~3·B34 card '작성 전 실측' 3):

| card | 대상 def | 지금 규칙(def 전체) | 직렬 시간(하한 ~ 상한) | **N2(결정됨)** | D1(택하지 않음) | 미실행 줄 대상 변이(지금 → N2) |
|---|---|---|---|---|---|---|
| P9 실제(`7535799 → b7765b0`) | 2 | 28 | -- | 12 | 11 | 0 |
| B26-1(#1) | 31 | 2,472 | 3.4 h ~ 129 h(현실 하한 19.2 h) | **294**(넓힌 T6 -- 24.5분 ~ 15.6 h, 현실 하한 0.88 h). 승인 당시 T6로 228 | 399 | 306 → **9**(승인 당시 6) |
| B34(#45) 최신 범위 | 4 | **55** | -- | 10(넓힌 T6도 10) | 14 | 1(card 새 test가 죽임 -- 55/55) |
| (v0.5) B37a(#47) v2 | 6(새 def 1) | 659 | -- | **81**(승인 당시 T6 분류기 -- 넓힌 T6 재분류 필요) | -- | -- (모의 판정 80/81, 생존 1 = UD-18 Q3) |
| (참고) B34 옛 넓은 범위 | 18 | 1,395 | 2.0 h ~ 56 h | 미측정 | 미측정 | 75 |

* 출처: `v3_cards_revision_log.md` §2(개정 정의 재측정, 인벤토리 시간 187~202 s), `v3_scope_systemic.md`(cd64170, 엔진 = HEAD), B34 card '작성 전 실측' 3. 공통: 사본 전체 test 1회 813건 272 s(`cd64170` [prep]. (v0.8, m3) HEAD `a796468` 수집 수 886건(`--gmid-phase=4 --collect-only`, 부록 A G2) -- 시간은 다시 재지 않았다), pytest 기동 4.7~7.1 s, 도구는 직렬.
* **B33 효과**(v0.5 개정 card 값): 병합되면 (소스 def, 도달 test) 쌍이 33,991 → **44,493(1.31배)**, def별 인벤토리 중앙값 61 → 67, 인벤토리 0 def 82 → 19(`b33_revision_log.md` §2.1 -- 작성자 측정. v0.4의 79,809·148은 v1 규칙 값이라 폐기). 레지스트리 경유 def의 '인벤토리 0 → 확정 FAIL'(예: B26-1의 `_metric_kcl_residual` 57)은 사라지지만, card별 V3 시간 상한은 늘고, 새로 인벤토리에 든 test가 격리 복제본 기준 실행에서 실패하면 V3 = ERROR(B28 규칙)다. 위 표의 시간은 B33 전 값이다.

**Phase 4 전반으로의 확장**(구조 추론 + 위 수치):
1. 큰 def(`_build_theta_evaluator` 498, `propose_device_roles_gap_fill` 331, `optimize_full_circuit_budget` 230)를 건드리는 card는 지금 규칙이면 매번 그 def 전체 변이를 냈다(확정 생존 몫 포함). **A1 = 2로 결정돼** 변이 수는 바뀐 문장(+ 감싸는 제어문·삭제 지점 주변·바뀐 매개변수를 읽는 문장) 수에 비례한다(B26-1: 2,472 → 294, 넓힌 T6). 평가 커널 빌더를 고치는 card는 §3.4 기준 7건, `propose_device_roles_gap_fill`은 #1·#17·#47. B37a는 `_build_theta_evaluator`의 호출문 한 줄(`ports=`)만 바꿔 N2 대상이 작다(B37a card 'V3 계획'이 U1 결과를 따르는 조건문을 이 결정으로 확정).
2. 완화책(원칙 안, A1과 무관): (a) CC-7a 추출 (b) registry 경유 metric test는 함수 이름으로 직접 부른다(모든 metric card의 interface card 조건) (c) 같은 큰 def를 고치는 card의 V3는 병합 순서대로 background 실행, 결과는 파일에 (d) 평가 커널 빌더 분할은 6b (e) 약화 없는 가속(줄 커버리지 선택·병렬)은 별도 게이트 card 후보(범위 정책 card '작성 전 실측' 5: B26-1 상한 122 h → 약 70 h, 확정 생존은 그대로).
3. 일정: U-27b 재생성(약 22시간)과 V3를 한 기계에서 동시에 돌리지 않는다 **[미확인: 병렬 시간 영향]**.

---

## 9. 열린 항목과 계획 정정 요청

N9.2-8은 "열린 질문이 없어야 한다"이다. **(v0.9.2)** 남은 열린 질문은 **없다** -- v0.9의 U-BF·Q-B34-PHASE와 B26-1 U3~U5, Q-P2DOD-E2가 결정됐고(§7 요약) 새 원칙 기본안 P-37은 사용자 선례를 따른다. **(v0.9)** 남은 열린 질문은 **없다** -- N-S1(앞당김 경로)은 P-35, N-S2(vsb 허용오차)는 P-36·§9-26으로 닫았고, 새 사용자 질문 U-BF·Q-B34-PHASE는 이 Phase card가 아니라 #1·#45·B26pre를 막는다(§7 결정 상태 요약). **(v0.8)** 남은 열린 질문은 **없다** -- §9-22(margin)는 원칙 기본안으로 결정됨, §9-23은 기록 원문으로 닫힘, 새 요청 §9-25(계획 한 줄 정정)는 기본안이 있다. v0.7의 남은 열린 질문은 **없다**(v0.6에서 생긴 것은 사용자 결정 UD-17 문구 정정·B26-1 U3~U5와 오케스트레이터 정정 요청 19~21. (v0.7) 19는 확정 순서로 닫혔고, 새 사용자 결정은 B26pre U2 하나, 새 오케스트레이터 요청은 22~24):
* V3 범위는 A1(사용자 결정)로 올렸고 **선택지 2로 결정됐다**(§3.2 표는 근거 기록). `v3_scope_systemic.md`는 있었고(v0.3 문장 정정) 수치는 §8.4에 넣었다.
* I-C11은 UD-6, 정본 실행 두 회로의 노드전압 충돌은 UD-17a~e(사용자 결정·공동분석)로 올렸다. card 중간 병합본의 IC11은 §10.6-0 결과 단위 불변으로 판정이 정의돼 있다. (v0.5) Phase 4 DoD의 E3(성공 단위)·E8(파일럿 `status=ok`)은 #54에 걸리고, 어느 답으로도 Phase 4 안에서 성공하는 SPECS 2레일 회로가 나오지 않으면 처리(N7 정정 요청 -- 아래 17)가 정해져 있다.
* 본문의 [미확인]은 전부 'card 작성 전 실측' 대상이고 설계 판단을 바꾸지 않는 수치다(E0 필드 이름, TS4 대상 수, DF-10 뿌리 동일, Phase 3 DoD 기록 형식, 병렬 시간, #43 뒤 two_stage 해 존재 여부, (v0.5) tol_V 값과 F27 충돌의 대소, VS 2.05 V 조회의 출처, F28의 원인 경로, B37a 넓힌 T6 대상 수). DF-23 행 수는 P10 inventory로 닫았다(#39: 63). 그중 설계를 바꿀 수 있는 것은 조건과 처리가 적혀 있다(TS4 대상 0 → 계획 정정, §10.1-4 발동 > 0이면서 원인 card가 Phase 4 밖 → N7 추가 요청).

아래는 계획 정정 요청이다(오케스트레이터, 경위는 history).

1. 계획 DF-29 행 닫힘(P5b 삭제), DF-09 행 닫힘(D-1 승인 시), TS4 행 "DF-09 등" → V4 lint 산출 목록, DEC-25의 `node_pole_estimate` 문장, DF-06 위치 열에서 `node_pole_estimate` 제거.
2. DF 위치 열 줄 번호 갱신 → 함수 이름 인용(DF-24 "3957행" → `derive_vsb_from_nodes`, §1.5-6 포함).
3. U-27 "SID_1F 열 추가" → "새 VS 축으로 함께 재스윕", 계획 158행, docstring·checklist.
4. DF-19 비고 "29개" 등 `draft_b26_plan_patch.md` §1~§6.
5. N3.16 PDK 상수 행: 엔진 폴백 15곳을 옛 이름(사본) 열에 추가.
6. **DF-01·DF-24 행에 vsb 조용한 기본값 사이트 추가**(SR `.get("vsb", 0.0)` 31곳, 조건식 기본값 SR 7411, `setdefault` SD 4605 -- 부록 C.2).
7. **N4.2 V3 행과 `05` §10**: 면제 묶기 card(⑤ 문구)와 범위 정책 card(① 문구, A1-b)가 각자 spec card와 같은 커밋에서 고친다. 이 칸은 `plan_tables_hash` 입력이 아니다(두 card 실측) -- v0.3의 'plan_tables 승인'은 틀렸다(검토2 B1-4).
8. **B21 (a) 매핑·P3c 재착수**: `tol_I`는 6b → P3c 재착수 위치 = 6b `tol_I` card 뒤. 조건 (b)는 #21, (c)는 #23에서 충족(Phase 2 DoD 기록의 'P3c 보류(B21, Phase 4)'를 '(6b)'로).
9. **N6.1 'TS4 첫 작업'**: #2가 Phase 3 전에 병합되지 않으면 Phase 4에서 #2가 TS4보다 앞선다 -- 그때 N6.1 순서 문구 정정(검토 M9). **(v0.9, N-S1 -- P-35)** #2는 F2 뒤 단일 경로이므로 이 정정이 **유일 경로**다(v0.8의 '앞당기면 정정 불필요' 갈래는 없다).
10. **U-09(UD-6 결과가 (A)이면)**: I-C11 해소 Phase를 DEC-70·71 구현 Phase로, N6.1 Phase 4 범위 문구 'I-C11' → '실패 명시화', xfail 3건 reason의 만료 Phase 갱신(백로그 B12).
11. **Phase 3 design 교차 항목**(§3.1, Phase 3 design 개정 요청 -- **(v0.8) Phase 3 v7 §9.1 재측정 (1)이 'B34·B26-1(test 보강 card 포함)과, D0b 전에 병합된 그 밖의 엔진 card'로 반영했다**. (v0.9) 이 문서 쪽 남은 일 없음 -- #2·#3·#4·#17·#18은 F2 뒤 단일 경로라(P-35) Phase 3 재측정 (1)에 들어갈 이 문서의 card가 없다(#1·#45·B26pre·backfill 결함 card만 -- (v0.9.2) U-BF 결정으로 조건 없음) -- 아래는 v0.4 요청 원문, 기록): v4 머리 재측정 조건에 "B26-1·B34(와 Phase 3 전에 병합되는 #2·#3·#4)가 병합되면 D0b 작성 전 실측·부록 A M6·M18·M22·G6을 그 병합본에서 다시 잰다", §1 범위 밖 "B26, Phase 4" → "B26-1은 Phase 3 전(A2), B26-2~4는 Phase 4". 그리고 G1과 V3 범위 정책 card가 같은 대상 선택 지점을 바꾸므로 병합 순서(범위 정책 → B33 → G1, §3.2)를 G1 행에 한 줄.
12. 백로그 추가(`backlog_additions.md`): **B51**(VS 0.2 V 간격 보간 오차 판단, P-5 -- v0.3의 'B39'·v0.4의 'B44'·v0.5~v0.9.1의 'B48' 제안은 기존 번호와 겹쳐 바꿨다), (v0.5) **B52**(sf_pushpull 경로 3 그룹이 M1~M4를 덮지 않음), **B53**(측정 사본에 analog-grammar 동봉 -- 브리핑 규칙). (v0.9.2) 번호는 오케스트레이터가 확정했다 -- B48(test_lint 빈 컨테이너 오탐)·B49(design 20 §8 P6·P8 판정 유형)·B50(층위1 폴백 중복)이 이미 쓰여 이 세 제안은 B51~B53(`backlog_commit_plan.md` '`--with-p4`'). v0.3의 B38 제안(바이어스 힌트)은 **철회**(B37b #52가 흡수, §1.4).
13. (v0.4) **계획 N4.1 IC11 행 '메트릭 전부 같음'**: 노드 절대 전위를 돌려주는 metric type(HEAD: `rail_referenced_voltage`)은 원점 이동에서 Δ만큼 이동하는 것이 정의상 맞다(F25 current_reuse `vg15_level_v`·`vop1_level_v`가 정확히 −0.9 V). → "전위형 metric은 Δ만큼 이동한 값과 비교"를 더한다(§10.6).
14. (v0.4) **계획 N3.16 MG1 행 'DF-19·24·26과 같은 변경 단위'**: IC11 test는 MG1 card(#21)에, DF-24는 바로 뒤 #22에 둔다(F25: #21만으로 rail2 PASS, DF-24의 두 몫은 #22 한 card). '같은 변경 단위'를 '같은 card 사슬(#21 → #22, IC11이 둘 다 지킴)'로 읽는다는 한 줄.
15. (v0.4) **계획 DF-27 행·U-27 행**: 정본 실행 두 회로가 지금 VS 축 밖을 조회한다(F26)는 사실과 '#22 → DF-27 → U-27 연속' 순서. DF-02 행: 정본 실행 두 회로에 conflicts가 있다(F27, UD-17).
16. (v0.5) **계획 DF-02 행**: (a) 지금 엔진은 충돌 노드에서 이름순 첫 경로 값을 채택하고 그 값으로 vsb를 유도한다(조용한 선택 -- F27) → DF-02 수정 범위에 '충돌 검사를 노드전압 첫 소비자 앞에'(P-27) 한 줄. (b) folded·current_reuse의 지금 사이징이 일관되지 않은 동작점 위의 값이라는 사실(§1.5-8)과 원인 결정 UD-17a~e. **계획 DF-27 행**: 축 밖 오류의 원인 오귀속(F29)과 고유 클래스 전파(P-28), 외삽 금지(P-29), VS 상한 1.8 V·레일 폭 초과 vsb 거부(P-30). **DF-01 행**: 매칭쌍 W 불일치 실사례(F28) -- 원인 경로가 7579 계열이 아니면 위치 열 추가.
17. (v0.5) **N6.2 Phase 4 완료 조건과 파일럿**(조건부): Phase 4 끝에 SPECS 2레일 회로 중 θ 평가가 끝나는 회로가 없으면(UD-17d·UD-17a의 답이 Phase 4 안 해소를 허락하지 않는 경우) IC11 rail2 'PASS'(N6.2)와 성능 보고 파일럿(`00-common` §10 `--circuit <파일럿>`)이 성공 단위로 판정되지 않는다. 그때의 정정안: IC11은 실패 단위 판정 + 해소 Phase 지정, E8 파일럿은 그 시점에 끝까지 도는 회로로 바꾸거나 '실패 실행의 탐색 시간'을 보고(U-09 재결정과 같은 N7 경로). 이 요청은 UD-17d 답을 받은 뒤에만 낸다.
18. (v0.5) **Phase 3 design 교차(정보)**: v5 §5.5.4의 'B33 V3 인벤토리 33,991 → 79,809'는 개정 card 값 44,493으로(3차 검토 S1 (iii)과 같은 지적 -- Phase 3 design 몫). D-19 결과가 #47(B37a 접근자) 모듈을 정한다.
19. **(v0.7) 결정됨 -- 읽기 (나)**: 근거 `user_decisions.md` 2026-10-01 "card 순서"("B34·B26-1은 Phase 2 DoD 뒤·Phase 3 M card 전(A2로 앞당긴 card), Phase 2 DoD N6.3 목록 밖"). 이 문서의 간선: P10b → Phase 2 DoD → 34 → 35 → B34 → B26pre → B26-1 → B33(하드), Phase 2 DoD의 선행에서 B34·B26-1을 뺐다(부록 A F1 S0 비순환, 옛 읽기 (가) + 확정 순서 = C1 순환). **후속 정리는 오케스트레이터 몫이고 사용자 결정이 아니다**: design 20 §10 DoD 범위 문구에서 B34·B26-1 제외, 두 card의 `phase: 2`는 그대로(`merge_gate.rule10_phase`는 순서를 강제하지 않는다 -- Phase 3 v6 §8.1). **(v0.9, 5차 검토 m-8) 정정**: 그 `phase` 값은 새 사용자 질문 **Q-B34-PHASE**(`pending_questions.md`, 기본안 `phase: 3` + 'M card 전' 유지, 대안 = 두 card를 Phase 2 DoD 앞으로)의 몫이 됐다. 실측(부록 A H6): `rule10_phase`(merge_gate.py 532~549)는 card `phase`가 `phase_order`에 있는지와 **V 검사 N/A 허용(card Phase < 그 V의 도입 Phase)**에만 쓰고 현재 Phase와 대조하지 않는다 -- 그래서 답은 이 문서의 간선을 바꾸지 않고, 바뀌는 것은 이 문서 곳곳의 'phase 2' 표기와 두 card 판정 기록의 V N/A 가능 범위다. **(v0.9.1, 6차 검토 m-2 정정)** 그 실측은 불완전했다 -- `merge_gate.py`는 card phase를 V1 `--gmid-phase=<card phase>` 강제(1009~1010·1213행)와 같은 Phase 엄격 집합(1042행 `strict_set`)에도 쓴다. 그래서 답은 B34·B26-1·b26pre·backfill card의 **V1 실행 옵션과 엄격 집합**도 바꾼다(부록 A H6). 이 문서 card(phase 4)의 판정은 같다. 답이 오면 이 문서의 'phase 2' 표기(§1.3·§3.2·§3.3·§5.1·부록 C.3)를 한 번에 고친다, Phase 3 design의 §9.1 'Phase 2에 남은 것 = P10b·B34·B26-1 병합' 문구에도 같은 정정 -- **(v0.8) Phase 3 v7 §9.1이 반영했다**('B34·B26-1은 Phase 2 DoD 뒤 … v6이 넣은 것은 틀렸다'). design 20 §10 문구 정정만 남는다. (v0.6 원문 -- 기록) Phase 3 v6 §9.1은 "Phase 2에 남은 것 = P10b·**B34·B26-1** 병합, 그리고 DoD E0~E5"(곧 B34·B26-1 → Phase 2 DoD)이고, `b34_commit_plan.md` §1(작업 순서, `user_decisions.md` 인용)은 "P10 → P10b → **Phase 2 DoD** → 34 → 35 → B34 → B26-1 → B33"(곧 Phase 2 DoD → B34·B26-1)이다. 둘을 같이 간선으로 넣으면 `Phase 2 DoD → 34 → 35 → B34 → B26-1 → Phase 2 DoD` 순환이다(부록 A E3 시나리오 S5). `user_decisions.md`에는 그 순서 원문이 없다(A1-a '순서 P9·P10·P10b 뒤, B26-1 전'만). 한쪽으로 고쳐야 한다: (가) B34·B26-1을 Phase 2 DoD 안에 둔다(Phase 3 v6, card 머리 `phase: 2`와 맞음 -- 이 문서의 기본 가정) (나) 'Phase 2 DoD'가 B34·B26-1을 뺀 DoD라면 design 20 §10 DoD 범위 문구와 두 card의 `phase` 값을 함께 고친다. 이 문서는 (가)로 간선을 둔다. **(v0.9.2) 닫음 -- Q-B34-PHASE 결정**("phase 3 + 정정 기록 (Recommended)", 기록 `20261001-b26-phase3-cards`): 네 card(#45·B26pre·backfill·#1) `phase: 3`, 순서 그대로. 이 문서의 'phase 2' 표기를 고쳤다(§1.3·§1.4·§3.1·§3.2·§3.3·§4.3·§5.1·§5.12·§7·§8.1·부록 C.3 -- 역사 기록 문장은 '(v0.9.2) phase 3' 덧붙임). v0.9.1 정정의 '엄격 집합도 바뀐다'는 틀렸다 -- phase 2·3 엄격 집합은 둘 다 빈 집합이라 같다(`review_b26_final.md` F2, 부록 A H6). 남는 오케스트레이터 몫은 그대로: design 20 §10 DoD 범위 문구(네 card 제외).
20. (v0.6) **N3.10 MOD6 행과 CC-7a**: Phase 3 v6 UD-0 개정 문안이 MOD6 행의 `` `optimize_full_circuit_budget` 탐색부 `` 백틱을 MOD8 행으로 옮기면 MOD6 '대표 대상'에 탐색부를 가리키는 이름이 없다. CC-7a(#7)가 추출 함수 이름을 정할 때 N3.10 MOD6 행에 그 이름을 더하는 문구 정정을 같은 card 커밋에 넣는다(N3.10은 `plan_tables_hash` 입력이 아니다 -- Phase 3 v6 §9.1).
21. (v0.6) **folded json 설명 주석 3곳(F35)**: 판정 아님. 메타데이터 정정이라 #53 데이터 커밋에 넣고, 그 전에 B47(추적 md 재생성)과 같은 사용자 확인 묶음으로 보여 준다. 계획 정정 아님 -- 기록용.
22. **(v0.8) 결정됨(원칙 기본안 -- UD-0이 덮음, 4차 검토 S2): `normalized_margin`(CC-9)을 #23으로 앞당긴다.** 근거: 계획 749행 "SEAL_VIOLATION·`local_infeasible` = 위반 크기 / 그 봉인 항목의 허용오차 … 분모가 0이거나 정의되지 않으면 margin은 `null`로 기록하고 비교·정렬에 쓰지 않는다(빠뜨린 것과 구분된다)" -- #23 노드 충돌은 봉인 항목 1(428행, 분모 tol_V)이라 분모가 **정의된다**. v0.7 기본안('위반 크기·분모 기록 + margin `null`')은 그 레코드에서 `null`을 '아직 계산 안 함'으로 써 749행이 구분하라는 두 뜻을 섞었다. v0.7이 든 'IC9 때문에'는 근거 오인이다: 계획 IC9(827행) 원문은 "| IC9 | 중복 복붙 | 레지스트리 정본 하나, 타입 setter만 | `test_no_raw_duplicated_writes`: 원시 대입·중복 상수 grep 0 | 6b |"이고 margin 전용 규칙이 아니다 -- 'margin을 계산하는 곳은 이 함수 하나(IC9)'는 `00-common` §7.2가 IC9 취지를 적용한 문장이며 시점 근거('첫 소비자는 실패 캐시 정렬(N3.5, Phase 5)이라 그 변경 단위에서 만든다(WP-01)')도 같은 절의 것이다. 앞당긴 뒤에도 '함수 하나'는 지켜진다(#43·#25도 같은 함수를 `tol=None`으로 부른다). **같이 고칠 문구**(`00-common`, 이 design 승인 diff에 포함 -- `a796468` 줄): 109행 표 칸 '2 -- 실패 캐시 정렬 입력' → '2 -- 실패 레코드 margin·실패 캐시 정렬 입력', 263행 절 제목 '(CC-9, Phase 5)' → '(CC-9, Phase 4 -- `40-defect-fixes` #23)', 266행 '첫 소비자는 실패 캐시 정렬(N3.5, Phase 5)이라 그 변경 단위(`50-failure-cache`)에서 만든다(WP-01)' → '첫 생산자는 노드 충돌 실패 레코드(`40-defect-fixes` #23)라 그 변경 단위에서 만든다(WP-01). 실패 캐시 정렬(N3.5, Phase 5)은 다음 소비자', 540행 소비자·Phase 열 '실패 캐시 정렬 | 5' → '실패 레코드 margin(#23), 실패 캐시 정렬 | 4', 559행 CC-9 행 마지막 열 `50-failure-cache` → `40-defect-fixes`, 607행 순서 '… CC-5와 나머지 DF → CC-9(5) → CC-6(6a)' → 'CC-9는 Phase 4 DF-02 card와 함께 … → CC-6(6a)', 618행 `common-margin` 행의 design 열 `50-failure-cache` → `40-defect-fixes`. (v0.9, 5차 검토 m-1) `00-common` 265행(§7.2 `normalized_margin` 정의 문장 -- 'margin을 계산하는 곳은 이 함수 하나')은 **읽기만** 한다(시그니처·문장 그대로). **(v0.9, 5차 검토 N-S3) 계획 문구**(같은 승인 diff -- `0f23786` 줄): **1159행** N9.1 `50-failure-cache` 행 '`00-common` CC-9(`normalized_margin`), 실패 캐시 키·저장, …'에서 'CC-9(`normalized_margin`), '를 빼고, **1158행** `40-defect-fixes` 행 '… `00-common` CC-4(실패 규약 …' 목록에 '`00-common` CC-9(`normalized_margin`, DF-02 노드 충돌 레코드 margin)'을 더한다. **1002행** N6.1 Phase 5 행('실패 캐시, 시작점 선택(S3 레코드 v1: θ*·start별 결과·실패), margin 반환')은 **변경 없음** -- '실패 캐시의 margin 반환'(정렬 소비)이고 함수 생산 위치를 말하지 않는다. 1158·1159·1002행은 `plan_tables_hash` 입력 밖(계획 698행 EL3: 입력 = N4.1 `담당 Phase`·`강제 test`, N4.2 `도입`, N6.1 `Phase` 열, N3.12.2 -- 1002행은 N6.1이지만 바꾸지 않는다)이라 승인 종류는 UD-0 문안 diff다. 계획 749행·IC9 행은 바꾸지 않는다. **대안**(승인 질문 둘째 선택지): 계획 749행에 'CC-9 전에는 margin `null` + 위반 크기·분모 기록' 한 줄 -- 그 경우 계획 정정 커밋이 #23 병합 **전**이어야 하고(간선 '계획 정정 → #23'), #21 조건부 실측과 §10.6-0·E2는 margin 차원 없이 잰다.
23. **(v0.8) 닫음 -- 기록 원문으로 확인됨**(4차 검토 m6): `user_decisions.md` 원문이 이미 "실제 순서는 Phase 3 design: G1이 D0a보다 먼저(D0a가 G1 moved_defs 재사용), T0 독립"이라 적고, Phase 3 v7 §8.1 표도 G1 → D0a(§11-12)다. (v0.7 원문 -- 기록) **확정 순서의 Phase 3 부분(오케스트레이터 확인)**: `user_decisions.md` "card 순서"의 "Phase 3(card 묶음: T0·G1(32)·D0a·D0b·M…)"는 기록 자체가 '실제 순서는 Phase 3 design(G1 → D0a, T0 독립)'이라고 적는다. 이 문서는 그 읽기로 간선을 둔다(B33 → G1 → D0a → D0b, Phase 2 DoD·B33 → T0). 글자 그대로 'T0·D0a·D0b → G1'로 넣으면 순환이다(부록 A F1 C2). Phase 3 v7 문구와 맞는지 오케스트레이터가 확인한다.
24. (v0.7) **정보 -- Phase 3 E5 기준 해시(Phase 3 design에 전달)**: 읽기 (나)에서는 Phase 2 DoD 해시를 B34·B26-1 **전에** 잰다. Phase 3 v6 E5('E-LIB·E-INST 재측정이 Phase 2 DoD와 같은 해시')의 기준이 B34·B26-1(동작 변경 red-green)로 달라질 수 있다 -- Phase 3 design이 E5의 base를 'B33 병합본'으로 고칠지 정한다. Phase 4 E2의 base는 Phase 3 DoD라 이 문서에는 영향이 없다. (v0.8) Phase 3 v7 E5는 여전히 'Phase 2 DoD와 같은 해시'다(v7 901행) -- 전달 유지. **(v0.9.2) 닫음**: Phase 3 v8.2가 E5 기본안을 선례 모양(Phase 2 DoD 대상 커밋 `P2D` 대 Phase 3 마지막 병합본, 의도된 필드 `MASK_META = ("rails",)`만 B26-1 계약값으로 따로, `EXCL_INST` 없음)으로 정했다. 이 문서도 E11의 E-LIB를 같은 모양으로 적었다(P-37) -- 그리고 #17이 같은 `meta["rails"]`를 Phase 4에서 다시 바꾼다(§5.4 #17 (c)).
25. **(v0.8, 4차 검토 S6) 계획 N3.6 봉인 항목 1에 '노드의 tol_V' 한 줄(오케스트레이터)**: 428행 '같은 노드에 도달한 경로별 값의 최대 차 ≤ tol_V'와 439행 'tol_V = (kind, L 앵커, VDS)별 LOO 보간 오차의 최댓값'은 노드 하나에 어느 소자의 (kind, L, VDS)를 쓰는지 정하지 않는다. 기본안(#23) = 그 노드에 서로 다른 값을 준 두 경로 소자의 tol_V 중 작은 쪽. 계획 문구: "노드 충돌의 tol_V는 그 노드에 값을 준 경로 소자들의 tol_V 중 최솟값(판정 기록에 그 소자를 남긴다)". ~~`plan_tables_hash` 입력인지는 #23 작성 전 실측이 확인~~ **(v0.9, 5차 검토 m-7) 확정: 입력이 아니다** -- `plan_tables_hash` 입력은 계획 698행 EL3의 N4.1 `담당 Phase`·`강제 test`, N4.2 `도입`, N6.1 `Phase` 열, N3.12.2 쓰기 경로표이고 N3.6은 없다. 승인 종류 = 문안 정정(UD-0 diff).
26. **(v0.9, 5차 검토 N-S2) 계획 정정 없음 -- 기록**: vsb 비교 허용오차(`reconcile_vsb_from_nodes`·`audit_vsb_consistency`의 `tol=1e-6`)는 계획 어디에도 없는 코드 상수다. 기본안 P-36(비트 동일, `node_tol` 명시 전달)은 계획 문장을 바꾸지 않는다(DF-02 행 '봉인 항목 1 ≤ tol_V'와 독립 -- vsb 비교는 봉인 항목이 아니라 저장값과 전체 그래프 재계산의 일치). #23 판정 기록에 두 함수의 비교 규칙과 영향 실측(§5.5 #23 -- (v0.9.1, R6-S1) 무동작이 아니라 current_reuse θ* 마지막 자리 변경이 기대, DEC-40은 §7.4)을 남긴다.

---

## 10. 인터페이스 (N9.2-2 -- v0.2 부록 B가 '보강판 과제'로 미뤘던 5건)

모듈 표기는 §3.1(D0b 확정 전 계획 MOD). 이름은 card 작성 전 test glob 충돌 grep 대상이다.

### 10.1 `fallback_events` (V8, #13)

**10.1-1 기록 단위와 함수**(v0.5: MOD4. **(v0.6) 모듈은 P-33** -- I·D 지점이 있는 MOD 중 가장 작은 번호. `FailureRecord`도 MOD2다(`00-common` §7.1) -- v0.5의 'N3.14 예외·`FailureRecord`와 같은 계층'은 두 기호의 모듈이 달라 맞지 않는 문장이었다):
```python
@dataclass(frozen=True)
class FallbackEvent:
    site: str        # "<모듈 이름>::<정규 이름>#<태그>" -- 줄 번호가 아닌 안정 id(태그는 한 함수 안 여러 지점 구분)
    kind: str        # 10.1-3의 어휘: "derivation_skipped" | "alternate_path" | "declared_default"
    device: str | None
    detail: str      # 첫 발생의 상세(선언 이름·대체된 값·원래 예외 타입)
    count: int       # 같은 (site, kind, device)의 발생 수

def record_fallback(site: str, kind: str, *, device: str | None, detail: str) -> None
def collect_fallbacks() -> ContextManager[list[FallbackEvent]]   # 실행 진입점이 연다
```
* 수집기는 `ContextVar` 하나(CC-7b의 계측 `ContextVar`와 같은 방식, 새 전역 가변 상태 없음). 실행 진입점(MOD10 `run_gmid_design_pipeline`, 그 전에는 `optimize_full_circuit_budget`)이 연다.
* 수집기가 열려 있지 않으면 `record_fallback`은 아무것도 하지 않는다. V8의 정의 범위가 '정본 spec 실행 결과'이고 계측은 출력만 바꾸므로 동작 경로에는 영향이 없다. 단위 test가 계측을 보려면 `collect_fallbacks()`를 직접 연다.
* 집계: (site, kind, device) 키 dict, 값 = 첫 detail + count(§4.4, NFR-2). 출력은 site 순 정렬 목록(결정론).

**10.1-2 산출 위치**: 성공 실행 = `optimize_full_circuit_budget` 결과 dict 키 `fallback_events` + `instance.json` 최상위 키 `fallback_events`. 실패 실행(#6 뒤 하네스가 쓰는 실행 기록 JSON) = 같은 키. 키가 없으면 E1 FAIL(계측 미배선).

**10.1-3 분류(부록 C의 처리 열 코드)**

| 코드 | 뜻 | `fallback_events` |
|---|---|---|
| R | 제거(거부로 교체) -- 담당 card 지정 | 아니오(사라진다) |
| I | 선언·유도 실패를 '없음'이나 다른 경로로 바꿈 → **계측** | 예, kind = `derivation_skipped`·`alternate_path` |
| X | 격자·후보점 배제(그 점을 쓰지 않을 뿐 값을 지어내지 않음) | 아니오 -- CC-4b(#10)가 잡는 타입을 LUT 정의역 오류로 좁힌다 |
| F | 탐색 후보 실패 기록(N3.14 '탐색 중 처리 = 실패 기록') | 아니오 -- `FailureRecord`(V8 밖) |
| N | 비운영·도구·구조화 반환(조용하지 않음) | 아니오 |
| D | 선언값 리터럴 기본값(`.get(k, <스칼라>)`·`setdefault`) | 10.1-4 규칙으로 R 또는 I(kind = `declared_default`) |
| C0 | 빈 컨테이너 기본값(`{}`·`[]`·`()`·`set()`) = '선택 선언 없음 = 빈 집합' 규약 | 아니오. 단 **필수 선언 키**의 빈 기본값이면 R(해당 card에서) |

**10.1-4 발동 규칙(D·I 지점)**: #13 작성 전 실측으로 지점마다 발동 계수를 잰다. 대상 = 하네스 정본 실행 4회로 + E-LIB 9회로(`load_topology`·audit, SPECS 4회로는 평가까지).
* **측정 방법(v0.4, 검토2 S9)**: CC-8 `activations_out`은 **쓰지 않는다** -- 그것은 card가 계측을 단 기능만 센다(`00-common` §11). D·I 지점은 #13 전에는 계측이 없으므로 그대로 재면 전부 0 → 아래 규칙으로 전부 R(거부)가 되어, 실제로 발동하는 지점이 정본 실행을 깨뜨린다. 대신 **사본 계수 래퍼**(저장소 쓰기 0, 스크립트는 `_drafts/`에 남김)를 쓴다: AST로 지점마다 (a) `.get("k", d)`·조건식 기본값(SR 7411) → 키가 **없을 때만** 세는 래퍼(`k not in obj`일 때 계수 -- 기본값이 실제로 쓰인 횟수), (b) `setdefault("k", v)` → 키가 없을 때 계수, (c) `x.get(k) or <리터럴>` → `or`가 리터럴로 넘어갈 때 계수, (d) `I` 핸들러 → 핸들러 진입 계수. '줄 실행'(`sys.monitoring` LINE)은 `.get`이 키가 있어도 실행되므로 (a)~(c)에 쓰지 않는다(핸들러 진입 (d)에는 써도 된다). 결과는 지점 × 회로 표로 #13 spec card '작성 전 실측'에 둔다. CC-8 병합을 기다리지 않는다(§8.1).
* 발동 0 → **R**(DEC-76 "발동 0인 폴백은 구현하지 않는다": 거부로 교체, 거부 메시지에 선언 이름).
* 발동 > 0 → **I**(계측)로 두고 원인 card를 지정한다(선언 추가·유도 규칙). V8 = 정본 실행 0이므로 Phase 4 DoD 전까지 원인 card가 병합돼야 한다. 원인 card가 Phase 4 범위 밖이면(예: vsb 기본값의 구조 제거 = 6b DF-01) 그 지점이 E1을 FAIL시키므로 **N7 추가 요청 대상**이다(N9.2-8). card 작성 전 실측에서 그런 지점이 나오면 이 design 개정으로 다룬다.
* 이미 담당이 있는 D 지점: `W_bounds`·`min_finger_w`(#28), `gm_id_bounds`·margin 0.05·`min_vds_by_role`·`_DEFAULT_METRIC_STAGE_BUDGET_GM_ID`(#38), `vsb` 기본값(10.1-4 적용 뒤 #24 또는 #22).

**10.1-5 계측 지점 전수**: 부록 C(핸들러 59, 스칼라·튜플 기본값 77 + 조건식 기본값 1(SR 7411), 빈 컨테이너 35, B34 사이트 -- 담당별로 나눔, C.3). 실측 도구·명령은 부록 A. Phase 3 뒤에는 같은 AST 규칙으로 MOD 파일에서 다시 센다(D0b 뒤 줄 번호 갱신). **(v0.4) 부록 C '운영 도달' 열은 HEAD V7 그래프 기준**이다 -- 레지스트리 바인딩·생성자 간선이 없고(레지스트리 값 함수가 미도달로 나온다: 예 `_metric_flicker_plus_thermal_sum`·`_metric_smallsignal_ratio_db`·`_metric_smallsignal_gain_db`는 `_METRICS_REGISTRY` 등록인데 '아니오(근사)') 비운영 파일로의 이름 폴백 누수가 있다(B33). **처리 열(R/I/X/F/N/D/C0)은 도달 열에 기대지 않는다**(D·I는 10.1-4의 발동 계수가 판정하고, 나머지는 코드 형태로 정한다) -- 그래서 설계 영향은 없고, B33 병합 뒤 도달 열과 F17 '운영 도달 52'를 다시 잰다.

### 10.2 공정 기록 JSON (U-30, #28)

* 파일: `A/pdk/sky130_fd_pr.process.json`(이름은 card에서 glob 충돌 grep) [prep: `prep_u27_u30.md` §3.4].
* 스키마(값은 SI m, 모든 값 항목에 출처):
```json
{
  "schema": "process_record/1",
  "pdk": {"name": "sky130_fd_pr", "commit": "<C:\\pdk\\sky130_fd_pr HEAD>"},
  "min_finger_w": {"value": 0.42e-6, "rule": "difftap.2", "source": "google/skywater-pdk docs/rules/periphery/periphery.csv"},
  "l_min":        {"value": 0.15e-6, "rule": "poly.1a",   "source": "(같은 파일)"},
  "l_grid_step":  {"value": 0.005e-6, "source": "sky130hs.tlef MANUFACTURINGGRID"},
  "vth0_slope":   {"source": {"file": "<mismatch.corner.spice 경로>", "params": {"nmos": "<param>", "pmos": "<param>"}}},
  "finger_pitch_overhead_m": {"value": null, "reason": "I-A12 미확보"},
  "passive_unit_area":       {"value": null, "reason": "U-36, 7b 전"}
}
```
* `vth0_slope` 값은 파일에 적지 않고 로더가 모델 파일에서 읽어 캐시한다(근거 하나).
* 로더(MOD1): `load_process_record(path) -> ProcessRecord`(실행당 1회, 미지 키·출처 없는 값 거부 = `SchemaRejectedError`). 유도: `w_bounds_lower(rec) = rec.min_finger_w`.
* 연결: U-27 npz 메타에 `process_record_sha256`. LUT 로드 때 해시가 다르면 거부.

### 10.3 `supply_roles` (UD-1 (C), #17)

* 자리만 계획에 둔다(첫 예외 회로와 함께 코드, 만들면 배선). 모양 [prep: `b26_decision_table.md` §1.4]:
```json
"supply_roles": {"<레일 넷>": {"role": "rail_high" | "rail_low" | "rail_mid"}}
```
* 게이트: 키 집합 = `supply_nets`(`_` 접두 제외), `rail_high`·`rail_low` 각 1 이상(**개수 상한 없음**), 구조 증거와 모순 거부, `supplies_v`가 있으면 min(high) > max(mid) > max(low).
* 선언이 없으면 구조 규칙(PMOS source만 = hi, NMOS source만 = lo, 둘 다 아님 = mid, 둘 다 = 거부).
* #17 코드가 만드는 것: `RailDeclaration`에 `polarity: Mapping[str, Literal["hi", "lo", "mid"]]` 필드(구조 규칙 결과).

### 10.4 `vdd` 유도 함수 (MG1, #21)

```python
@dataclass(frozen=True)
class RailVoltages:
    by_net: Mapping[str, float]   # supplies_v 그대로
    hi: float                     # max(by_net.values())
    lo: float                     # min(by_net.values())
    @property
    def span(self) -> float: ...  # hi - lo

def rail_voltages(spec: Mapping, rails: RailDeclaration) -> RailVoltages
```
* 모듈: MOD2(spec 로드 계층) [D0b 확정 뒤].
* 거부: `set(supplies_v) != set(rails.nets)` → `SchemaRejectedError`, spec에 스칼라 `vdd` → 옛 키 거부(CC-5 행).
* 계산은 spec 로드당 1회. **보관 위치는 spec dict 밖**(검토2 M4): spec에 키를 더하면 `instance.json`·E-INST 정규화 해시가 바뀌어 #21 equivalence가 깨질 수 있다. ~~`RailDeclaration`과 같은 계층(로드 결과 객체 → 평가 문맥 `ctx`)에 두고~~ **(v0.9.3 -- 실측 `p4_card21_rails_measure.md` §5 권고)** `load_topology`의 `meta`(`meta["rails"]` 포함)와 `RailDeclaration`에는 싣지 않는다 -- spec 로드 결과(하네스 `spec_fn()` 반환을 받은 쪽) → 평가 문맥 `ctx`에 둔다(계산 지점은 spec과 `meta["rails"]`가 만나는 `_build_theta_evaluator`의 `load_topology` 직후. 시제품 x2 `meta["rail_voltages"]`·x4 `RailDeclaration.voltages`가 '로드 결과 객체'의 두 오독이고 #21 oracle (c) 해시 같음이 둘 다 잡는다). 평가 루프 안 호출 0(계수 래퍼로 관찰 -- 시제품의 spec dict 식별자 캐시는 평가 루프가 spec을 복사해 current_reuse에서 build 1721회였다, 보고 §7: spec 로드당 1회 계산해 `ctx`에 둔다).
* F4 20줄의 교체는 **읽기의 뜻으로 분류**한다(v0.4 -- 뜻 네 가지, F25 S1이 이 분류로 비트 동일을 보였다):

| 뜻 | 값 | HEAD 줄 |
|---|---|---|
| 폭(레일 사이 전압 예산·KVL 합) | `span` | 1729(→1782 `const`), 3254, 7068, 7222, 7228, 8233, 8242(메시지), 8277 |
| **노드전압 프레임 인자**(`propagate_node_voltages`·`derive_vsb_from_nodes`·`reconcile_vsb_from_nodes`의 `vdd` -- rail_lo를 0.0에 고정한 프레임에서 rail_hi의 값) | **`span`**(#21에서는 프레임을 바꾸지 않는다. 절대 프레임 전환은 #22) | 7290·7295·7296, 7445·7449·7450, 8652 |
| 가장 높은 레일 절대 전위 | `hi` | 4626(`rail == "vdd"` 갈래), 10157·10159(pmos 갈래) |
| 두 레벨 합의 기준(센터링: 두 게이트 레벨 합 = 레일 전위 합) | `hi + lo` | 4653, 10160 |

  같은 함수의 **레일 0 V 리터럴 3곳**(4626 `else 0.0`, 10157·10159 nmos 갈래 `0.0 +`)은 `vdd` 읽기가 아니지만 같은 뜻의 짝(`lo`)이라 #21이 함께 바꾼다 -- 바꾸지 않으면 전위형 metric이 S_B에서 Δ만큼 움직이지 않아 IC11이 FAIL한다(F25 current_reuse `vop1_level_v`). 레일 **이름** 비교(`spec["rail"] == "vdd"`)는 #17(극성) 몫이다. 분류표는 #21 interface card에 줄마다 적는다. 원점 이동 전 4회로(최저 레일 0 V)에서는 네 뜻이 같은 값이라 #21은 equivalence가 성립한다. 뜻을 잘못 고른 줄은 #21 자신의 IC11 rail2가 잡는다(F25 S2: 노드전압 프레임 인자를 `hi`로 고르면 vsb 0.9 V 차).
* 극성(#17)이 있으면 게이트가 `hi`의 넷이 `rail_high`인지 대조한다(UD-1 게이트 4번과 같은 규칙).

### 10.5 전후 비교표(E2) 정규화와 허용오차

* 비교 단위(회로마다): 결과 종류(θ* / N3.14 실패 클래스), θ*, metric 전부, `instance.json` 정규화 해시, 실패면 margin과 실패 전 setup 양(소자별 VGS·VDS·VSB·gm_id·W).
* 정규화: `json.dumps(obj, sort_keys=True)`에 float는 `float.hex`로, 경로 값 키는 `20-dead-code-dup` §3 E-INST 정의의 제외 규칙을 그대로 쓴다(재서술하지 않는다). 해시 = sha256.
* 허용오차: **기본은 비트 동일**(equivalence·무동작 card). 동작 변경 card는 차이를 허용오차로 흡수하지 않고 항목마다 원인 card id와 DEC-40 승인 id를 붙인다(차이 = 기록 대상). 예외는 원점 이동 불변(IC11, #21·#22·#51)뿐이며 식은 10.6이다.
* **(v0.8, m1) margin 비교(E2)**: 같은 실패 클래스에서 둘 다 수이면 비트 동일이 기본이고 다르면 차를 기록하고 원인 card를 붙인다(위 규칙 그대로). 둘 다 `null`이면 같음, 한쪽만 `null`이면 다름(분모가 정의되는지가 바뀐 것 -- 원인 card). 클래스가 다르면 margin을 견주지 않는다(계획 749행).

### 10.6 IC11 감도 전파 허용오차 (#21 test 쪽 판정기)

계획 N4.1 IC11: "VGS·VDS·VSB·gm_id·W·metric(dc·ss·ls 전부)이 허용오차(전압 tol_V, 그 밖은 tol_V 섭동의 감도 전파값) 안에서 같음". 이를 다음으로 적는다.

**10.6-0 대상 회로·평가점·비교 단위**
* 두 레일 선언 S_A(현 `supplies_v`)와 S_B(모든 레일을 같은 Δ만큼 이동)로 **같은 θ 평가점**을 평가한다. Δ = −span/2(계획 IC11 예 (1.8, 0) 대 (0.9, −0.9), U-26 (a)의 분할 레일 형태 -- 2레일 회로에서 Δ = lo_B − lo_A). θ는 test **입력** 상수(대상 회로의 하네스 θ*를 card base 판정 기록에서 옮긴다 -- 기대값이 아니다).
* 대상 회로 = 하네스 SPECS의 2레일 회로 중 card base에서 θ 평가가 끝나는 회로, 우선순위 **current_reuse → folded_cascode**. 근거(F26·F27): current_reuse는 노드전압 충돌 0.22272 V·VS 축 밖 조회가 양수 0.81~1.5 V뿐(U-27b의 0~1.8 V가 덮음), folded는 충돌 최대 1.6 V·축 밖 조회에 음수(M7 −0.65)와 1.6·1.8. two_stage·nmcnr는 I-C11(UD-6). 평가 비용: 한 점 평가 current_reuse 약 15~23 s, folded 약 14~17 s(`C:/g61` 측정, 모델 빌드 포함), 판정 한 번 = 2 + 2·(레일 수) = 6회 평가.
* **결과 단위 불변**: 평가 결과가 성공이면 아래 10.6-1의 양 전부를 비교한다. 실패면(#6 뒤 N3.14 클래스, 그 전 `ValueError` 계열) **같은 실패 클래스 + margin 차가 허용오차 안 + 실패 전까지 설정된 소자 양**을 비교한다(v0.3 #51의 비교 단위와 같은 형태). **(v0.8, S2·m1) margin 비교 규칙**: margin은 `normalized_margin`(CC-9 -- #23이 만든다) 값이다. 둘 다 `null`이면 같음, 한쪽만 `null`이면 다름(FAIL), 둘 다 수이면 **위반 크기(분자, 전압 양) 차가 tol_V 안**이고 분모(tol_V 함수 값)가 두 평가에서 같음 -- 10.6-1의 전압 양 규칙을 분자에 적용한 것이다(원점 이동은 VDS·kind·L을 바꾸지 않으므로 같은 노드의 tol_V는 같아야 하고, 다르면 FAIL). **(v0.9, 5차 검토 정보)** '분모가 같음'은 **앵커 단위**로 판정한다: tol_V는 (kind, L 앵커, VDS 앵커)의 함수이므로, 두 평가에서 그 노드의 분모를 정한 소자(§9-25)의 (kind, L 앵커, VDS 앵커)가 같으면 같은 분모다 -- #22 뒤 절대 프레임에서 VDS가 비트 단위로만 달라 분모 **값** 비교가 가짜 red를 내지 않게 하기 위해서다(분모 값을 직접 비교하지 않는다). 비트 차이가 앵커 경계를 넘어 앵커 자체가 달라지면 FAIL로 두고 그 소자·VDS 두 값을 기록한다(드문 경우 -- 허용오차를 새로 두어 덮지 않는다). #21 interface card가 이 문장을 옮긴다. Phase 4의 실패 레코드 중 margin이 수인 것은 분모(그 봉인 항목의 허용오차)가 있는 #23 노드 충돌뿐이다(계획 749행) -- #43(기둥 VDS 합, 계획 396행 '검사 대상이 아니다')·#25(축 밖, LR3에 허용오차 없음)는 같은 함수가 `null`을 돌려준다. v0.7의 'IC9 때문에 Phase 4 card는 margin 수를 계산하지 않는다'는 근거 오인이라 철회했다(§9-22). #23·#25가 병합되고 UD-17이 해소되지 않으면 두 대상 회로가 실패로 끝날 수 있다(F26·F27) -- 그때도 판정은 정의돼 있지만 실패 지점 뒤의 양(예: reconcile 뒤 vsb)은 비교되지 않아 검출력이 준다. 판정 기록에 '성공/실패 단위' 중 무엇으로 판정했는지 남긴다.
* **(v0.5) 대상 선택 규칙 보강(P-32, [ud17])**:
  * 우선순위 근거를 원인 분석으로 바꾼다: current_reuse = 충돌 원인 1개(Vom1 이중 구속, UD-17d)·진짜 축 밖은 M9a·M18a 0.025 V(오차 0.7 %)뿐, folded = 원인 3개이고 UD-17a 전에는 **물리적 동작점이 없다**(축 밖 4소자 전부 F27 파생). 그래서 folded는 #53 뒤에만 후보다(그때도 일관된 노드전압에서 M7 W가 `W_bounds` 밖이면 θ 평가가 끝나지 않을 수 있다). **(v0.6)** folded는 #53이 UD-17c (i)·(ii)로 끝났을 때만 후보다((iii)이면 #23 뒤 실패로 남는다 -- F32). current_reuse는 #54가 UD-17d (i)이면 설계 변경이 함께일 때만 성공 단위를 준다(F33).
  * #21 base는 #23 뒤다. 그때 #54가 없으면 대상 후보 둘 다 θ 평가가 SEAL_VIOLATION(충돌)으로 끝날 것으로 본다(F27 -- tol_V 값 [미확인]). 그때 #21은 실패 단위로 판정하되, **#21 작성 전 실측이 먼저 실패 단위 판정기의 검출력을 잰다**: §10.6-2의 S2(노드전압 프레임 인자 오분류)·S3(DF-24 부분 수정) 합성 상태가 실패 단위에서도 FAIL(실패 클래스·margin·실패 전 setup 양 중 하나가 허용오차 밖)로 갈리는지. 갈리면 그대로 진행, 갈리지 않으면 #21은 #54를 기다린다(§3.3 '조건부' 간선). 측정 없이 실패 단위 PASS를 rail2의 근거로 쓰지 않는다(게이트는 '실제로 거부한다'를 먼저 보인다).
  * **Phase 4 DoD(E3)는 성공 단위**다: 계획 N4.1 IC11의 비교 양(VGS·VDS·VSB·gm_id·W·metric)은 성공한 평가에서만 정의되므로, 실패 단위 PASS는 card 중간 병합본의 무회귀 판정으로만 쓴다. 성공 단위를 주는 것은 #54(또는 #53)다(§6 E3, §9-17).

**10.6-1 허용오차(검토2 S7 반영 -- ±τ, 레일별 1차 상한의 합)**
* 전압 차 양 q ∈ {VGS, VDS, VSB}(소자별): |q_A − q_B| ≤ tol_V(kind, L, VDS_A)(#23의 MOD1 함수).
* **전위형 metric**(노드 절대 전위를 돌려주는 metric type -- HEAD에서는 `rail_referenced_voltage` 1종. 목록은 #21 interface card가 `_METRICS_REGISTRY` 전수 판독으로 type 단위로 적는다 -- 회로·metric 이름이 아니라 type): |(q_B − Δ) − q_A| ≤ tol_V. 근거: 절대 전위는 원점 이동에서 Δ만큼 움직이는 것이 정의다(F25: current_reuse 두 metric이 정확히 −0.9 V). 이 type을 '같음'으로 비교하면 올바른 엔진이 FAIL한다 -- 계획 IC11 행 문구 정정 요청(§9-13).
* 그 밖의 양 q(소자별 gm_id·W, 나머지 metric): |q_A − q_B| ≤ tol_q,
  **tol_q = Σ_{r ∈ supply_nets} max(|q(S_A; V_r + τ) − q(S_A)|, |q(S_A; V_r − τ) − q(S_A)|)**, τ = 평가점의 모든 소자에 대한 tol_V(kind, L, VDS)의 최댓값.
  * 근거: 계획에서 같은 종류의 허용오차는 모두 **1차 선형 상한**이다 -- N3.6 `tol_I = tol_V × gm`(전압 허용오차를 감도로 전파), N3.8 SPICE 비교 'AC gain = 노드 허용오차를 소신호 감도로 전파한 값', N4.1 IC2 '그 밖의 연속 필드 ≤ tol_V 섭동의 감도 전파값'. 여러 레일의 오차는 동시에 들어오므로 1차 상한은 레일별 기여의 **합**이다(v0.3의 레일별 **max**는 과소 → 가짜 red 위험). 한쪽(+τ) 차분은 비단조·꺾임 근처에서 과소이므로 **±τ 중 큰 쪽**을 쓴다. 새 상수 없음(τ는 tol_V에서, 섭동 방향은 선언 레일에서), topology 무관(`supply_nets`만 읽음).
  * **(v0.7, m4) τ에 최댓값을 쓰는 근거**: N3.6 `tol_I` = `tol_V` × 해당 순환 블록 소자 gm의 **최댓값**과 같은 형태다. 최댓값은 허용오차를 넓히는 쪽(판정을 느슨하게 하는 쪽)이므로 판정 기록에 τ 값과 그 τ를 준 소자(kind, L, VDS)를 함께 남긴다(계약).
  * **이산 양**(finger 수 등): 섭동이 경계를 넘으면 tol_q가 커져 판정이 약해진다 -- 판정 기록에 **양별 tol_q**를 남긴다(계약).
* tol_q = 0인 양(전압과 무관한 양)은 비트 동일을 요구한다.
* 섭동 평가가 실패하면(평가점 자체는 성공인데 ±τ 섭동이 실패) 판정은 ERROR다(PASS로 세지 않는다).

**10.6-2 검출력(실측 F25 -- v0.3의 'F16 NMOS 수' 서술을 대체, 검토2 M6)**
* #21만 병합된 엔진(노드전압 프레임의 lo = 0 고정 그대로): 뜻대로 분류하면 S_A와 S_B가 **비트 동일**(folded·current_reuse 소자 양 전부) -- rail2는 PASS가 정답이다. 그래서 #21에 xfail을 두지 않는다.
* 판정기가 잡아야 하는 것(자기 점검 입력 -- test-author가 합성 평가기로 구성): (i) 노드전압 프레임 인자를 `hi`로 잘못 분류한 상태(S2): vsb 0.9 V 차(M1·M2·M5), gm_id·W 차 (ii) DF-24 부분 수정 상태(S3, 레일만 절대 전위로 고정): nmos vsb −0.9 V(6소자), M8 gm_id 25.5 → 25.0, W 56.6 → 88.8 µm (iii) 전위형 metric을 '같음'으로 비교하는 판정기 구현(F25 current_reuse 두 metric) -- 올바른 엔진에서 FAIL하므로 판정기 쪽 결함이다.
* tol_V 값은 #23이 정한다 **[미확인: 값]**. 위 차이(0.9 V)보다 tol_V가 작아야 검출되는데, tol_V는 LUT 보간 오차라 이 크기가 아님을 #23 병합 때 판정 기록에 수로 남긴다.

**10.6-3 소유·V4**
* 소유: test 쪽 helper(`A/tests/contracts/`, test-author), **#21의 test 커밋**. 엔진 함수로 만들지 않는 이유 = Phase 4에 엔진 소비자가 없다(봉인은 6b). 소비자는 같은 card의 `rail2` test다(만들면 배선).
* V4: 기대값(S_A 결과)이 피검 함수 호출로 만들어지므로 규칙 (1) 발견이 난다. 선례 `20260923-c9-v4-exempt`와 같은 모양의 **V4 규칙 (1) 면제 승인 1건**이 #21의 착수 조건이다(§7.3). V4 면제는 test id에 묶이고 test 본문 해시에는 묶이지 않으므로(면제 묶기 card가 같은 부류 누수를 V4 백로그로 넘김 -- 검토2 M3) 승인 범위 설명에 **"이 test 본문이 바뀌면 재승인"**을 적는다. 규칙 (2)(식 복사)는 해당 없음(허용오차는 섭동 실행 결과이지 피검 식의 재서술이 아니다).

### 10.7 MOD1 LUT 정의역 오류 (P-34, #25 -- v0.7, 3차 검토 m3)

```python
class LutDomainError(ValueError):      # 이름은 초안 -- #25 작성 전 glob·옛 키 충돌 grep
    axis: str                          # "L" | "VGS" | "VDS" | "VS"
    value: float                       # 요청 값
    grid_min: float                    # 그 축 격자 최솟값
    grid_max: float                    # 그 축 격자 최댓값
    kind: str | None                   # "nmos" | "pmos"(보간 함수가 아는 경우)
```
* 모듈: MOD1(보간 함수 입구). MOD1은 N3.14 예외를 import하지 않는다(P-34, `00-common` §7.1).
* **기반 클래스 = `ValueError`(기본안)**. 근거: HEAD의 LUT 역산 실패(`vgs_for_gm_id` 등)가 `ValueError`라 #10이 X 핸들러를 좁히는 'LUT 정의역 오류' 집합과 한 계열이 된다((v0.9, 5차 검토 m-4) v0.7 첫 문장의 'I-C11 known-limitation xfail·`InfeasibleSizingError ⊂ ValueError` 관계를 깨지 않는다'는 철회한 근거라 지웠다 -- 그 xfail은 KVL 실패이고 LUT 정의역 오류와 무관하다, 아래 v0.8 문장). 위험 = 지금의 넓은 `except ValueError` 핸들러가 이 오류를 삼키는 것 -- 그것은 P-34 X 핸들러 규칙(#25)과 #10의 타입 좁히기가 막는다(삼키는 합성 구현에서 test FAIL -- §5.6 #25 oracle). 기반을 `ValueError`가 아닌 것으로 바꾸면 위 xfail·핸들러 목록을 다시 재야 하므로 #25 작성 전 실측이 'X 15곳·광범위 `ValueError` 핸들러(F5)가 이 오류를 어떻게 받는지'를 표로 둔다. **(v0.8, 4차 검토 m2)** 반대 선택의 근거 중 'I-C11 xfail `raises=ValueError`'는 KVL 실패라 LUT 정의역 오류와 무관하다 -- 그 줄은 근거에서 뺀다. 계획은 `SchemaRejectedError`를 '`Exception` 직접 하위 -- 기존 `except ValueError`와 후보 실패 처리가 삼키지 않게'로 정했다(N3.14 표). 기본안 `ValueError`는 #10의 'LUT 정의역 오류' 집합(HEAD 역산 실패가 `ValueError`)과 한 계열이라는 근거로만 유지하고, 위 표가 **MOD1 raise 지점부터 집계 지점·`SearchFailedError`까지 경로 위의 모든 `except ValueError`/`except Exception`**(F5: SR 26·6, SD 4·0, 하네스 1·2 중 그 경로)를 다뤄야 한다 -- #25가 #10보다 먼저 병합되므로 그 사이에는 #10의 좁히기가 없다. 경로 위 핸들러 중 이 오류를 삼키는 것이 하나라도 있으면 #25 범위에서 그 핸들러를 고치거나 기반을 `Exception`으로 바꾼다(card 작성 전 실측 결과로 정함).
* 변환: 집계 지점(MOD4 이상)이 `SealViolationError`(레코드 항목 `lut_axis_out_of_range`, 소자 + 위 필드)로 바꾼다. 필드는 그대로 옮긴다(P-28 원인 보존).

---

## 11. I-C11 해소 설계 (N9.1 필수, U-09)

### 11.1 현 상태(HEAD 실측, F15)

| 회로 | 실패 | 원인 기록 |
|---|---|---|
| two_stage_ota | `_hr_verify_group_kvl_sum`의 `ValueError`: `stage1_out` 그룹 VDS 합 2.37965 V ≠ vdd 1.8 V(diff +0.579654 V). M4 = 0.9172(`vds_match_vgs_of` M6 -- DC), M2 = 0.9(compensation -- AC 목표에서 정함), refs M5 = 0.5625(헤드룸) | 세션41(`.ai/context.md` 12380~12440행): 사용자가 `stage1` → `stage1_ref`/`stage1_out` 분리를 "올바른 방향이니 유지"로 확정, M4+M2+M5 불일치는 "DC/AC 조율 없이는 못 푸는 문제" |
| nmcnr_amplifier | 모든 θ 격자점 infeasible. 마지막 사유: `stage2_diode_ref` 그룹 예산 1.5 V 중 0.525 V를 배정할 곳이 없음(구간 제약 diode M203 ∈ [0.6375, 0.975]) | 엔진 메시지 자체가 "이 컬럼에 선언되지 않은 소자/수동소자가 있거나 vertical_stack_id 선언이 실제 직렬 경로와 다르다"고 가리킨다 |

둘 다 N3.14 클래스가 아닌 `ValueError`이고 하네스는 exit 0이다. 관련 test: xfail strict 3건 + known_limitation 3건(`20260922-c9-ic11-split`), V4 면제 2건(`20260923-c9-v4-exempt`, 'Phase 4 I-C11 해소 시 재검토' 명시, 백로그 B9·B12).

### 11.2 무조건 하는 것 -- #43 실패 명시화

원칙(조용한 실패 금지, N3.14)만으로 정해진다. KVL 불일치·예산 배정 불가를 `SealViolationError`(항목 = 기둥 KVL, 소자 목록, 위반 크기)로 바꾸고, 탐색은 후보 실패로 기록한 뒤 계속한다. 클래스 근거: 계획 N3.14 SEAL_VIOLATION 행(742행, 탐색 중 처리 = 실패 기록). `local_infeasible` 실패 레코드(739행)는 층 0(DEC-71 기둥 조립, 미구현)의 몫이고, 이 검사는 `_evaluate` 안의 헤드룸 해석 단계라 쓰지 않는다.

**판정 경계와 margin(v0.4, 검토2 S8 -- 무엇을 왜)**:
* **판정 경계 = HEAD 그대로**: `abs(Σ VDS − span) > 1e-9 × max(span, 1)`(SR 7068~7069, `vdd` → `span`은 #21). 계획 N3.6 항목 8의 '멤버 수 × tol_V'로 **바꾸지 않는다**. 이유: (1) 항목 8은 DEC-64 v2 `kvl_branch`(게이트-소스 LUT VGS 합) 등식의 봉인이고, 이 검사는 엔진이 **배정한** VDS의 합이 폭과 같다는 대수 불변식이다 -- LUT 보간 오차가 판정량에 직접 들어가는 항목이 아니다 (2) 경계를 허용오차로 넓히면 잔차가 1e-9와 Σ tol_V 사이인 그룹이 거부 → 통과로 바뀌는 **동작 변경**이고, 허용오차 기반 봉인 구현의 담당은 6b(`6b-node-voltage-seal` '봉인 항목 구현')다 (3) #43의 red-green은 실패 **형태**(클래스·exit code)에 관한 것이라 경계를 바꿀 필요가 없다 -- 알려진 두 사례(two_stage +0.58 V, nmcnr 0.525 V 미배정)는 어느 경계로도 위반이다.
* ~~margin = 위반 크기 / Σ_{m ∈ 기둥 멤버} tol_V~~ **(v0.7, 3차 검토 S1) margin = `null`**. 이유: 계획 749행 margin 정규화식은 SEAL_VIOLATION·`local_infeasible`에 대해 '위반 크기 / **그 봉인 항목의 허용오차**'이고 "분모가 0이거나 정의되지 않으면 margin은 `null`로 기록하고 비교·정렬에 쓰지 않는다". 위 경계 근거 (1)대로 이 검사는 허용오차를 가진 봉인 항목이 아니라 대수 불변식이므로 분모가 정의되지 않는다. (v0.8, 4차 검토 m6) 계획 396행이 직접 뒷받침한다: "노드 하나에 값 하나이므로 '기둥 VDS 합 ≠ 레일 전압차'는 표현할 수 없다(검사 대상이 아니다). 층 0의 기둥 KVL(DEC-71)은 같은 사실을 블록 국소 문제에서 등식으로 쓰는 것이라 새 검사 항목이 아니다" -- v0.6의 Σ tol_V 분모는 경계 근거와 서로 맞지 않는 새 분모였다(봉인 항목 8이라면 경계도 항목 8이어야 하고 그것은 6b 몫의 동작 변경). 클래스 `SealViolationError`의 근거는 '기둥 KVL'(739행 `local_infeasible` 정의가 기둥 KVL을 봉인 대상으로 든다)이고, **허용오차 기반 경계와 margin은 6b(봉인 항목 구현)가 함께 정한다**. 위반 크기는 레코드에 그대로 남겨 6b의 입력으로 쓴다. (v0.8, S2) margin은 #23이 앞당겨 만드는 `normalized_margin`을 `tol=None`으로 불러 `null`을 얻는다(margin을 쓰는 곳 하나 -- v0.7의 'CC-9는 Phase 5, 앞당기지 않음'은 §9-22 결정으로 바뀌었다. 경계 근거는 그대로: #43의 분모는 여전히 없다). §10.6-0·E2·#51의 margin 비교는 '둘 다 `null`이면 같음'. 모든 시작점이 실패하면 `SearchFailedError`(exit 6). 결과: 두 회로의 E1·E2 행이 '실행 끝 = 실패 클래스'로 판정 가능해진다. 메시지 문구('stage1_out', 'KVL')는 유지해 known_limitation test 3건이 계속 성립한다. θ 격자 다른 점에서 해가 나올 수 있는지는 [미확인]이다(#43 병합본에서 E2가 기록한다).

### 11.3 해소 선택지(UD-6)

| 안 | 내용 | 일반성(DEC-62) | 계획 영향 | 동작 영향 |
|---|---|---|---|---|
| (A) 계획 정정 | Phase 4는 11.2까지. 해소는 DEC-70(AC·대신호 → DC 되먹임: AC 결과는 θ의 제약으로만 되돌아간다)·DEC-71(기둥 조립)을 구현하는 Phase로 | 엔진 무변경 | U-09 재결정(N7), xfail 3건 만료 Phase 갱신, N6.1 Phase 4 범위 문구 'I-C11' → '실패 명시화' | 없음(11.2만) |
| (B) DEC-70 부분 선행 | 직렬 그룹의 KVL을 정본으로 두고, compensation이 정한 VDS는 고정값이 아니라 θ 제약(위반 = 후보 실패)으로 되돌린다. 이름 없는 규칙이라 두 회로 외에도 적용된다 | 규칙은 topology 무관 | DEC-70 상태 '미구현' → 부분 구현, Phase 배정 변경(계획 개정) | current_reuse·folded에도 적용된다 -- 무동작 증명 또는 DEC-40 |
| (C) topology 선언 정정 | 회로별 공동분석으로 선언을 바로잡는다: nmcnr `stage2_diode_ref` 멤버·직렬 경로(엔진 메시지가 가리키는 쪽), two_stage `vds_match_vgs_of`·compensation `stage_devices` | 데이터만 바뀐다(DEC-62 경로) | topology 수정은 사용자 확인 + 승인 기록(WP-07, U-16) | 그 회로만. S0 지문 변경 → `review_needed` |

* **권고**(§7.1 UD-6): nmcnr = (C)부터(원인이 선언이면 엔진을 바꿀 이유가 없다 -- 공동분석으로 확인), two_stage = (A)(DC/AC 조율은 DEC-70의 설계 몫이고, 세션41에 사용자가 별도 설계로 넘겼다). 이 권고는 회로 해석과 계획 범위 판단이라 결정은 사용자 몫이다.
* 어느 안이든 #44(또는 계획 정정)가 할 일: 해소된 회로의 xfail strict 해제(XPASS → 해제), known_limitation test 정리, V4 면제 2건 재검토(승인 기록의 '재검토' 절), 백로그 B12(xfail reason 만료 절) 처리.

---

## 부록 A. 재측정 명령과 결과

`R` = 저장소, `A` = `R/skills/analog-gmid-design/assets`, `$PY` = `C:/Python314/python.exe -B`. v0.2 표(A1~A11, `C:/g36`, cd64170)는 `draft_phase4_design.v02.md` 부록 A 그대로이고, 엔진·하네스가 HEAD까지 변경 0이라 값이 유지된다.

v0.3(스크래치 `C:/g48`, 끝나면 삭제):

| # | 명령 | 결과 |
|---|---|---|
| B1 | `git -C R rev-parse --short HEAD`, `git -C R diff --stat cd64170 HEAD -- skills workspaces tools`, `ls R/.ai/approvals \| wc -l` | `7535799`, skills·workspaces 0, tools 5파일(B28), 승인 42 |
| B2 | `git -C R archive HEAD skills/analog-gmid-design skills/analog-grammar workspaces/run_harness.py tools docs install.py \| tar -x -C C:/g48/repo` | 격리 사본 |
| B3 | `runall.sh`: 사본의 `workspaces/`에서 `$PY run_harness.py <key>` 4회로 병렬, 로그 `C:/g48/run_<key>.log`, 요약 `run_summary.txt`. folded는 보고 디렉터리를 만든 뒤 단독 재실행(`run_folded_cascode_2.log` -- 첫 실행은 사본에 보고 디렉터리가 없어 저장 단계에서만 `FileNotFoundError`, θ*까지는 같음) | F15 (rc 전부 0; two_stage 36 s, nmcnr 36 s, folded 43 s 단독, current_reuse 411 s 병렬) |
| B4 | `m.py`: AST로 (i) `raise` 없는 except 핸들러 (ii) `.get(<str>, <리터럴>)` (iii) `setdefault` (iv) `json.load(s)`·깊은 복사 관용구 (v) SD `_import_analog_grammar` 호출·`is None` 줄 (vi) library `ports` 모양 (vii) 레일 이름 문자열 상수 (viii) `_parse_output` 본문 (ix) `test_ic5` 표 대조 줄 (x) `test_ic11.py` (xi) `derived_spec` 사용처 (xii) `install.py` `SKILLS` → `m.json` | F17~F24, 부록 C |
| B5 | `reach.py`: `tools/gates/reachability.build_graph`로 사본 엔진+하네스 그래프, `gate_config.json` `reachability_roots.before_phase3`에서 도달(384 노드) → 지점별 운영 도달 → `reach.json` | 부록 C '운영 도달' 열. 중첩 함수는 이름 끝 부분으로만 맞춰 근사(`_known_vds` 등 '아니오(근사)') |
| B6 | `appc.py`·`appc2.py`: B4·B5 결과를 부록 C 표로 | 부록 C |
| B7 | folded·current_reuse topology에서 `kind == nmos`이고 source ∉ `supply_nets`인 소자 계수 | F16 |

v0.4(스크래치 `C:/g61`, 끝나면 삭제. 스크립트는 `_drafts/p4_scripts/`에 남김. 저장소 쓰기 0, 상태 변경 git 0):

| # | 명령 | 결과 |
|---|---|---|
| C1 | `git -C R rev-parse --short HEAD`, `git -C R archive HEAD skills/analog-gmid-design skills/analog-grammar workspaces/run_harness.py \| tar -x -C C:/g61/repo` | `7535799`, 격리 사본 `repo` |
| C2 | `$PY b2_patch.py` → `C:/g61/sim`(사본의 SR만: 노드전압 프레임 인자 5줄·절대 전위 읽기 5줄·레일 0 V 리터럴 3곳·rail_lo 고정 1곳을 환경변수 `P4_SIM`(S1/S2/S3)로 고르는 함수 호출로, 보간 2함수 입구에 VS 축 검사 `P4_AXIS`(count/raise)). `P4_SIM` 비움 = 원 코드와 같은 값(검증: 아래 C3의 `A_sim_full` = `A_head_full` 비트 동일) | 시뮬레이션 사본 |
| C3 | `b2_run_full.sh`: folded 하네스 전체 실행 5벌(repo S_A, sim S_A·S1·S2·S3+count) → `full.jsonl`, `b2_compare.py full.jsonl A_head_full` | F25 folded(전체 실행) |
| C4 | `b2_run_axis.sh`: sim S_A count·raise, S3 raise, S2 count → `axis.jsonl` | F26 folded 전체 실행 1,137 / 거부 시 400 격자점 infeasible |
| C5 | `b2_run_cr.sh`: folded θ* 한 점(`_build_theta_evaluator(...)["evaluate"]`) S_A·S1·S3·raise·count, current_reuse 전체 실행 S_A·S_A count·S1 → `cr.jsonl`, `b2_compare.py cr.jsonl F_theta_A`·`CR_A_full` | F25 θ* 한 점, current_reuse S1(전위형 metric 2개만 −0.9) |
| C6 | `b2_axes.py`(보간 2함수를 계수 래퍼로 바꿔 끼움, 축 4개) folded·current_reuse θ* | F26(축 밖은 VS만) |
| C7 | `b2_nodes.py`: θ* 평가 뒤 `propagate_node_voltages(by_name, sized, vdd)`의 conflicts·노드전압·소자 vsb | F27 |
| C8 | `b2_run_cr2.sh`: current_reuse θ* 거부 모드 평가 | `InfeasibleSizingError`(M9a) |

측정 한계: AST 규칙은 문자열 키의 `.get`·`setdefault`와 `raise` 없는 핸들러만 센다(변수 키, `or` 기본값(`x.get(k) or 0.0`), 조건식 대입은 세지 않는다 -- #13 작성 전 실측에서 같은 규칙에 `BoolOp(or)` 기본값을 더해 다시 센다). 운영 도달은 V7 그래프의 이름 과대 근사를 물려받는다(Phase 3 v3 §2.3).

v0.5(스크래치 `C:/g74`, 끝나면 삭제. 저장소 쓰기 0, 상태 변경 git 0 -- `rev-parse`·`log`·`diff --stat`·`show`·`ls`만. 엔진 실행은 하지 않았다 -- UD-17 수치는 [ud17] 인용):

| # | 명령 | 결과 |
|---|---|---|
| D1 | `git -C R rev-parse --short HEAD`, `git -C R log --oneline 7535799..HEAD`, `git -C R diff --stat 7535799 HEAD -- skills/analog-gmid-design/assets/*.py workspaces tools`, `git -C R diff -U0 7535799 HEAD -- …/stick_diagram.py \| grep '^@@'`, `git -C R diff --stat 7535799 HEAD -- docs/01-plan` | `2d58fd8`(작성 중 `fe638ab` → `2d58fd8`로 이동), 커밋 7개(P9 병합·판정, P10 문서·card, E4 정정, 승인 기록 2). 엔진 변경 = SD +3 −14(`kcl_series_union` 3023~3048 범위), 계획 변경 0 |
| D2 | `git -C R show <rev>:…/stick_diagram.py \| grep -n '^def (load_topology\|propose_device_roles_gap_fill\|_import_analog_grammar\|apply_device_roles_gap_fill)'` (rev = `7535799`, HEAD) | 1045 → 1045, 3845 → 3834, 4553 → 4542, 8550 → 8539 (SD 3041행 이후 −11) |
| D3 | `ls R/.ai/approvals \| wc -l`, `ls … \| grep` | 44(`_TEMPLATE.md` 포함), `20260930-b26-before-phase3.md`·`20260930-phase2-e4-phase.md` 있음. U-04·05·09·26·27·30·면제 묶기·범위 정책·B37a·UD-17 기록 0 |
| D4 | `$PY _drafts/p4_scripts/p4v05_dag.py`(이 문서 §3.3·§5 선행 열의 하드 간선 + 권고·조건부 간선 #54 → #23, #54 → #21, #53 → #23, #44 → #51을 노드 80개 그래프로 옮겨 위상 정렬) | 하드 간선만: 비순환(80/80 정렬). 하드 + 권고: 비순환(80/80). #53·#54 엔진 갈래(#23 → #53·#54, 그때 권고 간선 없음): 비순환(80/80) |
| D5 | `$PY -c "json.load(df23_inventory.json) → Counter(item['phase'])"`(`docs/03-analysis/gain-budget-gmid-sizing-20-dead-code-dup/`) | `measured_at` `766b5c2`, 항목 515: 해당 없음 317·4 = **63**·3 = 61·7b = 46·7a = 27·6b = 1(#39) |
| D6 | `ls R/tools/gates/redteam/attacks \| tail -3`, `sed -n 123p R/docs/01-plan/…plan.md` | 마지막 `31-v3-git-history`(32~35 없음), 계획 123행 = '기존 4개 회로 \| current_reuse(파일럿) / folded / two_stage / nmcnr' |
| D7 | `folded_cascode_nets.md`(json 파생 넷 표, 오케스트레이터 10-01 출력)와 [ud17] §2.1 연결 대조 | `tail` = M1.s·M2.s·M11.d, `X` = M1.d·M3.d·M6.s, `Y` = M2.d·M4.d·M5.s -- 일치. M1·M2 gate 넷만 추적 md와 다름(B47) |

v0.6(스크래치 `C:/g93`, 끝나면 삭제. 저장소 쓰기 0, 상태 변경 git 0 -- `rev-parse`·`show`만. 엔진 실행 없음 -- UD-17 수치는 [pack]·[ud17] 인용):

| # | 명령 | 결과 |
|---|---|---|
| E1 | `git -C R rev-parse --short HEAD` | `a796468` |
| E2 | `git -C R show HEAD:<A>/library/{folded_cascode,current_reuse_telescopic_ota}.topology.json`, `git -C R show HEAD:<A>/sizing_recipe.py` → `C:/g93`, `$PY C:/g93/chk.py`(netlist 소자의 `bulk` 키 계수, folded M1·M2 연결, 주석 키 존재, SR `bulk` 문자열 줄과 `propagate_node_voltages`·`derive_vsb_from_nodes`·`reconcile_vsb_from_nodes` 정의 줄) | folded 13소자·current_reuse 51소자 중 `bulk` 키 0. folded M1·M2 = pmos, source `tail`, drain X·Y. 주석 키 `symmetry._matching_pairs_comment`·`_netlist_correction_2026-08-05`·`device_roles._device_roles_comment_fold` 있음(내용은 [pack] §1.4와 같은 문장). SR `bulk` = 3795·3796(docstring)뿐, 정의 줄 3727·3789·3808(v0.2 표와 같음) → F34·F35 |
| E3 | `$PY _drafts/p4_scripts/p4v06_dag.py`(v0.5 스크립트에 #55, #53 = UD-17a·b·c, #54 = UD-17d, #55 ← UD-17e·UD-17d·사용자 connectivity·#22, E3 ← #21·#54, E8 ← #54·#55·#27, B26-1 ← U3·U4·U5, Phase 2 DoD ← P10b·#45·#1, T0·D0a·D0b ← Phase 2 DoD(D-23), D-19 → D0b·#47, 작업 순서 간선 #1 → B33을 더함. 결과는 `p4_scripts/out/p4v06_dag.out.txt`에 append) | **S0** 하드만: 비순환(91/91). **S1** 하드 + 권고(#54 → #23, #54 → #21, #53 → #23, #44 → #51, #1 → B33), UD-17c (i)/(iii)·UD-17e (ii): 비순환. **S2** UD-17c (ii)(#23 → #53, 권고 #53 → #23 없음): 비순환. **S3** UD-17e (i)(#55 없음): 비순환(90). **대조 S4**: v0.5처럼 bulk를 #54에 두고 #22 → #54 + 권고 #54 → #23: **순환**(#22·#23·#54 …) -- v0.5 그래프에는 #22 → #54 간선이 빠져 있었다, #55 분리의 근거. **대조 S5**: `b34_commit_plan.md` 순서(Phase 2 DoD → 34)를 Phase 3 v6 §9.1(Phase 2 DoD ← B34·B26-1)과 함께 넣으면 **순환** -- §9-19. **S6**(읽기 (나): Phase 2 DoD가 B34·B26-1을 뺌): 비순환 |

v0.7(저장소 재측정 없음 -- HEAD `a796468` 그대로, 3차 검토 §6이 사실 11개 재측정 일치. 스크래치 `C:/g98`, 끝나면 삭제):

| # | 명령 | 결과 |
|---|---|---|
| F1 | `$PY _drafts/p4_scripts/p4v07_dag.py`(v0.6 스크립트에서: Phase 2 DoD ← P10b만(읽기 (나)), 하드 사슬 Phase 2 DoD → 34 → 35 → #45 → B26pre → #1 → B33(33), B33 → T0, B26pre ← B26pre-U1, #1 ← B26pre-U2·U4·U5(U3 제거), 권고 간선에서 #1 → B33 제거(하드로), E3 ← #54는 OR 선행(#54 또는 #53)을 #54로 보수적으로 둠(주석). 결과 `p4_scripts/out/p4v07_dag.out.txt`에 append) | 노드 93. **S0** 하드만: 비순환. **S1** 하드 + 권고(#54 → #23, #54 → #21, #53 → #23, #44 → #51): 비순환. **S2** UD-17c (i)(#6 → #53, 권고 #53 → #23 유지): 비순환. **S3** UD-17c (ii)(#6 → #53, #23 → #53, 권고 없음): 비순환. **S4** UD-17e (i)(#55 없음): 비순환(92). **S5** UD-17d 엔진 갈래(#23 → #54, 권고 #54 → #23·#21 없음): 비순환. **S6** 권고 UD-17e → #22: 비순환. **S7** UD-17e (ii)가 #22 뒤(#55 엔진 몫, #6 → #55): 비순환. **S8** 엔진 갈래 전부 함께(S3 + S5 + S6): 비순환. 대조(순환이 맞음): **C1** 확정 순서 + v0.6 읽기 (가)(Phase 2 DoD ← #45·#1): 순환. **C2** 확정 순서 Phase 3 부분을 글자 그대로 'T0·D0a·D0b → G1'(v6 G1 → D0a와 함께): 순환. **C3** #54 엔진 갈래 + 권고 #54 → #23 유지: 순환. **C4** v0.5처럼 bulk를 #54에 두고 #22 → #54 + 권고 #54 → #23: 순환. 3차 검토 R1~R8과 결론이 같다 |
| F2 | `sed -n 749p R/docs/01-plan/features/gain-budget-gmid-sizing.plan.md`, `grep -n normalized_margin R/docs/02-design/features/gain-budget-gmid-sizing.00-common.design.md` | 749행 margin 정규화식('분모가 0이거나 정의되지 않으면 margin은 `null`'), `normalized_margin` 265행(MOD2, 'margin을 계산하는 곳은 이 함수 하나'), CC-9 행 559행(`50-failure-cache`) -- §11.2·§10.6-0 |
| F3 | `cmp _drafts/draft_phase3_design_v6.md _drafts/draft_phase3_design_v7.md` | 같음 -- **(v0.8) v0.7 작성 시점(16:32)의 사실이었고 지금은 다르다**(v7 16:45:58판 -- 아래 G4) |

v0.8(스크래치 `C:/g104` -- HEAD `git archive` 복제본 `iso`, `tools/gates` 사본 `cache`, 빈 `pyc`. 끝나면 삭제. 저장소 쓰기 0, 상태 변경 git 0 -- `rev-parse`·`archive`·`status`만. `PT4` = `PYTHONPATH=C:/g104/cache PYTHONPYCACHEPREFIX=C:/g104/pyc $PY -P -m pytest -c C:/g104/cache/pytest_gate.ini --rootdir=C:/g104/iso --confcutdir=C:/g104/iso <경로> --gmid-phase=4 -p no:cacheprovider`, `APPDATA` 지정. 명령 묶음 `_drafts/p4_scripts/p4v08_measure.sh`, 출력 사본 `_drafts/p4_scripts/out/p4v08_ic11.out.txt`·`p4v08_collect.out.txt`·`p4v08_dag.out.txt`):

| # | 명령 | 결과 |
|---|---|---|
| G1 | `$PY _drafts/p4_scripts/p4v08_dag.py`(v0.7 스크립트에서: P3DoD(= F2) → #2·#3·#4·#17 기본 간선(D-27), #23 → #25(`normalized_margin`), #53 (i) 형태별 시나리오와 D-27 앞당김 시나리오 추가. 결과 `p4_scripts/out/p4v08_dag.out.txt`) | 노드 93. 비순환: **S0** 하드만, **S1** 하드 + 권고, **S2a** (i-3) #6 → #53 + 권고 #53 → #23 + #53 → #22, **S2b** (i-1) #21 → #53, 권고 없음(4차 검토 R5), **S2c** (i-2) #22 → #53, 권고 없음, **S3** UD-17c (ii), **S4** UD-17e (i)(92), **S5** UD-17d 엔진 갈래, **S6** 권고 UD-17e → #22, **S7** #55 엔진 몫, **S8** S2c + S5 + S6, **R1** #2·#3·#4 → D0b(앞당김), **R8** #17·#18 → D0b, **R9** R1 + R8. 순환(대조, 맞음): **C1**~**C4**(v0.7과 같음), **C5** (i-1) + 권고 유지(= 4차 검토 R3), **C6** (i-2) + 권고 유지(= R4), **C7** S2a에 #22 → #53까지(경로 둘) |
| G2 | `PT4 <iso>/…/tests/contracts/test_ic11.py -rA -q`와 같은 명령 + `--gmid-dod`; `PT4 <iso>/…/tests/contracts -k legacy --collect-only -q`, `PT4 <iso>/…/tests -k lut_axis --collect-only -q`, `PT4 <iso>/…/tests --collect-only -q` | IC11: 옵션 없음 = `3 xfailed`(rail2 XFAIL reason 'IC11 -- 담당 Phase 4 -- 만료: 4 DoD'), `--gmid-dod` = `1 failed, 2 xfailed`(rail2 FAILED, `test_ic11.py:16` `Failed`). `-k legacy` = `1/606 tests collected (605 deselected)` -- `contracts/test_ts3_no_print_verdicts.py::test_target_set_includes_legacy_scripts`. `-k lut_axis` = `no tests collected (886 deselected)`. 전체 = `886 tests collected` |
| G3 | `sed -n 3727,3790p <iso>/…/sizing_recipe.py`, `grep -n 'propagate_node_voltages(' <iso>/…/*.py <iso>/workspaces/run_harness.py` | 시그니처 `(by_name, sized, vdd, rail_hi=_DEFAULT_RAIL_HI, rail_lo=_DEFAULT_RAIL_LO, tol: float = 1e-6, max_passes: int = 50)`(3727~3729). 루프 `for passes in range(1, max_passes + 1)` -- 진전 없으면 `break`, 진전 있는 pass는 `unresolved`에서 소자를 지운다. `diff > tol`이면 conflicts. 호출부 3831·3863·7294·7449 -- 어느 것도 `tol`·`max_passes`를 넘기지 않음(3863은 `**kw`) |
| G4 | `sed -n '396p;428p;439p;441p;739p;742p;749p;827p' <iso>/docs/01-plan/features/gain-budget-gmid-sizing.plan.md`, `grep -n 'normalized_margin\|CC-9' <iso>/docs/02-design/features/gain-budget-gmid-sizing.00-common.design.md`, `ls -la --time-style=full-iso`·`sha256sum _drafts/draft_phase3_design_v7.md`, `grep -n 'D-27' …v7.md` | 396 '검사 대상이 아니다', 428 봉인 항목 1 '노드 충돌 ≤ tol_V', 439 tol_V 정의, 441 `K_max`, 749 margin 정규화식, 827 IC9 '중복 복붙 -- 레지스트리 정본 하나 … 6b'. `00-common` 109·263·265·266·540·559·607·618행(§9-22). v7: 178,205 바이트, mtime 2026-10-01 16:45:58, sha256 `87c6351376911f3fc0af29b01c7d53a42052af71b6e8a15049bc3243a5dad85e`, D-27 = 649행(§8.1 544행, §9.1 570~573행) |

(v0.9 정정, 5차 검토 N-S4) G1의 `p4v08_dag.py`는 간선 3개(#6 → #10, #25 → #10, #17 → #18)를 줄 끝 주석 안에 삼켰다(`add(…)  # 설명; add("#10", …)` 형태). 그래서 G1 그래프의 #10은 선행 없는 뿌리, #18은 #17과 무관했다. 결론(시나리오별 비순환/대조 순환)은 복원해도 같다(5차 검토 재실행) -- 아래 H5가 복원본이다. G4의 `00-common` 8줄 중 265행은 **읽기만**(§9-22에서 고치지 않는다 -- 5차 검토 m-1).

v0.9(저장소 쓰기 0, 상태 변경 git 0 -- `rev-parse`·`diff --stat`·`status`·`show`·`grep`·작업 트리 `sed`만. 엔진·pytest 실행 없음. 스크래치 없음 -- 측정은 파이프로만. `R` = 저장소, SR = `R/skills/analog-gmid-design/assets/sizing_recipe.py`):

| # | 명령 | 결과 |
|---|---|---|
| H1 | `git -C R rev-parse --short HEAD`(시작·끝), `git -C R status --short \| md5sum`, `git -C R diff --stat a796468 0f23786` | `0f23786`(같음), md5 시작 `168fd530…`(5차 검토 값과 같음) → 끝 `07dad982…`(추적 밖 `cfg_*.json` 15개 -- 다른 프로세스가 만든 것, 이 작업 아님, 지우지 않음), 2파일(`.ai/approvals/20261001-p10b-v3-equiv.md`, `docs/02-design/specs/20260930-df23-registry-record.spec.md`) |
| H2 | `grep -n 'def propagate_node_voltages\|def reconcile_vsb_from_nodes\|def audit_vsb_consistency\|…(' SR`, `sed -n '3727,3735p;3808,3880p;7280,7300p;7445,7453p;8652,8662p;8886,8902p' SR`, `git -C R grep -n -w 'propagate_node_voltages\|reconcile_vsb_from_nodes\|audit_vsb_consistency' HEAD -- '*.py'` | F36: 시그니처 3727~3729·3808·3850~3851, `tol` 사용 3843·3875, 3831 tol 미전달, 3863 `**kw`만 전달. 운영 호출 7294(`except Exception` 7297)·7449(`except Exception` 7451)·8658·8892. 파일별 계수 SR 13·`test_ic5.py` 1(표 문자열)·`test_ts6_dead_probes.py` 16(합성 소스 문자열·상수 `_AUDIT_FUNC`)·`tests/probes/probe_full_research.py` 1(142 실호출) |
| H3 | `git -C R show HEAD:docs/01-plan/…plan.md \| sed -n '698p;1002p;1101p;1158p;1159p'`, `git -C R show HEAD:docs/02-design/…00-common.design.md \| sed -n '105,110p;263,266p'`, 같은 파일 `awk 'NR<=110 && /^#/'` | 698 EL3 `plan_tables_hash` 입력 = N4.1 `담당 Phase`·`강제 test`, N4.2 `도입`, N6.1 `Phase` 열, N3.12.2(§9-25·§9-22). 1002 N6.1 Phase 5 '… margin 반환'. 1101 U-26 (a) nmcnr **확정** `{vdd: 0.9, vss: −0.9}`. 1158 `40-defect-fixes` 행(CC-9 없음), 1159 `50-failure-cache` 행 '`00-common` CC-9(`normalized_margin`), …'. `00-common` 109행 = 94행 '### 3.3 이 문서 자신의 분류' 아래 표 |
| H4 | `git -C R show HEAD:<A>/sky130_lut_sweep.py \| grep -n 'VS{iVS}\|SID_1F\|xdut\|VS_GRID\|OUTPUT_DIR' \| wc -l` 대 `… \| grep -n -e 'VS.iVS.' -e SID_1F -e xdut -e VS_GRID -e OUTPUT_DIR \| wc -l` | v0.8 명령 0줄, 새 명령 33줄(267·275·276 `VS{iVS}`, 108 `VS_GRID`, 73·75 `OUTPUT_DIR`, 150 `xdut` 등). 이 환경에서는 패턴 안 중괄호가 셸 래퍼에서 바뀌는 것도 관찰했다(`-F '{iVS}'`가 중괄호 없이 매치) -- 그래서 중괄호 없는 `.`로 쓴다(#26) |
| H5 | `$PY _drafts/p4_scripts/p4v09_dag.py`(v0.8 스크립트에서: 삼킨 간선 3개 복원(별도 문장 + 스크립트 안 `assert`), 승인 시점 간선 `P3DoD → UD-0·UD-1·UD-6·UD-15`, `UD-0 → UD-4·UD-5·U26a`, `UD-0 → 이 문서가 계약을 정하는 card 전부`(#1·#45 제외), `U26a → #21`, B26pre-U1·U2 노드 제거(U1 원칙 기본안), S9(U-BF 결함 card BF: B26pre → BF → #1), N1(정보 -- (나) 별도 승인), R1·R8·R9를 대조 RC1·RC8·RC9로. 각 줄에 기대(비순환/순환) 대조 표시. 결과 `p4_scripts/out/p4v09_dag.out.txt`) | 노드 93(S4 92, S9 95). **비순환(기대대로)**: S0 하드만, S1 하드 + 권고, S2a·S2b·S2c·S3·S4·S5·S6·S7·S8(v0.8과 같은 갈래), **S9** U-BF 결함 card, **N1**(정보, 채택 안 함). **순환(대조, 기대대로)**: **RC1** #2·#3·#4 D0b 전 앞당김 + UD-0 Phase 4 착수 질문, **RC8** #17·#18 앞당김 + UD-1·UD-15 같은 질문, **RC9** 둘 다 -- 5차 검토 N-S1 재현, C1~C7(v0.8과 같음). `SUMMARY scenarios=23 unexpected=0` |
| H6 | `git -C R show HEAD:tools/gates/merge_gate.py \| grep -n 'def rule10_phase' -A 30` | 532~549: card `spec_phase`가 `phase_order`에 있어야 하고, V 검사 N/A는 card Phase가 그 V의 도입 Phase보다 앞일 때만 허용, V4 PASS basis 형식. 현재 Phase와의 대조는 없다(§9-19, Q-B34-PHASE). **(v0.9.1, 6차 검토 m-2 -- gate `master` `0f23786`에서 `git show … \| sed -n '1000,1015p;1030,1050p;1186,1216p'`로 재확인)** card phase의 다른 사용처 두 곳: (i) `v1_command_check` 1009~1010행 -- V1 명령의 `--gmid-phase=` 토큰이 card phase와 같아야 한다(1213행 `phase=card["phase"]`로 호출), (ii) `strict_set` 1042행 -- 같은 Phase의 기록된 spec card끼리 `activated_ic_case`를 합쳐 `--gmid-strict` 엄격 집합을 만든다(1210~1211행, old 트리 `skills/analog-gmid-design/assets/tests/conftest.py`에 `--gmid-phase` addoption이 있을 때 -- HEAD 52행에 있음). 그래서 Q-B34-PHASE 답은 B34·B26-1·b26pre·backfill card의 V1 실행 옵션과 엄격 집합을 바꾼다. 결론은 '이 문서 card의 판정은 같다'로 좁힌다(phase "4" card끼리만 합침) **(v0.9.2 정정, `review_b26_final.md` F2·`pending_questions.md` '[Q-B34-PHASE 정정]')** (ii)는 사용처로는 맞지만 결과가 같다 -- phase 2(판정 기록 15건 `activated_ic_case` 합집합)·phase 3(0건) 엄격 집합이 둘 다 빈 집합이고 phase 2·3 `gmid_ic` 표식이 0개다. 바뀌는 것은 V1 `--gmid-phase=` 토큰뿐(재측정 아님 -- 인용) |

v0.9.2(저장소 읽기·쓰기 0 -- `_drafts` 문서만 읽음, 스크래치 `C:/g147`(편집 스크립트만, 끝나면 삭제)):

| # | 명령 | 결과 |
|---|---|---|
| I1 | `C:/Python314/python.exe -B _drafts/p4_scripts/p4v091_dag.py`(`p4v09_dag.py`에서: U-BF 결함 card `BF`를 기본 노드로(B26pre → BF → #1, `U-BF` → BF), Q-B34-PHASE 기록 `PH3rec` → #45·B26pre·BF·#1, Q-P2DOD-E2 정정 기록 `E2rec` → Phase 2 DoD, U3 → #1(병합 전 조건), 스크립트 안 `assert` -- 네 card가 M1의 조상이고 Phase 2 DoD·`E2rec`이 네 card의 조상. S9는 'BF 없는 반사실(U-BF 2·3)'로, 대조 C8(Q-B34-PHASE 대안 '네 card를 Phase 2 DoD 앞으로' + 확정 순서 Phase 2 DoD → 34 → 35 → B34)을 더함. 결과 `p4_scripts/out/p4v091_dag.out.txt`) | 노드 98(S4·S9 97). **비순환(기대대로)**: S0·S1·S2a·S2b·S2c·S3·S4·S5·S6·S7·S8, **S9**(BF 없음), N1(정보). **순환(대조, 기대대로)**: RC1·RC8·RC9, C1~C7, **C8**(Q-B34-PHASE 대안은 확정 순서와 함께면 순환 -- 대안을 고르려면 34·35·B34 순서도 바꿔야 했다). `SUMMARY scenarios=24 unexpected=0` |
| I2 | `grep -n 'MASK_META\|v8.2\|EXCL_INST' _drafts/draft_phase3_design_v8.md`(머리 3행 '[초안 v8.2]', 21:19 판 -- 읽기만) | v8.2 머리 4행: UD-0 (c) E5 기본안 = 선례 모양(P2D 대 Phase 3 마지막 병합본, 의도된 필드만 card 계약값으로). 957~1018행 E5 블록: `MASK_META = ("rails",)`(994행), `e_lib_p3.py ... rails`(979행). 부록 J 1291행: E-INST 없음(backfill `interdig_ok`는 instance.json·report에 0), E-LIB `meta["rails"]` 하나(B26-1 계약값 `RailDeclaration(nets = supply_nets)`) → P-37·§5.4 #17 (c)·§6 E11 |

## 부록 B. N9.2 필수 절 대응

| N9.2 | 이 문서 |
|---|---|
| 1 범위 | §1 |
| 2 인터페이스 | §4.3 표(새 것·소비자), §3.1(목적 모듈), **§10(`fallback_events`·공정 기록·`supply_roles`·`rail_voltages`·E2 정규화·IC11 허용오차·(v0.7) MOD1 LUT 정의역 오류 §10.7)** |
| 3 판정식 | E-LIB·E-INST·NEW-TOPO는 `20-dead-code-dup` §3, 무동작은 `00-common` §11.4, **E2는 §10.5, IC11은 §10.6**, #19 lint 규칙은 §5.4 |
| 4 실패 경로 | N3.14 + `00-common` §7(#6), #43(I-C11 → `SealViolationError`/`SearchFailedError`), §10.1(`fallback_events`와 실패 레코드의 경계) |
| 5 역할별 산출물 | §5 |
| 6 DoD 측정 명령 | §6 |
| 7 착수 조건 | §7.3(U-04·05·09·26·27·30 승인 기록 0 -- F11, A2 기록(✓ `2d58fd8`), 면제 묶기·범위 정책(A1 결정됨, 기록 초안 있음)·#46 게이트 변경 승인, #21 V4 면제, B37a 승인 기록(UD-18), #53·#54·#55 topology 수정 승인, (v0.6) #53·#22 엔진 card 승인, B26-1 U4·U5, B33 결정됨), Phase 3 DoD PASS, 이 문서 승인 (v0.9.2) B26-1 U3·U4·U5·U-BF·Q-B34-PHASE 결정됨(기록 id §7.3), Q-P2DOD-E2 기록(Phase 2 DoD 몫) |
| 8 열린 질문 | §9 -- 없음(사용자 결정 UD-1·4~10·15·17a~e·18, (v0.7) B26pre U2·B26-1 U4·U5와 계획·순서 정정 요청만. (v0.9) B26pre U2는 U-BF(+ 조건부 U2-a)로 바뀌었고 Q-B34-PHASE가 더해졌다(둘 다 #1·#45·B26pre를 막음, 이 Phase card는 막지 않음). N-S1 = P-35, N-S2 = P-36·§9-26. (v0.8) §9-22 margin 결정됨(원칙 기본안), §9-23 닫음, §9-25 기본안 있음. UD-14 = A2, A1 = 선택지 2 + 넓힌 T6, B33 = 승인 + Q1 (a), card 순서(2026-10-01)로 결정됨) (v0.9.2) U-BF·Q-B34-PHASE·U3~U5·Q-P2DOD-E2 결정됨, U2-a 소멸 -- 이 문서 밖 대기도 #1·#45·B26pre·backfill 쪽은 0 |

## 부록 C. 조용한 폴백 후보 전수 (HEAD `7535799`, `A/*.py` + 하네스)

처리 코드는 §10.1-3. `#n` = 담당 card. 운영 도달 = 부록 A B5(근사). **(v0.4) 운영 도달 열은 HEAD V7 그래프(레지스트리 간선 없음·비운영 이름 폴백 누수 있음, B33) 기준이라 과소·과대 계수가 섞여 있다. 처리 열은 이 열에 기대지 않는다(§10.1-5). B33 병합 뒤 다시 잰다.**

### C.1 예외를 다시 던지지 않는 except 핸들러 (59)

| 파일 | 줄 | 함수 | except 타입 | 운영 도달 | 처리 |
|---|---|---|---|---|---|
| audit_current_forced.py | 164 | `<module>` | `Exception` | 아니오(근사) | N (도구·정리: 운영 판정 밖) |
| run_harness.py | 476 | `run` | `ValueError` | 예 | R #6 (CC-4a exit code) |
| run_harness.py | 512 | `run` | `Exception` | 예 | R #6 |
| run_harness.py | 528 | `run` | `Exception` | 예 | R #6 |
| sizing_recipe.py | 447 | `_idu_scan` | `ValueError` | 예 | X #10 |
| sizing_recipe.py | 893 | `find_optimal_sizing` | `ValueError,ZeroDivisionError` | 예 | X #10 |
| sizing_recipe.py | 1630 | `lut_vdsat_headroom` | `Exception` | 예 | R #13 (DF-14) |
| sizing_recipe.py | 1766 | `_known_vds` | `Exception` | 아니오(근사) | R #13 (DF-14) |
| sizing_recipe.py | 2081 | `search_gm_id_for_role` | `ValueError` | 예 | X #10 |
| sizing_recipe.py | 2172 | `measure_L_knee` | `ValueError,KeyError` | 예 | X #10 |
| sizing_recipe.py | 2586 | `feasible_L_window` | `ValueError` | 예 | X #10 |
| sizing_recipe.py | 2679 | `derive_role_L` | `KeyError,ValueError` | 예 | I #13 |
| sizing_recipe.py | 2737 | `derive_class_L` | `KeyError,ValueError` | 예 | I #13 |
| sizing_recipe.py | 3170 | `solve_diode_connected_vds` | `ValueError` | 예 | X #10 |
| sizing_recipe.py | 3219 | `diode_vds_cached` | `DiodeSelfConsistencyError` | 아니오(근사) | X #10 |
| sizing_recipe.py | 3462 | `diode_vds_window` | `ValueError,KeyError` | 예 | X #10 |
| sizing_recipe.py | 3474 | `diode_vds_window` | `ValueError,KeyError` | 예 | X #10 |
| sizing_recipe.py | 3538 | `solve_stacked_diode_pair` | `ValueError,KeyError` | 예 | R #15 (DF-11 `idu_up = 1.0`) |
| sizing_recipe.py | 3563 | `solve_stacked_diode_pair` | `ValueError,KeyError` | 예 | X #10 |
| sizing_recipe.py | 3975 | `node_pole_estimate` | `KeyError,ValueError` | 아니오(근사) | R #3 (D-6 `node_pole_estimate` test 이관) |
| sizing_recipe.py | 4054 | `_mna_stamp_capacitance` | `KeyError,ValueError` | 아니오(근사) | R #12 (DF-06 `_mna_stamp_capacitance`) |
| sizing_recipe.py | 5790 | `_score_and_apply` | `ValueError` | 예 | X #10 |
| sizing_recipe.py | 5809 | `_score_and_apply` | `KeyError` | 예 | R #13 (DEC-76: 코드 주석이 '이론상 도달하지 않음'이라 적은 방어 폴백 -- 발동 0 확인 뒤 거부) |
| sizing_recipe.py | 6739 | `check` | `InfeasibleSizingError` | 예 | F #10 |
| sizing_recipe.py | 6802 | `check` | `ValueError` | 예 | X #10 |
| sizing_recipe.py | 7297 | `_hr_resolve_vertical_group` | `Exception` | 예 | R #13 (DF-14) |
| sizing_recipe.py | 7376 | `_hr_resolve_vertical_group` | `ValueError,KeyError` | 예 | X #10 |
| sizing_recipe.py | 7451 | `_hr_resolve_vertical_group` | `Exception` | 예 | R #13 (DF-14) |
| sizing_recipe.py | 7801 | `achievable_metric_bound` | `Exception` | 아니오(근사) | N (seed 실패를 notes에 기록, DF-14 밖) |
| sizing_recipe.py | 7962 | `_build_theta_evaluator` | `KeyError,ValueError` | 예 | I #13 |
| sizing_recipe.py | 8457 | `_evaluate` | `KeyError,ValueError` | 예 | I #13 |
| sizing_recipe.py | 8639 | `_evaluate` | `_HeadroomDependencyNotReady` | 예 | N (내부 제어 신호 `_HeadroomDependencyNotReady` -- 다음 패스에서 재시도, 값 대입 없음) |
| sizing_recipe.py | 9034 | `diagnose_sizing_roles_gap` | `ValueError` | 예 | N (하네스 진단 경로 `diagnose_sizing_roles_gap`) |
| sizing_recipe.py | 9219 | `optimize_full_circuit_budget` | `InfeasibleSizingError` | 예 | F #10 |
| sizing_recipe.py | 9807 | `derive_theta_dependency_graph` | `InfeasibleSizingError` | 예 | F #10 |
| sizing_recipe.py | 9819 | `derive_theta_dependency_graph` | `InfeasibleSizingError` | 예 | F #10 |
| sizing_recipe.py | 9824 | `derive_theta_dependency_graph` | `InfeasibleSizingError` | 예 | F #10 |
| sizing_recipe.py | 9997 | `extract_linear_feasibility_constraints` | `ValueError` | 예 | N (거부를 구조화 레코드로 반환 -- 조용하지 않음) |
| sizing_recipe.py | 10355 | `search_stage_budget_L_warm_start` | `InfeasibleSizingError` | 예 | F #10 |
| sizing_recipe.py | 10476 | `_probe` | `InfeasibleSizingError` | 예 | F #10 |
| sizing_recipe.py | 10479 | `_probe` | `Exception` | 예 | R #13 (DF-14) |
| sizing_recipe.py | 10756 | `presolve_warm_start` | `InfeasibleSizingError` | 예 | F #10 |
| sizing_recipe.py | 10770 | `presolve_warm_start` | `InfeasibleSizingError` | 예 | F #10 |
| sizing_recipe.py | 10959 | `_objective_fn` | `InfeasibleSizingError` | 예 | F #10 |
| sizing_recipe.py | 10969 | `_fn` | `InfeasibleSizingError` | 예 | F #10 |
| sizing_recipe.py | 11025 | `_optimize_theta_slsqp` | `InfeasibleSizingError` | 예 | F #10 |
| sizing_recipe.py | 11047 | `_callback` | `InfeasibleSizingError` | 예 | F #10 |
| sizing_recipe.py | 11061 | `_optimize_theta_slsqp` | `InfeasibleSizingError` | 예 | F #10 |
| sizing_recipe.py | 11197 | `_optimize_theta_slsqp_block_coordinate` | `ValueError` | 예 | I #13 |
| sizing_recipe.py | 11452 | `apply_and_revalidate_pair_adjustment` | `ValueError` | 예 | N (거부를 구조화 레코드로 반환 -- 조용하지 않음) |
| sizing_recipe.py | 11565 | `apply_and_revalidate_matching_finger_growth` | `ValueError` | 예 | N (거부를 구조화 레코드로 반환 -- 조용하지 않음) |
| sky130_lut_sweep.py | 253 | `_cleanup_temp` | `FileNotFoundError` | 예 | N (도구·정리: 운영 판정 밖) |
| sky130_lut_sweep.py | 255 | `_cleanup_temp` | `OSError` | 예 | N (도구·정리: 운영 판정 밖) |
| stick_diagram.py | 374 | `_try_pattern_table_match` | `ValueError` | 예 | X (패턴표 후보 배제 → 다음 후보) |
| stick_diagram.py | 1057 | `_import_analog_grammar` | `ImportError` | 예 | R #45 (B34) |
| stick_diagram.py | 4818 | `_verified_euler_fix` | `ValueError` | 예 | X (Euler 검사 불가 → '검증 안 됨' 반환, 수리 후보 배제) |
| stick_diagram.py | 4911 | `audit_vertical_stack_id_euler_feasibility` | `ValueError` | 아니오(근사) | R #2 표 행 / #41 함수 (D-5) |
| stick_diagram.py | 8977 | `_topology_ref_relpath` | `ValueError` | 예 | N (다른 드라이브 → 바로 아래에서 거부) |
| topology_to_markdown.py | 191 | `<module>` | `Exception` | 예 | N (도구·정리: 운영 판정 밖) |

계수: F 14, I 5, N 11, R 14, X 15 (합 59)

`X #10` = 격자·후보점 배제(값을 지어내지 않음), CC-4b가 잡는 타입을 LUT 정의역 오류로 좁힌다(DF-27 뒤 `lut_axis_out_of_range`). `F #10` = 탐색 후보 실패 기록(`CANDIDATE_FAILURE_CLASSES` 이름으로), V8 밖. `I #13` = 선언·유도 실패를 '없음'·다른 경로로 바꿈 → `fallback_events` 계측 + §10.1-4 발동 규칙.

### C.2 선언값 리터럴 기본값 `.get(<문자열 키>, <스칼라·튜플>)` (77) + `setdefault` 선언 기본값 (2)

| 파일 | 키 | 기본값 | 줄(곳 수; 함수) | 운영 도달 | 처리 |
|---|---|---|---|---|---|
| run_harness.py | `search_method` | `'grid'` | 447 (1; `run`) | 예 | #13 발동 규칙 §10.1-4 |
| sizing_recipe.py | `ID` | `0` | 7261, 7274, 7404 (3; `_hr_resolve_vertical_group`) | 예 | #13 발동 규칙 §10.1-4 |
| sizing_recipe.py | `W_bounds` | `(1e-06, 0.0002)` | 1626, 2697, 2748, 3623, 5763, 6055, 6731, 7266, 7462, 8716 (10; `_evaluate`, `_feed_metric_stage_budget`, `_hr_resolve_vertical_group`, `_make_shared_current_scorer`, `apply_diode_self_consistent_gm_id`, `derive_class_L` 외) | 예 | R #28 (U-30 엔진 폴백) |
| sizing_recipe.py | `aggregate` | `'max'` | 4379 (1; `_mirror_ratio_aggregate`) | 아니오(근사) | #13 발동 규칙 §10.1-4 |
| sizing_recipe.py | `complement_key` | `'t_lln'` | 5558, 9635 (2; `_feed_settling_split`, `_theta_feed_footprint`) | 예 | #13 발동 규칙 §10.1-4 |
| sizing_recipe.py | `freq` | `1.0` | 3054 (1; `_metric_flicker_plus_thermal_sum`) | 아니오(근사) | #13 발동 규칙 §10.1-4 |
| sizing_recipe.py | `gds` | `0.0` | 3960 (1; `node_pole_estimate`) | 아니오(근사) | #13 발동 규칙 §10.1-4 |
| sizing_recipe.py | `gm` | `0.0` | 3960 (1; `node_pole_estimate`) | 아니오(근사) | #13 발동 규칙 §10.1-4 |
| sizing_recipe.py | `gm_id_bounds` | `(2.0, 30.0)` | 5521, 9298, 9372 (3; `_evaluate_row_split`, `_feed_gm_target_convention`, `optimize_full_circuit_budget`) | 예 | R #38 (DF-20 격자 리터럴) |
| sizing_recipe.py | `margin` | `0.05` | 1564 (1; `_default_cascode_headroom`) | 예 | R #38 (DF-20 margin 0.05) |
| sizing_recipe.py | `max_finger_w` | `4e-05` | 9273 (1; `optimize_full_circuit_budget`) | 예 | #28 (탐색 설정 공통 한 곳으로, P-4) |
| sizing_recipe.py | `max_layout_retry_rounds` | `6` | 9485 (1; `optimize_full_circuit_budget`) | 예 | #13 발동 규칙 §10.1-4 |
| sizing_recipe.py | `max_split_per_stack` | `6` | 9484 (1; `optimize_full_circuit_budget`) | 예 | #13 발동 규칙 §10.1-4 |
| sizing_recipe.py | `maxiter` | `80` | 11172 (1; `_optimize_theta_slsqp_block_coordinate`) | 예 | #13 발동 규칙 §10.1-4 |
| sizing_recipe.py | `metric` | `'gain_db'` | 5691, 6012 (2; `_build_shared_current_joint_plan`, `_feed_metric_stage_budget`) | 예 | #13 발동 규칙 §10.1-4 |
| sizing_recipe.py | `min_finger_w` | `1e-06` | 9273 (1; `optimize_full_circuit_budget`) | 예 | R #28 |
| sizing_recipe.py | `min_vds` | `0.0` | 7308, 7321 (2; `_hr_resolve_vertical_group`) | 예 | #13 발동 규칙 §10.1-4 |
| sizing_recipe.py | `n_samples` | `0` | 2789 (1; `estimate_area_budget`) | 아니오(근사) | #13 발동 규칙 §10.1-4 |
| sizing_recipe.py | `output_key` | `'t_slew'` | 5556, 9634 (2; `_feed_settling_split`, `_theta_feed_footprint`) | 예 | #13 발동 규칙 §10.1-4 |
| sizing_recipe.py | `sense_den` | `'common'` | 5038 (1; `_metric_smallsignal_ratio_db`) | 아니오(근사) | #13 발동 규칙 §10.1-4 |
| sizing_recipe.py | `sense_mode` | `'diff'` | 5054 (1; `_metric_smallsignal_gain_db`) | 아니오(근사) | #13 발동 규칙 §10.1-4 |
| sizing_recipe.py | `sense_num` | `'diff'` | 5036 (1; `_metric_smallsignal_ratio_db`) | 아니오(근사) | #13 발동 규칙 §10.1-4 |
| sizing_recipe.py | `sign` | `1` | 5411, 9994 (2; `_feed_root_signed_sum`, `extract_linear_feasibility_constraints`) | 예 | #13 발동 규칙 §10.1-4 |
| sizing_recipe.py | `stage_objective` | `'power'` | 8164 (1; `_evaluate`) | 예 | #13 발동 규칙 §10.1-4 |
| sizing_recipe.py | `temperature_K` | `300.0` | 3055 (1; `_metric_flicker_plus_thermal_sum`) | 아니오(근사) | #13 발동 규칙 §10.1-4 |
| sizing_recipe.py | `total_key` | `'t_settle_total'` | 5557 (1; `_feed_settling_split`) | 아니오(근사) | #13 발동 규칙 §10.1-4 |
| sizing_recipe.py | `type` | `''` | 2300 (1; `gain_stage_tails`) | 예 | #13 발동 규칙 §10.1-4 |
| sizing_recipe.py | `vsb` | `0.0` | 1527, 1629, 1765, 2695, 2746, 2935, 3067, 3314, 3389, 3665, 3974, 4053, 4625, 5504, 5789, 5802, 6026, 6053, 6116, 7138, 7175, 7302, 7454, 8714, 8776, 8788, 8838, 8838, 8864, 10223, 11332 (31; `_evaluate`, `_feed_gm_target_convention`, `_feed_metric_stage_budget`, `_hr_resolve_vertical_group`, `_known_vds`, `_metric_flicker_plus_thermal_sum` 외) | 예 | #13 발동 규칙 + #24(DF-01) -- §10.1-4 |
| sizing_recipe.py | `vsb`(조건식 기본값, v0.4 추가) | `ref_vds if ref_dev is not None else 0.0` | 7411 (1; `_hr_resolve_vertical_group`) | 예 | #13 발동 규칙 + #24(DF-01) -- 7579 `setdefault("vsb", ref_vds)`와 같은 묶음(주석 7406~7410), `0.0` 갈래가 조용한 기본값(검토2 M1) |
| stick_diagram.py | `sign` | `1` | 3772 (1; `propose_theta_kcl_gap_fill`) | 아니오(근사) | #13 발동 규칙 §10.1-4 |

표 = 스칼라·튜플 기본값 77곳. 빈 컨테이너 기본값(`{}`·`[]`·`()`·`set()`) 35곳(25종)은 표에서 뺐다(§10.1-3 분류 C0).

`setdefault`의 선언 값 기본값: SR 7579 `_hr_resolve_vertical_group` `other_entry.setdefault("vsb", ref_vds)`(DF-01 원인 코드, #24), SD 4605 `apply_device_roles_gap_fill` `entry.setdefault("vsb", 0.0)`(topology `device_roles`에 vsb 0 V 가정을 **기록**하는 W-3 도구 경로 -- #42와 §10.1-4). 나머지 `setdefault` 47곳은 캐시·집계용 내부 dict(`'_cache'`, union-find `find`, 목록 누적)라 선언 기본값이 아니다(C0).

### C.3 analog-grammar 부재 폴백 (B34 -- v0.4: 사이트별 담당으로 나눔)

v0.3의 "21곳 전부 #45에서 R"은 B34 v1 범위였다. 최신 B34 card(phase 3 -- (v0.9.2), 4 def)는 아래처럼 나눈다(검토2 S1, 사이트 번호 = B34 card 표, 줄 번호 HEAD `7535799`, `_import_analog_grammar` 호출 줄 1045·1072·1088·1312·1444·1713·1893·2258·2399·2494·3380·3528·4070 [재측정 v0.3]).

| 담당 | 사이트(함수, 줄) | 처리 |
|---|---|---|
| **#45**(B34, phase 3) | 1 `_import_analog_grammar` 1057~1058(재raise), 2 `find_idiom_matches` 1073~1074, 3 `find_stack_edges` 1089~1090, 11 `audit_theta_root_direction` 3381~3382, 11b 같은 함수 3387~3388 | R(삭제·재raise) |
| **#1**(B26-1, phase 3) | 9 `refine_differential_and_mirror_relations` 2400~2401·2410~2411, 10b 같은 함수 2440~2441, 13 `propose_device_roles_gap_fill` 4071~4073, 같은 함수 3966~3970 `unavailable_reason` 키(틀린 사유, 소비처 0 -- B40, U4 추가 승인 ✓ `20260930-b26-b40-reason-key`) | R(#45 뒤 도달 불가 분기 삭제 -- 문장 하나짜리만) |
| **B35** = UD-15 (2)=X → **#49**, (2)=Y → **#17** | 5 `suggest_vertical_stack_composites` 1445~1446, 6 `find_verified_differential_and_mirror_relations` 1714~1715, 7 `_propose_vertical_stack_ids` 1894~1895, 8 `_propose_headroom_roles` 2259~2260, **(v0.6) 10** `refine_differential_and_mirror_relations` 2494~2495(블록 2496~2523), **14** `propose_device_roles_gap_fill` 4087~4111(B34 최종판·B26-1 v4가 #1에서 옮김) | R(같은 card가 그 함수의 AG 호출부를 바꾼다. 10·14는 블록 내어쓰기라 블록 값 판정 계약 동반) |
| **백로그 B39**(이 Phase 밖) | 4 `find_differential_and_mirror_forks` 1313~1314(등가 변이 면제 필요), 12 `propose_theta_kcl_gap_fill` 3529~3531·3538~3540, 3533~3535 `unavailable_reason` | 도달 불가 분기로 남음(#45 뒤 동작 영향 없음) |
| 남김(gate 소자 없음 경로 -- 부재와 다른 뜻) | `find_idiom_matches` 1076~1077, `find_stack_edges` 1092~1093, `find_differential_and_mirror_forks` 1316~1317, `suggest_vertical_stack_composites` 1448~1449, `find_verified_…` 1717~1718, `_propose_headroom_roles` 2262~2263, `audit_theta_root_direction` 3384~3385, 전파 사이트 `find_differential_pair_candidates` 1543, `_propose_gm_id_roles` 2092, `_propose_L_roles` 2165·2169, `refine_…` 2420, `propose_vertical_stack_id_gap_fill` 3296, `geometry_colocation_union` 3115 | 코드 그대로, docstring만 #45가 고침 |

SR `_build_theta_evaluator` 7952(게이트가 막을 재료를 잃음)·`load_topology` 8668~8737 전파는 #45의 재raise로 부재가 먼저 `ImportError`가 되어 해소된다(B34 card 계약 1~3).

### C.4 계수 요약

| 분류 | 수 | 처리 |
|---|---|---|
| R(제거) | 핸들러 14 + 기본값(`W_bounds` 10·`min_finger_w` 1·`gm_id_bounds` 3·margin 1) + B34 사이트(#45 5·**#1 4·B35 6** -- C.3, (v0.6) 10·14가 #1 → B35. v0.5는 #1 6·B35 4) | 담당 card |
| (이 Phase 밖) | B34 사이트 3(4·12·3533~3535) | 백로그 B39 |
| F(실패 기록) | 핸들러 14 | #10 |
| X(후보 배제) | 핸들러 15 | #10 |
| I(계측) | 핸들러 5 | #13 |
| D(발동 규칙) | 기본값 약 62(vsb 31 포함) + 조건식 1(SR 7411) + `setdefault` 2 | #13 §10.1-4 → R 또는 I |
| N(비운영·구조화) | 핸들러 11 | 없음 |
| C0(빈 컨테이너) | 35 | 없음(필수 선언 키면 해당 card에서 R) |
