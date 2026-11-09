# card-specific prose for mkcards.py (exec'd). Facts here are from this scratch measurement or cited docs.
import os as _os
if _os.path.exists("C:/g226/out/iface.json"):
    IFACE = json.load(open("C:/g226/out/iface.json", encoding="utf-8"))
OPEN_REF = {
    "topology_authoring": "O-1·O-2·O-5·O-7",
    "circuit_state_graph": "O-1·O-2·O-7",
    "gmid_sizing_engine": "O-2·O-3·O-4·O-7",
    "circuit_metrics": "O-2",
    "theta_search": "O-2",
    "sizing_layout_convergence": "O-3·O-4·O-7·O-8",
    "instance_report_builder": "O-2·O-3·O-5·O-6",
}
COMMON_DEC = [
    "**M1-1·M1-3 그대로**: MOD 파일 모듈 docstring 없음(M1-1 (가) -- 모의 R-7이 `changed` 1로 거부되는 것을 이 card에서도 확인), E3·E3b 식 card 단위 사용(M1-3, 강화).",
    "**M1-2 닫힘**: 사용자 결정 D-11 (가)(2026-10-02 \"(가) 계획 표 MOD1에 추가 (Recommended)\")로 `_QUERY_CACHE_MAX`는 MOD1. 이 card 수치는 그 개정과 계약 문언 키(바인딩 이름)를 적용한 판이다 -- 조건('D0b가 다른 개정을 더 계산하면 다시 묻는다')대로 이 모의에서는 그 밖의 `upward`·`conflicts`가 0이었다.",
]
CARD_DECISIONS = {
    "topology_authoring": COMMON_DEC + [
        "**W-2 ACF 재수출 위치(질문 없음 -- design §2.2 목적문 안, p3_followup §3.2)**: 계약 10과 거부 입력 R-W2에 넣었다. 생성기의 머리 계산(`sys.path.*` 식 문장을 머리 묶음으로 넘김)은 `p3kit_m2_m9/gen226.py`.",
        "**B26-1·B34 미반영(W-9)**: 실제 base에서 MOD2 단위가 바뀐다 -- D-19 (가)(`rail_declaration` → MOD2, A-1)와 `RailDeclaration`(A-2 -- MOD2 구조 제안 함수의 `rails: RailDeclaration` 주석)이 더해질 것으로 본다(design §6.4). 그리고 B34가 바꾸는 def 4개(`_import_analog_grammar`·`find_idiom_matches`·`find_stack_edges`·`audit_theta_root_direction`)가 **모두 이 card 단위**다(모의 배정 A-4) -- 바이트 이동이라 B34 판 본문 그대로 옮긴다. `_import_analog_grammar`는 `__file__`을 읽지만 같은 디렉터리라 G1 M-4가 인정한다(모의 `move-rejected` 0). 단위 수·`mod_imports`는 D0b 판정 기록 값으로 바꾼다.",
    ],
    "circuit_state_graph": COMMON_DEC + [
        "**B26-1 계수 test(T0 계약 10)**: `load_topology`가 이 card에서 MOD3로 간다(모의 SD 8124~8313, A-1). B26-1 병합 뒤 `test_b26_rail_accessor.py`(design §7.1 v5 A군)는 래퍼 대상이 R-DEF 정의 파일 + import 바인딩 엔진 파일 전부여야 통과한다 -- T0 계약 10 몫이고 T0 병합이 착수 조건이다. 모의에는 B26-1이 없어 측정하지 못했다(실제 base에서 auditor가 PT3로 잰다). D-19 (가)면 `load_topology`(MOD3)가 `rail_declaration`(MOD2)을 import하는 줄이 `mod_imports`에 생길 것으로 본다(작은 번호 쪽 -- ORDER 허용).",
        "**규모(W-12)**: 82단위·100 def -- 바이트 이동이라 card를 나누지 않는다(모듈 하나 = card 하나, N3.12.3 674행).",
    ],
    "gmid_sizing_engine": COMMON_DEC + [
        "**W-1 완전 shim(사용자 결정 (가))**: TL이 이 card에서 완전 shim이 된다. 이 card는 추가 import를 남기지 않는다 -- T0가 `test_selftest_topology_library.py:24`의 `math`(그리고 M8·M9 몫 6이름)를 출처 import로 바꾼 뒤다. 모의(T0 W-1 대역 포함) PT3 수집 오류 0(이전 모의 M4 상태 `1 error during collection` -- m_cards_plan W-1).",
        "**문장 키 변경으로 이 card에 온 상수(W-4)**: 계약 문언 키(바인딩 이름)로 `_COMPENSATION_REGISTRY`·`_L_ROLE_TARGETS`가 MOD8이 아니라 **MOD4**(레지스트리 칸 A-4)로 온다 -- m_cards_plan 표의 MOD4 102단위(시제품 키) → 104. 계층 위반·`import_time_high` 0(p3_followup §1.4 '(i)').",
        "**CACHE-ID(W-7)**: `_KNEE_L_CACHE`·`_FEASIBLE_L_WINDOW_CACHE`가 `knee_L_for_kind`·`feasible_L_window`와 함께 MOD4로 온다(모의 `cache` 0). TL `@functools.lru_cache(maxsize=256)`(데코레이터 포함 바이트 이동, 모의 MOD4 221행)는 함수 단위 캐시라 CACHE-ID 대상 밖.",
        "**규모(W-12)**: 104단위·126 def.",
    ],
    "circuit_metrics": COMMON_DEC + [
        "**계층 확인**: `mod_imports`가 MOD3·MOD4에서 이름을 가져온다(`_metric_*` 중 MOD5 함수를 부르는 것은 승격으로 MOD5, 나머지는 MOD4 -- design §6.2 A-4 v8.4 정정). 모의 `upward` 0·`order` 0.",
    ],
    "theta_search": COMMON_DEC + [
        "**MOD6 범위**: `optimize_full_circuit_budget`·`_build_theta_evaluator`·`search_stage_budget_L_warm_start`·`presolve_warm_start`·`_optimize_theta_slsqp`는 Phase 3 위치 MOD8(UD-0 개정 -- D-3)이라 이 card에 오지 않는다(모의 MOD6 11단위, `repair_infeasible_baseline` A-1 하나 + A-4 10).",
    ],
    "sizing_layout_convergence": COMMON_DEC + [
        "**W-1 완전 shim(사용자 결정 (가))**: SR이 이 card에서 완전 shim이 된다. SR의 비엔진 import 이름(`_dc_replace`·`json`·`math`·`np`)과 TL 이름 `nmcnr_predict_ac_response`를 SR 경유로 읽던 `test_selftest_sizing_recipe.py:24`는 T0가 이미 출처 import로 바꿨다 -- 모의 W-1 점검 0곳, PT3 수집 오류 0. **SHIM (c)**: SR의 base 재수출 `from stick_diagram import (Transistor, load_topology, …)`(gate master 5302행)는 남긴다(모의 병합본 SR 42행 -- F1 초안 '결정 필요 항목' 5).",
        "**D-22 끝 import(W-5)**: MOD8은 SD 이름 14개를 파일 끝 한 줄로 받는다(재현할 수치). 모의 IMPORT-ANY 실패 0. **R-D22(그 줄을 머리로 올림)는 이 card 병합본에서 `check`·G1·IMPORT-ANY를 모두 통과한다**(SD가 아직 MOD8·MOD9를 import하지 않아 순환이 없다 -- 작성 전 실측 10) -- 그래서 배치는 계약 3 (a)의 문장 열 비교가 판정한다(open items O-8). M9에서는 같은 변형이 IMPORT-ANY FAIL.",
        "**CACHE-ID(W-7)**: `_ACHIEVABLE_BOUND_CACHE`가 `achievable_metric_bound`와 함께 MOD8로 온다(모의 `cache` 0).",
        "**문장 키 변경(W-4)**: `_COMPENSATION_REGISTRY`·`_L_ROLE_TARGETS`는 M4로 갔다(이 card 30단위 -- 시제품 키 판 32).",
    ],
    "instance_report_builder": COMMON_DEC + [
        "**W-1 완전 shim(사용자 결정 (가))**: DR이 완전 shim이 된다. `test_selftest_design_report.py:24`의 `os`는 T0가 고쳤다(모의 W-1 점검 0곳, PT3 수집 오류 0). **SHIM (c)**: DR의 base 재수출 `from stick_diagram import load_topology, _audit_result_json`(gate master DR 32행 줄)은 남긴다 -- `_audit_result_json`은 이 card에서 MOD9로 가고 SD 끝 재수출을 거쳐 같은 객체로 해석된다(`check` `shim` 0, IMPORT-ANY 실패 0).",
        "**W-2 ACF 재수출 위치(질문 없음)**: 계약 10·R-W2. ACF의 M2 재수출 줄 뒤에 쌓인다.",
        "**D-22·LAYER(W-5)**: MOD9는 SD 이름 3개(`AuditResult`·`INSTANCE_TOP_FIELDS`·`run_full_circuit_audit`)를 파일 끝에서 받고, SD는 MOD9로 간 8단위의 재수출을 SD 끝에 둔다 -- `import_layering` 발견 2(예상, F2가 없앤다). m_cards_plan 표의 '2이름'(시제품 키)과 달리 `INSTANCE_TOP_FIELDS`가 SD에 남아(문장 키 = 바인딩 이름, p3_followup §5 관찰 'IC3 쌍이 갈린다') 끝 import가 3이름이다. 동작 차이 없음(SD가 F2까지 MOD9 이름을 끝에서 재수출, `test_ic3.py:107`은 F1이 출처로 바꾼다).",
    ],
}
CARD_T0 = {
    "topology_authoring": ["이 card에서 처음 깨지는 것: `test_ic5.py::test_gate_docstring_declares_blind_spots`(`_DOMAIN_TABLE` 키 (파일, 함수) 중 이 card가 옮기는 함수 -- design §7.1 A군). T0 병합본에서는 R-DEF로 통과해야 한다(T0 계약). `test_restore_plan_functions.py` 등 B군은 재수출로 통과(F1 몫)."],
    "circuit_state_graph": ["T0 계약 10(`test_b26_rail_accessor.py`)은 B26-1 병합 뒤에만 있다 -- 모의 밖(결정 필요 항목)."],
    "gmid_sizing_engine": ["이 card에서 새로 깨지는 것: `test_dup_w_calc.py::test_size_transistor_calls_new_function`(`size_transistor` 정의를 SR에서 찾음 -- A군 442행). W-1 3파일 수집 오류는 T0 W-1 대역으로 0."],
    "circuit_metrics": ["이 card가 새로 깨는 계약 test 0(앞 card 몫만 남음)."],
    "theta_search": ["이 card가 새로 깨는 계약 test 0(앞 card 몫만 남음)."],
    "sizing_layout_convergence": ["이 card에서 새로 깨지는 것: `test_ts6_dead_probes.py::test_audit_vsb_consistency_has_operational_caller`(운영 호출자를 SR에서만 찾음 -- A군 261~262행; 호출자가 MOD8로 감). 같은 파일의 `_L_ROLE_MULTIPLIERS` 바인딩 검사는 SR이 완전 shim이 되면 **조용히 공허**(FAIL로 드러나지 않음 -- T0가 R-DEF로 고친다)."],
    "instance_report_builder": ["이 card가 새로 깨는 계약 test 0. B군(`test_df36_instance_relpath.py`·`test_ic3.py` 등 SD에서 MOD9 이름 import)은 SD 끝 재수출로 통과(F1 몫)."],
}
