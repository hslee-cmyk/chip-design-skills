# nmcnr_amplifier `stage2_diode_ref` 헤드룸 infeasible 진단 (2026-10-07)

(진단 agent 보고 본문을 오케스트레이터가 옮겨 적음 -- agent 쪽 파일 쓰기가 하네스에 막혔다.)

- 기준: gmid-light `git clone --no-hardlinks` → `/c/g456/repo`, `checkout 6df4bd7`. 메인 저장소 2곳 읽기만. Python `C:\Python314`, subprocess timeout 590 s. 함수 입출력은 monkeypatch 기록(소스 무수정).
- 표기: [실측] 이번 실행 출력 / [코드] 소스 읽기 / [추정] 미검증 / [사용자 확인 필요] 회로 해석이라 결론 보류.
- 부수 효과: 옛 커밋의 run_harness.py(메인 저장소 절대 경로 박힘, DF-35)를 실행해 메인 저장소 `assets/__pycache__/{sizing_recipe,stick_diagram}.cpython-314.pyc`가 17:02에 재생성됨(바이트코드 캐시, git status 무변화, 산출물 없음).

## 1. 재현·에러 원문 [실측]
`run_harness.py nmcnr_amplifier`: 약 11 s, exit 0(DF-18).
```
[FAIL] ValueError: 모든 theta 격자점이 infeasible -- bounds/constraints를 확인하세요. 마지막 평가 조합의 theta=None, metrics=None, 위반된 제약=[]. 물리적으로 불가능해 건너뛴 조합 1개(마지막 사유: 'stage2_diode_ref' 그룹(예산 1.5V, 미해결 ['M203']): 스택 예산 1.5V 중 0.525V를 배정할 곳이 없다 -- 이 그룹은 구간 제약 소자(diode)뿐인데 전부 상한까지 올려도 예산을 못 채운다. 구간: [M203∈[0.6375,0.975]]. ... theta={'Ibg_tail': 1e-05, 'r_split_M102_M103': 0.5, 'r_fold_M108_M109': 0.5, 'kcl_M104': 1.0, 'kcl_M105': 1.0, 'r_series_M106': 1.0, 'r_series_M107': 1.0, 'kcl_M203': 1.0, 'kcl_M302': 1.0, 'r_mirror_M204_M203': 1.0, 'kcl_M202': 1.0})
```
- 예외 경로: `allocate_stack_headroom()` sizing_recipe.py:1909-1915 → `_hr_resolve_vertical_group()` 7553-7565 → `optimize_full_circuit_budget()` 9218("건너뛴 조합") → 9239 ValueError.
- theta 11개 전부 `bounds=[x,x]` → grid 1점, 자유도 0.

## 2. 헤드룸 계산 각 항 [실측]
그룹: M201(pmos, vdd→NodeC, G=NodeM2, compensation stage1) / M203(nmos diode, NodeC→vss, L_role mirror) / M204(nmos, G=NodeC, gm_id_match_vgs_of=M203, vds_match_vgs_of=M301) / M109(vds_match_vgs_of=M201).

| 단계 | 값 | 출처 |
|---|---|---|
| ① compensation stage1 VDS 후보 | {0, 0.15, …, 1.5}, cap = 1.8 − 0.2 = 1.6 | `reserved_vds_for_other_stack_members` = M203 `min_vds_by_role['mirror']` 0.2(diode 여부 무시) |
| M201 결과 | VDS 0.3, L 0.44 µm, gm/ID 17, ID 60.32 µA, W 482.4 µm, gm 1.025 mS | 8301 `compensation:stage1` |
| ② M109 VDS = VGS(M201) | 0.9204 V | `vds_match_vgs_of` |
| ③ M203 L | 0.245 µm(knee를 feasible_L_window로 clamp, 예산 무시) | `derive_role_L` |
| ④ M203 창 | [0.6375, 0.975] | `diode_vds_window` 7458 |
| ⑤ 예산 | 1.8 − 0.3 = 1.5 | 7258-7264 |
| ⑥ allocate | lo 0.6375 + 흡수 0.3375 → 0.525 남음 → 실패 | 1895-1915 |

- KVL상 M201 VDS 허용 범위 [0.825, 1.1625], 격자에서는 {0.9, 1.05}만.
- M203 창의 L 의존(같은 ID): 0.15 µm [0.6, 0.9] / 0.245 [0.6375, 0.975] / 1.0 [0.6, 1.3125] / 1.595 [0.6, 1.5] / ≥2.65 [0.6375, 1.8].

