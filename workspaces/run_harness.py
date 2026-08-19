"""
run_harness.py -- 이 프로젝트의 **유일한** harness 실행 스크립트(2026-08-13 세션31,
사용자 지시로 topology별 복제본(`two-stage-ota-report/run_harness.py`,
`current-reuse-telescopic-ota-report/run_harness.py`)을 통합). 앞으로 새 회로를 돌릴
때도 이 파일을 복사해 새 run_harness.py를 만들지 않는다 -- SPECS 레지스트리에 항목만
추가한다.

사용법: python run_harness.py <circuit_key>
  circuit_key: SPECS에 등록된 키 중 하나. 예:
    python run_harness.py two_stage_ota
    python run_harness.py current_reuse_telescopic_ota

산출물은 기존과 동일하게 `workspaces/<circuit>-report/`에 저장한다(스크립트만 통합,
회로별 출력 위치는 그대로 유지).

## box-shape/floorplan 자동 재시도 루프(2026-08-14 세션32 -- `optimize_full_circuit_
## budget()` 내부로 이전, 세션18 §1.6 "순수 함수" 원칙은 이 지점에서 폐기)

세션31까지는 `optimize_full_circuit_budget()`을 "순수 함수"로 유지하고(§1.6), 어떤
`row_split`을 쓸지 자동 재탐색하는 orchestration은 이 harness 스크립트가 외부에서
맡았다 -- 매 반복마다 `optimize_full_circuit_budget()`을 통째로 재호출해서, row_split
1건만 바뀌어도 theta/gm-ID 그리드서치(가장 비싼 부분, row_split과 무관한데도)까지
매번 처음부터 다시 돌고 있었다(사용자 실측 지적: current_reuse_telescopic_ota 10분+
무응답). 이제 그 재시도 루프는 `spec["floorplan_target"]`을 넘기면
`optimize_full_circuit_budget()` 내부에서 (theta 서치는 1번만, row_split 조정만
반복하는 방식으로) 자동 실행된다 -- 이 스크립트는 그 결과 1회 호출만 하면 된다.
자세한 알고리즘(score 기반 best-so-far + backtracking)은 `sizing_recipe.py`의
`optimize_full_circuit_budget()`/`_evaluate_row_split()`/`_pick_split_target()`
docstring 참고.
"""
import sys
import os
import traceback
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"C:\Users\HSLEE\Documents\Todoc\fpga\chip-design-skills\skills\analog-gmid-design\assets")
import numpy as np
from sizing_recipe import (SemiEmpiricalGmIdLUT, optimize_full_circuit_budget, dense_candidates,
                            layout_grid_L_candidates, diagnose_sizing_roles_gap)
from stick_diagram import save_instance_json, run_full_circuit_audit_from_topology
from design_report import assemble_report_data, save_html_report

ASSETS_DIR = r"C:\Users\HSLEE\Documents\Todoc\fpga\chip-design-skills\skills\analog-gmid-design\assets"
LIBRARY_DIR = os.path.join(ASSETS_DIR, "library")
WORKSPACES_DIR = r"C:\Users\HSLEE\Documents\Todoc\fpga\chip-design-skills\workspaces"
LUTFILE = os.path.join(ASSETS_DIR, "sky130_nfet_pfet_lut_sample.npz")
# sky130 tech LEF(sky130hs.tlef, OpenROAD-Project 배포)의 "MANUFACTURINGGRID 0.005 ;"
# 원문으로 확인된 실제 제조그리드(um 단위) -- 이 값 자체는 추측이 아니라 웹에서 원문
# 대조로 확보함(.ai/context.md 세션31 참고). 레이아웃에서 임의 소수점 L을 구현할 수
# 없다는 제약을 반영하는 quantize_L()류 함수의 grid_step 인자로 씀.
L_GRID_STEP = 0.005e-6
# 2026-08-13(세션31, 사용자 지시) -- "최종 floorplan 결과가 빈공간없이 box형으로
# packing되면 만족" -- box_shape(옛 "행을 전부 한 컬럼으로 쌓으면"이라는 단일-컬럼
# 가정)이 아니라 **실제 2D packing 결과**(floorplan.aspect_ratio/packing_density)를
# 성공 판정의 정본으로 쓴다. box_shape/row_split_candidates는 "어느 stack을 더
# 접어야 하는가"를 고르는 진단 신호로만 쓴다(아래 _pick_split_target). aspect_ratio
# 기준은 stick_diagram.py self-test 관례("box-shape 목표 <=1.5")와 동일하게 유지.
FLOORPLAN_MAX_ASPECT_RATIO = 1.5
# packing_density(=block 면적 합/bbox 면적) 최소 기준 -- 이보다 낮으면 aspect_ratio가
# 좋아도 빈 공간이 많다는 뜻이라 "박스형으로 잘 packing됨"으로 볼 수 없다.
FLOORPLAN_MIN_PACKING_DENSITY = 0.5
MAX_ITERS = 6

