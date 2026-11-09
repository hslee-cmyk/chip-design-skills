---
id: 20260930-30-module-split-design
date: 2026-10-02
target_kind: diff
target: <rev-parse>
diff_base: <rev-parse>
diff_head: <rev-parse>
diff_path: docs/01-plan/features/gain-budget-gmid-sizing.plan.md
diff_path: docs/02-design/features/gain-budget-gmid-sizing.00-common.design.md
diff_path: docs/02-design/features/gain-budget-gmid-sizing.10-test-separation.design.md
diff_path: docs/02-design/features/gain-budget-gmid-sizing.30-module-split.design.md
diff_path: docs/03-analysis/gain-budget-gmid-sizing-30-module-split/scripts/e_inst_p3.py
diff_path: docs/03-analysis/gain-budget-gmid-sizing-30-module-split/scripts/e_lib_p3.py
scope: Phase 3 design `30-module-split` v8.5 승인(DEC-51, UD-0)과 그것이 덮는 문서 개정(계획 N3.10 표 정정 12건 -- MOD1~MOD6·MOD8·MOD9 행, D-19 (가) `rail_declaration` MOD2 포함 -- 534행 shim, N3.12.3 test-only T0·T1, 00-common 103·431행 `topology_path`, 10-test-separation §5.6 '파일' 열)·Phase 3 E-INST·E-LIB 측정 스크립트 2개, U-03(UD-1) (가) 계획 기본안
---

## 사용자 원문

> 승인 (Recommended)

> (가) MOD2 (Recommended)

> (가) 깨지게 둠 (Recommended)

(AskUserQuestion 한 번에 올린 네 질문 중 셋의 답이다. 질문 2026-10-02 01:46 KST, 답 2026-10-02 11:05 KST -- 세션 기록 `63c6146a-ab1d-4035-a169-bae810986922.jsonl`의
tool_use `toolu_01VKN8qT3BbTikfZQyV9sdQi`(headers UD-0·D-19·UD-5·UD-1)와 그 tool_result에서 바이트 대조해 옮겼다. 넷째 답 UD-5는 G1 승인 기록 `20260930-p3-gate-move-aware`가 인용한다.)

* 질문 [UD-0] 원문: "[UD-0] design 30-module-split(10모듈 분할, card 17건 — 준비 card FU 포함)과 문서 개정(N3.10 표 정정 12건 등), 기준에 닿는 기본값 (a) 판정 기록 스크립트 2개·원자료 1개 미갱신 (b) 계측 probe 8개 덮어쓰기 대상 이동 (c) 동작 보존 = Phase 2 완료 판정 판(5f643a9)과 직접 비교, meta["rails"]만 계약값 정확 일치 (d) 이관 목적지 열 = 하한, 계층 요구 시 승격(32개, 구조 제안 12개→MOD3, MOD7로는 승격 안 함)을 승인할까요?"
  선택지: "승인 (Recommended)" -- "위 범위 그대로. 이동 도구가 실제 코드에서 추가 표 개정을 계산하면 그때 다시 묻습니다." / "승인 + 추가 표 개정 위임" -- "이동 도구가 계산한 추가 표 개정은 다시 묻지 않고 계산 결과대로 반영합니다." /
  "수정 요청" -- "(a)~(d) 중 바꿀 것을 지정해 주십시오(예: (c) B0와 비교 + card 판정 기록 사슬 / (d) 열을 정본으로 두고 충돌 함수 32개를 계획 표에 적기)." / "보류" -- "Phase 3 착수를 미룹니다."
  답: "승인 (Recommended)".