## 3. 근본 원인
3.1 [실측 검증] compensation이 M201 VDS를 같은 기둥 diode 창과 무관하게 고정한다. 기둥 예약이 diode를 role min_vds(0.2)로만 세고(실제 lo 0.6375), diode만 남는 기둥의 하한(VDS ≥ vdd − Σhi)을 만드는 경로가 없다.
- 실험: stage1 VDS 후보를 {0.9, 1.05}로 제한 → M201 0.9 V(L 0.535 µm, W 427.5 µm), M203 0.9, M204 0.6153, M202 1.1847, M302 1.65, stop_after_sizing 완주(power_uA 4042.29, gain_db 97.51, pm_deg 45.36 -- 판정용 아님).

3.2 [실측] 시작 시점: 01fa9e5^(B16 직전)은 diode Vgs=Vds 일관성 미검사로 통과, 01fa9e5(B16)부터 같은 종류 실패. B16은 결함을 드러냈을 뿐이다.
- L을 키워 흡수하는 대안 배제는 [추정, 사용자 확인 필요]: VGS가 1.5 V가 되면 M204(drain이 VGS(M301) 0.615 V에 묶임)가 선형 영역으로 들어갈 가능성.

3.3 후속 결함(관찰만): NodeTail KCL 잔차 1779 µA(M101 10 µA vs M102·M103 각 894.7 µA, I-B8), M106·M107 vsb 1.3 V(DF-01), constraints=[](U-35), power_uA 중복 계상(DF-16).

## 4. 계획서 연결
I-C11(plan:981), U-09(1086), DEC-12(207), DEC-70(264, compensation `set_device_vds`가 위반), DEC-71(265), DF-25/DF-32(937/944), DF-03/DF-18(915/930), I-B8/DF-01(967/913), J2(history:5570).

## 5. 회로 해석 — 사용자 확인 필요
| 질문 | 근거 |
|---|---|
| Q1. M203은 gm2(M201)의 부하이자 M204 미러의 레퍼런스인가 | M203 G=D=NodeC, M204 G=NodeC, M201 D=NodeC, compensation.notes, M204 `gm_id_match_vgs_of=M203`, J2 미결 |
| Q2. M201 VDS = vdd − VGS(M203)인 종속 관계인가 | 2소자 직렬 기둥, NodeC 채널 단자 2개, `kcl_M203`=1.0×M201 |
| Q3. M204가 포화여야 하는가 | M204 D=NodeS2=M301 G, `vds_match_vgs_of=M301` |

## 6. 수정안(이름 하드코딩 없음)
**A (Phase 4 성격)** `_evaluate`의 `_stage_extra_feasible`(8255-8264)에 기둥 diode 창 검사 콜백(선례 6697·6744). 후보 (L, VDS, gm_id, ID)마다: (1) 기둥 멤버 중 diode를 connectivity(gate==drain)로 선택 (2) 직렬 사슬이면 KCL로 ID, 아니면 검사 불가 태그 (3) `derive_role_L`을 순수 함수로 분리해 공유 (4) 7380-7470 미러 수집 + `diode_vds_window`를 헬퍼로 공유(DEC-12) (5) R = vdd − Σref − VDS − Σ확정에 대해 R ≥ Σlo + Σmin, 자유 흡수 소자가 없으면 R ≤ Σhi(`allocate_stack_headroom` 판정 공유). 캐시 필수(기존 `id(lut)` 키는 DF-13).
- 별도 결정: `reserved_vds_for_other_stack_members`의 diode 예약을 lo로 바꿀지(바꾸면 two_stage cap 1.4 → 1.2625).
**B (7b)** DEC-70·DEC-71로 근본 해소, A 콜백 삭제.

발동 범위(실측): nmcnr 상·하한 발동 → {0.9, 1.05} / two_stage 상한만 1.2625(현 VDS 0.9 포함, 결과 불변 예상·검증 필요) / current_reuse 0회 / folded 경로 없음.

## 7. test와 기대값 독립 출처
- T1 nmcnr 정본 stop_after_sizing 완주(base red 재현)
- T2 vds(M201)+vds(M203)=1.8 (KVL, 1e-9)
- T3 M203 (W,L,ID,vds)에서 LUT npz 직접 보간, VGS=VDS ID 일치(엔진 함수 미사용)
- T4 이름 없는 2소자 toy 픽스처, 손계산 lo·hi
- T5 창 만족 후보 없는 픽스처에서 실제 거부 + 메시지에 그룹 이름
- T6 자유 흡수 소자 있으면 하한 없음(손계산)
- T7 equivalence: current_reuse 비트 동일, folded 산출 동일, two_stage compensation 결과·실패 메시지 동일