_d = np.load(LUTFILE)
_W_REF = 5e-6
_NMOS = SemiEmpiricalGmIdLUT(_d["L"], _d["VGS"], _d["VDS"], _d["VS"], _d["ID_n"], _d["GM_n"],
                              _d["GDS_n"], _d["CGG_n"], W_ref=_W_REF, SID_1F=_d["SID_1F_n"])
_PMOS = SemiEmpiricalGmIdLUT(_d["L"], _d["VGS"], _d["VDS"], _d["VS"], _d["ID_p"], _d["GM_p"],
                              _d["GDS_p"], _d["CGG_p"], W_ref=_W_REF, SID_1F=_d["SID_1F_p"])


def _spec_two_stage_ota():
    """`workspaces/two-stage-ota-report/run_harness.py`(세션31 최종본)에서 그대로 이전.

    ## 경위(.ai/context.md 세션31 BZ①~CJ 전체 요약)
    원래 목표(GBW=20MHz, gain_db>=60, "typical" 문헌값)는 실제 sky130 LUT로 모든 레버
    (L 범위 1um->4um 확장, 면적예산 500um->2000um, M5/M7 theta 독립분리)를 다 시도해도
    물리적으로 달성 불가능함이 확정됐다(진짜 상한 ~50~51dB). 유일하게 유효했던 레버는
    **GBW를 낮추는 것**(compensation 공식 gm1=2π·GBW·Cm 관계상 GBW가 낮아지면 같은
    면적예산으로 훨씬 긴 L을 쓸 여유가 생김) -- GBW 20MHz~1MHz 전 구간을 스윕해 "10MHz
    부근부터 수확체감(무릎)"을 확인한 뒤, 사용자가 그 무릎 지점에서 타협하기로 결정:
    **GBW=7MHz(원 스펙 대비 1/3)로 gain_db=57.5dB 달성(원 스펙 51dB보다 오히려 +6.4dB
    개선), 전력은 오히려 291uA로 66% 절감**. `library/two_stage_ota.topology.json`의
    `gain_db` constraint도 이 결정에 맞춰 `>=60`에서 `>=57`로 갱신됨(topology.json
    `_target_spec_comment` 참고). M5/M7은 theta 분리를 한 번 시도했다가(+1dB, 그런데
    folding 4배 필요) GBW 레버가 훨씬 크게 개선한 뒤라 가치가 낮아져 공유 theta
    (`L_mirror_M5`)로 원복.

    box-shape는 M6(매칭 파트너 없는 단독 소자, stage2 출력이라 W가 압도적으로 큼)만
    `row_split`(2026-08-13 세션31 CD/CE 신설 `apply_explicit_row_split()`)으로 2행
    folding하면 충분했었다(finger-count 기준 max_ratio 1.2, 허용치 1.5 이내 PASS) --
    **단, 이 값은 box-shape가 L을 반영하지 않던 시절의 결과다.** 이번 세션 후반(box-shape
    실제 물리 치수 반영) 이후로는 M3(L=2.7um대, 압도적으로 긴 L)가 새로 폭을 지배하게
    됐다 -- 위 harness 자동 재시도 루프가 이 재조정을 담당한다(row_split의 시작값은
    과거 세션이 손으로 찾은 `{"M6": 2}`를 그대로 두되, 자동 루프가 필요하면 추가로
    조정한다)."""
    return {
        "lut_by_kind": {"nmos": _NMOS, "pmos": _PMOS},
        "lut": _NMOS,
        # LUT 특성화 범위(VDS 0~1.8V)가 sky130 nominal rail과 일치.
        "vdd": 1.8,
        "L_candidates": layout_grid_L_candidates(_NMOS, L_GRID_STEP, n=41),
        "L_grid_step": L_GRID_STEP,
        "VDS_candidates": dense_candidates(_NMOS.VDS_grid, n=13),
        "gm_id_grid": [i * 0.5 for i in range(4, 61)],
        # 2026-08-13(세션31 CJ) -- GBW 20MHz->7MHz(무릎 지점, 사용자 결정). Z/NDP는 원래
        # "typical" 값 그대로(Z를 3.5까지 낮춰봐도 GBW 여유가 거의 안 늘어남을 실측 확인,
        # .ai/context.md CJ 참고 -- Z는 지배적 레버가 아니었다).
        "GBW": 7e6, "CL": 3e-12, "Z": 10.0, "NDP": 4.0,
        "stage_gain_min": [10 ** (30.0 / 20), 10 ** (30.0 / 20)],
        "L_min": 0.15e-6,
        "L_min_by_kind": {"nmos": 0.15e-6, "pmos": 0.15e-6},
        "W_bounds": (1e-6, 200e-6),
        "min_vds_by_role": {"cascode": 0.2, "tail": 0.2},
        "stage_objective": "power",
        "stage_w_max": 500e-6,
        "min_finger_w": 0.1e-6,
        "max_finger_w": 40e-6,
        "vth0_slope": {"nfet": 3.356e-3, "pfet": 5.856e-3},
        "stack_groups_override": {"M1": ["M1", "M2"], "M3": ["M3", "M4"],
                                    "M5": ["M5", "M7"], "M6": ["M6"]},
        # M6(단독 소자, 옛 finger-count 기준 box-shape의 유일한 병목)만 2행 folding --
        # 실제 물리 치수 반영 이후로는 harness 자동 루프가 추가로 조정할 수 있다.
        "row_split": {"M6": 2},
    }


