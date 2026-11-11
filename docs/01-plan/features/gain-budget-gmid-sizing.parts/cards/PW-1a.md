### N6.17 card PW-1a -- 엔진 `power_dc_w` 대조 연결(oracle OP-11 후속)(PW-1b는 사용자 결정 O-178로 삭제)

순서: **OP-11 → PW-1a → CL-1**(사용자 결정 O-178; PW-1a는 oracle 판정의 정의 동일성(전력 정의 하나) 몫이다).

**근거**: DEC-72 (3)(정의 동일성 관문 -- 엔진·oracle이 같은 전력 정의), DEC-78(전력 축 정의), oracle-portability v0.6.9 card OP-11과 그 계획 U-5 알림("엔진 `verified_by.py:42`가 `power_dc_w`를 오라클 measure `supply_current_A`(전류)에 잇는다 -- OP-11이 `power_dc_w` measure를 낸 뒤 그 연결을 바꾸는 것과 `derived.model_error_power_dc_w` 기록은 gain-budget 계획 card 몫" -- 인용 원문, 그 기록은 O-178로 삭제). 기존 card 중 이 범위를 가진 것이 없어 새로 둔다(DE-1의 `verified_by.py` 범위는 `offset_sys_mv` 행 `:45`뿐).

**사실**(base master `b2c72a01`, 2026-10-19 직접 확인): `E/metrics/verified_by.py:42` `("power_dc_w", SPICE_ORACLE, "supply_current_A")` -- **정의 불일치**: 엔진 `power_dc_w`는 모든 레일의 Σ V·I(W, DEC-78 -- 2026-10-19 as-built; v6.38.2 DEC-78 개정 뒤에는 `counted_rails` 선언이 있으면 그 레일의 Σ V·I)인데 oracle `supply_current_A`는 레일 **하나**의 전류(A)다(`tools/spice_oracle/legacy_adapter.py:418-419, :437-438` -- 항목에 `rail` 하나를 붙임; 레일 전류 원천 `oracle_simulate.py:150-153` `rail_current_A`). 같은 이름의 양을 다른 정의로 대조하는 것이라 O-29 (1)(정의 = SPICE 해석 종류·같은 정의)·O-32(oracle 측정 정의를 엔진 정의와 같게) 위반이다. 같은 줄 `supply_current_dc` → `supply_current_A`는 셈하는 레일(`counted_rails`, `E/search/objectives.py` 머리 `counted_rails_undeclared`)이 **하나일 때만** 정의가 같다 -- 둘 이상이 선언되면 같은 정정(O-29 (1)·O-32)이 필요하다. 지금은 `counted_rails` 미선언이라 발동 0이고 이 card 범위가 아니며, 아래 '백로그' (i) 행으로 둔다. `E/metrics/model_error.py`(`model_error_pairs`)는 사용자 결정 O-178 재작성 범위(삭제 대상)다.

**PW-1a -- 엔진 대조 연결 정정**(Role: code, O-34 (1) 동작 변경 -- 대조 대상 measure가 바뀜)
* 범위: `verified_by.py:42`의 `power_dc_w` measure를 OP-11이 내는 `power_dc_w`로 바꾼다.
* 완료 조건: (1) `verified_by` 대조표에서 `power_dc_w` → `power_dc_w` measure, 단위 일치 test(전력 metric이 전류 measure에 이어지면 red -- base에서 red), **부호 규약 대조 toy**(레일 둘 손 회로에서 엔진 `power_dc_w`와 OP-11 값의 부호·크기가 같음 -- 엔진 `supply_currents`(`E/metrics/dc_metrics.py:111` -- `power_dc_w` = `E/metrics/supply.py:69` 모든 레일 Σ V·I)와 oracle `rail_current_A = -i(Vrail)`(`oracle_simulate.py:39, :150-153`)의 규약 대조; v6.19 2차 전체 정합 검증 '미확인' 항목을 이 card 완료 조건으로 확인) (2) 결과 JSON의 `verified_by` notes 변화는 검증자 변화표(원인 미설명 0) (3) 결정성 비트 동일 (4) N6.3 공통.
* 완료 조건 추가(v6.38.2 -- DEC-78 개정, 검증 3 V3-9): `counted_rails` 선언 toy(엔진 `power_dc_w`와 OP-11이 같은 레일 집합)는 card SF-1 범위 8 완료 조건 한 곳에 둔다(O-166 E10).
* 착수 조건: oracle-portability v0.6.9 card OP-11 **승인**과 병합(measure 이름이 확정돼야 한다) → design(S-7 -- design 40 §3.8-6 `verified_by`에 design이 더할 `power_dc_w` → OP-11 measure 대응 항목·card 표 PW-1a 행, 규칙 근거 = design 40 §10.2 '검증 기준' E-1 (a) 정의 동일성 관문(§4는 인용); VB-1(N6.18)과 같은 절차). CL-1 앞. LA-1과 독립(파일 겹침 없음 -- 착수 때 확인).

**PW-1b -- 삭제**(사용자 결정 O-178: 회로별 `model_error_power_dc_w` 기록은 e_m 폐지로 소비자 0 -- 옛 범위·완료 조건·순서는 history)

**선언 레일 toy**(옛 백로그 (i) -- v6.38.4 백로그 재감사로 `supply_current_A` 정의는 card SF-1 범위 8 무조건 문언으로 옮김, 옛 (ii) `Role: data` 정식 등록은 삭제; 원문 history H2): PW-1a 대조 toy에 선언 레일 toy를 더한다(`counted_rails` 선언 시 엔진 `power_dc_w`·oracle OP-11이 같은 레일 집합 -- v6.38.2 DEC-78 개정, 사용자 결정 2026-10-14 N12).