* 질문 [D-19] 원문: "[D-19] rail_declaration(B26-1의 전원 선언 접근자, supply_nets 형식을 검사·거부, 유일한 호출자 load_topology는 MOD3로 감)을 어느 모듈에 둘까요?"
  선택지: "(가) MOD2 (Recommended)" -- "N3.10 MOD2 대표 대상에 이름을 더합니다. 선언 형식 검사 함수(validate_metric_units 등)와 같은 곳이고 B37a의 port_declaration도 같은 곳에 둡니다. 계층 위반 없음." /
  "(나) 규칙대로 MOD3" -- "유일한 호출자 load_topology 옆입니다. 계획 표에 이름을 더하지 않고, MOD2의 선언 검사 함수들과 떨어집니다."
  답: "(가) MOD2 (Recommended)".
* 질문 [UD-1] 원문: "[UD-1] 추적되지 않는 스크립트 workspaces/current-reuse-telescopic-ota-report/smoke_run_harness_session18_save.py는 sizing_recipe(SemiEmpiricalGmIdLUT·optimize_full_circuit_budget)와 stick_diagram.save_instance_json을 import합니다(9·10행). shim 삭제 뒤 두 import가 모두 깨집니다. 어떻게 할까요?"
  선택지: "(가) 깨지게 둠 (Recommended)" -- "계획 기본안입니다. 추적 파일만 갱신합니다." / "(나) 추가하고 F1에서 갱신" -- "지금 저장소에 추가(추적)하고 호출부 갱신 card(F1)에서 함께 갱신합니다." /
  "(다) 삭제" -- "사용자 작업입니다(오케스트레이터는 추적 안 된 사용자 파일을 지우지 않습니다)."
  답: "(가) 깨지게 둠 (Recommended)".

질문의 배경 문안은 `_drafts/phase3_approval_question.md` v8.5(sha256 `71bd157242a7da332f7efbcd32110ae6cb9876c4f8fd52faf99e0e49a626da0f`)다.

## 범위 설명

승인 대상 판(질문 때 올린 바이트, sha256 전체):
* design 초안 `_drafts/draft_phase3_design_v8.md` v8.5 `a4350dc05ff861799b15b0aa7e0a0af53c06c887b428718d4397e7f7b0cea9db` -- 저장소 파일
  `docs/02-design/features/gain-budget-gmid-sizing.30-module-split.design.md`는 이 바이트에서 **3행(초안 표지 "[초안 v8.5 -- 저장소 미반영] … (현재 없음).")만** 승인 표지로 바꿨다(본문 1,397행 중 나머지 1,396행 동일).
* 문서 개정 문안 `_drafts/p3_doc_amendments.md` v8.5 `363e3cc2da4fc96dd423e3ec1b8670b9e41742228ef2ea0567df972e4a29fd3a` -- §1 (a)는 D-19 답에 맞는 **(가) MOD2** 문안.
* 새 측정 스크립트 `e_inst_p3.py` `7d26134ad00ec50412bf65b1fcc3aa046845a315b8edf28dc93f4a102c25e283`, `e_lib_p3.py` `c6b82fc7b4cd974ce06032559c92ecdcc8cf21e327b154e4a56bda0772aa140e`(같은 바이트).

덮는 것:
* design `30-module-split` v8.5 전체(DEC-51): 범위·인터페이스(10모듈 파일 배치, shim 규칙, MOD10 진입점)·판정식·실패 경로·G1 이동 인식 방향·이관표 생성 규칙(§6.2 A-1~A-7·A-K·승격)·spec card 17건(준비 card FU 포함)과 순서·착수 조건·
  §9.3 원칙 유도 기본값 D-1~D-31·DoD 측정 명령(E0~E6, E3b, IMPORT-ANY, `PT3`).