def _spec_current_reuse_telescopic_ota():
    """`workspaces/current-reuse-telescopic-ota-report/run_harness.py`(batch 7-5,
    세션12~31 누적 정정)에서 그대로 이전."""
    return {
        "lut_by_kind": {"nmos": _NMOS, "pmos": _PMOS},
        "lut": _NMOS,
        "vdd": 1.8,
        # 2026-08-12(세션30) -- SemiEmpiricalGmIdLUT는 L/VDS 둘 다 이미 다중선형보간하는데
        # (sizing_recipe.py 클래스 docstring), 이 후보 리스트를 실측 앵커점(L 4개) 그대로
        # 쓰거나 과도하게 데시메이션(VDS 49점 -> 3점)해서 그 보간 능력을 검색이 안 쓰고
        # 있었다 -- dense_candidates()로 VDS는 실측 범위 안에서 촘촘하게(외삽 없음).
        # gm_id_to_id_density()의 중복 log(ID) 재계산 캐시 버그를 같이 고친 뒤 재실측
        # (perf_test_dense.py, .ai/context.md 세션30): L=41/VDS=13이 10초 수준으로
        # 내려가 VDS도 13으로 올렸다 -- optimize_multistage()가 comp_params로 캐싱돼
        # 호출 자체가 드물어 이 정도 비용은 감당 가능.
        # 2026-08-13(세션31) -- L_candidates는 dense_L_candidates()(임의 소수점 보간)
        # 대신 layout_grid_L_candidates()(L_GRID_STEP 배수만 나열)로 교체 -- 실제
        # 레이아웃에서 구현 못 하는 소수점 L을 애초에 후보에서 배제한다(n=41로 기존과
        # 동일한 격자 크기 예산 유지, sizing_recipe.py layout_grid_L_candidates()
        # docstring 참고).
        "L_candidates": layout_grid_L_candidates(_NMOS, L_GRID_STEP, n=41),
        "L_grid_step": L_GRID_STEP,
        "VDS_candidates": dense_candidates(_NMOS.VDS_grid, n=13),
        # 2026-08-12(세션30) -- L_candidates를 densify하자 compensation 단계 L이 옛 4개
        # 앵커점이 아닌 임의값이 될 수 있게 됐는데, matching_pairs로 그 L을 공유하는
        # gm_id_role="matching" 소자는 search_gm_id_for_role()의 **훨씬 성긴**(step=4,
        # 6점) gm_id_grid로 그 임의 L에서 feasible W를 못 찾아 ValueError로 전체 grid
        # search가 크래시했다(diagnose_gm_id_fail.py로 재현 확인 -- DENSE 표본 200/200
        # 크래시, BASELINE 200/200 성공). search_gm_id_for_role() 자체 문서화된
        # 기본값(2.0~30.0, 0.5 간격)과 맞춰 57점으로 -- L만이 아니라 gm_id 쪽 탐색
        # 해상도도 같이 촘촘해야 LUT 보간을 실제로 쓰는 게 완성된다(gm_id_curve_cache가
        # (L,vds,vs)당 1회만 비싸고 그 안에서 gm_id 재조회는 저렴해 이 축을 넓혀도
        # 상대적으로 싸다).
        "gm_id_grid": [i * 0.5 for i in range(4, 61)],
        "L_min": 0.15e-6,
        "L_min_by_kind": {"nmos": 0.15e-6, "pmos": 0.15e-6},
        "W_bounds": (1e-6, 200e-6),
        "min_vds_by_role": {"cascode": 0.2, "tail": 0.3, "mirror": 0.3},
        "stage_objective": "power",
        "stage_w_max": 200e-6,
        "min_finger_w": 1e-6,
        "max_finger_w": 40e-6,
        "vth0_slope": {"nfet": 3.356e-3, "pfet": 5.856e-3},
        # compensation.parameters
        "t_lln": 30e-9,
        "PM_target_deg": 70.0,
        "Cc": 500e-15,
        "Cf": 500e-15,
        "Cs": 500e-15,
        "C_Ltot": 1e-12,
        # 2026-08-10(세션27) 정정 -- t_settle_total은 do.md §7.3.1 Level1 "t_s=t_slew+t_lln
        # 배분"의 총합(논문 III.A "t_slew=10ns/t_lln=30ns"=40ns)이어야 하는데, 이전 값
        # (6.9*30e-9≈207ns)은 t_lln*omega_c=6.9 정의를 엉뚱하게 총정착시간에 갖다 쓴
        # 것이었다 -- f_slew->t_lln 배선이 미완결이던 동안엔 t_settle_total이 실제로
        # 아무 데도 안 읽혀서(derived[t_slew]를 아무도 안 읽음) 드러나지 않았을 뿐이다.
        # 이제 t_lln=t_settle_total*(1-f_slew)로 실제 유도되므로 물리적으로 맞는 값
        # (40ns)으로 정정 -- f_slew=0.25일 때 t_slew=10ns/t_lln=30ns로 논문 수치와
        # 정확히 재현됨(sizing_recipe.py self-test의 _feed_settling_split 데모와 동일 값).
        "t_settle_total": 40e-9,
        # omega_c는 더 이상 여기서 손으로 줄 필요가 없다(compensation이 t_lln에서
        # 자동 유도해 ctx.derived로 노출 -- _feed_gm_target_convention()이 우선 사용).
        # 다만 compensation이 없는 회로/구형 spec과의 하위호환을 위해 폴백값으로 남겨둔다.
        "omega_c": 6.9 / 30e-9,
    }


