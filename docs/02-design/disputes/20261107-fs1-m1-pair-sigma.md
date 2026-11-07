---
id: 20261107-fs1-m1-pair-sigma
spec_card: docs/02-design/specs/20261107-fs1.spec.md
test_id: skills/analog-gmid-design/gmid_engine/tests/search/test_iv_matching_l.py::test_m1_run_b_lower_bound_is_hand_picked_anchor_and_args_unchanged
test_id: skills/analog-gmid-design/gmid_engine/tests/search/test_iv_matching_l.py::test_m2_evaluation_sigma_rows_use_the_evaluation_cell_key_not_reference_width
---
## 문제의 test

1. M-1 (b) `test_m1_run_b_lower_bound_is_hand_picked_anchor_and_args_unchanged`: 실행 B(제약 값 = `σ_share·√2/1e-3` mV)의 입력 소자 matching L 하한이 손으로 고른 앵커 `L_k`(8 µm)와 `==` 이어야 하는데 실측 하한 = 2.0e-05(가장 긴 앵커 = '어느 앵커도 통과하지 못함' 폐쇄값) -- `AssertionError: ('M1', [1.9999999999999998e-05], 8e-06)`.
   (a) 4단계 spy w_f == w_ref(P1)은 통과한다(같은 test 의 앞 단언 -- 실측으로 기준 폭 슬라이스가 쓰였다).
2. M-2 후반 `test_m2_evaluation_sigma_rows_use_the_evaluation_cell_key_not_reference_width`: `check_theta: θ 키가 스키마와 다르다 -- 빠짐 [('y', 'OUT'), ('y', 'vin_p')]`(test 가 만든 θ 에 y 성분이 없다 -- 엔진 호출 전 입력 오류).

## 근거(oracle 또는 사용자 원문)

1. 엔진 정의(`iv_matching_l.py` 머리, 설계 41 §6.4-2, FS-1 이 바꾸지 않은 식): 입력 셀 몫 σ_share = 제약값 × 1e-3 / √2, L 하한 조건 = **쌍** σ_ΔVGS = √2·σ_VGS(단일 소자) ≤ σ_share. 그래서 제약 값을 `X mV` 로 두면 단일 소자 σ 가 `X·1e-3/(2)` 이하일 때 통과한다.
   interface §3.4 단계 4 는 '쌍 s(L) = √2·σ' 라 적고 단계 5 의 `s_ref(L)`을 '4의 식'(= 쌍 s)으로 정의한다. 그런데 `tests/search/fs1_hand_sigma.py::pick_anchor` 의 `s_of` 는 `sig.sigma(...)` = **단일 소자 σ**(√2 없음)를 그대로 `s_ref` 로 쓰고
   `share = (s_ref[Lp] + s_ref[Lk]) / 2` 를 만든다. 그 값 σ_share_hand 를 제약 값 `σ_share_hand·√2/1e-3` mV 로 주면 엔진 조건은 `√2·σ_dev(L) ≤ σ_share_hand`(쌍 비교)가 되어, 단일 σ 로 고른 L_k 에서는 √2 배 모자라 어느 앵커도 통과하지 못한다(→ 폐쇄값 2e-5).
   손 oracle 의 단위(단일 대 쌍)가 interface 문장과 한 칸(√2) 어긋난다. 엔진 식은 base 와 같다(FS-1 은 slope bin 폭만 바꿨다).
2. θ 입력 오류는 엔진과 무관하다.

## 요청

`fs1_hand_sigma.pick_anchor` 가 `s_ref`·`s_alt` 를 쌍 σ(`√2 × 단일 σ`)로 만들거나(interface 단계 4 'Σ 쌍 s(L) = √2·σ'), 제약 값 변환을 `σ_share_single·2/1e-3` 로 고친다. 둘째 test 는 θ 에 `y` 성분을 더한다.