* 이 design이 덮는 spec card 17건(design §8 -- 질문 원문 "card 17건 — 준비 card FU 포함"). 초안이 있는 card의 id(`_drafts/draft_p3_*.spec.md` 머리 `id:` 그대로):
  * G1 `20260930-p3-gate-move-aware`(phase 0.5, 게이트 변경 -- 설계 방향은 이 기록, 게이트 변경 승인은 UD-5 기록 `20260930-p3-gate-move-aware`)
  * T0 `20260930-p3-tests-location-free`(test-only -- V5 승인은 뒤에 올 기록 `20260930-p3-tests-location-free`)
  * FU `20261002-p3-future-annotations`(equivalence -- 아래 D-29)
  * D0a `20260930-p3-move-plan-tool`(red-green)
  * D0b `20260930-p3-registry-dest`(red-green)
  * 초안 아직 없음(design §8 slug, id 날짜는 card 작성 때): M1~M6·M8·M9 `p3-move-mod<n>-<이름>`, M10 `p3-mod10-entry`, T1 `p3-test-relocate`, F1 `p3-callers-update`, F2 `p3-shim-delete`(M7은 M2·M3·M9에 흡수).
* **준비 card FU `20261002-p3-future-annotations` = design D-29**. D-29 원문: "(v8.4, G1 착수 키트 0.2) **`__future__` 혼합은 준비 card FU로 푼다**: D0b 전에 `design_report.py`·`audit_current_forced.py` 머리에 `from __future__ import annotations` 한 줄씩(equivalence).
  (가) M card V3 판정·(다) 배정 변경은 기각(§6.5 표)" -- 근거 칸 "승인된 기준을 바꾸지 않아 UD-0 범위(card 수 16 → 17은 질문 본문에 사실로)". 곧 DR·ACF 머리 `from __future__ import annotations` 한 줄, 동작 불변, card 16 → 17.
* 질문에 드러낸 '기준에 닿는 기본값' (a)~(d) -- 사용자 원문 "승인 (Recommended)"(설명 "위 범위 그대로. …")로 그대로 승인:
  * (a) 질문 원문 "판정 기록 스크립트 2개·원자료 1개 미갱신" = D-9 -- 534행 "추적 파일 전부 갱신"의 예외: 판정 기록 증거 스크립트 `.ai/verification/**`와 기준 커밋 원자료 `probe_stage_partition.py`는 갱신하지 않는다(F2 뒤 깨지는 것은 근사 배정 기준 판정 기록 스크립트 2개·원자료 1개, 기록된 base 커밋에서만 재실행).
  * (b) 질문 원문 "계측 probe 8개 덮어쓰기 대상 이동" = D-17 -- §7.2 D군 probe·진단 스크립트 8파일(대입 14줄)의 덮어쓰기 대상을 F1에서 `binding_origin`으로 찾은 호출자 모듈 전부로 바꾸고, F1 oracle에서 그 대입 줄만 예외.
  * (c) 질문 원문 "동작 보존 = Phase 2 완료 판정 판(5f643a9)과 직접 비교, meta["rails"]만 계약값 정확 일치" = D-28 (e) -- E5: P2D `5f643a9`와 Phase 3 마지막 병합본을 같은 경로에서 비교, E-LIB `load_topology` `meta["rails"]`만 해시에서 빼서 계약값(`RailDeclaration`, nets = P2D library의 `supply_nets`)과 정확 일치로 따로 판정.
  * (d) 질문 원문 "이관 목적지 열 = 하한, 계층 요구 시 승격(32개, 구조 제안 12개→MOD3, MOD7로는 승격 안 함)" = D-31 -- 계획 517행 '레지스트리 이관 목적지 열이 정본'을 '칸 MOD = 하한'으로 읽고 계층이 요구하면 승격(시제품 32단위), MOD7 상한; D0b가 열을 도구 출력으로 다시 써서 열 = 이관표.