def _spec_folded_cascode():
    """2026-08-15(세션35) -- 완주 확인됨. `MP`(PMOS 다이오드 레퍼런스)의 전류를 대는
    `ideal_sources`의 `Ibg`가 원래 `value_amp: null`(TBD)이었던 gap을 다음 3단계로
    해소했다: (1) `diagnose_sizing_roles_gap()`으로 gap을 구조화된 리포트로 진단(날것의
    스택트레이스 대신), (2) Maloberti 원본(`Layout of Analog CMOS IC` p.34, 웹검색으로
    원문 확인 -- W비율만 있고 절대 전류값은 없음)의 미러비를 `sizing_roles.theta`(type
    "A"/"A_signed", 전부 고정값)로 KCL 유도, (3) `Ibg` 자체는 새 theta feed 타입 `"const"`
    (사용자 지시로 신설)로 자유변수화해 gain/PM/CMRR/PSRR 스펙(topology.json의
    `sizing_roles.constraints` 참고 -- Ibg=10uA 임의값의 baseline 실측을 그대로 스펙으로
    채택)을 만족하는 최소 전력점을 탐색. 이 과정에서 X/Y 폴딩 노드의 헤드룸 분배를 위한
    새 엔진 기능(`device_roles.*.fold_group`, `sizing_recipe.py`의 `_fold_group_check()`)
    과 새 성능 메트릭(`folded_cascode_gain_db`/`folded_cascode_pm_deg`)도 신설했다. 실측:
    Ibg~2.1uA에서 power_uA~40(Ibg=10uA 대비 4.7배 절감)으로 gain/PM/CMRR/PSRR 전부
    만족. ⚠️ gain/PM 폐형식은 sympy 전수 유도·ngspice 교차검증 전이다(각 메트릭 함수
    docstring 참고) -- 최종 확인은 SPICE 필요. `.ai/context.md` 세션35 참고."""
    return {
        "lut_by_kind": {"nmos": _NMOS, "pmos": _PMOS},
        "lut": _NMOS,
        "vdd": 1.8,
        "L_candidates": layout_grid_L_candidates(_NMOS, L_GRID_STEP, n=41),
        "L_grid_step": L_GRID_STEP,
        "VDS_candidates": dense_candidates(_NMOS.VDS_grid, n=13),
        "gm_id_grid": [i * 0.5 for i in range(4, 61)],
        "L_min": 0.15e-6,
        "L_min_by_kind": {"nmos": 0.15e-6, "pmos": 0.15e-6},
        "W_bounds": (1e-6, 200e-6),
        "min_vds_by_role": {"cascode": 0.2, "mirror": 0.2},
        "min_finger_w": 1e-6,
        "max_finger_w": 40e-6,
        "vth0_slope": {"nfet": 3.356e-3, "pfet": 5.856e-3},
    }


