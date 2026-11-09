# 백로그 추가 초안 (다음 문서 커밋 때 .ai/context.md에 Python 바이너리 append)

- B29 library topology.json 주석 필드의 삭제된 이름 안내 정리 -- current_reuse_telescopic_ota.topology.json 1250·1281(`suggest_headroom_stack_groups`)·1872(`_metrics_comment`), nmcnr_amplifier.topology.json 74(`slew_rate()`). 사용자 결정 2026-09-30 보류("topology.json주석은 보류해"). 고칠 때: 승인 기록(쓰기 경로표 634행·U-16), 주석 필드만·connectivity 불변, auditor가 주석 외 필드 동일·E-LIB 동일 확인. S0 지문 영향 여부 실측 먼저.
- B30 Phase 2 이전부터 낡은 이름 안내(references·SKILL.md) -- 예: SKILL.md:52 `run_sizing_pipeline`, consistency-map.md 약 20개. P10 사전 실측(_drafts/prep_p9_p10.md §9, b22_scan.out.txt)에 목록. 문서 card로 묶어 처리.
- B31 백로그 번호 겹침 -- 문서 백로그 B22(.ai/context.md 14943행)와 history 4002행 §10.3 B22(`diode_vds_window`, 2026-09-09 해소)가 같은 번호. 엔진 주석 SR 567·3425·7412·레지스트리 77행은 history 쪽 뜻. 제안: context 백로그를 이후 `BL-` 접두사로.
- B33 V7 호출 그래프 간선 누락 -- 클래스 → `__init__`, 레지스트리 dict → 값 함수 간선이 없어 HEAD 엔진 def 109개가 미도달로 셈(예: `SemiEmpiricalGmIdLUT.__init__`, `_feed_*`). Phase 3 이동 card의 V7 판정에 잡음이 되므로 G1 전후 검토(Phase 3 design v2 준비 agent 관찰, 2026-09-30).
- B34 `skills/analog-grammar` 부재 시 stick_diagram 조용한 폴백이 결과를 바꿈 -- current_reuse θ* 평가가 성공 → ValueError(vertical_stack_id 순환). 조용한 기본값/폴백 금지 원칙 위반 후보(B26 결정 자료 agent 관찰, 2026-09-30).
- B35 `skills/analog-grammar/assets/netclass.py` `RAILS`·`RAILS_POS`·`RAILS_NEG` 이름 집합 레일 판정 -- stick_diagram 11함수(운영 7)가 사용, code-author 쓰기 경로 밖(B26-1 초안 agent 관찰).
  (2026-10-01 추가) B34 인계 사이트 5~8에 더해 **사이트 10·14**(`refine_differential_and_mirror_relations`의 `if _netclass_al is not None:`, `propose_device_roles_gap_fill`의 `if _idioms_lcmf is not None:`·`else`·`cascoded_active_load_legs = set()` -- 도달 불가 분기 삭제 + 블록 내어쓰기)도 B35 몫. 내어쓴 블록은 V3 새 문장이라 그 출력(`active_load_leg_candidates`·`signal_referenced_mirror_legs`·`branch_load_partner_candidates`, 뒤 `gain_role_candidates |= cascoded_active_load_legs`)의 판정 계약이 필요하다(B26-1 v4로 이동 근거: `_drafts/review2_b26_1.md` E2·E2b, 모의 실측 생존 13+1).