* 문서 개정(같은 diff): 계획 N3.10 표 8행(MOD1·MOD2·MOD3·MOD4·MOD5·MOD6·MOD8·MOD9) -- 원래 3건(`load_topology`·`validate_theta_declaration_order` → MOD3, `optimize_full_circuit_budget` Phase 3 위치 MOD8),
  A-1 충돌 보정 8건(토큰 11개: `require_declared_spec_source`·`find_hub_merge_candidates`·`signal_path_nodes` → MOD3, `metric_unit_scale` → MOD2, `_build_theta_evaluator`·`search_stage_budget_L_warm_start`·`presolve_warm_start`·`_optimize_theta_slsqp`
  Phase 3 위치 MOD8, `apply_theta_feed` Phase 3 위치 MOD5, `_metric_nulling_resistor_ohm` → MOD4, `_multilinear_interp_point_multi` → MOD1), 책임 보정 1건(`_kv_table` → MOD9) = 질문의 "N3.10 표 정정 12건";
  계획 534행 shim 문장(D-2·D-9, `topology_library.py`·`design_report.py` shim, `stick_diagram` 임시 재수출 삭제 조건, D-9 예외), N3.12.3 test-only 열거에 "Phase 3 T0·T1", `00-common` §3.3 103행·§10.1 431행(D-5 --
  진입점 `run_gmid_design_pipeline`의 `topology_path` 인자, 진입점과 `topology_path`·`search`·`output_dir`는 Phase 3 M10), `10-test-separation` §5.6 영역 표 '파일' 열을 설명으로(T0 -- 영역 값 21개·함수 이름·이유 열 불변, oracle (d) 불변).
* **D-19 (가)**: `rail_declaration`(B26-1 전원 선언 접근자)은 MOD2 `topology_authoring` -- N3.10 MOD2 '대표 대상'에 이름을 더한다(위 문서 개정에 포함). B37a의 `port_declaration`도 같은 결정을 따라 그 card 커밋 때 적는다(design 30 §6.4).
* **UD-1 (가) = U-03(계획 N7.2) 답**: 계획 기본안 그대로 -- 추적 파일은 전부 F1에서 갱신하고, 추적되지 않는 `workspaces/current-reuse-telescopic-ota-report/smoke_run_harness_session18_save.py`(9·10행 import)는
  F2(shim 삭제) 뒤 두 import가 깨진 채 둔다. 오케스트레이터는 그 파일을 추가·수정·삭제하지 않는다.
* 새 파일 `docs/03-analysis/gain-budget-gmid-sizing-30-module-split/scripts/e_inst_p3.py`(F1 뒤 E-INST -- `e_inst_df36.py`와 엔진 출처 확인 한 곳만 다름, D-28)와 `e_lib_p3.py`(DoD E5 전용 -- `e_lib.py` + meta 키 빼기 인자, D-28 (e)).
* 판정 표 불변: 바뀐 계획서 줄(N3.10 표·534·687행)은 `plan_tables_hash` 입력(N4.1·N4.2·N6.1·N3.12.2) 밖이다 -- 커밋 전후 해시가 같다(값은 design 커밋 본문). 바뀌었다면 이 기록이 아니라 `plan_tables` 승인이 필요하다.

덮지 않는 것:
* UD-5(G1 게이트 변경, 답 "(가) 전역 이동 인식 (Recommended)") -- 별도 승인 기록 `20260930-p3-gate-move-aware`(`target_kind: diff`, G1 spec card·interface card·design 05 §10·계획 N3.10 533행 '이동 규칙' 줄 한 문장 -- G1 card 문서·spec 커밋 뒤).
  계획 533행은 이 diff에서 바꾸지 않는다(G1 spec card 계약 13).
* D0b가 B26-1·B34 병합본에서 **새로 계산하는** N3.10 개정(위 12건 밖의 `conflicts`·`upward`) -- 위임하지 않는다(답의 설명 "이동 도구가 실제 코드에서 추가 표 개정을 계산하면 그때 다시 묻습니다"). 나오면 D0b가 멈추고 그 diff를 따로 승인받는다(D-11).
* 뒤에 올 승인: T0·T1·F1의 V5 승인(test 커밋 뒤 diff 해시 -- T0는 '비교 완화 1건(유일성 단언)'을 이름으로), M10 V3 생존이 남을 때의 면제 승인, 각 card의 판정(판정 기록).
* 레지스트리 '이관 목적지' 열 재생성(D0b, code-author 경로)과 엔진 이동 자체 -- 이 기록은 설계와 문서만 덮는다.