def _spec_nmcnr_amplifier():
    """2026-08-15(세션35) 최초 등록 -- 2026-08-18(세션36)에 바이어스 전류망 gap을 완전히
    해소했다(이 docstring이 stale해졌던 걸 세션36 끝에 정정). ⚠️ 이 회로는 **아직도 끝까지
    사이징되지 않지만, 남은 원인은 하나뿐**이다(`.ai/context.md` 세션36 §4-① 참고):

    `sizing_roles.metrics`/`objective`/`constraints`가 아직 `null`이라 `optimize_full_
    circuit_budget()`이 마지막 단계(`objective["maximize"]`)에서 `KeyError`를 낸다 --
    15개 소자(`M101`~`M302`) 전체의 전류(KCL)/gm_id/L/W sizing 자체는 실제로 끝까지
    완주한다(세션36에 `python run_harness.py nmcnr_amplifier` 실행으로 직접 확인).
    `folded_cascode`의 `gain_db`/`pm_deg`/`cmrr_db`/`psrr_db` 폐형식 메트릭 패턴
    (`sizing_recipe.py`의 `_metric_folded_cascode_*`, `_METRICS_REGISTRY`)을 참고하되
    3단 구조(gm1/gm2/gm3)에 맞는 새 폐형식 설계가 필요하다.

    ⚠️ 세션35가 여기 적어뒀던 "바이어스 전류망(M101/M104~M107/M202/M302)이 `ideal_
    sources` 선언 없이 A엔진이 못 푼다"는 **틀린 진단이었다**(세션36 재조사로 밝혀짐 --
    `ideal_sources`/`voltage_source` 확장은 애초에 불필요, 실제로 필요했던 건 `M108`/
    `M109`를 진짜 전류생성원 root로 두는 KCL 구조뿐이었다). `nmcnr_amplifier.topology.
    json`에 `fold_group`/`vertical_stack_id`/`sizing_roles.theta`(7개)가 세션36에 전부
    채워져 있다 -- 더 이상 gap 아님, 재작업 불필요.

    `PM_target_deg=70.0`(아래)는 2026-08-19(세션37)에 **확정 스펙으로 결정됨** -- `topology.
    json`의 `_paper_target_spec.PM_target_deg`(46도, 논문 실측치)는 `nmcnr_3stage_topology()`
    자신의 `PM_target_deg>60` 전제와 구조적으로 충돌해 그대로 못 쓴다(사용자 확인 완료).
    `current_reuse_telescopic_ota`와 동일 값(구조적 하한 60도 대비 10도 여유)을 채택 --
    "논문 값 그대로 인용 금지, 값은 합리적으로 도출" 원칙에 따른 최종 결정이며 더 이상
    임시값이 아니다. gain_db/pm_deg metrics는 `sizing_roles.metrics`에 등록됨(`sizing_
    recipe.py`의 `_metric_nmcnr_gain_db`/`_metric_nmcnr_pm_deg`, `topology_library.
    nmcnr_predict_ac_response()` 배선) -- `.ai/context.md` 세션37 참고."""
    return {
        "lut_by_kind": {"nmos": _NMOS, "pmos": _PMOS},
        "lut": _NMOS,
        "vdd": 2.0,
        "GBW": 816000.0, "CL": 1e-10, "kg": 0.5,
        "PM_target_deg": 70.0,  # 2026-08-19(세션37) 확정 스펙 -- 위 docstring 참고
        "L_candidates": layout_grid_L_candidates(_NMOS, L_GRID_STEP, n=41),
        "L_grid_step": L_GRID_STEP,
        "VDS_candidates": dense_candidates(_NMOS.VDS_grid, n=13),
        "gm_id_grid": [i * 0.5 for i in range(4, 61)],
        "L_min": 0.15e-6,
        "L_min_by_kind": {"nmos": 0.15e-6, "pmos": 0.15e-6},
        "W_bounds": (1e-6, 200e-6),
        "stage_objective": "power",
        "stage_w_max": 500e-6,
        "min_vds_by_role": {"cascode": 0.2, "mirror": 0.2},
        "min_finger_w": 1e-6,
        "max_finger_w": 40e-6,
        "vth0_slope": {"nfet": 3.356e-3, "pfet": 5.856e-3},
    }