- B36 게이트 공백 -- `skills/analog-grammar`가 추적 파일인데 N3.12.2 쓰기 경로표 어느 행에도 없음: code-author는 못 쓰고 오케스트레이터·비 gmid agent 쓰기는 hook 통과, 게이트 도구(role_paths·V3·V7·source_lint·interface_card·weakening_diff) 범위 밖 -- 엔진 판정을 바꾸는 코드가 trailer·test·audit 없이 바뀔 수 있음. 결정 필요: 별도 skill로 게이트 범위 편입(기본안) 대 analog-gmid-design 흡수, 승인 2건. `install.py` SKILLS에 analog-grammar 추가는 사용자 작업(현재 설치본은 항상 B34 폴백으로 돔).
- B37 `load_topology`가 topology `ports` 선언을 analog-grammar에 넘기지 않아 운영 경로가 이름 정규식(`HINT_*`)으로 입력·바이어스 넷을 추정 -- topology 의존(B26과 같은 종류).
- B39 B34 범위 밖으로 넘긴 analog-grammar 부재 폴백 사이트 -- 사이트 4 `find_differential_and_mirror_forks`(기존 생존 변이 1개가 등가 `len(members) >= 2`→`>= 1`, 면제 승인 필요), 사이트 12 `propose_theta_kcl_gap_fill`(변이 242·인벤토리 5, 기존 생존 추정 ~48). B34(좁힌 범위) 뒤 처리.
- B40 `propose_device_roles_gap_fill`이 analog-grammar가 있어도 gate 없는 입력에 "analog-grammar를 import할 수 없어" 틀린 사유를 실음 -- B26-1에서 해당 분기 정리 때 함께(B34 초안 관찰).
- B41 DF-36 V3 판정(148bd6d, killed 22·exempt 4)의 exempt 4개는 `save_instance_json`이 바뀐 뒤 적용된 C8 승인(20260922-ic3-v3-exempt) id -- 승인 범위 밖 누수 실례. 판정 자동 번복 없음(3b 재판정은 V3 재실행 안 함). history 기록 + 면제 묶기 card(20260930-v3-exempt-binding) 근거로 인용. 필요하면 DF-36 V3 재측정.
- B42 V3 데코레이터 변이 NOOP -- `_replace_def`가 데코레이터 변이를 버림(실측, 예 topology_library.py:248 `lru_cache(maxsize=256)` 상수 변이가 적용 안 됨). 현행 규칙에도 있는 도구 결함.
- B43 V3 상수 변이에서 bool 제외 -- def 머리 기본값 bool 변경 등 동작 변경이 변이 0개가 될 수 있음(범위 정책 검토 B2).
- B32 레지스트리 누락 -- 픽스처 함수 `folded_cascode_example`·`two_stage_ota_example` 행 없음(P10 재측정에서 발견).
- B44 `test_s120_section`(tests/unit/test_selftest_stick_diagram.py 2712~2718) docstring의 "analog-grammar 미설치 상황(ImportError 경로)은 … self-test로 하기엔 위험 … 하지 않는다"는 B34 병합 뒤 낡은 서술 -- B34 계약 test(`tests/contracts/test_b34_grammar_explicit.py`)가 `sys.modules`로 재현한다. 판정 불변, test-author 경로, 다음에 그 파일을 고치는 card에서 참조로 고친다(review2_b34 §6).
- B45 Phase 3 G1 초안(`_drafts/draft_p3_g1.spec.md`) 계약 4 문장 추가 -- V3 범위 정책 card `20260930-v3-changed-stmt-scope`가 G1보다 먼저 병합되므로(A1·A2 순서), G1 계약 4의 "나머지 대상 선택은 지금과 같다(같은 입력에서 `changed_defs`와 같은 결과)"에 "def 안의 변이 선택은 `20260930-v3-changed-stmt-scope` 계약 1 그대로"를 더한다. 옮긴 def(해시 동일)는 두 card 모두에서 대상 아님. redteam 번호는 D-18 그대로(G1 32). G1 card 개정 때 처리(review2_v3_cards S7).
- B46 V3 두 규칙 공통의 기존 한계(범위 정책 card의 약화 아님) -- 연산자 집합에 bool·문자열·이름 교체·예외 종류 변이가 없고(적대 사례 1a·3a·7·8·9·10b: 변경을 관찰하지 않는 test로 PASS), V3는 def만 보아 모듈·클래스 수준 상수·별칭 변경(사례 2·3b)은 변이 0개 -- test가 없어도 PASS. 검토: 연산자 확장, 모듈 수준 이름을 읽는 def를 대상으로 삼기(review2_v3_cards M3, `v3_scripts/out/v3_adv21.txt`).
- B47 추적 파일 library/folded_cascode.topology.md가 topology.json과 어긋남(낡음) -- md는 M1.gate=vin_p·M2.gate=vin_n, json은 M1.gate=vin_n·M2.gate=vin_p. topology_to_markdown.py는 실행하면 이 추적 파일을 덮어씀(2026-10-01 오케스트레이터가 표 출력 중 덮어써 즉시 복원). 재생성 커밋은 사용자 확인 뒤(다른 library md 일치 여부도 확인).
- B48 test_lint (2) '확실한 복사' 오탐 -- 피검 함수의 누적 리스트 초기값 `[]`이 반환 변형으로 잡히고 빈 컨테이너가 잎으로 취급되지 않아 `assert findings == []`(계약상 '발견 0')가 FAIL(P10b 1차 V4, 2026-10-01). 이번 card는 test 모양(`len(...) == 0`)으로 우회, 게이트 수정은 별도 card + 사용자 승인.
- B49 design 20 §8 증거 형식 표기가 판정 기록과 다름 -- §8 표는 P6(`20260930-d-move-tests`)·P8(`20260930-dup-w-calc`)을 equivalence로 적지만(190·192행) 두 판정 기록의 `evidence_type`은 red-green이다. §8 아래 197행 문단이 P7·P8을 red-green으로 정정했으나 표 P8 칸은 그대로이고, P6은 표와 197행 문단 모두 equivalence로 남아 있다. Phase 2 DoD 판정 범위 밖(브리핑 v3는 기록의 evidence_type을 그대로 적게 함, 판정 영향 없음). 문서 정합 card에서 표·문단 정정(Phase 2 DoD 드라이런 2026-10-01 범위 밖 메모).
- B50 stick_diagram 층위1 폴백(1584~1596행 주석 "못 찾던 것만 보충")이 n=2에서 trace가 이미 찾은 쌍을 `layer1_fallback` 원소로 한 번 더 낸다 -- 주석 의도와 어긋나는 중복 의심. b26pre 계약 11은 이 원소를 판정에서 빼 거짓 기준값을 피함(2026-10-01). 결함 여부 확인·수정은 별도 card.
- B54 md 일치 test(20261001-topology-md-sync)가 표 머리 행을 strip한 뒤 비교 -- card 문장 "문자열로 같아야"보다 느슨(줄 끝 공백만 다른 머리 행 통과). 현재 library 영향 0(auditor 관찰, 판정 5f643a9 V4 basis). 고칠지는 다음 test card에서.
- B55 연결 topology 파일 병합 충돌: 진입·연결 두 파일이 같은 소자를 device_roles에 선언하면 연결 파일 항목이 통째로 덮어써 진입 파일 L_role이 사라지고, 같은 블록 키 _netlist_sections_structured도 덮어쓴다; 같은 쌍·disposition·이상원은 중복으로 남는다(b37a_survivor_options.md 실측). IC3 원칙대로 충돌 거부하는 별도 card. library 9회로는 연결 파일이 없어 현재 영향 0. B37a는 키가 겹치지 않는 합만 계약 10으로 고정.
- B41 분석 완료(2026-10-02, _drafts/b41_options.md): save_instance_json C8 면제 4개 중 scope_note 2개는 비등가(test 공백, b41_kit/test_instance_scope_note.py 18 test가 죽임), indent ±1 2개는 등가(파싱 결과 동일, E-INST 판정은 파싱 해시). 확정 순서 안에 이 변이를 V3 대상으로 삼는 card 없음 -- 오케스트레이터 기본안: 지금 질문하지 않고, (1) scope_note test는 test-only card로 Phase 4 #2 앞 아무 때나(강화, 승인 불필요), (2) indent 면제는 save_instance_json 본문을 고치는 첫 card가 자기 head 해시로 묶어 승인받는다(지금 묶어도 그 card에선 해시가 바뀌어 무효).
- B41 처리 방침(2026-10-02, card 초안 `_drafts/draft_b41_scope_note.spec.md` + 독립 검토 `_drafts/review_b41.md`, design 40 초안 v0.9.10 §1.4·§3.3·§5.1): (1) `scope_note` 몫(C8 해시 없는 비등가 원소 `stmt_delete:body[2]`·`body[2].body[0]`) = test-only card `20261002-b41-scope-note-test`(phase 4, **Phase 4 첫 card -- #2 `20261002-d4-delete-unwired` 앞**, 승인 줄 = Phase 4 design 승인, 게이트 변경 없음, 강화라 DEC-40 대상 아님). 새 test 1 + 4 x library(9회로 37개)가 M-a·M-b·H1~H6을 죽이고 P1~P5(indent ±1·ensure_ascii·빈 문자열 쓰기·sort_keys)는 통과(검토 재측정 `4a286f0` 일치). (2) `indent` ±1 등가 원소 2개 = `save_instance_json`의 `with`/`json.dump` 블록을 바꾸는 첫 card가 자기 head 묶기 해시로 decision 승인(등가 근거 `_drafts/b41_options.md` §1.2, 지금 묶으면 그 card에서 해시가 달라 무효). (3) C8 승인 기록·p10 기록은 고치지 않는다(해시 없는 원소는 면제 묶기 병합 뒤 이미 `exempt_ignored`). B41은 이 card + (2)로 닫는다.
- B41a `save_instance_json`의 `scope_note` 값 처리가 docstring 문면과 어긋나 보임(의도 확인 뒤 별도 card, 결함 확정 아님) -- docstring "`scope_note`(str)를 선택적으로 넣으면 그대로 옮겨 쓴다"인데 조건이 참거짓 판정(`if pipeline_result.get("scope_note"):`)이라 실측(gate `master` `4a286f0`, 격리 복제본 `C:/g239`, library 9회로 모두 같음): `""` -> 키 없음, `None`·`0`·`False` -> 키 없음, `"  "`(공백만) -> `"  "` 그대로 씀, `["x"]`(비 str) -> 그대로 씀, `"a"` -> 씀. 즉 (i) 빈 문자열(str)을 버리면서 공백만인 문자열은 쓰는 비일관 (ii) "(str)" 선언과 달리 비 str 값을 거부하지 않음(조용한 수용). 운영 경로(`workspaces/run_harness.py` 492행)는 `scope_note`를 넣지 않아 현재 산출물 영향 0, 추적 instance.json 12개(workspaces 6 + `.ai/verification` einst 6) 모두 키 없음. 정할 것: 빈·공백 문자열을 쓸지/거부할지, 비 str 거부(IC3식 `ValueError`) 여부 -- 정하면 B41 card 계약 '계약이 아닌 것' 첫 줄을 계약으로 올리는 red-green card.


## B56 (2026-10-02) V5 weakening_diff가 상수 삽입(튜플·목록 원소 추가)을 보지 못함
- 실측(_drafts/review_ts6_ma.md V5 절, 합성): `(1,2,3)`->`(1,2,3,4)`(자기 표의 '격자 확대'), `("a",)`->`("a","b")`(허용 목록 확대) 모두 발견 0건. replace·delete만 센다.
- 영향: 허용 목록·면제 튜플 확대가 V5 승인 없이 통과 가능. TS6 (마)는 정수 단언으로 우회(#2 T에서 리터럴 변경 1건으로 드러남).
- 처리: 게이트 card 후보(V5 insert 처리). 인프라 작업은 gmid 엔진을 막을 때만 -- 다음 게이트 card 묶음 때 검토.


## B57 (2026-10-02) card 35 redteam (g) delete-then-use가 T6 가 단독 누락을 판별하지 못함
- 근거: card 35 순서 3 auditor 판별력 ③ (audit worktree .ai/verification/20260930-v3-changed-stmt-scope/out/disc35.json). spec 계약 8 (g) 구성 문구가 원인(지운 문장이 바꾼 이름을 바로 뒤 문장이 읽어 T6 나로도 대상).
- 처리: card 35는 판정 V10 probe p9로 계약을 기계 판정(재시도 없음). redteam 단계 추가(구성: `LOG.append(x)`/`LOG.append(-x)`/`return str(x)`에서 가운데만 삭제)는 다음 게이트 card(B33 또는 G1)에 test 보강으로 묶는다.


## B58 (2026-10-02) V4가 diff에 걸린 파일 전체를 lint -- 손대지 않은 기존 test가 FAIL
- 근거: _drafts/review_t0_v4.md (test_lint.py 705~734행 @4a286f0). T0 계약 11로 test_selftest_sizing_recipe.py가 diff에 들어가 test_s009 두 줄이 규칙 (1) FAIL. 범위를 바뀐 문장으로 좁히는 게이트 card는 V3 범위 card 규모(약화 승인)라 지금은 C13 면제 경로로 처리(사용자 결정 대기).

## B59 (2026-10-02) md-sync 키트 v_tools.sh --subject CRLF로 공허 PASS
- _drafts/md_sync_kit/v_tools.sh 17행, 원인 v4_subjects.py write_text(Windows CRLF). card는 완료됨 -- 키트 재사용 시  제거(T0 p3kit_t0/v_tools.sh 수정 선례).


## B60 (2026-10-06) V4 test_lint _is_leaf가 빈 리스트를 잎으로 치지 않아 `assert f(...) == []`를 피검 `return []` 복사로 오판(FAIL)
- 근거: B34 test-author 보고(test d504784). 우회로 isinstance+len==0 두 문장(판정 강도 같음, UNJUDGED로 auditor 대조). 게이트 card 후보.


## B61 (2026-10-06) V8(도입 4)·V9(도입 6b)는 도구가 도입 Phase 안에서 생겨 그 Phase 앞쪽 card가 N/A도 PASS도 정직하게 못 냄(gate rule10)
- V8: _drafts/v8_phase4_analysis.md + review_v8_phase4.md -- Phase 4 승인 2차 묶음 질문 [V8 도입](도입 5 + 늘지 않음 test 권고). 계획 커밋은 B41 push 전에 따로(게이트가 old 트리 계획을 읽음).
- V9: 6b design 작성 전 같은 구조 점검(실측: 6b card V9 N/A 로더 거부).


## B62 (2026-10-06) 착수 스크립트 cache_dir 패턴이 샌드박스 리허설을 막음(launch 스크립트 ~20개 공통)
- 근거: _drafts/review_b33_dafe.md. 복제본 gate_path가 실제 gate를 가리켜 ensure_cache가 실제 gate master로 캐시를 만들고, cache_dir는 샌드박스 gate/master와 비교해 실패(fail-closed, 거짓 PASS 없음). 미래 상태·after-push 리허설과 리허설 중 gate 이동을 막고, 샌드박스에서 바꾼 게이트 코드는 리허설되지 않음.
- 제안: launch_common.sh에 복제본 모드 전용 lc_cache_dir(샌드박스 gate/master에서 tools/gates 추출). minor 인프라 -- 리허설이 막힐 때 처리.


## B63 kit_line_shift.py r2 minor 7건 (2026-10-06, review_kit_line_shift_r2.md n1~n7)
- 판정 minor(B0·S0). 틀린 패치 0. B34 실사례에서 남은 적용 패치 0(draft_b26_1:77은 병기로 반영됨).
- n1 모호 표의 새 값이 이미 새 번호인 인용엔 이중 이동 값 -- 두 판독 병기. n2 'Measured rev:' 대문자. n3 'SR와 SD n' multi-engine. n4 '이 card의' 문서 전체 anchored 과잉·--include-anchored가 두 앵커를 함께 풂. n5 출처 설명 표지 거짓 already-new. n6 S1 단언 OR 완화 → section-inherited 고정. n7 md 실사례 수치 갱신(현재 487/0/34, 선언 줄 483행). m4 생략은 알려진 한계로 md에 한 줄.
- 우선순위: 다음 엔진 줄 이동 card(실사용) 전에만. 인프라 작업은 gmid 엔진을 막을 때만(feedback_infra_work_serves_gmid_goal).


## B64 design 30 사실 문장 B34 뒤 낡음 (2026-10-06, g1_at_6c7.md)
- design 30 5·237·251행 변이 15,650 → 6c724de 실측 15,637(B34 고친 def 4개 68→55, B34 card 368행 예측과 같음).
- design 30 492행 'B34 코드만으로 4줄 당김' 예측 ↔ 실측 SD `__file__` 1050·8962 → 1049·8948(−1·−14).
- G1 card 13·281·296·349·365행도 같은 값 -- G1 착수 직전 재측정 때 함께 고친다(runbook 재측정 단계). design 30 정정은 history H2 기록과 함께 doc card.


## 대기열 2026-10-06 (M card minor 수정 agent 끝난 뒤)
- review_d0b_vs_d0a_det5.md m2: M1~M9 계약 3 (b) '이름순' → 'card base plan reexports 그 MOD 줄 그대로(코드 포인트 순)' -- mkcards.py 192·134행 + 초안 8개.
- 같은 리뷰 m3: p3kit_m1/·p3kit_m2_m9/ move_plan_sim.py 621~624, move_plan_alltok.py 623~626 -- det4 --allow-changed 문언으로(6줄 교체+한계 주석). build323.sh가 설치.
- F2 card: F1 확정 실행 문자열 규칙을 계약 4·6 (b)에 옮김(F1 규칙 수정 agent 보고 뒤).
- T1-2 사용자 질문: T1 착수 직전(새 id V4 면제 3건 decision 기록).


## B65 인용 검사기 minor (2026-10-07, review_b26_1_qbind.md)
- t0_quote_check._read_ask: tool_result is_error 미확인(실제 is_error 8건은 answers 없음으로 이미 거부 -- 위협 범위 밖). qbind is_error 판정 `is not True` → `in (None, False)`.
- qbind _result_meta 단일 tool_result 단정 미도달(t0가 먼저), CLI jsonl 폴더 미확인, test header 잠금 약함. 고칠 때 QCHK_SHA256·T0_QCHK_SHA256 핀 함께.


## 착수 직전 재측정 대기(2026-10-07)
- D0b card 272행 SD 인용 :8610·:8956·:8990 (863a037 실제 8596·8942·8976, B34 −14) -- B26-1이 SD를 다시 바꾸므로 D0b 착수 0단계 재측정 때 함께.
- G1 card 새 measured 문단 + __file__ 1049·8948 인용(kits_recheck_863a037 1항) -- G1 착수 직전.


## B66 Phase 4 첫 card(B41·#2) 863a037 재확인 (2026-10-07, review_b41_at_863a037.md)
- B1: D0b 영구 test T-E 표본이 #2 삭제 대상 3개(solve_diode_stack_current A-6 유일 표본, MultiLeafHubParityVerdict·check_multi_leaf_hub_parity A-7 유일 표본)를 고정 -- #2 계약·V5 목록·UD-0 승인 문안에 T-E 갱신을 넣거나, D0b 착수 전에 표본 선택 원칙(삭제 예정 def 회피 가능 여부) 재검토.
- B2: T1 뒤 test 파일 경로(test_mod4/7/8) -- #2 계약 7·V5 목록·쓰기 경로·id 집합은 Phase 3 DoD 뒤 기호 기준으로 다시 쓴다.
- B3: V8 'N/A -- 계측 미도입'은 rule10 거부 -- [V8 도입] 질문(phase4_approval_question 2차 묶음) 답·계획 커밋이 B41 push 전 필요. B41 '결정 필요 항목' 문구 정정.
- S1~S6·minor·교체 문안: 결과 파일 §6. Phase 4 착수 시(Phase 3 DoD PASS 뒤) 기호 기준 재측정과 함께 반영. b41_kit/는 재사용 금지(하드코딩 경로·cd).


## B64 갱신 (2026-10-07)
- 정정안 준비됨: design30_stale_facts.patch(28줄) + design30_stale_facts.h2.md. 6df4bd7 실측 변이 15,635(B34 −13, backfill −2), V6 항목 499·346·8·6, mutate_changed·SR·SD·계획 줄 인용 다수.
- card 불필요: design 30 §9.1 (3) 사실 문장 갱신 + N3.12.2 626행 → 오케스트레이터 Role: doc 커밋(선례 7f67ec3).
- 시점 결정(원칙): §9.1 재측정 (1)이 'B34와 B26-1 둘 다 병합된 판'을 요구 → B26-1 병합 뒤 키트를 그 판에서 다시 돌려 한 번에 넣는다(지금 넣으면 두 번 고침).

## B67 판정 기록 V basis 해시 표기 -- 40자리 전체 sha 규칙 (2026-10-07, b33_at_6df4bd7.md §1·§5 K2)
- 사실: b26pre 판정 기록 V7 근거가 `--base ae1b588… --head e4d5833…`(7자 + 말줄임 U+2026)로 적혀 B33 키트 m4_records.py 옛 정규식(`[0-9a-f]{6,40}\s+--head`)에 안 걸려 과거 V7 쌍에서 조용히 빠졌다. 6df4bd7 기록 중 말줄임 표기는 b26pre·p10-df23-inventory·topology-md-sync·probe-promote-differential(뒤 셋은 같은 기록 안 전체 sha 쌍이 따로 있어 쌍 수 영향 없음).
- 조치(키트): m4_records.py가 7~40자 16진 + 선택적 말줄임(문자 `…`·JSON `\u2026`·`...`)을 받아 `git rev-parse --verify --quiet <prefix>^{commit}`로 풀고, 모호·없음이면 m4.jsonl에 `what: error` 한 줄을 쓰고 멈춘다(fail-closed, 백업 m4_records.py.pre-6df.bak). 6df4bd7 재실행 결과는 b33_kit/out/head_6df4bd7/m4_fix.jsonl.
- 규칙(앞으로): gate 판정 기록은 불변이므로 고치지 않고, 이후 auditor 브리프에 "V basis의 `--base`·`--head`·커밋 표기는 40자리 전체 sha(약칭·말줄임 금지)" 한 줄을 넣는다 -- b26_1_briefs.md §2 공통 머리 블록·§4.3·§4.6에 반영(백업 b26_1_briefs.md.pre-sha.bak). 다음 브리프 템플릿(B33 등)에도 같은 줄.
- 남은 것: 6자 이하 16진 표기는 정규식이 받지 않는다(6df4bd7 코퍼스에 없음 -- 실측). 계획서·gate 도구 쪽 규칙화(test_lint/record 검사기에서 basis 약칭 거부)는 필요 시 별도 card.


## B67 V4 면제 재검토 -- SD selftest 이관 test 4개 (2026-10-07)
- 대상: test_s133_refine_differential_and_mirror_relations·test_s134__propose_vertical_stack_ids·test_s135_section·test_s159_apply_device_roles_gap_fill(규칙 (1) 7건).
- 시점: T1(test 재배치)에서 id가 바뀌어 면제가 풀릴 때. test별로 리터럴 기대값 수정 가능하면 수정, 정당한 관계 불변식만 새 id로 재면제. 분석: _drafts/v4_legacy_4tests_analysis.md.

- B67 갱신(2026-10-07): 사용자 "다로 하자." -- 면제 대신 강화 card로 처리(B26-1 1차·2차 사이). 재검토 줄 불필요.


## B68 d0b_launch.sh S-7 손적용 배정 (2026-10-07, s7b 797→1016줄)
- m2로 design 30 §6.2 배정 규칙을 키트 안에 손적용 구현(하한·정보 판정). D0a move_plan과 중복 -- D0a 병합 뒤 S-7 callee 판정을 plan 출력으로 대체하고 손적용 코드는 지운다(중복 금지).
- s7b 판은 아직 독립 검증 전 -- D0b 착수 전에 검증(또는 위 대체 뒤 검증). review_d0b_s7.md 기준.


## B69 실패 평가 부분 스냅샷의 parent keep 필드 (2026-10-22, IT-2a O-94 재검증 N-3)
- 사실: 스냅샷 파생 규칙(계획 v6.31 N3.3)으로 keep에 봉인 항목 블록이 들어가, 봉인 항목 k에서 후보 실패가 나면 부분 스냅샷(X-3 `attach_partial`)에 k+1 뒤 봉인 항목의 parent 필드가 남고 실패 줄 `snapshot_fp`(`E/search/kernel.py:90`)에 들어간다. 커널 블록에는 전부터 있던 성질. v1.12.7에서는 '없음'이었음 -- 계획 N3.3 "'없음'이 '낡은 값'보다 안전"과 반대 방향(design 41 v1.12.8 753 '원래 취지와 다름(작음)').
- 분석할 것: 부분 스냅샷·실패 줄 fp의 소비자 전수(`git grep attach_partial`, `.partial`, `snapshot_fp`) -- 엔진이 parent·재사용·판정 입력으로 다시 읽는 자리가 0인지. 0이 아니면 계획 먼저(부분 스냅샷에서 아직 부르지 않은 keep writer 필드를 지우는 규칙 등).

- **B70** (2026-10-22, O-103) 봉인 7 경계 비교를 수치 분해능으로(봉인 1 n·eps·max|V| 선례) -- 창 끝(여유 0 경계)에서 부동소수점 오차급(1e-12 V) 거부 제거. 봉인 규칙 변경이라 계획부터. 곡률 오차(커널 선형 끝)는 해결 안 됨.

- **B71** (2026-10-22, design 41 v1.12.10 715) (S4-나) 기간 선언 triode 소자가 동작점에서 꺼짐(off)인 경우의 커널 창 동작 미정 -- 계획 몫, 발동 0.

- **B72** (2026-10-22, A6 b 분석) 기준 LUT(cap) 적재 검사가 축 앞 셋(L·VGS·VDS)만 비교하고 VS 축은 비교하지 않음(lut_set.py:290 cap_grids[:3]) -- 의도인지 결함인지 확인 필요. ID·GM 열 없는 cap 표는 on_mask None(모든 점 참).
- **E-1** (design 41 정오 대기, 다음 design 판에 묶음) 41:694 A6 b 도달 조건 사실 정정: 중점 id_equivalent_v·vdsat_v 조건 삭제(셀 None이면 외부 값 미사용), 갈림 원인 = cap on_mask·VS 격자, 실행 확인(저장소 밖 toy, wt/_drafts/evidence/2026-10-22/a6b_reachability.md).

- **E-4** (design 41 정오 대기) 4.7-8 (8) 사실 추가: IT-2b 감사에서 two_stage_ota y=1 끝점 HEAD 6/12 봉인 7 거부(|slack| <= 4.32e-6 V, tol_v 약 6.3e-3) -- O-103 범위(선형 곡률) 사례 추가.
- **B73** (IT-2b 감사) D (c)(iii) EO-1 import 0 측정이 conduct 부분문자열 대리 -- EO-1 design이 모듈 이름을 정하면 그 이름으로 교체. D (b) AST는 import 별칭(as) 미추적.

- **B74** (2026-10-22, O-106 SPICE 대조) 엔진 동작점 대 BSIM 동작점 차 90~136 mV(two_stage O1·D3, ngcc V2, folded Vg7; folded M5 여유 엔진 +119 mV 대 SPICE -17 mV) -- 후보: finger 폭 대 1 um 슬라이스, W bin, VDSAT 기준 LUT 폭 5 um, 오라클 변환(legacy_adapter). LUT가 BSIM에서 나온 값이라 손계산 근사 오차가 아닌 모형·변환 결함 가능성. 근거 it2c_spice_frame.md.

- **B74 판정 (2026-10-22)**: 원인 = it2c 분석 스크립트 spice_follow.py:43 w_key*1e-9 (nm 오독, 실제 격자 5 nm -> slice w_m 5 um). 엔진·LUT·풀이 결함 아님. 5 um x m 기하로 3회로 노드 0.3 mV 안 일치. 영향: it2c_spice_frame.md 수치 무효 -> 재측정 중(O-108 근거). 후속: (1) 진단 SPICE 기하 = slice w_m finger, m = W/w_m(실수, 진단 전용) 계획 문언 후보(oracle 출구 card) (2) vdsat_query.py 머리말 문구 정정(VDSAT 슬라이스에도 있음) (3) 실현 finger 폭 잔여 오차 최대 40 mV = DEC-89 몫.

- **B75** (2026-10-22, design v1.13.0 검증 (4)) kvl_sensitivity 닫음 분모 정확 0일 때만 None -- 0 근처 분모(루프 이득 ~1, 특이)는 fail-open. 계획 판정 분해능(δA_num)을 닫음 분모 A_u에 넓혀 쓰는 안 -- 계획 몫.

- **B76** (2026-10-22, design v1.13.0 재검증 N-3) 규칙 A(새 공개 이름 사용자 >= 2) 검사기가 `__init__` 재수출도 사용 파일로 센다 -- 클래스·실사용(import 후 호출) 기준으로 고친다. 이번 판정은 실사용자 둘(block_columns, icm_config)로 취지 충족 확인 기록(41:760). 인프라 백로그(엔진을 막지 않음).

- **B77** (2026-10-22, 계획 v6.34.1 재검증 S-1 파생) `metrics_aux`(164-166)·`metrics_ss`(401-403)는 `SsCircuit.missing`이 용량만이어도 요청 전체(DC metric -- offset·스윙·ICMR 등 포함)를 `passive_value_undeclared`로 낸다. DC/AC 분리(DEC-67): DC 양은 결측 저항일 때만 정의 불능이어야 한다. IT-2c는 ss_nodal·icm_config만 좁힌다 -- 두 블록 정리는 별도 card.

- **B78** (2026-10-23, ICMR 정의 재검토 실측 icmr_definition_review/analysis/table.txt) nmcnr_amplifier에서 엔진 KCL 선형 끝 대 SPICE 위 끝 오차 +815 mV(follower A)·+817 mV(servo T)·+121 mV(S) -- 정의와 무관하게 같은 크기. 다른 4회로는 <= 50 mV. 원인 미상(봉인점 의심 또는 선형 틀 범위 밖 비선형). IT-2c 감사에서 일반성(회로 전수) 측정 때 재현·원인 조사.

## B79 (2026-10-24) 피크 부하 전류 행의 셀 전류 상한·하한 미증명
- `ls_fields` 방향별 전류(beta = 봉인점 ID, kappa = None)가 피크 부하 행(`load_peak_margin_a`)에 쓰인다. 내부 단자 beta(접힌 가지·cascode)는 슬루 중 전류가 봉인점보다 커질 수 있고(1.19x 실측), kappa = None은 행을 미측정으로 보낸다.
- 코퍼스 `load_peak_amp` 선언 0 -> 지금 엔진 결과에 영향 없음. 첫 선언이 생기는 card의 착수 조건으로 건다(판정 방향: 통과 판정이면 보수 하한, 잘라냄이면 증명된 상한).
- 출처: O-122, plan agent 소비자 grep(integ/it12 3179cd78).

## B80 (2026-10-24) pushpull_follower_buffer find_front가 front 0점
- 봉인되고 spec(rout <= 1 kOhm)도 맞는 점이 있다(theta 전류 x10^5.5: 정지 48 uA, SPICE rout 500 Ohm). 그런데 find_front는 eval 40에서 `eval_budget`, eval 2000에서 두 방향 모두 `slsqp_4`로 멈춰 front 0점이다. 원인은 재지 않았다.
- layer0은 feasibility 중심(rout spec 미포함)이라 정지 0.15 nA, rout 1e8 Ohm에서 시작한다. theta 전류 상자가 26자릿수에 걸친다.
- IT-0 기준선 기록과 중복되는지 확인하지 않았다.
- 출처: `_drafts/evidence/2026-10-24/classb_gmid_op_point.md`, `_scratch_classb/out/spice_pp.jsonl`.

## B81 (2026-10-24) sf_pushpull_output_opamp·current_reuse_telescopic_ota 봉인점 없음
- sf_pushpull: layer0 실패. 상자 0/400, IBias 앵커 0/1500.
- current_reuse: layer0 실패. 앵커 0/600, 상자 0/300.
- class-B와 무관한 별도 결함으로 보이지만 추정이다. IT-0 기준선과 중복되는지 확인하지 않았다.
- 출처: 위와 같음(`*.anchor.jsonl`, `*.box.jsonl`).

## B80 갱신 (2026-10-24) library front 0 (7/9) -- 원인 = as-built 층 0 최소형이 ss 선언(rout·GBW 등)을 안 씀
- 분석: `_drafts/evidence/2026-10-24/b80_pushpull_front_zero.md`, 원자료 `_scratch_b80/`. pushpull 1차 원인 = DEC-71 (3) 버퍼 rout 국소 AC 제약(design 41 E10) 미구현 -> 출발 전류 = W_min 자리값 0.15 nA. E10 손계산 출발(정지 24 uA)이면 엔진 무수정 front 1. 증폭 = rout 행이 먼 곳에서 평평(c -> -1/rho), SLSQP status 4(IIS = rout 행).
- 일반성: library 9 중 front 0이 7(pushpull, two_stage, two_stage_sf, folded, ngcc, nmcnr, current_reuse·sf_pushpull은 B81), common_gate만 2.
- IT-0 기준선 M-I3 n_front가 이미 기록(0)했지만 FE 지표가 결함으로 세지 않았음. 원인은 미기록이었음.
- '층 0 무동작'·'성능 판정 보류' 보고 경로 없음(WP-01 소지). design 41 861행 '(as-built와 같다)'는 사실과 다름.
- 덮는 card = LA-1(계획 그대로). 권고 (가).

- 정정(2026-10-24 오케스트레이터): O-125·B80 갱신의 'library front 0 (7/9)'는 셈 오류 -- B80 근거 파일 §4 표는 9회로 중 8회로 front 0(common_gate만 2점; sf_pushpull·current_reuse는 B81 봉인점 없음 포함). 봉인점 없는 B81 둘을 빼면 7회로 중 6회로. 계획 v6.38 F-LA12는 표대로 '9회로 중 8회로'.

## B82 (2026-10-24) 계획 결정 대상 -- design v1.14.2 검증·gap에서 올라온 것
- (a) spec 로더 `spice_unverifiable`(U5/MOD2, as-built MISS)를 VB-1 선행/착수 조건으로 둘지. VB-1 완료 조건 (1)이 이 로더에 걸림. 근거 design_v1142_validation.md M-2.
- (b) `load_dc_amp` 출력 포트 KCL 항(DEC-58, 미구현, 엔진 소비자 0)의 담당 card. 근거 design_v1142_vs_plan_v637_gap.md D-3.
- (c) 계획 P609 metric 결측 판정의 '`ls_fields` 슬루' 문언: DE-1 (d) 뒤 그 보고엔 DC 양만 남음 -> DEC-67·B77과 맞게 개정 검토(DE-1 때). gap P-1.
- (d) U-115 재질문 때 원칙 점검: DEC-65 정의(입력을 끝까지 몬 고정 회로 DC 해)는 DEC-103상 KCL 틀, 후보 (가)(나)는 theta 틀 손계산 -- 틀 정합 경고 함께. 검증 관찰.
- 처리: 다음 계획 개정(v6.39 또는 해당 card 착수 전)에 올림.

## B81 갱신 (2026-10-26) 원인 = 층 0 출발점 KVL 비정합 + 얇은 봉인 영역 (모델·정의 문제 아님)
- 분석: `_drafts/evidence/2026-10-26/b81_no_seal_root_cause.md`, 원자료 `_scratch_b81/`.
- sf_pushpull: 사다리 칸 0이 KVL 비정합(자기 바이어스 R*I << dVGS+VDsat; W4 창이 하류 게이트 사슬을 안 봄 -> N910 vdd 위) -> pmos M9·M10 VDS<0 -> tol_v 조회 실패. 예산 6000에서도 출발점 0. 원문 IBias 50 uA 손계산 theta 280/672 봉인, SPICE .op 노드 1.3 mV·전류 0.05 % 이내.
- current_reuse: 자기참조 노드 Ncmfb_tail 창에 근 없음. 직접 원인 = 평가 예산 40(fixture) -- 2000이면 Halton 927번째(커널 1112회)에서 출발점·max-min 수렴. 원문 노드 보존 theta 20/21 봉인, SPICE 노드 1 mV·전류 2.3 % 이내. MOD5·B34 무관.
- 나머지 7회로는 예산 40에서 층 0 성공. 잠재 조건(구조): (C1) 레일 KVL 경로가 W4/자기참조 노드 지나 VGS 강하 둘 이상 (C2) 자기 바이어스 R과 I가 독립 theta (C3) pmos 헤드룸 분할.
- 귀속: LA-1(DEC-71 (4) VDS 배분·기둥 KVL). gap: DEC-71 기둥은 게이트 엣지 제외 -> (C1) VGS 고리와 (C2) R*I 조건이 문언에 없음 -> LA-1 착수 전 design 41 §5 대조, 없으면 계획 DEC-71부터 개정.

## B81 추가 (2026-10-26) 출발점 이후 문제와 정정
- current_reuse: 예산 2000 출발점(Halton 927) 뒤 find_front front 0(1808 s, 커널 1555). 층 0 출발점 자체가 P 479 W·A 104 m2(theta 전류 15.9~47 A, 면적 예산 4e-8 m2) -- B80과 같은 꼴(층 0 feasibility_only, spec·면적 제약 미사용). 원문 전압 보존 점은 W 하한(M39 0.095 um < 0.42 um)·면적 예산(20배)을 못 넘음 -- 앞 보고 §3.2 정정.
- sf_pushpull: hp_sf3 봉인 280점은 전부 면적 예산 초과 -- 앞 보고 §3.1 정정. 재측정: 봉인 482점 중 면적 예산 안 56점(실측 확인, area_ok 57줄 중 요약 1줄 제외 추정), SPICE 노드 20 mV·전류 0.6 % 이내. rout 충족은 미측정(추정 미충족).
## B83 (2026-10-26) 봉인이 접합 누설·W 상한을 보지 않음 (결함 후보, 약)
- sf 손계산 점 M21 W 1.8e4 m에서 소스-벌크 접합 누설 39.3 uA가 vout KCL에 들어가 SPICE M21/M22 125/85.8 uA. 엔진 KCL은 채널 전류만. 커널 면적 행이 그런 점을 거르므로 영향은 출발·진단 점 한정(추정). 근거 `_drafts/evidence/2026-10-26/b81_no_seal_root_cause.md` §9.

## B84 (2026-10-26) nmcnr SR spec data 커밋 대기 (O-129)
- 방향별 SR(0.36/0.31 V/us)을 넣을 `constraints[]` .tran 키(slew_rise/fall)가 로더에 없음. Q5 spec 형식 card에서 키 신설과 함께 nmcnr data 커밋. heldout 슬루 선언 3개 이관도 같은 card.

## B84 갱신 (2026-10-26) spec 형식 card 대상 추가
- current_reuse: gain_ss_db >= 54 삭제, static settling error <= 0.1 % 원천 spec 신설(O-133), settle_s <= 40 ns(O-132), SR 미선언(O-132). nmcnr SR 0.36/0.31(O-129), ngcc 상승 SR 6.3(O-130).

## B85 (2026-10-26) 매크로 목표 gm이 theta 전류로 전파되지 않음 (folded_cascode)
- GBW 선언 시 매크로 gm 62.9 uS 정확, 그러나 theta 전류 M3·M4·M5·M6·MP 모두 uncovered -> 층 0 점 GBW 0.37 MHz. 원인 추정: 입력 소자 전류가 theta 전류의 차라서 `iv_currents` '미지 항 하나 방정식부터 전파' 규칙이 못 풂(코드 경로 미추적). two_stage는 같은 경로로 전파됨. LA-1 범위에 포함(O-140 D8). 근거 `_drafts/evidence/2026-10-26/spec_candidates_folded_cg.md` §6.
## B86 (2026-10-26) folded·common_gate spec data 커밋 대기 (O-140 D7)
- LA-1 병합 뒤 data 커밋: folded PM>=70·gain>=70·GBW>=10 MHz, common_gate C_L 1 pF(topology)·gain>=35·GBW>=10 MHz. pending_constraints SP-3~SP-5 제거.


## B87 (2026-10-26) beta=1 사용 시 출력 범위 ∩ ICMR 결합 -- 공집합 가능
- 출처: O-156, evidence/2026-10-26/swing_proposal_two_stage_ota_sf.md §4(gm/ID 10·12에서 교집합 없음, 15에서 34 mV), swing_proposal_folded_cascode.md §3(ICMR 하한 0.806 대 출력 하한 0.797), swing_proposal_two_stage_ota.md(follower [0.97,1.32]).
- 문제: follower(beta=1) 사용 회로의 DC 사용 창은 출력 범위와 입력 CM 창의 교집합인데 엔진은 이를 일반 규칙으로 잡지 않는다. 같은 gm/ID 가정 손계산 결론이라 실측 필요.
- 다음: 소자별 gm/ID로 oracle .dc 확인 -> 필요하면 계획 개정(결합 제약 형식 E안, 사용자 결정). 출력 범위 미선언 회로와의 관계 포함.

## B88 (2026-10-26) 약반전 pfet BSIM vdsat 바닥 -> 포화 판정 낙관
- 출처: O-156, swing 해석 5건 공통 지적(pfet gm/ID 약 18 이상에서 vdsat 약 0.045 V 바닥, nfet도 유사 경향).
- 문제: spec saturation_rule vds_ge_vdsat(BSIM vdsat, 여유 0)이 약반전에서 물리적 포화 여유보다 낙관적일 수 있다. 엔진·oracle이 같은 규칙인지, 판정 정의(DEC-88·봉인 7)가 약반전에서 맞는지 미확인.
- 다음: oracle과 엔진의 포화 규칙 대조, 약반전 점에서 SPICE gds 기준 실측 -> 정의 개정 필요 여부를 계획 결정으로.


## B89 (2026-10-26) oracle 어댑터 출력 부하 이중 (F-1)
- 출처: rereview_A §F-1, rereview_D 부수 발견, 오케스트레이터 코드 확인(integ-it12 tools/spice_oracle/legacy_adapter.py has_load가 0 V 레일 ref_net에 붙은 C만 부하로 셈 -> agnd에 붙은 nmcnr CL을 놓치고 LOAD_<out> 추가), E 넷리스트 실측(Cp_CL Vout agnd + Cp_LOAD_Vout Vout 0).
- 영향: nmcnr SR 약 1.93배 과소(0.108 -> 0.208, allx2 FAIL -> PASS 0.364), U-112 nmcnr '수렴 0/7' 무효, ngcc 1 % 미만. as-built oracle nmcnr GBW·PM 판정 경로 영향 미확인.
- 처리(O-157 S6): 어댑터 수정 card(oracle-portability EO-1/OP 범위), 재측정 = 2026-10-23·10-26 nmcnr 슬루 증거·U-112 nmcnr·E T2 끝 시각 민감도·oracle nmcnr GBW·PM.