# circuit_key -> 실행 설정. 새 회로를 추가할 땐 이 dict에 항목만 추가할 것 -- 새
# run_harness*.py 파일을 만들지 않는다(모듈 docstring 참고).
SPECS = {
    "two_stage_ota": {
        "topology_file": "two_stage_ota.topology.json",
        "spec_fn": _spec_two_stage_ota,
        "grid_points_per_theta": 7,
        "report_dir": "two-stage-ota-report",
    },
    "current_reuse_telescopic_ota": {
        "topology_file": "current_reuse_telescopic_ota.topology.json",
        "spec_fn": _spec_current_reuse_telescopic_ota,
        "grid_points_per_theta": 2,  # search_method="grid"로 폴백할 때만 쓰임(아래 참고)
        "report_dir": "current-reuse-telescopic-ota-report",
        # 2026-08-14(세션32, `.ai/context.md` 확인 중 발견) -- 이 회로는 자유 theta가
        # 13개라 grid_points_per_theta=2만 해도 2^13=8192개 조합(세션27 "## A"가 이미
        # "격자 폭발"로 지목, .ai/context.md line 754/6324) -- 세션31 AW절 실측으로도
        # 이 grid 방식은 완주해도 feasible point를 하나도 못 찾는다(해상도 문제, 버그
        # 아님). 세션29~31이 검증한 정답 경로는 search_method="slsqp"다 -- 세션31 BU가
        # 이 정확한 파라미터(n_starts=3, maxiter=25)로 gain_db=76.587/mismatch_sigma_mV=
        # 4.617/classab_centering_dev_v=0.14988(전부 통과)를 실측 확인했다. 이 harness가
        # 통합되면서(CQ/CR) 이 배선이 누락돼 기본값 "grid"로 실행되고 있었다 -- 여기서
        # 바로잡는다.
        "search_method": "slsqp",
        "slsqp_kwargs": {"n_starts": 3, "maxiter": 25},
    },
    "folded_cascode": {
        "topology_file": "folded_cascode.topology.json",
        "spec_fn": _spec_folded_cascode,
        "grid_points_per_theta": 400,
        "report_dir": "folded-cascode-report",
        # 2026-08-15(세션35) -- 자유 theta가 Ibg 1개뿐이라 촘촘한 그리드가 저렴하다.
        # SLSQP는 시도했으나 pm_deg 제약이 이 회로의 gm_id 격자 탐색(연속이 아니라 이산
        # search_gm_id_for_role() 스캔) 때문에 매끄럽지 않아 3회 multi-start 전부 실현
        # 불가능한 해로 수렴(선형탐색 실패) -- 1차원이라 정밀 그리드가 더 안정적이고
        # 저렴해 이쪽을 채택(_spec_folded_cascode() docstring 참고).
    },
    "nmcnr_amplifier": {
        "topology_file": "nmcnr_amplifier.topology.json",
        "spec_fn": _spec_nmcnr_amplifier,
        "grid_points_per_theta": 5,
        "report_dir": "nmcnr-amplifier-report",
        # 2026-08-19(세션37 갱신, 세션36의 stale 코멘트 정정) -- sizing_roles.metrics(gain_db/
        # pm_deg/cmrr_db/psrr_db)와 objective(minimize power_uA)가 등록됨, PM_target_deg=
        # 70.0도 확정 스펙으로 결정됨(_spec_nmcnr_amplifier() docstring 참고). constraints는
        # 아직 null -- 이 실행으로 baseline 실측을 얻어 채워 넣을 예정(.ai/context.md 세션37).
    },
}

def run(circuit_key: str) -> None:
    if circuit_key not in SPECS:
        raise ValueError(f"등록되지 않은 circuit_key={circuit_key!r} -- "
                          f"SPECS에 있는 것 중 하나를 쓸 것: {sorted(SPECS)}")
    cfg = SPECS[circuit_key]
    topo = os.path.join(LIBRARY_DIR, cfg["topology_file"])
    report_dir = os.path.join(WORKSPACES_DIR, cfg["report_dir"])
    stem = cfg["topology_file"].removesuffix(".topology.json")
    instance_out = os.path.join(report_dir, f"{stem}.instance.json")
    report_out = os.path.join(report_dir, f"{stem}.report.html")
    spec = cfg["spec_fn"]()
    # 2026-08-14(세션32) -- box-shape/floorplan 자동 재시도는 이제 optimize_full_circuit_
    # budget() 내부에서 처리한다(모듈 docstring 참고, sizing_recipe.py의 함수 docstring이
    # 정본) -- floorplan_target만 넘기면 theta 그리드서치는 1번만 돌고 row_split만 자동
    # 조정된다. MAX_ITERS는 그 내부 루프의 max_layout_retry_rounds로 그대로 넘긴다(같은
    # 숫자를 두 곳에 따로 안 두기 위해).
    spec.setdefault("floorplan_target", {
        "max_aspect_ratio": FLOORPLAN_MAX_ASPECT_RATIO,
        "min_packing_density": FLOORPLAN_MIN_PACKING_DENSITY,
    })
    spec.setdefault("max_layout_retry_rounds", MAX_ITERS)

    try:
        result = optimize_full_circuit_budget(
            topo, spec, grid_points_per_theta=cfg["grid_points_per_theta"],
            search_method=cfg.get("search_method", "grid"),
            slsqp_kwargs=cfg.get("slsqp_kwargs"))
        pr = result["pipeline_result"]
        if pr is None:
            print("pipeline_result=None -- 넷리스트 전체가 사이징되지 않아 자동 조정 불가")
        else:
            for r in pr.get("layout_retry_rounds", []):
                print(f"[row_split 재시도] target={r['target']} row_split={r['row_split']} "
                      f"score {r['score_before']:.3f}->{r['score_after']:.3f} "
                      f"accepted={r['accepted']}")
            floorplan = pr["floorplan"]
            aspect_ok = floorplan.aspect_ratio <= FLOORPLAN_MAX_ASPECT_RATIO
            density_ok = floorplan.packing_density >= FLOORPLAN_MIN_PACKING_DENSITY
            print(f"floorplan.aspect_ratio={floorplan.aspect_ratio:.3f}"
                  f"(<= {FLOORPLAN_MAX_ASPECT_RATIO} ? {aspect_ok}), packing_density="
                  f"{floorplan.packing_density:.3f}(>= {FLOORPLAN_MIN_PACKING_DENSITY} ? {density_ok}) "
                  f"-- 정본 판정=floorplan_ok={aspect_ok and density_ok}, "
                  f"row_split={pr.get('row_split', {})}")

        print("OK -- theta_star:", result["theta_star"])
        print("audit_ok:", result["audit_ok"])
        print("metrics:", result["metrics"])

        full_circuit_audit = None
        try:
            full_circuit_audit = run_full_circuit_audit_from_topology(topo)
            print("run_full_circuit_audit.ok:", full_circuit_audit.ok)
            for c in full_circuit_audit.checks:
                print(f"  - {c.name}: {c.ok} ({c.detail})")
        except ValueError as e:
            print(f"[SKIP] run_full_circuit_audit_from_topology() 실패(topology.json에 "
                  f"_netlist_sections_structured가 없는 등 별개 gap일 수 있음): {e}")

        if pr is not None:
            bs = pr["box_shape"]
            fp = pr["floorplan"]
            final_floorplan_ok = (fp.aspect_ratio <= FLOORPLAN_MAX_ASPECT_RATIO
                                   and fp.packing_density >= FLOORPLAN_MIN_PACKING_DENSITY)
            print(f"box_shape.ok={bs.ok}(참고용) rectangular={bs.rectangular} "
                  f"width_ratio={bs.width_ratio:.3f} approx={bs.approx} "
                  f"row_widths={bs.row_widths} row_heights={bs.row_heights}")
            print(f"floorplan.aspect_ratio={fp.aspect_ratio:.3f} "
                  f"packing_density={fp.packing_density:.3f} (정본 판정=floorplan_ok={final_floorplan_ok})")
            print(f"coverage.ok={pr['coverage'].ok} missing={pr['coverage'].missing}")

            save_instance_json(instance_out, topo, result["sizing"], result["pipeline_result"])
            note_parts = []
            if not result["audit_ok"]:
                note_parts.append("audit_ok=False -- audit_row_split에 남은 FAIL 항목 그대로 저장됨")
            if not final_floorplan_ok:
                note_parts.append("floorplan_ok=False -- 자동 재시도로도 못 고침(빈 공간 많거나 "
                                   "종횡비 초과), 그대로 저장됨")
            if full_circuit_audit is not None and not full_circuit_audit.ok:
                note_parts.append("run_full_circuit_audit.ok=False -- 위 체크 결과 참고")
            note = f" ({'; '.join(note_parts)})" if note_parts else ""
            print(f"instance.json 저장: {instance_out}{note}")

            if full_circuit_audit is not None:
                report_data = assemble_report_data(topo, instance_out, full_circuit_audit=full_circuit_audit)
                save_html_report(report_data, report_out)
                print(f"report.html 저장: {report_out}")
            else:
                print("report.html 생략(full_circuit_audit 실패로 assemble_report_data 입력 불완전)")
        else:
            print("pipeline_result=None -- 넷리스트 전체가 사이징되지 않아 instance.json/report 저장 생략")
    except Exception as e:
        print(f"[FAIL] {type(e).__name__}: {e}")
        traceback.print_exc()
        # 2026-08-15(세션35, 사용자 지시 -- "device_role/symmetry처럼 sizing_role도 자동으로
        # 채우는 걸 설계하고 통합하자") -- ValueError는 sizing_roles=null 상태에서
        # optimize_full_circuit_budget()이 A엔진/L-VDS/compensation 중 하나를 못 풀었을 때도
        # 나는 흔한 경로다(folded_cascode의 Ibg 미정, nmcnr_amplifier의 PM_target_deg<=60
        # 사례로 실측). 날것의 스택트레이스만 보고 사람이 원인을 다시 추적하지 않도록,
        # 같은 topo/spec으로 diagnose_sizing_roles_gap()을 한 번 더 돌려 구조화된 gap
        # 리포트를 이어 출력한다(진단 함수 자체가 값을 지어내지는 않는다 -- sizing_recipe.py
        # diagnose_sizing_roles_gap() docstring 참고).
        if isinstance(e, ValueError):
            print()
            print("[diagnose_sizing_roles_gap() 추가 진단]")
            try:
                print(" ", diagnose_sizing_roles_gap(topo, spec))
            except Exception as _diag_e:
                print(f"  (진단 자체도 실패: {type(_diag_e).__name__}: {_diag_e})")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"사용법: python run_harness.py <circuit_key>  (등록된 키: {sorted(SPECS)})")
        sys.exit(1)
    run(sys.argv[1])
